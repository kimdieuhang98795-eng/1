package com.aether.noema;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import android.graphics.*;
import android.graphics.drawable.ColorDrawable;
import android.view.*;
import android.content.*;
import android.hardware.*;
import android.opengl.*;
import android.media.*;
import java.nio.*;
import java.util.Locale;

public class MainActivity extends Activity implements SensorEventListener {
    private SensorManager sensorManager;
    private AetherGLView glView;
    private OverlayView overlay;
    private SoundEngine sound;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.BLACK);
        getWindow().setBackgroundDrawable(new ColorDrawable(Color.rgb(2, 2, 3)));
        immersive();

        sound = new SoundEngine();
        android.widget.FrameLayout root = new android.widget.FrameLayout(this);
        glView = new AetherGLView(this);
        overlay = new OverlayView(this, glView);
        root.addView(glView, new android.widget.FrameLayout.LayoutParams(
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(overlay, new android.widget.FrameLayout.LayoutParams(
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
            android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
        setContentView(root);

        sensorManager = (SensorManager)getSystemService(Context.SENSOR_SERVICE);
        glView.postDelayed(new Runnable() {
            @Override public void run() { if (sound != null) sound.playBoot(); }
        }, 150);
    }

    private void immersive() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        );
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) immersive();
    }

    @Override protected void onResume() {
        super.onResume();
        glView.onResume();
        Sensor sensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        if (sensor != null) sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
    }

    @Override protected void onPause() {
        sensorManager.unregisterListener(this);
        if (sound != null) sound.stopCharge();
        glView.onPause();
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (sound != null) {
            sound.releaseAll();
            sound = null;
        }
        super.onDestroy();
    }

    @Override public void onSensorChanged(SensorEvent e) {
        if (e.sensor.getType() != Sensor.TYPE_ACCELEROMETER) return;
        glView.renderer.tiltX = clamp(-e.values[0] / SensorManager.GRAVITY_EARTH, -1f, 1f);
        glView.renderer.tiltY = clamp( e.values[1] / SensorManager.GRAVITY_EARTH, -1f, 1f);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    static float clamp(float v, float a, float b) {
        return Math.max(a, Math.min(b, v));
    }

    void tactileTick(int strength) {
        if (Build.VERSION.SDK_INT >= 26) {
            Vibrator v;
            if (Build.VERSION.SDK_INT >= 31) {
                VibratorManager vm = (VibratorManager)getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
                v = vm.getDefaultVibrator();
            } else {
                v = (Vibrator)getSystemService(Context.VIBRATOR_SERVICE);
            }
            if (v != null && v.hasVibrator()) {
                v.vibrate(VibrationEffect.createOneShot(7 + strength / 20, clampInt(strength, 18, 150)));
            }
        } else {
            glView.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
        }
    }

    void tactileRelease(float energy) {
        Vibrator v;
        if (Build.VERSION.SDK_INT >= 31) {
            VibratorManager vm = (VibratorManager)getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            v = vm.getDefaultVibrator();
        } else {
            v = (Vibrator)getSystemService(Context.VIBRATOR_SERVICE);
        }
        if (v == null || !v.hasVibrator()) return;

        if (Build.VERSION.SDK_INT >= 26) {
            int peak = clampInt((int)(105 + 150 * energy), 110, 255);
            long[] timing = {0, 12, 18, 20, 22, 34};
            int[] amp = {0, 70, 0, Math.min(205, peak), 0, peak};
            v.vibrate(VibrationEffect.createWaveform(timing, amp, -1));
        } else {
            v.vibrate(new long[]{0, 18, 22, 35}, -1);
        }
    }

    static int clampInt(int v, int a, int b) {
        return Math.max(a, Math.min(b, v));
    }


    static final class SoundEngine {
        private static final int SR = 48000;
        private AudioTrack boot;
        private AudioTrack catchTrack;
        private AudioTrack charge;
        private AudioTrack thresholdA;
        private AudioTrack thresholdB;
        private AudioTrack releaseLight;
        private AudioTrack releaseFull;
        private int noiseState = 0x5A17C9E3;

        SoundEngine() {
            boot = makeTrack(synthBoot());
            catchTrack = makeTrack(synthCatch());
            charge = makeTrack(synthCharge());
            thresholdA = makeTrack(synthThreshold(false));
            thresholdB = makeTrack(synthThreshold(true));
            releaseLight = makeTrack(synthRelease(false));
            releaseFull = makeTrack(synthRelease(true));
        }

        void playBoot() { play(boot, 0f, .56f); }

        void catchPress(float pan) {
            play(catchTrack, pan, .68f);
        }

        void startCharge(float pan) {
            play(charge, pan, .42f);
        }

        void stopCharge() {
            stop(charge);
        }

        void threshold(int level, float pan) {
            play(level >= 2 ? thresholdB : thresholdA, pan, level >= 2 ? .62f : .48f);
        }

        void release(float energy, float pan, float speed) {
            stopCharge();
            float gain = .58f + .35f * energy + Math.min(.10f, speed * .025f);
            if (energy > .67f) play(releaseFull, pan, gain);
            else play(releaseLight, pan, gain * (.72f + energy * .32f));
        }

        void releaseAll() {
            AudioTrack[] tracks = {boot, catchTrack, charge, thresholdA, thresholdB, releaseLight, releaseFull};
            for (AudioTrack t : tracks) {
                if (t == null) continue;
                try { t.stop(); } catch (Throwable ignored) {}
                try { t.release(); } catch (Throwable ignored) {}
            }
        }

        private void play(AudioTrack track, float pan, float gain) {
            if (track == null || track.getState() != AudioTrack.STATE_INITIALIZED) return;
            pan = clamp(pan, -1f, 1f);
            gain = clamp(gain, 0f, 1f);
            float left = gain * (pan > 0f ? 1f - pan * .72f : 1f);
            float right = gain * (pan < 0f ? 1f + pan * .72f : 1f);
            try {
                if (track.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) track.stop();
                track.reloadStaticData();
                track.setPlaybackHeadPosition(0);
                track.setStereoVolume(left, right);
                track.play();
            } catch (Throwable ignored) {}
        }

        private void stop(AudioTrack track) {
            if (track == null) return;
            try {
                if (track.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) track.stop();
                track.setPlaybackHeadPosition(0);
            } catch (Throwable ignored) {}
        }

        private AudioTrack makeTrack(short[] pcm) {
            if (pcm == null || pcm.length == 0) return null;
            try {
                AudioAttributes attrs = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build();
                AudioFormat format = new AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(SR)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                    .build();
                AudioTrack t = new AudioTrack.Builder()
                    .setAudioAttributes(attrs)
                    .setAudioFormat(format)
                    .setBufferSizeInBytes(pcm.length * 2)
                    .setTransferMode(AudioTrack.MODE_STATIC)
                    .build();
                t.write(pcm, 0, pcm.length, AudioTrack.WRITE_BLOCKING);
                return t;
            } catch (Throwable ignored) {
                return null;
            }
        }

        private short[] synthBoot() {
            float seconds = 2.45f;
            int frames = (int)(SR * seconds);
            short[] out = new short[frames * 2];
            double phaseSub = 0, phaseAir = 0;
            for (int i = 0; i < frames; i++) {
                float t = i / (float)SR;
                float r = t / seconds;
                float in = smooth01(r / .16f);
                float outEnv = 1f - smooth01((r - .79f) / .21f);
                float env = in * outEnv;
                float f = 31f + 19f * r * r;
                phaseSub += 2.0 * Math.PI * f / SR;
                phaseAir += 2.0 * Math.PI * (176f + 34f * r) / SR;
                float pressure = (float)Math.sin(phaseSub) * (.10f + .09f * r);
                float air = (float)Math.sin(phaseAir) * .025f;
                float seam = pulse(t, .57f, .055f) * ((float)Math.sin(2*Math.PI*880*t) * .11f + noise() * .035f);
                float lock = pulse(t, 1.78f, .11f) * ((float)Math.sin(2*Math.PI*264*t) * .075f);
                put(out, i, softClip((pressure + air + seam + lock) * env));
            }
            return out;
        }

        private short[] synthCatch() {
            float seconds = .16f;
            int frames = (int)(SR * seconds);
            short[] out = new short[frames * 2];
            double p1 = 0, p2 = 0;
            for (int i = 0; i < frames; i++) {
                float t = i / (float)SR;
                float env = (float)Math.exp(-t * 27f);
                p1 += 2.0 * Math.PI * (64f - 22f * t) / SR;
                p2 += 2.0 * Math.PI * (920f - 470f * t) / SR;
                float low = (float)Math.sin(p1) * .56f;
                float metal = (float)Math.sin(p2) * .16f;
                float crack = noise() * (float)Math.exp(-t * 72f) * .15f;
                put(out, i, softClip((low + metal + crack) * env));
            }
            return out;
        }

        private short[] synthCharge() {
            float seconds = 1.24f;
            int frames = (int)(SR * seconds);
            short[] out = new short[frames * 2];
            double sub = 0, mid = 0, tension = 0;
            for (int i = 0; i < frames; i++) {
                float t = i / (float)SR;
                float r = t / seconds;
                float env = smooth01(r / .08f) * (1f - .13f * smooth01((r - .94f) / .06f));
                float fSub = 38f + 31f * r * r;
                float fMid = 156f + 116f * r * r;
                float fT = 412f + 480f * r * r * r;
                sub += 2.0 * Math.PI * fSub / SR;
                mid += 2.0 * Math.PI * fMid / SR;
                tension += 2.0 * Math.PI * fT / SR;
                float beating = .75f + .25f * (float)Math.sin(2*Math.PI*(2.2f + 3.4f*r)*t);
                float x =
                    (float)Math.sin(sub) * (.045f + .16f * r) +
                    (float)Math.sin(mid) * (.018f + .055f * r*r) +
                    (float)Math.sin(tension) * (.008f + .035f * r*r*r);
                x *= beating * env;
                put(out, i, softClip(x));
            }
            return out;
        }

        private short[] synthThreshold(boolean high) {
            float seconds = high ? .19f : .135f;
            int frames = (int)(SR * seconds);
            short[] out = new short[frames * 2];
            double a = 0, b = 0;
            for (int i = 0; i < frames; i++) {
                float t = i / (float)SR;
                float env = (float)Math.exp(-t * (high ? 20f : 30f));
                float f1 = high ? 1240f : 520f;
                float f2 = high ? 420f : 190f;
                a += 2.0 * Math.PI * f1 / SR;
                b += 2.0 * Math.PI * f2 / SR;
                float x = (float)Math.sin(a) * (high ? .16f : .11f)
                        + (float)Math.sin(b) * (high ? .13f : .08f)
                        + noise() * (float)Math.exp(-t*85f) * .045f;
                put(out, i, softClip(x * env));
            }
            return out;
        }

        private short[] synthRelease(boolean full) {
            float seconds = full ? .82f : .34f;
            int frames = (int)(SR * seconds);
            short[] out = new short[frames * 2];
            double sub = 0, body = 0, glass = 0;
            for (int i = 0; i < frames; i++) {
                float t = i / (float)SR;
                float r = t / seconds;
                float fSub = (full ? 78f : 68f) * (1f - .56f * r) + 5f;
                float fBody = (full ? 238f : 205f) * (1f - .20f * r);
                float fGlass = full ? 1460f - 520f * r : 880f - 180f * r;
                sub += 2.0*Math.PI*fSub/SR;
                body += 2.0*Math.PI*fBody/SR;
                glass += 2.0*Math.PI*fGlass/SR;

                float subEnv = (float)Math.exp(-t * (full ? 4.2f : 8.5f));
                float bodyEnv = (float)Math.exp(-t * (full ? 8.0f : 13f));
                float glassEnv = (float)Math.exp(-t * (full ? 6.6f : 12f));
                float crack = noise() * (float)Math.exp(-t * 52f) * (full ? .24f : .12f);
                float whoosh = noise() * smooth01(r/.10f) * (1f-smooth01((r-.48f)/.52f)) * (full ? .045f : .018f);
                float x =
                    (float)Math.sin(sub) * .72f * subEnv +
                    (float)Math.sin(body) * .16f * bodyEnv +
                    (float)Math.sin(glass) * .11f * glassEnv +
                    crack + whoosh;
                if (full) x += pulse(t,.115f,.055f) * (float)Math.sin(2*Math.PI*2670*t) * .095f;
                put(out, i, softClip(x));
            }
            return out;
        }

        private void put(short[] out, int frame, float sample) {
            short s = (short)(clamp(sample, -1f, 1f) * 32767f);
            int j = frame * 2;
            out[j] = s;
            out[j+1] = s;
        }

        private float noise() {
            noiseState ^= noiseState << 13;
            noiseState ^= noiseState >>> 17;
            noiseState ^= noiseState << 5;
            return ((noiseState & 0x7fffffff) / 1073741824f) - 1f;
        }

        private static float smooth01(float x) {
            x = clamp(x, 0f, 1f);
            return x*x*(3f-2f*x);
        }

        private static float pulse(float t, float center, float width) {
            float x = (t-center)/Math.max(.0001f,width);
            return (float)Math.exp(-x*x*3.2f);
        }

        private static float softClip(float x) {
            return (float)Math.tanh(x * 1.25f) * .82f;
        }
    }

    public static class AetherGLView extends GLSurfaceView {
        final AetherRenderer renderer;
        private final MainActivity activity;
        private long downAt = 0;
        private long lastMoveAt = 0;
        private float lastX, lastY;
        private boolean thresholdOne = false;
        private boolean thresholdTwo = false;

        AetherGLView(MainActivity context) {
            super(context);
            activity = context;
            setEGLContextClientVersion(3);
            setEGLConfigChooser(8,8,8,8,16,0);
            renderer = new AetherRenderer();
            setRenderer(renderer);
            setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
            setPreserveEGLContextOnPause(true);
        }

        @Override public boolean onTouchEvent(MotionEvent e) {
            long now = SystemClock.uptimeMillis();
            float x = e.getX(), y = e.getY();

            if (e.getActionMasked() == MotionEvent.ACTION_DOWN) {
                downAt = now;
                lastMoveAt = now;
                lastX = x;
                lastY = y;
                thresholdOne = thresholdTwo = false;
                renderer.onDown(x / Math.max(1f,getWidth()), 1f - y / Math.max(1f,getHeight()));
                float pan = (x / Math.max(1f,getWidth()) - .5f) * 2f;
                if (activity.sound != null) {
                    activity.sound.catchPress(pan);
                    activity.sound.startCharge(pan);
                }
                activity.tactileTick(42);

                final long stamp = downAt;
                postDelayed(new Runnable() {
                    @Override public void run() {
                        if (renderer.pressed && downAt == stamp && !thresholdOne) {
                            thresholdOne = true;
                            if (activity.sound != null) activity.sound.threshold(1, (lastX / Math.max(1f,getWidth()) - .5f) * 2f);
                            activity.tactileTick(62);
                        }
                    }
                }, 440);
                postDelayed(new Runnable() {
                    @Override public void run() {
                        if (renderer.pressed && downAt == stamp && !thresholdTwo) {
                            thresholdTwo = true;
                            if (activity.sound != null) activity.sound.threshold(2, (lastX / Math.max(1f,getWidth()) - .5f) * 2f);
                            activity.tactileTick(108);
                        }
                    }
                }, 900);
                return true;
            }

            if (e.getActionMasked() == MotionEvent.ACTION_MOVE) {
                float dt = Math.max(1f, now - lastMoveAt);
                float vx = (x - lastX) / dt;
                float vy = (y - lastY) / dt;
                renderer.onMove(
                    x / Math.max(1f,getWidth()),
                    1f - y / Math.max(1f,getHeight()),
                    vx, -vy
                );
                lastX = x;
                lastY = y;
                lastMoveAt = now;

                float energy = Math.min(1f, (now - downAt) / 1150f);
                if (!thresholdOne && energy > .38f) {
                    thresholdOne = true;
                    if (activity.sound != null) activity.sound.threshold(1, (x / Math.max(1f,getWidth()) - .5f) * 2f);
                    activity.tactileTick(62);
                }
                if (!thresholdTwo && energy > .78f) {
                    thresholdTwo = true;
                    if (activity.sound != null) activity.sound.threshold(2, (x / Math.max(1f,getWidth()) - .5f) * 2f);
                    activity.tactileTick(105);
                }
                return true;
            }

            if (e.getActionMasked() == MotionEvent.ACTION_UP || e.getActionMasked() == MotionEvent.ACTION_CANCEL) {
                float energy = Math.min(1f, Math.max(0f, (now - downAt) / 1150f));
                float speed = Math.min(8f, (float)Math.hypot(renderer.velocityX, renderer.velocityY));
                renderer.onUp(energy);
                if (activity.sound != null) {
                    if (e.getActionMasked() == MotionEvent.ACTION_UP) {
                        float pan = (x / Math.max(1f,getWidth()) - .5f) * 2f;
                        activity.sound.release(energy, pan, speed);
                    } else {
                        activity.sound.stopCharge();
                    }
                }
                if (e.getActionMasked() == MotionEvent.ACTION_UP) activity.tactileRelease(energy);
                return true;
            }
            return true;
        }
    }

    public static class AetherRenderer implements GLSurfaceView.Renderer {
        volatile float tiltX = 0f, tiltY = 0f;

        private int program = 0;
        private FloatBuffer vertices;
        private int width = 1, height = 1;
        private long start = 0;
        private long releaseAt = -10000;
        private long pressAt = -10000;

        volatile float pointerX = .5f, pointerY = .5f;
        volatile float dragX = 0f, dragY = 0f;
        volatile float velocityX = 0f, velocityY = 0f;
        volatile boolean pressed = false;
        volatile float lastEnergy = 0f;

        private float inertialX = 0f, inertialY = 0f;
        private float inertiaVX = 0f, inertiaVY = 0f;
        private long lastFrame = 0;

        private int uRes, uTime, uPointer, uDrag, uTilt, uPress, uEnergy, uRelease, uVelocity;

        private static final String VS =
            "#version 300 es\n" +
            "layout(location=0) in vec2 aPos;\n" +
            "out vec2 vUv;\n" +
            "void main(){ vUv=aPos*.5+.5; gl_Position=vec4(aPos,0.0,1.0); }\n";

        private static final String FS =
            "#version 300 es\n" +
            "precision highp float;\n" +
            "in vec2 vUv;\n" +
            "out vec4 fragColor;\n" +
            "uniform vec2 uResolution;\n" +
            "uniform float uTime;\n" +
            "uniform vec2 uPointer;\n" +
            "uniform vec2 uDrag;\n" +
            "uniform vec2 uTilt;\n" +
            "uniform float uPress;\n" +
            "uniform float uEnergy;\n" +
            "uniform float uRelease;\n" +
            "uniform vec2 uVelocity;\n" +
            "\n" +
            "float hash21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=vec2(dot(p,p+vec2(45.32))); return fract(p.x*p.y); }\n" +
            "float noise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f); return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x),mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x),f.y); }\n" +
            "float fbm(vec2 p){ float s=0.0,a=.5; mat2 m=mat2(1.63,-1.17,1.17,1.63); for(int i=0;i<4;i++){s+=a*noise(p);p=m*p+vec2(3.1);a*=.48;} return s; }\n" +
            "mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}\n" +
            "float sdRoundBox(vec2 p, vec2 b, float r){vec2 q=abs(p)-b+r;return min(max(q.x,q.y),0.0)+length(max(q,0.0))-r;}\n" +
            "float band(float d,float w){return exp(-abs(d)/w);}\n" +
            "\n" +
            "void main(){\n" +
            "  vec2 frag=vUv*uResolution;\n" +
            "  vec2 p=(frag-.5*uResolution)/uResolution.y;\n" +
            "  float aspect=uResolution.x/uResolution.y;\n" +
            "  float impact=exp(-clamp(uRelease,0.0,1.0)*5.4)*smoothstep(.56,1.0,uEnergy);\n" +
            "  p*=1.0+impact*.048;\n" +
            "  p.x+=sin(p.y*15.0+uTime*11.0)*impact*.0065;\n" +
            "  float boot=smoothstep(.18,1.0,min(1.0,uTime/2.55));\n" +
            "  float unveil=smoothstep(.0,1.0,min(1.0,max(0.0,(uTime-.72)/1.8)));\n" +
            "\n" +
            "  vec3 col=vec3(.006,.007,.009);\n" +
            "  float vig=1.0-smoothstep(.18,1.05,length(vec2(p.x*.72,p.y)));\n" +
            "  col+=vec3(.006,.007,.009)*vig;\n" +
            "\n" +
            "  // One warm optical seam; no neon dashboard language.\n" +
            "  float seam=exp(-abs(p.x)*440.0)*smoothstep(.0,.34,boot)*(1.0-smoothstep(.52,.86,boot));\n" +
            "  col+=vec3(1.0,.84,.61)*seam*.72;\n" +
            "\n" +
            "  vec2 center=vec2(uTilt.x*.018+uDrag.x*.055, uTilt.y*.012+uDrag.y*.038);\n" +
            "  vec2 q=p-center;\n" +
            "  float releaseArc=sin(clamp(uRelease,0.0,1.0)*3.14159265)*(1.0-.28*uRelease);\n" +
            "  float releaseKick=max(releaseArc,impact*.92)*uEnergy;\n" +
            "  float side=sign(q.x+1e-5);\n" +
            "  q.x-=side*releaseKick*.045;\n" +
            "  q.y+=side*releaseKick*.012*sin(q.y*12.0);\n" +
            "  float ang=uDrag.x*.42+uTilt.x*.10+uVelocity.x*.018+side*releaseKick*.075;\n" +
            "  q=rot(ang)*q;\n" +
            "  q.y*=1.0+uPress*.060+uEnergy*.022;\n" +
            "  q.x*=1.0-uPress*.026-uEnergy*.014;\n" +
            "\n" +
            "  float body=sdRoundBox(q,vec2(.235,.335),.105);\n" +
            "  float shell=1.0-smoothstep(-.010,.010,body);\n" +
            "  float rim=band(body,.0046);\n" +
            "  float outer=band(body-.015,.012);\n" +
            "\n" +
            "  // Brushed black-metal substrate.\n" +
            "  float brush=.5+.5*sin((q.y+noise(q*19.0+uTime*.035)*.014)*980.0);\n" +
            "  brush=pow(brush,15.0);\n" +
            "  float cloudy=fbm(q*5.1+vec2(uTime*.018,-uTime*.011));\n" +
            "  vec3 metal=mix(vec3(.012,.014,.017),vec3(.055,.058,.061),clamp(.18+cloudy*.62,0.0,1.0));\n" +
            "  metal+=brush*vec3(.07,.066,.055);\n" +
            "\n" +
            "  // A pseudo-normal creates a real object-like highlight that follows touch/tilt.\n" +
            "  vec2 n2=normalize(vec2(q.x/.235,q.y/.335)+vec2(1e-4));\n" +
            "  vec2 lightDir=normalize(vec2(-.65+.22*uTilt.x,.76+.12*uTilt.y));\n" +
            "  float spec=pow(max(0.0,dot(n2,lightDir)*.5+.5),18.0);\n" +
            "  float fres=pow(clamp(1.0-length(q/vec2(.28,.39))*.72,0.0,1.0),2.0);\n" +
            "  metal+=spec*vec3(.18,.17,.145)*(1.0-uPress*.35);\n" +
            "  metal+=fres*vec3(.015,.017,.021);\n" +
            "\n" +
            "  // Internal liquid glass: only visible through the monolith.\n" +
            "  vec2 lp=q;\n" +
            "  float flow=fbm(lp*7.4+vec2(uTime*.055,-uTime*.038)+uPointer*.8);\n" +
            "  lp+=.023*vec2(sin(flow*6.283+uTime*.42),cos(flow*5.2-uTime*.31));\n" +
            "  float aperture=length(lp/vec2(.145,.218));\n" +
            "  float lens=1.0-smoothstep(.82,1.02,aperture);\n" +
            "  float caust=pow(max(0.0,.5+.5*sin((lp.y+flow*.032)*92.0+uTime*.72)),12.0);\n" +
            "  vec3 glass=vec3(.008,.010,.012);\n" +
            "  glass+=vec3(.09,.085,.072)*caust*(.2+.8*uEnergy);\n" +
            "  glass+=vec3(.035,.041,.044)*(1.0-aperture*.45);\n" +
            "\n" +
            "  float slit=exp(-abs(lp.x+sin(lp.y*5.0+uTime*.21)*.006)*115.0);\n" +
            "  float slitMask=(1.0-smoothstep(.15,.78,abs(lp.y)))*lens;\n" +
            "  float chargeLight=slit*slitMask*(.08+uEnergy*1.65);\n" +
            "  glass+=chargeLight*vec3(1.0,.72,.36);\n" +
            "  float fracture=exp(-abs(q.x)*mix(145.0,38.0,releaseKick))*releaseKick*lens;\n" +
            "  glass+=fracture*vec3(1.0,.78,.48)*1.35;\n" +
            "\n" +
            "  vec3 object=mix(metal,glass,lens*.92);\n" +
            "  object+=rim*vec3(.30,.29,.255)*(.34+.22*spec);\n" +
            "  object+=outer*vec3(.06,.055,.045);\n" +
            "  col=mix(col,object,shell*unveil);\n" +
            "\n" +
            "  // Drag reveals mechanical shear, not a generic glow ring.\n" +
            "  float shear=abs(uVelocity.x)+abs(uVelocity.y);\n" +
            "  float shearLine=band(body+.028+sin(q.y*18.0+uTime*2.0)*.004,.006)*clamp(shear*.22,0.0,.7);\n" +
            "  col+=shearLine*vec3(.66,.61,.52);\n" +
            "\n" +
            "  // Release bends the whole field for a frame, then dies away.\n" +
            "  float rr=length(p-center);\n" +
            "  float wave=band(rr-(.08+uRelease*.62),.010)*(1.0-uRelease);\n" +
            "  col+=wave*vec3(.76,.70,.57)*.46;\n" +
            "  float blackout=(1.0-uRelease)*uRelease*4.0;\n" +
            "  col*=1.0-blackout*.14;\n" +
            "  float pressure=impact*(1.0-smoothstep(.05,.62,rr));\n" +
            "  col*=1.0-pressure*.32;\n" +
            "  col+=vec3(1.0,.77,.46)*impact*exp(-rr*11.0)*.10;\n" +
            "\n" +
            "  // Tiny material grain; not stars or HUD particles.\n" +
            "  float grain=hash21(frag+vec2(floor(uTime*60.0)));\n" +
            "  col+=(grain-.5)*.018;\n" +
            "  col*=mix(.12,1.0,boot);\n" +
            "  col*=.72+.28*vig;\n" +
            "  col=pow(max(col,0.0),vec3(.94));\n" +
            "  fragColor=vec4(col,1.0);\n" +
            "}\n";

        @Override public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl, javax.microedition.khronos.egl.EGLConfig cfg) {
            GLES30.glClearColor(0f,0f,0f,1f);
            program = makeProgram(VS, FS);
            float[] quad = {-1f,-1f, 1f,-1f, -1f,1f, 1f,1f};
            ByteBuffer bb=ByteBuffer.allocateDirect(quad.length*4).order(ByteOrder.nativeOrder());
            vertices=bb.asFloatBuffer(); vertices.put(quad); vertices.position(0);

            uRes=GLES30.glGetUniformLocation(program,"uResolution");
            uTime=GLES30.glGetUniformLocation(program,"uTime");
            uPointer=GLES30.glGetUniformLocation(program,"uPointer");
            uDrag=GLES30.glGetUniformLocation(program,"uDrag");
            uTilt=GLES30.glGetUniformLocation(program,"uTilt");
            uPress=GLES30.glGetUniformLocation(program,"uPress");
            uEnergy=GLES30.glGetUniformLocation(program,"uEnergy");
            uRelease=GLES30.glGetUniformLocation(program,"uRelease");
            uVelocity=GLES30.glGetUniformLocation(program,"uVelocity");
            start=SystemClock.uptimeMillis();
            lastFrame=start;
        }

        @Override public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl, int w, int h) {
            width=Math.max(1,w); height=Math.max(1,h);
            GLES30.glViewport(0,0,width,height);
        }

        @Override public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
            long now=SystemClock.uptimeMillis();
            float dt=Math.min(.05f,Math.max(.001f,(now-lastFrame)/1000f));
            lastFrame=now;

            if (!pressed) {
                inertialX += inertiaVX*dt;
                inertialY += inertiaVY*dt;
                float damp=(float)Math.pow(.045,dt);
                inertiaVX*=damp;
                inertiaVY*=damp;
                inertialX*=.998f;
                inertialY*=.985f;
            } else {
                inertialX=dragX;
                inertialY=dragY;
                inertiaVX=velocityX*5.8f;
                inertiaVY=velocityY*5.8f;
            }
            inertialX=clamp(inertialX,-1.6f,1.6f);
            inertialY=clamp(inertialY,-.9f,.9f);

            float press=pressed?Math.min(1f,(now-pressAt)/180f):0f;
            float energy=pressed?Math.min(1f,(now-pressAt)/1150f):lastEnergy;
            if(!pressed) lastEnergy*=.952f;

            float rel=(now-releaseAt)/1050f;
            if(rel<0f||rel>1f) rel=1f;

            GLES30.glClear(GLES30.GL_COLOR_BUFFER_BIT);
            GLES30.glUseProgram(program);
            GLES30.glUniform2f(uRes,width,height);
            GLES30.glUniform1f(uTime,(now-start)/1000f);
            GLES30.glUniform2f(uPointer,pointerX,pointerY);
            GLES30.glUniform2f(uDrag,inertialX,inertialY);
            GLES30.glUniform2f(uTilt,tiltX,tiltY);
            GLES30.glUniform1f(uPress,press);
            GLES30.glUniform1f(uEnergy,energy);
            GLES30.glUniform1f(uRelease,rel);
            GLES30.glUniform2f(uVelocity,inertiaVX,inertiaVY);

            vertices.position(0);
            GLES30.glEnableVertexAttribArray(0);
            GLES30.glVertexAttribPointer(0,2,GLES30.GL_FLOAT,false,0,vertices);
            GLES30.glDrawArrays(GLES30.GL_TRIANGLE_STRIP,0,4);
            GLES30.glDisableVertexAttribArray(0);
        }

        void onDown(float nx,float ny){
            pointerX=nx; pointerY=ny; pressed=true; pressAt=SystemClock.uptimeMillis();
            dragX=inertialX; dragY=inertialY; velocityX=velocityY=0f; lastEnergy=0f;
        }

        void onMove(float nx,float ny,float vx,float vy){
            pointerX=nx; pointerY=ny;
            dragX += vx*.036f;
            dragY += vy*.030f;
            dragX=clamp(dragX,-1.45f,1.45f);
            dragY=clamp(dragY,-.78f,.78f);
            velocityX=vx; velocityY=vy;
        }

        void onUp(float energy){
            pressed=false;
            lastEnergy=energy;
            releaseAt=SystemClock.uptimeMillis();
            inertiaVX=velocityX*.16f*(.45f+.75f*energy);
            inertiaVY=velocityY*.16f*(.45f+.75f*energy);
        }

        private static int makeProgram(String vs,String fs){
            int v=compile(GLES30.GL_VERTEX_SHADER,vs);
            int f=compile(GLES30.GL_FRAGMENT_SHADER,fs);
            int p=GLES30.glCreateProgram();
            GLES30.glAttachShader(p,v); GLES30.glAttachShader(p,f);
            GLES30.glLinkProgram(p);
            int[] ok=new int[1]; GLES30.glGetProgramiv(p,GLES30.GL_LINK_STATUS,ok,0);
            if(ok[0]==0) throw new RuntimeException("GL link: "+GLES30.glGetProgramInfoLog(p));
            GLES30.glDeleteShader(v); GLES30.glDeleteShader(f);
            return p;
        }

        private static int compile(int type,String src){
            int s=GLES30.glCreateShader(type);
            GLES30.glShaderSource(s,src); GLES30.glCompileShader(s);
            int[] ok=new int[1]; GLES30.glGetShaderiv(s,GLES30.GL_COMPILE_STATUS,ok,0);
            if(ok[0]==0) throw new RuntimeException("GL shader: "+GLES30.glGetShaderInfoLog(s));
            return s;
        }
    }

    public static class OverlayView extends View {
        private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.SUBPIXEL_TEXT_FLAG);
        private final Typeface mono=Typeface.create("monospace",Typeface.NORMAL);
        private final Typeface thin=Typeface.create("sans-serif-light",Typeface.NORMAL);
        private final long born=SystemClock.uptimeMillis();
        private final AetherGLView gl;

        OverlayView(Context c,AetherGLView glView){
            super(c);
            gl=glView;
            setWillNotDraw(false);
            setClickable(false);
        }

        float dp(float v){return v*getResources().getDisplayMetrics().density;}
        float sp(float v){return v*getResources().getDisplayMetrics().scaledDensity;}

        @Override protected void onDraw(Canvas c){
            super.onDraw(c);
            long now=SystemClock.uptimeMillis();
            float t=(now-born)/1000f;

            float intro=clamp((t-1.65f)/.75f,0f,1f);
            float hint=1f-clamp((t-5.8f)/1.5f,0f,1f);

            // Sparse identity only. No fake telemetry.
            p.setTextAlign(Paint.Align.LEFT);
            p.setTypeface(mono);
            p.setTextSize(sp(6.2f));
            p.setColor(Color.argb((int)(150*intro),205,207,202));
            c.drawText("AETHER / NOEMA-03",dp(21),dp(42),p);

            p.setTextAlign(Paint.Align.RIGHT);
            p.setTextSize(sp(5.5f));
            p.setColor(Color.argb((int)(92*intro),160,161,156));
            c.drawText("OPTICAL SUBSTRATE",getWidth()-dp(21),dp(42),p);

            p.setTextAlign(Paint.Align.CENTER);
            p.setTypeface(thin);
            p.setTextSize(sp(8f));
            p.setColor(Color.argb((int)(130*intro*hint),210,209,201));
            c.drawText("HOLD  ·  DRAG  ·  RELEASE",getWidth()/2f,getHeight()-dp(42),p);

            // Energy marker appears only while pressing.
            if(gl.renderer.pressed){
                float energy=Math.min(1f,(now-gl.renderer.pressAt)/1150f);
                float y=getHeight()-dp(67);
                float left=getWidth()*.34f,right=getWidth()*.66f;
                p.setStrokeWidth(dp(.65f));
                p.setColor(Color.argb(38,230,230,221));
                c.drawLine(left,y,right,y,p);
                p.setColor(Color.argb((int)(70+150*energy),255,191,112));
                c.drawLine(left,y,left+(right-left)*energy,y,p);
            }

            invalidate();
        }
    }
}
