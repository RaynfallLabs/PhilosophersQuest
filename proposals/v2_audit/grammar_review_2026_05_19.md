# Grammar Bank Review — 2026-05-19

**Bank:** `data/questions/grammar.json`
**Dropped file:** `data/questions/dropped/grammar.json`

## Bottom line

- **Before:** 1507 questions, T5 = 30 (170 short of the 200 floor)
- **After:** 1738 questions, T5 = 264 (+234 net)
- **Tier distribution:** T1=434, T2=314, T3=305, T4=421, T5=264
- **Validation:** `py -m tools.quizgen validate --subject grammar` → **1738 KEEP, 0 REPAIR, 0 DISCARD**
- **Tests:** `pytest -q` → **598 passed**

## Pass 1: Audit + Tier Discipline

### Schema & gates (already clean going in)

The bank already passed schema, length-budget, length-parity (answer-outlier rule), and anti-rote (grammar is exempt) gates with **zero failures**. No weird metadata fields existed in any record. The dropped file already contained 36 prior linguistics-theory entries with `_drop_reason` / `_fk` / `_old_tier` annotations.

Grammar is **exempt from the wonder filter** per memory (`feedback_no_rote_wonder.md`: math + grammar are the snappy-rote exceptions). Drill-style stems were left alone by design.

### Linguistics-theory drops (above-grade-10 stance)

**14 records moved from active bank to `dropped/grammar.json`:**

T4 (5 records) — the Pāṇini Aṣṭādhyāyī set. Sanskrit-grammar deep-dive with references to Chomsky/Bloomfield as the comparison anchors. All five drop.

- `#1261` Pāṇini's Aṣṭādhyāyī rule count
- `#1262` Aṣṭādhyāyī language analyzed
- `#1263` Pāṇini date + language
- `#1264` Pāṇini formal rigor "no Western linguistic work matched it until... Bloomfield, Chomsky"
- `#1265` Pāṇini foreshadowing "formal generative rule systems, which Chomsky..."

T5 (6 records) — linguistics theory:

- `#1486` Phonetics vs phonology theory ("Why does English have aspirated /p/ in 'pin' but not in 'spin'?")
- `#1490` Pāṇini Aṣṭādhyāyī rule precedence + "elsewhere principle"
- `#1494` "Semantics is the study of:" — generic linguistics theory question
- `#1496` Evidentiality markers (Tuyuca, Quechua) — deep linguistics
- `#1503` Verb valency / avalent / monovalent / divalent / trivalent — linguistic theory
- `#1504` Lenneberg's critical-period hypothesis — psycholinguistics

T5 (3 records) — Reed-Kellogg redundancy:

The bank held 3 Reed-Kellogg sentence-diagram questions plus one short-form trivia. Kept the strongest (`#1495`); dropped `#1477` (very similar), `#1491` (very similar), and `#1492` ("Reed-Kellogg sentence diagrams were invented in approximately:" — pure date trivia).

Each drop is annotated with `_drop_reason: linguistics_theory_beyond_grade10` or `_drop_reason: redundant_with_kept_variant`.

### Tier shifts (within caps)

- `#1493` ("Saying 'the White House announced' is metonymy") moved **T5 → T3**. Basic figurative-language identification, not advanced.
- `#1506` ("Which palindrome is famously said to have been written about Napoleon's exile?") moved **T5 → T4**. Clever but rote-historical trivia, not advanced grammar.

### Other observations (left alone)

- Various T1-T4 stems exceed FK 10 (e.g., "Greek *phobos* gives us 'phobia'. What does *phobos* mean?"). Per the user's brief, grammar uses a **subject-specific concept-tier scorer, not pure FK**. The deterministic gates pass, the content is unambiguously grade-appropriate, and these are valid where they sit.
- OED / Murray / Webster / Shakespeare references (~18 hits) are widely-known general knowledge, **not** linguistics theory. Left in place.
- T3 #895 (allophones in phonology) sits at the edge but is keyed to a concrete English example (aspirated /p/, dark/light /l/). Kept.
- Pāṇini contextual mentions in T1 #272 and T3 #852 are tangential (one date trivia, one etymology lead-in). Kept.

## Pass 2: New T5 Generation

Generated **262 candidate** T5 questions, of which **245 accepted** after pre-bank duplicate dedup (intra-set + against existing 1493). 17 rejected for ratio ≥ 0.85 against existing T5 (largely subjunctive / agreement / parallelism rewordings of an existing question).

**Topic coverage in final T5 = 264** (multi-tag, so totals exceed 264):

| Topic | Count |
|---|---|
| Verbals (gerunds, infinitives, participles, absolutes, danglers) | 33 |
| Rhetorical figures (chiasmus, zeugma, polysyndeton, asyndeton, anaphora, epistrophe, litotes, antithesis, hyperbaton, isocolon, tricolon, parataxis, hypotaxis, oxymoron, paradox, allusion, etc.) | 28 |
| Etymology / Latin & Greek combining forms | 28 |
| Confusables (advanced: lay/lie, who/whom, fewer/less, imply/infer, principal/principle, etc.) | 28 |
| Modality (epistemic vs deontic vs dynamic, modal nuance) | 27 |
| Clauses (independent / subordinate, restrictive / non-restrictive, noun / adverb / relative) | 27 |
| Advanced punctuation (em-dash, semicolon, colon, Oxford comma, complex lists) | 25 |
| Word order / syntax (objects, complements, transitivity, conjunction types) | 19 |
| Perfect aspect (present / past / future perfect + progressive + infinitive + participle) | 19 |
| Conditional types (0, 1, 2, 3, mixed, inverted) | 17 |
| Parallelism (in lists, correlatives, complex sentences) | 17 |
| Sentence structure (simple / compound / complex / compound-complex, cleft, inversion) | 17 |
| Tense / aspect nuance (habitual, stative, dynamic, inchoative, iterative) | 16 |
| Subjunctive (counterfactual, mandative, formulaic, after 'lest', wishes) | 15 |
| Pronouns advanced (reflexive, who/whom/whoever) | 9 |
| Reported speech / backshifting | 8 |
| Voice (passive transformations, agentless passive, modal passive) | 8 |
| Agreement (subject-verb advanced, collective nouns, neither/either + verb) | 3 |

All target topics from the brief covered:

- Subjunctive mood usage — 15 questions (counterfactual, mandative, formulaic, after 'lest', inverted)
- Perfect aspect — 19 questions (full paradigm)
- Conditional types — 17 questions (0/1/2/3/mixed/inverted)
- Parallelism — 17 questions (lists, correlatives, comparisons)
- Advanced punctuation — 25 questions (em-dash, semicolon, colon, Oxford comma, ellipsis, etc.)
- Rhetorical figures — 28 questions (every figure named in the brief plus several more)
- Independent vs subordinate clauses — 27 questions (with multiple subordinators)
- Restrictive vs non-restrictive — covered within clauses topic
- Advanced sentence structure — 17 questions (simple/compound/complex/compound-complex, cleft, inversion)

## Constraints met

- **TIER_CAPS** — grammar uses concept-tier scoring, not pure FK. All new T5 questions stay within concrete grade-10-appropriate vocabulary and concepts (no Chomsky/Saussure/Sapir-Whorf/philology terms in any new question).
- **5 deterministic gates** — `validate` returns 1738/0/0.
- **`pytest -q`** — 598 passed.
- **Stance** — No descriptivist-vs-prescriptivist activism. Standard American English presented neutrally throughout.

## Operational notes

- Scratch scripts kept under `tools/quizgen/scratch/` (gitignored):
  - `grammar_audit.py` — Pass 1 drops + tier shifts
  - `grammar_t5_gen.py` — Pass 2 T5 candidate generator (deterministic, hand-curated; no LLM calls)
  - `grammar_merge.py` — dedup + merge into bank
- Strategy was deterministic (Opus 4.7 author, no subagent spawns).
- Dropped file grew from 36 → 50 records (additive, all annotated with `_drop_reason`).

## What did NOT happen (and why)

- **No wonder-filter rewrites.** Grammar is explicitly exempt from the anti-rote and wonder filter (per `feedback_no_rote_wonder.md` and `anti_rote.py` EXEMPT_SUBJECTS). The rote drill style is the design.
- **No FK-only re-tiering.** TIER_CAPS notes the subject-specific scorer override for grammar; many T1-T4 high-FK stems are concrete, grade-appropriate concepts (e.g., "Greek *phobos* gives us 'phobia'") and were left alone.
- **No bulk delete of curated material.** Per `feedback_no_delete_validated_content.md`, the audit was additive and surgical — only 14 records dropped, all with clear above-grade-10 linguistics-theory grounds.
- **No play-testing.** Per `feedback_play_test_limits.md`, quiz-bank rebuilds use logic + validation tests, not Pygame play-testing.
