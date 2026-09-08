#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/java/com/ajiu/reva/MainActivity.java')
s=p.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('missing needle: '+old[:140].replace('\n','\\n'))
    s=s.replace(old,new,1)

def span(start,end,new):
    global s
    a=s.find(start)
    if a<0: raise SystemExit('missing span start: '+start)
    b=s.find(end,a)
    if b<0: raise SystemExit('missing span end: '+end)
    s=s[:a]+new+s[b:]

# Remove v1.3's synthetic keyboard-repeat bookkeeping. v1.4 models real key state only.
once('''    final Map<Integer,Integer> keyRepeatCounts = new HashMap<>();\n''','')
once('''            keyRepeatCounts.put(code,0);\n''','')
once('''            keyRepeatCounts.remove(code);\n''','')
once('''        keyRepeatCounts.clear();\n''','')
span('''    void repeatKeyCode(int code) {\n''','''    void pulse(String k) {''','''    void pulse(String k) {''')

# A skill release must not manufacture extra direction events.
once('''            pulseReleaseTasks.remove(code);\n            if(controls!=null) controls.reassertMovement();\n''','''            pulseReleaseTasks.remove(code);\n''')

# Touch model: no repeat modes/tasks. Keep only real held keys + momentary skill pulses.
once('''        static final int MODE_PAGE = 3;\n        static final int MODE_REPEAT = 4;\n''','''        static final int MODE_PAGE = 3;\n''')
once('''            boolean active;\n            boolean circle;\n            int mode;\n''','''            boolean active;\n            boolean circle;\n            int flashSeq;\n            int mode;\n''')
once('''        final float joyDesignX=154f, joyDesignY=565f, joyDesignR=105f;\n        float joyX,joyY,joyR,knobX,knobY;\n        int joystickPid=-1;\n        boolean moveLeft,moveRight,moveUp,moveDown;\n        Runnable movementRepeatTask;\n        Runnable attackRepeatTask;\n        B attackButton;\n''','''        final float joyDesignX=154f, joyDesignY=565f, joyDesignR=105f;\n        float joyHomeX,joyHomeY,joyBaseX,joyBaseY,joyR,knobX,knobY;\n        int joystickPid=-1;\n        boolean moveLeft,moveRight,moveUp,moveDown;\n''')
once('''            joyX=px(joyDesignX); joyY=py(joyDesignY); joyR=joyDesignR*sc;\n            knobX=joyX; knobY=joyY;\n''','''            joyHomeX=px(joyDesignX); joyHomeY=py(joyDesignY); joyR=joyDesignR*sc;\n            joyBaseX=joyHomeX; joyBaseY=joyHomeY;\n            knobX=joyHomeX; knobY=joyHomeY;\n''')

# Long-press attack is a genuine X hold again. No artificial 132ms X pulse stream.
once('''            addCircle("X","攻",MODE_REPEAT,0,1205,610,60);\n''','''            addCircle("X","攻",MODE_HOLD,0,1205,610,60);\n''')

# Layout logging keeps the stable home-center so emulator QA can target both fixed and outside-ring starts.
once('''                android.util.Log.i("REVA_TOUCH","JOY:"+(loc[0]+Math.round(joyX))+","+(loc[1]+Math.round(joyY))+","+Math.round(joyR));\n''','''                android.util.Log.i("REVA_TOUCH","JOY:"+(loc[0]+Math.round(joyHomeX))+","+(loc[1]+Math.round(joyHomeY))+","+Math.round(joyR));\n                android.util.Log.i("REVA_TOUCH","JOYZONE:"+(loc[0]+Math.round(px(8)))+","+(loc[1]+Math.round(py(300)))+","+(loc[0]+Math.round(px(430)))+","+(loc[1]+Math.round(py(718))));\n''')

# Draw the active floating base while touched; return to the original home visual when idle.
span('''        void drawJoystick(Canvas c){\n''','''        void drawButton(Canvas c,B b){''','''        void drawJoystick(Canvas c){
            float bx=joystickPid>=0?joyBaseX:joyHomeX;
            float by=joystickPid>=0?joyBaseY:joyHomeY;
            fill.setColor(0x5512171E); c.drawCircle(bx,by,joyR,fill);
            stroke.setStrokeWidth(2.2f*sc); stroke.setColor(0x88D9C99A); c.drawCircle(bx,by,joyR,stroke);
            stroke.setStrokeWidth(3f*sc); stroke.setColor(0x66FFFFFF);
            float nr=joyR*0.72f, ss=8f*sc;
            c.drawLine(bx-nr,by,bx-nr+ss,by,stroke); c.drawLine(bx+nr-ss,by,bx+nr,by,stroke);
            c.drawLine(bx,by-nr,bx,by-nr+ss,stroke); c.drawLine(bx,by+nr-ss,bx,by+nr,stroke);
            fill.setColor(joystickPid>=0?0xD5BCA35F:0xB72A2E36); c.drawCircle(knobX,knobY,46f*sc,fill);
            stroke.setStrokeWidth(2f*sc); stroke.setColor(joystickPid>=0?0xFFF0D78B:0x99FFFFFF); c.drawCircle(knobX,knobY,46f*sc,stroke);
        }

        void drawButton(Canvas c,B b){''')

# Wide lower-left ownership zone + hybrid fixed/floating joystick.
once('''        boolean hitJoystick(float x,float y){ float dx=x-joyX,dy=y-joyY; return dx*dx+dy*dy <= (joyR*1.12f)*(joyR*1.12f); }\n''','''        boolean hitJoystickStartZone(float x,float y){
            return x>=px(8f) && x<=px(430f) && y>=py(300f) && y<=py(718f);
        }
        void beginJoystick(int pid,float x,float y){
            joystickPid=pid;
            float dx=x-joyHomeX,dy=y-joyHomeY;
            float capture=joyR*1.75f;
            if(dx*dx+dy*dy<=capture*capture){
                joyBaseX=joyHomeX; joyBaseY=joyHomeY;
            } else {
                joyBaseX=Math.max(px(92f),Math.min(x,px(335f)));
                joyBaseY=Math.max(py(390f),Math.min(y,py(625f)));
            }
            updateJoystick(x,y);
            android.util.Log.i("REVA_TOUCH","JOY_CLAIM:pid="+pid+":base="+Math.round(joyBaseX)+","+Math.round(joyBaseY)+":touch="+Math.round(x)+","+Math.round(y));
        }
        boolean pointerMappedToButton(int pid){ return pointerMap.get(pid)!=null; }
        boolean pointerExists(MotionEvent e,int pid){ return pid>=0 && e.findPointerIndex(pid)>=0; }
        void recoverJoystickOnMove(MotionEvent e){
            if(joystickPid>=0 && !pointerExists(e,joystickPid)) releaseJoystick();
            if(joystickPid>=0) return;
            for(int i=0;i<e.getPointerCount();i++){
                int pid=e.getPointerId(i);
                if(pointerMappedToButton(pid)) continue;
                float x=e.getX(i),y=e.getY(i);
                if(hitJoystickStartZone(x,y)){ beginJoystick(pid,x,y); return; }
            }
        }
''')

# Replace pointer press/release wholesale: skill visual animation no longer gates input.
span('''        void pressPointer(int pid,float x,float y){\n''','''        void releasePointer(int pid){''','''        void pressPointer(int pid,float x,float y){
            if(joystickPid<0 && hitJoystickStartZone(x,y)) {
                beginJoystick(pid,x,y); performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK); invalidate(); return;
            }
            B b=hitButton(x,y); if(b==null)return;
            pointerMap.put(pid,b);
            if(b.mode==MODE_PAGE){ skillGroup=(skillGroup+1)%skillGroups.length; performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); rebuild(); return; }
            if(b.mode==MODE_PULSE){
                pulse(b.label);
                int seq=++b.flashSeq; b.active=true;
                performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); invalidate();
                postDelayed(()->{ if(b.flashSeq==seq){b.active=false;invalidate();} },82L);
                android.util.Log.i("REVA_TOUCH","PULSE:"+b.label+":pid="+pid+":seq="+seq);
                return;
            }
            if(!b.active){ b.active=true; send(b.label,true); performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); invalidate(); }
            android.util.Log.i("REVA_TOUCH","PRESS:"+b.label+":pid="+pid);
        }

        void releasePointer(int pid){''')
span('''        void releasePointer(int pid){\n''','''        void startAttackRepeat(B b){''','''        void releasePointer(int pid){
            if(pid==joystickPid){ releaseJoystick(); return; }
            B b=pointerMap.get(pid); if(b==null)return;
            pointerMap.remove(pid);
            if(b.mode==MODE_HOLD && b.active){
                boolean still=false;
                for(int i=0;i<pointerMap.size();i++) if(pointerMap.valueAt(i)==b){still=true;break;}
                if(!still){ b.active=false; send(b.label,false); invalidate(); android.util.Log.i("REVA_TOUCH","RELEASE:"+b.label+":pid="+pid); }
            }
            // Pulse buttons release themselves on their fixed timer; visual state is independent.
        }

        void startAttackRepeat(B b){''')

# Delete all v1.3 movement/attack repeat helpers and replace the joystick math.
span('''        void startAttackRepeat(B b){\n''','''        void updateJoystick(float x,float y){''','''        void updateJoystick(float x,float y){''')
span('''        void updateJoystick(float x,float y){\n''','''        void setMoveState(boolean l,boolean r,boolean u,boolean d){''','''        void updateJoystick(float x,float y){
            float dx=x-joyBaseX,dy=y-joyBaseY,dist=(float)Math.hypot(dx,dy);
            // If the thumb travels unusually far, let the floating base follow instead of losing ownership.
            float follow=joyR*1.22f;
            if(dist>follow && dist>0){
                float shift=dist-follow;
                joyBaseX+=dx/dist*shift; joyBaseY+=dy/dist*shift;
                joyBaseX=Math.max(px(92f),Math.min(joyBaseX,px(335f)));
                joyBaseY=Math.max(py(390f),Math.min(joyBaseY,py(625f)));
                dx=x-joyBaseX; dy=y-joyBaseY; dist=(float)Math.hypot(dx,dy);
            }
            float max=joyR*0.68f;
            float kx=dx,ky=dy;
            if(dist>max && dist>0){ kx=dx/dist*max;ky=dy/dist*max; }
            knobX=joyBaseX+kx; knobY=joyBaseY+ky;
            float nx=dx/max,ny=dy/max;
            float dead=0.20f;
            setMoveState(nx<-dead,nx>dead,ny<-dead,ny>dead);
            invalidate();
        }

        void setMoveState(boolean l,boolean r,boolean u,boolean d){''')

# Release means exactly one set of key-ups; no repeater callbacks or synthetic reasserts.
once('''        void releaseJoystick(){\n            joystickPid=-1; stopMovementRepeater(); knobX=joyX;knobY=joyY; setMoveState(false,false,false,false); invalidate();\n        }\n\n        void releaseAll(){\n            releaseJoystick();\n            if(attackButton!=null) stopAttackRepeat(attackButton);\n            for(B b:buttons) if(b.mode==MODE_HOLD && b.active){ b.active=false;send(b.label,false); }\n            pointerMap.clear(); invalidate();\n        }\n''','''        void releaseJoystick(){
            joystickPid=-1;
            setMoveState(false,false,false,false);
            joyBaseX=joyHomeX; joyBaseY=joyHomeY; knobX=joyHomeX; knobY=joyHomeY;
            invalidate();
        }

        void releaseAll(){
            releaseJoystick();
            for(B b:buttons) if(b.mode==MODE_HOLD && b.active){ b.active=false;send(b.label,false); }
            pointerMap.clear(); invalidate();
        }
''')

# Event ownership rewrite. ACTION_DOWN is a new gesture, so stale state is impossible to carry forward.
span('''        @Override public boolean onTouchEvent(MotionEvent e) {\n''','''    }\n\n}''','''        @Override public boolean onTouchEvent(MotionEvent e) {
            int a=e.getActionMasked(), idx=e.getActionIndex();
            if(a==MotionEvent.ACTION_DOWN) {
                // ACTION_DOWN is the first pointer of a new gesture. Any old ownership here is stale by definition.
                if(joystickPid>=0 || pointerMap.size()>0 || moveLeft||moveRight||moveUp||moveDown) releaseAll();
                float x=e.getX(idx),y=e.getY(idx);
                if(!hitJoystickStartZone(x,y) && hitButton(x,y)==null) return false;
                getParent().requestDisallowInterceptTouchEvent(true);
                pressPointer(e.getPointerId(idx),x,y); return true;
            }
            if(a==MotionEvent.ACTION_POINTER_DOWN) {
                recoverJoystickOnMove(e);
                pressPointer(e.getPointerId(idx),e.getX(idx),e.getY(idx));
            }
            else if(a==MotionEvent.ACTION_MOVE) {
                recoverJoystickOnMove(e);
                if(joystickPid>=0){
                    int j=e.findPointerIndex(joystickPid);
                    if(j>=0) updateJoystick(e.getX(j),e.getY(j)); else releaseJoystick();
                }
                // Button pointers never migrate into neighboring skills while sliding.
            }
            else if(a==MotionEvent.ACTION_UP||a==MotionEvent.ACTION_POINTER_UP) {
                releasePointer(e.getPointerId(idx));
            }
            else if(a==MotionEvent.ACTION_CANCEL||a==MotionEvent.ACTION_OUTSIDE) releaseAll();
            return true;
        }
    }

}''')

p.write_text(s)
print('PASS apply_v14: floating joystick + real held movement/attack + pulse visual/input separation')
