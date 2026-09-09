#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageStat
import sys

paths = [Path(p) for p in sys.argv[1:]]
if not paths:
    raise SystemExit('usage: check_render.py screenshot...')

ok = False
for p in paths:
    im = Image.open(p).convert('RGB')
    w, h = im.size
    # Deliberately avoid the left menu dots and most touch-control overlay.
    crop = im.crop((int(w*0.22), int(h*0.08), int(w*0.78), int(h*0.68)))
    px = list(crop.getdata())
    nonblack = sum(1 for r,g,b in px if max(r,g,b) >= 24)
    colored = sum(1 for r,g,b in px if max(r,g,b)-min(r,g,b) >= 10 and max(r,g,b) >= 24)
    ratio = nonblack / max(1, len(px))
    cratio = colored / max(1, len(px))
    stat = ImageStat.Stat(crop)
    mean = sum(stat.mean)/3.0
    print(f'{p.name}: size={w}x{h} nonblack={ratio:.5f} colored={cratio:.5f} mean={mean:.2f}')
    # v1.6's failed frame is exactly black in this crop. A real title/menu frame is far above these thresholds.
    if ratio >= 0.008 and (cratio >= 0.001 or mean >= 5.0):
        ok = True

if not ok:
    raise SystemExit('FAIL: EX game region remained effectively black in every capture')
print('PASS: visible non-black EX game render detected')
