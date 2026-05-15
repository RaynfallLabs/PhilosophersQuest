---
id: balance-cooking-hp-softcap-defeats-late-game-threat
dimension: balance
severity: P1
title: Cooking softcap (1000 HP) + 22 HP/stair ascent rest = player heals through almost any L100+chase damage
status: open
systems: [cooking, stair_rest, player_stats, boss_L100, death_chase]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:player_baseline (BASE_HP 20, COOKING_HP_SOFTCAP 1000, STAIR_REST_CAP_ASC 22)
  - src/player.py:171-207 (HP_PER_LEVEL=0, stair-rest ascend 4% capped at 22)
  - src/food_system.py:25-46 (compound recipe potency formula)
  - balance_curves_agent_b.json:boss_stats.abaddon_destroyer_L100 (apocalypse_blast 6d10+8 avg 41 piercing)
  - balance_curves_agent_b.json:death_chase_difficulty.attack (2d12+15 avg 28)
discovered: 2026-05-15
---

## What's out of balance

The player can permanently grow max HP via cooking up to `COOKING_HP_SOFTCAP = 1000` (`player.py:194`), with a floor of 20% diminishing returns. A determined player reaches ~1000 max HP. CON 30 (achievable via stat-bonus rings + quirk +CON awards: rasputin +2, fenrir +1, leonidas +2, ragnarok +5, darwin +3, green_knight +1, gawain +1, spartacus +1, etc.) adds another ~20. Base 20 + CON 30 + cooking ~1000 = **~1050 max HP** at L100 for an optimized run.

Against this:
- Abaddon's biggest hit is `apocalypse_blast 6d10+8` = **avg 41 damage, max 68**, piercing (bypasses armor resistances). With shield/armor magic resistance reducing the magic-type by 40-60%, actual damage ≈ 16-25 per hit.
- Hit chance is bounded by `min_hit_chance = 0.25` for bosses (`monster.py:275`). So ~1 hit in 4 lands, dealing 16-25.
- Death's `reap 2d12+15` = avg 28, max 39 (always-hits). Death attacks at most every 4-8 turns at 75% speed, every turn at 100%, ~1.25/turn at 125%.

**Per-hit damage as a fraction of max HP at full optimization**:
- Abaddon best hit: 41/1050 = ~3.9% HP, after resists ~1.5-2%
- Death best hit: 39/1050 = ~3.7% HP

Meanwhile **stair rest on ascent**: `4% of max_hp capped at 22 HP` (`player.py:184`). At 1050 max HP the 22 cap dominates — 22 HP per stair × 100 ascending stairs ≈ 2200 HP healed during the climb. Through 100 floors of Death pursuit, the player heals roughly 2x their max HP just by using stairs.

The numerical truth: **a player who saturates cooking softcap cannot lose the chase to damage. They can only lose by getting walled into a corner.**

## Curve evidence

`balance_curves_agent_b.json :: player_baseline` shows the relevant ceilings. The "realistic_max_hp_at_L100" note (1050) compared against `boss_stats.abaddon_destroyer_L100.attacks[0].damage_avg = 41` and `death_chase_difficulty.attack.damage_avg = 28` makes the ratio explicit.

`monsters_by_floor[L91-L100].max_max_dmg` is 41 (apocalypse_blast — that IS Abaddon). No regular monster on the climb out hits harder than Abaddon. The descent's hardest hits at L61-L80 (Fafnir/Fenrir 5d10+9 ≈ 36-37) are *lower than what fully scaled HP swallows trivially*.

## Suggested re-tuning

Options, increasingly aggressive:

1. **Lower COOKING_HP_SOFTCAP** from 1000 → 300. The 20% diminishing floor still kicks in but the asymptote is ~400 max HP, not ~1050. Now Abaddon's piercing hits matter (40/400 = 10% HP) and Death's hits sting (28/400 = 7%).
2. **Cap stair-rest ascent heal as % of max_hp without an absolute floor**. The `STAIR_REST_CAP_ASC = 22` was reasonable when max HP was 200-300; at 1050 it's noise. Drop to absolute cap 12 and keep the 4% scaling. Same player at 1050 HP heals 12/stair = 1200 over 100 stairs, *still high* — drop to flat 2%.
3. **Make Death's reap pierce armor resistances**. Death is supposed to be unstoppable; her scythe should bypass cold/fire/magic mults the same way Abaddon's apocalypse_blast does.

Pair (1) with (3) at minimum.

## Notes

- This finding interacts strongly with `balance-abaddon-trivialised-by-sword-of-michael.md`: even WITHOUT the sword exploit, a max-cooking player tanks Abaddon by patience alone.
- This is also a play-test rule case where it IS realistic: a kid eats cooking compound recipes and the HP shows on the sidebar. A parent can see HP=1000 long before reaching L100.
- The 4% scaling was tuned for "max HP around 100-200"; the cooking system was added/expanded later (per the COOKING_HP_SOFTCAP comment in `player.py:194`). This is a classic curve drift bug — two systems were tuned independently and the product overflows.
- The mystery system, the cooking gold ingredients, and the rasputin-class quirk awards all amplify CON without coordination.
