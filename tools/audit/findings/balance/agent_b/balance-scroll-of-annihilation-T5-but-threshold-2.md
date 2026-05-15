---
id: balance-scroll-of-annihilation-T5-but-threshold-2
dimension: balance
severity: P3
title: scroll_of_annihilation: T5 grammar but threshold 2 — needs only 2 correct in 4 questions to wipe everything in sight
status: open
systems: [scrolls, quiz_engine, monsters]
floors_affected: [30, 100]
evidence:
  - balance_curves_agent_b.json:scrolls_by_min_level (scroll_of_annihilation quiz_tier 5, quiz_threshold 2)
  - data/items/scroll.json:scroll_of_annihilation (min_level 30, effect "annihilate")
  - balance_curves_agent_b.json:scrolls_by_min_level (scroll_of_genocide quiz_tier 4, threshold 4 by contrast)
discovered: 2026-05-15
---

## What's out of balance

`scroll_of_annihilation` (`data/items/scroll.json`):
- `quiz_tier: 5` (high-school)
- `quiz_threshold: 2` (need 2 correct in N attempts)
- `read_threshold: 2`
- Effect: "every creature in sight dissolves" — clears the floor.

T5 threshold 2: in threshold mode (per `tests/test_balance.py` semantics) the player must answer 2 correctly out of (typically) 4 attempts. T5 questions are hard, but with 4 tries to get 2, the chance for a player who knows ~50% of T5 grammar is high (binomial 50%/4/≥2 = 68%).

Compare:
- `scroll_of_genocide` (`data/items/scroll.json`): T4 grammar, threshold 4 — the player must answer 4 correct in N attempts (no extra slack). The genocide effect (erase species from level) is sub-equivalent to annihilation (clear visible monsters once); but its quiz cost is HARDER.
- `scroll_of_great_power`: T5 threshold 4 — properly hard, gives +1 all stats.

The annihilation scroll is the *most powerful* AOE in the game (genocide is similar but species-limited). Its threshold gate is the EASIEST among the late-tier scrolls.

`scroll_of_annihilation` is also spawnable from L30 onward (`floorSpawnWeight: {"30-40": 3, ...}`). A player who picks it up and identifies it has a floor-clear button from L30 to L100.

## Curve evidence

`balance_curves_agent_b.json :: scrolls_by_min_level` (sorted by min_level):

| scroll | min_level | quiz_tier | threshold | effect |
|---|---|---|---|---|
| scroll_of_annihilation | 30 | 5 | 2 | annihilate |
| scroll_of_thoth | 35 | 4 | 2 | identify_all |
| scroll_of_genocide | 40 | 4 | 4 | genocide |
| scroll_of_time_stop | 40 | 5 | ? | time_stop |
| scroll_of_great_power | 50 | 5 | 4 | great_power |

annihilation and great_power are both T5; annihilation has threshold 2, great_power has 4. Both are floor-spawnable. Both are massive. The threshold gating is inconsistent.

## Suggested re-tuning

Set `scroll_of_annihilation.quiz_threshold = 4` (match `scroll_of_genocide` and `scroll_of_great_power`). Effects of similar magnitude should require similar mastery.

Alternatively: lower the effect's reach. Currently "every creature in sight" — that's the entire visible FOV. Reduce to "every creature within 3 tiles" (close-quarters panic button instead of floor wipe).

## Notes

- P3, not P2, because the player still has to identify the scroll first (philosophy quiz), and an unidentified T5 scroll has a high mis-fire rate.
- Cross-system: scrolls (the quiz gate) + monsters (the wipe target). The "T5 means hard" promise is broken by the threshold-2 escape valve.
- The two known biased subjects (per `tests/test_balance.py:252-254` KNOWN_BIASED) include grammar. The "longest answer = correct" exploit could push a kid past T5 threshold 2 without genuinely understanding. Pairs with the question-bank length-balance backlog.
