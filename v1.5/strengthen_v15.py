#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/java/com/ajiu/reva/MainActivity.java')
s=p.read_text()

def once(old,new):
    global s
    if old not in s: raise SystemExit('strengthen_v15 missing needle: '+old[:180].replace('\n','\\n'))
    s=s.replace(old,new,1)

# With immutable DOWN-time ownership, a generous lower-left joystick start zone is safe:
# a GAME pointer can no longer be stolen later during MOVE. Include the full rendered left edge.
once('''            return x>=px(18f) && x<=px(360f) && y>=py(365f) && y<=py(718f);\n''','''            return x>=px(0f) && x<=px(390f) && y>=py(340f) && y<=py(720f);
''')

# Dedicated in-app multi-pointer stress mode. This exercises the exact TouchControlsView state
# machine with two fingers simultaneously instead of relying only on adb's single-pointer input.
once('''        if(getIntent()!=null && getIntent().getBooleanExtra("qa_input", false)) {\n''','''        if(getIntent()!=null && getIntent().getBooleanExtra("qa_stress", false)) {
            localPlayback=true;
            web.loadUrl(LOCAL_ORIGIN + "qa_input.html");
            controls.postDelayed(() -> controls.runSyntheticStress(0), 2200L);
        } else if(getIntent()!=null && getIntent().getBooleanExtra("qa_input", false)) {
''')

marker='''        @Override public boolean onTouchEvent(MotionEvent e) {\n'''
if marker not in s: raise SystemExit('onTouchEvent marker missing')
helpers=r'''        void qaInject(int action,int actionIndex,int[] ids,float[] xs,float[] ys,long downTime){
            int n=ids.length;
            MotionEvent.PointerProperties[] pp=new MotionEvent.PointerProperties[n];
            MotionEvent.PointerCoords[] pc=new MotionEvent.PointerCoords[n];
            for(int i=0;i<n;i++){
                pp[i]=new MotionEvent.PointerProperties(); pp[i].id=ids[i]; pp[i].toolType=MotionEvent.TOOL_TYPE_FINGER;
                pc[i]=new MotionEvent.PointerCoords(); pc[i].x=xs[i]; pc[i].y=ys[i]; pc[i].pressure=1f; pc[i].size=1f;
            }
            int encoded=action;
            if(action==MotionEvent.ACTION_POINTER_DOWN || action==MotionEvent.ACTION_POINTER_UP)
                encoded |= (actionIndex << MotionEvent.ACTION_POINTER_INDEX_SHIFT);
            long now=SystemClock.uptimeMillis();
            MotionEvent ev=MotionEvent.obtain(downTime,now,encoded,n,pp,pc,0,0,1f,1f,0,0,InputDevice.SOURCE_TOUCHSCREEN,0);
            dispatchTouchEvent(ev); ev.recycle();
        }

        void runSyntheticStress(final int cycle){
            if(cycle>=8){
                releaseAll();
                traceInput("STRESS_DONE:cycles="+cycle);
                android.util.Log.i("REVA_STRESS","PASS_SEQUENCE_DONE:"+cycle);
                return;
            }
            B xb=findByLabel("X"), ab=findByLabel("A");
            if(xb==null || ab==null){ android.util.Log.e("REVA_STRESS","MISSING_BUTTON"); return; }
            final long down=SystemClock.uptimeMillis();
            final float jy=joyHomeY;
            final float lx=joyHomeX-joyR*0.78f, rx=joyHomeX+joyR*0.78f;
            final float xx=xb.r.centerX(), xy=xb.r.centerY(), ax=ab.r.centerX(), ay=ab.r.centerY();
            traceInput("STRESS_CYCLE_START:"+cycle);
            // Finger 0 owns joystick for the whole gesture. Start neutral, then move left.
            qaInject(MotionEvent.ACTION_DOWN,0,new int[]{0},new float[]{joyHomeX},new float[]{jy},down);
            postDelayed(() -> qaInject(MotionEvent.ACTION_MOVE,0,new int[]{0},new float[]{lx},new float[]{jy},down),35L);
            // Finger 1 presses and HOLDS X while finger 0 changes from left to right.
            postDelayed(() -> qaInject(MotionEvent.ACTION_POINTER_DOWN,1,new int[]{0,1},new float[]{lx,xx},new float[]{jy,xy},down),90L);
            postDelayed(() -> qaInject(MotionEvent.ACTION_MOVE,0,new int[]{0,1},new float[]{rx,xx},new float[]{jy,xy},down),210L);
            postDelayed(() -> qaInject(MotionEvent.ACTION_POINTER_UP,1,new int[]{0,1},new float[]{rx,xx},new float[]{jy,xy},down),340L);
            // While joystick remains owned by finger 0, a fresh second finger taps skill A.
            postDelayed(() -> qaInject(MotionEvent.ACTION_POINTER_DOWN,1,new int[]{0,2},new float[]{rx,ax},new float[]{jy,ay},down),390L);
            postDelayed(() -> qaInject(MotionEvent.ACTION_POINTER_UP,1,new int[]{0,2},new float[]{rx,ax},new float[]{jy,ay},down),455L);
            // Finish joystick gesture. No pointer is allowed to change role during any MOVE above.
            postDelayed(() -> qaInject(MotionEvent.ACTION_UP,0,new int[]{0},new float[]{rx},new float[]{jy},down),545L);
            postDelayed(() -> runSyntheticStress(cycle+1),720L);
        }

'''
s=s.replace(marker,helpers+marker,1)

for k in ['qa_stress','runSyntheticStress(','qaInject(','STRESS_DONE','x>=px(0f)','pointerRoles']:
    if k not in s: raise SystemExit('strengthen_v15 required missing: '+k)
if 'recoverJoystickOnMove(' in s: raise SystemExit('dynamic joystick reclaim returned')
p.write_text(s)
print('PASS strengthen_v15: generous immutable joystick zone + 8-cycle two-finger stress harness')
