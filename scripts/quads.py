"""Render PDF pages at 300 dpi and cut each into 4 overlapping quadrants for transcription.
usage: quads.py PDF OUTDIR [FIRST LAST]"""
import subprocess, sys, os, glob
from PIL import Image
pdf, out = sys.argv[1], sys.argv[2]
rng = ["-f", sys.argv[3], "-l", sys.argv[4]] if len(sys.argv) > 4 else []
os.makedirs(out, exist_ok=True)
subprocess.run(["pdftoppm", *rng, "-r", "300", "-png", pdf, f"{out}/full"], check=True)
for f in sorted(glob.glob(f"{out}/full-*.png")):
    n = int(f.rsplit("-", 1)[1].split(".")[0])
    im = Image.open(f); w, h = im.size
    boxes = {"1L": (0, 0, .6, .55), "2L": (0, .45, .6, 1), "3R": (.4, 0, 1, .55), "4R": (.4, .45, 1, 1)}
    for k, (x0, y0, x1, y1) in boxes.items():
        im.crop((int(x0*w), int(y0*h), int(x1*w), int(y1*h))).save(f"{out}/p{n:03d}_{k}.png")
    os.remove(f)
