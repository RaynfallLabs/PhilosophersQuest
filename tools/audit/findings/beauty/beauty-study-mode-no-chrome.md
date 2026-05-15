---
id: beauty-study-mode-no-chrome
dimension: beauty
severity: P2
title: Standalone Study Mode has no panel chrome — bare midnight fill with rounded-rect rows
status: open
systems: [study_mode_standalone, study_journal_ingame, welcome_screen]
evidence:
  - src/study_mode.py:135 — `self.screen.fill(FP.MIDNIGHT)` — full-screen midnight, no overlay or panel
  - src/study_mode.py:146-186 — `_draw_subject_picker` and `_draw_tier_picker` use raw `pygame.Rect` + `pygame.draw.rect(..., border_radius=4)`
  - src/study_mode.py:188-217 — `_draw_quiz` renders question and choices as bare text on midnight
  - src/study_mode.py:219-256 — `_draw_result` is similar
  - src/game_render.py:2656 — in-game study journal `_draw_study_journal` uses `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar`
  - src/welcome_screen.py:381 — F3 from welcome screen enters standalone study mode
  - beauty_screen_catalog.md#26
discovered: 2026-05-15
---

## The visual clash or inconsistency

The Welcome screen advertises **F3 study mode** as one of three top-level options (alongside ENTER to play and ESC to quit, line 669). When the player presses F3, they leave the grimoire-styled welcome screen and enter `study_mode.py` — which fills the screen with bare `FP.MIDNIGHT` and renders questions and choices as plain text on that fill.

There is no `draw_dark_panel`, no `draw_header_bar`, no `draw_overlay`, no flourishes. The selection highlight is a `pygame.Rect` + `pygame.draw.rect(..., border_radius=4)`. The result is a screen that looks like a quick prototype next to every other screen in the game.

Compare this to the **in-game study journal** (`;` key during play, `_draw_study_journal` at `game_render.py:2656`) — same gameplay function (review questions / study) — which uses `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar(text="STUDY JOURNAL")` + the rest of the grimoire chrome.

Two render paths for the same conceptual feature, with completely different visual fidelity. The path the player gets to from the welcome screen (the first impression of "study") is the lower-quality one. The path they get to once they're playing is grimoire-correct.

## Where it surfaces

- **Welcome screen → F3**: enters bare-fill study mode.
- **In-game `;` key during play**: enters draw_dark_panel-wrapped study journal.
- **In-game `R` review after death**: another draw_dark_panel-wrapped review screen.

The two in-game screens are siblings; the standalone is the orphan.

## Suggested unification

Refactor `study_mode.py` to use the grimoire primitives. Specifically:

1. Wrap each phase's content in `draw_dark_panel(border_color=FP.GOLD)` centered on the screen. Use `draw_overlay(190)` underneath if there's a background (or simply fill with `FP.MIDNIGHT` and skip the overlay since there's no underlying game state).
2. Use `draw_header_bar(text="STUDY MODE — SUBJECT", text_color=FP.GOLD_BRIGHT)` for the subject picker; same pattern for tier picker; the `text` changes to e.g. `"STUDY: GEOGRAPHY — TIER 3"` during the quiz.
3. Replace the inline subject palette (`study_mode.py:18-31`) with `FP.SUBJECT` (already defined at `fantasy_ui.py:79-90`).
4. Replace the rounded-rect row selection (`study_mode.py:155-157`) with `draw_choice_button` (`fantasy_ui.py:546`) — the helper already exists, ornate rune-stone-style, perfect for "this is a selectable option".
5. Use `FP.PARCHMENT_LIGHT` for question text, `FP.BODY_TEXT` for choices, `FP.SUCCESS_TEXT`/`FP.DANGER_TEXT` for correct/incorrect results. Already used in `_draw_result` (line 224, 226), so partial alignment exists.

After refactor, study mode looks like a sibling of every other modal in the game — and an extension of the welcome screen's chrome rather than a regression away from it.

## Notes

This is P2 because (a) it's a player-facing screen the welcome screen explicitly directs to, and (b) it's the only "first-impression" feature path that breaks the visual contract. The in-game version proves the team knows how to render this content correctly — the bug is that two copies exist and only one was polished.

Pure code refactor. No new assets needed.
