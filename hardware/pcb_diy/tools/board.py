"""Generic board model: components placed from footprints, net assignment,
coordinate transforms, and helpers shared by router / outputs."""
import math


class Component:
    def __init__(self, ref, fp, x, y, rot=0, side="top", value="", nets=None,
                 part="", package="", note="", show_value=True):
        self.ref = ref
        self.fp = fp
        self.x, self.y = x, y
        self.rot = rot % 360
        self.side = side
        self.value = value
        self.nets = nets or {}
        self.part = part
        self.package = package
        self.note = note
        self.show_value = show_value

    # local -> board
    def xf(self, lx, ly):
        if self.side == "bottom":
            lx = -lx
        a = math.radians(self.rot)
        c, s = round(math.cos(a), 12), round(math.sin(a), 12)
        return (self.x + lx * c - ly * s, self.y + lx * s + ly * c)

    def pad_dims(self, pad):
        """(w, h) of the pad in board orientation."""
        if self.rot in (90, 270):
            return pad.h, pad.w
        return pad.w, pad.h

    def pads(self):
        for p in self.fp.pads:
            x, y = self.xf(p.x, p.y)
            w, h = self.pad_dims(p)
            yield p, x, y, w, h, self.nets.get(p.name)

    def court_poly(self):
        if not self.fp.court:
            return None
        x0, y0, x1, y1 = self.fp.court
        return [self.xf(x0, y0), self.xf(x1, y0), self.xf(x1, y1), self.xf(x0, y1)]


class Board:
    def __init__(self, w, h, corner=2.0):
        self.w, self.h = w, h
        self.corner = corner
        self.comps = []
        self.copper_texts = []     # (text, x, y, h, anchor, rot)
        self.silk_texts = []       # free silkscreen texts
        self.silk_lines = []       # free silkscreen polylines
        self.net_class = {}        # net -> track width
        self.pad_width = {}        # (ref, pad) -> width override for the connection to this pad
        self.pad_stage = {}        # (ref, pad) -> routing stage override

    def add(self, c):
        self.comps.append(c)
        return c

    def comp(self, ref):
        for c in self.comps:
            if c.ref == ref:
                return c
        raise KeyError(ref)

    def all_pads(self):
        """list of dict(ref, pad, x, y, w, h, shape, drill, net, smd)"""
        out = []
        for c in self.comps:
            for p, x, y, w, h, net in c.pads():
                out.append(dict(ref=c.ref, pad=p.name, x=x, y=y, w=w, h=h, shape=p.shape,
                                drill=p.drill, net=net, smd=p.drill is None))
        return out

    def nets(self):
        d = {}
        for pd in self.all_pads():
            if pd["net"]:
                d.setdefault(pd["net"], []).append(pd)
        return d

    def internal_links(self):
        """Module-internal / jumper connections: list of ((ref,pad),(ref,pad))."""
        out = []
        for c in self.comps:
            for grp in c.fp.internal:
                for a in grp[1:]:
                    out.append(((c.ref, grp[0]), (c.ref, a)))
        return out

    def outline(self, n=8):
        """Board outline polygon with rounded corners."""
        r = self.corner
        pts = []
        for cx, cy, a0 in ((self.w - r, r, -90), (self.w - r, self.h - r, 0),
                           (r, self.h - r, 90), (r, r, 180)):
            for i in range(n + 1):
                a = math.radians(a0 + 90 * i / n)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts
