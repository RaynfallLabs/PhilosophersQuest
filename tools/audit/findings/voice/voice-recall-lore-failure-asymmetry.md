---
id: voice-recall-lore-failure-asymmetry
dimension: voice
severity: P3
title: Recall Lore opening line ("You close your eyes...") is in voice but failure follow-ups are uneven
status: open
systems: [game_magic.py (_start_recall_lore, _resolve_recall_lore), data/hints.json (success path)]
evidence:
  - src/game_magic.py:83 — "self.add_message(\"You close your eyes and search your memory...\", 'info')"
  - src/game_magic.py:116 (chain==0) — "self.add_message(\"Your thoughts scatter. Nothing surfaces.\", 'warning')"
  - src/game_magic.py:130 (file load fail) — "self.add_message(\"A lore scroll crumbles in your memory.\", 'warning')"
  - src/game_magic.py:137 (no pool) — "self.add_message(\"Nothing comes to mind.\", 'info')"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The Recall Lore loop is the heart of the game's discovery vehicle. The voice on it is mostly excellent — the opening "You close your eyes and search your memory..." perfectly sets the meditative-scholarly mode; the chain-0 failure ("Your thoughts scatter. Nothing surfaces.") is exemplary encouraging-on-failure language.

Two of the three failure paths are not quite the same caliber:
- File-load failure: *"A lore scroll crumbles in your memory."* — This is *technically* mythic, but it's reporting an internal error (data/hints.json failed to load) in mythic register. The player will never see this unless something is broken. It's a half-good string for a half-broken state.
- Empty pool: *"Nothing comes to mind."* — Bland; reads more like a player giving up than the dungeon withholding.

## Why it breaks the register

The chain-0 line ("Your thoughts scatter. Nothing surfaces.") is the *correct* failure tone — body-aware, mythic, in voice. The other two failure-adjacent lines are written by different gravity.

This is also a missed opportunity: the WIS-stat encouragement is specifically the kind of moment where the game can reinforce the parent-coaching tone ("you tried, you couldn't pull it up, that's how knowledge works"). All three failure lines should serve that purpose.

## Suggested rewrite direction

The chain-0 line is the model. Bring the others to match:

- File-load failure (rare, indicates bug): *"The dungeon's memory is silent today. Try again later."* (less mythic, more honest about the system state — the player can debug it)
- Empty pool: *"The well of stories is empty for now. Press on; more will surface as you descend."* (reinforces the descend-and-try-again loop)

## Notes

The chain-0 failure line is a model and is properly cited in CONTEXT.md's voice samples by implication ("Your thoughts scatter"-class lines are exactly the encouraging-on-failure register). The other two could be brought to the same level.
