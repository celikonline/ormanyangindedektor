# -*- coding: utf-8 -*-
"""
SVG -> PNG / PDF export through headless Chrome (no other tooling needed).
  python export.py png  <file.svg> [width_px]
  python export.py pdf  <out.pdf> <page: A3L|A4L> <file1.svg> [file2.svg ...]
"""
import os, sys, subprocess, tempfile, re, pathlib

CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def _viewbox(svg_path):
    txt = open(svg_path, encoding="utf-8").read(2000)
    m = re.search(r'viewBox="([\d.\- ]+)"', txt)
    x, y, w, h = map(float, m.group(1).split())
    return w, h


def _run(args):
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-first-run", "--no-default-browser-check", "--disable-extensions"] + args,
                       capture_output=True, text=True, timeout=180)
    return r


def png(svg_path, width=3500):
    svg_path = os.path.abspath(svg_path)
    w, h = _viewbox(svg_path)
    height = int(round(width * h / w))
    tmp = tempfile.mkdtemp()
    html = os.path.join(tmp, "page.html")
    uri = pathlib.Path(svg_path).as_uri()
    with open(html, "w", encoding="utf-8") as f:
        f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:#fff}}'
                f'img{{display:block;width:{width}px;height:{height}px}}</style></head>'
                f'<body><img src="{uri}"></body></html>')
    out = os.path.splitext(svg_path)[0] + ".png"
    _run([f"--screenshot={out}", f"--window-size={width},{height}", "--force-device-scale-factor=1",
          "--allow-file-access-from-files", pathlib.Path(html).as_uri()])
    print("png:", out, os.path.exists(out))
    return out


def pdf(out_pdf, page, svgs):
    size = {"A3L": ("420mm", "297mm"), "A4L": ("297mm", "210mm")}[page]
    tmp = tempfile.mkdtemp()
    html = os.path.join(tmp, "doc.html")
    parts = []
    for i, s in enumerate(svgs):
        uri = pathlib.Path(os.path.abspath(s)).as_uri()
        brk = "page-break-after:always;" if i < len(svgs) - 1 else ""
        parts.append(f'<div style="width:{size[0]};height:{size[1]};{brk}overflow:hidden">'
                     f'<img src="{uri}" style="width:{size[0]};height:{size[1]};display:block"></div>')
    with open(html, "w", encoding="utf-8") as f:
        f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>@page{{size:{size[0]} {size[1]};margin:0}}'
                f'html,body{{margin:0;padding:0}}</style></head><body>{"".join(parts)}</body></html>')
    out_pdf = os.path.abspath(out_pdf)
    _run([f"--print-to-pdf={out_pdf}", "--no-pdf-header-footer", "--allow-file-access-from-files",
          pathlib.Path(html).as_uri()])
    print("pdf:", out_pdf, os.path.exists(out_pdf))


if __name__ == "__main__":
    if sys.argv[1] == "png":
        png(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3500)
    else:
        pdf(sys.argv[2], sys.argv[3], sys.argv[4:])
