export const meta = {
  name: 'history-fix9',
  description: 'Fix the 9 known real problems (5 high-craft tells + 4 bad facts) found in the audited 1,200; web-verify the fact corrections; re-judge.',
  phases: [
    { title: 'Fix',   detail: 'rewrite craft tells; web-verify + correct the bad facts' },
    { title: 'Judge', detail: 'adversarial re-check: clean craft + sourced facts' },
  ],
}
const IN = String.raw`C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\_fix9_input.json`;
const readAll = `python -c "import json,sys;sys.stdout.write(json.dumps(json.load(open(r'${IN}',encoding='utf-8'))))"`;
const readKind = k => `python -c "import json,sys;d=json.load(open(r'${IN}',encoding='utf-8'));sys.stdout.write(json.dumps([x for x in d if x['kind']=='${k}']))"`;

const RULES = `WONDER: the answer is the single most memorable, retellable fact (a NAMED thing or VIVID action) -- never a bland venue/date/number/generic-label answer when drama sits in the stem.
NO TELEGRAPH: no stem word that leaks the answer (its key noun; a category/visual only it matches; a verb revealing the mechanism; the stem stating the goal/effect only the answer achieves). THREE high-severity leaks to kill: RESTATEMENT (answer restates a clause the stem already gave), TOPIC-NAME MATCH (answer is the topic's own name / a word from the title / just taught), ENUMERATION (stem lists the distractors so the answer is the only un-listed option). The answer must NOT be the structural odd-one-out; every distractor must be LIVE and share the answer's category.
LEGIBILITY: lead with the named subject; no false-friend word; pointed concrete closer.
VOICE: active voice, responsibility named; no verdict imposed on a contested question.
KEEP the same underlying FACT, topic, and tier; keep the context's sourcing. You may re-key the answer to a better wonder from the SAME episode, reword the stem, and rebalance distractors -- but stay truthful.`;

const FIX = { type:'object', additionalProperties:false, properties:{ fixes:{type:'array', items:{type:'object', additionalProperties:false, properties:{
  rid:{type:'string'}, stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4, maxItems:4},
  answer:{type:'string'}, context:{type:'string'}, note:{type:'string'}
}, required:['rid','stem','choices','answer','context','note']}} }, required:['fixes'] };

const VERD = { type:'object', additionalProperties:false, properties:{ reviews:{type:'array', items:{type:'object', additionalProperties:false, properties:{
  rid:{type:'string'}, verdict:{type:'string', enum:['clean','flag']}, flaw:{type:'string'}
}, required:['rid','verdict','flaw']}} }, required:['reviews'] };

async function tryAgent(p,o,ok){ let last=null; for(let a=0;a<3;a++){ const r=await agent(p,{...o,label:o.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r)))return r; last=r;} return last; }

const craftPrompt = `Fix these FLAGGED history-quiz rungs (a father's bank for his kids). An adversarial auditor caught a real craft tell in each.
STEP 1 -- read them (PowerShell): ${readKind('craft')}
Each: {rid, tier, topic, stem, choices, answer, context, flaw}. The 'flaw' is exactly what to kill.
STEP 2 -- rewrite EACH to eliminate its flaw WITHOUT adding a new tell, obeying:
${RULES}
Return one fix per rid: {rid, stem, 4 choices, answer (==one choice verbatim), context (keep the sourcing), note (<=12 words: what changed)}.`;

const factPrompt = `Fix these history-quiz rungs whose KEYED ANSWER is factually wrong or unsupported (a father's bank for his KIDS -- a child would memorize a falsehood).
STEP 1 -- read them: ${readKind('fact')}
Each: {rid, tier, topic, stem, choices, answer, context, flaw}. The 'flaw' explains the error (usually a misattribution or a legend stated as fact).
STEP 2 -- for EACH, use WebSearch/WebFetch to establish the TRUE, sourced fact, then rewrite the rung so the keyed answer is correct and supported -- fix the misattribution, or reframe a legend AS legend. Obey:
${RULES}
Return one fix per rid: {rid, stem, 4 choices, answer (==one choice verbatim, now TRUE), context (cite the corrected source), note (<=14 words: the correction)}.`;

const judgePrompt = rungs => `You are a SKEPTICAL auditor. These rungs were just rewritten to fix a craft tell or a factual error. Verify each is now genuinely CLEAN and (where it was a fact fix) TRUE + sourced. Assume nothing.
${RULES}
RUNGS: ${JSON.stringify(rungs)}
For each: rid, verdict 'clean' or 'flag', flaw (one line if flagged). Catch any remaining or newly-introduced tell, and any answer still unsupported.`;

phase('Fix');
log('Fixing the 9 known issues: 5 craft tells + 4 bad facts.');
const [cf, ff] = await parallel([
  () => tryAgent(craftPrompt, {schema:FIX, phase:'Fix', label:'fix:craft', model:'opus'}, x=>x&&Array.isArray(x.fixes)).then(r=>(r&&r.fixes)||[]),
  () => tryAgent(factPrompt,  {schema:FIX, phase:'Fix', label:'fix:fact',  model:'opus'}, x=>x&&Array.isArray(x.fixes)).then(r=>(r&&r.fixes)||[]),
]);
const fixes = [...(cf||[]), ...(ff||[])];

phase('Judge');
const reviews = (await tryAgent(judgePrompt(fixes), {schema:VERD, phase:'Judge', label:'judge:9', model:'opus'}, x=>x&&Array.isArray(x.reviews)).then(r=>(r&&r.reviews)||[])) || [];
const vmap = {}; for(const v of reviews) vmap[v.rid]=v;
const clean = fixes.filter(f=>vmap[f.rid] && vmap[f.rid].verdict==='clean');
const bad   = fixes.filter(f=>!vmap[f.rid] || vmap[f.rid].verdict==='flag');
log(`Fix done: ${clean.length}/${fixes.length} verified clean; ${bad.length} still flagged.`);
return { fixes, clean: clean.map(f=>f.rid), still_bad: bad.map(f=>({rid:f.rid, v:vmap[f.rid]})) };
