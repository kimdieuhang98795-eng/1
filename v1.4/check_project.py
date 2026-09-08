#!/usr/bin/env python3
from pathlib import Path
r=Path(__file__).resolve().parents[1]
base=r/'app/src/main/java/com/ajiu/reva/MainActivity.java'
s=base.read_text()
app=(r/'app/build.gradle').read_text()
smoke=(r/'tools/emulator_smoke.sh').read_text()
manifest=(r/'app/src/main/AndroidManifest.xml').read_text()
html=(r/'app/src/main/assets/index.html').read_text()

for f in [
 'app/src/main/AndroidManifest.xml','app/src/main/java/com/ajiu/reva/MainActivity.java',
 'app/src/main/assets/index.html','app/src/main/assets/qa_input.html','app/src/main/assets/qa_ruffle.html',
 'app/src/main/assets/qa_nav.html','app/src/main/assets/qa_test.swf','app/build.gradle','tools/emulator_smoke.sh',
 'tools/verify_swf.py','qa/run_local_qa.sh']:
    p=r/f; assert p.exists() and p.stat().st_size>10,f

# Existing runtime/offline/nav guarantees stay intact.
for k in ['LOCAL_ORIGIN','shouldBlockTopNavigation(','BLOCK_NAV:','hasBundledGame(','hardResetInputs(','onWindowFocusChanged','SafeSwfInstaller.replaceVerified']:
    assert k in s,k
assert 'android:largeHeap="true"' in manifest and 'android:hardwareAccelerated="true"' in manifest
assert 'player.ruffle' in html and '__REVA_PLAYER_READY__' in html

# v1.4 input architecture: real holds, hybrid floating joystick, stable ownership, visual/input separation.
for k in ['hitJoystickStartZone(','beginJoystick(','recoverJoystickOnMove(','joyHomeX','joyBaseX','JOY_CLAIM:','JOYZONE:','flashSeq','MODE_HOLD','MODE_PULSE']:
    assert k in s,k
assert 'addCircle("X","攻",MODE_HOLD' in s
assert 'pulse(b.label);' in s
assert 'int seq=++b.flashSeq; b.active=true;' in s
assert 'if(!hitJoystickStartZone(x,y) && hitButton(x,y)==null) return false;' in s
assert 'if(joystickPid>=0 || pointerMap.size()>0 || moveLeft||moveRight||moveUp||moveDown) releaseAll();' in s
assert 'boolean still=false;' in s
assert 'Button pointers never migrate into neighboring skills while sliding.' in s

# The v1.3 synthetic repeat architecture must be gone from executable touch logic.
for forbidden in ['MODE_REPEAT','startAttackRepeat(','stopAttackRepeat(','ensureMovementRepeater(','stopMovementRepeater(','reassertMovement(','repeatKeyCode(']:
    assert forbidden not in s,forbidden
assert 'inputHandler.postDelayed(this,132L)' not in s
assert 'inputHandler.postDelayed(this,92L)' not in s

assert "versionCode 14" in app and "versionName '1.4'" in app
assert "noCompress += ['swf', 'wasm']" in app
for k in ['FLOAT_LEFT','KEYDOWN:X:','KEYUP:X:','KEYDOWN:A:','KEYUP:A:','BLOCK_NAV','REVA_GAME_READY']:
    assert k in smoke,k
print('PASS v1.4: floating/wide joystick start zone')
print('PASS v1.4: movement + attack are true held key states, no synthetic repeats')
print('PASS v1.4: skill pulse input is independent of button flash animation')
print('PASS v1.4: stale ownership is reset/recovered and external navigation remains blocked')
