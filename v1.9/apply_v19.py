#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
main = root / 'app/src/main/java/com/ajiu/reva/MainActivity.java'
gradle = root / 'app/build.gradle'
painter_dst = root / 'app/src/main/java/com/ajiu/reva/SkillIconPainter.java'
painter_src = Path(__file__).with_name('SkillIconPainter.java')

s = main.read_text()

def once(old, new):
    global s
    if old not in s:
        raise SystemExit('v1.9 missing needle: ' + old[:180].replace('\n','\\n'))
    s = s.replace(old, new, 1)

def span(start, end, new):
    global s
    a = s.find(start)
    if a < 0:
        raise SystemExit('v1.9 missing span start: ' + start[:140])
    b = s.find(end, a)
    if b < 0:
        raise SystemExit('v1.9 missing span end: ' + end[:140])
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------------------
# 1) Feedback state belongs to each rendered button, never to input dispatch.
# ---------------------------------------------------------------------------
once('''            int flashSeq;\n            int mode;\n            int tone;\n            String category="core";\n            int slot=-1;\n''','''            int flashSeq;
            int mode;
            int tone;
            String category="core";
            int slot=-1;
            long feedbackStart=0L, feedbackUntil=0L;
''')

# Keep v1.8 layout/config architecture, only advance the QA/runtime marker.
once('''LAYOUT:MODERN_V18''','''LAYOUT:MODERN_V19''')

# ---------------------------------------------------------------------------
# 2) Replace flat flash with press compression + rebound + expanding energy ring.
# Skill artwork is delegated to SkillIconPainter so later class profiles can swap
# visuals without touching this view or the proven pointer/input router.
# ---------------------------------------------------------------------------
draw = '''        float feedbackPhase(B b,long now){
            if(b.feedbackStart<=0L || b.feedbackUntil<=b.feedbackStart || now>=b.feedbackUntil) return -1f;
            return Math.max(0f,Math.min(1f,(now-b.feedbackStart)/(float)(b.feedbackUntil-b.feedbackStart)));
        }

        int alphaColor(int rgb,int alpha){ return (rgb & 0x00FFFFFF) | ((alpha & 0xFF)<<24); }

        void drawButton(Canvas c,B b){
            long now=android.os.SystemClock.uptimeMillis();
            float phase=feedbackPhase(b,now);
            float scale=1f;
            if(phase>=0f){
                // Fast thumb compression, then an ease-out rebound to the resting size.
                if(phase<0.22f) scale=1f-0.105f*(phase/0.22f);
                else {
                    float q=(phase-0.22f)/0.78f;
                    float ease=1f-(float)Math.pow(1f-q,3);
                    scale=0.895f+0.105f*ease;
                }
                postInvalidateDelayed(16L);
            }

            int save=c.save();
            c.scale(scale,scale,b.r.centerX(),b.r.centerY());
            boolean circle=b.circle;

            int bg=baseColor(b);
            if(b.active && !"skill".equals(b.category)) bg=0xE7C9A65A;
            fill.setColor(bg);
            stroke.setStrokeWidth((b.active?3.4f:1.8f)*sc);
            stroke.setColor(b.active?0xFFFFE8A8:0xA9D8C895);
            if(circle){ c.drawOval(b.r,fill); c.drawOval(b.r,stroke); }
            else { c.drawRoundRect(b.r,15*sc,15*sc,fill); c.drawRoundRect(b.r,15*sc,15*sc,stroke); }

            if("skill".equals(b.category)) {
                SkillIconPainter.draw(c,b.r,b.label,b.active,sc);
                c.restoreToCount(save);
                drawFeedbackRing(c,b,phase);
                return;
            }
            if("item".equals(b.category)) {
                drawItemGlyph(c,b);
                drawTinyKey(c,b,b.label);
                c.restoreToCount(save);
                drawFeedbackRing(c,b,phase);
                return;
            }
            if("page".equals(b.category)) {
                text.setTextAlign(Paint.Align.CENTER); text.setTypeface(Typeface.DEFAULT_BOLD);
                text.setColor(0xFFF4E6B5); text.setTextSize(11.5f*sc);
                c.drawText("技能",b.r.centerX(),b.r.centerY()-1f*sc,text);
                text.setTextSize(8.5f*sc); text.setColor(0xCCFFFFFF);
                c.drawText((skillGroup+1)+" / "+skillGroups.length,b.r.centerX(),b.r.centerY()+13f*sc,text);
                c.restoreToCount(save);
                drawFeedbackRing(c,b,phase);
                return;
            }

            text.setTextAlign(Paint.Align.CENTER); text.setTypeface(Typeface.DEFAULT_BOLD);
            text.setColor(b.active?0xFF21190C:Color.WHITE);
            float size="attack".equals(b.category)?20.5f:("utility".equals(b.category)?11.5f:13.2f);
            text.setTextSize(size*sc);
            Paint.FontMetrics fm=text.getFontMetrics();
            float ty=b.r.centerY()-(fm.ascent+fm.descent)/2f;
            c.drawText(b.caption,b.r.centerX(),ty,text);
            // Core combat buttons now read as mobile actions, not keyboard labels.
            if("utility".equals(b.category)) drawTinyKey(c,b,b.label);
            c.restoreToCount(save);
            drawFeedbackRing(c,b,phase);
        }

        void drawFeedbackRing(Canvas c,B b,float phase){
            if(phase<0f) return;
            float grow=(5f+15f*phase)*sc;
            RectF ring=new RectF(b.r); ring.inset(-grow,-grow);
            int alpha=Math.max(0,Math.min(190,(int)(190f*(1f-phase))));
            stroke.setStyle(Paint.Style.STROKE);
            stroke.setStrokeWidth((2.8f-1.4f*phase)*sc);
            stroke.setColor(alphaColor(0x00FFE39A,alpha));
            if(b.circle) c.drawOval(ring,stroke); else c.drawRoundRect(ring,18f*sc,18f*sc,stroke);

            // Short inner flash gives the initial contact a crisp, readable hit.
            if(phase<0.34f){
                int ia=(int)(74f*(1f-phase/0.34f));
                fill.setColor(alphaColor(0x00FFF5C8,ia));
                RectF inner=new RectF(b.r); inner.inset(3f*sc,3f*sc);
                if(b.circle) c.drawOval(inner,fill); else c.drawRoundRect(inner,13f*sc,13f*sc,fill);
            }
        }

'''
span('''        void drawButton(Canvas c,B b){\n''','''        void drawTinyKey(Canvas c,B b,String key){''',draw)

# Remove v1.8's six-slot placeholder glyph function. The 12-key painter above owns skill art.
span('''        void drawSkillGlyph(Canvas c,B b){\n''','''        void drawItemGlyph(Canvas c,B b){''','')

# ---------------------------------------------------------------------------
# 3) Trigger feedback from the same DOWN event that already owns the button.
# No key timing, pointer ownership, pulse release, or WebView dispatch semantics change.
# ---------------------------------------------------------------------------
press = '''        void kickButtonFeedback(B b){
            long now=android.os.SystemClock.uptimeMillis();
            b.feedbackStart=now;
            b.feedbackUntil=now+180L;
            int h=("skill".equals(b.category)||"attack".equals(b.category))
                    ? HapticFeedbackConstants.VIRTUAL_KEY
                    : HapticFeedbackConstants.KEYBOARD_TAP;
            performHapticFeedback(h);
            invalidate();
            postInvalidateDelayed(16L);
            android.util.Log.i("REVA_TOUCH","FEEDBACK:"+b.label+":"+b.category);
        }

        void pressPointer(int pid,float x,float y){
            B b=hitButton(x,y); if(b==null)return;
            pointerMap.put(pid,b);
            if(b.mode==MODE_PAGE){
                performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                skillGroup=(skillGroup+1)%skillGroups.length;
                rebuild();
                return;
            }
            if(b.mode==MODE_PULSE){
                pulse(b.label);
                int seq=++b.flashSeq; b.active=true;
                kickButtonFeedback(b);
                // Visual emphasis lasts a little longer than key pulse, but never gates input.
                postDelayed(()->{ if(b.flashSeq==seq){b.active=false;invalidate();} },112L);
                android.util.Log.i("REVA_TOUCH","PULSE:"+b.label+":pid="+pid+":seq="+seq);
                return;
            }
            if(!b.active){
                b.active=true;
                send(b.label,true);
                kickButtonFeedback(b);
            }
            android.util.Log.i("REVA_TOUCH","PRESS:"+b.label+":pid="+pid);
        }

'''
span('''        void pressPointer(int pid,float x,float y){\n''','''        void releasePointer(int pid){''',press)

# ---------------------------------------------------------------------------
# 4) Metadata and separate visual module.
# ---------------------------------------------------------------------------
g=gradle.read_text()
if 'versionCode 18' not in g or "versionName '1.8'" not in g:
    raise SystemExit('expected v1.8 version markers not found')
g=g.replace('versionCode 18','versionCode 19',1).replace("versionName '1.8'","versionName '1.9'",1)
gradle.write_text(g)

if not painter_src.exists():
    raise SystemExit('missing v1.9 SkillIconPainter.java')
painter_dst.write_text(painter_src.read_text())
main.write_text(s)

# Architecture invariants: new visuals present, old placeholder artist gone, proven input untouched.
for required in [
    'SkillIconPainter.draw(c,b.r,b.label,b.active,sc)',
    'kickButtonFeedback(B b)',
    'feedbackStart=0L, feedbackUntil=0L',
    'LAYOUT:MODERN_V19',
    'ROLE_JOYSTICK','ROLE_BUTTON','ROLE_GAME','dispatchDomKey(','forceDomReleaseAll(',
    'pulse(b.label)','send(b.label,true)'
]:
    if required not in s:
        raise SystemExit('v1.9 required logic missing: '+required)
for forbidden in ['drawSkillGlyph(Canvas c,B b)','LAYOUT:MODERN_V18','inputHandler.postDelayed(this,132L)','inputHandler.postDelayed(this,92L)']:
    if forbidden in s:
        raise SystemExit('v1.9 forbidden residue: '+forbidden)

print('PASS apply_v19: 12-key vector skill art + tactile rebound/ripple feedback')
print('PASS apply_v19: pointer ownership and DOM keyboard input semantics preserved')
