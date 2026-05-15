---
id: beauty-celebration-screen-orphan
dimension: beauty
severity: P2
title: MAX CHAIN celebration screen has no grimoire chrome — pure black + yellow wash, "PERFECT COMBO!" arcade text
status: open
systems: [quiz_celebration, victory_screen, death_screen]
evidence:
  - src/game_render.py:1588-1616 — `_draw_celebration` fills full screen with pure black + warm yellow wash
  - src/game_render.py:1613 — sub-line "PERFECT COMBO!" in `(180,255,180)`
  - src/game_render.py:2456 — `_draw_victory_screen` uses `draw_rune_circle` + `draw_candle_glow` + `draw_filigree_bar`
  - src/game_render.py:2551 — `_draw_death_screen` uses `draw_rune_circle` (burgundy + blood) + filigree
  - beauty_screen_catalog.md#7
discovered: 2026-05-15
---

## The visual clash or inconsistency

The quiz "MAX CHAIN" celebration (`_draw_celebration`) is a full-screen take-over moment — the quiz modal is dismissed and the screen is repainted. It is the **most-celebratory in-run visual** and one of the player's earliest sustained positive feedback events.

Current implementation (`game_render.py:1593-1616`):
- Pure black `(0,0,0)` background fill.
- Warm yellow `(80,55,0)` SRCALPHA pulsing wash over the whole screen.
- `qe.celebration_text` (typically "MAX CHAIN!" or similar) rendered in `font_xl` with shadow, color pulses between `(255, 200..255, 40..120)`.
- Sub-line "PERFECT COMBO!" in `(180,255,180)` (a green that doesn't match `FP.SUCCESS_TEXT`).

There is **no grimoire chrome**: no `draw_rune_circle`, no `draw_candle_glow`, no `draw_filigree_bar`, no `draw_panel`. Just text and a yellow wash on black.

The victory screen and death screen, by contrast, both use `draw_rune_circle` with counter-rotating layers + `draw_candle_glow` (victory) + filigree bars. They feel like *moments in a grimoire*. The MAX CHAIN celebration feels like a *moment in an arcade game*. The text "PERFECT COMBO!" is straight Street Fighter II — direct violation of the Cormac-McCarthy chronicle voice.

This is a BEAUTY finding (the visual chrome is missing) but it also indirectly violates the VOICE contract — the celebration uses arcade-game phrasing that's inconsistent with the rest of the player-facing text.

## Where it surfaces

- **MAX CHAIN celebration** (`STATE_QUIZ` celebrating): no grimoire chrome, "PERFECT COMBO!" arcade copy.
- **Victory screen**: rune circles + candle glow + filigree bars; celebratory but grimoire.
- **Death screen**: rune circles (burgundy/blood) + filigree bars; somber but grimoire.

The celebration is the only screen in the game's "big emotional moments" trio that breaks the visual language.

## Suggested unification

Replace `_draw_celebration` with a grimoire-compatible celebration:

1. Use `draw_overlay(190, (12, 10, 0))` (same warm-tinted overlay as the victory screen).
2. Use `draw_rune_circle(cx, cy, 200, (*FP.GOLD_BRIGHT, 140), t, 12)` for an animated golden rune ring.
3. Use `draw_candle_glow(cx, cy, intensity=pulse)` for the warm pulse.
4. Use `draw_filigree_bar` above and below the headline text.
5. Render the headline with `draw_glow_text` (already in `fantasy_ui.py:421`) in `FP.GOLD_BRIGHT` with `FP.GOLD` glow.
6. Replace "PERFECT COMBO!" with something matching the game's voice — e.g., simply *"the chain holds."* or *"unbroken."* — short, McCarthy-register, no exclamation.

The visual change makes the celebration feel like a small victory-screen — appropriate for a max chain, scaled down from the run-ending victory.

## Notes

The sub-line copy fix is technically a VOICE finding too, but since the chrome and copy are co-rendered in `_draw_celebration`, fixing them together is one edit.

A side effect of this change: the celebration becomes shorter visually and more atmospheric — likely a net improvement to the game's "earned through reading" identity. The current arcade-victory framing implies "you scored points!" but the game's reward model is "you proved knowledge", which is a different feeling.

Code-only fix. No new primitives needed.
