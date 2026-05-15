# CODE Invariant Map — agent_a

Cross-module invariants the codebase relies on, with verified / broken / suspect status.

## Quiz engine

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| `quiz_engine.on_answer` fires for correct, wrong, AND timeout cases | quiz_engine.py | VERIFIED | line 192-193 (answer), line 217-218 (timeout). Consensus had previously flagged timeout-missing; line 217 now calls it. |
| Threshold mode allows continuation after wrong answers (don't fail on first wrong) | quiz_engine.py | VERIFIED (consensus claim is stale) | line 301-317 implements "end if threshold reached OR mathematically impossible OR ran out of questions", continues otherwise. Prior consensus P4 about line 259 is outdated. |
| Chain mode "success with score 0" path: callers know score=0 means no chain | quiz_engine.py | VERIFIED | Callers like `_resolve_recall_lore` (game_magic.py:114) check `chain == 0` explicitly. `_apply_spell_effect` checks chain>=1. Combat handles chain=0 with miss message. |
| Quiz timer never zeroes via float underflow | quiz_engine.py | VERIFIED | line 209 uses `<= 0.0` not `== 0.0`. Prior consensus P1 fixed. |
| Deck position survives quiz_engine sessions (anti-repeat shuffle) | quiz_engine.py | VERIFIED | `_decks`, `_deck_idx`, `_last_q` persisted via `get_deck_state` / `restore_deck_state`, saved at save_system.py:74. |
| `_pool` is never empty when `_next_question` runs | quiz_engine.py | **BROKEN** (defensive missing) | If `load_questions` returns `[]` (missing/corrupt JSON), `_pool` is empty and line 244 IndexErrors. See `code-quiz-engine-empty-pool-crash`. Currently dormant — all 12 data files exist. |

## Status effects

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Monster `tick_effects` runs exactly once per game turn | monster.py + main.py | **BROKEN** | Called once at main.py:1559 AND again inside `Monster.take_turn` at monster.py:358 → 2x DOT damage, 2x duration decrement, 2x troll regen. See `code-monster-tick-effects-double`. |
| Every `add_effect` that grants a stat bonus is paired with a `remove_effect` reverse | food_system.py + status_effects.py + game_menus.py | **BROKEN** | Heroism/brilliance powers in game_menus.py add the status without applying the stat bonus, but `tick_all` reverses it on expiry → permanent stat drain. See `code-quirk-power-heroism-stat-drain`. |
| `Player.tick_effects` runs exactly once per turn | main.py | VERIFIED | Only call site at main.py:1565 inside `_advance_turn`. |
| `hallucinating_pot` is in DEBUFFS, _EXPIRE_MSGS, and cure_all loops | status_effects.py | VERIFIED | line 96 (DEBUFFS), line 271 (_EXPIRE_MSGS), food_system.py:423 iterates DEBUFFS for cure_all. Prior consensus P5 fixed. |
| Damage routes through `Monster.take_damage` so sleeping/resistances are honoured | game_combat.py | **PARTIALLY BROKEN** | Fire shield / cold shield / Svalinn reflect all do `m.hp -= reflect_dmg` directly. See `code-fire-shield-bypasses-take-damage`. |

## Save/load round-trip

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Save is deleted immediately on load (no checkpoint exploit) | main.py | VERIFIED | line 4007 `delete_save(player_name)` runs right after `load_game()`. Consensus prior P2 fixed. |
| `_on_game_over` deletes save (permadeath) | main.py | VERIFIED | line 1471 calls `delete_save`. Six call sites all enter `_on_game_over` before setting STATE_DEAD. |
| `_save_on_quit` blocks save on dead/victory states | main.py | VERIFIED | line 4040 `if game.state not in (STATE_DEAD, STATE_VICTORY) and game._save_on_quit:` |
| All `Game.__init__` fields with persistent meaning are restored from save | main.py + save_system.py | **BROKEN (multiple gaps)** | `_score_saved` (consensus baseline) — confirmed still missing. `_cow_return_level` — see `code-cow-return-level-not-saved`. `_cow_npc` — lost but recoverable via tag. All `_chronicle_first_*` flags — see `code-chronicle-first-flags-not-saved`. |
| DeathMonster survives save/load round-trip | save_system.py | VERIFIED | Pickled in `death_monster` field, restored at main.py:340. All attrs survive (it's a Python object). `_speed_pct` and `_frozen_turns` round-trip. |
| `correct_answers` / `wrong_answers` persist | main.py | VERIFIED | line 36-37 (save), line 314-315 (load). Consensus prior P2 partially fixed; only `_score_saved` remains missing. |

## Permadeath enforcement

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Load → delete save → enter game loop (no checkpoint) | main.py | VERIFIED | lines 4005-4015. |
| Any game-ending event calls `_on_game_over` before transitioning to STATE_DEAD/STATE_VICTORY | game_combat.py + main.py + game_input.py | VERIFIED | All six call sites do `_on_game_over()` then set state. Multiple calls allowed (save_bones overwrites existing bones file harmlessly, delete_save is idempotent). |
| Bones file written before save deletion | bones.py + main.py | VERIFIED | `_on_game_over` calls `save_bones` (line 1468) BEFORE `delete_save` (line 1471). `save_bones` wraps file write in try/except so it never blocks `delete_save`. |

## Death-chase state machine

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| `death_pursues=True` ↔ `death_monster is not None` | main.py | VERIFIED | All 6 mutations co-set them. `_trigger_death_pursuit` sets both true; `_trigger_abyss` and `__init__` set both false/None. No mismatch path. |
| Death spawns at rooms[-1].center on every floor entry while pursuing | main.py | VERIFIED | `_change_level` line 540-542 calls `_maybe_escalate_death` and `_place_death_on_level`. |
| Death's speed escalates monotonically as player ascends from L100 to L1 | main.py | VERIFIED (with caveat) | `_maybe_escalate_death` line 1283-1300 escalates by current `dungeon_level`. Going back down would lower speed and fire a misleading speed-up message. Minor P4 (filed). |
| Prayer-freezing Death decrements per turn even while frozen | monster.py | VERIFIED | DeathMonster.take_turn line 1057-1059. Also survives save/load (pickled). |
| Reading scroll_lake_of_fire on activated Shimmer with Tablet + Death on tile triggers Abyss | game_magic.py | VERIFIED | line 1941-1959 logic-check is correct. But Complete Tablet is not consumed afterward — see `code-stone-on-shimmer-tablet-not-consumed`. |

## Secret-victory path

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Player holds Stone OR Complete Tablet → counts as victory at L1 exit | main.py | VERIFIED | `_do_exit` line 1450-1454 checks both ids. |
| Trigger Death pursuit only on first ascent from L100 with Stone | main.py | VERIFIED | `_ascend_stairs` line 1239 `if not self.death_pursues` guard prevents re-trigger via repeated ascent on the same chase. BUT post-Abyss re-descent and re-ascent re-spawns Death because `death_pursues` was reset to False by `_trigger_abyss`. See `code-stone-on-shimmer-tablet-not-consumed`. |
| Auto-identify on Stone pickup identifies inventory + ground + equipped | game_magic.py | **BROKEN** | `_auto_identify_all` iterates `get_equipped_items()` dict KEYS not values. See `code-auto-identify-iterates-dict-keys`. |

## Quirk counter graph

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Each quirk counter incremented in exactly one canonical place | quirk_system.py + many callers | **PARTIALLY BROKEN** | `hermes_teleports` previously double-counted (consensus); fixed at line 717 comment. `on_quiz_complete` (Apollo, Cassandra) and `on_disease_drain` (Paracelsus) are defined but NEVER called — see `code-quirks-on-quiz-complete-dead` and `code-quirks-on-disease-drain-dead`. |
| Identify-sight passive auto-identify notifies quirk system | main.py + game_magic.py | **BROKEN** | main.py:2113-2115 auto-identifies but doesn't call `on_item_identified`. See `code-identify-sight-pickup-no-quirk-notify`. |
| Loki `cursed` check works against new BUC system | items.py + quirk_system.py | VERIFIED | `Item.cursed` property at items.py:111-113 returns `self.buc == 'cursed'`. Loki at quirk_system.py:937 reads `getattr(slot_item, 'cursed', False)` — resolves via property. |

## Mixin / call-graph

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| No method defined in two mixins (MRO shadowing) | game_*.py | VERIFIED (spot-checked) | No duplicate method names found between InputMixin/MenuMixin/RenderMixin/MagicMixin/CombatMixin/DivineMixin/EncountersMixin. (Spot-checked, not exhaustive.) |
| `_on_monster_killed` is the single sink for all monster-kill bookkeeping | game_combat.py | VERIFIED | line 579-611. Increments `monsters_killed`, drops treasure, fires boss popup, tracks seal demons, drops corpse. All kill paths (melee, ranged, wand AOE, spell, shield reflect, piercing collateral, DOT, pet attack, sketch, sword-of-michael annihilate) route through this. Prior consensus P4 about melee/ranged not calling it was outdated — they do. |
| Sleeping/paralyzed player cannot act | main.py + game_input.py | **BROKEN** | Guards only in `_do_move`; menu actions bypass entirely. See `code-sleeping-paralyzed-bypass`. |

## State transitions

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Save can only happen from STATE_PLAYER | main.py + game_input.py | VERIFIED | `_confirm_exit_input` reached only from STATE_PLAYER (game_input.py:101). No other state opens the save-or-quit prompt. |
| Targeted spell cancellation refunds MP | game_input.py + game_magic.py | **BROKEN** (both directions) | No-candidates path adds MP from nothing (game_magic.py:1043); cancel-targeting (ESC) path loses MP. See `code-spell-mp-refund-from-nothing`. |
| State `_npc_encounter_active` is always cleared when state leaves STATE_NPC_ENCOUNTER | game_encounters.py | VERIFIED | line 913 nulls it in the resolved-or-not branch. |

## Items / inventory

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Adding to inventory goes through `Player.add_to_inventory` (weight check + sort) | player.py | **PARTIALLY BROKEN** | game_magic.py:1939 uses raw `inventory.append(scroll)` for the re-inserted Lake-of-Fire scroll. See `code-lake-of-fire-scroll-bypass-weight`. Other places use the public API correctly. |
| Equipped items are not in `player.inventory` | player.py | VERIFIED | `_apply_equip` removes from inventory at the caller; old equipped item gets re-added to inventory on swap. |
| Item identification via philosophy quiz notifies quirk system | game_magic.py | VERIFIED | line 1989 `_qs_id.on_item_identified(item.id)`. |
| Item identification via identify-sight (auto on pickup) notifies quirk system | main.py | **BROKEN** | main.py:2113-2115 — see `code-identify-sight-pickup-no-quirk-notify`. |

## Dice / data

| Invariant | Owner file | Status | Evidence |
|---|---|---|---|
| Dice strings parse correctly across all JSON formats | dice.py | VERIFIED (spot-checked) | The Lake-of-Fire scroll, DeathMonster's `2d12+15`, troll regen, and food restore_mp all use dice notation; all parse via `dice.roll`. The consensus P1 about `restore_mp` crashing on dice strings is **fixed** in food_system.py:647-666 with try/except wrapping. |
| Question files load gracefully on missing / corrupt JSON | quiz_engine.py | **PARTIALLY BROKEN** | `FileNotFoundError` handled; `json.JSONDecodeError` not. Empty pool crashes downstream. See `code-quiz-engine-empty-pool-crash`. |

## Summary status

- **Verified invariants**: ~20
- **Broken invariants (filed as findings)**: 11
- **Stale consensus claims (already fixed in source)**: 8 (timer ==0.0, on_item_identified zero-arg, restore_mp dice crash, eat-menu max recipes — assumed fixed via try/except shape; load-then-not-delete; melee on_complete missing _on_monster_killed; ranged same; threshold quiz exit-on-first-wrong; Sisyphus 'physical' mode; mimir's well stat_cost; hallucinating_pot orphaned; restore_str _base_STR — see notes in findings)

The strongest single-system bugs uncovered by this pass:
1. P1 — Monster tick_effects double-fire (combat balance shifted ~2x for DOT/durations)
2. P1 — Quirk powers heroism/brilliance permanently drain stats on expiry
3. P2 — Auto-identify dict-keys typo silently fails on equipped items at Stone pickup
4. P2 — Sleeping/paralyzed only blocks movement; all menus and meditation still work
5. P2 — Targeted-spell with no visible target adds free MP
6. P2 — `on_quiz_complete` hook never called (Apollo, Cassandra dead)
