"""Domain hazards and kin (Dungeon Alive slice 3, 2026-11-12).

Brandon: a domain's look "can BOTH be decorative AND also introduce unique
hazards or traps (or make a certain type more common)".

* **Hazards** (data/hazards.json) are fixtures that do something, and you can
  see them first. Each domain has its own:
  - the Forgotten Temple: crumbling floors, strangling vines;
  - the Scorched Deep: fire vents that breathe on a beat and glow the turn
    before;
  - the Rime Halls: thin ice that a heavy pack goes through, icicles;
  - the Abyss: brimstone, sigils that drink magic.

  Observe tells what each does. They catch monsters too, so a hero who reads
  them can lead a hunter across the ice.
* **Traps**: the hidden traps lean to the domain's kinds (a temple's pits, the
  deep's fire).
* **Kin**: each domain's families weigh more in the spawn pool. This is a
  weight from lore, never the floor number, and every kind is still eligible
  only from its own depth (LORE, NOT FLOOR).
* **Clans**: most floors are held by one family, which weighs more again and
  is named on arrival. So the hero knows which family to read up on.

The damage dice are written against a 60-point health bar and taken as that
share of the victim's own health (floor_curve). Pure module: no pygame, no
Game.
"""
from __future__ import annotations

import json
import random

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'hazards.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def hazard_def(fid: str) -> dict:
    return data()['hazards'].get(fid or '') or {}


def hazard_at(dungeon, x: int, y: int):
    """(fixture id, hazard def) if a live hazard lies on (x, y), else None."""
    import decor
    fid = decor.fixture_at(dungeon, x, y)
    if not fid:
        return None
    h = hazard_def(fid)
    if not h:
        return None
    if (dungeon.__dict__.get('fixture_state') or {}).get((x, y)) == 'spent':
        return None
    return fid, h


# ---------------------------------------------------------------------------
# Kin, clans, traps
# ---------------------------------------------------------------------------

def kin_weight(level: int, family: str) -> float:
    """How much more a family weighs in the spawn pool of this floor's
    domain (its kin). The floor's own clan is laid on top by
    dungeon._floor_pool."""
    import decor
    dom = decor.domain_for(level)
    if not dom:
        return 1.0
    return float((dom.get('kin') or {}).get(family or '', 1.0))


def pick_clan(level: int, eligible: dict, rng=None):
    """The family that holds this floor, or None. ``eligible`` is the spawn
    pool before weighting ({kind: def})."""
    import decor
    rng = rng or random.Random()
    cfg = decor.config().get('clans') or {}
    if rng.random() >= float(cfg.get('chance', 0.6)):
        return None
    never = set(cfg.get('never', ()))
    counts: dict = {}
    for v in eligible.values():
        fam = v.get('family')
        if fam and fam not in never and not v.get('is_mini_boss') and not v.get('is_boss'):
            counts[fam] = counts.get(fam, 0) + 1
    fams = [f for f, n in counts.items() if n >= int(cfg.get('min_kinds', 4))]
    if not fams:
        return None
    dom = decor.domain_for(level) or {}
    kin = dom.get('kin') or {}
    weights = [float(kin.get(f, 1.0)) * counts[f] for f in fams]
    roll = rng.random() * sum(weights)
    for f, w in zip(fams, weights):
        roll -= w
        if roll <= 0:
            return f
    return fams[-1]


def clan_line(family: str) -> str:
    import decor
    return (decor.config().get('clan_lines') or {}).get(family or '', '')


def pick_trap(level: int, trap_types: list, rng) -> dict:
    """One hidden trap, the domain's own kinds weighing more."""
    import decor
    dom = decor.domain_for(level) or {}
    w = dom.get('traps') or {}
    weights = [float(w.get(t['type'], 1.0)) for t in trap_types]
    roll = rng.random() * sum(weights)
    for t, wt in zip(trap_types, weights):
        roll -= wt
        if roll <= 0:
            return t
    return trap_types[-1]


# ---------------------------------------------------------------------------
# Placing a domain's hazards
# ---------------------------------------------------------------------------

def place_hazards(dungeon, level: int, taken: set, rooms: list, corridors: list, rng) -> int:
    """Set the domain's hazards (domains.json 'hazards'). ``taken`` holds the
    tiles that must stay clear; ``rooms`` the rooms that may hold them (never
    the arrival room); ``corridors`` the corridor tiles. Returns how many."""
    import decor
    dom = decor.domain_for(level) or {}
    n = 0
    for spec in dom.get('hazards') or ():
        fid = spec['id']
        where = spec.get('where', 'room')
        if where == 'room':
            lo, hi = spec.get('rooms', [1, 1])
            pool = [r for r in rooms if len(decor._inner(r, dungeon)) >= 9]
            rng.shuffle(pool)
            for room in pool[:rng.randint(int(lo), int(hi))]:
                inner = [t for t in decor._inner(room, dungeon) if t not in taken]
                if not inner:
                    continue
                plo, phi = spec.get('patch', [1, 1])
                size = rng.randint(int(plo), int(phi))
                patch = [rng.choice(inner)]
                inner_set = set(inner)
                while len(patch) < size:
                    x, y = rng.choice(patch)
                    nxt = (x + rng.choice((-1, 0, 1)), y + rng.choice((-1, 0, 1)))
                    if nxt in inner_set and nxt not in patch:
                        patch.append(nxt)
                    elif rng.random() < 0.1:
                        break
                for pos in patch:
                    decor.place(dungeon, pos, fid)
                    taken.add(pos)
                    n += 1
        elif where in ('corridor', 'anywhere', 'under_wall'):
            if where == 'corridor':
                pool = [t for t in corridors if t not in taken]
            elif where == 'under_wall':
                from dungeon import WALL
                pool = []
                for room in rooms:
                    for (x, y) in decor._inner(room, dungeon):
                        if (x, y) in taken:
                            continue
                        if any(dungeon.tiles[y + oy][x + ox] == WALL
                               for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                            pool.append((x, y))
            else:
                pool = [t for t in corridors if t not in taken]
                for room in rooms:
                    pool += [t for t in decor._inner(room, dungeon) if t not in taken]
            rng.shuffle(pool)
            lo, hi = spec.get('count', [1, 1])
            for pos in pool[:rng.randint(int(lo), int(hi))]:
                decor.place(dungeon, pos, fid)
                taken.add(pos)
                if hazard_def(fid).get('trigger') == 'cycle':
                    period = int(hazard_def(fid).get('period', 6))
                    dungeon.__dict__.setdefault('hazard_phase', {})[pos] = rng.randrange(period)
                n += 1
        if hazard_def(fid).get('trigger') == 'cycle':
            # Patches placed in rooms breathe together.
            period = int(hazard_def(fid).get('period', 6))
            phases = dungeon.__dict__.setdefault('hazard_phase', {})
            beat = rng.randrange(period)
            for pos, f in decor.fixtures_of(dungeon).items():
                if f == fid and pos not in phases:
                    phases[pos] = beat
    return n


# ---------------------------------------------------------------------------
# What a hazard does
# ---------------------------------------------------------------------------

_SIZES: dict | None = None


def _sizes() -> dict:
    global _SIZES
    if _SIZES is None:
        try:
            from paths import data_path
            with open(data_path('data', 'monster_sizes.json'), encoding='utf-8') as f:
                _SIZES = json.load(f)
        except (OSError, ValueError):
            _SIZES = {}
    return _SIZES


def is_heavy(m) -> bool:
    """A large or huge creature (data/monster_sizes.json) weighs like a hero
    with a full pack on thin ice and cracked floors."""
    s = _sizes()
    table = s.get('sizes', s) if isinstance(s, dict) else {}
    size = table.get(getattr(m, 'kind', ''), '') if isinstance(table, dict) else ''
    if isinstance(size, dict):
        size = size.get('size', '')
    if tuple(getattr(m, 'footprint', (1, 1)) or (1, 1)) != (1, 1):
        return True
    return str(size).lower() in ('large', 'huge', 'gargantuan')


_FLOATING_FAMILIES = ('ghosts', 'birds')
_FLOATING_KINDS = ('bat', 'camazotz', 'will_o_wisp', 'will_o_wisp_lesser', 'floating_eye',
                   'beholder', 'elder_beholder', 'beholder_spawn', 'stirge_swarm', 'giant_wasp',
                   'pixie_swarm', 'imp', 'quasit', 'air_elemental', 'storm_elemental',
                   'geryon')     # Dante's Geryon swims down through the air of Hell


def floats(m) -> bool:
    """A creature that does not walk the floor: it flies, floats or haunts."""
    return bool((getattr(m, 'family', '') or '') in _FLOATING_FAMILIES
                or getattr(m, 'kind', '') in _FLOATING_KINDS
                or m.has_effect('levitating'))


def step_fires(h: dict, *, heavy: bool, levitating: bool, rng) -> bool:
    """Whether a step hazard goes off for whoever stepped on it."""
    if h.get('trigger') != 'step':
        return False
    if levitating and h.get('levitate', True):
        return False
    chance = float(h.get('heavy', h.get('chance', 1.0)) if heavy else h.get('chance', 1.0))
    return rng.random() < chance


def cycle_phase(dungeon, pos, turn: int):
    """'fire' on the beat, 'warn' the turn before, else None."""
    import decor
    fid = decor.fixture_at(dungeon, *pos)
    h = hazard_def(fid)
    if h.get('trigger') != 'cycle':
        return None
    period = int(h.get('period', 6))
    phase = int((dungeon.__dict__.get('hazard_phase') or {}).get(pos, 0))
    k = (int(turn) - phase) % period
    if k == 0:
        return 'fire'
    if k == period - 1:
        return 'warn'
    return None


def cycle_hazards(dungeon) -> list:
    import decor
    return [pos for pos, fid in decor.fixtures_of(dungeon).items()
            if hazard_def(fid).get('trigger') == 'cycle']


def spend(dungeon, pos, h: dict) -> None:
    """A once-only hazard has gone off: leave what it leaves behind."""
    import decor
    if not h.get('once'):
        return
    after = h.get('after', '')
    decor.remove(dungeon, pos)
    if after:
        decor.place(dungeon, pos, after)
