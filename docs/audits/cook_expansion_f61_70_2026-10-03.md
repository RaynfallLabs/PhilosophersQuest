# Cooking Expansion — F61-F70 Floor Band (Phase 2, Agent Cook-P2)

**Date:** 2026-10-03
**Scope:** 27 new multi-ingredient recipes for floors F61-F70, per
`docs/design/multi_ingredient_cooking.md` and the Phase-1 outcome archetypes
audited in `docs/audits/cook_expansion_outcomes_2026-10-03.md`.
**Output:** `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f61_70.json`
(271 lines, 27 recipe entries).

---

## Quota — target vs delivered

| Ing count | Target | Delivered | Outcome bucket(s) used |
|-----------|--------|-----------|---------------------|
| 2         | 10     | 10        | `t3_combo_*` ×10   |
| 3         | 10     | 10        | `t4_tri_*` ×10     |
| 4         |  5     |  5        | `t4_quartet_*` ×4 + `t5_quartet_*` ×1 |
| 5         |  2     |  2        | `t5_mythic_*` ×2   |
| **Total** | **27** | **27**   |                     |

Outcome-tier histogram over the 27 recipes: T3 ×10, T4 ×14, T5 ×3. The band
leans T3/T4 — F61 is the opening of the band, and T5 is reserved for the four
most consequential recipes (the one 5-color quartet and the two legendaries).

## Floor-band constraint — enforced

Every recipe has at least one ingredient with `min_level ∈ [61, 70]`, and no
recipe contains any ingredient with `min_level > 70`. The band author uses the
full set of 23 F61-F70 primes available in `data/items/ingredient.json`
(min_level distribution 62→68: 2/9/2/4/1/3/2) with each appearing at least once
across the 27 recipes.

## Ingredient pool used (F61-F70, all 23 appear)

- **F62 (humanoid/undead):** `frostfang_giant_prime`, `crypt_summoner_prime`
- **F63 (mixed, 9):** `lich_sovereign_prime`, `ancient_vampire_lord_prime`,
  `elder_storm_giant_prime`, `primordial_fire_elemental_prime`,
  `zombie_legion_prime`, `mythic_hydra_prime`, `shadow_assassin_prime`,
  `plague_ooze_prime`, `shadow_archer_prime`
- **F64 (beast/humanoid):** `jormungandr_juvenile_prime`,
  `veiled_inquisitor_prime`
- **F65 (elemental/demon/undead/celestial):**
  `primordial_ice_elemental_prime`, `demon_general_prime`, `dracolich_prime`,
  `corrupted_angel_prime`
- **F66:** `banshee_lich_prime`
- **F67 (beast/humanoid/demon):** `sets_jackal_prime`, `titan_prime`,
  `abyssal_behemoth_prime`
- **F68 (demon/elemental):** `demon_emperor_prime`, `lava_elemental_prime`

## Dedup — validated against the full 614-recipe baseline

- **Sorted-ingredient-tuple collisions:** 0 against existing recipes;
  0 within the new 27.
- **Name collisions:** 0 against existing recipes; 0 within the new 27.

## Legendary cadence — 2 mythic names

Per `multi_ingredient_cooking.md` §"5-ingredient legendary cadence":

1. **"The Burning-Thrones Compact: Demon-King's Last Pact"** —
   `abyssal_behemoth_prime + demon_emperor_prime + demon_general_prime +
   lava_elemental_prime + primordial_fire_elemental_prime` →
   `t5_mythic_demons_pact` (fire_resist + WIS+1 + one_time_death_save).
   Five fire-crowned infernal cuts around a shared oath.
2. **"Blood-Moon Rite of the Five Un-Dying"** —
   `ancient_vampire_lord_prime + banshee_lich_prime + dracolich_prime +
   lich_sovereign_prime + zombie_legion_prime` → `t5_mythic_blood_moon`
   (berserk + STR+1 + lifesteal_5pct_on_melee). Five un-dying thrones around
   a shared red lid.

Both names invoke their specific ingredient collection and carry mythic weight.

## Naming — mandatory call-out of at least one ingredient per name

Every recipe name either names a specific ingredient (e.g. *"Frostfang-and-
Rimeheart Pot"*, *"Jackal-and-Assassin Fleet-Pot"*, *"Vampire-Legion
Dark-Balmroot Pot"*) or a canonical family synonym (*"Three-Titan"* for the
titan + hydra + storm-giant trio, *"Dark-Council"* for the four-lich terrine,
*"Quartet of the Burning Thrones"* for the four demon-lords). A kid reading
"Frostfang" can match it to the `frostfang_giant_prime` corpse in their pack.

## Flavor — one sentence, non-leaking

Each recipe has a single evocative sentence of cooking narration keyed to the
senses or ritual (`"the lid rattles like a war-drum"`,
`"the ladle insists on turning left"`,
`"the broth answers back when poured"`). No flavor text names the keyed
outcome, stat_grant, immunity, or permanent_power — only taste, smell, sound,
ritual, atmosphere.

## Hard-cap compliance (per `multi_ingredient_cooking.md`)

- **No single recipe grants more than +2 to a single stat.** The four t4_quartet
  outcomes used (`t4_quartet_titan`, `_mystagogue`, `_warchief`, `_hawkeye`)
  each grant `+2` to exactly one stat.
- **No immunity outside 5-ing.** The single 4-ing `t5_quartet_elementcrown`
  recipe carries `chromatic_resist_all` (a resist, not an immunity). Both
  5-ing legendaries carry non-immunity permanent powers
  (`one_time_death_save`, `lifesteal_5pct_on_melee`); no immunity assigned in
  this band (Agent Cook-P1 for F51-F60 already carries the two band immunities,
  per convention).
- **SP soft-boundary preserved.** All chosen outcomes have `sp` ≥ the raw-eat
  tier floors verified in Phase 1 (T3: 75, T4: 110, T5: 140).
- **Phasing.** No ingredient has `min_level > 70`, so the recipes do not
  unlock before their intended band.

## Automated validation (all PASS)

Script run from `gen_recipes_f61_70.py` + harness in-band check:

1. Every `outcome_id` resolves in `cook_outcomes.json`. **PASS** (27/27).
2. Every ingredient id resolves in `ingredient.json`. **PASS** (23 unique).
3. No duplicate sorted-ingredient-tuples (new + existing). **PASS** (0/27).
4. No duplicate recipe names (new + existing). **PASS** (0/27).
5. Every recipe has ≥1 ingredient with `min_level ∈ [61, 70]`. **PASS**.
6. No ingredient has `min_level > 70`. **PASS**.
7. Outcome prefix matches ingredient count. **PASS** (2-ing →
   `t2_combo_|t3_combo_`, 3-ing → `t3_tri_|t4_tri_`, 4-ing →
   `t4_quartet_|t5_quartet_`, 5-ing → `t5_mythic_`).

## Three sample names

- Non-legendary: *"Three-Primordial Prism Stew"*
  (frostfang_giant_prime + primordial_fire_elemental_prime +
  primordial_ice_elemental_prime).
- Legendary ×2:
  - *"The Burning-Thrones Compact: Demon-King's Last Pact"*
  - *"Blood-Moon Rite of the Five Un-Dying"*

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f61_70.json` —
  **27 recipes**, 271 lines (new).
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\gen_recipes_f61_70.py` —
  scratch generator (new, not committed).
- `docs/audits/cook_expansion_f61_70_2026-10-03.md` — this report (new).

## Hand-off

The 27 F61-F70 recipes are ready for the Phase-3 merge step into
`data/items/recipes.json`. Dedup already pre-checked against the full
614-recipe baseline, so merge is additive with zero conflict expected from
this band.
