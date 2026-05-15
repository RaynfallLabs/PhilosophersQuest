---
id: balance-monster-front-loading-L1-L10
dimension: balance
severity: P2
title: 214 spawnable monsters at L1-L10 (51% of all spawnable in 10% of floors) — early game floods, late game starves
status: open
systems: [monsters, dungeon_gen, pacing]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:monsters_by_floor (L1-L10 spawnable_count 214 of 418 total spawnable)
  - data/monsters.json (458 total, 418 spawnable across 100 floors)
discovered: 2026-05-15
---

## What's out of balance

The aggregate distribution of spawnable monsters by 10-floor band (`balance_curves_agent_b.json :: monsters_by_floor`):

| Band | Spawnable | % of spawnable | Floor ratio |
|---|---|---|---|
| L1-L10 | 214 | 51% | 10% |
| L11-L20 | 84 | 20% | 10% |
| L21-L30 | 15 | 3.6% | 10% |
| L31-L40 | 36 | 8.6% | 10% |
| L41-L50 | 15 | 3.6% | 10% |
| L51-L60 | 18 | 4.3% | 10% |
| L61-L70 | 19 | 4.5% | 10% |
| L71-L80 | 3 | 0.7% | 10% |
| L81-L90 | 14 | 3.3% | 10% |
| L91-L99 | 0 | 0% | 10% |

The early game is over-populated with creature types; the late game is under-populated. This produces:

1. **Early-floor analysis paralysis**: a new player sees giant_rat, goblin, grid_bug, floating_eye, bat, cobra, zombie, gelatinous_cube, ... (214 species). They cannot learn names. Each is a new harvest/quiz/threat to remember. This is anti-learning early.
2. **Late-game repetition**: L91-99 has the SAME 14 monsters from L81-90 stretched across 9 floors. Each floor is the same encounter table.

This is the kind of finding that comes from data shape, not gameplay. The spawn pool `dungeon.py:1076-1118` uses `min_level <= level` as inclusion filter, which means lower-level monsters CAN spawn deep (with frequency decay past max_level). The proximity weighting at L30+ (`dungeon.py:1110-1117`) corrects this somewhat for deep floors — but it doesn't INVENT new species, only reweights existing.

The L1-L10 surplus could be moved to fill L21-L30 and L41-L50 gaps. Conservation-of-monsters: re-balance the front-loading.

## Curve evidence

`balance_curves_agent_b.json :: monsters_by_floor` is the table. The histogram is severely right-skewed in introduction floor.

A counterweight: the histogram of monster *encounters* (not introductions) is probably more balanced because of `min_level <= level` reuse. But variety = species, not encounter count. Encounter variety is the player's "is this a new threat?" signal.

## Suggested re-tuning

1. **Lift `min_level` on 50-80 of the L1 monsters** to spread them across L1-L25. The introduction floor is a soft signal; floor-spawn-weights can keep them frequent.
2. **Generate or design 30-40 new monsters for L70-L99**: this finding *and* the L71-L80 / L91-L99 finding share a solution. The pool needs more high-level content.
3. **Accept the front-load as "early game variety is its own reward"**: argument for not fixing — kids see lots of monsters in the first hour, get hooked. Counter-argument: 214 in L1-L10 is far past "variety," it's noise.

(2) is the right answer; (1) is the next-best stopgap.

## Notes

- This finding compounds `balance-monster-density-collapses-L71-L99.md`. Together they describe the SAME core problem: monster pool is shaped wrong.
- The 458 monsters total is impressive content. 40 are bosses/specials (frequency=0). The 418 spawnable are a real ecology — they just live mostly at low floors.
- Cross-system: monsters + dungeon_gen + pacing (FUN dimension grazes). BALANCE owns "how many threats per floor"; FUN owns "does that feel monotonous."
