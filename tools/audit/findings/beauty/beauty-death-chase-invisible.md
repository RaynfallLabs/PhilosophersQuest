---
id: beauty-death-chase-invisible
dimension: beauty
severity: P1
title: Death-chase atmosphere is text-only — sidebar, message log chrome, and map all unchanged
status: open
systems: [dungeon_view, sidebar, message_log, map_renderer]
evidence:
  - src/game_render.py:1044-1052 — Death's tile gets a pale spectral pulse (RGB tweak per turn)
  - src/main.py:1408-1419 — `_death_proximity_warning` only emits `add_message` lines ("Death looms over you -- MOVE!", "Death draws near.")
  - src/main.py:1285-1310 — speed-tier transitions emit messages ("Death quickens. The scraping is faster now."), no visual effect
  - src/ui.py:78-377 — `Sidebar.draw` has no death-pursuit hook; no special indicator when `death_pursues=True`
  - src/ui.py:51-75 — `MessageLog.draw` has no death-pursuit hook; fades messages normally
  - beauty_screen_catalog.md#3
  - beauty_screen_catalog.md#5
  - beauty_screen_catalog.md#25 (consistency-matrix clash 9)
discovered: 2026-05-15
---

## The visual clash or inconsistency

Per the CONTEXT briefing, Death-chase is Act III of the game: "the moment the player ascends from L100 carrying the Stone, `death_pursues = True` and a `DeathMonster` instance spawns... Atmospheric messages at each tier ('Death quickens. The scraping is faster now.')". The chronicle voice for this act is explicit: *"Something is following me. I felt it before I saw it. Death itself. I need to run."*

The visual translation of this section into the rendered game:
- **Map renderer:** Death's own tile pulses pale-white (`game_render.py:1048-1052` — `r=200+55*pulse, g=200+55*pulse, b=255`). Everything else on the map looks identical to a normal floor.
- **Sidebar:** Nothing changes. No new indicator. The "Lore" / "Prayer" / "Hunger" status lines stay where they are. There is no `[Death Pursues]` badge, no chase-distance display, no countdown of Death's current speed tier.
- **Message log:** Atmospheric text appears as one more `add_message` call indistinguishable from "You see a corpse." or "You picked up gold." It uses `'danger'` tag color (`FP.BLOOD = (200,18,18)`), but the log background, font, and entry style are unchanged.
- **Map vignette / overlay:** No effect. The dungeon during the chase looks identical to the dungeon during a quiet exploration turn.
- **Audio:** out of scope for BEAUTY but worth noting — no sound system hook for `death_pursues` was found.

The narrative *promises* dread; the rendered game delivers a pale tile and some message-log lines. The most cinematic moment in the game is the visually flattest.

## Where it surfaces

Three systems should be carrying the atmospheric load and aren't:

1. **Sidebar (`Sidebar.draw`):** When `death_pursues=True`, the top of the sidebar should pull "Death" up to a maximum-urgency indicator — above HP/SP/MP. Suggested: `[DEATH PURSUES]` in `FP.BLOOD` at the very top, with current speed multiplier (`50% / 75% / 100% / 125%`) underneath in `FP.BURGUNDY_MID`. The visual hierarchy guideline already says "most-urgent at top". Death pursuing is the most urgent possible state.
2. **Map / dungeon view:** When `death_pursues=True` and Death is in FOV within (say) 6 tiles, the screen should pick up a slow red vignette (subtle SRCALPHA edge tint, similar to the death-screen background `(50,0,0)`). When Death is within 3 tiles, the vignette intensifies. This is mood; it can be very subtle.
3. **Message log:** The "Death" prefix in any Death-pursuit message should render in `font_bold` with a leading sigil, distinguishing it from generic combat danger lines.

## Suggested unification

Add a `_draw_death_pursuit_atmosphere` hook in `game_render.py`, called from `render()` after the map draws and before the sidebar draws. It should:
- Compute `dist = abs(dm.x - player.x) + abs(dm.y - player.y)` if `death_pursues and death_monster`.
- Apply a screen-tint overlay: 0 alpha at `dist > 12`, ramping to `alpha=40` at `dist <= 3`, with a slow pulse modulated by `turn_count`.
- The tint color comes from `FP.BURGUNDY_DARK` (existing palette entry).

Add a top-priority indicator to `Sidebar`: a new `_death_indicator` section drawn *before* `_vitals` whenever `death_pursues` is true. It should show the speed tier (using `game.death_monster.speed` or similar) and pulse subtly.

Both fixes are code-only — no new assets.

## Notes

This is P1 because Death-chase is the game's tentpole experience (the briefing places it on par with the boss fight). When the briefing says "When Death is 3 tiles away, the screen should *feel* different" — the code does not currently make it feel different. Only the message-log lines change.

This finding spans the sidebar (Screen 3), the map renderer (Screen 5), the message log (Screen 4), and the *absence* of a chase-mode overlay. It is a holistic gap, not a single-screen polish.
