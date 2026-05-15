---
id: code-quirks-on-disease-drain-dead
dimension: code
severity: P3
title: `on_disease_drain` hook is never called — Paracelsus quirk unreachable
status: open
systems: [quirks, status_effects]
evidence:
  - src/quirk_system.py:882 — `def on_disease_drain(self, stat, amount)` defined
  - src/quirk_system.py:885-888 — Paracelsus (#5): unlock when `disease_drain_total >= 5`, counter only incremented in this hook
  - `grep -rn on_disease_drain src/` returns ZERO callers
  - src/status_effects.py:323-328 — the only place disease drain happens; calls `player.apply_stat_bonus(stat, -1)` but does NOT call `on_disease_drain`
verified: true
discovered: 2026-05-15

---

## What's wrong

`QuirkSystem.on_disease_drain(stat, amount)` is defined but never invoked. The only path that drains stats from disease is `status_effects.tick_all` (status_effects.py:323-328):

```python
elif effect == 'diseased':
    if not player.has_effect('poison_resist') and not player.has_effect('drain_resist'):
        if random.random() < 0.08:
            stat = random.choice(['STR', 'CON'])
            player.apply_stat_bonus(stat, -1)
            messages.append((f'The disease saps your strength! {stat} -1.', 'danger'))
```

No notification to the quirk system. Paracelsus (#5) — "disease drains 5+ stat points total in one run, unlock for permanent `drain_resist`" — has its counter `disease_drain_total` permanently stuck at 0. The quirk is unreachable.

## How to reproduce / where it fires

1. Get diseased (zombie bite, ghoul bite, mummy contact, drink potion of sickness, etc.).
2. Stand around for ~60 turns to let the 0.08-per-turn drain hit you ~5 times.
3. Lose 5 STR/CON.
4. Open Quirks screen. Paracelsus progress: 0/5. Will never advance.

## Suggested fix

In status_effects.py, after line 327 (`player.apply_stat_bonus(stat, -1)`), notify the quirk system. The cleanest path is via the game reference — but `status_effects.tick_all` only has access to `player`. Two options:

**Option A** (player-side dispatch): give `Player` a back-ref to the quirk system, or have `apply_stat_bonus` itself notify when the call comes from a disease tick. Tag the call with a flag:

```python
# in status_effects.py
player.apply_stat_bonus(stat, -1)
if hasattr(player, '_quirk_hooks'):
    player._quirk_hooks.disease_drain(stat, 1)
```

**Option B** (return messages, dispatch in caller): Have `tick_all` return additional metadata, and have `main.py` handle the dispatch. Less coupling but more plumbing.

The simplest practical fix is to have `Game._advance_turn` watch for the disease-drain message in `effect_msgs` (main.py:1565-1575) and dispatch:

```python
for text, mtype in effect_msgs:
    ...
    elif text.startswith('The disease saps your strength!'):
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_disease_drain('UNKNOWN', 1)  # stat info lost, but counter still ticks
```

This loses the stat-name precision but at least unlocks the quirk.

## Notes

P3 (rather than P2) because only one quirk is affected and the quirk is niche (most players actively avoid being diseased and cure it quickly). The bug shape is identical to `on_quiz_complete`: defined-but-uncalled hook orphaning a quirk.
