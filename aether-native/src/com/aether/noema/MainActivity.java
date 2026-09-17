package com.aether.noema;

import android.app.Activity;
import android.os.Bundle;
import android.os.SystemClock;
import android.graphics.*;
import android.graphics.drawable.ColorDrawable;
import android.view.*;
import android.content.*;
import android.hardware.*;
import java.util.Locale;

public class MainActivity extends Activity implements SensorEventListener {
    private SensorManager sensorManager;
    private AetherView view;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        getWindow().setBackgroundDrawable(new ColorDrawable(Color.rgb(5,5,7)));
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        );
        view = new AetherView(this);
        setContentView(view);
        sensorManager = (SensorManager)getSystemService(Context.SENSOR_SERVICE);
    }

    @Override protected void onResume() {
        super.onResume();
        Sensor s = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        if (s != null) sensorManager.registerListener(this, s, SensorManager.SENSOR_DELAY_GAME);
    }

    @Override protected void onPause() {
        super.onPause();
        sensorManager.unregisterListener(this);
    }

    @Override public void onSensorChanged(SensorEvent e) {
        if (view == null) return;
        view.tiltX = clamp(-e.values[0] / SensorManager.GRAVITY_EARTH, -1f, 1f);
        view.tiltY = clamp( e.values[1] / SensorManager.GRAVITY_EARTH, -1f, 1f);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    private static float clamp(float v, float a, float b) {
        return Math.max(a, Math.min(b, v));
    }

    public static class AetherView extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Typeface thin = Typeface.create("sans-serif", Typeface.NORMAL);
        private final Typeface mono = Typeface.create("monospace", Typeface.NORMAL);
        private final long born = SystemClock.uptimeMillis();

        private final int INK = Color.rgb(5,5,7);
        private final int ICE = Color.rgb(200,247,255);
        private final int ELECTRIC = Color.rgb(123,140,255);
        private final int VIOLET = Color.rgb(196,155,255);
        private final int SILVER = Color.rgb(232,231,226);
        private final int MUTED = Color.rgb(112,123,142);

        public float tiltX = 0f, tiltY = 0f;
        private int mode = 0;
        private int serial = 27;
        private long pulseAt = -5000;

        public AetherView(Context c) {
            super(c);
            setBackgroundColor(INK);
            setLayerType(View.LAYER_TYPE_HARDWARE, null);
            setFocusable(true);
        }

        private float dp(float v) { return v * getResources().getDisplayMetrics().density; }
        private float sp(float v) { return v * getResources().getDisplayMetrics().scaledDensity; }
        private static float sat(float v) { return Math.max(0f, Math.min(1f, v)); }
        private int a(int color, float alpha) { return (Math.round(255f*sat(alpha))<<24) | (color & 0x00FFFFFF); }
        private float ease(float x) {
            x = sat(x);
            return x*x*(3f-2f*x);
        }

        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            long now = SystemClock.uptimeMillis();
            float elapsed = now - born;
            if (elapsed < 2950f) drawBoot(c, ease(elapsed / 2680f));
            else drawMain(c, ((elapsed - 2950f) % 14000f) / 14000f, now);
            postInvalidateOnAnimation();
        }

        private void resetPaint() {
            p.setShader(null);
            p.setStyle(Paint.Style.FILL);
            p.setStrokeWidth(1f);
            p.setStrokeCap(Paint.Cap.BUTT);
            p.setColor(Color.WHITE);
            p.setAlpha(255);
        }

        private void drawBoot(Canvas c, float v) {
            int w=getWidth(), h=getHeight();
            float cx=w*.5f, cy=h*.46f, short=Math.min(w,h);
            c.drawColor(INK);

            p.setShader(new RadialGradient(cx,cy,short*.72f,
                new int[]{a(ELECTRIC,.13f*v), Color.TRANSPARENT},
                new float[]{0f,1f}, Shader.TileMode.CLAMP));
            c.drawRect(0,0,w,h,p);
            resetPaint();

            p.setStrokeWidth(dp(.55f));
            for(int i=0;i<30;i++){
                float x=w*i/29f;
                float al=(.015f+.035f*Math.max(0,Math.sin(i*.73+v*5)))*v;
                p.setColor(a(ICE,al));
                c.drawLine(x,h*.28f,x,h*.68f,p);
            }

            float beam=w*.66f*v;
            p.setShader(new LinearGradient(cx-beam/2,cy,cx+beam/2,cy,
                new int[]{Color.TRANSPARENT,a(ICE,.78f),a(VIOLET,.58f),Color.TRANSPARENT},
                null,Shader.TileMode.CLAMP));
            p.setStrokeWidth(dp(.8f));
            c.drawLine(cx-beam/2,cy,cx+beam/2,cy,p);
            resetPaint();

            float base=dp(18)+short*.095f*v;
            int[] colors={ICE,ELECTRIC,VIOLET,ICE};
            p.setStyle(Paint.Style.STROKE);
            for(int i=0;i<4;i++){
                p.setStrokeWidth(dp(i==0?1.0f:.55f));
                p.setColor(a(colors[i],(.24f-i*.035f)*v));
                c.drawCircle(cx,cy,base+dp(11)*i,p);
            }

            for(int i=0;i<72;i++){
                float ang=(float)(i/72.0*Math.PI*2);
                float n=.5f+.5f*(float)Math.sin(i*1.83+v*9);
                float r1=base+dp(31), r2=r1+dp(3+12*n);
                p.setColor(a(ICE,.035f+n*.1f*v));
                p.setStrokeWidth(dp(.5f));
                c.drawLine(cx+(float)Math.cos(ang)*r1,cy+(float)Math.sin(ang)*r1,
                           cx+(float)Math.cos(ang)*r2,cy+(float)Math.sin(ang)*r2,p);
            }
            resetPaint();

            p.setShader(new RadialGradient(cx-dp(6),cy-dp(8),dp(38),
                new int[]{a(Color.WHITE,.85f*v),a(ICE,.28f*v),a(ELECTRIC,.06f*v),Color.TRANSPARENT},
                new float[]{0,.23f,.62f,1f},Shader.TileMode.CLAMP));
            c.drawCircle(cx,cy,dp(38),p);
            resetPaint();

            text.setTypeface(thin);
            text.setTextAlign(Paint.Align.CENTER);
            text.setColor(a(SILVER,Math.min(1f,v*1.5f)));
            text.setTextSize(sp(18));
            c.drawText("A E T H E R",cx,cy+dp(112),text);

            text.setTypeface(mono);
            text.setColor(a(MUTED,Math.min(1f,v*1.5f)));
            text.setTextSize(sp(7.5f));
            c.drawText("SYNTHETIC OBSERVATORY / NODE 01",cx,cy+dp(136),text);

            float y=h-dp(43), left=w*.18f, right=w*.78f;
            p.setStrokeWidth(dp(.7f)); p.setColor(a(Color.WHITE,.09f));
            c.drawLine(left,y,right,y,p);
            p.setShader(new LinearGradient(left,y,left+(right-left)*v,y,
                new int[]{ICE,VIOLET},null,Shader.TileMode.CLAMP));
            p.setStrokeWidth(dp(1f));
            c.drawLine(left,y,left+(right-left)*v,y,p);
            resetPaint();
            text.setTextAlign(Paint.Align.LEFT); text.setTypeface(mono); text.setTextSize(sp(7));
            text.setColor(MUTED);
            c.drawText(String.format(Locale.US,"%03d%%",(int)(v*100)),right+dp(10),y+dp(2),text);
        }

        private void drawMain(Canvas c, float t, long now) {
            int w=getWidth(), h=getHeight();
            float cx=w*(.5f+tiltX*.018f);
            float cy=h*(.46f+tiltY*.012f);
            float short=Math.min(w,h);
            int[] pal = mode==2 ? new int[]{VIOLET,Color.rgb(99,127,224),SILVER} : new int[]{ICE,ELECTRIC,VIOLET};

            c.drawColor(INK);
            p.setShader(new LinearGradient(0,0,0,h,
                new int[]{Color.rgb(7,8,11),INK,Color.rgb(4,4,6)},null,Shader.TileMode.CLAMP));
            c.drawRect(0,0,w,h,p);

            p.setShader(new RadialGradient(cx+w*.20f,cy-h*.12f,short*.86f,
                new int[]{a(pal[1],.12f),Color.TRANSPARENT},null,Shader.TileMode.CLAMP));
            c.drawCircle(cx+w*.20f,cy-h*.12f,short*.86f,p);
            p.setShader(new RadialGradient(cx-w*.26f,cy+h*.18f,short*.72f,
                new int[]{a(pal[0],.075f),Color.TRANSPARENT},null,Shader.TileMode.CLAMP));
            c.drawCircle(cx-w*.26f,cy+h*.18f,short*.72f,p);
            resetPaint();

            for(int i=0;i<80;i++){
                double seed=i*12.9898;
                float px=(float)((Math.sin(seed)*43758.5453)%1.0); if(px<0)px+=1;
                float py=(float)((Math.cos(seed*1.77)*24634.6345)%1.0); if(py<0)py+=1;
                float drift=(float)Math.sin(t*Math.PI*2+i*.37)*dp(2);
                p.setColor(a(pal[i%3],.05f+(i%5)*.012f));
                c.drawCircle(px*w+tiltX*(i%7)*dp(.4f),py*h+drift,dp(i%9==0?.8f:.42f),p);
            }

            drawHeader(c,t,mode,w);
            drawMetrics(c,t,w,h,pal);

            float coreCx=w*.5f+tiltX*dp(8), coreCy=h*.49f+tiltY*dp(6);
            drawCore(c,t,now,coreCx,coreCy,Math.min(w,h)*.265f,pal);

            text.setTypeface(mono); text.setTextAlign(Paint.Align.CENTER); text.setTextSize(sp(6.5f));
            text.setColor(a(MUTED,.78f));
            c.drawText("TOUCH TO COLLAPSE PHASE",coreCx,coreCy+Math.min(w,h)*.205f,text);

            drawDock(c,w,h,pal);
        }

        private void drawHeader(Canvas c,float t,int mode,int w){
            float x=dp(22), y=dp(38), hh=dp(52), r=dp(17);
            p.setColor(a(Color.rgb(11,13,18),.80f));
            c.drawRoundRect(x,y,w-x,y+hh,r,r,p);
            p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(.6f)); p.setColor(a(Color.WHITE,.09f));
            c.drawRoundRect(x,y,w-x,y+hh,r,r,p); resetPaint();

            p.setColor(a(ICE,.92f)); c.drawCircle(x+dp(16),y+hh/2,dp(3.2f),p);

            text.setTextAlign(Paint.Align.LEFT); text.setTypeface(thin); text.setTextSize(sp(9)); text.setColor(SILVER);
            c.drawText("AETHER / "+new String[]{"FIELD","TRACE","VEIL"}[mode],x+dp(30),y+dp(22),text);
            text.setTypeface(mono); text.setTextSize(sp(6)); text.setColor(MUTED);
            c.drawText("LOCAL SYNTHETIC OBSERVATORY",x+dp(30),y+dp(36),text);

            text.setTextAlign(Paint.Align.RIGHT); text.setTextSize(sp(6.5f)); text.setColor(a(ICE,.68f));
            c.drawText(((int)(72+8*Math.sin(t*Math.PI*2)))+" fps",w-x-dp(12),y+dp(29),text);
        }

        private void drawMetrics(Canvas c,float t,int w,int h,int[] pal){
            float y=dp(119);
            drawMetric(c,dp(23),y,"PHASE LOCK",String.format(Locale.US,"%.4f",.9927+Math.sin(t*Math.PI*2)*.0031),ICE,false);
            drawMetric(c,w-dp(23),y,"SYNTHETIC BAND",String.format(Locale.US,"%.2f THz",12.42+Math.cos(t*Math.PI*4)*.17),VIOLET,true);

            float by=h-dp(118);
            drawMetric(c,dp(23),by,"ENTROPY",String.format(Locale.US,"%.5f",.03141+Math.sin(t*Math.PI*8)*.004),ELECTRIC,false);

            text.setTextAlign(Paint.Align.RIGHT); text.setTypeface(mono); text.setTextSize(sp(6)); text.setColor(MUTED);
            c.drawText("STATUS / COHERENT",w-dp(23),by,text);
            p.setColor(ICE); c.drawCircle(w-dp(114),by+dp(16),dp(2.3f),p);
            text.setTextSize(sp(8)); text.setColor(a(SILVER,.88f));
            c.drawText("SYNCHRONIZED",w-dp(23),by+dp(19),text);
        }

        private void drawMetric(Canvas c,float x,float y,String label,String value,int accent,boolean right){
            text.setTypeface(mono); text.setTextSize(sp(6)); text.setColor(MUTED);
            text.setTextAlign(right?Paint.Align.RIGHT:Paint.Align.LEFT);
            c.drawText(label,x,y,text);
            p.setColor(a(accent,.7f)); p.setStrokeWidth(dp(.7f));
            if(right)c.drawLine(x-dp(13),y-dp(2),x-dp(3),y-dp(2),p);
            else c.drawLine(x+dp(3),y+dp(6),x+dp(13),y+dp(6),p);
            text.setTypeface(thin); text.setTextSize(sp(14)); text.setColor(SILVER);
            c.drawText(value,x,y+dp(22),text);
        }

        private void drawCore(Canvas c,float t,long now,float cx,float cy,float r,int[] pal){
            p.setShader(new RadialGradient(cx-r*.20f,cy-r*.24f,r*2f,
                new int[]{a(Color.WHITE,.12f),a(pal[0],.09f),a(pal[1],.035f),Color.TRANSPARENT},
                new float[]{0,.25f,.58f,1f},Shader.TileMode.CLAMP));
            c.drawCircle(cx,cy,r*1.82f,p); resetPaint();

            p.setStyle(Paint.Style.STROKE);
            for(int i=0;i<3;i++){
                p.setStrokeWidth(dp(i==0?1f:.55f));
                p.setColor(a(pal[i],.13f-i*.018f));
                c.drawCircle(cx,cy,r*(.98f+i*.29f),p);
            }

            RectF arc1=new RectF(cx-r*1.34f,cy-r*1.34f,cx+r*1.34f,cy+r*1.34f);
            p.setStrokeWidth(dp(1.5f)); p.setStrokeCap(Paint.Cap.ROUND); p.setColor(a(ICE,.75f));
            c.drawArc(arc1,t*360f,47f,false,p);
            RectF arc2=new RectF(cx-r*1.58f,cy-r*1.58f,cx+r*1.58f,cy+r*1.58f);
            p.setStrokeWidth(dp(.8f)); p.setColor(a(VIOLET,.44f));
            c.drawArc(arc2,-t*263f+126f,83f,false,p);

            for(int i=0;i<96;i++){
                float ang=(float)(i/96.0*Math.PI*2);
                float wave=.45f+.55f*(float)Math.sin(i*1.71+t*Math.PI*8);
                float r1=r*1.55f, r2=r1+dp(2+9*wave);
                p.setStrokeWidth(dp(i%12==0?.75f:.42f)); p.setColor(a(pal[i%3],.028f+wave*.09f));
                c.drawLine(cx+(float)Math.cos(ang)*r1,cy+(float)Math.sin(ang)*r1,
                           cx+(float)Math.cos(ang)*r2,cy+(float)Math.sin(ang)*r2,p);
            }
            resetPaint();

            for(int i=0;i<7;i++){
                float ang=(float)(t*Math.PI*2*(i%2==0?1:-.68)+i*.91);
                float rr=r*(1.05f+(i%3)*.22f);
                float x=cx+(float)Math.cos(ang)*rr, y=cy+(float)Math.sin(ang)*rr;
                p.setShader(new RadialGradient(x,y,dp(7),
                    new int[]{a(pal[i%3],.95f),Color.TRANSPARENT},null,Shader.TileMode.CLAMP));
                c.drawCircle(x,y,dp(7),p); resetPaint();
                p.setColor(a(pal[i%3],.92f)); c.drawCircle(x,y,dp(1),p);
            }

            p.setShader(new RadialGradient(cx-r*.18f,cy-r*.22f,r*.9f,
                new int[]{a(Color.WHITE,.58f),a(ICE,.15f),a(ELECTRIC,.05f),Color.TRANSPARENT},
                new float[]{0,.25f,.62f,1f},Shader.TileMode.CLAMP));
            c.drawCircle(cx,cy,r*.86f,p); resetPaint();

            float pulse=(now-pulseAt)/1000f;
            if(pulse>=0 && pulse<1){
                float e=ease(pulse);
                p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(1.4f)); p.setColor(a(Color.WHITE,(1-e)*.45f));
                c.drawCircle(cx,cy,r*(.72f+e*1.25f),p); resetPaint();
            }

            text.setTextAlign(Paint.Align.CENTER); text.setTypeface(thin); text.setTextSize(sp(31)); text.setColor(SILVER);
            c.drawText(String.format(Locale.US,"Σ.%02d",serial%100),cx,cy+dp(7),text);
            text.setTypeface(mono); text.setTextSize(sp(7)); text.setColor(a(ICE,.62f));
            c.drawText("NOEMA CORE",cx,cy+dp(29),text);
        }

        private void drawDock(Canvas c,int w,int h,int[] pal){
            float x=dp(22), y=h-dp(77), hh=dp(50), r=dp(20);
            p.setColor(a(Color.rgb(9,11,15),.88f)); c.drawRoundRect(x,y,w-x,y+hh,r,r,p);
            p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(.6f)); p.setColor(a(Color.WHITE,.08f));
            c.drawRoundRect(x,y,w-x,y+hh,r,r,p); resetPaint();

            String[] names={"FIELD","TRACE","VEIL"};
            float inner=x+dp(5), seg=(w-2*x-dp(10))/3f;
            for(int i=0;i<3;i++){
                float l=inner+i*seg, rr=l+seg-dp(4);
                if(i==mode){
                    p.setShader(new LinearGradient(l,y,rr,y+hh,
                        new int[]{a(ICE,.11f),a(ELECTRIC,.16f),a(VIOLET,.09f)},null,Shader.TileMode.CLAMP));
                    c.drawRoundRect(l,y+dp(5),rr,y+hh-dp(5),dp(15),dp(15),p); resetPaint();
                }
                text.setTextAlign(Paint.Align.CENTER); text.setTypeface(mono); text.setTextSize(sp(7.5f));
                text.setColor(i==mode?SILVER:MUTED);
                c.drawText(names[i],(l+rr)/2,y+dp(30),text);
            }
        }

        @Override public boolean onTouchEvent(android.view.MotionEvent e) {
            if(e.getAction()!=MotionEvent.ACTION_DOWN)return true;
            float w=getWidth(),h=getHeight();
            float cx=w*.5f+tiltX*dp(8),cy=h*.49f+tiltY*dp(6);
            float dx=e.getX()-cx,dy=e.getY()-cy;
            float core=Math.min(w,h)*.22f;
            if(dx*dx+dy*dy<core*core){
                serial++;
                pulseAt=SystemClock.uptimeMillis();
                performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
                invalidate();
                return true;
            }
            float dockTop=h-dp(82);
            if(e.getY()>dockTop){
                float left=dp(22), usable=w-2*left;
                int m=(int)((e.getX()-left)/(usable/3f));
                mode=Math.max(0,Math.min(2,m));
                performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
                invalidate();
            }
            return true;
        }
    }
}
