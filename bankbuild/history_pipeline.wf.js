export const meta = {
  name: 'history-bank-pipeline',
  description: 'Per-topic history bank pipeline: research -> author -> craft-judge + revise-until-clean. All 14 craft rules enforced; facts must be sourced.',
  phases: [
    { title: 'Research', detail: 'web-sourced fact sheet per topic (anti-hallucination)' },
    { title: 'Author', detail: 'wonder-driven ladder from sourced facts, 14 rules' },
    { title: 'Judge', detail: 'craft judge: 14 rules + fact-check vs sources' },
    { title: 'Revise', detail: 'fix flagged rungs, re-judge (cap 3, else needs_review)' },
  ],
}

const QUEUE = String.raw`C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\_queue.json`;
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const START = Number(A.start) || 0;
const COUNT = Number(A.count) || 3;

const RULES = `THE BANK: a history quiz bank a father is building for HIS OWN KIDS. History is a WONDER subject -- every question's answer should be the single most memorable, RETELLABLE, specific cool fact. Tiers = difficulty band by CONCEPTUAL difficulty (T1 ~grade5 simple/concrete .. T5 ~grade9-10 analytic), NOT obscurity. Grade-10 ceiling.

THE WONDER PATTERN (controlling voice): the answer is the MOST memorable specific cool fact. Hierarchy: NAMED THINGS (Excalibur, "Annus mirabilis", Mjolnir) > VIVID ACTIONS (Hercules strangling the lion; Joan offering to fight a whole gang) > OBJECTS > NUMBERS (ONLY when the stem CONSTRUCTS the number -- builds an expectation it shatters, e.g. Everett's 13,000 words -> Lincoln's 272; a number asked COLD = randomness, BANNED) > GENERIC LABELS (a venue/date/category as the answer = BANNED). Dinner Test: would a kid excitedly retell this answer at dinner? Drama-Available Rule: if the stem has drama (fire, blood, a trial, last words), the answer can NEVER be a venue/date/label.

THE 14 CRAFT RULES (each a hard requirement; a rung breaking ANY is FLAGGED):
1. LEAD WITH THE SUBJECT. Never open a stem on a dangling pronoun/possessive ("At her trial...", "When he...") before the named subject appears. The deck is SHUFFLED + timed -- the stem must parse in ONE forward pass; a player cannot re-read. Lead with the named subject, or a self-standing scene with no dangling reference.
2. CHOICE-FORMAT PARITY. All four choices structurally parallel -- similar length, same name-count, same grammatical shape. The answer must NEVER be the structural odd-one-out (the only dual-named, the only long one, the only full sentence, the only one with a date). No skim-tell.
3. NO LEXICAL/CATEGORY TELEGRAPH. No stem word that hands over the answer: not the answer's key noun, not a category word only the answer matches ("tree" when only the answer is a tree; a setup "about her body" when only the wound answer is bodily), not a verb revealing the mechanism ("sent an armorer to DIG for it" -> "buried"), not a tone-word matching only the answer. The player must KNOW the answer, not deduce it from a stem word. THREE recurring high-severity leaks to kill: (i) RESTATEMENT -- the answer must not restate a discriminating clause the stem already gave (stem "buried in the grandest tomb, beside William Pitt" -> answer "Westminster Abbey, beside William Pitt" is just an echo); (ii) TOPIC-NAME MATCH -- the answer must not be the topic's own name, a word from the topic title, or a name just taught in a lower rung (a "Ghana Empire" answer in a Ghana topic is pure name-matching); (iii) LONE STEM-ANCHOR -- the answer must not be the only choice tied to anything in the stem while the three distractors float free of it.
4. ECONOMY. Cut superlatives/qualifiers that add nothing ("her MOST FAMOUS sword" when she has one famous sword -> "her sword").
5. NO FALSE-FRIEND VOCAB. Don't use a word in an archaic/technical sense whose common MODERN meaning differs (medieval "doctors" = theologians reads as physicians to a kid; "clerk", "want" = lack, "suffer" = allow, "corn" = grain). Use the plain word.
6. TWO QUESTION SHAPES, NEVER THE COY HEDGE. Either (A) general stem + the ANSWER carries the full specific wonder, or (B) specific stem + a POINTED sub-question. NEVER the evasive middle that narrates the SHAPE of the answer ("something that would happen to her... naming WHERE on her body it would strike").
7. DON'T FORCE A STORY. If the scene-setting is awkward or the setup telegraphs the answer, the fact may not earn a rung -- pick a better fact. Don't cram a narrative around a fact until it reads wrong.
8. SCENE-SETTING MUST ORIENT. Locate the reader in the story: who the subject is, what they're trying to do, why this moment matters -- not just name them ("X was begging to be sent to the prince" tells the reader nothing about where in the story we are).
9. EARN THE PAYOFF. When the answer's impressiveness depends on context (who the adversary was, why a detail is remarkable), BUILD that context into the stem so the answer LANDS. Don't assume the reader supplies the stakes (an "illiterate teenager" outwitting theologians only hits if the stem first establishes the theologians' expertise AND her illiteracy).
10. THE ANSWER MUST ITSELF BE A WONDER. No unknown-name / insignificant-fact payoff -- an unknown name is just a label. If the answer would be a dead name, FLIP: make the WONDER itself the answer and the name supporting color ("the beloved honesty story was invented to sell books", NOT "who invented it? -> Weems"). Don't pad a ladder to a rung count with weak facts -- fewer great rungs beat filler.
11. PAY OFF THE TEASE. If the stem promises a beat ("what he did NEXT made his name"), the ANSWER must deliver exactly that beat -- don't tease an action then ask a vaguer question with a label answer.
12. ACTIVE VOICE / ASSIGN RESPONSIBILITY. When a person did something -- especially something TO someone, or a wrong -- write it ACTIVE and NAME the actor. No agent-hiding passive ("her clothes had been taken" -> "her jailers took her clothes"). Responsibility is core to the moral voice; the bank names who did what.
13. NO LOGICAL TELEGRAPH. Distractors must not be self-eliminating against a stem premise ("Historians say it never happened" + three distractors that assert it DID happen forces the answer). Every distractor must be a live, plausible option given everything the stem says. ENUMERATION is the sharpest form: if the stem LISTS items that match the distractors, the answer becomes the only un-listed option (stem names "eternal law, human law, and divine law" -> "natural law" is the only choice the stem didn't already name). Never enumerate the distractors in the stem.
14. STORY-IN-STEM + POINTED CLOSER + TEACH-BEFORE-TEST. Substantive content (named figures, dramatic specifics) lives in the STEM, not buried in context (context shows only on a wrong answer / end-game review). The closing question must be POINTED + CONCRETE about something specific -- never a weasel closer ("what's the takeaway/lesson/significance/pattern?"). Don't assume a technical term the bank should be teaching -- introduce it inline or it is flagged.

VALUES: never impose a verdict on a genuinely contested moral/political/metaphysical question -- attribute the claim to a person ("X testified", "Y argued"), present competing views, do not adjudicate. Apply the topic's framing_note (moral_vision) for stance + mandated emphasis, but never WARP content to force a principle in.

LADDER STRUCTURE: one FACT per rung (a fact spent as stem scenery can't be a payoff again). Rungs slotted by CONCEPTUAL difficulty (simple/concrete = T1; analytic/legal/theological = T5), roughly balanced across the tier_span. SELF-CONTAINED: each stem stands alone (full name on first reference, anchored scene) -- a kid hitting any rung cold can read it. DOWNWARD-ONLY scaffold: a stem may assume lower-tier facts but never reveal a same-or-higher-tier rung's answer. LEGEND labeled as legend (testimony, not forensic fact).

FACTUAL INTEGRITY (non-negotiable -- this is for real children): every keyed answer must trace to the sourced fact sheet. NOTHING fabricated. If a fact isn't in the sheet, don't use it. Disputed/legendary facts are framed as legend or testimony.`;

const RESEARCH = { type:'object', additionalProperties:false, properties:{
  topic_name:{type:'string'},
  status:{type:'string', enum:['ok','thin']},
  facts:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    fact:{type:'string'}, source:{type:'string'}, difficulty:{type:'string', enum:['easy','med','hard']},
    legend:{type:'boolean'}, confidence:{type:'string', enum:['high','medium','low']}
  }, required:['fact','source','difficulty','legend','confidence']}}
}, required:['topic_name','status','facts'] };

const RUNG = { type:'object', additionalProperties:false, properties:{
  tier:{type:'number'}, stem:{type:'string'},
  choices:{type:'array', items:{type:'string'}, minItems:4, maxItems:4},
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

// THROTTLE CONTROL: retry-with-backoff. Sequential re-spawns (each attempt takes ~30-60s, so they
// are naturally spaced minutes apart) ride out intermittent server rate-limiting instead of dropping
// the topic. ok(r) decides success; returns the last attempt (possibly null) if all tries fail.
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

function researchPrompt(idx){ return `You are the RESEARCH stage of a history quiz bank a father is building for HIS OWN KIDS. Accuracy is sacred.

STEP 1 -- read your topic. Run EXACTLY this (works in PowerShell, do not modify):
${readCmd(idx)}
It prints {name, scope, framing_note, tier_span, depth, target_q, source}. Non-ASCII chars appear as \\uXXXX escapes -- read them as the underlying character. Echo the name back as topic_name.

STEP 2 -- use WebSearch and WebFetch on REAL sources (encyclopedias, primary-source archives, reputable history/museum sites) to gather the most WONDER-worthy, specific, RETELLABLE facts: named things, vivid actions, real quotes, striking objects, startling specifics, primary-source human detail. Gather MORE than needed (about target_q + 5 distinct gems) so the author can choose the best.

For each fact: fact (the specific gem), source (a real URL or named primary source you ACTUALLY found), difficulty (easy=concrete/T1 .. hard=analytic/T5), legend (true if tradition/legend not forensic fact), confidence.

ANTI-HALLUCINATION (non-negotiable -- real kids read this): every fact MUST trace to a real source you actually found via search. Do NOT invent, guess, or pad from memory. If you cannot research this topic to real depth online, set status='thin' and return only what you genuinely verified. Better thin than fabricated.`; }

function authorPrompt(idx, name, research){ return `You are the AUTHOR stage of a history quiz bank for a father's kids. Turn the SOURCED fact sheet into a wonder-driven ladder for the topic "${name}".

STEP 1 -- read your topic spec: ${readCmd(idx)}
Use framing_note for stance/voice; depth sets length (deep = 10-15 rungs, standard = 3-5, mini = 1-3 standalone gems); author about target_q rungs across the tier_span.

SOURCED FACT SHEET -- use ONLY these facts, nothing from your own memory:
${JSON.stringify(research.facts)}

${RULES}

Author the ladder: pick the BEST gems, ONE fact per rung, slot by conceptual difficulty across the tier_span, roughly balanced WITH A REAL T1-T2 BASE. Every topic has simple, concrete, iconic entry points -- a named object, a vivid one-word answer, an image a 10-year-old grasps (SPQR = "the Senate and People of Rome"; "patres" = "fathers"; the fasces axe). Put those at T1-T2, and do NOT inflate a simple concrete fact to T3+. An all-T3-T5 ladder is mis-tiered: aim for at least ~30% of rungs at T1-T2 combined. Each rung: tier, stem, EXACTLY 4 choices, answer (must equal one choice verbatim), context (post-answer enrichment + the source), legend bool. Apply EVERY rule above. If a fact can't make a clean wonder-rung, drop it rather than force it.

FINAL SELF-AUDIT -- run on EVERY rung BEFORE returning; fix any failure or drop the rung. Most ladders fail on these, so be ruthless:
1. PARITY: are all 4 choices alike in length, name-count, and grammar? The answer must NOT be the only long one, the only full sentence, the only dual-clause, or (if numeric) the only oddly-precise number among round ones. If the choices are numbers, make all four equally precise or equally round.
2. STEM LEAK: does any stem word hand over the answer -- the answer's key noun; a category only the answer fits; a closing VERB that pre-announces the answer type ("paid only what?" -> a money answer; "let it DO?" -> an action; "sent a man to DIG for it" -> buried)? Reword the closer to be neutral. ALSO: does the answer RESTATE a discriminating clause already in the stem, or is it the TOPIC'S OWN NAME / a word just taught in a lower rung (name-matching)? Both let a kid pick it cold -- re-key or reword the stem.
3. LOGICAL ELIMINATION + DISTRACTOR-CATEGORY MATCH (the #1 telegraph -- be ruthless): EVERY distractor must stay a LIVE, plausible option. (a) Does the stem negate or kill any distractor ("not a temple or court" kills two; "instead"/"reverses" forces one outcome)? (b) CATEGORY MATCH -- if the stem names a category the ANSWER belongs to (a "Phoenician prince", a "non-elite" group, a script "descended from" X, the "victim" city), then ALL FOUR choices must fit that category, or the category word alone eliminates the distractors: Cadmus must sit among other PHOENICIANS (not Greek heroes); "merchants" among other practical/common groups (not literate elites); a descendant script among other plausible descendants (not scripts this ladder already excluded). (c) Does a visual/mechanism description match only the answer ("two horns and a snout" fits only the letter A)? (d) EFFECT/GOAL MATCH (recurring tell): does the stem state the OUTCOME or objective the answer achieves -- "make the invaders lose their way", "make that symbol gone from the center", "the men who ROWED the army across" -- so the keyed choice is the only one that fulfills it while the distractors describe other effects? A kid then maps the stem's stated goal to the one matching choice without knowing the fact (sharpened by any lose/lost-type lexical echo). Fix by making all four choices plausibly achieve the stated goal, or by not pre-stating the goal in the stem. (e) ENUMERATION: does the stem LIST items that match the distractors, leaving the answer as the only option the stem didn't name (lists "eternal, human, divine law" -> "natural law" is the lone un-listed choice)? Don't enumerate the distractors in the stem. Fix any of (a)-(e) by making the distractors share the answer's category/effect, or by removing the cue from the stem.
4. CLOSER: is the final question POINTED + CONCRETE about a specific thing -- never "why did they...?", "what does this show/reveal?", "what did it let it DO?", "what was the lesson?"
5. SCAFFOLD: does this rung STATE a number / name / fact that another rung ASKS as its answer? Remove the leak.
Return ONLY rungs that pass all five.`; }

function judgePrompt(name, research, ladder){ return `You are the CRAFT JUDGE -- the last line of defense before these questions reach a child. Be STRICT; flag anything that breaks a rule or isn't sourced. Topic: "${name}".

${RULES}

SOURCED FACTS (the ONLY allowed basis for any answer):
${JSON.stringify(research.facts)}

LADDER TO JUDGE (idx = position in this array):
${JSON.stringify(ladder.rungs)}

For EACH rung: verdict 'keep' or 'flag'. If flag: rules_flagged (name the rule numbers/labels broken, e.g. "3 lexical telegraph", "10 dead-name"), primary_flaw (one line), fix (concrete + actionable). ALSO fact-check every rung: if the keyed answer is NOT supported by the sourced facts, FLAG it ("factual integrity").

SEVERITY (set on every rung; 'none' for keeps). ALWAYS-HIGH (auto): a factual error, a dead-name answer, an agent-hiding passive, a weasel closer, a contested-verdict imposed as fact, OR a label/name/date answer under a DRAMA-carrying stem (Drama-Available Rule). Otherwise rate by the EXPLOIT TEST: could a smart kid who never studied this topic RELIABLY pick the answer from the telegraph alone? If YES (e.g. the answer is the only choice fitting a category the stem names; the only oddly-precise number among round ones; a closer verb that pre-announces the answer type) -> MEDIUM. If exploiting it is a stretch / theoretical / debatable -> LOW. Be honest -- do not under-rate a real exploitable telegraph to push a rung through, and do not inflate a theoretical nit to LOW-block a strong rung.

Set ladder_ok = true ONLY if NO rung is flagged HIGH or MEDIUM (a couple of LOW notes are acceptable).`; }

function revisePrompt(name, research, ladder, flags){ return `Revise this history ladder for "${name}". Fix ONLY the flagged rungs; leave the others byte-identical. Apply the rules and the given fixes, using ONLY the sourced facts.

${RULES}

SOURCED FACTS: ${JSON.stringify(research.facts)}
CURRENT LADDER: ${JSON.stringify(ladder.rungs)}
FLAGS TO FIX: ${JSON.stringify(flags)}

Return the FULL ladder (every rung, the flagged ones fixed, answer still equals one of its 4 choices).

IMPORTANT: re-audit the WHOLE ladder against the rules + the five-point self-audit (PARITY / STEM-LEAK / LOGICAL-ELIMINATION / CLOSER / SCAFFOLD), not only the listed flags -- fixing one rung must not leave a sibling telegraph, and your fixes must not introduce new ones (especially: don't make the new answer the only long choice, and don't seed the answer word in the stem).`; }

async function reviseUntilClean(idx, research, ladder){
  const name = research.topic_name || ('#'+idx);
  let cur = ladder, rounds = 0, last = [];
  for (let r=0; r<3; r++){
    const v = await tryAgent(judgePrompt(name, research, cur), {schema:VERDICTS, phase:'Judge', label:`judge:${name.slice(0,22)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts));
    if (!v) return {status:'error', ladder:cur, rounds:r, unresolved:['judge-failed']};
    const flags = (v.verdicts||[]).filter(x=>x.verdict==='flag');
    const high = flags.filter(x=>x.severity==='high');
    const med = flags.filter(x=>x.severity==='medium');
    const low = flags.filter(x=>x.severity==='low');
    const notes = [...med, ...low].map(f=>`T${f.tier}(${f.severity}):${f.primary_flaw}`);
    // pass bar: zero HIGH and at most 2 MEDIUM (residual medium/low recorded as review notes)
    if (high.length === 0 && med.length <= 2) return {status:'passed', ladder:cur, rounds:r+1, unresolved:[], notes};
    const toFix = [...high, ...med];
    last = toFix; rounds = r+1;
    if (r===2) break;
    const rev = await tryAgent(revisePrompt(name, research, cur, toFix), {schema:LADDER, phase:'Revise', label:`revise:${name.slice(0,22)}`, model:'opus'}, x=>x&&x.rungs&&x.rungs.length>0);
    if (!rev || !rev.rungs || !rev.rungs.length) return {status:'needs_review', ladder:cur, rounds, unresolved:toFix.map(f=>`T${f.tier}:${f.primary_flaw}`), notes:[]};
    cur = rev;
  }
  return {status:'needs_review', ladder:cur, rounds, unresolved:last.map(f=>`T${f.tier}:${f.primary_flaw}`), notes:[]};
}

const idxs = (Array.isArray(A.idxs) && A.idxs.length) ? A.idxs : Array.from({length:COUNT}, (_,i)=>START+i);
phase('Research');
log(`History pipeline: ${idxs.length} topics [${idxs[0]}..${idxs[idxs.length-1]}]. research -> author -> judge+revise (cap 3).`);

const results = await pipeline(idxs,
  (idx) => tryAgent(researchPrompt(idx), {schema:RESEARCH, phase:'Research', label:`res:${idx}`, model:'opus'}, x=>x&&x.facts&&x.facts.length>=2)
            .then(r => ({idx, research: (r&&r.facts&&r.facts.length>=2)?r:{topic_name:'#'+idx,status:'thin',facts:[]}}))
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
      return {idx, name:(s2.research&&s2.research.topic_name)||('#'+idx), status:'needs_review', ladder:s2.ladder, n_rungs:(s2.ladder.rungs||[]).length, rounds:0, unresolved:[s2.reason], sources:[]};
    const out = await reviseUntilClean(idx, s2.research, s2.ladder);
    return {idx, name:s2.research.topic_name||('#'+idx), status:out.status, ladder:out.ladder, n_rungs:(out.ladder.rungs||[]).length, rounds:out.rounds, unresolved:out.unresolved, notes:out.notes||[],
            sources: [...new Set((s2.research.facts||[]).map(f=>f.source))].slice(0,12)};
  }
);

const ok = results.filter(r=>r&&r.status==='passed');
const nr = results.filter(r=>r&&r.status==='needs_review');
phase('Research');
log(`Batch done: ${ok.length} passed, ${nr.length} needs_review, of ${idxs.length}. ` + results.map(r=>`#${r&&r.idx}:${r&&r.status}(${r&&r.n_rungs||0})`).join(' '));
return {start:START, count:COUNT, results};
