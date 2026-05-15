# BEAUTY — visual consistency, layout, style coherence

**Read `tools/audit/CONTEXT.md` first.**

## Mission
The game's aesthetic identity is **"arcane grimoire"** (see `fantasy_ui.py:2` — *"High-fantasy medieval / arcane grimoire UI theme"*). Every screen, panel, menu, popup, prompt, and tile must read as part of the same artifact. Style drift between screens — different borders, different palettes, different font sizes, different padding, different button conventions — *is the failure mode*. Absolute taste calls are secondary.

Findings must span ≥2 systems (e.g., "the death screen uses square borders but every other screen uses arcane gothic" spans the death screen + the screen library).

## Required deliverable
`tools/audit/deliverables/beauty_screen_catalog.md` — an enumerated catalog of every screen the player sees, with for each: file:line of the render code, border style, color palette, font choice, padding rhythm, button placement, tonal register. Then a *consistency matrix* at the end calling out clashes.

Screens to inventory (at minimum — find more):
- Welcome / title (`welcome_screen.py`)
- Character creation
- Dungeon main view (sidebar, message log, map)
- Quiz panel (arcane grimoire — `game_render.py:1446`)
- Equip menu, inventory menu, eat menu
- Spell menu, scroll menu, wand menu, identify menu
- Study mode (`study_mode.py`)
- Hint / Recall Lore display (STATE_HINT)
- Story popups (e.g., `exit_with_stone`)
- Death screen
- Victory screen (Stone exit + secret Abyss victory)
- Encyclopedia / known-monsters list
- Mystery prompts
- NPC dialog
- Container open / lockpick
- Quirk unlock notification
- Pacing/proximity warnings (Death looms over you)
- Combat log entries (color codes for damage / loot / danger / info / success / warning)

## Seed threads (investigate at minimum)
1. **Cross-screen consistency** — pick two random screens and read both render functions. Compare. Are they obviously siblings, or do they look like different games?
2. **Color discipline** — `add_message` uses tags ('info', 'danger', 'loot', 'success', 'warning'). Are those tag-to-color mappings consistent across renderers? Does the death screen use 'danger' red the same way the combat log does?
3. **Quiz panel as the centerpiece** — the quiz panel is the most-seen UI element. Does it look as polished as the welcome screen? More polished?
4. **The Recall Lore / hint display** — hints are atmospheric, mythic. Is the display matching that voice, or just dropping text in a generic box?
5. **The Death-chase atmosphere** — when Death is 3 tiles away, the screen should *feel* different. Pale spectral pulse is mentioned (`game_render.py:1044`). Are other escape-phase visual cues present? Should they be?
6. **The secret-victory ending** — `_trigger_abyss` shows several messages in sequence. Is the visual treatment matching the gravity of the moment? Or just message-log spam?
7. **Tile rendering** — is the tile set coherent? Are any monsters' tiles obviously out of style? (`assets/tiles/`)
8. **Encyclopedia bug** — known finding from prior audit: most categories return nothing. When fixed, is the encyclopedia *visually* consistent with the rest of the game?
9. **Padding, spacing, borders, fonts** — pick three screens and compare line-by-line.
10. **Status indicators in the sidebar** — Recall Lore cooldown badge (`game_render.py:671`, `ui.py:246`), death-pursuit indicators, status effects. Is the visual hierarchy correct (most-urgent at top)?
11. **Welcome → character creation → first turn** — the first three screens a player sees. Do they teach the visual language?

## Finding file schema
Filename: `tools/audit/findings/beauty/<id>.md` where `<id>` is `beauty-<short-kebab-slug>`.

```markdown
---
id: beauty-<slug>
dimension: beauty
severity: P1 | P2 | P3 | P4
title: <one-line>
status: open
systems: [<screen1>, <screen2>, ...]   # MUST be ≥2 for BEAUTY
evidence:
  - <file>:<line> — <screen A render>
  - <file>:<line> — <screen B render>
  - beauty_screen_catalog.md#<anchor>
discovered: 2026-05-15
---

## The visual clash or inconsistency
<2–6 sentences>

## Where it surfaces
<which screen looks wrong relative to which other screen>

## Suggested unification
<concrete direction — adopt the prevailing style, or pick a new shared rule>

## Notes
<optional — note if this requires asset changes vs. code changes>
```

## Severity guide (BEAUTY-specific)
- **P1** — Unreadable, broken layout, the player can't see critical info; a screen that obviously breaks the arcane-grimoire identity (looks like a different game).
- **P2** — Obvious style drift between two frequently-seen screens; inconsistent color semantics; the centerpiece (quiz panel) is less polished than secondary screens.
- **P3** — Subtle clash, minor padding/spacing differences.
- **P4** — Nit.

## Hard rules
- Single agent (no consensus).
- Cite `file:line` for every visual claim. The harness has no rendering capability — you're reviewing the *code that draws*, not screenshots.
- The agent cannot run the game. Be explicit when you're inferring visual outcome from code rather than confirming it.
- Question banks are out of scope.
