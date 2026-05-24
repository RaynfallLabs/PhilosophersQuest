# Shared Principles for Quiz Bank Generation

Cross-subject rules every bank rebuild should respect. Subject-specific docs (PHILOSOPHY_FRAMEWORK.md, GEOGRAPHY_TEMPLATES.md, etc.) extend and specialize these; they don't replace them.

## Highest authority: docs/quiz/moral_vision.md

**`docs/quiz/moral_vision.md` is the soul of the bank.** It is the version-tracked rubric every quiz question in every subject is scored against. Read it FIRST and hold it as the highest guiding principle. Everything in this SHARED_PRINCIPLES.md, every subject FRAMEWORK + TEMPLATES, every gate, every exemplar is subordinate to moral_vision.md. If any rule in those docs conflicts with moral_vision.md, **moral_vision.md wins**.

What moral_vision.md contains:
- **§1 The tradition** — *classical-liberal traditionalism with empirical-realist commitments*; lineage Locke → American Founders → Tocqueville → Douglass-Lincoln-MLK → Austrian school (Menger-Mises-Hayek-Friedman-Sowell-Rothbard) → moral witnesses (Solzhenitsyn-Havel-Sakharov) → contemporary heterodox (Sowell, McWhorter, Loury, Hughes, Steele, Pluckrose, Lindsay, Haidt, Pinker, Scruton)
- **§1 seven meta-principles** — reality is non-negotiable; anti-totalitarianism foundational; Western tradition as real achievement; virtues formable; children deserve moral formation not abandonment; intellectual seriousness over slogans; dual commitments held together as the mark of seriousness
- **§2 What we celebrate** — wonder, curiosity-over-completion, ordinary ingenuity, courage in pursuit of truth, beauty of mechanism, surprise reversals, Western tradition as real achievement, the American experiment, virtue by example
- **§3 The historical record we do not omit** — communist death toll as fact; economic calculation problem; Austrian school proportional coverage; Christian intellectual heritage; serious critiques of contemporary identity frameworks; American exceptionalism as historical claim; racism rejected in all directions; sex in humans biologically binary
- **§9** — what the bank is NOT (negative definition; boundaries against failure modes)

Per moral_vision.md's own statement: *"If a rule conflicts with another in a particular case, the player's experience of wonder wins."* Wonder is the always-on override; substantive moral vision is the always-on commitment.

Also see [[feedback_moral_vision_substantive]] for the user's canonical articulation and per-subject refinements.

## Subject fit: principles are MENUS, not CHECKLISTS

**Not every principle here applies to every subject.** The principles are TOOLS to apply when the natural content of a subject calls for them — not CHECKLIST ITEMS to force into every bank. Warping content to ensure every principle appears in every subject is a failure mode.

The application question to ask each time: *"Does this principle ARISE NATURALLY from this subject's content, or am I forcing it?"* If forcing → drop it. Better to leave a principle unrepresented in a subject than to warp content to include it.

**Examples of WARPING to avoid:**
- Shoehorning Austrian Business Cycle Theory into a cooking question about bread-making just because moral_vision §3.3 mandates Austrian coverage in economics
- Forcing a Sowell-vs-Diamond debate into philosophy just because geography uses it
- Adding American-exceptionalism distractors to a question about Madagascar's lemurs
- Inserting a communist-death-toll reference into a question about photosynthesis

**Examples of legitimate subject exemptions:**
- Math and grammar are explicitly snappy-rote exceptions to wonder-led / scene-led
- Cooking doesn't need Sowell vs Diamond debates
- Geography doesn't need care-ethics critique
- Animal shouldn't reach for Austrian Business Cycle Theory

Why this matters: forced principles read as polemical or absurd — exactly what moral_vision.md's intro forbids ("a serious argument... should read as fascinating, not polemical"). Warping breaks the very standard the principle was meant to uphold.

See [[feedback_no_content_warping]] for the full subject-fit rough hierarchy (which principles fit which subjects naturally) and detailed application guidance for both new-bank builds and existing-bank audits.

## How to use

**Starting a new subject rebuild**: read this doc top-to-bottom, then audit existing subject docs (`PHILOSOPHY_*`, `ANIMAL_*`, `COOKING_*`, `GEOGRAPHY_*`, etc.) for relevant lessons before drafting new ones. Per [[feedback_lift_discovered_rules]] and [[feedback_understand_before_proposing]] — don't invent parallel systems when prior subjects have already solved a problem.

**Discovering a new universal rule during review**: lift it here (this doc), update the relevant feedback memory, propagate to live subjects opportunistically (don't bulk-flag gate-passing curated content per [[feedback_no_delete_validated_content]]).

## Universal principles

### 1. Inline teaching (no theory-stacking)
**Principle**: The question must be answerable by a smart reader who has NEVER encountered the specific names or terms. Definitions, context, or the scenario itself must do the teaching. Theory references in stems require concrete grounding (named person making a specific argument, specific historical event, specific quoted argument).

**Failures look like**:
- Undefined specialist terms used as the thing being tested
- Named historical figures used as required prior knowledge
- Theory-vs-theory stems with no concrete anchor
- Pure abstract framing battles ("Which move is the geographer making?" with no grounded scenario)

**Passes look like**:
- Every named position carries an inline definition
- Named figures appear in *context*, not as required-knowledge in the stem
- Pattern J (recognize-the-move) examples demonstrate the move concretely with a named figure
- The scenario teaches the concept before testing it

**Implementations**:
- **Philosophy**: `inline_teaching` (judgment gate, LLM-as-judge per PHILOSOPHY_TEMPLATES.md §8.2)
- **Geography**: `no_theory_stacking_check` (deterministic regex per GEOGRAPHY_TEMPLATES.md §8.1)
- **Cooking/Animal**: not yet ported — KNOWN GAP

### 2. Choice decoration parity
**Principle**: All four choices must share the same surface shape AND decoration pattern. The em-dash gate catches the dash structure, but within-shape decoration (parens with examples, quoted phrases, citations, in-line lists) must also match across all four. Any decoration unique to the correct answer is a skim-tell.

**Failures look like**:
- Only correct answer has parens with examples
- Only correct answer has a date or citation
- Only correct answer has a quoted phrase
- Three choices are noun-phrases; one is a sentence

**Passes look like**:
- All four use identical surface structure
- Decoration (parens, quotes, citations) appears in all four or none

**Implementations**:
- **All subjects**: `choice_shape_parity` (deterministic, em-dash presence only — partial coverage)
- **Animal/Cooking**: "citation skim-tell" anti-pattern (partial — only citations covered)
- **Geography**: full decoration mismatch anti-pattern in GEOGRAPHY_TEMPLATES.md §7.3
- **Philosophy**: dash-only — KNOWN GAP for broader decoration

### 3. Register consistency
**Principle**: Stem vocabulary tier matches choice vocabulary tier. No choice introduces a specialist term at a tier where the stem stayed simple. Per-tier expectations live in each subject's TEMPLATES §3 (the tier register table).

**Implementations**:
- **Philosophy/Animal/Cooking**: `register_consistency` gate
- **Geography**: not yet added — KNOWN GAP

### 4. Scenario-anchored correct (for fallacy/scenario questions)
**Principle**: The correct answer references scenario-specific tokens from the stem (named character, scenario keyword). Distractors should be more generic. Without this, the question becomes name-recall in disguise.

**Implementations**:
- **Philosophy**: `scenario_anchored_correct` (fallacy-only)
- **Animal**: partial port
- **Cooking/Geography**: not directly applicable in the same shape; subject-specific analogs may exist

### 5. Scaffolding-must-be-grounded
**Principle**: When a stem names something (place, person, event, technique) as scaffolding — not as the thing being tested — the stem must include enough anchor for a first-time reader to ground it. Recognition-type questions are exempt, but the description must still let the player ground without the name.

**Subject-specific implementations**:
- **Geography**: `place_anchor_check` — anchor mountain ranges, regions, countries (GEOGRAPHY_TEMPLATES.md §8.1)
- **Philosophy**: wonder-bias rule — anchor to canonical tradition not mundane modern (PHILOSOPHY_TEMPLATES.md §8.3; different flavor, same spirit)
- **Animal**: "anchor-to-source" credibility anchoring (similar spirit)
- **Cooking**: not yet documented — consider anchor for cuisines/regions, techniques/traditions

### 6. Wonder-bias / scenery aesthetic
**Principle**: Prefer grand / canonical / mythological framings over mundane modern when the underlying logic permits. The Christian-Crusader game setting aligns naturally. Logic stays, scenery upgrades.

**Scenery upgrades must touch ALL fields** — stem + answer + every distractor + context. A half-applied upgrade where the stem has been moved to canonical scenery (knight, alchemist, monastery) but the choices still reference the old mundane scenery (pop star, smartphone, group chat) creates a stem/answer mismatch. This is both a content bug (the question stops being internally coherent) and a skim-tell (the canonical-scenery distractor is recognizable as "the answer the rewrite was reaching for"). The pop-star-in-choices artifact found in philosophy T1/T2 fallacy questions (2026-05-24 audit §8) is the canonical example.

**Failures look like**:
- Stem describes an alchemist's apprentice arguing X; correct answer references a knight's strategy; one distractor still references "the group chat"
- Stem upgraded to knight/dragon/monastery scenery; context still cites a modern psychology experiment without ever bridging the two

**Passes look like**:
- All four choices use scenery drawn from the stem's world (knights, alchemists, monks, scribes, scholars, traders, peasants — not "TikTok," "group chat," "smartphone")
- Context, if it references modern research, does so as an aside ("modern psychology calls this X") rather than as the load-bearing scene

**Implementations**:
- **Philosophy**: explicit §8.3
- **Animal/Cooking/Geography**: implicit in scene-selection guidelines
- **Deterministic gate candidate**: regex sweep for mundane-modern tokens in choices when stem contains canonical-scenery tokens — not yet implemented
- See also: [[feedback_wonder_bias]]

### 7. No verdict on contested questions
**Principle**: For contested metaphysics/ethics/identity (and analogs in other subjects), the stem must NOT impose a yes/no verdict the bank then adjudicates. Attribute the claim to a character; make all choices competing schools.

**Implementations**:
- **Philosophy**: `no_verdict_on_contested` gate
- **Geography**: `no_climate_policy_verdict` (subject-specific variant)
- See also: [[feedback_no_verdict_on_contested]], [[feedback_surface_good_critique]]

### 8. Wonder lives in the stem (scene-led, not context-deferred)
**Principle**: Every question's wonder hook must live in the STEM — the stem leads with the amazing/surprising/discoverable. The choices test something specific (use, mechanism, named breakthrough) about that discovery. Context elaborates and deepens but is supplementary; the wonder must NEVER be deferred to context while the stem asks a rote proportion/number/date as the test.

**Failures look like**:
- Stem describes location + named feature; asks for a number ("about what fraction... ?") with wonder facts buried in context
- Stem is a setup; the test is rote recall (proportion, date, count, definition, capital name)
- Context contains all the amazing stuff; stem is dry

**Passes look like**:
- Stem leads with the wonder ("Socotra has been isolated for 6 million years; 1 in 3 of its plants exist nowhere else. Its dragon blood tree looks like an umbrella and weeps red sap. What was the sap prized for...")
- Choices test something specific that adds depth
- Context supplements but isn't load-bearing for wonder

**Implementations**:
- **All subjects**: implicit in "Wonder hook" framework rule #1 (PHILOSOPHY/ANIMAL/COOKING/GEOGRAPHY/etc. §"What this framework REQUIRES")
- **All subjects**: anti-rote regex gate (see [[feedback_no_rote_wonder]] for the canonical regex list)
- **Subject reviews 2026-05-19**: extensive evidence that "scene-led" is the universal voice across philosophy/animal/cooking/history/science/theology/economics/ai/trivia
- **Geography**: this specific structural failure (#17 Socotra wonder-deferred-to-context) wasn't caught by any deterministic gate — proportion-recall isn't matched by existing anti-rote regex because the stem doesn't open with "What is..." Subject TEMPLATES should add an anti-pattern entry explicitly.

**Discovered explicitly**: 2026-05-23 user flag during geography exemplar review. Pattern was already implicit across all subjects but never structurally codified.

### 9. Context is uncapped — teaching depth allowed
**Principle**: The `context` field of each question is **uncapped in length**. Stems and choices have per-tier caps (they govern reading time during play); context does not (it's teaching content shown after the answer, read at the player's pace). Capping context forces shallow educational depth, which conflicts with moral_vision §"What we celebrate — Beauty of mechanism" and §"Curiosity over completion."

**Failure mode if capped**: agents tighten context past readability or drop important named anchors (figures, dates, mechanisms) to fit cap. Loss of teaching depth.

**Implementations**:
- **Geography**: `gate_length_budget` overridden locally to skip context check (2026-05-23 directive); GEOGRAPHY_TEMPLATES.md §6 updated; GEOGRAPHY_FRAMEWORK.md tier sections updated
- **Cooking/Animal/Philosophy**: still cap context per their original gates — KNOWN GAP, candidate for re-audit per [[project_post_geography_audits]]

**Discovered**: 2026-05-23 during geography bulk-gen recovery. 357 of 890 length_budget hard-fails resolved by removing context cap; pass rate jumped from 27.5% to 56.6%.

### 10. Length caps must be calibrated, not copied
**Principle**: Per-tier length budgets for stems + choices must be **calibrated against the canonical analysis** (subject timer + chain target + reading speed), NOT blindly copied from another subject's gate file. Each subject has its own SUBJECT_TIMER in `src/player.py:12-27` — a math question on a 16s combat timer needs a tighter stem than a theology question on a 46s prayer timer. Inheriting another subject's caps without reviewing the timer asymmetry produces a mismatch.

**Failure mode**: Geography's `geography_structural_gates.py` was built by copying cooking's per-field caps (200/240/280/320/360 stem caps). But geography's timer (40s) differs from cooking's (60s), and the canonical TOTAL budget in `tools/quizgen/deterministic/length_budget.py` had STILL OLDER values for geography (280/480/680/900/1100) that hadn't been refreshed when the 2026-05-11 philosophy bump happened. Result: three inconsistent caps systems, none matching the actual quality bar of the user-approved exemplars.

**Named failure mode — "Dual cap systems must be reconciled"**: When subject scratch gates (`<subject>_structural_gates.py`) define per-field caps AND `tools/quizgen/deterministic/length_budget.py` defines canonical `SUBJECT_TIER_BUDGETS`, the two will drift apart over time unless explicitly reconciled. The post-geography audits (2026-05-24) found this pattern in all three remaining subjects (philosophy, animal, cooking) — per-field scratch caps permit MORE total chars than the canonical total budget allows. Reconciliation rule: the scratch gate is the early-warning surface (during generation), the canonical gate is the validation surface (post-bank), and the math of per-field caps × 5 must not exceed the canonical total. If empirical exemplar density exceeds either, BOTH must be lifted together. **Now seen in 4 subjects** (geography pre-fix + philosophy + animal + cooking). Worth a deterministic cross-check (assert max-sum of per-field ≤ canonical total) added to test suite.

**Calibration sources** (in priority order):
1. **Empirical**: user-approved exemplars are the quality bar. Compute their total-char distribution per tier; the budget should fit them with ~15% headroom.
2. **Analytical**: subject timer (player.py:12-27) ÷ chain target × reading speed (~30-50 chars/sec skim). Gives a derived budget independent of exemplars.
3. **Canonical**: `tools/quizgen/llm_jobs/validate_gameplay.md` + `tools/quizgen/deterministic/length_budget.py` SUBJECT_TIER_BUDGETS. The pipeline's actual gate.

**Reconciliation rule**: empirical + analytical must agree before updating canonical. If they don't, surface the contradiction to the user.

**Discovered**: 2026-05-23 during geography bulk-gen recovery. Exemplars T1 avg 416 chars vs canonical 280 budget — 2/8 passed. Geography canonical updated to {500, 620, 770, 900, 1000} to match exemplar density. `geography_structural_gates.py` switched from per-field caps to total budget for consistency with canonical.

**Implementations**:
- **Geography**: total-budget gate in `geography_structural_gates.py` (matches canonical in `length_budget.py`); per-field caps retained as advisory; GEOGRAPHY_TEMPLATES.md §6 documents both
- **Cooking/Animal/Philosophy**: still on per-field caps; canonical budgets in `length_budget.py` may be stale (geography pre-update was 280/480/680/900/1100; check if others were also bumped or are stale). **Backport audit candidate** per [[project_post_geography_audits]].

See also [[feedback_cap_calibration_logic]] (saved 2026-05-23) for the full reasoning chain.

### 11. Substantive moral vision (not false equivalence)
**Principle**: The bank teaches with substantive moral content where appropriate — honest communist death-toll record, serious Austrian-econ coverage, Western tradition celebrated, serious critics included. False equivalence is the failure mode. Implementation is subject-specific; the *commitment* is universal.

**Implementations**:
- **All subjects**: per [[feedback_moral_vision_substantive]]
- Subject docs vary in how they apply (philosophy's care-ethics-critique pattern; geography's Diamond-vs-Sowell; cooking's Western tradition; etc.)

### 12. Trailing-token corruption signature
**Principle**: A string field containing **3+ consecutive repeated words** is always a generation-pass bug — never a legitimate stylistic choice in teaching content. Bulk-gen LLM passes occasionally fail by looping on the last word as they approach a length budget ("…benefits ecosystems overall overall overall overall overall"). The corruption is mechanical and the fix is mechanical: strip the trailing repeats. The signature is general; the canonical detection is the regex `\b(\w+)(\s+\1){2,}\b` applied across stem + answer + every choice + context.

**Failures look like**:
- `"...patterns do not correlate with environment or behavior overall overall"`
- `"...has evolved only twice — once in insects and once in mammals overall overall overall overall"`
- (rare but plausible: mid-string token-loops from sampling artifacts)

**Implementations**:
- **All subjects**: `validate_trailing_tokens` deterministic gate in `tools/quizgen/deterministic/trailing_tokens.py` (2026-05-24)
- Registered globally in `pipeline.py`; no subject exemptions (math/grammar have no plausible legitimate trigger either)

**Discovered**: 2026-05-24 animal post-geography audit. 14 corrupted strings across 11 T5 animal questions. The fix script and the gate were added together; the gate ensures the corruption class cannot regress silently.

See also: [[feedback_lift_discovered_rules]].

## Before starting a new subject rebuild

Required reading order:
0. **`docs/quiz/moral_vision.md` — SUPREME.** Read first, hold as highest authority for everything that follows.
1. This doc (SHARED_PRINCIPLES.md)
2. The most-recent subject FRAMEWORK + TEMPLATES docs (philosophy + animal + cooking + geography as of 2026-05-23)
3. The corresponding `*_structural_gates.py` files
4. Relevant feedback memories ([[feedback_rebuild_discipline]], [[feedback_moral_vision_substantive]], [[feedback_no_rote_wonder]], etc.)

Required actions:
- Identify which universal principles from this doc apply
- Identify which need subject-specific implementation
- Identify which need new variants
- Draft your subject FRAMEWORK and TEMPLATES referencing this doc explicitly
- Cross-reference universal gates by name when possible (don't re-invent)

## After discovering a new rule during review

Per [[feedback_lift_discovered_rules]]:
1. **Check other subjects' docs FIRST** — grep `proposals/v2_audit/*_TEMPLATES.md` + `*_structural_gates.py` for related keywords before drafting
2. Fix the exemplar
3. If universal: update THIS doc (add to principles list with subject implementations)
4. If subject-specific: update the subject's FRAMEWORK and TEMPLATES
5. Encode as gate (deterministic or judgment, per pattern)
6. Save a feedback memory if the rule generalizes

## Open universal-implementation gaps (as of 2026-05-23)

These are KNOWN gaps where a universal principle is partially implemented or missing entirely:
- **Cooking/Animal**: no `inline_teaching` equivalent (Principle 1)
- **Philosophy/Animal/Cooking**: decoration mismatch only partial — citation skim-tell, not parens/quotes/lists (Principle 2)
- **Geography**: no `register_consistency` gate (Principle 3)
- **Cooking**: no scaffolding-must-be-grounded equivalent (Principle 5)
- **Animal**: no comprehensive wonder-bias rule (Principle 6)

These are NOT marked for immediate backport (per [[feedback_no_delete_validated_content]]). Apply forward to next subject rebuilds; backport opportunistically when specific failures surface during play or audit.
