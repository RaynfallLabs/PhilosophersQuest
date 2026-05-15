---
id: balance-prayer-freeze-cheap-and-stackable
dimension: balance
severity: P2
title: Prayer-freeze of Death triggers on chain=0 (effective=1 at altar), with multiple altars and Fisher-King halving stacking
status: open
systems: [prayer, theology, death_chase, quirks, dungeon_gen]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:death_chase_difficulty.freeze_turns_formula
  - src/game_divine.py:747 (effective = chain + (1 if at_altar else 0))
  - src/game_divine.py:791-797 (freeze_turns = min(8, 3 + effective))
  - src/game_divine.py:780-785 (Fisher King halves cooldown TWICE)
  - src/quirk_system.py:1492 (fisher_king effect: prayer cd permanently halved)
discovered: 2026-05-15
---

## What's out of balance

CONTEXT.md describes prayer-freeze as a *desperate measure*: a high-tier theology chain that buys turns. The code permits an effective-1 prayer to freeze Death:

```python
# game_divine.py:747
effective = chain + (1 if at_altar else 0)
# game_divine.py:791-797
if self.death_pursues and self.death_monster is not None:
    freeze_turns = min(8, 3 + effective)
    self.death_monster._frozen_turns = freeze_turns
```

The minimum: chain=0 at altar = effective 1 = **4 turns of Death frozen**. A player who tanks the theology quiz still gets 4 turns of immunity. There's no minimum-chain gate.

Second mechanic stack: prayer cooldown after a *failed* prayer (chain=0) is `max(100, 80 + 0*25) = 100 turns` (`game_divine.py:780`). Fisher King quirk halves it (line 781-782), and `fisher_king_mystery_active` halves it AGAIN (line 784-785) → effective **25-turn cooldown** for an unlocked Fisher King player. Death moves at 100% speed for floors 26-50, so 25 turns = 25 Death-moves, but you re-freeze for 4 more turns every 29 turns. Net: Death moves ~25/29 = 86% of the time *if you're at chain 0*. With chain 3 (entirely achievable on T1 theology), it's 8-turn freezes on a 25-turn cooldown — Death moves <33% of the time.

Third stack: altars are placed by `dungeon._create_judgment_altar` and through normal floor gen. Multiple altars on a floor = multiple +1-effective rolls per floor without leaving altar tiles. Plus `at_altar=True` adds +1 effective baseline.

## Curve evidence

`balance_curves_agent_b.json :: death_chase_difficulty.freeze_turns_range` documents the 4-8 turn band. `quirks[id=fisher_king].effect = "Prayer cooldown permanently halved"`. The combined stack (4-turn floor + Fisher King halving + mystery halving) is the cross-system bug: each individual lever was tuned in isolation, the product is too cheap.

This is the *intended* desperation tool. Code-side it's a passive vending machine.

## Suggested re-tuning

1. Add a minimum effective requirement: `if effective < 3: no freeze; effective 3 = 3 turns, scale 1 turn per effective up to 8`.
2. Cap Fisher-King-style cooldown reductions to a single 50% reduction. Stacking two halvings produces a 4x reduction.
3. Set prayer cooldown floor higher when Death is active — e.g. `max(150, ...)` only while `death_pursues`. The chase should *eat* the player's prayers; once you've prayed, you can't safety-net for ~150 turns.

## Notes

- Speculation: the same effective=1 weirdness probably exists for other prayer outcomes (e.g. the L100 holy-fire altar stripping Abaddon resistances for `chain*2` turns — at chain 0 + altar that's `chain*2 = 0` turns, so harmless there, but verifies the dual-counting habit).
- This finding pairs with `balance-time-stop-trivializes-death-chase.md`; closing one and not the other still leaves the chase soft.
- The fisher_king effect description in `_QUIRK_EFFECTS` says "Prayer cooldown permanently halved" — but code halves TWICE if both `fisher_king_active` and `fisher_king_mystery_active` are set. Either intentional double-dipping (then doc the multiplicative stack) or a bug.
