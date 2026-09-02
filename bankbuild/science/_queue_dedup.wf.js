export const meta = {
  name: 'science-queue-dedup-sharded',
  description: 'Sharded pre-build dedup for the LARGE science queue (445 topics; single-agent clusterer overflows 64K). 5 per-section agents cluster SAME-FACT topics WITHIN each section (paged scope reads); 1 cross-section agent clusters the same discovery/figure/experiment appearing across sections (paged compact index). Read-only; unions the drop clusters for queue_dedup_apply.py.',
  phases: [
    { title: 'WithinSection', detail: 'one agent per section clusters same-fact topics using paged scope reads' },
    { title: 'CrossSection', detail: 'one agent over the paged name index catches the same discovery in two sections' },
  ],
}
const SUBJECT = 'science';
const QUEUE = `C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\${SUBJECT}\\_queue.json`;
// pages of 50 per section so each command's output stays under the tool-output cap
const SECTIONS = [
  { sec:'physics', pages:3 },
  { sec:'chemistry', pages:2 },
  { sec:'life', pages:2 },
  { sec:'earthspace', pages:2 },
  { sec:'howscience', pages:3 },
];
const IDX_PAGES = 3; // 445 topics / 150 per page

// python -c reads (return JSON; no JS-escaping traps, no control chars)
function sectionCmd(sec, page){
  return `python -c "import json,sys;q=[t for t in json.load(open(r'${QUEUE}',encoding='utf-8')) if t.get('section')=='${sec}'];sys.stdout.write(json.dumps([{'id':t['id'],'name':t['name'],'strand':t.get('strand'),'scope':(t.get('scope') or '')[:260]} for t in q[${page*50}:${page*50+50}]]))"`;
}
function indexCmd(page){
  return `python -c "import json,sys;q=json.load(open(r'${QUEUE}',encoding='utf-8'));sys.stdout.write(json.dumps([{'id':t['id'],'name':t['name'],'section':t.get('section'),'strand':t.get('strand')} for t in q[${page*150}:${page*150+150}]]))"`;
}

const SCHEMA = { type:'object', additionalProperties:false, properties:{
  clusters:{ type:'array', items:{ type:'object', additionalProperties:false, properties:{
    keep_id:{type:'string'},
    drop_ids:{type:'array', items:{type:'string'}},
    reason:{type:'string'}
  }, required:['keep_id','drop_ids','reason'] } }
}, required:['clusters'] };

const DUP_RULE = `A cluster is real ONLY if the topics would ask the SAME core facts (a kid would see near-identical questions). KEEP the richest / best-placed one: prefer the topic whose STRAND most naturally owns the story and whose scope is deepest. DO NOT cluster topics that share a figure or phenomenon but take genuinely DIFFERENT angles that yield different questions -- Marshall's full self-experiment ladder vs a mocked-vindicated PATTERN ladder that spends one rung naming him are NOT duplicates (a cross-link is not a dup); Newton's gravity ladder vs Newton's prism ladder are DIFFERENT discoveries; the double-slit (quantum weirdness) vs Young's original interference (light is a wave) are different angles IF their scopes key different facts. But TWO FULL LADDERS both telling the same arc with the same facts ARE duplicates (two Wegener ridicule-to-vindication ladders; two Perkin mauve-accident ladders; two Leeuwenhoek animalcule ladders; two Borlaug dwarf-wheat ladders; two Kepler eight-arcminute ladders) -- read the scopes and judge by FACT overlap, not by name alone. When unsure, DO NOT cluster -- a false drop loses good content, a missed dup only costs one build. Every id must be a real id from the lists.`;

function withinPrompt(s){
  const cmds = Array.from({length:s.pages}, (_,p)=>`  page ${p+1}: ${sectionCmd(s.sec,p)}`).join('\n');
  return `You are the WITHIN-SECTION dedup pass for the "${s.sec}" section of a ${SUBJECT} quiz-bank topic queue. Each topic becomes a mini-bank of quiz "rungs" via an expensive research->author->judge->adversarial build, so building two topics that teach the SAME core facts is pure waste.

STEP 1 -- read this section's topics in ${s.pages} page(s) (PowerShell, run EACH command, do NOT modify anything):
${cmds}
Each prints a JSON array of {id, name, strand, scope} (scope = the per-rung plan, truncated). Read ALL pages before judging.

STEP 2 -- find clusters of 2+ topics WITHIN this section that would produce OVERLAPPING questions (same core facts). ${DUP_RULE}

Return {clusters:[{keep_id, drop_ids:[...], reason}]} listing ONLY real same-fact clusters within this section (empty array if clean).`; }

function crossPrompt(){
  const cmds = Array.from({length:IDX_PAGES}, (_,p)=>`  page ${p+1}: ${indexCmd(p)}`).join('\n');
  return `You are the CROSS-SECTION dedup pass for a ${SUBJECT} quiz-bank topic queue. The queue was built by many independent researchers across five sections (physics / chemistry / life / earthspace / howscience), so the SAME discovery, figure, or experiment can appear under TWO sections -- e.g. Kepler's eight arcminutes seeded under both physics (Motion & gravity) and earthspace (Mapping the solar system); Wegener under earthspace (deep time) and howscience (mocked-then-vindicated); Margulis under life (cells) and howscience; Goddard under physics and howscience; Brownian motion under physics (energy/heat) and chemistry (atoms-real); the speed of light under physics (light) and howscience (measuring the world). Each topic is an expensive build, so the same story built twice is waste.

STEP 1 -- read the compact topic index in ${IDX_PAGES} pages (PowerShell, run EACH command, do NOT modify anything):
${cmds}
Each prints a JSON array of {id, name, section, strand} (no scope -- judge by the discovery/figure/experiment the name denotes; when two names look like the same story, that is a CANDIDATE cluster and your reason should say 'verify scopes').

STEP 2 -- find clusters of 2+ topics ACROSS DIFFERENT sections that name the SAME discovery/figure/experiment and would teach the SAME core facts. ${DUP_RULE} KEEP the one whose section most naturally owns it (a discovery's own domain strand usually beats a pattern-strand duplicate: Wegener's full story lives in deep time; the mocked-vindicated strand should hold DIFFERENT figures or a distinct pattern angle).

Return {clusters:[{keep_id, drop_ids:[...], reason}]} listing ONLY real same-story cross-section clusters (empty array if clean).`; }

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}

phase('WithinSection');
log(`${SUBJECT} sharded queue dedup: 5 within-section agents (paged reads) + 1 cross-section agent.`);
const within = await parallel(SECTIONS.map(s => () =>
  tryAgent(withinPrompt(s), {schema:SCHEMA, phase:'WithinSection', label:`within:${s.sec}`, model:'opus'}, x=>x&&Array.isArray(x.clusters))
    .then(r => ({sec:s.sec, clusters:(r&&Array.isArray(r.clusters))?r.clusters:[]}))
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
