#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/java/com/ajiu/reva/MainActivity.java')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.5 missing needle: '+old[:160].replace('\n','\\n'))
    s=s.replace(old,new,1)

def span(start,end,new):
    global s
    a=s.find(start)
    if a<0: raise SystemExit('v1.5 missing span start: '+start)
    b=s.find(end,a)
    if b<0: raise SystemExit('v1.5 missing span end: '+end)
    s=s[:a]+new+s[b:]

# ---------------------------------------------------------------------------
# 1) Replace the native Android-KeyEvent bridge for local Ruffle playback.
# Ruffle Web listens to window keydown/keyup. Focus + dispatch happen in the
# SAME JavaScript evaluation, removing the async focus race of v1.3/v1.4.
# Native KeyEvent remains only as fallback for the legacy online page.
# ---------------------------------------------------------------------------
span('''    void dispatchKeyCode(int code, boolean down) {\n''','''    void pulse(String k) {''','''    String[] domKeySpec(int code) {
        if(code>=KeyEvent.KEYCODE_A && code<=KeyEvent.KEYCODE_Z) {
            char upper=(char)('A'+(code-KeyEvent.KEYCODE_A));
            return new String[]{String.valueOf(Character.toLowerCase(upper)),"Key"+upper,"0"};
        }
        if(code>=KeyEvent.KEYCODE_0 && code<=KeyEvent.KEYCODE_9) {
            char d=(char)('0'+(code-KeyEvent.KEYCODE_0));
            return new String[]{String.valueOf(d),"Digit"+d,"0"};
        }
        switch(code) {
            case KeyEvent.KEYCODE_DPAD_LEFT: return new String[]{"ArrowLeft","ArrowLeft","0"};
            case KeyEvent.KEYCODE_DPAD_RIGHT: return new String[]{"ArrowRight","ArrowRight","0"};
            case KeyEvent.KEYCODE_DPAD_UP: return new String[]{"ArrowUp","ArrowUp","0"};
            case KeyEvent.KEYCODE_DPAD_DOWN: return new String[]{"ArrowDown","ArrowDown","0"};
            case KeyEvent.KEYCODE_SPACE: return new String[]{" ","Space","0"};
            case KeyEvent.KEYCODE_SHIFT_LEFT: return new String[]{"Shift","ShiftLeft","1"};
            case KeyEvent.KEYCODE_SHIFT_RIGHT: return new String[]{"Shift","ShiftRight","2"};
            case KeyEvent.KEYCODE_ENTER: return new String[]{"Enter","Enter","0"};
            default: return null;
        }
    }

    String domFocusPrelude() {
        return "var p=document.querySelector('ruffle-player');"
            +"if(p){p.tabIndex=0;p.focus();}"
            +"var c=document.querySelector('ruffle-player canvas,canvas');"
            +"if(c){c.tabIndex=0;c.focus();}";
    }

    void dispatchDomKey(int code, boolean down) {
        if(web==null) return;
        String[] k=domKeySpec(code);
        if(k==null) return;
        String type=down?"keydown":"keyup";
        String js="(function(){try{"+domFocusPrelude()
            +"var ev=new KeyboardEvent("+org.json.JSONObject.quote(type)+",{key:"
            +org.json.JSONObject.quote(k[0])+",code:"+org.json.JSONObject.quote(k[1])
            +",location:"+k[2]+",bubbles:true,cancelable:true,composed:true,repeat:false});"
            +"window.dispatchEvent(ev);"
            +"console.log('REVA_DOMKEY_EVENT:"+(down?"DOWN:":"UP:")+k[1]+"');"
            +"}catch(e){console.error('REVA_DOMKEY_FAIL:'+e);}})()";
        web.evaluateJavascript(js,null);
        android.util.Log.i("REVA_DOMKEY",(down?"DOWN:":"UP:")+k[1]);
    }

    void forceDomReleaseDirections() {
        if(web==null || !localPlayback) return;
        String js="(function(){try{"+domFocusPrelude()
            +"['ArrowLeft','ArrowRight'].forEach(function(c){window.dispatchEvent(new KeyboardEvent('keyup',{key:c,code:c,bubbles:true,cancelable:true,composed:true,repeat:false}));});"
            +"console.log('REVA_DOMKEY_FORCE_DIRECTIONS');"
            +"}catch(e){console.error('REVA_DOMKEY_FORCE_FAIL:'+e);}})()";
        web.evaluateJavascript(js,null);
        android.util.Log.i("REVA_DOMKEY","FORCE_DIRECTIONS_UP");
    }

    void forceDomReleaseAll() {
        if(web==null || !localPlayback) return;
        String js="(function(){try{"+domFocusPrelude()
            +"var a=[['ArrowLeft','ArrowLeft',0],['ArrowRight','ArrowRight',0],['ArrowDown','ArrowDown',0],['ArrowUp','ArrowUp',0],"
            +"['x','KeyX',0],['c','KeyC',0],['z','KeyZ',0],['v','KeyV',0],"
            +"['a','KeyA',0],['s','KeyS',0],['d','KeyD',0],['f','KeyF',0],['g','KeyG',0],['h','KeyH',0],"
            +"['q','KeyQ',0],['w','KeyW',0],['e','KeyE',0],['r','KeyR',0],['t','KeyT',0],['y','KeyY',0],"
            +"[' ','Space',0],['Shift','ShiftLeft',1],['1','Digit1',0],['2','Digit2',0],['3','Digit3',0]];"
            +"a.forEach(function(k){window.dispatchEvent(new KeyboardEvent('keyup',{key:k[0],code:k[1],location:k[2],bubbles:true,cancelable:true,composed:true,repeat:false}));});"
            +"console.log('REVA_DOMKEY_FORCE_ALL');"
            +"}catch(e){console.error('REVA_DOMKEY_FORCE_FAIL:'+e);}})()";
        web.evaluateJavascript(js,null);
        android.util.Log.i("REVA_DOMKEY","FORCE_ALL_UP");
    }

    void dispatchKeyCode(int code, boolean down) {
        if(web==null) return;
        long now=SystemClock.uptimeMillis();
        long downTime=now;
        if(down) {
            if(keyDownTimes.containsKey(code)) return;
            keyDownTimes.put(code,now);
            downTime=now;
        } else {
            Long saved=keyDownTimes.remove(code);
            if(saved!=null) downTime=saved;
            // For local Ruffle playback an extra key-up is safe and preferable to
            // ever leaving Ruffle's internal key state stuck.
            if(saved==null && !localPlayback) return;
        }

        if(localPlayback && domKeySpec(code)!=null) {
            dispatchDomKey(code,down);
            android.util.Log.i("REVA_INPUT",(down?"DOWN_DOM:":"UP_DOM:")+code);
            return;
        }

        // Legacy online fallback only.
        focusGamePlayer();
        KeyEvent ev=new KeyEvent(downTime,now,down?KeyEvent.ACTION_DOWN:KeyEvent.ACTION_UP,code,0);
        ev.setSource(InputDevice.SOURCE_KEYBOARD);
        web.dispatchKeyEvent(ev);
        android.util.Log.i("REVA_INPUT",(down?"DOWN_NATIVE:":"UP_NATIVE:")+code);
    }

''')

# Hard reset must unconditionally clear Ruffle's DOM key state after Java state cleanup.
span('''    void hardResetInputs() {\n''','''    boolean hasBundledGame() {''','''    void hardResetInputs() {
        if(controls!=null) controls.releaseAll();
        if(inputHandler!=null) {
            for(Runnable r:new ArrayList<>(pulseReleaseTasks.values())) inputHandler.removeCallbacks(r);
        }
        pulseReleaseTasks.clear();
        for(Integer code:new ArrayList<>(keyDownTimes.keySet())) dispatchKeyCode(code,false);
        keyDownTimes.clear();
        forceDomReleaseAll();
    }

''')

# ---------------------------------------------------------------------------
# 2) Correct the actual game's semantics: LEFT/RIGHT are movement; DOWN is
# BACKSTEP. The joystick must never synthesize vertical arrows.
# ---------------------------------------------------------------------------
# Add a dedicated backstep button and keep jump/up-attack/grab separate.
once('''            addCircle("V","抓",MODE_PULSE,3,977,646,37);\n\n            float[][] pos={{986,510,34},{1062,478,34},{1144,470,34},{908,548,33},{914,468,33},{982,420,33}};\n''','''            addCircle("V","抓",MODE_PULSE,3,977,646,37);
            addCircle("↓","后",MODE_PULSE,6,914,683,30);

            float[][] pos={{986,510,34},{1062,478,34},{1144,470,34},{908,548,33},{914,468,33},{982,420,33}};
''')

# Log the backstep button bounds for device regression tests.
once('''            B x=findByLabel("X"), a=findByLabel("A");\n''','''            B x=findByLabel("X"), a=findByLabel("A"), back=findByLabel("↓");
''')
once('''                if(a!=null) android.util.Log.i("REVA_TOUCH","ARECT:"+(loc[0]+Math.round(a.r.left))+","+(loc[1]+Math.round(a.r.top))+","+(loc[0]+Math.round(a.r.right))+","+(loc[1]+Math.round(a.r.bottom)));\n''','''                if(a!=null) android.util.Log.i("REVA_TOUCH","ARECT:"+(loc[0]+Math.round(a.r.left))+","+(loc[1]+Math.round(a.r.top))+","+(loc[0]+Math.round(a.r.right))+","+(loc[1]+Math.round(a.r.bottom)));
                if(back!=null) android.util.Log.i("REVA_TOUCH","BACKRECT:"+(loc[0]+Math.round(back.r.left))+","+(loc[1]+Math.round(back.r.top))+","+(loc[0]+Math.round(back.r.right))+","+(loc[1]+Math.round(back.r.bottom)));
''')

# Visually communicate a horizontal control rather than a four-way D-pad.
span('''        void drawJoystick(Canvas c){\n''','''        void drawButton(Canvas c,B b){''','''        void drawJoystick(Canvas c){
            float bx=joystickPid>=0?joyBaseX:joyHomeX;
            float by=joystickPid>=0?joyBaseY:joyHomeY;
            fill.setColor(0x5512171E); c.drawCircle(bx,by,joyR,fill);
            stroke.setStrokeWidth(2.2f*sc); stroke.setColor(0x88D9C99A); c.drawCircle(bx,by,joyR,stroke);
            // Horizontal-only rail: this game uses Down as BACKSTEP, not movement.
            stroke.setStrokeWidth(3f*sc); stroke.setColor(0x66FFFFFF);
            float nr=joyR*0.72f, ss=10f*sc;
            c.drawLine(bx-nr,by,bx-nr+ss,by,stroke);
            c.drawLine(bx+nr-ss,by,bx+nr,by,stroke);
            c.drawLine(bx-joyR*0.38f,by,bx+joyR*0.38f,by,stroke);
            fill.setColor(joystickPid>=0?0xD5BCA35F:0xB72A2E36); c.drawCircle(knobX,knobY,46f*sc,fill);
            stroke.setStrokeWidth(2f*sc); stroke.setColor(joystickPid>=0?0xFFF0D78B:0x99FFFFFF); c.drawCircle(knobX,knobY,46f*sc,stroke);
        }

''')

# Start exactly under the thumb and remain neutral until the user DRAGS.
span('''        void beginJoystick(int pid,float x,float y){\n''','''        boolean pointerMappedToButton(int pid){''','''        void beginJoystick(int pid,float x,float y){
            joystickPid=pid;
            joyBaseX=Math.max(px(92f),Math.min(x,px(335f)));
            joyBaseY=Math.max(py(390f),Math.min(y,py(625f)));
            knobX=joyBaseX; knobY=joyBaseY;
            setMoveState(false,false,false,false);
            invalidate();
            android.util.Log.i("REVA_TOUCH","JOY_CLAIM_NEUTRAL:pid="+pid+":base="+Math.round(joyBaseX)+","+Math.round(joyBaseY)+":touch="+Math.round(x)+","+Math.round(y));
        }
''')

# Horizontal-only joystick with hysteresis. Vertical thumb drift is ignored.
span('''        void updateJoystick(float x,float y){\n''','''        void setMoveState(boolean l,boolean r,boolean u,boolean d){''','''        void updateJoystick(float x,float y){
            float dx=x-joyBaseX;
            float follow=joyR*1.22f;
            if(Math.abs(dx)>follow){
                float excess=Math.abs(dx)-follow;
                joyBaseX+=Math.signum(dx)*excess;
                joyBaseX=Math.max(px(92f),Math.min(joyBaseX,px(335f)));
                dx=x-joyBaseX;
            }
            float max=joyR*0.68f;
            float kx=Math.max(-max,Math.min(max,dx));
            knobX=joyBaseX+kx;
            knobY=joyBaseY;

            float engage=joyR*0.26f;
            float release=joyR*0.12f;
            boolean l=moveLeft, r=moveRight;
            if(l){
                if(dx>-release) l=false;
                if(dx>engage){l=false;r=true;}
            } else if(r){
                if(dx<release) r=false;
                if(dx<-engage){r=false;l=true;}
            } else {
                if(dx<-engage) l=true;
                else if(dx>engage) r=true;
            }
            setMoveState(l,r,false,false);
            invalidate();
        }

''')

# Even if another caller accidentally passes u/d, movement state refuses to emit them.
span('''        void setMoveState(boolean l,boolean r,boolean u,boolean d){\n''','''        void releaseJoystick(){''','''        void setMoveState(boolean l,boolean r,boolean u,boolean d){
            if(l&&r){ l=false; r=false; }
            if(l!=moveLeft){moveLeft=l;send("←",l);}
            if(r!=moveRight){moveRight=r;send("→",r);}
            // Vertical arrows are not movement in this game. Down is a dedicated backstep pulse.
            moveUp=false; moveDown=false;
        }

''')

# Release the Java movement state AND send an unconditional DOM direction key-up pair.
span('''        void releaseJoystick(){\n''','''        void releaseAll(){''','''        void releaseJoystick(){
            joystickPid=-1;
            setMoveState(false,false,false,false);
            forceDomReleaseDirections();
            joyBaseX=joyHomeX; joyBaseY=joyHomeY; knobX=joyHomeX; knobY=joyHomeY;
            invalidate();
        }

''')

# Generation invariants: fail before Gradle if old wrong semantics survive.
for forbidden in [
    'setMoveState(nx<-dead,nx>dead,ny<-dead,ny>dead)',
    'inputHandler.postDelayed(this,92L)','inputHandler.postDelayed(this,132L)',
    'MODE_REPEAT','repeatKeyCode(','reassertMovement('
]:
    if forbidden in s: raise SystemExit('v1.5 forbidden residue: '+forbidden)
for required in [
    'REVA_DOMKEY','dispatchDomKey(','forceDomReleaseDirections(','forceDomReleaseAll(',
    'JOY_CLAIM_NEUTRAL:','addCircle("↓","后",MODE_PULSE',
    'setMoveState(l,r,false,false);','Vertical arrows are not movement in this game'
]:
    if required not in s: raise SystemExit('v1.5 required logic missing: '+required)

p.write_text(s)
print('PASS apply_v15: horizontal-only game semantics + direct DOM keyboard bridge + unconditional releases')
