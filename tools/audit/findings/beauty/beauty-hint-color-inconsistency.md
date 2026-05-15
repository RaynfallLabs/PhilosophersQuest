---
id: beauty-hint-color-inconsistency
dimension: beauty
severity: P3
title: "Press X to close" footer hint uses five different colors across screens
status: open
systems: [hint_screen, lore_screen, npc_dialog, quirks_screen, encyclopedia_detail, story_popup, victory_screen, death_screen]
evidence:
  - src/fantasy_ui.py:72 — `FP.HINT_TEXT = (170, 165, 215)` — the canonical hint color
  - src/game_render.py:3404 — `_draw_hint_screen` hint footer in `(100, 85, 45)`
  - src/game_render.py:3028 — `_draw_lore_screen` hint footer in `(80, 80, 100)`
  - src/game_render.py:823 — `_draw_npc_encounter` footer in `(120, 120, 120)`
  - src/game_render.py:493 — `_draw_quirks_screen` footer in `(90, 80, 120)`
  - src/game_render.py:3289 — `_draw_encyclopedia` entry-detail hint in `FP.HINT_TEXT` (correct)
  - src/game_render.py:2452 — `_draw_story_popup` footer in `FP.HINT_TEXT` (correct)
  - src/game_render.py:2548 — `_draw_victory_screen` hint in `FP.HINT_TEXT` (correct)
discovered: 2026-05-15
---

## The visual clash or inconsistency

Every modal in the game has a "Press X to close / continue" hint at the bottom. Across the codebase, this hint is rendered in **at least five different colors**:

1. `FP.HINT_TEXT (170, 165, 215)` — the centralized definition. Used by victory, death, story popup, encyclopedia detail, character sheet, help screen, confirm-exit, abandon, drop-gold input, study journal, cow encounter (some phases). This is the canonical color.
2. `(100, 85, 45)` — used by `_draw_hint_screen` footer (Recall Lore cooldown notice).
3. `(80, 80, 100)` — used by `_draw_lore_screen` close-prompt.
4. `(120, 120, 120)` — used by `_draw_npc_encounter` "Press ENTER to continue" footer (multiple phases — `game_render.py:823, 845, 873, 882`).
5. `(90, 80, 120)` — used by `_draw_quirks_screen` "Up/Down: scroll ... ESC: close" footer.

Plus minor variants:
- `(80, 80, 100)` and `(0, 100, 50)` (hack-reality) and `(100, 80, 30)` (hint screen separator line).

The player's eye is trained over many screens to look for the hint at the bottom of a modal. When that hint is `FP.HINT_TEXT` (lavender-grey), they know "this is where to look for what to press". When that same lifecycle slot is `(120, 120, 120)` neutral grey or `(100, 85, 45)` warm-amber, the hierarchy breaks subtly. The eye doesn't lock onto the hint location as quickly.

## Where it surfaces

This finding spans every screen with a "press X" footer. The clearest examples of drift:

- **Hint screen** (the Recall Lore atmospheric moment): the hint footer is in a warm amber that blends with the parchment-warm panel background. Hard to spot.
- **NPC dialog** (`_draw_npc_encounter`): "Press ENTER to continue" is in `(120, 120, 120)` — a flat neutral grey that doesn't match anything else in the screen's grimoire chrome.
- **Quirks screen**: footer in dim purple-grey `(90, 80, 120)` — closer to FP.HINT_TEXT than most, but still inline.

By comparison, screens that correctly use `FP.HINT_TEXT` (victory, death, story popup) feel cohesive — the hint always sits in the same lavender-grey footer slot.

## Suggested unification

Replace every inline footer-hint color with `FP.HINT_TEXT`. Five lines of edit across `game_render.py`:

```
src/game_render.py:3404 — (100, 85, 45) → FP.HINT_TEXT
src/game_render.py:3028 — (80, 80, 100) → FP.HINT_TEXT
src/game_render.py:823  — (120, 120, 120) → FP.HINT_TEXT  (and 845, 873, 882)
src/game_render.py:493  — (90, 80, 120) → FP.HINT_TEXT
```

If a particular screen needs a *dimmer* hint (e.g., to not compete with strong content above), introduce `FP.HINT_TEXT_DIM` once in `fantasy_ui.py` and use it consistently rather than each screen rolling its own dim grey.

## Notes

P3 because no single instance breaks the experience — but cumulatively the hint color drift undermines the "everything is in a single visual family" feeling. It also feeds into `beauty-palette-bypass` (the broader inline-RGB-literals finding) — these footer hints are the cleanest, smallest examples of the structural issue.

Trivial code edit.
