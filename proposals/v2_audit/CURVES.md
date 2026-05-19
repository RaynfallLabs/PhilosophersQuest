# Canonical balance curves — read this before auditing

Pre-v2 audit reference. Every subagent uses these formulas to validate balance fit.

## Monster HP curve

```python
def mob_hp(pf):
    if pf <= 0: return 0
    if pf <= 20: return 4 * 1.10 ** (pf - 1)
    return 4 * 1.10 ** 19 * 1.025 ** (pf - 20)
```

Sample values:
- L1: 4.0, L5: 5.9, L10: 9.4, L20: 24.5
- L30: 31.3, L50: 51.3, L70: 84.0, L95: 144

Bosses/mini-bosses/elites multiply this; common monsters cluster within ±50% of the curve.

## Weapon damage formula (chain-peak anchored)

```python
chain_5_mult = chainMultipliers[-1]   # peak of the chain table
weapon_base = max(1, round(mob_hp(peak_floor) / chain_5_mult))
base_damage = max(2, round(weapon_base * material.damage_mult * template.damage_modifier))
chain_damage[i] = max(1, round(base_damage * chainMultipliers[i]))
```

- Uniques have their own `chainMultipliers` (5-15 entries). Most are 5.
- Mythic exemptions (Excalibur, Mjolnir, Sling of David, etc.) can exceed 3x mob_hp at chain peak — listed in tests/test_chain_gradient.py LEGENDARY_EXEMPT.

Template `damage_modifier` table (in src/items.py):
```
bastard_sword=1.15  battleaxe=1.1   club=0.7    composite_bow=1.15
dagger=0.7          flail=1.1       glaive=1.35 great_axe=1.5
greatsword=1.45     heavy_crossbow=1.4 light_crossbow=1.1 longbow=1.0
longsword=1.0       mace=1.05       maul=1.55   quarterstaff=0.85
rapier=0.9          scimitar=1.0    shortbow=0.8 shortsword=0.85
sling=0.6           warhammer=1.4
```

## Armor AC curve

- Tier 1: 1-2 ac_bonus
- Tier 2: 2-3
- Tier 3: 3-4
- Tier 4: 4-5
- Tier 5: 5-6 (uniques can go to 6-8 with chain-equip tier_bonuses peak)

Material `ac_mult` from data/materials/armor/*.json applies on top of template ac_base.

## Mini-boss spawn

Pre-rolled per band (5 bands × 20 levels). Each band: 90% primary + 30% secondary. Expected: 5-7 per run.

## Chest loot

Per-chest single rare roll. rare_chance × CHAIN_RARE_MULT (0.25-2.0×).

## Drop curves

Per-monster `item_chance` from treasure dict. Common-pool monsters cluster:
- L1-15: 15-25% avg
- L16-30: 35-45% avg
- L31-50: 40-50% avg
- L51-70: 50-55% avg
- L71-100: 50-60% avg

## Required fields per entity type

### Weapon (uniques)
id, name, symbol, color, weight, is_unique:true, baseDamage, chainMultipliers, damage_types,
peak_floor (>0), spread, peak_weight, material, template_basis, lore, mastery_blessing

### Armor uniques
id, name, symbol, color, weight, slot, is_unique:true, ac_bonus, peak_floor, spread, peak_weight,
equip_threshold, quiz_tier, material, lore, mastery_blessing

### Shield uniques
same as armor but no slot

### Accessory uniques
id, name, symbol, color, weight, slot, is_unique:true, effects, peak_floor, spread, peak_weight,
equip_threshold, quiz_tier, lore, mastery_blessing

### Wand/Scroll/Spellbook uniques
id, name, symbol, color, weight, is_unique:true, effect, peak_floor, spread, peak_weight,
quiz_tier, quiz_threshold, lore, mastery_blessing

### Potion (no uniques)
id, name, symbol, color, weight, effect, min_level

### Food/Ingredient
id, name, symbol, color, weight, min_level, hp_restore OR ingredient fields

### Ammo
id, name, symbol, color, weight, ammo_type, tier

### Container
id, name, symbol, color, weight, tier (legacy field — chest templates now drive)

### Artifact
id, name, symbol, color, weight, is_unique:true, lore

### Recipe
id, name, ingredients (list), output (effect dict), tier, quiz_tier, quiz_threshold

### Monster
id (key), name, symbol, color, hp, speed, ai_pattern, thac0, peak_floor, spread, peak_weight,
min_level, attacks, resistances, weaknesses, tags, treasure (gold, item_chance, item_tier)

### Chain-equip JSON (armor/shield/accessory)
equip_chain_mode in ('escalator_chain', 'chain'), tier_bonuses keyed 1-5 (contiguous, strictly improving or with documented exception)

## Field anti-patterns

- `peak_floor: 0` AND `peak_weight: 0` AND no special spawn path → orphan, flag
- `is_unique: true` AND no `mastery_blessing` → flag (for items in {weapon, armor, shield, accessory, wand, scroll, spellbook} categories)
- `equip_chain_mode` set AND `tier_bonuses` empty → broken chain-equip
- Item with no `weight` → flag
- Monster with `treasure.unique_drop_id` not resolving → broken reference
