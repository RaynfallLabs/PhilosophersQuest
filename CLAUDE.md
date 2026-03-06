# Philosopher's Quest

## What This Is
A graphical roguelike RPG where the core mechanic is answering quiz questions. Players explore high-fantasy dungeons, fight monsters, collect loot, and interact with the world by answering knowledge-based questions. Correct answers succeed, wrong answers fail or have consequences.

Built with Pygame for rich 2D graphics, animations, and sound.

## Target Audience
Children ages 11-12 and growing. The game is designed to be played for years, with question content that scales from middle school through high school and beyond. Should be colorful, engaging, fun, and rewarding without being childish.

## Question System
- Questions stored in external JSON or YAML files, easily editable by a non-programmer
- Questions tagged by: category, difficulty level, age-appropriateness
- Difficulty levels: Elementary, Middle School, High School, Advanced
- Categories: Math, Science, History, Geography, Vocabulary, Literature, Logic, Philosophy
- Game pulls questions based on player's selected difficulty and action type
- Easy to add new questions or entire question packs over time
- Possible future: integration with educational APIs or AI-generated questions

## Project Structure
- `src/` - All game code
- `src/assets/` - Graphics, sprites, sounds, fonts
- `src/assets/sprites/` - Character and monster sprites
- `src/assets/tiles/` - Dungeon tiles (walls, floors, doors, etc.)
- `src/assets/ui/` - Interface elements (buttons, health bars, question boxes)
- `src/assets/sounds/` - Sound effects and music
- `data/questions/` - Question files (JSON/YAML), organized by category and difficulty
- `tests/` - All test files
- `requirements.txt` - Python dependencies

## Commands
- Run the game: `python src/main.py`
- Run tests: `pytest tests/ -v`
- Install dependencies: `pip install -r requirements.txt`

## Tech Stack
- Python 3.13
- Pygame for graphics, input, and sound
- Sprite-based 2D with tile maps
- Animated characters and monsters

## Development Rules
- Write clean, readable Python code
- Add tests for new features
- Commit after each working feature
- Use descriptive commit messages

## Visual Style
- High fantasy aesthetic (castles, dungeons, magical forests)
- Colorful and appealing but not babyish — think classic SNES RPGs
- Smooth animations for movement, attacks, effects
- Clear visual feedback for correct/incorrect answers
- Spell effects, particle systems for magic

## Game Design Notes
- Turn-based or real-time with pause (TBD)
- Quiz questions determine success of actions (combat, lockpicking, persuasion, magic, etc.)
- Question difficulty scales with action difficulty and player-selected difficulty level
- Rewards and progression system to keep players motivated
- Multiple character classes with different strengths
- Procedurally generated dungeons for replayability