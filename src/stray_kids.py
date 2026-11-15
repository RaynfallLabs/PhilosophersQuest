"""The Stray Kids easter egg (Brandon, 2026-11-13): "my kids love this
stupid kpop band called Stray Kids." Every run, on one floor from 8 to 12, a
gold shrine to the band stands in a room. Touch it and the hero is taken to
the Zombie Stage, a side floor like the Cow Level, where the eight members
wait as zombies; the fight is a dance-off (Brandon, 2026-11-14: "B-B-B-BOSS
BATTLE! DANCE OFF!"), and the last to fall leaves a signed photo that calls
the band, alive, for one short show.

This module is the pure half (no pygame, no Game):

* the run's roll: which floor holds the idol (``new_run_state``);
* the dance-off's rules: Simon Says over eight rounds, one member leading
  each, Bang Chan first. Round r dances the first steps of the written
  choreography, one more each round, a little faster each round
  (``round_phrase``, ``round_bpm``, ``round_timeline``); what follows a round
  (``after_round``: the next leader, the round again with a strike gone, the
  dance-off won or lost); the earworm a lost round brings (``earworm``: his
  song, its hindrance, a little damage that never kills);
* ``ZombieMember``: one zombie band member, a performer: he stands posed in
  his place on the stage, takes no harm and never strikes. No corpse
  (``_no_corpse``), an Observe line of his own;
* ``settle_band``: every member still standing back in his place, a
  performer (a lost dance-off, and a save from before the dance-off);
* ``StarDancer``: one living member called up by the photo: an ally that
  takes and deals no harm and dances round the hero;
* ``build_stage``: the Zombie Stage itself (boss_levels.STRAY_KIDS_STAGE).

The game half (the idol, the trip there and back, the announcement, the
dance-off on the Mooble's dance screen, the shouts, the photo, the show) is
game_stray_kids.StrayKidsMixin. Every line of text and every number is in
data/stray_kids.json; the members' songs (the earworm) in data/monsters.json.
No real lyrics anywhere: the lines are made up, and songs are named only by
their titles.
"""
from __future__ import annotations

import json
import random
import re

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
    """The eight, in their places on the stage (Bang Chan first: he leads)."""
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
    the floor to go back to, how the stage ended ('cleared' or 'left'),
    whether the photo has dropped, the dance-off's challenge (None, then
    'pending' once the band has seen the hero and the announcement fired,
    then 'made' once the dance-off screen first opened), and the dance-off
    screen if it is open (``dancing``: its mode and the strikes left; a load
    opens it again at the start of the current round)."""
    return {'floor': roll_for_new_run(), 'spawned': False, 'pos': None, 'called': False,
            'touched': False, 'return_floor': 0, 'outcome': None, 'photo_dropped': False,
            'challenge': None, 'dancing': None}


def old_save_state() -> dict:
    """A save from before the egg: a run without it (its floors may be behind
    the hero already)."""
    return {'floor': None, 'spawned': False, 'pos': None, 'called': False,
            'touched': False, 'return_floor': 0, 'outcome': None, 'photo_dropped': False,
            'challenge': None, 'dancing': None}


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def the_band(monsters) -> list:
    """The band members still standing, in their places' order."""
    return sorted((m for m in monsters or () if is_zombie(m) and getattr(m, 'alive', False)),
                  key=lambda m: int(getattr(m, '_sk_slot', 0)))


# ---------------------------------------------------------------------------
# The dance-off (pure): Simon Says, eight rounds, a member leading each
# ---------------------------------------------------------------------------

def dance_off() -> dict:
    return data()['dance_off']


def rounds() -> int:
    """One round for each member."""
    return len(members())


def strikes() -> int:
    """The strikes a dance-off allows (a lost round spends one)."""
    return max(1, int(dance_off()['strikes']))


def round_steps(i: int) -> int:
    """How many steps round ``i`` (0 first) has: first_steps, and
    steps_per_round more each round (never more than the choreography)."""
    d = dance_off()
    n = int(d['first_steps']) + int(d['steps_per_round']) * max(0, int(i))
    return max(1, min(len(d['choreography']), n))


def round_phrase(i: int) -> list:
    """The steps of round ``i`` as [[beat, dir], ...] (rhythm.phrase's form):
    the choreography's first round_steps(i) steps, one a beat. Simon Says:
    each round is the whole of the last, and one step more."""
    d = dance_off()
    return [[k, d['choreography'][k]] for k in range(round_steps(i))]


def round_bpm(i: int) -> int:
    """Round ``i``'s tempo: a little faster every round."""
    d = dance_off()
    return int(d['bpm_first']) + int(d['bpm_per_round']) * max(0, int(i))


def phrase_beats(steps: int) -> int:
    """The beats a phrase of ``steps`` takes: whole bars of bar_beats, with
    at least rest_beats of rest after its last step (a breath between the
    leader's call and the hero's turn)."""
    d = dance_off()
    bar = max(1, int(d.get('bar_beats', 4)))
    need = int(steps) + max(0, int(d.get('rest_beats', 1)))
    return bar * -(-need // bar)


def round_timeline(i: int) -> dict:
    """Round ``i`` laid out on the beat (rhythm.timeline): a count-in, the
    leader's call, then the hero's turn."""
    import rhythm
    d = dance_off()
    return rhythm.timeline(round_phrase(i), round_bpm(i), int(d['lead_beats']),
                           phrase_beats(round_steps(i)))


def fallen(monsters) -> int:
    """How many of the eight have fallen (the rounds won so far)."""
    return max(0, rounds() - len(the_band(monsters)))


def round_index(monsters) -> int:
    """The round to dance now (0 first): one for every member fallen."""
    return max(0, min(rounds() - 1, fallen(monsters)))


def leader(monsters):
    """Who leads the round now: the first of the band still standing."""
    band = the_band(monsters)
    return band[0] if band else None


def after_round(won: bool, strikes_left: int, standing_after: int) -> tuple:
    """What follows a round: ('won', strikes) when the last of the band fell;
    ('next', strikes) when its leader fell and another leads; ('retry',
    strikes - 1) a strike gone, and the round again; ('lost', 0) out of
    strikes, the dance-off lost."""
    if won:
        return ('won' if int(standing_after) <= 0 else 'next', int(strikes_left))
    left = int(strikes_left) - 1
    return ('retry', left) if left > 0 else ('lost', 0)


def _defs() -> dict:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def earworm_attack(member: str, defs: dict | None = None) -> dict:
    """His song: the attack of his (data/monsters.json) that carries a
    hindrance, a voice first; his first attack if none does."""
    attacks = list(((defs or _defs()).get(zombie_kind(member)) or {}).get('attacks') or ())
    with_effect = [a for a in attacks if a.get('effect')]
    voiced = [a for a in with_effect if a.get('delivery') == 'voice']
    pick = (voiced or with_effect or attacks or [{}])[0]
    return dict(pick)


def _roll(notation: str, rng) -> int:
    m = re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', str(notation or '').strip().lower().replace(' ', ''))
    if not m:
        return 0
    count = int(m.group(1) or 1)
    sides = max(1, int(m.group(2)))
    return sum(rng.randint(1, sides) for _ in range(count)) + int(m.group(3) or 0)


def earworm(member: str, hero_hp: int, rng, defs: dict | None = None) -> dict:
    """What a lost round does to the hero: the leader's song gets stuck in
    his head. {'song', 'quip', 'effect', 'turns', 'damage'}: his song's own
    hindrance (the data's when it has none), and its damage, never more than
    max_damage and never the last hit point (no dumb-luck death)."""
    ew = dance_off()['earworm']
    atk = earworm_attack(member, defs)
    effect = atk.get('effect') or ew['effect']
    turns = int(atk.get('effect_duration') or ew['turns']) if atk.get('effect') else int(ew['turns'])
    roll = max(0, _roll(atk.get('damage', '1d2'), rng))
    damage = max(0, min(roll, int(ew['max_damage']), int(hero_hp) - 1))
    return {'song': atk.get('name', ''), 'quip': atk.get('quip', ''), 'effect': effect,
            'turns': max(1, turns), 'damage': damage}


def leader_line(member: str, which: str, rng) -> str:
    """One of his lines for the dance-off: 'open' (his line as he leads the
    round) or 'roast' (when the hero misses it)."""
    lines = ((dance_off().get('leaders') or {}).get(member) or {}).get(which) or ()
    return rng.choice(list(lines)) if lines else ''


# ---------------------------------------------------------------------------
# The zombie band: performers on the stage
# ---------------------------------------------------------------------------

class ZombieMember(Monster):
    """One of the eight, dead and still performing. He stands posed in his
    place and waits for a dance-off: no blow or spell touches him (a
    performer, like the stars of a show: ``is_allied``), nothing holds him,
    and he never strikes. He falls only to a round of the dance-off."""

    is_sk_zombie = True
    _no_corpse = True               # they disintegrate (game_combat._on_monster_killed)

    def __init__(self, defn: dict, x: int, y: int, member: str = '', slot: int = 0):
        super().__init__({**defn, 'is_allied': True}, x, y)
        self._sk_member = member or defn['id'].replace('sk_zombie_', '', 1)
        self._sk_slot = int(slot)
        self._home = (int(x), int(y))
        self.perform()

    @property
    def member(self) -> str:
        return self.__dict__.get('_sk_member', '')

    def perform(self) -> None:
        """A performer again: unhurt, unhindered, out of any war-band (a save
        from before the dance-off had the band fighting)."""
        self.is_allied = True
        self.status_effects = {}
        self.hp = self.max_hp
        for attr in ('_band', '_band_id', '_band_role', '_band_leader', '_sk_events',
                     '_tracking', '_job', '_job_fixed'):
            self.__dict__.pop(attr, None)
        self.quarrelsome = False

    @property
    def observe_line(self) -> str:
        """What Observe (O) says of him, after the usual lines."""
        d = data()
        own = d['observe'].get(self.member, '')
        return ' '.join(p for p in (own, d['dance_off']['observe_tell']) if p)

    def take_damage(self, amount: int, damage_type: str = 'physical',
                    ignore_resistance: bool = False) -> int:
        return 0

    def add_effect(self, name: str, duration: int):
        pass                        # nothing stops the show

    def hold(self, name: str, duration: int):
        pass                        # (a held stare, a stun: nothing holds a performer)

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """He holds his pose, waiting for the dance-off."""
        return False


def make_zombie(member: str, x: int, y: int, slot: int) -> ZombieMember:
    defs = _defs()
    kind = zombie_kind(member)
    return ZombieMember({**defs[kind], 'id': kind}, x, y, member=member, slot=slot)


def _hall(dungeon):
    rooms = getattr(dungeon, 'rooms', None) or []
    return rooms[1] if len(rooms) > 1 else (rooms[0] if rooms else None)


def stage_home(dungeon) -> tuple:
    """Where the band's V is anchored: home_from_east tiles in from the
    hall's east wall, on its middle row."""
    hall = _hall(dungeon)
    back = int(data()['stage'].get('home_from_east', 6))
    return (hall.x + hall.width - 1 - back, hall.y + hall.height // 2)


def place_of(dungeon, slot: int) -> tuple:
    """Member ``slot``'s place in the V (stage.formation)."""
    offs = data()['stage']['formation']
    hx, hy = stage_home(dungeon)
    dx, dy = offs[int(slot) % len(offs)]
    return (hx + int(dx), hy + int(dy))


def stage_edge(dungeon) -> tuple:
    """The edge of the stage: the hall's first tile where the passage from
    the wings comes in (a lost dance-off sets the hero down here)."""
    hall = _hall(dungeon)
    return (hall.x, hall.y + hall.height // 2)


def on_stage(dungeon, x: int, y: int) -> bool:
    """Is (x, y) on the stage (the hall), not in the wings or the passage?"""
    hall = _hall(dungeon)
    if hall is None:
        return False
    return hall.x <= x < hall.x + hall.width and hall.y <= y < hall.y + hall.height


def settle_band(dungeon, monsters, hero_xy=None) -> int:
    """Every member still standing back in his place, a performer again
    (unhurt, unhindered, out of any war-band). A lost dance-off resets the
    band this way, and so does loading a save from before the dance-off,
    when the band was fighting in formation. The fallen stay fallen. The old
    dance's state on the floor is dropped. Returns how many were settled."""
    getattr(dungeon, '__dict__', {}).pop('sk_dance', None)
    taken = {tuple(hero_xy)} if hero_xy else set()
    taken |= {(m.x, m.y) for m in monsters or ()
              if getattr(m, 'alive', False) and not is_zombie(m)}
    band = the_band(monsters)
    for m in band:
        m.perform()
        spot = place_of(dungeon, int(getattr(m, '_sk_slot', 0)))
        if spot in taken or not dungeon.is_walkable(*spot):
            hall = _hall(dungeon)
            spot = next((t for t in hall.inner_tiles()
                         if dungeon.is_walkable(*t) and t not in taken), (m.x, m.y))
        m.x, m.y = spot
        m._home = spot
        taken.add(spot)
    return len(band)


# ---------------------------------------------------------------------------
# The stars: the band alive, called up by the photo
# ---------------------------------------------------------------------------

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
    stands posed in a V at the far end (stage.formation)."""
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

    monsters = []
    taken = set()
    for slot, member in enumerate(members()):
        spot = place_of(dungeon, slot)
        if not dungeon.is_walkable(*spot) or spot in taken:
            spot = next((t for t in hall.inner_tiles()
                         if dungeon.is_walkable(*t) and t not in taken), stage_home(dungeon))
        taken.add(spot)
        monsters.append(make_zombie(member, spot[0], spot[1], slot))
    dungeon.atmosphere_messages = list(data()['stage']['atmosphere'])
    return dungeon, monsters, []
