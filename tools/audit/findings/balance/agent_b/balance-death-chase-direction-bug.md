---
id: balance-death-chase-direction-bug
dimension: balance
severity: P3
title: Death speed escalation thresholds fire in EITHER direction; trigger an ascent->descent re-descent and Death re-mellows
status: open
systems: [death_chase, level_transitions]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:death_chase_difficulty.speed_phases
  - src/main.py:1283-1316 (_maybe_escalate_death uses `level = self.dungeon_level` and bands by raw floor number)
discovered: 2026-05-15
---

## What's out of balance

`_maybe_escalate_death` (`main.py:1283-1316`) sets Death's speed by absolute floor number:
- `level > 75`: 50%
- `level > 50, <= 75`: 75%
- `level > 25, <= 50`: 100%
- `level <= 25`: 125%

This is direction-agnostic. The intended semantics is "Death gets faster as the player gets closer to the surface during the ascent." But a player who started Death-pursuit, climbed to L50, then *descended* back to L75 (via stairs down, possible) would see Death's speed drop from 100% back to 50%. The player can intentionally yo-yo to keep Death at 50%.

This is also a problem at the **start of pursuit**: pursuit triggers when player ASCENDS from L100 (`main.py:1239-1246`). At the moment Death is summoned, `dungeon_level` is still 100, then becomes 99. The speed bands say `>75` is 50%, so Death starts at 50% — fine.

But a player who descends back to L100 (re-fighting Abaddon? exploring?) or who uses teleport-down would still be at 50%. The mechanism does not bind to "ascent only."

Speculation: code path `_change_level(self.dungeon_level - 1, enter_from_top=False)` (ascending) and `_change_level(self.dungeon_level + 1)` (descending) BOTH call `_maybe_escalate_death`. The function should track whether the level is being entered via ascent or descent and only escalate on ascent. Currently it just snaps to the raw floor number.

## Curve evidence

`balance_curves_agent_b.json :: death_chase_difficulty.speed_phases` documents the absolute-floor mapping; the curve has no concept of direction. The `_data_gaps` entry in the JSON flags this: *"Death chase speed escalation thresholds (level<=25 etc) are intended for ASCENT only; code does not distinguish direction explicitly."*

## Suggested re-tuning

Track `self._death_min_speed_reached` — once Death hits 100%, she stays at ≥100% even if the player descends. The speed function becomes monotonic-non-decreasing. Simple:

```python
new_speed = compute_speed_from_level(level)
dm._speed_pct = max(dm._speed_pct, new_speed)
```

This single-line fix prevents the yo-yo exploit.

## Notes

- Severity P3 because the yo-yo path requires the player to *go back down* into the dungeon during pursuit — a strange choice. But "strange choice" is exactly what speedrunners exploit. Mark it.
- Cross-system: death_chase + level_transitions + (implicitly) player_movement.
- Not a P2/P1 because in normal play the chase IS monotonic-ascending. This is theoretical exploit territory.
- Pair with `balance-time-stop-trivializes-death-chase.md` for the bigger chase-exploitability story.
