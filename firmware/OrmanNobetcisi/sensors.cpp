// sensors.cpp - Bkz. sensors.h
//
// Neden Adafruit kutuphaneleri yerine dogrudan yazmac surucusu?
//  * Adafruit_BME680 (Bosch BME68x API) ~10 KB flash + dinamik bellek kullanir; 30 KB'lik
//    Pro Mini'de modem/komut kodu ile birlikte %90 sinirini zorlar.
//  * Adafruit_AMG88xx 64 x float (256 B) dizi ister ve AMG8833 uyku modunu (0,2 mA; SPEC §5
//    guc butcesi buna dayanir) yonetmez.
//  Buradaki surucu Bosch BME680 veri sayfasindaki kayan nokta dengeleme formullerini ve
//  Panasonic Grid-EYE yazmac haritasini birebir uygular.
#include "sensors.h"
#include "power.h"
#include "pins.h"
#include "config.h"

// ---------------- AMG8833 ----------------
#define AMG_ADDR         0x69
#define AMG_REG_PCTL     0x00
#define AMG_REG_RST      0x01
#define AMG_REG_FPSC     0x02
#define AMG_REG_PIXEL    0x80
#define AMG_MODE_NORMAL  0x00
#define AMG_MODE_SLEEP   0x10
#define AMG_INITIAL_RST  0x3F

// ---------------- BME680 ----------------
#define BME_ADDR         0x77
#define BME_REG_CHIPID   0xD0
#define BME_CHIPID       0x61
#define BME_REG_RESET    0xE0
#define BME_REG_STATUS   0x1D
#define BME_REG_CTRL_HUM 0x72
#define BME_REG_CTRL_MEAS 0x74
#define BME_REG_CONFIG   0x75
#define BME_REG_CTRL_GAS1 0x71
#define BME_REG_RES_HEAT0 0x5A
#define BME_REG_GAS_WAIT0 0x64
#define BME_HEATER_C     320       // isitici hedef sicakligi
#define BME_HEATER_MS    150       // SPEC §5: 0,15 s

struct BmeCal {
  uint16_t t1; int16_t t2; int8_t t3;
  uint16_t h1, h2; int8_t h3, h4, h5; uint8_t h6; int8_t h7;
  int8_t gh1; int16_t gh2; int8_t gh3;
  uint8_t resHeatRange; int8_t resHeatVal; int8_t rangeSwErr;
};

static BmeCal s_cal;
static bool s_amgOk = false, s_bmeOk = false, s_amgAwake = false;
static uint8_t s_fault = 3;
static uint32_t s_lastRecover = 0;
static uint32_t s_amgStableAt = 0;   // AMG8833: ray acilisindan ~15 s sonra kararli cikis
static int8_t s_ambient = 25;   // isitici hesabi icin ortam sicakligi (C)

// ---------------- I2C (TWI) - yoklamali, zaman asimli minimal surucu ----------------
// Wire kutuphanesi yerine: ~1,3 KB flash ve ~160 B RAM tasarrufu; her bekleme sinirli oldugu icin
// bir slave SDA'yi tutsa bile MCU kilitlenmez (hata -> sensorsRecover ile ray dongusu).
static bool twiWait() {
  uint16_t n = 0;
  while (!(TWCR & _BV(TWINT))) {
    if (++n == 0) return false;  // ~55 ms
  }
  return true;
}

static void twiInit() {
  TWSR = 0;                                   // on bolucu 1
  TWBR = (uint8_t)(((F_CPU / 100000UL) - 16) / 2);  // 100 kHz (kablo ile ayrik kart)
  TWCR = _BV(TWEN);
}

static void twiStop() {
  TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWSTO);
  uint16_t n = 0;
  while ((TWCR & _BV(TWSTO)) && ++n) {
  }
}

static bool twiStart(uint8_t slaRw) {
  TWCR = _BV(TWINT) | _BV(TWSTA) | _BV(TWEN);
  if (!twiWait()) return false;
  uint8_t st = TWSR & 0xF8;
  if (st != 0x08 && st != 0x10) return false;     // START / tekrar START
  TWDR = slaRw;
  TWCR = _BV(TWINT) | _BV(TWEN);
  if (!twiWait()) return false;
  st = TWSR & 0xF8;
  return st == 0x18 || st == 0x40;                // SLA+W ACK / SLA+R ACK
}

static bool twiWrite(uint8_t b) {
  TWDR = b;
  TWCR = _BV(TWINT) | _BV(TWEN);
  return twiWait() && (TWSR & 0xF8) == 0x28;      // veri ACK
}

static bool twiFail() {
  TWCR = 0;            // TWI donanimini sifirla
  TWCR = _BV(TWEN);
  return false;
}

static bool i2cWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  bool ok = twiStart((uint8_t)(addr << 1)) && twiWrite(reg) && twiWrite(val);
  twiStop();
  return ok || twiFail();
}

static bool i2cRead(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t n) {
  bool ok = twiStart((uint8_t)(addr << 1)) && twiWrite(reg) && twiStart((uint8_t)((addr << 1) | 1));
  for (uint8_t i = 0; ok && i < n; i++) {
    TWCR = _BV(TWINT) | _BV(TWEN) | (i + 1 < n ? _BV(TWEA) : 0);  // son bayta NACK
    ok = twiWait();
    buf[i] = TWDR;
  }
  twiStop();
  return ok || twiFail();
}

// SDA LOW'da takili kaldiysa SCL'ye 9 darbe (slave'in yarim kalan baytini bitirmesi icin)
static void i2cBusClear() {
  pinMode(SDA, INPUT);
  pinMode(SCL, INPUT);
  for (uint8_t i = 0; i < 9 && digitalRead(SDA) == LOW; i++) {
    digitalWrite(SCL, LOW);
    pinMode(SCL, OUTPUT);
    delayMicroseconds(6);
    pinMode(SCL, INPUT);  // harici pull-up ile HIGH
    delayMicroseconds(6);
  }
}

// ---------------- AMG8833 ----------------
static bool amgSetMode(uint8_t mode) { return i2cWrite(AMG_ADDR, AMG_REG_PCTL, mode); }

static bool amgInit() {
  if (!amgSetMode(AMG_MODE_NORMAL)) return false;
  svcDelay(50);
  if (!i2cWrite(AMG_ADDR, AMG_REG_RST, AMG_INITIAL_RST)) return false;
  svcDelay(2);
  if (!i2cWrite(AMG_ADDR, AMG_REG_FPSC, 0x00)) return false;  // 10 kare/s
  s_amgAwake = true;
  return true;
}

static bool amgReadPixels(int16_t *px) {
  uint8_t buf[32];
  for (uint8_t chunk = 0; chunk < 4; chunk++) {
    if (!i2cRead(AMG_ADDR, (uint8_t)(AMG_REG_PIXEL + chunk * 32), buf, 32)) return false;
    for (uint8_t i = 0; i < 16; i++) {
      // 12 bit ikiye tumleyen, 0,25 C/LSB
      int16_t raw = (int16_t)(((uint16_t)(buf[2 * i + 1] & 0x0F) << 8) | buf[2 * i]);
      if (raw & 0x0800) raw -= 0x1000;
      px[chunk * 16 + i] = raw;
    }
  }
  return true;
}

// ---------------- BME680 ----------------
static bool bmeInit() {
  uint8_t id = 0;
  if (!i2cRead(BME_ADDR, BME_REG_CHIPID, &id, 1) || id != BME_CHIPID) return false;
  i2cWrite(BME_ADDR, BME_REG_RESET, 0xB6);
  svcDelay(10);
  uint8_t c[41];
  if (!i2cRead(BME_ADDR, 0x89, c, 25) || !i2cRead(BME_ADDR, 0xE1, c + 25, 16)) return false;
  s_cal.t1 = (uint16_t)((c[34] << 8) | c[33]);
  s_cal.t2 = (int16_t)((c[2] << 8) | c[1]);
  s_cal.t3 = (int8_t)c[3];
  s_cal.h1 = (uint16_t)(((uint16_t)c[27] << 4) | (c[26] & 0x0F));
  s_cal.h2 = (uint16_t)(((uint16_t)c[25] << 4) | (c[26] >> 4));
  s_cal.h3 = (int8_t)c[28];
  s_cal.h4 = (int8_t)c[29];
  s_cal.h5 = (int8_t)c[30];
  s_cal.h6 = c[31];
  s_cal.h7 = (int8_t)c[32];
  s_cal.gh1 = (int8_t)c[37];
  s_cal.gh2 = (int16_t)((c[36] << 8) | c[35]);
  s_cal.gh3 = (int8_t)c[38];
  uint8_t v;
  if (!i2cRead(BME_ADDR, 0x02, &v, 1)) return false;
  s_cal.resHeatRange = (uint8_t)((v & 0x30) >> 4);
  if (!i2cRead(BME_ADDR, 0x00, &v, 1)) return false;
  s_cal.resHeatVal = (int8_t)v;
  if (!i2cRead(BME_ADDR, 0x04, &v, 1)) return false;
  s_cal.rangeSwErr = (int8_t)(((int8_t)v & (int8_t)0xF0) / 16);
  return true;
}

// Bosch BME680 tamsayi isitici direnci formulu (hedef C, ortam C)
static uint8_t bmeHeaterRes(uint16_t target, int8_t amb) {
  int32_t var1 = (((int32_t)amb * s_cal.gh3) / 1000) * 256;
  int32_t var2 = ((int32_t)s_cal.gh1 + 784) *
                 (((((int32_t)s_cal.gh2 + 154009L) * (int32_t)target * 5) / 100) + 3276800L) / 10;
  int32_t var3 = var1 + (var2 / 2);
  int32_t var4 = var3 / ((int32_t)s_cal.resHeatRange + 4);
  int32_t var5 = (131L * s_cal.resHeatVal) + 65536L;
  int32_t x100 = ((var4 / var5) - 250) * 34;
  return (uint8_t)((x100 + 50) / 100);
}

static uint8_t bmeHeaterDur(uint16_t ms) {
  uint8_t factor = 0;
  if (ms >= 0xFC0) return 0xFF;
  while (ms > 0x3F) {
    ms /= 4;
    factor++;
  }
  return (uint8_t)(ms + factor * 64);
}

static bool bmeStart() {
  return i2cWrite(BME_ADDR, BME_REG_CTRL_HUM, 0x01) &&                       // nem x1
         i2cWrite(BME_ADDR, BME_REG_CONFIG, 0x00) &&                         // filtre kapali
         i2cWrite(BME_ADDR, BME_REG_RES_HEAT0, bmeHeaterRes(BME_HEATER_C, s_ambient)) &&
         i2cWrite(BME_ADDR, BME_REG_GAS_WAIT0, bmeHeaterDur(BME_HEATER_MS)) &&
         i2cWrite(BME_ADDR, BME_REG_CTRL_GAS1, 0x10) &&                      // run_gas, profil 0
         i2cWrite(BME_ADDR, BME_REG_CTRL_MEAS, (2 << 5) | (0 << 2) | 0x01);  // T x2, P atla (kullanilmiyor), forced
}

static bool bmeRead(Reading *r) {
  uint8_t b[15];
  uint32_t t0 = millis();
  for (;;) {
    if (!i2cRead(BME_ADDR, BME_REG_STATUS, b, 1)) return false;
    if (b[0] & 0x80) break;  // new_data_0
    if ((uint32_t)(millis() - t0) > 500) return false;
    svcDelay(10);
  }
  if (!i2cRead(BME_ADDR, BME_REG_STATUS, b, 15)) return false;
  uint32_t tadc = ((uint32_t)b[5] << 12) | ((uint32_t)b[6] << 4) | (b[7] >> 4);
  uint16_t hadc = (uint16_t)((b[8] << 8) | b[9]);
  uint16_t gadc = (uint16_t)(((uint16_t)b[13] << 2) | (b[14] >> 6));
  uint8_t grange = b[14] & 0x0F;
  bool gasValid = (b[14] & 0x20) && (b[14] & 0x10);  // gas_valid + heat_stab

  // Sicaklik (Bosch tamsayi formulu, 0,01 C)
  int32_t v1 = ((int32_t)tadc >> 3) - ((int32_t)s_cal.t1 << 1);
  int32_t v2 = (v1 * (int32_t)s_cal.t2) >> 11;
  int32_t v3 = ((v1 >> 1) * (v1 >> 1)) >> 12;
  v3 = (v3 * ((int32_t)s_cal.t3 << 4)) >> 14;
  int32_t tFine = v2 + v3;
  int32_t t100 = ((tFine * 5) + 128) >> 8;

  // Nem (Bosch tamsayi formulu, binde %)
  int32_t h1 = ((int32_t)hadc - ((int32_t)s_cal.h1 * 16)) - (((t100 * (int32_t)s_cal.h3) / 100) >> 1);
  int32_t h2 = ((int32_t)s_cal.h2 *
                (((t100 * (int32_t)s_cal.h4) / 100) +
                 (((t100 * ((t100 * (int32_t)s_cal.h5) / 100)) >> 6) / 100) + (int32_t)(1L << 14))) >> 10;
  int32_t h3 = h1 * h2;
  int32_t h4 = (int32_t)s_cal.h6 << 7;
  h4 = (h4 + ((t100 * (int32_t)s_cal.h7) / 100)) >> 4;
  int32_t h5 = ((h3 >> 14) * (h3 >> 14)) >> 10;
  int32_t h6 = (h4 * h5) >> 1;
  int32_t hum = (((h3 + h6) >> 10) * 1000L) >> 12;
  if (hum > 100000L) hum = 100000L;
  if (hum < 0) hum = 0;

  r->temp10 = (int16_t)(t100 / 10);
  r->rh10 = (int16_t)(hum / 100);
  r->envOk = t100 > -4000 && t100 < 8500 && hadc != 0x8000;  // 0x8000: olcum yok

  // Gaz direnci (BME680): R = 8e6 * g2 / (g3 * 2^aralik * (adc - 512 + g2))
  static const int8_t k1x10[16] PROGMEM = {0, 0, 0, 0, 0, -10, 0, -8, 0, 0, -2, -5, 0, -10, 0, 0};
  static const int8_t k2x10[16] PROGMEM = {0, 0, 0, 0, 1, 7, 0, -8, -1, 0, 0, 0, 0, 0, 0, 0};
  if (gasValid) {
    // Tamsayi hali: g2i = 1000*g2, g3i = 1000*g3, D = 1000*(adc - 512 + g2)
    //   R = (8e9 / 1024 / g3i) * q / 2^aralik,   q = 1024 * g2i / D  (~%0,1 hassasiyet)
    int32_t g2i = (1340L + 5L * s_cal.rangeSwErr) * (1000L + (int8_t)pgm_read_byte(&k1x10[grange]));
    uint16_t g3i = (uint16_t)(1000 + (int8_t)pgm_read_byte(&k2x10[grange]));
    int32_t d = ((int32_t)gadc - 512L) * 1000L + g2i;
    if (d > 0 && g2i > 0) {
      uint32_t q = ((uint32_t)g2i << 10) / (uint32_t)d;
      uint32_t res = ((7812500UL / g3i) * q) >> grange;
      r->gasOhm = res;
      r->gasOk = res > 100UL;
    }
  }
  return r->envOk;
}

// ---------------- Genel ----------------
void sensorsRecover() {
  DBGLN("I2C kurtarma: sensor rayi dongusu");
  s_lastRecover = clockNow();
  TWCR = 0;  // TWI kapali; SDA/SCL giris, ic pull-up kapali (kapali sensorleri I/O'dan beslememek icin)
  digitalWrite(SDA, LOW);
  digitalWrite(SCL, LOW);
  pinMode(SDA, INPUT);
  pinMode(SCL, INPUT);
  sensorRail(false);
  svcDelay(300);
  sensorRail(true);
  svcDelay(60);
  i2cBusClear();
  twiInit();
  s_bmeOk = bmeInit();
  s_amgOk = amgInit();
  s_amgStableAt = clockNow() + 15;
  // Ray yeni acildi: bir sonraki olcum tam uyandirma + kare bekleme yapsin
  // (AMG8833 cikisi ray acilisindan ~15 s sonra tam kararli hale gelir).
  s_amgAwake = false;
}

bool sensorsBegin() {
  sensorRail(true);
  svcDelay(60);
  twiInit();
  s_bmeOk = bmeInit();
  s_amgOk = amgInit();
  s_amgStableAt = clockNow() + 15;
  if (!s_bmeOk || !s_amgOk) sensorsRecover();
  if (s_amgOk && amgSetMode(AMG_MODE_SLEEP)) s_amgAwake = false;
  s_fault = (uint8_t)((s_amgOk ? 0 : 1) | (s_bmeOk ? 0 : 2));
  return s_amgOk && s_bmeOk;
}

void sensorsMeasure(Reading *r, uint8_t sens, bool keepAwake) {
  memset(r, 0, sizeof(Reading));
  // Bulunamayan sensor icin en fazla 10 dk'da bir ray dongusu ile yeniden dene
  if ((!s_amgOk || !s_bmeOk) && (clockNow() - s_lastRecover) >= 600UL) sensorsRecover();

  bool amgDone = false, bmeDone = false;
  for (uint8_t attempt = 0; attempt < 2; attempt++) {
    bool bmeStarted = s_bmeOk && bmeStart();
    bool amgReady = false;
    bool wasAsleep = !s_amgAwake;
    if (s_amgOk) {
      if (wasAsleep) {
        amgReady = amgSetMode(AMG_MODE_NORMAL);
        if (amgReady) {
          svcDelay(50);
          amgReady = i2cWrite(AMG_ADDR, AMG_REG_RST, AMG_INITIAL_RST);
          s_amgAwake = amgReady;
        }
      } else {
        amgReady = true;
      }
    }
    if (wasAsleep && amgReady) svcDelay(250);  // ilk 2 kare atlanir (10 kare/s)

    bmeDone = bmeStarted && bmeRead(r);
    amgDone = false;
    if (amgReady) {
      int16_t px[64];
      if (amgReadPixels(px)) {
        thermalStats(px, 64, hotDeltaFor(sens), &r->maxT10, &r->median10, &r->hotCount);
        bool sane = r->maxT10 > -200 && r->maxT10 < 1300 && r->median10 > -300 && r->median10 < 900;
        amgDone = sane;
        // Ray yeni acildiysa cikis henuz kararsiz: puanlamaya sokma (ariza da sayma)
        r->thermalOk = sane && (int32_t)(clockNow() - s_amgStableAt) >= 0;
      }
    }
    if (!keepAwake && s_amgAwake && amgSetMode(AMG_MODE_SLEEP)) s_amgAwake = false;

    bool failed = (s_amgOk && !amgDone) || (s_bmeOk && !bmeDone);
    if (!failed || attempt) break;
    sensorsRecover();
    memset(r, 0, sizeof(Reading));
  }
  if (r->envOk) s_ambient = (int8_t)(r->temp10 / 10);
  s_fault = (uint8_t)((amgDone ? 0 : 1) | (bmeDone ? 0 : 2));
}

uint8_t sensorsFaultMask() { return s_fault; }
