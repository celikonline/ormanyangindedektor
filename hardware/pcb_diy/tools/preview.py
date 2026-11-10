"""Quick development preview: placement, courtyards, ratsnest and (optional) routes."""
import json
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

import design
from font import text_strokes

S = 10  # px / mm
GRID = False


def render(b, routes=None, out="preview.png", ratsnest=True):
    W, H = int(b.w * S) + 1, int(b.h * S) + 1
    im = Image.new("RGB", (W, H), (245, 245, 235))
    d = ImageDraw.Draw(im)
    T = lambda x, y: (x * S, (b.h - y) * S)
    d.polygon([T(*p) for p in b.outline()], outline=(0, 0, 0))
    if GRID:
        for gx in range(0, int(b.w) + 1, 5):
            d.line([T(gx, 0), T(gx, b.h)], fill=(225, 225, 210) if gx % 10 else (200, 200, 180))
            d.text(T(gx + 0.2, b.h - 0.3), str(gx), fill=(150, 0, 0))
            d.text(T(gx + 0.2, 1.5), str(gx), fill=(150, 0, 0))
        for gy in range(0, int(b.h) + 1, 5):
            d.line([T(0, gy), T(b.w, gy)], fill=(225, 225, 210) if gy % 10 else (200, 200, 180))
            d.text(T(0.3, gy + 0.9), str(gy), fill=(150, 0, 0))
            d.text(T(b.w - 3, gy + 0.9), str(gy), fill=(150, 0, 0))
    for c in b.comps:
        cp = c.court_poly()
        if cp:
            d.polygon([T(*p) for p in cp], outline=(150, 150, 255))
        for st in c.fp.silk + c.fp.silk_dashed:
            d.line([T(*c.xf(*p)) for p in st], fill=(120, 120, 120))
        x, y = c.xf(*c.fp.ref_pos[:2])
        for st in text_strokes(c.ref, x, y, 1.3, "cm", c.fp.ref_pos[2] + (c.rot if c.rot in (90, 270) else 0)):
            d.line([T(*p) for p in st], fill=(0, 0, 160), width=1)
    if routes:
        for t in routes.get("tracks", []):
            d.line([T(*p) for p in t["pts"]], fill=(200, 120, 0), width=max(1, int(t["w"] * S)))
        for j in routes.get("jumpers", []):
            d.line([T(*j["a"]), T(*j["b"])], fill=(255, 0, 255), width=3)
    for pd in b.all_pads():
        x, y = T(pd["x"], pd["y"])
        w, h = pd["w"] * S / 2, pd["h"] * S / 2
        col = (60, 160, 60) if pd["net"] else (180, 180, 180)
        if pd["smd"]:
            col = (60, 120, 200)
        if pd["shape"] == "C":
            d.ellipse([x - w, y - h, x + w, y + h], fill=col)
        else:
            d.rectangle([x - w, y - h, x + w, y + h], fill=col)
    if ratsnest:
        for net, pads in b.nets().items():
            if len(pads) < 2:
                continue
            # simple MST
            done = [pads[0]]
            rest = pads[1:]
            while rest:
                best = None
                for p in rest:
                    for q in done:
                        dd = math.hypot(p["x"] - q["x"], p["y"] - q["y"])
                        if best is None or dd < best[0]:
                            best = (dd, p, q)
                _, p, q = best
                d.line([T(p["x"], p["y"]), T(q["x"], q["y"])],
                       fill=(255, 0, 0) if net in ("VBAT", "GND") else (230, 60, 200) if net == "+3V3" else (0, 150, 220), width=1)
                done.append(p)
                rest.remove(p)
    im.save(out)
    return out


if __name__ == "__main__":
    b = design.build()
    routes = None
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        routes = json.load(open(sys.argv[2]))
    if "--grid" in sys.argv:
        GRID = True
        S = 13
    render(b, routes, sys.argv[1] if len(sys.argv) > 1 else "preview.png", ratsnest=routes is None and "--nonet" not in sys.argv)
