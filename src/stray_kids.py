"""The Stray Kids easter egg (Brandon, 2026-11-13): "my kids love this
stupid kpop band called Stray Kids." Every run, on one floor from 8 to 12, a
gold shrine to the band stands in a room. Touch it and the hero is taken to
the Zombie Stage, a side floor like the Cow Level, where the eight members
dance as zombies; the last to fall leaves a signed photo that calls the band,
alive, for one short show.

This module is the pure half (no pygame, no Game):

* the run's roll: which floor holds the idol (``new_run_state``);
* the dance: the band moves as one formation. Its anchor closes on the hero
  and stops ``keep_off`` tiles short; every member walks to his place in the
  current shape, turned to face the hero; the shape changes every
  ``beats_per_shape`` beats, and a member strikes only on the downbeat
  (every ``strike_every`` beats). Before any of them has seen the hero they
  rehearse in place. A member who is held, frightened, confused or blinded
  drops out of the dance and acts as any monster would (Monster.take_turn),
  so every status still works on them;
* ``ZombieMember``: one zombie band member. No corpse (``_no_corpse``),
  an Observe line of his own, a quip after a blow that lands (the attack's
  ``quip`` in data/monsters.json), and Lee Know's cat;
* ``StarDancer``: one living member called up by the photo: an ally that
  takes and deals no harm and dances round the hero;
* ``build_stage``: the Zombie Stage itself (boss_levels.STRAY_KIDS_STAGE).

The game half (the idol, the trip there and back, the beat, the shouts, the
photo, the show) is game_stray_kids.StrayKidsMixin. Every line of text and
every number is in data/stray_kids.json; the members' fighting numbers in
data/monsters.json; the band's leader and morale in data/war_bands.json.
No real lyrics anywhere: the lines are made up, and songs are named only by
their titles.
"""
from __future__ import annotations

import json
import random

from monster import Monster

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'stray_kids.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def members() -> list:
    """The eight, in their places in the dance (Bang Chan first: he leads)."""
    return list(data()['members'])


def member_name(member: str) -> str:
    return data()['names'][member]


def zombie_kind(member: str) -> str:
    return f'sk_zombie_{member}'


def star_kind(member: str) -> str:
    return f'sk_star_{member}'


def zombie_kinds() -> list:
    return [zombie_kind(m) for m in members()]


def is_zombie(m) -> bool:
    return bool(getattr(m, 'is_sk_zombie', False))


def is_star(m) -> bool:
    return bool(getattr(m, 'is_sk_star', False))


def idol_id() -> str:
    return data()['idol_fixture']


def photo_id() -> str:
    return data()['photo_id']


# ---------------------------------------------------------------------------
# The roll: which floor holds the idol this run
# ---------------------------------------------------------------------------

def roll_floor(rng) -> int | None:
    d = data()
    if rng.random() >= float(d['chance_per_run']):
        return None
    return rng.randint(int(d['first_floor']), int(d['last_floor']))


def roll_for_new_run() -> int | None:
    """roll_floor from its own generator, seeded from the shared stream
    without moving it, so seeded floors and captures are unchanged."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return roll_floor(random.Random(seed ^ 0x5C2018))


def new_run_state() -> dict:
    """``game._stray_kids`` (saved): the idol's floor (None: not this run),
    placed yet and where, whether it has called the hero over, touched yet,
    the floor to go back to, how the stage ended ('cleared' or 'left'), and
    whether the photo has dropped."""
    return {'floor': roll_for_new_run(), 'spawned': False, 'pos': None, 'called': False,
            'touched': False, 'return_floor': 0, 'outcome': None, 'photo_dropped': False}


def old_save_state() -> dict:
    """A save from before the egg: a run without it (its floors may be behind
    the hero already)."""
    return {'floor': None, 'spawned': False, 'pos': None, 'called': False,
            'touched': False, 'return_floor': 0, 'outcome': None, 'photo_dropped': False}


# ---------------------------------------------------------------------------
# The dance
# ---------------------------------------------------------------------------

def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _sign(v) -> int:
    return (v > 0) - (v < 0)


def facing(ax: int, ay: int, hx: int, hy: int) -> tuple:
    """The way the formation faces: toward the hero, along the longer axis."""
    dx, dy = hx - ax, hy - ay
    if dx == 0 and dy == 0:
        return (0, 1)
    if abs(dx) >= abs(dy):
        return (_sign(dx), 0)
    return (0, _sign(dy))


def turn(offset, face) -> tuple:
    """A shape's place, written facing +y (the front row has the larger y),
    turned to face ``face``."""
    dx, dy = int(offset[0]), int(offset[1])
    fx, fy = face
    if (fx, fy) == (0, 1):
        return (dx, dy)
    if (fx, fy) == (0, -1):
        return (-dx, -dy)
    if (fx, fy) == (1, 0):
        return (dy, -dx)
    return (-dy, dx)            # facing -x


def shape_names() -> list:
    return list(data()['dance']['shape_order'])


def new_dance(home: tuple) -> dict:
    """The dance's state, kept on the stage's Dungeon (``sk_dance``): it
    pickles with the floor."""
    return {'anchor': [int(home[0]), int(home[1])], 'home': [int(home[0]), int(home[1])],
            'beat': 0, 'shape': 0, 'aware': False, 'facing': [-1, 0]}


def dance_of(dungeon) -> dict | None:
    d = getattr(dungeon, '__dict__', {}).get('sk_dance')
    return d if isinstance(d, dict) else None


def place_of(dance: dict, slot: int) -> tuple:
    """Where member ``slot`` should stand in the dance's current shape."""
    name = shape_names()[int(dance.get('shape', 0)) % len(shape_names())]
    offs = data()['dance']['shapes'][name]
    dx, dy = turn(offs[slot % len(offs)], tuple(dance.get('facing') or (0, 1)))
    ax, ay = dance['anchor']
    return (ax + dx, ay + dy)


def the_band(monsters) -> list:
    """The band members still standing, in their places' order."""
    return sorted((m for m in monsters or () if is_zombie(m) and getattr(m, 'alive', False)),
                  key=lambda m: int(getattr(m, '_sk_slot', 0)))


def strike_beat(dance: dict) -> bool:
    every = max(1, int(data()['dance']['strike_every']))
    return bool(dance.get('aware')) and int(dance.get('beat', 0)) % every == 0


def advance(dungeon, monsters, hero_xy: tuple, sees) -> list:
    """One beat of the dance, once a turn. ``sees(m)`` says whether band
    member ``m`` can see the hero. Returns what happened, for the game to
    say: ('seen',) the first time any of them sees him, ('shape', name)
    when the shape changes."""
    d = dance_of(dungeon)
    band = the_band(monsters)
    if d is None or not band:
        return []
    cfg = data()['dance']
    out = []
    hx, hy = hero_xy
    if not d.get('aware') and any(sees(m) for m in band):
        d['aware'] = True
        out.append(('seen',))
    d['beat'] = int(d.get('beat', 0)) + 1
    if d['beat'] % max(1, int(cfg['beats_per_shape'])) == 0:
        d['shape'] = (int(d.get('shape', 0)) + 1) % len(shape_names())
        out.append(('shape', shape_names()[d['shape']]))
    ax, ay = d['anchor']
    if d.get('aware'):
        face = facing(ax, ay, hx, hy)
        d['facing'] = list(face)
        keep = int(cfg['keep_off'])
        goal = (hx - face[0] * keep, hy - face[1] * keep)
        if _cheb(ax, ay, *goal) > 0:
            sx, sy = _sign(goal[0] - ax), _sign(goal[1] - ay)
            for nx, ny in ((ax + sx, ay + sy), (ax + sx, ay), (ax, ay + sy)):
                if (nx, ny) != (ax, ay) and dungeon.is_walkable(nx, ny):
                    d['anchor'] = [nx, ny]
                    break
    return out


def _step_toward(m, goal: tuple, dungeon, all_monsters, extra_occupied, player) -> bool:
    """One step that brings ``m`` nearer ``goal`` (never onto anyone, never
    further off). True if it moved."""
    from geom import all_occupied_tiles
    occupied = set(all_occupied_tiles(all_monsters, exclude=m))
    if extra_occupied:
        occupied |= set(extra_occupied)
    if player is not None:
        occupied.add((player.x, player.y))
    gx, gy = goal
    here = (_cheb(m.x, m.y, gx, gy), abs(m.x - gx) + abs(m.y - gy))
    best = None
    for ddx in (-1, 0, 1):
        for ddy in (-1, 0, 1):
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = m.x + ddx, m.y + ddy
            if (nx, ny) in occupied or not m._can_move_to(dungeon, nx, ny):
                continue
            score = (_cheb(nx, ny, gx, gy), abs(nx - gx) + abs(ny - gy))
            if score < here and (best is None or score < best[0]):
                best = (score, nx, ny)
    if best is None:
        return False
    m.x, m.y = best[1], best[2]
    return True


# ---------------------------------------------------------------------------
# The zombie band
# ---------------------------------------------------------------------------

# Statuses that take a member out of the dance: he acts as any monster would.
_HELD = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'stuck_in_pit', 'impaled')
_MIND = ('feared', 'charmed', 'confused', 'blinded')


class ZombieMember(Monster):
    """One of the eight, dead and still dancing."""

    is_sk_zombie = True
    _no_corpse = True               # they disintegrate (game_combat._on_monster_killed)

    def __init__(self, defn: dict, x: int, y: int, member: str = '', slot: int = 0):
        super().__init__(defn, x, y)
        self._sk_member = member or defn['id'].replace('sk_zombie_', '', 1)
        self._sk_slot = int(slot)
        self._sk_events = []        # lines for the game to say (Lee Know's cat)

    @property
    def member(self) -> str:
        return self.__dict__.get('_sk_member', '')

    @property
    def observe_line(self) -> str:
        """What Observe (O) says of him, after the usual lines."""
        d = data()
        own = d['observe'].get(self.member, '')
        return ' '.join(p for p in (own, d['dance']['beat_tell']) if p)

    def _off_the_dance(self) -> bool:
        if any(self.has_effect(e) for e in _HELD) or self._under('immobilized'):
            return True
        return any(self._under(e) for e in _MIND)

    def _reach(self) -> str:
        return 'ranged' if any(a.get('ranged') for a in self.attacks) else 'melee'

    def _in_reach(self, player, dungeon, all_monsters) -> bool:
        if self._adjacent_to(player):
            return True
        if self._reach() != 'ranged':
            return False
        dist = _cheb(self.x, self.y, player.x, player.y)
        return 2 <= dist <= self._RANGED_MAX and self._has_clear_shot(player.x, player.y,
                                                                     dungeon, all_monsters)

    def _distracted(self) -> bool:
        """Lee Know and his cat: now and then the cat matters more than you."""
        dd = (data().get('distracted') or {}).get(self.member)
        if not dd or random.random() >= float(dd.get('chance', 0)):
            return False
        self.__dict__.setdefault('_sk_events', []).append(random.choice(dd['lines']))
        return True

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        self._cached_all_monsters = all_monsters
        if not self.alive:
            return False
        dance = dance_of(dungeon)
        if dance is None or self._off_the_dance():
            return super().take_turn(player, dungeon, all_monsters, extra_occupied)
        if dance.get('aware'):
            self._aware = True
            self._tracking = True
        if strike_beat(dance) and self._in_reach(player, dungeon, all_monsters):
            return not self._distracted()
        _step_toward(self, place_of(dance, self._sk_slot), dungeon, all_monsters,
                     extra_occupied, player)
        return False

    def _resolve_blow(self, atk: dict, player, in_flurry: bool = False):
        dmg, msg = super()._resolve_blow(atk, player, in_flurry)
        quip = atk.get('quip', '')
        if quip and dmg > 0 and msg:
            msg = f"{msg} {quip}"
        return dmg, msg


def make_zombie(member: str, x: int, y: int, slot: int) -> ZombieMember:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    kind = zombie_kind(member)
    return ZombieMember({**defs[kind], 'id': kind}, x, y, member=member, slot=slot)


# ---------------------------------------------------------------------------
# The stars: the band alive, called up by the photo
# ---------------------------------------------------------------------------

class StarDancer(Monster):
    """One of the eight, alive, in a show for the hero: an ally who takes no
    harm, deals none, and dances in a ring round him."""

    is_sk_star = True
    _no_corpse = True

    def __init__(self, member: str, x: int, y: int, slot: int = 0):
        st = data()['stars']
        super().__init__({'id': star_kind(member), 'name': member_name(member),
                          'symbol': st.get('symbol', '@'), 'color': st.get('color', [255, 215, 120]),
                          'hp': '1', 'attacks': [], 'ai_pattern': 'aggressive',
                          'is_allied': True, 'proper_noun': True, 'pronoun': 'he',
                          'lore': data()['observe'].get(member, '')}, x, y)
        self._sk_member = member
        self._sk_slot = int(slot)
        self._sk_beat = 0

    @property
    def member(self) -> str:
        return self.__dict__.get('_sk_member', '')

    def take_damage(self, amount: int, damage_type: str = 'physical',
                    ignore_resistance: bool = False) -> int:
        return 0

    def add_effect(self, name: str, duration: int):
        pass                        # nothing interrupts the show

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """Round and round the hero, two tiles out, one step a beat."""
        ring = data()['stars']['ring']
        self._sk_beat = int(self.__dict__.get('_sk_beat', 0)) + 1
        dx, dy = ring[(self._sk_slot * 2 + self._sk_beat) % len(ring)]
        _step_toward(self, (player.x + dx, player.y + dy), dungeon, all_monsters,
                     extra_occupied, player)
        return False


def near_show(monsters, stars, dungeon) -> list:
    """The creatures near the show: in ``watch_radius`` of a star with a
    clear view of him. No friend, no star, and nothing blind (it cannot see
    the show at all)."""
    import senses
    radius = int(data()['stars']['watch_radius'])
    out = []
    for m in monsters or ():
        if (not getattr(m, 'alive', False) or is_star(m) or getattr(m, 'is_allied', False)
                or getattr(m, '_npc_encounter_tag', None) or getattr(m, '_flavor_encounter_tag', None)):
            continue
        if m.has_effect('blinded'):
            continue
        if any(_cheb(m.x, m.y, s.x, s.y) <= radius
               and senses.clear_view(s.x, s.y, m.x, m.y, dungeon) for s in stars):
            out.append(m)
    return out


def can_watch(m) -> bool:
    """Whether a creature near the show stops for it: never a named foe
    (they have seen better shows), nothing mindless, and nothing that
    cannot be stunned (a swarm: status_immune), so the watch line is never
    said of a creature the show did not hold (round 3)."""
    if m._is_named_foe() or set(m.tags or ()) & Monster._MINDLESS_TAGS:
        return False
    return not m.resists_control('stunned')


def watchers(monsters, stars, dungeon) -> list:
    """The monsters near the show that stop to watch it (near_show, can_watch)."""
    return [m for m in near_show(monsters, stars, dungeon) if can_watch(m)]


# ---------------------------------------------------------------------------
# The Zombie Stage
# ---------------------------------------------------------------------------

def build_stage():
    """(dungeon, monsters, items): the wings, where the hero arrives and the
    stage door (the way out, a down stair) stands; a short passage; and the
    stage hall, dressed with speakers, pyro and a runway, where the band
    rehearses at the far end."""
    import boss_levels as bl
    import decor
    from dungeon import STAIRS_DOWN, FLOOR

    tiles = bl._blank()
    wings = bl._carve_room(tiles, 14, 25, 4, 3)
    hall = bl._carve_room(tiles, 46, 25, 17, 9)
    bl._hline(tiles, wings.x + wings.width - 1, hall.x, 25)
    door = (wings.x + 1, 25)
    tiles[door[1]][door[0]] = STAIRS_DOWN
    dungeon = bl._make(tiles, [wings, hall], bl.STRAY_KIDS_STAGE)
    dungeon.domain = None
    dungeon.theme = None

    # Dressing: speaker stacks in the corners, pyro along the long walls,
    # a red runway down the middle.
    x0, y0 = hall.x, hall.y
    x1, y1 = hall.x + hall.width - 1, hall.y + hall.height - 1
    for pos in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        decor.place(dungeon, pos, 'sk_speaker')
    for x in (x0 + 9, x0 + 17, x0 + 25):
        for y in (y0 + 1, y1 - 1):
            decor.place(dungeon, (x, y), 'brazier_lit')
    for x in range(x0 + 4, x1 - 5):
        if tiles[25][x] == FLOOR:
            decor.place(dungeon, (x, 25), 'carpet')

    home = (x1 - 6, 25)
    dance = new_dance(home)
    dungeon.sk_dance = dance
    monsters = []
    leader = None
    taken = set()
    for slot, member in enumerate(members()):
        tx, ty = place_of(dance, slot)
        spot = (tx, ty)
        if not dungeon.is_walkable(*spot) or spot in taken:
            spot = next((t for t in hall.inner_tiles()
                         if dungeon.is_walkable(*t) and t not in taken), home)
        taken.add(spot)
        m = make_zombie(member, spot[0], spot[1], slot)
        _join_band(m, leader)
        if leader is None:
            leader = m
        monsters.append(m)
    dungeon.atmosphere_messages = list(data()['stage']['atmosphere'])
    return dungeon, monsters, []


def _join_band(m, leader) -> None:
    """Tag a member as one of the war-band (src/war_bands.py): Bang Chan
    leads; while he stands nobody runs, and when he falls the rest lose the
    count and stumble into one another."""
    m._band = f"{data()['band_id']}@stage"
    m._band_id = data()['band_id']
    m._band_role = 'leader' if leader is None else 'guard'
    if leader is not None:
        m._band_leader = leader
    m._home = (m.x, m.y)
    m._job_fixed = True
    m._job = 'guard'
