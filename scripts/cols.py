"""Render PDF pages at 300 dpi and cut each into its left/right page halves (scans hold two
book pages side by side, rotated) for transcription.
usage: cols.py PDF OUTDIR FIRST LAST"""
import subprocess, sys, os, glob
from PIL import Image
pdf, out, a, b = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
for n in range(int(a), int(b) + 1):
    subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-r", "300", "-png", pdf, f"{out}/full"], check=True)
    f = glob.glob(f"{out}/full*.png")[0]
    im = Image.open(f); w, h = im.size
    for k, (x0, x1) in {"L": (0, .56), "R": (.42, 1)}.items():
        im.crop((int(x0*w), int(.05*h), int(x1*w), int(.80*h))).save(f"{out}/c{n:03d}{k}.png")
    os.remove(f)
