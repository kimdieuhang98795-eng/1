#!/usr/bin/env bash
set -euo pipefail
APK="${1:-app/build/outputs/apk/debug/app-debug.apk}"
PKG="com.ajiu.reva"; ACTIVITY="$PKG/.MainActivity"; OUT_DIR="${2:-qa/emulator}"
mkdir -p "$OUT_DIR"; test -f "$APK"
adb wait-for-device; adb shell getprop sys.boot_completed | grep -q 1
adb install -r "$APK" | tee "$OUT_DIR/install.txt"

# Hosted API-35 images occasionally boot Pixel Launcher into an ANR dialog that sits above
# every app and absorbs adb touches. It is unrelated to Reva; suppress/dismiss it before QA.
adb shell settings put global hide_error_dialogs 1 || true
adb shell am force-stop com.google.android.apps.nexuslauncher || true
adb shell am force-stop com.android.launcher3 || true
sleep 1

capture_focus(){
  {
    adb shell dumpsys activity activities 2>/dev/null | grep -m1 -E 'mResumedActivity|topResumedActivity' || true
    adb shell dumpsys activity top 2>/dev/null | grep -m1 '^ACTIVITY ' || true
    adb shell dumpsys window displays 2>/dev/null | grep -m2 -E 'mCurrentFocus|mFocusedApp' || true
    adb shell dumpsys window windows 2>/dev/null | grep -m2 -E 'mCurrentFocus|mFocusedApp' || true
  } | tr -d '\r' > "$OUT_DIR/focus.txt"
}

assert_reva_foreground(){
  # API 35 / emulator 37 sometimes exposes no mCurrentFocus line even though the Activity is
  # visibly resumed. Prefer the ActivityManager resumed/top signals and retry through transitions.
  for i in $(seq 1 12); do
    capture_focus
    grep -q "$PKG" "$OUT_DIR/focus.txt" && return 0
    sleep 0.5
  done

  # Empty focus metadata is not itself a failure: the in-app QA sentinels below are stronger proof.
  # Only fail when Android positively reports a different foreground activity/package.
  if [[ ! -s "$OUT_DIR/focus.txt" ]]; then
    echo 'Foreground metadata unavailable on this API-35 image; continuing with in-app QA sentinels.' >&2
    return 0
  fi

  adb exec-out screencap -p > "$OUT_DIR/unexpected-system-dialog.png" || true
  echo 'Foreground is positively reported as non-Reva; possible system dialog:' >&2
  cat "$OUT_DIR/focus.txt" >&2
  return 1
}

# 1) Ruffle itself.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_ruffle true > "$OUT_DIR/am-ruffle.txt"
for i in $(seq 1 25); do sleep 1; adb logcat -d -s REVA_JS:I > "$OUT_DIR/ruffle-logcat.txt" || true; grep -q RUFFLE_QA_READY "$OUT_DIR/ruffle-logcat.txt" && break; done
grep -q RUFFLE_QA_READY "$OUT_DIR/ruffle-logcat.txt"; ! grep -q RUFFLE_QA_FAIL "$OUT_DIR/ruffle-logcat.txt"

# 2) Original Naver external navigation remains blocked.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_nav true > "$OUT_DIR/am-nav.txt"; sleep 3
assert_reva_foreground
adb logcat -d -s REVA_NAV:W REVA_JS:I > "$OUT_DIR/nav-logcat.txt" || true
grep -q 'NAV_QA_READY' "$OUT_DIR/nav-logcat.txt"; grep -q 'BLOCK_NAV:http://blog.naver.com/mister1315' "$OUT_DIR/nav-logcat.txt"
adb exec-out screencap -p > "$OUT_DIR/nav-blocked.png"

# 3) Touch/key harness.
adb logcat -c; adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true > "$OUT_DIR/am-input.txt"; sleep 3
assert_reva_foreground
adb exec-out screencap -p > "$OUT_DIR/input-ready.png"
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/layout-logcat.txt" || true
get_field(){ grep "$1" "$OUT_DIR/layout-logcat.txt" | tail -1 | sed "s/.*$1//" | awk '{print $1}'; }
XRECT="$(get_field 'XRECT:')"; ARECT="$(get_field 'ARECT:')"; JOY="$(get_field 'JOY:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$JOY" ]]
center(){ IFS=',' read -r L T R B <<< "$1"; echo "$(( (L+R)/2 )) $(( (T+B)/2 ))"; }
read X_X X_Y < <(center "$XRECT"); read A_X A_Y < <(center "$ARECT"); IFS=',' read -r J_X J_Y J_R <<< "$JOY"

# Real PC-style attack hold: exactly one X down and one X up, with zero leaked skill keys.
adb logcat -c
adb shell input touchscreen swipe "$X_X" "$X_Y" "$X_X" "$X_Y" 700; sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/x-hold-logcat.txt" || true
cat "$OUT_DIR/x-hold-logcat.txt"
[[ "$(grep -c 'KEYDOWN:X:' "$OUT_DIR/x-hold-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'KEYUP:X:' "$OUT_DIR/x-hold-logcat.txt" || true)" -eq 1 ]]
! grep -E -q 'KEYDOWN:(A|S|D|F|G|H|Q|W|E|R|T|Y|Z|V|C):' "$OUT_DIR/x-hold-logcat.txt"
! grep -q 'REPEAT:' "$OUT_DIR/x-hold-logcat.txt"

# Rapid same-skill taps must both enter the game even while the previous visual flash is still alive.
adb logcat -c
adb shell input touchscreen tap "$A_X" "$A_Y"; sleep 0.05; adb shell input touchscreen tap "$A_X" "$A_Y"; sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/a-double-logcat.txt" || true
cat "$OUT_DIR/a-double-logcat.txt"
[[ "$(grep -c 'KEYDOWN:A:' "$OUT_DIR/a-double-logcat.txt" || true)" -eq 2 ]]
[[ "$(grep -c 'KEYUP:A:' "$OUT_DIR/a-double-logcat.txt" || true)" -eq 2 ]]

# FLOAT_LEFT: begin 1.30 radii left of the old fixed center (outside v1.3's 1.12R hit circle).
# This reproduces the video's 'thumb is left of the drawn stick but the stick never claims it' failure.
FLOAT_LEFT=$(( J_X - J_R * 13 / 10 )); (( FLOAT_LEFT < 6 )) && FLOAT_LEFT=6
FLOAT_END=$(( FLOAT_LEFT - J_R / 2 )); (( FLOAT_END < 3 )) && FLOAT_END=3
echo "FLOAT_LEFT start=$FLOAT_LEFT,$J_Y end=$FLOAT_END,$J_Y center=$J_X,$J_Y r=$J_R" | tee "$OUT_DIR/floating-point.txt"
adb logcat -c
adb shell input touchscreen swipe "$FLOAT_LEFT" "$J_Y" "$FLOAT_END" "$J_Y" 850; sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/floating-left-logcat.txt" || true
cat "$OUT_DIR/floating-left-logcat.txt"
grep -q 'JOY_CLAIM:' "$OUT_DIR/floating-left-logcat.txt"
[[ "$(grep -c 'KEYDOWN:ARROWLEFT:' "$OUT_DIR/floating-left-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'KEYUP:ARROWLEFT:' "$OUT_DIR/floating-left-logcat.txt" || true)" -eq 1 ]]
! grep -q 'REPEAT:' "$OUT_DIR/floating-left-logcat.txt"
adb exec-out screencap -p > "$OUT_DIR/floating-left.png"

# Fixed-center right movement also remains a single held state.
RIGHT_END=$(( J_X + J_R * 2 / 3 ))
adb logcat -c
adb shell input touchscreen swipe "$J_X" "$J_Y" "$RIGHT_END" "$J_Y" 850; sleep 1
adb logcat -d -s REVA_TOUCH:I REVA_JS:I REVA_INPUT:I > "$OUT_DIR/fixed-right-logcat.txt" || true
[[ "$(grep -c 'KEYDOWN:ARROWRIGHT:' "$OUT_DIR/fixed-right-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'KEYUP:ARROWRIGHT:' "$OUT_DIR/fixed-right-logcat.txt" || true)" -eq 1 ]]

# 4) Bundled Final really loads, then survives background/resume.
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

echo 'PASS v1.4 emulator: nav blocked; X true hold/no stray skill; A rapid double accepted; FLOAT_LEFT outside old ring claimed; movement single down/up; Final ready; resume survived'
