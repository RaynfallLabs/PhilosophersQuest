---
id: voice-equipment-flatness-versus-lore
dimension: voice
severity: P3
title: Equipment success messages ("You wield X!", "You wear Y!") are flat against the gorgeous item lore
status: open
systems: [main.py / game_input.py (equip flow), data/items/*.json (lore)]
evidence:
  - data/items/artifact.json:24 (Bronze Bull lore) — "A small bronze figure of a bull, worn smooth by centuries of prayer. King Minos was given such a bull by Poseidon..."
  - data/items/potion.json:23 (Healing Potion lore) — "Brewed from cave moss and blessed spring water by wandering hedge-witches, this potion knits torn flesh with a gentle warmth..."
  - Equipment messages across game_input.py / main.py — pattern of "You wield the {weapon.name}.", "You wear the {armor.name}.", "You put on the {accessory.name}." (functional confirmations, no voice)
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The game spends enormous care on item lore — every potion, scroll, wand, artifact has a lovingly-written paragraph of mythic register. When the player actually picks up and equips that item, the in-message-log confirmation is bland: *"You wield the iron longsword."* / *"You wear the leather armor."* / *"You put on Ariadne's Thread."*

The lore is hidden behind the identify quiz; the equip message is the only confirmation the player gets in the message log on what should be an event. For unique/artifact items especially, this is a tonal collapse from gorgeous lore to functional bookkeeping in the same heartbeat.

Compare to the chronicle line that fires on legendary identifies (game_magic.py:1993): *"Identified something remarkable: {item.name}. The lore runs deep."* — that's the chronicle voice doing the work. The equip message lives one panel away in the message log and doesn't match.

## Why it breaks the register

Equipping a named artifact is the kind of moment where the chronicle voice should fire — the player has retrieved Mjolnir from the Dwarven Forge, won it through a math quiz, and now puts it in their hands. "You wield Mjolnir." is what should come *after* a beat of recognition that something has happened.

The chronicle already exists for some equip moments (e.g., the Vidar's Sandal equip in game_divine.py:521). The pattern of "chronicle fires on first-equip of a named artifact" could be extended.

## Suggested rewrite direction

Two options:

(a) Add a chronicle entry for first-equip of named/artifact items, matching the pattern in game_divine.py:521:
- `Mjolnir` first equip: *"Took up Mjolnir. It is heavier than expected. The dwarves built it for a god."*
- `Ariadne's Thread` first equip: *"Wrapped Ariadne's Thread around my wrist. I can feel the labyrinth on the other end."*

(b) Lift the equip message itself for named items, e.g. detect `item_class == 'artifact'` and use a richer template:
- *"You take up {item.name}. The weight is right."*

Option (a) preserves the message-log/chronicle split and is more in keeping with the existing patterns. Option (b) makes the message log itself less flat.

## Notes

Equipping is a frequent action. Even a small lift on artifact equip messages would close the lore→equip register gap without expanding effort to every iron-dagger pickup.
