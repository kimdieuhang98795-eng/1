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

# 1) Ruffle smoke.
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

# 2) The exact Naver blog navigation seen in the bug report must be blocked.
adb logcat -c
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_nav true | tee "$OUT_DIR/am-nav.txt"
sleep 3
adb logcat -d -s REVA_NAV:W REVA_JS:I > "$OUT_DIR/nav-logcat.txt" || true
cat "$OUT_DIR/nav-logcat.txt"
grep -q 'NAV_QA_READY' "$OUT_DIR/nav-logcat.txt"
grep -q 'BLOCK_NAV:http://blog.naver.com/mister1315' "$OUT_DIR/nav-logcat.txt"
adb exec-out screencap -p > "$OUT_DIR/nav-blocked.png"

# 3) Native touch -> WebView keyboard regression harness.
adb logcat -c
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true | tee "$OUT_DIR/am-input.txt"
sleep 3
PID="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
[[ -n "$PID" ]] || { echo "input harness died" >&2; exit 3; }
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

# Holding attack now emits balanced X pulses and must never leak into adjacent skill keys.
adb logcat -c
adb shell input touchscreen swipe "$X_X" "$X_Y" "$X_X" "$X_Y" 700
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/x-input-logcat.txt" || true
cat "$OUT_DIR/x-input-logcat.txt"
grep -q 'ATTACK_START' "$OUT_DIR/x-input-logcat.txt"
grep -q 'ATTACK_STOP' "$OUT_DIR/x-input-logcat.txt"
XD=$(grep -c 'KEYDOWN:X:' "$OUT_DIR/x-input-logcat.txt" || true)
XU=$(grep -c 'KEYUP:X:' "$OUT_DIR/x-input-logcat.txt" || true)
[[ "$XD" -ge 3 ]]
[[ "$XD" -eq "$XU" ]]
! grep -E -q 'KEYDOWN:(A|S|D|F|G|H|Q|W|E|R|T|Y|Z|V|C):' "$OUT_DIR/x-input-logcat.txt"

# Skill A remains one physical tap -> one down/up pair.
adb logcat -c
adb shell input touchscreen tap "$A_X" "$A_Y"
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/a-input-logcat.txt" || true
cat "$OUT_DIR/a-input-logcat.txt"
grep -q 'PULSE:A' "$OUT_DIR/a-input-logcat.txt"
[[ "$(grep -c 'KEYDOWN:A:' "$OUT_DIR/a-input-logcat.txt")" -eq 1 ]]
[[ "$(grep -c 'KEYUP:A:' "$OUT_DIR/a-input-logcat.txt")" -eq 1 ]]

# Joystick hold must produce keyboard-like repeats and end with exactly one key-up.
END_X=$(( J_X + J_R * 2 / 3 ))
adb logcat -c
adb shell input touchscreen swipe "$J_X" "$J_Y" "$END_X" "$J_Y" 850
sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/joy-input-logcat.txt" || true
cat "$OUT_DIR/joy-input-logcat.txt"
[[ "$(grep -c 'KEYDOWN:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt")" -ge 3 ]]
[[ "$(grep -c 'KEYUP:ARROWRIGHT:' "$OUT_DIR/joy-input-logcat.txt")" -eq 1 ]]
adb exec-out screencap -p > "$OUT_DIR/input-after.png"

# 4) Real bundled Final SWF must fully resolve player.load(game.swf).
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

# 5) Background/resume after the real game has loaded.
adb shell input keyevent KEYCODE_HOME
sleep 1
adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-resume.txt"
sleep 3
PID2="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"
[[ -n "$PID2" ]]
adb exec-out screencap -p > "$OUT_DIR/resume.png"
adb logcat --pid="$PID2" -d > "$OUT_DIR/logcat-resume.txt" || true
if grep -E -q 'FATAL EXCEPTION|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-resume.txt"; then exit 7; fi

echo "PASS emulator smoke: Ruffle; Naver nav blocked; repeat-attack balanced/no stray skills; A once; joystick repeats/releases; Final ready; background/resume survived"
