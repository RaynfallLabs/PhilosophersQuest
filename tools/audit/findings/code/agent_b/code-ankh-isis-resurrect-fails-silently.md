---
id: code-ankh-isis-resurrect-fails-silently
dimension: code
severity: P2
title: Ankh of Isis resurrection silently never fires — `getattr(player, 'amulet', None)` returns None
status: open
systems: [accessories, combat, death-handling]
evidence:
  - src/game_combat.py:1546-1554 — uses `getattr(self.player, _acc_slot, None)` for slots `('amulet', 'ring')`
  - src/player.py:58-59 — Player has `amulet_slot` and `accessory_slots`, NOT `amulet` or `ring`
  - data/items/accessory.json:5244 — Ankh of Isis has `resurrect_on_death: true`
  - src/items.py:208 — `resurrect_on_death` is a recognised Accessory attribute
verified: true
discovered: 2026-05-15
---

## What's wrong
The Ankh of Isis is a min_level=65 amulet with the unique mechanic "resurrect on death" — it should shatter and revive the player at half max HP when a killing blow lands. The mechanic is checked in the melee-attack-damage loop at `game_combat.py:1544-1554`:

```python
if self.player.hp <= 0:
    for _acc_slot in ('amulet', 'ring'):
        _acc = getattr(self.player, _acc_slot, None)
        if _acc and getattr(_acc, 'resurrect_on_death', False):
            self.player.hp = max(1, self.player.max_hp // 2)
            setattr(self.player, _acc_slot, None)
            self.add_message("The Ankh of Isis shatters! Isis breathes life back into you!", 'success')
            self._log_chronicle("I died. Then light. Isis pulled me back. The ankh is dust now.")
            _snd.play('player_healed')
            break
```

The names `'amulet'` and `'ring'` are not attributes on Player. `getattr(self.player, 'amulet', None)` returns `None`. The loop iterates twice, both `_acc` are None, the `if _acc and ...` body never executes. The Ankh of Isis is permanently inert — a player who picks one up, equips it, and dies at 1 HP simply dies. The resurrection never happens.

The bug is silent because of the defensive `getattr(..., None)`. Unlike the parallel cluster `code-player-amulet-attribute-crash` (which crashes), this site silently fails — meaning even the global try/except doesn't help diagnose it. The amulet's design intent (rare resurrection backup for late-game) is wholly defeated.

This is also the case for any future accessory with `resurrect_on_death: true` placed in a ring slot.

## How to reproduce / where it fires
1. Equip Ankh of Isis (amulet, found at L65+).
2. Take damage from any source to drop HP to 0.
3. Expected: Ankh shatters, HP restored to max_hp//2, chronicle entry.
4. Actual: player dies, save deleted, run ends.

Call graph: `_do_monster_turns` → monster attack callback → `player.take_damage` → game_combat.py:1535 → `for _acc_slot in ('amulet', 'ring')` → `getattr` returns None → loop ends → fall through to `Life Save` check → if no `life_save` effect, player dies.

## Suggested fix
Fix the attribute names:

```python
if self.player.hp <= 0:
    for _acc_slot, _acc in [
        ('amulet_slot', self.player.amulet_slot),
        *[(f'accessory_slots[{i}]', r) for i, r in enumerate(self.player.accessory_slots)],
    ]:
        if _acc and getattr(_acc, 'resurrect_on_death', False):
            self.player.hp = max(1, self.player.max_hp // 2)
            if _acc_slot == 'amulet_slot':
                self.player.amulet_slot = None
            else:
                # accessory_slots index
                i = int(_acc_slot.split('[')[1].rstrip(']'))
                self.player.accessory_slots[i] = None
            self.add_message("The Ankh of Isis shatters! Isis breathes life back into you!", 'success')
            self._log_chronicle("I died. Then light. Isis pulled me back. The ankh is dust now.")
            _snd.play('player_healed')
            break
```

Or simpler:

```python
if self.player.hp <= 0:
    _check = []
    if self.player.amulet_slot and getattr(self.player.amulet_slot, 'resurrect_on_death', False):
        _check.append(('amulet_slot', self.player.amulet_slot))
    for i, r in enumerate(self.player.accessory_slots):
        if r and getattr(r, 'resurrect_on_death', False):
            _check.append((i, r))
    if _check:
        slot_key, acc = _check[0]
        self.player.hp = max(1, self.player.max_hp // 2)
        if slot_key == 'amulet_slot':
            self.player.amulet_slot = None
        else:
            self.player.accessory_slots[slot_key] = None
        self.add_message("The Ankh of Isis shatters! Isis breathes life back into you!", 'success')
        ...
```

## Notes
This is the silent-failure counterpart to `code-player-amulet-attribute-crash`. Both bugs share the same root cause (wrong attribute names) but manifest differently because of the `getattr(..., default)` guard here.

Other accessories with similar single-trigger consumption mechanics — Jade Cicada (`death_save`, same code site lines 1535-1542) — also fail silently for the same reason.
