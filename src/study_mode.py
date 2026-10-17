"""Standalone Study Mode quiz.

Launched from the welcome screen (F3). Lets the player pick a subject and
difficulty tier, then runs an untimed quiz that shows the correct answer plus
any educational context after each question. Independent of the main game loop.
"""

import sys

import pygame

from fantasy_ui import FP, ScaledFont, centered_text, draw_divider
from ui_scale import px as S


class StudyMode:
    """Subject/tier picker → untimed quiz → wrong answers show context."""

    # Subject palette is sourced from FP.SUBJECT — see fantasy_ui.py for
    # the canonical table. This list pairs each key with its display name.
    _SUBJECTS = [
        (key, label, FP.SUBJECT[key]) for key, label in [
            ('math',       'Math'),
            ('geography',  'Geography'),
            ('history',    'History'),
            ('animal',     'Animals'),
            ('cooking',    'Cooking'),
            ('science',    'Science'),
            ('philosophy', 'Philosophy'),
            ('grammar',    'Grammar'),
            ('economics',  'Economics'),
            ('theology',   'Theology'),
            ('trivia',     'Trivia'),
            ('ai',         'AI'),
        ]
    ]

    # Fonts follow the UI scale (read on use; SCALE_PLAN.md).
    font_lg = ScaledFont('heading', 32)
    font_md = ScaledFont('body', 22)
    font_sm = ScaledFont('body', 18)
    font_tiny = ScaledFont('body', 16)

    def __init__(self, screen):
        self.screen = screen
        self._questions = []
        self._idx = 0
        self._phase = 'subject'  # subject -> tier -> quiz -> result
        self._subject = None
        self._tier = 1
        self._selected = 0
        self._last_correct = None
        self._correct_count = 0
        self._asked_count = 0

    def run(self, clock):
        """Main study mode loop. Returns when user presses ESC."""
        while True:
            clock.tick(60)
            W, H = self.screen.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                    # The window is read every frame; only the UI scale
                    # needs setting (layout is where it lives).
                    import layout
                    if (event.x, event.y) != (layout.WINDOW_W, layout.WINDOW_H):
                        layout.update(event.x, event.y)
                    continue
                if event.type != pygame.KEYDOWN:
                    continue

                if self._handle_key(event.key):
                    return  # back to welcome

            # Draw — paint the grimoire frame first so all phase drawers
            # land their content inside the panel body.
            self.screen.fill(FP.MIDNIGHT)
            from fantasy_ui import kit_on
            if kit_on():
                # The Midnight Codex kit: one framed page, inset plaque,
                # kit rows / answer cards, key-hint footer inside the frame.
                self._draw_kit(W, H)
                pygame.display.flip()
                continue
            self._draw_frame(W, H)
            if self._phase == 'subject':
                self._draw_subject_picker(W, H)
            elif self._phase == 'tier':
                self._draw_tier_picker(W, H)
            elif self._phase == 'quiz':
                self._draw_quiz(W, H)
            elif self._phase == 'result':
                self._draw_result(W, H)
            pygame.display.flip()

    # Keypad keys do what their main-keyboard twins do (Enter, 1-4).
    _KEY_ALIASES = {
        pygame.K_KP_ENTER: pygame.K_RETURN,
        pygame.K_KP1: pygame.K_1, pygame.K_KP2: pygame.K_2,
        pygame.K_KP3: pygame.K_3, pygame.K_KP4: pygame.K_4,
        pygame.K_KP8: pygame.K_UP,
    }

    def _handle_key(self, key) -> bool:
        """One key press. Returns True when Study Mode should close."""
        import json
        import random
        from paths import data_path

        if key == pygame.K_F11:
            # Full screen works here too (it did nothing outside the game).
            pygame.display.toggle_fullscreen()
            surf = pygame.display.get_surface()
            if surf is not None:
                import layout
                layout.update(*surf.get_size())
            return False
        # Keypad 2 is "down" in the pickers but "answer 2" in the quiz.
        if key == pygame.K_KP2 and self._phase in ('subject', 'tier'):
            key = pygame.K_DOWN
        key = self._KEY_ALIASES.get(key, key)

        if self._phase == 'subject':
            if key == pygame.K_ESCAPE:
                return True  # back to welcome
            if key == pygame.K_UP:
                self._selected = (self._selected - 1) % len(self._SUBJECTS)
            elif key == pygame.K_DOWN:
                self._selected = (self._selected + 1) % len(self._SUBJECTS)
            elif key == pygame.K_RETURN:
                self._subject = self._SUBJECTS[self._selected][0]
                self._selected = 0
                self._phase = 'tier'

        elif self._phase == 'tier':
            if key == pygame.K_ESCAPE:
                self._phase = 'subject'
            elif key == pygame.K_UP:
                self._selected = (self._selected - 1) % 5
            elif key == pygame.K_DOWN:
                self._selected = (self._selected + 1) % 5
            elif key == pygame.K_RETURN:
                self._tier = self._selected + 1
                # Load questions
                try:
                    with open(data_path('data', 'questions', f'{self._subject}.json'), encoding='utf-8') as f:
                        all_qs = json.load(f)
                    self._questions = [q for q in all_qs if q.get('tier', 1) == self._tier]
                    if not self._questions:
                        self._questions = all_qs[:]
                    random.shuffle(self._questions)
                    # ... and each question's choices. The banks store
                    # the answer first for nearly every question and
                    # only the order of QUESTIONS was shuffled, so in
                    # Study Mode the right answer was always choice [1].
                    self._questions = [
                        dict(_q, choices=random.sample(list(_q['choices']), len(_q['choices'])))
                        for _q in self._questions]
                except Exception:
                    self._questions = []
                self._idx = 0
                self._correct_count = 0
                self._asked_count = 0
                self._last_correct = None
                self._phase = 'quiz'

        elif self._phase == 'quiz':
            if key == pygame.K_ESCAPE:
                self._phase = 'subject'
            elif self._questions:
                q = self._questions[self._idx % len(self._questions)]
                choice_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
                ci = choice_map.get(key)
                if ci is not None and ci < len(q['choices']):
                    chosen = q['choices'][ci]
                    # Exactly as the game's QuizEngine.answer: a grammar
                    # question can turn on capitals alone, and case-folding
                    # marked all four case variants correct.
                    is_correct = str(chosen).strip() == str(q['answer']).strip()
                    self._asked_count += 1
                    if is_correct:
                        self._correct_count += 1
                    self._last_correct = is_correct
                    self._last_q = q
                    self._last_chosen = chosen
                    self._phase = 'result'

        elif self._phase == 'result':
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._idx += 1
                if self._idx >= len(self._questions):
                    random.shuffle(self._questions)
                    self._idx = 0
                # Esc quits the quiz, as the footer says (it used to go on
                # to the next question like Enter).
                self._phase = 'subject' if key == pygame.K_ESCAPE else 'quiz'
        return False

    def _draw_frame(self, W, H):
        """Paint the full-viewport grimoire panel that frames every phase."""
        from fantasy_ui import draw_dark_panel, draw_header_bar, draw_divider
        margin = S(24)
        rect = (margin, margin, W - 2 * margin, H - 2 * margin)
        draw_dark_panel(self.screen, rect, border_color=FP.GOLD)
        # Header bar with the current phase's title baked in
        titles = {
            'subject': 'STUDY MODE',
            'tier':    'STUDY: CHOOSE DIFFICULTY',
            'quiz':    'STUDY: QUIZ',
            'result':  'STUDY: RESULT',
        }
        title = titles.get(self._phase, 'STUDY MODE')
        draw_header_bar(self.screen, (margin, margin, W - 2 * margin, S(44)),
                        text=title, font=self.font_lg,
                        text_color=FP.GOLD_BRIGHT, accent=FP.GOLD,
                        frame=(rect, FP.GOLD))
        draw_divider(self.screen, margin + S(20), margin + S(50),
                     W - 2 * margin - 2 * S(20))

    def _draw_score(self, W, text):
        """The running score, right-aligned INSIDE the header strip and
        centred on it. (It used to be drawn at y=20, across the panel's top
        edge; once the header stopped painting over the frame, the two gold
        border lines ran through the middle of it: GROUNDWORK_REVIEW 2.)
        Right edge kept clear of the strip's side diamond (x + w - 15)."""
        from fantasy_ui import draw_shadow_text
        margin, header_h = S(24), S(44)     # the same strip _draw_frame draws
        tw, th = self.font_sm.size(text)
        x = W - margin - S(30) - tw
        y = margin + (header_h - th) // 2
        draw_shadow_text(self.screen, self.font_sm, text, FP.GOLD_PALE, (x, y))

    def _draw_subject_picker(self, W, H):
        # Panel header is painted by _draw_frame; just the sub-line + list here.
        centered_text(self.screen, self.font_sm, "Choose a subject to study", FP.BODY_TEXT, S(100))

        y = S(140)
        for i, (sid, name, color) in enumerate(self._SUBJECTS):
            sel = i == self._selected
            bg = FP.MIDNIGHT_MID if sel else FP.MIDNIGHT
            rect = pygame.Rect(W // 2 - S(200), y, S(400), S(32))
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if sel:
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=4)
            # Don't use raw subject color as text — some (science, grammar)
            # are too dark on the panel bg. Keep text as BODY/GOLD_BRIGHT
            # and let the BORDER carry the subject signal.
            text_col = FP.GOLD_BRIGHT if sel else FP.BODY_TEXT
            surf = self.font_md.render(name, True, text_col)
            self.screen.blit(surf, (rect.x + S(20), rect.y + S(4)))
            y += S(38)

        hint = self.font_tiny.render("Up/Down to select, ENTER to choose, ESC to go back", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - S(30)))

    def _draw_tier_picker(self, W, H):
        subj_name = next(n for s, n, _ in self._SUBJECTS if s == self._subject)
        # Panel header shows phase title; we add subject sub-line.
        centered_text(self.screen, self.font_md, subj_name.upper(), FP.GOLD_PALE, S(90))
        centered_text(self.screen, self.font_sm, "Choose difficulty tier", FP.BODY_TEXT, S(124))

        tier_labels = ["Tier 1 — Easy", "Tier 2 — Medium", "Tier 3 — Hard",
                       "Tier 4 — Expert", "Tier 5 — Master"]
        y = S(150)
        for i, label in enumerate(tier_labels):
            sel = i == self._selected
            bg = FP.MIDNIGHT_MID if sel else FP.MIDNIGHT
            rect = pygame.Rect(W // 2 - S(180), y, S(360), S(36))
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if sel:
                pygame.draw.rect(self.screen, FP.GOLD, rect, 2, border_radius=4)
            surf = self.font_md.render(label, True, FP.GOLD_BRIGHT if sel else FP.BODY_TEXT)
            self.screen.blit(surf, (rect.x + S(20), rect.y + S(6)))
            y += S(44)

        hint = self.font_tiny.render("Up/Down to select, ENTER to choose, ESC to go back", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - S(30)))

    def _draw_quiz(self, W, H):
        if not self._questions:
            centered_text(self.screen, self.font_md, "No questions available for this tier.", FP.WARNING_TEXT, H // 2)
            return

        q = self._questions[self._idx % len(self._questions)]
        score = f"{self._correct_count}/{self._asked_count}" if self._asked_count else "0/0"
        self._draw_score(W, f"Score: {score}")

        # Question
        q_text = q['question']
        lines = self._wrap(q_text, self.font_md, W - 2 * S(60))
        y = S(80)
        for line in lines:
            surf = self.font_md.render(line, True, FP.PARCHMENT_LIGHT)
            self.screen.blit(surf, (S(60), y))
            y += S(30)

        # Choices
        y = max(y + S(30), S(200))
        for i, choice in enumerate(q['choices'][:4]):
            key_label = f"[{i+1}]"
            key_surf = self.font_md.render(key_label, True, FP.GOLD_BRIGHT)
            choice_surf = self.font_md.render(f"  {choice}", True, FP.BODY_TEXT)
            self.screen.blit(key_surf, (S(100), y))
            self.screen.blit(choice_surf, (S(140), y))
            y += S(36)

        hint = self.font_tiny.render("Press 1-4 to answer, ESC to quit", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - S(30)))

    def _draw_result(self, W, H):
        q = self._last_q
        is_correct = self._last_correct

        if is_correct:
            centered_text(self.screen, self.font_lg, "CORRECT!", FP.SUCCESS_TEXT, S(40), shadow=True)
        else:
            centered_text(self.screen, self.font_lg, "INCORRECT", FP.DANGER_TEXT, S(40), shadow=True)
            # Show correct answer
            correct = q['answer']
            centered_text(self.screen, self.font_md, f"The correct answer is: {correct}",
                          FP.GOLD_BRIGHT, S(90))

        # Show question
        q_lines = self._wrap(q['question'], self.font_sm, W - 2 * S(60))
        y = S(140)
        for line in q_lines:
            surf = self.font_sm.render(line, True, FP.FADED_TEXT)
            self.screen.blit(surf, (S(60), y))
            y += S(24)

        # Show context (educational explanation) if available
        from fantasy_ui import display_text as _dt
        context = _dt(q.get('context', ''), sources=True)
        if context:
            y += S(20)
            draw_divider(self.screen, S(60), y, W - 2 * S(60))
            y += S(16)
            ctx_lines = self._wrap(context, self.font_sm, W - 2 * S(60))
            for line in ctx_lines:
                surf = self.font_sm.render(line, True, FP.BODY_TEXT)
                self.screen.blit(surf, (S(60), y))
                y += S(24)
        elif not is_correct:
            y += S(20)
            surf = self.font_tiny.render("(No additional context available for this question)", True, FP.FADED_TEXT)
            self.screen.blit(surf, (S(60), y))

        hint = self.font_tiny.render("Press ENTER or SPACE for next question, ESC to quit", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - S(30)))

    # ------------------------------------------------------------------
    # The Midnight Codex kit (assets/ui). Without the kit the procedural
    # drawers above are used, as before.
    # ------------------------------------------------------------------

    _KIT_TITLES = {
        'subject': 'Study Mode',
        'tier':    'Study: Choose Difficulty',
        'quiz':    'Study: Quiz',
        'result':  'Study: Result',
    }
    _KIT_HINTS = {
        'subject': "Up/Down: select   Enter: choose   Esc: back",
        'tier':    "Up/Down: select   Enter: choose   Esc: back",
        'quiz':    "1-4: answer   Esc: quit",
        'result':  "Enter / Space: next question   Esc: quit",
    }

    # Page widths per phase (UI px): the pickers are a short list, the quiz
    # and its result are reading text (long lines are hard to read).
    _KIT_PAGE_W = {'subject': 640, 'tier': 640, 'quiz': 1240, 'result': 1240}
    _KIT_ROW_H = 34

    def _draw_kit(self, W, H):
        """One framed page, sized to what it holds and centred on the window
        (VISUAL_REVIEW minor 3: at 3440x1440 the full-height page held a
        third of a page of content)."""
        from fantasy_ui import (draw_dark_panel, draw_header_bar, draw_divider,
                                draw_key_hints, key_hints_height, panel_band, KT)
        margin = S(24)
        pw = min(W - 2 * margin, S(self._KIT_PAGE_W.get(self._phase, 1240)))
        b = S(16)
        head_h = S(48)
        kh = key_hints_height()
        inner_w = pw - 2 * (b + S(28))
        content_h = self._kit_content(pygame.Rect(0, 0, inner_w, 10 ** 6), draw=False)
        chrome = 2 * b + head_h + S(14) + S(32) + kh + S(8)
        ph = max(S(260), min(H - 2 * margin, chrome + content_h))
        panel = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
        self.screen.fill(KT.VOID)
        draw_dark_panel(self.screen, panel, border_color=FP.GOLD)
        score_w = 0
        score = None
        if self._phase in ('quiz', 'result'):
            score = (f"Score: {self._correct_count}/{self._asked_count}"
                     if self._asked_count else "Score: 0/0")
            score_w = self.font_sm.size(score)[0] + S(76)
        hr = draw_header_bar(self.screen, (panel.x, panel.y, panel.w, head_h),
                             text=self._KIT_TITLES.get(self._phase, 'Study Mode'),
                             font=self.font_lg, accent=FP.GOLD, right_reserve=score_w,
                             left_reserve=score_w, frame=(panel, FP.GOLD))
        if score:
            # The running score, on the plaque, right-aligned well clear of
            # its scroll-roll end.
            ss = self.font_sm.render(score, True, KT.TEXT_SUB)
            self.screen.blit(ss, (hr.right - S(56) - ss.get_width(),
                                  hr.y + (hr.h - S(4) - ss.get_height()) // 2))
        b = panel_band('panel', panel)
        keys = pygame.Rect(panel.x + b + S(20), panel.bottom - b - S(8) - kh,
                           panel.w - 2 * (b + S(20)), kh)
        draw_divider(self.screen, panel.x + b + S(28), keys.y - S(16),
                     panel.w - 2 * (b + S(28)))
        draw_key_hints(self.screen, keys, self._KIT_HINTS.get(self._phase, ''))
        body = pygame.Rect(panel.x + b + S(28), hr.bottom + S(14),
                           panel.w - 2 * (b + S(28)), keys.y - S(32) - hr.bottom - S(14))
        self._kit_content(body, draw=True)

    def _kit_content(self, body, draw=True) -> int:
        """Draw (or, with ``draw=False``, only measure) the phase's content in
        ``body``; returns the height it takes."""
        if self._phase == 'subject':
            return self._kit_subjects(body, draw)
        if self._phase == 'tier':
            return self._kit_tiers(body, draw)
        if self._phase == 'quiz':
            return self._kit_quiz(body, result=False, draw=draw)
        if self._phase == 'result':
            return self._kit_quiz(body, result=True, draw=draw)
        return 0

    def _kit_rows(self, body, items, top, draw=True) -> int:
        """Centred list of kit rows: items = [(icon name or None, label)].
        Returns the y under the last row."""
        import ui_theme
        from fantasy_ui import KT, readable
        n = len(items)
        gap = S(4)
        row_h = S(self._KIT_ROW_H)
        if draw:
            row_h = max(S(26), min(row_h, (body.bottom - top) // max(1, n) - gap))
        w = min(body.w, S(440))
        x = body.centerx - w // 2
        y = top
        font = self.font_md if row_h >= S(32) else self.font_sm
        for i, (icon, label) in enumerate(items):
            if draw:
                sel = i == self._selected
                rect = pygame.Rect(x, y, w, row_h)
                ui_theme.draw_piece(self.screen, 'row_selected' if sel else 'row', rect)
                tx = rect.x + S(14)
                if icon:
                    isz = min(S(24), row_h - S(8))
                    if ui_theme.draw_icon(self.screen, icon, (tx, rect.centery - isz // 2, isz, isz)):
                        tx += isz + S(12)
                col = readable(KT.TEXT_HEAD if sel else KT.TEXT_BODY,
                               KT.SELECTED if sel else KT.RAISED)
                ts = font.render(label, True, col)
                # Centre the LETTERS, not the line box: Consolas' line box
                # carries a deep descender, so a box-centred label sat high
                # (5 px above, 12 below; VISUAL_REVIEW_2).
                cap = font.metrics('H')[0][3]
                self.screen.blit(ts, (tx, rect.centery - font.get_ascent() + cap // 2))
            y += row_h + gap
        return y

    def _kit_subjects(self, body, draw=True) -> int:
        from fantasy_ui import KT
        sub_h = self.font_sm.get_height()
        if draw:
            sub = self.font_sm.render("Choose a subject to study", True, KT.TEXT_DIM)
            self.screen.blit(sub, (body.centerx - sub.get_width() // 2, body.y))
        end = self._kit_rows(body, [(f"subject_{sid}", name) for sid, name, _c in self._SUBJECTS],
                             body.y + sub_h + S(10), draw)
        return end - body.y

    def _kit_tiers(self, body, draw=True) -> int:
        import ui_theme
        from fantasy_ui import KT, get_font
        subj_name = next(n for s_, n, _ in self._SUBJECTS if s_ == self._subject)
        hf = get_font('heading', 26, bold=True)
        isz = S(32)
        if draw:
            hs = hf.render(subj_name, True, KT.TEXT_HEAD)
            total = isz + S(10) + hs.get_width()
            x = body.centerx - total // 2
            ui_theme.draw_icon(self.screen, f"subject_{self._subject}", (x, body.y, isz, isz))
            self.screen.blit(hs, (x + isz + S(10), body.y + (isz - hs.get_height()) // 2))
        y = body.y + isz + S(10)
        if draw:
            sub = self.font_sm.render("Choose difficulty tier", True, KT.TEXT_DIM)
            self.screen.blit(sub, (body.centerx - sub.get_width() // 2, y))
        labels = ["Tier 1 \u2014 Easy", "Tier 2 \u2014 Medium", "Tier 3 \u2014 Hard",
                  "Tier 4 \u2014 Expert", "Tier 5 \u2014 Master"]
        end = self._kit_rows(body, [(None, t) for t in labels],
                             y + self.font_sm.get_height() + S(14), draw)
        return end - body.y

    def _kit_quiz(self, body, *, result, draw=True) -> int:
        from fantasy_ui import (KT, draw_choice_button, choice_text_insets,
                                get_font, display_text)
        if not self._questions:
            if draw:
                ts = self.font_md.render("No questions available for this tier.", True,
                                         FP.WARNING_TEXT)
                self.screen.blit(ts, (body.centerx - ts.get_width() // 2, body.y + S(20)))
            return self.font_md.get_height() + S(40)
        q = self._last_q if result else self._questions[self._idx % len(self._questions)]
        y = body.y
        if result:
            ok = self._last_correct
            vf = get_font('heading', 28, bold=True)
            if draw:
                vs = vf.render("Correct!" if ok else "Incorrect", True,
                               KT.OK_TEXT if ok else KT.BAD_TEXT)
                self.screen.blit(vs, (body.centerx - vs.get_width() // 2, y))
            y += vf.get_height() + S(4)
        # The question reads the same before and after it is answered (the
        # result used to set it smaller and dimmer than the answers).
        qf = self.font_md
        lh = qf.get_height() + S(6)
        for line in self._wrap(display_text(q['question']), qf, body.w):
            if draw:
                self.screen.blit(qf.render(line, True, KT.TEXT_QUIZ), (body.x, y))
            y += lh
        y += S(12)
        # The four answers as the game's own quiz cards, 2 x 2; in the result
        # the right one is marked correct and a wrong pick incorrect.
        gap = S(14)
        cw = (body.w - gap) // 2
        cf = get_font('body', 20)
        tw = cw - sum(choice_text_insets())
        choices = list(q['choices'][:4])
        wrapped = [self._wrap(display_text(str(c)), cf, tw) for c in choices]
        clh = cf.get_height() + S(3)
        ch = max(S(54), max((len(w) for w in wrapped), default=1) * clh + S(20))
        # Exact comparison, as the answer check (case can be the point).
        answer = str(q['answer']).strip()
        chosen = str(getattr(self, '_last_chosen', '')).strip() if result else ''
        for i, (c, lines) in enumerate(zip(choices, wrapped)):
            if not draw:
                break
            rect = (body.x + (i % 2) * (cw + gap), y + (i // 2) * (ch + gap), cw, ch)
            is_ans = str(c).strip() == answer
            draw_choice_button(self.screen, rect, str(i + 1), lines,
                               get_font('body', 24, bold=True), cf,
                               correct=(result and is_ans) or None,
                               incorrect=(result and not is_ans
                                          and str(c).strip() == chosen) or None)
        rows = (len(choices) + 1) // 2
        y += rows * ch + (rows - 1) * gap
        if not result:
            return y - body.y
        y += S(14)
        context = display_text(q.get('context', ''), sources=True)
        # The explanation reads at the question's size, and sits under the
        # cards with space, not a second divider: with a one-line
        # explanation the two divider ornaments sat almost on top of each
        # other (VISUAL_REVIEW_2, study_result_wrong at 3440).
        cfnt = self.font_md
        clh = cfnt.get_height() + S(6)
        if context:
            y += S(10)
            lines = self._wrap(context, cfnt, body.w)
            if draw:
                room = max(0, (body.bottom - y) // clh)
                if len(lines) > room and room > 0:
                    lines = lines[:room]
                    lines[-1] = lines[-1].rstrip() + ' \u2026'
                lines = lines[:room]
            for line in lines:
                if draw:
                    self.screen.blit(cfnt.render(line, True, KT.TEXT_BODY), (body.x, y))
                y += clh
        elif not self._last_correct:
            if draw and y + clh <= body.bottom + S(8):
                ts = self.font_sm.render("(No additional context available for this question)",
                                         True, KT.TEXT_DIM)
                self.screen.blit(ts, (body.x, y + S(8)))
            y += clh + S(8)
        return y - body.y

    @staticmethod
    def _wrap(text, font, max_w):
        words = text.split()
        lines, cur = [], ''
        for word in words:
            test = (cur + ' ' + word).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or ['']
