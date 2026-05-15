---
id: beauty-quiz-cards-vs-menu-rows
dimension: beauty
severity: P2
title: Quiz choice cards use modern button bevels — clash with every other selectable-item rendering
status: open
systems: [quiz_panel, menu_rows, choice_button_helper]
evidence:
  - src/game_render.py:1541-1551 — quiz cards rolled inline with shadow, `border_radius=7`, and `min(255, v+40)` top/left highlights
  - src/game_render.py:1555 — key hint is plain `font.render(f"[{i+1}]")` text
  - src/fantasy_ui.py:546-594 — `draw_choice_button` exists with ornate badge + parchment-style text — UNUSED
  - src/fantasy_ui.py:822-873 — `draw_menu` icon-row style (used by 12+ menus) uses solid bg + border_radius=6, no bevel
  - beauty_screen_catalog.md#6
discovered: 2026-05-15
---

## The visual clash or inconsistency

The quiz panel is the game's centerpiece — the player sees it on every combat round, every equip attempt, every cooking action. Its choice cards are rendered inline at `game_render.py:1541-1551`:

```
pygame.draw.rect(self.screen, (0, 0, 0), (cx+3, cy+3, cw, ch_height), border_radius=7)  # shadow
pygame.draw.rect(self.screen, bg_c, (cx, cy, cw, ch_height), border_radius=7)            # bg
pygame.draw.rect(self.screen, bdr_c, (cx, cy, cw, ch_height), 2, border_radius=7)        # border
bevel = tuple(min(255, v + 40) for v in bdr_c)
pygame.draw.line(self.screen, bevel, (cx+2, cy+1), (cx+cw-3, cy+1))  # top highlight
pygame.draw.line(self.screen, bevel, (cx+1, cy+2), (cx+1, cy+ch_height-3))  # left highlight
```

This is **modern flat-button-with-bevel** styling — drop shadow underneath, lightened top and left edges. The visual lineage is 2010s mobile-app buttons / Material Design cards, not medieval grimoire.

Compare to `draw_menu`'s row rendering (`fantasy_ui.py:825-873`): a single `pygame.draw.rect(surf, bg_col, ..., border_radius=6)` — flat, no bevel, no shadow. The row's highlighting comes from the row background color alone.

Compare to `fantasy_ui.py:546-594` — **a `draw_choice_button` helper already exists** with a parchment-styled badge, rune-stone-style key label area, and a parchment-light text color. It is **not used by `_draw_quiz`** despite being the obvious primitive. (No callers — `grep` finds zero references outside its definition.)

The result: the most-seen UI element in the game looks like it's from a different visual family than every menu the player ever opens.

## Where it surfaces

- **Quiz panel** (`game_render.py:1382`): 2×2 grid of beveled cards.
- **`draw_menu`** (~12+ menus): flat rows, no bevels.
- The selectable rows in **NPC dialog options** (`game_render.py:830-840` — phase `'options'`): rendered as plain text on the panel, no card chrome.
- The selectable rows in **Cow encounter options** (`game_render.py:773-780`): plain text on the panel.
- The selectable rows in **Mystery approach** (`game_render.py:131-133`): plain text.
- **The unused `draw_choice_button` helper**: would offer a third option (parchment badge + ornate frame) but is currently dead code.

Three different "this is a choice you can make" visual languages in the same game. The quiz is the loudest and the most often seen.

## Suggested unification

Two paths, ranked by ambition:

**Option A — Wire up `draw_choice_button`.** Replace the inline quiz card chrome with calls to `draw_choice_button`. The helper already handles `selected/correct/incorrect` states and the rune-stone key badge. Apply the same helper to NPC dialog options (`_draw_npc_encounter` phase `'options'`), cow options, and mystery prompts. Result: **one** way to render "a thing the player can pick by pressing 1–9", everywhere.

**Option B — Strip the bevels from the quiz.** Keep the quiz cards but match `draw_menu`'s flat rounded-rect style (drop the bevel + drop shadow). Less elaborate than Option A but achieves visual coherence.

Recommended: Option A. The `draw_choice_button` helper is already written, theme-correct, and currently unused. Wiring it up is a low-risk refactor that unifies multiple screens at once.

## Notes

The unused `draw_choice_button` is a red flag — it suggests an earlier polish pass intended to unify quiz styling and never landed. Reviving it is reclaiming intended-but-undelivered work, not new design.

Note that the quiz's beveled cards aren't *ugly* — they look fine in isolation. The problem is they don't look like siblings to anything else in the game. The clash is purely cross-screen.

Code-only fix.
