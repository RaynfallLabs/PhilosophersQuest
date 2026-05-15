---
id: fun-combat-math-monotony
dimension: fun
severity: P3
title: Boss fights and deep-floor combat are math-chain-only — no subject variation when the action is most sustained
status: open
systems: [combat, math_quiz, boss_levels, dungeon_pacing]
when_it_hits: "Boss fights (L20/40/60/80/100) and any extended late-game combat encounter"
evidence:
  - src/game_combat.py:1242-1346
  - src/player.py:18
  - src/boss_levels.py:75-84
  - fun_pacing_trace.md#checkpoint-d-floor-60
discovered: 2026-05-15
---

## The friction or flatness
All combat is math chain (`game_combat.py:1242` calls `player_attack` which uses the math escalator chain). Math timer is 16s per question at WIS 10 — the snappiest subject in the game, intentionally so (CONTEXT notes math is the combat tempo by design).

This is correct for **single-encounter combat** — a swing against a rat is 1-2 questions of math, fast and rhythmic. But for **boss fights** and **deep-floor multi-mob clears**, the player spends 5-15 minutes in continuous math-chain combat. A boss like Abaddon at L100 may take 30+ math chains to kill (each chain potentially 5-10 questions). That's potentially **300+ math questions** in a single fight.

A kid who's a strong reader but mid-grade at multiplication tables has *no relief subject* during sustained combat. Every system except combat lets the player play to their strengths:
- Strong at history? Use accessories (history threshold).
- Strong at philosophy? Identify items, sphinx mystery.
- Strong at theology? Pray frequently.
- Strong at cooking? Compound recipes.

But combat is locked to math, and combat is the most-frequent action in the game. A player whose math is their weakest subject *cannot escape it* by changing strategy. They can equip a wand and switch to science (`game_magic.py:152-300+`), but the wand's threshold is also a quiz, and wands have limited charges.

Additionally: sustained math at 16s/question creates a *real-world fatigue curve*. After 100 math questions in 25 minutes of play, the player is mentally tired. The fatigue compounds with depth pressure.

## When and how often it fires
- Every combat. The 5 boss fights are the most acute fatigue points: 5-15 minutes of sustained math.
- A long deep-floor session features 200-400 math questions per hour of play.

## Suggested redirect
- **Boss-specific subject signatures**: each boss has a primary subject (math) but a *secondary* subject that mid-fight switches kick in. Fafnir (dragon) might have an *animal* sub-question between combat phases ("name the dragon"). Medusa might force a *philosophy* question ("describe the lesson of the mirror"). Multi-subject boss fights would distinguish the boss levels mechanically and give the player relief.
- **Subject swap at low HP**: once Abaddon is below 25% HP, his attacks become *theology* questions ("the angel of the bottomless pit serves what?"). Reframes the climax as a wisdom contest rather than an arithmetic endurance test.
- **Combat sidekick spells**: spells already use science (`game_magic.py:1063-1093`). Encourage spell use mid-fight by lowering MP costs or adding "spell rest" cooldown reduction tied to landing math chains. The player gets subject variety *within* a single combat.
- **Pet attacks during combat** could resolve in the pet system without forcing the player to do math. Pets already exist; making their attacks more impactful during boss fights specifically would give the player a non-math contribution channel.

## Notes
This is not "math is hard" or "math is bad." The math timer at 16s and chain mechanic are *correct* for combat tempo. The finding is about the **monotony of having only one subject for the most frequent action**. The dungeon is supposed to be a love letter to *all* knowledge — but the action a player does most is locked to one subject. Cross-system fix: combat + boss design + subject-action mapping.
