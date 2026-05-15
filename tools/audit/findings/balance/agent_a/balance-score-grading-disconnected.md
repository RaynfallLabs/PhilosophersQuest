---
id: balance-score-grading-disconnected
dimension: balance
severity: P3
title: Score grading thresholds (S=200k, A+=100k) don't correspond to game milestones — Stone bonus alone hits A+ regardless of skill
status: open
systems: [score_economy, bosses, dungeon_progression]
floors_affected: [50, 100]
evidence:
  - balance_curves_agent_a.json:score_economy.stone_bonus (50000)
  - balance_curves_agent_a.json:score_economy.grade_thresholds (S=200000, A+=100000, A=60000)
  - balance_curves_agent_a.json:score_economy (per_turn=10, per_max_floor=1000, per_kill=100)
  - src/main.py:1478-1507
discovered: 2026-05-15
---

## What's out of balance

Score formula (main.py:1478-1489):
```
score = turn_count * 10 + max_level_reached * 1000 + monsters_killed * 100 + (50000 if Stone else 0)
```

Grade thresholds (main.py:1491-1507):
- S: 200,000
- A+: 100,000
- A: 60,000
- B+: 30,000
- B: 15,000
- C: 7,000

Hitting **A+** (100k) requires:
- max_level 100 = 100,000 — but you also need Stone (+50000) — together 150k. Done. **Any victorious player gets A+ minimum.**
- Without Stone (escape before F100): max_level 99 × 1000 = 99,000. Close to A+. Add 1000 from turns/kills = A+.
- **Without victory**: max_level 60 × 1000 = 60,000 + turns + kills = A territory. Player dies at F60 still gets A grade.

Hitting **S** (200k) requires significantly more — Stone (50k) + max_floor 100 (100k) + a LOT of turns/kills (50k more = 5000 turns OR 500 kills). Achievable but takes patience.

**Problem**: the grade S is anti-correlated with efficiency. The S threshold rewards turn-padding (each turn = 10 points). A player who explores every corner of every floor (high turn count) scores higher than a player who beelines. **Efficiency penalty.**

Compare to the design intent (CONTEXT.md): "Major in-game milestones drop codes the player gives their father for real-world rewards." The code drops should align with grade milestones. But the grade system doesn't track:

- Secret Victory (`_trigger_abyss` — kill Death) — this is the highest narrative achievement but doesn't grant a separate score bonus
- Recall Lore depth (how many T5 hints discovered)
- Quirk count (how many quirks unlocked)
- Item identification rate
- Cooking mastery

Currently a player who:
- Wins normally (Stone + ascend): A+ minimum, ~150k
- Wins secret (Stone + Tablet → kill Death): same score formula (the abyss path destroys Death but doesn't add score)
- Dies at F60: A grade
- Dies at F99: A+ grade

**The score barely differentiates skill levels.** Beat Abaddon = A+. Got close = A. Mastered = A+ slightly higher. The S grade is unreachable without grinding turns.

## Curve evidence

- score_economy from deliverable:
  - per_turn: 10
  - per_max_floor: 1000
  - per_kill: 100
  - stone_bonus: 50000
- A baseline F100-victor: max_floor 100 × 1000 = 100,000. Plus stone 50,000 = 150,000. Plus typical 200 kills × 100 = 20,000. Plus 3000 turns × 10 = 30,000. Total ~200,000 — hits S.
- A grinder-victor: same plus 10,000 turns total × 10 = 100,000 extra. Total ~300,000. Still S, but inflated.
- The S threshold (200k) is essentially "win + don't speed-run."

## Suggested re-tuning

1. **Add a Secret Victory bonus** of 100,000-200,000 points. Currently `_trigger_abyss` (main.py:1373-1406) destroys Death but provides no score bump. The secret victory should grade S minimum.
2. **Add quirk-count bonus**: 5,000 points per unlocked quirk. 12+ quirks (a real run) = 60,000 bonus.
3. **Add lore-tier bonus**: 1,000 points per T1 hint discovered, scaling 2/3/4/5k for T2/T3/T4/T5. Encourages Recall Lore engagement.
4. **Reduce per_turn from 10 to 2-3** — removes the turn-padding incentive. Speed-running becomes neutral, not penalized.
5. **Add efficiency bonus**: completing the game in fewer than X turns grants a multiplier. Currently the formula REWARDS slow play; this would invert.

## Notes

Cross-system: scoring × bosses (Stone bonus) × dungeon progression (max_floor) × secret victory path × the kid-reward contract.

This is P3 because the grade system isn't broken — it works mathematically. But it's not telling the story it should. A kid who beats the secret-victory ending shouldn't get the same grade as a kid who barely scrapes through normal Abaddon. Currently they DO.

The reward-code economy (per CONTEXT.md "take this code to your father proudly") implies the codes are tiered. Look at how `_trigger_abyss` describes the code drop (main.py:1392): "you have shown true Wisdom and Courage." This SHOULD be the S-grade reward. Currently the same code drop fires for any Stone-pickup ascent.

Verify with VOICE auditor whether the reward code messages actually differentiate by grade.
