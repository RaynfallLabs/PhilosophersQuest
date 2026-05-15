---
id: code-iron-mortar-blast-message-backwards
dimension: code
severity: P3
title: Baba Yaga's Iron Mortar 'blast' effect message logic is reversed — fires only when no monsters present
status: open
systems: [wands, ui-messages]
evidence:
  - src/game_magic.py:876-879 — list comprehension followed by `or self.add_message(...)`
  - Python semantics: non-empty list is truthy; `[...] or message` short-circuits when the list is non-empty
verified: true
discovered: 2026-05-15
---

## What's wrong
The 'blast' branch of Baba Yaga's Iron Mortar chaos table uses this construct:

```python
('blast', lambda: [
    (m.take_damage(_rng.randint(5, 15)), self._on_monster_killed(m) if not m.alive else None)
    for m in list(self.monsters) if m.alive and (m.x, m.y) in self.visible
] or self.add_message("Chaotic energy blasts all visible enemies!", 'success')),
```

The expression is `[list_comprehension] or self.add_message(...)`. Python evaluates the list comprehension first. If at least one monster is alive and visible, the list contains tuples and is truthy — `or` returns the list and **the add_message call never executes**. The blast inflicts damage silently with no UI feedback.

Conversely, if NO monsters are visible, the list is `[]` (falsy), `or` evaluates the add_message — which prints "Chaotic energy blasts all visible enemies!" despite there being no enemies to blast.

The intent was clearly to print the message AFTER applying damage. The reversed semantics is a subtle Python idiom mistake.

## How to reproduce / where it fires
1. Find Baba Yaga's Iron Mortar wand.
2. Invoke it; if the chaos roll selects 'blast' (1-in-7), expect a blast message + damage.
3. With monsters visible: damage applied, NO message. The player sees nothing happen.
4. With no monsters visible: NO damage (list is empty), but message claims monsters were blasted.

Call graph: `_apply_wand_effect` → `iron_mortar` branch → `_chaos[1]()` invokes the lambda → list-comprehension-or-message expression.

## Suggested fix
Restructure the lambda to use a `def` or a tuple of statements so both run unconditionally:

```python
def _do_blast():
    for m in list(self.monsters):
        if m.alive and (m.x, m.y) in self.visible:
            m.take_damage(_rng.randint(5, 15))
            if not m.alive:
                self._on_monster_killed(m)
    self.add_message("Chaotic energy blasts all visible enemies!", 'success')

('blast', _do_blast),
```

Or refactor the chaos table to use proper method calls instead of one-line lambdas — the other entries (heal, teleport, haste, etc.) also use the comma-tuple-from-print-side-effect pattern which is bug-prone:

```python
('heal', lambda: (self.player.restore_hp(25),
                  self.add_message("Chaotic healing washes over you! (+25 HP)", 'success'))),
```

This is a tuple of `(None, None)` (both calls return None) — works but only because both side effects execute eagerly. Not a bug there, but the same pattern in blast trips up because the list comprehension result is non-None.

## Notes
P3 because the wand is rare and the 'blast' branch is only 1-in-7 of the chaos roll. But it's a clear functional bug — the user-facing experience is "wand silently does damage" or "wand pretends to do damage when there's nothing to hit."

The mass_sleep entry at line 871-873 has the same construct: `[m.add_effect('sleeping', 12) for m in self.monsters if ...]`, then `self.add_message(...)` — but this one is on a separate line in the tuple, evaluated independently. So mass_sleep works correctly. Only 'blast' is broken.
