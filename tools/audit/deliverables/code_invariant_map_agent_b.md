# CODE Invariant Map — Agent B

Cross-module invariants the game relies on. Each is owned by one or more files; "status" is one of:
- **verified** — checked and holds
- **broken** — actively violated; see finding
- **suspect** — looked plausible but not fully traced

Findings are referenced by their `code-<slug>` id under `tools/audit/findings/code/agent_b/`.

---

## Quiz subsystem

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| Q1 | `on_answer` fires on every correct, wrong, AND timeout case | `quiz_engine.py` | **verified** | answer():193, update():217. Both call `self.on_answer(False)`. Consensus's prior P3 (timeout missing on_answer) is fixed. |
| Q2 | `on_complete` (per-quiz-session hook) fires at session end | `quiz_engine.py` | **broken** | `QuirkSystem.on_quiz_complete` defined but never invoked. See `code-quirk-on-quiz-complete-never-called`. Apollo (#23) and Cassandra (#12) unreachable. |
| Q3 | `start_quiz` always uses per-subject `base_seconds`; legacy `(10 + wisdom)` fallback unused | `quiz_engine.py:140-146` | **verified** | All 30+ call sites pass `base_seconds=player.get_quiz_timer(...)`. Legacy path dead. |
| Q4 | Timer expiry uses `<= 0.0` to avoid float-underflow hang | `quiz_engine.py:209` | **verified** | Fixed; was `== 0.0` per consensus. |
| Q5 | Threshold mode early-exits when math becomes impossible (not on first wrong) | `quiz_engine.py:307-310` | **verified** | Fixed since consensus baseline; uses `remaining < (required - correct_count)` check. |
| Q6 | Necronomicon custom quiz does NOT fire `on_answer` (intentional — different flow) | `game_magic.py:2121-2168` | **verified** | `_necro_answer` bypasses `quiz_engine.answer()`. Trade-off: Necronomicon Q&A doesn't count for `correct_answers` / quirks. |

## Death-chase state machine

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| D1 | `DeathMonster` is stored at game level (`game.death_monster`), NOT in `self.monsters` | `main.py:113`, `save_system.py:58` | **verified** | Confirmed in save/load schema and `_do_monster_turns` (`game_combat.py:1357-1371` treats Death separately from `self.monsters`). |
| D2 | `death_pursues` and `death_monster` round-trip through save/load | `save_system.py:57-58`, `main.py:339-340` | **verified** | Saved and restored. |
| D3 | Death's `_speed_pct` / `_frozen_turns` survive save/load via backwards-compat defaults | `monster.py:1051-1055` | **verified** | `take_turn` lazy-initializes if missing. |
| D4 | Death respawns near `dungeon.rooms[-1].center` on every level transition | `main.py:1266-1281` | **verified** | Always uses last room (down-stairs); fallback to center if no walkable. Works for boss/cow levels too. |
| D5 | Speed escalation is monotonic with ascent (L100→L1: 50%→75%→100%→125%) | `main.py:1283-1315` | **verified** | Threshold-based. Re-descending resets speed to slower tier — atmospheric, not exploit-relevant. |
| D6 | Prayer can freeze Death via `_frozen_turns` | `game_divine.py:792-797` | **verified** | Sets `freeze_turns = min(8, 3 + effective)` only when `death_pursues`. |
| D7 | Abyss trigger requires shimmer.activated AND complete_tablet on shimmer AND death on shimmer AND Lake-of-Fire-read | `game_magic.py:1942-1959` | **verified** | All four conditions checked; trigger destroys Death and drops the Bane scroll. |
| D8 | Failing Lake-of-Fire grammar quiz destroys the unique scroll | `game_magic.py:1544-1551` | **broken** | See `code-lake-of-fire-scroll-destroyed-on-fail`. P1 — secret victory becomes unreachable. |

## Permadeath / save round-trip

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| S1 | Save deleted IMMEDIATELY on load (no crash-reload exploit) | `main.py:4007` | **verified** | Consensus baseline's P2 is fixed: `delete_save(player_name)` after `load_game()` before any state restoration. |
| S2 | `_on_game_over()` always precedes save deletion | `main.py:1463-1472` | **verified** | save_bones → delete_save sequence; both idempotent. |
| S3 | `correct_answers`, `wrong_answers`, `missed_questions` round-trip through save/load | `save_system.py:36-38`, `main.py:314-316` | **verified** | Fixed since consensus baseline. |
| S4 | `_score_saved` does NOT need to round-trip (per-render flag for victory screen, naturally False after load) | `main.py:142`, `game_render.py:2526` | **verified** (intentional) | Score is written once at first victory-screen render. Load resets to False which is correct because a loaded save is by definition pre-victory. |
| S5 | All quirk progress (counters, set-types, dicts) round-trips via `quirk_system` pickling | `save_system.py:63`, `main.py:346-348` | **verified** | QuirkSystem.__setstate__ rebinds `game` to None; load_state restores. Player.quirk_progress is pickled with player. |
| S6 | Quiz deck state survives save/load (no question repeats on reload) | `save_system.py:74`, `main.py:359-361` | **verified** | `quiz_engine.get_deck_state` / `restore_deck_state`. |
| S7 | BUC migration patches old-format items on load | `main.py:368-395` | **verified** | `migrate_buc_all` walks inventory, equipment, ground, and stored levels. |
| S8 | `_lore_levels` / `_lore_placed` persist so deep-lore items spawn at most once per run | `save_system.py:60-61`, `main.py:341-344` | **verified** | Saved and restored. |

## Status-effect lifecycle

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| E1 | Every `add_effect` that grants a stat bonus is balanced by exactly one `remove_effect` (heroism, brilliance) | `food_system.py:446-465`, `status_effects.py:401-408` | **verified** | `already_active` guard in drink_potion; reverse in `to_expire` loop. Consensus's prior P4 was fixed. |
| E2 | Monster `tick_effects` is called exactly once per game turn for each alive monster | `main.py:1557-1562` (canonical), `monster.py:358` (DUPLICATE) | **broken** | Called TWICE per turn — once in `_advance_turn`, again at start of `Monster.take_turn`. Effect durations halved, DOT damage doubled. See `code-monster-tick-effects-double-call`. |
| E3 | `_EXPIRE_MSGS` covers every entry in `BUFFS ∪ DEBUFFS` | `status_effects.py:222-272` | **suspect** | Consensus flagged `hallucinating_pot` orphan — verified still missing from DEBUFFS by the user (line 96 includes it now). Possible regression — see consensus baseline P5. |
| E4 | Player `tick_effects()` signals `_teleport` and `_petrify_death` propagate correctly to game-level handlers | `main.py:1565-1576` | **verified** | Both handled. |
| E5 | Monster.tick_effects respects regen suppression while burning | `monster.py:163-167` | **verified** | Trolls/hydras stop regen when burning. |
| E6 | DOT damage on monsters consults damage-type resistances | `monster.py:155-160` | **broken (related)** | `tick_effects` calls `self.take_damage(N)` without damage_type — fire-resistant Fafnir takes full burn DOT. Same root cause as `code-spell-damage-bypasses-resistances`. |

## Inventory / equipment

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| I1 | `accessory_slots` (4 rings) and `amulet_slot` (1 amulet) are SEPARATE attributes | `player.py:58-59` | **verified** | Two attributes. |
| I2 | All "iterate equipped accessories" code paths cover both ring slots AND amulet slot | mixed | **broken** | Five call sites use non-existent `player.amulet` / `player.ring`. See `code-player-amulet-attribute-crash` (P1). |
| I3 | Cursed amulet uncurseable via prayer (effective≥2) | `game_divine.py:858-885` | **broken** | Amulet skipped. See `code-prayer-amulet-uncurse-skipped`. |
| I4 | Cursed amulet uncurseable via uncursed Scroll of Remove Curse | `game_magic.py:1685-1700` | **broken** | Amulet skipped. See `code-uncurse-scroll-skips-amulet`. |
| I5 | `_auto_identify_all` iterates equipment correctly | `game_magic.py:2354` | **broken** | Iterates dict keys instead of values. See `code-auto-identify-iterates-dict-keys`. |
| I6 | `get_equipped_items()` returns dict; callers must `.values()` or `.items()` | `player.py:392-401` | **verified** (except I5) | bones.py, ui.py, game_encounters.py all use correct iteration. |
| I7 | Stackable items merge by id+buc-known status; non-stackable items stay separate | `player.py:341-361` | **verified** | `_STACKABLE_CLASSES` whitelist. |

## Quirk counter graph

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| K1 | `hermes_teleports` incremented exactly once per teleport (regardless of source) | `quirk_system.py:1042-1050` | **verified** | Consensus's P3 double-count is fixed; `on_scroll_read` no longer increments. Single increment path via `on_teleport`. |
| K2 | Apollo and Cassandra unlock via `on_quiz_complete` hook | `quirk_system.py:442-461` | **broken** | Hook never called. See `code-quirk-on-quiz-complete-never-called`. |
| K3 | `on_kill` fires for every kill regardless of source (melee/ranged/wand/spell/AOE/Vidar) | `game_combat.py:1224,1333`, `game_magic.py:35+ sites` | **broken** | Only melee/ranged call `on_kill`. Wand/spell kills skip it. See `code-spell-wand-kills-skip-quirks`. |
| K4 | Penelope counter increments once per equip and once per unequip | `quirk_system.py:741-744, 767-771` | **verified** | Both equip and unequip increment by 1; total 100 events is intentional. |
| K5 | Hephaestus counter: unequip should check threshold but currently doesn't (only equip does) | `quirk_system.py:774-775` | **suspect** | Unequip increments without `is_unlocked` check; impacts only the exact 15th-equip-attempt timing. Minor. |
| K6 | Quirks that grant `add_effect(..., -1)` (permanent) don't expire | `quirk_system.py` various | **verified** | `status_effects.apply_effect` line 292-293: `if duration == -1: self.status_effects[effect] = -1` and tick_all checks `if val == 0: to_expire`. -1 never expires. |
| K7 | Quirks unlocked exactly once per run (no double-award) | `quirk_system.py:138-148` | **verified** | `if self.is_unlocked(qid): return` guard. |

## Spell / scroll / wand effects

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| M1 | All damage paths consult monster `resistances` / `weaknesses` / `dragon_scales` | `combat.py:_damage_multiplier`, `monster.py:take_damage` | **broken** | Only `player_attack` consults `_damage_multiplier`. Spell/wand/AOE paths bypass. See `code-spell-damage-bypasses-resistances`. |
| M2 | Read-scroll callback removes scroll from inventory exactly when it shouldn't be re-readable | `game_magic.py:1544-1558` | **broken** | Lake-of-Fire scroll destroyed on quiz fail. See `code-lake-of-fire-scroll-destroyed-on-fail`. |
| M3 | `_on_monster_killed` is the single point that increments `monsters_killed`, drops treasure, fires boss popup, tracks seals | `game_combat.py:579-611` | **verified** | All 30+ kill paths route through it. Consensus's prior P4 (melee skipping it) is fixed. |
| M4 | Spellbook learn quiz failure does NOT consume the book | `game_magic.py:2053-2066` | **verified** | `remove_from_inventory` only on success branch. |
| M5 | Scroll of Lake of Fire is re-added to inventory on success path | `game_magic.py:1939` | **verified** (success path only) | Failure path is broken (M2). |
| M6 | `Player.restore_hp` should return amount actually healed | `player.py:168-169` | **broken** | Void function; one caller (`drain_life_spell`) expects return value. See `code-drain-life-spell-prints-None`. |

## Mixin MRO

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| X1 | No method defined in two mixins | all `game_*.py` | **verified** | Grep of `def ` across 7 mixin files shows no duplicates. |
| X2 | Mixins access game state via `self.` consistently | all `game_*.py` | **verified** | All mixins use `self.player`, `self.dungeon`, `self.monsters`, etc. — bound at the `Game` subclass. |
| X3 | `game_helpers.py` pure utilities don't take `self` | `game_helpers.py` | **verified** | Module-level stateless functions; aliased onto Game as staticmethods. |

## Encyclopedia / journal

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| EN1 | Encyclopedia item entries include their `id` for the known-id filter | `main.py:3954-3968` | **broken** | `list(all_items.values())` discards the key. See `code-encyclopedia-item-id-lost`. Bestiary path is correct because monster entries iterate `.items()`. |
| EN2 | `_recalled_hints` round-trips through save/load | `save_system.py:71`, `main.py:356` | **verified** | Saved/loaded. |

## Dice / math

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| DC1 | All dice strings in JSON parse via `dice.roll` | `dice.py:5-26` | **verified** | Tested format `[count]d<sides>[+-mod]`. Spot-checked: `2d12+15` (DeathMonster), `2d6+4` (potion power), `4d8` (smite). All match regex. |
| DC2 | `dice.roll` rejects sides < 2 and count < 1 | `dice.py:21-24` | **verified** | Explicit guards. |

## Crash handling

| # | Invariant | Owner | Status | Evidence / Finding |
|---|-----------|-------|--------|--------------------|
| CR1 | Exceptions in `handle_event` / `update` reset state to STATE_PLAYER but DO NOT abort | `main.py:4022-4036` | **verified** (intentional but problematic) | Caught silently. Side effect: AttributeError in `_advance_turn` halts that turn's monster step (see I2). Free-action exploit. |
| CR2 | `crash_handler.write_crash_report` writes plain-text crash dump | `crash_handler.py` | **verified** | Only runs on unhandled exceptions in `main()`; the inner try/except prevents most crashes from reaching it. |
| CR3 | Crash report reads correct turn field | `crash_handler.py:73` | **suspect** | Consensus baseline noted `getattr(game, 'turn', '?')` but the field is `turn_count`. Verified at line 76: `getattr(game, 'turn_count', '?')` — looks fixed. |

---

## Summary

- **Verified invariants**: 35
- **Broken**: 13 (each with a finding id)
- **Suspect/intentional-but-questionable**: 5

The two most damaging clusters are:
1. The **`player.amulet` / `player.ring` typo** (I2) which silently halts every player turn's monster step due to the global exception-swallow at CR1. This is effectively a permadeath-breaking exploit even though it never crashes.
2. The **damage-type bypass in `Monster.take_damage`** (M1, E6) which breaks the entire resistance system for spells, wands, and DOT effects.

Together with the Lake-of-Fire scroll-destruction bug (D8/M2), these three findings dominate the CODE risk profile.
