---
id: voice-special-room-message-energy
dimension: voice
severity: P3
title: Some special-room enter messages clash with chronicle voice (treasure zoo, beehive)
status: open
systems: [main.py (_SPECIAL_ROOM_MSGS), main.py (_ROOM_CHRONICLE)]
evidence:
  - src/main.py:1114 — "'zoo': ('Welcome to the treasure zoo! Sleeping creatures surround you!', 'danger')"
  - src/main.py:1116 — "'beehive': ('A low buzzing fills the air. You\\'ve disturbed a hive!', 'danger')"
  - src/main.py:1110 — "'treasury': ('You enter a treasure vault -- riches gleam in the darkness!', 'success')"
  - src/main.py:1119 — "'throne_room': ('An aura of ancient authority radiates from a throne.', 'info')"
  - src/main.py:1136 (chronicle for treasury) — "'treasury': 'Found a treasure vault. Gold everywhere. Someone wanted this hidden.'"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player enters a special room, the game fires both an `add_message()` and (for some rooms) a `_log_chronicle()`. The chronicle entries are in pitch-perfect voice — *"Stumbled into an underground graveyard. The dead are restless."* / *"Found a treasure vault. Gold everywhere. Someone wanted this hidden."* — but the matching add_message strings are uneven:

- `'zoo': "Welcome to the treasure zoo! Sleeping creatures surround you!"` — the "Welcome to X!" phrasing is NetHack-pastiche / amusement-park energy. Exclamation point bookends.
- `'beehive': "A low buzzing fills the air. You've disturbed a hive!"` — first sentence is in voice, second sentence loses it with the exclamation.
- `'treasury': "You enter a treasure vault -- riches gleam in the darkness!"` — exclamation point on a description.
- `'throne_room': "An aura of ancient authority radiates from a throne."` — perfect, no exclamation.

The contrast within the same dict tells two writers (or two moods) wrote different entries.

## Why it breaks the register

The chronicle voice and the message log are reading-adjacent surfaces. When the message log fires "Welcome to the treasure zoo!" and the chronicle (one panel over) fires "Found a treasure vault. Gold everywhere. Someone wanted this hidden.", the chronicle's voice is the better one and the message-log line is what the player will read first. The exclamation points are doing tutorial-narrator work that the room itself should be doing.

## Suggested rewrite direction

Drop exclamation points, let descriptions describe. The throne_room line is the in-house model. Examples:

- zoo: "Sleeping creatures fill the room. None of them have noticed you. Yet."
- beehive: "A low buzzing fills the air. The hive has noticed you."
- treasury: "Gold glitters along the walls. Someone wanted this hidden."
- monster_den: "The stench of creatures fills the air. You are not alone here."
- graveyard: "The air grows cold. Graves stretch before you in the dark."

Same length budget; no exclamation point doing emotional labor the description can carry on its own.

## Notes

Six lines to tune. Low priority but high frequency — these fire several times per run as the player explores.
