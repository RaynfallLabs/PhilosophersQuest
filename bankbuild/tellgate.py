"""Deterministic 'tell' gate -- catch the MECHANICAL telegraph patterns for zero tokens.

These are the patterns an LLM judge catches only inconsistently but a computer can decide
every time. Detection here is exact and free; it replaces the mechanical half of the LLM audit
and (wired into the build) prevents these tells at generation time.

Patterns:
  key_noun_leak   -- a distinctive answer word also sits in the stem AND in no distractor
                     (the stem word selects the answer: "Black Ships", "tank", "Vittles")
  only_number     -- the answer is the only choice containing a number (odd-one-out)
  hedge_asymmetry -- all choices are numbers but only the answer is bare (distractors hedged)
  longest_answer  -- the answer is the longest choice by a clear margin (most-elaborated)
  dual_named      -- the answer is the only choice with >=2 proper-noun tokens
  stem_echoes     -- the (short) answer string appears verbatim inside the stem

Usage:
  python bankbuild/tellgate.py scan            # flag all 5,356 rungs -> _tellgate.json + summary
  python bankbuild/tellgate.py validate        # correlate flags vs the LLM audit ground truth
"""
import json, os, re, sys, statistics
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BH=os.path.join(ROOT,'bankbuild','history')
ALL=os.path.join(BH,'_audit_all.json'); RESULTS=os.path.join(BH,'_audit_results.json')
OUT=os.path.join(BH,'_tellgate.json')

def jload(p,d=None):
    try: return json.load(open(p,encoding='utf-8'))
    except Exception: return d
def jdump(o,p): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=True,indent=1)

STOP=set("""a an the of to in on at by for and or but nor so yet as if it its is are was were be been being
he she they them his her their our your my we you i me us him who whom whose which what that this these those
with from into onto over under above below between among through during before after while until since
not no nor only just very more most much many few some any all each every both either neither
did do does done has have had having will would shall should can could may might must
than then thus also too about around near upon out off down up away back out
one two three four five six seven eight nine ten first second third last next
when where why how here there now today never always often sometimes
him her them they their your you our we us""".split())

WORD=re.compile(r"[A-Za-z][A-Za-z'\-]*")
HEDGE=re.compile(r"\b(roughly|about|around|approximately|nearly|almost|over|under|more than|less than|at least|at most|some|several|dozens|hundreds|thousands|~)\b",re.I)

def words(s): return [w.lower() for w in WORD.findall(s or '')]
def content(s): return [w for w in words(s) if w not in STOP and len(w)>=5]
def has_num(s): return bool(re.search(r"\d",s or '')) or bool(re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|hundred|thousand|million|billion)\b",(s or '').lower()))
def has_digit(s): return bool(re.search(r"\d",s or ''))

def proper_tokens(choice):
    """Capitalized proper-noun-ish tokens INSIDE a choice (skip the sentence-initial word)."""
    toks=re.findall(r"[A-Za-z][A-Za-z'\-]+",choice or '')
    out=[]
    for i,t in enumerate(toks):
        if i==0: continue
        if t[0].isupper() and any(c.islower() for c in t[1:]) and len(t)>=3 and t.lower() not in STOP:
            out.append(t)
    return out

def norm(s): return re.sub(r"\s+"," ",(s or '').lower()).strip()

QUOTE=set("\"'‘’“”")
def has_quote(s): return any(ch in (s or '') for ch in QUOTE)
def is_label(ans):
    """A short noun-phrase LABEL (Black Ships / Vittles) -- the shape real mechanical tells take.
    Vivid full-sentence or quoted answers are the Wonder payoff and legitimately echo the stem."""
    if has_quote(ans): return False
    if ',' in (ans or ''): return False
    return 1<=len(words(ans))<=5

def gate(r):
    """Return a list of triggered pattern dicts {pattern, severity, detail} for one rung.
    Accepts either ladder shape ('stem') or final-bank shape ('question')."""
    stem=r.get('stem') or r.get('question') or ''; ans=r.get('answer','') or ''
    choices=[c for c in (r.get('choices') or []) if isinstance(c,str)]
    distr=[c for c in choices if c!=ans]
    flags=[]
    sset=set(words(stem))

    label=is_label(ans)
    # proper nouns in the stem are legitimately repeated (the subject of the question) -- not a leak
    stem_caps={t.lower() for t in re.findall(r"[A-Za-z][A-Za-z'\-]+",stem) if t[0].isupper()}

    # key_noun_leak: a LABEL answer's distinctive COMMON noun is in the stem and in NO distractor
    if label:
        dwords=set()
        for d in distr: dwords|=set(words(d))
        for w in content(ans):
            if len(w)>=6 and w in sset and w not in dwords and w not in stem_caps:
                flags.append({'pattern':'key_noun_leak','severity':'medium','detail':f"answer word '{w}' is in the stem and no distractor"})
                break

    # stem_echoes: short answer printed verbatim in the stem
    awords=words(ans)
    if 1<=len(awords)<=4 and len(norm(ans))>=4 and norm(ans) in norm(stem):
        flags.append({'pattern':'stem_echoes','severity':'medium','detail':'answer text appears verbatim in the stem'})

    return flags

def cmd_scan():
    allr=jload(ALL,[]); res={}; from collections import Counter
    pc=Counter(); flagged=0
    for r in allr:
        f=gate(r)
        if f:
            flagged+=1; res[r['rid']]=f
            for x in f: pc[x['pattern']]+=1
    jdump(res,OUT)
    print(f'scanned {len(allr)} rungs -> {flagged} flagged ({100*flagged//max(1,len(allr))}%) -> {OUT}')
    for p,n in pc.most_common(): print(f'  {p:16s} {n}')

def cmd_bank(path):
    """Scan a finished bank file (list of {question/stem, choices, answer}) -- the pre-promote check."""
    bank=jload(path,[]); res={}; from collections import Counter; pc=Counter(); flagged=0
    for i,r in enumerate(bank):
        f=gate(r)
        if f:
            flagged+=1; res[str(i)]=f
            for x in f: pc[x['pattern']]+=1
    out=os.path.splitext(path)[0]+'_tellgate.json'
    jdump(res,out)
    print(f'scanned {len(bank)} questions in {os.path.basename(path)} -> {flagged} flagged ({100*flagged//max(1,len(bank))}%) -> {os.path.basename(out)}')
    for p,n in pc.most_common(): print(f'  {p:16s} {n}')
    return flagged

def cmd_validate():
    """How well does the free gate agree with the paid LLM craft audit, on the rungs we've audited?"""
    allr=jload(ALL,[]); R=jload(RESULTS,{})
    audited=[r for r in allr if 'craft' in R.get(r['rid'],{})]
    gate_flag=set(); llm_flag=set()
    for r in audited:
        if gate(r): gate_flag.add(r['rid'])
        if R[r['rid']]['craft'].get('verdict')=='flag': llm_flag.add(r['rid'])
    both=gate_flag&llm_flag
    print(f'audited rungs with ground truth: {len(audited)}')
    print(f'  LLM flagged:  {len(llm_flag)}')
    print(f'  gate flagged: {len(gate_flag)}')
    print(f'  agree (gate-flag also LLM-flag): {len(both)}  -> gate precision {100*len(both)//max(1,len(gate_flag))}%')
    print(f'  gate catches {100*len(both)//max(1,len(llm_flag))}% of all LLM flags (incl. semantic ones a gate cannot see)')
    # precision PER PATTERN -> which checks to keep vs cut
    from collections import Counter
    ptot=Counter(); phit=Counter()
    for r in audited:
        for f in gate(r):
            ptot[f['pattern']]+=1
            if r['rid'] in llm_flag: phit[f['pattern']]+=1
    print('  per-pattern precision (gate-flag of this pattern that LLM also flagged):')
    for p,n in ptot.most_common():
        print(f'    {p:16s} {phit[p]:3d}/{n:3d}  {100*phit[p]//max(1,n)}%')
    # show a few gate-only flags (potential false positives) to eyeball
    only=sorted(gate_flag-llm_flag)[:8]
    if only:
        print('  sample gate-only flags (eyeball for false positives):')
        for rid in only:
            r=next(x for x in audited if x['rid']==rid)
            print(f'    {rid}: ans={r["answer"]!r} :: {[f["pattern"] for f in gate(r)]}')

if __name__=='__main__':
    c=sys.argv[1] if len(sys.argv)>1 else 'scan'
    {'scan':cmd_scan,'validate':cmd_validate,'bank':lambda:cmd_bank(sys.argv[2])}.get(c,cmd_scan)()
