import random
from dataclasses import dataclass
from typing import List, Tuple

# Tile type constants
WALL = 0
FLOOR = 1
STAIRS_UP = 2
STAIRS_DOWN = 3
DOOR = 4


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
        """Yields (x, y) for all floor tiles inside this room (excluding walls)."""
        for ry in range(self.y + 1, self.y + self.height - 1):
            for rx in range(self.x + 1, self.x + self.width - 1):
                yield rx, ry

    def intersects(self, other: 'Room') -> bool:
        return (
            self.x < other.x + other.width and
            self.x + self.width > other.x and
            self.y < other.y + other.height and
            self.y + self.height > other.y
        )


class Dungeon:
    def __init__(self, tiles: List[List[int]], rooms: List[Room],
                 width: int, height: int, level: int):
        self.tiles = tiles
        self.rooms = rooms
        self.width = width
        self.height = height
        self.level = level
        self.explored = [[False] * width for _ in range(height)]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x] != WALL

    def is_opaque(self, x: int, y: int) -> bool:
        return not self.in_bounds(x, y) or self.tiles[y][x] == WALL


def generate_dungeon(width: int = 80, height: int = 50, level: int = 1) -> Dungeon:
    rng = random.Random()
    tiles = [[WALL] * width for _ in range(height)]
    rooms: List[Room] = []

    max_rooms = 15
    min_size = 5
    max_size = 12

    for _ in range(max_rooms * 3):  # extra attempts to place max_rooms
        if len(rooms) >= max_rooms:
            break
        w = rng.randint(min_size, max_size)
        h = rng.randint(min_size, max_size)
        x = rng.randint(1, width - w - 2)
        y = rng.randint(1, height - h - 2)
        new_room = Room(x, y, w, h)

        if any(new_room.intersects(r) for r in rooms):
            continue

        for rx, ry in new_room.inner_tiles():
            tiles[ry][rx] = FLOOR

        if rooms:
            prev_cx, prev_cy = rooms[-1].center
            cx, cy = new_room.center
            _carve_corridor(tiles, prev_cx, prev_cy, cx, cy, rng)

        rooms.append(new_room)

    if len(rooms) >= 2:
        sx, sy = rooms[0].center
        tiles[sy][sx] = STAIRS_UP
        ex, ey = rooms[-1].center
        tiles[ey][ex] = STAIRS_DOWN

    return Dungeon(tiles, rooms, width, height, level)


def _carve_corridor(tiles, x1, y1, x2, y2, rng):
    if rng.random() < 0.5:
        _carve_h_corridor(tiles, x1, x2, y1)
        _carve_v_corridor(tiles, y1, y2, x2)
    else:
        _carve_v_corridor(tiles, y1, y2, x1)
        _carve_h_corridor(tiles, x1, x2, y2)


def _carve_h_corridor(tiles, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        tiles[y][x] = FLOOR


def _carve_v_corridor(tiles, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        tiles[y][x] = FLOOR
