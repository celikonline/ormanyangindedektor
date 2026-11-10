// commands.cpp - SAF MANTIK (AVR + host). Bkz. commands.h ve SPEC §6.3
//
// Guvenlik kurallari:
//  * PIN her zaman zorunlu.
//  * Numara listesi doluysa gonderen listede olmali; degilse mesaj SESSIZCE yok sayilir
//    (yabanci numaralara SMS harcanmaz, cihazin varligi ifsa edilmez).
//  * Liste bossa yalniz dogru PIN'li "EKLE 1" kabul edilir ve GONDEREN numara yonetici olur.
//  * ADMIN_ONLY_CONFIG=1 ise EKLE / SIL / PIN yalniz 1. numaradan (yonetici) kabul edilir.
#include "commands.h"
#include "config.h"

// Sira CmdId ile ayni olmalidir (CMD_DURUM = 1).
static const char kKeywords[] PROGMEM =
    "DURUM\0TEST\0EKLE\0SIL\0LISTE\0KONUM\0AD\0HASSAS\0SESSIZ\0SIREN\0ARAMA\0RAPOR\0KALIBRE\0"
    "SIFIRLA\0PIN\0";

uint8_t cmdLookup(const char *kw) {
  const char *p = kKeywords;
  for (uint8_t id = CMD_DURUM; id <= CMD_PIN; id++) {
    if (strcmp_P(kw, p) == 0) return id;
    p += strlen_P(p) + 1;
  }
  return CMD_NONE;
}

void cmdAddDeviceId(TextBuf &tb, uint16_t id) {
  tb.addP(PSTR("ON1-"));
  tb.addUintPad(id, 4);
  tb.addChar(' ');
}

// Bosluga kadar olan belirteci ayirir; p'yi sonraki belirtecin basina tasir.
static char *nextToken(char **p) {
  char *s = *p;
  while (*s == ' ') s++;
  if (!*s) {
    *p = s;
    return 0;
  }
  char *start = s;
  while (*s && *s != ' ') s++;
  if (*s) *s++ = 0;
  while (*s == ' ') s++;
  *p = s;
  return start;
}

// "AC" / "KAPA" (ve "ACIK", "KAPAT", "KAPALI") -> 1 / 0, gecersiz -> -1
static int8_t parseOnOff(char *arg) {
  toUpperAscii(arg);
  if (!strcmp_P(arg, PSTR("AC")) || !strcmp_P(arg, PSTR("ACIK")) || !strcmp_P(arg, PSTR("ON")))
    return 1;
  if (!strcmp_P(arg, PSTR("KAPA")) || !strcmp_P(arg, PSTR("KAPAT")) ||
      !strcmp_P(arg, PSTR("KAPALI")) || !strcmp_P(arg, PSTR("OFF")))
    return 0;
  return -1;
}

static void replyOk(TextBuf &r) { r.addP(PSTR("TAMAM: ")); }
static void replyErr(TextBuf &r) { r.addP(PSTR("HATA: ")); }

static void addOnOff(TextBuf &r, bool on) { r.addP(on ? PSTR("ACIK") : PSTR("KAPALI")); }

// AD parametresi: harf/rakam/'-'/'_'/'.'; bosluk -> '-'. Uzunluk 1..20.
static bool sanitizeName(const char *in, char *out) {
  uint8_t o = 0;
  for (; *in; in++) {
    char ch = *in;
    if (ch == ' ') ch = '-';
    bool ok = (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') ||
              ch == '-' || ch == '_' || ch == '.';
    if (!ok) continue;
    if (o >= NAME_LEN - 1) return false;
    out[o++] = ch;
  }
  out[o] = 0;
  return o > 0;
}

static bool isAdmin(const Settings *s, const char *sender) {
  return s->phones[0][0] && phoneMatch(s->phones[0], sender);
}

static bool senderListed(const Settings *s, const char *sender) {
  for (uint8_t i = 0; i < PHONE_SLOTS; i++)
    if (s->phones[i][0] && phoneMatch(s->phones[i], sender)) return true;
  return false;
}

static bool isDigits(const char *p, uint8_t minLen, uint8_t maxLen) {
  uint8_t n = 0;
  for (; *p; p++, n++)
    if (*p < '0' || *p > '9') return false;
  return n >= minLen && n <= maxLen;
}

static void addHelp(TextBuf &r) {
  r.addP(PSTR("bilinmeyen komut. DURUM TEST EKLE SIL LISTE KONUM AD HASSAS SESSIZ SIREN ARAMA "
              "RAPOR KALIBRE SIFIRLA PIN"));
}

uint8_t cmdProcess(char *text, const char *sender, Settings *s, const CmdHooks *h, TextBuf &r) {
  r.clear();
  if (!text || !sender || !*sender) return 0;

  // 1) Kodlama: UCS2 hex (Turkce karakterli SMS) veya UTF-8/Latin-5 -> ASCII
  if (!ucs2HexDecode(text)) utf8ToAscii(text);
  trimInPlace(text);

  // 2) Bolme: PIN, KOMUT, parametreler
  char *p = text;
  char *pinTok = nextToken(&p);
  char *kwTok = nextToken(&p);
  if (!pinTok || !kwTok) return 0;
  char *args = p;  // kalan metin (orijinal buyuk/kucuk harf korunur - AD icin)
  trimInPlace(args);
  toUpperAscii(kwTok);
  uint8_t cmd = cmdLookup(kwTok);

  // 3) Yetkilendirme
  bool listEmpty = settingsPhoneListEmpty(s);
  if (!listEmpty && !senderListed(s, sender)) return 0;  // yabanci numara: sessizce yok say
  if (strcmp(pinTok, s->pin) != 0) {
    if (listEmpty) return 0;
    cmdAddDeviceId(r, s->deviceId);
    replyErr(r);
    r.addP(PSTR("PIN yanlis"));
    return CMDR_REPLY;
  }

  cmdAddDeviceId(r, s->deviceId);

  if (listEmpty) {
    // Ilk kurulum: yalniz "EKLE 1" -> gonderen yonetici olur.
    char *slotTok = nextToken(&args);
    if (cmd != CMD_EKLE || !slotTok || strcmp_P(slotTok, PSTR("1")) != 0) {
      replyErr(r);
      r.addP(PSTR("once yonetici ekleyin: EKLE 1 <numara>"));
      return CMDR_REPLY;
    }
    char norm[PHONE_LEN];
    if (!phoneNormalize(sender, norm, sizeof(norm))) return 0;
    strcpy(s->phones[0], norm);
    replyOk(r);
    r.addP(PSTR("yonetici 1 = "));
    r.add(norm);
    return CMDR_REPLY | CMDR_SAVE;
  }

#if ADMIN_ONLY_CONFIG
  if ((cmd == CMD_EKLE || cmd == CMD_SIL || cmd == CMD_PIN) && !isAdmin(s, sender)) {
    replyErr(r);
    r.addP(PSTR("bu komut yalniz yonetici (1) icindir"));
    return CMDR_REPLY;
  }
#endif

  uint16_t num = 0;
  switch (cmd) {
    case CMD_DURUM:
      r.clear();
      if (h && h->status) h->status(r);
      return CMDR_REPLY;

    case CMD_TEST:
      // Yanit yok: test SMS'i gonderen dahil tum numaralara gider.
      if (h && h->action) h->action(ACT_TEST, 0);
      r.clear();
      return 0;

    case CMD_EKLE: {
      char *slotTok = nextToken(&args);
      char norm[PHONE_LEN];
      if (!slotTok || !parseUint16(slotTok, &num) || num < 1 || num > PHONE_SLOTS ||
          !phoneNormalize(args, norm, sizeof(norm))) {
        replyErr(r);
        r.addP(PSTR("bicim: EKLE <1-5> <numara>"));
        return CMDR_REPLY;
      }
      strcpy(s->phones[num - 1], norm);
      replyOk(r);
      r.addInt(num);
      r.addP(PSTR(" = "));
      r.add(norm);
      return CMDR_REPLY | CMDR_SAVE;
    }

    case CMD_SIL:
      if (!parseUint16(args, &num) || num < 1 || num > PHONE_SLOTS) {
        replyErr(r);
        r.addP(PSTR("bicim: SIL <1-5>"));
        return CMDR_REPLY;
      }
      s->phones[num - 1][0] = 0;
      replyOk(r);
      r.addInt(num);
      r.addP(PSTR(" silindi"));
      return CMDR_REPLY | CMDR_SAVE;

    case CMD_LISTE:
      r.addP(PSTR("LISTE"));
      for (uint8_t i = 0; i < PHONE_SLOTS; i++) {
        r.addChar(' ');
        r.addInt(i + 1);
        r.addChar(':');
        if (s->phones[i][0]) r.add(s->phones[i]);
        else r.addChar('-');
      }
      return CMDR_REPLY;

    case CMD_KONUM:
      if (!*args) {
        r.addP(PSTR("KONUM "));
        if (s->location[0]) {
          r.addP(PSTR("maps.google.com/?q="));
          r.add(s->location);
        } else {
          r.addP(PSTR("ayarlanmamis"));
        }
        return CMDR_REPLY;
      }
      if (!locationNormalize(args) || strlen(args) >= LOC_LEN) {
        replyErr(r);
        r.addP(PSTR("bicim: KONUM 39.70512,26.85211"));
        return CMDR_REPLY;
      }
      strcpy(s->location, args);
      replyOk(r);
      r.addP(PSTR("KONUM "));
      r.add(s->location);
      return CMDR_REPLY | CMDR_SAVE;

    case CMD_AD: {
      char nm[NAME_LEN];
      if (!sanitizeName(args, nm)) {
        replyErr(r);
        r.addP(PSTR("AD 1-20 karakter (harf, rakam, - _ .)"));
        return CMDR_REPLY;
      }
      strcpy(s->name, nm);
      replyOk(r);
      r.addP(PSTR("AD "));
      r.add(s->name);
      return CMDR_REPLY | CMDR_SAVE;
    }

    case CMD_HASSAS:
      if (!parseUint16(args, &num) || num < 1 || num > 3) {
        replyErr(r);
        r.addP(PSTR("bicim: HASSAS 1/2/3"));
        return CMDR_REPLY;
      }
      s->sens = (uint8_t)num;
      replyOk(r);
      r.addP(PSTR("HASSAS "));
      r.addInt(num);
      r.addP(num == 1 ? PSTR(" (dusuk)") : (num == 2 ? PSTR(" (normal)") : PSTR(" (yuksek)")));
      return CMDR_REPLY | CMDR_SAVE;

    case CMD_SESSIZ:
      if (!parseUint16(args, &num) || num > MUTE_MAX_MIN) {
        replyErr(r);
        r.addP(PSTR("bicim: SESSIZ <0-1440 dk>"));
        return CMDR_REPLY;
      }
      if (h && h->action) h->action(ACT_MUTE, num);
      replyOk(r);
      if (num == 0) {
        r.addP(PSTR("sessiz iptal"));
      } else {
        r.addP(PSTR("yerel alarm "));
        r.addInt(num);
        r.addP(PSTR(" dk sessiz (SMS devam eder)"));
      }
      return CMDR_REPLY;

    case CMD_SIREN:
    case CMD_ARAMA: {
      uint8_t bit = (cmd == CMD_SIREN) ? SFLAG_SIREN_EN : SFLAG_CALL_EN;
      uint8_t flags = 0;
      if (*args) {
        int8_t v = parseOnOff(args);
        if (v < 0) {
          replyErr(r);
          r.addP(cmd == CMD_SIREN ? PSTR("bicim: SIREN AC/KAPA") : PSTR("bicim: ARAMA AC/KAPA"));
          return CMDR_REPLY;
        }
        if (v) s->flags |= bit;
        else s->flags &= (uint8_t)~bit;
        replyOk(r);
        flags = CMDR_SAVE;
      }
      r.addP(cmd == CMD_SIREN ? PSTR("SIREN ") : PSTR("ARAMA "));
      addOnOff(r, (s->flags & bit) != 0);
      return (uint8_t)(CMDR_REPLY | flags);
    }

    case CMD_RAPOR:
      if (!parseUint16(args, &num) || num > 168) {
        replyErr(r);
        r.addP(PSTR("bicim: RAPOR <0-168 saat>"));
        return CMDR_REPLY;
      }
      s->reportHours = (uint8_t)num;
      replyOk(r);
      r.addP(PSTR("RAPOR "));
      if (num) {
        r.addInt(num);
        r.addP(PSTR(" saat"));
      } else {
        r.addP(PSTR("kapali"));
      }
      return CMDR_REPLY | CMDR_SAVE;

    case CMD_KALIBRE:
      if (h && h->action) h->action(ACT_CALIBRATE, 0);
      replyOk(r);
      r.addP(PSTR("gaz tabani sifirlandi"));
      return CMDR_REPLY;

    case CMD_SIFIRLA:
      if (h && h->action) h->action(ACT_RESET, 0);
      replyOk(r);
      r.addP(PSTR("alarm onaylandi, durum NORMAL"));
      return CMDR_REPLY;

    case CMD_PIN:
      if (!isDigits(args, 4, PIN_LEN - 1)) {
        replyErr(r);
        r.addP(PSTR("PIN 4-6 rakam olmali"));
        return CMDR_REPLY;
      }
      strcpy(s->pin, args);
      replyOk(r);
      r.addP(PSTR("PIN degistirildi"));
      return CMDR_REPLY | CMDR_SAVE;

    default:
      replyErr(r);
      addHelp(r);
      return CMDR_REPLY;
  }
}
