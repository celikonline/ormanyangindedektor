"""Single-layer grid router (A*, 8-direction, 0.254 mm grid) with automatic
top-side wire-jumper insertion.

Clearance model: copper of every net is painted into a fine raster (0.127 mm).
For the net being routed, a Euclidean distance transform of *foreign* copper
gives, for every routing cell, the distance to the nearest foreign copper.
A track centre is allowed where  dist >= half_width + CLEARANCE + SLACK.
SLACK covers raster quantisation, so the exact vector DRC (copper.py) passes.
"""
import heapq
import math
import time

import numpy as np
from scipy import ndimage

F = 0.127            # fine raster pitch
G = 0.254            # routing grid pitch (= 2 F, 0.01")
CLEARANCE = 0.5
SLACK = 0.13
EDGE_CLR = 1.0       # copper to board edge
HOLE_GAP = 1.0       # min copper-free gap between a jumper hole edge and any other hole edge
J_COST = 260.0       # cost of one wire jumper, in grid cells (~66 mm of track)
J_LENGTHS = [20, 30, 40, 50, 60, 70, 80, 100]   # grid cells: 5.08 ... 25.4 mm (2.54 multiples)
TURN_COST = {0: 0.0, 1: 0.35, 2: 2.5}
R2 = math.sqrt(2.0)


class Router:
    def __init__(self, board, net_ids):
        self.b = board
        self.W, self.H = board.w, board.h
        self.nx = int(round(self.W / G)) + 1
        self.ny = int(round(self.H / G)) + 1
        self.nfx = 2 * (self.nx - 1) + 1
        self.nfy = 2 * (self.ny - 1) + 1
        self.occ = np.full((self.nfy, self.nfx), -1, dtype=np.int32)   # [y, x]
        self.net_ids = net_ids          # name -> int
        self.KEEP = len(net_ids) + 1    # keep-out pseudo net (mount holes, text)
        self.tracks = []                # dict(net, w, pts)
        self.jumpers = []               # dict(net, a, b)
        self.holes = []                 # (x, y, d) for spacing checks
        # routing-grid helper masks
        gx = np.arange(self.nx) * G
        gy = np.arange(self.ny) * G
        self.gX, self.gY = np.meshgrid(gx, gy)
        edge = np.minimum.reduce([self.gX, self.gY, self.W - self.gX, self.H - self.gY])
        self.edge_dist = edge
        self.court = np.zeros((self.ny, self.nx), dtype=bool)      # jumper bodies not allowed
        self.court_end = np.zeros((self.ny, self.nx), dtype=bool)  # jumper ends not allowed
        self.jbody = np.zeros((self.ny, self.nx), dtype=bool)      # existing jumper bodies
        self.hole_block = np.zeros((self.ny, self.nx), dtype=bool) # jumper hole centres not allowed
        self.stats = dict(expansions=0)
        self.HW = 1.15  # heuristic weight (weighted A*)

    # ------------------------------------------------------------ painting
    def _box(self, x0, y0, x1, y1):
        u0 = max(0, int(math.floor(x0 / F)) - 1)
        u1 = min(self.nfx - 1, int(math.ceil(x1 / F)) + 1)
        v0 = max(0, int(math.floor(y0 / F)) - 1)
        v1 = min(self.nfy - 1, int(math.ceil(y1 / F)) + 1)
        xs = np.arange(u0, u1 + 1) * F
        ys = np.arange(v0, v1 + 1) * F
        X, Y = np.meshgrid(xs, ys)
        return u0, v0, X, Y

    def paint_mask(self, mask_fn, bbox, net):
        u0, v0, X, Y = self._box(*bbox)
        m = mask_fn(X, Y)
        sub = self.occ[v0:v0 + m.shape[0], u0:u0 + m.shape[1]]
        sub[m] = net

    def paint_pad(self, x, y, w, h, shape, net):
        if shape == "C":
            r = w / 2
            self.paint_mask(lambda X, Y: (X - x) ** 2 + (Y - y) ** 2 <= r * r,
                            (x - r, y - r, x + r, y + r), net)
        elif shape == "R":
            self.paint_mask(lambda X, Y: (abs(X - x) <= w / 2) & (abs(Y - y) <= h / 2),
                            (x - w / 2, y - h / 2, x + w / 2, y + h / 2), net)
        else:  # obround
            if w >= h:
                r = h / 2
                a, b_ = (x - (w / 2 - r), y), (x + (w / 2 - r), y)
            else:
                r = w / 2
                a, b_ = (x, y - (h / 2 - r)), (x, y + (h / 2 - r))
            self.paint_segment(a, b_, 2 * r, net)

    def paint_segment(self, a, b_, w, net):
        r = w / 2
        (x1, y1), (x2, y2) = a, b_
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy

        def fn(X, Y):
            if L2 == 0:
                t = 0
            else:
                t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
            px, py = x1 + t * dx, y1 + t * dy
            return (X - px) ** 2 + (Y - py) ** 2 <= r * r
        self.paint_mask(fn, (min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r), net)

    def add_courtyard(self, poly, raised, low_ok=False):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        m = (self.gX >= min(xs)) & (self.gX <= max(xs)) & (self.gY >= min(ys)) & (self.gY <= max(ys))
        if not raised:
            self.court_end |= m
        if not raised and not low_ok:
            self.court |= m

    def _block_hole(self, x, y, d):
        rr = d / 2 + 0.4 + HOLE_GAP + 0.9
        self.hole_block |= (self.gX - x) ** 2 + (self.gY - y) ** 2 <= rr * rr

    def add_hole(self, x, y, d):
        self.holes.append((x, y, d))
        self._block_hole(x, y, d)
        # jumper bodies must keep clear of component leads (lead r ~0.4 + wire r 0.3 + margin)
        r = d / 2 + 0.6
        self.court |= (self.gX - x) ** 2 + (self.gY - y) ** 2 <= r * r

    # ------------------------------------------------------------ cost maps
    def dist_foreign(self, net):
        foreign = (self.occ >= 0) & (self.occ != net)
        dist = ndimage.distance_transform_edt(~foreign) * F
        return dist[::2, ::2][:self.ny, :self.nx]

    def free_mask(self, dist, hw):
        need = hw + CLEARANCE + SLACK
        return (dist >= need) & (self.edge_dist >= hw + EDGE_CLR)

    def jumper_pad_ok(self, dist):
        r = 0.9
        return (dist >= r + CLEARANCE + SLACK) & (self.edge_dist >= r + EDGE_CLR) & ~self.court_end             & ~self.jbody & ~self.hole_block

    # ------------------------------------------------------------ A*
    def astar(self, free, sources, target, hdist, jpad=None, jline=None, max_exp=600000):
        nx = self.nx
        offs = [1, nx + 1, nx, nx - 1, -1, -nx - 1, -nx, -nx + 1]
        cost = [1.0, R2, 1.0, R2, 1.0, R2, 1.0, R2]
        freel = free.ravel().tolist()
        targ = target.ravel().tolist()
        hd = hdist.ravel().tolist()
        jp = jpad.ravel().tolist() if jpad is not None else None
        HWt = self.HW
        gbest = {}
        parent = {}
        pq = []
        for s in sources:
            st = s * 9 + 8
            gbest[st] = 0.0
            parent[st] = None
            heapq.heappush(pq, (hd[s] * HWt, 0.0, st))
        exp = 0
        while pq:
            f, g, st = heapq.heappop(pq)
            if gbest.get(st, 1e18) < g - 1e-9:
                continue
            idx, d = divmod(st, 9)
            if targ[idx]:
                self.stats["expansions"] += exp
                return self._path(parent, st)
            exp += 1
            if exp > max_exp:
                break
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
                ng = g + cost[nd] + tc
                ns = ni * 9 + nd
                if ng < gbest.get(ns, 1e18) - 1e-9:
                    gbest[ns] = ng
                    parent[ns] = (st, "t")
                    heapq.heappush(pq, (ng + hd[ni] * HWt, ng, ns))
            # wire jumpers (axis aligned, 2.54 mm multiples)
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
                        if not jp[ni] or not freel[ni]:
                            continue
                        if not jline(ix, iy, jx, jy):
                            continue
                        ng = g + J_COST + k
                        ns = ni * 9 + 8
                        if ng < gbest.get(ns, 1e18) - 1e-9:
                            gbest[ns] = ng
                            parent[ns] = (st, "j")
                            heapq.heappush(pq, (ng + hd[ni] * HWt, ng, ns))
        self.stats["expansions"] += exp
        return None

    def _path(self, parent, st):
        out = []
        while st is not None:
            idx = st // 9
            p = parent[st]
            out.append((idx, p[1] if p else None))
            st = p[0] if p else None
        out.reverse()
        return out   # [(idx, how_we_arrived)]

    # ------------------------------------------------------------ connection
    def idx_xy(self, idx):
        iy, ix = divmod(idx, self.nx)
        return (ix * G, iy * G)

    def cells_in_pad(self, pd, shrink=0.15):
        x, y, w, h = pd["x"], pd["y"], pd["w"], pd["h"]
        if pd["shape"] == "C":
            r = max(w / 2 - shrink, 0.05)
            m = (self.gX - x) ** 2 + (self.gY - y) ** 2 <= r * r
        else:
            m = (abs(self.gX - x) <= max(w / 2 - shrink, 0.05)) & (abs(self.gY - y) <= max(h / 2 - shrink, 0.05))
        return m

    def route_connection(self, net_name, pad, tree, hw, allow_jumpers=True, src=None):
        """Connect `pad` (dict) -- or the routing-grid mask `src` -- to the routing-grid
        bool mask `tree` of the same net. Returns (tracks, jumpers) or None."""
        net = self.net_ids[net_name]
        dist = self.dist_foreign(net)
        free = self.free_mask(dist, hw)
        if src is not None:
            src_m = src & free
            if not src_m.any():
                return None
        else:
            src_m = self.cells_in_pad(pad) & free
        if not src_m.any():
            # force the pad centre
            src_m = self.cells_in_pad(pad, shrink=0.0)
            src_m &= dist >= hw + CLEARANCE * 0.5
            if not src_m.any():
                return None
            free = free | src_m
        target = tree & free
        if not target.any():
            target = tree & (dist >= hw + CLEARANCE * 0.5)
            free = free | target
        hdist = ndimage.distance_transform_edt(~tree)
        sources = np.flatnonzero(src_m.ravel()).tolist()
        jpad = jline = None
        if allow_jumpers:
            jpad = self.jumper_pad_ok(dist) & free
            body = self.court | self.jbody
            rc = np.cumsum(body, axis=1)
            cc = np.cumsum(body, axis=0)

            def jline(ix, iy, jx, jy):
                if iy == jy:
                    a, b_ = sorted((ix, jx))
                    s = rc[iy, b_] - (rc[iy, a - 1] if a > 0 else 0)
                else:
                    a, b_ = sorted((iy, jy))
                    s = cc[b_, ix] - (cc[a - 1, ix] if a > 0 else 0)
                return s == 0
        path = self.astar(free, sources, target, hdist, jpad, jline)
        if path is None:
            return None
        return self._commit(net_name, path, hw)

    def _commit(self, net_name, path, hw):
        net = self.net_ids[net_name]
        segs = []      # polylines
        jumps = []
        cur = [path[0][0]]
        for idx, how in path[1:]:
            if how == "j":
                segs.append(cur)
                jumps.append((cur[-1], idx))
                cur = [idx]
            else:
                cur.append(idx)
        segs.append(cur)
        out_tracks = []
        for s in segs:
            pts = [self.idx_xy(i) for i in s]
            pts = simplify(pts)
            if len(pts) >= 2:
                t = dict(net=net_name, w=round(2 * hw, 3), pts=pts)
                self.add_track(t)
                out_tracks.append(t)
        out_j = []
        for a, b_ in jumps:
            j = dict(net=net_name, a=self.idx_xy(a), b=self.idx_xy(b_))
            self.add_jumper(j)
            out_j.append(j)
        return out_tracks, out_j

    def add_track(self, t):
        net = self.net_ids[t["net"]]
        for a, b_ in zip(t["pts"], t["pts"][1:]):
            self.paint_segment(a, b_, t["w"], net)
        self.tracks.append(t)

    def add_jumper(self, j):
        net = self.net_ids[j["net"]]
        for p in j.get("pts", [j["a"], j["b"]]):
            self.paint_pad(p[0], p[1], 1.8, 1.8, "C", net)
            self.add_hole(p[0], p[1], 1.0)
        (x1, y1), (x2, y2) = j["a"], j["b"]
        m = (self.gX >= min(x1, x2) - 0.9) & (self.gX <= max(x1, x2) + 0.9) & \
            (self.gY >= min(y1, y2) - 0.9) & (self.gY <= max(y1, y2) + 0.9)
        self.jbody |= m
        self.court |= m
        self.jumpers.append(j)

    def tree_mask_from(self, net_name, pads, tracks):
        """routing-grid mask of the given pads + tracks of one net"""
        m = np.zeros((self.ny, self.nx), dtype=bool)
        for pd in pads:
            m |= self.cells_in_pad(pd, shrink=0.05)
        for t in tracks:
            hw = t["w"] / 2
            for (x1, y1), (x2, y2) in zip(t["pts"], t["pts"][1:]):
                dx, dy = x2 - x1, y2 - y1
                L2 = dx * dx + dy * dy
                tt = np.clip(((self.gX - x1) * dx + (self.gY - y1) * dy) / (L2 if L2 else 1), 0, 1)
                m |= (self.gX - (x1 + tt * dx)) ** 2 + (self.gY - (y1 + tt * dy)) ** 2 <= (hw * 0.7) ** 2
        return m


def simplify(pts):
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        ax, ay = out[-1]
        bx, by = pts[i]
        cx, cy = pts[i + 1]
        if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) < 1e-9:
            continue
        out.append(pts[i])
    out.append(pts[-1])
    return [(round(x, 4), round(y, 4)) for x, y in out]
