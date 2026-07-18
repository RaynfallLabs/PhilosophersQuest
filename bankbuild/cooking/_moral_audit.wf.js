export const meta = {
  name: 'cooking-moral-audit',
  description: 'Independent Opus panel: score each stance-relevant cooking ladder against moral_vision.md + the cooking config (nutrition traditional-foods lean done fairly / no food-shaming / §18 adjacency drift / honest dark-history / no reveal-staging). Read-only -- flags only, never edits. BATCHED: one agent scores args.batch ladders (default 5).',
  phases: [{ title: 'Audit', detail: 'one moral-vision judge per batch of ladders' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const BATCH = Math.max(1, Number(A.batch) || 5);
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\cooking\\ladders';

const RUBRIC = `THE MORAL VISION for the COOKING bank (docs/quiz/moral_vision.md + bankbuild/subjects/cooking.json). The bank is PRACTICAL + WONDER-driven; most of it is settled food science, technique, provenance, and honest food history. It is NOT neutral on nutrition -- it LEANS traditional-foods. Score the ladder for VIOLATIONS of these:

1. NUTRITION STANCE -- the TRADITIONAL-FOODS LEAN, done FAIRLY (the priority on nutrition ladders; moral_vision §3.10 stance-vs-neutral). On the genuinely CONTESTED debates (seed oils, raw milk, the saturated-fat reversal, cholesterol revisionism, ultra-processed/NOVA, ancestral/paleo/keto, organic, non-celiac gluten) the bank STEEL-MANS BOTH sides and LEANS skeptical of industrial / ultra-processed / heated-seed-oil orthodoxy. VIOLATIONS: (a) the MAINSTREAM view strawmanned or sneered at -> FLAG HIGH; (b) a naive pro-industrial-orthodoxy claim keyed as flat settled fact with the debate erased ('seed oils are simply healthy', 'saturated fat simply causes heart disease') -> FLAG MEDIUM; (c) the traditional-foods side preached as smug advocacy ('and that's why processed food is evil') rather than presented -> FLAG MEDIUM. The correct answer should best SUMMARIZE the debate or state the traditional-foods case FAIRLY.

2. FIRM WHERE SETTLED -- the bank LEANS and states these as FACT (do NOT flag them as 'one-sided'): the 40-140F danger zone, cross-contamination from raw chicken, trans fats are harmful, reused fryer oil makes harmful aldehydes, nixtamalization prevents pellagra, whole foods generally beat ultra-processed, cooking makes some nutrients more/less available. A rung stating settled food science confidently is CORRECT, not a violation.

3. NO FOOD-SHAMING / MORALIZING (moral_vision §5-6). Present nutrition so a kid can DECIDE; do NOT moralize. FLAG a rung that shames ('if you eat X you are unhealthy / bad / weak'), assigns MORAL worth to eating choices, or induces food guilt. Empowerment ('here is what red meat gives you', 'here is what fat does') is CORRECT; shaming is a violation.

4. §18 ADJACENCY DRIFT (moral_vision §6 'adjacent-topic drift'; SHARED_PRINCIPLES §18) -- THE #1 STRUCTURAL CHECK. This bank is about the FOOD: how cooking works, where food comes from, the dish, the food story. A rung whose real SUBSTANCE is a human statute / agency / farm-subsidy / food-aid geopolitics / trade-law / policy debate -- and whose ANSWER is that law/agency/policy rather than a food fact -> FLAG (HIGH if the keyed answer IS the statute/agency/year/policy or a regulatory action like 'banned it'; MEDIUM if policy dominates but a food fact is present). Food-DRIVEN history where the FOOD is the anchor (the Banda islanders massacred over NUTMEG, the potato famine's blight + monoculture, sugar and the slave trade stated as fact) is FINE -- the food is the substance.

5. HONEST DARK HISTORY, PLAINLY (§4). Famine, slavery behind sugar/spice, poisonings, rationing, colonial food history are WELCOME stated matter-of-factly. VIOLATION: 'TIL: X is secretly bad/good' reveal-staging (moral_vision §6, both directions); a smug 'we now know better' voice; glib editorializing that blames a modern political side; or an atrocity flattened into a cute 'fun fact'. Honest fact = CORRECT; reveal-staging or sneering = FLAG.

6. SYMMETRIC RESPECT FOR FOOD TRADITIONS (§4). Where a religious or cultural food tradition appears (kosher, halal, Lent, Ramadan, a holiday dish, a coffee/tea ceremony), present it STRAIGHT and with respect -- no mockery, no scare-quotes, no 'primitive belief', no one tradition advertised as true over another. VIOLATION: any smug or mocking voice, or favoring/selling one tradition.

7. ACCURACY-STANCE / ANTI-PATTERN. A rung keying an ANACHRONISM as fact (tomatoes in Italy before ~1500, chili in Asia before the Columbian Exchange, universal fork-dining before the 18th c.), a wrong ATTRIBUTION keyed as correct (potato as Irish-native, Bolognese with spaghetti), or 'TIL secretly bad/good' reveal-staging -> FLAG.

CRITICAL GUARD -- DO NOT OVER-FLAG: the traditional-foods lean done FAIRLY, the firm settled-science leans (rule 2), honest dark food-history stated PLAINLY, straight respectful presentation of food traditions, and confident food science are all CORRECT. Flag only a genuine violation above. The #1 things to catch: adjacency drift (rule 4, an answer that is a law/policy not a food) and an unfair nutrition stance (rule 1, strawmanning the mainstream OR erasing a real debate OR preaching).`;

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
  return `You are an INDEPENDENT moral-vision auditor for the COOKING quiz bank a father is building for his kids. Score ${ids.length} ladders against the bank's values rubric -- give EACH its own full, independent score. Be fair but exacting; this is a VALUES + accuracy-stance check, NOT a craft check.

STEP 1 -- read each ladder (run EVERY command, do not modify):
${reads}
Each prints {name, strand, rungs:[{tier,stem,choices,answer,context}]}. idx = position in that ladder's rungs array.

${RUBRIC}

Audit EVERY rung of EVERY ladder. Flag a rung ONLY for a genuine VIOLATION above (not craft, not length). For each flag give idx + which rule (1-7) + severity + one concrete line. Remember the guard: the traditional-foods lean done fairly, the firm settled-science leans, honest dark history stated plainly, and straight respectful food traditions are CORRECT. The #1 catches: ADJACENCY DRIFT (rule 4 -- an answer that is a law/policy/regulatory action instead of a food) and an UNFAIR nutrition stance (rule 1).
Return one audit object PER LADDER (${ids.length} total), each carrying its own id: worst_severity = highest among that ladder's flags ('none' if clean); verdict = 'flag' if any high/medium else 'clean'; note = one line. Do not skip or merge ladders.`;
}

function agentFailed(ids){ return ids.map(id => ({id, verdict:'flag', worst_severity:'high', flags:[{idx:-1, rule:'0', severity:'high', detail:'audit-agent-failed'}], note:'agent failed'})); }

phase('Audit');
const groups = [];
for (let i = 0; i < IDS.length; i += BATCH) groups.push(IDS.slice(i, i + BATCH));
log(`cooking moral-vision audit: ${IDS.length} stance-relevant ladders in ${groups.length} batches of ${BATCH} vs moral_vision.md + cooking config`);
const nested = await parallel(groups.map(g => () =>
  tryAgent(auditPrompt(g), {schema:BATCH_AUDIT, phase:'Audit', label:`audit:${g[0].slice(0,16)}+${g.length}`, model:'opus'}, x=>x&&Array.isArray(x.audits))
    .then(r => (r && Array.isArray(r.audits) && r.audits.length) ? r.audits : agentFailed(g))
));
const results = nested.flat();
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'cooking', audited:results.length, flagged:flagged.length, results};
