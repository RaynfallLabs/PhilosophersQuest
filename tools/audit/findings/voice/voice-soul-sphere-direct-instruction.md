---
id: voice-soul-sphere-direct-instruction
dimension: voice
severity: P1
title: Soul Sphere lore directly instructs the player to throw it
status: open
systems: [mystery_system.py, game_combat.py (_throw_soul_sphere)]
evidence:
  - src/mystery_system.py:644-646 — "lore: 'A sphere of crimson and ivory that hums with trapped souls. Ancient texts say these vessels were used to bind creature spirits. One wonders what might happen if it were hurled with force...'"
  - src/game_combat.py:333 — _throw_soul_sphere function: "Throw a Soul Sphere — releases a random pet creature at the landing spot."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The Soul Sphere is a Pokeball — throw it at a monster to capture a pet. This is one of the game's better hidden mechanics: a small red-and-ivory sphere sold occasionally by the Svirfneblin Trader, with a clear visual reference for any kid who's ever seen a Pokeball. The discovery is supposed to be "Wait... what if I... throw this?"

The merchant lore makes that question redundant. "Ancient texts say these vessels were used to bind creature spirits. *One wonders what might happen if it were hurled with force...*" The ellipsis-trailing-instruction is not a hint; it is a stage direction. The player has been told what to do before they have a chance to wonder.

## Why it breaks the register

CONTEXT.md §4 lists hidden mechanics where discovery is itself the reward. The Pokeball joke is at its best when the player has to invent the mechanic themselves. Compare to how `data/hints.json` handles the equivalent — XYZZY:

> *"In 1976, a game was released that hid a secret word deep underground. Those who found it could bend the rules of the world. The dungeon remembers old games."*

That's the model. It locates the reference (1976, Crowther & Woods), gestures at "bend the rules," and stops. The Soul Sphere lore should do the equivalent for Pokémon — locate the reference, gesture at what's possible, leave the verb to the player.

The "One wonders what might happen if..." construction is the literary equivalent of nudging the player with an elbow.

## Suggested rewrite direction

Strip the trailing instruction. The first two sentences land the geek-dad reference cleanly:

> *"A sphere of crimson and ivory that hums with trapped souls. Ancient texts say these vessels were used to bind creature spirits."*

Or extend with myth rather than mechanism:

> *"A sphere of crimson and ivory that hums with trapped souls. Ancient texts say these vessels were used to bind creature spirits — though the binding was not done in calm, and not with words."*

Either version preserves the cultural reference, preserves the price of the item being "weird-and-worth-it", and leaves the throw-mechanic for the player to find.

## Notes

This is the closest analogue in the codebase to the "throw it" discovery mechanic — getting it right matters because future hidden-mechanic items will reference how this one was handled. The current lore is a precedent the codebase should not propagate.
