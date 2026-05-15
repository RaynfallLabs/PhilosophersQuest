---
id: voice-oracle-quirk-hints-uneven
dimension: voice
severity: P3
title: Oracle's quirk-reveal hints are uneven — most cryptic, a few effectively name the trigger
status: open
systems: [mystery_system.py, quirk_system.py (_QUIRK_TRIGGER)]
evidence:
  - src/mystery_system.py:414 (good) — "'odin': 'Some wait long enough to perceive all things.'"
  - src/mystery_system.py:415 (good) — "'mithridates': 'The great king survived every poison by tasting each one.'"
  - src/mystery_system.py:417 (too explicit) — "'penelope': 'She wove and unwove, ever patient. Armor is her art.'"
  - src/mystery_system.py:420 (too explicit) — "'merlin': 'Wands were used before they were understood.'"
  - src/mystery_system.py:416 (too explicit) — "'tiresias': 'The blind prophet answered correctly while he could not see.'"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The Oracle's Rift mystery (mystery_system.py:117-130) rewards the player with hints toward 3 random locked quirks. The hint dict at lines 413-425 holds 12 quirks' worth of cryptic hints. The voice quality is uneven:

**Pitch-perfect:**
- *"Some wait long enough to perceive all things."* (Odin)
- *"The great king survived every poison by tasting each one."* (Mithridates)
- *"Music calmed beasts. He descended to find those he had lost."* (Orpheus)
- *"Suffering repeated and survived becomes strength."* (Prometheus)

**Too explicit / names the trigger:**
- *"She wove and unwove, ever patient. Armor is her art."* (Penelope — the trigger is "equip/unequip armor 100 times." The clause "Armor is her art" reduces the myth to the mechanic.)
- *"Wands were used before they were understood."* (Merlin — trigger is "zap 10 unidentified wands." The hint says exactly that, with one figurative layer.)
- *"The blind prophet answered correctly while he could not see."* (Tiresias — trigger is "answer 25 questions correctly while blinded." The hint reads as a description of the trigger.)

The good ones gesture at the figure's myth and let the player connect it. The bad ones describe the mechanic in mythic words but with the structure of a trigger description.

## Why it breaks the register

These hints are shown immediately after a player succeeds at the Oracle — a moment that should feel like a prophet's veiled vision. When three hints appear and one of them is essentially the trigger condition phrased mythically, the player reads it as "oh, do this exact thing" rather than "huh, what does she mean?"

The standard set by the good entries in the same dict (and by `data/hints.json` T3-T5 generally) is to gesture at *who the figure was*, not *what the player must do*. The player should have to connect "wove and unwove" to the equip-unequip pattern themselves.

## Suggested rewrite direction

Rewrite the over-explicit ones to match the cryptic standard:

- penelope: *"What is woven by day can be unwoven by night. The same hands, the same threads, again and again."* (drops "Armor is her art")
- merlin: *"Before he was a wizard, he was a child holding objects he did not understand. He tested them anyway."* (drops "Wands were used before")
- tiresias: *"He gave up sight to gain another kind of sight. He never regretted the trade."* (drops the literal "answered correctly while he could not see")

Same length, same myth-frame, harder discovery puzzle.

## Notes

Three lines to rewrite. The Oracle mystery is a high-leverage moment — this is one of the few times the game gives the player a glimpse at the hidden-quirk space. Worth tuning.
