# -*- coding: utf-8 -*-
"""
Mechanical drawings for Orman Nöbetçisi ON-1 (SPEC §7).
Outputs (hardware/mechanical/):
  ON1_mechanical_drawing.svg      sheet 1/2  front / right-side / top views, scale 1:2 (A3)
  ON1_drilling_template.svg       sheet 2/2  wall development + bottom + lid hole layout, 1:2 (A3)
  ON1_drilling_template_wall_1to1.svg   full-scale wall template (print 100 %, 520 × 230 mm)
  ON1_drilling_template_discs_1to1.svg  full-scale bottom + lid templates (A3 landscape, 100 %)
All drawing units are millimetres on paper.
"""
import os, math, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import frame_svg, GREEN, ORANGE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "mechanical")
F = "Arial, Helvetica, sans-serif"

# ------------------------------------------------------------------ model data (mm)
R = 76.5            # can outer radius
H_BODY = 166.0      # body height up to lid skirt
H_CAN = 178.0       # overall with lid
R_LID = 78.0
GAP = 15.0          # panel air gap (low edge)
TILT = 30.0
P_W, P_L, P_T = 165.0, 135.0, 3.0
P_PROJ = P_L * math.cos(math.radians(TILT))    # 116.9
P_RISE = P_L * math.sin(math.radians(TILT))    # 67.5
P_Y0 = P_PROJ / 2                               # front edge y
Z_PLOW = H_CAN + GAP                            # 193
Z_PHIGH = Z_PLOW + P_RISE                       # 260.5
SPACER = 10.0
BR_T = 2.0
Y_PLATE = -(R + SPACER)                         # bracket plate front face (toward can)
Z_TAB = 290.0
C = math.pi * 2 * R                             # 480.66

WALL_HOLES = [  # id, label, theta(deg), z, dia, note
    ("H1", "Termal pencere", 0, 125, 30.0, "HDPE 0,4 mm + tel örgü"),
    ("H2", "M12 ePTFE vent", 32, 125, 12.2, "BME680 haznesi"),
    ("H3", "Işık borusu", -32, 125, 3.2, "durum LED’i"),
    ("H4", "Siren", 0, 62, 42.0, "flanş contalı"),
    ("H5", "Siren flanş M3", 18.7, 62, 3.2, "2 adet, ±25 mm yay"),
    ("H5", "Siren flanş M3", -18.7, 62, 3.2, ""),
    ("H6", "Siperlik M3", 15.0, 147, 3.2, "2 adet, ±20 mm yay"),
    ("H6", "Siperlik M3", -15.0, 147, 3.2, ""),
    ("H7", "L braket M5", 180, 60, 5.5, "2 adet, iç takviye pulu"),
    ("H7", "L braket M5", 180, 130, 5.5, ""),
    ("H8", "SMA bulkhead", 218, 150, 6.5, "D-düz 6,0 mm, O-ring"),
    ("H9", "PG7 rakor", 142, 150, 12.5, "panel kablosu"),
]
for th in (0, 120, 240):
    for d in (-6.74, 6.74):
        WALL_HOLES.append(("H10", "Klips perçini", th + d, 158, 3.2, "6 adet (3 klips × 2)" if (th == 0 and d < 0) else ""))

BOTTOM_HOLES = [  # id, label, r, theta, dia
    ("B1", "LED penceresi", 0, 0, 56.0),
    ("B2", "Kubbe flanşı M3", 32, 30, 3.4), ("B2", "", 32, 150, 3.4), ("B2", "", 32, 270, 3.4),
    ("B3", "Labirent drenaj", 55, 90, 6.0),
    ("B4", "M8 ePTFE vent", 55, 270, 8.2),
]
LID_HOLES = [("L1", "Panel braketi M4", x, y, 4.3) for x in (-60, 60) for y in (-40, 40)]


def e(s):
    return html.escape(str(s), quote=False)


class D:
    """Tiny drawing helper in paper mm."""
    def __init__(self):
        self.o = []

    def add(self, s):
        self.o.append(s)

    def line(self, x1, y1, x2, y2, w=0.5, style="vis", color="#000"):
        da = {"vis": "", "thin": "", "hid": ' stroke-dasharray="2.4,1.2"', "ctr": ' stroke-dasharray="7,1.4,1,1.4"',
              "ph": ' stroke-dasharray="9,1.4,1,1.4,1,1.4"'}[style]
        if style in ("thin", "ctr", "ph"):
            w = min(w, 0.25)
        if style == "hid":
            w = 0.35
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{w}"{da} stroke-linecap="round"/>')

    def path(self, d, w=0.5, style="vis", fill="none", color="#000"):
        da = {"vis": "", "thin": "", "hid": ' stroke-dasharray="2.4,1.2"', "ctr": ' stroke-dasharray="7,1.4,1,1.4"',
              "ph": ' stroke-dasharray="9,1.4,1,1.4,1,1.4"'}[style]
        if style in ("thin", "ctr", "ph"):
            w = min(w, 0.25)
        if style == "hid":
            w = 0.35
        self.add(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{w}"{da} stroke-linejoin="round"/>')

    def rect(self, x, y, w, h, lw=0.5, style="vis", fill="none"):
        self.path(f"M{x:.2f},{y:.2f} h{w:.2f} v{h:.2f} h{-w:.2f} Z", lw, style, fill)

    def circle(self, cx, cy, r, lw=0.5, style="vis", fill="none"):
        da = {"vis": "", "thin": "", "hid": ' stroke-dasharray="2.4,1.2"', "ctr": ' stroke-dasharray="7,1.4,1,1.4"', "ph": ""}[style]
        self.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" stroke="#000" stroke-width="{lw}"{da}/>')

    def ellipse(self, cx, cy, rx, ry, lw=0.5, style="vis", fill="none"):
        da = ' stroke-dasharray="2.4,1.2"' if style == "hid" else ""
        self.add(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill}" stroke="#000" stroke-width="{lw}"{da}/>')

    def text(self, x, y, s, size=2.5, anchor="start", weight="normal", color="#000", rot=0, italic=False):
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        it = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{F}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" fill="{color}"{tr}{it}>{e(s)}</text>')

    def arrowhead(self, x, y, ang, L=2.6, Wd=0.9):
        a = math.radians(ang)
        bx, by = x - L * math.cos(a), y - L * math.sin(a)
        px, py = -math.sin(a) * Wd, math.cos(a) * Wd
        self.add(f'<path d="M{x:.2f},{y:.2f} L{bx+px:.2f},{by+py:.2f} L{bx-px:.2f},{by-py:.2f} Z" fill="#000"/>')

    def dim(self, p1, p2, off, txt, orient="h", size=2.6, tshift=0):
        """Linear dimension between p1,p2 (paper). orient h: horizontal dim line at y=p.y+off."""
        (x1, y1), (x2, y2) = p1, p2
        if orient == "h":
            yd = y1 + off if abs(off) > 0 else y1
            yd = (min(y1, y2) if off < 0 else max(y1, y2)) + off
            for (x, y) in (p1, p2):
                s = 1 if yd > y else -1
                self.line(x, y + 0.8 * s, x, yd + 1.5 * s, 0.25, "thin")
            self.line(x1, yd, x2, yd, 0.25, "thin")
            self.arrowhead(x1, yd, 180 if x2 > x1 else 0)
            self.arrowhead(x2, yd, 0 if x2 > x1 else 180)
            self.text((x1 + x2) / 2 + tshift, yd - 0.9, txt, size, "middle")
        else:
            xd = (min(x1, x2) if off < 0 else max(x1, x2)) + off
            for (x, y) in (p1, p2):
                s = 1 if xd > x else -1
                self.line(x + 0.8 * s, y, xd + 1.5 * s, y, 0.25, "thin")
            self.line(xd, y1, xd, y2, 0.25, "thin")
            self.arrowhead(xd, y1, 270 if y2 > y1 else 90)
            self.arrowhead(xd, y2, 90 if y2 > y1 else 270)
            ym = (y1 + y2) / 2 + tshift
            self.text(xd - 0.9, ym, txt, size, "middle", rot=-90)

    def leader(self, x, y, tx, ty, txt, size=2.5, anchor=None, dot=False):
        self.line(x, y, tx, ty, 0.25, "thin")
        if dot:
            self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.6" fill="#000"/>')
        else:
            ang = math.degrees(math.atan2(y - ty, x - tx))
            self.arrowhead(x, y, ang, 2.2, 0.75)
        if anchor is None:
            anchor = "start" if tx >= x else "end"
        sh = 6 if anchor == "start" else -6
        self.line(tx, ty, tx + sh, ty, 0.25, "thin")
        self.text(tx + sh + (0.8 if anchor == "start" else -0.8), ty + 0.9, txt, size, anchor)

    def balloon(self, x, y, bx, by, n, r=2.9):
        ang = math.atan2(y - by, x - bx)
        sx, sy = bx + r * math.cos(ang), by + r * math.sin(ang)
        self.line(sx, sy, x, y, 0.25, "thin")
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.55" fill="#000"/>')
        self.add(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{r}" fill="#fff" stroke="#000" stroke-width="0.35"/>')
        self.text(bx, by + 1.05, str(n), 2.9, "middle", "bold")

    def angle(self, cx, cy, r, a1, a2, txt, size=2.5, tr=None):
        """Arc dimension from angle a1 to a2 (deg, SVG convention, y down)."""
        p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        (x1, y1), (x2, y2) = p(a1), p(a2)
        large = 1 if abs(a2 - a1) > 180 else 0
        sweep = 1 if a2 > a1 else 0
        self.add(f'<path d="M{x1:.2f},{y1:.2f} A{r},{r} 0 {large} {sweep} {x2:.2f},{y2:.2f}" fill="none" stroke="#000" stroke-width="0.25"/>')
        self.arrowhead(x1, y1, a1 - 90 if sweep else a1 + 90, 2.2, 0.75)
        self.arrowhead(x2, y2, a2 + 90 if sweep else a2 - 90, 2.2, 0.75)
        am = math.radians((a1 + a2) / 2)
        rr = tr or r + 3.5
        self.text(cx + rr * math.cos(am), cy + rr * math.sin(am) + 0.9, txt, size, "middle")

    def hatch_rect(self, x, y, w, h, step=1.2):
        cid = f"c{len(self.o)}"
        self.add(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
        g = [f'<g clip-path="url(#{cid})">']
        k = -h
        while k < w:
            g.append(f'<line x1="{x+k:.2f}" y1="{y+h:.2f}" x2="{x+k+h:.2f}" y2="{y:.2f}" stroke="#000" stroke-width="0.18"/>')
            k += step
        g.append("</g>")
        self.add("".join(g))

    def title(self, x, y, s, sub=None):
        self.text(x, y, s, 4.2, "middle", "bold")
        self.line(x - len(s) * 1.25, y + 1.3, x + len(s) * 1.25, y + 1.3, 0.35)
        if sub:
            self.text(x, y + 5.5, sub, 2.8, "middle")


def svg_doc(body, W=420, H=297, extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="{F}">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>{extra_defs}' + "\n".join(body) + "</svg>")


# ------------------------------------------------------------------ sheet 1: views
def sheet_views():
    d = D()
    s = 0.5
    # ---------------- FRONT VIEW ----------------
    FX, FY = 78, 212
    X = lambda x: FX + x * s
    Y = lambda z: FY - z * s
    # can body + lid
    d.rect(X(-R), Y(H_BODY), 2 * R * s, H_BODY * s, 0.6)
    d.rect(X(-R_LID), Y(H_CAN), 2 * R_LID * s, (H_CAN - H_BODY) * s, 0.6)
    d.line(X(-R), Y(3), X(R), Y(3), 0.25, "thin")
    d.line(X(0), Y(-32), X(0), Y(Z_TAB + 40), 0.25, "ctr")
    # dome
    d.rect(X(-38), Y(0), 76 * s, 3 * s, 0.5)
    d.path(f"M{X(-35):.2f},{Y(-3):.2f} A{35*s},{22*s} 0 0 0 {X(35):.2f},{Y(-3):.2f}", 0.6)
    d.path(f"M{X(-25):.2f},{Y(-3):.2f} A{25*s},{15*s} 0 0 0 {X(25):.2f},{Y(-3):.2f}", 0.25, "hid")
    # siren
    d.circle(X(0), Y(62), 28 * s, 0.35)
    d.circle(X(0), Y(62), 21 * s, 0.6)
    for rr in (15, 9, 3):
        d.circle(X(0), Y(62), rr * s, 0.25)
    for sx in (-1, 1):
        d.circle(X(sx * 25), Y(62), 1.6 * s, 0.3)
    # thermal window + mesh + hood
    d.circle(X(0), Y(125), 15 * s, 0.6)
    cid = "win"
    d.add(f'<clipPath id="{cid}"><circle cx="{X(0)}" cy="{Y(125)}" r="{15*s}"/></clipPath>')
    g = [f'<g clip-path="url(#{cid})">']
    for k in range(-16, 17, 2):
        g.append(f'<line x1="{X(k)-10}" y1="{Y(125)-10}" x2="{X(k)+10}" y2="{Y(125)+10}" stroke="#000" stroke-width="0.12"/>')
        g.append(f'<line x1="{X(k)-10}" y1="{Y(125)+10}" x2="{X(k)+10}" y2="{Y(125)-10}" stroke="#000" stroke-width="0.12"/>')
    g.append("</g>")
    d.add("".join(g))
    d.path(f"M{X(-22):.2f},{Y(116):.2f} L{X(-22):.2f},{Y(125):.2f} A{22*s},{22*s} 0 0 1 {X(22):.2f},{Y(125):.2f} L{X(22):.2f},{Y(116):.2f}", 0.6)
    for sx in (-1, 1):
        d.circle(X(sx * 76.5 * math.sin(math.radians(15))), Y(147), 1.6 * s, 0.3)
    # vent (θ=32) + light pipe (θ=-32)
    for th, rr, w in ((32, 8.5, 0.5), (-32, 2.2, 0.5)):
        cx = X(R * math.sin(math.radians(th)))
        d.ellipse(cx, Y(125), rr * s * math.cos(math.radians(th)), rr * s, w)
        if th > 0:
            d.ellipse(cx, Y(125), 4 * s * math.cos(math.radians(th)), 4 * s, 0.25)
    # front latch
    d.rect(X(-7), Y(176), 14 * s, 22 * s, 0.4)
    d.line(X(-5), Y(170), X(5), Y(170), 0.3)
    # panel (front view: top surface foreshortened)
    pz0, pz1 = Z_PLOW, Z_PHIGH + P_T
    d.rect(X(-P_W / 2), Y(pz1), P_W * s, (pz1 - pz0) * s, 0.6, fill="#F3F6FA")
    for i in range(1, 6):
        xx = -P_W / 2 + i * P_W / 6
        d.line(X(xx), Y(pz1 - 2), X(xx), Y(pz0 + 4), 0.18, "thin")
    for j in range(1, 3):
        zz = pz0 + j * (pz1 - pz0) / 3
        d.line(X(-P_W / 2 + 3), Y(zz), X(P_W / 2 - 3), Y(zz), 0.18, "thin")
    d.line(X(-P_W / 2), Y(pz0 + P_T), X(P_W / 2), Y(pz0 + P_T), 0.3)
    # bracket cheeks + feet
    for sx in (-1, 1):
        d.rect(X(sx * 60 - 1), Y(Z_PLOW), 2 * s, (Z_PLOW - H_CAN) * s, 0.5)
        d.rect(X(sx * 60 - 8 if sx > 0 else sx * 60 - 0), Y(H_CAN + 2), 8 * s, 2 * s, 0.4)
    # L bracket top + eye bolt + antenna above panel
    d.rect(X(-20), Y(Z_TAB + BR_T), 40 * s, (Z_TAB + BR_T - pz1) * s, 0.5)
    d.rect(X(-3), Y(Z_TAB + 34), 6 * s, 34 * s, 0.5)
    d.line(X(-3), Y(Z_TAB + 8), X(3), Y(Z_TAB + 8), 0.25, "thin")
    ax = (R + 15) * math.sin(math.radians(218))
    d.rect(X(ax - 3), Y(330), 6 * s, (330 - pz1) * s, 0.5)
    d.path(f"M{X(ax-5):.2f},{Y(322):.2f} l2,-1.2 l2,2.4 l2,-1.2", 0.35)
    d.text(X(ax), Y(333), "≈200 (kesik)", 2.3, "middle")
    # dims front view
    d.dim((X(-R), Y(0)), (X(R), Y(0)), 24, "Ø153", "h")
    d.dim((X(-P_W / 2), Y(pz1)), (X(P_W / 2), Y(pz1)), -10, "165", "h")
    d.dim((X(R_LID), Y(0)), (X(R_LID), Y(H_CAN)), 9, "178", "v")
    d.dim((X(-R), Y(0)), (X(-R), Y(62)), -7, "62", "v")
    d.dim((X(-R), Y(0)), (X(-R), Y(125)), -14, "125", "v")
    d.dim((X(-35), Y(-25)), (X(35), Y(-25)), 5, "Ø70", "h")
    d.leader(X(-10), Y(136), X(-60), Y(150) - 0, "Ø30 HDPE", 2.4)
    d.leader(X(14), Y(73), X(60), Y(90) + 4, "Ø42 siren", 2.4)
    # balloons front
    d.balloon(X(-60), Y(100), X(-105), Y(100), 1)
    d.balloon(X(-R_LID + 4), Y(172), X(-105), Y(172), 2)
    d.balloon(X(-70), Y(240), X(-105), Y(240), 3)
    d.balloon(X(-60), Y(186), X(-105), Y(200), 4)
    d.balloon(X(0), Y(119), X(-50), Y(112), 5)
    d.balloon(X(R * math.sin(math.radians(32))), Y(125), X(105), Y(130), 7)
    d.balloon(X(18), Y(62), X(105), Y(62), 8)
    d.balloon(X(-R * math.sin(math.radians(32))), Y(125), X(-105), Y(130), 9)
    d.balloon(X(20), Y(-12), X(105), Y(-15), 10)
    d.balloon(X(0), Y(Z_TAB + 22), X(40), Y(Z_TAB + 32), 14)
    d.balloon(X(ax), Y(300), X(-105), Y(300), 15)
    d.title(FX, 22, "ÖN GÖRÜNÜŞ", "Ölçek 1:2")

    # ---------------- RIGHT SIDE VIEW (front on the left) ----------------
    SX, SY = 222, FY
    X2 = lambda y: SX - y * s
    Y2 = lambda z: SY - z * s
    d.rect(X2(R), Y2(H_BODY), 2 * R * s, H_BODY * s, 0.6)
    d.rect(X2(R_LID), Y2(H_CAN), 2 * R_LID * s, (H_CAN - H_BODY) * s, 0.6)
    d.line(X2(R), Y2(3), X2(-R), Y2(3), 0.25, "thin")
    d.line(X2(0), Y2(-32), X2(0), Y2(H_CAN + 8), 0.25, "ctr")
    # dome
    d.rect(X2(38), Y2(0), 76 * s, 3 * s, 0.5)
    d.path(f"M{X2(35):.2f},{Y2(-3):.2f} A{35*s},{22*s} 0 0 0 {X2(-35):.2f},{Y2(-3):.2f}", 0.6)
    d.rect(X2(4), Y2(0) + 1.5, 8 * s, 6 * s, 0.4)   # M8 vent cap (θ=270 → y≈0, far side partly)
    # panel (parallelogram) + bracket cheek
    t = math.radians(TILT)
    p = [(P_Y0, Z_PLOW), (-P_Y0, Z_PHIGH), (-P_Y0 - P_T * math.sin(t), Z_PHIGH + P_T * math.cos(t)),
         (P_Y0 - P_T * math.sin(t), Z_PLOW + P_T * math.cos(t))]
    d.path("M" + " L".join(f"{X2(a):.2f},{Y2(b):.2f}" for a, b in p) + " Z", 0.6, fill="#F3F6FA")
    zu = lambda y: Z_PLOW + (P_Y0 - y) * math.tan(t)
    ch = [(50, H_CAN), (50, zu(50)), (-50, zu(-50)), (-50, H_CAN)]
    d.path("M" + " L".join(f"{X2(a):.2f},{Y2(b):.2f}" for a, b in ch) + " Z", 0.5)
    d.path(f"M{X2(30):.2f},{Y2(H_CAN+8):.2f} L{X2(-30):.2f},{Y2(H_CAN+8+60*math.tan(t)*0.62):.2f} "
           f"L{X2(-30):.2f},{Y2(H_CAN+8):.2f} Z", 0.25, "thin")
    d.rect(X2(55), Y2(H_CAN + 2), 110 * s, 2 * s, 0.4)
    # thermal window + hood + sensor axis/FOV
    d.line(X2(R), Y2(140), X2(R), Y2(110), 1.0)
    d.path(f"M{X2(R):.2f},{Y2(149):.2f} L{X2(R+28):.2f},{Y2(140):.2f} L{X2(R+28):.2f},{Y2(136):.2f}", 0.6)
    ox, oz = R - 6, 125
    for ang, sty, L in ((35, "ctr", 112), (5, "thin", 70), (65, "thin", 70)):
        a = math.radians(ang)
        d.line(X2(ox), Y2(oz), X2(ox + L * math.cos(a)), Y2(oz - L * math.sin(a)), 0.25, sty)
    d.line(X2(ox), Y2(oz), X2(ox + 60), Y2(oz), 0.25, "thin")
    d.angle(X2(ox), Y2(oz), 44 * s * 2 * 0.62, 180, 180 - 35, "35°", 2.5)
    d.angle(X2(ox), Y2(oz), 66 * s * 2 * 0.62, 180 - 5, 180 - 65, "FOV 60°", 2.4, tr=66 * 0.62 + 4)
    # siren protrusion, vent (θ=32 near side), PG7 (θ=142 near side)
    d.rect(X2(R + 4), Y2(83), 4 * s, 42 * s, 0.5)
    vy = R * math.cos(math.radians(32))
    d.ellipse(X2(vy), Y2(125), 8.5 * s * math.sin(math.radians(32)), 8.5 * s, 0.5)
    py = R * math.cos(math.radians(142))
    d.ellipse(X2(py), Y2(150), 9.5 * s * math.sin(math.radians(142)), 9.5 * s, 0.5)
    d.ellipse(X2(py), Y2(150), 4 * s * math.sin(math.radians(142)), 4 * s, 0.3)
    # L bracket, spacers, tab, eye bolt
    yb = Y_PLATE - BR_T
    d.rect(X2(Y_PLATE), Y2(Z_TAB + BR_T), BR_T * s, (Z_TAB + BR_T - 30) * s, 0.6, fill="#ddd")
    d.rect(X2(Y_PLATE + 30), Y2(Z_TAB + BR_T), 30 * s, BR_T * s, 0.6, fill="#ddd")
    for zz in (60, 130):
        d.rect(X2(-R), Y2(zz + 5), SPACER * s, 10 * s, 0.4)
        d.line(X2(-R + 8), Y2(zz), X2(yb - 6), Y2(zz), 0.25, "ctr")
    ey = Y_PLATE + 15
    d.line(X2(ey), Y2(Z_TAB + BR_T), X2(ey), Y2(Z_TAB + 10), 0.6)
    d.circle(X2(ey), Y2(Z_TAB + 25), 15 * s, 0.6)
    d.circle(X2(ey), Y2(Z_TAB + 25), 9 * s, 0.5)
    # antenna (θ=218 far side; visible above lid) + rope hint
    ay = (R + 12) * math.cos(math.radians(218))
    d.rect(X2(ay + 3), Y2(330), 6 * s, (330 - H_CAN) * s, 0.5)
    d.path(f"M{X2(ay+5):.2f},{Y2(322):.2f} l2,-1.2 l2,2.4 l2,-1.2", 0.35)
    d.path(f"M{X2(ey):.2f},{Y2(Z_TAB+40):.2f} C{X2(ey-5):.2f},{Y2(Z_TAB+55):.2f} {X2(ey-25):.2f},{Y2(Z_TAB+60):.2f} "
           f"{X2(ey-40):.2f},{Y2(Z_TAB+62):.2f}", 0.25, "ph")
    d.text(X2(ey - 41), Y2(Z_TAB + 61), "halat → dal", 2.2)
    # tree + strap
    tb = yb - 0.0
    d.line(X2(tb), Y2(-30), X2(tb), Y2(340), 0.25, "ph")
    d.text(X2(tb) + 2.5, Y2(-20), "ağaç kabuğu", 2.3, italic=True)
    for zz in (45, 150):
        d.rect(X2(yb + 1), Y2(zz + 10), 30 * s, 20 * s, 0.35)
        d.hatch_rect(X2(yb + 1), Y2(zz + 10), 30 * s, 20 * s, 1.0)
    # dims side view
    d.dim((X2(P_Y0), Y2(H_CAN)), (X2(P_Y0), Y2(Z_PLOW)), -22, "15", "v", tshift=0)
    d.angle(X2(P_Y0), Y2(Z_PLOW), 22, 180, 180 + 30, "30°", 2.6)
    d.line(X2(P_Y0), Y2(Z_PLOW), X2(P_Y0 + 25), Y2(Z_PLOW), 0.25, "thin")
    d.dim((X2(R + 28), Y2(-25)), (X2(Y_PLATE - BR_T), Y2(-25)), 12, "≈ 195 (siperlik – braket)", "h")
    d.dim((X2(-P_Y0), Y2(Z_PHIGH + P_T)), (X2(P_Y0), Y2(Z_PHIGH + P_T)), -14, "117 (135 × cos30°)", "h")
    d.dim((X2(-R), Y2(Z_TAB)), (X2(-R), Y2(0)), 0, "", "v") if False else None
    d.dim((X2(Y_PLATE - BR_T), Y2(0)), (X2(Y_PLATE - BR_T), Y2(Z_TAB + BR_T)), 22, "292", "v")
    d.dim((X2(-R), Y2(60)), (X2(Y_PLATE), Y2(60)), -40, "10", "h", tshift=0)
    d.dim((X2(R), Y2(-25)), (X2(R), Y2(0)), 14, "25", "v") if False else None
    # balloons side
    d.balloon(X2(0), Y2(225), X2(20), Y2(250), 3)
    d.balloon(X2(-20), Y2(200), X2(-15), Y2(240), 4)
    d.balloon(X2(R + 14), Y2(145), X2(R + 34), Y2(160), 6)
    d.balloon(X2(Y_PLATE - 1), Y2(95), X2(Y_PLATE - 60), Y2(95), 12)
    d.balloon(X2(yb - 10), Y2(150), X2(Y_PLATE - 60), Y2(175), 13)
    d.balloon(X2(ey - 8), Y2(Z_TAB + 25), X2(ey - 30), Y2(Z_TAB + 34), 14)
    d.balloon(X2(py - 8), Y2(150), X2(Y_PLATE - 60), Y2(135), 16)
    d.balloon(X2(30), Y2(-10), X2(42), Y2(-35), 10)
    d.balloon(X2(4), Y2(-4), X2(-25), Y2(-35), 11)
    d.title(SX, 22, "A — SAĞ YAN GÖRÜNÜŞ", "Ölçek 1:2 (ön solda, ağaç sağda)")

    # ---------------- TOP VIEW (front down) ----------------
    TX, TY = 352, 95
    X3 = lambda x: TX + x * s
    Y3 = lambda y: TY + y * s
    d.circle(X3(0), Y3(0), R_LID * s, 0.6)
    d.circle(X3(0), Y3(0), (R_LID - 3) * s, 0.25)
    d.line(X3(-90), Y3(0), X3(90), Y3(0), 0.25, "ctr")
    d.line(X3(0), Y3(-100), X3(0), Y3(115), 0.25, "ctr")
    # panel (hidden lid under it) – panel outline visible
    d.rect(X3(-P_W / 2), Y3(-P_Y0), P_W * s, P_PROJ * s, 0.6, fill="#F3F6FA")
    for i in range(1, 6):
        d.line(X3(-P_W / 2 + i * P_W / 6), Y3(-P_Y0 + 2), X3(-P_W / 2 + i * P_W / 6), Y3(P_Y0 - 2), 0.18, "thin")
    for sx in (-1, 1):
        d.rect(X3(sx * 60 - 1), Y3(-50), 2 * s, 100 * s, 0.3, "hid")
        for sy in (-1, 1):
            d.circle(X3(sx * 60), Y3(sy * 40), 2.15 * s, 0.3, "hid")
    # latches at 0,120,240 (outside lid)
    for th in (0, 120, 240):
        a = math.radians(th)
        cx, cy = (R + 4) * math.sin(a), (R + 4) * math.cos(a)
        d.rect(X3(cx) - 2, Y3(cy) - 2, 4, 4, 0.4)
    # window hood (front), siren & vent protrusions
    d.rect(X3(-22), Y3(R), 44 * s, 28 * s, 0.5)
    for sg in (-1, 1):
        d.line(X3(sg * 12), Y3(R + 28), X3(sg * (12 + 22 * math.tan(math.radians(30)))), Y3(R + 50), 0.25, "thin")
    d.text(X3(28), Y3(R + 46), "görüş ±30°", 2.2, italic=True)
    vx, vy2 = (R + 6) * math.sin(math.radians(32)), (R + 6) * math.cos(math.radians(32))
    d.circle(X3(vx), Y3(vy2), 8.5 * s, 0.5)
    # rear: bracket plate + tab + eye bolt, SMA/antenna, PG7, strap + tree
    d.rect(X3(-20), Y3(Y_PLATE - BR_T), 40 * s, BR_T * s, 0.6, fill="#ddd")
    d.rect(X3(-20), Y3(Y_PLATE - BR_T), 40 * s, 30 * s, 0.5)
    d.circle(X3(0), Y3(Y_PLATE + 15), 3 * s, 0.5)
    for th, L, lab in ((218, 18, "SMA"), (142, 16, "PG7")):
        a = math.radians(th)
        x0, y0 = R * math.sin(a), R * math.cos(a)
        x1, y1 = (R + L) * math.sin(a), (R + L) * math.cos(a)
        d.line(X3(x0), Y3(y0), X3(x1), Y3(y1), 1.6)
    ant = math.radians(218)
    d.circle(X3((R + 18) * math.sin(ant)), Y3((R + 18) * math.cos(ant)), 3 * s, 0.6)
    tr_ = 150   # Ø300 example trunk
    tcy = Y_PLATE - BR_T - tr_
    yy_ = tcy + math.sqrt(tr_**2 - 115**2)
    d.path(f"M{X3(-115):.2f},{Y3(yy_):.2f} A{tr_*s},{tr_*s} 0 0 0 {X3(115):.2f},{Y3(yy_):.2f}", 0.25, "ph")
    d.path(f"M{X3(-20):.2f},{Y3(Y_PLATE-BR_T-1):.2f} C{X3(-60):.2f},{Y3(Y_PLATE-8):.2f} {X3(-95):.2f},{Y3(Y_PLATE-30):.2f} "
           f"{X3(-112):.2f},{Y3(Y_PLATE-58):.2f}", 0.6)
    d.path(f"M{X3(20):.2f},{Y3(Y_PLATE-BR_T-1):.2f} C{X3(60):.2f},{Y3(Y_PLATE-8):.2f} {X3(95):.2f},{Y3(Y_PLATE-30):.2f} "
           f"{X3(112):.2f},{Y3(Y_PLATE-58):.2f}", 0.6)
    d.text(X3(0), Y3(Y_PLATE - 32), "ağaç (örnek Ø300; Ø150…600)", 2.3, "middle", italic=True)
    # angle dims for SMA / PG7 from rear axis
    d.line(X3(0), Y3(0), X3(0), Y3(-R - 25), 0.25, "thin")
    for th in (218, 142):
        a = math.radians(th)
        d.line(X3(0), Y3(0), X3((R + 25) * math.sin(a)), Y3((R + 25) * math.cos(a)), 0.25, "thin")
    d.angle(X3(0), Y3(0), 52 * s * 2 * 0.62, 270, 270 - 38, "38°", 2.4, tr=52 * 0.62 + 6)
    d.angle(X3(0), Y3(0), 52 * s * 2 * 0.62, 270, 270 + 38, "38°", 2.4, tr=52 * 0.62 + 6)
    d.angle(X3(0), Y3(0), 30, 90, 90 - 32, "32°", 2.4)
    d.dim((X3(-P_W / 2), Y3(P_Y0)), (X3(P_W / 2), Y3(P_Y0)), 26, "165", "h")
    d.dim((X3(P_W / 2), Y3(-P_Y0)), (X3(P_W / 2), Y3(P_Y0)), 6, "117", "v")
    d.balloon(X3(-(R + 4) * math.sin(math.radians(120))), Y3((R + 4) * math.cos(math.radians(120))), X3(-100), Y3(-20), 2)
    d.balloon(X3(-55), Y3(-36), X3(-100), Y3(-45), 4)
    d.balloon(X3((R + 14) * math.sin(math.radians(218))), Y3((R + 14) * math.cos(math.radians(218))), X3(-100), Y3(-75), 15)
    d.balloon(X3((R + 12) * math.sin(math.radians(142))), Y3((R + 12) * math.cos(math.radians(142))), X3(100), Y3(-75), 16)
    d.balloon(X3(vx), Y3(vy2), X3(100), Y3(55), 7)
    d.balloon(X3(-15), Y3(R + 14), X3(-100), Y3(80), 6)
    d.title(TX, 22, "B — ÜST GÖRÜNÜŞ", "Ölçek 1:2 (ön aşağıda)")

    # view arrows on front view
    for (x, y, ang, lab) in ((X(R) + 30, Y(20), 180, "A"), (X(0) + 40, Y(Z_TAB + 45), 90, "B")):
        a = math.radians(ang)
        d.line(x, y, x - 9 * math.cos(a), y - 9 * math.sin(a), 0.5)
        d.arrowhead(x, y, ang, 3.4, 1.3)
        d.text(x - 11 * math.cos(a) - (3 if ang == 90 else 0), y - 11 * math.sin(a) + 1.5, lab, 4.2, "middle", "bold")

    # ---------------- parts list ----------------
    items = [
        (1, "Gövde: kalaylı sac teneke Ø153 × 178, dış RAL 9010 ısı yansıtıcı epoksi, iç astar + 5 mm Al-yüzlü PE köpük"),
        (2, "Kapak + EPDM conta + 3 paslanmaz kilit klipsi (0° / 120° / 240°)"),
        (3, "Güneş paneli 6 V 3 W ETFE 165 × 135, 30° eğim — güneşlik görevi"),
        (4, "Al 5052 panel braketi (2 yan yanak, 4×M4 kapağa), panel–kapak 15 mm hava boşluğu"),
        (5, "Termal pencere Ø30: HDPE 0,4 mm + paslanmaz tel örgü (cam/akrilik yok)"),
        (6, "Yağmur siperliği; AMG8833 ekseni yataydan 35° aşağı, FOV 60°"),
        (7, "M12 ePTFE membran vent (BME680 haznesi), θ = +32°"),
        (8, "Piezo siren Ø42, 12 V 105 dB, 2×M3 flanş"),
        (9, "Durum LED’i ışık borusu Ø3, θ = −32°"),
        (10, "Alt PC kubbe Ø70 (6 × 1 W LED halkası Ø50) + mıknatıs test noktası (SW3)"),
        (11, "M8 ePTFE basınç dengeleme + labirentli drenaj (alt kapak)"),
        (12, "Paslanmaz L braket 2 mm, 2×M5 + 10 mm aralayıcı, iç takviye pulu"),
        (13, "Paslanmaz bant kelepçe (Ø15–60 cm ağaç), braket yarıklarından geçer"),
        (14, "M6 mapa + 2 mm paslanmaz emniyet halatı (üst dala)"),
        (15, "SMA dişi bulkhead (θ = 218°) + 90° adaptör + 3 dBi IP67 LTE anten (yukarı)"),
        (16, "PG7 kablo rakoru (θ = 142°) — panel kablosu"),
    ]
    bx, by = 290, 170
    d.add(f'<rect x="{bx}" y="{by}" width="120" height="{6 + len(items)*5.0 + 2}" fill="#fff" stroke="#000" stroke-width="0.35"/>')
    d.add(f'<rect x="{bx}" y="{by}" width="120" height="6" fill="{GREEN}"/>')
    d.text(bx + 2, by + 4.3, "PARÇA / ÖZELLİK LİSTESİ", 3, "start", "bold", "#fff")
    for i, (n, t) in enumerate(items):
        yy = by + 6 + 4.0 + i * 5.0
        d.add(f'<circle cx="{bx+4}" cy="{yy-1.0}" r="2.1" fill="#fff" stroke="#000" stroke-width="0.3"/>')
        d.text(bx + 4, yy, str(n), 2.4, "middle", "bold")
        words, line, lines = t.split(), "", []
        for w in words:
            if len(line + " " + w) > 74:
                lines.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        for k, ln in enumerate(lines[:2]):
            d.text(bx + 8, yy - 0.3 + k * 2.3 - (1.1 if len(lines) > 1 else 0), ln, 2.0)
    notes = ["NOTLAR",
             "1. Ölçüler mm. Genel tolerans ISO 2768-m. Delikler boyamadan önce açılır, çapakları alınır.",
             "2. Tüm dış delikler EPDM/O-ring ile sızdırmaz; hedef IP54. Teneke iç yüzeyi astarlanır.",
             "3. Anten zorunludur (teneke gövde Faraday kafesidir). Anten dikey yukarı.",
             "4. Panel tabanı ile kapak arası ≥ 15 mm hava boşluğu: gövdeyi güneşten korur.",
             "5. Delik konumları için sayfa 2 (delme şablonu) ve 1:1 şablon dosyalarına bakın.",
             "6. Montaj yüksekliği 3–5 m; sensör yamaca / izlenecek alana bakacak şekilde döndürülür."]
    for i, t in enumerate(notes):
        d.text(14, 252 + i * 4.3, t, 2.9 if i == 0 else 2.5, "start", "bold" if i == 0 else "normal")
    d.text(14, 248, "Görünüşler ok yöntemiyle (ISO 128-30) gösterilmiştir.", 2.4, italic=True, color="#444")
    fr, _ = frame_svg(420, 297, title="Orman Nöbetçisi ON-1 — Gövde montajı", subtitle="Mekanik resim 1/2: ön, yan ve üst görünüşler",
                      sheet="1/2", doc="ON1-MEC-001", scale="1:2", unit=0.1)
    return svg_doc(fr + d.o)


# ------------------------------------------------------------------ sheet 2: drilling template
def wall_development(d, ox, oy, s, full=False):
    """Draws the developed can wall. ox = x of θ=0 (front), oy = y of z=0 (bottom). s = scale."""
    half = C / 2
    X = lambda th: ox + R * math.radians(th) * s
    Y = lambda z: oy - z * s
    d.rect(X(-180), Y(H_BODY), C * s, H_BODY * s, 0.5)
    d.line(X(-180), Y(H_CAN - 12), X(180), Y(H_CAN - 12), 0.25, "hid") if False else None
    for th in range(-180, 181, 30):
        d.line(X(th), Y(H_BODY), X(th), Y(0), 0.25, "ctr" if th % 90 == 0 else "thin")
        d.text(X(th), Y(0) + (5 if not full else 6), f"{th}°", 2.6 if not full else 3.5, "middle")
        d.text(X(th), Y(H_BODY) - (2 if not full else 3), f"{R*math.radians(th):+.1f}".replace(".", ","), 2.0 if not full else 2.8, "middle", color="#555")
    for z in (0, 62, 125, 150, H_BODY):
        d.line(X(-180) - 2, Y(z), X(-180), Y(z), 0.25, "thin")
    names = {0: "ÖN", 90: "SAĞ", -90: "SOL", 180: "ARKA", -180: "ARKA"}
    for th, nm in names.items():
        d.text(X(th), Y(H_BODY) - (6 if not full else 9), nm, 3 if not full else 4.5, "middle", "bold", GREEN)
    for hid, lab, th, z, dia, note in WALL_HOLES:
        t = th if th <= 180 else th - 360
        cx, cy = X(t), Y(z)
        d.circle(cx, cy, dia / 2 * s, 0.45)
        cl = max(dia / 2 + 3, 5) * s
        d.line(cx - cl, cy, cx + cl, cy, 0.18, "ctr")
        d.line(cx, cy - cl, cx, cy + cl, 0.18, "ctr")
        if full:
            d.text(cx + dia / 2 * s + 1.5, cy - dia / 2 * s - 1, f"{hid} Ø{dia:g}".replace(".", ","), 3.2, weight="bold")
    return X, Y


def sheet_template():
    d = D()
    s = 0.5
    ox, oy = 162, 128
    X, Y = wall_development(d, ox, oy, s)
    d.title(150, 22, "GÖVDE YAN YÜZEY AÇINIMI (delme şablonu)", "Ölçek 1:2 • yatay = yay uzunluğu s = R·θ (R = 76,5, çevre 480,7 mm) • dikey = tabandan yükseklik z")
    # labels for holes
    tags = {}
    for hid, lab, th, z, dia, note in WALL_HOLES:
        t = th if th <= 180 else th - 360
        if hid in tags:
            continue
        tags[hid] = 1
        cx, cy = X(t), Y(z)
        off = {"H1": (-16, 9), "H2": (10, 8), "H3": (-10, 8), "H4": (16, 10), "H5": (10, -9), "H6": (14, -2), "H7": (8, 10),
               "H8": (10, 7), "H9": (-12, 7), "H10": (-14, -1)}[hid]
        sx_ = 1 if off[0] > 0 else -1
        sy_ = 1 if off[1] > 0 else -1
        k = dia / 2 * s * 0.71
        d.leader(cx + sx_ * k, cy + sy_ * k, cx + off[0], cy + off[1], hid, 2.7)
    # dims
    d.dim((X(-180), Y(0)), (X(180), Y(0)), 14, "480,7 (Ø153 × π)", "h")
    d.dim((X(180), Y(0)), (X(180), Y(H_BODY)), 8, "166 (gövde)", "v")
    for z in (62, 125, 150):
        d.dim((X(-180), Y(0)), (X(-180), Y(z)), -6 - {62: 0, 125: 7, 150: 14}[z], f"{z}", "v")
    d.dim((X(180), Y(150)), (X(218 - 360 + 360 if False else 180), Y(150)), 0, "", "h") if False else None
    d.text(X(-180) + 2, Y(H_BODY) - 12, "s (mm) →", 2.4, color="#555")
    # hole table
    rows = [("No", "Özellik", "θ (°)", "s (mm)", "z (mm)", "Ø (mm)", "Not")]
    seen = {}
    for hid, lab, th, z, dia, note in WALL_HOLES:
        t = th if th <= 180 else th - 360
        key = (hid, lab)
        seen.setdefault(key, []).append((t, z))
    for (hid, lab), pts in seen.items():
        dia = [h[4] for h in WALL_HOLES if h[0] == hid][0]
        note = [h[5] for h in WALL_HOLES if h[0] == hid and h[5]]
        ths = sorted(set(round(p[0], 1) for p in pts))
        zs = sorted(set(p[1] for p in pts))
        if hid == "H10":
            rows.append((hid, lab, "0 / 120 / −120, her biri ±6,74", "±9,0 yay (merkez: 0 / ±160,2)", "158", "3,2", "6 adet (3 klips × 2)"))
            continue
        rows.append((hid, lab, " / ".join(f"{t:g}" for t in ths).replace(".", ",").replace("-", "−"),
                     " / ".join(f"{R*math.radians(t):+.1f}" for t in ths).replace(".", ",").replace("-", "−"),
                     " / ".join(f"{z:g}" for z in zs), f"{dia:g}".replace(".", ","), note[0] if note else ""))
    tx, ty = 14, 168
    cw = [11, 30, 46, 46, 17, 13, 39]
    d.text(tx, ty - 3, "DELİK TABLOSU — yan yüzey (θ: önden saat yönünde, üstten bakış)", 3, "start", "bold")
    for i, r in enumerate(rows):
        yy = ty + i * 5.6
        if i == 0:
            d.add(f'<rect x="{tx}" y="{yy}" width="{sum(cw)}" height="5.6" fill="{GREEN}"/>')
        elif i % 2 == 0:
            d.add(f'<rect x="{tx}" y="{yy}" width="{sum(cw)}" height="5.6" fill="#EEF2EE"/>')
        cx = tx
        for j, c in enumerate(r):
            d.text(cx + 1.2, yy + 4.1, c, 2.3, "start", "bold" if i == 0 or j == 0 else "normal",
                   "#fff" if i == 0 else "#000")
            cx += cw[j]
    d.add(f'<rect x="{tx}" y="{ty}" width="{sum(cw)}" height="{5.6*len(rows)}" fill="none" stroke="{GREEN}" stroke-width="0.35"/>')

    # bottom disc
    bx, by = 264, 205
    d.circle(bx, by, R * s, 0.5)
    d.line(bx - 45, by, bx + 45, by, 0.18, "ctr")
    d.line(bx, by - 45, bx, by + 45, 0.18, "ctr")
    d.circle(bx, by, 32 * s, 0.18, "ctr")
    d.circle(bx, by, 55 * s, 0.18, "ctr")
    for hid, lab, r, th, dia in BOTTOM_HOLES:
        a = math.radians(th)
        cx, cy = bx - r * math.sin(a) * s, by + r * math.cos(a) * s
        d.circle(cx, cy, dia / 2 * s, 0.45)
    d.text(bx, by - R * s - 12, "ALT KAPAK (taban) — dıştan (alttan) bakış", 3, "middle", "bold")
    d.text(bx, by - R * s - 7.5, "ön aşağıda; cihazın sağı solda görünür (ayna)", 2.3, "middle", italic=True)
    d.leader(bx + 28 * s * 0.7, by - 28 * s * 0.7, bx + 16, by - 30, "B1 Ø56 LED penceresi", 2.4, anchor="start")
    a30 = math.radians(30)
    d.leader(bx - 32 * s * math.sin(a30), by + 32 * s * math.cos(a30), bx - 4, by + 30, "B2 3×Ø3,4 PCD 64", 2.4, anchor="start")
    d.leader(bx - 55 * s, by + 1.5, bx - 18, by + 20, "B3 Ø6 drenaj", 2.4, anchor="start")
    d.leader(bx + 55 * s, by, bx + 30, by + 12, "B4 Ø8,2 M8 vent", 2.4)
    d.text(bx, by + R * s + 6, "B2: 30°/150°/270° • B3: r 55, 90° • B4: r 55, 270° • test mıknatısı noktası: kubbe kenarı, 0°", 2.2, "middle", italic=True)
    d.dim((bx - R * s, by + R * s + 9), (bx + R * s, by + R * s + 9), 0, "", "h") if False else None
    # lid
    lx, ly = 360, 205
    d.circle(lx, ly, R_LID * s, 0.5)
    d.circle(lx, ly, (R_LID - 3) * s, 0.18)
    d.line(lx - 45, ly, lx + 45, ly, 0.18, "ctr")
    d.line(lx, ly - 45, lx, ly + 45, 0.18, "ctr")
    for hid, lab, x, y, dia in LID_HOLES:
        d.circle(lx + x * s, ly + y * s, dia / 2 * s, 0.45)
    d.text(lx, ly - R * s - 12, "ÜST KAPAK — üstten bakış, ön aşağıda", 3, "middle", "bold")
    d.dim((lx - 30, ly + 20), (lx + 30, ly + 20), 8, "120", "h")
    d.dim((lx + 30, ly - 20), (lx + 30, ly + 20), 14, "80", "v")
    d.leader(lx - 30 - 1.0, ly - 20 - 1.0, lx - 16, ly - 30, "L1 4×Ø4,3 (M4)", 2.4, anchor="start")
    d.text(lx, ly + R * s + 6, "Kapak eteğinde klips karşılıkları: 0° / 120° / 240°", 2.3, "middle", italic=True)
    d.text(14, 284 - 6, "1:1 şablonlar: ON1_drilling_template_wall_1to1.svg (520 × 230 mm) ve ON1_drilling_template_discs_1to1.svg "
           "(A3) — %100 ölçekle yazdırın, 100 mm kontrol çubuğunu ölçün.", 2.5, italic=True, color="#444")
    fr, _ = frame_svg(420, 297, title="Orman Nöbetçisi ON-1 — Delme şablonu", subtitle="Mekanik resim 2/2: gövde, alt kapak, üst kapak",
                      sheet="2/2", doc="ON1-MEC-002", scale="1:2", unit=0.1)
    return svg_doc(fr + d.o)


def template_wall_1to1():
    W, Hh = 520, 230
    d = D()
    X, Y = wall_development(d, W / 2, 200, 1.0, full=True)
    d.text(10, 12, "Orman Nöbetçisi ON-1 — Gövde yan yüzey delme şablonu (1:1)", 6, weight="bold")
    d.text(10, 19, "%100 ölçekle yazdırın. Şablonu ÖN (0°) çizgisi termal pencere ekseni olacak şekilde gövdeye sarın; "
           "alt kenar = gövde tabanı. Çevre 480,7 mm.", 3.5)
    # 100 mm check bar
    d.rect(10, 214, 100, 4, 0.4, fill="#000")
    d.text(10, 224, "Kontrol: bu çubuk tam 100 mm olmalı", 3.2)
    for hid, lab, th, z, dia, note in WALL_HOLES:
        pass
    leg = "H1 Ø30 pencere • H2 Ø12,2 M12 vent • H3 Ø3,2 ışık borusu • H4 Ø42 siren • H5 Ø3,2 siren flanşı • H6 Ø3,2 siperlik • " \
          "H7 Ø5,5 L braket • H8 Ø6,5 SMA • H9 Ø12,5 PG7 • H10 Ø3,2 klips perçini"
    d.text(130, 218, leg, 3.0)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{Hh}mm" viewBox="0 0 {W} {Hh}" font-family="{F}">'
            f'<rect width="{W}" height="{Hh}" fill="#fff"/>' + "\n".join(d.o) + "</svg>")


def template_discs_1to1():
    W, Hh = 420, 297
    d = D()
    d.text(10, 12, "ON-1 — Alt kapak ve üst kapak delme şablonu (1:1, A3 yatay, %100 yazdırın)", 5, weight="bold")
    for (cx, cy, title, holes, rr) in ((110, 150, "ALT KAPAK (dıştan bakış, ön aşağıda, ayna)", "b", R), (310, 150, "ÜST KAPAK (üstten, ön aşağıda)", "l", R_LID)):
        d.circle(cx, cy, rr, 0.4)
        d.line(cx - rr - 5, cy, cx + rr + 5, cy, 0.2, "ctr")
        d.line(cx, cy - rr - 5, cx, cy + rr + 5, 0.2, "ctr")
        d.text(cx, cy - rr - 8, title, 4, "middle", "bold")
        d.text(cx, cy + rr + 7, "ÖN ↓", 4, "middle", "bold", GREEN)
        if holes == "b":
            for hid, lab, r, th, dia in BOTTOM_HOLES:
                a = math.radians(th)
                x, y = cx - r * math.sin(a), cy + r * math.cos(a)
                d.circle(x, y, dia / 2, 0.4)
                d.line(x - dia / 2 - 2, y, x + dia / 2 + 2, y, 0.15, "ctr")
                d.line(x, y - dia / 2 - 2, x, y + dia / 2 + 2, 0.15, "ctr")
                if lab:
                    d.text(x + dia / 2 + 1.5, y - dia / 2 - 0.5, f"{hid} Ø{dia:g}".replace(".", ","), 3.2, weight="bold")
        else:
            for hid, lab, x0, y0, dia in LID_HOLES:
                x, y = cx + x0, cy + y0
                d.circle(x, y, dia / 2, 0.4)
                d.line(x - 4, y, x + 4, y, 0.15, "ctr")
                d.line(x, y - 4, x, y + 4, 0.15, "ctr")
            d.text(cx + 62, cy - 44, "L1 4×Ø4,3", 3.2, weight="bold")
    d.rect(10, 280, 100, 4, 0.4, fill="#000")
    d.text(115, 283.5, "Kontrol: çubuk = 100 mm", 3.2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{Hh}mm" viewBox="0 0 {W} {Hh}" font-family="{F}">'
            f'<rect width="{W}" height="{Hh}" fill="#fff"/>' + "\n".join(d.o) + "</svg>")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn, fnc in (("ON1_mechanical_drawing.svg", sheet_views), ("ON1_drilling_template.svg", sheet_template),
                    ("ON1_drilling_template_wall_1to1.svg", template_wall_1to1),
                    ("ON1_drilling_template_discs_1to1.svg", template_discs_1to1)):
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
            f.write(fnc())
        print("wrote", fn)
