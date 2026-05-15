---
id: beauty-sidebar-status-flat
dimension: beauty
severity: P3
title: Sidebar section headers and bars use ad-hoc chrome — break sibling relationship with modal headers
status: open
systems: [sidebar, modal_headers, message_log]
evidence:
  - src/ui.py:122-130 — `_header` draws a flat `FP.MIDNIGHT_MID` strip with `FP.GOLD_BRIGHT` text, no flourishes
  - src/ui.py:146-151 — `_bar` uses inline `(18, 18, 30)` dark slot + per-bar color, `border_radius=3`
  - src/fantasy_ui.py:353-385 — `draw_header_bar` (the canonical header primitive) has two-tone fill + mid-edge diamonds + accent line
  - src/fantasy_ui.py:392-402 — `draw_divider` (the canonical divider) has center-diamond ornament
  - beauty_screen_catalog.md#3
  - beauty_screen_catalog.md (Consistency Matrix item 5)
discovered: 2026-05-15
---

## The visual clash or inconsistency

The sidebar is the player's most-seen UI surface — visible 100% of the time during play. Its section headers (`VITALS`, `ATTRIBUTES`, `STATUS`, `EQUIPMENT`, `INVENTORY`) are rendered by `Sidebar._header` (`ui.py:122-130`) as a flat `FP.MIDNIGHT_MID` rectangle with `FP.GOLD_BRIGHT` text inside — no flourishes, no diamonds, no two-tone fill.

Every modal in the game uses `draw_header_bar` for the same conceptual purpose ("this is a section title"). `draw_header_bar` (`fantasy_ui.py:353-385`) is a two-tone strip (`FP.MIDNIGHT` top half + `FP.MIDNIGHT_MID` bottom half) with mid-edge diamond ornaments and an accent-colored separator line.

The sidebar's `_header` is a stripped-down version of `draw_header_bar`. The two don't visually agree. When the player opens an equip menu over a sidebar that's already showing "VITALS" / "STATUS" / etc., the modal's `EQUIP / UNEQUIP` header looks more decorative than the sidebar's `VITALS` header — even though they're both serving the same function.

Similarly, the sidebar's HP/SP/MP bars (`_bar`) use `border_radius=3` flat slots — the grimoire chrome elsewhere uses corner flourishes and ornamental dividers. The bars in the *quiz panel's combat HUD* (`_draw_combat_hud` line 1647-1651) also use flat rounded rects (`border_radius=4`). The two bar systems agree on plain rounded rect, which is internally consistent — but neither agrees with the surrounding panel chrome.

## Where it surfaces

- **Sidebar headers** (5+ section headers, visible always): flat `MIDNIGHT_MID` strip + `GOLD_BRIGHT` text.
- **Modal headers** (20+ modal panels): `draw_header_bar` two-tone + diamond ornaments + accent line.
- **HP/SP/MP bars** (sidebar + quiz combat HUD): plain rounded rects, no ornamentation.
- **Message log top border** (`ui.py:54`): plain 1px `GOLD_DARK` line — not a `draw_divider` (which has a center diamond).

## Suggested unification

Two options:

**Option A — Adopt `draw_header_bar` in the sidebar.** Modify `Sidebar._header` to use `draw_header_bar(surf, (x, y, w, h), text=text, font=self._fhd, text_color=FP.GOLD_BRIGHT)`. The two-tone fill and diamonds will appear in the sidebar headers. Result: every "section header" in the game looks the same.

**Option B — Add a "compact header bar" variant.** Introduce `draw_header_bar_compact` for places where the full two-tone + diamonds is too busy. The sidebar can use compact, modals stay with full. Define the contract explicitly.

Recommended: Option A. The sidebar section headers are currently the *flattest* visual element in the game's chrome, and they're the most-seen. Adopting `draw_header_bar` adds 2 mid-edge diamonds per header — a small, repeated grimoire signature that anchors the sidebar to the rest of the game.

For the bars: introduce a `draw_resource_bar` primitive in `fantasy_ui.py` that combines the slot + fill + readout + grimoire-correct accent (subtle bevel or framed inset). Both sidebar and combat HUD then call it. Keeps internal consistency *and* adds grimoire signature.

## Notes

P3 because (a) the current rendering is functional and readable, and (b) the sidebar isn't ugly — it's just visually understated. But understated in the most-seen surface area undercuts the grimoire identity across the whole game. Fixing this raises the floor for the whole experience.

Pure code refactor. No new assets.
