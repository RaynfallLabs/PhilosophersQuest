---
id: voice-mimic-detection-hint-tone
dimension: voice
severity: P4
title: Mimic detection hints are vivid but uneven; "Was that... breathing?" works, "tooth?" is jarring
status: open
systems: [main.py (_MIMIC_HINTS in _notify_ground), monster.py (mimic monster lore)]
evidence:
  - src/main.py:1166 — "f\"You see {_an} here. Something seems off… is that a tooth?\""
  - src/main.py:1167 — "f\"You see {_an} here. It glistens with what looks like saliva.\""
  - src/main.py:1168 — "f\"You see {_an} here. Was that… breathing?\""
  - src/main.py:1169 — "f\"You see {_an} here. The hinges look oddly organic.\""
  - src/main.py:1170 — "f\"You see {_an} here. You notice a faint, predatory smell.\""
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player's PER stat is high enough, they get a chance to detect that a container is actually a mimic. The detection rolls a random message from `_MIMIC_HINTS`. The pool is mostly good — three of the five are pitch-perfect ("Was that... breathing?", "The hinges look oddly organic.", "You notice a faint, predatory smell.").

Two of them feel off-tonally:
- *"Something seems off… is that a tooth?"* — the "is that a tooth?" question lands closer to a B-horror movie joke than chronicle register, and the leading "Something seems off…" is filler.
- *"It glistens with what looks like saliva."* — *"what looks like saliva"* is hedged in a way that the other hints aren't; "It glistens" already does the work; the "what looks like saliva" qualifier feels like an author covering for the absurdity.

## Why it breaks the register

The mimic-detection moment is supposed to be the dungeon's voice whispering *don't open that*. The best hints in the pool do that with one image and stop. The two weaker ones either over-explain ("what looks like saliva") or over-tell ("is that a tooth?" reads as comic).

This is the kind of thing that's hard to spot in isolation but matters when the player sees ~3-5 of these per dungeon run. Two-fifths of the pool being off-register means the player hits a flat one about 40% of the time.

## Suggested rewrite direction

Rewrite two entries to match the standard set by the other three:

- "Something seems off… is that a tooth?" → *"The shape of it is wrong. The corners are too soft."*
- "It glistens with what looks like saliva." → *"The wood glistens, as if it has been licked."*

Same trigger, same surprise, less hedge.

## Notes

P4 nit. Fix is two strings.
