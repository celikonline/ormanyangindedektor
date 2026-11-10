"""GND bus wire: after signal routing, find one straight top-side wire (2.54 mm tap pitch)
that crosses as many isolated GND pour islands as possible, place a solder tap inside each
island it crosses, then ground whatever is left through the normal GND phase.

    python gnd_bus.py in.json out.json
"""
import json
import math
import sys

from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

import design
import copper
import route as R_

PITCH = 2.54
TAP_R = 0.9


def strip_gnd_phase(routes):
    hand = {(t["net"], tuple(map(tuple, t["pts"]))) for t in
            [dict(net=n, pts=p) for n, w, p in design.HAND_ROUTES]}
    tracks = [t for t in routes["tracks"] if t["net"] != "GND" or (t["net"], tuple(map(tuple, t["pts"]))) in hand]
    jumpers = [j for j in routes["jumpers"] if j["net"] != "GND" or j.get("hand")]
    return dict(tracks=tracks, jumpers=jumpers)


def forbidden_geometry(b, routes):
    parts = []
    for c in b.comps:
        cp = c.court_poly()
        if cp and not c.fp.raised and not getattr(c.fp, "low_profile_ok", False):
            parts.append(box(min(p[0] for p in cp), min(p[1] for p in cp),
                             max(p[0] for p in cp), max(p[1] for p in cp)))
    holes = []
    for it in copper.pad_items(b, routes):
        if it["drill"]:
            holes.append((it["x"], it["y"], it["drill"]))
    for c in b.comps:
        for (hx, hy, d) in c.fp.npth:
            x, y = c.xf(hx, hy)
            holes.append((x, y, d))
    for (x, y, d) in holes:
        parts.append(Point(x, y).buffer(d / 2 + 0.6, quad_segs=8))
    for j in routes["jumpers"]:
        parts.append(LineString([j["a"], j["b"]]).buffer(1.0))
    return unary_union(parts), holes


def find_bus(b, routes, verbose=True):
    geoms = copper.net_geometries(b, routes, with_pour=False)
    pour = copper.make_pour(b, routes, geoms)
    gnd = unary_union([geoms.get("GND"), pour])
    isl = list(getattr(gnd, "geoms", [gnd]))
    main_i = max(range(len(isl)), key=lambda i: isl[i].area)
    # islands joined already through module links / hand jumpers count as one: approximate by pads
    shrunk = [g.buffer(-(TAP_R + 0.05)) for g in isl]
    forb, holes = forbidden_geometry(b, routes)
    from shapely.prepared import prep
    forb_p = prep(forb)
    foreign = unary_union([g for n, g in geoms.items() if n != "GND"])
    from shapely.prepared import prep as _prep
    foreign_p = _prep(foreign)
    best = None
    for orient in ("h", "v"):
        span = b.h if orient == "h" else b.w
        other = b.w if orient == "h" else b.h
        steps = int((span - 8) / 0.254)
        for k in range(steps):
            c = 4 + k * 0.254
            # candidate tap sites along the full line, on a 2.54 grid with arbitrary phase
            for phase in (0.0, 0.635, 1.27, 1.905):
                sites = []
                t = 3.0 + phase
                while t < other - 3.0:
                    p = (t, c) if orient == "h" else (c, t)
                    sites.append(p)
                    t += PITCH
                good = []
                for p in sites:
                    P = Point(p)
                    for i, g in enumerate(shrunk):
                        if not g.is_empty and g.contains(P):
                            if all(math.hypot(p[0] - x, p[1] - y) - d / 2 - 0.4 >= 0.6 for (x, y, d) in holes):
                                if not foreign_p.intersects(P.buffer(TAP_R + 0.55)):
                                    good.append((p, i))
                            break
                if not good:
                    continue
                # choose the longest clear run of the line containing taps from many islands
                good.sort(key=lambda q: q[0][0] if orient == "h" else q[0][1])
                n = len(good)
                for a in range(n):
                    seen = {}
                    for e in range(a, n):
                        p0, p1 = good[a][0], good[e][0]
                        line = LineString([p0, p1]) if p0 != p1 else Point(p0)
                        body = line.buffer(0.5)
                        if forb_p.intersects(body):
                            break
                        seen.setdefault(good[e][1], good[e][0])
                        islands = set(seen.keys())
                        score = len(islands) if main_i in islands else len(islands) - 1
                        length = line.length if p0 != p1 else 0
                        if len(islands) >= 2 and (best is None or (score, -length) > (best[0], -best[1])):
                            taps = sorted(seen.values(), key=lambda q: q[0] if orient == "h" else q[1])
                            # endpoints of the wire = first and last tap; all taps on the 2.54 grid
                            best = (score, length, orient, c, taps)
    if verbose and best:
        print("GND bus: orient=%s at %.2f, islands=%d, taps=%s" % (best[2], best[3], best[0],
                                                                    [(round(x, 2), round(y, 2)) for x, y in best[4]]))
    return best


def main():
    src, dst = sys.argv[1], sys.argv[2]
    routes = json.load(open(src))
    routes = strip_gnd_phase(routes)
    b = design.build()
    best = find_bus(b, routes)
    r = R_.setup(b)
    for t in routes["tracks"]:
        r.add_track(t)
    for j in routes["jumpers"]:
        r.add_jumper(j)
    if best:
        taps = [tuple(p) for p in best[4]]
        r.add_jumper(dict(net="GND", a=taps[0], b=taps[-1], pts=taps, bus=True))
    gf = R_.gnd_phase(b, r)
    data = dict(tracks=r.tracks, jumpers=r.jumpers, failures=gf)
    json.dump(data, open(dst, "w"), indent=0)
    print("RESULT jumpers=%d gnd_failures=%d" % (len(r.jumpers), len(gf)))


if __name__ == "__main__":
    main()
