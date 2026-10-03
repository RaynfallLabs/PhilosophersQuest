# Philosopher's Quest — Systems Reference

**v2.18.0** (shipped 2026-10-02)

The authoritative map of how Philosopher's Quest is wired. If you're changing a
system — gameplay, data, or UI — start here, read the one-paragraph summary
of the relevant doc, then open that doc.

If you are new to the codebase: read **[conventions.md](conventions.md) first**.
It is short and dense. Everything else makes more sense once you know the
cross-cutting rules.

---

## Architecture overview

**Three layers.** Philosopher's Quest is a tile-based roguelike built on
Pygame-ce where **every action is quiz-gated**. The game loop lives in
`src/main.py` as a `Game` class assembled from seven mixins
(`InputMixin`, `MenuMixin`, `RenderMixin`, `MagicMixin`, `CombatMixin`,
`DivineMixin`, `EncountersMixin`). Input routes through
`game_input.handle_event` to a state-dispatch table keyed on `Game.state`
(the `STATE_*` strings in `src/game_states.py`). Each state has a drawing
method on `RenderMixin` and an input handler on `MenuMixin` or
`InputMixin`.

Below the loop sit three parallel sublayers:

1. **Quiz-gate layer** — `quiz_engine.py` runs every player action that
   consumes a resource or applies an effect. Four modes: `threshold`,
   `chain`, `escalator_threshold`, `escalator_chain`. The engine is
   **zero-tolerance**: one wrong answer in any threshold-mode quiz ends
   that quiz. Chain v2 (combat only) lets a wrong answer close the chain
   at the achieved rank — the strike still lands.
2. **Mechanical layer** — `combat.py`, `food_system.py`,
   `container_system.py`, `game_magic.py`, `game_divine.py`,
   `status_effects.py`, `save_bonus_for`. These run after the quiz
   succeeds and own the dice.
3. **Data layer** — `data/*.json` loaded through `paths.data_path`. No
   hardcoded content in `.py`. Items, monsters, questions, recipes,
   outcomes, chest traps, and hints all live in JSON. The schema
   conventions are documented in [data_schemas.md](data_schemas.md).

Rendering is tile-based (32×32 PNGs in `assets/tiles/`) composited by
`renderer.py` on a 1600×900 window (`layout.py`). All chrome goes through
`fantasy_ui.FP` (the single palette), `panel.PanelBuilder` (the single
modal frame), and `text_layout` (the single word-wrap / column-fit
helper). Overlay menus are drawn by `RenderMixin._draw_*` methods and
driven by `MenuMixin._*_input` + `MenuMixin._open_*` handlers.

Save/load is Pickle (per player name) via atomic temp-file replace;
dev/frozen path split through `paths.py`. Highscores and the crash
reporter are small, independent JSON/text siblings. See
[save_meta.md](save_meta.md).

---

## System docs

| Doc | What it covers | When to read |
|---|---|---|
| [conventions.md](conventions.md) | Zero-tolerance, chain v2, math-only timing, no-masteries, resource-loss-is-the-penalty, flow-over-gradient, save-bonus cap, karma clamp, SP floor, system-change-sweep rule | **Read first.** The orientation doc. |
| [quiz_engine.md](quiz_engine.md) | threshold / chain / escalator modes, zero-tolerance, per-run tier-clear auto-pass, timing | Any time you touch quiz flow |
| [combat.md](combat.md) | Chain v2 peak-chain formula, hit resolution, _damage_multiplier, DR bypass tiers | Any combat change |
| [weapons_and_materials.md](weapons_and_materials.md) | 96 weapons, 11 materials, 149 uniques, chain-passive hooks | Weapon tuning |
| [monsters.md](monsters.md) | 527 monsters, AI patterns, boss / mini-boss flags, families | Monster add/edit |
| [items.md](items.md) | Item classes, slots, equip, True Name model, BUC per-instance | Item schema change |
| [identify_v3.md](identify_v3.md) | One philosophy Q, derived id_tier, True Name, NO masteries (2026-08-06) | Identify flow change |
| [containers_lockpick.md](containers_lockpick.md) | Chest tiers, chest_traps.json, Lockpick v3 (1 Q, master pick, traps on fail) | Loot-gate change |
| [magic.md](magic.md) | Spells, wands, spellbooks, MP, MAGIC_TIER_MULT, dispatch | Spell add/edit |
| [food_system.md](food_system.md) | Cook v2 (1 Q binary), harvest v4 (1 Q binary), outcome_id, prime_cuts.json, SP soft-boundary | Food flow change |
| [status_effects.md](status_effects.md) | BUFFS / DEBUFFS / HARD_CONTROL, _RESIST_BLOCKS, SAVE_STAT, apply_debuff_with_save | Status effect add/edit |
| [save_bonus.md](save_bonus.md) | Gradient defense on CON/WIS/DEX/all, +5 cap, timed +3 cap | Save add/edit |
| [world.md](world.md) | Dungeon gen, mazes, terrain (water/ice/lava), bones, boss floors, cow level | Floor layout change |
| [pets.md](pets.md) | Species, specials, Duck transform, Soul Sphere, apply_late_pickup_bonus | Pet add/edit |
| [progression.md](progression.md) | Quirks, hero specials, elder blood, secret builds, karma judgments | Progression add/edit |
| [quests_mysteries.md](quests_mysteries.md) | 9 quest chains + 12 mysteries + 30 karma NPCs + 5 flavor NPCs | Quest add/edit |
| [karma_prayer.md](karma_prayer.md) | Karma −10..+10 clamp, 30-NPC inventory, prayer chain, divine intercession, judgment tiers | Karma / prayer change |
| [ui.md](ui.md) | Menus, HUD, help, bestiary, kit, discoveries, threshold copy helper | UI change |
| [save_meta.md](save_meta.md) | save_system (atomic pickle), highscore_system, crash_handler, paths.py, player.`__setstate__` migration | Save format change |
| [data_schemas.md](data_schemas.md) | JSON conventions, `_meta` sub-object (v2.18), spawn tables, unidentified_name discipline | Data file edit |

---

## Quick lookup

Each row names the doc to open and the function or JSON file inside it
that answers the question. If the quick lookup disagrees with a doc,
the doc wins (and the row is a bug — please update it).

| Question | Open |
|---|---|
| "How do I add a monster?" | [monsters.md](monsters.md), `data/monsters.json` |
| "How do I add a new quiz subject?" | [quiz_engine.md](quiz_engine.md), `data/questions/`, `fantasy_ui.FP.SUBJECT`, `player.SUBJECT_TIMER` |
| "What does chain-v2 do differently from v1?" | [combat.md](combat.md); peak-chain damage, miss = chain 0, wrong = strike-now |
| "How does a scroll get identified?" | [identify_v3.md](identify_v3.md); one philosophy Q at derived id_tier |
| "Where does damage math live?" | [combat.md](combat.md); `combat.player_attack`, `_damage_multiplier` |
| "What statuses exist and how do resists apply?" | [status_effects.md](status_effects.md); `EFFECT_INFO`, `_RESIST_BLOCKS`, `apply_debuff_with_save` |
| "How do I add a save bonus from an accessory?" | [save_bonus.md](save_bonus.md); `_gear_save_bonus` + `Player.save_bonus_for` |
| "How do pets gain levels?" | [pets.md](pets.md); `Pet.gain_xp`, `apply_late_pickup_bonus` |
| "What is Duck of Doom?" | [pets.md](pets.md); 2026-turn transform in `main._duck_of_doom_transform` |
| "How does cook v2 work?" | [food_system.md](food_system.md); 1 Q binary, outcome_id → `cook_outcomes.json` |
| "What is harvest v4?" | [food_system.md](food_system.md); 1 Q, `prime_cuts.json` keyed by `monster.kind` |
| "How does the lockpick trap fire?" | [containers_lockpick.md](containers_lockpick.md); `chest_traps.json` keyed by chest tier |
| "Where is the save file written?" | [save_meta.md](save_meta.md); `paths.save_dir()` dev vs frozen split |
| "Why isn't my old save loading?" | [save_meta.md](save_meta.md); `player.__setstate__` migration list |
| "What is the `_meta` block in JSON?" | [data_schemas.md](data_schemas.md); introduced v2.18 for `spawn_method` / `plot_locked` |
| "Why do spawn tables use peak_weight + spread?" | [data_schemas.md](data_schemas.md); Gaussian + explicit floor bands |
| "What is zero-tolerance?" | [conventions.md](conventions.md); any wrong answer ends a threshold quiz |
| "What subjects are timed?" | [conventions.md](conventions.md); math only (combat chain). Everything else untimed |
| "What is the system-change-sweep rule?" | [conventions.md](conventions.md); grep OLD terms across all `src/` in same commit as mechanical change |
| "Where does help text live?" | [ui.md](ui.md); `game_render._draw_help_screen`, including the new System Rules card |
| "How is the sidebar built?" | [ui.md](ui.md); `ui.Sidebar._identity/_vitals/_attributes/_derived/_effects/_powers/_in_sight` |
| "Why does the HUD say 'unidentified longsword'?" | [ui.md](ui.md); `hud_context.hud_item_name` True-Name rule (v2.18 identify-v3 fix) |
| "How do mystery altars gate challenges?" | [quests_mysteries.md](quests_mysteries.md); `MYSTERIES` dict in `mystery_system.py` |
| "Where is karma clamped?" | [karma_prayer.md](karma_prayer.md); `_award_encounter_outcome`, −10..+10 |
| "What does `plot_locked` do in item JSON?" | [data_schemas.md](data_schemas.md); documentary only — real gate is `min_level: 9999` + custom spawn code |
| "How does the welcome screen pick a build?" | [progression.md](progression.md); `welcome_screen.SECRET_BUILDS`, `_qa_tools` gated by `PQ_QA_MODE=1` or `--qa` |

---

## Audit history

The system docs are the forward-looking reference. The audits are the
snapshot of findings at a point in time — kept because they still name
every known bug and dead field.

- **[SYSTEMS_AUDIT.md](../../SYSTEMS_AUDIT.md)** — 2026-09-27 full
  systems audit (10 agents, ~330 findings, 8 P0, ~25 P1, ~40 P2, ~200
  P3–P5). Scope: every monster, item, quest, mechanic, UI element.
- **[ITEM_QUIZ_AUDIT.md](../../ITEM_QUIZ_AUDIT.md)** — 2026-09-24 item
  + quirk audit. 25 Dad-reward scrolls, 18 non-math timer quirks, 10
  container thresholds, ~166 ingredient/prime-cut `temp_desc` fields.
- **[ANSWER_CORRECTNESS_SUSPECTS.md](../../ANSWER_CORRECTNESS_SUSPECTS.md)** —
  2026-09-19 full-coverage answer-correctness audit.

Fixes from these audits ship in the version bump that mentions them in
`git log` (e.g. v2.18.0 "Full systems audit + fix wave").

---

## Where to find the code

- **Game loop + mixin assembly:** `src/main.py` (`class Game(InputMixin,
  MenuMixin, RenderMixin, MagicMixin, CombatMixin, DivineMixin,
  EncountersMixin)`).
- **State dispatch:** `src/game_input.handle_event` → per-state
  `_*_input` methods on `MenuMixin` / `InputMixin`.
- **Rendering:** `src/game_render.RenderMixin._draw_*` methods, one
  per `STATE_*`.
- **UI theme:** `src/fantasy_ui.FP` (palette), `src/panel.PanelBuilder`
  (modal frame), `src/text_layout` (wrap / truncate / column-fit).
- **Data:** `data/` (all read-only JSON), `assets/tiles/` (PNGs).
- **Entry point:** `python src/main.py` (not the bundled exe — "run it"
  means source, per the user's memory rule).

---

## Project rules worth repeating

- Every quiz-gated action **consumes the target** when it fires. The
  resource loss **IS** the penalty. Don't stack stuns on cook / harvest
  / lockpick fails — the lost corpse / ingredient / chest tier is the
  cost. (Identify's stun exists because identify is the one action that
  doesn't consume the item.)
- **No masteries.** All three mastery systems (class, family, identify)
  were removed on 2026-08-06. If you see "mastery" vocabulary in UI, log,
  or JSON — that's a stale string, fix it. See `player.__setstate__`
  in [save_meta.md](save_meta.md) for the migration list.
- When a game system is renamed, redesigned, or removed, **grep the OLD
  terms across all of `src/` in the same commit as the mechanical
  change.** Pytest won't catch text-only rot. See
  [conventions.md](conventions.md) "system-change-sweep rule" for the
  file list.
