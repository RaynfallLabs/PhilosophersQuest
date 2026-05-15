---
id: beauty-rolled-inline-chrome
dimension: beauty
severity: P2
title: Five high-emotion screens roll their own panel chrome instead of using `draw_dark_panel`
status: open
systems: [hint_screen, lore_screen, mystery_approach, quirks_screen, welcome_leaderboard, welcome_god_prompt]
evidence:
  - src/game_render.py:3354-3356 — `_draw_hint_screen` raw `pygame.draw.rect(..., border_radius=10)`
  - src/game_render.py:2824-2839 — `_draw_lore_screen` raw rounded rect chrome
  - src/game_render.py:71-74 — `_draw_mystery_approach` raw rounded rect chrome
  - src/game_render.py:407-409 — `_draw_quirks_screen` raw rounded rect chrome
  - src/welcome_screen.py:705-708 — `_draw_leaderboard` raw rounded rect with `border_radius=6`
  - src/welcome_screen.py:417-420 — `_draw_god_prompt` raw `pygame.draw.rect`, no border_radius
  - src/fantasy_ui.py:278-316 — the canonical `draw_dark_panel` provides flourishes these screens lack
  - beauty_screen_catalog.md — Consistency Matrix
discovered: 2026-05-15
---

## The visual clash or inconsistency

The game has **two competing UI chrome traditions** running in parallel:

**Tradition A — Grimoire canon (`draw_dark_panel`):**
- Used by ~25 screens including all `draw_menu` menus, all confirm popups, story popup, NPC dialog, cow encounter, judgment, character sheet, help screen, review-missed, study-journal.
- Visual signature: midnight bg, gold double border (outer 2px + inner 1px), L-shaped corner flourishes with diamond caps (`_corner_flourish` `fantasy_ui.py:319`), mid-edge diamond ornaments (`_edge_diamond` `fantasy_ui.py:338`), optional `draw_header_bar` two-tone strip.

**Tradition B — Rolled-inline rounded rect:**
- Used by: hint screen, lore screen, mystery approach, quirks browse, welcome leaderboard, welcome god-prompt popup, welcome all-time top-100, hack reality (intentional exception).
- Visual signature: solid background rect + `border_radius=6..10` + one solid border + one inner stroke. No flourishes, no diamonds, no header bar.

These two traditions look like they're from different games. Tradition A is medieval / illuminated-manuscript. Tradition B is **2010s flat-card design** (rounded corners + flat fills + thin border). The hint screen and quirk screen are the clearest examples — their visual language is closer to a modern productivity app than to a fantasy roguelike.

This finding aggregates the chrome inconsistency across six screens. Each individually could be a P3, but together they constitute ~20% of the game's modal surface and include three high-emotion moments (Recall Lore hint, quirk unlock, mystery encounter). Separating the most-important ones (hint screen → `beauty-hint-screen-orphan`) leaves this finding to cover the residual cluster.

## Where it surfaces

The clash is most jarring when the player moves between screens:

- **Mystery approach → Mystery quiz → Mystery outcome**: the prompt uses Tradition B (rounded), the quiz uses Tradition A (grimoire), the outcome story popup uses Tradition A. The "investigate altar" decision is made in flat-card chrome; everything else around it is grimoire.
- **Recall Lore → Hint display**: the lore quiz is the standard quiz panel (Tradition A). The resulting hint is Tradition B. Player flow goes grimoire → flat-card.
- **Welcome screen**: title banner uses Tradition A (`draw_panel`). Leaderboard panel uses Tradition B. Same screen, two chromes.
- **`@` character sheet (Tradition A) vs. `W` quirks screen (Tradition B)**: adjacent menu commands, opposite visual languages.

## Suggested unification

Refactor these six screens to use `draw_dark_panel` + `draw_header_bar` + `draw_divider`:

1. `_draw_hint_screen` — covered in detail by `beauty-hint-screen-orphan` (P1).
2. `_draw_lore_screen` — replace inline rounded chrome with `draw_dark_panel(border_color=<corpse_amber or item_blue>)` + `draw_header_bar(text=f"{name.upper()} -- {category}", text_color=...)`.
3. `_draw_mystery_approach` — replace with `draw_dark_panel(border_color=altar.color)` + `draw_header_bar` + the existing Y/N prompt block.
4. `_draw_quirks_screen` — replace with `draw_dark_panel(border_color=FP.ARCANE_BRIGHT)` + `draw_header_bar(text=f"QUIRKS ({n}/{total})", text_color=FP.ARCANE_BRIGHT)`. The progress bars inside the panel are fine to keep as-is.
5. `_draw_leaderboard` (welcome) — could keep its compact layout but adopt `draw_dark_panel` chrome with reduced flourishes (the welcome screen has multiple chrome elements already; adding too many flourishes might look busy).
6. `_draw_god_prompt` (welcome) — small confirm popup; should use the same `draw_dark_panel` style as `_draw_confirm_exit`, `_draw_exit_quest`, `_draw_chicken`.

A unified rule for future work: **any time a screen needs a modal box, the answer is `draw_dark_panel`.** Exceptions require an explicit comment justifying the deviation (e.g., `# Hack Reality is the cyberpunk easter-egg screen — terminal-aesthetic intentional`).

## Notes

The hack-reality / XYZZY screen (`_draw_hack_reality_screen`) is a *deliberate* break — the hidden backtick terminal is meant to be cyberpunk, not grimoire. That's fine. The others are unintended drift.

Code-only fix. No new primitives needed; `draw_dark_panel` is fully sufficient.
