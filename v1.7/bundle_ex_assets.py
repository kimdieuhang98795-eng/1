#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, urllib.request, zlib, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
assets = root / 'app/src/main/assets'
(assets / 'BGM').mkdir(parents=True, exist_ok=True)

base = 'https://www.mhhf.com/files/game/4711/'
referer = 'https://www.mhhf.com/game/play/4711?format=11'
ua = 'Mozilla/5.0'

def get(rel: str) -> bytes:
    req = urllib.request.Request(base + rel, headers={'User-Agent': ua, 'Referer': referer})
    with urllib.request.urlopen(req, timeout=120) as r:
        b = r.read()
        ctype = r.headers.get('content-type', '')
    if len(b) < 256 or b[:1] == b'<' or 'text/html' in ctype.lower():
        raise RuntimeError(f'{rel}: suspicious response size/type {len(b)} {ctype!r}')
    return b

# Main 3.0 EX Chinese SWF: pinned to the body already validated in v1.6.
swf = get('lbmxex.swf')
expected_size = 17628685
expected_sha = '0c7904469438078919c705dc7d0da11a9e0595fce29decd68f84599b25d3f457'
sha = hashlib.sha256(swf).hexdigest()
assert len(swf) == expected_size, (len(swf), expected_size)
assert swf[:3] == b'CWS', swf[:3]
assert int.from_bytes(swf[4:8], 'little') == 28435282
assert sha == expected_sha, (sha, expected_sha)
raw = b'FWS' + swf[3:8] + zlib.decompress(swf[8:])
text = raw.decode('utf-8', 'ignore')
cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
assert cjk > 1000 and '雷巴' in text and '晓之车' in text
(assets / 'game.swf').write_bytes(swf)

rels = [
    'BGM/BG.jpg',
    'BGM/1602.mp3', 'BGM/7130.mp3', 'BGM/7599.mp3', 'BGM/7810.mp3',
    'BGM/8156.mp3', 'BGM/gate.mp3', 'BGM/8678.mp3', 'BGM/9041.mp3',
    'BGM/9285.mp3', 'BGM/9638.mp3', 'BGM/9411.mp3', 'BGM/9413.mp3', 'BGM/9599.mp3',
]

manifest = [
    f'SOURCE={base}lbmxex.swf',
    'EDITION=3.0 EX 汉化版',
    f'SWF_SIZE={len(swf)}',
    'SWF_DECLARED=28435282',
    f'SWF_SHA256={sha}',
    f'CJK_COUNT={cjk}',
]

for rel in rels:
    b = get(rel)
    # Prevent accidentally bundling an error page or tiny placeholder.
    if rel.lower().endswith('.jpg'):
        assert len(b) > 1024, (rel, len(b))
        assert b.startswith(b'\xff\xd8') or b.startswith(b'\x89PNG'), (rel, b[:8])
    else:
        assert len(b) > 2048, (rel, len(b))
    out = assets / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b)
    manifest.append(f'{rel}\tSIZE={len(b)}\tSHA256={hashlib.sha256(b).hexdigest()}')
    print(f'BUNDLED {rel}: {len(b)} bytes')

(root / 'bundled-game.txt').write_text('\n'.join(manifest) + '\n')
print(root.joinpath('bundled-game.txt').read_text())
print('PASS bundle_ex_assets: main SWF + 14 external EX resources pinned into APK assets')
