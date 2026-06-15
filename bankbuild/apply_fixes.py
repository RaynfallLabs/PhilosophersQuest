"""Apply verified audit fixes back into the ladder files, then re-merge + re-promote.
Usage: python bankbuild/apply_fixes.py <fixes.json>
  fixes.json = list of {sid, stem, choices, answer, context}  (the workflow's `fixed`, filtered to clean sids)
Locates each rung by its ORIGINAL stem (from _audit_sample.json) inside the ladder file for its topic."""
import json, glob, os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAD=os.path.join(ROOT,'bankbuild','history','ladders')
sample={r['sid']:r for r in json.load(open(os.path.join(ROOT,'bankbuild','history','_audit_sample.json'),encoding='utf-8'))}
# map topic name -> ladder file
byname={}
for f in glob.glob(os.path.join(LAD,'*.json')):
    d=json.load(open(f,encoding='utf-8')); byname[d.get('name')]=f
fixes=json.load(open(sys.argv[1],encoding='utf-8'))
applied=skipped=0
for fx in fixes:
    sid=fx['sid']; s=sample.get(sid)
    if not s: skipped+=1; continue
    if fx.get('answer') not in fx.get('choices',[]) or len(fx.get('choices',[]))!=4: 
        print('  SKIP sid%d: fix answer not in 4 choices'%sid); skipped+=1; continue
    f=byname.get(s['topic'])
    if not f: print('  SKIP sid%d: no ladder file for %r'%(sid,s['topic'])); skipped+=1; continue
    d=json.load(open(f,encoding='utf-8')); hit=False
    for r in d.get('rungs',[]):
        if r.get('stem','').strip()==s['stem'].strip():
            r['stem']=fx['stem']; r['choices']=fx['choices']; r['answer']=fx['answer']
            if fx.get('context'): r['context']=fx['context']
            hit=True; break
    if hit:
        json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=True,indent=1); applied+=1
    else:
        print('  SKIP sid%d: original stem not found in %s'%(sid,os.path.basename(f))); skipped+=1
print('applied %d, skipped %d'%(applied,skipped))
