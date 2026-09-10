#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, shutil, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
export=Path(sys.argv[2] if len(sys.argv)>2 else '/tmp/skill-export')
manifest=json.loads(Path(__file__).with_name('skill_manifest.json').read_text())
out=root/'app/src/main/assets/skill_icons'
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)

rows=[]
expected_visuals=0
for profile,pdata in manifest['profiles'].items():
    for key,entry in pdata['skills'].items():
        visual=entry['visual']
        if visual=='transparent-original':
            rows.append((profile,key,'transparent-original','',''))
            continue
        expected_visuals += 1
        typ=visual['type']; sid=int(visual['id'])
        if typ=='sprite':
            frame=int(visual.get('frame',1))
            src=export/'sprite'/f'DefineSprite_{sid}'/f'{frame}.png'
        elif typ=='shape':
            src=export/'shape'/f'{sid}.png'
        else:
            raise SystemExit(f'unsupported visual type {typ}: {profile}/{key}')
        if not src.is_file():
            raise SystemExit(f'missing proven original visual {profile}/{key}: {src}')
        data=src.read_bytes()
        if len(data)<60 or data[:8] != b'\x89PNG\r\n\x1a\n':
            raise SystemExit(f'invalid PNG for {profile}/{key}: {src}')
        dst=out/profile/f'{key.upper()}.png'
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        sha=hashlib.sha256(data).hexdigest()
        rows.append((profile,key,f'{typ}:{sid}',str(dst.relative_to(root)),sha))

real=[r for r in rows if r[2] != 'transparent-original']
if len(real)!=expected_visuals or expected_visuals<35:
    raise SystemExit(f'visual count mismatch: real={len(real)} expected={expected_visuals}')

index=root/'skill_asset_index.txt'
with index.open('w',encoding='utf-8') as f:
    f.write('profile\tkey\tsource\tasset\tsha256\n')
    for r in rows: f.write('\t'.join(r)+'\n')

# The renderer intentionally references only paths produced from this manifest.
for p in out.rglob('*.png'):
    if p.stat().st_size<=60: raise SystemExit(f'too-small skill asset: {p}')

print(f'PASS v1.11 skill assets: {len(real)} original PNG visuals + {len(rows)-len(real)} proven transparent states')
print(index.read_text())
