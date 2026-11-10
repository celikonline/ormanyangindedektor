# ORMAN NÖBETÇİSİ ON-1 — Sistem Spesifikasyonu (Tek Doğru Kaynak)

> Bu dosya tüm teslimatların (firmware, devre şeması, BOM, 3B model, broşür, web sitesi) dayandığı **tek referanstır**.
> Pin, değer veya parça değişikliği önce burada yapılır.

Revizyon: **Rev A — 2026-11-10**

---

## 1. Ürün özeti

**Orman Nöbetçisi ON-1**, ağaçlara asılan, güneş enerjisiyle çalışan, beyaza boyanmış kalaylı sac (teneke) gövdeli bir
**erken orman yangını algılama düğümüdür**. Termal kamera (8×8 IR dizisi) + gaz/duman + sıcaklık/nem verilerini birleştirerek
yangını tespit eder; **SMS** ile 5 numaraya konum bağlantılı uyarı gönderir ve bulunduğu yerde **kırmızı strob ışık + 105 dB siren**
ile yerel alarm verir.

| Başlık | Değer |
|---|---|
| Mikrodenetleyici | ATmega328P-AU @ 8 MHz, 3,3 V (Arduino Pro Mini 3V3/8 MHz uyumlu, Optiboot) |
| Haberleşme | SIMCom **A7670E** LTE Cat-1 (B1/B3/B5/B7/B8/B20) + GSM 900/1800 yedek; SMS + sesli arama |
| Anten | Harici 3 dBi IP67 LTE çubuk anten, SMA bulkhead (teneke Faraday kafesi olduğu için **zorunlu**) |
| Termal algılama | Panasonic **AMG8833** Grid-EYE, 8×8 = 64 piksel, 60° FOV, 0–80 °C, ±2,5 °C |
| Gaz / ortam | Bosch **BME680** (VOC gaz direnci, sıcaklık, nem, basınç) |
| Kurcalama | SW-18010P titreşim/eğim anahtarı + kapak reed anahtarı |
| Test | Manyetik reed anahtarı (gövde dışından mıknatısla test/kurulum modu) |
| Yerel alarm | 6 × 1 W kırmızı (625 nm) LED strob halkası + 12 V 105 dB IP65 piezo siren |
| Güneş paneli | 6 V 3 W monokristal ETFE, 165 × 135 mm, 30° eğimli alüminyum braket (aynı zamanda güneşlik) |
| Şarj | CN3791 MPPT tek hücre Li-ion şarj, NTC ile 0–45 °C şarj koruması |
| Batarya | 2 × 18650 Li-ion 3500 mAh paralel (1S2P) = 7000 mAh / 25,9 Wh, DW01A+FS8205A koruma |
| Ortalama tüketim | ≈ 2,3 mA (≈ 56 mAh/gün) |
| Güneşsiz çalışma | ≥ 60 gün garanti hedefi (hesaplanan ≈ 95 gün, §5) |
| Gövde | Kalaylı sac teneke Ø153 × 178 mm (≈ 3 L), beyaz RAL 9010 ısı yansıtıcı boya, EPDM conta, IP54 |
| Çalışma sıcaklığı | −20 … +60 °C (şarj 0 … 45 °C) |
| Ağırlık | ≈ 1,3 kg (panel + braket dahil) |
| Montaj | 3–5 m yükseklik; paslanmaz gövde kelepçesi (Ø15–60 cm ağaç) veya M6 mapa + 2 mm paslanmaz halat |
| Algılama menzili | Termal sıcak nokta: 1 m² açık alev için tipik **25–30 m** (açık görüş, hesaplanan; saha testiyle doğrulanmalı) |
| Önerilen yerleşim | Yüksek riskli hatlar (piknik alanı, yol kenarı, yerleşim-orman ara yüzü) boyunca 50–100 m aralık |

---

## 2. Blok diyagram

```
 [Güneş Paneli 6V 3W] -> SS34 + SMBJ7.0A -> [CN3791 MPPT] -> [2x18650 + DW01A/FS8205A + PTC 3A] = VBAT (3.0–4.2 V)
                                                                         |
       +------------------+---------------------+------------------------+----------------------+
       |                  |                     |                        |                      |
 [MCP1700 3V3 LDO]  [Q1 AO3401A hi-side]  [MT3608 boost 12V]       [Q3 AO3400A low-side]   [Gerilim bölücüler]
       |                  |                     |                        |                   A0=VBAT, A1=SOLAR
  3V3: MCU, sensörler  VMODEM -> A7670E      12V -> Siren             6x1W LED strob
       |                  |  UART/DTR/RI (1.8V)
 [ATmega328P] <-- BSS138 seviye çevirici x4 --> A7670E (VDD_EXT=1.8V)
       |  I2C (SW-rail Q2)
  AMG8833 (0x69) + BME680 (0x77)
```

---

## 3. Pin haritası (ATmega328P / Arduino Pro Mini numaralandırması)

| Arduino pin | AVR pin | Sinyal adı | Yön | Açıklama |
|---|---|---|---|---|
| D0 | PD0 RXD | FTDI_RX | G | Programlama/hata ayıklama (6 pin FTDI başlığı) |
| D1 | PD1 TXD | FTDI_TX | Ç | Programlama/hata ayıklama |
| D2 | PD2 INT0 | TAMPER_N | G | Titreşim + kapak reed anahtarı (paralel, GND'ye), 1 MΩ pull-up 3V3, aktif LOW, kesme |
| D3 | PD3 INT1 | MODEM_RI_N | G | A7670E RI (seviye çevrilmiş), aktif LOW darbe = yeni SMS/çağrı, kesme ile uyandırma |
| D4 | PD4 | MODEM_PWRKEY | Ç | MMBT3904 (Q4) bazına 4,7 kΩ; HIGH = PWRKEY'i GND'ye çeker |
| D5 | PD5 | MODEM_DTR | Ç | BSS138 üzerinden A7670E DTR; HIGH = modem uyku izni, LOW = uyandır |
| D6 | PD6 OC0A | LED_STROBE | Ç | AO3400A (Q3) kapısı, 100 Ω seri + 100 kΩ pull-down; HIGH = LED'ler yanar |
| D7 | PD7 | MODEM_TXD→MCU_RX | G | SoftwareSerial RX (A7670E TXD, seviye çevrilmiş), 9600 bps |
| D8 | PB0 | MCU_TX→MODEM_RXD | Ç | SoftwareSerial TX (A7670E RXD, seviye çevrilmiş) |
| D9 | PB1 | SIREN_EN | Ç | MT3608 EN, 100 kΩ pull-down; HIGH = 12 V siren çalışır |
| D10 | PB2 | MODEM_PWR_EN | Ç | MMBT3904 (Q5) → AO3401A (Q1) kapısı; HIGH = modem beslemesi açık |
| D11 | PB3 MOSI | SENSOR_PWR_N | Ç | AO3401A (Q2) kapısı doğrudan, 100 kΩ pull-up; LOW = sensör rayı açık (I2C kilitlenme kurtarma) |
| D12 | PB4 MISO | STATUS_LED | Ç | Yeşil durum LED'i (1 kΩ), ışık borusu ile dışarıdan görünür |
| D13 | PB5 SCK | CHG_INHIBIT | Ç | Q12 BSS138 → CN3791 MPPT pinini GND'ye çeker; HIGH = şarj durur (NTC koruması, Δ1) |
| A0 | PC0 ADC0 | VBAT_SENSE | Analog | 1 MΩ / 330 kΩ bölücü + 100 nF, iç 1,1 V referans |
| A1 | PC1 ADC1 | SOLAR_SENSE | Analog | 1 MΩ / 150 kΩ bölücü + 100 nF, iç 1,1 V referans |
| A2 | PC2 | TEST_REED_N | G | Manyetik test reed anahtarı, iç pull-up, aktif LOW |
| A3 | PC3 | CHG_STAT_N | G | CN3791 CHRG (açık drenaj), iç pull-up, LOW = şarj oluyor |
| A4 | PC4 SDA | I2C_SDA | Ç/G | 4,7 kΩ pull-up (sensör rayına) |
| A5 | PC5 SCL | I2C_SCL | Ç | 4,7 kΩ pull-up (sensör rayına) |
| A6 | ADC6 | — | — | Yedek |
| A7 | ADC7 | BAT_NTC | Analog | 220 kΩ (3V3'ten) / NTC 10 kΩ B3950 (GND'ye) + 100 nF; 0–45 °C şarj penceresi, 3 °C histerezis (Δ1) |

**Bölücü hesapları (iç 1,1 V referans):**
- VBAT: oran = 330k/(1M+330k) = 0,2481 → 4,20 V ⇒ 1,042 V. `Vbat = adc * 1.1 / 1023 / 0.2481`
- SOLAR: oran = 150k/(1M+150k) = 0,1304 → 7,0 V (açık devre) ⇒ 0,913 V. `Vsol = adc * 1.1 / 1023 / 0.1304`
- Kalibrasyon katsayısı EEPROM'da (`vrefCal`, varsayılan 1.100).

---

## 4. Devre blokları ve parça değerleri

### 4.1 Güç girişi ve şarj
- J1 güneş paneli girişi (JST-XH 2p, PG7 kablo rakoru ile dışarı).
- D1 **SS34** seri ters polarite koruma; TVS1 **SMBJ7.0A** panel girişine paralel.
- C1 10 µF/25 V + C2 100 nF giriş.
- U3 **CN3791** MPPT şarj: harici P-MOSFET Q10 **AO3401A**, Schottky D2 **SS34**, bobin L1 **22 µH / 2 A**, akım algılama
  R_CS **0,24 Ω 1206** (I_ch = 120 mV / 0,24 Ω = 500 mA).
  MPPT bölücü: R_MP1 = 390 kΩ (üst), R_MP2 = 100 kΩ (alt) → V_MPPT = 1,205 × (1 + 390/100) = **5,90 V** (6 V panel Vmp).
  ~~TEMP pini~~ **CN3791'de TEMP pini yoktur (Δ1)**: batarya üzerine yapıştırılmış **NTC 10 kΩ B3950** (J3) A7'den okunur; sıcaklık 0–45 °C dışındaysa D13 → Q12 BSS138 MPPT pinini GND'ye çekerek şarjı durdurur.
  CHRG → A3 (MCU), ayrıca kırmızı 0603 LED (opsiyonel, DNP üretimde).
- Batarya: 2 × 18650 3500 mAh paralel tutucu, J2 (JST-PH 2p).
- U6 **DW01A** + **FS8205A** tek hücre koruma (aşırı deşarj 2,4 V, aşırı şarj 4,3 V, aşırı akım).
- F1 **PTC 3 A** (1812) → **VBAT** rayı.

### 4.2 3,3 V rayı
- U4 **MCP1700T-3302E/TT**, Iq 1,6 µA, 250 mA. Giriş/çıkış 1 µF + 10 µF MLCC.
- Beslediği: ATmega328P, BSS138 HV tarafı pull-up'ları, sensör rayı (Q2 üzerinden).

### 4.3 Modem (A7670E)
- Q1 **AO3401A** yüksek taraf anahtar VBAT → VMODEM; kapı 100 kΩ ile VBAT'a pull-up, Q5 **MMBT3904** (baz 10 kΩ, D10) ile GND'ye çekilir.
- VMODEM dekuplaj: C10, C11 **2 × 470 µF 6,3 V polimer** (düşük ESR, 2 A darbe), C12 100 nF, C13 33 pF, C14 10 pF; TVS **ESD5Z5.0**.
- PWRKEY: Q4 MMBT3904 kollektörü PWRKEY'e, baz 4,7 kΩ → D4. (Açma: ≥ 500 ms LOW darbe; kapatma: ≥ 2,5 s veya `AT+CPOF`.)
- UART/DTR/RI: **4 × BSS138** seviye çevirici; LV tarafı modem **VDD_EXT (1,8 V)** + 10 kΩ pull-up, HV tarafı 3V3 + 10 kΩ pull-up.
  Kanallar: (1) MODEM_TXD→D7, (2) D8→MODEM_RXD, (3) D5→DTR, (4) RI→D3.
- SIM: Nano-SIM tutucu (push-push), SIM_VDD 100 nF + 33 pF, **ESDA6V1-5SC6** ESD koruma, 22 Ω seri dirençler (DATA/CLK/RST).
- Anten: U.FL → 15 cm pigtail → SMA dişi bulkhead (O-ring) → 3 dBi harici IP67 LTE anten.
- NETLIGHT: mavi 0603 LED + 1 kΩ (DNP üretimde, sadece debug).

### 4.4 Sensörler (SNS-1 yardımcı kartı, JST-SH 6p kablo ile)
- Q2 **AO3401A**: 3V3 → V_SNS (D11 LOW = açık; 100 kΩ pull-up = varsayılan kapalı), C 10 µF + 100 nF.
- U7 **AMG8833** (I2C adres **0x69**, AD_SELECT=VDD), INT kullanılmıyor.
- U8 **BME680** (I2C adres **0x77**, SDO=VDD), ePTFE membranlı havalandırılmış hazne içinde.
- I2C pull-up 2 × 4,7 kΩ → V_SNS.
- AMG8833 penceresi: **0,4 mm HDPE** (8–14 µm LWIR geçirgen; cam/akrilik KULLANILMAZ) + paslanmaz tel örgü + yağmur siperliği.
  Sensör ekseni yataydan **35° aşağı** bakar.

### 4.5 Yerel alarm
- **LED strob:** 6 × 1 W kırmızı 625 nm LED (Vf ≈ 2,2 V), her biri **4,7 Ω 1 W** seri direnç ile VBAT'tan (~300 mA/LED, toplam ~1,8 A tepe),
  ortak katot hattı Q3 **AO3400A** ile GND'ye anahtarlanır. Kapı: 100 Ω seri, 100 kΩ pull-down, D6. Alüminyum MCPCB halka Ø50 mm,
  alt kapakta UV dayanımlı polikarbonat kubbe lens Ø70 mm. Desen: çift flaş (60 ms açık / 90 ms kapalı / 60 ms açık / 790 ms kapalı) ≈ %12 görev.
- **Siren:** U5 **MT3608** boost (L 22 µH, D SS34, R_FB 200 kΩ/18 kΩ → **12 V**, C_out 22 µF/25 V), EN = D9 (100 kΩ pull-down).
  Çıkış → J5 → 12 V 105 dB @30 cm IP65 piezo siren (~30 mA @12 V).

### 4.6 Diğer
- TAMPER: SW-18010P titreşim anahtarı ‖ kapak reed anahtarı (NO) → D2, 1 MΩ pull-up, 100 nF.
- TEST: reed anahtarı → A2 (iç pull-up), gövde etiketinde mıknatıs noktası.
- Kristal: 8 MHz 3225 + 2 × 22 pF. RESET: 10 kΩ pull-up + 100 nF (DTR otomatik reset için FTDI hattında).
- Başlıklar: J6 FTDI 6p (GND, CTS, 3V3, TX, RX, DTR), J7 ISP 2×3.
- PCB: **ON1-MB Rev A**, 2 katman FR4 1,6 mm, 78 × 58 mm, ENIG, **konformal kaplama** (akrilik, sensör ve konektörler hariç).

---

## 5. Güç bütçesi

| Tüketici | Akım | Süre/oran | Ortalama |
|---|---|---|---|
| ATmega328P power-down + WDT | 6 µA | sürekli | 0,006 mA |
| MCP1700 Iq | 1,6 µA | sürekli | 0,002 mA |
| Gerilim bölücüler | 3,2 µA | sürekli | 0,003 mA |
| AMG8833 uyku modu | 0,2 mA | sürekli | 0,200 mA |
| AMG8833 ölçüm | 4,5 mA | 0,3 s / 60 s | 0,023 mA |
| BME680 gaz ölçümü (ısıtıcı) | 12 mA | 0,15 s / 60 s | 0,030 mA |
| MCU aktif | 3 mA | 0,5 s / 60 s | 0,025 mA |
| A7670E uyku (DTR HIGH, CSCLK=1, DRX) | 2,0 mA | sürekli | 2,000 mA |
| Günlük durum SMS'i | 300 mA | 10 s / gün | 0,035 mA |
| **Toplam** | | | **≈ 2,32 mA ≈ 56 mAh/gün (0,21 Wh)** |

- Ek bekleme yükleri (Rev A şemasında eklendi): NTC bölücü + boost geri besleme bölücüsü ≈ 33 µA → toplam ≈ 2,35 mA ≈ 57 mAh/gün.
- Kullanılabilir kapasite: 7000 mAh × %80 (sıcaklık/yaşlanma payı) = 5600 mAh → **≈ 95–100 gün** güneşsiz (hesap). Ürün hedefi ≥ 60 gün.
- Güneş üretimi: 3 W × 1,0 tepe güneş saati (orman gölgesi, kötümser) × %75 = 2,25 Wh/gün ≈ **10× marj**.
- Alarm modu: LED ~216 mA ort. + siren ~110 mA + modem → ≈ 350 mA → tam batarya ile ≈ 15 saat kesintisiz alarm.
- Düşük batarya eşikleri: < 3,45 V uyarı SMS'i + tasarruf modu; < 3,30 V kritik (modem kapalı, sadece algılama; alarmda yine SMS denenir); > 3,60 V normale dönüş.

---

## 6. Firmware davranışı

### 6.1 Durum makinesi
- **NORMAL**: ölçüm periyodu 60 s (Angström risk indeksine göre: I < 2,0 ⇒ 20 s).
- **SUPHE (ön alarm)**: skor ≥ 2 → 5 s aralıkla 6 doğrulama ölçümü; bunlardan ≥ 3'ünde skor ≥ 3 ⇒ ALARM; aksi halde NORMAL.
- **ALARM**: skor ≥ 5 ise doğrudan. Işık + siren + tüm numaralara SMS + 1. numaraya sesli arama (opsiyonel, `ARAMA AC`).
  Alarm sürerken her 15 dk'da güncel SMS (en fazla 4). Siren: 3 dk açık / 2 dk kapalı döngü, toplam en fazla 30 dk; ışık 60 dk.
  10 dk boyunca skor = 0 ⇒ "YANGIN BELIRTISI SONA ERDI" SMS'i ⇒ NORMAL.
- **DUSUK_PIL / KRITIK**: bkz. §5.

### 6.2 Algılama skoru (çoklu sensör füzyonu)
Hassasiyet `HASSAS` 1 (düşük) / 2 (normal, varsayılan) / 3 (yüksek) eşikleri ölçekler (tabloda seviye 2 değerleri; seviye 1 ×1,3, seviye 3 ×0,75):
- **Termal** (AMG8833): `maxT` ≥ 70 °C ⇒ +3; değilse `maxT − medyan` ≥ 25 °C ⇒ +2, ≥ 12 °C ⇒ +1. `maxT` artış hızı ≥ 8 °C/dk ⇒ +1.
  Sıcak piksel sayısı (`> medyan + 10`) ≥ 3 ⇒ +1.
- **Gaz** (BME680): `oran = gazR / taban`; < 0,40 ⇒ +2; < 0,65 ⇒ +1. Taban: temiz havada EMA (α = 0,01), sadece NORMAL'de ve oran > 0,8 iken güncellenir; ilk 30 dk ısınma.
- **Ortam**: sıcaklık ≥ 55 °C ⇒ +2; 5 dk'da ≥ 6 °C artış ⇒ +1; 5 dk'da nem ≥ 15 puan düşüş ⇒ +1.
- **Angström yangın risk indeksi**: `I = RH/20 + (27 − T)/10`; I < 2,0 "ÇOK YÜKSEK", 2,0–2,5 "YÜKSEK", 2,5–4,0 "ORTA", > 4,0 "DÜŞÜK".

### 6.3 SMS komutları (format: `<PIN> KOMUT [parametre]`, büyük/küçük harf duyarsız, varsayılan PIN `1234`)
| Komut | Örnek | İşlev |
|---|---|---|
| DURUM | `1234 DURUM` | Anlık sensör, pil, risk, sinyal raporu |
| TEST | `1234 TEST` | 5 s ışık+siren testi + tüm numaralara test SMS'i |
| EKLE | `1234 EKLE 2 +905321112233` | Numara yuvası 1–5'e numara ekler (1 = yönetici) |
| SIL | `1234 SIL 2` | Yuvayı siler |
| LISTE | `1234 LISTE` | Kayıtlı numaraları listeler |
| KONUM | `1234 KONUM 39.70512,26.85211` | Kurulum koordinatı |
| AD | `1234 AD KazDagi-K3` | Cihaz adı (≤ 20 karakter) |
| HASSAS | `1234 HASSAS 3` | Hassasiyet 1/2/3 |
| SESSIZ | `1234 SESSIZ 30` | Yerel alarmı N dk susturur (SMS devam eder) |
| SIREN | `1234 SIREN KAPA` | Sireni kalıcı kapat/aç (`AC`/`KAPA`) |
| ARAMA | `1234 ARAMA AC` | Alarmda 1. numarayı sesli arama aç/kapat |
| RAPOR | `1234 RAPOR 24` | Periyodik durum SMS aralığı (saat, 0 = kapalı) |
| KALIBRE | `1234 KALIBRE` | Gaz tabanını sıfırlar |
| SIFIRLA | `1234 SIFIRLA` | Alarmı onaylar / durumu NORMAL'e döndürür |
| PIN | `1234 PIN 5678` | PIN değiştirir |

Güvenlik: PIN her zaman zorunlu; numara listesi doluysa gönderen listede olmalı; liste boşsa doğru PIN ile ilk `EKLE 1` komutu gönderen numarayı yönetici yapar.
Yanıtlar ASCII Türkçe (GSM 7-bit uyumlu: ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u), tek SMS ≤ 160 karakter.

### 6.4 Örnek alarm SMS'i (≤ 160 karakter)
```
YANGIN ALARMI! ON1-0007 KazDagi-K3 maps.google.com/?q=39.70512,26.85211 Termal:78C Gaz:%38 Hava:41C/%12 Pil:%86 Skor:6
```

### 6.5 Sağlamlık
- Watchdog: uyku için WDT kesme modu (8 s tik), aktif çalışmada 8 s reset modu.
- I2C kilitlenmesinde sensör rayı (Q2) kapatılıp açılır, sensörler yeniden başlatılır.
- Modem yanıt vermezse güç döngüsü (Q1), 3 başarısız denemede 30 dk sonra tekrar.
- EEPROM ayar yapısı: sihirli sayı + sürüm + CRC8; bozuksa varsayılanlar.
- Zaman: 8 s WDT tikleri ile sayılır, modemden ağ saati (`AT+CCLK?`) ile günlük düzeltilir.
- Modem: `AT+CMGF=1`, `AT+CNMI=2,1,0,0,0`, `AT+CSCLK=1`, `AT+CFGRI=1`, `AT+IPR=9600`.

---

## 7. Mekanik

- Gövde: Ø153 × 178 mm kalaylı sac teneke, dış beyaz RAL 9010 ısı yansıtıcı epoksi, iç korozyon astarı, 5 mm alüminyum yüzlü kapalı hücreli PE köpük iç kaplama.
- Kapak (üst): EPDM conta + 3 paslanmaz kilit klipsi; üzerinde 30° eğimli alüminyum panel braketi, panel–kapak arası 15 mm hava boşluğu (panel güneşlik görevi görür).
- Yan yüz (ön): AMG8833 termal penceresi Ø30 (HDPE 0,4 mm) + siperlik, 35° aşağı bakış; BME680 havalandırma (M12 ePTFE membran); siren Ø42.
- Yan yüz (arka): paslanmaz L braket + gövde kelepçesi bağlantısı; SMA anten bulkhead (anten yukarı); PG7 panel kablo rakoru.
- Alt: Ø70 polikarbonat kubbe içinde 6 LED strob halkası; drenaj deliği (labirentli) + basınç dengeleme ePTFE vent.
- İç: 3B baskı ASA şasi (PCB + 2×18650 tutucu + 10 g silika jel cebi).
- Etiket: cihaz ID, QR kod (kurulum kılavuzu), mıknatıs test noktası, uyarılar.

---

## 8. Kimlik / marka
- Ürün adı: **Orman Nöbetçisi**, Model: **ON-1**, Cihaz kimliği formatı: `ON1-XXXX`.
- Renkler: Orman yeşili `#1F4D3A`, Alarm turuncu-kırmızı `#E4572E`, Kum/kağıt `#F4F1EA`, Antrasit `#1B1F1D`.
- Slogan: "Ormanın gece gündüz uyanık gözü."

---

## 9. Firmware uygulama notları (Rev A, 2026-11-10)
Spesifikasyonun yorumlandığı / tamamlandığı noktaların tam listesi `firmware/README.md` §12'dedir. Özet:
- A2 test reed'i yalnızca uyandırma için PCINT kullanır (SoftwareSerial tüm PCINT vektörlerini sahiplenir); uyanıkken yoklanır.
- INT0/INT1 derin uykudan yalnızca LOW seviyede uyandırır; kesme tetiklenince kendini kapatır, hat HIGH'a dönünce yeniden kurulur.
- BME680 basıncı okunmaz (hiçbir kural kullanmıyor). Tüm hesaplar sabit noktalı (0,1 °C, 0,1 %RH, gaz oranı ‰, mV).
- Hassasiyet: gaz eşikleri düşüş (1 − oran) üzerinden ölçeklenir; sıcak piksel sayısı eşiği 4/3/2.
- EKLE / SIL / PIN yalnızca 1. numaradan kabul edilir (`ADMIN_ONLY_CONFIG`).
- Kurcalama SMS'i: 2 dk içinde 5 ayrı sarsıntı veya 10 sn sürekli LOW; saatte en fazla 1.
- Mıknatıs 2 sn: TEST + 10 dk kurulum modu. KRITIK pilde modem yalnızca alarmda açılır.
- Modem fabrika hızı 115200 ise ilk açılışta otomatik 9600'e ayarlanır.

## 10. Şema incelemesinde yapılan düzeltmeler (Δ1–Δ7, ON1-MB Rev A şemasında işaretli)
- **Δ1** CN3791'de TEMP/NTC pini yok → NTC A7'den okunur, D13 + Q12 ile MPPT pini GND'ye çekilerek şarj kesilir (firmware'e eklendi: `chargeTempControl()`). Şarj kesme yöntemi prototipte doğrulanmalı.
- **Δ2** Batarya konektörü J2: JST-PH → **JST-VH 2p** (LED + modem darbe akımları).
- **Δ3** MT3608 referansı 0,6 V → R50 = **10,5 kΩ %1** (200 kΩ ile 12,03 V).
- **Δ4** MT3608 EN LOW iken çıkış ≈ VBAT kalır → siren için **Q11 AO3400A** alt taraf anahtarı (D9 ile birlikte sürülür).
- **Δ5** NETLIGHT 1,8 V → mavi LED için Q13 sürücü (DNP).
- **Δ6** Kapak reed anahtarı **normalde kapalı (Form B)** olmalı (kapak kapalıyken açık, açılınca D2'yi LOW yapar).
- **Δ7** Q4/Q5 bazlarına **100 kΩ pull-down** (reset/ISP sırasında modem açılmasın).
- Riskler: BSS138 eşiği 1,8 V kapıda −20 °C'de sınırda (NX3008NBK alternatif); 2 A darbede VMODEM ≈ 0,25 V düşer (Q1 yumuşak başlatma önerilir); test mıknatısı çelik gövdeden zor algılanır → SW3 alt PC kubbe kenarına yerleştirildi.
