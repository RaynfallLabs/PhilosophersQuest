---
id: voice-pandora-fail-text-soft-spoiler
dimension: voice
severity: P2
title: Pandora's Coffer fail_text telegraphs the invert-result trick via scare-quotes
status: open
systems: [mystery_system.py, items code (Pandora key spawn)]
evidence:
  - src/mystery_system.py:42 — "'fail_text': \"You open it 'correctly' -- but nothing is inside. Only gold.\""
  - src/mystery_system.py:44 — "'invert_result': True,  # INVERTED: failure quiz = actual reward"
  - src/mystery_system.py:36 — "description: \"A sealed obsidian coffer. A warning is etched: 'Do not open.' The keyhole glows red.\""
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

Pandora's Coffer is a mystery altar where the mechanic is **inverted**: failing the economics quiz produces the real reward, succeeding produces the "punishment" (just gold). The mystery is themed on the myth — Pandora is punished for opening the box correctly; only the "wrong" opening leaves Hope inside.

The fail_text says: *"You open it 'correctly' -- but nothing is inside. Only gold."* The scare-quotes around "correctly" point at the joke — it's "correctly" in the mechanical sense but "incorrectly" in the moral sense. A player who sees this on their first attempt now knows: failing the quiz was the right move. The next mystery they encounter where the description says "Do not open" or "Do not drink", they'll know to fail.

This is the soft spoiler version — not a direct mechanic reveal, but a wink that decodes the trick.

## Why it breaks the register

The mystery description itself ("A warning is etched: 'Do not open.' The keyhole glows red.") is doing the geek-dad work — it gestures at Pandora's myth, it warns the player not to open, it leaves the inversion for them to discover. The fail_text undermines that work. The scare-quotes are an authorial wink at the camera.

Compare to how the **success** path would read in a non-inverted mystery — silent on whether the player chose right or wrong, just delivering the outcome. The Pandora "fail" doesn't need to editorialize; the gold-only outcome speaks for itself.

## Suggested rewrite direction

Remove the scare-quotes and the meta-commentary. Two versions:

Version 1 (mythic, neutral):
> *"You open it cleanly. Only gold tumbles out. The warning was for someone else, perhaps."*

Version 2 (mythic, ambient):
> *"The coffer opens without resistance. Inside: gold, and a faint, disappointed sigh."*

Either preserves the mythic register and leaves the player to wonder whether they got it right. On a second playthrough or after seeing other inverted mysteries, they'll figure out the pattern — that's the discovery loop working.

## Notes

This is a single-line fix in `mystery_system.py:42`. Worth doing because it's the *clearest* version of the inverted-quiz mechanic in the game, and getting it right sets the template for future mysteries that may use the same `invert_result` flag.
