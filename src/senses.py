"""How a monster comes to know where the hero is (Dungeon Alive, 2026-11-12).

Brandon: "Monsters should have their own behaviors and patterns, but NONE
automatically know where you are unless it's thematically and lore
appropriate." Until now every monster noticed the hero within 8 tiles
through solid stone, then knew where he was for the rest of the floor.

A monster now notices the hero in one of three ways:

* **Sight**: a real line of sight within its perception range. Invisibility
  hides him from eyes, unless the eyes are a celestial's. A lit torch,
  lantern or Light spell shows him from farther (lights.shine).
* **Sound**: the noise he makes. Footsteps carry a few tiles; DEX, a heavy
  pack, Cat's Footfall and silent walking change how far. A fight, a door,
  coin or an alarm carries further. Sound travels along open ground, round
  corners and through doorways, never through stone. A sound gives the
  monster a PLACE to go and look, not the hero.
* **A lore sense** (data/senses.json):
  - a wolf's or a giant's nose ("Fee, fi, fo, fum");
  - a snake's or a spider's feel for footsteps;
  - the hungry dead feeling the warmth of the living;
  - a bat's echoes;
  - the Furies finding the guilty;
  - the master of a house knowing his own house (Asterion).

What it does with what it knows:

* **Hunting**: it senses him now and comes for him, by a real path round
  the walls when it has no clear view.
* **Searching**: it lost him, or heard something. It goes to the place,
  looks about for a while, then gives up.
* **Its own business** before that, chosen when the floor is made: it
  sleeps, keeps its post, or roams from room to room.

``_aware`` keeps its old meaning: the monster has noticed the hero at least
once (an ambusher has sprung, a mimic has dropped its disguise).
``_tracking`` is new: it knows where he is right now.

Pure module: no pygame, no Game import.
"""
from __future__ import annotations

import json
import random
from collections import deque
import random_streams

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'senses.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


class Turn:
    """What the game knows about this turn, set by the game before the
    monsters act (``begin_turn``). Tests and tools that call take_turn
    directly get the defaults."""
    moved = True          # the hero changed tile this turn
    guilty = False        # the hero carries a wrong on his conscience
    floor = 0
    rested = False        # the hero's action this turn was a rest (the wait key)


TURN = Turn()


def begin_turn(*, moved: bool, guilty: bool, floor: int, rested: bool = False) -> None:
    TURN.moved = bool(moved)
    TURN.guilty = bool(guilty)
    TURN.floor = int(floor or 0)
    TURN.rested = bool(rested)


def note_rest(player, turn: int) -> None:
    """The hero rests (the wait key: a wait, a meditation) on game turn
    ``turn``, the one about to pass. A stalker who preys on rest reads it
    (Monster._stalker_turn: Old Nickel darts in on a resting hero)."""
    player.__dict__['_rest_turn'] = int(turn)


def rested_on(player, turn: int) -> bool:
    """Was the hero's action on game turn ``turn`` a rest?"""
    return player.__dict__.get('_rest_turn') == int(turn)


# ---------------------------------------------------------------------------
# Which senses a creature has
# ---------------------------------------------------------------------------

def senses_of(m) -> list:
    d = data()
    kind = getattr(m, 'kind', '') or ''
    fam = d['families'].get(getattr(m, 'family', '') or '', [])
    own = d['monsters'].get(kind)
    if own is None:
        return list(fam)
    out = list(own)
    # A kind's own list replaces its family's lore senses, but a family's
    # 'blind' (oozes, plants) always holds.
    if 'blind' in fam and 'blind' not in out:
        out.append('blind')
    return out


def sense_range(m, sense: str) -> int:
    d = data()
    own = d.get('monster_ranges', {}).get(getattr(m, 'kind', '') or '', {})
    if sense in own:
        return int(own[sense])
    fam = d.get('ranges', {}).get(getattr(m, 'family', '') or '', {})
    if sense in fam:
        return int(fam[sense])
    return int(d['senses'].get(sense, {}).get('range', 0) or 0)


def sense_names(m) -> list:
    """The player-facing names of a creature's lore senses, for Observe."""
    names = data()['sense_names']
    return [names[s] for s in senses_of(m) if s in names]


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


# ---------------------------------------------------------------------------
# Seeing
# ---------------------------------------------------------------------------

def clear_view(x0: int, y0: int, x1: int, y1: int, dungeon) -> bool:
    """True if nothing opaque (wall, closed door, rock) stands between the
    two tiles (Dungeon.is_opaque: tall fixtures such as statues block it, low
    furniture, water and lava do not). A diagonal
    step between two opaque corners is blocked, as it is for arrows."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    opaque = getattr(dungeon, 'is_opaque', None)
    if opaque is None:                 # a bare test map: stone is what blocks
        def opaque(x, y):
            return not dungeon.is_walkable(x, y)
    while (cx, cy) != (x1, y1):
        e2 = 2 * err
        step_x = e2 > -dy
        step_y = e2 < dx
        if step_x and step_y and opaque(cx + sx, cy) and opaque(cx, cy + sy):
            return False
        if step_x:
            err -= dy
            cx += sx
        if step_y:
            err += dx
            cy += sy
        if (cx, cy) != (x1, y1) and opaque(cx, cy):
            return False
    return True


def sight_range(m, player=None) -> int:
    base = int(getattr(m, 'perception_range', 8) or 8)
    if 'keen_sight' in senses_of(m):
        base += int(data()['senses']['keen_sight'].get('sight_bonus', 4))
    if player is not None:
        import gear
        # The Hand of Glory and the Boots of Elvenkind: a monster has half
        # its usual reach on the wearer, as the item text says.
        if gear.wears_flag(player, 'passive_silent_walk'):
            base = max(1, base // 2)
        # A light shows the hero to every eye in the dark (lights.py,
        # 2026-11-19): a lit hero is seen from farther by the brightest
        # light's notice (a torch 2, the Light spell 3; the dark lantern's
        # shutter keeps it to 2). Doused, it costs nothing.
        import lights
        base += lights.shine(player)
    return base


def sees(m, player, dungeon) -> bool:
    ss = senses_of(m)
    if 'blind' in ss:
        return False
    d = _cheb(m.x, m.y, player.x, player.y)
    if d > sight_range(m, player):
        return False
    if d <= 1:
        return True
    import wards
    if wards.veil_hides(player, m, d):
        return False                  # the Mist of Manannan: it sees only what is close
    if player.has_effect('invisible') and 'truesight' not in ss:
        return False
    return clear_view(m.x, m.y, player.x, player.y, dungeon)


def lore_sense(m, player, dungeon):
    """The lore sense by which ``m`` finds the hero now, or None."""
    specs = data()['senses']
    for s in senses_of(m):
        spec = specs.get(s) or {}
        if 'range' not in spec:
            continue                      # a modifier, not a sense of its own
        if s == 'master':
            return s
        if _cheb(m.x, m.y, player.x, player.y) > sense_range(m, s):
            continue
        if spec.get('needs_motion') and not TURN.moved:
            continue
        if spec.get('fails_at_rest') and TURN.rested and _cheb(m.x, m.y, player.x, player.y) > 1:
            continue                      # he holds his breath (the jiangshi)
        if spec.get('needs_bleeding') and not player.has_effect('bleeding'):
            continue                      # no blood to follow (the Komodo)
        if s == 'tremor' and player.has_effect('levitating'):
            continue
        if s == 'guilt' and not TURN.guilty:
            continue
        if not spec.get('through_walls') and not clear_view(m.x, m.y, player.x, player.y, dungeon):
            continue
        return s
    return None


def _hidden(m, player, dungeon) -> bool:
    import wards
    if wards.hidden_from(player, m):
        return True                   # a sight ward (Hoichi's sutra): this family cannot see him
    try:
        from chain_passives import is_player_hidden_from
    except ImportError:
        return False
    return bool(is_player_hidden_from(player, m, dungeon))


def perceive(m, player, dungeon):
    """How ``m`` knows where the hero is this turn: 'sight', a lore sense's
    name, 'aggravated', or None."""
    if _hidden(m, player, dungeon):
        return None
    if player.has_effect('aggravated'):
        return 'aggravated'
    if sees(m, player, dungeon):
        return 'sight'
    return lore_sense(m, player, dungeon)


# ---------------------------------------------------------------------------
# Noise
# ---------------------------------------------------------------------------

def noise_radius(kind: str) -> int:
    return int(data()['noise'].get(kind, 0) or 0)


def step_radius(player) -> int:
    """How far the hero's footsteps carry (0 = silent)."""
    n = data()['noise']
    try:
        import sleepers
        if sleepers.factor(player, 'step') <= 0:
            return 0
    except Exception:
        pass
    r = int(n['step'])
    try:
        dex = int(getattr(player, 'DEX', 10) or 10)
    except (TypeError, ValueError):
        dex = 10
    r -= max(0, dex - 10) // max(1, int(n['dex_per_tile']))
    # The load (Light +1, Heavy +2, Burdened +3, Overloaded +3: Player.load_tier,
    # data/senses.json noise) and the body
    # armour (medium +1, heavy +2, metal +1 more unless quiet:
    # gear.footstep_tiles; winning-build plan 3.3).
    try:
        tier = player.load_tier() if hasattr(player, 'load_tier') else (
            'burdened' if player.is_burdened() else '')
        if tier:
            r += int(n.get(tier, 0))
    except Exception:
        pass
    try:
        import gear
        r += gear.footstep_tiles(player)
    except Exception:
        pass
    # A galloping Bococho is loud (riding.step_noise; data/bococho.json).
    if getattr(player, 'riding', False):
        try:
            import riding
            r += riding.step_noise(player)
        except Exception:
            pass
    return max(1, r)


def emit(dungeon, x: int, y: int, kind: str, radius: int | None = None) -> None:
    """Something at (x, y), usually the hero, made a noise of ``kind``."""
    if dungeon is None:
        return
    r = noise_radius(kind) if radius is None else int(radius)
    if r <= 0:
        return
    dungeon.__dict__.setdefault('_noises', []).append((int(x), int(y), kind, r))


def sound_map(dungeon, x: int, y: int, radius: int) -> dict:
    """{tile: distance} for every tile the sound reaches: along open
    ground, round corners and through doorways (a closed door costs
    ``door_cost``). Stone stops it."""
    from dungeon import WALL, DOOR, SECRET_DOOR
    door_cost = int(data()['noise'].get('door_cost', 3))
    tiles = dungeon.tiles
    w, h = dungeon.width, dungeon.height
    dist = {(x, y): 0}
    q = deque([(x, y)])
    while q:
        cx, cy = q.popleft()
        d0 = dist[(cx, cy)]
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if not ox and not oy:
                    continue
                nx, ny = cx + ox, cy + oy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                t = tiles[ny][nx]
                if t == WALL or t == SECRET_DOOR:
                    continue
                nd = d0 + (door_cost if t == DOOR else 1)
                if nd > radius:
                    continue
                if nd < dist.get((nx, ny), 1 << 30):
                    dist[(nx, ny)] = nd
                    q.append((nx, ny))
    return dist


def _hears(m) -> bool:
    return (getattr(m, 'family', '') or '') != 'plants'


def _wake_p(m, kind: str, d: int, r: int, player) -> float:
    """The chance a sleeper wakes to a noise of `kind` `d` tiles off (`r`
    the noise's reach)."""
    w = data()['waking']
    import sleepers
    if sleepers.laid(m):
        return 0.0                  # a spell's sleep (Mass Sleep...): only a blow wakes it
    if sleepers.factor(player, 'take') <= 0:       # the Hand of Glory
        return 0.0
    if sleepers.is_deep_sleeper(m):
        # The deep sleepers of a zoo, graveyard or barracks keep their own
        # odds (sleepers.py); only a fight or an alarm right beside one may
        # break that sleep.
        return float(w['deep_loud']) if (kind != 'step' and d <= int(w['deep_loud_reach'])) else 0.0
    if kind == 'step':
        return float(w['step_near'] if d <= int(w['near']) else w['step_far']) \
            * sleepers.factor(player, 'step')
    return float(w['loud'] if d * 2 <= r else w['loud_far'])


def _wakes(m, kind: str, d: int, r: int, player, rng) -> bool:
    return rng.random() < _wake_p(m, kind, d, r, player)


def _listens(m) -> bool:
    return (getattr(m, 'alive', False) and not getattr(m, 'is_allied', False)
            and not getattr(m, '_npc_encounter_tag', None)
            and not getattr(m, '_flavor_encounter_tag', None) and _hears(m))


def resolve_noises(dungeon, monsters, player, rng=None) -> list:
    """Hand this turn's noises to the monsters that hear them. Each one that
    does keeps ``_heard`` (x, y, kind) for its next move, and a sleeper may
    wake. Returns the monsters woken. Clears the noise list."""
    rng = rng or random
    noises = dungeon.__dict__.pop('_noises', None) or []
    if not noises:
        return []
    bonus = int(data()['noise'].get('hunter_bonus', 3))
    woken = []
    from geom import occupied_tiles
    reaches = [(nx, ny, kind, r, sound_map(dungeon, nx, ny, r + bonus))
               for nx, ny, kind, r in noises]
    for m in monsters or ():
        if not _listens(m):
            continue
        tiles = list(occupied_tiles(m))
        heard = []
        for nx, ny, kind, r, reach in reaches:
            ds = [reach[t] for t in tiles if t in reach]
            if not ds:
                continue
            d = min(ds)
            if d > r + (bonus if m.__dict__.get('_tracking') else 0):
                continue
            heard.append((nx, ny, kind, r, d))
        if not heard:
            continue
        if m.has_effect('sleeping'):
            # One chance to wake a turn, at the turn's most waking noise: a
            # fight is two noises a round, and a roll for each made the
            # sleepers near it all but sure to wake (Brandon, 2026-11-12:
            # "they all seemed to come running").
            p = max(_wake_p(m, k, dd, rr, player) for _x, _y, k, rr, dd in heard)
            if rng.random() >= p:
                continue
            m.status_effects.pop('sleeping', None)
            woken.append(m)
        for nx, ny, kind, _r, _d in heard:
            prev = m.__dict__.get('_heard')
            if prev is None or (prev[2] == 'step' and kind != 'step'):
                m._heard = (nx, ny, kind)
    return woken


def rouse(m, x: int, y: int) -> None:
    """Something called this monster to (x, y): an ally's cry, an alarm. One
    under a spell's sleep sleeps on (sleepers.laid): it goes there when it
    wakes."""
    import sleepers
    m._alerted = True
    m._aware = True
    m._goal = (int(x), int(y))
    m._searching = False
    m._lead_used = True
    if not sleepers.laid(m):
        m.status_effects.pop('sleeping', None)


def rouse_near(monsters, x: int, y: int, radius: int, dungeon=None) -> int:
    """Rouse every listening creature the sound of (x, y) reaches within
    ``radius`` (an alarm, a chest that shrieks). Returns how many."""
    n = 0
    reach = sound_map(dungeon, x, y, radius) if dungeon is not None else None
    for m in monsters or ():
        if not _listens(m):
            continue
        if reach is not None:
            if (m.x, m.y) not in reach:
                continue
        elif abs(m.x - x) + abs(m.y - y) > radius:
            continue
        rouse(m, x, y)
        n += 1
    return n


# ---------------------------------------------------------------------------
# Moving with purpose
# ---------------------------------------------------------------------------

# Wait Your Turn (AI-2, fix_corridor_pathing, 2026-11-20): a hunter stuck
# behind one of its own side in a narrow way waits its turn instead of
# walking off on any detour, however long, and searching again every turn;
# a way round is taken only if it is at most `slack` steps longer than the
# straight way (data/minds.json `queue`). QUEUE is the scenario harness's
# ablation.
QUEUE = True


def queue_rules() -> dict:
    try:
        import tactics
        return tactics.data().get('queue') or {}
    except (ImportError, OSError, ValueError):
        return {}


# What keeps a friend in the way from moving on: a creature does not wait
# behind one that will not move (asleep, held, rooted, begging).
_STUCK = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'immobilized', 'impaled',
          'stuck_in_pit', 'feared', 'charmed', 'confused')


def _friend_at(m, all_monsters, tile) -> bool:
    """One of its own side stands on ``tile`` and will move on: awake, free,
    not rooted, not broken by its morale, and itself hunting the hero. (A
    pet, a stranger or a friend that will not move is gone round, as
    before: a creature does not wait politely behind those.)"""
    import faction
    for o in all_monsters or ():
        if o is not m and getattr(o, 'alive', False) and (o.x, o.y) == tuple(tile):
            if not faction.same_side(m, o):
                return False
            od = getattr(o, '__dict__', {})
            if getattr(o, 'ai_pattern', '') in ('sessile', 'mimic') or not od.get('_tracking'):
                return False
            if any(int((getattr(o, 'status_effects', None) or {}).get(e, 0) or 0) > 0
                   for e in _STUCK):
                return False
            if (od.get('_yielded') or od.get('_cowed')
                    or int(od.get('_flee_timer', 0) or 0) > 0):
                return False
            return True
    return False


def keeps_way_round(m, player, all_monsters) -> bool:
    """It sees the hero, but a creature stands on the straight line to him,
    and it is already on its way round (a path to his tile from an earlier
    turn): it keeps to that way. It used to step greedily back into the
    blocked line each turn it saw him, and out again, for ever."""
    if not QUEUE or player is None:
        return False
    d = m.__dict__
    if not d.get('_path') or d.get('_path_goal') != (player.x, player.y):
        return False
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles([o for o in all_monsters or () if getattr(o, 'alive', False)],
                                 exclude=m))
    x0, y0, x1, y1 = m.x, m.y, player.x, player.y
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while (cx, cy) != (x1, y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
        if (cx, cy) != (x1, y1) and (cx, cy) in occ:
            return True
    return False


def rooted(m) -> bool:
    """It never walks: a mold, a floating eye, the Emberpup on his rock, a
    figure of a story (ai_pattern 'sessile', or stationary: the Black Knight)."""
    return getattr(m, 'ai_pattern', '') == 'sessile' or bool(getattr(m, 'stationary', False))


def _avoid_fn(m, dungeon):
    """A creature that knows the floor's snares (tactical_mind: knows_traps)
    keeps off them when it has another way; None for every other."""
    try:
        import tactical_mind
        if not tactical_mind.flag(m, 'knows_traps'):
            return None
    except (ImportError, OSError, ValueError):
        return None

    def avoid(x, y):
        return tactical_mind.hazard_here(dungeon, x, y) is not None
    return avoid


def _passable_fn(m, dungeon):
    from dungeon import DOOR
    fw, fh = tuple(getattr(m, 'footprint', (1, 1)) or (1, 1))
    tiles = dungeon.tiles
    if (fw, fh) == (1, 1) and not getattr(m, 'can_phase_walls', False):
        def ok(x, y):
            return dungeon.is_walkable(x, y) or (dungeon.in_bounds(x, y) and tiles[y][x] == DOOR)
        return ok

    def ok(x, y):
        if dungeon.in_bounds(x, y) and tiles[y][x] == DOOR:
            return True
        return m._can_move_to(dungeon, x, y)
    return ok


def find_path(m, dungeon, goal, blocked=frozenset(), max_nodes: int = 2500,
              max_len: int | None = None, avoid=None):
    """The tiles from the monster's next step to ``goal``, or None. Tiles in
    ``blocked`` (other creatures) are avoided. A goal the monster cannot
    stand on (the hero's tile, a wall a sound came through) is still
    reached: the path ends on it. ``max_len``: no path longer than that
    many steps (Wait Your Turn). ``avoid(x, y)``: tiles it keeps off while
    it has another way (a kobold's own snares)."""
    if avoid is not None and not isinstance(avoid, _Avoid):
        got = find_path(m, dungeon, goal, blocked, max_nodes, max_len, _Avoid(avoid))
        if got is not None:
            return got
        return find_path(m, dungeon, goal, blocked, max_nodes, max_len, None)
    start = (m.x, m.y)
    goal = (int(goal[0]), int(goal[1]))
    if start == goal:
        return []
    ok = _passable_fn(m, dungeon)
    keep_off = avoid.fn if isinstance(avoid, _Avoid) else None
    prev = {start: None}
    depth = {start: 0}
    q = deque([start])
    seen = 0
    gx, gy = goal
    found = False
    while q and not found:
        cur = q.popleft()
        seen += 1
        if seen > max_nodes:
            break
        if max_len is not None and depth[cur] >= max_len:
            continue
        cx, cy = cur
        nbrs = [(cx + ox, cy + oy) for ox in (-1, 0, 1) for oy in (-1, 0, 1) if ox or oy]
        nbrs.sort(key=lambda t: max(abs(t[0] - gx), abs(t[1] - gy)))
        for nxt in nbrs:
            if nxt in prev:
                continue
            if nxt == goal:
                prev[nxt] = cur
                found = True
                break
            if nxt in blocked or not ok(*nxt):
                continue
            if keep_off is not None and keep_off(*nxt):
                continue
            prev[nxt] = cur
            depth[nxt] = depth[cur] + 1
            q.append(nxt)
    if not found:
        return None
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def _occupied(m, all_monsters, extra_occupied, player):
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles(all_monsters or [], exclude=m))
    if extra_occupied:
        occ |= set(extra_occupied)
    if player is not None:
        occ.add((player.x, player.y))
    return occ


def step_toward(m, dungeon, goal, all_monsters, extra_occupied, player) -> bool:
    """One step along a real path toward ``goal``. True if it moved.

    Hunting the hero, it takes a way round the creatures in front only if
    that way is short (Wait Your Turn); behind one of its own side on the
    real way it waits its turn, a few turns with no new search, and steps
    up as soon as the tile in front is free."""
    from dungeon import DOOR
    if rooted(m):
        return False
    goal = (int(goal[0]), int(goal[1]))
    occ = _occupied(m, all_monsters, extra_occupied, player)
    d = m.__dict__
    hunting = QUEUE and player is not None and goal == (player.x, player.y)
    if hunting and d.get('_queue_goal') is not None and _cheb(*goal, *d['_queue_goal']) > 1:
        m._queue_wait = 0                # he has moved on: it looks for its way again
    if hunting and int(d.get('_queue_wait', 0) or 0) > 0:
        m._queue_wait = int(d['_queue_wait']) - 1
        nxt = d.get('_queue_step')
        if not nxt or tuple(nxt) in occ or _cheb(m.x, m.y, *nxt) != 1:
            return False                 # still behind its friend: no new search
        m._queue_wait = 0
        m.__dict__.pop('_queue_spent', None)
        path = [tuple(nxt)] + [tuple(t) for t in (d.get('_queue_rest') or ())]
        m._path_goal = goal
    else:
        path = d.get('_path')
        if (not path or d.get('_path_goal') != goal
                or _cheb(m.x, m.y, *path[0]) != 1 or path[0] in occ):
            near = {t for t in occ if _cheb(m.x, m.y, *t) <= 2 and t != goal}
            avoid = _avoid_fn(m, dungeon)
            if hunting:
                path = _hunting_path(m, dungeon, goal, near, occ, all_monsters, avoid)
                if path == 'queued':
                    return False
            else:
                path = find_path(m, dungeon, goal, blocked=near, avoid=avoid)
            m._path_goal = goal
    if not path:
        m._path = None
        return False
    nxt = path[0]
    if nxt in occ:
        m._path = None
        return False
    nx, ny = nxt
    if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == DOOR:
        dungeon.open_door(nx, ny)
        if not m._can_move_to(dungeon, nx, ny):
            dungeon.tiles[ny][nx] = DOOR
            m._path = None
            return False
    if not m._can_move_to(dungeon, nx, ny):
        m._path = None
        return False
    m.x, m.y = nx, ny
    m._path = path[1:]
    return True


class _Avoid:
    """find_path's keep-off rule, marked so the first search applies it."""

    def __init__(self, fn):
        self.fn = fn


def _hunting_path(m, dungeon, goal, near, occ, all_monsters, avoid):
    """Its way to the hero: round the creatures in front if the way round is
    short; else the real way if its first step is free; 'queued' when one of
    its own side stands on that step (it waits its turn); else, a pet or a
    stranger in the way, the old search round them."""
    q = queue_rules()
    budget = _cheb(m.x, m.y, *goal) + int(q.get('slack', 6))
    path = find_path(m, dungeon, goal, blocked=near, max_len=budget, avoid=avoid)
    if path:
        return path
    way = find_path(m, dungeon, goal, avoid=avoid)
    if not way:
        return None
    if way[0] not in occ:
        m.__dict__.pop('_queue_spent', None)
        return way
    # It waits its turn once (`wait` turns); if the friend is still in the
    # way after that, it goes round (a friend that never moves cannot hold
    # it for ever), and does not queue again until it has moved.
    spent = int(m.__dict__.get('_queue_spent', 0) or 0)
    if _friend_at(m, all_monsters, way[0]) and spent < 1:
        m._queue_spent = spent + 1
        m._queue_wait = int(q.get('wait', 3))
        m._queue_goal = tuple(goal)
        m._queue_step = tuple(way[0])
        m._queue_rest = [tuple(t) for t in way[1:]]
        m._queued = True
        m._path = None
        return 'queued'
    return find_path(m, dungeon, goal, blocked=near, avoid=avoid)


# ---------------------------------------------------------------------------
# The turn of a monster that hunts the hero
# ---------------------------------------------------------------------------

_LINE_SENSES = ('scent', 'tremor', 'lifesense', 'echo', 'mindsense', 'guilt')


def _fill(m, text: str) -> str:
    """The creature's name and pronouns put in (monster.fill), the first
    letter a capital."""
    from monster import fill
    t = fill(m, text or '')
    return t[:1].upper() + t[1:]


def _first_line(m, how: str, dungeon, player) -> None:
    """The first time on a floor that a kind finds the hero by a lore sense,
    mark it to be said (Game._say_sense_lines picks the version: only the
    Game knows whether he can see the creature, and what he knows of it)."""
    if how not in _LINE_SENSES:
        return
    if _cheb(m.x, m.y, player.x, player.y) > int(data().get('line_reach', 12)):
        return
    said = dungeon.__dict__.setdefault('_sense_lines_said', set())
    key = (getattr(m, 'kind', ''), how)
    if key in said:
        return
    said.add(key)
    if sense_line(how, 'unseen'):
        m._sense_how = how


def sense_line(how: str, version: str) -> str:
    """One version of a lore sense's line (2026-11-12): 'known' (he sees it
    and knows the kind: the sense is explained), 'seen' (he sees it, does not
    know it: only what it does), 'unseen' (he cannot see it: never named)."""
    return str(((data()['senses'].get(how) or {}).get('lines') or {}).get(version, '') or '')


def notice(m, player, dungeon, all_monsters, extra_occupied) -> bool:
    """The detection check for a monster that hunts the hero. True when it
    knows where he is and goes after him this turn; False when it has spent
    the turn on its own business or on looking for him."""
    how = perceive(m, player, dungeon)
    heard = m.__dict__.pop('_heard', None)
    felt = m.__dict__.pop('_felt_blow', False)
    tracking = bool(m.__dict__.get('_tracking'))
    hidden = how is None and _hidden(m, player, dungeon)
    if how is None and not hidden and heard and tracking and heard[2] == 'step':
        how = 'hearing'                # it hears him going round the corner
    if how is None and not hidden and felt and _cheb(m.x, m.y, player.x, player.y) <= 1:
        # A blow landed on it with the hero beside it: it feels where it came
        # from. An eyeless ooze or vine (blind, its tremor sense failing while
        # he stands still) lost the hero who stood hacking at it, and spent
        # half its turns beside him looking about for him.
        how = 'touch'
    if how:
        if not tracking:
            _first_line(m, how, dungeon, player)
            # One of a war-band has seen him: the band is roused.
            if getattr(m, '_band', None):
                import war_bands
                war_bands.alarm(m, all_monsters, player.x, player.y)
            else:
                # One of a pack has found him: it rouses the rest (a hound
                # bays, and the pack keeps his scent: src/packs.py).
                import packs
                if packs.pack_of(m) is not None:
                    packs.alarm(m, all_monsters, player.x, player.y, dungeon)
            # A lookout shouts (src/alarm.py, AI-1): its side is roused.
            import alarm
            alarm.shout(m, all_monsters, player, dungeon)
        m._aware = True
        m._tracking = True
        m._sensed_by = how
        m._goal = (player.x, player.y)
        m._searching = False
        m._lead_used = True
        return True
    m._tracking = False
    if rooted(m):
        # A rooted thing that has lost him has nowhere to go and look. (It
        # went after him: the Emberpup followed the hero out of his room,
        # Brandon's play-test 2026-11-22.)
        m._goal = None
        m._searching = False
        return False
    if int(m.__dict__.get('_tm_watch', 0) or 0) > 0 and not hidden:
        # It holds its post beyond a narrow way, out of the hero's sight,
        # for him to come out (the Tactical Mind: src/tactical_mind.py); it
        # does not walk in to look for him until its patience runs out. A
        # wound or a fight's noise ends the watch: it answers the shot.
        import under_fire
        hp_was = m.__dict__.get('_tm_hp')
        struck = hp_was is not None and under_fire.blow_hp(m) < int(hp_was)   # (a bleed is no blow)
        # One in cover from his bow (Into Cover) keeps it at the twang of
        # the bow: that is what it hides from.
        calm = ('step', 'shot') if m.__dict__.get('_tm_cover') else ('step',)
        if struck or (heard and heard[2] not in calm):
            m._tm_watch = 0
        else:
            m._tm_watch = int(m._tm_watch) - 1
            import tactical_mind
            tactical_mind.blind_turn(m, player, dungeon, all_monsters, extra_occupied)
            return False
    if heard and not hidden:
        m._goal = (heard[0], heard[1])
        m._searching = False
        m._lead_used = True
    elif (m.__dict__.get('_goal') is None and not m.__dict__.get('_lead_used')
          and (getattr(m, '_aware', False) or getattr(m, '_alerted', False))):
        # Made aware by the game itself (an announced foe, a summons, an
        # old save's hunter): one lead, to where the hero is now.
        m._goal = (player.x, player.y)
        m._searching = False
        m._lead_used = True
    if m.__dict__.get('_goal') is not None and not hidden:
        _search(m, player, dungeon, all_monsters, extra_occupied)
        return False
    idle(m, player, dungeon, all_monsters, extra_occupied)
    return False


def _search(m, player, dungeon, all_monsters, extra_occupied) -> None:
    """Go to the place, look about, give up."""
    s = data()['search']
    goal = m._goal
    if not m.__dict__.get('_searching'):
        if _cheb(m.x, m.y, *goal) > 1:
            if step_toward(m, dungeon, goal, all_monsters, extra_occupied, player):
                return
            stuck = int(m.__dict__.get('_stuck', 0) or 0) + 1
            m._stuck = stuck
            if stuck < 3:
                return                 # held up by another creature, for now
        m._stuck = 0
        lo, hi = s['roused_turns'] if getattr(m, '_alerted', False) else s['turns']
        m._searching = True
        m._search_left = random.randint(int(lo), int(hi))
    m._search_left = int(m.__dict__.get('_search_left', 0) or 0) - 1
    if m._search_left <= 0:
        _give_up(m)
        return
    rad = int(s.get('radius', 4))
    look = m.__dict__.get('_look')
    if not look or (m.x, m.y) == tuple(look) or random.random() < 0.25:
        gx, gy = goal
        look = (gx + random.randint(-rad, rad), gy + random.randint(-rad, rad))
        m._look = look
    if not step_toward(m, dungeon, look, all_monsters, extra_occupied, player):
        m._look = None


def _give_up(m) -> None:
    m._goal = None
    m._searching = False
    m._path = None
    m._look = None
    m._alerted = False
    if m.__dict__.get('_job') == 'sleep':
        m._job = 'guard'               # once woken, it keeps watch
        m._home = (m.x, m.y)
    m._lost_line = data()['search'].get('lost_line', '')


def idle(m, player, dungeon, all_monsters, extra_occupied) -> None:
    """What a creature does before it notices the hero."""
    pattern = getattr(m, 'ai_pattern', '')
    if pattern in ('sessile', 'ambush', 'cowardly', 'mimic') or getattr(m, 'stationary', False):
        return
    if m.has_effect('sleeping'):
        return
    # A scavenger with a corpse in reach goes to eat it, whatever its post
    # (game_combat._scavenge_prep sets the place; C3).
    feast = m.__dict__.get('_scavenge')
    if feast:
        if (m.x, m.y) != tuple(feast):
            if not step_toward(m, dungeon, feast, all_monsters, extra_occupied, player):
                m._scavenge = None
        return
    # A hunting pack goes about as one while it has no prey (src/packs.py):
    # its head keeps its own business, the rest keep beside it. (Each roamed
    # the floor alone, and a pack set down together was 8 to 10 tiles apart
    # within 50 to 200 turns: Brandon's play-test, 2026-11-22.)
    if _keep_with_pack(m, player, dungeon, all_monsters, extra_occupied):
        return
    job = m.__dict__.get('_job') or 'wander'
    if m._is_named_foe() or getattr(m, 'is_boss', False) or job in ('guard', 'sleep'):
        home = m.__dict__.get('_home')
        if home is None:
            m._home = (m.x, m.y)
            return
        if (m.x, m.y) != tuple(home):
            step_toward(m, dungeon, home, all_monsters, extra_occupied, player)
        return
    _roam(m, player, dungeon, all_monsters, extra_occupied)


def _keep_with_pack(m, player, dungeon, all_monsters, extra_occupied) -> bool:
    """One of a pack, not its head: it keeps within tactics idle_keep tiles
    of the head, and steps after it when it falls behind. True when its turn
    went on keeping with the pack."""
    import packs
    head = packs.head_of(m, all_monsters)
    if head is None or head is m:
        return False
    m._roam_to = None
    if _cheb(m.x, m.y, head.x, head.y) > int(packs.tactics().get('idle_keep', 2)):
        step_toward(m, dungeon, (head.x, head.y), all_monsters, extra_occupied, player)
    return True


def _roam(m, player, dungeon, all_monsters, extra_occupied) -> None:
    """Wander from room to room with a purpose, lingering a while in each."""
    wait = int(m.__dict__.get('_linger', 0) or 0)
    if wait > 0:
        m._linger = wait - 1
        return
    dest = m.__dict__.get('_roam_to')
    if dest is not None and (m.x, m.y) == tuple(dest):
        m._linger = random.randint(3, 10)
        m._roam_to = None
        return
    if dest is None:
        dest = _pick_roam_spot(m, dungeon)
        if dest is None:
            m._wander(dungeon, all_monsters, extra_occupied, player)
            return
        m._roam_to = dest
    if not step_toward(m, dungeon, dest, all_monsters, extra_occupied, player):
        m._roam_to = None
        m._wander(dungeon, all_monsters, extra_occupied, player)


def _pick_roam_spot(m, dungeon):
    rooms = list(getattr(dungeon, 'rooms', None) or ())
    random.shuffle(rooms)
    for room in rooms[:6]:
        try:
            tiles = [t for t in room.inner_tiles() if dungeon.is_walkable(*t)]
        except Exception:
            continue
        if not tiles:
            continue
        spot = random.choice(tiles)
        if _cheb(m.x, m.y, *spot) <= 40:
            return spot
    return None


# ---------------------------------------------------------------------------
# What each creature does before it notices the hero, set when a floor is made
# ---------------------------------------------------------------------------

_KEEP_OWN_WAYS = ('sessile', 'ambush', 'mimic', 'hit_and_run', 'dancer', 'dragon',
                  'fenrir_rage', 'abaddon', 'seek_locust', 'grid_bug', 'stalker_coward')


def _pick_job(family: str, rng) -> str:
    jobs = data()['jobs']
    w = jobs.get(family)
    if not isinstance(w, dict):
        w = jobs['default']
    roll = rng.random() * sum(w.values())
    for job, weight in w.items():
        roll -= weight
        if roll <= 0:
            return job
    return next(iter(w))


def assign_jobs(monsters, rooms, rng=None, sleep_rooms=()) -> None:
    """Give each freshly made floor's creatures their own business. The
    creatures of one room share a job, so a pack sleeps together; every
    creature in ``sleep_rooms`` (a monster den) sleeps. Its own random
    generator by default, seeded from the shared stream
    (random_streams.own_stream), so a seeded game gives the same jobs."""
    rng = rng or random_streams.own_stream()
    sleepy = {id(r) for r in sleep_rooms or ()}
    lo, hi = data()['jobs'].get('sleep_turns', [300, 700])
    by_room: dict = {}
    loose = []
    for m in monsters or ():
        if not getattr(m, 'alive', True) or not hasattr(m, 'ai_pattern'):
            continue
        for i, room in enumerate(rooms or ()):
            if room.x <= m.x < room.x + room.width and room.y <= m.y < room.y + room.height:
                by_room.setdefault(i, []).append(m)
                break
        else:
            loose.append(m)
    room_of = {}
    for i, room in enumerate(rooms or ()):
        room_of[i] = room
    for key, group in list(by_room.items()) + [(None, [m]) for m in loose]:
        job = _pick_job(getattr(group[0], 'family', '') or '', rng)
        if key is not None and id(room_of[key]) in sleepy:
            job = 'sleep'
        for m in group:
            if m.__dict__.get('_job_fixed'):
                continue                # a war-band keeps its own watch
            m._home = (m.x, m.y)
            if (getattr(m, 'ai_pattern', '') in _KEEP_OWN_WAYS or m._is_named_foe()
                    or getattr(m, 'is_boss', False)):
                m._job = 'guard'
                continue
            m._job = job
            if job == 'sleep' and not m.has_effect('sleeping'):
                # Its own rest, written straight in: a spell's sleep goes through
                # add_effect, which the dead and the mindless refuse
                # (status_immune), but a skeleton lying still is still dormant.
                m.status_effects['sleeping'] = max(int(m.status_effects.get('sleeping', 0) or 0),
                                                   rng.randint(int(lo), int(hi)))


# ---------------------------------------------------------------------------
# Scavengers (C3): the things that eat the dead
# ---------------------------------------------------------------------------

def is_scavenger(m) -> bool:
    s = data().get('scavengers') or {}
    return (getattr(m, 'kind', '') in s.get('kinds', ())
            or (getattr(m, 'family', '') or '') in s.get('families', ()))


def scavenge_target(m, corpses) -> tuple | None:
    """The nearest corpse an idle scavenger can smell, or None."""
    s = data().get('scavengers') or {}
    reach = int(s.get('reach', 8))
    best = None
    for c in corpses:
        d = _cheb(m.x, m.y, c.x, c.y)
        if d <= reach and (best is None or d < best[0]):
            best = (d, (c.x, c.y))
    return best[1] if best else None


# ---------------------------------------------------------------------------
# What Observe says
# ---------------------------------------------------------------------------

def status_line(m) -> str:
    """"He is asleep.", "It knows where you are.": its state, in its own
    pronoun (data/senses.json status_lines)."""
    lines = data()['status_lines']
    if m.has_effect('sleeping'):
        return _fill(m, lines['asleep'])
    if m.__dict__.get('_scavenge') and not m.__dict__.get('_tracking'):
        return _fill(m, lines.get('feeding', lines['unaware']))
    if getattr(m, 'ai_pattern', '') == 'stalker_coward' and m.__dict__.get('_tracking'):
        # The false friend, then the stalker he is (Old Nickel).
        key = 'stalking' if m.__dict__.get('_revealed') else 'stalking_friend'
        return _fill(m, lines.get(key, lines['hunting']))
    if m.__dict__.get('_tracking'):
        return _fill(m, lines['hunting'])
    if m.__dict__.get('_goal') is not None:
        return _fill(m, lines['searching'])
    return _fill(m, lines['unaware'])


def senses_line(m) -> str:
    names = sense_names(m)
    if not names:
        return ''
    joined = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    return _fill(m, data()['status_lines']['senses'].replace('{senses}', joined))
