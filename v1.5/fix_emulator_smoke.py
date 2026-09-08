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
    "logs(){ adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I REVA_DOMKEY:I REVA_TRACE:I REVA_STRESS:I REVA_NAV:W > \"$1\" || true; }"
)
# Require both logical and backend evidence for the held X test.
needle="grep -q 'DOM_DOWN:KeyX:x' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'DOM_UP:KeyX:x' \"$OUT_DIR/x-hold-logcat.txt\"\n"
insert=needle + "grep -q 'REVA_TRACE.*LOGICAL:DOWN:X' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'REVA_TRACE.*LOGICAL:UP:X' \"$OUT_DIR/x-hold-logcat.txt\"\n" + "grep -q 'REVA_TRACE.*BACKEND:DOM:DOWN:KeyX' \"$OUT_DIR/x-hold-logcat.txt\"; grep -q 'REVA_TRACE.*BACKEND:DOM:UP:KeyX' \"$OUT_DIR/x-hold-logcat.txt\"\n"
if needle not in s:
    raise SystemExit('x-hold insertion point missing')
s=s.replace(needle,insert,1)

# Add a true in-app two-pointer stress test after the adb single-pointer balance test.
marker="""! grep -q 'REVA_DOMKEY: DOWN:ArrowDown' \"$OUT_DIR/cycle-balance.txt\"\n\n# 4) Bundled Final loads through Ruffle and survives background/resume.\n"""
stress=r'''! grep -q 'REVA_DOMKEY: DOWN:ArrowDown' "$OUT_DIR/cycle-balance.txt"

# MULTI_POINTER_STRESS: eight in-app gestures hold joystick + X simultaneously,
# reverse direction while X is held, then tap A without ever changing pointer ownership.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_stress true > "$OUT_DIR/am-stress.txt"
for i in $(seq 1 20); do
  sleep 1
  logs "$OUT_DIR/multi-stress.txt"
  grep -q 'STRESS_DONE:cycles=8' "$OUT_DIR/multi-stress.txt" && break
done
cat "$OUT_DIR/multi-stress.txt"
grep -q 'STRESS_DONE:cycles=8' "$OUT_DIR/multi-stress.txt"
grep -q 'PASS_SEQUENCE_DONE:8' "$OUT_DIR/multi-stress.txt"
grep -q 'POINTER:ROLE:pid=0:1' "$OUT_DIR/multi-stress.txt"
grep -q 'POINTER:ROLE:pid=1:2' "$OUT_DIR/multi-stress.txt"
! grep -q 'REVA_DOMKEY: DOWN:ArrowDown' "$OUT_DIR/multi-stress.txt"
! grep -E -q 'REVA_DOMKEY: DOWN:Key(C|Z|V|S|D|F|G|H|Q|W|E|R|T|Y)' "$OUT_DIR/multi-stress.txt"
SLD="$(grep -c 'REVA_DOMKEY: DOWN:ArrowLeft' "$OUT_DIR/multi-stress.txt" || true)"; SLU="$(grep -c 'REVA_DOMKEY: UP:ArrowLeft' "$OUT_DIR/multi-stress.txt" || true)"
SRD="$(grep -c 'REVA_DOMKEY: DOWN:ArrowRight' "$OUT_DIR/multi-stress.txt" || true)"; SRU="$(grep -c 'REVA_DOMKEY: UP:ArrowRight' "$OUT_DIR/multi-stress.txt" || true)"
SXD="$(grep -c 'REVA_DOMKEY: DOWN:KeyX' "$OUT_DIR/multi-stress.txt" || true)"; SXU="$(grep -c 'REVA_DOMKEY: UP:KeyX' "$OUT_DIR/multi-stress.txt" || true)"
SAD="$(grep -c 'REVA_DOMKEY: DOWN:KeyA' "$OUT_DIR/multi-stress.txt" || true)"; SAU="$(grep -c 'REVA_DOMKEY: UP:KeyA' "$OUT_DIR/multi-stress.txt" || true)"
echo "MULTI_POINTER_STRESS L=$SLD/$SLU R=$SRD/$SRU X=$SXD/$SXU A=$SAD/$SAU" | tee -a "$OUT_DIR/multi-stress.txt"
[[ "$SLD" -eq 8 && "$SLU" -eq 8 && "$SRD" -eq 8 && "$SRU" -eq 8 ]]
[[ "$SXD" -eq 8 && "$SXU" -eq 8 && "$SAD" -eq 8 && "$SAU" -eq 8 ]]
echo 'MULTI_POINTER_STRESS PASS' | tee -a "$OUT_DIR/multi-stress.txt"

# 4) Bundled Final loads through Ruffle and survives background/resume.
'''
if marker not in s:
    raise SystemExit('cycle-balance insertion point missing')
s=s.replace(marker,stress,1)

# Upgrade final summary so a green run explicitly certifies the multi-finger path.
s=s.replace(
    "PASS v1.5 emulator: DOM bridge; horizontal-only joystick; vertical no backstep; dedicated backstep; balanced 20 direction gestures; Final ready/resume",
    "PASS v1.5 emulator: DOM bridge; immutable pointer router; horizontal-only joystick; vertical no backstep; dedicated backstep; balanced 20 direction gestures; 8-cycle two-finger stress; Final ready/resume"
)
p.write_text(s)
print('PASS fix_emulator_smoke: exact backend regex + REVA_TRACE + two-pointer stress evidence')
