---
id: code-stone-on-shimmer-tablet-not-consumed
dimension: code
severity: P3
title: Complete Tablet stays on the floor after Abyss triggers — player can carry the Stone post-victory
status: open
systems: [secret_victory, abyssal_shimmer, artifacts]
evidence:
  - src/main.py:1373-1407 — `_trigger_abyss` removes the Shimmer (line 1406) and clears `death_pursues`/`death_monster`, but does NOT remove the Complete Tablet from `self.ground_items`
  - src/main.py:1478-1489 — `_calc_score` awards 50,000 stone-bonus to `complete_tablet_of_second_death` carry
  - src/main.py:1449-1461 — `_do_exit` (L1 ascent) re-checks for Stone or Complete Tablet to determine victory popup vs. abandonment
  - src/game_magic.py:1939 — the `scroll_lake_of_fire` is re-inserted into inventory after read (also stays)
verified: true
discovered: 2026-05-15

---

## What's wrong

After the secret-victory ritual at `_trigger_abyss`, the player has:
- Killed Death (death_pursues = False, death_monster = None).
- Received the Scroll of Death's Bane (`make_death_bane_scroll` spawned at the Shimmer tile).
- Lost the Shimmer (line 1406 filters it from ground_items).

But the **Complete Tablet of Second Death is still on the floor at the same tile**. Nothing consumes it. The player can pick it back up and carry it. Then either:

1. **Re-exit the dungeon via L1.** The exit check at main.py:1449-1454 sees `complete_tablet_of_second_death` in inventory and treats this as carrying the Stone — fires the "exit_with_stone" victory ending in addition to the Abyss ending the player already received.

2. **Score it.** `_calc_score` (main.py:1488) gives `+50000 if has_stone`, where `has_stone` includes Complete Tablet. The player double-banks the Stone bonus — once for the Abyss kill, once for the exit.

3. **Walk back down to L100** carrying the Tablet (no mechanism stops it). The check at main.py:1239 says "trigger Death the moment the player leaves L100 carrying the Stone (either the raw stone or the Complete Tablet)". Death is already dead. `_trigger_death_pursuit` would re-spawn a new DeathMonster. Now the player is being chased again after killing Death — pure narrative incoherence.

The third path is the most damaging: the player can theoretically replay the chase indefinitely.

Whether this is intentional ("the Tablet remains as a relic") or a bug ("the Tablet should be consumed") is a design call. But the consequences listed above suggest the Tablet should at least become non-functional (no chase trigger, no Stone-bonus score) after the Abyss has consumed Death.

## How to reproduce / where it fires

1. Complete the secret victory sequence: drop Complete Tablet on Shimmer, bait Death onto Shimmer, read scroll_lake_of_fire.
2. Watch the abyss trigger. Death is consumed.
3. Pick up the Complete Tablet (still at the Shimmer's old tile).
4. Walk to a down-staircase. Descend to L100. Walk back to up-stairs. Ascend.
5. `_ascend_stairs` at main.py:1239 fires `_trigger_death_pursuit` again — a new DeathMonster instance.

The reproduction is contrived because the player has to choose to do this, but the game offers no countermeasures.

## Suggested fix

In `_trigger_abyss` after consuming Death, also remove the Complete Tablet:

```python
# Remove the Shimmer (the Abyss has closed)
self.ground_items = [g for g in self.ground_items if g.id != 'abyssal_shimmer']
# Also consume the Complete Tablet — its purpose is fulfilled
self.ground_items = [g for g in self.ground_items if g.id != 'complete_tablet_of_second_death']
```

Alternatively, leave the Tablet but give it a `spent` flag (`tablet.spent = True`) that:
- Blocks `_trigger_death_pursuit` in `_ascend_stairs` (re-check the inventory for an UNspent tablet).
- Blocks the L1 exit-with-Stone victory popup.
- Still allows scoring the +50k bonus once.

I prefer consumption — narratively the Tablet was the vehicle for Death's destruction; it should not survive that.

## Notes

This intersects the consensus baseline's coverage of the Abyss / Death-chase paths but was not flagged. P3 because the bug is reachable only via deliberate post-victory replay rather than normal play.
