export const meta = {
  name: 'geography-tone-audit',
  description: 'Independent Opus panel: read every geography ladder as a parent reviewing a kids\' game (ages 10-14). Flag gratuitously graphic/gruesome WORDING about disaster/death/atrocity, cruelty-or-suffering staged as entertainment, orientalist/condescending "exotic-mystical" tourist-brochure tone, and kid-inappropriate content. Honest dark place-history (eruptions, war sites, slave-trade memory, cremation ghats), told plainly and in the third person, is FINE. Read-only. BATCHED: one agent reviews args.batch ladders (default 5).',
  phases: [{ title: 'Audit', detail: 'one tone reviewer per batch of ladders' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const BATCH = Math.max(1, Number(A.batch) || 5);
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\geography\\ladders';

const RUBRIC = `You are reviewing a GEOGRAPHY quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank is a wonder-tour of the world's places -- cities, natural wonders, ancient marvels, cultures born in a place, and earth-processes. It honestly covers dark place-history: volcanic eruptions that buried cities, earthquakes and tsunamis, war memorials, the Atlantic slave-trade sites, cremation ghats, the Aral Sea's collapse, catacombs of bones. Honest history, told PLAINLY and in the THIRD person, is expected and STAYS. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. GRATUITOUSLY GRAPHIC / GRUESOME WORDING (the priority). Death, disaster, and human remains are a real part of geography (the ~6 million bones in the Paris Catacombs; the plaster casts of Pompeii's dead; a cremation ghat; a battlefield). Stated matter-of-factly they are FINE. FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the place fact needs: dwelling on bodies/gore/agony with relish, body-horror detail for its own sake. The test: would a parent wince at the WORDING, not at the fact that a volcano buried a city? (medium; high only if genuinely gruesome/nightmarish for a kid).

2. SUFFERING / ATROCITY STAGED AS ENTERTAINMENT. Honestly MENTIONING an atrocity as fact is OK (the Dutch massacre of the Bandanese; the transatlantic slave trade through Goree Island; a famine's geography). FLAG a rung that stages mass death, slavery, or human suffering as a fun/cool "did you know," treats it with relish or as a spectacle to enjoy, uses a smug/glib voice about real suffering, OR builds an ANSWER SET that makes a kid weigh atrocities against each other to score a point. (medium; high if it treats mass death or slavery as entertainment).

3. ORIENTALIST / CONDESCENDING TOURIST-BROCHURE TONE. A place's people, faith, or culture must be presented STRAIGHT and with respect. FLAG "exotic", "mystical", "primitive", "savage", scare-quotes around a belief or a people, a smug secular sneer at a sacred site, or gawking-at-the-strange-natives framing. (medium; high if it demeans a living people or faith). Honest wonder at a real achievement is CORRECT, not a violation.

4. KID-APPROPRIATENESS. (a) Anything sexual, crude, or otherwise off-limits for a 10-14 kid. (b) Gross-out overload (rot, remains, disease) in gratuitously graphic lingering detail beyond the place fact. (c) Content that would frighten or disturb a child out of proportion to teaching the place. FLAG.

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, gruesome, or creepy toward the reader in a way unrelated to teaching the place. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest dark place-history stated PLAINLY and in the THIRD person (eruptions, tsunamis, war sites, the slave trade, cremation, catacombs, famine geography), honest wonder at a real cultural or engineering achievement, and matter-of-fact natural hazard science are all EXPECTED and must STAY. You are flagging gratuitous GORE, suffering-as-fun, orientalist/condescending TONE, and kid-inappropriate WORDING -- NOT subject matter. When unsure, do NOT flag. Most ladders are clean.

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
const BATCH_AUDIT = { type:'object', additionalProperties:false, properties:{ audits:{type:'array', items:AUDIT} }, required:['audits'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'name':d['name'],'rungs':[{'tier':r['tier'],'stem':r['stem'],'choices':r['choices'],'answer':r['answer']} for r in d['rungs']]}))"`; }

function auditPrompt(ids){
  const reads = ids.map((id, k) => `  LADDER ${k + 1} (id="${id}"): ${readCmd(id)}`).join('\n');
  return `You are an INDEPENDENT tone/appropriateness reviewer for a kids' GEOGRAPHY quiz bank. Review ${ids.length} ladders as a careful parent would -- give EACH its own full, independent review.

STEP 1 -- read each ladder (run EVERY command, do not modify):
${reads}
Each prints {name, rungs:[{tier,stem,choices,answer}]}. idx = position in that ladder's rungs array.

${RUBRIC}

Audit EVERY rung of EVERY ladder. Return one audit object PER LADDER (${ids.length} total), each carrying its own id: worst_severity = highest among that ladder's flags ('none' if clean); verdict = 'flag' if any high/medium else 'clean'; note = one line. Do not skip or merge ladders.`;
}

function agentFailed(ids){ return ids.map(id => ({id, verdict:'flag', worst_severity:'high', flags:[{idx:-1, rule:'0', severity:'high', detail:'audit-agent-failed', fix:'re-run'}], note:'agent failed'})); }

phase('Audit');
const groups = [];
for (let i = 0; i < IDS.length; i += BATCH) groups.push(IDS.slice(i, i + BATCH));
log(`geography tone audit: ${IDS.length} ladders in ${groups.length} batches of ${BATCH} (parent's-eye: gratuitous gore + suffering-as-fun + orientalist tone + kid-appropriateness).`);
const nested = await parallel(groups.map(g => () =>
  tryAgent(auditPrompt(g), {schema:BATCH_AUDIT, phase:'Audit', label:`tone:${g[0].slice(0,16)}+${g.length}`, model:'opus'}, x=>x&&Array.isArray(x.audits))
    .then(r => (r && Array.isArray(r.audits) && r.audits.length) ? r.audits : agentFailed(g))
));
const results = nested.flat();
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`tone audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'geography', audited:results.length, flagged:flagged.length, results};
