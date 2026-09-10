#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/emulator_smoke.sh')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.11 smoke missing needle: '+old[:200].replace('\n','\\n'))
    s=s.replace(old,new,1)

# Extend the v1.10 layout-field parsing with the presentation-only profile selector.
once('''CTRLRECT="$(get_field 'CTRLRECT:')"; BEXRECT="$(get_field 'BEXRECT:')"\n[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" && -n "$CTRLRECT" && -n "$BEXRECT" ]]\n''','''CTRLRECT="$(get_field 'CTRLRECT:')"; BEXRECT="$(get_field 'BEXRECT:')"; PROFILERECT="$(get_field 'PROFILERECT:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" && -n "$CTRLRECT" && -n "$BEXRECT" && -n "$PROFILERECT" ]]
''')

# Do not anchor to the whole PARSED_RECTS printf: inherited smoke formatting has
# changed several times. Only extend the stable coordinate-read statement.
once('''read CTRL_X CTRL_Y < <(center "$CTRLRECT"); read BEX_X BEX_Y < <(center "$BEXRECT")''','''read CTRL_X CTRL_Y < <(center "$CTRLRECT"); read BEX_X BEX_Y < <(center "$BEXRECT"); read PROFILE_X PROFILE_Y < <(center "$PROFILERECT")''')

# Keep explicit evidence of the resolved selector target without altering the
# inherited PARSED_RECTS contract consumed by older regression checks.
once('''[[ "$X_X" -ne "$BEX_X" || "$X_Y" -ne "$BEX_Y" ]]\n''','''[[ "$X_X" -ne "$BEX_X" || "$X_Y" -ne "$BEX_Y" ]]
printf 'PROFILE_RECT center=%s,%s raw=%s\\n' "$PROFILE_X" "$PROFILE_Y" "$PROFILERECT" | tee -a "$OUT_DIR/parsed-rects.txt"
''')

# First selector regression: Spitfire -> Ranger. This is presentation state only
# and must not leak a game keydown into Ruffle.
marker='''# The parent workflow checks the final device log for LAYOUT:MODERN_V110.\n'''
insert='''# PROFILE_SWITCH: presentation-only selector must not leak a game key event.
adb logcat -c
adb shell input touchscreen tap "$PROFILE_X" "$PROFILE_Y"; sleep 1
logs "$OUT_DIR/profile-switch-logcat.txt"; cat "$OUT_DIR/profile-switch-logcat.txt"
grep -q 'REVA_TOUCH: PROFILE:Ranger:漫游' "$OUT_DIR/profile-switch-logcat.txt"
! grep -q 'REVA_DOMKEY: DOWN:' "$OUT_DIR/profile-switch-logcat.txt"
echo 'PROFILE_SWITCH PASS' | tee -a "$OUT_DIR/profile-switch-logcat.txt"

# The parent workflow checks the final device log for LAYOUT:MODERN_V111.
'''
once(marker,insert)

# v1.11 advances the runtime marker everywhere in the inherited final-layout block.
s=s.replace('LAYOUT:MODERN_V110','LAYOUT:MODERN_V111')

# The inherited smoke continues after its mid-suite "final layout" checkpoint and
# clears logcat again for later tests. Add one authoritative post-suite relaunch.
# The first selector tap persisted Ranger. After force-stop/start, one more tap must
# therefore advance Ranger -> Berserker; falling back to Spitfire would produce
# Ranger instead and fail this persistence check. This final tap also deliberately
# leaves a fresh V111 layout marker in device logcat for the parent workflow.
s += r'''

# v1.11 authoritative post-suite profile persistence + final marker.
adb logcat -c
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$ACTIVITY" --ez qa_input true > "$OUT_DIR/am-profile-persist.txt"
sleep 2
adb shell input touchscreen tap "$PROFILE_X" "$PROFILE_Y"; sleep 1
logs "$OUT_DIR/profile-persist-logcat.txt"; cat "$OUT_DIR/profile-persist-logcat.txt"
grep -q 'REVA_TOUCH: PROFILE:Berserker:狂战' "$OUT_DIR/profile-persist-logcat.txt"
grep -q 'REVA_TOUCH: LAYOUT:MODERN_V111:' "$OUT_DIR/profile-persist-logcat.txt"
! grep -q 'REVA_DOMKEY: DOWN:' "$OUT_DIR/profile-persist-logcat.txt"
echo 'PROFILE_PERSIST PASS' | tee -a "$OUT_DIR/profile-persist-logcat.txt"
'''

for token in ['PROFILERECT=','PROFILE_X','PROFILE_SWITCH PASS','PROFILE:Ranger:漫游',
              'PROFILE_PERSIST PASS','PROFILE:Berserker:狂战','LAYOUT:MODERN_V111','PROFILE_RECT center=']:
    if token not in s: raise SystemExit('v1.11 smoke insertion failed: '+token)
if 'LAYOUT:MODERN_V110' in s:
    raise SystemExit('v1.11 stale V110 marker in smoke')
p.write_text(s)

# The inherited v1.5 layout checker compares comma-spacing literally. v1.11
# intentionally keeps the same geometry with compact formatting, so normalize
# whitespace while retaining exact semantic/coordinate assertions.
check=p.parent/'check_project.py'
fix=Path(__file__).with_name('fix_check_v111.py')
if not check.is_file() or not fix.is_file():
    raise SystemExit('v1.11 QA normalization helper missing')
subprocess.run([sys.executable,str(fix),str(check)],check=True)

print('PASS fix_smoke_v111: profile switch + restart persistence + zero-keydown leak + authoritative V111 marker + semantic layout QA')
