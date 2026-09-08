#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/emulator_smoke.sh')
s=p.read_text()
# The old regex also matched the JS console marker REVA_DOMKEY_EVENT, doubling counts.
s=s.replace("REVA_DOMKEY.*DOWN:", "REVA_DOMKEY: DOWN:")
s=s.replace("REVA_DOMKEY.*UP:", "REVA_DOMKEY: UP:")
# Persist v1.5 black-box trace alongside the traditional logs.
s=s.replace(
    "logs(){ adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I REVA_DOMKEY:I REVA_NAV:W > \"$1\" || true; }",
    "logs(){ adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I REVA_DOMKEY:I REVA_TRACE:I REVA_NAV:W > \"$1\" || true; }"
)
# Require both logical and backend evidence for the held X test.
needle="grep -q 'DOM_DOWN:KeyX:x' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'DOM_UP:KeyX:x' \"$OUT_DIR/x-hold-logcat.txt\"\n"
insert=needle + "grep -q 'REVA_TRACE.*LOGICAL:DOWN:X' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'REVA_TRACE.*LOGICAL:UP:X' \"$OUT_DIR/x-hold-logcat.txt\"\n" + "grep -q 'REVA_TRACE.*BACKEND:DOM:DOWN:KeyX' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'REVA_TRACE.*BACKEND:DOM:UP:KeyX' \"$OUT_DIR/x-hold-logcat.txt\"\n"
if needle not in s:
    raise SystemExit('x-hold insertion point missing')
s=s.replace(needle,insert,1)
p.write_text(s)
print('PASS fix_emulator_smoke: exact backend regex + REVA_TRACE evidence')
