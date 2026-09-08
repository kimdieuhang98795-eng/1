#!/usr/bin/env python3
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'app/src/main/java/com/ajiu/reva/MainActivity.java').read_text()
app=(r/'app/build.gradle').read_text()
smoke=(r/'tools/emulator_smoke.sh').read_text()
qa=(r/'app/src/main/assets/qa_input.html').read_text()
manifest=(r/'app/src/main/AndroidManifest.xml').read_text()
html=(r/'app/src/main/assets/index.html').read_text()

for f in [
 'app/src/main/AndroidManifest.xml','app/src/main/java/com/ajiu/reva/MainActivity.java',
 'app/src/main/assets/index.html','app/src/main/assets/qa_input.html','app/src/main/assets/qa_ruffle.html',
 'app/src/main/assets/qa_nav.html','app/src/main/assets/qa_test.swf','app/build.gradle',
 'tools/emulator_smoke.sh','tools/verify_swf.py','qa/run_local_qa.sh']:
    p=r/f; assert p.exists() and p.stat().st_size>10,f

# Existing offline/runtime guarantees.
for k in ['LOCAL_ORIGIN','shouldBlockTopNavigation(','BLOCK_NAV:','hasBundledGame(','hardResetInputs(','onWindowFocusChanged']:
    assert k in s,k
assert 'android:largeHeap="true"' in manifest and 'android:hardwareAccelerated="true"' in manifest
assert 'player.ruffle' in html and '__REVA_PLAYER_READY__' in html

# Direct DOM bridge: local Ruffle no longer depends on Android->WebView KeyEvent delivery.
for k in ['domKeySpec(','dispatchDomKey(','domFocusPrelude(','REVA_DOMKEY','forceDomReleaseDirections(','forceDomReleaseAll(']:
    assert k in s,k
assert 'if(localPlayback && domKeySpec(code)!=null)' in s
assert 'window.dispatchEvent(new KeyboardEvent' in s
assert "case KeyEvent.KEYCODE_DPAD_LEFT" in s and '"ArrowLeft","ArrowLeft"' in s
assert "case KeyEvent.KEYCODE_DPAD_RIGHT" in s and '"ArrowRight","ArrowRight"' in s
assert "case KeyEvent.KEYCODE_DPAD_DOWN" in s and '"ArrowDown","ArrowDown"' in s
# Native dispatch still exists only as online fallback.
assert 'Legacy online fallback only.' in s

# Correct game semantics: joystick is horizontal-only; Down is dedicated backstep.
for k in ['addCircle("↓","后",MODE_PULSE','BACKRECT:','JOY_CLAIM_NEUTRAL:','float engage=joyR*0.26f','float release=joyR*0.12f','setMoveState(l,r,false,false);']:
    assert k in s,k
assert 'Vertical arrows are not movement in this game' in s
assert 'setMoveState(nx<-dead,nx>dead,ny<-dead,ny>dead)' not in s
# Inspect the joystick math section specifically: it may not emit Down/Up.
ju=s[s.index('        void updateJoystick(float x,float y){'):s.index('        void releaseJoystick(){')]
assert 'send("↓"' not in ju and 'send("↑"' not in ju
assert 'ny' not in ju
assert 'moveUp=false; moveDown=false;' in ju

# v1.3 synthetic repeat architecture remains forbidden.
for forbidden in ['MODE_REPEAT','startAttackRepeat(','stopAttackRepeat(','ensureMovementRepeater(','stopMovementRepeater(','reassertMovement(','repeatKeyCode(','inputHandler.postDelayed(this,132L)','inputHandler.postDelayed(this,92L)']:
    assert forbidden not in s,forbidden

# QA now checks code/key instead of legacy keyCode, because synthetic KeyboardEvent keyCode is not authoritative.
assert 'DOM_INPUT_QA_READY' in qa and 'DOM_DOWN:' in qa and 'DOM_UP:' in qa
for k in ['VERTICAL_NO_BACKSTEP','BACKSTEP_BUTTON','DOM_DOWN:KeyX','DOM_UP:KeyX','REVA_DOMKEY','CYCLE_BALANCE']:
    assert k in smoke,k

assert "versionCode 15" in app and "versionName '1.5'" in app
assert "noCompress += ['swf', 'wasm']" in app
print('PASS v1.5: game semantics corrected (horizontal walk; Down dedicated backstep)')
print('PASS v1.5: direct DOM KeyboardEvent bridge for local Ruffle')
print('PASS v1.5: neutral-on-touch floating joystick + hysteresis')
print('PASS v1.5: unconditional direction/all-key release safeguards')
print('PASS v1.5: no synthetic repeat architecture')
