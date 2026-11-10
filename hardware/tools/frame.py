# -*- coding: utf-8 -*-
"""A3 drawing frame + Turkish title block shared by schematic and mechanical sheets."""
from schlib import esc, FONT

GREEN = "#1F4D3A"
ORANGE = "#E4572E"
SAND = "#F4F1EA"
ANTH = "#1B1F1D"


def frame_svg(W=4200, H=2970, title="", subtitle="", sheet="1/1", doc="", scale="—", rev="A",
              date="2026-11-10", zones=True, unit=1.0, extra_rows=None):
    """Returns SVG elements (list of str). unit=1 for 0.1 mm user units, 0.1 for mm units."""
    u = lambda v: v * unit
    o = []
    m1, m2 = u(40), u(80)
    o.append(f'<rect x="{m1}" y="{m1}" width="{W-2*m1}" height="{H-2*m1}" fill="none" stroke="#000" stroke-width="{u(5)}"/>')
    o.append(f'<rect x="{m2}" y="{m2}" width="{W-2*m2}" height="{H-2*m2}" fill="none" stroke="#000" stroke-width="{u(3)}"/>')
    if zones:
        nx, ny = 8, 6
        zw, zh = (W - 2 * m2) / nx, (H - 2 * m2) / ny
        for i in range(nx):
            cx = m2 + zw * (i + 0.5)
            for yy in (m1 + (m2 - m1) / 2, H - m1 - (m2 - m1) / 2):
                o.append(f'<text x="{cx}" y="{yy+u(9)}" font-family="{FONT}" font-size="{u(26)}" text-anchor="middle">{i+1}</text>')
            if i:
                x = m2 + zw * i
                o.append(f'<line x1="{x}" y1="{m1}" x2="{x}" y2="{m2}" stroke="#000" stroke-width="{u(2)}"/>')
                o.append(f'<line x1="{x}" y1="{H-m2}" x2="{x}" y2="{H-m1}" stroke="#000" stroke-width="{u(2)}"/>')
        for j in range(ny):
            cy = m2 + zh * (j + 0.5)
            L = "ABCDEF"[j]
            for xx in (m1 + (m2 - m1) / 2, W - m1 - (m2 - m1) / 2):
                o.append(f'<text x="{xx}" y="{cy+u(9)}" font-family="{FONT}" font-size="{u(26)}" text-anchor="middle">{L}</text>')
            if j:
                y = m2 + zh * j
                o.append(f'<line x1="{m1}" y1="{y}" x2="{m2}" y2="{y}" stroke="#000" stroke-width="{u(2)}"/>')
                o.append(f'<line x1="{W-m2}" y1="{y}" x2="{W-m1}" y2="{y}" stroke="#000" stroke-width="{u(2)}"/>')
    # title block (bottom-right) 1220 x 290
    tw, th = u(1220), u(290)
    x0, y0 = W - m2 - tw, H - m2 - th
    o.append(f'<rect x="{x0}" y="{y0}" width="{tw}" height="{th}" fill="#fff" stroke="#000" stroke-width="{u(3)}"/>')
    # brand band
    o.append(f'<rect x="{x0}" y="{y0}" width="{u(330)}" height="{th}" fill="{GREEN}"/>')
    o.append(f'<circle cx="{x0+u(165)}" cy="{y0+u(95)}" r="{u(48)}" fill="none" stroke="{SAND}" stroke-width="{u(6)}"/>')
    o.append(f'<path d="M{x0+u(165)},{y0+u(62)} L{x0+u(195)},{y0+u(118)} L{x0+u(135)},{y0+u(118)} Z" fill="{ORANGE}"/>')
    o.append(f'<circle cx="{x0+u(165)}" cy="{y0+u(98)}" r="{u(9)}" fill="{SAND}"/>')
    o.append(f'<text x="{x0+u(165)}" y="{y0+u(190)}" font-family="{FONT}" font-size="{u(34)}" font-weight="bold" fill="#fff" text-anchor="middle">ORMAN</text>')
    o.append(f'<text x="{x0+u(165)}" y="{y0+u(228)}" font-family="{FONT}" font-size="{u(34)}" font-weight="bold" fill="#fff" text-anchor="middle">NÖBETÇİSİ</text>')
    o.append(f'<text x="{x0+u(165)}" y="{y0+u(262)}" font-family="{FONT}" font-size="{u(22)}" fill="{SAND}" text-anchor="middle">Model ON-1</text>')
    gx = x0 + u(330)
    gw = tw - u(330)
    rows = [u(0), u(110), u(170), u(230), u(290)]
    for r in rows[1:-1]:
        o.append(f'<line x1="{gx}" y1="{y0+r}" x2="{x0+tw}" y2="{y0+r}" stroke="#000" stroke-width="{u(2)}"/>')

    def cell(cx, cy, cw, label, val, vs=26, bold=False):
        o.append(f'<text x="{cx+u(10)}" y="{cy+u(20)}" font-family="{FONT}" font-size="{u(15)}" fill="#555">{esc(label)}</text>')
        o.append(f'<text x="{cx+u(10)}" y="{cy+u(48)}" font-family="{FONT}" font-size="{u(vs)}" '
                 f'font-weight="{"bold" if bold else "normal"}" fill="#000">{esc(val)}</text>')

    # row 1: title
    o.append(f'<text x="{gx+u(14)}" y="{y0+u(24)}" font-family="{FONT}" font-size="{u(15)}" fill="#555">Proje / Çizim başlığı</text>')
    o.append(f'<text x="{gx+u(14)}" y="{y0+u(62)}" font-family="{FONT}" font-size="{u(33)}" font-weight="bold">{esc(title)}</text>')
    o.append(f'<text x="{gx+u(14)}" y="{y0+u(96)}" font-family="{FONT}" font-size="{u(23)}">{esc(subtitle)}</text>')
    # row 2
    cw = gw / 4
    for i in range(1, 4):
        o.append(f'<line x1="{gx+cw*i}" y1="{y0+rows[1]}" x2="{gx+cw*i}" y2="{y0+rows[3]}" stroke="#000" stroke-width="{u(2)}"/>')
    cell(gx, y0 + rows[1], cw, "Doküman no", doc, 22, True)
    cell(gx + cw, y0 + rows[1], cw, "Revizyon", rev, 26, True)
    cell(gx + 2 * cw, y0 + rows[1], cw, "Tarih", date, 24)
    cell(gx + 3 * cw, y0 + rows[1], cw, "Sayfa", sheet, 26, True)
    cell(gx, y0 + rows[2], cw, "Boyut", "A3 yatay", 22)
    cell(gx + cw, y0 + rows[2], cw, "Ölçek", scale, 22)
    cell(gx + 2 * cw, y0 + rows[2], cw, "Çizen", "Algosense Danışmanlık", 19)
    cell(gx + 3 * cw, y0 + rows[2], cw, "Onay", "—", 22)
    o.append(f'<text x="{gx+u(14)}" y="{y0+u(268)}" font-family="{FONT}" font-size="{u(17)}" fill="#333">'
             f'{esc("Tek doğru kaynak: SPEC.md Rev A • Bu çizim programla üretilmiştir (hardware/tools) — elle düzenlemeyin.")}</text>')
    return o, (x0, y0, tw, th)
