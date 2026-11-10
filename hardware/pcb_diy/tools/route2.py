"""Shortest-connection-first router.

Every net (GND included) is decomposed into minimum-spanning-tree edges between
its pad groups; all edges of all nets are routed in ascending length order
(with a small random jitter for exploration). Each edge connects the two
current copper components of its net, so later edges may land anywhere on
already-routed copper. Wire jumpers are used by A* only when cheaper than any
detour. Hand-routed power skeleton (design.HAND_ROUTES) is laid down first.

    python route2.py --seed N --out file.json
"""
import json
import math
import os
import random
import sys
import time

import numpy as np

import design
import route as R_
import negotiate as NG
from router import G, CLEARANCE, SLACK, EDGE_CLR, simplify
from scipy import ndimage

HALO = 1.2      # mm beyond the clearance where a track pays extra
HALO_COST = 1.5


def connect_cost(r, net, src_mask, tree, hw, allow_j=True):
    """route_connection with a halo cost around foreign copper (keeps escape channels open)."""
    nid = r.net_ids[net]
    dist = r.dist_foreign(nid)
    need = hw + CLEARANCE + SLACK
    free = (dist >= need) & (r.edge_dist >= hw + EDGE_CLR)
    src = src_mask & free
    if not src.any():
        src = src_mask & (dist >= hw + CLEARANCE * 0.5)
        if not src.any():
            return None
        free = free | src
    target = tree & free
    if not target.any():
        target = tree & (dist >= hw + CLEARANCE * 0.5)
        free = free | target
    cellcost = 1.0 + HALO_COST * ((dist < need + HALO) & ~tree)
    hdist = ndimage.distance_transform_edt(~tree)
    jpad = jline = None
    if allow_j:
        jpad = r.jumper_pad_ok(dist) & free
        body = r.court | r.jbody
        rc = np.cumsum(body, axis=1)
        cc = np.cumsum(body, axis=0)

        def jline(ix, iy, jx, jy):
            if iy == jy:
                a, b_ = sorted((ix, jx))
                return rc[iy, b_] - (rc[iy, a - 1] if a > 0 else 0) == 0
            a, b_ = sorted((iy, jy))
            return cc[b_, ix] - (cc[a - 1, ix] if a > 0 else 0) == 0
    path = NG.NRouter.astar_c(r, free, np.flatnonzero(src.ravel()).tolist(), target, hdist, cellcost, jpad, jline)
    if path is None:
        return None
    return r._commit(net, path, hw)

HERE = os.path.dirname(os.path.abspath(__file__))


def mst_edges(groups):
    n = len(groups)
    if n < 2:
        return []

    def gd(a, c):
        best = None
        for p in groups[a]:
            for q in groups[c]:
                d = math.hypot(p["x"] - q["x"], p["y"] - q["y"])
                if best is None or d < best[0]:
                    best = (d, p, q)
        return best
    inside = {0}
    edges = []
    while len(inside) < n:
        best = None
        for a in inside:
            for c in range(n):
                if c in inside:
                    continue
                d, p, q = gd(a, c)
                if best is None or d < best[0]:
                    best = (d, a, c, p, q)
        d, a, c, p, q = best
        inside.add(c)
        edges.append((d, a, c, p, q))
    return edges


def route_edges(b, r, seed=0, jitter=0.25, verbose=True):
    rng = random.Random(seed)
    nets = b.nets()
    state = {}
    edges = []
    hand = {}
    for t in r.tracks:
        hand.setdefault(t["net"], []).append(t)
    for net, pads in nets.items():
        groups = R_.group_pads(b, pads)
        par = list(range(len(groups)))
        masks = [r.tree_mask_from(net, g, []) for g in groups]
        # hand tracks: merge every group touching a hand-routed polyline of this net
        if net in hand:
            hm = r.tree_mask_from(net, [], hand[net])
            touching = [i for i, g in enumerate(groups) if any((r.cells_in_pad(p, 0.3) & hm).any() for p in g)]
            if touching:
                root = touching[0]
                for i in touching[1:]:
                    par[i] = root
                masks[root] = masks[root] | hm
                for i in touching[1:]:
                    masks[root] |= masks[i]
        state[net] = dict(groups=groups, par=par, masks=masks)
        for (d, a, c, p, q) in mst_edges(groups):
            w = min(design.pad_width(b, p["ref"], p["pad"], net), design.pad_width(b, q["ref"], q["pad"], net))
            if net in R_.POWER_NETS or (net == "GND" and (p["ref"], p["pad"]) in design.GND_POWER
                                        and (q["ref"], q["pad"]) in design.GND_POWER):
                w = max(w, design.pad_width(b, p["ref"], p["pad"], net))
            key = d * (1 + jitter * (rng.random() - 0.5) * 2)
            edges.append((key, net, a, c, w))
    edges.sort(key=lambda e: (e[1] == "GND", e[0]))

    def find(par, i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    fails = []
    t0 = time.time()
    for (key, net, a, c, w) in edges:
        st = state[net]
        ra, rc = find(st["par"], a), find(st["par"], c)
        if ra == rc:
            continue
        src, tgt = st["masks"][ra], st["masks"][rc]
        res = connect_cost(r, net, src, tgt, w / 2)
        if res is None and w > design.W_SIG:
            res = connect_cost(r, net, src, tgt, design.W_SIG / 2)
        if res is None:
            fails.append((net, a, c))
            if verbose:
                g1, g2 = st["groups"][a][0], st["groups"][c][0]
                print("  FAIL %s %s.%s - %s.%s" % (net, g1["ref"], g1["pad"], g2["ref"], g2["pad"]), flush=True)
            continue
        tracks, jumps = res
        add = r.tree_mask_from(net, [], tracks)
        for j in jumps:
            for pnt in (j["a"], j["b"]):
                add |= r.cells_in_pad(dict(x=pnt[0], y=pnt[1], w=1.8, h=1.8, shape="C"), 0.05)
        st["par"][ra] = rc
        st["masks"][rc] = st["masks"][rc] | st["masks"][ra] | add
    if verbose:
        print("edges done %.0fs jumpers=%d fails=%d" % (time.time() - t0, len(r.jumpers), len(fails)), flush=True)
    return fails


def main():
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 0
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(HERE, "routes.json")
    jit = float(sys.argv[sys.argv.index("--jitter") + 1]) if "--jitter" in sys.argv else 0.25
    b = design.build()
    r = R_.setup(b)
    R_.add_hand_routes(b, r)
    fails = route_edges(b, r, seed, jit)
    gf = R_.gnd_phase(b, r, verbose=True)
    data = dict(tracks=r.tracks, jumpers=r.jumpers, failures=[list(map(str, f)) for f in fails] + gf, seed=seed)
    with open(out, "w") as fh:
        json.dump(data, fh, indent=0)
    print("RESULT seed=%d tracks=%d jumpers=%d fails=%d gndfails=%d" % (seed, len(r.tracks), len(r.jumpers), len(fails), len(gf)))


if __name__ == "__main__":
    main()
