---
id: voice-flux-capacitor-spoils-mechanic
dimension: voice
severity: P1
title: Flux Capacitor lore spoils the time-stop mechanic outright
status: open
systems: [main.py, game_magic.py]
evidence:
  - src/main.py:1440-1441 — "A device of impossible origin. Its single charge can freeze time itself for 10 turns. Use it wisely -- there are no second chances."
  - src/game_magic.py:165 — "The Flux Capacitor ignites! Time freezes around you -- 10 turns!"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The Flux Capacitor is a unique reward artifact. Its `lore` field, defined inline in `main.py` (not in `data/items/`), reads as a tooltip rather than as lore: "Its single charge can freeze time itself for 10 turns." This is verbatim mechanical exposition — charge count, effect, duration. The activation message at `game_magic.py:165` then re-confirms the same mechanic ("Time freezes around you -- 10 turns!"), reinforcing rather than veiling. The item is `identified=True` from the moment it spawns, so the player reads this prose before any experimentation.

## Why it breaks the register

CONTEXT.md §4 makes hidden-system non-spoiling load-bearing: "Hidden systems are HINTED at by Recall Lore, never directly explained. Direct spoilers in player-facing text are a P1 VOICE finding." Compare to how `data/hints.json` introduces conceptually similar items — the Sumerian mace ("smasher of a thousand minds"), Hephaestus' forge ("the rhythm faltered"), the Crowther/Woods cave word ("if you know where to speak it aloud"). Those gesture at the mechanic through myth. The Flux Capacitor lore reads like an item-database tooltip exported to lore. It also undercuts the "Back to the Future" geek-dad pop wink — the joke lands harder if the player has to figure out what the artifact does.

## Suggested rewrite direction

Mythic, veiled. Something like: *"A device of impossible origin — the gold plating still warm to the touch. The Doctor warned that some inventions are too dangerous to use twice. Press the lever only when you would trade the world for a breath of quiet."* Move the explicit charge count and duration to the in-game effect message (which players see only when they actually use it).

## Notes

This is the **explicit example called out in `tools/audit/dimensions/voice.md` line 38** as the canonical borderline case for the spoiler audit. The answer is: it spoils.
