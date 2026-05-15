---
id: beauty-quirk-unlock-no-moment
dimension: beauty
severity: P3
title: First-quirk-unlock has no dedicated visual treatment — appears only in message log
status: open
systems: [quirk_unlock_notification, quirks_browse_screen, story_popup, message_log]
evidence:
  - src/quirk_system.py:1+ — quirk unlock emits `add_message` (verified via grep for `add_message` in this file showing 6 occurrences)
  - src/game_render.py:393-494 — `_draw_quirks_screen` is the only quirk-related rendering, browse-only
  - src/game_render.py:2368 — `_draw_story_popup` exists and is used for other moments-of-significance (boss defeats, dungeon entrance, exit)
  - beauty_screen_catalog.md#35
discovered: 2026-05-15
---

## The visual clash or inconsistency

The CONTEXT briefing lists ~80 named mythological/historical quirks (Prometheus, Odysseus, Buddha, Hypatia, Sisyphus, Athena, Loki, Thor, Beowulf, Shiva, etc.). Each unlocks via a specific behavior — these are designed as **discovery moments** in the meta-game. The player has been doing something specific over many runs; the game finally registers the pattern and grants them a named identity tied to a mythological figure.

The current handling of an unlock:
- `quirk_system.py` emits an `add_message` line in the message log (the standard `add_message` infrastructure — flagged by 6 grep hits across the file).
- The unlock entry appears in the `_draw_quirks_screen` browse view (`W` key) as "UNLOCKED" — but only if the player thinks to check.
- No popup, no story-popup, no full-screen flourish, no chime+visual combo for the moment of unlock.

Compare to the `_draw_story_popup` infrastructure (`game_render.py:2368`), which exists for *exactly this kind of moment* — significant narrative beats with overlay, panel, accent border, body text, and reward code. It's used for boss defeats, dungeon entrance, and game-ending exits. Quirks would fit naturally into the same framework: each unlock is a paragraph of mythological flavor describing the deed and granting the title.

A first-time player who unlocks Prometheus (or any other quirk) probably misses the message-log line entirely — they're busy doing the thing that triggered it. The most resonant meta-moment in the game is invisible.

## Where it surfaces

- **Quirk unlock event**: message log only.
- **Boss defeat event**: `_draw_story_popup` with full panel and accent border (`game_combat.py:587`).
- **Dungeon entrance event**: `_draw_story_popup` ("dungeon_entrance", `main.py:204`).
- **Exit events**: `_draw_story_popup` with reward codes.

The quirk unlock is a category mismatch: it's at the same emotional altitude as a boss defeat (or higher — quirks are the deepest meta-progression in the game), but it's rendered at the altitude of a generic combat log line.

## Suggested unification

Add a new `_STORY_CONTENT` entry per quirk (or a single templated entry that takes the quirk name + flavor text). On unlock, call `_show_story_popup('quirk_unlock_prometheus', STATE_PLAYER)` (or similar with templated content) before continuing the game.

Sketch of the popup data:
- Title: e.g., "PROMETHEUS"
- Accent: arcane purple (or per-quirk color)
- Lines: 3–5 short paragraphs in the chronicle voice. Something like:
  > *"You brought fire where there was none. Three times. The dungeon noticed."*
  > *"The world calls this Prometheus — the Firebearer. The chained one whose gift was theft."*
  > *"You have his thread now. Use it."*
- Code: none (this isn't a reward-code event, just a story beat).

The popup uses the existing `draw_dark_panel` chrome — no new primitive needed. The narrative copy is the heavy lift; the visual treatment slot is already built.

For the **quirks browse screen** (`W` key), the relationship to this finding is secondary — the browse screen is fine for what it is (modulo `beauty-rolled-inline-chrome`), but it's a *reference* screen, not a *moment* screen. The moment-of-unlock is the missing experience.

## Notes

P3 because the quirk *does* unlock — mechanically nothing is broken. The unlock just lacks ceremony. Adding ceremony costs one new state transition and ~80 short flavor paragraphs (or a templated single paragraph).

This finding spans (a) the quirk unlock code path (`quirk_system.py`), and (b) the story popup renderer (`game_render.py:2368`) — two existing systems that should be wired together but aren't.

Code work + writing work (the flavor copy). No new visual primitives.
