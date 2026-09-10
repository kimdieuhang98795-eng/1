#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
main=root/'app/src/main/java/com/ajiu/reva/MainActivity.java'
gradle=root/'app/build.gradle'
check_project=root/'tools/check_project.py'
config_dst=root/'app/src/main/java/com/ajiu/reva/ControlLayoutConfig.java'
painter_dst=root/'app/src/main/java/com/ajiu/reva/SkillIconPainter.java'
config_src=Path(__file__).with_name('ControlLayoutConfig.java')
painter_src=Path(__file__).with_name('SkillIconPainter.java')

s=main.read_text()

def once(old,new):
    global s
    if old not in s:
        raise SystemExit('v1.11 missing needle: '+old[:220].replace('\n','\\n'))
    s=s.replace(old,new,1)

# ---------------------------------------------------------------------------
# 1) Persistent profession display profile. This changes HUD artwork only;
#    original keyboard dispatch and pointer ownership are deliberately untouched.
# ---------------------------------------------------------------------------
once('''        final ControlLayoutConfig controlLayout = ControlLayoutConfig.modern();\n''','''        final ControlLayoutConfig controlLayout = ControlLayoutConfig.modern();
        final String[] skillProfiles={"Spitfire","Ranger","Berserker","WeaponMaster"};
        final String[] skillProfileLabels={"弹药","漫游","狂战","剑魂"};
        int skillProfileIndex=-1;

        void ensureSkillProfile(){
            if(skillProfileIndex>=0) return;
            int saved=getContext().getSharedPreferences("reva_hud",android.content.Context.MODE_PRIVATE).getInt("skill_profile",0);
            skillProfileIndex=Math.max(0,Math.min(saved,skillProfiles.length-1));
        }

        String currentSkillProfile(){ ensureSkillProfile(); return skillProfiles[skillProfileIndex]; }
        String currentSkillProfileLabel(){ ensureSkillProfile(); return skillProfileLabels[skillProfileIndex]; }

        void cycleSkillProfile(){
            ensureSkillProfile();
            skillProfileIndex=(skillProfileIndex+1)%skillProfiles.length;
            getContext().getSharedPreferences("reva_hud",android.content.Context.MODE_PRIVATE)
                    .edit().putInt("skill_profile",skillProfileIndex).apply();
            android.util.Log.i("REVA_TOUCH","PROFILE:"+currentSkillProfile()+":"+currentSkillProfileLabel());
        }
''')

# Profile selector is rebuilt from metadata next to items; all v1.10 controls stay put.
once('''        void rebuild() {\n            releaseAll();\n            buttons.clear();\n''','''        void rebuild() {
            releaseAll();
            buttons.clear();
            ensureSkillProfile();
''')
once('''            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.itemButtons) addConfigured(spec,spec.key,spec.caption,-1);\n            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.utilityButtons) addConfigured(spec,spec.key,spec.caption,-1);\n''','''            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.itemButtons) addConfigured(spec,spec.key,spec.caption,-1);
            addConfigured(controlLayout.profileButton,"PROFILE",currentSkillProfileLabel(),-1);
            for(ControlLayoutConfig.ButtonSpec spec:controlLayout.utilityButtons) addConfigured(spec,spec.key,spec.caption,-1);
''')

# Add profile geometry to device-level QA evidence.
once('''            B x=findByLabel("X"), a=findByLabel("A"), back=findByLabel("↓"), ctrl=findByLabel("CTRL"), bex=findByLabel("B");\n''','''            B x=findByLabel("X"), a=findByLabel("A"), back=findByLabel("↓"), ctrl=findByLabel("CTRL"), bex=findByLabel("B"), profile=findByLabel("PROFILE");
''')
once('''                if(bex!=null) android.util.Log.i("REVA_TOUCH","BEXRECT:"+(loc[0]+Math.round(bex.r.left))+","+(loc[1]+Math.round(bex.r.top))+","+(loc[0]+Math.round(bex.r.right))+","+(loc[1]+Math.round(bex.r.bottom)));\n''','''                if(bex!=null) android.util.Log.i("REVA_TOUCH","BEXRECT:"+(loc[0]+Math.round(bex.r.left))+","+(loc[1]+Math.round(bex.r.top))+","+(loc[0]+Math.round(bex.r.right))+","+(loc[1]+Math.round(bex.r.bottom)));
                if(profile!=null) android.util.Log.i("REVA_TOUCH","PROFILERECT:"+(loc[0]+Math.round(profile.r.left))+","+(loc[1]+Math.round(profile.r.top))+","+(loc[0]+Math.round(profile.r.right))+","+(loc[1]+Math.round(profile.r.bottom)));
''')

# ---------------------------------------------------------------------------
# 2) Replace generic skill glyphs with original SWF-derived profile artwork.
#    The four EX utility keys participate in the same original-art mapping.
# ---------------------------------------------------------------------------
once('''                SkillIconPainter.draw(c,b.r,b.label,b.active,sc);\n''','''                SkillIconPainter.draw(c,b.r,b.label,currentSkillProfile(),b.active,sc,getContext().getAssets());
''')

utility_branch='''            if("utility".equals(b.category)) {
                SkillIconPainter.draw(c,b.r,b.label,currentSkillProfile(),b.active,sc,getContext().getAssets());
                c.restoreToCount(save);
                drawFeedbackRing(c,b,phase);
                return;
            }
            if("profile".equals(b.category)) {
                text.setTextAlign(Paint.Align.CENTER); text.setTypeface(Typeface.DEFAULT_BOLD);
                text.setColor(0xFFF0DEAC); text.setTextSize(10.5f*sc);
                c.drawText(currentSkillProfileLabel(),b.r.centerX(),b.r.centerY()+4f*sc,text);
                text.setTextSize(6.8f*sc); text.setColor(0x99FFFFFF);
                c.drawText("职业",b.r.centerX(),b.r.top+9f*sc,text);
                c.restoreToCount(save);
                drawFeedbackRing(c,b,phase);
                return;
            }
'''
once('''            if("item".equals(b.category)) {\n''',utility_branch+'''            if("item".equals(b.category)) {
''')

# Profile is presentation state, not a keyboard key. Intercept before PAGE logic.
once('''            pointerMap.put(pid,b);\n            if(b.mode==MODE_PAGE){\n''','''            pointerMap.put(pid,b);
            if("profile".equals(b.category)){
                performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK);
                cycleSkillProfile();
                rebuild();
                return;
            }
            if(b.mode==MODE_PAGE){
''')

# Optional distinct socket tone for the selector.
once('''            if("utility".equals(b.category)) return 0xA8191C22;\n''','''            if("utility".equals(b.category)) return 0xA8191C22;
            if("profile".equals(b.category)) return 0xB4232525;
''')

# Runtime marker and source modules.
once('''LAYOUT:MODERN_V110''','''LAYOUT:MODERN_V111''')
if not config_src.exists() or not painter_src.exists():
    raise SystemExit('v1.11 renderer/layout sources missing')
config_dst.write_text(config_src.read_text())
painter_dst.write_text(painter_src.read_text())

# Metadata.
g=gradle.read_text()
if 'versionCode 20' not in g or "versionName '1.10'" not in g:
    raise SystemExit('expected v1.10 version markers not found')
g=g.replace('versionCode 20','versionCode 21',1).replace("versionName '1.10'","versionName '1.11'",1)
gradle.write_text(g)
main.write_text(s)

# Inherited checker must understand the new marker.
if check_project.exists():
    q=check_project.read_text()
    old="['LAYOUT:MODERN_V18','LAYOUT:MODERN_V19','LAYOUT:MODERN_V110']"
    new="['LAYOUT:MODERN_V18','LAYOUT:MODERN_V19','LAYOUT:MODERN_V110','LAYOUT:MODERN_V111']"
    if old not in q: raise SystemExit('v1.11 QA marker whitelist needle missing')
    check_project.write_text(q.replace(old,new,1))

# ---------------------------------------------------------------------------
# 3) Architecture guards: require new visual/profile layer and prove the stable
#    input machinery survived byte-for-byte style transformations.
# ---------------------------------------------------------------------------
for required in [
    'currentSkillProfile()','cycleSkillProfile()','PROFILE:', 'PROFILERECT:',
    'addConfigured(controlLayout.profileButton,"PROFILE",currentSkillProfileLabel(),-1)',
    'SkillIconPainter.draw(c,b.r,b.label,currentSkillProfile(),b.active,sc,getContext().getAssets())',
    'LAYOUT:MODERN_V111','ROLE_JOYSTICK','ROLE_BUTTON','ROLE_GAME',
    'dispatchDomKey(','forceDomReleaseAll(','kickButtonFeedback(B b)',
    'pulse(b.label)','send(b.label,true)','keys.put("CTRL", KeyEvent.KEYCODE_CTRL_LEFT)'
]:
    if required not in s: raise SystemExit('v1.11 required logic missing: '+required)
for forbidden in ['LAYOUT:MODERN_V110','recoverJoystickOnMove(','inputHandler.postDelayed(this,132L)','inputHandler.postDelayed(this,92L)']:
    if forbidden in s: raise SystemExit('v1.11 forbidden residue: '+forbidden)

cfg=config_dst.read_text(); painter=painter_dst.read_text()
for token in ['profileButton','ButtonSpec.pill("PROFILE"','ButtonSpec.pill("CTRL"','ButtonSpec.pill("B"']:
    if token not in cfg: raise SystemExit('v1.11 layout missing: '+token)
for token in ['Spitfire:A','Ranger:T','Berserker:SPACE','WeaponMaster:CTRL','transparent','skill_icons/']:
    if token not in painter: raise SystemExit('v1.11 painter missing: '+token)
if check_project.exists() and "'LAYOUT:MODERN_V111'" not in check_project.read_text():
    raise SystemExit('v1.11 checker is not version-aware')

print('PASS apply_v111: profession-aware original 3.0 EX skill HUD wired')
print('PASS apply_v111: manual persisted profile switch added without keyboard dispatch')
print('PASS apply_v111: v1.10 pointer router, EX controls, paging and haptics preserved')
