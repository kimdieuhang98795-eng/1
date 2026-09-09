#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'tools/check_project.py')
s = p.read_text()

old = '''# Correct game semantics: joystick is horizontal-only; Down is dedicated backstep.\nfor k in ['addCircle("↓","后",MODE_PULSE','BACKRECT:','JOY_CLAIM_NEUTRAL:','float engage=joyR*0.26f','float release=joyR*0.12f','setMoveState(l,r,false,false);']:\n    assert k in s,k\n'''
new = '''# Correct game semantics: joystick is horizontal-only; Down remains a dedicated backstep.\n# v1.8 moved HUD construction into ControlLayoutConfig, so do not require the old\n# hard-coded addCircle() call in MainActivity.\nconfig=(r/'app/src/main/java/com/ajiu/reva/ControlLayoutConfig.java').read_text()\nfor k in ['BACKRECT:','JOY_CLAIM_NEUTRAL:','float engage=joyR*0.26f','float release=joyR*0.12f','setMoveState(l,r,false,false);']:\n    assert k in s,k\nfor k in ['ButtonSpec.circle("↓", "后跳", PULSE','joystickZoneLeft','joystickZoneTop','joystickZoneRight','joystickZoneBottom']:\n    assert k in config,k\n'''
if old not in s:
    raise SystemExit('v1.8 QA patch: old backstep assertion block not found')
s = s.replace(old, new, 1)

old = '''# Joystick start zone is forgiving at the rendered lower-left edge. Because role assignment is immutable,\n# widening DOWN-time capture cannot later steal a GAME pointer during MOVE.\nassert 'x>=px(0f) && x<=px(390f) && y>=py(340f) && y<=py(720f)' in s\n'''
new = '''# Joystick start zone remains forgiving, but its geometry is now data-driven.\n# Role assignment is still immutable, so widening DOWN-time capture cannot later\n# steal a GAME pointer during MOVE.\nfor k in ['controlLayout.joystickZoneLeft','controlLayout.joystickZoneRight','controlLayout.joystickZoneTop','controlLayout.joystickZoneBottom']:\n    assert k in s,k\nfor k in ['0f, 340f, 390f, 720f','92f, 390f, 335f, 625f']:\n    assert k in config,k\n'''
if old not in s:
    raise SystemExit('v1.8 QA patch: old joystick-zone assertion block not found')
s = s.replace(old, new, 1)

# Ensure the new separation itself is tested without weakening inherited input checks.
marker = '''# v1.3 synthetic repeat architecture remains forbidden.\n'''
extra = '''# v1.8 HUD architecture: geometry/labels live outside MainActivity while the proven\n# pointer router and DOM bridge stay in MainActivity.\nfor k in ['ControlLayoutConfig.modern()','addConfigured(controlLayout.skillSlots[i],g[i],"",i)','LAYOUT:MODERN_V18']:\n    assert k in s,k\nfor k in ['coreButtons','skillSlots','pageButton','itemButtons','utilityButtons','ButtonSpec.circle("X", "普攻"']:\n    assert k in config,k\nassert 'addCircle("X","攻"' not in s\nassert 'float[][] pos={{986,510,34}' not in s\n\n'''
if marker not in s:
    raise SystemExit('v1.8 QA patch: insertion marker not found')
s = s.replace(marker, extra + marker, 1)

# Keep the inherited version assertions aligned with this generated build if the
# workflow has not already rewritten them.
s = s.replace('assert "versionCode 15" in app and "versionName \'1.5\'" in app',
              'assert "versionCode 18" in app and "versionName \'1.8\'" in app')

p.write_text(s)
print('PASS fix_check_project_v18: inherited input QA adapted to data-driven HUD')
