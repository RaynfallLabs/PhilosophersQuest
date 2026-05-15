---
id: balance-secret-victory-tablet-luck
dimension: balance
severity: P2
title: Secret victory path is RNG-gated — Tablet spawn band F80-99 means players may not find it before reaching F100
status: open
systems: [secret_victory, level_manager, items_artifact, death_chase]
floors_affected: [80, 100]
evidence:
  - balance_curves_agent_a.json:secret_victory_path (tablet_band="80-99", shimmer_band="1-20", wrench_band="21-49", fire_scroll_band="50-79")
  - src/main.py:116-122 (`_lore_levels = {'shimmer': randint(1,20), 'wrench': randint(21,49), 'fire_scroll': randint(50,79), 'tablet': randint(80,99)}`)
  - src/main.py:1345-1371 (`_maybe_place_lore_items` — places once per run when player reaches the chosen level)
discovered: 2026-05-15
---

## What's out of balance

The Secret Victory (Act IV per CONTEXT.md) requires combining four lore items:

1. Philosopher's Stone (drops from Abaddon at F100)
2. Tablet of Second Death (placed at a random floor F80-F99)
3. Philosopher's Wrench (placed F21-F49)
4. Scroll of Lake of Fire (placed F50-F79)
5. Abyssal Shimmer (placed F1-F20)

These four non-stone items are placed ONCE per run, at a single floor each — chosen at game start (`_lore_levels` per src/main.py:116-122).

**Problem**: the Tablet of Second Death's spawn band is F80-F99. If RNG places the Tablet at F95, the player must find it on their initial descent (before reaching F100 and triggering the Death-chase). On the chase ascent, the player ascends F100→F99→F98→...→F1 — they pass through F95 again, but if they MISSED the tablet on descent (it spawns once and remains), they get a second chance, BUT:

- Death is pursuing at speed 50-125% depending on floor band
- Time spent searching F95 floor for a single item = Death gains ground
- The player wants to ascend ASAP, not loiter

If the Tablet spawns at F99 specifically: the descent reaches F99 with one floor to go, finds it (lucky), then F100 fight + ascent. If the player MISSED it on descent and the Tablet is on F99 → they must hike all the way back to F99 while Death pursues. The 1% chance of "Tablet at F99 + missed it on descent" is a frustrating run-loss.

Worse: there's no in-game indicator of WHICH floor the Tablet is on. The player must thoroughly explore every floor F80-F99 on descent to be sure. With dungeon-life features (mysteries, NPCs, encounters), thorough exploration adds 10-20 turns per floor; over 20 floors = 200-400 extra descent turns.

## Curve evidence

- `secret_victory_path.tablet_band` = "80-99" per deliverable
- `secret_victory_path.note` (deliverable): "One of each placed once per run, at random level within band."
- `death_chase_difficulty.speeds_by_floor_during_escape`:
  - F76-100 (immediately post-L100): Death is at 50% — slowest, safest band
  - But this is the same band Tablet may be on if missed
- The placement code (main.py:1352-1371) places the item on a random walkable tile within the dungeon level — could be in a far corner of a 80×50 map. Players need to explore the full floor.

## Suggested re-tuning

Three options:

1. **Narrow the Tablet band** to F80-F89 — guaranteed early enough in descent that players have 10+ floors of "Tablet found, now seek the path" buffer before F100. Floors F90-99 become a known "no-Tablet zone" so players can rush them.
2. **Add a Tier-3 or Tier-4 lore hint** that tells the player the Tablet's floor (data/hints.json). Tier-3 reveals are gated by chain 3 trivia quizzes — keeps the discovery rewarding but learnable. Example T3 hint: "An ancient stone tablet sleeps somewhere below the eightieth floor — its surface awaits the Stone." Currently lore-hints are general not run-specific.
3. **Place Tablet adjacent to a notable landmark** (e.g. an altar or a mini-boss arena). Currently it's placed in any random room. Anchoring it makes the discovery less RNG.

Option 1 is least disruptive.

## Notes

Cross-system: secret_victory_path × level_manager (placement) × death_chase_difficulty (the cost of search during chase) × player route planning.

This finding is P2 because it doesn't break the secret victory — it just makes it luck-dependent in a way that disadvantages thorough explorers (good behavior) vs rushers (worse behavior). The reward economy (`take this code to your father proudly`) means the secret victory is the most-prestigious code drop in the game. RNG should not gate the prestige path.

Also note: `_lore_placed` (src/main.py:122) is a set tracking which items have been placed this run. If a player saves+loads, the placement persists. But the load-save bug (consensus.json P2 main.py:8337) means save violations could enable scumming for ideal Tablet placements. CODE auditor's territory.
