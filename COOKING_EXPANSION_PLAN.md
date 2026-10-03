# Multi-Ingredient Cooking Expansion — Plan

**Date:** 2026-10-03
**Goal:** More multi-ingredient recipes, phased across the 100 floors, with the complex ones giving permanent stat bonuses — so cooking rewards saving ingredients and gives the player a durable sense of discovery through the whole run.

---

## Current state (data pulled from the shipped bank)

- **614 recipes total.** 87% single-ingredient, 13% multi.
- **Ingredient-count distribution:**
  - 1 distinct type: 537 recipes
  - 2 distinct types: 65 recipes
  - 3 distinct types: 12 recipes
  - 4+ types: **0 recipes**
- **Permanent bonuses are rare and concentrated:** only 14 recipes carry `permanent_power`, and ALL 14 are **single-ingredient T5** cooks. Zero multi-ingredient recipes grant permanent bonuses today.
- **Outcome tier spread:** T1 313, T2 114, T3 88, T4 56, T5 43 — top-heavy on T1.
- **Ingredient availability by floor band is uneven:**
  - F1-F10: 261 ingredients (flood)
  - F11-F20: 66
  - F21-F30: 25
  - F31-F40: 58
  - F41-F50: 26
  - F51-F60: 28
  - F61-F70: 23
  - F71-F80: 16
  - F81-F90: 25
  - F91-F100: 10
- **Ingredient families:** beast 109, humanoid 105, aberration 43, undead 117, demon 61, fey 22, elemental 19, construct 20, dragon 14, reptile 8, plant 9, celestial 3.

## The design, in short

- The 537 single-ingredient recipes are the **easy daily cook** — just restored to the UI last session. They stay.
- Multi-ingredient becomes the **aspirational / replayable layer**:
  - **2-ingredient** — fun combos. Bigger SP + a temp buff; occasional small permanent.
  - **3-ingredient** — potent. Half give a small permanent (`+1 stat` or `+5 max_hp`).
  - **4-ingredient** — rare. All give permanent (bigger: `+2 stat`, `+10 max_hp`, or a resist).
  - **5-ingredient** — legendary. Signature multi-faceted bonuses (several stat points, immunity, carry bonus).
- **Phasing is automatic** via ingredient `min_level`: a 4-ingredient recipe requiring ingredients from F15, F30, F50, F70 effectively unlocks around F70. No new "discovery" field needed.

## Targets

| Ing count | Current | Target | Delta |
|---|---|---|---|
| 1 | 537 | 537 | 0 (keep) |
| 2 | 65 | 200 | +135 |
| 3 | 12 | 80 | +68 |
| 4 | 0 | 25 | +25 |
| 5 | 0 | 10 | +10 |
| **Total new recipes** | | | **~240** |

### Phased by floor band (what unlocks when)

| Floor band | New 2-ing | New 3-ing | New 4-ing | New 5-ing |
|---|---|---|---|---|
| F1-F10 | 40 | 0 | 0 | 0 |
| F11-F20 | 35 | 10 | 0 | 0 |
| F21-F30 | 25 | 15 | 0 | 0 |
| F31-F40 | 20 | 15 | 5 | 0 |
| F41-F50 | 15 | 10 | 5 | 0 |
| F51-F60 | 10 | 10 | 5 | 2 |
| F61-F70 | 10 | 10 | 5 | 2 |
| F71-F80 | 5 | 5 | 3 | 2 |
| F81-F90 | 5 | 5 | 2 | 2 |
| F91-F100 | 0 | 0 | 0 | 2 |
| **Totals** | **165** (we already have 65) → +100 | **80** (we have 12) → +68 | **25** | **10** |

### Permanent-bonus distribution

| Ing count | Fraction giving permanent | Typical reward |
|---|---|---|
| 1 | ~3% (existing 14 T5 cooks) | Unchanged |
| 2 | ~10% | `+1 stat` OR `+3 max_hp` OR narrow resist |
| 3 | ~50% | `+1 stat` OR `+5 max_hp` OR mid resist |
| 4 | 100% | `+2 stat` OR `+10 max_hp` OR named resist |
| 5 | 100% | 2-slot bonus: `+1 stat + resist`, or `+5 max_hp + +1 WIS`, or an immunity + carry_bonus |

Rough new-outcome count: ~115 unique archetype entries added to `cook_outcomes.json` to back the 240 new recipes (many recipes share an archetype template).

---

## The plan — 5 phases

### PHASE 0 — Lock design rules

Short doc at `docs/design/multi_ingredient_cooking.md`:
- Ingredient-count → bonus tier mapping (table above)
- SP soft-boundary floor preserved (recipe SP ≥ raw-eat emergency floor; see `feedback_sp_soft_boundary.md`)
- No duplicate ingredient-combos across recipes (deterministic sort of ingredient-id list → stable hash → dedup gate)
- Recipe `name` must evoke the combo (no generic "Monster Stew" — think "Troll-Hoof + Elderberry Pot")
- `outcome_id` must exist in `cook_outcomes.json` before the recipe can reference it
- Permanent-bonus caps: no single recipe grants more than +2 to a single stat, no single recipe grants an immunity bigger than tier-matched elemental resist

### PHASE 1 — Author new outcome archetypes (~115 new entries)

Add to `data/items/cook_outcomes.json → outcomes`:
- ~30 new 2-ingredient outcome templates (tier 2-3; bigger SP + temp buff + occasional small permanent)
- ~40 new 3-ingredient outcome templates (tier 3-4; +1 stat / +5 max_hp)
- ~25 new 4-ingredient outcome templates (tier 4-5; +2 stat / +10 max_hp / resist)
- ~20 new 5-ingredient outcome templates (tier 5; multi-slot legendaries)

Preserve the existing 120 outcomes. Append; don't rewrite. Each new outcome gets a unique id like `t3_combo_vigor`, `t4_legendary_strength`, `t5_mythic_warden`.

**1 Opus agent for outcomes authoring.** ~115 outcomes × ~15 fields each = tractable.

### PHASE 2 — Author new recipes (~240 total)

For each floor band F1-F10 through F91-F100:
- Enumerate ingredients available at that band (ingredient `min_level ≤ band_upper`)
- Compose 2/3/4/5-ingredient combos targeting the phase totals above
- Pick an outcome_id from Phase 1's archetypes (tier appropriate to combo size)
- Pick a flavorful name (sacrosanct — kids see this on the cook menu)
- Pick a `flavor` line (one sentence of cooking narration)

Dedup: a recipe is defined by its sorted ingredient tuple. No two recipes share the same tuple.

**10 Opus agents in parallel**, one per floor band. Each authors ~24 recipes.

### PHASE 3 — Validate (automated)

A single validation script:
- Every recipe's `outcome_id` resolves to an entry in `cook_outcomes.json`
- Every recipe's `ingredients` are real ids in `ingredient.json`
- No duplicate ingredient-tuples across recipes
- Every multi-ingredient recipe's effective floor-level (max of its ingredients' `min_level`) matches the phase it was authored for
- Permanent-bonus caps per phase respected
- SP output ≥ raw-eat emergency floor for every outcome

Any violation → agent rewrites that specific recipe/outcome.

### PHASE 4 — Re-run cook tests, playtest hook

- `pytest tests/test_cooking*.py` + `tests/test_cooking_overhaul.py` + any downstream touched tests
- Full `pytest tests/ -q` suite
- The cook-menu UI already handles multi-ingredient recipes (restored last session) — no new UI work
- Spot-check in-game: F5 start, pick up 2-3 ingredients, press C, verify the new multi-ingredient recipes appear

### PHASE 5 — Ship v2.20.0

Version bump + commit + tag + push → CI builds Windows + Linux + GitHub Release.

---

## Cost estimate

- Phase 0: me, direct — 10 min
- Phase 1: 1 Opus agent (outcomes) — 20-30 min
- Phase 2: 10 Opus agents in parallel (recipes) — 1-2 hours wall time
- Phase 3: me + 1 small Opus agent (validate + repair) — 15-30 min
- Phase 4: me, direct — 15 min
- Phase 5: me, direct — 10 min

**Total: ~12 Opus sessions, ~2-3 hours wall time, mostly parallel.** All agents `model: 'opus'` per memory rule.

---

## Open design decisions (quick calls needed)

1. **Discovery mechanic** — rely on ingredient `min_level` alone (automatic phasing, my proposal), or add explicit `discovery_floor` field so the recipe is HIDDEN from the cook menu until the player reaches that floor even if they have the ingredients?
2. **Legendary 5-ingredient cadence** — 10 total across the 100-floor run (my proposal), or more sprinkled (15-20)?
3. **Permanent-bonus caps** — my proposal: no recipe grants >+2 to a single stat, no immunity bigger than tier-matched resist. OK?
4. **Named recipes** — I'd use evocative names ("Troll-Hoof + Elderberry Pot", "Dragon-Scale Terrine", "Ymir's Last Soup"). Prefer that style or more mundane ("Hearty Troll Stew")?
5. **Author in parallel OR sequential** — 10 parallel per-floor-band agents (my proposal, faster), or 1 agent per ingredient-family (fewer agents, more coherent per-family voice)?

Give me the calls and I fire Phase 0 immediately. The design above is the baseline I'll execute if you just say "go."
