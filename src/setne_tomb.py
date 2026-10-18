"""Setne's Tomb and the Book of Thoth (DEEDS_KARMA_DESIGN 11.12;
ENCOUNTER_STORIES_DRAFT H00 and C19).

The tomb is a sealed room on one floor of 45-65, rolled for the run like the
Emberpup's and the Black Knight's floors (its own generator, seeded from the
shared stream without moving it). Two ghosts wait inside: Prince Neferkaptah,
whose encounter is ordinary encounter data (``data/setne_tomb.json:
encounter``, ``callback_only`` so nothing else rolls it), and his wife Ahwere
beside him. The room has one door; the floor flood fill and every spawner
treat it like any other door, so the room is four-way reachable.

What the encounter's outcomes can ask of this system:

* ``seal_door`` (any outcome): when its page closes the door becomes wall
  for good, and a hero standing inside is put outside first.
* ``expel_up`` (the total loss at senet): the door becomes wall and the hero
  wakes on the floor above. The tomb never opens again this run.

The Book of Thoth itself (``game_magic._read_book_of_thoth`` and the altar
hook in ``main._do_drop_item``):

* Reading does not consume it. Its power is spent after one read, pass or
  fail; it renders as "Book of Thoth (Read)" and a second read does nothing.
* A failed read still lands Setne's curse, and the return is still owed.
* Laid on any altar while the oath ``thoth_return`` is open: refused unread;
  on time (deepest floor at or before the due floor) it keeps the oath
  (+1 'oath' karma into the earliest open block, tag virtue:kept); late
  (after the due floor, before the dead have come) it closes the oath as
  ``kept_late`` (0 karma, no tag, does not count toward 'faithful'), drops
  the pending callback of the dead and removes them if they already stand
  on the floor.
"""
from __future__ import annotations

import json
import random

BOSS_FLOORS = frozenset({20, 40, 60, 80})
SEED_XOR = 0x5E7E

_DATA = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'setne_tomb.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def candidate_floors() -> list:
    lo, hi = data().get('floors', [45, 65])[:2]
    return [f for f in range(int(lo), int(hi) + 1) if f not in BOSS_FLOORS]


def roll_floor(rng: random.Random) -> int:
    return rng.choice(candidate_floors())


def roll_for_new_run() -> int:
    """The tomb's floor from its own generator, seeded from the shared stream
    without disturbing it (seeded floors and captures stay unchanged)."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return roll_floor(random.Random(seed ^ SEED_XOR))


def new_run_state() -> dict:
    return {'floor': roll_for_new_run(), 'spawned': False, 'sealed': False, 'room': None}


def is_book(item) -> bool:
    return getattr(item, 'id', '') == data().get('prize_item', 'book_of_thoth')


class SetneMixin:
    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _setne_state(self) -> dict:
        st = getattr(self, '_setne', None)
        if not isinstance(st, dict):
            # A save from before the tomb keeps a run without it (the floors
            # it could stand on may be behind the hero).
            st = self._setne = {'floor': None, 'spawned': False, 'sealed': False, 'room': None}
        return st

    def _setne_encounter(self):
        """The tomb's encounter definition, priced, or None while the data
        does not have it yet."""
        from game_road import _encounter_by_tag
        _src, enc = _encounter_by_tag(data().get('encounter', ''))
        if enc is None:
            return None
        import economy
        return economy.price_encounter(enc)

    # ------------------------------------------------------------------
    # The room
    # ------------------------------------------------------------------

    def _maybe_spawn_setne_tomb(self, level: int):
        """On the first visit of the tomb's floor: carve the room, set its
        door, seat the two ghosts. Nothing happens without the encounter
        data, or after the tomb was sealed."""
        st = self._setne_state()
        if st.get('spawned') or st.get('sealed') or st.get('floor') != level:
            return
        enc = self._setne_encounter()
        if enc is None:
            return
        if enc.get('tag') in (getattr(self, '_encountered_flavor_npcs', None) or set()):
            return
        room = self._setne_carve_room()
        if room is None:
            # No solid rock to carve a room in: the ghosts sit in an ordinary
            # room instead (still reachable; nothing to seal).
            npc = self._spawn_encounter_npc(enc, '_flavor_encounter_tag', level)
            if npc is not None:
                npc.proper_noun = True
                st['spawned'] = True
            return
        from monster import Monster
        cx, cy = room['centre']
        npc = Monster(self._setne_npc_def(enc, level), cx, cy)
        npc._flavor_encounter_tag = enc['tag']
        npc.proper_noun = True
        npc._encounter_room = room
        self.monsters.append(npc)
        comp = data().get('companion') or {}
        spot = room.get('companion_at')
        if comp and spot:
            ghost = Monster(self._setne_npc_def(
                {'name': comp.get('name', 'Ahwere'), 'symbol': comp.get('symbol', '@'),
                 'color': comp.get('color', [170, 200, 220]),
                 'sprite_id': comp.get('sprite_id', 'npc_ghost')}, level), *spot)
            # She belongs to the same scene: bumping her opens it too.
            ghost._flavor_encounter_tag = enc['tag']
            ghost.proper_noun = True
            ghost._encounter_room = room
            self.monsters.append(ghost)
        st['spawned'] = True
        st['room'] = room
        msg = data().get('atmosphere')
        if msg and msg not in getattr(self.dungeon, 'atmosphere_messages', []):
            try:
                self.dungeon.atmosphere_messages.append(msg)
            except AttributeError:
                pass

    @staticmethod
    def _setne_npc_def(enc: dict, level: int) -> dict:
        return {
            'id': enc.get('sprite_id', 'npc_ghost'), 'name': enc.get('name', 'Neferkaptah'),
            'symbol': enc.get('symbol', '@'), 'color': list(enc.get('color', [200, 190, 150])),
            'hp': 1, 'thac0': 20, 'speed': 0, 'attacks': [], 'ai_pattern': 'sessile',
            'resistances': [], 'weaknesses': [], 'min_level': level, 'is_allied': True,
            'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None,
        }

    def _setne_carve_room(self):
        """A sealed 3x3 chamber off a room the hero can walk to, with one
        DOOR (bump to open). Returns the room record or None."""
        from dungeon import DOOR, _carve_sealed_shrine
        d = self.dungeon
        rooms = list(d.rooms[1:]) if len(d.rooms) > 1 else list(d.rooms)
        rng = random.Random(int(self._setne_state().get('floor') or 0) ^ SEED_XOR)
        rng.shuffle(rooms)
        from geom import all_occupied_tiles
        for r in rooms[:12]:
            carved = _carve_sealed_shrine(d, r.center)
            if not carved:
                continue
            (wx, wy), (sx, sy) = carved
            ddx = (sx - wx) // 2
            ddy = (sy - wy) // 2
            outside = (wx - ddx, wy - ddy)
            chamber = [(x, y) for x in range(sx - 1, sx + 2) for y in range(sy - 1, sy + 2)]
            d.tiles[wy][wx] = DOOR
            busy = set(all_occupied_tiles(self.monsters))
            # Anything the generator left in the new rock goes elsewhere.
            self.ground_items[:] = [g for g in self.ground_items
                                    if (g.x, g.y) not in set(chamber)]
            far = (sx + ddx, sy + ddy)               # the back row, by the bier
            side = (far[0] + ddy, far[1] + ddx)      # beside him on the back row
            if side not in chamber or side in busy:
                side = next((t for t in chamber if t not in (far, (sx, sy)) and t not in busy), None)
            return {'system': 'setne', 'door': (wx, wy), 'outside': outside,
                    'centre': far if far in chamber else (sx, sy),
                    'companion_at': side, 'chamber': chamber, 'sealed': False}
        return None

    def _setne_door_opened(self, x: int, y: int):
        """The tomb door, opened for the first time this run."""
        st = self._setne_state()
        room = st.get('room') or {}
        if st.get('floor') != getattr(self, 'dungeon_level', None) or not room:
            return
        if tuple(room.get('door') or ()) != (x, y) or room.get('announced'):
            return
        room['announced'] = True
        msg = data().get('door_message')
        if msg:
            self.add_message(msg, 'warning')

    # ------------------------------------------------------------------
    # The book: read path and the altar
    # ------------------------------------------------------------------

    def _thoth_mark_spent(self, book):
        book.spent = True
        name = data().get('spent_name')
        if name:
            book.name = name

    def _thoth_on_altar(self, book) -> bool:
        """Laying the Book of Thoth on an altar while its oath is open.
        Returns True when the altar took the action (kept, kept late or
        refused); False to let the book be dropped as any item."""
        import deeds
        import karma
        reg = self._deeds_reg()
        oath_id = data().get('oath', 'thoth_return')
        o = reg['oaths'].get(oath_id)
        if not o or o.get('status') != 'open':
            return False
        al = data().get('altar') or {}
        if not getattr(book, 'spent', False):
            self.add_message(al.get('unread_message', "Not yet. You swore to read it first."),
                             'warning')
            return True
        floor, deepest, block, turn = self._deed_where()
        self.player.remove_from_inventory(book)
        thread = data().get('thread') or o.get('thread')
        if not deeds.is_overdue(o, deepest):
            self.add_message(al.get('on_time_message', ''), 'success')
            self._keep_oath(oath_id)
            if thread:
                deeds.close_thread(reg, thread)
            if al.get('on_time_chronicle'):
                self._chron('oath', al['on_time_chronicle'])
        else:
            deeds.keep_oath_late(reg, oath_id, floor=floor, block=block, turn=turn)
            karma.adjust(self, 0, kind='oath', source=oath_id, made_block=o.get('made_block'))
            self.add_message(al.get('late_message', ''), 'success')
            if thread:
                deeds.close_thread(reg, thread, line=al.get('late_thread_line'))
            if al.get('late_chronicle'):
                self._chron('oath', al['late_chronicle'])
            self._thoth_call_off_the_dead()
        self._advance_turn()
        return True

    def _thoth_call_off_the_dead(self):
        """A late return before the dead came: no fight. Their pending
        callback is dropped and, if they already stand on a floor, they go."""
        import deeds
        tag = data().get('callback', '')
        reg = self._deeds_reg()
        for p in list(reg.get('pending', ())):
            if p.get('kind') == 'encounter' and (p.get('spec') or {}).get('encounter') == tag:
                deeds.pop(reg, p['id'])
        levels = getattr(self, '_flavor_encounter_levels', None) or {}
        for lvl in [k for k, e in levels.items() if (e or {}).get('tag') == tag]:
            levels.pop(lvl, None)
        for m in list(getattr(self, 'monsters', ()) or ()):
            if getattr(m, '_flavor_encounter_tag', None) == tag:
                m.alive = False
                m.hp = 0
        enc = getattr(self, '_encountered_flavor_npcs', None)
        if isinstance(enc, set):
            enc.add(tag)
