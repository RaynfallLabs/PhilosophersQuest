export const meta = {
  name: 'history-bank-audit',
  description: 'Independent adversarial audit of a 540-rung stratified sample: craft re-judge + web fact-check.',
  phases: [
    { title: 'Craft', detail: 'skeptical re-judge vs the 14 rules (catch what the author judge missed)' },
    { title: 'Fact', detail: 'web-verify every keyed answer against its cited + independent sources' },
  ],
}

const AUDIT = String.raw`C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\_audit_sample.json`;
const N = 540;

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for (let a=0; a<(tries||3); a++){
    const r = await agent(prompt, {...opts, label: opts.label + (a?`.r${a}`:'')}).catch(()=>null);
    if (r && (!ok || ok(r))) return r;
    last=r;
  }
  return last;
}

function readBatch(sids){
  return `python -c "import json,sys;d=json.load(open(r'${AUDIT}',encoding='utf-8'));s=set(${JSON.stringify(sids)});sys.stdout.write(json.dumps([x for x in d if x['sid'] in s]))"`;
}

const CRAFT_RULES = `WONDER: the answer should be the single most memorable, retellable fact (a NAMED thing or VIVID action) -- never a bland venue/date/generic-label answer when drama sits in the stem.
TELEGRAPHS (flag ANY): a stem word that leaks the answer (its key noun; a category only the answer matches; a verb that reveals the mechanism; the stem stating the very goal/effect only the answer achieves); the answer being the structural ODD-ONE-OUT (only long/elaborated choice, only dual-named, only number, only full sentence); a distractor the stem logically kills; distractors that don't share the answer's category so the category word alone eliminates them.
LEGIBILITY: the stem must lead with its named subject (no dangling 'her/his/the' before the subject is named); no FALSE-FRIEND word (archaic/technical sense a kid misreads, e.g. medieval 'doctors' = theologians); the closing question must be POINTED + CONCRETE, never a weasel ('what's the takeaway/lesson/significance/what does this show?').
VOICE: active voice with responsibility NAMED (no agent-hiding passive); NO verdict imposed on a genuinely contested moral/political/metaphysical question (attribute it, don't adjudicate).`;

const CRAFT = { type:'object', additionalProperties:false, properties:{
  reviews:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    sid:{type:'number'}, verdict:{type:'string', enum:['clean','flag']},
    severity:{type:'string', enum:['high','medium','low','none']},
    rule:{type:'string'}, flaw:{type:'string'}
  }, required:['sid','verdict','severity','rule','flaw']}}
}, required:['reviews'] };

const FACT = { type:'object', additionalProperties:false, properties:{
  checks:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    sid:{type:'number'}, verdict:{type:'string', enum:['verified','partly','unsupported','false']},
    confidence:{type:'string', enum:['high','medium','low']}, note:{type:'string'}
  }, required:['sid','verdict','confidence','note']}}
}, required:['checks'] };

function craftPrompt(sids){ return `You are an INDEPENDENT, SKEPTICAL auditor of a FINISHED history quiz bank a father built for his kids. Every question here ALREADY PASSED an automated judge -- your job is to catch what that judge MISSED. Assume nothing is good until you have checked it; do not rubber-stamp.

STEP 1 -- read your batch (works in PowerShell, do not modify):
${readBatch(sids)}
It prints rungs: {sid, topic, tier, stem, choices, answer, context}. Non-ASCII appears as \\uXXXX escapes.

STEP 2 -- audit EACH rung against the bar:
${CRAFT_RULES}

Return one review per rung: sid; verdict 'clean' or 'flag'. If flag: severity (high = the owner would pull it; medium = he'd likely object; low = trivial polish), rule (which one broke), flaw (one concrete line). A genuinely good bank will be MOSTLY clean -- but flag every real telegraph, skim-tell, weasel closer, dead-name answer, agent-hiding passive, false-friend, or imposed verdict you find. Be the adversary the author judge wasn't.`; }

function factPrompt(sids){ return `You are a FACT-CHECKER auditing a history quiz bank a father built for his KIDS. This is the most important check of all: the keyed answer must be TRUE and genuinely supported, or a child memorizes something false.

STEP 1 -- read your batch:
${readBatch(sids)}
It prints rungs: {sid, topic, tier, stem, choices, answer, context}. The 'context' field usually names the sources the bank used.

STEP 2 -- for EACH rung, VERIFY the keyed answer using WebSearch and WebFetch: confirm it is factually correct and really supported. Check the cited source where one is given, and cross-check at least one INDEPENDENT source. Watch hard for: fabricated quotes, wrong dates/numbers, mis-attributions, and legends asserted as plain fact.

Return per rung: sid; verdict -- 'verified' (true and well supported), 'partly' (core is true but a detail is off or imprecise), 'unsupported' (you could not confirm it from real sources), or 'false' (the keyed answer is wrong or fabricated); confidence (high/medium/low); note (one line: what you found, or the correction). Flag every error -- this is what protects the children.`; }

function chunks(n, size){ const out=[]; for(let i=0;i<n;i+=size) out.push(Array.from({length:Math.min(size,n-i)},(_,k)=>i+k)); return out; }

phase('Craft');
const craftBatches = chunks(N, 6);
log(`Audit: craft re-judge of ${N} rungs in ${craftBatches.length} batches.`);
const craft = (await parallel(craftBatches.map(b => () =>
  tryAgent(craftPrompt(b), {schema:CRAFT, phase:'Craft', label:`craft:${b[0]}`, model:'opus'}, x=>x&&Array.isArray(x.reviews))
    .then(r => (r&&r.reviews)||[]).catch(()=>[])
))).flat();

phase('Fact');
const factBatches = chunks(N, 3);
log(`Audit: web fact-check of ${N} rungs in ${factBatches.length} batches.`);
const fact = (await parallel(factBatches.map(b => () =>
  tryAgent(factPrompt(b), {schema:FACT, phase:'Fact', label:`fact:${b[0]}`, model:'opus'}, x=>x&&Array.isArray(x.checks))
    .then(r => (r&&r.checks)||[]).catch(()=>[])
))).flat();

const cflag = craft.filter(r=>r.verdict==='flag');
const fbad = fact.filter(r=>r.verdict==='false'||r.verdict==='unsupported');
log(`Craft: ${craft.length} reviewed, ${cflag.length} flagged. Fact: ${fact.length} checked, ${fbad.length} false/unsupported.`);
return { craft, fact };
