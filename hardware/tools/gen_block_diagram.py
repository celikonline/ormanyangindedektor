# -*- coding: utf-8 -*-
"""System block diagram (brochure/web) for Orman Nöbetçisi ON-1, brand colours SPEC §8."""
import os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "schematic", "block_diagram.svg")

GREEN, ORANGE, SAND, ANTH = "#1F4D3A", "#E4572E", "#F4F1EA", "#1B1F1D"
GREEN_T, ORANGE_T, ANTH_T = "#E3ECE6", "#FBE4DC", "#E6E7E6"
F = "Arial, Helvetica, sans-serif"
W, H = 1600, 1000
o = []


def e(s):
    return html.escape(s, quote=False)


def text(x, y, s, size=15, weight="normal", color=ANTH, anchor="start", italic=False):
    st = ' font-style="italic"' if italic else ""
    o.append(f'<text x="{x}" y="{y}" font-family="{F}" font-size="{size}" font-weight="{weight}" fill="{color}" '
             f'text-anchor="{anchor}"{st}>{e(s)}</text>')


CAT = {"power": (ORANGE, ORANGE_T), "ctrl": (GREEN, GREEN_T), "sense": (GREEN, "#FFFFFF"),
       "comm": (ANTH, ANTH_T), "alarm": (ORANGE, "#FFFFFF"), "info": (GREEN, SAND)}


def box(x, y, w, h, title, lines=(), cat="ctrl", tsize=17, lsize=13.5, icon=None):
    c, fill = CAT[cat]
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{c}" stroke-width="2.4"/>')
    o.append(f'<rect x="{x}" y="{y}" width="8" height="{h}" rx="4" fill="{c}"/>')
    tx = x + 20
    text(tx, y + 25, title, tsize, "bold", c if cat != "comm" else ANTH)
    for i, ln in enumerate(lines):
        text(tx, y + 25 + 21 + i * 18.5, ln, lsize, color="#333")
    return (x, y, w, h)


def arrow(pts, kind="power", label=None, lpos=None, lanchor="start", both=False):
    if kind == "power":
        col, wdt, dash, mk = ORANGE, 7, "", "url(#ap)"
    elif kind == "sig":
        col, wdt, dash, mk = GREEN, 2.6, "", "url(#as)"
    else:
        col, wdt, dash, mk = ANTH, 2.6, ' stroke-dasharray="9,6"', "url(#ar)"
    d = "M" + " L".join(f"{a},{b}" for a, b in pts)
    ms = f' marker-start="{mk.replace(")", "s)")}"' if both else ""
    o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-linejoin="round"{dash} '
             f'marker-end="{mk}"{ms}/>')
    if label:
        lx, ly = lpos
        text(lx, ly, label, 12.5, "bold" if kind == "power" else "normal", col if kind != "rf" else ANTH, lanchor)


o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{F}">')
o.append("""<defs>
<marker id="ap" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="3.2" markerHeight="3.2" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#E4572E"/></marker>
<marker id="as" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1F4D3A"/></marker>
<marker id="ass" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M10,0 L0,5 L10,10 Z" fill="#1F4D3A"/></marker>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1B1F1D"/></marker>
</defs>""")
o.append(f'<rect width="{W}" height="{H}" fill="{SAND}"/>')
# header
o.append(f'<rect width="{W}" height="88" fill="{GREEN}"/>')
o.append(f'<circle cx="62" cy="44" r="27" fill="none" stroke="{SAND}" stroke-width="4"/>')
o.append(f'<path d="M62,25 L80,58 L44,58 Z" fill="{ORANGE}"/><circle cx="62" cy="46" r="5" fill="{SAND}"/>')
text(106, 44, "Orman Nöbetçisi ON-1 — Sistem Blok Diyagramı", 30, "bold", "#FFFFFF")
text(108, 72, "Ormanın gece gündüz uyanık gözü.  •  Güneş enerjili erken yangın algılama düğümü", 16, "normal", SAND, italic=True)
text(1560, 44, "ON1-MB Rev A", 18, "bold", "#FFFFFF", "end")
text(1560, 68, "2026-11-10", 15, "normal", SAND, "end")

# ---------------- column headings
for x, t, c in ((40, "ENERJİ", ORANGE), (380, "GÜÇ DAĞITIMI", ORANGE), (640, "ALGILAMA ve KONTROL", GREEN),
                (1140, "HABERLEŞME ve YEREL ALARM", ANTH)):
    text(x, 118, t, 14, "bold", c)

# ---------------- energy column
box(40, 130, 250, 82, "Güneş paneli", ["6 V 3 W monokristal ETFE", "165×135 mm, 30° braket (güneşlik)"], "power")
box(40, 240, 250, 64, "Giriş koruması", ["Ters polarite + TVS"], "power")
box(40, 332, 250, 100, "MPPT şarj", ["CN3791 • 5,9 V MPPT • 500 mA", "NTC ile 0…45 °C şarj penceresi"], "power")
box(40, 460, 250, 118, "Batarya + koruma", ["2 × 18650 (1S2P) 7000 mAh", "25,9 Wh • DW01A + FS8205A", "PTC 3 A sigorta"], "power")
arrow([(165, 212), (165, 238)], "power")
arrow([(165, 304), (165, 330)], "power")
arrow([(165, 432), (165, 458)], "power")
# energy budget card
box(40, 610, 250, 196, "Enerji bütçesi", ["Ortalama tüketim ≈ 2,3 mA", "≈ 56 mAh/gün (0,21 Wh)", "Güneşsiz: ≥ 60 gün hedef", "(hesap ≈ 100 gün)", "Güneş marjı ≈ 10× (gölgede)",
                                          "Alarm modu ≈ 15 saat"], "info")

# ---------------- VBAT trunk + converters
o.append(f'<path d="M330,300 L330,892 L1400,892 L1400,625 M290,519 L330,519" fill="none" stroke="{ORANGE}" stroke-width="7" stroke-linejoin="round"/>')
text(338, 914, "VBAT 3,0–4,2 V (PTC sonrası)", 13, "bold", ORANGE)
arrow([(330, 300), (378, 300)], "power")
box(380, 262, 210, 76, "3,3 V LDO", ["MCP1700 • Iq 1,6 µA"], "power")
box(380, 130, 210, 84, "Sensör rayı", ["AO3401A anahtar (D11)", "I2C kilitlenme kurtarma"], "power")
arrow([(485, 262), (485, 216)], "power", "3V3", (494, 246))
arrow([(590, 318), (620, 318), (620, 470), (638, 470)], "power")
text(612, 420, "3V3", 12.5, "bold", ORANGE, "end")
arrow([(590, 170), (638, 170)], "power")
arrow([(606, 170), (606, 278), (638, 278)], "power")
text(596, 160, "V_SNS", 12, "bold", ORANGE)

# ---------------- sensors + MCU
box(640, 132, 300, 92, "Termal kamera AMG8833", ["8×8 IR dizi, 60° FOV, 0–80 °C", "HDPE pencere, yataydan 35° aşağı"], "sense")
box(640, 234, 300, 92, "Gaz / ortam BME680", ["VOC gaz direnci, sıcaklık, nem, basınç", "ePTFE membranlı havalandırma"], "sense")
o.append(f'<path d="M940,178 L972,178 L972,280 L940,280" fill="none" stroke="{GREEN}" stroke-width="2.6"/>')
arrow([(972, 229), (995, 229), (995, 395), (944, 395)], "sig", both=True)
text(1003, 300, "I2C", 13, "bold", GREEN)
text(1003, 316, "0x69 / 0x77", 12, color=GREEN)
box(640, 360, 300, 228, "ATmega328P MCU", ["8 MHz, 3,3 V, Optiboot", "Çoklu sensör füzyonu → skor", "NORMAL → ŞÜPHE → ALARM", "Angström yangın risk indeksi", "PIN korumalı SMS komutları",
                                            "Watchdog + uyku (≈ 6 µA)", "Pil / panel / NTC ölçümü (ADC)"], "ctrl", tsize=19)
box(380, 620, 210, 112, "Kurcalama ve test", ["Titreşim + kapak reed", "Mıknatıslı test reed", "Durum LED’i (ışık borusu)"], "ctrl")
arrow([(590, 660), (620, 660), (620, 560), (638, 560)], "sig")

# ---------------- comm
box(985, 430, 112, 62, "Seviye çev.", ["4× BSS138"], "comm", tsize=14.5, lsize=12.5)
arrow([(944, 460), (983, 460)], "sig", both=True)
arrow([(1099, 460), (1138, 460)], "sig", both=True)
text(948, 515, "UART 3,3 ↔ 1,8 V", 12, color=GREEN)
box(1140, 400, 230, 130, "LTE modem A7670E", ["LTE Cat-1 + GSM 900/1800", "SMS + sesli arama", "Nano-SIM • DTR uyku ≈ 2 mA"], "comm")
box(1420, 400, 140, 130, "Harici anten", ["3 dBi IP67", "SMA bulkhead", "(teneke = Faraday", "kafesi)"], "comm", tsize=15, lsize=12)
arrow([(1370, 465), (1418, 465)], "rf")
o.append(f'<path d="M1180,300 C1150,300 1145,250 1185,245 C1185,195 1260,185 1285,215 C1305,170 1400,170 1415,215 '
         f'C1460,200 1520,225 1505,262 C1545,275 1530,320 1490,318 L1190,318 C1170,318 1165,302 1180,300 Z" '
         f'fill="#FFFFFF" stroke="{ANTH}" stroke-width="2.2"/>')
text(1340, 238, "Uyarı alıcıları", 17, "bold", ANTH, "middle")
text(1340, 260, "SMS → 5 numara (Google Maps konum bağlantılı)", 12.5, color="#333", anchor="middle")
text(1340, 278, "1. numaraya sesli arama • günlük durum SMS’i", 12.5, color="#333", anchor="middle")
text(1340, 296, "SMS komutları: DURUM, TEST, EKLE, SESSIZ …", 12.5, color="#333", anchor="middle")
arrow([(1490, 398), (1490, 338)], "rf")
arrow([(1260, 338), (1260, 398)], "rf")
text(1500, 372, "LTE / GSM", 12.5, "bold", ANTH)
text(1252, 372, "SMS komut", 12.5, "bold", ANTH, "end")

# ---------------- modem switch + alarm chain (bottom row)
box(1140, 590, 230, 72, "Modem güç anahtarı", ["AO3401A (D10) • güç döngüsü"], "power", tsize=15.5)
arrow([(1400, 625), (1372, 625)], "power")
arrow([(1255, 590), (1255, 532)], "power", "VMODEM", (1263, 570))
box(640, 760, 180, 96, "LED strob sürücü", ["AO3400A (D6)", "6 × 4,7 Ω"], "power", tsize=15)
box(845, 760, 170, 96, "LED strob", ["6 × 1 W kırmızı", "625 nm, çift flaş"], "alarm", tsize=15.5)
box(1040, 760, 180, 96, "12 V boost", ["MT3608 (D9)", "+ siren ayırma"], "power", tsize=15)
box(1245, 760, 135, 96, "Siren", ["12 V piezo", "105 dB @30 cm"], "alarm", tsize=15.5)
arrow([(730, 892), (730, 858)], "power")
arrow([(1130, 892), (1130, 858)], "power")
arrow([(820, 808), (843, 808)], "power")
arrow([(1220, 808), (1243, 808)], "power")
# MCU control signals
arrow([(700, 588), (700, 758)], "sig")
text(708, 640, "D6", 12.5, "bold", GREEN)
arrow([(900, 588), (900, 720), (1100, 720), (1100, 758)], "sig")
text(1010, 712, "D9 EN", 12.5, "bold", GREEN)
arrow([(944, 540), (1030, 540), (1030, 610), (1138, 610)], "sig")
text(1038, 598, "D10", 12.5, "bold", GREEN)
box(1420, 590, 140, 266, "Mekanik", ["Teneke Ø153×178", "RAL 9010 boya", "IP54, EPDM conta", "−20…+60 °C", "≈ 1,3 kg", "Ağaca 3–5 m", "kelepçe + halat"], "info", tsize=15, lsize=12.5)

# ---------------- legend
lx, ly = 40, 840
o.append(f'<rect x="{lx}" y="{ly}" width="280" height="132" rx="10" fill="#FFFFFF" stroke="#BBB" stroke-width="1.5"/>')
text(lx + 14, ly + 24, "Gösterim", 15, "bold", ANTH)
o.append(f'<path d="M{lx+16},{ly+48} L{lx+76},{ly+48}" stroke="{ORANGE}" stroke-width="7" marker-end="url(#ap)"/>')
text(lx + 92, ly + 53, "Güç akışı", 13.5)
o.append(f'<path d="M{lx+16},{ly+78} L{lx+76},{ly+78}" stroke="{GREEN}" stroke-width="2.6" marker-end="url(#as)"/>')
text(lx + 92, ly + 83, "Sinyal / kontrol", 13.5)
o.append(f'<path d="M{lx+16},{ly+108} L{lx+76},{ly+108}" stroke="{ANTH}" stroke-width="2.6" stroke-dasharray="9,6" marker-end="url(#ar)"/>')
text(lx + 92, ly + 113, "Kablosuz (LTE / GSM)", 13.5)
text(1560, 985, "Kaynak: SPEC.md Rev A • hardware/tools/gen_block_diagram.py", 12, color="#777", anchor="end")
o.append("</svg>")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(o))
print("wrote", OUT)
