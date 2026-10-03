# Multi-Ingredient Cooking — F91-F100 Floor Band Recipes (Phase 2)

**Date:** 2026-10-03
**Agent:** Cook-P2 F91-F100
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion
(`COOKING_EXPANSION_PLAN.md`, `docs/design/multi_ingredient_cooking.md`).
Quota per the floor-band schedule: **2 five-ingredient legendary endgame
recipes**, both keyed to `t5_mythic_*` outcomes. No lower-count recipes in
this band — the apex.

---

## Quota

| Target bucket | Target | Delivered |
|---|---|---|
| 5-ingredient legendary (t5_mythic_*) | 2 | 2 |
| 4-ingredient | 0 | 0 |
| 3-ingredient | 0 | 0 |
| 2-ingredient | 0 | 0 |

Legendary-cadence contribution: 2 of the 10 total 5-ing legendaries across
the 100-floor run (F91-F100 slot of the F51/F61/F71/F81/F91 cadence).

---

## Recipes

### 1. `legendary_surtur_ragnarok_feast` — "Surtur's Ragnarok Feast"

- **outcome_id:** `t5_mythic_ragnarok`
  (SP 165, HP 25, heroism +4 for 200t, `max_hp_bonus +10`,
  `permanent_power: all_stats_plus_1`)
- **ingredients (sorted):**
  - `apocalypse_herald_prime` (min_level 91, demon) — band ingredient
  - `hrungnirs_ghost_trophy` (min_level 80, undead)
  - `nidhoggr_fragment_trophy` (min_level 93, dragon) — band ingredient
  - `surtur_trophy` (min_level 87, elemental)
  - `ymir_last_spawn_trophy` (min_level 82, elemental)
- **effective unlock floor (max min_level):** 93
- **flavor:** "Five last trophies of the end-days -- ember, marrow, scale,
  stone-heart, and herald's ichor -- set to simmer under a burning sky."

Theme: Norse Ragnarok + Revelation apocalypse — Surtur burns the sky, Ymir's
marrow is the primordial frame, Níðhöggr gnaws the roots, Hrungnir's
stone-heart is the giant's war-fist, the Apocalypse Herald blows the final
horn. Name calls out "Surtur" (→ Surtur's Ember). Flavor enumerates each
ingredient in order without naming the mechanical reward (`all_stats_plus_1`,
heroism, +10 max HP).

### 2. `legendary_tiamat_nine_world_soup` — "Tiamat's Nine-World Yggdrasil Soup"

- **outcome_id:** `t5_mythic_yggdrasil`
  (SP 160, HP 25, regenerating +5 for 200t, `max_hp_bonus +15`,
  `permanent_power: chromatic_resist_all`)
- **ingredients (sorted):**
  - `abyssal_locust_prime` (min_level 98, demon) — band ingredient
  - `celestial_guardian_prime` (min_level 85, celestial)
  - `heavenly_angel_prime` (min_level 98, celestial) — band ingredient
  - `tiamat_trophy` (min_level 85, reptile)
  - `void_wyrm_prime` (min_level 83, dragon)
- **effective unlock floor (max min_level):** 98
- **flavor:** "A soup drawn from every branch and root -- chromatic tear,
  void-scale, radiant mote, abyssal ichor, and angel-light -- stirred until
  the colors answer."

Theme: Yggdrasil cosmology — top branches (celestial, angel), middle world
(Tiamat the chromatic dragon mother), bottom roots (void wyrm, abyssal
locust). Name calls out "Tiamat" (→ Tiamat's Chromatic Tear). Flavor
enumerates each ingredient's distinctive form without leaking
`chromatic_resist_all`, regenerating, or +15 max HP.

---

## Validation (all PASS)

1. **Both recipes are 5-ingredient.**
2. **Every ingredient's `min_level` ≤ 100.** Max is 98 across both recipes.
3. **At least one ingredient per recipe in `[91, 100]`.**
   - Recipe 1: `apocalypse_herald_prime` (91) + `nidhoggr_fragment_trophy`
     (93).
   - Recipe 2: `abyssal_locust_prime` (98) + `heavenly_angel_prime` (98).
4. **`outcome_id` resolves** against `data/items/cook_outcomes.json →
   outcomes`.
5. **Both outcomes are `t5_mythic_*`** (`t5_mythic_ragnarok`,
   `t5_mythic_yggdrasil`).
6. **No duplicate sorted ingredient-tuple** against the existing 77
   multi-ingredient recipes nor between the two new recipes. (One existing
   3-tuple shares `heavenly_angel_prime` + `celestial_guardian_prime` with
   recipe 2, but the sorted 5-tuple is distinct — tuple identity is
   length-sensitive.)
7. **No duplicate name** against the 614 existing recipe names.
8. **Caps respected:** no `+2` to a single stat (both outcomes use
   `all_stats_plus_1` / `chromatic_resist_all` which were already approved
   as 5-ing legendary slots in Phase 1 — see Phase-1 audit §Permanent-power
   ids). No new power ids introduced.
9. **SP floor:** 165 (Ragnarok) and 160 (Yggdrasil) both exceed the T5 raw
   emergency floor of 140.
10. **Non-leaking flavor:** no mention of stats, resists, regeneration, or
    max HP in either flavor sentence.

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f91_100.json` — new
  (26 lines, 2 recipes). Hand-off to the Phase-2 merge step; no direct edit
  to `data/items/recipes.json`.
- `docs/audits/cook_expansion_f91_100_2026-10-03.md` — this report (new).
