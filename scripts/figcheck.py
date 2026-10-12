"""Render the figure crops declared in a transcript for visual checking.
usage: figcheck.py TRANSCRIPT OUTDIR [QNO ...]"""
import os, re, subprocess, sys, tempfile
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
only = set(sys.argv[3:])
pdf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(src)))),
                   os.path.basename(os.path.dirname(src)), os.path.basename(src)[:-4] + ".pdf")
os.makedirs(out, exist_ok=True)
for m in re.finditer(r"^## (\d+) \|.*?fig=([^|]+)", open(src).read(), re.M):
    q, specs = m.group(1), m.group(2).strip()
    if only and q not in only:
        continue
    parts = []
    for spec in specs.split(";"):
        page, box = spec.strip().split(":")
        x0, y0, x1, y1 = map(float, box.split(","))
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["pdftoppm", "-f", page, "-l", page, "-r", "100", "-png", pdf, f"{d}/p"], check=True)
            im = Image.open(os.path.join(d, os.listdir(d)[0])); w, h = im.size
            parts.append(im.crop((int(x0*w), int(y0*h), int(x1*w), int(y1*h))))
    img = Image.new("RGB", (max(p.width for p in parts), sum(p.height for p in parts)), "white")
    y = 0
    for p in parts:
        img.paste(p, (0, y)); y += p.height
    img.save(f"{out}/q{q}.png")
