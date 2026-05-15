---
id: balance-dot-stacking-bleeding-burning
dimension: balance
severity: P2
title: DoT effects bleeding (1/15 max_hp) and burning (1/20 max_hp) scale with monster max_hp — large monsters die fast to small DoTs
status: open
systems: [status_effects, monsters, magic, ammo]
floors_affected: [40, 100]
evidence:
  - src/monster.py:130-167 (`bleeding_dmg = max(1, self.max_hp // 15)`; `burning_dmg = max(1, self.max_hp // 20)`)
  - balance_curves_agent_a.json:boss_stats.abaddon.hp (5000)
  - balance_curves_agent_a.json:boss_stats.fafnir.hp (2500)
  - balance_curves_agent_a.json:boss_stats.fenrir.hp (3000)
  - balance_curves_agent_a.json:monster_tick_status (corrected — tick_effects IS called per turn)
discovered: 2026-05-15
---

## What's out of balance

Monster `tick_effects` (monster.py:130-167) applies damage-over-time scaled to the monster's **max_hp**:

- bleeding: `max(1, max_hp // 15)` per turn
- burning: `max(1, max_hp // 20)` per turn
- poisoned: 1 per turn (flat)
- diseased: 8% chance × `max(1, max_hp // 20)` per turn

The scaling-with-max_hp design means: **the bigger the monster, the larger the DoT** per turn. This makes DoTs disproportionately powerful against bosses.

Examples (using `boss_stats` from deliverable, assuming no resistance applies):

| Boss | max_hp | bleeding/turn | burning/turn |
|---|---|---|---|
| Asterion | 800 | 53 | 40 |
| Medusa | 1500 | 100 | 75 |
| Fafnir | 2500 (poison/fire immune) | 166 | 125 (immune) |
| Fenrir | 3000 (cold-resist not fire-immune) | 200 | 150 |
| Abaddon | 5000 (fire-resist not bleeding-immune) | 333 | 250 (resisted) |

A single 5-turn bleeding stack on Fenrir = 1000 damage (33% of HP). A 10-turn bleeding stack from a Hrunting bleed-on-hit effect = 2000 damage (67% of Fenrir HP).

Stacking matters: `status_effects[name] = min(current + duration, MAX_EFFECT_DURATION)`. So multiple hits with bleeding-on-hit weapons stack ADD duration. Hit a boss 10 times with a bleeding-trigger weapon and the bleeding could last 20+ turns. At Abaddon scale: 20 turns × 333 = 6660 damage from bleeding alone (more than total HP).

Most boss `resistances` lists in the deliverable do NOT include `bleeding` or `disease` as resist types. Looking specifically:

- Abaddon: resistances=['poison', 'cold', 'fire', 'slash', 'blunt'] — no bleed/disease resistance
- Fenrir: resistances=['cold', 'slash'] — no bleed/disease
- Fafnir: resistances=['fire', 'poison', 'blunt', 'slash', 'pierce', 'holy', 'magic'] — comprehensive, includes bleed-implicit via 'slash'? Unclear from data.
- Medusa: ['poison'] — no bleed
- Asterion: ['blunt'] — no bleed

(Note: `take_damage` checks damage_type not effect-name; bleeding ticks as `physical` damage which IS in 'slash' resist for Fafnir? Need to verify resist matching).

**Cross-finding with `balance-disintegrate-spell-dominant`**: a player who DISINTEGRATES then has a few stacks of bleeding from melee can effectively shred bosses without traditional damage.

## Curve evidence

- monster.py:140 `bleeding_dmg = max(1, self.max_hp // 15)`
- monster.py:146 `burning_dmg = max(1, self.max_hp // 20)`
- monster.py:153-158 `take_damage(bleeding_dmg)` and `take_damage(burning_dmg)` called per tick
- Player DoT delivery vectors in items data:
  - Weapons with `bleeding_chance` / `stunChance` (data/items/weapon.json — varies, several uniques have bleed-on-crit)
  - Spell `acid_arrow` applies poisoned (5-turn chain-scaled DoT)
  - Wand of fire applies burning
  - Ammo (data/items/ammo.json) — some flame/poison arrows
- The `MAX_EFFECT_DURATION` cap is not visible in this audit's reads — check status_effects.py for the upper bound. If it's, say, 100 turns, then stacking bleeding to 100 turns on Abaddon = 33300 damage.

## Suggested re-tuning

1. **Cap DoT per-turn at ~1% of max_hp** rather than `max_hp//15` (6.67%). 1% of max_hp/turn means a 30-turn DoT does 30% of HP — meaningful but not dominant. Abaddon bleeding/turn at 1%: 50 damage instead of 333.
2. **Add boss bleeding/burning/disease resistance** — most bosses should have at least one of these in their resist list. Abaddon especially should resist bleeding (lake-of-fire god is metaphysically "above" mortal wounds).
3. **Cap DoT duration stacking** — total bleeding cap at 8 turns regardless of how many hits add to it. Prevents perma-bleed.

## Notes

Cross-system: monster mechanics × status_effects × spells × weapons × the unfixed-as-of-consensus.json status now-fixed.

This is P2 because:
- The math says DoTs CAN over-perform vs bosses.
- But the player has to LAND the DoT via a weapon-trigger or spell — there are RNG gates.
- Boss resistances mitigate this partially (Fafnir is fire+slash immune, blocking the main DoT vectors).

If play-test reveals that bleeding/burning are not actually used much (because weapons rarely proc them), this severity drops to P3. Verify with VOICE/FUN auditors who'd see how common DoT triggers feel in actual play.

This finding REPLACES the earlier (incorrectly written and now deleted) `balance-monster-tick-fix-implications` finding. The consensus.json P3 claim that tick_effects is never called appears OUTDATED — current source HAS the call at main.py:1559.
