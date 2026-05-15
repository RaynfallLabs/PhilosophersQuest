---
id: voice-default-welcome-collapses
dimension: voice
severity: P2
title: Default greeting collapses to "Welcome, {name}!" while secret-build greetings are pitch-perfect
status: open
systems: [main.py, welcome_screen.py]
evidence:
  - src/main.py:271 — "self.add_message(f\"Welcome, {self.player_name}!\", 'success')"
  - src/main.py:272 — "self.add_message(\"Find the Philosopher's Stone and escape!\", 'info')"
  - src/welcome_screen.py:81 — "Diogenes enters the dungeon. He needs nothing. He wants nothing. He is still going to die."
  - src/welcome_screen.py:62 — "Nietzsche stares into the dungeon. The dungeon stares back."
  - src/main.py:274 (chronicle, fires moments later) — "Descended into the dungeon. The air smells like dust and old stone. The Stone is somewhere below. I need to find it and get back out."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The flow when a new player starts:
1. Story popup `'dungeon_entrance'` plays — pitch-perfect mythic register about Amber dying and the Stone below.
2. Popup is dismissed.
3. Two messages appear in the message log: *"Welcome, Brandon!"* and *"Find the Philosopher's Stone and escape!"*
4. The chronicle entry fires: *"Descended into the dungeon. The air smells like dust and old stone..."*

Line 3 is in a completely different voice than lines 1, 2, and 4. The exclamation points, the second-person imperative ("Find the X and escape!"), the parade-of-Welcome-to-Game-X register — this is the only place in the entire game that sounds like a 2007 mobile RPG tutorial.

Worse: if the player happened to enter a name in `SECRET_BUILDS`, they get a beautiful character portrait greeting instead — *"Diogenes enters the dungeon. He needs nothing. He wants nothing. He is still going to die."* The contrast tells the player they got "the default version" of the game. They got the lesser welcome.

## Why it breaks the register

The game's audience is the developer's kids (CONTEXT.md). A child typing "Sarah" into the name prompt gets "Welcome, Sarah!" with an exclamation point; a child typing "ash williams" gets "Good. Bad. I'm the guy with the gun." This is an *inversion* of what should happen — the named main quest character (their own name) deserves the warmer, more mythic welcome, not the Easter egg.

The chronicle entry that fires immediately after (*"Descended into the dungeon. The air smells like dust and old stone..."*) demonstrates exactly the line that should be the default greeting. It's already written. It's the voice.

## Suggested rewrite direction

Replace the two lines with a single chronicle-voice greeting and let the chronicle entry carry the rest. Something like:

```python
self.add_message(
    f"{self.player_name} steps into the dark. The dungeon does not greet them.",
    'success'
)
```

Or fully omit the message-log greeting and lean entirely on the chronicle + dungeon_entrance popup. The current Line 272 (*"Find the Philosopher's Stone and escape!"*) is purely instructional — it duplicates what the popup just said in a flatter tone.

## Notes

This is the first text a new player reads after the dungeon-entrance popup. The voice they imprint on at this moment shapes their expectation for the rest of the run. Fixing this is a one-line change that affects every default-named playthrough.
