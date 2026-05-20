# PHILOSOPHY Bank — Full Audit Review (2026-05-19)

**Bank**: `data/questions/philosophy.json`
**Dropped**: `data/questions/dropped/philosophy.json`

## Verdict

**PASS** — all gates clean (1139 KEEP / 0 REPAIR / 0 DISCARD), every tier ≥ 200,
598 pytest pass, fallacies heavily reinforced at every tier, topic coverage
satisfies the ≥2 per topic at T2-T4 rule.

## Final tier shape

| Tier | n before | n after | FK median | FK max | net change |
|---|---:|---:|---:|---:|---:|
| T1 | 178 | 200 | 2.34 | 6.58 | +22 |
| T2 | 90 | 200 | 4.02 | 7.77 | +110 |
| T3 | 234 | 234 | 5.87 | 8.25 | 0 |
| T4 | 297 | 297 | 7.19 | 9.62 | 0 |
| T5 | 180 | 208 | 8.76 | 9.97 | −31 + 59 = +28 |
| **Total** | **979** | **1139** | | | **+160** |

T1 median FK 2.34 (5th-grade target ≤ 5). T5 median FK 8.76 with max 9.97
(target ceiling 10). Every tier sits well inside its grade window.

## What I did

### 1. Cleaned weird metadata (51 questions)

The bank had a non-standard `topic_cell: "logic_fallacies_debate_skills"`
field on 51 fallacy questions. No other subject bank uses this key, no
loader reads it, no gate checks it. **Stripped.**

### 2. Dropped 31 over-cap T5 questions

TIER_CAPS.md sets a hard ceiling at FK > 10 → drop. I scanned every
question with the canonical FK formula and moved 31 T5 questions to
`dropped/philosophy.json` with `_drop_reason: "fk>10 (audit 2026-05-19)"`.

The highest-FK examples:

| FK | Tier | Question (preview) |
|---:|---|---|
| 12.11 | T5 | Equivocation slides between two senses of a word inside one argument… |
| 11.71 | T5 | Al-Farabi proposed an ideal city in his Mabadi Ara Ahl al-Madina al-Fadila… |
| 11.36 | T5 | Kierkegaard published most of his major works under invented names… |
| 11.23 | T5 | All these philosophers — Socrates, Plato, Confucius, Buddha, Marcus Aurelius… |
| 11.13 | T5 | Montesquieu argued, against pure theorists, that republican government required small states… |

All were intellectually serious (none were rote), but their reading
difficulty made them inaccessible to a 9-10th-grade reader given a quiz
timer. They live in `dropped/` as good source material for future
generations.

### 3. Replaced one shallow-rote question

The single question matching a definition-of-X pattern:

- `"What does the word 'evidence' mean?"` →
  replaced with a scene-led version where a kid (Maya) claims she saw a
  bear and her brother asks how she KNOWS — forcing the reader to USE
  the concept of evidence.

### 4. Added +22 new T1 (5th-grade) questions

Mix:
- **10 fallacy recognition** — ad hominem (Sara's bedtime), straw man
  (Tom on walking), false dilemma (spinach OR love), bandwagon
  (everyone's shoes), tu quoque (Ben on sugar), post-hoc/correlation
  (Coach on 5am), equivocation (yummy=healthy), appeal to authority
  (famous actor), internet-truth, no true Scotsman (Sox fan dad).
- **6 ethics edges** — generosity with bounds (one cookie of two);
  honesty about a win (small other team); secrets that should be kept
  (moving); cheating on a no-grade quiz; promise vs. fun party; movie
  without sick friend.
- **4 medieval/modern via scenes** — Augustine pear theft, Aquinas on
  learning by seeing, Descartes dream-doubt, Locke's three (life,
  liberty, property). Closes the T1=0 medieval gap.
- **2 mind/identity** — Ship of Theseus (mom's car), personal identity
  over time (baby photo).

All FK ≤ 4.53.

### 5. Added +110 new T2 (6th-grade) questions

This was the biggest lift. Mix:
- **40 fallacies** at T2 — closes the gap from 3 → 33 fallacy
  questions at T2. Covers: ad hominem, straw man, slippery slope,
  false dilemma, bandwagon, appeal to authority, tu quoque, hasty
  generalization, genetic fallacy, red herring, appeal to nature,
  sunk cost, appeal to emotion, begging the question, equivocation,
  loaded question, appeal to fear, black-and-white thinking,
  affirming the consequent, argument from silence, composition/
  division, burden-of-proof shift, appeal to ignorance, false cause
  (rooster), tu quoque (named), causation vs. correlation.
- **10 ethics/virtue** — Golden Rule context-sensitivity, virtue vs.
  rule, honesty about helping, promise to self (Kant), lying for a
  friend, fairness of process vs. result, forgiveness as process,
  courage vs. recklessness (Aristotle's mean), victimless cheating,
  hard cases with two real harms.
- **10 ancient** — Socrates' examined life, Plato's cave, philosopher
  king, Aristotle's eudaimonia, Aristotle's golden mean, Stoics on
  control (Epictetus), Marcus Aurelius's notes, Cicero on duty,
  Diogenes the Cynic, Epicurus on friends.
- **10 medieval** — Augustine on love, Augustine on time, Anselm's
  ontological argument, Aquinas's five ways, Aquinas's natural law,
  Abelard's Sic et Non, Ockham's razor, Maimonides on negative
  theology, Boethius's wheel of fortune, Avicenna's floating man.
- **15 modern** — Descartes' method of doubt, Spinoza's one substance,
  Leibniz's best world, Locke's blank slate, Hume on is/ought, Hume
  on induction, Kant's categorical imperative, Kant on persons as
  ends, Hobbes' state of nature, Mill's harm principle, Hegel's
  dialectic, Nietzsche on master/slave morality, Schopenhauer on
  will, Marx on alienation, Kierkegaard on faith.
- **6 American** — Jefferson on self-evident truths, Emerson on
  self-reliance, Thoreau on civil disobedience, William James on
  pragmatic truth, Dewey on learning by doing, Frederick Douglass on
  knowledge.
- **6 Eastern** — Confucius's golden rule (negative form),
  Confucius on filial piety, Lao Tzu on water, Lao Tzu on wu wei,
  Mencius on the child at the well, Buddha's four sights.
- **7 mind/identity** — free will (compatibilism), personal identity
  over time, other minds, mind-body (hard problem), memory as
  identity, animal minds, dreaming and reality.
- **6 epistemology** — justified true belief, testimony, doubt and
  certainty, evidence vs. proof, healthy skepticism, confirmation bias.

All FK ≤ 5.42 (well within the T2 ≤ 6 cap).

### 6. Added +59 new T5 (9-10th grade) questions

Target was +51 to reach 200, but I built +59 to give T5 some headroom
(T5 = 208 now). Mix:
- **10 fallacies at depth** — poisoning the well, reductio by
  association, confounding variables, Bulverism (C.S. Lewis),
  Galileo gambit, equivocation in legal reasoning, survivorship
  bias, tu quoque valid uses, begging the question vs. circularity
  (Aristotle), motte-and-bailey (Shackel).
- **10 modern philosophy depth** — Kant's transcendental idealism,
  Mill on higher pleasures, Hegel's objective freedom (Sittlichkeit),
  Nietzsche's death of God as crisis, Schopenhauer on the Will,
  Marx's commodity fetish, Kierkegaard's three stages, Hume's
  compatibilism vs. Kant, Leibniz's pre-established harmony,
  Spinoza's substance.
- **8 phil of mind / identity** — Chalmers' hard problem, Searle's
  Chinese Room, Parfit on personal identity, Kripke's rigid
  designators, Block's access/phenomenal, functionalism and absent
  qualia, Strawson's reactive attitudes, Wittgenstein's private
  language.
- **8 political philosophy** — Burke's Reflections, Hayek's knowledge
  problem, Sowell's two visions, Rawls's veil of ignorance, Nozick's
  Wilt Chamberlain, Scruton's oikophilia, Coleman Hughes on color-
  blindness, Tocqueville on soft despotism. This bloc steelmans the
  classical-liberal-traditionalist tradition the user emphasized.
- **7 ancient/medieval depth** — Aristotle on phronesis, Plato's Good
  beyond being, Augustine on evil as privation, Aquinas on analogy,
  Anselm's Cur Deus Homo, Plotinus on emanation, Maimonides on the
  via negativa.
- **6 epistemology depth** — Bayesian priors, Zagzebski's virtue
  epistemology, Hardwig on epistemic dependence, Goldman's
  reliabilism and the generality problem, Plantinga's Reformed
  Epistemology, closure principles.
- **5 phil of religion** — Plantinga's free will defense, divine
  simplicity, Rowe's evidential problem of evil, Pascal's wager and
  many-gods, Anselm vs. Gaunilo.
- **5 Eastern depth** — Mencius vs. Xunzi on human nature,
  Nagarjuna's Madhyamaka, Confucius on rectification of names,
  Zhuangzi's butterfly dream, Lao Tzu on reversal.

All FK ≤ 9.97 (under the T5 ≤ 10 cap).

## Final topic coverage

| topic | total | T1 | T2 | T3 | T4 | T5 |
|---|---:|---:|---:|---:|---:|---:|
| logic_fallacies | 105 | 21 | 33 | 12 | 14 | 25 |
| epistemology | 117 | 8 | 26 | 21 | 33 | 29 |
| metaphysics | 230 | 18 | 27 | 49 | 76 | 60 |
| ethics (narrow keys) | 86 | 10 | 16 | 21 | 24 | 15 |
| aesthetics | 284 | 37 | 42 | 57 | 89 | 59 |
| political | 46 | 2 | 4 | 13 | 15 | 12 |
| mind | 122 | 9 | 16 | 25 | 49 | 23 |
| religion | 236 | 18 | 28 | 58 | 74 | 58 |
| ancient | 165 | 20 | 29 | 41 | 55 | 20 |
| medieval | 72 | 2 | 16 | 19 | 17 | 18 |
| modern | 281 | 10 | 36 | 82 | 93 | 60 |
| american | 77 | 1 | 9 | 19 | 19 | 29 |
| eastern | 72 | 6 | 11 | 14 | 32 | 9 |

(The "ethics narrow keys" row counts only virtue/justice/utilitarian/
deontology-style words — a wider Boolean over Golden Rule, fairness,
moral, duty, rights returns 441 hits including many T1-T2 scene-led
questions. Either way the topic is covered.)

**Coverage check**: every topic with ≥3 hits in the bank has ≥2
representatives at every T2-T4 tier. Zero violations.

### Fallacy emphasis verified

Per user direction (fallacies = core content at every tier), every tier
now carries substantial fallacy presence:

- T1: 21 fallacy scenes (was 14)
- T2: 33 fallacy scenes (was 3) — biggest gain
- T3: 12 fallacy questions
- T4: 14 fallacy questions
- T5: 25 fallacy questions (was 16, +10 from this audit)

The named fallacies covered across the bank now include: ad hominem,
straw man, slippery slope, false dilemma, bandwagon, appeal to
authority, appeal to popularity, appeal to emotion, appeal to fear,
appeal to nature, appeal to ignorance, post hoc / false cause,
correlation vs. causation, hasty generalization, no true Scotsman,
equivocation, begging the question, red herring, tu quoque, genetic
fallacy, sunk cost, loaded question, black-and-white thinking, affirming
the consequent, argument from silence, composition/division, burden of
proof shifting, poisoning the well, reductio by association, Bulverism,
Galileo gambit, survivorship bias, motte-and-bailey.

### Stance verification

- **Logical fallacies**: heavy emphasis at every tier ✓
- **Western tradition gets top billing**: Ancient (165) + Medieval (72)
  + Modern (281) + American (77) = 595 Western-named-thinker questions.
  Eastern (72) is covered seriously but is not the spine. ✓
- **Identity-politics critics**: Sowell (Conflict of Visions),
  Hayek (knowledge problem), Burke (Reflections), Scruton (oikophilia),
  Coleman Hughes (End of Race Politics), Aristotle (virtue ethics) all
  steelmanned at T5. ✓
- **Classical-liberal-traditionalist tradition**: Locke's life-liberty-
  property; Mill's harm principle; Jefferson's self-evident truths;
  Emerson on self-reliance; Tocqueville on soft despotism. Natural
  rights, rule of law, virtue ethics, religious heritage of moral
  reasoning all present and serious. ✓

## Pipeline outputs

- `py -m tools.quizgen validate --subject philosophy` → **1139/1139
  KEEP, 0 REPAIR, 0 DISCARD**
- `py -m tools.quizgen calibrate --subject philosophy --sample 100
  --seed 20260519` → 100 KEEP (100%), 0 REPAIR, 0 DISCARD
- `pytest -q` → **598 passed in 61.63s**

## What I did NOT touch

- T3 (234) and T4 (297) already ≥ 200 and showed no rote-pattern
  hits, no FK overshoots, and strong topic coverage. Left as-is per
  "no delete-to-rebalance" rule.
- Existing T5 questions under FK 10 were preserved.
- The bank's substantive style (named thinkers + their actual moves,
  not generic philosophy trivia) was preserved and extended.

## Drops summary

`data/questions/dropped/philosophy.json` now contains 314 entries:
- 81 from prior `fk>10` audits
- 202 from prior `jargon>=90` audits
- 31 new `fk>10 (audit 2026-05-19)` drops from this run

None of these enter the active quiz pool. They are preserved as
source material for future generations or for re-tiering should the
cap formula change.

## Scratch scripts (gitignored)

Under `tools/quizgen/scratch/`:
- `_philosophy_audit_helpers.py` — q() guard + load/save helpers
- `_philosophy_audit_step1.py` — strip topic_cell, drop FK>10, fix rote
- `_philosophy_audit_t1_build.py` — +22 T1
- `_philosophy_audit_t2_build_p1.py` — +34 T2 (fallacies + ethics)
- `_philosophy_audit_t2_build_p2.py` — +76 T2 (everything else)
- `_philosophy_audit_t5_build.py` — +59 T5

Each script enforces parity, budget, anti-rote, and FK at construction
time via the q() helper. Issues are reported and the build aborts
rather than saving broken content.
