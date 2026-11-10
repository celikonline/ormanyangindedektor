"""Top silkscreen geometry (stroke polylines) for ON1-DIY."""
import math

from font import text_strokes, text_width

W_LINE = 0.2
W_TEXT = 0.15


def _upright(angle, anchor):
    a = angle % 360
    if 90 < a <= 270:
        a = (a + 180) % 360
        anchor = {"l": "r", "r": "l", "c": "c"}[anchor[0]] + {"b": "t", "t": "b", "m": "m"}[anchor[1]]
    return a, anchor


def dashed(pts, dash=0.6, gap=0.4):
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            continue
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        s = 0.0
        while s < L:
            e = min(L, s + dash)
            out.append([(x1 + ux * s, y1 + uy * s), (x1 + ux * e, y1 + uy * e)])
            s = e + gap
    return out


def comp_text(c, txt, lx, ly, h, anchor, rot):
    x, y = c.xf(lx, ly)
    a = rot + c.rot
    if c.side == "bottom":
        a = -rot + c.rot
    a, anchor = _upright(a, anchor)
    return text_strokes(txt, x, y, h, anchor, a)


def silk_strokes(b, routes, include_refs=True):
    """list of (polyline, width)."""
    out = []
    for c in b.comps:
        for st in c.fp.silk:
            out.append(([c.xf(*p) for p in st], W_LINE))
        for st in c.fp.silk_dashed:
            for seg in dashed([c.xf(*p) for p in st]):
                out.append((seg, W_TEXT))
        for (txt, lx, ly, h, anchor, rot) in c.fp.texts:
            for st in comp_text(c, txt, lx, ly, h, anchor, rot):
                out.append((st, W_TEXT))
        if include_refs and not c.ref.startswith("H"):
            lx, ly, rot = c.fp.ref_pos
            h = 1.15 if not getattr(c.fp, "ref_inside", False) else 1.0
            label = c.ref + ("▼" if c.side == "bottom" else "")
            label = c.ref + (" (ALT)" if c.side == "bottom" else "")
            for st in comp_text(c, label, lx, ly, h, "cm", rot):
                out.append((st, W_TEXT))
    for i, j in enumerate(routes.get("jumpers", [])):
        (x1, y1), (x2, y2) = j["a"], j["b"]
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx_, ny_ = -uy, ux
        for s in (0.45, -0.45):
            out.append(([(x1 + ux * 1.1 + nx_ * s, y1 + uy * 1.1 + ny_ * s),
                         (x2 - ux * 1.1 + nx_ * s, y2 - uy * 1.1 + ny_ * s)], W_TEXT))
        for q in j.get("pts", [])[1:-1]:
            out.append(([(q[0] + nx_ * 1.2, q[1] + ny_ * 1.2), (q[0] - nx_ * 1.2, q[1] - ny_ * 1.2)], W_TEXT))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ang = 0 if abs(uy) < 0.5 else 90
        off = 1.3
        tx, ty = (mx, my + off) if ang == 0 else (mx - off, my)
        for st in text_strokes("J-W%d" % (i + 1), tx, ty, 1.0, "cm", ang):
            out.append((st, W_TEXT))
    for (txt, x, y, h, anchor, rot) in b.silk_texts:
        for st in text_strokes(txt, x, y, h, anchor, rot):
            out.append((st, W_TEXT if h < 1.6 else 0.22))
    for st in b.silk_lines:
        out.append((st, W_LINE))
    return out
