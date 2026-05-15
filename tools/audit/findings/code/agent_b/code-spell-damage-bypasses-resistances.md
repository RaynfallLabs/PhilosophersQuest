---
id: code-spell-damage-bypasses-resistances
dimension: code
severity: P2
title: Spell mass-damage effects bypass monster resistances — `m.take_damage(amount)` drops the damage type
status: open
systems: [magic, combat, monster-resistances]
evidence:
  - src/monster.py:171-178 — `Monster.take_damage(amount: int)` has no damage_type parameter; resistances are never consulted
  - src/game_magic.py:1125 — `mass_ice`: `m.take_damage(scaled)` no type
  - src/game_magic.py:1140 — `mass_fire`: `m.take_damage(scaled)` no type
  - src/game_magic.py:461,470,491,509,542,559,636,670,688 — wand/spell single-target damage paths also pass no type
  - src/combat.py:9-30 — `_damage_multiplier` correctly consults `monster.resistances`/`weaknesses` — but it's only called inside `player_attack` for melee/ranged weapon attacks
  - data/monsters.json:19775-19778 — Fafnir has `"resistances": ["fire", "poison"]` plus `dragon_scales: 0.8`
verified: true
discovered: 2026-05-15
---

## What's wrong
`Monster.take_damage` has the signature `def take_damage(self, amount: int) -> int` — no damage_type argument. Resistance and weakness handling lives in `combat._damage_multiplier` and is only invoked inside `player_attack` (the melee/ranged weapon flow).

Every spell damage path bypasses this. `mass_fire`, `mass_ice`, `fire_bolt`, `cold_bolt`, `lightning_bolt`, `meteor`, `acid_arrow`, `drain_life_spell`, `disintegrate_spell`, and all single-target wand damage paths call `target.take_damage(scaled)` (`game_magic.py:1125`, `1140`, and ten other sites). The scaled number is the raw weapon-damage multiplier output — fire resistance, cold resistance, and dragon scales have no chance to attenuate it.

The most consequential case is the **Fafnir boss fight**. Fafnir's monster definition (`data/monsters.json:19775-19778`) has `dragon_scales: 0.8` (80% physical damage absorbed) AND `"resistances": ["fire", "poison"]`. By design, fire-based attacks should be the *worst* tool against Fafnir. But because spell damage skips the resistance lookup, **Fireball and Meteor deal full damage to Fafnir**, making the boss trivial for any caster build. This violates the design intent of elemental dragon weaknesses.

This is also true for elementals (fire elemental, ice elemental) and the seal demons — many of which carry resistance arrays for thematic reasons.

## How to reproduce / where it fires
1. Reach Fafnir on his boss level (~L40 or wherever he spawns).
2. Cast Fireball / Meteor / Fire Bolt.
3. `game_magic.py:1140` → `m.take_damage(scaled)` → `Monster.take_damage(amount)` at `monster.py:171` → `actual = max(0, amount)`. No resistance multiplier. Full damage applied.
4. Compare to a melee fire-elemental weapon: `combat.py:player_attack` calls `_damage_multiplier(['fire'], fafnir)` → returns 0.5 → damage halved correctly.

Call graph: `cast spell` → `_start_spell_quiz` → on_complete → `_apply_spell_effect` → `mass_fire` branch → direct `m.take_damage(scaled)` with no type.

## Suggested fix
Extend `Monster.take_damage` to accept an optional `damage_type` argument and consult `_damage_multiplier`:

```python
def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
    from combat import _damage_multiplier
    mult = _damage_multiplier([damage_type], self) if damage_type else 1.0
    # Dragon scales for physical damage
    if damage_type == 'physical':
        ds = getattr(self, 'dragon_scales', 0.0)
        if ds > 0:
            mult *= max(0.0, 1.0 - ds)
    actual = max(0, int(amount * mult))
    self.hp = max(0, self.hp - actual)
    if self.hp == 0:
        self.alive = False
    if actual > 0:
        self.status_effects.pop('sleeping', None)
    return actual
```

Then update every spell/wand call site to pass the type:
- `mass_fire`, `fire_bolt`, `meteor`, fire reflect → `'fire'`
- `mass_ice`, `cold_bolt`, ice storm → `'cold'`
- `lightning_bolt` → `'lightning'`
- `acid_arrow` → `'acid'`
- `magic_missile` → `'magic'`
- `drain_life_spell` → `'drain'`

The `player_attack` path can continue to use `_damage_multiplier` externally; the new in-Monster check is a defensive default for paths that skip the combat module.

## Notes
This intersects BALANCE — fire-resistant bosses become trivial for fire casters. But the root cause is CODE: the API contract `take_damage(amount, type)` is fulfilled for `Player` (player.py:106) but not for `Monster`. The mixin call sites assume both APIs match.

A simpler/safer alternative: keep `Monster.take_damage(amount)` for backward compat, and add a new `take_damage_typed(amount, type)`. Then update spell call sites only. This avoids touching the dozens of `target.take_damage(dmg)` sites that work fine for untyped (or always-physical) damage like `magic_missile`'s "unerring force" or `disintegrate`'s status-kill.
