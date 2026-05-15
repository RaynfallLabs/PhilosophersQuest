---
id: beauty-welcome-screen-ega-clash
dimension: beauty
severity: P2
title: Welcome screen vortex / domain ring uses self-described "EGA / 90s adventure-game" style — clashes with grimoire identity
status: open
systems: [welcome_screen, victory_screen, dungeon_view]
evidence:
  - src/welcome_screen.py:266 — comment "EGA-style color"
  - src/welcome_screen.py:450 — comment "Icon background panel (EGA-style bordered box)"
  - src/welcome_screen.py:456-457 — comment "Inner highlight line (top and left -- classic 90s bevel)"
  - src/welcome_screen.py:599 — comment "Octagon gem (EGA diamond feel)"
  - src/welcome_screen.py:606 — comment "Face highlights (EGA bevel)"
  - src/welcome_screen.py:267-280 — `_DOMAINS` palette uses saturated EGA colors `(85,255,255)`, `(85,255,85)`, `(255,85,85)`, `(255,85,255)` — not the FP grimoire palette
  - src/welcome_screen.py:633-665 — Title banner correctly uses `draw_panel` + `draw_filigree_bar` + grimoire colors
  - beauty_screen_catalog.md#1
  - beauty_screen_catalog.md#22
discovered: 2026-05-15
---

## The visual clash or inconsistency

The Welcome screen is the player's first impression. It contains:

- A **grimoire-styled title banner** at top using `draw_panel`, `draw_filigree_bar`, and the FP gold palette.
- A **grimoire-styled name input box** using `draw_panel` + `draw_header_bar`.
- A **rotating EGA-style vortex** filling the center: 6 rotating spiral arms, 12 floating "domain" icons in EGA-saturated cyan/magenta/yellow/green, an octagonal pulsing gem in EGA-bright gold.

The code is explicit about the divergence — every drawing comment for the vortex and domains uses words like "EGA-style", "classic 90s bevel", "EGA diamond feel". The author understood this is a different aesthetic than the rest. The two styles coexist on the same screen — the manuscript-grimoire chrome wraps the EGA-arcade centerpiece.

After name entry, the player is dropped into the dungeon, which has:
- Sidebar in grimoire chrome.
- Quiz panel in grimoire chrome (modulo `beauty-quiz-cards-vs-menu-rows`).
- Story popups, menus, character sheet, all grimoire.

So the welcome screen teaches the player one visual language (EGA arcade + grimoire frame) but the game then delivers a different one (pure grimoire). This is reverse onboarding — the welcome doesn't pre-teach the actual visual register the player will spend hundreds of hours inside.

The victory screen (`_draw_victory_screen`, `game_render.py:2456`) shows the alternative: rune circles + candle glow + filigree bars + arcane glow text. The same "spiritual centerpiece" need is met **without** EGA primitives. The welcome screen could be re-keyed to the same style without losing the cosmic-vortex sensation.

## Where it surfaces

- **Welcome screen** (vortex + domain ring + pulsing stone): EGA centerpiece in grimoire frame.
- **Victory screen** (rune circles + candle glow): pure grimoire spiritual-centerpiece treatment.
- **Death screen** (rune circles in burgundy + blood): mirror of victory, pure grimoire.
- **Dungeon view**: pure grimoire chrome.

The welcome screen is the outlier among the four "big composition" screens (welcome / victory / death / dungeon-with-quiz). Three of four are grimoire; one is EGA.

## Suggested unification

Two paths:

**Option A — Re-style the welcome centerpiece in grimoire.** Replace the EGA `_draw_vortex`, `_draw_domain_ring`, `_draw_stone` with:
- Rotating concentric rune circles (`draw_rune_circle` already exists, used on victory/death) sized large.
- The 12 domain icons rendered with grimoire-palette colors (use `FP.SUBJECT` dict, line 79-90), placed around a parchment-textured ring.
- The central gem can become a glowing illuminated initial letter in `Cinzel-Bold` — like the start of a chapter in an actual grimoire — or keep the octagonal gem but draw it in `FP.GOLD_BRIGHT`/`FP.GOLD_DARK` and surround it with `draw_candle_glow`.

**Option B — Keep the EGA welcome but commit to it.** Add another EGA-styled screen somewhere (perhaps a special "secret build" intro flourish) so the player learns "this game has two visual moods". Then the welcome stops being an outlier.

Recommended: Option A. The grimoire identity is the game's anchor; the welcome screen should set that expectation in its first three seconds.

## Notes

The vortex animation is genuinely cool and a lot of code went into it. Option A doesn't require deleting it — it requires re-keying the *palette* and *primitives* (use FP colors instead of EGA RGBs; use grimoire bevels instead of EGA bevels). The rotating-arms geometry can stay.

The "EGA-style bordered box" around each domain icon (`welcome_screen.py:449-457`) can be replaced with `draw_panel(bg=False)` for a similar but grimoire-correct framing.

This is P2 because the screen *works* and reads as evocative — it's just inconsistent with the rest of the game. P1 would require the screen being unreadable or breaking the identity contract in a more catastrophic way.

Code-only fix (no new assets).
