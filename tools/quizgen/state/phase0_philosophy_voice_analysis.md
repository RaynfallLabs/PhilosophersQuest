# Phase 0: Philosophy Question Bank — Voice Analysis

Source: `C:\Users\brand\Documents\PhilosophersQuest\data\questions\philosophy.json`
615 records, ~687 KB. Tier distribution: T1=73, T2=158, T3=176, T4=133, T5=75.
Honest summary: about a third of this bank is genuinely good (the "wonder-driven" voice we want — Heraclitus, Zhuangzi, Berkeley, Foucault), and about a third actively undermines the design (rote definitions, length-leaked answers, jargon walls). The rest is mediocre filler that could go either way.

---

## 1. Ten KEEP-EXEMPLARS (the voice we want to imitate)

### KEEP-1 (tier 2, Socrates / market dialogue)
> Q: "Socrates never lectured or wrote textbooks. Instead, he would approach strangers in the market and ask them questions until they contradicted themselves. What was he trying to prove?"
> A: "That most people do not actually understand the things they claim to know — wisdom begins with recognizing your own ignorance"

Why it works: opens with an image (markets, strangers), poses a *why* question rather than a *what*, the answer reframes wisdom in a way that reorients the player. This is the canonical voice.

### KEEP-2 (tier 2, Heraclitus / river)
> Q: "Heraclitus said 'You cannot step in the same river twice.' What philosophical claim does this illustrate?"
> A: "Reality is in constant flux; nothing stays the same"

Why it works: hooks on a famous concrete image; the four choices are all coherent philosophical positions (not throwaways); choices are within ~±10% length. Tier-appropriate.

### KEEP-3 (tier 2, Epicurus / surprise reversal)
> Q: "Epicurus taught that the goal of life is pleasure — but his idea of the highest pleasure surprises most people. What did he say a person most needs to be happy?"
> A: "Freedom from fear and pain, and the company of close friends — not excitement, wealth, or fame"

Why it works: explicit "you probably think you know this, but here's the twist" framing. Pure wonder-driven. The "surprises most people" cue is itself a signature move.

### KEEP-4 (tier 2, Zhuangzi / butterfly)
> Q: "The Taoist philosopher Zhuangzi woke from a dream in which he had been a butterfly. He asked: 'Am I a man who dreamed I was a butterfly, or a butterfly now dreaming I am a man?' What two philosophical questions does this raise at once?"
> A: "Whether we can ever know we are not dreaming, and whether the firm boundaries we draw between different kinds of being are really as fixed as we assume"

Why it works: leads with a scene, then asks the player to *see* the deeper structure. Note: the answer is on the long side, so distractors are also long — parity preserved.

### KEEP-5 (tier 3, Searle / Chinese Room)
> Q: "John Searle imagined a person locked in a room who receives Chinese symbols through a slot, looks up rules in a book to produce output symbols, and sends them back — never understanding a word of Chinese. What does this thought experiment argue?"
> A: (paraphrased in choices, Chinese Room as argument against strong AI)

Why it works: presents the thought experiment as a vivid story before asking what it argues. The player is given the puzzle and asked to interpret it, not just to remember a name. Very low jargon density.

### KEEP-6 (tier 2, Berkeley / unobserved tree)
> Q: "Berkeley argued that a tree you are not looking at does not actually exist at that moment. What was his philosophical argument for this strange claim?"
> A: "Without a mind perceiving it, there is nothing left — 'material substance' is just a name for a bundle of perceptions with no perceiver behind them"

Why it works: the question itself sounds insane on first read — that's the hook. "Strange claim" is permission for the player to be surprised. Distractors are coherent rival positions.

### KEEP-7 (tier 5, Foucault / Panopticon)
> Q: "Foucault analyzed Jeremy Bentham's Panopticon — a prison where one guard in a central tower can see every cell, but prisoners cannot see whether the guard is actually watching. He argued it was a model for how modern power works. What was his claim?"
> A: "Modern power operates by making people internalize the possibility of being watched — you discipline yourself because you might always be observed, making constant external force unnecessary"

Why it works: tier-5 idea conveyed without tier-5 jargon. The visual (tower, cells) does the heavy lifting; the answer connects to surveillance/credit-score/grading systems the player already lives in. Borderline long (timer hazard), but the payoff is real.

### KEEP-8 (tier 4, Gödel / killed Russell's project)
> Q: "Russell and Whitehead spent ten years and three volumes trying to prove that all of mathematics could be derived from pure logic. In 1931, a 25-year-old mathematician named Gödel destroyed their project. What did he prove?"
> A: "Any formal system powerful enough to express arithmetic must contain true statements it cannot prove — no complete, consistent foundation for all of mathematics is possible"

Why it works: framed as a story (ten years, three volumes, 25-year-old comes along and destroys it). "Huh, I didn't know that" guaranteed. Distractors are all plausible-sounding *wrong* takes someone might give about Gödel.

### KEEP-9 (tier 2, Mill / Socrates dissatisfied)
> Q: "Mill revised Bentham's utilitarianism by insisting pleasures differ in quality, not just quantity. What was his most famous line expressing this?"
> A: "It is better to be Socrates dissatisfied than a fool satisfied"

Why it works: tight, the quote *is* the payoff, distractors are real philosophical slogans (Bentham's, Kant's, Marx's) so the player has to actually know them apart. Excellent length parity.

### KEEP-10 (tier 2, Buddha / craving)
> Q: "The Buddha identified one root cause of all suffering. It is not pain, poverty, or illness. What is it, and why does understanding it point toward liberation?"
> A: "Craving and attachment — clinging to pleasant things and resisting unpleasant ones, when all things are impermanent and guaranteed to change"

Why it works: the question itself preemptively rules out the obvious wrong answers ("not pain, poverty, or illness"), which forces the player past the easy guess. Tone is respectful, not preachy. Distractors are also plausible religious-philosophical claims, not strawmen.

---

## 2. Ten ANTI-EXEMPLARS (what to avoid)

### ANTI-1 (tier 1, "Will to Power")
> Q: "Which philosopher is most associated with the concept of 'will to power'?"
> Choices: "Hegel, who saw history as..." (75 chars) / "Marx, who argued that..." (77) / **"Nietzsche"** (9) / "Schopenhauer, whose..." (79)

**Failure mode: catastrophic length-leak.** The correct answer is 9 chars; the distractors are 75–79 chars. A player skimming under time pressure will pick the one-word answer without reading the question. This pattern appears dozens of times in the bank.

### ANTI-2 (tier 1, Rex the dog)
> Q: "If all dogs are animals, and Rex is a dog, what is Rex?"
> Choices: "A plant" / "A mineral" / "An animal" / "A person"

**Failure mode: insultingly trivial + no philosophical content.** This is a syllogism-shaped tutorial pretending to be a philosophy question. The "context" gestures at Aristotle but the question itself teaches nothing. T1 should still be philosophical, not 1st-grade logic.

### ANTI-3 (tier 1, A > B > C)
> Q: "If A is bigger than B and B is bigger than C, which is smallest?"
> Choices: "A" / "B" / "C" / "All three are equal"

**Failure mode: not a philosophy question.** Length-leak too (the wrong "All three are equal" is much longer). This belongs in a math bank, if anywhere. Wonder content: zero.

### ANTI-4 (tier 1, "What does 'ethics' study?")
> Q: "What does 'ethics' study?"
> A: "Right and wrong behavior and how we ought to live"

**Failure mode: rote dictionary definition.** The exact pattern we said to avoid in the brief. Repeated across the bank for "epistemology," "metaphysics," "aesthetics," "skepticism," "empirical," "a posteriori," "teleology," etc. — at least 30 questions of this shape.

### ANTI-5 (tier 1, Alexander's tutor)
> Q: "Who was the tutor of Alexander the Great?"
> A: "Aristotle, who tutored the young prince from age 13 in Macedonia"

**Failure mode: the exact rote pattern the brief named.** Quoted in the brief as the anti-pattern, and here it is verbatim in the bank. Pure trivia, no philosophical insight.

### ANTI-6 (tier 5, "What is 'Husserlian epoche'?")
> Q: "What is 'Husserlian epoche'?"
> A: "Suspending judgment about the external world to focus purely on conscious experience"

**Failure mode: bare-jargon definition lookup.** Tier 5 here has decayed into "What is [Greek/German term]?" — same pattern as ANTI-4 but with harder vocabulary. The question gives the player nothing to grab onto. Same shape: "What is 'dialetheism'?", "What is 'thrownness'?", "What is 'opacity of reference'?".

### ANTI-7 (tier 1, Rand "parasite")
> Q: "Rand said that a person who produces nothing but lives off the work of others — especially using political connections to take from producers — is a what?"
> Choices: "A citizen" (9) / "A consumer" (10) / **"A parasite or moocher"** (21) / "A dependent" (11)

**Failure mode: length-leak + leading question.** The question itself ("produces nothing… takes from producers") rhetorically rules out the distractors before the choices appear. Combined with the answer being 2x the length of any distractor, this is unmissable. Also: Rand questions across the bank lean preachy in a way the brief flagged ("no smug-believer voice") — this one straps the player to an ideological frame.

### ANTI-8 (tier 4, Rand on measurement omission)
> Q: "Rand developed a theory of concept formation she called 'measurement omission.' What does it claim, and how does it avoid both Platonic forms and pure nominalism?"
> A: 228 chars (vs distractors at 93/101/115)

**Failure mode: length-leak + two-questions-in-one + timer-hazard.** The question asks two things ("What does it claim" AND "how does it avoid…"), so the correct answer is forced to address both — and is therefore 2–2.5x longer than every distractor. Skim-pick guaranteed. Plus the question + answer together are ~430 chars to parse in 4–5 seconds.

### ANTI-9 (tier 5, Nietzsche perspectivism)
> Q (305 chars): "Nietzsche's perspectivism holds that there are no facts, only interpretations. Yet Nietzsche himself makes what appear to be factual claims — that slave morality exists, that nihilism is coming, that God is dead. How can he avoid the self-refuting charge that perspectivism is itself just one perspective?"

**Failure mode: too long for the timer.** Question alone is 305 chars; with four choices the player must parse ~1,080 chars. At ~250 chars/sec quick-read pace that's 4+ seconds *just to read*, leaving zero for thought. Content is good; length is fatal at 38 s with a chain mechanic.

### ANTI-10 (tier 3, "free will" definition)
> Q: "What does 'free will' mean in philosophy?"
> A: "The ability to make choices independent of prior causes"

**Failure mode: rote definition disguised as a question.** "What does X mean in philosophy?" appears for "free will," "teleology," "skepticism," "empirical," "a posteriori," "a fortiori" — uninspired vocabulary drilling. The answer is also literally one of the contested positions (libertarian free will) presented as the definition, which is mildly factually misleading.

---

## 3. Pattern Summary (~300 words)

**The five dominant failure modes:**

1. **Length-leaks-answer is endemic.** 49.4% of records (304/615) have an answer length more than ±15% from the mean of their choices. The answer is the *longest* choice 47.0% of the time and the *shortest* 36.9% — so 84% of questions leak length information one direction or the other. The worst offenders are ~19× length ratios (one-word correct answer next to 75-char distractors). Under a 4–5-second skim budget this is the single most damaging defect.

2. **Rote-definition questions form a large under-belt.** "What does X mean / study?", "What is the term for…?", "Who wrote…?", "Who was the tutor of…?" — at least 30 explicit cases by strict pattern match, probably 80+ by spirit. T1 and T5 are the worst affected: T1 leans on dictionary definitions, T5 leans on "What is [German/Greek jargon]?". Neither produces wonder.

3. **Tier-5 timer hazards.** A cluster of T5 questions runs 250–305 chars in the question alone, plus four ~100-char distractors. Total parse budget exceeds what a 38-second timer with a chain mechanic can support — these questions are unwinnable in chain mode even for someone who knows the answer.

4. **Two-questions-in-one bloat.** Questions of the form "What does X claim, AND how does it…" force a correct answer that must address both clauses, blowing it past distractors in length and creating a compound length-leak. Especially common in the Rand/Rothbard/Mises cluster (idx 455–550).

5. **Ideological tonal drift.** A roughly 50-question cluster on Rand/Rothbard/Mises (T1 surprisingly, plus T4) frames distractors as obvious-wrong strawmen and answers as virtuous truisms — the "smug-believer voice" the brief warned against. Marx-related questions sometimes mirror this in the opposite direction ("Marx's theory gets *catastrophically* wrong…").

**Voice strengths worth preserving:**

- **Story-led questions.** The best questions open with a scene: Socrates in the market, Zhuangzi waking, a prisoner in the Panopticon, Russell + Whitehead's ten-year project being destroyed. This is the signature voice and it's already present in maybe a third of the bank.
- **Surprise reversals.** "Epicurus taught pleasure — but his idea of pleasure surprises most people." "Berkeley argued a tree you're not looking at doesn't exist." These give the player permission to be surprised, which is the wonder mechanic.
- **Coherent distractors.** The good questions use *real* rival positions as wrong answers (other schools, other philosophers' actual views), so the player learns something even when wrong. Many bad questions use obvious strawmen.
- **Concrete handles.** River, butterfly, cave, tower, slot in a door. The good questions weight toward image-bearing language. The bad ones weight toward Greek/German nouns.

---

## 4. Baseline Length Statistics

Computed across all 615 records.

| Metric | Median | Max | Min |
|---|---|---|---|
| Question text length (chars) | **102** | 305 | 17 |
| Single choice length (chars) | **86** | 283 | 1 |

| Per-record choice-length spread | Median | Max |
|---|---|---|
| Longest/shortest ratio | **1.33×** | 19.00× |
| (Longest − shortest) / shortest, as % | **32.7%** | 1800% |

**Answer-length-parity diagnostic:**

- Records where the answer is outside the ±15% band of mean choice length: **304 / 615 (49.4%)**
- Records where the answer is the longest choice: **289 (47.0%)**
- Records where the answer is the shortest choice: **227 (36.9%)**
- Combined "answer is an extreme of the four": **83.9%**

**Reading targets implied for new questions (for the timer math: 38 s @ WIS 10, chain cap ~5, so ~4–5 s per question):**

- Question text: aim ≤120 chars (current median 102 is fine; cull >200).
- Single choice: aim ≤100 chars (current median 86 is fine; cull >150).
- Per-record longest/shortest ratio: aim ≤1.15× (current median 1.33 — needs tightening on roughly half the bank).
- Hard rule: total record cost (question + 4 choices) under ~600 chars for T1–T3, under ~800 for T4–T5. Anything over kills the chain at the timer.
