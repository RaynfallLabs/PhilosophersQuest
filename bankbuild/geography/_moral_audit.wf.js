export const meta = {
  name: 'geography-moral-audit',
  description: 'Independent Opus panel: score each stance-relevant geography ladder against moral_vision.md + the geography config (celebrated Western/Discovery + indigenous civilizations done honestly / colonialism both-ways / Soviet-Maoist environmental record as fact / sacred sites respected / contested borders timeless / no climate alarmism / §18 lane drift). Read-only -- flags only, never edits. BATCHED: one agent scores args.batch ladders (default 5).',
  phases: [{ title: 'Audit', detail: 'one moral-vision judge per batch of ladders' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const BATCH = Math.max(1, Number(A.batch) || 5);
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\geography\\ladders';

const RUBRIC = `THE MORAL VISION for the GEOGRAPHY bank (docs/quiz/moral_vision.md + bankbuild/subjects/geography.json). The bank is WONDER-driven; most of it is settled earth science, place-wonder, and honest place-history. It is NOT neutral where moral_vision commits it, but it never WARPS a topic to force a stance. Score the ladder for VIOLATIONS of these:

1. §18 LANE / ADJACENCY DRIFT (moral_vision §6 'adjacent-topic drift'; SHARED_PRINCIPLES §18) -- THE #1 STRUCTURAL CHECK. This bank is about the PLACE: its landscape, its earth-process, its ancient marvel, or a culture born there. FLAG a rung whose real SUBSTANCE is an adjacent layer and whose ANSWER is not a place fact: (a) STRATEGIC/GEOPOLITICAL/TRADE-POLICY -- a chokepoint/supply-chain/export/statute/treaty/agency answer ('why Taiwan matters for chips', 'what Singapore exports', 'which treaty governs Antarctica' keyed as the answer) -> HIGH if the answer IS the policy/law/trade fact, MEDIUM if it dominates; (b) LANE-BORDER -- an ANSWER that is an animal's biology/anatomy (belongs to the ANIMAL bank) or a food's origin/recipe/ingredient (belongs to the COOKING bank), rather than the PLACE and its landscape -> FLAG MEDIUM (the place as scenery for a non-place payoff). Place-DRIVEN history where the PLACE/landscape is the anchor (Pompeii buried by Vesuvius, the Aral Sea drained, Goree Island's slave-trade memory) is FINE.

2. NO CLIMATE ALARMISM -- climate as descriptive EARTH SCIENCE (the geography config's firm line). Climate zones, monsoon mechanics, El Nino, glaciation cycles, rain-shadow, ocean currents are SETTLED science stated confidently and with wonder -- that is CORRECT, do NOT flag it as 'one-sided'. VIOLATION: a rung that adopts a 'climate change is destroying X' catastrophe/polemic frame as fact, editorializes doom, or blames a modern political side; SYMMETRICALLY, a climate-denial frame keyed as fact. Honest anthropogenic environmental FACT written on the land (the Aral Sea drained by Soviet cotton irrigation; a shrinking glacier stated plainly) is CORRECT -- it is fact, not alarmism.

3. CELEBRATED, done HONESTLY (moral_vision §1, §3 -- the LEAN, mark on vision_mandated ladders). The Age of Discovery / Western exploration and Western achievement (Roman roads, cathedral-builders, the spread of Christendom, English as lingua franca) are CELEBRATED as real human achievement. VIOLATION in EITHER direction: (a) a SELF-LOATHING anti-Western frame adopted as fact ('the West is uniquely evil') -> FLAG; (b) TRIUMPHALIST puffery that erases the honest costs, or a smug 'and that's why the West is best' sermon -> FLAG. Honest celebration WITH the costs stated is CORRECT.

4. INDIGENOUS CIVILIZATIONS -- CELEBRATED as FULL civilizations, NO CONDESCENSION (moral_vision §4). Inca roads, Maya astronomy, Polynesian wayfinding, Cahokia, Great Zimbabwe, Timbuktu's libraries treated as the real achievements they are. VIOLATION: any 'primitive' / 'exotic' / 'mystical' / tourist-brochure-orientalist framing or scare-quotes; SYMMETRICALLY, a romanticized noble-savage puffery that isn't honest. Straight, respectful, admiring-of-the-real-achievement = CORRECT.

5. COLONIALISM -- HONEST BOTH WAYS, no one-sided framing (moral_vision §3, §4; honest history is not strawmanning). State the costs (extracted labor, dislocation, the slave-trade sites) AND the benefits (legal systems, railways, ending practices like sati and foot-binding) plainly as geographic-historical fact. VIOLATION: a one-sided frame in EITHER direction keyed as the whole truth, or 'TIL: X was secretly bad/good' reveal-staging. Plain both-sided fact = CORRECT.

6. SOVIET / MAOIST ENVIRONMENTAL RECORD -- stated as FACT where written on the land (moral_vision §3.1): the Aral Sea, the Three Gorges displacement, the geography of the Great Leap famine, the Gulag map. VIOLATION: whitewashing it, or flattening it into generic climate-apocalypse polemic. Stated plainly = CORRECT.

7. SACRED SITES -- RESPECTED on their own terms, SYMMETRIC (moral_vision §4; theology symmetry). Mecca, Jerusalem, Varanasi, Bodh Gaya, Notre Dame, Hagia Sophia, Angkor Wat, Mount Kailash presented straight. VIOLATION: any smug secular dismissal ('primitive belief', scare-quoted deity, 'people used to think'), OR one faith advertised/sold as true over another, OR mockery. Doctrine belongs to the theology bank -- a geography rung should present the SITE and its meaning, not adjudicate the faith.

8. CONTESTED BORDERS -- named as TIMELESS geographic fact, no dated/partisan commentary, no false equivalence (moral_vision §5). A divided island, a watershed frontier, a de-facto vs de-jure line stated as geographic reality is CORRECT. VIOLATION: a rung that reads as present-day political hot-take, name-drops a current political figure, references a controversy of the past ~5 years, or otherwise DATES the bank; OR a partisan sneer.

9. ACCURACY-STANCE / ANTI-PATTERN. A FABRICATED place/date/height/coordinate/attribution keyed as fact -> FLAG HIGH; LEGEND or DISPUTED keyed as settled fact (the moai literally 'walked'; a geoglyph's purpose stated as settled; Atlantis as real) -> FLAG; 'TIL: X is secretly bad/good' reveal-staging of honest history -> FLAG; demographics stated with a taboo-driven distortion rather than plainly -> FLAG.

CRITICAL GUARD -- DO NOT OVER-FLAG: settled wonder, descriptive climate/earth science stated confidently, honest celebration of Western achievement WITH costs, indigenous civilizations celebrated, honest both-sided colonialism, honest environmental fact (the Aral Sea), sacred sites presented straight, and timeless border geography are ALL CORRECT. Flag only a genuine violation above. The #1 catches: LANE/ADJACENCY DRIFT (rule 1 -- an answer that is geopolitics/policy, or an animal-biology / food-origin payoff) and CLIMATE ALARMISM (rule 2).`;

const AUDIT = { type:'object', additionalProperties:false, properties:{
  id:{type:'string'},
  verdict:{type:'string', enum:['clean','flag']},
  worst_severity:{type:'string', enum:['none','low','medium','high']},
  flags:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    idx:{type:'number'}, rule:{type:'string'}, severity:{type:'string', enum:['low','medium','high']}, detail:{type:'string'}
  }, required:['idx','rule','severity','detail']}},
  note:{type:'string'}
}, required:['id','verdict','worst_severity','flags','note'] };
const BATCH_AUDIT = { type:'object', additionalProperties:false, properties:{ audits:{type:'array', items:AUDIT} }, required:['audits'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'name':d['name'],'strand':d.get('strand'),'rungs':[{'tier':r['tier'],'stem':r['stem'],'choices':r['choices'],'answer':r['answer'],'context':r['context']} for r in d['rungs']]}))"`; }

function auditPrompt(ids){
  const reads = ids.map((id, k) => `  LADDER ${k + 1} (id="${id}"): ${readCmd(id)}`).join('\n');
  return `You are an INDEPENDENT moral-vision auditor for the GEOGRAPHY quiz bank a father is building for his kids. Score ${ids.length} ladders against the bank's values rubric -- give EACH its own full, independent score. Be fair but exacting; this is a VALUES + accuracy-stance check, NOT a craft check.

STEP 1 -- read each ladder (run EVERY command, do not modify):
${reads}
Each prints {name, strand, rungs:[{tier,stem,choices,answer,context}]}. idx = position in that ladder's rungs array.

${RUBRIC}

Audit EVERY rung of EVERY ladder. Flag a rung ONLY for a genuine VIOLATION above (not craft, not length). For each flag give idx + which rule (1-9) + severity + one concrete line. Remember the guard: settled wonder, descriptive climate science, honest celebration with costs, celebrated indigenous civilizations, both-sided colonialism, honest environmental fact, straight sacred sites, and timeless border geography are CORRECT. The #1 catches: LANE/ADJACENCY DRIFT (rule 1) and CLIMATE ALARMISM (rule 2).
Return one audit object PER LADDER (${ids.length} total), each carrying its own id: worst_severity = highest among that ladder's flags ('none' if clean); verdict = 'flag' if any high/medium else 'clean'; note = one line. Do not skip or merge ladders.`;
}

function agentFailed(ids){ return ids.map(id => ({id, verdict:'flag', worst_severity:'high', flags:[{idx:-1, rule:'0', severity:'high', detail:'audit-agent-failed'}], note:'agent failed'})); }

phase('Audit');
const groups = [];
for (let i = 0; i < IDS.length; i += BATCH) groups.push(IDS.slice(i, i + BATCH));
log(`geography moral-vision audit: ${IDS.length} stance-relevant ladders in ${groups.length} batches of ${BATCH} vs moral_vision.md + geography config`);
const nested = await parallel(groups.map(g => () =>
  tryAgent(auditPrompt(g), {schema:BATCH_AUDIT, phase:'Audit', label:`audit:${g[0].slice(0,16)}+${g.length}`, model:'opus'}, x=>x&&Array.isArray(x.audits))
    .then(r => (r && Array.isArray(r.audits) && r.audits.length) ? r.audits : agentFailed(g))
));
const results = nested.flat();
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'geography', audited:results.length, flagged:flagged.length, results};
