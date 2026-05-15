---
id: balance-abaddon-trivialised-by-sword-of-michael
dimension: balance
severity: P1
title: Sword of Michael + Holy weakness + ignore_resistances reduces Abaddon to a 4-5 hit fight
status: open
systems: [boss_L100, weapons, karma_judgment, combat]
floors_affected: [99, 100]
evidence:
  - balance_curves_agent_b.json:boss_stats.abaddon_destroyer_L100
  - balance_curves_agent_b.json:weapons_by_min_level (sword_of_michael peak_damage 720)
  - src/combat.py:84-96 (ignore_resistances bypass)
  - src/combat.py:156-160 (abaddon_bonus_damage 6d10)
  - data/items/weapon.json:sword_of_michael (baseDamage 45, maxChain 9, critMultiplier 4.0)
  - src/game_encounters.py:936-961 (judgment grants sword + scales)
  - data/monsters.json:abaddon_destroyer (hp 5000, weaknesses ["holy"])
discovered: 2026-05-15
---

## What's out of balance

Abaddon has 5000 HP, thac0 -16, and resistances against `poison, cold, fire, slash, blunt` — five of the six common damage types. His only listed weakness is `holy`. The Sword of Michael, awarded on a positive-karma judgment at the L99 altar (`game_encounters.py:936-961`), has `baseDamage: 45`, a 9-rung chain capped at `16.0x`, `critMultiplier: 4.0`, `ignore_resistances: true`, deals `holy` damage (weakness on Abaddon → 1.5x), AND has `abaddon_bonus_damage: "6d10"` per hit (avg +33).

A single max-chain crit therefore lands at roughly:
`45 * 16.0 * 4.0 (crit) * 1.5 (holy weakness) * STR-factor ~1.3 + 6d10 ≈ 5,650 damage` — *one-shot lethal vs. Abaddon's 5000 HP*. Even a non-crit chain-9 (16x mult, no crit) clears ~4,300. Two ordinary chain-7s (9x mult ≈ 405*1.5 + 33 = ~640) over four turns close the fight regardless.

This is a karma-gated bypass. Every player who plays a "good" run is implicitly handed the auto-win sword for the climactic boss before ever reaching it. The "boss is a wall" contract is broken via judgment.

## Curve evidence

`balance_curves_agent_b.json :: boss_stats.abaddon_destroyer_L100` shows hp=5000, thac0=-16, resistances=["poison","cold","fire","slash","blunt"], weaknesses=["holy"]. `balance_curves_agent_b.json :: weapons_by_min_level` confirms Sword of Michael is the single peak weapon at peak_damage 720 (next: Tyrfing 306, Caladbolg 289 — half as deadly and *without* the holy/ignore_resistances trifecta).

Compare with the Asterion fight at L20 (HP 800, no boss weapon handed out): the L20 player must actually fight. Compare with Medusa L40 (HP 1500): same. The progression of "boss must be fought" *breaks* at L100, exactly the wrong place — the difficulty contract demands the climax escalate, not collapse.

## Suggested re-tuning

Three options, listed in order of preference:

1. Strip `abaddon_bonus_damage` from the Sword. The sword is already special (ignore_resistances + holy on a holy-weak target = 1.5x baked in + 16x peak chain). The Abaddon-specific bonus is double-counting.
2. Cap `critMultiplier` at 2.0 or remove crit entirely on the Sword. A 16x max-chain *and* a 4x crit is mechanically a 64x multiplier — even chain-9 spike feels like a cheat code.
3. Remove `weaknesses: ["holy"]` from Abaddon. The Destroyer is the king of the bottomless pit; he should resist holy, not double-suffer it. Reserve holy-weakness for lesser undead/demons.

A combination of (1) and (3) leaves the sword strong (still bypasses resistances) but Abaddon doesn't double-soak the holy bonus. Option (2) reins in spike damage independently.

## Notes

- Negative-karma path empowers Abaddon (+50% HP, locusts strengthened — `game_encounters.py:978-989`), which only widens the gap.
- The L99 altar holy-fire prayer ALSO strips Abaddon's resistances for `chain*2` turns (`game_divine.py:749-767`). Stacking that with the Sword is redundant overkill, but stripping resistances on a holy-only-weak boss is itself dubious (it removes the only condition that the holy bonus is conditional on — i.e. nothing left for the sword to flex against).
- Negative-karma "abaddon_empowered" doubling HP to 7500 is still a 5-hit fight with this loadout.
