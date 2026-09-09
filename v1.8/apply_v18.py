#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
main = root / 'app/src/main/java/com/ajiu/reva/MainActivity.java'
gradle = root / 'app/build.gradle'
config_dst = root / 'app/src/main/java/com/ajiu/reva/ControlLayoutConfig.java'
config_src = Path(__file__).with_name('ControlLayoutConfig.java')

s = main.read_text()

def once(old, new):
    global s
    if old not in s:
        raise SystemExit('v1.8 missing needle: ' + old[:180].replace('\n', '\\n'))
    s = s.replace(old, new, 1)

def span(start, end, new):
    global s
    a = s.find(start)
    if a < 0:
        raise SystemExit('v1.8 missing span start: ' + start[:120])
    b = s.find(end, a)
    if b < 0:
        raise SystemExit('v1.8 missing span end: ' + end[:120])
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------------------
# 1) Pull all HUD geometry / labels / input modes out of MainActivity.
# ---------------------------------------------------------------------------
once('''        float sc=1f, ox=0f, oy=0f;\n        final float joyDesignX=154f, joyDesignY=565f, joyDesignR=105f;\n''','''        float sc=1f, ox=0f, oy=0f;
        final ControlLayoutConfig controlLayout = ControlLayoutConfig.modern();
        final float joyDesignX=controlLayout.joystickHomeX, joyDesignY=controlLayout.joystickHomeY, joyDesignR=controlLayout.joystickRadius;
''')

once('''            int mode;\n            int tone;\n''','''            int mode;
            int tone;
            String category="core";
            int slot=-1;
''')

rebuild = '''        void rebuild() {
            releaseAll();
            buttons.clear();

            // Layout is data-driven in v1.8. Input ownership / key dispatch stays unchanged.
            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.coreButtons) addConfigured(spec,spec.key,spec.caption,-1);

            String[] g=skillGroups[skillGroup];
            for(int i=0;i<g.length && i<controlLayout.skillSlots.length;i++) {
                addConfigured(controlLayout.skillSlots[i],g[i],"",i);
            }
            addConfigured(controlLayout.pageButton,"PAGE","",-1);
            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.itemButtons) addConfigured(spec,spec.key,spec.caption,-1);
            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.utilityButtons) addConfigured(spec,spec.key,spec.caption,-1);

            invalidate();
            B x=findByLabel("X"), a=findByLabel("A"), back=findByLabel("↓");
            post(() -> {
                int[] loc=new int[2]; getLocationOnScreen(loc);
                if(x!=null) android.util.Log.i("REVA_TOUCH","XRECT:"+(loc[0]+Math.round(x.r.left))+","+(loc[1]+Math.round(x.r.top))+","+(loc[0]+Math.round(x.r.right))+","+(loc[1]+Math.round(x.r.bottom))+" VIEW:"+getWidth()+"x"+getHeight());
                if(a!=null) android.util.Log.i("REVA_TOUCH","ARECT:"+(loc[0]+Math.round(a.r.left))+","+(loc[1]+Math.round(a.r.top))+","+(loc[0]+Math.round(a.r.right))+","+(loc[1]+Math.round(a.r.bottom)));
                if(back!=null) android.util.Log.i("REVA_TOUCH","BACKRECT:"+(loc[0]+Math.round(back.r.left))+","+(loc[1]+Math.round(back.r.top))+","+(loc[0]+Math.round(back.r.right))+","+(loc[1]+Math.round(back.r.bottom)));
                android.util.Log.i("REVA_TOUCH","JOY:"+(loc[0]+Math.round(joyHomeX))+","+(loc[1]+Math.round(joyHomeY))+","+Math.round(joyR));
                android.util.Log.i("REVA_TOUCH","JOYZONE:"+(loc[0]+Math.round(px(controlLayout.joystickZoneLeft)))+","+(loc[1]+Math.round(py(controlLayout.joystickZoneTop)))+","+(loc[0]+Math.round(px(controlLayout.joystickZoneRight)))+","+(loc[1]+Math.round(py(controlLayout.joystickZoneBottom))));
                android.util.Log.i("REVA_TOUCH","LAYOUT:MODERN_V18:buttons="+buttons.size()+":page="+(skillGroup+1));
            });
        }

        int modeFor(String mode){
            if(ControlLayoutConfig.HOLD.equals(mode)) return MODE_HOLD;
            if(ControlLayoutConfig.PAGE.equals(mode)) return MODE_PAGE;
            return MODE_PULSE;
        }

        B addConfigured(ControlLayoutConfig.ButtonSpec spec,String key,String caption,int slot){
            B b=addButton(key,caption,modeFor(spec.inputMode),spec.tone,spec.left,spec.top,spec.right,spec.bottom);
            b.circle=spec.circle;
            b.category=spec.category;
            b.slot=slot;
            return b;
        }

'''
span('''        void rebuild() {\n''','''        B addCircle(String l,String cap,int mode,int tone,float cx,float cy,float r)''',rebuild)

# Old addCircle/addPill helpers are no longer needed; addButton remains the one constructor.
span('''        B addCircle(String l,String cap,int mode,int tone,float cx,float cy,float r)''','''        B findByLabel(String label)''','''        B addButton(String l,String cap,int mode,int tone,float lft,float top,float rgt,float bot){
            B b=new B(l,cap,mode,tone); b.r.set(px(lft),py(top),px(rgt),py(bot)); buttons.add(b); return b;
        }
''')

# ---------------------------------------------------------------------------
# 2) Modern mobile visual language. No proprietary DNF Mobile assets are copied;
# all glyphs are programmatic placeholders that can later be replaced by icons.
# ---------------------------------------------------------------------------
base = '''        int baseColor(B b){
            if("attack".equals(b.category)) return 0xC94B3717;
            if("skill".equals(b.category)) {
                int[] tones={0xC8322734,0xC8243142,0xC83A3021,0xC82B3B32,0xC83B2530,0xC8273540};
                return tones[Math.max(0,b.slot)%tones.length];
            }
            if("core".equals(b.category)) return b.tone==1?0xC8273342:(b.tone==2?0xC83A2630:0xC82C2A44);
            if("backstep".equals(b.category)) return 0xC23A2D22;
            if("page".equals(b.category)) return 0xB81B1C22;
            if("item".equals(b.category)) return 0xB3262520;
            if("utility".equals(b.category)) return 0xA8191C22;
            return 0xB8272B31;
        }

'''
span('''        int baseColor(B b){\n''','''        @Override protected void onDraw(Canvas c) {''',base)

draw = '''        void drawButton(Canvas c,B b){
            boolean circle=b.circle;
            fill.setColor(b.active?0xE9D8C17A:baseColor(b));
            stroke.setStrokeWidth((b.active?3.6f:1.9f)*sc);
            stroke.setColor(b.active?0xFFFFE4A0:0xA9D8C895);
            if(circle){ c.drawOval(b.r,fill); c.drawOval(b.r,stroke); }
            else { c.drawRoundRect(b.r,15*sc,15*sc,fill); c.drawRoundRect(b.r,15*sc,15*sc,stroke); }

            if(b.active){
                stroke.setStrokeWidth(1.6f*sc); stroke.setColor(0x66FFF0B0);
                RectF halo=new RectF(b.r); halo.inset(-5f*sc,-5f*sc);
                if(circle) c.drawOval(halo,stroke); else c.drawRoundRect(halo,18*sc,18*sc,stroke);
            }

            if("skill".equals(b.category)) {
                drawSkillGlyph(c,b);
                drawTinyKey(c,b,b.label);
                return;
            }
            if("item".equals(b.category)) {
                drawItemGlyph(c,b);
                drawTinyKey(c,b,b.label);
                return;
            }
            if("page".equals(b.category)) {
                text.setTextAlign(Paint.Align.CENTER); text.setTypeface(Typeface.DEFAULT_BOLD);
                text.setColor(0xFFF4E6B5); text.setTextSize(12f*sc);
                c.drawText("技能",b.r.centerX(),b.r.centerY()-1f*sc,text);
                text.setTextSize(9f*sc); text.setColor(0xCCFFFFFF);
                c.drawText((skillGroup+1)+" / "+skillGroups.length,b.r.centerX(),b.r.centerY()+13f*sc,text);
                return;
            }

            text.setTextAlign(Paint.Align.CENTER); text.setTypeface(Typeface.DEFAULT_BOLD);
            text.setColor(b.active?0xFF17140D:Color.WHITE);
            float size="attack".equals(b.category)?21f:("utility".equals(b.category)?12f:13.5f);
            text.setTextSize(size*sc);
            Paint.FontMetrics fm=text.getFontMetrics();
            float ty=b.r.centerY()-(fm.ascent+fm.descent)/2f;
            c.drawText(b.caption,b.r.centerX(),ty,text);
            if(!"attack".equals(b.category)) drawTinyKey(c,b,b.label);
        }

        void drawTinyKey(Canvas c,B b,String key){
            if(key==null || key.length()==0 || "PAGE".equals(key)) return;
            String shown="SPACE".equals(key)?"SP":"SHIFT".equals(key)?"SH":key;
            text.setTypeface(Typeface.DEFAULT_BOLD); text.setTextAlign(Paint.Align.RIGHT);
            text.setTextSize(7.5f*sc); text.setColor(0xAFFFFFFF);
            c.drawText(shown,b.r.right-5f*sc,b.r.bottom-4f*sc,text);
            text.setTextAlign(Paint.Align.CENTER);
        }

        void drawSkillGlyph(Canvas c,B b){
            float cx=b.r.centerX(), cy=b.r.centerY(), r=b.r.width()*0.24f;
            icon.setStyle(Paint.Style.STROKE); icon.setStrokeWidth(2.6f*sc);
            icon.setStrokeCap(Paint.Cap.ROUND); icon.setColor(b.active?0xFF2D2615:0xDDEFE7D0);
            int slot=Math.max(0,b.slot)%6;
            if(slot==0){
                c.drawLine(cx-r,cy+r*0.85f,cx+r,cy-r*0.85f,icon);
                c.drawLine(cx-r*0.35f,cy-r,cx+r*0.35f,cy+r,icon);
            } else if(slot==1){
                c.drawCircle(cx,cy,r*0.9f,icon);
                c.drawLine(cx-r*1.15f,cy,cx+r*1.15f,cy,icon);
            } else if(slot==2){
                Path p=new Path(); p.moveTo(cx-r,cy+r*0.7f); p.lineTo(cx,cy-r); p.lineTo(cx+r,cy+r*0.7f); c.drawPath(p,icon);
            } else if(slot==3){
                c.drawLine(cx-r,cy-r,cx+r,cy+r,icon);
                c.drawLine(cx-r,cy+r,cx+r,cy-r,icon);
            } else if(slot==4){
                RectF q=new RectF(cx-r,cy-r,cx+r,cy+r); c.drawArc(q,205,290,false,icon);
                c.drawLine(cx+r*0.7f,cy-r*0.7f,cx+r*1.15f,cy-r*0.4f,icon);
            } else {
                c.drawCircle(cx-r*0.45f,cy,r*0.35f,icon);
                c.drawCircle(cx+r*0.45f,cy,r*0.35f,icon);
                c.drawLine(cx-r*0.1f,cy-r*0.8f,cx+r*0.1f,cy+r*0.8f,icon);
            }
        }

        void drawItemGlyph(Canvas c,B b){
            float cx=b.r.centerX(),cy=b.r.centerY(),w=b.r.width()*0.18f,h=b.r.height()*0.24f;
            icon.setStyle(Paint.Style.STROKE); icon.setStrokeWidth(2.1f*sc); icon.setColor(0xDDEED9A2);
            RectF bottle=new RectF(cx-w,cy-h*0.55f,cx+w,cy+h); c.drawRoundRect(bottle,4f*sc,4f*sc,icon);
            c.drawLine(cx-w*0.45f,cy-h*0.75f,cx+w*0.45f,cy-h*0.75f,icon);
            c.drawLine(cx,cy-h*0.25f,cx,cy+h*0.58f,icon);
            c.drawLine(cx-w*0.45f,cy+h*0.18f,cx+w*0.45f,cy+h*0.18f,icon);
        }

'''
span('''        void drawButton(Canvas c,B b){\n''','''        boolean containsButton(B b,float x,float y){''',draw)

# ---------------------------------------------------------------------------
# 3) Joystick geometry comes from the same config object.
# ---------------------------------------------------------------------------
once('''        boolean hitJoystickStartZone(float x,float y){\n            return x>=px(0f) && x<=px(390f) && y>=py(340f) && y<=py(720f);\n        }\n''','''        boolean hitJoystickStartZone(float x,float y){
            return x>=px(controlLayout.joystickZoneLeft) && x<=px(controlLayout.joystickZoneRight)
                && y>=py(controlLayout.joystickZoneTop) && y<=py(controlLayout.joystickZoneBottom);
        }
''')
once('''            joyBaseX=Math.max(px(92f),Math.min(x,px(335f)));\n            joyBaseY=Math.max(py(390f),Math.min(y,py(625f)));\n''','''            joyBaseX=Math.max(px(controlLayout.joystickClampLeft),Math.min(x,px(controlLayout.joystickClampRight)));
            joyBaseY=Math.max(py(controlLayout.joystickClampTop),Math.min(y,py(controlLayout.joystickClampBottom)));
''')
once('''                joyBaseX=Math.max(px(92f),Math.min(joyBaseX,px(335f)));\n''','''                joyBaseX=Math.max(px(controlLayout.joystickClampLeft),Math.min(joyBaseX,px(controlLayout.joystickClampRight)));
''')

# Metadata.
g = gradle.read_text()
if 'versionCode 17' not in g or "versionName '1.7'" not in g:
    raise SystemExit('expected v1.7 version markers not found')
g = g.replace('versionCode 17', 'versionCode 18', 1).replace("versionName '1.7'", "versionName '1.8'", 1)
gradle.write_text(g)

config_dst.parent.mkdir(parents=True, exist_ok=True)
config_dst.write_text(config_src.read_text())
main.write_text(s)

# Strong invariants: the old hard-coded keyboard-like rebuild must be gone, while
# v1.7's proven pointer and DOM-input machinery remains intact.
for forbidden in [
    'addCircle("X","攻"',
    'float[][] pos={{986,510,34}',
    'addCircle(g[i],g[i]',
    'drawSkillMark(Canvas c,B b)'
]:
    if forbidden in s:
        raise SystemExit('v1.8 forbidden residue: '+forbidden)
for required in [
    'ControlLayoutConfig.modern()',
    'addConfigured(controlLayout.skillSlots[i],g[i],"",i)',
    'LAYOUT:MODERN_V18',
    'drawSkillGlyph(Canvas c,B b)',
    'ROLE_JOYSTICK','ROLE_BUTTON','ROLE_GAME','dispatchDomKey(','forceDomReleaseAll('
]:
    if required not in s:
        raise SystemExit('v1.8 required logic missing: '+required)

print('PASS apply_v18: data-driven modern mobile HUD; v1.7 input router preserved')
