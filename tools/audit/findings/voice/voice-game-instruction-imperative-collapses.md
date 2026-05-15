---
id: voice-game-instruction-imperative-collapses
dimension: voice
severity: P3
title: Imperative game instructions ("Press 'D' to dig", "Press 'D' to sit") clash with adjacent atmospheric prose
status: open
systems: [main.py (tile-step notifications), ui prompts, flavor_encounters.json (counter-example)]
evidence:
  - src/main.py:1098 — "self.add_message('A shimmering fountain bubbles here. Press \\'D\\' to drink.', 'info')"
  - src/main.py:1100 — "self.add_message('A weathered gravestone stands here. Press \\'D\\' to dig.', 'info')"
  - src/main.py:1102 — "self.add_message('An ancient throne sits here. Press \\'D\\' to sit upon it.', 'info')"
  - src/main.py:1155 — "self.add_message('\\u201cRevelation 20:14\\u201d', 'info')  # Abyssal Shimmer inscription (in voice)"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player steps onto certain interactive tiles (fountain, grave, throne), the game prints two-clause messages: the first clause is atmospheric prose, the second is a keybinding instruction.

- *"A shimmering fountain bubbles here. Press 'D' to drink."*
- *"A weathered gravestone stands here. Press 'D' to dig."*
- *"An ancient throne sits here. Press 'D' to sit upon it."*

The first clauses are in voice. The second clauses are tutorial-tooltip prose grafted onto the atmospheric setup. *"Press 'D' to drink"* reads like the help text from a 2008 RPG.

Compare to how the same screen handles the Abyssal Shimmer just two functions away (`main.py:1154-1155`): *"The ground shimmers with ancient power."* + *"Revelation 20:14"* (the Bible reference as the inscription). No keybinding. No "Press X to commune." The player has to figure it out.

## Why it breaks the register

The first-time-stepping-on-a-throne moment should land as a discovery. Adding "Press 'D' to sit upon it" instructs the discovery away. The player is being told what to do.

This is also inconsistent within the game: the Abyssal Shimmer (`main.py:1154-1155`) provides only atmospheric prose and trusts the player to attempt commands; the throne (`main.py:1102`) explicitly tells them to press D. Two different design philosophies in the same function.

## Suggested rewrite direction

Drop the keybinding instructions. Replace with atmospheric prose that leaves the player to discover the command (the help screen and the ? key already exist for keybinding reference per the T1 hint). Examples:

- Fountain: *"A shimmering fountain bubbles here. The water smells of copper and stars."*
- Gravestone: *"A weathered gravestone stands here. The earth beneath it is loose."*
- Throne: *"An ancient throne sits here. It is the wrong size for anyone modern."*

For accessibility-conscious players, the help screen and the ? hint can carry the keybinding info.

Alternatively, if the keybinding genuinely needs to be reachable from the message log: render it differently (e.g., in italic gray, separately styled) so it reads as UI metadata rather than continuing the prose.

## Notes

Three lines to tune. Same surface pattern as the special-room enter messages (voice-special-room-message-energy) — once you decide whether the message log is in-voice or instructional, apply it consistently.
