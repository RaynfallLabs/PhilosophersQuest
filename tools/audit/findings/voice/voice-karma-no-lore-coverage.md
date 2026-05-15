---
id: voice-karma-no-lore-coverage
dimension: voice
severity: P2
title: Karma system has no lore coverage despite being a substantial moral track
status: open
systems: [data/hints.json, game_encounters.py (karma chronicle), npc_encounters.py]
evidence:
  - data/hints.json (all 5 tiers, full read) — no entry mentions karma, moral weight, or the dungeon judging deeds
  - src/game_encounters.py:732 (karma=10 chronicle) — "I feel... clean. Like everything I've done down here has mattered. The dungeon feels lighter."
  - src/game_encounters.py:734 (karma=-10 chronicle) — "Something inside me has gone cold. The dungeon doesn't frighten me anymore. That frightens me."
  - src/npc_encounters.py docstring — "Options show action + justification only — no outcomes, no karma labels."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The game has a substantial karma system tied to NPC moral encounters (the 30-encounter, 10-block structure in `npc_encounters.py`). Each encounter has a karma-positive, neutral, and karma-negative option; the cumulative score has gameplay consequences at thresholds (`game_encounters.py:731-734` fires chronicle messages at karma == 10 and karma == -10).

A player can complete a full 100-floor run, save several NPCs (or steal from them), and only learn the system exists in three ways: (1) the option text gives no karma labels (intentional, per file docstring); (2) the chronicle eventually fires the threshold-crossing message; (3) some NPCs may telegraph it ("the dungeon weighs your deeds"). There is *no* `data/hints.json` entry that gestures at this entire moral system.

This is in tonal contrast with how the rest of the game is documented in lore. T2 hints discuss altars, T3 discusses karma-adjacent figures (Cassandra, Tantalus, Job), but the karma mechanic itself — a load-bearing system spanning 10 levels of the game — has no in-fiction acknowledgment in the hint corpus.

## Why it breaks the register

The geek-dad register depends on the lore corpus being thematically *thorough*. A child who plays the game, makes hard choices in NPC encounters, and never encounters a hint that gestures at "the dungeon remembers" loses out on the mythic framing that gives those choices weight beyond the immediate outcome.

The NPC encounter docstring (`npc_encounters.py:6`) is intentional and correct ("no karma labels"). The mechanic-level discretion is a feature — the player shouldn't see "+1 karma" in the choice menu. But the *thematic* framing — the idea that what you do underground is being weighed — belongs in the Recall Lore corpus as a mid-tier hint.

## Suggested rewrite direction

One or two new hints, T3 register:

> *"The dungeon is older than any of us, and it has watched many adventurers descend. Some say it remembers each one — not their gold, not their kills, but the moments when they chose between a hard thing and an easy one."*

> *"Souls in the deep places speak of being weighed. Not by gods, exactly. By something that has been listening longer than gods have been named."*

These would close the gap without naming any specific +karma/-karma values.

## Notes

This is a relatively low-cost addition (1–2 hints.json entries) that meaningfully completes the lore-coverage map. The chronicle voice at karma ±10 is already pitch-perfect — adding gentle foreshadowing hints would make those moments land harder.
