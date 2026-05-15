---
id: balance-asterion-too-hard-for-iron
dimension: balance
severity: P2
title: Asterion (L20 boss, HP 800, phasing walls) is brutal for an iron-sword loadout — wall at the wrong place
status: open
systems: [bosses, weapons, monsters, math_subsystem]
floors_affected: [15, 25]
evidence:
  - balance_curves_agent_a.json:boss_stats.asterion (HP 800, thac0 4, 2d12+1 gore, hit_and_run AI, can_phase_walls)
  - balance_curves_agent_a.json:weapons_by_min_level (iron sword L1 baseDmg 6, mult[5]=2.6 → chain-5 max 15.6 dmg; steel sword L21 baseDmg 8, available AFTER asterion)
  - src/boss_levels.py:194 (asterion_minotaur spawned in F20 labyrinth)
  - src/boss_levels.py:166-192 (phasing_walls — asterion can attack through walls)
discovered: 2026-05-15
---

## What's out of balance

The first boss the player meets is Asterion the Minotaur at F20. Stats from deliverable `boss_stats.asterion`:

- HP 800
- thac0 4 (very accurate at this floor)
- Attacks: gore 2d12+1 (avg 14, max 25), trample 1d8 (avg 4.5)
- AI: hit_and_run (engages then retreats)
- can_phase_walls: True (attacks through walls; boss_levels.py:169-192 phasing_walls set)

A typical L15-L20 player loadout per the deliverable:

- Best generic weapon at F20: iron sword L1 (baseDmg 6, mult[5]=2.6) — chain-5 damage = 15.6
- Unique pre-F20 weapons: Pharaoh's Crook L3 (5), Spear of Romulus L4 (7), Sling of David L5 (6), Prometheus's Torch L8 (8), Mjolnir Shard L10 (12), Sword of Damocles L12 (28!), Robin Hood's Longbow L14 (14)
- L20 weapons available AT Asterion: Achilles's Spear L20 (baseDmg 15-18)

Iron sword vs Asterion: 800 HP / 15.6 = **52 perfect-chain hits to kill**. With hit_and_run AI, Asterion retreats — the player can't reliably maintain chain. Asterion's phasing walls means melee tracking is unreliable.

The steel sword tier (L21 baseDmg 8, chain-5 = 21.6) is NOT YET AVAILABLE — it's a one-floor delta but the boss IS the floor 20 gate. A player who hasn't found Achilles's Spear / Sword of Damocles / Mjolnir Shard is fundamentally underequipped.

**Asterion's 800 HP is calibrated for someone who already has the L20 uniques**, but those drops are RNG. The bones-bug (per consensus.json P2: load-save violations preserved) means players may carry ghost gear, but a fresh run faces a brutal wall.

Compare to other bosses (deliverable):

| Boss | Floor | HP | Damage spike |
|---|---|---|---|
| Asterion | 20 | 800 | 2d12+1 (avg 14, max 25), phasing walls |
| Medusa | 40 | 1500 | gaze paralyze +2d8+2 piercing (avg 11) |
| Fafnir | 60 | 2500 | 4d12+5 slash (avg 31), fire breath piercing |
| Fenrir | 80 | 3000 | 5d10+9 bite (avg 36), cold |
| Abaddon | 100 | 5000 | 6d10+8 piercing (avg 41) |

Asterion 800 HP at F20 represents 16% of Abaddon's HP. By weapon scaling: iron sword chain-5 (15.6) vs adamantine zweihander chain-6 (176) = 11x ratio. So a F100 fight is 11x more damage with 6.25x more HP — that's appropriate scaling for Abaddon. But at F20 the player has NO 11x damage multiplier yet, only the chain-5 of iron sword.

The "this is the right kind of hard" question: F20 SHOULD be a learning gate. But 52 perfect-chain hits is too far above the math sustainability for a kid. Stalled chains, retreats, phasing-wall attacks — the player runs out of HP/SP before damage adds up.

## Curve evidence

- `weapons_by_min_level` floors 1-20: 25 generic L1 + 4 unique (L3-L14) + 1 unique L20 = 30 weapons available; many are NOT melee or have niche use (Sling, Net, Pharaoh's Crook is throwing).
- Best-case iron weapon at F20: Robin Hood's Longbow L14 (baseDmg 14, chain-5 mult ~2.6) = 36 dmg/shot — ranged, can keep distance from hit_and_run melee boss. **This is the meta path** — ranged combat. But a kid who picked melee build has the iron sword 15.6 dmg/hit chain-5.
- Phasing walls in src/boss_levels.py:169-192: Asterion has 70+ phasing wall tiles in a labyrinth. Player cannot consistently corner-trap or kite the boss.
- Mini-boss progression around F20: erlking_mini L20 (HP 350) is the alternate F20 threat. 350 HP vs 800 is reasonable for chain combat. Asterion is 2.3x harder.

## Suggested re-tuning

Either lower Asterion HP to ~400-500 (matching erlking_mini scale) OR introduce a generic weapon tier at L15-L18 (baseDmg ~7-8) so the player has a real upgrade before the first boss. The latter is preferable — it keeps Asterion meaningful as a wall but gives players a fair tool.

Alternative: weaken Asterion's phasing wall set (currently 70+ tiles; reduce to 15-20 tactical shortcuts). Or remove the hit_and_run AI in favor of standard aggressive — let the player chain reliably.

## Notes

Cross-system: weapon tier curve × boss HP scaling × AI patterns × math chain sustainability for ages ~8-12 (CONTEXT.md target audience).

This finding is partially about *the wall falling at the wrong place*. F20 is meant to be the first major test. CONTEXT.md says kids should reliably reach F20-F40. Asterion at HP 800 with phasing walls is currently too hard for the early gear curve — the wall is correctly placed but too high. Lowering HP or improving F15-F19 gear ladder fixes it.

Verify in play-test (per CLAUDE.md's play-test rule): does a real 5th-7th grader with iron sword and decent math actually beat Asterion? If yes, this finding may be P3 instead of P2. If no, P2 stands. I cannot drive pygame from the harness; user play-test required.
