"""Crop a zoomed region of a PDF page for close reading.
usage: zoom.py PDF PAGE X0 Y0 X1 Y1 OUT   (fractions of page, 0-1)"""
import subprocess, sys, tempfile, os
from PIL import Image
pdf, page, x0, y0, x1, y1, out = sys.argv[1], int(sys.argv[2]), *map(float, sys.argv[3:7]), sys.argv[7]
with tempfile.TemporaryDirectory() as d:
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "300", "-png", pdf, f"{d}/p"], check=True)
    im = Image.open(os.path.join(d, os.listdir(d)[0]))
    w, h = im.size
    im.crop((int(x0*w), int(y0*h), int(x1*w), int(y1*h))).save(out)
