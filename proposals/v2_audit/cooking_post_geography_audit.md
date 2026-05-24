# Cooking Post-Geography Audit (2026-05-24)

Read-only audit applying the gates and principles discovered during the 2026-05-23 geography rebuild against the existing cooking bank. Per [[feedback_no_content_warping]]: principles are MENUS not CHECKLISTS — each axis evaluated only where it naturally applies to cooking content. No edits made; this is a proposal for the user's review.

Source files audited:
- `data/questions/cooking.json` (992 questions, ~200/tier)
- `tools/quizgen/deterministic/length_budget.py` (canonical cap system)
- `tools/quizgen/scratch/cooking_structural_gates.py` (per-field cap system)
- `proposals/v2_audit/COOKING_FRAMEWORK.md` / `COOKING_TEMPLATES.md`
- `proposals/v2_audit/GEOGRAPHY_FRAMEWORK.md` / `GEOGRAPHY_TEMPLATES.md`
- `proposals/v2_audit/SHARED_PRINCIPLES.md` §§9-10

## Summary

- **Bank size**: 992 questions (T1=200, T2=199, T3=200, T4=196, T5=197)
- **Findings severity**: MEDIUM-HIGH
- **Top 3 actionable recommendations**:
  1. **Recalibrate cooking T1/T2 total-budget cap** ({280, 480} → ~{500, 620}, possibly higher given cooking's 60s timer). Current canonical caps in `length_budget.py` are violated by essentially every shipped T1-T2 question. This is the **same condition that broke geography** in the 2026-05-23 rebuild. Bank passed `validate` historically only because the scratch gate uses per-field caps (200/90 stem/choice ≈ 560 max) while canonical SUBJECT_TIER_BUDGETS uses total caps. Two cap systems, divergent verdicts.
  2. **Uncap context per SHARED_PRINCIPLES §9**. Cooking context is currently capped per-tier (200/240/300/360/420) and the cap is binding — only 2 questions exceed T5's 420 cap, while many T4-T5 contexts look saturated. Cooking is heavily mechanism + history-driven; depth genuinely helps (Maillard chemistry, garum reconstruction, koji microbiology).
  3. **Bank passes the other 4 audit axes cleanly** (decoration mismatch, wonder-in-stem, steelman distractors, cuisine/technique anchoring). No bulk-rewrite required for principle-level failures.

---

## 1. Total-budget calibration

### Current canonical budget (length_budget.py SUBJECT_TIER_BUDGETS["cooking"])
`{1: 280, 2: 480, 3: 680, 4: 900, 5: 1100}` — UNCHANGED since 2026-05-11 philosophy bump. Geography had the IDENTICAL budget pre-2026-05-23, bumped to `{500, 620, 770, 900, 1000}` because exemplars universally exceeded T1-T2 caps.

### Empirical sample (stem + 4 choices, total chars)
Spot-sampled across topics + tiers (~3-5 per cell):

| Tier | Samples examined | Approx avg | Approx max | Canonical cap | Over cap? |
|---:|---:|---:|---:|---:|---|
| T1 | 8 (Bread + Food-history + Ingredients) | ~420 | ~528 | 280 | **Yes — universally** |
| T2 | 7 (Bread + Sauces + Heat) | ~530 | ~620 | 480 | **Yes — most** |
| T3 | 6 (Bread + Sauces + Cuisines) | ~640 | ~720 | 680 | **Borderline (some over)** |
| T4 | 5 (Bread + Heritage + Sauces) | ~720 | ~830 | 900 | Under |
| T5 | 8 (Bread + Cuisines + Charcuterie + Food-politics) | ~810 | ~920 | 1100 | Under |

(Empirical sample reflects approximate hand-counts of representative questions, not the full 992. A scripted full-bank histogram is the right next step — flagged for the user.)

### Stem-length distribution (full bank, regex-counted)
- ≥150 chars: **976 of 992** (98%)
- ≥180 chars: **798 of 992** (80%)
- ≥200 chars: **616 of 992** (62%)

At T1 cap of 280 total, a stem ≥150 chars leaves only 130 chars for **all 4 choices combined** (~32 chars each — impossible for parallel meaningful choices). At cap 280 total, the bank's actual T1 design density is structurally incompatible. The cap was never realistic for this content.

### Why the bank historically passed `validate --subject cooking` despite this
The scratch gate (`cooking_structural_gates.py`) uses per-field caps `{1: (200, 90, 200), ...}` — stem ≤ 200, each choice ≤ 90, context ≤ 200, giving an implicit per-question total of up to ~560 at T1. The canonical pipeline gate (`validate_length_budget` from `length_budget.py`) uses a total-budget cap of 280 at T1. **The cooking rebuild was validated against the scratch gates only.** The cooking review of 2026-05-19 reporting "1203 KEEP, 0 REPAIR, 0 DISCARD" was the same configuration. Geography hit this divergence and resolved it 2026-05-23; cooking still has both systems in play.

### Comparison to geography pre-bump pattern
**Identical condition.** Geography exemplars showed T1 avg 416 / T2 avg 543 — bank was bumped to `{500, 620, 770, 900, 1000}` at +15% headroom. Cooking sampled means (T1 ~420, T2 ~530, T3 ~640) are essentially identical to geography's empirical bar. Same family of action (escalator-chain medium-frequency).

### Timer asymmetry — cooking can support DIFFERENT budgets than geography
- **Cooking timer**: 44 + 1.6×WIS = **60s @ WIS 10** (player.py:27)
- **Geography timer**: 28 + 1.2×WIS = **40s @ WIS 10** (player.py:22)
- **Asymmetry**: cooking has 50% more reading time per question

If we hold reading-speed ~30 chars/sec (skim-pace for a 14-year-old) as the analytical anchor:
- Geography 40s × 30 = 1,200 chars max per question — geography canonical caps at 1,000 in T5 (comfortable)
- Cooking 60s × 30 = 1,800 chars max per question — cooking canonical caps at 1,100 in T5 (very loose for the timer)

The timer asymmetry justifies cooking caps being EQUAL TO OR GREATER THAN geography's, never less. Yet cooking's canonical T1=280 is below geography's new T1=500.

### Recommendation

**Recalibrate cooking SUBJECT_TIER_BUDGETS to at least match geography**, possibly more generous:

| Tier | Current canonical | Geography canonical | Proposed cooking | Rationale |
|---:|---:|---:|---:|---|
| T1 | 280 | 500 | **500** (min) | Empirical 8-sample T1 avg ~420; ≥500 with grace handles the bank as-shipped |
| T2 | 480 | 620 | **620** (min) | Empirical ~530 avg; geography's 620 is the floor |
| T3 | 680 | 770 | **770** | Empirical ~640 avg; current 680 is borderline tight, geography's 770 gives room |
| T4 | 900 | 900 | 900 | Empirical comfortable; keep |
| T5 | 1100 | 1000 | 1100 (or 1050) | Cooking-specific T5 content (mole 30+ ingredients, Roman garum reconstruction, koji microbiology) supports more density; cooking's longer timer permits it |

These are LOWER BOUNDS. If the user wants to add scaffolding density to T1-T2 (parallel to geography's "scaffolding > compression" rule), the budget can go higher (e.g., T1 = 540, T2 = 660).

**Open question for the user**: should cooking adopt geography's "total budget as the operative gate, per-field as advisory" convention from GEOGRAPHY_TEMPLATES.md §6? Currently cooking uses per-field caps in scratch gates and total caps in canonical — two systems, divergent verdicts. Reconciling them (as geography did) prevents future drift.

---

## 2. Context uncap

### Current cap
Per `cooking_structural_gates.py` line 28: T1≤200, T2≤240, T3≤300, T4≤360, T5≤420.

### Distribution (full bank, regex-counted)
- ≥100 chars: **992 of 992** (100%)
- ≥200 chars: **712 of 992** (72%)
- ≥300 chars: **350 of 992** (35%)
- ≥400 chars: **53 of 992** (5%)
- ≥420 chars: **2 of 992** (0.2%) — cap is binding

### Qualitative read
Sampled T5 contexts at 400-420 (Lloyd's of London / Coffee House Enlightenment; Roman garum reconstruction; Heston Blumenthal meat fruit; Boudin Bakery 1849; Brian Cowan's *Social Life of Coffee*; Hamelman + Calvel on DDT math) consistently include name-drop-then-truncate patterns. Example:

> "...The causal claim — coffee 'enabled' the Enlightenment — is contested but Brian Cowan's *The Social Life of Coffee* (2005) develops it seriously." (sentence ends — Cowan's argument unmentioned)

The cap forces the context to **name** the source but not **transmit** the argument. That's a [moral_vision.md §"Beauty of mechanism" / §"Curiosity over completion"] failure mode: the author had more to teach and the gate cut them off.

### Recommendation

**Uncap context per SHARED_PRINCIPLES §9.** Cooking is heavily mechanism + history-driven (food chemistry; Columbian Exchange; Crusader spice trade; charcuterie microbiology; J-pattern recognize-the-move analysis), and depth here is genuinely the curriculum. The cap is shallow educational depth dressed as a parsing budget — but context is read at the player's pace AFTER the answer, so it doesn't compete with the timer.

**Implementation**:
- Update `cooking_structural_gates.py` `gate_length_budget` to skip context check (mirror geography 2026-05-23)
- Update `COOKING_TEMPLATES.md` §6 to mark context as uncapped, retain stem/choice envelopes
- Update `COOKING_FRAMEWORK.md` tier sections similarly
- Continue capping stem + choices per recalibration in §1

---

## 3. Decoration mismatch

### Citation/parens-only-in-correct-answer ("skim-tell")
Bank already has the citation skim-tell anti-pattern documented in `COOKING_TEMPLATES.md` §7.3. Counted:
- Choices with `(YYYY)` or `(YYYY-` pattern: **4 of 3968** choices (0.10%) — verified to be parallel within their question (other 3 choices have similar parens)
- Choices opening with parenthetical (parens with examples/cuisines/Latin terms): **130** total; spot-checked 10+ — **all are parallel within the 4-choice set** (e.g., when "Poolish (French wet)" is the answer, the other 3 choices also use "[Term] (region/category)" structure)

### Broader decoration patterns audited
- **Em-dash structure parity**: enforced by `gate_choice_shape_parity` (philosophy_structural_gates inherited via cooking_structural_gates)
- **Inline parenthetical (cuisines, dates, Latin terms, definitions)**: PARALLEL across all 4 choices in sampled questions
- **Quoted phrases**: when correct answer has `"..."`, the other choices share it (sampled T5 food-politics J-pattern questions; quoted critic-statements appear in stem, not in choice decoration)

### Count

**5-10 representative samples (all show PARITY, not mismatch)**:

| Q (line) | Decoration | Status |
|---|---|---|
| #1030 | "Poolish (French wet)" — all 4 choices use Term (origin) | OK |
| #2787 | "(the umami)" — all 4 use parenthetical glosses | OK |
| #3265 | "kappa carrageenan plus calcium ions" — all 4 are bare prose | OK |
| #4419 | "Public choice -" — all 4 use Name - explanation | OK |
| #5119 | "Mirepoix — celery, onion, and carrot" — all 4 use Term — definition | OK |
| #11537 | "The Mughal Empire (1526-1857)" — others have year ranges or none parallel | Borderline — only correct has full date range |

### Verdict
**LOW concern.** Cooking's existing scratch gate and the "citation skim-tell" anti-pattern catch most of the surface failures. The broader decoration mismatch principle (geography §7.3) holds — sampling confirms 4-choice parity across parens / quotes / lists. The Mughal-Empire-style borderline (where only one choice has a year range) is rare and minor.

No corrective action required at this audit pass.

---

## 4. Wonder-in-stem (vs context-deferred)

### Cooking-specific risk pattern
"What temperature does X bake at?" / "How many ingredients in mole?" / "How long does Y ferment?" with the wonder buried in context.

### Empirical sweep
- "How many" + ingredient/cup/teaspoon/minute pattern: **0 matches** (recipe-stat questions banned + absent)
- "What temperature" stems: **3 total** — all 3 wonder-in-stem (caramel-vs-hard-candy texture; whipped-cream physics; cold-smoke vs hot-smoke). Wonder lives in the comparative setup, not the temperature itself.
- "About how much" / "approximately": rare, ~3-5 cases; sampled — wonder always in the stem setup (e.g., maple sap 40:1 ratio is itself the wonder).
- Spot-checked T4-T5 cultural questions: stems lead with concrete wonder (Roman garum factories at Pompeii; Trappist monasteries; Boudin Bakery 1849 starter; Edomae nigiri vs narezushi history). Context elaborates rather than carrying the wonder.

### Count
**~0-3 questions show wonder-deferred-to-context** out of 992. Cooking is structurally clean on this axis — its scene-led voice was established early in the rebuild and the rebuild discipline held.

### Samples (representative, all PASSING wonder-in-stem)

| Q (line) | Stem leads with | Choices test | Verdict |
|---|---|---|---|
| #6414 (T1) | "Canadian maple farmer drills, sap drips, boiling reduces greatly" | the 40:1 ratio (wonder is the ratio itself) | wonder-in-stem |
| #2268 (T2) | "Caramel chews soft, hard candy brittle, both sugar-based" | what temperature changes the chemistry | wonder-in-stem |
| #6246 (T3) | "Persian tahdig — crispy bottom-of-the-pot rice, host saves largest piece for honored guest" | what tahdig reveals about Persian culinary values | wonder-in-stem |
| #11537 (T4) | "Indian and Persian cooking share biryani, kebab, tandoor, saffron rice — no coincidence" | what historical contact produced the overlap | wonder-in-stem |
| #3054 (T5) | "Roman garum factories at Pompeii produced fermented fish sauce in amphorae across the empire; modern researchers reconstructed it" | chemistry + production | wonder-in-stem |

### Verdict
**LOW concern.** No corrective action required.

---

## 5. Steelman distractors

### Sample size
~40 questions sampled across all 5 tiers (T1 bread + T2 onions/heat + T3 sourdough + T4 risotto/sushi/Italian regional + T5 J-pattern + T5 dry-cure/charcuterie/koji).

### Cooking-specific bad-distractor patterns audited
- **"is a misconception by chefs" / "this technique was abandoned" / "this dish is a 19th-century invention" formulaic dismissals**: only **1 distractor** matches this verbal pattern in the entire bank (line 12534 — Italian regional cuisine as "marketing construct from after WWII"). And it's properly framed as one of three contrarian historical claims, not a dismissive throwaway. No formula abuse.
- **"the chicken"-style joke distractors**: none observed.
- **Absurd distractors**: none observed in the sample.

### Distractor quality observations
- J-pattern recognize-the-move questions (11 total) have **gold-standard distractors**: each is a real analytical move (Bastiat, Sowell, Hayek, Pollan, public choice) accurately described and applied to the scenario. The same shape applies to philosophy's care-ethics critique pattern.
- T4-T5 charcuterie/koji/dry-cure questions have **chemistry-real distractors** (e.g., Maillard analogue distractors invoke proteolysis, lipid oxidation, surface molds — all real chemistry, just wrong for the specific question).
- T1-T2 bread/baking distractors are **plausible-wrong mechanisms** (yeast killing distinctions, hydration vs leavening, autolyse vs kneading) — kids who half-know the chemistry will pick wrong; the correct answer rewards real understanding.
- Cultural-cuisine distractors (T3-T5) are **other real cuisines/traditions accurately stated** that don't fit the specific scenario (e.g., sofritto vs sofrito vs trinity vs mirepoix all real bases, only one is French).

### Samples (steelman quality)

| Q (line) | Why steelmanned |
|---|---|
| #4419 (T5 J public-choice) | All 4 distractors are real economic-analytical moves (Bastiat, Sowell, Hayek, Pollan) accurately described |
| #9054 (T5 dry-cure Maillard) | Distractors invoke real but wrong chemistry: surface molds, cure-salt catalysis, brief warm-finishing — all real possibilities, all wrong for the actual mechanism (proteolysis + lipid oxidation + pigment concentration) |
| #5118 (T2 mirepoix) | Other distractors are real French foundation techniques (bouquet garni, sachet d'épices, court-bouillon) — not absurd, just not the answer |
| #11860 (T4 narezushi) | Distractors describe real-sounding-but-wrong mechanisms for narezushi rice's role (cooking via koji, absorbing oils, sweet binder) — each is a plausible alt-hypothesis a thoughtful student might consider |
| #11102 (T5 bagel American story) | Distractors are real alternative histories (Polish bakers abandoned form on arrival; pre-1900 records show no European tradition; American bagel uses different flour) — each must be evaluated against actual immigrant history |

### Verdict
**LOW concern.** The cooking bank's distractor quality is high. The "is a misconception/myth/marketing construct" formula is not abused. No corrective action required.

---

## 6. Cuisine/technique anchoring (cooking analog of place-anchoring)

### Geography's analog (place_anchor_check)
When a stem names "K2," it must include the Karakoram anchor for a first-time reader. Cooking's analog: when a stem names a cuisine or technique ("tahdig," "gravlax," "garum") it should anchor it (country/region/era).

### Empirical sweep
Searched stems for named non-anglo cuisine adjectives (Sichuan, Sicilian, Tuscan, Cantonese, Mughal, Persian, Levantine, etc.) and named techniques (tahdig, gravlax, garum, sofrito, mirepoix, tajine, chimichurri):

| Named term in stem | Anchored in same stem? |
|---|---|
| Sichuan (3 stems) | yes — "Sichuan cooks" + "tongue-numbing tingle and deep chile burn" / "Korean kimchi, Sichuan ma-la" / "Sichuan cuisine" |
| Sicilian (multi) | yes — "Sicilian pasta alla Norma," "Sicilian eggplant caponata," "Sicily preserves" etc. paired with region context |
| Cantonese (3 stems) | yes — "Cantonese cooks fire restaurant woks" / "Cantonese cuisine's wok and explosive stir-fry developed in southern China" |
| Mughal (1 stem) | yes — "The Mughal Empire (1526-1857) was a Persianate Muslim dynasty in India" |
| Persian (multi) | yes — "Persian cuisine prizes the crispy bottom-of-the-pot rice" / "Iranian (Persian) cuisine" |
| Levantine (2 stems) | yes — "Crusader era (~1095-1291)" anchor + "Levantine and Islamic world" |
| Norman/Norse (multi) | yes — "Norse fishermen packed salmon in salt with dill" / "Norman invasion (1071) brought eggplant" (a wrong-answer distractor; not stem scaffolding) |
| tahdig (3 stems) | yes — every "tahdig" stem anchors "Persian" + describes structure (crispy rice crust at bottom of pot) |
| gravlax (2 stems) | yes — "Norse fishermen" + "Scandinavian gravlax is salmon cured with..." anchor source + describe |
| sofrito/mirepoix (5 stems) | yes — explicitly contrasted ("Italian sofritto, Spanish sofrito, Cajun trinity, French mirepoix") |
| tajine (some) | yes — paired with "North African" anchor in samples |
| garum (multi) | yes — "Roman garum factories at Pompeii" or "salt cod, gravlax, garum" with context |

### Count of unanchored stems
**~0 of ~30+ named cuisine/technique stems sampled.** Cooking's scene-led voice naturally produces well-anchored stems because the wonder hook itself usually supplies the geography ("Persian cooks at the bottom of the pot"; "Norse fishermen buried in cold sand"; "Roman amphorae at Pompeii"). The bank's structural rule "stem must contain a forcing constraint" effectively requires the anchor.

### Verdict
**LOW concern.** Cooking is structurally clean. A formal `cuisine_anchor_check` deterministic gate (analog of `place_anchor_check`) would catch ~0-3 borderline cases out of 992. Cost-benefit suggests it's not the highest-leverage gate to add — but if the user wants completeness alignment with geography, a simple cuisine-name-without-region regex is straightforward to add as soft-warn.

If added, the gate spec:
- **Trigger**: stem contains a cuisine adjective from a list (Sichuan/Cantonese/Tuscan/Sicilian/Mughal/Persian/Norse/etc.) AND no nearby geographic anchor (country/region within ~20 words)
- **Action**: soft-warn for human review; not hard reject
- **Exempts**: Pattern D (identify-by-trait) where the cuisine name IS the answer

---

## 7. Excluded principles (per no-warping rule)

Per `feedback_no_content_warping.md`, the following principles from geography were considered but found NOT to naturally apply to cooking content:

- **`place_anchor_check` for geographic places**: cuisine-region anchoring IS relevant (§6), but mountain/river/continent anchoring is not.
- **`no_capital_recall`**: cooking has no capital-city test analog. The cooking-specific `no_toddler_recall` (pizza/hamburger/pasta/salt/sugar) is the parallel.
- **`no_climate_policy_verdict`**: cooking has no climate-policy content. The parallel — `no_food_moralism` (judgment gate) — already exists.
- **`no_theory_stacking_check`**: cooking is mostly practical chemistry + technique + cultural history. Theory-vs-theory abstraction at T5 is essentially absent (~2 stems with "framing" / "doctrine" — both anchored, e.g., "the cultural framing reveal" attached to Dom Perignon legend with concrete monks named). The J-pattern recognize-the-move questions are concrete (a specific food critic's specific argument), not theory-stacking.

These exclusions are aligned with [[feedback_no_content_warping]] — applying them would require manufactured content (forced theory-stacking distractors in a cooking-chemistry question, etc.). Cooking remains exempt naturally.

---

## Quick wins

1. **Bump cooking T1/T2 canonical caps to {500, 620, ...}** matching geography (single-line edit to `length_budget.py`). Unblocks the latent inconsistency between scratch and canonical gates.
2. **Uncap cooking context** in `cooking_structural_gates.py` `gate_length_budget` + `COOKING_TEMPLATES.md` §6 (mirror geography). Frees writers to teach mechanism depth.
3. **Document the dual-cap-system divergence** as a known gap in `COOKING_TEMPLATES.md`, like geography did, to prevent future regression.
4. **Optional**: add a soft-warn `cuisine_anchor_check` regex for completeness with geography's `place_anchor_check`. Low yield (~0-3 hits), but principle-aligned.
5. **Optional**: reconcile the scratch per-field caps with the canonical total caps (geography model) so there's one source of truth for length.

## Deeper concerns

**None requiring bulk rewrite.** Cooking's scene-led, wonder-hook-in-stem, steelman-distractor discipline is solid. The only structural finding is the cap miscalibration (§1) — and that's a configuration fix, not a content fix. The existing curated questions are well within the recalibrated caps that the audit recommends; no question would need to be touched to comply.

If the user later wants to ADD scaffolding density to T1-T2 (parallel to geography's "scaffolding > compression"), that's an additive expansion, not a rebuild — and the cap recalibration would unlock it.

## Cross-bank lessons (suggested updates to SHARED_PRINCIPLES.md)

1. **Lift the "two caps systems diverge" failure mode** to §10 explicitly. Currently §10 says "Per-tier length budgets must be calibrated against canonical analysis, not blindly copied." Add: *"When a subject has BOTH a per-field cap in scratch gates AND a total-budget cap in `length_budget.py` SUBJECT_TIER_BUDGETS, they MUST be reconciled to one source of truth — typically total-budget as operative, per-field as advisory."* This is the second time this pattern has appeared (geography 2026-05-23, cooking 2026-05-24).

2. **Add a "subject timer asymmetry overrides equal caps" note** to §10. Subjects with longer timers (cooking 60s, theology 50s, economics 50s, philosophy 50s) can support EQUAL OR GREATER caps than subjects with shorter timers (geography 40s, math 16s). Inheriting caps without checking the timer is a category error.

3. **Status of context-uncap rollout (§9)**: geography done 2026-05-23. Cooking flagged for backport 2026-05-24 (this audit). Animal + philosophy still pending; their banks likely have the same constraint and would benefit from the same uncap. Add to the cross-subject tracker.

4. **Status of universal-implementation gaps (§"Open universal-implementation gaps")**: this audit confirms cooking is structurally clean on the wonder-in-stem axis, the place-anchor analog (cuisine anchoring), the decoration-mismatch axis, and steelman distractors. The doc currently lists "Cooking: no scaffolding-must-be-grounded equivalent" as a gap — this audit shows the spirit of the principle IS already implemented through cooking's existing forcing-constraint + scene-led discipline. The gap is documentation-only, not enforcement.

## Files referenced

- Bank: `data/questions/cooking.json` (992 questions)
- Canonical gate (active): `tools/quizgen/deterministic/length_budget.py` (SUBJECT_TIER_BUDGETS["cooking"] = {280, 480, 680, 900, 1100})
- Scratch gate (used during rebuild): `tools/quizgen/scratch/cooking_structural_gates.py` (TIER_CAPS per-field)
- Docs: `proposals/v2_audit/COOKING_FRAMEWORK.md` + `COOKING_TEMPLATES.md`
- Shared: `proposals/v2_audit/SHARED_PRINCIPLES.md` (§9 context uncap, §10 cap calibration)
- Geography reference: `proposals/v2_audit/GEOGRAPHY_TEMPLATES.md` §6 (length envelopes after 2026-05-23 bump)
- Timer source: `src/player.py:12-30` (SUBJECT_TIMER)
- Moral vision (supreme): `docs/quiz/moral_vision.md`

## Final note on audit method

This audit was performed read-only without script execution (sandbox constraint). Distributional claims (stem-length histograms, decoration counts, distractor patterns) are from regex sweeps over the JSON; sample averages are hand-computed from ~5-8 representative questions per cell. A full scripted histogram of stem-char + total-char per tier is the appropriate next step before the user commits to specific cap numbers. The {500, 620, 770, 900, 1100} recommendation is the geography-equivalent floor; the analytical math + cooking's 60s timer arguably support higher values (e.g., T1=540, T2=660), and the user may want to set them empirically against the exemplars rather than the as-shipped bank.
