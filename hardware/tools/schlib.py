# -*- coding: utf-8 -*-
"""
schlib.py - minimal EDA-style schematic drawing library that emits SVG
and keeps real connectivity (pins, wires, labels, power ports) so that a
netlist / ERC report can be generated from the very same drawing.

Coordinate unit: 0.1 mm  (A3 landscape sheet = 4200 x 2970 units).
Rotation follows SVG convention (y down): rot=90 turns +x into +y.
"""
import math
import html
from collections import defaultdict

FONT = "Arial, Helvetica, sans-serif"
LW = 2.4          # wire width
SW = 2.4          # symbol stroke width
TXT = 21          # default text size (ref/value)
PIN_TXT = 17      # pin numbers
PNAME_TXT = 19    # pin names inside ICs
JR = 6.5          # junction dot radius


def esc(s):
    return html.escape(str(s), quote=False)


_AW = {}
for _c, _w in (("IJijl.,:;'|!", 0.28), ("frt()[]-/", 0.33), ("abcdeghknopqsuvxyz", 0.556), ("0123456789_", 0.556),
               ("mM", 0.84), ("wW", 0.85), ("ABEKPSVXYFTLZ", 0.667), ("CDHNRUGOQ", 0.75), (" ", 0.28),
               ("ÇĞÖŞÜ", 0.74), ("İı", 0.28), ("çğöşü", 0.556), ("+=<>~−±×", 0.584), ("µΩ°", 0.6)):
    for _ch in _c:
        _AW[_ch] = _w


def text_width(s, size):
    return sum(_AW.get(ch, 0.6) for ch in str(s)) * size


def fmt(v):
    v = round(v, 2)
    return str(int(v)) if v == int(v) else str(v)


# --------------------------------------------------------------------------
#  Symbol library (local coordinates, pins at lead ends)
# --------------------------------------------------------------------------
def _line(x1, y1, x2, y2, w=SW, extra=""):
    return f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke-width="{w}" {extra}/>'


def sym_res():
    g = [_line(0, -40, 0, -22), _line(0, 22, 0, 40),
         '<rect x="-8" y="-22" width="16" height="44" fill="#fff"/>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-9, -40, 9, 40)


def sym_cap():
    g = [_line(0, -40, 0, -5), _line(0, 5, 0, 40),
         _line(-17, -5, 17, -5, 4.2), _line(-17, 5, 17, 5, 4.2)]
    return g, {"1": (0, -40), "2": (0, 40)}, (-18, -40, 18, 40)


def sym_cap_pol():
    g = [_line(0, -40, 0, -7), _line(0, 7, 0, 40),
         '<rect x="-17" y="-8" width="34" height="5" fill="#fff"/>',
         '<rect x="-17" y="3" width="34" height="5" fill="#000"/>',
         _line(-27, -19, -19, -19, 2), _line(-23, -23, -23, -15, 2)]
    return g, {"1": (0, -40), "2": (0, 40)}, (-28, -40, 18, 40)


def sym_ind():
    p = "M0,-24 a6,6 0 0 1 0,12 a6,6 0 0 1 0,12 a6,6 0 0 1 0,12 a6,6 0 0 1 0,12"
    g = [_line(0, -40, 0, -24), _line(0, 24, 0, 40), f'<path d="{p}" fill="none"/>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-2, -40, 8, 40)


def _diode_body(kind):
    g = [_line(0, -40, 0, -12), _line(0, 12, 0, 40),
         '<path d="M-14,-12 L14,-12 L0,12 Z" fill="#fff"/>']
    if kind == "d":
        g.append(_line(-14, 12, 14, 12))
    elif kind == "schottky":
        g.append('<path d="M-13,7 L-19,7 L-19,12 L19,12 L19,17 L13,17" fill="none"/>')
    elif kind == "tvs":
        g.append('<path d="M-21,6 L-15,12 L15,12 L21,18" fill="none"/>')
    elif kind == "led":
        g.append(_line(-14, 12, 14, 12))
        for dy in (-8, 4):
            g.append(_line(17, dy, 30, dy - 12, 1.8))
            g.append(f'<path d="M30,{dy-12} l-7,1.5 l4.5,4.5 Z" fill="#000" stroke-width="1"/>')
    return g


def sym_diode(kind="d"):
    return _diode_body(kind), {"A": (0, -40), "K": (0, 40)}, (-20, -40, 30 if kind == "led" else 20, 40)


def sym_ptc():
    g = [_line(0, -40, 0, -22), _line(0, 22, 0, 40),
         '<rect x="-8" y="-22" width="16" height="44" fill="#fff"/>',
         '<path d="M-17,18 L15,-18 L23,-18" fill="none" stroke-width="1.8"/>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-17, -40, 23, 40)


def sym_ntc():
    g = [_line(0, -40, 0, -22), _line(0, 22, 0, 40),
         '<rect x="-8" y="-22" width="16" height="44" fill="#fff"/>',
         '<path d="M-23,18 L-15,18 L15,-18" fill="none" stroke-width="1.8"/>',
         f'<text x="12" y="20" font-size="15" font-family="{FONT}" stroke="none" fill="#000">-t°</text>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-23, -40, 35, 40)


def sym_xtal():
    g = [_line(0, -40, 0, -15), _line(0, 15, 0, 40),
         _line(-15, -15, 15, -15, 3), _line(-15, 15, 15, 15, 3),
         '<rect x="-10" y="-8" width="20" height="16" fill="#fff"/>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-16, -40, 16, 40)


def sym_switch(kind="no"):
    g = [_line(0, -40, 0, -18), _line(0, 18, 0, 40),
         '<circle cx="0" cy="-18" r="3.2" fill="#fff"/>',
         '<circle cx="0" cy="18" r="3.2" fill="#fff"/>']
    if kind in ("no", "reed_no", "vib"):
        g.append(_line(0, 15, -15, -14))
    if kind == "reed_nc":
        g.append(_line(0, 15, 6, -22))
        g.append(_line(0, -18, 8, -18, 2))
    if kind in ("reed_no", "reed_nc"):
        g.append('<rect x="-21" y="-30" width="42" height="60" rx="13" fill="none" stroke-width="1.6"/>')
    if kind == "vib":
        g.append('<path d="M8,-10 q5,4 0,8 q-5,4 0,8 q5,4 0,8" fill="none" stroke-width="1.6"/>')
    return g, {"1": (0, -40), "2": (0, 40)}, (-21, -40, 21, 40)


def sym_cell():
    g = [_line(0, -40, 0, -6), _line(0, 6, 0, 40),
         _line(-18, -6, 18, -6, 2.4), _line(-9, 6, 9, 6, 5),
         _line(-27, -18, -19, -18, 2), _line(-23, -22, -23, -14, 2)]
    return g, {"+": (0, -40), "-": (0, 40)}, (-28, -40, 18, 40)


def sym_nmos(body_diode=False):
    g = [_line(-40, 0, -2, 0), _line(-2, -20, -2, 20, 2.6),
         _line(8, -26, 8, -12, 3), _line(8, -6, 8, 6, 3), _line(8, 12, 8, 26, 3),
         _line(8, -19, 24, -19), _line(24, -19, 24, -40),
         _line(8, 19, 24, 19), _line(24, 0, 24, 40), _line(8, 0, 24, 0),
         '<path d="M9,0 l9,-5 l0,10 Z" fill="#000" stroke-width="1"/>']
    if body_diode:
        g += [_line(24, -30, 42, -30, 1.6), _line(42, -30, 42, 30, 1.6), _line(42, 30, 24, 30, 1.6),
              '<path d="M35,6 L49,6 L42,-6 Z" fill="#fff" stroke-width="1.6"/>', _line(35, -6, 49, -6, 1.6)]
    return g, {"G": (-40, 0), "D": (24, -40), "S": (24, 40)}, (-40, -40, 50 if body_diode else 26, 40)


def sym_pmos(body_diode=False):
    # source on top, drain at bottom
    g = [_line(-40, 0, -2, 0), _line(-2, -20, -2, 20, 2.6),
         _line(8, -26, 8, -12, 3), _line(8, -6, 8, 6, 3), _line(8, 12, 8, 26, 3),
         _line(8, -19, 24, -19), _line(24, -40, 24, 0),
         _line(8, 19, 24, 19), _line(24, 19, 24, 40), _line(8, 0, 24, 0),
         '<path d="M22,0 l-9,-5 l0,10 Z" fill="#000" stroke-width="1"/>']
    if body_diode:
        g += [_line(24, -30, 42, -30, 1.6), _line(42, -30, 42, 30, 1.6), _line(42, 30, 24, 30, 1.6),
              '<path d="M35,-6 L49,-6 L42,6 Z" fill="#fff" stroke-width="1.6"/>', _line(35, 6, 49, 6, 1.6)]
    return g, {"G": (-40, 0), "S": (24, -40), "D": (24, 40)}, (-40, -40, 50 if body_diode else 26, 40)


def sym_npn():
    g = ['<circle cx="10" cy="0" r="27" fill="none" stroke-width="1.6"/>',
         _line(-40, 0, 0, 0), _line(0, -16, 0, 16, 3),
         _line(0, -7, 24, -24), _line(24, -24, 24, -40),
         _line(0, 7, 24, 24), _line(24, 24, 24, 40),
         '<path d="M24,24 l-11,-1 l5,-7 Z" fill="#000" stroke-width="1"/>']
    return g, {"B": (-40, 0), "C": (24, -40), "E": (24, 40)}, (-40, -40, 38, 40)


def sym_siren():
    g = [_line(0, -40, 0, -22), _line(0, 22, 0, 40),
         '<rect x="-10" y="-22" width="20" height="44" fill="#fff"/>',
         '<path d="M10,-12 L28,-26 L28,26 L10,12" fill="#fff"/>',
         '<path d="M34,-12 q8,12 0,24 M40,-18 q12,18 0,36" fill="none" stroke-width="1.6"/>']
    return g, {"1": (0, -40), "2": (0, 40)}, (-10, -40, 50, 40)


def sym_antenna():
    g = [_line(0, 40, 0, -10), '<path d="M0,-10 L-18,-40 L18,-40 Z" fill="none"/>', _line(0, -10, 0, -40)]
    return g, {"1": (0, 40)}, (-18, -40, 18, 40)


def sym_coax():
    g = ['<circle cx="0" cy="0" r="15" fill="none"/>', '<circle cx="0" cy="0" r="4" fill="#000"/>',
         _line(-40, 0, -4, 0), _line(0, 15, 0, 40),
         '<path d="M-13,7 A15,15 0 0 0 13,7" fill="none" stroke-width="3"/>']
    return g, {"SIG": (-40, 0), "GND": (0, 40), "SIGR": (40, 0)}, (-40, -16, 40, 40)


SYMBOLS = {
    "R": sym_res, "C": sym_cap, "CP": sym_cap_pol, "L": sym_ind,
    "D": lambda: sym_diode("d"), "DS": lambda: sym_diode("schottky"),
    "TVS": lambda: sym_diode("tvs"), "LED": lambda: sym_diode("led"),
    "PTC": sym_ptc, "NTC": sym_ntc, "XTAL": sym_xtal,
    "SW": lambda: sym_switch("no"), "SWV": lambda: sym_switch("vib"),
    "REED_NO": lambda: sym_switch("reed_no"), "REED_NC": lambda: sym_switch("reed_nc"),
    "CELL": sym_cell, "NMOS": lambda: sym_nmos(False), "NMOSD": lambda: sym_nmos(True),
    "PMOS": lambda: sym_pmos(False), "PMOSD": lambda: sym_pmos(True), "NPN": sym_npn,
    "SIREN": sym_siren, "ANT": sym_antenna, "COAX": sym_coax,
}


def xform(px, py, x, y, rot, mirror):
    if mirror:
        px = -px
    r = math.radians(rot)
    c, s = round(math.cos(r), 9), round(math.sin(r), 9)
    return (x + px * c - py * s, y + px * s + py * c)


# --------------------------------------------------------------------------
#  Sheet
# --------------------------------------------------------------------------
class Sheet:
    def __init__(self, sid, w=4200, h=2970):
        self.sid = sid
        self.w, self.h = w, h
        self.bg = []        # block frames etc. (below everything)
        self.g = []         # symbols, text
        self.fg = []        # labels (on top)
        self.wires = []     # (pts, dashed)
        self.pins = []      # dict(x,y,ref,pin,name,nc)
        self.anchors = []   # labels / power ports: dict(x,y,name,kind)
        self.nc = []
        self.parts = {}     # ref -> meta dict
        self.pin_index = {}  # (ref,pin) -> (x,y)

    # ---------------- primitives ----------------
    def text(self, x, y, s, size=TXT, anchor="start", weight="normal", color="#000", italic=False,
             layer="g", family=FONT):
        st = ' font-style="italic"' if italic else ""
        el = (f'<text x="{fmt(x)}" y="{fmt(y)}" font-family="{family}" font-size="{size}" '
              f'text-anchor="{anchor}" font-weight="{weight}" fill="{color}"{st}>{esc(s)}</text>')
        getattr(self, layer).append(el)

    def wire(self, *pts, dashed=False):
        pts = [tuple(map(float, p)) for p in pts]
        # drop zero-length steps
        clean = [pts[0]]
        for p in pts[1:]:
            if p != clean[-1]:
                clean.append(p)
        if len(clean) < 2:
            return
        self.wires.append((clean, dashed))

    def hv(self, a, b):
        """L-shaped wire: horizontal first, then vertical."""
        self.wire(a, (b[0], a[1]), b)

    def vh(self, a, b):
        self.wire(a, (a[0], b[1]), b)

    def noconn(self, p):
        x, y = p
        self.nc.append((x, y))
        d = 9
        self.fg.append(f'<path d="M{fmt(x-d)},{fmt(y-d)} L{fmt(x+d)},{fmt(y+d)} M{fmt(x-d)},{fmt(y+d)} '
                       f'L{fmt(x+d)},{fmt(y-d)}" stroke="#000" stroke-width="2.2" fill="none"/>')

    def add_pin(self, ref, pin, x, y, name=""):
        self.pins.append(dict(x=round(x, 2), y=round(y, 2), ref=ref, pin=str(pin), name=name))
        self.pin_index[(ref, str(pin))] = (round(x, 2), round(y, 2))

    def P(self, ref, pin):
        return self.pin_index[(ref, str(pin))]

    def register(self, ref, **meta):
        m = self.parts.setdefault(ref, {})
        m.update(meta)
        m.setdefault("sheet", self.sid)

    # ---------------- discrete parts ----------------
    def part(self, kind, ref, value, x, y, rot=0, mirror=False, lbl="auto", lbl_dx=0, lbl_dy=0,
             value2=None, dnp=False, meta=None, show_ref=True, pin_names=None, size=TXT, inline=False):
        g, pins, bb = SYMBOLS[kind]()
        tr = f"translate({fmt(x)},{fmt(y)}) rotate({rot})" + (" scale(-1,1)" if mirror else "")
        self.g.append(f'<g transform="{tr}" stroke="#000" fill="none" stroke-linecap="round">' + "".join(g) + "</g>")
        out = {}
        for pn, (px, py) in pins.items():
            ax, ay = xform(px, py, x, y, rot, mirror)
            out[pn] = (round(ax, 2), round(ay, 2))
            nm = pin_names.get(pn, pn) if pin_names else pn
            self.add_pin(ref, pn, ax, ay, nm)
        # bounding box after transform
        cs = [xform(bx, by, x, y, rot, mirror) for bx, by in ((bb[0], bb[1]), (bb[2], bb[1]), (bb[0], bb[3]), (bb[2], bb[3]))]
        x0, x1 = min(c[0] for c in cs), max(c[0] for c in cs)
        y0, y1 = min(c[1] for c in cs), max(c[1] for c in cs)
        lines = [ref] if show_ref else []
        if value and inline and show_ref:
            lines = [ref + " " + value]
        elif value:
            lines.append(value)
        if value2:
            lines.append(value2)
        if dnp:
            lines.append("DNP")
        vertical = (rot % 180 == 0)
        if lbl == "auto":
            lbl = "r" if vertical else "t"
        lh = size * 1.12
        n = len(lines)
        if lbl == "r":
            tx, ty, anc = x1 + 8, (y0 + y1) / 2 - (n - 1) * lh / 2 + size * 0.35, "start"
        elif lbl == "l":
            tx, ty, anc = x0 - 8, (y0 + y1) / 2 - (n - 1) * lh / 2 + size * 0.35, "end"
        elif lbl == "t":
            tx, ty, anc = (x0 + x1) / 2, y0 - 8 - (n - 1) * lh, "middle"
        else:  # b
            tx, ty, anc = (x0 + x1) / 2, y1 + 6 + size * 0.8, "middle"
        tx += lbl_dx
        ty += lbl_dy
        for i, s in enumerate(lines):
            bold = "bold" if (i == 0 and show_ref and not inline) else "normal"
            col = "#B00000" if s == "DNP" else "#000"
            self.text(tx, ty + i * lh, s, size=size, anchor=anc, weight=bold, color=col)
        meta = dict(meta or {})
        meta.setdefault("value", value)
        self.register(ref, kind=kind, dnp=dnp, **meta)
        return out

    # ---------------- IC box ----------------
    def ic(self, ref, value, x, y, w, h, pins, value2=None, meta=None, pinlen=30, name_size=PNAME_TXT,
           title_pos="top", dnp=False):
        """pins: list of (side, pos, number, name[, 'nc'])  side in L,R,T,B; pos = offset from
        box top (L/R) or box left (T/B)."""
        self.g.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
                      f'fill="#FFFDF0" stroke="#000" stroke-width="{SW+0.4}"/>')
        out = {}
        for item in pins:
            side, pos, num, name = item[:4]
            nc = len(item) > 4 and item[4] == "nc"
            if side == "L":
                px0, py0, px1, py1 = x, y + pos, x - pinlen, y + pos
                self.text(x + 8, py0 + name_size * 0.35, name, size=name_size)
                self.text(x - 5, py0 - 5, num, size=PIN_TXT, anchor="end", color="#333")
            elif side == "R":
                px0, py0, px1, py1 = x + w, y + pos, x + w + pinlen, y + pos
                self.text(x + w - 8, py0 + name_size * 0.35, name, size=name_size, anchor="end")
                self.text(x + w + 5, py0 - 5, num, size=PIN_TXT, color="#333")
            elif side == "T":
                px0, py0, px1, py1 = x + pos, y, x + pos, y - pinlen
                self.text(px0, y + name_size + 6, name, size=name_size, anchor="middle")
                self.text(px0 + 5, y - 8, num, size=PIN_TXT, color="#333")
            else:
                px0, py0, px1, py1 = x + pos, y + h, x + pos, y + h + pinlen
                self.text(px0, y + h - 9, name, size=name_size, anchor="middle")
                self.text(px0 + 5, y + h + 18, num, size=PIN_TXT, color="#333")
            self.g.append(_line(px0, py0, px1, py1).replace("<line", '<line stroke="#000"'))
            key = str(num)
            self.add_pin(ref, key, px1, py1, name)
            out[key] = (round(px1, 2), round(py1, 2))
            out[name] = out[key]
            if nc:
                self.noconn((px1, py1))
        if title_pos == "top":
            self.text(x, y - 12 - TXT * 1.1, ref, weight="bold")
            self.text(x, y - 12, value)
        elif title_pos == "right":
            self.text(x + w + 16, y + h / 2 - 4, ref, weight="bold")
            self.text(x + w + 16, y + h / 2 - 4 + TXT * 1.1, value)
        elif title_pos == "bottom":
            self.text(x, y + h + 30, ref, weight="bold")
            self.text(x, y + h + 30 + TXT * 1.1, value)
        if value2:
            self.text(x + w / 2, y + h / 2, value2, size=17, anchor="middle", color="#555", italic=True)
        if dnp:
            self.text(x + w, y - 12, "DNP", anchor="end", color="#B00000")
        meta = dict(meta or {})
        meta.setdefault("value", value)
        self.register(ref, kind="IC", dnp=dnp, **meta)
        return out

    # ---------------- connector ----------------
    def conn(self, ref, value, x, y, names, side="R", pitch=40, far=True, w=None, meta=None,
             lbl="t", numbers=None, far_names=None):
        """Vertical connector box. side = side where board pins exit (R or L).
        Far side (cable) stubs on the opposite side get pin ids '<n>k'."""
        n = len(names)
        h = pitch * n
        if w is None:
            w = 26 + max(len(s) for s in names) * 10.5 + 26
        self.g.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
                      f'fill="#F2F5FA" stroke="#000" stroke-width="{SW}"/>')
        out = {}
        for i, nm in enumerate(names):
            num = str(numbers[i]) if numbers else str(i + 1)
            py = y + pitch / 2 + i * pitch
            if side == "R":
                bx, ex, fx0, fx1 = x + w, x + w + 30, x, x - 30
                self.text(x + w - 22, py + 6, nm, size=18, anchor="end")
                self.text(x + 6, py + 6, num, size=PIN_TXT, color="#333")
            else:
                bx, ex, fx0, fx1 = x, x - 30, x + w, x + w + 30
                self.text(x + 22, py + 6, nm, size=18)
                self.text(x + w - 6, py + 6, num, size=PIN_TXT, anchor="end", color="#333")
            self.g.append(f'<line x1="{fmt(bx)}" y1="{fmt(py)}" x2="{fmt(ex)}" y2="{fmt(py)}" stroke="#000" stroke-width="{SW}"/>')
            self.add_pin(ref, num, ex, py, nm)
            out[num] = (ex, py)
            if far:
                self.g.append(f'<line x1="{fmt(fx0)}" y1="{fmt(py)}" x2="{fmt(fx1)}" y2="{fmt(py)}" stroke="#000" '
                              f'stroke-width="{SW}" stroke-dasharray="6,4"/>')
                self.add_pin(ref, num + "k", fx1, py, (far_names[i] if far_names else nm) + " (kablo)")
                out[num + "k"] = (fx1, py)
        if lbl == "t":
            self.text(x + w / 2, y - 12 - TXT * 1.1, ref, weight="bold", anchor="middle")
            self.text(x + w / 2, y - 12, value, anchor="middle", size=18)
        elif lbl == "b":
            self.text(x + w / 2, y + h + 26, ref, weight="bold", anchor="middle")
            self.text(x + w / 2, y + h + 26 + TXT * 1.1, value, anchor="middle", size=18)
        meta = dict(meta or {})
        meta.setdefault("value", value)
        self.register(ref, kind="CONN", dnp=False, **meta)
        return out

    def hconn(self, ref, value, x, y, names, pitch=110, side="T", meta=None, lbl="r", hgt=70):
        """Horizontal connector (pins on top = board, bottom = cable when side='T')."""
        n = len(names)
        w = pitch * n
        self.g.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{hgt}" fill="#F2F5FA" '
                      f'stroke="#000" stroke-width="{SW}"/>')
        out = {}
        for i, nm in enumerate(names):
            num = str(i + 1)
            px = x + pitch / 2 + i * pitch
            self.g.append(f'<line x1="{fmt(px)}" y1="{y}" x2="{fmt(px)}" y2="{y-30}" stroke="#000" stroke-width="{SW}"/>')
            self.g.append(f'<line x1="{fmt(px)}" y1="{y+hgt}" x2="{fmt(px)}" y2="{y+hgt+30}" stroke="#000" '
                          f'stroke-width="{SW}" stroke-dasharray="6,4"/>')
            self.text(px, y + 24, num, size=PIN_TXT, anchor="middle", color="#333")
            self.text(px, y + hgt - 12, nm, size=17, anchor="middle")
            self.add_pin(ref, num, px, y - 30, nm)
            self.add_pin(ref, num + "k", px, y + hgt + 30, nm + " (kablo)")
            out[num] = (px, y - 30)
            out[num + "k"] = (px, y + hgt + 30)
        if lbl == "r":
            self.text(x + w + 14, y + 28, ref, weight="bold")
            self.text(x + w + 14, y + 28 + TXT * 1.1, value, size=18)
        meta = dict(meta or {})
        meta.setdefault("value", value)
        self.register(ref, kind="CONN", dnp=False, **meta)
        return out

    # ---------------- power / labels ----------------
    def pwr(self, p, name, d="up"):
        x, y = p
        self.anchors.append(dict(x=round(x, 2), y=round(y, 2), name=name, kind="power"))
        L = 16
        if d == "up":
            self.fg.append(_line(x, y, x, y - L).replace("<line", '<line stroke="#000"'))
            self.fg.append(_line(x - 17, y - L, x + 17, y - L, 3).replace("<line", '<line stroke="#000"'))
            self.text(x, y - L - 8, name, size=20, anchor="middle", weight="bold", layer="fg")
        elif d == "down":
            self.fg.append(_line(x, y, x, y + L).replace("<line", '<line stroke="#000"'))
            self.fg.append(_line(x - 17, y + L, x + 17, y + L, 3).replace("<line", '<line stroke="#000"'))
            self.text(x, y + L + 22, name, size=20, anchor="middle", weight="bold", layer="fg")
        elif d == "right":
            self.fg.append(_line(x, y, x + L, y).replace("<line", '<line stroke="#000"'))
            self.fg.append(_line(x + L, y - 15, x + L, y + 15, 3).replace("<line", '<line stroke="#000"'))
            self.text(x + L + 7, y + 7, name, size=20, weight="bold", layer="fg")
        else:
            self.fg.append(_line(x, y, x - L, y).replace("<line", '<line stroke="#000"'))
            self.fg.append(_line(x - L, y - 15, x - L, y + 15, 3).replace("<line", '<line stroke="#000"'))
            self.text(x - L - 7, y + 7, name, size=20, weight="bold", anchor="end", layer="fg")

    def gnd(self, p, d="down", name="GND"):
        x, y = p
        self.anchors.append(dict(x=round(x, 2), y=round(y, 2), name=name, kind="power"))
        s = '<g stroke="#000" stroke-width="2.4">'
        if d == "down":
            s += _line(x, y, x, y + 12) + _line(x - 16, y + 12, x + 16, y + 12) + \
                _line(x - 10, y + 18, x + 10, y + 18) + _line(x - 4, y + 24, x + 4, y + 24)
        elif d == "right":
            s += _line(x, y, x + 12, y) + _line(x + 12, y - 16, x + 12, y + 16) + \
                _line(x + 18, y - 10, x + 18, y + 10) + _line(x + 24, y - 4, x + 24, y + 4)
        elif d == "left":
            s += _line(x, y, x - 12, y) + _line(x - 12, y - 16, x - 12, y + 16) + \
                _line(x - 18, y - 10, x - 18, y + 10) + _line(x - 24, y - 4, x - 24, y + 4)
        s += "</g>"
        self.fg.append(s)

    def flag(self, p, name, d="right", note=None, size=19):
        """Global net label. p = connection point; d = direction the flag extends."""
        x, y = p
        self.anchors.append(dict(x=round(x, 2), y=round(y, 2), name=name, kind="label"))
        tw = text_width(name, size) + 16
        hh = 15
        if d == "right":
            pts = [(x, y), (x + 10, y - hh), (x + 10 + tw, y - hh), (x + 10 + tw, y + hh), (x + 10, y + hh)]
            tx, ty, anc = x + 12 + tw / 2, y + 6.5, "middle"
        elif d == "left":
            pts = [(x, y), (x - 10, y - hh), (x - 10 - tw, y - hh), (x - 10 - tw, y + hh), (x - 10, y + hh)]
            tx, ty, anc = x - 12 - tw / 2, y + 6.5, "middle"
        elif d == "up":
            pts = [(x, y), (x + tw / 2, y - 10), (x + tw / 2, y - 10 - 2 * hh), (x - tw / 2, y - 10 - 2 * hh), (x - tw / 2, y - 10)]
            tx, ty, anc = x, y - 10 - hh + 6.5, "middle"
        else:
            pts = [(x, y), (x + tw / 2, y + 10), (x + tw / 2, y + 10 + 2 * hh), (x - tw / 2, y + 10 + 2 * hh), (x - tw / 2, y + 10)]
            tx, ty, anc = x, y + 10 + hh + 6.5, "middle"
        d_ = "M" + " L".join(f"{fmt(a)},{fmt(b)}" for a, b in pts) + " Z"
        self.fg.append(f'<path d="{d_}" fill="#FFFFFF" stroke="#000" stroke-width="1.8"/>')
        self.text(tx, ty, name, size=size, anchor=anc, layer="fg")
        if note:
            if d == "right":
                self.text(x + 16 + tw, y + 6, note, size=16, color="#555", italic=True, layer="fg")
            elif d == "left":
                self.text(x - 16 - tw, y + 6, note, size=16, color="#555", italic=True, anchor="end", layer="fg")
        return tw + 10

    def netname(self, p, name, dx=6, dy=-8, size=16, anchor="start"):
        """Local net label: names the wire it sits on (text only, no flag)."""
        x, y = p
        self.anchors.append(dict(x=round(x, 2), y=round(y, 2), name=name, kind="netname"))
        self.text(x + dx, y + dy, name, size=size, color="#1F4D3A", anchor=anchor, layer="fg", weight="bold")

    def tp(self, p, ref, name, d="right"):
        x, y = p
        self.add_pin(ref, "1", x, y, name)
        self.fg.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="7" fill="#fff" stroke="#000" stroke-width="2"/>')
        if d == "right":
            self.text(x + 14, y + 7, f"{ref} {name}", size=17)
        else:
            self.text(x - 14, y + 7, f"{ref} {name}", size=17, anchor="end")
        self.register(ref, kind="TP", dnp=False, value=name)

    # ---------------- decorations ----------------
    def block(self, x, y, w, h, num, title, color="#1F4D3A"):
        self.bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" '
                       f'stroke-width="3" stroke-dasharray="18,8" rx="6"/>')
        self.bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="40" fill="{color}" rx="6"/>')
        self.bg.append(f'<rect x="{x}" y="{y+20}" width="{w}" height="20" fill="{color}"/>')
        self.bg.append(f'<text x="{x+16}" y="{y+29}" font-family="{FONT}" font-size="24" font-weight="bold" '
                       f'fill="#fff">{esc(str(num) + ")  " + title)}</text>')

    def offboard(self, x, y, w, h, title, tpos="top", fill="#F7F7F7", stroke="#666", dash="10,6", tsize=17):
        self.bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" '
                       f'stroke-width="2" stroke-dasharray="{dash}" rx="10"/>')
        ty = y + 24 if tpos == "top" else y + h - 12
        self.bg.append(f'<text x="{x+10}" y="{ty}" font-family="{FONT}" font-size="{tsize}" font-style="italic" '
                       f'fill="#444">{esc(title)}</text>')

    def revmark(self, x, y, n):
        """Revision delta marker (triangle with number) -> see notes."""
        self.fg.append(f'<path d="M{x},{y-16} L{x+16},{y+12} L{x-16},{y+12} Z" fill="#FFE8E0" stroke="#C0392B" stroke-width="2"/>')
        self.text(x, y + 8, str(n), size=16, anchor="middle", weight="bold", color="#C0392B", layer="fg")

    # ---------------- connectivity ----------------
    def connectivity(self):
        """Return list of point-groups (union-find) with attached pins/anchors."""
        parent = {}

        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        key = lambda x, y: (round(x, 1), round(y, 1))
        segs = []
        for pts, _d in self.wires:
            for i in range(len(pts) - 1):
                a, b = key(*pts[i]), key(*pts[i + 1])
                union(a, b)
                segs.append((a, b))
        hot = set()
        for pts, _d in self.wires:
            hot.add(key(*pts[0]))
            hot.add(key(*pts[-1]))
        for p in self.pins:
            hot.add(key(p["x"], p["y"]))
            find(key(p["x"], p["y"]))
        for a in self.anchors:
            hot.add(key(a["x"], a["y"]))
            find(key(a["x"], a["y"]))
        for n in self.nc:
            find(key(*n))
        # endpoints lying on segments
        deg = defaultdict(int)
        for a, b in segs:
            deg[a] += 1
            deg[b] += 1
        for p in hot:
            for a, b in segs:
                if p == a or p == b:
                    continue
                if on_seg(p, a, b):
                    union(p, a)
                    deg[p] += 2
        for p in self.pins:
            deg[key(p["x"], p["y"])] += 1
        for a in self.anchors:
            if a["kind"] != "netname":
                deg[key(a["x"], a["y"])] += 1
        self._deg = deg
        self._find = find
        self._key = key
        return find, key

    def junctions(self):
        pts = []
        for p, d in self._deg.items():
            if d >= 3:
                pts.append(p)
        return pts

    # ---------------- render ----------------
    def render_body(self):
        out = []
        out += self.bg
        for pts, dashed in self.wires:
            dd = ' stroke-dasharray="8,5" stroke="#555"' if dashed else ' stroke="#000"'
            path = "M" + " L".join(f"{fmt(a)},{fmt(b)}" for a, b in pts)
            out.append(f'<path d="{path}" fill="none" stroke-width="{LW}"{dd} stroke-linejoin="round"/>')
        out += self.g
        for x, y in self.junctions():
            out.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{JR}" fill="#000"/>')
        out += self.fg
        return out


def on_seg(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if ax == bx == px:
        return min(ay, by) < py < max(ay, by)
    if ay == by == py:
        return min(ax, bx) < px < max(ax, bx)
    return False


# --------------------------------------------------------------------------
#  Netlist across sheets
# --------------------------------------------------------------------------
def build_netlist(sheets):
    """Returns (nets: name -> list of (ref,pin,pinname)), problems list)."""
    gid = {}
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    names_at = defaultdict(set)
    members = defaultdict(list)
    problems = []
    for sh in sheets:
        f, key = sh.connectivity()
        for p in sh.pins:
            node = (sh.sid, f(key(p["x"], p["y"])))
            members[node].append((p["ref"], p["pin"], p["name"]))
            find(node)
        for a in sh.anchors:
            node = (sh.sid, f(key(a["x"], a["y"])))
            find(node)
            names_at[node].add(a["name"])
            union(node, ("NAME", a["name"]))
        for n in sh.nc:
            node = (sh.sid, f(key(*n)))
            names_at[node].add("__NC__")
        # dangling wire ends
        for pts, dashed in sh.wires:
            for e in (pts[0], pts[-1]):
                k = key(*e)
                if sh._deg.get(k, 0) < 2:
                    problems.append(f"[{sh.sid}] açık uçlu tel @ {k}")
    groups = defaultdict(lambda: {"names": set(), "pins": []})
    for node, mem in members.items():
        r = find(node)
        groups[r]["pins"] += mem
    for node, nm in names_at.items():
        r = find(node)
        groups[r]["names"] |= nm
    for node in list(parent):
        if isinstance(node, tuple) and node[0] == "NAME":
            r = find(node)
            groups[r]["names"].add(node[1])
    nets = {}
    for r, g in groups.items():
        nm = sorted(n for n in g["names"] if n != "__NC__")
        if len(nm) > 1:
            problems.append(f"Birden fazla isim aynı nette: {nm}")
        if nm:
            name = nm[0]
        else:
            if not g["pins"]:
                continue
            if "__NC__" in g["names"] and len(g["pins"]) <= 1:
                continue
            ref, pin, _ = sorted(g["pins"])[0]
            name = f"N_{ref}_{pin}"
        pins = sorted(set(g["pins"]), key=lambda t: (natkey(t[0]), natkey(t[1])))
        if name in nets:
            nets[name] += pins
        else:
            nets[name] = pins
    for name, pins in nets.items():
        if len(pins) < 2 and not name.startswith("TP"):
            problems.append(f"Tek uçlu net: {name} -> {pins}")
    return nets, problems


def natkey(s):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(s))]
