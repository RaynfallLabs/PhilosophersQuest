# World: dungeon, levels, terrain, bones

**Scope.** How a floor comes into existence. Procedural BSP room-and-corridor generation (`src/dungeon.py`), the hand-crafted boss floors (`src/boss_levels.py`), floor-to-floor state (`src/level_manager.py`), terrain features (water, lava, ice, altars, graves, thrones, fountains), the field-of-view pass (`src/fov.py`), traps and player-dug pits, and the bones file persistence that re-animates dead player ghosts across runs (`src/bones.py`). What `world.md` does **not** cover: monster behavior and spawn pools (see [monsters](monsters.md)), scripted mystery altars and seal-demon quest wiring beyond the raw spawn (see [quests_mysteries](quests_mysteries.md)), and the karma penalty tied to bones (see [karma_prayer](karma_prayer.md)).

**File map.**

```
src/dungeon.py            # BSP generation, mazes, terrain, items, special rooms, traps
src/boss_levels.py        # Hand-crafted maps for L20/40/60/80/100 and L999 Cow Level
src/level_manager.py      # Floor save/load, mini-boss planning, seal-demon forcing, bones hookup
src/bones.py              # Persistent death artifacts across runs
src/fov.py                # Recursive shadowcasting FOV (octant-based)
```

---

## 1. Floor taxonomy

The world is 100 descending floors plus one hidden floor (L999, the Cow Level). Floors fall into three kinds, each with different generators:

| Kind       | Floors                              | Generator                              |
|------------|-------------------------------------|----------------------------------------|
| Boss       | 20, 40, 60, 80, 100                 | `boss_levels.generate_boss_level`       |
| Maze       | 10, 30, 50, 70, 90                  | `dungeon._generate_maze_dungeon`        |
| Open (BSP) | all others                          | `dungeon.generate_dungeon`              |
| Secret     | 999 (Cow Level)                     | `boss_levels._level_999_moo_moo_farm`   |

The boss set lives in **a single source of truth**: `src/dungeon.py` exports `_BOSS_LEVELS = {20, 40, 60, 80, 100}`, and `src/level_manager.py` imports it (`from dungeon import _BOSS_LEVELS`) so the mini-boss roller and the boss-floor dispatcher never disagree about which floors reject random spawn (v2.18 consolidation — before the import, each file carried its own copy and a mini-boss plan could silently target a boss floor and vanish).

`generate_dungeon()` branches on the floor number:

```python
is_boss = level in _BOSS_LEVELS
if level % 10 == 0 and not is_boss:
    return _generate_maze_dungeon(...)
# otherwise BSP open floor
```

Note the `and not is_boss` guard: without it, the four boss floors from `{20, 40, 60, 80}` would be caught by `level % 10 == 0` and get maze-generated. The boss-level dispatcher in `level_manager.generate()` runs *before* `generate_dungeon`, so in practice the guard is defence in depth — but the two-check pattern (`BOSS_LEVELS` short-circuits in `level_manager`, `_BOSS_LEVELS` guards inside `generate_dungeon`) is load-bearing: never remove either half.

Boss floors use `BOSS_LEVELS` (uppercase, exported from `boss_levels.py`) at the dispatcher layer and `_BOSS_LEVELS` (underscore, exported from `dungeon.py`) inside the generation + mini-boss code. Both sets are the same `{20, 40, 60, 80, 100}`. The uppercase/underscore split marks "public API constant" vs "internal gate for same-file logic".

---

## 2. Floor generation pipeline (BSP open floors)

`generate_dungeon(width=80, height=50, level)` runs these numbered passes in order. The numbering in code comments is **the contract** — every pass can assume everything before it has run.

### 2.1 BSP partition
A binary-space-partition tree splits the 80×50 interior into leaves. Tuning:

```python
_BSP_MIN_LEAF   = 8       # stop splitting when a region shrinks below this
_ROOM_PAD       = 0       # rooms fill their leaf (dense packing)
_ROOM_MIN_INNER = 3       # minimum interior tile dim
_ROOM_MAX_INNER = 18      # 'great hall' upper bound
```

The split direction prefers the longer axis (hard rule above 1.25× aspect; coin flip inside that band). `target = min(7 + level, 20)` leaves are requested; the pass loops up to `target * 6` times doing random splits. Room count was raised 16 → 20 on 2026-05-19 as part of the density bump.

### 2.2 Room placement
Every leaf gets a `Room(x, y, w, h)`. Interior tiles become `FLOOR`; the outer 1-tile ring stays `WALL`. Rooms carry `inner_tiles()` and `wall_tiles()` generators.

### 2.3 Corridor carving — tree edges

`_connect_bsp(root, tiles, rng, corridor_width)` recursively connects every pair of BSP siblings. Each pair picks the nearest edge point on each room (not the center — short corridors feel better than always-cross-the-room ones), then carves an L-corridor with a 50/50 flip of which axis to run first. Long corridors (`manhattan > 20`) get a small 3×3 alcove at the bend.

Corridor width is a **function of depth**:

```python
def _corridor_width_for_level(level: int) -> int:
    return 2 if level >= 76 else 1
```

The 2-tile corridor exists so 2×2 cosmic-scale bosses — Tiamat, Surtur, Ymir's Last Spawn, Hrungnir's Ghost — can pathfind between rooms instead of getting stuck at their spawn anchor. Monster footprint validation (`_footprint_fits`) refuses to anchor a multi-tile monster where any of its tiles would land on wall.

### 2.4 Extra connections (loops)

`_add_extra_connections` sorts every non-adjacent room pair by Manhattan distance and adds up to `min(len(rooms) // 3, 3)` extra corridors between pairs with `5 <= dist <= 50`. The upper bound was raised 30 → 50 (noted in a code comment) so that long-diagonal room pairs on larger maps actually get a loop-back corridor instead of being topologically isolated from everything but the single BSP tree edge.

### 2.5 Doors — regular

`_place_doors` scans every room-wall tile. If a wall tile is `FLOOR` (meaning a corridor carved through), **and** the orthogonal neighbors form a valid 1-tile-wide passage (floor on two opposite sides, wall on the other two), the tile has a 70% chance to become `DOOR`. Adjacent doors are refused so you never get stacked doors.

### 2.6 Doors — secret

`_place_secret_doors` places `max(2, 2 + level // 4)` `SECRET_DOOR` tiles in walls that sit between two opposing `FLOOR` tiles — a shortcut gap through what would otherwise be a wall. Secret doors render as walls until the player bumps them or searches successfully.

### 2.7 Hidden chambers

`_place_hidden_chambers` tries to carve 0-2 small rooms off existing corridors/rooms via a `SECRET_DOOR`. Candidate sizes are 5×7, 7×5, 6×6 (interior); a floor-adjacent wall tile becomes the secret door and the chamber bounding box is checked to be entirely `WALL` before carving. Each chamber is classified 60% `treasure` (cache) / 40% `lair` (themed monster den). Lair themes scale with depth:

| Floor band | Themes                                              |
|------------|-----------------------------------------------------|
| 1-8        | rat_nest, spider_den, bat_cave                      |
| 9-18       | goblin_camp, kobold_den, orc_hideout                |
| 19-35      | troll_cave, bandit_hideout, undead_crypt            |
| 36-60      | demon_shrine, yuan_ti_lair, vampire_crypt           |
| 61+        | dragon_hoard, lich_sanctum, chaos_shrine            |

Chambers are returned as `{'room': Room, 'type': str, 'theme': str}` dicts and populated separately by `level_manager._populate_hidden_chambers` (see §4.5).

### 2.8 Stairs
`rooms[0].center` becomes `STAIRS_UP`; `rooms[-1].center` becomes `STAIRS_DOWN`. L100 has no `STAIRS_DOWN` (Philosopher's Stone goal, see §3.5).

### 2.9 Altars (one per 15 levels)
On `level % 15 == 1` (i.e. L1, L16, L31, L46, L61, L76, L91) one random inner tile in a non-start room becomes `ALTAR`.

### 2.10 Terrain pass — see §3.
### 2.11 Vault placement — see §3.4.
### 2.12 Dark rooms — see §5.2.
### 2.13 Atmosphere messages — flavor lines seeded by what's on the floor.

---

## 3. Terrain

Terrain tiles live inside the `_apply_terrain` pass. Each risky pass **snapshots** the tile grid, applies, then runs a BFS reachability check between `STAIRS_UP` and `STAIRS_DOWN`. If the pass severs the map, the snapshot is restored. This is a v2.18 hardening — pre-fix, water/lava could cut the exit off entirely.

### 3.1 Fountains (walkable)
20% chance per floor; one random inner tile in a non-start room becomes `FOUNTAIN`. Fountains are walkable, so they can't sever reachability (no snapshot).

### 3.2 Water pools — L10+ and NOT a maze
15% chance per non-maze floor at L10+. A random non-start room floods: all edge tiles plus ~30% of center tiles become `WATER`. Water blocks movement unless the player has `water_walking`; it's transparent to FOV. The `not dungeon.is_maze` gate is v2.18 — before the fix, mazes could flood and sever themselves (same reason the lava rule carries the maze guard; v2.18 unified the behavior).

### 3.3 Lava rivers — L30+ and NOT a maze
20% chance per non-maze floor at L30+. An anchor is picked from corridor tiles (floors not inside any room), then a river 1-2 wide, up to 16 tiles long, in a random axis, is painted as `LAVA`. Lava is transparent, impassable without `fire_resist`, and glows. Snapshot + reachability check applies — if the river seals the stairs-down, roll back.

### 3.4 Ice rooms — L40+ (any floor), excludes stairs-down room
10% chance at L40+. Picks a non-start room, **excluding the room that contains `STAIRS_DOWN`** (v2.18 fix — before this guard, ice could cover the exit and force a slippery landing on the stairs). Every floor tile in the chosen room becomes `ICE`. Ice is walkable but every step has a chance to slide the player one tile in a random direction. BFS verify runs even though pure `ICE` currently stays reachable (defence in depth for future interactions).

### 3.5 Vaults
20% chance per floor if `len(rooms) >= 6`. A 4×4 wall-only region (2×2 interior) is picked such that at least one face has a `FLOOR` neighbor; one such tile becomes `DOOR` and the interior gets carved out. The vault is stored on `dungeon.vault = {'room': Room, 'door': (x, y)}`.

Vault gold is **capped at 2000 total** (v2.18). The spawn pass rolls `rng.randint(level*5, level*15)` per inner tile — at F100 across the 2×2 interior that's up to ~6000 raw. If the raw total overshoots the cap, amounts are scaled down proportionally so individual tiles still get something, and the cap sits where "nice find" ends and "run-defining windfall" begins.

### 3.6 Stone statues
There is no dedicated statue pass — "stone statues" in the audit refers to the WALL pillars added inside hand-crafted boss rooms (`_level_40_temple`, `_level_60_lair`, `_level_80_hall`, `_level_100_abyss`) as line-of-sight blockers against Medusa's gaze and tactical cover against swarm bosses. See §6.

### 3.7 Reachability check (v2.18)
`_bfs_reaches(tiles, w, h, start, goal)` runs 4-neighbor BFS where the passable set is `(FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR, FOUNTAIN, GRAVE, THRONE, ICE)`. Doors and secret doors count as reachable because the player bumps through them. `WATER` and `LAVA` are the two tile types that block without an item (water-walking / fire-resist). The post-terrain check guarantees the floor stays completable.

### 3.8 Fountains, graves, thrones (interactive tiles)
`FOUNTAIN`, `GRAVE`, `THRONE`, `ALTAR` are all walkable and transparent. They're placed either by the generic altar/fountain passes above, or by special-room spawns (§4.4 — `graveyard` paints `GRAVE` tiles, `throne_room` paints a single `THRONE`), or by scripted quest hooks (see §7 and [quests_mysteries](quests_mysteries.md)).

---

## 4. Monster + item spawn (level_manager wiring)

After `generate_dungeon` returns a `Dungeon`, `LevelManager.generate(level_num)` runs the post-generation population passes.

### 4.1 Baseline monsters
```python
density = min(0.50 + level_num / 130, 0.95)
monsters = populate_floor(dungeon.rooms, level_num, dungeon, occupancy=density)
```
`populate_floor` rolls EVERY non-start room independently for a baseline monster. Density scales 0.50 at L1 → 0.95 at L75+. The per-room-roll pattern (vs. a global N-count scatter) is deliberate — it fixes the "all monsters in one corner" lumping bug by spreading the baseline across the floor, and packs / dens / zoos then cluster intentionally on top.

### 4.2 Items
`spawn_items(dungeon.rooms, level_num, dungeon)` places gear, magic items, ammo, food, potions, Soul Spheres, mystery altars, merchants, and special-room contents. The Soul Sphere spawn is a 5%-per-floor independent roll; it drops as an `Artifact` ID `soul_sphere` and does the throw-and-hatch dance (see [pets.md](pets.md) §4).

### 4.3 Monster-den extras
Monster-den special rooms (`special_rooms[(cx, cy)] == 'monster_den'`) get 3-5 extra monsters via `spawn_monsters([den_room, den_room], ...)`. The `spawn_monsters` helper **skips its first room** (the start-room convention). Passing the same room twice is the idiom that gets around that — the target room is the "second" one and gets populated. Same convention is used by `_populate_hidden_chambers` (§4.5). If `spawn_monsters` ever loses the skip-first convention, BOTH call sites break — this invariant is called out in a comment in `level_manager._spawn_monster_den_extras`.

### 4.4 Special rooms
`spawn_items` picks up to 2 special rooms (first roll 40%, second roll 25%) and tags them in `dungeon.special_rooms[(cx, cy)] = type`. Types are level-gated:

| Type         | Min floor | Contents                                                 |
|--------------|-----------|----------------------------------------------------------|
| treasury     | 1         | 2 chests + gold pile (`level*3 .. level*8`)              |
| library      | 1         | 3 scrolls + 50% spellbook                                |
| shrine       | 1         | 1 `ALTAR` tile                                           |
| monster_den  | 1         | +3-5 extras (via level_manager)                          |
| zoo          | 5         | Gold piles on ~70% of inner tiles                        |
| beehive      | 8         | Food on ~30% of tiles                                    |
| graveyard    | 10        | `GRAVE` on ~20% of tiles + 1-2 skeleton corpses          |
| barracks     | 12        | 2-3 weapon/armor items                                   |
| swamp        | 15        | `WATER` on ~40% of inner tiles + scattered food          |
| throne_room  | 18        | 1 `THRONE` tile + 1 chest                                |

### 4.5 Hidden chambers (populate)
`_populate_hidden_chambers` reads `dungeon.hidden_chambers` (built in §2.7). Treasure caches get 3-5 bonus items. Lair chambers get 3-6 themed monsters where theme is matched by keyword against monster names (`rat_nest` → `rat`/`rodent`, `undead_crypt` → `skeleton`/`zombie`/`ghoul`/`ghost`/`wraith`/`vampire`/`lich`/…). If no themed monster is level-appropriate, level-appropriate fallback monsters spawn — chambers never come up empty.

### 4.6 Mini-boss planning
`LevelManager._roll_planned_mini_bosses()` runs **once at run start** and pre-rolls which mini-bosses appear and on which floors. The bands are hard-coded:

```python
_MINI_BOSS_BANDS = [(1, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
_MINI_BOSS_PRIMARY_CHANCE   = 0.90
_MINI_BOSS_SECONDARY_CHANCE = 0.30
```

Each band gets a primary slot (90%) and secondary slot (30%). Candidates inside a band are every monster with `is_mini_boss=true`, `peak_floor` inside the band, `spawn_chance > 0`, and `id` NOT starting with `seal_demon` (seal demons use the forced path, §4.7). Each slot picks a candidate weighted by `spawn_chance`. Placement defaults to the chosen mini-boss's `peak_floor`.

**Boss-floor collision skip (v2.18).** If `peak_floor` lands on `_BOSS_LEVELS`, the primary target shifts to `peak_floor - 1`. The secondary slot walks forward (`target += 1`) past both already-planned floors AND boss floors (`while target in planned or target in _BOSS_LEVELS`), capped at the band's upper bound. Without this guard, a mini-boss planned for L20/40/60/80/100 would be silently discarded — `generate_boss_level` doesn't check the plan.

Expected mini-bosses per 100-floor run: 5 × (0.90 + 0.30) = **6.0**, range 4-8.

### 4.7 Seal demons (forced spawn)
```python
_SEAL_DEMON_LEVELS = {
    83: 'seal_demon_wrath',
    85: 'seal_demon_pestilence',
    87: 'seal_demon_famine',
    89: 'seal_demon_war',
    91: 'seal_demon_death',
    93: 'seal_demon_earthquake',
    97: 'seal_demon_silence',
}
```

Each of the seven seal demons is force-spawned on its designated floor. The Abaddon quest gates descent past L99 on all seven being slain. Seal demons compete with nothing from the random mini-boss pool (the pool explicitly excludes any id starting with `seal_demon`), so the forced spawn is always honored and the player's mini-boss luck doesn't eat the quest.

### 4.8 Bones ghost
Last, `load_bones(level_num)` checks for a bones file (50% gate — but checks file existence FIRST so unoccupied floors don't burn the roll). If a bones file is found and the roll passes, `spawn_ghost(bones, dungeon, monsters, items)` is called. The ghost placement **checks monster occupancy** (v2.18 — pre-fix it could co-locate with a mini-boss or seal demon placed earlier the same turn). Cursed gear is distributed around the ghost. See §8.

---

## 5. Field of view + dark rooms

### 5.1 FOV (`src/fov.py`)
Recursive shadowcasting over the eight octants. `calculate_fov(dungeon, px, py, radius)` returns the set of visible `(x, y)` tiles. The algorithm trusts `dungeon.is_opaque(x, y)` for blocker queries, which treats `WALL`, `DOOR`, and `SECRET_DOOR` as opaque. All other tiles (including `WATER`, `LAVA`, `FOUNTAIN`, `GRAVE`, `THRONE`, `ICE`) are transparent — you can see across lava and water, you just can't walk through them.

Sight radius: `Player.get_sight_radius()` returns `max(3, PER // 2)` baseline, with `+4` for `dark_vision` status or `passive_dark_vision` accessory (Hand of Glory), `+2` for `truesight`, and additive `equipped_light_aura` from wielded weapons (Prometheus Torch). Blindfold head slot forces radius 0; `blinded` status forces radius 1.

### 5.2 Dark rooms
Any non-start, non-boss BSP room at L5+ can be marked dark. Chance scales with depth: `min(0.6, 0.1 + level * 0.005)`. Dark rooms are stored as a set of **room center tuples** on `dungeon.dark_rooms`. The start room is never darkened; `_assign_dark_rooms` is skipped on boss levels and on L<5.

Main-loop consumer (`main.py:_refresh_fov`): for each room whose center is in `dark_rooms`, if the player is inside the room's bounding box, their FOV is clipped to a small radius around themselves:

```python
dark_radius = 1 + max(0, (self.player.PER - 10) // 5)
```

So PER 10 → radius 1, PER 15 → radius 2, PER 20 → radius 3. `see_invisible` status bypasses the clip. The player's `_in_dark_room` flag is set each FOV refresh so the `stealth_in_dark` chain-equip passive can read it.

### 5.3 Extra FOV layers
Beyond the base shadowcast, `_refresh_fov` folds in several accessory/passive expansions:
- `four_faces_360_fov` (Crown of Brahma T4): add every tile within `PER * 1.5`, ignoring wall occlusion.
- `forest_hearing` (Erlking Mantle) / `tremor_sense` (Blindfold): reveal monster tiles within radius through walls.
- `palladium`: all stair tiles become permanently `explored`.

---

## 6. Boss floors (hand-crafted)

Each boss floor is a static map authored in `src/boss_levels.py`. The common contract:
- `rooms[0]` holds `STAIRS_UP` (entry).
- `rooms[-1]` holds `STAIRS_DOWN` (exit), except L100 which has no exit.
- The boss spawns in a dedicated boss chamber (typically second-to-last room).
- No procedural terrain pass runs on boss floors (`_apply_terrain` gated by `if not is_boss`).
- No dark-room pass runs (`_assign_dark_rooms` gated the same way).
- No baseline monster population — boss levels return `(dungeon, boss_monster_list, [])`.

### 6.1 L20 — Labyrinth of Asterion (Minotaur)
Three parallel east-west corridors with vertical connectors, blocked connectors forming dead ends, a central boss chamber, treasure alcoves to each side. **Phasing walls**: a set of `WALL` tiles stored on `dungeon.phasing_walls` that Asterion (and only Asterion) can walk through, baked in across the three corridors and the shortcut from corridor 3 to the boss room. The hit-and-run AI uses this to ambush from any direction.

### 6.2 L40 — Temple of Medusa
Columned nave with 4 ALTARS and 2×2 pillars for LoS cover, four side chapels (two tiers), inner sanctum with 4 pillars sited to block Medusa's line of sight. Exit tunnel to the east.

### 6.3 L60 — Fafnir's Hoard
Twisting cave passages leading to a wide hoard chamber (14×9), 4 treasure alcoves cross-connected, and the dragon's lair as a deep chamber below. Stalagmites inside the hoard and rock formations in the boss room give the player cover to dig pits behind (shovel builds vs. Fafnir).

### 6.4 L80 — Fenrir's Frozen Hall
Grand hall with an Altar of Odin, four 5×3 side chambers (barracks/storerooms), secondary hall with two more sides, throne room with ice patches as slippery combat terrain (3 patches: left/center/right), 4 frozen pillars for tactical cover.

### 6.5 L100 — Abaddon's Abyss
Six outer-ring chambers (NW/NE/W/E/SW/SE) around a central boss arena, each cross-connected and spoked to the center. Six altars ringing the boss chamber (for holy-fire prayers vs. Abaddon). Boss arena has crumbled WALL remnants as minimal cover against locust swarms. **No STAIRS_DOWN** — the Philosopher's Stone is spawned here by `LevelManager._place_stone(dungeon, items)` (which prefers the deepest room). The player must slay Abaddon, grab the Stone, and ascend.

### 6.6 L999 — Moo Moo Farm (Cow Level)
Dispatched by `generate_boss_level(COW_LEVEL)` where `COW_LEVEL = 999`. A large open pasture (35×20) with fence-post wall pillars scattered as cover, a 6×4 pen in the top-right walled off by a `DOOR`. 40-50 Hell Bovines are placed in the pasture; the Cow King sits in his pen. The entrance is a reversed stair — `STAIRS_DOWN` leads *back home* (there's no deeper level than 100 in the main tower, so the cow floor's exit is the portal out). Atmosphere lines "The air smells of hay and brimstone." / "Welcome to the Moo Moo Farm."

### 6.7 Multi-tile boss anchor correction
`_spawn_boss` places the boss at `boss_room.center`. For a multi-tile footprint (Fafnir 2×2, procedural 2×2 cosmic bosses — Tiamat / Surtur / Ymir / Hrungnir), the anchor is shifted up to 3 tiles NW until every footprint tile is walkable and in-bounds. For 1×1 bosses this loop is a no-op.

---

## 7. Pits and traps

### 7.1 Floor traps (procedural)
`spawn_items` ends by placing `rng.randint(1, min(3, 1 + level // 20))` floor traps on random `FLOOR` tiles that aren't the start-room center and don't already carry a ground item. Trap types (uniform random choice):

| Type           | Damage     | Side effect                                     |
|----------------|------------|-------------------------------------------------|
| pit            | 2d6 phys   | Creates a permanent `pits[(x,y)]` entry         |
| arrow          | 1d6+2 pierce | —                                             |
| alarm          | 0          | Wakes/aggros nearby monsters in 10-tile radius   |
| acid           | 2d4 acid   | Applies `corroding` 5t                          |
| teleport       | 0          | Random teleport                                  |
| fire           | 2d4+2 fire | Applies `burning` 3t (unless `fire_resist`)     |
| sleep_gas      | 0          | `sleeping` 3-8t (save vs CON DC `12 + level//7`) |
| bear_trap      | 1d4 phys   | `immobilized` 2-4t (save vs CON)                |
| squeaky_board  | 0          | Wakes every monster on the floor                 |
| rust           | 0          | Rusts equipped rustables                        |
| polymorph      | 0          | Polymorphs the player                           |

Each trap carries `{'revealed': False, ...}`. The main-loop `_check_floor_trap` runs when the player steps onto a trap tile: if the trap is `safe_for_player` (rewired via disarm-chain ≥ 3) the player passes through, otherwise a PER-based sidestep check runs (`0.05 + PER * 0.02`, so PER 10 ≈ 25% dodge), and on failure the trap fires and is removed from the dict.

### 7.2 Pit traps (special)
When a pit trap fires it also writes `dungeon.pits.add((x, y))` so the hole persists after the trigger. Player steps on a pit → `in_pit` effect, 1d4 damage, must spend one move "climbing out."

### 7.3 Player-dug pits
With a shovel-class weapon the player can dig a pit at an adjacent tile: 30 SP cost, 3-turn commitment, writes `(x, y)` into `dungeon.pits`. Monsters that path over the pit fall in; the player will also fall in if they walk onto their own pit without `levitating`.

### 7.4 Trap reveal
Traps start hidden. They are revealed by:
- The PER-based sidestep roll on the main-loop trigger path (above).
- The `Search` action, which `_search_adjacent_traps` scans and flips `revealed=True`.
- `_try_disarm_trap` (AI escalator-chain quiz) — chain ≥ 3 rewires the trap to be safe for the player (`safe_for_player=True`); chain < 3 fires it.
- The Ethereal Unicorn pet's passive `trap`-detect scan — see [pets.md](pets.md) §3.4.

---

## 8. Bones — persistent death across runs

Bones files encode "a player died HERE, with THIS gear, in THIS way." Future runs can summon that player's ghost on the same floor, haunting with cursed loot.

### 8.1 On death — `save_bones(player_name, dungeon_level, defeat_reason, player, player_gold)`
Called from `_on_game_over` after death or victory. Writes `bones_L<N>.json` into `save_dir()/bones/`. Fields:

```json
{
  "player_name": "...",
  "dungeon_level": N,
  "defeat_reason": "...",
  "player_level": ...,
  "max_hp": ...,
  "gear": [...up to 5 equipped items...],
  "gold": min(player_gold, 500)
}
```

Gold is capped at 500 so a late-run death doesn't fund the next run's early floor from a bones windfall. Only 3 bones files are kept — the oldest is evicted when a 4th is saved (`_MAX_BONES = 3`, `_evict_oldest(bd)` by mtime).

### 8.2 Kilt of the Pharaoh — royal_burial
If any equipped item carries `royal_burial=True`, the first **non-kilt** equipped item in gear is tagged `'preserved': True`. On respawn, that preserved item stays uncursed with `buc_known=True` (the inscription reads "preserved by the Pharaoh").

### 8.3 On level entry — `load_bones(dungeon_level)`
File-existence check runs FIRST (no point burning the 50% roll on a floor with no bones). If a file exists, roll a 50% gate. On pass, the bones dict is returned AND the file is deleted (so this ghost only haunts once). Corrupt bones files are removed to prevent them occupying a slot forever.

### 8.4 `spawn_ghost(bones, dungeon, monsters, items)`
Builds a `Monster` defn:
- `id='player_ghost'`, `name='Ghost of <player_name>'`, symbol `'G'`, color `[180, 180, 255]`.
- HP: `max(20, min(max_hp // 2, 300))`.
- Attacks: `spectral touch` scaling with saved `player_level` (`'1d4+1'` to `'20d4+10'` — but see audit note: `player_level` isn't persisted on `Player`, so it reads 1 in practice).
- Resistances: physical, cold, poison. Weaknesses: holy, fire. Tags: `['undead']`.
- Treasure dict is a dead field — ground gear is placed separately below.

**Occupancy check (v2.18).** Ghost placement scans monsters already on the floor and refuses to overwrite them:

```python
occupied = {(m.x, m.y) for m in monsters if m.alive}
```

Up to 5 random non-start rooms are tried for a free `is_walkable` tile not in `occupied`. If every candidate is taken, the ghost is silently skipped rather than clobbering a mini-boss or seal demon placed earlier the same turn. The chosen room becomes the gear-drop room.

### 8.5 Cursed gear placement — `_place_cursed_gear`
For each gear entry: the item id is looked up in the appropriate class pool (weapon/armor/shield/accessory/wand/scroll/potion), `copy.copy`'d, and placed on a free tile inside the ghost's room. All entries are marked `buc='cursed'` with `buc_known=False`, **except** preserved items (Kilt of the Pharaoh), which stay uncursed. A used-tiles set tracks ground_items overlap so a bones drop doesn't stack on a pre-placed floor item. If the bones carried gold, a `GoldPile` lands on the next free tile.

### 8.6 Karma hook
See [karma_prayer](karma_prayer.md) — slaying a bones ghost pays a small karma price in current wiring; the design treats the ghost as "already dead", not as a hostile stranger. The exact penalty value and whether victory should skip bones at all are open follow-ups from the audit.

---

## 9. Cross-reference

- **Monsters.** Spawn pools, bell-curve weighting (`peak_floor`/`spread`/`peak_weight`), pack mechanics, boss definitions → [monsters](monsters.md).
- **Quests & mysteries.** Mystery altars (via `mystery_system.spawn_mystery_for_level`), Ariadne / Athena / Odin / Fenrir shrine wiring, the seven seals Abaddon gate, the Dwarven Forge, Vidar's Altar, the Altar of the Last Judgment → [quests_mysteries](quests_mysteries.md).
- **Karma + prayer.** How altars interact with prayer, bones-ghost karma penalty, prayer cooldown → [karma_prayer](karma_prayer.md).
- **Pets.** Soul Sphere throw/hatch, bones-ghost does not affect pets, Ethereal Unicorn trap-detect → [pets](pets.md).

---

## 10. Depth-indexed events reference

A quick lookup of every floor whose number triggers a scripted spawn. These are *in addition* to the procedural passes above, and they run from `spawn_items` at the end of floor generation.

| Floor | Event                                                                                       |
|-------|---------------------------------------------------------------------------------------------|
| 1     | Altar pass (level % 15 == 1)                                                                |
| 5     | First leather scrap drop (Vidar secret). Dark rooms become possible.                        |
| 10    | Maze floor. Water terrain unlocked. Graveyard special room unlocked.                        |
| 12    | Bronze Bull Idol (Ariadne quest trigger).                                                   |
| 13    | Leather scrap drop.                                                                         |
| 15    | Swamp special room unlocked.                                                                |
| 16    | Altar pass.                                                                                 |
| 17    | Ariadne shrine carved.                                                                       |
| 18    | Throne room special room unlocked.                                                           |
| 20    | **Boss: Asterion the Minotaur**. Labyrinth with phasing walls.                              |
| 21    | Leather scrap drop.                                                                         |
| 28    | Leather scrap drop.                                                                         |
| 29    | Eye of the Graeae (Athena quest trigger).                                                   |
| 30    | Maze floor. Lava rivers unlocked.                                                           |
| 31    | Altar pass.                                                                                 |
| 35    | Leather scrap drop.                                                                         |
| 37    | Athena shrine carved (Aegis of Athena interior).                                            |
| 40    | **Boss: Medusa**. Temple with LoS-blocking pillars. Ice rooms unlocked.                     |
| 42    | Leather scrap drop.                                                                         |
| 46    | Altar pass.                                                                                 |
| 48    | Broken Blade of Gram (Fafnir quest trigger).                                                |
| 50    | Maze floor. Leather scrap drop.                                                             |
| 53    | Odin's Altar + sealed shrine (Sigurd's Shovel).                                             |
| 58    | Leather scrap drop.                                                                         |
| 60    | **Boss: Fafnir the Dragon**. Hoard with stalagmite cover.                                   |
| 61    | Altar pass.                                                                                 |
| 62    | Cat's Footstep (Gleipnir component — silent-alarm trap ring).                               |
| 65    | Woman's Beard (Gleipnir — hidden behind a secret door).                                     |
| 66    | Leather scrap drop.                                                                         |
| 68    | Mountain Root (Gleipnir — surrounded by lava).                                              |
| 70    | Maze floor.                                                                                 |
| 71    | Fish Breath (Gleipnir — surrounded by water).                                               |
| 73    | Leather scrap drop.                                                                         |
| 74    | Bird Spittle (Gleipnir — placed on an altar).                                               |
| 76    | Dwarven Forge (L76+ uses 2-tile corridors). Altar pass.                                     |
| 77    | Bear Sinew (Gleipnir — 4 bear traps around the component).                                   |
| 79    | Vidar's Altar.                                                                              |
| 80    | **Boss: Fenrir the Wolf**. Frozen hall with ice patches.                                    |
| 83    | Forced spawn: seal_demon_wrath.                                                             |
| 85    | Forced spawn: seal_demon_pestilence.                                                        |
| 87    | Forced spawn: seal_demon_famine.                                                            |
| 89    | Forced spawn: seal_demon_war.                                                               |
| 90    | Maze floor.                                                                                 |
| 91    | Forced spawn: seal_demon_death. Altar pass.                                                 |
| 93    | Forced spawn: seal_demon_earthquake.                                                        |
| 97    | Forced spawn: seal_demon_silence.                                                           |
| 99    | Altar of the Last Judgment. Descent gated on all 7 seals.                                   |
| 100   | **Boss: Abaddon the Destroyer**. Philosopher's Stone placed here (no STAIRS_DOWN).          |
| 999   | **Secret: Moo Moo Farm**. Cow King + 40-50 Hell Bovines. Access path via Wrinkled Cow Rune. |

The `_LEATHER_SCRAP_LEVELS = [5, 13, 21, 28, 35, 42, 50, 58, 66, 73]` list is the complete scrap set — the Vidar secret requires all ten.

The six Gleipnir component rooms on L62/65/68/71/74/77 each wrap the component in a themed challenge keyed to the lore of the component (sound → silent alarm, mountain → lava, fish → water, bird → altar, bear → bear traps). `_create_gleipnir_room` reads from `_GLEIPNIR_COMPONENTS` and dispatches per-component.

---

## 11. Tile constants

Full list of tile integers (`dungeon.py` top of file):

| Const       | Value | Blocks move | Blocks sight | Notes                                                     |
|-------------|-------|-------------|--------------|-----------------------------------------------------------|
| WALL        | 0     | Yes         | Yes          | Default. Impassable + opaque.                              |
| FLOOR       | 1     | No          | No           | Default walkable floor.                                   |
| STAIRS_UP   | 2     | No          | No           | Ascend action.                                            |
| STAIRS_DOWN | 3     | No          | No           | Descend action (gated on seals at F99).                   |
| DOOR        | 4     | Opens on bump | Yes        | Opens into FLOOR; blocks LoS until opened.                 |
| SECRET_DOOR | 5     | Opens on bump/search | Yes | Looks like WALL until revealed.                            |
| ALTAR       | 6     | No          | No           | Prayer target. Amplifies divine effects.                   |
| WATER       | 7     | Yes w/o water_walking | No | Transparent; walking requires `water_walking`.             |
| LAVA        | 8     | Yes w/o fire_resist  | No | Transparent; walking causes damage w/o `fire_resist`.      |
| FOUNTAIN    | 9     | No          | No           | Quaff action (quiz-gated effects).                         |
| GRAVE       | 10    | No          | No           | Dig action (quiz-gated: items may surface, undead may rise). |
| THRONE      | 11    | No          | No           | Sit action (quiz-gated effects).                           |
| ICE         | 12    | No (slides) | No           | Walkable but slippery. Random slide on step.               |

`is_opaque(x, y)` returns True for `WALL`, `DOOR`, `SECRET_DOOR` — nothing else blocks LoS. `is_walkable(x, y)` returns False for `WALL`, `DOOR`, `SECRET_DOOR`, `WATER`, `LAVA`.

---

## 12. BFS reachability detail

```python
passable = (FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR,
            ALTAR, FOUNTAIN, GRAVE, THRONE, ICE)
```

`_bfs_reaches` walks 4-neighbors (not 8-neighbors) because the game's movement model is 4-neighbor for walls — diagonal squeezes through single-tile gaps are blocked in the actual player movement path. Treating `DOOR` and `SECRET_DOOR` as passable is intentional: both open on bump, so a corridor "sealed" by a secret door is still reachable to any player who walks into it.

`_snapshot_tiles(tiles)` and `_restore_tiles(tiles, snapshot)` are the pair used by each terrain pass. Snapshot is a list-of-lists shallow copy of each row (`[row[:] for row in tiles]`); restore writes back in place with `tiles[y][:] = snapshot[y]` so the dungeon object's `tiles` reference stays valid across the roll-back.

---

## 13. Quest shrine helpers

`_create_ariadne_shrine`, `_create_athena_shrine`, `_create_odin_shrine`, `_create_gleipnir_room`, `_create_dwarven_forge`, `_create_vidar_altar`, `_create_judgment_altar` share a common pattern:

1. Locate an anchor tile (fountain / altar / room center).
2. Spiral outward through the WALL layer for an opportunity to carve a 3×3 room (all-WALL candidate region, with at least one `FLOOR` neighbor on the shared wall for the sealed door).
3. Carve the 3×3 interior as FLOOR. The shared wall tile stays WALL (as the "sealed door") and is tracked on the dungeon via a quest-specific attribute (`ariadne_shrine_door`, `athena_shrine_door`, `odin_shrine_door`).
4. Place the quest item on the interior center.

Quest items are typically `Artifact` instances with `identified = True` so they display their true name. The shared-wall sealed door becomes a real `DOOR` when the quest trigger fires (e.g., Bronze Bull dropped at the fountain for Ariadne, Eye of the Graeae at an altar for Athena, Broken Gram at Odin's Altar for Odin).

If the spiral can't find a candidate region within radius 7, the shrine silently fails and the quest item is force-placed on a walkable tile via `_force_place_quest_item`. Quest items guarantee placement — the fallback walks the whole dungeon left-to-right, top-to-bottom.

---

## 14. Dungeon object fields reference

Every attribute set by `generate_dungeon` or later passes. Mostly ignored by consumers that don't need the feature, but useful for understanding what the data model carries.

| Field                       | Type               | Set by                                             |
|-----------------------------|--------------------|----------------------------------------------------|
| `tiles`                     | list[list[int]]    | Generator (BSP / maze / boss)                       |
| `rooms`                     | list[Room]          | Generator                                          |
| `width`, `height`           | int, int            | Generator (80, 50 standard)                        |
| `level`                     | int                 | Generator                                          |
| `explored`                  | set[(x,y)]         | FOV refresh in main loop                            |
| `hidden_chambers`           | list[dict]         | `_place_hidden_chambers`                            |
| `traps`                     | dict[(x,y)] → trap | `spawn_items` (procedural); Gleipnir rooms (quest) |
| `special_rooms`             | dict[(cx,cy)] → str | `spawn_items` first/second roll                    |
| `vault`                     | dict or None       | `_try_place_vault`                                 |
| `dark_rooms`                | set[(cx,cy)]       | `_assign_dark_rooms`                               |
| `atmosphere_messages`       | list[str]          | `_build_atmosphere`                                 |
| `is_maze`                   | bool                | `_generate_maze_dungeon`                           |
| `phasing_walls`             | set[(x,y)]         | `_level_20_labyrinth`                               |
| `ariadne_shrine_door`       | (x,y) or None       | `_create_ariadne_shrine`                           |
| `ariadne_shrine_thread_pos` | (x,y) or None       | `_create_ariadne_shrine`                           |
| `athena_shrine_door`        | (x,y) or None       | `_create_athena_shrine`                            |
| `athena_shrine_aegis_pos`   | (x,y) or None       | `_create_athena_shrine`                            |
| `odin_altar_pos`            | (x,y) or None       | `_create_odin_shrine`                              |
| `odin_shrine_door`          | (x,y) or None       | `_create_odin_shrine`                              |
| `pits`                      | set[(x,y)]         | `_check_floor_trap` (pit trap), `_dig_pit` (shovel) |
| `dwarven_forge_pos`         | (x,y) or None       | `_create_dwarven_forge`                            |
| `vidar_altar_pos`           | (x,y) or None       | `_create_vidar_altar`                              |
| `_has_water`, `_has_lava`   | bool                | `_apply_terrain` → used by `_build_atmosphere`     |
| `bones_ghost_name`          | str                 | `spawn_ghost` (set during level entry)             |

---

## 15. Invariants (do not break)

1. **`_BOSS_LEVELS` is a single source.** `level_manager.py` imports it from `dungeon.py`. Never fork a copy.
2. **The "spawn_monsters skips the first room" idiom is load-bearing.** Both `_spawn_monster_den_extras` and `_populate_hidden_chambers` pass `[dummy, target_room]`. Updating one call site without the other breaks the invariant.
3. **Terrain passes must snapshot + BFS-verify.** Pre-v2.18, this didn't happen and runs could hang on an unreachable `STAIRS_DOWN`.
4. **Boss levels bypass terrain + dark-room passes.** The hand-crafted layouts are the gameplay; a procedural water pool across the Minotaur's labyrinth is a bug, not variety.
5. **`generate_dungeon`'s pass numbering is a contract.** Secret doors expect regular doors to already be placed (adjacency rules). Hidden chambers expect secret-door placement to already have run (no overlap with the random secret doors). Dark rooms expect `rooms[0]` to still be the start room.
6. **Bones consume on load.** Pre-v2.18 corrupt-file cleanup, a bad bones file could permanently occupy a `_MAX_BONES` slot. Current code catches `OSError`/`JSONDecodeError` and removes.
7. **Vault gold is capped at 2000.** The raw `rng.randint(level*5, level*15)` per tile is proportionally scaled down if the raw sum overshoots — never hand out a 6000-gold vault.
