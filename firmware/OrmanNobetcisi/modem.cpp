// modem.cpp - Bkz. modem.h
//
// Notlar:
//  * SoftwareSerial 9600 bps (8 MHz'de guvenilir ust sinir). A7670E fabrika hizi 115200 oldugundan
//    ilk acilista 9600'de yanit yoksa 115200'de "AT+IPR=9600" gonderilir (yalniz TX gerekir).
//  * Tum yanitlar satir satir AKAN bicimde okunur; 64 baytlik SoftwareSerial tamponu tasmaz.
//  * Bekleme donguleri svcPoll() cagirir (WDT besleme + saat). Strob Timer2 ISR'de calistigi icin
//    SMS gonderimi sirasinda yerel alarm deseni bozulmaz.
//  * URC metinlerine guvenilmez: RI veya periyodik yoklamada AT+CMGL ile SIM taranir.
#include "modem.h"
#include "config.h"
#include "pins.h"
#include "power.h"
#include "textutil.h"
#include <SoftwareSerial.h>

#define AT_OK       0
#define AT_ERROR    1
#define AT_TIMEOUT  2
#define LINE_MAX    120   // UCS2 hex kodlu ~28 karakterlik komutlari da tasir

typedef void (*LineCb)(char *line, void *ctx);

static SoftwareSerial ss(PIN_MODEM_RX, PIN_MODEM_TX);
static bool s_on = false;
static bool s_ready = false;
static bool s_backoff = false;
static uint32_t s_backoffUntil = 0;

// ---------------------------------------------------------------------------
// Dusuk seviye
// ---------------------------------------------------------------------------
static void flushInput() {
  while (ss.available()) ss.read();
}

static bool readLine(char *buf, uint8_t size, uint32_t start, uint32_t timeout) {
  uint8_t n = 0;
  while ((uint32_t)(millis() - start) < timeout) {
    svcPoll();
    int c = ss.read();
    if (c < 0) continue;
    if (c == '\r') continue;
    if (c == '\n') {
      if (n == 0) continue;
      buf[n] = 0;
      return true;
    }
    if (n < size - 1) buf[n++] = (char)c;
  }
  return false;
}

static uint8_t atWait(uint32_t timeout, LineCb cb, void *ctx) {
  char line[LINE_MAX];
  uint32_t start = millis();
  while (readLine(line, sizeof(line), start, timeout)) {
    if (!strcmp_P(line, PSTR("OK"))) return AT_OK;
    if (!strcmp_P(line, PSTR("ERROR")) || !strncmp_P(line, PSTR("+CME ERROR"), 10) ||
        !strncmp_P(line, PSTR("+CMS ERROR"), 10))
      return AT_ERROR;
    if (cb) cb(line, ctx);
  }
  return AT_TIMEOUT;
}

// cmdP: PROGMEM komut (\r eklenir)
static uint8_t atCmd(const char *cmdP, uint32_t timeout, LineCb cb = 0, void *ctx = 0) {
  flushInput();
  ss.print((const __FlashStringHelper *)cmdP);
  ss.print('\r');
  return atWait(timeout, cb, ctx);
}

static bool waitPrompt(uint32_t timeout) {
  uint32_t start = millis();
  while ((uint32_t)(millis() - start) < timeout) {
    svcPoll();
    if (ss.read() == '>') return true;
  }
  return false;
}

static bool alive(uint8_t tries, uint16_t eachMs) {
  for (uint8_t i = 0; i < tries; i++) {
    if (atCmd(PSTR("AT"), eachMs) == AT_OK) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Guc
// ---------------------------------------------------------------------------
void modemBegin() {
  digitalWrite(PIN_MODEM_PWR_EN, LOW);
  pinMode(PIN_MODEM_PWR_EN, OUTPUT);
  digitalWrite(PIN_MODEM_PWRKEY, LOW);
  pinMode(PIN_MODEM_PWRKEY, OUTPUT);
  digitalWrite(PIN_MODEM_DTR, HIGH);   // HV tarafi 10k pull-up: HIGH'ta akim cekmez
  pinMode(PIN_MODEM_DTR, OUTPUT);
  ss.begin(MODEM_BAUD);
  ss.stopListening();
}

static void hardOff() {
  if (s_on && s_ready) {
    atCmd(PSTR("AT+CPOF"), 3000);
    svcDelay(2000);
  }
  digitalWrite(PIN_MODEM_PWRKEY, LOW);
  digitalWrite(PIN_MODEM_PWR_EN, LOW);
  digitalWrite(PIN_MODEM_DTR, HIGH);
  ss.stopListening();
  s_on = false;
  s_ready = false;
}

void modemPowerOff() {
  if (s_on) {
    digitalWrite(PIN_MODEM_DTR, LOW);
    ss.listen();
    svcDelay(60);
  }
  hardOff();
}

// Yapilandirma: '!' ile baslayanlar zorunlu (SIM/SMS hazir olana kadar tekrar denenir).
static const char kCfg[] PROGMEM =
    "ATE0\0"
    "AT+IPR=9600\0"
    "!AT+CMGF=1\0"
    "AT+CSCS=\"IRA\"\0"
    "!AT+CPMS=\"SM\",\"SM\",\"SM\"\0"
    "!AT+CNMI=2,1,0,0,0\0"
    "AT+CFGRI=1\0"
    "AT+CTZU=1\0"
    "AT+CSCLK=1\0";

static bool configure() {
  const char *p = kCfg;
  while (pgm_read_byte(p)) {
    bool essential = pgm_read_byte(p) == '!';
    const char *cmd = essential ? p + 1 : p;
    uint8_t tries = essential ? 20 : 2;
    bool ok = false;
    while (tries--) {
      if (atCmd(cmd, 2000) == AT_OK) {
        ok = true;
        break;
      }
      svcDelay(1000);
    }
    if (essential && !ok) return false;
    p += strlen_P(p) + 1;
  }
  return true;
}

static bool powerOnOnce() {
  DBGLN("Modem: guc ac");
  digitalWrite(PIN_MODEM_DTR, LOW);
  digitalWrite(PIN_MODEM_PWR_EN, HIGH);
  s_on = true;
  svcDelay(500);                        // 2x470 uF dolsun
  digitalWrite(PIN_MODEM_PWRKEY, HIGH); // PWRKEY LOW >= 500 ms
  svcDelay(600);
  digitalWrite(PIN_MODEM_PWRKEY, LOW);
  ss.begin(MODEM_BAUD);
  ss.listen();
  if (!alive(25, 1000)) {
    // Fabrika hizi 115200 olabilir: 9600'e cek (A7670E ayari kalici saklar; AT&W ek guvence)
    for (uint8_t i = 0; i < 3; i++) {
      ss.begin(MODEM_FACTORY_BAUD);
      ss.print(F("AT+IPR=9600\r"));
      svcDelay(300);
    }
    ss.begin(MODEM_BAUD);
    ss.listen();
    if (!alive(3, 1000)) return false;
    atCmd(PSTR("AT&W"), 2000);
  }
  return configure();
}

bool modemIsOn() { return s_on; }

bool modemInBackoff() { return s_backoff && (int32_t)(s_backoffUntil - clockNow()) > 0; }

static bool wake() {
  digitalWrite(PIN_MODEM_DTR, LOW);
  ss.listen();
  svcDelay(60);
  return alive(3, 600);
}

bool modemEnsure(bool force) {
  if (s_on && s_ready && wake()) return true;
  if (!force && modemInBackoff()) return false;
  uint8_t attempts = (force && s_backoff) ? 1 : MODEM_MAX_ATTEMPTS;
  for (uint8_t i = 0; i < attempts; i++) {
    hardOff();
    svcDelay(1500);
    if (powerOnOnce()) {
      s_ready = true;
      s_backoff = false;
      DBGLN("Modem: hazir");
      return true;
    }
  }
  hardOff();
  s_backoff = true;
  s_backoffUntil = clockNow() + MODEM_RETRY_BACKOFF_S;
  DBGLN("Modem: yanit yok, 30 dk bekleme");
  return false;
}

void modemSleep() {
  if (s_on) digitalWrite(PIN_MODEM_DTR, HIGH);  // AT+CSCLK=1: DTR HIGH iken modem uyur
  ss.stopListening();
}

// ---------------------------------------------------------------------------
// Sebeke / bilgi
// ---------------------------------------------------------------------------
static void cbReg(char *line, void *ctx) {
  // "+CREG: 0,1" / "+CEREG: 0,5"
  if (strncmp_P(line, PSTR("+CREG:"), 6) && strncmp_P(line, PSTR("+CEREG:"), 7)) return;
  const char *c = strchr(line, ',');
  if (c && (c[1] == '1' || c[1] == '5')) *(bool *)ctx = true;
}

bool modemWaitNetwork(uint16_t timeoutS) {
  uint32_t start = millis();
  for (;;) {
    bool reg = false;
    atCmd(PSTR("AT+CEREG?"), 2000, cbReg, &reg);
    if (!reg) atCmd(PSTR("AT+CREG?"), 2000, cbReg, &reg);
    if (reg) return true;
    if ((uint32_t)(millis() - start) >= (uint32_t)timeoutS * 1000UL) return false;
    svcDelay(2000);
  }
}

static void cbCsq(char *line, void *ctx) {
  if (strncmp_P(line, PSTR("+CSQ:"), 5)) return;
  const char *p = line + 5;
  while (*p == ' ') p++;
  int v = 0;
  while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
  *(int8_t *)ctx = (int8_t)v;
}

int8_t modemSignal() {
  int8_t v = -1;
  if (atCmd(PSTR("AT+CSQ"), 2000, cbCsq, &v) != AT_OK) return -1;
  return v;
}

static void cbCclk(char *line, void *ctx) {
  if (strncmp_P(line, PSTR("+CCLK:"), 6)) return;
  uint32_t *out = (uint32_t *)ctx;
  if (!parseCclk(line, out)) *out = 0;
}

bool modemNetworkTime(uint32_t *secs2000) {
  uint32_t v = 0;
  if (atCmd(PSTR("AT+CCLK?"), 2000, cbCclk, &v) != AT_OK || v == 0) return false;
  *secs2000 = v;
  return true;
}

// ---------------------------------------------------------------------------
// SMS
// ---------------------------------------------------------------------------
bool modemSendSms(const char *number, const char *text) {
  if (!number || !*number) return false;
  if (!modemWaitNetwork(MODEM_NET_WAIT_S)) return false;
  for (uint8_t attempt = 0; attempt < 2; attempt++) {
    flushInput();
    ss.print(F("AT+CMGS=\""));
    ss.print(number);
    ss.print(F("\"\r"));
    if (!waitPrompt(5000)) {
      ss.write((uint8_t)0x1B);  // ESC: istemi iptal
      svcDelay(500);
      continue;
    }
    uint8_t n = 0;
    for (const char *p = text; *p && n < 160; p++, n++) {
      char c = *p;
      if (c < 0x20 || c > 0x7E) c = '?';
      ss.write((uint8_t)c);
    }
    ss.write((uint8_t)0x1A);  // Ctrl-Z: gonder
    if (atWait(60000UL, 0, 0) == AT_OK) {
      DBG("SMS -> ");
      DBGVLN(number);
      return true;
    }
    svcDelay(2000);
  }
  return false;
}

struct CmglCtx {
  uint8_t state;   // 0: baslik bekleniyor, 1: metin bekleniyor, 2: tamam
  uint16_t idx;
  char *sender;
  uint8_t senderSize;
  char *text;
  uint8_t textSize;
};

static void cbCmgl(char *line, void *vctx) {
  CmglCtx *c = (CmglCtx *)vctx;
  if (c->state == 0 && !strncmp_P(line, PSTR("+CMGL:"), 6)) {
    // +CMGL: 3,"REC UNREAD","+905321112233","","26/11/10,13:45:00+12"
    const char *p = line + 6;
    while (*p == ' ') p++;
    uint16_t idx = 0;
    while (*p >= '0' && *p <= '9') idx = (uint16_t)(idx * 10 + (*p++ - '0'));
    c->idx = idx;
    c->sender[0] = 0;
    const char *q = p;
    for (uint8_t k = 0; k < 3 && q; k++) {
      q = strchr(q, '"');
      if (q) q++;
    }
    if (q) {
      uint8_t n = 0;
      while (*q && *q != '"' && n < c->senderSize - 1) c->sender[n++] = *q++;
      c->sender[n] = 0;
    }
    c->state = 1;
  } else if (c->state == 1) {
    strncpy(c->text, line, c->textSize - 1);
    c->text[c->textSize - 1] = 0;
    c->state = 2;
  }
}

bool modemReadFirstSms(uint16_t *idx, char *sender, uint8_t senderSize, char *text, uint8_t textSize) {
  CmglCtx c;
  c.state = 0;
  c.idx = 0;
  c.sender = sender;
  c.senderSize = senderSize;
  c.text = text;
  c.textSize = textSize;
  text[0] = 0;
  sender[0] = 0;
  uint8_t rc = atCmd(PSTR("AT+CMGL=\"ALL\""), 15000UL, cbCmgl, &c);
  if (c.state == 0) return false;
  (void)rc;  // OK gelmese de (zaman asimi) ilk mesaj islenebilir
  *idx = c.idx;
  return true;
}

bool modemDeleteSms(uint16_t idx) {
  flushInput();
  ss.print(F("AT+CMGD="));
  ss.print(idx);
  ss.print('\r');
  return atWait(5000, 0, 0) == AT_OK;
}

bool modemCall(const char *number, uint8_t seconds) {
  if (!number || !*number || !modemWaitNetwork(30)) return false;
  flushInput();
  ss.print(F("ATD"));
  ss.print(number);
  ss.print(F(";\r"));
  bool ok = atWait(10000, 0, 0) == AT_OK;
  if (ok) svcDelay((uint16_t)seconds * 1000u);
  atCmd(PSTR("AT+CHUP"), 5000);
  return ok;
}
