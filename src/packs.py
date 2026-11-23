"""Packs: kin that hunt together (Brandon 2026-11-18: "add packs that fight 2+
at a time, the more diverse and unique our monsters are, the better"; the
design he approved 2026-11-19, and "rats swarm could add damage based on how
many rats are adjacent to the player; build it").

A pack is a kin group of one lore family set down together (data/monsters.json
``pack`` and ``pack_size``; dungeon._spawn_one_in_room calls ``on_spawned``).
Which kinds are a pack, and each pack's trick, are data (data/packs.json). A
war-band (src/war_bands.py) is a different thing, a mixed group with a leader
and roles: a band's member keeps to its band and never uses pack tactics.

The hunt (every pack, ``hunt_turn``):
  * In the open they spread round the hero: each takes a free tile beside him
    on its own side rather than piling in on one (``choose_spot``); wolves and
    hounds come round to his back.
  * Where only one of them could reach him (``choke``: a corridor, the far side
    of a doorway) they do not come on single file to be killed one by one. One
    already on him fights; the rest go round to come at him from another side
    when there is a way (``round_path``), or hold beyond the mouth, out of his
    sight, for him to come out (``hold_step``). A rat pack presses on anyway:
    vermin do not think so far.
  * One that notices him rouses the rest (``alarm``; senses.notice calls it).

The tricks, each family's own (``blow_mult``, ``after_blow``, ``adjacent_turn``,
the sling and the dart in ``hunt_turn``): rats swarm (a bite is worth more for
every other rat beside the hero), wolves hamstring (a bite with a packmate
beside him can slow him), jackals dart in and out by turns, hyenas and gnolls
harry the wounded, goblins sling and then charge together, kobolds lay
snares and caltrops and back away over them, ghouls feed on a held hero,
harpies snatch food and fly off, hounds bay to call the pack and keep his
scent. Each has a tell (data/tells.json, ``tell_keys``).

Kept cheap: a short search round the hero for the pack member that is near
him (``reach_nodes`` tiles), and the longer search for a way round only at a
choke, kept for a few turns. Pure module: no pygame, no Game (the Game says
the lines a monster leaves in ``_pack_line``).
"""
from __future__ import annotations

import json
import random
from collections import deque

_DATA: dict | None = None
_KIND: dict | None = None
# The balance simulator's ablation (tools/balance/difficulty_sim.py, knob
# packs=0): with this False no kind hunts as a pack. The game never sets it.
ENABLED = True

# The words for a count in a line ("Three rats are on you at once").
_COUNT_WORDS = ('No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine')


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'packs.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def reload() -> None:
    """Forget the cached tables (tests)."""
    global _DATA, _KIND
    _DATA = None
    _KIND = None


def _kinds() -> dict:
    global _KIND
    if _KIND is None:
        table = {}
        for pid, p in data()['packs'].items():
            for k in p.get('kinds', ()):
                table[k] = pid
        _KIND = table
    return _KIND


def pack_of(kind) -> str | None:
    """The pack id of a kind (or a monster), None for one that does not hunt
    as a pack."""
    if not ENABLED:
        return None
    if not isinstance(kind, str):
        kind = getattr(kind, 'kind', '')
    return _kinds().get(str(kind or ''))


def spec(pid) -> dict:
    return data()['packs'].get(pid or '', {}) or {}


def tactics() -> dict:
    return data()['tactics']


def trick(tid) -> dict:
    return data()['tricks'].get(tid, {}) or {}


def tricks_of(m) -> list:
    if (getattr(m, 'status_effects', None) or {}).get('babbled', 0) > 0:
        return []                     # the Confusion of Tongues: it forgets its pack's ways
    return list(spec(pack_of(m)).get('tricks', ()) or ())


def has_trick(m, tid: str) -> bool:
    return tid in tricks_of(m)


def plural(m) -> str:
    return str(spec(pack_of(m)).get('plural') or 'pack')


def tell_keys(m) -> list:
    """The tell keys of its pack's tricks (data/tells.json 'pack_<trick>')."""
    return [f'pack_{t}' for t in tricks_of(m)]


def _fill(m, text: str, **kw) -> str:
    from monster import fill
    t = fill(m, text or '', pack=plural(m), **kw)
    return t[:1].upper() + t[1:]


def count_word(n: int) -> str:
    return _COUNT_WORDS[n] if 0 <= n < len(_COUNT_WORDS) else str(n)


# ---------------------------------------------------------------------------
# Who hunts with whom
# ---------------------------------------------------------------------------

def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _named(m) -> bool:
    try:
        return bool(m._is_named_foe())
    except Exception:
        return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False))


def in_pack(m) -> bool:
    """A hostile creature of a pack kind, not a war-band's member, a friend,
    an encounter's person or a named foe: it hunts as its pack does."""
    if pack_of(m) is None or not getattr(m, 'alive', False):
        return False
    if (getattr(m, 'status_effects', None) or {}).get('babbled', 0) > 0:
        return False                  # babbling, it fights alone (attack_gates.py)
    d = getattr(m, '__dict__', {})
    if d.get('_band') or getattr(m, 'is_allied', False) or d.get('_npc_encounter_tag') \
            or d.get('_flavor_encounter_tag'):
        return False
    return not _named(m)


def mates(m, all_monsters, radius: int | None = None) -> list:
    """Its living packmates (its pack's kinds, hunting as a pack) within
    ``radius`` tiles (tactics mates_radius by default)."""
    pid = pack_of(m)
    if pid is None:
        return []
    r = int(tactics().get('mates_radius', 8) if radius is None else radius)
    return [o for o in all_monsters or ()
            if o is not m and pack_of(o) == pid and in_pack(o) and _cheb(o.x, o.y, m.x, m.y) <= r]


def _beside(player, o) -> bool:
    from geom import is_adjacent
    return is_adjacent(player.x, player.y, o)


def beside_hero(m, player, all_monsters) -> list:
    """Its packmates (any distance from it) standing beside the hero, not
    counting itself."""
    pid = pack_of(m)
    if pid is None:
        return []
    return [o for o in all_monsters or ()
            if o is not m and getattr(o, 'alive', False) and pack_of(o) == pid
            and not getattr(o, 'is_allied', False) and _beside(player, o)]


# ---------------------------------------------------------------------------
# Who can act: a pack waits on no mate that cannot
# ---------------------------------------------------------------------------
_CANNOT_ACT = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'feared', 'charmed')
_CANNOT_MOVE = ('stuck_in_pit', 'impaled', 'immobilized')


def can_fight(o) -> bool:
    """Awake, its own master, not broken and at no peace."""
    import caster_ai
    import lore_powers
    st = getattr(o, 'status_effects', None) or {}
    return not (any(int(st.get(e, 0) or 0) != 0 for e in _CANNOT_ACT)
                or caster_ai.broken(o) or lore_powers.at_peace(o))


def can_come(o) -> bool:
    """It can fight and can walk to where the fight is."""
    st = getattr(o, 'status_effects', None) or {}
    return can_fight(o) and not any(int(st.get(e, 0) or 0) != 0 for e in _CANNOT_MOVE)


# ---------------------------------------------------------------------------
# Rats swarm (pure numbers first)
# ---------------------------------------------------------------------------

def swarm_bonus(others: int, per_other: float, cap: float) -> float:
    """The share a bite gains for ``others`` other rats beside the hero."""
    return min(float(cap), max(0, int(others)) * float(per_other))


def held(player) -> bool:
    """Paralysed, asleep, stuck fast or stunned: what a ghoul pack waits for."""
    return any(player.has_effect(e) for e in trick('feast').get('held', ()))


def wounded(player) -> bool:
    """Below the harrying line of his health (hyenas, gnolls)."""
    mx = max(1, int(getattr(player, 'max_hp', 1) or 1))
    return float(getattr(player, 'hp', mx)) < float(trick('harry').get('below', 0.5)) * mx


def blow_mult(m, player, atk, all_monsters) -> tuple:
    """(multiplier, note) for a blow of ``m`` that has hit: the rat swarm, the
    hyena harrying a wounded hero, the ghoul pack on a held one. (1.0, '')
    for anything else."""
    tricks = tricks_of(m)
    if not tricks:
        return 1.0, ''
    mult = 1.0
    notes = []
    import wards
    if 'swarm' in tricks and not wards.all_round(player):
        s = trick('swarm')
        # Only those that can act are at him (ruling D4, 2026-11-22): a mate
        # asleep or held lends nothing to the heap.
        on_him = [o for o in beside_hero(m, player, all_monsters) if can_fight(o)]
        n = len(on_him)
        b = swarm_bonus(n, s.get('per_other', 0.5), s.get('cap', 1.5))
        if b > 0:
            mult *= 1.0 + b
        told = int(m.__dict__.get('_swarm_told', 0) or 0)
        if n < told:
            m._swarm_told = n                 # some fell: say it again if it grows
        elif n >= int(s.get('line_at', 2)) and n > told:
            notes.append(_fill(m, s.get('line', ''), n=count_word(n + 1)))
            for o in on_him + [m]:
                o._swarm_told = n
    if 'harry' in tricks and wounded(player):
        mult *= float(trick('harry').get('mult', 1.3))
        if not m.__dict__.get('_harry_told'):
            notes.append(_fill(m, trick('harry').get('line', '')))
            for o in mates(m, all_monsters) + [m]:
                o._harry_told = True
    if 'feast' in tricks and held(player):
        mult *= float(trick('feast').get('mult', 1.25))
    return mult, ' '.join(n for n in notes if n)


def after_blow(m, player, atk, actual: int, all_monsters) -> str:
    """What follows a blow of ``m`` that landed (``actual`` > 0): a wolf's
    hamstring when a packmate stands beside the hero, a harpy's snatch. The
    words to add to the blow's line ('' for none)."""
    if actual <= 0:
        return ''
    tricks = tricks_of(m)
    # (A hero already slowed is not hamstrung again until it wears off: three
    # wolves must not keep him slowed for the whole fight.)
    import wards
    if ('hamstring' in tricks and not player.has_effect('slowed')
            and not wards.all_round(player)              # the Breastplate's guard
            and beside_hero(m, player, all_monsters)):
        h = trick('hamstring')
        # Through the one rider path (guards, counters, wards, the saving
        # throw): the boots and greaves can turn it, a DEX save halves it.
        rider = dict(atk or {}, effect=h.get('effect', 'slowed'),
                     effect_chance=float(h.get('chance', 0.3)),
                     effect_duration=int(h.get('turns', 3)))
        said = m._apply_attack_effect(rider, player)
        if said:
            return ' ' + _fill(m, h.get('line', '')) + said
    if 'snatch' in tricks:
        s = trick('snatch')
        if (str((atk or {}).get('name', '')) in (s.get('attacks') or ())
                and not m.__dict__.get('_wants_steal')
                and random.random() < float(s.get('chance', 0.35))):
            m._wants_steal = s.get('steal', 'food')
    return ''


# ---------------------------------------------------------------------------
# The ground round the hero
# ---------------------------------------------------------------------------

def ring(x: int, y: int) -> list:
    """The eight tiles round (x, y)."""
    return [(x + ox, y + oy) for oy in (-1, 0, 1) for ox in (-1, 0, 1) if ox or oy]


def _ok_fn(dungeon):
    from dungeon import DOOR

    def ok(x, y):
        if not dungeon.in_bounds(x, y):
            return False
        return dungeon.is_walkable(x, y) or dungeon.tiles[y][x] == DOOR
    return ok


def bfs(start, ok, blocked, goals, max_len: int, max_nodes: int, avoid=frozenset()) -> dict:
    """Shortest 8-way paths from ``start`` to each tile of ``goals`` it can
    reach in at most ``max_len`` steps, searching at most ``max_nodes``
    tiles: {goal: [first step, ..., goal]}. Tiles in ``blocked`` are never
    entered; tiles in ``avoid`` may be a goal but are not walked through."""
    goals = set(goals)
    out = {}
    if not goals:
        return out
    prev = {start: None}
    depth = {start: 0}
    q = deque([start])
    seen = 0
    while q and len(out) < len(goals):
        cur = q.popleft()
        seen += 1
        if seen > max_nodes:
            break
        d = depth[cur]
        if d >= max_len:
            continue
        cx, cy = cur
        for nxt in ring(cx, cy):
            if nxt in prev or nxt in blocked or not ok(*nxt):
                continue
            prev[nxt] = cur
            depth[nxt] = d + 1
            if nxt in goals:
                path = [nxt]
                p = cur
                while p != start:
                    path.append(p)
                    p = prev[p]
                out[nxt] = path[::-1]
                continue                  # a goal is the end of its path
            if nxt in avoid:
                continue
            q.append(nxt)
    return out


def slots(m, player, dungeon, all_monsters, extra_occupied=()) -> set:
    """The tiles beside the hero that the pack can get at from ``m``'s side
    with a short walk: free ones and ones a packmate already holds. At a
    choke (a corridor, the far side of a door) there is one, or none."""
    t = tactics()
    pid = pack_of(m)
    hero = (player.x, player.y)
    from geom import occupied_tiles
    others = set()
    for o in all_monsters or ():
        if o is m or not getattr(o, 'alive', False):
            continue
        if pack_of(o) == pid and in_pack(o):
            continue                          # a packmate's tile can still be a slot
        others.update(occupied_tiles(o))
    others |= set(extra_occupied or ())
    ok = _ok_fn(dungeon)
    goals = [p for p in ring(*hero) if ok(*p) and p not in others]
    d0 = _cheb(m.x, m.y, *hero)
    got = bfs((m.x, m.y), ok, others | {hero}, goals,
              max_len=d0 + int(t.get('slack', 3)), max_nodes=int(t.get('reach_nodes', 300)))
    return set(got)


def choke(slot_tiles) -> bool:
    return len(slot_tiles) <= int(tactics().get('choke_slots', 1))


def _occupied(m, all_monsters, extra_occupied, player) -> set:
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles([o for o in all_monsters or () if getattr(o, 'alive', False)],
                                 exclude=m))
    occ |= set(extra_occupied or ())
    occ.add((player.x, player.y))
    return occ


def _claims(m, player, all_monsters) -> dict:
    """{spot: packmate} for the tiles beside the hero its packmates are on
    their way to (a claim holds while the hero stays where he was)."""
    hero = (player.x, player.y)
    out = {}
    for o in mates(m, all_monsters):
        spot = o.__dict__.get('_pack_spot')
        if spot and o.__dict__.get('_pack_spot_at') == hero and not _beside(player, o):
            out[tuple(spot)] = o
    return out


def choose_spot(player, candidates: dict, pressure, circle: bool = False, back=None):
    """The tile beside the hero to come at him from: of ``candidates``
    ({tile: path there}), the one farthest round from where the pack already
    presses him (``pressure``: packmates beside him and the spots they are
    making for), the hero's back first for wolves and hounds (``circle``,
    ``back`` the tile behind him), a short walk breaking ties. None if there
    is no candidate."""
    if not candidates:
        return None
    pressure = list(pressure or ())

    def score(t):
        path = candidates[t]
        sep = min((((t[0] - p[0]) ** 2 + (t[1] - p[1]) ** 2) ** 0.5 for p in pressure), default=0.0)
        s = 2.0 * sep - 0.25 * len(path)
        if circle and back is not None:
            s += 2.0 * max(0.0, 2.0 - (((t[0] - back[0]) ** 2 + (t[1] - back[1]) ** 2) ** 0.5))
        return s
    return max(sorted(candidates), key=score)


def back_tile(player, engaged):
    """The tile behind the hero: away from the way he faces, or else away
    from the first of the pack on him."""
    fx = int(getattr(player, '_facing_dx', 0) or 0)
    fy = int(getattr(player, '_facing_dy', 0) or 0)
    if fx or fy:
        return (player.x - fx, player.y - fy)
    if engaged:
        o = engaged[0]
        dx = (o.x > player.x) - (o.x < player.x)
        dy = (o.y > player.y) - (o.y < player.y)
        return (player.x - dx, player.y - dy)
    return None


def _step_along(m, path, occ, player, dungeon, steps: int) -> str:
    """Walk up to ``steps`` tiles of ``path``. 'attack' when it came beside
    the hero with a step to spare (a fast one strikes), 'moved' when it
    walked, None when the way was blocked at once."""
    moved = False
    for i in range(steps):
        if not path:
            break
        nxt = tuple(path[0])
        if nxt in occ or _cheb(m.x, m.y, *nxt) != 1 or not m._can_move_to(dungeon, *nxt):
            from dungeon import DOOR
            if not (dungeon.in_bounds(*nxt) and dungeon.tiles[nxt[1]][nxt[0]] == DOOR):
                break
            dungeon.open_door(*nxt)
            if not m._can_move_to(dungeon, *nxt):
                dungeon.tiles[nxt[1]][nxt[0]] = DOOR
                break
        m.x, m.y = nxt
        path.pop(0)
        moved = True
        if _beside(player, m):
            return 'attack' if (i == 0 and steps > 1) else 'moved'
    return 'moved' if moved else None


def _say(m, line: str, player, unseen: str = '') -> None:
    """Leave a line for the Game to say after the monster's turn
    (game_combat): ``line`` if the hero can see it, ``unseen`` (a sound) if
    he cannot."""
    if line or unseen:
        m._pack_line = (line, unseen)


def _told(m, all_monsters, key: str) -> bool:
    """Said once a fight for the whole pack: True if a packmate (or itself)
    has said ``key`` already; otherwise marks it said for all of them."""
    group = [m] + mates(m, all_monsters)
    if any(o.__dict__.get(key) for o in group):
        return True
    for o in group:
        o.__dict__[key] = True
    return False


# ---------------------------------------------------------------------------
# The pack's turn (Monster.take_turn calls these)
# ---------------------------------------------------------------------------

def hunt_turn(m, player, dungeon, all_monsters, extra_occupied=None):
    """The turn of a pack hunter that knows where the hero is and is not
    beside him. Returns 'attack' (it strikes now: a sling stone, a jackal's
    dart, a fast one that came beside him), 'moved', 'held' (it waits), or
    None (it comes on the ordinary way)."""
    if band_slinger(m):
        return band_sling(m, player, dungeon, all_monsters)
    if not in_pack(m) or m.has_effect('confused') or m.has_effect('blinded'):
        return None
    t = tactics()
    hero = (player.x, player.y)
    d0 = _cheb(m.x, m.y, *hero)
    tricks = tricks_of(m)
    near = mates(m, all_monsters)
    # Goblins pelt him from range while the pack gathers.
    if 'sling' in tricks:
        got = _sling(m, player, dungeon, all_monsters, near, extra_occupied)
        if got is not None:
            return got
    occ = _occupied(m, all_monsters, extra_occupied, player)
    steps = 2 if m.speed >= 14 else 1
    going_round = _following_round(m, player, occ)
    if going_round:
        got = _step_along(m, going_round, occ, player, dungeon, steps)
        if got:
            return got
    if d0 > int(t.get('engage_radius', 5)) or not near:
        return None                    # far off, or alone: it comes on as any creature
    bold = ('feast' in tricks and held(player)) or ('harry' in tricks and wounded(player))
    if 'feast' in tricks and held(player):
        _call_to_feast(m, player, all_monsters)
    slot_tiles = slots(m, player, dungeon, all_monsters, extra_occupied)
    if choke(slot_tiles):
        return _at_choke(m, player, dungeon, all_monsters, occ, slot_tiles, steps, bold, near)
    m._pack_wait = 0
    if 'dart' in tricks:
        return _dart_in(m, player, dungeon, all_monsters, occ)
    return _surround(m, player, dungeon, all_monsters, occ, steps)


def _surround(m, player, dungeon, all_monsters, occ, steps):
    """In the open: take a free tile beside the hero on its own side."""
    hero = (player.x, player.y)
    ok = _ok_fn(dungeon)
    claims = _claims(m, player, all_monsters)
    rng_tiles = ring(*hero)
    free = [p for p in rng_tiles if ok(*p) and p not in occ and p not in claims]
    if not free:
        return 'held'                  # every side is taken: wait for a gap
    d0 = _cheb(m.x, m.y, *hero)
    max_len = d0 + int(tactics().get('slack', 3))
    nodes = int(tactics().get('reach_nodes', 300))
    blocked = occ
    paths = bfs((m.x, m.y), ok, blocked, free, max_len, nodes, avoid=set(rng_tiles))
    if not paths:
        paths = bfs((m.x, m.y), ok, blocked, free, max_len, nodes)
    if not paths:
        return None
    engaged = [o for o in mates(m, all_monsters) if _beside(player, o)]
    pressure = [(o.x, o.y) for o in engaged] + list(claims)
    circle = bool(spec(pack_of(m)).get('circle'))
    spot = choose_spot(player, paths, pressure, circle=circle, back=back_tile(player, engaged))
    if spot is None:
        return None
    m._pack_spot = spot
    m._pack_spot_at = hero
    if len(pressure) >= 1 and not _told(m, all_monsters, '_surround_said'):
        _say(m, _fill(m, tactics().get('surround_line', '')), player)
    return _step_along(m, list(paths[spot]), occ, player, dungeon, steps) or None


def _at_choke(m, player, dungeon, all_monsters, occ, slot_tiles, steps, bold, near):
    """Where only one of them could reach him: go round, or hold beyond the
    mouth out of his sight; a rat pack (corridor 'press') or a bold one comes
    on; and after ``patience`` turns with no one fighting him, one of those
    that can come tries its luck."""
    t = tactics()
    hero = (player.x, player.y)
    mode = spec(pack_of(m)).get('corridor', 'hold')
    # A way round to another side of him.
    path = round_path(m, player, dungeon, occ, slot_tiles)
    if path:
        m._pack_wait = 0
        if not m.__dict__.get('_round_said'):
            m._round_said = True
            _say(m, _fill(m, t.get('round_line', '')), player)
        got = _step_along(m, path, occ, player, dungeon, steps)
        if got:
            return got
    if mode == 'press' or bold:
        return None
    # Only one that can act is fighting him (a wolf asleep at his feet is not).
    engaged = [o for o in near if _beside(player, o) and can_fight(o)]
    # Hurt while it waited (an arrow, a thrown flask): it comes for him.
    import under_fire
    hp_was = m.__dict__.get('_pack_hp')
    m._pack_hp = under_fire.blow_hp(m)      # (a bleed ticking is no blow)
    if hp_was is not None and m._pack_hp < hp_was:
        m._pack_wait = 0
        return None
    wait = int(m.__dict__.get('_pack_wait', 0) or 0) + 1
    m._pack_wait = wait
    if wait > int(t.get('patience', 12)) and not engaged:
        # The nearest of them loses patience and tries his luck.
        able = [o for o in near if can_come(o) and not _beside(player, o)]
        nearest = min([m] + able, key=lambda o: (_cheb(o.x, o.y, *hero), id(o)))
        if nearest is m:
            for o in [m] + list(near):
                o._pack_wait = 0
            _say(m, _fill(m, t.get('press_line', '')), player)
            return None
    if not _told(m, all_monsters, '_hold_said'):
        _say(m, _fill(m, t.get('hold_line', '')), player)
    # A slinger holds where it can pelt him; the rest out of his sight.
    view = int(trick('sling').get('range', 5)) if 'sling' in tricks_of(m) and _ranged_attacks(m) else 0
    hold_step(m, player, dungeon, occ, slot_tiles, view=view)
    return 'held'


def hold_step(m, player, dungeon, occ, slot_tiles, view: int = 0) -> bool:
    """Hold at the mouth: to a tile beside it out of the hero's sight and out
    of his reach, nearest the mouth; if there is none, back off a step when
    he is close, else stand. A slinger (``view``, its range) holds where it
    can see him within its range instead. True if it moved."""
    import senses
    hero = (player.x, player.y)
    ok = _ok_fn(dungeon)
    mouth = min(slot_tiles, key=lambda s: _cheb(s[0], s[1], m.x, m.y)) if slot_tiles else hero
    here = (m.x, m.y)
    opts = [here] + [p for p in ring(*here) if ok(*p) and p not in occ]
    opts = [p for p in opts if _cheb(p[0], p[1], *hero) >= 2]
    if view:
        shot = [p for p in opts if _cheb(p[0], p[1], *hero) <= view
                and senses.clear_view(p[0], p[1], hero[0], hero[1], dungeon)]
        if shot:
            opts = shot
            covered = []
        else:
            covered = [p for p in opts if not senses.clear_view(p[0], p[1], hero[0], hero[1], dungeon)]
    else:
        covered = [p for p in opts if not senses.clear_view(p[0], p[1], hero[0], hero[1], dungeon)]
    if view and opts and not covered:
        best = min(opts, key=lambda p: (p != here, _cheb(p[0], p[1], *mouth), p))
    elif covered:
        best = min(covered, key=lambda p: (_cheb(p[0], p[1], *mouth), p != here, p))
    elif _cheb(m.x, m.y, *hero) <= 2 and opts:
        best = max(opts, key=lambda p: (_cheb(p[0], p[1], *hero), p == here))
    else:
        return False
    if best == here or not m._can_move_to(dungeon, *best):
        return False
    m.x, m.y = best
    return True


def round_path(m, player, dungeon, occ, slot_tiles):
    """A way round to a free tile beside the hero on another side than the
    mouth, or None. The search is kept for ``round_every`` turns while the
    hero stands where he was."""
    t = tactics()
    hero = (player.x, player.y)
    rp = m.__dict__.get('_pack_round')
    if rp and rp.get('at') == hero and int(rp.get('age', 0)) < int(t.get('round_every', 6)):
        rp['age'] = int(rp.get('age', 0)) + 1
        path = rp.get('path')
        if path and _cheb(m.x, m.y, *path[0]) == 1 and tuple(path[0]) not in occ:
            return path
        if not path:
            return None
    ok = _ok_fn(dungeon)
    goals = [p for p in ring(*hero) if ok(*p) and p not in occ and p not in slot_tiles]
    found = bfs((m.x, m.y), ok, occ | set(slot_tiles), goals,
                max_len=int(t.get('round_max', 30)), max_nodes=int(t.get('round_nodes', 1200)),
                avoid=set(ring(*hero)))
    path = [tuple(p) for p in min(found.values(), key=len)] if found else None
    m._pack_round = {'at': hero, 'age': 0, 'path': path}
    return path


def _following_round(m, player, occ):
    """The way round it is already walking, if it still leads to the hero
    (he has not gone more than a couple of tiles from where it was found)."""
    rp = m.__dict__.get('_pack_round')
    if not rp or not rp.get('path') or not rp.get('at'):
        return None
    at = tuple(rp['at'])
    if _cheb(at[0], at[1], player.x, player.y) > 2:
        return None
    path = rp['path']
    if _cheb(m.x, m.y, *path[0]) != 1 or tuple(path[0]) in occ:
        return None
    return path


def _call_to_feast(m, player, all_monsters) -> None:
    """The hero is held: every ghoul of the pack within call_radius comes."""
    import senses
    f = trick('feast')
    if m.__dict__.get('_feast_called') == (player.x, player.y):
        return
    for o in mates(m, all_monsters, int(f.get('call_radius', 10))):
        if not o.__dict__.get('_tracking'):
            senses.rouse(o, player.x, player.y)
        o._feast_called = (player.x, player.y)
    m._feast_called = (player.x, player.y)
    if not _told(m, all_monsters, '_feast_said'):
        _say(m, _fill(m, f.get('line', '')), player)


# --- Goblins: sling, then charge ------------------------------------------

def _ranged_attacks(m) -> list:
    import attack_gates                 # an unstrung slinger has no sling (attack_gates.py)
    return [a for a in getattr(m, 'attacks', ()) or ()
            if a.get('ranged') and not attack_gates.blocks_attack(m, a)]


def _melee_attacks(m) -> list:
    return [a for a in getattr(m, 'attacks', ()) or () if not a.get('ranged')]


def _sling(m, player, dungeon, all_monsters, near, extra_occupied=None):
    """A goblin at range with the hero in sight: a stone ('attack') while the
    pack gathers; once charge_at of them (or all that live) are up within
    gather_radius and each still gathering has thrown at least once, they all
    rush him (None: it closes). One already on him counts toward the number
    and owes no stone, as does one that cannot come or has nothing to throw.
    Into a choke they never rush: they keep pelting him from the mouth."""
    s = trick('sling')
    shots = _ranged_attacks(m)
    if not shots:
        return None
    hero = (player.x, player.y)
    d0 = _cheb(m.x, m.y, *hero)
    if d0 < 2 or d0 > int(s.get('range', 5)):
        return None
    # A clear shot: no wall, and no packmate in the way of the stone.
    if not m._has_clear_shot(player.x, player.y, dungeon,
                             [o for o in all_monsters or () if getattr(o, 'alive', False)]):
        return None
    if m.__dict__.get('_charged'):
        if not choke(slots(m, player, dungeon, all_monsters, extra_occupied)):
            return None
    else:
        radius = int(s.get('gather_radius', 5))
        gathered = [o for o in [m] + list(near) if _cheb(o.x, o.y, *hero) <= radius]
        need = min(int(s.get('charge_at', 3)), 1 + len(near))
        if (need >= 2 and len(gathered) >= need
                and all(int(o.__dict__.get('_stones', 0) or 0) >= 1 for o in gathered
                        if o is not m and not _beside(player, o) and can_come(o)
                        and _ranged_attacks(o))
                and int(m.__dict__.get('_stones', 0) or 0) >= 1
                and not choke(slots(m, player, dungeon, all_monsters, extra_occupied))):
            for o in [m] + list(near):
                o._charged = True
            if not _told(m, all_monsters, '_charge_said'):
                _say(m, _fill(m, s.get('line', '')), player)
            return None
    m._stones = int(m.__dict__.get('_stones', 0) or 0) + 1
    m._pack_blow = random.choice(shots)
    return 'attack'


def band_slinger(m) -> bool:
    """A war-band's member whose kind's pack slings (a goblin of the scouts
    or the raiders): its own master, hostile, with its wits about it."""
    d = getattr(m, '__dict__', {})
    if not d.get('_band') or 'sling' not in tricks_of(m) or not getattr(m, 'alive', False):
        return False
    if getattr(m, 'is_allied', False) or m.has_effect('confused') or m.has_effect('blinded'):
        return False
    return not _named(m)


def band_sling(m, player, dungeon, all_monsters):
    """A band's slinger with the hero two to its sling's range off and a
    clear throw past its friends pelts him ('attack') rather than walk into
    his blows, `stones` stones at most (as long as it likes at a narrow
    way), unless its leader has called the charge or the fall-back (None:
    it comes on, or keeps its band's order). The line is said once a
    fight for the band (data/packs.json band_sling)."""
    shots = _ranged_attacks(m)
    if not shots:
        return None
    hero = (player.x, player.y)
    d0 = _cheb(m.x, m.y, *hero)
    if d0 < 2 or d0 > int(trick('sling').get('range', 5)):
        return None
    band = getattr(dungeon, 'band', None)
    if isinstance(band, dict) and band.get('uid') == m.__dict__.get('_band') and \
            band.get('order') in ('charge', 'fall_back'):
        return None
    if not m._has_clear_shot(player.x, player.y, dungeon,
                             [o for o in all_monsters or () if getattr(o, 'alive', False)]):
        return None
    # Its stones thrown, it drops the sling and comes on; at a narrow way,
    # where its band will not follow him, it pelts him as long as it likes.
    cap = int((data().get('band_sling') or {}).get('stones', 3))
    if int(m.__dict__.get('_stones', 0) or 0) >= cap and not choke(
            slots(m, player, dungeon, all_monsters)):
        return None
    m._stones = int(m.__dict__.get('_stones', 0) or 0) + 1
    m._pack_blow = random.choice(shots)
    uid = m.__dict__.get('_band')
    band_mates = [o for o in all_monsters or () if getattr(o, '__dict__', {}).get('_band') == uid]
    if not any(o.__dict__.get('_band_sling_said') for o in band_mates):
        for o in band_mates:
            o._band_sling_said = True
        bs = data().get('band_sling') or {}
        _say(m, _fill(m, bs.get('line', '')), player, bs.get('unseen', ''))
    return 'attack'


# --- Jackals: in and out by turns -----------------------------------------

def _dart_in(m, player, dungeon, all_monsters, occ):
    """A jackal that can reach the hero this turn comes in and snaps at once,
    if fewer than max_in of the pack are on him; otherwise it waits."""
    d = trick('dart')
    hero = (player.x, player.y)
    on_him = [o for o in beside_hero(m, player, all_monsters) if can_fight(o)]
    if len(on_him) >= int(d.get('max_in', 2)):
        return 'held'
    # Each keeps its own beat (one in, the next out): the first time it can
    # dart in, it may wait a turn, so a pack does not dart all at once.
    phase = m.__dict__.get('_dart_phase')
    if phase is None:
        m._dart_phase = phase = random.randint(0, 1)
    if phase:
        m._dart_phase = 0
        return 'held'
    ok = _ok_fn(dungeon)
    free = [p for p in ring(*hero) if ok(*p) and p not in occ]
    paths = bfs((m.x, m.y), ok, occ, free, max_len=1, max_nodes=16)
    if not paths:
        return None                    # too far to dart in: it comes on
    pressure = [(o.x, o.y) for o in on_him]
    spot = choose_spot(player, paths, pressure)
    got = _step_along(m, list(paths[spot]), occ, player, dungeon, 1)
    if got and _beside(player, m):
        m._darted = True
        if not _told(m, all_monsters, '_dart_said'):
            _say(m, _fill(m, d.get('line', '')), player)
        return 'attack'
    return got


# ---------------------------------------------------------------------------
# Beside the hero
# ---------------------------------------------------------------------------

def adjacent_turn(m, player, dungeon, all_monsters, extra_occupied=None):
    """A pack hunter beside the hero, about to strike: 'moved' when its trick
    takes it away instead (a jackal darting out, a kobold backing off over a
    trap it lays), else None (it strikes; a goblin with its knife)."""
    tricks = tricks_of(m)
    if not tricks:
        return None
    if 'sling' in tricks:
        melee = _melee_attacks(m)
        if melee and _ranged_attacks(m):
            m._pack_blow = random.choice(melee)
    if not in_pack(m) or m.has_effect('confused') or m.has_effect('blinded'):
        return None
    occ = _occupied(m, all_monsters, extra_occupied, player)
    if 'dart' in tricks:
        if m.__dict__.get('_darted') and mates(m, all_monsters, 3):
            if _back_off(m, player, dungeon, occ):
                m._darted = False
                return 'moved'
        m._darted = True
        return None
    if 'traps' in tricks:
        tr = trick('traps')
        left = m.__dict__.get('_traps_left')
        if left is None:
            left = int(tr.get('each', 2))
        hurt = m.hp < m.max_hp * 0.5
        if left > 0 and (hurt or random.random() < float(tr.get('withdraw_chance', 0.5))):
            here = (m.x, m.y)
            step = _back_off_tile(m, player, dungeon, occ)
            if step is not None and lay_trap(dungeon, here, random) is not None:
                m.x, m.y = step
                m._traps_left = left - 1
                m._laid_at = here               # the Game shows it if he saw it laid
                _say(m, _fill(m, tr.get('line', '')), player)
                return 'moved'
    return None


def _back_off_tile(m, player, dungeon, occ):
    """The tile one step away from the hero, out of his reach, or None."""
    hero = (player.x, player.y)
    ok = _ok_fn(dungeon)
    opts = [p for p in ring(m.x, m.y) if ok(*p) and p not in occ
            and _cheb(p[0], p[1], *hero) >= 2 and m._can_move_to(dungeon, *p)]
    if not opts:
        return None
    return max(opts, key=lambda p: (_cheb(p[0], p[1], *hero),
                                    abs(p[0] - hero[0]) + abs(p[1] - hero[1]), p))


def _back_off(m, player, dungeon, occ) -> bool:
    """One step away from the hero, out of his reach; True if it moved."""
    step = _back_off_tile(m, player, dungeon, occ)
    if step is None:
        return False
    m.x, m.y = step
    return True


# ---------------------------------------------------------------------------
# Kobold traps
# ---------------------------------------------------------------------------

def trap_spec(name: str) -> dict:
    return dict((trick('traps').get('kinds') or {}).get(name) or {})


def lay_trap(dungeon, tile, rng=random, kind: str | None = None):
    """A kobold's snare or caltrops on ``tile`` (hidden), or None when the
    tile cannot hold one (not bare floor, a trap there already)."""
    from dungeon import FLOOR
    x, y = tile
    traps = getattr(dungeon, 'traps', None)
    if traps is None or not dungeon.in_bounds(x, y) or dungeon.tiles[y][x] != FLOOR:
        return None
    if tile in traps:
        return None
    kinds = sorted((trick('traps').get('kinds') or {}).keys())
    if not kinds:
        return None
    name = kind or rng.choice(kinds)
    t = trap_spec(name)
    t['color'] = tuple(t.get('color') or (160, 160, 160))
    t['revealed'] = False
    t['_laid_by_pack'] = True
    traps[tile] = t
    return t


def den_traps(dungeon, members, rng) -> list:
    """Snares and caltrops among the tiles round where a kobold pack is set
    down: the den's own defences, hidden. Returns the tiles."""
    tr = trick('traps')
    if not members:
        return []
    lo, hi = (tr.get('den') or [1, 2])[:2]
    n = rng.randint(int(lo), int(hi))
    r = int(tr.get('den_radius', 3))
    cx, cy = members[0].x, members[0].y
    taken = {(o.x, o.y) for o in members}
    from dungeon import STAIRS_UP, STAIRS_DOWN
    tiles = []
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x, y) in taken or not dungeon.in_bounds(x, y):
                continue
            near_stair = any(dungeon.in_bounds(x + ox, y + oy)
                             and dungeon.tiles[y + oy][x + ox] in (STAIRS_UP, STAIRS_DOWN)
                             for ox in (-1, 0, 1) for oy in (-1, 0, 1))
            if not near_stair:
                tiles.append((x, y))
    rng.shuffle(tiles)
    laid = []
    for tile in tiles:
        if len(laid) >= n:
            break
        if lay_trap(dungeon, tile, rng) is not None:
            laid.append(tile)
    return laid


# ---------------------------------------------------------------------------
# Set down together; roused together
# ---------------------------------------------------------------------------

def on_spawned(members, dungeon, rng, pool=None, monsters=None) -> list:
    """A pack has just been set down (dungeon._spawn_one_in_room): mark it
    one pack, let a leader take one place (a wolf pack led by its parent,
    when the floor's pool holds him), and lay a kobold den's traps. Returns
    the members (with the leader in place)."""
    members = [o for o in members if hasattr(o, 'kind')]
    if not members:
        return members
    pid = pack_of(members[0])
    if pid is None:
        return members
    uid = f'{pid}@{members[0].x},{members[0].y}'
    p = spec(pid)
    lead = (p.get('leader') or {}).get(members[0].kind)
    if lead and len(members) >= 2 and pool is not None and lead.get('kind') in pool \
            and rng.random() < float(lead.get('chance', 0.0)):
        from monster import Monster
        old = members[-1]
        new = Monster({**pool[lead['kind']], 'id': lead['kind']}, old.x, old.y)
        if monsters is not None:
            for i, o in enumerate(monsters):
                if o is old:
                    monsters[i] = new
                    break
        members[-1] = new
    for o in members:
        o._pack = uid
    # A den's traps are laid as the floor is first peopled (level_manager
    # sets _dens_open), not by a pack that wanders in later.
    if ('traps' in (p.get('tricks') or ()) and getattr(dungeon, 'traps', None) is not None
            and getattr(dungeon, '__dict__', {}).get('_dens_open')):
        den_traps(dungeon, members, rng)
    return members


def head_of(m, monsters):
    """The one an idle pack follows (senses.idle): the pack's leader kind
    when one is with it (the wolves' parent), else the first of it still
    alive. None for a creature in no pack, or one not hunting as its pack
    does (in_pack: a band's man, a friend, babbled). The rest keep within
    tactics idle_keep of it, so a pack set down together goes about together
    (Brandon's play-test, 2026-11-22: the dire rats were all over the floor,
    never two together)."""
    uid = getattr(m, '__dict__', {}).get('_pack')
    if not uid or not in_pack(m):
        return None
    mates = [o for o in monsters or () if getattr(o, 'alive', False)
             and getattr(o, '__dict__', {}).get('_pack') == uid]
    if not mates:
        return None
    leads = {v.get('kind') for v in (spec(pack_of(m)).get('leader') or {}).values()
             if isinstance(v, dict)}
    return next((o for o in mates if getattr(o, 'kind', '') in leads), mates[0])


def alarm(m, all_monsters, x: int, y: int, dungeon=None) -> int:
    """``m`` has just found the hero at (x, y): its pack is roused to him, as
    far as its cry carries (rouse_radius; a hound's bay, much farther). A
    hound's pack keeps his scent a while. Silenced, it has no voice to cry
    with. Returns how many were roused."""
    if not in_pack(m) or int((getattr(m, 'status_effects', None) or {}).get('silenced', 0) or 0):
        return 0
    import senses
    tricks = tricks_of(m)
    baying = 'bay' in tricks
    radius = int(trick('bay').get('radius', 14) if baying else tactics().get('rouse_radius', 8))
    reach = senses.sound_map(dungeon, m.x, m.y, radius) if dungeon is not None else None
    n = 0
    for o in mates(m, all_monsters, radius):
        if o.__dict__.get('_tracking'):
            continue
        if reach is not None and (o.x, o.y) not in reach:
            continue
        senses.rouse(o, x, y)
        n += 1
        if baying:
            o._scent_left = int(trick('bay').get('scent_turns', 20))
    if baying and not m.__dict__.get('_bayed'):
        m._bayed = True
        m._scent_left = int(trick('bay').get('scent_turns', 20))
        for o in mates(m, all_monsters, radius):
            o._bayed = True
        b = trick('bay')
        _say(m, _fill(m, b.get('line', '')), None, b.get('line_unseen', ''))
    return n


def keep_scent(m, player) -> None:
    """A hound of a pack that bayed keeps the hero's scent: it knows where
    he went for scent_turns turns."""
    left = int(m.__dict__.get('_scent_left', 0) or 0)
    if left <= 0:
        return
    m._scent_left = left - 1
    m._goal = (player.x, player.y)
    m._aware = True
    m._searching = False
