---
id: code-auto-identify-iterates-dict-keys
dimension: code
severity: P2
title: Philosopher's Stone auto-identify silently crashes on equipped items (iterates dict keys, not values)
status: open
systems: [identification, philosophers_stone, equip_slots]
evidence:
  - src/game_magic.py:2354 — `for slot_item in self.player.get_equipped_items():` iterates dict KEYS (strings)
  - src/game_magic.py:2355-2357 — `if slot_item: slot_item.identified = True; ...` — AttributeError on string
  - src/player.py:392-401 — `get_equipped_items` returns a dict mapping slot-name strings to item objects
  - src/main.py:2162 — only caller: `_auto_identify_all()` fired when player picks up Philosopher's Stone
  - src/main.py:4030-4036 — main game loop wraps `game.update` in try/except, catches and recovers to STATE_PLAYER (silent)
verified: true
discovered: 2026-05-15

---

## What's wrong

`Game._auto_identify_all` (game_magic.py:2345) is invoked when the player picks up the Philosopher's Stone — the climactic L100 moment. It correctly identifies items in inventory and on the ground, but the third loop iterates the dict returned by `get_equipped_items()` as if it returned values:

```python
for slot_item in self.player.get_equipped_items():
    if slot_item:
        slot_item.identified = True
        self.player.known_item_ids.add(slot_item.id)
```

In Python, `for x in dict_obj:` yields KEYS. `get_equipped_items()` returns `{'weapon': <Item>, 'shield': <Item>, 'amulet': <Item>, ...}`. So `slot_item` is a string like `'weapon'`. The condition `if slot_item:` is truthy (non-empty string), then `slot_item.identified = True` raises `AttributeError: 'str' object has no attribute 'identified'`.

The main loop wraps `game.update` in a try/except at main.py:4030-4036 that catches the exception, prints a traceback to stderr, and recovers to STATE_PLAYER. So the game does not hard-crash. But:

1. Equipped items (weapon, armour, shield, accessories, amulet) are never identified — a silent feature failure on the most important auto-identify trigger.
2. The traceback is visible in the dev console but the player sees only "Error: 'str' object has no attribute 'identified'" via `add_message` at main.py:4033.

## How to reproduce / where it fires

1. Reach L100 (any way).
2. Defeat Abaddon. Find/pick up the Philosopher's Stone.
3. `_auto_identify_all` runs at main.py:2162.
4. Inventory loop succeeds. Ground loop succeeds.
5. Equipped loop: first iteration `slot_item = 'weapon'`, `slot_item.identified = True` raises AttributeError.
6. Game catches it in main.py:4032-4036, prints traceback, recovers. Player sees red-text error message and no further identifying of equipped gear.

## Suggested fix

```python
# Equipped items too
for slot_item in self.player.get_equipped_items().values():
    if slot_item:
        slot_item.identified = True
        self.player.known_item_ids.add(slot_item.id)
```

Add `.values()` at line 2354. Five-character change.

## Notes

This is a P2 (silent feature failure + visible error message at the most pivotal moment) rather than P1 (the try/except prevents a hard crash). The Philosopher's Stone is meant to "illuminate" all items — failing to identify the gear the player is wearing breaks the design intent badly.

The pattern `for slot_item in self.player.get_equipped_items():` may exist elsewhere — bones.py:29 uses `for slot, item in equipped.items():` (correct), so other call sites have got it right; this is an isolated typo.
