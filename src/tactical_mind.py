"""The Tactical Mind in the game (AI-2, MONSTERS AND MAGIC, 2026-11-20).

src/tactics.py weighs the options (pure); this module builds what the
creature knows (``snapshot``: a tactics.View), asks it, and carries the
choice out with moves the game already has (packs.hold_step, round_path,
choose_spot and bfs; senses.step_toward; the archers' lanes, src/lanes.py).
Monster.take_turn calls ``turn`` at one line in the aggressive path and one
in the ranged path; ``None`` means "today's code", so a plain attack, and
every case the mind does not plan, runs as it always did.

Who thinks (``thinks``): a kind with a mind (data/minds.json, or its own
``mind`` in monsters.json), hunting the hero now (it senses him: no
omniscience), within think_radius of him, one tile big, of no pack that
hunts as one (packs.hunt_turn is its brain), and not:
  * a named foe, an ally, an encounter's person, the unicorn, Death or the
    stalker (kind_data.named / outside_rules), a legend or a mini-boss;
  * asleep, held, frightened, charmed, confused, blinded or babbling;
  * broken by its morale (running, at bay, cowed, yielded: src/morale.py);
  * a thief running with its haul.
What it knows of the hero is what it senses: his wounds and his light only
by sight, its friends only those it can see or of its own band (they shout).

Pets, escorts and called allies are obstacles. Only the focus option looks
at a pet, and never at an escort, the unicorn, a ridden Bococho or Dad.

A band's leader gives orders (``band_order``, The Captain's Orders) kept on
dungeon.band; what the hero was seen to do on this floor is on
its witnesses (src/habits.py). Every option but a plain attack says one
line the first time a fight uses it (``say``, through src/ai_lines.py: the
Game says the seen line or the unseen one). State is in the creature's own
__dict__ and written as new values, so the simulator's copies and an old
save need nothing (every read has a default).
"""
from __future__ import annotations

import random

import ai_lines
import kind_data
import tactics

ENABLED = True              # the scenario harness's ablation (tools/balance/tactics_scenarios.py)
OFF: set = set()            # options switched off (the same harness)
NEW_FIGHT = 20              # turns out of touch with the hero: its next sight of him is a new fight


class Turn:
    """What the Game knows about this turn (``begin_turn``). Tests and tools
    that call take_turn directly get the defaults."""

    def __init__(self):
        self.n = 0
        self.pets = ()
        self.focus = {}
        self.seers = {}


TURN = Turn()


def begin_turn(game) -> None:
    """Before the monsters move (CombatMixin._do_monster_turns): the turn,
    and the pets the focus option may look at."""
    TURN.n = int(getattr(game, 'turn_count', 0) or 0)
    TURN.pets = tuple(p for p in (getattr(game, 'pets', None) or ()) if focusable(p))
    TURN.focus = {}
    TURN.seers = {}


def focusable(p) -> bool:
    """A pet the focus option may go for: never the unicorn, the Bococho
    under her rider, Dad, or an escort."""
    if p is None or not getattr(p, 'alive', False):
        return False
    if (getattr(p, 'is_unicorn', False) or getattr(p, '_is_unicorn', False)
            or getattr(p, 'ridden', False) or getattr(p, 'is_dad', False)
            or getattr(p, '_is_escort', False) or getattr(p, 'is_escort', False)):
        return False
    return int(getattr(p, 'max_hp', 0) or 0) > 0


# ---------------------------------------------------------------------------
# Who has a mind
# ---------------------------------------------------------------------------

def _entry(kind) -> dict:
    e = (tactics.data().get('kinds') or {}).get(str(kind or ''))
    if isinstance(e, str):
        return {'mind': e}
    return e if isinstance(e, dict) else {}


def mind_of(m) -> str | None:
    """Its mind: its kind's own ``mind`` field, else data/minds.json, else
    None (beasts, vermin, the mindless and everything not listed)."""
    own = kind_data.field(m, 'mind', None)
    if isinstance(own, str):
        return own if own in tactics.MINDS else None
    mind = _entry(getattr(m, 'kind', '')).get('mind')
    return mind if mind in tactics.MINDS else None


def flag(m, name: str) -> bool:
    """A per-kind flag (dark_edge, knows_traps): its own data, else minds.json."""
    own = kind_data.field(m, name, None)
    if own is not None:
        return bool(own)
    return bool(_entry(getattr(m, 'kind', '')).get(name, False))


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _has(m, eff: str) -> bool:
    try:
        return int((getattr(m, 'status_effects', None) or {}).get(eff, 0) or 0) > 0
    except (TypeError, ValueError, AttributeError):
        return False


# What keeps a creature from planning anything: it is held, out of its
# wits, or babbling (the Confusion of Tongues: no pack or band ways).
CANNOT = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'feared', 'charmed',
          'confused', 'blinded', 'babbled', 'immobilized', 'impaled', 'stuck_in_pit')


def busy(m) -> bool:
    """It holds the hero fast (AI-3's Held Fast, src/holds.py: a coil, a
    swallow, a drag under): its turn is the hold's, so it plans nothing,
    takes no lane step, gives no order and heeds none."""
    return bool(getattr(m, '__dict__', {}).get('_holding'))


def broken(m) -> bool:
    """Its morale has it (src/morale.py): running, at bay, cowed, yielded,
    bolting or making for its friends."""
    d = getattr(m, '__dict__', {})
    return bool(int(getattr(m, '_flee_timer', 0) or 0) > 0 or int(d.get('_at_bay', 0) or 0) > 0
                or d.get('_yielded') or d.get('_cowed') or d.get('_bolting')
                or d.get('_rally_to') is not None)


def excluded(m) -> bool:
    """Never thinks here, whatever its kind: a named foe, a legend, an ally,
    an encounter's person, the unicorn, Death, the stalker, a pet."""
    if kind_data.named(m) or kind_data.outside_rules(m):
        return True
    try:
        if m._is_named_foe():
            return True
    except Exception:
        pass
    d = getattr(m, '__dict__', {})
    return bool('legendary' in (getattr(m, 'tags', None) or ())
                or d.get('_is_abandoned_emberpup') or d.get('_is_pet') or d.get('is_pet')
                or d.get('_called_ally') or d.get('_is_escort'))


def thinks(m, player) -> bool:
    """The gate: does this creature weigh its turn now?"""
    if not ENABLED or m is None or not getattr(m, 'alive', False):
        return False
    if mind_of(m) is None or excluded(m):
        return False
    if tuple(getattr(m, 'footprint', (1, 1)) or (1, 1)) != (1, 1):
        return False
    d = m.__dict__
    if not d.get('_tracking') or not getattr(m, '_aware', False):
        return False
    if player is None or _cheb(m.x, m.y, player.x, player.y) > int(tactics.data().get('think_radius', 12)):
        return False
    if any(_has(m, e) for e in CANNOT):
        return False
    if broken(m) or busy(m) or d.get('stolen_gold') or d.get('stolen_items'):
        return False
    try:
        import packs
        if packs.in_pack(m):
            return False                  # its pack's hunt is its brain
    except ImportError:
        pass
    return True


# ---------------------------------------------------------------------------
# What it knows: the View
# ---------------------------------------------------------------------------

class Ctx:
    """The tiles and paths the snapshot found, for carrying the choice out."""

    def __init__(self):
        self.slots = set()
        self.flank = None            # (spot, path)
        self.dark = None             # path to a tile out of his sight
        self.in_sight = False
        self.door = None             # path to a narrow tile behind it ([] : on one)
        self.rotate_with = None
        self.feint = None            # {'mouth', 'hides', 'waiters'}
        self.pet = None
        self.bait = None             # {'tile', 'path', 'hazard', 'name', 'hidden'}
        self.screen = None           # tile to stand on (None: hold where it is)
        self.leader = None
        self.allies = []
        self.occ = set()
        self.cover = None            # path to a tile out of his line of fire


def _clear(ax, ay, bx, by, dungeon) -> bool:
    import senses
    return senses.clear_view(ax, ay, bx, by, dungeon)


def allies_known(m, all_monsters, dungeon) -> list:
    """Its side (faction.same_side) that it knows of: in its sight within
    10 tiles, or of its own war-band (they shout to each other)."""
    import faction
    out = []
    band = m.__dict__.get('_band')
    for o in all_monsters or ():
        if o is m or not getattr(o, 'alive', False):
            continue
        if _cheb(o.x, o.y, m.x, m.y) > 10:
            continue
        if not faction.same_side(m, o):
            continue
        if (band and o.__dict__.get('_band') == band) or _clear(m.x, m.y, o.x, o.y, dungeon):
            out.append(o)
    return out


def side_slots(m, player, dungeon, all_monsters, extra_occupied, allies) -> set:
    """The tiles beside the hero its side can get at from where it stands
    with a short walk (its friends' tiles count: they are on him already). At
    a choke (a corridor, the far side of a doorway) there is one, or none."""
    import packs
    from geom import occupied_tiles
    mine = {id(o) for o in allies}
    others = set()
    for o in all_monsters or ():
        if o is m or not getattr(o, 'alive', False) or id(o) in mine:
            continue
        others.update(occupied_tiles(o))
    others |= set(extra_occupied or ())
    hero = (player.x, player.y)
    ok = packs._ok_fn(dungeon)
    goals = [p for p in packs.ring(*hero) if ok(*p) and p not in others]
    d0 = _cheb(m.x, m.y, *hero)
    got = set(packs.bfs((m.x, m.y), ok, others | {hero}, goals, max_len=d0 + 3, max_nodes=300))
    if d0 <= 1:
        got.add((m.x, m.y))                  # beside him already: its own tile is one
    return got


def narrow(dungeon, x, y) -> bool:
    """A narrow way: a walkable tile with rock on both sides (a corridor, a
    doorway)."""
    w = dungeon.is_walkable
    if not w(x, y):
        return False
    return (not w(x - 1, y) and not w(x + 1, y)) or (not w(x, y - 1) and not w(x, y + 1))


def hazard_here(dungeon, x, y):
    """(name, hidden) of a danger a creature of the floor knows on (x, y): a
    trap the hero's own hands did not set (no monster knows a rewired one),
    or a live hazard fixture. None for none."""
    t = (getattr(dungeon, 'traps', None) or {}).get((x, y))
    if t and not t.get('safe_for_player'):
        return (str(t.get('name') or 'trap').lower(), not t.get('revealed'))
    try:
        import hazards
        h = hazards.hazard_at(dungeon, x, y)
    except Exception:
        h = None
    if h:
        return (str((h[1] or {}).get('name') or h[0]).replace('_', ' ').lower(), False)
    return None


def line_tiles(x0, y0, x1, y1) -> list:
    """The tiles of a straight line from (x0, y0) to (x1, y1), both ends out."""
    out = []
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
        if (cx, cy) != (x1, y1):
            out.append((cx, cy))
    return out


_WAITING = ('hold_choke', 'wait_allies', 'screen', 'leave_light', 'bait', 'hold_door')


def _comes_on(o) -> bool:
    """A friend that will come to the hero (not an archer or a caster keeping
    its distance, not one holding back itself)."""
    if getattr(o, 'ai_pattern', '') != 'aggressive':
        return False
    if o.__dict__.get('_band_role') in ('shooter', 'caster', 'healer'):
        return False
    return o.__dict__.get('_tm_last') not in _WAITING


def _new_fight(m) -> None:
    """Out of touch with the hero a while: its patience and its tricks are
    its own again."""
    d = m.__dict__
    seen = d.get('_tm_seen')
    if TURN.n and seen is not None and TURN.n - int(seen) > NEW_FIGHT:
        for k in ('_tm_wait', '_tm_edge', '_tm_door', '_tm_bait', '_tm_dark_strike', '_tm_plan',
                  '_tm_watch', '_tm_cover', '_tm_covered', '_tm_cover_struck'):
            d.pop(k, None)
    m._tm_seen = TURN.n


def snapshot(m, player, dungeon, all_monsters, extra_occupied):
    """(View, Ctx) of what ``m`` knows this turn."""
    import lanes
    import packs
    import senses
    mind = mind_of(m)
    sp = tactics.spec(mind)
    w = sp.get('weights') or {}
    d = m.__dict__
    ctx = Ctx()
    hero = (player.x, player.y)
    dist = _cheb(m.x, m.y, *hero)
    adjacent = bool(m._adjacent_to(player))
    sees = bool(senses.sees(m, player, dungeon))
    hp_share = m.hp / max(1, m.max_hp)
    hero_share = (player.hp / max(1, player.max_hp)) if sees else 1.0
    held = bool(sees and packs.held(player))
    occ = packs._occupied(m, all_monsters, extra_occupied, player)
    ctx.occ = occ
    allies = allies_known(m, all_monsters, dungeon)
    ctx.allies = allies
    live = [o for o in allies if not broken(o)]
    engaged = sum(1 for o in live if o._adjacent_to(player))
    # A friend about to come up: hunting him, coming on, a little behind it.
    coming = sum(1 for o in live
                 if o.__dict__.get('_tracking') and _comes_on(o) and not o._adjacent_to(player)
                 and _cheb(o.x, o.y, *hero) > dist and _cheb(o.x, o.y, m.x, m.y) <= 4)
    engage_r = int(tactics.data().get('engage_radius', 6))
    choke = False
    if dist <= engage_r and (w.get('hold_choke') or w.get('flank') or w.get('feint')):
        ctx.slots = side_slots(m, player, dungeon, all_monsters, extra_occupied, allies)
        choke = len(ctx.slots) == 1 or (not ctx.slots and narrow(dungeon, *hero))
    import under_fire
    hp_was = d.get('_tm_hp')
    hurt = hp_was is not None and under_fire.blow_hp(m) < int(hp_was)   # (a bleed is no blow)
    usable = lanes.usable(m)
    has_lane = bool(usable) and 2 <= dist <= lanes.reach(m) and lanes.clear_shot(
        m.x, m.y, player.x, player.y, dungeon, occ - {hero})
    role = str(d.get('_band_role') or '') if d.get('_band') else ''
    order = band_order(m, player, dungeon, all_monsters) if role else ''
    import habits
    learns = bool(sp.get('learns'))

    def _habit(h):
        return habits.count(dungeon, m, h, monsters=all_monsters) if learns else 0
    view = dict(mind=mind, dist=dist, adjacent=adjacent, sees_hero=sees, hp_share=hp_share,
                hero_hp_share=hero_share, hero_held=held, choke=choke,
                engaged=engaged, coming=coming, waited=int(d.get('_tm_wait', 0) or 0),
                hurt_lately=hurt, has_lane=has_lane, role=role, order=order,
                habit_choke=_habit('choke_fighter'), habit_area=_habit('opens_with_area'),
                habit_kiter=_habit('kiter'), habit_rest=_habit('rester_near_foes'),
                hero_resting=bool(getattr(senses.TURN, 'rested', False)) and sees,
                knows_traps=flag(m, 'knows_traps'), dark_edge=flag(m, 'dark_edge'))
    if w.get('cast') and not adjacent and 'cast' not in OFF:
        view['can_cast'] = bool(castable(m, player, dungeon, all_monsters, occ))
    if w.get('flank') and engaged and not choke and not adjacent and dist <= 3 and ctx.slots:
        ctx.flank = _flank_spot(m, player, dungeon, occ, live, ctx.slots, view['habit_area'])
        view['flank_spot'] = ctx.flank is not None
    if view['dark_edge'] and w.get('leave_light') and sees and not adjacent:
        hs = _dark(m, player, dungeon, occ, ctx)
        view.update(in_his_sight=ctx.in_sight, hero_sight=hs, dark_tile=ctx.dark is not None,
                    dark_struck=bool(d.get('_tm_dark_strike')),
                    edge_retreats=int(d.get('_tm_edge', 0) or 0))
    # A companion beside him that it can see (a pet it has not seen is not
    # one it plans against).
    company = any(_cheb(p.x, p.y, *hero) <= 2
                  and _cheb(p.x, p.y, m.x, m.y) <= senses.sight_range(m, player)
                  and _clear(m.x, m.y, p.x, p.y, dungeon) for p in TURN.pets)
    view['hero_has_company'] = company
    if (w.get('hold_door') and company and not adjacent
            and hp_share < float(tactics.data().get('door_below', 0.5))):
        ctx.door = _door_path(m, player, dungeon, occ)
        view['door_tile'] = ctx.door is not None
        view['door_turns'] = int(d.get('_tm_door', 0) or 0)
    if sp.get('rotates') and adjacent and hp_share < float(tactics.data().get('rotate_below', 0.4)):
        ctx.rotate_with = _fresh_behind(m, player, dungeon, live)
        rested = TURN.n == 0 or d.get('_tm_rotated') is None or TURN.n - int(d['_tm_rotated']) >= int(
            tactics.data().get('rotate_rest', 6))
        view['rotate_ok'] = ctx.rotate_with is not None and rested
    if w.get('feint') and d.get('_band') and sees and dist <= 1:
        if not ctx.slots:
            ctx.slots = side_slots(m, player, dungeon, all_monsters, extra_occupied, allies)
            choke = len(ctx.slots) == 1
            view['choke'] = choke
        if choke:
            ctx.feint = _feint_plan(m, player, dungeon, all_monsters, occ, ctx.slots)
            view['feint_ok'] = ctx.feint is not None
    if sp.get('focus_weak') and sees and 'focus_pet' not in OFF and TURN.pets:
        ctx.pet = _pet_target(m, dungeon, all_monsters, hero_share)
        view['pet_target'] = ctx.pet is not None
    if view['knows_traps'] and w.get('bait') and not adjacent and sees and 2 <= dist <= 6:
        ctx.bait = _bait_spot(m, player, dungeon, occ)
        view['bait_tile'] = ctx.bait is not None
        view['bait_turns'] = int(d.get('_tm_bait', 0) or 0)
    if order == 'screen' and role in ('guard', 'leader') and not adjacent:
        ok, tile, leader = _screen(m, player, dungeon, all_monsters, occ, role)
        view['screen_tile'] = ok
        ctx.screen = tile
        ctx.leader = leader
    if order == 'fall_back' and not adjacent:
        leader = leader_of(m)
        if leader is not None and leader is not m and _cheb(m.x, m.y, leader.x, leader.y) > 2:
            view['rally_tile'] = True
            ctx.leader = leader
    # Into Cover (src/under_fire.py): shot from afar, a thinking kind that
    # fights hand to hand ducks out of his line of fire (a charger rushes).
    import under_fire
    view['under_fire'] = under_fire.under_fire(m)
    view['rushing'] = under_fire.rushing(m)
    if (tactics.cover_weight(mind) > 0 and getattr(m, 'ai_pattern', '') == 'aggressive'
            and not under_fire.rusher(m) and not adjacent and 'take_cover' not in OFF):
        in_sight = hero_sees(m, player, dungeon)
        view.setdefault('in_his_sight', in_sight)
        view['in_cover'] = bool(d.get('_tm_cover'))
        view['covered'] = int(d.get('_tm_covered', 0) or 0)
        view['cover_struck'] = bool(d.get('_tm_cover_struck'))
        if view['under_fire'] and in_sight and not has_lane:
            ctx.cover = _cover_path(m, player, dungeon, occ)
            view['cover_tile'] = ctx.cover is not None
    return tactics.View(**view), ctx


# ---------------------------------------------------------------------------
# The features
# ---------------------------------------------------------------------------

def _flank_spot(m, player, dungeon, occ, live, slots, area_habit):
    import packs
    hero = (player.x, player.y)
    on_him = [o for o in live if o._adjacent_to(player)]
    pressure = [(o.x, o.y) for o in on_him]
    free = [s for s in slots if s not in occ]
    if not free or not pressure:
        return None
    ok = packs._ok_fn(dungeon)
    paths = packs.bfs((m.x, m.y), ok, occ, free, _cheb(m.x, m.y, *hero) + 3, 200,
                      avoid=set(packs.ring(*hero)))
    if not paths:
        return None
    spot = packs.choose_spot(player, paths, pressure, circle=True,
                             back=packs.back_tile(player, on_him))
    if spot is None:
        return None
    if min(_cheb(spot[0], spot[1], px, py) for px, py in pressure) < 2:
        return None
    # Worth the walk only when it is not where it was going anyway.
    if _cheb(m.x, m.y, *spot) <= 1 and not area_habit:
        return None
    return spot, list(paths[spot])


def _dark(m, player, dungeon, occ, ctx) -> int:
    """Whether the hero can see it where it stands (ctx.in_sight), and a
    path to a tile within two steps out of his sight from which it still
    sees him (ctx.dark). Returns how far he sees."""
    import packs
    import senses
    try:
        hs = int(player.get_sight_radius())
    except Exception:
        hs = 5
    hero = (player.x, player.y)
    mine = senses.sight_range(m, player)
    here = _cheb(m.x, m.y, *hero)
    ctx.in_sight = here <= hs and senses.clear_view(player.x, player.y, m.x, m.y, dungeon)
    ctx.dark = None
    if not ctx.in_sight:
        return hs
    ok = packs._ok_fn(dungeon)
    goals = []
    for y in range(m.y - 2, m.y + 3):
        for x in range(m.x - 2, m.x + 3):
            if (x, y) in occ or not ok(x, y):
                continue
            dd = _cheb(x, y, *hero)
            if dd <= hs or dd > mine:
                continue
            if not senses.clear_view(x, y, player.x, player.y, dungeon):
                continue
            if hazard_here(dungeon, x, y):
                continue
            goals.append((x, y))
    if goals:
        paths = packs.bfs((m.x, m.y), ok, occ, goals, 2, 60)
        if paths:
            best = min(sorted(paths), key=lambda t: (len(paths[t]), _cheb(t[0], t[1], *hero)))
            ctx.dark = list(paths[best])
    return hs


def _cover_path(m, player, dungeon, occ):
    """A path to a tile within cover_reach steps that the hero cannot see
    (round a corner, or past his light), no more than cover_slack tiles
    farther from him than it stands, never beside him or on a danger; the
    shortest, then the nearest him. None when there is none."""
    import packs
    import senses
    cfg = tactics.data().get('under_fire') or {}
    reach = int(cfg.get('cover_reach', 2))
    slack = int(cfg.get('cover_slack', 1))
    try:
        hs = int(player.get_sight_radius())
    except Exception:
        hs = 5
    hero = (player.x, player.y)
    here = _cheb(m.x, m.y, *hero)
    ok = packs._ok_fn(dungeon)
    goals = []
    for y in range(m.y - reach, m.y + reach + 1):
        for x in range(m.x - reach, m.x + reach + 1):
            if (x, y) in occ or not ok(x, y):
                continue
            dd = _cheb(x, y, *hero)
            if dd < 2 or dd > here + slack:
                continue
            if dd <= hs and senses.clear_view(player.x, player.y, x, y, dungeon):
                continue
            if hazard_here(dungeon, x, y):
                continue
            goals.append((x, y))
    if not goals:
        return None
    paths = packs.bfs((m.x, m.y), ok, occ, goals, reach, 80)
    if not paths:
        return None
    best = min(sorted(paths), key=lambda t: (len(paths[t]), _cheb(t[0], t[1], *hero)))
    return list(paths[best])


def _door_path(m, player, dungeon, occ):
    """A narrow tile (a doorway, a corridor's mouth) within door_reach steps,
    no nearer the hero than it stands, to back into; [] when it stands in
    one; None when there is none."""
    import packs
    reach = int(tactics.data().get('door_reach', 4))
    hero = (player.x, player.y)
    here = _cheb(m.x, m.y, *hero)
    if narrow(dungeon, m.x, m.y):
        return []
    goals = []
    for y in range(m.y - reach, m.y + reach + 1):
        for x in range(m.x - reach, m.x + reach + 1):
            if (x, y) in occ or _cheb(x, y, *hero) < max(2, here):
                continue
            if narrow(dungeon, x, y) and not hazard_here(dungeon, x, y):
                goals.append((x, y))
    if not goals:
        return None
    paths = packs.bfs((m.x, m.y), packs._ok_fn(dungeon), occ, goals, reach, 120)
    if not paths:
        return None
    best = min(sorted(paths), key=lambda t: len(paths[t]))
    return list(paths[best])


def _fresh_behind(m, player, dungeon, live):
    """A fresh soldier of its side right behind it (beside it, not beside the
    hero), able to step up: the one it changes places with."""
    fresh = float(tactics.data().get('rotate_fresh', 0.7))
    if hazard_here(dungeon, m.x, m.y):
        return None
    for o in sorted(live, key=lambda o: (o.y, o.x)):
        if _cheb(o.x, o.y, m.x, m.y) != 1 or o._adjacent_to(player):
            continue
        if tuple(getattr(o, 'footprint', (1, 1)) or (1, 1)) != (1, 1):
            continue
        if o.hp < o.max_hp * fresh or not o.__dict__.get('_tracking'):
            continue
        if any(_has(o, e) for e in CANNOT) or mind_of(o) != 'soldier' or excluded(o):
            continue
        if hazard_here(dungeon, o.x, o.y):
            continue
        return o
    return None


def leader_of(m):
    """Its band's leader if he leads now, or None; itself, if it leads and
    may. He leads while he lives, is his own master and can shout, and his
    morale has not broken him (fleeing, at bay, cowed, yielded). Who still
    answers to him is AI-1's rule (war_bands.holds_nerve: a captain who begs
    leads no one; a babbled follower cannot hear him); a band whose captain
    cannot lead answers as if he had fallen."""
    if m.__dict__.get('_band_role') == 'leader':
        return m if commands(m) else None
    lead = m.__dict__.get('_band_leader')
    if lead is None:
        return None
    import war_bands
    if not war_bands.holds_nerve(m):
        return None
    return lead if commands(lead) else None


def commands(lead) -> bool:
    """A leader who can lead now: he can shout (can_shout) and his nerve is
    his own (not broken by his morale: src/morale.py)."""
    return can_shout(lead) and not broken(lead)


def _feint_plan(m, player, dungeon, all_monsters, occ, slots):
    """Can its band feign flight here? The mouth of the narrow way (its
    side's one tile beside the hero), at least `need` of the band in reach of
    hiding places beside the mouth that the hero cannot see, a captain alive.
    Once a band a floor."""
    import packs
    import senses
    import war_bands
    band = getattr(dungeon, 'band', None)
    uid = m.__dict__.get('_band')
    if not isinstance(band, dict) or band.get('uid') != uid or band.get('feinted'):
        return None
    if not slots or leader_of(m) is None:
        return None
    mouth = min(slots, key=lambda s: (_cheb(s[0], s[1], m.x, m.y), s))
    ok = packs._ok_fn(dungeon)
    hero = (player.x, player.y)
    hides = []
    for y in range(mouth[1] - 2, mouth[1] + 3):
        for x in range(mouth[0] - 2, mouth[0] + 3):
            if not ok(x, y) or (x, y) in occ or (x, y) == mouth:
                continue
            if _cheb(x, y, *hero) < 2 or _cheb(x, y, *mouth) > 2:
                continue
            if senses.clear_view(x, y, hero[0], hero[1], dungeon) or hazard_here(dungeon, x, y):
                continue
            hides.append((x, y))
    need = int((tactics.data().get('feint') or {}).get('need', 2))
    waiters = [o for o in war_bands.members_of(all_monsters, uid)
               if o is not m and o.alive and not broken(o) and o.__dict__.get('_tracking')
               and not any(_has(o, e) for e in CANNOT) and mind_of(o) is not None
               and _cheb(o.x, o.y, *mouth) <= 6 and not o._adjacent_to(player)]
    if len(hides) < need or len(waiters) < need:
        return None
    return {'mouth': mouth, 'hides': sorted(hides, key=lambda t: (_cheb(t[0], t[1], *mouth), t)),
            'waiters': waiters}


def _pet_target(m, dungeon, all_monsters, hero_share):
    """A badly hurt pet it can see within reach, while the hero is not
    badly hurt himself, and while fewer than half of the creatures that see
    that pet (at least one) already go for it."""
    import senses
    f = tactics.data().get('focus') or {}
    if hero_share < float(f.get('hero_above', 0.35)):
        return None
    reach = int(f.get('reach', 6))
    best = None
    for p in TURN.pets:
        if not focusable(p) or _cheb(p.x, p.y, m.x, m.y) > reach:
            continue
        if p.hp >= float(f.get('pet_below', 0.35)) * max(1, p.max_hp):
            continue
        if not senses.clear_view(m.x, m.y, p.x, p.y, dungeon):
            continue
        cap = max(1, int(seers(p, all_monsters, dungeon) * float(f.get('share', 0.5))))
        if TURN.focus.get(id(p), 0) >= cap:
            continue
        key = (p.hp / max(1, p.max_hp), _cheb(p.x, p.y, m.x, m.y), p.y, p.x)
        if best is None or key < best[0]:
            best = (key, p)
    return best[1] if best else None


def seers(p, all_monsters, dungeon) -> int:
    """How many hostile creatures can see this pet (counted once a turn)."""
    got = TURN.seers.get(id(p))
    if got is not None:
        return got
    import senses
    n = 0
    for o in all_monsters or ():
        if not getattr(o, 'alive', False) or kind_data.outside_rules(o):
            continue
        if _cheb(o.x, o.y, p.x, p.y) > senses.sight_range(o):
            continue
        if senses.clear_view(o.x, o.y, p.x, p.y, dungeon):
            n += 1
    TURN.seers[id(p)] = n
    return n


def _bait_spot(m, player, dungeon, occ):
    """A tile it can reach without stepping on a danger, from which the
    hero's straight way to it runs over a known danger near him."""
    import packs
    hero = (player.x, player.y)
    reach = int(tactics.data().get('bait_reach', 3))
    dangers = {}
    for y in range(hero[1] - 4, hero[1] + 5):
        for x in range(hero[0] - 4, hero[0] + 5):
            if (x, y) != hero:
                h = hazard_here(dungeon, x, y)
                if h:
                    dangers[(x, y)] = h
    if not dangers:
        return None
    ok0 = packs._ok_fn(dungeon)

    def ok(x, y):
        return ok0(x, y) and (x, y) not in dangers
    here = (m.x, m.y)
    goals = []
    for y in range(m.y - reach, m.y + reach + 1):
        for x in range(m.x - reach, m.x + reach + 1):
            if not ok(x, y) or ((x, y) in occ and (x, y) != here):
                continue
            dd = _cheb(x, y, *hero)
            if dd < 2 or dd > 5:
                continue
            on = [t for t in line_tiles(hero[0], hero[1], x, y)
                  if t in dangers and _cheb(t[0], t[1], *hero) <= 3]
            if on:
                goals.append(((x, y), on[0]))
    if not goals:
        return None
    paths = packs.bfs(here, ok, occ, [g for g, _h in goals if g != here], reach, 120)
    cands = [(g, h) for g, h in goals if g == here or g in paths]
    if not cands:
        return None
    tile, haz = min(sorted(cands), key=lambda gh: (0 if gh[0] == here else len(paths[gh[0]]), gh))
    name, hidden = dangers[haz]
    return {'tile': tile, 'path': [] if tile == here else list(paths[tile]),
            'hazard': haz, 'name': name, 'hidden': hidden}


def _screen(m, player, dungeon, all_monsters, occ, role):
    """(open, tile, leader): a guard's place between the hero and its
    leader (beside the leader, on his side toward the hero; None: hold
    where it is); the leader hangs back while a guard of his stands nearer
    the hero."""
    import packs
    lead = leader_of(m)
    if lead is None:
        return False, None, None
    reach = int((tactics.data().get('orders') or {}).get('screen_reach', 7))
    hero = (player.x, player.y)
    if _cheb(lead.x, lead.y, *hero) > reach:
        return False, None, lead
    if role == 'leader':
        # He hangs back while his guards come up and stand before him.
        import war_bands
        guards = [o for o in war_bands.members_of(all_monsters, m.__dict__.get('_band'))
                  if o is not m and o.alive and o.__dict__.get('_band_role') == 'guard'
                  and not broken(o) and not any(_has(o, e) for e in CANNOT)
                  and _cheb(o.x, o.y, m.x, m.y) <= 8]
        return bool(guards) and _cheb(m.x, m.y, *hero) >= 2, None, lead
    ok = packs._ok_fn(dungeon)
    for t in line_tiles(lead.x, lead.y, hero[0], hero[1])[:2]:
        if t == (m.x, m.y):
            return True, None, lead                    # on its place: it holds
        if ok(*t) and t not in occ and not hazard_here(dungeon, *t) and _cheb(m.x, m.y, *t) <= 6:
            return True, t, lead
    if _cheb(m.x, m.y, lead.x, lead.y) <= 1:
        return True, None, lead                        # beside him already
    return False, None, lead


# ---------------------------------------------------------------------------
# The cast (AI-3's caster_ai.choose() is meant to decide in choose_cast)
# ---------------------------------------------------------------------------

def is_spell(atk) -> bool:
    """A spell shot from afar, as the gates mean it (wards.is_cast: what
    Silence stops), not a missile, a breath, a gaze or a cry."""
    import wards
    return isinstance(atk, dict) and wards.is_cast(atk)


def castable(m, player, dungeon, all_monsters, occ=None) -> list:
    """The spells it may cast at the hero now: in reach, with a clear shot,
    and open to it by the gates (lanes.usable asks attack_gates.blocks_attack:
    none while it is silenced; no shot at all while it is unstrung), never a
    breath still drawing."""
    import lanes
    dist = _cheb(m.x, m.y, player.x, player.y)
    if dist < 2:
        return []
    if occ is None:
        import packs
        occ = packs._occupied(m, all_monsters, (), player)
    if not lanes.clear_shot(m.x, m.y, player.x, player.y, dungeon, set(occ) - {(player.x, player.y)}):
        return []
    return [a for a in lanes.usable(m) if is_spell(a) and lanes.attack_range(a) >= dist]


def choose_cast(m, player, dungeon, all_monsters, rng=random):
    """The spell it casts now, or None: of its castable spells, the one the
    Caster's Book picks (AI-3, caster_ai.pick_attack: its book's weight for
    it, a curse that would take, its weight of blow, never a type the hero
    wards off), the same choice a caster that does not think makes from
    range (Monster.attack). The book's other spells (a ward, a curse, a
    mending, a blink) come before the Tactical Mind's turn (src/ai_turn.py).
    At random only for a creature the book does not rule (a named foe)."""
    spells = castable(m, player, dungeon, all_monsters)
    if not spells:
        return None
    if len(spells) == 1:
        return spells[0]
    import caster_ai
    best = caster_ai.pick_attack(m, player, spells)
    return best if best is not None else rng.choice(spells)


# ---------------------------------------------------------------------------
# The Captain's Orders
# ---------------------------------------------------------------------------

def can_shout(m) -> bool:
    """A leader who can give an order: alive, awake, free, his own master,
    his voice his own, and not begging, fleeing or at bay."""
    if m is None or not getattr(m, 'alive', False):
        return False
    if any(_has(m, e) for e in CANNOT + ('silenced',)):
        return False
    return not broken(m) and not busy(m)


def band_order(m, player, dungeon, all_monsters) -> str:
    """The order of ``m``'s band this turn ('' for none): screen, charge or
    fall_back, decided once a turn while the leader can shout and knows
    where the hero is. A new order is shouted (the leader's line)."""
    band = getattr(dungeon, 'band', None)
    uid = m.__dict__.get('_band')
    if not isinstance(band, dict) or not uid or band.get('uid') != uid:
        return ''
    if TURN.n and band.get('order_turn') == TURN.n:
        return str(band.get('order') or '')
    lead = leader_of(m)
    order = ''
    if lead is not None and lead.__dict__.get('_tracking'):
        import packs
        import senses
        import war_bands
        o = tactics.data().get('orders') or {}
        # What he knows of the hero is what he sees (senses.sees: his sight,
        # its reach, invisibility); out of his sight, his last picture of
        # him, or nothing.
        if senses.sees(lead, player, dungeon):
            seen = (player.hp / max(1, player.max_hp), bool(packs.held(player)))
            band['hero_seen'] = seen
        else:
            seen = band.get('hero_seen')
        total = 1 + sum(int(v or 0) for v in (band.get('counts') or {}).values())
        alive = sum(1 for x in war_bands.members_of(all_monsters, uid) if x.alive)
        until = int(band.get('fall_back_until', -1) or -1)
        # Once called, the charge holds until the hero is well again (no
        # shouting back and forth as his health crosses the line).
        if seen:
            share, held = float(seen[0]), bool(seen[1])
            charging = band.get('order') == 'charge' and share < float(o.get('charge_until', 0.6))
            charge = charging or share < float(o.get('charge_below', 0.4)) or held
        else:
            charge = False
        if charge:
            order = 'charge'
        elif band.get('fell_back') and TURN.n and TURN.n < until:
            order = 'fall_back'
        elif alive * 2 <= total and not band.get('fell_back'):
            order = 'fall_back'
            band['fell_back'] = True
            band['fall_back_until'] = TURN.n + int(o.get('fall_back_turns', 6))
        else:
            import under_fire
            if under_fire.under_fire(lead):
                # Shot at, he no longer hangs back behind his guards: the
                # band comes on (src/under_fire.py).
                order = ''
                text = ((tactics.data().get('under_fire') or {}).get('lines') or {}).get('drop_screen', '')
                if text and band.get('order') == 'screen' and ai_lines.once(lead, 'drop_screen'):
                    ai_lines.say(lead, ai_lines.fill(lead, text), '', 'warning')
            else:
                order = 'screen'
    was = str(band.get('order') or '')
    band['order'] = order
    band['order_turn'] = TURN.n
    if order and order != was:
        _shout(lead, band, order, player)
    return order


def _shout(lead, band, order, player) -> None:
    o = tactics.data().get('orders') or {}
    lines = dict(o.get('default') or {})
    lines.update(o.get(str(band.get('id') or '')) or {})
    text = lines.get(order, '')
    if not text:
        return
    try:
        import counters
        deaf = counters.ears_stopped(player)
    except Exception:
        deaf = False
    if deaf:
        ai_lines.say(lead, ai_lines.fill(lead, o.get('wax', '')), '', 'warning')
    else:
        ai_lines.say(lead, ai_lines.fill(lead, text), o.get('unseen', ''), 'warning')


# ---------------------------------------------------------------------------
# Lines
# ---------------------------------------------------------------------------

def side_key(m) -> str:
    import faction
    f = faction.ai_faction(m)
    return f'{f[0]}:{f[1]}'


def say(m, key: str, dungeon, colour: str = 'warning', **kw) -> bool:
    """Say option ``key``'s line for ``m`` once a fight for its side (again
    after line_again_after turns). True if it was said."""
    text = (tactics.data().get('lines') or {}).get(key, '')
    if not text:
        return False
    store = dict((dungeon.__dict__.get('_tm_said') if dungeon is not None else None) or {})
    k = f'{side_key(m)}|{key}'
    last = store.get(k)
    again = int(tactics.data().get('line_again_after', 60))
    if last is not None and (TURN.n == 0 or TURN.n - int(last) < again):
        return False
    store[k] = TURN.n
    if dungeon is not None:
        dungeon.__dict__['_tm_said'] = store
    seen = ai_lines.fill(m, text, **kw)
    unseen = (tactics.data().get('unseen') or {}).get(key, '')
    if m.__dict__.get('_tm_witnessed'):
        # He saw it decide (it was in his sight when its turn began): the line
        # stands though its move took it out of his sight (the hold, the
        # dark edge, the feint).
        unseen = seen
    ai_lines.say(m, seen, unseen, colour)
    return True


def hero_sees(m, player, dungeon) -> bool:
    """Can the hero see this creature where it stands (his light's reach, a
    clear view, not invisible to him)? In the game, as its turn began, his
    own field of view says (the Game's ``_hero_saw``, Game._sees_monster):
    the guess below (a square of his sight's radius, a straight line) took
    a creature at the corner of his sight, outside his round field of view,
    for one he could see, and its line named it to a hero who could not.
    The guess is for a creature the Game has not looked at this turn (the
    simulator, a test)."""
    saw = getattr(m, '__dict__', {}).get('_hero_saw')
    if isinstance(saw, tuple) and len(saw) == 2 and TURN.n and saw[0] == TURN.n:
        return bool(saw[1])
    if getattr(m, '_unseen', False) is True:
        return False
    try:
        hs = int(player.get_sight_radius())
    except Exception:
        hs = 5
    if _cheb(m.x, m.y, player.x, player.y) > hs:
        return False
    return _clear(player.x, player.y, m.x, m.y, dungeon)


# ---------------------------------------------------------------------------
# The turn
# ---------------------------------------------------------------------------

def turn(m, player, dungeon, all_monsters, extra_occupied=None, pattern: str = 'aggressive'):
    """The mind's turn (Monster.take_turn, for its hunting ``pattern``: the
    aggressive or the ranged way). True: it strikes now; False: it spent the
    turn on its plan; None: today's code takes the turn."""
    d = m.__dict__
    if d.pop('_tm_cast_set', None):
        d.pop('_pack_blow', None)            # a cast never thrown (the turn went elsewhere)
    d.pop('_focus', None)
    d.pop('_tm_surprise', None)
    d.pop('_tm_witnessed', None)
    if pattern not in ('aggressive', 'ranged') or not thinks(m, player):
        if d.get('_tm_plan') is not None:
            m._tm_plan = None
        return None
    _new_fight(m)
    feint = _feint_turn(m, player, dungeon, all_monsters, extra_occupied)
    if feint is not None:
        m._tm_hp = _blow_hp(m)
        return feint
    view, ctx = snapshot(m, player, dungeon, all_monsters, extra_occupied)
    sp = tactics.spec(view.mind)
    plan = d.get('_tm_plan')
    if isinstance(plan, dict):
        at = plan.get('at')
        if at is None or _cheb(at[0], at[1], player.x, player.y) > 2 or (
                TURN.n and plan.get('n') is not None and TURN.n - int(plan['n']) > 3):
            plan = None
    opt, _sc = tactics.decide(view, sp, plan)
    if opt in OFF:
        opt = 'attack'
    if opt == 'attack':
        _say_why_it_comes(m, view, sp, dungeon)
    m._tm_hp = _blow_hp(m)
    m._tm_witnessed = hero_sees(m, player, dungeon)
    if opt == 'attack':
        m._tm_plan = None
        m._tm_last = 'attack'
        d.pop('_tm_watch', None)
        d.pop('_tm_cover', None)             # it comes out of cover
        if view.adjacent:
            m._tm_wait = 0
        return None
    got = execute(opt, m, player, dungeon, all_monsters, extra_occupied, view, ctx)
    if got is None:
        m._tm_plan = None
        m._tm_last = 'attack'
        return None
    if isinstance(plan, dict) and plan.get('opt') == opt:
        m._tm_plan = tactics.spend(plan)
    else:
        fresh = tactics.new_plan(opt)
        fresh.update(at=(player.x, player.y), n=TURN.n)
        m._tm_plan = tactics.spend(fresh)
    m._tm_last = opt
    count = dict(d.get('_tm_used') or {})
    count[opt] = int(count.get(opt, 0)) + 1
    m._tm_used = count                       # what its mind did (the scenario harness reads it)
    return got


def _say_why_it_comes(m, view, sp, dungeon) -> None:
    """It would have held the mouth or waited for its friends, and comes on
    instead: say why, once (a habit seen, or the hero's wounds)."""
    if view.adjacent or view.rushing:
        return                               # (a charger's rush said its own line)
    if not (view.choke or (view.coming and 3 <= view.dist <= 5)):
        return
    h = tactics.data().get('habits') or {}
    if view.hero_resting and view.habit_rest >= int(h.get('rester_near_foes', 2)):
        say(m, 'habit_rester_near_foes', dungeon)
    elif view.habit_kiter >= int(h.get('kiter', 2)):
        say(m, 'habit_kiter', dungeon)
    elif tactics.pressing(view, sp) and view.order != 'charge':
        say(m, 'press', dungeon)


def _stepped(m, path, ctx, player, dungeon) -> bool:
    """One step of ``path`` (a fast one two); True if it moved."""
    import packs
    import under_fire
    if not path:
        return False
    got = packs._step_along(m, list(path), ctx.occ, player, dungeon,
                            under_fire.steps(m, 2 if int(getattr(m, 'speed', 10) or 10) >= 14 else 1))
    return got is not None


def _blow_hp(m) -> int:
    import under_fire
    return under_fire.blow_hp(m)


def _waited(m) -> None:
    m._tm_wait = int(m.__dict__.get('_tm_wait', 0) or 0) + 1


def execute(opt, m, player, dungeon, all_monsters, extra_occupied, view, ctx):
    """Carry ``opt`` out. True / False as take_turn; None when it cannot
    (the plan is dropped and today's code runs)."""
    import packs
    import senses
    if opt == 'hold_choke':
        path = packs.round_path(m, player, dungeon, ctx.occ, ctx.slots)
        if path and _stepped(m, path, ctx, player, dungeon):
            say(m, 'round', dungeon)
            return False
        if view.habit_choke >= int((tactics.data().get('habits') or {}).get('choke_fighter', 2)):
            say(m, 'habit_choke_fighter', dungeon)
        say(m, 'hold_choke' if [o for o in ctx.allies if not broken(o)] else 'hold_choke_alone',
            dungeon)
        import lanes
        packs.hold_step(m, player, dungeon, ctx.occ, ctx.slots,
                        view=lanes.reach(m) if lanes.usable(m) else 0)
        _waited(m)
        # Out of his sight it keeps its post (senses.notice) for the rest of
        # its patience, rather than walk in to look for him.
        m._tm_watch = max(1, int(tactics.data().get('patience', 10)) - int(m.__dict__.get('_tm_wait', 0)))
        return False
    if opt == 'wait_allies':
        say(m, 'wait_allies', dungeon)
        _waited(m)
        return False
    if opt == 'flank':
        if not ctx.flank:
            return None
        spot, path = ctx.flank
        if not _stepped(m, path, ctx, player, dungeon):
            return None
        m._pack_spot = spot
        m._pack_spot_at = (player.x, player.y)
        if view.habit_area >= 1:
            say(m, 'habit_opens_with_area', dungeon)
        say(m, 'flank', dungeon)
        return False
    if opt == 'leave_light':
        return _leave_light(m, player, dungeon, all_monsters, extra_occupied, view, ctx)
    if opt == 'hold_door':
        if ctx.door is None:
            return None
        if ctx.door and not _stepped(m, ctx.door, ctx, player, dungeon):
            return None
        m._tm_door = int(m.__dict__.get('_tm_door', 0) or 0) + 1
        say(m, 'hold_door', dungeon)
        return False
    if opt == 'rotate':
        o = ctx.rotate_with
        if o is None or not o.alive:
            return None
        m.x, m.y, o.x, o.y = o.x, o.y, m.x, m.y
        m._tm_rotated = TURN.n
        o._tm_rotated = TURN.n
        say(m, 'rotate', dungeon)
        return False
    if opt == 'feint':
        return _start_feint(m, player, dungeon, ctx)
    if opt == 'focus_pet':
        p = ctx.pet
        if p is None:
            return None
        if _cheb(m.x, m.y, p.x, p.y) > 1:
            if not senses.step_toward(m, dungeon, (p.x, p.y), all_monsters, extra_occupied, player):
                return None
        if _cheb(m.x, m.y, p.x, p.y) <= 1:
            m._focus = (id(p), TURN.n)       # this turn's choice only (focus_of)
        TURN.focus[id(p)] = TURN.focus.get(id(p), 0) + 1
        say(m, 'focus_pet', dungeon, pet=getattr(p, 'name', 'your pet'))
        return False
    if opt == 'cast':
        spell = choose_cast(m, player, dungeon, all_monsters)
        if spell is None:
            return None
        if not (getattr(m, 'multi_attack_count', 0) or getattr(m, 'multi_attack_always', False)):
            m._pack_blow = spell
            m._tm_cast_set = True
        say(m, 'cast', dungeon)
        return True
    if opt == 'screen':
        if ctx.screen is not None:
            if not senses.step_toward(m, dungeon, ctx.screen, all_monsters, extra_occupied, player):
                return None
        elif view.role == 'leader' and view.dist <= 2:
            back_off(m, player, dungeon, ctx.occ)
        _waited(m)
        return False
    if opt == 'fall_back':
        lead = ctx.leader
        if lead is None:
            return None
        if not senses.step_toward(m, dungeon, (lead.x, lead.y), all_monsters, extra_occupied, player):
            return None
        return False
    if opt == 'take_cover':
        return _take_cover(m, player, dungeon, all_monsters, extra_occupied, view, ctx)
    if opt == 'bait':
        b = ctx.bait
        if not b:
            return None
        if b['path'] and not _stepped(m, b['path'], ctx, player, dungeon):
            return None
        m._tm_bait = int(m.__dict__.get('_tm_bait', 0) or 0) + 1
        if (m.x, m.y) == tuple(b['tile']):
            if b['hidden']:
                say(m, 'bait_hidden', dungeon)
            else:
                say(m, 'bait', dungeon, hazard=b['name'])
        return False
    return None


def back_off(m, player, dungeon, occ) -> bool:
    """A step away from the hero, out of his sight first, never onto a
    danger. True if it moved."""
    import packs
    import senses
    ok = packs._ok_fn(dungeon)
    hero = (player.x, player.y)
    here = _cheb(m.x, m.y, *hero)
    opts = [p for p in packs.ring(m.x, m.y) if ok(*p) and p not in occ
            and _cheb(p[0], p[1], *hero) > here and m._can_move_to(dungeon, *p)
            and not hazard_here(dungeon, *p)]
    if not opts:
        return False
    best = min(sorted(opts), key=lambda p: (senses.clear_view(p[0], p[1], hero[0], hero[1], dungeon),
                                             -_cheb(p[0], p[1], *hero)))
    m.x, m.y = best
    return True


def _leave_light(m, player, dungeon, all_monsters, extra_occupied, view, ctx):
    """In his sight: step out of his light. Out of it: lurk at the edge; when
    he comes within two tiles, close and strike in the same turn (once a
    fight)."""
    import senses
    d = m.__dict__
    if view.in_his_sight:
        if not ctx.dark or not _stepped(m, ctx.dark, ctx, player, dungeon):
            return None
        m._tm_edge = int(d.get('_tm_edge', 0) or 0) + 1
        say(m, 'leave_light', dungeon)
        return False
    if view.dist <= 2:
        if (senses.step_toward(m, dungeon, (player.x, player.y), all_monsters, extra_occupied, player)
                and m._adjacent_to(player)):
            m._tm_dark_strike = True
            return True
        return None
    _waited(m)
    return False


def _take_cover(m, player, dungeon, all_monsters, extra_occupied, view, ctx):
    """Into Cover: in his sight and shot at, it ducks out of his line of
    fire and keeps its post there (senses.notice: the twang of his bow does
    not draw it out); round the corner it waits, and when he comes within
    two tiles it steps out and strikes first (once a fight)."""
    import senses
    d = m.__dict__
    if view.in_cover and (view.dist <= 2 or not view.in_his_sight):
        if view.dist <= 2:
            if (senses.step_toward(m, dungeon, (player.x, player.y), all_monsters, extra_occupied, player)
                    and m._adjacent_to(player)):
                m._tm_cover_struck = True
                d.pop('_tm_cover', None)
                return True
            return None
        _waited(m)
        return False
    if not ctx.cover or not _stepped(m, ctx.cover, ctx, player, dungeon):
        return None
    m._tm_cover = True
    m._tm_covered = int(d.get('_tm_covered', 0) or 0) + 1
    m._tm_watch = max(1, int(tactics.data().get('patience', 10)) - int(d.get('_tm_wait', 0) or 0))
    text = ((tactics.data().get('under_fire') or {}).get('lines') or {}).get('take_cover', '')
    if text and ai_lines.once(m, 'take_cover'):
        ai_lines.say(m, ai_lines.fill(m, text), '', 'warning')
    return False


# ---------------------------------------------------------------------------
# Feigned Flight
# ---------------------------------------------------------------------------

def _start_feint(m, player, dungeon, ctx):
    """The feinter falls back into the room; the waiters take the hiding
    places beside the mouth (each on its own turn: _feint_turn)."""
    f = ctx.feint
    band = getattr(dungeon, 'band', None)
    if not f or not isinstance(band, dict):
        return None
    cfg = tactics.data().get('feint') or {}
    turns = int(cfg.get('turns', 4))
    band['feinted'] = True
    band['feint_sprung'] = False
    plan = {'mouth': tuple(f['mouth']), 'hides': [tuple(t) for t in f['hides']], 'left': turns + 2}
    for o in f['waiters']:
        o._tm_feint = dict(plan)
        o._tm_watch = turns + 2              # hidden, it keeps its place (senses.notice)
    m._tm_feinter = int(cfg.get('back', 3))
    known = False
    try:
        import family_lore
        known = family_lore.knowledge(player, m.kind) >= family_lore.KNOWN
    except Exception:
        known = False
    say(m, 'feint_known' if known else 'feint', dungeon, colour='info' if known else 'warning')
    back_off(m, player, dungeon, ctx.occ)
    return False


def _feint_turn(m, player, dungeon, all_monsters, extra_occupied):
    """A turn of the band's feint for ``m``, or None when it has no part in
    one now. The feinter keeps falling back; each waiter holds a hiding place
    beside the mouth; a hero who steps out of the narrow way is struck by
    each waiter beside him, its first blow easier to land."""
    import packs
    d = m.__dict__
    occ = None
    back = int(d.get('_tm_feinter', 0) or 0)
    if back > 0:
        m._tm_feinter = back - 1
        if m._adjacent_to(player):
            return None
        occ = packs._occupied(m, all_monsters, extra_occupied, player)
        back_off(m, player, dungeon, occ)
        return False
    f = d.get('_tm_feint')
    if not isinstance(f, dict):
        return None
    left = int(f.get('left', 0) or 0) - 1
    if left <= 0:
        d.pop('_tm_feint', None)
        return None
    m._tm_feint = dict(f, left=left)
    hero = (player.x, player.y)
    mouth = tuple(f.get('mouth') or hero)
    out = hero == mouth or not narrow(dungeon, *hero)
    if m._adjacent_to(player):
        if out:
            band = getattr(dungeon, 'band', None)
            if isinstance(band, dict) and not band.get('feint_sprung'):
                band['feint_sprung'] = True
                say(m, 'feint_sprung', dungeon, colour='danger')
            d['_tm_surprise'] = True
            d.pop('_tm_feint', None)
            return True
        return None                              # he came at it in the narrow way: it fights
    occ = packs._occupied(m, all_monsters, extra_occupied, player)
    hides = [tuple(t) for t in (f.get('hides') or ()) if tuple(t) not in occ or tuple(t) == (m.x, m.y)]
    if (m.x, m.y) in hides:
        return False
    if hides:
        paths = packs.bfs((m.x, m.y), packs._ok_fn(dungeon), occ, hides, 8, 200)
        if paths:
            best = min(sorted(paths), key=lambda t: len(paths[t]))
            if packs._step_along(m, list(paths[best]), occ, player, dungeon, 1):
                return False
    return False


def blind_turn(m, player, dungeon, all_monsters, extra_occupied) -> None:
    """A turn out of the hero's sight while it keeps a post (senses.notice):
    it counts against its patience; a feint's waiter still goes to its
    hiding place beside the mouth (where it means to be, not where he is);
    everyone else stands."""
    _waited(m)
    f = m.__dict__.get('_tm_feint')
    if not isinstance(f, dict):
        return
    left = int(f.get('left', 0) or 0) - 1
    if left <= 0:
        m.__dict__.pop('_tm_feint', None)
        return
    m._tm_feint = dict(f, left=left)
    import packs
    occ = packs._occupied(m, all_monsters, extra_occupied, player)
    hides = [tuple(t) for t in (f.get('hides') or ()) if tuple(t) not in occ]
    if not hides or (m.x, m.y) in [tuple(t) for t in f.get('hides') or ()]:
        return
    paths = packs.bfs((m.x, m.y), packs._ok_fn(dungeon), occ, hides, 8, 200)
    if paths:
        best = min(sorted(paths), key=lambda t: len(paths[t]))
        packs._step_along(m, list(paths[best]), occ, player, dungeon, 1)


def hit_shift(m) -> int:
    """To-hit the feint's waiting blow gains (ai_blow.to_hit_shift: lower is
    easier), once."""
    if m.__dict__.pop('_tm_surprise', None):
        return -int((tactics.data().get('feint') or {}).get('hit_bonus', 2))
    return 0


def focus_of(m):
    """The id of the pet it chose to strike this turn (the swipe pass gives
    that pet its whole blow), or None: a choice from an earlier turn, or one
    made before it fell into a pit, was held, broke or ran, is no choice
    now."""
    f = getattr(m, '__dict__', {}).get('_focus')
    if not isinstance(f, tuple) or len(f) != 2 or f[1] != TURN.n:
        return None
    if not getattr(m, 'alive', False) or broken(m) or any(_has(m, e) for e in CANNOT):
        return None
    return f[0]


# ---------------------------------------------------------------------------
# What the hero is told of a mind
# ---------------------------------------------------------------------------

class _Kind:
    def __init__(self, kind):
        self.kind = str(kind or '')


def bestiary_lines(kind) -> list:
    """The Bestiary's lines for a kind the hero knows: its mind in one plain
    sentence, then its ways (the dark edge, its snares)."""
    k = _Kind(kind)
    mind = mind_of(k)
    out = []
    if mind:
        line = tactics.spec(mind).get('bestiary')
        if line:
            out.append(line)
    flags = tactics.data().get('flags') or {}
    for name in ('dark_edge', 'knows_traps'):
        if mind and flag(k, name) and flags.get(name):
            out.append(flags[name])
    # Every archer finds a lane (src/lanes.py), mind or none.
    import kind_data
    kd = kind_data.kind_def(k)
    if kd.get('ai_pattern') == 'ranged' and flags.get('archer'):
        import wards
        if any(wards.is_missile(a) for a in kd.get('attacks') or () if isinstance(a, dict)):
            out.append(flags['archer'])
    # Into Cover: a thinking kind that fights hand to hand, shot at.
    import under_fire
    cover = (tactics.data().get('under_fire') or {}).get('bestiary', '')
    if (mind and cover and tactics.cover_weight(mind) > 0 and kd.get('ai_pattern') == 'aggressive'
            and not under_fire.rusher(k)):
        out.append(cover)
    return out


def tell_keys(m) -> list:
    """Its tells (data/tells.json): its mind, the dark edge, its snares, a
    band leader's orders."""
    mind = mind_of(m)
    if not mind or excluded(m):
        return []
    keys = [f'mind_{mind}']
    if flag(m, 'dark_edge'):
        keys.append('dark_edge')
    if flag(m, 'knows_traps'):
        keys.append('knows_traps')
    if getattr(m, '__dict__', {}).get('_band_role') == 'leader':
        keys.append('band_orders')
    return keys
