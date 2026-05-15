---
id: code-spell-mp-refund-from-nothing
dimension: code
severity: P2
title: Targeted spell with no visible monsters adds MP from nothing (free MP exploit)
status: open
systems: [magic, spells, player_mana]
evidence:
  - src/game_magic.py:1024-1029 — MP check on entry: returns early if `self.player.mp < mp_cost`
  - src/game_magic.py:1032-1057 — targeted-spell branch
  - src/game_magic.py:1043 — `self.player.mp += mp_cost  # refund MP` — but MP was NEVER deducted at this point
  - src/game_magic.py:1046 — MP is only deducted AFTER the candidate check, never before
verified: true
discovered: 2026-05-15

---

## What's wrong

In `_invoke_spell` (game_magic.py:1019), MP is deducted only AFTER the visible-monster candidate list is built and proven non-empty. But the "no candidates" branch at lines 1041-1045 calls `self.player.mp += mp_cost` as if refunding a deduction that never happened:

```python
if spell.get('needs_target'):
    self._pending_spell = spell
    self._pending_spell_id = spell_id
    px, py = self.player.x, self.player.y
    candidates = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
    candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
    if not candidates:
        self.add_message("No visible target for this spell.", 'warning')
        self.player.mp += mp_cost   # <-- ADDS MP that was never deducted
        self.state = STATE_PLAYER
        return
    self.player.mp -= mp_cost      # <-- only deducted on success path
    ...
```

Every time the player attempts to cast a targeted spell with no visible monsters, they gain `mp_cost` MP. There is no cap against `max_mp` because `+=` is a raw attribute write (unlike `restore_mp` which clips at max). The player can grind unlimited MP by repeatedly trying to cast targeted spells in empty rooms.

A secondary related bug: there is no MP refund on the cancel-targeting path (game_input.py:87-95) for spells that DID deduct MP. So a player who selects a target and presses ESC permanently loses the MP. This is the opposite-direction problem — minor player frustration rather than exploit.

## How to reproduce / where it fires

1. Learn any targeted spell (e.g., `fire_bolt`).
2. Walk into a corridor where no monsters are currently visible.
3. Press M, select the spell.
4. Receive message "No visible target for this spell."
5. MP is now `previous_mp + mp_cost` instead of unchanged.

Trace:
1. Player presses M → spell menu → selects spell with `needs_target=True`.
2. `_invoke_spell(spell_id)` runs.
3. MP-check passes.
4. Candidate list built — empty.
5. Line 1043: `self.player.mp += mp_cost`. Free MP.

## Suggested fix

Remove the spurious `+=` at line 1043. The branch should look like:

```python
if not candidates:
    self.add_message("No visible target for this spell.", 'warning')
    self.state = STATE_PLAYER
    return
```

For the secondary cancel-targeting MP-loss issue (P3 sub-finding), the ESC handler at game_input.py:87-95 should refund MP if `_pending_power` starts with `spell_`. Suggested addition before resetting state:

```python
if self.state == STATE_TARGET:
    if (self._power_targeting and getattr(self, '_pending_power', '') or '').startswith('spell_'):
        spell = getattr(self, '_pending_spell', None)
        if spell:
            self.player.mp = min(self.player.max_mp, self.player.mp + spell.get('mp_cost', 0))
    self._throw_targeting = False
    ...
```

## Notes

The bug exists because the developer apparently expected MP to be deducted up-front, then refunded on early exit — but the up-front deduction was later moved to after the candidate check, and the refund line was never removed. Net effect inverts: refund without ever charging = free MP.

Both bugs (free-MP and lost-MP-on-cancel) are reachable in normal play; the free-MP one is exploitable enough to bypass the magic-system economy.
