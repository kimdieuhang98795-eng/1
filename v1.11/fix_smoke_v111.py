#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/emulator_smoke.sh')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.11 smoke missing needle: '+old[:200].replace('\n','\\n'))
    s=s.replace(old,new,1)

once('''CTRLRECT="$(get_field 'CTRLRECT:')"; BEXRECT="$(get_field 'BEXRECT:')"\n[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" && -n "$CTRLRECT" && -n "$BEXRECT" ]]\n''','''CTRLRECT="$(get_field 'CTRLRECT:')"; BEXRECT="$(get_field 'BEXRECT:')"; PROFILERECT="$(get_field 'PROFILERECT:')"
[[ -n "$XRECT" && -n "$ARECT" && -n "$BACKRECT" && -n "$JOY" && -n "$CTRLRECT" && -n "$BEXRECT" && -n "$PROFILERECT" ]]
''')

once('''read CTRL_X CTRL_Y < <(center "$CTRLRECT"); read BEX_X BEX_Y < <(center "$BEXRECT")\nprintf 'PARSED_RECTS X=%s,%s A=%s,%s BACK=%s,%s CTRL=%s,%s BEX=%s,%s JOY=%s,%s,%s\\n' "$X_X" "$X_Y" "$A_X" "$A_Y" "$B_X" "$B_Y" "$CTRL_X" "$CTRL_Y" "$BEX_X" "$BEX_Y" "$J_X" "$J_Y" "$J_R" | tee "$OUT_DIR/parsed-rects.txt"\n''','''read CTRL_X CTRL_Y < <(center "$CTRLRECT"); read BEX_X BEX_Y < <(center "$BEXRECT"); read PROFILE_X PROFILE_Y < <(center "$PROFILERECT")
printf 'PARSED_RECTS X=%s,%s A=%s,%s BACK=%s,%s CTRL=%s,%s BEX=%s,%s PROFILE=%s,%s JOY=%s,%s,%s\n' "$X_X" "$X_Y" "$A_X" "$A_Y" "$B_X" "$B_Y" "$CTRL_X" "$CTRL_Y" "$BEX_X" "$BEX_Y" "$PROFILE_X" "$PROFILE_Y" "$J_X" "$J_Y" "$J_R" | tee "$OUT_DIR/parsed-rects.txt"
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

for token in ['PROFILERECT=','PROFILE_X','PROFILE_SWITCH PASS','PROFILE:Ranger:漫游','LAYOUT:MODERN_V111']:
    if token not in s: raise SystemExit('v1.11 smoke insertion failed: '+token)
if 'LAYOUT:MODERN_V110' in s:
    raise SystemExit('v1.11 stale V110 marker in smoke')
p.write_text(s)
print('PASS fix_smoke_v111: profession selector tap + zero-keydown leak + V111 final marker')
