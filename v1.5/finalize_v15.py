#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/java/com/ajiu/reva/MainActivity.java')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.5 finalize missing needle: '+old[:180].replace('\n','\\n'))
    s=s.replace(old,new,1)

def span(start,end,new):
    global s
    a=s.find(start)
    if a<0: raise SystemExit('v1.5 finalize missing span start: '+start)
    b=s.find(end,a)
    if b<0: raise SystemExit('v1.5 finalize missing span end: '+end)
    s=s[:a]+new+s[b:]

# ---------------------------------------------------------------------------
# A) Logical input state + black-box trace.
# UI does not directly own backend key state anymore: held inputs first pass
# through a logical de-duplication layer, then dispatch to the selected backend.
# ---------------------------------------------------------------------------
once('''    final Map<Integer,Long> keyDownTimes = new HashMap<>();\n''','''    final Map<Integer,Long> keyDownTimes = new HashMap<>();
    final Map<String,Boolean> logicalKeys = new HashMap<>();
    static final int TRACE_CAPACITY = 384;
    final java.util.ArrayDeque<String> inputTrace = new java.util.ArrayDeque<>();
''')

# Add trace helpers before key mapping.
once('''    void mapKeys() {\n''','''    void traceInput(String msg) {
        String line=SystemClock.uptimeMillis()+":"+msg;
        synchronized(inputTrace) {
            while(inputTrace.size()>=TRACE_CAPACITY) inputTrace.removeFirst();
            inputTrace.addLast(line);
        }
        android.util.Log.i("REVA_TRACE",line);
    }

    void dumpInputTrace() {
        synchronized(inputTrace) {
            android.util.Log.i("REVA_TRACE","--- TRACE DUMP BEGIN ---");
            for(String x:inputTrace) android.util.Log.i("REVA_TRACE",x);
            android.util.Log.i("REVA_TRACE","--- TRACE DUMP END ---");
        }
    }

    void mapKeys() {
''')

# Held controls go through a logical state table. This makes duplicate DOWN/UP
# impossible before the backend even sees the request.
once('''    void send(String k, boolean down) {\n        Integer code = keys.get(k);\n        if(code == null) return;\n        dispatchKeyCode(code, down);\n    }\n''','''    void send(String k, boolean down) {
        Integer code=keys.get(k);
        if(code==null) return;
        boolean old=logicalKeys.getOrDefault(k,false);
        if(old==down) return;
        if(down) logicalKeys.put(k,true); else logicalKeys.remove(k);
        traceInput("LOGICAL:"+(down?"DOWN:":"UP:")+k);
        dispatchKeyCode(code,down);
    }
''')

# Pulse controls are intentionally momentary, but still enter the black box.
once('''    void pulse(String k, long holdMs) {\n''','''    void pulse(String k, long holdMs) {
        traceInput("LOGICAL:PULSE:"+k+":hold="+holdMs);
''')

# Backend records show exactly what was injected into Ruffle / WebView.
once('''        android.util.Log.i("REVA_DOMKEY",(down?"DOWN:":"UP:")+k[1]);\n''','''        android.util.Log.i("REVA_DOMKEY",(down?"DOWN:":"UP:")+k[1]);
        traceInput("BACKEND:DOM:"+(down?"DOWN:":"UP:")+k[1]);
''')
once('''        android.util.Log.i("REVA_INPUT",(down?"DOWN_NATIVE:":"UP_NATIVE:")+code);\n''','''        android.util.Log.i("REVA_INPUT",(down?"DOWN_NATIVE:":"UP_NATIVE:")+code);
        traceInput("BACKEND:NATIVE:"+(down?"DOWN:":"UP:")+code);
''')

# Reset both physical/backend bookkeeping and logical state.
once('''        keyDownTimes.clear();\n        forceDomReleaseAll();\n    }\n''','''        keyDownTimes.clear();
        logicalKeys.clear();
        forceDomReleaseAll();
        traceInput("LOGICAL:RESET_ALL");
    }
''')

# ---------------------------------------------------------------------------
# B) Stable pointer ownership.
# Every finger gets exactly one role at DOWN. MOVE can update that role, but can
# NEVER change it. This removes v1.4's recoverJoystickOnMove() race entirely.
# ---------------------------------------------------------------------------
once('''        final SparseArray<B> pointerMap = new SparseArray<>();\n''','''        final SparseArray<B> pointerMap = new SparseArray<>();
        static final int ROLE_NONE=0, ROLE_JOYSTICK=1, ROLE_BUTTON=2, ROLE_GAME=3, ROLE_BLOCKED=4;
        final SparseArray<Integer> pointerRoles = new SparseArray<>();
        int gameTouchPid=-1;
        long gameTouchDownTime=0L;
''')

# Remove MOVE-time reclamation helpers left by v1.4.
span('''        boolean pointerMappedToButton(int pid){''','''        void pressPointer(int pid,float x,float y){''','''        void pressPointer(int pid,float x,float y){''')

# Insert ownership/router helpers immediately before pressPointer.
once('''        void pressPointer(int pid,float x,float y){\n''','''        int roleOf(int pid){ Integer r=pointerRoles.get(pid); return r==null?ROLE_NONE:r; }
        void role(int pid,int r){ pointerRoles.put(pid,r); traceInput("POINTER:ROLE:pid="+pid+":"+r); }

        void forwardGameTouch(int action,float x,float y,long eventTime){
            if(web==null || gameTouchPid<0) return;
            int[] me=new int[2],wv=new int[2];
            getLocationOnScreen(me); web.getLocationOnScreen(wv);
            float wx=x+me[0]-wv[0], wy=y+me[1]-wv[1];
            long down=gameTouchDownTime>0?gameTouchDownTime:eventTime;
            MotionEvent ev=MotionEvent.obtain(down,eventTime,action,wx,wy,0);
            web.dispatchTouchEvent(ev); ev.recycle();
            traceInput("POINTER:GAME:"+action+":"+Math.round(wx)+","+Math.round(wy));
        }

        void assignPointerRole(MotionEvent e,int idx){
            int pid=e.getPointerId(idx);
            if(roleOf(pid)!=ROLE_NONE) return;
            float x=e.getX(idx),y=e.getY(idx);
            B b=hitButton(x,y);
            if(b!=null){
                role(pid,ROLE_BUTTON);
                pressPointer(pid,x,y);
                return;
            }
            if(joystickPid<0 && hitJoystickStartZone(x,y)){
                role(pid,ROLE_JOYSTICK);
                beginJoystick(pid,x,y);
                performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                invalidate();
                return;
            }
            if(gameTouchPid<0){
                role(pid,ROLE_GAME); gameTouchPid=pid; gameTouchDownTime=e.getEventTime();
                forwardGameTouch(MotionEvent.ACTION_DOWN,x,y,e.getEventTime());
            } else {
                // The original Flash UI does not need multi-finger mouse input. Ignore additional
                // non-control fingers rather than letting them contaminate the one WebView gesture.
                role(pid,ROLE_BLOCKED);
            }
        }

        void releasePointerRole(MotionEvent e,int idx){
            int pid=e.getPointerId(idx),r=roleOf(pid);
            float x=e.getX(idx),y=e.getY(idx);
            if(r==ROLE_JOYSTICK){
                if(pid==joystickPid) releaseJoystick();
            } else if(r==ROLE_BUTTON){
                releasePointer(pid);
            } else if(r==ROLE_GAME){
                if(pid==gameTouchPid){
                    forwardGameTouch(MotionEvent.ACTION_UP,x,y,e.getEventTime());
                    gameTouchPid=-1; gameTouchDownTime=0L;
                }
            }
            pointerRoles.remove(pid);
            traceInput("POINTER:UP:pid="+pid+":role="+r);
        }

        void moveOwnedPointers(MotionEvent e){
            for(int i=0;i<e.getPointerCount();i++){
                int pid=e.getPointerId(i),r=roleOf(pid);
                if(r==ROLE_JOYSTICK && pid==joystickPid){
                    updateJoystick(e.getX(i),e.getY(i));
                } else if(r==ROLE_GAME && pid==gameTouchPid){
                    forwardGameTouch(MotionEvent.ACTION_MOVE,e.getX(i),e.getY(i),e.getEventTime());
                }
            }
        }

        void pressPointer(int pid,float x,float y){
''')

# pressPointer is now button-only. It must never claim a joystick by itself.
once('''            if(joystickPid<0 && hitJoystickStartZone(x,y)) {\n                beginJoystick(pid,x,y); performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK); invalidate(); return;\n            }\n''','')

# releaseAll cancels any synthetic mouse stream and clears all role ownership.
span('''        void releaseAll(){\n''','''        @Override protected void onDetachedFromWindow()''','''        void releaseAll(){
            if(gameTouchPid>=0){
                forwardGameTouch(MotionEvent.ACTION_CANCEL,0f,0f,SystemClock.uptimeMillis());
                gameTouchPid=-1; gameTouchDownTime=0L;
            }
            releaseJoystick();
            for(B b:buttons) if(b.mode==MODE_HOLD && b.active){ b.active=false;send(b.label,false); }
            pointerMap.clear(); pointerRoles.clear();
            invalidate();
            traceInput("POINTER:RELEASE_ALL");
        }

        @Override protected void onDetachedFromWindow()''')

# Entire event handler: overlay ALWAYS owns the Android gesture stream and routes
# each pointer explicitly. No return-false split-brain with WebView.
span('''        @Override public boolean onTouchEvent(MotionEvent e) {\n''','''    }\n\n}''','''        @Override public boolean onTouchEvent(MotionEvent e) {
            int a=e.getActionMasked(),idx=e.getActionIndex();
            if(a==MotionEvent.ACTION_DOWN || a==MotionEvent.ACTION_POINTER_DOWN){
                getParent().requestDisallowInterceptTouchEvent(true);
                assignPointerRole(e,idx);
            } else if(a==MotionEvent.ACTION_MOVE){
                moveOwnedPointers(e);
            } else if(a==MotionEvent.ACTION_UP || a==MotionEvent.ACTION_POINTER_UP){
                releasePointerRole(e,idx);
            } else if(a==MotionEvent.ACTION_CANCEL || a==MotionEvent.ACTION_OUTSIDE){
                releaseAll();
            }
            // Always true: this view is the single touch router. ROLE_GAME is forwarded explicitly.
            return true;
        }
    }

}''')

# ---------------------------------------------------------------------------
# C) Tighten joystick start zone now that there is no MOVE-time recovery.
# It remains forgiving around the thumb, but cannot steal arbitrary left-half touches.
# ---------------------------------------------------------------------------
once('''            return x>=px(8f) && x<=px(430f) && y>=py(300f) && y<=py(718f);\n''','''            return x>=px(18f) && x<=px(360f) && y>=py(365f) && y<=py(718f);
''')

# Strong generation invariants.
for forbidden in [
    'recoverJoystickOnMove(','pointerExists(MotionEvent e,int pid)','pointerMappedToButton(',
    'if(!hitJoystickStartZone(x,y) && hitButton(x,y)==null) return false',
    'setMoveState(nx<-dead,nx>dead,ny<-dead,ny>dead)',
    'MODE_REPEAT','startAttackRepeat(','ensureMovementRepeater(','repeatKeyCode('
]:
    if forbidden in s: raise SystemExit('v1.5 final forbidden residue: '+forbidden)
for required in [
    'pointerRoles','ROLE_JOYSTICK','ROLE_GAME','assignPointerRole(','releasePointerRole(',
    'moveOwnedPointers(','Always true: this view is the single touch router',
    'traceInput(','TRACE_CAPACITY','LOGICAL:','BACKEND:',
    'window.dispatchEvent(new KeyboardEvent','setMoveState(l,r,false,false);'
]:
    if required not in s: raise SystemExit('v1.5 final required logic missing: '+required)

p.write_text(s)
print('PASS finalize_v15: single touch router + immutable pointer roles + logical/backend trace')
