#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'tools/emulator_smoke.sh')
s = p.read_text()

needle = 'adb shell input keyevent KEYCODE_HOME; sleep 1; adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-resume.txt"; sleep 3\n'
if needle not in s:
    raise SystemExit('v1.7 real-game insertion point not found')
insert = '''# v1.7: READY is not enough. 3.0 EX performs root-frame external loads.\n# Give the game time to paint, retain full app logs, prove at least one EX sibling\n# resource was served from APK assets, and independently require a visible game frame.\nsleep 8\nadb exec-out screencap -p > "$OUT_DIR/normal-late.png"\nadb logcat --pid="$PID" -d > "$OUT_DIR/logcat-game-assets.txt" || true\ngrep -q 'REVA_ASSET.*SERVE:BGM/' "$OUT_DIR/logcat-game-assets.txt"\npython3 "$GITHUB_WORKSPACE/v1.7/check_render.py" \\\n  "$OUT_DIR/normal-launch.png" \\\n  "$OUT_DIR/normal-after-enter.png" \\\n  "$OUT_DIR/normal-late.png" | tee "$OUT_DIR/render-check.txt"\n\n'''
s = s.replace(needle, insert + needle, 1)

old = "echo 'PASS v1.6 emulator: Chinese EX body; DOM bridge; immutable pointer router; horizontal-only joystick; vertical no backstep; dedicated backstep; >=20 received direction cycles balanced; 8-cycle two-finger stress; EX ready/resume'"
new = "echo 'PASS v1.7 emulator: Chinese EX + offline external assets visibly rendered; DOM bridge; immutable pointer router; horizontal-only joystick; vertical no backstep; dedicated backstep; >=20 received direction cycles balanced; 8-cycle two-finger stress; resume'"
if old not in s:
    raise SystemExit('v1.6 PASS marker not found')
s = s.replace(old, new, 1)
p.write_text(s)
print('PASS fix_smoke_v17: generic EX asset-serve assertion + visible-render gate')
