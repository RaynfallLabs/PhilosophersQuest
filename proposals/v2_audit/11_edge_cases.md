# V2 Audit — 11 Edge Cases / Crash Scenarios (2026-05-19)

Scope: walk 29 named scenarios spanning inventory, combat, equipment,
status effects, movement, quizzes, pets, death, spawn, and save/load.
For each, decide PASS / CRASH / INTENDED, apply minimal hardening for
real crashes or undefined behavior, and add regression tests.

**Result:** 596 tests pass after fixes (was 568 + 28 new in
`test_edge_cases.py`). Two real engine bugs hardened:

1. `Player._apply_equip` for `Accessory` silently applied stat effects
   even when all 4 ring slots were full (game-level guard prevents
   reaching this path, but a direct caller could lose data).
2. `Game._advance_turn` had no recovery if `phasing` expired while the
   player was standing on a wall tile (soft-lock — no walkable
   neighbors meant no movement possible).

---

## Scenario tally

| # | Scenario | Status | Notes |
|---|----------|--------|-------|
| 1 | Inventory full + plot item drops | **PASS** | `add_to_inventory` returns False; pickup keeps item on floor with `"You are carrying too much..."` (main.py:3068). |
| 2 | Pick up Soul Sphere with full inventory | **PASS** | Same path as #1; Soul Sphere is a regular `Artifact` instance under weight. |
| 3 | Drop plot item | **PASS** | `_do_drop_item` (main.py:4861) removes from inventory, places at player's tile, persists via `level_mgr.save`. |
| 4 | Throw Soul Sphere then re-pickup | **PASS** | Throw removes from inventory at `_throw_soul_sphere`; if it lands without spawning a pet (no walkable tile within 1), sphere is wasted with message. Picking up from ground re-adds normally. |
| 5 | Equip cursed item — does try_unequip block? | **PASS** | `try_unequip_slot` returns `(False, "...welded to you!")` if the slot item has `cursed==True`. All equip-swap paths gate on this. |
| 6 | No melee weapon + bump monster | **PASS** | `combat.player_attack` falls back to `roll('1d4')` at line 207; default chain multipliers `[0.5, 1.0, 1.5, ...]`; final damage `max(1, ...)` so unarmed always lands at least 1. |
| 7 | 2H weapon equipped + try to equip shield | **PASS** | `can_equip_shield()` returns False; `_equip_item` shows warning `"You cannot use a shield while wielding a two-handed weapon!"` (main.py:3737). |
| 8 | Shield equipped + try to equip 2H weapon | **PASS** | `_apply_equip` for 2H weapon force-unequips the shield (player.py:783-788) and pushes it back to inventory. |
| 9 | Ranged with 0 ammo | **PASS** | `_fire_ranged` finds no matching `ammo_type` item → `"Out of {ammo_type}s!"` warning and returns without entering quiz state (game_combat.py:1262). |
| 10 | Cast spell with 0 MP | **PASS** | `_invoke_spell` gates on `self.player.mp < mp_cost`; emits warning and returns to STATE_PLAYER (game_magic.py:1039). MP is consumed only on success path. |
| 11 | Stack 5+ statuses at once | **PASS** | `tick_all` iterates `list(player.status_effects.items())` — safe under mutation. Tested with 7 simultaneous effects. |
| 12 | Damage immunity + multiple damage types | **INTENDED** | `take_damage` takes a single `damage_type` string — caller chooses which type. Fire damage with `fire_resist` returns 0; the same call with `cold` returns normal damage. |
| 13 | Apply status already active | **INTENDED** | `apply_effect` stacks: `status_effects[effect] = min(current + duration, MAX_EFFECT_DURATION=60)`. Permanent (-1) effects refuse further changes. |
| 14 | Phasing expires while in wall | **FIX APPLIED** | Was a soft-lock: player couldn't move from wall once phasing expired. Added safety net in `_advance_turn` that bumps the player to the nearest walkable tile within a 5×5 window with the message `"You feel solid again — the wall pushes you back into open space."` |
| 15 | Trapped in pit + try descend | **PASS** | `_do_move` consumes the pit on movement (main.py:1469). `_descend_stairs` requires the tile under the player to be `STAIRS_DOWN`. Pits arise from traps (placed on FLOOR) or `_dig_pit` (player-initiated, requires a shovel); the only intersection would be a player-dug pit on stairs, which is harmless because the descend tile still passes the check. |
| 16 | Descend at HP<1 from poison | **PASS** | Poison ticks happen in `_advance_turn`; if HP hits 0, `is_dead` flips and state machine transitions to STATE_DEAD before the next input is read. Descending while alive but at 1 HP is by-design. |
| 17 | Maze level with no down stairs | **PASS** | `_generate_maze_dungeon` (dungeon.py:381-392) places STAIRS_UP at `rooms[0]` and STAIRS_DOWN at `rooms[-1]`. When room count < 2, falls back to first/last floor tile. Verified for levels 10/30/50/70/90. |
| 18 | Cancel quiz with ESC | **PASS** | ESC handler calls `quiz_engine._end(success=False)` (game_input.py:71). Engine settles in `QuizState.COMPLETE`; `eng.active` becomes False; callback fires with `score = self.chain` so chain mode returns the chain achieved so far. |
| 19 | Apply Tablet of Destinies reroll twice | **PASS** | `reroll_available` is consumed on first use (`quiz_engine.py:304`). Second wrong answer ends the quiz normally. `_quiz_reroll_used` flag at the game level also prevents the player from setting `_reroll_flag` twice in the same floor. |
| 20 | Pet on stairs when player descends | **PASS** | `_change_level` (main.py:842-867) repositions every alive pet to a free tile within a 5×5 spiral around the player. Fallback: pet shares player's tile. |
| 21 | Pet adjacent to mimic on chest open | **PASS** (report-only) | Pet AI targets nearest hostile; mimic is created post-spawn so the pet's next turn attacks it. Mimic surprise attack hits the player only (game_combat.py mimic logic). |
| 22 | Multiple pets supported | **PASS** | `self.pets` is a list. Multiple Soul Spheres can spawn multiple pets. Verified by structure. |
| 23 | Die on L100 with Stone — Death post-death? | **PASS** | Death pursuit is only triggered by `_ascend_stairs` from L100 with the Stone (main.py:1876-1883). Dying on L100 never sets `death_pursues=True`. |
| 24 | Die mid-quiz | **PASS** | Status effects don't tick during STATE_QUIZ — only on `_advance_turn` after the quiz completes. The quiz can't kill the player; the subsequent turn-advance can, and that path runs the normal STATE_DEAD transition. |
| 25 | Die in cow level | **INTENDED** | Cow level death is permanent like any other floor — no special return logic. The cow-return level is only used on portal exit. |
| 26 | Boss floor with no rooms eligible for boss | **PASS** | All 5 boss floors (L20/40/60/80/100) plus L999 cow level are hand-crafted in `boss_levels.py` with explicit room layouts. No procedural fallback needed. |
| 27 | Mini-boss spawn with no candidates | **PASS** | `_roll_planned_mini_bosses` returns an empty dict if no candidates exist for a band; `_try_spawn_mini_boss` early-returns when `mid is None`. |
| 28 | Save with quiz pending | **PASS** | The save trigger is the `STATE_CONFIRM_EXIT` Y key (game_input.py:438). ESC out of STATE_CONFIRM_EXIT returns to STATE_PLAYER. STATE_QUIZ can only be exited via ESC (which cancels) or answer completion. Therefore the saved `game.state` (only saved implicitly via the in-process objects, not as a field — `save_system.py` does NOT serialize `game.state`) is always STATE_PLAYER on load. |
| 29 | Save in NPC encounter | **INTENDED** | Same gating as #28: save only happens via STATE_CONFIRM_EXIT, and ESC out of an NPC encounter returns to STATE_PLAYER first. NPC encounter state (e.g., dialog turn) is not serialized — on load, the player is at the encounter's tile and the encounter re-triggers on next bump. |

---

## Fixes applied

### Fix 1: `Player._apply_equip` defensive ring slot guard
**File:** `src/player.py` (lines 846-859)

Before: if all 4 `accessory_slots` were occupied, the loop exited without
slotting the new item, but the `fx` effects (stat/status) were still
applied. The game-level `_equip_accessory` (`main.py:3881`) blocks this
case with a "All ring slots are full!" message, but the engine method
itself was non-defensive.

After: explicit `next()` lookup for the first None slot; bail out
silently if none found. Reduces blast radius of any future direct
caller (`mystery_system.py:531` is one such case where rings are
granted as quirk rewards).

### Fix 2: Phasing-expiry unstick
**File:** `src/main.py` (lines 2258-2276, inside `_advance_turn`)

Before: if `phasing` expired while the player stood on a non-walkable
tile (because they had walked into a wall while phased), they could
not move out because the movement gate requires `is_walkable(nx, ny)`
or active `phasing`. Soft-lock — only escape would be teleport or
death.

After: post-tick check. If phasing is OFF and the player's current
tile is non-walkable, scan a 5×5 window for a walkable neighbor and
nudge the player there with a flavored message. Floor tiles still
gate the check so the regular path is unaffected.

---

## Tests added (`tests/test_edge_cases.py`, 28 tests)

| Test | Scenario(s) covered |
|---|---|
| `test_scenario_01_inventory_full_blocks_pickup` | 1 |
| `test_scenario_02_full_inventory_soul_sphere` | 2 |
| `test_scenario_03_drop_plot_item_returns_to_floor` | 3 |
| `test_scenario_04_thrown_soul_sphere_can_be_repickedup` | 4 |
| `test_scenario_05_cursed_item_blocks_unequip` | 5 |
| `test_scenario_06_unarmed_combat_uses_default_damage` | 6 |
| `test_scenario_07_shield_blocked_by_two_handed_weapon` | 7 |
| `test_scenario_08_two_handed_unequips_existing_shield` | 8 |
| `test_scenario_09_ranged_with_no_ammo_short_circuit` | 9 |
| `test_scenario_10_zero_mp_blocks_cast` | 10 |
| `test_scenario_11_many_statuses_tick_cleanly` | 11 |
| `test_scenario_12_damage_immunity_correct_type` | 12 |
| `test_scenario_13_apply_status_already_active_extends` | 13 |
| `test_scenario_14_phasing_expiry_in_wall_softlock_logic` | 14 |
| `test_scenario_15_pit_movement_climbs_out` | 15 |
| `test_scenario_16_descend_at_zero_hp_path` | 16 |
| `test_scenario_17_maze_level_has_stairs` | 17 (mazes 10/30/50/70/90) |
| `test_scenario_18_quiz_esc_ends_cleanly` | 18 |
| `test_scenario_19_tablet_reroll_only_once_per_quiz` | 19 |
| `test_scenario_20_pet_follows_on_floor_transition` | 20 |
| `test_scenario_22_multiple_pets_allowed` | 22 |
| `test_scenario_23_death_pursuit_only_triggered_on_ascend` | 23 |
| `test_scenario_24_quiz_end_returns_to_player_state` | 24 |
| `test_scenario_26_boss_levels_always_generate` | 26 (all 5 boss floors + cow) |
| `test_scenario_27_mini_boss_pre_roll_handles_empty_pool` | 27 |
| `test_scenario_28_save_path_safe` | 28 |
| `test_scenario_29_load_missing_returns_none` | 29 |
| `test_apply_equip_ring_when_all_slots_full_does_not_double_apply` | regression for Fix 1 |

Scenarios 21 and 25 are report-only — pet-vs-mimic adjacency is
naturally handled by the existing pet AI on its next turn, and
cow-level death has no special path. No additional code change or
test needed.

---

## Test results

```
596 passed in 65.54s
```

568 baseline + 28 new = 596. No regressions.
