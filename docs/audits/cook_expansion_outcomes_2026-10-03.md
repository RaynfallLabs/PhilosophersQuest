# Multi-Ingredient Cooking — Outcome Archetypes Audit (Phase 1)

**Date:** 2026-10-03
**Scope:** Phase 1 of the Multi-Ingredient Cooking Expansion (`COOKING_EXPANSION_PLAN.md`,
`docs/design/multi_ingredient_cooking.md`). This audit covers the 116 new outcome
archetypes appended to `data/items/cook_outcomes.json → outcomes`.

The pre-existing 120 outcome entries are PRESERVED verbatim; Phase 1 is strictly
additive.

---

## Counts

**Totals after Phase 1:** 236 outcomes (120 existing + 116 new).

### By ingredient-count bucket (target → delivered)

| Bucket   | ID prefix pattern         | Target | Delivered |
|----------|---------------------------|--------|-----------|
| 2-ing    | `t2_combo_*` / `t3_combo_*` | ~30  | 31        |
| 3-ing    | `t3_tri_*` / `t4_tri_*`     | ~40  | 40        |
| 4-ing    | `t4_quartet_*` / `t5_quartet_*` | ~25 | 25     |
| 5-ing    | `t5_mythic_*`               | ~20  | 20        |
| **Total** |                            | **~115** | **116** |

### By outcome tier

| Tier | Count |
|------|-------|
| T2   | 17    |
| T3   | 34    |
| T4   | 42    |
| T5   | 23    |

### Reward-type distribution

- **2-ing (31):** 26 pure temp-buff outcomes + 5 small-permanent carriers
  (≈16% permanent — slightly over the ~10% guideline, kept for theme variety).
  Permanents are modest (`stat_grant +1` or `max_hp_bonus +2/+3`).
- **3-ing (40):** exactly 20 with a `stat_grant +1` or `max_hp_bonus +5`
  (50%); the other 20 are pure temp-buff outcomes with stronger magnitudes
  and durations than the T2 combos.
- **4-ing (25):** 100% permanent:
  - 15 × `stat_grant +2` across all six stats (STR×3, CON×3, DEX×3, INT×2,
    WIS×2, PER×2)
  - 7 × `max_hp_bonus +10`
  - 3 × `permanent_power: chromatic_resist_all` (promoted to T5 because the
    engine's `permanent_power` field bypasses the per-floor softcap and these
    outcomes stack a resist on top of temp buffs).
- **5-ing (20):** 100% legendary two-slot:
  - 10 × immunity (`fire_immunity`, `cold_immunity`, `petrify_immunity`)
    paired with a `stat_grant +1` or `max_hp_bonus +10`.
  - 6 × utility permanent (`revive_once_at_half_hp`, `all_stats_plus_1`,
    `one_time_death_save` ×2, `lifesteal_5pct_on_melee`, `chromatic_resist_all`)
    + a `stat_grant +1`.
  - 4 × max-HP spine (`max_hp_bonus +10/+15`) + a permanent power
    (`chromatic_resist_all`, `max_mp_per_floor_descent_and_poison_immunity`,
    `all_stats_plus_1`).

---

## Permanent-power ids used (and dispatch confirmation)

Every `permanent_power` value in the new outcomes maps to a real branch in
`src/food_system.py::_apply_permanent_power`. No new ids were invented.

| permanent_power id                               | Used by new outcomes                                    |
|--------------------------------------------------|---------------------------------------------------------|
| `fire_immunity`                                  | t5_mythic_phoenix, lavablood, salamander, cinderking     |
| `cold_immunity`                                  | t5_mythic_jotunheim, frostcrown, rimeheart              |
| `petrify_immunity`                               | t5_mythic_adamant, stonebind, basilisk                  |
| `chromatic_resist_all`                           | t5_quartet_prism, elementcrown, fivecolor; t5_mythic_sunforge, yggdrasil, leviathan |
| `revive_once_at_half_hp`                         | t5_mythic_phoenix_rebirth                               |
| `all_stats_plus_1`                               | t5_mythic_banquet_of_kings, ragnarok                    |
| `one_time_death_save`                            | t5_mythic_demons_pact, abyss                            |
| `lifesteal_5pct_on_melee`                        | t5_mythic_blood_moon                                    |
| `max_mp_per_floor_descent_and_poison_immunity`   | t5_mythic_worldtree                                     |

All 14 engine-dispatched permanent-power ids remain available. The following
dispatched ids were deliberately NOT re-used in Phase 1 because they are already
load-bearing on specific trophy outcomes and would blur that identity:
`plus_3_str` (trophy_fenrir, trophy_blood_archon), `plus_2_con_petrify_immune`
(trophy_hrungnir), `plus_2_wis_auto_reveal_secret_doors` (trophy_whispering_crone),
`plus_2_str_confuse_immune` (trophy_asterion), `max_hp_per_floor_descent`
(trophy_fafnir).

---

## Validation checks (all PASS)

1. **No id collisions.** All 116 new ids are disjoint from the pre-existing 120.
2. **Known-buff gate.** Every `temp_power` is a member of `status_effects.BUFFS`
   (`berserk`, `fire_resist`, `cold_resist`, `shock_resist`, `poison_resist`,
   `searching`, `dark_vision`, `regenerating`, `hasted`, `blessed`, `sleep_resist`,
   `fear_immune`, `shielded`, `crit_buff`, `brilliance`, `see_invisible`,
   `reflecting`, `fire_shield`, `cold_shield`, `heroism`, `stand_ac`,
   `identify_sight`, `drain_resist`, `parry_armed`, `riposte_armed`, `truesight`,
   `telepathy`, `displacement`, `invisible`, `life_save`, `save_guard_*`,
   `sustained`).
3. **Known-perm gate.** Every `permanent_power` resolves to a real branch in
   `_apply_permanent_power` (see table above).
4. **SP soft-boundary floor (`feedback_sp_soft_boundary.md`).** For each new
   outcome: `sp` ≥ { T2: 45, T3: 75, T4: 110, T5: 140 }.
5. **Hard-cap compliance.** No new outcome grants `stat_grant` > 2 to a single
   stat. No new outcome grants a permanent immunity outside the 5-ingredient
   `t5_mythic_*` bucket (the three 4-ing-slot `t5_quartet_*` outcomes carry
   `chromatic_resist_all`, which is a resist, not an immunity).
6. **Engine loader.** `food_system._load_outcomes()` loads all 236 entries and
   can retrieve the new ids by key.

---

## Judgment calls

- **Field names: `stat_grant` + `stat_grant_default` + `max_hp_bonus` + `desc`,
  not `stat_bump` / `max_hp_bump` / `flavor`.** The task prompt described the
  outcome shape using `stat_bump: {STAT: +N}`, `max_hp_bump`, and `flavor`, but
  the live engine in `food_system._apply_outcome_body` only reads `stat_grant`
  (int) + `stat_grant_default` (stat name) + `max_hp_bonus` (int) + `desc`.
  Using the task's names would silently drop the mechanical effect. The engine
  field names are therefore used throughout, matching the 120 pre-existing
  outcomes. (A new `archetype: "success"` metadata field is included on every
  new outcome as the prompt requested; the engine does not read it today but
  Phase-2 recipe agents can key off it.)
- **No two-stats-at-once +1+1 shape.** The engine's single `stat_grant` /
  `stat_grant_default` pair cannot grant +1 to STAT_A and +1 to STAT_B
  simultaneously, and the task forbids adding new `permanent_power` dispatch
  branches. The 5-ingredient two-slot legendaries therefore pair `stat_grant +1`
  with either a bundled multi-stat permanent (`all_stats_plus_1`), a +10
  `max_hp_bonus`, a long-duration temp, or an immunity instead of two literal
  single-point stat bumps. The `all_stats_plus_1` ids (`t5_mythic_banquet_of_kings`,
  `ragnarok`) do deliver the "multiple stats at once" fantasy.
- **No `carry_bonus: 10` legendaries.** The task listed `carry_bonus: 10` as a
  possible 5-ing legendary slot, conditioned on it being a valid power_id in
  `player.py`. `carry_bonus` is an **item** field (worn via inventory items like
  stuffies — see `player.py::refresh_carry_bonuses`), not a cooking-dispatched
  permanent power. No dispatcher exists in `_apply_permanent_power` for it, so
  this bucket was dropped and the slot was redistributed across the other
  legendary shapes.
- **Three 4-ing outcomes promoted to T5 tier (`t5_quartet_*`).** Because they
  carry `permanent_power: chromatic_resist_all`, which is a potent reward,
  bumping their tier to 5 (SP floor 140) honors the SP soft-boundary rule and
  signals the escalator-chain quiz difficulty appropriately. They remain
  4-ingredient recipes.

---

## Files touched

- `data/items/cook_outcomes.json` — **+116 outcome entries appended**; existing
  120 preserved. Line delta: before 1226 lines, after approximately
  1 KB + ~15 KB new content (one additional note appended to `_meta.description`).
- `docs/audits/cook_expansion_outcomes_2026-10-03.md` — this report (new).
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\gen_cook_outcomes.py` — scratch
  generator (not committed; the project's `_archive/sweep_*` pattern applies).

---

## Hand-off to Phase 2

The 116 new outcome ids are now live in `cook_outcomes.json`. Phase-2
floor-band authoring agents should pick `outcome_id` values from this set per
the per-tier/per-ingredient-count intent, cross-reference the ingredient
availability for their band, and emit `recipes_fXX.json` under
`$CLAUDE_JOB_DIR/tmp/`. The archetype ids are stable; no further edits to the
new entries are planned pre-ship.
