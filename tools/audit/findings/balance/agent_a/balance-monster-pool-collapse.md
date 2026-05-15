---
id: balance-monster-pool-collapse
dimension: balance
severity: P2
title: Encounter variety craters in endgame — pool size drops from 254 at F15 to 14 at F100
status: open
systems: [monsters, dungeon_progression, level_manager, fun_factor_via_balance]
floors_affected: [50, 100]
evidence:
  - balance_curves_agent_a.json:monsters_by_floor (per-floor pool_size_normal)
  - data/monsters.json (458 monsters; min_level/max_level fields)
  - Per-floor pool counts: F1=20, F15=254, F30=104, F50=57, F70=42, F90=28, F100=14
discovered: 2026-05-15
---

## What's out of balance

The normal-monster spawn pool peaks at F15 (~254 monsters available to spawn) and collapses through the endgame:

- F1: 20 monsters
- F5: 124
- F10: 214
- F15: **254** (peak)
- F20: 174
- F30: 104
- F40: 51
- F50: 50
- F60: 32
- F70: 32
- F80: 23
- F90: 17
- F100: 14

The peak at F15 makes sense — the most common dungeon zone, lots of monster variety. But the cliff from F40 (~50) to F100 (14) means the deep dungeon has dramatically less encounter variety. At F100 only 14 normal-mob types can spawn (plus mini-bosses).

This conflicts with the difficulty contract in two ways:

1. **Memorization payoff**: The deeper a player descends, the fewer monsters they need to learn. The most-skilled player encounters fewer unique threats — opposite of "above grade level" learning. Once you've identified abyssal_mimic, ancient_dragon, ancient_lich, death_lord, chaos_spawn (the F90+ canonical set per pool sampling), you've seen the F90-100 menagerie.
2. **AI pattern repetition**: The L80+ pool is dominated by `aggressive`, `fenrir_rage`, `abaddon` patterns. With only 14 monsters and several sharing AI patterns, fights become formulaic.

Compare to NetHack lineage (CONTEXT.md cites NetHack as soft benchmark): NetHack's deepest floors have *more* variety, not less, because tougher demons, dragons, and elementals all populate the bottom levels.

## Curve evidence

- `monsters_by_floor` row sampling:
  - `[0]` (F1): pool_size_normal=20, new_intros=20
  - `[14]` (F15): pool_size_normal=254, new_intros=13
  - `[39]` (F40): pool_size_normal=51, new_intros=7
  - `[69]` (F70): pool_size_normal=32, new_intros=2
  - `[99]` (F100): pool_size_normal=14, new_intros=3
- The pool shrinks because most early monsters have max_level around 30-40, but few endgame monsters fill those slots. Specifically:
  - Monsters with min_level≥35 in raw data: 458 - (sum of monsters with min_level<35) ≈ 200 monsters
  - But many F35-50 monsters have low max_level (e.g. max_level=60 for some), so by F70 the pool is mostly L60+ monsters
- The deliverable's `_data_gaps` notes frequency=0 monsters (scripted-only) are excluded — this is correct, but it means the player's actual visible variety is even lower than 14 at F100.

## Suggested re-tuning

1. **Extend max_level** on existing mid-game monsters. Many F35-F55 monsters could spawn through F70-80 with scaled HP via a level-scaler. This is what other roguelikes do (NetHack's monster-level scaling).
2. **Add 10-15 new monster definitions** in the L60-L90 range filling the AI-pattern gaps. Each new entry should bring a unique threat: an ambush specialist, a sessile late-game caster, a hit_and_run flying threat, etc.
3. **Don't lower difficulty** — the issue is variety, not power. The current F90-100 monsters (abyssal_mimic, ancient_dragon, etc.) are appropriately scary; we need MORE of them, not weaker ones.

## Notes

Crosses 3 systems: monster pool generation, dungeon level_manager spawn logic, and the "dungeon feels alive" FUN-domain contract (per CONTEXT.md §8). This is a BALANCE finding because pool size directly governs the variety-of-threat axis of difficulty — but it's borderline with FUN.

Verify in level_manager.py whether monsters with frequency=0 are spawned by code or only manual scripts. The deliverable count excludes them; if level_manager actually spawns them naturally the variety is higher than computed here. But based on `frequency: 0` semantics in monsters.json (boss/scripted-spawn convention), this is unlikely.

The F90+ pool of 14-17 monsters is the most acute. Player runs that reach F90 are precious (cleared 90 floors of permadeath) — they deserve more visual and tactical variety in the final stretch.
