---
id: voice-combat-log-statblock-dissociation
dimension: voice
severity: P2
title: Combat log is pure RPG-statblock while the chronicle is Cormac McCarthy
status: open
systems: [game_combat.py, combat.py, monster.py, main.py (_log_chronicle)]
evidence:
  - src/game_combat.py:1300 — "CRITICAL! Chain x{chain}! You strike the {monster.name} for {damage} damage!"
  - src/game_combat.py:1302 — "Chain x{chain}! You strike the {monster.name} for {damage} damage!"
  - src/game_combat.py:582 — "The {monster.name} is slain!"
  - src/monster.py:314 — "The {self.name} hits you with {atk['name'].replace('_', ' ')} for {actual} damage!"
  - src/monster.py:285 — "The {self.name} swings at you and misses! (AC {player_ac} deflects)"
  - src/main.py:1264 (chronicle, for contrast) — "Something is following me. I felt it before I saw it. Death itself. I need to run."
  - src/main.py:1399 (chronicle, for contrast) — "I killed Death. The lake of fire opened beneath it and swallowed it whole."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

Combat is the highest-frequency player-facing surface in this game — every move that lands a hit prints a combat-log line. Every chain attack prints `"Chain x{chain}! You strike the {monster.name} for {damage} damage!"` — generic verb, capitalized stat, parenthetical numerics, exclamation-point energy.

The chronicle, the game's literal voice, sits one panel away and says things like "Fenrir is bound. Or dead. I'm not sure which. The ground still shakes." Two different writers appear to be working: one with mythic register and a sense of awe, one with the syntax of a 1995 shareware item-database.

The mismatch isn't subtle. The chronicle is documented in CONTEXT.md as the game's voice. The combat log is what the player reads constantly. The dissociation is structural.

## Why it breaks the register

CONTEXT.md §6 quotes the chronicle voice as the benchmark: "Short sentences. Frank. Slightly Cormac-McCarthy without the violence pornography. Awe without bombast." Combat is where you'd most expect that voice to live — the player is killing something with the math of their own knowledge — and instead it reads as a damage-printer.

This is also where the geek-dad register has the most opportunity. NetHack's combat log varies its verbs ("You hit the gnome. You smite the gnome. You crush the gnome.") and adds situational asides. Philosopher's Quest can do better — its chain mechanic is a fictional/dramatic event (a chain of correct answers), not just a damage multiplier.

The (AC X deflects) parenthetical on miss is also a tooltip leak — it's bookkeeping language in narrative space.

## Suggested rewrite direction

Variety + register lift. The chain count can stay (it's load-bearing for the player's feedback loop), but the verb and surrounding language can vary. Examples:

- Chain x1: "Your blade finds the {monster.name}. ({damage} damage)"
- Chain x3: "Three answers, three strikes. The {monster.name} reels. ({damage})"
- Chain x5: "You move faster than the {monster.name} can think. ({damage})"
- CRITICAL: "The math snaps clean. CRITICAL — {damage} damage."

Monster attack: replace "hits you with poison bite for 8 damage" with something like "The cave cobra strikes — fangs in the calf. (8 damage)". Boss attacks can carry more weight than mooks.

Most-impactful: have ~5–8 chain-tier templates the engine picks from, so the player doesn't see the exact same string 200 times per run. Even small variation moves this from 2/5 to 4/5.

## Notes

The combat log is far and away the most-read text surface in the game. Even a 30% improvement here is the largest possible voice gain in the project. The chronicle is already pitch-perfect — this finding is about closing the distance between the two so a player reading the message log doesn't feel they're playing two different games.
