---
id: code-death-speed-down-message-mismatch
dimension: code
severity: P4
title: Death speed-down (player descends back) triggers a misleading speed-UP message
status: open
systems: [death_chase, ui_messages]
evidence:
  - src/main.py:1290-1300 — `_maybe_escalate_death` sets `dm._speed_pct` based purely on current `dungeon_level`
  - src/main.py:1303-1315 — announces speed change only when value differs from previous, but the message text always implies acceleration ("Death quickens", "Death matches your pace now", "Death is FASTER")
verified: true
discovered: 2026-05-15

---

## What's wrong

`_maybe_escalate_death` recomputes Death's `_speed_pct` from the current dungeon level every level transition:

```python
if level <= 25: dm._speed_pct = 125
elif level <= 50: dm._speed_pct = 100
elif level <= 75: dm._speed_pct = 75
else:            dm._speed_pct = 50
```

This works fine for ascending (50 → 75 → 100 → 125 — speed monotonically increases). But the death chase doesn't force ascent — the player can descend during the chase (e.g., they accidentally take stairs DOWN, or use a scroll of `gain_level` from food_system.py:482-484 which signals `_gain_level`).

If a player at L25 (speed 125) descends to L26, `_maybe_escalate_death` runs and sets speed to 100. The change message fires: "Death matches your pace now. Every step you take, it takes one too." But Death just got SLOWER — it was 125 (faster than player) and now equals player. The message implies acceleration ("now matches your pace"), which is misleading.

Same problem at the 100→75 and 75→50 transitions if the player descends.

## How to reproduce / where it fires

1. Pick up Stone, ascend to L25. Death is at 125% speed.
2. Drink a potion of (un-)gain-level (descend one floor).
3. `_maybe_escalate_death` recomputes speed to 100%.
4. Message fires: "Death matches your pace now."

But Death is actually slower than before. The chronicle entry "Death moves as fast as I do now. No more outrunning it. I have to be smarter." is now factually wrong — the player IS outrunning Death again.

## Suggested fix

Gate the speed-up messages on direction:

```python
if dm._speed_pct > old_speed:   # only on acceleration
    msg = _SPEED_MSGS.get(dm._speed_pct)
    if msg:
        self.add_message(msg[0], msg[1])
        self._log_chronicle(msg[2])
elif dm._speed_pct < old_speed:
    # optional: announce relief
    self.add_message("Death's pace slows in the darker depths.", 'info')
```

Alternative: forbid setting `_speed_pct` downward, only allow it to climb:

```python
new_speed = ... # computed
dm._speed_pct = max(dm._speed_pct, new_speed)  # monotonic
```

The second option also makes design sense — once Death has matched your pace, descending shouldn't give you a free reprieve.

## Notes

P4 nit. Single-system UX/voice mismatch. The chronicle voice is described in CONTEXT.md as "frank, slightly Cormac-McCarthy"; lines that say "Death is gaining" when it isn't break the contract.
