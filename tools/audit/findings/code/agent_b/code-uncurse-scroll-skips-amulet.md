---
id: code-uncurse-scroll-skips-amulet
dimension: code
severity: P3
title: Uncursed Scroll of Remove Curse iterates ring slots but skips `amulet_slot`
status: open
systems: [magic, accessories]
evidence:
  - src/game_magic.py:1685-1695 — uncursed-branch builds `all_items` from weapon, ranged_weapon, armor_slots, shield, accessory_slots — but does not append `amulet_slot`
  - src/game_magic.py:1681-1684 — blessed branch correctly appends `amulet_slot`
  - src/player.py:59 — `amulet_slot = None` (separate from `accessory_slots` ring list)
verified: true
discovered: 2026-05-15
---

## What's wrong
`_apply_scroll_effect()` handles the `remove_curse` effect with three BUC branches:
- **Cursed scroll** (line 1664): no-op fizzle.
- **Blessed scroll** (line 1671-1684): builds the cursed-item candidate list from full inventory + every equipment slot, correctly including `amulet_slot` at line 1682-1684.
- **Uncursed scroll** (line 1685-1695): builds the candidate list from weapon, ranged_weapon, armor_slots, shield, and `accessory_slots` (ring slots) — but **never appends `amulet_slot`**.

A cursed amulet is therefore unaffected by a regular (uncursed) Scroll of Remove Curse. The player must find a *blessed* scroll for amulet uncursing.

## How to reproduce / where it fires
1. Equip an amulet, get it cursed (Loki gambit, altar mishap, or pre-cursed amulet entry).
2. Read an uncursed Scroll of Remove Curse.
3. Loop at `game_magic.py:1696-1700` iterates `all_items` looking for `buc == 'cursed'`. The cursed amulet is not in `all_items`. It stays cursed.

Call graph: `_read_scroll` → on_complete → `_apply_scroll_effect` → `remove_curse` branch → uncursed sub-branch → `all_items` missing the amulet.

## Suggested fix
Add the `amulet_slot` check to the uncursed branch, mirroring the blessed branch:

```python
# Uncursed: equipped items only
all_items = []
if self.player.weapon:
    all_items.append(self.player.weapon)
if self.player.ranged_weapon:
    all_items.append(self.player.ranged_weapon)
all_items.extend(s for s in self.player.armor_slots if s)
if self.player.shield:
    all_items.append(self.player.shield)
all_items.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
amulet = getattr(self.player, 'amulet_slot', None)
if amulet:
    all_items.append(amulet)
```

## Notes
Parallels `code-prayer-amulet-uncurse-skipped` — both code paths intend to operate on "equipped items" but forget `amulet_slot` is a separate attribute from `accessory_slots`. The blessed branch's correct handling shows the developer knew about `amulet_slot`; this is an oversight in the uncursed branch only.
