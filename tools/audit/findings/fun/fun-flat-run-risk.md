---
id: fun-flat-run-risk
dimension: fun
severity: P2
title: A single run can roll zero mysteries, zero NPCs, and zero special rooms — a fun-flat dice failure
status: open
systems: [mystery_spawn, npc_encounters, special_rooms, dungeon_pacing]
when_it_hits: "Bad-RNG short runs (death at floor 5-15) before any ambient encounter triggered"
evidence:
  - src/mystery_system.py:282-284
  - src/dungeon.py:1319-1320
  - src/npc_encounters.py:14-26
  - src/flavor_encounters.py:276
  - fun_pacing_trace.md#ambient-life-at-l1
discovered: 2026-05-15
---

## The friction or flatness
The game's *wonder budget* depends on ambient encounters firing. The spawn probabilities are:

- Mystery altar: 60% per floor *if any mystery is eligible* (`mystery_system.py:283`). Many mysteries don't start until L10+, so L1-9 has 0 eligible mysteries.
- Special room: 35% per floor (`dungeon.py:1319`).
- Flavor NPC: 40% per non-boss floor (`flavor_encounters.py:276`).
- Karma NPC: ~1 per 10-level block, but exactly 1 per block — so block 1 (L3-9) has 1 NPC on a *random* floor in that range.
- Merchant: 20% per floor (`mystery_system.py:615`).
- Magic Carrot: guaranteed once between L1-19.
- Soul Sphere: 5% per floor.

A player who dies on floor 6 may have rolled badly on every check:
- No mystery (L1-9 has none eligible).
- No special room on floors 1-6 (P = 0.65^6 ≈ 7.5% to roll zero).
- No flavor NPC (P = 0.60^6 ≈ 4.7%).
- No karma NPC (block 1 NPC is on a single floor L3-9; if you die before reaching it, you miss it).
- No merchant (P = 0.80^6 ≈ 26%).
- No Soul Sphere (P = 0.95^6 ≈ 73% — very common to roll none).

So roughly **1 in 200-300 short runs has *no ambient encounter at all***. That's a small percentage but a real one. A kid whose first 1-2 runs are short and unlucky may experience the game as "I walked, fought, died" — never seeing the rich world the game contains.

More commonly: a player who dies at floor 10-15 has seen 0-1 mysteries, 0-1 NPCs, 1-2 flavor NPCs, 1-2 special rooms. The wonder budget for that run is *thin*. Compared to a kid who reads through a run-end chronicle full of beats, the unlucky-short-run player has nothing to retell.

The encounters are *front-loaded* in the design — the game wants the kid to see them — but the *spawn dice* don't share that intent. There's no floor that's *guaranteed* to have an encounter, except L1's altar (because L1 % 15 == 1).

## When and how often it fires
- Roughly 5-10% of runs end with thin wonder budgets due to bad encounter rolls (combined with early death).
- More acutely: a kid's *first* run is highest-stakes for first impression, and the game gives no special guarantees for run 1.

## Suggested redirect
- **First-run special path**: when a save file is brand new (no chronicle history, no quirks unlocked, no high score), guarantee one mystery altar on L5-9 (the only band where most mysteries don't fire but a kid's first run might end). This costs nothing for experienced players (they're long past their first run) and dramatically improves first impressions.
- **Pity timer on encounters**: if no flavor NPC has fired in 5 floors, force one on the next non-boss floor. Same for mysteries (if no mystery in 10 floors and at least one is eligible, force-spawn).
- **L5 always has at least one special room.** A small guaranteed beat to teach the player that the dungeon has *rooms with character*, not just rooms with monsters.
- **L1 always has an altar AND a flavor NPC.** The opening sequence is the bedrock of the player's mental model. Right now L1 has an altar; adding a flavor NPC makes the first floor feel populated.

## Notes
Spans mystery spawn + special room generation + NPC encounter assignment. The core finding is that *probabilistic content gating produces inequitable first impressions*. The cure is small per-floor adjustments that **guarantee a baseline of ambient texture** in the earliest game.
