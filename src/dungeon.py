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

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """True if the player / monster can freely move onto this tile.
        Doors and secret doors block movement until explicitly opened."""
        return self.in_bounds(x, y) and self.tiles[y][x] not in (WALL, DOOR, SECRET_DOOR)

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

    # ── 1. BSP partitioning ──────────────────────────────────────────────────
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

    # ── 2. Place one room in each BSP leaf ───────────────────────────────────
    rooms: List[Room] = []
    for leaf in root.leaves():
        room = _room_in_leaf(leaf, rng)
        if room:
            leaf.room = room
            rooms.append(room)
            for rx, ry in room.inner_tiles():
                tiles[ry][rx] = FLOOR

    # ── 3. Connect sibling pairs up the BSP tree ─────────────────────────────
    _connect_bsp(root, tiles, rng)

    # ── 4. Place doors at room-wall openings ─────────────────────────────────
    _place_doors(tiles, rooms, rng, chance=0.70)

    # ── 5. Place secret doors (shortcuts) ────────────────────────────────────
    _place_secret_doors(tiles, width, height, rooms, rng, level)

    # ── 6. Place stairs ──────────────────────────────────────────────────────
    if len(rooms) >= 2:
        sx, sy = rooms[0].center
        tiles[sy][sx] = STAIRS_UP
        ex, ey = rooms[-1].center
        tiles[ey][ex] = STAIRS_DOWN
    elif rooms:
        cx, cy = rooms[0].center
        tiles[cy][cx] = STAIRS_UP

    return Dungeon(tiles, rooms, width, height, level)


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
    Any room-wall tile that is FLOOR was carved by a corridor — make it a DOOR.
    """
    for room in rooms:
        for wx, wy in room.wall_tiles():
            if tiles[wy][wx] == FLOOR:
                # Confirm it's a valid 1-tile passage (not a wide opening)
                # Count orthogonal floor neighbors — a doorway has exactly 2
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

    target   = max(1, 1 + level // 3)   # 1-2 per level
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
# Spawn helpers  (unchanged signatures — called by level_manager)
# ---------------------------------------------------------------------------

def spawn_monsters(rooms: List[Room], level: int, dungeon: Dungeon,
                   min_count: int = None, max_count: int = None) -> list:
    """Spawn monsters in dungeon rooms (skips the first room).
    Count scales with dungeon level: 3-5 at level 1, up to 10-15 at level 50+."""
    from monster import Monster

    monsters_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)

    # Build weighted pool: monsters past their max_level get fraction of normal weight
    eligible = {}
    for k, v in all_defs.items():
        if v.get('min_level', 1) > level:
            continue
        max_lv = v.get('max_level', None)
        freq = v.get('frequency', 5)
        if max_lv is not None and level > max_lv:
            over = level - max_lv
            freq = max(1, freq - over)   # frequency decays by 1 per level over cap
        eligible[k] = {**v, '_spawn_freq': freq}
    if not eligible:
        return []

    rng = random.Random()
    if min_count is None:
        min_count = min(3 + level // 10, 10)
    if max_count is None:
        max_count = min(5 + level // 5, 15)
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

    # ── Regular items (weapons/armor/shield/accessories/wands/scrolls/ammo) — 33% per room ──
    templates: list = []
    for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll', 'ammo'):
        try:
            templates += load_items(cls_name)
        except FileNotFoundError:
            pass

    eligible = _item_eligible_weighted(templates, level)

    for room in rooms[1:]:
        if rng.random() > 0.33:
            continue
        _place_one(eligible, room, dungeon, ground_items, rng)

    # ── Containers — guaranteed minimum 1; diminishing extras ────────────────
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
        # Tier variance: ±1 level, clamped 1-5
        tier = max(1, min(5, level + rng.randint(-1, 1)))
        inst.tier = tier
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
        extra_chance *= 0.45   # 0.55 → 0.25 → 0.11 → …

    # ── Lockpicks — 1-2 per level, in random rooms ─────────────────────────
    try:
        all_picks = load_items('lockpick')
    except FileNotFoundError:
        all_picks = []

    eligible_picks = [p for p in all_picks if p.min_level <= level] or all_picks[:]
    pick_count = rng.randint(1, 2)
    rooms_for_picks = rng.sample(rooms[1:], min(pick_count, len(rooms) - 1))
    for room in rooms_for_picks:
        _place_one(eligible_picks, room, dungeon, ground_items, rng)

    # ── Food — 1-3 items scattered across rooms ──────────────────────────────
    try:
        all_food = load_items('food')
    except FileNotFoundError:
        all_food = []

    eligible_food = _food_eligible(all_food, level)
    food_count = rng.randint(1, 3)
    food_rooms = rng.sample(rooms[1:], min(food_count, len(rooms) - 1))
    for room in food_rooms:
        _place_one(eligible_food, room, dungeon, ground_items, rng)

    return ground_items


def _item_eligible_weighted(templates: list, level: int) -> list:
    """Build a weighted eligible pool for non-food items.
    Items with a floorSpawnWeight table are repeated proportionally to their weight
    at the current level, so late-game items crowd out early-game ones naturally.
    Items without a weight table are eligible at weight 1 if min_level passes."""
    eligible = []
    for item in templates:
        if item.min_level > level:
            continue
        fw = getattr(item, 'floor_spawn_weight', {})
        if fw:
            w = _food_weight(fw, level)   # range-key parser handles both dict formats
            if w > 0:
                eligible.extend([item] * w)
            # Weight 0 for this level range means the item has aged out — skip it
        else:
            eligible.append(item)
    return eligible or [t for t in templates if t.min_level <= level] or templates[:]


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
