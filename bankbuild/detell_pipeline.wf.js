export const meta = {
  name: 'philosophy-detell',
  description: 'Surgical de-tell of needs_review philosophy ladders: reviser fixes/drops ONLY the flagged rungs (rest byte-identical, NO new facts), then a fresh ADVERSARIAL judge + deterministic mechanical gate confirm 0 high + 0 medium.',
  phases: [
    { title: 'Revise', detail: 'fix/drop only flagged rungs; keep the clean rungs byte-identical' },
    { title: 'Verify', detail: 'mech gate + fresh adversarial judge; pass only at 0 high + 0 medium' },
  ],
}

// args.ids = list of needs_review ladder ids to de-tell (the file is bankbuild/philosophy/needs_review/<id>.json)
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const SUBJECT = 'philosophy';
const NRDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\philosophy\\needs_review';

// --- philosophy voice (mirrors bankbuild/subjects/philosophy.json) ---
const VOICE = `PHILOSOPHY = REASONING MOVES + WONDER, never name-recall trivia. TWO shapes both welcome: (A) STORY/DRAMA -- a thinker's life/deed/death told as a vivid scene; the NAMED subject LEADS the stem (names ARE allowed); the answer is the most memorable specific MOVE or cool fact. (B) MOVE/SCENARIO -- a concrete scene embodies a reasoning move, fallacy, or dilemma; the four choices are competing POSITIONS in PLAIN language (NEVER -ism labels or jargon a kid must decode); the answer is the move that survives scrutiny. CONTESTED metaphysics/ethics: impose NO verdict -- put the claim in a CHARACTER's mouth, choices are competing schools, key the one matching the character's reasoning (the opposite view must not be markable wrong). FALLACY answer = the SUBSTANTIVE COLLAPSE spelled out, NOT the label (label -> context). Distractors are real rival positions, tight length-parity.`;
const FRAMING = `Never impose a verdict on a genuinely contested moral/political/metaphysical question. Method neutral, content substantive; never warp a topic to force a principle in.`;
const TIERNOTE = `Tiers = CONCEPTUAL difficulty (T1 lived/concrete .. T5 sophisticated disputes), grade-10 ceiling. Total-record char caps (stem+4 choices): T1<=660,T2<=770,T3<=930,T4<=1100,T5<=1200; context uncapped.`;

const RULES = `THE BANK: a ${SUBJECT} quiz bank a father is building for HIS OWN KIDS. ${TIERNOTE}

CONTROLLING VOICE (the soul of this subject's answers):
${VOICE}

THE CRAFT RULES (each a hard requirement):
1. LEAD WITH THE SUBJECT (no dangling pronoun before the named subject; parse in ONE forward pass).
2. CHOICE-FORMAT PARITY -- all four choices structurally parallel (similar length, same name-count, same shape); the answer is NEVER the structural odd-one-out (the only long/dual-named/full-sentence/number-bearing one).
3. NO LEXICAL/CATEGORY TELEGRAPH. Kill the three recurring leaks: (i) RESTATEMENT -- the answer must not restate a discriminating clause the stem already gave; (ii) TOPIC-NAME MATCH -- the answer is not the topic's own name or a word just taught; (iii) LONE STEM-ANCHOR -- the answer must not be the only choice tied to something in the stem while the distractors float free. The player must KNOW the answer, not deduce it from a stem word.
4. ECONOMY. Cut superlatives/qualifiers that add nothing.
5. NO FALSE-FRIEND VOCAB (no archaic/technical sense whose modern meaning differs).
6. TWO QUESTION SHAPES, NEVER THE COY HEDGE (general stem + full-payoff answer, OR specific stem + pointed sub-question; never narrate the SHAPE of the answer).
8. SCENE-SETTING MUST ORIENT (who/what, what's at stake, why this moment).
10. THE ANSWER MUST ITSELF BE THE PAYOFF the voice prizes, never a dead label.
12. ACTIVE VOICE / ASSIGN RESPONSIBILITY (name the actor).
13. NO LOGICAL TELEGRAPH. Every distractor must be a LIVE, plausible option given everything the stem says. ENUMERATION is the sharpest form: never list items in the stem that match the distractors, leaving the answer the only un-listed one. Also kill COUNT telegraphs (e.g. 'six-word motto' when only the answer has six words), CATEGORY-MATCH (only the answer fits a category the stem names), and EFFECT/GOAL-MATCH (the stem states the outcome only the answer achieves).
14. POINTED CLOSER -- the closing question is POINTED + CONCRETE about something specific, never a weasel ('what's the takeaway/lesson/significance?').

VALUES: never impose a verdict on a genuinely contested question -- attribute claims to a person, present competing views. ${FRAMING}

FACTUAL INTEGRITY: do NOT introduce, change, or invent any factual claim. The keyed answers were already researched, sourced, and judged factually correct -- preserve every keyed FACT exactly. You are removing TELEGRAPHS, not re-researching.`;

const RUNG = { type:'object', additionalProperties:false, properties:{
  tier:{type:'number'}, stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4, maxItems:4},
  answer:{type:'string'}, context:{type:'string'}, legend:{type:'boolean'}
}, required:['tier','stem','choices','answer','context','legend'] };
const LADDER = { type:'object', additionalProperties:false, properties:{ rungs:{type:'array', items:RUNG} }, required:['rungs'] };
const VERDICTS = { type:'object', additionalProperties:false, properties:{
  ladder_ok:{type:'boolean'},
  verdicts:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    tier:{type:'number'}, idx:{type:'number'}, verdict:{type:'string', enum:['keep','flag']},
    severity:{type:'string', enum:['high','medium','low','none']},
    rules_flagged:{type:'array', items:{type:'string'}}, primary_flaw:{type:'string'}, fix:{type:'string'}
  }, required:['tier','idx','verdict','severity','rules_flagged','primary_flaw','fix']}}
}, required:['ladder_ok','verdicts'] };

async function tryAgent(prompt, opts, ok, tries){
  let last = null;
  for (let a = 0; a < (tries || 3); a++){
    const r = await agent(prompt, { ...opts, label: opts.label + (a ? `.r${a}` : '') }).catch(() => null);
    if (r && (!ok || ok(r))) return r;
    last = r;
  }
  return last;
}

// deterministic mechanical gate (mirror of bank_pipeline.wf.js mechGate)
const STOPJS = new Set(("a an the of to in on at by for and or but nor so yet as if it its is are was were be been being he she "+
  "they them his her their our your my we you i me us him who whom whose which what that this these those with from into onto over "+
  "under above below between among through during before after while until since not no only just very more most much many few some "+
  "any all each every both either neither did do does done has have had having will would shall should can could may might must than "+
  "then thus also too about around near upon out off down up away back when where why how here there now today never always often "+
  "one two three four five six seven eight nine ten first second third last next").split(/\s+/));
function wordsJS(s){ return ((s||'').toLowerCase().match(/[a-z][a-z'\-]*/g)) || []; }
function isLabelJS(ans){ if (/["'‘’“”]/.test(ans||'')) return false; if ((ans||'').includes(',')) return false; const n = wordsJS(ans).length; return n>=1 && n<=5; }
function mechGate(rungs){
  const out = [];
  (rungs||[]).forEach((r, idx) => {
    const ans=r.answer||'', stem=r.stem||'', choices=(r.choices||[]).filter(c=>typeof c==='string');
    const distr=choices.filter(c=>c!==ans);
    const sset=new Set(wordsJS(stem));
    const stemCaps=new Set(((stem.match(/[A-Za-z][A-Za-z'\-]+/g))||[]).filter(t=>/[A-Z]/.test(t[0])).map(t=>t.toLowerCase()));
    if (isLabelJS(ans)){
      const dset=new Set(); distr.forEach(d=>wordsJS(d).forEach(w=>dset.add(w)));
      for (const w of wordsJS(ans)){
        if (w.length>=6 && !STOPJS.has(w) && sset.has(w) && !dset.has(w) && !stemCaps.has(w)){
          out.push({tier:r.tier, idx, pattern:'key_noun_leak', flaw:`answer word "${w}" is in the stem and in no distractor`}); break;
        }
      }
    }
    const an=(ans||'').toLowerCase().replace(/\s+/g,' ').trim(), sn=(stem||'').toLowerCase().replace(/\s+/g,' ');
    const aw=wordsJS(ans);
    if (aw.length>=1 && aw.length<=4 && an.length>=4 && sn.includes(an))
      out.push({tier:r.tier, idx, pattern:'stem_echoes', flaw:'the answer text appears verbatim in the stem'});
  });
  return out;
}

function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${NRDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'rungs':d['rungs'],'unresolved':d.get('unresolved',[])}))"`; }

function reviserPrompt(id, priorFlags, isFinal){ return `You are the SURGICAL DE-TELL reviser for a needs_review ${SUBJECT} ladder. A strict adversarial judge flagged a few rungs for TELEGRAPHS -- the answer can be picked WITHOUT engaging the reasoning. Remove those telegraphs while PRESERVING the vivid content.

STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {rungs, unresolved}. "unresolved" lists the flags (tier + the leak). Non-ASCII prints as \\uXXXX.

${RULES}

WHAT IS / ISN'T A TELL (this is a REASONING subject):
- It is GOOD and intended that a careful thinker can REASON to the answer from the scenario -- that is the skill. Do NOT flatten a good reasoning rung or strip its scene to "fix" it.
- A real TELL is ONLY when the answer is pickable WITHOUT reasoning: (a) it ECHOES a distinctive stem phrase; (b) it is the structural ODD-ONE-OUT (the only short/long one, the only 'Nothing--', the only one with an appositive, a different grammatical shape); (c) a STEM WORD hands over a label answer; (d) the distractors are OFF-TOPIC / factually dead / self-eliminate against a stem premise so the answer wins by elimination.

HOW TO FIX (fix > drop; reconceive, don't patch):
- ECHO: reword the ANSWER to state the actual philosophical MOVE in DIFFERENT words than the stem -- never reuse the stem's distinctive phrase.
- PARITY (sacred): after editing, ALL FOUR choices must share the same opening, grammatical shape, and similar length -- the answer must NEVER be the odd-one-out. If you reword one choice, reword the others to match. NEVER add a descriptive appositive/clause to a choice that names a role/trait the stem mentions (e.g. never label a choice 'a pupil' when the stem says 'his student').
- DEAD/SELF-ELIMINATING DISTRACTORS: replace them with LIVE, on-topic rival readings a careful kid could actually pick -- positions the scenario does NOT obviously refute. The kid must REASON, not eliminate the absurd.
- Reword the STEM only enough to stop it stating/echoing the discriminating point; keep the vivid scene.
- NEVER introduce, change, or invent a FACT. The keyed fact is already sourced -- preserve it exactly.
- Fix ONLY flagged rungs (+ any sibling tell you spot); leave clean rungs BYTE-IDENTICAL.
${isFinal ? `\nTHIS IS THE FINAL ROUND: any rung you cannot make FULLY clean right now, DROP it entirely (return fewer rungs). Do NOT return a still-telegraphed rung.` : ``}${priorFlags && priorFlags.length ? `\nThe previous revision STILL had these flags -- fix or drop them this time:\n${JSON.stringify(priorFlags)}` : ``}
Return the FULL ladder (fixed rungs corrected, others byte-identical, answer still == one of its 4 choices).`; }

function advPrompt(id, rungs, gate){ return `You are an INDEPENDENT, SKEPTICAL auditor. This ${SUBJECT} ladder was just DE-TELLED. Do NOT rubber-stamp -- verify the telegraphs are gone and no new one was introduced. Topic id: "${id}".
${RULES}
THE STANDARD (this is a REASONING subject): it is CORRECT and intended that a careful thinker can reason to the answer from a well-built scenario -- that is the skill being tested, NOT a telegraph. Flag a rung ONLY when the answer can be picked WITHOUT engaging the reasoning:
(a) a verbatim/near-verbatim ECHO of a distinctive stem phrase in the answer; (b) the answer is the structural ODD-ONE-OUT (shape / length / a lone appositive); (c) a STEM WORD hands over a label answer; (d) the three distractors are off-topic / factually dead / self-eliminate against a stem premise, so the answer survives by elimination. Do NOT flag a rung merely because the scenario logically supports the answer when the three distractors are LIVE, on-topic rival positions a careful kid could pick.
LADDER (idx = position in this array): ${JSON.stringify(rungs)}
${gate.length ? `A deterministic scanner flagged these (verify each -- ~76% precise, CONFIRM a real leak or CLEAR a false positive on a legitimately vivid answer):\n${JSON.stringify(gate)}` : `The mechanical scanner found nothing -- still hunt the SEMANTIC tells it cannot see.`}
Do NOT re-litigate factual sourcing (facts are pre-verified) unless a fact was clearly broken by the edit.
For EACH rung: verdict 'keep' or 'flag'; if flag: severity (high/medium/low) + rules_flagged + primary_flaw + fix. ladder_ok = true ONLY if nothing is HIGH or MEDIUM.`; }

async function detell(id){
  let cur = null, flags = null, lastNotes = [];
  for (let r = 0; r < 2; r++){
    const rev = await tryAgent(reviserPrompt(id, flags, r===1), {schema:LADDER, phase:'Revise', label:`rev:${id.slice(0,16)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
    if (!rev || !rev.rungs || !rev.rungs.length) return {id, status:'needs_review', ladder:cur||{rungs:[]}, unresolved:['reviser-failed'], notes:[]};
    cur = rev;
    const gate = mechGate(cur.rungs);
    const v = await tryAgent(advPrompt(id, cur.rungs, gate), {schema:VERDICTS, phase:'Verify', label:`adv:${id.slice(0,16)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts));
    if (!v) return {id, status:'needs_review', ladder:cur, unresolved: gate.map(g=>`gate:${g.pattern}@${g.idx}`), notes:[]};
    const fl = (v.verdicts||[]).filter(x=>x.verdict==='flag');
    const high = fl.filter(x=>x.severity==='high'), med = fl.filter(x=>x.severity==='medium'), low = fl.filter(x=>x.severity==='low');
    if (high.length===0 && med.length===0)
      return {id, status:'passed', ladder:cur, unresolved:[], notes: low.map(f=>`T${f.tier}(low):${f.primary_flaw}`), rounds:r+1};
    flags = [...high,...med].map(f=>({tier:f.tier, idx:f.idx, severity:f.severity, flaw:f.primary_flaw, fix:f.fix}));
    lastNotes = flags.map(f=>`T${f.tier}(${f.severity}):${f.flaw}`);
  }
  // deterministic final drop: shed the rungs the judge STILL flags after 2 rounds (the others were just
  // judged 'keep' = clean), so the ladder converges to passed by losing at most a rung or two.
  const dropIdx = new Set((flags||[]).map(f=>f.idx).filter(i=>typeof i==='number'));
  const kept = (cur && cur.rungs ? cur.rungs : []).filter((_,i)=>!dropIdx.has(i));
  if (dropIdx.size && kept.length)
    return {id, status:'passed', ladder:{rungs:kept}, unresolved:[], notes:[`dropped ${dropIdx.size} stuck rung(s) after 2 de-tell rounds`], rounds:2};
  return {id, status:'needs_review', ladder:cur, unresolved:lastNotes, notes:[], rounds:2};
}

if (!IDS.length){ log('ERROR: no args.ids passed.'); return {error:'no-ids'}; }
phase('Revise');
log(`philosophy de-tell: ${IDS.length} needs_review ladders -> ${IDS.join(', ')}`);
const results = await parallel(IDS.map(id => () => detell(id)));
const ok = results.filter(r=>r&&r.status==='passed').length;
phase('Verify');
log(`de-tell done: ${ok}/${IDS.length} now PASS (0 high + 0 medium). ` + results.map(r=>`${r&&r.id}:${r&&r.status}(${r&&(r.ladder.rungs||[]).length})`).join(' '));
return {subject:SUBJECT, results};
