"""RaceMixin: the Underway Run, the game's side (the scoring is src/race.py,
the track src/underway_run.py, the words data/bococho.json ``race``).

* The trip: Varro takes the fee (bococho_encounter ``_bc_challenge``) and
  ``_enter_underway_run`` takes the hero to the track (boss_levels.
  UNDERWAY_RUN, a side floor, as the Zombie Stage is). The young Bococho and
  Brassbeak stand at the line; Varro at the paddock rail.
* The race screen (STATE_RACE, ``_race_input``): before each leg the hero
  picks Sprint or Pace (and, on the cheat leg, the lane: Varro's taunt is
  the tell); the leg is one maths chain at his own maths tier (the weapon
  in his hand, as in combat). The birds move round the oval on the map
  after each leg, with a line of commentary; the finish has its photo.
  The whole oval stays in view above the race panel while the race is on
  (``_race_view``), each bird ringed and named.
* The way back (``_exit_underway_run``): the finish, a forfeit (Esc and Y),
  the gate stair, a potion of gain level or Hermes' step. Leaving before
  the finish gives Varro the race.
* A save mid-race loads with the race at the leg not yet run
  (``_race_resume``, from Game.update).
"""
from __future__ import annotations

import race as R
import bococho_encounter as bc
from game_states import STATE_PLAYER, STATE_QUIZ, STATE_RACE, STATE_DEAD


class RaceMixin:

    # ---- state -------------------------------------------------------------

    def _race(self) -> dict | None:
        r = self._bococho_state().get('race')
        return r if isinstance(r, dict) else None

    def _on_underway_run(self) -> bool:
        from boss_levels import UNDERWAY_RUN
        return getattr(self, 'dungeon_level', 0) == UNDERWAY_RUN

    def _race_full_view(self) -> bool:
        """The whole oval in view while the race is on (game_render.render)."""
        return self._on_underway_run() and self.state in (STATE_RACE, STATE_QUIZ) \
            and self._race() is not None

    def _race_view(self):
        """(centre x, centre y, tile size) that frames the whole oval above
        the race panel (game_render.render), or None when no race is on."""
        if not self._race_full_view():
            return None
        import layout
        import underway_run
        from ui_scale import px as S
        panel_h = int(self.__dict__.get('_race_panel_h') or S(300))
        room = max(S(120), layout.WINDOW_H - panel_h - S(16))
        ow = 2 * underway_run._OUT[0] + 3
        oh = 2 * underway_run._OUT[1] + 3
        ts = max(4, min(layout.MAP_W // ow, room // oh))
        cy = underway_run._CY + int(round((layout.GAME_H / 2 - room / 2) / ts))
        return underway_run._CX, cy, ts

    def _race_tier(self) -> int:
        """The hero's own maths tier, as in combat: the weapon in his hand."""
        w = getattr(self.player, 'weapon', None)
        return int(getattr(w, 'quiz_tier', 1) or 1) if w is not None else 1

    # ---- the trip there and back -------------------------------------------

    def _enter_underway_run(self):
        from boss_levels import UNDERWAY_RUN
        st = self._bococho_state()
        st['races'] = int(st.get('races', 0) or 0) + 1
        seed = (int(st.get('seed', 0) or 0) * 1009 + st['races'] * 7) & 0xFFFFFFFF
        st['race'] = R.new_race(seed, self._race_tier())
        self.state = STATE_PLAYER
        # A track raced before is laid out fresh: the birds at the line.
        saved = getattr(getattr(self, 'level_mgr', None), '_saved', None)
        if isinstance(saved, dict):
            saved.pop(UNDERWAY_RUN, None)
        try:
            self._change_level(UNDERWAY_RUN, enter_from_top=True, via='bococho')
        except Exception:
            from game_log import log_error
            log_error('game_race._enter_underway_run: recovered from an error')
            st['race'] = None
            return
        cfg = bc.data()['race']
        for line in cfg['arrival']:
            self.add_message(line, 'info')
        self.add_message(cfg['door_line'], 'info')
        self._race_place_runners()
        self._race_open('intro')

    def _exit_underway_run(self):
        """Back to the camp: the race finished, forfeited, or left."""
        st = self._bococho_state()
        r = self._race()
        won = False
        if r is not None:
            if r.get('done') and not r.get('forfeit'):
                won = bool(R.outcome(r)['won'])
            elif not r.get('done'):
                r['forfeit'] = True
                self.add_message(bc.data()['race']['forfeit'], 'warning')
        st['race'] = None
        back = int(st.get('floor') or 0) or max(
            1, int(getattr(self.player, 'deepest_floor_reached', 1) or 1))
        self.state = STATE_PLAYER
        try:
            self._change_level(back, enter_from_top=True, via='bococho')
        except Exception:
            from game_log import log_error
            log_error('game_race._exit_underway_run: recovered from an error')
            return
        # Beside the camp: arriving on the up stair of the camp's floor is a
        # long walk, so the hero comes back by the young Bococho's post.
        self._race_land_at_camp()
        self._bococho_after_race(won)

    def _race_land_at_camp(self):
        young = self._bococho_here('young')
        if young is None:
            return
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters)) | set(self._occupants(hero=False))
        for r in (1, 2, 3):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    t = (young.x + dx, young.y + dy)
                    if (max(abs(dx), abs(dy)) == r and self.dungeon.is_walkable(*t)
                            and t not in taken
                            and t not in self.dungeon.__dict__.get('fixture_blocks', ())):
                        self.player.x, self.player.y = t
                        self._refresh_fov()
                        return

    # ---- the runners on the map ---------------------------------------------

    def _race_place_runners(self):
        """The young Bococho and Brassbeak at the line, Varro at the paddock rail."""
        self.monsters[:] = [m for m in self.monsters if bc.role(m) != 'racer']
        d = bc.data()
        lvl = int(self._bococho_state().get('floor') or 51)
        hero_bird = bc.make_creature('young', 0, 0, lvl)
        rival = bc.make_creature('bird', 0, 0, lvl)
        rival.name = d['race']['rival_name']
        for m, who in ((hero_bird, 'hero'), (rival, 'rival')):
            m._bococho_role = 'racer'
            m._racer = who
            self.monsters.append(m)
        varro = bc.make_creature('varro', 0, 0, lvl)
        varro._bococho_role = 'racer'
        varro._racer = 'man'
        ex = getattr(self.dungeon, 'race_exit', None)
        spot = None
        if ex:
            for dx, dy in ((3, -2), (4, -2), (2, -2), (5, -1), (3, -1)):
                t = (ex[0] + dx, ex[1] + dy)
                if self.dungeon.is_walkable(*t) and not any((m.x, m.y) == t for m in self.monsters):
                    spot = t
                    break
        if spot is not None:
            varro.x, varro.y = spot
            self.monsters.append(varro)
        self._race_move_runners()

    def _race_runner(self, who: str):
        return next((m for m in self.monsters or () if bc.role(m) == 'racer'
                     and getattr(m, '_racer', '') == who), None)

    def _race_move_runners(self):
        import underway_run
        r = self._race()
        if r is None:
            return
        inside = underway_run.loop(self.dungeon, 0)
        outside = underway_run.loop(self.dungeon, 1)
        if not inside or not outside:
            return
        hi, _vi = R.positions(r, len(inside))
        _hi, vi = R.positions(r, len(outside))
        for who, ring, idx in (('hero', inside, hi), ('rival', outside, vi)):
            m = self._race_runner(who)
            if m is None:
                continue
            busy = {(o.x, o.y) for o in self.monsters if o is not m and o.alive}
            busy |= set(self._occupants())
            for step in range(len(ring)):
                t = ring[(idx - step) % len(ring)]
                if t not in busy:
                    m.x, m.y = t
                    break
        self._refresh_fov()

    def _underway_light(self, sight: int) -> None:
        """The cavern is lit by its lanterns: from anywhere on the Underway
        Run the hero sees the whole track (never while blind)."""
        if not self._on_underway_run() or sight <= 1:
            return
        import underway_run
        lit = set()
        for ring in (getattr(self.dungeon, 'race_loops', None) or ()):
            lit |= set(ring)
        d = self.dungeon
        for y in range(d.height):
            for x in range(d.width):
                if underway_run._inside(x, y, underway_run._OUT[0] + 1, underway_run._OUT[1] + 1):
                    lit.add((x, y))
        self.visible |= lit
        self.dungeon.explored |= lit

    # ---- the race screen ---------------------------------------------------

    def _race_open(self, phase: str):
        self._race_phase = phase
        self._race_lines = []
        if not hasattr(self, '_race_lane') or phase == 'intro':
            self._race_lane = 'inside'
        self.state = STATE_RACE

    def _race_resume(self):
        """A save made mid-race loads at the leg not yet run (Game.update)."""
        r = self._race()
        if r is None or not self._on_underway_run():
            return False
        if self.state != STATE_PLAYER:
            return False
        if not self._race_runner('hero'):
            self._race_place_runners()
        self._race_open('finish' if r.get('done') else 'choose')
        return True

    def _race_input(self, key: int):
        import pygame
        r = self._race()
        if r is None:
            self.state = STATE_PLAYER
            return
        phase = getattr(self, '_race_phase', 'choose')
        go = key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        if phase == 'forfeit_ask':
            if key in (pygame.K_y,):
                self._exit_underway_run()
            elif key in (pygame.K_n, pygame.K_ESCAPE):
                self._race_phase = getattr(self, '_race_back_phase', 'choose')
            return
        if phase == 'finish':
            if go or key == pygame.K_ESCAPE:
                self._exit_underway_run()
            return
        if key == pygame.K_ESCAPE:
            self._race_back_phase = phase
            self._race_phase = 'forfeit_ask'
            return
        if phase in ('intro', 'leg'):
            if go:
                self._race_phase = 'finish' if r.get('done') else 'choose'
                if self._race_phase == 'choose':
                    self._race_lane = 'inside'
            return
        # choose
        if key in (pygame.K_1, pygame.K_KP1):
            self._race_start_leg('sprint')
        elif key in (pygame.K_2, pygame.K_KP2):
            self._race_start_leg('pace')
        elif key in (pygame.K_3, pygame.K_KP3, pygame.K_l) and R.is_cheat_leg(r):
            self._race_lane = 'outside' if getattr(self, '_race_lane', 'inside') == 'inside' else 'inside'

    def _race_start_leg(self, mode: str):
        r = self._race()
        if r is None or r.get('done'):
            return
        cfg = bc.data()['race']
        lane = getattr(self, '_race_lane', 'inside') if R.is_cheat_leg(r) else 'inside'
        leg = int(r['leg']) + 1
        self.quiz_title = cfg['quiz_title'].format(leg=leg, legs=r['legs'])
        self.state = STATE_QUIZ

        def on_complete(result):
            self._race_leg_done(int(getattr(result, 'score', 0) or 0), mode, lane)

        self.quiz_engine.start_quiz(
            mode='chain', subject='math', tier=int(r['tier']), callback=on_complete,
            max_chain=int(cfg['max_chain']),
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('math'),
            base_seconds=self.player.get_quiz_timer('math'),
        )

    def _race_leg_done(self, chain: int, mode: str, lane: str):
        r = self._race()
        if r is None:
            self.state = STATE_PLAYER
            return
        cfg = bc.data()['race']
        out = R.run_leg(r, chain, mode, lane)
        lines = [cfg['events'][e] for e in out['events'] if cfg['events'].get(e)]
        # (In words, "a length" or "7 lengths": a winded leg through the
        # caltrops can be a single length, and "1 lengths" was said.)
        lines.append(cfg['chain'].format(chain=chain, run=self._race_gap_words(out['hero_run']),
                                         rival_run=self._race_gap_words(out['varro_run'])))
        if r.get('done'):
            lines = lines[-1:]           # the home straight: the run, then the finish
            res = R.outcome(r)
            gap_words = self._race_gap_words(res['gap'])
            if res['photo']:
                lines.append(cfg['photo'])
            if res['won']:
                lines.append(cfg['won_beak'] if res['gap'] < 0.5 else cfg['won_by'].format(gap=gap_words))
                lines.append(cfg['won'])
                self._chron('milestone', cfg['won_chronicle'], once='bococho:race_won')
            else:
                lines.append(cfg['lost_by'].format(gap=gap_words))
                lines.append(cfg['lost'])
                self._chron('milestone', cfg['lost_chronicle'], once='bococho:race_lost')
            # The Seeker (First Past the Post, Slow and Steady) and the
            # quirks (The Tortoise's Pace): the race as run.
            sprints = sum(1 for h in r.get('history') or () if h.get('mode') == 'sprint')
            self._seeker_event('race', won=bool(res['won']), sprints=int(sprints),
                               photo=bool(res['photo']))
            _qs = getattr(self, 'quirk_system', None)
            if _qs is not None:
                _qs.on_race(bool(res['won']), int(sprints))
            self._race_phase = 'finish'
        else:
            st = R.standing(r)
            lines.append(cfg['standing'][st].format(gap=self._race_gap_words(R.gap(r))))
            self._race_phase = 'leg'
        for line in lines:
            self.add_message(line, 'info')
        self._race_lines = lines
        self._race_move_runners()
        self.state = STATE_RACE
        self._advance_turn()
        if self.player.is_dead() or self.state == STATE_DEAD:
            return                      # (a poison can still kill between legs)
        self.state = STATE_RACE

    def _race_gap_words(self, gap: float) -> str:
        cfg = bc.data()['race']
        n = R.lengths(gap)
        return cfg['lengths_one'] if n == 1 else cfg['lengths_many'].format(n=n)

    def _race_panel(self) -> dict:
        """What the race screen shows now: {'title', 'lines', 'options',
        'footer'} (the drawing is game_bococho_render)."""
        r = self._race() or {}
        cfg = bc.data()['race']
        phase = getattr(self, '_race_phase', 'choose')
        legs = int(r.get('legs', cfg['legs']))
        leg = int(r.get('leg', 0)) + 1
        pos = cfg['positions'].format(hero=R.lengths(r.get('hero', 0)) if r.get('hero') else 0,
                                      rival=R.lengths(r.get('varro', 0)) if r.get('varro') else 0)
        wind = cfg['wind'].format(wind=int(round(float(r.get('wind', 100)))))
        out = {'title': cfg['title'], 'lines': [], 'status': '', 'options': [], 'footer': ''}
        if phase == 'intro':
            out['lines'] = list(cfg['arrival'][1:]) + [cfg['how']]
            out['footer'] = "Enter: to the line   |   Esc: leave the race"
        elif phase == 'choose':
            out['title'] = f"{cfg['title']}: {cfg['choose'].format(leg=leg, legs=legs)}"
            out['lines'] = [cfg['taunts'][min(leg - 1, len(cfg['taunts']) - 1)]]
            out['status'] = f"{pos} {wind}"
            if r.get('winded'):
                out['status'] = f"{out['status']} {cfg['winded_now']}"
            out['options'] = [('1', cfg['modes']['sprint']), ('2', cfg['modes']['pace'])]
            if R.is_cheat_leg(r):
                out['options'].append(('3', cfg['lane_line'][getattr(self, '_race_lane', 'inside')]))
                out['footer'] = f"1-2: run the leg   |   3: {cfg['lane_key']}   |   Esc: leave the race"
            else:
                out['footer'] = "1-2: run the leg   |   Esc: leave the race"
        elif phase == 'leg':
            out['title'] = f"{cfg['title']}: {cfg['choose'].format(leg=leg - 1, legs=legs)}"
            out['lines'] = list(getattr(self, '_race_lines', []) or [])
            out['status'] = f"{pos} {wind}"
            out['footer'] = "Enter: the next leg   |   Esc: leave the race"
        elif phase == 'finish':
            out['lines'] = list(getattr(self, '_race_lines', []) or [])
            out['status'] = pos
            out['footer'] = cfg['back']
        else:
            out['lines'] = [cfg['forfeit_ask']]
            out['footer'] = "Y: leave the race   |   N: stay"
        return out
