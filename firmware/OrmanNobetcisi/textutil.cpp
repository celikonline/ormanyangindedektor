// textutil.cpp - SAF MANTIK (AVR + host). Bkz. textutil.h
#include "textutil.h"

// ---------------------------------------------------------------------------
// TextBuf
// ---------------------------------------------------------------------------
void TextBuf::addChar(char ch) {
  if (n < c) {
    b[n++] = ch;
    b[n] = 0;
  }
}

void TextBuf::add(const char *s) {
  if (!s) return;
  while (*s && n < c) b[n++] = *s++;
  b[n] = 0;
}

void TextBuf::addP(const char *s) {
  if (!s) return;
  char ch;
  while ((ch = (char)pgm_read_byte(s++)) != 0 && n < c) b[n++] = ch;
  b[n] = 0;
}

void TextBuf::addInt(int32_t v) {
  char tmp[12];
  uint8_t i = 0;
  uint32_t u;
  if (v < 0) {
    addChar('-');
    u = (uint32_t)(-(v + 1)) + 1u;
  } else {
    u = (uint32_t)v;
  }
  do {
    tmp[i++] = (char)('0' + (u % 10u));
    u /= 10u;
  } while (u && i < sizeof(tmp));
  while (i) addChar(tmp[--i]);
}

void TextBuf::addUintPad(uint16_t v, uint8_t width) {
  char tmp[6];
  uint8_t i = 0;
  do {
    tmp[i++] = (char)('0' + (v % 10u));
    v /= 10u;
  } while (v && i < sizeof(tmp));
  while (width > i) {
    addChar('0');
    width--;
  }
  while (i) addChar(tmp[--i]);
}

void TextBuf::addDec(int32_t v, uint8_t decimals) {
  uint16_t mult = 1;
  for (uint8_t i = 0; i < decimals; i++) mult = (uint16_t)(mult * 10u);
  if (v < 0) {
    addChar('-');
    v = -v;
  }
  addInt(v / mult);
  if (decimals) {
    addChar('.');
    addUintPad((uint16_t)(v % mult), decimals);
  }
}

// ---------------------------------------------------------------------------
// ASCII Turkce donusum
// ---------------------------------------------------------------------------
char asciiFromCodepoint(uint16_t cp) {
  if (cp == '\t' || cp == '\r' || cp == '\n') return ' ';
  if (cp >= 0x20 && cp < 0x7F) return (char)cp;
  switch (cp) {
    case 0x00C7: return 'C';  // C cedilla
    case 0x00E7: return 'c';
    case 0x011E: return 'G';  // G breve
    case 0x011F: return 'g';
    case 0x0130: return 'I';  // noktali buyuk I
    case 0x0131: return 'i';  // noktasiz kucuk i
    case 0x00D6: return 'O';
    case 0x00F6: return 'o';
    case 0x015E: return 'S';  // S cedilla
    case 0x015F: return 's';
    case 0x00DC: return 'U';
    case 0x00FC: return 'u';
    case 0x00C2: return 'A';  // sapkali harfler
    case 0x00E2: return 'a';
    case 0x00CE: return 'I';
    case 0x00EE: return 'i';
    case 0x00DB: return 'U';
    case 0x00FB: return 'u';
    default: return '?';
  }
}

// ISO-8859-9 (Latin-5) tek bayt -> Unicode (gecersiz UTF-8 yedegi)
static uint16_t latin5ToCodepoint(uint8_t ch) {
  switch (ch) {
    case 0xD0: return 0x011E;
    case 0xF0: return 0x011F;
    case 0xDD: return 0x0130;
    case 0xFD: return 0x0131;
    case 0xDE: return 0x015E;
    case 0xFE: return 0x015F;
    default: return ch;
  }
}

void utf8ToAscii(char *s) {
  uint8_t *r = (uint8_t *)s;
  char *w = s;
  while (*r) {
    uint8_t ch = *r;
    if (ch < 0x80) {
      *w++ = asciiFromCodepoint(ch);
      r++;
    } else if ((ch & 0xE0) == 0xC0 && (r[1] & 0xC0) == 0x80) {
      uint16_t cp = (uint16_t)(((ch & 0x1F) << 6) | (r[1] & 0x3F));
      *w++ = asciiFromCodepoint(cp);
      r += 2;
    } else if ((ch & 0xF0) == 0xE0 && (r[1] & 0xC0) == 0x80 && (r[2] & 0xC0) == 0x80) {
      uint16_t cp = (uint16_t)(((uint16_t)(ch & 0x0F) << 12) | ((r[1] & 0x3F) << 6) | (r[2] & 0x3F));
      *w++ = asciiFromCodepoint(cp);
      r += 3;
    } else if ((ch & 0xF8) == 0xF0 && (r[1] & 0xC0) == 0x80 && (r[2] & 0xC0) == 0x80 &&
               (r[3] & 0xC0) == 0x80) {
      *w++ = '?';  // BMP disi (emoji vb.)
      r += 4;
    } else {
      *w++ = asciiFromCodepoint(latin5ToCodepoint(ch));
      r++;
    }
  }
  *w = 0;
}

static int8_t hexVal(char ch) {
  if (ch >= '0' && ch <= '9') return (int8_t)(ch - '0');
  if (ch >= 'A' && ch <= 'F') return (int8_t)(ch - 'A' + 10);
  if (ch >= 'a' && ch <= 'f') return (int8_t)(ch - 'a' + 10);
  return -1;
}

bool ucs2HexDecode(char *s) {
  size_t len = strlen(s);
  if (len < 8 || (len & 3u) != 0 || s[0] != '0' || s[1] != '0') return false;
  for (size_t i = 0; i < len; i++)
    if (hexVal(s[i]) < 0) return false;
  char *w = s;
  for (size_t i = 0; i < len; i += 4) {
    uint16_t cp = (uint16_t)((hexVal(s[i]) << 12) | (hexVal(s[i + 1]) << 8) |
                             (hexVal(s[i + 2]) << 4) | hexVal(s[i + 3]));
    *w++ = asciiFromCodepoint(cp);
  }
  *w = 0;
  return true;
}

void sanitizeAscii(char *s) {
  for (; *s; s++) {
    uint8_t ch = (uint8_t)*s;
    if (ch == '\r' || ch == '\n' || ch == '\t') *s = ' ';
    else if (ch < 0x20 || ch >= 0x7F) *s = '?';
  }
}

void toUpperAscii(char *s) {
  for (; *s; s++)
    if (*s >= 'a' && *s <= 'z') *s = (char)(*s - 'a' + 'A');
}

void trimInPlace(char *s) {
  char *p = s;
  while (*p == ' ') p++;
  if (p != s) memmove(s, p, strlen(p) + 1);
  size_t n = strlen(s);
  while (n && s[n - 1] == ' ') s[--n] = 0;
}

// ---------------------------------------------------------------------------
// Telefon numaralari
// ---------------------------------------------------------------------------
uint8_t phoneNormalize(const char *in, char *out, uint8_t outSize) {
  uint8_t o = 0, digits = 0;
  bool first = true;
  if (!in || outSize < 2) return 0;
  for (; *in; in++) {
    char ch = *in;
    if (ch == ' ' || ch == '-' || ch == '(' || ch == ')' || ch == '.') continue;
    if (ch == '+' && first) {
      if (o + 1 >= outSize) return 0;
      out[o++] = '+';
    } else if (ch >= '0' && ch <= '9') {
      if (o + 1 >= outSize) return 0;
      out[o++] = ch;
      digits++;
    } else {
      out[0] = 0;
      return 0;
    }
    first = false;
  }
  out[o] = 0;
  if (digits < 7 || digits > 15) {
    out[0] = 0;
    return 0;
  }
  return digits;
}

static uint8_t lastDigits(const char *s, char *out10) {
  // Son en fazla 10 rakami out10'a yazar, toplam rakam sayisini dondurur.
  uint8_t total = 0;
  for (const char *p = s; *p; p++)
    if (*p >= '0' && *p <= '9') total++;
  uint8_t skip = total > 10 ? (uint8_t)(total - 10) : 0;
  uint8_t o = 0, seen = 0;
  for (const char *p = s; *p; p++) {
    if (*p >= '0' && *p <= '9') {
      if (seen++ >= skip) out10[o++] = *p;
    }
  }
  out10[o] = 0;
  return total;
}

bool phoneMatch(const char *a, const char *b) {
  if (!a || !b || !*a || !*b) return false;
  char da[11], db[11];
  uint8_t na = lastDigits(a, da);
  uint8_t nb = lastDigits(b, db);
  if (na < 7 || nb < 7) return false;
  if (na >= 10 && nb >= 10) return strcmp(da, db) == 0;
  return na == nb && strcmp(da, db) == 0;
}

// ---------------------------------------------------------------------------
// Sayilar, konum
// ---------------------------------------------------------------------------
bool parseUint16(const char *s, uint16_t *out) {
  if (!s || !*s) return false;
  uint32_t v = 0;
  for (; *s; s++) {
    if (*s < '0' || *s > '9') return false;
    v = v * 10u + (uint32_t)(*s - '0');
    if (v > 65535u) return false;
  }
  *out = (uint16_t)v;
  return true;
}

// [-]DDD[.dddddddd] bicimini dogrular; tam kismi 'maxInt'i asmamali.
static const char *parseCoord(const char *p, uint16_t maxInt) {
  if (*p == '-' || *p == '+') p++;
  uint16_t ip = 0;
  uint8_t nd = 0;
  while (*p >= '0' && *p <= '9') {
    ip = (uint16_t)(ip * 10u + (uint16_t)(*p - '0'));
    if (++nd > 3) return 0;
    p++;
  }
  if (nd == 0) return 0;
  bool fracNonZero = false;
  if (*p == '.') {
    p++;
    uint8_t nf = 0;
    while (*p >= '0' && *p <= '9') {
      if (*p != '0') fracNonZero = true;
      if (++nf > 8) return 0;
      p++;
    }
    if (nf == 0) return 0;
  }
  if (ip > maxInt || (ip == maxInt && fracNonZero)) return 0;
  return p;
}

bool locationNormalize(char *s) {
  char *w = s;
  for (char *r = s; *r; r++)
    if (*r != ' ') *w++ = *r;
  *w = 0;
  const char *p = parseCoord(s, 90);
  if (!p || *p != ',') return false;
  p = parseCoord(p + 1, 180);
  return p && *p == 0;
}

// ---------------------------------------------------------------------------
// Ag saati
// ---------------------------------------------------------------------------
static uint8_t two(const char *p) {
  if (p[0] < '0' || p[0] > '9' || p[1] < '0' || p[1] > '9') return 255;
  return (uint8_t)((p[0] - '0') * 10 + (p[1] - '0'));
}

bool parseCclk(const char *line, uint32_t *secs2000) {
  const char *p = strchr(line, '"');
  if (!p) return false;
  p++;
  // yy/MM/dd,hh:mm:ss
  if (strlen(p) < 17 || p[2] != '/' || p[5] != '/' || p[8] != ',' || p[11] != ':' || p[14] != ':')
    return false;
  uint8_t yy = two(p), mo = two(p + 3), dd = two(p + 6);
  uint8_t hh = two(p + 9), mi = two(p + 12), ss = two(p + 15);
  // Modem saati hic ayarlanmamissa 70/80 gibi varsayilanlar doner -> reddet.
  if (yy < 24 || yy > 69 || mo < 1 || mo > 12 || dd < 1 || dd > 31 || hh > 23 || mi > 59 ||
      ss > 59)
    return false;
  static const uint8_t mdays[12] PROGMEM = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  uint32_t days = 0;
  for (uint8_t y = 0; y < yy; y++) days += ((y & 3u) == 0) ? 366u : 365u;
  for (uint8_t m = 1; m < mo; m++) {
    days += pgm_read_byte(&mdays[m - 1]);
    if (m == 2 && (yy & 3u) == 0) days++;
  }
  days += (uint32_t)(dd - 1);
  *secs2000 = days * 86400UL + (uint32_t)hh * 3600UL + (uint32_t)mi * 60UL + ss;
  return true;
}
