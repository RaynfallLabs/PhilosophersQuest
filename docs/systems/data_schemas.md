# Data Schemas — JSON Conventions

**v2.18.0** (shipped 2026-10-02)

Reference for every JSON file the game loads at runtime: schema shape,
field semantics, spawn-table conventions, the identified / unidentified
discipline, and the `_meta` sub-object introduced in v2.18.

**Sources on disk:**
- `data/items/*.json` — 15 item-category files
- `data/monsters.json` — 527 monster definitions
- `data/chest_traps.json` — trap pool keyed by chest tier
- `data/hints.json` — tier-banded hint pool
- `data/flavor_encounters.json` — scripted NPC encounters
- `data/questions/*.json` — quiz question banks (12 subjects)

**Loaders:**
- `src/items.py` — item classes + loaders
- `src/monster.py` + `src/monster_classes.py` — monster loader
- `src/food_system.py` — ingredients, recipes, outcomes, prime cuts
- `src/container_system.py` — chests + trap resolution
- `src/paths.py::data_path` — read-only path resolution

---

## 1. Conventions that apply across every file

### 1.1 File shape

Most item / monster files are **top-level objects** keyed by stable
machine id, with the value being the schema:

```json
{
  "giant_rat": {
    "name": "giant rat",
    "hp": "2d6",
    ...
  },
  "goblin": { ... }
}
```

The exceptions:

- `prime_cuts.json` — top-level is `{"meta": {...}, "primes": {...}}`;
  `primes` is the usual id-keyed object
- `cook_outcomes.json` — top-level is `{"_meta": {...}, "_comments":
  {...}, "outcomes": {...}}`
- `chest_traps.json` — top-level is `{"_meta": {...}, "traps_by_tier":
  {"1":[...], "2":[...], ..., "5":[...]}}`
- `hints.json` — top-level is `{"1":[...], ..., "5":[...]}`
- `flavor_encounters.json` — top-level is a **list** (not a dict),
  each entry has its own `tag` field as id
- `accessory_appearances.json` — top-level is `{"ring": [...],
  "amulet": [...]}`, each entry is `{"name", "color"}`

### 1.2 ID discipline

- IDs are `lowercase_snake_case` ASCII only.
- IDs are stable across runs and across player saves — renaming an id
  breaks every pickled Player's `known_item_ids` / references.
- Display names (`"name"`) are human-readable; the id is the key, the
  name is the string.
- Duplicate display names are a code smell (SYSTEMS_AUDIT §10 P3 —
  `Caduceus of Hermes` is both an accessory id and a wand id; same
  for `Níðhöggr's Scale` as armor and ingredient). Add `_meta.id` or
  rename when you catch one.

### 1.3 Comments

JSON has no comment syntax. The project convention:

- **`_meta` sub-object** (v2.18): put non-mechanical metadata on an
  item or on the file itself. See §6.
- **`_comment` / `_comments` top-level keys**: file-level prose. The
  loader for `cook_outcomes.json` keeps `_comments` as a sibling of
  `outcomes` and never iterates it.
- **`_note` field on an item** (rare, 1 observed): per-item inline
  note.
- **Avoid `_comment_<id>` as outcome keys** — that was the
  v2.6.4 bug where 6 stray `"_comment_t1"` entries polluted
  `cook_outcomes.outcomes` and would AttributeError if dispatched.
  The `_comments` collection moved to a sibling.

Fields prefixed with `_` are **ignored by the stat loop** in schemas
(e.g. SECRET_BUILDS, prime cuts). Treat `_`-prefix as "this is
metadata, not a mechanical field".

### 1.4 Numbers

- Dice notation: `"2d6"`, `"3d8+10"`, `"1d100"`. Parsed by
  `src/dice.py`.
- Plain integers for counts, levels, dice-less damage.
- Floats for weights, chain multipliers, resistance fractions
  (0.0–1.0), peak weight.
- `null` is tolerated for `id_level`, `temp_power`, and other
  optional fields — but `id_level: null` on an identified-false item
  is a **data bug** (SYSTEMS_AUDIT §10 P1 flagged this for
  `Palladium`, `Tablet of Destinies`); `int(None)` raises.

### 1.5 Lists are inclusive, dicts are per-key

- `"damage_types": ["slash", "pierce"]` — all apply.
- `"resistances": ["fire", "cold"]` — all apply.
- `"damage_resistances": {"fire": 0.35, "magic": 0.4}` — fractional
  per-key reduction (not percent — multiply raw damage by `(1 -
  value)`).

### 1.6 Floor-band keys are strings

Spawn-weight bands use string keys for JSON-readability:

```json
"floorSpawnWeight": {
  "1-20":  120,
  "21-40":  80,
  "41-60":  50,
  "61-80":  30,
  "81-100": 20
}
```

Loader parses `"<low>-<high>"` into `(int, int)` and matches the
current floor. Band keys may be sparse (missing bands = weight 0).

### 1.7 The identified / unidentified_name discipline

**Rule:** every item that spawns `identified: false` MUST carry an
`unidentified_name`. If missing, the appearance renders the TRUE name
on pickup — a major spoiler.

Enforcement is partial:
- `Artifact.__init__` falls back to `defn['name']` for
  `unidentified_name` — this is the leak path.
- **SYSTEMS_AUDIT §10 P1** flagged 24 artifacts in this state:
  Philosopher's Stone, Bronze Bull Idol, Eye of the Graeae, the
  seven seals, Scales of Michael, Palladium, Tablet of Destinies,
  Gleipnir, Vidar's Sandal, Cursed Lodestone, Sealed Dispatch,
  Roots / Breaths / Spittles of the Gleipnir recipe, leather scrap.
- **Fix pattern:** add a thematic appearance name — e.g. seals →
  `"sealed metal disc"`, Tablet → `"obsidian tablet"`, Palladium →
  `"ancient wooden idol"`.
- **Audit sweep:** `grep '"identified": false' data/items/*.json`
  then confirm `"unidentified_name"` is present for each hit.

The HUD + sidebar + menu rows all honor the True-Name identify-v3
model via `hud_context.hud_item_name` — see [ui.md](ui.md) §7.1.

---

## 2. Spawn tables — peak_weight, spread, floorSpawnWeight

Two complementary spawn models coexist. Both can be set on the same
item; the loader uses whichever is non-zero.

### 2.1 Explicit floor-band weights (`floorSpawnWeight`)

Dict keyed on `"<low>-<high>"` floor bands. The loader picks the
band containing the current floor and uses the integer weight. Used
by most legacy items.

```json
"floorSpawnWeight": {
  "1-20":   0,
  "21-40":  0,
  "41-60":  0,
  "61-80":  0,
  "81-100": 2
}
```

An all-zero `floorSpawnWeight` with no Gaussian fallback = unspawnable.
**SYSTEMS_AUDIT §10 P1** found `scroll_of_nine_hells` and
`scroll_of_chromatic_doom` in this state.

### 2.2 Gaussian spawn table (`peak_weight` + `peak_floor` + `spread`)

New-style spawn curve. Weight bells around `peak_floor` with the
`spread` (floors) as sigma. Simple and tunable.

```json
"peak_weight": 0.5,
"peak_floor":  92,
"spread":      12
```

- `peak_weight: 0.0` with any `peak_floor` / `spread` is dead data —
  the Gaussian evaluates to 0. SYSTEMS_AUDIT §10 P3 flagged `ruby_rod`
  as having `peak_weight: 3.0` but all-zero bands and `peak_floor:
  92` — not unspawnable (Gaussian wins) but misleading.

### 2.3 Combined (`floorSpawnWeight` + Gaussian)

When both are set, the dungeon's `_build_spawn_pool` sums them. This
lets a weapon be rare in bands 1-80 and common at 81-100 (via bands)
AND spawn softly outside those bands (via Gaussian spread).

### 2.4 `min_level` and plot-locked items

- `min_level: 1` — spawns from floor 1.
- `min_level: 9999` — effectively unspawnable from the random pool.
  Used for quest / plot-locked items that must spawn via custom code
  (altar reward, boss drop, scripted encounter).
- A `9999` with no custom spawn method = unreachable item. See
  SYSTEMS_AUDIT §3 P1 (7 quest-spawn armors in this state).
- `min_level` is NOT the same as `peak_floor` — `min_level` is the
  earliest floor the item can appear; `peak_floor` is the center of
  the Gaussian.

### 2.5 Monster spawn tables

Same model, extra fields:

```json
"peak_floor": 7,
"spread":     9,
"peak_weight": 10.0,
"min_level":  1,
```

Monsters have NO `floorSpawnWeight` — they use Gaussian exclusively.
`frequency: 10` is a tie-breaker weight within the band pool.

### 2.6 Tier semantics (1–5 cap)

- Item `"tier"` is 1–5 by design (`src/items.py` loader).
- Monster `"treasure.item_tier"` same cap.
- `tier` drives:
  - the quiz tier for quiz-gated actions on the item (identify,
    cook, equip, scroll-read)
  - the material + enchant cap on weapons / armor
  - the AC bonus / damage band
- **SYSTEMS_AUDIT §1 P4** flagged 7 dragon-tier monsters using
  `treasure.item_tier` 6-10 (`_spawn_treasure_item` accepts
  silently); cap-break candidates.
- **Hard rule:** 1 is weakest, 5 is strongest. Never ship a tier 0 or
  tier 6+.

---

## 3. `data/items/weapon.json`

### 3.1 Field inventory (sample: `soul_reaver`)

| Field | Type | Role |
|---|---|---|
| `name` | str | display name |
| `class` | str | weapon class (`longsword`, `rapier`, `bow`, …) |
| `variant` | str | `"1h"`, `"2h"`, `"ranged"`, `"thrown"` |
| `tier` | int 1-5 | tier (quiz + loot) |
| `material` | str | material id (indexed by `data/materials/`) |
| `mathTier` | int 1-5 | quiz tier when wielded in combat |
| `baseDamage` / `base_damage` | int | base damage before mult |
| `chainMultipliers` / `chain_multipliers` | list[float] | legacy array table |
| `chain_exponent` | float | polynomial path (preferred) |
| `maxChainLength` / `max_chain_length` | int | cap for array path |
| `damageTypes` / `damage_types` | list[str] | `"slash" | "pierce" | ...` |
| `symbol` | str (1 char) | map glyph |
| `color` | `[R,G,B]` | base color |
| `weight` | float | lbs |
| `twoHanded` / `two_handed` | bool | 2H flag |
| `reach` | int | tile reach |
| `stunChance` / `stun_chance` | float 0–1 | per-hit stun |
| `bleedChance` / `bleed_chance` | float 0–1 | per-hit bleed |
| `knockback` | bool | knockback flag |
| `ignoreShield` / `ignore_shield` | bool | pierces shields |
| `requiresAmmo` / `requires_ammo` | str or null | ammo id |
| `floorSpawnWeight` | dict | band spawn |
| `containerLootTier` / `container_loot_tier` | str | `"common"`, `"rare"`, … |
| `value` | int | gold value |
| `min_level` | int | min floor |
| `unidentified_name` | str | pre-id appearance |
| `lore` | str | lore paragraph |
| `quiz_tier` | int 1-5 | quiz tier (if different from `tier`) |
| `identified` | bool | spawn-identified-by-default (false for uniques) |
| `lifestealPercent` / `lifesteal_percent` | float | lifesteal fraction |
| `template_basis` | str | the base class this unique derives from |
| `peak_floor` / `spread` / `peak_weight` | spawn | Gaussian |
| `is_unique` | bool | unique item flag |
| `max_enchant` | int | enchant cap |
| `weapon_class_chain` | str | chain mode for this class |
| `design_notes` | str | author notes (not loaded) |
| `growth_on_innocent_kill` | bool | Curtana / Soul Reaver mechanic |

### 3.2 CamelCase + snake_case duplication

Many weapon fields appear in both camelCase (`chainMultipliers`,
`maxChainLength`, `baseDamage`) AND snake_case
(`chain_multipliers`, `max_chain_length`, `base_damage`). The loader
reads the canonical snake_case name; the camelCase variants are
LEGACY / archaeological. Prefer snake_case in new entries.

### 3.3 Dead or misleading fields (SYSTEMS_AUDIT §2)

Flagged for cleanup; still shipping while cleanup is incremental:

- `equip_threshold` on weapons — no weapon-equip quiz path exists.
- `equipped_monster_aggro_radius`, `equipped_sound_radius_modifier`,
  `_karma_disappear_rolled_this_floor` — loaded but no consumers.
- `max_chain_length` on `sword_of_michael` — overridden by a
  `@property` returning `len(chain_multipliers)`.
- `neverMiss: true` on `gungnir` — no reader.
- `counterAttackChance: 0.25` on `kladenets` — no consumer.
- `design_notes` claiming AOE / spread for `boomstick` and
  `mjolnir_shard` — not wired.
- `undead_bonus: 2.5` on `anduril` — code uses hardcoded 1.5× when
  `> 1.0`, so the 2.5 is ignored (bug).

### 3.4 Materials

Material ids are **underscore_snake_case** matching the material-file
basename. SYSTEMS_AUDIT §2 P1 flagged `vulcans_brand` using
`"volcanic iron"` (with a space) — doesn't match
`volcanic_iron` material file, so `_load_material_tags` returns
nothing and the signature effect never applies. Fix: normalize all
material refs to snake_case.

21 uniques reference lore-only material strings that don't exist as
material files (`"divine iron"`, `"dark iron"`, `"legendary"`, `"bone"`,
`"wood"`, `"dad"`). Treated as material 1.0× fallthrough — harmless
unless the weapon's design implicitly expected a material multiplier.

---

## 4. `data/items/armor.json` and `shield.json`

### 4.1 Shared schema

```json
"greater_aegis_of_athena": {
  "name": "Greater Aegis of Athena",
  "symbol":    ")",
  "color":     [200, 220, 255],
  "weight":    8.0,
  "min_level": 65,
  "tier":      4,
  "material":  "adamantine",
  "ac_bonus":  5,
  "enchant_bonus": 0,
  "equip_threshold": 3,
  "quiz_tier": 4,
  "damage_resistances": {
    "fire": 0.35, "magic": 0.4, "cold": 0.2, "petrifying": 1.0
  },
  "can_be_cursed": false,
  "cursed": false,
  "identified": false,
  "unidentified_name": "a polished shield of supernatural brightness",
  "floorSpawnWeight": {"81-100": 2},
  "value": 9500,
  "lore": "...",
  "is_unique": true,
  "template_basis": "kite_shield",
  "peak_floor": 70,
  "spread": 12,
  "peak_weight": 0.4,
  "max_enchant": 2,
  "equip_chain_mode": "escalator_chain",
  "tier_bonuses": {
    "1": {"ac_bonus": 4, "resistances": {...}},
    "2": {...},
    ...
  }
}
```

Armor adds a `"slot"` field (`body`, `head`, `legs`, `arms`,
`feet`, `cloak`).

### 4.2 `equip_threshold` + `equip_chain_mode`

- `equip_threshold: N` — N correct answers in the equip quiz
  (zero-tolerance, see conventions). Subject is **geography** for
  armor / shield, **history** for accessory.
- `equip_chain_mode: "escalator_chain"` on some uniques — turns the
  threshold quiz into an escalator chain for tier-climbing (Green
  Knight's Plate, Greater Aegis, …).
- `tier_bonuses: {"1": {...}, "2": {...}, ...}` — bonuses applied
  per rank earned in the chain.

### 4.3 Unreachable quest armors (SYSTEMS_AUDIT §3 P1)

7 boss-drop quest uniques declare `_meta.spawn_method:
quest_spawn_X` + `min_level: 9999` but no code implements the
spawn method:

- `quest_spawn_nemean` (Nemean Pelt)
- `quest_spawn_green_knight` (Green Knight's Plate)
- `quest_spawn_serpent` (serpent armor)
- `quest_spawn_arachne`
- `quest_spawn_erlking`
- `quest_spawn_anansi`
- `quest_spawn_nidhoggr`

Fix: implement the methods OR delete the dead JSON entries. Both
options are open.

### 4.4 Shield-specific

Shields share the armor schema minus `slot` (always `shield`).
`bronze_aegis` is the one documented pre-form plot-locked shield with
a `_meta.spawn_method: "quest_spawn_aegis_pre"` and `min_level: 9999`.

---

## 5. `data/items/accessory.json`

Keyed by id (`elaras_silver_ring`, `ring_magic_res_a`, etc.). Each
entry carries:

| Field | Role |
|---|---|
| `name` | display |
| `slot` | `"ring"` / `"amulet"` / `"belt"` |
| `equip_threshold` | history-quiz threshold (zero-tolerance) |
| `quiz_tier` | tier for the equip quiz |
| `effects` | dict of effects, see §5.1 |
| `unidentified_name` | required when identified-false |
| `use_charged` + `charges` | charged accessory (Lyre, Hand of Glory) |
| `save_bonus` | `{cat: "CON"/"WIS"/"DEX"/"all", amount: N}` |
| `set_id` + `set_name` | set membership banner |

### 5.1 `effects` dict

```json
"effects": {
  "stat":     "INT",     "amount":  2,
  "stat2":    "WIS",     "amount2": 1,
  "status":   "see_invisible"
}
```

- `stat` + `amount` grant a flat stat bonus.
- `stat2` + `amount2` grant a second one.
- `status` grants a permanent (while-equipped) effect from
  `status_effects.BUFFS`.

### 5.2 Cosmetic appearance pool

`accessory_appearances.json` is a `{"ring": [...], "amulet": [...]}`
dict with `[{"name": "...", "color": [R,G,B]}, ...]`. The
one-cosmetic-per-item system (`main.Game._appearance_map`) picks a
look from this pool per **ring type** and locks it for the run — so
every "ring of fire resistance" the player picks up looks the same.

---

## 6. `data/items/artifact.json`

Keyed by id. Artifacts are plot-locked, hand-authored items (Stone,
Gleipnir, the seven seals, Tablet, Palladium, …). Schema is
intentionally sparse — most mechanics live in `special_properties`.

**v2.18 example (`philosophers_stone`):**

```json
{
  "name": "Philosopher's Stone",
  "symbol": "*",
  "color":  [255, 215, 0],
  "weight": 1.0,
  "min_level": 0,
  "lore":   "...",
  "special_properties": {
    "plot_role": "abaddon_drop_endgame_anchor",
    "effects": ["auto_identify",
                "death_kill_ritual_component",
                "score_bonus_50000"],
    "spawn_method": "boss_drop_abaddon"
  },
  "is_unique": true,
  "identified": false,
  "id_level": 0,
  "unidentified_name": "smooth red stone",
  "_meta": {
    "plot_locked": true
  }
}
```

### 6.1 `special_properties` block

Free-form bag. Readers:

- `plot_role` — documentary; grep-only.
- `effects: [...]` — list of effect-id strings the artifact grants.
  Hard-coded dispatch in `game_magic` / `game_divine`.
- `spawn_method` — documentary **when inside `special_properties`**;
  real spawn gating is `min_level: 9999` + custom code (e.g.
  `_spawn_abaddon_drop`). See §9 on `_meta.spawn_method` for the new
  canonical location.

### 6.2 `_meta.plot_locked`

**v2.18 convention:** boolean flag inside the per-item `_meta`
sub-object. Documentary — no runtime consumer. SYSTEMS_AUDIT §3 P3
notes that `plot_locked` is never referenced in `src/`; real gating
is `min_level: 9999` + the game's custom spawn path.

### 6.3 `id_level: null` is a bug

`int(defn.get("id_level", 5 if identified else 0))` chokes on `null`.
SYSTEMS_AUDIT §10 P1 flagged `Palladium` and `Tablet of Destinies`.
Fix: set to `0` (unidentified) or `5` (identified).

---

## 7. `data/items/scroll.json`, `wand.json`, `spellbook.json`

### 7.1 Scroll schema

```json
"scroll_of_cure_wounds": {
  "name": "scroll of cure wounds",
  "symbol": "?",
  "color":  [180, 255, 180],
  "weight_lb": 0.1,
  "min_level": 1,
  "peak_floor": 10,
  "spread": 6,
  "tier": 1,
  "quiz_tier": 1,
  "quiz_threshold": 1,
  "effect": "heal",
  "power": "2d4",
  "unidentified_name": "faded rose parchment",
  "lore": "...",
  "weight": 0.1,
  "peak_weight": 0.25
}
```

- `quiz_threshold` — grammar-quiz threshold to read (zero-tolerance).
- `effect` — effect id (e.g. `"heal"`, `"identify"`, `"magic_mapping"`).
- `power` — dice string, scalar, or power argument interpreted per
  effect.

### 7.2 Wand schema

Adds `charges_min` / `charges_max` / `max_charges`. Science-quiz
threshold.

```json
"charges_min": 4,
"charges_max": 6,
"max_charges": 6,
"effect": "heal",
"power":  "2d4"
```

### 7.3 Spellbook schema

Adds `spell_id` / `spell_name` / `mp_cost`. Grammar-quiz threshold.

```json
"spell_id":  "fire_spark_spell",
"spell_name": "Fire Spark",
"mp_cost": 3
```

### 7.4 `single_copy` flag (v2.18 reward audit)

Dad-reward and quest scrolls carry `"single_copy": true` + `threshold:
1` so the player keeps a single reliable copy of a plot-flagged
scroll. See ITEM_QUIZ_AUDIT.md for the 25 scrolls affected.

---

## 8. `data/items/potion.json`

```json
"potion_of_healing": {
  "name": "potion of healing",
  "unidentified_name": "blue fizzy potion",
  "symbol": "!",
  "color":  [80, 180, 255],
  "weight": 0.4,
  "min_level": 1,
  "effect":  "heal",
  "power":   "2d8+4",
  "duration": 0,
  "floorSpawnWeight": {"1-20": 120, "21-40": 80, ...},
  "lore": "...",
  "peak_weight": 0.5
}
```

- `effect` — `"heal"`, `"cure_poison"`, `"gain_level"`, …
- `power` — dice string for roll-magnitude effects; a sentinel int
  for `gain_level` (number of levels gained); unused for binary
  effects (`cure_*`).
- `duration` — turns for timed effects (0 for instant).

---

## 9. `_meta` sub-object — introduced in v2.18

**Motivation:** several documentary-only fields (`spawn_method`,
`plot_locked`) were scattered at item level. They had zero runtime
consumers but polluted the "live mechanical fields" view. v2.18
collects them under a per-item `_meta` sub-object.

### 9.1 Canonical shape

```json
"_meta": {
  "spawn_method": "quest_spawn_aegis_pre",
  "plot_locked":  true
}
```

### 9.2 Current `_meta` sites (as of 2026-10-02)

| File | Item | Content |
|---|---|---|
| `data/items/armor.json` | `trainers_cap` | `{"spawn_method": "easter_egg"}` |
| `data/items/artifact.json` | `philosophers_stone` | `{"plot_locked": true}` |
| `data/items/shield.json` | `bronze_aegis` | `{"spawn_method": "quest_spawn_aegis_pre"}` |
| `data/chest_traps.json` (top-level) | file | `{"version": "v2.6.6", "description": "..."}` |
| `data/items/cook_outcomes.json` (top-level) | file | `{"version": "v2.6.4-draft", "description": "...", "buff_semantics": "...", "tier_bands": "..."}` |

Count: 21 `_meta` occurrences across data files (as of v2.18;
includes top-level and per-item).

### 9.3 Rule for adding `_meta`

- Only add documentary metadata (version, author note, spawn method
  name, plot flag). No runtime consumer should read from `_meta`.
- Per-item `_meta` goes inside the item's object.
- File-level `_meta` goes as a top-level sibling (same level as
  `outcomes` / `traps_by_tier`).
- Readers that iterate the file must skip `_meta` keys. The
  `cook_outcomes.json` loader skips `_meta` and `_comments`
  explicitly.

### 9.4 Migrating existing fields

If a dead field currently sits at item-level (`spawn_method`,
`plot_locked`, `_note`), moving it to `_meta` is a mechanical no-op.
The current migration is **gradual** — SYSTEMS_AUDIT §10 P4 lists
`spawn_method` + `plot_locked` as the two to sweep next (29
`spawn_method` + 28 `plot_locked` references file-wide).

---

## 10. `data/monsters.json`

### 10.1 Field inventory (`giant_rat`)

| Field | Type | Role |
|---|---|---|
| `name` | str | display |
| `symbol` | str | map glyph |
| `color` | `[R,G,B]` | base color |
| `hp` | dice str | HP roll |
| `speed` | int | ticks per move |
| `ai_pattern` | str | AI dispatch (`aggressive`, `coward`, …) |
| `thac0` | int | AD&D-style to-hit |
| `peak_floor` | int | Gaussian center |
| `spread` | int | Gaussian sigma |
| `peak_weight` | float | Gaussian peak |
| `min_level` | int | min floor |
| `attacks` | list[dict] | see §10.2 |
| `resistances` | list[str] | damage type names |
| `weaknesses` | list[str] | damage type names |
| `tags` | list[str] | `["beast", "undead", …]` for family lookup |
| `harvest_tier` | int 1-5 | tier for animal-quiz harvest |
| `treasure` | dict | gold + item drop |
| `lore` | str | bestiary lore |
| `frequency` | int | tie-breaker weight in band pool |
| `pack` | bool | spawns in packs |
| `is_boss` | bool | boss-immunity + bones flag |
| `is_mini_boss` | bool | mini-boss planning |

### 10.2 `attacks` list

```json
"attacks": [
  {
    "name":   "bite",
    "damage": "1d2",
    "type":   "physical",
    "effect": "poisoned",
    "effect_chance": 0.5
  }
]
```

- `type` — damage type (`physical`, `fire`, `cold`, `magic`, `psychic`,
  …).
- `effect` — status-effect id (optional).
- `effect_chance` — 0-1 roll (optional, default 1.0).

### 10.3 Dead fields on monsters (SYSTEMS_AUDIT §1)

- `harvest_threshold` on all 527 — threaded to `Corpse` but harvest
  v4 uses `threshold=1` unconditionally.
- `ingredient_id` on 525 — overridden by `prime_cuts.json` keyed by
  the monster's id (see §11.3).
- `attack_effects` on 3 monsters (baba_yaga, ravanas_arm, anansi) —
  no reader.
- `mortal_weapon_floor` (celestial_guardian) — no reader.
- `chain_break_on_hit: 0.35` on `abaddon_destroyer` — dead-wired flag
  only.

### 10.4 Boss / mini-boss discipline

- `is_boss: true` — boss-immunity to charm / paralyze / confuse /
  sleep AND bones recognition.
- `is_mini_boss: true` — mini-boss planner picks this up.
- **Both true** — flagged as conflict (SYSTEMS_AUDIT §1 P4):
  `blood_archon`, `seal_demon_wrath` through `seal_demon_silence`.
- `spawn_chance` is required for `is_mini_boss` entries — the planner
  filters `spawn_chance <= 0`. Missing it = unspawnable
  (`asmodeus`, `surtur`, `ymir_last_spawn`, `hrungnirs_ghost`).

### 10.5 Mojibake / Unicode risk

**SYSTEMS_AUDIT §10 P1:** `N��h�ggr's Scale` and related lore have
corrupted Unicode (U+FFFD replacement chars where `ð` should be).
`data/monsters.json`, `data/items/armor.json`,
`data/items/ingredient.json`. The project convention is **UTF-8 with
proper code points**, not escaped `ð` or mojibake. Fix: edit the
file in a UTF-8-aware editor; verify with
`python -c "import json; json.load(open(f, encoding='utf-8'))"`.

---

## 11. `data/items/ingredient.json` + `prime_cuts.json` + `recipes.json` + `cook_outcomes.json`

Four files that compose the food system; interrelated.

### 11.1 `ingredient.json` — per-ingredient schema

```json
"giant_rat_prime": {
  "name": "Giant Rat Prime Cut",
  "symbol": "~",
  "color":  [0, 180, 50],
  "weight": 0.25,
  "min_level": 1,
  "source_monster": "giant_rat",
  "family":        "beast",
  "tier_role":     "prime",
  "temp_power":    "night_vision",
  "temp_duration": 150,
  "temp_desc": "predator senses; sight radius +4 in dark",
  "stat_grant": "STR",
  "description": "Prime cut from giant rat.",
  "identified":  true,
  "edible_safe": true,
  "raw_sp": 10
}
```

- `tier_role` — `"prime"` (standard) or `"trophy"` (boss-tier).
- `temp_power` — status-effect id when eaten raw (not through a
  recipe).
- `raw_sp` — SP restored eating raw (10-30 range).
- `edible_safe` — if false, raw-eat triggers a penalty (currently
  always true in the shipped data).

### 11.2 `prime_cuts.json` — monster → ingredient key

```json
{
  "meta": { "design_version": "2026-05-31r2", "total_primes": 527, ... },
  "primes": {
    "giant_rat": {
      "monster_id":     "giant_rat",
      "monster_name":   "giant rat",
      "family":         "beast",
      "is_trophy":      false,
      "ingredient_id":  "giant_rat_prime",
      "ingredient_name": "Giant Rat Prime Cut"
    },
    "asterion_minotaur": {
      "monster_id":   "asterion_minotaur",
      ...
      "is_trophy":    true,
      "ingredient_id": "asterion_minotaur_trophy",
      ...
    }
  }
}
```

**The canonical mapping.** The old `monster.ingredient_id` field is
dead. Harvest v4 and the bestiary dossier both route through
`prime_cuts.json` keyed by the monster's id (kind).

### 11.3 `recipes.json`

```json
"u_mushroom_tea": {
  "name": "Mushroom Tea",
  "ingredients": ["cave_mushroom"],
  "outcome_id":  "t1_snack_perception",
  "flavor": "..."
}
```

- `ingredients` — list of ingredient ids. Repeated ids are allowed
  (`["x", "x", "x"]` means "3 of x"). Cook menu collapses to "x3".
- `outcome_id` — key into `cook_outcomes.outcomes`.
- `name` — display dish name.
- `flavor` — one-line prose shown on success.
- `recipe_class: "trophy"` — flags trophy recipes (gold-colored
  entry).
- `stat_grant` / `stat_grant_default` — see §11.4.

614 recipes shipped; all have valid `outcome_id`. Zero orphans
(SYSTEMS_AUDIT §5 VERIFIED).

### 11.4 `cook_outcomes.json`

```json
{
  "_meta": {
    "version": "v2.6.4-draft",
    "description": "...",
    "buff_semantics": "temp_power = status_effects.BUFFS name; ...",
    "tier_bands":    "T1: SP 30-50, ...; T2: SP 50-75, ...; ..."
  },
  "_comments": { ... },
  "outcomes": {
    "t1_snack_perception": {
      "tier": 1,
      "sp":   55,
      "hp":   2,
      "temp_power": null,
      "desc": "A quick bite; hunger eased."
    },
    "trophy_asterion": {
      "tier": 5,
      "sp":   150,
      "hp":   22,
      "max_hp_bonus":  3,
      "stat_grant":    1,
      "stat_grant_default": "STR",
      "temp_power":    "save_guard_WIS",
      "temp_amount":   3,
      "temp_duration": 200,
      "permanent_power": "plus_2_str_confuse_immune",
      "permanent_desc":  "The Minotaur's cunning is yours; ...",
      "desc": "Crown of the Labyrinth..."
    },
    ...
  }
}
```

- `tier` — outcome tier (= quiz tier for cooking).
- `sp` / `hp` — SP / HP restored.
- `max_hp_bonus` — permanent max-HP bump.
- `stat_grant` — permanent +N to `stat_grant_default`.
- `temp_power` — status-effect id from `status_effects.BUFFS`.
- `temp_duration` / `temp_amount` — effect params.
- `permanent_power` — key into `food_system._apply_permanent_power`
  dispatch.
- `desc` — one-line flavor.

**120 outcomes shipped.**

**Dead comment keys (SYSTEMS_AUDIT §5 P3):** before v2.18, the
`outcomes` dict carried 6 `_comment_*` entries that a stray dispatch
could AttributeError on. The `_comments` collection moved to a
sibling under the top-level `_meta`. If you add a prose note, put it
in the top-level `_comments`, not inside `outcomes`.

**Non-canonical `temp_power` names:** `trophy_medusa` ships
`"petrify_resist"` which isn't in `status_effects.BUFFS` /
`DEBUFFS` — it works via the legacy `_TEMP_POWER_REMAP` alias
(`petrify_resist → save_guard_CON`). Prefer canonical status-effect
ids in new outcomes.

### 11.5 `food.json` — pre-cooked foods

```json
"bread_ration": {
  "name": "bread ration",
  "sp_restore":    45,
  "hp_restore":    0,
  "bonus_type":    "none",
  "bonus_amount":  0,
  "floor_spawn_weight": {"1-30": 80, "31-60": 40, "61-100": 15}
}
```

Note the **snake_case** `floor_spawn_weight` — different from the
item files' `floorSpawnWeight`. Both loaders accept their file's
convention; the inconsistency is historical.

---

## 12. `data/items/container.json` + `lockpick.json`

### 12.1 `container.json`

```json
"wooden_chest": {
  "name": "wooden chest",
  "symbol": "&",
  "color":  [139, 90, 43],
  "weight": 20.0,
  "min_level": 1,
  "tier":   1,
  "frequency": 10,
  "gold":   [5, 25]
}
```

- `tier` — chest tier (also the trap tier on failed pick).
- `frequency` — spawn weight within the chest pool for the band.
- `gold: [min, max]` — gold roll on open.

**Dead fields (SYSTEMS_AUDIT §5 P3):**
- `trapped` + `trap: {...}` block — every "trapped" chest carries a
  full `trap:{...}` sub-object, but the real trap comes from
  `chest_traps.json` keyed by chest tier (v2.6.6 fix). The sub-object
  is a stale decoration.
- `extra_item_chance` — no reader.
- `quiz_threshold` — recently patched to 1 but the loader doesn't
  read it; lockpick v3 uses hard-coded `threshold=1`.

### 12.2 `lockpick.json`

```json
"lockpick":        { ...standard item fields... },
"master_lockpick": { ...same shape, min_level: 3... }
```

Two entries ship: the basic lockpick and the master lockpick. The
master pick (`"master_lockpick"`) is the permanent handle granted at
game start (`main._new_game` grants `picks[0]`, which is the basic
lockpick — SYSTEMS_AUDIT §5 P1 flagged this as a naming/reality
mismatch; comment says "Master Lockpick" but code grants basic).

**Dead lockpick entries:** 4 types (`mithril_lockpick`,
`diamond_lockpick`, `philosophers_pick`, the basic `lockpick` if you
count the name-mismatch) with no spawn path. Fix: delete from JSON
OR add spawn gating.

**Dead lockpick fields (SYSTEMS_AUDIT §5 P3):**
`max_durability`, `durability`, `durability_loss_success`,
`durability_loss_failure` — the durability system was removed; fields
retained for migration safety.

---

## 13. `data/chest_traps.json`

```json
{
  "_meta": {
    "version": "v2.6.6",
    "description": "Trap pool for lockpick failures (2026-09-03). Every failed chest pick fires a random trap from the chest's OWN tier (not the floor tier -- that was a bug pre-v2.6.6). ..."
  },
  "traps_by_tier": {
    "1": [
      {
        "type":            "needle",
        "damage":          "1d4",
        "effect":          "poisoned",
        "effect_duration": 5,
        "message":         "A poisoned needle springs from the lock!"
      },
      ... (4-5 variants per tier)
    ],
    "2": [...],
    "3": [...],
    "4": [...],
    "5": [...]
  }
}
```

- `type` — trap kind (`"needle"`, `"spring"`, `"glyph"`, …). Used by
  Job's Endurance quirk unlock (needs 5 distinct types).
- `damage` — dice string.
- `effect` — canonical `status_effects` debuff id.
- `effect_duration` — turns.
- `message` — one-line log on trigger.

### 13.1 v2.6.6 fix note

Pre-v2.6.6, lockpick trap tier was tied to the floor (so a T1 chest
on floor 90 fired a T5 trap). Fixed to chest-tier-based. The
`_meta.description` carries this history.

### 13.2 Job's Endurance consumer

The Job's Endurance quirk unlocks when the player has survived 5
**distinct** trap types. SYSTEMS_AUDIT §5 P1 flagged a bug: the
`on_complete` callback passes a static `'chest_fail'` type string, so
only one entry is ever registered. Fix: pass the real `type` from
`chest_traps.json`.

---

## 14. `data/hints.json`

```json
{
  "1": ["Stats: Strength carries weight ...", "Wisdom is patience, ...", ...],
  "2": [...],
  "3": [...],
  "4": [...],
  "5": [...]
}
```

Top-level dict keyed by tier (1-5). Each value is a flat list of hint
strings. The Recall Lore mechanic picks a hint matching the player's
current tier floor; the Encyclopedia Lore Hints tab lists already-
recalled hints.

---

## 15. `data/flavor_encounters.json`

**List, not dict.** 92 entries. Each entry:

```json
{
  "tag":  "flv_lost_merchant",
  "name": "Lost Merchant",
  "symbol": "@",
  "color":  [200, 170, 100],
  "min_level": 1,
  "max_level": 12,
  "text": "...",
  "options": [
    {
      "label":   "Buy a potion from him (30g)",
      "cost":    {"type": "gold", "amount": 30},
      "reward":  {"type": "random_item", "category": "potion"},
      "outcome": "..."
    },
    ...
  ]
}
```

- `tag` is the id. `name` is display.
- `min_level` / `max_level` gate spawning.
- `options` is the branching dialog — see `game_encounters` for the
  cost / reward dispatch and the full type inventory.

---

## 16. `data/questions/<subject>.json`

Each subject bank is its own file (`math.json`, `grammar.json`,
`history.json`, …). Schema (per-question):

```json
{
  "subject": "math",
  "tier":    1,
  "question": "What is 2 + 2?",
  "choices":  ["3", "4", "5", "6"],
  "answer":   "4"
}
```

Banks are flat lists. Loader shuffles per-run and tracks deck
position in `quiz_deck_state` on save. See
[quiz_engine.md](quiz_engine.md) for the deck + anti-repeat design.

**Compile-time checks:**
- `bankbuild/` tooling runs deterministic gates (choice-count 4,
  answer-in-choices, char budget per subject, lowercase answers for
  grammar, …).
- Pre-ship: moral vision audit + tone audit + adversarial judge.
  See `bankbuild/PIPELINE.md`.
- Per-subject rules + voice are in `docs/quiz/subjects/<X>.md` and
  the memory bullets.

---

## 17. Invariants (what not to break)

1. **UTF-8 on disk.** Everything is UTF-8. Scripted via
   `encoding='utf-8'` on every `open(...)` in the loader. Mojibake is
   a bug (SYSTEMS_AUDIT §10 P1 — Níðhöggr strings).
2. **`identified: false` → `unidentified_name` required.** Else
   TRUE name leaks on pickup.
3. **`min_level: 9999` + no custom spawn code = unreachable item.**
   Document the spawn method or delete the entry.
4. **Boss / mini-boss consistency.** `is_boss` and `is_mini_boss`
   should be mutually exclusive. `is_mini_boss` without
   `spawn_chance` = unspawnable.
5. **Tier 1-5 cap.** Never ship `tier: 0`, `tier: 6`, or
   `treasure.item_tier: 6+`.
6. **Spawn tables sum.** `floorSpawnWeight` + Gaussian both apply; a
   non-zero floor-band weight always wins over `peak_weight: 0`.
7. **`_meta` is documentary.** No runtime consumer; loaders skip it.
8. **`_comment` / `_comments` / `_note` are documentary.** Loaders
   skip underscore-prefix keys at outcome / entry level.
9. **`id` keys are stable.** Renaming an id breaks every saved
   `known_item_ids` reference.
10. **Material refs are snake_case.** `volcanic_iron`, not
    `"volcanic iron"`.
11. **`outcome_id` must resolve.** Every recipe's `outcome_id` must
    be a key in `cook_outcomes.outcomes`. 614/614 verified.
12. **`spawn_method` / `plot_locked` go in `_meta`.** New entries use
    the sub-object; the gradual sweep moves old entries.
13. **No `_comment_*` keys inside `outcomes` / `primes` /
    `traps_by_tier` / `effects`.** Prose siblings only.

---

## 18. Audit path (verifying a data file)

A quick repeatable loop before shipping a data edit:

```sh
# 1. Encoding + parse
python -c "import json; json.load(open('data/items/<file>.json', encoding='utf-8'))"

# 2. unidentified_name discipline
rg '"identified": false' data/items/<file>.json
# every hit must have a nearby "unidentified_name"

# 3. Spawn-table sanity
rg '"peak_weight":\s*0' data/items/<file>.json
# combined with a non-zero floor band, OK; else unspawnable

# 4. Tier cap
rg '"tier":\s*[6-9]' data/items/<file>.json
# any hit is a bug (except quest/boss items by explicit design)

# 5. Materials
rg '"material":\s*"[^"]*\s' data/items/<file>.json
# any hit (space in material string) is the vulcans_brand pattern
```

Run `pytest tests/` for data-layer tests before merging.
