---
id: code-lake-of-fire-scroll-bypass-weight
dimension: code
severity: P4
title: Lake-of-Fire scroll re-insertion bypasses weight check and inventory sort
status: open
systems: [scrolls, inventory, secret_victory]
evidence:
  - src/game_magic.py:1939 — `self.player.inventory.append(scroll)` — raw list append, no weight check, no sort
  - src/player.py:341-361 — `add_to_inventory` rejects items that exceed carry limit, then sorts inventory alphabetically
verified: true
discovered: 2026-05-15

---

## What's wrong

The Scroll of Lake of Fire is intentionally multi-use: when read, the `lake_of_fire` effect handler re-inserts it into the player's inventory at game_magic.py:1939:

```python
elif effect == 'lake_of_fire':
    self.add_message('"Then Death and Hades were thrown into the lake of fire."', 'info')
    # Keep the scroll in inventory -- it may need to be read again
    self.player.inventory.append(scroll)
    ...
```

This bypasses two invariants enforced everywhere else:

1. **Weight check.** `Player.add_to_inventory` (player.py:345) rejects items that would push the player above carry limit. The raw `inventory.append(scroll)` ignores this. A player at carrying capacity who reads the scroll ends up over-encumbered with no warning.

2. **Alphabetical sort.** `Player.add_to_inventory` resorts inventory by name (player.py:360) so the inventory list stays alphabetical. Raw `append` puts the scroll at the END of the list, breaking the invariant for one quirky letter slot.

Neither effect is catastrophic. The weight bypass is minor because the scroll is weight 0.2 (Scroll defaults) and most players won't be carrying-capped during the death chase. The sort break is purely cosmetic.

## How to reproduce / where it fires

1. Have a Scroll of Lake of Fire in inventory.
2. Load up to exact carry capacity.
3. Read the scroll. Effect fires, scroll is re-added.
4. Player is now over-carry. No message, no warning.

Inventory sort:
1. Save your inventory alphabetical (it is by default).
2. Read the scroll.
3. The Scroll of Lake of Fire is now the last entry in your inventory regardless of name.

## Suggested fix

Replace the raw append with the public API:

```python
elif effect == 'lake_of_fire':
    self.add_message('"Then Death and Hades were thrown into the lake of fire."', 'info')
    # Keep the scroll in inventory -- it may need to be read again
    if not self.player.add_to_inventory(scroll):
        # too heavy to keep -- drop at feet
        scroll.x, scroll.y = self.player.x, self.player.y
        self.ground_items.append(scroll)
        self.add_message("The scroll falls from your hand -- too heavy to keep!", 'warning')
    ...
```

## Notes

P4 nit. The scroll is meant to be reusable; the bypass exists because `_read_scroll` removes the scroll first (game_magic.py:1544). Using the public API would either accept it back or gracefully drop it.
