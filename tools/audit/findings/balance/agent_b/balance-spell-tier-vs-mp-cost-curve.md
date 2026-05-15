---
id: balance-spell-tier-vs-mp-cost-curve
dimension: balance
severity: P3
title: Spell quiz_tier weakly correlates with mp_cost; T1 spells exist with mp 15 and T5 spells with mp 18 — gating is incoherent
status: open
systems: [spells, magic, INT_scaling]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:spells_by_tier (39 spells, T1 mp range 2-15, T5 mp range 18-20)
  - src/spells.py:8-210 (LEARNABLE_SPELLS table)
discovered: 2026-05-15
---

## What's out of balance

The spell roster (`balance_curves_agent_b.json :: spells_by_tier`) shows mp_cost varies wildly within each quiz_tier:

| quiz_tier | spell count | mp_cost range | example outliers |
|---|---|---|---|
| 1 | 12 | 2-15 | sign_aard (3), army_of_darkness (15) |
| 2 | 9 | 4-10 | knock (4), elder_scream (10) |
| 3 | 11 | 6-12 | detect_monsters (6), smite (12), polymorph (9) |
| 4 | 5 | 7-16 | meteor (16), reflect (11), paralyze (12) |
| 5 | 2 | 18-20 | time_freeze (20), disintegrate (18) |

`army_of_darkness_spell` is the wildest outlier: quiz_tier 1, mp_cost 15, effect "summon_undead_horde." Tier 1 = 5th-grade-equivalent grammar (to read the spellbook) and science (to cast). But the effect — summoning an undead horde — is endgame-equivalent. The mp_cost 15 gates the spell via mana pool, BUT quiz tier should also gate.

Compare: T5 disintegrate_spell mp 18 = the player must answer 5 escalator-chain math/science questions (T5 is high-school) AND afford 18 MP. T1 army_of_darkness mp 15 only needs 5th-grade grammar to read the book + a science T1 to cast + 15 MP. A kid can cast army_of_darkness much earlier than they can cast disintegrate.

The dev intent for the Ash Williams jokes (army_of_darkness, "Give me some sugar, baby.") is clear — that spell is a flavor power for the Ash Williams hero. But it shouldn't be T1 castable by any player. Either it's locked to Ash (currently no such gate visible) or its tier should rise.

Similarly:
- `meteor_spell` T4 mp 16 — strong AOE, properly gated.
- `summon_guardian_spell` T3 mp 10 — modest.
- `polymorph_spell` T3 mp 9 — powerful (turn any monster into anything) at a mid tier.

## Curve evidence

`balance_curves_agent_b.json :: spells_by_tier` is the table. Total 39 spells. The T5 tier has only 2 spells (`time_freeze`, `disintegrate`) — both endgame-shaped. The T1 tier has 12 spells, mostly Witcher signs (sign_aard, igni, quen, yrden, axii) and Ciri's elder_blink/elder_charge — character-themed. This is a *content tier*, not a *power tier*. Then `army_of_darkness` at T1 sticks out.

## Suggested re-tuning

1. **Re-tier outliers**: army_of_darkness → T4. The character-flavor argument for Ash holds if his spellbook is gated to his character class.
2. **Add tier-gated cost minimum**: at quiz_tier T, minimum mp_cost = T * 3 (so T1 ≥ 3 MP, T5 ≥ 15 MP). army_of_darkness mp 15 already qualifies for T5 by cost, anomaly resolved by re-tiering.
3. **Document the asymmetry**: if T1 = "easy to read the spellbook" and mp_cost = "power gate", they're orthogonal. Then `army_of_darkness` mp 15 = "easy to learn, hard to cast often" is intentional. Player still needs to grind MP from cooked recipes/INT bumps. Defensible but should be explicit.

(3) is cheapest if the design is intentional; (1) is cleanest if not.

## Notes

- P3 because the worst outlier (army_of_darkness) has a 15 MP wall that DOES gate early-game use. At INT 10, max MP = 20 (10 + INT 10). So a starting player CAN cast it once. That's still spammable enough to break L1-L20.
- Cross-system: spells + INT scaling + spellbook drop floors. Spellbook for army_of_darkness — at what min_level does it drop? Quick check needed (not done in this finding).
- Speculation: if `army_of_darkness_spellbook` is min_level 50+, the early-game break vanishes. The spell tier could stay T1 with that gate in place.
