---
id: balance-f17-19-no-monster-intro
dimension: balance
severity: P3
title: Three small monster-intro dead bands (F17-19, F72-74, F94-96) — minor variety gaps
status: open
systems: [monsters, dungeon_progression]
floors_affected: [17, 96]
evidence:
  - balance_curves_agent_a.json:monsters_by_floor (entries 17-19, 72-74, 94-96 all have new_intros_count=0)
  - data/monsters.json (no monster has min_level in {17, 18, 19, 72, 73, 74, 94, 95, 96})
discovered: 2026-05-15
---

## What's out of balance

Three small dead bands where no new monster types are introduced:

- **F17-19**: 3 floors. The previous intro is F16 (6 monsters); next is F20 (the Asterion mini-boss + erlking miniboss + 0 normals). Players cross the L20 boss with the same monster pool they had at F16.
- **F72-74**: 3 floors. Previous L71 has 1 monster; next is L75 (2 monsters). This dead band is partially inside the larger 71-80 equipment dead band — but at least new monsters at L75 land before adamantine gear at L81.
- **F94-96**: 3 floors. Previous is L91 (Seal Demon Death); next is L97 (Seal Demon Silence). The seal-demon chain is paced unevenly (L83/85/87/89/91/93/97). Specifically there's no L94-96 demon.

These are minor — three floors each is not as bad as the 10-floor equipment dead band F71-F80. But they cluster at meaningful narrative beats:

- F17-19 is just before the Asterion (Minotaur) boss at L20. The pre-boss approach floor lacks a fresh threat.
- F94-96 is in the final approach to Abaddon. Sandwiched between seal demons.

## Curve evidence

- `monsters_by_floor[16].new_intros_count` = 6 (F17 inherits)
- `[17].new_intros_count` = 0, `[18].new_intros_count` = 0, `[19].new_intros_count` = 0 (F17, F18, F19)
- `[20].new_intros_count` = 2 (boss + erlking)
- `[71].new_intros_count` = 1 (one monster), `[72-74]` = 0, `[75].new_intros_count` = 2
- `[93].new_intros_count` = 1, `[94-96]` = 0, `[97].new_intros_count` = 1

## Suggested re-tuning

Each dead band gets 1-2 new monster definitions:

- F17-19: a Minotaur cultist (foreshadows Asterion), a maze rat (themed). AI patterns: ambush, hit_and_run.
- F72-74: an ice variant of a mid-game threat (themed for Asgard/Fenrir approach).
- F94-96: a void-touched seer or Abaddon herald (foreshadows Abaddon, lore-ties to the seals).

The variety boost is small but matters because these dead bands are at narrative inflection points (pre-boss approach). Players who notice variety should encounter the dungeon "thickening" toward bosses; currently it thins.

## Notes

Cross-system: monster spawn pool × dungeon-narrative cadence × boss-level foreshadowing. This is a P3 because individually each dead band is short (3 floors), but the placement (right before bosses) makes them feel duller than statistics suggest.

Verify against test_balance.py — the project's own monster gap tests apparently passed despite these gaps. The test threshold may permit ≤3-floor gaps, in which case this finding flags an aesthetic/narrative gap rather than a numerical one.
