"""Auras: what a creature does to the hero by standing near him (monster
behaviour, third wave: AI-3, auras, 2026-11-20).

A kind with ``aura`` (data/monsters.json, on the kind):

    {"kind": "fear" | "stench" | "heat" | "cold", "radius": 1-3,
     fear:   "turns", "save_dc"?                  (a WIS save, the feared rules)
     stench: "effect", "chance", "turns", "save_dc"?   (a CON check first)
     heat / cold: "share", "type"?                (of the hero's own health a turn)
     "line", "steady_line"?}

* Dread (the dullahan, a death knight, a lich, the old dragons): the
  first time the hero SEES it within its radius in a fight, a WIS save
  against fear (apply_debuff_with_save: the cap, the grace, the family
  wards). Saved or not, he is steady against that creature for the fight;
  it rolls again only after it has lost him a while (OPENER_RESET_TURNS).
* Stench (the ghast, the mapinguari, the upas tree): each turn he stands
  in the reek, until he once masters his stomach (a CON check: then he is
  used to it for the fight), its effect may take him. It needs no sight.
* Heat and cold (the fire and frost elementals, the fire and frost giants):
  each turn he ends within the radius, a share of his own health as fire
  or cold. A fire or cold resistance halves it, a fire or cold shield turns
  it, a family ward against the kind's damage lessens it. Several at once
  burn at most twice the strongest.

Only the hero feels an aura in this pass (not pets, not escorts). Named
foes keep their own fights. A sleeping creature burns and stinks still,
but fills no one with dread. Pure module: the Game pulses it once a world
turn before the monsters act (game_monster_ways.py); the simulator runs
the same pulse (tools/balance/sim_ai3.py).
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_aura knob
AURA_KINDS = ('fear', 'stench', 'heat', 'cold')


def rules() -> dict:
    return kind_data.rules('auras')


def spec(m) -> dict | None:
    a = kind_data.field(m, 'aura', None)
    if isinstance(a, dict) and a.get('kind') in AURA_KINDS:
        return a
    return None


def _ruled(m) -> bool:
    return bool(getattr(m, 'alive', False) and not kind_data.named(m)
                and not kind_data.outside_rules(m))


def distance(m, player) -> int:
    """Its nearest tile to the hero (a big creature's whole body counts)."""
    try:
        from geom import occupied_tiles
        tiles = list(occupied_tiles(m))
    except ImportError:
        tiles = [(m.x, m.y)]
    return min(max(abs(tx - player.x), abs(ty - player.y)) for tx, ty in tiles)


def in_reach(m, player) -> bool:
    a = spec(m)
    return a is not None and distance(m, player) <= max(1, min(3, int(a.get('radius', 1) or 1)))


def _dc(m, a) -> int:
    return min(18, int(a.get('save_dc', 12 + int(getattr(m, 'min_level', 1) or 1) // 7)))


def _rearm(m) -> None:
    """A creature that has lost the hero a while rolls its dread again (the
    fight is over: monster.OPENER_RESET_TURNS)."""
    try:
        from monster import OPENER_RESET_TURNS
    except ImportError:
        OPENER_RESET_TURNS = 5
    if int(m.__dict__.get('_lost_turns', 0) or 0) >= OPENER_RESET_TURNS:
        m.__dict__.pop('_aura_rolled', None)
        m.__dict__.pop('_aura_steady', None)


def _open_air(m, player, dungeon) -> bool:
    """Heat and cold reach through open air only: a clear line from one of
    its tiles to him (never through a wall or a shut door)."""
    if dungeon is None:
        return True
    import senses
    try:
        from geom import occupied_tiles
        tiles = list(occupied_tiles(m))
    except ImportError:
        tiles = [(m.x, m.y)]
    return any(max(abs(tx - player.x), abs(ty - player.y)) <= 1
               or senses.clear_view(tx, ty, player.x, player.y, dungeon) for tx, ty in tiles)


def _smell_reaches(m, player, dungeon, radius: int) -> bool:
    """A reek carries through open ground, round a corner if need be, never
    through rock: a walk of at most radius + 1 steps over open tiles."""
    if dungeon is None:
        return True
    from collections import deque
    goal = (player.x, player.y)
    start = (m.x, m.y)
    seen = {start}
    q = deque([(start, 0)])
    limit = radius + 1
    while q:
        (cx, cy), d = q.popleft()
        if (cx, cy) == goal or max(abs(cx - goal[0]), abs(cy - goal[1])) == 0:
            return True
        if d >= limit:
            continue
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                nxt = (cx + ox, cy + oy)
                if nxt in seen or not dungeon.in_bounds(*nxt):
                    continue
                seen.add(nxt)
                if nxt == goal or dungeon.is_walkable(*nxt):
                    q.append((nxt, d + 1))
    return False


def _said(m, a, key: str, seen: bool, **kw) -> str:
    """Its line if the hero can see it, else a plain line that names no one."""
    lines = rules().get('lines') or {}
    if seen:
        return ai_lines.fill(m, a.get('line') if key == a['kind'] and a.get('line') else
                             (a.get('steady_line') if key.endswith('_steady') and a.get('steady_line')
                              else lines.get(key, '')), **kw)
    return ai_lines.fill(None, (rules().get('unseen') or {}).get(key, ''), **kw)


def pulse(monsters, player, sees=None, rng=random, dungeon=None) -> list:
    """One world turn of every aura on the hero. ``sees(m)`` says whether he
    can see the creature (the Game's own test; None: he sees all, the
    simulator's melee); ``dungeon`` the floor (None in the simulator: no
    walls). Applies what lands; returns [(line, colour)].

    Reach by lore: dread needs sight and a waking creature; heat and cold
    open air (a clear line, never through a wall); a stench smell (round a
    corner, never through rock). A sleeping creature still burns, freezes and
    stinks (it is its body), but fills no one with dread. Nothing outside a
    creature that has swallowed the hero reaches him (holds.shields). A
    creature he cannot see is never named."""
    if not ENABLED or player is None or getattr(player, 'hp', 0) <= 0:
        return []
    import holds
    out = []
    burn = {}                              # type -> [damage of each aura]
    for m in monsters or ():
        a = spec(m)
        if a is None or not _ruled(m):
            continue
        _rearm(m)
        if not in_reach(m, player) or holds.shields(player, m):
            continue
        k = a['kind']
        seen = sees is None or bool(sees(m))
        if k in ('heat', 'cold') and not _open_air(m, player, dungeon):
            continue
        if k == 'stench' and not _smell_reaches(
                m, player, dungeon, max(1, min(3, int(a.get('radius', 1) or 1)))):
            continue
        if k == 'fear':
            if m.has_effect('sleeping') or not getattr(m, '_aware', True):
                continue
            if m.__dict__.get('_aura_rolled'):
                continue
            if sees is not None and not sees(m):
                continue
            m._aura_rolled = True
            out.extend(_dread(m, a, player))
        elif k == 'stench':
            out.extend(_stench(m, a, player, rng, seen))
        else:
            share = max(0.0, min(0.08, float(a.get('share', 0.02) or 0.02)))
            from floor_curve import wound
            dmg = wound(share, int(getattr(player, 'max_hp', 1) or 1))
            try:
                import wards
                dmg = max(1, int(round(dmg * wards.damage_mult(player, m))))
            except (ImportError, AttributeError):
                pass
            dtype = str(a.get('type') or ('fire' if k == 'heat' else 'cold'))
            burn.setdefault(dtype, []).append((dmg, m, a, seen))
    for dtype, hits in burn.items():
        cap = 2 * max(h[0] for h in hits)
        total = min(cap, sum(h[0] for h in hits))
        got = player.take_damage(total, dtype)
        _d, m, a, seen = max(hits, key=lambda h: h[0])
        counts = dict(m.__dict__.get('_aura_hits') or {})
        counts[a['kind']] = counts.get(a['kind'], 0) + 1
        m._aura_hits = counts
        if got > 0:
            out.append((_said(m, a, a['kind'], seen, damage=got), 'danger'))
    return out


def _dread(m, a, player) -> list:
    from status_effects import apply_debuff_with_save
    turns = max(1, int(a.get('turns', 3) or 3))
    applied, text = apply_debuff_with_save(player, 'feared', turns, _dc(m, a), source=m)
    counts = dict(m.__dict__.get('_aura_hits') or {})
    counts['fear_rolled'] = counts.get('fear_rolled', 0) + 1
    if applied:
        counts['fear'] = counts.get('fear', 0) + 1
    m._aura_hits = counts
    if applied:
        line = a.get('line') or (rules().get('lines') or {}).get('fear', '')
        return [(ai_lines.fill(m, line), 'danger')]
    steady = a.get('steady_line') or (rules().get('lines') or {}).get('fear_steady', '')
    return [(ai_lines.fill(m, steady), 'info')] if steady else ([(text, 'info')] if text else [])


def _stench(m, a, player, rng, seen: bool = True) -> list:
    if m.__dict__.get('_aura_steady'):
        return []
    eff = str(a.get('effect') or 'weakened')
    if int((getattr(player, 'status_effects', None) or {}).get(eff, 0) or 0) != 0:
        return []                          # it has him already
    if rng.random() >= float(a.get('chance', 1.0) or 0.0):
        return []
    mod = (int(getattr(player, 'CON', 10) or 10) - 10) // 2
    try:
        bonus = int(player.save_bonus_for('CON'))
    except (AttributeError, TypeError):
        bonus = 0
    counts = dict(m.__dict__.get('_aura_hits') or {})
    if rng.randint(1, 20) + mod + bonus >= _dc(m, a):
        m._aura_steady = True
        counts['stench_steady'] = counts.get('stench_steady', 0) + 1
        m._aura_hits = counts
        steady = _said(m, a, 'stench_steady', seen)
        return [(steady, 'info')] if steady else []
    from status_effects import apply_debuff_with_save
    applied, text = apply_debuff_with_save(player, eff, max(1, int(a.get('turns', 3) or 3)),
                                           _dc(m, a), source=m)
    if not applied:
        return [(text, 'info')] if text else []
    counts['stench'] = counts.get('stench', 0) + 1
    m._aura_hits = counts
    return [(_said(m, a, 'stench', seen) + (' ' + text if text else ''), 'danger')]


def tell_keys(m) -> list:
    a = spec(m)
    return ['aura_' + a['kind']] if a else []
