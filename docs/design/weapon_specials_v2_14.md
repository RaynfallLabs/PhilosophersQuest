# Weapon Chain Specials + Crit Removal — v2.14.0

**Status:** Design agreed 2026-09-10. Companion doc to `chain_combat_v2.md`.

**Scope:** Per-class chain-triggered specials at chain 5 / 10 / 15 / 20 that all common and unique weapons inherit from their class. Uniques will layer distinctive passives on top in a follow-up pass — but they still inherit the class chain-special ladder.

Also: **crit is removed from the game.** Chain IS the crit. `crit_multiplier` and `petrify_on_crit` are stripped from the engine and from all weapon JSON.

---

## Core principles

1. **Chain 20 is achievable on floor 1.** A player fast at simple math can hit 20 on their first attack in the dungeon. So chain-20 effects must be rewarding but not floor-clearing.
2. **No player-input specials.** No teleports, dashes, forced targeting choices. The player pressed SPACE, the effect just happens.
3. **No forced monster movement.** No knockback, no pull — moving monsters out of your way (or into your way) is unpredictable and often bad for the player.
4. **No extra ammo cost.** Ranged specials work off the SAME projectile already fired.
5. **No instant-kills.** Chain 20 is repeatable, so it can't be a kill button.
6. **Effects grounded in weapon physics.** Spears pierce, maces stun, arrows hit vitals, stones bounce, axes chop limbs.
7. **Rung inheritance rule:** at chain N, the HIGHEST-threshold effect that qualifies fires (not all lower ones — each threshold's effect is designed as the full package for that rung).
8. **No `crit`** — chain IS the crit. Never call anything a critical hit. Never fire a crit multiplier. Never write `crit=True` to a message.

## Effect vocabulary

**Already in engine:** `bleeding, poisoned, stunned, slowed, blinded, paralyzed, confused, petrifying, shielded, regenerating, ignore_resistances`

**New in v2.14.0:**

| Effect | Applies to | Behavior |
|--------|-----------|----------|
| `armor_crack` | Monster | Takes +25% damage from all sources for N turns |
| `sundered` | Monster | Deals -30% outgoing damage for N turns |
| `deep_wound` | Monster | Takes +25% dmg AND cannot regenerate for N turns |
| `blade_flow` | Player | Next N attacks bypass damage reduction (stack-consumed) |
| `ruptured` | Monster | 10% max HP/turn DoT for N turns; cannot be healed while active |
| `impaled` | Monster | Cannot move for N turns (can still attack in place) |

## Class chain-special ladder

Each weapon class has its own row. Chain 5 → 10 → 15 → 20 is the ladder; only the highest threshold fires per attack (rung inheritance is BY DESIGN, not additive).

### Martial / self-sustain family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **Fist** | Target `slowed` 2t | Target `sundered` 3t | Target `deep_wound` 3t + `bleeding` 5t | Target `stunned` 3t + `deep_wound` 5t + `bleeding` 8t |
| **Rapier** | Target `bleeding` 3t | Target `sundered` 3t + `bleeding` 5t | Target `sundered` 5t + `bleeding` 8t + player -30% melee dmg 2t | Target `sundered` 8t + `bleeding` 10t + player -50% melee dmg 4t |
| **Staff** | Target `slowed` 2t | All adjacent monsters `slowed` 2t | Player -50% dmg 3t + regen 15% HP | All adjacent `slowed` 3t + player regen 15% HP + regen 10% MP + -50% dmg 3t |

### Precision / assassin family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **Dagger** | Target `bleeding` 4t | Target `deep_wound` 3t | Target `poisoned` 6t + `bleeding` 6t | Target `ruptured` 5t + `poisoned` 8t + `bleeding` 10t |
| **1h Sword** | Target `bleeding` 3t | This hit bypasses damage reduction | Player `blade_flow` 3 stacks + player -30% melee dmg 3t | Player `blade_flow` 4 stacks + player -30% melee dmg 3t |
| **Bow** | Target `bleeding` 3t (barbed) | Target `blinded` 4t (eye-shot) | This shot bypasses damage reduction | Target `blinded` 6t + `bleeding` 8t + this shot bypasses DR + hits vitals (×2 dmg) |

### Brute / crushing family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **1h Axe** | Target `bleeding` 4t | Target `sundered` 3t | Cleave 1 adjacent 0.5× + all `bleeding` 4t | Cleave all adjacent 0.5× + `bleeding` 8t all + `sundered` 5t all + regen 5% HP per adjacent hit (max 15%) |
| **Mace** | Target `stunned` 1t (40%) | Target `armor_crack` 5t | Target `stunned` 2t (100%) + `armor_crack` 8t | Target `stunned` 3t + `armor_crack` 10t + this hit bypasses DR |
| **2h Warhammer** | Target `stunned` 2t | Target `stunned` 3t + all adjacent `stunned` 1t | 2-tile radius: all `stunned` 1t + `armor_crack` 5t | 2-tile radius: all `stunned` 1t + `armor_crack` 5t + AoE 0.4× dmg |

### Reach / control family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **Spear** | Target `bleeding` 3t | This thrust bypasses DR | Pierces tile behind (0.6× to secondary) + `bleeding` both + bypass DR both | Pierces line 2 tiles (0.5× each) + `bleeding` 8t all + bypass DR all + primary `impaled` 3t |
| **Halberd** | Target `bleeding` 3t | Target `sundered` 2t + `bleeding` 5t | Reach line to +1 tile behind (0.6×) + all `bleeding` 5t + `sundered` 3t all | Full reach-2 line at 0.6× + `bleeding` 8t all + `sundered` 5t all |
| **Glaive** | Cleave 1 adjacent 0.7× | Cleave 2 adjacent 0.6× + all `bleeding` 3t | Full reach-2 arc 0.5× + all `bleeding` 5t | 2-tile radius arc 0.5× + `bleeding` 8t all + `slowed` 3t all |

### Great weapon / cinematic family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **2h Sword** | +1 adjacent 0.7× | +2 adjacent 0.6× | 360° arc 0.5× + all `bleeding` 4t | 2-tile radius 0.5× + all `bleeding` 8t + player `blade_flow` 3 stacks |
| **2h Axe** | Cleave 1 adjacent 0.7× + target `bleeding` 4t | Cleave 2 adjacent 0.6× + all `bleeding` 4t + primary `sundered` 3t | Full arc 0.5× + all `bleeding` 6t + all `sundered` 5t | 360° arc 0.6× + all `bleeding` 10t + all `sundered` 8t + regen 5% HP per hit (max 15%) |

### Ranged mechanical family

| Class | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|-------|---------|----------|----------|----------|
| **Crossbow** | Bolt bypasses DR | + target `slowed` 3t | Skip next 3 reloads | Ballista: bolt continues through target in line (max 5 tiles behind) at 0.7× each + bypass DR all + `slowed` 3t all |
| **Sling** | Same stone ricochets to nearest adjacent enemy (25%, 0.5×) | Guaranteed ricochet + primary `stunned` 1t | Primary `stunned` 2t + `slowed` 2t | Stone shatters: fragments hit all in 3-tile radius at 0.5× + `stunned` 1t all |

## Damage reduction ("DR") — what "bypasses DR" means

For monster targets, damage reduction is:
- **`dragon_scales`** — flat physical reduction (dragons)
- **`shielded` status** — 0.5× received while active
- **`resistances` list** — 0.5× to matching damage types

"Bypasses DR" means: `dragon_scales` skipped for that hit, `shielded` ignored, and the damage-type resistance multiplier clamped to 1.0 (weaknesses still apply — pierce vs pierce-vulnerable still hits harder).

## Rung dispatch rule

```
if chain >= 20: fire chain-20 effect only
elif chain >= 15: fire chain-15 effect only
elif chain >= 10: fire chain-10 effect only
elif chain >= 5: fire chain-5 effect only
else: no chain special
```

Each rung is the complete effect package for that threshold. Chain 20's effects were designed knowing chain 15's effects don't fire alongside them.

## Universal caps (unchanged from earlier design)

- Stun-immunity 3t window after any stun expires on a monster (already-planned; prevents perma-lock)
- AoE secondary targets take **damage only** — no secondary status procs (bleeding/sundered/etc. only on primary target unless the effect explicitly says "all")
- Instant-kills: removed entirely

## Crit removal — cleanup list

- `Weapon.crit_multiplier` field: delete from `items.py`, remove from `weapon.json` (all ~30 uniques with `critMultiplier`)
- `Weapon.petrify_on_crit` field: delete from `items.py`, remove from `weapon.json` (Harpe only)
- `combat.py` lines 503-527: rip the entire crit block including Kusanagi force-crit + Soul Reaver next-hit-auto-crit
- `combat.py:761-766`: rip cleave-mechanic crit multiplier
- Any `on_complete(crit=...)` message paths in `game_combat.py`: drop crit messaging
- Player buff `crit_buff` in `status_effects.py`: retire (Phase 3B hero special, no longer applicable)

### Unique rewires (crit-adjacent mechanics that need to survive)

- **Harpe** (`petrify_on_crit` → chain 15): applies `petrifying` 3t at chain 15 via the scimitar/sword class-specials pathway or via a per-weapon `petrify_at_chain_15` flag
- **Kusanagi** (`surrounded_proc_bonus` force-crit → flat +25% damage): when 3+ monsters adjacent, `mult *= 1.25` instead of firing a crit
- **Soul Reaver** (`growth_on_innocent_kill` next-hit-crit → `blade_flow` 1 stack): after innocent kill, player gains 1 stack of `blade_flow`

## Migration order

1. Design doc (this file)
2. Register 6 new statuses in `status_effects.py`
3. Wire monster tick behavior (`ruptured` DoT, `impaled` movement block) in `monster.py`
4. Wire `sundered` damage-output multiplier in monster attack sites (`monster.py` 3 locations)
5. Wire `armor_crack` / `deep_wound` damage-received multiplier in `combat.py` `player_attack`
6. Wire `blade_flow` player-buff check in `combat.py` (bypass DR + consume stack)
7. Add `_CLASS_CHAIN_SPECIALS` table + `_apply_chain_specials()` dispatch in `combat.py` (called after damage)
8. Rip crit block + `crit_multiplier` + `petrify_on_crit` (combat.py, items.py, game_combat.py)
9. Rewire Harpe, Kusanagi, Soul Reaver
10. Strip `critMultiplier` and `petrifyOnCrit` from `data/items/weapon.json` (script)
11. Update `crit_buff` retirement in `status_effects.py`
12. Update tests
13. Full pytest + fix regressions
14. Commit

Uniques follow-up: revisit `data/items/weapon.json` and rebuild per-unique base_damage / chain_exponent / distinctive passives on top of the class chain-special ladder they now inherit.
