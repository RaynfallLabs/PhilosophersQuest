# Generator Briefing — Philosopher's Quest Content Regeneration

**ALL CONTENT GENERATOR AGENTS MUST READ THIS FIRST.** This is the single source of truth for how to generate fresh content against the unified curve. Skim nothing.

---

## 1. The mission

The game's content (monsters, weapons, armor, ingredients, recipes, etc.) is being **completely regenerated from scratch** against a unified balance curve. The current data files are no longer the reference for numbers — they're style/lore inspiration only.

You're producing new content that:
- Fits the curve (HP/damage/weight/etc. derived from `tools/balance/curve.py`)
- Preserves the geek-dad mythological voice from existing names + lore
- Implements the design intent in `tools/balance/CROSS_SYSTEM_MAP.md` and the per-system docs in `tools/balance/systems/`

**You do not modify code.** You write new data files into `tools/balance/generated/`. The integration into `data/` happens after review.

---

## 2. The curve — read this carefully

The single source of truth for numerical scaling is `tools/balance/curve.py`. Run `py tools/balance/curve.py` to see the anchor table. Key functions:

```python
monster_hp_med(floor)            # median normal monster HP at this floor
monster_hp_tough(floor)          # 75th-percentile monster HP
monster_damage_med(floor)        # median monster damage per hit
monster_damage_tough(floor)      # max damage per hit
monster_thac0_med(floor)         # median THAC0 (lower = more accurate)
monster_thac0_elite(floor)       # elite THAC0 (4 better than median)
player_hp_baseline(floor)        # stat-only HP at this floor
player_hp_target(floor, 'P'/'SL'/'UP')  # target effective HP per profile
cooking_softcap(deepest_floor)   # HP cap from cooking at deepest floor reached
player_chain_5_damage(floor)     # target damage per hit at chain rung 5
weapon_base_damage(min_level)    # base damage for a weapon at this min_level
player_ac_target(floor)          # target AC for prepared player
boss_hp_naive(floor)             # naive boss HP at this floor
boss_hp_effective(floor, mult)   # boss HP after quest layer multipliers
math_tier_dominant(floor)        # T1-T5 dominant at this floor
```

**Every number in your generated content must derive from these functions.** Anchor your monster's HP, your weapon's damage, your recipe's HP gain — all derived. No magic numbers.

---

## 3. AD&D-feel scale reference (the world we're building)

| Axis | F1 | F50 | F100 |
|---|---|---|---|
| Normal monster HP | 4 | 51 | 176 |
| Normal monster damage per hit | 1 | 6 | 21 |
| Monster THAC0 | 19 | 4 | -10 |
| Player stat HP | 12 | 31 | 50 |
| Player cooking softcap | 0 | 5 | 76 |
| Player target HP (prepared) | 12 | 36 | 126 |
| Player chain-5 damage | 1 | 17 | 58 |
| Weapon base damage | 1 | 6 | 23 |
| Player AC | 9 | -2 | -14 |

**Bosses (stored HP):**
- Asterion L20: 144
- Medusa L40: 249
- Fafnir L60: 421
- Fenrir L80: 722
- Abaddon L100: 1235

Use AD&D 2E monsters as the spirit guide. Giant rat HP ~4. Orcs ~6-10. Minotaurs ~50. Ancient dragons ~150-200. Demon princes ~300+. Avoid MMO-inflation.

---

## 4. REALISTIC WEIGHTS (AD&D-style, in pounds)

The player has a STR-derived carry capacity. **Weight must matter.** Quest-item collectors should feel the burden. Use these reference values:

### Weapons (one-handed)
| Weapon | Weight (lb) |
|---|---|
| Dagger | 1.0 |
| Shortsword | 2.0 |
| Longsword | 3.0 |
| Scimitar | 3.0 |
| Rapier | 2.0 |
| Mace | 4.0 |
| Warhammer | 4.0 |
| Battleaxe | 4.0 |
| Flail | 3.0 |
| Club | 3.0 |

### Weapons (two-handed)
| Weapon | Weight (lb) |
|---|---|
| Bastard sword | 5.0 |
| Greatsword | 6.0 |
| Maul | 8.0 |
| Great axe | 7.0 |
| Glaive / Polearm | 7.0 |
| Quarterstaff | 4.0 |

### Ranged
| Weapon | Weight (lb) |
|---|---|
| Shortbow | 2.0 |
| Longbow | 3.0 |
| Composite bow | 3.0 |
| Light crossbow | 5.0 |
| Heavy crossbow | 8.0 |
| Sling | 0.5 |
| Arrow (each) | 0.05 |
| Crossbow bolt (each) | 0.05 |
| Sling stone (each) | 0.1 |

### Armor (body, baseline iron material — multiply by material weight_mult)
| Armor | Weight (lb) |
|---|---|
| Padded | 8 |
| Leather | 10 |
| Studded leather | 13 |
| Hide | 15 |
| Chain shirt | 20 |
| Ringmail | 25 |
| Scale | 30 |
| Chainmail | 40 |
| Breastplate | 20 |
| Splint | 40 |
| Banded | 35 |
| Plate | 50 |
| Full plate | 65 |

Material weight multipliers apply: mithril × 0.5, adamantine × 1.4, etc. So a **mithril full plate** = 65 × 0.5 = 32.5 lb. An **adamantine full plate** = 65 × 1.4 = 91 lb (heavy as hell).

### Shields
| Shield | Weight (lb) |
|---|---|
| Buckler | 2 |
| Light wooden | 5 |
| Heavy wooden | 10 |
| Light steel | 6 |
| Heavy steel | 15 |
| Tower | 30 |

### Other gear
| Item | Weight (lb) |
|---|---|
| Potion | 0.5 |
| Scroll | 0.1 |
| Spellbook | 3.0 |
| Wand | 1.0 |
| Ring | 0.0 (negligible) |
| Amulet | 0.1 |
| Accessory (other) | 0.2-0.5 |
| Food ration (1 day) | 1.0 |
| Cooked meal (typical) | 0.5-2.0 |
| Raw meat / ingredient | 0.3-1.0 |
| Loaf of bread | 0.5 |
| Cheese wheel | 1.0 |
| Backpack (empty) | 2.0 |
| Torch | 1.0 |
| Waterskin (full) | 4.0 |

### Quest items (set these specifically)
| Quest item | Weight (lb) | Reason |
|---|---|---|
| Bronze Bull | 0.5 | small idol |
| Eye of Graeae | 0.2 | small relic |
| Ariadne's Thread | 0.1 | spool of string |
| Each Gleipnir component | 0.2 | abstract bound essence |
| **Leather scrap (each ×10)** | **0.3** | meaningful at 3.0 lb total for the set |
| Broken Gram | 4.0 | broken sword chunk |
| Sigurd's Shovel | 6.0 | a real shovel |
| Philosopher's Stone | 1.0 | dense gem |
| Tablet of Second Death | 5.0 | stone tablet |
| Complete Tablet of Second Death | 6.0 | tablet + embedded stone |
| Philosopher's Wrench | 2.0 | metal tool |
| Scroll of the Lake of Fire | 0.1 | scroll |
| Scroll of Death's Bane | 0.1 | scroll |
| Aegis of Athena (shield) | 10.0 | shield with mythological weight |
| Greater Aegis | 15.0 | heavier, more powerful |
| Vidar's Sandal (armor — foot slot) | 2.0 | leather sandal |

### Carry capacity (player formula — already in code, here for reference)
- STR 8: ~30 lb light load, ~60 lb max
- STR 12: ~50 lb light, ~100 lb max
- STR 16: ~100 lb light, ~200 lb max
- STR 18: ~130 lb light, ~260 lb max

A mid-STR character (12) carries 100 lb max. Armor 30-50 lb + weapon 3-5 lb + 1-day rations 5 lb + few potions + scrolls + 17 lb of Death-killer quest items = 70-80 lb. Tight but doable. Low-STR characters have to choose.

---

## 5. Soft spawn curves — NO HARD GATES

Every material, every monster, every item with floor-locked spawning uses a **bell-curve spawn weight**, not a fixed floor range.

```python
def spawn_weight(floor, peak_floor, spread, peak_weight):
    distance = floor - peak_floor
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    return max(0.02, peak_weight * bell)
```

Materials, monsters, and items each declare:
- `peak_floor`: where they're most common
- `spread`: standard deviation (smaller = narrower band)
- `peak_weight`: maximum spawn weight at peak

Effect: every material/monster has a long, soft tail. An iron sword is rare-rare-rare at F60 but possible. A mithril sword is possible but vanishingly rare at F10. This eliminates jarring "suddenly steel appears at L21" gates.

**Replace `min_level` / `max_level` with `peak_floor` / `spread` in all NEW content.** Use `min_level` as the *first floor where this item COULD plausibly spawn* (where bell weight first crosses ~0.05).

---

## 6. The schemas

### 6.1 Weapon template (`tools/balance/generated/templates/weapons/<id>.json`)

```json
{
  "id": "longsword",
  "name": "longsword",
  "category": "weapon",
  "weapon_class": "sword",
  "hands": 1,
  "damage_types": ["slash"],
  "chain_multipliers": [0.5, 1.0, 1.5, 2.5, 4.0, 6.0],
  "max_chain_length": 6,
  "damage_modifier": 1.0,
  "base_weight_lb": 3.0,
  "speed": 10,
  "compatible_material_classes": ["metal", "rare_metal", "magical_metal"],
  "lore_template": "A {material_name} longsword, balanced for one-handed wielding."
}
```

### 6.2 Material (`tools/balance/generated/materials/<id>.json`)

```json
{
  "id": "mithril",
  "name": "mithril",
  "material_class": "rare_metal",
  "applies_to": ["weapon", "armor", "shield"],
  "peak_floor": 45,
  "spread": 14,
  "peak_weight": 6,
  "damage_mult": 1.2,
  "weight_mult": 0.5,
  "max_enchant": 3,
  "color": [180, 200, 220],
  "armor_ac_bonus": 1,
  "resistances": [],
  "weaknesses": [],
  "vulnerabilities": [],
  "effective_against": [],
  "special_properties": ["light", "elven_favored"],
  "lore_descriptor": "moonlight-pale, weighs almost nothing",
  "unidentified_descriptor": "pale metal",
  "first_pickup_chronicle": "Mithril. Elven-make. It hums against my palm — and weighs less than a memory."
}
```

### 6.3 Armor template (`tools/balance/generated/templates/armor/<id>.json`)

```json
{
  "id": "plate",
  "name": "plate",
  "category": "armor",
  "armor_class_tier": "heavy",
  "slot": "body",
  "base_ac_value": 4,
  "base_weight_lb": 50.0,
  "compatible_material_classes": ["metal", "rare_metal", "magical_metal"],
  "lore_template": "Plate of {material_name}, articulated for combat. Heavy but unyielding."
}
```

### 6.4 Shield template (`tools/balance/generated/templates/shields/<id>.json`)

```json
{
  "id": "kite_shield",
  "name": "kite shield",
  "category": "shield",
  "base_ac_value": 2,
  "base_weight_lb": 10.0,
  "compatible_material_classes": ["wood", "metal", "magical_metal", "dragon_material"],
  "lore_template": "A {material_name} kite shield, tapered to protect the leg."
}
```

### 6.5 Unique named weapon (`tools/balance/generated/uniques/weapons/<id>.json`)

For each of the 78 named weapons in current `data/items/weapon.json`. Preserve name + lore; re-derive numbers from curve.

```json
{
  "id": "hrunting",
  "name": "Hrunting",
  "category": "weapon",
  "weapon_class": "sword",
  "template_basis": "longsword",
  "is_unique": true,
  "hands": 1,
  "damage_types": ["slash", "iron"],
  "base_damage": 9,
  "chain_multipliers": [0.5, 1.0, 1.5, 2.5, 4.0, 6.0, 8.0],
  "max_chain_length": 7,
  "weight_lb": 4.0,
  "min_level": 45,
  "peak_floor": 55,
  "spread": 10,
  "peak_weight": 0.5,
  "max_enchant": 3,
  "special_properties": ["fails_vs_worthy_foes"],
  "lore": "An ancient blade of the Geats. Wieldable, but legends say it falters against truly noble enemies."
}
```

### 6.6 Monster (`tools/balance/generated/monsters/<id>.json` — but consolidate into `monsters.json` at end)

```json
{
  "id": "giant_rat",
  "name": "giant rat",
  "symbol": "r",
  "color": [180, 130, 90],
  "hp": "1d4+2",
  "speed": 8,
  "ai_pattern": "aggressive",
  "min_level": 1,
  "peak_floor": 3,
  "spread": 5,
  "peak_weight": 8,
  "thac0": 19,
  "attacks": [
    {"name": "bite", "damage": "1d2", "type": "pierce"}
  ],
  "tags": ["beast", "vermin"],
  "resistances": [],
  "weaknesses": ["holy"],
  "harvest_tier": 1,
  "harvest_threshold": 1,
  "ingredient_id": "rat_meat",
  "treasure": {"gold": [0, 2], "item_chance": 0.01, "item_tier": 1},
  "lore": "Bloated by dungeon spores. Skitters in the shadows, eyes shining."
}
```

### 6.7 Ingredient + recipe schemas — preserve from current data; rebalance HP gains via curve

```json
// ingredient
{
  "id": "rat_meat",
  "name": "rat meat",
  "symbol": ",",
  "color": [200, 130, 80],
  "weight_lb": 0.3,
  "min_level": 1,
  "source_monster": "giant_rat",
  "recipes": {
    "0": {"name": "ruined rat slop", "sp": 0, "bonus_type": "none", "bonus_amount": 0},
    "1": {"name": "roasted rat", "sp": ...},
    ...
  },
  "lore": "..."
}
```

HP gain comes from `food_system.py` formulas — those stay the same SHAPE (single_max_hp = potency × SINGLE_MULT[quality]); only the SOFTCAP changes per `curve.cooking_softcap(floor)`.

---

## 7. The first-pickup chronicle discovery system

Every new material on first sight in a run triggers a chronicle entry. The agent generating materials provides a `first_pickup_chronicle` string per material in the **first-person geek-dad voice** matching the existing chronicle samples:

> *"Something is following me. I felt it before I saw it. Death itself. I need to run."*
> *"I killed Death. The lake of fire opened beneath it and swallowed it whole."*

Material chronicle examples:
- **Iron:** "Iron. Solid. Honest. The dungeon's first lesson in trust."
- **Silver:** "Silver. The dead will hate this. The good news is, the dungeon has plenty of them."
- **Cold iron:** "Cold iron. The fey will not love this. I am told the trick is in the hammering — cold, never hot."
- **Mithril:** "Mithril. Elven-make. It hums against my palm — and weighs less than a memory."
- **Adamantine:** "Adamantine. The metal does not bend, does not chip, does not forgive."
- **Starmetal:** "Starmetal. The dungeon's roof opened once, long ago, and let this fall."
- **Sunsteel:** "Sunsteel. They forged it from a vein the sun touched at solstice. I can feel the warmth even through the leather wrap."
- **Shadowiron:** "Shadowiron. Drains me a little every turn. Worth it for what it does to the dead."
- **Orichalcum:** "Orichalcum. Atlantis was real, then. Or my memory of it just became real."

Each agent generating materials should write these in this register.

---

## 8. The 8 generator agents — what each one produces

### Agent A — Weapon templates + weapon materials
- Output: `tools/balance/generated/templates/weapons/*.json` (~17 templates)
- Output: `tools/balance/generated/materials/weapons/*.json` (~15 weapon-capable materials)
- Each material's `damage_mult`, `weight_mult`, `max_enchant`, `peak_floor`, `spread`, and special properties per the proposed table in the design doc
- ALL materials include `first_pickup_chronicle` string in geek-dad voice

### Agent B — Armor + shield templates + armor materials
- Output: `tools/balance/generated/templates/armor/*.json` (~10 armor templates)
- Output: `tools/balance/generated/templates/shields/*.json` (~5 shield templates)
- Output: `tools/balance/generated/materials/armor/*.json` (~8 armor-capable materials)
- AC values per material × template combinations validated against curve `player_ac_target(floor)`

### Agent C — Named/unique weapons rebalance (~78 entries)
- Read every named weapon in current `data/items/weapon.json`
- Preserve: name, lore, special property (the *mechanic that makes it unique*)
- Regenerate: base_damage, chain_multipliers, max_chain_length, weight_lb, min_level, peak_floor/spread, max_enchant
- Use curve.weapon_base_damage(min_level) as the anchor; apply ~1.3-2.0× multiplier for "unique" feel
- Output: `tools/balance/generated/uniques/weapons/*.json` per entry
- Boss-quest weapons (Sword of Michael, Reforged Gram, Vidar's Sandal, Gleipnir-tier) get explicit power but capped per the layered-difficulty model

### Agent D — Artifacts + accessories rebalance
- ~24 artifacts (mostly quest items — Bronze Bull, Eye of Graeae, Tablet, Stone, Wrench, Shimmer, etc.) — preserve all but audit weights
- ~290 accessories (rings, amulets, accessories) — preserve all; rebalance their stat bonuses against the new curve (e.g., +CON accessory bonuses should fit `player_hp_baseline` growth)
- Output: `tools/balance/generated/uniques/artifacts/*.json`, `tools/balance/generated/uniques/accessories/*.json`

### Agent E — Ingredients + recipes
- ~296 ingredients: preserve names + lore + monster source. Audit `weight_lb` for realism (0.1-1.0 typical). Recipe per-quality structure preserved.
- ~335 compound recipes: preserve names + lore + ingredient lists. Verify SP values and stat bonuses fit the new curve (e.g., recipes giving +stat shouldn't out-scale the natural progression)
- Output: `tools/balance/generated/data/ingredient.json`, `tools/balance/generated/data/recipes.json`

### Agent F — Wands + scrolls + spellbooks
- Wands: ~50 entries. Preserve effects + lore; rebalance damage/charges against curve (`weapon_base_damage` analog for elemental damage)
- Scrolls: ~30 entries. Preserve effects; rebalance numerical effects against curve
- Spellbooks: ~25 entries. Preserve names + spell IDs; rebalance MP cost and quiz_tier against floor band the spell appears
- Output: `tools/balance/generated/data/wand.json`, `scroll.json`, `spellbook.json`

### Agent G — Monsters (the big one, ~458 entries)
- Read every monster in current `data/monsters.json`
- Preserve: name, symbol, color, ai_pattern, attacks, tags, harvest data, lore, special abilities
- Regenerate: hp (dice string targeting curve.monster_hp_med + variance), thac0 (curve.monster_thac0_med per floor), attack damages, peak_floor + spread (replace min_level/max_level pair)
- Boss monsters (Asterion, Medusa, Fafnir, Fenrir, Abaddon, seal demons, Cow King): HP per curve.boss_hp_naive or curve.monster_hp_med at boss floor × elite multiplier
- Output: `tools/balance/generated/data/monsters.json` (single file)

### Agent H — Schema validator + integration plan
- Build `tools/balance/validate.py` that reads any generator output and checks compliance with curve
- Report drift per content type
- Build `tools/balance/INTEGRATION.md` — step-by-step plan for copying generated files into `data/`, modifying `items.py` for template+material instantiation, updating `dungeon.py` spawn logic, etc.
- Output: `tools/balance/validate.py`, `tools/balance/INTEGRATION.md`

---

## 9. Hard rules for every generator

1. **Read `tools/balance/curve.py` and `tools/audit/CONTEXT.md` first.** Don't generate without context.
2. **Every number must derive from `curve.py` functions.** No magic constants.
3. **Preserve names, lore, and special mechanics.** The voice and design intent of existing content stays. Only numbers change.
4. **AD&D-feel scale.** No MMO-inflation. Player HP at L100 ~120-180, not 1000+.
5. **Soft spawn curves.** `peak_floor` + `spread`, NOT fixed level gates.
6. **Realistic weights** per Section 4.
7. **Use first-person geek-dad chronicle voice** for first-pickup material entries.
8. **Write to `tools/balance/generated/`**, not `data/`. The integration happens after review.
9. **Citations.** When you reference a specific design decision, cite `tools/balance/CROSS_SYSTEM_MAP.md`, `tools/balance/CURVE.md`, `tools/balance/curve.py`, or specific source files.
10. **Return a brief summary** (under 400 words): counts, top 5 design choices made, top 3 open questions for the developer.

---

## 10. Where to find what you need

- **Curve formulas:** `tools/balance/curve.py` (run it to see anchor table)
- **Design intent:** `tools/balance/CURVE.md`, `tools/balance/CROSS_SYSTEM_MAP.md`
- **Existing content (for names/lore/style ONLY):** `data/items/*.json`, `data/monsters.json`, `data/hints.json`
- **Voice samples:** `tools/audit/CONTEXT.md` Section 6 (the chronicle voice)
- **System interactions:** `tools/balance/systems/` (boss quests, divine, secrets, progression, lore)
- **Project rules:** `CLAUDE.md`

Go.
