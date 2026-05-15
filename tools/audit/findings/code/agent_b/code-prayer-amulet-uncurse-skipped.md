---
id: code-prayer-amulet-uncurse-skipped
dimension: code
severity: P3
title: Prayer "uncurse one item" branch iterates ring slots but skips `amulet_slot`
status: open
systems: [divine, accessories]
evidence:
  - src/game_divine.py:869 — `for acc in getattr(p, 'accessory_slots', [])`  (ring slots only)
  - src/game_divine.py:870-871 — appends cursed rings to `cursed_items`
  - src/player.py:58-59 — `accessory_slots = [None] * 4` (rings) and `amulet_slot = None` (separate)
  - src/main.py:2738-2740 — example of correct `amulet_slot` iteration elsewhere
verified: true
discovered: 2026-05-15
---

## What's wrong
The prayer "effective>=2" outcome at `game_divine.py:851-879` collects cursed equipment items and uncurses one (or all). It walks `armor_slots`, `shield`, `weapon`, `ranged_weapon`, and `accessory_slots` (ring slots), but **never inspects `amulet_slot`**. A cursed amulet (typically planted on the player via the Loki gambit, scrolls of curse, or a `cursed` Rand's Heart) is therefore invisible to this prayer outcome.

Because amulets in the base data set all have `"can_be_cursed": false`, the immediate impact is limited — but a cursed amulet can still arise via `_altar_buc_upgrade` (failed altar blessing) or Loki interactions, and the player has no other in-game uncurse path besides the scroll of remove curse. The player praying with a cursed amulet falsely receives the "no items to uncurse" fallback message and is given SP instead.

## How to reproduce / where it fires
1. Acquire a cursed amulet (Loki-curse or altar mishap).
2. Pray with chain length ≥2 that lacks an active poisoned/paralyzed/blinded debuff.
3. The code at `game_divine.py:858-871` constructs `cursed_items` without inspecting `amulet_slot`. The cursed amulet is never added.
4. If no other cursed items exist, the function falls through to the minor-effect branch and grants a tiny SP gain, leaving the amulet cursed.

Call graph: `_resolve_prayer` → effective>=2 branch → cursed_items collection → fallback SP gain.

## Suggested fix
Add the amulet check next to the ring-slot iteration at `game_divine.py:869`:

```python
am = getattr(p, 'amulet_slot', None)
if am and getattr(am, 'buc', 'uncursed') == 'cursed':
    cursed_items.append(am)
```

## Notes
Cross-references the broader `amulet_slot` discoverability hazard. Multiple call sites in `main.py` and `game_combat.py` use the non-existent `player.amulet` attribute instead of `amulet_slot` — see `code-player-amulet-attribute-crash`. The fix here uses the correct attribute name.
