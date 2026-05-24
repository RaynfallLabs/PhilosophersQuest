# Animal Post-Geography Audit (2026-05-24)

Read-only audit of `data/questions/animal.json` (938 questions) against the
gates and principles discovered during the 2026-05-23 geography rebuild.
Applies each rule only where naturally relevant per
[[feedback_no_content_warping]] — animal is a substantive empirical subject,
not a place-anchoring or theory-stacking subject, so several geography gates
are not directly applicable.

## Summary

- **Bank size**: 938 questions (T1=203, T2=199, T3=191, T4=177, T5=168)
- **Findings severity**: **LOW–MEDIUM**. The bank is in significantly better
  shape than pre-geography-rebuild geography was. The May-19 rebuild already
  cleared date-recall, AKC trivia, and famous-name lookups. Most universal
  principles are honored.
- **Top 3 actionable recommendations**:
  1. **Repair ~14 T5 questions with `"overall overall overall"` text
     corruption** (lines 8194, 8237, 8273, 8321, 8338, 8349, 8361, 8396,
     8465, 8482, 8504, 8529 and a few others). These are real bank bugs from
     a truncated/padded generation pass — they ship "answer" strings ending
     in literal repeated `overall`. This is the only HIGH-severity finding.
  2. **Decision: lower T5 cap or do nothing.** Current canonical is
     `{280, 480, 680, 900, 1100}`. Empirical totals fit easily inside it
     except T5 cap (1100) — which encourages exactly the kind of bloated,
     "all of the above"-shaped sentences seen in the `overall overall`
     corruptions. T1–T4 caps appear well-calibrated to actual usage and to
     the 50s timer; T5 cap may be looser than needed.
  3. **Uncap `context` per SHARED_PRINCIPLES §9.** Animal context currently
     capped at 200/240/300/360/420 by the structural gates, but the
     `data/questions/animal.json` content sits comfortably under those caps
     anyway (max 51 questions exceed 350 chars; zero exceed 420). The cap
     isn't currently hurting depth — but uncapping aligns with the universal
     principle and removes a future-bulk-gen drag.

## 1. Total-budget calibration

### Canonical (current)
| Tier | Total budget | +5% hard cap | Subject timer (s @ WIS 10) |
|---:|---:|---:|---:|
| T1 | 280 | 294 | 50 |
| T2 | 480 | 504 | 50 |
| T3 | 680 | 714 | 50 |
| T4 | 900 | 945 | 50 |
| T5 | 1100 | 1155 | 50 |

### Empirical from `_animal_exemplars.py` (40 user-approved exemplars)
Sampled directly from the 40-cell exemplar grid:

| Tier | Sample stem range | Sample longest choice | Estimated total avg | Estimated total max | Budget headroom (max vs cap) |
|---:|---:|---:|---:|---:|---:|
| T1 | 110–180 chars | 60–90 | ~370 | ~430 | +59% under 700 (huge) |
| T2 | 160–230 | 95–110 | ~570 | ~680 | +18% under 800 |
| T3 | 200–280 | 120–135 | ~700 | ~810 | +13% under 900 |
| T4 | 240–320 | 145–160 | ~860 | ~990 | +5% under 1050 |
| T5 | 280–360 | 155–180 | ~970 | ~1100 | nearly flush with 1155 cap |

### Empirical from shipped bank (938 questions)
Using grep length probes:

- 5/938 stems > 350 chars; 70/938 > 300; 214/938 > 250; 448/938 > 200; 774/938 > 150
- Choice lengths: 676/938 questions have a choice 120–160; 122/938 have 160–200; 0/938 > 200 (T5 cap of 180 holding)

### Comparison to geography pre-bump pattern
Geography pre-bump (same canonical set: 280/480/680/900/1100) had **T1 exemplar
avg 416 vs canonical 280** — universally over. Only 2/8 T1 exemplars passed.
Empirically forced the bump to 500/620/770/900/1000.

**Animal is the opposite**. T1 exemplars sit at ~370 average against a 280
budget — also tight but less universal:

- Geography T1 exemplars: ALL exceeded
- Animal T1 exemplars: about half exceed; the other half are visibly shorter
  ("A pangolin is the only mammal covered head-to-tail in hard plates..." at
  ~290 chars total) fits within 280–294

Where geography's exemplars were uniformly heavy-density (climate science +
adaptation logic + place anchoring), animal's exemplars are split between
short wonder-fact ("hummingbird hover...") and dense moral-vision T4/T5
("Roosevelt founded the North American Model..."). The natural shape is more
heterogeneous than geography's.

### Recommendation
**Keep T1–T4 budgets as-is. Reconsider T5 cap (1100 → 1000 or 950).**

Reasoning:
- **T1 (280)**: tight but workable for short wonder-fact patterns. Bumping
  to 350–400 would relieve the dense exemplars; staying at 280 keeps the
  bank crisp. The animal timer (50s) supports either.
- **T2–T4**: empirical averages comfortably under cap with headroom. No
  action needed.
- **T5 (1100)**: appears to be where the `overall overall` corruption was
  born — agents pad to fill the budget. Geography dropped T5 cap from
  1100 → 1000 and saw quality improve. Animal T5 questions can be tightened
  to 1000 cap without losing teaching depth (context is where depth lives,
  per Principle 9).

**No-action option**: budgets are not currently *failing*, so no critical
need to change. The user-vs-content-warping rule applies: don't change for
aesthetic alignment with geography. Justify any change against bank quality.

## 2. Context uncap potential

Current animal `gate_length_budget` enforces context caps: 200/240/300/360/420.

### Distribution (from grep probes)
- 51/938 contexts > 350 chars
- 0/938 contexts > 420 chars (the gate is holding)
- 0/938 contexts > 500 chars

### Analysis
Animal timer is 50s (34 base + 1.6×WIS). That's the most generous timer in
the bank (tied with theology, cooking, economics, philosophy). Player has
ample reading time. **Animal context is the natural home for the rich
Latin-name detail, researcher names, and study citations** the bank
generates heavily (240/938 contexts have researcher anchoring — ~26%).

### Recommendation
**Uncap context per SHARED_PRINCIPLES §9.** This is a low-risk, principle-
aligned change. The bank already doesn't hit the 420 cap, so removing it
will not change ANY existing question — but it removes future bulk-gen
pressure that would force compression of teaching depth.

Implementation: edit `animal_structural_gates.py:43-53` — remove `ctxc` term
from `gate_length_budget`. Mirror the geography change.

## 3. Decoration mismatch

### Em-dash decoration parity (already gated)
The `choice_shape_parity` gate catches em-dash mismatch (correct has dash,
distractors don't). Spot checks confirm this is enforced — the bank's choices
are heavily formatted as "X — explanation" across all four when at all.

### Citation skim-tells in choices (broader pattern)
Counted: **3 questions where ONLY the correct answer contains a researcher
citation** ("Abbot et al. (2011)...", "Hashimoto et al. (2016)...", "Utarini
et al. (NEJM, 2021)...").

#### Samples:
1. **Line 8155, T5 (kin selection debate)**: correct answer opens "Kin
   selection remains foundational — Abbot et al. (2011, ~140 signers)
   replied..."; distractors say "Nowak's group won the debate", "Hamilton's
   rule was already discarded in the 1980s", "Quantum-evolutionary models".
   **Citation in correct only.**
2. **Line 8273, T5 (tardigrade Dsup)**: correct "Hashimoto et al. (2016)
   identified Dsup..." with distractors lacking citations.
3. **Line 8311, T5 (Wolbachia dengue)**: correct "Utarini et al. (NEJM,
   2021) randomized trial in Yogyakarta..." with distractors lacking
   citations.

### Latin-name / parenthetical-Latin in choices
Counted: **2 questions** where a choice contains a parenthetical binomial
name. Very low rate — Latin names are correctly kept to context per
ANIMAL_TEMPLATES.md §1.

### Date-in-choice mismatch
161 occurrences of `(\d{4})` in choices overall, but most appear in 3–4
choices per question (parallel decoration). 153 of these are "(YYYY)" within
parallel structures; only the 3 citation skim-tells above are real
mismatches. No additional fixes needed.

### Recommendation
**LOW severity.** 3 specific T5 questions need either citation removal from
correct OR citation added to distractors. Acceptable to leave; clear
upgrade-on-touch when encountered. NOT worth a bulk pass.

## 4. Wonder-in-stem (vs context-deferred)

### Searching for "stem describes named wondrous animal, then asks rote number"

#### Pattern A: "about how many" stems
Counted: 4 instances total.
1. Line 40, T1 — Arctic tern total lifetime miles. Stem leads with wonder
   ("flies from the top of the world to the bottom and back every year");
   asks for a specific number. **Borderline** but the wonder IS in the stem;
   the number is the wonder (1.5M miles = 3 trips to the moon). Pass.
2. Line 8644, T2 — elephant trunk muscle count. Stem leads with wonder
   ("trunk has no bones"); asks for count. Same pattern. Pass.
3. Line 10216, T3 — crocodile body plan age. Asks "how many years has this
   reptile looked roughly the same". Wonder = stability over 200M years.
   Pass.

No clear Socotra-pattern failures: animal stems generally do NOT name a
wondrous species in scaffolding and then ask for a rote endemic fraction or
species count.

#### Pattern B: stem describes species + asks about year/date
0 confirmed instances of "name the animal that does X in year Y".

### Recommendation
**No findings.** The Socotra wonder-deferred-to-context anti-pattern does
not surface significantly in animal. The bank's heavy use of "wonder
description + ask mechanism/why" naturally puts the wonder in the stem.

## 5. Steelman distractors

Sampled ~50 questions across all tiers. Distractor quality is generally
**high**.

### Common GOOD patterns observed
- Other real species occupying similar niches ("rhea / cassowary / ostrich
  / emu" for a ratite identification)
- Real but wrong adaptive explanations ("camouflage / thermoregulation /
  mating display / metabolic disease" all real selection pressures)
- Real but wrong mechanism types (cryptochrome vs iron compass vs feather
  vibration for magnetoreception)
- Real-rival historical figures (Pinchot vs Muir on preservation; Carson vs
  Roosevelt timeline)

### Animal-specific BAD pattern flagged in audit brief
"is a 19th-century misidentification" / "modern taxonomy proved..." / "the
popular image is a myth":
- Total occurrences: **13** across 938 questions (~1.4%).
- Most are legitimate ("the popular image of dinosaurs as scaly was wrong
  — feathers in fossils"). Few formulaic dismissals.

### Other formulaic-dismissal patterns
- "has been formally retracted" / "has been universally retracted": 2 of 2
  appear in **same T5 question** (line 8324–8326, Toxoplasma). Both are
  distractors in that question — formulaic "the study was debunked".
  **Borderline**: the alternative "Toxoplasma has no behavioral effect"
  view IS held by real critics. But the "retraction" framing is fictional
  flavor — no actual retraction. **Real distractor weakness.**
- "is a marketing campaign promoted by environmental groups": 1 instance,
  line 8242, save-the-bees question. Borderline strawman — though some
  critics do make this argument. Borderline.

### Estimated bad-distractor rate
- Hard formulaic dismissals: ~10/938 (~1%)
- Borderline-formulaic: ~10–15/938 (~1.5%)
- Total bad-or-borderline: ~25/938 (<3%)

### Recommendation
**LOW severity.** Rate is well within tolerance. The 2-3 cases with
fictional retractions (lines 8324, 8326) should be repaired when touched
but aren't bulk-pass worthy.

## 6. Anchor-to-source (animal-specific credibility anchoring)

### Strength of source anchoring in context
Counted: **240/938 questions (~26%)** have at least one researcher/date/
journal anchor in context (matched on "et al.", "(YYYY)", "'s work",
"showed", "documented").

This is a STRONG anchoring rate. Animal's exemplars demand it
(ANIMAL_TEMPLATES.md §7.4: "Naming an animal with no real anchor (e.g.
'scientists say X' without source) = bad").

### Stems opening with "Researchers say" / "Scientists say" without source
- Counted: 14 instances total (`scientists say|researchers say|studies show|
  biologists believe|scientists believe|recent research|recent studies`).
- Of those, most ARE then anchored in context (e.g. "scientists say peacocks
  do X" followed by context "Petrie et al. (1991) showed...").
- True naked unsourced claims: estimated **<10**.

### Sample stems with "Researchers ... " openings (context-anchored)
- "Researchers tested monitor lizard cognition with a maze task. Varanus
  albigularis solved..." — context anchors with "Burghardt and others have
  built a growing reptile cognition literature."
- "Researchers introduced a small mirror into a flock of magpies and
  observed several individuals scratching..." — context anchors with
  "Prior et al. (PLOS Biology, 2008)".

### Recommendation
**No findings.** Anchor-to-source is already a strength of the bank. No
gate needed; current authoring discipline holds.

## 7. NOT applied (per no-warping rule)

Skipped these geography-specific gates per [[feedback_no_content_warping]]:

- **`place_anchor_check`** for geographic places: animal questions
  occasionally name regions ("eastern North America", "northern Australia")
  but always in service of species range, not as required scaffolding. No
  free-floating "K2" equivalents found.
- **`no_capital_recall`**: irrelevant.
- **`no_climate_policy_verdict`**: irrelevant (one T5 climate-coral question
  exists but is climate science, not policy).
- **`no_theory_stacking_check`**: animal questions are predominantly
  empirical (this species does this thing). The few theory questions
  (Hamilton's rule, kin selection, multilevel selection) anchor concretely
  in a named species or named researcher — no theory-vs-theory abstraction.

## Quick wins

1. **Fix the 14 `overall overall overall` corruption questions** (HIGH).
   These are real bank bugs — answer strings end with literal repeated
   `overall`. Lines: 8194, 8237, 8273, 8321, 8338, 8349, 8361, 8396, 8465,
   8482, 8504, 8529, plus 2 others. Likely an artifact of an OpenAI/Claude
   completion that hit token limits and looped on the last word during a T5
   bulk pass. Easy regex find; rewrite is mechanical.
2. **Uncap context in `animal_structural_gates.py`** (LOW effort, principle
   alignment). Zero existing questions affected; future-proofs against
   bulk-gen compression pressure.
3. **Soft-flag 3 citation-skim-tell T5 questions** (lines 8155, 8273,
   8311). Either add citation parens to distractors or remove from correct.
4. **Fix 2 fictional-retraction distractors** (line 8324, 8326, Toxoplasma).
   Replace "has been formally retracted" / "has been universally retracted"
   with real critic positions (Boice's correlational-vs-causal critique).

## Deeper concerns

1. **T5 cap (1100) may encourage padding.** The `overall overall` bug only
   shows up at T5. The same pattern could surface again in any future T5
   bulk-gen. Dropping cap to 1000 (matching geography's recalibrated T5)
   would tighten the production process. Trade-off: 168 existing T5
   questions; some may exceed 1000 and need recalibration.
2. **Sequencing: T5 corruption fix should precede any cap change.** Fixing
   bugs first prevents accidentally re-validating corrupted content under
   a new gate.

## Cross-bank lessons

### Suggested SHARED_PRINCIPLES.md updates
1. **Add §12: Trailing-token corruption signature.** Animal T5 contains
   ~14 instances of `(.+) overall overall overall` truncation. This is a
   real generation-pass failure mode worth a deterministic gate across all
   subjects. Suggested regex: `\b(\w+)(\s+\1){2,}` (any 3+ repeated
   consecutive words). Cheap, catches the bug class.
2. **Note in §10 (cap calibration)**: animal at T1=280/T5=1100 fits its
   content better than geography's pre-bump did. Geography needed bumps
   (260→500 T1, 1100→1000 T5); animal's distribution is heterogeneous
   enough that the existing tiered shape works. Subject content density
   should be checked empirically against exemplars before assuming
   geography's lesson generalizes.
3. **Note in §9 (context uncap)**: the practical impact of the cap is
   determined by how compressed the content naturally is, not by the cap
   value alone. Animal's gate at 420 isn't currently hurting (zero
   exceedances) — but uncapping still good per principle, just zero
   immediate quality lift.

### Items NOT generalizable
- Animal's research-citation anchoring (~26% of contexts) is already at
  the bar GEOGRAPHY_TEMPLATES sets for "name researchers/dates". No
  back-port action needed.
- Animal's distractor steelmanning is solid; no cross-bank lesson.
- Animal lacks the wonder-deferred-to-context failure that geography hit
  with Socotra. Cross-bank lesson is just "vigilance" — not a new gate.

## Reference

Audit method:
- Read ANIMAL_FRAMEWORK.md, ANIMAL_TEMPLATES.md, animal_structural_gates.py
- Read 40-cell exemplar grid in `_animal_exemplars.py`
- Read ~30% of `data/questions/animal.json` directly via offset reads
- Grep probes for: stem length bins, choice length bins, context length
  bins, decoration-mismatch (citation/Latin/dates), formulaic dismissals,
  source anchoring, wonder-in-stem patterns, banned answer types,
  trailing-token corruption
- Cross-referenced against moral_vision.md, SHARED_PRINCIPLES.md §§7-11,
  feedback memories on cap calibration, no-content-warping, lift-discovered-
  rules

Audit performed read-only. No changes made to `data/questions/animal.json`
or any structural gate file.
