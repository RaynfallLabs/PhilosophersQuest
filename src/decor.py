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


def config() -> dict:
    """The whole of data/domains.json (domains, clans, clan lines)."""
    domains()
    return _DOMAINS


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
    band_room = _band_room_of(dungeon)
    if band_room is not None:
        out.append(band_room)
    return [r for r in out if r is not None]


def _band_room_of(dungeon):
    band = dungeon.__dict__.get('band')
    if not isinstance(band, dict) or not band.get('room'):
        return None
    bx, by, bw, bh = band['room']
    for r in dungeon.rooms:
        if (r.x, r.y, r.width, r.height) == (bx, by, bw, bh):
            return r
    return None


def furnish_band_camp(dungeon, taken: set, placed_blocks: list, rng) -> int:
    """A war-band's camp (data/war_bands.json 'camp'): its fire and banner
    near the middle of its room, its bedrolls round the fire, its bones and
    candles against a wall in one group."""
    room = _band_room_of(dungeon)
    if room is None:
        return 0
    import war_bands
    b = war_bands.data()['bands'].get(dungeon.band.get('id', ''), {})
    camp = b.get('camp') or {}
    cx, cy = room.center
    inner = [t for t in _inner(room, dungeon) if t not in taken]
    inner.sort(key=lambda t: max(abs(t[0] - cx), abs(t[1] - cy)))
    n = 0
    for fid in camp.get('stand', ()):
        for pos in list(inner):
            if any(max(abs(pos[0] - b2[0]), abs(pos[1] - b2[1])) <= 1 for b2 in placed_blocks):
                continue
            place(dungeon, pos, fid)
            taken.add(pos)
            inner.remove(pos)
            if fixture_def(fid).get('blocks'):
                placed_blocks.append(pos)
            n += 1
            break
    # Bedding lies round the fire; bones, candles and the like go against a
    # wall in one group (_place_cluster), not dotted about the floor
    # (Brandon's play-test, 2026-11-12).
    ring = [t for t in inner if 2 <= max(abs(t[0] - cx), abs(t[1] - cy)) <= 3]
    rng.shuffle(ring)
    objs = {}
    for fid in camp.get('floor', ()):
        if fid == 'bedroll' or _flat(fid):
            pos = next((t for t in ring if t not in taken), None)
            if pos is not None:
                place(dungeon, pos, fid)
                taken.add(pos)
                n += 1
        else:
            objs[fid] = objs.get(fid, 0) + 1
    if objs:
        n += _place_cluster(dungeon, room, objs, sum(objs.values()), taken, rng)
    return n


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


def _reserved_doors(dungeon) -> set:
    """Doors that are still rock when a floor is dressed: the quest shrines
    of Ariadne (17), Athena (37) and Odin (53). Their doorsteps must stay
    clear, or the shrine opens onto a statue."""
    out = set()
    for attr in ('ariadne_shrine_door', 'athena_shrine_door', 'odin_shrine_door'):
        pos = dungeon.__dict__.get(attr)
        if pos:
            out.add((int(pos[0]), int(pos[1])))
    return out


def _against_wall_spots(room, dungeon, taken):
    """Inner tiles beside the room's wall, away from every way in."""
    from dungeon import WALL, DOOR, SECRET_DOOR
    inner = set(_inner(room, dungeon))
    reserved = _reserved_doors(dungeon)
    out = []
    for (x, y) in inner:
        if (x, y) in taken:
            continue
        if any(max(abs(x - rx), abs(y - ry)) <= 1 for rx, ry in reserved):
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


def _flat(fid: str) -> bool:
    """A mark lying flat on the floor (a scorch, a crack, ash, snow): it may
    lie anywhere. Anything else loose is an object (data/fixtures.json)."""
    return bool(fixture_def(fid).get('flat'))


def _wall_sides(pos, room, dungeon) -> int:
    """How many of a tile's four sides are the room's own wall."""
    from dungeon import WALL
    x, y = pos
    return sum(1 for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if dungeon.in_bounds(x + ox, y + oy) and dungeon.tiles[y + oy][x + ox] == WALL
               and not _room_contains_inner(room, x + ox, y + oy))


def _place_cluster(dungeon, room, ids: dict, want: int, taken: set, rng) -> int:
    """Loose objects as one small group against a wall, the way such things
    come to lie: rubble where a corner came down, bones in a nook, broken
    jars along a wall. A corner first when there is one, the rest beside it
    along the wall; most of the group is one thing (Brandon's play-test,
    2026-11-12: "big empty rooms with random stuff on the floor")."""
    spots = set(_against_wall_spots(room, dungeon, taken))
    if not spots or want <= 0:
        return 0
    corners = sorted(s for s in spots if _wall_sides(s, room, dungeon) >= 2)
    anchor = rng.choice(corners or sorted(spots))
    first = _weighted(ids, rng)
    placed = [anchor]
    place(dungeon, anchor, first)
    taken.add(anchor)
    while len(placed) < want:
        nbrs = sorted(s for s in spots if s not in taken
                      and any(max(abs(s[0] - p[0]), abs(s[1] - p[1])) <= 1 for p in placed))
        if not nbrs:
            break
        pos = rng.choice(nbrs)
        place(dungeon, pos, first if rng.random() < 0.7 else _weighted(ids, rng))
        taken.add(pos)
        placed.append(pos)
    return len(placed)


def _room_contains_inner(room, x, y) -> bool:
    return room.x < x < room.x + room.width - 1 and room.y < y < room.y + room.height - 1


def _walk_set(dungeon) -> set:
    """Tiles the hero can walk to from the up stair (four ways, through
    doors and secret doors, never through water, lava or a blocker)."""
    from dungeon import STAIRS_UP, DOOR, SECRET_DOOR
    start = next(((x, y) for y in range(dungeon.height) for x in range(dungeon.width)
                  if dungeon.tiles[y][x] == STAIRS_UP), None)
    if start is None:
        return set()
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
    return seen


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


_ROOMS: dict | None = None
_LORE: dict | None = None


def room_dressing() -> dict:
    global _ROOMS
    if _ROOMS is None:
        from paths import data_path
        _ROOMS = _load(data_path('data', 'room_dressing.json'))
    return _ROOMS


def lore_fixtures() -> dict:
    global _LORE
    if _LORE is None:
        from paths import data_path
        _LORE = _load(data_path('data', 'lore_fixtures.json'))
    return _LORE


def _room_for_center(dungeon, center):
    for room in dungeon.rooms:
        if tuple(room.center) == tuple(center):
            return room
    return None


def _place_layer(dungeon, room, layer: str, spec: dict, taken: set, placed_blocks: list, rng) -> int:
    lo, hi = spec.get('count', [1, 1])
    want = rng.randint(int(lo), int(hi))
    if want <= 0:
        return 0
    if layer == 'floor':
        return _place_floor_layer(dungeon, room, spec['ids'], want, taken, rng)
    n = 0
    if layer == 'wall':
        spots = [t for t in _ring_walls(room, dungeon) if t not in fixtures_of(dungeon)]
    elif layer == 'water':
        from dungeon import WATER
        spots = [(x, y) for y in range(room.y + 1, room.y + room.height - 1)
                 for x in range(room.x + 1, room.x + room.width - 1)
                 if dungeon.in_bounds(x, y) and dungeon.tiles[y][x] == WATER
                 and (x, y) not in fixtures_of(dungeon)]
    elif layer == 'stand':
        spots = _against_wall_spots(room, dungeon, taken)
    else:
        spots = [t for t in _inner(room, dungeon) if t not in taken]
    rng.shuffle(spots)
    for pos in spots:
        if n >= want:
            break
        fid = _weighted(spec['ids'], rng)
        if fixture_def(fid).get('blocks'):
            if any(max(abs(pos[0] - b[0]), abs(pos[1] - b[1])) <= 1 for b in placed_blocks):
                continue
            placed_blocks.append(pos)
        place(dungeon, pos, fid)
        taken.add(pos)
        n += 1
    return n


def _place_floor_layer(dungeon, room, ids: dict, want: int, taken: set, rng) -> int:
    """A special room's loose floor pieces: its objects (bones, candles) as
    one group against a wall, its flat things (straw, reeds, dripped honey)
    anywhere in the room (Brandon's play-test, 2026-11-12)."""
    flat = {k: v for k, v in ids.items() if _flat(k)}
    objs = {k: v for k, v in ids.items() if not _flat(k)}
    wf, wo = float(sum(flat.values())), float(sum(objs.values()))
    n_obj = sum(1 for _ in range(want) if objs and (not flat or rng.random() * (wf + wo) >= wf))
    n = _place_cluster(dungeon, room, objs, n_obj, taken, rng) if n_obj else 0
    if flat:
        spots = [t for t in _inner(room, dungeon) if t not in taken]
        rng.shuffle(spots)
        for pos in spots[:want - n_obj]:
            place(dungeon, pos, _weighted(flat, rng))
            taken.add(pos)
            n += 1
    return n


def _lay_runner(dungeon, room, fid: str, taken: set) -> int:
    """A carpet from the throne to the far wall, along the room's longer
    side (a throne room's runner)."""
    from dungeon import THRONE
    throne = next(((x, y) for (x, y) in
                   ((x, y) for y in range(room.y, room.y + room.height)
                    for x in range(room.x, room.x + room.width))
                   if dungeon.in_bounds(x, y) and dungeon.tiles[y][x] == THRONE), None)
    if throne is None:
        return 0
    tx, ty = throne
    n = 0
    if room.height >= room.width:
        far_down = (room.y + room.height - 2) - ty
        far_up = ty - (room.y + 1)
        step = 1 if far_down >= far_up else -1
        line = [(tx, y) for y in range(ty + step, ty + step * (max(far_down, far_up) + 1), step)]
    else:
        far_r = (room.x + room.width - 2) - tx
        far_l = tx - (room.x + 1)
        step = 1 if far_r >= far_l else -1
        line = [(x, ty) for x in range(tx + step, tx + step * (max(far_r, far_l) + 1), step)]
    inner = set(_inner(room, dungeon))
    for pos in line:
        if pos in inner and pos not in fixtures_of(dungeon):
            place(dungeon, pos, fid)
            n += 1
    return n


def furnish_special_rooms(dungeon, taken: set, placed_blocks: list, rng) -> int:
    """Each special room's own furniture (data/room_dressing.json, A1)."""
    rooms_cfg = room_dressing().get('rooms') or {}
    n = 0
    for center, rtype in (dungeon.__dict__.get('special_rooms') or {}).items():
        cfg = rooms_cfg.get(rtype)
        room = _room_for_center(dungeon, center)
        if not cfg or room is None:
            continue
        if cfg.get('runner'):
            n += _lay_runner(dungeon, room, cfg['runner'], taken)
        for layer in ('wall', 'water', 'stand', 'floor'):
            spec = cfg.get(layer)
            if spec:
                n += _place_layer(dungeon, room, layer, spec, taken, placed_blocks, rng)
    return n


def _lore_tier(level: int) -> int:
    dom = domain_for(level)
    if not dom:
        return 1
    ids = [d['id'] for d in domains()]
    return min(5, ids.index(dom['id']) + 1)


def place_lore_fixtures(dungeon, level: int, taken: set, placed_blocks: list, rng) -> int:
    """Worth a Closer Look (data/lore_fixtures.json, B1): one to three lore
    fixtures, each in the special room it belongs to when the floor has
    one, otherwise in an ordinary room; the riddle lintel only over a
    hidden chamber's door."""
    cfg = lore_fixtures()
    if level < int(cfg.get('first_floor', 2)):
        return 0
    lo, hi = cfg.get('per_floor', [1, 3])
    want = min(3, rng.randint(int(lo), int(hi)))
    defs = cfg['fixtures']
    special = dungeon.__dict__.get('special_rooms') or {}
    chosen = []
    # Those that belong in a special room on this floor come first.
    for center, rtype in special.items():
        for fid, d in defs.items():
            if rtype in d.get('rooms', ()) and fid not in [c[0] for c in chosen]:
                room = _room_for_center(dungeon, center)
                if room is not None:
                    chosen.append((fid, room))
    # The lintel, over a hidden chamber's secret door.
    from dungeon import SECRET_DOOR
    doors = []
    for ch in dungeon.__dict__.get('hidden_chambers') or ():
        r = ch.get('room')
        if r is None:
            continue
        for y in range(r.y, r.y + r.height):
            for x in range(r.x, r.x + r.width):
                if dungeon.in_bounds(x, y) and dungeon.tiles[y][x] == SECRET_DOOR:
                    doors.append((x, y))
    n = 0
    state = dungeon.__dict__.setdefault('lore_fixtures', {})
    if doors and rng.random() < 0.5 and len(chosen) < want:
        pos = rng.choice(doors)
        if pos not in fixtures_of(dungeon):
            place(dungeon, pos, 'riddle_lintel')
            state[pos] = {'tier': _lore_tier(level)}
            n += 1
    skip = {id(r) for r in _skip_rooms(dungeon)}
    first = dungeon.rooms[0] if dungeon.rooms else None
    # Only rooms the hero can walk into (audit G15: a few stood behind a
    # pool or lava).
    reach = _walk_set(dungeon)

    def reachable(r):
        return not reach or any((x, y) in reach for (x, y) in _inner(r, dungeon))
    chosen = [(f, r) for (f, r) in chosen if reachable(r)]
    ordinary = [r for r in dungeon.rooms if id(r) not in skip and r is not first and reachable(r)]
    rng.shuffle(ordinary)
    free = [fid for fid, d in defs.items()
            if d.get('placement') not in ('secret_door', 'boss') and fid not in [c[0] for c in chosen]]
    rng.shuffle(free)
    for room, fid in zip(ordinary, free):
        if len(chosen) + n >= want:
            break
        chosen.append((fid, room))
    for fid, room in chosen[:max(0, want - n)]:
        layer = fixture_def(fid).get('layer', 'stand')
        if layer == 'wall':
            spots = [t for t in _ring_walls(room, dungeon) if t not in fixtures_of(dungeon)]
        else:
            spots = _against_wall_spots(room, dungeon, taken)
        rng.shuffle(spots)
        for pos in spots:
            if layer != 'wall' and any(max(abs(pos[0] - b[0]), abs(pos[1] - b[1])) <= 1
                                       for b in placed_blocks):
                continue
            place(dungeon, pos, fid)
            taken.add(pos)
            if fixture_def(fid).get('blocks'):
                placed_blocks.append(pos)
            state[pos] = {'tier': _lore_tier(level)}
            n += 1
            break
    return n


def lore_fixture_near(dungeon, x: int, y: int):
    """(pos, id) of an unspent lore fixture on or beside (x, y), or None."""
    state = dungeon.__dict__.get('lore_fixtures') or {}
    spent = dungeon.__dict__.get('fixture_state') or {}
    for oy in (0, -1, 1):
        for ox in (0, -1, 1):
            pos = (x + ox, y + oy)
            if pos in state and spent.get(pos) != 'spent':
                fid = fixture_at(dungeon, *pos)
                if fid:
                    return pos, fid
    return None


def arrival_lines(dungeon) -> None:
    """D1/G1: what the floor says on arrival, from what is really on it: its
    special rooms (these lines never fired before: the atmosphere was built
    before the rooms existed) and its domain hazards. Treasure is learned by
    exploring: the floor keeps an explore line for half-way."""
    import hazards
    msgs = dungeon.atmosphere_messages
    arr = room_dressing().get('arrival') or {}
    said = 0
    for rtype in (dungeon.__dict__.get('special_rooms') or {}).values():
        line = arr.get(rtype)
        if line and line not in msgs and said < 2:
            msgs.append(line)
            said += 1
    present = set(fixtures_of(dungeon).values())
    for fid in present:
        line = hazards.hazard_def(fid).get('arrival', '')
        if line and line not in msgs:
            msgs.append(line)
    rich = (dungeon.__dict__.get('vault') is not None
            or 'treasury' in (dungeon.__dict__.get('special_rooms') or {}).values()
            or any(ch.get('type') == 'treasure' for ch in dungeon.__dict__.get('hidden_chambers') or ()))
    if rich and arr.get('explore_line'):
        dungeon.explore_line = arr['explore_line']


# ---------------------------------------------------------------------------
# The five finales: gate floors and stair barriers (slice 6)
# ---------------------------------------------------------------------------

_BOSS: dict | None = None


def boss_floors() -> dict:
    global _BOSS
    if _BOSS is None:
        from paths import data_path
        _BOSS = _load(data_path('data', 'boss_floors.json'))
    return _BOSS


def _barrier_ids(guardian: str):
    bars = boss_floors().get('barriers') or {}
    if guardian in bars:
        return bars[guardian]
    if (guardian or '').startswith('seal_demon'):
        return bars.get('seal_demon')
    return None


def place_barrier(dungeon) -> bool:
    """Draw the bar across the down stair while the floor's keeper lives
    (the grate, the statues, the fire, the snow, the wax seal). The bar
    itself is main._descend_stairs's: this is its picture."""
    from dungeon import STAIRS_DOWN
    ids = _barrier_ids(getattr(dungeon, 'stairs_guardian', None) or '')
    if not ids:
        return False
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] == STAIRS_DOWN:
                place(dungeon, (x, y), ids[0])
                dungeon.barrier = {'pos': (x, y), 'open': ids[1]}
                return True
    return False


def open_barrier(dungeon) -> None:
    """The keeper is dead: the bar breaks (the grate rises, the statues
    topple, the fire dies, the snow slumps, the seal falls in pieces)."""
    bar = dungeon.__dict__.get('barrier')
    if not isinstance(bar, dict) or not bar.get('pos'):
        return
    place(dungeon, tuple(bar['pos']), bar.get('open') or 'rubble')
    bar['opened'] = True


def _isolated_walls(dungeon) -> list:
    """Free-standing wall columns: a WALL tile with walkable ground on at
    least five of its eight sides."""
    from dungeon import WALL
    out = []
    for y in range(1, dungeon.height - 1):
        for x in range(1, dungeon.width - 1):
            if dungeon.tiles[y][x] != WALL:
                continue
            open_sides = sum(1 for ox in (-1, 0, 1) for oy in (-1, 0, 1)
                             if (ox or oy) and dungeon.tiles[y + oy][x + ox] != WALL
                             and dungeon.tiles[y + oy][x + ox] != 5)
            if open_sides >= 7:
                out.append((x, y))
    return out


def _bbox_floor(room, dungeon) -> list:
    """Every walkable tile inside a room's box. A gate floor's rooms are
    carved without a wall ring, so their edge is floor too."""
    return [(x, y) for y in range(room.y, room.y + room.height)
            for x in range(room.x, room.x + room.width)
            if dungeon.in_bounds(x, y) and dungeon.is_walkable(x, y)]


def _in_bbox(room, x, y) -> bool:
    return room.x <= x < room.x + room.width and room.y <= y < room.y + room.height


def _room_wall_tiles(room, dungeon) -> list:
    """WALL tiles beside the room's floor (its walls, its pillars)."""
    from dungeon import WALL
    out = set()
    for (x, y) in _bbox_floor(room, dungeon):
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + a, y + b
            if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == WALL \
                    and (nx, ny) not in fixtures_of(dungeon):
                out.add((nx, ny))
    return sorted(out)


def _room_openings(room, dungeon) -> list:
    """The room's floor tiles that a way in opens onto."""
    from dungeon import DOOR
    out = []
    for (x, y) in _bbox_floor(room, dungeon):
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + a, y + b
            if not _in_bbox(room, nx, ny) and dungeon.in_bounds(nx, ny) and (
                    dungeon.is_walkable(nx, ny) or dungeon.tiles[ny][nx] == DOOR):
                out.append((x, y))
                break
    return out


def _room_wall_side(room, dungeon, taken: set) -> list:
    """Floor tiles of the room against a wall, away from every way in."""
    from dungeon import WALL
    openings = set(_room_openings(room, dungeon)) | _reserved_doors(dungeon)
    out = []
    for (x, y) in _bbox_floor(room, dungeon):
        if (x, y) in taken or (x, y) in openings:
            continue
        if not any(dungeon.tiles[y + b][x + a] == WALL for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if dungeon.in_bounds(x + a, y + b)):
            continue
        if any(max(abs(x - o[0]), abs(y - o[1])) <= 1 for o in openings):
            continue
        out.append((x, y))
    return out


def _boss_room(dungeon, monsters):
    guardian = getattr(dungeon, 'stairs_guardian', None)
    keeper = next((m for m in monsters or () if getattr(m, 'alive', True)
                   and (m.kind == guardian or getattr(m, 'is_boss', False))), None)
    if keeper is not None:
        for r in dungeon.rooms:
            if r.x <= keeper.x < r.x + r.width and r.y <= keeper.y < r.y + r.height:
                return r, keeper
    rooms = sorted(dungeon.rooms, key=lambda r: -(r.width * r.height))
    return (rooms[0] if rooms else None), keeper


def _walkable_floor(dungeon):
    from dungeon import FLOOR
    return [(x, y) for y in range(dungeon.height) for x in range(dungeon.width)
            if dungeon.tiles[y][x] == FLOOR and (x, y) not in fixtures_of(dungeon)]


def _spots(dungeon, where: str, layer: str, room, taken: set):
    from dungeon import WALL, FLOOR
    if layer == 'wall':
        if where == 'boss_room' and room is not None:
            return _room_wall_tiles(room, dungeon)
        out = []
        for y in range(1, dungeon.height - 1):
            for x in range(1, dungeon.width - 1):
                if dungeon.tiles[y][x] != WALL or (x, y) in fixtures_of(dungeon):
                    continue
                nbrs = [(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                flo = [n for n in nbrs if dungeon.tiles[n[1]][n[0]] == FLOOR]
                if not flo:
                    continue
                if where == 'junctions':
                    if not any(sum(1 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                                   if dungeon.is_walkable(n[0] + a, n[1] + b)) >= 3 for n in flo):
                        continue
                out.append((x, y))
        return out
    if layer == 'stand':
        if where == 'entry':
            first = dungeon.rooms[0] if dungeon.rooms else None
            return _room_wall_side(first, dungeon, taken) if first else []
        if room is None:
            return []
        return _room_wall_side(room, dungeon, taken)
    floor = [t for t in _walkable_floor(dungeon) if t not in taken]
    if where == 'boss_room' and room is not None:
        return [t for t in floor if _in_bbox(room, *t)]
    if where == 'items':
        held = dungeon.__dict__.get('_dress_item_tiles') or set()
        return [t for t in _walkable_floor(dungeon) if t in held]
    if where == 'dead_ends':
        return [t for t in floor
                if sum(1 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if dungeon.is_walkable(t[0] + a, t[1] + b)) == 1]
    return floor


def dress_boss_floor(dungeon, level: int, monsters=(), items=(), rng=None) -> int:
    """A gate floor dressed for its showdown (data/boss_floors.json)."""
    rng = rng or random.Random()
    apply_theme(dungeon, level)
    place_barrier(dungeon)
    spec = (boss_floors().get('floors') or {}).get(str(level))
    if not spec:
        return 0
    room, keeper = _boss_room(dungeon, monsters)
    taken = _taken_tiles(dungeon, monsters, items)
    dungeon._dress_item_tiles = {(getattr(i, 'x', -1), getattr(i, 'y', -1)) for i in items or ()}
    before = _reachable_count(dungeon)
    placed_blocks = []
    n = 0
    pillars = spec.get('pillars')
    if pillars:
        art = dungeon.__dict__.setdefault('tile_art', {})
        for pos in _isolated_walls(dungeon):
            art[pos] = 'floor'
            place(dungeon, pos, _weighted(pillars, rng))
            n += 1
    for layer in ('walls', 'stand', 'floor'):
        for part in spec.get(layer) or ():
            lay = 'wall' if layer == 'walls' else layer
            spots = _spots(dungeon, part.get('where', 'any'), lay, room, taken)
            rng.shuffle(spots)
            lo, hi = part.get('count', [1, 1])
            want = rng.randint(int(lo), int(hi))
            for pos in spots:
                if want <= 0:
                    break
                fid = _weighted(part['ids'], rng)
                if fixture_def(fid).get('blocks'):
                    if any(max(abs(pos[0] - b[0]), abs(pos[1] - b[1])) <= 1 for b in placed_blocks):
                        continue
                    placed_blocks.append(pos)
                place(dungeon, pos, fid)
                taken.add(pos)
                want -= 1
                n += 1
    if spec.get('entrance') and room is not None:
        for (x, y) in _room_openings(room, dungeon):
            if (x, y) not in taken:
                place(dungeon, (x, y), spec['entrance'])
                taken.add((x, y))
                n += 1
    dungeon.__dict__.pop('_dress_item_tiles', None)
    if spec.get('hoard') and room is not None and keeper is not None:
        art = dungeon.__dict__.setdefault('tile_art', {})
        r = int(spec['hoard'])
        for (x, y) in _bbox_floor(room, dungeon):
            if max(abs(x - keeper.x), abs(y - keeper.y)) <= r:
                art[(x, y)] = 'hoard'
    state = dungeon.__dict__.setdefault('lore_fixtures', {})
    for part in spec.get('lore') or ():
        fid = part['id']
        lay = fixture_def(fid).get('layer', 'stand')
        spots = _spots(dungeon, part.get('where', 'boss_room'), lay, room, taken)
        rng.shuffle(spots)
        lo, hi = part.get('count', [1, 1])
        want = rng.randint(int(lo), int(hi))
        for pos in spots:
            if want <= 0:
                break
            if fixture_def(fid).get('blocks'):
                if any(max(abs(pos[0] - b[0]), abs(pos[1] - b[1])) <= 1 for b in placed_blocks):
                    continue
                placed_blocks.append(pos)
            place(dungeon, pos, fid)
            taken.add(pos)
            state[pos] = {'tier': _lore_tier(level)}
            want -= 1
            n += 1
    if before > 0 and placed_blocks:
        while placed_blocks and _reachable_count(dungeon) < before - len(placed_blocks):
            pos = placed_blocks.pop()
            remove(dungeon, pos)
            state.pop(pos, None)
            n -= 1
    if spec.get('arrival') and spec['arrival'] not in dungeon.atmosphere_messages:
        dungeon.atmosphere_messages.append(spec['arrival'])
    return n


def boss_phase(dungeon, keeper, rng=None) -> str:
    """The keeper has turned (its enrage): the room changes with it
    (boss_floors.json 'phase'). Returns '' (the keeper's own line is said
    by the game)."""
    rng = rng or random.Random()
    spec = (boss_floors().get('floors') or {}).get(str(getattr(dungeon, 'level', 0))) or {}
    ph = (spec.get('phase') or {}).get(getattr(keeper, 'kind', ''))
    if not ph:
        return ''
    if ph.get('floor'):
        part = ph['floor']
        near = [t for t in _walkable_floor(dungeon)
                if max(abs(t[0] - keeper.x), abs(t[1] - keeper.y)) <= 5]
        rng.shuffle(near)
        lo, hi = part.get('count', [3, 5])
        for pos in near[:rng.randint(int(lo), int(hi))]:
            place(dungeon, pos, _weighted(part['ids'], rng))
    if ph.get('gutter'):
        lit = [pos for pos, fid in fixtures_of(dungeon).items() if fid == ph['gutter']]
        if lit:
            pos = rng.choice(lit)
            place(dungeon, pos, 'brazier_cold')
            (dungeon.__dict__.setdefault('lore_fixtures', {}))[pos] = {'tier': _lore_tier(dungeon.level)}
    return ''


def dress_floor(dungeon, level: int, monsters=(), items=(), rng=None) -> int:
    """Theme the floor and set its domain's dressing about it: the special
    rooms' own furniture, the lore fixtures, the domain's decor and hazards,
    then the arrival lines. Returns how many fixtures were placed. Call
    after the monsters and items are down, so nothing lands under a statue."""
    rng = rng or random.Random()
    dom = apply_theme(dungeon, level)
    if not dom:
        return 0
    decor = dom.get('decor') or {}
    taken = _taken_tiles(dungeon, monsters, items)
    skip = {id(r) for r in _skip_rooms(dungeon)}
    before = _reachable_count(dungeon)
    placed_blocks = []
    # A seal demon's floor: the red wax across the stair (slice 6, E0).
    place_barrier(dungeon)
    n = furnish_special_rooms(dungeon, taken, placed_blocks, rng)
    n += furnish_band_camp(dungeon, taken, placed_blocks, rng)
    n += place_lore_fixtures(dungeon, level, taken, placed_blocks, rng)
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
        # The loose floor layer: flat marks out in the room, or one small
        # group of objects against a wall (_place_cluster), never objects
        # dotted about the open floor.
        spec = decor.get('floor')
        if spec and rng.random() < float(spec.get('room_chance', 0)):
            flat = {k: v for k, v in spec['ids'].items() if _flat(k)}
            objs = {k: v for k, v in spec['ids'].items() if not _flat(k)}
            wf, wo = float(sum(flat.values())), float(sum(objs.values()))
            if objs and rng.random() * (wf + wo) >= wf:
                lo, hi = spec.get('cluster', [2, 3])
                n += _place_cluster(dungeon, room, objs, rng.randint(int(lo), int(hi)), taken, rng)
            elif flat:
                rng.shuffle(inner)
                lo, hi = spec.get('per_room', [1, 1])
                for pos in inner[:rng.randint(int(lo), int(hi))]:
                    place(dungeon, pos, _weighted(flat, rng))
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
    # Corridor decals: flat marks only (a jar or a skull in a corridor is
    # clutter in the way, not a story).
    spec = decor.get('floor')
    chance = float((spec or {}).get('corridor_chance', 0) or 0)
    corridors = _corridor_tiles(dungeon, taken)
    flat = {k: v for k, v in ((spec or {}).get('ids') or {}).items() if _flat(k)}
    if chance > 0 and flat:
        for pos in corridors:
            if rng.random() < chance:
                place(dungeon, pos, _weighted(flat, rng))
                taken.add(pos)
                n += 1
    # The domain's hazards (src/hazards.py): never in the arrival room,
    # never on a stair or beside one.
    import hazards
    from dungeon import STAIRS_UP, STAIRS_DOWN
    near_stairs = set()
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] in (STAIRS_UP, STAIRS_DOWN):
                near_stairs |= {(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
    # Never in the arrival room, nor the down-stair's room, where a hero
    # climbing back up (or fleeing Death) arrives (audit G16).
    first = dungeon.rooms[0] if dungeon.rooms else None
    downs = [(x, y) for y in range(dungeon.height) for x in range(dungeon.width)
             if dungeon.tiles[y][x] == STAIRS_DOWN]
    down_rooms = {id(r) for r in dungeon.rooms if any(_room_contains(r, sx, sy) for sx, sy in downs)}
    hz_rooms = [r for r in rooms if r is not first and id(r) not in down_rooms]
    n += hazards.place_hazards(dungeon, level, taken | near_stairs, hz_rooms,
                               [t for t in corridors if t not in taken], rng)
    # Nothing may cut the floor in two: undo blockers until the walk from
    # the up stair reaches as much as it did, less the tiles now furnished.
    if before > 0 and placed_blocks:
        while placed_blocks and _reachable_count(dungeon) < before - len(placed_blocks):
            pos = placed_blocks.pop()
            remove(dungeon, pos)
            (dungeon.__dict__.get('lore_fixtures') or {}).pop(pos, None)
            n -= 1
    arrival_lines(dungeon)
    return n
