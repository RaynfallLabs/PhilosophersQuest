import json,glob,os,re,difflib,sys
def n(s): return re.sub(r'\s+',' ',str(s)).strip().lower()
rungs=[]
for f in sorted(glob.glob('bankbuild/grammar/ladders/*.json')):
    slug=os.path.basename(f)[:-5]
    for r in json.load(open(f,encoding='utf-8'))['rungs']:
        rungs.append((slug,n(r['stem']),n(r['answer']),frozenset(n(c) for c in r.get('choices',[]))))
by_stem={}
for r in rungs: by_stem.setdefault(r[1],set()).add(r[0])
by_ans={}
for r in rungs: by_ans.setdefault(r[2],set()).add(r[0])
by_choices={}
for r in rungs: by_choices.setdefault(r[3],set()).add(r[0])
q=json.load(open('data/questions/grammar.json',encoding='utf-8'))
out=[]; how={'stem':0,'choices':0,'answer':0,'fuzzy':0,'none':0}
for x in q:
    st=n(x['question']); a=n(x['answer']); cs=frozenset(n(c) for c in x.get('choices',[]))
    s=by_stem.get(st)
    if s and len(s)==1: out.append(next(iter(s))); how['stem']+=1; continue
    s=by_choices.get(cs)
    if s and len(s)==1: out.append(next(iter(s))); how['choices']+=1; continue
    s=by_ans.get(a)
    if s and len(s)==1: out.append(next(iter(s))); how['answer']+=1; continue
    best=max(rungs,key=lambda r: difflib.SequenceMatcher(None,st,r[1]).ratio()*0.6+difflib.SequenceMatcher(None,a,r[2]).ratio()*0.4)
    sc=difflib.SequenceMatcher(None,st,best[1]).ratio()*0.6+difflib.SequenceMatcher(None,a,best[2]).ratio()*0.4
    if sc>=0.55: out.append(best[0]); how['fuzzy']+=1
    else: out.append(None); how['none']+=1; print('NONE',round(sc,2),x['question'][:80],'|',best[0])
print(how)
if '--write' in sys.argv:
    for x,t in zip(q,out):
        if t: x['topic']=t
    open('data/questions/grammar.json','w',encoding='utf-8').write(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    print('written')
