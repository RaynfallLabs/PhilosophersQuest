"""Standalone Study Mode quiz.

Launched from the welcome screen (F3). Lets the player pick a subject and
difficulty tier, then runs an untimed quiz that shows the correct answer plus
any educational context after each question. Independent of the main game loop.
"""

import sys

import pygame

from fantasy_ui import FP, get_font, centered_text, draw_divider


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

    def __init__(self, screen):
        self.screen = screen
        self.font_lg = get_font('heading', 32)
        self.font_md = get_font('body', 22)
        self.font_sm = get_font('body', 18)
        self.font_tiny = get_font('body', 14)
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
        import json
        import random
        from paths import data_path

        while True:
            clock.tick(60)
            W, H = self.screen.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.WINDOWRESIZED:
                    continue
                if event.type != pygame.KEYDOWN:
                    continue

                key = event.key

                if self._phase == 'subject':
                    if key == pygame.K_ESCAPE:
                        return  # back to welcome
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
                            correct_ans = str(q['answer']).strip().lower()
                            is_correct = chosen.strip().lower() == correct_ans
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
                        self._phase = 'quiz'

            # Draw — paint the grimoire frame first so all phase drawers
            # land their content inside the panel body.
            self.screen.fill(FP.MIDNIGHT)
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

    def _draw_frame(self, W, H):
        """Paint the full-viewport grimoire panel that frames every phase."""
        from fantasy_ui import draw_dark_panel, draw_header_bar, draw_divider
        margin = 24
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
        draw_header_bar(self.screen, (margin, margin, W - 2 * margin, 44),
                        text=title, font=self.font_lg,
                        text_color=FP.GOLD_BRIGHT, accent=FP.GOLD)
        draw_divider(self.screen, margin + 20, margin + 50,
                     W - 2 * margin - 40)

    def _draw_subject_picker(self, W, H):
        # Panel header is painted by _draw_frame; just the sub-line + list here.
        centered_text(self.screen, self.font_sm, "Choose a subject to study", FP.BODY_TEXT, 100)

        y = 140
        for i, (sid, name, color) in enumerate(self._SUBJECTS):
            sel = i == self._selected
            bg = FP.MIDNIGHT_MID if sel else FP.MIDNIGHT
            rect = pygame.Rect(W // 2 - 200, y, 400, 32)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if sel:
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=4)
            # Don't use raw subject color as text — some (science, grammar)
            # are too dark on the panel bg. Keep text as BODY/GOLD_BRIGHT
            # and let the BORDER carry the subject signal.
            text_col = FP.GOLD_BRIGHT if sel else FP.BODY_TEXT
            surf = self.font_md.render(name, True, text_col)
            self.screen.blit(surf, (rect.x + 20, rect.y + 4))
            y += 38

        hint = self.font_tiny.render("Up/Down to select, ENTER to choose, ESC to go back", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

    def _draw_tier_picker(self, W, H):
        subj_name = next(n for s, n, _ in self._SUBJECTS if s == self._subject)
        # Panel header shows phase title; we add subject sub-line.
        centered_text(self.screen, self.font_md, subj_name.upper(), FP.GOLD_PALE, 90)
        centered_text(self.screen, self.font_sm, "Choose difficulty tier", FP.BODY_TEXT, 124)

        tier_labels = ["Tier 1 — Easy", "Tier 2 — Medium", "Tier 3 — Hard",
                       "Tier 4 — Expert", "Tier 5 — Master"]
        y = 150
        for i, label in enumerate(tier_labels):
            sel = i == self._selected
            bg = FP.MIDNIGHT_MID if sel else FP.MIDNIGHT
            rect = pygame.Rect(W // 2 - 180, y, 360, 36)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if sel:
                pygame.draw.rect(self.screen, FP.GOLD, rect, 2, border_radius=4)
            surf = self.font_md.render(label, True, FP.GOLD_BRIGHT if sel else FP.BODY_TEXT)
            self.screen.blit(surf, (rect.x + 20, rect.y + 6))
            y += 44

        hint = self.font_tiny.render("Up/Down to select, ENTER to choose, ESC to go back", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

    def _draw_quiz(self, W, H):
        if not self._questions:
            centered_text(self.screen, self.font_md, "No questions available for this tier.", FP.WARNING_TEXT, H // 2)
            return

        q = self._questions[self._idx % len(self._questions)]
        score = f"{self._correct_count}/{self._asked_count}" if self._asked_count else "0/0"
        centered_text(self.screen, self.font_sm, f"Score: {score}", FP.GOLD_PALE, 20)

        # Question
        q_text = q['question']
        lines = self._wrap(q_text, self.font_md, W - 120)
        y = 80
        for line in lines:
            surf = self.font_md.render(line, True, FP.PARCHMENT_LIGHT)
            self.screen.blit(surf, (60, y))
            y += 30

        # Choices
        y = max(y + 30, 200)
        for i, choice in enumerate(q['choices'][:4]):
            key_label = f"[{i+1}]"
            key_surf = self.font_md.render(key_label, True, FP.GOLD_BRIGHT)
            choice_surf = self.font_md.render(f"  {choice}", True, FP.BODY_TEXT)
            self.screen.blit(key_surf, (100, y))
            self.screen.blit(choice_surf, (140, y))
            y += 36

        hint = self.font_tiny.render("Press 1-4 to answer, ESC to quit", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

    def _draw_result(self, W, H):
        q = self._last_q
        is_correct = self._last_correct

        if is_correct:
            centered_text(self.screen, self.font_lg, "CORRECT!", FP.SUCCESS_TEXT, 40, shadow=True)
        else:
            centered_text(self.screen, self.font_lg, "INCORRECT", FP.DANGER_TEXT, 40, shadow=True)
            # Show correct answer
            correct = q['answer']
            centered_text(self.screen, self.font_md, f"The correct answer is: {correct}", FP.GOLD_BRIGHT, 90)

        # Show question
        q_lines = self._wrap(q['question'], self.font_sm, W - 120)
        y = 140
        for line in q_lines:
            surf = self.font_sm.render(line, True, FP.FADED_TEXT)
            self.screen.blit(surf, (60, y))
            y += 24

        # Show context (educational explanation) if available
        context = q.get('context', '')
        if context:
            y += 20
            draw_divider(self.screen, 60, y, W - 120)
            y += 16
            ctx_lines = self._wrap(context, self.font_sm, W - 120)
            for line in ctx_lines:
                surf = self.font_sm.render(line, True, FP.BODY_TEXT)
                self.screen.blit(surf, (60, y))
                y += 24
        elif not is_correct:
            y += 20
            surf = self.font_tiny.render("(No additional context available for this question)", True, FP.FADED_TEXT)
            self.screen.blit(surf, (60, y))

        hint = self.font_tiny.render("Press ENTER or SPACE for next question, ESC to quit", True, FP.HINT_TEXT)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

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
