---
id: balance-iron-sword-carries-to-floor-20
dimension: balance
severity: P3
title: Tier-1 weapons (25 at min_level 1) carry past their band; no new weapons L2-L19 except 4 outliers
status: open
systems: [weapons, dungeon_gen_loot]
floors_affected: [2, 20]
evidence:
  - balance_curves_agent_b.json:weapons_by_min_level (25 at L1, 1 at L3, 1 at L4, 1 at L5, 1 at L8, 1 at L10)
  - data/items/weapon.json:iron_sword (baseDamage 6, floorSpawnWeight {"1-20":100,"21-40":60})
  - src/dungeon.py:1249 (_item_eligible_weighted uses floorSpawnWeight)
discovered: 2026-05-15
---

## What's out of balance

`balance_curves_agent_b.json :: weapons_by_min_level` shows a steep front-load: **25 weapons at min_level 1**, then a desert of 1 weapon at L3, 1 at L4, 1 at L5, 1 at L8, 1 at L10 — so floors 2-20 are mechanically a long iron-sword tail. The next big batch arrives at L21 (26 weapons), then again at L41, L61, L81.

The `floorSpawnWeight` map on iron_sword (100 weight at 1-20, 60 at 21-40) keeps it dominant for the whole first 20 floors and into the early 20s, by design. But there's no *new* mid-range damage upgrade between L1 and L20 for the player to feel "better gear." `tests/test_balance.py:test_weapon_spawn_weighting` only verifies iron_sword weight is HIGHER at L1 than L100, not that something else fills the gap.

This is a "dead band" finding in the rubric sense: the player makes no equipment decisions for 18-20 floors at the start of the run. The early game is supposed to be character-learning, so the band is partly tolerable — but the same shape repeats at L41-L60 (`26 at L41`, then 7 single-weapon floors before L61's batch), and at L61-L80 (`22 at L61`, then 11+8 small batches at L65/L70, then 22 at L81). So the *whole curve* is batch-batch-batch with deserts between.

## Curve evidence

| min_level | weapons introduced |
|---|---|
| 1 | 25 |
| 3-20 | 7 (one weapon at most each "interesting" level) |
| 21 | 26 |
| 22-40 | 6 |
| 41 | 25 |
| 42-60 | 11 |
| 61 | 22 |
| 62-80 | 14 |
| 81 | 22 |
| 9999 | 15 (specials) |

The batching is on the boss-level boundaries (1/21/41/61/81 = entry to each 20-floor act). The dev clearly *intended* this — new act, new gear tier — but the in-between floors offer no incremental decisions.

## Suggested re-tuning

1. Spread the 25-weapon "act 1" batch across L1, L5, L10, L15 — so a player who reaches L10 sees a new sword class introduced (e.g. shortsword at L1, longsword at L5, scimitar at L10).
2. Same shape at L21 (act 2): 5 weapons at L21, 5 at L26, 5 at L31, 5 at L36 instead of 26 at L21 and ~6 trickled out.
3. The `floorSpawnWeight` system can stay — it controls *rarity* — but `min_level` should be the *introduction floor*. Currently min_level is overloaded.

## Notes

- This is P3, not P1, because the game IS playable through these bands — items still drop, just no NEW item types. The aesthetic problem is bigger than the mechanical one.
- Cross-system: weapons + dungeon spawn weighting + the implicit "loot table per floor should feel new every 5 floors" expectation from NetHack lineage.
- The 9999 min_level weapons are explicitly special drops (quest rewards, judgment, etc.) — they should be excluded from the "new gear per floor" expectation.
