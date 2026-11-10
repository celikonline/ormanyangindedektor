#!/usr/bin/env bash
# 3B render'ları headless Chrome ile PNG'ye dönüştürür. Önce web sunucusu (port 5077) çalışmalı.
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
OUT="$(cd "$(dirname "$0")" && pwd)/renders"
mkdir -p "$OUT"
for v in ${@:-hero exploded alarm front side top}; do
  "$CHROME" --headless=new --disable-gpu-sandbox --use-angle=swiftshader --enable-unsafe-swiftshader \
    --hide-scrollbars --force-device-scale-factor=1 --window-size=1600,1200 --virtual-time-budget=9000 \
    --screenshot="$(cygpath -w "$OUT/on1_$v.png")" "http://localhost:5077/web/render.html?view=$v" 2>/dev/null
  echo "render: $v -> $OUT/on1_$v.png"
done
