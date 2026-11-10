"""Exact (vector) copper geometry with shapely: pads, tracks, jumper pads, copper text,
GND pour with thermal reliefs, design-rule check and connectivity check.

The connectivity check is built from the copper geometry itself: all copper is
unioned into islands without looking at net names; afterwards every pad is
located in an island and the result is compared with the intended netlist.
Only wire jumpers and module-internal links (e.g. the two GND pins of the Pro
Mini, which are joined on the module) are added as explicit connections.
"""
import math
from collections import defaultdict

from shapely.geometry import Point, Polygon, LineString, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from shapely.strtree import STRtree

import design
from font import text_strokes

POUR_CLR = 0.6
POUR_EDGE = 1.0
POUR_MIN = 0.45         # pour features narrower than this are removed
THERMAL_GAP = 0.5
SPOKE_W = 0.8
DRC_CLR = 0.5
EDGE_CLR = 1.0
TEXT_W = 0.35
QS = 12                 # quad segments for circles


def pad_poly(x, y, w, h, shape):
    if shape == "C":
        return Point(x, y).buffer(w / 2, quad_segs=QS)
    if shape == "R":
        return box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if w >= h:
        r = h / 2
        return LineString([(x - (w / 2 - r), y), (x + (w / 2 - r), y)]).buffer(r, quad_segs=QS)
    r = w / 2
    return LineString([(x, y - (h / 2 - r)), (x, y + (h / 2 - r))]).buffer(r, quad_segs=QS)


def track_poly(pts, w):
    if len(pts) == 1:
        return Point(pts[0]).buffer(w / 2, quad_segs=QS)
    return LineString(pts).buffer(w / 2, quad_segs=QS)


def copper_text_polys(b):
    out = []
    for (txt, x, y, h, anchor, rot) in b.copper_texts:
        for st in text_strokes(txt, x, y, h, anchor, rot):
            out.append(LineString(st).buffer(TEXT_W / 2, quad_segs=6))
    return unary_union(out) if out else None


def pad_items(b, routes):
    """list of dict(ref,pad,x,y,net,poly,drill) incl. jumper pads (ref J-Wn)."""
    items = []
    for pd in b.all_pads():
        items.append(dict(ref=pd["ref"], pad=pd["pad"], x=pd["x"], y=pd["y"], net=pd["net"],
                          drill=pd["drill"], poly=pad_poly(pd["x"], pd["y"], pd["w"], pd["h"], pd["shape"]),
                          shape=pd["shape"], w=pd["w"], h=pd["h"]))
    for i, j in enumerate(routes.get("jumpers", [])):
        for k, p in [(str(n + 1), q) for n, q in enumerate(j.get("pts", [j["a"], j["b"]]))]:
            items.append(dict(ref="J-W%d" % (i + 1), pad=k, x=p[0], y=p[1], net=j["net"], drill=1.0,
                              poly=pad_poly(p[0], p[1], 1.8, 1.8, "C"), shape="C", w=1.8, h=1.8))
    return items


def net_geometries(b, routes, with_pour=True):
    """dict net -> geometry (unioned). NC pads get unique names, text -> '_TEXT', keepouts '_KEEP'."""
    parts = defaultdict(list)
    for it in pad_items(b, routes):
        n = it["net"] or "NC:%s.%s" % (it["ref"], it["pad"])
        parts[n].append(it["poly"])
    for t in routes.get("tracks", []):
        parts[t["net"]].append(track_poly(t["pts"], t["w"]))
    tx = copper_text_polys(b)
    geoms = {n: unary_union(v) for n, v in parts.items()}
    if tx is not None:
        geoms["_TEXT"] = tx
    if with_pour and routes.get("pour") is not False:
        pour = make_pour(b, routes, geoms)
        geoms["GND"] = unary_union([geoms.get("GND", Polygon()), pour])
    return geoms


def keepouts(b):
    out = []
    for c in b.comps:
        for (kx, ky, kr) in c.fp.keepout:
            x, y = c.xf(kx, ky)
            out.append(Point(x, y).buffer(kr, quad_segs=QS))
        for (hx, hy, d) in c.fp.npth:
            x, y = c.xf(hx, hy)
            out.append(Point(x, y).buffer(d / 2 + 0.6, quad_segs=QS))
    return unary_union(out) if out else Polygon()


def make_pour(b, routes, geoms, net="GND"):
    area = Polygon(b.outline()).buffer(-POUR_EDGE)
    foreign = unary_union([g for n, g in geoms.items() if n != net])
    allowed = area.difference(foreign.buffer(POUR_CLR, quad_segs=8)).difference(keepouts(b))
    gpads = [it for it in pad_items(b, routes) if it["net"] == net and it["drill"]]
    cut = unary_union([it["poly"].buffer(THERMAL_GAP, quad_segs=8) for it in gpads]) if gpads else Polygon()
    pour = allowed.difference(cut)
    # remove slivers / thin necks
    pour = pour.buffer(-POUR_MIN / 2, quad_segs=4).buffer(POUR_MIN / 2, quad_segs=4).intersection(allowed)
    spokes = []
    for it in gpads:
        r = max(it["w"], it["h"]) / 2 + THERMAL_GAP + 0.7
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ln = LineString([(it["x"], it["y"]), (it["x"] + dx * r, it["y"] + dy * r)])
            spokes.append(ln.buffer(SPOKE_W / 2, cap_style="flat"))
    if spokes:
        sp = unary_union(spokes).intersection(allowed)
        # keep only spokes that actually touch the pour (avoid dangling stubs)
        keep = []
        for g in getattr(sp, "geoms", [sp]):
            if g.area > 0 and g.buffer(0.01).intersects(pour):
                keep.append(g)
        pour = unary_union([pour] + keep)
    # drop pour islands that touch no GND copper (pads, tracks, spokes)
    gnd_cu = geoms.get(net, Polygon())
    pieces = list(getattr(pour, "geoms", [pour]))
    pieces = [p for p in pieces if p.area > 0.5 and p.buffer(0.01).intersects(gnd_cu)]
    return unary_union(pieces) if pieces else Polygon()


# ------------------------------------------------------------------ checks
def drc(b, routes, geoms=None):
    """returns dict with violations lists"""
    if geoms is None:
        geoms = net_geometries(b, routes)
    names = list(geoms.keys())
    tree = STRtree([geoms[n] for n in names])
    viol = []
    mind = {}
    for i, n in enumerate(names):
        g = geoms[n]
        for j in tree.query(g.buffer(DRC_CLR + 0.05)):
            if j <= i:
                continue
            m = names[j]
            if n.startswith("NC:") and m.startswith("NC:") and n.split(".")[0] == m.split(".")[0]:
                pass
            d = g.distance(geoms[m])
            key = tuple(sorted((n, m)))
            mind[key] = d
            if d < DRC_CLR - 1e-6:
                p1 = g.buffer(DRC_CLR / 2).intersection(geoms[m].buffer(DRC_CLR / 2))
                c = p1.centroid if not p1.is_empty else None
                viol.append((n, m, round(d, 3), (round(c.x, 2), round(c.y, 2)) if c else None))
    # edge clearance
    edge = Polygon(b.outline()).exterior
    edge_viol = []
    for n, g in geoms.items():
        d = g.distance(edge)
        if d < EDGE_CLR - 0.02:
            edge_viol.append((n, round(d, 3)))
    # track widths
    width_viol = []
    for t in routes.get("tracks", []):
        if t["w"] < design.W_SIG - 1e-6:
            width_viol.append((t["net"], t["w"]))
    # hole spacing (edge to edge >= 0.5)
    holes = [(it["x"], it["y"], it["drill"], it["ref"], it["pad"]) for it in pad_items(b, routes) if it["drill"]]
    for c in b.comps:
        for (hx, hy, d) in c.fp.npth:
            x, y = c.xf(hx, hy)
            holes.append((x, y, d, c.ref, "npth"))
    hole_viol = []
    for i in range(len(holes)):
        for k in range(i + 1, len(holes)):
            a, c = holes[i], holes[k]
            dd = math.hypot(a[0] - c[0], a[1] - c[1]) - a[2] / 2 - c[2] / 2
            if dd < 0.5:
                hole_viol.append((a[3] + "." + a[4], c[3] + "." + c[4], round(dd, 3)))
    min_clear = min(mind.values()) if mind else None
    return dict(clearance=viol, edge=edge_viol, width=width_viol, holes=hole_viol, min_clearance=min_clear)


def connectivity(b, routes, geoms=None):
    """Geometry-based connectivity: union of ALL copper -> islands; locate pads."""
    if geoms is None:
        geoms = net_geometries(b, routes)
    allcu = unary_union(list(geoms.values()))
    islands = list(getattr(allcu, "geoms", [allcu]))
    tree = STRtree(islands)
    items = pad_items(b, routes)
    parent = {}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a, c):
        parent[find(a)] = find(c)
    pad_island = {}
    for it in items:
        p = Point(it["x"], it["y"])
        cand = [i for i in tree.query(p) if islands[i].covers(p)]
        isl = cand[0] if cand else None
        key = (it["ref"], it["pad"])
        pad_island[key] = isl
        parent[key] = key
        if isl is not None:
            ik = ("_island", isl)
            parent.setdefault(ik, ik)
            union(key, ik)
    netof_pre = {(it["ref"], it["pad"]): it["net"] for it in items}
    links = list(b.internal_links())
    for i, j in enumerate(routes.get("jumpers", [])):
        n = len(j.get("pts", [j["a"], j["b"]]))
        for t in range(1, n):
            links.append((("J-W%d" % (i + 1), str(t)), ("J-W%d" % (i + 1), str(t + 1))))
    for a, c in links:
        if a in parent and c in parent and netof_pre.get(a) and netof_pre.get(c):
            union(a, c)
    groups = defaultdict(set)
    netof = {}
    for it in items:
        key = (it["ref"], it["pad"])
        groups[find(key)].add(it["net"] or "NC:%s.%s" % key)
        netof[key] = it["net"]
    shorts = []
    for v in groups.values():
        real = [x for x in v if not x.startswith("NC:")]
        if len(real) > 1 or (len(real) == 1 and len(v) > 1):
            shorts.append(sorted(v))
    opens = []
    by_net = defaultdict(set)
    for it in items:
        if it["net"]:
            by_net[it["net"]].add(find((it["ref"], it["pad"])))
    for n, s in by_net.items():
        if len(s) > 1:
            parts = defaultdict(list)
            for it in items:
                if it["net"] == n:
                    parts[find((it["ref"], it["pad"]))].append("%s.%s" % (it["ref"], it["pad"]))
            opens.append((n, list(parts.values())))
    return dict(islands=len(islands), nets=len(by_net), shorts=shorts, opens=opens,
                links=len(links))
