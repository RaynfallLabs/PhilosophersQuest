---
id: voice-bones-ghost-flat-encounter
dimension: voice
severity: P3
title: Bones-file ghost encounter is announced in two short generic messages; misses a chronicle-class moment
status: open
systems: [main.py (level entry), bones.py, data/hints.json]
evidence:
  - src/main.py:439 — "self.add_message(f\"You sense a restless presence... the {ghost_name} haunts this floor.\", 'danger')"
  - src/main.py:440 — "self._log_chronicle(f\"Encountered the {ghost_name}. A chill ran through me.\")"
  - data/hints.json — no entries reference bones, ghosts of prior runs, or restless presences as a class
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The bones system is one of the genuinely emotionally resonant features of NetHack-lineage roguelikes: a previous character's ghost (with their gear) haunts a future run, on the floor where they died. The mechanic is in place (`bones.py`, full save/restore). The voice surrounding it is thin.

When the player enters a floor with a ghost:
- Message log: *"You sense a restless presence... the {ghost_name} haunts this floor."*
- Chronicle: *"Encountered the {ghost_name}. A chill ran through me."*

Both are functional, but neither does what the moment deserves — a previous *version of you* (or someone else's name, if you played under multiple names) is here. The message-log line uses two cliché phrases ("restless presence", "chill ran through me"). The chronicle line is brief and template-y where most chronicle lines are vivid.

There is also no `data/hints.json` coverage of bones/ghosts as a concept. A player who has never seen one before encounters it cold.

## Why it breaks the register

Compare to other chronicle entries on equivalent first-time moments:
- First throne sit: *"Sat on a throne in the dark. It fit perfectly. That worries me."*
- First cow dimension: *"I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension. This is not in any lore I've read."*
- First Wrench use: *"Used the Wrench. The Stone and the Tablet fused into one. The Complete Tablet glows with purpose."*

Each of those has personality, specificity, in-character reaction. The bones encounter chronicle ("A chill ran through me") is the most generic phrase in the whole `_log_chronicle()` corpus.

The encounter deserves the same vivid treatment, especially since it's the only mechanic in the game where the player can meet a previous character's name in-fiction.

## Suggested rewrite direction

Rewrite both the add_message and chronicle entries to honor the moment. Suggestions:

- Message log: *"Someone died on this floor. Their gear is still here, and so are they."*
- Chronicle: *"Found {ghost_name}'s ghost on L{level}. I never met them in life. Now we're meeting now."*

If `ghost_name` matches the player's own name (multi-run case): add a special path:
- Chronicle: *"Met my own ghost. I had forgotten this floor was where I died last time."*

Also: add a T2 hint that gestures at the bones system:

> *"The dungeon does not let go of those who die in it. Sometimes their bodies are found by the next traveler. Sometimes their bodies find them first."*

## Notes

Bones is a NetHack-lineage feature with high mythic-register potential. The current treatment is the only piece of the bones system that's been left at "functional" rather than "chronicle-class."
