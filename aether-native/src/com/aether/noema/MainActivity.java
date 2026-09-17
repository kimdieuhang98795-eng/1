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
        getWindow().setBackgroundDrawable(new ColorDrawable(Color.rgb(4, 5, 7)));
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

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            );
        }
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
        if (view == null || e.sensor.getType() != Sensor.TYPE_ACCELEROMETER) return;
        view.tiltX = clamp(-e.values[0] / SensorManager.GRAVITY_EARTH, -1f, 1f);
        view.tiltY = clamp( e.values[1] / SensorManager.GRAVITY_EARTH, -1f, 1f);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    private static float clamp(float v, float a, float b) {
        return Math.max(a, Math.min(b, v));
    }

    public static class AetherView extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.DITHER_FLAG);
        private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Typeface display = Typeface.create("sans-serif-light", Typeface.NORMAL);
        private final Typeface ui = Typeface.create("sans-serif-medium", Typeface.NORMAL);
        private final Typeface mono = Typeface.create("monospace", Typeface.NORMAL);
        private final long born = SystemClock.uptimeMillis();

        private final int INK = Color.rgb(4, 5, 7);
        private final int SILVER = Color.rgb(237, 238, 235);
        private final int MUTED = Color.rgb(105, 116, 133);

        private final int[][] PALETTES = {
            { Color.rgb(200, 247, 255), Color.rgb(112, 137, 255), Color.rgb(194, 157, 255) },
            { Color.rgb(226, 247, 255), Color.rgb(91, 192, 255), Color.rgb(113, 255, 224) },
            { Color.rgb(226, 214, 255), Color.rgb(169, 118, 255), Color.rgb(105, 136, 255) }
        };

        public float tiltX = 0f, tiltY = 0f;

        private int mode = 0;
        private int previousMode = 0;
        private long modeChangedAt = -5000;
        private int serial = 27;

        private long pulseAt = -5000;
        private long touchDownAt = 0;
        private float touchStartX, touchStartY, lastTouchX, lastTouchY;
        private boolean touchDown = false;
        private boolean dragGesture = false;
        private float manualYaw = 0f;
        private float manualPitch = 0f;

        private final Bitmap noiseBitmap;
        private final BitmapShader noiseShader;

        public AetherView(Context c) {
            super(c);
            setBackgroundColor(INK);
            setLayerType(View.LAYER_TYPE_HARDWARE, null);
            setFocusable(true);

            noiseBitmap = Bitmap.createBitmap(96, 96, Bitmap.Config.ARGB_8888);
            int[] px = new int[96 * 96];
            long seed = 0xA37F21L;
            for (int i = 0; i < px.length; i++) {
                seed ^= (seed << 13);
                seed ^= (seed >>> 7);
                seed ^= (seed << 17);
                int n = (int)(seed & 0xFF);
                int alpha = 3 + (n % 10);
                int grey = 175 + (n % 42);
                px[i] = Color.argb(alpha, grey, grey + (n % 4), 255);
            }
            noiseBitmap.setPixels(px, 0, 96, 0, 0, 96, 96);
            noiseShader = new BitmapShader(noiseBitmap, Shader.TileMode.REPEAT, Shader.TileMode.REPEAT);
        }

        private float dp(float v) { return v * getResources().getDisplayMetrics().density; }
        private float sp(float v) { return v * getResources().getDisplayMetrics().scaledDensity; }
        private static float sat(float v) { return Math.max(0f, Math.min(1f, v)); }
        private static float ease(float x) { x = sat(x); return x * x * (3f - 2f * x); }
        private static float easeOut(float x) { x = sat(x); float y = 1f - x; return 1f - y * y * y; }
        private static float remap(float v, float a, float b) { return sat((v - a) / (b - a)); }
        private static float lerp(float a, float b, float t) { return a + (b - a) * t; }

        private int a(int color, float alpha) {
            return (Math.round(255f * sat(alpha)) << 24) | (color & 0x00FFFFFF);
        }

        private int mixColor(int c1, int c2, float t) {
            t = sat(t);
            int r = Math.round(Color.red(c1) + (Color.red(c2) - Color.red(c1)) * t);
            int g = Math.round(Color.green(c1) + (Color.green(c2) - Color.green(c1)) * t);
            int b = Math.round(Color.blue(c1) + (Color.blue(c2) - Color.blue(c1)) * t);
            return Color.rgb(r, g, b);
        }

        private int palette(int index, long now) {
            float blend = ease((now - modeChangedAt) / 520f);
            return mixColor(PALETTES[previousMode][index], PALETTES[mode][index], blend);
        }

        private void resetPaint() {
            p.setShader(null);
            p.setStyle(Paint.Style.FILL);
            p.setStrokeWidth(1f);
            p.setStrokeCap(Paint.Cap.BUTT);
            p.setStrokeJoin(Paint.Join.MITER);
            p.setColor(Color.WHITE);
            p.setAlpha(255);
            p.setPathEffect(null);
        }

        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            long now = SystemClock.uptimeMillis();
            float elapsed = now - born;

            if (elapsed < 3200f) {
                drawBoot(c, elapsed, now);
            } else {
                float t = ((elapsed - 3200f) % 16000f) / 16000f;
                drawMain(c, t, now, elapsed - 3200f);
            }

            if (!touchDown) {
                manualPitch *= .982f;
                manualYaw *= .9975f;
                if (Math.abs(manualPitch) < .01f) manualPitch = 0f;
                if (Math.abs(manualYaw) < .01f) manualYaw = 0f;
            }
            postInvalidateOnAnimation();
        }

        private void drawBoot(Canvas c, float ms, long now) {
            int w = getWidth(), h = getHeight();
            float cx = w * .5f, cy = h * .465f;
            float shortSide = Math.min(w, h);

            float seam = easeOut(remap(ms, 100f, 760f));
            float aperture = ease(remap(ms, 520f, 1480f));
            float field = ease(remap(ms, 980f, 2080f));
            float identity = ease(remap(ms, 1740f, 2550f));
            float resolve = ease(remap(ms, 2460f, 3180f));

            c.drawColor(INK);

            // Optically dark background with barely visible cold bloom.
            p.setShader(new RadialGradient(
                cx, cy, shortSide * .78f,
                new int[]{ a(PALETTES[0][1], .06f * field), a(PALETTES[0][2], .018f * field), Color.TRANSPARENT },
                new float[]{ 0f, .48f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawRect(0, 0, w, h, p);
            resetPaint();

            // A single precision seam appears before the rest of the UI.
            float seamHalf = h * .22f * seam;
            p.setShader(new LinearGradient(
                cx, cy - seamHalf, cx, cy + seamHalf,
                new int[]{ Color.TRANSPARENT, a(SILVER, .55f), a(PALETTES[0][0], .95f), a(SILVER, .48f), Color.TRANSPARENT },
                null, Shader.TileMode.CLAMP
            ));
            p.setStrokeWidth(dp(.75f));
            c.drawLine(cx, cy - seamHalf, cx, cy + seamHalf, p);
            resetPaint();

            // Aperture rails close in from the edges, then settle into the orbital core.
            float rail = w * .39f * aperture;
            p.setShader(new LinearGradient(
                cx - rail, cy, cx + rail, cy,
                new int[]{ Color.TRANSPARENT, a(PALETTES[0][0], .22f), a(SILVER, .72f), a(PALETTES[0][2], .28f), Color.TRANSPARENT },
                null, Shader.TileMode.CLAMP
            ));
            p.setStrokeWidth(dp(.7f));
            c.drawLine(cx - rail, cy, cx + rail, cy, p);
            resetPaint();

            // Interference bands: soft, technical, not a HUD grid.
            p.setStrokeWidth(dp(.42f));
            for (int i = -18; i <= 18; i++) {
                float x = cx + i * dp(9.4f) * aperture;
                float lift = (float)Math.sin(i * .82 + ms * .0042) * dp(3.5f) * field;
                float alpha = (.012f + .048f * (1f - Math.abs(i) / 18f)) * field;
                p.setColor(a(PALETTES[0][0], alpha));
                c.drawLine(x, cy - shortSide * .20f + lift, x, cy + shortSide * .20f - lift, p);
            }

            float r = dp(18f) + shortSide * .132f * aperture;
            drawBootLens(c, cx, cy, r, field, ms);

            // Tiny registration marks suggest a very expensive optical instrument.
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(dp(.55f));
            p.setStrokeCap(Paint.Cap.ROUND);
            p.setColor(a(PALETTES[0][0], .30f * field));
            RectF o = new RectF(cx - r * 1.52f, cy - r * 1.52f, cx + r * 1.52f, cy + r * 1.52f);
            c.drawArc(o, 218f, 22f * field, false, p);
            c.drawArc(o, 38f, 22f * field, false, p);
            resetPaint();

            // Wordmark materializes late. It feels like the system has identified itself,
            // rather than like a conventional splash screen.
            float titleY = cy + dp(126);
            text.setTextAlign(Paint.Align.CENTER);
            text.setTypeface(display);
            text.setTextSize(sp(18f));
            text.setColor(a(SILVER, identity));
            c.drawText("A E T H E R", cx, titleY, text);

            text.setTypeface(mono);
            text.setTextSize(sp(6.5f));
            text.setColor(a(MUTED, identity * .9f));
            c.drawText("OPTICAL SYNTHETIC INSTRUMENT / Σ-01", cx, titleY + dp(23), text);

            // Boot telemetry stays minimal: one line, one resolving state.
            float footerY = h - dp(44);
            float left = w * .18f, right = w * .82f;
            p.setColor(a(SILVER, .07f * identity));
            p.setStrokeWidth(dp(.55f));
            c.drawLine(left, footerY, right, footerY, p);
            p.setShader(new LinearGradient(
                left, footerY, lerp(left, right, identity), footerY,
                new int[]{ a(PALETTES[0][0], .85f), a(PALETTES[0][2], .70f) },
                null, Shader.TileMode.CLAMP
            ));
            p.setStrokeWidth(dp(1.05f));
            c.drawLine(left, footerY, lerp(left, right, identity), footerY, p);
            resetPaint();

            text.setTextAlign(Paint.Align.RIGHT);
            text.setTypeface(mono);
            text.setTextSize(sp(6.4f));
            text.setColor(a(MUTED, identity));
            c.drawText(identity < .94f ? "RESOLVING FIELD" : "FIELD LOCKED", right, footerY - dp(9), text);

            // Optical resolve flash bridges straight into the main instrument.
            if (resolve > 0f) {
                float waveR = shortSide * (.10f + resolve * .78f);
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(dp(1.0f));
                p.setColor(a(PALETTES[0][0], (1f - resolve) * .42f));
                c.drawCircle(cx, cy, waveR, p);
                resetPaint();

                p.setShader(new RadialGradient(
                    cx, cy, shortSide * .42f,
                    new int[]{ a(Color.WHITE, .16f * (1f - Math.abs(resolve - .45f) * 1.9f)), a(PALETTES[0][0], .05f), Color.TRANSPARENT },
                    new float[]{ 0f, .44f, 1f }, Shader.TileMode.CLAMP
                ));
                c.drawCircle(cx, cy, shortSide * .42f, p);
                resetPaint();
            }

            drawNoise(c, w, h, .34f);
            drawVignette(c, w, h, .92f);
        }

        private void drawBootLens(Canvas c, float cx, float cy, float r, float field, float ms) {
            int c0 = PALETTES[0][0], c1 = PALETTES[0][1], c2 = PALETTES[0][2];

            // Volumetric shell.
            p.setShader(new RadialGradient(
                cx - r * .18f, cy - r * .22f, r * 1.72f,
                new int[]{ a(Color.WHITE, .20f * field), a(c0, .12f * field), a(c1, .055f * field), a(c2, .018f * field), Color.TRANSPARENT },
                new float[]{ 0f, .18f, .42f, .68f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawCircle(cx, cy, r * 1.72f, p);
            resetPaint();

            p.setStyle(Paint.Style.STROKE);
            p.setStrokeCap(Paint.Cap.ROUND);
            p.setStrokeWidth(dp(.7f));
            for (int i = 0; i < 4; i++) {
                p.setColor(a(new int[]{c0,c1,c2,c0}[i], (.16f - i * .022f) * field));
                c.drawCircle(cx, cy, r * (1.00f + i * .23f), p);
            }

            RectF orbit = new RectF(cx - r * 1.45f, cy - r * .48f, cx + r * 1.45f, cy + r * .48f);
            c.save();
            c.rotate(24f + (ms * .008f) % 360f, cx, cy);
            p.setStrokeWidth(dp(1.0f));
            p.setColor(a(c0, .34f * field));
            c.drawArc(orbit, 18f, 76f, false, p);
            p.setColor(a(c2, .22f * field));
            c.drawArc(orbit, 202f, 118f, false, p);
            c.restore();

            for (int i = 0; i < 84; i++) {
                float ang = (float)(i / 84.0 * Math.PI * 2.0);
                float wave = .5f + .5f * (float)Math.sin(i * 1.71 + ms * .0055);
                float r1 = r * 1.49f;
                float r2 = r1 + dp(2.5f + wave * 9.5f);
                p.setColor(a(new int[]{c0,c1,c2}[i % 3], (.022f + wave * .085f) * field));
                p.setStrokeWidth(dp(i % 12 == 0 ? .8f : .42f));
                c.drawLine(
                    cx + (float)Math.cos(ang) * r1, cy + (float)Math.sin(ang) * r1,
                    cx + (float)Math.cos(ang) * r2, cy + (float)Math.sin(ang) * r2, p
                );
            }
            resetPaint();

            // A glassy center with asymmetric caustic.
            p.setShader(new RadialGradient(
                cx - r * .22f, cy - r * .29f, r * .86f,
                new int[]{ a(Color.WHITE, .52f * field), a(c0, .14f * field), a(c1, .045f * field), a(INK, .72f * field) },
                new float[]{ 0f, .20f, .56f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawCircle(cx, cy, r * .72f, p);
            resetPaint();

            p.setShader(new LinearGradient(
                cx - r * .55f, cy - r * .55f, cx + r * .18f, cy + r * .34f,
                new int[]{ Color.TRANSPARENT, a(Color.WHITE, .16f * field), Color.TRANSPARENT },
                null, Shader.TileMode.CLAMP
            ));
            c.save();
            c.rotate(-26f, cx, cy);
            c.drawOval(new RectF(cx - r * .40f, cy - r * .69f, cx + r * .40f, cy - r * .11f), p);
            c.restore();
            resetPaint();
        }

        private void drawMain(Canvas c, float t, long now, float sceneAge) {
            int w = getWidth(), h = getHeight();
            int c0 = palette(0, now), c1 = palette(1, now), c2 = palette(2, now);
            float cx = w * (.5f + tiltX * .016f);
            float cy = h * (.486f + tiltY * .010f);
            float shortSide = Math.min(w, h);

            drawBackground(c, w, h, cx, cy, t, c0, c1, c2);
            drawHeader(c, w, t, now, c0, c1, c2);
            drawSpectralScale(c, w, h, t, c0, c1);
            drawFloatingMetrics(c, w, h, t, c0, c1, c2);

            float coreX = cx + tiltX * dp(7f);
            float coreY = cy + tiltY * dp(5f);
            float coreR = shortSide * .238f;
            drawCore(c, t, now, coreX, coreY, coreR, c0, c1, c2);
            drawSweep(c, now, coreX, coreY, coreR, c0, c1);

            text.setTextAlign(Paint.Align.CENTER);
            text.setTypeface(mono);
            text.setTextSize(sp(6.2f));
            text.setColor(a(MUTED, .72f));
            c.drawText("TOUCH / DRAG THE FIELD", coreX, coreY + coreR * 1.39f, text);

            drawDock(c, w, h, now, c0, c1, c2);
            drawNoise(c, w, h, .44f);
            drawVignette(c, w, h, .88f);

            // Seamless main-scene arrival after the custom boot.
            float entry = easeOut(sceneAge / 720f);
            if (entry < 1f) {
                p.setColor(a(INK, 1f - entry));
                c.drawRect(0, 0, w, h, p);
                resetPaint();

                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(dp(1f));
                p.setColor(a(c0, (1f - entry) * .38f));
                c.drawCircle(coreX, coreY, coreR * (.44f + entry * 1.52f), p);
                resetPaint();
            }
        }

        private void drawBackground(Canvas c, int w, int h, float cx, float cy, float t, int c0, int c1, int c2) {
            c.drawColor(INK);

            p.setShader(new LinearGradient(
                0, 0, 0, h,
                new int[]{ Color.rgb(7, 8, 11), INK, Color.rgb(3, 4, 6) },
                new float[]{ 0f, .48f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawRect(0, 0, w, h, p);

            p.setShader(new RadialGradient(
                cx + w * .23f, cy - h * .18f, Math.min(w, h) * .88f,
                new int[]{ a(c1, .105f), a(c2, .028f), Color.TRANSPARENT },
                new float[]{ 0f, .46f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawRect(0, 0, w, h, p);

            p.setShader(new RadialGradient(
                cx - w * .32f, cy + h * .19f, Math.min(w, h) * .72f,
                new int[]{ a(c0, .060f), Color.TRANSPARENT },
                new float[]{ 0f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawRect(0, 0, w, h, p);
            resetPaint();

            // Sparse depth field. Near points respond more to device tilt.
            for (int i = 0; i < 92; i++) {
                double seed = i * 12.9898;
                float px = (float)((Math.sin(seed) * 43758.5453) % 1.0); if (px < 0) px += 1f;
                float py = (float)((Math.cos(seed * 1.77) * 24634.6345) % 1.0); if (py < 0) py += 1f;
                float depth = .22f + (i % 7) / 7f;
                float drift = (float)Math.sin(t * Math.PI * 2f + i * .37f) * dp(2.1f);
                float x = px * w + tiltX * dp(5f) * depth;
                float y = py * h + drift + tiltY * dp(4f) * depth;
                p.setColor(a(new int[]{c0,c1,c2}[i % 3], .025f + depth * .055f));
                c.drawCircle(x, y, dp(i % 11 == 0 ? .78f : .36f), p);
            }

            // Long optical filaments add motion without turning the screen into a dashboard.
            for (int i = 0; i < 4; i++) {
                float y = h * (.68f + i * .026f);
                float shift = (float)Math.sin(t * Math.PI * 2f + i * .8f) * dp(8f);
                p.setShader(new LinearGradient(
                    0, y, w, y,
                    new int[]{ Color.TRANSPARENT, a(new int[]{c0,c1,c2,c0}[i], .058f), Color.TRANSPARENT },
                    new float[]{ 0f, .55f, 1f }, Shader.TileMode.CLAMP
                ));
                p.setStrokeWidth(dp(.45f));
                c.drawLine(0, y + shift, w, y - shift, p);
                resetPaint();
            }
        }

        private void drawHeader(Canvas c, int w, float t, long now, int c0, int c1, int c2) {
            float x = dp(20f), y = dp(30f), right = w - dp(20f), hh = dp(55f), r = dp(18f);

            p.setShader(new LinearGradient(
                x, y, right, y + hh,
                new int[]{ a(Color.rgb(15, 17, 22), .88f), a(Color.rgb(8, 10, 14), .74f) },
                null, Shader.TileMode.CLAMP
            ));
            c.drawRoundRect(x, y, right, y + hh, r, r, p);
            resetPaint();

            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(dp(.58f));
            p.setColor(a(Color.WHITE, .085f));
            c.drawRoundRect(x, y, right, y + hh, r, r, p);
            resetPaint();

            // Small optical slit instead of a generic green "status dot".
            p.setShader(new LinearGradient(
                x + dp(13f), y + hh * .5f, x + dp(24f), y + hh * .5f,
                new int[]{ a(c0, .18f), a(c0, .95f), a(c2, .32f) },
                null, Shader.TileMode.CLAMP
            ));
            p.setStrokeWidth(dp(1.5f));
            p.setStrokeCap(Paint.Cap.ROUND);
            c.drawLine(x + dp(13f), y + hh * .5f, x + dp(24f), y + hh * .5f, p);
            resetPaint();

            text.setTextAlign(Paint.Align.LEFT);
            text.setTypeface(ui);
            text.setTextSize(sp(8.8f));
            text.setColor(a(SILVER, .94f));
            c.drawText("AETHER / " + new String[]{"FIELD","TRACE","VEIL"}[mode], x + dp(34f), y + dp(23f), text);

            text.setTypeface(mono);
            text.setTextSize(sp(5.7f));
            text.setColor(a(MUTED, .90f));
            c.drawText("SYNTHETIC OBSERVATORY   //   NOEMA-Σ", x + dp(34f), y + dp(38f), text);

            text.setTextAlign(Paint.Align.RIGHT);
            text.setTextSize(sp(5.8f));
            text.setColor(a(c0, .62f));
            int fpsLike = (int)(117 + 3 * Math.sin(t * Math.PI * 2f));
            c.drawText(fpsLike + " Hz  /  LOCK", right - dp(13f), y + dp(31f), text);
        }

        private void drawSpectralScale(Canvas c, int w, int h, float t, int c0, int c1) {
            float x = w - dp(17f);
            float top = h * .27f;
            float bottom = h * .67f;

            p.setStrokeWidth(dp(.42f));
            for (int i = 0; i <= 34; i++) {
                float y = lerp(top, bottom, i / 34f);
                float pulse = .5f + .5f * (float)Math.sin(t * Math.PI * 2f * 2f + i * .42f);
                float len = dp(i % 5 == 0 ? 8f : (3f + pulse * 2.5f));
                p.setColor(a(i % 5 == 0 ? c0 : c1, i % 5 == 0 ? .25f : .08f));
                c.drawLine(x - len, y, x, y, p);
            }

            float marker = top + (bottom - top) * (.5f + .44f * (float)Math.sin(t * Math.PI * 2f));
            p.setColor(a(c0, .72f));
            p.setStrokeWidth(dp(1.2f));
            c.drawLine(x - dp(11f), marker, x, marker, p);

            text.setTypeface(mono);
            text.setTextAlign(Paint.Align.RIGHT);
            text.setTextSize(sp(5.1f));
            text.setColor(a(MUTED, .60f));
            c.drawText("λ", x, top - dp(9f), text);
            c.drawText("Σ", x, bottom + dp(13f), text);
        }

        private void drawFloatingMetrics(Canvas c, int w, int h, float t, int c0, int c1, int c2) {
            float top = dp(118f);
            drawMetric(
                c, dp(22f), top,
                "PHASE LOCK", String.format(Locale.US, "Φ %.4f", .9927 + Math.sin(t * Math.PI * 2f) * .0031),
                c0, false
            );
            drawMetric(
                c, w - dp(22f), top,
                "SYNTHETIC BAND", String.format(Locale.US, "%.2f THz", 12.42 + Math.cos(t * Math.PI * 4f) * .17),
                c2, true
            );

            float bottom = h - dp(119f);
            drawMetric(
                c, dp(22f), bottom,
                "ENTROPY VECTOR", String.format(Locale.US, "ΔE %.3f", 31.4 + Math.sin(t * Math.PI * 7f) * 2.1),
                c1, false
            );

            text.setTextAlign(Paint.Align.RIGHT);
            text.setTypeface(mono);
            text.setTextSize(sp(5.5f));
            text.setColor(a(MUTED, .84f));
            c.drawText("STATE / COHERENT", w - dp(22f), bottom, text);

            p.setShader(new RadialGradient(
                w - dp(108f), bottom + dp(17f), dp(4.5f),
                new int[]{ a(c0, .90f), Color.TRANSPARENT },
                null, Shader.TileMode.CLAMP
            ));
            c.drawCircle(w - dp(108f), bottom + dp(17f), dp(4.5f), p);
            resetPaint();

            text.setTextSize(sp(7.3f));
            text.setColor(a(SILVER, .90f));
            c.drawText("SYNCHRONIZED", w - dp(22f), bottom + dp(20f), text);
        }

        private void drawMetric(Canvas c, float x, float y, String label, String value, int accent, boolean right) {
            text.setTextAlign(right ? Paint.Align.RIGHT : Paint.Align.LEFT);
            text.setTypeface(mono);
            text.setTextSize(sp(5.5f));
            text.setColor(a(MUTED, .86f));
            c.drawText(label, x, y, text);

            p.setColor(a(accent, .58f));
            p.setStrokeWidth(dp(.65f));
            if (right) c.drawLine(x - dp(18f), y + dp(7f), x, y + dp(7f), p);
            else c.drawLine(x, y + dp(7f), x + dp(18f), y + dp(7f), p);

            text.setTypeface(display);
            text.setTextSize(sp(13.3f));
            text.setColor(a(SILVER, .96f));
            c.drawText(value, x, y + dp(26f), text);
        }

        private void drawCore(Canvas c, float t, long now, float cx, float cy, float r, int c0, int c1, int c2) {
            float phase = (float)(t * Math.PI * 2.0);
            float pulse = sat((now - pulseAt) / 1120f);

            // Wide energy envelope.
            p.setShader(new RadialGradient(
                cx, cy, r * 2.15f,
                new int[]{ a(c0, .045f), a(c1, .025f), Color.TRANSPARENT },
                new float[]{ 0f, .43f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawCircle(cx, cy, r * 2.15f, p);
            resetPaint();

            // Spectral ribbons: projected paths around the lens.
            for (int ribbon = 0; ribbon < 3; ribbon++) {
                Path path = new Path();
                float rx = r * (1.24f + ribbon * .17f);
                float ry = r * (.37f + ribbon * .07f);
                float rot = new float[]{ -17f, 46f, 112f }[ribbon] + manualYaw * (ribbon + 1) * .18f;
                c.save();
                c.rotate(rot, cx, cy);
                for (int i = 0; i <= 72; i++) {
                    float ang = (float)(i / 72.0 * Math.PI * 2.0);
                    float warp = (float)Math.sin(ang * 3f + phase * (1f + ribbon * .28f)) * r * .025f;
                    float x = cx + (float)Math.cos(ang) * (rx + warp);
                    float y = cy + (float)Math.sin(ang) * ry;
                    if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
                }
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeCap(Paint.Cap.ROUND);
                p.setStrokeWidth(dp(ribbon == 0 ? .72f : .46f));
                p.setShader(new LinearGradient(
                    cx - rx, cy, cx + rx, cy,
                    new int[]{ Color.TRANSPARENT, a(new int[]{c0,c2,c1}[ribbon], .32f), a(SILVER, .15f), Color.TRANSPARENT },
                    new float[]{ 0f, .31f, .66f, 1f }, Shader.TileMode.CLAMP
                ));
                c.drawPath(path, p);
                c.restore();
                resetPaint();
            }

            // Concentric precision shells.
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeCap(Paint.Cap.ROUND);
            float[] shells = { 1.02f, 1.28f, 1.53f };
            int[] shellColors = { c0, c1, c2 };
            for (int i = 0; i < shells.length; i++) {
                p.setStrokeWidth(dp(i == 0 ? .72f : .45f));
                p.setColor(a(shellColors[i], .095f + i * .018f));
                c.drawCircle(cx, cy, r * shells[i], p);
            }

            // Broken arc segments make the geometry feel manufactured rather than decorative.
            RectF outer = new RectF(cx - r * 1.52f, cy - r * 1.52f, cx + r * 1.52f, cy + r * 1.52f);
            p.setStrokeWidth(dp(1.2f));
            p.setColor(a(c0, .69f));
            c.drawArc(outer, t * 360f + manualYaw, 39f, false, p);
            p.setStrokeWidth(dp(.75f));
            p.setColor(a(c2, .42f));
            c.drawArc(outer, -t * 270f - manualYaw * .7f + 131f, 82f, false, p);
            p.setColor(a(c1, .24f));
            c.drawArc(outer, t * 148f + 249f, 26f, false, p);
            resetPaint();

            // Dense micro-ticks around the optical boundary.
            for (int i = 0; i < 120; i++) {
                float ang = (float)(i / 120.0 * Math.PI * 2.0);
                float wave = .5f + .5f * (float)Math.sin(i * 1.59f + phase * 4.4f);
                float r1 = r * 1.56f;
                float r2 = r1 + dp((i % 10 == 0 ? 6.0f : 2.0f) + wave * 4.6f);
                p.setStrokeWidth(dp(i % 10 == 0 ? .68f : .34f));
                p.setColor(a(new int[]{c0,c1,c2}[i % 3], i % 10 == 0 ? .18f : .035f + wave * .045f));
                c.drawLine(
                    cx + (float)Math.cos(ang) * r1, cy + (float)Math.sin(ang) * r1,
                    cx + (float)Math.cos(ang) * r2, cy + (float)Math.sin(ang) * r2, p
                );
            }

            // Main glass lens: several asymmetric gradients create a pseudo-refractive material.
            p.setShader(new RadialGradient(
                cx - r * .25f, cy - r * .31f, r * 1.12f,
                new int[]{
                    a(Color.WHITE, .23f),
                    a(c0, .105f),
                    a(c1, .045f),
                    a(Color.rgb(11, 13, 18), .83f),
                    a(INK, .98f)
                },
                new float[]{ 0f, .20f, .47f, .78f, 1f }, Shader.TileMode.CLAMP
            ));
            c.drawCircle(cx, cy, r * .92f, p);
            resetPaint();

            // Dark inner aperture.
            p.setShader(new RadialGradient(
                cx + r * .13f, cy + r * .12f, r * .69f,
                new int[]{ a(Color.rgb(4,6,9), .24f), a(Color.rgb(2,3,5), .96f) },
                null, Shader.TileMode.CLAMP
            ));
            c.drawCircle(cx, cy, r * .66f, p);
            resetPaint();

            // Iridescent rim.
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(dp(1.12f));
            p.setShader(new SweepGradient(
                cx, cy,
                new int[]{ a(c0,.12f), a(c1,.74f), a(SILVER,.32f), a(c2,.72f), a(c0,.12f) },
                new float[]{ 0f,.24f,.49f,.76f,1f }
            ));
            c.drawCircle(cx, cy, r * .90f, p);
            resetPaint();

            // Lens caustic: rotated, clipped-looking highlights.
            c.save();
            c.rotate(-24f + manualPitch * .22f, cx, cy);
            p.setShader(new LinearGradient(
                cx - r * .46f, cy - r * .66f, cx + r * .23f, cy + r * .31f,
                new int[]{ Color.TRANSPARENT, a(Color.WHITE, .14f), a(c0, .08f), Color.TRANSPARENT },
                new float[]{ 0f,.42f,.61f,1f }, Shader.TileMode.CLAMP
            ));
            c.drawOval(new RectF(cx - r * .45f, cy - r * .78f, cx + r * .47f, cy - r * .14f), p);
            c.restore();
            resetPaint();

            // Inner aperture glyph.
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeCap(Paint.Cap.ROUND);
            p.setStrokeWidth(dp(.58f));
            p.setColor(a(c0, .26f));
            float gr = r * .32f;
            Path glyph = new Path();
            for (int i = 0; i < 6; i++) {
                float ang = (float)(-Math.PI / 2 + i * Math.PI / 3);
                float gx = cx + (float)Math.cos(ang) * gr;
                float gy = cy + (float)Math.sin(ang) * gr;
                if (i == 0) glyph.moveTo(gx, gy); else glyph.lineTo(gx, gy);
            }
            glyph.close();
            c.drawPath(glyph, p);
            resetPaint();

            // Orbiting luminous samples.
            for (int i = 0; i < 9; i++) {
                float ang = phase * (i % 2 == 0 ? 1.0f : -.61f) + i * .73f + manualYaw * .008f;
                float rr = r * (1.04f + (i % 3) * .23f);
                float x = cx + (float)Math.cos(ang) * rr;
                float y = cy + (float)Math.sin(ang) * rr * (.62f + (i % 2) * .15f);
                int cc = new int[]{c0,c1,c2}[i % 3];
                p.setShader(new RadialGradient(
                    x, y, dp(7f),
                    new int[]{ a(cc, .95f), a(cc, .13f), Color.TRANSPARENT },
                    new float[]{ 0f,.26f,1f }, Shader.TileMode.CLAMP
                ));
                c.drawCircle(x, y, dp(7f), p);
                resetPaint();
                p.setColor(a(SILVER, .88f));
                c.drawCircle(x, y, dp(.75f), p);
            }

            // Collapse shockwave.
            if (pulse >= 0f && pulse < 1f) {
                float e = easeOut(pulse);
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeCap(Paint.Cap.ROUND);
                for (int i = 0; i < 3; i++) {
                    float rr = r * (.72f + e * (1.30f + i * .22f));
                    float al = (1f - e) * (.45f - i * .09f);
                    p.setStrokeWidth(dp(i == 0 ? 1.4f : .65f));
                    p.setColor(a(new int[]{c0,c2,c1}[i], al));
                    c.drawCircle(cx, cy, rr, p);
                }
                resetPaint();

                float flash = (1f - e) * .18f;
                p.setShader(new RadialGradient(
                    cx, cy, r * 1.22f,
                    new int[]{ a(Color.WHITE, flash), a(c0, flash * .45f), Color.TRANSPARENT },
                    null, Shader.TileMode.CLAMP
                ));
                c.drawCircle(cx, cy, r * 1.22f, p);
                resetPaint();
            }

            // Sparse central identity, intentionally quieter than the material around it.
            text.setTextAlign(Paint.Align.CENTER);
            text.setTypeface(display);
            text.setTextSize(sp(30f));
            text.setColor(a(SILVER, .94f));
            c.drawText(String.format(Locale.US, "Σ.%02d", serial % 100), cx, cy + dp(8f), text);

            text.setTypeface(mono);
            text.setTextSize(sp(6.4f));
            text.setColor(a(c0, .58f));
            c.drawText("NOEMA  /  OPTICAL CORE", cx, cy + dp(31f), text);
        }

        private void drawSweep(Canvas c, long now, float cx, float cy, float r, int c0, int c1) {
            float scan = ((now - born) % 7200L) / 7200f;
            float y = cy - r * 1.55f + r * 3.10f * ease(scan);
            float dy = Math.abs(y - cy);
            float envelope = r * 1.52f;
            if (dy < envelope) {
                float half = (float)Math.sqrt(Math.max(0f, envelope * envelope - dy * dy));
                p.setShader(new LinearGradient(
                    cx - half, y, cx + half, y,
                    new int[]{ Color.TRANSPARENT, a(c1, .06f), a(c0, .42f), a(SILVER, .18f), Color.TRANSPARENT },
                    new float[]{ 0f,.36f,.50f,.58f,1f }, Shader.TileMode.CLAMP
                ));
                p.setStrokeWidth(dp(.7f));
                c.drawLine(cx - half, y, cx + half, y, p);
                resetPaint();

                p.setColor(a(c0, .025f));
                c.drawRect(cx - half, y - dp(9f), cx + half, y, p);
            }
        }

        private void drawDock(Canvas c, int w, int h, long now, int c0, int c1, int c2) {
            float x = dp(20f), right = w - dp(20f), y = h - dp(78f), hh = dp(52f), radius = dp(21f);

            p.setShader(new LinearGradient(
                x, y, right, y + hh,
                new int[]{ a(Color.rgb(12,14,18), .92f), a(Color.rgb(6,8,11), .86f) },
                null, Shader.TileMode.CLAMP
            ));
            c.drawRoundRect(x, y, right, y + hh, radius, radius, p);
            resetPaint();

            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(dp(.55f));
            p.setColor(a(Color.WHITE, .08f));
            c.drawRoundRect(x, y, right, y + hh, radius, radius, p);
            resetPaint();

            String[] names = {"FIELD", "TRACE", "VEIL"};
            float inner = x + dp(5f);
            float seg = (right - x - dp(10f)) / 3f;
            for (int i = 0; i < 3; i++) {
                float l = inner + i * seg;
                float rr = l + seg - dp(3.5f);
                if (i == mode) {
                    p.setShader(new LinearGradient(
                        l, y, rr, y + hh,
                        new int[]{ a(c0,.075f), a(c1,.14f), a(c2,.075f) },
                        null, Shader.TileMode.CLAMP
                    ));
                    c.drawRoundRect(l, y + dp(5f), rr, y + hh - dp(5f), dp(16f), dp(16f), p);
                    resetPaint();

                    p.setStyle(Paint.Style.STROKE);
                    p.setStrokeWidth(dp(.55f));
                    p.setColor(a(c0, .16f));
                    c.drawRoundRect(l, y + dp(5f), rr, y + hh - dp(5f), dp(16f), dp(16f), p);
                    resetPaint();
                }

                text.setTextAlign(Paint.Align.CENTER);
                text.setTypeface(mono);
                text.setTextSize(sp(7.0f));
                text.setColor(i == mode ? a(SILVER,.95f) : a(MUTED,.75f));
                c.drawText(names[i], (l + rr) / 2f, y + dp(31f), text);
            }
        }

        private void drawNoise(Canvas c, int w, int h, float strength) {
            resetPaint();
            Matrix m = new Matrix();
            float s = 1.15f + getResources().getDisplayMetrics().density * .12f;
            m.setScale(s, s);
            m.postTranslate((born % 31), (born % 47));
            noiseShader.setLocalMatrix(m);
            p.setShader(noiseShader);
            p.setAlpha(Math.round(255f * .26f * strength));
            c.drawRect(0, 0, w, h, p);
            resetPaint();
        }

        private void drawVignette(Canvas c, int w, int h, float strength) {
            float radius = (float)Math.hypot(w * .52f, h * .54f);
            p.setShader(new RadialGradient(
                w * .5f, h * .48f, radius,
                new int[]{ Color.TRANSPARENT, a(Color.BLACK, .08f * strength), a(Color.BLACK, .72f * strength) },
                new float[]{ .36f,.69f,1f }, Shader.TileMode.CLAMP
            ));
            c.drawRect(0, 0, w, h, p);
            resetPaint();
        }

        private boolean insideCore(float x, float y) {
            float w = getWidth(), h = getHeight();
            float cx = w * (.5f + tiltX * .016f) + tiltX * dp(7f);
            float cy = h * (.486f + tiltY * .010f) + tiltY * dp(5f);
            float r = Math.min(w, h) * .31f;
            float dx = x - cx, dy = y - cy;
            return dx * dx + dy * dy <= r * r;
        }

        private void triggerCollapse() {
            serial++;
            pulseAt = SystemClock.uptimeMillis();
            performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
            invalidate();
        }

        private void selectMode(int next) {
            next = Math.max(0, Math.min(2, next));
            if (next == mode) return;
            previousMode = mode;
            mode = next;
            modeChangedAt = SystemClock.uptimeMillis();
            pulseAt = modeChangedAt;
            performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
            invalidate();
        }

        @Override public boolean onTouchEvent(MotionEvent e) {
            float x = e.getX(), y = e.getY();

            switch (e.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    touchDown = true;
                    dragGesture = false;
                    touchDownAt = SystemClock.uptimeMillis();
                    touchStartX = lastTouchX = x;
                    touchStartY = lastTouchY = y;
                    return true;

                case MotionEvent.ACTION_MOVE:
                    if (!touchDown) return true;
                    float dx = x - lastTouchX;
                    float dy = y - lastTouchY;
                    if (Math.hypot(x - touchStartX, y - touchStartY) > dp(5f)) dragGesture = true;

                    // Direct manipulation only when the gesture begins near the core.
                    if (insideCore(touchStartX, touchStartY)) {
                        manualYaw += dx * .18f;
                        manualPitch = clamp(manualPitch + dy * .06f, -22f, 22f);
                    }
                    lastTouchX = x;
                    lastTouchY = y;
                    invalidate();
                    return true;

                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    boolean wasDown = touchDown;
                    touchDown = false;

                    if (e.getActionMasked() == MotionEvent.ACTION_CANCEL) return true;

                    float dockTop = getHeight() - dp(84f);
                    if (y >= dockTop) {
                        float left = dp(20f);
                        float usable = getWidth() - left * 2f;
                        int next = (int)((x - left) / (usable / 3f));
                        selectMode(next);
                        return true;
                    }

                    if (wasDown && !dragGesture && insideCore(x, y)) {
                        triggerCollapse();
                    } else if (wasDown && dragGesture && insideCore(touchStartX, touchStartY)) {
                        performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                    }
                    return true;
            }
            return true;
        }
    }
}
