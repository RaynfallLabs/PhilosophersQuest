---
id: balance-spell-int-scaling
dimension: balance
severity: P2
title: Spell damage scales linearly with INT — 25 INT = 3.5x damage; Smite at chain 5 hits 378 dmg/cast vs Fafnir 2500 HP
status: open
systems: [spells, magic, items_accessory, bosses]
floors_affected: [40, 100]
evidence:
  - src/game_magic.py:1095-1101 (`_spell_damage = base * mult * (1.0 + INT * 0.1)`; mults=[0.5,1.0,1.8,2.8,4.0])
  - balance_curves_agent_a.json:spells_by_tier (Smite T3, 6d8, chain-scales + INT)
  - balance_curves_agent_a.json:accessories_by_min_level (Amulet of Merlin L70 INT+5, Heart of Ahriman L70 INT+5, Amulet of archmage intellect L65 INT+5)
  - balance_curves_agent_a.json:boss_stats.fafnir.hp (2500)
  - balance_curves_agent_a.json:boss_stats.abaddon.hp (5000)
discovered: 2026-05-15
---

## What's out of balance

Spell damage formula (game_magic.py:1098-1101):
```
mult = _SPELL_CHAIN_MULTS[chain-1]  # [0.5, 1.0, 1.8, 2.8, 4.0]
damage = base_dmg * mult * (1.0 + INT * 0.1)
```

The INT term is **linear** with no cap. Every point of INT adds 10% damage. With base INT 10, mult = 2.0x. With INT 25 (achievable via three +5 INT amulets + brilliance buff): mult = 3.5x. With INT 30 (theoretical maximum with quirk-stacking): 4.0x.

**Compounding with chain mult 4.0x** at chain 5, the total multiplier is:
- INT 10: 4.0 × 2.0 = 8.0x base damage
- INT 20: 4.0 × 3.0 = 12.0x base damage
- INT 25: 4.0 × 3.5 = 14.0x base damage
- INT 30: 4.0 × 4.0 = 16.0x base damage

For **Smite** (T3, base 6d8 ≈ 27 avg):
- INT 10 chain 5: 27 × 8 = 216 dmg/cast (12 MP)
- INT 25 chain 5: 27 × 14 = **378 dmg/cast** (12 MP)

Vs Fafnir (HP 2500): 6.6 casts at INT 25, chain 5. Player MP at INT 25 = 30+24=54, enough for 4 casts. With Arcane Surge restoring all MP (1 use, free at quirk-unlock): 8 casts total = 3024 dmg. **Fafnir dies before even retaliating** if the player can keep chain.

For **Lightning Bolt** (T3, base 5d6 ≈ 17 avg) at INT 25 chain 5: 17 × 14 = 238 dmg/cast (10 MP).

For **Magic Missile** (T1, base 2d6 ≈ 7) at INT 25 chain 5: 7 × 14 = 98 dmg/cast (3 MP).

**3 MP for 98 dmg** is a 32 dmg/MP ratio at low cost. Player max_mp 54 = 1764 dmg per rest. A pure mage build can clear Fafnir in 25 missiles, all chain-scaled, T1 quiz only. This sidesteps the design intent that science (T3 quizzes) gates magic.

## Curve evidence

- INT-boost accessories (deliverable `accessories_by_min_level`):
  - L65 amulet of archmage intellect: +5 INT
  - L70 Amulet of Merlin: +5 INT
  - L70 Heart of Ahriman: +5 INT
  - L60 Ring of Scheherazade: +4 INT
- A player stacking 3 of these accessories: INT 10 + 15 = 25. The brilliance status (focused_scholar / arcane_surge quirks) adds +1 INT temporarily for 25 → 26.
- Spell base damages from deliverable `spells_by_tier`:
  - magic_missile T1: 2d6 (avg 7), 3 MP
  - fire_bolt T2: 4d6 (avg 14), 6 MP
  - lightning T3: 5d6 (avg 17), 10 MP
  - smite T3: 6d8 (avg 27), 12 MP
  - ice_storm T4: 4d8 (avg 18), 14 MP, mass
  - meteor T4: 5d8 (avg 22), 16 MP, mass
- Boss HP (deliverable `boss_stats`):
  - asterion L20: 800
  - medusa L40: 1500
  - fafnir L60: 2500
  - fenrir L80: 3000
  - abaddon L100: 5000

## Suggested re-tuning

1. **Cap INT contribution at +200%** (factor 3.0): `factor = min(3.0, 1.0 + INT * 0.1)`. This makes INT 20 = max scaling; further INT investments don't trivialize damage.
2. **Diminishing returns on INT**: replace linear with sqrt-like: `factor = 1.0 + sqrt(INT) * 0.3`. INT 10 → 1.95x, INT 25 → 2.5x, INT 36 → 2.8x. Same baseline but flatter top.
3. **Make boss resistances bite more**: Abaddon's `resistances` includes magic in some lore — but `attack_effects` shows physical attacks dominate. Add a 50% magic resistance to bosses to halve incoming spell damage.

Option 2 is most elegant — preserves INT as the primary mage stat without runaway scaling.

## Notes

Cross-system: spells × accessories × bosses × player stats. This is in tension with `balance-weapon-chain-superlinear` — both melee (Excalibur chain-10) and magic (INT-stacked spells) have damage explosions at the top end. The wall placement is consistent (T5 quiz / T3 quiz tiers gate access), but the consequence is that a *skilled* player at any character build wins by a lot, and a *less-skilled* player struggles.

The `_SPELL_CHAIN_MULTS` cap at chain 5 (mult 4.0) is the right shape — capped, finite. The INT term is the unbounded one. Fix the INT scaling, not the chain mult.

Verify: the brilliance status effect adds INT+1 WIS+1 (status_effects.py expiry path) — same heroism-style asymmetry might affect brilliance applied via quirks. See `balance-power-quirk-heroism-broken` finding for the broader pattern.
