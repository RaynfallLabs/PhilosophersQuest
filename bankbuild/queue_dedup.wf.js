export const meta = {
  name: 'queue-dedup',
  description: 'Pre-build efficiency gate: one Opus agent clusters SAME-FACT topics in an assembled subject queue so redundant ladders are dropped BEFORE they cost a full research->author->judge->adversarial build. Cross-strand duplicates (e.g. Maillard in kitchen AND baking) are the target. Read-only; returns drop clusters for queue_dedup_apply.py.',
  phases: [{ title: 'Cluster', detail: 'one agent over the whole topic list -> same-fact clusters' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const SUBJECT = A.subject || 'cooking';
const QUEUE = `C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\${SUBJECT}\\_queue.json`;

function listCmd(){
  return `python -c "import json,sys;q=json.load(open(r'${QUEUE}',encoding='utf-8'));sys.stdout.write(json.dumps([{'id':t['id'],'name':t['name'],'section':t.get('section'),'scope':(t.get('scope') or '')[:200]} for t in q]))"`;
}

const SCHEMA = { type:'object', additionalProperties:false, properties:{
  clusters:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    keep_id:{type:'string'},
    drop_ids:{type:'array', items:{type:'string'}},
    reason:{type:'string'}
  }, required:['keep_id','drop_ids','reason'] } }
}, required:['clusters'] };

function prompt(){ return `You are the PRE-BUILD DEDUP gate for a ${SUBJECT} quiz-bank topic queue. Each topic becomes a mini-bank of quiz "rungs" via an expensive research->author->judge->adversarial build, so building two topics that teach the SAME core facts is pure waste. Find the redundancy BEFORE the build.

STEP 1 -- read the topic list (PowerShell, do NOT modify): ${listCmd()}
It prints a JSON array of {id, name, section, scope} for every queued topic (scope = the per-rung plan, truncated).

STEP 2 -- find clusters of topics that would produce OVERLAPPING questions -- i.e. they teach the SAME core fact(s), just worded differently (e.g. three separate "the Maillard reaction / browning" ladders; two "tomato reaches Italy" ladders; the same dish or ingredient covered twice). For each such cluster of 2+ topics, pick the ONE best to KEEP and list the rest as drops.
  KEEP the richest / best-placed one: prefer the topic whose SECTION most naturally owns the fact and whose scope is deepest (more tiers / more distinct facts).
  A cluster is real ONLY if the topics would ask the SAME facts. DO NOT cluster topics that share a subject but take genuinely DIFFERENT angles that yield different questions -- e.g. "black pepper: the spice-trade drama" (history) vs "black pepper: the plant, a dried unripe berry" (botany) are NOT duplicates; a technique vs a dish that merely mentions it are NOT duplicates. When unsure, DO NOT cluster -- a false drop loses good content, a missed dup only costs one build.

Return {clusters:[{keep_id, drop_ids:[...], reason}]} listing ONLY real same-fact clusters (empty array if the queue is already clean). Every id must be a real id from the list.`; }

phase('Cluster');
log(`${SUBJECT} queue dedup: clustering same-fact topics from ${QUEUE}`);
const r = await agent(prompt(), { schema:SCHEMA, phase:'Cluster', label:`dedup:${SUBJECT}`, model:'opus' }).catch(()=>null);
const clusters = (r && Array.isArray(r.clusters)) ? r.clusters : [];
const drops = clusters.reduce((n,c)=>n+((c.drop_ids||[]).length), 0);
log(`found ${clusters.length} same-fact clusters -> ${drops} topics recommended for drop. Apply with: python bankbuild/queue_dedup_apply.py --subject=${SUBJECT} "<this task output>"`);
return { subject:SUBJECT, clusters, total_drops:drops };
