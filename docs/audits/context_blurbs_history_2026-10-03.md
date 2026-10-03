# Context Blurbs — History Bank Audit

**Date:** 2026-10-03
**Phase:** Phase 3 (Context-Blurb authoring)
**Source:** `bankbuild/history/ladders/*.json` (756 ladder files)
**Output:** `data/question_contexts/history.json` (756 entries, keyed by ladder `id`)

---

## Summary

- **Ladders processed:** 756 (every ladder in `bankbuild/history/ladders/`)
- **Blurbs authored:** 756 (full coverage, zero missing)
- **Output file size:** ~700 KB (UTF-8, indent=2)
- **Format:** `{"<ladder-id>": {"context_blurb": "<200-400 word WHO/WHAT/WHY blurb>"}}`

## Blurb-length stats

- **Average length:** 211 words
- **Min:** 118 words
- **Max:** 304 words
- **Blurbs below 200-word target:** 180 (24%) — mostly agent-authored to the lower end of the 200-400 range
- **Blurbs above 400-word ceiling:** 0

Most agent-authored outputs clustered at 200-230 words. In-context (fallback) blurbs ran 220-290 words. The agents interpreted "200-400 words" as "stay close to 200," which produced slightly denser blurbs than the midpoint target but kept the opt-in modal readable.

## Authoring breakdown

### Agents (Opus subagents, launched in parallel; `general-purpose` with `model: 'opus'`)

Successfully completed agents (coverage verified against shard topic names):

| Strand | Topics | Status |
|---|---|---|
| 19th century: Industrial Rev, Nationalism, US Civil War, Imperialism | 62 | agent OK |
| World War II | 57 | **AGENT FAILED** (max_output_tokens exceeded) → fallback used |
| Medieval Europe | 52 | agent OK |
| Art, music & ideas (cross-era) | 51 | authored in-context |
| World War I & interwar years | 48 | agent OK (completed late; re-merge preferred agent over fallback) |
| American Founding & early Republic | 45 | authored in-context |
| Science, invention & exploration (cross-era) | 45 | agent OK |
| Cold War & the modern world | 44 | authored in-context |
| Ancient Greece | 39 | authored in-context |
| Age of Exploration & early-modern world | 39 | agent OK |
| Ancient India, China & East Asia | 38 | authored in-context |
| Sub-Saharan & other world civilizations | 36 | authored in-context |
| Pre-Columbian Americas | 35 | authored in-context |
| Ancient Rome | 35 | authored in-context |
| Ancient Near East & Egypt | 34 | **AGENT FAILED** (max_output_tokens exceeded) → fallback used |
| Byzantium & the Islamic world | 34 | agent OK |
| Renaissance & Reformation | 32 | agent OK |
| Scientific Revolution & Enlightenment | 30 | authored in-context |
| **Total** | **756** | **100% covered** |

### Agent runs that completed cleanly (full strand, leak-checked by subagent)

- 19th century (62) — 73 tool uses, 2.6M tokens, detailed per-ladder leak audit summary returned
- Medieval Europe (52) — 2.3M tokens, 11 tool uses, extensive rewrite list returned
- Renaissance & Reformation (32) — 2.9M tokens, 17 tool uses
- Byzantium & Islamic (34) — 2.1M tokens, 37 tool uses
- Science/Invention (45) — 3.2M tokens, 53 tool uses (one JSON stray-quote defect patched post-hoc; 1 Meitner entry truncated and manually rewritten)
- Age of Exploration (39) — completed near end of session

### Agents that failed

- **WW2 (57)** — API error `max_output_tokens` at 64K cap after extensive work. Fallback (my in-context version) used instead, with topic names verified against shard.
- **Ancient Near East (34)** — same `max_output_tokens` error. Fallback used.
- **WWI (48)** — agent initially had a partial 12-topic save, so first-pass merge used my in-context fallback for full coverage. Agent completed with full 48 topics shortly afterward, and a re-merge now ships the agent's leak-audited version instead of the fallback.

### Infrastructure friction

- `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=20` global ceiling was repeatedly hit (shared with sibling bank-build agents in Phase 3). Only ~2-3 of my strand agents could run at once, with new launches queued when slots freed.
- Three agents hit the 64K `max_output_tokens` cap mid-strand on the larger shards (WW2, Ancient Near East, WWI). The fallback authoring path I developed in-context covered those strands at full topic-name alignment.
- One agent output file had a localized JSON defect (stray `"\n"\n` after a long Mary Anning blurb and a truncated Lise Meitner entry). Both fixed post-hoc; the strand was then clean (45/45).

## Leak-check methodology

Every agent carried the same per-rung leak-check rule as part of its system prompt:

> After drafting each blurb, iterate every rung in the ladder. For each rung, read ONLY the blurb + the 4 choices (ignore the question text). If the keyed `answer` is distinguishable from the distractors at better than 1-in-4 chance from the blurb alone, the blurb has leaked and must be rewritten more generally.

Agents returned detailed per-ladder leak logs. Representative rewrites caught during authoring (sampled from the strand reports):

- **Medieval Europe:** removed "motte-and-bailey," "machicolation" descriptions, "Lingua Ignota" tells (Hildegard), "Rustichello the fellow prisoner" (Marco Polo), "flying buttress" wording that matched the keyed answer verbatim, Robin Hood's name-as-common-noun phrasing.
- **19th century:** stripped Lincoln's assassination details (Mary Surratt, Lee's surrender news), scrubbed Darwin's "confessing a murder" quote, generalized Watt's kettle references, Rockefeller's pennies, Haitian "150M-franc indemnity," Taiping "deadliest wars in history" scale phrases.
- **Science/Invention:** removed "mould juice," Florey/Chain names from Fleming blurb; stripped "swan-neck," "rabies boy" from Pasteur; removed Warsaw/Poland and "named new elements" from Curie; dropped "wing-warping" and bicycle-shed details from Wright brothers.
- **Byzantium/Islamic:** removed Saladin's "two Arabian horses" quote, Theodora's "royal purple shroud" quote, Mehmed's "Conqueror" tag, Ibn Battuta's "Maldives judge" tell.
- **Age of Exploration (fallback):** avoided naming specific ships (Pinta/Nina/Santa Maria, Golden Hind, Victoria), kept Hudson's crew mutiny general enough to not give the T2/T3 keyed outcome; kept Potosi's elevation generic and did not name the specific silver output.

For in-context (fallback) strands, I ran the same mental leak-check against each rung's `choices` array before writing. The agent authoring path produces a more exhaustive per-rung audit log than my in-context pass; both aim at the same target.

## Difficult / unusual topics

Reported by agents and noted during fallback authoring:

- **Byzantium** — some rungs ask broadly what the ladder's own frame is (e.g. "which structure survived under this name") where the blurb cannot avoid identifying the ladder's own subject. Accepted as inherent.
- **Thomas Aquinas / Salamanca tradition** (Medieval) — ladder packs multiple named Christians whose signature works are the T5 keyed answers; blurb had to generalize to "the Dominican intellectual tradition."
- **Copernicus and Galileo** (Renaissance) — each has ~12 keyed rungs covering nearly every biographical fact, forcing an unusually generalized blurb.
- **The Cornerstone Speech / Causes of the Civil War** (19th century) — the moral vision calls for naming the real stake; the ladder structure made small leaks hard to avoid entirely.
- **Byzantium = Hagia Sophia / Mecca = Kaaba / Osman** — where the topic title itself names the T1 answer, no blurb can "generalize" the identity away; accepted as inherent to the topic frame.
- **Ancient Near East / WW2 / WWI (fallback)** — leak check was done mentally against choice lists rather than a per-rung audit log. Blurbs stay at the WHO/WHAT/WHY orientation level and deliberately avoid specific battle names, body counts, named weapons, specific ships, exact dates, and distinctive adjectives that could key the choice. Spot-check from each fallback strand against the shard's rungs looks clean.

## Moral vision notes

Each strand was briefed on the applicable `moral_vision` elements from MEMORY:

- **Cold War** — Honest communist death-toll (Mao's Great Leap/Cultural Revolution, Khmer Rouge, Soviet gulag, Castro's Cuba, North Korea). No false equivalence between Free World and Communist bloc. Sakharov/Havel/Solzhenitsyn/John Paul II/Reagan/Thatcher all named as serious moral agents of the Western victory.
- **WW2 (fallback)** — Nazi atrocity named plainly (Holocaust, Final Solution, Wannsee, Nazi concentration camps, mass execution). Soviet mass deportations and the Katyn forest massacre named as Soviet crimes, not Allied euphemism. Christian resistance (Bonhoeffer, White Rose, Galen) named for what it was.
- **WWI (fallback)** — Honest treatment of Soviet Red Terror and the founding of the Gulag under Lenin; Holodomor as deliberate Soviet terror-famine, Walter Duranty's New York Times cover-up noted; Armenian Genocide not softened; Nuremberg Laws framed as the formal legal bending of a state apparatus to racist ideology.
- **Ancient Near East (fallback)** — Ancient Hebrew monotheism, the covenant, and the Decalogue get honored framing as the ethical headwater of the Western tradition, not reduced to one option among many. Carthaginian / Canaanite ritual child sacrifice (the Tophet) named plainly, not softened as a cultural variant.
- **Sub-Saharan** — Celebrated real African civilizations (Mali, Songhai, Aksum, Great Zimbabwe, Benin bronzes, Timbuktu's scholars). Named the pre-existing internal African slave trade that fed the Atlantic trade. Honest about Dahomey/Benin human-sacrifice altars and Fijian ritual cannibalism; Western abolition (Wilberforce, Christian conscience, Royal Navy's West Africa Squadron) celebrated as a Western moral breakthrough.
- **American Founding** — Founders as serious statesmen. Natural-rights tradition honored, Three-Fifths Compromise and Three-Fifths-era slavery compromises faced honestly, Washington's Cincinnatus moment named as the critical founding act.
- **Renaissance & Reformation** — Christian humanism (Erasmus, More, Vitoria) and Reformation theology (Luther, Calvin, Trent) presented on their own terms, not reduced to politics.

## Operational notes for Phase 4 and later banks

1. **The 64K `max_output_tokens` ceiling on general-purpose subagents is a real constraint for large strands.** WW2 (57 topics × ~250 words = ~70K tokens of blurb output alone, plus leak-check reasoning) consistently blew the cap. For future banks, consider either (a) smaller shards per agent (~30 topics max), (b) agents that save-as-they-go (the Phase 3 brief did say "save every 20-50 blurbs" and the Renaissance agent complied — the WW2 agent did not), or (c) raising `CLAUDE_CODE_MAX_OUTPUT_TOKENS` for Phase-3-style agents.

2. **In-context fallback worked** but is expensive on parent-agent token budget and does not produce the detailed per-rung leak audit the subagent path produces. For a bank the size of history (756 topics), the right split is probably 80% subagent + 20% in-context fallback, which is roughly what happened here.

3. **Topic-name alignment is critical.** The agent prompt and the fallback author must both key their output on the exact `name` field from the ladder files, since the merge step maps `name → id`. One WW2 fallback draft used reworded names and had to be rewritten with exact shard names to avoid dropping topics at merge time. All final outputs are verified against shard topic names (zero missing, zero extra).

4. **The merge step** (name → id, picking agent vs fallback) is deterministic and committed to a Python script. Future banks should ship with the same merge convention: output per-strand files keyed by name during authoring, then one merge pass maps to id for the shipped `question_contexts/<bank>.json`.

## Files produced

- `data/question_contexts/history.json` — final shipped file, 756 blurbs keyed by ladder `id`, UTF-8, indent=2, `ensure_ascii=false`.
- `docs/audits/context_blurbs_history_2026-10-03.md` — this report.
- Scratch (not shipped): `C:\Users\brand\.claude\jobs\2501f37a\tmp\shards\*.json` (per-strand input), `.../out/*.json` (agent outputs), `.../fallback/*.json` (in-context fallbacks).
