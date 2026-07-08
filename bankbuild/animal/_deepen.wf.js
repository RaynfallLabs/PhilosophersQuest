export const meta = {
  name: 'animal-deepen',
  description: 'Additively deepen existing animal ladders: research NEW advanced facts (Grokipedia FIRST) not already covered, author N fresh T4/T5 rungs, adversarial-judge + gate + revise, return only clean new rungs. Never touches existing rungs.',
  phases: [
    { title: 'Research', detail: 'advanced T4/T5 facts not already in the ladder (Grokipedia first)' },
    { title: 'Author',   detail: 'N new upper-tier rungs, no duplication of covered facts' },
    { title: 'Verify',   detail: 'adversarial judge + gate + revise; drop any that still leak' },
  ],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const NNEW = Number(A.count) || 2;
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\animal\\ladders';
const QUEUE = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\animal\\_queue.json';

const CONFIG = {
  voice_rule: "ANIMAL = pure animal-KNOWLEDGE: amazing biology, behavior, senses, adaptation, life cycle, paleobiology, how creatures SURVIVE -- plus the truly BIZARRE. THE ANIMAL IS ALWAYS THE ANCHOR: every rung's ANSWER is a fact about an animal. ONE COHERENT WONDER PER RUNG: hook + setup + answer all about the SAME fact; never staple an unrelated detail onto a different answer. WONDER PATTERN answer hierarchy: NAMED THINGS > VIVID ACTIONS/ADAPTATIONS > CONCRETE OBJECTS > NUMBERS (only when the stem CONSTRUCTS the number as a payoff; a cold number = BANNED) > GENERIC LABELS (banned). Dinner Test. Concrete handles beat jargon. DISTRACTOR & ANTI-RESTATEMENT DISCIPLINE: the stem sets up the CHALLENGE/PUZZLE, NEVER the SOLUTION the answer names; all four choices stay LIVE; never DEFINE a term then ask its label; strict choice parity; numbers only when the stem builds an expectation the number shatters. ACCURACY: real binomials; current taxonomy (Brontosaurus valid; dire wolf=Aenocyon; birds ARE theropod dinosaurs; 'T. rex' not 'T. Rex'); no anthropomorphizing as fact; flag research-in-progress honestly. NO BUTCHER-TABLE / DISSECTION FRAME: never frame a question as the player processing a corpse or a second-person 'cut it open' on a LIVING animal -- describe internal anatomy observationally ('inside the eel...'); a fossil / museum specimen / third-person historical account is fine. Extinctions reframed onto the animal.",
  framing: "Mostly SETTLED science, presented with WONDER. Evolution + deep timeline = standard science stated confidently. Reproductive/sexual diversity in OTHER species = wonder on its OWN terms, NEVER a human-sex analogy. Pleistocene overkill (Martin 1967) vs climate = both sides, no verdict. No smug voice, no anthropomorphizing, no reveal-staging. The answer is always the ANIMAL, never an adjacent human layer.",
  tier_note: "This DEEPEN pass adds UPPER-TIER rungs only: T4 (multi-step analytic, mechanism, deep evidence) and T5 (deep paleobiology, contested-debate framing, the analytic capstone). Operative gameplay gate = TOTAL record chars (stem + 4 choices): T4<=900, T5<=1100; context UNCAPPED."
};

const RULES = `THE BANK: an animal quiz bank a father is building for HIS OWN KIDS. ${CONFIG.tier_note}

CONTROLLING VOICE:
${CONFIG.voice_rule}

CRAFT RULES (each a hard requirement): 1. Lead with the subject, parse in one forward pass. 2. CHOICE PARITY -- four choices alike in length/shape/name-count; answer never the odd-one-out. 3. NO TELEGRAPH -- kill RESTATEMENT (answer restates a stem clause), DEFINE-THEN-LABEL, TOPIC-NAME MATCH, LONE STEM-ANCHOR; the player must KNOW the answer, not deduce it. 4. Economy. 6. Two shapes, never the coy hedge. 8. Scene orients (who/what the animal is, what's at stake). 10. The answer is the PAYOFF (a wonder), never a dead label/jargon term/bare number. 13. NO LOGICAL TELEGRAPH -- every distractor stays LIVE; no self-elimination, no enumeration, no category/effect-match. 14. Pointed closer.

VALUES: ${CONFIG.framing}

FACTUAL INTEGRITY: every keyed fact traces to a real source you found (Grokipedia first). NOTHING fabricated; if a fact isn't sourced, don't use it.`;

const RESEARCH = { type:'object', additionalProperties:false, properties:{
  facts:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    fact:{type:'string'}, source:{type:'string'}, difficulty:{type:'string', enum:['hard','med']},
    legend:{type:'boolean'}, confidence:{type:'string', enum:['high','medium','low']}
  }, required:['fact','source','difficulty','legend','confidence']}}
}, required:['facts'] };
const RUNG = { type:'object', additionalProperties:false, properties:{
  tier:{type:'number'}, stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4, maxItems:4},
  answer:{type:'string'}, context:{type:'string'}, legend:{type:'boolean'}
}, required:['tier','stem','choices','answer','context','legend'] };
const LADDER = { type:'object', additionalProperties:false, properties:{ rungs:{type:'array', items:RUNG} }, required:['rungs'] };
const VERDICTS = { type:'object', additionalProperties:false, properties:{
  verdicts:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    idx:{type:'number'}, verdict:{type:'string', enum:['keep','flag']}, severity:{type:'string', enum:['high','medium','low','none']}, fix:{type:'string'}
  }, required:['idx','verdict','severity','fix']}}
}, required:['verdicts'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||4);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
const STOPJS=new Set("a an the of to in on at by for and or but is are was were be been he she they them its this that with from into over under than then out up down when where why how one two three four five six seven eight nine ten".split(/\s+/));
function wordsJS(s){ return ((s||'').toLowerCase().match(/[a-z][a-z'\-]*/g))||[]; }
function isLabelJS(a){ if(/["'‘’“”]/.test(a||''))return false; if((a||'').includes(','))return false; const n=wordsJS(a).length; return n>=1&&n<=5; }
function mechGate(rungs){ const out=[]; (rungs||[]).forEach((r,idx)=>{ const ans=r.answer||'',stem=r.stem||'',ch=(r.choices||[]).filter(c=>typeof c==='string'),dis=ch.filter(c=>c!==ans); const sset=new Set(wordsJS(stem)); const caps=new Set(((stem.match(/[A-Za-z][A-Za-z'\-]+/g))||[]).filter(t=>/[A-Z]/.test(t[0])).map(t=>t.toLowerCase())); if(isLabelJS(ans)){ const dset=new Set(); dis.forEach(d=>wordsJS(d).forEach(w=>dset.add(w))); for(const w of wordsJS(ans)){ if(w.length>=6&&!STOPJS.has(w)&&sset.has(w)&&!dset.has(w)&&!caps.has(w)){ out.push({idx,flaw:`answer word "${w}" in stem, not in distractors`}); break; } } } const an=(ans||'').toLowerCase().replace(/\s+/g,' ').trim(),sn=(stem||'').toLowerCase().replace(/\s+/g,' '); if(wordsJS(ans).length<=4&&an.length>=4&&sn.includes(an)) out.push({idx,flaw:'answer appears verbatim in stem'}); }); return out; }

// python reads existing ladder (rungs) + joins the queue entry for scope/framing/name
function readCmd(id){ return `python -c "import json;lp=r'${LADDIR}\\${id}.json';d=json.load(open(lp,encoding='utf-8'));q=json.load(open(r'${QUEUE}',encoding='utf-8'));m=next((t for t in q if t['id']=='${id}'),{});import sys;sys.stdout.write(json.dumps({'name':d['name'],'scope':m.get('scope',''),'framing_note':m.get('framing_note',''),'tier_span':d.get('tier_span'),'covered':[{'tier':r['tier'],'stem':r['stem'],'answer':r['answer']} for r in d['rungs']]}))"`; }

function researchPrompt(id){ return `You are the RESEARCH stage adding DEPTH to an existing animal ladder. Accuracy is sacred.
STEP 1 -- read the topic + what's ALREADY covered (PowerShell, do not modify): ${readCmd(id)}
It prints {name, scope, framing_note, tier_span, covered:[{tier,stem,answer}]}.
STEP 2 -- research ${NNEW+3} ADVANCED, upper-tier facts about this ANIMAL topic suitable for T4-T5: a mechanism explained a step deeper, hard evidence / a landmark study, a genuine scientific debate, deep paleobiology, a quantitative surprise the stem can build to. They MUST be genuinely NEW -- NOT restating any 'covered' fact/answer above.
SOURCE PRIORITY (required): check **Grokipedia (grokipedia.com) FIRST** for every fact; prefer it over Wikipedia whenever both cover a fact; then corroborate with Wikipedia and other reputable primary sources. Cite the Grokipedia URL when it is your source.
ANTI-HALLUCINATION: every fact traces to a real source you FOUND. Better fewer than fabricated. difficulty = 'hard' (T5) or 'med' (T4).
Return the fact sheet.`; }

function authorPrompt(id, name, research){ return `You are the AUTHOR adding ${NNEW} NEW UPPER-TIER rungs to the existing animal ladder "${name}". Read the topic + covered rungs first: ${readCmd(id)}
${RULES}
SOURCED NEW FACTS (use ONLY these; nothing from memory):
${JSON.stringify(research.facts)}
Write EXACTLY ${NNEW} new rungs, each at tier 4 OR tier 5 (analytic / mechanism / deep-paleo / contested-debate). Each rung: tier, EXACTLY 4 choices, answer (== one choice verbatim), context (post-answer enrichment + the source), legend bool. HARD REQUIREMENT: each new rung must teach a DISTINCT fact NOT in the covered list, and must not duplicate another new rung. Apply every craft rule + run the self-audit (parity, no telegraph/restatement, live distractors, answer-is-the-payoff). If a fact can't make a clean upper-tier rung, drop it and return fewer.
Return {rungs:[...]}.`; }

function judgePrompt(id, name, rungs){ return `You are an INDEPENDENT, SKEPTICAL judge of ${rungs.length} NEW upper-tier rungs proposed for the animal ladder "${name}". Knowledge subject: the player must KNOW the animal fact, not DEDUCE it. Flag a rung if: the answer restates a stem clause / define-then-label; the answer is the structural odd-one-out; a stem word hands it over; the distractors self-eliminate or enumerate; the answer is a dead label/bare number; or a butcher-table/dissection frame. Also flag any that is NOT genuinely T4/T5 depth.
RUNGS (idx = position): ${JSON.stringify(rungs)}
For EACH: verdict keep/flag; if flag, severity + a one-line fix. Do not rubber-stamp.`; }

function revisePrompt(id, name, rungs, flags){ return `Revise the flagged NEW rungs for "${name}". ${RULES}
RUNGS: ${JSON.stringify(rungs)}
FLAGS to fix (idx + fix): ${JSON.stringify(flags)}
Fix ONLY flagged rungs (reword stem/choices to kill the leak, keep parity, keep the sourced FACT exact, keep tier 4/5); leave clean rungs byte-identical. Return {rungs:[...]} (same length).`; }

async function deepen(id){
  const res = await tryAgent(researchPrompt(id), {schema:RESEARCH, phase:'Research', label:`res:${id.slice(0,18)}`, model:'opus'}, x=>x&&x.facts&&x.facts.length>=1);
  if(!res||!res.facts||!res.facts.length) return {id, status:'thin', new_rungs:[]};
  const nameM = res.name || id;
  let lad = await tryAgent(authorPrompt(id, nameM, res), {schema:LADDER, phase:'Author', label:`auth:${id.slice(0,18)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
  if(!lad||!lad.rungs||!lad.rungs.length) return {id, status:'failed', new_rungs:[]};
  // verify (1 round of judge+revise, then drop stuck)
  for(let round=0; round<2; round++){
    const gate = mechGate(lad.rungs);
    const v = await tryAgent(judgePrompt(id, nameM, lad.rungs), {schema:VERDICTS, phase:'Verify', label:`judge:${id.slice(0,18)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts));
    if(!v) return {id, status:'failed', new_rungs:[], reason:'judge-unavailable'};  // never accept UNjudged rungs (e.g. a walled judge)
    const flagged = (v.verdicts||[]).filter(x=>x.verdict==='flag'&&(x.severity==='high'||x.severity==='medium'));
    const gateIdx = new Set(gate.map(g=>g.idx));
    const bad = new Set([...flagged.map(f=>f.idx), ...gateIdx]);
    if(bad.size===0) return {id, status:'passed', new_rungs:lad.rungs};
    if(round===1){ // final: drop the still-bad ones
      const kept = lad.rungs.filter((_,i)=>!bad.has(i));
      return {id, status: kept.length?'passed':'failed', new_rungs:kept, dropped:bad.size};
    }
    const fixes = [...flagged, ...gate.map(g=>({idx:g.idx, fix:'mechanical: '+g.flaw}))];
    const rev = await tryAgent(revisePrompt(id, nameM, lad.rungs, fixes), {schema:LADDER, phase:'Verify', label:`rev:${id.slice(0,18)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length===lad.rungs.length);
    if(rev&&rev.rungs) lad = rev;
  }
  return {id, status:'passed', new_rungs:lad.rungs};
}

if(!IDS.length){ log('ERROR: no args.ids'); return {error:'no-ids'}; }
phase('Research');
log(`animal deepen: adding ~${NNEW} T4/T5 rungs each to ${IDS.length} ladders (Grokipedia-first research)`);
const results = await parallel(IDS.map(id => () => deepen(id).catch(()=>({id,status:'failed',new_rungs:[]}))));
const added = results.reduce((s,r)=>s+((r&&r.new_rungs||[]).length),0);
phase('Verify');
log(`deepen done: ${results.filter(r=>r&&r.status==='passed').length}/${IDS.length} topics; ${added} new rungs total.`);
return {subject:'animal', added, results};
