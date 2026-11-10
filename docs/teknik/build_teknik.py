# -*- coding: utf-8 -*-
"""
Orman Nöbetçisi ON-1 — Teknik Tasarım Dokümanı üreticisi.
SPEC.md, hardware/BOM.csv, hardware/pinout_netlist.md ve görsellerden A4 HTML üretir;
PDF'e dönüştürme headless Chrome ile build.sh tarafından yapılır.

Kullanım:  python docs/teknik/build_teknik.py   (proje kökünden)
"""
import csv, html, io, os, re, sys, glob, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'docs', 'teknik', 'teknik.html')


def rel(p):
    return os.path.relpath(os.path.join(ROOT, p), os.path.dirname(OUT)).replace('\\', '/')


def read(p):
    with open(os.path.join(ROOT, p), encoding='utf-8-sig') as f:
        return f.read()


def esc(s):
    return html.escape(str(s))


# ---------- Mini Markdown (tablolar, başlıklar, listeler, kod) ----------
def md_inline(t):
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', t)
    return t


def md_to_html(md, shift=0):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith('```'):
                buf.append(lines[j]); j += 1
            out.append('<pre>' + esc('\n'.join(buf)) + '</pre>')
            i = j + 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)', ln)
        if m:
            lvl = min(6, len(m.group(1)) + shift)
            out.append(f'<h{lvl}>{md_inline(m.group(2))}</h{lvl}>'); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
            h = '<table class="t"><thead><tr>' + ''.join(f'<th>{md_inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
            for r in rows[1:]:
                h += '<tr>' + ''.join(f'<td>{md_inline(c)}</td>' for c in r) + '</tr>'
            out.append(h + '</tbody></table>'); continue
        if re.match(r'^\s*[-*]\s+', ln):
            buf = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]):
                buf.append('<li>' + md_inline(re.sub(r'^\s*[-*]\s+', '', lines[i])) + '</li>'); i += 1
            out.append('<ul>' + ''.join(buf) + '</ul>'); continue
        if re.match(r'^\s*\d+\.\s+', ln):
            buf = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]):
                buf.append('<li>' + md_inline(re.sub(r'^\s*\d+\.\s+', '', lines[i])) + '</li>'); i += 1
            out.append('<ol>' + ''.join(buf) + '</ol>'); continue
        if ln.startswith('>'):
            out.append('<blockquote>' + md_inline(ln.lstrip('> ')) + '</blockquote>'); i += 1; continue
        if ln.strip() in ('---', ''):
            i += 1; continue
        buf = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|\s*[-*]\s|\s*\d+\.\s|>)', lines[i]):
            buf.append(lines[i]); i += 1
        out.append('<p>' + md_inline(' '.join(buf)) + '</p>')
    return '\n'.join(out)


def spec_section(spec, num):
    """SPEC.md içinden '## <num>.' bölümünü döndürür."""
    m = re.search(rf'^## {num}\.[^\n]*\n(.*?)(?=^## \d+\.|\Z)', spec, flags=re.S | re.M)
    return m.group(1) if m else ''


# ---------- BOM ----------
def bom_table():
    p = os.path.join(ROOT, 'hardware', 'BOM.csv')
    if not os.path.exists(p):
        return '<p class="warn">BOM.csv bulunamadı.</p>', ''
    with open(p, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f, delimiter=';'))
    head, body = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]
    h = '<table class="t bom"><thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in head) + '</tr></thead><tbody>'
    totals = []
    for r in body:
        txt = ' '.join(r).lower()
        is_total = (not r[0].strip() and any(k in txt for k in ('toplam', 'ara toplam', 'subtotal', 'genel'))) or 'toplam' in r[0].lower()
        cls = ' class="tot"' if is_total else ''
        if is_total:
            totals.append(r)
        h += f'<tr{cls}>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>'
    return h + '</tbody></table>', totals


def first_existing(*paths):
    for p in paths:
        hits = glob.glob(os.path.join(ROOT, p))
        if hits:
            return os.path.relpath(sorted(hits)[0], ROOT).replace('\\', '/')
    return None


def fig(path, cap, cls=''):
    if not path:
        return f'<div class="missing">Görsel eksik: {esc(cap)}</div>'
    return f'<figure class="{cls}"><img src="{rel(path)}" alt="{esc(cap)}"><figcaption>{esc(cap)}</figcaption></figure>'


def main():
    spec = read('SPEC.md')
    today = datetime.date(2026, 11, 10).strftime('%d.%m.%Y')
    bom_html, _ = bom_table()
    pin_md = read('hardware/pinout_netlist.md') if os.path.exists(os.path.join(ROOT, 'hardware/pinout_netlist.md')) else ''
    fw_readme = read('firmware/README.md') if os.path.exists(os.path.join(ROOT, 'firmware/README.md')) else ''
    fw_stats = read('docs/teknik/firmware_build.txt').strip() if os.path.exists(os.path.join(ROOT, 'docs/teknik/firmware_build.txt')) else ''

    sch_sheets = sorted(glob.glob(os.path.join(ROOT, 'hardware', 'schematic', 'ON1-MB_RevA_schematic*.png')))
    sch_sheets = [os.path.relpath(p, ROOT).replace('\\', '/') for p in sch_sheets]
    block = first_existing('hardware/schematic/block_diagram.svg', 'hardware/schematic/block_diagram.png')
    mech = first_existing('hardware/mechanical/ON1_mechanical_drawing.png', 'hardware/mechanical/*.png')

    fw_files = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'firmware', 'OrmanNobetcisi', '*'))):
        n = os.path.basename(p)
        try:
            with open(p, encoding='utf-8', errors='ignore') as f:
                lines = sum(1 for _ in f)
        except Exception:
            lines = 0
        fw_files.append((n, lines))

    S = {k: md_to_html(spec_section(spec, k), shift=1) for k in range(1, 9)}

    sch_pages = ''.join(
        f'<section class="page land"><div class="lhead">Devre şeması · {esc(os.path.basename(p))}</div><img class="sch" src="{rel(p)}" alt="Devre şeması"></section>'
        for p in sch_sheets) or '<section class="page"><div class="missing">Devre şeması PNG bulunamadı.</div></section>'

    diy_pngs = sorted(glob.glob(os.path.join(ROOT, 'hardware', 'pcb_diy', 'png', '*.png')))
    diy_pngs = [os.path.relpath(p, ROOT).replace('\', '/') for p in diy_pngs]
    diy_readme = read('hardware/pcb_diy/README.md') if os.path.exists(os.path.join(ROOT, 'hardware/pcb_diy/README.md')) else ''
    diy_html = ''
    if diy_readme or diy_pngs:
        figs = ''.join(fig(p, 'ON1-DIY · ' + os.path.basename(p), 'mech-fig') for p in diy_pngs)
        diy_html = ('<section class="page"><h2><span>B</span>Ek B — Ev yapımı baskı devre (ON1-DIY)</h2>'
                    + '<div class="small">' + md_to_html(diy_readme, shift=1) + '</div></section>'
                    + '<section class="page"><h2 class="cont">ON1-DIY kart görselleri</h2>' + figs + '</section>')

    fw_table = ''.join(f'<tr><td><code>{esc(n)}</code></td><td>{l}</td></tr>' for n, l in fw_files)

    doc = f'''<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>Orman Nöbetçisi ON-1 — Teknik Tasarım Dokümanı</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,500..800&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="teknik.css">
</head><body>

<section class="page cover">
  <div class="cv-top"><svg width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="19" fill="#1f4d3a"/><path d="M20 7l8 12h-4l6 9H10l6-9h-4z" fill="#f4f1ea"/><circle cx="20" cy="21" r="3" fill="#e4572e"/></svg><span>Orman Nöbetçisi</span></div>
  <div class="cv-mid">
    <div class="eyebrow">Teknik tasarım dokümanı</div>
    <h1>ON-1 Güneş Enerjili<br>Erken Orman Yangını<br>Algılama Düğümü</h1>
    <p class="sub">Donanım, firmware, mekanik, üretim ve saha kurulumu</p>
  </div>
  <img class="cv-img" src="{rel('web/assets/img/on1_exploded.jpg')}" alt="">
  <table class="cv-meta">
    <tr><td>Doküman no</td><td>ON1-TDD-001</td><td>Revizyon</td><td>A</td></tr>
    <tr><td>Tarih</td><td>{today}</td><td>Durum</td><td>Üretime hazır tasarım (pilot öncesi)</td></tr>
    <tr><td>Ana kart</td><td>ON1-MB Rev A</td><td>Firmware</td><td>ON1-FW 1.0.0</td></tr>
  </table>
</section>

<section class="page toc">
  <h2>İçindekiler</h2>
  <ol class="toc-list">
    <li>Ürün özeti ve gereksinimler</li><li>Sistem mimarisi</li><li>Donanım tasarımı</li><li>Pin haritası ve bağlantı listesi</li>
    <li>Güç bütçesi</li><li>Firmware, algılama algoritması ve SMS protokolü</li><li>Mekanik tasarım</li>
    <li>Malzeme listesi (BOM) ve maliyet</li><li>Üretim, test ve kalite</li><li>Saha kurulumu ve bakım</li><li>Uyumluluk, riskler ve yol haritası</li>
    <li>Ek A — Devre şeması</li><li>Ek B — Ev yapımı baskı devre (ON1-DIY)</li>
  </ol>
  <div class="note"><b>Tek doğru kaynak:</b> Bu dokümandaki pin, değer ve davranışlar depo kökündeki <code>SPEC.md</code> dosyasından üretilir. Değişiklikler önce orada yapılır, ardından <code>build.sh</code> ile tüm çıktılar yeniden oluşturulur.</div>
  <h3>Teslimat dosyaları</h3>
  <table class="t">
    <tr><th>Klasör</th><th>İçerik</th></tr>
    <tr><td><code>SPEC.md</code></td><td>Sistem spesifikasyonu (tek doğru kaynak)</td></tr>
    <tr><td><code>hardware/</code></td><td>Devre şeması (SVG/PNG/PDF), blok diyagram, BOM.csv, bağlantı listesi, mekanik çizim, üretici scriptler</td></tr>
    <tr><td><code>firmware/</code></td><td>Arduino kaynak kodu, birim testleri, derleme ve kurulum kılavuzu</td></tr>
    <tr><td><code>web/</code></td><td>Tanıtım sitesi, etkileşimli 3B model (Three.js), render sayfası</td></tr>
    <tr><td><code>renders/</code></td><td>3B ürün görselleri (1600×1200 PNG)</td></tr>
    <tr><td><code>docs/</code></td><td>Broşür ve bu doküman (HTML kaynak + PDF)</td></tr>
  </table>
</section>

<section class="page">
  <h2><span>1</span>Ürün özeti ve gereksinimler</h2>
  {S[1]}
  <h3>Tasarım gereksinimleri</h3>
  <table class="t">
    <tr><th>No</th><th>Gereksinim</th><th>Karşılama</th></tr>
    <tr><td>G-01</td><td>Arduino tabanlı, yerelde programlanabilir</td><td>ATmega328P (Pro Mini 3V3/8 MHz uyumlu), FTDI + ISP başlıkları</td></tr>
    <tr><td>G-02</td><td>Güneş enerjisiyle bakım gerektirmeden çalışma</td><td>3 W panel + MPPT, ≈ 10× enerji marjı, ≥ 60 gün güneşsiz</td></tr>
    <tr><td>G-03</td><td>Teneke gövde, ağaca asılabilir</td><td>Ø153×178 mm teneke, paslanmaz kelepçe ve M6 mapa</td></tr>
    <tr><td>G-04</td><td>Yangında SMS uyarısı</td><td>LTE Cat-1/GSM, 5 numara, konum bağlantısı, ≤ 160 karakter</td></tr>
    <tr><td>G-05</td><td>Yerinde ışıklı alarm</td><td>6 × 1 W kırmızı strob + 105 dB siren</td></tr>
    <tr><td>G-06</td><td>Düşük yanlış alarm</td><td>3 sensör füzyonu + 30 sn doğrulama + hassasiyet ayarı</td></tr>
    <tr><td>G-07</td><td>Sahada uzaktan yönetim</td><td>PIN korumalı SMS komutları, günlük durum raporu</td></tr>
  </table>
</section>

<section class="page">
  <h2><span>2</span>Sistem mimarisi</h2>
  {fig(block, 'Şekil 2.1 — Sistem blok diyagramı', 'wide')}
  {S[2] if not block else ''}
  <h3>Çalışma prensibi</h3>
  <p>Sistem iki enerji alanından oluşur: <b>sürekli alan</b> (ATmega328P, MCP1700 LDO, AMG8833 ve BME680 uyku modunda, modem ağda uyku/DRX modunda) toplam ≈ 2,3 mA çeker; <b>darbe alanı</b> (ölçüm, SMS, alarm) yalnızca gerektiğinde açılır. Mikrodenetleyici watchdog ile 8 saniyede bir uyanır, ölçüm periyodu dolduysa sensörleri okur, skoru hesaplar ve tekrar uyur. Modemden gelen SMS, RI hattındaki darbe ile mikrodenetleyiciyi anında uyandırır; kurcalama ve mıknatıslı test anahtarı da kesme kaynağıdır.</p>
  <p>Batarya rayı (VBAT, 3,0–4,2 V) üç yüke dağılır: 3,3 V LDO (mantık ve sensörler), yüksek taraf P-MOSFET ile anahtarlanan modem rayı ve alarm yükleri (doğrudan VBAT'tan beslenen LED strob, MT3608 ile 12 V'a yükseltilen siren). Bu ayrım modemin 2 A darbe akımının mikrodenetleyici beslemesini çökertmesini önler.</p>
</section>

<section class="page">
  <h2><span>3</span>Donanım tasarımı</h2>
  {S[4]}
  <div class="note"><b>Tasarım notları.</b> (1) A7670E 2 A darbe akımı çeker; modem rayı doğrudan bataryadan, düşük ESR'li 2×470 µF polimer kondansatörle beslenir ve LDO'dan ayrılır. (2) Modem UART'ı 1,8 V'tur; BSS138 çift yönlü seviye çevirici zorunludur. (3) AMG8833 cam ve akrilikten göremez — pencere 0,4 mm HDPE'dir. (4) Li-ion 45 °C üzerinde şarj edilmez; CN3791 TEMP girişi NTC ile bunu donanımsal olarak engeller. (5) Teneke gövde Faraday kafesidir; anten dışarıdadır.</div>
</section>

<section class="page">
  <h2><span>4</span>Pin haritası ve bağlantı listesi</h2>
  {md_to_html(spec_section(spec, 3), shift=1)}
</section>

<section class="page">
  <h2 class="cont">Bağlantı listesi (netlist)</h2>
  <div class="small">{md_to_html(pin_md, shift=2) if pin_md else '<p class="warn">pinout_netlist.md bulunamadı.</p>'}</div>
</section>

<section class="page">
  <h2><span>5</span>Güç bütçesi</h2>
  {S[5]}
  <div class="kpis"><div><b>≈ 2,32 mA</b><span>ortalama akım</span></div><div><b>56 mAh</b><span>günlük tüketim</span></div><div><b>2,25 Wh</b><span>kötümser günlük üretim</span></div><div><b>≈ 15 sa</b><span>sürekli alarm</span></div></div>
</section>

<section class="page">
  <h2><span>6</span>Firmware, algılama algoritması ve SMS protokolü</h2>
  <svg class="sm" viewBox="0 0 760 230" xmlns="http://www.w3.org/2000/svg" font-family="IBM Plex Sans, sans-serif" font-size="13">
    <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#1b1f1d"/></marker></defs>
    <g stroke="#1b1f1d" stroke-width="1.5" fill="none" marker-end="url(#a)">
      <path d="M160 70 H262"/><path d="M370 70 H472"/><path d="M262 92 C220 140 190 140 150 96"/><path d="M560 96 C520 170 160 190 100 96"/><path d="M100 140 V160 H40 V80"/>
    </g>
    <g font-weight="700" text-anchor="middle">
      <rect x="40" y="44" width="120" height="52" rx="10" fill="#dce5da" stroke="#1f4d3a"/><text x="100" y="75">NORMAL</text>
      <rect x="262" y="44" width="108" height="52" rx="10" fill="#fff1d6" stroke="#c98a00"/><text x="316" y="75">SUPHE</text>
      <rect x="472" y="44" width="120" height="52" rx="10" fill="#fde1d8" stroke="#e4572e"/><text x="532" y="75">ALARM</text>
      <rect x="40" y="166" width="140" height="44" rx="10" fill="#eee" stroke="#6b736f"/><text x="110" y="193">DUSUK_PIL / KRITIK</text>
    </g>
    <g font-size="11.5" fill="#3c4440" text-anchor="middle">
      <text x="212" y="62">skor ≥ 2</text><text x="420" y="62">≥3/6 skor≥3</text><text x="205" y="132">doğrulanmadı</text>
      <text x="330" y="190">10 dk skor = 0 → "SONA ERDI" SMS</text><text x="420" y="36">skor ≥ 5 → doğrudan ALARM</text>
    </g>
  </svg>
  {S[6]}
</section>

<section class="page">
  <h2 class="cont">Firmware modülleri</h2>
  <table class="t"><tr><th>Dosya</th><th>Satır</th></tr>{fw_table or '<tr><td colspan=2>firmware klasörü bulunamadı</td></tr>'}</table>
  {('<h3>Derleme sonucu</h3><pre>' + esc(fw_stats) + '</pre>') if fw_stats else ''}
  <div class="small">{md_to_html(fw_readme, shift=2)}</div>
</section>

<section class="page">
  <h2><span>7</span>Mekanik tasarım</h2>
  {S[7]}
  {fig(mech, 'Şekil 7.1 — Ölçülü mekanik çizim ve delik şablonu', 'mech-fig')}
  <div class="row3">{fig('web/assets/img/on1_front.jpg', 'Önden görünüm')}{fig('web/assets/img/on1_side.jpg', 'Yandan görünüm')}{fig('web/assets/img/on1_top.jpg', 'Üstten görünüm')}</div>
</section>

<section class="page land bomland">
  <h2><span>8</span>Malzeme listesi (BOM) ve maliyet</h2>
  <p>Fiyatlar 100 adetlik alım için 2026 tahmini birim fiyatlardır (USD); döviz ve tedarik koşullarına göre güncellenmelidir. Kaynak dosya: <code>hardware/BOM.csv</code>.</p>
  <div class="small">{bom_html}</div>
</section>

<section class="page">
  <h2><span>9</span>Üretim, test ve kalite</h2>
  <h3>Üretim akışı</h3>
  <ol>
    <li>PCB üretimi (2 katman, ENIG) ve SMT montajı; THT konektörler el lehimi.</li>
    <li>Optiboot bootloader yükleme (ISP, sigortalar: Low 0xFF, High 0xDA, Ext 0xFD — BOD 2,7 V).</li>
    <li>Firmware yükleme (FTDI, 57600 bps) ve EEPROM'a cihaz kimliği <code>ON1-XXXX</code> yazımı.</li>
    <li>Konformal kaplama (akrilik), sensör pencereleri, konektörler ve SIM yuvası maskelenir.</li>
    <li>Teneke delme (şablon: Şekil 7.1), boya, conta, rakor, anten bulkhead, ePTFE vent montajı.</li>
    <li>İç şasi (ASA) montajı, batarya + NTC, sensör kartı, silika jel; kapak kapatma.</li>
  </ol>
  <h3>Hat sonu testi (EOL) — her cihaz</h3>
  <table class="t">
    <tr><th>Test</th><th>Yöntem</th><th>Kabul kriteri</th></tr>
    <tr><td>Uyku akımı</td><td>Modem uyku, sensörler uyku, 60 sn ortalama</td><td>≤ 2,8 mA</td></tr>
    <tr><td>Şarj</td><td>Panel simülatörü 6 V / 0,6 A</td><td>CHRG aktif, 450–550 mA</td></tr>
    <tr><td>Batarya ölçümü</td><td>Referans 3,90 V</td><td>±30 mV (kalibrasyon EEPROM'a)</td></tr>
    <tr><td>Termal sensör</td><td>60 °C siyah cisim plakası 1 m'de</td><td>maxT ≥ 45 °C, 64 piksel geçerli</td></tr>
    <tr><td>Gaz sensörü</td><td>İzopropil alkol buharı / tütsü dumanı</td><td>Gaz oranı &lt; 0,65 içinde 30 sn</td></tr>
    <tr><td>Modem</td><td>Test SIM, <code>AT+CSQ</code>, SMS gönderme</td><td>RSSI ≥ −95 dBm, SMS iletildi</td></tr>
    <tr><td>Alarm çıkışları</td><td><code>TEST</code> komutu</td><td>6 LED yanıyor, siren ≥ 100 dB @30 cm</td></tr>
    <tr><td>Kurcalama</td><td>Kapak açma / sarsma</td><td>Kesme ve SMS</td></tr>
    <tr><td>Sızdırmazlık</td><td>IPX4 sprey testi 10 dk (örneklem)</td><td>İçeride su yok</td></tr>
  </table>
  <h3>Tip testleri (pilot öncesi)</h3>
  <ul>
    <li>Isıl döngü −20 / +60 °C, 20 çevrim; güneş altında iç sıcaklık ölçümü (hedef: dış ortam + 10 °C altı).</li>
    <li>Saha yangın testi: kontrollü 0,5 / 1 / 2 m² odaklarla 10–40 m mesafe ve rüzgâr yönü matrisi; algılama süresi ve menzil raporu.</li>
    <li>Yanlış alarm kampanyası: 30 gün, 10 cihaz, güneşli taş/araç/hayvan senaryoları; hedef ≤ 1 yanlış alarm / cihaz / yıl.</li>
    <li>Enerji: 30 gün karanlık kutu testi ile güneşsiz çalışma doğrulaması.</li>
  </ul>
</section>

<section class="page">
  <h2><span>10</span>Saha kurulumu ve bakım</h2>
  <ol>
    <li>Saha keşfi: risk haritası, şebeke kapsaması (sahada <code>AT+CSQ</code> ölçümü), güneş/gölge analizi.</li>
    <li>Yerleşim: riskli hatlar boyunca 50–100 m; termal pencere riskli alana, panel güneye; yükseklik 3–5 m.</li>
    <li>SIM takılır (PIN kapalı), kapak 3 klipsle kilitlenir; kelepçe EPDM pedlerle gerdirilir.</li>
    <li>Etiketteki “N” noktasına mıknatıs 3 sn tutulur → kurulum modu (yeşil LED hızlı).</li>
    <li>SMS: <code>1234 EKLE 1 +90…</code>, <code>1234 KONUM enlem,boylam</code>, <code>1234 AD …</code>, <code>1234 PIN ….</code></li>
    <li><code>1234 TEST</code> ile uçtan uca doğrulama; kurulum formu (ID, konum, fotoğraf, RSSI) doldurulur.</li>
    <li>İlk 30 dk gaz sensörü temiz havada taban değerini öğrenir; bu sürede gaz skoru devre dışıdır.</li>
  </ol>
  <h3>Bakım planı</h3>
  <table class="t">
    <tr><th>Periyot</th><th>İşlem</th></tr>
    <tr><td>Günlük (otomatik)</td><td>Durum SMS'i: pil, güneş, sinyal, risk indeksi; gelmezse saha kontrolü</td></tr>
    <tr><td>Yıllık</td><td>Panel ve HDPE pencere temizliği, kelepçe gevşetme (ağaç büyümesi), silika jel değişimi, <code>TEST</code></td></tr>
    <tr><td>4–5 yıl</td><td>18650 hücre değişimi; EPDM conta kontrolü</td></tr>
    <tr><td>Yangın sonrası</td><td>Gövde, pencere ve kablo kontrolü; <code>KALIBRE</code> komutu ile gaz tabanının yenilenmesi</td></tr>
  </table>
</section>

<section class="page">
  <h2><span>11</span>Uyumluluk, riskler ve yol haritası</h2>
  <h3>Uyumluluk</h3>
  <ul>
    <li><b>CE / RED 2014/53/EU:</b> SIMCom A7670E modül sertifikalı; son ürün için EN 301 489-1/-52 (EMC), EN 62368-1 (güvenlik), EN 62311 (RF maruziyet) testleri gerekir.</li>
    <li><b>RoHS 2011/65/EU</b> ve <b>WEEE</b>: tüm parçalar RoHS uyumlu seçilmiştir; batarya için 2023/1542 Batarya Yönetmeliği etiketlemesi.</li>
    <li><b>Batarya taşıma:</b> UN 38.3 test raporlu hücreler; Li-ion içeren ürün olarak sevkiyat beyanı.</li>
    <li>Türkiye'de M2M hat ve cihaz IMEI kaydı (BTK) operatör üzerinden yapılmalıdır.</li>
  </ul>
  <h3>Riskler ve önlemler</h3>
  <table class="t">
    <tr><th>Risk</th><th>Etki</th><th>Önlem</th></tr>
    <tr><td>Yaz sıcağında iç sıcaklık &gt; 60 °C</td><td>Batarya ömrü, şarj kesintisi</td><td>Panel güneşlik, beyaz boya, köpük; NTC şarj kesme; tip testinde doğrulama</td></tr>
    <tr><td>Güneşte ısınan nesnelerden yanlış alarm</td><td>Güven kaybı</td><td>Çoklu sensör skoru, artış hızı, doğrulama; sahaya göre <code>HASSAS</code></td></tr>
    <tr><td>Şebeke kapsaması zayıf</td><td>SMS gecikmesi</td><td>Dış anten, GSM yedek, keşifte RSSI ölçümü; LoRa seçeneği</td></tr>
    <tr><td>2G şebekesinin kapatılması</td><td>Yedek kaybı</td><td>Birincil LTE Cat-1; 2G yalnızca yedek</td></tr>
    <tr><td>Hırsızlık / vandalizm</td><td>Cihaz kaybı</td><td>Kurcalama SMS'i, yükseklik, paslanmaz kelepçe kilidi</td></tr>
    <tr><td>AMG8833 menzil sınırı</td><td>Uzak odakların kaçması</td><td>Yoğun yerleşim, gaz algılama ile tamamlama; ON-2'de 32×24 MLX90640</td></tr>
  </table>
  <h3>Yol haritası</h3>
  <ul>
    <li><b>ON-1.1:</b> LTE veri ile MQTT/HTTPS bulut paneli, harita üzerinde filo görünümü, OTA yapılandırma.</li>
    <li><b>ON-1-LR:</b> Şebekesiz bölgeler için LoRa 868 MHz mesh + ağ geçidi.</li>
    <li><b>ON-2:</b> MLX90640 32×24 termal, elektrokimyasal CO sensörü, rüzgâr yönü tahmini.</li>
  </ul>
</section>

{sch_pages}

{diy_html}

</body></html>'''
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(doc)
    print('yazıldı:', OUT)


if __name__ == '__main__':
    main()
