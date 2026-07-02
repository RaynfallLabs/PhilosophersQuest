export const meta = {
  name: 'history-moral-audit',
  description: 'Independent Opus panel: score every history ladder against moral_vision.md, tuned for history triggers (communism record, Western/Christian heritage, American exceptionalism + honest failures, no anti-Western framing, honest-not-preachy, no TIL-problematic, no condescension to the past). Read-only — flags only.',
  phases: [{ title: 'List', detail: 'enumerate history ladders' }, { title: 'Audit', detail: 'one moral-vision judge per ladder' }],
}
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});
let IDS = Array.isArray(A.ids) ? A.ids : [];
const LADDIR = 'C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\history\\ladders';

const RUBRIC = `THE MORAL VISION (docs/quiz/moral_vision.md v5) applied to the HISTORY bank. The bank is NOT politically neutral -- it is intellectually honest, standing in classical-liberal traditionalism with empirical-realist commitments. METHOD is fair (state what happened, real distractors, attribute interpretations); CONTENT is substantive. Score each ladder for VIOLATIONS:

1. HONEST, NOT PREACHY (§4) -- the #1 history trigger. NO editorializing at the reader: no 'modern audiences find this troubling', no 'we now know better', no 'sadly', no anachronistic moralizing. State hard facts plainly (Columbian Exchange mortality, Aztec human sacrifice, Assyrian atrocity, the Atlantic AND internal-African AND Islamic slave trades, the Holodomor, the Terror) WITHOUT a theatrical reveal or a lecture. The record is the argument.
2. NO 'TIL X IS SECRETLY GOOD/BAD' REVEAL (§6, both directions) -- no question whose punchline is 'this admired person/thing was actually bad' or 'this reviled thing was actually good'. Honest history states facts; it does not stage gotchas.
3. NO CONDESCENSION TO THE PAST OR ANY CULTURE (§4) -- premodern people were as smart as us (Aristotle wasn't stupid to think the heart thinks). No 'primitive belief', no 'exotic', no smug-modern superiority; non-Western civilizations presented on their own terms as real achievements. (Honest comparison is NOT condescension: some traditions built institutions -- rule of law, the abolition movement -- others did not; the bank may say so.)
4. NO IMPOSED VERDICT ON A GENUINELY CONTESTED INTERPRETATION -- attribute disputed causes/judgments to historians or figures, present rival readings. BUT: stating an established fact (the Holodomor happened; the death toll) is FACT, not an imposed verdict -- do NOT flag honest fact-stating as if it were bias.
5. NO SMUG-ATHEIST OR SMUG-BELIEVER VOICE in religious history (§4) -- no scare-quoted 'God', no 'people used to think', no 'and that's why X faith is true'. Every tradition (Christian, Jewish, Islamic, Hindu, Buddhist, Aztec, Norse, etc.) taken seriously on its own terms.
6. NO STRAWMAN (§6) -- every wrong choice is a real position or real misunderstanding, applied as strongly to Marxism/revolutions as to the West/religion.

=== WHERE THE BANK LEANS (moral_vision SS1/SS3/SS9 -- not neutral; still steel-man, never sneer) ===
- §3.1 COMMUNISM'S RECORD is established fact: ~65-100M civilian deaths (Black Book; Holodomor, Great Leap, Gulag, Killing Fields). A ladder must NOT go soft ('a controversial policy', 'some historians say'), whitewash, or omit the record on a communist-regime topic; Marxism-as-philosophy may be treated seriously, but the implementation's body count is stated plainly.
- §3.3/§3.4/§3.6 THE WEST + AMERICA are real human achievements (rule of law, universities, science, abolition-as-worldwide-crusade, natural rights, the American founding on principles not blood). Present as the achievement they are -- honest about failures (slavery, Trail of Tears, Jim Crow, internment, Tuskegee, colonial violence, wars of religion) stated plainly as part of the SAME record, but NOT self-loathing (the West defined by its sins) and NOT triumphalist (failures airbrushed). Christian heritage acknowledged, not apologized-for.
- §3.7 NO ANTI-WESTERN / ANTI-WHITE inherent-condemnation as fact; symmetric -- no group cast as inherently superior or inferior. §3.8 human sex is binary. §3.9 no positive 'right' to a good keyed as a natural right. Relativism/postmodern frame: present attributed, never adopt as fact.

Flag severity: HIGH = a kid is taught something the vision forbids (whitewashed communism, anti-Western-as-fact, a smug reveal keyed as the answer); MEDIUM = a preachy/editorializing/condescending stem or a soft-pedaled record; LOW = a mild tonal slip. verdict='flag' if any HIGH/MEDIUM. POSITIVE (note if present): wonder, ordinary ingenuity, courage-at-cost, honest plain-fact voice.`;

const AUDIT = { type:'object', additionalProperties:false, properties:{
  id:{type:'string'}, verdict:{type:'string', enum:['clean','flag']}, worst_severity:{type:'string', enum:['none','low','medium','high']},
  flags:{type:'array', items:{type:'object', additionalProperties:false, properties:{
    idx:{type:'number'}, rule:{type:'string'}, severity:{type:'string', enum:['low','medium','high']}, detail:{type:'string'}
  }, required:['idx','rule','severity','detail']}}, note:{type:'string'}
}, required:['id','verdict','worst_severity','flags','note'] };

async function tryAgent(prompt, opts, ok, tries){
  let last=null;
  for(let a=0;a<(tries||3);a++){ const r=await agent(prompt,{...opts,label:opts.label+(a?`.r${a}`:'')}).catch(()=>null); if(r&&(!ok||ok(r))) return r; last=r; }
  return last;
}
function readCmd(id){ return `python -c "import json,sys;d=json.load(open(r'${LADDIR}\\${id}.json',encoding='utf-8'));sys.stdout.write(json.dumps({'name':d['name'],'strand':d.get('strand'),'rungs':[{'tier':r['tier'],'stem':r['stem'],'choices':r['choices'],'answer':r['answer'],'context':r['context']} for r in d['rungs']]}))"`; }
function auditPrompt(id){ return `You are an INDEPENDENT moral-vision auditor for a HISTORY quiz bank a father built for his kids. Score ONE ladder against the values rubric. Fair but exacting; VALUES check, not craft.
STEP 1 -- read the ladder (PowerShell, do not modify): ${readCmd(id)}
It prints {name, strand, rungs:[{tier,stem,choices,answer,context}]}. idx = position.
${RUBRIC}
Audit EVERY rung. Flag ONLY genuine VALUES violations above. For each flag: idx + rule(1-6 or a SS number) + severity + one concrete line. worst_severity = highest ('none' if clean). verdict='flag' if any high/medium. note = one line. Return ONLY the JSON object.`; }

phase('List');
if (!IDS.length){
  const listPrompt = A.ids_file
    ? `Run this and return the result: read the JSON file '${A.ids_file}' — it is an array of id strings. Use PowerShell: Get-Content -Raw '${A.ids_file}'. Return ONLY a JSON object {"ids":[...]} with exactly those ids.`
    : `Run this and return the result: list every .json filename (WITHOUT the .json extension) in the folder ${LADDIR}. Use PowerShell: (Get-ChildItem -Path '${LADDIR}\\*.json').BaseName. Return ONLY a JSON object {"ids":[...]} with all of them (there are ~777).`;
  const r = await tryAgent(listPrompt,
    {schema:{type:'object',additionalProperties:false,properties:{ids:{type:'array',items:{type:'string'}}},required:['ids']}, label:'list-ids'}, x=>x&&Array.isArray(x.ids)&&x.ids.length>10);
  IDS = (r&&r.ids)||[];
}
log(`history moral-audit: ${IDS.length} ladders vs moral_vision.md (history-tuned)`);
phase('Audit');
// Single pass, 2 tries each. Caller keeps chunks small (~40) so total agents stay
// well under the 1000-agent workflow cap; whatever throttles is re-run in a later
// launch (a fresh launch after a gap dodges the throttle better than in-run retries).
const results = await parallel(IDS.map(id => () =>
  tryAgent(auditPrompt(id), {schema:AUDIT, phase:'Audit', label:`audit:${id.slice(0,20)}`, model:'opus'}, x=>x&&x.verdict, 2)
    .then(r => r || {id,verdict:'flag',worst_severity:'high',flags:[{idx:-1,rule:'0',severity:'high',detail:'audit-agent-failed'}],note:'agent failed'})));
const flagged = results.filter(r=>r&&r.verdict==='flag');
log(`history audit done: ${results.length-flagged.length}/${results.length} clean; ${flagged.length} flagged.`);
return {subject:'history', audited:results.length, flagged:flagged.length, results};
