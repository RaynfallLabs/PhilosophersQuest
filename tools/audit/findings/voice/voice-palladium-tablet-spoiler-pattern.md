---
id: voice-palladium-tablet-spoiler-pattern
dimension: voice
severity: P1
title: Palladium, Tablet of Destinies, and Black Stone lore directly explain their mechanics
status: open
systems: [data/items/artifact.json, game_magic.py (identify flow)]
evidence:
  - data/items/artifact.json:297 (Palladium) — "...It reveals the path forward: while carried, the stairs on every floor glow faintly in the bearer's mind, visible even through walls and darkness."
  - data/items/artifact.json:311 (Tablet of Destinies) — "...The Tablet allows its bearer to reject fate once per floor — when a question is answered wrongly, the Tablet cracks and offers a different question. A second chance, drawn from the well of all possible futures."
  - data/items/artifact.json:270 (Black Stone of Sir Gareth) — "...It weighs twenty pounds and cannot be put down — the curse binds it to whoever takes it freely. Only a scroll of Remove Curse can break the bond."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

Three named artifacts present beautifully written mythic openings — Palladium recapping Troy and Odysseus, the Tablet of Destinies invoking Enlil and Anzu, the Black Stone framed as a knight's debt — and then collapse into mechanical exposition in their final sentence:
- "It reveals the path forward: while carried, the stairs on every floor glow faintly..."
- "...once per floor — when a question is answered wrongly, the Tablet cracks and offers a different question."
- "It weighs twenty pounds and cannot be put down... Only a scroll of Remove Curse can break the bond."

The pattern is the same across all three: myth lead-in, then tooltip exit. These lore strings are displayed via `game_magic.py:1995-1997` upon identification — the player sees them in a dedicated lore screen, with implicit emphasis. The mythic register makes the mechanical sentence feel even more jarring than if the whole thing were dry.

## Why it breaks the register

The chronicle voice and the geek-dad mythic register depend on **the player discovering what things do by using them**. The artifact lore samples in CONTEXT.md (Egyptian eye, Roman shield) explicitly *gesture* at the mechanic rather than naming it: "mends what was torn", "thought more clearly under pressure." That register is the contract.

When the Palladium lore says "the stairs on every floor glow faintly in the bearer's mind, visible even through walls and darkness," it's not just spoiling the mechanic — it's also describing the *render* (the glow effect on the map). This is data-layer prose escaping into the player's eyes.

The Tablet is particularly egregious because the entire ritual of the reroll — the cracking, the second-chance feel — is supposed to be a *moment* the player experiences. Reading "the Tablet cracks and offers a different question" beforehand short-circuits the surprise.

The Black Stone is the most defensible of the three (the "cannot be put down" is itself a curse premise, and a player picking up a 20lb item would notice immediately), but "Only a scroll of Remove Curse can break the bond" is still naming the cure path mechanically.

## Suggested rewrite direction

Strip the mechanical-exposition tail sentence from each. The myth carries the meaning:
- Palladium: end at "Odysseus and Diomedes had to steal it before the horse could work." Let the player notice the stairs.
- Tablet of Destinies: end at "Ninurta slew Anzu and returned it." Let the reroll surprise them.
- Black Stone: keep "the curse binds it to whoever takes it freely," strip the scroll-of-Remove-Curse pointer. The puzzle is the point.

If a player genuinely needs a mechanic explanation, that's what the chronicle entry on first use can carry — in the voice of someone discovering it.

## Notes

This is a **pattern**, not an isolated case — three artifacts share the identical structure. The fix is editorial discipline on the final sentence of mythic lore. Other artifacts in the same file (Gleipnir, Bronze Bull, Eye of the Graeae) demonstrate the correct register and serve as the in-house example to copy.
