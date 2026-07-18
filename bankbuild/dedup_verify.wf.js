export const meta = {
  name: 'dedup-verify',
  description: 'Verify queue_dedup clusters against the FULL built ladders before pruning (subject-generic). For each proposed cluster an agent reads keep + drop ladders and confirms per drop whether it is a TRUE same-fact duplicate (safe to remove) or a genuinely distinct angle to KEEP. Conservative: biased toward keeping validated content. Read-only; returns the confirmed drop set for dedup_prune_apply.py.',
  phases: [{ title: 'Verify', detail: 'read full ladders per cluster; confirm or spare each drop' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const SUBJECT = A.subject || 'cooking';
const CLUSTERS = Array.isArray(A.clusters) ? A.clusters : [];
const BATCH = Math.max(1, Number(A.batch) || 6);
const LADDIR = `C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\${SUBJECT}\\ladders`;

const VERDICT = { type:'object', additionalProperties:false, properties:{
  keep_id:{type:'string'},
  confirmed_drop_ids:{type:'array', items:{type:'string'}},
  kept_distinct_ids:{type:'array', items:{type:'string'}},
  note:{type:'string'}
}, required:['keep_id','confirmed_drop_ids','kept_distinct_ids','note'] };
const SCHEMA = { type:'object', additionalProperties:false, properties:{ verdicts:{type:'array', items:VERDICT} }, required:['verdicts'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'id':'${id}','name':d['name'],'rungs':[{'tier':r['tier'],'stem':r['stem'],'answer':r['answer']} for r in d['rungs']]}))"`; }

function prompt(clusters){
  const blocks = clusters.map((c, k) => {
    const keepR = `  KEEP candidate "${c.keep_id}": ${readCmd(c.keep_id)}`;
    const dropR = (c.drop_ids||[]).map(d => `  DROP candidate "${d}": ${readCmd(d)}`).join('\n');
    return `CLUSTER ${k + 1} (keep_id="${c.keep_id}"):\n${keepR}\n${dropR}\n  (tool's reason: ${c.reason || ''})`;
  }).join('\n\n');
  return `You are VERIFYING proposed duplicate clusters in a SHIPPED ${SUBJECT} quiz bank before any pruning. A first pass clustered topics it thinks teach the SAME facts and nominated one to KEEP and the rest to DROP. Your job: read the FULL ladders and decide, per DROP candidate, whether it is truly redundant.

STEP 1 -- read every ladder below (run EVERY command, do not modify). Each prints {id, name, rungs:[{tier,stem,answer}]}.

${blocks}

DECISION per DROP candidate:
- CONFIRM the drop ONLY if essentially ALL of its distinct FACTS (the answers + what each rung teaches) are already covered by the KEEP ladder (or another confirmed-kept ladder in the cluster) -- i.e. building both produced overlapping questions a player would notice as repetition.
- SPARE it (keep as distinct) if it carries a genuinely DIFFERENT angle or several unique facts the keep ladder lacks. When a drop candidate has 3+ facts the keep ladder does not teach, SPARE it.
Be CONSERVATIVE: these are all validated, gate-passing questions. A wrong drop deletes good content; a spared near-dup only costs a little redundancy. When genuinely unsure, SPARE.

Return one verdict per cluster: {keep_id, confirmed_drop_ids:[ids truly redundant], kept_distinct_ids:[drop candidates you SPARED], note:one line}. Every id must come from that cluster.`;
}

phase('Verify');
const groups = [];
for (let i = 0; i < CLUSTERS.length; i += BATCH) groups.push(CLUSTERS.slice(i, i + BATCH));
log(`${SUBJECT} dedup verify: ${CLUSTERS.length} clusters in ${groups.length} batches of ${BATCH} (full-ladder read, conservative).`);
const nested = await parallel(groups.map(g => () =>
  tryAgent(prompt(g), {schema:SCHEMA, phase:'Verify', label:`verify:${g[0].keep_id.slice(0,16)}`, model:'opus'}, x=>x&&Array.isArray(x.verdicts))
    .then(r => (r && Array.isArray(r.verdicts) && r.verdicts.length) ? r.verdicts : g.map(c=>({keep_id:c.keep_id, confirmed_drop_ids:[], kept_distinct_ids:c.drop_ids||[], note:'verify-agent-failed -> spared all'})))
));
const verdicts = nested.flat();
const confirmed = verdicts.reduce((n,v)=>n+(v.confirmed_drop_ids||[]).length, 0);
const spared = verdicts.reduce((n,v)=>n+(v.kept_distinct_ids||[]).length, 0);
log(`verify done: ${confirmed} drops CONFIRMED, ${spared} spared as distinct across ${verdicts.length} clusters.`);
return { subject:SUBJECT, verdicts, confirmed, spared };
