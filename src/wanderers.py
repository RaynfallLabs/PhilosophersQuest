"""Wandering monsters: the floor's own first, newcomers only when the hero
lingers (3.5.1).

Brandon, play-testing floor 1: "I just don't think we need a constant stream
of monsters... I'd rather have a larger population at first, with complex
encounters set up, then a trickle if you hang around TOO LONG, but give the
player some time to explore... walking back and forth becomes a massive
chore."

Until 3.5.1 a newcomer came every 22 turns from the hero's first turn on a
floor, whenever it held fewer than about what it started with. Every kill
was replaced, and newcomers were half of all floor-1 fights. Now each floor
keeps a clock of the turns the hero has spent on it:

* **Time to explore.** Nothing new comes onto a floor for a grace measured
  from its own map: the walk of a full explore (``explore_tour``) times
  ``floor_curve.WANDER_GRACE_PER_TILE``, plus ``WANDER_GRACE_FLAT``.
* **The floor stirs.** Near the end of the grace, one line says he has been
  here a long while. When it runs out, another says things are coming.
* **A trickle.** Then a newcomer comes down a stair at a slow pace that
  quickens the longer he stays (``floor_curve.wander_gap``), up to the
  floor's old pace. The caps in main._maybe_wander_spawn still hold.
* **Coming back.** A hero who leaves and comes back finds the floor settled
  again: at least one full tour of quiet before the trickle starts over.

The floor's monsters are set down when it is made (dungeon.populate_floor,
war_bands, the dens, zoos and barracks); this module only paces newcomers.

Pure module: no pygame, no Game import. The simulator
(tools/balance/difficulty_sim.py) reads the same dials.
"""
from __future__ import annotations

import random
from collections import deque

import floor_curve

def _lines() -> dict:
    """data/senses.json 'wanderers': the floor's stirring lines."""
    import senses
    return senses.data().get('wanderers') or {}


def line(key: str, rng=None) -> str:
    """One of the floor's stirring lines: 'warning' or 'stirs'."""
    opts = list(_lines().get(key) or ())
    return (rng or random).choice(opts) if opts else ''


# ---------------------------------------------------------------------------
# The floor's explore tour
# ---------------------------------------------------------------------------

def _walk_map(dungeon):
    """The tiles a hero can walk across in a full explore (closed doors
    included: he opens them)."""
    from dungeon import DOOR
    w, h = dungeon.width, dungeon.height
    tiles = dungeon.tiles
    ok = set()
    for y in range(h):
        row = tiles[y]
        for x in range(w):
            if row[x] == DOOR or dungeon.is_walkable(x, y):
                ok.add((x, y))
    return ok


def _distances(ok: set, start) -> dict:
    dist = {start: 0}
    q = deque([start])
    while q:
        cx, cy = q.popleft()
        d0 = dist[(cx, cy)] + 1
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                n = (cx + ox, cy + oy)
                if n in ok and n not in dist:
                    dist[n] = d0
                    q.append(n)
    return dist


# A floor whose rooms hold less than this share of its walkable ground is a
# maze of passages (the maze floors 10, 30, 50, 70 and 90 hold about 5% in
# their few clearings, the Labyrinth on 20 13%; every room-and-corridor floor
# and the other gate floors 73% or more). Its explore walks the passages too.
MAZE_ROOM_SHARE = 0.5
# The passages of a maze are reached block by block: one stop in each square
# of this many tiles that holds passage.
MAZE_BLOCK = 10


def _room_stop(room, ok):
    """Where a full explore stands to see a room: its centre, or the
    walkable tile nearest it when a fountain, a statue or water stands
    there (such a room was left out of the tour)."""
    c = tuple(room.center)
    if c in ok:
        return c
    inner = [(x, y) for y in range(room.y, room.y + room.height)
             for x in range(room.x, room.x + room.width) if (x, y) in ok]
    if not inner:
        return None
    return min(inner, key=lambda t: (max(abs(t[0] - c[0]), abs(t[1] - c[1])), t))


def _passage_stops(dungeon, ok, rooms) -> list:
    """A maze's passages, one stop in each MAZE_BLOCK square that holds
    passage (walkable ground outside every room), or nothing on a floor of
    rooms and corridors (MAZE_ROOM_SHARE)."""
    in_room = set()
    for r in rooms:
        for y in range(r.y, r.y + r.height):
            for x in range(r.x, r.x + r.width):
                if (x, y) in ok:
                    in_room.add((x, y))
    if not ok or len(in_room) >= MAZE_ROOM_SHARE * len(ok):
        return []
    blocks: dict = {}
    for t in ok:
        if t not in in_room:
            blocks.setdefault((t[0] // MAZE_BLOCK, t[1] // MAZE_BLOCK), []).append(t)
    half = MAZE_BLOCK // 2
    out = []
    for (bx, by), tiles in sorted(blocks.items()):
        c = (bx * MAZE_BLOCK + half, by * MAZE_BLOCK + half)
        out.append(min(tiles, key=lambda t: (abs(t[0] - c[0]) + abs(t[1] - c[1]), t)))
    return out


def explore_tour(dungeon) -> int:
    """Tiles walked in a full explore of this floor: from the up stair, the
    nearest room not yet seen each time, every room, then the down stair.
    On a maze (MAZE_ROOM_SHARE) the walk reaches every stretch of its
    passages as well: its few clearings alone gave a maze floor a tour of
    20 tiles, and two minutes' grace in a maze of 1,900. Worked out once and
    kept on the floor."""
    have = dungeon.__dict__.get('_explore_tour')
    if have is not None:
        return int(have)
    from dungeon import STAIRS_UP, STAIRS_DOWN
    ok = _walk_map(dungeon)
    up = down = None
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            t = dungeon.tiles[y][x]
            if t == STAIRS_UP and up is None:
                up = (x, y)
            elif t == STAIRS_DOWN and down is None:
                down = (x, y)
    rooms = list(getattr(dungeon, 'rooms', None) or ())
    todo = [s for s in (_room_stop(r, ok) for r in rooms) if s is not None]
    todo += [s for s in _passage_stops(dungeon, ok, rooms) if s not in todo]
    cur = up or (todo[0] if todo else None)
    total = 0
    if cur is not None:
        while todo:
            dist = _distances(ok, cur)
            reach = [c for c in todo if c in dist]
            if not reach:
                break
            nxt = min(reach, key=dist.__getitem__)
            total += dist[nxt]
            todo.remove(nxt)
            cur = nxt
        if down is not None:
            total += _distances(ok, cur).get(down, 0)
    dungeon._explore_tour = int(total)
    return int(total)


def grace(dungeon) -> int:
    return floor_curve.wander_grace(explore_tour(dungeon))


# ---------------------------------------------------------------------------
# The floor's clock
# ---------------------------------------------------------------------------

def clock(dungeon) -> dict:
    c = dungeon.__dict__.get('_wander_clock')
    if c is None:
        c = {'here': 0, 'next': None, 'warned': False, 'stirred': False, 'last': None}
        dungeon._wander_clock = c
    return c


def _settle(dungeon, c: dict, away: int) -> None:
    """The hero has been off this floor for ``away`` turns: the floor
    settles by as much, down to one full tour of quiet before the trickle
    starts over. (Time spent away is what settles it, so a hop down the
    stair and straight back up buys nothing.)"""
    g = grace(dungeon)
    floor_to = max(0, g - max(100, explore_tour(dungeon)))
    if c['here'] <= floor_to:
        return
    c['here'] = max(floor_to, int(c['here']) - int(away))
    if c['here'] < g:
        c['next'] = None
        c['stirred'] = False
    if c['here'] < int(g * floor_curve.WANDER_WARN_SHARE):
        c['warned'] = False


# A gap this short in the game's turns is haste or a stair hop, not time away.
_AWAY_MIN = 3


def advance(dungeon, level: int, turn: int | None = None) -> tuple:
    """One turn of the hero's on this floor. Returns (line key or None,
    whether a newcomer is due now). ``turn`` is the game's turn count, so
    a return after time away is noticed."""
    c = clock(dungeon)
    if turn is not None:
        last = c.get('last')
        if last is not None:
            away = int(turn) - int(last) - 1
            if away > _AWAY_MIN:
                _settle(dungeon, c, away)
        c['last'] = int(turn)
    c['here'] = int(c['here']) + 1
    here = c['here']
    g = grace(dungeon)
    say = None
    if not c['warned'] and here >= int(g * floor_curve.WANDER_WARN_SHARE):
        c['warned'] = True
        say = 'warning'
    if here < g:
        return say, False
    if not c['stirred']:
        c['stirred'] = True
        c['warned'] = True
        c['next'] = here + floor_curve.wander_gap(level, 0)
        return 'stirs', True
    nxt = c.get('next')
    if nxt is None or here >= int(nxt):
        c['next'] = here + floor_curve.wander_gap(level, here - g)
        return say, True
    return say, False


def make_due(dungeon) -> None:
    """Tests and tools: the grace is long past and a newcomer is due on the
    next turn."""
    c = clock(dungeon)
    c['here'] = grace(dungeon) + 10 ** 6
    c['stirred'] = c['warned'] = True
    c['next'] = 0
    c['last'] = None
