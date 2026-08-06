export const meta = {
  name: 'geography-queue-dedup-sharded',
  description: 'Sharded pre-build dedup for the LARGE geography queue (the single-agent clusterer overflows 64K). 5 per-section agents cluster SAME-FACT topics WITHIN each section (full scope); 1 cross-section agent clusters same place/feature appearing across sections (compact name-only index). Read-only; unions the drop clusters for queue_dedup_apply.py.',
  phases: [
    { title: 'WithinSection', detail: 'one agent per section clusters same-fact topics using full scope' },
    { title: 'CrossSection', detail: 'one agent over the compact name index catches the same place in two sections' },
  ],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const SUBJECT = 'geography';
const QUEUE = `C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\${SUBJECT}\\_queue.json`;
const SECTIONS = ['city', 'nature', 'ancient', 'culture', 'earthsystem'];

// python -c reads (return JSON; no JS-escaping traps, no control chars)
function sectionCmd(sec){
  return `python -c "import json,sys;q=json.load(open(r'${QUEUE}',encoding='utf-8'));sys.stdout.write(json.dumps([{'id':t['id'],'name':t['name'],'strand':t.get('strand'),'scope':(t.get('scope') or '')[:220]} for t in q if t.get('section')=='${sec}']))"`;
}
function indexCmd(){
  return `python -c "import json,sys;q=json.load(open(r'${QUEUE}',encoding='utf-8'));sys.stdout.write(json.dumps([{'id':t['id'],'name':t['name'],'section':t.get('section'),'strand':t.get('strand')} for t in q]))"`;
}

const SCHEMA = { type:'object', additionalProperties:false, properties:{
  clusters:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    keep_id:{type:'string'},
    drop_ids:{type:'array', items:{type:'string'}},
    reason:{type:'string'}
  }, required:['keep_id','drop_ids','reason'] } }
}, required:['clusters'] };

const DUP_RULE = `A cluster is real ONLY if the topics would ask the SAME core facts (a kid would see near-identical questions). KEEP the richest / best-placed one: prefer the topic whose SECTION most naturally owns the place/fact and whose scope is deepest. DO NOT cluster topics that share a place but take genuinely DIFFERENT angles that yield different questions -- "Vienna" the CITY (its coffee-houses, its palaces) vs "The Waltz -- Vienna" the DANCE born there are NOT duplicates; "Rio de Janeiro" the city vs "Samba -- Rio" the music are NOT duplicates; the Great Pyramid vs the Great Sphinx are DIFFERENT monuments; a desert-as-a-place vs the rain-shadow PROCESS that dries it are NOT duplicates. When unsure, DO NOT cluster -- a false drop loses good content, a missed dup only costs one build. Every id must be a real id from the list.`;

function withinPrompt(sec){ return `You are the WITHIN-SECTION dedup pass for the "${sec}" section of a ${SUBJECT} quiz-bank topic queue. Each topic becomes a mini-bank of quiz "rungs" via an expensive research->author->judge->adversarial build, so building two topics that teach the SAME core facts is pure waste.

STEP 1 -- read this section's topics (PowerShell, do NOT modify): ${sectionCmd(sec)}
It prints a JSON array of {id, name, strand, scope} for every "${sec}" topic (scope = the per-rung plan, truncated).

STEP 2 -- find clusters of 2+ topics WITHIN this section that would produce OVERLAPPING questions (same core facts). ${DUP_RULE}

Return {clusters:[{keep_id, drop_ids:[...], reason}]} listing ONLY real same-fact clusters within this section (empty array if clean).`; }

function crossPrompt(){ return `You are the CROSS-SECTION dedup pass for a ${SUBJECT} quiz-bank topic queue. The queue was built by many independent researchers across five sections (city / nature / ancient / culture / earthsystem), so the SAME place or feature can appear under TWO sections (e.g. Petra as a city AND as an ancient marvel; Cappadocia under three; the Terracotta Army as a city site AND an ancient marvel; Djenne's Great Mosque as a town AND an ancient marvel). Each topic becomes an expensive build, so the same place built twice is waste.

STEP 1 -- read the compact topic index (PowerShell, do NOT modify): ${indexCmd()}
It prints a JSON array of {id, name, section, strand} for EVERY topic (no scope -- judge by the place/feature the name denotes).

STEP 2 -- find clusters of 2+ topics ACROSS DIFFERENT sections that name the SAME place or feature and would teach the SAME core facts. ${DUP_RULE} Focus on the same NAMED place/monument/feature appearing in more than one section. KEEP the one whose SECTION most naturally owns it (a carved ancient monument -> 'ancient'; a living city's wonders -> 'city'; a landform/earth-process -> 'nature'/'earthsystem'; a sacred place whose wonder is its reverence -> 'earthsystem' sacred; the dance/craft/script -> 'culture').

Return {clusters:[{keep_id, drop_ids:[...], reason}]} listing ONLY real same-place cross-section clusters (empty array if clean).`; }

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}

phase('WithinSection');
log(`${SUBJECT} sharded queue dedup: 5 within-section agents + 1 cross-section agent.`);
const within = await parallel(SECTIONS.map(sec => () =>
  tryAgent(withinPrompt(sec), {schema:SCHEMA, phase:'WithinSection', label:`within:${sec}`, model:'opus'}, x=>x&&Array.isArray(x.clusters))
    .then(r => ({sec, clusters:(r&&Array.isArray(r.clusters))?r.clusters:[]}))
));

phase('CrossSection');
const cross = await tryAgent(crossPrompt(), {schema:SCHEMA, phase:'CrossSection', label:`cross-section`, model:'opus'}, x=>x&&Array.isArray(x.clusters));
const crossClusters = (cross && Array.isArray(cross.clusters)) ? cross.clusters : [];

// union all clusters (tag origin for the review)
const allClusters = [];
for (const w of within) for (const c of w.clusters) allClusters.push({...c, origin:`within:${w.sec}`});
for (const c of crossClusters) allClusters.push({...c, origin:'cross-section'});
const drops = allClusters.reduce((n,c)=>n+((c.drop_ids||[]).length), 0);
log(`found ${allClusters.length} same-fact clusters -> ${drops} topics recommended for drop. Apply with: python bankbuild/queue_dedup_apply.py --subject=${SUBJECT} "<this task output>"`);
return { subject:SUBJECT, clusters:allClusters, total_drops:drops };
