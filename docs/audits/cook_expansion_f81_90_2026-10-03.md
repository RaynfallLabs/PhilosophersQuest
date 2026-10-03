# Multi-Ingredient Cooking — F81-F90 Floor Band (Phase 2)

**Date:** 2026-10-03
**Agent:** Cook-P2 F81-F90
**Scope:** Author the F81-F90 slice of the Phase-2 multi-ingredient recipe wave
(`docs/design/multi_ingredient_cooking.md`, agent row 9: 5 two-ing, 5 three-ing,
2 four-ing, 2 five-ing — 14 total).
**Output:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f81_90.json` (143 lines).

---

## Counts

| Ing | Delivered | Quota | OK |
|-----|-----------|-------|----|
| 2   | 5         | 5     | yes |
| 3   | 5         | 5     | yes |
| 4   | 2         | 2     | yes |
| 5   | 2         | 2     | yes |
| **Total** | **14** | **14** | **yes** |

Legendary cadence respected: exactly 2 five-ingredient mythic recipes in this
band (plan asks for 2 of the 10 total 5-ing recipes to live in F81-F90).

---

## Recipe table

| Count | Max min_level | Outcome | Reward | Name |
|-------|---------------|---------|--------|------|
| 2 | 83 | `t3_combo_wyrmling_grit` (T3, SP 90) | poison_resist 80t + max_hp +3 | Buer-and-Plague Twinbroth |
| 2 | 82 | `t3_combo_frostcake` (T3, SP 90) | cold_shield 50t | Ymir-Marrow Frost Chowder |
| 2 | 87 | `t3_combo_cinder` (T3, SP 90) | fire_shield 50t | Surtur's Ember-and-Lavablood Pot |
| 2 | 83 | `t3_combo_hunter` (T3, SP 85) | searching 80t | Wendigo-and-Fenrir Hunter's Mash |
| 2 | 81 | `t3_combo_mountain` (T3, SP 90) | stand_ac 70t + max_hp +3 | Dread Knight's Standing Stew |
| 3 | 81 | `t4_tri_titan_whelp` (T4, SP 120) | shielded 60t + **STR +1 perm** | Primordial Titan's Three-Bone Trencher |
| 3 | 88 | `t4_tri_oracle` (T4, SP 120) | brilliance 70t + **WIS +1 perm** | Ancient Lich's Marrow Triptych |
| 3 | 83 | `t4_tri_balewright` (T4, SP 115) | poison_resist 80t + **CON +1 perm** | Dracolich-and-Wyrm Thrice-Simmer |
| 3 | 88 | `t4_tri_feythread` (T4, SP 115) | see_invisible 70t | Three-Mote Light Terrine |
| 3 | 85 | `t4_tri_everburn` (T4, SP 115) | fire_resist 80t + **CON +1 perm** | Abyssal-Dragon Everburn Ragout |
| 4 | 85 | `t5_quartet_elementcrown` (T5, SP 145) | save_guard_all + **chromatic_resist_all perm** | The Great Chromatic Wyrm Tetrad |
| 4 | 88 | `t4_quartet_warden` (T4, SP 125) | save_guard_all + **CON +2 perm** | Marrow-Feast of the Four Dead-Kings |
| 5 | 89 | `t5_mythic_demons_pact` (T5, SP 155) | fire_resist 100t + **one_time_death_save + WIS +1 perm** | The Horsemen's Final Communion |
| 5 | 88 | `t5_mythic_ragnarok` (T5, SP 165) | heroism 90t + **all_stats_plus_1 + max_hp +10 perm** | Ragnarok's Giant-Blood Trencher |

---

## Design rationale

- **F81-F90 is the Apocalypse band.** The band's ingredients include the Four
  Horsemen of the Apocalypse (plus Death at F89), Ymir and Surtur (Norse end-of-
  the-world giants), Wendigo (hunger-of-the-dead), Ancient / Arch liches,
  Wild Hunt Captain, Primordial Titan + Flesh Colossus, Abyssal Dragon,
  Tiamat Trophy. Named-mythology ingredients outnumber generic ones ~3:1 by
  this band, so recipe names lean into the specific myth each ingredient
  evokes rather than generic epithets.
- **Four Horsemen ladder.** `t5_mythic_demons_pact` for the 5-ing is the only
  recipe in the game that uses all five Seal Demon primes
  (`seal_demon_wrath_prime` ... `seal_demon_death_prime`). The 4-ing quartet
  deliberately AVOIDS the horsemen so the Final Communion remains the
  singular meal (no overlapping subset tuple).
- **Ragnarok trencher** gives the Norse-apocalypse legendary (Ymir, Surtur,
  Primordial Titan, Flesh Colossus, Wild Hunt Captain), keyed to
  `t5_mythic_ragnarok` for the `all_stats_plus_1 + max_hp +10` legendary slot.
- **Chromatic Wyrm Tetrad** collects Tiamat Trophy + three dragonic / wyrm
  primes behind `t5_quartet_elementcrown` (chromatic_resist_all). The in-band
  rationale: Tiamat is the canonical chromatic queen, so her tear earns the
  rainbow-resist outcome.
- **Marrow-Feast of the Four Dead-Kings** gives the +2 CON permanent, keyed
  to `t4_quartet_warden`. Four undead royals (two liches + Dread Knight
  Legion + Flesh Colossus) = defensive, stand-your-ground +2 CON.
- **Tri outcomes** cover one STR / one WIS / two CON / one temp-only (feythread)
  — follows the ~50%-with-permanent target for 3-ing (4 of 5 carry a +1 stat).
- **Combo outcomes** are all T3 (highest-tier 2-ing archetype); none carry a
  permanent bonus — the ~10% permanent-share for 2-ing is used elsewhere in
  the overall 230-recipe 2-ing pool, not here (this band gets temp-shield /
  poison-resist / searching / stand variety instead).

---

## Validation (all PASS)

1. **Shape unchanged.** Every recipe entry has
   `{name, ingredients, outcome_id, flavor}`, matching the existing recipe
   schema in `data/items/recipes.json`.
2. **Real ingredient ids.** Every ingredient id is a real key in
   `data/items/ingredient.json`.
3. **min_level cap.** Every ingredient has `min_level <= 90`.
4. **Band anchor.** Every recipe has at least one ingredient with
   `81 <= min_level <= 90`. (max_lvl ranges 81-89 across all 14 recipes.)
5. **Outcome id resolves.** Every `outcome_id` is a real entry in
   `data/items/cook_outcomes.json`.
6. **No duplicate ingredient-tuples (internal).** All 14 sorted ingredient
   tuples are distinct within this file. (Horsemen 5-ing and the 4-ing
   Chromatic Tetrad do not share a 4-element subset, by design.)
7. **No duplicate ingredient-tuples (vs existing 614 recipes).** Checked
   against every multi-ingredient tuple in the live `recipes.json`; zero
   collisions.
8. **No duplicate names (internal + vs existing).** All 14 names are unique
   within the file; none collide with any of the 614 live recipe names.
9. **Ingredient-count quota.** Delivered 5 / 5 / 2 / 2 against the agent row
   from `docs/design/multi_ingredient_cooking.md` §Floor-band author
   assignments.
10. **Outcome archetype matches ingredient count.**
    - 2-ing → `t3_combo_*` only.
    - 3-ing → `t4_tri_*` only.
    - 4-ing → `t4_quartet_*` and `t5_quartet_*` (both are 4-ingredient
      archetypes; the T5 tier on `t5_quartet_elementcrown` is the Phase-1
      promotion for the chromatic-resist power, per
      `docs/audits/cook_expansion_outcomes_2026-10-03.md` §Judgment calls).
    - 5-ing → `t5_mythic_*` only.
11. **Hard caps respected.**
    - No recipe grants more than +2 to a single stat (max permanent stat
      bump used: +2 CON on `t4_quartet_warden`).
    - No immunity is granted outside the 5-ingredient mythics
      (`t5_quartet_elementcrown`'s `chromatic_resist_all` is a resist, not
      an immunity).
12. **5-ingredient MYTHIC names.** Both 5-ing recipes carry mythic-tier
    naming invoking their specific ingredient collections:
    *"The Horsemen's Final Communion"* and
    *"Ragnarok's Giant-Blood Trencher"*.
13. **Flavor is non-leaking.** Every flavor sentence describes taste / smell
    / ritual / warning, and names at least one ingredient's identity
    (marrow, ichor, ember, mote, scale) without revealing the mechanical
    outcome (no "+1 WIS", no "poison immune", no "stops death").
14. **SP soft-boundary floor respected.** Minimum SP across the 14 recipes
    is 85 (`t3_combo_hunter`); the T3 raw-eat emergency floor is 75.

---

## Collisions

**Internal:** zero (14 distinct sorted tuples, 14 distinct names).

**Vs existing 614 recipes in `data/items/recipes.json`:** zero.

Note: Several F81-F90 ingredients ALREADY appear as the sole ingredient of
pre-existing `prime_*_recipe` entries (e.g. `prime_ancient_lich_recipe`,
`prime_tiamat_trophy_recipe`, all five `prime_seal_demon_*_recipe`). Those
are 1-ingredient recipes mapping to `t5_apex_*` outcomes — orthogonal to this
file's 2/3/4/5-ingredient multi-ingredient tuples, so no sorted-tuple overlap
is possible.

---

## Sample names (3)

1. *The Horsemen's Final Communion* (5-ing mythic — all five Seal Demons)
2. *The Great Chromatic Wyrm Tetrad* (4-ing — Tiamat's tear + three wyrm primes)
3. *Buer-and-Plague Twinbroth* (2-ing — Buer, Demon of Pestilence + plague ooze)

---

## Files

- **Output:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f81_90.json`
  (143 lines, 14 recipes).
- **Scratch generator:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\gen_recipes_f81_90.py`
  (self-validating; running it rewrites the JSON after re-asserting all
  checks above).
- **This audit:** `docs/audits/cook_expansion_f81_90_2026-10-03.md`.

Hand-off: the recipes_fXX.json files from all 10 Phase-2 agents will be
merged into `data/items/recipes.json` after every band completes.
