---
id: balance-time-freeze-vs-abaddon
dimension: balance
severity: P2
title: Time Freeze spell vs Abaddon — 5 free turns of perfect-chain damage = 30%+ HP off the final boss
status: open
systems: [spells, bosses, magic, math_subsystem]
floors_affected: [60, 100]
evidence:
  - balance_curves_agent_a.json:spells_by_tier (Time Freeze T5, 20MP, "Freeze all monsters for 5 turns")
  - balance_curves_agent_a.json:boss_stats.abaddon (HP 5000)
  - balance_curves_agent_a.json:weapons_by_min_level (Excalibur L60 mult[10]=10x, baseDmg 22 → 220 per perfect chain swing)
  - src/spells.py:104-108 (time_freeze_spell definition)
discovered: 2026-05-15
---

## What's out of balance

Time Freeze is a T5 spell: 20 MP, "Freeze all monsters for 5 turns. The ultimate emergency." Sourced from data/items/spellbook.json (L60 — Spellbook of Time Freeze).

Mechanically, freeze stops ALL monsters for 5 player turns. Player is free to:

- Cast more spells
- Wield + chain attack
- Drink potions
- Wait for the chain to optimize

Vs Abaddon (HP 5000): 5 turns of unopposed damage. With Excalibur (220 dmg/chain-10) plus Heroism + Empower buffs:

- 5 turns of chain-7 (typical sustained): Excalibur chain-7 mult = 4.5, 22*4.5 = 99 dmg/swing. 5 swings = 495 dmg. 10% of Abaddon HP free.
- 5 turns of chain-10 (top): 220 dmg/swing × 5 = 1100 dmg. **22% of Abaddon HP gone, no counter-attack.**
- 5 turns of disintegrate spam (if disintegrate works against Abaddon — it does 4d8 to bosses, 4d8 avg 18 × 5 = 90 dmg, weak): negligible
- 5 turns of meteor (T4 5d8 to all visible): 23 avg dmg × 5 = 115 dmg

The Excalibur path is dominant. A skilled player who lands chain-10 5 times in 5 turns clears 22% of Abaddon's HP for one cast of Time Freeze (20 MP).

**Combined with**: 
- Tyrfing chain-8 (8.5 mult) at 36 baseDmg = 306 dmg/hit, 5 hits = 1530 dmg (30.6% of Abaddon)
- Battle Trance / Atlas Burden (heroism) + Empower spell (next melee 3x dmg) — if chained correctly, a single Time Freeze period could output 2000+ dmg

The Abaddon fight is supposed to test the player's math under combat pressure. Time Freeze removes that pressure for 5 turns. With **two** Time Freeze spellbooks (rare but possible), the player has 10 free turns — potentially 60-80% of Abaddon's HP cleared without retaliation.

## Curve evidence

- `spells_by_tier`: "Time Freeze" T5 quiz_tier, mp_cost 20, effect "time_freeze", desc "Freeze all monsters for 5 turns. The ultimate emergency."
- Abaddon HP from `boss_stats.abaddon.hp`: 5000
- Player max_mp at INT 20+ (boost from Heart of Ahriman L70 +5 INT, Idunn's Apple gives CON not INT, Amulet of Merlin +5 INT): 20+24 = ~44 max_mp at INT 20-24
- 44 MP / 20 MP per Time Freeze = 2 castings before rest (or 3 with arcane_surge quirk auto-restoring MP)
- The boss takes piercing damage that bypasses armor: `boss_stats.abaddon.attacks` include 6d10+8 piercing apocalypse_blast. But during Time Freeze, the boss casts nothing.

## Suggested re-tuning

1. **Bosses are immune to time_freeze** OR have a 75% resistance (treats 5 turns as 1-2 turns).
2. **Time Freeze cooldown after casting** — once cast, can't cast again for 50+ turns. Prevents multi-cast cheese.
3. **Time Freeze costs more MP against bosses** — increment cost by 20 per boss in visible range (1 boss = 40 MP, hard to afford).

Option 1 is cleanest. The spell description "ultimate emergency" suggests it's meant for swarms of normal mobs — making bosses immune preserves that role while protecting boss-fight integrity.

## Notes

Cross-system: spells (Time Freeze definition) × boss mechanics (Abaddon fight design) × weapons (chain multipliers stacking on free turns) × MP economy (multiple casts possible).

The interaction with Excalibur is particularly notable because Excalibur's 10x chain mult was already flagged in `balance-weapon-chain-superlinear`. The two compound: Excalibur alone makes Abaddon clearable in ~23 hits at perfect chain; Time Freeze alone gives 5 free turns; combined they trivialize the F100 fight for a T5-math-capable player.

This is in tension with the design intent — Abaddon should be a true wall. The CONTEXT.md cites Abaddon as the Act II climax. If the player has Excalibur + Time Freeze + Heroism stack, Abaddon falls in 3-4 minutes of focused play.

For the kid audience: a kid who reaches F100 with these tools has already demonstrated mastery (cleared 99 floors, found two artifacts, learned T5 math + science). At that point the question is whether the BOSS fight is the actual test, or whether the test is the journey TO the boss. Currently it's the journey.
