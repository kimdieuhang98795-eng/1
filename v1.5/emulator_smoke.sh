#!/usr/bin/env bash
set -euo pipefail
APK="${1:-app/build/outputs/apk/debug/app-debug.apk}"
PKG="com.ajiu.reva"; ACTIVITY="$PKG/.MainActivity"; OUT_DIR="${2:-qa/emulator}"
mkdir -p "$OUT_DIR"; test -f "$APK"
adb wait-for-device; adb shell getprop sys.boot_completed | grep -q 1
adb install -r "$APK" | tee "$OUT_DIR/install.txt"
adb shell settings put global hide_error_dialogs 1 || true
adb shell am force-stop com.google.android.apps.nexuslauncher || true
adb shell am force-stop com.android.launcher3 || true
sleep 1

capture_focus(){
  {
    adb shell dumpsys activity activities 2>/dev/null | grep -m1 -E 'mResumedActivity|topResumedActivity' || true
    adb shell dumpsys activity top 2>/dev/null | grep -m1 '^ACTIVITY ' || true
    adb shell dumpsys window displays 2>/dev/null | grep -m2 -E 'mCurrentFocus|mFocusedApp' || true
  } | tr -d '\r' > "$OUT_DIR/focus.txt"
}
assert_reva_foreground(){
  for i in $(seq 1 12); do capture_focus; grep -q "$PKG" "$OUT_DIR/focus.txt" && return 0; sleep 0.5; done
  if [[ ! -s "$OUT_DIR/focus.txt" ]]; then return 0; fi
  adb exec-out screencap -p > "$OUT_DIR/unexpected-system-dialog.png" || true
  cat "$OUT_DIR/focus.txt" >&2; return 1
}
logs(){ adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I REVA_DOMKEY:I REVA_NAV:W > "$1" || true; }

# 1) Ruffle engine can load a real tiny SWF.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_ruffle true > "$OUT_DIR/am-ruffle.txt"
for i in $(seq 1 25); do sleep 1; adb logcat -d -s REVA_JS:I > "$OUT_DIR/ruffle-logcat.txt" || true; grep -q RUFFLE_QA_READY "$OUT_DIR/ruffle-logcat.txt" && break; done
grep -q RUFFLE_QA_READY "$OUT_DIR/ruffle-logcat.txt"; ! grep -q RUFFLE_QA_FAIL "$OUT_DIR/ruffle-logcat.txt"

# 2) Original external navigation remains blocked.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_nav true > "$OUT_DIR/am-nav.txt"; sleep 3
assert_reva_foreground
adb logcat -d -s REVA_NAV:W REVA_JS:I > "$OUT_DIR/nav-logcat.txt" || true
grep -q 'NAV_QA_READY' "$OUT_DIR/nav-logcat.txt"; grep -q 'BLOCK_NAV:http://blog.naver.com/mister1315' "$OUT_DIR/nav-logcat.txt"

# 3) Direct DOM input harness.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true > "$OUT_DIR/am-input.txt"; sleep 3
assert_reva_foreground
adb exec-out screencap -p > "$OUT_DIR/input-ready.png"
logs "$OUT_DIR/layout-logcat.txt"
grep -q 'DOM_INPUT_QA_READY' "$OUT_DIR/layout-logcat.txt"
get_field(){ grep "$1" "$OUT_DIR/layout-logcat.txt" | tail -1 | sed "s/.*$1//" | awk '{print $1}'; }
XRECT="$(get_field 'XRECT:')"; ARECT="$(get_field 'ARECT:')"; BACKRECT="$(get_field 'BACKRECT:')"; JOY="$(get_field 'JOY:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" ]]
center(){ IFS=',' read -r L T R B <<< "$1"; echo "$(( (L+R)/2 )) $(( (T+B)/2 ))"; }
read X_X X_Y < <(center "$XRECT"); read A_X A_Y < <(center "$ARECT"); read B_X B_Y < <(center "$BACKRECT"); IFS=',' read -r J_X J_Y J_R <<< "$JOY"

# X hold: direct DOM route, one real held state, no leaked skill/down events.
adb logcat -c
adb shell input touchscreen swipe "$X_X" "$X_Y" "$X_X" "$X_Y" 700; sleep 1
logs "$OUT_DIR/x-hold-logcat.txt"; cat "$OUT_DIR/x-hold-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY.*DOWN:KeyX' "$OUT_DIR/x-hold-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY.*UP:KeyX' "$OUT_DIR/x-hold-logcat.txt" || true)" -eq 1 ]]
grep -q 'DOM_DOWN:KeyX:x' "$OUT_DIR/x-hold-logcat.txt"; grep -q 'DOM_UP:KeyX:x' "$OUT_DIR/x-hold-logcat.txt"
! grep -E -q 'REVA_DOMKEY.*DOWN:Key(A|S|D|F|G|H|Q|W|E|R|T|Y|Z|V|C)' "$OUT_DIR/x-hold-logcat.txt"
! grep -q 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/x-hold-logcat.txt"

# Rapid same skill twice: visual flash must not eat the second input.
adb logcat -c
adb shell input touchscreen tap "$A_X" "$A_Y"; sleep 0.05; adb shell input touchscreen tap "$A_X" "$A_Y"; sleep 1
logs "$OUT_DIR/a-double-logcat.txt"; cat "$OUT_DIR/a-double-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY.*DOWN:KeyA' "$OUT_DIR/a-double-logcat.txt" || true)" -eq 2 ]]
[[ "$(grep -c 'REVA_DOMKEY.*UP:KeyA' "$OUT_DIR/a-double-logcat.txt" || true)" -eq 2 ]]

# VERTICAL_NO_BACKSTEP: a downward joystick drag must NOT emit ArrowDown.
VERT_END_Y=$(( J_Y + J_R * 3 / 4 ))
adb logcat -c
adb shell input touchscreen swipe "$J_X" "$J_Y" "$J_X" "$VERT_END_Y" 700; sleep 1
logs "$OUT_DIR/vertical-no-backstep.txt"; cat "$OUT_DIR/vertical-no-backstep.txt"
! grep -q 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/vertical-no-backstep.txt"
! grep -q 'REVA_DOMKEY.*DOWN:ArrowLeft' "$OUT_DIR/vertical-no-backstep.txt"
! grep -q 'REVA_DOMKEY.*DOWN:ArrowRight' "$OUT_DIR/vertical-no-backstep.txt"
! grep -q 'PULSE:↓' "$OUT_DIR/vertical-no-backstep.txt"
echo 'VERTICAL_NO_BACKSTEP PASS' | tee -a "$OUT_DIR/vertical-no-backstep.txt"

# BACKSTEP_BUTTON: Down exists only as an explicit dedicated button.
adb logcat -c
adb shell input touchscreen tap "$B_X" "$B_Y"; sleep 1
logs "$OUT_DIR/backstep-button.txt"; cat "$OUT_DIR/backstep-button.txt"
[[ "$(grep -c 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/backstep-button.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY.*UP:ArrowDown' "$OUT_DIR/backstep-button.txt" || true)" -eq 1 ]]
grep -q 'PULSE:↓' "$OUT_DIR/backstep-button.txt"
echo 'BACKSTEP_BUTTON PASS' | tee -a "$OUT_DIR/backstep-button.txt"

# Floating left start outside the old ring: neutral on touch, then left only after drag.
FLOAT_LEFT=$(( J_X - J_R * 13 / 10 )); (( FLOAT_LEFT < 6 )) && FLOAT_LEFT=6
FLOAT_END=$(( FLOAT_LEFT - J_R / 2 )); (( FLOAT_END < 3 )) && FLOAT_END=3
adb logcat -c
adb shell input touchscreen swipe "$FLOAT_LEFT" "$J_Y" "$FLOAT_END" "$J_Y" 850; sleep 1
logs "$OUT_DIR/floating-left-logcat.txt"; cat "$OUT_DIR/floating-left-logcat.txt"
grep -q 'JOY_CLAIM_NEUTRAL:' "$OUT_DIR/floating-left-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY.*DOWN:ArrowLeft' "$OUT_DIR/floating-left-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY.*UP:ArrowLeft' "$OUT_DIR/floating-left-logcat.txt" || true)" -eq 1 ]]
! grep -q 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/floating-left-logcat.txt"
adb exec-out screencap -p > "$OUT_DIR/floating-left.png"

# Right movement behaves the same.
RIGHT_END=$(( J_X + J_R * 2 / 3 ))
adb logcat -c
adb shell input touchscreen swipe "$J_X" "$J_Y" "$RIGHT_END" "$J_Y" 850; sleep 1
logs "$OUT_DIR/right-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY.*DOWN:ArrowRight' "$OUT_DIR/right-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY.*UP:ArrowRight' "$OUT_DIR/right-logcat.txt" || true)" -eq 1 ]]
! grep -q 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/right-logcat.txt"

# CYCLE_BALANCE: repeated alternating gestures may never accumulate a held direction.
LEFT_END=$(( J_X - J_R * 2 / 3 )); (( LEFT_END < 3 )) && LEFT_END=3
adb logcat -c
for i in $(seq 1 10); do
  adb shell input touchscreen swipe "$J_X" "$J_Y" "$LEFT_END" "$J_Y" 160 >/dev/null
  adb shell input touchscreen swipe "$J_X" "$J_Y" "$RIGHT_END" "$J_Y" 160 >/dev/null
done
sleep 1
logs "$OUT_DIR/cycle-balance.txt"
LD="$(grep -c 'REVA_DOMKEY.*DOWN:ArrowLeft' "$OUT_DIR/cycle-balance.txt" || true)"; LU="$(grep -c 'REVA_DOMKEY.*UP:ArrowLeft' "$OUT_DIR/cycle-balance.txt" || true)"
RD="$(grep -c 'REVA_DOMKEY.*DOWN:ArrowRight' "$OUT_DIR/cycle-balance.txt" || true)"; RU="$(grep -c 'REVA_DOMKEY.*UP:ArrowRight' "$OUT_DIR/cycle-balance.txt" || true)"
echo "CYCLE_BALANCE L=$LD/$LU R=$RD/$RU" | tee -a "$OUT_DIR/cycle-balance.txt"
[[ "$LD" -eq 10 && "$LU" -eq 10 && "$RD" -eq 10 && "$RU" -eq 10 ]]
! grep -q 'REVA_DOMKEY.*DOWN:ArrowDown' "$OUT_DIR/cycle-balance.txt"

# 4) Bundled Final loads through Ruffle and survives background/resume.
adb logcat -c; adb shell am force-stop "$PKG"
adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-normal.txt"
for i in $(seq 1 60); do
  sleep 1; PID="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"; [[ -n "$PID" ]] || exit 4
  adb logcat --pid="$PID" -d > "$OUT_DIR/logcat-app.txt" || true
  grep -q REVA_GAME_READY "$OUT_DIR/logcat-app.txt" && break
  ! grep -E -q 'FATAL EXCEPTION|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-app.txt" || exit 4
done
grep -q REVA_GAME_READY "$OUT_DIR/logcat-app.txt"; adb exec-out screencap -p > "$OUT_DIR/normal-launch.png"
adb shell input keyevent KEYCODE_HOME; sleep 1; adb shell am start -W -n "$ACTIVITY" > "$OUT_DIR/am-resume.txt"; sleep 3
PID2="$(adb shell pidof "$PKG" | tr -d '\r' | awk '{print $1}')"; [[ -n "$PID2" ]]
adb logcat --pid="$PID2" -d > "$OUT_DIR/logcat-resume.txt" || true; ! grep -E -q 'FATAL EXCEPTION|ANR in com\.ajiu\.reva' "$OUT_DIR/logcat-resume.txt"
adb exec-out screencap -p > "$OUT_DIR/resume.png"

echo 'PASS v1.5 emulator: DOM bridge; horizontal-only joystick; vertical no backstep; dedicated backstep; balanced 20 direction gestures; Final ready/resume'
