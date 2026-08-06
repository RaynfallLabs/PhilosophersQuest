# Philosopher's Quest

## Core Concept
A graphical roguelike where knowledge is power. Every action requires answering quiz questions. Performance determines outcome — not random chance.

## Quiz Modes
- **threshold** — Must answer X correct to succeed (e.g., equipping armor, harvesting)
- **chain** — Build combo until wrong answer; score = chain length (e.g., combat attacks)
- **escalator_threshold** — Questions get harder each round; must hit a correct threshold
- **escalator_chain** — Questions get harder each round; chain until failure (e.g., cooking)

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
- **CON** — Max HP and SP
- **DEX** — Armor class bonus
- **INT** — Max MP
- **WIS** — Quiz timer bonus (+1 second per point)
- **PER** — Sight radius

## Project Structure
```
src/
  main.py             - Entry point, game loop, state management (large; split planned)
  player.py           - Player class: stats, inventory, equipment
  monster.py          - Monster class with AI patterns
  dungeon.py          - Procedural dungeon generation
  combat.py           - Combat resolution
  quiz_engine.py      - All quiz logic (threshold, chain, escalator modes)
  fov.py              - Shadowcasting field of view
  renderer.py         - Pygame tile rendering
  ui.py / fantasy_ui  - Sidebar, message log, menus, fantasy-themed screens
  items.py            - Item classes and equipment system
  food_system.py      - Harvest and cooking mechanics
  dice.py             - Dice notation parser ("2d6+3")
  boss_levels.py      - Hand-crafted boss floor layouts
  bones.py            - Persistent ghost/bones across runs
  container_system.py - Chests, sacks, lockable containers
  flavor_encounters.py, npc_encounters.py - Scripted encounters and NPC dialog
  mystery_system.py   - Random mystery / event system
  quirk_system.py     - Per-character unlockable quirks
  pet_system.py       - Pet AI and bonding
  status_effects.py   - Buffs/debuffs (paralysis, poison, berserk, etc.)
  level_manager.py    - Floor transitions
  save_system.py, highscore_system.py, sound_system.py, crash_handler.py
  paths.py            - Path resolution helpers

data/
  questions/        - Quiz question JSON files organized by subject
  monsters.json     - Monster definitions
  items/            - Item JSON files by category (weapon/armor/shield/accessory/artifact)
  hints.json        - In-game hint pool
  (data/ also contains many generator/migration scripts — offline tooling, not loaded at runtime)

assets/
  tiles/            - Tile graphics
  icon.ico          - Window icon
```

## Tech Stack
- Python 3.14 (Microsoft Store install on Windows)
- Pygame-ce — rendering, input, sound
- Tile-based graphics (32×32 pixels)
- JSON data files for questions, monsters, items

## Commands
- Run game: `python src/main.py`
- Run tests: `pytest tests/ -v`
- Install dependencies: `pip install -r requirements.txt`

## Rebuilding a Quiz Bank
When the user says they want to build or rebuild a quiz bank for a subject — e.g. **"now we're going to do the theology bank"** — STOP and read **[`bankbuild/PIPELINE.md`](bankbuild/PIPELINE.md)** before doing anything else. It is the complete, authoritative, zero-to-shipped process: prerequisites (topic queue + subject config + the controlling voice rule), the batched build loop, the built-in prevention layers (deterministic gate + adversarial judge), the per-batch **de-tell sweep**, the pre-ship **moral-vision audit**, the **tone/kid-appropriateness audit**, the optional **deepen pass** for the tier curve, and merge → gate → promote → ship. Follow it exactly; do not improvise an ad-hoc process. The **history**, **philosophy**, **animal**, **cooking**, and **geography** banks are the reference implementations — see **PIPELINE.md §9–§12** for each build's additions (Grokipedia-first sourcing, the two-ladder-shape reframe, knowledge-subject de-tell, tone audit, the conditional deepen pass, the efficiency levers, and the multi-window wall-recovery). geography (§12) is the most recent and the closest template for another place/knowledge subject. **PIPELINE.md §13** is the subject roster — for any subject it names the KIND (knowledge / reasoning / snappy-rote), controlling voice, which de-tell rubric to fork, ladder-shape fit, and stance load; if Brandon is choosing what to build, §13 also carries the which-next recommendation (science is the current pick). Note: a subject's old `docs/quiz/subjects/<X>.md` may describe a design Brandon has since rejected (animal's did) — treat the config `voice_rule` + memory as authoritative, state your understanding back before building. **Before building any value-laden subject, read `docs/quiz/moral_vision.md` §3.10 (stance vs neutral — the no-verdict rule is NOT uniform) and bake the subject's stance into the config `framing` + topic `framing_note`s, not only the audit.**

## Development Rules
- Keep code modular — one responsibility per file (main.py is a known exception, split planned)
- All questions and game data loaded from JSON files — no hardcoded content
- Commit after each working feature
- **Play-test rule**: when changing player-facing mechanics that are *easily reachable in a few minutes of play* (combat basics, equipping common gear, food prep, common UI), the user plays the game in person before the feature is "done". Claude can't drive Pygame from the harness, so unit tests and type checks do not prove the feature works — say so explicitly rather than claiming success.
- **When play-test isn't realistic**: for randomized loot, late-game content, deep-dungeon spawns, or probabilistic effects, play-testing is impractical. Write logic tests instead — at minimum a data-layer test (load the JSON and assert the mechanical fields are set correctly), and a pure-function test where the mechanic is implemented in a standalone module.
