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
| grammar     | Reading scrolls         |
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
  main.py           - Entry point
  game.py           - Main game loop and state management
  player.py         - Player class: stats, inventory, equipment
  monster.py        - Monster class with AI patterns
  dungeon.py        - Procedural dungeon generation
  combat.py         - Combat resolution
  quiz_engine.py    - All quiz logic (threshold, chain, escalator modes)
  fov.py            - Shadowcasting field of view
  renderer.py       - Pygame tile rendering
  ui.py             - Sidebar, message log, menus
  input_handler.py  - Keyboard input processing
  items.py          - Item classes and equipment system
  food_system.py    - Harvest and cooking mechanics
  dice.py           - Dice notation parser ("2d6+3")

data/
  questions/        - Quiz question JSON files organized by subject
  monsters.json     - Monster definitions
  items/            - Item JSON files by category

assets/
  tiles/            - Tile graphics (placeholder colored squares initially)
  fonts/            - Game fonts
```

## Tech Stack
- Python 3.13
- Pygame — rendering, input, sound
- Tile-based graphics (32×32 pixels)
- JSON data files for questions, monsters, items

## Commands
- Run game: `python src/main.py`
- Run tests: `pytest tests/ -v`
- Install dependencies: `pip install -r requirements.txt`

## Development Rules
- Keep code modular — one responsibility per file
- Match mechanics exactly from the JS prototype
- Use placeholder graphics (colored rectangles) initially; swap in real art later
- All questions and game data loaded from JSON files — no hardcoded content
- Commit after each working feature
