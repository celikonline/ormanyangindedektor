"""Footprint library for ON1-DIY (single-sided, home-made friendly).

Local coordinates in mm, Y up, as seen from the TOP (component side).
Copper is on the bottom layer only. THT pads go through; SMD pads (SOT-23)
are soldered on the copper (bottom) side, so those footprints are placed with
side='bottom' which mirrors them in X.

Pad: shape 'C' circle (w = diameter), 'O' obround (w x h), 'R' rectangle (w x h).
"""
import math

HOLE_SMALL = 0.8     # passives, TO-92, LED, DO-35
HOLE_PIN = 1.0       # 2.54 mm header pins
HOLE_MED = 1.2       # TO-220, wire pads, PTC
HOLE_TERM = 1.3      # 5.08 mm screw terminals
HOLE_BIG = 1.5       # 1N5822 (1.3 mm leads)
HOLE_MOUNT = 3.2     # M3


class Pad:
    def __init__(self, name, x, y, shape="C", w=1.8, h=None, drill=HOLE_SMALL, label=None):
        self.name = name
        self.x, self.y = x, y
        self.shape = shape
        self.w = w
        self.h = h if h is not None else w
        self.drill = drill          # None = SMD
        self.label = label


class Footprint:
    def __init__(self, name):
        self.name = name
        self.pads = []
        self.silk = []          # polylines (local)
        self.silk_dashed = []   # polylines drawn dashed (bottom-side parts)
        self.texts = []         # (text, x, y, h, anchor, rot)
        self.court = None       # (x0, y0, x1, y1) local
        self.raised = False     # sits on headers -> wire jumpers may pass underneath
        self.low_profile_ok = False  # small part on legs: a flat wire jumper may pass under its body
        self.internal = []      # groups of pad names connected inside the module
        self.npth = []          # (x, y, d) non-plated holes
        self.ref_pos = (0, 0, 0)   # x, y, rot for reference designator
        self.val_pos = None
        self.keepout = []       # (x, y, r) copper keep-out circles

    def pad(self, *a, **k):
        p = Pad(*a, **k)
        self.pads.append(p)
        return p

    def rect(self, x0, y0, x1, y1):
        self.silk.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])

    def circle(self, cx, cy, r, n=36, a0=0, a1=360):
        pts = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.silk.append(pts)

    def line(self, *pts):
        self.silk.append(list(pts))


# ---------------------------------------------------------------- modules
def pro_mini():
    """Arduino Pro Mini 3V3/8MHz (SparkFun DEV-11114 geometry, Eagle file v14).

    Origin = module bottom-left corner, FTDI header edge at the top (y = 33.02).
    Left row (x=1.27) bottom->top : D9 D8 D7 D6 D5 D4 D3 D2 GND RST RXI TXO
    Right row (x=16.51) bottom->top: D10 D11 D12 D13 A0 A1 A2 A3 VCC RST GND RAW
    Inner pins: A4 (13.589,17.907) A5 (13.589,20.447) A6 (13.589,7.493) A7 (13.589,10.033)
    """
    f = Footprint("ProMini")
    left = ["D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RST", "RXI", "TXO"]
    right = ["D10", "D11", "D12", "D13", "A0", "A1", "A2", "A3", "VCC", "RST2", "GND2", "RAW"]
    for i, n in enumerate(left):
        f.pad(n, 1.27, 1.27 + 2.54 * i, "C", 1.8, drill=HOLE_PIN)
    for i, n in enumerate(right):
        f.pad(n, 16.51, 1.27 + 2.54 * i, "C", 1.8, drill=HOLE_PIN)
    f.pad("A4", 13.589, 17.907, "C", 1.8, drill=HOLE_PIN)
    f.pad("A5", 13.589, 20.447, "C", 1.8, drill=HOLE_PIN)
    f.pad("A6", 13.589, 7.493, "C", 1.8, drill=HOLE_PIN)
    f.pad("A7", 13.589, 10.033, "C", 1.8, drill=HOLE_PIN)
    f.rect(-0.2, -0.2, 17.98, 33.22)
    f.line((3.5, 33.22), (3.5, 31.2), (14.3, 31.2), (14.3, 33.22))
    f.texts.append(("FTDI", 8.89, 32.2, 0.9, "cm", 0))
    for i, n in enumerate(left):
        f.texts.append((n, 2.6, 1.27 + 2.54 * i, 0.8, "lm", 0))
    for i, n in enumerate(right):
        f.texts.append((n.replace("2", "") if n in ("RST2", "GND2") else n, 15.2, 1.27 + 2.54 * i, 0.8, "rm", 0))
    for n, y in (("A4", 17.907), ("A5", 20.447), ("A6", 7.493), ("A7", 10.033)):
        f.texts.append((n, 12.3, y, 0.8, "rm", 0))
    f.court = (-0.3, -0.3, 18.08, 33.32)
    f.raised = True
    f.internal = [["GND", "GND2"], ["RST", "RST2"]]
    f.ref_pos = (8.89, 26.5, 0)
    f.val_pos = (8.89, 24.6, 0)
    return f


def level_shifter():
    """4-ch BSS138 bidirectional level shifter (SparkFun BOB-12009 geometry).

    Origin bottom-left. LV row y=1.27: LV1 LV2 LV GND LV3 LV4 ; HV row y=11.43: HV1 HV2 HV GND HV3 HV4
    (row spacing 0.4" = 10.16 mm, board 15.24 x 12.7 mm)
    """
    f = Footprint("BSS138x4")
    lv = ["LV1", "LV2", "LV", "GNDL", "LV3", "LV4"]
    hv = ["HV1", "HV2", "HV", "GNDH", "HV3", "HV4"]
    for i, n in enumerate(lv):
        f.pad(n, 1.27 + 2.54 * i, 1.27, "C", 1.8, drill=HOLE_PIN)
    for i, n in enumerate(hv):
        f.pad(n, 1.27 + 2.54 * i, 11.43, "C", 1.8, drill=HOLE_PIN)
    f.rect(-0.2, -0.2, 15.44, 12.9)
    for i, n in enumerate(["1", "2", "LV", "G", "3", "4"]):
        f.texts.append((n, 1.27 + 2.54 * i, 3.0, 0.8, "cm", 0))
    for i, n in enumerate(["1", "2", "HV", "G", "3", "4"]):
        f.texts.append((n, 1.27 + 2.54 * i, 9.7, 0.8, "cm", 0))
    f.court = (-0.3, -0.3, 15.54, 13.0)
    f.raised = True
    f.internal = [["GNDL", "GNDH"]]
    f.ref_pos = (7.62, 6.35, 0)
    return f


def header(n, labels=None, pitch=2.54):
    f = Footprint("PinHeader_1x%d" % n)
    for i in range(n):
        f.pad(str(i + 1), pitch * i, 0, "R" if i == 0 else "C", 1.8, drill=HOLE_PIN,
              label=(labels[i] if labels else None))
    f.rect(-1.4, -1.4, pitch * (n - 1) + 1.4, 1.4)
    if labels:
        for i, l in enumerate(labels):
            f.texts.append((l, pitch * i, 2.0, 0.9, "lm", 90))
    f.court = (-1.5, -1.5, pitch * (n - 1) + 1.5, 1.5)
    f.ref_pos = (-2.4, 0, 90)
    return f


def wirepads(labels, pitch=3.81, title=None):
    """Solder points for wiring an off-the-shelf module (or a glued-on module)."""
    f = Footprint("WirePads_%d" % len(labels))
    for i, l in enumerate(labels):
        f.pad(l, pitch * i, 0, "C", 2.5, drill=HOLE_MED, label=l)
        f.texts.append((l, pitch * i, -2.2, 0.9, "ct", 0))
    w = pitch * (len(labels) - 1)
    f.line((-1.9, 1.9), (w + 1.9, 1.9))
    f.court = (-1.9, -3.6, w + 1.9, 1.9)
    f.ref_pos = (w / 2, 3.0, 0)
    return f


def terminal(n, labels=None):
    """5.08 mm PCB screw terminal (KF301/DG301 style). Wire entry towards -Y."""
    f = Footprint("Terminal_5.08_%dp" % n)
    for i in range(n):
        f.pad(str(i + 1), 5.08 * i, 0, "O", 2.6, 3.2, drill=HOLE_TERM,
              label=(labels[i] if labels else None))
    x1 = 5.08 * (n - 1) + 2.54
    f.rect(-2.54, -3.6, x1, 4.0)
    f.line((-2.54, -2.6), (x1, -2.6))          # wire entry side
    if labels:
        for i, l in enumerate(labels):
            f.texts.append((l, 5.08 * i, 2.9, 1.0, "cm", 0))
    f.court = (-2.6, -3.7, x1 + 0.06, 4.1)
    f.ref_pos = (-3.6, 0.2, 90)
    return f


# ---------------------------------------------------------------- passives
def resistor(pitch=10.16, body=6.4, dia=2.5, drill=HOLE_SMALL, pad=1.8):
    f = Footprint("R_Axial_%.2f" % pitch)
    f.pad("1", 0, 0, "C", pad, drill=drill)
    f.pad("2", pitch, 0, "C", pad, drill=drill)
    x0 = (pitch - body) / 2
    f.rect(x0, -dia / 2, x0 + body, dia / 2)
    f.line((pad / 2 + 0.25, 0), (x0, 0))
    f.line((x0 + body, 0), (pitch - pad / 2 - 0.25, 0))
    f.court = (-pad / 2 - 0.1, -dia / 2 - 0.1, pitch + pad / 2 + 0.1, dia / 2 + 0.1)
    f.ref_pos = (pitch / 2, 0, 0)
    f.ref_inside = True
    f.low_profile_ok = True
    return f


def resistor_1w():
    return resistor(pitch=15.24, body=10.0, dia=4.0, drill=HOLE_PIN, pad=2.2)


def cap_ceramic(pitch=5.08):
    f = Footprint("C_Disc_%.2f" % pitch)
    f.pad("1", 0, 0, "C", 1.8, drill=HOLE_SMALL)
    f.pad("2", pitch, 0, "C", 1.8, drill=HOLE_SMALL)
    f.rect(-1.3, -1.3, pitch + 1.3, 1.3)
    f.court = (-1.4, -1.4, pitch + 1.4, 1.4)
    f.ref_pos = (pitch / 2, 2.1, 0)
    f.low_profile_ok = True
    return f


def cap_elec(pitch, dia, drill=HOLE_SMALL, pad=1.8):
    """Radial electrolytic, pad 1 = '+' (square)."""
    f = Footprint("CP_Radial_D%.1f_P%.2f" % (dia, pitch))
    f.pad("+", 0, 0, "R", pad, drill=drill)
    f.pad("-", pitch, 0, "C", pad, drill=drill)
    cx = pitch / 2
    f.circle(cx, 0, dia / 2, n=48)
    f.texts.append(("+", -pad / 2 - 0.9, dia / 2 - 1.2 if dia > 6 else 1.6, 1.3, "cm", 0))
    # shaded '-' side band
    r = dia / 2
    xb = cx + r * 0.62
    f.line((xb, -r * 0.78), (xb, r * 0.78))
    f.court = (cx - r - 0.2, -r - 0.2, cx + r + 0.2, r + 0.2)
    f.ref_pos = (cx, r + 1.0, 0)
    return f


def to92(names, title="TO92"):
    """TO-92 with legs spread to 2.54 mm (hand solderable). Flat face towards -Y.
    names: pin names left->right looking at the flat face."""
    f = Footprint(title)
    for i, n in enumerate(names):
        f.pad(n, 2.54 * i, 0, "R" if i == 0 else "C", 1.8, drill=HOLE_SMALL)
    f.line((-0.2, -1.55), (5.28, -1.55))
    f.circle(2.54, -0.6, 2.75, n=30, a0=-20, a1=200)
    f.court = (-1.0, -1.7, 6.1, 2.3)
    f.ref_pos = (2.54, -2.6, 0)
    f.low_profile_ok = True
    return f


def to220v(names=("G", "D", "S")):
    f = Footprint("TO220_Vertical")
    for i, n in enumerate(names):
        f.pad(n, 2.54 * i, 0, "O", 1.8, 2.8, drill=HOLE_MED)
    f.rect(-2.54, -1.9, 7.62, 2.7)
    f.line((-2.54, 1.6), (7.62, 1.6))          # metal tab side (+Y)
    f.court = (-2.64, -2.0, 7.72, 2.8)
    f.ref_pos = (2.54, -2.9, 0)
    return f


def sot23(names=("G", "S", "D")):
    """SOT-23 with enlarged hand-solder pads. Defined as seen from the part's own
    top; place with side='bottom' (mounted on the copper side)."""
    f = Footprint("SOT23_HandSolder")
    f.pad(names[0], -0.95, -1.25, "R", 1.0, 1.5, drill=None)
    f.pad(names[1], 0.95, -1.25, "R", 1.0, 1.5, drill=None)
    f.pad(names[2], 0.0, 1.25, "R", 1.0, 1.5, drill=None)
    f.silk_dashed.append([(-1.9, -2.3), (1.9, -2.3), (1.9, 2.3), (-1.9, 2.3), (-1.9, -2.3)])
    f.court = (-1.6, -2.1, 1.6, 2.1)
    f.ref_pos = (0, 3.1, 0)
    f.smd = True
    return f


def diode(pitch, drill=HOLE_SMALL, pad=1.8, body=4.0, dia=2.0):
    """Axial diode: pad 'A' at 0, 'K' at pitch, band on K side."""
    f = Footprint("D_Axial_%.2f" % pitch)
    f.pad("A", 0, 0, "C", pad, drill=drill)
    f.pad("K", pitch, 0, "R", pad, drill=drill)
    x0 = (pitch - body) / 2
    f.rect(x0, -dia / 2, x0 + body, dia / 2)
    xb = x0 + body * 0.78
    f.line((xb, -dia / 2), (xb, dia / 2))
    f.line((xb + 0.25, -dia / 2), (xb + 0.25, dia / 2))
    f.line((pad / 2 + 0.25, 0), (x0, 0))
    f.line((x0 + body, 0), (pitch - pad / 2 - 0.25, 0))
    f.court = (-pad / 2 - 0.1, -dia / 2 - 0.1, pitch + pad / 2 + 0.1, dia / 2 + 0.1)
    f.ref_pos = (pitch / 2, dia / 2 + 1.0, 0)
    f.low_profile_ok = True
    return f


def led3():
    f = Footprint("LED_3mm")
    f.pad("A", 0, 0, "C", 1.8, drill=HOLE_SMALL)
    f.pad("K", 2.54, 0, "R", 1.8, drill=HOLE_SMALL)
    f.circle(1.27, 0, 2.0, n=40, a0=-60, a1=240)
    x = 1.27 + 2.0 * math.cos(math.radians(60))
    f.line((x, -1.73), (x, 1.73))              # flat = cathode
    f.court = (-1.0, -2.2, 3.6, 2.2)
    f.ref_pos = (1.27, 3.0, 0)
    f.low_profile_ok = True
    return f


def ptc():
    f = Footprint("PTC_Radial_5.08")
    f.pad("1", 0, 0, "C", 2.0, drill=HOLE_PIN)
    f.pad("2", 5.08, 0, "C", 2.0, drill=HOLE_PIN)
    f.rect(-1.9, -1.6, 6.98, 1.6)
    f.court = (-2.0, -1.7, 7.08, 1.7)
    f.ref_pos = (2.54, 2.4, 0)
    f.low_profile_ok = True
    return f


def sw18010p():
    """SW-18010P vibration switch, lying flat, both leads at one end (2.54 mm)."""
    f = Footprint("SW18010P")
    f.pad("1", 0, 0, "C", 1.8, drill=HOLE_SMALL)
    f.pad("2", 2.54, 0, "C", 1.8, drill=HOLE_SMALL)
    f.rect(-1.4, 1.3, 3.94, 14.5)
    f.court = (-1.5, -1.0, 4.04, 14.6)
    f.ref_pos = (1.27, 8.0, 90)
    f.low_profile_ok = True
    return f


def testpoint(label):
    f = Footprint("WirePoint")
    f.pad("1", 0, 0, "C", 2.5, drill=HOLE_MED, label=label)
    f.circle(0, 0, 1.75, n=24)
    f.texts.append((label, 0, -2.4, 1.0, "ct", 0))
    f.court = (-1.8, -3.6, 1.8, 1.8)
    f.ref_pos = (0, 2.6, 0)
    return f


def mount_hole():
    f = Footprint("MountingHole_M3")
    f.npth.append((0, 0, HOLE_MOUNT))
    f.circle(0, 0, 3.0, n=40)
    f.keepout.append((0, 0, 3.6))
    f.court = (-3.1, -3.1, 3.1, 3.1)
    return f


def jumper(length):
    f = Footprint("WireJumper_%.2f" % length)
    f.pad("1", 0, 0, "C", 1.8, drill=HOLE_SMALL)
    f.pad("2", length, 0, "C", 1.8, drill=HOLE_SMALL)
    f.line((0.9, 0.35), (length - 0.9, 0.35))
    f.line((0.9, -0.35), (length - 0.9, -0.35))
    f.court = (0, -0.5, length, 0.5)
    f.internal = [["1", "2"]]
    f.ref_pos = (length / 2, 1.2, 0)
    return f


def resistor_1w_vertical():
    """1 W axial resistor standing upright (hairpin), 5.08 mm pad spacing.
    Body sits over pad '1'."""
    f = Footprint("R_Axial_1W_Vertical")
    f.pad("1", 0, 0, "C", 2.2, drill=HOLE_PIN)
    f.pad("2", 5.08, 0, "C", 2.2, drill=HOLE_PIN)
    f.circle(0, 0, 2.3, n=40)
    f.line((2.3, 0), (5.08 - 1.4, 0))
    f.court = (-2.4, -2.4, 6.3, 2.4)
    f.ref_pos = (0, 0, 0)
    f.low_profile_ok = True
    return f


def resistor_standing(pitch=2.54):
    """1/4 W axial resistor standing upright (hairpin) at 2.54 mm. Body over pad '1'."""
    f = Footprint("R_Axial_Standing_%.2f" % pitch)
    f.pad("1", 0, 0, "C", 1.8, drill=HOLE_SMALL)
    f.pad("2", pitch, 0, "C", 1.8, drill=HOLE_SMALL)
    f.circle(0, 0, 1.45, n=32)
    f.court = (-1.55, -1.55, pitch + 1.0, 1.55)
    f.ref_pos = (pitch / 2, 2.3, 0)
    f.low_profile_ok = True
    return f
