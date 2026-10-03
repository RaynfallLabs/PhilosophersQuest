# Multi-Ingredient Cooking Expansion — F1-F10 Recipe Author Audit

**Date:** 2026-10-03
**Agent:** Cook-P2 F1-F10
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion
(`docs/design/multi_ingredient_cooking.md`,
`docs/audits/cook_expansion_outcomes_2026-10-03.md`).

---

## Output

- **File:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f1_10.json`
- **Line count:** 362
- **Recipes authored:** 40 two-ingredient recipes
- **Three/four/five-ingredient:** 0 (per band quota)

## Quota compliance

| Count | Required | Delivered |
|-------|----------|-----------|
| 2-ing | 40       | 40        |
| 3-ing | 0        | 0         |
| 4-ing | 0        | 0         |
| 5-ing | 0        | 0         |

Every recipe's two ingredients have `min_level` in `[1, 10]`
(verified by `_gen_recipes_f1_10.py`'s band check — ran clean, no
out-of-band ingredient).

## Collision log

- `(altar_incense, skeleton_prime)` was the author's first draft for the
  "Pilgrim's Bone-and-Smoke Soup" slot — rejected: already in
  `recipes.json`. Rerouted to `(altar_incense, skeleton_warrior_prime)`,
  which is free.

No other sorted-ingredient-tuple collisions with the existing 65
two-ingredient recipes or internal to this batch of 40. Validation
asserts fired `ALL CHECKS PASS`:

```
INGREDIENT MISSING / OUT OF BAND:   0
INTERNAL DUP TUPLE:                 0
EXISTING TUPLE CLASH:               0
OUTCOME MISSING:                    0
```

## Outcome reuse

25 distinct outcome ids used across 40 recipes. Reuse is expected per the
pipeline (Phase 1 authored only 31 `t2/t3_combo_*` outcomes). Breakdown:

| outcome_id              | uses |
|-------------------------|------|
| t2_combo_wyrmling       | 4    |
| t2_combo_bogmire        | 3    |
| t2_combo_cunning        | 3    |
| t2_combo_barrow         | 2    |
| t2_combo_haunt          | 2    |
| t2_combo_hearth         | 2    |
| t2_combo_mossgrown      | 2    |
| t2_combo_pilgrim        | 2    |
| t2_combo_vigor          | 2    |
| t2_combo_warmth         | 2    |
| t2_combo_wild           | 2    |
| t2_combo_mire           | 1    |
| t2_combo_quickstep      | 1    |
| t2_combo_sailor         | 1    |
| t2_combo_sandfury       | 1    |
| t2_combo_shadow         | 1    |
| t2_combo_sunwarm        | 1    |
| t3_combo_arrowfang      | 1    |
| t3_combo_cinder         | 1    |
| t3_combo_coldforge      | 1    |
| t3_combo_fierce         | 1    |
| t3_combo_frostcake      | 1    |
| t3_combo_mountain       | 1    |
| t3_combo_sage           | 1    |
| t3_combo_wyrmling_grit  | 1    |

- **T2 (temp-buff) outcomes:** 32 of 40 recipes (80%).
- **T3 outcomes:** 8 of 40 recipes (20%) — including the 4 with a
  permanent carrier (coldforge hp+2, arrowfang stat+1, mountain hp+3,
  wyrmling_grit hp+3). That lands the permanent-bonus share at
  **10% of 40**, right on the guideline from
  `docs/design/multi_ingredient_cooking.md`.

## Sample names (for coordinator voice check)

1. **Ratbat Hollow-Pot** — `(bat_prime, giant_rat_prime)` →
   `t2_combo_shadow` (dark_vision).
2. **Venom-Pot of Two Deaths** — `(cobra_prime, giant_scorpion_prime)` →
   `t2_combo_wyrmling` (poison_resist).
3. **Weaver-and-Ettercap Set-Stew** — `(ettercap_prime, web_spinner_prime)`
   → `t3_combo_coldforge` (shielded + hp+2).

Voice intent per design rule: every name calls out at least one
ingredient (ratbat, venom-pot/two deaths, weaver/ettercap), reads as
fantastical cookbook rather than generic, and no two names collide.

## Hand-off

The file at `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f1_10.json`
is ready to merge into `data/items/recipes.json` once all ten band
agents complete. No edits to the live recipes file were made.
