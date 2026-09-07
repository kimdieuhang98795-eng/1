#!/usr/bin/env python3
from pathlib import Path
r=Path(__file__).resolve().parents[1]
req=[
 'app/src/main/AndroidManifest.xml',
 'app/src/main/java/com/ajiu/reva/MainActivity.java',
 'app/src/main/java/com/ajiu/reva/Resolver4399.java',
 'app/src/main/java/com/ajiu/reva/DriveConfirmParser.java',
 'app/src/main/java/com/ajiu/reva/SwfInspector.java',
 'app/src/main/java/com/ajiu/reva/ProjectorExtractor.java',
 'app/src/main/java/com/ajiu/reva/OfficialFinalExtractor.java',
 'app/src/main/java/com/ajiu/reva/GamePackageInspector.java',
 'app/src/main/java/com/ajiu/reva/GamePackageConverter.java',
 'app/src/main/java/com/ajiu/reva/SafeSwfInstaller.java',
 'app/src/main/assets/index.html',
 'app/src/main/assets/qa_input.html',
 'app/src/main/assets/qa_ruffle.html',
 'app/src/main/assets/qa_test.swf',
 'app/build.gradle',
 'tools/Resolver4399FixtureTest.java',
 'qa/run_local_qa.sh',
 'tools/emulator_smoke.sh',
 'tools/verify_swf.py',
 'tools/extract_projector.py',
 'tools/extract_official_final.py',
 'tools/compare_swf.py',
]
for f in req:
    p=r/f
    if f.endswith('qa_test.swf'):
        assert p.exists() and p.stat().st_size >= 18, f
    else:
        assert p.exists() and p.stat().st_size > 50, f
qa=(r/'app/src/main/assets/qa_test.swf').read_bytes()
assert qa[:3] == b'FWS' and len(qa) == 18
assert int.from_bytes(qa[4:8], 'little') == len(qa)
s=(r/'app/src/main/java/com/ajiu/reva/MainActivity.java').read_text()
resolver=(r/'app/src/main/java/com/ajiu/reva/Resolver4399.java').read_text()
for k in ['KEYCODE_DPAD_LEFT','KEYCODE_DPAD_RIGHT','KEYCODE_DPAD_UP','KEYCODE_DPAD_DOWN','keyCodeFromString("KEYCODE_"+c)','ONLINE']:
    assert k in s,k
for k in ['"X"','"C"','"Z"','"V"']:
    assert k in s,k
for k in 'ASDFGHQWERTY': assert '"'+k+'"' in s,k
for k in ['ACTION_POINTER_DOWN','ACTION_POINTER_UP','SparseArray<B>','ACTION_OPEN_DOCUMENT','looksLikeSwf','shouldInterceptRequest','application/wasm','LOCAL_ORIGIN','GamePackageConverter.convert','manual-original-package.part']:
    assert k in s,k
for k in ['GAME_4399_ID = "234798"','OFFICIAL_FINAL_ZIP_DRIVE_ID = "0B4rnLgqFctGvbXpYbVN0ZHliN0E"','acquireFromOfficialFinalZip','OfficialFinalExtractor.extractFromZip','smartAcquire()','resolve4399Swf()','probeSwf(','downloadSwfFromDrive','DriveConfirmParser.parse','rememberResponseCookies','inspectSwf(','game_source.txt','Resolver4399.probeCandidates','CookieManager.getInstance().getCookie']:
    assert k in s,k
for k in ['playingPath(','serverJsPath(','webServer(','gamePath(','buildTrueUrl(','probeCandidates(','binaryCandidates(','jifen3.htm','mainload.swf']:
    assert k in resolver,k

# v1.2 touch/input regression guards.
for k in ['MODE_HOLD','MODE_PULSE','MODE_PAGE','hitJoystick','setMoveState(','releaseJoystick(','pulse(','hardResetInputs(','hasBundledGame(','onWindowFocusChanged','lastPulseTimes','pulseReleaseTasks','ARECT:','JOY:']:
    assert k in s,k
assert 'if(!hitJoystick(x,y) && hitButton(x,y)==null) return false' in s
assert 'Deliberately do not migrate skill pointers between buttons while sliding.' in s
assert 'if(keyDownTimes.containsKey(code)) return' in s
assert 'if(last != null && now - last < 110L) return' in s
assert 'if(!hasFocus) hardResetInputs()' in s
assert 'if((local.exists() && looksLikeSwf(local)) || hasBundledGame()) loadLocal(); else loadOnline();' in s

workflow=(r/'.github/workflows/build-apk.yml').read_text()
for k in ['android-actions/setup-android@v4.0.1','platforms;android-35','assembleDebug','upload-artifact','ruffle-nightly-2026_09_05-web-selfhosted.zip','reactivecircus/android-emulator-runner@v2.38.0','api-level: 35','tools/emulator_smoke.sh']:
    assert k in workflow,k
html=(r/'app/src/main/assets/index.html').read_text()
manifest=(r/'app/src/main/AndroidManifest.xml').read_text()
assert "fetch('game.swf'" not in html
assert 'player.ruffle' in html and '__REVA_PLAYER_READY__' in html
assert "allowScriptAccess:'sameDomain'" in html and 'allowScriptAccess:true' not in html
assert "contextMenu:'off'" in html
assert 'qa_input' in s and 'qa_ruffle' in s and 'REVA_JS' in s and 'qa_input.html' in s and 'qa_ruffle.html' in s
assert 'android:largeHeap="true"' in manifest and 'android:hardwareAccelerated="true"' in manifest
assert 'SafeSwfInstaller.replaceVerified' in s and 'SafeSwfInstaller.recover' in s
assert 'aapt" dump badging' in workflow and 'apk-badging.txt' in workflow
smoke=(r/'tools/emulator_smoke.sh').read_text()
for k in ['KEYDOWN:X:','KEYUP:X:','KEYDOWN:A:','KEYUP:A:','PRESS:X','RELEASE:X','PULSE:A','--ez qa_input true','--ez qa_ruffle true','RUFFLE_QA_READY','XRECT:','ARECT:','JOY:']:
    assert k in smoke,k
app=(r/'app/build.gradle').read_text()
assert "versionCode 12" in app and "versionName '1.2'" in app
assert "noCompress += ['swf', 'wasm']" in app
print('PASS: project structure + v1.2 version')
print('PASS: joystick + DNF-mobile-inspired skill arc + two skill pages')
print('PASS: input manager guards: de-dupe, fixed skill pulse, release-all lifecycle')
print('PASS: virtual HTTPS local origin + bundled-game startup path')
print('PASS: 4399 resolver + repair/fallback acquisition chain')
print('PASS: Android 35 cloud build + pinned Ruffle + emulator input regression hooks')

readme=(r/'README.md').read_text()
status=(r/'STATUS.md').read_text()
assert 'GitHub Actions' in readme and '模拟器' in status
assert '修复 / 更换本体' in s
assert '导入 SWF / FINAL.exe / Final.zip' in s and 'GamePackageConverter.convert' in s
assert 'SWF / FINAL.exe / Final.zip' in readme
print('PASS: repair menu + legacy import paths retained')
