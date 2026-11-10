"""Routing driver: builds the router from design.py, routes every net in stages,
then grounds everything through the GND pour (joining pour islands with tracks
or wire jumpers). Writes routes.json.

    python route.py            # route with the default order
    python route.py --seed N   # shuffled order inside each stage (exploration)
"""
import json
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Point
from shapely.ops import unary_union

import design
import copper
from router import Router, F, G
from font import text_strokes

HERE = os.path.dirname(os.path.abspath(__file__))
ROUTES = os.path.join(HERE, "routes.json")

POWER_NETS = ["SOL_IN", "SOL_P", "PACK_P", "CELL_N", "VBAT", "VMODEM", "LED_K",
              "LED_A1", "LED_A2", "LED_A3", "LED_A4", "LED_A5", "LED_A6", "SIR_VIN"]
ROOTS = {"VBAT": ("F1", "2"), "GND": ("U5", "P-"), "+3V3": ("U6", "VOUT"), "PACK_P": ("J3", "2"),
         "SOL_P": ("D1", "K"), "VMODEM": ("Q1", "D"), "LED_K": ("Q3", "D"), "V_SNS": ("Q2", "D")}


def setup(b):
    nets = sorted(b.nets().keys())
    net_ids = {n: i for i, n in enumerate(nets)}
    r = Router(b, net_ids)
    nid = len(nets) + 10
    for c in b.comps:
        for p, x, y, w, h, net in c.pads():
            if net is None:
                net = "NC_%s_%s" % (c.ref, p.name)
                net_ids[net] = nid
                nid += 1
            r.paint_pad(x, y, w, h, p.shape, net_ids[net])
            if p.drill:
                r.add_hole(x, y, p.drill)
        for (hx, hy, d) in c.fp.npth:
            x, y = c.xf(hx, hy)
            r.add_hole(x, y, d)
        for (kx, ky, kr) in c.fp.keepout:
            x, y = c.xf(kx, ky)
            r.paint_pad(x, y, 2 * kr, 2 * kr, "C", r.KEEP)
        cp = c.court_poly()
        if cp:
            r.add_courtyard(cp, c.fp.raised, getattr(c.fp, "low_profile_ok", False))
    for (txt, x, y, h, anchor, rot) in b.copper_texts:
        for st in text_strokes(txt, x, y, h, anchor, rot):
            for a, b_ in zip(st, st[1:]):
                r.paint_segment(a, b_, copper.TEXT_W, r.KEEP)
        # keep the text area clear of jumpers too
    return r


def group_pads(b, pads):
    links = b.internal_links()
    key = lambda pd: (pd["ref"], pd["pad"])
    parent = {key(p): key(p) for p in pads}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    for a, c in links:
        if a in parent and c in parent:
            parent[find(a)] = find(c)
    groups = {}
    for p in pads:
        groups.setdefault(find(key(p)), []).append(p)
    return list(groups.values())


def stage_of(net, pd):
    k = (pd["ref"], pd["pad"])
    if net in POWER_NETS:
        return 2 if pd["ref"] in design.SMALL_TAP_REFS else 0
    if net == "+3V3":
        return 2
    return 1


def route_nets(b, r, seed=None, verbose=True):
    nets = {n: p for n, p in b.nets().items() if n != "GND"}
    state = {}
    for net, pads in nets.items():
        groups = group_pads(b, pads)
        root = ROOTS.get(net)
        gi = 0
        if root:
            for i, g in enumerate(groups):
                if any((p["ref"], p["pad"]) == root for p in g):
                    gi = i
        hand = [t for t in r.tracks if t["net"] == net]
        tree = r.tree_mask_from(net, groups[gi], hand)
        conn = {gi}
        changed = True
        while changed:
            changed = False
            for i, g in enumerate(groups):
                if i in conn:
                    continue
                if any((r.cells_in_pad(p, 0.3) & tree).any() for p in g):
                    conn.add(i)
                    tree |= r.tree_mask_from(net, g, [])
                    changed = True
        state[net] = dict(groups=groups, connected=conn, tree=tree)
    failures = []
    hint = getattr(design, "ROUTE_ORDER", [])
    rng = random.Random(seed)
    t0 = time.time()
    for stage in range(3):
        order = sorted(nets.keys(), key=lambda n: (hint.index(n) if n in hint else 999, n))
        if seed is not None:
            order = sorted(order, key=lambda n: (hint.index(n) if n in hint else 999) + rng.random() * 40)
        for net in order:
            st = state[net]
            while True:
                todo = [i for i, g in enumerate(st["groups"]) if i not in st["connected"]
                        and min(stage_of(net, p) for p in g) <= stage]
                if not todo:
                    break
                ty, tx = np.nonzero(st["tree"])
                txy = np.stack([tx * G, ty * G], axis=1)
                best = None
                for i in todo:
                    for p in st["groups"][i]:
                        d = np.min((txy[:, 0] - p["x"]) ** 2 + (txy[:, 1] - p["y"]) ** 2)
                        if best is None or d < best[0]:
                            best = (d, i, p)
                _, gi, pad = best
                w = design.pad_width(b, pad["ref"], pad["pad"], net)
                res = r.route_connection(net, pad, st["tree"], w / 2)
                if res is None and w > design.W_MID:
                    res = r.route_connection(net, pad, st["tree"], design.W_MID / 2)
                st["connected"].add(gi)
                if res is None:
                    failures.append((net, pad["ref"], pad["pad"]))
                    if verbose:
                        print("  FAIL", net, pad["ref"], pad["pad"], flush=True)
                    continue
                tracks, jumps = res
                add = r.tree_mask_from(net, st["groups"][gi], tracks)
                for j in jumps:
                    for pnt in (j["a"], j["b"]):
                        add |= r.cells_in_pad(dict(x=pnt[0], y=pnt[1], w=1.8, h=1.8, shape="C"), 0.05)
                st["tree"] |= add
                if verbose and jumps:
                    print("  jumper on", net, "->", pad["ref"], pad["pad"], [(j["a"], j["b"]) for j in jumps], flush=True)
        if verbose:
            print("stage", stage, "%.0fs jumpers=%d failures=%d" % (time.time() - t0, len(r.jumpers), len(failures)), flush=True)
    return failures


def raster_geom(r, geom, fine=False):
    """bool mask of cells whose centre lies inside geom (routing grid or fine grid)."""
    pitch = F if fine else G
    nx, ny = (r.nfx, r.nfy) if fine else (r.nx, r.ny)
    im = Image.new("L", (nx, ny), 0)
    d = ImageDraw.Draw(im)
    polys = sorted(getattr(geom, "geoms", [geom]), key=lambda p: -p.area)
    for p in polys:
        if p.is_empty:
            continue
        d.polygon([(x / pitch, y / pitch) for x, y in p.exterior.coords], fill=1)
        for h in p.interiors:
            d.polygon([(x / pitch, y / pitch) for x, y in h.coords], fill=0)
    return np.array(im, dtype=bool)


def jumper_links(jumpers):
    out = []
    for k, j in enumerate(jumpers):
        n = len(j.get("pts", [j["a"], j["b"]]))
        for i in range(1, n):
            out.append((("J-W%d" % (k + 1), str(i)), ("J-W%d" % (k + 1), str(i + 1))))
    return out


def gnd_phase(b, r, verbose=True, max_iter=40):
    """Ground through the pour: route GND pads that are not in the main pour island."""
    failures = []
    skip = set()
    for it in range(max_iter):
        routes = dict(tracks=r.tracks, jumpers=r.jumpers)
        geoms = copper.net_geometries(b, routes, with_pour=False)
        pour = copper.make_pour(b, routes, geoms)
        gnd = unary_union([geoms.get("GND"), pour])
        isl = list(getattr(gnd, "geoms", [gnd]))
        # union-find islands through module-internal links and jumpers
        items = [x for x in copper.pad_items(b, routes) if x["net"] == "GND"]
        par = list(range(len(isl)))

        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        loc = {}
        for x in items:
            p = Point(x["x"], x["y"])
            for i, g in enumerate(isl):
                if g.covers(p):
                    loc[(x["ref"], x["pad"])] = i
                    break
        links = list(b.internal_links()) + jumper_links(r.jumpers)
        for a, c in links:
            if a in loc and c in loc:
                par[find(loc[a])] = find(loc[c])
        main = find(loc[("U5", "P-")])
        comps = {}
        for i in range(len(isl)):
            comps.setdefault(find(i), []).append(i)
        others = [k for k in comps if k != main and k not in skip]
        if not others:
            break
        # paint pour as GND copper for the router
        gid = r.net_ids["GND"]
        pm = raster_geom(r, pour, fine=True)
        r.occ[pm & (r.occ < 0)] = gid
        main_geom = unary_union([isl[i] for i in comps[main]])
        tree = raster_geom(r, main_geom.buffer(-0.05))
        # nearest other component first
        best = None
        for k in others:
            g = unary_union([isl[i] for i in comps[k]])
            d = g.distance(main_geom)
            if best is None or d < best[0]:
                best = (d, k, g)
        _, k, g = best
        src = raster_geom(r, g.buffer(-0.05))
        if not src.any():
            c = g.representative_point()
            src = r.cells_in_pad(dict(x=c.x, y=c.y, w=0.6, h=0.6, shape="C"), 0)
        res = r.route_connection("GND", None, tree, design.W_PWR / 2, src=src)
        if res is None:
            res = r.route_connection("GND", None, tree, design.W_SIG / 2, src=src)
        names = [ "%s.%s" % key for key, i in loc.items() if find(i) == k]
        if res is None:
            failures.append(("GND", names))
            skip.add(k)
            if verbose:
                print("  GND FAIL", names, flush=True)
            continue
        if verbose:
            print("  GND join", names[:6], "jumpers:", len(res[1]), flush=True)
    return failures


def add_hand_routes(b, r):
    for net, w, pts in getattr(design, "HAND_ROUTES", []):
        r.add_track(dict(net=net, w=w, pts=[tuple(p) for p in pts]))
    for net, pts in getattr(design, "HAND_JUMPERS", []):
        pts = [tuple(p) for p in pts]
        r.add_jumper(dict(net=net, a=pts[0], b=pts[-1], pts=pts, hand=True))


def route_all(b, seed=None, verbose=True):
    r = setup(b)
    add_hand_routes(b, r)
    t0 = time.time()
    f1 = route_nets(b, r, seed, verbose)
    f2 = gnd_phase(b, r, verbose)
    if verbose:
        print("total %.0fs" % (time.time() - t0))
    return r, f1 + f2


def main():
    seed = None
    out = ROUTES
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    b = design.build()
    r, failures = route_all(b, seed)
    data = dict(tracks=r.tracks, jumpers=r.jumpers, failures=failures, seed=seed)
    with open(out, "w") as fh:
        json.dump(data, fh, indent=0)
    print("RESULT seed=%s tracks=%d jumpers=%d failures=%d" % (seed, len(r.tracks), len(r.jumpers), len(failures)))


if __name__ == "__main__":
    main()
