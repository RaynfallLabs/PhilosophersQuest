# Philosophy Post-Geography Audit (2026-05-24)

Read-only audit of `data/questions/philosophy.json` (882 questions) against the
gates and principles discovered during the 2026-05-23 geography rebuild.
Applies each rule only where naturally relevant per
[[feedback_no_content_warping]] — philosophy is the original "reasoning move"
subject, with the most mature gate set in the bank (8 deterministic gates
already enforced by `tools/quizgen/scratch/philosophy_structural_gates.py`),
so several geography gates are already implemented in philosophy under
different names (e.g., geography's `no_theory_stacking_check` is philosophy's
`inline_teaching` judgment gate per PHILOSOPHY_TEMPLATES.md §8.2).

Source files audited:
- `data/questions/philosophy.json` (882 questions: T1=162, T2=165, T3=182, T4=186, T5=187)
- `tools/quizgen/deterministic/length_budget.py` (canonical cap system — philosophy uses DEFAULTS, not an override)
- `tools/quizgen/scratch/philosophy_structural_gates.py` (8 deterministic + heuristic gates)
- `proposals/v2_audit/PHILOSOPHY_FRAMEWORK.md` + `PHILOSOPHY_TEMPLATES.md`
- `proposals/v2_audit/GEOGRAPHY_FRAMEWORK.md` + `GEOGRAPHY_TEMPLATES.md`
- `proposals/v2_audit/SHARED_PRINCIPLES.md` §§9-10

## Summary

- **Bank size**: 882 questions (T1=162, T2=165, T3=182, T4=186, T5=187)
- **Findings severity**: **MEDIUM** overall, with **one HIGH-severity content
  bug** (~15-20 fallacy questions where the wonder-bias scenery upgrade was
  applied to stems but not to answers/distractors).
- **Top 3 actionable recommendations**:
  1. **HIGH — Repair stem/answer scenery mismatches**. ~15-20 T1/T2 fallacy
     questions show stems rewritten with canonical wonder-bias scenery
     (squire, chapter-house, tavern in the realm, alchemist's tonic, citadel)
     while answers/distractors still reference the original mundane modern
     scenery (sleepover, pizza, smartphone, fundraiser, cleats). Example
     (line 3760-3761): stem says "alchemist's tonic / bard"; answer says
     "pop star's commercial / energy drink." This is a content bug, not a
     style preference — the answer no longer matches the stem.
  2. **MEDIUM — Recalibrate philosophy SUBJECT_TIER_BUDGETS** to match the
     templates §6 per-field caps. Current canonical caps {600, 700, 750, 950,
     1000} are TIGHTER than what the philosophy templates §6 allow (per-field:
     stem 220/250/290/340/400 + each-choice 110/130/160/190/230 = 660/770/930/
     1100/1320 total). The bank was authored against the looser per-field
     spec; most T3 and T5 questions exceed the canonical total. Same "two
     cap systems diverge" failure mode as geography pre-2026-05-23.
  3. **LOW-MEDIUM — Uncap context per SHARED_PRINCIPLES §9.** Philosophy is
     heavily history-of-ideas-driven (Plantinga 1974, Aquinas Summa I.2.3,
     Hick 1966, Foot 1967, etc.). Contexts are systematically clipped at
     250-350 chars even at T5; uncapping would let "named source" tags
     transmit the actual argument rather than just announce it. Same fix as
     geography 2026-05-23.

The bank passes the other audit axes cleanly:
- **Decoration mismatch**: low — most decorated answers have matching
  decoration on at least some distractors; no systemic skim-tells.
- **Wonder-in-stem deferral**: zero hits on the geographic-style pattern
  (philosophy stems lead with scenarios, not "what year did X happen").
- **Theory-stacking**: ~3 cases at T4-T5, all properly anchored inline.
- **Verdict-on-contested**: zero hits — the gate is working.
- **Register consistency**: zero hits at low tiers for specialist vocab.
- **Steelman distractors**: HIGH — formulaic dismissals essentially absent;
  distractors are uniformly real philosophical positions.

---

## 1. Total-budget calibration

### Current canonical (philosophy falls through to DEFAULT_TIER_BUDGETS)
Per `tools/quizgen/deterministic/length_budget.py` lines 22-28 — philosophy is
**not** in SUBJECT_TIER_BUDGETS (line 32-42), so it inherits the defaults:

| Tier | Default budget | +5% hard cap | Philosophy timer (s @ WIS 10) |
|---:|---:|---:|---:|
| T1 | 600 | 630 | 65 |
| T2 | 700 | 735 | 65 |
| T3 | 750 | 787 | 65 |
| T4 | 950 | 997 | 65 |
| T5 | 1000 | 1050 | 65 |

(Timer: `src/player.py:26` — `'philosophy': (50, 1.5)` → 50 + 1.5×10 = 65s.)

### Per-templates caps (PHILOSOPHY_TEMPLATES.md §6)
The templates spec specifies per-field caps that imply a much higher total:

| Tier | Stem ≤ | Each choice ≤ | Implied 4-choice total | Implied stem+4choices total |
|---:|---:|---:|---:|---:|
| T1 | 220 | 110 | 440 | **660** |
| T2 | 250 | 130 | 520 | **770** |
| T3 | 290 | 160 | 640 | **930** |
| T4 | 340 | 190 | 760 | **1100** |
| T5 | 400 | 230 | 920 | **1320** |

**Two cap systems are in active disagreement** by 60-320 chars per tier. The
templates spec is more generous; the canonical pipeline gate is tighter.

### Empirical (full bank, regex-counted from `philosophy.json`)
Stem-length histogram across the bank (all 882 questions):

| Stem length | Count | % of bank |
|---:|---:|---:|
| ≥ 150 chars | 880 | 99.8% |
| ≥ 200 | 734 | 83.2% |
| ≥ 250 | 513 | 58.2% |
| ≥ 300 | 272 | 30.8% |
| ≥ 350 | 56 | 6.3% |
| ≥ 400 | 0 | 0% |

Stems hit the templates §6 stem caps (T5=400 max) — none exceed. Median ~250.

### Sample-based per-tier totals (hand-counted from JSON)
Spot-sampled 5-8 questions per tier from blocks at the start of each tier band:

| Tier | Stem typical | Choices typical (each×4) | Approx total avg | Canonical budget | Templates implied | Over canonical? |
|---:|---:|---:|---:|---:|---:|---|
| T1 | 170-220 | 80-100 each → 320-400 | ~500-560 | 600 | 660 | mostly under |
| T2 | 220-260 | 100-130 each → 400-520 | ~700-750 | 700 | 770 | **right at edge, many over** |
| T3 | 260-300 | 130-160 each → 520-640 | ~850-950 | 750 | 930 | **frequently over** |
| T4 | 280-340 | 160-200 each → 640-800 | ~950-1100 | 950 | 1100 | **frequently over** |
| T5 | 330-400 | 190-280 each → 760-1100 | ~1150-1400 | 1000 | 1320 | **majority over** |

(These are approximate hand-counts of representative questions, not a full
histogram. A scripted full-bank histogram is the right next step — flagged
for the user; pytest could run the analysis if a regression test were added.)

### Why the bank historically passed `validate --subject philosophy` despite this
Two possibilities, both worth user confirmation:

1. **The pipeline `length_budget` gate is enforced as a soft-warn for
   philosophy specifically** in `validate_length_budget` (the test for
   `total > hard_cap` → FAIL). If the pipeline is run with philosophy in
   the override, this check would fire. The author-time scaffolding-over-
   compression rule (per `moral_vision.md` §6 "Phrasing awkwardness" /
   "Scaffolding > compression (2026-05-11 update)") explicitly says to add
   scaffolding rather than trim — but the gate hasn't been updated to match.
   The 2026-05-11 update bumped DEFAULT_TIER_BUDGETS to 600/700/750/950/1000,
   yet the philosophy templates §6 was set with stem/choice per-field caps
   computed *independently*. The two specs were never reconciled.

2. **Practical: the gate fails for many questions, but the bank ships
   anyway** — judgment calls about scaffolding-over-compression override
   the deterministic budget at human review. This is the geography pre-
   2026-05-23 pattern: pipeline gate present, exemplars exceeded, bumped.

### Timer asymmetry — philosophy can support GENEROUS budgets
- **Philosophy timer**: 50 + 1.5×WIS = **65s @ WIS 10** (player.py:26)
- **Geography timer**: 28 + 1.2×WIS = **40s @ WIS 10** (geography rebuild
  base; player.py:22)

If we hold reading-speed ~30 chars/sec (skim-pace for a 14-year-old):
- Geography 40s × 30 = 1,200 chars max per question — geography canonical
  caps at 1,000 in T5 (comfortable)
- Philosophy 65s × 30 = **1,950 chars max per question** — philosophy
  canonical caps at 1,000 in T5 (very tight for the timer)

Philosophy has **62% more reading time than geography**. The canonical caps
should be EQUAL TO OR GREATER THAN geography's at every tier; currently they
are equal or LOWER (T1 600 vs geography 500 = higher only at T1; T5 1000 vs
geography 1000 = equal). The timer asymmetry justifies a generous bump.

### Recommendation

**Recalibrate philosophy SUBJECT_TIER_BUDGETS to match the per-field templates
§6 caps**, which equal the implied stem+4×choice totals:

| Tier | Current canonical | Templates §6 implied | Proposed canonical | Rationale |
|---:|---:|---:|---:|---|
| T1 | 600 | 660 | **660** | Templates §6 cap; bank avg ~530, leaves headroom |
| T2 | 700 | 770 | **770** | Templates §6 cap; bank often hits 700-750 (right at canonical edge) |
| T3 | 750 | 930 | **930** | Templates §6 cap; bank often hits 850-950 (over canonical) |
| T4 | 950 | 1100 | **1100** | Templates §6 cap; bank often hits 950-1100 (over canonical) |
| T5 | 1000 | 1320 | **1200** (or full 1320) | Templates §6 cap is 1320; bank hits 1100-1400. Could go full 1320, but 1200 covers >95% with reading-comfort margin. |

These match the templates per-field × 4-choices math. The 65s timer easily
supports them (analytical ceiling ~1,950 chars per question — comfortable for
1320). If the user wants a tighter analytical ceiling (e.g., chain target 2
questions per timer cycle), divide the analytical ceiling by chain target:
~975 chars/question at chain 2 — but that's the OPPOSITE direction from where
the bank is.

**Alternative — reconcile down**: if the canonical 600/700/750/950/1000 is
intentional and the templates §6 was an oversight, *most of T3-T5 needs
trimming*. ~200-300 questions would need rewriting to fit. Per
[[feedback_no_delete_validated_content]], "Don't trim gate-passing curated
content for an aesthetic histogram." The bumping direction is correct here.

**Open question for the user**: which spec is authoritative — the templates
§6 per-field caps (which the bank was authored against) or the DEFAULT_TIER_
BUDGETS that haven't been updated since 2026-05-11? They've been silently
inconsistent for ~2 weeks. The bumping fix aligns canonical with templates.

---

## 2. Context uncap

### Current cap
Per `PHILOSOPHY_TEMPLATES.md` §6: T1≤250, T2≤290, T3≤340, T4≤400, T5≤480.
(The scratch gate `philosophy_structural_gates.py` does not enforce context
length — it's a templates §6 spec only. The canonical pipeline gate
`validate_length_budget` only counts question + choices, not context.)

### Distribution (full bank, regex-counted)
- ≥ 100 chars: **882/882** (100%)
- ≥ 150 chars: **880/882** (99.8%)
- ≥ 200 chars: **767/882** (87%)
- ≥ 250 chars: **564/882** (64%)
- ≥ 300 chars: **220/882** (25%)
- ≥ 350 chars: **56/882** (6%)
- ≥ 400 chars: **4/882** (0.5%)

Caps in templates §6 are 250/290/340/400/480. Only 4 questions exceed 400 —
not a single context bumps the T5 cap of 480, and only ~4 hit T4 cap of 400.
Contexts cluster at 200-300 chars, suggesting authoring against the caps,
**not** that the content has nothing more to say.

### Qualitative read — context patterns
Sampled T4 and T5 contexts. Pattern: contexts NAME the source but TRUNCATE
the argument. Examples (from existing T5 questions):

- T5 line 2160: "Higher-order evidence (David Christensen 2010, Maria
  Lasonen-Aarnio 2014) is evidence about whether one's first-order evidence
  has been correctly evaluated. Its existence complicates Bayesian updating,
  because it doesn't change first-order probabilities directly." [stops at
  ~260 chars — Christensen's distinctive contribution to the conciliationist
  vs steadfast debate, unmentioned]

- T5 line 2196: "The chicken-sexer case is from BonJour and others arguing
  against externalism: process reliability isn't enough without internal
  justification. Reliabilists (Goldman, Process Reliabilism, 1979) reply
  that the case actually establishes their view. Conee and Feldman defend
  evidentialism in Evidentialism (2004)." [~340 chars; three names dropped
  in last sentence with no transmitted argument]

- T5 line 1008: "Arthur Danto's 'The Artworld' (Journal of Philosophy, 1964)
  and The Transfiguration of the Commonplace (1981) respond to Warhol's
  Brillo Boxes (1964) by arguing the art/non-art distinction cannot be
  perceptual. Danto's view shaped Dickie's institutional theory; the two
  diverge on whether artworld is interpretive (Danto) or institutional
  (Dickie)." [~370 chars — Danto vs Dickie distinction stated but not
  developed]

The cap forces the context to **name** sources but not **transmit** them.
That's a moral_vision §"Beauty of mechanism" / §"Curiosity over completion"
failure mode: the author had more to teach and the gate cut them off.

### Recommendation

**Uncap context per SHARED_PRINCIPLES §9.** Philosophy is the bank's deepest
history-of-ideas subject (Plato → Aquinas → Hume → Kant → Russell → Plantinga
chain woven throughout); context is the natural place to transmit primary-
source argument, not just primary-source NAMES. Capping it produces shallow
educational depth, which conflicts with moral_vision.md §"Curiosity over
completion."

**Implementation**:
- Update `PHILOSOPHY_TEMPLATES.md` §6 to mark context as uncapped, retain
  stem/choice envelopes
- Update `PHILOSOPHY_FRAMEWORK.md` tier sections similarly (cross-reference
  geography's pattern)
- Continue capping stem + choices per recalibration in §1
- No change to `philosophy_structural_gates.py` required (it doesn't gate
  context length)
- No change to `length_budget.py` required (it doesn't gate context either)

The cap was never enforced computationally — it lived only in
`PHILOSOPHY_TEMPLATES.md` §6 — but authors evidently respected it. Removing
it from the spec is the actionable change.

---

## 3. Decoration mismatch (broader than em-dash)

### Existing coverage
- `gate_choice_shape_parity` in `philosophy_structural_gates.py` lines
  128-141 — catches the classic em-dash skim-tell (only correct answer has
  the dash structure).

### Citation skim-tells (year-in-correct-answer-only)
Searched for `(YYYY)` patterns in answer text:

- Choices opening with `(1[5-9]\d{2})` or `(20\d{2})` years in the correct
  answer: **6 hits** (lines 1085, 10385, 10421, 10469, 10493, 10541) — all
  spot-checked and **decoration is parallel within the question**:
  - Line 10385 "Free-will defense — Plantinga (God, Freedom, and Evil,
    1974)..." — distractors at 10388-10390 each carry "(book + year)" too
    (Hick 1966, Bergmann, Augustine). Parallel.
  - Line 10493 "Pascalian wager — Pascal (Pensees, 1670)..." — distractors
    each cite a book or critic. Parallel.

### Parens-with-content (only-in-correct-answer)
Searched answers for `(...)` patterns ≥ 15 chars of content:

- **88 questions** have parens-with-content in the answer. Spot-checked
  10+ — in ALL cases, the other choices use parallel parens or the same
  general structure (e.g., when correct answer has "Aesthetic realism —
  real qualities (depth, craft, structure)...", the other three choices
  also use the "[Name] — content (parenthetical detail)" structure).
- Pattern is consistent across the bank because philosophy was authored
  with strict "[Name] — definition" parallel-structure discipline.

### Decoration-type sample table

| Q (line) | Decoration | Status |
|---|---|---|
| 100 (T1) | Aesthetic realism — real qualities (depth, craft, structure)... | All 4 choices use parens or parallel | OK |
| 1084 (T5) | Formalism — Bell (Art, 1914)... | Distractor at 1088 has "Expressionism — Collingwood (Principles of Art, 1938)..." — Parallel | OK |
| 7920 (sampled) | Multi-clause answer with quoted phrase | Other choices share quoted-phrase shape | OK |

### Verdict
**LOW concern.** Philosophy's parallel-structure discipline is the strongest
in the bank — the templates §5 fallacy-question shape "[Name] — explanation"
applied universally, and the author-time double-assert rule (FRAMEWORK §11)
catches shape divergence. No broader-than-em-dash gate needed. The 4-7
citation-year-in-correct-answer-only cases are likely false positives
because the distractors carry parallel citations of OTHER scholars.

No corrective action required.

---

## 4. Wonder-in-stem (vs context-deferred)

### Philosophy-specific risk pattern
Geography's failure mode: stem describes wondrous named feature, then asks
for a rote proportion/number/date with the wonder in context. The
philosophy analog would be: stem names a thought experiment / philosophical
puzzle, then asks for "what year did X say Y?" or "how many of them held
this view?" or similar rote-recall closer.

### Empirical sweep
Searched stems for date-recall closers: `What (year|date|century|decade)`,
`In what year`, `Who (wrote|invented|founded|composed|taught) (this|that|it)`:
- **Zero matches** in philosophy stems. The PHILOSOPHY_FRAMEWORK.md §
  "What this framework forbids" #2 ("Definition recall") and the
  `BANNED_NAMES` rule in §11 explicitly prohibit name-in-stem. The bank
  is structurally clean on this axis.

### Sampled "scene-led wonder" vs test-something-specific
- T2 (line 280, aesthetics): "Arguing about a famous album, Theo says: 'Sure,
  taste differs. But critics who've listened to thousands of records tend
  to agree about the great ones. That agreement tracks something real.'" —
  wonder (Hume's convergence puzzle) is in stem; test is "which view is
  Theo defending."
- T5 (line 2176, epistemology): "A philosophy student is told to strip away
  every belief that could conceivably be the product of a systematic
  deception..." — wonder (Cartesian doubt) is in stem; test is "what would
  still be certain."
- T1 (line 5656, sorites): "The Sorites paradox: one grain isn't a heap.
  Adding one grain never turns a not-heap into a heap. Yet a million grains
  IS a heap." — wonder (the paradox itself) is in stem; test is which view
  the puzzle presses.

### Verdict
**LOW concern.** Zero matches on the geographic-style "rote-recall-while-
wonder-in-context" pattern. Philosophy is structurally clean here — its
"scene-led" discipline (FRAMEWORK §"What this framework REQUIRES") was
established at the original rebuild and held.

No corrective action required.

---

## 5. Steelman distractors

### Sample size
~50 questions sampled across all 5 tiers (T1 aesthetics + T1 identity + T1
fallacy + T2 epistemology + T3 ethics + T3 political + T4 epistemology + T5
philosophy of art + T5 epistemology + T5 religion).

### Philosophy-specific bad-distractor patterns audited
- **"X is mythology / Cold War fiction / nonsense / made up" formulaic
  dismissals**: regex sweep over the bank — **21 hits** but **ZERO are bad
  distractor patterns**. All 21 hits are legitimate uses:
  - "useful fiction" — Hume's deflationary view, modal fictionalism,
    no-self view (each is a real philosophical position called by its
    proper name, not a dismissal)
  - "nonsense" — Bentham's actual quote about natural rights ("nonsense
    upon stilts" — Legal positivism)
  - "is fiction" — modal fictionalism (Rosen 1990, a real metaphysical
    position)
- **"the case is malformed" / "the question is absurd"**: 2 hits at lines
  2110 (BonJour clairvoyance, properly framed as a real possible objection)
  and 7654 (category-mistake reply, properly framed). Both are real
  philosophical responses someone might genuinely give.
- **"the teacher is just dumb" / mockery-distractors**: zero.
- **Punchline-as-distractor** (per moral_vision §6): zero.

### Distractor quality observations
- **T1-T2 fallacy questions** (templates §5.1): distractors are "[Other
  fallacy name] — generic definition." Each is a real named fallacy a
  pedagogically alert student needs to be able to distinguish. Pedagogical
  closeness rule (distractors should be related to correct fallacy) is
  consistently respected — ad-hominem distractors include genetic fallacy
  and tu quoque, not motte-and-bailey.
- **T3-T5 ethics / political questions** (templates §5.2): distractors are
  "[Other ethical position name] — what THAT view says about this case."
  Each is the genuine view of a real philosophical tradition (Rawlsian
  vs Nozickian vs Hayekian vs Communitarian — all four steelmanned with
  inline definitions).
- **T5 epistemology / mind**: distractors at line 2167-2170 (forecaster /
  broken weather station) are real epistemological responses: JTB still
  satisfied (reasoning), reliabilism on track-record (Goldman), pure
  "ordinary observation" rejection. Each is a real position someone has
  defended.

### Samples (steelman quality — all PASSING)

| Q (line) | Topic | Why steelmanned |
|---|---|---|
| 100 (T1) | aesthetic value | Subjectivism / Cultural relativism / Convention theory — three real rival positions in aesthetics, each accurately summarized |
| 3676 (T1 fallacy) | Ad hominem | Distractors are Straw man / Bandwagon / Tu quoque — all real fallacies, all named correctly, each pedagogically close to ad hominem |
| 2008 (T4 epistem) | Reliabilism vs JTB vs internalist | All four distractors are real epistemological positions, each invoking a real defeater concept (undercutting / accessibility / process reliability) |
| 8500 (T3 political) | Classical liberalism vs Communitarianism vs Hobbesian vs Civic republicanism | All four are real Western political philosophy traditions, each with a named historical defender |
| 10385 (T5 religion) | Free-will defense | Distractors are Soul-making theodicy / Skeptical theism / Privation theory — all real responses to the problem of evil with named defenders |

### Verdict
**LOW concern.** Steelmanning is the strongest axis of the philosophy bank.
Distractors are uniformly real philosophical positions accurately described.
The "viral test" (moral_vision §7) — would an opposing-school philosopher be
embarrassed by the distractor description? — passes easily. No corrective
action required.

---

## 6. Theory-stacking (especially relevant for philosophy)

### Existing coverage
Philosophy's `inline_teaching` judgment gate (PHILOSOPHY_TEMPLATES.md §8.2)
is the equivalent of geography's deterministic `no_theory_stacking_check`.
Per SHARED_PRINCIPLES.md §1 both implement the same universal principle.

### Empirical sweep — multiple `-ism` in stem
Searched stems for two `-ism` tokens:
- **3 hits total** (lines 8500, 8848, 8884) — all at T3-T4.

Each was inspected. Verdict:

| Line | Stem opener | Tier | Anchor? | Verdict |
|---|---|---:|---|---|
| 8500 | "A debate-club captain argues: 'The state may use force only to prevent harm to others...'" — uses "Lockean liberalism vs Hobbesian absolutism" implicitly via her position-defended | T3 | Has quoted speech + named character; choices define each "-ism" inline | OK |
| 8752 | "A panel debates whether a regime that retains power but has stopped protecting basic rights is still legitimate. Lockean liberalism and Hobbesian absolutism give different answers." | T4 | Both -isms appear in stem WITHOUT inline definition; the definition appears in CHOICES | **Borderline** — relies on choices to define; templates §3 vocabulary policy says this is OK for T4 |
| 8848 | "Two traditions disagree on when the state may legitimately coerce its citizens. Hobbesian absolutism grounds coercion in the prior need for order; Millian liberalism restricts it to preventing harm to others." | T4 | Both -isms appear with inline definition in stem ("grounds coercion in..." / "restricts it to...") | OK — teaching is inline |
| 8884 | "Rawlsian contractualism and Nozickian libertarianism give different verdicts on a society with large income inequalities that arose through legal acquisition and transfer." | T4 | -isms named but NOT defined inline; definitions appear in answer + first distractor | **Borderline** — same pattern as 8752 |

### Sampled at T5
At T5 the bank often references named positions (Reliabilism, Internalism,
Contextualism, Sensitivity, Safety, Fallibilism, etc.) but per templates §3
the T5 vocabulary policy allows specialist terms with parenthetical or
choice-based definition. Sampled T5 questions at lines 2008-2160 all
provide inline definitions in either stem or first-correct-choice.

### Verdict
**LOW concern.** Philosophy's `inline_teaching` judgment-gate model and the
templates §3 vocabulary policy (each used-term must be either defined inline
OR derivable from context) is being respected. The 2 borderline T4 cases
(8752, 8884) push the definition into choices rather than stem — defensible
under templates §3 but could be tightened by inline-defining one of the two
in the stem. Total of 0 hard fails out of ~370 T3-T5 questions.

### Recommendation
Optional follow-up: at the next philosophy generation pass, prefer the
"position-defended with quoted character speech" pattern (templates §4.1
Pattern A) over the "X-vs-Y comparison" pattern at T4, when both views are
named. The former auto-anchors via the character + quote; the latter relies
on the reader to absorb both -isms before reading choices.

---

## 7. Register consistency

### Existing coverage
Philosophy's `register_consistency` gate (`philosophy_structural_gates.py`
lines 421-443) checks for specialist vocabulary in choices at tiers below
the word's min_tier.

### Empirical sweep
The gate's SPECIALIST_VOCAB dict (line 421-428) includes physicalism (T4),
eliminativism (T5), qualia (T4), hermeneutic (T5), epistemic (T4),
dialectical (T4), noumenon (T5), haecceity (never), quiddity (never),
consequentialism (T3), deontology (T3), contractualism (T4), intentionalism
(T4), eternalism (T4), presentism (T4).

Sampled regex searches across T1-T2 for these terms:
- **physicalism** at T1: 0 hits (sampled — none in T1 stems or choices)
- **epistemic** at T1-T2: appears only in context (T2 line 1524, etc.) —
  not in stems or choices
- **dialectical** at T1-T2: 0 hits in choices
- **noumenon** at T1-T2: 0 hits

### Spot-check at T3-T4
- **consequentialism / deontology** at T3-T4: defined inline when used
  (e.g., line 8651 "Utilitarian justice — distributions are just when they
  maximize aggregate good" — defines utilitarianism without using the
  bare -ism term)

### Verdict
**LOW concern.** Register consistency is well-controlled. The existing gate
catches violations; sampling confirms no hits. No corrective action
required.

---

## 8. NEW finding — Wonder-bias scenery half-applied (stem ≠ answer mismatch)

### Discovered during audit (not on the original audit list)
While sampling the T1-T2 fallacy block (lines 3674-4400 approx), I found a
pattern of **stem rewritten with canonical wonder-bias scenery, but the
answer (and sometimes distractors) still referencing the original mundane
modern scenery**. This is a content bug from a partial wonder-bias upgrade
pass.

### Concrete instances (sampled — partial enumeration)

| Line | Tier | Stem scenery | Answer scenery | Status |
|---:|---:|---|---|---|
| 3736 / 3737 | 1 | "Standing watch with the night-guard, Riley tells the company: 'Either we tell the ghost-story tonight, or the whole vigil is ruined.'" | "False dilemma — Riley pretends the **sleepover** is either **scary-movie**-tonight or ruined." | **MISMATCH** |
| 3760 / 3761 | 1 | "Tess insists her **alchemist's tonic** is healthy because her favorite **bard** sings of drinking it from the great market." | "Appeal to authority — Tess takes the **pop star's commercial** as proof her **energy drink** is healthy." | **MISMATCH** |
| 3784 / 3785 | 1 | "When the captain asks why Marcus skipped two **squire-training drills**, Marcus answers: 'Well, Jake forgot his **sword** last Tuesday...'" | "Red herring — Marcus drags Jake's forgotten **cleats** in to dodge the question about skipped **practices**." | **MISMATCH** |
| 3868 / 3869 | 1 | "Eli tries one bite from a new **tavern in the realm** and declares: 'This whole tavern is terrible.'" | "Hasty generalization — Eli judges the whole **restaurant's menu** from a single slice of **pizza**." | **MISMATCH** |
| 3904 / 3905 | 1 | "Trying to skip his **stable duties**, Max tells the **steward**: 'Either I get to ride at the **quintain** right now, or you don't actually love me.'" | "False dilemma — Max squeezes the **chores** question into either **video games** right now or 'you don't love me.'" | **MISMATCH** |
| 4012 / 4013 | 2 | "Asked why she wants to attempt the **rope-walk between the high towers**, Tess shrugs: 'Every traveling **minstrel** sings of it, and the **heralds** all approve...'" | "Bandwagon — Tess treats the challenge's **TikTok** popularity and comment count as evidence..." | **MISMATCH** |
| 4036 / 4037 | 2 | "Planning the **watch-night vigil** in a sealed missive, Riley writes: 'Either we tell a **ghost-story** or this whole weekend is officially RUINED...'" | "False dilemma — Riley squeezes the whole **sleepover** into either **horror-movie**-tonight or 'ruined,' hiding every other plan." | **MISMATCH** |
| 4048 / 4049 | 2 | "The **squire-captain** Ben warns that letting one **trainee help themselves to a fair-day honey-cake** without paying would somehow snowball into the whole **company** stealing food from every market the rest of the year." | "Slippery slope — Ben treats one **unpaid cookie** as if it must trigger year-long, **class-wide fundraiser** stealing." | **MISMATCH** |
| 4060 / 4061 | 2 | "Trying to convince her parents about a new **alchemist's tonic**, Layla holds up the **flask** and announces: 'A **famed actor swears by these between epic verses at court**, so they obviously must work.'" | "Appeal to authority — Layla takes a **podcasting actor's** say-so on **supplements** as proof the **pills** actually work." | **MISMATCH** |
| 4228 / 4229 | 2 | "By sealed letter, Wesley drops a wild claim to his fellow **squires**: 'There's a **secret tunnel under the citadel**.'" | "Burden of proof — Wesley pushes the work of proving the **gym tunnel** onto skeptics..." | **MISMATCH** |
| 4276 / 4277 | 2 | "Trying one bite from a new **tavern in the realm**, Theo declares to his household **by messenger**: 'This whole **tavern** is awful — NONE of their food is worth eating, ever, by anyone.'" | "Hasty generalization — Theo jumps from a single **pizza** slice to a sweeping verdict about every dish on the whole **restaurant's menu**." | **MISMATCH** |
| 4336 / 4337 | 2 | "Asked about a thoughtful idea for the **company's market fund**, Jordan sneers in his sealed reply: 'That idea came from the **squire who never even joined our company last year**...'" | "Genetic fallacy — Jordan rejects the **fundraiser idea** based on its source (a **kid who skipped last year**) instead of its merits." | **MISMATCH** |

### Estimated total scope
Based on this pattern's clustering in the T1-T2 fallacy blocks at lines
3674-4400, I estimate **15-25 questions** show this stem/answer scenery
mismatch. A scripted full-bank scan looking for {pop star, smartphone, TikTok,
sleepover, pizza, cleats, fundraiser, gym tunnel, video games, podcasting,
supplements} appearing in answers when {squire, knight, tavern, alchemist,
bard, herald, monastery, citadel, scriptorium, paladin, chapter-house,
quintain} appear in the same question's stem is the precise way to confirm
the count.

### Why this matters
**Content bug, not style preference.** The player reads the stem (which
describes an alchemist's tonic), then reads the correct answer which says
"pop star's commercial / energy drink" — the answer no longer matches the
scenario. At minimum it's confusing; at worst it suggests the correct answer
might apply to a different question entirely. The pedagogical contract — the
answer explains WHY this scenario commits THIS fallacy — is broken.

This is consistent with [[feedback_wonder_bias]] noting that scenery upgrades
must keep logic intact. The bug appears to be an incomplete upgrade pass:
stems were rewritten; answers/distractors weren't visited.

### Recommendation

**MEDIUM-HIGH priority repair.** For each mismatched question:
1. Identify the wonder-bias-upgraded stem
2. Update the answer (and any distractors that reference the original
   modern scenery) to match the canonical scene
3. Verify the answer still correctly identifies the fallacy in the
   re-cast scenario

Example fix for line 3737:
- Before: "False dilemma — Riley pretends the sleepover is either scary-movie-tonight or ruined."
- After: "False dilemma — Riley pretends the vigil is either ghost-story-tonight or ruined."

This is a content-touching repair, not a structural change. ~15-25 questions
to fix. Could be done in a single session.

Also worth considering: was the wonder-bias upgrade applied consistently
across distractors too? Several questions sampled had distractors that
appeared mostly generic (which is the correct shape for fallacy distractors
per templates §5.1), but a few (e.g., line 4060) had wonder-bias-cast
distractors paired with modern-mundane correct answers — also a mismatch
worth checking.

---

## Quick wins

1. **Update DEFAULT_TIER_BUDGETS or add philosophy to SUBJECT_TIER_BUDGETS**
   in `length_budget.py` to match `PHILOSOPHY_TEMPLATES.md` §6 per-field
   implied totals (660 / 770 / 930 / 1100 / 1200-1320). Single-line edit
   per tier. Reconciles the two-spec inconsistency that's been silent for
   2 weeks.
2. **Update PHILOSOPHY_TEMPLATES.md §6** to mark context as uncapped, with
   cross-reference to SHARED_PRINCIPLES.md §9.
3. **Document the dual-cap-system divergence** in PHILOSOPHY_TEMPLATES.md
   so the next subject rebuild doesn't re-introduce it.
4. **Repair the 15-25 stem/answer scenery mismatches** in §8. Mostly T1-T2
   fallacy block (lines 3674-4400). Single editing session.

## Deeper concerns

**The 15-25 wonder-bias stem/answer mismatches in §8 are the only
content-touching findings.** Everything else (cap reconciliation, context
uncap) is configuration / documentation. The bank's reasoning content,
steelman quality, scene-led wonder-in-stem discipline, no-verdict-on-
contested compliance, and inline-teaching discipline are all sound.

If the user later wants to ADD scaffolding density to T1-T2 (parallel to
geography's "scaffolding > compression"), that's an additive expansion and
the cap recalibration would unlock it.

## Cross-bank lessons (suggested updates to SHARED_PRINCIPLES.md)

1. **Lift the "wonder-bias scenery upgrade must be applied to BOTH stem and
   answer" rule** to a new principle in SHARED_PRINCIPLES.md §6 ("Wonder-
   bias / scenery aesthetic"). Currently §6 says "Logic stays, scenery
   upgrades" — but doesn't explicitly say "scenery upgrade applies to ALL
   four fields: stem, answer, three distractors, context." This audit
   found the bug because the upgrade pass missed answers/distractors.
   The principle: *"A wonder-bias scenery upgrade is incomplete if it
   touches the stem but leaves any of {answer, distractor 1, distractor
   2, distractor 3, context} using the original scenery. The four-field
   parity check should be part of any bulk scenery upgrade."*

2. **Confirm the "two caps systems diverge" failure pattern is now
   universal** (geography 2026-05-23, cooking 2026-05-24, philosophy
   2026-05-24 — three subjects in a row). Update SHARED_PRINCIPLES.md §10
   to explicitly call this out as a recurring pattern, with the
   reconciliation rule: *"When a subject has BOTH a per-field cap in
   templates §6 AND a total-budget cap in `length_budget.py` SUBJECT_TIER_
   BUDGETS, they MUST be reconciled to one source of truth — typically
   total-budget as operative, per-field as advisory."*

3. **Status of context-uncap rollout (§9)**: geography done 2026-05-23,
   cooking flagged 2026-05-24, philosophy flagged 2026-05-24 (this audit),
   animal flagged 2026-05-24. All three pending subjects identified the
   cap as latent (not currently hurting depth) but not pulling its weight
   either. Recommend a single batch update of {cooking, philosophy, animal}
   to uncap context across all three.

4. **Status of universal-implementation gaps**: this audit confirms
   philosophy is structurally clean on the decoration-mismatch axis, the
   wonder-in-stem axis, theory-stacking, register consistency, and
   steelman distractors. The SHARED_PRINCIPLES.md "Open universal-
   implementation gaps" section lists "Philosophy/Animal/Cooking:
   decoration mismatch only partial — citation skim-tell, not parens/
   quotes/lists" — this audit shows philosophy's parens/quotes/lists ARE
   already in parity, just not by an explicit deterministic gate. The
   gap is documentation-only, not enforcement.

## Files referenced

- Bank: `data/questions/philosophy.json` (882 questions)
- Canonical gate: `tools/quizgen/deterministic/length_budget.py` lines
  22-28 (philosophy uses DEFAULT_TIER_BUDGETS = 600/700/750/950/1000)
- Scratch gate: `tools/quizgen/scratch/philosophy_structural_gates.py`
  (8 deterministic + heuristic gates)
- Docs: `proposals/v2_audit/PHILOSOPHY_FRAMEWORK.md` +
  `proposals/v2_audit/PHILOSOPHY_TEMPLATES.md`
- Shared: `proposals/v2_audit/SHARED_PRINCIPLES.md` (§9 context uncap,
  §10 cap calibration)
- Geography reference: `proposals/v2_audit/GEOGRAPHY_TEMPLATES.md` §6
  (length envelopes after 2026-05-23 bump)
- Timer source: `src/player.py:12-30` (SUBJECT_TIMER) —
  philosophy `(50, 1.5)` → 65s at WIS 10
- Moral vision (supreme): `docs/quiz/moral_vision.md`
- Wonder bias memory: [[feedback_wonder_bias]]

## Final note on audit method

This audit was performed read-only without script execution (sandbox
constraint). Distributional claims (stem-length histograms, decoration
counts, distractor patterns) are from regex sweeps over the JSON; per-tier
totals are hand-counted from ~5-8 representative questions per tier. A
full scripted histogram of stem-char + total-char per tier is the
appropriate next step before the user commits to specific cap numbers.
The {660, 770, 930, 1100, 1200} recommendation matches the templates §6
per-field implied totals, which were the spec the bank was authored
against; the analytical math (65s timer × ~30 chars/sec = ~1,950 chars
ceiling) easily supports them. If the user wants a tighter or looser
target, the analytical and empirical numbers are both in §1 above.

The §8 stem/answer scenery mismatch finding (~15-25 questions) is the
most actionable. A scripted scan looking for {pop star, smartphone,
TikTok, sleepover, pizza, cleats, fundraiser, gym tunnel, video games,
podcasting, supplements, snack} in answers when {squire, knight, tavern,
alchemist, bard, herald, monastery, citadel, scriptorium, paladin,
chapter-house, quintain, vigil, watch} appear in the same question's
stem is the precise way to confirm the full count.
