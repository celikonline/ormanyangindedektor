// =============================================================================
//  ORMAN NOBETCISI ON-1 - Firmware
//  Gunes enerjili erken orman yangini algilama dugumu
//  Hedef: ATmega328P @ 8 MHz / 3,3 V (Arduino Pro Mini 3V3 8 MHz)
//  Tek dogru kaynak: SPEC.md (Rev A). Pin/davranis degisikligi once orada yapilir.
// =============================================================================
//
//  Modul yapisi
//    config.h / pins.h   ayarlar ve pin haritasi
//    storage.*           EEPROM ayar yapisi (sihirli sayi + surum + CRC8)       [saf + AVR]
//    textutil.*          SMS metin tamponu, ASCII Turkce, telefon, ag saati     [saf]
//    detector.*          skor, Angstrom indeksi, gaz tabani EMA, artis gecmisi  [saf]
//    commands.*          SMS komut ayristirici, PIN / beyaz liste guvenligi     [saf]
//    power.*             WDT uykusu, saat, kesmeler, ADC (ic 1,1 V), raylar
//    sensors.*           AMG8833 + BME680 dogrudan surucu, I2C kurtarma
//    alarm.*             Timer2 cift flas strob, siren dongusu, susturma
//    modem.*             A7670E guc, AT, SMS, RI/DTR, CSQ, ag saati, arama
//    OrmanNobetcisi.ino  durum makinesi (NORMAL / SUPHE / ALARM + pil modlari)
//
//  [saf] dosyalar Arduino'ya bagimli degildir ve firmware/test altinda PC'de test edilir.
// =============================================================================

#include <avr/wdt.h>
#include "config.h"
#include "pins.h"
#include "compat.h"
#include "textutil.h"
#include "storage.h"
#include "detector.h"
#include "commands.h"
#include "power.h"
#include "sensors.h"
#include "alarm.h"
#include "modem.h"

enum DevState : uint8_t { ST_NORMAL = 0, ST_SUPHE, ST_ALARM };
enum PowerMode : uint8_t { PM_NORMAL = 0, PM_LOW, PM_CRIT };
enum SmsKind : uint8_t { K_ALARM, K_UPDATE, K_END, K_TEST, K_TAMPER, K_LOWBAT, K_CRITBAT, K_BATOK };

#define SMS_MAX 160

// ---------------------------------------------------------------------------
// Durum
// ---------------------------------------------------------------------------
static Settings g_set;
static Detector g_det;
static Reading g_rd;
static DevState g_state = ST_NORMAL;
static PowerMode g_pm = PM_NORMAL;
static uint16_t g_vbat = 0, g_vsol = 0;   // mV
static uint8_t g_chgTemp = CHG_TEMP_OK;   // batarya sicaklik / sarj kesme durumu
static int8_t g_csq = -1;
static char g_sms[SMS_MAX + 1];

static uint32_t g_nextMeas = 0, g_nextSmsPoll = 0, g_nextDaily = 0, g_nextReport = 0;
static uint8_t g_reportHoursSched = 0;
static bool g_smsCheck = false, g_testPending = false;

static uint8_t g_supheN = 0, g_supheHits = 0;

static uint32_t g_zeroSince = 0, g_nextAlarmUpd = 0, g_nextAlarmRetry = 0;
static bool g_zeroActive = false, g_callPending = false;
static uint8_t g_alarmUpdCount = 0, g_alarmPending = 0, g_alarmRetries = 0;

static uint8_t g_cntLow = 0, g_cntCrit = 0, g_cntOk = 0;

static uint8_t g_tamperPulses = 0;
static uint32_t g_tamperWinStart = 0, g_tamperLowSince = 0, g_lastTamperSms = 0;
static bool g_tamperLowActive = false, g_tamperSmsSent = false;

static bool g_install = false, g_reedLatched = false;
static uint32_t g_installUntil = 0;

static bool g_wallValid = false;
static uint32_t g_wallRef = 0, g_clockRef = 0;

// ---------------------------------------------------------------------------
// Yardimcilar
// ---------------------------------------------------------------------------
static inline bool sirenEnabled() { return (g_set.flags & SFLAG_SIREN_EN) != 0; }
static inline bool due(uint32_t now, uint32_t t) { return (int32_t)(now - t) >= 0; }

static void ledBlink(uint8_t n, uint16_t onMs, uint16_t offMs) {
  for (uint8_t i = 0; i < n; i++) {
    digitalWrite(PIN_STATUS_LED, HIGH);
    svcDelay(onMs);
    digitalWrite(PIN_STATUS_LED, LOW);
    if (i + 1 < n) svcDelay(offMs);
  }
}

static uint8_t phoneMask() {
  uint8_t m = 0;
  for (uint8_t i = 0; i < PHONE_SLOTS; i++)
    if (g_set.phones[i][0]) m |= (uint8_t)(1u << i);
  return m;
}

// g_sms metnini maskedeki numaralara gonderir; basarisiz olanlarin maskesini dondurur.
static uint8_t smsToMask(uint8_t mask) {
  uint8_t failed = 0;
  for (uint8_t i = 0; i < PHONE_SLOTS; i++) {
    if (!(mask & (1u << i)) || !g_set.phones[i][0]) continue;
    if (!modemSendSms(g_set.phones[i], g_sms)) failed |= (uint8_t)(1u << i);
  }
  return failed;
}

static void readPower() {
  g_vbat = readVbatMv(g_set.vrefMv);
  g_vsol = readVsolarMv(g_set.vrefMv);
  g_chgTemp = chargeTempControl(g_set.vrefMv);
}

// ---------------------------------------------------------------------------
// SMS metinleri (ASCII, <= 160)
// ---------------------------------------------------------------------------
static void addIdName(TextBuf &tb) {
  cmdAddDeviceId(tb, g_set.deviceId);
  if (g_set.name[0]) {
    tb.add(g_set.name);
    tb.addChar(' ');
  }
}

static void addLocation(TextBuf &tb) {
  if (g_set.location[0]) {
    tb.addP(PSTR("maps.google.com/?q="));
    tb.add(g_set.location);
  } else {
    tb.addP(PSTR("Konum:YOK"));
  }
  tb.addChar(' ');
}

static void addGas(TextBuf &tb) {
  tb.addP(PSTR("Gaz:"));
  if (g_rd.gasOk && g_det.gasPm >= 0) {
    tb.addChar('%');
    int16_t p = (int16_t)((g_det.gasPm + 5) / 10);
    tb.addInt(p > 999 ? 999 : p);
  } else {
    tb.addChar('-');
  }
  tb.addChar(' ');
}

static void addAir(TextBuf &tb) {
  tb.addP(PSTR("Hava:"));
  if (g_rd.envOk) {
    tb.addInt(roundX10(g_rd.temp10));
    tb.addP(PSTR("C/%"));
    tb.addInt(roundX10(g_rd.rh10));
  } else {
    tb.addChar('-');
  }
  tb.addChar(' ');
}

// "Pil:3.95V/%80 Gunes:5.2V"
static void addBattery(TextBuf &tb) {
  tb.addP(PSTR("Pil:"));
  tb.addDec((g_vbat + 5) / 10, 2);
  tb.addP(PSTR("V/%"));
  tb.addInt(batteryPercent(g_vbat));
  tb.addP(PSTR(" Gunes:"));
  tb.addDec((g_vsol + 50) / 100, 1);
  tb.addChar('V');
}

// SPEC §6.4 bicimi:
// YANGIN ALARMI! ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:78C Gaz:%38 Hava:41C/%12 Pil:%86 Skor:6
static void buildEventSms(TextBuf &tb, uint8_t kind) {
  tb.clear();
  switch (kind) {
    case K_ALARM: tb.addP(PSTR("YANGIN ALARMI! ")); break;
    case K_UPDATE:
      tb.addP(PSTR("YANGIN DEVAM "));
      tb.addInt(g_alarmUpdCount);
      tb.addP(PSTR("/4! "));
      break;
    case K_END: tb.addP(PSTR("YANGIN BELIRTISI SONA ERDI ")); break;
    case K_TEST: tb.addP(PSTR("TEST OK ")); break;
    case K_TAMPER: tb.addP(PSTR("KURCALAMA UYARISI! ")); break;
    case K_LOWBAT: tb.addP(PSTR("DUSUK PIL UYARISI ")); break;
    case K_CRITBAT: tb.addP(PSTR("KRITIK PIL! ")); break;
    default: tb.addP(PSTR("PIL NORMALE DONDU ")); break;
  }
  addIdName(tb);

  if (kind >= K_LOWBAT) {
    addBattery(tb);
    if (kind == K_LOWBAT) tb.addP(PSTR(" Tasarruf modu"));
    if (kind == K_CRITBAT) tb.addP(PSTR(" Modem kapaniyor, yalniz algilama"));
    return;
  }

  addLocation(tb);
  if (kind != K_TAMPER) {
    tb.addP(PSTR("Termal:"));
    if (g_rd.thermalOk) tb.addInt(roundX10(g_rd.maxT10));
    else tb.addChar('-');
    tb.addP(PSTR("C "));
    addGas(tb);
    addAir(tb);
  }
  tb.addP(PSTR("Pil:%"));
  tb.addInt(batteryPercent(g_vbat));
  if (kind == K_TEST) {
    tb.addP(PSTR(" Sinyal:"));
    tb.addInt(g_csq);
  }
  if (kind != K_TAMPER) {
    tb.addP(PSTR(" Skor:"));
    tb.addInt(g_det.score);
  }
}

// DURUM / RAPOR
static void buildStatus(TextBuf &tb, const char *headP) {
  tb.clear();
  tb.addP(headP);
  addIdName(tb);
  tb.addP(g_state == ST_ALARM ? PSTR("ALARM") : (g_state == ST_SUPHE ? PSTR("SUPHE") : PSTR("NORMAL")));
  if (g_pm == PM_LOW) tb.addP(PSTR(" DUSUK PIL"));
  if (g_pm == PM_CRIT) tb.addP(PSTR(" KRITIK PIL"));
  tb.addP(PSTR(" Termal:"));
  if (g_rd.thermalOk) {
    tb.addInt(roundX10(g_rd.maxT10));
    tb.addChar('/');
    tb.addInt(roundX10(g_rd.median10));
    tb.addP(PSTR("C "));
  } else {
    tb.addP(PSTR("HATA "));
  }
  addGas(tb);
  addAir(tb);
  if (g_rd.envOk) {
    int16_t idx = angstromIndex100(g_rd.rh10, g_rd.temp10);
    tb.addP(PSTR("Risk:"));
    tb.addP(riskNameP(angstromLevel(idx)));
    tb.addChar('(');
    tb.addDec((idx + (idx >= 0 ? 5 : -5)) / 10, 1);
    tb.addP(PSTR(") "));
  }
  addBattery(tb);
  if (g_chgTemp == CHG_TEMP_HOT) tb.addP(PSTR(" Sarj:SICAK"));
  else if (g_chgTemp == CHG_TEMP_COLD) tb.addP(PSTR(" Sarj:SOGUK"));
  else if (g_chgTemp == CHG_TEMP_FAULT) tb.addP(PSTR(" Sarj:NTC?"));
  else tb.addP(isCharging() ? PSTR(" Sarj:E") : PSTR(" Sarj:H"));
  tb.addP(PSTR(" Sinyal:"));
  tb.addInt(g_csq);
  tb.addP(PSTR(" Skor:"));
  tb.addInt(g_det.score);
  if (alarmMuted(clockNow())) tb.addP(PSTR(" SESSIZ"));
  if (!sirenEnabled()) tb.addP(PSTR(" SirenKapali"));
  if (g_wallValid) {
    uint32_t w = g_wallRef + (clockNow() - g_clockRef);
    uint32_t sod = w % 86400UL;
    tb.addP(PSTR(" Saat:"));
    tb.addUintPad((uint16_t)(sod / 3600UL), 2);
    tb.addChar(':');
    tb.addUintPad((uint16_t)((sod / 60UL) % 60UL), 2);
  }
}

// ---------------------------------------------------------------------------
// Alarm akisi
// ---------------------------------------------------------------------------
static void deliverAlarm(uint32_t now) {
  if (!g_alarmPending && !g_callPending) return;
  g_alarmRetries++;
  g_nextAlarmRetry = now + ALARM_SMS_RETRY_S;
  if (modemEnsure(true)) {  // KRITIK pilde bile denenir (SPEC §5)
    TextBuf tb(g_sms, SMS_MAX);
    buildEventSms(tb, K_ALARM);
    g_alarmPending = smsToMask(g_alarmPending);
    if (g_callPending) {
      modemCall(g_set.phones[0], CALL_RING_S);
      g_callPending = false;
    }
  }
  if (g_alarmRetries >= ALARM_SMS_RETRY_MAX) {
    g_alarmPending = 0;
    g_callPending = false;
  }
}

static void enterAlarm(uint32_t now) {
  DBGLN(">>> ALARM");
  g_state = ST_ALARM;
  g_zeroActive = false;
  g_alarmUpdCount = 0;
  g_nextAlarmUpd = now + ALARM_UPDATE_INTERVAL_S;
  alarmStart(now);
  alarmUpdate(now, sirenEnabled());  // isik + siren hemen
  g_alarmPending = phoneMask();
  g_alarmRetries = 0;
  g_callPending = (g_set.flags & SFLAG_CALL_EN) && g_set.phones[0][0];
  deliverAlarm(now);
}

static void endAlarm(bool sendSms) {
  DBGLN("<<< ALARM BITTI");
  alarmStop();
  g_state = ST_NORMAL;
  g_alarmPending = 0;
  g_callPending = false;
  g_zeroActive = false;
  if (sendSms && phoneMask() && modemEnsure(true)) {
    TextBuf tb(g_sms, SMS_MAX);
    buildEventSms(tb, K_END);
    smsToMask(phoneMask());
  }
  if (g_pm == PM_CRIT) modemPowerOff();
}

// ---------------------------------------------------------------------------
// Pil modlari (SPEC §5)
// ---------------------------------------------------------------------------
static void sendEventToAll(uint8_t kind) {
  if (!phoneMask()) return;
  TextBuf tb(g_sms, SMS_MAX);
  buildEventSms(tb, kind);
  smsToMask(phoneMask());
}

static void updatePowerMode() {
  if (alarmOutputsActive()) return;  // LED/siren yukunde gerilim sarkar; karar verme
  bool crit = g_pm != PM_CRIT && g_vbat < BATT_CRIT_MV;
  bool low = g_pm == PM_NORMAL && g_vbat < BATT_LOW_MV && !crit;
  bool ok = g_pm != PM_NORMAL && g_vbat > BATT_OK_MV;
  g_cntCrit = crit ? (uint8_t)(g_cntCrit + 1) : 0;
  g_cntLow = low ? (uint8_t)(g_cntLow + 1) : 0;
  g_cntOk = ok ? (uint8_t)(g_cntOk + 1) : 0;

  if (g_cntCrit >= BATT_CONFIRM_CNT) {
    g_pm = PM_CRIT;
    if (modemEnsure(false)) sendEventToAll(K_CRITBAT);
    if (g_state != ST_ALARM) modemPowerOff();
  } else if (g_cntLow >= BATT_CONFIRM_CNT) {
    g_pm = PM_LOW;
    if (modemEnsure(false)) sendEventToAll(K_LOWBAT);
  } else if (g_cntOk >= BATT_CONFIRM_CNT) {
    g_pm = PM_NORMAL;
    if (modemEnsure(false) && g_set.phones[0][0]) {
      TextBuf tb(g_sms, SMS_MAX);
      buildEventSms(tb, K_BATOK);
      smsToMask(0x01);
      g_smsCheck = true;
    }
  } else {
    return;
  }
  g_cntCrit = g_cntLow = g_cntOk = 0;
}

// ---------------------------------------------------------------------------
// Olcum ve durum makinesi (SPEC §6.1)
// ---------------------------------------------------------------------------
static uint16_t measPeriod() {
  if (g_state == ST_SUPHE || g_install) return MEAS_PERIOD_SUPHE_S;
  if (g_state == ST_ALARM) return MEAS_PERIOD_ALARM_S;
  uint16_t p = MEAS_PERIOD_NORMAL_S;
  if (g_rd.envOk && angstromLevel(angstromIndex100(g_rd.rh10, g_rd.temp10)) == RISK_VERY_HIGH)
    p = MEAS_PERIOD_HIGHRISK_S;
  if (g_pm != PM_NORMAL) p *= LOWPOWER_PERIOD_FACTOR;
  return p;
}

static void statusBlink(uint8_t score) {
  if (g_state == ST_ALARM) return;  // durum LED'i strobu takip ediyor
  if (g_install) {                  // kurulum: uzun + skor kadar kisa (nisan alma yardimi)
    ledBlink(1, 400, 0);
    if (score) {
      svcDelay(250);
      ledBlink(score > 8 ? 8 : score, 120, 200);
    }
    return;
  }
  if (g_state == ST_SUPHE) {
    ledBlink(1, 300, 0);
    return;
  }
  uint8_t code = 1;                                     // 1: her sey yolunda
  if (g_pm != PM_NORMAL) code = 4;                      // 4: dusuk/kritik pil
  else if (sensorsFaultMask()) code = 3;                // 3: sensor hatasi
  else if (!modemIsOn() || modemInBackoff()) code = 2;  // 2: modem/sebeke yok
  ledBlink(code, 30, 250);
}

static void measurementCycle(uint32_t now) {
  bool keepAwake = g_state != ST_NORMAL || g_install;
  readPower();  // yuk yokken (modem uykuda, LED kapali) olc
  sensorsMeasure(&g_rd, g_set.sens, keepAwake);
  uint8_t score = detEvaluate(&g_det, &g_rd, now, g_set.sens, g_state == ST_NORMAL);
  DBG("Skor=");
  DBGV(score);
  DBG(" maxT10=");
  DBGV(g_rd.maxT10);
  DBG(" T10=");
  DBGV(g_rd.temp10);
  DBG(" RH10=");
  DBGV(g_rd.rh10);
  DBG(" gaz_pm=");
  DBGVLN(g_det.gasPm);

  switch (g_state) {
    case ST_NORMAL:
      if (score >= SCORE_ALARM) {
        enterAlarm(now);
      } else if (score >= SCORE_SUPHE) {
        DBGLN("> SUPHE");
        g_state = ST_SUPHE;
        g_supheN = 0;
        g_supheHits = 0;
      }
      break;
    case ST_SUPHE:
      g_supheN++;
      if (score >= SCORE_CONFIRM) g_supheHits++;
      if (score >= SCORE_ALARM || g_supheHits >= SUPHE_CONFIRM_HITS) enterAlarm(now);
      else if (g_supheN >= SUPHE_SAMPLES) g_state = ST_NORMAL;
      break;
    case ST_ALARM:
      if (score == 0) {
        if (!g_zeroActive) {
          g_zeroActive = true;
          g_zeroSince = now;
        } else if (now - g_zeroSince >= ALARM_CLEAR_S) {
          endAlarm(true);
        }
      } else {
        g_zeroActive = false;
      }
      break;
  }

  updatePowerMode();
  statusBlink(score);
  g_nextMeas = clockNow() + measPeriod();
}

// ---------------------------------------------------------------------------
// Test (TEST komutu / miknatis)
// ---------------------------------------------------------------------------
static void runTest() {
  g_testPending = false;
  DBGLN("TEST");
  alarmTest(sirenEnabled());
  uint32_t t0 = millis();
  while ((uint32_t)(millis() - t0) < TEST_DURATION_MS + 20) {
    alarmUpdate(clockNow(), sirenEnabled());
    powerIdle();
  }
  alarmUpdate(clockNow(), sirenEnabled());
  if (g_pm != PM_CRIT && phoneMask() && modemEnsure(false)) {  // kritik pilde yalniz yerel test
    g_csq = modemSignal();
    TextBuf tb(g_sms, SMS_MAX);
    buildEventSms(tb, K_TEST);
    smsToMask(phoneMask());
  }
}

// ---------------------------------------------------------------------------
// SMS komutlari
// ---------------------------------------------------------------------------
static void hookStatus(TextBuf &tb) {
  int8_t q = modemSignal();
  if (q >= 0) g_csq = q;
  buildStatus(tb, PSTR("DURUM "));
}

static void hookAction(uint8_t act, uint16_t arg) {
  uint32_t now = clockNow();
  switch (act) {
    case ACT_TEST: g_testPending = true; break;
    case ACT_MUTE: alarmMute(now, arg); break;
    case ACT_CALIBRATE: detCalibrateGas(&g_det); break;
    case ACT_RESET:
      if (g_state == ST_ALARM) endAlarm(false);
      g_state = ST_NORMAL;
      alarmMute(now, 0);
      break;
  }
}

static const CmdHooks kHooks = {hookStatus, hookAction};

static void processIncomingSms() {
  g_smsCheck = false;
  if (g_pm == PM_CRIT && !modemIsOn()) return;  // kritik pilde modem kapali
  if (!modemEnsure(false)) return;
  char text[LINE_TEXT_MAX];
  char sender[PHONE_LEN + 4];
  for (uint8_t i = 0; i < SMS_PER_WAKE_MAX; i++) {
    uint16_t idx;
    if (!modemReadFirstSms(&idx, sender, sizeof(sender), text, sizeof(text))) break;
    modemDeleteSms(idx);  // once sil: hatali mesaj dongu yaratmasin
    DBG("SMS <- ");
    DBGV(sender);
    DBG(": ");
    DBGVLN(text);
    TextBuf tb(g_sms, SMS_MAX);
    uint8_t r = cmdProcess(text, sender, &g_set, &kHooks, tb);
    if (r & CMDR_SAVE) settingsSave(&g_set);
    if ((r & CMDR_REPLY) && tb.length()) modemSendSms(sender, g_sms);
  }
}

// ---------------------------------------------------------------------------
// Kurcalama ve test reed
// ---------------------------------------------------------------------------
static void tamperCheck(uint32_t now, bool edge) {
  static uint32_t lastEdgeMs = 0;
  if (edge && (uint32_t)(millis() - lastEdgeMs) >= 1000UL) {  // ayni sarsintinin sekmelerini tek say
    lastEdgeMs = millis();
    if (now - g_tamperWinStart > TAMPER_WINDOW_S) {
      g_tamperWinStart = now;
      g_tamperPulses = 0;
    }
    if (g_tamperPulses < 255) g_tamperPulses++;
  }
  bool held = false;
  if (digitalRead(PIN_TAMPER_N) == LOW) {
    if (!g_tamperLowActive) {
      g_tamperLowActive = true;
      g_tamperLowSince = now;
    } else if (now - g_tamperLowSince >= TAMPER_HOLD_S) {
      held = true;
    }
  } else {
    g_tamperLowActive = false;
  }
  if (!(held || g_tamperPulses >= TAMPER_PULSES)) return;
  g_tamperPulses = 0;
  g_tamperLowSince = now;
  if (g_install || g_pm == PM_CRIT) return;  // kurulumda beklenen durum; kritik pilde modem kapali
  if (g_tamperSmsSent && now - g_lastTamperSms < TAMPER_SMS_MIN_INTERVAL_S) return;
  if (!phoneMask() || !modemEnsure(false)) return;
  g_tamperSmsSent = true;
  g_lastTamperSms = now;
  sendEventToAll(K_TAMPER);
}

static void checkReed() {
  if (digitalRead(PIN_TEST_REED_N) != LOW) {
    g_reedLatched = false;
    return;
  }
  if (g_reedLatched) return;
  digitalWrite(PIN_STATUS_LED, HIGH);  // miknatis algilandi
  uint32_t t0 = millis();
  bool held = true;
  while ((uint32_t)(millis() - t0) < REED_HOLD_MS) {
    svcPoll();
    if (digitalRead(PIN_TEST_REED_N) != LOW) {
      held = false;
      break;
    }
  }
  digitalWrite(PIN_STATUS_LED, LOW);
  if (!held) return;
  g_reedLatched = true;
  g_install = true;
  g_installUntil = clockNow() + INSTALL_MODE_S;
  g_testPending = true;
  g_nextMeas = clockNow() + 1;
}

// ---------------------------------------------------------------------------
// Periyodik isler
// ---------------------------------------------------------------------------
static void syncTime() {
  uint32_t wall;
  if (!modemNetworkTime(&wall)) return;
  uint32_t now = clockNow();
  if (g_wallValid) clockCalibrate(wall - g_wallRef, now - g_clockRef);
  g_wallRef = wall;
  g_clockRef = now;
  g_wallValid = true;
}

static void housekeeping(uint32_t now) {
  if (g_install && due(now, g_installUntil)) g_install = false;

  if (g_state == ST_ALARM) {
    if ((g_alarmPending || g_callPending) && due(now, g_nextAlarmRetry)) deliverAlarm(now);
    if (g_alarmUpdCount < ALARM_UPDATE_MAX && due(now, g_nextAlarmUpd)) {
      g_alarmUpdCount++;
      g_nextAlarmUpd += ALARM_UPDATE_INTERVAL_S;
      if (phoneMask() && modemEnsure(true)) {
        TextBuf tb(g_sms, SMS_MAX);
        buildEventSms(tb, K_UPDATE);
        smsToMask(phoneMask());
      }
    }
  }

  if (due(now, g_nextSmsPoll)) {
    g_nextSmsPoll = now + SMS_POLL_INTERVAL_S;
    g_smsCheck = true;
  }
  if (g_smsCheck) processIncomingSms();

  if (g_reportHoursSched != g_set.reportHours) {  // RAPOR komutu ile degisti
    g_reportHoursSched = g_set.reportHours;
    g_nextReport = now + (uint32_t)g_set.reportHours * 3600UL;
  }
  if (g_set.reportHours && due(now, g_nextReport)) {
    g_nextReport = now + (uint32_t)g_set.reportHours * 3600UL;
    if (g_pm != PM_CRIT && g_set.phones[0][0] && modemEnsure(false)) {
      g_csq = modemSignal();
      TextBuf tb(g_sms, SMS_MAX);
      buildStatus(tb, PSTR("RAPOR "));
      modemSendSms(g_set.phones[0], g_sms);
    }
  }

  if (due(now, g_nextDaily)) {
    g_nextDaily = now + DAILY_INTERVAL_S;
    if (g_pm != PM_CRIT && modemEnsure(false)) {
      int8_t q = modemSignal();
      if (q >= 0) g_csq = q;
      syncTime();
    }
  }

  // Kritik pilde modem yalniz alarm icin acilir; is bitince kapat (SPEC §5)
  if (g_pm == PM_CRIT && g_state != ST_ALARM && modemIsOn()) modemPowerOff();
}

// ---------------------------------------------------------------------------
// Arduino
// ---------------------------------------------------------------------------
void setup() {
  digitalWrite(PIN_STATUS_LED, LOW);
  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_CHG_INHIBIT, LOW);   // varsayilan: sarja izin ver (NTC ilk olcumde kontrol edilir)
  pinMode(PIN_CHG_INHIBIT, OUTPUT);
  modemBegin();
  alarmInit();
#if DEBUG
  Serial.begin(DEBUG_BAUD);
  Serial.print(F("\r\nOrman Nobetcisi ON-1 v" FW_VERSION " reset=0x"));
  Serial.println(g_resetCause, HEX);
#endif
  powerInit();
  wdt_enable(WDTO_8S);

  if (!settingsLoad(&g_set)) settingsSave(&g_set);  // bozuk/bos EEPROM -> varsayilanlar

  digitalWrite(PIN_STATUS_LED, HIGH);  // acilis: 1 s yanar
  svcDelay(1000);
  digitalWrite(PIN_STATUS_LED, LOW);

  if (!sensorsBegin()) ledBlink(3, 100, 150);

  uint32_t now = clockNow();
  detInit(&g_det, now);
  readPower();
  g_pm = g_vbat < BATT_CRIT_MV ? PM_CRIT : (g_vbat < BATT_LOW_MV ? PM_LOW : PM_NORMAL);

  if (g_pm != PM_CRIT) {
    if (modemEnsure(false)) {
      bool net = modemWaitNetwork(MODEM_NET_WAIT_S);
      int8_t q = modemSignal();
      if (q >= 0) g_csq = q;
      if (net) syncTime();
      ledBlink(net ? 2 : 5, 80, 120);  // 2: sebeke tamam, 5: sebeke yok
      g_smsCheck = true;               // acilista SIM'de bekleyen komutlari isle
    } else {
      ledBlink(5, 80, 120);
    }
  }

  now = clockNow();
  g_nextMeas = now;
  g_nextSmsPoll = now + SMS_POLL_INTERVAL_S;
  g_nextDaily = now + DAILY_INTERVAL_S;
  g_reportHoursSched = g_set.reportHours;
  g_nextReport = now + (uint32_t)g_set.reportHours * 3600UL;
}

void loop() {
  svcPoll();
  uint8_t wf = powerTakeWakeFlags();
  if (wf & WAKE_RI) g_smsCheck = true;

  uint32_t now = clockNow();
  checkReed();
  tamperCheck(now, (wf & WAKE_TAMPER) != 0);

  if (due(now, g_nextMeas)) measurementCycle(now);
  if (g_testPending) runTest();

  now = clockNow();
  housekeeping(now);
  alarmUpdate(clockNow(), sirenEnabled());

  // --- Uyku ---
  if (alarmOutputsActive()) {
    powerIdle();  // strob/siren: Timer2 calismali -> idle
    return;
  }
  now = clockNow();
  if (g_smsCheck || g_testPending || due(now, g_nextMeas)) return;
  modemSleep();
  powerSleep(g_nextMeas - now);
}
