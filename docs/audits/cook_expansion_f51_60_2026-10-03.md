# Cook Expansion — F51-F60 Band Audit (Cook-P2 agent)

**Date:** 2026-10-03
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion
(`COOKING_EXPANSION_PLAN.md`, `docs/design/multi_ingredient_cooking.md`).
This audit covers the 27 recipes authored for the F51-F60 floor band and
written to `$CLAUDE_JOB_DIR/tmp/recipes_f51_60.json`.

---

## Deliverable

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f51_60.json` — 27 recipes,
  167 lines, 8,278 bytes.

## Quota compliance

| Ing count | Required | Delivered | Outcome prefixes used |
|-----------|---------:|----------:|-----------------------|
| 2         | 10       | 10        | `t2_combo_*` (2) + `t3_combo_*` (8) |
| 3         | 10       | 10        | `t3_tri_*` (2) + `t4_tri_*` (8) |
| 4         |  5       |  5        | `t4_quartet_*` (4) + `t5_quartet_*` (1) |
| 5         |  2       |  2        | `t5_mythic_*` (2) |
| **Total** | **27**   | **27**    |                   |

## Outcome-tier distribution

| Tier | Count |
|------|------:|
| T2   | 2     |
| T3   | 10    |
| T4   | 12    |
| T5   | 3     |

The two T2 outcomes are 2-ingredient recipes (`t2_combo_barrow` on
Death-Lord Hallowed Marrow and `t2_combo_shadow` on Trickster-Smoke
Hood-Broth) — kept for thematic fit; both still clear the T2 SP floor of 45.

## Floor-band compliance

- All 27 recipes have at least one ingredient with `min_level ∈ [51, 60]`.
- No recipe uses an ingredient with `min_level > 60`.
- Ingredient primes drawn from the band: `elder_dragon_prime` (60),
  `adult_dragon_prime` (58), `fafnir_dragon_trophy` (58),
  `greater_lich_prime` (58), `arch_demon_prime` (58), `iron_golem_prime` (58),
  `baba_yaga_prime` (58), `gilded_mimic_prime` (58), `abyssal_overlord_prime`
  (56), `goblin_kingslayer_prime` (56), `whispering_crone_trophy` (55),
  `demonic_trickster_prime` (55), `deep_one_priest_prime` (55),
  `dread_wyrm_prime` (53), `nemean_lion_prime` (53), `lich_lord_prime` (53),
  `spectral_dragon_prime` (not used), `pit_fiend_spawn_prime` (52),
  `frost_giant_jarl_prime` (51), `fire_giant_king_prime` (51),
  `death_knight_lord_prime` (51), `arcane_golem_prime` (51),
  `dread_sphinx_prime` (51), `demon_captain_prime` (51), `iron_sentinel_prime`
  (51), `dread_orc_champion_prime` (not used — reserved for sister bands),
  `skeleton_lich_prime` (51), `grave_knight_prime` (51).
- Secondary ingredients: F41-F50 primes (`young_dragon_prime`, `wyrm_prime`,
  `war_troll_prime`, `the_sphinx_prime`, `elder_mind_flayer_prime`,
  `beholder_prime`, `lich_prime`, `abyssal_hound_prime`, `imp_lord_prime`),
  plus pantry (`crystal_shard`, `deep_iron`, `holy_water`, `altar_incense`,
  `swamp_moss`, `river_salt`, `abyssal_kelp`).

## Dedup checks (all PASS)

1. **No duplicate ingredient-tuples across the 27 new recipes.**
2. **No ingredient-tuple collisions with the pre-existing 614 recipes.**
3. **No duplicate recipe `name` across new + existing.**
4. **No duplicate recipe-id across new + existing.**

## Outcome shape

- All 27 `outcome_id`s resolve to entries in `data/items/cook_outcomes.json`.
- SP floor compliance (`feedback_sp_soft_boundary.md`): every outcome's SP ≥
  the ing-count tier floor (2-ing ≥ 45, 3-ing ≥ 75, 4-ing ≥ 110, 5-ing ≥ 140).
- Permanent-bonus caps:
  - All 5 4-ing recipes carry a permanent bonus (`stat_grant +2` x 4 or
    `permanent_power: chromatic_resist_all` x 1) — zero immunities.
  - Both 5-ing legendaries carry a two-slot legendary bonus
    (`t5_mythic_sunforge`: heroism temp + STR+1 + `chromatic_resist_all`;
    `t5_mythic_banquet_of_kings`: save_guard_all + max_hp +5 +
    `all_stats_plus_1`). No fire/cold/petrify immunities issued in this band —
    those are reserved for later bands to pace the legendary curve across the
    full 100-floor run.

## Legendary names

Per the "mythic, god-tier" rule for 5-ing recipes:

1. **The Sun-Forge Cauldron of First-Age Flame** — elder dragon + fire giant
   king + Fafnir's trophy + arch demon + deep iron.
2. **The Nine-Night Feast of the Dead Crone-Kings** — Baba Yaga + whispering
   crone trophy + greater lich + lich lord + altar incense.

Both names call out at least one ingredient family (dragons/giants/flame
for the first; crones/liches/undeath for the second) so the player can
recognize the ingredient in the name.

## Sample names (span tiers)

- `Elder-Wyrm Prism Pot` (2-ing, dragon + crystal shard, reflecting buff)
- `The Thrice-Wise Crone-Pot` (4-ing, Baba Yaga + Whispering Crone + lich +
  incense, permanent WIS +2)
- `The Sun-Forge Cauldron of First-Age Flame` (5-ing legendary — permanent
  chromatic resist + STR +1)
- `The Nine-Night Feast of the Dead Crone-Kings` (5-ing legendary — permanent
  all stats +1 + max_hp +5)

## Flavor-leak check

Each `flavor` string is one sentence, evocative, and does NOT name the keyed
mechanical effect. (E.g. the Sun-Forge Cauldron's flavor says "the pot hums
the same note the sun hums" — not "grants chromatic resist".)

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f51_60.json` (new, 27 recipes)
- `docs/audits/cook_expansion_f51_60_2026-10-03.md` (this report, new)
