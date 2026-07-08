export const meta = {
  name: 'animal-moral-audit',
  description: 'Independent Opus panel: score each stance-relevant animal ladder against moral_vision.md + animal.md (conservation-policy drift / contested-both-sides / hunting-advocacy / smug-myth-voice / anthropomorphism / accuracy). Read-only — flags only, never edits.',
  phases: [{ title: 'Audit', detail: 'one moral-vision judge per ladder' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
const IDS = Array.isArray(A.ids) ? A.ids : [];
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\animal\\ladders';

const RUBRIC = `THE MORAL VISION for the ANIMAL bank (docs/quiz/moral_vision.md + docs/quiz/subjects/animal.md). The bank is WONDER-DRIVEN with practical anchoring. It is NOT neutral on everything, but most biology is simply settled science. Score the ladder for VIOLATIONS of these:

1. CONSERVATION-POLICY / ADJACENCY DRIFT (moral_vision §6 'adjacent-topic drift'; animal.md §6; SHARED_PRINCIPLES §18) -- THE PRIORITY CHECK. This bank is about the ANIMAL: biology, behavior, senses, adaptation, life cycle, the creature. A rung whose real SUBSTANCE is a human statute / agency / treaty / policy debate -- the Lacey Act, Pittman-Robertson, the Duck Stamp Act, the Migratory Bird Treaty Act, 'which law protects this species', the North American Conservation Model's 7 principles as a list to memorize -- is HISTORY/POLICY, not animal. FLAG it (HIGH if the keyed answer IS the statute/agency/year; MEDIUM if policy dominates but an animal fact is present). A restoration STORY is fine ONLY when the rung teaches the animal (the population bottleneck, the biology, the vivid near-extinction moment). The conservation-funding framing is a STANCE the bank holds, never a quiz answer.

2. CONTESTED TOPICS -> BOTH SIDES, NO VERDICT. On genuinely contested animal topics the stem must NOT impose a verdict and a rung must NOT key one side as simply 'correct'/'enlightened': trophy hunting (funds conservation in some African models e.g. CAMPFIRE vs. ethical concerns), indigenous whaling/hunting rights (Makah, Inuit, Faroese), Pleistocene overkill (Paul Martin 1967) vs. climate-driven extinction, A2 vs. A1 milk, industrial vs. heritage/regenerative husbandry (CAFO concerns real AND cost/food-access tradeoff real), religious-slaughter pre-stunning debate, modern fur, blood sports (bullfighting/cockfighting/dog-fighting/fox-hunting). Keying/rewarding one side of these = FLAG MEDIUM (HIGH if it sneers at the other side).

3. HUNTING -- NO ADVOCACY EITHER DIRECTION. The bank holds hunting is a LEGITIMATE 200,000-year practice and teaches the real ethics hunters practice (fair chase, quick kill, no waste). VIOLATION in EITHER direction: (a) an 'all hunting is cruel/wrong' frame adopted as fact -> FLAG; (b) a PREACHY pro-hunting 'and that's why hunting is good' sermon -> FLAG. Wonder, not advocacy. Eating animals is BIOLOGY (humans are omnivores) -- a rung that smuggles a vegetarian/'is eating meat wrong' frame as fact -> FLAG.

4. HUMANE TREATMENT is a FIRM position (cruelty is wrong; Five Freedoms real) -- this is one place the bank LEANS; a rung stating cruelty is wrong is CORRECT, not a violation. Do NOT flag the humane-treatment lean.

5. MYTH/RELIGION -- SYMMETRIC RESPECT (§4). Egyptian, Greek, Roman, Norse, Hindu, Chinese, Native American, and Christian animal symbolism sit on the SAME plane. VIOLATION: any smug voice ('primitive belief', scare-quoted deity, 'people used to think'), OR one tradition favored/advertised ('and that's why X is true'), OR one tradition mocked. All are wonder, presented straight. The animal-rights MOVEMENT (Bergh, Singer, PETA) is a real phenomenon; Singer's argument is a POSITION someone holds -- neither endorsed nor strawmanned.

6. ACCURACY / ANTI-PATTERN VIOLATIONS (animal.md §6): anthropomorphizing as FACT ('the elephant cried' rather than 'displayed grief-like behavior') -> FLAG; a FABRICATED binomial or a species/date/attribution that is simply wrong -> FLAG HIGH; outdated taxonomy stated as current (Brontosaurus-is-invalid, dire-wolf-is-Canis, 'T. rex' as 'T. Rex') -> FLAG; 'TIL: X is secretly bad/good' reveal-staging of honest history -> FLAG.

7. SEX BINARY (§3.8). Reproductive diversity in OTHER species (clownfish sex change, parthenogenesis, hermaphroditism) is celebrated as WONDER on its own terms -- that is CORRECT and must NOT be flagged. VIOLATION only if a rung uses another species' biology as an ANALOGICAL claim about HUMAN sex being a spectrum.

8. EVOLUTION = STANDARD SCIENCE stated plainly (birds are theropod dinosaurs; whales from land mammals; deep time). A theological/creationist framing injected here (belongs in the theology bank) -> FLAG. Do NOT flag confident evolutionary science for 'not presenting both sides' -- it is settled, not a live fork.

CRITICAL GUARD -- DO NOT OVER-FLAG: settled biology, the humane-treatment lean, the hunting-is-legitimate lean, symmetric myth presented straight, and other-species reproductive wonder are all CORRECT. Flag only a genuine violation above.

POSITIVE (note if present, don't require all): wonder/curiosity, scene-led openings, concrete handles, real steel-manned distractors, the animal (not the policy) as the substance.`;

const AUDIT = { type:'object', additionalProperties:false, properties:{
  id:{type:'string'},
  verdict:{type:'string', enum:['clean','flag']},
  worst_severity:{type:'string', enum:['none','low','medium','high']},
  flags:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    idx:{type:'number'}, rule:{type:'string'}, severity:{type:'string', enum:['low','medium','high']}, detail:{type:'string'}
  }, required:['idx','rule','severity','detail']}},
  note:{type:'string'}
}, required:['id','verdict','worst_severity','flags','note'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'name':d['name'],'strand':d.get('strand'),'rungs':[{'tier':r['tier'],'stem':r['stem'],'choices':r['choices'],'answer':r['answer'],'context':r['context']} for r in d['rungs']]}))"`; }

function auditPrompt(id){ return `You are an INDEPENDENT moral-vision auditor for the ANIMAL quiz bank a father is building for his kids. You score ONE ladder against the bank's values rubric. Be fair but exacting; this is a VALUES + accuracy-stance check, NOT a craft check.

STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {name, strand, rungs:[{tier,stem,choices,answer,context}]}. idx = position in the rungs array.

${RUBRIC}

Audit EVERY rung. Flag a rung ONLY for a genuine VIOLATION above (not craft, not length). For each flag give idx + which rule (1-8) + severity + one concrete line. Remember the guard: settled biology, the humane/hunting leans, straight symmetric myth, and other-species reproductive wonder are CORRECT -- do not flag them. The #1 thing to catch is CONSERVATION-POLICY DRIFT (rule 1) -- a rung whose answer is a law/agency/year instead of the animal.
worst_severity = the highest among your flags ('none' if clean). verdict = 'flag' if any high/medium, else 'clean'. note = one line overall.
Return ONLY the JSON object.`; }

phase('Audit');
log(`animal moral-vision audit: ${IDS.length} stance-relevant ladders vs moral_vision.md + animal.md`);
const results = await parallel(IDS.map(id => () => tryAgent(auditPrompt(id), {schema:AUDIT, phase:'Audit', label:`audit:${id.slice(0,20)}`, model:'opus'}, x=>x&&x.verdict).then(r=>r||{id,verdict:'flag',worst_severity:'high',flags:[{idx:-1,rule:'0',severity:'high',detail:'audit-agent-failed'}],note:'agent failed'})));
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'animal', audited:results.length, flagged:flagged.length, results};
