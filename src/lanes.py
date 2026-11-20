"""Archers Find a Lane (AI-2, fix_ranged_lanes, 2026-11-20).

What was wrong (B/GAPS.md B18): a shot blocked by a friend made a ranged
creature walk at the hero (Monster._ranged_turn fell through to the standard
move), so archers walked into melee behind their own front line; beside the
hero an archer stepped back only half the time; and every missile reached
the same six tiles, a sling as far as a longbow.

Now (data/minds.json `lanes` and `ranges`):
  * A shot blocked by a friend: it steps to a lane, a free tile within a
    few steps, three or more tiles from the hero and in its reach, not
    beside him, with a clear shot; it likes about four tiles off, a wall or
    a tall fixture at its side (cover), and a tile outside the hero's sight.
    With no lane it holds a few turns for the line to clear, then comes on.
  * Beside the hero: it steps back when it has somewhere to shoot from (at
    most twice running: a hero who keeps after it gets it in melee).
  * With no shot and no lane it comes on, but stops two tiles off.
  * Each missile reaches as its weapon does: an attack's own `range`, else
    the first word of its name in the table (a longbow 8, a sling 5, a
    thrown dagger 4), else 6.
An unstrung creature has no missile (src/attack_gates.py): no lane at all.
A lane never stands on a trap or a hazard. Pets and escorts stand in the
way of a shot like anyone.

Pure module: no Game. Monster._ranged_turn calls it at four one-line hooks;
Monster.attack keeps a missile out of reach from being chosen (within_reach).
"""
from __future__ import annotations

ENABLED = True              # the scenario harness's ablation


def applies(m) -> bool:
    """The lanes are the ranged AI's (the archers, slingers and bolt-casters);
    a healer or a summoner that borrows its turn keeps beside its friends."""
    return ENABLED and getattr(m, 'ai_pattern', '') == 'ranged'


def rules() -> dict:
    import tactics
    return tactics.data().get('lanes') or {}


def _ranges() -> dict:
    import tactics
    return tactics.data().get('ranges') or {}


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def is_missile(atk) -> bool:
    """An attack that reaches from a distance: flagged `ranged`, or named
    with a ranged word (monster._RANGED_WORDS, as Monster._distance_attacks)."""
    if not isinstance(atk, dict):
        return False
    if atk.get('ranged'):
        return True
    from monster import _RANGED_WORDS
    name = str(atk.get('name', '')).lower()
    return any(w in name for w in _RANGED_WORDS)


def attack_range(atk) -> int:
    """How far this attack reaches."""
    own = (atk or {}).get('range') if isinstance(atk, dict) else None
    if own:
        try:
            return max(1, int(own))
        except (TypeError, ValueError):
            pass
    r = _ranges()
    name = str((atk or {}).get('name', '')).lower()
    for word, reach_ in r.get('words') or ():
        if word in name:
            return int(reach_)
    return int(r.get('default', 6))


def usable(m) -> list:
    """Its distance attacks it may use now: not shut by a gate (silenced,
    unstrung) and not a breath still being drawn."""
    atks = [a for a in (getattr(m, 'attacks', None) or ()) if is_missile(a)]
    if not atks:
        return []
    try:
        import attack_gates
        atks = [a for a in atks if not attack_gates.blocks_attack(m, a)]
    except ImportError:
        pass
    try:
        import breath
        atks = [a for a in atks if breath.ready(m, a)]
    except ImportError:
        pass
    return atks


def reach(m) -> int:
    """How far its farthest usable missile reaches (the old six when it has
    none, so the ranged AI's tests stay as they were)."""
    got = [attack_range(a) for a in usable(m)]
    if got:
        return max(got)
    return int(_ranges().get('default', 6))


def within_reach(m, player, atks: list) -> list:
    """Of ``atks``, those that reach the hero from where it stands; all of
    them if none does (Monster.attack's choice from range)."""
    if not ENABLED or not atks or player is None:
        return atks
    dist = _cheb(m.x, m.y, player.x, player.y)
    near = [a for a in atks if attack_range(a) >= dist]
    return near or atks


def clear_shot(x0, y0, x1, y1, dungeon, blocked) -> bool:
    """A missile from (x0, y0) reaches (x1, y1): no wall (combat's line of
    sight) and no body in ``blocked`` on the tiles between."""
    from combat import _line_of_sight
    if not _line_of_sight(x0, y0, x1, y1, dungeon):
        return False
    import tactical_mind
    return not any(t in blocked for t in tactical_mind.line_tiles(x0, y0, x1, y1))


def _blockers(m, all_monsters, extra_occupied, player) -> set:
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles([o for o in all_monsters or () if getattr(o, 'alive', False)],
                                 exclude=m))
    occ |= set(extra_occupied or ())
    occ.discard((player.x, player.y))
    return occ


def _cover(dungeon, x, y) -> bool:
    opaque = getattr(dungeon, 'is_opaque', None)
    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tx, ty = x + ox, y + oy
        if opaque is not None:
            if dungeon.in_bounds(tx, ty) and opaque(tx, ty):
                return True
        elif not dungeon.is_walkable(tx, ty):
            return True
    return False


def find_lane(m, player, dungeon, all_monsters, extra_occupied):
    """(tile, path) of the best lane within `steps` steps, or None. Kept
    `keep` turns while the hero stands where he was."""
    import packs
    import tactical_mind
    r = rules()
    hero = (player.x, player.y)
    d = m.__dict__
    cached = d.get('_lane')
    if (isinstance(cached, dict) and cached.get('at') == hero and cached.get('from') == (m.x, m.y)
            and int(cached.get('age', 0)) < int(r.get('keep', 2))):
        m._lane = dict(cached, age=int(cached.get('age', 0)) + 1)
        got = cached.get('lane')
        return (tuple(got[0]), [tuple(p) for p in got[1]]) if got else None
    R = reach(m)
    lo = int(r.get('min_range', 3))
    steps = int(r.get('steps', 3))
    ideal = int(r.get('ideal', 4))
    blocked = _blockers(m, all_monsters, extra_occupied, player)
    try:
        hs = int(player.get_sight_radius())
    except Exception:
        hs = 99
    ok = packs._ok_fn(dungeon)
    goals = []
    for y in range(m.y - steps, m.y + steps + 1):
        for x in range(m.x - steps, m.x + steps + 1):
            if (x, y) in blocked or (x, y) == hero or not ok(x, y):
                continue
            dd = _cheb(x, y, *hero)
            if dd < lo or dd > R:
                continue
            if tactical_mind.hazard_here(dungeon, x, y):
                continue
            if not clear_shot(x, y, hero[0], hero[1], dungeon, blocked - {(x, y), (m.x, m.y)}):
                continue
            goals.append((x, y))
    best = None
    if goals:
        paths = packs.bfs((m.x, m.y), ok, blocked | {hero}, goals, steps, 150)
        scored = []
        for t, path in paths.items():
            dd = _cheb(t[0], t[1], *hero)
            s = -abs(dd - ideal) + (1 if _cover(dungeon, *t) else 0) + (1 if dd > hs else 0) \
                - 0.3 * len(path)
            scored.append((-s, t, path))
        if scored:
            scored.sort()
            best = (scored[0][1], list(scored[0][2]))
    m._lane = {'at': hero, 'from': (m.x, m.y), 'age': 0,
               'lane': [best[0], best[1]] if best else None}
    return best


def blocked_turn(m, player, dungeon, all_monsters, extra_occupied):
    """Its shot is blocked by a body: to a lane (False: it moved), or hold a
    few turns for the line to clear (False), else None (it comes on)."""
    if not applies(m):
        return None
    d = m.__dict__
    got = find_lane(m, player, dungeon, all_monsters, extra_occupied)
    if got:
        tile, path = got
        import packs
        occ = packs._occupied(m, all_monsters, extra_occupied, player)
        if packs._step_along(m, list(path), occ, player, dungeon, 1):
            m._lane_hold = 0
            import tactical_mind
            tactical_mind.say(m, 'lane', dungeon)
            return False
    held = int(d.get('_lane_hold', 0) or 0)
    if held < int(rules().get('hold', 4)):
        m._lane_hold = held + 1
        return False
    m._lane_hold = 0
    return None


def back_off(m, player, dungeon, all_monsters, extra_occupied) -> bool:
    """Beside the hero: a step back to a tile two or more from him that
    still has a shot at him, when it has a missile to use, at most `backs`
    times running. True if it moved."""
    if not applies(m) or not usable(m):
        return False
    d = m.__dict__
    n = int(d.get('_lane_backs', 0) or 0)
    if n >= int(rules().get('backs', 2)):
        m._lane_backs = 0
        return False
    import tactical_mind
    blocked = _blockers(m, all_monsters, extra_occupied, player)
    hero = (player.x, player.y)
    opts = []
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if not ox and not oy:
                continue
            t = (m.x + ox, m.y + oy)
            if t in blocked or t == hero or _cheb(t[0], t[1], *hero) < 2:
                continue
            if not m._can_move_to(dungeon, *t) or tactical_mind.hazard_here(dungeon, *t):
                continue
            if not clear_shot(t[0], t[1], hero[0], hero[1], dungeon, blocked):
                continue
            opts.append(t)
    if not opts:
        m._lane_backs = 0
        return False
    t = max(sorted(opts), key=lambda p: (_cheb(p[0], p[1], *hero), _cover(dungeon, *p)))
    m.x, m.y = t
    m._lane_backs = n + 1
    return True


def shot(m) -> None:
    """It loosed a shot: its back-steps start again."""
    m.__dict__.pop('_lane_backs', None)


def hold_short(m, player, dungeon) -> bool:
    """With no shot and no lane it comes on as any creature, but no nearer
    than `stop_at` tiles: True when it should hold where it is."""
    if not applies(m) or not usable(m):
        return False
    return _cheb(m.x, m.y, player.x, player.y) <= int(rules().get('stop_at', 2))
