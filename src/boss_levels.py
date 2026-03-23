"""
Static hand-crafted boss level maps for levels 20, 40, 60, 80 and 100.

Each boss level:
  - Has a unique visual theme
  - Contains a unique named boss monster
  - STAIRS_UP in the first room (rooms[0]) -- player enters here
  - STAIRS_DOWN in the last room -- exit to next level
  - Boss spawns in the main chamber (second-to-last room)
"""
import json
import os

from dungeon import Dungeon, Room, WALL, FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, ALTAR, ICE

BOSS_LEVELS = {20, 40, 60, 80, 100}
COW_LEVEL = 999   # Moo Moo Farm (secret)

_W, _H = 80, 50


# ---------------------------------------------------------------------------
# Tile helpers
# ---------------------------------------------------------------------------

def _blank():
    return [[WALL] * _W for _ in range(_H)]


def _fill(tiles, x1, y1, x2, y2, tile=FLOOR):
    for y in range(max(0, y1), min(_H, y2 + 1)):
        for x in range(max(0, x1), min(_W, x2 + 1)):
            tiles[y][x] = tile


def _hline(tiles, x1, x2, y, tile=FLOOR):
    for x in range(max(0, min(x1, x2)), min(_W, max(x1, x2) + 1)):
        if 0 <= y < _H:
            tiles[y][x] = tile


def _vline(tiles, y1, y2, x, tile=FLOOR):
    for y in range(max(0, min(y1, y2)), min(_H, max(y1, y2) + 1)):
        if 0 <= x < _W:
            tiles[y][x] = tile


def _carve_room(tiles, cx, cy, hw, hh):
    """Carve a floor room centered at (cx, cy) with half-dims hw, hh. Returns Room."""
    x1, y1 = cx - hw, cy - hh
    x2, y2 = cx + hw, cy + hh
    _fill(tiles, x1, y1, x2, y2)
    return Room(x1, y1, x2 - x1 + 1, y2 - y1 + 1)


def _connect(tiles, r1, r2):
    """L-shaped corridor connecting two room centers."""
    cx1, cy1 = r1.center
    cx2, cy2 = r2.center
    _hline(tiles, cx1, cx2, cy1)
    _vline(tiles, cy1, cy2, cx2)


def _load_boss(boss_id):
    """Load a monster definition from monsters.json by id."""
    from paths import data_path
    mp = data_path('data', 'monsters.json')
    with open(mp, encoding='utf-8') as f:
        all_defs = json.load(f)
    if boss_id not in all_defs:
        return None
    defn = {**all_defs[boss_id], 'id': boss_id}
    return defn


def _spawn_boss(dungeon, boss_id, boss_room):
    """Spawn the boss monster at the center of its chamber."""
    from monster import Monster
    defn = _load_boss(boss_id)
    if defn is None:
        return []
    cx, cy = boss_room.center
    boss = Monster(defn, cx, cy)
    boss.is_boss = True
    return [boss]


# ---------------------------------------------------------------------------
# Level 20 -- Labyrinth of Asterion (The Minotaur)
# ---------------------------------------------------------------------------

def _level_20_labyrinth():
    """
    The Labyrinth of Knossos. Winding corridors, dead-end alcoves,
    and a central chamber where Asterion the Minotaur awaits.
    """
    tiles = _blank()
    rooms = []

    # Entry chamber (top area, center-left)
    entry = _carve_room(tiles, 12, 6, 5, 3)
    rooms.append(entry)
    tiles[entry.y + 1][entry.center[0]] = STAIRS_UP

    # Three parallel maze corridors (east-west)
    _hline(tiles, 4, 75, 14)
    _hline(tiles, 4, 75, 20)
    _hline(tiles, 4, 75, 26)

    # Vertical connectors between horizontal corridors
    for cx in [8, 16, 24, 32, 40, 48, 56, 64, 72]:
        _vline(tiles, 14, 20, cx)
    for cx in [12, 20, 28, 36, 44, 52, 60, 68]:
        _vline(tiles, 20, 26, cx)

    # Wall off some connectors to create a proper maze (dead ends)
    # Note: first block on each corridor is omitted so the player has a
    # solvable path through the labyrinth (entry→C1→C2→C3→boss room).
    # Asterion still has phasing-wall shortcuts everywhere.
    for cx in [32, 48, 64]:
        tiles[14][cx] = WALL
        tiles[14][cx + 1] = WALL
    for cx in [36, 52, 68]:
        tiles[20][cx] = WALL
        tiles[20][cx + 1] = WALL
    for cx in [40, 56]:
        tiles[26][cx] = WALL
        tiles[26][cx + 1] = WALL

    # Connect entry to top maze corridor
    _vline(tiles, entry.y + entry.height - 1, 14, entry.center[0])

    # Small dead-end alcoves off the corridors
    for ax, ay in [(6, 11), (20, 11), (36, 11), (52, 11), (68, 11)]:
        _fill(tiles, ax - 2, ay - 1, ax + 2, ay + 1)
    for ax, ay in [(8, 17), (28, 17), (44, 17), (60, 17), (72, 17)]:
        _fill(tiles, ax - 2, ay - 1, ax + 2, ay + 1)
    for ax, ay in [(12, 23), (32, 23), (52, 23), (68, 23)]:
        _fill(tiles, ax - 2, ay - 1, ax + 2, ay + 1)

    # Boss chamber -- large central room
    boss_room = _carve_room(tiles, 39, 35, 10, 7)
    rooms.append(boss_room)
    # Dramatic entrance door
    tiles[boss_room.y - 1][boss_room.center[0]] = DOOR

    # Connect bottom maze corridor to boss chamber
    _vline(tiles, 26, boss_room.y, boss_room.center[0])

    # Treasure alcoves off the boss chamber
    alcove_l = _carve_room(tiles, 22, 35, 4, 3)
    alcove_r = _carve_room(tiles, 56, 35, 4, 3)
    _hline(tiles, alcove_l.x + alcove_l.width, boss_room.x, 35)
    _hline(tiles, boss_room.x + boss_room.width, alcove_r.x, 35)

    # Exit chamber (bottom-right)
    exit_room = _carve_room(tiles, 68, 44, 5, 3)
    rooms.append(exit_room)
    tiles[exit_room.y + exit_room.height - 2][exit_room.center[0]] = STAIRS_DOWN
    tiles[exit_room.y - 1][exit_room.center[0]] = DOOR

    # Connect boss room to exit
    _connect(tiles, boss_room, exit_room)

    dungeon = _make(tiles, rooms, 20)

    # --- Phasing walls: secret passages only Asterion knows ---
    # These are WALL tiles that Asterion can walk through (hit-and-run AI).
    # Placed at strategic points between corridors so he can ambush from any direction.
    dungeon.phasing_walls = set()
    # Vertical shortcuts between the three horizontal corridors
    for cx in [10, 22, 34, 46, 58, 70]:
        for y in range(15, 20):   # between corridor 1 and 2
            if tiles[y][cx] == WALL:
                dungeon.phasing_walls.add((cx, y))
        for y in range(21, 26):   # between corridor 2 and 3
            if tiles[y][cx] == WALL:
                dungeon.phasing_walls.add((cx, y))
    # Horizontal shortcuts along blocked connectors
    for cx in [16, 17, 32, 33, 48, 49, 64, 65]:
        if tiles[14][cx] == WALL:
            dungeon.phasing_walls.add((cx, 14))
    for cx in [20, 21, 36, 37, 52, 53, 68, 69]:
        if tiles[20][cx] == WALL:
            dungeon.phasing_walls.add((cx, 20))
    for cx in [24, 25, 40, 41, 56, 57]:
        if tiles[26][cx] == WALL:
            dungeon.phasing_walls.add((cx, 26))
    # Shortcut from corridor 3 to boss chamber area
    for y in range(27, 35):
        for cx in [30, 50]:
            if tiles[y][cx] == WALL:
                dungeon.phasing_walls.add((cx, y))

    return dungeon, _spawn_boss(dungeon, 'asterion_minotaur', boss_room), []


# ---------------------------------------------------------------------------
# Level 40 -- Temple of Medusa
# ---------------------------------------------------------------------------

def _level_40_temple():
    """
    An ancient Hellenic temple. Columned nave, altar, side chapels,
    and the inner sanctum where Medusa waits in stone-cold silence.
    """
    tiles = _blank()
    rooms = []

    # Entrance portico
    entry = _carve_room(tiles, 39, 4, 8, 3)
    rooms.append(entry)
    tiles[entry.y + 1][entry.center[0]] = STAIRS_UP
    tiles[entry.y + entry.height - 1][entry.center[0]] = DOOR

    # Main nave (long central corridor)
    nave = _carve_room(tiles, 39, 22, 6, 14)
    rooms.append(nave)
    _connect(tiles, entry, nave)

    # Altar in center of nave
    tiles[nave.center[1]][nave.center[0]] = ALTAR

    # Pillars (WALL tiles within the nave area -- 2x2 solid squares)
    for py in [13, 18, 24, 29]:
        for px in [35, 43]:
            tiles[py][px] = WALL

    # Left side chapel
    l_chapel = _carve_room(tiles, 20, 15, 5, 4)
    rooms.append(l_chapel)
    _hline(tiles, l_chapel.x + l_chapel.width, nave.x, l_chapel.center[1])
    tiles[l_chapel.center[1]][nave.x - 1] = DOOR

    # Right side chapel
    r_chapel = _carve_room(tiles, 58, 15, 5, 4)
    rooms.append(r_chapel)
    _hline(tiles, nave.x + nave.width, r_chapel.x, r_chapel.center[1])
    tiles[r_chapel.center[1]][nave.x + nave.width] = DOOR

    # Second pair of side chapels
    l_chapel2 = _carve_room(tiles, 20, 29, 5, 4)
    rooms.append(l_chapel2)
    _hline(tiles, l_chapel2.x + l_chapel2.width, nave.x, l_chapel2.center[1])
    tiles[l_chapel2.center[1]][nave.x - 1] = DOOR

    r_chapel2 = _carve_room(tiles, 58, 29, 5, 4)
    rooms.append(r_chapel2)
    _hline(tiles, nave.x + nave.width, r_chapel2.x, r_chapel2.center[1])
    tiles[r_chapel2.center[1]][nave.x + nave.width] = DOOR

    # Inner sanctum (boss room)
    boss_room = _carve_room(tiles, 39, 43, 9, 4)
    rooms.append(boss_room)
    tiles[boss_room.y - 1][boss_room.center[0]] = DOOR
    _vline(tiles, nave.y + nave.height, boss_room.y, nave.center[0])

    # Pillars in boss room — LOS blockers against Medusa's gaze
    for px, py in [(35, 41), (43, 41), (35, 45), (43, 45)]:
        tiles[py][px] = WALL

    # Exit passage
    exit_room = _carve_room(tiles, 68, 43, 4, 3)
    rooms.append(exit_room)
    _hline(tiles, boss_room.x + boss_room.width, exit_room.x, 43)
    tiles[exit_room.center[1]][exit_room.x + exit_room.width // 2] = STAIRS_DOWN

    dungeon = _make(tiles, rooms, 40)
    return dungeon, _spawn_boss(dungeon, 'medusa_gorgon', boss_room), []


# ---------------------------------------------------------------------------
# Level 60 -- Fafnir's Dragon Hoard
# ---------------------------------------------------------------------------

def _level_60_lair():
    """
    A vast underground cavern. Winding passages, a gold-littered hoard
    chamber, and the ancient dragon Fafnir coiled atop his treasure.
    """
    tiles = _blank()
    rooms = []

    # Cave entrance
    entry = _carve_room(tiles, 10, 5, 4, 3)
    rooms.append(entry)
    tiles[entry.y + 1][entry.center[0]] = STAIRS_UP

    # Twisting cave passages
    ante1 = _carve_room(tiles, 22, 5, 4, 3)
    _connect(tiles, entry, ante1)

    ante2 = _carve_room(tiles, 22, 16, 5, 4)
    _connect(tiles, ante1, ante2)

    ante3 = _carve_room(tiles, 38, 10, 4, 3)
    _connect(tiles, ante2, ante3)

    side1 = _carve_room(tiles, 10, 20, 4, 3)
    _connect(tiles, ante2, side1)

    side2 = _carve_room(tiles, 55, 10, 4, 3)
    _connect(tiles, ante3, side2)

    rooms.extend([ante1, ante2, ante3, side1, side2])

    # Wide central hoard chamber
    hoard = _carve_room(tiles, 42, 28, 14, 9)
    rooms.append(hoard)
    _connect(tiles, ante3, hoard)
    tiles[hoard.y - 1][hoard.center[0]] = DOOR

    # Stalagmites / treasure piles in the hoard
    for sx, sy in [(35, 25), (50, 30), (38, 33)]:
        tiles[sy][sx] = WALL

    # Treasure alcoves
    for ax, ay in [(20, 28), (20, 34), (64, 28), (64, 34)]:
        alcove = _carve_room(tiles, ax, ay, 4, 3)
        rooms.append(alcove)
        if ax < hoard.center[0]:
            _hline(tiles, alcove.x + alcove.width, hoard.x, ay)
        else:
            _hline(tiles, hoard.x + hoard.width, alcove.x, ay)

    # Dragon's lair (boss room) -- deepest part of the cavern
    boss_room = _carve_room(tiles, 42, 43, 12, 5)
    rooms.append(boss_room)
    _vline(tiles, hoard.y + hoard.height, boss_room.y, hoard.center[0])
    tiles[boss_room.y - 1][boss_room.center[0]] = DOOR

    # Rock formations -- cover to dig pits behind
    for rx, ry in [(36, 41), (36, 42), (48, 44), (48, 45)]:
        tiles[ry][rx] = WALL

    # Exit tunnel (narrow passage to the right)
    exit_room = _carve_room(tiles, 70, 43, 5, 3)
    rooms.append(exit_room)
    _hline(tiles, boss_room.x + boss_room.width, exit_room.x, boss_room.center[1])
    tiles[exit_room.center[1]][exit_room.x + exit_room.width // 2] = STAIRS_DOWN

    dungeon = _make(tiles, rooms, 60)
    return dungeon, _spawn_boss(dungeon, 'fafnir_dragon', boss_room), []


# ---------------------------------------------------------------------------
# Level 80 -- Fenrir's Frozen Hall
# ---------------------------------------------------------------------------

def _level_80_hall():
    """
    Asgard lies in ruins, frozen at the eve of Ragnarok.
    Fenrir, the great wolf, paces the collapsed throne room.
    """
    tiles = _blank()
    rooms = []

    # Main entrance gate
    entry = _carve_room(tiles, 39, 4, 8, 3)
    rooms.append(entry)
    tiles[entry.y + 1][entry.center[0]] = STAIRS_UP
    tiles[entry.y + entry.height - 1][entry.center[0]] = DOOR

    # Grand hall -- wide central passage
    hall = _carve_room(tiles, 39, 17, 12, 6)
    rooms.append(hall)
    _vline(tiles, entry.y + entry.height, hall.y, entry.center[0])

    # Altar of Odin
    tiles[hall.center[1]][hall.center[0]] = ALTAR

    # Side chambers (barracks / storerooms)
    for side_x, side_y in [(16, 12), (62, 12), (16, 22), (62, 22)]:
        side = _carve_room(tiles, side_x, side_y, 5, 3)
        rooms.append(side)
        _connect(tiles, hall, side)

    # Secondary hall
    hall2 = _carve_room(tiles, 39, 31, 12, 5)
    rooms.append(hall2)
    _vline(tiles, hall.y + hall.height, hall2.y, hall.center[0])
    tiles[hall2.y - 1][hall.center[0]] = DOOR

    # More side rooms off secondary hall
    for side_x, side_y in [(14, 31), (64, 31)]:
        side = _carve_room(tiles, side_x, side_y, 4, 3)
        rooms.append(side)
        _connect(tiles, hall2, side)

    # Throne room -- boss chamber
    boss_room = _carve_room(tiles, 39, 43, 14, 4)
    rooms.append(boss_room)
    _vline(tiles, hall2.y + hall2.height, boss_room.y, hall2.center[0])
    tiles[boss_room.y - 1][boss_room.center[0]] = DOOR

    # Frozen pillars -- crumbled ice columns for tactical cover
    for px, py in [(31, 42), (35, 44), (43, 44), (47, 42)]:
        tiles[py][px] = WALL

    # Ice patches -- slippery terrain (left, center, right)
    for ix, iy in [(27, 42), (27, 43), (28, 42), (28, 43), (28, 44),  # left patch
                   (38, 40), (39, 40), (40, 40), (38, 41), (39, 41), (40, 41),  # center
                   (49, 43), (49, 44), (50, 43), (50, 44), (50, 45), (51, 43)]:  # right
        tiles[iy][ix] = ICE

    # Collapsed exit (narrow opening on the right)
    exit_room = _carve_room(tiles, 70, 43, 4, 3)
    rooms.append(exit_room)
    _hline(tiles, boss_room.x + boss_room.width, exit_room.x, boss_room.center[1])
    tiles[exit_room.center[1]][exit_room.x + exit_room.width // 2] = STAIRS_DOWN

    dungeon = _make(tiles, rooms, 80)
    return dungeon, _spawn_boss(dungeon, 'fenrir_wolf', boss_room), []


# ---------------------------------------------------------------------------
# Level 100 -- Abaddon's Abyss
# ---------------------------------------------------------------------------

def _level_100_abyss():
    """
    The bottommost pit of creation. A void ringed by crumbling stone arches,
    converging on the throne of Abaddon, the Destroyer.

    Level 100 has no STAIRS_DOWN -- the Philosopher's Stone is placed here
    by the level manager. The player must defeat Abaddon and ascend to victory.
    """
    tiles = _blank()
    rooms = []

    # Entry: a narrow ledge descending into the pit
    entry = _carve_room(tiles, 39, 4, 5, 3)
    rooms.append(entry)
    tiles[entry.y + 1][entry.center[0]] = STAIRS_UP

    # Descent corridor
    _vline(tiles, entry.y + entry.height, 15, entry.center[0])

    # Outer ring of chambers around the void
    ring_rooms = []
    ring_positions = [
        (16, 15), (62, 15),  # North-left, North-right
        (10, 25), (68, 25),  # West, East
        (16, 35), (62, 35),  # South-left, South-right
    ]
    for rx, ry in ring_positions:
        r = _carve_room(tiles, rx, ry, 5, 3)
        ring_rooms.append(r)
        rooms.append(r)

    # Connect entry to the top-left ring room
    _connect(tiles, entry, ring_rooms[0])
    _connect(tiles, entry, ring_rooms[1])

    # Cross-connect the ring
    _connect(tiles, ring_rooms[0], ring_rooms[2])
    _connect(tiles, ring_rooms[1], ring_rooms[3])
    _connect(tiles, ring_rooms[2], ring_rooms[4])
    _connect(tiles, ring_rooms[3], ring_rooms[5])

    # Spoke corridors from ring to center
    center_x, center_y = 39, 28
    for rr in ring_rooms:
        rcx, rcy = rr.center
        # Spoke: go horizontal then vertical to center
        _hline(tiles, rcx, center_x, rcy)
        _vline(tiles, rcy, center_y, center_x)

    # Altar ring around the boss chamber (6 altars for holy fire prayers)
    for ax, ay in [
        (center_x - 8, center_y),
        (center_x + 8, center_y),
        (center_x, center_y - 8),
        (center_x, center_y + 8),
        (center_x - 6, center_y - 6),
        (center_x + 6, center_y - 6),
    ]:
        if 0 <= ay < _H and 0 <= ax < _W:
            tiles[ay][ax] = ALTAR

    # Boss arena -- the Void Throne
    boss_room = _carve_room(tiles, center_x, center_y, 10, 7)
    rooms.append(boss_room)

    # Crumbled void-throne remnants -- minimal cover against locust swarms
    tiles[27][37] = WALL
    tiles[29][41] = WALL

    # Stone bridges (spokes already carved) -- add doors
    tiles[boss_room.y - 1][boss_room.center[0]] = DOOR
    tiles[boss_room.y + boss_room.height][boss_room.center[0]] = DOOR
    tiles[boss_room.center[1]][boss_room.x - 1] = DOOR
    tiles[boss_room.center[1]][boss_room.x + boss_room.width] = DOOR

    # No STAIRS_DOWN -- this is the final level; Philosopher's Stone is spawned here
    # by LevelManager._place_stone(). We add an exit to the entry for tactical retreat.

    dungeon = _make(tiles, rooms, 100)
    return dungeon, _spawn_boss(dungeon, 'abaddon_destroyer', boss_room), []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _make(tiles, rooms, level):
    return Dungeon(tiles, rooms, _W, _H, level)


def generate_boss_level(level_num):
    """
    Return (dungeon, monsters, items) for the given boss level.
    Raises ValueError for non-boss levels.
    """
    if level_num == 20:
        return _level_20_labyrinth()
    if level_num == 40:
        return _level_40_temple()
    if level_num == 60:
        return _level_60_lair()
    if level_num == 80:
        return _level_80_hall()
    if level_num == 100:
        return _level_100_abyss()
    if level_num == COW_LEVEL:
        return _level_999_moo_moo_farm()
    raise ValueError(f"No boss level defined for level {level_num}")


# ---------------------------------------------------------------------------
# Level 999 -- Moo Moo Farm (Secret Cow Level)
# ---------------------------------------------------------------------------

def _level_999_moo_moo_farm():
    """
    The Moo Moo Farm. A vast open pasture filled with Hell Bovines.
    Fenced perimeter, open interior, Cow King in a pen at the far end.
    Portal back home in the entry area.
    """
    import random as rng
    from monster import Monster

    tiles = _blank()
    rooms = []

    # --- Main pasture: large open field (most of the map) ---
    pasture = _carve_room(tiles, 40, 25, 35, 20)
    rooms.append(pasture)

    # Entry area (bottom-left) — portal back
    tiles[pasture.y + pasture.height - 2][pasture.x + 3] = STAIRS_DOWN

    # Cow King's pen (top-right corner, walled off with a door)
    pen = _carve_room(tiles, 68, 8, 6, 4)
    rooms.append(pen)
    _connect(tiles, pasture, pen)
    # Door into the pen
    _pen_door_x = pen.x + pen.width // 2
    _pen_door_y = pen.y + pen.height - 1
    if tiles[_pen_door_y][_pen_door_x] == FLOOR:
        tiles[_pen_door_y][_pen_door_x] = DOOR

    # Scatter some fence posts (wall pillars) across the pasture for cover
    _fence_positions = [
        (15, 12), (25, 12), (35, 12), (55, 12), (65, 12),
        (15, 25), (25, 25), (45, 25), (55, 25), (65, 25),
        (15, 38), (30, 38), (45, 38), (60, 38),
        (20, 18), (40, 18), (60, 18),
        (20, 32), (40, 32), (60, 32),
    ]
    for fx, fy in _fence_positions:
        if (pasture.x < fx < pasture.x + pasture.width - 1
                and pasture.y < fy < pasture.y + pasture.height - 1):
            tiles[fy][fx] = WALL

    dungeon = _make(tiles, rooms, COW_LEVEL)

    # --- Spawn Hell Bovines ---
    monsters = []
    bovine_defn = _load_boss('hell_bovine')
    if bovine_defn:
        # Place 40-50 bovines in the pasture
        bovine_count = rng.randint(40, 50)
        placed = 0
        inner = list(pasture.inner_tiles())
        rng.shuffle(inner)
        for bx, by in inner:
            if placed >= bovine_count:
                break
            if tiles[by][bx] != FLOOR:
                continue
            # Don't place on the exit portal
            if tiles[by][bx] == STAIRS_DOWN:
                continue
            if any(m.x == bx and m.y == by for m in monsters):
                continue
            m = Monster({**bovine_defn}, bx, by)
            monsters.append(m)
            placed += 1

    # --- Spawn Cow King in his pen ---
    king_defn = _load_boss('cow_king')
    if king_defn:
        kcx, kcy = pen.center
        king = Monster({**king_defn}, kcx, kcy)
        king.is_boss = True
        monsters.append(king)

    # Atmosphere
    dungeon.atmosphere_messages = [
        "The air smells of hay and brimstone.",
        "You hear an ominous chorus of mooing.",
        "Welcome to the Moo Moo Farm.",
    ]

    return dungeon, monsters, []


def _make(tiles, rooms, level):
    """Create a Dungeon object from tiles and rooms."""
    return Dungeon(tiles, rooms, _W, _H, level)
