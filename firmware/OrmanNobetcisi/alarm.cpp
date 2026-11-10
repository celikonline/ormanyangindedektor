// alarm.cpp - Bkz. alarm.h
//
// Strob deseni (SPEC §4.5): 60 ms acik / 90 ms kapali / 60 ms acik / 790 ms kapali = 1 s, ~%12 gorev.
// Timer2 CTC, 8 MHz / 1024 / 78 = 100,16 Hz (10 ms tik) ISR'i deseni surer; boylece modem/sensor
// beklemeleri (SMS gonderimi saniyeler surebilir) strobu hic bozmaz. Timer2 idle uykuda calisir.
#include "alarm.h"
#include "config.h"
#include "pins.h"

#define STROBE_PERIOD_TICKS 100   // 1000 ms
#define STROBE_ON1_END        6   //   0- 60 ms acik
#define STROBE_ON2_START     15   // 150-210 ms acik
#define STROBE_ON2_END       21

static volatile uint8_t s_tick = 0;
static bool s_strobeOn = false;
static bool s_sirenOn = false;
static bool s_session = false;
static uint32_t s_start = 0;
static uint32_t s_muteUntil = 0;
static bool s_testActive = false;
static bool s_testSiren = false;
static uint32_t s_testStartMs = 0;

ISR(TIMER2_COMPA_vect) {
  uint8_t t = s_tick;
  bool on = (t < STROBE_ON1_END) || (t >= STROBE_ON2_START && t < STROBE_ON2_END);
  if (on) {
    STROBE_PORT |= _BV(STROBE_BIT);
    SLED_PORT |= _BV(SLED_BIT);   // durum LED'i strobu takip eder
  } else {
    STROBE_PORT &= (uint8_t)~_BV(STROBE_BIT);
    SLED_PORT &= (uint8_t)~_BV(SLED_BIT);
  }
  if (++t >= STROBE_PERIOD_TICKS) t = 0;
  s_tick = t;
}

static void strobe(bool on) {
  if (on == s_strobeOn) return;
  s_strobeOn = on;
  if (on) {
    s_tick = 0;
    TCCR2A = _BV(WGM21);                          // CTC
    TCNT2 = 0;
    OCR2A = 77;                                   // 100,16 Hz
    TIFR2 = _BV(OCF2A);
    TIMSK2 = _BV(OCIE2A);
    TCCR2B = _BV(CS22) | _BV(CS21) | _BV(CS20);   // /1024
  } else {
    TIMSK2 = 0;
    TCCR2B = 0;
    digitalWrite(PIN_LED_STROBE, LOW);
    digitalWrite(PIN_STATUS_LED, LOW);
  }
}

static void siren(bool on) {
  if (on == s_sirenOn) return;
  s_sirenOn = on;
  digitalWrite(PIN_SIREN_EN, on ? HIGH : LOW);
}

void alarmInit() {
  digitalWrite(PIN_LED_STROBE, LOW);
  pinMode(PIN_LED_STROBE, OUTPUT);
  digitalWrite(PIN_SIREN_EN, LOW);
  pinMode(PIN_SIREN_EN, OUTPUT);
  TIMSK2 = 0;
  TCCR2B = 0;
}

void alarmStart(uint32_t now) {
  s_session = true;
  s_start = now;  // cikislar bir sonraki alarmUpdate() cagrisinda (ayarlara gore) acilir
}

void alarmStop() {
  s_session = false;
  s_testActive = false;
  s_muteUntil = 0;
  strobe(false);
  siren(false);
}

void alarmMute(uint32_t now, uint16_t minutes) { s_muteUntil = minutes ? now + (uint32_t)minutes * 60UL : 0; }

bool alarmMuted(uint32_t now) { return s_muteUntil && (int32_t)(s_muteUntil - now) > 0; }

void alarmTest(bool sirenAllowed) {
  s_testActive = true;
  s_testSiren = sirenAllowed;
  s_testStartMs = millis();
}

void alarmUpdate(uint32_t now, bool sirenEnabled) {
  bool light = false, snd = false;
  if (s_session) {
    uint32_t el = now - s_start;
    if (el < LIGHT_TOTAL_S) light = true;
    if (sirenEnabled && el < SIREN_TOTAL_S && (el % (SIREN_ON_S + SIREN_OFF_S)) < SIREN_ON_S) snd = true;
    if (alarmMuted(now)) light = snd = false;
  }
  if (s_testActive) {
    if ((uint32_t)(millis() - s_testStartMs) < TEST_DURATION_MS) {
      light = true;
      if (s_testSiren) snd = true;
    } else {
      s_testActive = false;
    }
  }
  strobe(light);
  siren(snd);
}

bool alarmSessionActive() { return s_session; }

bool alarmOutputsActive() { return s_strobeOn || s_sirenOn || s_testActive; }
