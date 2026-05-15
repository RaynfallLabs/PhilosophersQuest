---
id: voice-pet-mechanic-no-coverage
dimension: voice
severity: P3
title: Pet/Soul-Sphere capture mechanic has no Recall Lore coverage; only the spoilery item lore introduces it
status: open
systems: [data/hints.json, mystery_system.py (Soul Sphere lore), pet_system.py]
evidence:
  - data/hints.json (all tiers, full read) — no entries reference pets, soul-binding, Pokeball-style capture, or named pet figures
  - src/mystery_system.py:644 — Soul Sphere is described only at the merchant; the lore is the only in-game pointer
  - src/pet_system.py (entire file) — pet AI exists but has no hint anchoring
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The pet system is a real mechanic — there's a `pet_system.py`, bonding AI, named pet creatures (Charmander stuffie starts certain builds with one). The capture vector is the Soul Sphere (the Pokeball reference, see voice-soul-sphere-direct-instruction). Yet `data/hints.json` — the entire discovery vehicle of the game — has zero entries that gesture at pets as a concept, soul-binding as a magical practice, or any of the pet-figure references that would frame this mythically (Hercules and Cerberus; Theseus and the bull; Argos the dog; Odin's ravens Huginn and Muninn; Bastet's cats; Anubis' jackal).

A player who learns about pets only through the merchant's Soul Sphere lore (currently too explicit, per voice-soul-sphere-direct-instruction) and the Ash Ketchum secret build greeting ("Gotta catch 'em all") has minimal mythic context for the mechanic.

The Pokémon reference is the punchline. The setup — mythic figures bonding with animals — is what's missing.

## Why it breaks the register

The geek-dad register works best when modern pop-culture jokes (Pokémon, Ash Williams, Geralt, Ciri) are *underlaid* with the classical/mythic register. Without the underlay, the Pokémon reference reads as cute-easter-egg rather than as *Bastet had hers; Odin had his; you can have yours.*

The full set of hidden-character hints in T3-T5 covers most of the geek-dad surface area: there's a hint for the fire-bringer (Prometheus), the bald monk (Diogenes/Buddha), the hooded wanderer (Odysseus), the philosopher-mathematician (Pythagoras), the chainsaw-survivor (Ash Williams), the white-haired hunter (Geralt), the elder-blood girl (Ciri), and even the red-and-white-cap trainer (Ash Ketchum, T5 *"Those who have watched him say he does not fight his battles alone — he fights them through what he has captured."*). That last hint is the only one in the entire 108-entry corpus that gestures at "fighting through what you've captured" — and even there, it's framed as a character's signature, not a system the player can use.

## Suggested rewrite direction

Add ~2-3 hints across tiers that gesture at pets/bonding as a mythic practice:

- **T2:** *"Wild things in the dungeon will sometimes accept a partner if the bond is offered correctly. The old kings of Egypt knew this. Their cats walked beside them, even into death."*
- **T3:** *"Some spheres in the deep places do not stay sealed. The hands that crafted them meant to use them, not to admire them."*
- **T4:** *"Odin had two ravens — Huginn for thought, Muninn for memory. He did not order them; they served because they chose. Some creatures in the dungeon work this way too."*

Combine with rewriting the Soul Sphere merchant lore (separate finding) and the mechanic finds a proper lore anchor.

## Notes

This is the second-largest lore-coverage gap after power-quirks. Like that finding, the fix is additive to `data/hints.json` rather than rewriting existing surfaces.
