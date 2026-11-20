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
* The announcement (``_stray_kids_announce``, once a turn from
  ``_stray_kids_tick``): the first time the hero sets foot on the stage the
  band strikes a pose, "B-B-B-BOSS BATTLE! DANCE OFF!" fills the map (the
  effects runtime's banner, as a kill's) with its fanfare, and once the
  banner is over the dance-off opens (``_stray_kids_frame``, every frame).
* The dance-off (Brandon, 2026-11-14): on the Mooble's dance screen
  (game_mooble_dance.py) with the band's own words, pictures and rules
  (``_sk_open_dance``, ``_sk_dance_key``, ``_sk_dance_finished``). Practice
  first, free and as often as wanted; then eight rounds of Simon Says, a
  member leading each. A round won and its leader crumbles into glitter
  (``_sk_fall``: the kill handler, his Journal line, and the last one's
  photo). A round lost and the earworm hits (his song, a hindrance, a little
  damage that never kills), with a strike gone. Out of strikes: the band
  laughs, the members still standing go back to their places, and the hero
  is set down at the edge of the stage (``_sk_dance_lost``). Walking into
  any member challenges them again (``_stray_kids_bump``).
* The shouts (``_stray_kids_tick``): once the band has seen the hero, a
  member in sight now and then shouts his own line, a riff on a song or a
  band line; Lee Know sometimes pets his cat instead.
* The deaths (``_stray_kids_member_died``, from _on_monster_killed): each
  member crumbles to nothing, and the last leaves the photo.
* The photo (``_stray_kids_summon``): read (the scroll path, one grammar
  question), it calls the band up alive for a short show.
* QA (Titivillus build, Shift+K): the idol beside the hero; pressed again,
  the photo in the pack; on the stage with the band standing, the dance-off
  at once.

Run state is ``game._stray_kids`` (saved; stray_kids.new_run_state). The
stage and the band pickle with their floor. A save made while the dance-off
screen is open opens it again on load, at the start of the current round
(``dancing``: its mode and the strikes left).
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
        # The floor's own kind of stream (random_streams), not the shouts':
        # that one is seeded by the OS, and a seeded floor would set the
        # idol down somewhere new in every process.
        pos = decor.place_event_stand(self.dungeon, stray_kids.idol_id(), self.monsters,
                                      self.ground_items)
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
        st['dancing'] = None
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

    def _stray_kids_after_load(self) -> None:
        """A save from before the dance-off, made on the stage, has the band
        fighting in formation (hostile, hurt, held, quarrelling in a
        war-band). Every member still standing goes back to his place as a
        performer; the fallen stay fallen; the announcement waits for the
        hero's next step on the stage. Game.load_state calls it."""
        if not self._on_stray_kids_stage():
            return
        band = stray_kids.the_band(self.monsters)
        old = ('sk_dance' in getattr(self.dungeon, '__dict__', {})
               or any(not getattr(m, 'is_allied', False) for m in band))
        if not old:
            return
        p = self.player
        stray_kids.settle_band(self.dungeon, self.monsters, (p.x, p.y))
        st = self._stray_kids_state()
        st.setdefault('challenge', None)
        st.setdefault('dancing', None)

    # ------------------------------------------------------------------
    # The stage: the lights, the shouts
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

    @staticmethod
    def _stray_kids_line(m, text: str) -> str:
        """One of the eight's lines as the log says it: an action ("*flips
        his hair*") as a sentence about him, a shout in quotes after his name.
        A song title quoted inside the shout takes single quotes: ""Thunderous"!
        Stop nagging me" read as an empty quote and a stray one (bug bash
        WB-E05)."""
        from monster import the_name
        who = the_name(m)
        if text.startswith('*') and text.endswith('*'):
            act = text.strip('*')
            return f"{who} {act[:1].lower()}{act[1:]}."
        return f'{who}: "{text.replace(chr(34), chr(39))}"'

    def _stray_kids_say(self, m, text: str, kind: str = 'info'):
        """A line from one of the eight, in the log and floating over him
        (the Black Knight's speech bubble, which draws over any speaker). The
        bubble keeps the line as is."""
        self.add_message(self._stray_kids_line(m, text), kind)
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
        if self._on_stray_kids_stage():
            self._stray_kids_stage_tick()
        self._stray_kids_show_tick()

    def _stray_kids_stage_tick(self):
        """On the stage, once a turn: the first step onto the stage brings the
        announcement; after it, the band in sight now and then shouts."""
        st = self._stray_kids_state()
        band = stray_kids.the_band(self.monsters)
        if not band:
            return
        p = self.player
        if not st.get('challenge'):
            if stray_kids.on_stage(self.dungeon, p.x, p.y):
                self._stray_kids_announce()
            return
        visible = getattr(self, 'visible', set()) or set()
        in_view = [m for m in band if (m.x, m.y) in visible]
        if in_view:
            self._stray_kids_shout(in_view)

    def _stray_kids_shout(self, in_view) -> None:
        d = stray_kids.data()
        cfg = d['shouting']
        rng = self._stray_kids_rng()
        if rng.random() >= float(cfg['line_chance']):
            return
        m = rng.choice(in_view)
        # Lee Know and his cat: you are less important than the cat.
        cat = (d.get('distracted') or {}).get(m.member)
        if cat and rng.random() < float(cat.get('chance', 0)):
            self.add_message(rng.choice(cat['lines']), 'info')
            return
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
    # The announcement: B-B-B-BOSS BATTLE! DANCE OFF!
    # ------------------------------------------------------------------

    def _stray_kids_announce(self) -> None:
        """The band sees the hero on the stage: it strikes a pose, and the
        announcement fills the map, big, as a kill's banner does (the effects
        runtime's 'dance_off_banner'), with its fanfare. The dance-off opens
        once the banner is over (``_stray_kids_frame``)."""
        sk = stray_kids.data()
        st = self._stray_kids_state()
        st['challenge'] = 'pending'
        for key in ('seen', 'pose'):
            if sk['stage'].get(key):
                self.add_message(sk['stage'][key], 'warning')
        ann = sk['dance_off']['announce']
        self.add_message(ann['log'], 'warning')
        self.add_message(sk['stage']['tell'], 'info')
        try:
            import sound_system
            sound_system.play('dance_off')
        except Exception:
            pass
        rt = getattr(self, 'effects_runtime', None)
        if rt is not None:
            rt.fire('dance_off_banner', {'main_line': ann['main'], 'top_line': ann['top'],
                                         'color': tuple(ann.get('colour') or (255, 96, 200)),
                                         'tier': 'big'})

    def _stray_kids_frame(self) -> None:
        """Every frame of plain play (Game.update): a dance-off left open by a
        save opens again, at the start of its round; the challenge the
        announcement made opens once the banner is over and play is calm."""
        st = self.__dict__.get('_stray_kids')
        if not isinstance(st, dict) or not self._on_stray_kids_stage():
            return
        if st.get('dancing'):
            self._stray_kids_dance_after_load()
        elif st.get('challenge') == 'pending' and self._play_is_calm():
            self._stray_kids_challenge()

    def _stray_kids_bump(self, member) -> None:
        """The hero walked into one of the band: the dance-off (before the
        band has seen him, the announcement first). A bump costs no turn."""
        st = self._stray_kids_state()
        if not st.get('challenge'):
            self._stray_kids_announce()
            return
        if st.get('challenge') != 'pending' and st.get('lost'):
            self.add_message(stray_kids.data()['stage']['challenge_again'], 'info')
        self._stray_kids_challenge()

    def _stray_kids_challenge(self) -> None:
        """The dance-off's first card: practise as often as wanted, or
        dance."""
        if not stray_kids.the_band(self.monsters):
            return
        self._stray_kids_state()['challenge'] = 'made'
        self._sk_open_dance('practice')

    # ------------------------------------------------------------------
    # The dance-off, on the Mooble's dance screen
    # ------------------------------------------------------------------

    def _sk_open_dance(self, mode: str, strikes: int | None = None, first: bool = True) -> None:
        """The dance screen for the round now: 'practice' (its card: practise,
        dance, or not yet) or 'dance' (the round itself, in a dance-off with
        ``strikes`` left; ``first`` while no round of it has been danced)."""
        from game_states import STATE_MOOBLE_DANCE
        band = stray_kids.the_band(self.monsters)
        if not band:
            return
        self._mooble_music(False)
        lead = band[0]
        i = stray_kids.round_index(self.monsters)
        do = stray_kids.dance_off()
        sc = do['screen']
        mode = 'dance' if mode == 'dance' else 'practice'
        if strikes is None:
            strikes = stray_kids.strikes()
        name = stray_kids.member_name(lead.member)
        words = dict(sc)
        words['watch'] = sc['watch'].format(leader=name)
        words['his_row'] = sc['his_row'].format(leader=name)
        title = (sc['title_dance'].format(round=i + 1, rounds=stray_kids.rounds())
                 if mode == 'dance' else sc['title_practice'])
        md = self._dance_spec(
            mode, stray_kids.round_timeline(i), stray_kids.round_bpm(i), title=title, info='',
            rules=do, words=words, poses={'idle': lead.kind}, owner='stray_kids', nudge=True,
            beat_light={'colour': (235, 70, 175), 'glow': (255, 110, 210), 'shine': (255, 220, 245),
                        'wire': False},
            sk_member=lead.member, sk_round=i, sk_strikes=int(strikes), sk_first=bool(first),
            footers={'ready': sc['footer_ready_practice'] if mode == 'practice'
                     else sc['footer_ready_first' if first else 'footer_ready_dance'],
                     'play': sc['footer_practice' if mode == 'practice' else 'footer_dance'],
                     'result': sc['footer_practice_done']})
        md['ready_head'] = (sc['how'] if mode == 'practice' else self._stray_kids_line(
            lead, stray_kids.leader_line(lead.member, 'open', self._stray_kids_rng())))
        self._sk_refresh_card(md)
        self._mdance = md
        self._stray_kids_state()['dancing'] = {'mode': mode, 'strikes': int(strikes),
                                               'first': bool(first)}
        self.state = STATE_MOOBLE_DANCE

    def _sk_refresh_card(self, md: dict) -> None:
        """The card's left column: the round, who leads, the tempo, the
        strikes left (in a dance-off), and the band, the fallen dimmed."""
        sc = stray_kids.dance_off()['screen']
        i = int(md['sk_round'])
        lines = [sc['info_round'].format(round=i + 1, rounds=stray_kids.rounds()),
                 sc['info_leader'].format(leader=stray_kids.member_name(md['sk_member'])),
                 sc['info_tempo'].format(steps=len(md['tl']['response']), bpm=int(md['bpm']))]
        if md['mode'] == 'dance':
            lines.append(sc['info_strikes'].format(n=int(md['sk_strikes']), of=stray_kids.strikes()))
        md['info_lines'] = lines
        standing = {m.member for m in stray_kids.the_band(self.monsters)}
        md['roster'] = [(stray_kids.zombie_kind(mem), mem not in standing, mem == md['sk_member'])
                        for mem in stray_kids.members()]

    def _sk_dance_key(self, key: int) -> None:
        """The dance-off's keys (the arrows while it plays are the screen's)."""
        import pygame
        md = self._mdance
        go = key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        dance_off = key in (pygame.K_d, pygame.K_2, pygame.K_KP2)
        esc = key == pygame.K_ESCAPE
        phase, mode = md['phase'], md['mode']
        if phase == 'play':
            if self._dance_arrow_key(key):
                return
            if esc and mode == 'practice':
                self._sk_open_dance('practice')   # stop: back to the card, nothing lost
            return
        if phase == 'ready':
            if go:
                if mode == 'dance':
                    md['sk_first'] = False
                    self._stray_kids_state()['dancing'] = {'mode': 'dance', 'strikes': int(md['sk_strikes']),
                                                           'first': False}
                self._mooble_dance_start()
            elif mode == 'practice' and dance_off:
                self._sk_open_dance('dance')
            elif esc and mode == 'practice':
                self._sk_close()
            elif esc and md.get('sk_first'):
                self._sk_open_dance('practice')   # not danced yet: back to the card
            return
        # result
        if mode == 'practice':
            if go:
                self._mooble_dance_start()        # again, as often as wanted
            elif dance_off:
                self._sk_open_dance('dance')
            elif esc:
                self._sk_close()
            return
        if go or esc:
            self._sk_continue(md)

    def _sk_dance_finished(self, md: dict) -> None:
        """A round danced through (the screen judged it): practice says how it
        would have gone; a dance-off round makes its leader fall, or brings
        the earworm and costs a strike."""
        from game_mooble_dance import _play
        sc = stray_kids.dance_off()['screen']
        if md['mode'] == 'practice':
            _play('trait' if md['won'] else 'lock_fail')
            return
        lead = next((m for m in stray_kids.the_band(self.monsters) if m.member == md['sk_member']), None)
        st = self._stray_kids_state()
        lines = []
        if md['won'] and lead is not None:
            from monster import the_name
            who = the_name(lead)
            standing = self._sk_fall(lead)
            outcome, left = stray_kids.after_round(True, md['sk_strikes'], standing)
            md['result_head'] = sc['falls_last' if outcome == 'won' else 'falls'].format(name=who)
        else:
            standing = len(stray_kids.the_band(self.monsters))
            outcome, left = stray_kids.after_round(False, md['sk_strikes'], standing)
            if lead is not None:
                roast = stray_kids.leader_line(lead.member, 'roast', self._stray_kids_rng())
                md['result_head'] = self._stray_kids_line(lead, roast)
                self._stray_kids_say(lead, roast, 'warning')
                lines += self._sk_earworm(lead)
            strike = sc['strike_line'].format(n=left) if outcome == 'retry' else sc['out_line']
            # (The card has room for his song and one line more: the
            # hindrance and the strike share it; the row shows the misses.)
            if len(lines) > 1:
                lines[1:] = [' '.join(lines[1:] + [strike])]
            else:
                lines.append(strike)
            md['hide_result_line'] = True
            _play('lock_fail')
        md['result_lines'] = lines
        md['sk_outcome'] = outcome
        md['sk_strikes'] = left
        md['footers']['result'] = sc['footer_' + outcome]
        self._sk_refresh_card(md)
        st['dancing'] = (None if outcome == 'won' else
                         {'mode': 'dance', 'strikes': int(left), 'first': False})

    def _sk_earworm(self, lead) -> list:
        """The earworm a lost round brings: his song stuck in the hero's
        head. Its hindrance and a little damage, never the last hit point.
        Returns the lines it said (they show on the card too)."""
        from monster import the_name
        ew_cfg = stray_kids.dance_off()['earworm']
        p = self.player
        ew = stray_kids.earworm(lead.member, int(p.hp), self._stray_kids_rng())
        hit = ew_cfg['hit'].format(name=the_name(lead), song=ew['song'], quip=ew['quip']).strip()
        out = [hit]
        one, many = ew_cfg['turn_words']
        turns = (one if ew['turns'] == 1 else many).format(n=ew['turns'])
        bits = []
        if p.add_effect(ew['effect'], ew['turns']) or p.has_effect(ew['effect']):
            what = ew_cfg['effects'].get(ew['effect'], ew['effect'])
            bits.append(ew_cfg['effect_line'].format(what=what, turns=turns))
        if ew['damage'] > 0:
            p.hp = max(1, int(p.hp) - int(ew['damage']))
            bits.append(ew_cfg['hurt_line'].format(damage=ew['damage']))
        if bits:
            out.append(' '.join(bits))
        for line in out:
            self.add_message(line, 'warning')
        return out

    def _sk_fall(self, lead) -> int:
        """A round won: its leader falls to the dance, through the kill
        handler like any death (the kill's events, his Journal line, and the
        last one's photo, ``_stray_kids_member_died``). Returns how many of
        the band still stand."""
        lead._danced_down = True              # (crumbles: not "slain")
        lead.hp = 0
        lead.alive = False
        self._on_monster_killed(lead)
        return len(stray_kids.the_band(self.monsters))

    def _sk_continue(self, md: dict) -> None:
        """Enter on a dance-off round's result: the next round, the round
        again, the bow, or off the stage."""
        outcome = md.get('sk_outcome')
        if outcome in ('next', 'retry'):
            self._sk_open_dance('dance', strikes=int(md['sk_strikes']), first=False)
        elif outcome == 'won':
            self._sk_dance_won()
        else:
            self._sk_dance_lost()

    def _sk_close(self) -> None:
        """Leave the dance-off's card (Not Yet): nothing changes, no turn
        passes. Walk into any of the band to come back to it."""
        from game_states import STATE_PLAYER
        self._mooble_music(False)
        self._mdance = None
        self._stray_kids_state()['dancing'] = None
        self.state = STATE_PLAYER

    def _sk_dance_won(self) -> None:
        """The last of the band has fallen: the photo lies where he stood
        (``_stray_kids_member_died``). The dance-off was the turn."""
        sk = stray_kids.data()
        self._sk_close()
        self.add_message(sk['dance_off']['won_log'], 'success')
        try:
            import sound_system
            sound_system.play('victory')
        except Exception:
            pass
        self._advance_turn()

    def _sk_dance_lost(self) -> None:
        """Out of strikes: the band laughs, the members still standing go
        back to their places (the fallen stay fallen), and the hero is set
        down at the edge of the stage, shaken but alive. He can practise and
        challenge them again, or leave by the stage door."""
        sk = stray_kids.data()
        do = sk['dance_off']
        st = self._stray_kids_state()
        self._sk_close()
        st['lost'] = int(st.get('lost') or 0) + 1
        p = self.player
        edge = stray_kids.stage_edge(self.dungeon)
        taken = {(m.x, m.y) for m in self.monsters if getattr(m, 'alive', False)}
        if edge in taken or not self.dungeon.is_walkable(*edge):
            edge = self._stray_kids_free_tile(edge[0], edge[1], taken) or (p.x, p.y)
        p.x, p.y = edge
        stray_kids.settle_band(self.dungeon, self.monsters, (p.x, p.y))
        self.add_message(do['laugh'], 'warning')
        self.add_message(do['lost_log'], 'info')
        self._chron('milestone', do['lost_chronicle'], once='stray_kids:lost')
        self._refresh_fov()
        self._advance_turn()

    def _stray_kids_dance_after_load(self) -> None:
        """A save made while the dance-off screen was open: it opens again at
        the start of the current round, with the strikes that were left (a
        round left unfinished was never judged). Out of strikes already, the
        dance-off is lost."""
        st = self._stray_kids_state()
        dancing = st.get('dancing')
        st['dancing'] = None
        if not isinstance(dancing, dict) or not stray_kids.the_band(self.monsters):
            return
        mode = dancing.get('mode', 'practice')
        strikes = int(dancing.get('strikes', stray_kids.strikes()) or 0)
        st['challenge'] = 'made'
        if mode == 'dance' and strikes <= 0:
            self._sk_dance_lost()
            return
        self._sk_open_dance(mode, strikes=strikes if mode == 'dance' else None,
                            first=bool(dancing.get('first', True)))

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
        self._seeker_event('stray_kids', outcome='cleared')     # the Seeker's Stage Fright
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
        self._seeker_event('stray_kids', outcome='show')        # the Seeker's Encore!

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
        """Every creature near the show that can watch it stops: held for
        ``watch_turns`` (the longer of the two holds, so it watches while
        the show lasts and a moment after, never the sum of every turn's).
        The watch line is said once, and only of one the show really held;
        one that does not stop (a named foe, the mindless, a swarm that
        cannot be stunned) is told once as unmoved (round 3)."""
        from monster import fill
        d = stray_kids.data()['stars']
        visible = getattr(self, 'visible', set()) or set()
        for m in stray_kids.near_show(self.monsters, stars, self.dungeon):
            seen = (m.x, m.y) in visible and getattr(m, '_unseen', False) is not True
            if stray_kids.can_watch(m):
                m.hold('stunned', int(d['watch_turns']))
                if not m.has_effect('stunned'):
                    continue                       # its nature or its will refused it
                if not m.__dict__.get('_sk_watching') and seen:
                    self.add_message(fill(m, d['watch_line']), 'success')
                m._sk_watching = True
            elif seen and not m.__dict__.get('_sk_unmoved'):
                m._sk_unmoved = True
                key = 'unmoved_named' if m._is_named_foe() else 'unmoved'
                if d.get(key):
                    self.add_message(fill(m, d[key]), 'info')

    def _stray_kids_show_tick(self) -> None:
        stars = [m for m in self.monsters if stray_kids.is_star(m) and m.alive]
        if not stars:
            return
        d = stray_kids.data()['stars']
        self._stray_kids_hold_the_room(stars)
        rng = self._stray_kids_rng()
        visible = getattr(self, 'visible', set()) or set()
        seen = [s for s in stars if (s.x, s.y) in visible]
        if seen and rng.random() < float(stray_kids.data()['shouting']['line_chance']):
            self._stray_kids_say(rng.choice(seen), rng.choice(d['lines']), 'success')
        gone = []
        for s in stars:
            s._sk_turns = int(s.__dict__.get('_sk_turns', 0)) - 1
            if s._sk_turns <= 0:
                gone.append(s)
        if gone:
            self.monsters[:] = [m for m in self.monsters if m not in gone]
            if len(gone) == len(stars):
                self._stray_kids_bow()

    def _stray_kids_bow(self) -> None:
        """The show is over: the bow, and the room forgets it watched."""
        self.add_message(stray_kids.data()['stars']['bow'], 'success')
        for m in self.monsters:
            m.__dict__.pop('_sk_watching', None)
            m.__dict__.pop('_sk_unmoved', None)

    def _stray_kids_leaving(self) -> None:
        """The hero leaves the floor in the middle of a show: the stars came
        for him and do not stay behind, so the show ends here with its bow
        (a revisit never finds it running on; data/stray_kids.json
        stars._bow_doc). Called by Game._change_level before the floor is
        saved."""
        monsters = getattr(self, 'monsters', None)
        if not monsters or not any(stray_kids.is_star(m) for m in monsters):
            return
        monsters[:] = [m for m in monsters if not stray_kids.is_star(m)]
        self._stray_kids_bow()

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
        pack. On the stage with the band still standing: the dance-off at
        once (no walk, no banner)."""
        if not getattr(self.player, 'qa_tools', False):
            return
        import decor
        st = self._stray_kids_state()
        if self._on_stray_kids_stage() and stray_kids.the_band(self.monsters):
            self.add_message("[QA] The dance-off, at once.", 'info')
            self._stray_kids_challenge()
            return
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
                   'pos': [int(spot[0]), int(spot[1])], 'challenge': None, 'dancing': None,
                   'lost': 0})
        # A stage already played this run is struck: the next touch builds it fresh.
        from boss_levels import STRAY_KIDS_STAGE
        saved = getattr(getattr(self, 'level_mgr', None), '_saved', None)
        if isinstance(saved, dict):
            saved.pop(STRAY_KIDS_STAGE, None)
        self.add_message("[QA] A Stray Kids idol is set down beside you. Walk into it twice.", 'info')
