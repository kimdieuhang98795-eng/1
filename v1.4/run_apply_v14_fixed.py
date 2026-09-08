#!/usr/bin/env python3
"""Run the v1.4 transformer with corrected span semantics.

The original v1.4 transform intentionally writes each replacement including its end-boundary
method signature. Its first span helper preserved that boundary as well, duplicating signatures.
This runner corrects the helper before executing the transform, then lets finalize_v14 enforce
that every input method exists exactly once.
"""
from pathlib import Path
import sys

src_path=Path(__file__).with_name('apply_v14.py')
code=src_path.read_text()
old='    s=s[:a]+new+s[b:]\n'
new='    s=s[:a]+new+s[b+len(end):]\n'
if code.count(old)!=1:
    raise SystemExit('unexpected apply_v14 span helper')
code=code.replace(old,new,1)
compiled=compile(code,str(src_path),'exec')
ns={'__name__':'__main__','__file__':str(src_path)}
exec(compiled,ns,ns)
