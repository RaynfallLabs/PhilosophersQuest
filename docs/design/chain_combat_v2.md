# Chain Combat v2 — Design

**Status:** Design agreed 2026-09-07. Not yet implemented in code. Chain specials per weapon are deferred to a follow-up doc.

**Owner:** Brandon (RaynfallLabs).

**Supersedes:** the existing 5-rung `chain_multipliers` weapon templates in `tools/balance/generated/templates/weapons/`, the current `_DEFAULT_MULTIPLIERS = [0.3, 0.5, 0.7, 0.9, 1.2]` in `src/combat.py`, the current `SUBJECT_TIMER['math'] = (8, 0.8)` in `src/player.py`.

---

## Core loop

Attack a monster → math quiz starts → answer as many questions as you can within your timer → strike lands when you **cancel** (SPACE), **run out of time**, or **answer wrong**. Chain length drives damage multiplier and (later) weapon-signature effects.

## Timer

- **Flat WIS seconds.** `SUBJECT_TIMER['math'] = (0, 1.0)`. WIS 10 = 10s, WIS 15 = 15s, WIS 20 = 20s.
- Set once at quiz start (`quiz_engine.start_quiz`); runs continuously; no per-question reset.
- WIS becomes the load-bearing combat stat.

## Damage formula

Per-hit chain multiplier:

```
mult = n^weapon.chain_exponent
```

Default `chain_exponent = 1.15`. Per-weapon override allowed (e.g. 1.20 for greataxe, 1.10 for rapier).

Reference multipliers at default exponent:

| Chain | Mult |
|-------|------|
| 1  | 1.00 |
| 3  | 3.60 |
| 5  | 6.50 |
| 8  | 11.4 |
| 10 | 14.1 |
| 15 | 22.9 |
| 20 | 36.4 |

Full final-damage formula (replaces current `combat.py:360-381`):

```
final = base_dmg
      × material.damage_mult
      × material_effective_mult      # 1.5× if monster tag in material.effective_against, else 1.0
      × dmg_type_mult                # 1.5 weakness, 0.5 resistance, 1.0 neutral (max over weapon damage_types)
      × n^chain_exponent
      + ranged_stat_bonus            # STR + PER hits, computed per shot; see Ranged
      - dragon_scales_reduction      # existing physical reduction, unchanged
```

Existing per-weapon and per-unique multipliers (crit, prophecy_blade, stealth_damage_bonus, etc.) still stack on top.

## Chain resolution

| Trigger | Result |
|---------|--------|
| Player presses SPACE          | Strike lands at current chain mult |
| Wrong answer at chain ≥ 1     | Chain shatters visually, strike lands at current chain mult |
| Wrong answer at chain 0       | Weapon misses, no damage |
| Timer expires                 | Strike lands at current chain mult |

Chain resets to 0 at every new attack. No stockpiling between attacks.

**Key binding:** SPACE (ESC is reserved for menu exit).

## Mid-quiz UI overlay

Live display, updated on each correct answer:

- **Combo counter** — chain number, size + color shifts at milestones
- **Multiplier** — e.g. "6.5×"
- **Damage preview** — what the strike would deal right now (base × material × mult, rounded)
- **Timer bar** — seconds remaining
- **Cancel hint** — "SPACE to strike"

## Universal chain milestones (visual only)

| Chain | Rank | Combo counter treatment |
|-------|------|-------------------------|
| 3  | Solid     | Green tint, small pulse |
| 5  | Sharp     | +20% size, yellow glow |
| 8  | Brilliant | Orange, screen edge glow |
| 10 | Genius    | Red, slight zoom on hit |
| 15 | Prodigy   | Gold, full-screen flash on land |
| 20 | Mythic    | Rainbow, screen-consuming counter (rare — designed to feel legendary) |

No mechanical bonuses layered on the milestones themselves — the escalating damage curve IS the reward. Weapon-specific chain specials at chain 5/10/15/20 come in the follow-up doc.

## Weapon classes (16)

Each weapon has ONE material pool (no composites; head material drives hafted weapons).

| Weapon | Base Dmg | Weight | Reach | Hands | Damage Type | Material | Throw | Notes |
|--------|----------|--------|-------|-------|-------------|----------|-------|-------|
| Fist          | 2  | 0.0 | 1 | 0 | crush | none | no | Default unarmed; base scales with STR (see Fist STR scaling) |
| Dagger        | 3  | 1.0 | 1 | 1 | pierce + slash | metal | 1.0× | Throwable; finesse (DEX) |
| Rapier        | 4  | 1.5 | 1 | 1 | pierce | metal | no | Finesse (DEX) |
| 1h Sword      | 5  | 3.0 | 1 | 1 | pierce + slash | metal | no | Dual-type tax |
| 1h Axe        | 6  | 3.5 | 1 | 1 | slash | metal | no | Single type |
| Mace          | 6  | 4.0 | 1 | 1 | crush | metal | no | — |
| Spear         | 5  | 3.0 | 2 | 1 | pierce | metal | 1.0× | Reach 2; throwable (javelin) |
| 2h Sword      | 8  | 5.0 | 1 | 2 | pierce + slash | metal | no | — |
| 2h Axe        | 10 | 6.0 | 1 | 2 | slash | metal | no | — |
| 2h Warhammer  | 11 | 7.0 | 1 | 2 | crush | metal | no | Heaviest |
| Staff         | 8  | 4.0 | 2 | 2 | crush | wood | no | Reach 2 |
| Glaive        | 8  | 5.5 | 2 | 2 | slash | metal | no | Reach 2 |
| Halberd       | 7  | 5.5 | 2 | 2 | pierce + slash | metal | no | Reach 2, dual-type + reach tax |
| Bow           | 4  | 2.0 | var | 2 | pierce | wood | no | Range = 5 + (STR-10)/2, cap 10 |
| Crossbow      | 8  | 4.5 | 7 | 2 | pierce | wood | no | Fixed range 7; 1-turn reload between shots |
| Sling         | 2  | 0.5 | var | 1 | crush | leather | no | Range = 4 + (STR-10)/2, cap 8 |

**Tax rules baked in:**

- **Dual-type tax:** swords/daggers get -1 to -2 base vs single-type cousins. In exchange, `dmg_type_mult` picks the better of pierce/slash against the monster.
- **Reach tax:** reach-2 weapons (spear, staff, glaive, halberd) get -1 to -2 base vs reach-1 cousins.

## Material system

Three pools. 5 tiers per pool. Each tier has a core material; some tiers have a specialty (creature-typed) or elemental (elemental-typed) variant.

### METAL — for dagger, rapier, 1h/2h sword, 1h/2h axe, mace, 2h warhammer, spear, halberd, glaive

| Tier | Material | dmg | wt | Type | Effective against |
|------|----------|-----|-----|------|-------------------|
| 1 | **copper**       | 0.70 | 1.10 | core       | — |
| 1 | bronze           | 0.80 | 1.05 | specialty  | fey |
| 2 | **iron**         | 1.00 | 1.00 | core       | — |
| 2 | silver           | 0.90 | 1.05 | specialty  | undead, lycanthrope |
| 2 | volcanic_iron    | 0.95 | 1.00 | elemental  | fire-vulnerable (ice/frost creatures) |
| 3 | **steel**        | 1.20 | 0.95 | core       | — |
| 3 | cold_iron        | 1.10 | 1.00 | specialty  | fey, demon |
| 3 | frost_iron       | 1.15 | 1.00 | elemental  | cold-vulnerable (fire creatures, salamanders) |
| 3 | stormiron        | 1.15 | 1.00 | elemental  | shock-vulnerable (water/sea creatures) |
| 4 | **mithril**      | 1.40 | 0.55 | core       | — |
| 4 | sunsteel         | 1.35 | 1.00 | specialty  | undead, fiend |
| 4 | shadowiron       | 1.35 | 0.90 | specialty  | celestial, aberration |
| 5 | **adamantine**   | 1.70 | 1.30 | core       | — |
| 5 | orichalcum       | 1.60 | 0.95 | specialty  | outsider, demon_major |
| 5 | void_touched     | 1.55 | 0.80 | elemental  | aberration, void_spawn |

### WOOD — for staff, bow, crossbow

| Tier | Material | dmg | wt | Type | Effective against |
|------|----------|-----|-----|------|-------------------|
| 1 | **oak**         | 0.75 | 0.90 | core      | — |
| 2 | **ash**         | 1.00 | 0.90 | core      | — |
| 2 | yew             | 0.95 | 0.85 | specialty | fey |
| 3 | **ironwood**    | 1.15 | 1.15 | core      | — |
| 4 | **silverbark**  | 1.35 | 0.80 | core      | undead, fey |
| 4 | dragonwood      | 1.30 | 1.00 | specialty | dragon |
| 5 | **worldtree**   | 1.55 | 0.90 | core      | demon |

### LEATHER — for sling

| Tier | Material | dmg | wt |
|------|----------|-----|-----|
| 1 | rawhide     | 0.75 | 0.60 |
| 2 | cured       | 0.95 | 0.70 |
| 3 | boiled      | 1.15 | 0.85 |
| 4 | drakeskin   | 1.35 | 0.75 |
| 5 | dragonhide  | 1.55 | 0.85 |

### Spawn rate rule

Within a tier's floor band, per pool:

- **Core** = weight 6 (most common)
- **Specialty** = weight 2
- **Elemental** = weight 1 (rare, exciting drop)

Example T3 metal spawn: steel 60%, cold_iron 20%, frost_iron 10%, stormiron 10%.

### Elemental effect

Elemental materials do NOT add flat elemental damage. Their `effective_against` tag applies the standard 1.5× multiplier against matching monster categories, same math as any specialty. Elemental designation is a visual/generation cue (rare drop, themed particle/glow), not a damage-mechanic difference.

### Damage-type / material stacking

Chain damage, material multiplier, material `effective_against`, and weapon `damage_type` weakness/resistance ALL stack multiplicatively. A volcanic iron 2h sword hitting a frost giant (fire-vulnerable AND slash-vulnerable): `8 base × 0.95 material × 1.5 effective_against × 1.5 slash-weakness × chain_mult`. At chain 10 this yields ~254 damage per hit. This is intended — the vulnerabilities layer up for the "really weak" story.

## Ranged mechanics

### Range

| Weapon | Formula | Cap |
|--------|---------|-----|
| Bow     | 5 + (STR-10)/2 | 10 |
| Sling   | 4 + (STR-10)/2 | 8  |
| Crossbow | 7 (fixed)      | 7  |

Crossbow beats bow at STR ≤ 13, ties at 14, loses at 15+. Sling never exceeds bow but is dirt-cheap.

### Per-hit stat bonuses (added to base damage before material/chain scaling)

| Weapon | STR bonus per hit | PER bonus per hit |
|--------|-------------------|-------------------|
| Bow            | +(STR-10)/4 | +(PER-10)/4 |
| Sling          | +(STR-10)/4 | +(PER-10)/4 |
| Dagger (thrown)| +(STR-10)/4 | +(PER-10)/4 |
| Spear (thrown) | +(STR-10)/4 | +(PER-10)/4 |
| Crossbow       | —           | +(PER-10)/4 |

STR 16 + PER 16 archer: +1 + +1 = +2 per hit. At chain 15 = +30 total.

### Crossbow reload

Fires every OTHER turn. Effective DPS is halved. This is the tempo tradeoff for the +2 base damage vs bow.

## Throw mechanics

Only **dagger** and **spear** are throwable, both at **1.0×** damage.

- Treated as a ranged attack. Removes the weapon from inventory, places it on the ground at the target's tile.
- Range = `base + (STR-10)/2` — dagger base 3 (cap 7), spear base 4 (cap 8).
- Break chance on throw: keep existing `_THROW_BREAK_CHANCE` table (`src/game_combat.py:96-104`), or replace with class-based (metal 0.25, rare_metal 0.15, magical 0.08, exotic 0.05, wood 0.35, leather 0.40) — to be decided at implementation time.

All other throw entries in `_THROWABLE_CLASSES` (mace, flail, net, morningstar, rapier, scimitar, sword) are removed.

## Fist STR scaling

`fist.base_damage = 2 × (1 + (STR-10)/10)`. STR 10 = 2 base, STR 15 = 3 base, STR 20 = 4 base. Fist stays intentionally weak — it's the "you dropped your weapon" fallback.

## Anti-cheese rules

- Chain resets to 0 on strike land — no stockpiling between attacks.
- Base weapon damage retuned so chain-5 with the new curve is close to today's chain-5 numbers on comparable gear (protects the current floor while opening the ceiling).
- Wrong answer ends the chain (no rung-drop penalty on top of that).

## Reference: chain damage at iron/ash/boiled

| Weapon | Base | Chain 1 | Chain 5 | Chain 10 | Chain 15 | Chain 20 |
|--------|------|---------|---------|----------|----------|----------|
| Fist          | 2  | 2  | 13 | 28  | 46  | 73  |
| Dagger        | 3  | 3  | 20 | 42  | 69  | 109 |
| Rapier        | 4  | 4  | 26 | 56  | 92  | 146 |
| 1h Sword      | 5  | 5  | 33 | 71  | 115 | 182 |
| 1h Axe / Mace | 6  | 6  | 39 | 85  | 138 | 218 |
| Spear         | 5  | 5  | 33 | 71  | 115 | 182 |
| 2h Sword      | 8  | 8  | 52 | 113 | 183 | 291 |
| 2h Axe        | 10 | 10 | 65 | 141 | 229 | 364 |
| 2h Warhammer  | 11 | 11 | 72 | 155 | 252 | 400 |
| Staff / Glaive | 8 | 8  | 52 | 113 | 183 | 291 |
| Halberd       | 7  | 7  | 46 | 99  | 160 | 255 |
| Bow           | 4  | 4  | 26 | 56  | 92  | 146 |
| Crossbow      | 8  | 8  | 52 | 113 | 183 | 291 (÷2 reload) |
| Sling         | 2  | 2  | 13 | 28  | 46  | 73  |

Reference for balance: T5 damage spells hit ~55 max, cost 22-25 MP per science quiz. Chain 5-10 on a mid-tier weapon is comparable per-question; chain 15+ pulls ahead as the reward for math skill.

## Migration order (proposed)

1. `SUBJECT_TIMER['math'] = (0, 1.0)` — flat WIS seconds. One line.
2. Live combo UI: counter + mult + damage preview + timer bar + SPACE-to-cancel key.
3. Damage formula: polynomial with per-weapon `chain_exponent`. Rewrite `combat.py:360-381`.
4. Universal milestone visuals (rank labels + counter treatments).
5. Rebase common weapon `base_damage` per the table above. Update `tools/balance/generated/templates/weapons/*.json`.
6. Rebuild material files in `data/materials/weapons/` to match this doc (15 metal / 7 wood / 5 leather = 27 total).
7. Trim `_THROWABLE_CLASSES` in `src/game_combat.py:82-93` to dagger + spear only.
8. Add crossbow reload turn.
9. Rebase monster HP per `tools/balance/CURVE.md` targets (still 2-11× under target — separate but interlocking work).
10. Weapon-specific chain specials — follow-up doc.

## Open questions (to resolve before or during implementation)

1. **Weapon `chain_exponent` per class:** default 1.15 for all, or do we ship with per-weapon overrides from day one? Suggest: default 1.15 everywhere; tune per weapon after playtest.
2. **Crossbow reload UX:** is the reload turn silent, or does the UI show a reload progress indicator? What can the player do during it (move? cast?)?
3. **Bosses at chain 20:** later, in the specials doc, we'll decide whether bosses are immune to disable effects (stun/paralyze/impale) at chain 20 or take reduced-duration versions. Damage always applies.
4. **Throw break chance:** keep the per-material `_THROW_BREAK_CHANCE` table or switch to class-based fallback (see Throw section).
5. **Wood ceiling:** wood tops out at 1.55× (worldtree) vs metal's 1.70× (adamantine). Bows/staves have range/reach to compensate; accept the gap or add a rare wood specialty at T5 that reaches ~1.65×?
6. **Fist STR scaling — bumped chain 20:** at STR 20 the fist chain 20 iron-equivalent is `4 × 36.4 = 146`. Higher than a chain-20 sling. Intended?

## Deferred to follow-up doc

- Weapon-specific chain specials at chain 5/10/15/20 (bleed/stun/cleave/pull/etc.). Must be grounded in real `status_effects` names and real damage-modifying flags from `src/monster.py` and `src/combat.py`.
- Boss interaction rules for chain 20 disable effects.
- Migration script for existing save games (probably: no migration; new material system on new saves only).
