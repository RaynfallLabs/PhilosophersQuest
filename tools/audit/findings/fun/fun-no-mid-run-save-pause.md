---
id: fun-no-mid-run-save-pause
dimension: fun
severity: P3
title: A 3-4 hour run with no graceful pause point — kid-player session length doesn't match game length
status: open
systems: [save_system, session_length, audience_fit]
when_it_hits: "Any run extending past 90 minutes — the kid-player vs. session-length mismatch"
evidence:
  - src/save_system.py
  - src/main.py:1463-1472
  - fun_pacing_trace.md#tldr-pacing-summary
discovered: 2026-05-15
---

## The friction or flatness
Per the pacing trace, a successful full run (L1→L100→escape) takes **3-4+ hours of real-world time**. A kid's typical play session is 30-60 minutes. The game has save/load via `save_system.py` (the player can quit and resume), but:

1. There is **no natural pause point** in the game's pacing arc. Every meaningful beat (boss fight, mystery altar, NPC encounter, Recall Lore, Death chase) is part of a chain you can't graceful-exit from mid-action.
2. The save is **automatic, persistent, and tied to the player name** — but the game doesn't explicitly tell the player "this is a 4-hour commitment, but you can quit anytime and pick up later." A new player may assume the save is mid-session checkpoint only.
3. Permadeath is **absolute** — death deletes the save (`main.py:1466-1472`). Quitting between sessions is safe; dying mid-action is not. The play-test dynamic for a kid: they sit down for 45 minutes, they're mid-floor when bedtime arrives, they save and quit. Tomorrow they resume — but they may not remember which floor or what strategy they were on.

The mismatch between game-arc length and kid-session length is **structural**. A full run isn't completable in a single sitting for most kids, and the save system doesn't try to mitigate this with narrative bookmarks.

## When and how often it fires
- Every kid who plays the game past floor 20. The shorter sessions (deaths in the first hour) match kid attention spans well; the long sessions don't.
- The game's *peak* memory (Stone pickup, Death chase, Secret Victory) is in the 3rd-4th hour for a long run. Most kids will hit those moments split across 2-3 sessions.

## Suggested redirect
- **Save-and-quit chronicle entry**: when the player quits via save, write a chronicle entry "Closed my eyes. Resting before I go deeper." When they resume, "Opened my eyes again. Picked up the pack. Kept going." Bookmarks the session in the chronicle's own voice.
- **Session-recap on load**: when resuming, show a short "previously..." panel: last 5 chronicle entries, last 3 hints recalled, last enemy killed. Three seconds of UI before play resumes. Helps a kid who's been away for a day remember where they were.
- **Optional run-length toggle**: a "short run" mode that caps the dungeon at L50 with a smaller boss ladder. Keeps the *feel* of the game but in a 60-90 minute session. Maintain a "long run" mode as the canonical version.
- **Save points that explicitly bookmark for resuming**: after every boss kill (L20, L40, L60, L80, L100), prompt "Save and rest until tomorrow?" — a low-effort UX adjustment that fits the natural beat-points of the game.

## Notes
Spans save system + session length + audience fit. The game's intended audience is *kids* per CONTEXT, and the gap between a kid's attention envelope and a full run is real. This is one of the few findings where "make the game shorter" is on the table — but the answer is probably "make it easier to come back to" rather than "compress the experience." The Stone-bearing chase doesn't need to be shorter; it needs to be *narratable across sessions*.
