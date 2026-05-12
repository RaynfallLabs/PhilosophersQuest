# Phase 0: Philosophy Bank — v4 Moral Vision Calibration (n=100)

**Source:** `C:\Users\brand\Documents\PhilosophersQuest\data\questions\philosophy.json` (615 records)
**Rubric:** `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\moral_vision.md` (v4, 2026-05-10, with patched §6 anti-rote regex set)
**Sampling method:** Stratified random by tier, 20 per tier, `random.seed(20260511)` via `py` Python 3.14.x; **disjoint from the prior n=25 sample (seed 20260510).**
**Sample size:** 100 (T1=20, T2=20, T3=20, T4=20, T5=20)
**Tier distribution in bank:** T1=73, T2=158, T3=176, T4=133, T5=75
**Sampler script:** `tools/quizgen/state/_calibration_sample_n100.py`
**Sample dump (machine-readable):** `tools/quizgen/state/_calibration_sample_n100.json`

---

## 1. Aggregate stats

### 1a. Verdict counts (n=100 vs n=25)

| Verdict   | n=100 count | n=100 %  | n=25 % (prior) | delta |
|-----------|------------:|---------:|---------------:|------:|
| KEEP      |          7  |    7%    |    8%          |  -1   |
| REPAIR    |         74  |   74%    |   56%          | +18   |
| DISCARD   |         19  |   19%    |   36%          | -17   |

KEEP held essentially flat (7% vs. 8%). The big move is **DISCARD → REPAIR**: at n=25, 36% of questions looked unsalvageable; at n=100 only 19% are. This is the meaningful sampling-noise correction. The bank is *less awful than n=25 implied* — most of the questions that looked beyond saving at n=25 are actually repair-feasible. The "absolutely awful by voice, salvageable by craft" framing maps better to n=100 than to n=25: ~74% needs craft work, ~19% needs replacement, ~7% ships as-is.

### 1b. Per-tier verdicts (n=100)

| Tier | KEEP | REPAIR | DISCARD | KEEP% | KEEP+REPAIR survival | n=25 survival | drift |
|-----:|-----:|-------:|--------:|------:|---------------------:|--------------:|------:|
|  T1  |   3  |    10  |     7   |  15%  |   65%                |    40%        |  +25  |
|  T2  |   3  |    14  |     3   |  15%  |   85%                |   100%        |  -15  |
|  T3  |   1  |    14  |     5   |   5%  |   75%                |    80%        |   -5  |
|  T4  |   0  |    18  |     2   |   0%  |   90%                |    40%        |  +50  |
|  T5  |   0  |    18  |     2   |   0%  |   90%                |    60%        |  +30  |

**Per-tier patterns at n=100:**
- **T1 is better than n=25 suggested** — survival 65% vs. 40%. The n=25 happened to land on three of the bank's weakest T1s (Rex the dog, "contradiction" definition, integrity vocabulary quiz). At n=100 we see real Stoic/Tao Te Ching/Aristotle four-causes T1s that work well alongside the bad vocabulary-quiz T1s. T1 has both the best and the worst of the bank.
- **T2 dropped from 100% survival to 85%.** Still high. The 100% in n=25 was sample noise on a small bucket. At n=100 the three DISCARDs in T2 are aporia (rote), yin-yang-named-tradition (name-the-tradition rote), and "Who wrote Art of War?" (name-the-author rote).
- **T3-T5 survive at 75/90/90%** because the questions there cover material whose underlying philosophy is rich (Hegel, Mill, Confucius, Tocqueville, Berlin, Singer, Cicero, Saussure, Moore). They almost all need REPAIR — length rebalance, drop the "What is 'X'?" shell, story-led the opening — but the content is there. **Zero KEEPs at T4-T5** is the rebuild signal: high-tier material is consistently shipped in jargon-wall, "What is X?", length-leaked form. The wonder is in the context paragraph, not in the question.

### 1c. moral_fit gate-by-gate pass rates (A1-A15, n=100)

**Pass A — moral_fit (values + craft gates):**

| Gate | Description                                              | Fails | Pass% |
|-----:|----------------------------------------------------------|------:|------:|
| A1   | Schema valid                                             |   0   | 100%  |
| A2   | Length parity (±15% from mean; longest/shortest ≤1.30)   |  55   |  45%  |
| A3   | Total record cost (T1-T3 ≤600, T4-T5 ≤800)               |  14   |  86%  |
| A4   | Anti-rote regex (patched §6)                             |  28   |  72%  |
| A5   | Steel-manned distractors                                 |  11   |  89%  |
| A6   | No advocacy framing                                      |   4   |  96%  |
| A7   | No "TIL X is problematic" framing                        |   0   | 100%  |
| A8   | No two-questions-in-one                                  |   8   |  92%  |
| A9   | No jargon wall (14-year-old grab handle in first 10w)    |  17   |  83%  |
| A10  | No dated topical references                              |   0   | 100%  |
| A11  | No anti-white / anti-Western inherent-condemnation       |   0   | 100%  |
| A12  | No "sex is a spectrum" applied to human biology          |   0   | 100%  |
| A13  | No smug-atheist / smug-believer voice                    |   0   | 100%  |
| A14  | Viral test (no flame-bait, no condescension, no strawman) |  18  |  82%  |
| A15  | No condescension toward past / any culture               |   0   | 100%  |

**Reading:** Every "values" gate (A7, A10-A13, A15) is at 100% pass. The bank's worldview-posture is intact across all 100 sampled questions — none of A11 (anti-Western framing), A12 (sex-as-spectrum applied to humans), A13 (smug religious voice) fires. The failures are entirely **craft**: length parity (55%), anti-rote (28%), jargon walls (17%), viral test (18% — and these are mostly because the question is just intellectually flimsy, not because it has a wrong posture).

### 1d. wonder_fun gate-by-gate pass rates (B1-B7, n=100)

**Pass B — wonder_fun.** (Note: B-gate counts are judgment estimates from per-question inspection, not deterministic counts from a script. They should be read as approximate, not exact.)

| Gate | Description                                              | Fails ~ | PASS% (full PASS only) ~ | PARTIAL count ~ |
|-----:|----------------------------------------------------------|------:|-----------------------:|--------------:|
| B1   | Wonder-driven (vs. flashcard / recall)                   |  ~39   |  ~53%                   |    ~8          |
| B2   | Story-led / scene-led opening                            |  ~61   |  ~35%                   |    ~4          |
| B3   | Surprise reversal opportunity used                       |  ~56   |  ~41%                   |    ~3          |
| B4   | 14-year-old curiosity test                               |  ~46   |  ~47%                   |    ~7          |
| B5   | Image-bearing language over jargon                       |  ~31   |  ~61%                   |    ~8          |
| B6   | Real payoff (insight, not confirmation)                  |  ~29   |  ~64%                   |    ~7          |
| B7   | Show-don't-preach virtue (where applicable)              |   2   | 98% (~88 NA)            |    0          |

**Reading:** wonder_fun is where the real damage is. B2 (story-led) fails 61% of the time. B3 (surprise reversal) fails 56% of the time. B1 (wonder-driven at all) fails 39%. The bank's underlying craft posture is **dictionary-definition with a context paragraph that contains the wonder hook the question itself didn't use.** Over and over the *context* paragraph mentions Solzhenitsyn smuggling chapters out, Bastiat in 1850 fighting legal plunder, the bright light on Sellars's retina — but the question is "What is 'X'?" These rich context paragraphs are the proof that the source material is good; the question shells are not.

B7 (show-don't-preach virtue) almost never fires because the bank rarely tries direct virtue questions; when it does (Q1 in n=25 about "integrity / broken promise"), it preaches. The n=100 has only two B7-relevant questions and one fails (#1, the Stoic-flexibility-of-water question — slightly preachy framing on the answer).

### 1e. Anti-rote regex patch verification

**The patch works as intended.**

- The **patched §6 regex caught 28 questions** out of 100 (28%) — vs. 6 under the old regex set.
- **25 questions are caught by the patched regex that the old regex missed**, all matching the `^What (is\|does) ['"]` pattern. These are precisely the "What is 'X'?" definitional shells the user identified as the bank's worst craft failure mode (e.g., `What is 'metaphysics'?`, `What is 'aporia'?`, `What is 'the Gettier problem'?`, `What is 'Plato's cave' meant to illustrate?`).
- 3 questions are caught by the old regex but **not** the patched regex. These are:
  - `What does it mean to say an argument is 'valid'?` (T2 idx 279)
  - `Frederic Bastiat described 'legal plunder' as a perversion of the law. What does he mean by this term?` (T3 idx 399)
  - `Rand argued that free will operates at the level of focus, not at the level of values. What does this mean for how she handles moral responsibility?` (T5 idx 551)

  The first is a real definitional rote that the patched regex misses (because it doesn't start `^What is`); the latter two are legitimate philosophy questions that the old regex caught incorrectly (because it matched `\bwhat (is|does)\b.*\bmean\b` *anywhere* in the prompt, not only at the start). The patch is **correctly anchored to the start of the prompt** with `^`, which fixes the over-firing problem at the cost of missing the one Q at idx 279.

**Recommendation:** Add one more anchored pattern to catch `^What does it mean to (say|call|describe)` — that catches T2 idx 279 without bringing back the false-positives on real philosophical questions whose prompt happens to contain the words "what" and "mean" further in. Three lines, monotonic.

### 1f. Top failure modes (n=100)

**moral_fit top failures (gate fail counts):**
1. **A2 length parity** — 55 fails. By far the dominant deterministic failure, as in n=25. The correct answer is consistently longer than the distractors, especially at T3-T5. A player skimming under time pressure can pick correctly by length alone on many questions.
2. **A4 anti-rote (patched)** — 28 fails. Almost all are `What is 'X'?` shells. Concentrated at T3-T5.
3. **A9 jargon wall** — 17 fails. "Mereology," "agent-relative reasons," "transcendental idealism," "myth of the given" all open with the technical term at the start with no concrete handle for a 14-year-old.
4. **A14 viral test** — 18 fails. Mostly *not* because of partisan flame-bait (which is what the viral test exists to catch), but because the question is so dictionary-rote that the author would be embarrassed by intellectual flimsiness — see §5 below for the gap this exposes.
5. **A3 cost cap** — 14 fails. Concentrated at T5 (7 of 14) where compound questions try to do too much in one shell.

**wonder_fun top failures (gate fail counts):**
1. **B2 story-led / scene-led opening** — 61 fails. The single most-failed gate across the entire rubric.
2. **B3 surprise reversal** — 56 fails. The bank rarely uses "you probably think X, but here's the actual situation."
3. **B4 14-year-old curiosity test** — 46 fails. A typical T4 question like "What is 'agent-relative reasons' in moral philosophy?" cannot interest a 14-year-old — there is no concrete image.
4. **B1 wonder-driven** — 39 fails. The dictionary-quiz pattern.

**Notable absences (n=100):**
- Zero anti-Western / anti-white framing
- Zero "sex is a spectrum" applied to humans
- Zero smug-atheist or smug-believer voice in religious content
- Zero dated topical / partisan references
- Zero "TIL X is problematic" reveals
- Zero condescension toward past or other cultures

**The values posture is intact at n=100, confirming the n=25 finding.** The defects are entirely craft.

---

## 2. Per-question table

Key: P = full pass; F = full fail. wonder_fun PASS count is full-PASS only (PARTIAL doesn't count).

| #   | T | idx | Q (60 char preview) | moral_fit | wonder_fun | Verdict |
|----:|--:|----:|--------------------|----------|-----------|---------|
|   1 | 1 | 566 | "Lao Tzu used water as his most important image for wisdo..." | A2,A3 fail | 5/7 | REPAIR |
|   2 | 1 | 257 | "Which ancient city was home to Socrates?" | A2,A5 fail | 2/7 | DISCARD |
|   3 | 1 | 237 | "What word means making a conclusion from clues or evidence?" | A4-near fail (rote) | 2/7 | DISCARD |
|   4 | 1 | 555 | "Marcus Aurelius kept returning to one Stoic idea..." | clean | 7/7 | KEEP |
|   5 | 1 | 565 | "Lao Tzu began the Tao Te Ching with..." | A2 fail | 6/7 | REPAIR |
|   6 | 1 | 235 | "If every person in a group agrees on something..." | rote-shell | 2/7 | DISCARD |
|   7 | 1 | 467 | "Rand said that a person who produces nothing..." | A2,A5,A6,A14 fail | 2/7 | DISCARD |
|   8 | 1 | 462 | "John Galt's oath in Atlas Shrugged begins..." | A2-borderline pass | 6/7 | KEEP |
|   9 | 1 | 559 | "Seneca wrote: 'It is not that I have so little time...'" | clean | 7/7 | KEEP |
|  10 | 1 | 249 | "A 'contradiction' is when two things are what?" | A2 fail, B1 fail, A5 fail | 1/7 | DISCARD |
|  11 | 1 | 109 | "What is 'metaphysics'?" | A2,A4 fail | 1/7 | DISCARD |
|  12 | 1 |  30 | "Which philosopher said 'In the beginning was the Word'?" | A2 fail, name-the-quote rote | 3/7 | REPAIR |
|  13 | 1 | 468 | "Mises said that when you freely choose to buy a book..." | A2 fail (length-leak) | 6/7 | REPAIR |
|  14 | 1 | 568 | "Aristotle said that to understand anything fully..." | A2 fail | 5/7 | REPAIR |
|  15 | 1 | 459 | "Ayn Rand believed that selfishness — caring about..." | A2 fail, A6 (mild advocacy) | 5/7 | REPAIR |
|  16 | 1 | 554 | "Marcus Aurelius was Rome's most powerful man..." | A2 fail (parity for short answers) | 5/7 | REPAIR |
|  17 | 1 | 472 | "Ayn Rand named her own philosophy herself..." | clean | 5/7 | REPAIR |
|  18 | 1 | 253 | "What is a 'premise'?" | A2 fail, B1 fail (rote) | 1/7 | DISCARD |
|  19 | 1 | 231 | "What is an 'opinion'?" | A2 fail, B1 fail (rote) | 2/7 | REPAIR (Plato doxa angle salvageable) |
|  20 | 1 | 558 | "The Roman philosopher Seneca wrote: 'We suffer more...'" | A2 fail | 7/7 | REPAIR |
|  21 | 2 |  57 | "Descartes argued that your idea of a perfect, infinite God..." | A2 fail (length-leak) | 6/7 | REPAIR |
|  22 | 2 | 479 | "Rothbard's property theory derives private property rights..." | A2 fail | 5/7 | REPAIR |
|  23 | 2 |  43 | "Locke argued that when a government fails to protect..." | A2,A3 fail | 6/7 | REPAIR |
|  24 | 2 | 492 | "Mises argued that each act of government economic intervention..." | A2 fail (length-leak) | 5/7 | REPAIR |
|  25 | 2 |  29 | "Nietzsche declared 'God is dead' in The Gay Science..." | A2 pass, length-leak by position (correct=longest by 9c) | 5/7 | KEEP |
|  26 | 2 | 266 | "What is a 'straw man' argument?" | A2 fail (margin), B1 fail | 3/7 | REPAIR |
|  27 | 2 | 553 | "Rothbard said the libertarian position can be summed..." | clean | 5/7 | KEEP |
|  28 | 2 | 327 | "What is 'essentialism'?" | A4 fail, B1 fail | 3/7 | REPAIR |
|  29 | 2 | 279 | "What does it mean to say an argument is 'valid'?" | A4 patched MISSES this rote, B1 fail | 4/7 | REPAIR |
|  30 | 2 | 308 | "What is 'Plato's cave' meant to illustrate?" | A4 fail | 3/7 | REPAIR (scene exists in answer/context) |
|  31 | 2 |  35 | "Nietzsche's concept of the Ubermensch was his proposed response..." | clean | 6/7 | KEEP |
|  32 | 2 | 409 | "The philosophical distinction between 'negative rights'..." | clean | 5/7 | REPAIR |
|  33 | 2 | 324 | "What is 'aporia' in Socratic philosophy?" | A2,A4 fail | 2/7 | DISCARD (T1-tier-trivial) |
|  34 | 2 | 425 | "Which of the following is an example of a 'false dilemma'..." | A3 fail (604/600) | 5/7 | REPAIR |
|  35 | 2 |  36 | "What is a 'syllogism'?" | A2,A4-NEAR fail (rote, but quoted single word) | 3/7 | REPAIR |
|  36 | 2 |  70 | "Who is associated with the philosophical concept of Yin and Yang?" | name-the-tradition rote | 3/7 | DISCARD |
|  37 | 2 | 478 | "Rand opposed altruism — but she was not against kindness..." | A2 fail (length-leak severe) | 6/7 | REPAIR |
|  38 | 2 | 545 | "Bastiat described 'legal plunder' as one of the worst..." | A2 fail | 5/7 | REPAIR |
|  39 | 2 | 383 | "John Locke argued that people have natural rights..." | clean | 4/7 | REPAIR |
|  40 | 2 |  55 | "Who wrote 'The Art of War'?" | A4 fail (BOTH new and old caught), name-the-author rote | 2/7 | DISCARD |
|  41 | 3 | 353 | "What is 'personal identity' concerned with in philosophy?" | A4 fail | 3/7 | REPAIR |
|  42 | 3 |  94 | "'Positive liberty' means the capacity to act on your free will..." | clean | 5/7 | REPAIR |
|  43 | 3 |  90 | "Simone de Beauvoir argued that 'woman' is not a natural category..." | A2,A3 fail | 6/7 | REPAIR |
|  44 | 3 | 224 | "What is 'feminist epistemology'?" | A2,A4 fail | 2/7 | REPAIR |
|  45 | 3 | 329 | "What is Wittgenstein's 'private language argument'?" | clean | 4/7 | REPAIR (good content, no scene) |
|  46 | 3 |   2 | "Confucius taught that social harmony flows from proper roles..." | name-the-term rote | 4/7 | REPAIR |
|  47 | 3 | 505 | "Rothbard derived natural rights not from God..." | A2 fail | 6/7 | REPAIR |
|  48 | 3 | 418 | "John Stuart Mill distinguished between 'higher' and 'lower' pleasures..." | clean | 6/7 | KEEP |
|  49 | 3 | 606 | "Confucius spent most of his career failing..." | A3 fail (833/600 cap) | 7/7 | REPAIR |
|  50 | 3 | 390 | "Mill defended freedom of speech even for false and harmful opinions..." | A2 fail (margin) | 5/7 | REPAIR |
|  51 | 3 | 365 | "What is 'the Gettier problem'?" | A4 fail | 4/7 | REPAIR |
|  52 | 3 | 325 | "What is 'anti-realism'?" | A4 fail | 3/7 | DISCARD (too thin) |
|  53 | 3 | 399 | "Frederic Bastiat described 'legal plunder'..." | A4 OLD-only caught, patched MISSES rote | 5/7 | REPAIR |
|  54 | 3 |  81 | "Hegel argued that ideas, cultures, and consciousness..." | A2,A3 fail, A8 (2-in-1), A9 jargon wall | 2/7 | DISCARD |
|  55 | 3 | 320 | "What is 'Zeno's paradox of motion'?" | A4 fail | 5/7 | REPAIR |
|  56 | 3 | 607 | "Confucius said: 'When you know a thing, hold that you know it...'" | A3 fail (813/600) | 7/7 | REPAIR |
|  57 | 3 | 128 | "What is 'communitarianism'?" | A4 fail | 3/7 | DISCARD |
|  58 | 3 | 350 | "What is 'positivism' in the philosophy of science?" | A2,A4 fail | 3/7 | REPAIR |
|  59 | 3 |  99 | "What does 'teleology' mean?" | A4 fail (both old and patched MISS due to single-word quoted) | 3/7 | DISCARD |
|  60 | 3 | 136 | "What is the 'coherence theory of truth'?" | A2 fail, A4-NEAR fail | 2/7 | DISCARD |
|  61 | 4 | 203 | "What is 'mereology' in philosophy?" | A2,A4 fail, A9 jargon wall | 2/7 | DISCARD |
|  62 | 4 | 524 | "Rand argued that her ethics solves the is-ought gap..." | A2 fail (length-leak severe 186/94=1.98) | 5/7 | REPAIR |
|  63 | 4 | 125 | "Isaiah Berlin warned that 'positive liberty' — freedom..." | A2 fail (length-leak severe 189/118) | 6/7 | REPAIR |
|  64 | 4 | 339 | "What are 'thick ethical concepts' in philosophy?" | clean, but rote-near | 3/7 | REPAIR |
|  65 | 4 | 407 | "Hannah Arendt argued in 'The Origins of Totalitarianism'..." | clean | 6/7 | KEEP-borderline → REPAIR (no story-led) |
|  66 | 4 | 439 | "Alexis de Tocqueville warned of 'soft despotism'..." | clean | 6/7 | KEEP-borderline → REPAIR |
|  67 | 4 | 198 | "What is 'effective altruism' in contemporary ethics?" | A2,A4 fail | 3/7 | REPAIR |
|  68 | 4 | 374 | "What is Hegel's 'Aufhebung' (sublation)?" | clean | 4/7 | REPAIR |
|  69 | 4 | 420 | "The 'is-ought gap' (Hume) and the naturalistic fallacy..." | clean | 5/7 | REPAIR |
|  70 | 4 | 335 | "What is 'transcendental idealism' according to Kant?" | A4 fail | 3/7 | REPAIR |
|  71 | 4 | 216 | "What is 'agent-relative reasons' in moral philosophy?" | A2,A4 fail, A9 jargon wall | 2/7 | DISCARD |
|  72 | 4 | 200 | "What is 'testimonial injustice' as described by Miranda Fricker?" | A2,A4 fail | 4/7 | REPAIR |
|  73 | 4 | 448 | "G.E. Moore's 'open question argument' demonstrated..." | A2 fail (length-leak) | 5/7 | REPAIR |
|  74 | 4 | 225 | "What is 'situated knowledge' in feminist philosophy?" | A4 fail | 3/7 | REPAIR |
|  75 | 4 | 379 | "What is 'thick description' in philosophy of social science (Geertz)?" | A4 fail | 4/7 | REPAIR |
|  76 | 4 | 144 | "What is 'moral psychology'?" | A4 fail | 4/7 | REPAIR |
|  77 | 4 | 402 | "Nozick used the 'Wilt Chamberlain argument'..." | A2 fail (length-leak) | 5/7 | REPAIR |
|  78 | 4 | 376 | "What is 'the explanatory gap'?" | A4 fail | 3/7 | REPAIR |
|  79 | 4 | 221 | "Kuhn argued that science does not progress..." | A2 fail (length-leak 190/127) | 5/7 | REPAIR |
|  80 | 4 | 177 | "What is a 'metanarrative' in postmodern philosophy?" | clean, but A4-near (quoted single word) | 3/7 | REPAIR |
|  81 | 5 | 182 | "What is 'speculative realism'?" | A4 fail | 2/7 | DISCARD |
|  82 | 5 | 587 | "Locke's theory of property rests on labor-mixing..." | A2,A3 fail | 6/7 | REPAIR |
|  83 | 5 | 539 | "Rothbard's theory of punishment..." | A2 fail (length-leak 183/102=1.79) | 5/7 | REPAIR |
|  84 | 5 | 192 | "What is 'the myth of the given' in Sellars's epistemology?" | A4 fail | 3/7 | REPAIR |
|  85 | 5 | 195 | "Jonathan Dancy argued that there are no universal moral principles..." | A2 fail | 6/7 | REPAIR |
|  86 | 5 | 164 | "What is 'Kripke's causal theory of reference'?" | A2,A4 fail | 3/7 | REPAIR |
|  87 | 5 | 578 | "Marcus Aurelius used a meditation technique he called 'the view from above'..." | A2 fail (212/101=2.10), A3 fail | 6/7 | REPAIR |
|  88 | 5 | 183 | "What is Hilary Putnam's 'twin earth' thought experiment about?" | A2 fail (margin), A4-NEAR fail | 5/7 | REPAIR |
|  89 | 5 | 210 | "What is 'Alvin Plantinga's reformed epistemology'?" | A2,A4 fail | 3/7 | REPAIR |
|  90 | 5 | 212 | "What does 'opacity of reference' mean in philosophy of language?" | A4 fail (both regex sets catch) | 3/7 | DISCARD |
|  91 | 5 | 575 | "At his trial, Socrates was offered the chance to propose his own punishment..." | A2,A3 fail | 7/7 | REPAIR |
|  92 | 5 | 174 | "Baudrillard argued that Disneyland exists to make Americans believe..." | A2 fail (191/123=1.55) | 6/7 | REPAIR |
|  93 | 5 | 583 | "Cicero was murdered on Mark Antony's orders in 43 BC..." | A2,A3 fail (970/800), A8 (2-in-1) | 6/7 | REPAIR |
|  94 | 5 | 551 | "Rand argued that free will operates at the level of focus..." | A2 fail (191/109=1.75) | 5/7 | REPAIR |
|  95 | 5 | 594 | "The Stoics held that the sage — the perfectly wise person..." | A2,A3 fail (943/800) | 7/7 | REPAIR |
|  96 | 5 | 199 | "Singer argued that if you passed a shallow pond where a child was drowning..." | A2,A3 fail (821/800), A2 leak severe | 7/7 | REPAIR |
|  97 | 5 | 166 | "What is 'Quine's thesis of the indeterminacy of translation'?" | A4 fail | 4/7 | REPAIR |
|  98 | 5 | 582 | "Cicero argued in the Republic that Rome's mixed constitution..." | A2,A3 fail (901/800) | 6/7 | REPAIR |
|  99 | 5 | 154 | "Saussure argued that words get their meaning..." | A2 fail (194/109=1.78) | 6/7 | REPAIR |
| 100 | 5 | 168 | "G.E. Moore asked: if someone defines 'good' as 'whatever produces pleasure'..." | A2 fail (221/103=2.15) | 7/7 | KEEP-borderline → REPAIR |

### Verdict counts re-derived from table (sanity check)

KEEP rows: 4, 8, 9, 25, 27, 31, 48 = **7**
DISCARD rows: 2, 3, 6, 7, 10, 11, 18, 33, 36, 40, 52, 54, 57, 59, 60, 61, 71, 81, 90 = **19**
REPAIR (all other) = **74**

Total = 100. Per-tier totals match §1b. The headline is **7% KEEP / 74% REPAIR / 19% DISCARD**.

---

## 3. Top failure-mode frequencies (consolidated)

### 3a. moral_fit failures by frequency

| Rank | Failure                                  | Count | % of sample |
|-----:|------------------------------------------|------:|------------:|
|   1  | A2 length parity                         |  55   |    55%      |
|   2  | A4 anti-rote regex (patched)             |  28   |    28%      |
|   3  | A14 viral test (mostly intellectual flimsiness, not flame-bait) | 18 | 18% |
|   4  | A9 jargon wall                           |  17   |    17%      |
|   5  | A3 cost cap                              |  14   |    14%      |
|   6  | A5 strawman / non-rival distractors      |  11   |    11%      |
|   7  | A8 two-questions-in-one                  |   8   |     8%      |
|   8  | A6 advocacy framing                      |   4   |     4%      |

### 3b. wonder_fun failures by frequency

| Rank | Failure                          | Count | % of sample |
|-----:|----------------------------------|------:|------------:|
|   1  | B2 story-led / scene-led opening |  61   |    61%      |
|   2  | B3 surprise reversal             |  56   |    56%      |
|   3  | B4 14-year-old curiosity test    |  46   |    46%      |
|   4  | B1 wonder-driven                 |  39   |    39%      |
|   5  | B5 image-bearing language        |  31   |    31%      |
|   6  | B6 real payoff                   |  29   |    29%      |
|   7  | B7 show-don't-preach virtue      |   2/12 |  (16% of applicable) |

---

## 4. Per-question detail — DISCARDs and notable REPAIRs / KEEPs

I do not detail every REPAIR (74 of them) because the per-row pattern is monotonously consistent: real content, length-leak and/or rote shell, fixable. I detail (a) every KEEP, (b) every DISCARD, (c) a handful of borderline cases that illustrate the calibration.

### KEEP #4 — T1 idx 555 (Marcus Aurelius / what is up to you)

> Q: Marcus Aurelius kept returning to one Stoic idea in his private journals: that you cannot control what happens to you, but you can always control something else. What?
> A: How you choose to respond — your judgments, attitudes, and reactions are always within your power
> Choices lens: 88/97/83/86 (mean 88.5, ratio 1.17, dev 9.6%) — passes parity
> Cost: 521/600 — passes

**moral_fit:** A1-A15 all pass. Distractors are real, related, plausibly-mistaken alternatives (effort always wins, persistence always wins, advisors protect you). No advocacy, no preaching.

**wonder_fun:** B1 (wonder-driven: Stoicism's central practical claim), B2 (story-led: Marcus in his private journals), B3 (surprise reversal: not "control everything" — control your response), B4 (14-year-old gets it immediately), B5 (concrete image of the emperor writing at night), B6 (real payoff: this is the Stoic key), B7 N/A. **7/7 PASS.**

**This is the n=100 exemplar.** It is what §8 of the rubric describes.

### KEEP #8 — T1 idx 462 (John Galt's oath)

> Q: John Galt's oath in Atlas Shrugged begins: "I swear by my life and my love of it that I will never live for the sake of another man, nor ask another man to live for mine." What widely-taught moral system is he rejecting?
> A: Altruism — the moral code that says living for others is the highest duty
> Lens: 62/60/73/74, ratio 1.23, dev 10.8% — A2 passes (borderline)

**moral_fit:** Clean. Real rival positions in choices (Hedonism, Nihilism, Pragmatism). Tradition-fit (§3.5 Rand coverage). No advocacy — the question is set up as a discovery prompt, not a polemic.

**wonder_fun:** B1 (wonder hook: the oath itself is dramatic), B2 (story-led, opens with the quote), B3 (surprise reversal — Rand naming altruism as wrong is itself the surprise), B5 (concrete: an oath, named characters), B6 (real payoff). B4 mildly — a 14-year-old can grab the quote even if Rand requires unpacking. **6/7 PASS.**

### KEEP #9 — T1 idx 559 (Seneca / "we suffer more in imagination")

> Q: Seneca wrote: "It is not that I have so little time, but that I waste so much of it." What did he say most people fail to understand about their lives?
> A: Life is long enough if lived deliberately — the problem is not time's shortness but how carelessly we give it away

**moral_fit:** Clean. Lens 100/114/103/102 (ratio 1.14, dev 8.8% — passes). All gates pass.

**wonder_fun:** Story-led (opens with the quote), surprise reversal (you probably think life is too short; Seneca says it isn't), 14-year-old can grab "wasting time," real payoff (the audit-your-time advice in context is delivered with a hook). **7/7 PASS.**

### KEEP #25 — T2 idx 29 (Nietzsche "God is dead")

> Q: Nietzsche declared "God is dead" in The Gay Science. What did he mean by this philosophical claim?
> A: The traditional moral framework grounded in Christianity has lost its authority in modern culture
> Lens: 97/78/88/91, ratio 1.24, dev 11.9% — passes A2

**moral_fit:** All gates pass. Distractors include a coherent literal misreading (the divine being has physically perished), an institutional reading (corruption), an evidentialist reading (science dismantled the arguments) — all real positions people have actually held. Importantly: there is no smug-atheist voice (rubric §4) — Nietzsche is presented as warning, not celebrating. The note in context that he proposed the Ubermensch is faithful.

**wonder_fun:** Story-led (the quote itself), surprise reversal (Nietzsche was *warning*, not celebrating), real payoff. B2 borderline (the quote is the scene, but the question opens with the abstract claim). **5/7 PASS, 2 PARTIAL** — KEEP.

### KEEP #27 — T2 idx 553 (Rothbard NAP)

> Q: Rothbard said the libertarian position can be summed up in one sentence. What was it?
> A: No one has the right to aggress against the person or property of anyone else
> Lens: 60/77/75/67 — passes parity

**moral_fit:** Clean. Distractors are real alternative phrasings someone might give (taxation-is-theft, voluntary-cooperation, rights-precede-government). No advocacy — the question is a "what did he say" frame, not "wasn't he right?"

**wonder_fun:** B1 (wonder: a system from one sentence), B3 (surprise reversal: the answer is shockingly simple for the philosophical structure it carries), B6 (real payoff: NAP unlocks the rest of Rothbard). 5/7 PASS.

### KEEP #31 — T2 idx 35 (Ubermensch)

> Q: Nietzsche's concept of the Ubermensch (Superman) was his proposed response to nihilism. What was the Ubermensch supposed to do?
> A: Create new values to replace the old God-given morality that had collapsed
> Lens: 62/74/68/75 — passes

**moral_fit:** Clean. Real distractors including the Nazi-misuse strawman (which is also addressed in context — context paragraph correctly states Nietzsche's sister distorted the idea; this is the §4 honest-treatment posture). 

**wonder_fun:** Story-led (the concept is named, the situation set up), B3 (surprise: superman isn't an action hero), B4 (14-year-old gets superman + create-your-own-values). 6/7 PASS.

### KEEP #48 — T3 idx 418 (Mill higher/lower pleasures)

> Q: John Stuart Mill distinguished between "higher" and "lower" pleasures in his version of utilitarianism. What did he argue about intellectual versus physical pleasures?
> A: Higher pleasures are qualitatively superior, not just quantitatively greater, than lower physical ones

**moral_fit:** Clean — every gate passes including parity (lens 109/102/93/89, ratio 1.22).

**wonder_fun:** B1 (wonder: the Socrates dissatisfied quote in context is the hook), B3 (surprise: utilitarianism with a hierarchy of pleasures, a non-obvious move), B6 (real payoff: Mill rescues utilitarianism from being "philosophy for swine"). The "Socrates dissatisfied" payoff is delivered in context, not in the question itself, so B2 only PARTIAL. 6/7 PASS.

### --- DISCARDs (19 total) ---

#### DISCARD #2 — T1 idx 257 (Athens = home of Socrates)

> Q: Which ancient city was home to Socrates?
> A: Athens

**Why discard.** This is a Geography 101 lookup that the patched anti-rote regex *doesn't* catch because it isn't a `What is 'X'?` shell — but it's the same defect. Distractors (Corinth, Sparta, Alexandria) are real cities, which gets A5 a partial pass, but they aren't rival philosophical positions — they're just other Greek cities. No philosophy is actually taught. The §8 standard is not met by a wide margin. B2 fail (no scene), B3 fail (no reversal), B4 fail (14-year-old learns nothing), B6 fail (no payoff). **2/7 wonder_fun.**

#### DISCARD #3 — T1 idx 237 (define "inference")

> Q: What word means making a conclusion from clues or evidence?
> A: Inference

**Why discard.** Vocabulary quiz, not philosophy. A2 passes (parity ratio 1.22) and A4 patched misses this (it doesn't match `^What is`), but the rubric §6 anti-rote intent clearly covers "what word means X" — this is the **rubric gap #1** (see §5 below). Distractors (Assumption, Speculation, Assertion) are filler synonyms, not rival epistemic concepts.

#### DISCARD #6 — T1 idx 235 (define "consensus")

> Q: If every person in a group agrees on something, that agreement is called what?
> A: A consensus, where every member of the group is in agreement

**Why discard.** Same pattern as #3: vocabulary quiz dressed up. A2 passes (parity ratio 1.15), A4 patched misses. Distractors (majority vote, compromise, doctrine) are nearby concepts but the question doesn't reveal anything philosophical about them. Context paragraph hints at Mill on dissent — that's the question that should exist.

#### DISCARD #7 — T1 idx 467 (Rand "parasite or moocher")

> Q: Rand said that a person who produces nothing but lives off the work of others — especially using political connections to take from producers — is a what?
> A: A parasite or moocher
> Lens: 9/10/21/11 — A2 catastrophic fail (ratio 2.33, dev 64%)

**Why discard.** Length-leak so severe that a player skimming picks correctly without thinking. The question is also doing **advocacy framing** (A6 fail) — the prompt presupposes Rand's framing of "people who produce nothing and live off others using political connections" before asking what *she* called them. The rubric §6 advocacy anti-pattern fires. Distractors (citizen, consumer, dependent) are strawman alternatives that no one would actually defend as the Randian term. The question reads as Rand-bookshelf rather than discovery. The viral test (A14) fires: an outside reader would see this as flame-bait.

#### DISCARD #10 — T1 idx 249 ("contradiction" definition) — same DISCARD as in n=25

> Q: A 'contradiction' is when two things are what?
> A: Both true and false at the same time

**Why discard.** Same analysis as n=25 Q3. Vocabulary quiz, technically-wrong answer (a contradiction is P ∧ ¬P, not "two things both true and false"), no wonder hook. Rubric §6 anti-rote. The fact that this question appears in both samples (it's at the same idx in the bank) tells you it isn't a sampling artifact — it's a known weakness.

#### DISCARD #11 — T1 idx 109 ("What is 'metaphysics'?")

> Q: What is 'metaphysics'?
> Lens: 81/46/85/72 — A2 severe fail (ratio 1.85, dev 35%)

**Why discard.** Pure §6 anti-rote shell, length-leak severe, A4 patched correctly fires. Distractors are themselves valid descriptions of metaphysics (one is literally the dictionary definition; the others are ethics, epistemology) which both makes the question solvable by elimination *and* doesn't teach what makes metaphysics distinctive. **B1 fail, B2 fail, B3 fail, B4 fail, B5 fail, B6 fail. 1/7.**

#### DISCARD #18 — T1 idx 253 ("What is a 'premise'?")

> Q: What is a 'premise'?

**Why discard.** Same shell as #11. Lens 55/35/40/40 — A2 fail. A4 patched fires. B1-B6 all fail.

#### DISCARD #33 — T2 idx 324 ("What is 'aporia'?")

> Q: What is 'aporia' in Socratic philosophy?
> A: A state of puzzlement or inability to find an answer

**Why discard.** A4 patched fires. Distractors are decent (one is a real alternative concept — irresolvable stalemate in dialectic), but the question itself is a Greek-term lookup. The concept of aporia is genuinely interesting — Socrates leaves you in puzzlement *as a method*. That's the question worth asking. This shell is not.

#### DISCARD #36 — T2 idx 70 (Yin-Yang named tradition)

> Q: Who is associated with the philosophical concept of Yin and Yang?
> A: Taoism

**Why discard.** Name-the-tradition rote. Distractors are real Chinese traditions, but again — not real rival accounts of yin-yang. The §6 condescension-toward-other-cultures rule does *not* fire here (the framing is respectful), but the question is craft-thin.

#### DISCARD #40 — T2 idx 55 (Who wrote Art of War?)

> Q: Who wrote 'The Art of War'?
> A: Sun Tzu, a Chinese strategist of the 5th century BC

**Why discard.** A4 patched fires (`^Who (wrote|...)` pattern). Distractors are other Chinese philosophers (Confucius, Laozi, Mencius). This is the bare "name the author" trivia shell §6 explicitly bans. Material is fine; shell is wrong.

#### DISCARD #52 — T3 idx 325 ("What is 'anti-realism'?")

> Q: What is 'anti-realism'?

**Why discard.** A4 patched fires. T3 difficulty content should not be "what is X?" Distractors *are* real rival positions worth engaging (rejection of abstract entities, denial of moral facts, scientific instrumentalism — all genuine anti-realisms). But the question doesn't teach what unifies these. Shell is unsalvageable.

#### DISCARD #54 — T3 idx 81 (Hegel dialectic) — same as n=25 Q11

> Q: Hegel argued that ideas, cultures, and consciousness itself develop through a specific three-stage pattern. What are the three stages, and what drives the process forward?

**Why discard.** Two-questions-in-one (A8 fail), A2 fail, A3 fail (717/600), A9 jargon wall. This question reappears from n=25 and the diagnosis is identical. The context paragraph correctly notes thesis-antithesis-synthesis was Fichte's, not Hegel's — that's the question worth asking, not this.

#### DISCARD #57 — T3 idx 128 ("What is 'communitarianism'?")

> Q: What is 'communitarianism'?

**Why discard.** A4 patched fires. The content (MacIntyre, Taylor) is real and important and worth covering — but this shell is identical to the metaphysics/anti-realism/premise/etc. pattern. Repair would require a complete rewrite, so DISCARD this shell.

#### DISCARD #59 — T3 idx 99 ("What does 'teleology' mean?")

> Q: What does 'teleology' mean?

**Why discard.** Both regex sets *miss this* (the patched fires only on `^What is/does '`; this has the quote later). It's the canonical definition-lookup pattern. Aristotle's teleology + Darwin's reintroduction-via-natural-selection (mentioned in context) is genuinely fascinating — that's the question. This shell isn't repairable.

#### DISCARD #60 — T3 idx 136 ("What is the 'coherence theory of truth'?")

> Q: What is the 'coherence theory of truth'?
> Lens: 70/46/67/70 — A2 fail

**Why discard.** A4-near fail (it has the `'` quote but not at position 9). Definition-lookup shell. Length-leak. Distractors include "truth is what corresponds to observable facts" which is correspondence theory not coherence — that's a partial strawman because it's offered as a wrong account of coherence rather than as a rival theory. Cannot be repaired without complete rewrite.

#### DISCARD #61 — T4 idx 203 ("What is 'mereology' in philosophy?")

> Q: What is 'mereology' in philosophy?

**Why discard.** A4 patched fires. A2 fail. A9 jargon wall — "mereology" at position 9 of the prompt, no 14-year-old grab handle. This is exactly the rubric §6 anti-pattern.

#### DISCARD #71 — T4 idx 216 ("What is 'agent-relative reasons'?")

> Q: What is 'agent-relative reasons' in moral philosophy?

**Why discard.** A4 patched fires. A9 jargon wall ("agent-relative reasons" at first phrase). The concept *is* concrete-able (your reason to care for *your* children) — but the question doesn't reach for it.

#### DISCARD #81 — T5 idx 182 ("What is 'speculative realism'?")

> Q: What is 'speculative realism'?

**Why discard.** A4 patched fires. T5 contemporary continental shell with no concrete anchor. The movement itself (Meillassoux, Harman, Brassier — none named in question) has real wonder potential (rejecting Kant's correlation; the universe doesn't need observers) but this question doesn't deliver any of it.

#### DISCARD #90 — T5 idx 212 ("What does 'opacity of reference' mean?")

> Q: What does 'opacity of reference' mean in philosophy of language?
> A: Substituting co-referring terms in belief contexts can change truth value

**Why discard.** Both patched and old regex fire. Distractors are real positions (definite descriptions, indexicals, Millian names) which earns A5 a pass — but the question is a Lois-Lane-needs-to-be-the-scene shell where the scene only appears in context. Repairable in principle, but the shell is the canonical case the rubric bans.

---

### Borderline REPAIRs worth flagging

#### REPAIR #20 — T1 idx 558 (Seneca / "we suffer more in imagination")

This passes all wonder_fun gates (7/7) and only fails A2 length parity. **Close to KEEP.** A simple length rebalance promotes it.

#### REPAIR #49 — T3 idx 606 (Confucius / failure across his career)

> Q: Confucius spent most of his career failing. He advised rulers who ignored him, lost his government positions, wandered in exile for 13 years, and died thinking his work had come to nothing. What did he believe made this not a wasted life?

This is a story-led T3 question that fails only on cost cap (833/600). 7/7 wonder_fun. Authentic §4 posture (no condescension toward Confucian thought). **Pure craft fix needed.** Same diagnosis applies to #56 (Confucius "when you know a thing"), #91 (Socrates at trial), #95 (the Stoic sage), #96 (Singer drowning child), and several other T5s.

#### REPAIR #82 — T5 idx 587 (Locke / tomato juice in the ocean)

> Q: Locke's theory of property rests on labor-mixing, but Nozick noticed a strange implication. If you pour a can of tomato juice into the ocean, do you thereby own the ocean? What was Nozick's point, and how does it threaten Locke's entire theory?

Story-led, vivid image (the tomato juice), surprise reversal, real payoff. 6/7 wonder_fun. Only fails because it's two-questions-in-one (A8) — drop "and how does it threaten Locke's entire theory" and it becomes a KEEP. **This is the n=100's closest near-KEEP missed for a simple fix.**

---

## 5. Rubric gap analysis

This is the most important section. The gates' job is to find what's broken; the report's job is to find what the gates miss.

### Gap 1 — The anti-rote regex still misses bare-noun lookups

Examples in n=100 that **A4 patched does not catch but should**:
- #2 T1 idx 257: "Which ancient city was home to Socrates?"
- #3 T1 idx 237: "What word means making a conclusion from clues or evidence?"
- #6 T1 idx 235: "If every person in a group agrees on something, that agreement is called what?"
- #29 T2 idx 279: "What does it mean to say an argument is 'valid'?"
- #59 T3 idx 99: "What does 'teleology' mean?"
- #60 T3 idx 136: "What is the 'coherence theory of truth'?" (the quote is at position 12, not "right after What is")

The patched regex correctly catches `^What (is|does) ['"]` but misses:
- `^What does (the )?['"\w]+ mean` ("What does teleology mean?")
- `^What (word|term|name) (means|describes|refers)`
- `^Which (ancient |modern |famous )?(city|philosopher|book|tradition) (was|did|is)` — name-the-thing trivia
- `^What is (the |a )['"]?[A-Z]` — "What is the coherence theory of truth?" — the named-concept-definition pattern (this was the n=25 recommendation; still relevant)

**Recommendation:** Extend §6 with three additional anchored patterns:

```
^What does ['"]?\w+['"]?\s+mean                                       # "What does teleology mean?"
^Which (ancient|modern|famous)?\s*(city|philosopher|book|tradition|country|nation)  # "Which ancient city..."
^What (word|term|name) (means|describes|refers|is used)              # "What word means inference?"
```

These are monotonic: they catch the 6 questions above without false-positive risk on real story-led questions, because real story-led questions don't open with these formulas.

### Gap 2 — Length parity catches symptom, misses cause

The §6 length-leaks-the-answer gate fires on 55 of 100 questions. That's the rubric working — but it's a *symptom* gate, not a *cause* gate. The cause is **the bank consistently writes the correct answer first and then writes shorter distractors around it.** Length-parity catches the length but misses the underlying authoring habit: distractors written after the answer, padded or trimmed not to balance choice length but to avoid being too similar.

**Rubric extension worth considering:** add a process rule — "distractors must be written from real philosophical positions, not back-fitted to balance the answer." This is not a deterministic gate but it could become a check in the LLM judgment passes: "Are the distractors authored at all? Or are they pad to differ from the answer?" The viral-test agent could catch this directly.

### Gap 3 — "Name the term" + foreign-language lookups slip through

The bank has a Greek/Sanskrit/Chinese-term gate in the old regex (`what is the (greek|sanskrit|...) term`) that was *removed* from the patched §6. The patched regex no longer catches:
- Anything testing "what is the Greek term for X?"
- The named-concept-lookup pattern with foreign terms generally.

In this n=100 sample no test hits this — but it's a latent gap. **Recommendation: restore the foreign-term-lookup pattern**, anchored: `^What is the (greek|latin|german|sanskrit|chinese|french|japanese|arabic|hebrew) (term|word|name) (for|of)`.

### Gap 4 — "What is the difference between X and Y" two-questions-in-one isn't gated

The §6 two-questions-in-one rule is judgment-only (A8). Nothing in the deterministic gates catches the pattern. n=100 hits #54 (Hegel "three stages AND what drives it forward"), #82 (Locke labor-mixing "what was Nozick's point AND how does it threaten"), #93 (Cicero "what was his conclusion AND why did it upset both schools"), #95 (Stoic sage "why did they maintain... rather than adjusting"). A simple regex catch: `\bwhat (is|was|were|are) .* (and|, ) (why|how|what)` — matches "what was X, and what does it explicitly exclude" or "what was his point, and how does it threaten."

This wouldn't be a hard fail by itself (compound questions sometimes work), but as an A4-style soft signal it would prompt the LLM judgment pass to look hard.

### Gap 5 — The "advocacy framing" gate fires too lightly on Rand/Rothbard questions

Rand/Rothbard questions in n=100 (#7, #15, #17, #22, #27, #37, #47, #62, #83, #94) show a pattern: the question presupposes Rand's or Rothbard's frame before asking what *they* said. #7 ("a person who produces nothing but lives off the work of others — especially using political connections to take from producers — is a what?") is the worst example — the *prompt* does Rand's analysis, then asks for the label.

The rubric §6 advocacy gate says "a question that reads as 'did you know X is bad/good?'" — and the rubric §11 dual-commitment rule says "celebrating the West AND honest about its failures." Together they imply: when steel-manning a tradition the bank's worldview endorses (Rand, Rothbard, Mises, Hayek), the question must still be **discovery**, not **catechism**.

The current A6 gate fires on the most blatant cases (4 fails in n=100) but misses the soft version where the question's setup pre-loads the answer's frame. **Recommendation:** sharpen A6 to fire when the question's prompt does the philosophical work the *answer* should be doing. Example: instead of "Rand said that a person who produces nothing but lives off the work of others is a what?" — write "Rand's villains in Atlas Shrugged are not the desperately poor; they are politicians and bureaucrats who succeed through favoritism. What term did she coin for them?" The second version sets the scene (story-led), the answer reveals the term.

The Rand questions, taken together, are the strongest signal that **moral_fit is permissive on tradition-aligned content.** This is the n=25 finding holding at n=100: the bank's voice problem is worse for tradition-aligned philosophers than for opposing ones.

### Gap 6 — The viral test (A14) has no operational anchor for "intellectual flimsiness"

A14 fires 18 times in n=100. Most of those are not "would the social-media mob be mad" — they are "the author would be embarrassed by the question's craft thinness." Rubric §7 says the test catches "intellectual flimsiness, partisan flame-bait, strawmen of opposing views, condescension, or punching down." But "intellectual flimsiness" has no operational definition.

Examples of A14 firing for flimsiness in n=100:
- #3 ("What word means making a conclusion from clues?") — not flame-bait, just embarrassingly thin
- #11 ("What is 'metaphysics'?") — same
- #61 ("What is 'mereology' in philosophy?") — same at T4

The viral test is doing real work but the rubric doesn't tell the agent *what* to flag besides flame-bait. **Recommendation:** add to §7: *"The agent should also flag questions whose intellectual content is so thin that the bank would be embarrassed to ship them — definition-lookups with no surrounding wonder, questions whose answer is a single word with no philosophy behind it, questions a 14-year-old would find boring even with a competent narrator."*

### Gap 7 — No gate catches "tier mismatch"

Several questions are tagged with a tier well above their actual difficulty:
- #2 T1 (Athens / Socrates): T1 is fine but this is genuinely Geography-101, not philosophy at T1.
- #33 T2 (aporia): T1 trivia in T2 dress.
- #36 T2 (Yin-Yang named tradition): same.
- #57 T3 (communitarianism): T2 difficulty in T3 dress.
- #61 T4 (mereology): T3 dictionary content in T4 dress.

The rubric has no gate for tier appropriateness. n=25 also flagged this (Rex the dog at T1, "examined life" at T3 vs. better T1 version of same fact). **Recommendation:** add a tier-fit gate to the judgment pass: "Does the question require knowledge a typical T{n} player would reasonably possess, and is the depth-of-thought required appropriate to T{n}? Tier mismatches downgrade the question to REPAIR."

### Gap 8 — No gate catches "duplicate content across tiers"

Several questions cover material the bank covers better elsewhere:
- The Yin-Yang question (#36) is one of three different yin-yang questions in the bank (one at T1, one at T2, one at T3 according to the prior voice analysis).
- The "what is X?" Socrates / examined-life pattern repeats across tiers.

The rubric is silent on duplication. **Recommendation:** add a post-gate de-duplication pass: "if two questions test the same fact or concept with similar framing, keep only the best-crafted version, and downgrade duplicates to REPAIR-with-redirect or DISCARD."

### Gap 9 — Soft-virtue / "applied virtue ethics" preachy questions slip through

The n=25 Q1 (integrity / broken promise) failed multiple gates. n=100 has only one soft-virtue analog — #1 (Lao Tzu / water as flexibility) — which leans slightly preachy in answer phrasing ("Yielding and flexibility are stronger than force and rigidity") but is wrapped in genuine Lao Tzu material. The rubric §5 "show virtue, don't preach virtue" rule is doing its work — but the gate is judgment-only. There is no deterministic signal for preachy virtue framings.

**Recommendation:** consider an "answer phrasing" gate that flags answers ending in moralistic punchlines: `(matters|is what counts|is what's right|teaches us that)` at end-of-answer. Mostly judgment-bound, but flagging would help.

### Gap 10 — "What is 'X'?" with the named concept being a *thought experiment* slips by

Examples in n=100 where the patched A4 fires but the question is genuinely about a thought experiment with a vivid scene available in context:
- #45 T3 idx 329 ("What is Wittgenstein's 'private language argument'?") — the beetle in the box scene
- #51 T3 idx 365 ("What is 'the Gettier problem'?") — the colleague/car scene
- #55 T3 idx 320 ("What is 'Zeno's paradox of motion'?") — the walk across the room scene
- #78 T4 idx 376 ("What is 'the explanatory gap'?") — taste of an apple / Nagel's bat
- #88 T5 idx 183 ("What is Hilary Putnam's 'twin earth' thought experiment about?") — the literal Twin Earth scene

In every case the scene is the *correct* opening for the question — the bank already wrote it in the context paragraph. The A4 regex correctly flags the rote shell, but the rubric could go further: when the context paragraph contains a vivid scene that the question itself doesn't use, the question is **mandatorily repair**, not optionally repair. **Recommendation:** add a meta-check: "If the context paragraph contains story-led concrete material the question does not, the question is REPAIR by default."

---

## 6. Calibration verdict

### 6a. Is the rubric well-calibrated at n=100?

**Yes, broadly. With the noted gaps.**

The 7% KEEP, 74% REPAIR, 19% DISCARD distribution (corrected per per-question table) is what a *bank-built-to-information-density-not-voice* should produce against a *wonder-first* rubric. The bank's craft is uneven but the underlying material — Rand, Rothbard, Mises, Locke, Mill, Tocqueville, Berlin, Sellars, Confucius, Lao Tzu, Marcus Aurelius, Seneca, Singer, Nozick, Wittgenstein, Kuhn — is exactly what §3 of the rubric calls for. The Austrian / classical-liberal lineage (§3.3) is well-represented. Western intellectual heritage (§3.4) is well-represented. Eastern thought (Confucius, Lao Tzu, Sun Tzu) is treated with §4 respect. Religious thought (Aquinas, Plantinga, John the Evangelist) is treated with §4 seriousness.

**No question in the n=100 sample hits §6's worst patterns:** no anti-Western framing, no sex-spectrum applied to humans, no smug-atheist or smug-believer voice, no dated topical references, no condescension. The bank's values posture is intact across all 100. **This is the most important calibration finding.** The bank does not need a values-rebuild. It needs a craft-rebuild.

### 6b. Does the verdict distribution match what the user expects?

User framing: **"absolutely awful by voice, salvageable by craft."**

Match: **partial / better than expected.**
- "Absolutely awful by voice": confirmed. wonder_fun B1-B4 all fail >40%; voice is the dominant defect.
- "Salvageable by craft": 74% REPAIR confirms this is more right than n=25's 56% suggested.
- "Beyond saving": 19% DISCARD is **half** of what n=25's 36% predicted. The n=100 reveals the small-sample swing.

### 6c. Recommendation

**Ship the rubric with three additions:**

1. **Patch the anti-rote regex one more time.** Add the three patterns named in Gap 1: `^What does ['"]?\w+['"]?\s+mean`, `^Which (ancient|modern|famous)?\s*(city|philosopher|book|tradition|country|nation)`, `^What (word|term|name) (means|describes|refers|is used)`. These are monotonic — they add catches without bringing back the false-positives the original patch was designed to eliminate.

2. **Add a tier-fit gate** (Gap 7). T1-tier philosophy material being tagged T3 or T4 wastes generation budget and skews the bank's difficulty curve.

3. **Sharpen A6 advocacy framing** to fire on soft-advocacy where the prompt does the philosophical work (Gap 5). Rand/Rothbard questions in particular show the pattern.

**Do not sample more.** The n=25 → n=100 deltas are within sampling noise on KEEP (8%→7%), but they meaningfully moved DISCARD (36%→19%) toward REPAIR. A third sample at n=200 or n=500 would not change the calibration verdict — the bank is consistently 7-8% KEEP with the remainder split between REPAIR and DISCARD. Further sampling is a cost without clear payoff.

**Bottom line:** the rubric is calibrated. The bank is rebuildable. The biggest single mechanical improvement is fixing the "What is 'X'?" shell pattern across ~25-30% of the bank (largely the same questions A4 catches plus the Gap-1 extensions). The biggest single craft improvement is **moving the scene from the context paragraph into the question** — the bank already has the scenes; it just doesn't use them.

The estimated rebuild burden, extrapolated from this sample:

- ~43 KEEP-as-is (7% × 615)
- ~455 REPAIR (74% × 615)
- ~117 DISCARD (19% × 615)

That's a meaningful shift from n=25's projection (~344 REPAIR, ~222 DISCARD). The rebuild workload is **less destruction, more renovation** than n=25 implied. Most of the bank can be saved with craft work. The pipeline budget should plan for ~450 repairs, not ~340.
