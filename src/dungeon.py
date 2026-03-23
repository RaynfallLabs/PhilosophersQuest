"""
Dungeon generation using Binary Space Partitioning (BSP).

BSP guarantees:
  - No overlapping rooms
  - Every room is reachable (corridors connect every sibling pair)
  - Natural, evenly-distributed room placement

After BSP placement the generator runs post-processing passes for:
  - Doors      at corridor/room junctions (70% chance)
  - Secret doors in shortcut wall gaps between parallel corridors
  - Stairs up (first room) and stairs down (last room)
"""

import copy
import json
import os
import random
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Tile constants
# ---------------------------------------------------------------------------

WALL        = 0   # impassable, opaque
FLOOR       = 1   # passable, transparent
STAIRS_UP   = 2   # exit to previous level
STAIRS_DOWN = 3   # exit to next level
DOOR        = 4   # opaque until opened (bump to open)
SECRET_DOOR = 5   # looks like WALL; discovered by searching or bumping
ALTAR       = 6   # sacred altar; walkable, amplifies prayers
WATER       = 7   # blocks movement unless water_walking; transparent
LAVA        = 8   # instant damage without fire_resist; transparent; glows
FOUNTAIN    = 9   # walkable, interactive (quaff for quiz-gated effects)
GRAVE       = 10  # walkable, interactive (dig for items, may spawn undead)
THRONE      = 11  # walkable, interactive (sit for quiz-gated effects)
ICE         = 12  # walkable but slippery (random slide); transparent

# ---------------------------------------------------------------------------
# Trap definitions
# ---------------------------------------------------------------------------

TRAP_TYPES = [
    {'type': 'pit',          'damage': '2d6',   'damage_type': 'physical', 'message': 'You fall into a pit!',                         'symbol': '^', 'color': (150, 75, 0)},
    {'type': 'arrow',        'damage': '1d6+2', 'damage_type': 'pierce',   'message': 'An arrow fires from the wall!',                 'symbol': '^', 'color': (180, 140, 80)},
    {'type': 'alarm',        'damage': '0',     'damage_type': 'none',     'message': 'A pressure plate triggers an alarm!',           'symbol': '^', 'color': (200, 50, 50)},
    {'type': 'acid',         'damage': '2d4',   'damage_type': 'acid',     'message': 'Acid sprays from a nozzle!',                    'symbol': '^', 'color': (100, 200, 50)},
    {'type': 'teleport',     'damage': '0',     'damage_type': 'none',     'message': 'The floor vanishes -- you teleport!',           'symbol': '^', 'color': (100, 100, 220)},
    {'type': 'fire',         'damage': '2d4+2', 'damage_type': 'fire',     'message': 'A column of flame erupts beneath you!',         'symbol': '^', 'color': (255, 100, 30)},
    {'type': 'sleep_gas',    'damage': '0',     'damage_type': 'none',     'message': 'A cloud of sleeping gas envelops you!',         'symbol': '^', 'color': (150, 200, 150)},
    {'type': 'bear_trap',    'damage': '1d4',   'damage_type': 'physical', 'message': 'A bear trap snaps shut on your leg!',           'symbol': '^', 'color': (160, 160, 160)},
    {'type': 'squeaky_board','damage': '0',     'damage_type': 'none',     'message': 'SQUEEEAK! The floorboard alerts everything!',   'symbol': '^', 'color': (180, 140, 60)},
    {'type': 'rust',         'damage': '0',     'damage_type': 'none',     'message': 'Water sprays from the ceiling!',                'symbol': '^', 'color': (80, 130, 200)},
    {'type': 'polymorph',    'damage': '0',     'damage_type': 'none',     'message': 'Strange energies wash over you!',               'symbol': '^', 'color': (200, 50, 200)},
]

# ---------------------------------------------------------------------------
# BSP tuning
# ---------------------------------------------------------------------------

_BSP_MIN_LEAF  = 8    # minimum region dimension before splitting stops
_ROOM_PAD      = 1    # minimum tiles between room edge and region edge
_ROOM_MIN_INNER = 4   # minimum interior (floor) tiles per axis
_ROOM_MAX_INNER = 11  # maximum interior tiles per axis

# Boss levels — skip maze generation and special terrain on these
_BOSS_LEVELS = {20, 40, 60, 80, 100}


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------

@dataclass
class Room:
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def inner_tiles(self):
        """Yields every floor tile inside this room (excluding the outer wall ring)."""
        for ry in range(self.y + 1, self.y + self.height - 1):
            for rx in range(self.x + 1, self.x + self.width - 1):
                yield rx, ry

    def wall_tiles(self):
        """Yields every tile on the outer border of this room."""
        for x in range(self.x, self.x + self.width):
            yield x, self.y
            yield x, self.y + self.height - 1
        for y in range(self.y + 1, self.y + self.height - 1):
            yield self.x, y
            yield self.x + self.width - 1, y

    def intersects(self, other: 'Room', pad: int = 1) -> bool:
        return (
            self.x - pad < other.x + other.width  and
            self.x + self.width  + pad > other.x  and
            self.y - pad < other.y + other.height and
            self.y + self.height + pad > other.y
        )


# ---------------------------------------------------------------------------
# Dungeon
# ---------------------------------------------------------------------------

class Dungeon:
    def __init__(self, tiles: List[List[int]], rooms: List[Room],
                 width: int, height: int, level: int):
        self.tiles  = tiles
        self.rooms  = rooms
        self.width  = width
        self.height = height
        self.level  = level
        # Explored tiles stored as a set of (x, y) tuples for easy membership checks
        self.explored: Set[Tuple[int, int]] = set()
        # Hidden chambers carved adjacent to existing corridors/rooms
        self.hidden_chambers: list = []  # list of {'room': Room, 'type': str, 'theme': str}
        # Floor traps: (x, y) -> trap definition dict
        self.traps: dict = {}
        # Special rooms: (cx, cy) -> type string ('treasury', 'library', 'shrine', 'monster_den', ...)
        self.special_rooms: dict = {}
        # Vault: {'room': Room, 'door': (x, y)} or None
        self.vault = None
        # Dark rooms: set of (room_center_x, room_center_y) tuples
        self.dark_rooms: Set[Tuple[int, int]] = set()
        # Atmospheric messages from special features on this level
        self.atmosphere_messages: List[str] = []
        # True if this level is a maze instead of BSP rooms
        self.is_maze: bool = False
        # Phasing walls: wall tiles certain monsters (Asterion) can walk through
        self.phasing_walls: Set[Tuple[int, int]] = set()
        # Ariadne quest: shrine room door position (None until quest activated)
        self.ariadne_shrine_door: tuple = None
        self.ariadne_shrine_thread_pos: tuple = None
        # Athena quest: shrine room for Aegis (Medusa quest)
        self.athena_shrine_door: tuple = None
        self.athena_shrine_aegis_pos: tuple = None
        # Odin quest: altar position and shrine for Shovel (Fafnir quest)
        self.odin_altar_pos: tuple = None
        self.odin_shrine_door: tuple = None
        # Pit traps dug by the player (set of (x,y))
        self.pits: Set[Tuple[int, int]] = set()
        # Fenrir quest: Dwarven Forge and Vidar's Altar positions
        self.dwarven_forge_pos: tuple = None
        self.vidar_altar_pos: tuple = None

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """True if the player / monster can freely move onto this tile.
        Doors and secret doors block movement until explicitly opened.
        WATER and LAVA are hazard tiles that block normal movement."""
        return (self.in_bounds(x, y) and
                self.tiles[y][x] not in (WALL, DOOR, SECRET_DOOR, WATER, LAVA))

    def is_altar(self, x: int, y: int) -> bool:
        """True if this tile is a sacred altar."""
        return self.in_bounds(x, y) and self.tiles[y][x] == ALTAR

    def is_opaque(self, x: int, y: int) -> bool:
        """True if the tile blocks line-of-sight (for FOV).
        New terrain tiles (WATER, LAVA, FOUNTAIN, GRAVE, THRONE, ICE) are all transparent."""
        return (not self.in_bounds(x, y)
                or self.tiles[y][x] in (WALL, DOOR, SECRET_DOOR))

    def open_door(self, x: int, y: int) -> bool:
        """Open a closed door or reveal a secret door.  Returns True on success."""
        if self.in_bounds(x, y) and self.tiles[y][x] in (DOOR, SECRET_DOOR):
            self.tiles[y][x] = FLOOR
            return True
        return False

    def is_water(self, x: int, y: int) -> bool:
        """True if this tile is a water tile."""
        return self.in_bounds(x, y) and self.tiles[y][x] == WATER

    def is_lava(self, x: int, y: int) -> bool:
        """True if this tile is a lava tile."""
        return self.in_bounds(x, y) and self.tiles[y][x] == LAVA

    def is_fountain(self, x: int, y: int) -> bool:
        """True if this tile is a fountain."""
        return self.in_bounds(x, y) and self.tiles[y][x] == FOUNTAIN

    def is_grave(self, x: int, y: int) -> bool:
        """True if this tile is a grave."""
        return self.in_bounds(x, y) and self.tiles[y][x] == GRAVE

    def is_throne(self, x: int, y: int) -> bool:
        """True if this tile is a throne."""
        return self.in_bounds(x, y) and self.tiles[y][x] == THRONE


# ---------------------------------------------------------------------------
# BSP node
# ---------------------------------------------------------------------------

class _BSPNode:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left:  Optional['_BSPNode'] = None
        self.right: Optional['_BSPNode'] = None
        self.room:  Optional[Room]       = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None

    def split(self, rng: random.Random) -> bool:
        if not self.is_leaf:
            return False

        # Prefer splitting the longer axis; fall back to random
        if   self.w > self.h * 1.25:
            horiz = False
        elif self.h > self.w * 1.25:
            horiz = True
        else:
            horiz = rng.random() < 0.5

        dim = self.h if horiz else self.w
        if dim < _BSP_MIN_LEAF * 2:
            return False

        split = rng.randint(_BSP_MIN_LEAF, dim - _BSP_MIN_LEAF)
        if horiz:
            self.left  = _BSPNode(self.x, self.y,         self.w, split)
            self.right = _BSPNode(self.x, self.y + split, self.w, self.h - split)
        else:
            self.left  = _BSPNode(self.x,         self.y, split,          self.h)
            self.right = _BSPNode(self.x + split,  self.y, self.w - split, self.h)
        return True

    def get_room(self) -> Optional[Room]:
        """Return any room in this subtree (depth-first, left-preferred)."""
        if self.room:
            return self.room
        lr = self.left.get_room()  if self.left  else None
        rr = self.right.get_room() if self.right else None
        return lr or rr

    def leaves(self):
        if self.is_leaf:
            yield self
        else:
            yield from self.left.leaves()
            yield from self.right.leaves()


# ---------------------------------------------------------------------------
# Public generator
# ---------------------------------------------------------------------------

def generate_dungeon(width: int = 80, height: int = 50, level: int = 1) -> Dungeon:
    """
    Generate a complete dungeon level using BSP + post-processing passes.
    Every room is guaranteed to be connected.  Room count scales with depth.
    On every 10th non-boss level (10, 30, 50, 70, 90), a maze is generated instead.
    """
    rng   = random.Random()
    is_boss = level in _BOSS_LEVELS

    # -- Maze levels (every 10th level that is not a boss level) --------------
    if level % 10 == 0 and not is_boss:
        return _generate_maze_dungeon(width, height, level, rng)

    tiles = [[WALL] * width for _ in range(height)]

    # -- 1. BSP partitioning --------------------------------------------------
    root   = _BSPNode(1, 1, width - 2, height - 2)
    queue  = [root]
    target = min(5 + level, 14)

    for _ in range(target * 4):
        leaves = [n for n in queue if n.is_leaf and max(n.w, n.h) >= _BSP_MIN_LEAF * 2]
        if not leaves or sum(1 for n in queue if n.is_leaf) >= target:
            break
        node = rng.choice(leaves)
        if node.split(rng):
            queue.append(node.left)
            queue.append(node.right)

    # -- 2. Place one room in each BSP leaf -----------------------------------
    rooms: List[Room] = []
    for leaf in root.leaves():
        room = _room_in_leaf(leaf, rng)
        if room:
            leaf.room = room
            rooms.append(room)
            for rx, ry in room.inner_tiles():
                tiles[ry][rx] = FLOOR

    # -- 3. Connect sibling pairs up the BSP tree -----------------------------
    _connect_bsp(root, tiles, rng)

    # -- 4. Place doors at room-wall openings ---------------------------------
    _place_doors(tiles, rooms, rng, chance=0.70)

    # -- 5. Place secret doors (shortcuts) ------------------------------------
    _place_secret_doors(tiles, width, height, rooms, rng, level)

    # -- 5b. Carve hidden chambers off existing corridors/rooms ---------------
    hidden_chambers = _place_hidden_chambers(tiles, rooms, width, height, rng, level)

    # -- 6. Place stairs ------------------------------------------------------
    if len(rooms) >= 2:
        sx, sy = rooms[0].center
        tiles[sy][sx] = STAIRS_UP
        ex, ey = rooms[-1].center
        tiles[ey][ex] = STAIRS_DOWN
    elif rooms:
        cx, cy = rooms[0].center
        tiles[cy][cx] = STAIRS_UP

    # -- 7. Place altar (one per 15 levels: level 1, 16, 31, 46, ...) ---------
    if level % 15 == 1 and len(rooms) >= 2:
        # Place altar in a random room (not the first room where player starts)
        altar_room = rng.choice(rooms[1:])
        inner = [
            (tx, ty) for tx, ty in altar_room.inner_tiles()
            if tiles[ty][tx] == FLOOR
        ]
        if inner:
            ax, ay = rng.choice(inner)
            tiles[ay][ax] = ALTAR

    dungeon = Dungeon(tiles, rooms, width, height, level)
    dungeon.hidden_chambers = hidden_chambers

    # -- 8. Terrain passes (non-boss levels only) -----------------------------
    if not is_boss:
        _apply_terrain(dungeon, level, rng)

    # -- 9. Vault generation --------------------------------------------------
    if not is_boss:
        _try_place_vault(dungeon, level, rng)

    # -- 10. Dark rooms -------------------------------------------------------
    if not is_boss and level >= 5:
        _assign_dark_rooms(dungeon, level, rng)

    # -- 11. Atmosphere messages ----------------------------------------------
    _build_atmosphere(dungeon)

    return dungeon


# ---------------------------------------------------------------------------
# Maze level generation
# ---------------------------------------------------------------------------

def _generate_maze_dungeon(width: int, height: int, level: int,
                           rng: random.Random) -> 'Dungeon':
    """Generate a maze level using recursive backtracking, with a few room clearings."""
    tiles = [[WALL] * width for _ in range(height)]
    _generate_maze(tiles, width, height, level, rng)

    # Collect all floor tiles to identify rooms/open areas
    floor_tiles = [(x, y)
                   for y in range(1, height - 1)
                   for x in range(1, width - 1)
                   if tiles[y][x] == FLOOR]

    # Build synthetic Room objects from the carved clearings we remember
    # (populated inside _generate_maze as a side-channel via returned list)
    rooms = _find_maze_rooms(tiles, width, height)

    # Ensure stairs exist
    if len(rooms) >= 2:
        sx, sy = rooms[0].center
        tiles[sy][sx] = STAIRS_UP
        ex, ey = rooms[-1].center
        tiles[ey][ex] = STAIRS_DOWN
    elif floor_tiles:
        fx, fy = floor_tiles[0]
        tiles[fy][fx] = STAIRS_UP
        if len(floor_tiles) > 1:
            ex, ey = floor_tiles[-1]
            tiles[ey][ex] = STAIRS_DOWN

    # Place doors at dead-end corridors (simulates NetHack maze doors)
    _place_maze_doors(tiles, width, height, rng, chance=0.25)

    dungeon = Dungeon(tiles, rooms, width, height, level)
    dungeon.is_maze = True

    # Apply terrain and dark rooms to mazes too
    _apply_terrain(dungeon, level, rng)
    _try_place_vault(dungeon, level, rng)
    _assign_dark_rooms(dungeon, level, rng)
    _build_atmosphere(dungeon)

    return dungeon


def _generate_maze(tiles: List[List[int]], width: int, height: int,
                   level: int, rng: random.Random):
    """
    Recursive backtracking maze carved on an odd-coordinate grid.
    Works on tiles in-place.  Also carves 3-5 random room clearings.
    """
    # Work on odd coordinates so every cell is separated by a wall cell
    # Grid cells are at (1, 1), (1, 3), (3, 1), ... up to the odd boundary
    mw = (width  - 1) // 2
    mh = (height - 1) // 2

    visited = [[False] * mw for _ in range(mh)]

    def cell_to_tile(cx, cy):
        return cx * 2 + 1, cy * 2 + 1

    def carve(cx, cy):
        visited[cy][cx] = True
        tx, ty = cell_to_tile(cx, cy)
        tiles[ty][tx] = FLOOR
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        rng.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < mw and 0 <= ny < mh and not visited[ny][nx]:
                # Carve wall between current and neighbour
                wx, wy = tx + dx, ty + dy
                tiles[wy][wx] = FLOOR
                carve(nx, ny)

    # Start from a random cell
    start_cx = rng.randint(0, mw - 1)
    start_cy = rng.randint(0, mh - 1)

    import sys
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, mw * mh * 2 + 500))
    try:
        carve(start_cx, start_cy)
    finally:
        sys.setrecursionlimit(old_limit)

    # Carve 3-5 room clearings scattered through the maze
    num_clearings = rng.randint(3, 5)
    for _ in range(num_clearings):
        cw = rng.randint(3, 5)
        ch = rng.randint(3, 5)
        cx = rng.randint(2, width  - cw - 2)
        cy = rng.randint(2, height - ch - 2)
        for ry in range(cy, cy + ch):
            for rx in range(cx, cx + cw):
                tiles[ry][rx] = FLOOR


def _find_maze_rooms(tiles: List[List[int]], width: int, height: int) -> List[Room]:
    """
    Find rectangular open areas in a maze to use as Room objects for
    item/monster placement.  Returns a small list of non-overlapping pseudo-Rooms.
    """
    rooms = []
    claimed: Set[Tuple[int, int]] = set()

    for y in range(1, height - 3):
        for x in range(1, width - 3):
            if (x, y) in claimed:
                continue
            if tiles[y][x] != FLOOR:
                continue
            # Expand right as far as FLOOR goes (up to 5 wide)
            w = 1
            while w < 5 and x + w < width - 1 and tiles[y][x + w] == FLOOR:
                w += 1
            # Expand down as far as all columns are FLOOR (up to 5 tall)
            h = 1
            while h < 5 and y + h < height - 1:
                if all(tiles[y + h][x + dx] == FLOOR for dx in range(w)):
                    h += 1
                else:
                    break
            if w < 3 or h < 3:
                continue
            # Check none of these tiles are already claimed
            area = [(x + dx, y + dy) for dy in range(h) for dx in range(w)]
            if any(t in claimed for t in area):
                continue
            # Accept this room
            room = Room(x - 1, y - 1, w + 2, h + 2)
            rooms.append(room)
            claimed.update(area)

    # Fallback: create a small pseudo-room around any unclaimed floor tile
    if not rooms:
        floor_tiles = [(fx, fy)
                       for fy in range(1, height - 1)
                       for fx in range(1, width - 1)
                       if tiles[fy][fx] == FLOOR]
        if floor_tiles:
            mid = len(floor_tiles) // 2
            for fx, fy in [floor_tiles[0], floor_tiles[mid], floor_tiles[-1]]:
                rooms.append(Room(max(0, fx - 1), max(0, fy - 1), 3, 3))
    return rooms


def _place_maze_doors(tiles: List[List[int]], width: int, height: int,
                      rng: random.Random, chance: float = 0.25):
    """Place doors at dead-end passages in the maze."""
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if tiles[y][x] != FLOOR:
                continue
            # Count floor neighbours
            nbrs = sum(
                1 for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]
                if tiles[y + dy][x + dx] == FLOOR
            )
            # Dead end: exactly 1 floor neighbour
            if nbrs == 1 and rng.random() < chance:
                tiles[y][x] = DOOR


# ---------------------------------------------------------------------------
# Terrain passes
# ---------------------------------------------------------------------------

def _apply_terrain(dungeon: 'Dungeon', level: int, rng: random.Random):
    """Apply terrain features: fountains, water pools, lava rivers, ice rooms."""
    tiles = dungeon.tiles
    rooms = dungeon.rooms
    width = dungeon.width
    height = dungeon.height
    has_water = False
    has_lava  = False

    # -- Fountains: 1 per ~5 levels (20% chance per level) --------------------
    if rng.random() < 0.20 and len(rooms) >= 2:
        # Pick a random non-start room
        fountain_room = rng.choice(rooms[1:])
        candidates = [(fx, fy) for fx, fy in fountain_room.inner_tiles()
                      if tiles[fy][fx] == FLOOR]
        if candidates:
            fx, fy = rng.choice(candidates)
            tiles[fy][fx] = FOUNTAIN

    # -- Water pools: L10+, 15% chance ----------------------------------------
    if level >= 10 and rng.random() < 0.15 and len(rooms) >= 2:
        water_room = rng.choice(rooms[1:])
        inner = list(water_room.inner_tiles())
        # Flood edges first, then ~30% of remaining tiles
        edge_tiles = [(x, y) for x, y in inner
                      if (x == water_room.x + 1 or x == water_room.x + water_room.width - 2
                          or y == water_room.y + 1 or y == water_room.y + water_room.height - 2)]
        center_tiles = [t for t in inner if t not in edge_tiles]
        for x, y in edge_tiles:
            if tiles[y][x] == FLOOR:
                tiles[y][x] = WATER
                has_water = True
        for x, y in center_tiles:
            if tiles[y][x] == FLOOR and rng.random() < 0.30:
                tiles[y][x] = WATER
                has_water = True

    # -- Lava rivers: L30+, 20% chance ----------------------------------------
    if level >= 30 and not dungeon.is_maze and rng.random() < 0.20:
        # Find a corridor-ish region by picking a floor tile not in any room
        room_tiles: Set[Tuple[int, int]] = set()
        for room in rooms:
            for t in room.inner_tiles():
                room_tiles.add(t)
        corridor_floor = [(x, y)
                          for y in range(1, height - 1)
                          for x in range(1, width - 1)
                          if tiles[y][x] == FLOOR and (x, y) not in room_tiles]
        if corridor_floor:
            anchor = rng.choice(corridor_floor)
            ax, ay = anchor
            river_w = rng.randint(1, 2)
            horiz   = rng.random() < 0.5
            placed_lava = False
            if horiz:
                for x in range(max(1, ax - 8), min(width - 1, ax + 9)):
                    for dy in range(river_w):
                        ry = ay + dy
                        if 0 < ry < height - 1 and tiles[ry][x] == FLOOR:
                            tiles[ry][x] = LAVA
                            placed_lava = True
            else:
                for y in range(max(1, ay - 8), min(height - 1, ay + 9)):
                    for dx in range(river_w):
                        rx = ax + dx
                        if 0 < rx < width - 1 and tiles[y][rx] == FLOOR:
                            tiles[y][rx] = LAVA
                            placed_lava = True
            if placed_lava:
                has_lava = True

    # -- Ice rooms: L40+, 10% chance ------------------------------------------
    if level >= 40 and rng.random() < 0.10 and len(rooms) >= 2:
        ice_room = rng.choice(rooms[1:])
        for ix, iy in ice_room.inner_tiles():
            if tiles[iy][ix] == FLOOR:
                tiles[iy][ix] = ICE

    # Store flags for atmosphere building
    dungeon._has_water = has_water
    dungeon._has_lava  = has_lava


# ---------------------------------------------------------------------------
# Vault placement
# ---------------------------------------------------------------------------

def _try_place_vault(dungeon: 'Dungeon', level: int, rng: random.Random):
    """
    20% chance per level (if 6+ rooms) to carve an isolated vault.
    Vault: 4x4 room (2x2 interior) surrounded by walls, connected via one DOOR.
    Stores info in dungeon.vault = {'room': Room, 'door': (x, y)}.
    """
    if len(dungeon.rooms) < 6 or rng.random() >= 0.20:
        return

    tiles  = dungeon.tiles
    width  = dungeon.width
    height = dungeon.height

    # Try to find a wall-only 4x4 region adjacent to an existing floor tile
    # The vault room is 4 wide x 4 tall (2x2 interior + 1-tile walls on all sides)
    VAULT_W = 4
    VAULT_H = 4

    attempts = 0
    while attempts < 300:
        attempts += 1
        vx = rng.randint(2, width  - VAULT_W - 2)
        vy = rng.randint(2, height - VAULT_H - 2)

        # All tiles in vault bounding box must be WALL
        if not all(tiles[ry][rx] == WALL
                   for ry in range(vy, vy + VAULT_H)
                   for rx in range(vx, vx + VAULT_W)):
            continue

        # Find a FLOOR neighbor just outside one of the 4 faces
        door_candidates = []
        # Top face: row vy, columns vx..vx+VAULT_W-1 -> neighbour row vy-1
        for dx in range(VAULT_W):
            nx, ny = vx + dx, vy - 1
            if 0 < nx < width - 1 and 0 < ny < height - 1 and tiles[ny][nx] == FLOOR:
                door_candidates.append(('top', vx + dx, vy, nx, ny))
        # Bottom face
        for dx in range(VAULT_W):
            nx, ny = vx + dx, vy + VAULT_H
            if 0 < nx < width - 1 and 0 < ny < height - 1 and tiles[ny][nx] == FLOOR:
                door_candidates.append(('bottom', vx + dx, vy + VAULT_H - 1, nx, ny))
        # Left face
        for dy in range(VAULT_H):
            nx, ny = vx - 1, vy + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and tiles[ny][nx] == FLOOR:
                door_candidates.append(('left', vx, vy + dy, nx, ny))
        # Right face
        for dy in range(VAULT_H):
            nx, ny = vx + VAULT_W, vy + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and tiles[ny][nx] == FLOOR:
                door_candidates.append(('right', vx + VAULT_W - 1, vy + dy, nx, ny))

        if not door_candidates:
            continue

        _, door_x, door_y, _, _ = rng.choice(door_candidates)

        # Carve vault interior (2x2 floor inside the 4x4 box)
        for ry in range(vy + 1, vy + VAULT_H - 1):
            for rx in range(vx + 1, vx + VAULT_W - 1):
                tiles[ry][rx] = FLOOR

        # Place the single door
        tiles[door_y][door_x] = DOOR

        vault_room = Room(vx, vy, VAULT_W, VAULT_H)
        dungeon.vault = {'room': vault_room, 'door': (door_x, door_y)}
        return


# ---------------------------------------------------------------------------
# Dark rooms
# ---------------------------------------------------------------------------

def _assign_dark_rooms(dungeon: 'Dungeon', level: int, rng: random.Random):
    """Mark some rooms as dark — FOV will be limited to 1 tile inside them."""
    if level < 5:
        return
    chance = min(0.6, 0.1 + level * 0.005)
    for room in dungeon.rooms[1:]:  # never darken the start room
        if rng.random() < chance:
            dungeon.dark_rooms.add(room.center)


# ---------------------------------------------------------------------------
# Atmosphere messages
# ---------------------------------------------------------------------------

def _build_atmosphere(dungeon: 'Dungeon'):
    """Populate dungeon.atmosphere_messages based on features present."""
    msgs = dungeon.atmosphere_messages

    for room_type in dungeon.special_rooms.values():
        if room_type == 'zoo':
            msgs.append("You hear exotic roars in the distance...")
        elif room_type == 'graveyard':
            msgs.append("The air grows cold and unnaturally quiet...")
        elif room_type == 'beehive':
            msgs.append("You hear a low, persistent buzzing...")
        elif room_type == 'barracks':
            msgs.append("You hear the sound of blades being sharpened...")
        elif room_type == 'swamp':
            msgs.append("The stench of marsh gas fills your nostrils...")
        elif room_type == 'throne_room':
            msgs.append("You sense an aura of ancient authority...")

    if dungeon.vault is not None:
        msgs.append("You hear someone counting coins behind a wall...")

    if getattr(dungeon, '_has_lava', False):
        msgs.append("The air shimmers with intense heat...")

    if getattr(dungeon, '_has_water', False):
        msgs.append("You hear the drip of water echoing...")


# ---------------------------------------------------------------------------
# BSP helpers
# ---------------------------------------------------------------------------

def _room_in_leaf(leaf: _BSPNode, rng: random.Random) -> Optional[Room]:
    """Fit a randomly-sized room inside the BSP leaf with padding."""
    max_w = min(leaf.w - _ROOM_PAD * 2, _ROOM_MAX_INNER + 2)
    max_h = min(leaf.h - _ROOM_PAD * 2, _ROOM_MAX_INNER + 2)
    min_w = _ROOM_MIN_INNER + 2  # +2 for the surrounding wall ring
    min_h = _ROOM_MIN_INNER + 2

    if max_w < min_w or max_h < min_h:
        return None

    rw = rng.randint(min_w, max_w)
    rh = rng.randint(min_h, max_h)
    rx = leaf.x + rng.randint(_ROOM_PAD, max(leaf.w - rw - _ROOM_PAD, _ROOM_PAD))
    ry = leaf.y + rng.randint(_ROOM_PAD, max(leaf.h - rh - _ROOM_PAD, _ROOM_PAD))
    return Room(rx, ry, rw, rh)


def _connect_bsp(node: _BSPNode, tiles: List[List[int]], rng: random.Random):
    """Recursively connect every pair of BSP siblings with a corridor."""
    if node.is_leaf:
        return
    _connect_bsp(node.left,  tiles, rng)
    _connect_bsp(node.right, tiles, rng)

    left_room  = node.left.get_room()
    right_room = node.right.get_room()
    if left_room and right_room:
        # Connect nearest edges rather than centers for shorter corridors
        x1, y1 = _nearest_edge_point(left_room, right_room, rng)
        x2, y2 = _nearest_edge_point(right_room, left_room, rng)
        _carve_corridor(tiles, x1, y1, x2, y2, rng)


def _nearest_edge_point(room: Room, target: Room, rng: random.Random) -> Tuple[int, int]:
    """Pick a point on room's interior edge closest to target's center."""
    tcx, tcy = target.center
    # Inner bounds of the room (floor area)
    x1 = room.x + 1
    y1 = room.y + 1
    x2 = room.x + room.width - 2
    y2 = room.y + room.height - 2
    # Clamp target center to room interior
    cx = max(x1, min(x2, tcx))
    cy = max(y1, min(y2, tcy))
    # Determine which edge to use based on target direction
    dx = tcx - (room.x + room.width // 2)
    dy = tcy - (room.y + room.height // 2)
    if abs(dx) >= abs(dy):
        # Connect horizontally: pick left or right wall
        ex = x2 if dx >= 0 else x1
        return (ex, cy)
    else:
        # Connect vertically: pick top or bottom wall
        ey = y2 if dy >= 0 else y1
        return (cx, ey)


def _carve_corridor(tiles, x1: int, y1: int, x2: int, y2: int, rng: random.Random):
    """Carve an L-shaped (or straight) corridor between two points."""
    if rng.random() < 0.5:
        _carve_h(tiles, x1, x2, y1)
        _carve_v(tiles, y1, y2, x2)
    else:
        _carve_v(tiles, y1, y2, x1)
        _carve_h(tiles, x1, x2, y2)


def _carve_h(tiles, x1: int, x2: int, y: int):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if tiles[y][x] == WALL:
            tiles[y][x] = FLOOR


def _carve_v(tiles, y1: int, y2: int, x: int):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if tiles[y][x] == WALL:
            tiles[y][x] = FLOOR


# ---------------------------------------------------------------------------
# Door placement
# ---------------------------------------------------------------------------

def _place_doors(tiles, rooms: List[Room], rng: random.Random, chance: float = 0.70):
    """
    A corridor enters a room by carving through the room's outer wall.
    Any room-wall tile that is FLOOR was carved by a corridor -- make it a DOOR.
    """
    for room in rooms:
        for wx, wy in room.wall_tiles():
            if tiles[wy][wx] == FLOOR:
                # Confirm it's a valid 1-tile passage (not a wide opening)
                # Count orthogonal floor neighbors -- a doorway has exactly 2
                floor_nbrs = sum(
                    1 for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]
                    if 0 <= wx+dx < len(tiles[0]) and 0 <= wy+dy < len(tiles)
                    and tiles[wy+dy][wx+dx] in (FLOOR, STAIRS_UP, STAIRS_DOWN)
                )
                if floor_nbrs >= 1 and rng.random() < chance:
                    tiles[wy][wx] = DOOR


# ---------------------------------------------------------------------------
# Secret door placement
# ---------------------------------------------------------------------------

def _place_secret_doors(tiles, width: int, height: int,
                        rooms: List[Room], rng: random.Random, level: int):
    """
    Place a handful of secret doors in WALL tiles that sit between two separate
    FLOOR regions (providing a hidden shortcut).  They look identical to WALL
    until the player discovers them by bumping or searching.
    """
    # Build a quick set of room-wall positions so we don't overlap with regular doors
    room_walls: Set[Tuple[int, int]] = set()
    for room in rooms:
        room_walls.update(room.wall_tiles())

    target   = max(2, 2 + level // 4)   # 2+ per level (was max(1, 1 + level // 3))
    placed   = 0
    attempts = 0

    while placed < target and attempts < 400:
        attempts += 1
        x = rng.randint(2, width  - 3)
        y = rng.randint(2, height - 3)

        if tiles[y][x] != WALL or (x, y) in room_walls:
            continue

        # Check for exactly-opposite floor neighbours (N/S or E/W) = shortcut gap
        ns = (tiles[y-1][x] == FLOOR and tiles[y+1][x] == FLOOR)
        ew = (tiles[y][x-1] == FLOOR and tiles[y][x+1] == FLOOR)

        if ns or ew:
            tiles[y][x] = SECRET_DOOR
            placed += 1


# ---------------------------------------------------------------------------
# Hidden chamber placement
# ---------------------------------------------------------------------------

def _place_hidden_chambers(tiles, rooms: List[Room], width: int, height: int,
                            rng: random.Random, level: int) -> list:
    """
    Try to carve 0-2 small hidden rooms adjacent to existing floor/corridor tiles.
    Each chamber is connected to the main dungeon via a SECRET_DOOR in the shared wall.
    Returns a list of chamber dicts: {'room': Room, 'type': str, 'theme': str}
    """
    # Lair themes by level range
    def _lair_theme(lvl: int) -> str:
        if lvl <= 8:
            return rng.choice(['rat_nest', 'spider_den', 'bat_cave'])
        elif lvl <= 18:
            return rng.choice(['goblin_camp', 'kobold_den', 'orc_hideout'])
        elif lvl <= 35:
            return rng.choice(['troll_cave', 'bandit_hideout', 'undead_crypt'])
        elif lvl <= 60:
            return rng.choice(['demon_shrine', 'yuan_ti_lair', 'vampire_crypt'])
        else:
            return rng.choice(['dragon_hoard', 'lich_sanctum', 'chaos_shrine'])

    # Candidate chamber sizes: (interior_w, interior_h)
    SIZES = [(5, 7), (7, 5), (6, 6)]

    chambers = []
    # Collect all floor tile positions to pick anchor points from
    floor_tiles = [
        (x, y)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if tiles[y][x] == FLOOR
    ]
    if not floor_tiles:
        return chambers

    rng.shuffle(floor_tiles)
    attempts = 0
    max_attempts = min(200, len(floor_tiles))
    target_count = rng.randint(0, 2)

    for ax, ay in floor_tiles:
        if len(chambers) >= target_count:
            break
        if attempts >= max_attempts:
            break
        attempts += 1

        # Try each direction the chamber could be placed (N/S/E/W of the anchor)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        rng.shuffle(directions)

        for ddx, ddy in directions:
            # Layout: anchor(FLOOR) -> door_tile(must be WALL -> SECRET_DOOR) -> chamber
            door_x = ax + ddx
            door_y = ay + ddy

            # The door tile must currently be WALL
            if not (0 < door_x < width - 1 and 0 < door_y < height - 1):
                continue
            if tiles[door_y][door_x] != WALL:
                continue

            # Pick a chamber size
            iw, ih = rng.choice(SIZES)
            # Full room including 1-tile wall border
            rw = iw + 2
            rh = ih + 2

            # The chamber bounding box starts one step past the door in the same direction.
            # The door_tile sits in the shared wall between anchor and chamber.
            # We position the chamber so the door is on its near face wall.
            if ddx == 0:
                # Moving vertically: door is on top wall (ddy=+1) or bottom wall (ddy=-1)
                cx = door_x - rw // 2
                if ddy == 1:
                    cy = door_y          # door is the top wall row of the chamber
                else:
                    cy = door_y - rh + 1  # door is the bottom wall row of the chamber
            else:
                # Moving horizontally: door on left wall (ddx=+1) or right wall (ddx=-1)
                cy = door_y - rh // 2
                if ddx == 1:
                    cx = door_x          # door is the left wall col of the chamber
                else:
                    cx = door_x - rw + 1  # door is the right wall col of the chamber

            # Bounds check
            if cx < 1 or cy < 1 or cx + rw >= width or cy + rh >= height:
                continue

            # All tiles in bounding box must currently be WALL
            # (the door tile is inside the box and is already confirmed WALL above)
            all_wall = True
            for ty2 in range(cy, cy + rh):
                for tx2 in range(cx, cx + rw):
                    if tiles[ty2][tx2] != WALL:
                        all_wall = False
                        break
                if not all_wall:
                    break
            if not all_wall:
                continue

            # Carve it: interior becomes FLOOR, border stays WALL (already WALL),
            # and we set the connecting wall tile to SECRET_DOOR.
            room = Room(cx, cy, rw, rh)
            for rx2, ry2 in room.inner_tiles():   # inner_tiles yields (x, y)
                tiles[ry2][rx2] = FLOOR
            tiles[door_y][door_x] = SECRET_DOOR

            # Classify: 60% treasure, 40% lair
            if rng.random() < 0.60:
                ctype = 'treasure'
                theme = 'cache'
            else:
                ctype = 'lair'
                theme = _lair_theme(level)

            chambers.append({'room': room, 'type': ctype, 'theme': theme})
            break  # placed one; move to next anchor

    return chambers


# ---------------------------------------------------------------------------
# Spawn helpers  (unchanged signatures -- called by level_manager)
# ---------------------------------------------------------------------------

def spawn_monsters(rooms: List[Room], level: int, dungeon: Dungeon,
                   min_count: int = None, max_count: int = None) -> list:
    """Spawn monsters in dungeon rooms (skips the first room).
    Count scales with dungeon level: 3-5 at level 1, up to 10-15 at level 50+."""
    from monster import Monster

    from paths import data_path
    monsters_path = data_path('data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)

    # Build weighted pool:
    #  - L1-29: original behavior (freq decays past max_level, floor at 1)
    #  - L30+: proximity weighting ramps up so deep floors spawn harder monsters
    #    * Monsters past max_level can decay to 0 (no floor)
    #    * On-level monsters get weight bonus that grows with depth
    eligible = {}
    use_proximity = level >= 30
    for k, v in all_defs.items():
        min_lv = v.get('min_level', 1)
        if min_lv > level:
            continue
        freq = v.get('frequency', 5)
        if freq <= 0:
            continue  # bosses / non-spawning
        max_lv = v.get('max_level', None)
        if max_lv is not None and level > max_lv:
            over = level - max_lv
            if use_proximity:
                freq = freq - over  # no floor: decays to 0
                if freq <= 0:
                    continue
            else:
                freq = max(1, freq - over)  # gentle: floor at 1
        if use_proximity:
            distance = level - min_lv
            # Ramp: 0 at L30, 3 at L60, 7 at L100
            prox_scale = max(0, (level - 30) // 10)
            if distance <= 5:
                freq *= (2 + prox_scale)        # on-level
            elif distance <= 15:
                freq *= max(1, 1 + prox_scale // 2)  # near-level
        eligible[k] = {**v, '_spawn_freq': freq}
    if not eligible:
        return []

    rng = random.Random()
    if min_count is None:
        min_count = min(4 + level // 10, 8)
    if max_count is None:
        max_count = min(6 + level // 5, 14)
    count    = rng.randint(min_count, max_count)
    monsters = []
    spawn_rooms = rooms[1:]

    for _ in range(count):
        if not spawn_rooms:
            break
        room  = rng.choice(spawn_rooms)
        tiles = list(room.inner_tiles())
        rng.shuffle(tiles)

        for tx, ty in tiles:
            if not dungeon.is_walkable(tx, ty):
                continue
            if any(m.x == tx and m.y == ty for m in monsters):
                continue
            kind = _weighted_choice(eligible, rng)
            defn = {**eligible[kind], 'id': kind}
            monsters.append(Monster(defn, tx, ty))

            # --- Pack spawning: spawn 2-3 extras of same type nearby ---
            if defn.get('pack', False):
                pack_extra = rng.randint(2, 3)
                for ptx, pty in tiles:
                    if pack_extra <= 0:
                        break
                    if not dungeon.is_walkable(ptx, pty):
                        continue
                    if any(m.x == ptx and m.y == pty for m in monsters):
                        continue
                    monsters.append(Monster({**defn}, ptx, pty))
                    pack_extra -= 1

            break

    return monsters


def spawn_items(rooms: List[Room], level: int, dungeon: Dungeon) -> list:
    """Spawn items, containers, and lockpicks in dungeon rooms."""
    from items import load_items, Container, Lockpick

    rng          = random.Random()
    ground_items = []

    # -- Regular items (weapons/armor/shield/accessories/wands/scrolls/ammo) -- 33% per room --
    templates: list = []
    for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll', 'spellbook', 'ammo'):
        try:
            templates += load_items(cls_name)
        except FileNotFoundError:
            pass

    eligible = _item_eligible_weighted(templates, level, rng)

    for room in rooms[1:]:
        if rng.random() > 0.33:
            continue
        _place_one(eligible, room, dungeon, ground_items, rng)

    # -- Containers -- guaranteed minimum 1; diminishing extras ----------------
    try:
        all_containers = load_items('container')
    except FileNotFoundError:
        all_containers = []

    _MIMIC_CHANCE = 0.08  # 8% of containers are secretly mimics

    eligible_containers = [c for c in all_containers if c.min_level <= level]
    if not eligible_containers:
        eligible_containers = all_containers[:]

    # Weight containers by frequency field
    total_freq = sum(getattr(c, 'quiz_threshold', 1) for c in eligible_containers) or 1

    def pick_container() -> Optional[Container]:
        if not eligible_containers:
            return None
        weights = [c.extra_item_chance for c in eligible_containers]
        chosen  = rng.choices(eligible_containers, weights=weights, k=1)[0]
        inst    = copy.copy(chosen)
        # Map dungeon level 1-100 to container tier 1-5, with +/-1 variance
        base_tier = max(1, min(5, (level - 1) // 20 + 1))
        inst.tier = max(1, min(5, base_tier + rng.randint(-1, 1)))
        inst.is_mimic = rng.random() < _MIMIC_CHANCE
        return inst

    # Guaranteed first container
    for room in rng.sample(rooms[1:], min(len(rooms) - 1, len(rooms) - 1)):
        c = pick_container()
        if c and _place_one([c], room, dungeon, ground_items, rng):
            break

    # Additional containers with diminishing probability
    extra_chance = 0.55
    for room in rng.sample(rooms[1:], min(len(rooms) - 1, len(rooms) - 1)):
        if rng.random() > extra_chance:
            continue
        c = pick_container()
        if c:
            _place_one([c], room, dungeon, ground_items, rng)
        extra_chance *= 0.45   # 0.55 -> 0.25 -> 0.11 -> ...

    # -- Lockpicks -- 1-2 per level, in random rooms -------------------------
    try:
        all_picks = load_items('lockpick')
    except FileNotFoundError:
        all_picks = []

    eligible_picks = [p for p in all_picks if p.min_level <= level] or all_picks[:]
    pick_count = rng.randint(1, 2)
    rooms_for_picks = rng.sample(rooms[1:], min(pick_count, len(rooms) - 1))
    for room in rooms_for_picks:
        _place_one(eligible_picks, room, dungeon, ground_items, rng)

    # -- Food -- 1-3 items scattered across rooms ------------------------------
    try:
        all_food = load_items('food')
    except FileNotFoundError:
        all_food = []

    eligible_food = _food_eligible(all_food, level)
    food_count = rng.randint(2, 4)
    food_rooms = rng.sample(rooms[1:], min(food_count, len(rooms) - 1))
    for room in food_rooms:
        _place_one(eligible_food, room, dungeon, ground_items, rng)

    # -- Potions -- 1-2 per level, weighted by floorSpawnWeight ----------------
    try:
        all_potions = load_items('potion')
    except FileNotFoundError:
        all_potions = []

    eligible_potions = _item_eligible_weighted(all_potions, level, rng)
    potion_count = rng.randint(1, 2)
    potion_rooms = rng.sample(rooms[1:], min(potion_count, len(rooms) - 1))
    for room in potion_rooms:
        _place_one(eligible_potions, room, dungeon, ground_items, rng)

    # -- Soul Spheres -- ~5% per floor ------------------------------------------
    if rng.random() < 0.05:
        from items import Artifact
        sphere = Artifact({
            'id': 'soul_sphere',
            'name': 'Soul Sphere',
            'symbol': 'O',
            'color': [255, 80, 80],
            'item_class': 'artifact',
            'weight': 0.5,
            'min_level': 1,
            'lore': 'A sphere of crimson and ivory that hums with trapped souls. '
                    'Ancient texts say these vessels were used to bind creature spirits. '
                    'One wonders what might happen if it were hurled with force...',
        })
        sphere_room = rng.choice(rooms[1:])
        _place_one([sphere], sphere_room, dungeon, ground_items, rng)

    # -- Mystery altars --------------------------------------------------------
    try:
        from mystery_system import spawn_mystery_for_level
        mystery_result = spawn_mystery_for_level(level, rooms, dungeon, ground_items, rng)
        if mystery_result:
            altar, key = mystery_result
            ground_items.append(altar)
            if key:
                ground_items.append(key)
    except Exception:
        pass  # mystery system is optional; don't crash dungeon gen on error

    # -- Travelling merchant ---------------------------------------------------
    try:
        from mystery_system import spawn_merchant
        merchant = spawn_merchant(level, rooms, dungeon, ground_items, rng)
        if merchant:
            ground_items.append(merchant)
    except Exception:
        pass  # merchant is optional; don't crash dungeon gen on error

    # -- Special rooms ---------------------------------------------------------
    SPECIAL_ROOM_CHANCE = 0.35
    if rng.random() < SPECIAL_ROOM_CHANCE and len(rooms) > 3:
        special_room = rng.choice(rooms[2:])
        cx, cy = special_room.center

        # Build level-gated candidate list
        candidates = ['treasury', 'library', 'shrine', 'monster_den']
        if level >= 5:
            candidates.append('zoo')
        if level >= 8:
            candidates.append('beehive')
        if level >= 10:
            candidates.append('graveyard')
        if level >= 12:
            candidates.append('barracks')
        if level >= 15:
            candidates.append('swamp')
        if level >= 18:
            candidates.append('throne_room')

        room_type = rng.choice(candidates)
        dungeon.special_rooms[(cx, cy)] = room_type

        if room_type == 'treasury':
            for _ in range(2):
                c = pick_container()
                if c:
                    _place_one([c], special_room, dungeon, ground_items, rng)
            gold_amount = rng.randint(level * 3, level * 8)
            tiles_in_room = [(tx, ty) for tx, ty in special_room.inner_tiles()
                             if dungeon.tiles[ty][tx] == FLOOR and
                             not any(i.x == tx and i.y == ty for i in ground_items)]
            if tiles_in_room:
                from items import GoldPile
                gx, gy = rng.choice(tiles_in_room)
                ground_items.append(GoldPile(gold_amount, gx, gy))

        elif room_type == 'library':
            try:
                scrolls = [i for i in load_items('scroll') if i.min_level <= level]
                books = [i for i in load_items('spellbook') if i.min_level <= level]
                for _ in range(3):
                    if scrolls:
                        _place_one([copy.copy(rng.choice(scrolls))], special_room, dungeon, ground_items, rng)
                if books and rng.random() < 0.5:
                    _place_one([copy.copy(rng.choice(books))], special_room, dungeon, ground_items, rng)
            except Exception:
                pass

        elif room_type == 'shrine':
            tiles_in_room = [(tx, ty) for tx, ty in special_room.inner_tiles()
                             if dungeon.tiles[ty][tx] == FLOOR]
            if tiles_in_room:
                ax, ay = rng.choice(tiles_in_room)
                dungeon.tiles[ay][ax] = ALTAR

        elif room_type == 'monster_den':
            # Extra monsters spawned by level_manager after spawn_items()
            pass

        elif room_type == 'zoo':
            # Gold piles on most inner tiles; message handled in main.py via special_rooms
            from items import GoldPile
            for tx, ty in special_room.inner_tiles():
                if dungeon.tiles[ty][tx] == FLOOR and rng.random() < 0.70:
                    amount = rng.randint(level * 2, level * 5)
                    if not any(i.x == tx and i.y == ty for i in ground_items):
                        ground_items.append(GoldPile(amount, tx, ty))

        elif room_type == 'graveyard':
            # Place GRAVE tiles on ~20% of inner floor tiles; also drop 1-2 corpses
            grave_count = 0
            for tx, ty in special_room.inner_tiles():
                if dungeon.tiles[ty][tx] == FLOOR and rng.random() < 0.20:
                    dungeon.tiles[ty][tx] = GRAVE
                    grave_count += 1
            # Place 1-2 corpse items on remaining floor tiles
            try:
                from food_system import make_corpse
                corpse_tiles = [(tx, ty) for tx, ty in special_room.inner_tiles()
                                if dungeon.tiles[ty][tx] == FLOOR
                                and not any(i.x == tx and i.y == ty for i in ground_items)]
                corpse_count = rng.randint(1, 2)
                for _ in range(min(corpse_count, len(corpse_tiles))):
                    if not corpse_tiles:
                        break
                    tx, ty = corpse_tiles.pop(rng.randint(0, len(corpse_tiles) - 1))
                    corpse = make_corpse('skeleton', tx, ty)
                    ground_items.append(corpse)
            except Exception:
                pass

        elif room_type == 'beehive':
            # Food items on ~30% of tiles
            if eligible_food:
                for tx, ty in special_room.inner_tiles():
                    if dungeon.tiles[ty][tx] == FLOOR and rng.random() < 0.30:
                        if not any(i.x == tx and i.y == ty for i in ground_items):
                            inst = copy.copy(rng.choice(eligible_food))
                            inst.x = tx
                            inst.y = ty
                            ground_items.append(inst)

        elif room_type == 'barracks':
            # 2-3 weapon/armor items
            barracks_items: list = []
            for cls_name in ('weapon', 'armor'):
                try:
                    barracks_items += [i for i in load_items(cls_name) if i.min_level <= level]
                except Exception:
                    pass
            count = rng.randint(2, 3)
            for _ in range(count):
                if barracks_items:
                    _place_one(barracks_items, special_room, dungeon, ground_items, rng)

        elif room_type == 'swamp':
            # Replace ~40% of inner tiles with WATER; spawn food on remaining floor
            for tx, ty in special_room.inner_tiles():
                if dungeon.tiles[ty][tx] == FLOOR and rng.random() < 0.40:
                    dungeon.tiles[ty][tx] = WATER
            # Food on remaining floor tiles
            if eligible_food:
                for tx, ty in special_room.inner_tiles():
                    if dungeon.tiles[ty][tx] == FLOOR and rng.random() < 0.25:
                        if not any(i.x == tx and i.y == ty for i in ground_items):
                            inst = copy.copy(rng.choice(eligible_food))
                            inst.x = tx
                            inst.y = ty
                            ground_items.append(inst)

        elif room_type == 'throne_room':
            # Place a THRONE tile at room center; place 1 container
            tcx, tcy = special_room.center
            if dungeon.tiles[tcy][tcx] == FLOOR:
                dungeon.tiles[tcy][tcx] = THRONE
            c = pick_container()
            if c:
                _place_one([c], special_room, dungeon, ground_items, rng)

    # -- Vault items (gold piles) -----------------------------------------------
    if dungeon.vault is not None:
        from items import GoldPile
        vault_room = dungeon.vault['room']
        for tx, ty in vault_room.inner_tiles():
            if dungeon.tiles[ty][tx] == FLOOR:
                amount = rng.randint(level * 5, level * 15)
                ground_items.append(GoldPile(amount, tx, ty))

    # -- Floor traps -----------------------------------------------------------
    start_center = rooms[0].center if rooms else (0, 0)
    n_traps = rng.randint(1, min(3, 1 + level // 20))
    trap_candidates = []
    for ry in range(dungeon.height):
        for rx in range(dungeon.width):
            if (dungeon.tiles[ry][rx] == FLOOR
                    and (rx, ry) != start_center
                    and not any(i.x == rx and i.y == ry for i in ground_items)):
                trap_candidates.append((rx, ry))
    rng.shuffle(trap_candidates)
    for tx, ty in trap_candidates[:n_traps]:
        trap = dict(rng.choice(TRAP_TYPES))
        trap['revealed'] = False
        dungeon.traps[(tx, ty)] = trap

    # -- Ariadne quest items ---------------------------------------------------
    # Bronze Bull: guaranteed single spawn on one level in L10-15
    if level == 12:
        from items import Artifact
        bull = Artifact({
            'id': 'bronze_bull',
            'name': 'Bronze Bull Idol',
            'symbol': '!',
            'color': [180, 120, 60],
            'item_class': 'artifact',
            'weight': 0.5,
            'min_level': 10,
        })
        bull_room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        if not _place_one([bull], bull_room, dungeon, ground_items, rng):
            _force_place_quest_item(bull, dungeon, ground_items)

    # Ariadne shrine: guaranteed single creation on L17
    if level == 17:
        _create_ariadne_shrine(dungeon, rooms, ground_items, rng)

    # -- Athena quest items (Medusa) -------------------------------------------
    # Eye of the Graeae: guaranteed single spawn on L29
    if level == 29:
        from items import Artifact
        eye = Artifact({
            'id': 'eye_of_graeae',
            'name': 'Eye of the Graeae',
            'symbol': 'o',
            'color': [200, 200, 220],
            'item_class': 'artifact',
            'weight': 0.2,
            'min_level': 25,
        })
        eye_room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        if not _place_one([eye], eye_room, dungeon, ground_items, rng):
            _force_place_quest_item(eye, dungeon, ground_items)

    # Athena shrine: guaranteed single creation on L37
    if level == 37:
        _create_athena_shrine(dungeon, rooms, ground_items, rng)

    # -- Odin quest items (Fafnir) ---------------------------------------------
    # Broken Blade of Gram: guaranteed single spawn on L48
    if level == 48:
        from items import load_items, copy_at
        weapons = load_items('weapon')
        broken = next((w for w in weapons if w.id == 'broken_gram'), None)
        if broken:
            bg = copy_at(broken, 0, 0)
            bg_room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
            if not _place_one([bg], bg_room, dungeon, ground_items, rng):
                _force_place_quest_item(bg, dungeon, ground_items)

    # Odin's Altar + shrine: guaranteed on L53
    if level == 53:
        _create_odin_shrine(dungeon, rooms, ground_items, rng)

    # -- Leather scraps (Vidar secret) -----------------------------------------
    # 10 scraps distributed across the dungeon, guaranteed spawn
    _LEATHER_SCRAP_LEVELS = [5, 13, 21, 28, 35, 42, 50, 58, 66, 73]
    if level in _LEATHER_SCRAP_LEVELS:
        from items import Artifact
        scrap = Artifact({
            'id': 'leather_scrap', 'name': 'leather scrap',
            'symbol': ',', 'color': [120, 90, 60],
            'item_class': 'artifact', 'weight': 2.0, 'min_level': 1,
            'lore': "Useless scrap left over from leather-working. Too small for armor, too stiff for bandages.",
        })
        scrap.identified = True
        scrap_room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        if not _place_one([scrap], scrap_room, dungeon, ground_items, rng):
            _force_place_quest_item(scrap, dungeon, ground_items)

    # -- Gleipnir component rooms (Fenrir quest) --------------------------------
    _GLEIPNIR_COMPONENTS = {
        62: ('cats_footstep', "Sound of a Cat's Footstep", [180, 160, 200]),
        65: ('womans_beard', "Roots of a Woman's Beard", [200, 170, 140]),
        68: ('mountain_root', "Root of a Mountain", [140, 130, 120]),
        71: ('fish_breath', "Breath of a Fish", [140, 200, 220]),
        74: ('bird_spittle', "Spittle of a Bird", [220, 220, 180]),
        77: ('bear_sinew', "Sinew of a Bear's Sensitivity", [180, 140, 100]),
    }
    if level in _GLEIPNIR_COMPONENTS:
        comp_id, comp_name, comp_color = _GLEIPNIR_COMPONENTS[level]
        _create_gleipnir_room(dungeon, rooms, ground_items, rng, level,
                              comp_id, comp_name, comp_color)

    # -- Dwarven Forge: guaranteed on L76 ----------------------------------------
    if level == 76:
        _create_dwarven_forge(dungeon, rooms, ground_items, rng)

    # -- Vidar's Altar: guaranteed on L79 ----------------------------------------
    if level == 79:
        _create_vidar_altar(dungeon, rooms, rng)

    # -- Altar of the Last Judgment: guaranteed on L99 ---------------------------
    if level == 99:
        _create_judgment_altar(dungeon, rooms, rng)

    return ground_items


def _force_place_quest_item(item, dungeon: Dungeon, ground_items: list):
    """Guaranteed placement: put item on any walkable tile (fallback for quest items)."""
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.is_walkable(x, y):
                item.x, item.y = x, y
                ground_items.append(item)
                return
    # Absolute last resort: place at (1,1) regardless
    item.x, item.y = 1, 1
    ground_items.append(item)


def _create_ariadne_shrine(dungeon: Dungeon, rooms, ground_items, rng):
    """Create a small sealed shrine room near a fountain on L16-19.

    The shrine contains Ariadne's Thread but is walled off.
    When the player drops the Bronze Bull at the fountain, the shrine door opens.
    """
    # Find a fountain on this level
    fountain_pos = None
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] == FOUNTAIN:
                fountain_pos = (x, y)
                break
        if fountain_pos:
            break

    # If no fountain, place one in a random room
    if not fountain_pos:
        room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        cx, cy = room.center
        # Try to place fountain near center
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            fx, fy = cx + dx, cy + dy
            if dungeon.in_bounds(fx, fy) and dungeon.tiles[fy][fx] == FLOOR:
                dungeon.tiles[fy][fx] = FOUNTAIN
                fountain_pos = (fx, fy)
                break

    if not fountain_pos:
        return  # shouldn't happen, but safety check

    fx, fy = fountain_pos

    # Find a wall adjacent to a floor tile near the fountain to carve the shrine
    # Search in expanding radius around fountain
    shrine_carved = False
    for radius in range(2, 8):
        if shrine_carved:
            break
        for dx in range(-radius, radius + 1):
            if shrine_carved:
                break
            for dy in range(-radius, radius + 1):
                if shrine_carved:
                    break
                wx, wy = fx + dx, fy + dy
                if not dungeon.in_bounds(wx, wy):
                    continue
                if dungeon.tiles[wy][wx] != WALL:
                    continue
                # Check if we can carve a 3x3 shrine behind this wall
                # Find which direction is "into the wall" (away from floor)
                for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    sx, sy = wx + ddx, wy + ddy  # shrine center
                    # Need a 3x3 block of all-wall tiles for the shrine
                    can_carve = True
                    for cx in range(sx - 1, sx + 2):
                        for cy in range(sy - 1, sy + 2):
                            if not dungeon.in_bounds(cx, cy):
                                can_carve = False
                                break
                            if dungeon.tiles[cy][cx] != WALL:
                                can_carve = False
                                break
                        if not can_carve:
                            break
                    # Also need the door tile (wx, wy) to have a floor neighbor
                    has_floor_neighbor = False
                    for nx, ny in [(wx-1, wy), (wx+1, wy), (wx, wy-1), (wx, wy+1)]:
                        if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == FLOOR:
                            has_floor_neighbor = True
                            break
                    if can_carve and has_floor_neighbor:
                        # Carve the 3x3 shrine room
                        for cx in range(sx - 1, sx + 2):
                            for cy in range(sy - 1, sy + 2):
                                dungeon.tiles[cy][cx] = FLOOR
                        # The door position (wx, wy) stays as WALL -- will become DOOR when quest triggers
                        dungeon.tiles[wy][wx] = WALL  # ensure it's wall (the sealed door)
                        dungeon.ariadne_shrine_door = (wx, wy)
                        dungeon.ariadne_shrine_thread_pos = (sx, sy)
                        # Place Ariadne's Thread inside the shrine
                        from items import Artifact
                        thread = Artifact({
                            'id': 'ariadnes_thread',
                            'name': "Ariadne's Thread",
                            'symbol': '&',
                            'color': [255, 215, 100],
                            'item_class': 'artifact',
                            'weight': 0.1,
                            'min_level': 15,
                        })
                        thread.x = sx
                        thread.y = sy
                        ground_items.append(thread)
                        shrine_carved = True
                        break


def _create_athena_shrine(dungeon: Dungeon, rooms, ground_items, rng):
    """Create a sealed shrine room near an altar on L36-39.

    The shrine contains the Aegis of Athena (mirror shield).
    When the player drops the Eye of the Graeae at an altar, the shrine door opens.
    """
    # Find an altar on this level
    altar_pos = None
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] == ALTAR:
                altar_pos = (x, y)
                break
        if altar_pos:
            break

    # If no altar, place one in a random room
    if not altar_pos:
        room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        cx, cy = room.center
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            ax, ay = cx + dx, cy + dy
            if dungeon.in_bounds(ax, ay) and dungeon.tiles[ay][ax] == FLOOR:
                dungeon.tiles[ay][ax] = ALTAR
                altar_pos = (ax, ay)
                break

    if not altar_pos:
        return

    ax, ay = altar_pos

    # Find a wall near the altar to carve a 3x3 shrine room
    shrine_carved = False
    for radius in range(2, 8):
        if shrine_carved:
            break
        for dx in range(-radius, radius + 1):
            if shrine_carved:
                break
            for dy in range(-radius, radius + 1):
                if shrine_carved:
                    break
                wx, wy = ax + dx, ay + dy
                if not dungeon.in_bounds(wx, wy):
                    continue
                if dungeon.tiles[wy][wx] != WALL:
                    continue
                for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    sx, sy = wx + ddx, wy + ddy
                    can_carve = True
                    for cx in range(sx - 1, sx + 2):
                        for cy in range(sy - 1, sy + 2):
                            if not dungeon.in_bounds(cx, cy):
                                can_carve = False
                                break
                            if dungeon.tiles[cy][cx] != WALL:
                                can_carve = False
                                break
                        if not can_carve:
                            break
                    has_floor_neighbor = False
                    for nx, ny in [(wx-1, wy), (wx+1, wy), (wx, wy-1), (wx, wy+1)]:
                        if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == FLOOR:
                            has_floor_neighbor = True
                            break
                    if can_carve and has_floor_neighbor:
                        for cx in range(sx - 1, sx + 2):
                            for cy in range(sy - 1, sy + 2):
                                dungeon.tiles[cy][cx] = FLOOR
                        dungeon.tiles[wy][wx] = WALL  # sealed door
                        dungeon.athena_shrine_door = (wx, wy)
                        dungeon.athena_shrine_aegis_pos = (sx, sy)
                        # Place Aegis of Athena inside the shrine
                        from items import Shield
                        import json as _json
                        _shield_path = Path(__file__).parent / '..' / 'data' / 'items' / 'shield.json'
                        with open(_shield_path, encoding='utf-8') as _f:
                            _shield_data = _json.load(_f)
                        aegis_defn = {**_shield_data['aegis_of_athena'],
                                      'id': 'aegis_of_athena', 'item_class': 'shield'}
                        aegis = Shield(aegis_defn)
                        aegis.x = sx
                        aegis.y = sy
                        ground_items.append(aegis)
                        shrine_carved = True
                        break


def _create_odin_shrine(dungeon: Dungeon, rooms, ground_items, rng):
    """Create Odin's Altar and a sealed shrine room containing Sigurd's Shovel.

    The player drops the Broken Blade of Gram on the altar to open the shrine.
    Secret: throwing Gram over the altar from one side reforges it.
    """
    # Place Odin's Altar in a room (prefer a non-start room)
    altar_room = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
    cx, cy = altar_room.center
    placed = False
    for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
        ax, ay = cx + dx, cy + dy
        if dungeon.in_bounds(ax, ay) and dungeon.tiles[ay][ax] == FLOOR:
            dungeon.tiles[ay][ax] = ALTAR
            dungeon.odin_altar_pos = (ax, ay)
            placed = True
            break
    if not placed:
        return

    ax, ay = dungeon.odin_altar_pos

    # Carve a sealed 3x3 shrine near the altar
    shrine_carved = False
    for radius in range(2, 8):
        if shrine_carved:
            break
        for ddx in range(-radius, radius + 1):
            if shrine_carved:
                break
            for ddy in range(-radius, radius + 1):
                if shrine_carved:
                    break
                wx, wy = ax + ddx, ay + ddy
                if not dungeon.in_bounds(wx, wy):
                    continue
                if dungeon.tiles[wy][wx] != WALL:
                    continue
                for dddx, dddy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    sx, sy = wx + dddx, wy + dddy
                    can_carve = True
                    for ccx in range(sx - 1, sx + 2):
                        for ccy in range(sy - 1, sy + 2):
                            if not dungeon.in_bounds(ccx, ccy):
                                can_carve = False
                                break
                            if dungeon.tiles[ccy][ccx] != WALL:
                                can_carve = False
                                break
                        if not can_carve:
                            break
                    has_floor = False
                    for nx, ny in [(wx-1, wy), (wx+1, wy), (wx, wy-1), (wx, wy+1)]:
                        if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == FLOOR:
                            has_floor = True
                            break
                    if can_carve and has_floor:
                        for ccx in range(sx - 1, sx + 2):
                            for ccy in range(sy - 1, sy + 2):
                                dungeon.tiles[ccy][ccx] = FLOOR
                        dungeon.tiles[wy][wx] = WALL  # sealed door
                        dungeon.odin_shrine_door = (wx, wy)
                        # Place Sigurd's Shovel inside
                        from items import load_items, copy_at
                        weapons = load_items('weapon')
                        shovel_t = next((w for w in weapons if w.id == 'sigurds_shovel'), None)
                        if shovel_t:
                            shovel = copy_at(shovel_t, sx, sy)
                            ground_items.append(shovel)
                        shrine_carved = True
                        break


def _item_eligible_weighted(templates: list, level: int,
                            rng: random.Random | None = None) -> list:
    """Build a category-balanced weighted pool for non-food items.

    Items are first grouped by class (Weapon, Armor, Scroll, ...) so that each
    category contributes equally regardless of its raw floorSpawnWeight values.
    Within a category, weights are normalised to SLOTS_PER_TYPE total slots so
    that heavily-weighted items (e.g. iron swords at L1) still appear more
    often than rare items -- but weapons can't crowd out armor 100:1.
    """
    from collections import defaultdict

    SLOTS_PER_TYPE = 20   # each item class gets this many weighted slots in the pool
    if rng is None:
        rng = random.Random()

    by_type: dict[str, list] = defaultdict(list)
    for item in templates:
        if item.min_level > level:
            continue
        fw = getattr(item, 'floor_spawn_weight', {})
        if fw:
            w = _food_weight(fw, level)
            if w <= 0:
                continue   # aged out of this level range
        else:
            w = 1
        by_type[type(item).__name__].append((item, w))

    if not by_type:
        return [t for t in templates if t.min_level <= level] or templates[:]

    eligible = []
    for items_weights in by_type.values():
        total_w = sum(w for _, w in items_weights) or 1
        n = len(items_weights)
        if n <= SLOTS_PER_TYPE:
            # Few candidates -- give each at least 1 slot, proportional distribution
            for item, w in items_weights:
                slots = max(1, round(w / total_w * SLOTS_PER_TYPE))
                eligible.extend([item] * slots)
        else:
            # Many candidates -- weighted sample to ensure variety across levels
            weights = [w for _, w in items_weights]
            selected = rng.choices(items_weights, weights=weights, k=SLOTS_PER_TYPE)
            for item, _ in selected:
                eligible.append(item)
    return eligible


def _food_eligible(templates: list, level: int) -> list:
    """Return food items eligible for this level, weighted by floor_spawn_weight."""
    eligible = []
    for item in templates:
        w = _food_weight(item.floor_spawn_weight, level)
        if w > 0:
            eligible.extend([item] * w)
    return eligible or templates[:]


def _food_weight(spawn_weights: dict, level: int) -> int:
    """Look up the spawn weight for a given level from a range-keyed dict."""
    for key, weight in spawn_weights.items():
        parts = str(key).split('-')
        lo = int(parts[0])
        hi = int(parts[1]) if len(parts) > 1 else lo
        if lo <= level <= hi:
            return int(weight)
    return 0


# --- BUC and enchantment helpers ---
# Base rates per item_class: (blessed%, uncursed%, cursed%)
_BUC_RATES = {
    'weapon':    (0.08, 0.82, 0.10),
    'armor':     (0.08, 0.82, 0.10),
    'shield':    (0.08, 0.82, 0.10),
    'accessory': (0.05, 0.85, 0.10),
    'potion':    (0.12, 0.75, 0.13),
    'scroll':    (0.10, 0.80, 0.10),
    'wand':      (0.05, 0.90, 0.05),
}


def _assign_buc(inst, level: int, rng: random.Random):
    """Roll BUC status for an item based on its class and dungeon depth."""
    rates = _BUC_RATES.get(getattr(inst, 'item_class', ''), None)
    if rates is None:
        return  # non-BUC item types (food, corpse, ammo, etc.)
    blessed_base, _, cursed_base = rates
    # Depth scaling: cursed +0.1%/level, blessed +0.05%/level
    cursed_pct  = min(0.50, cursed_base + level * 0.001)
    blessed_pct = min(0.30, blessed_base + level * 0.0005)
    roll = rng.random()
    if roll < cursed_pct:
        inst.buc = 'cursed'
    elif roll < cursed_pct + blessed_pct:
        inst.buc = 'blessed'
    else:
        inst.buc = 'uncursed'


def _assign_enchant(inst, level: int, rng: random.Random):
    """Roll random enchantment for weapon/armor/shield based on depth.
    Armor/shield spawn enchant is capped at +1; weapons use full depth range."""
    if not hasattr(inst, 'enchant_bonus'):
        return
    if inst.item_class not in ('weapon', 'armor', 'shield'):
        return
    from items import SPAWN_ENCHANT_CAP_ARMOR, ENCHANT_CAP
    # Determine chance and range by depth
    if level <= 15:
        chance, lo, hi = 0.10, 1, 1
    elif level <= 35:
        chance, lo, hi = 0.15, 1, 2
    elif level <= 60:
        chance, lo, hi = 0.20, 1, 3
    else:
        chance, lo, hi = 0.25, 1, 4
    if rng.random() >= chance:
        return
    bonus = rng.randint(lo, hi)
    # Armor/shield: cap spawn enchant at +1 (scrolls push higher)
    if inst.item_class in ('armor', 'shield'):
        bonus = min(bonus, SPAWN_ENCHANT_CAP_ARMOR)
    else:
        # Weapons: respect per-slot cap
        bonus = min(bonus, ENCHANT_CAP.get('weapon', 5))
    # Cursed items get negative enchantment
    if getattr(inst, 'buc', 'uncursed') == 'cursed':
        bonus = -bonus
    inst.enchant_bonus = bonus


def _place_one(templates: list, room: 'Room', dungeon: 'Dungeon',
               ground_items: list, rng: random.Random) -> bool:
    """Try to place one randomly-chosen template item in room. Returns True on success."""
    if not templates:
        return False
    tiles = list(room.inner_tiles())
    rng.shuffle(tiles)
    for tx, ty in tiles:
        if not dungeon.is_walkable(tx, ty):
            continue
        if any(i.x == tx and i.y == ty for i in ground_items):
            continue
        inst = copy.copy(rng.choice(templates))
        # Re-roll wand charges semi-randomly at spawn time
        if hasattr(inst, 'charges_min'):
            inst.charges = rng.randint(inst.charges_min, inst.charges_max)
        # Re-roll ammo count at spawn time
        if hasattr(inst, 'count_min'):
            inst.count = rng.randint(inst.count_min, inst.count_max)
        # --- BUC assignment (depth-scaled) ---
        _assign_buc(inst, dungeon.level, rng)
        # --- Random enchantment for weapon/armor/shield ---
        _assign_enchant(inst, dungeon.level, rng)
        inst.x = tx
        inst.y = ty
        ground_items.append(inst)
        return True
    return False


def _weighted_choice(pool: dict, rng: random.Random) -> str:
    total = sum(v.get('_spawn_freq', v.get('frequency', 1)) for v in pool.values())
    r = rng.random() * total
    for key, val in pool.items():
        r -= val.get('_spawn_freq', val.get('frequency', 1))
        if r <= 0:
            return key
    return next(iter(pool))


# ---------------------------------------------------------------------------
# Fenrir quest room generators
# ---------------------------------------------------------------------------

def _create_gleipnir_room(dungeon, rooms, ground_items, rng, level,
                          comp_id, comp_name, comp_color):
    """Create a themed room containing one Gleipnir component with a light challenge."""
    from items import Artifact

    component = Artifact({
        'id': comp_id, 'name': comp_name,
        'symbol': '~', 'color': comp_color,
        'item_class': 'artifact', 'weight': 0.2, 'min_level': 60,
    })
    component.identified = True

    # Pick a non-start room
    candidates = rooms[1:] if len(rooms) > 1 else rooms
    room = rng.choice(candidates)
    cx, cy = room.center

    # Each component has a themed challenge
    if comp_id == 'cats_footstep':
        # Silent room: item guarded by placing traps around it
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                tx, ty = cx + dx, cy + dy
                if dungeon.in_bounds(tx, ty) and dungeon.tiles[ty][tx] == FLOOR:
                    dungeon.traps[(tx, ty)] = {
                        'type': 'alarm', 'damage': '0', 'damage_type': 'none',
                        'message': 'A silent alarm triggers!', 'symbol': '^',
                        'color': (150, 150, 180), 'revealed': False
                    }
    elif comp_id == 'womans_beard':
        # Hidden behind a secret door in the room wall
        for wx, wy in room.wall_tiles():
            if dungeon.in_bounds(wx, wy) and dungeon.tiles[wy][wx] == WALL:
                # Check if we can carve a small alcove
                for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ax, ay = wx + ddx, wy + ddy
                    if (dungeon.in_bounds(ax, ay) and dungeon.tiles[ay][ax] == WALL
                            and not any(dungeon.tiles[ay + d][ax + e] == FLOOR
                                        for d in [-1, 0, 1] for e in [-1, 0, 1]
                                        if dungeon.in_bounds(ax + e, ay + d)
                                        and (d, e) != (0, 0)
                                        and (ax + e, ay + d) != (wx, wy))):
                        dungeon.tiles[wy][wx] = SECRET_DOOR
                        dungeon.tiles[ay][ax] = FLOOR
                        component.x, component.y = ax, ay
                        ground_items.append(component)
                        return
                break  # only try one wall tile
    elif comp_id == 'mountain_root':
        # Surrounded by lava tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                lx, ly = cx + dx, cy + dy
                if dungeon.in_bounds(lx, ly) and dungeon.tiles[ly][lx] == FLOOR:
                    dungeon.tiles[ly][lx] = LAVA
    elif comp_id == 'fish_breath':
        # Surrounded by water tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                wx, wy = cx + dx, cy + dy
                if dungeon.in_bounds(wx, wy) and dungeon.tiles[wy][wx] == FLOOR:
                    dungeon.tiles[wy][wx] = WATER
    elif comp_id == 'bird_spittle':
        # Placed on an altar (requires prayer-style interaction to pick up)
        dungeon.tiles[cy][cx] = ALTAR
    elif comp_id == 'bear_sinew':
        # Bear trap protecting the item
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            tx, ty = cx + dx, cy + dy
            if dungeon.in_bounds(tx, ty) and dungeon.tiles[ty][tx] == FLOOR:
                dungeon.traps[(tx, ty)] = {
                    'type': 'bear_trap', 'damage': '1d4', 'damage_type': 'physical',
                    'message': 'A bear trap snaps shut!', 'symbol': '^',
                    'color': (160, 160, 160), 'revealed': False
                }

    # Default placement at room center (used for all except womans_beard secret door)
    if comp_id != 'womans_beard':
        component.x, component.y = cx, cy
        ground_items.append(component)
        return

    # Fallback for womans_beard if secret door creation failed
    if not _place_one([component], room, dungeon, ground_items, rng):
        _force_place_quest_item(component, dungeon, ground_items)


def _create_dwarven_forge(dungeon, rooms, ground_items, rng):
    """Create a Dwarven Forge room on L76 where Gleipnir can be assembled."""
    # Pick a room away from start
    candidates = rooms[2:] if len(rooms) > 2 else rooms
    room = rng.choice(candidates)
    cx, cy = room.center

    # Place the forge tile (reuse ALTAR visually, store position for detection)
    dungeon.tiles[cy][cx] = ALTAR
    dungeon.dwarven_forge_pos = (cx, cy)


def _create_vidar_altar(dungeon, rooms, rng):
    """Create Vidar's Altar on L79 where leather scraps can be assembled."""
    # Pick a non-start room
    candidates = rooms[1:] if len(rooms) > 1 else rooms
    room = rng.choice(candidates)
    cx, cy = room.center

    # Place altar tile and store position
    dungeon.tiles[cy][cx] = ALTAR
    dungeon.vidar_altar_pos = (cx, cy)


def _create_judgment_altar(dungeon, rooms, rng):
    """Create the Altar of the Last Judgment on L99 — a massive set of scales.
    Mechanic implementation comes later; for now, just place the tile and store metadata."""
    # Pick a large room (prefer largest non-start room)
    candidates = sorted(rooms[1:], key=lambda r: r.width * r.height, reverse=True)
    room = candidates[0] if candidates else rooms[0]
    cx, cy = room.center

    # Place altar tile and store position
    dungeon.tiles[cy][cx] = ALTAR
    dungeon.judgment_altar_pos = (cx, cy)
