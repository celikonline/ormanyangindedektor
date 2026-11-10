"""Independent verification: read the generated Gerber + Excellon back with
gerbonara (a third-party parser), rasterise the bottom copper at 20 um,
and check
  * connectivity: copper islands (connected-component labelling of the raster)
    compared with the intended netlist at every drilled hole / SMD pad,
  * clearance: no two islands that belong to different nets closer than ~0.48 mm,
  * every hole lands inside copper (except NPTH mounting holes).
Also renders the read-back layers to PNG for visual inspection.
"""
import math
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from gerbonara import GerberFile, ExcellonFile
from gerbonara.utils import MM
from gerbonara import graphic_primitives as gp

RES = 0.02   # mm per pixel


def raster_gerber(path, W, H, res=RES, pad=1.0):
    gf = GerberFile.open(path)
    nx, ny = int((W + 2 * pad) / res), int((H + 2 * pad) / res)
    im = Image.new("L", (nx, ny), 0)
    d = ImageDraw.Draw(im)
    T = lambda x, y: ((x + pad) / res, (H + pad - y) / res)
    count = 0
    for obj in gf.objects:
        for prim in obj.to_primitives(MM):
            col = 255 if prim.polarity_dark else 0
            count += 1
            if isinstance(prim, gp.Line):
                r = prim.width / 2 / res
                a, b = T(prim.x1, prim.y1), T(prim.x2, prim.y2)
                d.line([a, b], fill=col, width=max(1, int(round(prim.width / res))))
                for p in (a, b):
                    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
            elif isinstance(prim, gp.Circle):
                cx, cy = T(prim.x, prim.y)
                r = prim.r / res
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
            elif isinstance(prim, gp.Rectangle):
                c, s = math.cos(prim.rotation), math.sin(prim.rotation)
                pts = []
                for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    px, py = dx * prim.w / 2, dy * prim.h / 2
                    pts.append(T(prim.x + px * c - py * s, prim.y + px * s + py * c))
                d.polygon(pts, fill=col)
            elif isinstance(prim, gp.ArcPoly):
                pts = [T(x, y) for x, y in prim.outline]
                if len(pts) >= 3:
                    d.polygon(pts, fill=col)
            elif isinstance(prim, gp.Arc):
                d.line([T(prim.x1, prim.y1), T(prim.x2, prim.y2)], fill=col,
                       width=max(1, int(round(prim.width / res))))
            else:
                raise RuntimeError("unhandled primitive %r" % prim)
    return np.array(im) > 127, T, count


def read_drills(path):
    ef = ExcellonFile.open(path)
    holes = []
    for obj in ef.objects:
        prims = obj.to_primitives(MM)
        for p in prims:
            if isinstance(p, gp.Circle):
                holes.append((p.x, p.y, 2 * p.r))
    return holes


def verify(gerber_dir, prefix, W, H, pad_table, links, out_png=None, verbose=True, npth=()):
    """pad_table: list of (x, y, net, label, has_hole). links: list of (label_a, label_b)."""
    cu, T, nprim = raster_gerber(os.path.join(gerber_dir, prefix + "-B_Cu.gbr"), W, H)
    holes = read_drills(os.path.join(gerber_dir, prefix + ".drl"))
    lab, nlab = ndimage.label(cu, structure=np.ones((3, 3)))
    rep = dict(primitives=nprim, holes=len(holes), islands=int(nlab))
    # map design pads to islands
    def at(x, y):
        px, py = T(x, y)
        i, j = int(round(py)), int(round(px))
        return int(lab[i, j])
    pad_isl = {}
    unknown_holes = []
    for (x, y, d) in holes:
        best = None
        for (px, py, net, label, hh) in pad_table:
            dd = math.hypot(px - x, py - y)
            if best is None or dd < best[0]:
                best = (dd, label, net)
        if best[0] > 0.05 and not any(math.hypot(x - a, y - c) < 0.05 for (a, c) in npth):
            unknown_holes.append((round(x, 3), round(y, 3), d))
    for (px, py, net, label, hh) in pad_table:
        pad_isl[label] = at(px, py)
    # union-find on island ids through jumpers / module-internal links
    par = list(range(nlab + 1))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for a, c in links:
        ia, ic = pad_isl.get(a, 0), pad_isl.get(c, 0)
        if ia and ic:
            par[find(ia)] = find(ic)
    nets_of = defaultdict(set)
    group_of_net = defaultdict(set)
    no_copper = []
    for (px, py, net, label, hh) in pad_table:
        i = pad_isl[label]
        if i == 0:
            if net is not None:
                no_copper.append(label)
            continue
        g = find(i)
        nets_of[g].add(net if net else "NC:" + label)
        if net:
            group_of_net[net].add(g)
    shorts = [sorted(v) for v in nets_of.values() if len([n for n in v if not n.startswith("NC:")]) > 1
              or (len(v) > 1 and any(n.startswith("NC:") for n in v) and any(not n.startswith("NC:") for n in v))]
    opens = {n: len(g) for n, g in group_of_net.items() if len(g) > 1}
    # clearance between islands of different nets
    lab_net = {}
    for g, v in nets_of.items():
        real = [n for n in v if not n.startswith("NC:")]
        lab_net[g] = real[0] if len(real) == 1 else ("|".join(sorted(v)))
    canon = np.array([find(i) for i in range(nlab + 1)], dtype=np.int32)
    L = canon[lab]
    dist, inds = ndimage.distance_transform_edt(~cu, return_indices=True)
    nearest = L[inds[0], inds[1]]
    r = 0.24 / RES
    zone = (~cu) & (dist <= r)
    viol = []
    for dy, dx in ((0, 1), (1, 0)):
        a = zone[:-dy or None, :-dx or None] & zone[dy:, dx:]
        na = nearest[:-dy or None, :-dx or None]
        nb = nearest[dy:, dx:]
        m = a & (na != nb)
        ys, xs = np.nonzero(m)
        for y, x in zip(ys[:2000], xs[:2000]):
            n1, n2 = lab_net.get(int(na[y, x]), "island%d" % na[y, x]), lab_net.get(int(nb[y, x]), "island%d" % nb[y, x])
            if n1 != n2 and not (n1.startswith("island") and n2.startswith("island")):
                viol.append((n1, n2, round(x * RES - 1.0, 2), round(H + 1.0 - y * RES, 2)))
    # unlabelled islands (floating copper that is not part of any net, e.g. text)
    used = set(find(i) for i in pad_isl.values() if i)
    floating = len(set(canon[1:]) - used)
    rep.update(shorts=shorts, opens=opens, clearance_violations=viol[:20], n_clearance_violations=len(viol),
               unmatched_holes=unknown_holes, pads_without_copper=no_copper, floating_islands=floating)
    if out_png:
        small = Image.fromarray((~cu * 255).astype(np.uint8)).resize((cu.shape[1] // 4, cu.shape[0] // 4))
        small.save(out_png)
    if verbose:
        print("read-back: %d primitives, %d holes, %d copper islands, %d floating (text/unused)" % (
            nprim, len(holes), nlab, floating))
        print("  shorts:", shorts if shorts else "none")
        print("  opens:", opens if opens else "none")
        print("  raster clearance (<0.48 mm) violations:", len(viol))
        print("  holes not matching a design pad:", unknown_holes if unknown_holes else "none")
        print("  pads without copper:", no_copper if no_copper else "none")
    return rep
