"""War-bands: groups that fight like a unit (Dungeon Alive slice 5, C1).

Brandon: monsters must "pose a real challenge and players need to pay
attention to lore, weaknesses, abilities". A floor used to be a random
sample: fourteen unrelated kinds, one to a room, none with a job. A band
makes camp in one room (data/war_bands.json):

* **A leader.** While he lives his followers hold their nerve, and when any
  one of the band spots the hero the whole band is roused.
* **Guards** keep beside him. **Shooters** keep their distance. **Casters**
  hang back. **Healers** finally have someone to mend.
* **Morale.** When the leader falls the band breaks its own way:
  - a goblin war-band routs;
  - a necromancer's dead crumble;
  - devils turn on one another.
  When half the band is down, the rest may flee. A great maths chain on
  the leader can break their nerve before he falls.
* **Knowing pays.** A hero who knows the leader's family hears the band's
  make-up on arrival.

Only kinds the floor's own spawn pool allows are used, so a band is never
out of its depth (LORE, NOT FLOOR). Pure module: no pygame, no Game.
"""
from __future__ import annotations

import json
import random

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'war_bands.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


ROLES = ('guard', 'shooter', 'caster', 'healer')


def pick_band(level: int, pool: dict, rng):
    """(band id, {'leader': kind, role: [kinds]}) for a band that can live on
    this floor, or None."""
    d = data()
    fits = []
    for bid, b in d['bands'].items():
        lo, hi = b['floors']
        if not lo <= level <= hi:
            continue
        leaders = [k for k in b['leader'] if k in pool]
        guards = [k for k in b.get('guard', ()) if k in pool]
        if leaders and guards:
            fits.append(bid)
    if not fits:
        return None
    bid = rng.choice(fits)
    b = d['bands'][bid]
    roster = {'leader': rng.choice([k for k in b['leader'] if k in pool])}
    for role in ROLES:
        kinds = [k for k in b.get(role, ()) if k in pool]
        lo, hi = (b.get('counts') or {}).get(role, [0, 0])
        n = rng.randint(int(lo), int(hi)) if kinds else 0
        roster[role] = [rng.choice(kinds) for _ in range(n)]
    return bid, roster


def _protected(m) -> bool:
    """A creature a band may never displace: a named foe, a seal demon, a
    mini-boss or legend, a person of an encounter, anything the run needs."""
    try:
        if m._is_named_foe():
            return True
    except Exception:
        pass
    return bool(getattr(m, 'is_seal_demon', False) or getattr(m, 'is_mini_boss', False)
                or 'legendary' in (getattr(m, 'tags', None) or ())
                or getattr(m, 'is_allied', False)
                or getattr(m, '_npc_encounter_tag', None)
                or getattr(m, '_flavor_encounter_tag', None)
                or getattr(m, '_is_unicorn', False) or getattr(m, '_is_abandoned_emberpup', False))


def _band_room(dungeon, rng, monsters=()):
    special = dungeon.__dict__.get('special_rooms') or {}
    first = dungeon.rooms[0] if dungeon.rooms else None

    def holds_protected(r):
        return any(_protected(m) and r.x <= m.x < r.x + r.width and r.y <= m.y < r.y + r.height
                   for m in monsters or ())
    rooms = [r for r in dungeon.rooms
             if r is not first and tuple(r.center) not in special
             and (r.width - 2) * (r.height - 2) >= 30 and not holds_protected(r)]
    if not rooms:
        return None
    rooms.sort(key=lambda r: -(r.width * r.height))
    return rng.choice(rooms[:max(1, len(rooms) // 2)])


def place_band(dungeon, monsters: list, level: int, rng=None) -> list:
    """Maybe set a war-band down on this floor. Returns its members (already
    added to ``monsters``)."""
    rng = rng or random.Random()
    d = data()
    if level < int(d.get('first_floor', 3)) or rng.random() >= float(d.get('chance', 0.4)):
        return []
    from dungeon import _floor_pool
    from monster import Monster
    pool = _floor_pool(level, dungeon)
    picked = pick_band(level, pool, rng)
    if not picked:
        return []
    bid, roster = picked
    room = _band_room(dungeon, rng, monsters)
    if room is None:
        return []

    def inside(m):
        return room.x <= m.x < room.x + room.width and room.y <= m.y < room.y + room.height

    # The band takes the room: whatever the ordinary roll put there goes
    # (never a named foe or anything the run needs: _protected).
    monsters[:] = [m for m in monsters if not inside(m) or _protected(m)]
    taken = {(m.x, m.y) for m in monsters}
    tiles = [(x, y) for y in range(room.y + 1, room.y + room.height - 1)
             for x in range(room.x + 1, room.x + room.width - 1)
             if dungeon.is_walkable(x, y) and (x, y) not in taken]
    if len(tiles) < 6:
        return []
    cx, cy = room.center
    tiles.sort(key=lambda t: max(abs(t[0] - cx), abs(t[1] - cy)))
    uid = f'{bid}@{room.x},{room.y}'
    members = []

    def put(kind, role, near_center):
        if not tiles:
            return None
        spot = tiles.pop(0) if near_center else tiles.pop(rng.randrange(len(tiles)))
        defn = {**pool[kind], 'id': kind}
        if tuple(defn.get('footprint', [1, 1])) != (1, 1):
            return None
        m = Monster(defn, spot[0], spot[1])
        m._band = uid
        m._band_id = bid
        m._band_role = role
        members.append(m)
        return m

    leader = put(roster['leader'], 'leader', True)
    if leader is None:
        return []
    for role in ROLES:
        for kind in roster.get(role, ()):
            m = put(kind, role, role in ('guard', 'healer'))
            if m is not None:
                m._band_leader = leader
    # A sentry keeps watch by the fire; the rest sleep, or all stand guard.
    sleeping = rng.random() < 0.5
    lo, hi = 300, 700
    for i, m in enumerate(members):
        m._home = (m.x, m.y)
        m._job_fixed = True
        if sleeping and i > 1:
            m._job = 'sleep'
            # Its own rest (see senses.py's idle sleep): not a spell, so the
            # dead's status_immune to sleep does not keep a band awake.
            m.status_effects['sleeping'] = max(int(m.status_effects.get('sleeping', 0) or 0),
                                               rng.randint(lo, hi))
        else:
            m._job = 'guard'
    monsters.extend(members)
    dungeon.band = {'id': bid, 'uid': uid, 'leader_kind': roster['leader'],
                    'room': (room.x, room.y, room.width, room.height),
                    'counts': {r: len(roster.get(r, ())) for r in ROLES},
                    'said': False}
    return members


def roster_text(band: dict) -> str:
    d = data()
    names = d.get('role_names', {})
    parts = [names.get('leader', 'a leader')]
    for role in ROLES:
        n = int((band.get('counts') or {}).get(role, 0))
        if n:
            word = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five'}.get(n, str(n))
            parts.append(names.get(role, '{n}').replace('{n}', word))
    if len(parts) == 1:
        text = parts[0]
    else:
        text = ', '.join(parts[:-1]) + ' and ' + parts[-1]
    return text[:1].upper() + text[1:]


def arrival_line(band: dict, knows_family: bool) -> str:
    """The band heard on arrival; named in full, with how to break it, only
    for a hero who knows the leader's kind (family_lore.knowledge KNOWN)."""
    b = data()['bands'].get(band.get('id', ''), {})
    if knows_family and b.get('known_line'):
        return b['known_line'].replace('{roster}', roster_text(band))
    return b.get('line', '')


def observe_line(b: dict, role: str, knows: bool, m=None) -> str:
    """What Observe says of band member ``m`` (data/war_bands.json
    'observe'), in his own pronoun. Anyone can see who the others watch;
    what happens when he falls is for a hero who knows the leader's kind."""
    from monster import fill
    o = data().get('observe') or {}
    if role != 'leader':
        return fill(m, o.get('member', ''), name=b.get('name', 'a band'))
    if not knows:
        return fill(m, o.get('leader', ''))
    morale = (o.get('morale') or {}).get(b.get('morale', 'rout'), '')
    return fill(m, ' '.join(p for p in (o.get('leader_known', ''), morale) if p))


def members_of(monsters, uid: str) -> list:
    return [m for m in monsters or () if getattr(m, '_band', None) == uid]


def leader_of(monsters, uid: str):
    return next((m for m in members_of(monsters, uid)
                 if getattr(m, '_band_role', '') == 'leader'), None)


def alarm(m, all_monsters, x: int, y: int) -> int:
    """One of the band has spotted the hero: rouse the rest to the place."""
    uid = getattr(m, '_band', None)
    if not uid:
        return 0
    import senses
    n = 0
    for o in members_of(all_monsters, uid):
        if o is m or not o.alive or o.__dict__.get('_tracking'):
            continue
        senses.rouse(o, x, y)
        n += 1
    return n


def on_death(monsters, dead) -> dict:
    """What the band does when ``dead`` falls: {'line', 'effect', 'fall':
    [members who fall with him]}. Applies fear or quarrel itself."""
    uid = getattr(dead, '_band', None)
    out = {'line': '', 'effect': '', 'fall': []}
    if not uid:
        return out
    d = data()
    b = d['bands'].get(getattr(dead, '_band_id', ''), {})
    alive = [m for m in members_of(monsters, uid) if m.alive and m is not dead]
    if getattr(dead, '_band_role', '') == 'leader':
        effect = b.get('morale', 'rout')
        out['effect'] = effect
        out['line'] = b.get('rout_line', '')
        for m in alive:
            m._band_leader = None
            if effect == 'crumble':
                if getattr(m, 'family', '') == 'restless_dead':
                    out['fall'].append(m)
                else:
                    _frighten(m, 10)
            elif effect == 'quarrel':
                m.quarrelsome = True
                m.add_effect('confused', 8)
            else:
                _frighten(m, 12)
        return out
    # Half the band down: some of the rest lose heart, leader or no.
    total = len(members_of(monsters, uid))
    if total and len(alive) * 2 <= total and not getattr(dead, '_band_halved', False):
        p = float(d.get('half_down_flee', 0.5))
        for m in alive:
            m._band_halved = True
            if getattr(m, '_band_role', '') != 'leader' and random.random() < p:
                _frighten(m, 8)
    return out


def on_great_blow(monsters, leader, chain: int) -> str:
    """A chain of ``nerve_chain`` or more on a band's living leader shakes
    the followers who see it: about half of them falter. Returns the line."""
    d = data()
    if (not getattr(leader, '_band', None) or getattr(leader, '_band_role', '') != 'leader'
            or not leader.alive or int(chain) < int(d.get('nerve_chain', 6))):
        return ''
    b = d['bands'].get(getattr(leader, '_band_id', ''), {})
    shaken = 0
    for m in members_of(monsters, leader._band):
        if m is leader or not m.alive:
            continue
        if random.random() < 0.5:
            _frighten(m, 4)
            shaken += 1
    return b.get('break_line', '') if shaken else ''


def _frighten(m, turns: int) -> None:
    if getattr(m, 'fearless', False):
        return
    try:
        if m.resists_control('feared'):
            return
    except Exception:
        pass
    m.add_effect('feared', turns)


def holds_nerve(m) -> bool:
    """A follower whose leader still lives does not run when hurt."""
    lead = getattr(m, '_band_leader', None)
    return lead is not None and getattr(lead, 'alive', False)
