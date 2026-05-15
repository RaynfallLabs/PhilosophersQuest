---
id: balance-shield-desert
dimension: balance
severity: P2
title: Shield slot underprovisioned — 21 total shields, several +0/+1 AC bands spanning 20+ floors
status: open
systems: [shields, monsters, geography_subsystem, combat]
floors_affected: [1, 80]
evidence:
  - balance_curves_agent_a.json:shields_by_min_level (21 total: wooden L1 +1, hide L11 +1, Spartans L12 +3, iron L21 +2, Ancile L30 +3, bronze L31 +2, steel L41 +2, Svalinn L50/55 +4, mithril L51 +3, Scutum L60 +5, crystal L61 +3, ...)
  - balance_curves_agent_a.json:weapons_by_min_level (194 weapons)
  - balance_curves_agent_a.json:armor_by_min_level (135 armor pieces)
  - data/items/shield.json (21 entries total)
  - data/items/weapon.json (194 weapons)
discovered: 2026-05-15
---

## What's out of balance

The shield slot has just **21 items** in the entire game — compared to 194 weapons, 135 armor pieces, and 195 accessories. That's a 9-1 weapon-to-shield ratio, and the geography subject (shield equipping per CLAUDE.md spine) is supposed to be a meaningful action loop.

Worse, the shield AC curve has long plateaus:

- L1-L10: wooden_shield +1 only (10 floors, +1 AC)
- L11-L20: hide_shield +1 (same AC) and Spartans +3 (unique, gated by quiz_tier; L12-30 only via floorSpawnWeight)
- L21-L30: iron +2 (same AC as Spartans? no, +2 vs +3 — Spartans wins)
- L41-L50: steel +2 (no AC improvement over iron despite 20 floor delta)
- L51-L60: mithril +3, Scutum_of_Aeneas +5 (unique)
- L61-L70: crystal +3 (no improvement over mithril)
- L71-L80: obsidian +3 (no improvement over mithril/crystal across 20 floors)
- L81-L100: dragonscale +4, adamantine +4

The generic shield tier ladder: +1 → +2 (L21) → +2 → +3 (L51) → +3 → +3 → +4 (L81). That's just **four meaningful AC improvements** across 100 floors. By contrast armor has 17 meaningful upgrade tiers across the same range.

**For the geography subject** (per the subject-action mapping in CLAUDE.md), this means there are far fewer reasons to engage with shield-equip than with other equip actions. A player who finds a wooden_shield at F1 has no incentive to engage with a geography quiz again until they reach F12 (Shield of the Spartans) or F21 (iron). That's a huge gap in subject-engagement.

## Curve evidence

- Shield introductions histogram (deliverable):
  - L1: 1 (wooden)
  - L11: 1 (hide — same +1 AC as wooden)
  - L12: 1 (Spartans unique +3)
  - L21: 1 (iron +2)
  - L30: 1 (Ancile unique +3)
  - L31: 1 (bronze +2 — same AC as iron from 10 floors prior)
  - L41: 1 (steel +2 — same AC again)
  - L50-65: mithril +3, Svalinn +4, Scutum +5, crystal +3, Aegis +5/+6
  - L71-100: obsidian +3, dragonscale +4, adamantine +4, tower_shield_ajax +6 (L65 dominant)
- Compare armor introductions (deliverable):
  - L1 (23), L21 (18), L41 (18), L61 (20), L81 (12) — generic tiers in groups of ~18-20 items
  - Plus 11 unique L22-L70 artifacts filling the gaps
- Tower Shield of Ajax (L65, +6 AC) is best-in-slot for floors 65-100 with no competitor — 35 floors of dominance from a single unique drop.

## Suggested re-tuning

Two complementary changes:

1. **Add a generic shield mid-tier** — introduce 3-5 new generic shields at L31 (+2 → +3 step), and L71 (+3 → +4 step). This smooths the AC curve and gives shield-equip a real reason to trigger every 10-15 floors.
2. **Add unique shield artifacts** at L40 and L80 to match the mini-boss cadence. Examples: a Shield of Athena (L40, +4 AC, reflects gaze attacks — pairs with Medusa boss), a Shield of Aeneas (L80, +5 AC, fire resist — pairs with frozen Asgard themes).
3. **Spawn-weight rebalance**: currently shields share spawn slots with armor. Verify in floorSpawnWeight whether shields are appearing often enough; players may go entire 20-floor stretches without ever seeing a shield drop simply due to RNG.

## Notes

Cross-system: shields × monster damage curve × geography quiz frequency × the equip-loop in CLAUDE.md's subject mapping. The Power-curve in deliverable also shows the player has TWO weapon slots (`weapon` + `ranged_weapon` per player.py:54-55) but only one shield slot — so shields are inherently lower-priority gear which the player wears once and then forgets unless a strict upgrade appears.

The bones system (`bones.py:103`) sets default ghost max_hp=50 but I don't think bones carry shield info. Verify with CODE auditor if shield items survive into bones — if so, the shield desert is amplified by ghost-shield carry.
