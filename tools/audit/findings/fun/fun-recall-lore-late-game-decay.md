---
id: fun-recall-lore-late-game-decay
dimension: fun
severity: P2
title: Recall Lore's discovery loop becomes unusable when it matters most (L60-100)
status: open
systems: [recall_lore, wander_spawn, trivia_quiz, dungeon_pacing]
when_it_hits: "Deep dungeon, floors 60+ when wander spawn interval drops to ~10 turns"
evidence:
  - src/game_magic.py:75-122
  - src/main.py:1660-1692
  - data/hints.json
  - fun_pacing_trace.md#checkpoint-e-floor-90
discovered: 2026-05-15
---

## The friction or flatness
Recall Lore (`n` key) is the game's *primary discovery vehicle* (CONTEXT §5). It is an escalator-chain trivia quiz, max chain 5. Chain quality determines hint tier: chain 5 = T5 (deepest secrets). Cooldown scales with chain: 65-125 turns of game time before another use (`game_magic.py:115-122`).

The system works as intended in the early game when wander spawns are infrequent (every 22 turns at L1) and the player has rest beats between combats. By L60+, the wander spawn interval is `max(10, 22 - level//4)` — at L60 it's 7 turns, at L80 it's 5, at L90 it's a hard floor of 10 turns (`main.py:1664`). Cap is 14 simultaneous alive monsters at L80+.

This means in the deep dungeon, **the player is almost never in a 65+ turn safe zone where they can sit down and run a 5-question escalator chain.** The player begins Recall Lore expecting a contemplative discovery moment; mid-quiz, a wander monster spawns 8 tiles away and starts approaching, and the player can't see/respond to it until they exit the quiz. By chain 3 (a science-tier trivia question, ~38s timer), an unseen monster may have closed half the distance.

The result: **Recall Lore — the system that should produce the deepest wonder beats — is the system most punished by depth.** The deep dungeon is exactly where the player needs T4/T5 hints (which point at the Tablet, the Wrench, the Lake of Fire scroll, the Abyssal Shimmer). But the deep dungeon is also where running a max-chain trivia escalator is most dangerous.

## When and how often it fires
Every deep run. A player who reaches L70+ will likely have abandoned Recall Lore as too risky to use. By L90 it's effectively shelved. The biggest payoff hints (T4/T5) come from chains 4/5 — which require the most uninterrupted time.

## Suggested redirect
- **Recall Lore could pause wander spawns and monster turns** during the quiz itself. Treat it like a meditation: time stops, the dungeon pauses, no penalty for taking the time. The cooldown still gates how often it fires.
- **Alternatively**, Recall Lore could be **stair-bound or altar-bound** in deep floors — the player must be on a staircase or altar tile to invoke it. This gives the system a *place* in the dungeon where it lives, and stops it from being a constant menu-option that depth makes unusable.
- **Or**: scale Recall Lore quiz speed by floor. Deep floors get a shortened version (3-question max chain instead of 5) reflecting the player's accumulated wisdom. The T5 hint still requires a perfect run.

## Notes
The lore voice in `data/hints.json` is exemplary (CONTEXT cites it explicitly). The *vehicle* for hint delivery is what's broken, not the hints themselves. This finding spans the *recall lore* system + the *wander spawn* system + the *dungeon pacing* system — fixing just one of them won't address the wonder-degradation curve.
