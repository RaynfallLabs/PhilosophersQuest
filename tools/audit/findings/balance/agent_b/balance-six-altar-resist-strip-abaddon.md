---
id: balance-six-altar-resist-strip-abaddon
dimension: balance
severity: P2
title: L100 arena has 6 altars, each prayer can strip ALL Abaddon resistances for chain*2 turns; cumulative 60+ turns of unresistance
status: open
systems: [boss_L100, prayer, altars, dungeon_layout]
floors_affected: [100]
evidence:
  - balance_curves_agent_b.json:boss_stats.abaddon_destroyer_L100 (resistances [poison, cold, fire, slash, blunt])
  - src/boss_levels.py:467-478 (six altars placed around boss chamber)
  - src/game_divine.py:749-767 (each altar's holy-fire strips ALL resistances for chain*2 turns)
discovered: 2026-05-15
---

## What's out of balance

The L100 boss arena (`boss_levels.py:467-478`) places 6 altars in a ring around Abaddon's chamber. Each altar's holy-fire prayer (`game_divine.py:749-767`) strips Abaddon's resistances *entirely* (`abaddon.resistances = []`) for `chain * 2` turns. The altar tracks its used state per-position (`_l100_altars_used.add(pos)`) — single-use per altar.

Math: chain 5 prayer at one altar = 10 turns of stripped resistances. Six altars × 10 turns = **60 turns of total stripped-resistance windows** the player can sequence across the fight.

Abaddon's 5000 HP at speed 10 with intervening locust spawns is typically a 20-40 turn fight. If the player uses each altar in sequence and times them around the locust-spawn cycle (every 4 turns), Abaddon's only physical resistance (`slash`, `blunt`, `cold`, `fire`, `poison` — basically everything except holy/magic) is gone for the entire fight.

This is a planned mechanic — the dev clearly wants the holy-fire to be the Act II resolution. But the *quantity* matters:

- 1 altar would be a desperate clutch.
- 2 altars would be a strategic decision.
- 6 altars is a feature, not a balance lever.

A standard weapon (e.g. mjolnir, base 26, peak chain 9x = 234, dealing slash) normally hits Abaddon at 50% damage from `slash` resistance — 117 effective. With altars active, full 234. Over 4 chain-9 attacks: 4 * 234 = 936. With cooking-stacked CON/STR run, easily 10+ chain hits in the 60-turn window = 2340+ damage = half of Abaddon down for free.

The dev DID build for this case: see `balance-abaddon-trivialised-by-sword-of-michael.md`. The Sword of Michael has `ignore_resistances: true` so the altar strip is redundant for the karma-blessed player. But a NORMAL player without the Sword still gets the altar nerf — and that normal player is who the difficulty contract is for.

## Curve evidence

`balance_curves_agent_b.json :: boss_stats.abaddon_destroyer_L100.resistances` = 5 types. `boss_levels.py:467-478` places 6 altars (manually counted from the code). The 6-altar layout is intentional; each one independently strips ALL resistances.

`balance_curves_agent_b.json :: weapons_by_min_level` filtered to slash/blunt/pierce types at peak_damage > 200: tyrfing (slash), caladbolg (slash), durendal (slash), hrunting (slash), spear_of_longinus (pierce), etc. — 10+ weapons that benefit from the resistance strip.

## Suggested re-tuning

1. **Reduce altar count from 6 to 3**: the arena still has the ring shape (`boss_levels.py:467-478`) but only 3 of the 6 ring positions are altars; the others are decorative WALL/FLOOR. The fight allows 3 strip windows, not 6.
2. **Cap stripping duration**: regardless of chain score, strip lasts a flat 5 turns. Chain still gates the OTHER prayer benefits (the resist-strip is the special L100 benefit). Stops chain-8 prayers from buying 16 turns each.
3. **Stack: only one resist-strip at a time** — using a second altar while first window is active extends, not refreshes. Already the case if `abaddon_resist_removed_turns` accumulates additively rather than overwriting — verify.

(1) is cleanest. Pair with (2) for compound safety.

## Notes

- Cross-system: boss arena layout + prayer mechanic + Abaddon's resistance set.
- Speculation: the dev placed 6 altars for narrative parallel ("the seventh seal" reference) — narrative-driven count, not balance-driven. Easy to push back to 3 without losing the visual.
- This finding pairs with `balance-abaddon-trivialised-by-sword-of-michael.md` and `balance-prayer-freeze-cheap-and-stackable.md` — together they describe L100 as having three independent boss-trivializers (sword, altars, prayer-freeze-during-locust-swarms).
