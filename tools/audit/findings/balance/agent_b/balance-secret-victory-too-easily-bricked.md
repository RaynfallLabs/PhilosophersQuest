---
id: balance-secret-victory-too-easily-bricked
dimension: balance
severity: P2
title: Secret-victory ritual requires 4 random-floor items spanning floors 1-99; missing any one bricks the path
status: open
systems: [secret_victory, dungeon_gen, items, lore_progression]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:secret_victory_path.item_levels
  - src/main.py:115-121 (4 random levels: shimmer 1-20, wrench 21-49, scroll 50-79, tablet 80-99)
  - src/main.py:1345-1371 (_maybe_place_lore_items spawns once per floor)
  - src/items.py:461-541 (item factories: shimmer is terrain, weight 9999 — uncarryable)
discovered: 2026-05-15
---

## What's out of balance

The Abyss ritual (Act IV) requires the player to hold:
- `philosophers_stone` (drops at L100)
- `tablet_of_second_death` (random floor 80-99)
- `philosophers_wrench` (random floor 21-49)
- AND stand on an `abyssal_shimmer` (random floor 1-20)

The shimmer is `weight: 9999.0` and item_class `terrain` (`items.py:461-475`), so it CANNOT be picked up — the player must physically descend back to the floor 1-20 where it spawned, while Death is at 125% speed in that band.

The four items are placed *once* per run, on *one* specific procedurally-chosen floor each (`main.py:1351-1371`). If the player misses the wrench on its single floor — perhaps because it spawned in a locked container that requires a lockpick they don't have, or in a room they never visited — there is no recovery. The path is bricked silently.

The cost of bricking: the entire secret-victory reward code (the most prestigious one in the reward economy per CONTEXT.md) cannot be unlocked this run. The player doesn't know the path is bricked because the four items are unidentified ("plain tablet", "odd tool", "worn scroll", and the shimmer is on the floor invisibly).

Pairwise check:
- Shimmer placement L1-L20: player at 125% Death speed during return ascent. Plausibly survivable.
- Wrench placement L21-L49: player at 100% Death speed during return.
- Scroll placement L50-L79: player at 75% Death speed during return.
- Tablet placement L80-L99: player at 50% Death speed during return.

The 4-item gauntlet is *meant* to be hard but the random-single-floor placement has a high "miss it on the only floor it exists" rate.

## Curve evidence

`balance_curves_agent_b.json :: secret_victory_path` lists the four random ranges. Multiply through: the player must explore "1 of 20" * "1 of 29" * "1 of 30" * "1 of 20" = a specific 4-tuple of floors and find ONE item on each. Floors are 80x50 tiles ≈ 4000 walkable per floor in a typical map. Even with full exploration there's a non-trivial chance the spawned tile is unreachable (locked room, ambush, sealed).

`balance_curves_agent_b.json :: monsters_by_floor[L21-L30].spawnable_count = 15` and the L11-L20 / L41-L50 / L71-L80 deserts make the dungeon thin enough that *if* the player descends slowly and explores, they CAN find each item — but the design depends on the player figuring out the ritual on a first/second run without spoilers (per CONTEXT.md the lore hints should hint, not tell). First-run play almost certainly bricks.

## Suggested re-tuning

1. **Multi-floor placement**: each of the 4 items spawns on 2-3 candidate floors in their band, with the first floor the player descends through being the spawn. Removes the "miss a single floor and brick" failure.
2. **Or**: persist unplaced items across floor descents — if shimmer didn't place on its randomized floor (e.g. floor genned with no valid candidates), retry on the next floor.
3. **Or**: place the items in a known-recoverable container/altar/NPC (shimmer = altar boon at low-floor altar; wrench = locked container; etc.) so the player has a *system* to interact with rather than a needle-in-haystack search.
4. **Inventory carryback for shimmer**: drop the weight=9999 constraint so a player who finds the shimmer early can stash it. Then the ritual can be performed anywhere with the right items.

Option (4) breaks the "ritual on a specific terrain" narrative beat. (3) preserves it best.

## Notes

- Cross-system: items + dungeon_gen + secret_victory + Death chase pacing (one-pass-only ascent).
- The lore hints at tier 4-5 are supposed to teach the path. They live in `data/hints.json`. Recall Lore at chain 5 gives a T5 hint — see VOICE audit for whether the hints are explicit enough to be discoverable but not spoiler-y.
- Speculation: a player who fails to find the wrench *cannot* use the Stone they earned. The chronicle quote "I made it. I climbed back out with the Stone." is still satisfying — but the higher reward is gated behind RNG-survivable exploration.
- The Stone-only victory bonus (50000 score) IS achievable without the ritual. So the failure mode is just "best reward bricked," not "run wasted." That tempers severity from P1 to P2.
