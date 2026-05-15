# VOICE — narrative consistency, wonder, geek-dad register

**Read `tools/audit/CONTEXT.md` first.**

## Mission
The game's voice is **first-person chronicle + geek-dad mythic register + encouraging without being soft**. Sample lines from the code:

> *"I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard."*
> *"An Egyptian eye of blue faience mends what was torn. Patience is its method — the old gods do not hurry."*
> *"Strange altars sometimes appear in the dungeon. Those who approach and kneel before them discover ancient challenges — and ancient rewards."*

Short sentences. Frank. Awe without bombast. Defeat without self-pity. Mythic vocabulary used naturally. Encouraging on failure, never mean. Substantive moral vision — this is being built for the developer's kids, and the world it depicts is honest where the world is honest.

You are auditing whether **every piece of player-facing prose in the game** lives up to this voice. Findings must span ≥2 systems (e.g., "monster descriptions are mythic but combat log is corporate, creating dissociation" spans monsters.json + combat.py). Voice register clashes between adjacent pieces of content are the headline failure mode.

**Question banks are out of scope.** Do not audit `data/questions/*.json`. You are auditing:
- `_log_chronicle()` calls and the resulting first-person voice
- `add_message()` calls — combat log, status messages, prompts
- `data/hints.json` — Recall Lore content
- `data/monsters.json` — monster names, descriptions, flavor fields
- `data/flavor_encounters.json` — ambient encounter prose
- `src/npc_encounters.py` — NPC dialog
- `src/mystery_system.py` — mystery prompts and resolutions
- `src/welcome_screen.py` and story popups (`'exit_with_stone'`, `'exit_without_stone'`, etc.)
- Status effect messages (`status_effects.py`)
- Death screen / victory screen text
- Quirk unlock messages (`quirk_system.py`)
- Item lore fields (e.g., the Flux Capacitor's `lore` field in `main.py:1440`)
- UI prompts and menu labels (`ui.py`, `fantasy_ui.py`)

## Required deliverable
`tools/audit/deliverables/voice_content_catalog.md` — an enumerated catalog of player-facing prose surfaces. For each surface:
- File and approximate line range
- Sample lines (3–5 quotes)
- Voice score: 1–5 (1 = dissociated/corporate/dry, 5 = pitch-perfect chronicle/mythic register)
- Notes on drift, clashes, register issues

Then a **secret-spoilage scan**: walk every player-facing string and flag any that *explicitly explains* a hidden system instead of hinting. Example: `main.py:1440` (Flux Capacitor's lore) is borderline — does it spoil the time-stop mechanic? Or hint?

Then a **lore-coverage gap analysis**: enumerate the major strategic systems and quests, and for each note whether `data/hints.json` has appropriately tiered lore entries hinting at it. Missing coverage is a finding.

## Seed threads (investigate at minimum)
1. **The chronicle voice** — sample 20+ `_log_chronicle()` calls. Are they all in the same first-person voice? Does any one read like generic prose?
2. **The combat log register** — `add_message` calls in `game_combat.py` and `combat.py`. Combat happens constantly. Is the language fresh, varied, mythic? Or boilerplate ("You hit the X for Y damage")?
3. **Status effect messages** — `_EXPIRE_MSGS` and per-turn DOT messages in `status_effects.py`. Are they vivid? Or technical?
4. **Hint pool depth & voice consistency** — `data/hints.json` is mostly excellent (sample T1–T3). Are T4 and T5 entries at the same quality? Is the *density* of secret-hinting hints right (not too cryptic, not too explicit)?
5. **NPC dialog** — `src/npc_encounters.py`. Are NPCs distinct voices, or do they all sound like the same narrator?
6. **Flavor encounters** — `data/flavor_encounters.json`. Are these tonally coherent with the chronicle voice?
7. **Mystery prompts** — `src/mystery_system.py`. Do mysteries feel like *mysteries* (curiosity-inducing) or like puzzles (mechanical)?
8. **Monster descriptions** — `data/monsters.json` flavor fields. Geek-dad register? Or D&D-statblock?
9. **The encouraging-on-failure rule** — sample death messages, quiz-fail messages, "your thoughts scatter" messages. Are they kind? Or do they punch down?
10. **The hidden-system non-spoiling rule** — direct spoilers of secret mechanics in code comments, tooltips, menu text are **P1 findings**. Audit the Power-quirk text, lore text on rare items, tooltip strings.
11. **Quirk unlock notifications** — when Prometheus unlocks, does the player get a mythic moment? Or just a "Unlocked: Prometheus" toast?
12. **Tier discipline** — the lore-hint pool is tiered 1–5. T1 hints should teach basics; T5 should reveal deep secrets. Are entries placed at the right tier? Is anything in T1 that should be in T4?

## Finding file schema
Filename: `tools/audit/findings/voice/<id>.md` where `<id>` is `voice-<short-kebab-slug>`.

```markdown
---
id: voice-<slug>
dimension: voice
severity: P1 | P2 | P3 | P4
title: <one-line>
status: open
systems: [<surface1>, <surface2>, ...]   # MUST be ≥2 for VOICE
evidence:
  - <file>:<line> — "<quote>"
  - <file>:<line> — "<quote>"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness
<2–6 sentences>

## Why it breaks the register
<reference the chronicle voice or the geek-dad register>

## Suggested rewrite direction
<concrete tone note; sample alternative phrasing optional>

## Notes
<optional — note if this is a frequent surface or rare>
```

## Severity guide (VOICE-specific)
- **P1** — Tone-violating content that contradicts the moral/voice vision; **explicit spoilers of hidden systems** in player-facing text; cruel or punishing failure messages; voice that would embarrass a parent showing the game to a kid.
- **P2** — Dry/dissociated register on a frequent surface (combat log, status messages); a major hidden system has no lore coverage at any tier; obvious clash between two adjacent prose surfaces.
- **P3** — Flat or generic phrasing in an occasional surface; mistier placement (T1 hint that should be T3).
- **P4** — Nit on word choice.

## Hard rules
- Single agent (no consensus).
- Cite `file:line` AND the literal quoted text for every claim.
- **Do not audit `data/questions/*.json`** — that's the question banks, out of scope.
- The chronicle voice samples in CONTEXT.md are your North Star.
- Hidden-system non-spoiling is **load-bearing**. Spoilers are P1.
