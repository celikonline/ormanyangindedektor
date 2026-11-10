"""Stroke (single-line) font for silkscreen / copper text.

Glyph data: Hershey "futural" (public-domain Hershey fonts, A. V. Hershey 1967),
exported once to hershey_futural.json so the generator has no font dependency.
Turkish letters are composed from the base glyph + extra strokes.
"""
import json
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "hershey_futural.json"), encoding="utf-8") as fh:
    _F = json.load(fh)
_CAP = _F["cap"]          # cap height in font units (21)
_G = _F["glyphs"]

# composed glyphs: base char + extra strokes (font units, baseline 0, cap 21)
_DOTS_HI = [[[5, 25], [5, 26]], [[11, 25], [11, 26]]]
_EXTRA = {
    "Ö": ("O", [[[7, 25], [7, 26]], [[13, 25], [13, 26]]]),
    "Ü": ("U", [[[7, 25], [7, 26]], [[13, 25], [13, 26]]]),
    "İ": ("I", [[[4, 25], [4, 26]]]),
    "Ç": ("C", [[[11, 0], [11, -3], [9, -4]]]),
    "Ş": ("S", [[[10, 0], [10, -3], [8, -4]]]),
    "Ğ": ("G", [[[7, 26], [9, 24], [13, 24], [15, 26]]]),
    "ö": ("o", [[[7, 17], [7, 18]], [[12, 17], [12, 18]]]),
    "ü": ("u", [[[6, 17], [6, 18]], [[12, 17], [12, 18]]]),
    "ç": ("c", [[[10, 0], [10, -3], [8, -4]]]),
    "ş": ("s", [[[9, 0], [9, -3], [7, -4]]]),
    "ğ": ("g", [[[6, 18], [8, 16], [11, 16], [13, 18]]]),
    "ı": ("i", None),           # dotless i: strip the dot (handled below)
    "µ": ("u", [[[4, 14], [4, -7]]]),
    "Ω": ("O", None),
    "°": (" ", [[[3, 21], [5, 21], [6, 20], [6, 18], [5, 17], [3, 17], [2, 18], [2, 20], [3, 21]]]),
    "→": (" ", [[[1, 7], [15, 7]], [[11, 11], [15, 7], [11, 3]]]),
    "−": ("-", []),
}


def _glyph(ch):
    if ch in _G:
        g = _G[ch]
        return g["w"], g["s"]
    if ch in _EXTRA:
        base, extra = _EXTRA[ch]
        w, s = _glyph(base)
        s = [list(x) for x in s]
        if ch == "ı":
            s = [st for st in s if not (len(st) <= 2 and min(p[1] for p in st) > 15)]
        if ch == "Ω":
            # omega: open-bottom O with feet
            s = [[[3, 0], [7, 0], [7, 2], [4, 5], [3, 9], [3, 13], [5, 18], [8, 21], [12, 21], [15, 18],
                  [17, 13], [17, 9], [16, 5], [13, 2], [13, 0], [17, 0]]]
            w = 20
        if extra:
            s = s + extra
        return w, s
    return _glyph("?")


def text_width(s, h):
    sc = h / _CAP
    return sum(_glyph(c)[0] for c in s) * sc


def text_strokes(s, x, y, h, anchor="ml", rot=0, mirror=False):
    """Return list of polylines [(x,y),...] in board mm.

    anchor: two chars, horizontal l/c/r and vertical b/m/t (e.g. 'cm').
    rot: degrees CCW about the anchor point. mirror: mirror X (for bottom-side text).
    """
    sc = h / _CAP
    w = text_width(s, h)
    ha, va = anchor[0], anchor[1]
    ox = {"l": 0, "c": -w / 2, "r": -w}[ha]
    oy = {"b": 0, "m": -h / 2, "t": -h}[va]
    out = []
    cx = 0.0
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for c in s:
        gw, strokes = _glyph(c)
        for st in strokes:
            pts = []
            for px, py in st:
                lx = ox + cx + px * sc
                ly = oy + py * sc
                if mirror:
                    lx = -lx
                pts.append((x + lx * ca - ly * sa, y + lx * sa + ly * ca))
            if len(pts) >= 2:
                out.append(pts)
        cx += gw * sc
    return out
