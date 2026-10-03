# Multi-Ingredient Cooking — F71-F80 Recipe Band Audit (Phase 2 / Agent 8)

**Date:** 2026-10-03
**Scope:** Phase 2 of the Multi-Ingredient Cooking Expansion
(`docs/design/multi_ingredient_cooking.md`). This audit covers the 15 new
multi-ingredient recipes authored for the F71-F80 floor band and staged at
`$CLAUDE_JOB_DIR/tmp/recipes_f71_80.json`.

Recipes are intermediate output. They are merged into
`data/items/recipes.json` after all 10 floor-band agents complete.

---

## Counts (target vs delivered)

| Bucket | Target | Delivered | Outcome archetype pool used |
|---|---|---|---|
| 2-ingredient | 5 | 5 | `t3_combo_*` (5 picks — hp_bonus or stat_grant carriers) |
| 3-ingredient | 5 | 5 | `t4_tri_*` (5 picks — all `stat_grant +1`) |
| 4-ingredient | 3 | 3 | `t4_quartet_*` + 1 × `t5_quartet_*` (prism) |
| 5-ingredient MYTHIC | 2 | 2 | `t5_mythic_phoenix` + `t5_mythic_leviathan` |
| **Total** | **15** | **15** | |

### Permanent-bonus distribution
- 2-ing (5): 2 × `max_hp_bonus` (+2/+3), 2 × `stat_grant +1` (PER / DEX), 1 × `max_hp_bonus +3`.
- 3-ing (5): 5 × `stat_grant +1` (3 × CON, 1 × STR, 1 × DEX).
- 4-ing (3): 1 × `stat_grant +2` INT (arcanum), 1 × `max_hp_bonus +10` (colossus), 1 × `permanent_power: chromatic_resist_all` (prism).
- 5-ing (2): 1 × fire_immunity + `stat_grant +1 STR` (phoenix); 1 × chromatic_resist_all + `stat_grant +1 CON` + `max_hp_bonus +10` (leviathan).

Both 5-ing picks match the audit's two-slot legendary pattern (an immunity /
all-element resist paired with a stat or HP bump). They honor the §51 cadence
(2 mythic recipes per band in F51-F100).

---

## Ingredients used

### F71-F80 band primes/trophies (16 total; 14 used across the 15 recipes)
- `world_serpent_prime` (72), `green_knight_trophy` (72), `abyssal_mimic_prime` (73),
  `entropy_wraith_prime` (75), `blood_archon_prime` (75), `charybdis_prime` (76),
  `astral_horror_prime` (76), `ancient_dragon_prime` (78), `death_lord_prime` (78),
  `chaos_spawn_prime` (78), `soul_eater_prime` (78), `fenrir_wolf_prime` (78),
  `ravanas_arm_prime` (78), `hrungnirs_ghost_trophy` (80).
- Unused this band: `blood_archon_trophy` (75), `fenrir_wolf_trophy` (78) — the
  trophy variants carry their own single-ingredient trophy recipes already
  (`trophy_blood_archon_recipe`, `trophy_fenrir_wolf_recipe`); leaving them out
  of combos preserves the trophy identity signal and keeps room for other
  authoring passes.

### F61-F70 primes used as supporting cuts (max min_level ≤ 80 constraint)
- `primordial_ice_elemental_prime` (65), `primordial_fire_elemental_prime` (63),
  `elder_storm_giant_prime` (63), `plague_ooze_prime` (63), `titan_prime` (67),
  `abyssal_behemoth_prime` (67), `lava_elemental_prime` (68),
  `lich_sovereign_prime` (63), `banshee_lich_prime` (66),
  `jormungandr_juvenile_prime` (64).

### Terrain / dungeon ingredients (common foraging layer)
- `altar_incense` (1), `swamp_moss` (5), `river_salt` (10), `holy_water` (15),
  `crystal_shard` (20), `deep_iron` (30), `abyssal_kelp` (40).

---

## Validation checks (all PASS)

1. **No key collisions.** All 15 recipe keys are disjoint from the 614
   pre-existing recipe keys in `data/items/recipes.json`.
2. **No ingredient-tuple collisions.** Every new sorted-ingredient-tuple is
   disjoint from the 614 existing tuples AND unique among the 15 new recipes.
3. **Every ingredient id exists** in `data/items/ingredient.json`.
4. **Every `outcome_id` exists** in `data/items/cook_outcomes.json → outcomes`.
5. **Band constraint.** Every recipe has `max(min_level over ingredients)` in
   `[71, 80]` — satisfies the "effectively unlocks in this band" rule.
6. **Hard-cap compliance (via outcome selection).**
   - No new outcome delivers `stat_grant > 2`.
   - No new outcome delivers a permanent immunity outside the 5-ingredient
     mythic bucket. (The 4-ing `t5_quartet_prism` pick carries
     `chromatic_resist_all`, a resist, not an immunity — matches the Phase 1
     audit's judgment call.)
7. **SP soft-boundary floor.** Every selected outcome's `sp` ≥ its tier floor
   per the Phase 1 audit (T3: 75, T4: 110, T5: 140). Verified against
   `cook_outcomes.json` entries at build time.
8. **No duplicate recipe names.** All 15 `name` strings are unique.
9. **Fantastical name rule.** Every name calls out at least one ingredient
   in-the-clear (e.g. "World-Serpent", "Hrungnir-Ghost", "Fenrir-Fang"); no
   name is reused from the pre-existing bank.
10. **Non-leaking flavor.** No `flavor` string reveals the keyed outcome
    (no "+1 CON", "immunity", "chromatic", "stat bump", etc.).

---

## Judgment calls

- **No `t5_quartet_elementcrown` / `t5_quartet_fivecolor` picks.** These two
  outcomes also carry `chromatic_resist_all` but are themed on elemental
  harmony; the F71-F80 ingredient roster is already heavy with specific-fire
  and specific-cold primes earmarked for the F71-F80 mythic phoenix /
  leviathan picks. `prism` is used once and the other two are left for later
  bands.
- **Fire-themed mythic uses two fire primes.** The phoenix picks a
  deliberate four-corner fire ensemble (ancient dragon haunch, Ravana's
  arm, primordial fire-elemental, lava elemental) around altar incense as
  the lamp. This maximizes the "burning kings' feast" scene while keeping
  the max ingredient min_level at 78 (ancient_dragon_prime,
  ravanas_arm_prime), well within the ≤ 80 cap.
- **Water-themed mythic uses two serpent primes.** The leviathan picks
  the three deep-water primes (`world_serpent_prime`,
  `jormungandr_juvenile_prime`, `charybdis_prime`) plus
  `abyssal_mimic_prime` and `abyssal_kelp` — the whole dish is one coherent
  sea-feast image. Max min_level 76 (charybdis).
- **Three trophy-tier picks promoted into multi-ing combos
  (`green_knight_trophy`, `hrungnirs_ghost_trophy` ×2).** These are trophy
  ingredients, not primes, so they can appear in combos without undercutting
  their respective single-ingredient trophy recipes. Hrungnir's ghost is
  the lone min_level=80 ingredient in the game, so it anchors two of the
  three top-shelf recipes (titan-whelp terrine and colossus-marrow quartet)
  to pull real weight at the band ceiling.
- **No recipe uses the exact ingredient set of any trophy recipe.** A
  trophy recipe's single-item tuple will never equal a multi-ing tuple, so
  this is automatically clean, but it was explicitly checked.

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f71_80.json` — new
  (15 recipes, 154 lines).
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\gen_recipes_f71_80.py` — scratch
  generator / validator (not committed; the project's `_archive/sweep_*`
  pattern applies).
- `docs/audits/cook_expansion_f71_80_2026-10-03.md` — this report (new).

No live project files under `data/` were modified by this agent; the recipes
JSON is intermediate output per
`docs/design/multi_ingredient_cooking.md § Write targets`.

---

## Hand-off to Phase 3 (merge gate)

The 15 recipes at `recipes_f71_80.json` are ready to merge into
`data/items/recipes.json`. The Phase 3 validation gate should re-run the
same six checks listed in the design doc:

1. Every `outcome_id` resolves in `cook_outcomes.json` — PASS this agent.
2. Every ingredient id resolves in `ingredient.json` — PASS this agent.
3. No duplicate sorted-ingredient-tuples across ALL recipes new+existing —
   PASS this agent against the current snapshot; the cross-agent check is
   Phase 3's responsibility.
4. Every recipe's max-ingredient-min_level is in `[71, 80]` — PASS this
   agent (±5 tolerance explicitly not needed; all 15 sit inside the band).
5. Permanent-bonus caps per phase — PASS this agent.
6. SP output ≥ tier floor — PASS this agent (inherited from Phase 1
   outcome selection).
