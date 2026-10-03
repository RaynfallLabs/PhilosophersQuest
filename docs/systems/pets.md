# Pets

**Scope.** Companion creatures that follow the player, fight alongside them, and (for most species) level up and evolve. The entire system is in `src/pet_system.py` — species dictionary, Pet base class, four subclassed one-off pets, and the `random_species()` picker. Call sites that spawn or transform pets live in `src/game_combat.py` (Soul Sphere throw, Dad Sphere, summon-at-adjacent), `src/main.py` (`_duck_of_doom_transform`), `src/hero_specials.py` (Leonardo's Codex Sketch), `src/game_encounters.py` (Unicorn), and `src/game_menus.py` (Shift+P pet menu — feed, heal, pet-interaction, recall, command cycle, specials).

Out of scope here: pet damage resolution inside combat (see [combat](combat.md)), quirks that change pet behavior (see [progression](progression.md)), and the specific items that spawn or heal pets (Soul Sphere, pet-food, healing potions on pets — see [items](items.md)).

**File map.**
```
src/pet_system.py       # Species, Pet, FenrirPet, SketchedPet, DadPet, UnicornPet, random_species
src/game_combat.py      # Soul Sphere throw hatch, Dad Sphere, bound-sphere resummon, _dig_pit
src/game_menus.py       # Shift+P pet menu + sub-menus (feed/heal/pet/recall/command/specials)
src/game_encounters.py  # UnicornPet spawn via unicorn-encounter chain
src/hero_specials.py    # SketchedPet via Leonardo's Codex (summon_sketch_helper)
src/main.py             # _duck_of_doom_tick + _duck_of_doom_transform, FenrirPet via XYZZY T5
```

---

## 1. Species schema

Normal pet species live in the module-level `_SPECIES` dict, keyed by species_key. Each entry carries:

| Field         | Type                 | Meaning                                                               |
|---------------|----------------------|------------------------------------------------------------------------|
| `element`     | str                  | Thematic element (electric, water, plant, fire, psychic)              |
| `damage_type` | str                  | Damage type dealt by base attacks (`shock`, `cold`, `poison`, `fire`, `psychic`) |
| `color`       | tuple[int, int, int] | RGB color used for the renderer glyph                                 |
| `stages`      | list[dict]           | 3 stages: `{name, symbol, msg}`. Stage 0 is base; stages 1/2 unlock at `_EVOLVE_1`/`_EVOLVE_2`. |
| `specials`    | list[dict]           | Per-species special attacks (see §2)                                  |

The four elemental species (`electric`, `water`, `plant`, `fire`) are the standard pool. `duck_of_doom` is a fifth species, hatched exclusively from the Duck-of-Doom quirk (§5). The symbol field uses lowercase for stage 0, uppercase for stages 1/2.

### 1.1 Standard species pool

| species_key | Stage 0 → 1 → 2                                     | Element   | Damage type |
|-------------|-----------------------------------------------------|-----------|-------------|
| electric    | Zappik → Voltpaw → Thundertail                      | electric  | shock       |
| water       | Shellkit → Tideshell → Torrentoise                  | water     | cold        |
| plant       | Seedling → Thornback → Bloomsaur                    | plant     | poison      |
| fire        | Emberpup → Flamescale → Infernodrake                | fire      | fire        |
| duck_of_doom | Waddlekind → Drake of the Covenant → Seraphimallard | psychic   | psychic     |

### 1.2 Random pool
`pet_system.random_species()` returns a random key with equal probability from `_SPECIES`, **excluding `duck_of_doom`** (v2.18). Waddlekind is the endpoint of the 2026-turn Duck-of-Doom quirk, not a Soul Sphere / Summon Guardian / Gate outcome; the exclusion closes a leak where throwing a Soul Sphere could pop a free Waddlekind without the quirk commitment. Call sites that need a random species import this helper as `random_pet_species`.

### 1.3 Evolution thresholds
```python
_EVOLVE_1 = 25
_EVOLVE_2 = 55
_XP_PER_LEVEL = 20   # xp_to_next = level * _XP_PER_LEVEL
```

Totals: ~6,000 XP to L25, ~30,000 XP to L55. Combined with passive XP (one grain every 3 pet turns) + per-kill XP scaling with monster `max_hp` + late-pickup bonus, stage 1 lands around 20-25 pet-floors, stage 2 only in deep late-game play. The L100 cap is terminal — further XP is silently dropped.

---

## 2. Specials schema

Each entry in `_SPECIES[species_key]['specials']` is one activated attack:

| Field              | Type   | Meaning                                                               |
|--------------------|--------|------------------------------------------------------------------------|
| `id`               | str    | Unique id used in cooldown table + menu                              |
| `name`             | str    | Display name                                                           |
| `unlock_stage`     | int    | 0, 1, or 2. Available iff `pet.stage >= unlock_stage`                 |
| `damage_mult`      | float  | Multiplier on `pet.base_damage` (scaled by quiz accuracy)             |
| `damage_type`      | str    | shock / cold / poison / fire / psychic / holy                         |
| `targeting`        | str    | `single`, `aoe`, `cone`, `line`, `self`, `visible_all`                 |
| `range`            | int    | Tiles. 0 = pet-centered for `aoe`/`self`                              |
| `aoe_radius`       | int    | Tiles (for `aoe` + `cone`)                                            |
| `status`           | str    | Status effect applied on hit (`paralyzed`, `slowed`, `immobilized`, `poisoned`, `burning`, `confused`, `feared`, `bleeding`) |
| `status_chance`    | float  | 0.0-1.0                                                                |
| `status_duration`  | int    | Turns                                                                  |
| `knockback`        | int    | Tiles (water specials)                                                |
| `cooldown`         | int    | Turns before this id is usable again                                  |
| `effect`           | str    | Non-damage effect id (`player_telepathy` for duck Stage 0)            |
| `effect_duration`  | int    | Turns, for `effect`-driven specials                                   |
| `flavor_message`   | str    | Printed on activation (duck Stage 2 Sometimes Goose)                  |
| `desc`             | str    | One-line description shown in the pet-specials sub-menu               |

The player triggers specials from the pet menu (Shift+P → specials). The `Pet.available_specials()` filter is `unlock_stage <= self.stage`; `can_use_special(id)` additionally requires the id's cooldown to be 0. Cooldowns are stored in `pet._special_cooldowns: dict[str, int]` and tick every pet turn via `Pet.tick_cooldown()`.

### 2.1 Special inventory (standard species)

| Species    | Stage 1 (unlock L25)                               | Stage 2 (unlock L55)                                      |
|------------|----------------------------------------------------|-----------------------------------------------------------|
| electric   | **Spark Bolt** — single, range 5, 1.5× shock, 50% paralyze 2t (cd 250) | **Thunder Strike** — AoE 3×3 at range 4, 2.0× shock, 40% paralyze 1t (cd 400) |
| water      | **Water Jet** — single, range 4, 1.5× cold, kb1, 60% slow 3t (cd 250) | **Tidal Crash** — line 4, 1.8× cold, kb1, 50% slow 4t (cd 400) |
| plant      | **Vine Lash** — single, range 3, 1.5× poison, 70% root 2t (cd 250) | **Bloomburst** — pet-centered AoE r2, 0.4×, 100% poison 5t (cd 400) |
| fire       | **Flame Breath** — cone r3, 1.5× fire, 50% burn 3t (cd 250) | **Inferno Pillar** — AoE 3×3 at range 5, 2.5× fire, 75% burn 4t (cd 400) |

### 2.2 Duck of Doom specials (unique shape)

Unique among species: Waddlekind has a **Stage 0** special, because the player already paid 2026 cursed-turns to be here.

| Stage | Special                                             |
|-------|-----------------------------------------------------|
| 0     | **Detect Monsters** — `targeting='self'`, applies `player_telepathy` 30t (reveal every monster on the floor). cd 200. |
| 1     | **Psionic Blast** — single, range 6, 1.8× psychic, 50% confuse 3t. cd 300. |
| 2     | **Sometimes Goose** — `targeting='visible_all'`, hits every alive monster in the player's FOV, 1.2× psychic, 40% fear 4t. cd 600. Flavor line: "Reality folds. A goose the size of a cathedral hisses from a dimensional rift — every enemy in sight reels." |

**Audit note.** `psychic` is not in the standard resistance table, so Duck of Doom damage is effectively untyped — nothing resists or amplifies it. This is a deliberate choice; Waddlekind is a reward pet and should feel strange.

---

## 3. The Pet base class

```python
class Pet:
    def __init__(self, species_key: str, x: int = 0, y: int = 0):
```

### 3.1 Stats
```python
def _calc_max_hp(self):  return 20 + int(self.level * 1.8)   #   20 → ~200
def _calc_damage(self):  return  3 + int(self.level * 0.27)  #    3 → ~30
```

`_refresh_stats()` is called on every level up: `max_hp` recomputed, HP healed by the delta.

Attack damage with quiz-accuracy scaling:
```python
def get_attack_damage(self, quiz_accuracy=0.5):
    mult = 0.5 + min(0.7, quiz_accuracy * 0.7)   # 0.5× (whiff) to 1.2× (perfect)
    return max(1, int(self.base_damage * mult))
```

### 3.2 XP sources

| Source               | Method                              | Amount                                   |
|----------------------|-------------------------------------|------------------------------------------|
| Monster kill         | `gain_xp_from_kill(monster_max_hp)` | `3 + max_hp // 10` (4 for a 10-HP F1 mob, 23 for a 200-HP F90 mob) |
| Passive              | `gain_xp_passive()`                 | 1 XP every 3rd call                      |
| Pet-interaction      | menu action, `gain_xp(5)`           | +5 XP once per floor                     |
| Feed food            | menu action                         | half of food's `sp_restore`, clamped 20-80 |
| Late-pickup bonus    | `apply_late_pickup_bonus(floor)`    | `min(floor * 50, 4000)`                  |

`apply_late_pickup_bonus(floor)` is the one-time XP grant that keeps a pet hatched deep in the dungeon from being combat-useless at L1. The 4000-XP cap sits just below stage 1 evolution (6000 XP to L25) so a late pet still earns its first big milestone but doesn't need 20 floors of catch-up to be useful.

**Call sites that CALL `apply_late_pickup_bonus`:**
- `game_combat.py` Soul Sphere throw (`_sphere_throw` path) — the primary case.
- `main.py::_duck_of_doom_transform` — the Waddlekind hatch (v2.18 wiring; before this the hatched duck was L1 regardless of floor).

**Call sites that DO NOT call it (open ticket in the audit):**
- Hero-special summon paths (`_eff_summon_sketch_helper`, Summon Guardian pending).
- Spell-summon paths that spawn via `game_combat.py`'s `_pending_summon` block.

The policy pattern should be: anything that spawns a new standard pet via `Pet(species_key, x, y)` should follow with `pet.apply_late_pickup_bonus(dungeon_level)` — subclassed pets that start at max level (Fenrir, Dad, Unicorn) do not need the bonus.

### 3.3 Nickname + identity

```python
self.nickname = ''
```

Set via the naming popup after Soul-Sphere hatch. If empty, display name is the species name; if set, display name becomes `"<Nickname> the <SpeciesName>"`. The nickname persists through evolution — "Sparky the Zappik" becomes "Sparky the Voltpaw" at L25.

The `name` / `symbol` / `color` properties resolve against the current `stage` so UI code reads the right stage without the pet caching it.

### 3.4 AI — `take_turn(player, dungeon, monsters, pets, ground_items)`

```python
self.command: str = 'return'   # 'return' | 'stay' | 'wander'
```

Command cycle (Shift+P → Command): `return → stay → wander → return`.

- **return** (default): follow player, engage enemies within 4 tiles.
- **stay**: hold position; only attack adjacent enemies.
- **wander**: engage enemies within 8 tiles; don't auto-follow player.

Nearest enemy is picked by Chebyshev distance. Adjacent enemies are melee-attacked regardless of command. Beyond adjacency, movement runs through `_move_toward(tx, ty, dungeon, monsters, pets, player, ground_items)`.

### 3.5 `_move_toward` (v2.18 — pit + trap awareness)

Pets now consult `dungeon.pits` and `dungeon.traps` so they don't walk into a player-dug pit or repeatedly trigger an alarm trap. The logic is **two-pass**:

```
cursed_tiles = {(gi.x, gi.y) for gi in ground_items if gi.buc == 'cursed'}
pits         = dungeon.pits
traps        = dungeon.traps
```

**Pass 1** — preferred directions (diagonal, horizontal, vertical) that skip:
- Non-walkable, player tile, monster-occupied, other-pet-occupied tiles.
- Cursed-item tiles (pets instinctively avoid cursed loot).
- Pit tiles (`in pits`) — **hard refuse, every pass**.
- Floor-trap tiles (`in traps`) — soft avoid.

**Pass 2** — same filter but tolerate traps. Only reached if every preferred direction in pass 1 was trapped. Pits still block. This "soft avoid, hard refuse" split is deliberate: forgetting the goal entirely because every path is trapped defeats the purpose of AI movement, but a pit is a one-way trip and the pet should stay out at all cost.

### 3.6 HP regen + sketch duration tick

```python
def tick_regen(self, bonus: int = 0):   # 1+bonus HP every 3 turns
```

Called every pet turn by `game_combat`. `FenrirPet` overrides for 3+bonus HP every turn (very fast). Sketched + Dad pets also decrement their `turns_remaining` counters here.

### 3.7 Dead flag + damage

```python
def take_damage(self, amount: int) -> int:
    actual = min(self.hp, max(0, amount))
    self.hp -= actual
    if self.hp <= 0: self.alive = False
    return actual
```

Dad overrides to return 0 (invincible). Unicorn's `base_damage = 0` means the pet never deals contact damage.

---

## 4. Spawn paths

### 4.1 Soul Sphere — thrown by the player

The 5%-per-floor artifact drop (`spawn_items` in dungeon.py; see [world.md](world.md) §4.2). When the player throws it:

1. If it's a **bound** sphere (recalled from a prior pet via Shift+P → Recall), the stored pet is resummoned with ALL state preserved (level, XP, nickname, kills, command). The sphere is consumed.
2. Otherwise, `random_pet_species()` picks a species, `Pet(species, spawn_x, spawn_y)` is constructed, `pet.apply_late_pickup_bonus(self.dungeon_level)` runs, and the naming popup opens.

The sphere lands at the thrown target tile; if the tile is occupied the pet falls to an adjacent walkable tile.

### 4.2 Duck of Doom transform — `main.py::_duck_of_doom_transform`

The Duck of Doom is a cursed head-slot item. Each turn the player wears it, `_duck_of_doom_tick` increments `player.quirk_progress['duck_of_doom_turns']`. On turn 2026 (`DUCK_OF_DOOM_TURNS_REQUIRED = 2026`, exported from `pet_system.py`) the transform fires:

```python
head = self.player.armor_slots[0]
# ...consume the duck, clear the counter...
pet = Pet('duck_of_doom', self.player.x, self.player.y)
pet.apply_late_pickup_bonus(int(self.dungeon_level) or 1)
self.pets.append(pet)
```

The constant lives in `pet_system.py` so the quirk code in `main.py` and any future hero-special / summon path that wants to reference the threshold agrees on a single value. Messages: "The duckie's eyes glow. It hops off your head, suddenly weightless." → "Waddlekind has hatched!".

### 4.3 FenrirPet — XYZZY tier 5

```python
class FenrirPet(Pet):
```

Spawned from `main.py` on the XYZZY hero-special at tier 5. Enters at level 100, 500 HP, base_damage 45 (~1.5× a max-level standard pet). Overrides:

- `_calc_max_hp` / `_calc_damage` are fixed constants — no scaling.
- `gain_xp` returns `[]` — doesn't level.
- `tick_regen` heals 3+bonus HP **every turn** (vs. the base class's every 3 turns).
- `take_turn` calls `super().take_turn` twice — Fenrir moves/attacks at double speed, mirroring a wolf's natural pace.

Fenrir's species dict (`_FENRIR_SPECIES`, module-level) carries two specials unlocked at `unlock_stage=0` (because Fenrir enters at max level, so stage 2 is immediate):

- **Ragnarok Bite** — adjacent single target, 2.2× holy, 50% bleed 5t (cd 200)
- **World-Shaking Howl** — pet-centered AoE r3, 1.4× holy, 60% fear 4t (cd 500)

### 4.4 SketchedPet — Leonardo's Codex Sketch

Spawned by `hero_specials.py::_eff_summon_sketch_helper` (hero special id `summon_sketch_helper`). The caller passes a target `monster`, player position, and a tier-driven duration:

```python
class SketchedPet(Pet):
    SCALE = 0.40   # 40% of monster stats
    def __init__(self, monster, px, py, duration):
```

The sketch mimics the targeted monster's `symbol`, `name`, and attack dice (`monster.attacks[0]['damage']`, default `'1d4'`) at 40% HP/damage. **Tier-scaled attacks (v2.18).** Pre-fix the sketch always used `'1d8+2'` damage regardless of tier; the hero-special data now passes a tier-scaled `damage` string (`'1d8+2'` at T1 → `'3d8+6'` at T5), aligned with other pet/spell damage curves.

Overrides:
- `name` reports `"Sketched <monster_name>"`.
- `get_attack_damage` ignores quiz accuracy and rolls the monster's dice at 40% power.
- `can_use_special` → False.
- `gain_xp` → no-op.
- `tick_duration` decrements `turns_remaining`; returns True when the sketch dissolves (sets `self.alive = False`).

### 4.5 DadPet — Dad Sphere

Spawned by `game_combat.py` on the Dad Sphere throw. Dad is comically overtuned:
- `max_hp = 99999`, `base_damage = 9999`.
- `take_damage` returns 0 (invincible).
- `duration = 5` turns, decremented by `tick_duration`.
- Symbol `'@'`, color `(255, 220, 100)`.
- Specials disabled; no leveling.

### 4.6 UnicornPet — unicorn-encounter chain

Spawned by `game_encounters.py` when the player clears the Unicorn encounter at chain ≥ 5. The unicorn joins as a non-attacking healer:

```python
self.max_hp = 120
self.base_damage = 0
```

AI differs from the base class — see `UnicornPet.take_turn`:
- **Heal** player 3-5 HP every 4 turns.
- **Cleanse** one negative status (from `status_effects.DEBUFFS`) every 8 turns.
- **Detect** traps within 3 tiles — sets `trap['revealed'] = True` (v2.18: pre-fix this set a `detected` key that nothing read, a silent no-op bug).
- **Follow** player, stay within 2 tiles. Never attacks or targets enemies.
- `tick_regen` self-heals 2 HP every 3 turns.
- `gain_xp` → no-op (unicorn doesn't level).

Return value from `take_turn` is `('unicorn_actions', [messages])` where messages are `('heal', amount)`, `('cleanse', effect_name)`, `('trap', tx, ty)` tuples the game loop prints.

### 4.7 Hero-special + spell summon paths

`game_combat.py` has a `_pending_summon` block that spawns a time-limited standard pet via `Pet(random_pet_species(), spawn_x, spawn_y)` with scaled `max_hp` and a duration flag. These paths currently **do not** call `apply_late_pickup_bonus` (open follow-up — the policy should be: every `Pet(...)` constructor site other than Fenrir/Dad/Unicorn/Sketch calls it).

---

## 5. The Shift+P pet menu

`game_menus.py` opens the pet menu with Shift+P. Items eligible for the menu exclude sketch pets and Dad (both temporary). Per-pet actions:

### 5.1 Feed — STATE_PET_FEED
Opens a sub-menu listing `Food` and `Ingredient` items in the player's inventory. On select:
- Heal: 25% of pet max HP, rounded up.
- XP: half of food's `sp_restore`, clamped 20-80.
- Consume one unit (handles stackables).

Message: `"You feed <name> the <food>. (+<n> HP, +<xp> XP)"`.

### 5.2 Heal — STATE_PET_HEAL
Lists identified `Potion` items with `effect in ('heal', 'extra_heal', 'full_heal')`. On select the potion's `power` dice are rolled and the pet is healed. Potion is consumed. The potion must be identified — unidentified potions can't be poured on pets (prevents accidental harm from a poison).

### 5.3 Pet (interaction) — once per floor
`_pet_action_pet`: bonds via XP grant of +5. Gated by `pet.last_pet_floor == self.dungeon_level` — pre-set to -1 at construction, bumped to the current floor when the player interacts. Repeat attempts on the same floor are refused with "has already had your attention this floor."

### 5.4 Recall → bound Soul Sphere
`_pet_action_recall`: requires player adjacent to the pet (Chebyshev ≤ 1). Creates a `Bound Soul Sphere (<pet_name>)` artifact with `bound_pet = pet` attached, adds to inventory, removes the pet from the active list. Throwing the bound sphere later resurrects the pet in full state. Pet menu refreshes; if no eligible pets remain, state falls back to `STATE_PLAYER`.

### 5.5 Command cycle
`_pet_action_command_cycle`: cycles `return → stay → wander → return` and prints `"<pet>: command set to <label>"`.

### 5.6 Specials
`_pet_open_specials` lists `pet.available_specials()`. On select, the targeting hint from the special definition drives the aim phase (`single` / `aoe` / `cone` / `line` / `self` / `visible_all`). Self-targeted specials (Duck Stage 0 Detect Monsters) skip the cursor phase and auto-resolve. Visible-all specials (Duck Stage 2 Sometimes Goose) iterate `game.visible`.

---

## 6. Leveling flow — worked example

A fresh Zappik hatched at F1 from an unmodified Soul Sphere:

| Floor | Pet level approx | Notes                                                          |
|-------|------------------|-----------------------------------------------------------------|
| F1    | L1 (20 HP, 3 dmg) | Hatched. Late-pickup bonus = `min(1*50, 4000) = 50` XP → still L1. |
| F10   | ~L8-12           | Kills + passive XP accumulate; still Stage 0 Zappik.           |
| F20   | ~L18-23          | Approaching the Stage 1 threshold.                              |
| F25   | **L25 → Stage 1** | Evolves to Voltpaw. Unlocks **Spark Bolt**. HP ~65, dmg ~9.    |
| F55   | **L55 → Stage 2** | Evolves to Thundertail. Unlocks **Thunder Strike**. HP ~119, dmg ~17. |
| F100  | L100 cap         | HP ~200, dmg ~30. Further XP is dropped.                        |

A Soul Sphere thrown at F40 with no bound pet:
- Random species → L1 at construction.
- Late-pickup bonus = `min(40*50, 4000) = 2000` XP → levels up repeatedly until it runs out, lands around L15-18.
- Reaches Stage 1 (L25) within ~5-7 floors of play.

A Waddlekind hatched at F30 from the Duck of Doom quirk:
- Spawns at L1 at the player's tile.
- Late-pickup bonus `min(30*50, 4000) = 1500` XP → ~L12-14.
- **Already has Stage 0 special Detect Monsters** at level 1 — the duck's Stage 0 unlock is the design reward for 2026 cursed turns.

---

## 7. Serialization + persistence

Pets live in `game.pets: list[Pet]`. The save system pickles the whole list via `Game.__getstate__`/`__setstate__` paths (see [save_meta](save_meta.md)). Fields that must round-trip:

- `species_key`, `level`, `xp`, `x`, `y`, `alive`, `hp`.
- `nickname`, `kills_count`, `command`, `last_pet_floor`.
- `_special_cooldowns` dict.
- `_regen_timer`, `_passive_xp_timer`.
- For subclassed pets: `turns_remaining` (Sketch, Dad), `_heal_timer` + `_cleanse_timer` (Unicorn), `monster_kind` + `monster_name` + `_attack_dice` + `is_sketch` (Sketch), `is_dad` / `is_unicorn` flags.

The `_special_cooldown` **singular** attribute set alongside `_special_cooldowns` by the subclasses (Fenrir / Sketch / Dad / Unicorn) is a dead legacy field — safe to ignore, present for save-compat with older runs.

---

## 8. Cross-reference

- **Progression / quirks.** Pet-affecting quirks, Trainer's Cap (`bond_check` → +1 pet level on floor entry), the Duck of Doom quirk itself → [progression](progression.md).
- **Items.** Soul Sphere spawn and throw mechanics, pet-food inventory types (`Food`, `Ingredient`), healing potions, the Duck of Doom head item → [items](items.md).
- **Combat.** Pet attack resolution, damage application to monsters, status-effect application → [combat](combat.md).
- **World.** Floor-generation hook that places Soul Spheres, pit tracking (`dungeon.pits`), trap tracking (`dungeon.traps`) that pet AI reads → [world](world.md).

---

## 9. XP curve table

With `_XP_PER_LEVEL = 20`, `xp_to_next(L) = L * 20`. Cumulative XP to reach level N:

| Target level | XP from previous | Cumulative XP | Milestone                     |
|--------------|------------------|---------------|-------------------------------|
| 1 → 2        | 20               | 20            |                               |
| 1 → 5        | 20..80           | 200           |                               |
| 1 → 10       |                  | 900           |                               |
| 1 → 15       |                  | 2,100         |                               |
| 1 → 20       |                  | 3,800         |                               |
| **1 → 25**   |                  | **6,000**     | **Stage 1 evolution unlock**  |
| 1 → 30       |                  | 8,700         |                               |
| 1 → 40       |                  | 15,600        |                               |
| 1 → 50       |                  | 24,500        |                               |
| **1 → 55**   |                  | **29,700**    | **Stage 2 evolution unlock**  |
| 1 → 70       |                  | 48,300        |                               |
| 1 → 85       |                  | 71,400        |                               |
| 1 → 100      |                  | 99,000        | L100 cap — further XP dropped |

With the kill-XP formula `3 + max_hp // 10` and typical monster HPs scaling 10 → 300 across floors, a pet averaging ~1 kill per 3 turns in a 200-turn floor gets roughly 400-1500 XP per floor from kills plus 60-70 XP from passive. The late-pickup bonus (`min(floor * 50, 4000)`) covers the first 10-25 floors of catch-up for a hatched-late pet.

---

## 10. Pet-turn ordering

Pet turns run inside `game_combat.py`'s turn loop, after the player action resolves. For each alive pet, in list order:

1. **`tick_cooldown()`** — decrement every active special cooldown by 1; evict entries that hit zero.
2. **`tick_regen(bonus)`** — HP regen pass (varies by subclass).
3. **`tick_duration()`** — temporary pets only (Sketch, Dad). If it returns True, the pet dissolves.
4. **`gain_xp_passive()`** — may return messages for level-ups.
5. **`take_turn(player, dungeon, monsters, pets, ground_items)`** — AI action.
6. **Resolve action** — `('attack', target)` → melee damage with quiz-accuracy scaling; `('unicorn_actions', msgs)` → iterate healing/cleanse/trap messages; `None` → no action.
7. **Post-kill XP** — if the action killed a monster, `gain_xp_from_kill(monster_max_hp)` runs and may produce evolution messages.

Dead pets are left in the list but skipped by `take_turn` (they return None immediately). The game loop prunes dead pets on floor transitions (`_change_level`) so stale references don't accumulate.

---

## 11. Species picking + distribution

```python
def random_species() -> str:
    pool = [k for k in _SPECIES.keys() if k != 'duck_of_doom']
    return random.choice(pool)
```

4 standard species → each has 25% probability on a random Soul Sphere hatch. There's no weighting by element or floor — fire pets appear on F1 as readily as water pets. The `duck_of_doom` exclusion is enforced here (don't push the exclusion to call sites).

If a design future adds a sixth species, it defaults in to the random pool unless explicitly excluded. Common pattern: new "reward" species (hatched from a quirk / mystery / scripted event) should be excluded from `random_species` the same way Waddlekind is.

---

## 12. Soul Sphere lifecycle

```
spawn_items (5%/floor)
    ↓
Soul Sphere Artifact on the floor
    ↓
player picks up → inventory
    ↓
player throws (press 't' + aim)
    ↓ (lands on target tile or an adjacent walkable tile)
┌───────────────────────────────┐
│ sphere.bound_pet is None?     │
├── YES → random_pet_species()   │
│         Pet(species, x, y)     │
│         apply_late_pickup_bonus │
│         open naming popup      │
├── NO  → bound_pet re-added     │
│         to self.pets with ALL  │
│         saved state preserved  │
└───────────────────────────────┘
    ↓
pet in play
    ↓
Shift+P → Recall
    ↓
bound_pet attached to new sphere
    ↓
sphere in inventory, pet removed from active list
    ↓
(repeat throw cycle)
```

The bound sphere is **cyan-tinted** (`color=[80, 200, 255]`) to visually distinguish it from a fresh sphere (`color=[255, 80, 80]`). Its name reads `"Bound Soul Sphere (<pet_name>)"`. Lore reads: "A Soul Sphere humming with the bound spirit of <name>. Hurl it to summon them back to your side."

Recall requires adjacency to the pet (Chebyshev ≤ 1). This prevents long-range recall shenanigans and makes recalling a wandering pet require you to catch it first.

---

## 13. Pet-food details

Pet-food is any `Food` or `Ingredient` in the player inventory. Cooked compound recipes (made via the cooking system) tend to carry higher `sp_restore` and are therefore better pet-food than raw ingredients:

| Food type              | Typical sp_restore | Pet XP (half, clamped 20-80) |
|------------------------|--------------------|-------------------------------|
| Raw ingredient         | 10-30              | 20 (hits clamp floor)         |
| Prepared basic recipe  | 40-70              | 20-35                         |
| High-tier cooked meal  | 80-160             | 40-80                         |
| Trophy meal            | 100-200            | 50-80 (hits clamp ceiling)    |

The 25%-max-HP heal is independent of the XP calculation — feeding a Zappik any food heals it 5 HP (20 max × 0.25), feeding a L100 Thundertail heals it ~50 HP (200 max × 0.25).

Stackable foods are decremented one unit per feed (`food.count -= 1`); non-stackable foods are removed from inventory on feed. This mirrors how the player self-eat path consumes stacks.

---

## 14. Pet rendering + display

- **Glyph**: `pet.symbol` property returns the per-stage character.
- **Color**: `pet.color` property returns the species RGB tuple.
- **Sprite fallback**: SketchedPet mirrors a monster's `kind` so renderers that look up `monster_kind` to find the sprite see the sketched creature's monster-sprite rather than a generic pet-sprite.
- **Sidebar / info panel**: shows name (nickname + species or species alone), level, HP/max_HP, XP progress bar toward next level, and command label.
- **Specials menu**: `pet.available_specials()` filtered by `unlock_stage <= stage`; cooldowns pulled from `_special_cooldowns`.

Dead pets are not rendered. Sketch/Dad pets with `turns_remaining <= 0` set `alive = False` and get pruned.

---

## 15. Design notes

- **Pokémon pattern.** The 3-stage evolution + per-species single-target + AoE specials deliberately echoes a Pokémon starter. The 4 elemental species (electric/water/plant/fire) include the three classic Gen-1 starter types; Zappik is the Pikachu equivalent and the only standard species with a stage 0 lowercase glyph.
- **Reward asymmetry.** Fenrir, Dad, and Unicorn are **reward pets** acquired through specific gates (XYZZY T5 hero-special, Dad Sphere, Unicorn-encounter chain 5). None of them level — they come at full power. Waddlekind is the fifth reward pet, costing 2026 cursed-turns.
- **Why L100 cap?** Pet stats scale to roughly match a mid-tier F100 monster. Beyond L100 the pet would overshoot even boss stat budgets, breaking the pet-as-helper design (pets are a *support* line, not a replacement for the player).
- **Why command cycle, not toggles?** Each pet gets ONE menu action (vs. per-command checkboxes). Cycle is one keypress to iterate `return → stay → wander`, matching the one-keypress feel of the rest of the pet menu.
- **Soul-sphere late-pickup bonus curve.** `min(floor * 50, 4000)` caps at F80 (`80 * 50 = 4000`). The curve is deliberately below the Stage 1 evolution threshold (6000 XP) so a late pet still has to earn its first big milestone through play. Design intent: the bonus closes the "useless-at-spawn" gap but preserves the growth arc.

---

## 16. Invariants (do not break)

1. **`DUCK_OF_DOOM_TURNS_REQUIRED = 2026` lives in `pet_system.py`.** Both the quirk timer in `main.py` and any future hero-special that references the threshold must import it from here.
2. **`random_species()` excludes `duck_of_doom`.** Waddlekind is the Duck quirk endpoint, not a random Soul Sphere outcome. If a new random spawner is written, use `random_pet_species` (the `game_combat.py` alias) and inherit the exclusion.
3. **`apply_late_pickup_bonus` is called on every `Pet(species, x, y)` construction unless the pet starts at max level.** Soul Sphere ✓, Duck transform ✓ (v2.18). The hero-special + spell-summon paths still need to be wired — don't ship a new summon site without it.
4. **Pet `_move_toward` consults `dungeon.pits` + `dungeon.traps`.** Pits are hard refuse (always); traps are soft avoid (pass 1 skip, pass 2 tolerate). Never collapse the two-pass structure — forgetting the goal because every direction is trapped is worse than stepping on an alarm.
5. **The "SketchedPet is temporary" invariant depends on `tick_duration` being called every pet turn.** The audit flagged this call site as the risk area — a lost tick means a permanent sketch pet.
6. **Dad is invincible.** `take_damage` returning 0 is load-bearing — Dad has to survive to the duration timeout.
7. **Unicorn sets `trap['revealed'] = True`** (not `detected`). Pre-v2.18 the wrong key was being written and the whole feature was a silent no-op. Keep the key name aligned with `_check_floor_trap` + `_try_disarm_trap` + renderer.
8. **L100 is the pet level cap.** `gain_xp` short-circuits at L100 and drops residual XP. Raising the cap means re-stat-curving `_calc_max_hp` + `_calc_damage`.
