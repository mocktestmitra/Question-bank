"""Render the figure crops declared in a transcript for visual checking.
usage: figcheck.py TRANSCRIPT OUTDIR"""
import os, re, subprocess, sys, tempfile
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
pdf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(src)))),
                   os.path.basename(os.path.dirname(src)), os.path.basename(src)[:-4] + ".pdf")
os.makedirs(out, exist_ok=True)
for m in re.finditer(r"^## (\d+) \|.*fig=(\d+):([\d.,]+)", open(src).read(), re.M):
    q, page, box = m.groups()
    x0, y0, x1, y1 = map(float, box.split(","))
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-f", page, "-l", page, "-r", "100", "-png", pdf, f"{d}/p"], check=True)
        im = Image.open(os.path.join(d, os.listdir(d)[0])); w, h = im.size
        im.crop((int(x0*w), int(y0*h), int(x1*w), int(y1*h))).save(f"{out}/q{q}.png")
    print(q)
