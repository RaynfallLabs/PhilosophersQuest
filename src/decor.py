"""Domains and fixtures: what a floor looks like and what stands in it
(Dungeon Alive, 2026-11-12).

Brandon: "dividing the dungeon into thematic segments. Asterion's 20 levels
look like our current dungeon; Medusa's 20 levels have their OWN look, maybe
a mossy, forgotten temple look; Fafnir has HIS own look." The five domains
are in data/domains.json, one per gate boss. Each has:

* a **theme**: the folder under assets/tiles/env/themes/ whose wall, floor,
  door and water pictures replace the base tiles (renderer.py; any picture
  it lacks falls back to the base set, so missing art never breaks a floor);
* its **dressing**: fixtures from data/fixtures.json set about its rooms and
  corridors.

A **fixture** stands in or on a tile without changing what the tile is. A
statue on a floor tile blocks movement (and, if opaque, sight, as a pillar
does), but the tile stays FLOOR, so the level's own logic (reachability,
Medusa's gaze lines, Asterion's phasing walls) is untouched. Blocking
fixtures go only against a room's walls, away from its ways in, and every
one is checked with a reachability walk before it stays.

State lives on the Dungeon, which pickles with its floor:

* ``fixtures``: {(x, y): id};
* ``fixture_state``: {(x, y): 'spent' ...};
* ``fixture_blocks`` / ``fixture_opaque``: sets read by ``is_walkable`` /
  ``is_opaque``;
* ``theme``, ``domain``;
* ``tile_art``: {(x, y): picture name}, a per-tile picture override.

Pure module: no pygame.
"""
from __future__ import annotations

import json
import random
from collections import deque

_DOMAINS: dict | None = None
_FIXTURES: dict | None = None


def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def domains() -> list:
    global _DOMAINS
    if _DOMAINS is None:
        from paths import data_path
        _DOMAINS = _load(data_path('data', 'domains.json'))
    return _DOMAINS['domains']


def fixture_defs() -> dict:
    global _FIXTURES
    if _FIXTURES is None:
        from paths import data_path
        _FIXTURES = _load(data_path('data', 'fixtures.json'))
    return _FIXTURES['fixtures']


def fixture_def(fid: str) -> dict:
    return fixture_defs().get(fid) or {}


def domain_for(level: int):
    """The domain a floor belongs to, or None (the Cow Level, floor 0)."""
    try:
        level = int(level)
    except (TypeError, ValueError):
        return None
    for d in domains():
        lo, hi = d['floors']
        if lo <= level <= hi:
            return d
    return None


def domain_by_id(did: str):
    for d in domains():
        if d['id'] == did:
            return d
    return None


# ---------------------------------------------------------------------------
# Fixture state on a Dungeon
# ---------------------------------------------------------------------------

def fixtures_of(dungeon) -> dict:
    return dungeon.__dict__.setdefault('fixtures', {})


def _sets(dungeon):
    blocks = dungeon.__dict__.get('fixture_blocks')
    if not isinstance(blocks, set):
        blocks = set()
        dungeon.fixture_blocks = blocks
    opaque = dungeon.__dict__.get('fixture_opaque')
    if not isinstance(opaque, set):
        opaque = set()
        dungeon.fixture_opaque = opaque
    return blocks, opaque


def place(dungeon, pos, fid: str, state: str = '') -> None:
    pos = (int(pos[0]), int(pos[1]))
    fixtures_of(dungeon)[pos] = fid
    defn = fixture_def(fid)
    blocks, opaque = _sets(dungeon)
    blocks.discard(pos)
    opaque.discard(pos)
    if defn.get('blocks'):
        blocks.add(pos)
    if defn.get('opaque'):
        opaque.add(pos)
    st = dungeon.__dict__.setdefault('fixture_state', {})
    if state:
        st[pos] = state
    else:
        st.pop(pos, None)


def remove(dungeon, pos) -> None:
    pos = (int(pos[0]), int(pos[1]))
    fixtures_of(dungeon).pop(pos, None)
    blocks, opaque = _sets(dungeon)
    blocks.discard(pos)
    opaque.discard(pos)
    dungeon.__dict__.setdefault('fixture_state', {}).pop(pos, None)


def fixture_at(dungeon, x: int, y: int):
    return (dungeon.__dict__.get('fixtures') or {}).get((x, y))


def look_line(dungeon, x: int, y: int) -> str:
    fid = fixture_at(dungeon, x, y)
    if not fid:
        return ''
    line = fixture_def(fid).get('look', '')
    if (dungeon.__dict__.get('fixture_state') or {}).get((x, y)) == 'spent':
        spent = fixture_def(fid).get('spent_look', '')
        if spent:
            line = spent
    return line


def blocking_name(dungeon, x: int, y: int) -> str:
    """'a statue' when a blocking fixture stands on (x, y), else ''."""
    if (x, y) not in (dungeon.__dict__.get('fixture_blocks') or ()):
        return ''
    return fixture_def(fixture_at(dungeon, x, y) or '').get('name', 'something')


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

def apply_theme(dungeon, level: int):
    """Set the floor's domain and theme. Returns the domain (or None)."""
    dom = domain_for(level)
    dungeon.domain = dom['id'] if dom else None
    dungeon.theme = dom.get('theme') if dom else None
    return dom


# ---------------------------------------------------------------------------
# Dressing an ordinary floor
# ---------------------------------------------------------------------------

def _weighted(table: dict, rng) -> str:
    total = sum(float(w) for w in table.values())
    roll = rng.random() * total
    for k, w in table.items():
        roll -= float(w)
        if roll <= 0:
            return k
    return next(iter(table))


def _room_contains(room, x, y) -> bool:
    return room.x <= x < room.x + room.width and room.y <= y < room.y + room.height


def _taken_tiles(dungeon, monsters, items) -> set:
    from dungeon import FLOOR
    taken = set()
    tiles = dungeon.tiles
    for y in range(dungeon.height):
        row = tiles[y]
        for x in range(dungeon.width):
            if row[x] != FLOOR:
                taken.add((x, y))
    taken |= set((dungeon.__dict__.get('traps') or {}).keys())
    taken |= set(dungeon.__dict__.get('pits') or ())
    taken |= set((dungeon.__dict__.get('bridge_tiles') or {}).keys())
    taken |= set(fixtures_of(dungeon).keys())
    try:
        from geom import occupied_tiles
        for m in monsters or ():
            taken |= set(occupied_tiles(m))
    except Exception:
        for m in monsters or ():
            taken.add((m.x, m.y))
    for it in items or ():
        try:
            taken.add((it.x, it.y))
        except AttributeError:
            pass
    return taken


def _skip_rooms(dungeon) -> list:
    """Rooms the domain dressing leaves alone: special rooms (they get their
    own furniture), the vault, hidden chambers."""
    out = []
    special = dungeon.__dict__.get('special_rooms') or {}
    for room in dungeon.rooms:
        if tuple(room.center) in special:
            out.append(room)
    vault = dungeon.__dict__.get('vault')
    if vault is not None:
        out.append(vault.get('room') if isinstance(vault, dict) else vault)
    for ch in dungeon.__dict__.get('hidden_chambers') or ():
        r = ch.get('room') if isinstance(ch, dict) else None
        if r is not None:
            out.append(r)
    return [r for r in out if r is not None]


def _inner(room, dungeon):
    from dungeon import FLOOR
    out = []
    for ry in range(room.y + 1, room.y + room.height - 1):
        for rx in range(room.x + 1, room.x + room.width - 1):
            if dungeon.in_bounds(rx, ry) and dungeon.tiles[ry][rx] == FLOOR:
                out.append((rx, ry))
    return out


def _ring_walls(room, dungeon):
    """Wall tiles of the room's ring that face its floor (no corners)."""
    from dungeon import WALL
    out = []
    inner = set(_inner(room, dungeon))
    for ry in range(room.y, room.y + room.height):
        for rx in range(room.x, room.x + room.width):
            on_ring = rx in (room.x, room.x + room.width - 1) or ry in (room.y, room.y + room.height - 1)
            if not on_ring or not dungeon.in_bounds(rx, ry) or dungeon.tiles[ry][rx] != WALL:
                continue
            if any((rx + ox, ry + oy) in inner for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.append((rx, ry))
    return out


def _against_wall_spots(room, dungeon, taken):
    """Inner tiles beside the room's wall, away from every way in."""
    from dungeon import WALL, DOOR, SECRET_DOOR
    inner = set(_inner(room, dungeon))
    out = []
    for (x, y) in inner:
        if (x, y) in taken:
            continue
        if not any(dungeon.in_bounds(x + ox, y + oy) and dungeon.tiles[y + oy][x + ox] == WALL
                   and not _room_contains_inner(room, x + ox, y + oy)
                   for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        near_opening = False
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                nx, ny = x + ox, y + oy
                if not dungeon.in_bounds(nx, ny):
                    continue
                t = dungeon.tiles[ny][nx]
                if t in (DOOR, SECRET_DOOR):
                    near_opening = True
                elif (nx, ny) not in inner and t != WALL:
                    near_opening = True          # a corridor running in
        if not near_opening:
            out.append((x, y))
    return out


def _room_contains_inner(room, x, y) -> bool:
    return room.x < x < room.x + room.width - 1 and room.y < y < room.y + room.height - 1


def _reachable_count(dungeon) -> int:
    from dungeon import STAIRS_UP, DOOR, SECRET_DOOR
    start = None
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] == STAIRS_UP:
                start = (x, y)
                break
        if start:
            break
    if start is None:
        return -1
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ox, y + oy
            if (nx, ny) in seen or not dungeon.in_bounds(nx, ny):
                continue
            if dungeon.is_walkable(nx, ny) or dungeon.tiles[ny][nx] in (DOOR, SECRET_DOOR):
                seen.add((nx, ny))
                q.append((nx, ny))
    return len(seen)


def _corridor_tiles(dungeon, taken) -> list:
    from dungeon import FLOOR
    rooms = dungeon.rooms
    out = []
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] != FLOOR or (x, y) in taken:
                continue
            if any(_room_contains(r, x, y) for r in rooms):
                continue
            out.append((x, y))
    return out


def dress_floor(dungeon, level: int, monsters=(), items=(), rng=None) -> int:
    """Theme the floor and set its domain's dressing about it. Returns how
    many fixtures were placed. Call after the monsters and items are down,
    so nothing lands under a statue."""
    rng = rng or random.Random()
    dom = apply_theme(dungeon, level)
    if not dom:
        return 0
    decor = dom.get('decor') or {}
    taken = _taken_tiles(dungeon, monsters, items)
    skip = {id(r) for r in _skip_rooms(dungeon)}
    before = _reachable_count(dungeon)
    placed_blocks = []
    n = 0
    rooms = [r for r in dungeon.rooms if id(r) not in skip]
    for room in rooms:
        inner = [t for t in _inner(room, dungeon) if t not in taken]
        if len(inner) < 4:
            continue
        # Wall pieces.
        spec = decor.get('wall')
        if spec and rng.random() < float(spec.get('room_chance', 0)):
            walls = [t for t in _ring_walls(room, dungeon) if t not in fixtures_of(dungeon)]
            rng.shuffle(walls)
            lo, hi = spec.get('per_room', [1, 1])
            for pos in walls[:rng.randint(int(lo), int(hi))]:
                place(dungeon, pos, _weighted(spec['ids'], rng))
                n += 1
        # Floor decals.
        spec = decor.get('floor')
        if spec and rng.random() < float(spec.get('room_chance', 0)):
            rng.shuffle(inner)
            lo, hi = spec.get('per_room', [1, 1])
            for pos in inner[:rng.randint(int(lo), int(hi))]:
                place(dungeon, pos, _weighted(spec['ids'], rng))
                taken.add(pos)
                n += 1
        # Standing pieces, against the walls, never two side by side.
        spec = decor.get('stand')
        if spec and len(inner) >= 9 and rng.random() < float(spec.get('room_chance', 0)):
            spots = _against_wall_spots(room, dungeon, taken)
            rng.shuffle(spots)
            lo, hi = spec.get('per_room', [1, 1])
            want = rng.randint(int(lo), int(hi))
            for pos in spots:
                if want <= 0:
                    break
                if any(max(abs(pos[0] - b[0]), abs(pos[1] - b[1])) <= 1 for b in placed_blocks):
                    continue
                fid = _weighted(spec['ids'], rng)
                place(dungeon, pos, fid)
                taken.add(pos)
                if fixture_def(fid).get('blocks'):
                    placed_blocks.append(pos)
                want -= 1
                n += 1
    # Corridor decals.
    spec = decor.get('floor')
    chance = float((spec or {}).get('corridor_chance', 0) or 0)
    if chance > 0:
        for pos in _corridor_tiles(dungeon, taken):
            if rng.random() < chance:
                place(dungeon, pos, _weighted(spec['ids'], rng))
                n += 1
    # Nothing may cut the floor in two: undo blockers until the walk from
    # the up stair reaches as much as it did, less the tiles now furnished.
    if before > 0 and placed_blocks:
        while placed_blocks and _reachable_count(dungeon) < before - len(placed_blocks):
            remove(dungeon, placed_blocks.pop())
            n -= 1
    return n
