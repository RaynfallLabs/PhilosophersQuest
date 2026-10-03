# Weapons and Materials
**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/items.py` (Weapon, Ammo), `src/combat.py` (CLASS_MECHANIC_INFO, _weapon_key, class ladder dispatch), `src/game_combat.py` (CombatMixin — equip, throw, ranged openers), `src/hero_specials.py` (hero combat passives)
**Data:** `data/items/weapon.json` (96 uniques), `data/items/ammo.json` (14 entries), `data/materials/weapons/*.json` (54 materials across 9 material_classes), `tools/balance/generated/templates/weapons/*.json` (22 common templates)
**Related docs:** [combat](combat.md) · [monsters](monsters.md) · [items](items.md) · [identify_v3](identify_v3.md) · [progression](progression.md) · [status_effects](status_effects.md) · [magic](magic.md) · design history: [`docs/design/chain_combat_v2.md`](../design/chain_combat_v2.md), [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md), [`docs/design/uniques_v2_14.md`](../design/uniques_v2_14.md)

## Purpose

This doc covers the weapon catalog itself — what a weapon LOOKS LIKE on disk, how commons differ from uniques, how material tags modify damage, how the 22 class templates map to the chain-ladder, and what the 149+ unique proc flags actually do.

For the combat loop (chain quiz, peak-damage formula, hit resolution, resistance/weakness application, boss-immunity gating, reflect handling), see [combat.md](combat.md).

## Design intent

- **Weapon class carries most of the identity.** Base damage, reach, hands, damage type, chain exponent, and chain-special ladder all come from the weapon's class template or (for uniques) a class-aligned hand-tuned block.
- **Material is a modifier, not an identity.** `damage_mult`, `weight_mult`, `effective_against` tags, and spawn depth come from the material. 54 materials across 9 classes offer variety; most are weighted so a "core" (iron, ash, boiled_leather) is 6× more common than its specialty/elemental siblings.
- **Uniques inherit the class ladder.** Every one of the 96 uniques carries `chain_exponent: 1.15` and inherits its class ladder for free. The unique's job is to layer a distinctive passive on top — lifesteal, lightning splash, boss-doom DoT, +STR on kill, etc.
- **Grade-10 lore + geek-dad canon.** Every unique has a 1-paragraph `lore` block referencing a specific mythic source. See `feedback_trivia_voice.md` for the Easter-Egg Pattern (reveal a cool detail that makes the kid go experience the source).

## Data model / schema

### Weapon JSON schema (data/items/weapon.json)

The file is a dict keyed on weapon id. Every entry is a UNIQUE weapon in the current build (96 entries). Common weapons spawn from `tools/balance/generated/templates/weapons/*.json` combined with a material from `data/materials/weapons/*.json`.

```jsonc
{
  "soul_reaver": {
    "name": "Soul Reaver",
    "class": "scimitar",        // weapon_class — drives _weapon_key dispatch
    "variant": "1h",            // "1h" | "2h"
    "tier": 5,                  // 1–5 depth band
    "material": "adamantine",   // material id (looked up in data/materials/weapons/)
    "mathTier": 5,              // quiz_tier — difficulty of the math chain quiz
    "baseDamage": 14,           // flat per-hit before multipliers
    "chainMultipliers": [0.2, 0.55, 1.0, 1.8, 3.0],  // legacy per-rung array (polynomial supersedes)
    "chain_exponent": 1.15,     // v2.14.0: polynomial path — uncapped chain
    "maxChainLength": 5,        // legacy; irrelevant when chain_exponent is set
    "damageTypes": ["slash", "pierce"],  // for resistance/weakness lookup
    "symbol": ")", "color": [80, 50, 180],
    "weight": 3.0, "twoHanded": false, "reach": 1,
    "stunChance": 0.0, "bleedChance": 0.3, "knockback": false,
    "ignoreShield": false, "requiresAmmo": null,
    "floorSpawnWeight": {"1-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 2},
    "containerLootTier": "rare", "value": 5000, "min_level": 82,
    "unidentified_name": "a dark whispering curved blade",
    "lore": "Few who have held the Soul Reaver remember doing so willingly…",
    "quiz_tier": 5,
    "lifestealPercent": 0.3,     // unique proc — see §Unique procs
    "is_unique": true,
    "max_enchant": 5,
    "weapon_class_chain": "finesse",  // "normal" | "finesse" — purely cosmetic design-note tag
    "growth_on_innocent_kill": true,  // unique proc
    "design_notes": "Signature chain: finesse opener…"
  }
}
```

### Weapon Python class (`src/items.py::Weapon` @ line 298)

The `Weapon.__init__` block (lines 298–627) loads all of the above plus:

- 15 "standard" fields: `weapon_class`, `variant`, `tier`, `material`, `base_damage`, `chain_multipliers`, `chain_exponent`, `quiz_tier`, `damage_types`, `two_handed`, `reach`, `stun_chance`, `bleed_chance`, `knockback`, `ignore_shield`, `requires_ammo`, `infinite_ammo`, `value`, `enchant_bonus`, `unidentified_name`, `poison_chance`, `burn_chance`, `confuse_chance`.
- 149+ unique proc fields (see §Unique procs).
- `max_chain_length` as a `@property` returning `len(self.chain_multipliers)` — always derived, so pickled weapons from before `chain_exponent` was added stay correct. The property silently overrides any `max_chain_length` written in JSON.
- `cursed` as a `@property` on `.buc == 'cursed'`.

### Ammo JSON schema (data/items/ammo.json)

14 entries. 5 arrows (iron / steel / hardened_gold / diamond / dragonbone), 5 bolts (iron / steel / hardened_gold / diamond / adamantine), 3 mythic ammo (Arrows of Eros, Arrows of Artemis, Bolts of Zeus), 1 joke (shotgun_shell, `min_level: 9999`).

```jsonc
{
  "diamond_arrow": {
    "name": "diamond arrow",
    "symbol": "\\", "color": [160, 220, 255], "weight": 0.04,
    "min_level": 61, "ammo_type": "arrow", "tier": 4,
    "damage_bonus": 3,        // flat +N to base before material/chain scaling
    "count_min": 5, "count_max": 15,
    "floor_spawn_weight": {"61-80": 100, "81-100": 60, ...},
    "value": 20,
    "unidentified_name": "arrows",
    "lore": "Diamond points ground to molecular sharpness…"
  }
}
```

Ammo tiers 1–5 progress `damage_bonus 0, 1, 2, 3, 5` — the T5 skip from +3 to +5 is intentional, late-game ammo is rare and should feel like it.

### Material JSON schema (data/materials/weapons/*.json)

54 material files across 9 `material_class` buckets:

```jsonc
{
  "id": "iron",
  "name": "iron",
  "material_class": "metal",
  "applies_to": ["weapon", "armor", "shield"],
  "peak_floor": 8,                // floor where this material spawns most
  "spread": 12,                   // how wide the spawn tail is (12 = very long)
  "peak_weight": 10.0,
  "min_level": 1,
  "damage_mult": 1.0,             // multiplier on weapon.base_damage (iron = 1.0 reference)
  "weight_mult": 1.0,             // multiplier on weapon.weight
  "max_enchant": 2,               // material cap on enchant_bonus
  "color": [180, 180, 180],
  "armor_ac_bonus": 0,
  "resistances": [],              // armor only
  "weaknesses": [],               // armor only
  "vulnerabilities": [],          // wielder takes extra damage from these tags
  "effective_against": [],        // weapon deals 1.5x to monsters with these tags
  "special_properties": ["common", "reliable"],
  "lore_descriptor": "honest gray, with the faint ring of a forge",
  "unidentified_descriptor": "a plain blade",
  "design_notes": "…"
}
```

Materials are loaded lazily into `_MATERIAL_EFFECTIVE_AGAINST` and `_MATERIAL_VULNERABILITIES` dicts in `combat.py::_load_material_tags`. First call reads every `*.json` in `data/materials/weapons/`.

## Material classes (9 classes, 54 materials)

Material **class** controls what else inherits it (sorting / loot banding / UI color). The combat engine reads individual material IDs — the class is a design-side bucket.

### metal (9) — core industrial
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| copper | 0.70 | 1.10 | — |
| tin | 0.85 | 0.80 | — |
| bronze | 0.80 | 1.05 | fey |
| tempered_bronze | 1.15 | 1.00 | construct, golem |
| iron | **1.00** | **1.00** | — (reference baseline) |
| silver | 0.90 | 1.05 | undead, lycanthrope |
| volcanic_iron | 0.95 | 1.00 | ice_creature, frost_creature |
| steel | 1.20 | 0.95 | — |
| pig_iron | 1.20 | 1.50 | — |

### rare_metal (11) — specialty / depth
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| cold_iron | 1.10 | 1.00 | fey, demon (also vuln=demon) |
| frost_iron | 1.15 | 1.00 | fire_creature, salamander |
| stormiron | 1.15 | 1.00 | water_creature, sea_creature |
| ghost_iron | 1.15 | 0.95 | undead, ghost, spectre |
| hematite | 1.05 | 1.10 | undead |
| hardened_gold | 1.20 | 1.25 | undead, fiend |
| cobalt_steel | 1.20 | 1.00 | — |
| damascus_steel | 1.25 | 0.90 | — |
| elven_silver | 1.00 | 0.80 | undead |
| mithril | 1.40 | 0.55 | — |
| meteoric_iron | 1.45 | 1.60 | — |

### magical_metal (10) — late-game canonical
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| soulsteel | 1.15 | 0.95 | undead, ghost |
| glassteel | 1.20 | 0.85 | elemental |
| godweave | 1.30 | 0.60 | — |
| sunsteel | 1.35 | 1.00 | undead, fiend |
| shadowiron | 1.35 | 0.90 | celestial, aberration |
| starmetal | 1.45 | 0.85 | aberration, void_spawn, outsider |
| orichalcum | 1.60 | 0.95 | outsider, demon_major |
| titanforged | 1.65 | 1.70 | giant |
| adamantine | **1.70** | 1.30 | — (T5 reference) |
| quicksilver | 0.95 | 0.70 | — (also vuln=fire) |

### exotic_metal (4) — weird depth-5
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| obsidian | 1.25 | 0.70 | demon_minor |
| tungsten | 1.40 | 1.60 | heavy_armor |
| void_touched | 1.55 | 0.80 | aberration, void_spawn (also vuln=holy) |
| primordial_stone | 1.75 | 2.00 | — |

### wood (5) — stave / sling / bow baseline
| id | dmg × | wt × | effective_against | vulnerabilities |
|---|---|---|---|---|
| willow | 0.75 | 0.65 | — | fire |
| oak | 0.75 | 0.90 | — | fire |
| yew | 0.95 | 0.85 | fey | fire |
| ash | **1.00** | **0.90** | — | fire |
| blackthorn | 1.15 | 1.25 | — | fire |

### rare_wood (5)
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| petrified_wood | 1.00 | 1.30 | — |
| ironwood | 1.15 | 1.15 | — |
| wormwood | 1.30 | 1.30 | — |
| dragonwood | 1.30 | 1.00 | dragon |
| silverbark | 1.35 | 0.80 | undead, fey |

### exotic_organic (3)
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| leviathan_rib | 1.20 | 1.30 | — |
| treant_heart | 1.35 | 0.90 | — (vuln=fire) |
| worldtree | 1.55 | 0.90 | demon |

### leather (5) — sling exclusive
| id | dmg × | wt × | vulnerabilities |
|---|---|---|---|
| rawhide | 0.75 | 0.60 | acid |
| cured_leather | 0.95 | 0.70 | fire |
| boiled_leather | 1.15 | 0.85 | fire |
| drakeskin | 1.35 | 0.75 | — |
| dragonhide | 1.55 | 0.85 | — |

### dragon_material (2) — dragon-slayer
| id | dmg × | wt × | effective_against |
|---|---|---|---|
| dragonbone | 1.30 | 0.80 | dragon, wyrm, reptilian |
| petrified_dragon | 1.50 | 1.10 | dragon |

### Spawn-weighting

Within a floor band + material_class, the generator weights `peak_weight` × a bell curve around `peak_floor` with width `spread`. The chain_combat_v2 design doc proposed a 6/2/1 core/specialty/elemental split within a tier. Current data uses `peak_weight`+`spread` instead — same spirit, more granular tuning per material.

### Material naming drift (known rough edge)

21 unique weapons reference material names that don't exist as material files: `"divine iron"`, `"dark iron"`, `"enchanted iron"`, `"spectral iron"`, `"legendary"`, `"bone"`, `"fang"`, `"hardwood"`, `"wood"`, `"gold"`, `"leather"`, `"dad"` (Punch in the Face). These are pure lore strings. Any material lookup silently returns `1.0 damage_mult, 1.0 weight_mult, no effective_against`. The weapon's `base_damage` still applies, so the weapon still works — it just doesn't carry a material-driven anti-tag bonus.

Audit still open: either rename the fictional materials to real ones, or make `_load_material_tags` tolerate spaces (`"volcanic iron"` ↔ `"volcanic_iron"`). v2.18.0 fixed the one that mattered — `vulcans_brand`'s `"volcanic iron"` → `"volcanic_iron"` — so the sword's fire-tag effective_against actually fires.

## Weapon classes (15 in JSON, 22 common templates)

### Classes present in weapon.json (uniques)

```
axe        (6)  bow        (1)  club       (6)  dagger     (7)  fist       (1)
mace       (2)  morningstar(1)  net        (1)  ranged     (6)  scimitar   (7)
spear     (15)  staff      (7)  sword     (33)  warhammer  (2)  zweihander (1)
```

### Common weapon templates (`tools/balance/generated/templates/weapons/*.json`)

22 files:

```
bastard_sword   battleaxe       club            composite_bow   dagger
flail           glaive          great_axe       greatsword      heavy_crossbow
light_crossbow  longbow         longsword       mace            maul
quarterstaff    rapier          scimitar        shortbow        shortsword
sling           warhammer
```

Each template declares a reference `base_damage`, `weight`, `reach`, `two_handed`, `damage_types`, `chain_exponent` (1.15), and a `class_mechanic` tag. The generator cross-products each template with each material (filtered by `applies_to`) to build the common spawn pool. Uniques do NOT use these templates — they hand-author every field.

### `_weapon_key` dispatch — from `class` to chain-special ladder

`combat.py::_weapon_key(weapon)` normalizes `weapon.weapon_class` + `two_handed` + id/name hints into one of the 15 class-ladder keys the dispatch table uses:

```
fist, dagger, rapier, sword, 2h_sword, axe, 2h_axe, mace, 2h_warhammer,
spear, halberd, glaive, staff, bow, crossbow, sling
```

Aliases handled inside `_weapon_key`:

- `sword` (variant 1h) → `sword`; `sword` (2h) → `2h_sword`
- `zweihander` → `2h_sword`; `scimitar` → `sword`; `morningstar` → `mace`
- `axe` (1h) → `axe`; `axe` (2h) → `2h_axe`
- `blunt` common-template → by id/name + hands: `staff` (quarterstaff), `mace` (mace / warhammer-1h / club / flail), `2h_warhammer` (maul / great-hammer)
- `warhammer` (1h) → `mace`; `warhammer` (2h) → `2h_warhammer`
- `club`, `flail`, `hammer` (1h) → `mace`; `hammer` (2h) → `2h_warhammer`; `maul` → `2h_warhammer`
- `polearm` → by id/name: `halberd`, `spear`, else `glaive`
- `ranged` catch-all (legacy uniques) → by `requires_ammo` + `infinite_ammo`: bolt-type ⇒ `crossbow`, infinite ⇒ `sling`, else `bow`

This normalization was added in v2.15.0 (2026-09-13). Before it, every common hafted-blunt weapon (mace, warhammer, maul) was getting zero chain specials because `weapon_class='blunt'` had no entry in the specials table.

## Class mechanics (22 entries, from common templates)

Common templates ship a `class_mechanic` tag that the engine reads at hit time to layer per-attack behavior ON TOP of the universal class chain-special ladder. These are the "signature" of a given weapon shape — Meisterhau for longsword, backstab for dagger, etc. The 22 entries in `combat.py::CLASS_MECHANIC_INFO` (line 23):

| mech_id | Short name | Behavior |
|---|---|---|
| `backstab` | Backstab | ×2 damage if the target is unaware of you (sleeping or ambush+not-aware). At max chain only. (dagger) |
| `bleed_at_max` | Bleed | On chain rung 3+, inflicts `bleeding` 1d4/turn for 3 turns. (battleaxe, great_axe) |
| `cleave_at_max` | Cleave | At max chain, on a KILL: cleave 0.5× damage to one adjacent foe. (greatsword) |
| `cleave_at_max_plus_bleed` | Cleave + Bleed | Max-chain kill: cleave + apply `bleeding` 1d6/turn for 3. (great_axe) |
| `concussion_at_max` | Concussion | Max chain: 35% chance to `confused` 2t. (club) |
| `defensive_parry` | Parry | Max chain: `parry_armed` +2 AC for 2t. (quarterstaff) |
| `finesse_dex` | Finesse | Uses DEX instead of STR for the damage bonus. (rapier) |
| `free_stones` | Free Stones | Max chain: 25% ricochet to adjacent foe (0.6×). Ammo weightless + auto-gathered. (sling) |
| `ignores_all_armor` | Armor-Piercing | Ignores ALL armor AC. Single-shot reload. (heavy_crossbow) |
| `ignores_half_armor` | Half Armor-Pierce | Ignores half of target armor AC. (light_crossbow) |
| `ignores_shield` | Shield-Bypass | Ignores shield AC bonus. (flail) |
| `master_strike` | Master Strike | At chain 3+, +15% damage AND treats target AC as 1 lower — longsword Meisterhau. (longsword) |
| `quick_riposte` | Riposte | Max chain: `riposte_armed` for 2t; if struck next turn, free 0.85× counter. (shortsword) |
| `rapid_shot_at_max` | Rapid Shot | Max chain: follow-up arrow at half damage on same target. (shortbow) |
| `reach_2` | Reach 2 | Strike foes 2 tiles away; at max chain hits all in the line. (quarterstaff) |
| `str_bonus_range_7` | Range 7 (STR) | Range 7 tiles; each STR point above 10 adds 5% to damage. (composite_bow) |
| `stun_at_max` | Stun | On chain rung 3+, 20% chance to stun (resist roll vs HP/300). (mace) |
| `stun_knockdown_at_max` | Stun + Knockdown | Max chain: stun + knockdown (lose 2 turns), stronger resist DC. (maul) |
| `versatile` | Versatile | +20% damage when wielded 2H (no shield). Fires every hit. (bastard_sword) |
| `anti_heavy_at_max` | Anti-Armor | Max chain: +50% damage vs heavy-armored (tag or name-hint). (warhammer-variant) |
| `armor_pierce_at_max` | Pierce at Max | Max chain: +35% damage AND ignores 50% of armor. (hooked polearm variants) |
| `guaranteed_hit` | Never Miss | Chain 0 promotes to chain 1 — a failed quiz still lands a minimum hit. (Fail-not unique, kept as unique signature) |
| `returning_blow` | Returning Blow | Max chain: strike rebounds on you for half damage. (Green Chapel Axe unique) |

The last two (`guaranteed_hit`, `returning_blow`) are unique-only. Everything else was shed from uniques in v2.14.0 — the class chain-special ladder covers the same ground, and leaving them on uniques double-fired. See `docs/design/uniques_v2_14.md` §Redundant class_mechanic values retired.

Fired in `combat.py::player_attack._callback`:
- Pre-damage (`combat.py:1157-1196`): `versatile`, `master_strike`, `str_bonus_range_7`, and the at-max multipliers (`anti_heavy_at_max`, `armor_pierce_at_max`, `ignores_all_armor`, `ignores_half_armor`).
- Post-damage (`combat.py:1865-1964`): bleed/stun/backstab/disarm/concussion/riposte/returning_blow/parry_armed/rapid_shot; cleave + sling-ricochet surfaced via `on_complete` kwargs.

## Class chain-special ladder (abridged)

Full ladder in [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md). Rung-dispatch rule: **only the HIGHEST qualifying rung fires** (chain 20 does NOT additionally fire 15/10/5).

```
Chain 5 → 10 → 15 → 20

Fist:        slow 2t → sunder 3t → deep_wound+bleed → stun+deep_wound+bleed
Dagger:      bleed 4t → deep_wound 3t → poison+bleed → ruptured+poison+bleed
Rapier:      bleed 3t → sunder+bleed → sunder+bleed+player_DR → +longer
Sword(1h):   bleed 3t → bypass DR → blade_flow 3 + player DR → blade_flow 4
2h_Sword:    +1 adj 0.7× → +2 adj 0.6× → 360° 0.5× + bleed → 2-tile 0.5× + blade_flow 3
Axe(1h):     bleed 4t → sunder → cleave 1 + bleed → cleave all + sunder + regen
2h_Axe:      cleave + bleed → cleave 2 + sunder → full arc + bleed+sunder → 360° + regen
Mace:        stun 1t (40%) → armor_crack → stun+armor_crack → stun+crack+bypass DR
2h_Warhammer: stun 2t → stun+adjacent → 2-tile stun+crack → +AoE dmg
Spear:       bleed 3t → bypass DR → pierce behind + bleed+bypass → impale+line-2
Halberd:     bleed 3t → sunder+bleed → reach line +bleed+sunder → full 2-reach
Glaive:      cleave 1 0.7× → cleave 2 + bleed → arc + bleed → 2-tile arc + bleed+slow
Staff:       slow 2t → all-adj slow → player DR + regen → all-adj slow + player regen HP+MP
Bow:         bleed 3t → blinded → bypass DR → vitals ×2 + blinded + bleed + bypass
Crossbow:    bypass DR → +slowed → skip 3 reloads → ballista line + slow all + bypass
Sling:       ricochet 25% → guaranteed ricochet + stun → stun+slow → shatter 3-tile radius
```

## Equip flow

Weapons are **not** quiz-gated. `_equip_item(weapon)` at `main.py:5462` calls `player._apply_equip(weapon)` immediately and consumes a turn — the player's class/skill carries the equip, no questions asked. This differs from Armor and Shield, which require a geography-threshold quiz (`_start_armor_quiz`), and Accessory, which requires a history-threshold quiz (`_equip_accessory`).

The `equip_threshold` field exists on 4 quest-mythic weapons (hunt_captains_sword, wendigo_fang, echidna_fang, vulcans_brand) — this is DEAD data (SYSTEMS_AUDIT.md P3). There is no weapon-equip quiz path.

### 2H weapon ↔ shield handshake

`_equip_item(weapon)` where `weapon.two_handed`:
1. If `player.shield`, call `player.try_unequip_slot(shield)`. Fails if shield is cursed → message, abort.
2. `player._apply_equip(weapon)` sets `player.weapon`, applies `on_equip_status`, triggers `prophecy_blade` (first-equip tag roll), handles `cursed_lineage` ledger (Pelops: -1 STR + 2 max HP), `selects_wielder` lock.

`_equip_item(shield)` where `player.weapon` is two-handed: refuses with "You cannot use a shield while wielding a two-handed weapon!" at `main.py:5481`.

### Ranged weapons

Ranged weapons (bow / crossbow / sling / "ranged") live in the SAME `player.weapon` slot as melee — there's no separate `ranged_weapon` slot in the inventory sense. BUT `Player.ranged_weapon` as a property returns the current weapon only if it has `requires_ammo`. The `_fire_ranged` path reads `player.ranged_weapon`; `_start_combat` reads `player.weapon`. This caused the Musashi passive bug fixed in v2.18.0 (see `combat.py:1214-1224` call-out below).

### Throw

Only dagger and spear are throwable (v2.14.0 trimmed the throwable list). See `game_combat.py::_THROWABLE_CLASSES`:

```python
_THROWABLE_CLASSES = {
    'dagger': 1.0,   # designed for throwing
    'spear':  1.0,   # javelin
}
```

Throw range = `base + (STR-10)//2`, dagger base 3 (cap 7), spear base 4 (cap 8). Break chance per material in `_THROW_BREAK_CHANCE`: bone 50%, iron 35%, steel 25%, hardened_gold 20%, diamond 10%, adamantine 5%; legendary/named default 5%.

## Damage dice / chain-mult / material tags (combined example)

A **steel longsword** vs a **frost giant** (slash-vulnerable, fire-vulnerable) at chain 10:

```
base_damage      = 5                   (longsword template)
material.damage_mult = 1.20            (steel)
chain_exponent   = 1.15 → mult = 10^1.15 = 14.1
dtype_mult       = 1.5                 (frost giant weak to slash)
str_factor       = 1.0 + 0.03*(STR-10) = 1.15 at STR 15
enchant_bonus    = +1

damage = max(1, round((5 + 1 + 0 + 0) * (14.1 * 1.20) * 1.5 * 1.15 * 1.0))
       = max(1, round(6 * 16.92 * 1.5 * 1.15))
       = max(1, round(175))
       = 175
```

Change the weapon to a **volcanic_iron longsword** (effective_against ice/frost creatures) and the material.effective_against layer kicks in via `_damage_multiplier`:

```
dtype_mult = max(1.5 slash-vuln, 1.5 volcanic_iron-eff) = 1.5
```

Same multiplier — a single 1.5× from `_damage_multiplier`. The design doc's "layer up" story in chain_combat_v2.md §Damage-type/material stacking describes a case where material.effective_against and the weapon's damage_type weakness BOTH apply (volcanic iron 2h sword hitting a frost giant that is both fire-vulnerable AND slash-vulnerable → ~254 dmg at chain 10). The `max()` in `_damage_multiplier` means only ONE of the material/damage-type bonuses applies per call; the other layer comes from `_material_effective_multiplier` applied separately (currently inlined into `_damage_multiplier` as a merged list, so in practice this is still a single 1.5×, not a 2.25× stack — the design intent and the current code don't quite line up; see audit note below).

**Audit cross-ref:** `combat.py::_material_effective_multiplier` exists but is **not called** by `player_attack` — the material.effective_against is folded into `_damage_multiplier` via the lazy-loaded `_MATERIAL_EFFECTIVE_AGAINST` dict. So the "stacking" is `max()`, not multiplicative. The 2.25× yew-crossbow-vs-fey bug fixed on 2026-06-07 is the symptom of a different double-count path (unique vs compositional); see `combat.py:1068` `if is_unique:` guard.

## Unique procs (149 fields — representative sample)

Every unique has at least one distinctive mechanic. The audit of 2026-05-30 counted ~149 "promised" mechanics across the 96 uniques; v2.18.0's weapon count surfaces 213 live proc field uses (counting multi-tag fields). Below is a representative sample (not exhaustive — see `src/items.py::Weapon.__init__` lines 379–627 for the full schema and `data/items/weapon.json` for the data).

| Weapon | Flag(s) | Behavior |
|---|---|---|
| **Soul Reaver** | `lifestealPercent: 0.3`, `growth_on_innocent_kill: true`, `chain_exponent: 1.15` | Heals 30% of damage dealt. Killing a non-hostile NPC grants +1 `blade_flow` stack (rewired from "next hit auto-crit" in v2.14.0). |
| **Mjolnir** | `chain_lightning_at_chain_n: {from_chain: 6, splash_pct: 0.5, max_targets: 1}`, `effective_against: [giant]`, `undead_bonus: 2.5` (inert) | At chain 6+, splash lightning damage to one adjacent enemy of the primary target. Material + unique anti-tag arrays stack. |
| **Dawnbreaker** | `effective_against: [undead]`, `ignore_resistances: true`, `burnChance: 0.3`, `holy` damage type | Shatters resistance checks; every hit vs undead is +1.5× via per-weapon anti-tag; burn proc on top. |
| **Sword of Michael** | `abaddon_bonus_damage: "2d20"`, `holy_smite_message: true` | Rolls 2d20 bonus damage vs `monster.kind == 'abaddon_destroyer'`. Emits flavor messages on evil-tagged hits (demon / undead / evil). |
| **Excalibur** | `kill_heal_amount: 10`, `cast_me_away: true` | +10 HP on kill. At HP ≤ 25%, one-shot: drain weapon enchant -1 and grant `life_save` status. One use per run. |
| **Gram (reforged)** | `ignore_resistances: true`, `base_damage: 18` | Clamps `dtype_mult` to 1.0 — resistances stop cutting damage. Weaknesses still apply. |
| **Fail-not** | `cannot_miss_before_player_takes_damage: true`, `class_mechanic: guaranteed_hit` | Chain 0 promotes to chain 1 (bow). While `_combat_player_taken_damage` is False, every miss lands as a minimum hit. |
| **Gungnir** | `cannot_miss: true` | Chain 0 → chain 1 always. The spear has never missed. |
| **Hrunting** | `one_shot_chain_save_per_floor: true` | Once per floor, chain 0 is demoted to chain 1 instead of a miss. `_hrunting_save_used` reset in `_change_level`. |
| **Harpe** | `petrify_on_crit: true`, `skip_chain_warmup_vs_tag: [medusa, gorgon, ...]` | At chain ≥ 15, apply `petrifying 3t` (rewired from the retired crit path). Against matching tags, chain starts at rung 2. |
| **Tyrfing** | `cursedMissBacklash: 3`, `cursed_lineage` fallback | On chain 0, player.hp -= 3 (floor at 0). Cursed-blade identity. |
| **Mistilteinn** | `damage_double_vs_resistant_at_max: true` | At max chain, double damage if target has ANY resistance (Baldur's flaw). |
| **Laevateinn** | `boss_doom_dot_at_chain_5: {pct_max_hp_per_turn: 0.05, duration: 30}` | At chain 5 hit on a boss, apply `doom_dot` for 30t ticking 5% max HP/turn. Boss-gated via `'boss' in tags OR is_boss`. |
| **Ruyi Jingu Bang** | `chain_modulated_reach: {4: 4, 7: 5}` | Reach grows with chain; `can_melee_attack` uses `max(values)` for targeting (known lie at chain 0). |
| **Robin Hood's Longbow** | `stealth_damage_bonus: 0.5` | +50% damage when the player has `invisible` status. |
| **Kusanagi** | `surrounded_proc_bonus: true` | When 3+ enemies are adjacent to the player, ×1.25 damage. Rewired from force-crit in v2.14.0. |
| **Khopesh of Anubis** | `kill_max_hp_bonus: 1`, `kill_max_hp_cap: 10` | +1 max HP per kill, capped at +10 total. |
| **Chandrahasa** | `low_hp_damage_bonus: true` | At HP < 50%, damage mult up to 2× at 0% HP. |
| **Green Chapel Axe** | `class_mechanic: returning_blow`, `on_hit_regen: N` | Max chain blows return to the wielder for half damage. The beheading-game pact. |
| **Oathkeeper** | `adjacent_pet_damage_bonus: 0.25` | +25% damage when any pet is within 1 tile of the player. |
| **Curtana** | `spare_kill_chance: 0.25`, `spare_kill_max_hp_per_floor: 5` | On a kill-blow, 25% chance to spare: leave monster at 1 HP, grant player +1 max HP. Up to 5/floor (counter never reset — bug). |
| **Zulfiqar** | `every_hit_secondary_target: {splash_pct: 0.5, range_tiles: 1}` | Every successful hit also deals 50% splash to one adjacent enemy. Bifurcated-tip identity. |
| **Gandiva** | `multi_arrow_at_chain_5: {targets: 3, damage_per: 0.5}` | At max-chain ranged hit, hit up to 3 other visible monsters at 50% damage. |
| **Rod of Moses** | `chain_tier_status_table: {"3": {status: slowed, duration: 3}, ...}` | Ten plagues by chain rung — status applied when `chain >= key`. |
| **Sudarshana Chakra** | `return_to_hand_ward: true`, thrown returning | On max-chain kill, next monster attack misses outright (consumed by `monster.attack`). |
| **Spear of Longinus** | `weep_heal_on_kill_scaled: 0.1` | On kill, heal player by 10% of target's max_hp. |
| **Vulcan's Brand** | `effects: {status: burning, effect_chance: 0.3, effect_duration: 5}`, `material: volcanic_iron` | **v2.18.0 fix:** material id corrected from `"volcanic iron"` (space) to `"volcanic_iron"` so effective_against tags (ice/frost) apply. On-hit burn status via Weapon.effects (wire-up 2026-05-30). |
| **Kladenets (Samosek)** | `_note: "design_intent: counterAttackChance=0.25 ..."` | **v2.18.0 fix:** removed inert `counterAttackChance: 0.25` field. Added `_note` recording the Slavic "Sword That Fights Itself" counter-attack design, flagged for a future passive-defense hook. |
| **Punch in the Face** | `base_damage: 35`, `material: dad` | Dad-tier joke. Not part of the balance curve. Material lookup silently returns 1.0× — the base_damage carries the gag. |

### Full proc field list

See `src/items.py::Weapon.__init__` lines 379–627 for the schema. Field count by category:

- **On-equip status / aura** (6): `on_equip_status`, `wielder_fire_immunity`, `wielder_status_immunity`, `equipped_light_aura`, `equipped_monster_aggro_radius`, `equipped_sound_radius_modifier`, `equipped_ally_aura_buff_str`.
- **Chain modifiers** (7): `cannot_miss`, `cannot_miss_before_hurt`, `one_shot_chain_save_per_floor`, `chain_bonus_on_low_hp_window`, `skip_chain_warmup_vs_tag`, `chain_no_reset_on_tag`, `chain_modulated_reach`.
- **At-max / per-chain-rung procs** (10): `multi_arrow_at_chain_5`, `boss_doom_dot_at_chain_5`, `chain_lightning_at_chain_n`, `damage_double_vs_resistant_at_max`, `reveal_tag_on_chain_5_kill`, `return_to_hand_ward`, `chain_tier_status_table`, `every_hit_secondary_target`, `combat_start_aoe_confuse_chance`, `surrounded_proc_bonus`.
- **Damage mults vs condition** (8): `first_blood_bonus`, `low_hp_damage_bonus`, `stealth_damage_bonus`, `damage_bonus_vs_gaze`, `adjacent_pet_damage_bonus`, `prophecy_blade`, `undead_bonus`, `effective_against` (list), `bonus_damage_vs_tag` (dict of 8 pre-known tags).
- **On-hit statuses + chances** (10): `stunChance`, `bleedChance`, `poisonChance`, `burnChance`, `confuseChance`, `freezeChance`, `apply_heal_block_chance`, `random_status_from_pool`, `effects` (dict), `knockback`.
- **On-kill** (10): `lifestealPercent`, `kill_heal_amount`, `growingPower + killsToGrow`, `kill_max_hp_bonus + cap`, `aoe_slow_on_kill`, `weep_heal_on_kill_scaled`, `kill_count_karma_adjust`, `extra_action_after_kill`, `growth_on_innocent_kill`, `spare_kill_chance`, `summon_after_kill_with_tag`.
- **Shields / resistances bypass** (3): `ignore_shield`, `ignore_resistances`, `ignores_all_armor` / `ignores_half_armor` (via class_mechanic).
- **Cursed / selected** (6): `cursed_lineage`, `selects_wielder`, `betrays_at_low_hp`, `cursedMissBacklash`, `cast_me_away`, `glows_near_orcs`.
- **Flavor / messaging** (3): `abaddon_bonus_damage` (Sword of Michael), `holy_smite_message`, `vigilance_aware`.
- **Damocles** (2): `damoclean_counter_threshold`, `damoclean_counter_auto_kill`.
- **Lore-only / inert as of v2.18.0** (5): `floor_start_reveal_chance` (Sharur partial wire), `karma_disappear_proc`, `weapon_immune_to_enchant_loss` (Chrysaor; audited to work), `equipped_light_aura` (works via sight-radius bump), `can_dig` (shovel weapons / pit mechanic).

The audit's bottom line: of ~149 unique mechanics declared in JSON on 2026-05-30, waves 2 / 3 / 4 wired all but ~5. The remaining dead flags are documented in SYSTEMS_AUDIT.md P3-P4.

## Hero combat passives

Set on `player.hero_passives: set[str]` by the hero-specials system and checked at combat hook sites:

| Passive | Hero | Hook | Effect |
|---|---|---|---|
| `will_to_power` | Friedrich Nietzsche | `combat.py:1208` | +30% damage when player HP ≤ 30% |
| `witcher_mutations` | Geralt of Rivia | `combat.py:1212` | +20% damage vs all monsters |
| `niten_ichi_ryu` | Miyamoto Musashi | `combat.py:1214-1224` | **v2.18.0 fix:** +15% damage when a non-ammo weapon is in the primary slot. Was previously gated on `weapon AND ranged_weapon`, which broke because Musashi ships two melee swords and `ranged_weapon` only accepts ammo-requiring weapons. The new gate preserves the two-swords fantasy for any melee loadout. |
| `cynic_detachment` | Diogenes | `combat.py:1242` | Cursed items don't penalize (buc=-1 is skipped) |
| `witcher_resists` | Geralt | — | Elemental resists at ingress (not in combat.py) |
| `demigod_hide_25` | Achilles | — | 25% physical reduction (not in combat.py) |
| `plato_no_shard` | Plato | — | Identify-side (bypasses the ID shard) |
| `elder_blood_escape` | Ciri | — | Escape mechanic (not in combat.py) |
| `vengeance_wakes` | Boudicca | — | Status counter (not in combat.py) |
| `resonant_frequency` | Nikola Tesla | `monster.py:678` | Shock-counter on melee hits: `self.take_damage(dmg // 3)`. Fires back at the attacker. |

## v2.18.0 fixes (weapons scope)

Full commit `409e15d` message in the git log — these are the weapon/combat-adjacent entries:

1. **`Monster.__init__` reads `is_boss` from JSON** (`monster.py:104`). Repair for 10 mini-bosses that had lost their boss-immunity to charm/paralyze/confuse/sleep/hold_monster/fear: `blood_archon`, `iron_patriarch`, `whispering_crone`, the 7 `seal_demon_*` monsters.
2. **`DeathMonster.take_damage` accepts kwargs** (`monster.py:1706-1708`). Signature now matches `Monster.take_damage(amount, damage_type='physical', ignore_resistance=False)` so spell/wand paths and chain-passive procs don't TypeError on Death.
3. **`vulcans_brand` material id** fixed from `"volcanic iron"` (space) to `"volcanic_iron"` (underscore) so `_load_material_tags()` finds the file and the effective_against=[ice_creature, frost_creature] actually applies.
4. **`kladenets` _note + removed `counterAttackChance`.** Dropped the inert `counterAttackChance: 0.25` field; added a `_note` field recording the Slavic "Self-Swinger" counter-attack design intent so a future passive-defense hook can wire it in.
5. **Niten Ichi-Ryū retargeted** (`combat.py:1214-1224`). Gate rewired from `weapon AND ranged_weapon` to `weapon is not None AND NOT weapon.requires_ammo`. Musashi's +15% dual-wield bonus now fires for his starting two-sword kit (which is two melee swords, zero `ranged_weapon` slot occupancy).
6. **7 quest armors deleted** from `data/items/armor.json`: `quest_spawn_nemean`, `quest_spawn_green_knight`, `quest_spawn_serpent`, `quest_spawn_arachne`, `quest_spawn_erlking`, `quest_spawn_anansi`, `quest_spawn_nidhoggr`. All had `min_level: 9999` and no code implementing their `quest_spawn_*` methods. ~15KB of dead stat blocks removed. (Not weapons but same wave + same unreachable-content pattern.)

## Invariants (don't break)

- **96 uniques in weapon.json. All `is_unique: true`. All `chain_exponent: 1.15`.** Don't add a unique without setting both. Don't add a common there — commons live in templates+materials.
- **22 common templates.** Don't add a new weapon shape without a template file; the generator cross-products it with every applicable material.
- **Weapon class drives chain-special ladder via `_weapon_key`.** Any new class alias needs an entry in `_weapon_key` else the weapon gets zero class chain specials.
- **Material names must match a file id OR be understood as "lore material = 1.0 everything."** Don't half-ass this; if a unique needs a special material (e.g. "divine iron"), add the file to `data/materials/weapons/`.
- **Per-weapon effective_against is UNIQUE-ONLY** (`combat.py:1068` guard). Compositional weapons inherit the material's `effective_against`; counting the weapon's inherited copy ALSO double-dips. If you want a common to get an anti-tag bonus, put it on the MATERIAL.
- **Ammo tiers 1-5 progress 0/1/2/3/5 `damage_bonus`.** The T4→T5 jump from +3 to +5 is intentional. Don't smooth it.
- **Fist is weakest.** Fist base scales `2 × (1 + max(0, STR-10)/10)`. STR 10 → 2, STR 20 → 4. Chain 20 at STR 20 ≈ 146 damage. Keep it under the floor-1 sling baseline.
- **Only dagger + spear are throwable.** v2.14.0 trimmed. Don't resurrect scimitar / mace / rapier throw entries — they were novelty, not tactical.
- **Crit is retired.** Do not resurrect `crit=True` paths. Any legacy JSON field (`critMultiplier`, `petrifyOnCrit`) is dead data; keep the loader for compat, don't act on the value.

## Interactions

- **[combat](combat.md)** — this is the parent system. Weapons feed into `player_attack`, `_apply_chain_class_pre_damage`, `_apply_chain_class_post_damage`.
- **[monsters](monsters.md)** — resistances / weaknesses lists, tags for `effective_against`, `is_boss`, `drain_heals_self`, `dragon_scales`.
- **[identify_v3](identify_v3.md)** — unidentified weapons work normally in combat; the player just sees "unidentified <true name>" and doesn't know BUC/enchant. Blessed weapons gain `holy` damage type at use-site. See [identify_v3](identify_v3.md) for the one-question identify flow.
- **[progression](progression.md)** — enchant caps per slot (weapon = +5, Panoply of Hephaestus → +6). STR gates the `str_factor` damage multiplier for melee and the ranged stat bonus for bow/sling/dagger/spear. PER gates the ranged stat bonus for all ranged + ranged weapon reach bonus.
- **[status_effects](status_effects.md)** — `armor_crack`, `sundered`, `deep_wound`, `blade_flow`, `ruptured`, `impaled` added for the v2.14.0 chain ladder. Also `bleeding`, `poisoned`, `burning`, `stunned`, `paralyzed`, `confused`, `blinded`, `slowed`, `shielded`, `heal_blocked`, `petrifying`, `frozen`.
- **[magic](magic.md)** — Weapons with `holy` damage type (blessed OR Dawnbreaker/Michael) interact with the magic resistance pipeline. The `apply_spell_damage_passives` function layers chain-equip bonuses onto spell damage, mirroring the weapon-side `_damage_multiplier`.

## History of major decisions

- **2026-05-19 — Combat rebuild** canonizes 22 class mechanics + 149 unique proc intent.
- **2026-05-30 — Engine waves 2 / 3 / 4** wire the inert JSON flags on the uniques. Every unique has at least one distinctive mechanic in code after this.
- **2026-06-07 — Ranged double-dip fix** (yew crossbow vs fey). `effective_against` on compositional weapons gated to `is_unique: true` only.
- **2026-09-07 — Chain combat v2 design.** Polynomial damage, flat WIS seconds, SPACE strike. See [`docs/design/chain_combat_v2.md`](../design/chain_combat_v2.md).
- **2026-09-10 — Weapon specials + crit removal (v2.14.0).** 6 new statuses, per-class 5/10/15/20 ladder, crit retired. See [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md).
- **2026-09-11 — Uniques rebase (v2.14.0).** 96 uniques → `chain_exponent: 1.15`. Iconic exceptions keep bumped `base_damage`. 8 redundant `class_mechanic` values stripped. See [`docs/design/uniques_v2_14.md`](../design/uniques_v2_14.md).
- **2026-09-13 (v2.15.0) — `_weapon_key` normalization** for `blunt`/`polearm` common templates.
- **2026-10-02 (v2.18.0) — Full audit fix wave.** See §v2.18.0 fixes above.

## Testing

- **`tests/test_weapon_loading.py`** — all 96 uniques load, every required field present.
- **`tests/test_material_tags.py`** — every material file in `data/materials/weapons/` has valid `effective_against` / `vulnerabilities` lists.
- **`tests/test_engine_wave*_unique_mechanics.py`** — field-load + consumer-code presence per wave.
- **`tests/test_combat_invariants.py`** — chain-peak shape, class-tag presence, bypass-DR behavior.
- **`tests/test_bundled_dirs_contain_only_runtime_files`** — guards the PyInstaller bundle doesn't include non-runtime material files.
- **No play-test** for randomized unique rolls or deep-floor cross-material combos.

## Known rough edges

Open items from SYSTEMS_AUDIT.md, not fixed in v2.18.0:

- **`boomstick` dual-identity bug.** `template_basis: "crossbow"` but `weapon_class: "ranged"` + `min_level: 9999`. Routes through BOW specials, so its crossbow-identity reload lockout doesn't apply.
- **`mjolnir_shard` lore vs code.** Design notes claim a chain-5 lightning proc; only Mjolnir carries `chain_lightning_at_chain_n`.
- **`Curtana._spare_kill_floor_hp` counter not reset** on floor change. "Per floor" silently becomes "per run."
- **`chandrahas` ≠ `chandrahasa`.** Two nearly identical-named entries (T4 finesse-3.0× and T5 normal-2.0×). Likely duplicate; both spawn under different tier bands.
- **`equipped_monster_aggro_radius`, `equipped_sound_radius_modifier`, `_karma_disappear_rolled_this_floor`** loaded but no consumers.
- **`sword_of_michael::max_chain_length=6`** silently overridden by the `@property` returning `len(chain_multipliers)`. Works incidentally; JSON field is authoritative-in-name-only.
- **`ammo.shotgun_shell` + `boomstick`** both `min_level: 9999`. No natural discovery path.
- **Ranged weapons consume ammo BEFORE the quiz.** Chain 0 miss still burns ammo. Unarmed melee whiffs are free.
- **21 fictional-material uniques.** `"divine iron"`, `"legendary"`, `"bone"`, `"fang"`, `"hardwood"`, `"wood"`, `"gold"`, `"leather"`, `"dad"` — all return 1.0× everything from material lookup. Either rename or add material files.
