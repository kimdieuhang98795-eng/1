#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'tools/check_project.py')
s = p.read_text()
old = """    for k in ['ControlLayoutConfig.modern()','LAYOUT:MODERN_V18']:\n        assert k in s,k\n"""
new = """    assert 'ControlLayoutConfig.modern()' in s\n    # v1.8 introduced the data-driven layout; later HUD-only revisions keep the\n    # same layout architecture while advancing the runtime marker.\n    assert ('LAYOUT:MODERN_V18' in s or 'LAYOUT:MODERN_V19' in s), 'modern layout marker'\n"""
if old not in s:
    raise SystemExit('v1.9 QA migration: expected v1.8 layout assertion not found')
s = s.replace(old, new, 1)
p.write_text(s)
print('PASS fix_check_project_v19: modern layout QA accepts v1.8/v1.9 markers')
