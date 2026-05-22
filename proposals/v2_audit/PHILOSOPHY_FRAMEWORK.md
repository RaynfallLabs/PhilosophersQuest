# Philosophy Bank Framework (2026-05-20)

This is the rule set for what a good Philosopher's Quest philosophy question
looks like. Every generation pass against this bank must hit it. If the past
three rebuilds drifted, this document is why.

## Core principle

The bank teaches the **reasoning move**, not the **name of the person who
made it**. A 5th-10th grader should leave this bank with sharper thinking
about ethics, knowledge, fallacies, and meaning — not a list of attributable
quotes.

If a question can be answered by recognizing the philosopher's name on the
stem, it has failed. If a question forces the player to work through a
situation and identify what move survives scrutiny, it has succeeded.

## What this framework forbids

1. **"X said Y"** stems — "Plato argued...", "Kant wrote...", "Nagarjuna
   taught...". The name in the stem turns the question into trivia.
2. **Long, hedged answers** — "A commitment that reason cannot guarantee
   in advance — the believer steps past what argument can show" is a
   paragraph dressed as an answer. Choices must be short, parseable in
   under 5 seconds.
3. **All-distractors-look-plausible-and-take-forever** — if every choice
   is a long technical phrasing, the player isn't reasoning, they're
   eye-scanning for the longest one. Distractors must read fast.
4. **Definition recall** — "What does 'empiricism' mean?" is not philosophy.
   It's vocabulary.
5. **Doctrine fragments without scaffolding** — "Avicenna drew a line
   between essence and existence. What did the horse add?" The reader has
   no foothold; they're either trained on Avicenna or they're guessing.
6. **Multiple-legit-answers without a forcing constraint.** If three of
   the four choices are all legitimate moves a careful thinker would
   consider, the player has no way to pick the "right" one without trivia
   knowledge of which philosopher held which view. The stem MUST include a
   forcing constraint — a phrase, detail, or pre-stated condition in the
   scenario that only ONE option logically completes. Examples:
   - "If God is just..." forces a *justice* answer, not a virtue answer.
   - A scenario stating "motive, multiple witnesses, and contemporary
     record are all satisfied" forces a *prior-probability* answer.
   - A scenario showing "years lost to postponement" forces a *time-now*
     answer, not a wealth/gossip/duty answer.
   Without the forcing constraint, the question is name-recall in disguise.
7. **Doctrine jargon in choices** — *"synthetic a priori"*, *"analytic
   a posteriori"*, *"empirical a priori"*. If the player needs to know
   technical terminology to decode the choices, the question is
   nomenclature recall, not reasoning.

## Where philosopher names belong

**In the `context` field.** Always. The context is exactly the place to
say "Augustine wrestled with this same puzzle in *Confessions XI*" or
"this dilemma was sharpened by Foot in 1967." That builds cultural
literacy without making the quiz itself name-recall.

```json
{
  "tier": 3,
  "question": "A child asks where time goes when it 'passes.' If the past is gone and the future has not arrived, where does the time we measure actually exist?",
  "choices": [
    "In the mind — we hold past, present, and future together by attention.",
    "On a clock — time is just what clocks measure.",
    "In motion — time is the same as movement.",
    "Nowhere — time is an illusion that does not exist."
  ],
  "answer": "In the mind — we hold past, present, and future together by attention.",
  "context": "This puzzle is roughly the one Augustine raised in Confessions XI (~400 AD). The 'in the mind' answer is his — he relocated time from the world into the soul. The other answers are positions other thinkers held."
}
```

## The five tiers

Each tier raises the **conceptual** difficulty, not the reading level alone.
Length budgets are tight to force the writer to find the lever.

### T1 — 5th grade (10-11)

- **Scope**: lived situations the player has actually been in — friend
  lies to protect you; you find a wallet; teacher unfair; group pressure.
- **Reasoning move**: spot the simple fallacy or the obvious-once-named
  asymmetry.
- **Form**: scene-led, ≤120 char stem, ≤60 char answer, ≤80 char choices.
- **Voice**: a kid's voice. Concrete nouns. No -isms.
- **Names**: zero in stem. Optional in context.

**GOOD T1**:
> *Q*: A friend lies to protect Ben from getting in trouble. Ben feels bad
> about the lie even though it helped him. What is Ben noticing?
> *A*: Right and wrong don't always match what works out.
> *Ctx*: This is the difference between *consequence* and *rule* thinking.
> Philosophers have argued for thousands of years about which one matters more.

**BAD T1** (currently in bank):
> *Q*: A young Stoic complains 'my friend insulted me!' His Stoic teacher
> would say something like: 'is the insult IN you, or is it just in the
> air?' What does this teach?
> — too much setup, the Stoic name is doing the work, the answer is
> a paraphrase of the stem.

### T2 — 6th grade (11-12)

- **Scope**: simple dilemmas + named fallacies. Bandwagon, ad hominem,
  straw man, slippery slope, false dilemma — by name, with examples.
- **Reasoning move**: name the fallacy, or pick which response holds up.
- **Form**: ≤140 char stem, ≤80 char answer.
- **Voice**: still concrete; can have a story setup of 1-2 sentences.
- **Names**: zero in stem. Context can name a philosopher.

**GOOD T2**:
> *Q*: A politician says: 'Don't trust her tax plan — she dresses oddly.'
> What is wrong with that argument?
> *A*: It attacks the person, not the argument. (ad hominem)
> *Ctx*: Logicians since Aristotle have flagged this move...

**BAD T2** (currently in bank):
> *Q*: Voltaire is remembered for the line 'I disapprove of what you say,
> but I will defend to the death your right to say it.' What principle
> was that line meant to honor?
> — pure attribution recall.

### T3 — 7th grade (12-13)

- **Scope**: classic thought experiments simplified — ring of Gyges
  (would you be good if invisible?), trolley problem, ship of Theseus,
  Plato's cave.
- **Reasoning move**: hold two competing positions in mind, pick which
  one survives the strongest objection.
- **Form**: ≤160 char stem, ≤100 char answer.
- **Voice**: still scene/scenario; positions presented as actions, not
  doctrines.
- **Names**: zero in stem. Context names the thought-experiment author.

**GOOD T3**:
> *Q*: A man finds a ring that makes him invisible. He can take whatever
> he wants and no one will know. If he is GENUINELY a good person, what
> happens to his behavior?
> *A*: Nothing changes — being seen wasn't the reason he was good.
> *Ctx*: This is Plato's ring of Gyges (Republic II). The other answers
> are real positions: Glaucon argued ALL people would steal; Hobbes...

**BAD T3** (currently in bank):
> *Q*: Augustine asked in Confessions XI how we measure time when the past
> is gone, the future not yet, and the present a vanishing instant. Where
> did he locate it?
> *A*: In the mind — as memory of the past, attention to the present, and
> expectation of the future, held together at once.
> — 99 chars of answer reading like a paragraph. The kid is just looking
> for the longest option.

### T4 — 8th grade (13-14)

- **Scope**: harder dilemmas, implicit assumptions, basic epistemology
  (knowledge vs. true belief), free will, mind-body.
- **Reasoning move**: find the hidden premise; identify which framing of
  the problem dissolves it.
- **Form**: ≤180 char stem, ≤110 char answer.
- **Voice**: tighter, more demanding — but still scene-first.
- **Names**: still zero in stem. Context can name multiple thinkers.

**GOOD T4**:
> *Q*: You truly believe your friend will help you, and you are right —
> but only because you misread her face. She had decided to help for an
> unrelated reason. Did you KNOW she would help?
> *A*: No — true belief isn't knowledge unless your reasons track the truth.
> *Ctx*: This kind of case (Gettier, 1963) showed that "justified true
> belief" wasn't enough...

### T5 — 9-10th grade (14-16)

- **Scope**: serious thought experiments — Newcomb's problem, brain in
  a vat, original position, Mary's room. Free will and determinism head-on.
- **Reasoning move**: spot which philosophical move resists the strongest
  objection; identify the assumption that drives the disagreement.
- **Form**: ≤200 char stem, ≤120 char answer.
- **Voice**: can be more demanding; scene-led still.
- **Names**: zero in stem. Context can sketch the historical lineage.

## Topic taxonomy — 8 branches × 5 tiers + fallacy ladder

Eight branches, each represented across all five tiers. Plus a parallel
**fallacy ladder** that gets heavy treatment because the user has flagged
it as the single most important content for kid-level philosophy.

| Branch | T1 anchor | T2 anchor | T3 anchor | T4 anchor | T5 anchor |
|---|---|---|---|---|---|
| **Ethics** | what's fair? | rules vs. consequences | trolley / ring of Gyges | virtue vs. duty vs. outcomes | metaethics: where do morals come from? |
| **Epistemology** | how do you know X? | evidence vs. testimony | dream/skepticism | knowledge ≠ true belief (Gettier) | brain in a vat |
| **Logic / Fallacy** | bandwagon (basic) | named fallacies (5 main) | conditional reasoning | hidden premises | quantifier confusion / vagueness |
| **Metaphysics** | what makes you YOU? | change vs. sameness | ship of Theseus | personal identity | causation, possible worlds |
| **Philosophy of Mind** | thoughts vs. things | feelings vs. facts | mind/body | qualia / Mary's room | consciousness |
| **Political** | what's a fair rule? | majority vs. minority | rights | social contract | justice (Rawls vs. Nozick) |
| **Religion/Theology overlap** | wonder / awe | problem of evil (basic) | faith vs. reason | arguments for God | religious experience |
| **Aesthetics** | what makes art good? | taste vs. quality | beauty vs. truth | sublime / wonder | art and meaning |

### Fallacy ladder (parallel, weighted heavy)

User's stated priority. Currently the bank has 23 fallacy questions out of
1139 (2%). Target: **20% of the bank** is fallacy-recognition. ~230 questions.

Per tier:
- T1 fallacies (40 questions): bandwagon, "but they did it too" (tu quoque
  at kid level), name-calling (ad hominem at kid level), promise breaking
  as betrayal vs. as accident.
- T2 fallacies (50): named — ad hominem, straw man, false dilemma,
  slippery slope, appeal to popularity, hasty generalization. Each with a
  story stem.
- T3 fallacies (50): named + conditional reasoning. Affirming the
  consequent, denying the antecedent, post hoc, equivocation, red herring.
- T4 fallacies (45): hidden premises, begging the question, no true
  Scotsman, genetic fallacy, appeal to nature, appeal to authority done
  carefully (when does it work?).
- T5 fallacies (45): subtle — quantifier shift, scope ambiguity, motte and
  bailey, isolated demand for rigor, false equivalence, gish gallop.

## Hard length budgets

Tighter than current. The "p90 161 chars" answers at T4 are the disease.

| Tier | Stem ≤ | Choices each ≤ | Answer ≤ | Context ≤ |
|---|---:|---:|---:|---:|
| T1 | 120 | 60 | 60 | 200 |
| T2 | 140 | 80 | 80 | 240 |
| T3 | 160 | 100 | 100 | 280 |
| T4 | 180 | 110 | 110 | 320 |
| T5 | 200 | 120 | 120 | 360 |

These are MAXIMUMS, not targets. Median should sit at 60-70% of cap.

## Generation discipline (carry forward from rebuild memory)

1. **Double-assert** every question on creation: budget + parity + anti-rote
   + FK ≤ tier-cap + jargon ≤ tier-cap.
2. **Scene-led**, full sentences ending in `?`.
3. **No -isms** in T1-T2 stems. No "-ology" terms either ("epistemology",
   "phenomenology" — too far for grade 5-6).
4. **Save as you go** when generating large batches.
5. **Hand-author then validate** — don't validate-then-author.
6. **Distractors short** — every distractor under tier's cap. Length-parity
   gate enforces this.
7. **Steelman distractors** — wrong, but in a way smart people are wrong.
   A 10-year-old should be able to say "I see why someone might pick that
   one."

## Stance preserved (carry forward)

- Western tradition spine (Greek, Roman, Christian, Modern, American).
- Eastern covered seriously (Buddha, Confucius, Lao Tzu).
- Logical fallacies as the single heaviest sub-topic.
- Classical-liberal-traditionalist orientation on political philosophy.
- Identity-politics critics steelmanned (Sowell, Hayek, Burke, Scruton,
  Coleman Hughes, Aristotle).
- Real positions of postmodernism / critical theory included as
  *critique targets*, not as foundational truths.
- Christian-Crusader framework: theology overlap content respects
  the framework (single God, no pantheons in the THEOLOGY overlap rows).

## Substantive moral vision (learned from 2026-05-22 rebuild)

The following positions are SUBSTANTIVE views the bank teaches, not "interesting alternatives" to be neutrally balanced against opposing schools. The pedagogical method stays neutral (students follow chains of reasoning to recognize moves; no verdicts declared in answers). The CONTENT selection is not neutral — these are the questions worth asking.

### Care ethics: harsh treatment, not endorsement
- Care ethics is the feel-good default position humans naturally hold. The bank's job is to TEACH the LOGICAL CRITIQUES of it.
- 1-2 questions per tier define care ethics so students recognize the school. The remaining T2-T5 ethics questions on care SHOULD challenge it from real philosophical angles: enabling dependency, neglect of root causes, scaling failures, parochialism.
- The bank does NOT moralize at the player ("you should help your friend"). It teaches the student to RECOGNIZE the philosophical positions and their structural critiques.

### Parental and local partiality is JUST AND RIGHT
- Cottingham (Partiality and the Virtues, 1998) and Williams ("one thought too many") defend agent-relative obligations as morally grounded — not as bias to be corrected.
- Singer's drowning-child impartialism is the abstract demand being CHALLENGED, not the default to defend.
- Parents preferring their own children, communities preferring their own members, citizens preferring their countrymen — all morally grounded under this view.
- Frame impartialism as the implausibly abstract foil; partiality as the substantive position.

### Men and women ARE different
- Christina Hoff Sommers (Who Stole Feminism?, 1994) distinguishes EQUITY feminism (fair treatment of individuals on their merits; acknowledges real differences between the sexes) from GENDER feminism (insists men and women are interchangeable, frames any difference as oppression).
- The bank teaches equity feminism as the substantive view. Gender feminism appears as a position to be scrutinized.
- Celebrating difference between the sexes does NOT diminish individuals. The bank does not pretend men and women are interchangeable.

### Hayekian-style critique as substantive
- When the bank treats welfare-as-scaled-care, central-planning critiques, or social-justice rhetoric, the Hayekian view (The Use of Knowledge in Society, 1945; The Mirage of Social Justice, 1976) is the substantive winner of the structural argument. Adjacent traditions (Bastiat, Friedman, Sowell, Buchanan, Olson, Stigler, Mises) work in the same tradition.
- The bank teaches students to RECOGNIZE the reasoning moves these thinkers use — Bastiat's seen-vs-unseen, Hayek's knowledge problem, public-choice incentive analysis, moral hazard, regulatory capture, Sowell's "compared to what?", Friedman's "judge by results not intentions" — without declaring policies "wrong" or schools "correct."

### Surface-good critique frame (pedagogical method)
- Many modern policy proposals sound good on the surface but produce predictable harms. The bank teaches students to LOOK FOR these patterns, not to memorize verdicts.
- Question shape: advocate proposes feel-good policy → critic articulates a specific reasoning move → student identifies which reasoning move the critic is making.
- Choices are competing REASONING MOVES (with inline definitions), not school names alone.
- Whether the student accepts the critic's conclusion is left open. They have learned to SEE the move.

### Coercion-beneath-consent frame (pedagogical method)
- Modern political language softens coercion ("asking the wealthy to pay their fair share", "society decides", "we the people"). The bank teaches students to RECOGNIZE the gap between rhetoric and mechanism — without declaring "taxation is theft" or any verdict.
- Question shape: speaker uses softening language → critic identifies a specific distinction the language obscures → student identifies which distinction.
- Distinctions taught: voluntary vs compelled, specific actors vs abstract collective, consent vs majority decision (Mill, Tocqueville), just law vs legal plunder (Bastiat), conditional vs unconditional cooperation, procedural vs substantive justice, public choice vs benevolent planner.

## Wonder bias — scenario aesthetics

When choosing scenarios, prefer GRAND / WONDROUS / CANONICAL framings over mundane modern ones. Logic stays the same; scenery upgrades. The wonder framing serves two purposes: (a) the Christian-Crusader game setting feels coherent, (b) kids encountering canonical scenarios later in life recognize them.

**Prefer:**
- Knights, squires, paladins, generals, captains
- Battles, sieges, single combat, tournaments, training yards
- Creatures: dragons, gryphons, basilisks, manticores, wyverns
- Mysteries: alchemical labs, oracles, prophecies, hidden ruins, ancient texts
- Mythology: Greek, Norse, Arthurian, biblical heroes
- Fortresses, citadels, monasteries, scriptoriums, refectories, great libraries
- Bards, scribes, messengers, heralds, merchants of the realm
- Named canonical thought experiments: Ship of Theseus, Mary's Room, Chinese Room, Brain in a Vat, Trolley Problem, Ring of Gyges, Newcomb's Paradox, Buridan's Ass, Sorites Paradox, Statue and the Lump, Black's Spheres, Experience Machine

**Avoid:**
- "Theo's bike", "Maya's group chat", "Pop star endorses energy drink", "Sleepover snack", "Bake sale rules", "Pizza place", "Soccer practice", "School newspaper" — these scenarios diminish the philosophical weight of the question and don't anchor students to a tradition.
- Exception: T1 lived-situation framings (family dinner rules, classroom rules) are acceptable when the philosophical content genuinely belongs in lived experience (e.g., basic political-authority questions).

## How to use this framework

Future bank rebuilds: read this document FIRST. Read PHILOSOPHY_TEMPLATES.md SECOND for the concrete patterns. Generators instantiate templates that conform to this framework.

If a generation pass produces content that violates the substantive moral vision above (e.g., presents care ethics under no critical pressure, or treats Hayek as merely "an interesting alternative", or frames sex differences as inherently oppressive), the pass is wrong on the framework — not just on the templates.

## The implementation pattern

Every batch of new questions goes through this pipeline:

```python
def q(tier, stem, choices, answer, context):
    # Cap checks
    cap = TIER_CAPS[tier]
    assert len(stem) <= cap['stem'], f"stem over: {len(stem)}"
    assert len(answer) <= cap['answer'], f"answer over: {len(answer)}"
    for c in choices:
        assert len(c) <= cap['choice'], f"choice over: {len(c)}"
    # FK + jargon
    assert fk(stem) <= cap['fk'], f"FK {fk(stem)} > {cap['fk']}"
    assert jargon(stem) < cap['jargon']
    # No name in stem
    assert not any(name in stem for name in BANNED_NAMES), f"name in stem: {stem}"
    # Length parity — no answer >1.6x longest distractor
    longest_d = max(len(d) for d in choices if d != answer)
    assert len(answer) <= 1.6 * longest_d, "answer too long vs distractors"
    return {tier, question, choices, answer, context}
```

The BANNED_NAMES list is the philosopher canon. About 80 names. If any
appears in the stem, the question is rejected at write time, not at
validate time.
