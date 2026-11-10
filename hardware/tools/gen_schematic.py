# -*- coding: utf-8 -*-
"""
ON1-MB Rev A schematic generator  (Orman Nöbetçisi ON-1)
Run:  python hardware/tools/gen_schematic.py
Emits: hardware/schematic/ON1-MB_RevA_schematic_sheet1.svg, ..._sheet2.svg,
       hardware/tools/build/netlist.json (used by gen_docs.py)
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schlib import Sheet, build_netlist, FONT, esc
from frame import frame_svg

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
OUT = os.path.join(HW, "schematic")
BUILD = os.path.join(HERE, "build")


def B(key, **kw):
    d = {"bom": key}
    d.update(kw)
    return d


# =====================================================================
#  SHEET 1 — GÜÇ: güneş/şarj, batarya/koruma, 3V3 LDO, LED strob + siren
# =====================================================================
def sheet1():
    s = Sheet("S1")
    # ---------------------------------------------------------------- block 1
    s.block(100, 100, 2060, 990, 1, "Güneş paneli girişi ve CN3791 MPPT şarj")
    RY = 330
    s.offboard(112, 210, 128, 300, "Panel")
    pv = s.part("CELL", "PV1", "", 165, 370, lbl="b", lbl_dy=8, show_ref=False,
                meta=B("OFF", offboard=True))
    s.text(176, 470, "PV1 6V 3W", size=16, anchor="middle")
    j1 = s.conn("J1", "JST-XH 2p", 260, 310, ["PV+", "PV−"], side="R", w=90, meta=B("J_XH2"))
    s.wire(pv["+"], (165, 330), j1["1k"], dashed=True)
    s.wire(pv["-"], (200, 410), (200, 370), j1["2k"], dashed=True)
    s.wire(j1["2"], (410, 370))
    s.gnd((410, 370))
    tv = s.part("TVS", "TVS1", "SMBJ7.0A", 480, 400, rot=180, meta=B("SMBJ7"))
    s.wire(j1["1"], (480, RY))
    s.wire((480, RY), tv["K"])
    s.gnd(tv["A"])
    s.wire((480, RY), (560, RY))
    s.wire((560, RY), (560, 270))
    s.flag((560, 270), "SOLAR_IN", "up")
    d1 = s.part("DS", "D1", "SS34", 650, RY, rot=270, meta=B("SS34"), value2="ters polarite")
    s.wire((560, RY), d1["A"])
    c1 = s.part("C", "C1", "10µF", 750, 370, value2="25V", meta=B("C10u25"))
    c2 = s.part("C", "C2", "100nF", 860, 370, value2="50V", meta=B("C100n50"))
    s.wire(d1["K"], (1020, RY))
    for c in (c1, c2):
        s.wire((c["1"][0], RY), c["1"])
        s.gnd(c["2"])
    q10 = s.part("PMOSD", "Q10", "AO3401A", 1060, RY + 24, rot=270, lbl="t", lbl_dy=-6, meta=B("AO3401"))
    s.netname((1140, RY), "SW_CHG", dx=-30, dy=-10)
    s.netname((940, RY), "VIN_CHG", dx=-36, dy=-10)
    s.netname((1480, RY), "CSP", dx=-14, dy=-10)
    s.wire(q10["D"], (1200, RY))
    d2 = s.part("DS", "D2", "SS34", 1200, 400, rot=180, meta=B("SS34"))
    s.wire((1200, RY), d2["K"])
    s.gnd(d2["A"])
    l1 = s.part("L", "L1", "22µH 2A", 1330, RY, rot=90, lbl="t", meta=B("L22u2A"))
    s.wire((1200, RY), l1["2"])
    s.wire(l1["1"], (1600, RY))
    r6 = s.part("R", "R6", "0,24Ω 1206", 1650, RY, rot=90, lbl="t", value2="R_CS, Ich=500 mA", meta=B("R0R24"))
    s.wire((1600, RY), r6["2"])
    s.wire(r6["1"], (2050, RY))
    s.flag((2050, RY), "BAT+", "right")
    c6 = s.part("C", "C6", "22µF", 1860, 370, value2="10V 1206", meta=B("C22u10"))
    s.wire((1860, RY), c6["1"])
    s.gnd(c6["2"])

    u3 = s.ic("U3", "CN3791 (SSOP-10)", 1240, 520, 260, 380, [
        ("L", 40, 10, "DRV"), ("L", 100, 9, "VCC"), ("L", 200, 1, "VG"), ("L", 280, 6, "MPPT"),
        ("L", 340, 5, "COM"),
        ("R", 40, 8, "CSP"), ("R", 100, 7, "BAT"), ("R", 200, 3, "CHRG"), ("R", 280, 4, "DONE", "nc"),
        ("B", 130, 2, "GND")], meta=B("CN3791"), value2="MPPT Li-ion şarj")
    s.wire(u3["DRV"], (1060, u3["DRV"][1]), q10["G"])
    s.wire(u3["VCC"], (980, u3["VCC"][1]), (980, RY))
    c4 = s.part("C", "C4", "100nF", 1130, 660, lbl="l", meta=B("C100n50"))
    s.wire(c4["2"], (1130, u3["VG"][1]), u3["VG"])
    s.gnd(u3["GND"])
    s.netname((1010, 800), "MPPT", dy=-10)
    # MPPT divider + charge inhibit
    s.wire(u3["MPPT"], (870, u3["MPPT"][1]))
    r4 = s.part("R", "R4", "390k 1%", 870, 715, value2="R_MP1", meta=B("R390k"))
    r5 = s.part("R", "R5", "100k 1%", 870, 870, value2="R_MP2", meta=B("R100k1"))
    s.wire(r4["2"], (870, 800))
    s.wire((870, 800), r5["1"])
    s.gnd(r5["2"])
    s.wire(r4["1"], (870, 655))
    s.flag((870, 655), "SOLAR_IN", "up")
    q12 = s.part("NMOS", "Q12", "BSS138", 676, 860, lbl="r", lbl_dx=4, meta=B("BSS138"))
    s.wire(q12["D"], (700, 800), (870, 800))
    s.gnd(q12["S"])
    r7 = s.part("R", "R7", "100k", 590, 920, lbl="l", meta=B("R100k"))
    s.wire(q12["G"], (520, 860))
    s.wire((590, 860), r7["1"])
    s.gnd(r7["2"])
    s.flag((520, 860), "CHG_INHIBIT", "left")
    s.revmark(470, 935, 1)
    # COM network
    r3 = s.part("R", "R3", "120Ω", 1140, 860, rot=90, lbl="t", meta=B("R120"))
    s.wire(r3["1"], u3["COM"])
    c5 = s.part("C", "C5", "220nF", 1050, 930, lbl="l", meta=B("C220n"))
    s.wire(r3["2"], (1050, 860), c5["1"])
    s.gnd(c5["2"])
    # CSP / BAT
    s.wire(u3["CSP"], (1600, u3["CSP"][1]), (1600, RY))
    s.wire(u3["BAT"], (1770, u3["BAT"][1]), (1770, RY))
    # CHRG
    s.wire(u3["CHRG"], (2010, u3["CHRG"][1]))
    s.flag((2010, u3["CHRG"][1]), "CHG_STAT_N", "right")
    led2 = s.part("LED", "LED2", "kırmızı 0603", 1960, 650, dnp=True, meta=B("LED_R"))
    r8 = s.part("R", "R8", "1k", 1960, 520, dnp=True, meta=B("R1k"))
    s.wire(led2["K"], (1960, u3["CHRG"][1]))
    s.wire(r8["2"], led2["A"])
    s.pwr(r8["1"], "3V3")
    s.text(130, 1020, "MPPT: V_MPPT = 1,205 V × (1 + R4/R5) = 5,90 V (panel tarafında, D1 öncesi ölçülür)  •  "
           "Ich = 120 mV / R6 = 500 mA  •  CHRG → A3", size=18, color="#333")
    s.text(130, 1050, "Q12: D13=HIGH → MPPT pini GND’ye çekilir → şarj durur (NTC ile 0…45 °C penceresi firmware’de, bkz. Δ1). "
           "Prototipte doğrulanmalı.", size=18, color="#333")

    # ---------------------------------------------------------------- block 2
    s.block(2190, 100, 1910, 990, 2, "Batarya ve koruma (DW01A + FS8205A, PTC, NTC)")
    s.flag((2300, RY), "BAT+", "left")
    s.offboard(2210, 440, 215, 380, "2×18650 (1S2P)")
    bt1 = s.part("CELL", "BT1", "", 2275, 620, show_ref=False, meta=B("OFF", offboard=True))
    bt2 = s.part("CELL", "BT2", "", 2370, 620, show_ref=False, meta=B("OFF", offboard=True))
    s.text(2318, 750, "BT1 ‖ BT2", size=17, anchor="middle")
    s.text(2318, 772, "18650 3500 mAh", size=15, anchor="middle")
    s.text(2318, 792, "= 7000 mAh", size=15, anchor="middle")
    j2 = s.conn("J2", "JST-VH 2p", 2480, 520, ["B+", "B−"], side="R", w=90, meta=B("J_VH2"))
    s.wire(bt1["+"], (2275, 545), (2370, 545), bt2["+"], dashed=True)
    s.wire((2370, 545), (2420, 545), (2420, 540), j2["1k"], dashed=True)
    s.wire(bt1["-"], (2275, 695), (2370, 695), bt2["-"], dashed=True)
    s.wire((2370, 695), (2435, 695), (2435, 580), j2["2k"], dashed=True)
    s.revmark(2620, 470, 2)
    s.wire(j2["1"], (2690, 540), (2690, RY))
    s.wire(j2["2"], (2650, 580), (2650, 800))
    r9 = s.part("R", "R9", "100Ω", 2810, 390, meta=B("R100"))
    s.wire((2810, RY), r9["1"])
    u6 = s.ic("U6", "DW01A (SOT-23-6)", 2910, 470, 250, 180, [
        ("L", 30, 5, "VCC"), ("L", 90, 6, "GND"),
        ("R", 30, 1, "OD"), ("R", 70, 3, "OC"), ("R", 110, 2, "CS"), ("R", 150, 4, "TD", "nc")],
        meta=B("DW01A"))
    s.wire(r9["2"], (2810, 500), u6["VCC"])
    c7 = s.part("C", "C7", "100nF", 2750, 540, lbl="l", meta=B("C100n50"))
    s.wire(c7["1"], (2750, 500), (2810, 500))
    s.wire(c7["2"], (2750, 800))
    s.wire(u6["GND"], (2850, 560), (2850, 800))
    u9 = s.ic("U9", "FS8205A (TSSOP-8)", 3270, 770, 230, 140, [
        ("L", 30, 2, "S1"), ("L", 70, 3, "S1"), ("R", 30, 7, "S2"), ("R", 70, 6, "S2"),
        ("T", 60, 5, "G2"), ("T", 170, 4, "G1"), ("B", 60, 1, "D"), ("B", 170, 8, "D")],
        meta=B("FS8205A"), title_pos="none")
    s.text(3270, 1000, "U9  FS8205A (TSSOP-8)", size=20, weight="bold")
    s.text(3270, 1023, "çift N-MOSFET, ortak drenaj (1, 8)", size=16, color="#555")
    s.wire((2650, 800), u9["2"])
    s.wire(u9["3"], (3220, u9["3"][1]), (3220, 800))
    s.wire(u6["OD"], (u9["4"][0], u6["OD"][1]), u9["4"])
    s.wire(u6["OC"], (u9["5"][0], u6["OC"][1]), u9["5"])
    r10 = s.part("R", "R10", "1k", 3230, 620, meta=B("R1k"))
    s.wire(u6["CS"], (3230, u6["CS"][1]), r10["1"])
    s.gnd(r10["2"])
    s.wire(u9["7"], (3560, u9["7"][1]), (3560, u9["6"][1]), u9["6"])
    s.gnd((3560, u9["6"][1]))
    s.wire(u9["1"], (u9["1"][0], 955), (u9["8"][0], 955), u9["8"])
    s.netname((2660, 800), "BAT−", dy=24)
    s.text(3580, 880, "P− = GND", size=16, color="#555")
    # rail BAT+ -> PTC -> VBAT
    s.wire((2300, RY), (3660, RY))
    f1 = s.part("PTC", "F1", "PTC 3A 1812", 3700, RY, rot=90, lbl="t", meta=B("PTC3A"))
    s.wire(f1["2"], (3660, RY))
    s.wire(f1["1"], (3960, RY))
    s.pwr((3960, RY), "VBAT")
    s.text(3790, RY + 32, "VBAT 3,0–4,2 V", size=16, color="#555")
    s.text(2730, 280, "DW01A: aşırı şarj 4,3 V • aşırı deşarj 2,4 V • aşırı akım 150 mV/R_SS", size=16, color="#555")
    # NTC
    s.offboard(3575, 560, 165, 230, "NTC (hücrede)")
    ntc = s.part("NTC", "NTC1", "", 3640, 680, show_ref=False, meta=B("OFF", offboard=True))
    s.text(3657, 772, "NTC1 10k B3950", size=15, anchor="middle")
    j3 = s.conn("J3", "JST-PH 2p", 3790, 620, ["NTC", "GND"], side="R", w=90, meta=B("J_PH2"))
    s.wire(ntc["1"], j3["1k"], dashed=True)
    s.wire(ntc["2"], (3720, 720), (3720, 680), j3["2k"], dashed=True)
    s.gnd(j3["2"])
    r11 = s.part("R", "R11", "220k 1%", 3960, 560, lbl="r", meta=B("R220k"))
    s.pwr(r11["1"], "3V3")
    s.wire(j3["1"], (3960, 640))
    s.wire(r11["2"], (3960, 640))
    c9 = s.part("C", "C9", "100nF", 3960, 720, lbl="r", meta=B("C100n50"))
    s.wire((3960, 640), c9["1"])
    s.gnd(c9["2"])
    s.wire((3960, 640), (3985, 640))
    s.flag((3985, 640), "BAT_NTC", "right")
    s.text(3790, 840, "BAT_NTC → U1 A7 (ADC7)", size=16, color="#555")
    s.revmark(3880, 500, 1)

    # ---------------------------------------------------------------- block 3
    s.block(100, 1120, 960, 540, 3, "3,3 V LDO")
    LY = 1320
    s.pwr((200, LY), "VBAT")
    c15 = s.part("C", "C15", "1µF", 290, LY + 40, meta=B("C1u"))
    c16 = s.part("C", "C16", "10µF", 390, LY + 40, meta=B("C10u10"))
    u4 = s.ic("U4", "MCP1700T-3302E/TT", 530, LY - 50, 180, 110, [
        ("L", 50, 3, "VIN"), ("R", 50, 2, "VOUT"), ("B", 90, 1, "GND")], meta=B("MCP1700"))
    s.wire((200, LY), u4["VIN"])
    c17 = s.part("C", "C17", "1µF", 810, LY + 40, meta=B("C1u"))
    c18 = s.part("C", "C18", "10µF", 910, LY + 40, meta=B("C10u10"))
    s.wire(u4["VOUT"], (1000, LY))
    s.pwr((1000, LY), "3V3")
    for c in (c15, c16, c17, c18):
        s.gnd(c["2"])
    s.gnd(u4["GND"])
    s.text(130, 1500, "Iq = 1,6 µA, 250 mA, dropout 178 mV.", size=18, color="#333")
    s.text(130, 1528, "Besler: U1 ATmega328P, BSS138 HV pull-up’ları,", size=18, color="#333")
    s.text(130, 1556, "NTC bölücü, Q2 üzerinden sensör rayı V_SNS.", size=18, color="#333")
    s.text(130, 1600, "Not: FTDI 3V3 yalnızca batarya takılıyken bağlanmalı", size=16, color="#8a4b00", italic=True)
    s.text(130, 1622, "(MCP1700 ters akım korumasız).", size=16, color="#8a4b00", italic=True)

    # ---------------------------------------------------------------- block 8
    s.block(1090, 1120, 3010, 830, 8, "Yerel alarm: 6×LED strob sürücü + MT3608 12 V siren besleme")
    s.text(1110, 1192, "8a) LED strob (D6 → Q3)", size=20, weight="bold", color="#1F4D3A")
    s.text(2730, 1192, "8b) Siren: MT3608 boost 12 V (D9 → EN, Q11)", size=20, weight="bold", color="#1F4D3A")
    BY = 1255
    xs = [1200 + 110 * i for i in range(6)]
    s.pwr((xs[0], BY), "VBAT")
    s.wire((xs[0], BY), (xs[-1], BY))
    j8 = s.hconn("J8", "JST-XH 8p", 1145, 1450, ["A1", "A2", "A3", "A4", "A5", "A6", "K", "K"], pitch=110,
                 meta=B("J_XH8"))
    for i, x in enumerate(xs):
        r = s.part("R", f"R{41+i}", "4,7Ω", x, 1335, lbl="r", meta=B("R4R7_1W"))
        s.wire((x, BY), r["1"])
        s.wire(r["2"], j8[str(i + 1)])
    s.text(1300, 1230, "R41–R46: 4,7 Ω 1 W 2512 (her LED ≈300 mA, toplam ≈1,8 A tepe)", size=17, color="#333")
    s.wire(j8["7"], (j8["7"][0], 1400), (j8["8"][0], 1400), j8["8"])
    s.wire((j8["8"][0], 1400), (2560, 1400))
    s.netname((2140, 1400), "LED_K", dy=-10)
    s.offboard(1125, 1560, 905, 330, "LED halkası — Al-MCPCB Ø50 mm, alt kapakta PC kubbe Ø70 mm (kart dışı)", tpos="bottom")
    for i, x in enumerate(xs):
        ld = s.part("LED", f"LD{i+1}", "", x, 1650, lbl="r", lbl_dx=6, meta=B("LED1W_R", offboard=True))
        s.wire(j8[f"{i+1}k"], ld["A"], dashed=True)
        s.wire(ld["K"], (x, 1730), dashed=True)
    s.wire((xs[0], 1730), (j8["8k"][0], 1730), dashed=True)
    s.wire((j8["7k"][0], 1730), j8["7k"], dashed=True)
    s.wire((j8["8k"][0], 1730), j8["8k"], dashed=True)
    s.text(1140, 1790, "LD1–LD6: 1 W kırmızı 625 nm, Vf ≈ 2,2 V, ortak katot (K) → Q3", size=17)
    s.text(1140, 1815, "Desen: 60 ms açık / 90 ms kapalı / 60 ms açık / 790 ms kapalı (≈ %12 görev)", size=17)
    q3 = s.part("NMOS", "Q3", "AO3400A", 2536, 1480, lbl="r", meta=B("AO3400"))
    s.wire((2560, 1400), q3["D"])
    s.gnd(q3["S"])
    r47 = s.part("R", "R47", "100Ω", 2420, 1480, rot=90, lbl="t", meta=B("R100"))
    s.wire(r47["1"], q3["G"])
    r48 = s.part("R", "R48", "100k", 2478, 1580, lbl="r", meta=B("R100k"))
    s.wire((2478, 1480), r48["1"])
    s.gnd(r48["2"])
    s.flag(r47["2"], "LED_STROBE", "left")
    s.text(2240, 1700, "Q3 kapı: 100 Ω seri + 100 kΩ pull-down", size=16, color="#555")
    s.text(2240, 1722, "D6 HIGH → LED’ler yanar", size=16, color="#555")

    # siren
    SY = 1300
    s.pwr((2800, SY), "VBAT")
    c35 = s.part("C", "C35", "22µF", 2880, SY + 40, lbl="l", meta=B("C22u10"))
    s.gnd(c35["2"])
    u5 = s.ic("U5", "MT3608 (SOT-23-6)", 3010, 1460, 220, 180, [
        ("L", 40, 5, "IN"), ("L", 110, 4, "EN"), ("R", 40, 1, "SW"), ("R", 110, 3, "FB"),
        ("R", 150, 6, "NC", "nc"), ("B", 110, 2, "GND")], meta=B("MT3608"))
    s.wire((2800, SY), (3040, SY))
    s.wire(u5["IN"], (2950, u5["IN"][1]), (2950, SY))
    l2 = s.part("L", "L2", "22µH 1,5A", 3080, SY, rot=90, lbl="t", meta=B("L22u15"))
    s.wire(l2["1"], (3300, SY))
    s.wire(u5["SW"], (3300, u5["SW"][1]), (3300, SY))
    d3 = s.part("DS", "D3", "SS34", 3380, SY, rot=270, lbl="t", meta=B("SS34"))
    s.wire((3300, SY), d3["A"])
    s.wire(d3["K"], (3740, SY))
    c36 = s.part("C", "C36", "22µF", 3490, SY + 40, value2="25V 1206", meta=B("C22u25"))
    s.gnd(c36["2"])
    s.wire((3490, SY), c36["1"])
    r49 = s.part("R", "R49", "200k 1%", 3610, 1400, meta=B("R200k"))
    r50 = s.part("R", "R50", "10,5k 1%", 3610, 1650, meta=B("R10k5"))
    s.wire((3610, SY), r49["1"])
    s.wire(r49["2"], (3610, u5["FB"][1]), r50["1"])
    s.wire(u5["FB"], (3610, u5["FB"][1]))
    s.gnd(r50["2"])
    s.revmark(3720, 1600, 3)
    s.pwr((3680, SY), "V12")
    s.wire(u5["EN"], (2840, u5["EN"][1]))
    r51 = s.part("R", "R51", "100k", 2900, 1650, lbl="r", meta=B("R100k"))
    s.wire((2900, u5["EN"][1]), r51["1"])
    s.gnd(r51["2"])
    s.flag((2840, u5["EN"][1]), "SIREN_EN", "left")
    s.gnd(u5["GND"])
    j5 = s.conn("J5", "JST-XH 2p", 3830, 1480, ["+12V", "SİREN−"], side="L", w=110, meta=B("J_XH2"))
    s.wire((3740, SY), (3740, j5["1"][1]), j5["1"])
    s.wire(j5["2"], (3770, j5["2"][1]), (3770, 1780))
    q11 = s.part("NMOS", "Q11", "AO3400A", 3746, 1820, lbl="r", meta=B("AO3400"))
    s.wire((3770, 1780), q11["D"])
    s.gnd(q11["S"])
    r52 = s.part("R", "R52", "100Ω", 3620, 1820, rot=90, lbl="t", meta=B("R100"))
    s.wire(r52["1"], q11["G"])
    s.flag(r52["2"], "SIREN_EN", "left")
    s.revmark(3880, 1890, 4)
    s.netname((3770, 1660), "SIREN_N", dx=8, dy=6)
    s.netname((3200, SY), "SW_BST", dy=-10)
    s.netname((3430, 1570), "FB", dy=-10)
    s.offboard(3985, 1400, 105, 250, "Siren")
    sr = s.part("SIREN", "SR1", "", 4010, 1560, show_ref=False, meta=B("OFF", offboard=True))
    s.wire(j5["1k"], (4010, j5["1k"][1]), sr["1"], dashed=True)
    s.wire(j5["2k"], (3990, j5["2k"][1]), (3990, 1620), (4010, 1620), sr["2"], dashed=True)
    s.text(3995, 1680, "SR1 12 V", size=15)
    s.text(3995, 1700, "105 dB", size=15)
    s.text(3995, 1720, "IP65", size=15)
    s.text(2730, 1885, "Vout = 0,6 V × (1 + R49/R50) = 0,6 × (1 + 200k/10,5k) = 12,03 V  •  siren ≈ 30 mA @ 12 V", size=17, color="#333")
    s.text(2730, 1910, "Q11: EN = LOW iken boost çıkışı ≈ VBAT kalır → siren Q11 ile ayrılır (Δ4)", size=17, color="#333")
    return s


# =====================================================================
#  notes / legend
# =====================================================================
DELTAS = [
    ("Δ1", "CN3791’de TEMP/NTC pini yok (SSOP-10: VG, GND, CHRG, DONE, COM, MPPT, BAT, CSP, VCC, DRV). "
           "NTC → J3 → R11 220k bölücü → A7 (ADC7); şarj kesme: D13 → Q12 BSS138 → MPPT pini GND."),
    ("Δ2", "J2 batarya konektörü JST-PH (2 A) yerine JST-VH 2p (10 A): LED strob 1,8–2,5 A + modem 2 A darbe."),
    ("Δ3", "MT3608 VREF = 0,6 V: 200k/18k → 7,27 V verir. 12 V için R50 = 10,5 kΩ %1 (12,03 V)."),
    ("Δ4", "Boost EN=LOW iken çıkış ≈ VBAT−0,4 V kalır, siren zayıf öter/akım çeker → Q11 AO3400A alçak taraf anahtar (D9)."),
    ("Δ5", "NETLIGHT 1,8 V çıkış mavi LED’i (Vf≈2,9 V) süremez → Q13 MMBT3904 + LED3/R29 VMODEM’den (DNP)."),
    ("Δ6", "Kapak reed’i paralel bağlıyken kapak açılınca LOW vermesi için NC (Form-B/C) olmalı; spec’te NO yazıyor."),
    ("Δ7", "Q4/Q5 baz pull-down 100 kΩ (R23/R21) eklendi: reset/ISP sırasında modem kendiliğinden açılmasın."),
]


def notes_box(s, x, y, w, h, deltas_first=True):
    s.bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FBFAF6" stroke="#1F4D3A" stroke-width="2.5" rx="6"/>')
    s.text(x + 16, y + 34, "NOTLAR", size=24, weight="bold", color="#1F4D3A")
    gen = ["Dirençler 0603 %1 / 1/10 W, kondansatörler 0603 X7R/X5R (aksi belirtilmedikçe).",
           "DNP = üretimde takılmaz (yalnızca hata ayıklama).  Kesik çizgi = kart dışı (kablo/harici parça).",
           "Bayrak etiketleri (▷) aynı isimli netleri iki sayfa arasında birleştirir. GND = P− (FS8205A sonrası).",
           "Pin numaraları üretici veri sayfasına göredir (A7670E: SIMCom A7672X/A7670X HW Design V1.03).",
           "Kırmızı üçgen Δn: SPEC.md Rev A’dan sapma / düzeltme — açıklama aşağıda."]
    yy = y + 66
    for t in gen:
        s.text(x + 20, yy, "• " + t, size=18)
        yy += 27
    yy += 8
    s.text(x + 16, yy, "SPEC Rev A düzeltmeleri", size=20, weight="bold", color="#C0392B")
    yy += 30
    for k, t in DELTAS:
        s.text(x + 20, yy, k, size=18, weight="bold", color="#C0392B")
        s.text(x + 70, yy, t, size=17)
        yy += 26
    return yy


RAILS = [
    ("Ray", "Kaynak", "Gerilim / akım", "Besledikleri"),
    ("SOLAR_IN", "PV1 → J1", "0–7,5 V / 0,5 A", "D1 → U3 VCC, MPPT ve SOLAR_SENSE bölücü"),
    ("BAT+", "BT1‖BT2 (P+)", "3,0–4,2 V", "U3 BAT (şarj), R9 → U6, F1"),
    ("VBAT", "F1 PTC 3 A", "3,0–4,2 V / ≤4,5 A tepe", "U4, Q1→modem, R41–46 LED, U5, VBAT_SENSE"),
    ("3V3", "U4 MCP1700", "3,3 V / 250 mA", "U1, HV pull-up, Q2→V_SNS, R11 NTC, R8"),
    ("V_SNS", "Q2 AO3401A", "3,3 V anahtarlı", "SNS-1: U7 AMG8833, U8 BME680, I2C pull-up"),
    ("VMODEM", "Q1 AO3401A", "VBAT, 2 A darbe", "U2 A7670E VBAT (55–57), LED3 (DNP)"),
    ("VDD_EXT", "U2 pin 15", "1,8 V / 50 mA", "Q6–Q9 kapıları + LV pull-up"),
    ("V12", "U5 MT3608", "12,0 V / ≈30 mA", "J5 → SR1 siren (Q11 alçak taraf)"),
]


def table(s, x, y, rows, colw, size=17, rh=27, head_fill="#1F4D3A"):
    tw = sum(colw)
    for i, row in enumerate(rows):
        yy = y + i * rh
        if i == 0:
            s.bg.append(f'<rect x="{x}" y="{yy}" width="{tw}" height="{rh}" fill="{head_fill}"/>')
        elif i % 2 == 0:
            s.bg.append(f'<rect x="{x}" y="{yy}" width="{tw}" height="{rh}" fill="#EEF2EE"/>')
        cx = x
        for j, cell in enumerate(row):
            s.text(cx + 8, yy + rh - 8, cell, size=size, weight="bold" if (i == 0 or j == 0) else "normal",
                   color="#fff" if i == 0 else "#000")
            cx += colw[j]
    s.bg.append(f'<rect x="{x}" y="{y}" width="{tw}" height="{rh*len(rows)}" fill="none" stroke="#1F4D3A" stroke-width="2"/>')
    return y + rh * len(rows)


def assemble(s, title, subtitle, sheetno):
    fr, tb = frame_svg(title=title, subtitle=subtitle, sheet=sheetno, doc="ON1-MB-SCH")
    body = s.render_body()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 4200 2970" '
           f'font-family="{FONT}">',
           '<rect x="0" y="0" width="4200" height="2970" fill="#ffffff"/>']
    svg += fr
    svg += body
    svg.append("</svg>")
    return "\n".join(svg)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    s1 = sheet1()
    yy = notes_box(s1, 100, 1990, 2760, 880)
    s1.text(116, yy + 22, "GÜÇ RAYLARI", size=20, weight="bold", color="#1F4D3A")
    table(s1, 120, yy + 34, RAILS, [150, 200, 270, 560], size=16, rh=26)
    cx = 1340
    s1.text(cx, yy + 22, "TASARIM HESAPLARI", size=20, weight="bold", color="#1F4D3A")
    calc = ["MPPT: 1,205 V × (1 + 390k/100k) = 5,90 V (panel tarafı; bölücü D1 öncesine bağlı → gece sızıntı yok)",
            "Şarj akımı: 120 mV / 0,24 Ω = 500 mA  •  R6 kaybı 60 mW",
            "VBAT bölücü: 330k/1,33M = 0,2481 → 4,20 V = 1,042 V < 1,1 V ref  •  3,2 µA",
            "SOLAR bölücü: 150k/1,15M = 0,1304 → 8,4 V’a kadar ölçer (Voc soğukta ≈ 7,6 V)",
            "NTC: 220k + 10k B3950 → 0 °C = 0,437 V, 25 °C = 0,143 V, 45 °C = 0,064 V (15 µA)",
            "LED: (3,7 − 2,2) / 4,7 Ω ≈ 0,32 A/LED; 4,2 V’ta 0,40 A → 2,4 A tepe, R kaybı 0,76 W tepe / 0,09 W ort.",
            "Boost: 12 V × 30 mA / (0,85 × 3,7 V) ≈ 115 mA giriş  •  FB sızıntısı EN=LOW: 3,7 V / 210k ≈ 18 µA"]
    for i, t in enumerate(calc):
        s1.text(cx, yy + 52 + i * 25, "• " + t, size=16)
    ry = yy + 52 + len(calc) * 25 + 22
    s1.text(cx, ry, "RİSKLER / ÖNERİLER (çizimi değiştirmez)", size=20, weight="bold", color="#8a4b00")
    risks = ["BSS138 VGS(th) ≤ 1,5 V, kapı 1,8 V: −20 °C’de marjinal → NX3008NBK (pin uyumlu) önerilir.",
             "VMODEM yolu (FS8205A + PTC + Q1) 2 A GSM darbesinde ≈ 0,25 V düşer; VBAT < 3,6 V’ta modem resetlenebilir.",
             "Q1 açılışında 940 µF ani akımı: gerekirse Q1 kapısına 10 kΩ seri + 100 nF (soft-start) ekleyin.",
             "Test reed’i teneke içinden zor tetiklenir → SW3 alt PC kubbe kenarına (manyetik olmayan) yerleştirin.",
             "Bekleme bütçesine eklenmeli: NTC 15 µA + boost FB 18 µA ≈ 0,8 mAh/gün (toplam ≈ 57 mAh/gün)."]
    for i, t in enumerate(risks):
        s1.text(cx, ry + 30 + i * 25, "• " + t, size=16)
    sheets = [s1]
    try:
        from gen_sheet2 import sheet2
        s2 = sheet2(notes_box)
        sheets.append(s2)
    except ImportError:
        s2 = None
    nets, problems = build_netlist(sheets)
    total = len(sheets)
    names = {"S1": ("Güç katı", "şarj, koruma, 3V3, LED strob, siren"),
             "S2": ("Kontrol ve haberleşme", "MCU, LTE modem, sensörler")}
    for i, s in enumerate(sheets):
        t, sub = names[s.sid]
        svg = assemble(s, f"Orman Nöbetçisi ON-1 — ON1-MB Rev A", f"Devre şeması {i+1}/{total}: {t} — {sub}", f"{i+1}/{total}")
        fn = os.path.join(OUT, f"ON1-MB_RevA_schematic_sheet{i+1}.svg")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", fn)
    parts = {}
    for s in sheets:
        for ref, m in s.parts.items():
            parts[ref] = m
    with open(os.path.join(BUILD, "netlist.json"), "w", encoding="utf-8") as f:
        json.dump({"nets": nets, "parts": parts, "problems": problems}, f, ensure_ascii=False, indent=1)
    print(f"{len(nets)} nets, {len(parts)} parts")
    for p in problems:
        print("ERC:", p)


if __name__ == "__main__":
    main()
