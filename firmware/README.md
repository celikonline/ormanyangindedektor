# Orman Nöbetçisi ON-1 — Firmware

Güneş enerjili erken orman yangını algılama düğümü **ON-1** için Arduino firmware'i.
Tek doğru kaynak: [`../SPEC.md`](../SPEC.md) (Rev A). Pin, eşik veya davranış değişikliği **önce SPEC.md'de** yapılır.

| | |
|---|---|
| Hedef | ATmega328P @ 8 MHz, 3,3 V — Arduino Pro Mini 3V3/8 MHz uyumlu |
| FQBN | `arduino:avr:pro:cpu=8MHzatmega328` |
| Çekirdek | Arduino AVR Boards **1.8.8** (`arduino:avr`) |
| Bellek (üretim derlemesi, `DEBUG 0`) | Flash **27 040 / 30 720 B (%88)**, global RAM **733 / 2048 B (%35)** |
| Bellek (`DEBUG 1`) | Flash ≈ 28 000 B (%91), RAM ≈ 900 B (%44) — yalnız geliştirme için |

---

## 1. Dosya yapısı

```
firmware/
├── OrmanNobetcisi/           Arduino sketch klasörü
│   ├── OrmanNobetcisi.ino    durum makinesi (NORMAL / SUPHE / ALARM + pil modları), SMS metinleri
│   ├── config.h              tüm ayarlar, eşikler, süreler, DEBUG anahtarı
│   ├── pins.h                pin haritası (SPEC §3 — değiştirmeyin)
│   ├── compat.h              AVR/PC ortak katmanı (PROGMEM)
│   ├── storage.h/.cpp        EEPROM ayar yapısı: sihirli sayı + sürüm + CRC8        [saf + AVR]
│   ├── textutil.h/.cpp       SMS tamponu (≤160), ASCII Türkçe, UCS2, telefon, ağ saati [saf]
│   ├── detector.h/.cpp       skor, Angström indeksi, gaz tabanı EMA, artış geçmişi    [saf]
│   ├── commands.h/.cpp       SMS komut ayrıştırıcı + PIN / beyaz liste güvenliği      [saf]
│   ├── power.h/.cpp          WDT uykusu, saat, kesmeler, ADC (iç 1,1 V), raylar
│   ├── sensors.h/.cpp        AMG8833 + BME680 doğrudan yazmaç sürücüsü, I2C kurtarma
│   ├── alarm.h/.cpp          Timer2 çift flaş strob, siren döngüsü, susturma
│   └── modem.h/.cpp          A7670E güç/PWRKEY, AT, SMS, RI/DTR uykusu, CSQ, ağ saati, arama
└── test/
    ├── test_logic.cpp        [saf] modüllerin birim testleri (PC'de g++/clang++/cl)
    ├── Makefile, run_tests.cmd
    └── node/                 C++ derleyici olmayan ortamlar için Node.js yedeği
```

**[saf]** dosyalar Arduino'ya bağımlı değildir; aynı kaynak hem AVR'de hem PC'de derlenir ve test edilir.

---

## 2. Kütüphaneler

| Kütüphane | Sürüm | Not |
|---|---|---|
| Arduino AVR Boards (`arduino:avr`) | 1.8.8 | çekirdek |
| SoftwareSerial | 1.0 (çekirdekle gelir) | A7670E, 9600 bps |

**Başka kütüphane gerekmez.** `Wire`, `EEPROM`, Adafruit AMG88xx / BME680 kullanılmaz:

* Adafruit AMG88xx 1.3.2 + Adafruit BME680 2.0.6 (+ Unified Sensor 1.1.15, BusIO 1.17.4) yalnız başına
  **14,6 KB flash + 933 B RAM** tutuyor (ölçüldü); modem/komut koduyla birlikte 30 KB'ye **sığmıyor** (~38 KB).
* Bunun yerine `sensors.cpp` içinde ~2 KB'lık doğrudan yazmaç sürücüsü var: Bosch BME680 tamsayı dengeleme
  formülleri (sıcaklık, nem, ısıtıcı) + gaz direnci formülü; Panasonic Grid-EYE yazmaç haritası; AMG8833 **uyku modu**
  (0,2 mA — SPEC §5 güç bütçesi buna dayanır).
* `Wire` yerine zaman aşımlı, yoklamalı küçük bir TWI sürücüsü var (−1,3 KB flash, −160 B RAM; hiçbir I2C beklemesi
  MCU'yu kilitleyemez). EEPROM için doğrudan `avr/eeprom.h` (`eeprom_update_block`).
* Firmware'de kayan nokta (float) **hiç yoktur**: tüm hesaplar sabit noktalı (0,1 °C, 0,1 %RH, binde oran, mV).

---

## 3. Derleme

### 3.1 Arduino IDE (2.x)
1. *Boards Manager* → **Arduino AVR Boards 1.8.8** kurulu olsun.
2. `firmware/OrmanNobetcisi/OrmanNobetcisi.ino` dosyasını açın (klasör adı sketch adıyla aynı olmalı).
3. *Tools → Board*: **Arduino Pro or Pro Mini**; *Processor*: **ATmega328P (3.3V, 8 MHz)**.
4. Cihaza özel kimlik: `config.h` → `#define DEVICE_ID_DEFAULT 7` (SMS'lerde `ON1-0007`).
5. *Verify* (✓). Beklenen çıktı: `Sketch uses 27040 bytes (88%)… Global variables use 733 bytes (35%)`.

### 3.2 arduino-cli
```sh
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.8
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 --warnings all firmware/OrmanNobetcisi

# Cihaz kimliğini kaynak değiştirmeden vermek için:
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 \
  --build-property "build.extra_flags=-DDEVICE_ID_DEFAULT=7" firmware/OrmanNobetcisi

# Hata ayıklama derlemesi (D0/D1 FTDI, 38400 bps log):
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 \
  --build-property "build.extra_flags=-DDEBUG=1" firmware/OrmanNobetcisi
```
> `DEVICE_ID_DEFAULT` yalnız EEPROM boş/bozukken kullanılır. Önceden kurulmuş bir karta farklı kimlik vermek için
> `storage.h` içindeki `SETTINGS_VERSION` değerini artırın (tüm ayarlar varsayılana döner) veya EEPROM'u silin.

---

## 4. Sigorta (fuse) ve bootloader

| Sigorta | Değer | Anlamı |
|---|---|---|
| Low | `0xFF` | harici kristal 8 MHz, 16K CK başlangıç |
| High | `0xDA` | 2 KB bootloader alanı, SPIEN |
| Extended | `0xFD` | BOD 2,7 V |

* SPEC, **Optiboot** öngörür. Arduino'nun Pro Mini için verdiği eski `ATmegaBOOT_168_atmega328_pro_8MHz` yükleyicisi
  watchdog sıfırlamasından sonra WDT'yi kapatmaz ve kart **sonsuz sıfırlama döngüsüne** girebilir. Firmware WDT'yi
  `.init3` aşamasında hemen kapatır ama yükleyici önce çalıştığı için **Optiboot önerilir**:
  * ISP programlayıcı (USBasp / Arduino-as-ISP) ile J7 (2×3) başlığından, örn. MiniCore
    (`MiniCore:avr:328:clock=8MHz_external,bootloader=uart0,BOD=2v7`) → *Burn Bootloader*.
    Optiboot 0,5 KB yer kaplar; firmware her iki yükleyiciye de (30 720 B sınırı) sığar.
  * Alternatif: bootloader'sız, doğrudan ISP ile yükleme (`arduino-cli upload -P usbasp …`).
* BOD 2,7 V uygundur (MCP1700 3,3 V çıkışı pil 3,0 V'a inene kadar regülasyonda kalır).

## 5. FTDI ile yükleme

1. **3,3 V** FTDI (FT232RL/CH340, 3V3 lojik) kullanın. J6: `GND, CTS, 3V3, TX, RX, DTR`
   (FTDI TX → kart RX, FTDI RX → kart TX; DTR otomatik reset içindir).
2. Piller takılıysa FTDI'nin 3V3 besleme ucunu **bağlamayın** (MCP1700 çıkışına geri besleme olmasın); yalnız
   GND/TX/RX/DTR yeterlidir. Pilsiz masada FTDI 3V3 MCU'yu besleyebilir (modem bu durumda açılamaz).
3. ```sh
   arduino-cli upload -p COM5 --fqbn arduino:avr:pro:cpu=8MHzatmega328 firmware/OrmanNobetcisi
   ```
   IDE'de: *Sketch → Upload*. Port Linux'ta `/dev/ttyUSB0`.

---

## 6. İlk kurulum prosedürü

1. **SIM kart:** SMS destekli, LTE/2G hattı. Telefonda **SIM PIN kilidini kapatın**. Kartı nano-SIM yuvasına takın.
2. Harici LTE antenini SMA'ya takın (teneke gövde Faraday kafesidir; antensiz çekmez).
3. Pilleri takın / ana anahtarı açın. LED dizisi:
   * 1 s sürekli yanar → açılış,
   * (3 hızlı yanıp sönme → sensör bulunamadı),
   * modem açılırken 10–60 s karanlık,
   * **2 kısa** → şebeke tamam · **5 kısa** → modem/şebeke yok (antene, SIM'e bakın).
4. Yönetici numarasını ekleyin (liste boşken **gönderen numara** yönetici olur):
   ```
   1234 EKLE 1 +905321112233
   ```
   Yanıt: `ON1-0007 TAMAM: yonetici 1 = +905321112233`
5. Kurulum koordinatı ve cihaz adı:
   ```
   1234 KONUM 39.70512,26.85211
   1234 AD KazDagi-K3
   ```
6. Diğer numaralar (yuva 2–5) ve PIN değişimi (önerilir):
   ```
   1234 EKLE 2 +905321112244
   1234 PIN 5678
   ```
7. Cihazı ağaca 3–5 m yüksekliğe, termal pencere yataydan 35° aşağı bakacak şekilde asın.
8. **Mıknatıs testi** yapın (§9) ve `5678 DURUM` ile raporu kontrol edin.
9. Gaz tabanı ilk **30 dakikada** ısınır; bu sürede gaz puanı verilmez. Temiz havada `5678 KALIBRE` tabanı sıfırlar.

---

## 7. SMS komut referansı

Biçim: `<PIN> KOMUT [parametre]` — büyük/küçük harf duyarsız, varsayılan PIN `1234`.
Türkçe karakterli yazım da kabul edilir (`SİL`, `SESSİZ`, `SİREN AÇ`; UTF-8, Latin-5 veya UCS2 SMS).
Tüm yanıtlar `ON1-XXXX` ile başlar, ASCII'dir ve en fazla 160 karakterdir.

| Komut | Örnek | İşlev | Örnek yanıt |
|---|---|---|---|
| DURUM | `1234 DURUM` | Anlık sensör, pil, risk, sinyal raporu | bkz. §8 |
| TEST | `1234 TEST` | 5 s ışık+siren testi + **tüm numaralara** test SMS'i | (ayrı yanıt yok; test SMS'i gelir) |
| EKLE | `1234 EKLE 2 +905321112233` | Yuva 1–5'e numara (1 = yönetici) ¹ | `TAMAM: 2 = +905321112233` |
| SIL | `1234 SIL 2` | Yuvayı siler ¹ | `TAMAM: 2 silindi` |
| LISTE | `1234 LISTE` | Kayıtlı numaralar | `LISTE 1:+90532… 2:- 3:- 4:- 5:-` |
| KONUM | `1234 KONUM 39.70512,26.85211` | Kurulum koordinatı (parametresiz: mevcut konumu gösterir) | `TAMAM: KONUM 39.70512,26.85211` |
| AD | `1234 AD KazDagi-K3` | Cihaz adı ≤ 20 karakter (harf, rakam, `- _ .`; boşluk → `-`) | `TAMAM: AD KazDagi-K3` |
| HASSAS | `1234 HASSAS 3` | Hassasiyet 1 (düşük) / 2 (normal) / 3 (yüksek) | `TAMAM: HASSAS 3 (yuksek)` |
| SESSIZ | `1234 SESSIZ 30` | Yerel alarmı N dk susturur, 0 = iptal (SMS devam eder), en fazla 1440 | `TAMAM: yerel alarm 30 dk sessiz (SMS devam eder)` |
| SIREN | `1234 SIREN KAPA` | Sireni kalıcı kapat/aç (`AC`/`KAPA`; parametresiz: durum) | `TAMAM: SIREN KAPALI` |
| ARAMA | `1234 ARAMA AC` | Alarmda 1. numarayı 30 s sesli arama aç/kapat | `TAMAM: ARAMA ACIK` |
| RAPOR | `1234 RAPOR 24` | Periyodik durum SMS'i (saat, 0 = kapalı, ≤168) → yalnız 1. numaraya | `TAMAM: RAPOR 24 saat` |
| KALIBRE | `1234 KALIBRE` | Gaz tabanını sıfırlar (bir sonraki ölçüm yeni taban) | `TAMAM: gaz tabani sifirlandi` |
| SIFIRLA | `1234 SIFIRLA` | Alarmı onaylar, NORMAL'e döner, ışık/siren kapanır | `TAMAM: alarm onaylandi, durum NORMAL` |
| PIN | `1234 PIN 5678` | PIN değiştirir (4–6 rakam) ¹ | `TAMAM: PIN degistirildi` |

¹ `ADMIN_ONLY_CONFIG 1` (varsayılan): EKLE / SIL / PIN yalnız **1. numaradan** kabul edilir.

**Güvenlik kuralları**
* PIN her zaman zorunludur. Kayıtlı bir numaradan yanlış PIN → `HATA: PIN yanlis`.
* Liste doluysa **listede olmayan numaralara hiç yanıt verilmez** (SMS harcanmaz, cihaz ifşa edilmez).
* Liste boşsa yalnız doğru PIN'li `EKLE 1` kabul edilir; **gönderen numara** yönetici olur.
* Hatalı biçim → `HATA: bicim: …`; bilinmeyen komut → komut listesi.

---

## 8. SMS örnekleri

```
YANGIN ALARMI! ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:78C Gaz:%38 Hava:41C/%12 Pil:%86 Skor:6
YANGIN DEVAM 1/4! ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:95C Gaz:%31 Hava:44C/%10 Pil:%84 Skor:8
YANGIN BELIRTISI SONA ERDI ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:27C Gaz:%92 Hava:26C/%35 Pil:%80 Skor:0
TEST OK ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:24C Gaz:%98 Hava:23C/%45 Pil:%86 Sinyal:18 Skor:0
KURCALAMA UYARISI! ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Pil:%86
DUSUK PIL UYARISI ON1-0007 KazDagi-K3 Pil:3.44V/%8 Gunes:0.3V Tasarruf modu
KRITIK PIL! ON1-0007 KazDagi-K3 Pil:3.29V/%1 Gunes:0.0V Modem kapaniyor, yalniz algilama
PIL NORMALE DONDU ON1-0007 KazDagi-K3 Pil:3.65V/%25 Gunes:6.1V
DURUM ON1-0007 KazDagi-K3 NORMAL Termal:24/22C Gaz:%98 Hava:23C/%45 Risk:ORTA(3.1) Pil:3.95V/%80 Gunes:5.2V Sarj:E Sinyal:18 Skor:0 Saat:13:45
```
* `Termal` = en sıcak piksel (DURUM'da `maks/medyan`), `Gaz:%38` = gaz direnci / temiz hava tabanı,
  `Hava` = BME680 sıcaklık/nem, `Risk` = Angström indeksi, `Sinyal` = CSQ (0–31, 99 bilinmiyor),
  `Sarj:E/H` = güneşten şarj oluyor mu. Konum ayarlı değilse `Konum:YOK` yazılır; okunamayan değer `-`.
* Uzun ad + tüm bayraklar (`SUPHE DUSUK PIL … SESSIZ SirenKapali`) bir araya gelirse DURUM metni 160 karakterde
  kesilir (sondaki `Saat` düşer).
* RAPOR SMS'i DURUM ile aynıdır, `RAPOR` ile başlar.

---

## 9. LED durum kodları (yeşil, ışık borusu)

| Desen | Anlam |
|---|---|
| 1 s sürekli | açılış |
| 3 hızlı (açılışta) | sensör bulunamadı (AMG8833 ve/veya BME680) |
| 2 kısa (açılışta) | modem hazır, şebekeye kayıtlı |
| 5 kısa (açılışta) | modem yanıt vermiyor / şebeke yok |
| Her ölçümde 1 kısa (60 s / 20 s) | NORMAL, her şey yolunda |
| Her ölçümde 2 kısa | modem kapalı / 30 dk bekleme (3 başarısız deneme) |
| Her ölçümde 3 kısa | sensör hatası (I2C ray döngüsü denendi) |
| Her ölçümde 4 kısa | DÜŞÜK PİL veya KRİTİK PİL |
| 5 s'de bir 0,3 s | SÜPHE (doğrulama ölçümleri) |
| Strob ile birlikte çift flaş | ALARM |
| Mıknatıs yaklaştırınca sürekli | mıknatıs algılandı (2 s tutun) |
| Kurulum modunda: 1 uzun + N kısa | anlık skor N (nişan alma yardımı) |

---

## 10. Test prosedürü

### 10.1 Mıknatıs testi (sahada, kapak açmadan)
1. Mıknatısı gövde etiketindeki **mıknatıs noktasına** tutun → LED sürekli yanar.
2. **2 s** tutun ve çekin. Sonuç:
   * 5 s strob + siren (siren `SIREN KAPA` ile kapatıldıysa yalnız strob),
   * tüm kayıtlı numaralara `TEST OK …` SMS'i (sinyal gücü dahil),
   * **10 dk kurulum modu:** 5 s'de bir ölçüm, LED 1 uzun + skor kadar kısa yanıp söner; bu sürede kurcalama SMS'i
     gönderilmez (kapak açılabilir).
3. Isı testi (kurulum modunda): 1–2 m mesafeden **güvenli bir ısı kaynağı** (sıcak su şişesi, saç kurutma makinesi)
   gösterin; LED'deki skor artmalı. Skor ≥ 2 SÜPHE'ye, doğrulamada ≥ 3/6 veya tek ölçümde ≥ 5 **gerçek ALARM**'a geçer
   (SMS'ler gider). Testten sonra `<PIN> SIFIRLA` gönderin. Ormanda açık alev **kullanmayın**.

### 10.2 `TEST` komutu
`1234 TEST` → 5 s ışık + siren ve tüm numaralara test SMS'i (kurulum modu açılmaz).

### 10.3 Birim testleri (PC)
```sh
cd firmware/test
make                     # g++ (veya: make CXX=clang++)
run_tests.cmd            # Windows: g++ / clang++ / cl sırayla denenir
node node/test_logic.mjs # C++ derleyici yoksa Node.js yedeği (aynı test vektörleri)
```
Kapsam: CRC8 ve ayar doğrulama, TextBuf ≤160 sınırı, ASCII Türkçe/UTF-8/Latin-5/UCS2 dönüşümü, telefon eşleştirme,
konum doğrulama, `+CCLK` ayrıştırma, Angström sınırları, pil yüzdesi, termal istatistik, tüm skor kuralları ve
hassasiyet ölçeklemesi, gaz tabanı EMA/ısınma/KALIBRE, artış hızı ve 5 dk pencereleri, tüm SMS komutları ve güvenlik
kuralları.

---

## 11. Davranış özeti (SPEC §5–§6)

**Durum makinesi**
* **NORMAL:** 60 s'de bir ölçüm; Angström I < 2,0 ise 20 s. Gaz tabanı yalnız burada güncellenir.
* **SÜPHE:** skor ≥ 2 → 5 s arayla 6 doğrulama; ≥ 3'ünde skor ≥ 3 (veya herhangi birinde ≥ 5) → ALARM, yoksa NORMAL.
* **ALARM:** skor ≥ 5 → doğrudan. Strob 60 dk; siren 3 dk açık / 2 dk kapalı, toplam ≤ 30 dk; tüm numaralara SMS
  (teslim edilemeyen numaralara 60 s'de bir, en fazla 10 deneme); `ARAMA AC` ise 1. numara 30 s aranır. 15 dk'da bir
  güncel SMS (en fazla 4). 10 dk boyunca skor = 0 → `YANGIN BELIRTISI SONA ERDI` → NORMAL. ALARM'da 10 s'de bir ölçüm.
* **DÜŞÜK PİL** (< 3,45 V, 3 ardışık ölçüm): uyarı SMS'i, ölçüm periyodu ×2.
  **KRİTİK** (< 3,30 V): uyarı SMS'i, modem kapatılır, yalnız algılama; alarmda modem açılıp SMS yine denenir.
  > 3,60 V → normale dönüş (yöneticiye SMS). Işık/siren yükü altındayken karar verilmez.

**Algılama skoru** (seviye 2 eşikleri; seviye 1 ×1,3, seviye 3 ×0,75)

| Kural | Puan |
|---|---|
| maxT ≥ 70 °C | +3 |
| aksi halde maxT − medyan ≥ 25 °C / ≥ 12 °C | +2 / +1 |
| maxT artış hızı ≥ 8 °C/dk | +1 |
| sıcak piksel (> medyan + 10 °C) sayısı ≥ 3 | +1 |
| gaz oranı < 0,40 / < 0,65 (ısınma sonrası) | +2 / +1 |
| ortam ≥ 55 °C | +2 |
| 5 dk'da ortam ≥ 6 °C artış | +1 |
| 5 dk'da nem ≥ 15 puan düşüş | +1 |

Angström: `I = RH/20 + (27 − T)/10` → < 2,0 ÇOK YÜKSEK, 2,0–2,5 YÜKSEK, 2,5–4,0 ORTA, > 4,0 DÜŞÜK.

**Güç / sağlamlık**
* Uyku: power-down + WDT kesmesi (8 s tik; 8 s'den yakın olay için 4/2/1 s). Uyanma: WDT, INT0 kurcalama,
  INT1 modem RI, A2 test reed (pin-change). Aktif çalışmada WDT 8 s **sıfırlama** modunda.
* Alarm/test sırasında MCU *idle* uykuda kalır; strob deseni Timer2 kesmesinde üretildiği için SMS gönderimi gibi
  uzun işlemler deseni bozmaz.
* Saat WDT tikleriyle sayılır; modem ağ saati (`AT+CCLK?`, `AT+CTZU=1`) ile günlük düzeltilir ve WDT tik süresi
  buna göre kalibre edilir.
* I2C hatası → sensör rayı (Q2) kapatılıp açılır, sensörler yeniden başlatılır; AMG8833 çıkışı ray açılışından sonraki
  15 s puanlamaya alınmaz.
* Modem yanıt vermezse güç döngüsü (Q1); 3 başarısız denemede 30 dk bekleme. RI kaçırılırsa diye SIM 30 dk'da bir
  taranır. Modem ayarları: `ATE0, AT+IPR=9600, AT+CMGF=1, AT+CSCS="IRA", AT+CPMS="SM","SM","SM",
  AT+CNMI=2,1,0,0,0, AT+CFGRI=1, AT+CTZU=1, AT+CSCLK=1`. A7670E fabrika hızı 115200 ise ilk açılışta otomatik
  olarak 9600'e çekilir.
* EEPROM ayarları: sihirli sayı + sürüm + CRC8; bozuksa varsayılanlar yüklenir. Yazma `eeprom_update_block` ile
  (yalnız değişen baytlar).
* Kurcalama: 2 dk içinde ≥ 5 ayrı sarsıntı **veya** hattın ≥ 10 s LOW kalması (kapak açık) → tüm numaralara
  `KURCALAMA UYARISI` (en fazla saatte 1; kurulum modunda ve kritik pilde gönderilmez).

---

## 12. SPEC'e göre yorumlar ve küçük sapmalar

| Konu | Uygulama |
|---|---|
| Sensör kütüphaneleri | Adafruit yerine doğrudan sürücü (flash/RAM; ayrıntı §2). Davranış aynı. |
| Basınç | BME680 basıncı okunmaz/dengelenmez: hiçbir kural veya SMS kullanmıyor (kod + ölçüm süresi tasarrufu). |
| `vrefCal` | EEPROM'da mV tamsayı olarak saklanır (`vrefMv`, varsayılan 1100 = 1,100 V). |
| Hassasiyet ölçeklemesi | Sıcaklık/hız/nem eşikleri ×k; gaz eşikleri **düşüş miktarı** (1 − oran) üzerinden ×k (aksi halde seviye 1 daha hassas olurdu); sıcak piksel sayısı round(3k) = 4/3/2. |
| Gaz ısınması | İlk 30 dk gaz puanı yok; bu sürede taban α = 0,1 ile hızlı izlenir, sonra SPEC'teki α = 0,01 (oran > 0,8, yalnız NORMAL). |
| "5 dk'da" artış/düşüş | Son 330 s içindeki geçmiş örneklerine göre en büyük artış/düşüş (geçmiş 50 s'de bir, 8 kayıt). |
| Yönetici yetkisi | EKLE/SIL/PIN yalnız 1. numara (`ADMIN_ONLY_CONFIG`, 0 yapılırsa tüm kayıtlı numaralar). |
| Tasarruf modu | SPEC tanımlamadığı için: ölçüm periyodu ×2, RAPOR/DURUM devam eder. |
| Kurcalama/mıknatıs | SPEC yalnız donanımı tanımlar; eşikler, SMS ve 10 dk kurulum modu bu firmware'in yorumudur. |
| A2 test reed kesmesi | PCINT vektörleri SoftwareSerial'e ait olduğundan A2 yalnız uyandırma kaynağıdır (uyumadan önce SoftwareSerial dinlemesi kapatılır); uyanıkken pin yoklanır. |
| Erken uyanma | INT0/INT1/PCINT ile erken uyanılırsa o WDT periyodunun geçen kısmı (≤ 8 s) saate eklenmez; günlük ağ saati düzeltmesi bunu telafi eder. |
| SIFIRLA sonrası | Yangın sürüyorsa bir sonraki ölçümler yeniden SÜPHE/ALARM'a geçebilir (güvenli taraf). Yerinde ekip için `SESSIZ` kullanın. |

## 13. Batarya sıcaklık koruması (şema incelemesi Δ1, 2026-11-10)

CN3791 şarj entegresinde sıcaklık (TEMP/NTC) girişi bulunmadığı için Li-ion şarj sıcaklık penceresi firmware tarafından uygulanır:

- **A7 (ADC7) = BAT_NTC:** 3V3 → 220 kΩ → A7 → NTC 10 kΩ B3950 → GND (NTC hücrelere yapıştırılır, J3).
- **D13 = CHG_INHIBIT:** HIGH olduğunda Q12 BSS138, CN3791'in MPPT pinini GND'ye çekerek şarjı durdurur.
- Her ölçüm döngüsünde `chargeTempControl()` çağrılır: 0 °C altı (≥ 437 mV) veya 45 °C üstü (≤ 64 mV) → şarj durur; 3–42 °C aralığına dönünce (381…72 mV) tekrar başlar.
- NTC kopuk (≥ 1000 mV) veya kısa devre (≤ 20 mV) → güvenli tarafta kalınır, şarj durdurulur.
- `DURUM` SMS'inde şarj alanı: `Sarj:E` (şarj oluyor), `Sarj:H` (hayır), `Sarj:SICAK`, `Sarj:SOGUK`, `Sarj:NTC?`.
- D13 aynı zamanda ISP SCK hattıdır; ISP programlama sırasında şarjın kısa süre kesilmesi zararsızdır.

Derleme (bu değişiklikle): Flash 27 040 B (%88), RAM 733 B (%35).
