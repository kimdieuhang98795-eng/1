#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/java/com/ajiu/reva/MainActivity.java')
s=p.read_text()

# Canonicalize the entire pointer-release -> movement-state section in one operation.
# This deliberately erases every v1.3 synthetic attack/movement repeat helper, even if
# an earlier text transform left a duplicated method header behind.
start='        void releasePointer(int pid){'
end='        void setMoveState(boolean l,boolean r,boolean u,boolean d){'
a=s.find(start)
if a<0: raise SystemExit('missing releasePointer start')
b=s.find(end,a)
if b<0: raise SystemExit('missing setMoveState boundary')

canonical='''        void releasePointer(int pid){
            if(pid==joystickPid){ releaseJoystick(); return; }
            B b=pointerMap.get(pid); if(b==null)return;
            pointerMap.remove(pid);
            if(b.mode==MODE_HOLD && b.active){
                boolean still=false;
                for(int i=0;i<pointerMap.size();i++) if(pointerMap.valueAt(i)==b){still=true;break;}
                if(!still){
                    b.active=false;
                    send(b.label,false);
                    invalidate();
                    android.util.Log.i("REVA_TOUCH","RELEASE:"+b.label+":pid="+pid);
                }
            }
            // MODE_PULSE key-up is timer driven. The visual flash never controls whether input is accepted.
        }

        void updateJoystick(float x,float y){
            float dx=x-joyBaseX,dy=y-joyBaseY,dist=(float)Math.hypot(dx,dy);
            // Keep ownership when the thumb moves far: the floating base follows instead of dropping the gesture.
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

'''
s=s[:a]+canonical+s[b:]

# Strong generation-time invariants. Fail before Gradle if any old synthetic architecture survives.
for forbidden in [
    'MODE_REPEAT','startAttackRepeat(','stopAttackRepeat(','ensureMovementRepeater(',
    'stopMovementRepeater(','reassertMovement(','repeatKeyCode(','attackRepeatTask',
    'movementRepeatTask','keyRepeatCounts'
]:
    if forbidden in s:
        raise SystemExit('v1.4 forbidden residue: '+forbidden)

for required in [
    'addCircle("X","攻",MODE_HOLD','hitJoystickStartZone(','beginJoystick(',
    'recoverJoystickOnMove(','JOY_CLAIM:','flashSeq','pulse(b.label);'
]:
    if required not in s:
        raise SystemExit('v1.4 required logic missing: '+required)

if s.count('        void releasePointer(int pid){') != 1:
    raise SystemExit('releasePointer duplicate')
if s.count('        void updateJoystick(float x,float y){') != 1:
    raise SystemExit('updateJoystick duplicate')
if s.count('        void setMoveState(boolean l,boolean r,boolean u,boolean d){') != 1:
    raise SystemExit('setMoveState duplicate')

p.write_text(s)
print('PASS finalize_v14: canonical input section; all synthetic repeat helpers removed')
