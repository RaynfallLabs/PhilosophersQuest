---
id: balance-permadeath-wall-placement
dimension: balance
severity: P2
title: Permadeath wall analysis — current curves suggest most kid-runs die F1-15 (learning), then plateau toward F60-80 if cooking is learned; F100 too easy if cooking, too hard if not
status: open
systems: [dungeon_progression, food_system, monsters, bosses, player_stats]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_a.json:stat_scaling.max_typical_late_game_hp_no_cooking ("~44 — dangerously low")
  - balance_curves_agent_a.json:stat_scaling.max_typical_late_game_hp_with_full_cooking_softcap ("~1030")
  - balance_curves_agent_a.json:boss_stats.asterion (F20, HP 800, phasing_walls)
  - balance_curves_agent_a.json:boss_stats.abaddon (F100, HP 5000, multiple piercing 6d10+8 attacks)
  - balance_curves_agent_a.json:monsters_by_floor (F100 pool=14, F1 pool=20)
discovered: 2026-05-15
---

## What's out of balance

Per CONTEXT.md target distribution: kids should "reach floor 20-40 reliably, 60 with effort, 100 only with mastery." This finding evaluates whether the current numbers produce that distribution.

**Phase 1: F1-15 (learning floors).** Iron sword loadout. Avg monster HP 4-30. 5-6 questions per chain. Player HP base 30. Mistakes are recoverable: a 5-dmg goblin hit takes 17% HP. Kid plays, dies at F8 (running low SP, ran into too many mobs), restarts, dies at F12 (overcommitted to an ambush). Reaches F15 by run 4-5. **Pacing: appropriate.**

**Phase 2: F16-30 (Asterion gate).** Avg HP 50-100. Iron sword chain-5 = 15 dmg = 3-6 hits per mob. Asterion F20: HP 800, 2d12+1 (avg 14) gore + phasing walls. **For an iron-sword build with no uniques: ~50 perfect-chain hits required.** Kid dies repeatedly at Asterion. To beat: need Achilles's Spear L20 (baseDmg 18, the F20 unique drop). **Drop rate determines this gate.** Per `balance-asterion-too-hard-for-iron`, this wall may be too high.

**Phase 3: F30-60 (cooking emerges).** Avg HP 100-500. Generic gear steel/gold tiers. Cooking is the critical skill — recipes give max_hp boosts. A kid who learned cooking quizzes scales their HP from 30 → ~200-300 by F60. Combat tempo: chain-5 steel sword (22 dmg) vs F40 avg 263 HP = 12 turns per mob. **Pacing: appropriate IF cooking is engaged.**

**Phase 4: F60-99 (gear divergence).** This is where lucky/unlucky runs diverge:
- LUCKY: found Excalibur (L60), Tyrfing (L70), max_hp >500 via cooking — F60-90 cruises.
- UNLUCKY: stuck on adamantine sword L81 with chain-7 ~75 dmg, max_hp ~150, faces F80 Fenrir (HP 3000) — dies repeatedly.
- The 10-floor dead band F71-F80 (see `balance-dead-band-71-80`) makes this worse.

**Phase 5: F100 Abaddon.** Abaddon HP 5000, hits 6d10+8 piercing.
- COOKING build (HP 1000): 5 turns to die. 5000/22 dmg/turn from average attacks = 36 turns of combat. WIN.
- NON-COOKING build (HP 44): 1 turn to die. Forced retreat/bones.
- LUCKY-WEAPON build (Excalibur chain-10 = 220 dmg/turn): Abaddon dies in 23 turns. **Trivial fight.**

**Phase 6: Death-chase F1.** Per `balance-death-chase-prayer-loop`, prayer-freeze + Fisher King quirks make this skippable.

**Result**: the wall placement is NOT at F100 (Abaddon) for cooking-builds — it's at F20 (Asterion) for non-lucky players. Kids who learn cooking dominate F40+. Kids who don't learn cooking can't survive Phase 5. The variance is gear+cooking dependent, not skill-dependent.

## Curve evidence

- Compiled from deliverable: `stat_scaling.max_typical_late_game_hp_no_cooking` vs `with_full_cooking_softcap` (23x divergence).
- `boss_stats.asterion`: HP 800, phasing walls, hit_and_run AI — hard at F20.
- `boss_stats.abaddon`: HP 5000, 5 attack types including piercing — hard but DPS-soluble with Excalibur.
- `monsters_by_floor` pool collapse (`balance-monster-pool-collapse`): less variety in endgame compounds the lucky-loadout issue.

## Suggested re-tuning

Four coordinated changes to fix the variance:

1. **Lower Asterion HP to 400-500** OR add a generic L11 weapon tier (between iron and steel). Removes the F20 wall for unlucky builds.
2. **Cap cooking max_hp at 200-300** (per `balance-cooking-hp-economy-dominates`). Removes the lucky-cooker dominance.
3. **Boost Abaddon HP to 8000-10000** OR add phase mechanics (multi-stage fight). Forces real combat at F100 even for cooking+weapon-stacked builds.
4. **Add intermediate generic gear at L11/31/51/71/91** (`balance-tier-20-staircase`). Smooths the curve and reduces RNG variance.

Without these: the wall falls in unintended places. Kids who learn cooking AND find Excalibur ace the game. Kids who don't learn cooking can't pass Phase 5. Kids who learn cooking BUT have bad weapon luck struggle through F60-80.

## Notes

Cross-system: monsters × bosses × weapons × food_system × player stats × Death-chase mechanics × score economy. This is a holistic finding consolidating insights from `balance-cooking-hp-economy-dominates`, `balance-dead-band-71-80`, `balance-asterion-too-hard-for-iron`, `balance-time-freeze-vs-abaddon`, `balance-weapon-chain-superlinear`, and `balance-tier-20-staircase`.

Severity is P2 because the design intent (per CONTEXT.md) explicitly says "reach 20-40 reliably, 60 with effort, 100 with mastery." Current numbers produce different distribution — more like "20 hard (Asterion), 30-50 trivial (steel sword), 60-80 hard (no gear bridge), 80-100 easy if cooked / impossible if not."

The reward-code economy depends on F100 being mastery-gated. Currently it's mastery-OR-cooking-OR-luck-gated. Tightening to mastery-only requires the 4 changes above.

User play-test required to confirm the actual wall placement — per CLAUDE.md's play-test rule, mid-game balance is a play-test concern. I can't drive pygame from the harness; the dev should play and report.
