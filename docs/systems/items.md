# Items

**Scope.** Item classes, canonical JSON schemas, equip gating, enchant/BUC
model, carry bonus, how items drop (floor spawn + chest loot), inventory
rules. For scroll/wand/spellbook *effects* see [magic](magic.md); for
corpse harvest/cook see [food_system](food_system.md); for the identify
quiz see [identify_v3](identify_v3.md); for chest/trap logic see
[containers_lockpick](containers_lockpick.md).

Source of truth: `src/items.py` + `data/items/*.json`.

---

## 1. Base `Item` schema

Every item class subclasses `Item` (`src/items.py:215`). Base fields set on
all items regardless of class:

| Field | Type | Default | Notes |
|------|------|---------|-------|
| `id` | str | required | JSON object key. Loader stamps it onto the defn. |
| `name` | str | required | Identified display name. |
| `symbol` | str | required | One-char glyph for terrain rendering. |
| `color` | `[r,g,b]` | required | RGB triple. |
| `weight` | float | 1.0 | Pounds. STR gates carry; see §9. |
| `item_class` | str | "unknown" | `weapon|armor|shield|accessory|wand|scroll|spellbook|ingredient|artifact|ammo|food|potion|lockpick|container`. Loader stamps this from the JSON filename. |
| `min_level` | int | 1 | Earliest floor the item is eligible to spawn. |
| `lore` | str | "" | Shown on the lore screen after full ID. |
| `set_id`, `set_name` | str | "" | Set-membership tags. |
| `is_unique` | bool | false | Named/legendary marker. Routes identify to T4+ (see [identify_v3](identify_v3.md)), filters spawn pool, drives chest `rare_chance` draws. |
| `peak_floor` | int | 0 | Bell-curve peak (0 = no bell weighting). |
| `spread` | int | 10 | Bell-curve σ. |
| `peak_weight` | float | 0.0 | Bell-curve peak amplitude. |
| `floor_spawn_weight` / `floorSpawnWeight` | `{"<lo>-<hi>": weight, …}` | `{}` | Alternative to the bell curve: step weights per 20-floor band. See §8. |
| `container_loot_tier` / `containerLootTier` | str | "common" | Chest-pool bucket (`common`/`rare`). |
| `identified` | bool | **property** | Read-only alias for `id_level >= 4`. Setter bumps `id_level` to 4 when true, 0 when false. |
| `id_level` | int | from `identified` default | 0 = fully unknown, 5 = fully identified. See [identify_v3](identify_v3.md). |
| `id_tier` | int | 0 | Explicit philosophy-tier override for the identify quiz (0 = derive from spawn depth). |
| `buc` | str | "uncursed" | `blessed` | `uncursed` | `cursed`. |
| `buc_known` | bool | false | Reveals BUC in HUD/kit; see [ui](ui.md). |
| `unidentified_name` | str | copy of `name` | **Required when `identified` is false** (post-v2.18.0 sweep added it to 24 spoilered artifacts; see §12). |
| `carry_bonus` | `{stat, amount}` or null | null | Applied while held in inventory; see §10. |
| `save_bonus` | `{cat, amount}` or null | null | Permanent save bonus while equipped; capped +5 by `Player.save_bonus_for`. |

Loader (`load_items`, `src/items.py:1208`) picks a class from `_CLASS_MAP`
by filename stem, slurps the whole JSON dict, and instantiates each
`{id: defn}` pair.

---

## 2. Weapon

File: `data/items/weapon.json`. Class: `Weapon`
(`src/items.py:298`). Weapons are **not** gated by an equip quiz —
combat itself is the quiz (chain-mode math; see [combat](combat.md)).

Canonical fields on top of base:

```json
{
  "soul_reaver": {
    "name": "Soul Reaver",
    "class": "scimitar",
    "variant": "1h",
    "tier": 5,
    "material": "adamantine",
    "baseDamage": 14,
    "chainMultipliers": [0.2, 0.55, 1.0, 1.8, 3.0],
    "damageTypes": ["slash", "pierce"],
    "symbol": ")",
    "color": [80, 50, 180],
    "weight": 3.0,
    "twoHanded": false,
    "reach": 1,
    "stunChance": 0.0,
    "bleedChance": 0.3,
    "ignoreShield": false,
    "requiresAmmo": null,
    "unidentified_name": "a dark whispering curved blade",
    "quiz_tier": 5,
    "identified": false,
    "lifestealPercent": 0.3,
    "peak_floor": 92,
    "spread": 12,
    "peak_weight": 0.5,
    "max_enchant": 5,
    "is_unique": true,
    "chain_exponent": 1.15
  }
}
```

Required-ish fields: `class` (weapon_class), `tier`, `material`,
`baseDamage` or legacy dice `damage`, `chainMultipliers`,
`damageTypes`, `symbol`, `color`, `peak_floor`, `peak_weight`.

Chain combat v2 lets a template opt into `chainExponent` (`mult = chain
** exponent`) instead of a handcrafted multipliers array; see
[combat](combat.md).

Ranged weapons set `requiresAmmo: "arrow"` (etc.) and route through the
`ranged_weapon` slot; see §5.

Weapons also carry 100+ opt-in flags for unique mechanics (lifesteal,
`chain_lightning_at_chain_n`, `prophecy_blade`, `wielder_fire_immunity`
…). These are loaded by `Weapon.__init__` into waves 2–4 and consumed in
`combat.player_attack`; see [combat](combat.md) for the dispatch table.

### Templates + materials (compositional)

Common weapons/armor/shields aren't authored one-by-one — they're built
on demand by `instantiate_weapon(template_id, material_id, …)` and
sibling factories (`src/items.py:1692`). Templates live under
`data/templates/{weapons,armor,shields}/` (shape, chain, slot, mechanics);
materials under `data/materials/{weapons,armor}/` (damage mult, weight
mult, max enchant, resistances, lore descriptor).

Composed id is `{material_id}_{template_id}` (e.g. `iron_long_sword`).
Name is assembled by `compose_item_name(material, template, noun)` with
redundancy stripping ("steel iron boots" → "steel boots",
"boiled leather hide armor" → "Boiled Leather Armor"); the
unidentified form is composed by `compose_unidentified_name`.

Dropping a weapon on the floor: `pick_random_weapon_for_floor(floor,
rng)` rolls a material by `material_spawn_weight` (bell curve on
`peak_floor`), picks a compatible template, and calls
`instantiate_weapon`. Uniques (Soul Reaver, Excalibur, …) stay in
`weapon.json` and are drawn separately.

---

## 3. Armor

File: `data/items/armor.json`. Class: `Armor`
(`src/items.py:643`). Equip gate: **geography threshold**.

Canonical schema (unique example):

```json
{
  "hide_of_nemean_lion": {
    "name": "Hide of the Nemean Lion",
    "symbol": "[", "color": [200, 180, 80],
    "weight": 16.0, "min_level": 65,
    "slot": "body",
    "tier": 4,
    "material": "adamantine",
    "ac_bonus": 7,
    "enchant_bonus": 0,
    "equip_threshold": 4,
    "quiz_tier": 4,
    "damage_resistances": {"slash": 0.35, "blunt": 0.3, "pierce": 0.25},
    "can_be_cursed": false,
    "identified": false,
    "unidentified_name": "a rough amber pelt of unnatural density",
    "floorSpawnWeight": {"61-80": 1, "81-100": 2},
    "max_enchant": 3,
    "peak_floor": 72, "spread": 12, "peak_weight": 0.3,
    "template_basis": "hide",
    "is_unique": true,
    "unskinnable": true
  }
}
```

Required: `slot`, `ac_bonus`, `tier`, `material`.

`slot` ∈ `['head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak',
'shirt']` (`ARMOR_SLOTS`, `src/items.py:9`). Each slot has one item;
`Player.armor_slots[8]` indexed by `ARMOR_SLOTS.index(slot)`.

Optional per-template fields: `on_equip_status` (status applied while
worn), `chain_bonus`, `fire_reflect`, `berserk_trigger`,
`invisibility_power` (activated per-floor power), plus 30+ armor-proc
flags (`cannae_encirclement`, `boundary_guardian`, `thors_step`,
`divine_smithing`, …) consumed by `src/armor_procs.py` and
[combat](combat.md).

Chain-equip (legendary uniques only): set `equip_chain_mode:
"escalator_chain"` or `"chain"` plus `tier_bonuses: {"1": {…}, …,
"5": {…}}` and the equip quiz switches modes — see
`src/chain_equip.py` and §6.

---

## 4. Shield

File: `data/items/shield.json`. Class: `Shield`
(`src/items.py:740`). Equip gate: **geography threshold** (same path as
armor).

```json
{
  "greater_aegis_of_athena": {
    "name": "Greater Aegis of Athena",
    "symbol": ")", "color": [200, 220, 255],
    "weight": 8.0, "min_level": 65,
    "tier": 4, "material": "adamantine",
    "ac_bonus": 5, "enchant_bonus": 0,
    "equip_threshold": 3,
    "quiz_tier": 4,
    "damage_resistances": {"fire": 0.35, "magic": 0.4, "petrifying": 1.0},
    "unidentified_name": "a polished shield of supernatural brightness",
    "floorSpawnWeight": {"81-100": 2},
    "is_unique": true,
    "equip_chain_mode": "escalator_chain",
    "tier_bonuses": {"1": {}, "2": {}, "3": {}, "4": {}, "5": {}}
  }
}
```

Shields cannot be equipped alongside a two-handed weapon
(`Player.can_equip_shield`). Signature fields: `fire_reflect`
(Svalinn), `quiz_timer_bonus` (Ancile — bonus seconds on quiz timers).

---

## 5. Accessory (rings + amulets + belts)

File: `data/items/accessory.json`. Class: `Accessory`
(`src/items.py:776`). Equip gate: **history threshold**.

```json
{
  "ring_magic_res_a": {
    "name": "ring of magic resist",
    "symbol": "=", "color": [160, 140, 200],
    "weight": 0.1, "min_level": 25,
    "slot": "ring",
    "equip_threshold": 3,
    "quiz_tier": 3,
    "effects": {"status": "magic_resist", "duration": -1},
    "unidentified_name": "warded pewter ring",
    "lore": "...",
    "floorSpawnWeight": {"21-40": 80, "41-60": 80, "61-80": 80, "81-100": 80},
    "peak_weight": 0.4,
    "peak_floor": 30, "spread": 13
  }
}
```

`slot` ∈ `{ring, amulet, belt, none}`. `none` = carry-only (equip
blocked; the item is intended to live in the pack and grant a
`carry_bonus`).

Slots: `Player.accessory_slots` has 4 ring slots; `amulet_slot`
and `belt_slot` are single. Equipping a second amulet/belt swaps the
existing one into inventory (see `_apply_equip`,
`src/player.py:1349`).

`effects`: `{status, duration}` for permanent debuff/buff statuses, or
`{stat, amount[, stat2, amount2]}` for stat bonuses. Applied by
`Player._apply_equip`; reversed on unequip. Charge-based accessories
(Lyre of Orpheus, Hand of Glory) set `use_charged: true` and are listed
in the power menu with their remaining `charges`/`max_charges`.

Cosmetic variants of a ring/amulet collapse to one canonical id (see
`LEGACY_ACCESSORY_ID_REMAP`, `src/items.py:1246`); the per-run
appearance is dealt once from `data/items/accessory_appearances.json`.

#### Ring / Amulet subtypes

The game has no separate `Ring` or `Amulet` class — both are
`Accessory` with `slot: "ring"` or `slot: "amulet"`. The distinction
lives entirely in the JSON `slot` field.

---

## 6. Equip gating (one-question threshold)

All equip quizzes run in **threshold mode** with `threshold =
item.equip_threshold`. Zero-tolerance applies: **any wrong answer =
fail**. The `_threshold_line` helper (`src/game_render.py:53`) prints
every threshold line in the format `"<Label>: N correct (any wrong =
fail)"` so item cards, lore screens, and bestiary panels all state the
rule explicitly.

| Item class | Subject | Entry point | Code |
|------------|---------|-------------|------|
| Armor | `geography` | `_start_armor_quiz` | `src/main.py:5597` |
| Shield | `geography` | `_start_armor_quiz` (shared) | `src/main.py:5597` |
| Accessory | `history` | `_equip_accessory` | `src/main.py:5664` |
| Scroll | `grammar` | `_read_scroll` | `src/game_magic.py` |
| Spellbook | `grammar` | `_learn_from_spellbook` | `src/game_magic.py` |
| Wand | `science` | `_invoke_wand` | `src/game_magic.py:276` |

Each call site passes:

```python
self.quiz_engine.start_quiz(
    mode='threshold',
    subject=<subject>,
    tier=item.quiz_tier,
    callback=on_complete,
    threshold=item.equip_threshold,  # or item.quiz_threshold for scrolls/wands
    wisdom=self.player.WIS,
    timer_modifier=self.player.get_quiz_timer_modifier(),
    extra_seconds=self.player.get_quiz_extra_seconds(<subject>),
    base_seconds=self.player.get_quiz_timer(<subject>),
)
```

Threshold copy sweep (post-v2.18.0): the 12 threshold strings on item
cards, lore screens, and bestiary panels all now flow through
`_threshold_line`, so every one of them ends in `(any wrong = fail)`.
Previously the kit panel said "Equip: 3 correct" and lied by omission.

### Chain-equip (legendary uniques)

When an Armor/Shield/Accessory sets `equip_chain_mode:
"escalator_chain"` or `"chain"`, `_start_armor_quiz` / `_equip_accessory`
detect it via `chain_equip.is_chain_equip` and redirect to
`_start_chain_equip_quiz` (`src/main.py:5723`). The chain reached (1–5)
drives `apply_tier_bonuses(player, item, chain)` from the item's
`tier_bonuses` dict. On chain 0 (failed rung 1) the item is not
equipped at all. Each equip is a fresh quiz — no sticky progression.

Default `equip_chain_subject`:
- Armor/Shield → `geography`
- Accessory → `history`
Override via `equip_chain_subject` in JSON.

### Cursed-gear welded

`try_unequip_slot` (`src/player.py:1138`) refuses to remove any item
whose `cursed`/`buc == "cursed"` holds OR whose `selects_wielder` is
true (Stormbringer). Returns `(False, "<msg>")` so the caller can log
"The X is welded to you!"

### Galahad purity

Equipping an item with `purity: true` cleanses all cursed items in
contact with the bearer. See `_apply_equip`, `src/player.py:1199`.

---

## 7. Scroll / Spellbook / Wand

Three sibling consumables. All three gate on the **grammar** (scrolls,
spellbooks) or **science** (wands) threshold, one question at the
item's `tier`.

### Scroll (`data/items/scroll.json`, class `Scroll` at `src/items.py:894`)

```json
{
  "scroll_of_cure_wounds": {
    "name": "scroll of cure wounds",
    "symbol": "?", "color": [180, 255, 180],
    "weight": 0.1, "min_level": 1,
    "peak_floor": 10, "spread": 6, "peak_weight": 0.25,
    "tier": 1,
    "quiz_tier": 1,
    "quiz_threshold": 1,
    "effect": "heal",
    "power": "2d4",
    "unidentified_name": "faded rose parchment",
    "lore": "..."
  }
}
```

`tier` is authoritative (v2.10.0+); `quiz_tier` is kept in sync for
legacy readers. `quiz_threshold` defaults to 1 (single grammar
question); unique artifact scrolls (Dead Sea Scroll) override to 3.
Set `single_copy: true` on quest scrolls that must survive a failed
read (secret-victory path can't brick on one bad grammar quiz). See
[magic](magic.md) for scroll effects.

### Spellbook (`data/items/spellbook.json`, class `Spellbook` at `src/items.py:935`)

```json
{
  "spellbook_fire_spark": {
    "name": "Spellbook of Fire Spark",
    "symbol": "+", "color": [255, 160, 60],
    "weight": 0.3, "min_level": 1,
    "peak_floor": 8, "spread": 8, "peak_weight": 0.3,
    "tier": 1, "quiz_tier": 1,
    "quiz_threshold": 1,
    "spell_id": "fire_spark_spell",
    "spell_name": "Fire Spark",
    "mp_cost": 3,
    "unidentified_name": "scorched slim tome",
    "lore": "..."
  }
}
```

On successful read the spell is learned permanently
(`Player.known_spells[spell_id] = mp_cost`). Unique artifact books
(Necronomicon, Sefer Yetzirah, Book of Thoth) set
`is_consumable_artifact: true` and route through
`_learn_from_spellbook`'s omniscience branch.

### Wand (`data/items/wand.json`, class `Wand` at `src/items.py:844`)

```json
{
  "wand_of_cure_minor_wounds": {
    "name": "wand of cure minor wounds",
    "symbol": "/", "color": [180, 255, 180],
    "weight": 0.3, "min_level": 1,
    "peak_floor": 10, "spread": 6, "peak_weight": 0.25,
    "charges_min": 4, "charges_max": 6, "max_charges": 6,
    "tier": 1, "quiz_tier": 1,
    "quiz_threshold": 1,
    "effect": "heal",
    "power": "2d4",
    "unidentified_name": "birch wand",
    "lore": "..."
  }
}
```

Wands have `charges` rolled at spawn from `charges_min..charges_max`,
decremented per use whether the quiz succeeds or fails
(`_invoke_wand`'s on_complete). BUC shifts charges ±1 (blessed +1,
cursed −1 with floor 1; `src/items.py:852`). A spent wand crumbles to
dust.

---

## 8. Floor-spawn: bell curve + band weights

Two drop paths coexist:

**(a) Bell curve** (`peak_floor`, `spread`, `peak_weight`). Used by
`material_spawn_weight` for templated weapons/armor/shields and by
`dungeon._item_eligible_weighted` for anything with `peak_floor` set.
Weight at floor F is `peak_weight * exp(-((F - peak_floor)² / 2σ²))`.

**(b) Band weights** (`floor_spawn_weight` / `floorSpawnWeight`, a dict
of `"<lo>-<hi>": weight`). Used by potions/scrolls/wands/accessories
and by chest templates for level bands.

Both coexist on the base `Item`:

```python
self.peak_floor:  int   = int(defn.get('peak_floor', 0) or 0)
self.spread:      int   = int(defn.get('spread', 10) or 10)
self.peak_weight: float = float(defn.get('peak_weight', 0.0) or 0.0)
self.floor_spawn_weight: dict = defn.get(
    'floor_spawn_weight', defn.get('floorSpawnWeight', {})) or {}
```

`id_tier` derivation (`derive_id_tier`, `src/items.py:48`) reads both
and takes the harder of them: a scroll's quiz_tier is its *read*
difficulty, but spawn depth overrides it so a floor-90 Scroll of
Ragnarok identifies at T5, not T1. Uniques never sit below tier 4.

### Container loot (summary; see [containers_lockpick](containers_lockpick.md))

Chests draw from a template's `loot_table` weights (per category) and
build pools of eligible items filtered by `level_cap = dungeon_level +
chest.tier * 2`. Common gear (weapon/armor/shield) is instantiated via
the template+material factories at draw time. Uniques come from the
category's `is_unique: true` entries; the per-chest draw rolls one
`rare_slot_index`.

---

## 9. Carry, encumbrance, inventory

`Player.inventory: list[Item]`. Max weight is
`CARRY_BASE (50) + STR * CARRY_PER_STR (5)` = 100 at STR 10, 175 at
STR 25. Encumbrance is intentional: item weights are deliberately
realistic (full plate ~65 lb, maul ~8 lb) and STR is the lever
(`Player.get_carry_limit`, `src/player.py:928`).

Stacking: `Item._STACKABLE_CLASSES = (Ingredient, Food, Potion, Scroll,
Ammo)`. `add_to_inventory` merges same-id items only when `buc`
*values* match (whether or not the player has identified them yet) —
previously the merge silently dropped incoming BUC on a known stack
(bug-bash A7-5, `src/player.py:1000`).

Equipment slots:
- `weapon` (melee), `ranged_weapon` (any weapon with `requires_ammo`),
  `shield`
- `armor_slots[8]` indexed by `ARMOR_SLOTS` order
- `accessory_slots[4]` (rings only)
- `amulet_slot`, `belt_slot` (singleton)

Full map via `Player.get_equipped_items()` (`src/player.py:1118`).

---

## 10. Carry bonus

An item carrying `carry_bonus: {"stat": "CON", "amount": 2}` grants its
bonus while in inventory. `Player.refresh_carry_bonuses`
(`src/player.py:1076`) diffs against `active_carry_bonuses` — idempotent,
applies on pickup, removes on drop. Formerly implemented as
`stuffies_active` / `_active_stuffies` keyed stores; those attrs are
stripped from loaded saves (`Player.__setstate__`, `src/player.py:650`).

Users today:
- **Charmander Stuffie** (`carry_bonus: {"stat": "CON", "amount": 2}`)
- **Dreamspun Sketchbook**

Any new keepsake item can opt in by adding the field to its JSON entry.

---

## 11. Enchant + BUC

**Enchant.** Integer `enchant_bonus` on weapons/armor/shields;
rendered as `+N` on the identified name. Per-slot caps (`ENCHANT_CAP`,
`src/items.py:186`):

```
head 2, body 3, arms 1, hands 1, legs 1, feet 1, cloak 2, shirt 1
shield 2, weapon 5
```

`effective_enchant_cap(player, slot)` (`src/items.py:195`) adds
Panoply of Hephaestus `divine_smithing` to the weapon cap. Random spawn
enchant for armor/shield is capped at +1 (`SPAWN_ENCHANT_CAP_ARMOR`);
scrolls can push to the per-slot cap.

**BUC.** Three-value `buc` field: `blessed` / `uncursed` / `cursed`.
- Cursed weapons/armor welded on (`try_unequip_slot`).
- Cursed status applies penalties through `Player.get_ac` (±1 per piece).
- Blessed wands get +1 charge at spawn; cursed −1.
- `buc_known` is a per-instance flag. The HUD prints `{blessed}` /
  `{cursed}` tags only when `buc_known` is true; see
  `hud_item_name` in [ui](ui.md).

Instance BUC is revealed by the one-question identify quiz; see
[identify_v3](identify_v3.md).

---

## 12. Artifact + special factories

File: `data/items/artifact.json`. Class: `Artifact`
(`src/items.py:963`) — a tag class for items that aren't weapons /
armor / etc. but still live in inventory (sealed metal discs, tablets,
palladium, scales, …).

v2.18.0 sweep: 24 spoilered artifacts got `unidentified_name` so
pickup/identify doesn't leak the true name. Examples:
- Seven Seals → `"sealed metal disc (red|green|black|rust|pale|grey|silver)"`
- Michael's Scales → `"ornate golden scales"`
- Palladium → `"ancient wooden idol"`
- Tablet of Destinies → `"obsidian tablet"`
- Philosopher's Stone → `"smooth red stone"`
- Pithos of Pandora → `"a sealed pithos"`
- Lamp of Diogenes / Aladdin's Lamp → `"a tarnished brass lamp"`

### Deep-lore factories

Hand-coded builders in `src/items.py` for secret-victory artifacts not
loaded from JSON:
- `make_abyssal_shimmer(x, y)` — terrain feature.
- `make_tablet_of_second_death(x, y)` → an `Artifact`.
- `make_scroll_lake_of_fire(x, y)` → `Scroll`, `single_copy`.
- `make_philosophers_wrench(x, y)` → `Wand`, 99 charges.
- `make_complete_tablet(x, y)` → `Artifact`, pre-identified.
- `make_death_bane_scroll(x, y)` → `Scroll`.

---

## 13. Food / Ingredient / Corpse

### Food (`data/items/food.json`, class `Food` at `src/items.py:1115`)

Ready-to-eat; no quiz. Restores `sp_restore` and optional `hp_restore`;
may grant a `bonus_type`/`bonus_stat`/`bonus_amount` or
`bonus_effect`.

```json
{
  "bread_ration": {
    "name": "bread ration",
    "symbol": "%", "color": [210, 180, 100],
    "weight": 0.5, "min_level": 1,
    "sp_restore": 45, "hp_restore": 0,
    "bonus_type": "none", "bonus_amount": 0,
    "floor_spawn_weight": {"1-30": 80, "31-60": 40, "61-100": 15},
    "unidentified_name": "bread ration",
    "lore": "..."
  }
}
```

### Ingredient (`data/items/ingredient.json`, class `Ingredient` at `src/items.py:1001`)

Raw material consumed by cooking (see [food_system](food_system.md)).
`tier_role` ∈ `{universal, family, prime, trophy, dungeon}`:
- `dungeon` = terrain-foraged (cave mushroom, swamp moss, river salt)
  — the only kind that spawns on the floor or in chests.
- `family` / `prime` / `trophy` = monster-derived, only from harvest.

```json
{
  "giant_rat_prime": {
    "name": "Giant Rat Prime Cut",
    "symbol": "~", "color": [0, 180, 50],
    "weight": 0.25, "min_level": 1,
    "source_monster": "giant_rat",
    "family": "beast",
    "tier_role": "prime",
    "stat_grant": "STR",
    "identified": true,
    "edible_safe": true,
    "raw_sp": 10
  }
}
```

`edible_safe: true` + `raw_sp: N` lets `food_system.eat_raw` return a
no-poison, data-driven SP restore (jerky-style ingredients).

### Corpse (class `Corpse` at `src/items.py:1027`)

Not loaded from JSON — made by `game_combat._make_corpse` when a
monster dies. Carries `monster_id`, `monster_name`, `harvest_tier`,
`harvest_threshold`, `ingredient_id`, `monster_def`, and an `id_tier`
derived at construction time (see [identify_v3](identify_v3.md) §5).

Harvest = **animal threshold**, 1 question at `corpse.harvest_tier`;
success produces an `Ingredient` of `corpse.ingredient_id` or picks one
from the monster's `prime_cuts` table. See [food_system](food_system.md).

### Potion (`data/items/potion.json`, class `Potion` at `src/items.py:1131`)

Drink; no quiz; identified-by-use (not identified by default).

```json
{
  "potion_of_healing": {
    "name": "potion of healing",
    "unidentified_name": "blue fizzy potion",
    "symbol": "!", "color": [80, 180, 255],
    "weight": 0.4, "min_level": 1,
    "effect": "heal", "power": "2d8+4", "duration": 0,
    "floorSpawnWeight": {"1-20": 120, "21-40": 80, "41-60": 50, "61-80": 30, "81-100": 20},
    "peak_weight": 0.5
  }
}
```

### Ammo (`data/items/ammo.json`, class `Ammo` at `src/items.py:1099`)

Stackable; always identified; consumed by ranged weapons via
`requires_ammo` match.

```json
{
  "iron_arrow": {
    "name": "iron arrow",
    "symbol": "\\", "color": [180, 180, 190],
    "weight": 0.05, "min_level": 1,
    "ammo_type": "arrow", "tier": 1, "damage_bonus": 0,
    "count_min": 10, "count_max": 30,
    "floor_spawn_weight": {"1-20": 100, "21-40": 60, "41-60": 20, "61-80": 5, "81-100": 2},
    "value": 1,
    "unidentified_name": "arrows"
  }
}
```

---

## 14. Lockpick + Container

Minimal schemas (lockpick, container). Full flow lives in
[containers_lockpick](containers_lockpick.md).

### Lockpick (`data/items/lockpick.json`, class `Lockpick` at `src/items.py:968`)

```json
{
  "lockpick": {
    "name": "lockpick",
    "symbol": "~", "color": [210, 205, 160],
    "weight": 0.2, "min_level": 1,
    "unidentified_name": "a slender pick",
    "lore": "..."
  }
}
```

Lockpick v3 reduces picks to a flavor item — the actual lockpick
mechanic is one economics question against the container
(`attempt_lockpick`). The historical `max_durability`,
`durability_loss_success` fields are kept for loader compatibility but
unused.

### Container (`data/items/container.json`, class `Container` at `src/items.py:979`)

Post-v2.18.0 cleanup trimmed decoration fields (`trap`, `trapped`,
`quiz_threshold`, `extra_item_chance`); current authoritative shape is:

```json
{
  "wooden_chest": {
    "name": "wooden chest",
    "symbol": "&", "color": [139, 90, 43],
    "weight": 20.0, "min_level": 1,
    "tier": 1, "frequency": 10,
    "gold": [5, 25]
  }
}
```

Only `tier` + `gold` range + `chest_type` (frequency / variant) are
read at runtime; everything else comes from the chest template
(`data/chest_templates.json`) stamped on at spawn by
`dungeon.pick_container()`.

---

## 15. HUD + display rules

Name resolution: `hud_context.hud_item_name(player, item,
include_count=False)` (`src/hud_context.py:84`). Three-state tree
(True Name model from identify v3):
1. **Instance identified** (`id_level >= 4`) → full name + enchant +
   BUC tag.
2. **Type known, BUC unknown** → `"unidentified <true name>"` — player
   knows what it is but doesn't know *this* copy's BUC/enchant.
3. **Type unknown** → `unidentified_name` (the fallback appearance).

Covered in detail in [identify_v3 §6](identify_v3.md) and [ui](ui.md).

---

## 16. Cross-references

- [combat](combat.md) — weapon chain-mode math, damage, unique-weapon
  mechanics dispatch.
- [magic](magic.md) — scroll effects, wand effects, spell list.
- [food_system](food_system.md) — harvest, raw eating, cooking, cook
  outcomes.
- [identify_v3](identify_v3.md) — the one-question identify flow,
  Plato bypass, backlash, HUD rules.
- [containers_lockpick](containers_lockpick.md) — chest templates,
  lockpick v3, trap table.
- [progression](progression.md) — career identifies, Philosopher's
  Mantle, quirks that touch items.
- [ui](ui.md) — `hud_item_name`, kit panel, threshold-copy sweep.
