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
    """Spawn the boss monster at the center of its chamber.

    For multi-tile bosses (footprint != (1, 1)), nudge the anchor so
    the whole footprint fits inside walkable tiles. The boss room is
    hand-crafted in this file and known to be large enough, but the
    naive center may put the anchor at a position where one of the
    extra footprint tiles falls outside the room."""
    from monster import Monster
    defn = _load_boss(boss_id)
    if defn is None:
        return []
    cx, cy = boss_room.center
    boss = Monster(defn, cx, cy)
    boss.is_boss = True
    # If multi-tile, ensure all footprint tiles are walkable. The
    # naive center is good enough for square boss rooms, but if any
    # extra tile lands on a wall or outside the dungeon we shift the
    # anchor NW until the whole footprint fits.
    fw, fh = boss.footprint
    if fw != 1 or fh != 1:
        for shift in range(3):
            ok = True
            for dy in range(fh):
                for dx in range(fw):
                    tx, ty = boss.x + dx, boss.y + dy
                    if not (dungeon.in_bounds(tx, ty)
                            and dungeon.is_walkable(tx, ty)):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                break
            # Shift NW one tile and retry
            boss.x -= 1
            boss.y -= 1
    return [boss]


# ---------------------------------------------------------------------------
# Level 20 -- Labyrinth of Asterion (The Minotaur)
# ---------------------------------------------------------------------------

# Labyrinth geometry. Cells are 2x2 floor blocks on a pitch of 4, so every
# passage is two tiles wide (room to sidestep, and for a charge to matter) and
# every wall is two tiles thick.
_LAB_X0, _LAB_Y0, _LAB_PITCH = 3, 3, 4
_LAB_COLS, _LAB_ROWS = 19, 11
# Asterion's hall: a block of cells in the middle, carved out whole.
_LAB_HALL = (7, 4, 11, 6)          # col0, row0, col1, row1 (inclusive)
# The stair chamber lies beyond the hall and is reached only through it.
_LAB_EXIT = (8, 8, 10, 9)
_LAB_PASSAGE = (9, 7)              # the cell between them


def _lab_cell_origin(i, j):
    return _LAB_X0 + i * _LAB_PITCH, _LAB_Y0 + j * _LAB_PITCH


def _lab_in_block(i, j, block):
    c0, r0, c1, r1 = block
    return c0 <= i <= c1 and r0 <= j <= r1


def _lab_is_maze_cell(i, j):
    return (0 <= i < _LAB_COLS and 0 <= j < _LAB_ROWS
            and not _lab_in_block(i, j, _LAB_HALL)
            and not _lab_in_block(i, j, _LAB_EXIT)
            and (i, j) != _LAB_PASSAGE)


def _lab_open(tiles, a, b):
    """Carve the two-wide gap between orthogonally adjacent cells a and b."""
    (i1, j1), (i2, j2) = sorted((a, b))
    x, y = _lab_cell_origin(i1, j1)
    if i2 != i1:        # east-west neighbours
        _fill(tiles, x + 2, y, x + 3, y + 1)
    else:               # north-south neighbours
        _fill(tiles, x, y + 2, x + 1, y + 3)


def _level_20_labyrinth(rng=None):
    """
    The Labyrinth of Knossos: a real maze, different every run.

    The player enters at the north-west corner. Asterion's hall is the block
    at the centre, with one way in from the west and one from the north. The
    stair down lies in a chamber beyond the hall and can only be reached by
    crossing it, so the way out is through the Minotaur.

    The maze is a depth-first maze with about 40% of its dead ends opened
    into loops, so there is usually more than one route and a hunted player
    can circle. The dead ends that remain hold what earlier visitors left.

    Asterion knows every wall: all interior walls are `phasing_walls` for
    him (see Monster._phase_move), which is what Ariadne's Thread takes away.

    The old layout was three straight east-west corridors joined by rungs.
    Two thirds of it, and most of its alcoves, could not be reached by the
    player at all, and the stairs could be walked to without a fight.
    """
    import random as _random
    rng = rng or _random.Random()
    tiles = _blank()

    # --- carve every maze cell -------------------------------------------
    cells = [(i, j) for i in range(_LAB_COLS) for j in range(_LAB_ROWS)
             if _lab_is_maze_cell(i, j)]
    for i, j in cells:
        x, y = _lab_cell_origin(i, j)
        _fill(tiles, x, y, x + 1, y + 1)

    def neighbours(c):
        i, j = c
        return [n for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))
                if _lab_is_maze_cell(*n)]

    # --- depth-first maze --------------------------------------------------
    links = {c: set() for c in cells}
    start = (0, 0)
    seen = {start}
    stack = [start]
    while stack:
        cur = stack[-1]
        fresh = [n for n in neighbours(cur) if n not in seen]
        if not fresh:
            stack.pop()
            continue
        nxt = rng.choice(fresh)
        links[cur].add(nxt)
        links[nxt].add(cur)
        _lab_open(tiles, cur, nxt)
        seen.add(nxt)
        stack.append(nxt)

    # --- braid: turn some dead ends into loops -----------------------------
    for c in cells:
        if len(links[c]) == 1 and c != start and rng.random() < 0.40:
            closed = [n for n in neighbours(c) if n not in links[c]]
            if closed:
                n = rng.choice(closed)
                links[c].add(n)
                links[n].add(c)
                _lab_open(tiles, c, n)

    # --- Asterion's hall -----------------------------------------------------
    c0, r0, c1, r1 = _LAB_HALL
    hx0, hy0 = _lab_cell_origin(c0, r0)
    hx1, hy1 = _lab_cell_origin(c1, r1)
    hx1 += 1
    hy1 += 1
    _fill(tiles, hx0, hy0, hx1, hy1)
    boss_room = Room(hx0, hy0, hx1 - hx0 + 1, hy1 - hy0 + 1)
    # Four rough pillars, so the hall is not an empty box.
    for px, py in ((hx0 + 4, hy0 + 2), (hx1 - 4, hy0 + 2),
                   (hx0 + 4, hy1 - 2), (hx1 - 4, hy1 - 2)):
        tiles[py][px] = WALL
    # Ways in: from the west (middle row) and from the north (middle column).
    wx, wy = _lab_cell_origin(c0 - 1, (r0 + r1) // 2)
    _fill(tiles, wx + 2, wy, wx + 3, wy + 1)
    nx, ny = _lab_cell_origin((c0 + c1) // 2, r0 - 1)
    _fill(tiles, nx, ny + 2, nx + 1, ny + 3)

    # --- the stair chamber, beyond the hall ---------------------------------
    e0, f0, e1, f1 = _LAB_EXIT
    ex0, ey0 = _lab_cell_origin(e0, f0)
    ex1, ey1 = _lab_cell_origin(e1, f1)
    ex1 += 1
    ey1 += 1
    _fill(tiles, ex0, ey0, ex1, ey1)
    exit_room = Room(ex0, ey0, ex1 - ex0 + 1, ey1 - ey0 + 1)
    pcx = _lab_cell_origin(*_LAB_PASSAGE)[0]
    _vline(tiles, hy1 + 1, ey0 - 1, pcx)            # one tile wide
    tiles[hy1 + 1][pcx] = DOOR
    tiles[ey1 - 1][exit_room.center[0]] = STAIRS_DOWN

    # --- entry ---------------------------------------------------------------
    sx, sy = _lab_cell_origin(*start)
    entry = Room(sx, sy, 2, 2)
    tiles[sy][sx] = STAIRS_UP

    rooms = [entry, boss_room, exit_room]
    dungeon = _make(tiles, rooms, 20)

    # --- Asterion's secret doors: every interior wall -----------------------
    dungeon.phasing_walls = {
        (x, y) for y in range(2, _H - 2) for x in range(2, _W - 2)
        if tiles[y][x] == WALL
    }
    # The stair is barred while he lives (main._descend_stairs).
    dungeon.stairs_guardian = 'asterion_minotaur'
    dungeon.stairs_guardian_line = (
        "A bronze grate is shut across the stair. Whatever keeps this maze "
        "still keeps the key.")
    dungeon.stairs_guardian_open_line = (
        "Somewhere beyond the hall, a bronze grate swings open.")
    dungeon.atmosphere_messages = [
        "These passages were built to lose people. Something heavy is walking "
        "on the other side of the wall.",
    ]

    # --- what earlier visitors left in the dead ends -------------------------
    items = []
    dead_ends = [c for c in cells if len(links[c]) == 1 and c != start]
    rng.shuffle(dead_ends)
    try:
        from items import (add_gold_to_tile, load_items, copy_at,
                           pick_random_weapon_for_floor, pick_random_armor_for_floor)
        potions = {pt.id: pt for pt in load_items('potion')}
        for n, (i, j) in enumerate(dead_ends[:7]):
            x, y = _lab_cell_origin(i, j)
            if n < 3:
                add_gold_to_tile(items, rng.randint(40, 110), x, y)
            elif n == 3:
                w = pick_random_weapon_for_floor(20, rng)
                if w is not None:
                    w.x, w.y = x, y
                    items.append(w)
            elif n == 4:
                arm = pick_random_armor_for_floor(20, rng)
                if arm is not None:
                    arm.x, arm.y = x, y
                    items.append(arm)
            else:
                heal = potions.get('potion_of_healing')
                if heal is not None:
                    items.append(copy_at(heal, x, y))
    except Exception:
        items = [it for it in items if it is not None]

    return dungeon, _spawn_boss(dungeon, 'asterion_minotaur', boss_room), items


def labyrinth_thread_route(dungeon) -> list:
    """Tiles on a shortest walk from the up stair to Asterion's hall.

    Ariadne's Thread shows the way: main marks these explored when the
    player arrives on floor 20 carrying it."""
    from collections import deque
    start = None
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.tiles[y][x] == STAIRS_UP:
                start = (x, y)
                break
        if start:
            break
    if start is None or len(dungeon.rooms) < 2:
        return []
    goal = dungeon.rooms[1].center
    prev = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        cx, cy = cur
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cx + dx, cy + dy)
            if nxt in prev or not dungeon.in_bounds(*nxt):
                continue
            if dungeon.tiles[nxt[1]][nxt[0]] == WALL:
                continue
            prev[nxt] = cur
            queue.append(nxt)
    if goal not in prev:
        return []
    route = []
    cur = goal
    while cur is not None:
        route.append(cur)
        cur = prev[cur]
    return route[::-1]


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

    # Pillars in the sanctum: cover against Medusa's gaze, which reaches
    # across open floor but not through stone. Two rows of four, so there is
    # always a pillar to step behind, and none on the centre line from the
    # door: she sees whoever walks straight in.
    for px in (33, 37, 41, 45):
        for py in (41, 45):
            tiles[py][px] = WALL

    # Exit passage
    exit_room = _carve_room(tiles, 68, 43, 4, 3)
    rooms.append(exit_room)
    _hline(tiles, boss_room.x + boss_room.width, exit_room.x, 43)
    tiles[exit_room.center[1]][exit_room.x + exit_room.width // 2] = STAIRS_DOWN

    dungeon = _make(tiles, rooms, 40)

    # The way down lies past the sanctum and is shut while she lives.
    dungeon.stairs_guardian = 'medusa_gorgon'
    dungeon.stairs_guardian_line = (
        "The stair is choked with statues, shoulder to shoulder, every one "
        "caught in the act of leaving. They will not move while she still "
        "looks this way.")
    dungeon.stairs_guardian_open_line = (
        "Beyond the sanctum, stone figures topple and break. The stair is clear.")
    dungeon.atmosphere_messages = [
        "Statues line the portico. Every one is looking back over its shoulder.",
    ]

    # The side chapels hold what her earlier visitors carried, and one of
    # them holds the cheap answer: a blindfold, tied over a statue's eyes too
    # late to help its owner. It is always here, so a player who missed the
    # Eye and the Aegis still has a way to fight her.
    items = []
    try:
        import random as _random
        from items import (add_gold_to_tile, load_items, copy_at,
                           pick_random_weapon_for_floor, pick_random_shield_for_floor)
        blindfold = next((a for a in load_items('armor') if a.id == 'blindfold'), None)
        if blindfold is not None:
            bx, by = l_chapel2.center
            bf = copy_at(blindfold, bx, by)
            bf.buc = 'uncursed'
            items.append(bf)
        gx, gy = l_chapel.center
        add_gold_to_tile(items, _random.randint(120, 260), gx, gy)
        w = pick_random_weapon_for_floor(40, _random)
        if w is not None:
            w.x, w.y = r_chapel.center
            items.append(w)
        potions = {pt.id: pt for pt in load_items('potion')}
        heal = potions.get('potion_of_extra_healing') or potions.get('potion_of_healing')
        if heal is not None:
            hx, hy = r_chapel2.center
            items.append(copy_at(heal, hx, hy))
        sh = pick_random_shield_for_floor(40, _random)
        if sh is not None:
            sh.x, sh.y = r_chapel2.center[0] + 1, r_chapel2.center[1]
            items.append(sh)
    except Exception:
        items = [it for it in items if it is not None]

    return dungeon, _spawn_boss(dungeon, 'medusa_gorgon', boss_room), items


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

    # Rock formations: cover from the breath on the way in
    for rx, ry in [(36, 41), (36, 42), (48, 44), (48, 45)]:
        tiles[ry][rx] = WALL

    # Exit tunnel (narrow passage to the right)
    exit_room = _carve_room(tiles, 70, 43, 5, 3)
    rooms.append(exit_room)
    _hline(tiles, boss_room.x + boss_room.width, exit_room.x, boss_room.center[1])
    tiles[exit_room.center[1]][exit_room.x + exit_room.width // 2] = STAIRS_DOWN

    dungeon = _make(tiles, rooms, 60)

    # Someone has been here before with Sigurd's idea: one old pit, already
    # dug, off to one side of the lair. A player who never found the Shovel
    # (or the broken blade that buys it) can still fight from below, so the
    # barred stair can never strand a run. The Shovel's worth is choosing
    # WHERE to dig.
    dungeon.old_pit = (38, 46)
    dungeon.pits.add(dungeon.old_pit)

    # The way down is past the lair and shut while he lives.
    dungeon.stairs_guardian = 'fafnir_dragon'
    dungeon.stairs_guardian_line = (
        "A curtain of fire hangs across the stair and does not burn down. "
        "It is his fire.")
    dungeon.stairs_guardian_open_line = (
        "Beyond the lair, the fire across the stair gutters and goes out.")
    dungeon.atmosphere_messages = [
        "The rock is warm underfoot. A worn track, wide as a cart road, runs "
        "down toward the sound of water.",
    ]

    # The hoard. Boss floors used to return no items at all, so the
    # "gold-littered hoard chamber" was bare stone.
    items = []
    try:
        import random as _random
        from items import (add_gold_to_tile, pick_random_weapon_for_floor,
                           pick_random_armor_for_floor, pick_random_shield_for_floor)
        hx, hy = hoard.center
        for dx, dy in ((-9, -5), (-4, 4), (3, -6), (8, 2), (-11, 3), (10, -3)):
            x, y = hx + dx, hy + dy
            if tiles[y][x] == FLOOR:
                add_gold_to_tile(items, _random.randint(150, 350), x, y)
        gear = (pick_random_weapon_for_floor, pick_random_armor_for_floor,
                pick_random_shield_for_floor, pick_random_weapon_for_floor)
        alcoves = [r for r in rooms if r not in (entry, ante1, ante2, ante3, side1,
                                                 side2, hoard, boss_room, exit_room)]
        for alcove, pick in zip(alcoves, gear):
            ax, ay = alcove.center
            add_gold_to_tile(items, _random.randint(300, 600), ax, ay)
            it = pick(60, _random)
            if it is not None:
                it.x, it.y = ax + 1, ay
                items.append(it)
    except Exception:
        items = [it for it in items if it is not None]

    return dungeon, _spawn_boss(dungeon, 'fafnir_dragon', boss_room), items


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

    # Altar ring around the boss chamber (6 altars for holy fire prayers).
    # Placed AFTER the arena and its doors are carved: placed before, the
    # room carve and the doors overwrote all six and level 100 shipped with
    # no altar at all, so the Abaddon holy-fire prayer could not be used.
    # Each altar goes on the nearest plain FLOOR tile to its intended spot.
    for ax, ay in [
        (center_x - 8, center_y),
        (center_x + 8, center_y),
        (center_x, center_y - 8),
        (center_x, center_y + 8),
        (center_x - 6, center_y - 6),
        (center_x + 6, center_y - 6),
    ]:
        spots = sorted(
            ((abs(dx) + abs(dy), ax + dx, ay + dy)
             for dx in range(-3, 4) for dy in range(-3, 4)),
        )
        for _dist, sx, sy in spots:
            if 0 <= sy < _H and 0 <= sx < _W and tiles[sy][sx] == FLOOR:
                tiles[sy][sx] = ALTAR
                break

    # No STAIRS_DOWN -- this is the final level. The Philosopher's Stone drops
    # where Abaddon falls (game_combat._drop_philosophers_stone). We add an
    # exit to the entry for tactical retreat.

    dungeon = _make(tiles, rooms, 100)
    return dungeon, _spawn_boss(dungeon, 'abaddon_destroyer', boss_room), []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _make(tiles, rooms, level):
    """Create a Dungeon object from tiles and rooms."""
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
