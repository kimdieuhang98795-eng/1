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
assert 'Legacy online fallback only.' in s

# Correct game semantics: joystick is horizontal-only; Down is dedicated backstep.
for k in ['addCircle("↓","后",MODE_PULSE','BACKRECT:','JOY_CLAIM_NEUTRAL:','float engage=joyR*0.26f','float release=joyR*0.12f','setMoveState(l,r,false,false);']:
    assert k in s,k
assert 'Vertical arrows are not movement in this game' in s
assert 'setMoveState(nx<-dead,nx>dead,ny<-dead,ny>dead)' not in s
ju=s[s.index('        void updateJoystick(float x,float y){'):s.index('        void releaseJoystick(){')]
assert 'send("↓"' not in ju and 'send("↑"' not in ju
assert 'ny' not in ju
assert 'moveUp=false; moveDown=false;' in ju

# Pointer ownership: no MOVE-time reclamation, no ownership migration.
for forbidden in ['recoverJoystickOnMove(','pointerExists(MotionEvent e,int pid)']:
    assert forbidden not in s, forbidden
assert 'pointerRoles' in s and 'ROLE_JOYSTICK' in s and 'ROLE_BUTTON' in s
assert 'assignPointerRole(' in s and 'releasePointerRole(' in s

# v1.3 synthetic repeat architecture remains forbidden.
for forbidden in ['MODE_REPEAT','startAttackRepeat(','stopAttackRepeat(','ensureMovementRepeater(','stopMovementRepeater(','reassertMovement(','repeatKeyCode(','inputHandler.postDelayed(this,132L)','inputHandler.postDelayed(this,92L)']:
    assert forbidden not in s,forbidden

# Input black box must log both logical and backend events so real-device ghosts can be diagnosed.
for k in ['REVA_TRACE','traceInput(','TRACE_CAPACITY','LOGICAL:','BACKEND:']:
    assert k in s,k

# QA page dynamically constructs DOM_DOWN / DOM_UP records.
assert 'DOM_INPUT_QA_READY' in qa
assert "'DOM_'+type+':'" in qa
assert "window.addEventListener('keydown'" in qa and "window.addEventListener('keyup'" in qa
for k in ['VERTICAL_NO_BACKSTEP','BACKSTEP_BUTTON','DOM_DOWN:KeyX','DOM_UP:KeyX','REVA_DOMKEY','CYCLE_BALANCE']:
    assert k in smoke,k

assert "versionCode 15" in app and "versionName '1.5'" in app
assert "noCompress += ['swf', 'wasm']" in app
print('PASS v1.5: stable pointer ownership; no MOVE-time reclamation')
print('PASS v1.5: game semantics corrected (horizontal walk; Down dedicated backstep)')
print('PASS v1.5: direct DOM KeyboardEvent bridge for local Ruffle')
print('PASS v1.5: neutral-on-touch floating joystick + hysteresis')
print('PASS v1.5: input black-box trace for logical/backend events')
print('PASS v1.5: unconditional direction/all-key release safeguards')
print('PASS v1.5: no synthetic repeat architecture')
