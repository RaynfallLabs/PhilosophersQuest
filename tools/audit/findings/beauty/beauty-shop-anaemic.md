---
id: beauty-shop-anaemic
dimension: beauty
severity: P3
title: Shop screen has no panel chrome — only filigree bars on a dim overlay
status: open
systems: [shop, story_popup, npc_encounter]
evidence:
  - src/game_render.py:3093-3138 — `_draw_shop` uses `draw_overlay` + two `draw_filigree_bar` calls, no `draw_dark_panel`
  - src/game_render.py:2368 — `_draw_story_popup` (similar modal use case) uses `draw_dark_panel` + filigree
  - src/game_render.py:792 — `_draw_npc_encounter` (also a dialog modal) uses `draw_dark_panel`
  - beauty_screen_catalog.md#38
discovered: 2026-05-15
---

## The visual clash or inconsistency

The merchant shop (`Y` key) is a full overlay modal where the player browses goods, navigates with arrows, and presses ENTER to buy. It is functionally identical to a menu, semantically identical to an NPC dialog.

The current implementation (`game_render.py:3094-3138`):
1. `draw_overlay(190, (10, 8, 2))` — dims the screen.
2. `draw_filigree_bar` above and below the title.
3. Title text "TRAVELLING MERCHANT" rendered with `centered_text` + shadow.
4. Player gold displayed as plain text below.
5. Item list rendered as bare `font_md.render(...)` lines, with a translucent `(60,50,20,180)` SRCALPHA highlight rect on the selected row.
6. Bottom filigree + hint text.

**No panel.** No `draw_dark_panel`. No `draw_header_bar`. No outer border. The shop floats on the dim overlay with only filigree-bar accents above and below the title text. Visually it looks like an unfinished mockup compared to (e.g.) the cow encounter or the NPC dialog, which use full `draw_dark_panel` chrome.

The Travelling Merchant is also a *narrative character* — they "haggle" and have stock — so they fit the NPC-dialog visual family more than the menu family.

## Where it surfaces

- **Shop** (`STATE_SHOP`): bare filigree treatment.
- **NPC dialog** (`STATE_NPC_ENCOUNTER`, same kind of "talk to a person" interaction): full `draw_dark_panel(border_color=enc['color'])` + `draw_header_bar`.
- **Cow encounter** (`STATE_COW_ENCOUNTER`): `draw_dark_panel(border_color=(180,140,80))` + `draw_header_bar`.
- **Story popup** (`STATE_STORY_POPUP`): full `draw_dark_panel(border_color=accent)` + accent strip.

The shop is the odd one out among "modal interactions with a character/situation".

## Suggested unification

Wrap `_draw_shop` in `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar(text="TRAVELLING MERCHANT", text_color=FP.GOLD_BRIGHT)`. Keep the filigree bars *inside* the panel — they can frame the item list or the gold readout. The visual outcome is a small grimoire panel (~600px wide) at center screen, matching the cow encounter pattern.

While there: replace the inline selection highlight `(60,50,20,180)` with `FP.MIDNIGHT_MID` row background and FP-palette text colors for buy/haggle hints.

## Notes

P3 because the shop *works* — items render, navigation works, the screen is readable. The visual issue is "looks like a quick first pass" rather than "looks broken or wrong". A single afternoon's refactor would bring it in line with NPC encounters.

Code-only fix.
