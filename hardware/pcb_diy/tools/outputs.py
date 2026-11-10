"""PNG previews and printable PDFs for ON1-DIY."""
import math
import os
from collections import defaultdict

from shapely.geometry import Point
from shapely.ops import unary_union
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white

import artwork as AW
import copper
from artwork import Sheet, draw_copper, draw_strokes, Canvas2

REV = "Rev A — 2026-11-10"
TITLE = "Orman Nöbetçisi ON-1  •  ON1-DIY ev yapımı taşıyıcı kart"


# ====================================================================== PNG
def make_pngs(b, routes, copper_all, holes, strokes, odir):
    os.makedirs(odir, exist_ok=True)
    W, H = b.w, b.h
    outline = copper.Polygon(b.outline())
    pads = copper.pad_items(b, routes)
    pad_geo = unary_union([p["poly"] for p in pads])
    th = [(x, y) for (x, y, d, n) in holes if not n]
    th_d = {(x, y): d for (x, y, d, n) in holes}
    npth = [(x, y, d) for (x, y, d, n) in holes if n]

    # 1) copper, black on white, top view (as in the Gerber)
    cv = Canvas2(W, H)
    cv.strokes([(list(outline.exterior.coords), 0.1)], (150, 150, 150))
    cv.fill(copper_all, (0, 0, 0))
    for (x, y) in th:
        cv.circles([(x, y)], th_d[(x, y)], (255, 255, 255))
    for (x, y, d) in npth:
        cv.circles([(x, y)], d, (255, 255, 255))
    cv.save(os.path.join(odir, "ON1-DIY_bakir_600dpi.png"))

    # 2) silkscreen, black on white, with pad outlines for orientation
    cv = Canvas2(W, H)
    cv.fill(outline, (250, 250, 250))
    cv.strokes([(list(outline.exterior.coords), 0.15)], (0, 0, 0))
    cv.fill(pad_geo, (200, 200, 200))
    for (x, y) in th:
        cv.circles([(x, y)], th_d[(x, y)], (255, 255, 255))
    cv.strokes(strokes, (0, 0, 0))
    for (x, y, d) in npth:
        cv.circles([(x, y)], d, (255, 255, 255))
    cv.save(os.path.join(odir, "ON1-DIY_serigrafi_600dpi.png"))

    # 3) composite "x-ray" preview: brand-green board, copper seen through, silkscreen
    cv = Canvas2(W, H, bg=(244, 241, 234))
    cv.fill(outline, (31, 77, 58))
    cv.fill(copper_all, (196, 128, 62), alpha=150)
    cv.fill(pad_geo, (214, 216, 219))
    cv.strokes(strokes, (250, 250, 245))
    for (x, y) in th:
        cv.circles([(x, y)], th_d[(x, y)], (35, 35, 35))
    for (x, y, d) in npth:
        cv.circles([(x, y)], d, (244, 241, 234))
    for j in routes["jumpers"]:
        cv.strokes([([tuple(j["a"]), tuple(j["b"])], 0.6)], (230, 230, 232))
    cv.save(os.path.join(odir, "ON1-DIY_onizleme_kompozit_600dpi.png"))

    # 4) realistic top side of a home-made single-sided board (bare FR4, holes, silkscreen)
    cv = Canvas2(W, H, bg=(244, 241, 234))
    cv.fill(outline, (205, 186, 128))
    cv.fill(copper_all, (182, 160, 98), alpha=110)      # copper faintly visible through FR4
    cv.strokes(strokes, (250, 250, 250))
    for (x, y) in th:
        cv.circles([(x, y)], th_d[(x, y)] + 0.5, (150, 132, 80))
        cv.circles([(x, y)], th_d[(x, y)], (40, 34, 25))
    for (x, y, d) in npth:
        cv.circles([(x, y)], d, (244, 241, 234))
    for j in routes["jumpers"]:
        cv.strokes([([tuple(j["a"]), tuple(j["b"])], 0.6)], (200, 200, 205))
    cv.save(os.path.join(odir, "ON1-DIY_onizleme_ust_600dpi.png"))

    # 5) realistic bottom (copper side, mirrored = as you see it when you flip the board)
    cv = Canvas2(W, H, bg=(244, 241, 234), mirror=True)
    cv.fill(outline, (176, 140, 78))
    cv.fill(copper_all, (205, 210, 214))                  # tinned copper
    for (x, y) in th:
        cv.circles([(x, y)], th_d[(x, y)], (40, 34, 25))
    for (x, y, d) in npth:
        cv.circles([(x, y)], d, (244, 241, 234))
    cv.save(os.path.join(odir, "ON1-DIY_onizleme_alt_600dpi.png"))


# ====================================================================== PDF
PRINT_NOTE = [
    "YAZDIRMA: %100 / \"Gerçek boyut\" seçin.  \"Sayfaya sığdır\", \"Fit to page\", \"Küçült\" KAPALI olmalı.",
    "Yazdırdıktan sonra 50 mm ölçek çubuğunu cetvelle ölçün; 50,0 mm değilse tekrar yazdırın.",
]


def header(sh, title, sub, note_lines, y_top=None):
    W = sh.W
    y = y_top or sh.H - 12
    sh.text(12, y, TITLE, 9, color=AW.GREEN)
    sh.text(W - 12, y, REV, 9, anchor="r", color=AW.GREEN)
    sh.text(12, y - 8, title, 15, bold=True)
    sh.text(12, y - 13.5, sub, 9)
    # big printing note box
    bh = 6 + 4.2 * len(note_lines)
    sh.box(10, y - 20 - bh, W - 20, bh, stroke=AW.ORANGE, fill=Color(1, 0.95, 0.92), lw=0.6)
    yy = y - 20 - 5.2
    for i, s in enumerate(note_lines):
        sh.text(14, yy - i * 4.2, s, 9.5 if i < 2 else 8.5, bold=(i < 2), color=black)
    return y - 22 - bh


def make_pdfs(b, routes, copper_all, holes, strokes, counts, odir):
    os.makedirs(odir, exist_ok=True)
    W, H = b.w, b.h
    outline = b.outline()
    hl = [(x, y, d, n) for (x, y, d, n) in holes]

    # ---------------------------------------------------------------- toner transfer
    sh = Sheet(os.path.join(odir, "ON1-DIY_bakir_toner_transfer.pdf"), "ON1-DIY bakir - toner transfer")
    y0 = header(sh, "Alt bakır (B.Cu) — TONER TRANSFER çıktısı (2 kopya)",
                "Siyah = bakır kalacak.  Lazer yazıcı + kuşe/parlak dergi kâğıdı veya toner-transfer kâğıdı.",
                PRINT_NOTE + [
                    "Bu çıktı AYNALANMAMIŞTIR (bilerek). Bakır alt yüzdedir ve çizim üstten bakışla yapılmıştır; kâğıt",
                    "yüzü bakıra gelecek şekilde ters çevrilince görüntü kendiliğinden aynalanır ve bakırda doğru desen oluşur.",
                    "Kontrol: kâğıtta \"ON1-DIY ALT\" yazısı düz okunur; bakırda (alttan bakınca) ters okunur. Beyaz noktalar matkap merkezidir."])
    ox = (sh.W - W) / 2
    for k, oy in enumerate((y0 - 8 - H, y0 - 8 - H - 12 - H)):
        draw_copper(sh, copper_all, hl, outline, ox, oy, W, H=H)
        sh.text(ox, oy + H + 2, "Kopya %d%s" % (k + 1, "" if k == 0 else " (yedek)"), 8)
    sh.scale_bar(ox, 14)
    sh.text(12, 6, "Kart: 100 × 75 mm, 1 katman, FR4 35 µm.  Ütü: en yüksek (pamuk) ısı, 3-5 dk bastırarak; laminatör: 4-6 geçiş.", 7.5)
    sh.save()

    # ---------------------------------------------------------------- positive photoresist film
    sh = Sheet(os.path.join(odir, "ON1-DIY_bakir_fotorezist_film.pdf"), "ON1-DIY bakir - pozitif fotorezist filmi")
    y0 = header(sh, "Alt bakır (B.Cu) — POZİTİF FOTOREZİST için asetat film",
                "Siyah = opak = bakır kalacak (pozitif rezist: ışık gören yer gelişir/çözülür).  Asetat/transparan film, lazer yazıcı.",
                PRINT_NOTE + [
                    "Toner yüzü bakıra (rezist yüzüne) değecek şekilde yerleştirin → ışık saçılması/alttan sızma en az olur.",
                    "Bu nedenle çıktı AYNALANMAMIŞTIR: film toner yüzü aşağı konduğunda bakırda doğru (alttan bakış) desen oluşur.",
                    "Yoğunluk için iki filmi üst üste hizalayıp bantlayın (toner yoğunluğu ikiye katlanır). Kontrol yazısı: \"ON1-DIY ALT\"."])
    ox = (sh.W - W) / 2
    for k, oy in enumerate((y0 - 8 - H, y0 - 8 - H - 12 - H)):
        draw_copper(sh, copper_all, hl, outline, ox, oy, W, H=H)
        sh.text(ox, oy + H + 2, "Film %d (iki film üst üste kullanılabilir)" % (k + 1), 8)
    sh.scale_bar(ox, 14)
    sh.text(12, 6, "Pozlama: UV LED (395-405 nm) ~10 cm'den 60-120 s (önce test şeridi). Banyo: %0,5-1 NaOH (veya rezist üreticisinin banyosu).", 7.5)
    sh.save()

    # ---------------------------------------------------------------- negative
    sh = Sheet(os.path.join(odir, "ON1-DIY_bakir_negatif.pdf"), "ON1-DIY bakir - negatif (kuru film)")
    y0 = header(sh, "Alt bakır (B.Cu) — NEGATİF film (negatif kuru film / dry-film)",
                "Şeffaf (beyaz) = bakır kalacak, siyah = aşınacak.  Mavi/yeşil kuru film fotorezistler genelde NEGATİF çalışır.",
                PRINT_NOTE + [
                    "Toner yüzü bakıra değecek şekilde yerleştirin; çıktı bu yüzden AYNALANMAMIŞTIR (alt katman, üstten bakış çizimi).",
                    "Kuru filmi 100-110 °C laminatörle bakıra yapıştırın, filmle UV pozlayın, koruyucu folyoyu soyup %1 Na2CO3 ile banyo yapın.",
                    "Kontrol yazısı \"ON1-DIY ALT\" kâğıtta düz okunmalı. Siyah noktalar matkap merkezidir (aşınınca pedde küçük delik kalır)."])
    ox = (sh.W - W) / 2
    for k, oy in enumerate((y0 - 12 - H, y0 - 12 - H - 16 - H)):
        draw_copper(sh, copper_all, hl, outline, ox, oy, W, negative=True, H=H)
        sh.text(ox, oy + H + 4.5, "Film %d" % (k + 1), 8)
    sh.scale_bar(ox, 14)
    sh.save()

    # ---------------------------------------------------------------- placement / silkscreen
    placement_pdf(b, routes, strokes, hl, os.path.join(odir, "ON1-DIY_yerlesim_ust.pdf"))

    # ---------------------------------------------------------------- drill map
    drill_pdf(b, routes, hl, counts, os.path.join(odir, "ON1-DIY_delik_haritasi.pdf"))


def pads_outline(sh, b, routes, ox, oy, scale, mirror=False, only_smd=False, fill_smd=None):
    c = sh.c
    for it in copper.pad_items(b, routes):
        if only_smd and it["drill"]:
            continue
        poly = it["poly"]
        c.setLineWidth(0.12 * mm)
        c.setStrokeColor(Color(0.45, 0.45, 0.45))
        if it["drill"] is None and fill_smd is not None:
            c.setFillColor(fill_smd)
            c.drawPath(AW.poly_path(c, poly, ox, oy, mirror, b.w, scale), stroke=1, fill=1)
        else:
            c.drawPath(AW.poly_path(c, poly, ox, oy, mirror, b.w, scale), stroke=1, fill=0)
        if it["drill"]:
            X = (b.w - it["x"]) if mirror else it["x"]
            c.circle((ox + X * scale) * mm, (oy + it["y"] * scale) * mm, it["drill"] / 2 * scale * mm, stroke=1, fill=0)


def value_labels(sh, b, ox, oy, scale, size):
    c = sh.c
    c.setFillColor(Color(0.0, 0.25, 0.6))
    c.setFont(AW.FONT, size)
    for comp in b.comps:
        if not comp.show_value or not comp.value or comp.ref.startswith("H"):
            continue
        poly = comp.court_poly()
        if not poly:
            continue
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if comp.ref.startswith("R") and comp.ref not in ("R8", "R9", "R10", "R11", "R12", "R13"):
            cy = cy - 1.9 if comp.rot in (0, 180) else cy
            cx = cx + 2.0 if comp.rot in (90, 270) else cx
        elif comp.ref == "U1":
            cy = cy - 4
        else:
            cy = min(ys) - 0.9
        c.drawCentredString((ox + cx * scale) * mm, (oy + cy * scale) * mm, comp.value)


def placement_pdf(b, routes, strokes, hl, path):
    W, H = b.w, b.h
    sh = Sheet(path, "ON1-DIY yerlesim (ust yuz)")
    y0 = header(sh, "Üst yüz yerleşim / serigrafi — 1:1",
                "Parçalar ÜST yüze (bakırsız yüz) takılır, bacaklar alt yüzdeki bakıra lehimlenir. Değerler mavi.",
                PRINT_NOTE + [
                    "Bu sayfa 1:1'dir: üst yüze (bakırsız) yapıştırıp delik şablonu / serigrafi yerine kullanabilirsiniz (aynalanmamış).",
                    "Kalın gri çift çizgi + J-Wn = üst yüzde düz tel köprü (atlama teli). (ALT) işaretli SOT-23'ler bakır tarafına lehimlenir.",
                    "Kutup: elektrolitik '+' kare ped; diyot bandı = K (kare ped); LED düz kenar = K; TO-92 düz yüz çizgisi; header 1. pin kare."])
    ox = (sh.W - W) / 2
    oy = y0 - 10 - H
    sh.box(ox, oy, W, H, stroke=Color(0.6, 0.6, 0.6), lw=0.1)
    pads_outline(sh, b, routes, ox, oy, 1.0)
    draw_strokes(sh.c, strokes, ox, oy, W)
    jumper_marks(sh, routes, ox, oy, 1.0)
    value_labels(sh, b, ox, oy, 1.0, 3.2)
    sh.scale_bar(ox, oy - 12)
    legend(sh, b, routes, 12, oy - 22)
    sh.c.showPage()
    # page 2: 2:1 landscape
    sh.c.setPageSize(landscape(A4))
    sh.W, sh.H = 297, 210
    sh.text(12, 200, TITLE + "   —   Üst yüz yerleşim, 2:1 büyütülmüş (okuma kolaylığı için; ölçü için 1. sayfayı kullanın)", 9,
            color=AW.GREEN)
    ox, oy = (297 - 2 * W) / 2, 12
    pads_outline(sh, b, routes, ox, oy, 2.0)
    draw_strokes(sh.c, strokes, ox, oy, W, scale=2.0, wscale=0.8)
    jumper_marks(sh, routes, ox, oy, 2.0)
    value_labels(sh, b, ox, oy, 2.0, 5.2)
    sh.c.showPage()
    # page 3: bottom view (copper side) with the SMD parts
    sh.c.setPageSize(landscape(A4))
    sh.text(12, 200, TITLE + "   —   ALT yüz (bakır tarafı) görünümü, 2:1, aynalı: SOT-23 parçalar buraya lehimlenir", 9,
            color=AW.GREEN)
    geoms = copper.net_geometries(b, routes)
    cu = unary_union(list(geoms.values()))
    ox, oy = (297 - 2 * W) / 2, 12
    c = sh.c
    c.setFillColor(Color(0.85, 0.62, 0.35))
    for poly in getattr(cu, "geoms", [cu]):
        c.drawPath(AW.poly_path(c, poly, ox, oy, True, W, 2.0), stroke=0, fill=1, fillMode=1)
    c.setFillColor(white)
    for (x, y, d, n) in hl:
        c.circle((ox + (W - x) * 2) * mm, (oy + y * 2) * mm, d * mm, stroke=0, fill=1)
    c.setStrokeColor(black)
    c.setLineWidth(0.2 * mm)
    p = c.beginPath()
    for i, (x, y) in enumerate(b.outline()):
        (p.moveTo if i == 0 else p.lineTo)((ox + (W - x) * 2) * mm, (oy + y * 2) * mm)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    for comp in b.comps:
        if comp.side != "bottom":
            continue
        for pd, x, y, w, h, net in comp.pads():
            c.setFillColor(Color(0.1, 0.1, 0.1))
            c.setFont(AW.FONTB, 7)
            c.drawCentredString((ox + (W - x) * 2) * mm, (oy + y * 2 - 1.2) * mm, pd.name)
        cx, cy = comp.x, comp.y
        c.setFillColor(AW.ORANGE)
        c.setFont(AW.FONTB, 9)
        c.drawString((ox + (W - cx) * 2 + 5) * mm, (oy + cy * 2) * mm, "%s %s" % (comp.ref, comp.value))
    sh.text(12, 6, "G = kapı (gate), S = kaynak (source), D = savak (drain). AO3401A gövdesindeki nokta/pin-1 = G. Önce bir pedi kalaylayın, "
                   "parçayı cımbızla tutup o pedi eritin, sonra diğer bacakları lehimleyin.", 8)
    sh.save()


def jumper_marks(sh, routes, ox, oy, scale):
    c = sh.c
    for i, j in enumerate(routes["jumpers"]):
        (x1, y1), (x2, y2) = j["a"], j["b"]
        c.setStrokeColor(AW.ORANGE)
        c.setLineWidth(0.7 * scale * mm)
        c.line((ox + x1 * scale) * mm, (oy + y1 * scale) * mm, (ox + x2 * scale) * mm, (oy + y2 * scale) * mm)


def legend(sh, b, routes, x, y):
    jl = ["J-W%d: %s, %.2f mm" % (i + 1, j["net"], math.hypot(j["b"][0] - j["a"][0], j["b"][1] - j["a"][1]))
          for i, j in enumerate(routes["jumpers"])]
    lines = ["Atlama telleri (üst yüz, Ø0,6-0,8 mm kalaylı bakır tel, önce bunları takın):"] + \
        ["   " + "    ".join(jl[i:i + 3]) for i in range(0, len(jl), 3)]
    sh.para(x, y, lines, 8, bold_first=True)


def drill_pdf(b, routes, hl, counts, path):
    W, H = b.w, b.h
    sh = Sheet(path, "ON1-DIY delik haritasi")
    y0 = header(sh, "Delik haritası (matkap planı) — 1:1",
                "Üstten bakış. Her delik çapı gerçek boyutta çizildi; harf = matkap ucu (tabloya bakın).",
                PRINT_NOTE + [
                    "Delmeyi aşındırma ve kalaylamadan SONRA, bakır tarafından yapın (pedlerdeki merkez noktası ucu ortalar).",
                    "Önce en küçük uçla tüm delikleri açın, sonra büyük delikleri büyütün. Dik matkap standı + karbür uç önerilir."])
    tools = sorted(counts.keys())
    letters = {d: chr(ord("A") + i) for i, d in enumerate(tools)}
    use = defaultdict(set)
    for it in copper.pad_items(b, routes):
        if it["drill"]:
            use[round(it["drill"], 2)].add(it["ref"].rstrip("0123456789") if not it["ref"].startswith("J-W") else "J-W")
    for comp in b.comps:
        for (_, _, d) in comp.fp.npth:
            use[round(d, 2)].add("M3 montaj")
    ox = (sh.W - W) / 2
    oy = y0 - 10 - H
    c = sh.c
    c.setStrokeColor(Color(0.5, 0.5, 0.5))
    c.setLineWidth(0.12 * mm)
    p = c.beginPath()
    for i, (x, y) in enumerate(b.outline()):
        (p.moveTo if i == 0 else p.lineTo)((ox + x) * mm, (oy + y) * mm)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    for (x, y, d, n) in hl:
        L = letters[round(d, 2)]
        c.setStrokeColor(black)
        c.setLineWidth(0.15 * mm)
        c.circle((ox + x) * mm, (oy + y) * mm, d / 2 * mm, stroke=1, fill=0)
        c.setFillColor(AW.ORANGE if d >= 1.2 else black)
        c.setFont(AW.FONTB, 3.2 if d < 2 else 6)
        c.drawCentredString((ox + x) * mm, (oy + y - 0.55) * mm if d < 2 else (oy + y - 1.0) * mm, L)
    sh.scale_bar(ox, oy - 10)
    # table
    ty = oy - 20
    sh.text(12, ty, "Matkap tablosu", 11, bold=True)
    ty -= 6
    cols = [12, 30, 52, 75, 100]
    for x, s in zip(cols, ["Harf", "Çap (mm)", "Adet", "Matkap ucu", "Kullanıldığı yer"]):
        sh.text(x, ty, s, 8.5, bold=True)
    total = 0
    bits = {0.8: "0,8 mm", 1.0: "1,0 mm", 1.2: "1,2 mm", 1.3: "1,3 mm", 1.5: "1,5 mm", 3.2: "3,2 mm"}
    for d in tools:
        ty -= 4.6
        n = counts[d]
        total += n
        sh.text(cols[0], ty, letters[d], 8.5, bold=True)
        sh.text(cols[1], ty, ("%.1f" % d).replace(".", ","), 8.5)
        sh.text(cols[2], ty, str(n), 8.5)
        sh.text(cols[3], ty, bits.get(d, "%.1f mm" % d), 8.5)
        sh.text(cols[4], ty, ", ".join(sorted(use[d]))[:70], 7.5)
    ty -= 6
    sh.text(12, ty, "TOPLAM: %d delik" % total, 10, bold=True)
    ty -= 6
    sh.para(12, ty, ["Notlar: 0,8 mm uçla tüm küçük delikleri açtıktan sonra büyükleri büyütün. M3 delikleri için 3 mm uç + hafif rayba da olur.",
                     "J-W = üst yüz atlama teli delikleri (bara teli J-W1 Ø1,0 mm tel kullanıyorsa 1,0 mm'ye büyütülebilir).",
                     "1N5822 (D1) bacakları kalındır: 1,5 mm. Klemensler 1,3 mm, TO-220/kablo pedleri 1,2 mm."], 8)
    sh.save()
