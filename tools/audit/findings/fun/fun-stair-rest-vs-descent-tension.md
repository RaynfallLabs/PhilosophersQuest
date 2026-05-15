---
id: fun-stair-rest-vs-descent-tension
dimension: fun
severity: P3
title: "Descent stairs heal 0 HP — players who don't cook either die or grind cooking for 30 minutes"
status: open
systems: [healing_economy, cooking, food, level_transitions, hp_regen]
when_it_hits: "Floors 5-30 for players who haven't internalized that cooking is the only HP repair path"
evidence:
  - src/player.py:171-189
  - src/food_system.py:34-46
  - src/main.py:2042-2051
  - fun_pacing_trace.md#foundational-tempos
discovered: 2026-05-15
---

## The friction or flatness
The game has three HP-recovery paths during the descent:

1. **Cooking** — escalator chain, max +50ish max_hp per compound recipe at high quality, cumulative.
2. **Prayer** — gated by 100-280 turn cooldown, also gives partial HP heal at chain 5-8.
3. **Passive regen** — 1 HP every 15-20 turns (`main.py:2049`), blocked by bleeding/poison.

Stair-rest healing on descent is **exactly 0 HP** (`player.py:172: STAIR_REST_CAP_DESC = 0`). The design comment says this is intentional: "NO stair-rest HP healing on descent (damage accumulates)."

This is fine in *concept* — it pressures the player toward cooking, which is good design. But the game does not *teach* this. There's no in-game text that says "your HP doesn't recover between floors going down; cook to grow max HP." A new player who's been raised on dungeon games where stairs heal hits L10 with 12/30 HP, descends, and is shocked to find themselves at 12/30 on L11. The mismatch between expectation and behavior is silent — there's no "the stairs offer no rest. You must cook." message.

The result for a player who hasn't yet learned cooking: a slow grind down through floors with a tiny HP reserve, where one bad chain breaks the run. The information is in the game (Tier-3 hints reference dragon/wolf+fungi cooking, item lore on ingredients hints at HP), but the *practical instruction* "cook frequently or you will die" is not surfaced.

Conversely, a player who *has* internalized cooking can spend 5-10 minutes per floor cooking everything they harvest — turning the descent into a kitchen sim. This is also a fun-friction tension: cooking is the *only* dependable HP growth, and the cooking quiz is a 60s escalator chain. **A risk-averse player spends more time at the cooking screen than fighting monsters.**

## When and how often it fires
- For a new player: hits at L5-15 when HP becomes a real constraint and the realization "stairs don't heal" lands cold.
- For an experienced player: hits at every floor as a tempo choice — "cook now or push forward?"

## Suggested redirect
- **A one-time teaching beat at L3-5**: a chronicle line or NPC encounter that says explicitly "The dungeon does not let you rest as you descend. Cooking what you harvest is how a Philosopher endures." Surface the rule.
- **Lore hint at T1 that names cooking as the HP path**: a hint like "Those who cook what they kill grow stronger; those who only fight grow weaker." Tier 1 so a new player will hit it within 5-10 Recall Lore tries.
- **Optionally**, give descent a tiny stair-rest (5 HP, not max_hp%) just to take the *edge* off the surprise — keeping the design intent (damage accumulates) but smoothing the no-rest cliff.

## Notes
This is a *teaching* finding, not a balance finding. The mechanic is sound. The problem is the silent contract between game and player. A kid who learns to cook is rewarded; a kid who hasn't learned yet dies on L8 wondering why their HP didn't reset. The play-test rule applies here: a 10-year-old's first run is where this finding lives or dies.
