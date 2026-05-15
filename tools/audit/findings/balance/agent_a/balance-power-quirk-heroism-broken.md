---
id: balance-power-quirk-heroism-broken
dimension: balance
severity: P1
title: Atlas Burden / Battle Trance / Death Wish quirks silently apply heroism without STR+2, but expiry still penalizes -2 STR
status: open
systems: [quirks, status_effects, combat, food_system]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_a.json:power_quirks (atlas_burden, battle_trance, death_wish all claim "Heroism" effect)
  - src/game_menus.py:794-796 (atlas_burden: pl.add_effect('heroism', 20) — no STR bonus)
  - src/game_menus.py:817-819 (battle_trance: pl.add_effect('heroism', 15) — no STR bonus)
  - src/game_menus.py:831-834 (death_wish: pl.add_effect('heroism', 10) + hasted — no STR bonus)
  - src/food_system.py:446-454 (food path applies STR+2 via apply_stat_bonus, gated by already_active check)
  - src/status_effects.py:401-402 (expiry: `if effect == 'heroism': player.apply_stat_bonus('STR', -2)`)
  - src/status_effects.py:279-296 (apply_effect — only manipulates status_effects dict, never touches stats)
discovered: 2026-05-15
---

## What's out of balance

Three Power-quirks (Atlas Burden, Battle Trance, Death Wish) invoke `pl.add_effect('heroism', N)` to grant the Heroism buff. **But the +2 STR bonus that Heroism is supposed to provide is NOT applied** — `add_effect` calls `apply_effect` (src/status_effects.py:279), which only writes to `status_effects` dict and never touches `player.STR`.

Meanwhile, when the effect expires, `tick_all` unconditionally subtracts 2 STR (status_effects.py:401-402: `if effect == 'heroism': player.apply_stat_bonus('STR', -2)`). So every quirk-activation of Heroism produces:

1. **During the buff**: STR is unchanged (the buff does nothing mechanically except modify the buff list).
2. **After the buff expires**: STR -2 is applied — permanently lowering the player's STR below baseline.

The only path that correctly applies +2 STR is `food_system.py:446-454` (potion/food path), which explicitly calls `player.apply_stat_bonus('STR', 2)` after the `add_effect`.

**Net result**: Atlas Burden, Battle Trance, Death Wish actively HURT the player. They are Power-quirks the player worked for (Atlas requires 100 burdened turns, Battle Trance 200 kills, Death Wish 10 sub-25%HP kills) and they produce negative outcomes when used. Combined with stackability (each use applies a fresh -2 on expiry), repeated power-use can drive a player's STR to single digits.

## Curve evidence

- Deliverable `power_quirks` entries describe Heroism as the effect of three quirks; verify in game_menus.py:
  - atlas_burden (game_menus.py:794-796): "Heroism for 20 turns" — adds effect, NO `apply_stat_bonus`
  - battle_trance (game_menus.py:817-819): "Heroism for 15 turns!" — adds effect, NO `apply_stat_bonus`
  - death_wish (game_menus.py:831-834): "Heroism + Hasted for 10 turns!" — adds effect, NO `apply_stat_bonus`
- Compare with food_system.py:446-454 (working path):
  ```
  player.add_effect('heroism', dur)
  if not already_active:
      player.apply_stat_bonus('STR', 2)
  ```
- Expiry path (status_effects.py:401-402):
  ```
  if effect == 'heroism':
      player.apply_stat_bonus('STR', -2)
  ```
- The expiry is unconditional — it does NOT check whether the +2 was originally granted.
- STR drives:
  - Carry capacity (player.py:6-7, CARRY_PER_STR=5)
  - SP cap (player.py:44, max_sp = BASE_SP + STR)
  - Many quirk progress triggers
- So a player who uses Atlas Burden five times (2 uses x ~2.5 runs of stacking decay) ends with STR baseline - 10, max_sp baseline - 10, carry baseline - 50.

## Suggested re-tuning

CODE-fix: in `game_menus.py`, replicate the food_system pattern — wrap each `add_effect('heroism', X)` with an `already_active` check + `apply_stat_bonus('STR', 2)`. Same fix for brilliance (focused_scholar quirk, arcane_surge quirk, philosophers_stone quirk — verify whether the +1 INT +1 WIS happens at apply or only at expiry).

Once fixed, the quirks become real damage buffs as designed. BALANCE re-tuning may be needed AFTER fix: a +2 STR for 10-20 turns with 2-3 uses per run is genuinely strong; Battle Trance at 3 uses x 15 turns = 45 turns of +2 STR is significant.

## Notes

Cross-system finding: quirks (Power-quirks subset) + status_effects (apply/expire asymmetry) + combat (STR drives damage indirectly via carry/SP). This is technically a CODE bug but I'm flagging as BALANCE because:

1. The deliverable `power_quirks` advertises a balance contribution that doesn't exist.
2. Three of the curated 12 Power-quirks listed in the rubric (atlas_burden, battle_trance, philosophers_stone) are affected — and philosophers_stone also calls add_effect('brilliance') without applying INT/WIS bonus.
3. The fix changes the power budget of these quirks materially.

The CODE-domain bug entry should also exist; this finding documents the balance impact.
