---
id: balance-cooking-hp-economy-dominates
dimension: balance
severity: P1
title: Cooking softcap +1000 HP vs base ~44 HP creates a 23x divergence by F100
status: open
systems: [food_system, player_stats, bosses, items_accessory]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_a.json:stat_scaling.max_typical_late_game_hp_no_cooking ("~44 (30 base + 14 CON) — dangerously low")
  - balance_curves_agent_a.json:stat_scaling.max_typical_late_game_hp_with_full_cooking_softcap ("~1030")
  - balance_curves_agent_a.json:stat_scaling.cooking_hp_softcap (1000)
  - balance_curves_agent_a.json:boss_stats.abaddon (attacks include 6d10+8 apocalypse_blast piercing, 4d8+4 hellfire, 3d10+4 plague_breath piercing)
  - src/player.py:1-7 (BASE_HP=20)
  - src/player.py:194-207 (increase_max_hp with softcap)
  - src/food_system.py:160 (cooking grants increase_max_hp(hp_bonus, from_cooking=True))
discovered: 2026-05-15
---

## What's out of balance

The player has TWO separate HP economies that don't talk to each other:

1. **Stat-driven HP** — base 20 + CON. With the best stackable accessory load (+5 Amulet of Titan Constitution L65 + +5 Idunn's Apple L70 + +4 Ring of Endurance L45) the player tops out at CON 24 → max_hp 44. Plus any quirk-granted +CON (mostly +1 to +3 per quirk) and rare scroll/altar boons.
2. **Cooking-driven HP** — `Player.increase_max_hp(from_cooking=True)` has a softcap of 1000 with diminishing returns floor of 0.20x. A patient cook can stack to roughly max_hp 1030 by F100.

This creates a 23x gap between the "I don't cook" build and the "I cook" build. Abaddon (F100, deliverable `boss_stats.abaddon`) has multiple piercing attacks averaging 14-41 damage per hit (avg `apocalypse_blast` 6d10+8 = 41, piercing means armor doesn't help). A 44 HP player dies in 1-2 Abaddon hits. A 1030 HP player can soak 25+ hits.

**This breaks the difficulty contract**: cooking is a skill-gate quiz (escalator_chain, 4d8 quiz rounds per dish per `cooking` tier requirements) but the player doesn't have to answer FRONTAL combat questions to ramp HP this way. A diligent cooker who quizzes well on cooking can effectively skip the harder combat questions because Abaddon becomes a sponge fight.

## Curve evidence

- Base HP scaling: `BASE_HP=20` (player.py:2) + `max_hp = BASE_HP + CON` (player.py:42). With base CON 10: max_hp=30. With +14 CON from late accessories: 44.
- Cooking softcap: `COOKING_HP_SOFTCAP = 1000` (player.py:194). Diminishing returns `cap_factor = max(0.20, 1.0 - cooking_hp_gained/1000)`. Even after 1000 cooking_hp_gained, every new cooking bonus is floored at 0.20x — so the cap is approximate but reachable.
- Abaddon damage profile (`boss_stats.abaddon.attacks`):
  - `apocalypse_blast`: 6d10+8 piercing magic — avg 41, max 68
  - `hellfire`: 4d8+4 fire — avg 22, max 36
  - `plague_breath`: 3d10+4 piercing poison — avg 21, max 34
  - `soul_chill`: 3d8+3 cold — avg 17, max 27
  - `abyssal_claw`: 2d10+3 slash — avg 14, max 23
- Locust_count [3,5] means Abaddon spawns 3-5 locust adds per turn (extra HP attrition)
- Player at 44 HP: dies in 1 average apocalypse_blast (41) + any other attack. 100% death in 1 turn.
- Player at 1030 HP: 25 turns of 41-dmg apocalypse blasts. With stair-rest and prayer healing, infinite survival.

## Suggested re-tuning

Three options, ordered from least to most disruptive:

1. **Tighten the softcap** to 200-300 max cooking HP. Keep cooking valuable for SP/stat buffs but make HP from cooking a meaningful boost, not a 25x multiplier. The bone-system already exists for ghost HP — `bones.py` defaults `max_hp = 50` (line 103), suggesting the original design didn't anticipate 1000+ HP.
2. **Cap based on dungeon level reached** — softcap = `max(50, dungeon_level * 5)`. This forces players to actually descend to unlock the HP ceiling.
3. **Tie cooking-HP gain to combat math performance** — only award cooking max-HP if the player has answered N math questions correctly that floor. Cross-couples the systems so a pure-cooker can't dodge the combat-quiz core loop.

Option 1 is recommended. The current softcap of 1000 turns Abaddon into a tank fight instead of the apocalyptic damage-race the design intends.

## Notes

This finding spans 4 systems: food_system (cooking grants HP), player stat formulas (CON gives 1 HP), accessories (the realistic CON ceiling), and the F100 boss damage profile. Without a fix here, the difficulty contract collapses: the kid who quizzes well on cooking can survive Abaddon at 1030 HP without ever needing to answer well on T5 math during combat. The reward-code economy is undermined.

Verified cross-system: data/items/accessory.json (line 4983 Idunn's Apple +5 CON), src/food_system.py:160 (cooking max-HP path), src/main.py:1488 (50000 score for Stone — incentivizes reaching Abaddon).
