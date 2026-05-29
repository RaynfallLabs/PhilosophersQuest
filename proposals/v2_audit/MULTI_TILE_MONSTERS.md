# Multi-Tile Monsters — Design Proposal (v2, NetHack-informed)

Draft: 2026-05-29. Status: proposal, awaiting user verdict before any
code work begins. No commits yet — every code site referenced is the
*current* (1×1) reality, not a proposed change.

**Revision history**
- v1: drafted from first principles. Recommended "skip Phase 3" (general
  dungeon roam) as risky.
- v2: revised after reading NetHack's `worm.c` + `mkmaze.c` and
  Cogmind's "Developing Multitile Creatures" post-mortem. Phase 3 is now
  recommended — NetHack already proved variable-width corridors work.
  Phase 4 (worms) gains the cutting/splitting mechanic. AOE design
  rules are pinned to Cogmind's "once per entity" lesson.

---

## §0 Why this exists

The bank is built to make the late-game *feel* mythic — ancient dragons
that "shadow cities" in lore, a juvenile Jormungandr who is the World
Serpent in the making, a Nemean Lion with skin no blade can pierce.
Mechanically, every one of those 39 boss/mini-boss creatures occupies
the same 32×32 tile as a giant rat. Walking up to Tiamat and touching
the corner of her tile is indistinguishable from poking a kobold.

This proposal adds **footprint** to the monster model so the late-game
bosses physically *feel* like the things the lore claims they are: a
4-tile dragon you have to circle, a 5-segment serpent that fills the
boss chamber, a 2-tile cyclops you can't squeeze past in a corridor.

The proposal is structured in phases so each phase **ships
independently** with its own play-test gate. We can stop at any phase
boundary and keep what's already in.

---

## §0.5 Research baseline — what NetHack and Cogmind teach us

Two existing implementations anchor every design choice below. Both are
referenced explicitly throughout the proposal so future readers can
trace each rule to its source.

### NetHack — `src/worm.c` (the canonical long-worm model, 35 years of polish)

The data structure is a linked list of segment positions:

```c
struct wseg {
    struct wseg *nseg;
    coordxy wx, wy;   /* the segment's position */
};
```

Globals: `wtails[wormno]` (oldest segment, the trailing tail end),
`wheads[wormno]` (newest segment, co-located with the monster head),
`wgrowtime[wormno]` (next growth tick).

Key behaviours we want to import:

| NetHack function   | What it does                                                                                        | Apply to us? |
|--------------------|-----------------------------------------------------------------------------------------------------|--------------|
| `worm_move()`      | Add new dummy segment at new head position; if growth timer not ready, also `shrink_worm()`         | YES          |
| `shrink_worm()`    | Pop oldest segment from tail (i.e., from `wtails[wormno]`)                                          | YES          |
| `cutworm()`        | When the worm is hit at a mid-segment AND `level ≥ 3 && !rn2(3)`, **clone the worm into two**       | YES — epic   |
| `worm_cross()`     | Detect diagonal player move between two adjacent body segments; **block it** (no slipping through)  | YES          |
| `count_wsegs()`    | Visible segment count (excludes dummy head)                                                          | YES          |
| `wgrowtime` growth | Long worms grow longer over time on a timer                                                          | SKIP — out of scope; doesn't fit our run pacing |

The cutting/splitting in particular is *the* iconic moment: hit a
4-segment serpent in the middle, suddenly you're fighting two
2-segment serpents. We want this.

### NetHack — `src/mkmaze.c` (variable-width corridors)

```c
void create_maze(int corrwid, int wallthick, boolean rmdeadends);

if (corrwid < 1)  corrwid = 1;
else if (corrwid > 5) corrwid = 5;

/* from makemaz(): */
if (!Invocation_lev(&u.uz) && rn2(2))
    create_maze(-1, -1, !rn2(5));
/* -1 → corrwid = rnd(4); */
```

**This is the key precedent.** NetHack already generates 1- to 4-wide
corridors at random. Our Phase 3 is no longer "we're inventing
something" — it's "we're doing the established roguelike pattern."

### Cogmind — Josh Ge's [multi-tile creature post-mortem](https://www.gridsagegames.com/blog/2020/04/developing-multitile-creatures-roguelikes/)

The modern reference, from a roguelike with real mechanical multi-tile
support. The rules we'll follow verbatim:

1. **Anchor = top-left corner.** "I chose the Entity's top-left corner
   as their reference position." (Matches our §2 design.)
2. **Dual data: cells store entity handle + entity stores its tile list.**
   Cells point at the entity; entities know their footprint. Both
   directions queryable in O(1). (Matches our `occupied_tiles()` helper.)
3. **Pathfinding via A* + per-tile validity callback** that checks the
   FULL footprint, not just the anchor. "isValid() just needs to be
   sure to check not only whether the reference position at each cell
   along the path is valid, but that all other relative parts of the
   same creature are also valid."
4. **AOE damage applies once per entity, period.** "Regardless of size,
   a single unit can only be affected once by a given AOE attack…
   keep a record of all the entities already impacted by each active
   AOE effect." Penetrating shots are the trap — same rule applies.
5. **Square footprints only, no rectangles or non-square shapes.**
   "Non-square shapes (even just rectangles!) are problematic since
   then you likely have to deal with the logic and consequences of
   rotation." So: 1×1, 2×2, 3×3, never 2×3 or 1×4. Worms use the
   segment model instead.
6. **Partial-FOV visibility: show the whole creature if ANY tile is
   visible.** Cogmind tried "fade the out-of-FOV tiles" and bounced;
   the simpler rule reads better.
7. **Cogmind's regret: "add this kind of creature early."** We're
   adding mid-development. Acknowledged risk. Mitigation: the §4
   helper-and-grep-replace pass has to be thorough; we'll have a
   test for every footprint code path before we commit.

---

## §1 The current state (single-tile assumption)

A baseline audit so the design doesn't drift from reality.

### Data — `data/monsters.json`

- 522 monster definitions
- 0 of them have any size field (`size`, `width`, `height`, `footprint`,
  `segments`, `tile_w`, `tile_h`, `large`, `huge`, `multi_tile` — all
  absent across all 522)
- 10 final bosses (the 7 seal demons + iron_patriarch + whispering_crone
  + blood_archon) and 29 mini-bosses (jormungandr_juvenile, nemean_lion,
  echidna, talos, baba_yaga, anansi, …) are the natural candidates for
  sizing up

### Code — single-tile coordinate touches

`m.x` / `m.y` appears in **57 places across 12 source files**:

| File                      | Refs | What it does                                  |
|---------------------------|------|-----------------------------------------------|
| `game_combat.py`          | 18   | Attack adjacency, AOO, line-of-sight          |
| `main.py`                 |  9   | Player move, target lookup, FOV, traps        |
| `game_magic.py`           |  7   | Wand/spell targeting, AOE                      |
| `game_divine.py`          |  6   | Prayer effects on monsters                    |
| `monster.py`              |  4   | All 12 AI patterns                            |
| `combat.py`, `game_render.py`, `hero_specials.py` | 3 each | Damage flow, render, hero specials |
| `game_input.py`, `pet_system.py`, `game_encounters.py` | 1–2 each | UI, pets, NPCs |

Every one of these assumes `(m.x, m.y)` is the **only** tile the monster
occupies. The single hottest pattern is:

```python
target = next((m for m in self.monsters
               if m.alive and m.x == nx and m.y == ny), None)   # main.py:1652
```

— this fires every time the player walks into a tile to attack. It would
miss every tile of a 2×2 monster except the top-left.

### Movement geometry — `dungeon.py`

The structural blocker that shapes every phase below:

- `_carve_h(tiles, x1, x2, y)` and `_carve_v(tiles, y1, y2, x)` at
  `dungeon.py:824-833` carve **1-tile-wide corridors** by setting a
  single row or column to FLOOR.
- `_ROOM_MIN_INNER = 3` (`dungeon.py:64`) — rooms are at least 3×3
  interior. Boss rooms in `boss_levels.py` are 7×10 or larger.

A 2×2 creature cannot fit through a 1-tile corridor. So **any phase
that lets a multi-tile creature roam the main dungeon requires
corridor-widening logic** — a real piece of work in its own right.

### Renderer — `renderer.py:266-287`

`draw_entity(x, y, color, ...)` does exactly one `screen.blit(sprite,
(sx, sy))` at exactly one tile. It has no awareness of a footprint.

### FOV — `fov.py`

`calculate_fov(dungeon, px, py, radius)` casts shadow from a single
source point. Monster-visibility checks ask "is `(m.x, m.y)` in the
visible set?" — which means a multi-tile monster is "visible" iff its
anchor tile is, even if the rest of the footprint is in the open.

---

## §2 Data model

A single new optional field on every monster definition, plus its
companion runtime state on the `Monster` instance.

### Data field — `data/monsters.json`

```jsonc
"ancient_dragon": {
  ...,
  "footprint": [2, 2],          // [w, h]; absent ⇒ [1, 1] (default)
  "footprint_anchor": "nw"       // optional; default "nw"
}
```

- `footprint`: `[w, h]` with `w, h ∈ {1, 2, 3}`. Absent = `[1, 1]`
  (every existing monster keeps current behavior).
- `footprint_anchor`: which corner of the footprint `(m.x, m.y)`
  represents. Default "nw" (top-left). Listed for future flexibility;
  Phase 1 hardcodes "nw" and ignores the field.

### Runtime — `Monster.__init__`

```python
self.footprint: tuple[int, int] = tuple(defn.get('footprint', (1, 1)))
self.footprint_w, self.footprint_h = self.footprint
```

Add a single helper on `Monster`:

```python
def occupied_tiles(self) -> Iterator[tuple[int, int]]:
    """Yield every (x, y) tile this monster currently occupies. For
    1×1 monsters this is just the anchor tile."""
    for dy in range(self.footprint_h):
        for dx in range(self.footprint_w):
            yield (self.x + dx, self.y + dy)
```

Every adjacency / collision / hit-test call site is rewritten in terms
of `occupied_tiles()` rather than `m.x == nx and m.y == ny`. This is
the **single biggest mechanical change** and the one that has to be
done right — every "is this tile inside this monster?" question becomes
a footprint membership test.

For segmented creatures (Phase 4), `occupied_tiles` is overridden to
yield the head + every trailing segment.

---

## §3 Phase 1 — Cosmetic-only ("hero sprite", 1×1 mechanics)

**Goal**: ancient dragons render as one **64×64** sprite (covering a
2×2 block) but still mechanically occupy 1 tile. Nothing about
collision / FOV / attack / AI changes. The player can still walk on the
3 "phantom" tiles around the dragon's anchor.

**Scope**: only the renderer changes.

### Changes

1. `monster.py` — add `footprint` field + `occupied_tiles()` helper
   (so Phase 2 has it ready). No behavior change yet.
2. `renderer.py:draw_entity` — when called for a monster with
   `footprint != (1, 1)`, look up a **scaled** sprite (or tile the 32×32
   sprite across the footprint), and blit it at the anchor tile with
   the full footprint dimensions.
3. `data/monsters.json` — add `"footprint": [2, 2]` to the 4 dragon
   tiers (young / adult / ancient + Fafnir) and to the 3 obvious
   "huge" non-dragon bosses (Talos the bronze giant, Cacus the
   fire-breathing giant, Cyclops if present).

### Wins
- Visual impact lands immediately.
- Zero engineering risk for the rest of the engine.
- Every save file is forward-compatible (missing field defaults to
  `(1, 1)`).

### Losses
- Dishonest geometry. Player can stand "inside" the dragon. Hit a
  corner and you're hitting "the dragon." Spatial puzzles don't change.
- We tell a visual lie the engine doesn't back up. Some players will
  notice and find it cheap.

### Effort
- ~half-day. Renderer change is ~30 lines, data is 7 monster entries,
  no AI/movement/FOV code touched.

### Tests
- Source-regression: `Monster.footprint` exists and defaults to (1, 1).
- Source-regression: dragon definitions carry `"footprint": [2, 2]`.
- Data: every existing 1×1 monster still loads with `footprint == (1, 1)`.

---

## §4 Phase 2 — Footprint-aware mechanics, **room-bound only**

**Goal**: a 2×2 dragon is real. Player attacks any tile of the
footprint, the dragon's tiles all block movement, FOV sees any
occupied tile that's in line of sight. The dragon never leaves the
boss room — no corridor support needed.

This is the **phase that makes the feature feel honest** and is where
the bulk of the engineering work lives.

### Required code edits

| Site                                  | Current code (1×1)                                    | New (footprint-aware)                                              |
|---------------------------------------|--------------------------------------------------------|---------------------------------------------------------------------|
| `main.py:1652` player-attack target   | `m.x == nx and m.y == ny`                              | `(nx, ny) in m.occupied_tiles()`                                    |
| `main.py:1545-1548` feared flee logic | `abs(m.x - px) + abs(m.y - py)` per monster            | use nearest occupied tile of `m`                                    |
| `main.py:1647-1649` AOO pre-adjacent  | `abs(_m.x - px) <= 1 and abs(_m.y - py) <= 1`          | any tile of `_m` is within Chebyshev-1 of `(px, py)`                |
| `combat.py:_line_of_sight`            | start = `(m.x, m.y)`                                   | LOS from any occupied tile (cheapest valid path)                    |
| `game_combat.py` adjacency (18 refs)  | Chebyshev-1 check on `m.x, m.y`                        | adjacency = any occupied tile of `m` is Chebyshev-1 of `(px, py)`   |
| `monster.py` AI movement (`self.x, self.y = nx, ny`) | single-tile teleport                | "step the footprint": validate every destination tile is walkable + unoccupied, then move all tiles together |
| `monster.py` packs / allies-within-N  | `abs(m.x - self.x) + abs(m.y - self.y)`                | distance between nearest occupied tiles                             |
| `fov.py` (caller-side)                | `(m.x, m.y) in visible`                                | `any(t in visible for t in m.occupied_tiles())`                     |
| `renderer.py:draw_entity`             | one blit                                                | (already done in Phase 1)                                           |
| `game_magic.py` wand/AOE targeting    | tile-equality compare                                  | footprint membership                                                |
| `game_divine.py` prayer effects       | iterate monsters by tile                               | iterate occupied tiles → unique monsters                            |

### A single helper carries most of this

```python
# combat.py or a new geom.py
def tile_in_monster(tile: tuple[int, int], m: Monster) -> bool:
    return tile in m.occupied_tiles()

def monster_at_tile(monsters, tile) -> Monster | None:
    for m in monsters:
        if m.alive and tile_in_monster(tile, m):
            return m
    return None

def chebyshev_to_monster(px: int, py: int, m: Monster) -> int:
    return min(max(abs(mx - px), abs(my - py))
               for mx, my in m.occupied_tiles())
```

The grep-and-replace pass becomes "find every `m.x == nx and m.y == ny`
and route through `monster_at_tile`" + "find every `abs(m.x - px) <= 1`
and route through `chebyshev_to_monster(...) <= 1`".

### Spawn placement — `level_manager.py` / `boss_levels.py`

The boss-spawn helper needs to validate the full footprint fits in the
boss room. Boss rooms are hand-carved at 7×10 or larger — a 2×2 dragon
fits easily. Restrict multi-tile monsters to **room-bound spawns
only**:

- Phase 2 contract: **monsters with `footprint != (1, 1)` only ever
  spawn in boss rooms** (`is_boss` / `is_mini_boss` flag + boss-room
  placement in `boss_levels.py`).
- The wandering-spawn picker (`main.py:_maybe_wander_spawn`) skips
  any monster whose footprint can't fit in a 1-tile corridor.

This sidesteps the corridor-width problem entirely for Phase 2. We get
the visual + spatial puzzle in the boss chamber (where it matters
most), without touching `dungeon.py` at all.

### Boss-room movement

Inside a 7×10 chamber, a 2×2 dragon has plenty of room to maneuver.
The AI's "step toward player" turn calls `try_step((dx, dy))`, which:

1. Computes destination tiles for every footprint tile.
2. Rejects if any destination is a wall, monster, or door.
3. (Optional) allows step if the player is standing on one of the
   destination tiles — that's an attack, not a move. Phase 2 keeps it
   simple: any blocker including the player rejects the step.

### Wins
- Real spatial puzzle: dragon fills half the boss room, you have to
  retreat through the door.
- "Get out of the corner" becomes a real player skill.
- Boss fights actually FEEL like boss fights.

### Losses
- Touches ~80 code sites (the 57 refs plus several adjacency formulas).
- High regression risk if a footprint test gets missed somewhere.

### Effort
- 2–3 days of careful, test-led work. The footprint helpers are small;
  the long pole is the grep-replace audit + writing tests that exercise
  every adjacency path with a 2×2 monster present.

### Tests (the rigor demanded by the §2 helper design)

1. `test_footprint_helpers.py`: `occupied_tiles`, `monster_at_tile`,
   `chebyshev_to_monster`, `tile_in_monster` on 1×1, 2×2, 3×2 cases.
2. `test_attack_2x2.py`: player attacks each of the 4 tiles of a 2×2
   dragon; combat starts on all four.
3. `test_movement_blocks_2x2.py`: 2×2 dragon blocks player from stepping
   into ANY of its 4 tiles.
4. `test_fov_2x2.py`: dragon counts as visible if any occupied tile is
   in FOV.
5. `test_boss_room_fits_2x2.py`: every boss room in `boss_levels.py`
   has at least one 2×2 spawn anchor that's walkable.
6. `test_dungeon_no_2x2_in_corridors.py`: `_maybe_wander_spawn` rejects
   any candidate whose footprint exceeds 1×1.

---

## §5 Phase 3 — Corridor traversal (general dungeon roam) **— do it**

**Goal**: 2×2 creatures can walk the main dungeon, not just boss
rooms. An adult dragon can roam floor 60–80 as a wandering encounter;
a young dragon can show up at floor 30. Late-game corridors gain real
strategic weight.

This is the **structural** phase — touches the dungeon generator. Per
the v2 research, **this is what NetHack does** (`mkmaze.c:create_maze`
with `corrwid = rnd(4)` randomly picking 1–4 tile widths) — so we're
not inventing, we're matching the established pattern.

### Revised approach: NetHack-style variable-width per floor

NetHack picks a corridor width per floor at generation time. We do
the same. The floor's `corrwid` is rolled at the start of
`generate_dungeon()`:

```python
# In dungeon.py, near the BSP / generation entry point
def _roll_corridor_width(level: int, rng: random.Random) -> int:
    """Return the corridor width for this floor, 1..3.
    Early floors stay tight (1); deeper floors get more wide variants
    so the player encounters wide-corridor floors more often as
    dragon-tier monsters become reachable."""
    if level < 20:
        return 1                       # tutorial / early game stays tight
    if level < 50:
        return 1 if rng.random() < 0.85 else 2   # ~15% wide
    if level < 80:
        return rng.choices([1, 2], weights=[0.6, 0.4])[0]
    return rng.choices([1, 2, 3], weights=[0.4, 0.5, 0.1])[0]
```

Boss levels at 20/40/60/80/100 keep their hand-crafted layouts — they
ignore the rolled width.

### Carving change

`_carve_h` and `_carve_v` accept a `width` parameter and carve a
`width`-tile-thick stripe:

```python
def _carve_h(tiles, x1, x2, y, width=1):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for w in range(width):
            yy = y + w
            if 0 <= yy < len(tiles) and tiles[yy][x] == WALL:
                tiles[yy][x] = FLOOR

def _carve_v(tiles, y1, y2, x, width=1):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        for w in range(width):
            xx = x + w
            if 0 <= xx < len(tiles[0]) and tiles[y][xx] == WALL:
                tiles[y][xx] = FLOOR
```

`_carve_corridor` propagates the width through.

### Spawn picker uses the floor's width

`_maybe_wander_spawn` and the initial-placement code in
`level_manager.py` consult `dungeon.corridor_width` (a new attribute
stamped at generation time) to decide whether a 2×2 monster is allowed
to spawn on this floor at all. Floors that rolled `width=1` reject
multi-tile candidates the same as today.

### Visual change to the player

- Most early-game floors look exactly like today's.
- Starting around L20, occasional floors feel "more open" — sight
  lines longer, fewer pinch points.
- L80+, you'll see entire 3-wide hallways where a wing-spread dragon
  fits naturally.

This gradient is good design: it pre-signals to the player that
something different lives down here.

### Wins
- 2×2 monsters get to roam, not just boss-camp.
- Floor variety increases (some floors feel tight, some open) — a
  feature in itself.
- Follows NetHack's actual generator — no novel technique to debug.

### Losses
- 1–2 days of generator work + heavy play-testing because every
  late-game floor's spatial feel shifts.
- Room-corridor junctions need attention — a 1-wide corridor meeting
  a wide corridor at an L-bend can leave a single notch tile. Need a
  cleanup pass.

### Effort
- 1.5 days of focused work + a play-test pass with you. Smaller than
  Phase 2 because the carve helpers are localised.

### Tests
1. `test_corridor_width_rolls_by_floor`: width distribution matches
   the table above for L1, L20, L50, L80.
2. `test_2x2_traverses_wide_corridor`: given a generated floor with
   `corridor_width=2`, a 2×2 monster can step along the corridor
   without colliding.
3. `test_2x2_rejected_in_narrow_corridor`: width=1 floor rejects 2×2
   spawn candidates in wandering-spawn.
4. `test_no_notch_junctions`: every floor-tile is part of either a
   room or a width-`n` corridor; no single-tile notches at L-bends.

---

## §6 Phase 4 — Segmented serpents (1×N worms, full NetHack model)

**Goal**: Jormungandr Juvenile and 1–2 other serpent-class creatures
occupy a *chain* of tiles — a head + trailing body. The body bends
naturally, blocks the player like a wall, and **splits into two
serpents if cut in the middle**.

This is a clean port of `NetHack/src/worm.c`. We've already validated
the data structure (§0.5).

### Data

```jsonc
"jormungandr_juvenile": {
  ...,
  "segments": 5,                // total body length including the head
  "split_on_cut": true,         // hitting a mid-segment may clone the worm
  "split_chance": 0.33,         // matches NetHack's !rn2(3)
  "hp_per_segment": 40          // HP scales with length (max_hp = N × this)
}
```

Mutually exclusive with `footprint` on the same monster (assert in
the loader).

### Runtime state

The `wseg`-equivalent. We use a Python list of `(x, y)` tuples instead
of a linked list — Python lists are O(1) at both ends with `appendleft`
on a `deque`, and we never need to traverse the chain.

```python
from collections import deque

self.segments: int = int(defn.get('segments', 1))
self.tail: deque[tuple[int, int]] = deque(maxlen=self.segments - 1)
self.split_on_cut: bool = bool(defn.get('split_on_cut', False))
self.split_chance: float = float(defn.get('split_chance', 0.0))
self.hp_per_segment: int = int(defn.get('hp_per_segment', 0))
if self.hp_per_segment:
    self.max_hp = self.segments * self.hp_per_segment
    self.hp = self.max_hp
```

### Movement — `worm_move` equivalent

```python
def _move_head(self, nx: int, ny: int):
    """NetHack's worm_move: add a new dummy at the new head position,
    drop the oldest tail segment. The deque's maxlen handles the drop
    automatically."""
    self.tail.appendleft((self.x, self.y))   # previous head → neck
    self.x, self.y = nx, ny
    # deque trims to maxlen, no explicit shrink needed

def occupied_tiles(self):
    yield (self.x, self.y)
    yield from self.tail
```

### **Cutting & splitting** — `cutworm` equivalent (the iconic feature)

When the player hits a body segment (NOT the head), and the worm is
long enough, there's a chance it splits into two worms. From NetHack:

```c
/* cutworm: cuttier means a more brutal cut (e.g., scimitar) */
if (worm->m_lev >= 3 && !rn2(3)) {
    /* clone the worm via clone_mon, split the wseg list at the hit */
}
```

Our port:

```python
def take_damage_at_segment(self, hit_idx: int, dmg: int, game):
    """hit_idx: 0 = head, 1..N-1 = body segment. Called when the
    player attacks a tile that's mid-body."""
    self.hp -= dmg
    if hit_idx == 0 or not self.split_on_cut:
        return
    # NetHack: clone if level high enough AND random gate passes
    if (self.segments >= 4
            and random.random() < self.split_chance):
        front_len = hit_idx
        back_len = self.segments - hit_idx
        if front_len >= 2 and back_len >= 2:
            game.add_message(
                f"The {self.name} is cleaved in two — "
                f"both halves writhe to life!", 'danger')
            self._spawn_split_clone(game, front_len, back_len)
```

The clone gets its own monster ID via a new helper that walks the
existing spawn pipeline. Both halves keep their AI pattern (still
"snake," still hungry). HP is split proportionally. Levels drop by 1
on each half. This is the NetHack rule.

Cap: a serpent that's already 2 segments can't split (would produce a
1-segment which is just a regular snake). Enforced by the `>= 2` checks
above.

### **Diagonal-cross prevention** — `worm_cross` equivalent

NetHack's `worm_cross()` blocks the player from moving diagonally
between two adjacent body segments. Without this, the player can
"slip through" the worm body diagonally and break the spatial puzzle.

```python
def player_diagonal_blocked_by_worm(self, px, py, dx, dy, worm) -> bool:
    """Return True if the player's diagonal step (dx, dy) would pass
    BETWEEN two adjacent segments of `worm`. Both intermediate tiles
    must be worm-occupied."""
    if abs(dx) != 1 or abs(dy) != 1:
        return False   # not a diagonal
    occ = set(worm.occupied_tiles())
    side_a = (px + dx, py)
    side_b = (px, py + dy)
    return side_a in occ and side_b in occ
```

Called from `_do_move` before the destination check. If True, message
"The {worm.name}'s body blocks your path!" and reject the step.

### Corridor traversal — free

Segmented creatures need NO wide corridors. Each segment is 1 tile.
A 5-segment Jormungandr slithers through a 1-tile corridor single-file.
Phase 4 is genuinely independent of Phase 3.

### Combat & AOE — Cogmind's rule applies

- Attacking any tile of the worm hits the worm (Phase 2's
  `monster_at_tile` helper handles this).
- AOE spells that geometrically cover multiple worm tiles **deal
  damage once.** Per Cogmind: every AOE handler keeps a per-cast
  `hit_entity_ids: set[int]` and skips entities already in the set.
  Penetrating shots (the wand-of-lightning straight-line ray) follow
  the same rule.
- Exception we may want: a cutting weapon (e.g., scimitar mastery
  blessing) DOES count separately because it triggers `cutworm`. The
  player gets to "saw through" the body with multiple hits, each one
  potentially the split-trigger.

### Spawn placement

Initial body layout: serpent needs a clear straight-line run of
`segments` floor tiles at spawn time. The existing
`level_manager.place_monsters` is extended with a "needs_straight: int"
parameter; the placer rejects candidates that can't fit. Boss-room
Jormungandr always fits (boss rooms are 7×10+).

### Candidates

| Monster                | Segments | Split? | Lore                                       |
|------------------------|----------|--------|---------------------------------------------|
| `jormungandr_juvenile` | 5        | YES    | World Serpent — splitting fits the myth     |
| `tiamat` (new at L90?) | 7        | YES    | Five-headed dragon-serpent; epic late game  |
| `cave_naga` (new mid)  | 3        | NO     | Mid-game variety; too short to split        |

### Tests
1. `test_serpent_tail_follows_head`: head moves 5 times; tail is the
   prior 5 head positions in order.
2. `test_serpent_diagonal_cross_blocked`: player can't slip diagonally
   between two adjacent body segments.
3. `test_serpent_attack_any_segment`: damage lands when hitting any of
   the N tiles.
4. `test_serpent_split_on_midbody_cut`: long enough + cuttable, mid-hit
   produces two valid serpents.
5. `test_serpent_no_split_on_head_hit`: head hit never triggers split.
6. `test_serpent_no_split_when_too_short`: 3-segment serpent never
   splits (would produce 1-segment).
7. `test_aoe_hits_serpent_once`: lightning bolt grazing 3 body tiles
   damages once.
8. `test_corridor_serpent_slithers`: 5-segment serpent successfully
   moves through a 1-wide L-bend corridor.

### Effort
- 2 days. The model is clean (≈100 lines new) but the split mechanic
  needs careful interaction-testing with the existing `_on_monster_killed`
  / loot / corpse pipeline.

---

## §7 Per-monster manifest (recommended footprints)

Bring everyone forward at the same time so the player meets a coherent
ecology, not "the dragons are big but the cyclops is the same size as a
goblin."

### 2×2 (Phase 1 + 2)

| Monster                | Lore justification                                          |
|------------------------|-------------------------------------------------------------|
| `young_dragon`         | "Already more dangerous than most dungeon denizens"         |
| `adult_dragon`         | "Calculating predators who have lived long enough"          |
| `ancient_dragon`       | "City-shadowing wyrm" (per lore)                            |
| `fafnir`               | Norse dragon-king, sleeps on hoard of the Rhine             |
| `talos`                | Bronze giant of Crete                                       |
| `cacus`                | Fire-breathing giant slain by Hercules                      |
| `nemean_lion`          | Hercules' first labor — the lion the size of a hut          |
| `cyclops` (if present) | Polyphemus, blinded by Odysseus                             |
| `whispering_crone`     | Final boss with cosmic-horror framing                       |
| `iron_patriarch`       | Final boss with cosmic-horror framing                       |
| `blood_archon`         | Final boss with cosmic-horror framing                       |

### 1×N (Phase 4)

| Monster                | Segments | Notes                                |
|------------------------|----------|--------------------------------------|
| `jormungandr_juvenile` | 5        | World serpent. Mini-boss already.    |
| `cave_naga` (new?)     | 3        | Mid-game variety if we want it       |

### Stays 1×1

The other ~500 monsters. Including most mini-bosses (Lamia, Arachne,
Anansi, etc. are humanoid-scale in their myths — Lamia is the size of
a woman, Arachne is a spider, Anansi is a spider). Sizing them up
would be lore-violating.

---

## §8 Risk register

| Risk                                          | Phase | Severity | Mitigation                                                       |
|-----------------------------------------------|-------|----------|------------------------------------------------------------------|
| Footprint test missed in some combat path     | 2     | HIGH     | Add `test_attack_2x2` covering every attack code path. Per Cogmind: "isValid() must check ALL constituent parts." |
| Save format change breaks existing runs       | 1+    | MED      | Missing `footprint` defaults to `(1, 1)`; `segments` field optional |
| Boss room too cramped for 2×2 + player        | 2     | MED      | `test_boss_room_fits_2x2` per room; widen any failing room       |
| AOE double-hits multi-tile monster            | 2 + 4 | MED      | Per-cast `hit_entity_ids: set` in every AOE handler (Cogmind's rule, baked in from day 1) |
| 2×2 monster blocks the only path out          | 2     | LOW      | Boss rooms have a door wider than the dragon; verify in tests    |
| Renderer scales sprite badly                  | 1     | LOW      | `pygame.transform.smoothscale` for v1; new 64×64 art is a follow-up content task |
| Footprint anchor confusion (NW vs center)     | 2     | LOW      | Hardcode NW per Cogmind precedent; documented; revisit if confusing |
| Wandering spawn picks a 2×2 in a 1-corridor   | 3     | HIGH     | Spawn picker reads `dungeon.corridor_width` (new field stamped at gen time); tested |
| Player can't kite a dragon because it's 2×2   | 2     | LOW      | Intended feature; boss rooms have retreat space; corridor-roam floors are wide |
| Notch tiles at width-changing corridor bends  | 3     | MED      | Cleanup pass after carving; `test_no_notch_junctions`            |
| Late-game floors feel "too open" with wide corridors | 3 | MED   | Gradient by floor depth (15% → 50% wide); play-test gate         |
| Serpent tail clips through walls when bending | 4     | MED      | `test_corridor_serpent_slithers` explicitly covers L-bend        |
| Worm split spawns clone in occupied tile      | 4     | MED      | Split-clone placement uses same spawn validator as a fresh monster |
| Player slips diagonally between worm segments | 4     | MED      | Port NetHack's `worm_cross()`; `test_serpent_diagonal_cross_blocked` |
| Adding mid-development bites us (Cogmind regret) | all | MED     | Thorough grep-replace + per-phase test suite; treat each footprint blind spot as a release blocker |

---

## §9 What this does NOT touch

Per the project memory's "no warping content to fit principles" rule
and "understand before proposing" — be explicit about scope.

- **Quiz subjects / banks**: unaffected. No bank entries reference
  monster physical size.
- **Combat formula**: chain-peak / damage / THAC0 all stay as-is.
  Multi-tile monsters get the *same* combat math; the change is
  spatial only.
- **Identify / corpse lore**: id_level mechanic stays. Corpse on death
  still drops at the head/anchor tile.
- **Pet system**: pets follow the same single-tile model. No multi-tile
  pets planned.
- **Save format for existing fields**: only adds an optional
  `footprint` (or `segments`) field; everything else untouched.
- **Boss-room hand-crafted layouts in `boss_levels.py`**: these stay
  unchanged in Phase 1–2. Phase 3 (if we do it) wouldn't touch them
  either.

---

## §10 Open questions for the user

Before any code change, I need your call on:

1. **Renderer in Phase 1 — scaled sprite or new 64×64 art?** Scaling a
   single 32×32 sprite up to 64×64 with `pygame.transform.smoothscale`
   is fast and looks coherent for v1. Commissioning new 64×64 dragon
   art is higher quality but blocks Phase 1 shipping. **Recommended:
   scaled for v1, schedule new art as a follow-up.**

2. **Which floor for the first big monster?** I'd suggest the L20
   Asterion Minotaur stays 1×1 (man-bull, ~normal height), and the
   first 2×2 boss is the **L40 Medusa** (snake-bodied, scary).
   Dragons start showing up wandering from L40+; the L60 Echidna
   becomes 2×2; ancient dragons + final bosses at L80+. **Agree, or
   want the first big monster earlier/later?**

3. **Serpent split mechanic — chance and floor gate?** NetHack uses
   33% per mid-body hit, gated on monster level ≥ 3. For us, suggest
   **40% chance per cutting-weapon mid-body hit, gated on
   `segments ≥ 4`**, so a 3-segment cave naga can't split but
   Jormungandr can. **Agree on 40% / N≥4? Or want it rarer (e.g.
   25%, more memorable when it happens)?**

4. **Which mini-bosses get sized up?** My v2 list adds Echidna (mother
   of monsters), Wendigo (ice giant), Charybdis (whirlpool). I left
   out Anansi (spider) and Lamia (half-snake humanoid) as borderline.
   **Add any others? Anything you'd take off the list?**

5. **Phase 4 segmented candidates beyond Jormungandr?** I propose
   `tiamat` (7-segment, splittable, late-game L90) and `cave_naga`
   (3-segment, non-split, mid-game). Tiamat doesn't exist in the
   monster bank yet — adding her is a content task. **Add Tiamat as
   a new mini-boss, or only do Jormungandr in Phase 4?**

6. **Corridor-width gradient** — my §5 proposal scales width
   by floor (`<L20: 1`, `L20-49: 15% wide`, `L50-79: 40% wide`,
   `L80+: 50% wide + 10% 3-wide`). **Tune up or down?** More wide
   corridors = more dragon-friendly + lighter spatial puzzle.

---

## §11 Suggested execution order (revised for v2 ambition)

The full plan = all four phases. Each phase ships independently with
its own play-test gate; we can stop at any phase boundary.

| Day | Phase                                                    | Ship gate                          |
|-----|----------------------------------------------------------|------------------------------------|
| 1   | Phase 1: data field + renderer (2×2 cosmetic sprites)   | Play-test L40+ boss visuals        |
| 2–3 | Phase 2: footprint helpers + grep-replace + tests       | 100% test pass + L40 Medusa fight  |
| 4   | Phase 2 play-test pass with you, fix issues             | "Feels right" verdict              |
| 5   | Phase 3: variable-width corridor generator              | L60+ dragon-roam play-test         |
| 6   | Phase 3 play-test + cleanup pass                        | "No notch-tile bugs" verdict       |
| 7–8 | Phase 4: segmented serpent model + Jormungandr + split  | L80 Jormungandr fight              |
| 9   | Phase 4 play-test pass + Tiamat (if approved)           | Full multi-tile ecology shipped    |

**Total: 8–9 days of focused work** for the full ambitious build. Each
day ends with a commit + play-test gate; nothing big-bangs.

Phases can be paused between days without leaving the codebase in a
weird half-state — each phase is independently complete.

---

## §12 Honest closer (v2)

You said: "not looking for easy, looking for most fun and epic." With
NetHack as proof, here's the revised verdict:

**Phase 1+2 (cosmetic + boss-room-bound 2×2):** still must-have. This
is the floor for "the late-game feels mythic." Solid 3 days.

**Phase 3 (variable-width corridors, 2×2 roam):** **YES, now
recommended.** NetHack already proved this works (`mkmaze.c` with
`corrwid=rnd(4)`). Skipping it would have given you boss-room
spectacle without the *world* feeling like dragon country. With it,
L60+ floors physically read as "dragons live here" — wider sightlines,
real spatial breathing room. The "no notch-tile bugs" cleanup is the
only real risk and it's testable.

**Phase 4 (segmented serpents with split-on-cut):** **YES, this is
where the proposal gets epic.** Cutting Jormungandr in half and
suddenly fighting TWO Jormungandr is the kind of moment kids tell
their friends about. NetHack solved it 35 years ago; we get it for
free by porting `cutworm` and `worm_cross`.

**One genuine concern remains** — Cogmind's regret: "add multi-tile
early in development." We're adding mid-stride. Mitigation = the §4
grep-replace pass + the per-phase test suite. If we do that work
properly, the regret doesn't apply because the test gate catches every
footprint-blind code path before it hits the player.

**Total commitment if you greenlight everything: 8–9 focused days.**

The bank will already be there to back it up — "ancient dragon"
becoming literal in the geometry is just the engine catching up to
what the lore field has been claiming all along.
