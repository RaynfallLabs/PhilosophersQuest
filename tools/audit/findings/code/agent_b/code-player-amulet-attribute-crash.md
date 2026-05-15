---
id: code-player-amulet-attribute-crash
dimension: code
severity: P1
title: AttributeError every turn — `self.player.amulet` and `self.player.ring` do not exist on Player
status: open
systems: [combat, turn-loop, accessories]
evidence:
  - src/main.py:1593 — `for _acc in (self.player.amulet, self.player.ring):` in `_advance_turn` (every turn)
  - src/main.py:1627 — Seal of Solomon pacify loop reads `self.player.amulet, self.player.ring`
  - src/main.py:1644 — Torc of Boudicca AC-bonus loop reads `self.player.amulet, self.player.ring`
  - src/main.py:2088 — Draupnir gold pickup reads `self.player.amulet, self.player.ring`
  - src/game_combat.py:1536 — Jade Cicada death-save reads `self.player.amulet, self.player.ring`
  - src/player.py:53-59 — Player defines `weapon`, `ranged_weapon`, `shield`, `armor_slots`, `accessory_slots` (4 rings) and `amulet_slot`. No `amulet` or `ring` attributes/properties exist.
verified: true
discovered: 2026-05-15
---

## What's wrong
Five separate code paths reference `self.player.amulet` and `self.player.ring` as if they were attributes on the `Player` object. They are not. `Player` defines `amulet_slot` (a single Item or None) and `accessory_slots` (a list of 4 ring slots). There is no `amulet` attribute, no `ring` attribute, and no `__getattr__` fallback on `Player` to coerce them.

The construct `for _acc in (self.player.amulet, self.player.ring):` evaluates the tuple eagerly — Python looks up `self.player.amulet` first, which raises `AttributeError: 'Player' object has no attribute 'amulet'`. Verified by direct execution:

```
>>> from player import Player; p = Player(); p.amulet
AttributeError: 'Player' object has no attribute 'amulet'
```

The most damaging instance is `main.py:1593` inside `_advance_turn()`, which runs every single turn the player takes. This means the game crashes on **every player turn**, not just edge cases. Either the crash handler silently absorbs the exception, or the game is currently unplayable as soon as any normal action is taken.

The intended logic was clearly to iterate through "amulet then a ring," matching the patterns for `passive_regen` (Eye of Horus), `pacify_chance` (Seal of Solomon), `surrounded_ac_bonus` (Torc of Boudicca), `gold_multiplier` (Draupnir), and `death_save` (Jade Cicada). All five artifacts are currently completely non-functional and the code path crashes the turn.

## How to reproduce / where it fires
1. Start the game and take any action that calls `_advance_turn` (move one tile, attack, anything).
2. `_advance_turn` reaches line 1593 → tries to construct `(self.player.amulet, self.player.ring)` → AttributeError.

Other paths that fire whenever invoked:
- Picking up a gold pile (`main.py:2088`)
- Player taking damage when at low HP (`game_combat.py:1536` — Jade Cicada check)
- Adjacent-monster pacification check (`main.py:1627-1632`)
- Surrounded AC bonus check (`main.py:1644-1652`)

Note: `game_combat.py:1546-1554` uses the **correct** pattern (`for _acc_slot in ('amulet', 'ring'): _acc = getattr(self.player, _acc_slot, None)`) — but `getattr(self.player, 'amulet', None)` returns None because the attribute doesn't exist. So Ankh of Isis resurrection also silently fails (downgrade-severity: that path doesn't crash, but the artifact never fires either).

## Suggested fix
Replace every occurrence of `(self.player.amulet, self.player.ring)` with iteration over the correct slots. Two patterns are needed:

```python
# Single-slot helper:
_amulet = self.player.amulet_slot
_rings  = [r for r in self.player.accessory_slots if r is not None]
for _acc in [_amulet, *_rings]:
    if _acc is None:
        continue
    ...
```

Or define properties on `Player`:
```python
@property
def amulet(self) -> 'Accessory | None':
    return self.amulet_slot

@property
def ring(self) -> 'Accessory | None':
    # Legacy: first ring slot
    return self.accessory_slots[0] if self.accessory_slots else None
```

The property approach restores the call sites without code changes, but only iterates ring slot 0. If the original intent was "check any equipped accessory," all five call sites should iterate the full slot set.

Also fix `game_combat.py:1546-1554` — change `getattr(self.player, 'amulet', None)` to `getattr(self.player, 'amulet_slot', None)`, and add ring iteration via `self.player.accessory_slots`.

## Notes
The exception is swallowed silently because `main()` wraps both `handle_event` and `update(dt)` in try/except blocks (`main.py:4022-4036`):

```python
try:
    game.update(dt)
except Exception as _upd_err:
    game.add_message(f"Error: {_upd_err}", 'danger')
    game.state = STATE_PLAYER
    import traceback
    traceback.print_exc()
```

When `_advance_turn` reaches line 1593, the AttributeError propagates up, is caught at line 4032, prints a stack trace to stderr, and resets state to STATE_PLAYER. The remainder of `_advance_turn` — including `_do_monster_turns()` at line 1654 — **never executes** that turn. Each player action prints "Error: 'Player' object has no attribute 'amulet'" in the message log and **skips the monster turn entirely**.

This is effectively a **free-action exploit**: the player can move, attack, drink potions, and cast spells without monsters ever responding. The game becomes trivial. This dramatically elevates the bug from "broken artifacts" to "the entire AI loop is dead the moment the player has any inventory action." This must be a recent regression — the consensus baseline doesn't note this and the project memory indicates the game is being actively played.
