---
id: code-lake-of-fire-scroll-destroyed-on-fail
dimension: code
severity: P1
title: Failing the grammar quiz on Scroll of the Lake of Fire destroys it — secret-victory unrecoverable
status: open
systems: [magic, scrolls, secret-victory]
evidence:
  - src/game_magic.py:1544 — `self.player.remove_from_inventory(scroll)` runs BEFORE the success check
  - src/game_magic.py:1546-1551 — on `not result.success`, scroll is never re-added; "scroll crumbles unread"
  - src/game_magic.py:1938-1939 — on success, lake_of_fire effect appends scroll back to inventory
  - src/items.py:498-518 — `make_scroll_lake_of_fire` is the unique deep-lore scroll; only one is spawned per run (one per fire_scroll level range 50-79)
  - src/main.py:1352-1358 — `_lore_placed` set prevents respawn within a run
verified: true
discovered: 2026-05-15
---

## What's wrong
`_read_scroll`'s callback at `game_magic.py:1540-1558` follows this order:
1. Line 1542: `scroll.identified = True`
2. Line 1544: `self.player.remove_from_inventory(scroll)`  ← scroll is GONE from inventory
3. Line 1546-1551: if `not result.success`, print "scroll crumbles unread", advance turn, return
4. Line 1553-1558: on success, apply effect → for `lake_of_fire`, the effect handler re-appends the scroll

For the **Scroll of the Lake of Fire** (one of only 5 spawn-once deep-lore artifacts and the trigger for the secret victory ending — Act IV), failing the grammar quiz **permanently destroys** the scroll. The game's intent (lore comment at game_magic.py:1938) is *"Keep the scroll in inventory -- it may need to be read again"* — but only the success path honors that intent. The failure path removes the scroll first and then never re-adds it.

The scroll spawns exactly once per run on a floor in the 50-79 range (`main.py:119`, `main.py:1352-1358`, `_lore_placed` gating). If the player carries it to L100, kills Abaddon, ascends, brings Death to the Abyssal Shimmer, and then **fails one grammar quiz**, the secret-victory ending becomes mechanically unreachable for the rest of the run. There is no respawn, no fallback, no in-game way to recover it.

This violates the difficulty contract documented in CONTEXT.md: "The Scroll of Death's Bane" is the maximum-prestige reward code, and "Death is Dead" is the secret victory. Difficulty should come from the quizzes themselves, not from one-shot artifact destruction on a single grammar threshold roll.

## How to reproduce / where it fires
1. Reach a level in 50-79 range and pick up the Scroll of the Lake of Fire (`scroll_lake_of_fire`).
2. Read it (`s` key).
3. The grammar threshold quiz starts (quiz_tier=3, quiz_threshold=3).
4. Answer just enough wrong to fail the threshold.
5. `_read_scroll.on_complete`:
   - line 1544 removes the scroll from inventory.
   - line 1546-1551 prints "you stumble over the words — the scroll crumbles unread."
   - The scroll is **gone forever**.

Call graph: `read scroll` keybind → `_read_scroll(scroll)` → `start_quiz(grammar, threshold=3)` → quiz callback → on failure, scroll is destroyed.

## Suggested fix
The Lake of Fire scroll must survive a failed read because it is the unique secret-victory trigger. Two options:

**Option A (preferred, minimal)** — In `_read_scroll.on_complete`, special-case `lake_of_fire`: do not remove the scroll on failure. Add a guard before line 1544:

```python
if not result.success:
    if scroll.effect != 'lake_of_fire':
        self.player.remove_from_inventory(scroll)
    self.add_message(
        "You stumble over the words -- the scroll's power fades for now.",
        'warning'
    )
    self._advance_turn()
    return
```

**Option B (broader)** — Apply the same protection to all unique deep-lore scrolls (e.g., `scroll_deaths_bane`, any future one-shot scrolls). Tag them with a class-level flag like `single_copy = True` and skip removal on failure.

Either fix preserves the design intent: the scroll teaches an inscription the player must read repeatedly to invoke. Failing once should waste a turn, not waste a run.

## Notes
This is plausibly already a known design tension — the `boss_reward` effect (line 1583-1590) explicitly re-adds the scroll because the player needs to re-read it for the reward code. The `lake_of_fire` effect does the same on the success path. Only the failure path was missed.

The Scroll of Death's Bane (`scroll_deaths_bane`, items.py:569-588) has the same vulnerability: it's the reward for the secret victory and would also be destroyed on a failed grammar quiz (its quiz_threshold=1 makes failure unlikely but not impossible).
