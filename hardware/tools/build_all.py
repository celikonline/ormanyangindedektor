# -*- coding: utf-8 -*-
"""Regenerate every hardware deliverable:  python hardware/tools/build_all.py"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
py = sys.executable


def run(*a):
    print(">", " ".join(a))
    subprocess.run([py, *a], cwd=HERE, check=True)


run("gen_schematic.py")
run("gen_docs.py")
run("gen_block_diagram.py")
run("gen_mechanical.py")
sch = os.path.join(HW, "schematic")
mec = os.path.join(HW, "mechanical")
for f in ("ON1-MB_RevA_schematic_sheet1.svg", "ON1-MB_RevA_schematic_sheet2.svg"):
    run("export.py", "png", os.path.join(sch, f), "3500")
run("export.py", "png", os.path.join(sch, "block_diagram.svg"), "2400")
run("export.py", "pdf", os.path.join(sch, "ON1-MB_RevA_schematic.pdf"), "A3L",
    os.path.join(sch, "ON1-MB_RevA_schematic_sheet1.svg"), os.path.join(sch, "ON1-MB_RevA_schematic_sheet2.svg"))
for f in ("ON1_mechanical_drawing.svg", "ON1_drilling_template.svg"):
    run("export.py", "png", os.path.join(mec, f), "3500")
run("export.py", "pdf", os.path.join(mec, "ON1_mechanical.pdf"), "A3L",
    os.path.join(mec, "ON1_mechanical_drawing.svg"), os.path.join(mec, "ON1_drilling_template.svg"))
