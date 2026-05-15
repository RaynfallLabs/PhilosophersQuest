---
id: code-auto-identify-iterates-dict-keys
dimension: code
severity: P2
title: `_auto_identify_all` iterates `get_equipped_items()` dict as values, gets keys, raises AttributeError
status: open
systems: [identification, philosophers-stone, mixin-magic]
evidence:
  - src/game_magic.py:2354 — `for slot_item in self.player.get_equipped_items():` iterates the DICT, yielding string keys
  - src/game_magic.py:2356 — `slot_item.identified = True` raises AttributeError because `slot_item` is a string like 'weapon' or 'amulet'
  - src/player.py:392-401 — `get_equipped_items()` returns a `dict[str, Item|None]`
  - src/main.py:2162 — call site: triggered on Philosopher's Stone pickup (post-Abaddon, peak narrative moment)
verified: true
discovered: 2026-05-15
---

## What's wrong
`_auto_identify_all()` is the "Philosopher's Stone reveals all" effect — called once per run when the player picks up the Stone after defeating Abaddon. It identifies every item in inventory, on the ground, and in equipment slots.

The inventory and ground-items loops are correct (lines 2347-2352). The equipment loop at line 2354 is wrong:

```python
for slot_item in self.player.get_equipped_items():   # iterates dict → yields keys
    if slot_item:                                     # truthy: non-empty string
        slot_item.identified = True                   # AttributeError: 'str' has no attribute 'identified'
        self.player.known_item_ids.add(slot_item.id)  # AttributeError too
```

`Player.get_equipped_items()` returns a dict like `{'weapon': <Weapon>, 'shield': None, 'amulet': <Accessory>, 'ring_1': None, ...}`. Iterating it yields the string keys, not the items.

The exception is caught by the global `try/except` at `main.py:4032`, which prints a stack trace and resets state to STATE_PLAYER. The pickup chain (`_pickup_item` → message → `_auto_identify_all`) is broken at line 2356. As a side effect, the **player's equipped items remain unidentified** even after picking up the Stone (the inventory and ground items are identified before the loop crashes, but equipment never is).

For a player who picks up the Stone with cursed-but-unidentified gear in their slots (e.g., a Loki-cursed weapon), the Stone's "reveal all" promise is broken: the cursed gear is the most important thing to identify at this point, and it stays unknown.

The message log shows two messages on Stone pickup:
- `"The Stone's radiance illuminates your mind — all items are revealed!"` (line 2164 — fires before the crash)
- `"Error: 'str' object has no attribute 'identified'"` (from line 4032 — caught exception)

## How to reproduce / where it fires
1. Defeat Abaddon on L100 and pick up the Philosopher's Stone.
2. Pickup flow `main.py:2156-2162`:
   - Print "The Philosopher's Stone! Return to the surface to win!"
   - `player.add_effect('identify_sight', -1)` (succeeds)
   - `_auto_identify_all()` — works for inventory + ground, then crashes on the equipment loop.
3. Equipped items still show as unidentified (`???` names) in the inventory screen.

Call graph: `_pickup_item` → Stone handling block → `_auto_identify_all` → equipment loop → AttributeError on first iteration that has a non-empty equipment slot.

## Suggested fix
Change line 2354 to iterate values:

```python
for slot_item in self.player.get_equipped_items().values():
    if slot_item:
        slot_item.identified = True
        self.player.known_item_ids.add(slot_item.id)
```

Or use the explicit slot collections:

```python
slots = [self.player.weapon, self.player.ranged_weapon, self.player.shield,
         self.player.amulet_slot]
slots.extend(self.player.armor_slots)
slots.extend(self.player.accessory_slots)
for slot_item in slots:
    if slot_item:
        slot_item.identified = True
        self.player.known_item_ids.add(slot_item.id)
```

The explicit-slot version is more robust against future changes to `get_equipped_items()`.

## Notes
This is plausibly never noticed by players because of the silent-catch in `main.py:4032` — the error message scrolls by and the Stone's narrative beat ("The Stone's radiance illuminates your mind") fires first. The bug only matters when the player has cursed-but-unidentified equipment at L100, which is rare.

The bug is real however and breaks the Stone's documented effect. It also fragments the "every action triggers the silent error message" experience for the user.
