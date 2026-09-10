#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/emulator_smoke.sh')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.10 smoke missing needle: '+old[:180].replace('\n','\\n'))
    s=s.replace(old,new,1)

# XRECT is a suffix of BEXRECT. The old substring grep plus tail -1 therefore
# returned the later BEXRECT line when asking for XRECT, making the legacy X
# hold regression physically press B. Match the REVA_TOUCH field token exactly.
once('''get_field(){ grep "$1" "$OUT_DIR/layout-logcat.txt" | tail -1 | sed "s/.*$1//" | awk '{print $1}'; }\n''','''get_field(){ grep -F "REVA_TOUCH: $1" "$OUT_DIR/layout-logcat.txt" | tail -1 | sed "s/.*REVA_TOUCH: $1//" | awk '{print $1}'; }
''')

once('''XRECT="$(get_field 'XRECT:')"; ARECT="$(get_field 'ARECT:')"; BACKRECT="$(get_field 'BACKRECT:')"; JOY="$(get_field 'JOY:')"\n[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" ]]\n''','''XRECT="$(get_field 'XRECT:')"; ARECT="$(get_field 'ARECT:')"; BACKRECT="$(get_field 'BACKRECT:')"; JOY="$(get_field 'JOY:')"
CTRLRECT="$(get_field 'CTRLRECT:')"; BEXRECT="$(get_field 'BEXRECT:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" && -n "$CTRLRECT" && -n "$BEXRECT" ]]
''')

once('''read X_X X_Y < <(center "$XRECT"); read A_X A_Y < <(center "$ARECT"); read B_X B_Y < <(center "$BACKRECT"); IFS=',' read -r J_X J_Y J_R <<< "$JOY"\n''','''read X_X X_Y < <(center "$XRECT"); read A_X A_Y < <(center "$ARECT"); read B_X B_Y < <(center "$BACKRECT"); IFS=',' read -r J_X J_Y J_R <<< "$JOY"
read CTRL_X CTRL_Y < <(center "$CTRLRECT"); read BEX_X BEX_Y < <(center "$BEXRECT")
printf 'PARSED_RECTS X=%s,%s A=%s,%s BACK=%s,%s CTRL=%s,%s BEX=%s,%s JOY=%s,%s,%s\n' "$X_X" "$X_Y" "$A_X" "$A_Y" "$B_X" "$B_Y" "$CTRL_X" "$CTRL_Y" "$BEX_X" "$BEX_Y" "$J_X" "$J_Y" "$J_R" | tee "$OUT_DIR/parsed-rects.txt"
[[ "$X_X" -ne "$BEX_X" || "$X_Y" -ne "$BEX_Y" ]]
''')

marker='''echo 'BACKSTEP_BUTTON PASS' | tee -a "$OUT_DIR/backstep-button.txt"\n'''
insert=marker+'''

# EX_CTRL: original 3.0 EX polls Ctrl via Key.isDown(17); Android must emit a
# browser ControlLeft hold, not silently drop it at domKeySpec().
adb logcat -c
adb shell input touchscreen swipe "$CTRL_X" "$CTRL_Y" "$CTRL_X" "$CTRL_Y" 420; sleep 1
logs "$OUT_DIR/ex-ctrl-logcat.txt"; cat "$OUT_DIR/ex-ctrl-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY: DOWN:ControlLeft$' "$OUT_DIR/ex-ctrl-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY: UP:ControlLeft$' "$OUT_DIR/ex-ctrl-logcat.txt" || true)" -eq 1 ]]
grep -q 'DOM_DOWN:ControlLeft:Control' "$OUT_DIR/ex-ctrl-logcat.txt"
grep -q 'DOM_UP:ControlLeft:Control' "$OUT_DIR/ex-ctrl-logcat.txt"
grep -q 'PRESS:CTRL' "$OUT_DIR/ex-ctrl-logcat.txt"
grep -q 'RELEASE:CTRL' "$OUT_DIR/ex-ctrl-logcat.txt"
echo 'EX_CTRL PASS' | tee -a "$OUT_DIR/ex-ctrl-logcat.txt"

# EX_B: B already benefits from the generic A..Z DOM mapping, but v1.10 gives
# it a real touch target and covers it in the unconditional hard-release list.
adb logcat -c
adb shell input touchscreen swipe "$BEX_X" "$BEX_Y" "$BEX_X" "$BEX_Y" 420; sleep 1
logs "$OUT_DIR/ex-b-logcat.txt"; cat "$OUT_DIR/ex-b-logcat.txt"
[[ "$(grep -c 'REVA_DOMKEY: DOWN:KeyB$' "$OUT_DIR/ex-b-logcat.txt" || true)" -eq 1 ]]
[[ "$(grep -c 'REVA_DOMKEY: UP:KeyB$' "$OUT_DIR/ex-b-logcat.txt" || true)" -eq 1 ]]
grep -q 'DOM_DOWN:KeyB:b' "$OUT_DIR/ex-b-logcat.txt"
grep -q 'DOM_UP:KeyB:b' "$OUT_DIR/ex-b-logcat.txt"
grep -q 'PRESS:B' "$OUT_DIR/ex-b-logcat.txt"
grep -q 'RELEASE:B' "$OUT_DIR/ex-b-logcat.txt"
echo 'EX_B PASS' | tee -a "$OUT_DIR/ex-b-logcat.txt"

# The parent workflow checks the final device log for LAYOUT:MODERN_V110.
# Individual input regressions intentionally clear logcat, so finish with a
# fresh real app launch and verify that the layout marker is emitted again.
adb logcat -c
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true > "$OUT_DIR/am-final-layout.txt"
sleep 2
adb logcat -d -s REVA_TOUCH:I > "$OUT_DIR/final-layout-logcat.txt" || true
grep -q 'LAYOUT:MODERN_V110' "$OUT_DIR/final-layout-logcat.txt"
echo 'FINAL_LAYOUT PASS' | tee -a "$OUT_DIR/final-layout-logcat.txt"
'''
once(marker,insert)

if 'EX_CTRL PASS' not in s or 'EX_B PASS' not in s or 'FINAL_LAYOUT PASS' not in s or "CTRLRECT=" not in s or 'REVA_TOUCH: $1' not in s:
    raise SystemExit('v1.10 EX smoke insertion failed')
p.write_text(s)
print('PASS fix_smoke_v110: exact layout fields + Ctrl/B regression + final layout evidence; render QA is stdlib-only')
