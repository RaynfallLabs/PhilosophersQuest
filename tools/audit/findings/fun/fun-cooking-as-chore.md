---
id: fun-cooking-as-chore
dimension: fun
severity: P3
title: Cooking is mechanically identical at all 5 qualities — same 5-question escalator regardless of context
status: open
systems: [cooking, food, harvest, hp_economy]
when_it_hits: "After 5-8 cooks (mid-game L15+), every cook feels the same"
evidence:
  - src/food_system.py:227-287
  - src/main.py:2344-2394
  - fun_pacing_trace.md#cooking
discovered: 2026-05-15
---

## The friction or flatness
Cooking — single ingredient (`food_system.py:227-287`) and compound recipe (`food_system.py:112-175`) — uses the same escalator-chain cooking quiz: max 5 questions, T1 → T5 escalator, chain length = meal quality. The mechanics never change. The cook quiz at L5 (a rat corpse, single ingredient) is mechanically identical to the cook quiz at L80 (a dragon corpse with a stat-boosting recipe).

What changes is the *outcome*: ingredients at deeper floors have higher `min_level`, which boosts potency via `sqrt(min_level)`, which scales SP/HP/permanent max_hp rewards. The reward varies; the *action* doesn't.

By cook #10, the player knows: "Type C to open cook menu, pick ingredient, answer 5 cooking questions, eat the result." It is the same 5-cooking-questions loop forever. Compared to combat (which varies by monster type, damage type, distance, AC, status effects) and lockpicking (which varies by container tier, trap state, alert chance) and prayer (which varies by altar, chain reward, cooldown), **cooking has the thinnest interaction texture** of any major action.

This wouldn't matter if cooking were rare — but cooking is the *only* dependable max-HP-growth path. A serious player cooks 30-80 times per run. The action repetition adds up.

## When and how often it fires
- A 30-min play session at mid-game floors features 4-6 cooks. By session 3 the player has done this loop 15-20 times. The "ooh, what's the recipe quality going to be?" reward varies, but the inputs are identical.
- A full successful run (L1→L100) features 60-100 cooks for max-HP optimization.

## Suggested redirect
- **Recipe-specific quiz tier curves**: instead of always escalating T1→T5, deeper recipes (compound, late-game) start at T2 or T3. The escalator becomes a per-recipe difficulty fingerprint.
- **Ingredient-specific cooking subjects**: most cooks are the cooking subject, but rare ingredients (dragon, lich, abyssal) trigger a *philosophy* or *science* sub-question mid-chain. Mythologically: "to prepare dragon, one must understand the dragon." A single rotation question per chain would add variety without overhauling the system.
- **Speed-bonus quality**: chain length is one dimension; *answer speed* could be a second dimension. Fast perfect chain → +1 bonus quality. Encourages high-WIS / high-literacy players to push.
- **Burns**: occasional "you must answer within X seconds or the meal burns" — adds tempo variance.

## Notes
This is not a "cooking is broken" finding. Cooking *works* — the reward variation, compound recipes, BUC interaction, and the chronicle moment for first compound cook all land. The friction is that the **input vocabulary** of cooking is identical from cook #1 to cook #100. Every other big action in the game has more texture per repetition. Compare to combat math chain: even though every combat is a math chain, the *target* changes (different monster damage, different distance, different AC, different elemental matchups), so the *strategic envelope* is different per fight. Cooking has no such envelope variation.
