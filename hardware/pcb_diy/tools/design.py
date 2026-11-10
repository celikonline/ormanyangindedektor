"""ON1-DIY Rev A — placement and netlist (the single source for the generator).

Pin assignments follow SPEC.md §3 exactly (Arduino Pro Mini numbering).
Coordinates: mm, origin = board bottom-left, Y up, viewed from the TOP (component side).
"""
from board import Board, Component
import footprints as F

BOARD_W, BOARD_H = 100.0, 75.0
MOUNT_HOLES = [(4.0, 4.0), (96.0, 4.0), (4.0, 71.0), (96.0, 71.0)]

# track widths (mm)
W_SIG = 0.8
W_PWR = 1.5
W_MID = 1.0

NET_WIDTH = {
    "VBAT": W_PWR, "VMODEM": W_PWR, "PACK_P": W_PWR, "CELL_N": W_PWR, "SOL_IN": W_PWR,
    "SOL_P": W_PWR, "LED_K": W_PWR, "GND": W_PWR,
    "LED_A1": W_MID, "LED_A2": W_MID, "LED_A3": W_MID, "LED_A4": W_MID, "LED_A5": W_MID,
    "LED_A6": W_MID, "SIR_VIN": W_MID, "SIREN_P": W_SIG, "+3V3": W_SIG,
}

# components whose power-net pins are only small-signal taps (0.8 mm is plenty)
SMALL_TAP_REFS = {"R17", "R1", "R14", "R19", "C1", "C2"}
# GND pads that carry real current (used for the width of their pour connection)
GND_POWER = {
    ("U5", "P-"), ("U4", "BAT-"), ("U4", "IN-"), ("J1", "1"), ("Q3", "S"), ("J2", "3"), ("J2", "4"),
    ("C10", "-"), ("C11", "-"), ("U7", "VIN-"), ("U7", "OUT-"), ("J7", "2"), ("TVS1", "A"),
}

# routing priority inside a stage (earlier = routed first)
ROUTE_ORDER = ["PACK_P", "CELL_N", "SOL_IN", "SOL_P", "VBAT", "LED_K", "VMODEM",
               "LED_A1", "LED_A2", "LED_A3", "LED_A4", "LED_A5", "LED_A6", "SIR_VIN",
               "D3_RI", "D5_DTR", "D7_RX", "D8_TX", "M_RI", "M_DTR", "M_TXD", "M_RXD", "VDD_EXT"]


# Hand-routed power skeleton (net, width, waypoints). The auto-router completes the rest.
HAND_ROUTES = [
    ("PACK_P", 1.5, [(95.25, 17.78), (91.5, 17.78), (91.5, 29.0)]),
    ("PACK_P", 1.5, [(88.0, 16.51), (89.27, 17.78), (91.5, 17.78)]),
    ("CELL_N", 1.5, [(95.25, 12.7), (93.0, 12.7), (93.0, 8.89), (88.0, 8.89)]),
    ("VBAT", 1.5, [(86.42, 23.0), (81.28, 17.86), (81.28, 16.5), (50.8, 16.5)]),
    # modem supply: Q1 drain up the riser to the 470 uF caps and J2.1
    ("VMODEM", 1.5, [(22.75, 18.5), (21.6, 19.65), (21.6, 37.8), (9.19, 37.8), (7.62, 39.37)]),
    ("SOL_IN", 1.5, [(95.25, 43.18), (92.7, 43.18), (88.0, 47.88), (88.0, 48.5)]),
    ("SOL_P", 1.5, [(88.0, 33.26), (81.7, 33.26), (81.7, 33.2)]),
    ("SOL_P", 1.5, [(81.7, 33.2), (80.07, 31.57), (80.07, 29.0)]),
    ("LED_K", 1.5, [(41.14, 12.0), (41.14, 7.12), (43.18, 5.08), (48.26, 5.08)]),
] + [("LED_A%d" % (i + 1), 1.0, [(x, 11.42), (x, 5.08)])
     for i, x in enumerate([53.34, 58.42, 66.04, 71.12, 76.2, 81.28])]
# GND perimeter ring: runs between the edge connectors and the board edge (nothing crosses it),
# detouring inward around the four M3 holes. The pour ties into it everywhere.
HAND_ROUTES += [
    ("GND", 1.5, [(9.0, 2.0), (91.0, 2.0)]),
    ("GND", 0.8, [(9.0, 2.0), (9.0, 9.0), (2.0, 9.0), (2.0, 66.2), (9.0, 66.2), (9.0, 73.4), (91.5, 73.4),
                  (91.5, 66.5), (98.2, 66.5), (98.2, 20.5)]),
    ("GND", 1.5, [(88.0, 12.7), (85.3, 10.0), (85.3, 2.0)]),     # battery P- into the ring
    # modem ground: J2 GND pins to the ring and into the level shifter's underside channel
    ("GND", 1.5, [(2.0, 44.45), (7.62, 44.45), (7.62, 46.99)]),
    ("GND", 0.8, [(7.62, 44.45), (9.4, 44.45), (11.35, 42.5), (26.1, 42.5), (26.1, 49.53), (24.13, 49.53)]),
    # modem-enable driver ground riser (runs under the top-side VBAT bus wire)
    ("GND", 0.8, [(30.1, 2.0), (30.1, 20.32)]),
    # solar terminal ground into the right edge of the ring
    ("GND", 1.5, [(95.25, 38.1), (98.2, 38.1)]),
]
# VBAT bus wire on the TOP side (J-W1): one straight 1.0 mm tinned copper wire, 16 x 2.54 mm long,
# soldered at 5 points. It carries VBAT to the LDO, the modem switch Q1 and the siren switch Q6 and
# leaves the bottom copper underneath free for GND and signals.
HAND_JUMPERS = [
    ("VBAT", [(50.8, 16.5), (45.72, 16.5), (27.94, 16.5), (17.78, 16.5), (10.16, 16.5)]),
]


def R():
    return F.resistor()


def build():
    b = Board(BOARD_W, BOARD_H, corner=2.0)
    A = b.add

    # ------------------------------------------------------------------ MCU
    A(Component("U1", F.pro_mini(), 40.64, 40.64, 0, value="Pro Mini 3V3/8MHz",
                part="Arduino Pro Mini 328 3,3 V / 8 MHz", package="Modül, 2×12 + 4 pin",
                nets={"D9": "D9_SIREN", "D8": "D8_TX", "D7": "D7_RX", "D6": "D6_STROBE",
                      "D5": "D5_DTR", "D4": "D4_PWRKEY", "D3": "D3_RI", "D2": "TAMPER_N",
                      "GND": "GND", "GND2": "GND", "VCC": "+3V3",
                      "D10": "D10_MODEM_EN", "D11": "D11_SNS_N", "D12": "D12_LED", "D13": "D13_CHG_INH",
                      "A0": "A0_VBAT", "A1": "A1_SOLAR", "A2": "A2_TEST", "A3": "A3_CHG",
                      "A4": "SDA", "A5": "SCL", "A7": "A7_NTC"}))

    # ------------------------------------------------------------------ modem block (left)
    # Level shifter: module channel order chosen so that all four HV runs to the Pro Mini are
    # straight (no crossings). The four signal pairs are exactly SPEC 4.3.
    A(Component("U3", F.level_shifter(), 22.86, 58.42, 270, value="BSS138 x4",
                part="4 kanal BSS138 çift yönlü seviye çevirici", package="Modül 2×6 (0,4\")",
                nets={"HV1": "D3_RI", "HV2": "D5_DTR", "HV": "+3V3", "GNDH": "GND",
                      "HV3": "D7_RX", "HV4": "D8_TX",
                      "LV1": "M_RI", "LV2": "M_DTR", "LV": "VDD_EXT", "GNDL": "GND",
                      "LV3": "M_TXD", "LV4": "M_RXD"}))
    j2lab = ["VMOD", "VEXT", "GND", "GND", "RXD", "TXD", "DTR", "RI", "PWRK"]
    A(Component("J2", F.header(9, j2lab), 7.62, 39.37, 90, value="A7670E",
                part="Pin header 1×9 erkek (A7670E kablosu)", package="2,54 mm",
                nets={"1": "VMODEM", "2": "VDD_EXT", "3": "GND", "4": "GND", "5": "M_RXD",
                      "6": "M_TXD", "7": "M_DTR", "8": "M_RI", "9": "M_PWRKEY"}))
    A(Component("C10", F.cap_elec(2.5, 6.3), 8.0, 34.0, 0, value="470µ 6V3",
                part="470 µF 6,3 V düşük ESR radyal (Ø6,3 mm)", package="Ø6,3 mm, 2,5 mm",
                nets={"+": "VMODEM", "-": "GND"}))
    A(Component("C11", F.cap_elec(2.5, 6.3), 14.8, 34.0, 0, value="470µ 6V3",
                part="470 µF 6,3 V düşük ESR radyal (Ø6,3 mm)", package="Ø6,3 mm, 2,5 mm",
                nets={"+": "VMODEM", "-": "GND"}))
    A(Component("C12", F.cap_ceramic(), 4.0, 35.5, 90, value="100n",
                part="100 nF seramik", package="5,08 mm", nets={"1": "GND", "2": "VMODEM"}))
    A(Component("Q1", F.sot23(), 24.0, 18.5, 90, side="bottom", value="AO3401A",
                part="AO3401A P-MOSFET (ALT YÜZ, SMD)", package="SOT-23",
                nets={"G": "Q1_G", "S": "VBAT", "D": "VMODEM"}))
    A(Component("R1", R(), 26.0, 11.0, 90, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "VBAT", "2": "Q1_G"}))
    A(Component("Q5", F.to92(["E", "B", "C"], "TO92_2N3904"), 28.8, 20.32, 90, value="2N3904",
                part="2N3904 NPN", package="TO-92", nets={"E": "GND", "B": "Q5_B", "C": "Q1_G"}))
    A(Component("R2", R(), 33.6, 22.86, 90, value="10k", part="10 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q5_B", "2": "D10_MODEM_EN"}))
    A(Component("R3", F.resistor_standing(), 31.4, 22.86, 270, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel, dik montaj 2,54", nets={"1": "Q5_B", "2": "GND"}))
    A(Component("Q4", F.to92(["E", "B", "C"], "TO92_2N3904"), 10.5, 64.5, 0, value="2N3904",
                part="2N3904 NPN", package="TO-92", nets={"E": "GND", "B": "Q4_B", "C": "M_PWRKEY"}))
    A(Component("R4", R(), 11.0, 71.5, 0, value="4k7", part="4,7 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q4_B", "2": "D4_PWRKEY"}))
    A(Component("R5", R(), 11.0, 68.2, 0, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q4_B", "2": "GND"}))

    # ------------------------------------------------------------------ tamper (D2), top-left
    A(Component("J8", F.terminal(2, ["TMP", "GND"]), 37.5, 70.6, 180, value="KAPAK REED (NC)",
                part="Klemens 2p 5,08 mm (kapak reed, NC/Form-B)", package="5,08 mm",
                nets={"1": "TAMPER_N", "2": "GND"}))
    A(Component("R24", R(), 11.0, 60.8, 0, value="1M", part="1 MΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "+3V3", "2": "TAMPER_N"}))
    A(Component("C13", F.cap_ceramic(), 31.0, 62.5, 0, value="100n", part="100 nF seramik",
                package="5,08 mm", nets={"1": "GND", "2": "TAMPER_N"}))

    # ------------------------------------------------------------------ siren (D9), bottom-left
    A(Component("J7", F.terminal(2, ["+12V", "GND"]), 13.97, 5.08, 0, value="SİREN",
                part="Klemens 2p 5,08 mm", package="5,08 mm",
                nets={"1": "SIREN_P", "2": "GND"}))
    A(Component("U7", F.wirepads(["VIN+", "VIN-", "OUT+", "OUT-"]), 5.5, 11.8, 0, value="MT3608 12V",
                part="MT3608 boost modülü (12 V'a ayarlı)", package="Modül, 4 kablo",
                nets={"VIN+": "SIR_VIN", "VIN-": "GND", "OUT+": "SIREN_P", "OUT-": "GND"}))
    A(Component("Q6", F.sot23(), 8.35, 18.5, 90, side="bottom", value="AO3401A",
                part="AO3401A P-MOSFET (ALT YÜZ, SMD)", package="SOT-23",
                nets={"G": "Q6_G", "S": "VBAT", "D": "SIR_VIN"}))
    A(Component("R14", R(), 15.0, 25.5, 270, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q6_G", "2": "VBAT"}))
    A(Component("Q7", F.to92(["E", "B", "C"], "TO92_2N3904"), 4.0, 23.5, 0, value="2N3904",
                part="2N3904 NPN", package="TO-92", nets={"E": "GND", "B": "Q7_B", "C": "Q6_G"}))
    A(Component("R15", R(), 14.0, 29.5, 0, value="10k", part="10 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q7_B", "2": "D9_SIREN"}))
    A(Component("R16", R(), 3.0, 27.0, 0, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "GND", "2": "Q7_B"}))

    # ------------------------------------------------------------------ strobe (D6), bottom
    A(Component("Q3", F.to220v(), 38.6, 12.0, 0, value="IRLZ44N",
                part="IRLZ44N N-MOSFET mantık seviyeli", package="TO-220 dik",
                nets={"G": "Q3_G", "D": "LED_K", "S": "GND"}))
    A(Component("R6", R(), 34.5, 10.0, 90, value="100R", part="100 Ω 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q3_G", "2": "D6_STROBE"}))
    A(Component("R7", R(), 33.0, 2.8, 90, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "GND", "2": "Q3_G"}))
    xs = [53.34, 58.42, 66.04, 71.12, 76.2, 81.28]
    for i, x in enumerate(xs):
        A(Component("R%d" % (8 + i), F.resistor_1w_vertical(), x, 16.5, 270, value="4R7 1W",
                    part="4,7 Ω 1 W", package="Eksenel, dik montaj 5,08",
                    nets={"1": "VBAT", "2": "LED_A%d" % (i + 1)}))
    A(Component("J5", F.terminal(4, ["K", "K", "A1", "A2"]), 43.18, 5.08, 0, value="LED HALKA",
                part="Klemens 4p 5,08 mm", package="5,08 mm",
                nets={"1": "LED_K", "2": "LED_K", "3": "LED_A1", "4": "LED_A2"}))
    A(Component("J6", F.terminal(4, ["A3", "A4", "A5", "A6"]), 66.04, 5.08, 0, value="LED HALKA",
                part="Klemens 4p 5,08 mm", package="5,08 mm",
                nets={"1": "LED_A3", "2": "LED_A4", "3": "LED_A5", "4": "LED_A6"}))

    # ------------------------------------------------------------------ 3V3 LDO + NTC (A7), below U1
    A(Component("U6", F.to92(["GND", "VIN", "VOUT"], "TO92_MCP1700"), 44.5, 20.6, 0,
                value="MCP1700-3302E", part="MCP1700-3302E/TO LDO 3,3 V", package="TO-92",
                nets={"GND": "GND", "VIN": "VBAT", "VOUT": "+3V3"}))
    A(Component("C5", F.cap_ceramic(), 41.0, 23.5, 270, value="1µ", part="1 µF seramik (X7R)",
                package="5,08 mm", nets={"1": "GND", "2": "VBAT"}))
    A(Component("C6", F.cap_ceramic(), 52.0, 19.0, 90, value="10µ", part="10 µF seramik (X5R/X7R)",
                package="5,08 mm", nets={"1": "+3V3", "2": "GND"}))
    A(Component("R26", R(), 59.5, 37.6, 0, value="220k", part="220 kΩ %1 1/4 W",
                package="Eksenel 10,16", nets={"1": "A7_NTC", "2": "+3V3"}))
    A(Component("C14", F.cap_ceramic(), 63.0, 40.6, 0, value="100n", part="100 nF seramik",
                package="5,08 mm", nets={"1": "A7_NTC", "2": "GND"}))
    A(Component("J10", F.header(2, ["NTC", "GND"]), 71.0, 40.6, 0, value="NTC 10k",
                part="Pin header 1×2 (NTC 10k B3950 kablosu)", package="2,54 mm",
                nets={"1": "A7_NTC", "2": "GND"}))
    A(Component("SW1", F.sw18010p(), 24.0, 60.1, 0, value="SW-18010P",
                part="SW-18010P titreşim anahtarı", package="THT 2 bacak",
                nets={"1": "TAMPER_N", "2": "GND"}))

    # ------------------------------------------------------------------ power input (right / bottom-right)
    A(Component("J3", F.terminal(2, ["B-", "B+"]), 95.25, 12.7, 90, value="PİL 1S2P",
                part="Klemens 2p 5,08 mm", package="5,08 mm", nets={"1": "CELL_N", "2": "PACK_P"}))
    A(Component("U5", F.wirepads(["B+", "P-", "B-"]), 88.0, 16.51, 270, value="1S KORUMA",
                part="1S Li-ion koruma modülü (DW01A+FS8205A), P+ = B+", package="Modül, 3 kablo",
                nets={"B-": "CELL_N", "B+": "PACK_P", "P-": "GND"}))
    A(Component("F1", F.ptc(), 91.5, 23.0, 180, value="PTC 3A",
                part="PTC sigorta 3 A tutma (RXEF300)", package="Radyal 5,08",
                nets={"1": "PACK_P", "2": "VBAT"}))
    A(Component("J1", F.terminal(2, ["-", "SOL+"]), 95.25, 38.1, 90, value="GÜNEŞ 6V",
                part="Klemens 2p 5,08 mm", package="5,08 mm", nets={"1": "GND", "2": "SOL_IN"}))
    A(Component("D1", F.diode(15.24, drill=F.HOLE_BIG, pad=3.0, body=9.5, dia=5.0), 88.0, 48.5, 270,
                value="1N5822", part="1N5822 Schottky 3 A 40 V", package="DO-201AD",
                nets={"A": "SOL_IN", "K": "SOL_P"}))
    A(Component("TVS1", F.diode(12.7, drill=F.HOLE_PIN, pad=2.0, body=7.5, dia=3.6), 84.5, 45.96, 270,
                value="P6KE8.2A", part="P6KE8.2A TVS 600 W (Vrwm 7,02 V)", package="DO-15",
                nets={"A": "GND", "K": "SOL_P"}))
    A(Component("C1", F.cap_elec(2.54, 5.0), 79.0, 37.5, 90, value="10µ 25V",
                part="10 µF 25 V elektrolitik", package="Ø5 mm", nets={"+": "SOL_P", "-": "GND"}))
    A(Component("C2", F.cap_ceramic(), 83.5, 37.0, 90, value="100n", part="100 nF seramik",
                package="5,08 mm", nets={"1": "GND", "2": "SOL_P"}))
    A(Component("U4", F.wirepads(["IN+", "IN-", "BAT-", "BAT+"]), 80.07, 29.0, 0,
                value="CN3791 MPPT", part="CN3791 6 V MPPT şarj modülü", package="Modül, 5 kablo",
                nets={"IN+": "SOL_P", "IN-": "GND", "BAT+": "PACK_P", "BAT-": "GND"}))
    A(Component("TP2", F.testpoint("CHRG"), 73.0, 66.5, 0, value="",
                part="Kablo noktası → CN3791 modülü CHRG (kırmızı LED katodu)", package="Ø1,2 delik",
                nets={"1": "CHRG_K"}, show_value=False))
    A(Component("D2", F.diode(7.62), 61.5, 66.5, 0, value="BAT85",
                part="BAT85 Schottky sinyal diyodu", package="DO-35",
                nets={"A": "A3_CHG", "K": "CHRG_K"}))

    # ------------------------------------------------------------------ dividers etc. (right of U1)
    A(Component("R19", R(), 61.5, 58.2, 0, value="1M", part="1 MΩ %1 1/4 W",
                package="Eksenel 10,16", nets={"1": "A1_SOLAR", "2": "SOL_P"}))
    A(Component("R20", R(), 61.5, 60.8, 0, value="150k", part="150 kΩ %1 1/4 W",
                package="Eksenel 10,16", nets={"1": "A1_SOLAR", "2": "GND"}))
    A(Component("C4", F.cap_ceramic(), 78.5, 58.5, 90, value="100n", part="100 nF seramik",
                package="5,08 mm", nets={"1": "GND", "2": "A1_SOLAR"}))
    A(Component("R17", R(), 61.5, 53.0, 0, value="1M", part="1 MΩ %1 1/4 W",
                package="Eksenel 10,16", nets={"1": "A0_VBAT", "2": "VBAT"}))
    A(Component("R18", R(), 61.5, 55.6, 0, value="330k", part="330 kΩ %1 1/4 W",
                package="Eksenel 10,16", nets={"1": "A0_VBAT", "2": "GND"}))
    A(Component("C3", F.cap_ceramic(), 75.5, 52.5, 90, value="100n", part="100 nF seramik",
                package="5,08 mm", nets={"1": "GND", "2": "A0_VBAT"}))

    # ------------------------------------------------------------------ sensor rail (D11, A4, A5), top-right
    A(Component("Q2", F.sot23(), 58.6, 27.4, 0, side="bottom", value="AO3401A",
                part="AO3401A P-MOSFET (ALT YÜZ, SMD)", package="SOT-23",
                nets={"G": "D11_SNS_N", "S": "+3V3", "D": "V_SNS"}))
    A(Component("R21", F.resistor_standing(), 57.65, 22.4, 0, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel, dik montaj 2,54", nets={"1": "+3V3", "2": "D11_SNS_N"}))
    A(Component("C8", F.cap_ceramic(2.54), 61.8, 27.14, 270, value="10µ", part="10 µF seramik",
                package="2,54 mm", nets={"1": "GND", "2": "V_SNS"}))
    A(Component("C9", F.cap_ceramic(2.54), 64.4, 27.14, 270, value="100n", part="100 nF seramik",
                package="2,54 mm", nets={"1": "GND", "2": "V_SNS"}))
    A(Component("R22", F.resistor_standing(), 54.58, 31.0, 270, value="4k7", part="4,7 kΩ 1/4 W",
                package="Eksenel, dik montaj 2,54", nets={"1": "SDA", "2": "V_SNS"}))
    A(Component("R23", F.resistor_standing(), 52.04, 31.0, 270, value="4k7", part="4,7 kΩ 1/4 W",
                package="Eksenel, dik montaj 2,54", nets={"1": "SCL", "2": "V_SNS"}))
    A(Component("J4", F.header(4, ["VSNS", "SCL", "SDA", "GND"]), 49.5, 34.0, 0, value="SENSÖR",
                part="Pin header 1×4 (AMG8833 + BME680 kablosu)", package="2,54 mm",
                nets={"1": "V_SNS", "2": "SCL", "3": "SDA", "4": "GND"}))

    # ------------------------------------------------------------------ misc I/O (right)
    A(Component("J9", F.terminal(2, ["TEST", "GND"]), 95.25, 61.0, 90, value="TEST REED",
                part="Klemens 2p 5,08 mm (test reed)", package="5,08 mm",
                nets={"1": "A2_TEST", "2": "GND"}))
    A(Component("R25", R(), 61.5, 47.0, 0, value="1k", part="1 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "D12_LED", "2": "LED_ST"}))
    A(Component("LED1", F.led3(), 73.6, 47.0, 0, value="YEŞİL", part="3 mm yeşil LED",
                package="3 mm", nets={"A": "LED_ST", "K": "GND"}))
    # charge inhibit on D13 (spec update)
    A(Component("Q8", F.to92(["S", "G", "D"], "TO92_2N7000"), 75.0, 50.0, 0, value="2N7000",
                part="2N7000 N-MOSFET", package="TO-92",
                nets={"S": "GND", "G": "Q8_G", "D": "MPPT_INH"}))
    A(Component("R27", R(), 71.66, 50.0, 180, value="100R", part="100 Ω 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q8_G", "2": "D13_CHG_INH"}))
    A(Component("R28", R(), 81.5, 47.6, 90, value="100k", part="100 kΩ 1/4 W",
                package="Eksenel 10,16", nets={"1": "Q8_G", "2": "GND"}))
    A(Component("TP1", F.testpoint("MPPT"), 85.5, 60.0, 0, value="",
                part="Kablo noktası → CN3791 MPPT bölücü düğümü", package="Ø1,2 delik",
                nets={"1": "MPPT_INH"}, show_value=False))

    # ------------------------------------------------------------------ mounting
    for i, (x, y) in enumerate(MOUNT_HOLES):
        A(Component("H%d" % (i + 1), F.mount_hole(), x, y, 0, value="M3", part="M3 montaj deliği",
                    package="Ø3,2 NPTH", show_value=False))

    # copper text on the bottom layer: reads correctly on the toner-transfer print and when the
    # board is viewed from the top through the FR4 (mirrored when looking at the copper side)
    b.copper_texts.append(("ON1-DIY ALT", 80.0, 70.2, 1.6, "cm", 0))
    # top silkscreen title block
    b.silk_texts.append(("ORMAN NÖBETÇİSİ ON-1", 80.5, 73.1, 1.3, "cm", 0))
    b.silk_texts.append(("ON1-DIY Rev A  2026-11", 80.5, 71.2, 1.0, "cm", 0))
    b.silk_texts.append(("tek yüz, bakır altta", 80.5, 69.6, 0.9, "cm", 0))
    b.net_class = dict(NET_WIDTH)
    return b


def pad_width(b, ref, pad, net):
    """Track width used when connecting this pad to its net."""
    if net == "GND":
        return W_PWR if (ref, pad) in GND_POWER else W_SIG
    if ref in SMALL_TAP_REFS and net in ("VBAT", "SOL_P"):
        return W_SIG
    return b.net_class.get(net, W_SIG)
