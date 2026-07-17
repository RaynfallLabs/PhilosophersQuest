export const meta = {
  name: 'cooking-tone-audit',
  description: 'Independent Opus panel: read every cooking ladder as a parent reviewing a kids\' game (ages 10-14). Flag gratuitous butchery/offal gore, cruelty-as-entertainment, alcohol glamorization, and gruesome dark-history WORDING. The prep-frame ("you sear/cut it") and honest butchery/food-safety/food-history facts are FINE. Read-only.',
  phases: [{ title: 'Audit', detail: 'one tone reviewer per ladder' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\cooking\\ladders';

const RUBRIC = `You are reviewing a COOKING quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank teaches how cooking works, where food comes from (including cuts of meat and offal), classic dishes, food history, amazing food facts, and nutrition. The in-game action is FOOD PREPARATION, so a second-person "you sear / knead / cut / prep it" frame is FINE and expected. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. GRATUITOUS BUTCHERY / SLAUGHTER / OFFAL GORE (the priority). Cuts of meat, offal (liver, kidney, tongue, tripe, sweetbreads), curing, and nose-to-tail cooking are a REAL, expected part of this bank -- stated matter-of-factly they are FINE. FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the food fact needs: dwelling on the killing/slaughter with relish, blood-and-viscera detail for its own sake, a body-horror description of an animal being cut apart. The test: would a parent wince at the WORDING, not at the fact that meat comes from animals? (medium; high only if genuinely gruesome/nightmarish for a kid).

2. CRUELTY AS ENTERTAINMENT. Honestly MENTIONING a practice as fact is OK (foie gras is force-fed goose/duck liver; some cooks boil lobster live; ortolan). FLAG a rung that frames an animal's SUFFERING as fun, cool, a thrill, or a spectacle to enjoy -- glorifying the cruelty rather than stating the food fact plainly. (medium; high if it invites the kid to relish the suffering).

3. KID-APPROPRIATENESS. (a) ALCOHOL: wine, beer, spirits, and cocktails may appear as HISTORY/technique/science, but NEVER glamorize drinking or teach a kid to get drunk -- flag consumption-glamorizing or how-to-get-drunk framing. (b) Gross-out overload: food poisoning, parasites, rot, maggots, mold described in gratuitously graphic, lingering detail beyond the safety/food fact. (c) Anything sexual, crude, or otherwise off-limits for a 10-14 kid. FLAG.

4. GRUESOME DARK-HISTORY WORDING. Honest food history is welcome and stays: famine, the slave trade behind sugar, the Banda nutmeg massacre, poisonings, rationing -- stated PLAINLY and matter-of-factly. FLAG ONLY wording that is gratuitously graphic/lingering about atrocity, that stages an atrocity as a fun/cool "did you know," or a smug/glib voice about real suffering. (medium; high if it treats mass death or slavery with relish or as entertainment).

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, gruesome, or creepy toward the reader in a way unrelated to teaching the food. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: the prep-frame ("you cut/sear/prep it"), matter-of-fact butchery / cuts / offal / curing, honest food-safety facts (raw chicken, the danger zone, cross-contamination, pathogens), honest nutrition, and honest dark food-history stated PLAINLY are all EXPECTED and must STAY. You are flagging gratuitous GORE, cruelty-as-fun, alcohol glamorization, and gruesome atrocity WORDING -- NOT subject matter, and NOT the cooking action itself. When unsure, do NOT flag. Most ladders are clean.

For each flagged rung give idx + rule(1-5) + severity + one concrete line + a one-line fix suggestion.`;

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

function auditPrompt(id){ return `You are an INDEPENDENT tone/appropriateness reviewer for a kids' COOKING quiz bank. Review ONE ladder as a careful parent would.

STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {name, rungs:[{tier,stem,choices,answer}]}. idx = position in the rungs array.

${RUBRIC}

Audit EVERY rung. worst_severity = highest among flags ('none' if clean). verdict = 'flag' if any high/medium, else 'clean'. note = one line overall.
Return ONLY the JSON object.`; }

phase('Audit');
log(`cooking tone audit: ${IDS.length} ladders reviewed as a parent (gratuitous gore + cruelty-as-fun + alcohol + dark-history wording).`);
const results = await parallel(IDS.map(id => () => tryAgent(auditPrompt(id), {schema:AUDIT, phase:'Audit', label:`tone:${id.slice(0,22)}`, model:'opus'}, x=>x&&x.verdict).then(r=>r||{id,verdict:'flag',worst_severity:'high',flags:[{idx:-1,rule:'0',severity:'high',detail:'audit-agent-failed',fix:'re-run'}],note:'agent failed'})));
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`tone audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'cooking', audited:results.length, flagged:flagged.length, results};
