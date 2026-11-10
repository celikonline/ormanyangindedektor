"""Generate every ON1-DIY output from design.py + routes.json:

  gerber/  RS-274X + Excellon (+ zip)       print/  1:1 A4 PDFs
  png/     600 dpi previews                 ON1-DIY_BOM.csv, ON1-DIY_netlist.md, drc_report.txt

    python build.py            (uses tools/routes.json; run autoroute.py first to re-route)
"""
import json
import math
import os
import sys
from collections import defaultdict

from shapely.ops import unary_union
from shapely.geometry import Polygon

import design
import copper
import gerber as GB
import silk as SK
import artwork as AW
import verify as VF
import docs
from font import text_strokes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GDIR = os.path.join(ROOT, "gerber")
PDIR = os.path.join(ROOT, "print")
IDIR = os.path.join(ROOT, "png")
PFX = "ON1-DIY"


def holes_of(b, routes):
    holes = []   # (x, y, d, npth)
    for it in copper.pad_items(b, routes):
        if it["drill"]:
            holes.append((it["x"], it["y"], it["drill"], False))
    for c in b.comps:
        for (hx, hy, d) in c.fp.npth:
            x, y = c.xf(hx, hy)
            holes.append((x, y, d, True))
    return holes


def write_gerbers(b, routes, geoms_np, pour, strokes):
    os.makedirs(GDIR, exist_ok=True)
    files = []
    # ---------------- bottom copper
    g = GB.GerberWriter("Copper,L1,Bot")
    g.body.append("G04 GND pour (regions; clear polarity = holes in the pour)*")
    g.polygons(pour)
    g.body.append("%LPD*%")
    g.body.append("G04 tracks*")
    for t in routes["tracks"]:
        g.stroke(t["pts"], t["w"])
    g.body.append("G04 pads*")
    for it in copper.pad_items(b, routes):
        GB.flash_pad(g, it["x"], it["y"], it["w"], it["h"], it["shape"])
    g.body.append("G04 copper text*")
    for (txt, x, y, h, anchor, rot) in b.copper_texts:
        for st in text_strokes(txt, x, y, h, anchor, rot):
            g.stroke(st, copper.TEXT_W)
    p = os.path.join(GDIR, PFX + "-B_Cu.gbr")
    g.write(p, "Bottom copper, viewed from TOP (not mirrored)")
    files.append(p)
    # ---------------- bottom solder mask (openings)
    g = GB.GerberWriter("Soldermask,Bot", polarity="Negative")
    for it in copper.pad_items(b, routes):
        GB.flash_pad(g, it["x"], it["y"], it["w"], it["h"], it["shape"], grow=0.1)
    p = os.path.join(GDIR, PFX + "-B_Mask.gbr")
    g.write(p, "Bottom solder mask openings (optional)")
    files.append(p)
    # ---------------- top silkscreen
    g = GB.GerberWriter("Legend,Top")
    for pts, w in strokes:
        g.stroke(pts, w)
    p = os.path.join(GDIR, PFX + "-F_SilkS.gbr")
    g.write(p, "Top silkscreen / component legend")
    files.append(p)
    # ---------------- outline
    g = GB.GerberWriter("Profile,NP")
    ol = b.outline()
    g.stroke(ol + [ol[0]], 0.15)
    p = os.path.join(GDIR, PFX + "-Edge_Cuts.gbr")
    g.write(p, "Board outline 100 x 75 mm, R2 corners")
    files.append(p)
    # ---------------- drill
    holes = holes_of(b, routes)
    p = os.path.join(GDIR, PFX + ".drl")
    counts = GB.write_excellon(p, holes)
    files.append(p)
    GB.zip_files(os.path.join(GDIR, PFX + "_gerber.zip"), files)
    return files, counts, holes


def main():
    rpath = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "routes.json")
    routes = json.load(open(rpath))
    b = design.build()
    AW.setup_fonts()
    # -------- geometry, DRC, connectivity (vector, from our own geometry)
    geoms_np = copper.net_geometries(b, routes, with_pour=False)
    pour = copper.make_pour(b, routes, geoms_np)
    geoms = dict(geoms_np)
    geoms["GND"] = unary_union([geoms_np.get("GND"), pour])
    drc = copper.drc(b, routes, geoms)
    con = copper.connectivity(b, routes, geoms)
    print("DRC: clearance violations=%d (min %.3f mm), edge=%d, width=%d, hole-spacing=%d" % (
        len(drc["clearance"]), drc["min_clearance"], len(drc["edge"]), len(drc["width"]), len(drc["holes"])))
    for v in drc["clearance"][:20]:
        print("   ", v)
    for v in drc["holes"][:10]:
        print("   hole", v)
    print("Connectivity (geometry): islands=%d nets=%d shorts=%d opens=%d" % (
        con["islands"], con["nets"], len(con["shorts"]), len(con["opens"])))
    for s in con["shorts"][:10]:
        print("   short", s)
    for o in con["opens"][:10]:
        print("   open", o)
    copper_all = unary_union(list(geoms.values()))
    strokes = SK.silk_strokes(b, routes)
    # -------- Gerbers
    files, counts, holes = write_gerbers(b, routes, geoms_np, pour, strokes)
    # -------- independent read-back
    pad_table = []
    for it in copper.pad_items(b, routes):
        pad_table.append((it["x"], it["y"], it["net"], "%s.%s" % (it["ref"], it["pad"]), bool(it["drill"])))
    links = [("%s.%s" % a, "%s.%s" % c) for a, c in b.internal_links()]
    for i, j in enumerate(routes["jumpers"]):
        n = len(j.get("pts", [j["a"], j["b"]]))
        links += [("J-W%d.%d" % (i + 1, t), "J-W%d.%d" % (i + 1, t + 1)) for t in range(1, n)]
    # module-internal links only between connected pins
    netof = {lab: n for (_, _, n, lab, _) in pad_table}
    links = [(a, c) for a, c in links if netof.get(a) and netof.get(c)]
    os.makedirs(IDIR, exist_ok=True)
    rb = VF.verify(GDIR, PFX, b.w, b.h, pad_table, links,
                   out_png=os.path.join(IDIR, "ON1-DIY_dogrulama_geriokuma_bakir.png"),
                   npth=[(x, y) for (x, y, d, n) in holes if n])
    # -------- PNG + PDF artwork
    import outputs
    outputs.make_pngs(b, routes, copper_all, holes, strokes, IDIR)
    outputs.make_pdfs(b, routes, copper_all, holes, strokes, counts, PDIR)
    # -------- BOM / netlist / report
    docs.write_bom(b, routes, os.path.join(ROOT, PFX + "_BOM.csv"))
    docs.write_netlist(b, routes, os.path.join(ROOT, PFX + "_netlist.md"))
    rep = dict(drc=dict(clearance_violations=len(drc["clearance"]), min_clearance_mm=round(drc["min_clearance"], 3),
                        edge_violations=len(drc["edge"]), width_violations=len(drc["width"]),
                        hole_spacing_violations=len(drc["holes"])),
               connectivity_geometry=dict(islands=con["islands"], nets=con["nets"], shorts=con["shorts"],
                                          opens=con["opens"]),
               readback=dict((k, v) for k, v in rb.items()),
               jumpers=len(routes["jumpers"]), tracks=len(routes["tracks"]),
               holes=len(holes), drill_counts={str(k): v for k, v in counts.items()})
    with open(os.path.join(ROOT, "tools", "drc_report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    uses = defaultdict(set)
    for it in copper.pad_items(b, routes):
        if it["drill"]:
            uses[round(it["drill"], 2)].add(it["ref"] if it["ref"].startswith("J-W") else it["ref"].rstrip("0123456789"))
    for c in b.comps:
        for (_, _, d) in c.fp.npth:
            uses[round(d, 2)].add("M3")
    uses = {k: sorted({("J-W" if v.startswith("J-W") else v) for v in vs}) for k, vs in uses.items()}
    docs.update_readme(os.path.join(ROOT, "README.md"), b, routes, rep, counts, uses)
    print("jumpers:", len(routes["jumpers"]), " holes:", len(holes), " drill tools:", counts)


if __name__ == "__main__":
    main()
