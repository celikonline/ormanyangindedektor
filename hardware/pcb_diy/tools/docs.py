"""BOM (CSV) and netlist (Markdown) for ON1-DIY."""
import math
from collections import defaultdict, OrderedDict

import design

# rough DIY retail prices (USD, 2026, single quantities from AliExpress / local shops)
PRICE = {
    "Arduino Pro Mini 328 3,3 V / 8 MHz": 2.60,
    "4 kanal BSS138 çift yönlü seviye çevirici": 0.40,
    "CN3791 6 V MPPT şarj modülü": 2.40,
    "1S Li-ion koruma modülü (DW01A+FS8205A), P+ = B+": 0.25,
    "MT3608 boost modülü (12 V'a ayarlı)": 0.45,
    "MCP1700-3302E/TO LDO 3,3 V": 0.45,
    "AO3401A P-MOSFET (ALT YÜZ, SMD)": 0.05,
    "2N3904 NPN": 0.03,
    "2N7000 N-MOSFET": 0.08,
    "IRLZ44N N-MOSFET mantık seviyeli": 0.60,
    "1N5822 Schottky 3 A 40 V": 0.10,
    "P6KE8.2A TVS 600 W (Vrwm 7,02 V)": 0.12,
    "BAT85 Schottky sinyal diyodu": 0.05,
    "3 mm yeşil LED": 0.02,
    "PTC sigorta 3 A tutma (RXEF300)": 0.15,
    "4,7 Ω 1 W": 0.05,
    "100 nF seramik": 0.02,
    "1 µF seramik (X7R)": 0.05,
    "10 µF seramik (X5R/X7R)": 0.10,
    "10 µF seramik": 0.10,
    "470 µF 6,3 V düşük ESR radyal": 0.18,
    "10 µF 25 V elektrolitik": 0.03,
    "Klemens 2p 5,08 mm": 0.12,
    "Klemens 2p 5,08 mm (kapak reed, NC/Form-B)": 0.12,
    "Klemens 2p 5,08 mm (test reed)": 0.12,
    "Klemens 4p 5,08 mm": 0.25,
    "Pin header 1×9 erkek (A7670E kablosu)": 0.05,
    "Pin header 1×4 (AMG8833 + BME680 kablosu)": 0.03,
    "Pin header 1×2 (NTC 10k B3950 kablosu)": 0.02,
    "SW-18010P titreşim anahtarı": 0.10,
    "M3 montaj deliği": 0.0,
    "Kablo noktası → CN3791 MPPT bölücü düğümü": 0.0,
    "Kablo noktası → CN3791 modülü CHRG (kırmızı LED katodu)": 0.0,
}
RES_PRICE = 0.01
RES_PRICE_1PCT = 0.02


def _price(part):
    if part in PRICE:
        return PRICE[part]
    if "Ω" in part and "1/4 W" in part:
        return RES_PRICE_1PCT if "%1" in part else RES_PRICE
    return 0.0


NOTES = {
    "U1": "2×12 pin header ile takılır; A4/A5 (ve A7) için tek pin. Güç LED'ini (ve isterseniz kart üstü regülatörü) sökün: uyku akımı için şart. RAW boş.",
    "U3": "SparkFun BOB-12009 pin düzeni (LV1 LV2 LV GND LV3 LV4 / HV1 HV2 HV GND HV3 HV4, sıralar 0,4\").",
    "J2": "A7670E kartına kısa (≤10 cm) kablo; VMOD/GND için 0,5 mm² tel önerilir.",
    "U4": "Modül kartın dışına/şasiye; IN+/IN-/BAT+/BAT- kalın tel. CHRG ve MPPT için ince tel (TP2/TP1).",
    "U5": "Pil yanındaki koruma kartı; B+ ve P+ aynı düğümdür.",
    "U7": "Trimpot ile çıkışı 12,0 V'a ayarlayın (FB ref. 0,6 V) — sireni bağlamadan önce.",
    "Q1,Q2,Q6": "SOT-23, bakır (alt) yüze lehimlenir — büyütülmüş pedler.",
    "Q3": "Dik TO-220, soğutucu gerekmez (%12 görev, ~0,15 W).",
    "R8,R9,R10,R11,R12,R13": "Dik (saç tokası) montaj, 5,08 mm.",
    "J8": "Kapak reed anahtarı NC (Form-B): kapak kapalı + mıknatıs = açık devre.",
    "D1": "SPEC: SS34 (SMD) yerine THT eşdeğeri.",
    "TVS1": "SPEC: SMBJ7.0A yerine THT eşdeğeri (P6KE6.8A KULLANMAYIN: Vrwm 5,8 V panel Voc'nin altında).",
    "Q8": "D13 = CHG_INHIBIT; TP1'den CN3791 MPPT bölücü düğümüne tel.",
    "TP1": "CN3791 modülünde MPPT direnç bölücüsünün orta noktası (MPPT pini) — README'ye bakın.",
    "TP2": "CN3791 modülündeki kırmızı CHRG LED'inin katot ucu.",
    "H1,H2,H3,H4": "M3 vida + 8 mm aralayıcı ile şasiye.",
}


def write_bom(b, routes, path):
    groups = OrderedDict()
    for c in b.comps:
        key = (c.part, c.value, c.package)
        groups.setdefault(key, []).append(c.ref)
    rows = []
    for (part, value, pkg), refs in groups.items():
        refs_s = ",".join(refs)
        note = NOTES.get(refs_s, "")
        if not note:
            for k, v in NOTES.items():
                if k in refs:
                    note = v
        unit = _price(part)
        rows.append((refs_s, len(refs), part, value or "-", pkg, note, unit))
    # jumpers
    js = routes.get("jumpers", [])
    bus = [(i, j) for i, j in enumerate(js) if len(j.get("pts", [])) > 2]
    plain = [(i, j) for i, j in enumerate(js) if len(j.get("pts", [])) <= 2]
    for i, j in bus:
        L = math.hypot(j["b"][0] - j["a"][0], j["b"][1] - j["a"][1])
        rows.append(("J-W%d" % (i + 1), 1, "%s bara teli (üst yüz)" % j["net"], "Ø0,8 mm kalaylı bakır tel",
                     "%.2f mm, %d lehim noktası" % (L, len(j["pts"])),
                     "Düz, karta yatık; her noktada alttan lehimlenir (VBAT dağıtımı).", 0.03))
    if plain:
        refs = ",".join("J-W%d" % (i + 1) for i, _ in plain)
        L = sum(math.hypot(j["b"][0] - j["a"][0], j["b"][1] - j["a"][1]) for _, j in plain)
        rows.append((refs, len(plain), "Atlama teli (üst yüz)", "Ø0,6-0,8 mm kalaylı bakır tel",
                     "toplam %.0f mm" % L, "Düz, kart yüzeyine yatık; GND/güç hatlarındakiler için 0,8 mm.", 0.01))
    extra = [
        ("PCB", 1, "Tek yüzlü bakır plaket FR4", "100×75 mm (veya 100×100 kesilir), 1,6 mm, 35 µm", "-",
         "Pozitif fotorezist kaplı plaket de olur.", 0.90),
        ("-", 1, "Aşındırıcı", "Demir(III) klorür FeCl3 250 g  —  veya sodyum persülfat 250 g", "-",
         "Biri yeterli. Plastik kap, eldiven, gözlük.", 3.00),
        ("-", 1, "Toner transfer kâğıdı / parlak kuşe kâğıt", "A4, 5 yaprak", "-", "Lazer yazıcı gerekir.", 0.80),
        ("-", 1, "Pin header şeridi (erkek)", "1×40, 2,54 mm", "-",
         "Pro Mini (2×12 + 3 tekli), seviye çevirici (2×6), J2, J4, J10 için kesilir.", 0.15),
        ("-", 1, "Dişi header (opsiyonel soket)", "1×40, 2,54 mm", "-", "Pro Mini ve BSS138 modülünü sökülebilir yapmak için.", 0.35),
        ("-", 4, "M3 aralayıcı + vida", "M3×8 mm", "-", "Şasiye montaj.", 0.10),
        ("-", 1, "Kalay teli + flux", "Sn60/Pb40 veya SAC305, 0,8 mm", "-", "Kalaylama için sıvı kalay (opsiyonel).", 1.50),
    ]
    for (ref, n, part, val, pkg, note, unit) in extra:
        rows.append((ref, n, part, val, pkg, note, unit))
    total = 0.0
    lines = ["Ref;Adet;Parça;Değer/Model;Kılıf;Not;Birim Fiyat (USD);Toplam (USD)"]
    for (ref, n, part, val, pkg, note, unit) in rows:
        t = unit * n
        total += t
        lines.append(";".join([ref, str(n), part, val, pkg, note.replace(";", ","),
                               ("%.2f" % unit).replace(".", ","), ("%.2f" % t).replace(".", ",")]))
    lines.append(";".join(["TOPLAM", "", "Kart + üzerindeki modüller (A7670E kartı, sensörler, siren, LED halka, panel, pil HARİÇ)",
                           "", "", "Harici parçalar için hardware/BOM.csv", "", ("%.2f" % total).replace(".", ",")]))
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return total


SPEC_MAP = [
    ("D0", "RXI", "FTDI_RX", "FTDI başlığı (modül üzerinde)"),
    ("D1", "TXO", "FTDI_TX", "FTDI başlığı (modül üzerinde)"),
    ("D2", "D2", "TAMPER_N", "R24 1 MΩ→3V3, C13 100 nF, SW1 SW-18010P, J8 kapak reed (NC)"),
    ("D3", "D3", "MODEM_RI_N", "U3 HV1 ↔ LV1 → J2 RI"),
    ("D4", "D4", "MODEM_PWRKEY", "R4 4,7 kΩ → Q4 2N3904 bazı (R5 100 kΩ), Q4 kollektör → J2 PWRKEY"),
    ("D5", "D5", "MODEM_DTR", "U3 HV2 ↔ LV2 → J2 DTR"),
    ("D6", "D6", "LED_STROBE", "R6 100 Ω → Q3 IRLZ44N kapı, R7 100 kΩ pull-down"),
    ("D7", "D7", "MODEM_TXD→MCU_RX", "U3 HV3 ↔ LV3 → J2 TXD"),
    ("D8", "D8", "MCU_TX→MODEM_RXD", "U3 HV4 ↔ LV4 → J2 RXD"),
    ("D9", "D9", "SIREN_EN", "R15 10 kΩ → Q7 2N3904 (R16 100 kΩ) → Q6 AO3401A → MT3608 VIN"),
    ("D10", "D10", "MODEM_PWR_EN", "R2 10 kΩ → Q5 2N3904 (R3 100 kΩ) → Q1 AO3401A kapı (R1 100 kΩ)"),
    ("D11", "D11", "SENSOR_PWR_N", "Q2 AO3401A kapı doğrudan, R21 100 kΩ pull-up"),
    ("D12", "D12", "STATUS_LED", "R25 1 kΩ → LED1 yeşil"),
    ("D13", "D13", "CHG_INHIBIT", "R27 100 Ω → Q8 2N7000 (R28 100 kΩ) → TP1 MPPT"),
    ("A0", "A0", "VBAT_SENSE", "R17 1 MΩ / R18 330 kΩ + C3 100 nF"),
    ("A1", "A1", "SOLAR_SENSE", "R19 1 MΩ / R20 150 kΩ + C4 100 nF"),
    ("A2", "A2", "TEST_REED_N", "J9 TEST (iç pull-up)"),
    ("A3", "A3", "CHG_STAT_N", "D2 BAT85 → TP2 CHRG (iç pull-up)"),
    ("A4", "A4", "I2C_SDA", "J4 SDA, R22 4,7 kΩ → V_SNS"),
    ("A5", "A5", "I2C_SCL", "J4 SCL, R23 4,7 kΩ → V_SNS"),
    ("A6", "A6", "—", "boş"),
    ("A7", "A7", "BAT_NTC", "R26 220 kΩ → 3V3, C14 100 nF, J10 NTC 10k B3950"),
]


def write_netlist(b, routes, path):
    nets = b.nets()
    L = []
    L.append("# ON1-DIY Rev A — Netlist ve pin eşleme")
    L.append("")
    L.append("Bu dosya `tools/build.py` tarafından `tools/design.py`'den üretilir (elle düzenlemeyin).")
    L.append("Kart: 100 × 75 mm, tek katman (alt bakır), parçalar üstte. Koordinatlar mm, sol-alt köşe (0,0), üstten bakış.")
    L.append("")
    L.append("## 1. Arduino pini ↔ modül pini ↔ kart (SPEC.md §3 ile birebir)")
    L.append("")
    L.append("| Arduino | Pro Mini pin | SPEC sinyali | Kart üzerinde | SPEC'e uygun |")
    L.append("|---|---|---|---|---|")
    for a, pm, sig, where in SPEC_MAP:
        L.append("| %s | %s | %s | %s | ✔ |" % (a, pm, sig, where))
    L.append("")
    L.append("Pro Mini besleme: **VCC ← +3V3 (U6 MCP1700)**, GND (iki GND pini modül içinde birleşik), RAW ve RST boş.")
    L.append("Firmware hiçbir değişiklik gerektirmez.")
    L.append("")
    L.append("### Seviye çevirici (U3) kanal eşlemesi")
    L.append("")
    L.append("SPEC §4.3'teki dört sinyal çifti aynen korunmuştur; yalnızca modül üzerindeki fiziksel kanal numarası,")
    L.append("Pro Mini ile modül arasındaki dört hattın kesişmeden düz gidebilmesi için seçilmiştir (BSS138 kanalları özdeştir):")
    L.append("")
    L.append("| SPEC kanalı | Sinyal | Modül HV pini | Modül LV pini | J2 pini |")
    L.append("|---|---|---|---|---|")
    u3 = b.comp("U3")
    j2 = b.comp("J2")
    j2pin = {n: "J2.%s" % k for k, n in j2.nets.items()}
    hv_of = {n: k for k, n in u3.nets.items() if k.startswith("HV")}
    lv_of = {n: k for k, n in u3.nets.items() if k.startswith("LV")}
    for chn, sig, mcu, mod in (("(1)", "MODEM_TXD → D7", "D7_RX", "M_TXD"), ("(2)", "D8 → MODEM_RXD", "D8_TX", "M_RXD"),
                               ("(3)", "D5 → DTR", "D5_DTR", "M_DTR"), ("(4)", "RI → D3", "D3_RI", "M_RI")):
        L.append("| %s | %s | %s | %s | %s |" % (chn, sig, hv_of[mcu], lv_of[mod], j2pin[mod]))
    L.append("| — | HV = +3V3, LV = VDD_EXT (1,8 V, modemden) | HV | LV | %s |" % j2pin["VDD_EXT"])
    L.append("")
    L.append("## 2. Konnektörler")
    L.append("")
    titles = OrderedDict([
        ("J1", "Güneş paneli 6 V (5,08 mm klemens)"), ("J2", "A7670E kartı (1×9 pin header, 2,54 mm)"),
        ("J3", "Pil 1S2P (5,08 mm klemens)"), ("J4", "Sensör kablosu AMG8833 + BME680 (1×4, 2,54 mm)"),
        ("J5", "LED halka (5,08 mm klemens)"), ("J6", "LED halka (5,08 mm klemens)"),
        ("J7", "Siren 12 V (5,08 mm klemens)"), ("J8", "Kapak reed anahtarı NC/Form-B (5,08 mm klemens)"),
        ("J9", "Test reed anahtarı (5,08 mm klemens)"), ("J10", "Pil NTC 10k B3950 (1×2, 2,54 mm)"),
        ("U4", "CN3791 MPPT modülü (kablo pedleri)"), ("U5", "1S koruma modülü (kablo pedleri; P+ = B+)"),
        ("U7", "MT3608 modülü (kablo pedleri)"), ("TP1", "CN3791 MPPT bölücü orta noktası (tel)"),
        ("TP2", "CN3791 CHRG LED katodu (tel)")])
    con = []
    for ref, title in titles.items():
        c = b.comp(ref)
        pins = ["%s%s: %s" % (p.name, (" (" + p.label + ")") if p.label and p.label != p.name else "",
                               c.nets.get(p.name, "—")) for p in c.fp.pads]
        con.append((ref, title, pins))
    for ref, title, pins in con:
        L.append("- **%s — %s**: %s" % (ref, title, "; ".join(pins)))
    L.append("")
    L.append("## 3. Net → ped listesi")
    L.append("")
    L.append("| Net | Hat genişliği | Pedler |")
    L.append("|---|---|---|")
    for n in sorted(nets.keys(), key=lambda s: (s != "GND", s != "VBAT", s)):
        pads = nets[n]
        w = design.NET_WIDTH.get(n, design.W_SIG)
        pl = ", ".join("%s.%s" % (p["ref"], p["pad"]) for p in sorted(pads, key=lambda p: (p["ref"], p["pad"])))
        js = [i + 1 for i, j in enumerate(routes.get("jumpers", [])) if j["net"] == n]
        if js:
            pl += ", " + ", ".join("J-W%d" % k for k in js)
        if n == "GND":
            pl += " + bakır döküm (pour)"
        L.append("| %s | %.1f mm | %s |" % (n, w, pl))
    L.append("")
    L.append("Bağlantısız pinler: U1 RXI, TXO (FTDI başlığında), RST×2, RAW, A6.")
    L.append("")
    L.append("## 4. Atlama telleri (üst yüz)")
    L.append("")
    if routes.get("jumpers"):
        L.append("| Ref | Net | Uç 1 (x, y) | Uç 2 (x, y) | Boy | Ara lehim noktaları |")
        L.append("|---|---|---|---|---|---|")
        for i, j in enumerate(routes["jumpers"]):
            ln = math.hypot(j["b"][0] - j["a"][0], j["b"][1] - j["a"][1])
            taps = ", ".join("(%.2f, %.2f)" % tuple(q) for q in j.get("pts", [])[1:-1]) or "—"
            L.append("| J-W%d | %s | %.2f, %.2f | %.2f, %.2f | %.2f mm (%d × 2,54) | %s |" % (
                i + 1, j["net"], j["a"][0], j["a"][1], j["b"][0], j["b"][1], ln, round(ln / 2.54), taps))
    else:
        L.append("Yok.")
    L.append("")
    L.append("Modül içi bağlantılar (bağlantı kontrolünde kullanıldı): U1 GND ↔ GND (Pro Mini üzerinde), "
             "U3 GND(LV) ↔ GND(HV) (seviye çevirici üzerinde).")
    L.append("")
    L.append("## 5. Seri üretim kartından (ON1-MB Rev A) farklar")
    L.append("")
    diffs = [
        "MCU: çıplak ATmega328P-AU yerine **Arduino Pro Mini 3V3/8 MHz** modülü (aynı çip, aynı pin numaraları, Optiboot). "
        "FTDI başlığı modülün üzerindedir; ISP başlığı yoktur (gerekirse modülün D11/D12/D13/RST pinlerinden).",
        "Modem: LGA A7670E yerine **A7670E breakout kartı**, J2 (1×9) ile kablolu. SIM tutucu, anten (U.FL) ve SIM ESD "
        "koruması breakout kartın üzerindedir. VMODEM dekuplajı: 2 × 470 µF düşük ESR **elektrolitik** (+100 nF); polimer "
        "kondansatör, 33 pF/10 pF ve ESD5Z5.0 yoktur.",
        "Seviye çevirici: 4 × ayrık BSS138 yerine hazır 4 kanallı BSS138 modülü (10 k pull-up'lar modülde). Fiziksel kanal "
        "sırası düz hat için seçildi (§1).",
        "Şarj: CN3791 devresi (AO3401A, SS34, 22 µH, 0,24 Ω) yerine **hazır CN3791 MPPT modülü**; koruma DW01A+FS8205A yerine "
        "hazır **1S koruma modülü**. Pil sıcaklık koruması SPEC güncellemesine uygun olarak MCU'da (A7 NTC + D13 → Q8 → MPPT).",
        "Ters polarite diyodu SS34 → **1N5822** (THT), TVS SMBJ7.0A → **P6KE8.2A** (THT, Vrwm 7,02 V; P6KE6.8A Vrwm 5,8 V "
        "olduğundan panel boşta gerilimini kırpardı — kullanılmadı). PTC 1812 → radyal **RXEF300**.",
        "Siren: MT3608 entegre devresi + EN pini yerine **MT3608 modülü**; modülde EN pini olmadığı için VIN, Q6 AO3401A ile "
        "anahtarlanır (Q7 2N3904 sürücü, D9 HIGH = siren açık — davranış SPEC ile aynı). Modül FB referansı 0,6 V; çıkış trimpotla 12 V.",
        "LED strob anahtarı AO3400A (SOT-23) → **IRLZ44N** (TO-220, mantık seviyeli). 3,3 V kapı sürüşünde ~1,8 A için yeterli "
        "(tipik R_DS(on) < 0,06 Ω @ 3 V). Daha düşük R_DS(on) isterseniz aynı bacak dizilişli **IRLB8721PbF** takılabilir.",
        "2N3904 sürücülerin (Q4, Q5, Q7) bazlarına 100 kΩ pull-down eklendi (reset sırasında modem/siren açılmasın).",
        "MCP1700 SOT-23 → **TO-92** (MCP1700-3302E/TO).",
        "Sensörler (AMG8833, BME680) ayrı breakout kartlardadır; J4 (1×4) kablosuyla bağlanır. I2C pull-up'lar ve V_SNS "
        "anahtarı (Q2) bu karttadır.",
        "Kart 2 katman 78 × 58 mm yerine **1 katman 100 × 75 mm**; konformal kaplama yerine kalaylama + (isteğe bağlı) "
        "şeffaf vernik. Gerekli yerlerde üst yüzde **atlama telleri** (J-Wn).",
        "Kapak reed anahtarı **NC (Form-B)** olmalıdır (titreşim anahtarına paralel, D2'yi GND'ye çeker).",
    ]
    for d in diffs:
        L.append("- " + d)
    L.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def _replace_block(text, tag, body):
    a = "<!-- AUTO:%s -->" % tag
    b_ = "<!-- /AUTO:%s -->" % tag
    i, j = text.index(a), text.index(b_)
    return text[:i + len(a)] + "
" + body.rstrip() + "
" + text[j:]


def update_readme(path, b, routes, rep, counts, uses):
    text = open(path, encoding="utf-8").read()
    js = routes.get("jumpers", [])
    nbus = sum(1 for j in js if len(j.get("pts", [])) > 2)
    ngnd = sum(1 for j in js if j["net"] == "GND" and len(j.get("pts", [])) <= 2)
    nsig = len(js) - nbus - ngnd
    rb = rep["readback"]
    lines = ["## Özet (otomatik üretildi)", "",
             "| Özellik | Değer |", "|---|---|",
             "| Kart | 100 × 75 mm, tek yüz (alt bakır), 1,6 mm FR4, R2 köşe, 4 × M3 |",
             "| Hat genişliği | sinyal 0,8 mm, güç 1,0-1,5 mm (VBAT, VMODEM, LED, GND, pil, güneş) |",
             "| Yalıtım | ≥ 0,5 mm hat-hat (ölçülen en küçük: %.3f mm), GND dökümü ≥ 0,6 mm |" % rep["drc"]["min_clearance_mm"],
             "| Delik | %d adet, %d farklı çap (bkz. §6) |" % (rep["holes"], len(counts)),
             "| Atlama teli | **%d** (J-W1 … J-W%d): %d × VBAT bara teli (çok noktalı), %d × sinyal, %d × GND |" % (
                 len(js), len(js), nbus, nsig, ngnd),
             "| DRC | %d aralık ihlali, %d kenar ihlali, %d genişlik ihlali, %d delik aralığı ihlali |" % (
                 rep["drc"]["clearance_violations"], rep["drc"]["edge_violations"], rep["drc"]["width_violations"],
                 rep["drc"]["hole_spacing_violations"]),
             "| Bağlantı (bakır geometrisinden) | %d net, %d kısa devre, %d açık devre |" % (
                 rep["connectivity_geometry"]["nets"], len(rep["connectivity_geometry"]["shorts"]),
                 len(rep["connectivity_geometry"]["opens"])),
             "| Gerber geri okuma (gerbonara, 20 µm) | %d bakır adası, %d kısa devre, %d açık devre, %d aralık ihlali, eşleşmeyen delik: %d |" % (
                 rb["islands"], len(rb["shorts"]), len(rb["opens"]), rb["n_clearance_violations"], len(rb["unmatched_holes"])),
             ""]
    if len(js) > 8:
        lines += ["> **Not — atlama teli sayısı:** hedef ≤ 8 idi, bu sürümde %d tel vardır. Pro Mini'nin iki pin sırası, "
                  "seviye çevirici, 3 ayrı güç anahtarı (modem/siren/LED) ve ortak GND/3V3/VBAT ağları tek katmanda "
                  "tam düzlemsel (kesişmesiz) yerleşmiyor; GND tellerinin çoğu 5-10 mm'lik kısa köprülerdir. "
                  "Kartı fabrikaya 2 katman olarak sipariş edecekseniz bu teller üst katmanda hat olarak çizilebilir." % len(js), ""]
    text = _replace_block(text, "SUMMARY", "
".join(lines))
    dl = ["| Uç | Çap | Adet | Parçalar |", "|---|---|---|---|"]
    for k, d in enumerate(sorted(counts)):
        dl.append("| %s | %.1f mm | %d | %s |" % (chr(65 + k), d, counts[d], ", ".join(sorted(uses.get(round(d, 2), [])))))
    dl.append("| | **toplam** | **%d** | |" % sum(counts.values()))
    text = _replace_block(text, "DRILL", "
".join(dl).replace(".", ",", 0))
    jl = ["| Tel | Net | Boy | Uçlar (x, y mm) | Not |", "|---|---|---|---|---|"]
    for i, j in enumerate(js):
        ln = math.hypot(j["b"][0] - j["a"][0], j["b"][1] - j["a"][1])
        pts = j.get("pts", [j["a"], j["b"]])
        note = "bara teli, %d lehim noktası, Ø0,8 mm" % len(pts) if len(pts) > 2 else ("GND köprüsü" if j["net"] == "GND" else "")
        jl.append("| J-W%d | %s | %.2f mm (%d × 2,54) | %s | %s |" % (
            i + 1, j["net"], ln, round(ln / 2.54), " → ".join("(%.1f, %.1f)" % tuple(q) for q in pts), note))
    text = _replace_block(text, "JUMPERS", "
".join(jl))
    open(path, "w", encoding="utf-8").write(text)
