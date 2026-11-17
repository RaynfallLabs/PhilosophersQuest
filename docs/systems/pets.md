# Pets

**Scope.** Companion creatures that follow the player, fight alongside them, and (for most species) level up and evolve. The entire system is in `src/pet_system.py` — species dictionary, Pet base class, four subclassed one-off pets, and the `random_species()` picker. Call sites that spawn or transform pets live in `src/game_combat.py` (the six Soul Spheres, the Unusual Soul Sphere (Dad), summon-at-adjacent), `src/main.py` (`_duck_of_doom_transform`), `src/hero_specials.py` (Leonardo's Codex Sketch), `src/game_manifest.py` (the Dreamspun Sketchbook's Manifest), `src/game_encounters.py` (Unicorn), and `src/game_menus.py` (Shift+P pet menu — feed, heal, pet-interaction, recall, command cycle, specials).

Out of scope here: pet damage resolution inside combat (see [combat](combat.md)), quirks that change pet behavior (see [progression](progression.md)), and the specific items that spawn or heal pets (Soul Sphere, pet-food, healing potions on pets — see [items](items.md)).

**File map.**
```
src/pet_system.py       # Species, Pet, FenrirPet, SketchedPet, DadPet, UnicornPet, random_species;
                        # the six spheres: spheres, sphere_spec, hatch_level, roll_sphere_species, sphere_for_floor
src/game_combat.py      # the six Soul Spheres, the Unusual Soul Sphere (Dad), bound-sphere resummon, _dig_pit
src/game_menus.py       # Shift+P pet menu + sub-menus (feed/heal/pet/recall/command/specials)
src/game_encounters.py  # UnicornPet spawn via unicorn-encounter chain
src/hero_specials.py    # SketchedPet via Leonardo's Codex (summon_sketch_helper)
src/sketch_manifest.py, src/game_manifest.py, data/manifest.json
                        # SketchedPet via the Dreamspun Sketchbook's Manifest (its menu, the quiz)
src/main.py             # _duck_of_doom_tick + _duck_of_doom_transform, FenrirPet via XYZZY T5
src/bococho_encounter.py, src/game_race.py, src/race.py, src/riding.py, src/game_riding.py
                        # the Bococho: the camp, the race, her saddlebags, riding
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
| sherlock    | Sherlock → Sherlock the Stout → Sherlock the Immovable | earth  | crushing    |
| irene       | Irene → Irene the Skyleaper → Irene the Seraph      | air       | slashing    |
| shep        | Shep → Shep the Farmhound → Shep the Legend         | earth     | piercing    |
| mooble      | Mooble → Mooble Dancer → Mooble Troupe-Leader       | light     | piercing    |
| bococho     | Bococho Chick → Bococho → Bococho Champion          | earth     | crushing    |

`sherlock` and `irene` (the family cats, `family_cat: True`) and `shep` (the family farm dog, `family_dog: True`) are rare hatches from an ordinary sphere and the sure hatch of a Hearth Sphere, met at most once a run; see §11 and §12.

`mooble` is a **quest pet** (`quest_pet: True`): won by his own story (the Mooble, at the end of this file), never from a sphere (`random_species` leaves out every quest pet). His species lives in his own data file, `data/mooble.json` (`pet.species`), and `pet_system._load_quest_species` adds it to `_SPECIES` at import. A stage may name its own picture (`sprite`: `mooble_troupe_leader`, not the stage name's "troupe-leader"), with `sprite_standin` shown until that file is installed (`pet_system.art_or_standin`; never a letter on the map).

### 1.2 Random pool
`pet_system.random_species()` returns a random key with equal probability from `_SPECIES`, **excluding `duck_of_doom`** (v2.18) **and every companion with its own name** (`has_own_name`: the family cats and Shep) **and every quest pet** (`quest_pet`: the Mooble). Waddlekind is the endpoint of the 10,000-turn Duck-of-Doom quirk, not a Soul Sphere / Summon Guardian / Gate outcome; the exclusion closes a leak where throwing a Soul Sphere could pop a free Waddlekind without the quirk commitment. Call sites that need a random species import this helper as `random_pet_species`.

### 1.3 Evolution thresholds
```python
_EVOLVE_1 = 25
_EVOLVE_2 = 55
_XP_PER_LEVEL = 20   # xp_to_next = level * _XP_PER_LEVEL
```

Totals: ~6,000 XP to L25, ~30,000 XP to L55. Combined with passive XP (one grain every 3 pet turns) + per-kill XP, a newborn reaches stage 1 around 20-25 pet-floors and stage 2 only in deep late-game play. A Greater or Master sphere skips the climb: its pet hatches AT 25 or 55 (§12). The L100 cap is terminal — further XP is silently dropped.

---

## 2. Specials schema

Each entry in `_SPECIES[species_key]['specials']` is one activated attack:

| Field              | Type   | Meaning                                                               |
|--------------------|--------|------------------------------------------------------------------------|
| `id`               | str    | Unique id used in cooldown table + menu                              |
| `name`             | str    | Display name                                                           |
| `unlock_stage`     | int    | 0, 1, or 2. Available iff `pet.stage >= unlock_stage`                 |
| `damage_mult`      | float  | Multiplier on `pet.base_damage` (scaled by quiz accuracy)             |
| `damage_type`      | str    | shock / cold / poison / fire / psychic / holy; lands through `_pet_hit` as the monsters' word (`pet_damage_type`: piercing→pierce, slashing→slash, crushing→blunt, shock→lightning), so resistances, weaknesses and split-by-form apply |
| `targeting`        | str    | `single`, `aoe`, `cone`, `line`, `self`, `visible_all`                 |
| `range`            | int    | Tiles. 0 = pet-centered for `aoe`/`self`                              |
| `aoe_radius`       | int    | Tiles (for `aoe` + `cone`)                                            |
| `status`           | str    | Status effect applied on hit (`paralyzed`, `slowed`, `immobilized`, `poisoned`, `burning`, `confused`, `feared`, `bleeding`) |
| `status_chance`    | float  | 0.0-1.0                                                                |
| `status_duration`  | int    | Turns                                                                  |
| `leap`             | bool   | The pet moves beside the target (Pounce, Seraph Dive, Sic 'Em!). The target tile must be in the hero's sight with no rock between pet and tile; a single-target leap only goes for a creature the hero can see |
| `knockback`        | int    | Tiles pushed straight away from the pet (water specials; `_pet_knockback`: walls, bodies, bosses, big and stationary creatures stop it) |
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

### 2.1a Family companions (rare Soul Sphere hatches)

| Species  | Stage 1 (unlock L25) | Stage 2 (unlock L55) |
|----------|----------------------|----------------------|
| sherlock | **Belly Flop** — adjacent AoE, 1.5× crushing, 50% stun 2t, then heals himself 20% (cd 250) | **Midnight Aria** — pulls foes within 4, then AoE r2, 1.6× sonic, 50% confuse 3t (cd 400) |
| irene    | **Pounce** — single, range 4, leaps beside it, 1.5× slashing, 50% bleed 3t (cd 250) | **Seraph Dive** — AoE 3×3 at range 5, flies there, 2.0× holy, 40% blind 3t (cd 400) |
| shep     | **Sic 'Em!** — single, range 7, dashes beside it, 1.7× piercing, 50% stun 2t (cd 250) | **Sic 'Em All!** — `targeting='hero_adjacent'`: from anywhere, dashes to the hero and bites every foe beside the hero, 2.0× each, 50% stun 2t (cd 400) |

Shep's line is the one deliberately stronger family line (about a tenth: 1.7× against the others' 1.5× at stage 1; 2.0× against the cats' 1.6×/2.0× at stage 2). His growth table is everyone's.

**He Always Comes (Shep, passive, from hatching).** `species['rescue']`, run by `_shep_rescue()` at the top of `_do_pet_turns` (straight after the monsters' turn). When the hero is at 25% health or less with a foe beside him that can fight (not asleep, paralysed, stunned, frozen, feared or charmed), Shep comes from anywhere on the floor to the hero's side (`_dash_pet_to_hero`) and hits the toughest adjacent foe for 1.5× with a 50% stun (2t); that is his turn. Shep the Legend (stage 2) hits every adjacent foe and then the hero is Shielded for 3 turns. Once a floor: `rescue_spent_at` holds the hero's deepest floor when it was used, so it comes back only on a floor reached for the first time, like every other once-a-floor charge.

**Hackles Up (Shep, passive, from hatching).** `species['growl']`, run by `_do_pet_growl()` each turn straight after `_do_warning()`. The real Shep lowered his head and growled at danger. When a hostile the hero cannot see comes within 5 / 6 / 7 tiles of the hero (by stage), and Shep is alive and within 10 tiles, the log says he growls low, staring toward the nearest one (compass word). Each monster sets him off once (`_growled_at`, keyed on `pet_system.growl_tag`, which lasts through a save) until it dies, goes more than two tiles past his range, or the floor changes; the hero glimpsing it does not reset it. So a lurking threat is one growl, not one a turn; allies, encounter NPCs and the unicorn never set him off.

### 2.2 Duck of Doom specials (unique shape)

Unique among species: Waddlekind has a **Stage 0** special, because the player already paid 10,000 cursed turns to be here.

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

**Starting level (LORE NOT FLOOR, 2026-10-18).** A pet starts at the level its ORIGIN gives it, never the floor's: `Pet(species, x, y, level=...)`. A sphere's pet starts at `pet_system.hatch_level(sphere)` (1, 25 or 55, from the sphere's data; §12); the Emberpup is a pup (level 1); Waddlekind starts with `DUCK_OF_DOOM_HATCH_XP` (10,000 // 3 = 3,333 XP: what any companion riding along for 10,000 turns would have learned); summons take their spell's level (`SUMMON_GUARDIAN_LEVEL`, `GATE_ALLY_LEVEL`) or the slain creature's own. The old late-pickup grant (`apply_late_pickup_bonus`, floor x 50 XP up to 4,000) was a floor multiplier and is gone; `tests/test_lore_not_floor.py` fails if any hatch reads the floor again.

### 3.3 Nickname + identity

```python
self.nickname = ''
```

Set via the naming popup after a sphere hatch. If empty, display name is the species name; if set, display name becomes `"<Nickname> the <SpeciesName>"`. The nickname persists through evolution — "Sparky the Zappik" becomes "Sparky the Voltpaw" at L25.

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

### 3.5 `_move_toward` (v2.18 — pit + trap awareness; 2026-10-24 — routes round walls)

First `_route_step` looks for the shortest walk (breadth-first, at most
`_ROUTE_LIMIT` tiles, eight directions) to a tile beside the goal, under the
same rules as one step below (traps avoided on the first search, allowed on a
second). A pet that only tried the three steps pointing at its goal stood in a
room's corner when the straight line met a wall. The two passes below are the
fallback when no route exists.

**Being hit.** A monster beside a pet swipes at it once a turn
(`_monster_swipes`): half its first attack's dice when it is also beside the
hero (it has struck him this turn), but a whole blow of one of its attacks when
it cannot reach him, or when the pet bit it in the last two turns
(`_pet_aggro`). Every hit the hero can see is in the log ("The goblin hits
Ember."); before 2026-10-24 a pet's wounds were silent, so pets looked
untouchable. The unicorn is never targeted.

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

Called every pet turn by `game_combat`. `FenrirPet` overrides for 3+bonus HP every turn (very fast). Sketched pets also decrement their `turns_remaining` counters here; Dad does only when he has no song (one pickled before 3.5.2).

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

### 4.0 One companion at a time (2026-11-06)

Brandon's rule: one bonded companion walks with the hero. Before a new one joins, `CombatMixin._companions_to_stasis()` puts the one at his side back into a Bound Soul Sphere in the pack (from any distance, state kept, exactly as Recall does; `_bound_sphere_for` builds the sphere for both). In the sphere it gains no XP and needs no food. A pack over its limit sets the sphere at the hero's feet; it is never lost. A save from before the rule may have several companions out: the next join stores all of them.

- **Counts** (`pet_system.is_companion`): a pet from any of the six Soul Spheres or a bound sphere (the family cats and Shep too, and a rare hatch from the Unusual Soul Sphere), the Emberpup, the Mooble, the Bococho, Waddlekind, and the Summon Guardian and Gate spells.
- **Extras, never stored:** Dad, a sketch (the Sketchbook's Manifest or Leonardo's helper), an ally sprung from a kill (`_temp_duration`), Fenrir, the Army of Darkness deadites (`_summoned_minion`), and the unicorn (a healer that never fights). A bound sphere holding one of these does not store the companion when thrown.

### 4.1 The six Soul Spheres — thrown by the player

Found on the floor by band, or bought from a trader (§12). When the player throws one (`game_combat._throw_soul_sphere`):

1. If it's a **bound** sphere (recalled via Shift+P → Recall, or stored by the one-companion rule, §4.0), the companion at the hero's side goes into a sphere first, then the stored pet is resummoned with ALL state preserved (level, XP, nickname, kills, command, `hatch_sphere`). The sphere is consumed. No naming popup.
2. Otherwise `roll_sphere_species(sphere, present)` picks the species (an ordinary sphere: rarely Shep or a family cat, else `random_species()`; a Hearth Sphere: one of the family not yet met, else `random_species()`; see §11), the sphere's kind becomes known (as a thrown potion's does), and `_hatch_sphere_pet(species, x, y, level=hatch_level(sphere), sphere_id=sphere.id)` builds the pet at its sphere's level, logs `hatch_message(pet)` (a grown pet has its own stage words: "out steps Shep the Legend..."), and opens the naming popup (defaulting to the species name at that stage: "Shep the Farmhound"; Shep and the family cats bring their own popup words, `naming_story`).

Once a sphere's kind is known (thrown, identified, or bought known), it has an Encyclopedia page under **Wonders** (B, l): its art, its lore and the level it wakes at, never who hatches from it (`Game._wonder_entries`, 2026-10-18).

The sphere lands at the thrown target tile; if the tile is occupied the pet falls to an adjacent walkable tile. With no room at all, any sphere (bound or not) rolls to a stop unbroken on the open tile it reached, to be thrown again somewhere with room (it used to shatter, wasting an unbound one).

### 4.2 Duck of Doom transform — `main.py::_duck_of_doom_transform`

The Duck of Doom is a cursed head-slot item that does nothing for the hero: no AC, no enchantment, just a duck taking up his head (Brandon 2026-11-16: "It's supposed to SUCK to have it on your head. No benefits"). Lifting its curse (a scroll of remove curse, an altar) is the one way to take it off early, and an uncursed duck can be taken off like any hat. Each turn the player wears it, `_duck_of_doom_tick` increments `player.quirk_progress['duck_of_doom_turns']`. On turn 10,000 (`DUCK_OF_DOOM_TURNS_REQUIRED = 10000`, exported from `pet_system.py`; it was 2026 until 2026-11-16, "too quick, just a few floors") the transform fires:

```python
head = self.player.armor_slots[0]
# ...consume the duck, clear the counter...
pet = Pet('duck_of_doom', *spot)
pet.gain_xp(DUCK_OF_DOOM_HATCH_XP)    # 675 XP: what it learned riding along, not the floor
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

### 4.4 SketchedPet — the Dreamspun Sketchbook's Manifest, and Leonardo's Codex Sketch

Two things make a sketch: Manifest, the power the **Dreamspun Sketchbook** grants while carried (Fianna, Fluffs and Leonardo start with it), and Leonardo's hero special Codex Sketch (`hero_specials.py::_eff_summon_sketch_helper`, special id `summon_sketch_helper`). Both are helpers that come and go, never a companion (§4.0).

```python
class SketchedPet(Pet):
    SCALE = 0.40          # 40% of the subject's health
    bite_type = 'physical'   # class default: a sketch pickled before 2026-11-15
    def __init__(self, monster, px, py, duration):
```

**Manifest (2026-11-15; Brandon: "she should be able to Manifest ANY monster she has studied... sorted by level, descending"; "the image last[s] based on how many quiz questions she gets right, with the base being her INT").** The rules are `data/manifest.json` and the pure `src/sketch_manifest.py`; the Game side (menu, quiz, spawn, QA key) is `src/game_manifest.py` (`ManifestMixin`).

- **She draws from memory.** V, Manifest opens `STATE_MANIFEST_MENU` (no turn spent): every kind she has **studied** (`family_lore.studied`: a correct corpse study, the Wand of Probing, Omnisight) plus any creature **in view** (`Game._sees_monster`; so a first meeting can still be drawn). Never a boss or a named foe: a kind with `is_boss`, `is_mini_boss`, `proper_noun`, `quest_only`, `is_seal_demon` or `is_allied` (`exclude_flags`), the cow level's `hell_bovine` and `cow_king` and the Black Knight (`exclude_kinds`), or a kind with no `family` or no attack. With nothing to draw: "You open the sketchbook, but there is nothing to draw yet. Study a creature first."
- **The menu** (`ui.md` §13b): tabs All, then one per bite type she can draw (in `affinity.HERO_TYPES` order, each with its count); rows sorted by level, highest first, then name, each with the kind's picture, name, level and bite type ("In View" for a kind seen but never studied). A creature in view whose kind she KNOWS (`family_lore.knowledge` = KNOWN: studied, its page opened, or its family at Lore) marks every row whose bite it is weak to with **Weak!**; the detail says "Strong against <Name>" (and "Resisted by <Name>"), and the menu opens on the tab with the most such kinds ("Opened on Blunt: Strong against Skeleton"), else on All. The detail pane: the picture large, level, attack type, health, bite, memory or sight, how long it lasts. Enter draws; Esc closes, no turn spent.
- **The quiz is unchanged:** AI, `escalator_chain`, tier 1, max chain 5 (`quiz`). No right answer and the page smudges (no sketch, the power stays ready).
- **Duration = INT + 5 turns for each right answer** (`base_stat` + `turns_per_right` x chain): INT 14 with all five right is 39 turns (Fianna's INT 14 is 16 while she carries the sketchbook, its `carry_bonus`: 41 turns). The menu says it: "Lasts INT (14) + 5 turns for each right answer: up to 39 turns."
- **The sketch** is made from the kind's definition (`Monster(dict(defn, id=kind))`), its health the kind's MEAN health (`sketch_manifest.mean_hp`, from its `hp` dice) times `SCALE`, set beside the hero (a free tile next to him, else `_escort_tile_near_hero`, never his own tile; no room and it fades). The power then rests for `cooldown` (500) turns.
- **It fights like its subject.** `bite_type` is the subject's FIRST attack's `type` in the hero's words (`sketch_manifest.bite_type_of`): the HERO_TYPES as they are; `necrotic` and `shadow` drain, `psionic` is magic, a plain `physical` blow is blunt (`type_map`); anything else stays plain physical. In `Game._do_pet_turns` a sketch's bite calls `target.take_damage(dmg, bite_type)`, so a weakness doubles it, a resistance halves it, and the hit lines say so (`affinity.note`). Every other pet's plain bite is still physical. A sketch pickled before this has no `bite_type` of its own and reads the class default, physical: it bites as it always did.
- **QA:** on the Titivillus build, Shift+V puts the sketchbook in the pack, studies every kind it can draw up to `min_level` max(10, floor + 5) (`qa`) and readies the power (`ManifestMixin._qa_manifest`).

**Bite and level.** The sketch's level is its subject's `min_level` (1-100); a Sketchbook drawing bites like a pet of that level (`growth('bite', level)`, give or take a fifth). Leonardo's helper bites by its table's dice (`bite_dice`: `'1d8+2'` at chain 1 → `'3d8+6'` at chain 5); bug bash 4, ruling 30: the table was never read and a chain-5 helper bit for 254 on floor 1. The helper's attack has no type, so it bites plain physical.

Overrides:
- `name` reports `"Sketched <monster_name>"`.
- `get_attack_damage` ignores quiz accuracy: the helper's `bite_dice` if it has them, else the level bite give or take a fifth.
- `can_use_special` → False.
- `gain_xp` → no-op.
- `tick_duration` decrements `turns_remaining`; returns True when the sketch dissolves (sets `self.alive = False`).

### 4.5 DadPet — the Unusual Soul Sphere

Spawned by `game_combat.py` when the Unusual Soul Sphere is thrown (`_throw_unusual_sphere`). The Unusual Soul Sphere is NOT one of the six (it has no `sphere` block): only the family secret builds start with it, it is never spawned, sold or hinted at, and nothing in the 2026-10-18 sphere change touched it. Dad is comically overtuned:
- `max_hp = 99999`, `base_damage = 9999`.
- `take_damage` returns 0 (invincible).
- `duration = 5` turns, decremented by `tick_duration`.
- Symbol `'@'`, color `(255, 220, 100)`.
- Specials disabled; no leveling.

The Unusual Soul Sphere first makes the same rare roll as an ordinary sphere (`roll_rare_sphere_pet`: Shep 1%, each cat 5%, each only while not yet met); a companion it hatches is a newborn (level 1). Only when that misses does Dad come, with his song: "The Greatest Trainer of All Time" (Brandon's, as A Man Before a King; the song Dad and his special attacks come from) plays in place of the soundtrack, and Dad stays exactly as long as it plays, in real seconds (3.5.2: `DadPet.song_id`; `game_songs._song_over` sees him off when it ends, with its closing line "Dad smiles at you and fades away. He believes in you!"; a song no longer playing takes him at his next turn). On a boss floor it is not used up, and with another song playing (one song at a time: `songs.py`) it stays in the pack. QA: Shift+U on the Titivillus build puts one in the pack.

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

`game_combat.py` has a `_pending_summon` block that spawns a time-limited standard pet via `Pet(random_pet_species(), spawn_x, spawn_y)` at the slain creature's own level (from `monsters.json`) with scaled `max_hp` and a duration flag. Summon Guardian and Gate use their spell's level. None of them reads the floor.

---

## 5. The Shift+P pet menu

`game_menus.py` opens the pet menu with Shift+P. Items eligible for the menu exclude sketch pets and Dad (both temporary).

**The card shows the pet** (round 3, 2026-11-14: "pet panel should show the pet, just like bestiary and item lore"). `_draw_pet_menu` gives each entry a `plate`: `lore_art.pet_ref(pet)`, the sprite the map draws for it NOW (`Pet.sprite_id`: the stage it has grown to; the Emberpup in the Bloomleaf Cloak has `<stage>_cloaked` for every stage). The decision menu heads the Detail pane with it (`_menu_draw_portrait`): `lore_art.plate` in the lore pages' framed well (`_draw_plate_well`), the largest whole enlargement (3x at UI scale 1, 2x or 1x when the card is long) that leaves the card room, with the name, level, HP, XP, sphere and command beside it, and the cloak, Shep's rescue and growl below. A pet with no art has no picture, never a letter glyph (the Bestiary's rule). The actions (F/P/H/R/C/S) sit in the Choices pane under the companion's row (`list_footer`), and the Detail pane is the wider one (`detail_share`): Shep's whole card did not fit one pane at 1280x720. Captures: `menu_pet`, `menu_pet_plain`, `menu_pet_final_stage`, `menu_pet_cloaked`, `menu_pet_cloaked_evolved`, `menu_pet_cloaked_final`, `menu_pet_shep`.

Per-pet actions:

### 5.1 Feed — STATE_PET_FEED
Opens a sub-menu listing `Food` and `Ingredient` items in the player's inventory: a scrolling list beside a detail pane (`_draw_pet_sub_picker` → `_draw_decision_menu`), so every food is reachable with Up/Down, PgUp/PgDn, Home/End or its letter, with a scroll bar and "x-y of N" when the list is long (the old two-column picker seemed to stop at eight; 2026-10-18). The heal picker below is the same list. On select:
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

A fresh Zappik hatched at F1 from a Soul Sphere:

| Floor | Pet level approx | Notes                                                          |
|-------|------------------|-----------------------------------------------------------------|
| F1    | L1 (20 HP, 3 dmg) | Hatched as a newborn.                                          |
| F10   | ~L8-12           | Kills + passive XP accumulate; still Stage 0 Zappik.           |
| F20   | ~L18-23          | Approaching the Stage 1 threshold.                              |
| F25   | **L25 → Stage 1** | Evolves to Voltpaw. Unlocks **Spark Bolt**. HP ~65, dmg ~9.    |
| F55   | **L55 → Stage 2** | Evolves to Thundertail. Unlocks **Thunder Strike**. HP ~119, dmg ~17. |
| F100  | L100 cap         | HP ~200, dmg ~30. Further XP is dropped.                        |

A Soul Sphere thrown at F40 hatches the same newborn as one thrown at F1: the floor does not matter. A Greater Soul Sphere (found from floor 34, or bought) hatches a Voltpaw at L25 with Spark Bolt; a Master Sphere (from floor 67, or from Vesper from 61) hatches a Thundertail at L55 with both specials.

A Waddlekind hatched from the Duck of Doom quirk:
- Spawns beside the hero with 675 XP (about L8) on any floor.
- **Already has Stage 0 special Detect Monsters** — the duck's Stage 0 unlock is the design reward for 10,000 cursed turns.

---

## 7. Serialization + persistence

Pets live in `game.pets: list[Pet]`. The save system pickles the whole list via `Game.__getstate__`/`__setstate__` paths (see [save_meta](save_meta.md)). Fields that must round-trip:

- `species_key`, `level`, `xp`, `x`, `y`, `alive`, `hp`.
- `nickname`, `kills_count`, `command`, `last_pet_floor`, `hatch_sphere` (the sphere id it hatched from, for the card's "Hatched From" line; absent on pets from older saves and on non-sphere pets, which simply show no line).
- `_special_cooldowns` dict.
- `_regen_timer`, `_passive_xp_timer`.
- For subclassed pets: `turns_remaining` (Sketch, Dad), `_heal_timer` + `_cleanse_timer` (Unicorn), `monster_kind` + `monster_name` + `_attack_dice` + `is_sketch` (Sketch), `is_dad` / `is_unicorn` flags.

The `_special_cooldown` **singular** attribute set alongside `_special_cooldowns` by the subclasses (Fenrir / Sketch / Dad / Unicorn) is a dead legacy field — safe to ignore, present for save-compat with older runs.

---

## 8. Cross-reference

- **Progression / quirks.** Pet-affecting quirks, Trainer's Cap (`bond_check` → +1 pet level on floor entry), the Duck of Doom quirk itself → [progression](progression.md).
- **Items.** The six Soul Spheres (data, identity, prices), pet-food inventory types (`Food`, `Ingredient`), healing potions, the Duck of Doom head item → [items](items.md), [economy](economy.md).
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

With the kill-XP formula `3 + max_hp // 10` and typical monster HPs scaling 10 → 300 across floors, a pet averaging ~1 kill per 3 turns in a 200-turn floor gets roughly 400-1500 XP per floor from kills plus 60-70 XP from passive. There is no catch-up grant for a pet hatched deep: a stronger start comes from a stronger sphere.

---

## 10. Pet-turn ordering

Pet turns run inside `game_combat.py`'s turn loop, after the player action resolves. For each alive pet, in list order:

1. **`tick_cooldown()`** — decrement every active special cooldown by 1; evict entries that hit zero.
2. **`tick_regen(bonus)`** — HP regen pass (varies by subclass).
3. **`tick_duration()`** — temporary pets only (Sketch, and Dad with no song). If it returns True, the pet dissolves. Dad with his song: the song decides.
4. **`gain_xp_passive()`** — may return messages for level-ups.
5. **`take_turn(player, dungeon, monsters, pets, ground_items)`** — AI action.
6. **Resolve action** — `('attack', target)` → melee damage with quiz-accuracy scaling; `('unicorn_actions', msgs)` → iterate healing/cleanse/trap messages; `None` → no action.
7. **Post-kill XP** — if the action killed a monster, `gain_xp_from_kill(monster_max_hp)` runs and may produce evolution messages.

Dead pets are left in the list but skipped by `take_turn` (they return None immediately). The game loop prunes dead pets on floor transitions (`_change_level`) so stale references don't accumulate.

---

## 11. Species picking + distribution

```python
def random_species() -> str:
    pool = [k for k in _SPECIES.keys()
            if k != 'duck_of_doom' and not has_own_name(_SPECIES[k])
            and not _SPECIES[k].get('quest_pet')]
    return random.choice(pool)
```

An ORDINARY sphere's hatch (Soul, Greater Soul or Master; `roll_soul_sphere_species`) first makes the rare roll, `roll_rare_sphere_pet`: Shep's 1% on his own random stream (`_SHEP_RNG`), then each family cat's 5% on theirs (`_CAT_RNG`). Neither touches the global stream that seeded floors depend on. Only when both miss does `random_species()` pick one of the four elemental lines evenly. While Shep is still to be met the cats' roll is rescaled (`shep_in_play`) so each cat stays at exactly 5% of all hatches.

| Already met this run | Shep | Sherlock | Irene | Each elemental line |
|----------------------|------|----------|-------|---------------------|
| nobody               | 1%   | 5%       | 5%    | 22.25%              |
| Shep                 | —    | 5%       | 5%    | 22.5%               |
| one cat              | 1%   | 5% / —   | — / 5% | 23.5%              |
| both cats            | 1%   | —        | —     | 24.75%              |
| all three            | —    | —        | —     | 25%                 |

A HEARTH sphere (any tier; `roll_family_sphere_pet`, its own stream `_FAMILY_SPHERE_RNG`) always holds one of the family not yet met: `FAMILY_SPHERE_ODDS` Sherlock 40%, Irene 40%, Shep 20%, a met one's share spread over the rest in proportion.

| Already met this run | Sherlock | Irene | Shep | Elemental at the sphere's tier |
|----------------------|----------|-------|------|--------------------------------|
| nobody               | 40%      | 40%   | 20%  | —                              |
| Shep                 | 50%      | 50%   | —    | —                              |
| Sherlock             | —        | 67%   | 33%  | —                              |
| both cats            | —        | —     | 100% | —                              |
| all three            | —        | —     | —    | 100% (evenly, `random_species`) |

"Met" (`family_pets_present`) means hatched before this run (`player.family_cats_met`, which holds Shep too; the name is kept for older saves), walking with the hero, or waiting in a bound Soul Sphere. The rare companions never come from Summon Guardian, a Gate or a kill-summon: those call `random_species()` directly. For play-testing, `PQ_QA_MODE=1` with `PQ_FORCE_SPHERE=shep` (or `sherlock`, `irene`) makes the next sphere hatch that companion, and `PQ_FORCE_SPHERE_TIER=1`, `2` or `3` makes every sphere hatch at that tier's level (1, 25, 55). The QA hero (Titivillus) starts with one of each of the six. There's no weighting by element or floor — fire pets appear on F1 as readily as water pets. The `duck_of_doom` and family exclusions are enforced here (don't push them to call sites).

If a design future adds a sixth species, it defaults in to the random pool unless explicitly excluded. Common pattern: new "reward" species (hatched from a quirk / mystery / scripted event) should be excluded from `random_species` the same way Waddlekind is.

---

## 12. The six Soul Spheres (2026-10-18)

THE SPHERE DECIDES WHAT IS INSIDE, NEVER THE FLOOR. What each holds is data (`data/items/artifact.json`, the `sphere` block; read by `pet_system.spheres()` / `sphere_spec()`, by id, so an old save's pickled `soul_sphere` works):

| Sphere | id | Hatches | Floor chance by band (1-33 / 34-66 / 67-100) | Traders |
|---|---|---|---|---|
| Soul Sphere | `soul_sphere` | a newborn, level 1, stage 0 | 8% / 3% / 1% | Grindle, Mags |
| Greater Soul Sphere | `greater_soul_sphere` | at its first evolution, level 25, stage 1 | 0 / 4% / 2% | Grindle, Mags |
| Master Sphere | `master_sphere` | at its final evolution, level 55, stage 2 | 0 / 0 / 2% | Vesper (61+) |
| Hearth Sphere | `hearth_sphere` | always one of the family, level 1 | 0.8% / 0.3% / 0.1% | none |
| Greater Hearth Sphere | `greater_hearth_sphere` | always one of the family, level 25 | 0 / 0.4% / 0.2% | Vesper (61+) |
| Master Hearth Sphere | `master_hearth_sphere` | always one of the family, level 55 | 0 / 0 / 0.2% | Vesper (67+) |

- **Floor roll** (`dungeon.spawn_items` → `pet_system.sphere_for_floor`): ONE draw from the floor's stream against the six chances in turn, so at most one sphere a floor. When the room it rolls is already full (a small maze cell), it goes to the next room with a free floor tile, never lost. (A hidden treasure chamber no longer re-runs the loot pass, so it holds no sphere: its cache is coin, treasure, potions and scrolls.) Spheres carry no `peak_weight` / `floorSpawnWeight`, so they stay out of every random pool (chests, gifts, rewards) and thieves never take one.
- **Traders** (`data/traders.json`, `id` entries with `floors`): a sphere he has rolled is always on the shelf. Prices: `data/item_worth.json` `share_by_id` (Soul 2.0, Greater 3.5, Master 5.0, Hearth 3.0, Greater Hearth 5.0, Master Hearth 7.0 floors' share), so the price follows the tier. A trader buys an unbound sphere back like anything else; a bound one is never sold or given as payment (`items.withheld`).
- **Identity**: each looks the same identified or not (its art is the item; the unidentified name describes that look: "Iron-Caged Sphere", "Silver-Caged Sphere", "Crowned Silver Sphere", "Gold-Trimmed Iron Sphere", "Gold-Trimmed Silver Sphere", "Gold-Crowned Sphere"). Its kind is learned by identifying it or by throwing one. Never cursed (`can_be_cursed: false`, `buc_known: true`).
- **Art**: `assets/tiles/items/<id>.png`, 64 px, drawn by `tools/content/genart/briefs/spheres.json` (review sheet `SPHERES_ART.png`). Plain tiers go pale wisp → bright core → radiant crowned globe; the Hearth versions match their tier, gold-touched, with warm light.
- **Starting kits**: Ash Ketchum's four are plain Soul Spheres (`_start_soul_spheres`); the QA hero has one of each (`_start_spheres`).

```
spawn_items (by band) / a trader
    ↓
one of the six on the floor or in the pack
    ↓
player picks up → inventory
    ↓
player throws (press 't' + aim)
    ↓ (lands on target tile or an adjacent walkable tile)
┌───────────────────────────────┐
│ sphere.bound_pet is None?     │
├── YES → roll_sphere_species() │
│         Pet(species, x, y,     │
│             level=hatch_level) │
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

A bound sphere is always made from a plain `soul_sphere` whatever the pet hatched from (its art is the Soul Sphere's), **cyan-tinted** (`color=[80, 200, 255]`) on the map's old glyph colour. Its name reads `"Bound Soul Sphere (<pet_name>)"`. Lore reads: "A Soul Sphere humming with the bound spirit of <name>. Hurl it to summon it back to your side."

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

Dead pets are not rendered. Sketch pets (and a Dad with no song) with `turns_remaining <= 0` set `alive = False` and get pruned; Dad with his song goes when it ends.

---

## 15. Design notes

- **Pokémon pattern.** The 3-stage evolution + per-species single-target + AoE specials deliberately echoes a Pokémon starter. The 4 elemental species (electric/water/plant/fire) include the three classic Gen-1 starter types; Zappik is the Pikachu equivalent and the only standard species with a stage 0 lowercase glyph.
- **Reward asymmetry.** Fenrir, Dad, and Unicorn are **reward pets** acquired through specific gates (XYZZY T5 hero-special, the Unusual Soul Sphere, Unicorn-encounter chain 5). None of them level — they come at full power. Waddlekind is the fifth reward pet, costing 10,000 cursed turns.
- **Why L100 cap?** Pet stats scale to roughly match a mid-tier F100 monster. Beyond L100 the pet would overshoot even boss stat budgets, breaking the pet-as-helper design (pets are a *support* line, not a replacement for the player).
- **Why command cycle, not toggles?** Each pet gets ONE menu action (vs. per-command checkboxes). Cycle is one keypress to iterate `return → stay → wander`, matching the one-keypress feel of the rest of the pet menu.
- **Stronger starts come from stronger spheres (2026-10-18).** The late-pickup grant (floor x 50 XP) is gone: it was a floor multiplier. A player deep in the dungeon finds Greater and Master spheres there, or buys one, and those hatch grown. Brandon: "pets are a fun part of the game, want to make sure they do show up", so the floor chances run about 8% early and the traders carry spheres too.

---

## 16. Invariants (do not break)

1. **`DUCK_OF_DOOM_TURNS_REQUIRED = 10000` lives in `pet_system.py`.** Both the quirk timer in `main.py` and any future hero-special that references the threshold must import it from here.
2. **`random_species()` excludes `duck_of_doom`.** Waddlekind is the Duck quirk endpoint, not a random Soul Sphere outcome. If a new random spawner is written, use `random_pet_species` (the `game_combat.py` alias) and inherit the exclusion.
3. **No pet's starting level reads the floor.** A sphere's pet starts at `hatch_level(sphere)`; every other source names its own level. `tests/test_lore_not_floor.py::test_no_pet_hatch_reads_the_floor` holds this.
4. **Pet `_move_toward` consults `dungeon.pits` + `dungeon.traps`.** Pits are hard refuse (always); traps are soft avoid (pass 1 skip, pass 2 tolerate). Never collapse the two-pass structure — forgetting the goal because every direction is trapped is worse than stepping on an alarm.
5. **The "SketchedPet is temporary" invariant depends on `tick_duration` being called every pet turn.** The audit flagged this call site as the risk area — a lost tick means a permanent sketch pet.
6. **Dad is invincible.** `take_damage` returning 0 is load-bearing — Dad has to survive to the duration timeout.
7. **Unicorn sets `trap['revealed'] = True`** (not `detected`). Pre-v2.18 the wrong key was being written and the whole feature was a silent no-op. Keep the key name aligned with `_check_floor_trap` + `_try_disarm_trap` + renderer.
8. **L100 is the pet level cap.** `gain_xp` short-circuits at L100 and drops residual XP. Raising the cap means re-stat-curving `_calc_max_hp` + `_calc_damage`.
9. **One companion at a time** (§4.0). Every new way a pet joins calls `_companions_to_stasis()` before `self.pets.append`, unless it is a short-lived helper; `is_companion` is the one test of which is which. `tests/test_one_companion.py` holds it.

## The abandoned Emberpup: every run, earned (Dungeon Alive slice 8, 2026-11-12; winning-build plan 3.8, 2026-11-13)

Brandon: the one-in-N events happen every run, on a range of floors, but winning one takes "a pattern of behavior AND the right items (similar to unicorn)". The Emberpup (`src/emberpup_encounter.py`, `data/abandoned_emberpup.json`) waits on one floor of 3-8 every run (`chance_per_run` 1.0). He (Brandon's word; the data says "he" throughout) was mistreated and left on that rock by a hard master, and he has learned to shy from anyone bigger than he is. His trust thaws a step at a time:

- **Three feeds, with time between.** Feed him `visits_needed` (3) times, each at least `feed_gap_turns` (25) after the last; leaving his floor counts as waiting (`Game._change_level` calls `_emberpup_left`, which notes `away`). Each feed raises `pup._emberpup_feeds` (an old save's `_emberpup_visits` is read in its place) and has its own line (`fed`, three, each warmer: he flinches, then lingers, then comes close). Bumped or fed before the gap, he is still eating the treat you provided, and growls and backs away as you approach (`too_soon`, a list: one line per feed so far, read by `too_soon_line`; after the second feed he growls but no longer runs): the screen shows only that, nothing counts and no turn passes. The choices screen says where his trust stands (`waiting`, by `stage`).
- **The right item.** Only the **Bloomleaf Cloak** turns his rain (`shelter_choices`; `src/emberpup_encounter.py` (BloomleafMixin)). Any other cloak or shield no longer does (`not_leaves`: "A cloak of leaves would turn this rain"), nor a leaf cloak still worn (`take_off`). Left over his rock, it is his (`pup._emberpup_cloak`): his map picture becomes `npc_abandoned_emberpup_sheltered`. `emberpup_encounter.sheltered(pup)` is the one test (the flag AND the leaf cloak): a Dungeon Alive save (2026-11-12), whose pup any cloak or shield sheltered with no record of which, reads as unsheltered, so that pup needs the leaf cloak too and never adopts as the cloaked Emberpup without it (bug bash WB-C03).
- **I choose you.** It asks the animal quiz (tier 2, two right) only with three feeds, fed since the last try, and sheltered. Otherwise it refuses with `refused`, `refused_trust`, `refused_hungry` or `refused_cold`, so the player learns what is missing.
- **He keeps the cloak.** The adopted pup is a `Pet` with `bloomleaf = True`: he wears the cloak at every stage (`Pet.sprite_id` gives `emberpup_cloaked`, `flamescale_cloaked`, `infernodrake_cloaked`, drawn by `tools/content/genart/bloomleaf.py` over the approved art, which is never overwritten), his evolution line says the cloak still hangs round his shoulders, his card says he wears it, and his line's weakness to water is gone for him alone (`Pet.weak_to`).
- **The fire line's weakness.** A fire-line pet takes blows of `cold` (the game's water: the water line's own jets land as cold) twice as hard (`_SPECIES['fire']['weak_to']`, `pet_system.harm_taken`, applied in the monsters' swipes at pets; the log adds "The cold bites deep."). Soul Sphere fire pets keep it; the cloaked Emberpup does not.
- **Karma** is unchanged: feeding moves none, attacking costs -1.

The Black Knight (`data/black_knight.json`) also stands every run now, on one floor of 15-19. Tests: `tests/test_abandoned_emberpup.py`, `tests/test_black_knight.py`.

## The Mooble: a dance in the deep mines (RARE_PETS_PLAN_2026_11_14 section 2)

Brandon: "add two more rare pets... through little quests like emberpup and unicorn", with "a small rhythm game to 'dance' with the moogle", and then "kids have to win the rhythm game... offer to let the player practice the dance before a dance off". An homage, never a copy: the name, art, lines and sounds are ours (no Square Enix word or tune). Code: `src/mooble_encounter.py` (`MoobleMixin`: his floor, cave, screen, adoption, his gifts as a pet, QA), `src/game_mooble_dance.py` (`MoobleDanceMixin`: the dance screen, which the Stray Kids' dance-off also uses, owner `stray_kids`: [monsters.md](monsters.md)), `src/rhythm.py` (pure scoring). Every word and number: `data/mooble.json`.

- **Where.** Every run (`chance_per_run` 1.0), one floor of 31-45 rolled at run start on the run's own generator (`new_run_state`; never a gate boss's floor, a planned mini-boss's only when nothing else is left), kept clear of the Road's scenes (`_secret_floors`). On first arrival he is set down in a quiet **side cave**: a 3x3 chamber carved behind a room's wall and left open by one tile (`_mooble_carve_cave`, dungeon `_carve_sealed_shrine`'s carving), at its back; with no rock to carve, in a quiet room. A Starnut grows in his cave (`starnuts_in_cave`), so the tart can always be baked.
- **Meet.** His story, from his ledge (`npc_mooble`). He misses the miners' **Starnut Tarts** and says what goes in one; the hero learns the dish (`player.dishes_learned`: the cook menu shows it under Building Toward; food_system.md §5.5).
- **The tart.** Only a Starnut Tart brings him down (choice 3; `no_tart`, `on_ledge` and `refused_ledge` say what is missing). It is eaten; his picture becomes `mooble`, off the ledge.
- **Three dances, time between.** Each visit: **Practise** (1: free, no stakes, no turn, as often as wanted, Esc any time; D from its result goes to the dance-off) and the **Dance-off** (2), which must be WON. A win counts (`_mooble_dances`) and ends the visit with its own line ("He bobs, unsure." / "His bobble glows." / "He spins and laughs." and asks to come along); a loss ends it with "Not yet...pom." Either way the next try waits `gap_turns` (30); leaving his floor counts as waiting (`_mooble_left`). Bumped too soon: his choices show `too_soon` (one line per dance won); the dance-off (and a fumbled ask) waits, but **practice is always on offer** (Brandon, 2026-11-14: "an option to practice as many times as you want before you try it"). No turn passes. After the third win there is no wait to answer him.
- **The rhythm game** (`rhythm.py`, `game_mooble_dance.py`; `STATE_MOOBLE_DANCE`). Space starts it: a count-in of four beats ("5, 6, 7, 8!"), his CALL (two bars: his pose for each step, `mooble_dance_<dir>`, its arrow lit, a chime), then the RESPONSE (the same two bars): echo the phrase on the arrow keys (or the number pad). Every arrow lights as its beat comes (it reads with the sound off), his bobble pulses on the beat, `sound_system` plays the beat (`dance_beat`, `dance_bar`, `dance_step_*`), and the soundtrack is held while a dance plays (`music.hold` / `release`). Timing is real time from pygame's clock judged against the beat SCHEDULE (`rhythm.timeline`), so a slow frame never steals a beat. Each step: **Perfect** within ±50 ms, **Good** within ±150 ms, else **Miss** (early, late, wrong arrow, no key); a key that belongs to no step is a stray and counts as a miss. Win: 75% of the steps hit, at most 2 misses. Visits: 4 steps at 80 beats a minute, 6 at 95, 8 at 110 (`dance.visits`, written in the data). No automatic slowing.
- **I choose you.** After the third win: the animal quiz, tier 2, two right (refusals by dances won, `refused_dances`). A fumbled ask waits the gap. Pass: he joins (`_companions_to_stasis` first: one companion), at **level 20** whatever the floor (`pet_level`: years of dancing; LORE, NOT FLOOR), with his own naming popup.
- **The companion** (`pet.species`): **small health and weak bites** (`health_mult` 0.6, `bite_mult` 0.5 on the growth table); **a support line** (`support`: on `return` he keeps within two tiles of the hero and bites only what comes beside him); **Bobble Glow** (`mana_gift`, `Pet.mana_gift`, each pet turn): +1 MP every 5 / 4 / 3 turns by stage while within 3 tiles and the hero's mana is not full, said once a floor; **Dance of the Dark** (his special from stage 0, cooldown 300; `effect: dance_of_the_dark`, `rhythm: true`) is **danced** (Brandon, 2026-11-14: "that should trigger a dance rhythm game as well, where your success determines how powerful it is (no practice, just a count in)"): using it (Shift+P, S) opens the dance screen at once (`_mooble_special_dance`): a count-in ("5, 6, 7, 8!"), then his phrase for his stage (4 steps at 90, 6 at 100, 8 at 110; `pet.special_dance.phrases`) with no call, danced as its arrows light. The cooldown is spent when it starts; no monster acts while it is danced (it is his turn, like a quiz); Enter afterwards passes the turn. The score (`rhythm.score`: steps hit over steps due, a Perfect worth 1.25, a stray key -0.5) picks a band (`mooble_encounter.dance_band`, `pet.special_dance.bands`): **A Flop** (2 tiles, 1 turn, the nearest one: the bobble only flickers), **Shaky** (3, 2, two), **Good** (4, 3, four), **Great** (5, 3, six), **Dazzling** (6, 4, every one; it takes Perfects). Every foe within the band's reach with a clear view of him that can be stunned stands staring for its turns, the nearest first, up to its count (`_mooble_dance_of_the_dark`, through `Monster.hold`), with the Stray Kids' watch rule: never a named foe, the mindless, the blind or what cannot be stunned, and each of those in sight is told why (`why_unmoved`). The band's line says how well it went. A **Mooble Troupe-Leader**'s dance, danced Good or better (the band's `lift`), also lifts one hindrance from the hero (a hold first, then the longest left). His card says all three (`_pet_gift_lines`).
- **Saves.** `game._mooble` (`floor`, `spawned`, `outcome`, `seed`, `last_turn`, `away`, `choose_failed`, `dancing`); his own state on the creature (`_mooble_met`, `_mooble_tart`, `_mooble_dances`, `_mooble_cave`). A save while his dance is on screen opens it again on load, at the start of its phrase (`dancing`, `_mooble_after_load` from `Game.update`); a dance-off left open is still to be danced. A save from before him rolls him a floor still ahead of the hero, or none when 31-45 are all behind.
- **Art.** P3's ids: `npc_mooble` (on his ledge), `mooble`, `mooble_dancer`, `mooble_troupe_leader`, `mooble_dance_left/right/up/down`; until each file is installed, `art_standin` (`will_o_wisp`) shows in its place, never a letter.
- **QA (Titivillus, Shift+D).** Sets him down in a cave beside this room (his floor this run becomes this floor) and the hero beside him (`_qa_beside_mooble`), with a Starnut and a Starnut Tart in the pack; again with him here: another tart, and no wait before the next dance.
- **Hint.** One story-led Recall Lore line (tier 3), never the steps.

`rhythm.py` knows nothing of the Mooble (a phrase, a timeline with or without a call, `judge`, `passed`, `score`, `band`), and the dance screen reads everything it shows from the dance it was given (`_mooble_dance_spec`), so another dance-off can reuse both.

Tests: `tests/test_mooble.py` (floors, words, the state machine, practice always on offer, dance-off, too soon, refusals, the quiz, adoption and one companion, cook to carry, the pet's mana, the danced special's bands (pure), its watch rule, reach and lift, the special danced with real keys at a high and a low score, saves mid-quest and mid-dance, old saves, QA, a real-keys journey), `tests/test_rhythm.py` (the scoring, a dance with no call, score and band). The rhythm's FEEL needs Brandon's hands.

## The Bococho: a race in the Underway, and riding (RARE_PETS_PLAN 3, 2026-11-14)

Brandon: "add two more rare pets... through little quests like emberpup and unicorn... something about racing for the chocobo", and on riding: "We'd need to have riding code, but I like the idea." The Bococho is a homage, never a copy: our own golden riding bird, her own call ("whirrup"), no Square Enix names, words or tunes. Every word and number is in `data/bococho.json`.

**The camp** (`src/bococho_encounter.py`, `BocochoMixin`). Every run (`chance_per_run` 1.0), on one floor of 51-65 rolled off the shared stream (`new_run_state`, the Emberpup's way; never a gate boss's floor, `candidate_floors`: 60 is Fafnir's hand-built hoard), the camp is set up on first arrival in the biggest ordinary room that is not the hero's (`_maybe_spawn_bococho`, `place_camp`): three tether posts against its walls (`race_tether_post`), the betting board (`race_betting_board`), Gilt Varro (he) by the board, his two birds at the first two posts and the young Bococho (she) at the third. All are allied, sessile creatures carrying `_bococho_role` ('young', 'varro', 'bird'); bumping one opens its screen (`STATE_BOCOCHO`) or says a line (the birds: harmless while tethered). The camp's floor is a secret floor for the Road and the traders (`_secret_floors`, `_trader_plan`).

- **Meet her:** she shies (`story`, then `waiting` by trust).
- **Sunroot, twice** (`feeds_needed`), at least `feed_gap_turns` apart; leaving the floor counts as waiting (`_bococho_left` clears `waits`). Back too soon: `too_soon`, one line per feed so far, and nothing counts and no turn passes. Only Sunroot will do (`not_sunroot`, `no_food`; a forage find from floor 40, `data/items/ingredient.json`). Each feed is a turn with its own line (`fed`).
- **Varro's challenge** (his screen, 1): refused until she trusts the hero (`challenge_untrusted`), too soon after a lost race (`challenge_soon`), or without the fee (`challenge_poor`). The fee is `race_fee_share` of a floor's gold on the camp's floor (`economy.share`), paid to him (`_pay_gold`: coin, then treasure), every challenge. Then the trip to the Underway Run.
- **Strike him** (3): there is no race now. He turns hostile (a real fight for his floor, a man of the `mortals` family whose numbers are in the data; he never starts one), and she tears her frayed rope and bolts (`strike_bolts`): she will not trust a hero who fights in front of her (decided 2026-11-14; the brief's "won't trust a hero who kills in front of her"). Killing him moves no karma (he is nobody's innocent); the deed `slew.gilt_varro` is noted and his birds pull free and run (`_bococho_monster_died`, from the kill handler).
- **Win the race:** back at the camp Varro storms off, the tethers are cut and his birds run free (`_bococho_after_race`). She stays: **"I choose you!"** asks the animal quiz (`quiz`: tier 3, two right), as for the Emberpup; refusals say what is missing (`refused`, `refused_trust`, `refused_tethered`, `refused_soon`). A failed try waits the gap. Pass, and she joins (`_bc_adopt`): `Pet('bococho', level=pet.start_level)` after `_companions_to_stasis` (the one-companion rule), then the naming popup in her own words (`name_title`...).
- **Lose:** back at the camp, Varro gloats (`lost_back`) and the next challenge waits the gap, at the fee again.

**The race** (`src/race.py` pure scoring; `src/game_race.py`, `RaceMixin`; the floor `src/underway_run.py`, [world](world.md) "The Underway Run"). Five legs; each is ONE maths chain (the quiz engine's chain mode) at the hero's own maths tier, as in combat (the weapon in his hand), capped at `max_chain`. A leg runs `base_per_leg` + chain x `stride[tier]` lengths (a harder sum is worth more ground: the stride follows a sum's time, so no weapon is a handicap or a trick). Before each leg (`STATE_RACE`): **Sprint** (x1.5, costs wind, and the NEXT leg runs winded, x0.6; a sprint with too little wind is a tired one) or **Pace** (wind back). The home straight gets up to `final_kick` more from the wind left. On leg 3 Varro has salted the inside lane with caltrops (x0.35); his taunt before it is the tell, and the outside lane (3 on that leg) runs clean but a little longer (x0.85). Brassbeak runs `varro_pace` by leg with `varro_luck` from the race's own seed. After each leg the birds move round the oval on the map, with commentary (`events`, `chain`, `standing`); the finish has its photo. Esc between legs asks to leave: leaving before the finish, by any way, gives Varro the race. A save mid-race loads at the leg not yet run (`_race_resume`, from `Game.update`). Tuned by a simulator of kids (answer times from `tools/balance/difficulty_sim.py`): a mastery-level kid who paces well wins 81-90% at tiers 2-4, the same kid sprinting every leg on the inside 3-5%, a good kid who paces well about 40-46%, a sloppy kid almost never.

**The pet** (`pet_system._SPECIES['bococho']`, loaded from the data by `_species_from_data`; `quest_only`, so never a sphere's hatch, `random_species`). Bococho Chick -> Bococho -> Bococho Champion, she (`pronoun`), crushing kicks a quarter harder than the growth table's bite (`bite_mult` 1.25, `Pet._calc_damage`). She joins at level 25 (`pet.start_level`, a grown runner: LORE NOT FLOOR); the chick stage is her line's first and is never hatched. **Charge** (stage 2, the champion's): a dash in a straight line (range 6, a leap) and a two-footed kick, 2x, a tile of knockback, 50% stun 2 turns, cooldown 300. Her card shows her saddlebags and riding (`_pet_bococho_lines`) and an M action. Her pictures, Varro's and the camp's are the art run's (`tools/content/genart/install_rare_pets.py`, 2026-11-14); a picture ever missing is stood in for by one that is there (`sprites.fallback`, read by `Pet.sprite_id` and `bococho_encounter.sprite`), never a letter. The rider's seat is the art run's measure, (33, 23) in the 64 px frame (`riding.seat`).

**Saddlebags.** While she is out with the hero, `Player.saddlebag_lb` = `pet.saddlebags_lb` (20) and `Player.get_carry_limit` adds it, so Heavy, Burdened and Overloaded all move up ([items](items.md) 9). Kept by `Game._sync_saddlebags` every turn, on load and when she joins or is stored.

**Riding** (`src/riding.py` the rules, `src/game_riding.py` `RidingMixin` the game's side; `data/bococho.json` `riding`).
- **Getting on:** Shift+R on the map, or M on her card in the pet menu: she must be beside the hero, grown (`min_stage` 1: not the chick), no hostile in sight, the hero not Overloaded, not in a pit, not in a state that unseats. One turn. The hero's `riding` flag is on the Player (class default False: an old save loads on foot); the mount is the pet with `ridden`. A save while mounted loads mounted.
- **The step:** each step covers two tiles (`_riding_second_step`, from `_do_move` after the first step's FOV): the second only if the first was clean (no trap, no hazard, no foe come into view, not ice) and the second is open ground nobody stands on. Both tiles are stepped on as tiles are: traps and hazards (`_check_floor_trap`), dug pits, what lies there. One move is one turn for the monsters (`_advance_turn` once): riding is speed over the ground, never free turns. She takes no turn of her own under him (`_do_pet_turns`), stands on his tile and is not drawn apart: the map draws her saddled picture (`bococho_saddled`, `bococho_champion_saddled`) with the hero's own sprite on the seat (`riding.seat`, `rider_scale`; `BocochoRenderMixin._draw_rider`). The sidebar's Effects list shows "Riding".
- **Set down at once, with a line** (`set_down`): a hostile in view (`foe`, each turn and between the two tiles), a blow (`blow`: `_blows_on_hero`; a thief's touch is a blow), a trap or hazard (`trap`, `hazard`: `_check_floor_trap`, `_hazard_hit_hero`), any quiz starting (`quiz`: the quiz engine's `start_hook`, so an attack, a spell, a wand or any quiz action), the stairs and every other way off a floor (`stairs`; she follows as every companion does), a status that unseats (`unseat_statuses`: paralysed, asleep, stunned, confused), being Overloaded, her being stored (`stored`: Recall, `_companions_to_stasis`), hurt (`hurt`) or sent on her Charge (`special`), and the hero's death (quietly).
- **Noise:** a galloping bird is loud: `senses.step_radius` adds `step_noise` (3 tiles) and `sleepers.factor('step')` multiplies by `sleeper_step_factor` (2).

QA (Titivillus, Shift+G): the camp set up in the hero's room, with two Sunroots; pressed again, her trust (the two feeds counted) and two more; once more, she joins at once, the race skipped, so riding can be tried in a minute. Recall Lore has one story-led hint (`data/hints.json`, never the steps). Help: the key map's Movement column (Shift+R) and the Gear and Load page's last section. Tests: `tests/test_race.py` (the scoring), `tests/test_bococho.py` (the data, the camp, Varro, the side floor, the pet, saddlebags, every set-down, noise, old saves, the Effects chip), `tests/test_bococho_journey.py` (the whole way through the real keys). The race's pace and riding's feel are Brandon's play-test.
