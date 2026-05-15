---
id: beauty-missing-fonts
dimension: beauty
severity: P1
title: Grimoire TTF fonts are not shipped — title/heading/gothic/italic silently fall back to system fonts
status: open
systems: [welcome_screen, all_modals, quiz_panel, victory_screen, death_screen]
evidence:
  - src/fantasy_ui.py:96 — `_FONT_DIR = data_path('assets', 'fonts')`
  - src/fantasy_ui.py:100-107 — `_ROLE_FILES` expects `Cinzel-Bold.ttf`, `Cinzel-Regular.ttf`, `IMFellEnglish-Regular.ttf`, `UnifrakturMaguntia.ttf`, `IMFellEnglish-Italic.ttf`
  - src/fantasy_ui.py:140-147 — fallback path: `pygame.font.SysFont('garamond,palatino linotype,palatino,georgia,book antiqua,times new roman,consolas')`
  - assets/ directory listing — no `fonts/` subdirectory exists
  - beauty_screen_catalog.md (preface)
discovered: 2026-05-15
---

## The visual clash or inconsistency

The "arcane grimoire" theme depends on three TTF families: **Cinzel** (display serif), **IM Fell English** (body italic), and **UnifrakturMaguntia** (blackletter gothic). The font loader `get_font('title' | 'heading' | 'gothic' | 'italic', ...)` looks for these TTFs in `assets/fonts/`. The directory does not exist in the repo (no `.ttf` files anywhere under `assets/`). The loader's `try/except` and `os.path.exists` checks (`fantasy_ui.py:141`) silently fall back to `pygame.font.SysFont(_FALLBACK_FAMILIES, ...)`, which picks the first installed family from `garamond, palatino linotype, palatino, georgia, book antiqua, times new roman, consolas`.

On any machine without Garamond installed (which is most machines — Garamond is not a default Windows font), the title bar of every screen — Welcome "PHILOSOPHER'S QUEST", panel headers "EQUIP / UNEQUIP", "RECALL LORE", "YOU HAVE DIED" — falls through to Palatino, Georgia, or eventually Times. The "arcane grimoire" type identity is invisible to most players.

This is inferred from code (no rendering capability), but the directory absence is verified.

## Where it surfaces

- **Welcome screen** title banner (`welcome_screen.py:633` — `font_xl = get_font('title', 52, bold=True)`, `font_lg = get_font('heading', 32)`).
- **Every modal header** rendered via `draw_header_bar` (used by 20+ screens). The header text font is the modal's `font_md` or `font_lg` — usually `get_font('heading', 20)` or `get_font('title', 24)`.
- **Victory screen** title "VICTORY!" (`game_render.py:2472`), `font_xl`.
- **Death screen** title "YOU HAVE DIED" (`game_render.py:2578`), `font_xl`.
- **Quiz panel** header text (`game_render.py:1448` — `font=self.font_md`).
- **Story popups** title (`game_render.py:2422` — `font_lg`).
- **Character creation** badge "[*] SECRET BUILD ACTIVE!" (`welcome_screen.py:664`).
- **Study mode** title "STUDY MODE" (`study_mode.py:147`).

Every "look" the player most associates with brand identity — the title and the death screen — runs through these missing fonts.

## Suggested unification

Either:
1. **Ship the TTFs.** Download the three font families (all freely licensed: Cinzel SIL OFL, IM Fell English SIL OFL, UnifrakturMaguntia SIL OFL) and place them in `assets/fonts/`. Update `MANIFEST.in` / packaging if needed. This is the lowest-disruption fix.
2. **Or, narrow the fallback families to widely-available fonts** that are reliably grimoire-feeling (e.g., `book antiqua, palatino, georgia` — drop Garamond from primary and put it after Palatino since Palatino ships with Windows since Vista). Then test the fallback chain explicitly.

Either way: add an integration test that asserts `pygame.font.Font(path)` actually loaded a TTF (not the system fallback) for `role='title'`. Currently the fallback is silent.

## Notes

This blocks evaluating most other BEAUTY findings — until the title font is actually displaying as Cinzel (or whatever), claims like "the title looks medieval" cannot be verified.
