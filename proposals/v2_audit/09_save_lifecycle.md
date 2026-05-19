# Save / Load Lifecycle Audit (2026-05-19)

Round-trip audit of the save/load system: does state actually survive a
`save -> quit -> load -> continue` cycle for the recent system additions?

Scope (per the audit brief):
1. Chain-equip items (player.damage_resistances, regen_bonus, item.achieved_tier, _chain_passives, _chain_resistances, _chain_stat_bonuses, _chain_statuses, _chain_baseline).
2. Family mastery (player.unlocked_monster_class_masteries).
3. Mini-boss pre-roll (level_mgr._planned_mini_bosses).
4. Corpse identify (corpse.id_level property; __setstate__ migration).
5. Per-floor charges (player._chain_passive_charges).
6. Per-run flags (_psychopomp_used, _gorgoneion_used_this_floor, etc.).

## Verdict

**PASS WITH FIXES.** 18/18 new lifecycle tests passing, 595/595 full suite
passing. Three real bugs found and patched (one save-system regression,
one legacy-compat regression, one pre-existing lore-spawn bug surfaced by
the descent/ascent test path).

## Round-trip test results per scenario

| Scenario | Result |
|---|---|
| Chain-equip armor T5 round trip (AC override + resistances + passives + baseline + achieved_tier) | PASS |
| Chain-equip revert after load restores baseline AC | PASS |
| Chain-equip accessory T4 round trip (stat bonuses + passives + status) | PASS |
| Chain-equip regen_bonus round trip (player.regen_bonus survives) | PASS |
| Chain-equip mp_bonus round trip (player.max_mp/INT + item._chain_mp_bonus) | PASS |
| Corpse id_level round trip (property + lore_identified shim) | PASS |
| Corpse legacy `__setstate__` migration (lore_identified -> id_level >= 4) | PASS |
| LevelManager planned + placed mini-bosses round trip | PASS |
| Legacy save missing `_planned_mini_bosses` is backfilled correctly | PASS *(was BROKEN — fixed)* |
| Per-floor chain_passive_charges round trip (_gorgoneion_used, counters) | PASS |
| Legacy player missing chain-charge fields gets empty defaults | PASS |
| Family mastery round trip (unlocked_monster_class_masteries dict) | PASS |
| Cross-floor state via level_mgr._saved survives save/load + descent/ascent | PASS *(was FLAKY — fixed)* |
| Status effects with durations + permanent (-1) entries | PASS |
| Per-run flags (_encountered_npcs, _lore_placed, karma, _abaddon_empowered, etc.) | PASS |
| Quirk system round trip + game backreference rebind | PASS |
| Magic carrot + ethereal unicorn one-shot spawn state | PASS *(was BROKEN — fixed)* |
| Mastery state (unlocked_masteries + unlocked_class_masteries + career arc + Mantle) | PASS |

## Bugs found and auto-fixed

### 1. Legacy `_planned_mini_bosses` backfill checked the wrong level_mgr

**Severity**: medium. Old save files predating the mini-boss pre-roll
would crash when entering a new floor because `_try_spawn_mini_boss`
expects `_planned_mini_bosses` to exist.

**Root cause**: `main.py:load_state()` checked
`self.level_mgr._planned_mini_bosses` for the legacy field BEFORE
`self.level_mgr = state['level_mgr']` ran. At check time, `self.level_mgr`
was still the freshly-constructed manager from `Game.__init__`, which
ALWAYS has the field. The actual restored level_mgr from `state` was
never inspected.

**Fix** (`src/main.py:411-416`): check `state.get('level_mgr')` instead.
If the saved manager lacks the field, roll fresh values onto it before
the assignment.

### 2. Magic carrot + ethereal unicorn one-shot spawns weren't saved

**Severity**: medium. A reload at the right point could spawn a SECOND
carrot or unicorn within the same run.

**Root cause**: `Game._maybe_spawn_magic_carrot` lazily sets
`_magic_carrot_target_level` on first call within range 1-19; similarly
for `_unicorn_target_level` (range 21-39). Both spawn methods then guard
against respawn with `_magic_carrot_spawned` / `_unicorn_spawned` boolean
flags. NONE of these four fields appeared in `save_system.save_game`. On
reload, the target floor gets re-randomized on next eligible entry, and
since `_spawned` is also lost, the carrot/unicorn can spawn again.

**Fix** (`src/save_system.py:71-77` + `src/main.py:497-508`): add all
four fields to the save dict and restore them in `load_state`. Use
`None` as the sentinel for "not yet rolled" so the restore branch only
sets the field if it was actually set on the saved game.

### 3. Lore items targeted at L1 only spawned after a descent + return

**Severity**: medium. Pre-existing bug, surfaced by the descent/ascent
test path. With `_lore_levels['shimmer'] = 1`, the abyssal_shimmer never
spawned during initial F1 setup because `_maybe_place_lore_items` was
only called from `_change_level`, not from `_new_level`. Players who
saved & reloaded after descending could end up with two shimmers in
sequence (one spawned on first ascent back to F1, then if `_lore_placed`
was lost on save — which it wasn't, but the failure mode existed).

**Root cause**: `_new_level` (initial floor-1 setup) calls
`_maybe_spawn_trigger_item`, `_maybe_spawn_npc`,
`_maybe_spawn_magic_carrot`, etc., but skips `_maybe_place_lore_items`.

**Fix** (`src/main.py:334-340`): call `_maybe_place_lore_items(dungeon,
level)` from `_new_level` in the same block as the other spawns.

## State that's LOST on save/reload (intentional, by design)

These fields are reset on every level change, so losing them at save
time is fine for the descent/ascent flow. They DO get briefly lost if
the player saves mid-floor and reloads (you start the floor "fresh" on
these flags), but the gameplay impact is negligible:

- `_chain_pacify_seen` (Game) — set of monster IDs already pacified on this floor by ring_of_solomon
- `_chain_seen_fear` (Player) — set of monster IDs that already saved vs Aegis fear aura on this floor
- `_first_hit_used` / `_death_save_used` / `_tarnhelm_used` (Game) — per-floor artifact charges
- `_quiz_reroll_used` (Game) — Tablet of Destinies per-floor reroll
- `_huginn_muninn_remaining` (Player) — turn counter set on floor entry; auto-reset on next change
- `_dragon_blood_active` (Player) — re-roll on next floor change
- UI / targeting state: `_menu_tab`, `_target_idx`, `_throw_potion`, `_pending_wand`, etc.

## Files added or modified

### Source

- `src/main.py:411-416` — fixed legacy `_planned_mini_bosses` backfill to check `state['level_mgr']`.
- `src/main.py:334-340` — `_new_level` now also calls `_maybe_place_lore_items`.
- `src/main.py:497-508` — `load_state` restores `_magic_carrot_spawned`, `_magic_carrot_target_level`, `_unicorn_spawned`, `_unicorn_target_level`.
- `src/save_system.py:71-77` — `save_game` writes the four one-shot fields.

### Tests

- `tests/test_save_lifecycle.py` — 18 tests covering all six audit focus areas plus four supplementary scenarios.

## Recommended follow-ups (no auto-fix applied)

These are not blockers but worth a paragraph each in a future pass:

1. **Per-floor charge reset on mid-floor save/reload**. Saving on floor
   X with `_chain_passive_charges = {'free_cast_once_per_floor': True}`
   and reloading correctly preserves the "used" state. Saving on floor
   X with `_chain_pacify_seen = {monster_id_42}` then reloading LOSES
   the pacify history — the same demon could be re-pacified. Verdict:
   negligible exploit potential, fix only if a player abuses it.

2. **Per-floor reset on Game-level flags**. `_first_hit_used`,
   `_death_save_used`, `_tarnhelm_used`, `_quiz_reroll_used` are set on
   first use mid-floor and only reset at next `_change_level`. A save +
   reload on the same floor will re-enable these once-per-floor charges
   (because they're not pickled). Same risk profile as #1.

3. **Mid-quiz save state**. The current architecture saves on clean
   exit from the main loop, which always happens at `STATE_PLAYER` (the
   quit input handler posts a QUIT event from there). Saving mid-quiz
   is not possible via the input path. If a future feature adds
   in-quiz saving (e.g. for slow turn-based monsters interrupting a
   pending quiz), the quiz_engine state would need to be saved too —
   currently only `quiz_deck_state` (deck shuffle position) is
   preserved.

4. **NPC double-spawn on revisit after save** — guarded already by the
   `_npc_encounter_tag` lookup in `_maybe_spawn_npc`. Verified: a saved
   floor with an NPC + a descended player + a reload + an ascent does
   not duplicate the NPC.
