---
id: code-quirk-power-heroism-stat-drain
dimension: code
severity: P1
title: Quirk powers granting heroism/brilliance permanently drain STR/INT/WIS on expiry
status: open
systems: [quirk_powers, status_effects, player_stats]
evidence:
  - src/game_menus.py:770 — focused_scholar/arcane_surge power: `pl.add_effect('brilliance', 10)` without applying INT+1/WIS+1
  - src/game_menus.py:791 — philosophers_stone power: `pl.add_effect('brilliance', 10)` without applying INT+1/WIS+1
  - src/game_menus.py:795 — atlas_burden power: `pl.add_effect('heroism', 20)` without applying STR+2
  - src/game_menus.py:818 — battle_trance power: `pl.add_effect('heroism', 15)` without applying STR+2
  - src/game_menus.py:832 — death_wish power: `pl.add_effect('heroism', 10)` without applying STR+2
  - src/status_effects.py:401-405 — `tick_all` on heroism expiry: `apply_stat_bonus('STR', -2)`; on brilliance expiry: `-1 INT, -1 WIS`
  - src/food_system.py:446-465 — potion path correctly pairs `add_effect` with `apply_stat_bonus` (guarded by `if not already_active`)
verified: true
discovered: 2026-05-15

---

## What's wrong

The status-effects module unconditionally reverses heroism (STR -2) and brilliance (INT -1, WIS -1) when those effects expire (status_effects.py:401-405). That reverse is balanced ONLY when paired with the matching `apply_stat_bonus` at apply-time — which is what the potion path in `food_system.drink_potion` does (food_system.py:446-465).

Five quirk-power activations in `game_menus.py` add the heroism/brilliance status WITHOUT calling `apply_stat_bonus`:

- `focused_scholar` / `arcane_surge` → brilliance (10 turns)
- `philosophers_stone` (quirk power) → brilliance (10 turns)
- `atlas_burden` → heroism (20 turns)
- `battle_trance` → heroism (15 turns)
- `death_wish` → heroism (10 turns)

When any of these effects expire, the unconditional reverse fires anyway. Net result: every activation permanently drains the player's STR (-2) or INT/WIS (-1/-1). A player using `atlas_burden` ten times in a run loses 20 STR. The player can permanently zero out a stat with enough power uses.

## How to reproduce / where it fires

Trigger any of the five powers via the power menu (V key). Wait for the heroism/brilliance status to expire. Stats are now lower than before activation.

Trace:
1. Player activates `atlas_burden` via `_use_power` in game_menus.py — calls `pl.add_effect('heroism', 20)` at line 795. No `apply_stat_bonus('STR', 2)`.
2. 20 turns later, `_advance_turn` → `self.player.tick_effects()` → `status_effects.tick_all()`.
3. `tick_all` line 392-395 expires 'heroism' (val reaches 0).
4. Line 401-402: `if effect == 'heroism': player.apply_stat_bonus('STR', -2)`.
5. Player STR is now permanently -2 even though they never gained +2.

## Suggested fix

For each of the five power activations in game_menus.py, add the corresponding stat bonus before/with the `add_effect` call, mirroring the potion pattern at food_system.py:446-465:

```python
elif pid == 'atlas_burden':
    if not pl.has_effect('heroism'):
        pl.apply_stat_bonus('STR', 2)
    pl.add_effect('heroism', 20)
```

Same shape for `battle_trance`, `death_wish`, `focused_scholar`/`arcane_surge`, `philosophers_stone`. For brilliance powers, apply INT+1 and WIS+1.

Alternative: change `status_effects.tick_all` to only reverse the stat bonus if a flag (e.g., `player._heroism_str_applied`) records that the bonus was applied at apply-time. More invasive but bullet-proof against future paths.

## Notes

Consensus had a related P4 about heroism stacking on re-drink — that has since been fixed in the potion path with `if not already_active`. The quirk-power paths were missed by that fix.
