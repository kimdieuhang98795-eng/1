package com.ajiu.reva;

import android.content.res.AssetManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;

import java.io.InputStream;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * v1.11 skill HUD renderer backed only by visuals traced from the pinned
 * Reva 3.0 EX Chinese SWF. No look-alike replacement art is synthesized.
 *
 * A bound key may intentionally have no bitmap: a few original frame-1 input
 * handlers are genuinely transparent. Those remain empty sockets with a key
 * badge instead of borrowing artwork from another profession/state.
 */
public final class SkillIconPainter {
    private SkillIconPainter() {}

    private static final Paint socket = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final Paint bitmapPaint = new Paint();
    private static final Paint badge = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final RectF tmp = new RectF();
    private static final Rect src = new Rect();
    private static final Map<String, Bitmap> cache = new HashMap<>();
    private static final Set<String> missing = new HashSet<>();

    private static String token(String profile, String key) {
        return (profile == null ? "" : profile) + ":" + (key == null ? "" : key.toUpperCase());
    }

    /** True when decompiled 3.0 EX controller evidence proves this profile owns the key. */
    public static boolean isBound(String profile, String key) {
        String t = token(profile,key);
        switch (t) {
            case "Spitfire:A": case "Spitfire:S": case "Spitfire:D": case "Spitfire:F":
            case "Spitfire:G": case "Spitfire:H": case "Spitfire:Q": case "Spitfire:W":
            case "Spitfire:E": case "Spitfire:R": case "Spitfire:T": case "Spitfire:Y":
            case "Spitfire:SHIFT": case "Spitfire:B": case "Spitfire:CTRL": case "Spitfire:SPACE":
            case "Ranger:A": case "Ranger:S": case "Ranger:D": case "Ranger:F":
            case "Ranger:G": case "Ranger:H": case "Ranger:Q": case "Ranger:W":
            case "Ranger:E": case "Ranger:R": case "Ranger:T":
            case "Ranger:SHIFT": case "Ranger:B": case "Ranger:CTRL": case "Ranger:SPACE":
            case "Berserker:A": case "Berserker:S": case "Berserker:D": case "Berserker:F":
            case "Berserker:G": case "Berserker:H": case "Berserker:Q": case "Berserker:W":
            case "Berserker:E": case "Berserker:R":
            case "Berserker:SHIFT": case "Berserker:B": case "Berserker:CTRL": case "Berserker:SPACE":
            case "WeaponMaster:A": case "WeaponMaster:D": case "WeaponMaster:F": case "WeaponMaster:G":
            case "WeaponMaster:H": case "WeaponMaster:Q": case "WeaponMaster:W": case "WeaponMaster:E":
            case "WeaponMaster:SHIFT": case "WeaponMaster:B": case "WeaponMaster:CTRL": case "WeaponMaster:SPACE":
                return true;
            default:
                return false;
        }
    }

    /** Asset path exists only for a visually proven original frame/layer. */
    private static String assetPath(String profile, String key) {
        String t=token(profile,key);
        // These are intentionally transparent in the original frame-1 state.
        switch(t) {
            case "Spitfire:A": case "Spitfire:S": case "Spitfire:D":
            case "Spitfire:Q": case "Spitfire:W": case "Spitfire:E": case "Spitfire:R": case "Spitfire:T":
            case "Ranger:A": case "Ranger:S":
                return null;
        }
        if(!isBound(profile,key)) return null;
        return "skill_icons/"+profile+"/"+key.toUpperCase()+".png";
    }

    private static Bitmap load(AssetManager assets, String path) {
        if(path==null || missing.contains(path)) return null;
        Bitmap b=cache.get(path);
        if(b!=null && !b.isRecycled()) return b;
        try(InputStream in=assets.open(path)) {
            b=BitmapFactory.decodeStream(in);
            if(b!=null) {
                cache.put(path,b);
                return b;
            }
        } catch(Exception ignored) {}
        missing.add(path);
        return null;
    }

    public static void draw(Canvas c, RectF r, String key, String profile,
                            boolean active, float sc, AssetManager assets) {
        final boolean bound=isBound(profile,key);

        // Keep the tactile socket from v1.9, but make it quieter so the original
        // pixel artwork is the visual focus.
        tmp.set(r); tmp.inset(4.5f*sc,4.5f*sc);
        socket.setStyle(Paint.Style.FILL);
        socket.setColor(active ? 0xE51B1711 : (bound ? 0xD6101216 : 0x9C101216));
        if(Math.abs(r.width()-r.height()) < 8f*sc) c.drawOval(tmp,socket);
        else c.drawRoundRect(tmp,10f*sc,10f*sc,socket);

        socket.setStyle(Paint.Style.STROKE);
        socket.setStrokeWidth((active?2.5f:1.25f)*sc);
        socket.setColor(active ? 0xFFFFD96F : (bound ? 0xA8C9B675 : 0x574F5359));
        if(Math.abs(r.width()-r.height()) < 8f*sc) c.drawOval(tmp,socket);
        else c.drawRoundRect(tmp,10f*sc,10f*sc,socket);

        Bitmap b=load(assets,assetPath(profile,key));
        if(b!=null) {
            src.set(0,0,b.getWidth(),b.getHeight());
            float max=Math.min(r.width(),r.height())*(active?0.72f:0.68f);
            float scale=Math.min(max/b.getWidth(),max/b.getHeight());
            float w=b.getWidth()*scale, h=b.getHeight()*scale;
            RectF dst=new RectF(r.centerX()-w/2f,r.centerY()-h/2f,r.centerX()+w/2f,r.centerY()+h/2f);
            bitmapPaint.setAntiAlias(false);
            bitmapPaint.setFilterBitmap(false); // preserve original pixel edges
            bitmapPaint.setDither(false);
            bitmapPaint.setAlpha(active?255:238);
            c.drawBitmap(b,src,dst,bitmapPaint);
        } else if(!bound) {
            // UI-only unavailable mark; never presented as skill artwork.
            socket.setStyle(Paint.Style.STROKE);
            socket.setStrokeWidth(1.4f*sc);
            socket.setColor(0x596E7074);
            float half=Math.min(r.width(),r.height())*.15f;
            c.drawLine(r.centerX()-half,r.centerY(),r.centerX()+half,r.centerY(),socket);
        }

        drawKeyBadge(c,r,key,bound,active,sc);
    }

    private static void drawKeyBadge(Canvas c, RectF r, String key, boolean bound, boolean active, float sc) {
        if(key==null || key.length()==0) return;
        String shown=key.toUpperCase();
        if("SHIFT".equals(shown)) shown="SH";
        else if("SPACE".equals(shown)) shown="SP";
        else if("CTRL".equals(shown)) shown="CT";

        float br=9.6f*sc;
        float bx=r.right-7.6f*sc, by=r.bottom-7.6f*sc;
        badge.setStyle(Paint.Style.FILL);
        badge.setColor(active?0xF2E8C766:(bound?0xDC0B0D10:0xB00B0D10));
        c.drawCircle(bx,by,br,badge);
        badge.setStyle(Paint.Style.STROKE); badge.setStrokeWidth(1.0f*sc);
        badge.setColor(active?0xFFFFE79D:(bound?0xB9E8D9A9:0x66787A7D));
        c.drawCircle(bx,by,br,badge);
        badge.setStyle(Paint.Style.FILL); badge.setTextAlign(Paint.Align.CENTER);
        badge.setTypeface(Typeface.DEFAULT_BOLD); badge.setTextSize(7.6f*sc);
        badge.setColor(active?0xFF211A0A:(bound?0xFFF1EAD8:0xFF777A7E));
        Paint.FontMetrics fm=badge.getFontMetrics();
        c.drawText(shown,bx,by-(fm.ascent+fm.descent)/2f,badge);
    }
}
