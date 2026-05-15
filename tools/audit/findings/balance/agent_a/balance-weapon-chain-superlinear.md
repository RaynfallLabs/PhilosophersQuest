---
id: balance-weapon-chain-superlinear
dimension: balance
severity: P2
title: Unique weapon chain multipliers scale to 10x — perfect math players one-shot late-game monsters
status: open
systems: [weapons, combat, math_subsystem, bosses]
floors_affected: [50, 100]
evidence:
  - balance_curves_agent_a.json:weapons_by_min_level (Excalibur maxChainLength=10, mults=[..., 10.0])
  - data/items/weapon.json (Excalibur: baseDamage=22, chainMultipliers last=10.0)
  - data/items/weapon.json (Tyrfing baseDmg=36, mult[7]=8.5 → 306 dmg at chain 8)
  - data/items/weapon.json (Caladbolg baseDmg=34, mult[7]=8.5 → 289 dmg)
  - data/items/weapon.json (adamantine zweihander maxChain=6, mults max=5.5 → 32*5.5=176 dmg)
  - balance_curves_agent_a.json:boss_stats.abaddon.hp (5000)
discovered: 2026-05-15
---

## What's out of balance

Generic adamantine weapons (L81) max at chain 6 with a 5.0-5.5x final multiplier — appropriate scaling. **But unique L50-L70 weapons have wildly longer chain caps (8-10 hits) with super-linear multipliers up to 10x at perfect chain.** A perfect math player wielding Excalibur (L60, baseDmg 22, mult[10]=10.0) hits for **220 damage per swing** at max chain.

Examples (from weapons.json verified):

| Weapon | min_level | baseDmg | maxChain | final mult | max-chain dmg |
|---|---|---|---|---|---|
| iron sword (L1 baseline) | 1 | 6 | 6 | 3.2x | 19 |
| adamantine sword (L81 generic) | 81 | 15 | 7 | 5.0x | 75 |
| adamantine zweihander (L81 best generic) | 81 | 32 | 6 | 5.5x | 176 |
| Excalibur | 60 | 22 | 10 | 10.0x | **220** |
| Tyrfing | 70 | 36 | 8 | 8.5x | **306** |
| Caladbolg | 65 | 34 | 8 | 8.5x | **289** |
| Hrunting | 50 | 26 | 9 | 9.0x | **234** |
| Mjolnir | 65 | 26 | 9 | 9.0x | **234** |
| Dawnbreaker | 81 | 30 | 9 | 9.0x | **270** |

Critically, **Hrunting (L50, baseDmg 26, 9-chain, 9x final = 234 dmg at perfect chain) outperforms every generic L81 adamantine weapon at perfect chain**. A player with Hrunting at F50 and decent math skill is over-equipped through F80.

Vs Abaddon (HP 5000): Tyrfing perfect-chain damage = 306. Number of perfect-chain swings to kill Abaddon = **17 swings**. At ~30 turns per swing (chain-build + execute) = ~500 turns total. With Time Freeze spell (5 free turns no-counterattack) and Heroism/Empower bonuses, this drops to ~10-12 swings.

For comparison, Excalibur was advertised as the ultimate sword (per its name and lore). Its 10x chain multiplier is the steepest curve in the game. **Earning Excalibur basically wins the run** for a math-skilled player. For a kid who's good at math, F60+ becomes a steamroll.

## Curve evidence

- `weapons_by_min_level` rows show maxChainLength varies from 6 (iron sword, all generic adamantine 2H) to 10 (Excalibur). The unique-weapon multiplier table reaches 10x.
- Excalibur is L60 (min_level 60) — available 40 floors before Abaddon. The L60 boss-floor reward placement makes Excalibur a likely Fafnir drop or post-Fafnir reward.
- `boss_stats.abaddon.hp` = 5000. At Excalibur chain 10 (10 perfect math answers consecutively): 220 dmg/hit. To clear: 23 hits. At average chain 5 (60% multiplier band): 22 * 2.5 = 55 dmg. To clear: 91 hits. The chain-skill gap is **4x damage difference**.
- Compare to adamantine zweihander at chain 5 (mult 4.5): 32*4.5 = 144 dmg. So a poor-math player with the best generic weapon (144) outperforms a good-math player with iron sword (19) and an average player with Excalibur (55). The relative power is determined by:
  1. Weapon chain cap (6 vs 10)
  2. Player's math performance during combat

This is by design — math performance determines damage output. But the SLOPE of the chain multiplier (from 6 → 10 chains, mult 3.2x → 10x) is too steep at the top. A 25% better math player has access to **312% better damage**, not 25% better damage.

## Suggested re-tuning

1. **Cap unique weapon maxChainLength at 8** and the final multiplier at 7-8x. This preserves the prestige feel (better than generics) while removing the runaway-scaling at chain 9-10.
2. **Diminishing returns on chain mults**: currently mults are super-linear (mult[0..6] doubles approximately every 2 chain). Flatten chain 8-10 to incremental gains: 7x → 7.5x → 8x rather than 7.5x → 9.0x → 10.0x.
3. **Quirk-gating long chains**: a maxChainLength of 10 should only be reachable with a specific quirk unlocked (e.g. Apollo "10 max chain hits"). Otherwise cap at 8.

The current state rewards math-skilled players appropriately (this is the design), but the slope is too steep. A 10x multiplier is so dominant that a single weapon choice (Excalibur, Tyrfing, Mjolnir) overrides the entire item-tier system.

## Notes

Crosses systems: weapons (chain definitions), math subsystem (which determines chain), combat (damage calculation), and bosses (the design target for difficulty). This is also a math-subject pacing issue: the math timer is 16s @ WIS 10 (per SUBJECT_TIMER `'math': (8, 0.8)`), and the player must hold concentration for 10 consecutive correct answers to hit chain 10. That's HARD for a kid — appropriately so — but when it succeeds the reward is disproportionate.

This may be intentional. The CONTEXT.md says math is "the high-frequency combat tempo" and the chain reward is the carrot. But the slope between chain 6 and chain 10 is too steep. Either flatten the top end, or extend boss HP to keep pace.

Note also: weapon chain length interacts with chain modes for math. The deliverable shows mathTier per weapon — late weapons require mathTier 4-5 (high school). So while a kid in T1-T3 cannot reach chain 10 with Excalibur (because they can't answer T5 math), a kid in T5 might. The wall placement is "kid must reach T5 math to unlock the 10x multiplier" — which IS the difficulty contract. Severity stays P2 not P1 because the gating works.
