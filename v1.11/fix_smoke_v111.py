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

# Insert selector regression immediately before v1.10's final fresh-layout launch.
marker='''# The parent workflow checks the final device log for LAYOUT:MODERN_V110.\n'''
insert='''# PROFILE_SWITCH: presentation-only selector must not leak a game key event.
adb logcat -c
adb shell input touchscreen tap "$PROFILE_X" "$PROFILE_Y"; sleep 1
logs "$OUT_DIR/profile-switch-logcat.txt"; cat "$OUT_DIR/profile-switch-logcat.txt"
grep -q 'PROFILE:Ranger:漫游' "$OUT_DIR/profile-switch-logcat.txt"
! grep -q 'REVA_DOMKEY.*DOWN:' "$OUT_DIR/profile-switch-logcat.txt"
echo 'PROFILE_SWITCH PASS' | tee -a "$OUT_DIR/profile-switch-logcat.txt"

# The parent workflow checks the final device log for LAYOUT:MODERN_V111.
'''
once(marker,insert)

# v1.11 advances the runtime marker everywhere in the final-layout smoke block.
s=s.replace('LAYOUT:MODERN_V110','LAYOUT:MODERN_V111')

for token in ['PROFILERECT=','PROFILE_X','PROFILE_SWITCH PASS','PROFILE:Ranger:漫游','LAYOUT:MODERN_V111','PROFILE_RECT center=']:
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

print('PASS fix_smoke_v111: robust profile selector tap + zero-keydown leak + V111 final marker + semantic layout QA')
