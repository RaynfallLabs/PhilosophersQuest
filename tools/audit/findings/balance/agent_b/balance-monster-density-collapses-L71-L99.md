---
id: balance-monster-density-collapses-L71-L99
dimension: balance
severity: P1
title: Spawnable-monster density collapses from L71-L99 (3 and 0 species respectively); descent fails to PREPARE the player for L100
status: open
systems: [monsters, dungeon_gen, endgame_pacing]
floors_affected: [71, 99]
evidence:
  - balance_curves_agent_b.json:monsters_by_floor[L71-L80] (spawnable_count 3)
  - balance_curves_agent_b.json:monsters_by_floor[L91-L100] (spawnable_count 0, only Abaddon + locust at min_level 100)
  - src/dungeon.py:1076-1145 (spawn_monsters weighted pool, min_level<=level filter)
  - data/monsters.json (frequency=0 = boss/special, 458 total / 418 spawnable)
  - tests/test_balance.py:81-93 (existing gap test only covers L26-L80 introductions)
discovered: 2026-05-15
---

## What's out of balance

The audit count (`balance_curves_agent_b.json :: monsters_by_floor`, filtered to `frequency > 0`) shows:

| Band | Spawnable species introduced | Top monster HP |
|---|---|---|
| L1-L10 | 214 | 120 |
| L11-L20 | 84 | 600 |
| L21-L30 | 15 | 800 |
| L31-L40 | 36 | 600 |
| L41-L50 | 15 | 1500 |
| L51-L60 | 18 | 1100 |
| L61-L70 | 19 | 2500 |
| **L71-L80** | **3** | **1500** |
| L81-L90 | 14 | 3000 |
| **L91-L99** | **0** | (only Abaddon ml=100 + locusts ml=100) |

L71-L80 introduces only `demon_emperor`, `world_serpent`, `entropy_wraith` (per data/monsters.json grep). L91-L99 introduces *nothing new*. The dungeon at floors 91-99 reuses L81-L90 monsters via the `min_level <= level` filter (`dungeon.py:1095-1097`).

The existing test `test_no_monster_gaps_26_to_80` (`tests/test_balance.py:81`) only checks for *any* monster at *any* min_level inside each 10-floor band — it does not check density or variety. The test passes despite L71-L80 having 3 species total and L91-L99 zero.

This is two cross-system problems:

1. **Descent doesn't prepare for climax.** The "endgame practice" floors L91-99 throw the same monster cast at the player nine times. The player arrives at L100 with no new monster mechanics to teach them. Abaddon is the only new thing in 10+ floors.
2. **L71-L80 (Fenrir boss at 80) is a procedural hike with three monster types.** The hand-crafted L80 Fenrir lair (`boss_levels.py:349-412`) is the wall, but the lead-up is rote.

## Curve evidence

`balance_curves_agent_b.json :: monsters_by_floor[L91-L100].spawnable_count: 0` is the smoking gun row.

Density problem reinforces the time-stop and Sword-of-Michael findings: if every monster on the final 10-floor climb is something the player has already mastered, AND the boss is a 4-hit fight, the climb back is administrative. The Death chase is supposed to *carry* L1-100 ascent, but the upward climb's monster ecosystem is identical to the descent's L81-90 — no new threat appears with Death behind you.

## Suggested re-tuning

Two interventions, parallel:

1. **L71-L80**: add 6-10 new spawnable monsters. Candidates from existing flavor: greater fafnir-spawn (descendants), shadow demon hunters, void prelates. The transition from "lots of variety at L61-70" to "three species at L71-L80" feels procedurally broken, like a generator skipped a step.
2. **L91-L99**: add an "Abyssal heralds" tier of 4-6 monsters with min_level 90-95 and `tags: ["demon"]` to telegraph Abaddon's arrival. Locust precursors. Lesser destroyers. Things whose corpses, when harvested, telegraph the final-floor mechanic.

The fix is additive only — no removals. Per the moral-vision rule in MEMORY.md, do not delete validated content to rebalance.

## Notes

- `min_level: 9999` items (e.g. green_knights_plate) are special drops not in the spawn pool — they're not relevant to monster density.
- A simpler test for the test suite: `assert each 10-floor band has >= 5 spawnable monster species with `min_level` IN that band`. The current `26-80` test gives no signal on density.
- Cross-system: this is monsters + dungeon_gen + the implicit "Death chase tension is sourced from a hostile ecosystem the player has to navigate." Empty ecosystem = no tension reinforcement.
