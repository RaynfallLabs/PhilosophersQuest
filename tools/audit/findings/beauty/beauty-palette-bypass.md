---
id: beauty-palette-bypass
dimension: beauty
severity: P2
title: Heavy use of inline RGB literals bypasses the FP palette — silent drift risk + ad-hoc colors everywhere
status: open
systems: [sidebar, hint_screen, lore_screen, mystery_approach, quirks_screen, npc_dialog, encyclopedia, study_mode, welcome_leaderboard]
evidence:
  - src/ui.py:233 — `pray_color = (140, 100, 200)` inline (would be `FP.ARCANE`)
  - src/ui.py:247 — `lore_cd_color = (80, 160, 200)` inline (no FP analog)
  - src/ui.py:254 — Lore ready `(120, 200, 240)` — different from cooldown color
  - src/ui.py:291 — `[Fire Protect]` color `(245, 150, 60)` inline
  - src/ui.py:295 — `[Manifest]` color `(200, 170, 240)` inline
  - src/ui.py:299 — `[Death Ward]` color `(220, 220, 255)` inline
  - src/game_render.py:1454-1457 — quiz chain color `(80,255,140)`, threshold color `(120,200,255)` inline
  - src/game_render.py:1508 — quiz question text `(255,245,210)` inline (close to but not `FP.VELLUM`)
  - src/game_render.py:1582 — quiz hint `(90,85,130)` inline (not `FP.HINT_TEXT`)
  - src/game_render.py:2825-2836 — lore screen color set (corpse `(160,120,40)/(80,60,20)/...` vs item `(80,120,200)/(40,60,120)/...`)
  - src/game_render.py:3267 / 3277 / 3285 — encyclopedia detail lore color `(180,200,230)` / `(80,120,200)` / `(200,215,240)` inline
  - src/game_render.py:3367-3372 — hint screen colors `(220,180,80)`, `(200,160,60)` inline
  - src/game_render.py:3404 — hint cooldown `(100,85,45)` inline
  - src/game_render.py:407-409 — quirks panel colors `(16,12,24)/(140,100,200)/(70,50,100)` inline
  - src/game_render.py:418 — quirks title `(200,170,255)` inline
  - src/game_render.py:825 — NPC dialog text color `(220, 210, 190)` inline
  - src/study_mode.py:18-31 — `_SUBJECTS` palette inline (duplicate of `fantasy_ui.py:79-90` `FP.SUBJECT`)
discovered: 2026-05-15
---

## The visual clash or inconsistency

`fantasy_ui.py:22-90` defines the `FP` palette as the single source of truth for the game's color identity. There are 30+ named entries with semantic aliases (`BODY_TEXT`, `HINT_TEXT`, `LOOT_TEXT`, `DANGER_TEXT`, `SUCCESS_TEXT`, `WARNING_TEXT`, `ACCENT_TEXT`, etc.) plus a `SUBJECT` dict mapping subjects to colors. The whole design is set up to be the centralized palette.

In practice, **inline RGB literals are everywhere**. A grep across the listed evidence files turned up over 70 distinct inline color tuples in the render code. Examples:

- **Sidebar prayer cooldown** is `(140, 100, 200)` — close to but not identical to `FP.ARCANE = (82, 35, 118)`. Refactoring FP.ARCANE will not affect the sidebar.
- **Sidebar lore cooldown** is `(80, 160, 200)` and **lore ready** is `(120, 200, 240)` — two different teals for the same status family.
- **NPC dialog options** color is `(210, 200, 180)` for normal options (not `FP.BODY_TEXT = (218, 192, 145)`) and `(220, 210, 190)` for description text. The two close-but-distinct values create subtle drift within the same render function.
- **Encyclopedia entry detail lore** uses `(200, 215, 240)` body text + `(80, 120, 200)` header (line 3277). **`_draw_lore_screen`** uses identical-but-separate `(200, 215, 240)` / `(80, 120, 200)` for items (line 2832-2836). They agree by coincidence; whichever file gets edited first will desync from the other.
- **Study mode** duplicates the entire subject color palette inline at `study_mode.py:18-31` rather than importing `FP.SUBJECT` (`fantasy_ui.py:79-90`).

The drift risk is structural: every inline RGB is a place that does *not* update when the palette is rebalanced. The "fix the FP palette and the whole game updates" mental model is false.

## Where it surfaces

This is a cross-cutting concern — it shows up in nearly every file that does direct drawing:

- **Sidebar** (`ui.py`): 6+ inline cooldown/passive/effect colors.
- **Quiz panel** (`game_render.py:1382`): 8+ inline colors for question/timer/choice text and chain feedback.
- **Hint screen, lore screen, mystery approach, quirks screen**: heavy inline color use.
- **Study mode** (`study_mode.py`): full subject palette duplicated.
- **NPC dialog** (`game_render.py:792`): inline text colors.
- **Welcome screen** (`welcome_screen.py:266-280`): 12 inline EGA domain colors.

Anywhere outside the `draw_menu` family and the `draw_dark_panel` family, raw RGB literals dominate.

## Suggested unification

This is a refactor, not a single fix. Two complementary steps:

1. **Add missing FP entries** for recurring inline colors. Candidates that recur often enough to warrant naming:
   - `FP.COOLDOWN_TEAL = (80, 160, 200)` and `FP.READY_TEAL = (120, 200, 240)` — used by lore/prayer/various cooldown indicators.
   - `FP.LORE_BLUE = (200, 215, 240)` and `FP.LORE_BLUE_DIM = (80, 120, 200)` — used by encyclopedia + lore screen item display.
   - `FP.HINT_TEXT_DIM = (100, 85, 45)` — currently inline in hint cooldown footer.
   - Or, equivalently: drop these inline colors entirely and use existing FP entries that are "close enough" (e.g., `FP.HINT_TEXT` for all hint text).
2. **Import `FP.SUBJECT` in `study_mode.py`** instead of redefining `_SUBJECTS` palette. Pure DRY fix.
3. **Replace existing inline tuples with FP references** in `ui.py`, `game_render.py`, and `welcome_screen.py` (where applicable). Most inline literals can be mapped to an existing FP entry that's within 10 RGB units.
4. **Add a lint rule or test** that flags hex/tuple literals that match `\((\d+,\s*\d+,\s*\d+)\)` in src/, excluding `fantasy_ui.py`. This freezes the palette discipline for future changes.

The first step (add FP entries) is the cheapest and most-impactful — most inline colors *want* a name; they just don't have one yet.

## Notes

This is P2 not P1 because nothing is broken — every screen has a color. The issue is structural risk: the palette system is *not* the source of truth, it's *a* source of truth. A future palette rebalance will only update half the game.

A side effect of fixing this: the cluster of "rolled inline chrome" screens (`beauty-rolled-inline-chrome`) will become much easier to refactor — they have many of these inline colors as their identifying signature.

Pure code refactor. No new assets.
