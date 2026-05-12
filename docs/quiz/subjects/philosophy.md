---
version: 1
date: 2026-05-10
subject: philosophy
in_game_action: identification (per CLAUDE.md subject→action mapping)
style_verdict: WONDER-DRIVEN
---

# Subject: Philosophy

Philosophy is the flagship wonder subject. Questions here are the calibration set for the rest of the bank. If the philosophy questions feel boring, the project has failed; if they feel like discovery, the rest follows.

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('philosophy', (26, 1.2))` in `src/player.py` |
| Total timer at WIS 10 | **38s** |
| Total timer at WIS 25 (late-game) | **56s** |
| Typical chain cap | **5** (escalator_chain mode for identification) |
| Per-question budget at WIS 10, chain-5 | **7.6s** |
| Per-question parse budget (60% of above) | **4.6s** |
| Readable words at 240 wpm | **~18 words** |

**Implication:** question + 4 choices together should be readable in ~4 seconds. Total record cost (question + all four choices) should stay under ~600 chars at T1–T3 and under ~800 chars at T4–T5.

## 2. Per-tier character budgets (the operative gameplay gate)

The pipeline's pilot calibration confirmed that the binding gameplay constraint is **total record character count**, not a strict parse-time formula. Reason: real players scan four-choice questions at ~400 wpm (not the 240 wpm cold-read assumption) and skim-recognize repeats from deck rotation. The strict "words / 4 wps" formula rejects every spec-exemplar question, including the Foucault Panopticon and Russell+Whitehead/Gödel models in §4 — so we trust the char cap as the operative gate and treat parse-time as informational.

| Tier | Expected WIS | Total timer @ that WIS | Per-Q budget @ chain-5 | **Max record chars (gate)** | Density flag if over |
|---|---|---|---|---|---|
| 1 | 10–12 | 55–58s | 11–12s | **≤ 600** | 110 words |
| 2 | 12–15 | 58–63s | 12–13s | **≤ 700** | 130 words |
| 3 | 15–18 | 63–67s | 13–13s | **≤ 750** | 140 words |
| 4 | 18–22 | 67–73s | 13–15s | **≤ 950** | 175 words |
| 5 | 22+ | 73s+ | 15s+ | **≤ 1000** | 185 words |

**Timer bumped 2026-05-11**: `SUBJECT_TIMER['philosophy']` changed from `(26, 1.2)` to `(40, 1.5)` for learning-focused gameplay. Char caps raised in parallel so writers can scaffold unfamiliar concepts inline rather than compress them out. **Scaffolding > compression** is the new priority — see moral_vision.md §6.

**Hard rejection rule for the gameplay validator:** any record exceeding its tier's char cap by more than +5% is rejected regardless of content quality. Records at or near the cap that are also flagged for ambiguity get sent to repair.

*Notes on the timing model:*
- The timer is continuous across a chain, so the player can spend more time on harder questions and less on easier ones — average must hold, not every-question parse time.
- Deck rotation means questions repeat. Players who have seen a question 2–3 times can scan-recognize it in 1–2 seconds even at maximum length. Chain mode rewards mastery, not first-encounter speed.
- If after running multiple cells we find the char caps are too generous OR too tight, we can bump them. Don't bump the in-game `SUBJECT_TIMER` first — it requires player-facing rebalancing.

## 3. Per-tier content profile

| Tier | Conceptual demand | Voice | Assumed knowledge |
|---|---|---|---|
| 1 | Famous moves and famous people, framed by image or story. The player meets philosophy. | Scene-led, low jargon. The wonder hook does the work. | None. Names like "Socrates" and "Plato" are recognized but not assumed-known. |
| 2 | Famous *ideas* — what they actually claim, with image-bearing framing. | Story-led with a clear "huh" payoff. Surprise reversals welcome. | Vague familiarity with major Greek philosophers. |
| 3 | Less-famous moves by famous thinkers, or famous moves by lesser-known thinkers. Cross-tradition comparisons. | Drier than T2 only where the content demands. Image hooks still strong. | T1–T2 content presumed familiar. |
| 4 | Technical moves, but conveyed through their consequences. Mid-20th-century analytic + continental. Eastern + Islamic mid-difficulty. | Allowed to lean on technical terms with plain-language gloss. | Recognizes "phenomenology," "utilitarianism" as words. |
| 5 | Hard problems and disputes between sophisticated positions. *Why* a question is hard. Real disagreements among living philosophers. | Allowed dense, but never bloated. The Foucault/Panopticon level: tier-5 idea, no tier-5 jargon. | Comfortable with the names of contemporary subfields. |

## 4. North-star exemplars

Three per tier. Generators few-shot from these.

### Tier 1 — accessible, image-led

```
Q: Socrates never lectured or wrote textbooks. Instead, he would approach
   strangers in the market and ask them questions until they contradicted
   themselves. What was he trying to prove?
A: That most people do not actually understand the things they claim to know.
```
Why it's tier 1: the scene does all the conceptual work; "wisdom = recognizing your ignorance" lands without any jargon.

```
Q: Heraclitus said "you cannot step in the same river twice." What
   philosophical claim does this illustrate?
A: That reality is in constant flux — nothing stays exactly the same.
```
Why it's tier 1: famous quote, famous philosopher, but the player has to interpret the metaphor rather than recognize a name.

```
Q: Diogenes the Cynic lived in a wine jar in the Athenian marketplace,
   begged for food, and once told Alexander the Great to step out of his
   sunlight. What was the point of his bizarre lifestyle?
A: To show that almost everything people chase is unnecessary — virtue
   alone is enough.
```
Why it's tier 1: vivid scene, real history, payoff is a real philosophical position the player walks away owning.

### Tier 2 — famous ideas, with surprise

```
Q: Epicurus taught that the goal of life is pleasure — but his idea of the
   highest pleasure surprises most people. What did he say a person most
   needs to be happy?
A: Freedom from fear and pain, and the company of close friends — not
   excitement, wealth, or fame.
```
Why it's tier 2: "you probably think X, but actually Y" mechanic in pure form. Excellent length parity.

```
Q: Berkeley argued that a tree you are not looking at does not actually
   exist at that moment. What was his philosophical argument for this
   strange claim?
A: Without a mind perceiving it, there is nothing left — "material
   substance" is just a name for a bundle of perceptions with no
   perceiver behind them.
```
Why it's tier 2: question itself sounds insane on first read (= hook), distractors can be coherent rival epistemologies.

```
Q: The Buddha identified one root cause of all suffering. It is not pain,
   poverty, or illness. What is it?
A: Craving and attachment — clinging to pleasant things and resisting
   unpleasant ones, when all things are impermanent.
```
Why it's tier 2: preemptive "not the obvious answer" clause forces the player to think; tone is respectful, not exoticizing.

```
Q: Frédéric Bastiat in 1850 told a story about a shopkeeper whose window
   is broken by a careless boy. The neighbors say it's good news —
   breaking windows gives the glazier work. Bastiat said this argument
   misses something crucial. What did he say we should also count?
A: What the shopkeeper would have spent the money on instead — the shoes
   never bought, the book never published, the meal never eaten. The
   seen versus the unseen.
```
Why it's tier 2: famous parable with a built-in surprise reversal; vivid concrete handle; introduces opportunity cost as a moral concept without jargon.

```
Q: When someone says "you can't trust Hayek's economics because he was a
   wealthy Austrian aristocrat," they have committed a specific logical
   fallacy that attacks the arguer rather than the argument. What is it
   called?
A: Ad hominem — attacking the person making an argument instead of the
   argument itself. The argument's truth does not depend on who made it.
```
Why it's tier 2: concrete example, fallacy is named, player walks away with a tool they can use to spot bad arguments in everyday speech.

### Tier 3 — less-famous moves, cross-tradition

```
Q: The Mu'tazila school of medieval Islamic theology argued that reason
   alone could establish moral truths, and that God himself is bound by
   justice. Why did this view eventually lose out to the Ash'ari school?
A: The Ash'aris argued that calling God "bound" by anything — even
   justice — limits divine sovereignty; goodness is whatever God commands.
```
Why it's tier 3: real intra-tradition dispute, not famous in the West, treated with the same seriousness as a Greek debate.

```
Q: Zhuangzi woke from a dream of being a butterfly and asked whether he
   was a man who had dreamed he was a butterfly, or a butterfly now
   dreaming he was a man. What two philosophical questions does this
   raise at once?
A: Whether we can ever know we are not dreaming, and whether the
   boundaries we draw between kinds of being are as fixed as we assume.
```
Why it's tier 3: the dream-skepticism move is tier 2, but the *second* question (categorical fluidity) lifts it to tier 3.

```
Q: Hume noticed that we never observe causation directly — only that one
   event follows another. He concluded that "cause and effect" is a habit
   of mind, not a feature of the world. What problem did this create for
   science?
A: If causation is psychological rather than real, scientific laws
   describe our expectations, not nature itself — undermining the
   confidence that the future will resemble the past.
```
Why it's tier 3: requires the player to follow two steps of consequence.

```
Q: Frederick Douglass gave his most famous speech on July 4th, 1852, in
   Rochester, NY. He asked his audience: "What, to the American slave,
   is your Fourth of July?" Yet his argument was not that the Declaration
   of Independence was wrong. It was something more sophisticated. What
   did he argue?
A: That the Declaration's natural-rights claims were exactly right, but
   America was failing to live up to its own founding principles —
   making slavery an American betrayal of America, not an American truth.
```
Why it's tier 3: requires the player to grasp immanent critique (judging a tradition by its own standards) as a more powerful move than external rejection; American political philosophy on its own terms.

### Tier 4 — technical moves through their consequences

```
Q: Russell and Whitehead spent ten years and three volumes trying to
   derive all of mathematics from pure logic. In 1931, a 25-year-old
   named Gödel destroyed their project in a single paper. What did he
   prove?
A: Any formal system rich enough to express arithmetic contains true
   statements it cannot prove — no complete, consistent foundation is
   possible.
```
Why it's tier 4: technical result (Gödel's first incompleteness theorem), conveyed entirely through story + consequence. No technical vocabulary required.

```
Q: Wittgenstein early in his career argued that the structure of language
   mirrors the structure of the world; the limits of one are the limits of
   the other. Decades later he reversed himself entirely. What was his
   later view?
A: That language has no single structure — words get their meaning from
   the rule-governed games people play with them, not from any underlying
   form.
```
Why it's tier 4: requires the player to hold two positions and grasp a reversal — a real intellectual movement.

```
Q: Quine attacked the long-standing distinction between "analytic" truths
   (true by meaning alone, like "all bachelors are unmarried") and
   "synthetic" truths (true by how the world is). What did he argue
   instead?
A: That no sentence is held true purely by meaning — even logical truths
   can in principle be revised if doing so makes our overall theory
   simpler.
```
Why it's tier 4: real philosophical dispute, requires the player to grasp what's at stake in dissolving a distinction.

```
Q: Hayek argued in 1945 that no central planner could ever direct an
   economy as well as a price system — not because planners are corrupt
   or stupid, but because of something specific about knowledge itself.
   What was his claim?
A: That the knowledge needed to run an economy — who needs what, where,
   when, at what cost — exists only as fragments in millions of minds,
   and prices are the one mechanism that gathers those fragments into a
   single coherent signal.
```
Why it's tier 4: serious economic-philosophical argument conveyed through its core insight; no jargon; the player walks away understanding why central planning failed in principle, not just in practice.

### Tier 5 — hard problems, sophisticated positions

```
Q: Foucault analyzed Bentham's Panopticon — a prison where one guard in
   a central tower can see every cell, but prisoners cannot see whether
   the guard is watching. He argued it was a model for how modern power
   works. What was his claim?
A: Modern power operates by making people internalize the possibility of
   being watched — you discipline yourself because you might always be
   observed, making external force unnecessary.
```
Why it's tier 5: deep idea (productive vs. repressive power), conveyed without academic jargon, connects to surveillance/credit-score/grading systems the player already lives in.

```
Q: Frank Jackson imagined a brilliant scientist named Mary who has lived
   her entire life in a black-and-white room studying the physics of
   color. One day she walks outside and sees red for the first time.
   What does this thought experiment argue?
A: That she learns something new the moment she sees red — meaning
   there are facts about conscious experience that no amount of
   physical knowledge can capture.
```
Why it's tier 5: hard problem of consciousness, presented as story before any technical move.

```
Q: Derek Parfit argued that personal identity is not what matters when
   we think about our future. He imagined being teleported by being
   scanned, destroyed on Earth, and reconstructed on Mars from new atoms.
   What did he conclude about why we fear death?
A: That we are wrong to assume a single continuing "self" persists
   through time — psychological continuity is all there is, and survival
   is a matter of degree, not all-or-nothing.
```
Why it's tier 5: serious philosophical move (reductionism about personal identity), accessed through a vivid thought experiment.

```
Q: Solzhenitsyn wrote The Gulag Archipelago by memorizing chapters and
   smuggling them out through friends — never keeping the full manuscript
   in one place. When the West finally read it in 1973, he argued the
   real evil of the Soviet system was not Stalin's particular cruelty
   but something deeper that ordinary citizens were doing every day.
   What was it?
A: That the system rested on every citizen being asked, daily, to assent
   to lies they knew were lies — and the moral collapse was in the
   assent, not the camps themselves.
```
Why it's tier 5: deep moral philosophy (the lie as the foundation of totalitarianism — "Live Not by Lies"), accessed through story; requires the player to grasp a non-obvious thesis that reframes their understanding of how regimes survive.

## 5. Distractor design

The single most important rule. Half the current bank fails here.

- **All four choices within ±15% of mean choice length.** Hard enforced.
- **Every distractor is a real rival position or a real misunderstanding.** No throwaways. The player who picks wrong should learn something from being wrong.
- **No "obviously dumb" options.** "A plant / a mineral / an animal / a person" is not a quiz — it is an insult.
- **Distractors that map to other thinkers' positions are excellent.** A Plato question's distractors can be Aristotle, Pythagoras, Heraclitus positions. The player who picks one of them has confused two real philosophers, which is a useful confusion.
- **Period-appropriate.** A T2 question on Hume should not have a distractor citing Kripke unless the question is *about* the historical chain — anachronistic distractors are sloppy.

## 6. Philosophy-specific anti-patterns

In addition to the cross-subject anti-patterns in `moral_vision.md`:

- **"What is [Greek or German term]?"** Banned at every tier. Reframe as: present the move or the consequence, ask what concept is at work.
- **"Who wrote *X*?"** Banned unless the question is really about authorship-as-puzzle (e.g., Plato dialogues' attribution disputes, the Wittgenstein/early-vs-late split).
- **Trivia about a philosopher's biography** unless the biography illuminates the philosophy. "Who tutored Alexander?" — banned. "Aristotle's tutoring of Alexander shaped his thinking about which question?" — fine if true and interesting.
- **Strawmen of any tradition.** Especially: no cartoonish Marxism, no cartoonish Objectivism, no "primitive religion" framings. Real positions only.
- **Smug-believer voice** (Rand cluster in current bank is the canonical failure). Distractors-as-virtuous-truisms with answer-as-obvious-good-guy is banned.
- **Dictionary definitions disguised as questions.** "What does 'ethics' study?" — banned.

## 7. What success looks like for the rebuild

A philosophy bank where:
- A randomly drawn T2 question makes a curious 14-year-old want to look something up.
- A randomly drawn T5 question makes a philosophy grad student nod approvingly.
- No question can be solved by picking the longest or shortest choice.
- No question feels like a flashcard.
- No question reads like advocacy for or against any tradition.
- A player who plays 50 chains over a run encounters Confucian, Daoist, Islamic, Christian, Hindu, secular, ancient, and contemporary thought — not just the Greek-to-German-to-French canon.

That last point is the coverage rule. The taxonomy is what guarantees it.
