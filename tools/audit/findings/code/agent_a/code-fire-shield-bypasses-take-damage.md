---
id: code-fire-shield-bypasses-take-damage
dimension: code
severity: P3
title: Fire/cold shield reflect bypasses Monster.take_damage and may double-trigger kill on fire shield
status: open
systems: [combat, status_effects, shields]
evidence:
  - src/game_combat.py:1480-1486 — fire shield reflect path: `m.hp -= reflect_dmg`, no `m.alive` guard on the kill check
  - src/game_combat.py:1488-1494 — cold shield reflect path: `m.hp -= reflect_dmg`, has `and m.alive` guard at line 1492
  - src/monster.py:171-178 — `Monster.take_damage` is the canonical damage path; clears sleeping, returns actual damage
verified: true
discovered: 2026-05-15

---

## What's wrong

Two related issues in the shield-reflect block at game_combat.py:1480-1494.

**(1) Direct hp mutation bypasses `Monster.take_damage`** — Both branches do `m.hp -= reflect_dmg` directly instead of calling `m.take_damage(reflect_dmg)`. Consequences:
- `Monster.take_damage` clears the `sleeping` status on damage (monster.py:177). Direct hp mutation does not — a sleeping monster hit by a fire-shield reflect stays asleep with reduced HP.
- Future resistance/material-defense logic added to `take_damage` will not apply to shield reflects.
- The return value of `take_damage` (actual damage clipped to current hp) is lost, so display messages may say "10 damage" when only 3 were dealt.

**(2) Fire shield kill check is missing `and m.alive`** — Looking at the two branches:

```python
# fire shield (line 1480-1486)
if self.player.has_effect('fire_shield') and dmg > 0:
    reflect_dmg = random.randint(2, 9)
    m.hp -= reflect_dmg
    self.add_message(...)
    if m.hp <= 0:                  # NO `and m.alive` guard
        m.alive = False
        self._on_monster_killed(m)
# cold shield (line 1488-1494)
if self.player.has_effect('cold_shield') and dmg > 0:
    reflect_dmg = random.randint(2, 9)
    m.hp -= reflect_dmg
    self.add_message(...)
    if m.hp <= 0 and m.alive:      # GUARDED
        m.alive = False
        self._on_monster_killed(m)
```

A player wearing both fire and cold shields who gets hit by a low-HP monster could trigger:
- Fire shield reflect kills the monster (sets alive=False, calls `_on_monster_killed` — increments `monsters_killed`, drops corpse, calls boss popup).
- Cold shield reflect runs, `m.hp <= 0` still true, BUT `m.alive` is now False so it correctly skips the kill path.

So the cold shield is the correct one. The fire shield's missing `and m.alive` is harmless in *this* combination because the cold shield happens to run second and is guarded — but if any future code path drops HP to 0 before fire-shield reflect runs (collateral damage from piercing arrows at game_combat.py:1456-1470 already does this), the fire shield will double-trigger `_on_monster_killed` on an already-dead monster, double-incrementing `monsters_killed`, double-dropping corpse/treasure, and potentially crashing the boss-popup path.

Both issues were flagged in the consensus baseline; both remain present in the source.

## How to reproduce / where it fires

Scenario for issue (2):
1. Player has fire shield active and a ranged weapon that deals piercing collateral.
2. A multi-monster row: piercing arrow kills the second monster via `_on_monster_killed` at game_combat.py:1469. That monster has hp=0 alive=False.
3. The first monster attacks (still alive). Lands a hit. The damage handler enters the fire-shield branch with `m` = first monster (still alive, attacker). Reflect deals damage. If first monster's hp drops to 0, `_on_monster_killed` fires. Fine.
4. BUT: imagine the first monster was already at 0 hp from a separate effect (e.g., bleeding tick from main.py:1559 ran before melee), or a Sketchbook attack damaged it via direct hp manipulation in a custom code path. `m.hp <= 0 and m.alive=False` — fire shield branch triggers `_on_monster_killed(m)` again. Boss popup, treasure, increment.

Slightly contrived; less reachable in normal play than the issue-(1) bypass, which is reachable every time fire/cold shield reflects damage.

## Suggested fix

```python
# fire shield
if self.player.has_effect('fire_shield') and dmg > 0:
    reflect_dmg = random.randint(2, 9)
    m.take_damage(reflect_dmg)
    self.add_message(f"Flames lash back at the {m.name} for {reflect_dmg}!", 'danger')
    if not m.alive:
        self._on_monster_killed(m)

# cold shield -- same pattern
if self.player.has_effect('cold_shield') and dmg > 0:
    reflect_dmg = random.randint(2, 9)
    m.take_damage(reflect_dmg)
    self.add_message(f"Ice shatters back at the {m.name} for {reflect_dmg}!", 'danger')
    if not m.alive:
        self._on_monster_killed(m)
```

`take_damage` already sets `alive = False` when hp drops to 0 (monster.py:174-175), so we don't need to do it manually.

## Notes

Consensus had this as a P4. I'm keeping it at P3 because the bypass of `take_damage` is real and broad (every reflect interacts with the sleeping clear). The double-kill is rare but possible. Includes Svalinn shield reflect at game_combat.py:1513-1523 which has the SAME pattern (uses `m.alive` guard correctly, but bypasses `take_damage`).
