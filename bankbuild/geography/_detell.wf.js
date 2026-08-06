export const meta = {
  name: 'geography-detell',
  description: 'Surgical de-tell of needs_review GEOGRAPHY ladders (config-driven): reviser fixes/drops ONLY flagged rungs (rest byte-identical, NO new facts), then a fresh ADVERSARIAL judge + deterministic mechanical gate confirm 0 high + 0 medium. Knowledge-subject standard: the player must KNOW the place fact, not deduce it.',
  phases: [
    { title: 'Revise', detail: 'fix/drop only flagged rungs; keep clean rungs byte-identical' },
    { title: 'Verify', detail: 'mech gate + fresh adversarial judge; pass only at 0 high + 0 medium' },
  ],
}

// args.ids = needs_review ladder ids to de-tell. args.config optional (defaults to the embedded geography config).
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const CONFIG = {
  "name": "geography",
  "tier_note": "Tiers = CONCEPTUAL difficulty (T1 = a place-fact a kid can almost picture .. T5 = layered earth-science/history-culture), grade-10 ceiling. Operative gameplay gate = TOTAL record chars (stem + 4 choices): T1<=500, T2<=620, T3<=770, T4<=900, T5<=1100; context is UNCAPPED. Geography is THRESHOLD mode; each rung a DIFFERENT wonder of the place.",
  "voice_rule": "GEOGRAPHY = PLACE -> WONDER: every rung links a real, NAMED, concrete PLACE to a real magical fact (an ancient marvel, a natural wonder, a cultural creation born there, or an earth-process). THE PLACE IS ALWAYS THE ANCHOR: a place name is visible in every stem and every ANSWER is a fact about a place, its landscape, its earth-process, its marvel, or a culture born there. ONE COHERENT WONDER PER RUNG: hook + setup + answer all about the SAME fact; never staple an unrelated detail onto a different answer. ANSWER HIERARCHY: NAMED THINGS (a specific named wonder/landform -- 'the Catacombs', 'a fjord', 'the walking moai') and VIVID PROCESSES beat bare generic labels; a BARE country name, capital, plain date, or bare superlative-pick is BANNED as an answer. Dinner Test: would a kid excitedly retell THIS answer? Scene-led, never 'What is a fjord?'/'What is the capital of X?'. DISTRACTOR & ANTI-RESTATEMENT DISCIPLINE (critical): the stem sets up the PLACE/SCENE/PUZZLE -- NEVER the SOLUTION the answer names. If the stem describes the feature/process and the answer merely names it, that is RESTATEMENT and the player DEDUCES instead of KNOWS. FIX: describe the place/situation and let the ANSWER supply the fact as NEW information. ALL FOUR choices must stay LIVE -- never let a stem clause self-eliminate a distractor; distractors are adjacent-but-wrong REAL places/features. Never DEFINE a term then ask for its label. CHOICE PARITY: all four choices structurally parallel -- if the answer is a place name, all four are place names. Numbers are answers ONLY when the stem builds a specific expectation the number SHATTERS.",
  "framing": "Mostly SETTLED wonder, presented vividly, not advocacy or alarmism. Climate = descriptive earth science, never a moral fork. Stance where moral_vision commits (Age of Discovery + Western achievement celebrated; indigenous civilizations celebrated as full civilizations; colonialism honest both ways; Soviet/Maoist environmental record stated as fact; sacred sites respected on their own terms; contested borders named as timeless geographic fact). The answer is always the PLACE, never an adjacent human-policy layer."
};
const CFG = A.config || CONFIG;
const IDS = Array.isArray(A.ids) ? A.ids : [];
const SUBJECT  = CFG.name || 'geography';
const VOICE    = CFG.voice_rule || '';
const FRAMING  = CFG.framing || '';
const TIERNOTE = CFG.tier_note || 'Tiers = conceptual difficulty, grade-10 ceiling.';
const NRDIR = `C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\${SUBJECT}\\needs_review`;

const RULES = `THE BANK: a ${SUBJECT} quiz bank a father is building for HIS OWN KIDS. ${TIERNOTE}

CONTROLLING VOICE (the soul of this subject's answers):
${VOICE}

THE CRAFT RULES (each a hard requirement):
1. LEAD WITH THE SUBJECT (no dangling pronoun before the named place; parse in ONE forward pass).
2. CHOICE-FORMAT PARITY -- all four choices structurally parallel (similar length, same name-count, same shape); the answer is NEVER the structural odd-one-out (the only long/proper-named/full-sentence/number-bearing one).
3. NO LEXICAL/CATEGORY TELEGRAPH. Kill the recurring leaks: (i) RESTATEMENT -- the answer must not restate a clause the stem already gave (stem describes the feature/process/effect, answer merely names it); (ii) DEFINE-THEN-LABEL -- the stem must not fully describe a thing then ask only for its name/term; (iii) TOPIC-NAME MATCH -- the answer is not the topic's own name or a word just taught; (iv) LONE STEM-ANCHOR -- the answer must not be the only choice tied to something in the stem while distractors float free. The player must KNOW the answer, not deduce it from a stem word.
4. ECONOMY. Cut superlatives/qualifiers that add nothing.
6. TWO QUESTION SHAPES, NEVER THE COY HEDGE (general stem + full-payoff answer, OR specific stem + pointed sub-question; never narrate the SHAPE of the answer).
8. SCENE-SETTING MUST ORIENT (which place this is, what's remarkable, why it matters) -- keep the vivid scene, it is the wonder.
10. THE ANSWER MUST ITSELF BE THE PAYOFF the voice prizes (the memorable place fact / named wonder), never a dead label/bare superlative/bare date/bare country.
13. NO LOGICAL TELEGRAPH. Every distractor must be a LIVE, plausible option given everything the stem says. Kill: SELF-ELIMINATION (a stem premise rules a distractor dead); ENUMERATION (the stem lists items matching the distractors, leaving the answer the only un-listed one); CATEGORY-MATCH (only the answer fits a category the stem names); EFFECT/GOAL-MATCH (the stem states the outcome only the answer achieves).

VALUES: ${FRAMING}

FACTUAL INTEGRITY: do NOT introduce, change, or invent any factual claim. The keyed place facts were already researched, sourced, and judged correct -- preserve every keyed FACT exactly. You are removing TELEGRAPHS, not re-researching.`;

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

function reviserPrompt(id, priorFlags, isFinal){ return `You are the SURGICAL DE-TELL reviser for a needs_review ${SUBJECT} ladder. A strict adversarial judge flagged a few rungs for TELEGRAPHS -- the answer can be picked WITHOUT knowing the place fact. Remove those telegraphs while PRESERVING the vivid content.

STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {rungs, unresolved}. "unresolved" lists the flags (tier + the leak). Non-ASCII prints as \\uXXXX.

${RULES}

WHAT IS / ISN'T A TELL (this is a KNOWLEDGE subject -- the player must KNOW the place fact, not DEDUCE it from the stem):
- A real TELL is when the answer is pickable WITHOUT knowing the place fact: (a) RESTATEMENT -- the stem describes the feature/process/effect and the answer merely names it; (b) DEFINE-THEN-LABEL -- the stem fully describes a thing then asks only for its name/term; (c) ODD-ONE-OUT -- the answer is the structural standout (the only proper name, number, long one, different shape); (d) a STEM WORD hands over the answer; (e) the distractors are OFF-TOPIC / factually dead / SELF-ELIMINATE against a stem premise, or the stem ENUMERATES items matching the distractors so the answer is the only un-listed one.
- It is GOOD to set a vivid scene -- do NOT strip the wonder. The fix is to move the giveaway OUT of the stem so the ANSWER carries the place fact as NEW information, and to make all four distractors LIVE.

HOW TO FIX (fix > drop; reconceive, don't patch):
- RESTATEMENT / DEFINE-THEN-LABEL: reword the STEM so it sets up the place/scene/challenge WITHOUT stating the feature or naming the term; let the ANSWER supply the place fact as new information. If a rung is fundamentally 'describe X then name X', reconceive it to test a fact the player must actually KNOW.
- PARITY (sacred): after editing, ALL FOUR choices share the same opening, grammatical shape, and similar length -- the answer must NEVER be the odd-one-out. If the answer is a place name, make all four place names; if a phrase, all four phrases. Reword the others to match.
- DEAD / SELF-ELIMINATING DISTRACTORS: replace them with LIVE, plausible wrong place-facts a kid could actually believe -- never one the stem's own words rule out. The kid must KNOW the right one, not eliminate the impossible.
- Reword the STEM only enough to stop it stating/echoing the answer; keep the vivid scene and the named place.
- NEVER introduce, change, or invent a FACT. The keyed place fact is already sourced -- preserve it exactly.
- Fix ONLY flagged rungs (+ any sibling tell you spot); leave clean rungs BYTE-IDENTICAL.
${isFinal ? `\nTHIS IS THE FINAL ROUND: any rung you cannot make FULLY clean right now, DROP it entirely (return fewer rungs). Do NOT return a still-telegraphed rung.` : ``}${priorFlags && priorFlags.length ? `\nThe previous revision STILL had these flags -- fix or drop them this time:\n${JSON.stringify(priorFlags)}` : ``}
Return the FULL ladder (fixed rungs corrected, others byte-identical, answer still == one of its 4 choices).`; }

function advPrompt(id, rungs, gate){ return `You are an INDEPENDENT, SKEPTICAL auditor. This ${SUBJECT} ladder was just DE-TELLED. Do NOT rubber-stamp -- verify the telegraphs are gone and no new one was introduced. Topic id: "${id}".
${RULES}
THE STANDARD (this is a KNOWLEDGE subject): the player must KNOW the place fact -- flag a rung when the answer can be picked WITHOUT knowing it:
(a) the answer RESTATES a clause the stem gave, or the stem DEFINES-THEN-asks-the-LABEL; (b) the answer is the structural ODD-ONE-OUT (shape / length / lone proper-name / lone number); (c) a STEM WORD hands over the answer; (d) the three distractors are off-topic / factually dead / self-eliminate against a stem premise, or the stem ENUMERATES the distractors, so the answer survives by elimination. Do NOT flag a rung merely for having a vivid scene when the answer is a genuine place fact the player must KNOW and the three distractors are LIVE, plausible wrong facts.
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
  // deterministic final drop: shed the rungs the judge STILL flags after 2 rounds
  const dropIdx = new Set((flags||[]).map(f=>f.idx).filter(i=>typeof i==='number'));
  const kept = (cur && cur.rungs ? cur.rungs : []).filter((_,i)=>!dropIdx.has(i));
  if (dropIdx.size && kept.length)
    return {id, status:'passed', ladder:{rungs:kept}, unresolved:[], notes:[`dropped ${dropIdx.size} stuck rung(s) after 2 de-tell rounds`], rounds:2};
  return {id, status:'needs_review', ladder:cur, unresolved:lastNotes, notes:[], rounds:2};
}

if (!IDS.length){ log('ERROR: no args.ids passed.'); return {error:'no-ids'}; }
phase('Revise');
log(`${SUBJECT} de-tell: ${IDS.length} needs_review ladders -> ${IDS.join(', ')}`);
const results = await parallel(IDS.map(id => () => detell(id)));
const ok = results.filter(r=>r&&r.status==='passed').length;
phase('Verify');
log(`de-tell done: ${ok}/${IDS.length} now PASS (0 high + 0 medium). ` + results.map(r=>`${r&&r.id}:${r&&r.status}(${r&&(r.ladder.rungs||[]).length})`).join(' '));
return {subject:SUBJECT, results};
