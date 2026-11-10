#!/usr/bin/env bash
# Orman Nöbetçisi ON-1 — tüm çıktıları yeniden üretir:
#   3B render'lar -> web görselleri -> teknik doküman HTML -> PDF'ler -> web/downloads
# Gereksinim: Google Chrome (headless), Python 3 (+ Pillow, görsel dönüştürme için).
# Kullanım:  ./build.sh            (proje kökünden, Git Bash)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
PY="${PYTHON:-python}"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
PORT=5077
winpath() { if command -v cygpath >/dev/null; then cygpath -w "$1"; else echo "$1"; fi; }

# 1) Yerel sunucu (ES modülleri ve fontlar için)
SERVER_PID=""
if ! curl -s -o /dev/null "http://localhost:$PORT/SPEC.md"; then
  "$PY" -m http.server "$PORT" --directory "$ROOT" >/dev/null 2>&1 &
  SERVER_PID=$!
  sleep 1.5
fi
trap '[ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true' EXIT

# 2) 3B render'lar
./tools_render.sh hero exploded alarm front side top

# 3) Web görselleri
"$PY" - <<'EOF'
import glob, os, shutil
os.makedirs('web/assets/img', exist_ok=True)
try:
    from PIL import Image
    for p in glob.glob('renders/on1_*.png'):
        n = os.path.splitext(os.path.basename(p))[0]
        Image.open(p).convert('RGB').save(f'web/assets/img/{n}.jpg', quality=86, optimize=True, progressive=True)
except ImportError:
    print('UYARI: Pillow yok, JPG dönüşümü atlandı')
for src in ('hardware/schematic/block_diagram.svg',):
    if os.path.exists(src):
        shutil.copy(src, 'web/assets/img/')
EOF

# 4) Teknik doküman HTML
"$PY" docs/teknik/build_teknik.py

# 5) PDF'ler
mkdir -p docs/out
pdf() { "$CHROME" --headless=new --no-pdf-header-footer --virtual-time-budget=10000 \
          --print-to-pdf="$(winpath "$ROOT/docs/out/$2")" "http://localhost:$PORT/$1" 2>/dev/null; echo "pdf: docs/out/$2"; }
pdf docs/brosur/brosur.html Orman_Nobetcisi_ON-1_Brosur.pdf
pdf docs/teknik/teknik.html Orman_Nobetcisi_ON-1_Teknik_Dokuman.pdf

# 6) İndirilebilir dosyalar
"$PY" - <<'EOF'
import os, shutil, zipfile
d = 'web/downloads'; os.makedirs(d, exist_ok=True)
for src in ['docs/out/Orman_Nobetcisi_ON-1_Brosur.pdf', 'docs/out/Orman_Nobetcisi_ON-1_Teknik_Dokuman.pdf',
            'hardware/schematic/ON1-MB_RevA_schematic.pdf', 'hardware/BOM.csv',
            'hardware/mechanical/ON1_mechanical_drawing.png', 'hardware/mechanical/ON1_mechanical.pdf',
            'hardware/pcb_diy/gerber/ON1-DIY_gerber.zip', 'hardware/pcb_diy/ON1-DIY_BOM.csv',
            'hardware/pcb_diy/print/ON1-DIY_bakir_toner_transfer.pdf', 'hardware/pcb_diy/print/ON1-DIY_bakir_fotorezist_film.pdf',
            'hardware/pcb_diy/print/ON1-DIY_bakir_negatif.pdf', 'hardware/pcb_diy/print/ON1-DIY_yerlesim_ust.pdf',
            'hardware/pcb_diy/print/ON1-DIY_delik_haritasi.pdf']:
    if os.path.exists(src):
        shutil.copy(src, d)
    else:
        print('UYARI: eksik', src)
with zipfile.ZipFile(f'{d}/ON1_firmware.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk('firmware'):
        if any(x in base for x in ('build', '.pio', '__pycache__')):
            continue
        for f in files:
            if f.endswith(('.exe', '.o', '.elf', '.hex')) and 'test' in base:
                continue
            p = os.path.join(base, f)
            z.write(p, os.path.relpath(p, '.'))
print('downloads hazır')
EOF
echo "Tamamlandı."
