"""The Bococho: a racing camp in the Underway, every run, earned.

Brandon, 2026-11-14 (RARE_PETS_PLAN_2026_11_14 section 3): "add two more
rare pets... through little quests like emberpup and unicorn... something
about racing for the chocobo." The Bococho is a homage, never a copy: our
own golden riding bird, with her own call (a rolling "whirrup").

Every run, on one floor of 51-65 (``first_floor`` to ``last_floor``), a
racing camp stands in a cavern room: tether posts, a betting board, Gilt
Varro the race-runner (he), two of his birds on short tethers (harmless
while tethered), and the young Bococho (she), wary of everyone. The story
leads:

  * **Meet her.** She shies away: someone has handled her roughly.
  * **Feed her Sunroot, twice** (``feeds_needed``), at least
    ``feed_gap_turns`` apart; leaving the floor counts as waiting. Back too
    soon, and she is still crunching the last root (``too_soon``, one line
    per feed so far): nothing counts and no turn passes. Each feed has its
    own line (``fed``), and her screen says where her trust stands
    (``waiting``). Only Sunroot will do (``not_sunroot``, ``no_food``).
  * **Challenge Varro.** Trusting the hero, she will run for him. Varro
    takes a fee (``race_fee_share`` of a floor's gold, ``economy.share``),
    and the race is run on the Underway Run, a side floor (src/game_race.py,
    src/race.py, src/underway_run.py).
  * **Win,** and Varro storms off; his birds are cut loose and run off.
    She stays: "I choose you!" asks the animal quiz (``quiz``), as for the
    Emberpup. Pass, and she joins as a Bococho (pet_system ``bococho``,
    level ``pet.start_level``), under the one-companion rule, with the
    naming popup. Fail, and ask again after the gap.
  * **Lose,** and try again after the gap; Varro gloats and takes the fee
    again.
  * **Strike Varro** (his screen's third choice) and there is no race. He
    fights (a real fight for his floor; he never starts one), and the young
    Bococho tears her rope and bolts: she will not trust a hero who fights
    in front of her (the choice made here, 2026-11-14: the brief asked "she
    won't trust a hero who kills in front of her"). Killing him moves no
    karma (he is nobody's innocent); when he falls his birds pull free and
    run.

Run state lives in ``game._bococho`` (saved): the floor, placed yet, how it
ended ('fled' or 'adopted'), feeds, the waits ('waits': the turn a wait
began, by kind: 'feed', 'race', 'choose'; leaving the floor clears them),
the race won, Varro's state, and an unfinished race ('race', src/race.py).
The creatures carry ``_bococho_role`` ('young', 'varro', 'bird'; 'racer'
on the track). Every word and number is in data/bococho.json.
"""
from __future__ import annotations

import json
import os
import random

from game_states import STATE_PLAYER, STATE_QUIZ, STATE_BOCOCHO, STATE_PET_NAME_INPUT

_DATA: dict | None = None
_ART: dict = {}


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'bococho.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


# ---------------------------------------------------------------------------
# The run's roll
# ---------------------------------------------------------------------------

def roll_floor(rng) -> int | None:
    """The camp's floor this run (every run, with chance_per_run 1.0)."""
    d = data()
    if rng.random() >= float(d['chance_per_run']):
        return None
    return rng.randint(int(d['first_floor']), int(d['last_floor']))


def _run_rng() -> random.Random:
    """The run's own generator for the camp, seeded from the shared stream
    without moving it (the Emberpup's way), so seeded floors are as before."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return random.Random(seed ^ 0xB0C0C0)


def new_run_state() -> dict:
    rng = _run_rng()
    return {'floor': roll_floor(rng), 'spawned': False, 'outcome': None,
            'seed': rng.getrandbits(32), 'feeds': 0, 'waits': {},
            'won': False, 'races': 0, 'race': None, 'varro': 'camp'}


def old_save_state() -> dict:
    """A save from before the Bococho keeps a run without her (the floors she
    could wait on may be behind the hero)."""
    return {'floor': None, 'spawned': False, 'outcome': None, 'seed': 0, 'feeds': 0,
            'waits': {}, 'won': False, 'races': 0, 'race': None, 'varro': 'camp'}


# ---------------------------------------------------------------------------
# Pictures
# ---------------------------------------------------------------------------

def sprite(sid: str) -> str:
    """``sid`` when its picture is installed, else the stand-in the data
    names (never a letter glyph). The art run installs the real ones
    (tools/content/genart/install_rare_pets.py)."""
    if sid in _ART:
        return _ART[sid]
    from paths import data_path
    have = os.path.exists(data_path('assets', 'tiles', 'monsters', sid + '.png'))
    out = sid if have else (data()['sprites'].get('fallback', {}).get(sid) or sid)
    _ART[sid] = out
    return out


# ---------------------------------------------------------------------------
# Who is who
# ---------------------------------------------------------------------------

def role(m) -> str:
    return str(getattr(m, '_bococho_role', '') or '')


def is_young(m) -> bool:
    return role(m) == 'young'


def is_varro(m) -> bool:
    return role(m) == 'varro'


def is_bird(m) -> bool:
    return role(m) == 'bird'


def needed() -> int:
    return int(data().get('feeds_needed', 2))


def feeds(st: dict) -> int:
    return int((st or {}).get('feeds', 0) or 0)


def trusts(st: dict) -> bool:
    return feeds(st) >= needed()


def too_soon_line(st: dict) -> str:
    lines = data().get('too_soon') or ['']
    return lines[max(0, min(feeds(st), len(lines)) - 1)]


def waiting_text(st: dict) -> str:
    d = data()
    if (st or {}).get('won'):
        return d['waiting_won']
    lines = d.get('waiting') or ['']
    return lines[min(feeds(st), len(lines) - 1)]


def fee(level: int) -> int:
    """Varro's fee on the camp's floor: a share of a floor's gold."""
    import economy
    return int(economy.share(int(level or 1), float(data().get('race_fee_share', 0.25))))


def sunroot_in(inventory):
    """A Sunroot in the pack, or None."""
    want = data().get('food_id', 'sunroot')
    return next((i for i in inventory if getattr(i, 'id', None) == want), None)


def other_food(inventory):
    """Any other food or ingredient the hero might hold out, or None."""
    from items import Food, Ingredient
    return next((i for i in inventory if isinstance(i, (Food, Ingredient))
                 and getattr(i, 'id', None) != data().get('food_id', 'sunroot')), None)


def creature_defn(which: str, level: int) -> dict:
    """The camp's people and birds, from the data: Varro a man of the
    world (a fight only when struck), the birds harmless."""
    d = data()
    if which == 'varro':
        v = d['varro']
        return {
            'id': v['id'], 'name': v['name'], 'symbol': v['symbol'], 'pronoun': v['pronoun'],
            'color': list(v['color']), 'hp': v['hp'], 'thac0': int(v['thac0']),
            'speed': int(v['speed']), 'attacks': [dict(a) for a in v['attacks']],
            'ai_pattern': 'sessile', 'resistances': [], 'weaknesses': [],
            'family': v.get('family', 'mortals'), 'min_level': level, 'peak_floor': level,
            'is_allied': True, 'lore': v.get('lore', ''),
            'kill_chronicle': v.get('kill_chronicle', ''),
            'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None,
            'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        }
    spec = d['young'] if which == 'young' else d['varro_bird']
    sid = d['sprites']['young'] if which == 'young' else d['sprites']['varro_bird']
    return {
        'id': sid, 'name': spec['name'], 'symbol': spec['symbol'], 'pronoun': spec['pronoun'],
        'color': list(spec['color']), 'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [],
        'ai_pattern': 'sessile', 'resistances': [], 'weaknesses': [], 'family': 'birds',
        'min_level': level, 'is_allied': True,
        'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None,
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
    }


def make_creature(which: str, x: int, y: int, level: int):
    from monster import Monster
    m = Monster(creature_defn(which, level), x, y)
    m._bococho_role = which
    m.sprite_id = sprite(m.kind)
    m._no_corpse = which != 'varro'
    return m


def _room_of(rooms, x: int, y: int):
    for r in rooms:
        if r.x <= x < r.x + r.width and r.y <= y < r.y + r.height:
            return r
    return None


def _against_wall(dungeon, room, taken) -> list:
    """The room's floor tiles with a wall beside them (not a doorway, not a
    corridor mouth): where a tether post can stand."""
    from dungeon import FLOOR, WALL
    out = []
    for x, y in room.inner_tiles():
        if (x, y) in taken or dungeon.tiles[y][x] != FLOOR:
            continue
        sides = [dungeon.tiles[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if WALL in sides and all(t in (FLOOR, WALL) for t in sides):
            near_door = any(dungeon.tiles[y + dy][x + dx] not in (FLOOR, WALL)
                            for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if not near_door:
                out.append((x, y))
    return out


def place_camp(dungeon, room, level: int, rng, taken=(), spacing: int = 2) -> list:
    """Set the camp down in ``room``: tether posts against its walls, a bird
    at each (Varro's two, then the young one), the betting board, and Varro
    beside it, each fixture more than ``spacing`` tiles from the last. Never
    cuts the floor off (decor's reach check). Returns the creatures placed
    ([] when the room has no room)."""
    import decor
    d = data()
    taken = set(taken)
    spots = _against_wall(dungeon, room, taken)
    rng.shuffle(spots)
    before = decor._reachable_count(dungeon)
    posts = []
    for pos in spots:
        if len(posts) >= int(d['camp']['posts']) + 1:     # the posts, then the board
            break
        if any(max(abs(pos[0] - p[0]), abs(pos[1] - p[1])) <= spacing for p in posts):
            continue
        fid = d['camp']['post_fixture'] if len(posts) < int(d['camp']['posts']) else d['camp']['board_fixture']
        decor.place(dungeon, pos, fid)
        if before >= 0 and decor._reachable_count(dungeon) < before - 1:
            decor.remove(dungeon, pos)
            continue
        before = decor._reachable_count(dungeon)
        posts.append(pos)
    if len(posts) < int(d['camp']['posts']) + 1:
        for pos in posts:
            decor.remove(dungeon, pos)
        return []
    taken |= set(posts)

    def beside(pos):
        free = [(pos[0] + dx, pos[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                                          (1, 1), (-1, 1), (1, -1), (-1, -1))]
        free = [t for t in free if dungeon.is_walkable(*t) and t not in taken
                and t not in dungeon.__dict__.get('fixture_blocks', ())
                and room.x < t[0] < room.x + room.width - 1 and room.y < t[1] < room.y + room.height - 1]
        return free[0] if free else None

    out = []
    roles = ['bird', 'bird', 'young', 'varro']
    for pos, which in zip(posts, roles):
        spot = beside(pos)
        if spot is None:
            # Somebody has no room at his post: the camp goes elsewhere.
            for p in posts:
                decor.remove(dungeon, p)
            return []
        taken.add(spot)
        m = make_creature(which, spot[0], spot[1], level)
        m._bococho_post = pos
        out.append(m)
    return out


class BocochoMixin:
    """The camp's side: spawn, the two screens, the feeds, the challenge,
    Varro's fall, the adoption, QA. Drawing is
    game_bococho_render.BocochoRenderMixin; the race is game_race.RaceMixin."""

    # ---- state -------------------------------------------------------------

    def _bococho_state(self) -> dict:
        st = self.__dict__.get('_bococho')
        if not isinstance(st, dict):
            st = old_save_state()
            self._bococho = st
        st.setdefault('waits', {})
        return st

    def _bococho_left(self, from_level: int, to_level: int | None = None):
        """Leaving the camp's floor is waiting: every wait is over (Game.
        _change_level)."""
        st = self._bococho_state()
        if from_level == st.get('floor') and to_level != from_level:
            st['waits'] = {}

    def _bococho_waiting(self, kind: str) -> bool:
        """Is a wait of ``kind`` ('feed', 'race', 'choose') still running?"""
        st = self._bococho_state()
        start = (st.get('waits') or {}).get(kind)
        if start is None:
            return False
        gap = int(data().get('feed_gap_turns', 25))
        return int(getattr(self, 'turn_count', 0)) - int(start) < gap

    def _bococho_wait_from_now(self, kind: str):
        self._bococho_state().setdefault('waits', {})[kind] = int(getattr(self, 'turn_count', 0))

    # ---- spawn -------------------------------------------------------------

    def _maybe_spawn_bococho(self, level: int):
        """Set the camp up on its floor, once a run, on first arrival: in the
        biggest ordinary room that is not the first (the hero's) room."""
        st = self._bococho_state()
        if st.get('spawned') or st.get('outcome') or st.get('floor') != level:
            return
        if any(role(m) for m in self.monsters):
            st['spawned'] = True
            return
        rng = random.Random(int(st.get('seed', 0) or 0) * 131 + int(level))
        rooms = list(self.dungeon.rooms)
        here = _room_of(rooms, self.player.x, self.player.y)
        import decor
        special = {id(r) for r in decor._skip_rooms(self.dungeon)}
        picks = [r for r in rooms[1:] if r is not here and id(r) not in special
                 and (r.width - 2) * (r.height - 2) >= int(data()['camp']['min_room_tiles'])]
        picks.sort(key=lambda r: -(r.width * r.height))
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters)) | set(self._occupants())
        taken |= {(i.x, i.y) for i in self.ground_items if hasattr(i, 'x')}
        # Every run must find its camp: a tighter room takes the posts closer
        # together, and as a last resort the hero's own room will do.
        order = picks + [r for r in rooms if r not in picks and r is not here]
        if here is not None:
            order.append(here)
        for spacing in (2, 1, 0):
            for room in order:
                placed = place_camp(self.dungeon, room, level, rng, taken, spacing)
                if placed:
                    self.monsters.extend(placed)
                    st['spawned'] = True
                    st['room'] = [room.x, room.y, room.width, room.height]
                    return

    def _bococho_refresh_art(self):
        """A creature saved before its picture was installed shows it now."""
        for m in self.monsters or ():
            if role(m) in ('young', 'varro', 'bird', 'racer'):
                want = sprite(m.kind)
                if getattr(m, 'sprite_id', None) != want:
                    m.sprite_id = want

    def _bococho_here(self, which: str):
        return next((m for m in self.monsters or () if role(m) == which and m.alive), None)

    # ---- bumping -----------------------------------------------------------

    def _bococho_bump(self, target) -> bool:
        """The hero walked into one of the camp's creatures: True when its
        screen or line answered (no attack). Varro once struck is a foe."""
        r = role(target)
        if not r:
            return False
        if r == 'varro' and getattr(target, '_bococho_hostile', False):
            return False
        if r == 'bird':
            self.add_message(data()['varro_bird']['bump'], 'info')
            return True
        if r == 'racer':
            self.add_message(data()['race']['how'], 'info')
            return True
        self._bococho_open(r, target)
        return True

    # ---- the screen --------------------------------------------------------

    def _bococho_open(self, who: str, m):
        st = self._bococho_state()
        self._bc_npc = m
        self._bc_who = who
        met_key = 'met_young' if who == 'young' else 'met_varro'
        first = not st.get(met_key)
        st[met_key] = True
        self._bc_phase = 'story' if first else 'options'
        self._bc_text = ''
        self._bc_after = 'options'
        self._bc_acted = False
        self.state = STATE_BOCOCHO
        if who == 'young' and not first and not st.get('won') and self._bococho_waiting('feed') \
                and not trusts(st):
            # Too soon: no choices, no turn spent. Come back in a while.
            self._bococho_outcome(too_soon_line(st), 'player')

    def _bococho_outcome(self, text: str, after: str):
        self._bc_text = text
        self._bc_after = after
        self._bc_phase = 'outcome'

    def _close_bococho(self):
        acted = getattr(self, '_bc_acted', False)
        self._bc_npc = None
        self._bc_phase = 'story'
        self._bc_acted = False
        self.state = STATE_PLAYER
        if acted:
            self._advance_turn()

    def _bococho_input(self, key: int):
        import pygame
        phase = getattr(self, '_bc_phase', 'options')
        if getattr(self, '_bc_npc', None) is None and phase != 'outcome':
            self.state = STATE_PLAYER
            return
        if phase == 'story':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._bc_phase = 'options'
            elif key == pygame.K_ESCAPE:
                self._close_bococho()
            return
        if phase == 'outcome':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                after = self._bc_after
                if after == 'options' and self._bc_npc is not None:
                    self._bc_phase = 'options'
                elif after == 'name':
                    self._bc_open_naming()
                elif after == 'race':
                    self._bc_npc = None
                    self.state = STATE_PLAYER
                    self._enter_underway_run()
                else:
                    self._close_bococho()
            return
        if getattr(self, '_bc_who', 'young') == 'varro':
            if key in (pygame.K_1, pygame.K_KP1):
                self._bc_challenge()
            elif key in (pygame.K_2, pygame.K_KP2, pygame.K_ESCAPE):
                self._bc_leave_varro()
            elif key in (pygame.K_3, pygame.K_KP3):
                self._bc_strike()
            return
        if key in (pygame.K_1, pygame.K_KP1):
            self._bc_feed()
        elif key in (pygame.K_2, pygame.K_KP2, pygame.K_ESCAPE):
            self._bc_ignore()
        elif key in (pygame.K_3, pygame.K_KP3):
            self._bc_choose()

    def _bococho_options(self) -> list:
        """[(key, label)] for the screen's choices."""
        d = data()
        if getattr(self, '_bc_who', 'young') == 'varro':
            f = fee(self._bococho_state().get('floor') or self.dungeon_level)
            o = d['options_varro']
            return [('1', o['challenge'].format(fee=f'{f:,}')), ('2', o['leave']), ('3', o['strike'])]
        o = d['options_young']
        return [('1', o['feed']), ('2', o['ignore']), ('3', o['choose'])]

    def _bococho_waiting_text(self) -> str:
        st = self._bococho_state()
        d = data()
        if getattr(self, '_bc_who', 'young') == 'varro':
            f = f"{fee(st.get('floor') or self.dungeon_level):,}"
            w = d['varro_waiting']
            if int(st.get('races', 0) or 0) > 0:
                return w['lost'].format(fee=f)
            return (w['trusted'] if trusts(st) else w['untrusted']).format(fee=f)
        return waiting_text(st)

    # ---- the young Bococho -------------------------------------------------

    def _bc_feed(self):
        d = data()
        st = self._bococho_state()
        if not trusts(st) and self._bococho_waiting('feed'):
            self._bococho_outcome(too_soon_line(st), 'options')
            return
        root = sunroot_in(self.player.inventory)
        if root is None:
            other = other_food(self.player.inventory)
            if other is not None:
                self._bococho_outcome(d['not_sunroot'].format(food=self._bare_name_one(other)),
                                      'options')
            else:
                self._bococho_outcome(d['no_food'], 'options')
            return
        if getattr(root, 'count', 1) > 1:
            root.count -= 1
        else:
            self.player.remove_from_inventory(root)
        self._bc_acted = True
        before = feeds(st)
        self.add_message(d['log']['fed'], 'success')
        if before >= needed():
            self._bococho_outcome(d['fed_again'], 'options')
            return
        st['feeds'] = before + 1
        self._bococho_wait_from_now('feed')
        if before == 0:
            import deeds
            deeds.note(self, 'aid.bococho', source='bococho', unique=True)
        lines = d['fed']
        self._bococho_outcome(lines[min(before, len(lines) - 1)], 'options')

    def _bc_ignore(self):
        self.add_message(data()['ignore'], 'info')
        self._close_bococho()

    def _bc_choose(self):
        d = data()
        st = self._bococho_state()
        pup = self._bc_npc
        if feeds(st) <= 0:
            self._bococho_outcome(d['refused'], 'options')
            return
        if not trusts(st):
            self._bococho_outcome(d['refused_trust'], 'options')
            return
        if not st.get('won'):
            self._bococho_outcome(d['refused_tethered'], 'options')
            return
        if self._bococho_waiting('choose'):
            self._bococho_outcome(d['refused_soon'], 'options')
            return
        q = d['quiz']
        subject, tier, need = q['subject'], int(q['tier']), int(q['threshold'])
        self.quiz_title = d['quiz_title']
        self.state = STATE_QUIZ

        def on_complete(result):
            self._bc_npc = pup
            if result.success:
                self._bc_adopt(pup)
            else:
                self._bococho_wait_from_now('choose')
                self.add_message(d['log']['shied'], 'info')
                self._bc_acted = True
                self._bococho_outcome(d['fail'], 'player')
                self.state = STATE_BOCOCHO

        self.quiz_engine.start_quiz(
            mode='threshold', subject=subject, tier=tier, callback=on_complete,
            threshold=need,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )

    def _bc_adopt(self, bird):
        """She joins you, through the path a Soul Sphere pet takes: one
        companion at a time, then the naming popup."""
        from pet_system import Pet
        d = data()
        x, y = bird.x, bird.y
        bird.alive = False                       # she came with you: not a kill
        try:
            self.monsters.remove(bird)
        except ValueError:
            pass
        st = self._bococho_state()
        st['outcome'] = 'adopted'
        import deeds
        deeds.note(self, 'saved.bococho', source='bococho', unique=True)
        pet = Pet(d['pet']['species_key'], x, y, level=int(d['pet']['start_level']))
        self._companions_to_stasis()            # one companion at a time
        self.pets.append(pet)
        self._bc_new_pet = pet
        self._sync_saddlebags()
        self.add_message(d['log']['joined'], 'success')
        self._bococho_outcome(d['pass'], 'name')
        self.state = STATE_BOCOCHO

    def _bc_open_naming(self):
        d = data()
        pet = getattr(self, '_bc_new_pet', None)
        self._bc_npc = None
        self._bc_new_pet = None
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

    # ---- Gilt Varro --------------------------------------------------------

    def _bc_challenge(self):
        d = data()
        st = self._bococho_state()
        f = fee(st.get('floor') or self.dungeon_level)
        if not trusts(st):
            self._bococho_outcome(d['challenge_untrusted'], 'options')
            return
        if self._bococho_waiting('race'):
            self._bococho_outcome(d['challenge_soon'], 'options')
            return
        if self._payment_plan(f) is None:
            self._bococho_outcome(d['challenge_poor'].format(fee=f'{f:,}'), 'options')
            return
        self._pay_gold(f, who=d['varro']['name'])
        st['fee_paid'] = f
        self.add_message(d['log']['challenged'].format(fee=f'{f:,}'), 'info')
        self._bococho_outcome(d['challenge_accepted'].format(fee=f'{f:,}'), 'race')

    def _bc_leave_varro(self):
        self.add_message(data()['leave_varro'], 'info')
        self._close_bococho()

    def _bc_strike(self):
        """No race now: Varro fights, and she bolts."""
        d = data()
        st = self._bococho_state()
        varro = self._bc_npc
        self._bococho_turn_hostile(varro)
        young = self._bococho_here('young')
        if young is not None:
            young.alive = False                  # she ran: not a kill
            try:
                self.monsters.remove(young)
            except ValueError:
                pass
        st['outcome'] = 'fled'
        self.add_message(d['log']['bolted'], 'danger')
        self._chron('deed', d['strike_chronicle'], source='bococho')
        self._bc_acted = True
        self._bc_npc = None
        self._bococho_outcome(f"{d['strike']} {d['strike_bolts']}", 'player')

    def _bococho_turn_hostile(self, varro):
        if varro is None:
            return
        varro._bococho_hostile = True
        varro.is_allied = False
        varro.ai_pattern = 'aggressive'
        varro._aware = True
        varro._tracking = True
        self._bococho_state()['varro'] = 'hostile'

    def _bococho_monster_died(self, monster):
        """Varro fell: no karma (he is nobody's innocent); his birds pull
        free and run. Called from the kill handler."""
        if not is_varro(monster):
            return
        d = data()
        st = self._bococho_state()
        st['varro'] = 'slain'
        if st.get('outcome') is None:
            st['outcome'] = 'fled'
        import deeds
        deeds.note(self, 'slew.gilt_varro', source='bococho', unique=True)
        if d['varro'].get('kill_chronicle'):
            self._chron('boss', d['varro']['kill_chronicle'], once='bococho:varro')
        self._bococho_birds_run(d['varro_dies_birds'])

    def _bococho_birds_run(self, line: str = '') -> int:
        birds = [m for m in self.monsters if is_bird(m)]
        if not birds:
            return 0
        for b in birds:
            b.alive = False
        self.monsters[:] = [m for m in self.monsters if not is_bird(m)]
        if line:
            self.add_message(line, 'info')
        return len(birds)

    def _bococho_after_race(self, won: bool):
        """Back at the camp from the Underway Run (game_race)."""
        d = data()
        st = self._bococho_state()
        if won:
            st['won'] = True
            varro = self._bococho_here('varro')
            if varro is not None:
                varro.alive = False             # he left: not a kill
                self.monsters.remove(varro)
            st['varro'] = 'gone'
            lines = d['won_back']
            for line in lines[:1]:
                self.add_message(line, 'success')
            self._bococho_birds_run(lines[1] if len(lines) > 1 else '')
            for line in lines[2:]:
                self.add_message(line, 'success')
            self.add_message(d['log']['varro_left'], 'success')
        else:
            self._bococho_wait_from_now('race')
            self.add_message(d['lost_back'], 'warning')

    # ---- every turn --------------------------------------------------------

    def _bococho_tick(self):
        st = self._bococho_state()
        if st.get('floor') == getattr(self, 'dungeon_level', None):
            self._bococho_refresh_art()

    # ---- QA (Titivillus, Shift+G) ------------------------------------------

    def _qa_bococho(self):
        """Titivillus QA build only: the camp set up in the room the hero is
        in (this floor becomes the camp's floor), and two Sunroots in the
        pack. Pressed again with the camp here: her trust (the two feeds
        counted) and two more Sunroots; once more: she joins at once, the
        race skipped, to try riding (the naming popup opens)."""
        if not getattr(self.player, 'qa_tools', False):
            return
        d = data()
        st = self._bococho_state()

        def roots():
            from items import load_items, copy_at, grant_identified
            tpl = next((i for i in load_items('ingredient')
                        if getattr(i, 'id', '') == d['food_id']), None)
            if tpl is None:
                return
            r = copy_at(tpl, self.player.x, self.player.y)
            r.count = 2
            grant_identified(self, r)
            if not self.player.add_to_inventory(r):
                self.ground_items.append(r)
        young = self._bococho_here('young')
        if young is not None and st.get('floor') == self.dungeon_level:
            if not trusts(st):
                # Second press: her trust (the feeds counted) and two more roots.
                st['feeds'] = needed()
                st['waits'] = {}
                roots()
                self.add_message(d['qa']['again'], 'info')
                return
            # Third press: she joins at once, the race skipped (to try riding).
            st['won'] = True
            self._bc_npc = young
            self._bc_adopt(young)
            self.add_message(d['qa']['joined'], 'info')
            return
        from boss_levels import is_side_floor
        if is_side_floor(self.dungeon_level):
            self.add_message(d['qa']['no_room'], 'info')
            return
        room = _room_of(self.dungeon.rooms, self.player.x, self.player.y)
        rooms = [room] if room is not None else []
        rooms += sorted((r for r in self.dungeon.rooms if r is not room),
                        key=lambda r: abs(r.x - self.player.x) + abs(r.y - self.player.y))
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters)) | set(self._occupants())
        taken |= {(i.x, i.y) for i in self.ground_items if hasattr(i, 'x')}
        rng = random.Random(int(st.get('seed', 0) or 0) + int(self.turn_count))
        for r in rooms:
            placed = place_camp(self.dungeon, r, int(self.dungeon_level), rng, taken)
            if placed:
                self.monsters.extend(placed)
                st.update({'floor': int(self.dungeon_level), 'spawned': True, 'outcome': None,
                           'feeds': 0, 'waits': {}, 'won': False, 'races': 0, 'race': None,
                           'varro': 'camp', 'room': [r.x, r.y, r.width, r.height]})
                st.pop('met_young', None)
                st.pop('met_varro', None)
                # A track already raced this run is struck: the next race builds it fresh.
                from boss_levels import UNDERWAY_RUN
                saved = getattr(getattr(self, 'level_mgr', None), '_saved', None)
                if isinstance(saved, dict):
                    saved.pop(UNDERWAY_RUN, None)
                roots()
                self.add_message(d['qa']['placed'].format(floor=self.dungeon_level), 'info')
                return
        self.add_message(d['qa']['no_room'], 'info')
