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

### 13. The Wonder Pattern — cool-fact-is-answer + Drama-Available + Hierarchy
**Principle (refined through five iterations of user-flagged failures during the 2026-05-24 history rebuild)**: The answer to every question must be the **most memorable specific cool fact** available about the event. Walking up from weakest answer-types to strongest:

**Hierarchy of Cool-Fact Types** — always prefer higher tiers when the event supports them:
- **TIER 1 — NAMED THINGS** (strongest): specific quotes (`"Victory or Death"`, `"Kiss me, Hardy"`, `"Sic semper tyrannis"`), cultural terms (`"lotus foot"`, `"samizdat"`, `"kamikaze"`), titles/epithets (`"the Hammer"`), named objects (the True Cross, the Cyrus Cylinder)
- **TIER 2 — VIVID ACTIONS**: specific physical acts (Pascal sewing parchment into his coat; Brunelleschi tapping the egg flat; Cleopatra fleeing with 60 ships)
- **TIER 3 — OBJECTS / MATERIALS**: items with memorable properties (obsidian knives, Tycho's silver nose, herringbone bricks)
- **TIER 4 — NUMBERS**: weak — use ONLY when SINGULAR and UNFORGETTABLE (Wright Brothers 12 seconds, Lincoln 272 words, Joan at 19, Mandela 27 years, Halley's Comet 76 years). **Never as a magnitude-pick** (`"about how many millions"`) when a Tier-1 named thing exists.
- **TIER 5 — GENERIC LABELS** (BANNED as primary answers): battle names, place names, dates, country names, generic "what is this called?"

**The three-question test** (every question must pass before shipping):
1. **The Dinner Test** — does the ANSWER ALONE (not the stem) make a parent ask "wait, why?" If "Rouen, France" stops conversation cold but "Threw her ashes into the Seine" makes them ask "WHOSE ashes?", you wrote the wrong question.
2. **Most-memorable-detail test** — across all the cool facts available about this event, am I asking for THE most memorable? Or burying it in context?
3. **Drama-Available Rule** ⚠ STRICTEST RULE ⚠ — if stem contains drama (fire, blood, death, escape, suicide, last words, betrayal, ashes, prison, torture, code phrases, dramatic acts) AND question asks for venue/date/label → STOP. The drama IS the cool fact. Ask about THAT.

**Failures look like** (these are the actual user-flagged cases that taught the rule):
- Wesley/Aldersgate "strangely warmed" — obscure figure + trivial single-word distinction = delete or repurpose around horseback miles
- Nelson at Trafalgar / "Thank God I have done my duty" — chose the dutiful line over the funnier "Kiss me, Hardy"; ALSO had a distractor paraphrasing the real "Kiss me, Hardy" line
- Joan of Arc at Rouen / "Where was she executed?" — burned alive + ashes in Seine + last word "Jesus" in stem; asked the venue
- Battle of Actium / "What is this battle called?" — Cleopatra fleeing with her lover and both killing themselves in stem; asked the venue
- Chinese foot binding / "Approximately how many millions?" — `"lotus foot"` is the Tier-1 cultural term sitting right there; asked the magnitude pick

**Passes look like**:
- Trenton: stem has Christmas-night-crossing + Hessians-at-dawn; answer is `"Victory or Death"` (password). Tier-1 phrase.
- Trafalgar: stem has Nelson-dying + Hardy-kneeling; answer is `"Kiss me, Hardy"`. Tier-1 quote + context-reveal of older English usage.
- Joan: stem has burned-alive + 19-years-old + ashes; answer is `"Threw her ashes into the Seine"`. Tier-2 vivid action + context-reveal of WHY (deny French any relic).
- Lotus foot: stem has 1000-years + broken-toes + tens-of-millions-suffered; answer is `"A lotus foot (golden/silver/iron by size)"`. Tier-1 cultural term + named gradations + context-reveal of Western interventions that ended it.

**Implementations**:
- **History**: explicit in `HISTORY_TEMPLATES.md` §1 (THE controlling rule of the bank); five worked examples (Trenton, Trafalgar, Joan, Actium, lotus foot, Brunelleschi-as-5-questions); applied during 2026-05-24 history rebuild quality passes
- **All subjects (going forward)**: this principle generalizes. Future rebuilds and audits should treat the three-question test + the hierarchy as the universal voice rule. The Wonder Pattern is to history what `inline_teaching` is to philosophy + what `no_capital_recall` is to geography.
- **Cannot be deterministically gated** — requires reading judgment. The closest auto-detection is the Drama-Available scan (regex for drama keywords in stem + WH-word question structure) and the magnitude-pick scan (`how many` / `approximately how many` + all-numeric distractors). Both produce many false positives; human judgment required on the candidates.

**Discovered**: 2026-05-24 in five user-flagged cases during the history rebuild sample review. The rule was iteratively refined — each user push revealed a deeper version of the same underlying pattern. The final shape (Hierarchy + three tests) is the most-stable formulation discovered to date.

See also: `HISTORY_TEMPLATES.md` §1 (worked examples); [[feedback_lift_discovered_rules]].

### 14. Story-in-stem — substance must be LIVE, not context-deferred
**Principle (refined through the 2026-05-26 user flag during science rebuild Surgisphere review)**: The dramatic substance the kid is meant to learn — named figures, dates, dollar amounts, body counts, institutional failures, specific quoted phrases — must live in the **stem** (or be carried by the **answer** as the recognition skill). Context is supporting detail, NEVER the carrier of the story.

**Why this matters**: in *Philosopher's Quest* mechanics, the `context` field is shown to the player ONLY if they get the question wrong OR review at end of game. The vast majority of correct-answer plays don't see the context at all. Live learning happens at **stem + answer**. Anything buried in context is dead substance for the typical player.

This is the broader form of §8 (which addressed "wonder hooks" specifically) and §13 (which addressed "cool-fact-is-answer" in wonder subjects). §14 generalizes both to contested-topic recognition, institutional-failure substance, and any other dramatic content the kid is meant to extract.

**The user's canonical exemplar (Surgisphere T3, science bank, 2026-05-26)**:

> ❌ **Buried-story version**:
> - Stem: "The Surgisphere scandal of 2020 was one of the fastest implosions in modern medical research. What was published, where, and how quickly was it retracted?"
> - Answer: "Two papers in *The Lancet* and *NEJM* on COVID-19 treatments — retracted within weeks once the data couldn't be produced"
> - Context: "...The May 2020 *Lancet* paper used it to claim hydroxychloroquine increased COVID mortality... **WHO suspended HCQ trials based on the *Lancet* findings**. Within weeks, requests for data verification revealed the dataset's authenticity couldn't be confirmed..."
>
> The travesty — **WHO suspended hydroxychloroquine trials globally based on data that didn't exist** — was in context. The kid playing this question never saw the actual recognition skill.

> ✅ **Story-in-stem version**:
> - Stem: "A May 2020 *Lancet* study from a company called Surgisphere claimed hydroxychloroquine raised COVID death rates. WHO suspended its global HCQ trial within days. Both *Lancet* and *NEJM* retracted the papers within weeks: Surgisphere had no database. What does this illustrate?"
> - Answer: "A single fabricated paper passed peer review and changed global treatment policy in real time"
> - Context: supporting detail — Mehra et al., specific dates, James Watson + 200 co-signatories, retraction date June 4 2020

**Failures look like**:
- Stem is generic recall prompt ("what happened?", "describe", "explain", "what was published?")
- Answer is dry list of facts (journals, dates, retraction timing)
- Context contains the actual story: named figures, dollar amounts, body counts, policy consequences, dramatic specifics
- Players who get it right never see the substance

**Passes look like**:
- Stem leads with the full narrative: who, when, what, dramatic specifics, policy consequences
- Answer is the **recognition skill** the kid extracts from the story
- Context is **additional sources, secondary specifics**, not the carrier of the story

**Especially load-bearing for**:
- Contested-topic recognition (COVID, vaccines, climate, eugenics, replication crisis)
- Institutional-failure substance (PR-vs-method, capture-vs-rigor distinction)
- Reversal-arc stories (Wegener, Semmelweis, Marshall, GBD-then-NIH-director, Bhattacharya-fringe-to-director)
- Whistleblower / dissenter content (Twitter Files, Murthy v Missouri, FOIA reveals)

**Heuristic for catching this pattern in audit**:
- Stem ends in generic prompt ("what happened" / "what was the" / "explain" / "describe" / "what does this illustrate") without giving setup details
- Context length > stem length × 1.5 AND contains specific years / dollar amounts / named institutions not in stem+answer
- BUT human review required: the heuristic over-flags; many already-good questions have rich context. Only **rewrite** the ones where the cinematic detail is genuinely missing from the live moment.

**Implementations**:
- **Science**: 17 rewrites landed 2026-05-26 (Surgisphere, Sims/Anarcha/Betsey/Lucy, Stapel hotel room, Climategate "hide the decline", Joe Rogan #1757 protest, Feb 1 2020 Fauci/Farrar teleconference, etc.). See `_buried_story_audit.md` for the full triage + before/after.
- **All future subjects (going forward)**: this principle generalizes. Future rebuilds + audits should treat **story-in-stem** as a universal voice rule. The heuristic in `_hunt_buried_story.py` is reusable across subjects.
- **Cannot be deterministically gated** — requires human reading judgment. The heuristic narrows candidates; the agent (or human auditor) decides KEEP vs REWRITE.

**Discovered explicitly**: 2026-05-26 user flag during science Surgisphere review. Pattern was implicit across all subjects but never codified at this level of generality.

See also: §8 (wonder lives in stem), §13 (Wonder Pattern cool-fact-is-answer), `_hunt_buried_story.py` (heuristic), `_buried_story_audit.md` (worked examples).

### 15. No weasel closers — questions must be pointed and concrete
**Principle (refined through the 2026-05-26 user flag during economics financial-literacy review)**: The final question in every stem must be POINTED, CONCRETE, and LEGIBLE. It must ask about something SPECIFIC in the substance. Abstract meta-framings as closers are an anti-pattern.

**Why this matters**: A stem can have beautiful §14 story-in-stem substance (named figures, dates, dollar amounts, dramatic specifics) and still fail the kid if the final question is a vague meta-prompt. The kid then has to pick "the abstract framing" rather than answer a concrete inquiry. Real questions ask real things.

**Banned closers** (the canonical weasels — caught by the regex in `_hunt_weasel_closers.py`):
- "What's the recognition?"
- "What's the recognition skill?"
- "What's the takeaway?"
- "What's the substance?"
- "What's the lesson?"
- "What's the pattern?"
- "What's the connection?"
- "What's the moral?"
- "What's the deeper lesson/point/recognition?"
- "What's the structural recognition?"
- "What's the kid's takeaway?"
- "What does this illustrate?"
- "What does this case/episode/story/incident illustrate/show/teach/reveal?"
- "What does this prove?"
- "What does this period/case demonstrate?"
- "Why does this matter?"

**The user's canonical exemplar (FICA tax-wedge question, economics financial-literacy supplement)**:

> ❌ "Your first $400 paycheck shows $337 deposited. The missing $63 is FICA (7.65%). Your EMPLOYER also paid $63 you never saw. **What's the recognition?**"
> → answer: "The employer half is also your wage — economists call this the tax wedge"

> ✅ "Your first $400 paycheck shows $337 deposited. The missing $63 is FICA (7.65%). Your EMPLOYER also paid $63 you never saw. **What do economists call the combined ~15.3% (employee + employer halves) hidden in this kind of paystub?**"
> → answer: "The tax wedge"

Same substance. Same recognition skill. But the second version asks a REAL question — "what do economists call X?" is concrete and answerable. "What's the recognition?" makes the kid hunt for the abstract framing.

**The fix template**:
- Identify what concrete thing in the substance the answer names
- Ask about THAT thing directly
- Use ordinary human question forms: "What do economists call ___?", "Who did ___?", "How much did ___?", "Which year ___?", "What's the technical name for ___?", "What was the specific consequence ___?", "Why specifically ___?"
- Avoid academic meta-prompts entirely

**Allowed closers** (specific concrete inquiries):
- "How much did inflation drop from, and to, under Volcker's chairmanship?"
- "Who has the authority to change Bitcoin's 21-million supply cap?"
- "What's the technical name for the gap between what your boss pays and what you take home?"
- "Which two specific bank failures in 2023 were the biggest?"
- "Specifically, what should a kid check before believing a 'new study shows X' headline?"
- "Who suspended its global HCQ trial in the weeks before the Lancet paper was retracted?"
- "What specific event launched the trial that built his political career?"

**Failures look like**:
- Beautiful §14 story-in-stem substance + weasel closer
- Stem has named figure + date + dollar amount + dramatic specific, then asks "What does this illustrate?"
- Closer is structurally identical to many other questions in the bank — refrain pattern (the §3 T5 P5 governance run that got compressed during the AI bank audit was this)

**Passes look like**:
- Closer is concrete, specific, ordinary-human-question-form
- Each closer is structurally different across questions
- Kid reads the closer and knows exactly what is being asked
- Answer is the natural reply to a real question, not the natural reply to "pick the abstract framing"

**Implementations**:
- **Economics + science (2026-05-26)**: 72 weasel-closers identified by `_hunt_weasel_closers.py` heuristic (19 science + 53 economics); rewritten with pointed-concrete closers in the same session
- **All future subjects (going forward)**: this principle generalizes. The heuristic in `_hunt_weasel_closers.py` should be re-run against every rebuild before commit
- **Cannot be deterministically gated** (yet) — requires reading judgment about whether the closer is concrete vs abstract. The regex catches the obvious weasels; a more general detector could be added later
- **§14 and §15 are companion rules**: §14 says SUBSTANCE must be in stem; §15 says the CLOSING QUESTION about that substance must be concrete

**Discovered explicitly**: 2026-05-26 user flag during economics financial-literacy supplement review. The user had been training me out of this pattern repeatedly across earlier sessions; codifying it now to break the recurrence.

See also: §14 (story-in-stem), §13 (Wonder Pattern cool-fact-is-answer), `_hunt_weasel_closers.py` (heuristic).

### 16. Teach before test — no question may assume a term it hasn't been given a chance to teach
**Principle (refined through the 2026-05-26 user flag on the Madoff Ponzi question)**: A question must not ASSUME the player already knows a technical term that the bank should be TEACHING. Foundational concepts (named figures, named events, technical terms) need to be introduced somewhere — either inline in the stem itself, or via a separate origin/biographical question elsewhere in the bank.

**Why this matters**: The player encounters questions in randomized order. If question #847 references "Ponzi scheme" or "Cantillon effect" or "tax wedge" without ever teaching what those things ARE, the player either already-knew the term (so the question taught nothing) or doesn't know it (so the question is unanswerable except by lucky-guess elimination).

**The user's canonical exemplar (Madoff Ponzi question, economics financial-literacy supplement)**:

> ❌ "Bernie Madoff returned ~10% per year for 47 years regardless of market conditions. Harry Markopolos warned the SEC starting in 2000. Madoff was arrested Dec 11 2008. What's the Ponzi tell?"

The question used "Ponzi" as if the player already knew what it meant. The bank had **7 questions using the word Ponzi but ZERO teaching who Charles Ponzi was** (1920, Boston, International Reply Coupon scheme, promised 50% in 45 days, scheme collapsed in months, became the namesake). The closer was also a §15 weasel ("What's the X tell?") on top of the assumed-knowledge failure.

**The fix template**:

> ✅ "Charles Ponzi promised investors 50% returns in 45 days in 1920 Boston, paying early investors with later investors' money until the scheme collapsed within a year. His name became the term for that kind of fraud. Bernie Madoff ran the largest one in history — claiming 10% annual returns for 47 years regardless of market conditions until he was arrested December 11, 2008. What specific pattern in Madoff's reported returns should have signaled fraud?"
> 
> → "The returns were too smooth — real investing has down years, but Madoff reported steady ~10% gains even during 1987, 2000-02, and 2008"

This stem teaches WHO Charles Ponzi was AND introduces Madoff as the canonical modern case AND asks a concrete pointed question (§15).

**Two valid fixes for an assumed-knowledge failure**:
1. **Inline teach**: rewrite the stem to define the term in-place ("the tax wedge — economists' name for the gap between what your boss pays and what you take home")
2. **Add a foundational question**: write a separate origin/biographical question that teaches the term. The bank-as-a-whole then provides the foundation, even though any given playthrough may or may not hit the foundational question first.

**Failures look like**:
- Stem says "Madoff's Ponzi scheme" without ever defining what a Ponzi scheme is, AND no other question in the bank teaches Charles Ponzi 1920
- Stem says "Cantillon effect" without ever introducing Richard Cantillon (18th-c banker who knew John Law), AND no biographical question exists
- Stem says "RLHF" or "fine-tuning" or "Mises calculation problem" at T4+ without those terms being defined anywhere
- Stem uses jargon ("the writ of habeas corpus", "the principal-agent problem", "the calculation problem") that has no foundational anchor

**Passes look like**:
- T2 or T3 foundational question explicitly teaches the term ("In 1920 Boston, Charles Ponzi promised 50% in 45 days...")
- T4+ questions reference the term confidently, building on that foundation
- Players who hit the T4 question without the T2/T3 first can still figure it out from inline context

**Especially load-bearing for**:
- Named historical figures referenced in deeper-tier questions (need T2/T3 biographical foundation)
- Specialized jargon from a particular tradition (Austrian econ, AI research, science philosophy, theology)
- Acronym-heavy domains (FICA, NCVIA, VAERS, ABCT, MMT, RLHF, GBD, CCW)
- Origin stories for namesake terms (Ponzi scheme, Bastiat's broken window, Pareto efficiency, Coase theorem, Cantillon effect, Volcker shock, Reagan revolution)

**Heuristic for catching this pattern in audit**:
- Build a list of jargon terms used in stems
- For each, check if it's introduced/explained somewhere in the bank
- Flag terms used in N questions but with no foundational question
- BUT: human reading is required — many "uses" of a term are inline-defined, and the heuristic over-flags

**Implementations**:
- **Economics (2026-05-26)**: Charles Ponzi origin missing → added T2 biographical question. Richard Cantillon biographical, Bastiat 1850 essay origin, John Law Mississippi Bubble 1719-20, Mises 1920 calculation foundation, Hayek 1945 knowledge foundation, Buchanan+Tullock 1962 founding, Bitcoin block / halving / tax-wedge foundations — 10 foundational adds
- **AI (2026-05-26)**: "agent" and "jailbreak" foundational adds + 2 stem rewrites for inline-teach
- **Science (2026-05-26)**: 5 stem rewrites to inline-teach Galileo 1633 / Semmelweis 1847 / Marshall 1984 / NCVIA spell-out / COVID-dissenter credentials at T1 (the random-shuffle entry-point problem)
- **All future subjects**: this principle generalizes. Pre-rebuild: build a glossary of subject-specific jargon; ensure every term has a foundational question OR is inline-defined wherever it appears
- **Cannot be deterministically gated** — requires reading judgment about which terms count as "should be taught" vs "common-knowledge defaults"

**Discovered explicitly**: 2026-05-26 user flag during economics Madoff/Ponzi review. The bank had been treating the player as an insider who already knew jargon. Real teaching requires either inline-define or foundational anchor.

See also: §14 (story-in-stem), §15 (no weasel closers), `_assumed_knowledge_*.json` audits per subject (worked examples).

### 17. Knowable answer — no unanswerables (number-recall AND unfalsifiable speculation)
**Principle (refined through the 2026-06-08 user audit of cooking + philosophy)**: A quiz answer must be KNOWABLE, learnable, or reason-able to ONE defensible position. Two failure modes both collapse to *"no one can really know,"* and both are banned:
- **(a) Obscure recall** — a specific number or obscure proper noun IS the answer ("how many crocus flowers make a pound of saffron?" → 150,000; "name the bacterium in this ferment" → *Leuconostoc*). Largely caught by the §6 anti-rote gate (count-the-things, name-the-creator) — but note the gate is stem-START anchored, so scene-led recall ("Saffron costs more than gold. How many crocuses…") slips it and needs review.
- **(b) Unfalsifiable speculation** — "does the (robot / computer / machine / animal / knight) REALLY feel / think / have consciousness / an inner life?" The honest answer is *"no one knows."* The user's words: *"useless because no one knows, and it's not interesting."*

**The carve-out (this is the whole subtlety)**: a real thought experiment that teaches a NAMED, decidable philosophical MOVE is GREAT, not banned — Frank Jackson's Mary's Room (→ "she learns something new, so physical facts don't capture experience"), Nozick's experience machine, Parfit's teleporter. Those have a DEFENSIBLE answer that names a real position you can argue for. "Is the chatbot really lonely?" has no such answer — it's a bull-session prompt, not a quiz question.

**The test**: *Is there a defensible answer naming a real fact or position — or is the honest answer "who knows"?* If the latter: cut, or reframe to the decidable move underneath.

**Implementations**: §17a largely caught by the anti-rote gate (+ a non-anchored advisory pattern added 2026-06-08 for scene-led recall). §17b is an **LLM-judge** call during generation/review (like §16) — regex can't tell Mary's Room from "is the AI sad," since both are scene-led and both use "feel." Cooking applied this 2026-06-08 (strain-naming + number-recall purge). Philosophy + Animal: apply during their next rebuild.
See also: §19 (the constructive fix — invert it), §6 anti-rote gate, `docs/quiz/subjects/cooking.md` §3.1.

### 18. On the subject's own core — no adjacent-policy / politics drift
**Principle (refined through the 2026-06-08 user audit of the animal bank)**: A wonder subject must teach ITS OWN substance, not an adjacent human-politics / policy / institutional layer. The ANIMAL bank is about ANIMALS — biology, behavior, senses, adaptation, life cycle, the wonder of the creature itself — NOT conservation legislation, agency history, treaties, or policy debates (the Lacey Act, CITES, the founding of a wildlife refuge, a DDT ban). Cooking is about how cooking works, not food-aid geopolitics.

**The test**: *Strip the human politics/policy — is a [subject] fact still being taught?* If the real content is a LAW, an AGENCY, a TREATY, or a POLICY DEBATE, it belongs in **history** or **economics**, not the wonder subject. The user: *"focus on the animals, not human politics around conservation policy."*

**Why this matters**: drift toward adjacent policy is seductive — it *feels* educational and important — but it hollows the subject: the kid stops learning about the eagle and starts memorizing the 1940 Bald Eagle Protection Act. Each subject has ONE job; the SUBJECT→ACTION mapping (animal→harvesting) means the animal bank should make the kid LOVE animals, not legislation.

**Allowed slice**: a little conservation is fine IF it stays on the animal's BIOLOGY — "the whooping crane's population bottleneck shrank its genetic diversity; why is that dangerous for a species?" is about the ANIMAL. "Which 1973 law protects it?" is policy → out.
**Implementations**: advisory keyword heuristic (legislation / agency / treaty / "Act of 19XX" / policy terms dominating an animal stem → flag for review; over-flags, human reads). Animal rebuild 2026-06-08 audit: ~88 conservation-policy questions (9%). All wonder subjects: keep adjacent-policy a small minority, always subject-first.

### 19. Invert the wonder — a cool fact is a STEM HOOK, never the answer
**Principle (refined through the 2026-06-08 user insight on the saffron question)**: A cool fact — a big surprising number, a superlative, a surprising origin — must NOT be the ANSWER (that's §17a, unanswerable recall). It belongs in the STEM as the HOOK, with a KNOWABLE thing (the origin, the part, the concept) as the answer. **Don't CUT a cool fact — INVERT it.**

**The user's canonical exemplar (saffron)**:
> ❌ "How many crocus flowers make a pound of saffron?" → *150,000* (nobody knows; recall)
> ✅ "It takes ~150,000 hand-picked flowers to make one pound of saffron, the world's costliest spice — each red thread a stigma plucked by hand. Which FLOWER is saffron harvested from?" → **"The crocus"** (tulip / marigold / lavender)

The number stays the hook; the answer is the origin the kid LEARNS and remembers. This is §13 (Wonder Pattern) + §14 (story-in-stem) applied to a fact that was being tested *backwards*. Other inversions: maple's ~40-gallons-of-sap→"boil it down," vanilla→orchid pod, chocolate→fermented-then-roasted cacao bean, katsuobushi→dried tuna.

**The fix template**: put the wonder in the stem; ask the knowable origin / part / concept; give 3 plausible peer distractors (other flowers, other trees). A fact is genuinely CUT only when it has no knowable hook to invert toward (pure lab jargon, proper-noun recall with no origin story).
**Implementations**: Cooking 2026-06-08 — 24 cool facts recovered by inversion (cooking.md §3.2). Before cutting ANY number-recall question, try inversion first.
See also: §13, §14, §17, cooking.md §3.2.

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
