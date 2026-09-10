#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/check_project.py')
s=p.read_text()

# v1.11 keeps the exact v1.10 control semantics/geometry but formats the
# data-driven ControlLayoutConfig more compactly. The inherited v1.5 checker
# accidentally treated spaces after commas as part of the contract. Normalize
# whitespace for config assertions while preserving every semantic value.
needle="config=config_path.read_text() if config_path.exists() else ''\nmodern_layout=bool(config)\n"
replace="config=config_path.read_text() if config_path.exists() else ''\nconfig_compact=''.join(config.split())\nmodern_layout=bool(config)\n"
if needle not in s:
    raise SystemExit('v1.11 QA missing config initialization anchor')
s=s.replace(needle,replace,1)

repls={
    "assert 'ButtonSpec.circle(\"↓\", \"后跳\", PULSE' in config":
        "assert 'ButtonSpec.circle(\"↓\",\"后跳\",PULSE' in config_compact",
    "for k in ['0f, 340f, 390f, 720f','92f, 390f, 335f, 625f']:\n        assert k in config,k":
        "for k in ['0f,340f,390f,720f','92f,390f,335f,625f']:\n        assert k in config_compact,k",
    "for k in ['coreButtons','skillSlots','pageButton','itemButtons','utilityButtons','ButtonSpec.circle(\"X\", \"普攻\"']:\n        assert k in config,k":
        "for k in ['coreButtons','skillSlots','pageButton','itemButtons','utilityButtons']:\n        assert k in config,k\n    assert 'ButtonSpec.circle(\"X\",\"普攻\",HOLD,\"attack\",0,1190,610,66)' in config_compact",
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit('v1.11 QA missing fragile assertion: '+old[:120])
    s=s.replace(old,new,1)

# Keep v1.11's new selector and all four EX controls explicitly covered here,
# so making the legacy checks whitespace-independent cannot weaken layout QA.
anchor="    assert 'addCircle(\"X\",\"攻\"' not in s\n"
extra="""    assert 'ButtonSpec.pill(\"PROFILE\",\"弹药\",PAGE,\"profile\",8,585,615,690,650)' in config_compact
    for k in [
        'ButtonSpec.pill(\"CTRL\",\"EXⅠ\",HOLD,\"utility\",7,714,592,786,638)',
        'ButtonSpec.pill(\"SHIFT\",\"EXⅡ\",HOLD,\"utility\",7,795,592,867,638)',
        'ButtonSpec.pill(\"SPACE\",\"EXⅢ\",HOLD,\"utility\",7,714,650,786,700)',
        'ButtonSpec.pill(\"B\",\"EXⅣ\",HOLD,\"utility\",7,795,650,867,700)'
    ]:
        assert k in config_compact,k
"""
if anchor not in s:
    raise SystemExit('v1.11 QA missing layout guard insertion anchor')
s=s.replace(anchor,extra+anchor,1)

for token in ['config_compact','ButtonSpec.circle("↓","后跳",PULSE','ButtonSpec.pill("PROFILE"','ButtonSpec.pill("CTRL"']:
    if token not in s:
        raise SystemExit('v1.11 QA normalization incomplete: '+token)

p.write_text(s)
print('PASS fix_check_v111: whitespace-robust semantic layout QA + exact v1.11 profile/EX geometry guards')
