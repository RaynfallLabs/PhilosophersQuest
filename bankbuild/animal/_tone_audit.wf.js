export const meta = {
  name: 'animal-tone-audit',
  description: 'Independent Opus panel: read every animal ladder as a parent reviewing a kids\' game (ages 10-14). Flag butcher-table/gameplay-frame leaks and gratuitously disturbing WORDING. Honest natural history (predation, death, scavenging) is fine. Read-only.',
  phases: [{ title: 'Audit', detail: 'one tone reviewer per ladder' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\animal\\ladders';

const RUBRIC = `You are reviewing an ANIMAL quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank teaches animal biology, behavior, adaptation, survival, and paleobiology with wonder. The in-game action is "harvesting," but the QUESTIONS must live in the animal's world, not on a butcher's table. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. BUTCHER-TABLE / GAMEPLAY-FRAME LEAK (the priority). A rung framed as the PLAYER processing a corpse: 'harvest table', 'you harvest / skin / gut / field-dress / haul it in', 'a carcass on your table/slab', a body being cut open by the reader, and ESPECIALLY nursing/feeding young pressed to a DEAD parent. The question must be set in the LIVING animal observed in nature. FLAG (high if a corpse-on-the-table or young-on-a-dead-parent image; medium for a softer 'you caught/killed it' frame).

2. GRATUITOUSLY DISTURBING / GORY WORDING for a 10-14 kid. Honest natural history is FINE and expected -- predation, scavenging, parasites, venom, death, whale-falls, barotrauma, roadkill, extinction -- stated matter-of-factly. FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the fact needs (e.g. dwelling on mutilation, 'eyes bulging out of its head, horribly deformed', a death described with relish, body-horror wording). The test: would a parent wince at the WORDING, not the fact? (medium; high only if genuinely nightmarish).

3. CRUELTY AS ENTERTAINMENT. A rung that frames an animal's suffering or a cruel practice as fun, cool, or spectacle rather than as biology or honest fact. FLAG.

4. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing/gruesome/creepy toward the reader in a way unrelated to teaching the animal. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest predation, death, parasitism, scavenging, venom, and extinction stated PLAINLY are the real biology of animals and MUST stay -- a lion eating a zebra, a wasp parasitizing a caterpillar, a vulture at a carcass, a fish eaten by a bigger fish, an animal that went extinct. You are flagging FRAMING and WORDING (the butcher-table frame, gratuitous gore, cruelty-as-fun), NOT subject matter. When unsure, do NOT flag. Most ladders are clean.

For each flagged rung give idx + rule(1-4) + severity + one concrete line + a one-line fix suggestion.`;

const AUDIT = { type:'object', additionalProperties:false, properties:{
  id:{type:'string'},
  verdict:{type:'string', enum:['clean','flag']},
  worst_severity:{type:'string', enum:['none','low','medium','high']},
  flags:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    idx:{type:'number'}, rule:{type:'string'}, severity:{type:'string', enum:['low','medium','high']},
    detail:{type:'string'}, fix:{type:'string'}
  }, required:['idx','rule','severity','detail','fix']}},
  note:{type:'string'}
}, required:['id','verdict','worst_severity','flags','note'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'name':d['name'],'rungs':[{'tier':r['tier'],'stem':r['stem'],'choices':r['choices'],'answer':r['answer']} for r in d['rungs']]}))"`; }

function auditPrompt(id){ return `You are an INDEPENDENT tone/appropriateness reviewer for a kids' ANIMAL quiz bank. Review ONE ladder as a careful parent would.

STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {name, rungs:[{tier,stem,choices,answer}]}. idx = position in the rungs array.

${RUBRIC}

Audit EVERY rung. worst_severity = highest among flags ('none' if clean). verdict = 'flag' if any high/medium, else 'clean'. note = one line overall.
Return ONLY the JSON object.`; }

phase('Audit');
log(`animal tone audit: ${IDS.length} ladders reviewed as a parent (butcher-frame + gratuitous-gore + cruelty).`);
const results = await parallel(IDS.map(id => () => tryAgent(auditPrompt(id), {schema:AUDIT, phase:'Audit', label:`tone:${id.slice(0,22)}`, model:'opus'}, x=>x&&x.verdict).then(r=>r||{id,verdict:'flag',worst_severity:'high',flags:[{idx:-1,rule:'0',severity:'high',detail:'audit-agent-failed',fix:'re-run'}],note:'agent failed'})));
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`tone audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'animal', audited:results.length, flagged:flagged.length, results};
