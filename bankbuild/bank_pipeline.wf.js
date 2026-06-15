export const meta = {
  name: 'bank-pipeline',
  description: 'Subject-agnostic bank pipeline: research -> author -> craft-judge+revise -> ADVERSARIAL judge + deterministic mechanical gate. Clean banks by construction, any subject.',
  phases: [
    { title: 'Research', detail: 'web-sourced fact sheet per topic (anti-hallucination)' },
    { title: 'Author',   detail: 'voice-driven ladder from sourced facts, all craft rules + self-audit' },
    { title: 'Judge',    detail: 'craft judge + revise-until-clean (cap 2)' },
    { title: 'Verify',   detail: 'fresh ADVERSARIAL judge fed the mechanical-gate flags; final de-tell pass' },
  ],
}

// ---- subject config (passed in by the launcher: args.config = bankbuild/subjects/<subject>.json) ----
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const CFG = A.config || {};
const SUBJECT  = CFG.name || 'unknown';
const QUEUE    = CFG.queue;                 // path to the subject's topic queue JSON
const VOICE    = CFG.voice_rule || 'THE CONTROLLING VOICE: the answer must be the single most memorable, retellable payoff of its topic -- never a bland label/date/number when something vivid is available.';
const FRAMING  = CFG.framing || '';
const TIERNOTE = CFG.tier_note || 'Tiers = conceptual difficulty (T1 simple/concrete .. T5 analytic), grade-10 ceiling; aim ~30% of rungs at T1-T2.';
const START = Number(A.start) || 0, COUNT = Number(A.count) || 3;
const idxs = (Array.isArray(A.idxs) && A.idxs.length) ? A.idxs : Array.from({length:COUNT}, (_,i)=>START+i);

// ---- GENERIC craft rules (subject-independent). The subject's controlling voice is injected as ${VOICE}. ----
const RULES = `THE BANK: a ${SUBJECT} quiz bank a father is building for HIS OWN KIDS. ${TIERNOTE}

CONTROLLING VOICE (the soul of THIS subject's answers):
${VOICE}

THE CRAFT RULES (each a hard requirement; a rung breaking ANY is FLAGGED):
1. LEAD WITH THE SUBJECT. Never open a stem on a dangling pronoun/possessive ("At her trial...", "When he...") before the named subject appears. The deck is SHUFFLED + timed -- the stem must parse in ONE forward pass; a player cannot re-read. Lead with the named subject, or a self-standing scene with no dangling reference.
2. CHOICE-FORMAT PARITY. All four choices structurally parallel -- similar length, same name-count, same grammatical shape. The answer must NEVER be the structural odd-one-out (the only dual-named, the only long one, the only full sentence, the only one with a date/number). No skim-tell.
3. NO LEXICAL/CATEGORY TELEGRAPH. No stem word that hands over the answer: not the answer's key noun, not a category word only the answer matches ("tree" when only the answer is a tree), not a verb revealing the mechanism ("sent an armorer to DIG for it" -> "buried"), not a tone-word matching only the answer. THREE recurring high-severity leaks to kill: (i) RESTATEMENT -- the answer must not restate a discriminating clause the stem already gave (stem "buried in the grandest tomb, beside William Pitt" -> answer "Westminster Abbey, beside William Pitt" is just an echo); (ii) TOPIC-NAME MATCH -- the answer must not be the topic's own name, a word from the topic title, or a name just taught in a lower rung (a "Ghana Empire" answer in a Ghana topic is pure name-matching); (iii) LONE STEM-ANCHOR -- the answer must not be the only choice tied to anything in the stem while the three distractors float free. The player must KNOW the answer, not deduce it from a stem word.
4. ECONOMY. Cut superlatives/qualifiers that add nothing ("her MOST FAMOUS sword" when she has one famous sword -> "her sword").
5. NO FALSE-FRIEND VOCAB. Don't use a word in an archaic/technical sense whose common MODERN meaning differs (medieval "doctors" = theologians reads as physicians to a kid; "clerk", "want" = lack, "suffer" = allow, "corn" = grain). Use the plain word.
6. TWO QUESTION SHAPES, NEVER THE COY HEDGE. Either (A) general stem + the ANSWER carries the full specific payoff, or (B) specific stem + a POINTED sub-question. NEVER the evasive middle that narrates the SHAPE of the answer ("something that would happen to her... naming WHERE it would strike").
7. DON'T FORCE A STORY/SCENARIO. If the scene-setting is awkward or the setup telegraphs the answer, the fact may not earn a rung -- pick a better fact. Don't cram a narrative around a fact until it reads wrong.
8. SCENE-SETTING MUST ORIENT. Locate the reader: who/what the subject is, what's at stake, why this moment matters -- not just name it.
9. EARN THE PAYOFF. When the answer's impressiveness depends on context (who the adversary was, why a detail is remarkable), BUILD that context into the stem so the answer LANDS. Don't assume the reader supplies the stakes.
10. THE ANSWER MUST ITSELF BE THE PAYOFF the controlling voice prizes (a wonder, a punchline, a recognition -- per the voice above), never a dead label/insignificant name. If the answer would be a dead name, FLIP: make the memorable THING the answer and the name supporting color. Fewer great rungs beat filler.
11. PAY OFF THE TEASE. If the stem promises a beat ("what he did NEXT made his name"), the ANSWER must deliver exactly that beat -- don't tease an action then ask a vaguer question with a label answer.
12. ACTIVE VOICE / ASSIGN RESPONSIBILITY. When a person did something -- especially to someone, or a wrong -- write it ACTIVE and NAME the actor ("her jailers took her clothes", not "her clothes had been taken"). Responsibility is core to the moral voice.
13. NO LOGICAL TELEGRAPH. Distractors must not be self-eliminating against a stem premise. Every distractor must be a live, plausible option given everything the stem says. ENUMERATION is the sharpest form: if the stem LISTS items that match the distractors, the answer becomes the only un-listed option (stem names "eternal law, human law, and divine law" -> "natural law" is the only choice the stem didn't name). Never enumerate the distractors in the stem.
14. STORY-IN-STEM + POINTED CLOSER + TEACH-BEFORE-TEST. Substantive content (named figures, dramatic specifics) lives in the STEM, not buried in context (context shows only on a wrong answer / review). The closing question must be POINTED + CONCRETE about something specific -- never a weasel closer ("what's the takeaway/lesson/significance/pattern?"). Don't assume a technical term the bank should be teaching -- introduce it inline or it is flagged.

VALUES: never impose a verdict on a genuinely contested moral/political/metaphysical question -- attribute the claim to a person ("X testified", "Y argued"), present competing views, do not adjudicate. ${FRAMING}

LADDER STRUCTURE: one FACT per rung (a fact spent as stem scenery can't be a payoff again). Rungs slotted by CONCEPTUAL difficulty, roughly balanced across the tier_span with a real T1-T2 base. SELF-CONTAINED: each stem stands alone (full name on first reference, anchored scene) -- a kid hitting any rung cold can read it. DOWNWARD-ONLY scaffold: a stem may assume lower-tier facts but never reveal a same-or-higher-tier rung's answer. LEGEND labeled as legend.

FACTUAL INTEGRITY (non-negotiable -- this is for real children): every keyed answer must trace to the sourced fact sheet. NOTHING fabricated. If a fact isn't in the sheet, don't use it. Disputed/legendary facts are framed as legend or testimony.`;

// ---- schemas ----
const RESEARCH = { type:'object', additionalProperties:false, properties:{
  topic_name:{type:'string'}, status:{type:'string', enum:['ok','thin']},
  facts:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    fact:{type:'string'}, source:{type:'string'}, difficulty:{type:'string', enum:['easy','med','hard']},
    legend:{type:'boolean'}, confidence:{type:'string', enum:['high','medium','low']}
  }, required:['fact','source','difficulty','legend','confidence']}}
}, required:['topic_name','status','facts'] };

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
function readCmd(idx){ return `python -c "import json,sys;q=json.load(open(r'${QUEUE}',encoding='utf-8'));sys.stdout.write(json.dumps(q[${idx}]))"`; }

// ---- DETERMINISTIC MECHANICAL GATE (JS port of bankbuild/tellgate.py; keep the two in sync) ----
// Catches the mechanical telegraphs an LLM judge misses inconsistently: key-noun leak on a LABEL
// answer, and a short answer printed verbatim in the stem. 76% precision -> flags feed the adversarial
// judge (which vetoes the ~24% false positives), so good vivid answers are never forced to change.
const STOPJS = new Set(("a an the of to in on at by for and or but nor so yet as if it its is are was were be been being he she "+
  "they them his her their our your my we you i me us him who whom whose which what that this these those with from into onto over "+
  "under above below between among through during before after while until since not no only just very more most much many few some "+
  "any all each every both either neither did do does done has have had having will would shall should can could may might must than "+
  "then thus also too about around near upon out off down up away back when where why how here there now today never always often "+
  "one two three four five six seven eight nine ten first second third last next").split(/\s+/));
function wordsJS(s){ return ((s||'').toLowerCase().match(/[a-z][a-z'\-]*/g)) || []; }
function isLabelJS(ans){
  if (/["'‘’“”]/.test(ans||'')) return false;
  if ((ans||'').includes(',')) return false;
  const n = wordsJS(ans).length; return n>=1 && n<=5;
}
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
          out.push({tier:r.tier, idx, pattern:'key_noun_leak', flaw:`answer word "${w}" is in the stem and in no distractor (mechanical key-noun leak)`}); break;
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

// ---- prompts ----
function researchPrompt(idx){ return `You are the RESEARCH stage of a ${SUBJECT} quiz bank a father is building for HIS OWN KIDS. Accuracy is sacred.
STEP 1 -- read your topic (PowerShell, do not modify): ${readCmd(idx)}
It prints {name, scope, framing_note, tier_span, depth, target_q, source}. Non-ASCII appears as \\uXXXX escapes. Echo name back as topic_name.
STEP 2 -- use WebSearch/WebFetch on REAL sources to gather the most memorable, specific, RETELLABLE facts that fit this subject's controlling voice: named things, vivid actions, real quotes, striking specifics, primary-source human detail. Gather MORE than needed (about target_q + 5 gems) so the author can choose.
For each fact: fact, source (a real URL/named primary source you ACTUALLY found), difficulty (easy=T1 .. hard=T5), legend (bool), confidence.
ANTI-HALLUCINATION (non-negotiable): every fact MUST trace to a real source you found. Do NOT invent or pad from memory. If you can't research to depth, set status='thin' and return only what you verified. Better thin than fabricated.`; }

function authorPrompt(idx, name, research){ return `You are the AUTHOR stage of a ${SUBJECT} quiz bank for a father's kids. Turn the SOURCED fact sheet into a voice-driven ladder for "${name}".
STEP 1 -- read your topic spec: ${readCmd(idx)}
Use framing_note for stance/voice; depth sets length (deep = 10-15 rungs, standard = 3-5, mini = 1-3 standalone gems); author about target_q rungs across the tier_span.
SOURCED FACT SHEET -- use ONLY these facts, nothing from memory:
${JSON.stringify(research.facts)}

${RULES}

Author the ladder: pick the BEST gems, ONE fact per rung, slot by conceptual difficulty across the tier_span with a REAL T1-T2 base (~30%+). Each rung: tier, EXACTLY 4 choices, answer (== one choice verbatim), context (post-answer enrichment + the source), legend bool. Apply EVERY rule. If a fact can't make a clean rung, drop it.

FINAL SELF-AUDIT -- run on EVERY rung BEFORE returning; fix or drop any failure. Be ruthless:
1. PARITY: all 4 choices alike in length, name-count, grammar? Answer not the only long/dual-named/full-sentence/oddly-precise-number one?
2. STEM LEAK: any stem word hand over the answer (key noun; a category only it fits; a closing verb that pre-announces the answer type)? ALSO: does the answer RESTATE a clause already in the stem, or is it the TOPIC'S OWN NAME / a word just taught (name-matching)? Both are leaks -- re-key or reword.
3. LOGICAL ELIMINATION: every distractor stays LIVE? (a) stem negates/kills none; (b) CATEGORY MATCH -- if the stem names a category the answer belongs to, all four choices fit it; (c) no visual/mechanism description matching only the answer; (d) EFFECT/GOAL MATCH -- stem doesn't state the outcome only the answer achieves; (e) ENUMERATION -- stem doesn't LIST items matching the distractors, leaving the answer the only un-listed one. Fix by making distractors share the answer's category/effect or removing the cue.
4. CLOSER: final question POINTED + CONCRETE, never a weasel.
5. SCAFFOLD: does this rung STATE a number/name/fact another rung ASKS as its answer? Remove the leak.
Return ONLY rungs that pass all five.`; }

function judgePrompt(name, research, ladder){ return `You are the CRAFT JUDGE -- the last line of defense before these questions reach a child. Be STRICT; flag anything that breaks a rule or isn't sourced. Topic: "${name}".
${RULES}
SOURCED FACTS (the ONLY allowed basis for any answer): ${JSON.stringify(research.facts)}
LADDER TO JUDGE (idx = position in this array): ${JSON.stringify(ladder.rungs)}
For EACH rung: verdict 'keep' or 'flag'. If flag: rules_flagged (rule numbers/labels), primary_flaw (one line), fix (concrete). ALSO fact-check: if the keyed answer is NOT supported by the sourced facts, FLAG ("factual integrity").
SEVERITY (every rung; 'none' for keeps). ALWAYS-HIGH: a factual error, a dead-name answer, an agent-hiding passive, a weasel closer, a contested-verdict imposed as fact, a restatement/topic-name/enumeration leak, OR a label/name/date answer under a payoff-carrying stem. Otherwise the EXPLOIT TEST: could a smart kid who never studied this RELIABLY pick the answer from the telegraph alone? YES -> MEDIUM; a stretch -> LOW.
Set ladder_ok = true ONLY if NO rung is flagged HIGH or MEDIUM (a couple LOW notes ok).`; }

// fresh, hostile, INDEPENDENT re-judge -- the audit's strength, moved into the build. Fed the gate flags.
function advJudgePrompt(name, research, ladder, gateFlags){ return `You are an INDEPENDENT, SKEPTICAL auditor. This ${SUBJECT} ladder ALREADY PASSED a craft judge -- your job is to catch what that judge MISSED. Assume nothing is good; do not rubber-stamp. Topic: "${name}".
${RULES}
SOURCED FACTS: ${JSON.stringify(research.facts)}
LADDER (idx = position): ${JSON.stringify(ladder.rungs)}
${gateFlags.length ? `A DETERMINISTIC mechanical scanner already flagged these (verify each -- it is ~76% precise, so CONFIRM a real leak or clear it as a false positive on a legitimately vivid/named answer):\n${JSON.stringify(gateFlags)}` : `The mechanical scanner found nothing -- still hunt the SEMANTIC tells it cannot see.`}
Hunt especially the tells a lenient judge waves through: RESTATEMENT (answer echoes a stem clause), ENUMERATION (stem lists the distractors), CATEGORY-MATCH (only the answer fits a category the stem names), EFFECT/GOAL-MATCH, Drama-Available (a label/number answer under a vivid stem), dead-name answers, weasel closers, agent-hiding passive, and any unsourced/false fact.
For EACH rung: verdict 'keep' or 'flag'; if flag: severity (high/medium/low) + rules_flagged + primary_flaw + fix. Be the adversary the first judge wasn't. ladder_ok = true ONLY if nothing is HIGH or MEDIUM.`; }

function revisePrompt(name, research, ladder, flags){ return `Revise this ${SUBJECT} ladder for "${name}". Fix ONLY the flagged rungs; leave the others byte-identical. Apply the rules + the given fixes, using ONLY the sourced facts.
${RULES}
SOURCED FACTS: ${JSON.stringify(research.facts)}
CURRENT LADDER: ${JSON.stringify(ladder.rungs)}
FLAGS TO FIX: ${JSON.stringify(flags)}
Return the FULL ladder (the flagged rungs fixed, answer still == one of its 4 choices), leaving unflagged rungs byte-identical.
If a flagged rung CANNOT be cleanly fixed from the sourced facts -- a fabricated/unsupported claim with no good alternative, or a telegraph that only disappears by gutting the rung -- DROP that rung entirely rather than ship it flawed; returning FEWER rungs is correct. NEVER keep a rung with a known fabricated fact.
IMPORTANT: re-audit the WHOLE ladder against the rules + five-point self-audit, not only the listed flags -- a fix must not leave a sibling telegraph or introduce a new one (don't make the new answer the only long choice; don't seed the answer word in the stem).`; }

// ---- build one ladder: judge+revise, then adversarial judge + gate, then de-tell ----
async function buildLadder(idx, research, ladder){
  const name = research.topic_name || ('#'+idx);
  let cur = ladder, rounds = 0;

  // PASS A -- primary craft judge + revise (cap 2)
  for (let r=0; r<2; r++){
    const v = await tryAgent(judgePrompt(name, research, cur), {schema:VERDICTS, phase:'Judge', label:`judge:${name.slice(0,20)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts));
    if (!v) return {status:'error', ladder:cur, rounds:r, unresolved:['judge-failed'], notes:[]};
    const flags = (v.verdicts||[]).filter(x=>x.verdict==='flag');
    const high = flags.filter(x=>x.severity==='high'), med = flags.filter(x=>x.severity==='medium');
    rounds = r+1;
    if (high.length===0 && med.length<=2) break;          // good enough to hand to the adversary
    if (r===1) break;
    const rev = await tryAgent(revisePrompt(name, research, cur, [...high,...med]), {schema:LADDER, phase:'Judge', label:`revise:${name.slice(0,20)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
    if (!rev || !rev.rungs || !rev.rungs.length) break;
    cur = rev;
  }

  // PASS B -- mechanical gate + fresh adversarial judge, then de-tell (cap 2)
  let advNotes = [];
  for (let r=0; r<2; r++){
    const gate = mechGate(cur.rungs);
    const v = await tryAgent(advJudgePrompt(name, research, cur, gate), {schema:VERDICTS, phase:'Verify', label:`adv:${name.slice(0,20)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts));
    if (!v) { advNotes = gate.map(g=>`gate:${g.pattern}@${g.idx}`); break; }
    const flags = (v.verdicts||[]).filter(x=>x.verdict==='flag');
    const high = flags.filter(x=>x.severity==='high'), med = flags.filter(x=>x.severity==='medium'), low=flags.filter(x=>x.severity==='low');
    rounds += 1;
    if (high.length===0 && med.length===0){
      return {status:'passed', ladder:cur, rounds, unresolved:[], notes: low.map(f=>`T${f.tier}(low):${f.primary_flaw}`)};
    }
    if (r===1){ advNotes = [...high,...med].map(f=>`T${f.tier}(${f.severity}):${f.primary_flaw}`); break; }
    const rev = await tryAgent(revisePrompt(name, research, cur, [...high,...med]), {schema:LADDER, phase:'Verify', label:`detell:${name.slice(0,20)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
    if (!rev || !rev.rungs || !rev.rungs.length){ advNotes = [...high,...med].map(f=>`T${f.tier}(${f.severity}):${f.primary_flaw}`); break; }
    cur = rev;
  }
  return {status:'needs_review', ladder:cur, rounds, unresolved:advNotes, notes:[]};
}

if (!QUEUE){ log('ERROR: no config.queue passed. Launch with args.config = the subject config JSON.'); return {error:'no-config'}; }
phase('Research');
log(`${SUBJECT} pipeline: ${idxs.length} topics [${idxs[0]}..${idxs[idxs.length-1]}]. research -> author -> judge+revise -> adversarial+gate.`);

const results = await pipeline(idxs,
  (idx) => tryAgent(researchPrompt(idx), {schema:RESEARCH, phase:'Research', label:`res:${idx}`, model:'opus'}, x=>x&&x.facts&&x.facts.length>=2)
            .then(r => ({idx, research:(r&&r.facts&&r.facts.length>=2)?r:{topic_name:'#'+idx,status:'thin',facts:[]}}))
            .catch(()=>({idx, research:{topic_name:'#'+idx,status:'thin',facts:[]}})),
  async (s1, idx) => {
    const res = s1.research, name = res.topic_name || ('#'+idx);
    if (!res.facts || res.facts.length < 2) return {idx, status:'needs_review', research:res, ladder:{rungs:[]}, reason:'thin-research'};
    const lad = await tryAgent(authorPrompt(idx, name, res), {schema:LADDER, phase:'Author', label:`auth:${idx}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
    const ok = lad && lad.rungs && lad.rungs.length;
    return {idx, research:res, ladder: ok?lad:{rungs:[]}, status: ok?'authored':'needs_review', reason: ok?'':'author-failed'};
  },
  async (s2, idx) => {
    if (s2.status === 'needs_review')
      return {idx, name:(s2.research&&s2.research.topic_name)||('#'+idx), status:'needs_review', ladder:s2.ladder, n_rungs:(s2.ladder.rungs||[]).length, rounds:0, unresolved:[s2.reason], notes:[], sources:[]};
    const out = await buildLadder(idx, s2.research, s2.ladder);
    return {idx, name:s2.research.topic_name||('#'+idx), status:out.status, ladder:out.ladder, n_rungs:(out.ladder.rungs||[]).length, rounds:out.rounds, unresolved:out.unresolved, notes:out.notes||[],
            sources: [...new Set((s2.research.facts||[]).map(f=>f.source))].slice(0,12)};
  }
);

const ok = results.filter(r=>r&&r.status==='passed');
const nr = results.filter(r=>r&&r.status==='needs_review');
phase('Verify');
log(`Batch done: ${ok.length} passed, ${nr.length} needs_review, of ${idxs.length}. ` + results.map(r=>`#${r&&r.idx}:${r&&r.status}(${r&&r.n_rungs||0})`).join(' '));
return {subject:SUBJECT, start:START, count:COUNT, results};
