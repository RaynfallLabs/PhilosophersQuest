---
id: balance-math-quiz-tempo-vs-mob-density
dimension: balance
severity: P3
title: Math quiz timer 16s @ WIS 10 vs F40+ mob density — sustained combat asks for ~30+ T4 math answers per encounter
status: open
systems: [math_subsystem, monsters, combat, player_stats]
floors_affected: [30, 100]
evidence:
  - src/player.py:18 (`'math': (8, 0.8)` — 8s base + 0.8 per WIS = 16s @ WIS 10)
  - balance_curves_agent_a.json:monsters_by_floor (F30 pool ~100 monsters; F50 pool ~50; F70 pool 32)
  - balance_curves_agent_a.json:weapons_by_min_level (chain length 6-10 means 6-10 math questions per swing chain)
  - balance_curves_agent_a.json:stat_scaling.wis_to_quiz_timer
discovered: 2026-05-15
---

## What's out of balance

Math is the combat subject (per CLAUDE.md spine). Timer per question @ WIS 10: 16s (formula `8 + WIS*0.8`).

Combat tempo analysis:
- Player encounters an F40 monster avg HP 263.
- Iron sword chain-5: 15.6 dmg. Requires 17 hits to kill.
- 17 hits × ~5 math questions per chain (to maintain chain 5) = 85 math questions per kill.
- At 16s per question = 1360s = 22 minutes of pure math per kill.

This is FAR too slow. In practice:
- Players don't always maintain chain 5; they swing at chain 1-2 for quick hits.
- Iron sword chain 1: 0.6×6 = 3.6 dmg/hit. 263 HP / 3.6 = 73 hits. Each chain-1 takes 1 question. 73 questions × 16s = **20 minutes per kill** at low chain.

For an F40 encounter (the dungeon usually presents 1-3 monsters per room): 20-60 minutes of math per room. Across 99 floors of descent + 100 of ascent, that's hundreds of hours of pure math.

The actual game must have much higher chain efficiency. With Hrunting (L50, chain 9 mult, baseDmg 26): chain-9 hit = 234 dmg. F40 mob dies in 1 hit (1 chain of 9 = 9 questions = 144s = 2.4 minutes per kill). That's playable.

**The disparity reveals the design**: combat is meant to be solved via high-chain weapons. Players in iron sword/early gear face very long combats. **The kid who finds Hrunting at F50 has 6x faster combat than the kid who doesn't**. This is RNG-driven and harsh.

For T4 (8th grade) math, a 16s timer @ WIS 10 is appropriate. For T1 (5th grade), 16s is generous. But for sustained 50-100 questions per encounter, **player fatigue is the real limiter**, not quiz time. The game expects kids to answer math correctly under combat pressure for extended sessions.

## Curve evidence

- `monsters_by_floor` pool size by floor reaches peak 254 at F15 and drops thereafter. Per floor, dungeon spawns typically 8-15 monsters initially with respawn.
- `weapons_by_min_level` shows iron sword (L1) baseDmg 6, chain 6 final mult 3.2x = 19 dmg/hit. Compared to F30+ monsters HP 85 = 4.5 hits per mob.
- `stat_scaling.wis_to_quiz_timer`: math base 8s + 0.8s/WIS. Even at WIS 20 (rare): 24s per question. Theology at WIS 20 = 48 + 17 = 65s — but theology fires rarely (prayer only).
- The chain economy assumes uninterrupted math sequences. In practice players take damage during chains (mob attacks while quiz UI active per `_process_input` in game_input.py).

## Suggested re-tuning

Three options:

1. **Increase iron-sword baseDmg from 6 to 9-10** (or add a generic L11 tier between iron and steel). This reduces the floor of combat tempo for unlucky players who don't get uniques early. See `balance-tier-20-staircase` for the broader fix.
2. **Reduce monster HP scaling F30-F70** to match what generic gear can output. Currently F40 avg 263 vs iron sword 16/turn = 17 turns per kill (too long). Cutting F40 HP to ~100 = 6 turns per kill (more reasonable).
3. **Adjust the chain math** — reduce chain-1 multiplier from 0.6 to 1.0 so first-hit damage is uncompromised. Currently chain 1 PUNISHES the player for missing the second answer. Making chain 1 = 1.0x makes "quick stab" combat viable.

Option 3 is least disruptive. The current `0.6/1.0/1.5/2.0/2.6/3.2` multipliers PENALIZE chain 1 — flipping to `1.0/1.4/1.8/2.2/2.7/3.2` would smooth the curve and make low-chain combat tolerable for less-skilled players.

## Notes

Cross-system: math subject × player stats (WIS) × weapon chain economy × monster HP scaling × dungeon density.

This is P3 because the design intent is clearly "combat is hard; reward skilled math players." The numbers ARE asking a lot but the difficulty contract supports it. The flag is that the iron-sword-to-Hrunting variance is large enough that lucky/unlucky runs diverge sharply.

For the kid audience: a kid who finds Hrunting at F50 has a different game than a kid who finds nothing. The first kid feels powerful; the second feels stuck. RNG variance should be smoothed by adding more generic tiers (see `balance-tier-20-staircase`).

Also note: the math chain produces SP cost (combat costs stamina). High-chain attacks cost more SP per hit. The SP economy interacts with this — a player who runs out of SP can't swing, can't chain. SP economy was not deeply audited here; flagging as additional research direction.
