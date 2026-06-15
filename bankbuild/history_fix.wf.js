export const meta = {
  name: 'history-bank-fix',
  description: 'Rewrite audit-flagged rungs to kill the tell, then re-judge the fix (only clean fixes are kept).',
  phases: [
    { title: 'Fix', detail: 'rewrite each flagged rung to remove its flaw + all tells' },
    { title: 'Verify', detail: 'adversarial re-judge of each fix; keep only clean ones' },
  ],
}

const FLAGS = String.raw`C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\_audit_flags.json`;
// which severities to fix this run (default high). Pass args:{sev:["high","medium"]} to widen.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const SEV = Array.isArray(A.sev) ? A.sev : ['high'];

const RULES = `WONDER: the answer must be the single most memorable, retellable fact (a NAMED thing or VIVID action) -- NEVER a bland venue/date/number/generic-label answer when drama sits in the stem (Drama-Available Rule). A number is acceptable ONLY when the stem CONSTRUCTS it (builds an expectation it shatters), never asked cold.
NO TELEGRAPH: no stem word that leaks the answer (its key noun; a category/visual only it matches; a verb revealing the mechanism; the stem stating the goal/effect only the answer achieves); the answer must NOT be the structural odd-one-out (only long/elaborated, only dual-named, only number, only emphasized); every distractor must be a LIVE option the stem doesn't kill, and distractors must SHARE the answer's category so the category word can't eliminate them.
LEGIBILITY: lead with the named subject (no dangling pronoun first); no false-friend word; pointed concrete closer (never "what's the takeaway/lesson?").
VOICE: active voice, responsibility named; no verdict imposed on a genuinely contested question.
KEEP: the same underlying FACT, topic, and tier. You may re-key the answer to a better wonder from the same episode, reword the stem, and rebalance distractors -- but stay truthful and keep the context's sourcing.`;

const RUNG = { type:'object', additionalProperties:false, properties:{
  sid:{type:'number'}, stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4, maxItems:4},
  answer:{type:'string'}, context:{type:'string'}, note:{type:'string'}
}, required:['sid','stem','choices','answer','context','note'] };
const FIXBATCH = { type:'object', additionalProperties:false, properties:{ fixes:{type:'array', items:RUNG} }, required:['fixes'] };

const VERDICT = { type:'object', additionalProperties:false, properties:{
  reviews:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    sid:{type:'number'}, verdict:{type:'string', enum:['clean','flag']}, severity:{type:'string', enum:['high','medium','low','none']}, flaw:{type:'string'}
  }, required:['sid','verdict','severity','flaw']}} }, required:['reviews'] };

function readCmd(sids){ return `python -c "import json,sys;d=json.load(open(r'${FLAGS}',encoding='utf-8'))['flags'];s=set(${JSON.stringify(sids)});sys.stdout.write(json.dumps([x for x in d if x['sid'] in s]))"`; }

function fixPrompt(sids){ return `An adversarial auditor FLAGGED these history-quiz rungs (built for a father's kids). Rewrite EACH to eliminate its specific flaw WITHOUT introducing any new tell.

STEP 1 -- read your batch (PowerShell):
${readCmd(sids)}
Each item: {sid, severity, topic, tier, rule, flaw, stem, answer, choices}. The 'flaw' tells you exactly what the auditor caught.

STEP 2 -- rewrite each into a clean rung obeying ALL of these:
${RULES}

Return one fix per sid: {sid, stem, 4 choices, answer (must equal one choice verbatim), context (keep the sourcing note), note (<=12 words: what you changed)}. If the flaw is a drama-then-number/label answer, RE-KEY to the vivid/named wonder of that same episode. If it's a stem-word leak, reword the stem to stop leaking. If it's an odd-one-out answer, rebalance the choices. Keep the fact true.`; }

function judgePrompt(rungs){ return `You are a SKEPTICAL auditor. These are REWRITTEN history-quiz rungs that were just fixed to remove a flaw. Verify each is now genuinely CLEAN -- assume nothing.

${RULES}

RUNGS:
${JSON.stringify(rungs)}

For each: sid, verdict 'clean' or 'flag'; if flag, severity (high/medium/low) + flaw (one line). Be the adversary -- catch any remaining or newly-introduced tell.`; }

async function tryAgent(prompt, opts, ok){ let last=null; for(let a=0;a<3;a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r)))return r; last=r;} return last; }

// load the flag sids of the requested severities (read via an agent-free helper is not possible in-script; we know them from the file -> pass through a tiny reader agent? No: hardcode by reading is impossible here, so we slice by re-deriving below)
// The script can't read files; instead we author over INDEX RANGES is wrong. We pull sids from a manifest the launcher writes:
const SIDS = A.sids || [];   // launcher passes the exact sids to fix
if (!SIDS.length) { log('No sids passed (args.sids). Nothing to do.'); return {fixed:[]}; }

function chunks(arr,size){ const o=[]; for(let i=0;i<arr.length;i+=size)o.push(arr.slice(i,i+size)); return o; }

phase('Fix');
log(`Fixing ${SIDS.length} flagged rungs (severities: ${SEV.join(',')}).`);
const fixBatches = chunks(SIDS, 4);
const fixed = (await parallel(fixBatches.map(b => () =>
  tryAgent(fixPrompt(b), {schema:FIXBATCH, phase:'Fix', label:`fix:${b[0]}`, model:'opus'}, x=>x&&Array.isArray(x.fixes))
    .then(r=>(r&&r.fixes)||[]).catch(()=>[])
))).flat();

phase('Verify');
const vBatches = chunks(fixed, 6);
const verdicts = (await parallel(vBatches.map(b => () =>
  tryAgent(judgePrompt(b), {schema:VERDICT, phase:'Verify', label:`verify:${b[0]&&b[0].sid}`, model:'opus'}, x=>x&&Array.isArray(x.reviews))
    .then(r=>(r&&r.reviews)||[]).catch(()=>[])
))).flat();
const vmap = {}; for(const v of verdicts) vmap[v.sid]=v;

const clean = fixed.filter(f => vmap[f.sid] && vmap[f.sid].verdict==='clean');
const stillBad = fixed.filter(f => !vmap[f.sid] || vmap[f.sid].verdict==='flag');
log(`Fix done: ${clean.length}/${fixed.length} fixes verified clean; ${stillBad.length} still flagged (left for another pass).`);
return { fixed, clean: clean.map(f=>f.sid), still_bad: stillBad.map(f=>({sid:f.sid, v:vmap[f.sid]})) };
