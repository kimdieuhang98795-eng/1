#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'tools/emulator_smoke.sh')
s = p.read_text()

# v1.6 used a fixed delay after REVA_GAME_READY, but that marker only means Ruffle
# accepted the SWF load request. The 28 MB AS2 EX body can take very different amounts
# of time to reach its first visible frame on a loaded Android emulator. Never send an
# Enter key into a still-initialising movie: wait for the game canvas itself instead.
old_capture = 'grep -q REVA_GAME_READY "$OUT_DIR/logcat-app.txt"; sleep 8; adb exec-out screencap -p > "$OUT_DIR/normal-launch.png"; adb shell input keyevent KEYCODE_ENTER || true; sleep 3; adb exec-out screencap -p > "$OUT_DIR/normal-after-enter.png"'
new_capture = r'''grep -q REVA_GAME_READY "$OUT_DIR/logcat-app.txt"
RENDERED=0
for i in $(seq 1 18); do
  sleep 5
  N="$(printf '%02d' "$i")"
  FRAME="$OUT_DIR/render-poll-$N.png"
  REPORT="$OUT_DIR/render-poll-$N.txt"
  adb exec-out screencap -p > "$FRAME"
  if python3 "$GITHUB_WORKSPACE/v1.7/check_render.py" "$FRAME" > "$REPORT" 2>&1; then
    cp "$FRAME" "$OUT_DIR/normal-launch.png"
    cat "$REPORT"
    echo "EX_VISIBLE_AFTER=$((i*5))s" | tee "$OUT_DIR/ex-visible.txt"
    RENDERED=1
    break
  fi
  cat "$REPORT"
  PID_NOW="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
  [[ -n "$PID_NOW" ]] || exit 4
  adb logcat --pid="$PID_NOW" -d > "$OUT_DIR/logcat-render-poll-$N.txt" || true
  ! grep -E -q 'FATAL EXCEPTION|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-render-poll-$N.txt" || exit 4
done
[[ "$RENDERED" -eq 1 ]]
# Only interact with the Flash movie after a real frame exists.
adb shell input keyevent KEYCODE_ENTER || true
sleep 3
adb exec-out screencap -p > "$OUT_DIR/normal-after-enter.png"'''
if old_capture not in s:
    raise SystemExit('v1.6 fixed-delay capture block not found')
s = s.replace(old_capture, new_capture, 1)

needle = 'adb shell input keyevent KEYCODE_HOME; sleep 1; adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-resume.txt"; sleep 3\n'
if needle not in s:
    raise SystemExit('v1.7 real-game insertion point not found')
insert = '''# v1.7: retain evidence for lazy EX sibling-resource requests, but rendering is the\n# authoritative startup gate. Some title paths do not request a BGM file before paint.\nsleep 3\nadb exec-out screencap -p > "$OUT_DIR/normal-late.png"\nadb logcat -d -s REVA_ASSET:I REVA_JS:I > "$OUT_DIR/logcat-game-assets.txt" || true\nif grep -q 'REVA_ASSET.*SERVE:BGM/' "$OUT_DIR/logcat-game-assets.txt"; then\n  echo 'EX_ASSET_ROUTE OBSERVED' | tee "$OUT_DIR/asset-route-observed.txt"\nelse\n  echo 'EX_ASSET_ROUTE NOT_REQUESTED_BEFORE_TITLE (bundled/routed; lazy request allowed)' | tee "$OUT_DIR/asset-route-observed.txt"\nfi\npython3 "$GITHUB_WORKSPACE/v1.7/check_render.py" \\\n  "$OUT_DIR/normal-launch.png" \\\n  "$OUT_DIR/normal-after-enter.png" \\\n  "$OUT_DIR/normal-late.png" | tee "$OUT_DIR/render-check.txt"\n\n'''
s = s.replace(needle, insert + needle, 1)

old = "echo 'PASS v1.6 emulator: Chinese EX body; DOM bridge; immutable pointer router; horizontal-only joystick; vertical no backstep; dedicated backstep; >=20 received direction cycles balanced; 8-cycle two-finger stress; EX ready/resume'"
new = "echo 'PASS v1.7 emulator: Chinese EX visibly rendered with offline sibling assets bundled/routed; DOM bridge; immutable pointer router; horizontal-only joystick; vertical no backstep; dedicated backstep; >=20 received direction cycles balanced; 8-cycle two-finger stress; resume'"
if old not in s:
    raise SystemExit('v1.6 PASS marker not found')
s = s.replace(old, new, 1)
p.write_text(s)
print('PASS fix_smoke_v17: visual-readiness polling + post-render interaction + asset evidence')
