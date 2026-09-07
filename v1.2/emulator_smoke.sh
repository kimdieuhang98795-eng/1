#!/usr/bin/env bash
set -euo pipefail

APK="${1:-app/build/outputs/apk/debug/app-debug.apk}"
PKG="com.ajiu.reva"
ACTIVITY="$PKG/.MainActivity"
OUT_DIR="${2:-qa/emulator}"
mkdir -p "$OUT_DIR"

if [[ ! -f "$APK" ]]; then echo "APK not found: $APK" >&2; exit 2; fi

adb wait-for-device
adb shell getprop sys.boot_completed | grep -q 1
adb install -r "$APK" | tee "$OUT_DIR/install.txt"
adb logcat -c
adb shell am force-stop "$PKG" || true

# 1) Prove bundled Ruffle JS/WASM can load an actual tiny SWF in Android WebView.
adb shell am start -W -n "$ACTIVITY" --ez qa_ruffle true | tee "$OUT_DIR/am-ruffle.txt"
for i in $(seq 1 25); do
  sleep 1
  adb logcat -d -s REVA_JS:I > "$OUT_DIR/ruffle-logcat.txt" || true
  if grep -q 'RUFFLE_QA_READY' "$OUT_DIR/ruffle-logcat.txt"; then break; fi
done
cat "$OUT_DIR/ruffle-logcat.txt"
if grep -q 'RUFFLE_QA_FAIL' "$OUT_DIR/ruffle-logcat.txt"; then exit 5; fi
grep -q 'RUFFLE_QA_READY' "$OUT_DIR/ruffle-logcat.txt"
adb exec-out screencap -p > "$OUT_DIR/ruffle-ready.png"

# 2) Native touch -> Android KeyEvent -> WebView regression harness.
adb logcat -c
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true | tee "$OUT_DIR/am-input.txt"
sleep 3
PID="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
if [[ -z "$PID" ]]; then
  adb logcat -d > "$OUT_DIR/logcat-all.txt" || true
  echo "App process is not running after input harness launch" >&2; exit 3
fi
printf '%s\n' "$PID" > "$OUT_DIR/pid.txt"
adb exec-out screencap -p > "$OUT_DIR/input-before.png"

adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/layout-logcat.txt" || true
cat "$OUT_DIR/layout-logcat.txt"
get_field(){ grep "$1" "$OUT_DIR/layout-logcat.txt" | tail -1 | sed "s/.*$1//" | awk '{print $1}'; }
XRECT="$(get_field 'XRECT:')"
ARECT="$(get_field 'ARECT:')"
JOY="$(get_field 'JOY:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$JOY" ]] || { echo "Missing native control bounds" >&2; exit 6; }
center_of_rect(){ IFS=',' read -r L T R B <<< "$1"; echo "$(( (L+R)/2 )) $(( (T+B)/2 ))"; }
read X_X X_Y < <(center_of_rect "$XRECT")
read A_X A_Y < <(center_of_rect "$ARECT")
IFS=',' read -r J_X J_Y J_R <<< "$JOY"
printf 'x=%s,%s a=%s,%s joy=%s,%s r=%s\n' "$X_X" "$X_Y" "$A_X" "$A_Y" "$J_X" "$J_Y" "$J_R" | tee "$OUT_DIR/touch-points.txt"

# X hold: one physical tap == exactly one down/up pair.
adb logcat -c
adb shell input touchscreen tap "$X_X" "$X_Y"
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/x-input-logcat.txt" || true
cat "$OUT_DIR/x-input-logcat.txt"
grep -q 'PRESS:X' "$OUT_DIR/x-input-logcat.txt"
grep -q 'RELEASE:X' "$OUT_DIR/x-input-logcat.txt"
grep -q 'KEYDOWN:X:' "$OUT_DIR/x-input-logcat.txt"
grep -q 'KEYUP:X:' "$OUT_DIR/x-input-logcat.txt"
[[ "$(grep -c 'KEYDOWN:X:' "$OUT_DIR/x-input-logcat.txt")" -eq 1 ]]
[[ "$(grep -c 'KEYUP:X:' "$OUT_DIR/x-input-logcat.txt")" -eq 1 ]]

# A pulse: Cross-Slash-style regression, one touch == one cast pulse.
adb logcat -c
adb shell input touchscreen tap "$A_X" "$A_Y"
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/a-input-logcat.txt" || true
cat "$OUT_DIR/a-input-logcat.txt"
grep -q 'PULSE:A' "$OUT_DIR/a-input-logcat.txt"
grep -q 'KEYDOWN:A:' "$OUT_DIR/a-input-logcat.txt"
grep -q 'KEYUP:A:' "$OUT_DIR/a-input-logcat.txt"
[[ "$(grep -c 'KEYDOWN:A:' "$OUT_DIR/a-input-logcat.txt")" -eq 1 ]]
[[ "$(grep -c 'KEYUP:A:' "$OUT_DIR/a-input-logcat.txt")" -eq 1 ]]

# Joystick right must always finish with ArrowRight key-up (ghost-walk regression).
END_X=$(( J_X + J_R * 2 / 3 ))
adb logcat -c
adb shell input touchscreen swipe "$J_X" "$J_Y" "$END_X" "$J_Y" 500
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/joy-input-logcat.txt" || true
cat "$OUT_DIR/joy-input-logcat.txt"
grep -q 'KEYDOWN:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt"
grep -q 'KEYUP:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt"
[[ "$(grep -c 'KEYDOWN:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt")" -eq 1 ]]
[[ "$(grep -c 'KEYUP:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt")" -eq 1 ]]
adb exec-out screencap -p > "$OUT_DIR/input-after.png"

# 3) Real bundled Final SWF: wait until player.load(game.swf) resolves, not merely process survival.
adb logcat -c
adb shell am force-stop "$PKG"
adb shell am start -W -n "$ACTIVITY" | tee "$OUT_DIR/am-normal.txt"
for i in $(seq 1 60); do
  sleep 1
  PID="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
  [[ -n "$PID" ]] || { echo 'App died during real Final load' >&2; exit 4; }
  adb logcat --pid="$PID" -d > "$OUT_DIR/logcat-app.txt" || true
  if grep -q 'REVA_GAME_READY' "$OUT_DIR/logcat-app.txt"; then break; fi
  if grep -E -q 'FATAL EXCEPTION|Process: com\.ajiu\.reva.*has died|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-app.txt"; then
    tail -200 "$OUT_DIR/logcat-app.txt" >&2; exit 4
  fi
done
grep -q 'REVA_GAME_READY' "$OUT_DIR/logcat-app.txt"
adb exec-out screencap -p > "$OUT_DIR/normal-launch.png"

# 4) Background/resume after the real game has loaded.
adb shell input keyevent KEYCODE_HOME
sleep 1
adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-resume.txt"
sleep 3
PID2="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
[[ -n "$PID2" ]]
adb exec-out screencap -p > "$OUT_DIR/resume.png"
adb logcat --pid="$PID2" -d > "$OUT_DIR/logcat-resume.txt" || true
if grep -E -q 'FATAL EXCEPTION|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-resume.txt"; then exit 7; fi

echo "PASS emulator smoke: Ruffle QA; X once; A pulse once; joystick releases; bundled Final reached REVA_GAME_READY; background/resume survived; pid=$PID2"
