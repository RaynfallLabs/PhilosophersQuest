---
id: balance-death-chase-prayer-loop
dimension: balance
severity: P1
title: Death-chase trivialized by prayer-freeze loop — Fisher King double-halving makes Death lock down 15-30% of escape turns
status: open
systems: [death_chase, theology, quirks, mystery_system]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_a.json:death_chase_difficulty.freeze_method ("min(8, 3+effective_chain)")
  - balance_curves_agent_a.json:death_chase_difficulty.prayer_cooldown_base ("100-280 turns")
  - balance_curves_agent_a.json:death_chase_difficulty.compound_halving_means ("with both Fisher King quirks active, prayer cooldown can drop to floor of 1")
  - src/game_divine.py:780 (`p.prayer_cooldown = max(100, 80 + effective * 25)`)
  - src/game_divine.py:781-782 (fisher_king_active: `p.prayer_cooldown = max(1, p.prayer_cooldown // 2)`)
  - src/game_divine.py:783-785 (fisher_king_mystery_active: another `// 2`)
  - src/game_divine.py:792-797 (Death-freeze granted; `freeze_turns = min(8, 3 + effective)`)
  - src/monster.py:1057-1059 (DeathMonster._frozen_turns decremented per turn)
discovered: 2026-05-15
---

## What's out of balance

The Death-chase escape is supposed to be the game's terror moment. Player carries the Stone from F100 back up to F1, with Death pursuing at escalating speed (50→75→100→125% per `_maybe_escalate_death` src/main.py:1283-1316). Death is invulnerable. The only mechanic to slow Death is prayer-freeze: a successful theology quiz with chain N produces `min(8, 3+N)` turns of Death-freeze.

Cooldown math in `game_divine.py:780`:
- Base cooldown: `max(100, 80 + effective*25)` — at effective chain 5, cooldown = 205 turns.
- Freeze duration at effective 5: `min(8, 3+5) = 8` turns.
- Ratio: 8/205 = 3.9% of turns frozen. Reasonable.

But **Fisher King** quirk (game_divine.py:781-782) halves cooldown: 205/2 = 102. **Fisher King mystery** (game_divine.py:783-785) halves AGAIN: 102/2 = 51. With both active, freeze ratio = 8/51 = **15.7%** of turns locked.

At lower chains the ratio gets worse: effective chain 8 (perfect) → freeze 8 turns / cooldown ceil((80+200)/4)=70 → 11.4%. Effective chain 3 → freeze 6 turns / cooldown ceil((80+75)/4)=39 → 15.4%.

**At chain 1**: cooldown = max(100, 80+25)/4 = max(25, 26)/floor = 25 turns. Freeze = 4 turns. **Death is frozen 16% of the time even on a poor theology quiz**.

Combine with: player escapes F100→F1 over hundreds of turns. The "scariness" of Death depends on the player NOT being able to pray every 25-50 turns. With the Fisher King quirks, prayer is available on every floor transition, every danger moment, every stair-rest.

## Curve evidence

- `death_chase_difficulty.speeds_by_floor_during_escape`:
  - F76-100 (immediately post-L100): 50% speed — Death takes half-turns, easy to outrun
  - F26-50: 100% speed — matched
  - F1-25: 125% speed — outpacing the player
- Player turn budget vs Death turn budget at 125%: per 100 player turns, Death gets ~125 actions. Subtract 15.7% frozen = ~106 actions. That's slightly above player rate but with prayer breathing room. Without Fisher King quirks: per 100 player turns Death gets 125 actions, 3.9% frozen = 120 actions — meaningfully scarier.
- `freeze_method` text in deliverable: "freeze_turns = min(8, 3+effective_chain) on threshold quiz"
- `compound_halving_means` in deliverable: with both Fisher King quirks the cooldown can drop to floor of 1; that means in extreme cases prayer is available every single turn, and Death can be frozen 100% of the time.

## Suggested re-tuning

Three options:

1. **Cap the Fisher King halving** — prayer cooldown floor should be 60-80 turns minimum, regardless of quirks. Add `max(60, p.prayer_cooldown // 2)` instead of `max(1, ...)` in both halving branches.
2. **Decouple prayer-freeze from prayer healing** — make Death-freeze a dedicated theology challenge that has its own cooldown (e.g. one freeze per 100 turns), independent of healing prayer cooldown. This way the player still gets life-saving heals but can't freeze-loop Death.
3. **Diminishing returns on freeze** — each subsequent freeze in the same escape grants half duration. First freeze 8t, second 4t, third 2t, fourth 1t. After ~5 freezes the freeze becomes useless.

Recommended: option 2 — preserves the prayer/healing economy but restores the terror of Death.

## Notes

Cross-system: theology subsystem (game_divine.py), Power-quirk Fisher King (quirk_system.py), mystery_system.py (Fisher King mystery), DeathMonster mechanics (monster.py:1006-1078), and chase escalation logic (main.py:1283).

The Fisher King mystery is one of the seven mystery-system rewards (mystery_system.py). It's intended to be a meaningful prayer reward, but combined with the Fisher King quirk it produces an unintended balance double-dip. Without these two quirks active, Death-chase math is appropriately threatening (3.9-8% lockdown ratio at chain 5+). The "is it scary?" answer depends entirely on whether the player has these two quirks — a binary outcome which breaks tension.

Also worth noting: the freeze cap is min(8, 3+chain), but no upper bound on cooldown sub-1-turn means a player who has these quirks AND a Mystery prayer-pillar AND chain 8 could conceivably loop perpetually. Verify in play-test.
