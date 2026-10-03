# Multi-Ingredient Cooking — F11-F20 Recipes Audit (Phase 2, Cook-P2)

**Date:** 2026-10-03
**Agent:** Cook-P2 (F11-F20 floor band)
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion. This agent authored
45 new recipes for the F11-F20 floor band (35 two-ingredient + 10 three-ingredient)
and emitted them to the intermediate drop file:

- **Output:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f11_20.json`
- **Line count:** 417
- **Phase-3 merger** will consume this file alongside the other floor-band drops.

---

## Counts delivered

| Bucket | Quota | Delivered |
|---|---|---|
| 2-ingredient recipes | 35 | 35 |
| 3-ingredient recipes | 10 | 10 |
| **Total** | **45** | **45** |

Outcome-tier mapping honored:
- 2-ing recipes → `t2_combo_*` (24) or `t3_combo_*` (11)
- 3-ing recipes → `t3_tri_*` (6) or `t4_tri_*` (4)

---

## Floor-band compliance

Every recipe's `max(min_level over ingredients)` falls inside the F11-F20 window:

| max min_level | recipes |
|---|---|
| 11 | 13 |
| 12 | 12 |
| 13 | 7 |
| 14 | 4 |
| 15 | 1 |
| 18 | 3 |
| 19 | 4 |
| 20 | 1 |

Every recipe satisfies the stricter author rule: at least one ingredient has
`min_level ∈ [11, 20]`. Low-tier anchor ingredients used only as the second slot
(for thematic / variety reasons) and never as the lone level-anchor:
- `swamp_moss` (ml=5) — paired with `myconid_sovereign_prime` (11) and
  `charybdis_spawn_prime` (11); also inside the 3-ing grove recipe.
- `cave_mushroom` (ml=1) — paired with `anzu_bird_prime` (11); also inside the
  3-ing grove recipe.
- `holy_water` (ml=15) — paired with `cult_priest_prime` (18) and
  `owlbear_prime` (12); itself in-band.
- `crystal_shard` (ml=20) — paired with `talos_prime` (19); itself in-band.

---

## Dedup — collisions

| Check | Result |
|---|---|
| In-batch sorted-tuple collisions | 0 |
| Collisions against `data/items/recipes.json` existing 614 tuples | 0 |
| In-batch recipe-id collisions | 0 |
| In-batch name collisions | 0 |

Ingredients are reused across recipes with distinct sorted-tuples — e.g.
`ice_troll_prime` appears in the (ice-troll, ettin) vigor pot and the
(ice-troll, lesser-stone-golem) coldforge pot. All 45 sorted-tuples are unique.

---

## Outcome-id resolution

Every `outcome_id` resolves to a real entry in
`data/items/cook_outcomes.json → outcomes`. Validator confirmed 41 distinct
outcome ids referenced:
- 2-ing outcomes drawn from 17 `t2_combo_*` + 14 `t3_combo_*` = 31 available.
  All 31 referenced; 4 reused across distinct ingredient-tuples (`t2_combo_wild`,
  `t2_combo_haunt`, `t3_combo_fierce`, `t3_combo_wyrmling_grit`).
- 3-ing outcomes drawn from 20 `t3_tri_*` + 20 `t4_tri_*` = 40 available.
  10 referenced (one each), zero reuse.

Reuse is permitted by the design doc ("Many recipes → one outcome") and the
pre-existing recipes.json pattern.

---

## Naming + flavor compliance

- All 45 names are unique within the batch.
- Every name calls out at least one ingredient (e.g. "Ice-Troll Shank and
  Ettin-Shoulder Vigil" names both; "Myconid-Sovereign Heartwood and Swamp-Moss
  Pot" names both).
- No generic / template names ("Hearty Stew", etc.) — every one is evocative.
- Flavor text is one sentence; narrates taste / smell / ritual without leaking
  the mechanical outcome.

---

## Three sample names

1. **"Ice-Troll, Ettin, and Fire-Giant Thrice-Shoulder Stew"** → `t3_tri_sinew`
2. **"Niohoggr-Brood and Greater-Wyvern Grit Stew"** → `t3_combo_wyrmling_grit`
3. **"Dread-Wraith and Ghast-Eater Haunting Pot"** → `t2_combo_haunt`

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f11_20.json` — **new**,
  45 recipes, 417 lines.
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\_build_f11_20.py` — scratch build
  + inline validator (deterministic — re-run always produces the same output).
- `docs/audits/cook_expansion_f11_20_2026-10-03.md` — this report (new).

No edits to `data/items/recipes.json`, `data/items/cook_outcomes.json`, or
`data/items/ingredient.json`. Phase-3 merger owns the write back into
`recipes.json`.
