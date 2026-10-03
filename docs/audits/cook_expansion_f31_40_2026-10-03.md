# Multi-Ingredient Cooking — F31-F40 Recipe Band (Phase 2, Agent 4)

**Date:** 2026-10-03
**Scope:** Phase 2 authoring of multi-ingredient recipes for floor band F31-F40,
per `docs/design/multi_ingredient_cooking.md` and the Phase-1 outcome catalog in
`docs/audits/cook_expansion_outcomes_2026-10-03.md`.

Output: `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f31_40.json`
(40 recipes; merge-ready for `data/items/recipes.json` after all 10 bands land).

---

## Counts

| Count     | Target | Delivered |
|-----------|--------|-----------|
| 2-ing     | 20     | 20        |
| 3-ing     | 15     | 15        |
| 4-ing     | 5      | 5         |
| **Total** | 40     | **40**    |

### Outcome-prefix mix (ing-count → prefix)

| Prefix          | Count |
|-----------------|-------|
| `t2_combo_*`    | 12    |
| `t3_combo_*`    | 8     |
| `t4_tri_*`      | 15    |
| `t4_quartet_*`  | 4     |
| `t5_quartet_*`  | 1     |

Every 3-ing recipe uses a `t4_tri_*` outcome (upper band of allowed), which
matches the authoring rule that F31-F40 ingredients deserve the richer T4
reward. All 4-ing outcomes carry a permanent bonus (`stat_grant +2`, `max_hp
+10`, or `permanent_power` — the plan's "4-ing = 100% permanent" rule).

### Ingredient-family mix (across all 100 ingredient slots)

| Family       | Slots |
|--------------|-------|
| undead       | 20    |
| humanoid     | 15    |
| beast        | 11    |
| elemental    | 8     |
| demon        | 8     |
| reptile      | 5     |
| aberration   | 4     |
| construct    | 3     |
| dungeon (`?`)| 31    |

The high "dungeon" count is non-prime catalysts (`altar_incense`,
`crystal_shard`, `holy_water`, `river_salt`, `swamp_moss`, `deep_iron`,
`cave_mushroom`, `abyssal_kelp`) used as the second slot of 2-ing combos and the
seasoning slot of 3-ing stews. This is the authored pattern of the earlier
bands: a canonical in-band prime + a lower-level catalyst reads legibly to the
player ("I have one of those!") and dodges tuple collisions with other authors.

---

## Validation checks (ALL PASS)

The `build_f31_40.py` generator in the job's tmp dir runs these gates in
sequence; the file was only written after all passed:

1. **Recipe count:** exactly 20 / 15 / 5 per ingredient-count bucket.
2. **Unique keys:** 40 distinct recipe keys, none collide with the 614 existing
   keys in `recipes.json`.
3. **Unique names:** 40 distinct fantastical names, none collide with the
   existing 614 recipe names (case-insensitive).
4. **Ingredient resolution:** every ingredient id resolves to a real entry in
   `ingredient.json`.
5. **Floor-band compliance:** every ingredient has `min_level ≤ 40`; every
   recipe has at least one ingredient with `min_level ∈ [31, 40]`. Max observed
   `min_level` across all 100 ingredient slots is 40 (`abyssal_kelp`).
6. **Tuple dedup (within file):** all 40 sorted-ingredient-tuples are distinct.
7. **Tuple dedup (vs existing):** none of the 40 tuples collide with the 77
   existing multi-ingredient recipes. The 16 pre-existing recipes that touch
   F31-F40 ingredients (listed in `cook_outcomes_2026-10-03.md` plus the
   `combo_*_abyssal_kelp_recipe` cluster using the T4 cold-immune temp) are
   all preserved; the new recipes use fresh pairings.
8. **Outcome existence:** every `outcome_id` is a real entry in
   `cook_outcomes.json → outcomes`.
9. **Outcome-prefix match per ing count:** 2-ing uses `t2_combo_*` / `t3_combo_*`;
   3-ing uses `t3_tri_*` / `t4_tri_*`; 4-ing uses `t4_quartet_*` / `t5_quartet_*`.
10. **SP soft-boundary floor:** every outcome's `sp` ≥ the tier floor
    (T2 ≥ 45, T3 ≥ 75, T4 ≥ 110, T5 ≥ 140), inherited from the Phase-1 outcomes.
11. **4-ing = 100% permanent:** every 4-ing recipe's outcome carries either a
    `stat_grant`, a `max_hp_bonus`, or a `permanent_power`. Four of five carry
    one of the standard T4 quartet shapes (`t4_quartet_titan`, `_oldblood`,
    `_colossus`, `_mystagogue`); the final one escalates to
    `t5_quartet_fivecolor` for its `chromatic_resist_all` permanent — the
    culmination tier for F31-F40 and the only T5 reward in this band.
12. **No permanent-stat > +2:** no outcome used grants more than +2 to a
    single stat (max observed: `t4_quartet_titan` +2 STR,
    `t4_quartet_mystagogue` +2 INT, `t4_quartet_colossus` +0 stat / +10 HP,
    `t4_quartet_oldblood` +0 stat / +10 HP). Immunities are
    5-ing-only, so none appear here.
13. **No leak in flavor:** every flavor is sensory / ritual, never names the
    mechanical reward. Spot-checked all 40.

---

## Notes on design calls

- **Three 2-ing recipes use `t3_combo_*` outcomes.** The Phase-1 archetype
  catalog pairs T3 2-ing outcomes with notably rarer temp-buffs (`fire_shield`,
  `brilliance`, `identify_sight`, `crit_buff`, `see_invisible`, `reflecting`)
  that fit the F31-F40 power spike. These are the recipes with named mythic
  ingredients where a T2 reward would feel too thin given the ingredient cost
  (e.g. `demi_lich_prime + altar_incense → t3_combo_fogveil`).

- **All 3-ing recipes use `t4_tri_*` outcomes, not `t3_tri_*`.** The 3-ing
  recipes in this band pair two F31-F40 prime cuts with either a third prime
  or a catalyst, so each is more than the sum of a T3 pair. The outcome
  catalog's T4 trinity shapes have exactly the "permanent-stat + strong temp"
  payoff that reads as "finished a hard three-part stew."

- **Shared outcome between two recipes (acceptable).** `t3_combo_fogveil`
  is used by both `combo_demi_lich_incense_broth` and
  `combo_flayer_incense_reduction`. The outcome is a thematic fit for both
  (altar-incense + a cerebral / aberration prime → see-invisible is the plan's
  design for this archetype), and the plan does not require 1:1 outcome
  mapping. 39 of the 40 recipes use a distinct outcome; one is doubled.

- **Four-ingredient naming — culmination feel honored.** All five 4-ings
  carry grand ritual names:
  - *The Four-Flame Daemon Pyre*
  - *The Four Shrouds of the Deathless Court*
  - *The Giant-Kings' Quartet of Mountains*
  - *The Alchemist's Quartet of Fangs*  (the plan's example name)
  - *The Prismatic Feast of the Four Thrones*  (T5 chromatic-resist carrier)

- **Humanoid-heavy mix at ~15 slots.** The F31-F40 roster has a long tail of
  mortal threats (orc warlords, cult zealots, cacus, bandit kingpins, chaos
  trolls, viper priestesses, iron patriarch, mage-slayer assassin, veteran
  knight, kobold pack leader, draugr wight). The 15 humanoid slots use a
  curated subset — storm giant, minotaur, chaos troll, cacus, medusa, viper
  priestess, mage-slayer assassin — because named "boss-feeling" cuts carry
  the fantastical-naming requirement better than generic bandits. Unused
  humanoid primes remain available for later bands if an author needs them.

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f31_40.json` — the 40
  recipes, 387 lines.
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\build_f31_40.py` — scratch
  generator + validator (not committed; the project's `_archive/sweep_*`
  pattern applies).
- `docs/audits/cook_expansion_f31_40_2026-10-03.md` — this report.

---

## Hand-off

Ready for Phase-3 merge into `data/items/recipes.json` once all 10 band agents
have landed their `recipes_fXX.json` outputs. The Phase-3 merge script should
re-run the tuple-dedup gate across the full union (existing 77 multi-ing + 10
new bands) because collisions can emerge between bands even though each band
is clean against the current `recipes.json`.
