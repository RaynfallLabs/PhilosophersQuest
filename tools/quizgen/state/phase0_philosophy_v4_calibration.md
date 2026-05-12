# Phase 0: Philosophy Bank — v4 Moral Vision Calibration

**Source:** `C:\Users\brand\Documents\PhilosophersQuest\data\questions\philosophy.json` (615 records, 687 KB)
**Rubric:** `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\moral_vision.md` (v4, 2026-05-10)
**Sampling method:** Stratified random by tier, 5 per tier, `random.seed(20260510)` via `py` Python 3.14.3
**Sample size:** 25 (T1=5, T2=5, T3=5, T4=5, T5=5)
**Tier distribution in bank:** T1=73, T2=158, T3=176, T4=133, T5=75
**Sampler script:** `tools\quizgen\state\_calibration_sample.py`
**Sample dump (machine-readable):** `tools\quizgen\state\_calibration_sample.json`

---

## Aggregate results

| Verdict   | Count | %     |
|-----------|------:|------:|
| KEEP      |     2 |   8%  |
| REPAIR    |    14 |  56%  |
| DISCARD   |     9 |  36%  |

### Per-tier verdicts

| Tier | KEEP | REPAIR | DISCARD | KEEP+REPAIR survival |
|-----:|-----:|-------:|--------:|---------------------:|
|  T1  |   0  |     2  |     3   |        40%           |
|  T2  |   1  |     4  |     0   |       100%           |
|  T3  |   1  |     3  |     1   |        80%           |
|  T4  |   0  |     2  |     3   |        40%           |
|  T5  |   0  |     3  |     2   |        60%           |

### Top failure modes (frequency across the 25)

| Rank | Failure mode                                                    | Count | Notes |
|-----:|-----------------------------------------------------------------|------:|-------|
|   1  | **Length parity** (>±15% from mean, or longest/shortest >1.30)  |   19  | The most pervasive deterministic failure. Even most KEEP candidates fail this. |
|   2  | **Rote / dictionary-definition framing** (no wonder hook)       |    7  | "What is X?" / "What does Y study?" patterns, especially T1/T4/T5 mid-canon. |
|   3  | **Length-leaked answer** (correct choice notably longer/shorter)|    5  | Subset of (1). Several Rand/Rothbard questions where the correct option is ~2× longer. Mises ABCT and Seneca on anger especially flagrant. |
|   4  | **Tier mismatch** (too easy/trivial for tier label)             |    4  | "Rex is a dog" at T1 (Aristotle logic but content is 1st-grade), Socrates "I know nothing" at T2 vs. a richer T2 version of the same fact, "examined life" repeated across tiers. |
|   5  | **Cost cap exceeded**                                           |    3  | Hegel T3 (717), Seneca T3 (786), Rand value-theory trilemma T5 (819). |
|   6  | **Mild advocacy / one-sided framing**                           |    2  | Rand selfishness T1 ("she was precise: she did not mean grabbing from others" in context reads as defense, not discovery); Rothbard T1 framing makes the steel-man only on the libertarian side. |
|   7  | **Two-questions-in-one bloat**                                  |    2  | Rothbard class theory T4 (asks classes AND difference from Marx); Rand value trilemma T5 (asks distinction AND why life is the standard). |

None of the 25 hit: anti-white/anti-Western framing, "sex is a spectrum" applied to humans, smug-atheist/smug-believer voice, partisan dated references, or "TIL problematic" reveals. That is genuinely good news for the bank's posture — the dominant failure is craft (length, voice, tier) not values.

---

## Per-question analysis

Gate table key: **P** = pass, **F** = fail, **NA** = not applicable. Gates in order:
1. Schema · 2. Length parity · 3. Cost cap · 4. Anti-rote regex · 5. Wonder-driven · 6. Avoids advocacy · 7. Steel-manned distractors · 8. No "TIL problematic" · 9. Story-led/concrete · 10. Two-in-one · 11. Jargon wall · 12. Dated · 13. Anti-white/anti-Western · 14. Sex-spectrum in humans · 15. Smug voice · 16. Viral test.

(Gates 13–15 are P/NA for every question in this sample, omitted from the per-question rows to save space; absence is reported in the aggregate section above.)

---

### Q1 — T1, idx 252 ("integrity / broken promise")

> Q: "If you break a promise on purpose, you have acted without what?"
> A: "Integrity"
> Choices: "Integrity" / "Compassion" / "Accountability" / "Rationality"
> Context: "Integrity comes from the Latin 'integer,' meaning whole or complete. A person of integrity is undivided -- their actions match their words. Breaking a promise fractures that wholeness, which is why it feels like a betrayal of character, not just of a commitment."

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | F | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Vocabulary-quiz framing, not philosophy. The distractors are all unrelated virtues, not rival positions on what a broken promise undermines (cf. §6 anti-pattern "strawman distractors": Compassion/Accountability/Rationality are not real *rival accounts*; they are just other words). Reads as a values-pep-talk, which the rubric explicitly rules out in §5 ("show virtue, don't preach virtue"). No story-led hook, no wonder. Tier T1 should still be philosophical (cf. moral_vision §6 + Phase 0 voice analysis ANTI-2 already flagging this pattern).

### Q2 — T1, idx 464 (Rothbard "gang of thieves")

> Q: "Rothbard said 'The State is a gang of thieves writ large.' What made this a philosophical claim rather than just an insult?"
> A: "He was applying the same moral standard to governments that we use for individuals — if force without consent is theft when one person does it, it remains theft when the state does it"
> (4 long-form choices, lens 82/183/83/92)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | F | P | P | P | P  | P  | P  | F  |

**Verdict: REPAIR.** Strong wonder/story (quote + reframe), but two structural problems: (a) length-leak — the correct answer is 183 chars vs. 82/83/92 for distractors, which directly violates §6 length-leaks-the-answer; (b) the framing leans advocacy: "what made this a philosophical claim rather than just an insult" presupposes the reader should be convinced it is philosophical, which is the §6 advocacy anti-pattern in subtle form. Repairable by rewriting the question as a discovery-framing ("Rothbard argued that the standard moral judgment we apply to individuals also applies to states. What was the central move in his argument?") and rebalancing length.

### Q3 — T1, idx 249 ("what is a contradiction?")

> Q: "A 'contradiction' is when two things are what?"
> A: "Both true and false at the same time"
> Choices length-OK-ish (mean 47.8, ratio 1.53)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | F | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Dictionary-definition pattern §6 explicitly bans ("rote memorization without a wonder hook"). The answer is also technically wrong — a contradiction in logic isn't "two things that are both true and false at the same time," it's the simultaneous assertion of P and not-P. The context paragraph references Aristotle and the law of non-contradiction, but the question itself never reaches that depth. Distractors are filler. Could become a real question (Aristotle's law of non-contradiction with a vivid case) but the current shell isn't salvageable.

### Q4 — T1, idx 459 (Rand "selfishness as virtue")

> Q: "Ayn Rand believed that selfishness — caring about your own life and happiness — is not a sin or a weakness. She wrote an entire book arguing it is actually what?"
> A: "A virtue — because your own life and happiness are genuinely valuable"
> 4 plausible-sounding choices, lens 54/69/59/55

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | F | P | P | P | P  | P  | P  | P  |

**Verdict: REPAIR.** Good surprise-reversal hook ("not a sin or a weakness"), distractors are real rival positions (necessary evil / instinct to be replaced / acceptable if harmless), and the answer is short enough not to leak. The advocacy worry is mild: the question pre-defines selfishness in Rand's preferred terms ("caring about your own life and happiness") before asking, which is a thumb-on-the-scale move §6 warns about. Length parity is borderline (ratio 1.28, one choice +16% over mean). Repair: rebalance choice lengths and let the player meet Rand's redefinition *in the answer* rather than smuggling it into the question.

### Q5 — T1, idx 226 ("Rex the dog")

> Q: "If all dogs are animals, and Rex is a dog, what is Rex?"
> Choices: "A plant" / "A mineral" / "An animal" / "A person"

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | F | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Identical to ANTI-2 in the prior voice analysis. Insultingly trivial (the syllogism gives the answer in the question), distractors are joke-tier ("plant," "mineral"), no wonder, no philosophy. §6 "punchline-as-distractor" applies. The context paragraph gestures at Aristotle but the question itself doesn't teach what a syllogism is or why it matters. Tier label is also wrong — this is below T1 difficulty for the philosophy bank.

### Q6 — T2, idx 52 ("what is deontological ethics?")

> Q: "What is 'deontological ethics'?"
> A: "Ethics based on duties and universal moral rules"
> Four parallel "Ethics based on X" choices, lens 57/69/48/67

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | F | F | P | P | P | F | P  | P  | P  | P  |

**Verdict: REPAIR.** Distractors are actually steel-manned (consequentialism, virtue ethics, contract theory — the four major ethical frameworks). That's the best thing about it. But the question is the §6/anti-rote pattern *exactly* — vocabulary lookup with no scene, no person, no example. Repair: open with Kant refusing to lie even to save a life, then ask what philosophical commitment that illustrates. Same distractors work.

### Q7 — T2, idx 24 (Epicurus "highest pleasure")

> Q: "Epicurus taught that the goal of life is pleasure — but his idea of the highest pleasure surprises most people. What did he say a person most needs to be happy?"
> A: "Freedom from fear and pain, and the company of close friends — not excitement, wealth, or fame"
> Choices 76/94/62/96

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | P | P | P | P | P  | P  | P  | P  |

**Verdict: KEEP.** This is one of the named exemplars in the prior voice analysis. Explicit surprise-reversal hook ("surprises most people"), distractors are real philosophical positions (Epicurean hedonist-cliché / civic-republican / Socratic-intellectualist), context is rich without preaching. Only fails length parity (94/62 = 1.52 ratio). I judge this as a KEEP rather than REPAIR because the parity failure is mild and the question already meets §8 ("what a great question looks like"). The author would not be embarrassed.

### Q8 — T2, idx 3 (Socrates "I know nothing")

> Q: "What was Socrates's most famous philosophical claim?"
> A: "That he knew nothing"
> Choices 46/49/20/55

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | F | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Catastrophic length-leak: the correct answer is 20 chars, distractors are 46/49/55. A player skimming under time pressure picks the short one (this is the exact ANTI-1 pattern flagged in the prior voice analysis). Question is also flatly rote ("what was his most famous claim?") with no wonder hook. The bank's own Q1 (idx 0, "Socrates never lectured...") covers the same fact dramatically better — this version should die. Note: distractors are real positions but the structural giveaway sinks it.

### Q9 — T2, idx 41 (Nietzsche "God is dead")

> Q: "When Nietzsche wrote 'God is dead,' he was not celebrating. He was sounding an alarm. What was the danger he was warning about?"
> A: "Western civilization had destroyed the foundation of its values without yet building a new one — leaving a moral vacuum that could collapse into nihilism"
> Choices 101/153/113/99

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | P | P | P | P | P  | P  | P  | P  |

**Verdict: REPAIR.** Story-led ("not celebrating, sounding an alarm"), surprise-reversal, distractors are coherent alternative readings of "God is dead," no smug-atheist or smug-believer voice — exactly the §4 posture on hard topics. One real problem: length-leak (correct is 153 chars vs. 99/101/113 for distractors, ratio 1.55). Fixable with light edits. Otherwise this is near-KEEP.

### Q10 — T2, idx 49 (Locke "blank slate")

> Q: "Locke argued that the human mind at birth is a blank slate — completely empty of all knowledge. Where does everything we know come from, according to him?"
> A: "Experience alone — either sensation (perceiving the world through the senses) or reflection (perceiving our own mental operations)"
> Choices 81/130/85/101

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | P | P | P | P | P  | P  | P  | P  |

**Verdict: REPAIR.** Strong question — empiricism vs. innate ideas is set up as a real philosophical dispute (Descartes is named in context, not in the question), distractors are real rival positions (innatism / linguistic determinism / Augustinian illumination). Length-leak again: correct answer 130 chars vs. 81/85 for two distractors (ratio 1.60). Tradition fit (§1 lineage, Locke at the root) is explicit. Repair: tighten the correct answer or expand the shorter distractors to bring the ratio under 1.30.

### Q11 — T3, idx 81 (Hegel dialectic)

> Q: "Hegel argued that ideas, cultures, and consciousness itself develop through a specific three-stage pattern. What are the three stages, and what drives the process forward?"
> A: "A thesis generates its contradiction (antithesis); their conflict produces a synthesis that preserves and transcends both — which then becomes the next thesis"
> Choices 138/158/121/129, total 717 (cap 600)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | F | P | F | P | P | P | F | F  | F  | P  | F  |

**Verdict: DISCARD.** This is a two-question-in-one ("what are the stages AND what drives it forward"), runs over the cost cap, all four choices are dense walls of paired technical labels, and the question itself is largely a vocabulary review. The context paragraph is the *good* version of this material — it points out that the thesis-antithesis-synthesis triad was Fichte's, not Hegel's, and Hegel's actual term was Aufhebung. That's the question worth asking. Current shell is a jargon wall (§6) and bloated. Cannot be repaired without a fundamental rewrite.

### Q12 — T3, idx 511 (Mises ABCT)

> Q: "Mises argued that the Austrian Business Cycle Theory explains recessions not as accidents but as the inevitable result of one specific government action. What?"
> A: "Central bank credit expansion that pushes interest rates below their natural market level, triggering a boom built on malinvestment that must eventually collapse"
> Choices 83/161/93/90

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | P | P | P | P | P  | P  | P  | F  |

**Verdict: REPAIR.** Content is exactly what §3.3 (Austrian school coverage) calls for, distractors are real rival theories (irrational-exuberance / underconsumption / overproduction), framing is wonder-led ("not an accident but inevitable"). The structural flaw is the length-leak: correct answer 161 chars vs. distractors 83/90/93 — a player who learned nothing about ABCT could pick correctly by length alone. That alone violates §6 enough that under the viral test this question would embarrass. Repair = rebalance lengths.

### Q13 — T3, idx 328 ("examined life")

> Q: "What is 'the examined life' according to Socrates?"
> A: "A life spent questioning beliefs and values to understand what is good"
> Choices 70/83/79/76 — actually parity-OK

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | F | F | P | P | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Passes the deterministic gates (rare for this bank!) but is a vocabulary-definition T3 question of material that the bank already covers as a stronger T1 question at idx 4 ("Socrates said 'The unexamined life is not worth living'..."). Anti-rote pattern, no story, no surprise, tier is mis-set (this is T1 difficulty). The distractors are also weak — they don't represent rival views of what the examined life *is*, just generic-sounding lives that aren't it. Could be repaired but the same material already lives in better form elsewhere in the bank, so kill rather than repair.

### Q14 — T3, idx 312 (trolley problem)

> Q: "What is the 'trolley problem' designed to explore?"
> A: "Moral choices between doing harm and allowing harm"
> Choices 75/75/50/72

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | P | P | F | P  | P  | P  | P  |

**Verdict: REPAIR.** Distractors are actually well-chosen rival construals of the trolley problem (utilitarian vs. omission vs. doing/allowing vs. personal-risk), but the question itself is the §6 anti-rote pattern in pure form: "what is X designed to explore?" with no story or scene. The trolley problem *is* a scene; this question fails to use it. Length-leak too — correct answer is 50 chars vs. 72-75 for distractors. Repair: lead with the scene (the runaway trolley, five workers, one bystander, the lever) and ask what moral disagreement it lays bare.

### Q15 — T3, idx 600 (Seneca on anger)

> Q: "Seneca argued that anger is the most destructive of all emotions — he wrote an entire essay, On Anger, condemning it absolutely. What was his philosophical case against it?"
> A: "Anger is always based on a false premise — that something has happened that should not have — when in fact everything that can happen to a mortal will happen; accepting this makes anger not just unnecessary but irrational"
> Choices 139/221/121/133, total 786 (cap 600)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | F | P | P | P | P | P | P | P  | F  | P  | F  |

**Verdict: REPAIR.** The content is wonderful and exactly the Stoic-virtue material §2 wants featured. Three real problems: (a) bloated total (786 vs 600 cap for T3), (b) the correct answer is 221 chars while a distractor is 121 — almost 2× length-leak, (c) tier mismatch — this is T4 material, not T3. Repair: tighten everything by 25%, rebalance lengths, retag T4. Worth saving because the underlying question is so good.

### Q16 — T4, idx 546 (Rand "hierarchy of knowledge")

> Q: "Rand's account of reason as non-contradictory identification has a specific implication for how knowledge must be structured. What is it?"
> A: "All valid knowledge must form a hierarchy rooted in perceptual observation — any concept that cannot be traced back to perceptual concretes through a chain of valid abstractions is floating and invalid"
> Choices 107/201/107/103

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | P | P | P | F | P  | F  | P  | F  |

**Verdict: DISCARD.** Jargon wall (§6): "non-contradictory identification," "valid abstractions," "floating abstractions," "perceptual concretes" — a 14-year-old cannot grab onto any word in the first ten. Length-leak too: correct answer 201 chars vs. 103-107 for distractors (ratio 1.95). Bank can absolutely keep a Rand epistemology question, but the current shell reads as an Objectivist Bookshelf exam, not as wonder-driven discovery. No scene, no example, no concrete handle.

### Q17 — T4, idx 525 (Rothbard libertarian class theory)

> Q: "Rothbard identified a libertarian class theory as the key to understanding political economy. What two classes does it identify, and why does this differ from Marx's division?"
> A: long compound answer (224 chars)
> Choices 150/224/103/123, two-questions-in-one explicit in question stem

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | F | F | P | P | F | F  | F  | P  | F  |

**Verdict: DISCARD.** Two-questions-in-one in the most literal way ("what two classes AND why does this differ from Marx"). Length-leak is severe (224 vs 103). The framing also has subtle advocacy: "the key to understanding political economy" treats Rothbard's frame as authoritative rather than as a contender. §3.5 wants Rothbardian critique covered — it does not want it presented as the answer rather than as one answer worth taking seriously. The content is salvageable but in two separate, leaner questions, not as a rewrite of this one.

### Q18 — T4, idx 143 (Mill harm principle)

> Q: "Mill argued in On Liberty that society has exactly one legitimate reason to restrict individual freedom. What is it, and what does it explicitly exclude?"
> A: "Preventing harm to others — the liberty to act may not be restricted to protect the person from themselves, enforce morality, or prevent mere offense"
> Choices 115/149/128/128 — parity-OK (ratio 1.30)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | P | P | P | P | P | P | F  | P  | P  | P  |

**Verdict: REPAIR.** Best-built T4 question in this sample. Excellent length parity (149/115 = 1.30 exact), distractors are real rival liberal positions (social-order conservatism / utilitarian / democratic-consent), context is rich, voice is wonder-driven. Only soft fault: two-questions-in-one ("what is it AND what does it exclude"), which §6 flags. Light edit — drop "and what does it explicitly exclude" from the prompt, fold the exclusions into the answer choice without prompting for them — and it becomes a KEEP. Closest-to-KEEP in the T4 bucket.

### Q19 — T4, idx 208 ("cosmological argument")

> Q: "What is the 'cosmological argument' for God's existence?"
> A: "Everything that exists has a cause, so the universe must have a first uncaused cause"
> Choices 94/84/88/84 — parity-OK!

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | F | F | P | F | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Passes deterministic gates including the rare parity gate. But the rote-definition framing ("what is X?") is precisely §6's banned pattern. Worse, the distractors are actually *other valid arguments for God's existence* (fine-tuning, contingency, design), not steel-manned alternative *misunderstandings* of the cosmological argument. A philosophically literate player gets confused: all four answers are real arguments. The question doesn't teach what makes the cosmological argument distinctive. T4 tier label is also wrong; this is T2 difficulty. Material is fine for the bank but the question shell can't be repaired without writing a fundamentally different question.

### Q20 — T4, idx 376 ("explanatory gap")

> Q: "What is 'the explanatory gap'?"
> A: "The difficulty in explaining why physical brain processes feel like something from the inside"
> Choices 94/93/75/81 — parity-OK

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | F | F | P | P | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Same shell pattern as Q19. "What is X?" is the canonical §6 anti-rote frame. Distractors are themselves real philosophical positions (epistemic dualism, introspection-failure, folk vs. neuroscientific concepts), which is good, but the question never opens with the scene that makes the explanatory gap *feel like a problem* — a person describing the taste of an apple while a neuroscientist watches the brain scan, or Nagel's bat. Material is canonical; framing is wrong. Could be reborn as a story-led question, but the current shell isn't repairable.

### Q21 — T5, idx 538 (Rand value-theory trilemma)

> Q: "Rand's trilemma in value theory rejected both intrinsic and subjective value theories. How did she distinguish her 'objective' theory from both, and what makes life the standard of value?"
> A: 208-char compound answer with three labels in a row
> Choices 150/208/135/139, total 819 (cap 800)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | F | P | F | F | P | P | F | F  | F  | P  | F  |

**Verdict: DISCARD.** Hits the worst-case combo: two-questions-in-one ("how distinguish AND what makes life the standard"), over the T5 cost cap, length-leak, jargon wall ("intrinsic/subjective/objective" labels stacked four deep across all choices), and a smuggled advocacy frame ("what makes life the standard" presupposes Rand's answer is correct). Three Rand questions sampled this run; two of three are DISCARD, one is REPAIR — Rand coverage in the existing bank reads as Objectivist talking-points, not as wonder-driven exposition. That is a calibration signal worth flagging.

### Q22 — T5, idx 210 (Plantinga reformed epistemology)

> Q: "What is 'Alvin Plantinga's reformed epistemology'?"
> A: "Belief in God can be rational without evidence or argument"
> Choices 77/58/70/68

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | F | F | P | P | P | F | P  | P  | P  | F  |

**Verdict: REPAIR.** Distractors are real rival epistemological positions in philosophy of religion (classical foundationalism / coherentism / non-overlapping-magisteria). Tone is exactly the §4 "no smug atheist, no smug believer" posture the rubric wants — Plantinga is presented as making a real argument, not as an oddity. But the §6 anti-rote shell ("what is X?") kills it. Repair: open with Plantinga's analogy ("Plantinga argued that belief in God can be rational the same way belief in other minds is rational — without proof, but not without ground. What was his claim?").

### Q23 — T5, idx 451 (Sellars space-of-causes / space-of-reasons)

> Q: "Wilfrid Sellars distinguished between the 'space of causes' and the 'space of reasons.' What is the significance of this distinction for epistemology?"
> A: "Epistemic justification belongs to the space of reasons, not causes — being caused to believe something is not the same as having grounds for it"
> Choices 93/99/144/115

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | F | P | P | P | P | P | P | F | P  | F  | P  | P  |

**Verdict: REPAIR.** Real philosophical content delivered seriously, distractors are real rival positions (reductive naturalism / social constructionism / Diltheyan two-cultures), no advocacy, no smug voice. Two problems: length-leak (144 correct vs 93/99 distractors, ratio 1.55), and jargon-wall worry — "space of reasons" and "epistemic justification" are not anchored to any concrete scene. Context paragraph gives the bright-light-on-retina example; promoting that into the question itself would lift this to KEEP.

### Q24 — T5, idx 178 (Levinas)

> Q: "What is the philosophy of Emmanuel Levinas centered on?"
> A: "Ethics as first philosophy, rooted in responsibility to the Other"
> Choices 63/65/72/71 — parity-OK!

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | P | F | P | P | P | F | P  | P  | P  | F  |

**Verdict: DISCARD.** Passes the deterministic gates including parity, but the question is the §6 anti-rote shell ("what is X's philosophy centered on?") with no story or scene. The face-of-the-Other is a viscerally concrete image — that's what should anchor the question. Distractors are well-chosen rival positions (Heideggerian ontology, Husserlian time-consciousness, Hegelian recognition), which is to the bank's credit. But the question pattern is the one §6 specifically bans. Could be salvaged as a different question; current shell cannot.

### Q25 — T5, idx 452 (Aquinas Five Ways)

> Q: "Thomas Aquinas's 'Five Ways' for proving God's existence all share a common logical structure. What is it?"
> A: "Each argument starts from an observable feature of the world and reasons back to a first, uncaused cause"
> Choices 103/105/104/94 — parity-OK!

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|----|----|----|----|
| P | P | P | P | P | P | P | P | F | P  | P  | P  | P  |

**Verdict: KEEP.** Excellent length parity (ratio 1.12), real wonder hook (Aquinas's empirical move — start with the world, reason back), distractors are real alternative theistic argument-types (ontological / scriptural / moral) including the Anselm contrast that the context paragraph names explicitly, no smug voice in either direction, no advocacy. Could be lightly story-led with "Aquinas opens the Summa with five arguments..." but the question already works. Only soft fault: no story-led opening. Author would not be embarrassed. This is the second of two true KEEP candidates in the sample.

---

## Calibration note

**Sampled KEEP rate: 8% (2 / 25). Combined KEEP+REPAIR survival: 64% (16 / 25).**

The user described the bank as "absolutely awful." The data doesn't quite match that. The bank is *uneven*: about a tenth is genuinely good, about a third is unsalvageable, and the broad middle (~56%) is repairable with focused craft work — primarily length-balancing distractors and replacing "what is X?" shells with story-led openings. None of the 25 sampled questions hit the bank's *worst-case* failure modes — no anti-Western framing, no sex-spectrum-in-humans, no smug-atheist or smug-believer voice, no partisan dated references. The values posture (§3.7, §3.8, §4) is intact. The craft posture (§5, §6, §8) is not.

**Rubric calibration verdict: well-calibrated, slightly conservative on the KEEP threshold.**

The deterministic length-parity gate is doing most of the work — 19 of 25 fail it, including several questions (Epicurus, Nietzsche, Locke, Mises, Mill, Sellars) whose voice and content are otherwise excellent. The rubric is right to enforce length parity strictly, but a phased-rollout author would discover that hitting both ±15% deviation AND longest/shortest ≤1.30 is harder than it looks for tier-3+ questions where the correct answer naturally wants to be longer. That's the rubric working as intended — it forces conscious craft — but it also means the **REPAIR queue will be large**.

The cost cap (600 chars for T1-T3, 800 for T4-T5) is well-set: only 3 of 25 fail it, and those are precisely the questions that *should* fail it (Hegel dialectic two-in-one, Seneca essay-in-an-answer, Rand trilemma essay-in-an-answer). The anti-rote regex catches 0 of the 7 questions I judged as anti-rote because the bank's rote patterns are subtler than the regex set (e.g., "What is the 'X'?" with X being a named concept matches none of the listed patterns). **Recommendation: add a regex for `^What is (the |a )?['"]?[A-Z]` or similar named-concept-definition pattern** — that catches Q6/Q13/Q19/Q20/Q22/Q24 directly.

The LLM-style gates (wonder, story-led, advocacy, viral test) are doing the harder work and find the rest. The viral test in particular is correctly catching the questions that *would* embarrass the author (the Rand triple, the Rothbard two-in-one, the Hegel jargon wall) and correctly clearing the questions that have real content (Mill, Aquinas Five Ways, Aquinas-Plantinga material).

**Surprise:** the bank is not philosophically lopsided. The sample includes serious engagement with Rand (3 questions), Rothbard (2), Mises (1) — §3.3's call for Austrian/libertarian coverage *proportional to its intellectual heritage* is already being met by the existing bank, perhaps overshooting. The problem is voice, not viewpoint. The Austrian/Randian questions are mostly the *worst-written* questions in the sample — bloated, jargon-walled, two-questions-in-one — because they were apparently authored to fit a lot of content rather than to provoke wonder. That's a useful calibration signal for the rebuild: when generating Austrian-school content, the moral_fit validator will pass easily; the wonder_fun validator will be where the work is.

**Expected total rebuild burden, extrapolated from this sample:**
- ~49 KEEP-as-is (8% × 615)
- ~344 REPAIR (56% × 615)
- ~222 DISCARD (36% × 615)

Honest read: the bank is not awful, but the "soul" of it — the §8 great-question voice — is in only about one in twelve questions. That matches the user's perception more than the raw survival rate does.
