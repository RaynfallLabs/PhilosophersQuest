---
id: balance-f35-kitchen-sink
dimension: balance
severity: P3
title: F35 introduces 27 new monsters in a single floor — variety dump vs neighboring floors
status: open
systems: [monsters, dungeon_progression]
floors_affected: [33, 38]
evidence:
  - balance_curves_agent_a.json:monsters_by_floor (entry 35: new_intros_count=27; F33 = 0; F34 = 0; F36 = 1)
  - data/monsters.json (27 monsters with min_level=35)
discovered: 2026-05-15
---

## What's out of balance

The F35 floor introduces **27 new monster types** in one go. By comparison:

- F33: 0 new intros
- F34: 0 new intros
- F36: 1 new intro (one monster)
- F38: 1 new intro
- F40: 9 new intros (mini-boss + 8 others)
- F45: 6 new intros

F35 represents a "variety dump" — the dev added a large batch of mid-game monsters all at the same min_level rather than spreading them across F30-F40. This means:

1. The player has the same monster pool from F32-F34, then suddenly the pool TRIPLES at F35.
2. Monsters introduced at F35 then persist through F60-F70 in many cases, so the F35 dump anchors the entire mid-game variety.
3. The neighboring floors (F33, F34, F36, F37) feel monotonous by contrast.

This isn't a difficulty problem — the F35 monsters have appropriate avg HP (~141 per deliverable). But it's a pacing problem: encounter variety should ramp smoothly with depth, not arrive in step functions.

## Curve evidence

- `monsters_by_floor[34]` (F35): new_intros_count=27. Looking at the list: many F35 entries include greater_mimic variants, frost_crawler, vampire_spawn, multiple demons.
- Neighboring floors:
  - F30: 6 new
  - F31: 0 new
  - F32: 1 new
  - F33: 0 new
  - F34: 0 new
  - F35: **27 new**
  - F36: 1 new
  - F37: 0 new
  - F38: 1 new

The L35 cluster is anomalously large. Compare to other "rich" floors: F1 (20 monsters intro), F4 (37), F7 (34), F14 (29), F35 (27), F40 (9), F61 (4). F35 is one of the most-loaded floors but it's mid-game, not early or boss.

## Suggested re-tuning

Spread the 27 monsters across F33-F40. Assign min_level values F33=4, F34=5, F35=5, F36=4, F37=4, F38=3, F39=2 (totals 27 across 7 floors). This:

1. Removes the F33-F34 dead zone.
2. Smooths the variety ramp toward F40 (Medusa boss).
3. Keeps the F35 floor feeling significant without it being the lone variety floor.

Alternatively, leave F35 as the "deep midgame thicket" but add 2-3 new monsters each at F33, F34, F36, F37 to remove the dead-band feel — without removing from F35.

## Suggested re-tuning (alternative)

If the dev wants F35 to remain a "discovery floor" (per the L35 boss-level cadence — though F35 is NOT a boss floor, F40 is), reduce to ~10-12 monsters at L35 and move the remainder to L32-L38. Reserve L35 for thematically-linked monsters.

## Notes

Cross-system: monster intros × dungeon variety pacing × the kid-player expectation of "things get more interesting as I go deeper." Currently the F33-F37 stretch feels lopsided.

This is P3 — it's a variety/pacing concern, not a numerical imbalance. Severity could rise if play-test reveals the F33-F34 dead floors actually feel boring to kids (per the FUN dimension).
