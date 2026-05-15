---
id: balance-score-economy-stone-bonus-dominates
dimension: balance
severity: P3
title: Score economy: 50000 Stone bonus dominates all other categories; grades S/A+/A are gated almost entirely by reaching L100 with Stone
status: open
systems: [score, grades, progression_rewards]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:score_economy
  - src/main.py:1478-1507 (_calc_score and _get_grade)
discovered: 2026-05-15
---

## What's out of balance

`balance_curves_agent_b.json :: score_economy`:
```
per_turn      = 10
per_max_floor = 1000
per_kill      = 100
stone_bonus   = 50000
grades: S=200000, A+=100000, A=60000, B+=30000, B=15000, C=7000, D=3000, F=0
```

Without stone bonus:
- Reaching L100 (max_level_reached 100) = 100 * 1000 = 100,000 from floors
- Plus ~5000 turns of play * 10 = 50,000
- Plus ~300 kills * 100 = 30,000
- Total = ~180,000 → grade B+

With stone bonus:
- Same totals + 50,000 = ~230,000 → grade S

Without ever reaching L100:
- Max realistic floor 80, ~3000 turns, ~150 kills
- 80*1000 + 3000*10 + 150*100 = 80,000 + 30,000 + 15,000 = 125,000 → grade A+

Wait, that's already A+. Re-check: a player who reaches L80 (Fenrir kill = ~150 kills, ~3000 turns) gets ~125,000 = A+. A player who clears L100+Stone gets S (~230,000). The MARGINAL value of pushing from L80 to L100 is +20*1000 (floors) + ~2000*10 (turns) + ~100*100 (kills) + 50,000 (stone) = +90,000.

So the Stone bonus is worth 50000/90000 = 55% of the L80→L100 jump. The other 45% is the natural per-floor/per-kill accumulation.

**That's correctly balanced.** Stone bonus is meaningful but not the whole story. The grade thresholds (S 200k, A+ 100k) DO reflect a real curve.

The problem is more subtle: **per_turn × per_max_floor encourages slow play**. A player who farms the same floor at L80 for 100 turns gets 1000 points (100 turns * 10). A player who descends L80→L99 quickly gets ~19,000 (19 new floors * 1000). The DESCEND-FAST strategy dominates per-grade-tier.

Compare to NetHack scoring which discourages turn-farming via diminishing returns. PQ's flat per_turn=10 means a player who plays a 30-hour run gets a flat bonus. That's not balance-breaking but it does mean a single very-long run can grade S without reaching L100, by sheer turn-accumulation.

Math: 200000 / 10 = 20,000 turns just from turn count to hit S. At 1 turn/second, 20,000 turns = 5.5 hours of clicking. A patient player who waits in safe rooms for 20,000 turns hits S without reaching the Stone.

## Curve evidence

`balance_curves_agent_b.json :: score_economy.per_turn = 10` is the lever. Combined with the `wait` action (no time cost in real life beyond pressing `.`), this is an idle bonus.

`src/main.py:1485` computes: `self.turn_count * 10 + max_level_reached * 1000 + monsters_killed * 100 + (50000 if has_stone else 0)`.

## Suggested re-tuning

1. **Diminishing returns on turn count**: 10 per turn up to 1000 turns, then 5, then 1. Caps the "wait-to-S-grade" exploit.
2. **Per-turn bonus only counted when player is in danger** (visible hostile monster on screen). Removes idle farming.
3. **Reduce per_turn to 2-5**: caps the turn-economy contribution.

(1) is cleanest. The play-test rule applies: a kid waiting in a corner for hours to grade up is a real failure mode.

## Notes

- P3 not P2 because the kid playing for hours isn't actually a balance break — they DO learn quizzes during the play. But the grade is supposed to reflect ACHIEVEMENT, and 20000 turns of waiting is achievement-poor.
- Cross-system: turn_count + score_economy + grade thresholds + (implicit) the kid-reward economy. If grade S unlocks the prestige code, and S can be gained by waiting, the reward semantics drift.
- The Stone bonus 50k is the most "real-world relevant" reward (it gates the chronicle "I made it" + the most prestigious code) and it IS proportional. The OTHER score categories are the weak link.
