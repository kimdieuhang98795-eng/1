#!/usr/bin/env python3
from pathlib import Path
import struct
import sys
import zlib


def paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png_rgb(path):
    """Decode the non-interlaced 8-bit RGB/RGBA PNG emitted by adb screencap.

    Keep this QA helper stdlib-only so GitHub runner image changes cannot make
    render verification fail merely because Pillow is absent.
    """
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'{path}: not a PNG')

    pos = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    while pos + 12 <= len(data):
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IHDR':
            width, height, bit_depth, color_type, _comp, _flt, interlace = struct.unpack('>IIBBBBB', payload)
        elif kind == b'IDAT':
            idat.extend(payload)
        elif kind == b'IEND':
            break

    if width is None or not idat:
        raise ValueError(f'{path}: missing IHDR/IDAT')
    if bit_depth != 8 or color_type not in (2, 6) or interlace != 0:
        raise ValueError(
            f'{path}: unsupported PNG bit_depth={bit_depth} color_type={color_type} interlace={interlace}'
        )

    bpp = 3 if color_type == 2 else 4
    stride = width * bpp
    raw = zlib.decompress(bytes(idat))
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise ValueError(f'{path}: unexpected decompressed size {len(raw)} != {expected}')

    rows = []
    prev = bytearray(stride)
    off = 0
    for _y in range(height):
        filt = raw[off]
        src = raw[off + 1:off + 1 + stride]
        off += stride + 1
        recon = bytearray(stride)
        for i, value in enumerate(src):
            left = recon[i - bpp] if i >= bpp else 0
            up = prev[i]
            upper_left = prev[i - bpp] if i >= bpp else 0
            if filt == 0:
                out = value
            elif filt == 1:
                out = value + left
            elif filt == 2:
                out = value + up
            elif filt == 3:
                out = value + ((left + up) // 2)
            elif filt == 4:
                out = value + paeth(left, up, upper_left)
            else:
                raise ValueError(f'{path}: unsupported PNG filter {filt}')
            recon[i] = out & 0xff
        rows.append(recon)
        prev = recon
    return width, height, bpp, rows


def inspect_game_crop(path):
    w, h, bpp, rows = read_png_rgb(path)
    x0, y0 = int(w * 0.27), int(h * 0.08)
    x1, y1 = int(w * 0.58), int(h * 0.65)

    total = nonblack = colored = rgb_sum = 0
    for y in range(y0, y1):
        row = rows[y]
        for x in range(x0, x1):
            i = x * bpp
            r, g, b = row[i], row[i + 1], row[i + 2]
            hi, lo = max(r, g, b), min(r, g, b)
            total += 1
            rgb_sum += r + g + b
            if hi >= 24:
                nonblack += 1
            if hi - lo >= 10 and hi >= 24:
                colored += 1

    ratio = nonblack / max(1, total)
    cratio = colored / max(1, total)
    mean = rgb_sum / max(1, total * 3)
    return w, h, ratio, cratio, mean


paths = [Path(p) for p in sys.argv[1:]]
if not paths:
    raise SystemExit('usage: check_render.py screenshot...')

ok = False
for p in paths:
    w, h, ratio, cratio, mean = inspect_game_crop(p)
    print(f'{p.name}: size={w}x{h} nonblack={ratio:.5f} colored={cratio:.5f} mean={mean:.2f}')
    # Measured v1.7 evidence: the initial black frame is 0.000/0.000/0.00 here,
    # while the actual Chinese EX title frame is ~0.805/~0.441/~72.7.
    if ratio >= 0.05 and (cratio >= 0.005 or mean >= 5.0):
        ok = True

if not ok:
    raise SystemExit('FAIL: central EX game canvas remained effectively black in every capture')
print('PASS: visible non-black EX game render detected in game-only crop')
