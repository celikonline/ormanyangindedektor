# -*- coding: utf-8 -*-
"""Sheet 2 of ON1-MB Rev A: MCU, A7670E modem, level shifter, sensor rail + SNS-1."""
from schlib import Sheet


def B(key, **kw):
    d = {"bom": key}
    d.update(kw)
    return d


def sheet2(notes_box):
    s = Sheet("S2")
    # ================================================================ block 4 MCU
    s.block(100, 100, 1840, 1860, 4, "ATmega328P-AU MCU (8 MHz, 3,3 V) — kristal, reset, FTDI, ISP, LED, reed, bölücüler")
    L = [("L", 40, 4, "VCC"), ("L", 80, 6, "VCC"), ("L", 120, 18, "AVCC"), ("L", 180, 20, "AREF"),
         ("L", 300, 29, "PC6/RESET"), ("L", 380, 7, "PB6/XTAL1"), ("L", 460, 8, "PB7/XTAL2"),
         ("L", 540, 23, "PC0/ADC0 [A0]"), ("L", 590, 24, "PC1/ADC1 [A1]"), ("L", 640, 25, "PC2/ADC2 [A2]"),
         ("L", 690, 26, "PC3/ADC3 [A3]"), ("L", 740, 19, "ADC6 [A6]", "nc"), ("L", 790, 22, "ADC7 [A7]")]
    rnames = [(30, "[D0] PD0/RXD"), (31, "[D1] PD1/TXD"), (32, "[D2] PD2/INT0"), (1, "[D3] PD3/INT1"),
              (2, "[D4] PD4"), (9, "[D5] PD5"), (10, "[D6] PD6/OC0A"), (11, "[D7] PD7"), (12, "[D8] PB0"),
              (13, "[D9] PB1"), (14, "[D10] PB2"), (15, "[D11] PB3/MOSI"), (16, "[D12] PB4/MISO"),
              (17, "[D13] PB5/SCK"), (27, "[A4] PC4/SDA"), (28, "[A5] PC5/SCL")]
    R = [("R", 40 + 50 * i, n, nm) for i, (n, nm) in enumerate(rnames)]
    Bt = [("B", 100, 5, "GND"), ("B", 200, 21, "GND"), ("B", 300, 3, "GND")]
    u1 = s.ic("U1", "ATmega328P-AU (TQFP-32)", 760, 260, 400, 830, L + R + Bt, meta=B("ATMEGA"))
    # power + decoupling
    s.pwr((700, 230), "3V3")
    s.wire((700, 230), (700, 380))
    for p in ("4", "6", "18"):
        s.wire(u1[p], (700, u1[p][1]))
    s.wire((700, 250), (430, 250))
    for x, ref in ((650, "C19"), (540, "C20"), (430, "C21")):
        c = s.part("C", ref, "100nF", x, 290, lbl="l", meta=B("C100n50"))
        s.gnd(c["2"])
    s.wire(u1["20"], (480, u1["20"][1]))
    c22 = s.part("C", "C22", "100nF", 480, 480, lbl="l", meta=B("C100n50"))
    s.gnd(c22["2"])
    s.flag(u1["29"], "RESET_N", "left")
    # crystal
    y1 = s.part("XTAL", "Y1", "8 MHz", 620, 680, lbl="r", meta=B("XTAL8"))
    s.wire(u1["7"], y1["1"])
    s.wire(u1["8"], y1["2"])
    c23 = s.part("C", "C23", "22pF", 520, 640, rot=90, lbl="t", inline=True, meta=B("C22p"))
    c24 = s.part("C", "C24", "22pF", 520, 720, rot=90, lbl="b", inline=True, lbl_dx=34, meta=B("C22p"))
    s.wire(c23["1"], y1["1"])
    s.wire(c24["1"], y1["2"])
    s.wire(c23["2"], (480, 720))
    s.wire(c24["2"], (480, 720))
    s.gnd((480, 720))
    # analog / inputs
    s.flag(u1["23"], "VBAT_SENSE", "left")
    s.flag(u1["24"], "SOLAR_SENSE", "left")
    s.flag(u1["25"], "TEST_REED_N", "left")
    s.flag(u1["26"], "CHG_STAT_N", "left")
    s.flag(u1["22"], "BAT_NTC", "left")
    s.wire(u1["5"], (u1["5"][0], 1150), (u1["3"][0], 1150), u1["3"])
    s.wire(u1["21"], (u1["21"][0], 1150))
    s.gnd((u1["21"][0], 1150))
    right = [("30", "FTDI_RX", "← J6 (RXI)"), ("31", "FTDI_TX", "→ J6 (TXO)"), ("32", "TAMPER_N", "← SW1 ‖ SW2, INT0"),
             ("1", "MODEM_RI_N", "← Q9, INT1 uyandırma"), ("2", "MODEM_PWRKEY", "→ Q4"), ("9", "MODEM_DTR", "→ Q8"),
             ("10", "LED_STROBE", "→ Q3 (sayfa 1)"), ("11", "MCU_RX_MDM", "← Q6 (SoftSerial RX)"),
             ("12", "MCU_TX_MDM", "→ Q7 (SoftSerial TX)"), ("13", "SIREN_EN", "→ U5 EN, Q11 (sayfa 1)"),
             ("14", "MODEM_PWR_EN", "→ Q5 → Q1"), ("15", "SENSOR_PWR_N", "→ Q2 (LOW = açık)"),
             ("16", "STATUS_LED", "→ LED1"), ("17", "CHG_INHIBIT", "→ Q12 (sayfa 1) Δ1"),
             ("27", "I2C_SDA", "↔ SNS-1"), ("28", "I2C_SCL", "→ SNS-1")]
    for pn, net, note in right:
        s.flag(u1[pn], net, "right", note=note)
    s.text(780, 1215, "Optiboot, Arduino Pro Mini 3V3/8 MHz uyumlu • BOD 2,7 V • ADC iç 1,1 V referans", size=17, color="#333")

    # ---- row A: reset / FTDI / ISP / test reed
    s.text(120, 1268, "Programlama ve reset", size=19, weight="bold", color="#1F4D3A")
    r12 = s.part("R", "R12", "10k", 400, 1340, lbl="r", meta=B("R10k"))
    s.pwr(r12["1"], "3V3")
    s.wire(r12["2"], (400, 1420))
    c25 = s.part("C", "C25", "100nF", 300, 1420, rot=90, lbl="t", meta=B("C100n50"))
    s.wire(c25["1"], (400, 1420))
    s.wire((400, 1420), (500, 1420))
    s.flag((500, 1420), "RESET_N", "right")
    s.flag(c25["2"], "FTDI_DTR", "left")
    s.text(130, 1500, "DTR otomatik reset (Arduino uyumlu)", size=15, color="#555")
    j6 = s.conn("J6", "FTDI 6p 2,54 mm", 760, 1300, ["GND", "CTS", "3V3", "RXI", "TXO", "DTR"], side="R", w=96,
                far=False, meta=B("J_HDR6"))
    s.gnd(j6["1"], "right")
    s.gnd(j6["2"], "right")
    s.pwr(j6["3"], "3V3", "right")
    s.flag(j6["4"], "FTDI_RX", "right")
    s.flag(j6["5"], "FTDI_TX", "right")
    s.flag(j6["6"], "FTDI_DTR", "right")
    j7 = s.ic("J7", "ISP 2×3 2,54 mm", 1190, 1310, 110, 160, [
        ("L", 40, 1, "MISO"), ("L", 80, 3, "SCK"), ("L", 120, 5, "RST"),
        ("R", 40, 2, "VCC"), ("R", 80, 4, "MOSI"), ("R", 120, 6, "GND")], meta=B("J_ISP"), name_size=16)
    s.flag(j7["1"], "STATUS_LED", "left")
    s.flag(j7["3"], "CHG_INHIBIT", "left")
    s.flag(j7["5"], "RESET_N", "left")
    s.pwr(j7["2"], "3V3", "right")
    s.flag(j7["4"], "SENSOR_PWR_N", "right")
    s.gnd(j7["6"], "right")
    j10 = s.conn("J10", "JST-PH 2p", 1700, 1340, ["TEST", "GND"], side="L", w=90, meta=B("J_PH2"))
    s.flag(j10["1"], "TEST_REED_N", "left")
    s.wire(j10["2"], (1640, j10["2"][1]))
    s.gnd((1640, j10["2"][1]))
    s.offboard(1835, 1290, 95, 250, "Test")
    sw3 = s.part("REED_NO", "SW3", "", 1880, 1420, show_ref=False, meta=B("REED_NO", offboard=True))
    s.wire(j10["1k"], (1880, j10["1k"][1]), sw3["1"], dashed=True)
    s.wire(j10["2k"], (1845, j10["2k"][1]), (1845, 1475), (1880, 1475), sw3["2"], dashed=True)
    s.text(1840, 1505, "SW3", size=15, weight="bold")
    s.text(1840, 1525, "reed NO", size=14)
    s.text(1520, 1585, "SW3: mıknatıs test noktası — alt PC kubbe kenarı", size=14, color="#555")
    s.text(1520, 1603, "(teneke gövde manyetik alanı zayıflatır)", size=14, color="#555")

    # ---- row B: dividers, status LED, tamper
    s.text(120, 1640, "Analog ölçüm, durum LED’i, kurcalama", size=19, weight="bold", color="#1F4D3A")
    s.pwr((220, 1700), "VBAT")
    r15 = s.part("R", "R15", "1M 1%", 220, 1740, lbl="l", meta=B("R1M"))
    s.wire(r15["2"], (220, 1820))
    r16 = s.part("R", "R16", "330k 1%", 220, 1880, lbl="l", meta=B("R330k"))
    s.wire((220, 1820), r16["1"])
    s.gnd(r16["2"])
    c27 = s.part("C", "C27", "100nF", 320, 1880, meta=B("C100n50"))
    s.wire((220, 1820), (380, 1820))
    s.wire((320, 1820), c27["1"])
    s.gnd(c27["2"])
    s.flag((380, 1820), "VBAT_SENSE", "right")
    s.flag((640, 1690), "SOLAR_IN", "up")
    r17 = s.part("R", "R17", "1M 1%", 640, 1730, lbl="l", meta=B("R1M"))
    s.wire((640, 1690), r17["1"])
    s.wire(r17["2"], (640, 1820))
    r18 = s.part("R", "R18", "150k 1%", 640, 1880, lbl="l", meta=B("R150k"))
    s.wire((640, 1820), r18["1"])
    s.gnd(r18["2"])
    c28 = s.part("C", "C28", "100nF", 740, 1880, meta=B("C100n50"))
    s.wire((640, 1820), (800, 1820))
    s.wire((740, 1820), c28["1"])
    s.gnd(c28["2"])
    s.flag((800, 1820), "SOLAR_SENSE", "right")
    s.flag((1030, 1690), "STATUS_LED", "up")
    r13 = s.part("R", "R13", "1k", 1030, 1730, meta=B("R1k"))
    s.wire((1030, 1690), r13["1"])
    led1 = s.part("LED", "LED1", "yeşil 0603", 1030, 1850, lbl="r", lbl_dx=4, meta=B("LED_G"))
    s.wire(r13["2"], led1["A"])
    s.gnd(led1["K"])
    s.pwr((1230, 1660), "3V3")
    r14 = s.part("R", "R14", "1M", 1230, 1700, lbl="l", meta=B("R1M"))
    s.wire(r14["2"], (1230, 1770), (1650, 1770))
    s.wire((1230, 1770), (1230, 1795))
    s.flag((1230, 1795), "TAMPER_N", "down")
    c26 = s.part("C", "C26", "100nF", 1330, 1830, meta=B("C100n50"))
    s.wire((1330, 1770), c26["1"])
    s.gnd(c26["2"])
    sw1 = s.part("SWV", "SW1", "SW-18010P", 1450, 1830, meta=B("SW18010"))
    s.wire((1450, 1770), sw1["1"])
    s.gnd(sw1["2"])
    j9 = s.conn("J9", "JST-PH 2p", 1680, 1750, ["LID", "GND"], side="L", w=80, meta=B("J_PH2"), lbl="b")
    s.wire((1650, 1770), j9["1"])
    s.wire(j9["2"], (1630, j9["2"][1]), (1630, 1830))
    s.gnd((1630, 1830))
    s.offboard(1800, 1690, 130, 255, "Kapak")
    sw2 = s.part("REED_NC", "SW2", "", 1870, 1830, show_ref=False, meta=B("REED_NC", offboard=True))
    s.wire(j9["1k"], (1870, j9["1k"][1]), sw2["1"], dashed=True)
    s.wire(j9["2k"], (1820, j9["2k"][1]), (1820, 1890), (1870, 1890), sw2["2"], dashed=True)
    s.text(1812, 1920, "SW2 reed NC", size=14, weight="bold")
    s.text(1812, 1938, "+ kapak mıknatısı", size=13)
    s.revmark(1905, 1745, 6)

    # ================================================================ block 5 modem
    s.block(1970, 100, 2130, 1200, 5, "A7670E LTE Cat-1 modem — güç anahtarı, PWRKEY, SIM, anten")
    RY = 320
    s.pwr((2060, RY), "VBAT")
    r19 = s.part("R", "R19", "100k", 2180, 380, lbl="l", meta=B("R100k"))
    s.wire((2060, RY), (2310, RY))
    s.wire((2180, RY), r19["1"])
    q1 = s.part("PMOSD", "Q1", "AO3401A", 2350, RY + 24, rot=270, lbl="t", lbl_dy=-6, lbl_dx=-34, meta=B("AO3401"))
    s.wire(r19["2"], (2350, 420))
    s.wire(q1["G"], (2350, 420), (2350, 460))
    s.netname((2265, 420), "Q1_GATE", dy=-10, anchor="middle")
    q5 = s.part("NPN", "Q5", "MMBT3904", 2326, 500, lbl="r", lbl_dx=6, meta=B("MMBT3904"))
    s.gnd(q5["E"])
    r20 = s.part("R", "R20", "10k", 2190, 500, rot=90, lbl="t", inline=True, meta=B("R10k"))
    s.wire(r20["1"], q5["B"])
    r21 = s.part("R", "R21", "100k", 2258, 580, lbl="r", meta=B("R100k"))
    s.wire((2258, 500), r21["1"])
    s.gnd(r21["2"])
    s.flag(r20["2"], "MODEM_PWR_EN", "left")
    s.revmark(2300, 660, 7)
    s.wire(q1["D"], (2990, RY))
    s.pwr((2440, RY), "VMODEM")
    caps = [("CP", "C10", "470µF", 2490, "C470u"), ("CP", "C11", "470µF", 2580, "C470u"),
            ("C", "C12", "100nF", 2670, "C100n50"), ("C", "C13", "33pF", 2760, "C33p"),
            ("C", "C14", "10pF", 2850, "C10p")]
    for k, ref, val, x, key in caps:   # pin 1 of each cap lies on the VMODEM rail (y = 320)
        c = s.part(k, ref, val, x, 360, lbl="b", lbl_dy=26, meta=B(key))
        s.gnd(c["2"])
    tv2 = s.part("TVS", "TVS2", "ESD5Z5.0", 2940, 360, rot=180, lbl="b", lbl_dy=26, meta=B("ESD5Z"))
    s.gnd(tv2["A"])
    s.text(2470, 500, "C10, C11: 6,3 V polimer, düşük ESR (2 A GSM darbe)", size=15, color="#555")
    u2 = s.ic("U2", "SIMCom A7670E (LCC+LGA)", 3050, 290, 350, 910, [
        ("L", 30, 55, "VBAT"), ("L", 70, 56, "VBAT"), ("L", 110, 57, "VBAT"),
        ("L", 270, 9, "TXD"), ("L", 310, 10, "RXD"), ("L", 350, 3, "DTR"), ("L", 390, 4, "RI"),
        ("L", 440, 7, "CTS", "nc"), ("L", 480, 8, "RTS", "nc"), ("L", 520, 5, "DCD", "nc"),
        ("L", 590, 15, "VDD_EXT (1V8)"), ("L", 670, 1, "PWRKEY"), ("L", 710, 16, "RESET", "nc"),
        ("R", 70, 60, "RF_ANT"),
        ("R", 300, 31, "USIM_DATA"), ("R", 350, 32, "USIM_CLK"), ("R", 400, 33, "USIM_RST"),
        ("R", 450, 30, "USIM_VDD"), ("R", 500, 34, "USIM_DET", "nc"),
        ("R", 570, 52, "NETLIGHT"), ("R", 610, 66, "STATUS", "nc"),
        ("R", 690, 24, "USB_VBUS"), ("R", 730, 27, "USB_DP"), ("R", 770, 28, "USB_DM"),
        ("R", 810, 6, "USB_BOOT"), ("R", 850, 23, "UART_LOG_TX"),
        ("B", 80, 2, "GND"), ("B", 160, 17, "GND"), ("B", 240, 18, "GND")], meta=B("A7670E"))
    s.wire((2990, RY), (3020, RY))
    s.wire((2990, RY), (2990, 400))
    s.wire(u2["56"], (2990, u2["56"][1]))
    s.wire(u2["57"], (2990, u2["57"][1]))
    s.wire(u2["2"], (u2["2"][0], 1255), (u2["18"][0], 1255), u2["18"])
    s.wire(u2["17"], (u2["17"][0], 1255))
    s.gnd((u2["17"][0], 1255))
    s.text(3330, 1275, "+ GND: 29, 39, 45, 46, 54, 58, 59, 61–65, 69–89, 91, 92, 94", size=14, color="#555")
    s.flag(u2["9"], "MDM_TXD_1V8", "left")
    s.flag(u2["10"], "MDM_RXD_1V8", "left")
    s.flag(u2["3"], "MDM_DTR_1V8", "left")
    s.flag(u2["4"], "MDM_RI_1V8", "left")
    s.pwr(u2["15"], "VDD_EXT", "left")
    # PWRKEY
    s.wire(u2["1"], (2760, u2["1"][1]), (2760, 1000))
    q4 = s.part("NPN", "Q4", "MMBT3904", 2736, 1040, lbl="r", lbl_dx=6, meta=B("MMBT3904"))
    s.gnd(q4["E"])
    r22 = s.part("R", "R22", "4,7k", 2600, 1040, rot=90, lbl="t", inline=True, meta=B("R4k7"))
    s.wire(r22["1"], q4["B"])
    r23 = s.part("R", "R23", "100k", 2668, 1120, lbl="l", meta=B("R100k"))
    s.wire((2668, 1040), r23["1"])
    s.gnd(r23["2"])
    s.flag(r22["2"], "MODEM_PWRKEY", "left")
    s.text(2400, 1215, "PWRKEY: ≥ 500 ms LOW = aç, ≥ 2,5 s = kapat (veya AT+CPOF)", size=15, color="#555")
    # NETLIGHT (DNP)
    s.pwr((2250, 720), "VMODEM")
    r29 = s.part("R", "R29", "1k", 2250, 760, dnp=True, meta=B("R1k"))
    led3 = s.part("LED", "LED3", "mavi 0603", 2250, 860, dnp=True, lbl="r", lbl_dx=4, meta=B("LED_B"))
    s.wire(r29["2"], led3["A"])
    s.wire(led3["K"], (2250, 940))
    q13 = s.part("NPN", "Q13", "MMBT3904", 2226, 980, dnp=True, lbl="r", lbl_dx=6, meta=B("MMBT3904"))
    s.gnd(q13["E"])
    s.flag((2080, 860), "MDM_NETLIGHT", "up")
    r28 = s.part("R", "R28", "10k", 2080, 910, lbl="l", dnp=True, meta=B("R10k"))
    s.wire((2080, 860), r28["1"])
    s.wire(r28["2"], (2080, 980), q13["B"])
    s.revmark(2140, 1120, 5)
    # RF
    s.wire(u2["60"], (3480, u2["60"][1]))
    c31 = s.part("C", "C31", "", 3480, 400, dnp=True, lbl="b", lbl_dy=26, meta=B("C_RF"))
    s.gnd(c31["2"])
    r27 = s.part("R", "R27", "0Ω", 3570, 360, rot=90, lbl="t", inline=True, meta=B("R0"))
    s.wire((3480, 360), r27["2"])
    s.wire(r27["1"], (3700, 360))
    c32 = s.part("C", "C32", "", 3650, 400, dnp=True, lbl="b", lbl_dy=26, meta=B("C_RF"))
    s.gnd(c32["2"])
    j12 = s.part("COAX", "J12", "U.FL", 3740, 360, lbl="t", inline=True, meta=B("UFL"))
    s.gnd(j12["GND"])
    s.text(3410, 265, "π eşleştirme (50 Ω hat)", size=15, color="#555")
    ant = s.part("ANT", "ANT1", "", 4030, 290, show_ref=False, meta=B("OFF", offboard=True))
    s.wire(j12["SIGR"], (4030, 360), ant["1"], dashed=True)
    s.text(3800, 395, "15 cm U.FL–SMA pigtail", size=14, color="#555")
    s.text(3800, 413, "+ SMA dişi bulkhead (O-ring)", size=14, color="#555")
    s.text(3790, 255, "ANT1 3 dBi IP67 LTE", size=14, weight="bold")
    # SIM
    for pn, ref, net in (("31", "R24", "SIM_DATA"), ("32", "R25", "SIM_CLK"), ("33", "R26", "SIM_RST")):
        y = u2[pn][1]
        r = s.part("R", ref, "22Ω", 3510, y, rot=90, lbl="t", inline=True, meta=B("R22"))
        s.wire(u2[pn], r["2"])
        s.flag(r["1"], net, "right")
    s.flag(u2["30"], "SIM_VDD", "right")
    s.flag(u2["52"], "MDM_NETLIGHT", "right")
    for pn, ref, nm in (("24", "TP1", "USB_VBUS"), ("27", "TP2", "USB_DP"), ("28", "TP3", "USB_DM"),
                        ("6", "TP4", "USB_BOOT"), ("23", "TP5", "LOG_TX")):
        s.wire(u2[pn], (3470, u2[pn][1]))
        s.tp((3470, u2[pn][1]), ref, nm)
    s.text(3440, 1185, "TP1–TP5: FW güncelleme / log", size=14, color="#555")
    j11 = s.ic("J11", "Nano-SIM push-push", 3850, 560, 150, 230, [
        ("L", 40, "C1", "VCC"), ("L", 80, "C7", "I/O"), ("L", 120, "C3", "CLK"), ("L", 160, "C2", "RST"),
        ("L", 200, "C6", "VPP", "nc"), ("B", 75, "C5", "GND")], meta=B("SIM"), name_size=16)
    s.flag(j11["C1"], "SIM_VDD", "left")
    s.flag(j11["C7"], "SIM_DATA", "left")
    s.flag(j11["C3"], "SIM_CLK", "left")
    s.flag(j11["C2"], "SIM_RST", "left")
    s.gnd(j11["C5"])
    s.flag((3700, 900), "SIM_VDD", "left")
    s.wire((3700, 900), (3880, 900))
    c29 = s.part("C", "C29", "100nF", 3780, 940, lbl="b", lbl_dy=26, meta=B("C100n50"))
    c30 = s.part("C", "C30", "33pF", 3880, 940, lbl="b", lbl_dy=26, meta=B("C33p"))
    for c in (c29, c30):
        s.gnd(c["2"])
    u10 = s.ic("U10", "ESDA6V1-5SC6", 3800, 1060, 120, 170, [
        ("L", 30, 1, "IO1"), ("L", 70, 3, "IO2"), ("L", 110, 4, "IO3"), ("L", 150, 5, "IO4"),
        ("R", 30, 6, "IO5", "nc"), ("B", 60, 2, "GND")], meta=B("ESDA6V1"), name_size=15, title_pos="right")
    s.flag(u10["1"], "SIM_VDD", "left")
    s.flag(u10["3"], "SIM_DATA", "left")
    s.flag(u10["4"], "SIM_CLK", "left")
    s.flag(u10["5"], "SIM_RST", "left")
    s.gnd(u10["2"])

    # ================================================================ block 6 level shifter
    s.block(1970, 1330, 900, 1540, 6, "4 kanal BSS138 seviye çevirici (1,8 V ↔ 3,3 V)")
    s.text(1990, 1400, "LV: VDD_EXT 1,8 V + 10 kΩ  •  HV: 3V3 + 10 kΩ", size=17, color="#333")
    s.text(1990, 1424, "Modem kapalı (VDD_EXT = 0) iken FET’ler kapalı → modem geri beslenmez", size=15, color="#555")
    chans = [("Q6", "R30", "R34", "MDM_TXD_1V8", "MCU_RX_MDM", "Kanal 1: A7670E TXD (9) → U1 D7"),
             ("Q7", "R31", "R35", "MDM_RXD_1V8", "MCU_TX_MDM", "Kanal 2: U1 D8 → A7670E RXD (10)"),
             ("Q8", "R32", "R36", "MDM_DTR_1V8", "MODEM_DTR", "Kanal 3: U1 D5 → A7670E DTR (3)"),
             ("Q9", "R33", "R37", "MDM_RI_1V8", "MODEM_RI_N", "Kanal 4: A7670E RI (4) → U1 D3 (INT1)")]
    for i, (q, rl, rh, lv, hv, title) in enumerate(chans):
        ly = 1650 + 300 * i
        s.text(1990, ly - 172, title, size=17, weight="bold")
        r_l = s.part("R", rl, "10k", 2240, ly - 70, lbl="l", meta=B("R10k"))
        s.pwr(r_l["1"], "VDD_EXT")
        s.wire(r_l["2"], (2240, ly))
        qq = s.part("NMOS", q, "BSS138", 2420, ly - 24, rot=90, lbl="b", lbl_dy=4, meta=B("BSS138"))
        s.pwr(qq["G"], "VDD_EXT")
        r_h = s.part("R", rh, "10k", 2600, ly - 70, lbl="r", meta=B("R10k"))
        s.pwr(r_h["1"], "3V3")
        s.wire(r_h["2"], (2600, ly))
        s.flag((2170, ly), lv, "left")
        s.wire((2170, ly), qq["S"])
        s.wire(qq["D"], (2680, ly))
        s.flag((2680, ly), hv, "right")
    s.text(1990, 2830, "Öneri: düşük VGS(th) pin uyumlu NX3008NBK (−20 °C marjı)", size=15, color="#8a4b00", italic=True)

    # ================================================================ block 7 sensors
    s.block(2900, 1330, 1200, 1240, 7, "Sensör rayı (Q2) + SNS-1 kartı: AMG8833 + BME680")
    SY = 1450
    s.pwr((2960, SY), "3V3")
    r38 = s.part("R", "R38", "100k", 3040, 1510, lbl="l", meta=B("R100k"))
    s.wire((2960, SY), (3100, SY))
    s.wire((3040, SY), r38["1"])
    q2 = s.part("PMOSD", "Q2", "AO3401A", 3140, SY + 24, rot=270, lbl="t", lbl_dy=-6, meta=B("AO3401"))
    s.wire(r38["2"], (3040, 1580), (3140, 1580))
    s.wire(q2["G"], (3140, 1580), (3140, 1600))
    s.flag((3140, 1600), "SENSOR_PWR_N", "down")
    s.wire(q2["D"], (3770, SY))
    c33 = s.part("C", "C33", "10µF", 3260, SY + 40, meta=B("C10u10"))
    c34 = s.part("C", "C34", "100nF", 3360, SY + 40, meta=B("C100n50"))
    for c in (c33, c34):
        s.gnd(c["2"])
    r39 = s.part("R", "R39", "4,7k", 3490, 1510, lbl="r", meta=B("R4k7"))
    r40 = s.part("R", "R40", "4,7k", 3600, 1510, lbl="r", meta=B("R4k7"))
    s.wire((3490, SY), r39["1"])
    s.wire((3600, SY), r40["1"])
    s.flag(r39["2"], "I2C_SDA", "down")
    s.flag(r40["2"], "I2C_SCL", "down")
    s.pwr((3710, SY), "V_SNS")
    j4 = s.conn("J4", "JST-SH 6p", 3800, 1430, ["V_SNS", "GND", "SDA", "GND", "SCL", "INT"], side="L", w=100,
                meta=B("J_SH6"))
    s.gnd(j4["2"], "left")
    s.flag(j4["3"], "I2C_SDA", "left")
    s.gnd(j4["4"], "left")
    s.flag(j4["5"], "I2C_SCL", "left")
    s.noconn(j4["6"])
    s.text(2920, 1700, "D11 = LOW → V_SNS açık; R38 → varsayılan kapalı (I2C kilitlenme kurtarma)", size=15, color="#555")
    # SNS-1 board
    s.offboard(2920, 1725, 1035, 830, "SNS-1 yardımcı kartı (termal pencere arkasında, yataydan 35° aşağı)",
               fill="#FAFAF4", stroke="#1F4D3A", dash="none", tsize=18)
    j101 = s.conn("J101", "JST-SH 6p", 3800, 1900, ["INT", "SCL", "GND", "SDA", "GND", "V_SNS"], side="L", w=100,
                  numbers=[6, 5, 4, 3, 2, 1], meta=B("J_SH6"))
    for i in range(6):
        n = str(i + 1)
        a = j4[n + "k"]
        b = j101[n + "k"]
        xr = 4050 - 20 * i
        s.wire(a, (xr, a[1]), (xr, b[1]), b, dashed=True)
    s.text(3640, 1880, "kablo 1:1", size=14, color="#555", italic=True)
    s.text(3600, 1712, "JST-SH 6p kablo ≈ 25 cm", size=15, color="#555", italic=True)
    s.flag(j101["6"], "AMG_INT", "left")
    s.flag(j101["5"], "I2C_SCL", "left")
    s.gnd(j101["4"], "left")
    s.flag(j101["3"], "I2C_SDA", "left")
    s.gnd(j101["2"], "left")
    s.pwr(j101["1"], "V_SNS", "left")
    u7 = s.ic("U7", "AMG8833 Grid-EYE (0x69)", 3060, 1840, 280, 200, [
        ("L", 40, 9, "VDD"), ("L", 80, 13, "VPP"), ("L", 120, 5, "AD_SELECT"),
        ("R", 40, 2, "SDA"), ("R", 80, 3, "SCL"), ("R", 120, 4, "INT"),
        ("B", 50, 6, "GND"), ("B", 140, 10, "AVDD-PC"), ("B", 230, 12, "DVDD-PC")], meta=B("AMG8833"), name_size=16)
    s.pwr((2990, 1855), "V_SNS")
    s.wire((2990, 1855), (2990, 2000))
    for p in ("9", "13", "5"):
        s.wire(u7[p], (2990, u7[p][1]))
    c101 = s.part("C", "C101", "10µF", 2990, 2040, lbl="l", meta=B("C10u10"))
    s.gnd(c101["2"])
    s.gnd(u7["6"])
    c102 = s.part("C", "C102", "1µF", 3200, 2110, lbl="l", meta=B("C1u"))
    r101 = s.part("R", "R101", "20Ω", 3200, 2230, lbl="l", meta=B("R20"))
    s.wire(c102["2"], r101["1"])
    s.gnd(r101["2"])
    c103 = s.part("C", "C103", "1,5µF", 3290, 2110, lbl="r", meta=B("C1u5"))
    s.gnd(c103["2"])
    s.flag(u7["2"], "I2C_SDA", "right")
    s.flag(u7["3"], "I2C_SCL", "right")
    s.flag(u7["4"], "AMG_INT", "right")
    s.text(2940, 2335, "NC: 1, 7, 8, 11, 14 boş", size=14, color="#555")
    u8 = s.ic("U8", "BME680 (0x77)", 3470, 2250, 210, 210, [
        ("T", 60, 8, "VDD"), ("T", 140, 6, "VDDIO"),
        ("L", 40, 3, "SDI"), ("L", 80, 4, "SCK"), ("L", 120, 2, "CSB"), ("L", 160, 5, "SDO"),
        ("B", 60, 1, "GND"), ("B", 140, 7, "GND")], meta=B("BME680"), name_size=16, title_pos="none")
    s.text(3696, 2420, "U8", weight="bold")
    s.text(3696, 2443, "BME680 (0x77)")
    s.wire(u8["8"], (u8["8"][0], 2200), (u8["6"][0], 2200), u8["6"])
    s.pwr((3570, 2200), "V_SNS")
    s.flag(u8["3"], "I2C_SDA", "left")
    s.flag(u8["4"], "I2C_SCL", "left")
    s.wire(u8["2"], (3400, u8["2"][1]), (3400, u8["5"][1]), u8["5"])
    s.pwr((3400, 2390), "V_SNS", "left")
    s.wire(u8["1"], (u8["1"][0], 2510), (u8["7"][0], 2510), u8["7"])
    s.gnd((3570, 2510))
    s.pwr((3760, 2190), "V_SNS")
    s.wire((3760, 2190), (3890, 2190))
    c104 = s.part("C", "C104", "100nF", 3810, 2230, lbl="b", lbl_dy=26, meta=B("C100n50"))
    c105 = s.part("C", "C105", "100nF", 3890, 2230, lbl="b", lbl_dy=26, meta=B("C100n50"))
    for c in (c104, c105):
        s.gnd(c["2"])
    s.text(2940, 2505, "U7: AD_SELECT = VDD → I2C 0x69", size=15, color="#333")
    s.text(2940, 2527, "U8: SDO = CSB = VDD → I2C 0x77", size=15, color="#333")

    # ================================================================ notes
    notes_box_s2(s)
    return s


PINMAP = [
    ("Pin", "AVR (TQFP#)", "Net", "Yön", "Açıklama"),
    ("D0", "PD0 (30)", "FTDI_RX", "G", "FTDI başlığı J6.4"),
    ("D1", "PD1 (31)", "FTDI_TX", "Ç", "FTDI başlığı J6.5"),
    ("D2", "PD2 (32)", "TAMPER_N", "G", "SW1 ‖ SW2 → GND, 1 MΩ pull-up, INT0"),
    ("D3", "PD3 (1)", "MODEM_RI_N", "G", "A7670E RI (Q9), INT1 uyandırma"),
    ("D4", "PD4 (2)", "MODEM_PWRKEY", "Ç", "Q4 MMBT3904 → PWRKEY, HIGH = basılı"),
    ("D5", "PD5 (9)", "MODEM_DTR", "Ç", "Q8 → DTR; HIGH = uyku izni"),
    ("D6", "PD6 (10)", "LED_STROBE", "Ç", "Q3 AO3400A (sayfa 1)"),
    ("D7", "PD7 (11)", "MCU_RX_MDM", "G", "SoftwareSerial RX ← A7670E TXD (Q6)"),
    ("D8", "PB0 (12)", "MCU_TX_MDM", "Ç", "SoftwareSerial TX → A7670E RXD (Q7)"),
    ("D9", "PB1 (13)", "SIREN_EN", "Ç", "U5 EN + Q11 kapı, 100 kΩ pull-down"),
    ("D10", "PB2 (14)", "MODEM_PWR_EN", "Ç", "Q5 → Q1 AO3401A, HIGH = modem açık"),
    ("D11", "PB3 (15)", "SENSOR_PWR_N", "Ç", "Q2 AO3401A kapı, LOW = sensör rayı açık"),
    ("D12", "PB4 (16)", "STATUS_LED", "Ç", "LED1 yeşil (R13 1 kΩ), ışık borusu"),
    ("D13", "PB5 (17)", "CHG_INHIBIT", "Ç", "Δ1 YENİ: Q12 → CN3791 MPPT, HIGH = şarj durur"),
    ("A0", "PC0 (23)", "VBAT_SENSE", "An", "1 MΩ / 330 kΩ, oran 0,2481"),
    ("A1", "PC1 (24)", "SOLAR_SENSE", "An", "1 MΩ / 150 kΩ, oran 0,1304 (D1 öncesi)"),
    ("A2", "PC2 (25)", "TEST_REED_N", "G", "SW3 test reed (J10), iç pull-up"),
    ("A3", "PC3 (26)", "CHG_STAT_N", "G", "CN3791 CHRG açık drenaj, iç pull-up"),
    ("A4/A5", "PC4/PC5 (27/28)", "I2C_SDA / I2C_SCL", "G/Ç", "4,7 kΩ → V_SNS"),
    ("A6", "ADC6 (19)", "—", "", "boş"),
    ("A7", "ADC7 (22)", "BAT_NTC", "An", "Δ1 YENİ: NTC 10k B3950 / 220 kΩ, 0…45 °C şarj penceresi"),
]

CONNS = [
    ("Ref", "Tip", "Pinler (1 → n)"),
    ("J1", "JST-XH 2p", "1 PV+ (SOLAR_IN), 2 PV− (GND) — panel, PG7 rakor"),
    ("J2", "JST-VH 2p (Δ2)", "1 B+ (BAT+), 2 B− (BAT−) — 2×18650 tutucu"),
    ("J3", "JST-PH 2p (Δ1)", "1 NTC (BAT_NTC), 2 GND — hücreye yapıştırılmış NTC 10k B3950"),
    ("J4 / J101", "JST-SH 6p", "1 V_SNS, 2 GND, 3 I2C_SDA, 4 GND, 5 I2C_SCL, 6 AMG_INT (ana kartta NC) — SNS-1 kablosu"),
    ("J5", "JST-XH 2p", "1 +12V (V12), 2 SİREN− (Q11 drenaj) — piezo siren"),
    ("J6", "Pin başlık 1×6", "1 GND, 2 CTS (GND), 3 3V3, 4 RXI ← FTDI TX, 5 TXO → FTDI RX, 6 DTR (C25 → RESET)"),
    ("J7", "Pin başlık 2×3", "1 MISO/D12, 2 3V3, 3 SCK/D13, 4 MOSI/D11, 5 RESET_N, 6 GND (AVR ISP)"),
    ("J8", "JST-XH 8p", "1–6 LED anot A1–A6 (R41–R46 üzerinden VBAT), 7–8 LED_K ortak katot (Q3)"),
    ("J9 / J10", "JST-PH 2p", "J9: 1 TAMPER_N, 2 GND (kapak reed NC)  •  J10: 1 TEST_REED_N, 2 GND (test reed NO)"),
    ("J11", "Nano-SIM", "C1 VCC, C2 RST, C3 CLK, C5 GND, C6 VPP (NC), C7 I/O"),
    ("J12", "U.FL", "RF_ANT (π: R27 0 Ω, C31/C32 DNP) → 15 cm pigtail → SMA bulkhead → 3 dBi anten"),
]


def notes_box_s2(s):
    from gen_schematic import table
    x, y, w, h = 100, 1990, 1840, 880
    s.bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FBFAF6" stroke="#1F4D3A" stroke-width="2.5" rx="6"/>')
    s.text(x + 16, y + 32, "U1 PİN HARİTASI (SPEC §3 + düzeltmeler)", size=22, weight="bold", color="#1F4D3A")
    yy = table(s, x + 16, y + 44, PINMAP, [90, 200, 260, 60, 1190], size=15, rh=23)
    s.text(x + 16, yy + 24, "Firmware değişikliği gerekir (Δ1): A7 (BAT_NTC) okunur; T < 0 °C veya T > 45 °C ise D13 = HIGH "
           "(şarj durur).  VBAT = ADC×1,1/1023/0,2481", size=15, color="#C0392B")
    s.text(x + 16, yy + 56, "KONEKTÖRLER", size=19, weight="bold", color="#1F4D3A")
    table(s, x + 16, yy + 66, CONNS, [90, 220, 1490], size=14, rh=21)
