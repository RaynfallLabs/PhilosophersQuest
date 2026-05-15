---
id: balance-math-timer-vs-tier-escalation
dimension: balance
severity: P2
title: Math 16s/question budget collides with T4-T5 question complexity once weapon mathTier scales
status: open
systems: [quiz_engine, weapons, combat_tempo, tiers]
floors_affected: [41, 100]
evidence:
  - balance_curves_agent_b.json:quiz_timers.math (base 8s, wis_scale 0.8)
  - balance_curves_agent_b.json:weapons_by_min_level (sword_of_michael mathTier 5)
  - data/items/weapon.json (mathTier 1 at iron_sword L1; mathTier 5 at L60+ legendary)
  - src/player.py:18 (math: (8, 0.8) — 16s @ WIS 10)
  - src/quiz_engine.py (chain mode escalates on success)
discovered: 2026-05-15
---

## What's out of balance

The math quiz timer is intentionally short — 16s @ WIS 10 — so combat feels snappy. This is correct in design (per CONTEXT.md and `player.py:18` comment). The problem is that the QUESTIONS asked DURING combat are gated by the weapon's `mathTier`:

- iron_sword (L1): mathTier 1 → T1 math (5th-grade equivalent)
- steel_sword (L1): mathTier 2 → T2 math
- ... weapons with mathTier 3, 4, 5 exist throughout the curve
- sword_of_michael: mathTier 5 → T5 math (high-school equivalent)

A T1 math question at 16s is achievable for an 8-year-old. A T5 math question (algebra, multi-step) at 16s is brutal even for a 13-year-old. The **per-question** budget didn't scale with question difficulty.

CONTEXT.md explicitly says T5 = "high school (9th-10th grade)" and the audience is "younger than these tiers." A 5th-grader equipping the Sword of Michael — given to them automatically by the L99 karma judgment — must answer 9 T5 math questions IN A ROW within 16 seconds each, OR break their chain and lose the multiplier (and thus the boss fight).

The chain mode penalty: first wrong answer = chain score = chain length so far. So a player who can solve T1-T3 math in 16s but not T5 will hit a chain ceiling at whatever tier they tap out — which means their best weapon CAN'T be used at full power.

## Curve evidence

`balance_curves_agent_b.json :: quiz_timers.math.at_wis_10 = 16`. Compare to `theology.at_wis_10 = 65` and `cooking.at_wis_10 = 60`. The math timer is 4x tighter than the slowest quiz.

`balance_curves_agent_b.json :: weapons_by_min_level` shows `peak_damage` heavily weighted by chain length × multiplier. Sword of Michael peak_damage 720 assumes chain 9. At chain 1, damage is base 45 * 0.5 = 22 — *worse than iron_sword chain 1* (6 * 0.6 = 3.6, but the iron_sword max-chain is 6*3.2=19, so within similar range).

So a younger player wielding the L99 reward sword underperforms a starting iron_sword if they can't solve T5 in 16s.

## Suggested re-tuning

Two parallel fixes:

1. **Scale math timer with weapon mathTier**: when the active weapon has mathTier 4 or 5, add +4s and +8s respectively to math timer. The base 16s stays for T1-T3; T4 gets 20s, T5 gets 24s. Combat still feels snappy at low tiers but mirrors the gradient elsewhere.
2. **Cap weapon mathTier at the player's *current* mathTier capability**: track per-run highest successful math chain length and bound queried tier to that + 1. Removes the "young kid wields adult weapon" failure mode.

Option (1) is simpler and more transparent.

## Notes

- This is the right *direction* for design: math IS the combat tempo. But the tier-vs-time-budget multiplier matters.
- The MEMORY.md note says "math and grammar are the snappy-rote exceptions" — that's correct, but "snappy" should be a tier-1 baseline not a permanent ceiling.
- Cross-system: quiz_engine + weapons (mathTier metadata) + combat tempo. Pure quiz timer tuning would be single-system; weapon-mediated escalation is the holistic part.
- Speculation: similar issue may exist for cooking escalator_chain — at quality 5 the meal pulls T5 cooking, but `quiz_timers.cooking.at_wis_10 = 60`, generous. Cooking is fine. Math is the outlier.
