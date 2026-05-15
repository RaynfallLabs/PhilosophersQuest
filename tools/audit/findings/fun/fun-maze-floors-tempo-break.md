---
id: fun-maze-floors-tempo-break
dimension: fun
severity: P3
title: Maze floors (10/20/30/50/70/90) constrict FOV during peak wander-spawn pressure
status: open
systems: [dungeon_gen, wander_spawn, fov, combat_tempo]
when_it_hits: "Every maze floor in a run — six dedicated maze floors per descent"
evidence:
  - src/main.py:422-435
  - src/main.py:1660-1692
  - src/player.py:276-289
  - fun_pacing_trace.md#checkpoint-c-floor-30
discovered: 2026-05-15
---

## The friction or flatness
The game flags certain procedural levels as mazes — the chronicle entries explicitly call them out: "Level 10. The tunnels twist into a maze.", "Level 30. A maze again.", L50, L70, L90 (`main.py:422-435`).

Mazes are 1-tile-wide corridors with frequent dead ends. FOV (`player.py:276-289`, default radius 5 at PER 10) is constricted to the corridor — you see 2-3 tiles ahead and 0 to the sides. Monsters appearing around corners are *invisible until they're adjacent*.

Concurrent with maze geometry, **wander spawn fires every `max(10, 22 - level//4)` turns** (`main.py:1664`). On L30 (interval 14), L50 (interval 10), L70 (interval 10), L90 (interval 10), wander spawns are constant. The wander spawn lands on an explored-but-not-visible tile 8+ tiles away (`main.py:1676-1682`). In maze geometry, "8 tiles away" almost certainly means "around a corner you can't see."

Combined effect: on maze floors the player is fighting an invisible spawn pipeline. The math chain combat starts when the monster arrives at the player's tile — there's no positioning, no kiting, no spell-cast-at-distance. The maze removes most of the tactical envelope the game otherwise supports (`game_magic.py` targeting cursors, ranged weapons, wand bolts, AoE spells).

This isn't *unfair* — the player has been told it's a maze, and the difficulty is intentional. But the *mechanical envelope* shrinks: combat becomes pure math chain on adjacent enemies, no positioning. The wonder of the dungeon (rooms with character, lines of sight, terrain, AoE moments) is shut off for the duration of the maze.

Compounded: identification, lockpicking, harvest, cook — all the *side activities* — become very risky on maze floors because there's nowhere safe to sit. The 65s economics quiz for a chest is suddenly a death sentence because a wander spawn will arrive in 8-14 turns and the player can't see them.

## When and how often it fires
- 6 maze floors per descent (L10, 20, 30, 50, 70, 90), so 6% of game floors.
- But these are highly-trafficked floors — the player must clear them to descend. Each one is 10-20 minutes of pinched gameplay.

## Suggested redirect
- **Suppress wander spawns on maze floors** or extend the interval significantly (2x or 3x). The maze is its own pressure system; doubling it with hidden-spawn-from-around-corners is excessive.
- **Or**: maze floors get a sight-radius bonus (+2 tiles) as the player's eyes adjust to the dark. Compensates the maze geometry without removing the spawn pressure.
- **Or**: maze floors guarantee an altar OR mystery altar nearby (within 5 floors) — give the player a recovery beat *near* the maze rather than after it.
- **Tactical alternative**: maze floors get ranged-monster spawns rotated *out* (only melee monsters spawn). The math-chain-on-adjacency loop is unchanged but feels more like a maze experience and less like a sniper alley.

## Notes
Mazes are CONTEXT-flagged as part of the design ("Level 30. A maze again. The walls feel like they're watching me.") — the chronicle leans into it. The finding isn't "remove mazes." It's that **maze floors stack three pressure systems** (constricted FOV + wander spawn + monster density scaling) **on top of the player's intentional disadvantage**, and the result is friction without compensating wonder. Spans dungeon_gen + wander_spawn + FOV + combat tempo.
