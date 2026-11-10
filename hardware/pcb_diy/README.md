# ON1-DIY Rev A — Orman Nöbetçisi ON-1 için ev yapımı taşıyıcı kart

Bu klasör, **Orman Nöbetçisi ON-1** orman yangını dedektörünün **evde, çıplak bakır plaketten** yapılabilen
sürümünü içerir. Seri üretim kartı (ON1-MB Rev A) TQFP ATmega328P ve LGA A7670E kullandığı için evde yapılamaz;
**ON1-DIY** aynı devreyi **hazır modüller + delikli (THT) parçalarla** kurar:

- Tek katman bakır (alt yüz), parçalar üst yüzde; hat genişliği ≥ 0,8 mm (sinyal), ≥ 1,5 mm (VBAT, modem,
  LED, GND güç yolları); aralık ≥ 0,5 mm; ped Ø ≥ 1,8 mm; GND bakır dökümü (≥ 0,6 mm aralık) aşındırma süresini kısaltır.
- Arduino pin atamaları **SPEC.md §3 ile birebir aynıdır** → firmware **değişmeden** çalışır.
- Kart: **100 × 75 mm**, 4 × M3 montaj deliği (köşelerden 4 mm), Ø153 mm teneke içindeki şasiye oturur.

Ayrıntılı pin eşlemesi, net listesi ve seri karttan farklar: **[ON1-DIY_netlist.md](ON1-DIY_netlist.md)**.
Malzeme listesi: **[ON1-DIY_BOM.csv](ON1-DIY_BOM.csv)** (UTF-8, `;` ayraçlı, Excel'de doğrudan açılır).

<!-- AUTO:SUMMARY -->
<!-- /AUTO:SUMMARY -->

## Klasör içeriği

| Dosya | Ne işe yarar |
|---|---|
| `print/ON1-DIY_bakir_toner_transfer.pdf` | Toner transfer için alt bakır, **2 kopya**, A4, 1:1 |
| `print/ON1-DIY_bakir_fotorezist_film.pdf` | Pozitif fotorezist için asetat film (2 film) |
| `print/ON1-DIY_bakir_negatif.pdf` | Negatif kuru film (dry-film) için ters görüntü |
| `print/ON1-DIY_yerlesim_ust.pdf` | Üst yüz yerleşim/serigrafi (1:1 + 2:1 + alt yüz SMD sayfası) |
| `print/ON1-DIY_delik_haritasi.pdf` | Delik haritası, matkap tablosu ve adetler |
| `gerber/ON1-DIY-B_Cu.gbr` … `ON1-DIY.drl` | RS-274X Gerber + Excellon (metrik), `ON1-DIY_gerber.zip` |
| `png/*.png` | 600 dpi önizlemeler (bakır, serigrafi, kompozit, üst/alt gerçekçi) |
| `ON1-DIY_BOM.csv` | Malzeme listesi + yaklaşık fiyatlar (USD) |
| `ON1-DIY_netlist.md` | Net → ped listesi, modül pin ↔ Arduino pin tablosu, farklar |
| `tools/` | Üreteç (Python) — kartı yeniden üretmek için |

## 1. Yazdırma (çok önemli: %100 ölçek)

1. PDF'i Adobe Reader / tarayıcıda açın → Yazdır → **"Gerçek boyut" / "%100" / "Actual size"** seçin.
   **"Sayfaya sığdır", "Fit to page", "Küçült" KAPALI** olmalı.
2. Çıktıdaki **50 mm ölçek çubuğunu cetvelle ölçün**. 50,0 mm değilse (ör. 48,5 mm) yazıcı ölçekliyordur → ayarı düzeltip tekrar yazdırın.
3. Lazer yazıcıda **en koyu / toner tasarrufu kapalı** ayarı kullanın. Mürekkep püskürtmeli yazıcı toner transferde **işe yaramaz**
   (asetat film için mürekkep püskürtmeli + transparan film olur ama lazer daha opaktır).

**Ayna (mirror) konusu:** Bakır kartın **alt** yüzündedir ve tüm çizimler **üstten bakış** ile yapılmıştır. Bu yüzden
bakır çıktıları **AYNALANMAMIŞTIR (bilerek)**: kâğıt/film toner yüzü bakıra gelecek şekilde ters çevrildiğinde görüntü
kendiliğinden aynalanır ve bakırda doğru (alttan bakış) desen oluşur. Kontrol: bakırdaki **"ON1-DIY ALT"** yazısı
kâğıtta **düz** okunur; bitmiş kartın bakır yüzüne bakınca **ters** okunur (üstten, FR4'ün içinden bakınca düz).

## 2. Plaketin hazırlanması

- Tek yüzlü FR4 bakır plaket (35 µm), en az 100 × 75 mm. Kesmek için maket bıçağıyla iki yüzden derin çizip kırın veya demir testeresi.
- Kenarları zımparalayın. Bakırı **ince bulaşık teli / 600-1000 kum zımpara** ile parlatın, sonra izopropil alkol (veya aseton) ile
  yağdan arındırın. Bundan sonra bakıra parmak sürmeyin.

## 3a. Toner transfer (ütü veya laminatör)

1. `ON1-DIY_bakir_toner_transfer.pdf`'i **parlak kuşe dergi kâğıdına** veya toner-transfer kâğıdına lazer yazıcıyla basın (2 kopya var; birini yedek tutun).
2. Kopyayı kenarlarından ~5 mm pay bırakarak kesin, **toner yüzü bakıra** gelecek şekilde yerleştirip kenarlardan kâğıt bantla sabitleyin.
3. **Ütü:** buharsız, en yüksek ısı (pamuk), önce 30 s hafif, sonra 3-5 dk boyunca tüm yüzeyi ağırlık vererek gezdirin (kenarlara dikkat).
   **Laminatör:** fotoğraf/kalın ayarda 5-8 kez geçirin (en düzgün sonucu bu verir).
4. Plaketi ılık suya bırakın (10-15 dk), kâğıdı parmakla ovarak katman katman sökün. Toner kalmalı, kâğıt lifleri kalmamalı.
5. Eksik/kopuk yerleri **permanent kalem** (asetat kalemi) ile düzeltin. Küçük kısa devreleri iğneyle kazıyın.

## 3b. Pozitif fotorezist (hazır kaplı plaket)

1. `ON1-DIY_bakir_fotorezist_film.pdf`'i asetata basın. Daha opak olması için **iki filmi üst üste** hizalayıp bantlayın.
2. Filmi **toner yüzü rezist yüzüne** değecek şekilde koyun, üstüne cam bastırın (temas tam olmalı).
3. UV pozlama: 395-405 nm UV LED ~10 cm'den **60-120 s** (önce bir şerit üzerinde 30/60/90/120 s test yapın).
4. Banyo: %0,5-1 NaOH (veya rezist üreticisinin developer'ı), desen belirince hemen suyla durulayın.
   Negatif kuru film kullanıyorsanız `ON1-DIY_bakir_negatif.pdf` (siyah = aşınacak) ve %1 Na₂CO₃ banyosu.

## 4. Aşındırma (FeCl₃ veya sodyum persülfat)

**Güvenlik:** nitril eldiven + koruyucu gözlük, iyi havalandırma, **plastik/cam kap** (metal kap ve metal maşa KULLANMAYIN),
çocuk ve hayvanlardan uzak. Sıçrayan FeCl₃ kalıcı kahverengi leke bırakır. Kullanılmış çözeltiyi **lavaboya dökmeyin**:
bakır içerir — kapalı şişede saklayıp atık toplama noktasına (belediye/kimyasal atık) verin.

- **Demir(III) klorür (FeCl₃):** ~40 °C ılık çözelti (sıcak su banyosunda), plaketi bakır yüzü aşağı yüzdürün veya sallayarak
  10-20 dk. Opak olduğu için arada çıkarıp kontrol edin.
- **Sodyum persülfat (Na₂S₂O₈):** 200 g/L, **45-50 °C** (daha soğukta çok yavaş), şeffaf olduğu için takip kolay, 15-30 dk.
  Toz halini su içine yavaşça ekleyin; kapalı kapta gaz birikir — kapağı sıkı kapatmayın.
- Tüm açık bakır gidince hemen bol suyla durulayın, toneri **aseton** veya tiner ile silin.

## 5. Kalaylama (önerilir)

Bakır oksitlenir ve teneke içinde nem vardır. Seçenekler: soğuk kimyasal kalaylama (sıvı kalay, 5-10 dk) **veya** havya + flux
ile ince kat lehim sürmek. Sonra izopropil alkolle temizleyin. İsteğe bağlı: montajdan sonra elektronik vernik/konformal kaplama
(konnektörlere ve modül pinlerine sürmeyin).

## 6. Delme

`print/ON1-DIY_delik_haritasi.pdf` tablosundaki uçları kullanın (özet aşağıda). Pedlerdeki **beyaz merkez noktası** ucu ortalar.
Dik matkap standı + karbür uç önerilir; elde delecekseniz 0,8 mm uç kolay kırılır — yavaş ve dik tutun. Önce en küçük uçla
tüm delikleri açın, sonra listeye göre büyütün. M3 montaj delikleri 3,2 mm.

<!-- AUTO:DRILL -->
<!-- /AUTO:DRILL -->

## 7. Atlama telleri (üst yüz)

Tek yüzlü kartta bazı bağlantılar kesişmek zorundadır; bunlar **üst yüzde düz tel köprü** (J-W1 …) ile yapılır. Uçlar 2,54 mm
katlarıdır (serigrafide çift çizgi + etiket). Ø0,6-0,8 mm kalaylı bakır tel (veya kesilmiş direnç bacağı) kullanın, karta
yatık ve gergin takın; VBAT/GND gibi güç hatlarındakiler için 0,8 mm. **Önce atlama tellerini** takın (diğer parçaların altında kalabilirler).

<!-- AUTO:JUMPERS -->
<!-- /AUTO:JUMPERS -->

## 8. Montaj sırası

1. Atlama telleri (J-W…).
2. **Alt yüz SMD**: Q1, Q2, Q6 (AO3401A, SOT-23) — bakır tarafına lehimlenir (yerleşim PDF'inin 3. sayfası, aynalı alt görünüm).
   Bir pedi kalaylayın, parçayı cımbızla yerleştirip o pedi eritin, sonra diğer bacakları lehimleyin. G-S-D yönüne dikkat.
3. Dirençler (yatık), BAT85 diyot (band = K), dik 1 W dirençler R8-R13 (saç tokası), seramik kondansatörler.
4. TO-92'ler: Q4, Q5, Q7 (2N3904, E-B-C), Q8 (2N7000, S-G-D), U6 (MCP1700, GND-VIN-VOUT) — düz yüz serigrafideki çizgiye.
   Bacaklar 2,54 mm'ye hafifçe açılır.
5. LED1 (düz kenar/kısa bacak = K), PTC F1, SW1, 1N5822 (D1, band = K), P6KE8.2A (TVS1, band = K).
6. Elektrolitikler C1, C10, C11 (**+ kare ped**), IRLZ44N (Q3, yazılı yüz serigrafi önüne).
7. Klemensler J1, J3, J5-J9, pin başlıkları J2, J4, J10.
8. Pro Mini (U1) ve BSS138 modülü (U3) için pin başlıkları (isterseniz dişi soket). Pro Mini'nin **güç LED'ini sökün**
   (uyku akımı ~1-3 mA yerine µA seviyesine iner) — isterseniz kart üstü regülatörü de sökebilirsiniz (RAW boş kalır).
   A4/A5 (ve A7) tek pinleri SparkFun v14 yerleşimindedir; klonunuzda bu delikler farklı yerdeyse o pinleri karttaki pedlere
   kısa tellerle bağlayın.
9. Modüller (kablo ile): CN3791 (U4: IN+, IN−, BAT−, BAT+ kalın tel; **CHRG → TP2**, **MPPT → TP1** ince tel),
   1S koruma kartı (U5: B+, P−, B−), MT3608 (U7: VIN+, VIN−, OUT+, OUT−). MT3608'i karta bağlamadan önce ayrı bir kaynaktan
   besleyip trimpotla **12,0 V**'a ayarlayın.

**TP1 (MPPT) teli:** CN3791 modülünde entegrenin **MPPT** pinine giden direnç bölücünün **orta noktasını** bulun
(pin numarası için kullandığınız modülün şemasına / CN3791 datasheet'ine bakın; bölücü panel girişinden GND'ye giden iki
dirençtir). TP1'i buraya ince bir telle bağlayın. D13 HIGH olunca Q8 (2N7000) bu düğümü GND'ye çeker, MPPT eşiği düşer ve
şarj durur (pil sıcaklığı 0-45 °C dışındayken firmware bunu yapar; SPEC güncellemesi: CN3791'de TEMP pini yoktur).
**TP2 (CHRG) teli:** modüldeki kırmızı CHRG LED'inin **katot** ucuna (entegrenin açık drenajlı CHRG pini) bağlanır;
BAT85 diyodu, LED'in panel tarafındaki besleme geriliminin A3'e ulaşmasını engeller (A3 iç pull-up ile okunur, LOW = şarj oluyor).

**Kapak reed anahtarı NC (Form-B)** olmalı: kapak kapalıyken mıknatıs anahtarı açık tutar, kapak açılınca kontak kapanır ve D2'yi
GND'ye çeker (titreşim anahtarı SW1 ile paralel).

## 9. İlk çalıştırma kontrolleri (multimetre)

Pil, panel ve modüller **takılı değilken**:

1. **VBAT–GND arası kısa devre YOK** (ölçü: > 100 kΩ civarı; bölücüler yüzünden sonsuz olmayabilir). PACK+–GND, SOL+–GND, 3V3–GND,
   VMOD–GND için de kısa devre olmadığını kontrol edin.
2. Diyot ölçümü: J1 SOL+ → D1 → C1+ yönünde ~0,2-0,3 V (Schottky), ters yönde açık.
3. Pili takın (koruma kartı bağlı, önce akım sınırlı güç kaynağı 3,7 V / 200 mA ile denemek en iyisi):
   - VBAT (F1 çıkışı) ≈ pil gerilimi. Boşta akım (Pro Mini takılı değil) < 10 µA olmalı.
   - **3V3 (U6 çıkışı, J4.1 değil!) = 3,30 V ± %2.**
   - **J2.1 VMOD = 0 V** (modem kapalı: D10 LOW/girişte, Q5 bazı 100 k ile çekili). D10'u HIGH yaptığınızda VBAT görünmeli.
   - **J7 siren = 0 V** (D9 LOW). LED halka anotları (J5.3 … J6.4) ≈ VBAT, K uçları ile ölçüm yapmayın.
   - **J4.1 V_SNS = 0 V** (D11 HIGH = sensörler kapalı) — Pro Mini takılı değilken R21 kapıyı 3V3'e çeker.
4. Pro Mini'yi takıp FTDI ile firmware'i yükleyin (FTDI adaptörünü **3,3 V** konumuna alın; pil bağlıyken FTDI'nin VCC'sini
   bağlamamak en temizidir). Seri monitörde açılış mesajını görün; mıknatısla test reed'ini (J9) tetikleyin.
5. Modem kartını (J2) en son bağlayın; VMOD hattında 2 A darbeler için 0,5 mm² kablo kullanın.

## 10. CNC ile izolasyon frezeleme (FlatCAM)

1. FlatCAM'de `gerber/ON1-DIY-B_Cu.gbr`, `ON1-DIY-Edge_Cuts.gbr` ve Excellon `ON1-DIY.drl` dosyalarını açın (birim: mm).
2. Alt katmanı freze için **X ekseninde aynalayın** (Tools → Double-Sided PCB / Mirror, eksen = kart merkezi X = 50 mm)
   — çünkü plaket bakır yüzü yukarı bakacak şekilde tezgâha bağlanır. Delikleri de aynı eksenle aynalayın.
3. Isolation Routing: V-uç 20-30°, takım çapı ~0,2 mm, **3-4 geçiş**, %15-20 bindirme (0,5 mm aralık bunu rahat kaldırır).
   Bakır döküm (GND) sayesinde kaldırılacak bakır azdır; isterseniz "Non-copper clearing" ile kalan adacıkları temizleyin.
4. Drill: 0,8 / 1,0 / 1,2 / 1,3 / 1,5 / 3,2 mm takımlar (veya hepsini 0,8 mm ile delip büyüklerini elde büyütün).
5. Cutout: 2 mm freze, 4 köprü (tab), kalınlık 1,6 mm.
6. Kalaylama ve montaj yukarıdaki gibi.

## 11. Üreticiye sipariş (JLCPCB / PCBWay vb.)

`gerber/ON1-DIY_gerber.zip` dosyasını yükleyin: **Layers = 1**, 1,6 mm FR4, HASL, 1 oz bakır, lehim maskesi yeşil, serigrafi beyaz.
Tek katmanlı siparişte bakır alt yüzde olacak şekilde dosyalar hazırlanmıştır (`B_Cu`, `B_Mask`, `F_SilkS`, `Edge_Cuts`, `.drl`).
Tek katmanlı kartlarda delikler kaplamasızdır (NPTH) — tasarım buna göre yapılmıştır (THT parçalar bakır tarafından lehimlenir).
Atlama tellerini fabrika kartında da takmanız gerekir (tek katman).

## 12. Kartı yeniden üretmek

```
cd hardware/pcb_diy/tools
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
python autoroute.py      # yerleşim design.py'den; yönlendirme -> routes.json (birkaç dakika)
python build.py          # DRC + bağlantı kontrolü + Gerber/Excellon + geri okuma doğrulaması + PDF/PNG/BOM/netlist
```

- `design.py` — tüm parça yerleşimi, net atamaları, elle çizilmiş güç hatları (tek doğru kaynak).
- `footprints.py` — ayak izleri (ev yapımı için büyütülmüş pedler; Pro Mini ve BSS138 modül ölçüleri SparkFun Eagle dosyalarından).
- `router.py`, `negotiate.py`, `route.py`, `autoroute.py` — 0,254 mm ızgarada A* yönlendirici, müzakereli tıkanıklık
  çözümü (PathFinder), gerektiğinde üst yüz atlama teli ekleme, GND'nin bakır dökümle bağlanması.
- `copper.py` — shapely ile kesin geometri: GND dökümü + termal ped bağlantıları, DRC, bakır geometrisinden bağlantı kontrolü.
- `gerber.py`, `outputs.py`, `artwork.py`, `silk.py`, `docs.py` — çıktılar. `verify.py` — Gerber/Excellon'u bağımsız bir
  ayrıştırıcıyla (gerbonara) geri okuyup 20 µm çözünürlükte bağlantı ve aralık kontrolü.
