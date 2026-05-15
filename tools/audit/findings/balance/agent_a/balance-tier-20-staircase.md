---
id: balance-tier-20-staircase
dimension: balance
severity: P2
title: Generic gear introduced only every 20 floors (L1/21/41/61/81) — the mid-band feels barren outside unique drops
status: open
systems: [weapons, armor, accessories, dungeon_progression]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_a.json:weapons_by_min_level (clusters: L1=25, L21=26, L41=25, L61=22, L81=22)
  - balance_curves_agent_a.json:armor_by_min_level (clusters: L1=23, L21=18, L41=18, L61=20, L81=12)
  - balance_curves_agent_a.json:shields_by_min_level (one per L1/11/21/31/41/51/61/71/81 generic + uniques)
  - balance_curves_agent_a.json:accessories_by_min_level (clusters: L1=36, L8=49, L25=30, L45=11, L65=15)
discovered: 2026-05-15
---

## What's out of balance

The generic equipment tier system is locked to a strict 20-floor cadence:

| Weapon tier | min_level | count |
|---|---|---|
| iron / bronze | 1 | 25 |
| steel | 21 | 26 |
| hardened gold | 41 | 25 |
| diamond | 61 | 22 |
| adamantine | 81 | 22 |

| Armor tier | min_level | count |
|---|---|---|
| padded / leather / bronze | 1 | 23 |
| iron | 21 | 18 |
| steel | 41 | 18 |
| plate / diamond | 61 | 20 |
| dragonscale / adamantine | 81 | 12 |

| Accessory cluster | min_level | count |
|---|---|---|
| plain rings | 1 | 36 |
| stat rings T1 | 8 | 49 |
| stat rings T2 | 25 | 30 |
| stat rings T3 (philosopher tier) | 45 | 11 |
| stat rings T4 | 65 | 15 |

Between these clusters, generic gear is **absent**. Unique artifacts fill some gaps (Mjolnir Shard L10, Sword of Damocles L12, Achilles's Spear L20, Hrunting L50, Excalibur L60, Tyrfing L70, etc.) but they're RNG drops, not reliable upgrade ladder.

This means in floors F2-F20, F22-F40, F42-F60, F62-F80, F82-F100 the player's GENERIC gear quality is locked — they can only upgrade if they get a unique drop. In an unlucky run with no uniques in band, the player relies on the same gear for 18-20 floors while monster HP and damage scale up.

Monster HP scaling for context (deliverable):
- F1: avg ~4 HP
- F21: avg ~27 HP (iron sword chain 5 = 16 dmg = 2 hits per mob) ✓ paced
- F41: avg ~141 HP (steel sword chain 5 = 22 dmg = 6-7 hits per mob) — feels slow
- F61: avg ~501 HP (gold sword chain 5 = 29 dmg = 17 hits per mob) — feels brutal
- F81: avg ~1018 HP (diamond sword chain 5 = 36 dmg = 28 hits per mob) — adamantine sword chain 5 = 48 dmg = 21 hits — small relief but still huge

The damage gap between generic tier and monster HP grows: at F61 a generic gold weapon takes 17 hits per mob, when each hit requires a chain-build (math quizzes). Players run out of SP, miss chain answers, take damage in return. This is the design — but the gap between unique weapons (which solve this) and generics (which don't) is widening.

## Curve evidence

- The 20-floor cadence shows in deliverable `weapons_by_min_level` histogram and the F70-F81 dead band already flagged in `balance-dead-band-71-80`.
- Within each 20-floor block, the deliverable shows ~2-6 unique weapons (e.g. L25 Staff of Moses, L30 Khopesh of Anubis, L35 Gilgamesh's Axe, L38 Cronus's Scythe within the 21-40 block). These are *the only* mid-block weapon power-ups.
- Compare to a hypothetical even cadence: a new generic tier every 10 floors (L1/11/21/31/41/51/61/71/81/91) would give 9 generic tiers. Currently 5.

## Suggested re-tuning

Two paths:

1. **Add intermediate generic tiers at L11, L31, L51, L71, L91** — each tier ~10-15 weapons with stats halfway between adjacent tiers. e.g. L31 bronze sword baseDmg 9 (between iron 6 and steel 8 / between steel 8 and gold 10). This doubles the generic cadence from 5 to 10 tiers and smooths the per-floor power curve.
2. **Increase unique-drop weights in mid-bands** — the floorSpawnWeight dict per unique weapon controls drop rates. Currently uniques are very rare in non-target bands. Boosting weight by 2-3x in the mid-block (e.g. Hrunting L50 spawning more reliably in F45-F55) gives players reliable upgrade options.

Option 1 is more disruptive but solves the curve issue. Option 2 is cosmetic and may still RNG-screw unlucky runs.

## Notes

Cross-system: weapons × armor × accessories × monster HP scaling × the math chain economy. The 20-floor cadence may be an artifact of historical design — five "tiers" with five Roman/medieval-themed metals (iron/steel/gold/diamond/adamantine). Adding intermediate tiers requires naming and theming work.

This is P2 not P1 because unique artifacts genuinely DO fill many gaps for lucky runs. But the variance is too high — a player who finds Achilles's Spear at F20 cruises to F40, while a player who finds nothing struggles. Reducing this variance is BALANCE territory.

Cross-reference `balance-dead-band-71-80` for the worst-case manifestation of this pattern.
