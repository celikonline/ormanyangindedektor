// test_logic.cpp - ON-1 saf mantik birim testleri (PC'de calisir).
//
// Test edilen moduller (firmware/OrmanNobetcisi altindaki AYNI kaynak dosyalar):
//   storage.cpp  : CRC8, varsayilanlar, dogrulama
//   textutil.cpp : TextBuf, ASCII Turkce donusum, UCS2, telefon, konum, ag saati
//   detector.cpp : skor, hassasiyet olcekleme, Angstrom, termal istatistik, gaz tabani, gecmis
//   commands.cpp : SMS komut ayristirici + PIN / beyaz liste / yonetici guvenligi
//
// Derleme (bkz. Makefile / run_tests.cmd):
//   g++ -std=c++11 -Wall -Wextra -I../OrmanNobetcisi test_logic.cpp ../OrmanNobetcisi/{storage,textutil,detector,commands}.cpp
#include <stdio.h>
#include <string.h>
#include "storage.h"
#include "textutil.h"
#include "detector.h"
#include "commands.h"

static int g_fail = 0, g_pass = 0;

#define CHECK(cond)                                                     \
  do {                                                                  \
    if (cond) {                                                         \
      g_pass++;                                                         \
    } else {                                                            \
      g_fail++;                                                         \
      printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);            \
    }                                                                   \
  } while (0)

#define CHECK_EQ(a, b)                                                                  \
  do {                                                                                  \
    long _a = (long)(a), _b = (long)(b);                                                \
    if (_a == _b) {                                                                     \
      g_pass++;                                                                         \
    } else {                                                                            \
      g_fail++;                                                                         \
      printf("FAIL %s:%d: %s == %s  (%ld != %ld)\n", __FILE__, __LINE__, #a, #b, _a, _b); \
    }                                                                                   \
  } while (0)

#define CHECK_STR(a, b)                                                                     \
  do {                                                                                      \
    const char *_a = (a), *_b = (b);                                                        \
    if (strcmp(_a, _b) == 0) {                                                              \
      g_pass++;                                                                             \
    } else {                                                                                \
      g_fail++;                                                                             \
      printf("FAIL %s:%d: %s\n   got:  \"%s\"\n   want: \"%s\"\n", __FILE__, __LINE__, #a, _a, _b); \
    }                                                                                       \
  } while (0)

// ---------------------------------------------------------------------------
static void test_crc_storage() {
  const char *v = "123456789";
  CHECK_EQ(crc8((const uint8_t *)v, 9), 0xF4);  // CRC-8/SMBUS kontrol degeri
  CHECK_EQ(crc8((const uint8_t *)v, 0), 0x00);

  Settings s;
  settingsDefaults(&s);
  CHECK(settingsValid(&s));
  CHECK_STR(s.pin, "1234");
  CHECK_EQ(s.sens, 2);
  CHECK_EQ(s.vrefMv, 1100);
  CHECK(s.flags & SFLAG_SIREN_EN);
  CHECK(!(s.flags & SFLAG_CALL_EN));
  CHECK(settingsPhoneListEmpty(&s));

  s.name[0] = 'X';  // CRC guncellenmeden degisiklik -> gecersiz
  CHECK(!settingsValid(&s));
  settingsSeal(&s);
  CHECK(settingsValid(&s));
  s.magic = 0;
  settingsSeal(&s);
  CHECK(!settingsValid(&s));
  settingsDefaults(&s);
  s.sens = 4;
  settingsSeal(&s);
  CHECK(!settingsValid(&s));
}

// ---------------------------------------------------------------------------
static void test_textbuf() {
  char b[161];
  TextBuf tb(b, 160);
  for (int i = 0; i < 300; i++) tb.addChar('A');
  CHECK_EQ(tb.length(), 160);
  CHECK_EQ(strlen(b), 160);

  tb.clear();
  tb.addInt(-1234);
  tb.addChar(' ');
  tb.addInt(0);
  tb.addChar(' ');
  tb.addUintPad(7, 4);
  tb.addChar(' ');
  tb.addDec(395, 2);
  tb.addChar(' ');
  tb.addDec(-5, 1);
  tb.addChar(' ');
  tb.addDec(52, 1);
  CHECK_STR(b, "-1234 0 0007 3.95 -0.5 5.2");

  char small[6];
  TextBuf t2(small, 5);
  t2.add("ABCDEFGH");
  CHECK_STR(small, "ABCDE");
}

static void test_ascii() {
  CHECK_EQ(asciiFromCodepoint(0x00E7), 'c');
  CHECK_EQ(asciiFromCodepoint(0x011F), 'g');
  CHECK_EQ(asciiFromCodepoint(0x0131), 'i');
  CHECK_EQ(asciiFromCodepoint(0x0130), 'I');
  CHECK_EQ(asciiFromCodepoint(0x00F6), 'o');
  CHECK_EQ(asciiFromCodepoint(0x015F), 's');
  CHECK_EQ(asciiFromCodepoint(0x00FC), 'u');
  CHECK_EQ(asciiFromCodepoint(0x00C7), 'C');
  CHECK_EQ(asciiFromCodepoint(0x011E), 'G');
  CHECK_EQ(asciiFromCodepoint(0x015E), 'S');
  CHECK_EQ(asciiFromCodepoint(0x00D6), 'O');
  CHECK_EQ(asciiFromCodepoint(0x00DC), 'U');
  CHECK_EQ(asciiFromCodepoint(0x20AC), '?');  // euro
  CHECK_EQ(asciiFromCodepoint('\n'), ' ');

  char s1[] = "\xC3\x87\xC4\xB1\xC4\x9F \xC5\x9E\xC3\x9C\xC3\x96 \xC3\xBCnl\xC3\xBC \xC4\xB0zmir";  // "Çığ ŞÜÖ ünlü İzmir"
  utf8ToAscii(s1);
  CHECK_STR(s1, "Cig SUO unlu Izmir");

  char s2[] = "\xDD\xFE\xF0\xE7";  // Latin-5: İ ş ğ ç
  utf8ToAscii(s2);
  CHECK_STR(s2, "Isgc");

  char s3[] = "\xF0\x9F\x94\xA5 ates";  // emoji (4 bayt) + ascii
  utf8ToAscii(s3);
  CHECK_STR(s3, "? ates");

  char u1[] = "003500360037003800200044005500520055004D";  // "5678 DURUM"
  CHECK(ucs2HexDecode(u1));
  CHECK_STR(u1, "5678 DURUM");
  char u2[] = "0035003600370038002000530130004C00200032";  // "5678 SİL 2"
  CHECK(ucs2HexDecode(u2));
  CHECK_STR(u2, "5678 SIL 2");
  char u3[] = "1234 DURUM";
  CHECK(!ucs2HexDecode(u3));
  char u4[] = "12345678";  // hex gibi ama "00" ile baslamiyor
  CHECK(!ucs2HexDecode(u4));

  char a[] = "a\x01" "b\x7F";
  sanitizeAscii(a);
  CHECK_STR(a, "a?b?");
  char up[] = "durum SIL ac";
  toUpperAscii(up);
  CHECK_STR(up, "DURUM SIL AC");
  char tr[] = "   x y  ";
  trimInPlace(tr);
  CHECK_STR(tr, "x y");
}

static void test_phone_location_time() {
  char out[17];
  CHECK_EQ(phoneNormalize("+90 532 111 22 33", out, sizeof(out)), 12);
  CHECK_STR(out, "+905321112233");
  CHECK_EQ(phoneNormalize("0(532)111-22-33", out, sizeof(out)), 11);
  CHECK_STR(out, "05321112233");
  CHECK_EQ(phoneNormalize("12345", out, sizeof(out)), 0);
  CHECK_EQ(phoneNormalize("+90532abc", out, sizeof(out)), 0);
  CHECK_EQ(phoneNormalize("90+532111223", out, sizeof(out)), 0);  // + yalniz basta
  CHECK_EQ(phoneNormalize("+1234567890123456", out, sizeof(out)), 0);  // 16 hane

  CHECK(phoneMatch("+905321112233", "05321112233"));
  CHECK(phoneMatch("+905321112233", "5321112233"));
  CHECK(phoneMatch("+90 532 111 22 33", "+905321112233"));
  CHECK(!phoneMatch("+905321112233", "+905321112234"));
  CHECK(!phoneMatch("+905321112233", ""));
  CHECK(!phoneMatch("TURKCELL", "+905321112233"));
  CHECK(phoneMatch("1234567", "1234567"));
  CHECK(!phoneMatch("1234567", "01234567"));

  uint16_t v = 0;
  CHECK(parseUint16("24", &v) && v == 24);
  CHECK(parseUint16("65535", &v) && v == 65535);
  CHECK(!parseUint16("65536", &v));
  CHECK(!parseUint16("", &v));
  CHECK(!parseUint16("1a", &v));
  CHECK(!parseUint16("-1", &v));

  char l1[] = "39.70512, 26.85211";
  CHECK(locationNormalize(l1));
  CHECK_STR(l1, "39.70512,26.85211");
  char l2[] = "-90,-180";
  CHECK(locationNormalize(l2));
  char l3[] = "90.0001,10";
  CHECK(!locationNormalize(l3));
  char l4[] = "45,180.5";
  CHECK(!locationNormalize(l4));
  char l5[] = "abc";
  CHECK(!locationNormalize(l5));
  char l6[] = "39.7";
  CHECK(!locationNormalize(l6));
  char l7[] = "39.,26";
  CHECK(!locationNormalize(l7));

  uint32_t t = 0;
  CHECK(parseCclk("+CCLK: \"26/11/10,13:45:00+12\"", &t));
  CHECK_EQ(t, 847633500UL);
  CHECK(parseCclk("+CCLK: \"24/02/29,23:59:59+12\"", &t));
  CHECK_EQ(t, 762566399UL);
  CHECK(parseCclk("+CCLK: \"25/03/01,00:00:00+00\"", &t));
  CHECK_EQ(t, 794102400UL);
  CHECK(!parseCclk("+CCLK: \"70/01/01,00:00:00+00\"", &t));  // ayarlanmamis modem saati
  CHECK(!parseCclk("+CCLK: \"26/13/10,13:45:00+12\"", &t));
  CHECK(!parseCclk("+CCLK: 26/11/10", &t));
}

// ---------------------------------------------------------------------------
static void test_angstrom_battery() {
  CHECK_EQ(angstromIndex100(410, 220), 255);  // RH 41 %, 22 C -> I = 2,55
  CHECK_EQ(angstromLevel(255), RISK_MEDIUM);
  CHECK_EQ(angstromLevel(angstromIndex100(200, 350)), RISK_VERY_HIGH);  // 1,0 - 0,8 = 0,2
  CHECK_EQ(angstromLevel(199), RISK_VERY_HIGH);
  CHECK_EQ(angstromLevel(200), RISK_HIGH);
  CHECK_EQ(angstromLevel(249), RISK_HIGH);
  CHECK_EQ(angstromLevel(250), RISK_MEDIUM);
  CHECK_EQ(angstromLevel(400), RISK_MEDIUM);
  CHECK_EQ(angstromLevel(401), RISK_LOW);
  CHECK_EQ(angstromIndex100(800, 100), 400 + 170);  // nemli serin gun -> 5,7 DUSUK
  CHECK_STR(riskNameP(RISK_VERY_HIGH), "COK YUKSEK");
  CHECK_STR(riskNameP(RISK_LOW), "DUSUK");

  CHECK_EQ(batteryPercent(4200), 100);
  CHECK_EQ(batteryPercent(4300), 100);
  CHECK_EQ(batteryPercent(3700), 40);
  CHECK_EQ(batteryPercent(3750), 48);
  CHECK_EQ(batteryPercent(3450), 7);
  CHECK_EQ(batteryPercent(3000), 0);
  CHECK_EQ(batteryPercent(2500), 0);
}

static void test_thermal_stats() {
  int16_t px[64];
  for (int i = 0; i < 64; i++) px[i] = 80;  // 20,0 C
  int16_t mx, md;
  uint8_t hot;
  thermalStats(px, 64, hotDeltaFor(2), &mx, &md, &hot);
  CHECK_EQ(mx, 200);
  CHECK_EQ(md, 200);
  CHECK_EQ(hot, 0);

  for (int i = 0; i < 64; i++) px[i] = 80;
  px[5] = 160;   // 40 C
  px[17] = 160;
  px[40] = 121;  // 30,25 C (> 20 + 10)
  px[41] = 120;  // tam 30 C (esit -> sicak degil)
  thermalStats(px, 64, hotDeltaFor(2), &mx, &md, &hot);
  CHECK_EQ(mx, 400);
  CHECK_EQ(md, 200);
  CHECK_EQ(hot, 3);
  for (int i = 1; i < 64; i++) CHECK(px[i - 1] <= px[i]);  // siralandi

  for (int i = 0; i < 64; i++) px[i] = (int16_t)(-20 + i);  // negatif degerler
  thermalStats(px, 64, hotDeltaFor(3), &mx, &md, &hot);
  CHECK_EQ(mx, 107);   // 43 x 0,25 = 10,75 C -> 107 (0,1 C, kesme)
  CHECK_EQ(md, 28);    // (11 + 12) / 2 x 0,25 = 2,875 C -> 28
  CHECK_EQ(hot, 2);    // seviye 3 esik: 2,875 + 7,5 = 10,375 C -> q > 41,5 -> {42, 43}
}

// ---------------------------------------------------------------------------
static ScoreInput baseInput() {
  ScoreInput in;
  memset(&in, 0, sizeof(in));
  in.thermalOk = true;
  in.maxT10 = 250;
  in.median10 = 240;
  in.envOk = true;
  in.temp10 = 250;
  return in;
}

static void test_score() {
  uint16_t rs;
  ScoreInput in = baseInput();
  CHECK_EQ(detScore(&in, 2, &rs), 0);
  CHECK_EQ(rs, 0);

  in.maxT10 = 700;  // >= 70 C -> +3 (fark kurali uygulanmaz)
  CHECK_EQ(detScore(&in, 2, &rs), 3);
  CHECK_EQ(rs, R_TH_ABS);
  in.maxT10 = 699;
  in.median10 = 200;  // fark 49,9 -> +2
  CHECK_EQ(detScore(&in, 2, &rs), 2);
  CHECK_EQ(rs, R_TH_DIFF2);
  in.maxT10 = 449;  // fark 24,9 -> +1
  CHECK_EQ(detScore(&in, 2, &rs), 1);
  in.maxT10 = 319;  // fark 11,9 -> 0
  CHECK_EQ(detScore(&in, 2, &rs), 0);
  in.maxT10 = 320;  // fark 12,0 -> +1
  CHECK_EQ(detScore(&in, 2, &rs), 1);

  in = baseInput();
  in.rateValid = true;
  in.rate10 = 80;  // 8 C/dk -> +1
  CHECK_EQ(detScore(&in, 2, &rs), 1);
  CHECK_EQ(rs, R_TH_RATE);
  in.rate10 = 79;
  CHECK_EQ(detScore(&in, 2, &rs), 0);
  in.rateValid = false;
  in.rate10 = 500;
  CHECK_EQ(detScore(&in, 2, &rs), 0);

  in = baseInput();
  in.hotCount = 3;
  CHECK_EQ(detScore(&in, 2, &rs), 1);
  CHECK_EQ(detScore(&in, 1, &rs), 0);  // seviye 1: 4 piksel gerekir
  in.hotCount = 2;
  CHECK_EQ(detScore(&in, 3, &rs), 1);  // seviye 3: 2 piksel yeter
  CHECK_EQ(detScore(&in, 2, &rs), 0);

  in = baseInput();
  in.gasValid = true;
  in.gasPm = 399;
  CHECK_EQ(detScore(&in, 2, &rs), 2);
  CHECK_EQ(rs, R_GAS2);
  in.gasPm = 400;
  CHECK_EQ(detScore(&in, 2, &rs), 1);
  in.gasPm = 649;
  CHECK_EQ(detScore(&in, 2, &rs), 1);
  in.gasPm = 650;
  CHECK_EQ(detScore(&in, 2, &rs), 0);
  in.gasPm = 300;
  CHECK_EQ(detScore(&in, 1, &rs), 1);  // seviye 1: <0,22 -> +2, <0,545 -> +1
  in.gasPm = 219;
  CHECK_EQ(detScore(&in, 1, &rs), 2);
  in.gasPm = 700;
  CHECK_EQ(detScore(&in, 3, &rs), 1);  // seviye 3: <0,7375 -> +1
  in.gasPm = 549;
  CHECK_EQ(detScore(&in, 3, &rs), 2);  // seviye 3: <0,55 -> +2
  in.gasValid = false;
  in.gasPm = 10;
  CHECK_EQ(detScore(&in, 2, &rs), 0);  // isinma: puan yok

  in = baseInput();
  in.temp10 = 550;
  CHECK_EQ(detScore(&in, 2, &rs), 2);
  CHECK_EQ(rs, R_AMB_T);
  in.temp10 = 549;
  CHECK_EQ(detScore(&in, 2, &rs), 0);
  CHECK_EQ(detScore(&in, 3, &rs), 2);  // 0,75 x 55 = 41,25 C
  in.temp10 = 250;
  in.riseValid = true;
  in.rise10 = 60;
  in.dropValid = true;
  in.drop10 = 150;
  CHECK_EQ(detScore(&in, 2, &rs), 2);
  CHECK_EQ(rs, R_AMB_RISE | R_RH_DROP);
  CHECK_EQ(detScore(&in, 1, &rs), 0);  // 7,8 C / 19,5 puan gerekir

  // Hassasiyet olcekleme
  CHECK_EQ(scaleTh(TH_MAXT_ABS_X10, 1), 910);
  CHECK_EQ(scaleTh(TH_MAXT_ABS_X10, 2), 700);
  CHECK_EQ(scaleTh(TH_MAXT_ABS_X10, 3), 525);
  CHECK_EQ(hotDeltaFor(3), 75);

  // SPEC §6.4 ornegi: Termal 78 C, Gaz %38, Hava 41 C / %12 -> dogrudan ALARM (>= 5)
  in = baseInput();
  in.maxT10 = 780;
  in.median10 = 260;
  in.hotCount = 6;
  in.gasValid = true;
  in.gasPm = 380;
  in.temp10 = 410;
  CHECK(detScore(&in, 2, &rs) >= 5);
  CHECK_EQ(detScore(&in, 2, &rs), 3 + 1 + 2);
  // Tum kurallar birden: 3+1+1+2+2+1+1 = 11
  in.rateValid = true;
  in.rate10 = 200;
  in.temp10 = 600;
  in.riseValid = in.dropValid = true;
  in.rise10 = 100;
  in.drop10 = 300;
  CHECK_EQ(detScore(&in, 2, &rs), 11);
}

static Reading rd(int16_t maxT10, int16_t med10, int16_t t10, int16_t rh10, uint32_t gas) {
  Reading r;
  memset(&r, 0, sizeof(r));
  r.thermalOk = true;
  r.envOk = true;
  r.gasOk = gas != 0;
  r.maxT10 = maxT10;
  r.median10 = med10;
  r.temp10 = t10;
  r.rh10 = rh10;
  r.gasOhm = gas;
  return r;
}

static void test_evaluate() {
  Detector d;
  detInit(&d, 0);
  Reading r = rd(200, 200, 200, 400, 100000);
  CHECK_EQ(detEvaluate(&d, &r, 0, 2, true), 0);
  CHECK(d.gasBaseValid);
  CHECK_EQ(d.gasBase, 100000UL);
  CHECK_EQ(d.gasPm, 1000);

  // Isinma (ilk 30 dk): gaz dususu puan vermez
  r = rd(200, 200, 200, 400, 30000);
  CHECK_EQ(detEvaluate(&d, &r, 60, 2, true), 0);
  CHECK_EQ(d.gasPm, 300);
  // isinmada taban alfa=0,1 ile takip eder: 100000 + (30000-100000)/10 = 93000
  CHECK_EQ(d.gasBase, 93000UL);

  // Isinma sonrasi
  detInit(&d, 0);
  r = rd(200, 200, 200, 400, 100000);
  detEvaluate(&d, &r, 0, 2, true);
  r = rd(200, 200, 200, 400, 35000);  // %35 -> +2
  CHECK_EQ(detEvaluate(&d, &r, 1800, 2, false), 2);
  CHECK_EQ(d.reasons, R_GAS2);
  CHECK_EQ(d.gasBase, 100000UL);  // NORMAL degil -> taban guncellenmez
  r = rd(200, 200, 200, 400, 70000);  // oran 0,7 <= 0,8 -> NORMAL'de bile guncellenmez
  CHECK_EQ(detEvaluate(&d, &r, 1900, 2, true), 0);
  CHECK_EQ(d.gasBase, 100000UL);
  r = rd(200, 200, 200, 400, 90000);  // 0,9 > 0,8 -> EMA %1: 100000 - 100 = 99900
  detEvaluate(&d, &r, 2000, 2, true);
  CHECK_EQ(d.gasBase, 99900UL);
  r = rd(200, 200, 200, 400, 120000);  // yukari yonde de takip
  detEvaluate(&d, &r, 2100, 2, true);
  CHECK_EQ(d.gasBase, 99900UL + 201UL);

  // KALIBRE: bir sonraki okuma yeni taban olur
  detCalibrateGas(&d);
  r = rd(200, 200, 200, 400, 50000);
  CHECK_EQ(detEvaluate(&d, &r, 2200, 2, true), 0);
  CHECK_EQ(d.gasBase, 50000UL);

  // Artis hizi: 60 s'de 20 -> 30 C = 10 C/dk -> +1 ; fark 10 C (<12) -> 0
  detInit(&d, 0);
  r = rd(200, 200, 200, 400, 0);
  detEvaluate(&d, &r, 0, 2, true);
  r = rd(300, 200, 200, 400, 0);
  CHECK_EQ(detEvaluate(&d, &r, 60, 2, true), 1);
  CHECK_EQ(d.reasons, R_TH_RATE);
  CHECK_EQ(d.rate10, 100);
  // 40 s once alinmis ornekten hiz hesaplanmaz (min 45 s); gecmise 50 s'den sik eklenmez
  detInit(&d, 0);
  r = rd(200, 200, 200, 400, 0);
  detEvaluate(&d, &r, 0, 2, true);
  r = rd(300, 200, 200, 400, 0);
  CHECK_EQ(detEvaluate(&d, &r, 40, 2, true), 0);
  CHECK_EQ(d.histCount, 1);

  // 5 dk ortam: 20 C/%40 -> 27 C/%20 : +1 (artis 7) +1 (nem dususu 20)
  detInit(&d, 0);
  for (uint32_t t = 0; t <= 240; t += 60) {
    r = rd(200, 200, 200, 400, 0);
    detEvaluate(&d, &r, t, 2, true);
  }
  r = rd(200, 200, 270, 200, 0);
  CHECK_EQ(detEvaluate(&d, &r, 300, 2, true), 2);
  CHECK_EQ(d.reasons, R_AMB_RISE | R_RH_DROP);
  CHECK_EQ(d.rise10, 70);
  CHECK_EQ(d.drop10, 200);
  // Pencere disi (> 330 s) ornekler hesaba katilmaz
  detInit(&d, 0);
  r = rd(200, 200, 200, 400, 0);
  detEvaluate(&d, &r, 0, 2, true);
  r = rd(200, 200, 270, 200, 0);
  CHECK_EQ(detEvaluate(&d, &r, 400, 2, true), 0);

  // Gecmis halka tamponu tasmaz
  detInit(&d, 0);
  for (uint32_t t = 0; t < 60 * 20; t += 60) {
    r = rd(200, 200, 200, 400, 0);
    detEvaluate(&d, &r, t, 2, true);
  }
  CHECK_EQ(d.histCount, DET_HIST_LEN);

  // Sensor arizasi: termal gecersiz -> termal kurallari yok
  detInit(&d, 0);
  r = rd(900, 200, 200, 400, 0);
  r.thermalOk = false;
  CHECK_EQ(detEvaluate(&d, &r, 0, 2, true), 0);
}

// ---------------------------------------------------------------------------
// Komutlar
// ---------------------------------------------------------------------------
static int g_lastAct = 0, g_lastArg = -1, g_statusCalls = 0;
static void fakeStatus(TextBuf &tb) {
  g_statusCalls++;
  tb.add("DURUM ON1-0001 NORMAL");
}
static void fakeAction(uint8_t act, uint16_t arg) {
  g_lastAct = act;
  g_lastArg = arg;
}
static const CmdHooks kHooks = {fakeStatus, fakeAction};

static char g_reply[161];

static uint8_t run(Settings *s, const char *sender, const char *msg) {
  char text[121];
  strncpy(text, msg, sizeof(text) - 1);
  text[sizeof(text) - 1] = 0;
  TextBuf tb(g_reply, 160);
  uint8_t r = cmdProcess(text, sender, s, &kHooks, tb);
  if (strlen(g_reply) > 160) {
    g_fail++;
    printf("FAIL: reply > 160\n");
  }
  return r;
}

static void test_commands() {
  const char *ADMIN = "+905321112233";
  const char *USER2 = "+905321112244";
  const char *STRANGER = "+905559998877";
  Settings s;
  settingsDefaults(&s);

  CHECK_EQ(cmdLookup("DURUM"), CMD_DURUM);
  CHECK_EQ(cmdLookup("PIN"), CMD_PIN);
  CHECK_EQ(cmdLookup("SIFIRLA"), CMD_SIFIRLA);
  CHECK_EQ(cmdLookup("XYZ"), CMD_NONE);

  // --- Liste bos ---
  CHECK_EQ(run(&s, STRANGER, "0000 DURUM"), 0);  // yanlis PIN: sessiz
  CHECK_EQ(run(&s, STRANGER, "1234 DURUM"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA: once yonetici ekleyin") != 0);
  CHECK_EQ(run(&s, STRANGER, "1234 EKLE 2 +905321112233"), CMDR_REPLY);  // yalniz EKLE 1
  CHECK(settingsPhoneListEmpty(&s));
  CHECK_EQ(run(&s, STRANGER, "1234"), 0);  // komut yok
  CHECK_EQ(run(&s, STRANGER, ""), 0);

  // Ilk EKLE 1: GONDEREN yonetici olur (parametre farkli olsa bile)
  CHECK_EQ(run(&s, ADMIN, "1234 ekle 1 +905000000000"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.phones[0], ADMIN);
  CHECK_STR(g_reply, "ON1-0001 TAMAM: yonetici 1 = +905321112233");

  // --- Liste dolu ---
  CHECK_EQ(run(&s, STRANGER, "1234 DURUM"), 0);  // listede yok: sessiz
  CHECK_EQ(run(&s, ADMIN, "9999 DURUM"), CMDR_REPLY);
  CHECK_STR(g_reply, "ON1-0001 HATA: PIN yanlis");
  g_statusCalls = 0;
  CHECK_EQ(run(&s, "05321112233", "  1234   durum  "), CMDR_REPLY);  // farkli bicim, fazla bosluk
  CHECK_EQ(g_statusCalls, 1);
  CHECK_STR(g_reply, "DURUM ON1-0001 NORMAL");

  CHECK_EQ(run(&s, ADMIN, "1234 EKLE 2 0532 111 22 44"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.phones[1], "05321112244");
  CHECK_STR(g_reply, "ON1-0001 TAMAM: 2 = 05321112244");
  CHECK_EQ(run(&s, ADMIN, "1234 EKLE 6 +905321112255"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA: bicim: EKLE") != 0);
  CHECK_EQ(run(&s, ADMIN, "1234 EKLE 3 abc"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA") != 0);

  // Yonetici olmayan kullanici: EKLE/SIL/PIN yasak, digerleri serbest
  CHECK_EQ(run(&s, USER2, "1234 EKLE 3 +905321112255"), CMDR_REPLY);
  CHECK(strstr(g_reply, "yalniz yonetici") != 0);
  CHECK_EQ(s.phones[2][0], 0);
  CHECK_EQ(run(&s, USER2, "1234 PIN 0000"), CMDR_REPLY);
  CHECK_STR(s.pin, "1234");
  CHECK_EQ(run(&s, USER2, "1234 HASSAS 3"), CMDR_REPLY | CMDR_SAVE);
  CHECK_EQ(s.sens, 3);
  CHECK_STR(g_reply, "ON1-0001 TAMAM: HASSAS 3 (yuksek)");
  CHECK_EQ(run(&s, USER2, "1234 HASSAS 4"), CMDR_REPLY);
  CHECK_EQ(s.sens, 3);

  CHECK_EQ(run(&s, ADMIN, "1234 LISTE"), CMDR_REPLY);
  CHECK_STR(g_reply, "ON1-0001 LISTE 1:+905321112233 2:05321112244 3:- 4:- 5:-");
  CHECK_EQ(run(&s, ADMIN, "1234 SIL 2"), CMDR_REPLY | CMDR_SAVE);
  CHECK_EQ(s.phones[1][0], 0);
  CHECK_EQ(run(&s, ADMIN, "1234 SIL 0"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA") != 0);

  // KONUM
  CHECK_EQ(run(&s, ADMIN, "1234 KONUM"), CMDR_REPLY);
  CHECK_STR(g_reply, "ON1-0001 KONUM ayarlanmamis");
  CHECK_EQ(run(&s, ADMIN, "1234 KONUM 39.70512, 26.85211"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.location, "39.70512,26.85211");
  CHECK_EQ(run(&s, ADMIN, "1234 KONUM 99.1,26"), CMDR_REPLY);
  CHECK_STR(s.location, "39.70512,26.85211");
  CHECK_EQ(run(&s, ADMIN, "1234 KONUM"), CMDR_REPLY);
  CHECK_STR(g_reply, "ON1-0001 KONUM maps.google.com/?q=39.70512,26.85211");

  // AD (buyuk/kucuk harf korunur, UTF-8 Turkce -> ASCII, bosluk -> '-')
  CHECK_EQ(run(&s, ADMIN, "1234 AD KazDagi-K3"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.name, "KazDagi-K3");
  CHECK_EQ(run(&s, ADMIN, "1234 AD Kaz Da\xC4\x9F\xC4\xB1 K3"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.name, "Kaz-Dagi-K3");
  CHECK_EQ(run(&s, ADMIN, "1234 AD 123456789012345678901"), CMDR_REPLY);  // 21 karakter
  CHECK(strstr(g_reply, "HATA") != 0);
  CHECK_STR(s.name, "Kaz-Dagi-K3");
  CHECK_EQ(run(&s, ADMIN, "1234 AD 12345678901234567890"), CMDR_REPLY | CMDR_SAVE);  // 20
  CHECK_EQ(strlen(s.name), 20);

  // SESSIZ
  g_lastAct = 0;
  CHECK_EQ(run(&s, ADMIN, "1234 SESSIZ 30"), CMDR_REPLY);
  CHECK_EQ(g_lastAct, ACT_MUTE);
  CHECK_EQ(g_lastArg, 30);
  CHECK_STR(g_reply, "ON1-0001 TAMAM: yerel alarm 30 dk sessiz (SMS devam eder)");
  CHECK_EQ(run(&s, ADMIN, "1234 SESS\xC4\xB0Z 0"), CMDR_REPLY);  // "SESSİZ 0"
  CHECK_EQ(g_lastArg, 0);
  CHECK_STR(g_reply, "ON1-0001 TAMAM: sessiz iptal");
  CHECK_EQ(run(&s, ADMIN, "1234 SESSIZ 5000"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA") != 0);

  // SIREN / ARAMA
  CHECK_EQ(run(&s, ADMIN, "1234 SIREN KAPA"), CMDR_REPLY | CMDR_SAVE);
  CHECK(!(s.flags & SFLAG_SIREN_EN));
  CHECK_STR(g_reply, "ON1-0001 TAMAM: SIREN KAPALI");
  CHECK_EQ(run(&s, ADMIN, "1234 S\xC4\xB0REN A\xC3\x87"), CMDR_REPLY | CMDR_SAVE);  // "SİREN AÇ"
  CHECK(s.flags & SFLAG_SIREN_EN);
  CHECK_EQ(run(&s, ADMIN, "1234 ARAMA ac"), CMDR_REPLY | CMDR_SAVE);
  CHECK(s.flags & SFLAG_CALL_EN);
  CHECK_EQ(run(&s, ADMIN, "1234 ARAMA"), CMDR_REPLY);  // sorgu
  CHECK_STR(g_reply, "ON1-0001 ARAMA ACIK");
  CHECK_EQ(run(&s, ADMIN, "1234 ARAMA belki"), CMDR_REPLY);
  CHECK(strstr(g_reply, "HATA") != 0);

  // RAPOR
  CHECK_EQ(run(&s, ADMIN, "1234 RAPOR 12"), CMDR_REPLY | CMDR_SAVE);
  CHECK_EQ(s.reportHours, 12);
  CHECK_EQ(run(&s, ADMIN, "1234 RAPOR 0"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(g_reply, "ON1-0001 TAMAM: RAPOR kapali");
  CHECK_EQ(run(&s, ADMIN, "1234 RAPOR 200"), CMDR_REPLY);
  CHECK_EQ(s.reportHours, 0);

  // Eylemler
  CHECK_EQ(run(&s, ADMIN, "1234 KALIBRE"), CMDR_REPLY);
  CHECK_EQ(g_lastAct, ACT_CALIBRATE);
  CHECK_EQ(run(&s, ADMIN, "1234 SIFIRLA"), CMDR_REPLY);
  CHECK_EQ(g_lastAct, ACT_RESET);
  CHECK_EQ(run(&s, ADMIN, "1234 TEST"), 0);  // yanit yok, test SMS'i herkese gider
  CHECK_EQ(g_lastAct, ACT_TEST);

  // Bilinmeyen komut
  CHECK_EQ(run(&s, ADMIN, "1234 YARDIM"), CMDR_REPLY);
  CHECK(strstr(g_reply, "bilinmeyen komut") != 0);

  // PIN degistirme
  CHECK_EQ(run(&s, ADMIN, "1234 PIN 12a4"), CMDR_REPLY);
  CHECK_STR(s.pin, "1234");
  CHECK_EQ(run(&s, ADMIN, "1234 PIN 5678"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.pin, "5678");
  CHECK_EQ(run(&s, ADMIN, "1234 DURUM"), CMDR_REPLY);
  CHECK_STR(g_reply, "ON1-0001 HATA: PIN yanlis");

  // UCS2 (Turkce karakterli telefon klavyesi) mesaji
  g_statusCalls = 0;
  CHECK_EQ(run(&s, ADMIN, "003500360037003800200044005500520055004D"), CMDR_REPLY);  // 5678 DURUM
  CHECK_EQ(g_statusCalls, 1);

  // Yonetici silinirse liste bosalabilir -> yeniden kurulum akisi
  CHECK_EQ(run(&s, ADMIN, "5678 SIL 1"), CMDR_REPLY | CMDR_SAVE);
  CHECK(settingsPhoneListEmpty(&s));
  CHECK_EQ(run(&s, USER2, "5678 EKLE 1"), CMDR_REPLY | CMDR_SAVE);
  CHECK_STR(s.phones[0], USER2);
}

int main() {
  test_crc_storage();
  test_textbuf();
  test_ascii();
  test_phone_location_time();
  test_angstrom_battery();
  test_thermal_stats();
  test_score();
  test_evaluate();
  test_commands();
  printf("\n%d gecti, %d basarisiz\n", g_pass, g_fail);
  return g_fail ? 1 : 0;
}
