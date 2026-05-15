---
id: balance-ariadnes-thread-defangs-3-bosses
dimension: balance
severity: P3
title: Ariadne's Thread (L15 artifact) neutralizes phasing/hit-and-run mechanic on Asterion + two vampire types; the L17 quest is a 60-floor cheat
status: open
systems: [artifacts, boss_AI, monster_AI]
floors_affected: [15, 80]
evidence:
  - balance_curves_agent_b.json:boss_stats.asterion_minotaur_L20.ai_pattern (hit_and_run, can_phase_walls)
  - src/game_combat.py:1373-1382 (Thread overrides hit_and_run -> aggressive, removes phasing, caps speed 6)
  - data/items/artifact.json:ariadnes_thread (min_level 15)
  - data/monsters.json:elder_vampire, ancient_vampire_lord (hit_and_run + can_phase_walls)
discovered: 2026-05-15
---

## What's out of balance

`ariadnes_thread` is an artifact acquired via the L17 Ariadne quest shrine (`dungeon.py:1501`, min_level 15). Its mechanical effect (`game_combat.py:1373-1382`) is to:

1. Remove `can_phase_walls` from any monster
2. Cap speed at 6 (slow them — speed 6 means skip 20% of turns per `monster.py:371-374`)
3. Convert `hit_and_run` AI to `aggressive`

Three monsters have these properties: `asterion_minotaur` (L20 boss), `elder_vampire` (L52), `ancient_vampire_lord` (L66). All three are entirely defanged by the player carrying the Thread.

The L20 boss fight (Labyrinth of Asterion, `boss_levels.py:91-194`) is built around Asterion's phasing-wall shortcuts — the level has 90+ phasing-wall tiles for him to teleport through. With Ariadne's Thread, he loses ALL phasing AND becomes a slow predictable melee target. The intricate hand-crafted maze becomes irrelevant.

The vampires at L52/L66 lose their *signature* mechanic (engage-and-retreat into walls), reducing them to slow aggressors.

This is a single L15 item that warps 3 fights across 60+ floors of the descent.

## Curve evidence

`balance_curves_agent_b.json :: boss_stats.asterion_minotaur_L20` shows `ai_pattern: "hit_and_run"`. Cross-reference `balance_curves_agent_b.json :: monsters_by_floor[L51-L60]` and `[L61-L70]` for the vampires.

The artifact has `min_level: 15` (just before the L20 boss) — the QUEST is designed to deliver this for Asterion. But the player keeps the Thread *forever*, neutralizing future vampires too.

## Suggested re-tuning

1. **Thread consumed by use**: when Thread's effect activates against a boss (Asterion), it shines and unravels — single-use artifact. Vampires later still need to be fought with full mechanic.
2. **Thread effect bounded to L20 floor**: only activate on dungeon_level <= 20 or for "labyrinth" tagged monsters.
3. **Make the Thread weaken phase frequency** instead of removing entirely: phasing-monsters now phase every N turns where N=10 instead of every turn. Asterion's flavor preserved, fight is harder but not signature-stripped.

Option (3) keeps the boss interesting while still rewarding the player for completing the side-quest.

## Notes

- This is P3 because:
  - The Asterion fight is at L20 — even defanged, an L1-19 player without Ariadne's Thread can struggle.
  - The vampire impact is at L52/L66 — by then players have many tools.
- Cross-system: artifacts + boss_AI + monster_AI. Single-item polish would be "Thread is too strong"; the curve story is "one artifact warps three encounters spanning 50 floors."
- Speculation: the dev's intent may have been "if you completed Ariadne's quest you EARN this advantage." That's defensible for L20. Less defensible for L52 and L66 — those are different acts.
