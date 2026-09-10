#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
main = root / 'app/src/main/java/com/ajiu/reva/MainActivity.java'
gradle = root / 'app/build.gradle'
config_dst = root / 'app/src/main/java/com/ajiu/reva/ControlLayoutConfig.java'
config_src = Path(__file__).with_name('ControlLayoutConfig.java')

s = main.read_text()

def once(old, new):
    global s
    if old not in s:
        raise SystemExit('v1.10 missing needle: ' + old[:180].replace('\n','\\n'))
    s = s.replace(old, new, 1)

# ---------------------------------------------------------------------------
# 1) Expose Ctrl to the same Android -> DOM keyboard bridge used by all other
#    proven controls. B already maps through the generic A..Z map.
# ---------------------------------------------------------------------------
once('''        keys.put("↑", KeyEvent.KEYCODE_DPAD_UP);\n''','''        keys.put("↑", KeyEvent.KEYCODE_DPAD_UP);
        keys.put("CTRL", KeyEvent.KEYCODE_CTRL_LEFT);
''')

once('''            case KeyEvent.KEYCODE_SPACE: return new String[]{" ","Space","0"};\n''','''            case KeyEvent.KEYCODE_CTRL_LEFT: return new String[]{"Control","ControlLeft","1"};
            case KeyEvent.KEYCODE_CTRL_RIGHT: return new String[]{"Control","ControlRight","2"};
            case KeyEvent.KEYCODE_SPACE: return new String[]{" ","Space","0"};
''')

# The unconditional recovery path is intentionally broader than current Java
# keyDownTimes: it repairs Ruffle state even after focus/lifecycle edge cases.
once('''            +"['x','KeyX',0],['c','KeyC',0],['z','KeyZ',0],['v','KeyV',0],"\n''','''            +"['x','KeyX',0],['c','KeyC',0],['z','KeyZ',0],['v','KeyV',0],['b','KeyB',0],"
''')
once('''            +"[' ','Space',0],['Shift','ShiftLeft',1],['1','Digit1',0],['2','Digit2',0],['3','Digit3',0]];"\n''','''            +"['Control','ControlLeft',1],[' ','Space',0],['Shift','ShiftLeft',1],['1','Digit1',0],['2','Digit2',0],['3','Digit3',0]];"
''')

# Keep utility key badges compact inside the new 2x2 EX cluster.
once('''            String shown="SPACE".equals(key)?"SP":"SHIFT".equals(key)?"SH":key;\n''','''            String shown="SPACE".equals(key)?"SP":"SHIFT".equals(key)?"SH":"CTRL".equals(key)?"CT":key;
''')

# ---------------------------------------------------------------------------
# 2) Swap only layout metadata. Do not alter v1.9 pointer ownership, pulse
#    timing, haptics, drawing feedback, or the twelve-key skill painter.
# ---------------------------------------------------------------------------
once('''LAYOUT:MODERN_V19''','''LAYOUT:MODERN_V110''')

if not config_src.exists():
    raise SystemExit('missing v1.10 ControlLayoutConfig.java')
config_dst.write_text(config_src.read_text())

# Metadata.
g = gradle.read_text()
if 'versionCode 19' not in g or "versionName '1.9'" not in g:
    raise SystemExit('expected v1.9 version markers not found')
g = g.replace('versionCode 19', 'versionCode 20', 1).replace("versionName '1.9'", "versionName '1.10'", 1)
gradle.write_text(g)
main.write_text(s)

# ---------------------------------------------------------------------------
# 3) Regression guards. v1.10 is a narrowly-scoped completeness patch.
# ---------------------------------------------------------------------------
for required in [
    'keys.put("CTRL", KeyEvent.KEYCODE_CTRL_LEFT)',
    'case KeyEvent.KEYCODE_CTRL_LEFT: return new String[]{"Control","ControlLeft","1"}',
    "['b','KeyB',0]",
    "['Control','ControlLeft',1]",
    'LAYOUT:MODERN_V110',
    'ROLE_JOYSTICK','ROLE_BUTTON','ROLE_GAME',
    'dispatchDomKey(','forceDomReleaseAll(',
    'kickButtonFeedback(B b)',
    'SkillIconPainter.draw(c,b.r,b.label,b.active,sc)',
    'pulse(b.label)','send(b.label,true)'
]:
    if required not in s:
        raise SystemExit('v1.10 required logic missing: ' + required)

for forbidden in [
    'LAYOUT:MODERN_V19',
    'recoverJoystickOnMove(',
    'inputHandler.postDelayed(this,132L)',
    'inputHandler.postDelayed(this,92L)'
]:
    if forbidden in s:
        raise SystemExit('v1.10 forbidden residue: ' + forbidden)

cfg = config_dst.read_text()
for token in [
    'ButtonSpec.pill("CTRL",  "EXⅠ", HOLD',
    'ButtonSpec.pill("SHIFT", "EXⅡ", HOLD',
    'ButtonSpec.pill("SPACE", "EXⅢ", HOLD',
    'ButtonSpec.pill("B",     "EXⅣ", HOLD'
]:
    if token not in cfg:
        raise SystemExit('v1.10 missing EX control: ' + token)

print('PASS apply_v110: Ctrl/B EX controls + DOM mapping + unconditional release coverage')
print('PASS apply_v110: v1.9 pointer router, skill paging and tactile feedback preserved')
