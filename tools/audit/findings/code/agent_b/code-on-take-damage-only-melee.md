---
id: code-on-take-damage-only-melee
dimension: code
severity: P3
title: `quirk_system.on_take_damage` only fires from melee monster attacks — DOT, traps, Death's reap all skipped
status: open
systems: [quirks, status-effects, death-chase]
evidence:
  - src/game_combat.py:1591-1597 — only call site; fires inside the per-monster melee turn loop
  - src/quirk_system.py:579-606 — Rasputin (#8), Green Knight (#47), Phoenix Rising (#75) track via `on_take_damage`
  - src/status_effects.py:319 — poison DOT: `dmg = player.take_damage(1, 'poison')` — no quirk hook
  - src/status_effects.py:331 — strangulation DOT: `dmg = player.take_damage(2, 'physical')` — no quirk hook
  - src/status_effects.py:350 — bleeding DOT: same pattern
  - src/main.py:1722 — trap damage: `actual = self.player.take_damage(raw, ...)` — no quirk hook
  - src/monster.py:1077 — Death's reap: `actual = player.take_damage(dmg, 'physical')` — no quirk hook
verified: true
discovered: 2026-05-15
---

## What's wrong
`QuirkSystem.on_take_damage(amount, pct_of_max)` is the canonical hook for damage-tracking quirks:
- **Rasputin (#8)** — survive at ≤5% HP × 5
- **Green Knight (#47)** — survive single hit ≥30% max_hp × 5
- **Phoenix Rising (#75)** — survive at ≤5% HP × 10

The hook is only invoked from a single site — the per-monster melee/ranged attack callback in `_do_monster_turns` (`game_combat.py:1594`). Every other damage source skips it:

- **Status DOT damage** (poison, bleeding, burning, strangulation, doomed, draining): each tick calls `player.take_damage(N, ...)` directly. No quirk notification.
- **Trap damage** (`main.py:1722` inside `_check_floor_trap`): `take_damage` called directly. No hook.
- **Cursed-miss backlash** (`combat.py:56`): `player.hp -= weapon.cursed_miss_backlash` — bypasses `take_damage` entirely, AND no quirk hook.
- **Death's reap** (`monster.py:1077`): Death calls `player.take_damage(dmg, 'physical')`. No `on_take_damage` because Death's attack is handled in `_do_monster_turns:1357-1371` (the Death-specific branch), separate from the regular monster loop that invokes the hook.
- **Self-damage from spells** (e.g., Sword of Michael holy blast self-recoil if any): direct take_damage calls.
- **Reflection damage** (`monster.py:319-323`): when a monster's fire/cold is reflected, the monster takes damage but the player doesn't — N/A.

Practical impact: a player who survives Death's chase at low HP repeatedly will never trigger Rasputin or Phoenix Rising. A player who survives 5 traps that hit for ≥30% max HP will never trigger Green Knight. Survival-themed quirks become unreachable for low-HP-trap and DOT-heavy builds.

## How to reproduce / where it fires
1. Enter the Death chase from L100. Allow Death to hit you to ≤5% HP repeatedly.
2. Each Death hit goes through `monster.py:1077` → `player.take_damage` → no `qs.on_take_damage` call.
3. Rasputin counter `rasputin_survivals` stays at 0.
4. Check Quirks panel post-chase — Rasputin: 0% progress.

Call graph (the working case): `_do_monster_turns` → regular monster `take_turn` → attack → `take_damage` → game_combat.py:1591-1594 fires `qs.on_take_damage`.

Call graph (broken case): `_do_monster_turns` → Death-specific branch → `dm.attack(self.player)` (line 1364) → `player.take_damage` (monster.py:1077) → **no quirk hook**.

## Suggested fix
Move the quirk hook inside `Player.take_damage`:

```python
def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
    ...
    actual = max(0, int(amount * resistance))
    self.hp = max(0, self.hp - actual)
    if actual > 0 and 'sleeping' in self.status_effects:
        del self.status_effects['sleeping']
    # Notify quirk system (if a game reference is available)
    qs_hook = getattr(self, '_quirk_system_ref', None)
    if qs_hook and actual > 0:
        qs_hook.on_take_damage(actual, actual / max(1, self.max_hp))
    return actual
```

The `_quirk_system_ref` would need to be set during Game.__init__. Alternative: pass quirk_system into Player.take_damage explicitly, or — simpler — have callers other than `_do_monster_turns` also invoke the hook (more brittle).

Either way, the canonical fix is centralising the hook so every damage path triggers it.

## Notes
This intersects `code-spell-damage-bypasses-resistances`: both reflect the broader pattern of damage-application paths bypassing canonical hooks. A unified `take_damage` that handles type, resistance, sleeping-wake, AND quirk notification would fix both.
