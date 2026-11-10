"""Negotiated-congestion router (PathFinder style) for a single copper layer with
optional top-side wire jumpers.

Every iteration rips up and re-routes every net. Pads are hard obstacles; other
nets' tracks are soft obstacles whose cost grows with a present-congestion factor
and an accumulated history term, so nets negotiate for the free space. A wire
jumper (axis-aligned, 2.54 mm multiple) is a fixed-cost alternative that lets a
net hop over other tracks. When no overlaps remain the result is legal.
GND is not routed here (it is grounded through the pour afterwards).
"""
import heapq
import math
import random
import time

import numpy as np
from scipy import ndimage

import design
from router import (Router, F, G, CLEARANCE, SLACK, EDGE_CLR, HOLE_GAP, J_LENGTHS, TURN_COST, simplify)
import route as R_

R2 = math.sqrt(2.0)
J_COST = float(__import__('os').environ.get('JCOST', '300'))


class NRouter(Router):
    def __init__(self, board, net_ids):
        super().__init__(board, net_ids)
        self.trk = {}          # net -> fine bool raster (tracks + jumper pads)
        self.trk_count = np.zeros_like(self.occ, dtype=np.int16)
        self.ntracks = {}      # net -> list
        self.njumps = {}       # net -> list
        self.hist = np.zeros((self.ny, self.nx), dtype=np.float32)
        self._hard_cache = {}
        self.static_holes = None

    # --- per-net track rasters
    def _paint_into(self, arr, fn, bbox):
        u0, v0, X, Y = self._box(*bbox)
        m = fn(X, Y)
        arr[v0:v0 + m.shape[0], u0:u0 + m.shape[1]] |= m

    def _seg_fn(self, a, b_, w):
        r = w / 2
        (x1, y1), (x2, y2) = a, b_
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy

        def fn(X, Y):
            t = 0 if L2 == 0 else np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
            return (X - x1 - t * dx) ** 2 + (Y - y1 - t * dy) ** 2 <= r * r
        return fn, (min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r)

    def net_raster(self, net, tracks, jumps):
        arr = np.zeros_like(self.occ, dtype=bool)
        for t in tracks:
            for a, b_ in zip(t["pts"], t["pts"][1:]):
                fn, bb = self._seg_fn(a, b_, t["w"])
                self._paint_into(arr, fn, bb)
        for j in jumps:
            for (x, y) in (j["a"], j["b"]):
                r = 0.9
                self._paint_into(arr, lambda X, Y, x=x, y=y: (X - x) ** 2 + (Y - y) ** 2 <= r * r,
                                 (x - r, y - r, x + r, y + r))
        return arr

    def set_net(self, net, tracks, jumps):
        old = self.trk.get(net)
        if old is not None:
            self.trk_count -= old
        arr = self.net_raster(net, tracks, jumps)
        self.trk[net] = arr
        self.trk_count += arr
        self.ntracks[net] = tracks
        self.njumps[net] = jumps

    def clear_net(self, net):
        self.set_net(net, [], [])

    # --- distance fields
    def hard_dist(self, net):
        nid = self.net_ids[net]
        if nid not in self._hard_cache:
            foreign = (self.occ >= 0) & (self.occ != nid)
            d = ndimage.distance_transform_edt(~foreign) * F
            self._hard_cache[nid] = d[::2, ::2][:self.ny, :self.nx]
        return self._hard_cache[nid]

    def soft_dist(self, net):
        own = self.trk.get(net)
        foreign = self.trk_count > (own.astype(np.int16) if own is not None else 0)
        d = ndimage.distance_transform_edt(~foreign) * F
        return d[::2, ::2][:self.ny, :self.nx]

    def other_jbody(self, net):
        m = np.zeros((self.ny, self.nx), dtype=bool)
        for n, js in self.njumps.items():
            if n == net:
                continue
            for j in js:
                (x1, y1), (x2, y2) = j["a"], j["b"]
                m |= (self.gX >= min(x1, x2) - 0.9) & (self.gX <= max(x1, x2) + 0.9) & \
                     (self.gY >= min(y1, y2) - 0.9) & (self.gY <= max(y1, y2) + 0.9)
        return m

    def other_jholes(self, net):
        m = np.zeros((self.ny, self.nx), dtype=bool)
        for n, js in self.njumps.items():
            if n == net:
                continue
            for j in js:
                for (x, y) in (j["a"], j["b"]):
                    rr = 0.5 + 0.4 + HOLE_GAP + 0.9
                    m |= (self.gX - x) ** 2 + (self.gY - y) ** 2 <= rr * rr
        return m

    # --- one connection
    def connect(self, net, src_mask, tree, hw, pres, allow_j=True, ctx=None):
        hard = ctx["hard"]
        soft = ctx["soft"]
        need = hw + CLEARANCE + SLACK
        free = (hard >= need) & (self.edge_dist >= hw + EDGE_CLR)
        conf = (soft < need) & free
        src = src_mask & free
        if not src.any():
            src = src_mask & (hard >= hw + CLEARANCE * 0.5)
            if not src.any():
                return None
            free = free | src
        target = tree & free
        if not target.any():
            target = tree & (hard >= hw + CLEARANCE * 0.5)
            free = free | target
        cellcost = (1.0 + self.hist + conf * pres).astype(np.float64)
        hdist = ndimage.distance_transform_edt(~tree)
        jpad = jline = None
        if allow_j:
            jpad = (hard >= 0.9 + CLEARANCE + SLACK) & (soft >= 0.9 + CLEARANCE + SLACK) & \
                   (self.edge_dist >= 0.9 + EDGE_CLR) & ~self.court_end & ~self.hole_block & \
                   ~ctx["ojholes"] & ~ctx["ojbody"] & free
            body = self.court | ctx["ojbody"]
            rc = np.cumsum(body, axis=1)
            cc = np.cumsum(body, axis=0)

            def jline(ix, iy, jx, jy):
                if iy == jy:
                    a, b_ = sorted((ix, jx))
                    return rc[iy, b_] - (rc[iy, a - 1] if a > 0 else 0) == 0
                a, b_ = sorted((iy, jy))
                return cc[b_, ix] - (cc[a - 1, ix] if a > 0 else 0) == 0
        path = self.astar_c(free, np.flatnonzero(src.ravel()).tolist(), target, hdist, cellcost, jpad, jline)
        if path is None:
            return None
        confl = conf.ravel()
        self._last_conf = [idx for idx, how in path if confl[idx]]
        segs, jumps = [], []
        cur = [path[0][0]]
        for idx, how in path[1:]:
            if how == "j":
                segs.append(cur)
                jumps.append((cur[-1], idx))
                cur = [idx]
            else:
                cur.append(idx)
        segs.append(cur)
        tracks = []
        for s in segs:
            pts = simplify([self.idx_xy(i) for i in s])
            if len(pts) >= 2:
                tracks.append(dict(net=net, w=round(2 * hw, 3), pts=pts))
        js = [dict(net=net, a=self.idx_xy(a), b=self.idx_xy(b_)) for a, b_ in jumps]
        return tracks, js

    def astar_c(self, free, sources, target, hdist, cellcost, jpad, jline, max_exp=400000):
        nx = self.nx
        offs = [1, nx + 1, nx, nx - 1, -1, -nx - 1, -nx, -nx + 1]
        step = [1.0, R2, 1.0, R2, 1.0, R2, 1.0, R2]
        freel = free.ravel().tolist()
        targ = target.ravel().tolist()
        hd = hdist.ravel().tolist()
        cc = cellcost.ravel().tolist()
        jp = jpad.ravel().tolist() if jpad is not None else None
        HW = 1.1
        gbest = {}
        parent = {}
        pq = []
        for s in sources:
            st = s * 9 + 8
            gbest[st] = 0.0
            parent[st] = None
            pq.append((hd[s] * HW, 0.0, st))
        heapq.heapify(pq)
        exp = 0
        while pq:
            f, g, st = heapq.heappop(pq)
            if gbest.get(st, 1e18) < g - 1e-9:
                continue
            idx, d = divmod(st, 9)
            if targ[idx]:
                return self._path(parent, st)
            exp += 1
            if exp > max_exp:
                return None
            for nd in range(8):
                if d != 8:
                    t = (nd - d) % 8
                    t = min(t, 8 - t)
                    if t > 2:
                        continue
                    tc = TURN_COST[t]
                else:
                    tc = 0.0
                ni = idx + offs[nd]
                if not freel[ni]:
                    continue
                ng = g + step[nd] * 0.5 * (cc[idx] + cc[ni]) + tc
                ns = ni * 9 + nd
                if ng < gbest.get(ns, 1e18) - 1e-9:
                    gbest[ns] = ng
                    parent[ns] = (st, "t")
                    heapq.heappush(pq, (ng + hd[ni] * HW, ng, ns))
            if jp is not None and jp[idx] and not (parent.get(st) and parent[st][1] == "j"):
                iy, ix = divmod(idx, nx)
                for a in (0, 2, 4, 6):
                    for k in J_LENGTHS:
                        if a == 0:
                            jx, jy = ix + k, iy
                        elif a == 4:
                            jx, jy = ix - k, iy
                        elif a == 2:
                            jx, jy = ix, iy + k
                        else:
                            jx, jy = ix, iy - k
                        if not (0 <= jx < nx and 0 <= jy < self.ny):
                            continue
                        ni = jy * nx + jx
                        if not jp[ni] or not jline(ix, iy, jx, jy):
                            continue
                        ng = g + getattr(self, "jcost", J_COST) + k
                        ns = ni * 9 + 8
                        if ng < gbest.get(ns, 1e18) - 1e-9:
                            gbest[ns] = ng
                            parent[ns] = (st, "j")
                            heapq.heappush(pq, (ng + hd[ni] * HW, ng, ns))
        return None


def route_net(r, b, net, groups, hand, pres, stage_max=2, allow_j=True):
    """Route all connections of one net (tree growth). Returns (tracks, jumps, failures)."""
    root = R_.ROOTS.get(net)
    gi = 0
    if root:
        for i, g in enumerate(groups):
            if any((p["ref"], p["pad"]) == root for p in g):
                gi = i
    tree = r.tree_mask_from(net, groups[gi], hand)
    conn = {gi}
    changed = True
    while changed:
        changed = False
        for i, g in enumerate(groups):
            if i not in conn and any((r.cells_in_pad(p, 0.3) & tree).any() for p in g):
                conn.add(i)
                tree |= r.tree_mask_from(net, g, [])
                changed = True
    tracks, jumps, fails = [], [], []
    ctx = dict(hard=r.hard_dist(net), soft=r.soft_dist(net), ojbody=r.other_jbody(net),
               ojholes=r.other_jholes(net))
    order_stage = lambda g: min(R_.stage_of(net, p) for p in g)
    while True:
        todo = [i for i, g in enumerate(groups) if i not in conn]
        if not todo:
            break
        ty, tx = np.nonzero(tree)
        txy = np.stack([tx * G, ty * G], axis=1)
        best = None
        for i in todo:
            for p in groups[i]:
                d = np.min((txy[:, 0] - p["x"]) ** 2 + (txy[:, 1] - p["y"]) ** 2)
                key = (order_stage(groups[i]), d)
                if best is None or key < best[0]:
                    best = (key, i, p)
        _, gi, pad = best
        w = design.pad_width(b, pad["ref"], pad["pad"], net)
        res = r.connect(net, r.cells_in_pad(pad), tree, w / 2, pres, allow_j, ctx)
        if res is None and w > design.W_MID:
            res = r.connect(net, r.cells_in_pad(pad), tree, design.W_MID / 2, pres, allow_j, ctx)
        conn.add(gi)
        if res is None:
            fails.append((net, pad["ref"], pad["pad"]))
            continue
        tr, js = res
        tracks += tr
        jumps += js
        r._conf_cells.extend(r._last_conf)
        if r._last_conf:
            r._conf_log.append((net, len(r._last_conf), r.idx_xy(r._last_conf[0])))
        add = r.tree_mask_from(net, groups[gi], tr)
        for j in js:
            for pnt in (j["a"], j["b"]):
                add |= r.cells_in_pad(dict(x=pnt[0], y=pnt[1], w=1.8, h=1.8, shape="C"), 0.05)
        tree |= add
        # own new jumpers block later jumper holes of this net too
        for j in js:
            for pnt in (j["a"], j["b"]):
                rr = 0.5 + 0.4 + HOLE_GAP + 0.9
                ctx["ojholes"] = ctx["ojholes"] | ((r.gX - pnt[0]) ** 2 + (r.gY - pnt[1]) ** 2 <= rr * rr)
            (x1, y1), (x2, y2) = j["a"], j["b"]
            ctx["ojbody"] = ctx["ojbody"] | ((r.gX >= min(x1, x2) - 0.9) & (r.gX <= max(x1, x2) + 0.9) &
                                             (r.gY >= min(y1, y2) - 0.9) & (r.gY <= max(y1, y2) + 0.9))
    return tracks, jumps, fails


def overlaps(r):
    """Cells (routing grid) where a net's copper is closer than the clearance to
    another net's track copper -- the same notion of conflict the router uses."""
    bad = np.zeros((r.ny, r.nx), dtype=bool)
    lim = CLEARANCE + SLACK - 0.1
    for n, arr in r.trk.items():
        if not arr.any():
            continue
        foreign = r.trk_count > arr.astype(np.int16)
        d = ndimage.distance_transform_edt(~arr) * F
        hit = foreign & (d < lim)
        if hit.any():
            bad |= hit[::2, ::2][:r.ny, :r.nx] | ndimage.binary_dilation(hit, iterations=2)[::2, ::2][:r.ny, :r.nx]
    return bad


def _gnd_first():
    import os as _os
    return _os.environ.get("GND_FIRST", "0") == "1"


def negotiate(b, iters=30, seed=0, verbose=True):
    random.seed(seed)
    base = R_.setup(b)
    r = NRouter.__new__(NRouter)
    r.__dict__.update(base.__dict__)
    r.trk, r.ntracks, r.njumps = {}, {}, {}
    r.trk_count = np.zeros_like(r.occ, dtype=np.int16)
    r.hist = np.zeros((r.ny, r.nx), dtype=np.float32)
    r._hard_cache = {}
    # hand routes are static copper of their net
    hand_by_net = {}
    for net, w, pts in getattr(design, "HAND_ROUTES", []):
        t = dict(net=net, w=w, pts=[tuple(p) for p in pts])
        base.add_track(t)
        hand_by_net.setdefault(net, []).append(t)
    base.hand_jumpers = []
    for net, pts in getattr(design, "HAND_JUMPERS", []):
        pts = [tuple(p) for p in pts]
        j = dict(net=net, a=pts[0], b=pts[-1], pts=pts, hand=True)
        base.add_jumper(j)
        base.hand_jumpers.append(j)
        for q in pts:   # tree seeds (not output as tracks)
            hand_by_net.setdefault(net, []).append(dict(net=net, w=1.8, pts=[q, q], seed=True))
    r.occ = base.occ
    r.tracks = []
    if _gnd_first():
        # route the GND tree alone first (only pads + ring as obstacles), then freeze it
        gp = b.nets()["GND"]
        gg = R_.group_pads(b, gp)
        ctx_r = r
        r.trk, r.ntracks, r.njumps = {}, {}, {}
        r.trk_count = np.zeros_like(r.occ, dtype=np.int16)
        r.hist = np.zeros((r.ny, r.nx), dtype=np.float32)
        r._hard_cache = {}
        r._conf_cells, r._conf_log = [], []
        r.jcost = 1e5
        gt, gj, gf = route_net(r, b, "GND", gg, hand_by_net.get("GND", []), pres=1.0, allow_j=False)
        r.jcost = J_COST
        for t in gt:
            base.add_track(t)
            hand_by_net.setdefault("GND", []).append(t)
        r.occ = base.occ
        r._hard_cache = {}
        if verbose:
            print("GND-first: %d tracks, %d unrouted" % (len(gt), len(gf)), flush=True)
    import os as _os
    with_gnd = _os.environ.get("ROUTE_GND", "0") == "1"
    nets = {n: p for n, p in b.nets().items() if with_gnd or n != "GND"}
    groups = {n: R_.group_pads(b, p) for n, p in nets.items()}
    hint = getattr(design, "ROUTE_ORDER", [])
    order = sorted(nets.keys(), key=lambda n: (hint.index(n) if n in hint else 999, n))
    pres = 0.6
    best = None
    t0 = time.time()
    for it in range(iters):
        fails = []
        r._conf_cells = []
        r._conf_log = []
        if it > 0:
            random.shuffle(order)
        for net in order:
            if len(groups[net]) < 2 and net not in hand_by_net:
                continue
            r.clear_net(net)
            tr, js, fl = route_net(r, b, net, groups[net], hand_by_net.get(net, []), pres)
            r.set_net(net, tr, js)
            fails += fl
        bad = np.zeros((r.ny, r.nx), dtype=bool)
        if r._conf_cells:
            bad.ravel()[np.array(r._conf_cells)] = True
            bad = ndimage.binary_dilation(bad, iterations=2)
        nb = len(set(r._conf_cells))
        nj = sum(len(v) for v in r.njumps.values())
        if verbose and it % 5 == 4:
            agg = {}
            for (nn, k, xy) in r._conf_log:
                agg.setdefault(nn, [0, xy])[0] += k
            print("   conflicts:", sorted(((v[0], nn, tuple(round(c, 1) for c in v[1])) for nn, v in agg.items()), reverse=True)[:12])
        if verbose:
            print("iter %d pres=%.1f overlaps=%d jumpers=%d fails=%d  %.0fs" % (it, pres, nb, nj, len(fails),
                                                                              time.time() - t0), flush=True)
        if nb == 0 and not fails:
            if best is None or nj < best[0]:
                best = (nj, {n: list(v) for n, v in r.ntracks.items()}, {n: list(v) for n, v in r.njumps.items()})
            if nj <= getattr(design, "JUMPER_TARGET", 0):
                break
        r.hist += bad.astype(np.float32) * 0.6
        r._last_conf_cells = list(r._conf_cells)
        r._conf_by_net = {}
        pres *= float(__import__('os').environ.get('PGROW', '1.25'))
    if best is None:
        best = (None, r.ntracks, r.njumps)
    else:
        # restore the best converged state and try to eliminate jumpers one net at a time
        for net in list(r.trk.keys()):
            r.set_net(net, best[1].get(net, []), best[2].get(net, []))
        reduce_jumpers(r, b, groups, hand_by_net, verbose=verbose)
        best = (sum(len(v) for v in r.njumps.values()), dict(r.ntracks), dict(r.njumps))
    r.hand_jumpers = base.hand_jumpers
    return r, best, hand_by_net


def _net_conflicts(r, net, tracks, jumps):
    """number of routing cells of this net's tracks that violate clearance to other nets' tracks"""
    arr = r.net_raster(net, tracks, jumps)
    own = r.trk.get(net)
    foreign = r.trk_count - (own.astype(np.int16) if own is not None else 0) > 0
    d = ndimage.distance_transform_edt(~arr) * F
    return int((foreign & (d < CLEARANCE + SLACK - 0.1)).sum())


def reduce_jumpers(r, b, groups, hand, rounds=3, verbose=True):
    for rd in range(rounds):
        improved = 0
        cands = sorted([n for n, js in r.njumps.items() if js], key=lambda n: -len(r.njumps[n]))
        for net in cands:
            old_t, old_j = r.ntracks[net], r.njumps[net]
            r.clear_net(net)
            r.jcost = 4000.0
            tr, js, fl = route_net(r, b, net, groups[net], hand.get(net, []), pres=1e5)
            r.jcost = J_COST
            ok = not fl and len(js) < len(old_j) and _net_conflicts(r, net, tr, js) == 0
            if ok:
                r.set_net(net, tr, js)
                improved += 1
                if verbose:
                    print("   jumper reduced on %s: %d -> %d" % (net, len(old_j), len(js)), flush=True)
            else:
                r.set_net(net, old_t, old_j)
        if verbose:
            print("reduce round %d: improved %d nets, jumpers now %d" % (rd, improved, sum(len(v) for v in r.njumps.values())), flush=True)
        if not improved:
            break
