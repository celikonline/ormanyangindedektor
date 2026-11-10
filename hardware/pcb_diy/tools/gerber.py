"""RS-274X (Gerber X2 attributes) and Excellon writers for ON1-DIY."""
import datetime
import math
import os
import zipfile

from shapely.geometry import Polygon, MultiPolygon

GEN = "ON1-DIY generator (hardware/pcb_diy/tools)"


def fmt(v):
    return "%d" % int(round(v * 1e6))


class GerberWriter:
    def __init__(self, function, polarity="Positive", side=None):
        self.lines = []
        self.aps = {}
        self.next_d = 10
        self.function = function
        self.polarity = polarity
        self.body = []
        self.cur_ap = None

    def ap(self, kind, *dims):
        key = (kind,) + tuple(round(d, 4) for d in dims)
        if key not in self.aps:
            self.aps[key] = self.next_d
            self.next_d += 1
        return self.aps[key]

    def select(self, d):
        if self.cur_ap != d:
            self.body.append("D%d*" % d)
            self.cur_ap = d

    def flash(self, x, y, kind, *dims):
        self.select(self.ap(kind, *dims))
        self.body.append("X%sY%sD03*" % (fmt(x), fmt(y)))

    def stroke(self, pts, width):
        if len(pts) < 2:
            return
        self.select(self.ap("C", width))
        self.body.append("X%sY%sD02*" % (fmt(pts[0][0]), fmt(pts[0][1])))
        for x, y in pts[1:]:
            self.body.append("X%sY%sD01*" % (fmt(x), fmt(y)))

    def region(self, ring, dark=True):
        self.body.append("%LPD*%" if dark else "%LPC*%")
        self.body.append("G36*")
        pts = list(ring)
        self.body.append("X%sY%sD02*" % (fmt(pts[0][0]), fmt(pts[0][1])))
        for x, y in pts[1:]:
            self.body.append("X%sY%sD01*" % (fmt(x), fmt(y)))
        self.body.append("G37*")
        if not dark:
            self.body.append("%LPD*%")

    def polygons(self, geom):
        """Fill shapely (Multi)Polygon: exteriors dark, holes clear, larger first."""
        polys = sorted(getattr(geom, "geoms", [geom]), key=lambda p: -p.area)
        for p in polys:
            if p.is_empty:
                continue
            self.region(p.exterior.coords, True)
            for h in p.interiors:
                self.region(h.coords, False)

    def write(self, path, comment=""):
        now = datetime.datetime(2026, 11, 10).strftime("%Y-%m-%dT%H:%M:%S")
        out = ["G04 ON1-DIY Rev A -- Orman Nobetcisi ON-1 home-made carrier board*",
               "G04 %s*" % comment if comment else "G04 *",
               "%TF.GenerationSoftware,Algosense,ON1-DIY-gen,RevA*%",
               "%%TF.CreationDate,%s*%%" % now,
               "%TF.ProjectId,ON1-DIY,0001,RevA*%",
               "%%TF.FileFunction,%s*%%" % self.function,
               "%%TF.FilePolarity,%s*%%" % self.polarity,
               "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%", "G01*", "G75*"]
        for key, d in sorted(self.aps.items(), key=lambda kv: kv[1]):
            kind = key[0]
            if kind == "C":
                out.append("%%ADD%dC,%.4f*%%" % (d, key[1]))
            elif kind == "R":
                out.append("%%ADD%dR,%.4fX%.4f*%%" % (d, key[1], key[2]))
            elif kind == "O":
                out.append("%%ADD%dO,%.4fX%.4f*%%" % (d, key[1], key[2]))
        out += self.body
        out.append("M02*")
        with open(path, "w", newline="\n") as fh:
            fh.write("\n".join(out) + "\n")


def flash_pad(gw, x, y, w, h, shape, grow=0.0):
    w, h = w + 2 * grow, h + 2 * grow
    if shape == "C":
        gw.flash(x, y, "C", w)
    elif shape == "R":
        gw.flash(x, y, "R", w, h)
    else:
        gw.flash(x, y, "O", w, h)


def write_excellon(path, holes):
    """holes: list of (x, y, d, plated:bool)."""
    tools = sorted({round(d, 2) for (_, _, d, _) in holes})
    tnum = {d: i + 1 for i, d in enumerate(tools)}
    out = ["M48", "; DRILL file {ON1-DIY Rev A} -- Orman Nobetcisi ON-1 home-made carrier",
           "; FORMAT={-:-/ absolute / metric / decimal}",
           "; Single-sided board: all holes are non-plated (NPTH) on a 1-layer fab order",
           "; #@! TF.FileFunction,NonPlated,1,1,NPTH", "FMAT,2", "METRIC,TZ"]
    for d in tools:
        out.append("T%dC%.3f" % (tnum[d], d))
    out += ["%", "G90", "G05"]
    for d in tools:
        out.append("T%d" % tnum[d])
        pts = sorted([(x, y) for (x, y, dd, _) in holes if round(dd, 2) == d], key=lambda p: (round(p[1], 1), p[0]))
        for x, y in pts:
            out.append("X%.3fY%.3f" % (x, y))
    out += ["T0", "M30"]
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return {d: sum(1 for h in holes if round(h[2], 2) == d) for d in tools}


def zip_files(zpath, files):
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.basename(f))
