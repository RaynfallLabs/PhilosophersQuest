"""The Mooble: the last dancer of the old mines (RARE_PETS_PLAN_2026_11_14,
section 2; Brandon's answers at its top).

Every run, on one floor of 31-45, in a quiet side cave carved off the main
floor, a small cream-furred sprite with little bat wings and a red bobble on
a wire antenna dances alone on a ledge. The Moobles once danced with the
miners to keep the dark back; the others went quiet one by one when the
miners left. He is the last, and a dance needs a partner. He is "he", and he
ends what he says with "...pom" (an homage, never a copy).

The visits (all words and numbers in data/mooble.json):

  * MEET: his story, from his ledge. He misses the miners' Starnut Tarts,
    and says what goes in one; the hero learns the dish
    (``player.dishes_learned``: the cook menu shows it under Building
    Toward) and a Starnut grows in the cracks of his cave.
  * THE TART: give him a Starnut Tart (cooked to carry: kitchen.py) and he
    eats it and comes down. Nothing else will bring him down.
  * THREE DANCES, with ``gap_turns`` between; leaving his floor counts as
    waiting. Every visit he offers PRACTICE (free, no stakes, as often as
    wanted, leavable any time; always on offer, even while the next
    dance-off waits), then the DANCE-OFF, which must be WON (rhythm.py; the
    screen is game_mooble_dance.py). A lost dance-off ends the visit with a
    line. Come back too soon and he is still dancing the last one through
    (``too_soon``, one line a stage): the dance-off waits, practice does
    not. Each win has its own line: he bobs, unsure; his bobble glows; he
    spins and laughs.
  * "I CHOOSE YOU!": after the third win he asks to come along. The animal
    quiz (as the Emberpup's); refusals say what is missing. Pass, and he
    joins as the support companion (pet_system species 'mooble': small
    health, weak bites, mana while near, the Dance of the Dark, which is
    danced: a count-in, then his phrase, and the better it is danced the
    stronger it is, ``dance_band``).

Run state lives in ``game._mooble`` (saved): the floor (None in a run
without him), placed yet, how it ended ('adopted'), the turn of the last
dance-off (or fumbled ask), whether the hero has been away since, a failed
ask, and the dance screen if it was open (a load opens it again at the
start of its phrase). His own state (met, the tart, dances won) is on the
creature, saved with the floor.
"""
from __future__ import annotations

import json
import random

from game_states import STATE_PLAYER, STATE_QUIZ, STATE_PET_NAME_INPUT, STATE_MOOBLE

_DATA: dict | None = None
SEED_XOR = 0x300B1E


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'mooble.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def art(sid: str) -> str:
    """One of his pictures, or the stand-in until it is installed (never a
    letter on the map)."""
    from pet_system import art_or_standin
    return art_or_standin(sid, data().get('art_standin'))


def candidate_floors(exclude=(), above: int = 0) -> list:
    """The floors he may wait on: first_floor to last_floor, never a gate
    boss's floor, deeper than ``above``; a floor in ``exclude`` (a planned
    mini-boss's) only when nothing else is left."""
    from boss_levels import BOSS_LEVELS
    d = data()
    floors = [f for f in range(int(d['first_floor']), int(d['last_floor']) + 1)
              if f not in BOSS_LEVELS and f > int(above or 0)]
    free = [f for f in floors if f not in set(exclude or ())]
    return free or floors


def roll_floor(rng, exclude=(), above: int = 0) -> int | None:
    """This run's floor for him, or None (no run, with the data as it ships:
    chance_per_run is 1.0; or every floor of his is behind the hero)."""
    if rng.random() >= float(data()['chance_per_run']):
        return None
    floors = candidate_floors(exclude, above)
    return rng.choice(floors) if floors else None


def _run_rng() -> random.Random:
    """The run's own generator for him, seeded from the shared stream
    without moving it (seeded floors and captures stay as they were)."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return random.Random(seed ^ SEED_XOR)


def new_run_state(exclude=(), above: int = 0) -> dict:
    """A run's Mooble: his floor, nothing done yet."""
    rng = _run_rng()
    return {'floor': roll_floor(rng, exclude, above), 'spawned': False, 'outcome': None,
            'seed': rng.getrandbits(32)}


def is_mooble(thing) -> bool:
    return bool(getattr(thing, '_is_mooble', False))


def needed() -> int:
    return int(data().get('dances_needed', 3))


def dances(m) -> int:
    """Dance-offs he has won with the hero (0 to dances_needed)."""
    return max(0, min(needed(), int(getattr(m, '_mooble_dances', 0) or 0)))


def has_tart(m) -> bool:
    return bool(getattr(m, '_mooble_tart', False))


def visit_spec(m) -> dict:
    """The dance of his next visit: {'bpm', 'steps'} (data dance.visits,
    one a visit: the first dance slow and short, the last long and quick)."""
    visits = data()['dance']['visits']
    return visits[max(0, min(len(visits) - 1, dances(m)))]


def waiting_text(m) -> str:
    d = data()
    if not has_tart(m):
        return d['waiting_ledge']
    lines = d['waiting']
    return lines[min(dances(m), len(lines) - 1)]


def special_spec() -> dict:
    """The Dance of the Dark as a dance (data pet.special_dance)."""
    return (data().get('pet') or {}).get('special_dance') or {}


def special_phrase(stage: int) -> dict:
    """His phrase for the special at his stage: {'bpm', 'steps'}."""
    phrases = special_spec().get('phrases') or [{'bpm': 90, 'steps': [[0, 'left']]}]
    return phrases[max(0, min(len(phrases) - 1, int(stage)))]


def dance_band(result: dict) -> dict:
    """How strong the Dance of the Dark is for a danced ``result``
    (rhythm.judge): the band its score reaches (radius, turns, max_held,
    lift, label, line), with the score itself under 'score'. Pure."""
    import rhythm
    spec = special_spec()
    s = rhythm.score(result, float(spec.get('perfect_worth', 1.0)), float(spec.get('stray_cost', 0.0)))
    b = dict(rhythm.band(s, spec.get('bands') or ()))
    b['score'] = s
    return b


def special_result_line(band: dict) -> str:
    """What the Dance of the Dark's result card says it did (data
    pet.special_dance ``result``): its band, its reach, how long they stare
    ("1 turn", "3 turns": ``turn_words``) and how many it held. Pure."""
    sd = special_spec()
    held_words = sd.get('held_words') or ['{n}', '{n}', '{n}']
    mh = int(band.get('max_held', 99))
    held = (held_words[0] if mh <= 1 else held_words[2] if mh >= 99 else held_words[1]).format(n=mh)
    turns = int(band.get('turns', 0) or 0)
    one, many = sd.get('turn_words') or ('{n} turn', '{n} turns')
    return sd.get('result', '').format(label=band.get('label', ''), radius=band.get('radius'),
                                       turns=(one if turns == 1 else many).format(n=turns),
                                       held=held)


def too_soon_line(m) -> str:
    lines = data()['too_soon']
    return lines[max(0, min(dances(m), len(lines) - 1))]


def sprite_of(m) -> str:
    """On his ledge until the tart; down on the cave floor after."""
    d = data()
    return art(d['sprite_down'] if has_tart(m) else d['sprite_ledge'])


def tart_in(inventory):
    """A Starnut Tart in the pack, or None."""
    tid = data()['tart_item']
    return next((i for i in inventory or () if getattr(i, 'id', None) == tid), None)


def make_starnut(x: int = 0, y: int = 0):
    from food_system import load_ingredient_for
    nut = load_ingredient_for(data().get('starnut_id', 'starnut'))
    if nut is not None:
        nut.x, nut.y = x, y
    return nut


def make_tart(x: int = 0, y: int = 0):
    from items import make_item_by_id
    tart = make_item_by_id('food', data()['tart_item'])
    if tart is not None:
        tart.x, tart.y = x, y
        tart.count = 1
        tart.identified = True
    return tart


def near_dance(monsters, pet, dungeon, radius: int) -> list:
    """The creatures near the dance: within ``radius`` of him with a clear
    view of him. No friend, no encounter's person (the Stray Kids' show
    keeps the same company: stray_kids.near_show)."""
    import senses
    out = []
    for m in monsters or ():
        if (not getattr(m, 'alive', False) or getattr(m, 'is_allied', False)
                or getattr(m, '_npc_encounter_tag', None) or getattr(m, '_flavor_encounter_tag', None)
                or getattr(m, 'is_sk_star', False)):
            continue
        if max(abs(m.x - pet.x), abs(m.y - pet.y)) > int(radius):
            continue
        if not senses.clear_view(pet.x, pet.y, m.x, m.y, dungeon):
            continue
        out.append(m)
    return out


def why_unmoved(m) -> str | None:
    """Why a creature near the dance does not stop for it, or None when it
    does: 'blind' (it cannot see it), 'named' (a named foe), 'mindless',
    or 'unmoved' (it cannot be stunned). The Stray Kids' watch rule
    (stray_kids.can_watch), with the reasons told apart for the lines."""
    from monster import Monster
    if m.has_effect('blinded'):
        return 'blind'
    if m._is_named_foe():
        return 'named'
    if set(getattr(m, 'tags', None) or ()) & Monster._MINDLESS_TAGS:
        return 'mindless'
    if m.resists_control('stunned'):
        return 'unmoved'
    return None


class MoobleMixin:
    """His place in the run, his screen and his gifts as a companion. The
    dance itself is game_mooble_dance.MoobleDanceMixin."""

    # ---- run state --------------------------------------------------------

    def _mooble_state(self) -> dict:
        st = getattr(self, '_mooble', None)
        if not isinstance(st, dict):
            st = {'floor': None, 'spawned': False, 'outcome': None}
            self._mooble = st
        return st

    def _mooble_left(self, from_level: int, to_level=None):
        """Leaving his floor after a dance-off is waiting, as good as the
        turns (Game._change_level)."""
        st = self._mooble_state()
        if st.get('last_turn') is not None and from_level == st.get('floor') and to_level != from_level:
            st['away'] = True

    # ---- spawn ------------------------------------------------------------

    def _maybe_spawn_mooble(self, level: int):
        """His cave and him, on his floor, once a run, on first arrival."""
        st = self._mooble_state()
        if st.get('last_turn') is not None and level != st.get('floor'):
            st['away'] = True
        if st.get('spawned') or st.get('outcome') or st.get('floor') != level:
            return
        if any(is_mooble(m) for m in self.monsters):
            return
        d = data()
        cave = self._mooble_carve_cave()
        spot = cave['back'] if cave else self._mooble_room_spot()
        if spot is None:
            return
        from monster import Monster
        defn = {
            'id': d['sprite_ledge'], 'name': d['name'], 'symbol': d.get('symbol', 'm'),
            'pronoun': 'he', 'color': list(d.get('color', [240, 225, 200])), 'hp': 1, 'thac0': 20,
            'speed': 0, 'attacks': [], 'ai_pattern': 'sessile', 'resistances': [],
            'weaknesses': [], 'min_level': level, 'is_allied': True,
            'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None,
        }
        m = Monster(defn, *spot)
        m._is_mooble = True
        m._mooble_met = False       # his story has been told
        m._mooble_tart = False      # he has eaten a Starnut Tart and come down
        m._mooble_dances = 0        # dance-offs won with the hero
        m.sprite_id = sprite_of(m)
        if cave:
            m._mooble_cave = cave
        self.monsters.append(m)
        st['spawned'] = True
        # Starnuts grow in the cracks of his cave: the tart can always be baked.
        n = int(d.get('starnuts_in_cave', 0) or 0)
        tiles = [t for t in (cave['chamber'] if cave else ()) if t != spot and t != cave['centre']]
        if not tiles:
            tiles = [t for t in self._mooble_tiles_near(spot) if t != spot]
        for t in tiles[:n]:
            nut = make_starnut(*t)
            if nut is not None:
                self.ground_items.append(nut)
        msg = (d.get('log') or {}).get('cave')
        if msg:
            try:
                if msg not in self.dungeon.atmosphere_messages:
                    self.dungeon.atmosphere_messages.append(msg)
            except AttributeError:
                pass

    def _mooble_carve_cave(self):
        """A quiet 3x3 side cave behind a room's wall, open to it by one
        tile (dungeon._carve_sealed_shrine's carving, left open: no door).
        Returns {'mouth', 'centre', 'back', 'chamber'} or None (no rock)."""
        from dungeon import FLOOR, _carve_sealed_shrine
        d = self.dungeon
        rooms = list(d.rooms[1:]) if len(d.rooms) > 1 else list(d.rooms)
        # Never off a war-band's camp (war_bands.camp_tiles): three dance-offs
        # meant three fights through the band.
        import war_bands
        rooms = war_bands.outside_camp(d, rooms)
        camp = war_bands.camp_tiles(d)
        rng = random.Random(int(self._mooble_state().get('seed') or 0) ^ SEED_XOR)
        rng.shuffle(rooms)
        for r in rooms[:12]:
            carved = _carve_sealed_shrine(d, r.center, avoid=camp)
            if not carved:
                continue
            (wx, wy), (sx, sy) = carved
            ddx, ddy = (sx - wx) // 2, (sy - wy) // 2
            d.tiles[wy][wx] = FLOOR
            chamber = [(x, y) for y in range(sy - 1, sy + 2) for x in range(sx - 1, sx + 2)]
            import decor
            for pos in chamber + [(wx, wy), (wx - ddx, wy - ddy)]:
                if decor.fixture_at(d, *pos):
                    decor.remove(d, pos)
            self.ground_items[:] = [g for g in self.ground_items if (g.x, g.y) not in set(chamber)]
            back = (sx + ddx, sy + ddy)
            return {'mouth': (wx, wy), 'centre': (sx, sy), 'back': back, 'chamber': chamber}
        return None

    def _mooble_room_spot(self):
        """No rock to carve a cave in: a quiet room's inner tile instead."""
        from geom import all_occupied_tiles
        import war_bands
        occupied = (all_occupied_tiles(self.monsters) | self._occupants()
                    | war_bands.camp_tiles(self.dungeon))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        rooms = war_bands.outside_camp(self.dungeon, rooms)
        rng = random.Random(int(self._mooble_state().get('seed') or 0))
        for room in rng.sample(list(rooms), min(len(rooms), 6)):
            tiles = [t for t in room.inner_tiles()
                     if self.dungeon.is_walkable(*t) and t not in occupied]
            if tiles:
                return rng.choice(tiles)
        return self._free_spawn_tile(occupied)

    def _mooble_tiles_near(self, spot) -> list:
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = (spot[0] + dx, spot[1] + dy)
                if self.dungeon.is_walkable(*t):
                    out.append(t)
        return out

    def _mooble_here(self):
        return next((m for m in self.monsters if is_mooble(m) and getattr(m, 'alive', True)), None)

    # ---- the screen -------------------------------------------------------

    def _mooble_too_soon(self, m) -> bool:
        """Less than gap_turns since the last dance-off (or a fumbled ask),
        the hero never away since: he is still dancing the last one through.
        Once he has danced all three he waits for the ask, unless an ask
        was fumbled."""
        st = self._mooble_state()
        if st.get('last_turn') is None or st.get('away'):
            return False
        if dances(m) >= needed() and not st.get('choose_failed'):
            return False
        gap = int(data().get('gap_turns', 30))
        return int(getattr(self, 'turn_count', 0)) - int(st.get('last_turn') or 0) < gap

    def _start_mooble_encounter(self, m):
        """Bumping him: his story the first time; his choices after that,
        unless he is still dancing the last one through."""
        d = data()
        self._mooble_npc = m
        first = not getattr(m, '_mooble_met', False)
        self._mooble_phase = 'story' if first else 'options'
        m._mooble_met = True
        self._mooble_text = ''
        self._mooble_after = 'options'
        self._mooble_acted = False
        self.state = STATE_MOOBLE
        if first:
            self._mooble_learn_tart()
            self._chron('discovery', d['met_chronicle'], once='mooble:met')
        elif self._mooble_too_soon(m):
            # Too soon: the dance-off (and the ask) wait; his choices show
            # the line, and practice is always on offer. No turn is spent.
            self._mooble_text = too_soon_line(m)

    def _mooble_learn_tart(self):
        """The miners' Starnut Tart: the cook menu shows it from now on."""
        rid = data()['tart_recipe']
        known = self.player.__dict__.get('dishes_learned')
        if known is None:
            known = self.player.__dict__['dishes_learned'] = set()
        if rid not in known:
            known.add(rid)
            self.add_message(data()['log']['learned_tart'], 'info')

    def _mooble_outcome(self, text: str, after: str):
        self._mooble_text = text
        self._mooble_after = after
        self._mooble_phase = 'outcome'

    def _close_mooble(self):
        acted = getattr(self, '_mooble_acted', False)
        self._mooble_npc = None
        self._mooble_phase = 'story'
        self._mooble_acted = False
        self.state = STATE_PLAYER
        if acted:
            self._advance_turn()

    def _mooble_input(self, key: int):
        import pygame
        phase = getattr(self, '_mooble_phase', 'options')
        m = getattr(self, '_mooble_npc', None)
        if m is None:
            self.state = STATE_PLAYER
            return
        if phase == 'story':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._mooble_phase = 'options'
            elif key == pygame.K_ESCAPE:
                self._close_mooble()
            return
        if phase == 'outcome':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                after = self._mooble_after
                if after == 'options':
                    self._mooble_phase = 'options'
                elif after == 'name':
                    self._mooble_open_naming()
                else:
                    self._close_mooble()
            return
        if key in (pygame.K_1, pygame.K_KP1):
            self._mooble_practice()
        elif key in (pygame.K_2, pygame.K_KP2):
            self._mooble_dance_off()
        elif key in (pygame.K_3, pygame.K_KP3):
            self._mooble_give_tart()
        elif key in (pygame.K_4, pygame.K_KP4):
            self._mooble_choose()
        elif key in (pygame.K_5, pygame.K_KP5, pygame.K_ESCAPE):
            self._mooble_leave()

    # ---- the choices ------------------------------------------------------

    def _mooble_practice(self):
        """Practice: free, no stakes, as often as wanted, once he is off his
        ledge (after all three dances, the last one again, for fun)."""
        m = self._mooble_npc
        if not has_tart(m):
            self._mooble_outcome(data()['on_ledge'], 'options')
            return
        self._mooble_open_dance('practice')

    def _mooble_dance_off(self):
        """The dance-off, which must be won: off his ledge, with a dance
        still to dance."""
        m = self._mooble_npc
        if not has_tart(m):
            self._mooble_outcome(data()['on_ledge'], 'options')
            return
        if dances(m) >= needed():
            self._mooble_outcome(data()['all_danced'], 'options')
            return
        if self._mooble_too_soon(m):
            self._mooble_outcome(too_soon_line(m), 'options')
            return
        self._mooble_open_dance('dance')

    def _mooble_give_tart(self):
        d = data()
        m = self._mooble_npc
        if has_tart(m):
            self._mooble_outcome(d['already_ate'], 'options')
            return
        tart = tart_in(self.player.inventory)
        if tart is None:
            self._mooble_outcome(d['no_tart'], 'options')
            return
        self.player.remove_from_inventory(tart)
        m._mooble_tart = True
        m.sprite_id = sprite_of(m)
        self._mooble_acted = True
        import deeds
        deeds.note(self, 'aid.mooble', source='mooble', unique=True)
        self.add_message(d['log']['gave_tart'], 'success')
        self._mooble_outcome(d['tart_given'], 'options')

    def _mooble_leave(self):
        self.add_message(data()['ignore'], 'info')
        self._close_mooble()

    def _mooble_dance_done(self, result: dict, won: bool):
        """A dance-off is over (game_mooble_dance): the visit ends with its
        line. Won: one dance more (the third, and he asks to come along).
        Lost: the bobble dims. Either way the next try waits gap_turns."""
        d = data()
        m = getattr(self, '_mooble_npc', None) or self._mooble_here()
        st = self._mooble_state()
        st['last_turn'] = int(getattr(self, 'turn_count', 0))
        st['away'] = False
        self._mooble_npc = m
        self._mooble_acted = True
        self.state = STATE_MOOBLE
        fill = {'hits': result.get('hits', 0), 'steps': result.get('total', 0)}
        # The Seeker (Not a Step Missed) and the quirks (Terpsichore's Step):
        # the dance-off as danced, and whether it was practised first.
        practised = bool(st.pop('practised', False))
        self._seeker_event('dance_off', won=bool(won), misses=int(result.get('misses', 0) or 0),
                           perfects=int(result.get('perfects', 0) or 0),
                           total=int(result.get('total', 0) or 0), practised=practised,
                           dance=(dances(m) + 1) if m is not None else 0)
        _qs = getattr(self, 'quirk_system', None)
        if _qs is not None:
            _qs.on_dance_off(bool(won), practised)
        if m is None:
            self.state = STATE_PLAYER
            return
        if won:
            before = dances(m)
            m._mooble_dances = min(needed(), before + 1)
            self.add_message(d['log']['won'].format(**fill), 'success')
            lines = d['dance_won']
            text = lines[min(before, len(lines) - 1)]
            self._mooble_outcome(text, 'options' if dances(m) >= needed() else 'player')
        else:
            self.add_message(d['log']['lost'].format(**fill), 'info')
            self._mooble_outcome(d['dance_lost'], 'player')

    def _mooble_choose(self):
        d = data()
        m = self._mooble_npc
        if not has_tart(m):
            self._mooble_outcome(d['refused_ledge'], 'options')
            return
        if dances(m) < needed():
            lines = d['refused_dances']
            self._mooble_outcome(lines[min(dances(m), len(lines) - 1)], 'options')
            return
        if self._mooble_too_soon(m):
            self._mooble_outcome(too_soon_line(m), 'options')
            return
        q = d['quiz']
        subject, tier, need = q['subject'], int(q['tier']), int(q['threshold'])
        self.quiz_title = d['quiz_title']
        self.state = STATE_QUIZ

        def on_complete(result):
            self._mooble_npc = m
            if result.success:
                self._mooble_adopt(m)
            else:
                st = self._mooble_state()
                st['last_turn'] = int(getattr(self, 'turn_count', 0))
                st['away'] = False
                st['choose_failed'] = True
                self.add_message(d['log']['shied'], 'info')
                self._mooble_acted = True
                self._mooble_outcome(d['fail'], 'player')
                self.state = STATE_MOOBLE

        self.quiz_engine.start_quiz(
            mode='threshold', subject=subject, tier=tier, callback=on_complete,
            threshold=need,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )

    def _mooble_adopt(self, m):
        """He joins you, at the level his years of dancing give him (never
        the floor's), through the one-companion rule."""
        from pet_system import Pet
        d = data()
        x, y = m.x, m.y
        m.alive = False
        try:
            self.monsters.remove(m)
        except ValueError:
            pass
        st = self._mooble_state()
        st['outcome'] = 'adopted'
        st.pop('choose_failed', None)
        import deeds
        deeds.note(self, 'saved.mooble', source='mooble', unique=True)
        pet = Pet(d['pet_species'], x, y, level=int(d.get('pet_level', 1)))
        self._companions_to_stasis()          # one companion at a time
        self.pets.append(pet)
        self._mooble_new_pet = pet
        self.add_message(d['log']['joined'], 'success')
        self._mooble_outcome(d['pass'], 'name')
        self.state = STATE_MOOBLE

    def _mooble_open_naming(self):
        """The naming popup, with the Mooble's own words."""
        d = data()
        pet = getattr(self, '_mooble_new_pet', None)
        self._mooble_npc = None
        self._mooble_new_pet = None
        if pet is None:
            self.state = STATE_PLAYER
            return
        self._naming_pet = pet
        self._pet_name_input_buffer = pet.species_name
        self._naming_story = {
            'title': d['name_title'], 'prompt': d['name_prompt'],
            'named_message': d['named_message'], 'unnamed_message': d['unnamed_message'],
            'named_chronicle': d['named_chronicle'], 'unnamed_chronicle': d['unnamed_chronicle'],
        }
        self.state = STATE_PET_NAME_INPUT

    # ---- after a load -------------------------------------------------------

    def _mooble_after_load(self):
        """A save made while his dance was on screen: open it again, at the
        start of its phrase (nothing was judged; a dance-off left open is
        still to be danced)."""
        st = self._mooble_state()
        dancing = st.get('dancing')
        if not dancing:
            return
        m = self._mooble_here()
        st['dancing'] = None
        if m is None or not has_tart(m) or dances(m) >= needed():
            return
        self._mooble_npc = m
        self._mooble_phase = 'options'
        self._mooble_acted = False
        self._mooble_open_dance(dancing.get('mode', 'practice') if isinstance(dancing, dict) else 'practice')

    # ---- the companion ------------------------------------------------------

    def _mooble_gift_said(self, pet, given: int):
        """His mana gift: said once a floor, the first time it comes (it
        comes every few turns; the log is not a ticker)."""
        if given <= 0:
            return
        floor = int(getattr(self, 'dungeon_level', 0) or 0)
        if pet.__dict__.get('_gift_said_floor') == floor:
            return
        pet._gift_said_floor = floor
        gift = (pet.species or {}).get('mana_gift') or {}
        line = gift.get('line')
        if line:
            self.add_message(line.replace('{pet}', pet.name), 'success')

    def _mooble_dance_of_the_dark(self, pet, special: dict, band: dict | None = None):
        """The Dance of the Dark, as strong as it was danced (``band``,
        dance_band; with none, the special's own written numbers): every foe
        within the band's reach with a clear view of him that can be stunned
        stands staring for the band's turns, the nearest first, up to its
        max_held (the Stray Kids' watch rule: never a named foe, the
        mindless, the blind, or what cannot be stunned, and each of those
        the hero can see is told why). A Troupe-Leader's dance, danced well
        enough (the band's lift), also lifts one hindrance from the hero.
        Returns how many were held."""
        from monster import fill
        lines = (data().get('pet') or {}).get('lines') or {}
        band = band or {}
        radius = int(band.get('radius', special.get('aoe_radius', 4)))
        turns = int(band.get('turns', special.get('status_duration', 3)))
        room = int(band.get('max_held', 99))
        near = near_dance(self.monsters, pet, self.dungeon, radius)
        near.sort(key=lambda m: (max(abs(m.x - pet.x), abs(m.y - pet.y)), m.x, m.y))
        visible = getattr(self, 'visible', set()) or set()
        line = band.get('line') or lines.get('dance', '')
        self.add_message(line.replace('{pet}', pet.name), 'success')
        held = 0
        for m in near:
            seen = (m.x, m.y) in visible and getattr(m, '_unseen', False) is not True
            why = why_unmoved(m)
            if why is None:
                if held >= room:
                    continue                 # the dance held only so many
                m.hold('stunned', turns)
                if m.has_effect('stunned'):
                    held += 1
                    if seen:
                        self.add_message(fill(m, lines.get('held', '')), 'success')
                    continue
                why = 'unmoved'
            if seen:
                key = {'named': 'unmoved_named', 'mindless': 'unmoved_mindless',
                       'blind': 'blind'}.get(why, 'unmoved')
                if lines.get(key):
                    self.add_message(fill(m, lines[key]), 'info')
        if not near and lines.get('nobody'):
            self.add_message(lines['nobody'].replace('{pet}', pet.name), 'info')
        if (pet.stage >= int(special.get('lift_debuff_stage', 99))
                and band.get('lift', not band)):
            self._mooble_lift_debuff(lines)
        return held

    def _mooble_lift_debuff(self, lines: dict):
        """One hindrance off the hero: the worst first (a hold before a
        slower harm), the one with longest to run among equals."""
        from status_effects import DEBUFFS, HARD_CONTROL, EFFECT_INFO
        effects = getattr(self.player, 'status_effects', None) or {}
        active = [e for e in effects if e in DEBUFFS]
        if not active:
            return None

        def worst(e):
            left = effects.get(e, 0)
            return (e in HARD_CONTROL, left if isinstance(left, int) and left > 0 else 9999)
        gone = max(active, key=worst)
        effects.pop(gone, None)
        label = (EFFECT_INFO.get(gone) or (gone.replace('_', ' '),))[0]
        if lines.get('lift'):
            self.add_message(lines['lift'].replace('{effect}', str(label).lower()), 'success')
        return gone

    def _pet_gift_lines(self, pet) -> list:
        """The Mooble's gifts on his card (the pet menu)."""
        from fantasy_ui import FP
        species = getattr(pet, 'species', None) or {}
        gift = species.get('mana_gift')
        if not gift:
            return []
        p = data().get('pet') or {}
        every = pet.mana_gift_every() if hasattr(pet, 'mana_gift_every') else gift.get('every', 5)
        out = [(p.get('card_gift', '').format(radius=gift.get('radius', 3), amount=gift.get('amount', 1),
                                              every=every), FP.SUCCESS_TEXT, self.font_sm)]
        if any(s.get('effect') == 'dance_of_the_dark' for s in species.get('specials', ())):
            out.append((p.get('card_dance', ''), FP.FADED_TEXT, self.font_sm))
            if pet.stage >= 2:
                out.append((p.get('card_lift', ''), FP.FADED_TEXT, self.font_sm))
        return out

    # ---- QA (Titivillus, Shift+D) -----------------------------------------

    def _qa_mooble(self):
        """Titivillus QA build only: the Mooble set down in a cave beside
        this room (his floor this run becomes this floor), a Starnut and a
        Starnut Tart in the pack; pressed again with him here, another tart
        and the wait between dances waived."""
        if not getattr(self.player, 'qa_tools', False):
            return
        st = self._mooble_state()
        m = self._mooble_here()
        if m is None:
            st.update({'floor': self.dungeon_level, 'spawned': False, 'outcome': None})
            self._maybe_spawn_mooble(self.dungeon_level)
            m = self._mooble_here()
            if m is None:
                self.add_message("[QA] No room for the Mooble here.", 'info')
                return
            self._qa_beside_mooble(m)
            self.add_message("[QA] You are beside the Mooble. A Starnut and a Starnut Tart are "
                             "in your pack. Shift+D again: another tart, and no wait before "
                             "the next dance.", 'info')
        else:
            self._qa_beside_mooble(m)
            st['last_turn'] = None
            st['away'] = False
            st.pop('choose_failed', None)
            self.add_message(f"[QA] No wait before the next dance. Dances won: {dances(m)}.", 'info')
        for make in (make_starnut, make_tart):
            it = make(self.player.x, self.player.y)
            if it is not None and not self.player.add_to_inventory(it):
                self.player.inventory.append(it)

    def _qa_beside_mooble(self, m) -> bool:
        """QA: the hero set down on the open tile nearest the Mooble (in his
        cave), so a test run need not go looking for him."""
        taken = {(o.x, o.y) for o in self.monsters if getattr(o, 'alive', True)}
        best = None
        for r in range(1, 6):
            ring = [(m.x + dx, m.y + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                    if max(abs(dx), abs(dy)) == r]
            free = [t for t in ring if self.dungeon.is_walkable(*t) and t not in taken]
            if free:
                best = min(free, key=lambda t: (abs(t[0] - m.x) + abs(t[1] - m.y), t))
                break
        if best is None:
            return False
        self.player.x, self.player.y = best
        self._refresh_fov()
        return True

    # ---- drawing ------------------------------------------------------------

    def _draw_mooble_encounter(self):
        """His screen: his picture on the left (on his ledge, or down on the
        cave floor), the phase's words or choices on the right. Sized to
        what the phase holds and centred, like the Emberpup's."""
        import pygame
        import layout
        import lore_art
        from ui_scale import px as S
        from fantasy_ui import (FP, get_font, draw_dark_panel, draw_header_bar, draw_divider,
                                draw_overlay, panel_band, key_hints_height, display_text)
        from game_render import _centre_x, _centre_y
        d = data()
        m = getattr(self, '_mooble_npc', None)
        phase = getattr(self, '_mooble_phase', 'options')
        border = FP.AMBER_ACCENT

        draw_overlay(self.screen, 190)
        kit = bool(panel_band('panel', pygame.Rect(0, 0, S(860), S(400))))
        bw = min(S(860), layout.WINDOW_W - S(48))
        b = S(16) if kit else 0
        inner_w = bw - 2 * (b + S(28)) if kit else bw - 2 * S(30)
        pic = lore_art.plate('monster', sprite_of(m) if m is not None else art(d['sprite_ledge']), S(192))
        pic_w = (pic.get_width() + S(24)) if pic is not None else 0
        text_w = inner_w - pic_w
        font = get_font('body', 18)
        line_h = font.get_height() + S(4)
        row_h = S(50)

        def text_h(paras):
            n = sum(len(self._wrap_text(display_text(p), font, text_w)) for p in paras)
            return n * line_h + max(0, len(paras) - 1) * S(10)

        keys = (('1', 'practice'), ('2', 'dance'), ('3', 'tart'), ('4', 'choose'), ('5', 'leave'))
        if phase == 'story':
            paras = list(d['story'])
            content_h = text_h(paras)
        elif phase == 'options':
            # Too soon for the dance-off: his line says so (practice is on).
            soon = m is not None and has_tart(m) and self._mooble_too_soon(m)
            paras = [(too_soon_line(m) if soon else waiting_text(m)) if m is not None else '']
            content_h = text_h(paras) + S(14) + len(keys) * (row_h + S(8))
        else:
            paras = [getattr(self, '_mooble_text', '') or '']
            content_h = text_h(paras)
        content_h = max(content_h, pic.get_height() + S(8) if pic is not None else 0)
        head_h = S(48)
        foot_h = S(8) + key_hints_height() + S(32)
        bh = 2 * b + head_h + S(18) + content_h + S(10) + foot_h
        bh = max(S(240), min(bh, layout.WINDOW_H - S(48)))
        bx = _centre_x(bw)
        by = _centre_y(bh)
        panel = pygame.Rect(bx, by, bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        if panel_band('panel', panel):
            b = panel_band('panel', panel)
            body_top = self._ui_header(panel, d['title'], border_color=border, h=48)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body_rect = pygame.Rect(bx + b + S(28), body_top + S(4),
                                    bw - 2 * (b + S(28)), foot_bottom - body_top - S(4))
        else:
            draw_header_bar(self.screen, (bx, by, bw, S(44)), text=d['title'],
                            font=get_font('heading', 20), text_color=FP.GOLD_BRIGHT,
                            accent=border, frame=(panel, border))
            draw_divider(self.screen, bx + S(20), by + S(54), bw - 2 * S(20))
            body_rect = pygame.Rect(bx + S(30), by + S(72), bw - 2 * S(30), bh - S(124))

        if pic is not None:
            well = pygame.Rect(body_rect.x, body_rect.y, pic.get_width() + S(8), pic.get_height() + S(8))
            pygame.draw.rect(self.screen, FP.MIDNIGHT, well)
            self.screen.blit(pic, (well.x + S(4), well.y + S(4)))
            pygame.draw.rect(self.screen, border, well, 1)
        tx = body_rect.x + pic_w
        col = pygame.Rect(tx, body_rect.y, body_rect.right - tx, body_rect.h)
        y = col.y
        for i, p in enumerate(paras):
            if i:
                y += S(10)
            y = self._ui_wrap_text(display_text(p), font, FP.PARCHMENT_LIGHT,
                                   pygame.Rect(col.x, y, col.w, col.bottom - y), line_gap=4)
        if phase == 'story':
            self._ui_footer(panel, "Enter / Space: continue   |   Esc: walk away")
        elif phase == 'options':
            y += S(14)
            for key, which in keys:
                self._ui_action_row(pygame.Rect(col.x, y, col.w, row_h), key,
                                    display_text(d['options'][which]), color=FP.PARCHMENT_LIGHT)
                y += row_h + S(8)
            self._ui_footer(panel, "1-5: choose   |   Esc: leave him be")
        else:
            self._ui_footer(panel, "Enter / Space / Esc: continue")
