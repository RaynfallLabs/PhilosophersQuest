"""Full-bank audit manager: build the flat rung list, accumulate verdicts across windows,
report progress/flags, and patch verified fixes back by stable rung-id.

rid = "<topic_id>#<rung_index>"  -> maps a verdict/fix to an exact rung in a ladder file.

Modes:
  init                  -> build bankbuild/history/_audit_all.json (every rung, with rid + list index)
  integrate <wf_output> -> merge a window's {craft,fact} verdicts into _audit_results.json
  status                -> audited / flagged / verified counts
  flags                 -> print the rids needing a fix (high craft OR false fact)
  applyfix <fixes.json> -> patch [{rid, stem, choices, answer, context}] into the ladder files
"""
import json, glob, os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BH=os.path.join(ROOT,'bankbuild','history'); LAD=os.path.join(BH,'ladders')
ALL=os.path.join(BH,'_audit_all.json'); RESULTS=os.path.join(BH,'_audit_results.json')

def jload(p,d=None):
    try: return json.load(open(p,encoding='utf-8'))
    except Exception: return d
def jdump(o,p): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=True,indent=1)

def cmd_init():
    rungs=[]
    for f in sorted(glob.glob(os.path.join(LAD,'*.json'))):
        tid=os.path.splitext(os.path.basename(f))[0]
        d=jload(f,{})
        for i,r in enumerate(d.get('rungs',[])):
            rungs.append({'rid':f'{tid}#{i}','topic_id':tid,'topic':d.get('name','?'),
                          'rung_idx':i,'tier':r.get('tier'),'stem':r.get('stem',''),
                          'choices':r.get('choices',[]),'answer':r.get('answer',''),
                          'context':r.get('context','')})
    jdump(rungs,ALL)
    if not os.path.exists(RESULTS): jdump({},RESULTS)
    print(f'init: {len(rungs)} rungs -> {ALL}')

def extract(w):
    res=w.get('result',w) if isinstance(w,dict) else w
    if isinstance(res,str): res=json.loads(res)
    return res

def cmd_integrate(outfile):
    w=jload(outfile)
    if w is None: print('cannot read',outfile); return
    r=extract(w); R=jload(RESULTS,{})
    nc=nf=0
    for c in r.get('craft',[]) or []:
        rid=c.get('rid')
        if rid: R.setdefault(rid,{})['craft']={'verdict':c.get('verdict'),'severity':c.get('severity'),'flaw':c.get('flaw')}; nc+=1
    for fc in r.get('fact',[]) or []:
        rid=fc.get('rid')
        if rid: R.setdefault(rid,{})['fact']={'verdict':fc.get('verdict'),'note':fc.get('note')}; nf+=1
    jdump(R,RESULTS)
    print(f'integrated craft:{nc} fact:{nf} | results now: {len(R)} rids')

def cmd_status():
    R=jload(RESULTS,{}); allr=jload(ALL,[])
    from collections import Counter
    craftd=sum(1 for v in R.values() if 'craft' in v); factd=sum(1 for v in R.values() if 'fact' in v)
    cflag=Counter(v['craft'].get('severity') for v in R.values() if v.get('craft',{}).get('verdict')=='flag')
    fbad=Counter(v['fact'].get('verdict') for v in R.values() if v.get('fact',{}).get('verdict') in ('false','unsupported'))
    print(f'total rungs: {len(allr)}')
    print(f'craft audited: {craftd} ({100*craftd//max(1,len(allr))}%) | flags {dict(cflag)}')
    print(f'fact  audited: {factd} ({100*factd//max(1,len(allr))}%) | bad {dict(fbad)}')

def cmd_gaps():
    """Contiguous index ranges (into _audit_all.json order) missing a craft OR fact verdict.
    Used for the end-of-sweep reconciliation pass: re-run the workflow over each range
    (integrate is idempotent, so already-covered rungs in the range are just refreshed)."""
    R=jload(RESULTS,{}); allr=jload(ALL,[])
    miss=[i for i,row in enumerate(allr) if 'craft' not in R.get(row['rid'],{}) or 'fact' not in R.get(row['rid'],{})]
    ranges=[]
    for i in miss:
        if ranges and i==ranges[-1][1]+1: ranges[-1][1]=i
        else: ranges.append([i,i])
    out=[{'start':a,'count':b-a+1} for a,b in ranges]
    print(json.dumps(out))
    cm=sum(1 for i,row in enumerate(allr) if 'craft' not in R.get(row['rid'],{}))
    fm=sum(1 for i,row in enumerate(allr) if 'fact' not in R.get(row['rid'],{}))
    print(f'missing: craft {cm}, fact {fm}; {len(miss)} rungs in {len(out)} ranges')

def cmd_flags():
    R=jload(RESULTS,{})
    fix=[rid for rid,v in R.items()
         if (v.get('craft',{}).get('verdict')=='flag' and v['craft'].get('severity')=='high')
         or (v.get('fact',{}).get('verdict')=='false')]
    print(json.dumps(sorted(fix)))
    print('count:',len(fix))

def cmd_applyfix(fixes_path):
    fixes=jload(fixes_path,[]); applied=skipped=0
    cache={}
    for fx in fixes:
        rid=fx.get('rid');
        if not rid or '#' not in rid: skipped+=1; continue
        if fx.get('answer') not in fx.get('choices',[]) or len(fx.get('choices',[]))!=4: skipped+=1; continue
        tid,idx=rid.rsplit('#',1); idx=int(idx); f=os.path.join(LAD,tid+'.json')
        if not os.path.exists(f): skipped+=1; continue
        d=cache.get(f) or jload(f); cache[f]=d
        if 0<=idx<len(d.get('rungs',[])):
            r=d['rungs'][idx]; r['stem']=fx['stem']; r['choices']=fx['choices']; r['answer']=fx['answer']
            if fx.get('context'): r['context']=fx['context']
            applied+=1
        else: skipped+=1
    for f,d in cache.items(): jdump(d,f)
    print(f'applied {applied}, skipped {skipped}')

if __name__=='__main__':
    c=sys.argv[1] if len(sys.argv)>1 else 'status'
    {'init':cmd_init,'integrate':lambda:cmd_integrate(sys.argv[2]),'status':cmd_status,
     'gaps':cmd_gaps,'flags':cmd_flags,'applyfix':lambda:cmd_applyfix(sys.argv[2])}.get(c,cmd_status)()
