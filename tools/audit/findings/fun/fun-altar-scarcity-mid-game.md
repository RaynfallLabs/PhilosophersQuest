---
id: fun-altar-scarcity-mid-game
dimension: fun
severity: P3
title: "Altars appear every 15 floors — 25-floor gaps make prayer feel like a once-per-act ritual"
status: open
systems: [altars, prayer, dungeon_gen, hp_economy]
when_it_hits: "Floors 17-30 and 32-45 — long gaps between altars where prayer is essentially shelved"
evidence:
  - src/dungeon.py:326-336
  - src/main.py:498
  - src/game_divine.py:682-728
  - fun_pacing_trace.md#ambient-life-at-l10
discovered: 2026-05-15
---

## The friction or flatness
Altars spawn deterministically: `if level % 15 == 1` (`dungeon.py:327`). This places altars on **L1, L16, L31, L46, L61, L76, L91** — seven altars total in the 99-floor procedural dungeon, plus the L100 boss ring.

Prayer (`game_divine.py:682-728`) is theology escalator chain with 100-280 turn cooldown. Prayer at an altar is **2x more powerful** at every chain tier (`game_divine.py:747`: `effective = chain + (1 if at_altar else 0)`). The altar bonus is significant: it converts a chain-3 prayer (minor cleanse) into a chain-4 prayer (SP renewal), or a chain-5 (HP restore) into chain-6 (half HP + full SP).

This means prayer's *full impact* is gated by altar presence. Between altars — L17 through L30, for example — the player can pray but only at half effectiveness. Most players will *save* their prayer cooldown for the next altar floor.

Result: prayer essentially fires **5-7 times in a full run** (once or twice per altar). The system is meaningfully gated by altar scarcity in a way that makes it feel like a once-per-act ritual rather than an ongoing tool.

For a P1 system (theology is a high-stakes subject with the longest timer, designed for desperate moments), prayer's actual frequency is closer to *occasional ritual* than *desperate measure*. The flavor of "kneel and pray, the heavens answer" lands beautifully once or twice — but the *practical* role in the loop is too rare to be a tool the player learns to wield.

Counter-evidence: the Death-chase chase use of prayer to freeze Death (`game_divine.py:792-797`) IS a "desperate measure" moment, and the prayer cooldown does fit there. The friction is in the descent, where prayer's gated-by-altar nature makes it less of a tactical tool than the system seems to promise.

## When and how often it fires
- Every run, all the time, between altar floors. The 15-floor gap at L17-30 is the most acute "I have prayer charges but no altar to use them powerfully" stretch.

## Suggested redirect
- **Mystery altars count as altars for prayer purposes** when player meets the key requirement. (`mystery_system.py` altars are different objects than dungeon ALTAR tiles. They don't grant the prayer 2x bonus.) This would lift altar density during the L20-50 band where mysteries cluster.
- **Add 1-2 *shrine* tiles per floor** at random — a weaker altar effect (50% bonus instead of 100%, single-use per floor). Available at every floor. Lets the player pray usefully without the heavy gating, while preserving the *full* altar's narrative weight.
- **Or**: leave altar count as-is but explicitly mark altar floors in pre-floor messaging. "You feel a presence at this depth" on L16, L31, L46 (when the player enters). Players plan their prayer cooldown around it.

## Notes
Altars also serve BUC identification (`game_encounters.py:235`) and BUC upgrade (`game_encounters.py:184`). Their rarity makes those *more* impactful. The finding isn't "more altars please" — it's that **prayer's role in the loop is structurally crippled by altar scarcity**, and the system has a richer life if altar-effective prayer can happen at intermediate-power locations between full altars. Spans altars + prayer + dungeon_gen + HP economy.
