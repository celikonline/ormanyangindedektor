"""Print artwork (1:1 A4 PDFs with reportlab) and 600 dpi PNG previews (Pillow)."""
import math
import os

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black, white

FONT = "Helvetica"
FONTB = "Helvetica-Bold"


def setup_fonts():
    global FONT, FONTB
    for reg, bold in ((r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("UIF", reg))
            pdfmetrics.registerFont(TTFont("UIFB", bold))
            FONT, FONTB = "UIF", "UIFB"
            return


GREEN = Color(0x1F / 255, 0x4D / 255, 0x3A / 255)
ORANGE = Color(0xE4 / 255, 0x57 / 255, 0x2E / 255)


# ---------------------------------------------------------------- PDF helpers
class Sheet:
    def __init__(self, path, title, pagesize=A4):
        self.c = canvas.Canvas(path, pagesize=pagesize)
        self.c.setTitle(title)
        self.c.setAuthor("Algosense - Orman Nobetcisi ON-1")
        self.c.setSubject("ON1-DIY Rev A")
        self.W, self.H = pagesize[0] / mm, pagesize[1] / mm

    def text(self, x, y, s, size=10, bold=False, color=black, anchor="l"):
        c = self.c
        c.setFillColor(color)
        c.setFont(FONTB if bold else FONT, size)
        if anchor == "l":
            c.drawString(x * mm, y * mm, s)
        elif anchor == "c":
            c.drawCentredString(x * mm, y * mm, s)
        else:
            c.drawRightString(x * mm, y * mm, s)

    def para(self, x, y, lines, size=9, lead=1.35, bold_first=False, color=black):
        for i, s in enumerate(lines):
            self.text(x, y - i * size * lead * 0.3528, s, size, bold=(bold_first and i == 0), color=color)
        return y - len(lines) * size * lead * 0.3528

    def box(self, x, y, w, h, stroke=black, fill=None, lw=0.3):
        c = self.c
        c.setLineWidth(lw * mm)
        c.setStrokeColor(stroke)
        if fill is not None:
            c.setFillColor(fill)
        c.rect(x * mm, y * mm, w * mm, h * mm, stroke=1, fill=1 if fill is not None else 0)

    def scale_bar(self, x, y, length=50.0, color=black):
        c = self.c
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(0.25 * mm)
        c.line(x * mm, y * mm, (x + length) * mm, y * mm)
        for i in range(0, int(length) + 1, 5):
            h = 2.5 if i % 10 == 0 else 1.4
            c.line((x + i) * mm, y * mm, (x + i) * mm, (y + h) * mm)
        for i in range(0, int(length), 10):
            if (i // 10) % 2 == 0:
                c.rect((x + i) * mm, (y - 1.2) * mm, 10 * mm, 1.2 * mm, stroke=0, fill=1)
        c.setFont(FONT, 7)
        for i in range(0, int(length) + 1, 10):
            c.drawCentredString((x + i) * mm, (y + 3.1) * mm, "%d" % i)
        c.drawString((x + length + 2) * mm, (y - 0.6) * mm, "mm  (cetvelle ölçün: tam 50,0 mm olmalı)")

    def save(self):
        self.c.showPage()
        self.c.save()


def poly_path(c, poly, ox, oy, mirror, W, scale=1.0):
    p = c.beginPath()
    for ring in [poly.exterior] + list(poly.interiors):
        pts = list(ring.coords)
        for i, (x, y) in enumerate(pts):
            X = (W - x) if mirror else x
            if i == 0:
                p.moveTo((ox + X * scale) * mm, (oy + y * scale) * mm)
            else:
                p.lineTo((ox + X * scale) * mm, (oy + y * scale) * mm)
        p.close()
    return p


def draw_copper(sh, copper, holes, outline, ox, oy, W, mirror=False, negative=False, scale=1.0,
                drill_dot=0.6, margin=3.0, H=75.0):
    c = sh.c
    fg, bg = (white, black) if negative else (black, white)
    if negative:
        c.setFillColor(black)
        c.rect((ox - margin) * mm, (oy - margin) * mm, (W * scale + 2 * margin) * mm, (H * scale + 2 * margin) * mm,
               stroke=0, fill=1)
    c.setFillColor(fg)
    for poly in sorted(getattr(copper, "geoms", [copper]), key=lambda p: -p.area):
        c.drawPath(poly_path(c, poly, ox, oy, mirror, W, scale), stroke=0, fill=1, fillMode=1)  # even-odd
    # drill guide dots (centre marks) — helps the drill bit to centre
    c.setFillColor(bg)
    for (x, y, d, npth) in holes:
        X = (W - x) if mirror else x
        if npth:
            c.setStrokeColor(fg)
            c.setLineWidth(0.15 * mm)
            c.circle((ox + X * scale) * mm, (oy + y * scale) * mm, d / 2 * scale * mm, stroke=1, fill=0)
            c.line((ox + (X - 1) * scale) * mm, (oy + y * scale) * mm, (ox + (X + 1) * scale) * mm, (oy + y * scale) * mm)
            c.line((ox + X * scale) * mm, (oy + (y - 1) * scale) * mm, (ox + X * scale) * mm, (oy + (y + 1) * scale) * mm)
        else:
            c.circle((ox + X * scale) * mm, (oy + y * scale) * mm, drill_dot / 2 * scale * mm, stroke=0, fill=1)
    # board outline (cut line) and corner marks
    c.setStrokeColor(fg if negative else Color(0.35, 0.35, 0.35))
    c.setLineWidth(0.12 * mm)
    p = c.beginPath()
    for i, (x, y) in enumerate(outline):
        X = (W - x) if mirror else x
        (p.moveTo if i == 0 else p.lineTo)((ox + X * scale) * mm, (oy + y * scale) * mm)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    if not negative:
        c.setStrokeColor(black)
        c.setLineWidth(0.15 * mm)
        for (cx, cy, dx, dy) in ((0, 0, -1, -1), (W, 0, 1, -1), (0, H, -1, 1), (W, H, 1, 1)):
            X, Y = ox + cx * scale, oy + cy * scale
            c.line((X + dx * 1.5) * mm, Y * mm, (X + dx * 5) * mm, Y * mm)
            c.line(X * mm, (Y + dy * 1.5) * mm, X * mm, (Y + dy * 5) * mm)


def draw_strokes(c, strokes, ox, oy, W, mirror=False, scale=1.0, color=black, wscale=1.0):
    c.setStrokeColor(color)
    c.setLineCap(1)
    c.setLineJoin(1)
    for pts, w in strokes:
        c.setLineWidth(w * scale * wscale * mm)
        p = c.beginPath()
        for i, (x, y) in enumerate(pts):
            X = (W - x) if mirror else x
            (p.moveTo if i == 0 else p.lineTo)((ox + X * scale) * mm, (oy + y * scale) * mm)
        c.drawPath(p, stroke=1, fill=0)


# ---------------------------------------------------------------- PNG rendering
class Canvas2:
    """Supersampled Pillow canvas in board coordinates."""

    def __init__(self, W, H, dpi=600, margin=2.0, ss=2, bg=(255, 255, 255), mirror=False):
        self.s = dpi / 25.4 * ss
        self.ss = ss
        self.margin = margin
        self.W, self.H = W, H
        self.mirror = mirror
        self.size = (int((W + 2 * margin) * self.s), int((H + 2 * margin) * self.s))
        self.im = Image.new("RGB", self.size, bg)
        self.d = ImageDraw.Draw(self.im)

    def T(self, x, y):
        if self.mirror:
            x = self.W - x
        return ((x + self.margin) * self.s, (self.H + self.margin - y) * self.s)

    def mask_of(self, geom):
        m = Image.new("L", self.size, 0)
        d = ImageDraw.Draw(m)
        for poly in sorted(getattr(geom, "geoms", [geom]), key=lambda p: -p.area):
            if poly.is_empty:
                continue
            d.polygon([self.T(*p) for p in poly.exterior.coords], fill=255)
            for h in poly.interiors:
                d.polygon([self.T(*p) for p in h.coords], fill=0)
        return m

    def fill(self, geom, color, alpha=255):
        m = self.mask_of(geom)
        if alpha < 255:
            m = m.point(lambda v: v * alpha // 255)
        self.im.paste(Image.new("RGB", self.size, color), (0, 0), m)

    def strokes(self, strokes, color, wmin=0.0):
        for pts, w in strokes:
            w = max(w, wmin)
            r = w / 2 * self.s
            P = [self.T(*p) for p in pts]
            self.d.line(P, fill=color, width=max(1, int(round(w * self.s))))
            for x, y in P:
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def circles(self, pts, d, color):
        r = d / 2 * self.s
        for (x, y) in pts:
            X, Y = self.T(x, y)
            self.d.ellipse([X - r, Y - r, X + r, Y + r], fill=color)

    def save(self, path, dpi=600):
        out = self.im.resize((self.size[0] // self.ss, self.size[1] // self.ss), Image.LANCZOS)
        out.save(path, dpi=(dpi, dpi))
        return out
