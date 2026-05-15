---
id: balance-shield-progression-vs-monster-thac0
dimension: balance
severity: P3
title: Shield AC progression is gentle (1->4 across 100 floors) but bunched at boss-acts; minimal mid-floor incentive to upgrade
status: open
systems: [shields, armor, dungeon_loot]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:shields_by_min_level
  - tests/test_balance.py:60-67 (test_shields_cover_every_20_levels)
discovered: 2026-05-15
---

## What's out of balance

`balance_curves_agent_b.json :: shields_by_min_level` shows 21 shields, AC range 1-6:

| min_level | shield | ac_bonus |
|---|---|---|
| 1 | wooden_shield | 1 |
| 11 | hide_shield | 1 |
| 12 | shield_of_the_spartans | 3 |
| 21 | iron_shield | 2 |
| 30 | ancile | 3 |
| 31 | bronze_shield | 2 |
| 41 | steel_shield | 2 |
| 50 | svalinn | 4 |
| 51 | mithril_shield | 3 |
| 55 | svalinn_shield, pridwen | 4 |
| 60 | scutum_of_aeneas | 5 |
| 61 | crystal_shield | 3 |
| 65 | greater_aegis_of_athena, tower_shield_of_ajax | 5, 6 |
| 71 | obsidian_shield | 3 |
| 81 | dragonscale_shield, adamantine_shield | 4, 4 |
| 9999 | 4 specials | 3-4 |

The plain-material shield progression is wooden 1 → hide 1 → iron 2 → bronze 2 → steel 2 → mithril 3 → crystal 3 → obsidian 3 → dragonscale 4 → adamantine 4. **The slope is exceptionally gentle**: 0 AC delta from L1 to L20, then +1 every 10-20 floors.

Compared to monster THAC0 floor (-16 from L40+, see `balance-AC-runaway-deep-monsters-cannot-hit.md`), shield progression doesn't matter — the player's TOTAL AC is dominated by armor (32 max contribution) and DEX. Shield contributes 4-6 of the ~33 AC total.

Meanwhile the "special" shields like `tower_shield_of_ajax` (ac 6, L65), `pridwen` (ac 4, L55), `scutum_of_aeneas` (ac 5, L60) jump 2-3 AC over their plain peers. The plain progression is a feint — the named shields are the actual upgrade path.

## Curve evidence

`tests/test_balance.py:test_shields_cover_every_20_levels` ensures at-least-one shield per 20-floor band. Passing. But "at least one shield with min_level in the band" doesn't mean "the shield is mechanically a meaningful upgrade." Mithril shield AC 3 at L51 is the same AC as the L30 ancile.

The mechanical reality:
- L1-L29: wooden/hide (ac 1) or shield_of_the_spartans (ac 3 at L12).
- L30-L49: ancile (ac 3) or iron/bronze/steel (ac 2).
- L50-L65: svalinn/pridwen (ac 4), scutum (ac 5), aegis (ac 5).
- L65+: tower_shield_of_ajax (ac 6), dragonscale (ac 4), adamantine (ac 4).

So the named special shields are the upgrade curve. The plain-material shields are filler.

## Suggested re-tuning

1. **Steepen plain progression**: wooden 1, hide 2, iron 3, bronze 3, steel 4, mithril 4, crystal 5, obsidian 5, dragonscale 5, adamantine 6. Now there's a noticeable upgrade every 10-20 floors and the player FEELS material progression.
2. **Or accept the design**: plain shields are utility (cheap, common), special shields are rewards. But then the test name `test_shields_cover_every_20_levels` is misleading — what's tested is *availability*, not *progression*.

(1) is more consistent with the game's broader "more depth = more power" promise.

## Notes

- P3 because the player can pick up any shield and feel something. The curve isn't BROKEN, just shallow.
- Cross-system: shields + (implicit) armor synergy + monster thac0 expectations.
- The 9999 min_level "special" shields (aegis_of_athena ac 4, bronze_aegis ac 3, lionheart_shield ac 4) are quest rewards — they aren't in the standard spawn pool. Their AC values being modest is reasonable; their EFFECTS (reflect Medusa, etc.) are the value.
