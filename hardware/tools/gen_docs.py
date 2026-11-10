# -*- coding: utf-8 -*-
"""
Generates hardware/BOM.csv and hardware/pinout_netlist.md from the netlist that
gen_schematic.py extracted from the drawing (tools/build/netlist.json).
Run after gen_schematic.py.
"""
import os, json, re, sys
from collections import defaultdict, OrderedDict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bomdata import E, OFFBOARD, CABLES, MECH, PROD
from schlib import natkey

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
data = json.load(open(os.path.join(HERE, "build", "netlist.json"), encoding="utf-8"))
NETS, PARTS = data["nets"], data["parts"]


def money(v, nd=2):
    s = f"{v:.{nd}f}"
    return s.replace(".", ",")


def uprice(v):
    s = f"{v:.3f}"
    if s.endswith("0"):
        s = s[:-1]
    return s.replace(".", ",")


def compress(refs):
    """R41,R42,R43 -> R41–R43"""
    refs = sorted(refs, key=natkey)
    out = []
    i = 0
    while i < len(refs):
        m = re.match(r"([A-Z]+)(\d+)$", refs[i])
        j = i
        if m:
            p, n = m.group(1), int(m.group(2))
            while j + 1 < len(refs):
                m2 = re.match(r"([A-Z]+)(\d+)$", refs[j + 1])
                if m2 and m2.group(1) == p and int(m2.group(2)) == n + (j + 1 - i):
                    j += 1
                else:
                    break
        out.append(refs[i] if j - i < 2 else f"{refs[i]}–{refs[j]}")
        if 0 < j - i < 2:
            out += refs[i + 1:j + 1]
        i = j + 1
    return ", ".join(out)


ORDER = ["U", "Q", "D", "TVS", "F", "L", "Y", "R", "C", "LED", "SW", "J", "TP", "LD"]


def refclass(r):
    m = re.match(r"([A-Z]+)", r)
    p = m.group(1)
    return ORDER.index(p) if p in ORDER else 99


def board_of(ref, m):
    if m.get("offboard"):
        return "OFF"
    n = re.match(r"[A-Z]+(\d+)", ref)
    if ref in ("U7", "U8") or (n and int(n.group(1)) >= 100):
        return "SNS"
    return "MB"


# ------------------------------------------------------------------ BOM
def build_bom():
    groups = OrderedDict()
    for ref, m in PARTS.items():
        if m.get("kind") == "TP":
            continue
        key = m.get("bom")
        if key == "OFF":
            continue
        b = board_of(ref, m)
        g = groups.setdefault((b, key, bool(m.get("dnp"))), [])
        g.append(ref)
    rows = []
    sections = {"MB": "ELEKTRONİK — ON1-MB ana kart", "SNS": "ELEKTRONİK — SNS-1 sensör kartı",
                "OFF": "ELEKTRONİK — kart dışı parçalar ve kablolar"}
    tot = defaultdict(float)
    for b in ("MB", "SNS", "OFF"):
        rows.append([f"## {sections[b]}"] + [""] * 8)
        items = [(k, v) for k, v in groups.items() if k[0] == b]
        items.sort(key=lambda kv: (refclass(sorted(kv[1], key=natkey)[0]), natkey(sorted(kv[1], key=natkey)[0])))
        for (bb, key, dnp), refs in items:
            part, val, pkg, mpn, desc, price = E[key]
            qty = 0 if dnp else len(refs)
            d = desc
            if dnp:
                d = (desc + " — " if desc else "") + f"DNP: {len(refs)} konum, üretimde takılmaz"
            total = qty * price
            tot["Elektronik"] += total
            rows.append([compress(refs), str(qty), part, val, pkg, mpn, d, uprice(price), uprice(total)])
        if b == "MB":
            tps = sorted([r for r, m in PARTS.items() if m.get("kind") == "TP"], key=natkey)
            rows.append([compress(tps), "0", "Test noktası", "Ped Ø1,5 mm", "SMD ped", "—",
                         "A7670E USB/BOOT/LOG (SIMCom önerisi), maliyetsiz", "0,00", "0,00"])
        if b == "OFF":
            for refs, (part, val, pkg, mpn, desc, price) in OFFBOARD.items():
                n = len(refs.split(","))
                tot["Elektronik"] += n * price
                rows.append([refs.replace(",", ", "), str(n), part, val, pkg, mpn, desc, uprice(price), money(n * price)])
            for ref, n, part, val, pkg, mpn, desc, price in CABLES:
                tot["Elektronik"] += n * price
                rows.append([ref, str(n), part, val, pkg, mpn, desc, uprice(price), money(n * price)])
    rows.append(["## MEKANİK — gövde, montaj ve aksesuarlar"] + [""] * 8)
    for ref, n, part, val, pkg, mpn, desc, price in MECH:
        tot["Mekanik"] += n * price
        rows.append([ref, str(n), part, val, pkg, mpn, desc, uprice(price), money(n * price)])
    rows.append(["## ÜRETİM — PCB, dizgi, kaplama, test, montaj"] + [""] * 8)
    for ref, n, part, val, pkg, mpn, desc, price in PROD:
        tot["Üretim"] += n * price
        rows.append([ref, str(n), part, val, pkg, mpn, desc, uprice(price), money(n * price)])
    rows.append([""] * 9)
    rows.append(["", "", "ARA TOPLAM — Elektronik", "", "", "", "", "", money(tot["Elektronik"])])
    rows.append(["", "", "ARA TOPLAM — Mekanik", "", "", "", "", "", money(tot["Mekanik"])])
    rows.append(["", "", "ARA TOPLAM — Üretim", "", "", "", "", "", money(tot["Üretim"])])
    g = tot["Elektronik"] + tot["Mekanik"] + tot["Üretim"]
    rows.append(["", "", "GENEL TOPLAM (cihaz başı, ~100 adet)", "", "", "", "SIM kart/abonelik, KDV, nakliye hariç", "",
                 money(g)])
    head = ["Ref", "Adet", "Parça", "Değer/Model", "Kılıf", "Üretici/Örnek P/N", "Açıklama",
            "Birim Fiyat (USD, ~100 adet)", "Toplam (USD)"]

    def q(c):
        c = str(c)
        if any(ch in c for ch in ';"\n'):
            c = '"' + c.replace('"', '""') + '"'
        return c
    with open(os.path.join(HW, "BOM.csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write("\r\n".join(";".join(q(c) for c in r) for r in [head] + rows) + "\r\n")
    return tot, g


# ------------------------------------------------------------------ netlist md
POWER = ["GND", "VBAT", "BAT+", "SOLAR_IN", "3V3", "V_SNS", "VMODEM", "VDD_EXT", "V12"]


def ep(t):
    ref, pin, name = t
    pin_s = pin[:-1] + " (kablo ucu)" if pin.endswith("k") and not pin[:-1].isalpha() else pin
    nm = name.replace(" (kablo)", "")
    if nm and nm != pin and not pin.endswith("k"):
        return f"{ref}:{pin} ({nm})"
    return f"{ref}:{pin_s}"


def build_md(tot, g):
    L = []
    A = L.append
    A("# ON1-MB Rev A — Pin ve Bağlantı (Netlist) Tablosu")
    A("")
    A("**Orman Nöbetçisi ON-1** — ana kart ON1-MB Rev A + sensör kartı SNS-1 + kart dışı demetler.  ")
    A("Tarih: 2026-11-10 • Kaynak: `SPEC.md` Rev A • Şema: `schematic/ON1-MB_RevA_schematic_sheet1/2.svg`")
    A("")
    A("> Bu tablo, şema çiziminden **otomatik çıkarılmıştır** (`hardware/tools/gen_schematic.py` → `gen_docs.py`). "
      "Şemadaki her tel, pin, güç sembolü ve net etiketi birleştirilerek bağlantılar hesaplanır; "
      f"ERC kontrolü (tek uçlu net, açık uçlu tel, çakışan isim): **{len(data['problems'])} sorun**.")
    A("")
    A("Gösterim: `U1:23 (PC0/ADC0 [A0])` = U1’in 23 numaralı pini (pin adı). `(kablo ucu)` = konektörün kablo tarafı.")
    A("")
    A("## 1. SPEC Rev A’ya göre düzeltmeler (şemaya işlendi)")
    A("")
    A("| # | Düzeltme |")
    A("|---|---|")
    from gen_schematic import DELTAS
    for k, t in DELTAS:
        A(f"| {k} | {t} |")
    A("")
    # power nets
    A("## 2. Güç netleri")
    A("")
    A("| Net | Uç sayısı | Uçlar |")
    A("|---|---|---|")
    for n in POWER:
        pins = NETS.get(n, [])
        if n == "GND":
            A(f"| **{n}** | {len(pins)} | " + ", ".join(ep(p) for p in pins) + " |")
        else:
            A(f"| **{n}** | {len(pins)} | " + ", ".join(ep(p) for p in pins) + " |")
    A("")
    A("## 3. Sinyal netleri (isimli)")
    A("")
    A("| Net | Uçlar |")
    A("|---|---|")
    for n in sorted(NETS, key=natkey):
        if n in POWER or n.startswith("N_"):
            continue
        A(f"| **{n}** | " + ", ".join(ep(p) for p in NETS[n]) + " |")
    A("")
    A("## 4. Yerel (isimsiz) netler — kart üzeri")
    A("")
    A("İsimsiz netler ilk uca göre adlandırılır (`N_<ref>_<pin>`).")
    A("")
    A("| Net | Uçlar |")
    A("|---|---|")
    cable = []
    for n in sorted(NETS, key=natkey):
        if not n.startswith("N_"):
            continue
        if any(p[1].endswith("k") or p[0] in ("PV1", "BT1", "BT2", "NTC1", "SR1", "ANT1", "SW2", "SW3") or p[0].startswith("LD")
               or p[1] == "SIGR" for p in NETS[n]):
            cable.append(n)
            continue
        A(f"| {n} | " + ", ".join(ep(p) for p in NETS[n]) + " |")
    A("")
    A("## 5. Kablo / kart dışı bağlantılar")
    A("")
    A("| Net | Uçlar |")
    A("|---|---|")
    for n in cable:
        A(f"| {n} | " + ", ".join(ep(p) for p in NETS[n]) + " |")
    A("")
    # connectors
    A("## 6. Konektör pin tabloları")
    A("")

    def netof(ref, pin):
        for n, pins in NETS.items():
            for p in pins:
                if p[0] == ref and p[1] == str(pin):
                    return n
        return "— (NC)"

    conns = [
        ("J1 — Güneş paneli girişi (JST-XH 2p, 2,50 mm)", "J1", ["1", "2"], {"1": "PV+ (panel +, kırmızı)", "2": "PV− (panel −, siyah)"},
         "Panel kablosu PG7 rakordan girer. D1 SS34 seri ters polarite, TVS1 SMBJ7.0A paralel."),
        ("J2 — Batarya (JST-VH 2p, 3,96 mm) — Δ2", "J2", ["1", "2"], {"1": "B+ (2×18650 paralel +)", "2": "B− (hücre −, FS8205A S1)"},
         "Hücre tarafı koruma öncesidir; sistem GND’si P− (FS8205A S2)."),
        ("J3 — Batarya NTC (JST-PH 2p) — Δ1", "J3", ["1", "2"], {"1": "NTC (10k B3950)", "2": "GND"},
         "NTC hücreler arasına termal macun/kaptonla yapıştırılır."),
        ("J4 — SNS-1 sensör kablosu, ana kart (JST-SH 6p, 1,00 mm)", "J4", ["1", "2", "3", "4", "5", "6"],
         {"1": "V_SNS (3,3 V anahtarlı)", "2": "GND", "3": "I2C_SDA", "4": "GND", "5": "I2C_SCL", "6": "AMG_INT (ana kartta NC)"},
         "Kablo 1:1, ≈25 cm, SDA/SCL arasında GND tel (çapraz konuşma azaltma)."),
        ("J101 — SNS-1 kart tarafı (JST-SH 6p)", "J101", ["1", "2", "3", "4", "5", "6"],
         {"1": "V_SNS", "2": "GND", "3": "I2C_SDA", "4": "GND", "5": "I2C_SCL", "6": "AMG_INT (U7 pin 4)"}, ""),
        ("J5 — Siren (JST-XH 2p)", "J5", ["1", "2"], {"1": "+12V (V12, kırmızı)", "2": "SİREN− (Q11 drenaj, siyah)"},
         "12 V 105 dB piezo siren ≈30 mA. Siren Q11 ile ayrılır (Δ4)."),
        ("J6 — FTDI programlama (1×6, 2,54 mm, Pro Mini sırası)", "J6", ["1", "2", "3", "4", "5", "6"],
         {"1": "GND", "2": "CTS (GND)", "3": "3V3", "4": "RXI ← FTDI TX", "5": "TXO → FTDI RX", "6": "DTR → C25 → RESET"},
         "Yalnızca 3,3 V FTDI kullanın; programlamada batarya takılı olmalı."),
        ("J7 — AVR ISP (2×3, 2,54 mm)", "J7", ["1", "2", "3", "4", "5", "6"],
         {"1": "MISO (D12)", "2": "VCC 3V3", "3": "SCK (D13)", "4": "MOSI (D11)", "5": "RESET", "6": "GND"},
         "ISP sırasında D11 sensör rayını, D13 şarj kesmeyi kısa süre değiştirir — zararsız."),
        ("J8 — LED strob halkası (JST-XH 8p)", "J8", [str(i) for i in range(1, 9)],
         {**{str(i): f"LED{i} anot (R{40+i} 4,7 Ω → VBAT)" for i in range(1, 7)}, "7": "LED_K ortak katot", "8": "LED_K ortak katot"},
         "Katot dönüşü 2 pine bölünmüştür (≈2,4 A tepe)."),
        ("J9 — Kapak reed anahtarı (JST-PH 2p) — Δ6", "J9", ["1", "2"], {"1": "TAMPER_N", "2": "GND"},
         "Reed NC (Form-B) ya da Form-C’nin NC kontağı; kapak kapalıyken mıknatıs kontağı açık tutar."),
        ("J10 — Test reed anahtarı (JST-PH 2p)", "J10", ["1", "2"], {"1": "TEST_REED_N", "2": "GND"},
         "Reed NO; alt PC kubbe kenarına yerleştirilir (teneke manyetik alanı zayıflatır)."),
        ("J11 — Nano-SIM (push-push)", "J11", ["C1", "C2", "C3", "C5", "C6", "C7"],
         {"C1": "VCC", "C2": "RST", "C3": "CLK", "C5": "GND", "C6": "VPP (NC)", "C7": "I/O"}, ""),
        ("J12 — U.FL anten", "J12", ["SIG", "GND"], {"SIG": "RF (π ağı üzerinden U2 pin 60)", "GND": "GND"},
         "U.FL → 15 cm pigtail → SMA dişi bulkhead (O-ring) → 3 dBi IP67 LTE anten."),
    ]
    for title, ref, pins, desc, note in conns:
        A(f"### {title}")
        A("")
        A("| Pin | Sinyal | Net |")
        A("|---|---|---|")
        for p in pins:
            A(f"| {p} | {desc.get(p, '')} | `{netof(ref, p)}` |")
        if note:
            A("")
            A(note)
        A("")
    A("### Sensör kablosu J4 ↔ J101 (JST-SH 6p, 1:1)")
    A("")
    A("| J4 pin | Tel rengi (öneri) | J101 pin | Sinyal |")
    A("|---|---|---|---|")
    for p, c, sgn in (("1", "kırmızı", "V_SNS"), ("2", "siyah", "GND"), ("3", "mavi", "I2C_SDA"), ("4", "siyah", "GND"),
                      ("5", "sarı", "I2C_SCL"), ("6", "beyaz", "AMG_INT")):
        A(f"| {p} | {c} | {p} | {sgn} |")
    A("")
    A("### LED halkası (Al-MCPCB Ø50 mm, 6 × 1 W kırmızı 625 nm)")
    A("")
    A("| Halka pedi | LED | Bağlantı | J8 pin |")
    A("|---|---|---|---|")
    for i in range(1, 7):
        A(f"| A{i} | LD{i} anot | R{40+i} 4,7 Ω 1 W → VBAT | {i} |")
    A("| K | LD1–LD6 katot (ortak) | Q3 AO3400A drenaj → GND | 7, 8 |")
    A("")
    A("Her LED ≈0,32 A @ 3,7 V (0,40 A @ 4,2 V); desen 60/90/60/790 ms (≈ %12 görev).")
    A("")
    A("### Siren")
    A("")
    A("| Siren teli | J5 pin | Net | Not |")
    A("|---|---|---|---|")
    A("| + (kırmızı) | 1 | V12 | MT3608 çıkışı 12,03 V (R49 200k / R50 10,5k) |")
    A("| − (siyah) | 2 | SIREN_N → Q11 | SIREN_EN (D9) HIGH → U5 EN + Q11 açık |")
    A("")
    # MCU
    A("## 7. ATmega328P pin haritası (Arduino Pro Mini numaralandırması)")
    A("")
    from gen_sheet2 import PINMAP
    A("| " + " | ".join(PINMAP[0]) + " |")
    A("|" + "---|" * len(PINMAP[0]))
    for r in PINMAP[1:]:
        A("| " + " | ".join(r) + " |")
    A("")
    A("Kullanılmayan: A6 (ADC6). TQFP GND: 3, 5, 21; VCC: 4, 6; AVCC: 18; AREF: 20 (100 nF → GND, iç 1,1 V referans).")
    A("")
    A("## 8. A7670E kullanılan pinler")
    A("")
    A("| Pin | Ad | Bağlantı |")
    A("|---|---|---|")
    for p, nm, c in (("55, 56, 57", "VBAT", "VMODEM (Q1), 2×470 µF + 100 nF + 33 pF + 10 pF + ESD5Z5.0"),
                     ("1", "PWRKEY", "Q4 kollektör (iç 50 kΩ pull-up VBAT’a)"), ("16", "RESET", "NC (iç pull-up)"),
                     ("9", "TXD", "MDM_TXD_1V8 → Q6 → D7"), ("10", "RXD", "MDM_RXD_1V8 ← Q7 ← D8"),
                     ("3", "DTR", "MDM_DTR_1V8 ← Q8 ← D5"), ("4", "RI", "MDM_RI_1V8 → Q9 → D3"),
                     ("7, 8, 5", "CTS, RTS, DCD", "NC"), ("15", "VDD_EXT (VDD_1V8)", "BSS138 kapıları + LV pull-up (50 mA maks.)"),
                     ("30–33", "USIM_VDD/DATA/CLK/RST", "J11 (22 Ω seri, ESDA6V1-5SC6, 100 nF + 33 pF)"),
                     ("34", "USIM_DET", "NC"), ("60", "RF_ANT", "R27 0 Ω π ağı → J12 U.FL"),
                     ("52", "NETLIGHT", "R28 → Q13 → LED3 (DNP, Δ5)"), ("66", "STATUS", "NC"),
                     ("24, 27, 28, 6, 23", "VBUS, DP, DM, USB_BOOT, LOG_TX", "TP1–TP5 (FW güncelleme)"),
                     ("2, 17, 18, …", "GND", "Tüm GND pinleri katı GND düzlemine")):
        A(f"| {p} | {nm} | {c} |")
    A("")
    A("## 9. DNP (üretimde takılmayan) parçalar")
    A("")
    dnp = sorted([r for r, m in PARTS.items() if m.get("dnp")], key=natkey)
    A(", ".join(dnp) + " — hata ayıklama / RF ayarı içindir.")
    A("")
    A("## 10. Maliyet özeti (BOM.csv)")
    A("")
    A(f"Elektronik: **{money(tot['Elektronik'])} USD** • Mekanik: **{money(tot['Mekanik'])} USD** • "
      f"Üretim: **{money(tot['Üretim'])} USD** • Genel toplam: **{money(g)} USD / cihaz** (~100 adet, KDV/nakliye/SIM hariç).")
    A("")
    with open(os.path.join(HW, "pinout_netlist.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    tot, g = build_bom()
    build_md(tot, g)
    print({k: round(v, 2) for k, v in tot.items()}, "TOTAL", round(g, 2))
