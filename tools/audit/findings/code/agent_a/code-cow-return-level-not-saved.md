---
id: code-cow-return-level-not-saved
dimension: code
severity: P3
title: `_cow_return_level` not persisted — save-and-load on Moo Moo Farm strands the player at L0
status: open
systems: [secret_level, save_load, level_transition]
evidence:
  - src/main.py:127 — `self._cow_return_level: int = 0` initialized to 0 in `__init__`
  - src/game_encounters.py:91 — `self._cow_return_level = self.dungeon_level` set when entering cow level
  - src/game_encounters.py:110 — `self._change_level(self._cow_return_level, enter_from_top=False)` to exit
  - src/save_system.py:22-78 — `_cow_return_level` is NOT in the save dict
  - src/main.py:276-365 — `_cow_return_level` is NOT restored in `load_state`
verified: true
discovered: 2026-05-15

---

## What's wrong

The secret cow level (Moo Moo Farm, `COW_LEVEL = 999`) is a special floor reached by poking the cow NPC too many times. Before transitioning to L999, `_enter_cow_level` saves the current floor in `self._cow_return_level` (game_encounters.py:91). Exiting the cow level reads that variable to return the player to the floor where the cow was.

The variable is initialized to **0** in `Game.__init__` (main.py:127) — never saved in `save_game`, never restored in `load_state`. If the player saves while ON the cow level and reloads, `_cow_return_level` resets to 0. When they walk to the exit portal, `_exit_cow_level` (game_encounters.py:104-110) calls `self._change_level(0, enter_from_top=False)`. Level 0 doesn't exist in the design space. `level_manager.generate(0)` is called:

- `level=0 % 10 == 0`, NOT in `_BOSS_LEVELS`, so it generates a maze dungeon.
- The maze function does not crash, but the player ends up on a phantom "L0" floor where:
  - All quirk progress that depends on `dungeon_level` queries (e.g., Sibyl, Diogenes, level-bonus loot) gets level=0 inputs.
  - L0's STAIRS_UP would let them ascend... but to L-1? That depends on the ascent code.

Looking at `_ascend_stairs` (main.py:1224): `if self.dungeon_level == 1: state=STATE_EXIT_QUEST`. Otherwise `_change_level(self.dungeon_level - 1, ...)`. So from L0, ascending goes to L-1. L-1 also generates a maze. The player is now in nonsense levels with all the bookkeeping that depends on positive `dungeon_level` operating on negative numbers.

## How to reproduce / where it fires

1. Find a cow on the dungeon-level designated as `_cow_level` (randint(30,39) at __init__).
2. Poke it 4+ times → enter Moo Moo Farm (game_encounters.py:83-97).
3. While on Moo Moo Farm, press ESC → Y (save & quit).
4. Restart the game, type the same player name, load.
5. `_cow_return_level` is 0 (default from __init__).
6. Walk to the exit portal. `_change_level(0, ...)` runs.
7. Game continues at "level 0" — playable but completely off-script.

## Suggested fix

Add `_cow_return_level` to the save dict and to `load_state`. Two-line fix:

```python
# save_system.py:save_game state dict
'_cow_return_level': getattr(game, '_cow_return_level', 0),

# main.py:load_state
self._cow_return_level = state.get('_cow_return_level', 0)
```

Also defensive: in `_exit_cow_level`, clamp the return target:

```python
target = self._cow_return_level if self._cow_return_level > 0 else 30
self._change_level(target, enter_from_top=False)
```

## Notes

P3 because the secret cow level is itself a deep secret — most players will never reach it, and even fewer will save while inside. But the failure mode (silent stranding at L0/L-1 with all the strange bookkeeping side-effects) is severe enough to flag.

Related field `_cow_npc` (line 128 init, never saved) is a Monster reference that becomes None on load. It's only used in `_enter_cow_level` to remove the cow from the source level's monster list — if the reference is lost, the cow stays in monsters and the player can re-encounter it. Smaller P4 sibling bug to this one.
