#!/usr/bin/env python3
"""Execute finalize_v15 with span replacements consuming their end boundary.

finalize_v15 replacement blocks include the boundary they replace. Consuming the old
boundary prevents duplicated method headers / closing braces in generated Java.
"""
from pathlib import Path

src=Path(__file__).with_name('finalize_v15.py')
code=src.read_text()
old='    s=s[:a]+new+s[b:]\n'
new='    s=s[:a]+new+s[b+len(end):]\n'
if code.count(old)!=1:
    raise SystemExit('unexpected finalize_v15 span helper')
code=code.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(src)}
exec(compile(code,str(src),'exec'),ns,ns)
