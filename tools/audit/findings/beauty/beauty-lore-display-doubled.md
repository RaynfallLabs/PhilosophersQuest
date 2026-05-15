---
id: beauty-lore-display-doubled
dimension: beauty
severity: P2
title: Item/monster lore is rendered by two separate code paths with two coincidentally-matching color schemes
status: open
systems: [lore_screen, encyclopedia_detail, philosophers_shard_identify, harvest_corpse]
evidence:
  - src/game_render.py:2808-3029 — `_draw_lore_screen` (item-identify + corpse-bestiary)
  - src/game_render.py:3198-3291 — `_draw_encyclopedia` entry detail branch
  - src/game_render.py:2832-2836 — `_draw_lore_screen` item-lore colors: `border (80,120,200)`, `inner (40,60,120)`, `title (160,210,255)`, `stat (180,200,230)`, `lore (200,215,240)`
  - src/game_render.py:3267-3285 — `_draw_encyclopedia` entry-detail colors: `stat_col=(180,200,230)`, divider `(40,60,120)`, header `(80,120,200)`, lore `(200,215,240)`
  - beauty_screen_catalog.md#28
  - beauty_screen_catalog.md#29
discovered: 2026-05-15
---

## The visual clash or inconsistency

The game has **two separate code paths** that render an "item/monster card with stats + LORE section":

**Path 1 — `_draw_lore_screen`** (`game_render.py:2808`)
Triggered when the player identifies an item via the Philosopher's Shard, or harvests/examines a corpse with `H`/`I`. Shows item stats or monster bestiary entry. Renders inside a hand-rolled rounded-rect panel.

**Path 2 — `_draw_encyclopedia` entry detail** (`game_render.py:3198`)
Triggered when the player opens the encyclopedia (`B` key) and selects a specific entry. Same kind of content — name + stats + LORE. Renders inside a `draw_dark_panel`.

The two paths use **the exact same color palette** for item-class lore: border `(80, 120, 200)`, inner stroke `(40, 60, 120)`, stat text `(180, 200, 230)`, header `(80, 120, 200)`, body lore `(200, 215, 240)`. They look identical when rendered (modulo the panel chrome — Path 1 is rolled inline, Path 2 uses `draw_dark_panel`).

This is **coincidental DRY**. Two render functions, neither using `FP` palette entries, both rolling inline tuples. If anyone edits one set of colors, the other will silently drift away. They are essentially copy-paste duplicates.

Additionally:
- Path 1 has a *separate* branch for corpses (`game_render.py:2825-2829`) with a *warm amber* palette `(160,120,40)` / `(80,60,20)` / etc. — different from item-lore blue.
- Path 2 (encyclopedia) uses the cool-blue palette for **everything** including corpse-bestiary entries — losing the item-vs-monster color distinction that Path 1 makes.

So the encyclopedia displays a dragon's bestiary entry in cool-blue, but `_draw_lore_screen` displays the *exact same dragon's lore* in warm-amber. Two different color schemes for two different paths into the same content.

## Where it surfaces

- **`_draw_lore_screen` corpse path** (warm amber): triggered by harvesting a corpse, examining a corpse, or identifying a monster via lore.
- **`_draw_lore_screen` item path** (cool blue): triggered by Philosopher's Shard identification.
- **`_draw_encyclopedia` entry detail** (cool blue for all): triggered by the encyclopedia `B` menu.
- A player who reads the Dragon's lore via `H` (harvest, warm) and then opens the encyclopedia and reads the same dragon's bestiary entry (cool) sees two completely different color treatments for the *same paragraph of text*.

## Suggested unification

Three changes, in order of importance:

1. **Extract the lore-display chrome into a shared primitive.** Both render functions are doing the same job — they should share rendering code. Suggested: a `draw_lore_card(surf, rect, title, stats, lore, is_corpse=False, border=...)` helper in `fantasy_ui.py` or a new `lore_view.py` module. Both `_draw_lore_screen` and `_draw_encyclopedia` entry-detail call it.
2. **Promote the inline color set to FP entries** — `FP.LORE_BLUE`, `FP.LORE_BLUE_DIM`, `FP.LORE_AMBER`, `FP.LORE_AMBER_DIM` (or use existing entries if close enough — `FP.GOLD_PALE` is close to the amber title color, `FP.ARCANE_BRIGHT` could play the blue role).
3. **Pick one rule for corpse-vs-item color distinction and apply consistently.** Either:
   - Both paths render corpses warm-amber, items cool-blue. (Encyclopedia entry detail branches on `category == 'bestiary'`.)
   - Both paths render everything the same color (drop the warm-amber/cool-blue distinction). Less ambitious; loses the "monsters feel different from items" signal.

Either choice is fine — but the current state of "one path branches, the other doesn't" is incoherent.

## Notes

This is P2 because (a) two separate code paths render the most-loved content type in the game (the lore text — the discovery payoff), and (b) the duplication risks silent drift. A future "make the lore screen feel more grimoire" pass that updates only one path will fragment the visual identity.

The shared primitive also pays dividends if/when the team wants to make the lore card feel more grimoire (`beauty-rolled-inline-chrome` finding) — they can refactor once instead of twice.

Code-only refactor.
