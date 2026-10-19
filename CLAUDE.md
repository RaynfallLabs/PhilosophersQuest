# Philosopher's Quest

## Core Concept
A graphical roguelike where knowledge is power. Every action requires answering quiz questions. Performance determines outcome — not random chance.

## Quiz Modes
- **threshold** — Must answer X correct to succeed (e.g., equipping armor, harvesting)
- **chain** — Build combo until wrong answer; score = chain length (e.g., combat attacks)
- **escalator_threshold** — Questions get harder each round; must hit a correct threshold
- **escalator_chain** — Questions get harder each round; chain until failure (e.g., praying)

## Subject → Action Mapping
| Subject     | Action                  |
|-------------|-------------------------|
| math        | Combat attacks (chain)  |
| geography   | Armor/shield equipping  |
| history     | Accessory equipping     |
| animal      | Harvesting corpses      |
| cooking     | Preparing food          |
| science     | Magic / wands           |
| philosophy  | Identification          |
| grammar     | Reading scrolls + spellbooks |
| economics   | Lockpicking             |
| theology    | Praying                 |

## Player Stats
- **STR** — Carry capacity
- **CON** — Max HP (3 per point) and toughness (1% less damage per point over 10, cap 40%)
- **DEX** — Armor class (up to 3 points) and dodge (0.75% per point over 10, cap 30%)
- **INT** — Max MP
- **WIS** — Quiz timer bonus (+1 second per point)
- **PER** — Sight radius

## Project Structure
Fuller per-system docs live in `docs/systems/` (start at `docs/systems/README.md`).
```
src/
  # Entry point and the Game class (main.py + its game_* mixins)
  main.py             - Entry point, game loop, Game class and state (large; split planned)
  game_states.py      - Game.state string constants
  game_input.py       - InputMixin: key handling outside menus
  game_menus.py       - MenuMixin: menu open logic and per-tab item lists
  game_render.py      - RenderMixin: render() and every _draw_* screen (help screen included)
  game_combat.py      - CombatMixin: attacks, monster turns, pet and escort swipes, kills
  game_magic.py       - MagicMixin: spells, wands, scrolls, spellbooks
  game_divine.py      - DivineMixin: prayer, intercession, Judgment
  game_encounters.py  - EncountersMixin: NPC, flavor and special-level encounters
  game_road.py        - RoadMixin: the Road, pending queue and oath lifecycle
  game_helpers.py     - Stateless helpers once static methods on Game
  layout.py           - Live window / viewport globals (and the version string)
  display_setup.py    - First window size and Windows DPI awareness

  # Hero, monsters, world
  player.py           - Player class: stats, inventory, equipment, quiz timers
  monster.py          - Monster class with AI patterns
  monster_classes.py  - Monster family tags (bestiary line, family-targeted gear)
  dungeon.py          - Procedural BSP dungeon generation
  level_manager.py    - Floor transitions
  boss_levels.py      - Hand-crafted boss floor layouts (and COW_LEVEL)
  floor_curve.py      - Median monster HP / damage by floor (balance anchors)
  geom.py             - Multi-tile footprint geometry
  fov.py              - Shadowcasting field of view
  unseen.py           - What the hero cannot see on a visible tile (invisible, ambush, disguise)
  false_stairs.py     - Hellmouth mimics that pose as the down stair
  splitting.py        - Creatures that split when struck the wrong way
  theft.py            - Thieves that really steal, and give it back on death
  black_knight.py     - The Black Knight bridge easter egg (floors 15-19)
  emberpup_encounter.py - The abandoned Emberpup random event (floors 3-8)
  setne_tomb.py       - Setne's Tomb and the Book of Thoth (floors 45-65)

  # Combat, items, magic
  combat.py           - Combat resolution
  dice.py             - Dice notation parser ("2d6+3")
  items.py            - Item classes and equipment system
  item_actions.py     - Item actions shared by the Kit (K) and the character sheet (@)
  chain_equip.py      - Chain-equip for lore-rich legendary uniques
  chain_passives.py   - Chain-equip passive flag lookups and wiring
  armor_procs.py      - Flat-armour proc registry and per-floor charges
  hero_specials.py    - One special ability per Secret Build
  spells.py           - Spellbook spell definitions (tiered families)
  prayers.py          - The prayer list and what each grants
  boons.py            - Gate-boss gifts (pick one of three)
  status_effects.py   - Buffs/debuffs (paralysis, poison, berserk, etc.)
  food_system.py      - Harvest and cooking mechanics
  container_system.py - Chests, sacks, lockable containers (lockpicking)
  economy.py          - The gold economy: what a floor earns and what things cost
  traders.py          - Named traders: who, where, their stock, prices, selling, services
  game_traders.py     - TradersMixin: placing traders and the Buy / Sell / Services screens
  treasure.py         - Coin weight (1 gp = 0.1 oz) and treasure: gems, jewellery, art; values, payment plans
  game_purse.py       - PurseMixin: receiving gold (weight-limited), paying with coin then treasure, gold piles
  pet_system.py       - Soul Sphere pets: AI, bonding, levels
  escort_system.py    - Escorts: people the hero walks somewhere

  # Quiz
  quiz_engine.py      - All quiz logic (threshold, chain, escalator modes)
  study_mode.py       - Standalone untimed Study Mode (title screen F3)

  # Story, deeds and karma
  deeds.py            - The deeds register: what the hero has done this run
  karma.py            - The single karma entry point (adjust)
  chronicle.py        - The hero's chronicle (Journal and Your Story entries)
  road.py             - The Road: where the run's encounters stand
  encounter_schema.py - Encounter loader normalisation and shared runtime rules
  npc_encounters.py   - NPC moral encounters (one anchor per 10-floor block)
  flavor_encounters.py - Story and flavor encounters
  mystery_system.py   - Mystery altars, key items, encounter logic
  quirk_system.py     - Per-character unlockable quirks
  quirk_text.py       - Player-facing quirk and power text

  # UI and presentation
  renderer.py         - Pygame tile rendering
  ui.py / fantasy_ui.py - Sidebar, message log, menus, fantasy-themed helpers
  ui_theme.py         - The UI art kit (painted panels and pieces)
  ui_scale.py         - The one UI scale factor
  text_layout.py      - Text fitting and containment helpers
  hud_context.py      - Pure HUD row builders
  lore_art.py         - The subject's art on lore pages
  welcome_screen.py   - Title screen and Secret Build definitions
  naming.py           - Display-name capitalisation (proper_name)
  effects_runtime.py  - Pluggable visual-effects controller (effects/ holds the handlers)
  sound_system.py     - Procedural sound effects

  # Persistence and plumbing
  save_system.py      - Per-name pickle saves
  bones.py            - Persistent ghost/bones across runs
  highscore_system.py - High score table
  game_log.py         - ERROR_LOG.txt logging (log_error)
  crash_handler.py    - Crash report writer
  paths.py            - Path resolution helpers (dev and frozen)
  dev_tools/          - Developer-only previews

data/
  questions/        - Quiz question JSON files organized by subject
  monsters.json     - Monster definitions
  items/            - Item JSON files by category (weapon/armor/shield/accessory/artifact)
  hints.json        - In-game hint pool
  (data/ holds only runtime JSON; the old generator/migration scripts were moved out)

assets/
  tiles/            - Tile graphics
  icon.ico          - Window icon
```

## Tech Stack
- Python 3.14 (Microsoft Store install on Windows)
- Pygame-ce — rendering, input, sound
- Tile-based graphics (64×64 sprite art, drawn on 40-pixel map tiles)
- JSON data files for questions, monsters, items

## Commands
- Run game: `python src/main.py`
- Run tests: `pytest tests/ -v` (parallel: `pytest tests/ -q -n auto`, about 1 minute; add `--run-slow` for the UI gates, about 6 minutes)
- Install dependencies: `pip install -r requirements.txt`

## Rebuilding a Quiz Bank
When the user says they want to build or rebuild a quiz bank for a subject — e.g. **"now we're going to do the theology bank"** — STOP and read **[`bankbuild/PIPELINE.md`](bankbuild/PIPELINE.md)** before doing anything else. It is the complete, authoritative, zero-to-shipped process: prerequisites (topic queue + subject config + the controlling voice rule), the batched build loop, the built-in prevention layers (deterministic gate + adversarial judge), the per-batch **de-tell sweep**, the pre-ship **moral-vision audit**, the **tone/kid-appropriateness audit**, the optional **deepen pass** for the tier curve, and merge → gate → promote → ship. Follow it exactly; do not improvise an ad-hoc process. The **history**, **philosophy**, **animal**, **cooking**, and **geography** banks are the reference implementations — see **PIPELINE.md §9–§12** for each build's additions (Grokipedia-first sourcing, the two-ladder-shape reframe, knowledge-subject de-tell, tone audit, the conditional deepen pass, the efficiency levers, and the multi-window wall-recovery). geography (§12) is the most recent and the closest template for another place/knowledge subject. **PIPELINE.md §13** is the subject roster — for any subject it names the KIND (knowledge / reasoning / snappy-rote), controlling voice, which de-tell rubric to fork, ladder-shape fit, and stance load; if Brandon is choosing what to build, §13 also carries the which-next recommendation (science is the current pick). Note: a subject's old `docs/quiz/subjects/<X>.md` may describe a design Brandon has since rejected (animal's did) — treat the config `voice_rule` + memory as authoritative, state your understanding back before building. **Before building any value-laden subject, read `docs/quiz/moral_vision.md` §3.10 (stance vs neutral — the no-verdict rule is NOT uniform) and bake the subject's stance into the config `framing` + topic `framing_note`s, not only the audit.** **Every topic ladder you build must ship with a TEACHING card in `data/question_contexts/<subject>.json`: WHO/WHAT/WHY orientation for a 10th-grader, then every rung's fact taught in story order, so a reader can answer the whole ladder (ruling reversed 2026-10-18; the old no-leak rule is retired). See `bankbuild/PIPELINE.md §16` and `bankbuild/cards/AUTHOR_SPEC.md`.**

## Development Rules
- **LORE, NOT FLOOR (Brandon, 2026-10-07; broken three times before it was written here).** Decide what a thing IS from its lore, then work out where in the progression that power belongs, and write it as real numbers in the base data. NEVER multiply damage or health by the dungeon floor at runtime, and never change an item's tier or base by depth. A weapon's maths tier is fixed (the material's for a common, its own for a unique). Hero weapons are unique artifacts and are meant to be unbalanced. If the early floors are too hard and the dice cannot go lower, change something else in `monsters.json` (to-hit, health, attack count). Depth schedules are baked into the data with `tools/balance/scale_monsters.py`. `tests/test_lore_not_floor.py` fails if game code multiplies by the floor or writes a weapon's tier.
- Keep code modular — one responsibility per file (main.py is a known exception, split planned)
- All questions and game data loaded from JSON files — no hardcoded content
- Commit after each working feature
- **Play-test rule**: when changing player-facing mechanics that are *easily reachable in a few minutes of play* (combat basics, equipping common gear, food prep, common UI), the user plays the game in person before the feature is "done". Claude can't drive Pygame from the harness, so unit tests and type checks do not prove the feature works — say so explicitly rather than claiming success.
- **When play-test isn't realistic**: for randomized loot, late-game content, deep-dungeon spawns, or probabilistic effects, play-testing is impractical. Write logic tests instead — at minimum a data-layer test (load the JSON and assert the mechanical fields are set correctly), and a pure-function test where the mechanic is implemented in a standalone module.
- **System-change sweep rule (added 2026-09-06)**: any time a game system is renamed, redesigned, or removed (masteries deleted, cook redesign, harvest v3→v4, lockpick v3, identify v3, etc.), do a **full-codebase grep for the OLD system's terms, symbols, field names, comment references, help text, message strings, and menu labels** — not just the direct call sites. Fix stale UI, tooltips, log messages, docstrings, and comments in the SAME commit as the mechanical change. Categories to check every time: (1) `src/game_render.py` (menus, panels, cards, lore screens), (2) `src/game_menus.py` + `src/fantasy_ui.py` (menu strings), (3) all `add_message(...)` / `_log_chronicle(...)` calls, (4) the help screen (`_draw_help_screen` in `src/game_render.py`) / help text, (5) docstrings + comments in `src/main.py` (which mixes many systems), (6) `src/mystery_system.py` challenge configs, (7) `src/quirk_system.py` descriptions, (8) any `data/*.json` schema fields. **Don't rely on tests to catch text-only regressions** — pytest won't notice a menu still says "5/5" when the system is now binary. When in doubt, ripgrep for the old term across ALL of `src/` and read every hit. Save-file compatibility with old written state is a separate concern (usually document as-is; only migrate on explicit user request).
