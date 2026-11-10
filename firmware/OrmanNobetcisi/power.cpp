// power.cpp - Bkz. power.h. Harici dusuk-guc kutuphanesi kullanilmaz (avr/sleep.h, avr/wdt.h).
//
// Uyanma kaynaklari (power-down):
//   * WDT kesmesi (8 s tik; siradaki olaya 8 s'den az varsa 4/2/1 s)
//   * INT0  D2 TAMPER_N  - ATmega328P power-down'dan yalniz SEVIYE (LOW) kesmesiyle uyanir;
//                          ISR kendini kapatir, pin tekrar HIGH olunca yeniden kurulur.
//   * INT1  D3 MODEM_RI_N - ayni yontem.
//   * PCINT10 A2 TEST_REED_N - PCINT vektorleri SoftwareSerial kutuphanesine aittir
//                          (ISR(PCINT1_vect) orada tanimli). Uyumadan once modem
//                          stopListening() yapildigi icin o ISR bos doner; bize yalniz
//                          uyandirma lazim oldugundan bu yeterlidir. Uyanik iken A2 yoklanir.
#include "power.h"
#include "config.h"
#include "pins.h"
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/power.h>
#include <util/atomic.h>

// Sifirlama nedeni: .bss sifirlanmadan (.init4) once .init3'te yakalanir.
uint8_t g_resetCause __attribute__((section(".noinit")));
void earlyInit(void) __attribute__((naked, used, section(".init3")));
void earlyInit(void) {
  g_resetCause = MCUSR;
  MCUSR = 0;
  wdt_disable();  // WDT sifirlamasindan sonra 16 ms dongusune girmemek icin
}

static volatile uint32_t s_sec = 0;
static volatile uint16_t s_ms = 0;          // < 1000
static volatile uint16_t s_sleepTickMs = 0; // gecerli uykunun tik suresi
static volatile uint8_t s_wake = 0;
static uint32_t s_lastMillis = 0;
static uint16_t s_tick8Ms = WDT_TICK_MS_DEFAULT;

ISR(WDT_vect) {
  uint16_t t = s_ms + s_sleepTickMs;
  while (t >= 1000) {
    t -= 1000;
    s_sec++;
  }
  s_ms = t;
  s_wake |= WAKE_WDT;
}

ISR(INT0_vect) {
  EIMSK &= (uint8_t)~_BV(INT0);
  s_wake |= WAKE_TAMPER;
}

ISR(INT1_vect) {
  EIMSK &= (uint8_t)~_BV(INT1);
  s_wake |= WAKE_RI;
}

static void armExtInterrupts() {
  // Seviye kesmesi: pin hala LOW ise kurma (aksi halde surekli kesme firtinasi).
  if (PIND & _BV(PD2)) {
    EIFR = _BV(INTF0);
    EIMSK |= _BV(INT0);
  }
  if (PIND & _BV(PD3)) {
    EIFR = _BV(INTF1);
    EIMSK |= _BV(INT1);
  }
}

void powerInit() {
  pinMode(PIN_TAMPER_N, INPUT);          // harici 1 MOhm pull-up
  pinMode(PIN_MODEM_RI_N, INPUT);        // seviye cevirici 10k pull-up
  pinMode(PIN_TEST_REED_N, INPUT_PULLUP);
  pinMode(PIN_CHG_STAT_N, INPUT_PULLUP);
  pinMode(PIN_VBAT_SENSE, INPUT);
  pinMode(PIN_SOLAR_SENSE, INPUT);
  DIDR0 = _BV(ADC0D) | _BV(ADC1D);       // analog girislerde dijital tampon kapali
  ACSR = _BV(ACD);                       // analog karsilastirici kapali
  EICRA = 0;                             // INT0/INT1 dusuk seviye
  analogReference(INTERNAL);
  power_spi_disable();
  power_timer1_disable();
#if !DEBUG
  power_usart0_disable();
#endif
  s_lastMillis = millis();
  armExtInterrupts();
}

void clockUpdate() {
  uint32_t m = millis();
  uint32_t d = m - s_lastMillis;
  if (d < 1000) return;  // bolme maliyetini azalt; kalan ms bir sonrakine
  s_lastMillis = m;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    uint32_t t = (uint32_t)s_ms + d;
    s_sec += t / 1000UL;
    s_ms = (uint16_t)(t % 1000UL);
  }
}

uint32_t clockNow() {
  clockUpdate();
  uint32_t v;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { v = s_sec; }
  return v;
}

uint16_t clockTickMs() { return s_tick8Ms; }

void clockCalibrate(uint32_t realElapsedS, uint32_t clockElapsedS) {
  if (clockElapsedS < 3600UL || realElapsedS < 3600UL) return;
  if (realElapsedS > 400000UL || clockElapsedS > 400000UL) return;  // tasma korumasi (~4,6 gun)
  uint32_t t = ((uint32_t)s_tick8Ms * realElapsedS + clockElapsedS / 2) / clockElapsedS;
  if (t < 6400UL) t = 6400UL;
  if (t > 9600UL) t = 9600UL;
  s_tick8Ms = (uint16_t)t;
}

void svcPoll() {
  wdt_reset();
  clockUpdate();
}

void svcDelay(uint16_t ms) {
  uint32_t start = millis();
  while ((uint32_t)(millis() - start) < ms) {
    svcPoll();
  }
}

uint8_t powerTakeWakeFlags() {
  uint8_t f;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    f = s_wake;
    s_wake = 0;
  }
  armExtInterrupts();
  return f;
}

void powerSleep(uint32_t maxSeconds) {
  if (maxSeconds == 0) return;
  uint8_t wdp;
  uint16_t tick;
  if (maxSeconds >= 8) {
    wdp = _BV(WDP3) | _BV(WDP0);
    tick = s_tick8Ms;
  } else if (maxSeconds >= 4) {
    wdp = _BV(WDP3);
    tick = s_tick8Ms / 2;
  } else if (maxSeconds >= 2) {
    wdp = _BV(WDP2) | _BV(WDP1) | _BV(WDP0);
    tick = s_tick8Ms / 4;
  } else {
    wdp = _BV(WDP2) | _BV(WDP1);
    tick = s_tick8Ms / 8;
  }

  clockUpdate();
  uint8_t adcsra = ADCSRA;
  ADCSRA = 0;  // ADC kapali (~100 uA tasarruf)

  cli();
  s_sleepTickMs = tick;
  armExtInterrupts();
  PCIFR = _BV(PCIF1);
  PCMSK1 |= _BV(PCINT10);
  PCICR |= _BV(PCIE1);
  // WDT: yalniz kesme modu
  wdt_reset();
  MCUSR &= (uint8_t)~_BV(WDRF);
  WDTCSR = _BV(WDCE) | _BV(WDE);
  WDTCSR = _BV(WDIE) | wdp;
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  if (s_wake == 0) {
    sleep_enable();
    sleep_bod_disable();
    sei();
    sleep_cpu();
    sleep_disable();
  }
  sei();

  PCMSK1 &= (uint8_t)~_BV(PCINT10);
  // Aktif calisma: 8 s sifirlama modlu WDT
  wdt_reset();
  wdt_enable(WDTO_8S);
  ADCSRA = adcsra;
  // Not: Timer0 power-down'da durdugu icin millis() uyku suresini icermez; uyku suresi
  // yalniz WDT ISR'inde eklenir, uyaniklik suresi clockUpdate() ile millis farkindan gelir.
}

void powerIdle() {
  set_sleep_mode(SLEEP_MODE_IDLE);
  sleep_enable();
  sleep_cpu();  // bir sonraki Timer0 (1 ms) / Timer2 kesmesinde uyanir
  sleep_disable();
  svcPoll();
}

static uint16_t adcSum16(uint8_t pin) {
  analogReference(INTERNAL);
  analogRead(pin);  // referans/kanal oturmasi icin bos okuma
  svcDelay(3);
  analogRead(pin);
  uint16_t sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += (uint16_t)analogRead(pin);
  return sum;  // 16 ornek toplami (en fazla 16368)
}

// V = adc * Vref / 1023 / oran  (SPEC §3), tamsayi: once pin gerilimi 0,1 mV biriminde
static uint16_t toMv(uint16_t sum16, uint16_t vrefMv, uint16_t ratioX10000) {
  uint32_t pin01mV = ((uint32_t)sum16 * vrefMv * 10UL + 8184UL) / 16368UL;  // 16 x 1023
  return (uint16_t)((pin01mV * 1000UL + ratioX10000 / 2) / ratioX10000);
}

uint16_t readVbatMv(uint16_t vrefMv) { return toMv(adcSum16(PIN_VBAT_SENSE), vrefMv, VBAT_DIV_X10000); }

uint16_t readVsolarMv(uint16_t vrefMv) { return toMv(adcSum16(PIN_SOLAR_SENSE), vrefMv, SOLAR_DIV_X10000); }

bool isCharging() { return digitalRead(PIN_CHG_STAT_N) == LOW; }

// NTC bolucu: V = 3300 mV * Rntc / (220k + Rntc), Rntc = 10k*exp(3950*(1/T - 1/298.15))
//  0 C -> 437 mV,  3 C -> 381 mV,  42 C -> 72 mV,  45 C -> 64 mV  (3 C histerezis)
static const uint16_t NTC_COLD_OFF_MV = 437, NTC_COLD_ON_MV = 381;
static const uint16_t NTC_HOT_OFF_MV = 64, NTC_HOT_ON_MV = 72;
static const uint16_t NTC_OPEN_MV = 1000, NTC_SHORT_MV = 20;
static bool s_chgInhibit = false;
static uint8_t s_chgTemp = CHG_TEMP_OK;

uint8_t chargeTempControl(uint16_t vrefMv) {
  uint16_t mv = toMv(adcSum16(PIN_BAT_NTC), vrefMv, 10000);
  if (mv >= NTC_OPEN_MV || mv <= NTC_SHORT_MV) {
    s_chgTemp = CHG_TEMP_FAULT; s_chgInhibit = true;      // NTC kopuk/kisa: guvenli taraf, sarj yok
  } else if (!s_chgInhibit || s_chgTemp == CHG_TEMP_FAULT) {
    if (mv > NTC_COLD_OFF_MV)      { s_chgTemp = CHG_TEMP_COLD; s_chgInhibit = true; }
    else if (mv < NTC_HOT_OFF_MV)  { s_chgTemp = CHG_TEMP_HOT;  s_chgInhibit = true; }
    else                           { s_chgTemp = CHG_TEMP_OK;   s_chgInhibit = false; }
  } else if (mv < NTC_COLD_ON_MV && mv > NTC_HOT_ON_MV) {
    s_chgTemp = CHG_TEMP_OK; s_chgInhibit = false;         // histerezis penceresine dondu
  }
  digitalWrite(PIN_CHG_INHIBIT, s_chgInhibit ? HIGH : LOW);
  return s_chgTemp;
}

bool chargeInhibited() { return s_chgInhibit; }

void sensorRail(bool on) {
  digitalWrite(PIN_SENSOR_PWR_N, on ? LOW : HIGH);
  pinMode(PIN_SENSOR_PWR_N, OUTPUT);
}
