"""Placement sanity check: courtyard overlaps, pad collisions, board/keep-out violations."""
from shapely.geometry import Polygon, Point, box
import design
import copper


def check(b, verbose=True):
    issues = []
    outline = Polygon(b.outline())
    cps = []
    for c in b.comps:
        cp = c.court_poly()
        if cp:
            cps.append((c.ref, Polygon(cp), c.fp.raised))
    for i in range(len(cps)):
        for j in range(i + 1, len(cps)):
            a, bb = cps[i], cps[j]
            if a[0].startswith("H") or bb[0].startswith("H"):
                continue
            ov = a[1].intersection(bb[1]).area
            if ov > 0.05:
                issues.append("courtyard %s/%s %.1fmm2" % (a[0], bb[0], ov))
        if not outline.contains(cps[i][1]):
            issues.append("outside board: " + cps[i][0])
    pads = b.all_pads()
    polys = [(p, copper.pad_poly(p["x"], p["y"], p["w"], p["h"], p["shape"])) for p in pads]
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            p, q = polys[i][0], polys[j][0]
            if p["ref"] == q["ref"]:
                continue
            d = polys[i][1].distance(polys[j][1])
            if d < 0.5 and not (p["net"] and p["net"] == q["net"]):
                issues.append("pad %s.%s - %s.%s gap %.2f" % (p["ref"], p["pad"], q["ref"], q["pad"], d))
    ko = copper.keepouts(b)
    for p, g in polys:
        if g.intersects(ko):
            issues.append("pad in keepout %s.%s" % (p["ref"], p["pad"]))
        if g.distance(outline.exterior) < 1.0:
            issues.append("pad near edge %s.%s" % (p["ref"], p["pad"]))
    if verbose:
        print("\n".join(issues) if issues else "placement OK")
    return issues


if __name__ == "__main__":
    check(design.build())
