---
id: code-drain-life-spell-prints-None
dimension: code
severity: P4
title: Drain Life spell message prints "heal None HP" — `Player.restore_hp` returns `None`
status: open
systems: [magic, ui]
evidence:
  - src/game_magic.py:1454 — `healed = self.player.restore_hp(actual)` expects a return value
  - src/game_magic.py:1456 — `f"... heal {healed} HP! ..."` — `healed` is None
  - src/player.py:168-169 — `restore_hp` is a void function, no `return`
verified: true
discovered: 2026-05-15
---

## What's wrong
`Player.restore_hp(amount)` is a void function (no `return` statement). It mutates `self.hp` in place and returns `None`.

The `drain_life_spell` callback assigns its return value to `healed`:
```python
healed = self.player.restore_hp(actual)
self.add_message(
    f"You drain {actual} life from the {target.name} and heal {healed} HP! (chain {chain})", 'success')
```

The message becomes literally: `"You drain 12 life from the orc and heal None HP! (chain 3)"`. The drain mechanically works (HP is restored), but the message displays "None" instead of the heal amount.

## How to reproduce / where it fires
1. Learn Drain Life spell (Tier 3 spellbook).
2. Cast it on any monster.
3. Spell quiz callback `_apply_spell_effect` → `drain_life_spell` branch → message displays "heal None HP".

## Suggested fix
Either:

**Option A** — Compute the heal amount before calling restore_hp:
```python
before = self.player.hp
self.player.restore_hp(actual)
healed = self.player.hp - before
```

**Option B** — Make `restore_hp` return the actual healed amount:
```python
def restore_hp(self, amount: int) -> int:
    old = self.hp
    self.hp = min(self.max_hp, self.hp + amount)
    return self.hp - old
```

Option B is canonical (matches the pattern in `take_damage` which returns actual damage applied).

## Notes
Cosmetic only — the spell works, only the message is broken. Found while auditing spell effect call sites for the resistance bypass bug (`code-spell-damage-bypasses-resistances`).
