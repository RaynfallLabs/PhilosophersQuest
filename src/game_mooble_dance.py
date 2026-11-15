"""The Mooble's dance screen (STATE_MOOBLE_DANCE): the one action in the game
that is not a quiz (RARE_PETS_PLAN_2026_11_14 section 2; Brandon: "kids
have to win the rhythm game... offer to let the player practice the dance
before a dance off").

The screen only draws and reads keys; every judgement is rhythm.py's. Time is
real elapsed time from pygame's clock (``_mooble_now``), never turns or
frames: the beat is a SCHEDULE laid out when the dance starts
(rhythm.timeline), each key is stamped with the time it was read, and a slow
frame neither steals a beat nor moves a step.

A dance, after Space starts it:
  * a count-in of four beats ("Five, Six, Seven, Eight"),
  * his CALL: two bars in which he dances the phrase (his pose for each
    step, its arrow lit, a chime),
  * the RESPONSE: the same two bars for the hero to echo it on the arrow
    keys; each arrow lights as its beat comes (it reads with the sound off),
    and each step is judged Perfect, Good or Miss as it passes.
His bobble pulses on every beat, and a tone from sound_system marks it (a
brighter one on each bar's first beat). The soundtrack is held while a
dance plays (music.hold / release), so the beat is clear.

PRACTICE is free and has no stakes: Esc stops it any time, Enter dances it
again (as often as wanted), D goes on to the dance-off. The DANCE-OFF must be
danced through; its result goes back to the Mooble's screen
(mooble_encounter._mooble_dance_done). A save made while the screen is open
opens it again on load, at the start of the phrase (``game._mooble['dancing']``).

His SPECIAL, the Dance of the Dark (Brandon, 2026-11-14: "that should
trigger a dance rhythm game as well, where your success determines how
powerful it is (no practice, just a count in)"), uses the same screen with no
call: a count-in ("5, 6, 7, 8!") and then his phrase for his stage, danced as
its arrows light. Its cooldown is spent when it starts; how well it went
(mooble_encounter.dance_band) sets its reach, its hold and how many it holds.
No monster acts while it is danced: it is his turn, like a quiz.

What the screen shows is carried by the dance itself (``_mdance``: its
timeline, windows, pass mark, words and pictures), so the screen and
rhythm.py serve any dance laid out the same way.
"""
from __future__ import annotations

import mooble_encounter as mo
import rhythm
from game_states import STATE_MOOBLE, STATE_MOOBLE_DANCE

try:
    import sound_system as _snd
except Exception:          # pragma: no cover - sound is optional
    _snd = None


def _keys():
    import pygame
    return {
        pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right', pygame.K_UP: 'up', pygame.K_DOWN: 'down',
        pygame.K_KP4: 'left', pygame.K_KP6: 'right', pygame.K_KP8: 'up', pygame.K_KP2: 'down',
    }


def _play(name: str):
    if _snd is not None:
        try:
            _snd.play(name)
        except Exception:
            pass


class MoobleDanceMixin:
    """The dance screen's state, keys, beat and drawing."""

    # ---- the clock ----------------------------------------------------------

    def _mooble_now(self) -> int:
        """Milliseconds on pygame's clock (a test may set ``_mooble_clock_fn``)."""
        fn = self.__dict__.get('_mooble_clock_fn')
        if fn is not None:
            return int(fn())
        import pygame
        return int(pygame.time.get_ticks())

    # ---- open and close -------------------------------------------------------

    def _mooble_open_dance(self, mode: str):
        """Open the dance screen for his next visit's phrase: 'practice' or
        'dance' (the dance-off). It waits for Space before the count-in."""
        m = getattr(self, '_mooble_npc', None) or self._mooble_here()
        if m is None:
            return
        self._mooble_npc = m
        d = mo.data()
        dd = d['dance']
        spec = mo.visit_spec(m)
        tl = rhythm.timeline(spec['steps'], spec['bpm'], int(dd['lead_beats']), int(dd['phrase_beats']))
        mode = 'dance' if mode == 'dance' else 'practice'
        if mode == 'practice':
            # Practised before this visit's dance-off (the Seeker's dance_off
            # event and Terpsichore's Step read it; cleared by the dance-off).
            self._mooble_state()['practised'] = True
        visit = min(mo.dances(m) + 1, len(dd['visits']))
        self._mdance = self._mooble_dance_spec(
            mode, tl, spec['bpm'],
            title=d['screen']['title_dance' if mode == 'dance' else 'title_practice'],
            info=f"Dance {visit} of {len(dd['visits'])}: {int(spec['bpm'])} beats a minute")
        self._mooble_state()['dancing'] = {'mode': mode}
        self.state = STATE_MOOBLE_DANCE

    def _mooble_dance_spec(self, mode: str, tl: dict, bpm, *, title: str, info: str) -> dict:
        """Everything the screen needs for one dance: its timeline, the
        judging windows and pass mark (data/mooble.json ``dance``), its
        words and his pictures."""
        d = mo.data()
        dd = d['dance']
        return {
            'mode': mode, 'tl': tl, 'bpm': int(bpm), 'title': title, 'info': info,
            'good_ms': float(dd['good_ms']), 'perfect_ms': float(dd['perfect_ms']),
            'stray_is_miss': bool(dd.get('stray_is_miss', True)),
            'pass_share': float(dd['pass_share']), 'max_misses': int(dd['max_misses']),
            'words': d['screen'],
            'poses': {'idle': d['sprite_down'], **{k: f'mooble_dance_{k}' for k in rhythm.DIRS}},
            't0': None, 'phase': 'ready',
            'presses': [], 'beat_played': -1, 'step_played': -1,
            'decided': 0, 'flash': None, 'result': None, 'won': False,
        }

    def _mooble_special_dance(self, pet, special: dict):
        """The Dance of the Dark, danced: the count-in starts at once (no
        practice, no Space), then his phrase for his stage with no call. The
        cooldown is spent now: a dance abandoned is a dance spent."""
        sd = mo.special_spec()
        ph = mo.special_phrase(pet.stage)
        tl = rhythm.timeline(ph['steps'], ph['bpm'], int(sd.get('lead_beats', 4)),
                             int(sd.get('phrase_beats', 8)), call=False)
        md = self._mooble_dance_spec('special', tl, ph['bpm'], title=sd.get('title', special['name']),
                                     info=f"{pet.name}: {int(ph['bpm'])} beats a minute")
        md['pet'] = pet
        md['special'] = special
        pet.use_special(special['id'])
        self._mdance = md
        self.state = STATE_MOOBLE_DANCE
        self._mooble_dance_start()

    def _mooble_dance_start(self):
        md = self._mdance
        md.update({'t0': self._mooble_now(), 'phase': 'play', 'presses': [], 'beat_played': -1,
                   'step_played': -1, 'decided': 0, 'flash': None, 'result': None, 'won': False})
        self._mooble_music(True)

    def _mooble_music(self, quiet: bool):
        """The soundtrack steps aside while the dance's beat plays: held when
        a dance begins, released when it ends or is left (music.py)."""
        if bool(self.__dict__.get('_mooble_music_held')) == bool(quiet):
            return
        self.__dict__['_mooble_music_held'] = bool(quiet)
        try:
            import music
            (music.hold if quiet else music.release)()
        except Exception:
            pass

    def _mooble_dance_back(self):
        """Leave the screen without a dance-off danced (practice, or a
        dance-off not started): back to his choices, nothing changed."""
        self._mooble_music(False)
        self._mdance = None
        self._mooble_state()['dancing'] = None
        self._mooble_phase = 'options'
        self.state = STATE_MOOBLE

    # ---- judging ------------------------------------------------------------

    def _mooble_windows(self) -> dict:
        md = self._mdance
        good = float(md['good_ms'])
        return {'good_ms': good, 'perfect_ms': float(md['perfect_ms']),
                'attach_ms': rhythm.attach_window(md['tl']['beat_ms'], good),
                'stray_is_miss': bool(md['stray_is_miss'])}

    def _mooble_judge(self, now_rel=None) -> dict:
        md = self._mdance
        return rhythm.judge(md['tl']['response'], md['presses'], now_ms=now_rel, **self._mooble_windows())

    def _mooble_flash(self, now_rel: float):
        """The newest judgement, shown big for a moment: a step decided since
        the last look, or a stray key (a miss)."""
        md = self._mdance
        res = self._mooble_judge(now_rel)
        decided = [s for s in res['steps'] if s['grade'] != rhythm.PENDING]
        n = len(decided) + res['strays']
        if n > md['decided']:
            if res['strays'] > md.get('strays_seen', 0):
                grade = rhythm.MISS
            else:
                grade = max(decided, key=lambda s: s['t'])['grade'] if decided else rhythm.MISS
            md['flash'] = (grade, now_rel)
            md['decided'] = n
            md['strays_seen'] = res['strays']
        return res

    def _mooble_end_ms(self) -> float:
        tl = self._mdance['tl']
        last = max((t for t, _d in tl['response']), default=tl['response_start'])
        return max(tl['response_end'], last + self._mooble_windows()['attach_ms'])

    # ---- every frame --------------------------------------------------------

    def _mooble_dance_tick(self):
        """Called every frame while the screen is open (Game.update): the
        beat's tone, his step chimes, timed-out steps and the end. Only the
        newest beat sounds after a slow frame; the schedule never moves."""
        md = getattr(self, '_mdance', None)
        if not md or md['phase'] != 'play':
            return
        t = self._mooble_now() - md['t0']
        tl = md['tl']
        b = int(t // tl['beat_ms']) if t >= 0 else -1
        if md['beat_played'] < b < tl['beats']:
            md['beat_played'] = b
            _play('dance_bar' if b % 4 == 0 else 'dance_beat')
        k = -1
        for i, (st, _d) in enumerate(tl['call']):
            if st <= t:
                k = i
        if k > md['step_played']:
            md['step_played'] = k
            _play('dance_step_' + tl['call'][k][1])
        self._mooble_flash(t)
        if t >= self._mooble_end_ms():
            self._mooble_dance_finish()

    def _mooble_dance_finish(self):
        md = self._mdance
        res = self._mooble_judge(None)
        md['result'] = res
        md['won'] = rhythm.passed(res, md['pass_share'], md['max_misses'])
        md['phase'] = 'result'
        self._mooble_music(False)
        if md['mode'] == 'special':
            # As strong as it was danced (mooble_encounter.dance_band).
            band = mo.dance_band(res)
            md['band'] = band
            md['held'] = self._mooble_dance_of_the_dark(md['pet'], md['special'], band)
            _play('trait' if band.get('name') != 'flop' else 'lock_fail')
            return
        _play('trait' if md['won'] else 'lock_fail')

    # ---- keys -----------------------------------------------------------------

    def _mooble_dance_key(self, key: int):
        import pygame
        md = getattr(self, '_mdance', None)
        if not md:
            self.state = STATE_MOOBLE
            return
        if md['phase'] == 'ready':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._mooble_dance_start()
            elif key == pygame.K_ESCAPE:
                self._mooble_dance_back()
            return
        if md['phase'] == 'play':
            d = _keys().get(key)
            if d is not None:
                t = self._mooble_now() - md['t0']
                tl = md['tl']
                attach = self._mooble_windows()['attach_ms']
                if tl['response_start'] - attach <= t <= self._mooble_end_ms():
                    md['presses'].append((t, d))
                    _play('dance_step_' + d)
                    self._mooble_flash(t)
            elif key == pygame.K_ESCAPE and md['mode'] == 'practice':
                self._mooble_dance_back()
            return
        # result
        if md['mode'] == 'special':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                from game_states import STATE_PLAYER
                self._mooble_music(False)
                self._mdance = None
                self.state = STATE_PLAYER
                self._advance_turn()          # his dance was the turn
            return
        if md['mode'] == 'practice':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._mooble_dance_start()    # again, as often as wanted
            elif key in (pygame.K_d, pygame.K_2, pygame.K_KP2):
                # On to the dance-off, if it is not too soon (his screen says).
                self._mooble_dance_back()
                self._mooble_dance_off()
            elif key == pygame.K_ESCAPE:
                self._mooble_dance_back()
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
            res, won = md['result'], md['won']
            self._mooble_music(False)
            self._mdance = None
            self._mooble_state()['dancing'] = None
            self._mooble_dance_done(res, won)

    # ---- drawing ------------------------------------------------------------

    def _draw_mooble_dance(self):
        """The dance: his picture and bobble on the left, the beat's two rows
        of steps on the right (his, then yours), the words above them."""
        import pygame
        import layout
        import lore_art
        from ui_scale import px as S
        from fantasy_ui import (FP, get_font, draw_dark_panel, draw_overlay, panel_band,
                                display_text)
        from game_render import _centre_x, _centre_y
        md = getattr(self, '_mdance', None)
        if not md:
            return
        sc = md['words']
        tl = md['tl']
        bm = tl['beat_ms']
        border = FP.AMBER_ACCENT
        t = (self._mooble_now() - md['t0']) if md['phase'] == 'play' else None
        special = md['mode'] == 'special'
        sd = mo.special_spec() if special else {}

        draw_overlay(self.screen, 200)
        bw = min(S(940), layout.WINDOW_W - S(48))
        bh = min(S(600), layout.WINDOW_H - S(48))
        panel = pygame.Rect(_centre_x(bw), _centre_y(bh), bw, bh)
        draw_dark_panel(self.screen, panel, border_color=border)
        title = md['title']
        if panel_band('panel', panel):
            b = panel_band('panel', panel)
            top = self._ui_header(panel, title, border_color=border, h=48)
            _div, _keys, foot_bottom = self._ui_footer_metrics(panel)
            body = pygame.Rect(panel.x + b + S(24), top + S(6),
                               panel.w - 2 * (b + S(24)), foot_bottom - top - S(10))
        else:
            from fantasy_ui import draw_header_bar
            draw_header_bar(self.screen, (panel.x, panel.y, panel.w, S(44)), text=title,
                            font=get_font('heading', 20), text_color=FP.GOLD_BRIGHT,
                            accent=border, frame=(panel, border))
            body = pygame.Rect(panel.x + S(28), panel.y + S(64), panel.w - S(56), panel.h - S(130))

        # -- his picture, his pose for the step, and the bobble on the beat --
        poses = md['poses']
        pose = poses['idle']
        if t is not None:
            # His call, or (his special, with no call) the steps he dances
            # with you: his pose for each, as it comes.
            for st, dirn in (tl['call'] or tl['response']):
                if st <= t < st + 0.75 * bm:
                    pose = poses.get(dirn, pose)
        pic_px = S(160)
        pic = lore_art.plate('monster', mo.art(pose), pic_px)
        left_w = pic_px + S(24)
        bob_y = body.y + S(26)
        cx = body.x + left_w // 2
        pulse = 0.0
        if t is not None and t >= 0 and t < tl['beats'] * bm:
            pulse = max(0.0, 1.0 - (t % bm) / bm)
        rad = int(S(10) + S(10) * pulse)
        glow = pygame.Surface((S(64), S(64)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 90, 80, int(60 + 150 * pulse)), (S(32), S(32)), min(S(31), rad + S(8)))
        self.screen.blit(glow, (cx - S(32), bob_y - S(32)))
        pygame.draw.line(self.screen, FP.PARCHMENT_DARK, (cx, bob_y + rad), (cx, bob_y + S(34)), max(1, S(2)))
        pygame.draw.circle(self.screen, (230, 50, 50), (cx, bob_y), rad)
        pygame.draw.circle(self.screen, (255, 200, 190), (cx - rad // 3, bob_y - rad // 3), max(2, rad // 3))
        well = pygame.Rect(body.x, bob_y + S(36), pic_px + S(8), pic_px + S(8))
        pygame.draw.rect(self.screen, FP.MIDNIGHT, well)
        if pic is not None:
            self.screen.blit(pic, (well.x + S(4) + (pic_px - pic.get_width()) // 2,
                                   well.y + S(4) + (pic_px - pic.get_height()) // 2))
        pygame.draw.rect(self.screen, border, well, 1)
        small = get_font('body', 16)
        info = md['info']
        self._ui_wrap_text(info, small, FP.FADED_TEXT,
                           pygame.Rect(body.x, well.bottom + S(8), left_w + S(40), S(60)), line_gap=2)

        # -- the words above the rows --------------------------------------
        col = pygame.Rect(body.x + left_w + S(40), body.y, body.right - body.x - left_w - S(40), body.h)
        big = get_font('heading', 26)
        font = get_font('body', 17)
        if md['phase'] == 'ready':
            head = sc['how']
        elif md['phase'] == 'result' and special:
            head = (md.get('band') or {}).get('line', '').replace('{pet}', md['pet'].name)
        elif md['phase'] == 'result':
            head = (sc['dance_pass'] if md['won'] else sc['dance_fail']) if md['mode'] == 'dance' else \
                (sc['practice_pass'] if md['won'] else sc['practice_fail'])
        else:
            beat = int(t // bm) if t >= 0 else 0
            if beat < tl['lead']:
                head = sc['count_in'][min(beat, len(sc['count_in']) - 1)]
            elif t < tl['response_start']:
                head = sc['watch']
            else:
                head = sc['your_turn']
        if special and md['phase'] == 'result':
            hfont_small = True
        else:
            hfont_small = False
        y = col.y
        hfont = font if (md['phase'] == 'ready' or hfont_small) else big
        y = self._ui_wrap_text(display_text(head), hfont, FP.GOLD_BRIGHT if hfont is big else FP.PARCHMENT_LIGHT,
                               pygame.Rect(col.x, y, col.w, S(90)), line_gap=4)
        y = max(y, col.y + S(56)) + S(10)

        # -- the two rows of eight beats -----------------------------------
        res = self._mooble_judge(t if t is not None else None) if md['phase'] != 'ready' else None
        if md['phase'] == 'result':
            res = md['result']
        n = int(tl['phrase_beats'])
        gap = S(6)
        cell = max(S(28), min(S(56), (col.w - (n - 1) * gap) // n))
        label_font = get_font('body', 16)
        grade_font = get_font('body', 16)
        rows = (('call', sc['his_row'], tl['call_start']), ('response', sc['your_row'], tl['response_start']))
        if not tl['call']:
            rows = rows[1:]                   # his special: no call, only your steps
        steps_by_row = {'call': tl['call'], 'response': tl['response']}
        for r_i, (which, label, start) in enumerate(rows):
            self._ui_wrap_text(label, label_font, FP.PARCHMENT, pygame.Rect(col.x, y, col.w, S(22)))
            y += S(24)
            row_rect = pygame.Rect(col.x - S(20), y - S(6), n * cell + (n - 1) * gap + S(40), cell + S(56))
            pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, row_rect)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, row_rect, 1)
            cur = int((t - start) // bm) if (t is not None and start <= t < start + n * bm) else -1
            for i in range(n):
                cr = pygame.Rect(col.x + i * (cell + gap), y, cell, cell)
                pygame.draw.rect(self.screen, FP.MIDNIGHT, cr)
                pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if i == cur else FP.INK_LIGHT, cr,
                                 max(1, S(2)) if i == cur else 1)
            for s_i, (st, dirn) in enumerate(steps_by_row[which]):
                beat_i = int(round((st - start) / bm))
                if not 0 <= beat_i < n:
                    continue
                cr = pygame.Rect(col.x + beat_i * (cell + gap), y, cell, cell)
                # Lit as it comes: faint far off, brightening over the beat
                # before it, full on its beat (it reads with the sound off).
                light = 0.25
                if md['phase'] == 'ready':
                    light = 0.55
                elif t is not None:
                    ahead = st - t
                    if ahead <= 0:
                        light = 1.0 if ahead > -0.6 * bm else 0.6
                    elif ahead < bm:
                        light = 0.35 + 0.65 * (1.0 - ahead / bm)
                elif md['phase'] == 'result':
                    light = 0.6
                colour = _mix(FP.INK_LIGHT, FP.GOLD_BRIGHT, light)
                grade = None
                if which == 'response' and res is not None:
                    grade = res['steps'][s_i]['grade'] if s_i < len(res['steps']) else None
                    if grade == rhythm.PERFECT:
                        colour = FP.SUCCESS_TEXT
                    elif grade == rhythm.GOOD:
                        colour = FP.GOLD_BRIGHT
                    elif grade == rhythm.MISS:
                        colour = FP.DANGER_TEXT_LIGHT
                if light >= 0.99 and grade in (None, rhythm.PENDING):
                    pygame.draw.rect(self.screen, _mix(FP.MIDNIGHT, FP.GOLD, 0.35), cr.inflate(-2, -2))
                _arrow(self.screen, cr, dirn, colour)
                if grade and grade != rhythm.PENDING:
                    word = sc['grades'].get(grade, grade)
                    surf = grade_font.render(word, True, colour)
                    self.screen.blit(surf, (cr.centerx - surf.get_width() // 2, cr.bottom + S(3) + (beat_i % 2) * S(19)))  # staggered: a word may be wider than its cell
            y += cell + S(60)

        # -- the newest judgement, big, for a moment -----------------------
        flash = md.get('flash')
        if md['phase'] == 'play' and flash and t is not None and t - flash[1] < 0.8 * bm:
            g = flash[0]
            colour = {rhythm.PERFECT: FP.SUCCESS_TEXT, rhythm.GOOD: FP.GOLD_BRIGHT}.get(g, FP.DANGER_TEXT_LIGHT)
            surf = big.render(sc['grades'].get(g, g), True, colour)
            self.screen.blit(surf, (col.x, y - S(4)))
        y += S(36) if md['phase'] == 'play' else S(4)

        # -- the pass mark, or the result -----------------------------------
        steps = len(tl['response'])
        need = rhythm.hits_needed(steps, md['pass_share'])
        lines = []
        if md['phase'] == 'result' and res is not None:
            one, many = sc.get('miss_words') or ('{n} miss', '{n} misses')
            misses = (one if res['misses'] == 1 else many).format(n=res['misses'])
            lines.append(sc['result_line'].format(hits=res['hits'], steps=res['total'],
                                                  perfects=res['perfects'], misses=misses))
        if special:
            band = md.get('band')
            if md['phase'] == 'result' and band:
                held_words = sd.get('held_words') or ['{n}', '{n}', '{n}']
                mh = int(band.get('max_held', 99))
                held = (held_words[0] if mh <= 1 else held_words[2] if mh >= 99 else held_words[1]).format(n=mh)
                lines.append(sd.get('result', '').format(label=band.get('label', ''), radius=band.get('radius'),
                                                         turns=band.get('turns'), held=held))
            else:
                lines.append(sd.get('how', ''))
        else:
            lines.append(sc['pass_mark'].format(need=need, steps=steps, misses=md['max_misses']))
        if md['mode'] == 'practice':
            lines.append(sc['practice_note'])
        for ln in lines:
            if y > col.bottom - S(20):
                break
            y = self._ui_wrap_text(display_text(ln), font, FP.PARCHMENT_LIGHT,
                                   pygame.Rect(col.x, y, col.w, col.bottom - y), line_gap=3) + S(6)

        if md['phase'] == 'ready':
            foot = ("Space: start   |   Esc: back")
        elif special:
            foot = sd.get('footer_special' if md['phase'] == 'play' else 'footer_special_done', 'Enter: continue')
        elif md['phase'] == 'play':
            foot = sc['footer_practice'] if md['mode'] == 'practice' else sc['footer_dance']
        else:
            foot = sc['footer_practice_done'] if md['mode'] == 'practice' else sc['footer_dance_done']
        self._ui_footer(panel, foot)


def _mix(a, b, k: float):
    k = max(0.0, min(1.0, float(k)))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def _arrow(surface, rect, direction: str, colour):
    """A plain arrow in ``rect`` pointing ``direction``, drawn (never a font
    glyph, so it reads at any size)."""
    import pygame
    cx, cy = rect.center
    r = max(4, int(min(rect.w, rect.h) * 0.36))
    w = max(2, int(r * 0.45))
    if direction == 'up':
        pts = [(cx, cy - r), (cx + r, cy), (cx + w, cy), (cx + w, cy + r), (cx - w, cy + r), (cx - w, cy), (cx - r, cy)]
    elif direction == 'down':
        pts = [(cx, cy + r), (cx - r, cy), (cx - w, cy), (cx - w, cy - r), (cx + w, cy - r), (cx + w, cy), (cx + r, cy)]
    elif direction == 'left':
        pts = [(cx - r, cy), (cx, cy - r), (cx, cy - w), (cx + r, cy - w), (cx + r, cy + w), (cx, cy + w), (cx, cy + r)]
    else:
        pts = [(cx + r, cy), (cx, cy + r), (cx, cy + w), (cx - r, cy + w), (cx - r, cy - w), (cx, cy - w), (cx, cy - r)]
    pygame.draw.polygon(surface, colour, pts)
