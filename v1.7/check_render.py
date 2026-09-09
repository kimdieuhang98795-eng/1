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
    # Inspect only the central-left game canvas. This excludes the menu dots, joystick,
    # and right-side skill buttons, so a black SWF with a healthy Android overlay cannot pass.
    crop = im.crop((int(w*0.27), int(h*0.08), int(w*0.58), int(h*0.65)))
    px = list(crop.getdata())
    nonblack = sum(1 for r,g,b in px if max(r,g,b) >= 24)
    colored = sum(1 for r,g,b in px if max(r,g,b)-min(r,g,b) >= 10 and max(r,g,b) >= 24)
    ratio = nonblack / max(1, len(px))
    cratio = colored / max(1, len(px))
    stat = ImageStat.Stat(crop)
    mean = sum(stat.mean)/3.0
    print(f'{p.name}: size={w}x{h} nonblack={ratio:.5f} colored={cratio:.5f} mean={mean:.2f}')
    # Measured v1.7 evidence: the initial black frame is 0.000/0.000/0.00 here,
    # while the actual Chinese EX title frame is ~0.805/~0.441/~72.7.
    if ratio >= 0.05 and (cratio >= 0.005 or mean >= 5.0):
        ok = True

if not ok:
    raise SystemExit('FAIL: central EX game canvas remained effectively black in every capture')
print('PASS: visible non-black EX game render detected in game-only crop')
