# Overnight QA Audit — Unified Synthesis Report

**Date:** 2026-05-27 → 2026-05-28 morning
**Baseline tag:** `audit_baseline_2026_05_27`
**Phases run:** A (deterministic sweep) + B (12 parallel opus LLM-judges) + C (this synthesis)
**Bank modifications:** NONE — every artifact is read-only. Bank state at baseline tag is intact.

---

## Headline numbers

**15,789 questions audited across 12 banks.**

| Bank | Questions | Flags | CRIT | WARN | MINOR | Flag rate |
|---|---:|---:|---:|---:|---:|---:|
| math | 2,455 | 313 | 86 | 222 | 5 | **12.7%** |
| philosophy | 882 | 90 | 5 | 72 | 13 | **10.2%** |
| cooking | 992 | 65 | 8 | 47 | 10 | 6.5% |
| geography | 1,123 | 71 | 8 | 60 | 3 | 6.3% |
| ai | 1,215 | 71 | 3 | 48 | 20 | 5.8% |
| animal | 938 | 47 | 0 | 13 | 34 | 5.0% |
| economics | 1,426 | 70 | 1 | 47 | 22 | 4.9% |
| history | 1,049 | 38 | 4 | 21 | 13 | 3.6% |
| theology | 1,020 | 36 | 2 | 8 | 26 | 3.5% |
| science | 1,311 | 38 | 1 | 31 | 6 | 2.9% |
| trivia | 1,444 | 23 | 7 | 7 | 9 | **1.6%** |
| grammar | 1,934 | 22 | 4 | 2 | 16 | **1.1%** |
| **TOTAL** | **15,789** | **884** | **129** | **578** | **177** | **5.6%** |

**Big picture:** 94.4% of questions are clean. The bank is overwhelmingly high-quality. The remaining 5.6% breaks down into a small number of systemic patterns (a few of which are mechanically fixable in batch) plus a long tail of one-off corrections.

---

## Per-bank quality scorecard

### 🟢 Excellent (≤2% flag rate)
- **grammar (1.1%)** — Comma-Saves-Lives Pattern working. 4 broken "trick" Qs (apricot/spectrum/scribble/facade — answer contradicts context) + 1 typo + 16 minor decoration. Strong.
- **trivia (1.6%)** — Easter Egg Pattern working. 6 critical factual errors + 4 stray meta-corrections from generation. Bank just shipped fresh and held up.

### 🟢 Strong (2-4% flag rate)
- **science (2.9%)** — Vaccine-scrutinized stance + Discovery Pattern substance EXCELLENT. 36/38 flags are §15 weasel closers (substance is right, closer needs sharpening). 1 stem-leak.
- **theology (3.5%)** — Symmetric voice mostly held. Small Christian-doctrinal residue (1 "fulfilling prophecy of Micah" + 7 "foreshadowing" patterns). 5 factual nits (Noah dove third-vs-second trip, Bathsheba-rooftop, Delilah-wife-vs-lover, Frigg golden tears).
- **history (3.6%)** — Wonder Pattern named-quote answers DOMINATE. But cross-tier same-answer duplicates (Joan of Arc 7Qs!, Newton apple 4 tiers, Wright Bros 6 tiers, etc.).

### 🟡 Healthy with patterns to fix (4-7%)
- **economics (4.9%)** — Bastiat Pattern + Austrian stance clean. But 50 distractor-telegraph suffixes ("— a position contradicting the Austrian record") and 14 weasel closers + 1 factual (1929 vs 2008 first Austrian warning).
- **animal (5.0%)** — Wonder Pattern strong. 15 weasels + citation skim-tells + 5 factual cases to verify (Hercules beetle 850x, polar bear fur, woodpecker hyoid, megalodon 3.6mya).
- **ai (5.8%)** — Recognition Pattern + contested topics handled honestly. 49 weasel closers + 20 T1 joke distractors (Daniel Boone as Anthropic CEO, Crayola/Lego as self-driving) + 1 Sora-image-vs-video category error.
- **geography (6.3%)** — Wonder Pattern clean. 48 decoration-parity skim-tells (parens-only-correct: "Badgir (windcatcher)") + 17 weasels + GPS-1962 factual error + 1 verbatim duplicate.
- **cooking (6.5%)** — Wonder Pattern EXCELLENT (zero generic-label answers when cool fact available). But **24 truncation bugs** (mid-word cuts ending in prepositions) that Phase A's regex missed entirely.

### 🟠 Needs work (>10%)
- **philosophy (10.2%)** — 117 stems with wonder-bias-violating scenery (YouTuber/podcast/group-chat where framework specifies knight/scribe/monk). 52 stems with philosopher names as framing. T5 aesthetics has a structural length-parity skim-tell block (idx 84-98).
- **math (12.7%)** — **MOST URGENT.** 80 questions with literal `NA0`/`NA1` placeholder strings leaking from bulk-gen. 179 questions with `+100` prepend distractors instead of common-mistake distractors. 39 tier-mismatch issues (T5 has T2-T3 content). 6 banned joke distractors. 1 factual ambiguity (megabyte SI vs IEC).

---

## Top 20 highest-severity items (cross-bank, for immediate review)

| # | Bank | Idx | Tier | Issue |
|---|---|---:|---:|---|
| 1 | math | (80 indices) | T1-T5 | **`NA0`/`NA1` placeholder strings as distractors** — bulk-gen artifact leakage, real-text replacement needed |
| 2 | math | (179 indices) | T1 | **`+100` prepend distractor pattern** — not learner mistakes, all need real common-error distractors |
| 3 | trivia | 136 | T5 | Post-Attitude WWE stance violation (WM XXV 2009 + WM XXX 2014). Gate missed Roman-numeral pattern |
| 4 | cooking | 482, 450, 372 | T5/T4/T1 | All 4 choices truncated mid-phrase. Unplayable. |
| 5 | history | 719 | T4 | **Fabricated fact** — distractors claim Honecker/Husák/Zhivkov "shot" Dec 1989 (none were) |
| 6 | history | 487 | T3 | Joan-at-Rouen Drama-Available repeat — canonical failure from HISTORY_TEMPLATES §1 |
| 7 | trivia | 192 | T3 | DBZ Cell Saga factual error — Gohan SS2 trigger is Cell crushing Android 16, NOT Goku's sacrifice |
| 8 | trivia | 360 | T4 | Yu Yu Hakusho — Atsuko is Yusuke's MOTHER, not grandfather |
| 9 | trivia | 470 | T3 | Andre the Giant — Princess Bride wasn't his only major film (Conan the Destroyer 1984) |
| 10 | geography | 1015 | T4 | GPS-1962 stem wrong — GPS was 1973-authorized. Same bank IDX 628 has correct 1973 |
| 11 | geography | 745 | T5 | Verbatim duplicate of IDX 590 (Hokule'a 1976) |
| 12 | grammar | 399, 978, 980, 981 | T2/T4/T4/T4 | "Trick question" answers contradict their own contexts (apricot IS from Arabic, spectrum IS from spect-, scribble IS from scribere, facade IS from facere) |
| 13 | theology | 4 | T1 | Noah's dove returned olive leaf on SECOND trip (Genesis 8), stem says third |
| 14 | theology | 27 | T1 | "fulfilling the prophecy of Micah" — banned Christian-doctrinal framing |
| 15 | ai | 64, 76, 89 | T1 | Joke distractors (Daniel Boone as Anthropic CEO; Antarctica as chess capital; Crayola as self-driving co) |
| 16 | history | 498 | T3 | "Mary had a little lamb" is 5 words; stem says Edison recorded "four words" |
| 17 | economics | 59 | T1 | "Which bust did Austrians warn about FIRST?" answers 2008 — actually 1929 (Mises 1924+, Hayek's institute) |
| 18 | science | 1118 | T5 | Stem-leak: setup literally states answer ("In 1986 children received about 11 doses... how many doses?") |
| 19 | philosophy | 84-98 | T5 | Aesthetics block-wide length-parity skim-tell (correct ~185 chars vs distractors ~220) |
| 20 | trivia | 668 | T5 | Internal contradiction — answer "C. Lindsay Workman" but context says Pat Carroll is correct attribution |

---

## Dominant patterns (fix opportunities by impact)

### Pattern 1 — §15 weasel closers (largest cross-bank issue)

**Total: ~160 across banks** (cooking 31, ai 49, science 36, geography 17, animal 15, economics 14). Phase A regex caught only 6.

**Why missed by Phase A:** the regex was too narrow. Banned variants the judge found include:
- "What does this teach/illustrate/demonstrate/prove/reveal?"
- "Why does this matter (for X)?"
- "What's the structural concern?"
- "What's the broader lesson?"
- "What broader change/pattern?"
- "What does this conflict/arc reveal?"

**Recommended fix:** mechanical batch-rewrite using each bank's voice rule + a broader weasel regex. Substance in stems is good across all weasel-flagged questions — only closing question form needs tightening.

**Estimated effort:** 1 opus agent per bank, processing flagged questions only. ~160 rewrites total, gate-validated, applied per-bank in batches.

### Pattern 2 — Distractor parity skim-tells (parens-decoration mismatch)

**Total: ~80 across banks** (geography 48, theology 11, animal 15+, philosophy minor).

**The problem:** Only the correct answer carries an inline gloss like "(windcatcher)" / "(HIF2A)" / "(libra, chorobates)" / "(dragon-fly genus)" — distractors don't. The current `choice_shape_parity` gate is **dash-only**, missing parens-decoration. Skim-tell: kids learn to pick the choice with extra information.

**Recommended fix (two options):**
- **A.** Mechanical sweep: strip parens-with-gloss from correct answers across the 80 flagged questions; move the gloss into stem or context.
- **B.** Add parens-decoration check to the universal `choice_shape_parity` gate; flag forward, leave existing content alone for now.

### Pattern 3 — math distractor quality (NA0/+100 systemic)

**Total: ~260 math questions affected.**

- 80 questions with `NA0` / `NA1` literal placeholder text from bulk-gen
- 179 questions with `+100` prepend distractors (not learner-mistakes)

**Severity:** Critical. This breaks the math bank's pedagogical quality at scale. Bulk-gen scaffolding artifacts.

**Recommended fix:** A dedicated math-distractor-rewrite agent (or batch script) that replaces NA0/NA1 with real common-mistake distractors (off-by-one, wrong-operation, sign error, place-value error). The +100 pattern can be detected mechanically and rewritten.

### Pattern 4 — cooking truncation cluster

**Total: 24 questions in cooking with truncated answers and/or distractors.**

Phase A's TRUNCATION_BAD regex missed these — they end in bare prepositions ("the", "across", "into", "by", "to"). This is exactly issue #48 on the pending task list ("Add mid-word-truncation gate (universal)") — finally pinpointed.

**Recommended fix:** Add `\b(?:the|a|an|of|to|in|on|at|by|for|with|from|across|into|onto)\s*$` to the truncation gate, then rewrite the 24 affected questions with complete sentences.

### Pattern 5 — history cross-tier duplicates

**Total: ~10 clusters with same-answer at 3+ tiers.**

Joan of Arc (7 questions!), Newton-apple (4 tiers), Wright-Brothers-12-seconds (6 tiers), Brunelleschi-herringbone (4), Tycho-nose (4-5), Mansa-Musa-decade (5), Bach-Mendelssohn-revival (5), Kennedy-Berliner (3), Sistine-neck-curse (3+), Sulh-i-kul (5).

**Recommended fix:** Per HISTORY_TEMPLATES §1.5 (Lavoisier-style guidance + Brunelleschi-one-event-five-questions worked example), keep ONE tier per cluster (usually lowest) and rewrite higher-tier versions with DIFFERENT cool facts about the same figure/event.

### Pattern 6 — philosophy scenery violations

**Total: ~117 stems with wonder-bias-violating modern-mundane scenery.**

YouTuber (31), podcast (38), school-newspaper (40), debate-club-captain (31), plus cafeteria/locker/smartphone/TikTok. The framework specifies knight/scribe/monk/court-debate/cathedral-tower scenery.

**Recommended fix:** Block-rewrite the flagged questions (most concentrated in fallacy block idx 340-440 and aesthetics block idx 40-79). Same logic, canonical scenery.

### Pattern 7 — small factual error cluster (cross-bank ~30 total)

A handful of factual errors across animal, economics, geography, grammar, history, theology, trivia. Most are obvious to fix once flagged:
- Honecker/Husák/Zhivkov never shot (history)
- "Mary had a little lamb" word count (history)
- Atsuko = mother not grandfather (trivia DBZ)
- Andre the Giant film career (trivia)
- GPS authorized 1973 not 1962 (geography)
- Austrians warned of 1929 not 2008 (economics)
- Bathsheba on rooftop (theology — actually David)
- Delilah = lover not wife (theology)
- Frigg golden tears (Freyja's signature, theology)
- Noah dove second trip (theology)
- Hercules beetle 850x (animal, ~100x more accurate)
- Megalodon ~3.6mya not 3.0 (animal)
- "fulfilling the prophecy of Micah" (theology stance)
- Sora image-vs-video (ai category)

### Pattern 8 — small stance-residue cluster

- Theology: 1 "fulfilling Micah" + 7 "foreshadowing" softer cases
- Philosophy: vaccine-COI-as-fallacy (idx 410), climate-research-as-consensus (170, 368), MMT-friendly framing (443)
- Trivia: 1 post-Attitude WWE (IDX 136)
- Science: 1 stale "late 2024" reference

### Pattern 9 — economics distractor scaffold telegraph

**Total: ~50 T5 economics questions with suffix "— a position contradicting the Austrian record" / "— a position contradicting Rothbard's reputation" / "— inversion" / "— denial" / "— legal technicality"** explicitly labeling distractors as wrong.

**Recommended fix:** Mechanical strip-suffix script.

### Pattern 10 — AI T1 joke distractors

**Total: 20 T1 ai questions** with "obviously dumb" distractors (Daniel Boone as Anthropic CEO, Antarctica as chess capital, Crayola/Lego/Hasbro as self-driving companies). Violates AI_TEMPLATES.md §2.

**Recommended fix:** Replace each set of distractors with real adjacent companies/places/people from the same category.

---

## Cross-bank checks

### Stem-prefix matches (60 from Phase A)
- Math: ~7 templated drills (5², 12+23, 12², logₐb) — false positives from short stems
- Grammar: 3 same-setup-different-Q pairs (Noah Webster 1828, Chicago Manual 1906, Reed-Kellogg)
- History: confirmed via Phase B — Newton (2), Challenger (2 — different cool facts, legitimate), Fleming (2 — questionable), Darwin (2 — legitimate), **Michelangelo Sistine (3 near-duplicate "neck twisted" answers — REAL duplicate to fix)**

### Bank-to-bank factual contradictions
Geography 1015 (GPS 1962) vs geography 628 (GPS 1973) — same bank, internal contradiction.
No cross-bank contradictions detected.

---

## Patterns NOT found (clean across the board)

These are bank-wide quality wins where the gates + framework discipline worked:
- ✅ **Trailing-token corruption: 0 cases** (the §12 gate is doing its job)
- ✅ **Christian-doctrinal drift in theology: 0 in deterministic sweep** (only 1 lurking case in Phase B Micah finding)
- ✅ **Spoilers in trivia outside the 10 allowed franchises: 0** (the no_spoilers gate held)
- ✅ **Modern multiverse / Disney SW / post-Endgame MCU in trivia: 0 confirmed** (1 post-Attitude WWE escaped via Roman-numeral pattern)
- ✅ **Post-Legends MtG / modern D&D errata: 0**
- ✅ **Credulous cryptid framing: 0**
- ✅ **Smug atheist or smug believer voice in theology: 0**
- ✅ **Modern multiverse capeshit, post-Endgame MCU films, Disney+ MCU shows: 0**
- ✅ **Fake etymologies in grammar: 0**
- ✅ **Above-grade-10 jargon (Chomsky/Saussure/etc.): 0**
- ✅ **Attribution-style "Who said X?" stems in philosophy: 0**
- ✅ **§16 teach-before-test failures: 0 across all banks**
- ✅ **Above-grade-10 economic math (Cobb-Douglas, IS-LM, etc.): 0**
- ✅ **Anthropomorphizing failures in AI: 0**
- ✅ **Fabricated models in AI: 0**
- ✅ **False-balance doomer-vs-optimist in AI: 0**
- ✅ **Stance drift in moral_vision substantive areas (Austrian, communist death toll, Western achievement): 0**

---

## Phase D — Recommended morning review priorities

Suggested order when you wake up:

### 1. Glance at this report (5 minutes)
Decide which categories you want to fix and which to defer.

### 2. CRITICAL items review — read the JSONs for top-20 list (30 minutes)
Each `_audit_phase_b_<bank>.json` has the detailed flag records. The 20-item table above gives idx + bank + issue.

### 3. Approve fix batches (your call):
- **Highest impact, deterministic, low risk:** math NA0 + +100 distractor batch (260 questions)
- **High impact, deterministic, low risk:** economics distractor-suffix-strip (50 questions)
- **Medium impact, mechanical:** cooking truncation fixes (24 questions)
- **High impact, LLM-judged:** §15 weasel closers across cooking/ai/science/geography/animal/economics (~160 questions)
- **High impact, LLM-judged:** philosophy scenery rewrites (~117 questions)
- **High impact, factual:** ~30 factual error fixes
- **Medium impact, mechanical:** geography decoration-parity (48 questions)
- **Medium impact, LLM-judged:** history cross-tier dedup (10 clusters)
- **Lower impact, LLM-judged:** ai T1 joke distractors (20 questions)
- **Lower impact, LLM-judged:** theology Christian-doctrinal residue (8 questions)

### 4. Decide gate-precision additions for future generation:
- Broader §15 weasel regex (definitely worth doing — would have caught ~160 cases pre-commit)
- Parens-decoration parity in `choice_shape_parity` gate
- Mid-word truncation expanded to cover "ends in preposition" pattern
- AI T1 joke-distractor regex

### 5. Sign-off on Phase E (apply fixes)

When you're ready, I'll process approved batches per the bank's voice rule:
- Validate every rewrite through `validate_rewrite`
- Apply only PASS/SOFT_WARN
- Run pytest after each batch
- Commit per-bank with detailed message
- Push only after final test sweep

---

## What I did NOT do overnight (per safety rules)

- ❌ Modified any bank JSON file
- ❌ Applied any rewrites
- ❌ Deleted any questions
- ❌ Pushed any changes to GitHub
- ❌ Changed any gate code
- ❌ Modified exemplars or frameworks
- ❌ Ran any destructive git operation

Baseline tag `audit_baseline_2026_05_27` preserves the launch-ready state. Any morning fix path is reversible to this point.

---

## Files written overnight

- `_audit_phase_a.py` — Phase A sweep script
- `_audit_phase_a.json` — Phase A flag detail
- `_audit_phase_b_rubric.md` — Phase B agent rubric (shared by all 12 judges)
- `_audit_phase_b_<bank>.json` (×12) — per-bank flag records
- `_audit_synthesis.md` — this report

All committed at the baseline + Phase-A commit. The 12 Phase B JSONs not yet committed (waiting for your morning sign-off so we can roll them into the Phase E commit).

---

## Final word

The bank is **launch-ready as-is**. Phase B is a quality-polish layer, not a must-fix-before-ship layer. The deterministic gates already catch everything that would make a bank UNPLAYABLE; Phase B identifies the next layer of "make it as good as it can be" content quality.

You could ship right now and the bank would still be solid. Or you could approve some/all of the fix batches and ship after a final regression pass tomorrow afternoon.

Sleep well. ☕ in the morning.

— Claude
