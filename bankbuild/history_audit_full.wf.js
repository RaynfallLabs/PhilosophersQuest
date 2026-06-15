export const meta = {
  name: 'history-audit-full',
  description: 'Full-bank audit over a rung-range: skeptical craft re-judge + web fact-check, keyed by rung-id.',
  phases: [ { title:'Craft', detail:'adversarial re-judge vs the 14 rules' }, { title:'Fact', detail:'web-verify every keyed answer' } ],
}
const ALL = String.raw`C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\_audit_all.json`;
const A = (typeof args==='string')?JSON.parse(args):(args||{});
const START = Number(A.start)||0, COUNT = Number(A.count)||400;

const RULES = `WONDER: the answer must be the single most memorable, retellable fact (a NAMED thing or VIVID action) -- NEVER a bland venue/date/number/generic-label answer when drama sits in the stem (Drama-Available Rule). A number is OK only when the stem CONSTRUCTS it.
NO TELEGRAPH: no stem word that leaks the answer (its key noun; a category/visual only it matches; a verb revealing the mechanism; the stem stating the goal/effect only the answer achieves); the answer must NOT be the structural odd-one-out (only long/elaborated, only dual-named, only number); every distractor must be LIVE and SHARE the answer's category so the category word can't eliminate it.
LEGIBILITY: lead with the named subject (no dangling pronoun first); no false-friend word; pointed concrete closer (never "what's the takeaway?").
VOICE: active voice, responsibility named; no verdict imposed on a genuinely contested question.`;

const CRAFT = {type:'object',additionalProperties:false,properties:{reviews:{type:'array',items:{type:'object',additionalProperties:false,properties:{
  rid:{type:'string'},verdict:{type:'string',enum:['clean','flag']},severity:{type:'string',enum:['high','medium','low','none']},rule:{type:'string'},flaw:{type:'string'}
},required:['rid','verdict','severity','rule','flaw']}}},required:['reviews']};
const FACT = {type:'object',additionalProperties:false,properties:{checks:{type:'array',items:{type:'object',additionalProperties:false,properties:{
  rid:{type:'string'},verdict:{type:'string',enum:['verified','partly','unsupported','false']},confidence:{type:'string',enum:['high','medium','low']},note:{type:'string'}
},required:['rid','verdict','confidence','note']}}},required:['checks']};

async function tryAgent(p,o,ok){let last=null;for(let a=0;a<3;a++){const r=await agent(p,{...o,label:o.label+(a?`.r${a}`:'')}).catch(()=>null);if(r&&(!ok||ok(r)))return r;last=r;}return last;}
function readCmd(idx){return `python -c "import json,sys;d=json.load(open(r'${ALL}',encoding='utf-8'));i=${JSON.stringify(idx)};sys.stdout.write(json.dumps([d[k] for k in i]))"`;}

function craftPrompt(idx){return `You are an INDEPENDENT, SKEPTICAL auditor of a finished history quiz bank built for a father's kids. Every rung ALREADY PASSED an automated judge -- catch what it MISSED; assume nothing is good.
STEP 1 -- read your batch (PowerShell): ${readCmd(idx)}
Each item has {rid, topic, tier, stem, choices, answer, context}. Non-ASCII as \\uXXXX.
STEP 2 -- audit EACH against the bar:
${RULES}
Return one review per rung, echoing its rid: verdict 'clean'/'flag'; if flag, severity (high=owner would pull it; medium=he'd likely object; low=trivial) + rule + flaw (one line). Mostly-clean is expected for a good bank, but flag every real telegraph/skim-tell/weasel-closer/dead-name/passive/imposed-verdict.`;}

function factPrompt(idx){return `You are a FACT-CHECKER auditing a history quiz bank for a father's KIDS -- the most important check: the keyed answer must be TRUE and supported, or a child learns something false.
STEP 1 -- read your batch: ${readCmd(idx)}
Each item: {rid, topic, tier, stem, choices, answer, context}. 'context' usually names the bank's sources.
STEP 2 -- for EACH, VERIFY the keyed answer with WebSearch/WebFetch: confirm it is correct and supported (check the cited source + one independent source). Watch for fabricated quotes, wrong dates/numbers, mis-attributions, legends stated as fact.
Return per rung, echoing rid: verdict 'verified'/'partly'/'unsupported'/'false'; confidence; note (one line: what you found / the correction).`;}

function chunks(arr,s){const o=[];for(let i=0;i<arr.length;i+=s)o.push(arr.slice(i,i+s));return o;}
const idxs=Array.from({length:COUNT},(_,i)=>START+i);

phase('Craft');
log(`Full audit: rungs ${START}..${START+COUNT-1} (${COUNT}). craft + fact.`);
const craft=(await parallel(chunks(idxs,6).map(b=>()=>tryAgent(craftPrompt(b),{schema:CRAFT,phase:'Craft',label:`craft:${b[0]}`,model:'opus'},x=>x&&Array.isArray(x.reviews)).then(r=>(r&&r.reviews)||[]).catch(()=>[])))).flat();
phase('Fact');
const fact=(await parallel(chunks(idxs,3).map(b=>()=>tryAgent(factPrompt(b),{schema:FACT,phase:'Fact',label:`fact:${b[0]}`,model:'opus'},x=>x&&Array.isArray(x.checks)).then(r=>(r&&r.checks)||[]).catch(()=>[])))).flat();
log(`Window done: craft ${craft.length}, fact ${fact.length}. craft-flags ${craft.filter(r=>r.verdict==='flag').length}, fact-bad ${fact.filter(r=>['false','unsupported'].includes(r.verdict)).length}.`);
return {start:START,count:COUNT,craft,fact};
