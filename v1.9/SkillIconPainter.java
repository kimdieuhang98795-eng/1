package com.ajiu.reva;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;

/**
 * Lightweight vector skill artwork for the mobile HUD.
 *
 * These are original, class-neutral combat glyphs rather than copied DNF assets.
 * The key is deliberately part of the visual contract so a later class/profile
 * layer can replace the artwork without touching TouchControlsView or input code.
 */
public final class SkillIconPainter {
    private SkillIconPainter() {}

    private static final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final Path path = new Path();
    private static final RectF tmp = new RectF();

    public static void draw(Canvas c, RectF r, String key, boolean active, float sc) {
        float cx = r.centerX(), cy = r.centerY();
        float radius = Math.min(r.width(), r.height()) * 0.33f;
        int accent = accent(key);
        int pale = active ? 0xFFFFF0C2 : 0xFFF4E9D3;

        // Deep inner socket + colored energy well.
        tmp.set(r); tmp.inset(5f * sc, 5f * sc);
        p.setStyle(Paint.Style.FILL);
        p.setColor(active ? 0xE51B1711 : 0xD812151B);
        c.drawOval(tmp, p);
        tmp.inset(3f * sc, 3f * sc);
        p.setColor(withAlpha(accent, active ? 118 : 76));
        c.drawOval(tmp, p);

        // Broken outer energy arc keeps each socket from reading as a flat button.
        tmp.set(r); tmp.inset(4f * sc, 4f * sc);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth((active ? 3.2f : 2.0f) * sc);
        p.setStrokeCap(Paint.Cap.ROUND);
        p.setColor(withAlpha(accent, active ? 255 : 205));
        c.drawArc(tmp, 205f, 102f, false, p);
        c.drawArc(tmp, 25f, 92f, false, p);

        String k = key == null ? "" : key.toUpperCase();
        switch (k) {
            case "A": slash(c, cx, cy, radius, accent, pale, sc); break;
            case "S": crossBurst(c, cx, cy, radius, accent, pale, sc); break;
            case "D": crescent(c, cx, cy, radius, accent, pale, sc); break;
            case "F": shockwave(c, cx, cy, radius, accent, pale, sc); break;
            case "G": vortex(c, cx, cy, radius, accent, pale, sc); break;
            case "H": finisher(c, cx, cy, radius, accent, pale, sc); break;
            case "Q": aura(c, cx, cy, radius, accent, pale, sc); break;
            case "W": beam(c, cx, cy, radius, accent, pale, sc); break;
            case "E": barrage(c, cx, cy, radius, accent, pale, sc); break;
            case "R": meteor(c, cx, cy, radius, accent, pale, sc); break;
            case "T": sigil(c, cx, cy, radius, accent, pale, sc); break;
            case "Y": dash(c, cx, cy, radius, accent, pale, sc); break;
            default: slash(c, cx, cy, radius, accent, pale, sc); break;
        }

        drawKeyBadge(c, r, k, active, sc);
    }

    private static int accent(String key) {
        if (key == null) return 0xFFBCA869;
        switch (key.toUpperCase()) {
            case "A": return 0xFFE8B55A;
            case "S": return 0xFFE56D64;
            case "D": return 0xFF8C7BEA;
            case "F": return 0xFF61B8E7;
            case "G": return 0xFF63C89B;
            case "H": return 0xFFF08B4F;
            case "Q": return 0xFFB88AE8;
            case "W": return 0xFF70C7EF;
            case "E": return 0xFFE6C35F;
            case "R": return 0xFFE47B53;
            case "T": return 0xFFD7A85A;
            case "Y": return 0xFF79C7A2;
            default: return 0xFFC9B578;
        }
    }

    private static int withAlpha(int color, int alpha) {
        return (color & 0x00FFFFFF) | ((alpha & 0xFF) << 24);
    }

    private static void line(float width, int color, float sc) {
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(width * sc);
        p.setStrokeCap(Paint.Cap.ROUND);
        p.setStrokeJoin(Paint.Join.ROUND);
        p.setColor(color);
    }

    private static void slash(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(5.0f,a,sc); c.drawLine(cx-r*.82f,cy+r*.72f,cx+r*.82f,cy-r*.72f,p);
        line(2.1f,pale,sc); c.drawLine(cx-r*.57f,cy+r*.45f,cx+r*.67f,cy-r*.63f,p);
        line(2.2f,withAlpha(a,145),sc); c.drawLine(cx-r*.86f,cy+r*.16f,cx-r*.28f,cy-r*.42f,p);
    }

    private static void crossBurst(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(3.4f,a,sc);
        for(int i=0;i<4;i++){
            double q=Math.toRadians(45+i*90); float x=(float)Math.cos(q),y=(float)Math.sin(q);
            c.drawLine(cx+x*r*.28f,cy+y*r*.28f,cx+x*r*.96f,cy+y*r*.96f,p);
        }
        path.reset(); path.moveTo(cx,cy-r*.52f); path.lineTo(cx+r*.42f,cy); path.lineTo(cx,cy+r*.52f); path.lineTo(cx-r*.42f,cy); path.close();
        p.setStyle(Paint.Style.FILL); p.setColor(a); c.drawPath(path,p);
        line(1.7f,pale,sc); c.drawPath(path,p);
    }

    private static void crescent(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        tmp.set(cx-r*.82f,cy-r*.82f,cx+r*.82f,cy+r*.82f);
        line(5.3f,a,sc); c.drawArc(tmp,118,235,false,p);
        tmp.inset(5f*sc,5f*sc); line(1.7f,pale,sc); c.drawArc(tmp,124,220,false,p);
        line(2.0f,withAlpha(a,150),sc); c.drawLine(cx+r*.40f,cy-r*.70f,cx+r*.92f,cy-r*.28f,p);
    }

    private static void shockwave(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(3.2f,a,sc);
        c.drawLine(cx-r*.9f,cy,cx+r*.75f,cy,p);
        c.drawLine(cx-r*.64f,cy-r*.42f,cx+r*.42f,cy-r*.42f,p);
        c.drawLine(cx-r*.64f,cy+r*.42f,cx+r*.42f,cy+r*.42f,p);
        path.reset(); path.moveTo(cx+r*.75f,cy); path.lineTo(cx+r*.35f,cy-r*.28f); path.moveTo(cx+r*.75f,cy); path.lineTo(cx+r*.35f,cy+r*.28f);
        line(2.2f,pale,sc); c.drawPath(path,p);
    }

    private static void vortex(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(3.0f,a,sc);
        for(int i=0;i<3;i++){
            float rr=r*(.38f+i*.22f); tmp.set(cx-rr,cy-rr,cx+rr,cy+rr); c.drawArc(tmp,205-i*28,205+i*18,false,p);
        }
        p.setStyle(Paint.Style.FILL); p.setColor(pale); c.drawCircle(cx,cy,r*.13f,p);
    }

    private static void finisher(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(2.8f,a,sc);
        for(int i=0;i<8;i++){
            double q=Math.toRadians(i*45); float x=(float)Math.cos(q),y=(float)Math.sin(q);
            c.drawLine(cx+x*r*.42f,cy+y*r*.42f,cx+x*r*.98f,cy+y*r*.98f,p);
        }
        p.setStyle(Paint.Style.FILL); p.setColor(a); c.drawCircle(cx,cy,r*.34f,p);
        p.setColor(pale); c.drawCircle(cx-r*.08f,cy-r*.08f,r*.11f,p);
    }

    private static void aura(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        path.reset(); path.moveTo(cx-r*.75f,cy+r*.72f); path.cubicTo(cx-r*.82f,cy-r*.1f,cx-r*.2f,cy-r*.8f,cx,cy-r*.98f); path.cubicTo(cx+r*.05f,cy-r*.35f,cx+r*.78f,cy-r*.22f,cx+r*.72f,cy+r*.72f); path.close();
        p.setStyle(Paint.Style.FILL); p.setColor(withAlpha(a,205)); c.drawPath(path,p);
        path.reset(); path.moveTo(cx-r*.25f,cy+r*.55f); path.cubicTo(cx-r*.35f,cy, cx+.05f,cy-r*.38f,cx+r*.12f,cy-r*.55f); path.cubicTo(cx+r*.38f,cy-r*.05f,cx+r*.32f,cy+r*.24f,cx+r*.18f,cy+r*.55f); path.close();
        p.setColor(pale); c.drawPath(path,p);
    }

    private static void beam(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(7.0f,withAlpha(a,185),sc); c.drawLine(cx-r*.92f,cy,cx+r*.92f,cy,p);
        line(2.3f,pale,sc); c.drawLine(cx-r*.96f,cy,cx+r*.96f,cy,p);
        line(2.0f,withAlpha(a,170),sc); c.drawLine(cx-r*.55f,cy-r*.40f,cx+r*.32f,cy-r*.22f,p); c.drawLine(cx-r*.55f,cy+r*.40f,cx+r*.32f,cy+r*.22f,p);
    }

    private static void barrage(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        p.setStyle(Paint.Style.FILL);
        float[][] pts={{-.58f,-.46f},{.08f,-.66f},{.55f,-.18f},{-.30f,.32f},{.35f,.48f}};
        for(int i=0;i<pts.length;i++){
            float x=cx+pts[i][0]*r,y=cy+pts[i][1]*r,rr=(i==2?.22f:.15f)*r;
            p.setColor(i==2?pale:a); c.drawCircle(x,y,rr,p);
            line(1.7f,withAlpha(a,155),sc); c.drawLine(x-r*.28f,y+r*.30f,x-r*.55f,y+r*.57f,p);
        }
    }

    private static void meteor(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(3.0f,withAlpha(a,185),sc); c.drawLine(cx-r*.82f,cy-r*.82f,cx-r*.18f,cy-r*.16f,p); c.drawLine(cx-r*.42f,cy-r*.92f,cx+r*.02f,cy-r*.40f,p);
        p.setStyle(Paint.Style.FILL); p.setColor(a); c.drawCircle(cx+r*.25f,cy+r*.23f,r*.48f,p);
        p.setColor(pale); c.drawCircle(cx+r*.12f,cy+r*.08f,r*.13f,p);
    }

    private static void sigil(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        tmp.set(cx-r*.78f,cy-r*.78f,cx+r*.78f,cy+r*.78f); line(2.2f,a,sc); c.drawOval(tmp,p);
        path.reset(); path.moveTo(cx,cy-r*.75f); path.lineTo(cx+r*.67f,cy+r*.45f); path.lineTo(cx-r*.67f,cy+r*.45f); path.close(); line(2.0f,pale,sc); c.drawPath(path,p);
        p.setStyle(Paint.Style.FILL); p.setColor(a); c.drawCircle(cx,cy,r*.16f,p);
    }

    private static void dash(Canvas c,float cx,float cy,float r,int a,int pale,float sc){
        line(3.8f,a,sc);
        for(int i=0;i<3;i++){
            float off=(i-1)*r*.38f;
            path.reset(); path.moveTo(cx-r*.62f+off,cy-r*.58f); path.lineTo(cx-r*.08f+off,cy); path.lineTo(cx-r*.62f+off,cy+r*.58f); c.drawPath(path,p);
        }
        line(1.7f,pale,sc); c.drawLine(cx-r*.72f,cy,cx+r*.84f,cy,p);
    }

    private static void drawKeyBadge(Canvas c, RectF r, String key, boolean active, float sc) {
        if (key.length() == 0) return;
        float br = 10.5f * sc;
        float bx = r.right - 8.5f * sc, by = r.bottom - 8.5f * sc;
        p.setStyle(Paint.Style.FILL); p.setColor(active ? 0xEAF3D98A : 0xD10C0E12); c.drawCircle(bx,by,br,p);
        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(1.2f*sc); p.setColor(active ? 0xFFFBE7A8 : 0x99E9D9A9); c.drawCircle(bx,by,br,p);
        p.setStyle(Paint.Style.FILL); p.setTextAlign(Paint.Align.CENTER); p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        p.setTextSize(8.0f*sc); p.setColor(active ? 0xFF201A0D : 0xFFEFE8D5);
        Paint.FontMetrics fm=p.getFontMetrics();
        c.drawText(key,bx,by-(fm.ascent+fm.descent)/2f,p);
    }
}
