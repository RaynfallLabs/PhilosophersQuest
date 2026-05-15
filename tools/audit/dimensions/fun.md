# FUN — play feel, pacing, friction, wonder

**Read `tools/audit/CONTEXT.md` first.**

## Mission
The north star: **"Knowledge is power, but gaining knowledge should be FUN."** The game is hard *and* it must be a game a kid wants to come back to. Friction from *learning* is good (that's the design). Friction from broken UX, repetitive grind, unfair timer-vs-action mismatches, or pacing dead zones is bad.

You are reasoning about the **player loop** — minute-by-minute, floor-by-floor — and where the game gets boring, frustrating, monotonous, unfair, or fails to deliver wonder. Findings must span ≥2 systems (e.g., "the food economy plus the stair-rest meta makes mid-floor combat trivially safe, removing tension" spans food + level transitions + combat). Single-system polish notes ("the inventory menu is slow") belong in BEAUTY.

## Required deliverable
`tools/audit/deliverables/fun_pacing_trace.md` — a minute-by-minute walkthrough of player experience at floors 1, 10, 30, 60, 90, and the Death-chase. For each:

- What is the player doing turn-by-turn? (Walk, fight, identify, eat, rest, pick lock, pray, etc.)
- What is the quiz tempo? (Math chain every N turns; philosophy threshold occasionally; etc.)
- What ambient life exists? (Mysteries, NPCs, flavor encounters, altars?)
- What is the tension curve? (Are HP/SP/MP reserves drained meaningfully? Or is the player coasting?)
- Where does friction appear?
- Where does wonder appear (or fail to appear)?

This is a narrative trace, but *grounded* in actual code paths and data. Cite `file:line` when you reference a mechanic.

## Seed threads (investigate at minimum)
1. **The quiz tempo × action frequency match** — math 16s timer fires constantly in combat; theology 46s fires rarely under high stakes (prayer during Death chase). Does the budget feel right? Is the player ever stuck doing a slow subject under combat pressure? Is the chain-mode "always fast math" loop fatiguing across a 30-minute session?
2. **The three acts' distinct feel** — does Act I (descent) feel different from Act II (boss) from Act III (escape)? Or is the escape just "descent in reverse with one monster behind you"? The escape is supposed to be a *climax*.
3. **Recall Lore as a discovery loop** — is the cooldown right? Is the chain payoff exciting? Is the hint pool deep enough to keep the player surprised across a full run? When the player gets a T5 hint about a secret, does it land?
4. **Hidden-system density** — does the player *feel* the secret surface area without being spoiled? Are there enough cryptic hints, altar appearances, NPC riddles, mystery encounters, weird item descriptions, easter eggs that the dungeon feels alive with secrets?
5. **Pets and NPCs** — does pet bonding feel rewarding or vestigial? Do NPCs add meaningful break-from-combat moments? Or are they speed bumps?
6. **Death curve** — when a 10-year-old dies on floor 8 to a bad math chain, does the *moment of death* feel earned and parseable? Or feel like the game cheated? Bones writing future ghosts is supposed to ease the sting — does it?
7. **Identification loop** — philosophy threshold quizzes for ID. Is this fun the 30th time? Or grindy? Does the Philosopher's Stone (auto-ID) come at the right point in the curve?
8. **Cooking** — escalator-chain cooking quizzes for food prep. Cooking ingredients have an HP boost (per Tier-3 hint: dragon-type for resilience, wolf+fungi for strength, etc.). Is cooking a *fun* mini-game or a chore?
9. **Lockpicking** — economics threshold for chests. Lockpicks are fragile (Tier-1 hint). Is the failure-and-recovery loop satisfying? Or punishing?
10. **The escape's Death-chase pacing** — speed escalation 50→75→100→125 across the climb. Does the screen-time of "Death is N tiles behind you" stretch too long? Too short? Are there moments to breathe between proximity warnings?
11. **Quirks as a meta-loop** — ~80 unlockable quirks across many runs. Does the unlock cadence feel exciting? Are there obviously-grindy quirks that fall flat? Do the mythological references resonate with a kid who knows some but not all of them?
12. **The "I want to play again" hook** — what makes a run end *with wanting to start another run*, vs. *putting down the controller*? Identify both kinds of run endings present in the code paths.

## Finding file schema
Filename: `tools/audit/findings/fun/<id>.md` where `<id>` is `fun-<short-kebab-slug>`.

```markdown
---
id: fun-<slug>
dimension: fun
severity: P1 | P2 | P3 | P4
title: <one-line>
status: open
systems: [<system1>, <system2>, ...]   # MUST be ≥2 for FUN
when_it_hits: "<floor / act / situation>"
evidence:
  - <file>:<line>
  - fun_pacing_trace.md#<anchor>
discovered: 2026-05-15
---

## The friction or flatness
<2–6 sentences describing what makes this less fun than it should be>

## When and how often it fires
<a kid playing for 30 min hits this N times>

## Suggested redirect
<design-level suggestion — may require a decision, not just a code change>

## Notes
<optional — including whether this is constrained by intentional difficulty>
```

## Severity guide (FUN-specific)
- **P1** — Repeated unavoidable misery in the main loop; the game punishes the player for *correct play* (not failed learning); a mechanic is so broken-feeling a kid would quit; the Death chase is boring instead of terrifying; the boss is anticlimactic.
- **P2** — Significant friction in a frequent action; mid-game tedium; the wonder budget is empty at a moment when wonder should fire.
- **P3** — Minor pacing dip, occasional repetitiveness, fixable with a one-line tone shift.
- **P4** — Nit on phrasing or timing.

## Hard rules
- Single agent (no consensus). Lean into voice and judgment — that's the point.
- Cite `file:line` even for soft observations.
- Reference your pacing trace for evidence.
- Difficulty is **NOT a FUN finding**. Hardness is the design. FUN finds *unfair* hard, *boring* hard, or *broken* hard — not "this is hard."
- Question banks are out of scope. You can reason about *quiz tempo*, but not bank content.
