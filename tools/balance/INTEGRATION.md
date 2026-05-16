# Integration Plan — Regenerated Content into `data/` and `src/`

Step-by-step plan for promoting `tools/balance/generated/` content into the live game.

**Authority:** every change cites a specific file:line. Run `py tools/balance/validate.py` after each tier to confirm no regression.

**Tiers, in order:**

| Tier | Scope | Risk | Files touched |
|---|---|---|---|
| **T1** | Cooking softcap fix | LOW | `src/player.py` only |
| **T2** | Monster file replacement | MEDIUM | `data/monsters.json` only |
| **T3** | Template + material runtime | HIGH | `src/items.py`, `src/dungeon.py`, `src/save_system.py`, `src/combat.py`, `data/items/*.json` |
| **T4** | Uniques + artifacts + accessories swap | MEDIUM | `data/items/{artifact,accessory,wand,scroll,spellbook}.json` + uniques merge |

---

## Pre-flight (do once, before any tier)

### Backup procedure

Move current files to a legacy folder so we can A/B and roll back:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force "data/_legacy/$ts"
Copy-Item -Recurse "data/items" "data/_legacy/$ts/items"
Copy-Item "data/monsters.json" "data/_legacy/$ts/monsters.json"
```

Why copy not move: the game still needs `data/items/*.json` to start (the legacy weapon.json etc. is still loaded today). We swap files **per tier**.

### Validator gate

Run `py tools/balance/validate.py` BEFORE starting integration. Confirm:
- ERROR count = 0 (any ERROR blocks integration of that category)
- Note the WARN baseline so we can detect regressions post-integration
- VALIDATION_REPORT.md is checked in for diffing

---

## Tier 1 — Cooking softcap fix (LOW RISK)

**Goal:** replace the broken flat 1000 cap at `src/player.py:194-213` with `curve.cooking_softcap(deepest_floor_reached)`.

### T1.1 Add `deepest_floor_reached` tracking to Player

**File:** `src/player.py`

The field doesn't exist yet. `level_manager.LevelManager.max_level_reached` (set at `src/level_manager.py:11,37,75`) tracks deepest floor reached but lives on the level manager, not the player. We need it accessible from `Player.increase_max_hp()`.

**Proposed change at `src/player.py:101-103`** (in `__init__`, near `self.cooking_hp_gained`):

```python
# Cooking HP balance: diminishing returns tracking
self.cooking_hp_gained: int = 0    # total max HP gained from cooking (for softcap)
# Deepest floor reached this run — drives cooking softcap formula.
# Updated by the game loop on every floor descent (see Game._change_level
# in src/main.py:420 and LevelManager.max_level_reached in level_manager.py:37).
self.deepest_floor_reached: int = 1
```

**Add update hook in `src/main.py:420`** (the `_change_level` method):

```python
self.dungeon_level = new_level
self.player.deepest_floor_reached = max(
    self.player.deepest_floor_reached, new_level
)
```

(Also in `level_manager.py:37,75` where `max_level_reached` is set — but the simpler hook is the single `_change_level` chokepoint at `main.py:420`.)

### T1.2 Replace softcap formula

**File:** `src/player.py:203-216`

**Current code:**
```python
COOKING_HP_SOFTCAP = 1000  # diminishing returns on cooking-gained max HP

def increase_max_hp(self, amount: int, from_cooking: bool = False):
    if from_cooking:
        cap_factor = max(0.20, 1.0 - self.cooking_hp_gained / self.COOKING_HP_SOFTCAP)
        amount = max(1, int(amount * cap_factor))
        self.cooking_hp_gained += amount
    self.max_hp += amount
    self.hp = min(self.hp + amount, self.max_hp)
```

**Replace with:**
```python
# Cooking softcap is now floor-derived. See tools/balance/curve.py:cooking_softcap()
# F1=0, F50=5, F100=76. The deeper you go, the more cooking can give you.

def _cooking_softcap(self) -> int:
    """Lazy-import the curve so importing player.py stays cheap and offline-tool-safe."""
    try:
        from tools.balance.curve import cooking_softcap   # type: ignore
    except ImportError:
        # Fallback if tools/ isn't on sys.path: derive inline (matches curve.py)
        # Curve baseline: cooking_softcap(f) = player_hp_target(f, 'P') - player_hp_baseline(f)
        # This is intentionally duplicated logic — runtime must not depend on tools/.
        return self._cooking_softcap_inline()
    return cooking_softcap(self.deepest_floor_reached)

def _cooking_softcap_inline(self) -> int:
    """Inline copy of curve.cooking_softcap. Update both if curve constants change."""
    # CONSTANTS — must match tools/balance/curve.py exactly.
    f = max(1, min(100, self.deepest_floor_reached))
    # monster_hp_med:
    if f <= 20:
        mob_hp = max(1, int(4 * (1.10 ** (f - 1))))
    else:
        early_cap = 4 * (1.10 ** 19)
        mob_hp = max(1, int(early_cap * (1.025 ** (f - 20))))
    mob_dmg = max(1, int(mob_hp * 0.12))
    target = max(1, mob_dmg * 6)   # TENSION_KILLS_TO_DIE_P
    progress = (f - 1) / 99
    stat = int(round(12 + (50 - 12) * progress))
    return max(0, max(stat, target) - stat)

def increase_max_hp(self, amount: int, from_cooking: bool = False):
    """Permanently increase max HP. Heals the amount too.

    If from_cooking=True, applies a depth-scaling softcap: when cooking_hp_gained
    nears curve.cooking_softcap(deepest_floor_reached), the bonus shrinks to 20% floor.
    Descent unlocks higher caps — F1 cap is 0, F100 cap is 76.
    """
    if from_cooking:
        cap = max(1, self._cooking_softcap())  # avoid div-by-zero on F1
        cap_factor = max(0.20, 1.0 - self.cooking_hp_gained / cap)
        amount = max(1, int(amount * cap_factor))
        self.cooking_hp_gained += amount
    self.max_hp += amount
    self.hp = min(self.hp + amount, self.max_hp)
```

### T1.3 Test plan

- **Unit test (write new in `tests/test_balance.py`):** call `player._cooking_softcap()` at deepest_floor 1, 50, 100. Assert returns match curve table (0, 5, 76).
- **Logic test:** simulate cooking gain of 10 HP at floor 30 (cap=0). Confirm gain is floored at 1 (the `max(1, ...)`).
- **Save compatibility:** load a pre-fix save (no `deepest_floor_reached` field). Assert it loads with field defaulting to current `dungeon_level`. See T1.4.

### T1.4 Save compatibility

**File:** `src/save_system.py` — needs to handle pre-fix saves missing `deepest_floor_reached`.

**At load (search for `Player()` instantiation):** after restoring fields, do:
```python
if not hasattr(player, 'deepest_floor_reached'):
    player.deepest_floor_reached = state.get('dungeon_level', 1)
```

### T1.5 Rollback

Revert `src/player.py` and `src/main.py:420` to current versions. No data file changes — fully reversible.

---

## Tier 2 — Monster file replacement (MEDIUM RISK)

**Goal:** swap `data/monsters.json` (464 entries) wholesale.

### T2.1 Schema mapping

Generator G produces the new monster schema per `GENERATORS_BRIEFING.md` §6.6. Compare to current consumer in `src/dungeon.py:1083-1118` and `src/monster.py`:

- **`peak_floor` + `spread`** replace `min_level` + `max_level` for spawn weighting
- **`thac0`** is preserved
- **`attacks`** list with `{name, damage, type}` — same shape today
- **`treasure`** with `gold` range, `item_chance`, `item_tier` — needs to be honored by `_pickup` / drop logic at `src/dungeon.py` (currently treasure is largely ad-hoc)
- **`harvest_tier` + `harvest_threshold` + `ingredient_id`** — already consumed by `src/food_system.py:harvest_corpse`

**Required spawn-logic change in `src/dungeon.py:1083-1118`** (in `spawn_monsters`):

Replace the `min_level`/`max_level` eligibility band with a `peak_floor`/`spread` bell:
```python
for k, v in all_defs.items():
    peak = v.get('peak_floor', v.get('min_level', 1))
    spread = v.get('spread', 8)
    base_weight = v.get('peak_weight', v.get('frequency', 5))
    # Bell weight (per curve.spawn_weight signature — see T3.2)
    distance = level - peak
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    weight = max(0.02, base_weight * bell)
    if weight < 0.05:
        continue  # too rare to consider
    eligible[k] = {**v, '_spawn_freq': max(1, int(weight * 100))}
```

Keep `min_level` as a hard floor for monsters that would be too dangerous (sanity-clamp). Drop the proximity-weight system at `dungeon.py:1110-1117` — the bell handles that intrinsically.

### T2.2 Boss preservation

Bosses (Asterion, Medusa, Fafnir, Fenrir, Abaddon, Cow King, 7 seal demons) MUST NOT change ID. Their IDs are referenced from:
- `src/main.py` boss-floor logic (search for `'asterion'`, `'medusa'`, `'fafnir'`, `'fenrir'`, `'abaddon'`)
- `src/boss_levels.py` (the arena handlers)
- `src/game_combat.py:600-610` (seal-break tracking, `self.seals_broken`)

**Action:** before swapping, diff the generated `monsters.json` against current `data/monsters.json` and confirm every boss/seal ID is identical. Reject the swap if any ID is renamed.

### T2.3 Frequency → peak_weight migration

Current monsters use `frequency: int` (1-10 scale). Generated monsters use `peak_weight: float` (0-10 scale). The two are NOT interchangeable for `_weighted_choice` in `dungeon.py:1143`.

**Action:** patch `_weighted_choice` to accept either, defaulting to `peak_weight` if present.

### T2.4 Test plan

- **Data-load test:** load new monsters.json. Assert every entry parses and instantiates a `Monster`.
- **Spawn smoke test:** call `spawn_monsters(rooms, level=N, dungeon)` for N in [1, 20, 50, 80, 100]. Assert non-empty, no exceptions, peak-monster counts are sane (no 100 trolls at F1).
- **Boss test:** load each boss by ID. Assert HP ≥ `curve.boss_hp_naive(boss_floor) × 0.5` (allows quest-layer multiplier room).
- **Re-run validator:** `py tools/balance/validate.py`. Monster WARN count should match expected baseline.

### T2.5 Rollback

`Copy-Item data/_legacy/{timestamp}/monsters.json data/monsters.json` then revert `src/dungeon.py` spawn changes.

---

## Tier 3 — Template + material runtime (HIGHEST RISK)

**Goal:** replace flat `data/items/weapon.json`, `armor.json`, `shield.json` with template + material runtime instantiation.

### T3.1 New classes in `src/items.py`

Add after the existing `Item` class (around `items.py:218`):

```python
class WeaponTemplate:
    """A weapon template defines shape (hands, chain, weight) without material specifics.
    Materials apply at instantiate_weapon() time."""
    def __init__(self, defn: dict):
        self.id              = defn['id']
        self.name            = defn['name']
        self.weapon_class    = defn['weapon_class']
        self.hands           = int(defn['hands'])
        self.damage_types    = defn['damage_types']
        self.chain_multipliers = defn['chain_multipliers']
        self.max_chain_length  = int(defn.get('max_chain_length', len(self.chain_multipliers)))
        self.damage_modifier   = float(defn.get('damage_modifier', 1.0))
        self.base_weight_lb    = float(defn['base_weight_lb'])
        self.speed             = int(defn.get('speed', 10))
        self.compatible_material_classes = set(defn['compatible_material_classes'])
        self.lore_template     = defn.get('lore_template', '')

class ArmorTemplate:
    def __init__(self, defn: dict):
        self.id                 = defn['id']
        self.name               = defn['name']
        self.armor_class_tier   = defn['armor_class_tier']
        self.slot               = defn['slot']
        self.base_ac_value      = int(defn['base_ac_value'])
        self.base_weight_lb     = float(defn['base_weight_lb'])
        self.compatible_material_classes = set(defn['compatible_material_classes'])
        self.lore_template      = defn.get('lore_template', '')

class ShieldTemplate:
    def __init__(self, defn: dict):
        self.id                 = defn['id']
        self.name               = defn['name']
        self.base_ac_value      = int(defn['base_ac_value'])
        self.base_weight_lb     = float(defn['base_weight_lb'])
        self.compatible_material_classes = set(defn['compatible_material_classes'])
        self.lore_template      = defn.get('lore_template', '')

class Material:
    def __init__(self, defn: dict):
        self.id              = defn['id']
        self.name            = defn['name']
        self.material_class  = defn['material_class']
        self.applies_to      = set(defn['applies_to'])
        self.peak_floor      = int(defn['peak_floor'])
        self.spread          = int(defn['spread'])
        self.peak_weight     = float(defn['peak_weight'])
        self.damage_mult     = float(defn.get('damage_mult', 1.0))
        self.weight_mult     = float(defn.get('weight_mult', 1.0))
        self.ac_bonus        = int(defn.get('ac_bonus', 0))
        self.max_enchant     = int(defn.get('max_enchant', 2))
        self.color           = tuple(defn.get('color', [180, 180, 180]))
        self.resistances     = defn.get('resistances', [])
        self.weaknesses      = defn.get('weaknesses', [])
        self.vulnerabilities = defn.get('vulnerabilities', [])
        self.effective_against = defn.get('effective_against', [])
        self.special_properties = defn.get('special_properties', [])
        self.lore_descriptor    = defn.get('lore_descriptor', '')
        self.unidentified_descriptor = defn.get('unidentified_descriptor', '')
        self.first_pickup_chronicle  = defn.get('first_pickup_chronicle', '')
```

### T3.2 Instantiation factories in `src/items.py`

Add after the classes above:

```python
def instantiate_weapon(template: WeaponTemplate, material: Material,
                       enchant_bonus: int = 0, buc: str = 'uncursed',
                       spawn_floor: int = 1) -> Weapon:
    """Build a runtime Weapon from a template+material pair.

    Damage = curve.weapon_base_damage(spawn_floor) × damage_modifier × material.damage_mult
    Weight = template.base_weight_lb × material.weight_mult
    """
    from tools.balance.curve import weapon_base_damage   # safe: this is offline-only data tooling import
    base_dmg = weapon_base_damage(spawn_floor)
    final_dmg = max(1, int(base_dmg * template.damage_modifier * material.damage_mult))
    final_weight = template.base_weight_lb * material.weight_mult
    name = f"{material.name} {template.name}"
    defn = {
        'id': f"{template.id}_{material.id}",
        'name': name,
        'symbol': ')',
        'color': list(material.color),
        'weight': round(final_weight, 2),
        'item_class': 'weapon',
        'min_level': max(1, material.peak_floor - material.spread),
        'weapon_class': template.weapon_class,
        'material': material.id,
        'base_damage': final_dmg,
        'chain_multipliers': template.chain_multipliers,
        'damage_types': list(template.damage_types) + [
            dt for dt in material.special_properties if dt in
            ('silver', 'cold_iron', 'holy', 'fire', 'ice', 'shadow')
        ],
        'two_handed': template.hands == 2,
        'enchant_bonus': min(enchant_bonus, material.max_enchant),
        'buc': buc,
        'lore': template.lore_template.format(material_name=material.name),
        'unidentified_name': f"a {material.unidentified_descriptor} {template.name}",
        'identified': False,
    }
    return Weapon(defn)

def instantiate_armor(template: ArmorTemplate, material: Material,
                      enchant_bonus: int = 0, buc: str = 'uncursed') -> Armor:
    final_weight = template.base_weight_lb * material.weight_mult
    ac_bonus = template.base_ac_value + material.ac_bonus
    name = f"{material.name} {template.name}"
    defn = {
        'id': f"{template.id}_{material.id}",
        'name': name,
        'symbol': '[',
        'color': list(material.color),
        'weight': round(final_weight, 2),
        'item_class': 'armor',
        'slot': template.slot,
        'material': material.id,
        'ac_bonus': ac_bonus,
        'enchant_bonus': min(enchant_bonus, material.max_enchant),
        'buc': buc,
        'min_level': max(1, material.peak_floor - material.spread),
        'lore': template.lore_template.format(material_name=material.name),
        'unidentified_name': f"{material.unidentified_descriptor} {template.name}",
        'identified': False,
    }
    return Armor(defn)

# Equivalent for Shield, omitted for brevity but follows same pattern.
```

### T3.3 New loader functions in `src/items.py`

Replace `load_items('weapon')`/`armor`/`shield` with template+material loaders:

```python
def load_weapon_templates() -> list[WeaponTemplate]:
    path = data_path('data', 'templates', 'weapons')
    return [WeaponTemplate(_load_with_id(p)) for p in os.listdir(path)
            if p.endswith('.json')]

def load_armor_templates() -> list[ArmorTemplate]: ...
def load_shield_templates() -> list[ShieldTemplate]: ...
def load_materials(category: str) -> list[Material]: ...   # 'weapons' or 'armor'
```

### T3.4 Add `spawn_weight()` to `curve.py`

**Proposed signature** (already used by validator and per `GENERATORS_BRIEFING.md` §5):

```python
def spawn_weight(floor: int, peak_floor: int, spread: int,
                 peak_weight: float) -> float:
    """Bell-curve spawn weight. Soft tails — never a hard 0 except at extreme floors."""
    import math
    distance = floor - peak_floor
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    return max(0.02, peak_weight * bell)
```

Add to `tools/balance/curve.py` after `monster_thac0_elite()`.

### T3.5 Rewrite `spawn_items` in `src/dungeon.py:1180-1200`

**Replace lines 1188-1200** (the `'weapon'` and friends loader block):

```python
# -- Regular items (template+material weapons/armor/shields) -- 33% per room --
from items import (load_weapon_templates, load_armor_templates,
                   load_shield_templates, load_materials,
                   instantiate_weapon, instantiate_armor, instantiate_shield)
from tools.balance.curve import spawn_weight

wpn_templates  = load_weapon_templates()
arm_templates  = load_armor_templates()
sh_templates   = load_shield_templates()
wpn_materials  = load_materials('weapons')
arm_materials  = load_materials('armor')

# Other non-template categories load as before
templates = []
for cls_name in ('accessory', 'wand', 'scroll', 'spellbook', 'ammo'):
    try:
        templates += load_items(cls_name)
    except FileNotFoundError:
        pass
eligible = _item_eligible_weighted(templates, level, rng)

def _pick_template_material(template_pool, material_pool, level):
    """Pick a (template, material) pair using bell-curve material weights."""
    # Filter materials compatible with at least one template
    weights = [spawn_weight(level, m.peak_floor, m.spread, m.peak_weight)
               for m in material_pool]
    mat = rng.choices(material_pool, weights=weights, k=1)[0]
    # Filter templates that accept this material's class
    compat = [t for t in template_pool if mat.material_class in t.compatible_material_classes]
    if not compat:
        compat = template_pool[:]
    tpl = rng.choice(compat)
    return tpl, mat

for room in rooms[1:]:
    if rng.random() > 0.33:
        continue
    # 50/50 weapon-or-armor on each room (rest as before)
    roll = rng.random()
    if roll < 0.40:
        tpl, mat = _pick_template_material(wpn_templates, wpn_materials, level)
        item = instantiate_weapon(tpl, mat, enchant_bonus=0, buc='uncursed',
                                  spawn_floor=level)
        _place_one([item], room, dungeon, ground_items, rng)
    elif roll < 0.70:
        tpl, mat = _pick_template_material(arm_templates, arm_materials, level)
        item = instantiate_armor(tpl, mat, enchant_bonus=0, buc='uncursed')
        _place_one([item], room, dungeon, ground_items, rng)
    elif roll < 0.85:
        tpl, mat = _pick_template_material(sh_templates, arm_materials, level)
        item = instantiate_shield(tpl, mat, enchant_bonus=0, buc='uncursed')
        _place_one([item], room, dungeon, ground_items, rng)
    else:
        _place_one(eligible, room, dungeon, ground_items, rng)
```

Replace the same pattern at `dungeon.py:1422-1433` (barracks special-room loader) and `dungeon.py:1529-1530, 1852-1853` (weapon racks in flavor rooms).

### T3.6 Save compatibility

**Problem:** existing saves contain pickled `Weapon` instances whose `id` is e.g. `'iron_longsword'`. The new instantiation produces the same ID format `'{template.id}_{material.id}'`. As long as we preserve the schema (Weapon class shape unchanged), old saves load fine. Pre-existing IDs not in the new system (e.g. `'hrunting'` if Agent C generates uniques) need an alias map.

**Action:** add `_LEGACY_WEAPON_ID_ALIASES` in `src/items.py`:
```python
_LEGACY_WEAPON_ID_ALIASES = {
    # old_id: (new_template, new_material)
    'iron_longsword': ('longsword', 'iron'),
    'steel_longsword': ('longsword', 'steel'),
    # ...
}
```
And in `save_system.load_save()`, if a weapon ID isn't found in templates/materials, look it up in this map.

### T3.7 Damage type system — `src/combat.py:81-150`

The combat code at `src/combat.py:81` already iterates `weapon.damage_types` and checks `monster.resistances`/`weaknesses`. The new instantiation puts material-derived types into `damage_types` (e.g. `['slash', 'silver']` for a silver longsword). **No code change needed** — the existing damage-type advantage system handles it.

**Verify:** monsters with `weaknesses: ['silver']` (vampires, werewolves) take 1.5× from silver weapons via existing `_damage_multiplier()` function at `src/combat.py:9-25`.

### T3.8 `on_kill` quirk hooks — `src/game_combat.py`

Phase 2 work already wired up quirk hooks for kills. **Verify:** these fire by monster ID, not weapon ID — so template+material weapons cause no regression. Smoke test: kill a monster with an instantiated weapon and confirm quirk progress increments.

### T3.9 Hardcoded weapon references in `src/main.py`

Search for these and audit each:

| ID / name | `main.py:line` | Status |
|---|---|---|
| `'sword_of_michael'` | 2119, 2137 | Layer-1 reward for Abaddon. Must remain as a unique entry in `data/items/artifact.json` or the new uniques path. |
| `'scales_of_michael'` | 2119, 2136 | Same |
| `'broken_blade_of_gram'` / `'broken_gram'` | 2118, 3744 | Quest item. Survives template+material — it's an artifact, not a weapon template. |
| `'reforged_gram'` | — | Spawned via `make_*` factory in items.py if it exists, OR via Odin altar throw handler. Audit needed. |
| `'gleipnir'` | 2118, 2134 | Quest item (artifact). |
| `'vidars_sandal'` | 2119, 2135 | Quest item (armor slot foot). |
| `'leather_scrap'` | 3760-63 | Quest collectible. 10 needed for Vidar's Sandal. |
| `'hrunting'`, `'gungnir'`, `'mjolnir'`, `'durandal'`, `'excalibur'` | search again | Uniques — must come from `tools/balance/generated/uniques/weapons/` once Agent C completes. |

### T3.10 Material discovery (first-pickup chronicle)

**Goal:** trigger a chronicle entry the first time the player picks up an item of a given material.

**File:** `src/main.py:_pickup` at line `2052-2160`.

**New player field:**
```python
# In Player.__init__ (player.py:104)
self.chronicle_seen_materials: set[str] = set()
```

**New hook at `main.py:2150`** (right after the existing `_CHRONICLE_ITEMS` quest-item chronicle block, before the Philosopher's Stone branch at line 2151):

```python
# Material-discovery chronicle (first sighting of each material per run)
mat_id = getattr(item, 'material', None)
if mat_id and mat_id not in self.player.chronicle_seen_materials:
    self.player.chronicle_seen_materials.add(mat_id)
    # Look up the material's first_pickup_chronicle string
    from items import _MATERIAL_INDEX   # built at startup; lazy-init OK
    mat_def = _MATERIAL_INDEX.get(mat_id)
    if mat_def and mat_def.first_pickup_chronicle:
        self._log_chronicle(mat_def.first_pickup_chronicle)
```

`_MATERIAL_INDEX` is built once at startup by `items.py` when materials load.

### T3.11 Carry-capacity sanity (quest items now weigh real pounds)

Current formula at `src/player.py:339`: `CARRY_BASE + STR × CARRY_PER_STR = 50 + STR×5`.

- STR 8: 90 lb max
- STR 12: 110 lb max
- STR 16: 130 lb max
- STR 18: 140 lb max

Quest-item totals (per generator briefing §4):
- 10 leather scraps: 3.0 lb
- Bronze Bull: 0.5
- Eye of Graeae: 0.2
- Broken Gram: 4.0
- Sigurd's Shovel: 6.0
- Stone: 1.0
- Tablet: 5.0
- Wrench: 2.0
- Lake of Fire scroll: 0.1
- Sub-total: 21.8 lb

**That's tight for a STR 8 character** (24% of capacity for just the Death-killer set). Per the brief, that's **intentional** — STR-8 characters must trade something. **No code change**. Document in INTEGRATION.md (this file).

### T3.12 Test plan

- **Data-load test:** load every template + every material. Assert non-empty.
- **Instantiation test:** for each compatible (template, material) pair, instantiate. Assert weight > 0, damage > 0, name is `"{material} {template}"`.
- **Save compatibility:** load 3 pre-T3 saves. Confirm weapons resolve via alias map.
- **Validator re-run:** `py tools/balance/validate.py` — must show 0 new ERRORs.
- **Play-test (REQUIRED — see CLAUDE.md play-test rule):** start a new run, walk 3 floors, equip a weapon and armor. Verify chronicle fires on first material pickup. Verify weight totals match what we expect.

### T3.13 Rollback

T3 touches code, not just data. Rollback = `git checkout` on `src/items.py`, `src/dungeon.py`, `src/save_system.py`. Then restore `data/items/weapon.json`, `armor.json`, `shield.json` from `data/_legacy/{ts}/`.

---

## Tier 4 — Uniques + artifacts + accessories swap (MEDIUM RISK)

**Goal:** swap `data/items/{artifact,accessory,wand,scroll,spellbook,ingredient,recipes}.json` files.

### T4.1 Schema check

The generated files at `tools/balance/generated/data/{wand,scroll,spellbook}.json` and `tools/balance/generated/uniques/{artifacts,accessories}/*.json` follow the same schemas as the live files (per inspection — `Accessory`, `Artifact`, `Wand`, `Scroll`, `Spellbook` classes in `items.py` already accept all the keys these files produce).

### T4.2 Consolidate uniques

The generator produces one JSON per artifact (24 files) and per accessory (195 files). The runtime loader expects ONE consolidated file:
- `data/items/artifact.json` (dict keyed by id)
- `data/items/accessory.json` (dict keyed by id)

**Action:** write a one-shot script `tools/balance/consolidate_uniques.py` that reads all generator outputs and merges them into the expected file shape. Run once, check output, then promote.

### T4.3 Unique weapons (waiting on Agent C)

Generator C had not produced output at last check. When it does, consolidate them into `data/items/weapon.json` — these are unique named weapons (Hrunting, Excalibur, Durandal, etc.) that bypass the template+material runtime. They live alongside templates: the spawn logic in `dungeon.py` rolls "unique vs procedural" with low probability (e.g. 1-3% per item slot) per their `peak_floor`/`spread`.

### T4.4 Wand/scroll/spellbook swap

Direct file replacement: `tools/balance/generated/data/{wand,scroll,spellbook}.json` → `data/items/`.

**Notable:** Generator F's `spells.py.proposed` file suggests there's a parallel `src/spells.py` change needed. Open question for the dev.

### T4.5 Ingredient + recipe swap

`tools/balance/generated/data/ingredient.json` (296 entries) → `data/items/ingredient.json`. Same for `recipes.json`.

**Validator caught 8 ingredient WARNs and 22 recipe WARNs** (weight + stat-bonus drift). Review these before swap.

### T4.6 Test plan

- Load each file. Assert dict shape, every entry has required keys.
- Start a new run. Pick up an accessory. Confirm UI shows correct unidentified_name. Identify it via Philosopher's Stone. Confirm effects fire.
- Run an in-game cook. Confirm SP/HP gain matches `food_system._cooking_*` formulas.

### T4.7 Rollback

Same as T2 — copy from `data/_legacy/{ts}/` back to `data/items/`.

---

## Validator re-run after each tier

The validator is the yardstick. After each tier:

```powershell
py tools/balance/validate.py
```

Compare `VALIDATION_REPORT.md` ERROR/WARN/INFO counts against pre-tier baseline. Any new ERROR blocks promotion to the next tier.

---

## Open questions for the developer

1. **`reforged_gram` handling** — is the throw-over-Odin-altar reforge produced via a runtime `make_reforged_gram()` factory, or is it generator C's job to produce it as a unique? The current `src/main.py:3744` references it by ID.
2. **Spell system change** — Generator F dropped `spells.py.proposed`. Is the integration plan supposed to also rewire spells, or only the spellbook items?
3. **Unique weapon spawn rate** — at what probability should a unique weapon roll instead of a procedural template+material weapon? 1%? 3%? Suggest 1% per item slot, gated to material's `peak_floor` band.

---

## Phase summary checklist

- [ ] Pre-flight: backup + validator baseline captured
- [ ] T1: cooking softcap — `player.py`, `main.py:420`, `save_system.py`
- [ ] T1 test: floor 1/50/100 softcap matches curve
- [ ] T2: monsters.json swap
- [ ] T2 test: boss IDs intact, spawn smoke test passes
- [ ] T3: items.py + dungeon.py + save_system.py (template + material)
- [ ] T3 test: instantiate + save-load + material chronicle
- [ ] T3 play-test: 3-floor manual walkthrough
- [ ] T4: artifact/accessory/wand/scroll/spellbook/ingredient/recipes
- [ ] T4 test: in-game cook + accessory equip
- [ ] Final validator run — assert 0 ERROR, no WARN regression
- [ ] Commit with message referencing each tier
