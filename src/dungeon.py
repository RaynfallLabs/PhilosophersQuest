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

# ---------------------------------------------------------------------------
# Trap definitions
# ---------------------------------------------------------------------------

TRAP_TYPES = [
    {'type': 'pit',      'damage': '2d6',   'damage_type': 'physical', 'message': 'You fall into a pit!',              'symbol': '^', 'color': (150, 75, 0)},
    {'type': 'arrow',    'damage': '1d6+2', 'damage_type': 'pierce',   'message': 'An arrow fires from the wall!',     'symbol': '^', 'color': (180, 140, 80)},
    {'type': 'alarm',    'damage': '0',     'damage_type': 'none',     'message': 'A pressure plate triggers an alarm!','symbol': '^', 'color': (200, 50, 50)},
    {'type': 'acid',     'damage': '2d4',   'damage_type': 'acid',     'message': 'Acid sprays from a nozzle!',        'symbol': '^', 'color': (100, 200, 50)},
    {'type': 'teleport', 'damage': '0',     'damage_type': 'none',     'message': 'The floor vanishes -- you teleport!','symbol': '^', 'color': (100, 100, 220)},
]

# ---------------------------------------------------------------------------
# BSP tuning
# ---------------------------------------------------------------------------

_BSP_MIN_LEAF  = 9    # minimum region dimension before splitting stops
_ROOM_PAD      = 2    # minimum tiles between room edge and region edge
_ROOM_MIN_INNER = 3   # minimum interior (floor) tiles per axis
_ROOM_MAX_INNER = 9   # maximum interior tiles per axis


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
        # Special rooms: (cx, cy) -> type string ('treasury', 'library', 'shrine', 'monster_den')
        self.special_rooms: dict = {}

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """True if the player / monster can freely move onto this tile.
        Doors and secret doors block movement until explicitly opened."""
        return self.in_bounds(x, y) and self.tiles[y][x] not in (WALL, DOOR, SECRET_DOOR)

    def is_altar(self, x: int, y: int) -> bool:
        """True if this tile is a sacred altar."""
        return self.in_bounds(x, y) and self.tiles[y][x] == ALTAR

    def is_opaque(self, x: int, y: int) -> bool:
        """True if the tile blocks line-of-sight (for FOV)."""
        return (not self.in_bounds(x, y)
                or self.tiles[y][x] in (WALL, DOOR, SECRET_DOOR))

    def open_door(self, x: int, y: int) -> bool:
        """Open a closed door or reveal a secret door.  Returns True on success."""
        if self.in_bounds(x, y) and self.tiles[y][x] in (DOOR, SECRET_DOOR):
            self.tiles[y][x] = FLOOR
            return True
        return False


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
    """
    rng   = random.Random()
    tiles = [[WALL] * width for _ in range(height)]

    # -- 1. BSP partitioning --------------------------------------------------
    root   = _BSPNode(1, 1, width - 2, height - 2)
    queue  = [root]
    target = min(6 + level * 2, 18)

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
    return dungeon


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
        x1, y1 = left_room.center
        x2, y2 = right_room.center
        _carve_corridor(tiles, x1, y1, x2, y2, rng)


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
        min_count = min(2 + level // 15, 7)
    if max_count is None:
        max_count = min(3 + level // 8, 11)
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
    food_count = rng.randint(1, 3)
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
        room_type = rng.choice(['treasury', 'library', 'shrine', 'monster_den'])
        cx, cy = special_room.center
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
            pass  # monster density handled by spawn_monsters seeing the flag

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

    return ground_items


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
        # Randomly curse armor/shield at spawn (10% chance if can_be_cursed)
        if getattr(inst, 'can_be_cursed', False) and rng.random() < 0.10:
            inst.cursed = True
            # Cursed items often have negative enchantment
            inst.enchant_bonus = rng.choice([-2, -1, -1, 0])
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
