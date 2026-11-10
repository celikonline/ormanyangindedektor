// textutil.h - SAF MANTIK (AVR + host). Sinirli metin tamponu, ASCII Turkce
// donusturme, UCS2 cozme, telefon numarasi karsilastirma, ag saati ayristirma.
#pragma once
#include "compat.h"

// En fazla 'cap' karakter tutan, tasmayan metin tamponu (SMS <= 160 garantisi).
class TextBuf {
public:
  TextBuf(char *buf, uint8_t cap) : b(buf), c(cap), n(0) { b[0] = 0; }
  void clear() { n = 0; b[0] = 0; }
  void add(const char *s);
  void addP(const char *s);          // PROGMEM dizgi
  void addChar(char ch);
  void addInt(int32_t v);
  void addUintPad(uint16_t v, uint8_t width);  // sifir dolgulu (ON1-0007)
  void addDec(int32_t v, uint8_t decimals);    // addDec(395, 2) -> "3.95"
  uint8_t length() const { return n; }
  const char *c_str() const { return b; }
private:
  char *b;
  uint8_t c;
  uint8_t n;
};

// Unicode kod noktasini ASCII'ye cevirir (c->c, g->g, i->i, o->o, s->s, u->u ...).
// Desteklenmeyen karakter icin '?' dondurur.
char asciiFromCodepoint(uint16_t cp);

// UTF-8 metni yerinde ASCII Turkce'ye cevirir.
void utf8ToAscii(char *s);

// Metin "0031003200330034..." gibi UCS2 hex ise yerinde ASCII'ye cozer ve true dondurur.
bool ucs2HexDecode(char *s);

// Yazdirilamayan/ASCII disi karakterleri '?' yapar (GSM 7-bit guvenli cikti).
void sanitizeAscii(char *s);

void toUpperAscii(char *s);
void trimInPlace(char *s);

// Numarayi normalize eder: '+' (varsa) ve rakamlar; bosluk, '-', '(', ')' atilir.
// Gecerliyse rakam sayisini (7..15), degilse 0 dondurur.
uint8_t phoneNormalize(const char *in, char *out, uint8_t outSize);

// Iki numara ayni aboneyi mi gosteriyor? (son 10 hane karsilastirmasi:
// "+905321112233" == "05321112233" == "5321112233")
bool phoneMatch(const char *a, const char *b);

// Ondalik tam sayi ayristirma (yalniz rakam). Basarisizsa false.
bool parseUint16(const char *s, uint16_t *out);

// "39.70512,26.85211" bicimini dogrular; bosluklari yerinde siler.
bool locationNormalize(char *s);

// +CCLK: "26/11/10,13:45:00+12" satirindan 2000-01-01'den beri gecen yerel saniyeyi cikarir.
bool parseCclk(const char *line, uint32_t *secs2000);
