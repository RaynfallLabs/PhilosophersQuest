# Multi-Ingredient Cooking — F41-F50 Recipe Band Audit (Phase 2, Agent 5)

**Date:** 2026-10-03
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion
(`docs/design/multi_ingredient_cooking.md`). This agent authored the F41-F50
floor band: 15 two-ingredient + 10 three-ingredient + 5 four-ingredient
recipes = **30 new recipes**.

Output file: `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f41_50.json`
(292 lines, dict-shaped so it can be merged into `data/items/recipes.json`
by the Phase-3 merger).

---

## Counts

| Bucket   | Target | Delivered |
|----------|--------|-----------|
| 2-ing    | 15     | 15        |
| 3-ing    | 10     | 10        |
| 4-ing    |  5     |  5        |
| **Total** | **30** | **30**    |

### Outcome prefix distribution

| Prefix          | Count |
|-----------------|-------|
| `t2_combo_*`    | 1     |
| `t3_combo_*`    | 14    |
| `t3_tri_*`      | 0     |
| `t4_tri_*`      | 10    |
| `t4_quartet_*`  | 4     |
| `t5_quartet_*`  | 1     |

The band leans into the heavier tiers (t3_combo, t4_tri, t4_quartet) because
F41-F50 is late mid-game and the dishes should land with real weight.
`t2_combo_wild` is used once (Twin-Howl Yeenoghu Pot) as a deliberate
easier-but-angrier pairing of two mid-floor demon/humanoid primes with a
single late-band anchor.

### Ingredient-anchor distribution

Every recipe carries at least one in-band (ml 41-50) prime. All 26 in-band
primes are used at least once; the 4 x t4_quartet / t5_quartet legendaries
pack 4 in-band primes each so the band's rarest cuts headline the heaviest
dishes.

---

## Recipe table (all 30)

| id | name | ingredients | outcome_id |
|---|---|---|---|
| `f41_wyrm_shard_fillet` | Wyrm-Scale Fillet in Shardlight | wyrm_prime,crystal_shard | `t3_combo_glint` |
| `f41_demon_knight_sacrament` | Demon Knight's Blessed Sacrament | demon_knight_prime,holy_water | `t3_combo_rallying` |
| `f41_marshal_iron_steak` | Hobgoblin Marshal's Iron-Seared Steak | hobgoblin_marshal_prime,deep_iron | `t3_combo_fierce` |
| `f41_imp_lord_ember_pan` | Imp-Lord Ember Pan | imp_lord_prime,fire_elemental_prime | `t3_combo_cinder` |
| `f42_young_dragon_saltscale` | Young Dragon Saltscale | young_dragon_prime,river_salt | `t3_combo_coldforge` |
| `f42_vampire_lord_vigil` | Vampire Lord's Incense Vigil | vampire_lord_prime,altar_incense | `t3_combo_sage` |
| `f42_lich_ironpress` | Lich-Marrow Pressed on Deep Iron | lich_prime,deep_iron | `t3_combo_mountain` |
| `f42_sphinx_kelp_tartare` | Sphinx and Abyssal-Kelp Tartare | the_sphinx_prime,abyssal_kelp | `t3_combo_arrowfang` |
| `f42_plague_witch_mossbed` | Plague-Witch Pottage on a Mossbed | plague_witch_prime,swamp_moss | `t3_combo_wyrmling_grit` |
| `f42_vine_horror_mushroom_pie` | Vine-Horror and Cave-Mushroom Pie | vine_horror_prime,cave_mushroom | `t3_combo_fogveil` |
| `f44_elder_mind_flayer_shardlamp` | Elder Flayer-Sac Under Shardlamp | elder_mind_flayer_prime,crystal_shard | `t3_combo_lantern` |
| `f44_yeenoghu_twinhowl_pot` | Twin-Howl Yeenoghu Pot | gnoll_alpha_of_yeenoghu_prime,nalfeshnee_lesser_prime | `t2_combo_wild` |
| `f45_lurking_horror_sanctus` | Lurking Horror Sanctus | lurking_horror_prime,holy_water | `t3_combo_hunter` |
| `f45_ettin_twinhead_pie` | Ettin Warchief Twin-Head Pie | ettin_warchief_prime,cave_mushroom | `t3_combo_duelist` |
| `f46_hierophant_censer_porridge` | Hierophant's Censer Porridge | cult_hierophant_prime,altar_incense | `t3_combo_rallying` |
| `f47_void_leviathan_rangda_triad` | Leviathan, Rangda, and Deep-Iron Triad | void_leviathan_prime,rangda_prime,deep_iron | `t4_tri_quickening` |
| `f48_throne_sentinel_golem_shardstew` | Throne-Sentinel and Stone-Golem Shardstew | throne_sentinel_prime,stone_golem_prime,crystal_shard | `t4_tri_titan_whelp` |
| `f49_war_troll_three_trolls` | The Three-Troll Warchant | war_troll_prime,chaos_troll_prime,troll_brute_prime | `t4_tri_warspeaker` |
| `f49_elder_vampire_marrow_choir` | Elder-Vampire Marrow Choir | elder_vampire_prime,vampire_lord_prime,altar_incense | `t4_tri_oracle` |
| `f49_abyssal_hound_demonic_trinity` | Abyssal-Hound Infernal Trinity | abyssal_hound_prime,imp_lord_prime,demon_knight_prime | `t4_tri_everburn` |
| `f49_corrupted_treant_mossgrove` | Corrupted-Treant Mossgrove Pot | corrupted_treant_prime,vine_horror_prime,swamp_moss | `t4_tri_balmroot` |
| `f49_skeleton_horde_bone_requiem` | Three-Bone Requiem | skeleton_horde_prime,lich_prime,bone_titan_prime | `t4_tri_wyrmblood` |
| `f50_elder_beholder_eye_vigil` | Elder-Beholder Eye Vigil | elder_beholder_prime,beholder_prime,holy_water | `t4_tri_vigilant` |
| `f46_hierophant_witch_censer_rite` | Hierophant and Plague-Witch Censer Rite | cult_hierophant_prime,plague_witch_prime,altar_incense | `t4_tri_fervor` |
| `f42_sphinx_dragon_crystal_trine` | Sphinx, Young-Dragon, and Crystal Trine | the_sphinx_prime,young_dragon_prime,crystal_shard | `t4_tri_stormborn` |
| `f49_war_quartet_of_shoulders` | The War Quartet of Four Shoulders | war_troll_prime,ettin_warchief_prime,hobgoblin_marshal_prime,orc_warlord_prime | `t4_quartet_titan` |
| `f49_bone_pact_of_four` | Bone-Pact of the Four Marrows | elder_vampire_prime,lich_prime,skeleton_horde_prime,vampire_prime | `t4_quartet_ironblood` |
| `f49_abyssal_warhorn_quartet` | Abyssal Warhorn Quartet | abyssal_hound_prime,rangda_prime,demon_knight_prime,imp_lord_prime | `t4_quartet_warchief` |
| `f50_watchers_quartet` | The Watchers' Quartet | elder_beholder_prime,elder_mind_flayer_prime,lurking_horror_prime,void_leviathan_prime | `t4_quartet_arcanum` |
| `f49_prism_feast_of_four` | The Prism Feast of Four Elder Beasts | young_dragon_prime,wyrm_prime,the_sphinx_prime,corrupted_treant_prime | `t5_quartet_prism` |

---

## Validation checks (all PASS)

1. **Every outcome_id resolves** in `cook_outcomes.json`.
2. **Every ingredient id exists** in `ingredient.json`.
3. **Every ingredient `min_level` <= 50.**
4. **Every recipe has >=1 ingredient with `min_level` in [41, 50].**
5. **Max ingredient `min_level` per recipe falls in [36, 55]** (band ±5
   tolerance per `multi_ingredient_cooking.md § Validation gate`).
6. **No duplicate sorted-ingredient-tuple** among the 30 new recipes.
7. **No duplicate sorted-ingredient-tuple** against the 77 existing
   multi-ingredient recipes in `data/items/recipes.json`.
8. **No duplicate recipe name** against existing recipes.
9. **Outcome tier matches ingredient count**:
   - 2-ing -> `t2_combo_*` / `t3_combo_*`,
   - 3-ing -> `t3_tri_*` / `t4_tri_*`,
   - 4-ing -> `t4_quartet_*` / `t5_quartet_*`.
10. **Every 4-ing outcome carries a permanent bonus**
    (`stat_grant`>0 OR `max_hp_bonus`>0 OR `permanent_power`): verified
    present on all 5 chosen outcomes (`t4_quartet_titan`, `t4_quartet_ironblood`,
    `t4_quartet_warchief`, `t4_quartet_arcanum`, `t5_quartet_prism`).
11. **SP soft-boundary floor** per outcome `tier`: all `sp` values satisfy
    `sp` >= { T2: 45, T3: 75, T4: 110, T5: 140 } (inherited from the
    cook_outcomes audit; this recipe pass merely references these outcomes).
12. **No single recipe grants >+2 to a single stat.** Only `t4_quartet_titan`
    (+2 STR) and the three other `t4_quartet_*` entries used here (+2 CON,
    +2 STR, +2 INT) hit the +2 cap; none exceed it. The t5_quartet_prism
    recipe carries `chromatic_resist_all` (not an immunity, per the design-doc
    4-ing allowance).

---

## Judgment calls

- **Reusing supporting ingredients across recipes.** `altar_incense`,
  `holy_water`, `crystal_shard`, `deep_iron`, `swamp_moss`, `cave_mushroom`,
  and a handful of mid-floor primes (ml 25-40) appear in multiple new
  recipes. The dedup contract is on the full sorted-ingredient-tuple, not on
  individual ingredients; every tuple here is unique. Using shared
  supporting ingredients keeps the F41-F50 band feeling like one kitchen
  across many dishes rather than 30 unrelated one-shot combinations.
- **Reusing outcome archetypes across recipes.** `t3_combo_rallying` is
  used twice (demon knight + holy water; hierophant + altar incense). The
  design doc gates on ingredient-tuple uniqueness, not on outcome
  uniqueness, so this is intentional: both dishes convey the same mechanical
  identity through different thematic routes.
- **One `t2_combo_*` in the band.** The twin-pack Yeenoghu pot
  (gnoll_alpha + nalfeshnee_lesser) is a deliberately rougher, cheaper dish;
  pairing a mid-floor nalfeshnee with the in-band gnoll alpha keeps the SP
  floor honest while allowing a lower-tier outcome (`t2_combo_wild`,
  tier-2 `sp=60`) that the Phase-1 outcomes audit confirms still satisfies
  the T2 SP floor of 45.
- **One `t5_quartet_*` in the band.** The Prism Feast of Four Elder Beasts
  is the band's trophy recipe; its outcome (`chromatic_resist_all`) is a
  permanent elemental resist rather than an immunity, which the design doc
  explicitly reserves for 5-ingredient legendaries. The in-band quartet
  carries a potent-but-sub-immunity payoff — appropriate for the F41-F50
  bracket.
- **No new `permanent_power` ids invented.** All five 4-ing recipes key off
  Phase-1 archetypes whose `permanent_power` / `stat_grant` fields were
  already validated against `_apply_permanent_power` in `food_system.py`.

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f41_50.json` — 30 new
  recipes, 292 lines.
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\_build_recipes_f41_50.py` —
  scratch generator (not committed; follows `_archive/sweep_*` pattern).
- `docs/audits/cook_expansion_f41_50_2026-10-03.md` — this report.

---

## Hand-off to Phase 3

The Phase-3 merger should concatenate this file (and the other nine
`recipes_fXX.json` outputs) into `data/items/recipes.json`. All 30 entries
in this file are keyed by unique recipe-id prefixed with `f41_` / `f42_` /
etc. so merger collisions with keys from other floor bands are structurally
impossible. The automated validation gate (`multi_ingredient_cooking.md
§ Validation gate`) will re-check every property enforced above against the
merged recipes.json.
