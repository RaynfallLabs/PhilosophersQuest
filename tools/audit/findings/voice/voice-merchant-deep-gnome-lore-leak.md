---
id: voice-merchant-deep-gnome-lore-leak
dimension: voice
severity: P4
title: Merchant NPC name "Svirfneblin Trader" and lore string read as D&D-statblock geek-dad
status: open
systems: [mystery_system.py (MerchantNPC class), flavor_encounters.json (parallel surface)]
evidence:
  - src/mystery_system.py:592 — "self.name = 'Svirfneblin Trader'"
  - src/mystery_system.py:601-602 — "self.lore = 'A deep gnome trader who navigates the subterranean passages with ease, hauling wares between settlements no surface-dweller has ever seen.'"
  - data/flavor_encounters.json:82-127 (parallel: Suspiciously Cheerful Goblin "Brix") — Brix has a fully realized voice in dialogue, no encyclopedic third-person lore
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The Merchant NPC (`MerchantNPC` class) is a frequently-encountered NPC across many runs — 20% chance per floor to spawn. Their identity is established by:

- **Name:** "Svirfneblin Trader" — this is the D&D term for Deep Gnome. To anyone who didn't grow up on AD&D 2nd edition Monster Manual, this is just a fantasy-syllable name that doesn't tell the player anything.
- **Lore:** *"A deep gnome trader who navigates the subterranean passages with ease, hauling wares between settlements no surface-dweller has ever seen."* — encyclopedic third-person Wikipedia voice.

The flavor_encounters.json file has multiple merchant-class NPCs handled completely differently. Brix the Cheerful Goblin gets a 4-line entrance and a distinct voice ("HELLO CUSTOMER! Brix has very good items! Definitely not cursed! Most of them!"). Grix the "Legitimate" Merchant gets a fully realized stall with signage. The Wandering Herbalist has a voice ("I'm cataloguing. Don't touch the blue ones..."). The Svirfneblin Trader has none — they appear, they have stock, they sell things, no voice.

## Why it breaks the register

The geek-dad register lives in distinct character voices. The flavor_encounters NPCs prove the game can do this — every NPC has a distinct mode of speech. The merchant being voiceless is conspicuous against that backdrop. And "Svirfneblin" is a reference that's *too inside-baseball* for the audience — it's a name only D&D-history nerds will catch, not the broader mythic-canon the rest of the game pulls from.

## Suggested rewrite direction

Either (a) rename the merchant to something with broader cultural recognition (e.g., "Deep Gnome Trader" — descriptive, kid-readable), or (b) give the merchant a distinct in-character voice during the shop interaction (1-2 lines of greeting, a haggling pattern, a sign-off), the way the flavor-encounter NPCs have.

The lore field can stay but should match the register of artifact lore in `data/items/`:

> *"A deep gnome, dust-soft of foot, with a coat full of pockets full of pockets. The Svirfneblin walk the dungeon as their grandfathers walked it — by feel, by memory, and by a refusal to ever be in a hurry. They will not say where they sleep."*

## Notes

P4 nit. Single NPC, but high-frequency encounter (~20% per floor). Worth one writing pass.
