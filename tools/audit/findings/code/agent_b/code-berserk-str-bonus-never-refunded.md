---
id: code-berserk-str-bonus-never-refunded
dimension: code
severity: P2
title: Cu Chulainn berserk STR bonus is never refunded — permanent stacking exploit
status: open
systems: [armor-effects, status-effects, stats]
evidence:
  - src/main.py:1601-1609 — re-triggers berserk every turn when hp ≤ threshold; adds STR bonus each time
  - src/main.py:1610-1624 — `elif has_effect('berserk')` STR-refund branch
  - src/main.py:1606 — `self.player.status_effects['berserk'] = _arm_slot.berserk_duration` (direct write, bypasses `add_effect` and the MAX_EFFECT_DURATION cap)
  - src/status_effects.py — 'berserk' is NOT registered in EFFECT_INFO, DEBUFFS, BUFFS, or _EXPIRE_MSGS
  - src/status_effects.py:312-396 — `tick_all` decrements every effect including 'berserk' (no registration required); when it hits 0 it gets popped
verified: true
discovered: 2026-05-15
---

## What's wrong
The Cu Chulainn berserk mechanic in `_advance_turn` at `main.py:1600-1624` has a sequencing bug that breaks STR-bonus management.

Order of operations per turn:
1. `_advance_turn` runs.
2. `self.player.tick_effects()` runs (line 1565) → `status_effects.tick_all` decrements every effect including 'berserk'. When duration reaches 0, the effect is **popped from `status_effects`** (line 399 in status_effects.py).
3. Lines 1600-1609: `if not self.player.has_effect('berserk'):` — fires because berserk was just popped. If hp ≤ threshold, re-trigger berserk by writing `status_effects['berserk'] = berserk_duration` and **adding STR bonus** via `self.player.STR += _arm_slot.berserk_str_bonus` (line 1608).
4. Lines 1610-1624: `elif has_effect('berserk')` — never fires on the expiration turn (berserk was already popped at step 2). The STR refund at line 1622 is unreachable.

Two bad outcomes:

**Case A — player stays at low HP**: Each turn, tick_all decrements berserk to 0, pops it; then line 1601 re-triggers, adding STR_BONUS again WITHOUT refunding the previous one. STR accumulates by `berserk_str_bonus` every turn the player is below threshold. After 10 turns at low HP, STR is +10·berserk_str_bonus instead of +berserk_str_bonus.

**Case B — player heals above threshold**: tick_all expires berserk silently. Line 1601 fires but hp check fails → no re-trigger. Line 1610's elif never sees `has_effect('berserk')==True` because it was already popped. The STR bonus granted on previous trigger is never refunded. Player keeps the +N STR permanently.

Both paths increase STR; neither path returns it.

Additional issue: line 1606 writes `status_effects['berserk'] = berserk_duration` directly, bypassing `add_effect` which would clamp at `MAX_EFFECT_DURATION = 60` (status_effects.py:14). If a Coat with `berserk_duration > 60` is ever introduced, this would silently exceed the system cap.

Additional issue 2: 'berserk' is not in `EFFECT_INFO`/`DEBUFFS`/`BUFFS`/`_EXPIRE_MSGS`. The status panel UI doesn't recognise it. No expiration message is rendered. Players have no in-game signal that berserk dropped (only the message "The fury fades..." at line 1624, which is unreachable per the bug above).

## How to reproduce / where it fires
1. Equip Coat of Cú Chulainn (`berserk_trigger=True`, `berserk_str_bonus=N`).
2. Drop below `berserk_hp_threshold` (25% by default).
3. Watch each turn: STR increments by `berserk_str_bonus`. After 5 turns at low HP: STR +5N.
4. Heal above threshold: berserk expires silently, STR keeps the cumulative bonus.

Call graph: `_advance_turn` → `player.tick_effects()` (pops expired berserk) → `if not has_effect` branch → re-trigger + STR bump.

## Suggested fix
The simplest fix is to register 'berserk' in `status_effects.EFFECT_INFO` so its lifecycle is documented, AND restructure the main.py logic to refund STR BEFORE tick_all clears the effect.

```python
# Refactored: handle berserk lifecycle INSIDE _advance_turn before tick_effects
# (or move it into status_effects.py's tick_all to_expire branch)

# Best approach: emit the STR refund in status_effects.tick_all when berserk expires
# (mirrors the heroism/brilliance pattern at status_effects.py:401-405):

# In status_effects.py tick_all to_expire loop:
elif effect == 'berserk':
    str_bonus = getattr(player, '_berserk_str_bonus', 0)
    if str_bonus:
        player.STR -= str_bonus
        player._berserk_str_bonus = 0

# Then in main.py:1600-1609, only trigger if NOT already berserk; the
# re-trigger-every-turn pattern goes away. Use add_effect to set duration:
if not self.player.has_effect('berserk') and self.player.hp / max(1, self.player.max_hp) <= _bpct:
    self.player.add_effect('berserk', _arm_slot.berserk_duration)
    self.player.STR += _arm_slot.berserk_str_bonus
    self.player._berserk_str_bonus = _arm_slot.berserk_str_bonus
    ...
# Remove the elif refund block entirely (now handled by tick_all)
```

Also register 'berserk' in EFFECT_INFO and BUFFS/DEBUFFS (probably DEBUFFS given the HP cost) and add to _EXPIRE_MSGS.

## Notes
The bug is currently dormant in shipping data because the only `berserk_trigger=True` armor is Coat of Cú Chulainn and its `berserk_str_bonus` is presumably moderate. But the dormancy is fragile — any future armor with berserk + moderate STR bonus exploit-stacks immediately.

Cross-references: `code-monster-tick-effects-double-call` (effect lifecycle pattern), and `code-status-effects-berserk-not-registered` (related — see notes).
