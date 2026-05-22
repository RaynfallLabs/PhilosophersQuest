# Philosophy Bank Question Templates (Source of Truth)

This document is the **recipe** that every philosophy question is built from.
`PHILOSOPHY_FRAMEWORK.md` is the philosophy (the "why"); this document is the
mechanics (the "how"). If a generated question doesn't match a pattern here,
it isn't shipped.

The chain of authority:
1. The user's stance (in conversation + memory entries) — highest authority.
2. `PHILOSOPHY_FRAMEWORK.md` — long-form principles.
3. **`PHILOSOPHY_TEMPLATES.md` (this doc)** — concrete patterns generators must conform to.
4. Generator scripts.

Generators do not invent patterns. They instantiate patterns from this doc.

---

## 1. Core principles (restate, do not relitigate)

- The bank teaches the **reasoning move**, not the **name of the person who made it**.
- Names of philosophers belong in the **context field** for additional knowledge; they can be characters or noted in the stem, but not as framing or context.
- Choices must be **parallel in shape** — if one starts with a fallacy name + dash,
  all four do; if one is a "Yes/No — reason" form, all four are.
- The stem must contain a **forcing constraint** that rules out 3 of the 4
  choices. Without it the question is name-recall in disguise.
- **No verdict on contested questions**: for genuinely contested metaphysical/ethical/identity questions (persistence-through-change, personal identity, free will, mind-body, taste/beauty), the stem must NOT ask "Is X really the same?" with one "yes — reason" presented as canonically correct. Instead, attribute the claim to a character with stated reasoning ("Your sister says you ARE that kid — you remember being him") and make all four choices competing schools (Memory continuity / Bodily continuity / Soul theory / No-self view). The correct answer is the school whose reasoning matches the character. This applies to genuinely contested questions only — Gettier-style accidental-truth and clear logical fallacies have settled answers and verdict-style is fine.
- The bank's content scope is **Logic / Reasoning / Debate / Philosophy**.
  The subject identifier stays `philosophy` for code stability.

## 2. The 8 topics

| Topic | What it teaches |
|---|---|
| **Logic/Fallacy** | Spot the reasoning move; name the flaw. THE HEAVIEST sub-topic — target 25% of bank. |
| **Ethics** | Moral reasoning, virtue vs. rule vs. consequence, real dilemmas. |
| **Epistemology** | How do we know? Knowledge vs. true belief, skepticism, testimony. |
| **Metaphysics/Identity** | What is real? What makes something the SAME over time? |
| **Philosophy of Mind** | Mind/body, consciousness, the puzzle of subjective experience. |
| **Political philosophy** | Authority, rights, justice, consent, the social contract. |
| **Religion/Theology overlap** | Faith and reason, the problem of evil, religious experience. |
| **Aesthetics** | Beauty, taste, art, the sublime. |

## 3. The 5 tiers — register progression

The user emphasized: lower tiers must NOT be kiddy. The student reads adult
books but doesn't know the philosophical jargon. **Learning the concept is
the focus of the question** — terms can be USED, but each used-term must be
either defined inline OR be derivable from context; teaching the meaning of these terms can be legitimate questions in the lower tiers.

### Tier register markers

| Tier | Reading age | Voice | Scene material |
|---|---|---|---|
| **T1** | 10-11 (5th gr) | Concrete, no philosophy jargon in stem. Choices can introduce terms with inline definitions or definition as the question. | Lived situations: family, school, friend group, sports, online basics. |
| **T2** | 11-12 (6th gr) | Slightly more abstract; named fallacies appear in choices with brief definitions. | Pre-teen world: group chats, class debates, sibling fairness, bake sales. |
| **T3** | 12-13 (7th gr) | Vocabulary expands; can use *premise*, *argument*, *evidence*, *principle*. | Online creators, school newspaper, debate club, brand claims, peer-review. |
| **T4** | 13-14 (8th gr) | Mature analytical; *framing*, *structural*, *epistemic*. Concepts named, definitions still given. | Op-ed columnists, podcast hosts, statistical claims, public-figure rhetoric. |
| **T5** | 14-16 (9-10th gr) | Analyst-grade; can use *rhetorical maneuver*, *dialectical*, *physicalism*, *response-dependent*. Specialist terms still get parenthetical definitions on first appearance. | Forecaster transcripts, self-help guru contradictions, expert disagreements, journalistic framing. |

### Vocabulary policy (the learning-is-focus rule)

A term like `virtue ethics` can appear at T1 IF the choice that names it
defines it inline: *"Virtue ethics — character is what you do when no one is
watching."* The student learns the term by reading the choices.

A term like `physicalism` is fine at T5 with parenthetical: *"...challenges
physicalism (the view that everything mental is fully captured by physical
facts)..."*

A term like `quiddity` or `haecceity` does NOT appear in choices at any tier.
Specialist scholastic jargon → context field only, or drop.

## 4. Stem patterns by topic

Each topic has 3-5 approved stem patterns. Generators must use one of these
patterns; ad-hoc phrasings are not allowed.

### 4.1 Logic / Fallacy stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Subject-commits** | T1-T5 | *"[Subject]'s [reply/response/argument] commits which logical fallacy?"* |
| **B. Argument-relies-on** | T2-T5 | *"This argument relies on which logical fallacy?"* |
| **C. Framing-commits** | T3-T5 | *"The op-ed's framing commits which logical fallacy?"* |
| **D. Identify-flaw** | T3-T5 | *"Identify the reasoning flaw in [Subject]'s [response]."* |
| **E. Diagnose-maneuver** | T5 only | *"Diagnose the rhetorical maneuver."* / *"Identify the rhetorical move."* |
| **F. Even-if-correct** | T4-T5 | *"Even if [Subject]'s conclusion happens to be correct, what fallacy does the ARGUMENT commit?"* (teaches the form-vs-conclusion distinction) |

**Subject construction**: at T1-T2, use kid scene characters (Maya, Ben, the boy, Mom). At T3-T5, use scene roles (the YouTuber, the columnist, the forecaster, the coach).

**Banned**:
- *"What's wrong?"* (kindergarten)
- *"What's missed?"* (vague)
- *"Where's the slip?"* (informal)
- *"What did X avoid?"* (implies hiding, not committing)
- *"What's the trick?"* (game-show register)
- *"What is the flaw?"* alone without naming the subject

### 4.2 Ethics stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Position-defended** | T2-T5 | *"Which view of ethics is [the teacher / Sam / the speaker] defending?"* |
| **B. Best-response-holds** | T3-T5 | *"Which response to this dilemma holds together under scrutiny?"* |
| **C. Principle-priority** | T4-T5 | *"When [duty] and [consequence] conflict in this case, which principle takes priority?"* |
| **D. Why-not-defense** | T1-T3 | *"Why is '[bad reasoning]' NOT a good defense in ethics?"* |
| **E. What-makes-X-right** | T3-T5 | *"What makes [the choice] right or wrong, on the [stoic/Kantian/utilitarian] reading?"* (named view + inline definition) |

Each ethics question must distinguish the **scenario** from the **ethical view being tested**. A scenario can be analyzed under multiple views; the question tells the student which lens to use.

### 4.3 Epistemology stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Did-X-know** | T2-T5 | *"Did [Person] actually KNOW [the fact]?"* (Gettier shape) |
| **B. What-survives-doubt** | T4-T5 | *"What, if anything, would still be certain after [radical skeptical move]?"* |
| **C. Strongest-reason-to-doubt** | T3-T5 | *"What's STILL the strongest reason to doubt [the testimony]?"* (use forcing-constraint shape) |
| **D. Conception-challenged** | T5 | *"Which conception of knowledge does this case challenge?"* |
| **E. Which-question-to-ask** | T1-T3 | *"What's the most careful question to ask before believing?"* |

### 4.4 Metaphysics/Identity stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Puzzle-exposes-tension** | T4-T5 | *"The puzzle exposes a tension between two competing principles of identity."* |
| **B. Which-view-captures** | T3-T5 | *"Which view best captures what makes [X] the same over time?"* |
| **C. What-makes-X-X** | T1-T3 | *"What makes you the same person you were five years ago?"* |
| **D. If-A-and-B-which** | T3-T5 | *"If [ship A] and [ship B] both have a claim to being the original, which feature settles identity?"* |

### 4.5 Philosophy of mind stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Thought-experiment-asks** | T4-T5 | *"The thought experiment asks: did [Mary] LEARN something genuinely new?"* |
| **B. What-does-X-expose** | T5 | *"What does the [zombie / inverted spectrum / Chinese room] case expose?"* |
| **C. What-makes-X-conscious** | T3-T5 | *"What does it take for a system to be genuinely conscious, on this view?"* |
| **D. Could-X-have-felt** | T2-T4 | *"Could the robot have felt the same thing the kid felt? Why or why not?"* |

### 4.6 Political philosophy stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Which-view-is-stricter** | T4-T5 | *"Which view holds individual autonomy as the stricter standard?"* |
| **B. Where-do-rights-come-from** | T3-T5 | *"On this view, where do rights come from?"* |
| **C. What-justifies-X** | T3-T5 | *"What, on this argument, would justify the state's use of force?"* |
| **D. Why-is-X-not-the-same** | T2-T4 | *"Why is 'majority approved' not the same as 'justly decided'?"* |
| **E. Surface-good-critique** | T3-T5 | *"An advocate proposes [feel-good policy]. A critic argues [specific reasoning]. Which reasoning move is the critic making?"* — choices are competing reasoning moves (Bastiat seen-vs-unseen, Hayek knowledge problem, public choice, moral hazard, Sowell compared-to-what, regulatory capture, etc.). Student identifies the move. **DO NOT close with "the policy is bad" or "the critic is correct" — close with the move name.** |
| **F. Coercion-beneath-consent** | T3-T5 | *"A speaker uses softening language: '[example].' A critic notes the language obscures a distinction. Which distinction is the critic drawing?"* — choices are competing distinctions (voluntary/compelled, specific/abstract, consent/majority, conditional/unconditional, etc.). Student identifies the distinction. **DO NOT close with "taxation is theft" or any verdict — close with the distinction name.** |

### 4.7 Religion/Theology overlap stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Which-response-engages** | T3-T5 | *"Which response actually engages the problem the skeptic raises?"* |
| **B. What-does-X-argument-claim** | T4-T5 | *"What does the [cosmological / moral / design] argument claim, at its sharpest?"* |
| **C. How-does-X-handle-Y** | T4-T5 | *"How does the free-will defense handle the suffering of children?"* |
| **D. Why-is-X-not-enough** | T3-T5 | *"Why is 'I sincerely believe it' not enough, on this account, to make X true?"* |

### 4.8 Aesthetics stems

| Pattern | Tier range | Example |
|---|---|---|
| **A. Which-view-handles-X** | T4-T5 | *"Which view best handles the observed agreement WITHOUT [collapsing into objectivism]?"* |
| **B. Is-X-art** | T3-T5 | *"On this view, is [the case] genuinely art?"* |
| **C. What-makes-X-beautiful** | T2-T4 | *"What, on this view, makes the [object] beautiful — a property of it, or a response in us?"* |

## 5. Choice structures by question type

The defining rule: **all four choices have the same shape**. If choice 1 leads with a concept name, all four do. If choice 1 is a "Yes/No — reason," all four are.

### 5.1 Fallacy questions (the most rigorous structure)

Every choice is **"[Fallacy Name] — [definition]"**.

- **Correct answer**: `[Correct Fallacy Name] — [scenario-tied explanation: why it fits HERE].`
- **Three distractors**: `[Different Fallacy Name] — [generic definition of that fallacy].`

The student MATCHES the scenario to the right fallacy by reading what each fallacy IS.

**Distractor selection rule**: distractors should be **pedagogically close** to the correct fallacy when possible. For example, distractors for an ad hominem question should include genetic fallacy and tu quoque (both source-related), not motte-and-bailey (totally different category).

### 5.2 Ethics questions

Every choice is **"[Ethical position name] — [the claim that view makes about THIS scenario]"**.

- **Correct**: `[Position] — [why it supports the right action in this scene].`
- **Distractors**: `[Other Position] — [what that other view would say about this scene — accurately].`

This means the student learns multiple ethical positions per question. Distractors are NOT strawmen of competing positions — they're accurate.

### 5.3 Epistemology (Gettier-style)

**"Yes / No — [reason]"** structure.

- **Correct**: `No — true belief isn't knowledge unless reasons track the truth.`
- **Distractors**: `Yes — [different criterion of knowledge]`, `No — [different but wrong criterion]`, etc.

### 5.4 Metaphysics / identity

**"[Principle A] vs. [Principle B] — [why this case forces a choice]"** structure.

- **Correct**: identifies the genuine tension the puzzle exposes.
- **Distractors**: other plausible tensions that DON'T quite fit (e.g., "the puzzle dissolves once you define X" — tempting but wrong).

### 5.5 Philosophy of mind

**"Yes / No — [what the case is supposed to expose]"** structure.

- **Correct**: identifies what the thought experiment is designed to show, including the philosophical position it challenges.
- **Distractors**: alternative interpretations (the case is malformed; the case shows the opposite; the case is incomplete).

### 5.6 Political / Religion / Aesthetics

**"[Position name + brief stance] — [reason]"** structure (parallel to ethics).

## 6. Length envelopes

Looser than the previous framework's caps — generous enough to define concepts inline at lower tiers, capped to prevent paragraph-style answers.

| Tier | Stem ≤ | Each choice ≤ | Context ≤ |
|---|---:|---:|---:|
| T1 | 220 | 110 | 250 |
| T2 | 250 | 130 | 290 |
| T3 | 290 | 160 | 340 |
| T4 | 340 | 190 | 400 |
| T5 | 400 | 230 | 480 |

**Length-parity rule still applies**: longest/shortest choice ratio ≤ 1.30, max deviation ≤ 15%.

## 7. Anti-patterns (banned)

### 7.1 Stem anti-patterns

- *"What's wrong?"* / *"What is wrong?"* — kindergarten register
- *"What's missed?"* / *"What is missed?"* — vague
- *"Where's the slip?"* / *"What slips by?"* — informal
- *"What did [X] avoid?"* — implies hiding, not committing
- *"What's the trick?"* — game-show register
- *"What is the flaw?"* alone (without naming the subject of analysis)
- *"Just spot it."* / *"Which one is it?"* — register too thin
- *"What is the problem?"* — kindergarten
- *"Is X really the same?"* / *"Are you the same person?"* / *"Is it still the SAME river?"* on contested metaphysical questions — imposes a verdict where serious philosophers disagree. Reframe: assign the position to a character and ask which school defends them.

### 7.2 Choice anti-patterns

- **Only correct answer has the name prefix** (the bug from earlier today)
- **Distractors are obviously wrong** (e.g., "The teacher is just dumb")
- **One choice is conspicuously longer** than the rest
- **Distractors contain content not introduced in the stem** (irrelevant invention)
- **Distractor lengths use awkward padding** ("in every case that comes up")

### 7.3 Context anti-patterns

- Naming a philosopher with no source/date (just "Plato said this")
- Context shorter than 80 chars at T3+ (context should teach, not summarize)
- Context that just repeats the answer
- **Authoring metadata leaks**: context is player-facing — never include template section references (§4.5-D), pattern names ("Could-X-have-felt", "Position-defended", "Even-if-correct", etc.), or tier labels used to refer to the cell ("at T2"). Caught by `context_no_meta_references` gate.

## 8. Structural gates (every question must pass)

Two layers: deterministic gates (fast, Python, no LLM cost) and judgment gates (LLM-as-judge calls; per [[feedback-no-api-spend]] all calls use Opus explicitly).

### 8.1 Deterministic + heuristic gates

Beyond the existing 5 deterministic gates (schema / length_budget / length_parity / anti_rote / duplicate):

| Gate | Check |
|---|---|
| **choice_shape_parity** | All four choices match the template's shape. For fallacy questions: all four start with `[Name] — `. For ethics: all four start with `[Position] — `. Etc. |
| **register_consistency** | Stem vocabulary tier ≈ choice vocabulary tier. (Heuristic: no choice uses a specialist term at a tier the stem stayed simple.) |
| **forcing_constraint** | Stem must contain a scenario detail (named character, specific situation, distinct setting). Heuristic: minimum stem length OR presence of scene-specific tokens. |
| **stem_pattern_match** | Stem matches one of the approved patterns in section 4 for this topic + tier. |
| **anti_pattern_clear** | Stem does not contain any phrase from section 7.1. |
| **no_verdict_on_contested** | For metaphysics/identity/free-will/mind-body/aesthetics topics, the stem must NOT be a yes-or-no question that the bank then adjudicates. Either (a) attribute the claim to a character and ask which school defends it, or (b) only ship as verdict-style if the question is in the carve-out (clear logical fallacies, Gettier-style accidental-truth, etc.). Heuristic: if a competent philosopher with the opposite view would be marked WRONG by the answer key, the question fails this gate. |
| **scenario_anchored_correct** | The correct answer references scenario-specific tokens from the stem (named character, scenario keyword). Distractors should be more generic. Without this, the question is name-recall in disguise. **Applies to fallacy questions only** (templates §5.1); position-defended questions are excluded. |
| **context_no_meta_references** | Context is player-facing and must not contain authoring metadata: no template section refs (§4.5, §5.1), no pattern names in quotes ("Could-X-have-felt", "Position-defended", "Even-if-correct", etc.), no tier labels used as authoring labels ("at T2", "pattern at T3"). |

(Note: an earlier draft listed `answer_position_bias` as a bank-level gate. Dropped — `src/quiz_engine.py:280-285` shuffles choice order at presentation time, so bank-level positional patterns are invisible to the player.)

### 8.2 Judgment gates (LLM-as-judge, Opus subagent)

Each is a single Opus call per question, one-time at gate-clearance time:

| Gate | Check |
|---|---|
| **distractor_coherence** | Each distractor's text matches the concept it's labeled as (so "Ad hominem — attacks the person" not "Ad hominem — but the violin player is obsessed"). |
| **distractor_plausibility** | Each distractor must be a defensible position a real philosophical tradition or competent person could hold — not a strawman ("Picking a winner before the game starts to save time"). |
| **single_defensible_answer** | Under the scenario's stated reasoning, only one choice should remain defensible. Test by asking the judge to defend each choice in turn; gate fails if >1 can be defended. |
| **inline_teaching** | The question must be answerable by a smart reader who has *never* encountered the specific names or terms. Definitions, context, or the scenario itself must do the teaching. **Failures look like:** undefined specialist terms used as the thing being tested ("What did Stoics mean by apatheia?" with no inline definition); named historical figures used as required prior knowledge ("Douglass broke with Garrison over..." with no inline introduction); moral-verdict questions that assume the player already shares the implied moral framework ("Should you do it?" with no exploration of competing ethical reasoning). **Passes look like:** every named position carries an inline definition ("Memory continuity — you're the same person if an unbroken chain of memory connects past and present selves"); philosophers' names appear in *context*, not as authority in the stem; every scenario teaches the concept before testing it. |

## 8.3 Wonder-bias rule (scenario aesthetics)

Prefer grand / canonical / mythological framings over mundane modern ones when the underlying logic permits. The Christian-Crusader game setting aligns naturally with this aesthetic.

**Preferred scenery vocabulary:**
- Knights, squires, paladins, generals, captains, heralds, scribes, monks, alchemists, bards, messengers
- Battles, sieges, single combat, tournaments, training yards, refectories, scriptoriums, citadels, monasteries, great halls, ancient ruins, oracles, prophecies
- Creatures: dragons, gryphons, basilisks, manticores, wyverns
- Named canonical thought experiments (Ship of Theseus, Mary's Room, Chinese Room, Brain in a Vat, Ring of Gyges, Trolley Problem, Newcomb's Paradox, Buridan's Ass, Sorites Paradox, Statue and Lump, Black's Spheres, Experience Machine)

**Disprefer:** "Theo's bike", "school newspaper", "group chat", "bake sale", "sleepover", "pop star endorsement", "soccer practice", "pizza place", "TikTok" — these reduce the philosophical weight and don't anchor to a tradition.

**Exception:** T1 lived-situation framings (family dinner rules, classroom fairness) are acceptable when the philosophical content genuinely belongs in lived experience.

## 9. Example bank (the "good looks like this" reference)

The repo carries a small "exemplar" set: ~5 fully-developed questions per topic at each tier. Generators consult these when picking phrasings. New samples must be visually consistent with the exemplars at their tier.

(Exemplars to be authored in Phase 2.)

## 10. Workflow rule (the gate that catches my failure pattern)

**Sample-before-scale**: every bulk-generation batch ≤ 50 questions stops here:

1. Generate 50 (or whatever the batch size is).
2. Pass them through the 5 deterministic gates + the 6 structural gates in section 8.
3. Show the user 5 random samples.
4. User: yes / no / "fix this specific thing."
5. If yes → commit, move to next batch.
6. If no → fix and re-sample.

**No batch is merged without user yes-on-samples.** This is the gate that catches my historical failure pattern (mutating bank then discovering bugs only at playtest).

## 11. What this document does NOT do

- Doesn't promise subjective elegance — that's still human judgment.
- Doesn't replace the framework doc — it's the mechanics layer on top.
- Doesn't enforce voice nuance at T5 perfectly — register gate is heuristic; final voice judgment is human.

What it DOES promise: structural failures (skim-tells, kindergarten stems, register mismatches, anti-pattern phrasings) become catchable BEFORE the bank touches user-visible play.
