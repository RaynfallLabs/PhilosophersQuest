---
id: voice-throw-potion-statblock
dimension: voice
severity: P3
title: Thrown potion results are statblock-flat across many effect types
status: open
systems: [game_combat.py (_apply_thrown_potion), combat log surface]
evidence:
  - src/game_combat.py:486-488 — "f\"The {display} splashes {monster.name}! It is {label}!\"  # label is debuff effect_id .replace('_',' ').title()"
  - src/game_combat.py:496-498 — "f\"The {display} splashes {monster.name}. It looks {label}!\""
  - src/game_combat.py:518 — "f\"The {display} splashes {monster.name}. It looks unaffected.\""
  - src/game_combat.py:557 — "f\"The {display} splashes {monster.name} but has no effect.\""
  - src/game_combat.py:550-551 — "f\"The {display} saps {monster.name}'s vitality! ({actual} damage)\""
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The thrown-potion code path (`_apply_thrown_potion`) handles ~20 effect types. All of them produce strings of the form `"The {potion_name} splashes {monster.name}!"` with a swappable effect label. The label is generated mechanically from the effect_id (`debuff.replace('_', ' ').title()`), producing strings like:

- *"The Potion of Confusion splashes goblin warrior! It is Confused!"*
- *"The Potion of Speed splashes goblin warrior. It looks Hasted!"*
- *"The Potion of Healing splashes goblin warrior. It heals 8 HP!"* (you healed the enemy)

The "splashes" verb is consistent and fine. The effect label being `title()`-cased is the tooltip leak — the player is reading `It is Hallucinating!` with sentence-case capitalization that looks like a UI element. The structure is the same across all 20 effect types, which means the player sees this pattern dozens of times per run with only the proper noun changing.

The healing-the-enemy moment is dramatically interesting (you wasted a heal potion on a goblin!) but the line lands flat: *"It heals 8 HP!"* — the same exclamation as every other effect.

## Why it breaks the register

Compared to other combat-log surfaces (which are also flat — see voice-combat-log-statblock-dissociation), this is the same disease in a smaller dose. The potion-throw moments are *narratively interesting* — accidentally healing a tough enemy is a *story*, throwing a Potion of Hallucination on a Sphinx is a *story* — and the text doesn't carry the story.

The fix is similar to combat-log: a small library of effect-specific lines that give the moment shape.

## Suggested rewrite direction

Per-effect overrides for the high-drama cases. Examples:

- Confusion: "The {display} catches the {monster.name} in the face. It staggers, eyes unfocused."
- Healing (own enemy): "The {display} pours over the {monster.name}. The wounds close. You curse aloud."
- Sleep: "The {display} bursts. The {monster.name} sags, then snores."
- No effect: "The {display} splashes. The {monster.name} blinks, unimpressed."
- Resisted: "The {display} hits, but the {monster.name} sheds it like rain."

The generic *splashes* + effect_id pattern can remain as fallback for effects that don't have a custom line.

## Notes

Same surface family as voice-combat-log-statblock-dissociation, but lower frequency (a player only throws a potion occasionally). Lower severity, same fix pattern.
