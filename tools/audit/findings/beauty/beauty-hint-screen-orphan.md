---
id: beauty-hint-screen-orphan
dimension: beauty
severity: P1
title: Recall Lore hint screen bypasses grimoire chrome — looks like a different game than story popups
status: open
systems: [hint_screen, story_popup, lore_screen, mystery_approach]
evidence:
  - src/game_render.py:3336-3404 — `_draw_hint_screen` uses raw `pygame.draw.rect(..., border_radius=10)` chrome
  - src/game_render.py:3354-3356 — `pygame.draw.rect(self.screen, (24,18,8), (bx,by,bw,bh), border_radius=10)` + `(160,130,60)` border + `(80,65,25)` inner stroke
  - src/game_render.py:2414 — `_draw_story_popup` correctly uses `draw_dark_panel(border_color=accent)`
  - src/fantasy_ui.py:278-316 — `draw_dark_panel` provides corner flourishes + mid-edge diamonds + inner double border
  - beauty_screen_catalog.md#27
discovered: 2026-05-15
---

## The visual clash or inconsistency

Recall Lore is the game's **central discovery mechanism** — the only way to learn about hidden systems. The hint screen is the atmospheric payoff for a successful lore chain. Per the CONTEXT briefing, hints are "Egyptian eye of blue faience mends what was torn. Patience is its method — the old gods do not hurry." — mythic, geek-dad register, the most important atmospheric moment in the run.

The render code (`game_render.py:3354-3356`) draws a plain rounded rectangle (`border_radius=10`) with one solid border and an inner stroke. No corner flourishes. No diamond mid-edge ornaments. No header bar with two-tone strip. No filigree.

Meanwhile, `_draw_story_popup` (`game_render.py:2414`) — which delivers narratively-similar mythological text — correctly uses `draw_dark_panel(border_color=accent)`, gets full corner-flourish + diamond ornament chrome from `fantasy_ui.py:278-316`, and feels like a grimoire artifact.

The most important atmospheric moment in the discovery loop is visually rendered as **the least grimoire screen in the game**.

## Where it surfaces

- **Hint screen (`STATE_HINT`)** vs. **Story popup (`STATE_STORY_POPUP`)**: identical lifecycle position (text overlay, dismissed by any key), nearly identical content type (mythological lore), but two completely different visual languages. The story popup wraps the player's victory over a boss in arcane-grimoire chrome; the lore-hint shows mythic memory recalls in a plain rounded box.
- **Hint screen** vs. **Mystery approach** (`_draw_mystery_approach`, `game_render.py:50-139`) — *both* use the same hand-rolled rounded-rect chrome (this finding spans them too), which means the "ornate" half of the game (story popups, NPC dialogs, character sheet) and the "plain rounded" half (hints, mystery, lore detail) are essentially two competing UI traditions inside the same game.
- **Hint screen** vs. **Lore screen** (`_draw_lore_screen`, `game_render.py:2808`) — both rolled inline, both *should* be grimoire but neither is. They at least look like each other.

## Suggested unification

Replace the hand-rolled chrome in `_draw_hint_screen` with `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar(text=f"RECALL LORE — {label}", text_color=FP.GOLD_BRIGHT)` + `draw_divider`. Then the lore "chain quality" stars indicator should probably move into the header subtitle position. Footer cooldown text should use `FP.HINT_TEXT`, not the current `(100,85,45)`.

This single change brings the most important atmospheric screen into the same family as story popups, character sheet, confirm-exit popups, and the entire `draw_menu` ecosystem.

For consistency, do the same to `_draw_lore_screen` and `_draw_mystery_approach` — they are the other two "rolled inline" screens that should be grimoire.

## Notes

This is P1 because Recall Lore is the **vehicle for the entire hidden-content discovery system** (~80 quirks, hidden characters, the Abyssal Shimmer ritual, the debug terminal). If the hint visually feels like a generic message box, the player will not register that they just unlocked a piece of mythic lore. The mechanic and the chrome are out of phase.

Code-only fix — no asset work needed.
