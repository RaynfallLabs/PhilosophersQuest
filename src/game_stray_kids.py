"""StrayKidsMixin: the Stray Kids easter egg, the game's side (the pure
half, and the whole design, is src/stray_kids.py).

* The idol: placed on its floor on first arrival (``_maybe_spawn_stray_kids_idol``).
  It calls the hero over the first time he sees it (``_stray_kids_idol_calls``);
  Observe shows a shrine plainly Stray Kids without naming them; walking into
  it hums and invites a proper touch, and walking into it again touches it
  (``_stray_kids_idol_bump``, from the bump code in main.py).
* The trip: ``_enter_stray_kids_stage`` takes the hero to the Zombie Stage
  (boss_levels.STRAY_KIDS_STAGE, a side floor); its stage door (the down
  stair in the wings) brings him back to the idol's floor, arriving on its
  down stair as from the Cow Level (``_exit_stray_kids_stage``, reached
  through EncountersMixin._leave_side_floor). One trip a run.
* The beat (``_stray_kids_tick``, once a turn from Game._advance_turn): the
  dance moves on, the band shouts, Lee Know's cat is seen to, and the stars
  of a show dance, hold the room's attention, and bow out.
* The deaths (``_stray_kids_member_died``, from _on_monster_killed): each
  member crumbles to nothing, and the last leaves the photo.
* The photo (``_stray_kids_summon``): read (the scroll path, one grammar
  question), it calls the band up alive for a short show.
* QA (Titivillus build, Shift+K): the idol beside the hero; pressed again,
  the photo in the pack.

Run state is ``game._stray_kids`` (saved; stray_kids.new_run_state). The
stage and its dance pickle with their floor.
"""
from __future__ import annotations

import random

import stray_kids

SPEECH_MS = 3200


class StrayKidsMixin:

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _stray_kids_state(self) -> dict:
        st = self.__dict__.get('_stray_kids')
        if not isinstance(st, dict):
            st = stray_kids.old_save_state()
            self._stray_kids = st
        return st

    def _stray_kids_rng(self) -> random.Random:
        r = self.__dict__.get('_sk_rng')
        if r is None:
            r = self._sk_rng = random.Random()   # its own stream: shouts never shift the game's dice
        return r

    def _on_stray_kids_stage(self) -> bool:
        from boss_levels import STRAY_KIDS_STAGE
        return getattr(self, 'dungeon_level', 0) == STRAY_KIDS_STAGE

    # ------------------------------------------------------------------
    # The idol
    # ------------------------------------------------------------------

    def _maybe_spawn_stray_kids_idol(self, level: int):
        st = self._stray_kids_state()
        if st.get('spawned') or st.get('floor') != level:
            return
        import decor
        pos = decor.place_event_stand(self.dungeon, stray_kids.idol_id(), self.monsters,
                                      self.ground_items, self._stray_kids_rng())
        if pos is not None:
            st['spawned'] = True
            st['pos'] = [int(pos[0]), int(pos[1])]

    def _stray_kids_idol_calls(self) -> None:
        """The first time the hero sees the idol, it calls him over (once a
        run). Observe (O) says what it is."""
        st = self._stray_kids_state()
        if (st.get('called') or st.get('touched') or not st.get('spawned')
                or st.get('floor') != getattr(self, 'dungeon_level', None)):
            return
        pos = st.get('pos')
        if not pos:
            fixtures = getattr(getattr(self, 'dungeon', None), '__dict__', {}).get('fixtures') or {}
            pos = next((p for p, f in fixtures.items() if f == stray_kids.idol_id()), None)
            if pos is None:
                return
            st['pos'] = [int(pos[0]), int(pos[1])]
        if tuple(pos) not in (getattr(self, 'visible', set()) or set()):
            return
        st['called'] = True
        self.add_message(stray_kids.data()['idol']['call'], 'info')

    def _stray_kids_idol_bump(self, x: int, y: int) -> bool:
        """The hero walked into a fixture at (x, y): True if it was the idol.
        The first bump hums and invites a proper touch (what it is, Observe
        says); the next one, from the same spot, touches it. A bump costs no
        turn."""
        import decor
        if decor.fixture_at(self.dungeon, x, y) != stray_kids.idol_id():
            return False
        d = stray_kids.data()['idol']
        spent = (self.dungeon.__dict__.get('fixture_state') or {}).get((x, y)) == 'spent'
        if spent or self._stray_kids_state().get('touched'):
            self.add_message(d['spent_bump'], 'info')
            return True
        here = (self.dungeon_level, (self.player.x, self.player.y), (x, y))
        if self.__dict__.get('_sk_armed') != here:
            self._sk_armed = here
            self.add_message(d['first_bump'], 'info')
            return True
        self._sk_armed = None
        self.dungeon.__dict__.setdefault('fixture_state', {})[(x, y)] = 'spent'
        self._enter_stray_kids_stage()
        return True

    # ------------------------------------------------------------------
    # The trip there and back
    # ------------------------------------------------------------------

    def _enter_stray_kids_stage(self):
        from boss_levels import STRAY_KIDS_STAGE
        from game_states import STATE_PLAYER
        sk = stray_kids.data()
        st = self._stray_kids_state()
        st['touched'] = True
        st['return_floor'] = int(self.dungeon_level)
        for line in sk['idol']['touch']:
            self.add_message(line, 'warning')
        self._chron('milestone', sk['idol']['touch_chronicle'], once='stray_kids:touch')
        self.state = STATE_PLAYER
        try:
            self._change_level(STRAY_KIDS_STAGE, enter_from_top=True, via='stray_kids')
        except Exception:
            from game_log import log_error
            log_error('game_stray_kids._enter_stray_kids_stage: recovered from an error')
            return
        # Everybody knows who they are: their Bestiary pages are open, and
        # Observe tells all of it (family_lore.knowledge KNOWN).
        known = getattr(self.player, 'lore_known_monster_ids', None)
        if isinstance(known, set):
            known.update(stray_kids.zombie_kinds())
        for line in sk['stage']['arrival']:
            self.add_message(line, 'warning')
        self.add_message(sk['stage']['door_line'], 'info')

    def _exit_stray_kids_stage(self):
        sk = stray_kids.data()
        d = sk['stage']
        st = self._stray_kids_state()
        cleared = not stray_kids.the_band(self.monsters)
        if cleared:
            st['outcome'] = 'cleared'
            self.add_message(d['leave_cleared'], 'info')
        else:
            st['outcome'] = st.get('outcome') or 'left'
            self.add_message(d['leave_unfinished'], 'info')
            self._chron('milestone', sk['stage']['leave_chronicle'], once='stray_kids:left')
        back = int(st.get('return_floor') or 0) or max(
            1, int(getattr(self.player, 'deepest_floor_reached', 1) or 1))
        try:
            self._change_level(back, enter_from_top=False, via='stray_kids')
        except Exception:
            from game_log import log_error
            log_error('game_stray_kids._exit_stray_kids_stage: recovered from an error')

    # ------------------------------------------------------------------
    # The beat
    # ------------------------------------------------------------------

    def _stray_kids_light_the_stage(self, sight: int) -> None:
        """The stage hall is lit: from anywhere on the stage the hero sees
        every hall tile in his line of sight, however far (never while blind)."""
        if not self._on_stray_kids_stage() or sight <= 1:
            return
        rooms = getattr(self.dungeon, 'rooms', None) or []
        if len(rooms) < 2:
            return
        hall = rooms[1]
        from fov import calculate_fov
        far = calculate_fov(self.dungeon, self.player.x, self.player.y,
                            max(self.dungeon.width, self.dungeon.height))
        lit = {(x, y) for (x, y) in far
               if hall.x - 1 <= x <= hall.x + hall.width and hall.y - 1 <= y <= hall.y + hall.height}
        self.visible |= lit
        self.dungeon.explored |= lit

    def _stray_kids_say(self, m, text: str, kind: str = 'info'):
        """A line from one of the eight, in the log and floating over him
        (the Black Knight's speech bubble, which draws over any speaker)."""
        from monster import the_name
        who = the_name(m)
        if text.startswith('*') and text.endswith('*'):
            act = text.strip('*')
            self.add_message(f"{who} {act[:1].lower()}{act[1:]}.", kind)
        else:
            # A song title quoted inside the shout takes single quotes:
            # ""Thunderous"! Stop nagging me" read as an empty quote and a
            # stray one (bug bash WB-E05). The bubble keeps the line as is.
            self.add_message(f'{who}: "{text.replace(chr(34), chr(39))}"', kind)
        try:
            import pygame
            now = pygame.time.get_ticks()
        except Exception:
            now = 0
        self._bk_speech = {'text': text, 'knight': m, 'until': now + SPEECH_MS,
                           'turn': getattr(self, 'turn_count', 0)}

    def _stray_kids_tick(self):
        """Once a turn, after the world has moved (Game._advance_turn)."""
        self._stray_kids_idol_calls()
        if not getattr(self, 'monsters', None):
            return
        visible = getattr(self, 'visible', set()) or set()
        for m in stray_kids.the_band(self.monsters):
            events, m.__dict__['_sk_events'] = list(m.__dict__.get('_sk_events') or ()), []
            for line in events:
                if (m.x, m.y) in visible:
                    self.add_message(line, 'info')
        if self._on_stray_kids_stage():
            self._stray_kids_beat()
        self._stray_kids_show_tick()

    def _stray_kids_beat(self):
        import senses
        d = stray_kids.data()
        cfg = d['dance']
        p = self.player
        rng = self._stray_kids_rng()
        reach = int(cfg['notice_range'])
        hidden = p.has_effect('invisible')

        def sees(m):
            dist = max(abs(m.x - p.x), abs(m.y - p.y))
            if dist > reach or (hidden and dist > 1):
                return False
            return senses.clear_view(m.x, m.y, p.x, p.y, self.dungeon)

        band = stray_kids.the_band(self.monsters)
        in_view = [m for m in band if (m.x, m.y) in (getattr(self, 'visible', set()) or set())]
        for ev in stray_kids.advance(self.dungeon, self.monsters, (p.x, p.y), sees):
            if ev[0] == 'seen':
                self.add_message(d['stage']['seen'], 'warning')
                self.add_message(d['stage']['tell'], 'warning')
            elif ev[0] == 'shape' and in_view and rng.random() < float(cfg['shape_line_chance']):
                self.add_message(cfg['shape_lines'].get(ev[1], ''), 'info')
        dance = stray_kids.dance_of(self.dungeon)
        if not dance or not dance.get('aware') or not in_view:
            return
        if rng.random() >= float(cfg['line_chance']):
            return
        m = rng.choice(in_view)
        # His own line, a riff on one of their songs, or a band line.
        own = d['shouts'].get(m.member) or []
        songs = d['shouts'].get('songs') or []
        roll = rng.random()
        mine = float(cfg['member_line_share'])
        if own and roll < mine:
            line = rng.choice(own)
        elif songs and roll < mine + float(cfg.get('song_line_share', 0)):
            line = rng.choice(songs)
        else:
            line = rng.choice(d['shouts']['band'])
        self._stray_kids_say(m, line, 'warning')

    # ------------------------------------------------------------------
    # The deaths
    # ------------------------------------------------------------------

    def _stray_kids_member_died(self, monster) -> None:
        """A member crumbles to nothing (he has no corpse: ``_no_corpse``),
        and the last of them leaves the photo where he stood."""
        if not stray_kids.is_zombie(monster):
            return
        from monster import the_name
        sk = stray_kids.data()
        self.add_message(sk['disintegrate'].format(name=the_name(monster)), 'success')
        # Each has a Journal line of his own (they are a band, not eight
        # mini-bosses, so the kill handler does not write it).
        if monster.kill_chronicle:
            self._chron('boss', monster.kill_chronicle, once=f'boss:{monster.kind}')
        st = self._stray_kids_state()
        if any(m is not monster for m in stray_kids.the_band(self.monsters)):
            return
        if st.get('photo_dropped'):
            return
        st['photo_dropped'] = True
        st['outcome'] = 'cleared'
        self.add_message(sk['last_falls'], 'success')
        if self._stray_kids_drop_photo(monster.x, monster.y):
            self.add_message(sk['photo_drop'], 'loot')
        self._chron('boss', sk['stage']['cleared_chronicle'], once='stray_kids:cleared')

    def _stray_kids_photo(self, x: int, y: int):
        """A fresh Autographed Stray Kids Photo at (x, y), known on sight."""
        from items import load_items, copy_at, grant_identified
        tpl = next((s for s in load_items('scroll') if s.id == stray_kids.photo_id()), None)
        if tpl is None:
            return None
        photo = copy_at(tpl, x, y)
        grant_identified(self, photo)
        return photo

    def _stray_kids_drop_photo(self, x: int, y: int) -> bool:
        photo = self._stray_kids_photo(x, y)
        if photo is None:
            return False
        self.ground_items.append(photo)
        return True

    # ------------------------------------------------------------------
    # The photo: a show
    # ------------------------------------------------------------------

    def _stray_kids_summon(self):
        """The photo was read: the eight, alive, dance round the hero for a
        few turns. They neither strike nor are struck, and the monsters near
        them stop to watch."""
        d = stray_kids.data()['stars']
        for line in d['summon']:
            self.add_message(line, 'success')
        p = self.player
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters)) | set(self._occupants())
        stars = []
        for slot, member in enumerate(stray_kids.members()):
            dx, dy = d['ring'][(slot * 2) % len(d['ring'])]
            spot = self._stray_kids_free_tile(p.x + dx, p.y + dy, taken)
            if spot is None:
                continue
            taken.add(spot)
            s = stray_kids.StarDancer(member, spot[0], spot[1], slot=slot)
            s._sk_turns = int(d['dance_turns'])
            stars.append(s)
        self.monsters.extend(stars)
        self._stray_kids_hold_the_room(stars)
        sk = stray_kids.data()
        self._chron('discovery', sk['stars']['chronicle'], once='stray_kids:show')

    def _stray_kids_free_tile(self, x: int, y: int, taken: set):
        """(x, y) if a dancer can stand there, else the nearest such tile
        within three steps of it, else None."""
        best = None
        for r in range(0, 4):
            for ty in range(y - r, y + r + 1):
                for tx in range(x - r, x + r + 1):
                    if max(abs(tx - x), abs(ty - y)) != r:
                        continue
                    if (tx, ty) in taken or not self.dungeon.is_walkable(tx, ty):
                        continue
                    if (tx, ty) == (self.player.x, self.player.y):
                        continue
                    best = (tx, ty)
                    break
                if best:
                    return best
        return None

    def _stray_kids_hold_the_room(self, stars) -> None:
        from monster import the_name
        d = stray_kids.data()['stars']
        visible = getattr(self, 'visible', set()) or set()
        for m in stray_kids.watchers(self.monsters, stars, self.dungeon):
            m.add_effect('stunned', int(d['watch_turns']))
            if not m.__dict__.get('_sk_watching') and (m.x, m.y) in visible:
                self.add_message(d['watch_line'].replace('{The}', the_name(m)), 'success')
            m._sk_watching = True

    def _stray_kids_show_tick(self) -> None:
        stars = [m for m in self.monsters if stray_kids.is_star(m) and m.alive]
        if not stars:
            return
        d = stray_kids.data()['stars']
        self._stray_kids_hold_the_room(stars)
        rng = self._stray_kids_rng()
        visible = getattr(self, 'visible', set()) or set()
        seen = [s for s in stars if (s.x, s.y) in visible]
        if seen and rng.random() < float(stray_kids.data()['dance']['line_chance']):
            self._stray_kids_say(rng.choice(seen), rng.choice(d['lines']), 'success')
        gone = []
        for s in stars:
            s._sk_turns = int(s.__dict__.get('_sk_turns', 0)) - 1
            if s._sk_turns <= 0:
                gone.append(s)
        if gone:
            self.monsters[:] = [m for m in self.monsters if m not in gone]
            if len(gone) == len(stars):
                self.add_message(d['bow'], 'success')
                for m in self.monsters:
                    m.__dict__.pop('_sk_watching', None)

    def _stray_kids_star_step_past(self, star) -> None:
        """Walking into a dancer swaps places with him: the show never
        blocks the hero in."""
        ox, oy = self.player.x, self.player.y
        self.player.x, self.player.y = star.x, star.y
        star.x, star.y = ox, oy
        self.add_message(f"You slip past {star.name}, who keeps dancing.", 'info')
        self._refresh_fov()
        self._advance_turn()

    # ------------------------------------------------------------------
    # QA (Titivillus build)
    # ------------------------------------------------------------------

    def _qa_stray_kids(self) -> None:
        """Shift+K: a Stray Kids idol beside the hero on this floor; pressed
        again (an idol already here, or the stage done), the photo in the
        pack."""
        if not getattr(self.player, 'qa_tools', False):
            return
        import decor
        st = self._stray_kids_state()
        fixtures = self.dungeon.__dict__.get('fixtures') or {}
        here = any(f == stray_kids.idol_id() for f in fixtures.values())
        if here or self._on_stray_kids_stage():
            photo = self._stray_kids_photo(self.player.x, self.player.y)
            if photo is not None:
                self.player.inventory.append(photo)
                self.add_message("[QA] An Autographed Stray Kids Photo is put in your pack.", 'info')
            return
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters)) | set(self._occupants())
        taken |= {(i.x, i.y) for i in self.ground_items if hasattr(i, 'x')}
        p = self.player
        from dungeon import FLOOR
        spot = next(((p.x + dx, p.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                                         (1, 1), (-1, 1), (1, -1), (-1, -1))
                     if self.dungeon.in_bounds(p.x + dx, p.y + dy)
                     and self.dungeon.tiles[p.y + dy][p.x + dx] == FLOOR
                     and (p.x + dx, p.y + dy) not in taken
                     and not decor.fixture_at(self.dungeon, p.x + dx, p.y + dy)), None)
        if spot is None:
            self.add_message("[QA] No room beside you for the idol.", 'warning')
            return
        decor.place(self.dungeon, spot, stray_kids.idol_id())
        st.update({'floor': int(self.dungeon_level), 'spawned': True, 'touched': False,
                   'outcome': None, 'photo_dropped': False, 'called': False,
                   'pos': [int(spot[0]), int(spot[1])]})
        # A stage already played this run is struck: the next touch builds it fresh.
        from boss_levels import STRAY_KIDS_STAGE
        saved = getattr(getattr(self, 'level_mgr', None), '_saved', None)
        if isinstance(saved, dict):
            saved.pop(STRAY_KIDS_STAGE, None)
        self.add_message("[QA] A Stray Kids idol is set down beside you. Walk into it twice.", 'info')
