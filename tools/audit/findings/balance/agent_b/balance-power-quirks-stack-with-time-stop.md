---
id: balance-power-quirks-stack-with-time-stop
dimension: balance
severity: P2
title: Power-quirk roster contains 4 effective Death-skips (time_dilation, eye_storm, astral_form, shadow_step) on top of consumable time-stop
status: open
systems: [quirks_power, death_chase, status_effects]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:quirks (filter is_power=true)
  - src/quirk_system.py:1562 (time_dilation = [POWER x1] Time Stop 10 turns)
  - src/quirk_system.py:1552 (eye_storm = [POWER x3] Invisible + Blessed 10 turns)
  - src/quirk_system.py:1574 (astral_form = [POWER x2] Levitate + Invisible + Phase 8 turns)
  - src/quirk_system.py:1557 (shadow_step = [POWER x3] Invisible + Phasing 5 turns)
discovered: 2026-05-15
---

## What's out of balance

The Power-quirk roster includes powers usable during the Death chase. Beyond time_dilation (which directly time-stops — covered by `balance-time-stop-trivializes-death-chase.md`), three more powers are functionally "skip Death for N turns":

| Quirk | Power effect | Uses/run | Death-skip turns |
|---|---|---|---|
| `time_dilation` | Time Stop 10 turns | 1 | 10 (Death frozen) |
| `eye_storm` | Invisible + Blessed 10 turns | 3 | ~10 (Death's aggressive AI may still pathfind to player loc) |
| `astral_form` | Levitate + Invisible + Phase 8 turns | 2 | ~16 (Phase walks through walls — *kite Death through walls*) |
| `shadow_step` | Invisible + Phasing 5 turns | 3 | ~15 |

Critical: `astral_form` includes `phasing` status, which lets the player walk through walls. The Death pursuit AI (`DeathMonster.take_turn` → `super().take_turn` → standard `_aggressive` pathfind) cannot follow through walls. So an 8-turn phasing window is 8 turns of Death stranded on the far side of a wall, watching the player walk away.

Cumulative budget across these four powers: 1+10 + 3*10 + 2*16 + 3*15 = ~117 "Death-skip-equivalent" turns over the ascent. The chase is 100 floors; even at the worst case (125% speed near the surface), the player has more skip-turns than chase-turns.

## Curve evidence

`balance_curves_agent_b.json :: quirks` filtered to `is_power: true` shows ~35 power quirks. The ones above are the chase-relevant ones. The trigger thresholds are intentionally end-game (200 monster kills for `battle_trance`, 25 in-a-row for `time_dilation`, etc.) — exactly the player who would HAVE the Stone and be running the chase.

`balance_curves_agent_b.json :: death_chase_difficulty.speed_phases` shows the 125% phase covers only floors 1-25 of the ascent (player going 100→1). 24 stair-steps in that phase. The four power quirks alone furnish ~117 turns of bypass — most of which the player will burn during the 125% phase.

## Suggested re-tuning

1. **Phasing does NOT work during Death pursuit**: when `game.death_pursues == True`, the player's `phasing` status is suppressed for movement-through-walls purposes (still phases through monsters fine). This closes the `astral_form` kite.
2. **Invisible doesn't blind Death**: similar to existing comment in `main.py:855` about see_invisible vs dark. Death is a metaphysical entity; she sees you regardless of invisibility. The player's invisible status no longer affects Death's targeting (it still affects all other monsters).
3. **Power-quirk cooldown applied even at x1 use**: currently `time_dilation` is x1 use, no cooldown listed — once used, gone. That's fine for x1. But `eye_storm` x3 / `astral_form` x2 / `shadow_step` x3 should have a *between-uses* cooldown of 50+ turns each, so the player can't fire all uses back-to-back.

## Notes

- The dad-rule note from MEMORY.md: power-quirks are mastery rewards, deliberately strong. The intent is reward, not balance breakage. Fix (1) and (2) targeted at Death only preserves their power against the rest of the game.
- Cross-system: quirks_power + status_effects (phasing, invisible) + death_chase mechanic.
- These quirks ALSO affect Abaddon at L100. `astral_form` phasing through walls lets a player escape the boss arena. `eye_storm` invisibility against Abaddon's piercing apocalypse_blast may already not help — needs verification.
- Speculation: a "no power-quirks during chase" mode (player chooses to not use any powers while `death_pursues`) yields the highest reward code. Make heroism a player choice.
