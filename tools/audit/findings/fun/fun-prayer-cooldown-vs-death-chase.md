---
id: fun-prayer-cooldown-vs-death-chase
dimension: fun
severity: P3
title: Prayer-freeze on Death is the chase's panic button, but cooldown gating makes it rare even at peak crisis
status: open
systems: [prayer, death_chase, theology_quiz, cooldowns]
when_it_hits: "Death-chase escape, particularly the 125% speed band L25-L1"
evidence:
  - src/game_divine.py:780-797
  - src/main.py:1283-1316
  - src/monster.py:1057-1072
  - fun_pacing_trace.md#checkpoint-f-the-death-chase-escape-post-l100
discovered: 2026-05-15
---

## The friction or flatness
The Death-chase escape has only one mechanic that *meaningfully* slows Death: prayer (`game_divine.py:792-797`). A successful prayer mid-chase freezes Death for `min(8, 3 + effective_chain)` turns — 4 to 8 turns depending on chain quality.

Prayer cooldown after firing is `max(100, 80 + effective × 25)` turns (`game_divine.py:780`), so 100 turns minimum. At chase speed 100% (L50-25), 100 turns = 100 floors of Death advance. At 125% speed (L25-L1), 100 turns = 125 floors of Death advance.

This means **prayer can fire effectively 2-3 times during the entire 99-floor ascent**, even if the player optimally manages cooldowns. Most of those prayers will be at less than max chain (theology escalator at high tiers, with wander mobs distracting).

**The asymmetry:**
- Death's speed escalation is *deterministic* (50→75→100→125 based on dungeon_level).
- Prayer's relief is *probabilistic* (chain quality × cooldown × altar adjacency).
- Death advances every turn. Prayer is gated.

In the 25-floor 125% speed band (L25→L1, the most desperate stretch), prayer can fire **maybe once** with effective relief. The rest of the chase relies on consumables (Flux Capacitor — 1 charge, Scroll of Teleportation, Potion of Haste).

The wonder beat of prayer-freeze ("Holy light blazes! Death recoils, frozen for 8 turns!") is *singular* — it lands once or twice and then the player is back to the chase. By the time the player hits 125% speed, prayer is *probably on cooldown* from a previous use, and **the chase becomes purely a consumables race**. This pivot is fine — it's intentional difficulty — but it means the chase's most thematic mechanic (knowledge → faith → divine relief) is structurally side-lined in the final act.

Compare the **chronicle line on prayer-freeze**: *"Prayed while Death hunted me. It froze in place. {N} turns. That's all I get."* The voice is exquisite. But "that's all I get" turns out to be *literally* — the player gets one prayer-freeze in the 25-floor crisis band.

## When and how often it fires
- Every successful chase escape uses prayer 1-3 times total. Most of the chase is *not* prayer.
- In the 125% speed band, prayer is on cooldown almost all the time.

## Suggested redirect
- **Reduce prayer cooldown specifically during the chase**: when `death_pursues` is True, prayer cooldown is halved. Lets the prayer-freeze mechanic actually be the chase's signature tool.
- **Or**: add a chase-specific altar tile that spawns on ascent. On ascent only, every 10 floors, the down-stairs tile is converted to an altar (the dying earth offers final mercies). Player can spend more time at altars during the climb.
- **Or**: the L100 altar ring (`boss_levels.py:469-477`) — six altars in a ring — is consumed via "Holy fire surges around the Destroyer" (`game_divine.py:761-763`). The chase could preserve one altar from this ring as a "blessing reserve" that follows the player up.
- **Surface the cooldown visibly during chase**: Death proximity messages already fire (`main.py:1408-1419`). Add a "Prayer: ready" / "Prayer: 47 turns" indicator near the message. Player makes informed decisions about when to engage Death vs. when to flee.

## Notes
Spans prayer system + death chase + cooldown gating + theology quiz. The mechanic is *correct*; the *cadence* doesn't match the act's intent. Act III is supposed to be the climax — but its most thematic mechanic fires twice. Compare to wand of haste (limited charges but each charge instantly affects movement) or scroll of teleportation (one-shot but immediate). Prayer is *more thematic* but *less responsive*.
