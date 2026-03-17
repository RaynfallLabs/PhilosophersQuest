import json
import math
import os
import random
from enum import Enum, auto
from dataclasses import dataclass


class QuizMode(Enum):
    THRESHOLD = "threshold"
    CHAIN = "chain"
    ESCALATOR_THRESHOLD = "escalator_threshold"
    ESCALATOR_CHAIN = "escalator_chain"


class QuizState(Enum):
    IDLE = auto()
    ASKING = auto()
    RESULT = auto()
    COMPLETE = auto()


@dataclass
class QuizResult:
    success: bool
    score: int        # chain length for chain modes; correct count for threshold modes
    correct: int
    asked: int


from paths import data_path
_QUESTIONS_DIR = data_path('data', 'questions')


class QuizEngine:
    RESULT_DISPLAY_TIME = 0.8   # seconds to show correct/wrong feedback

    def __init__(self):
        self._cache: dict[str, list] = {}

        # Persistent shuffle-decks: keyed by (subject, tier).
        # Each deck is walked in order across *all* quiz sessions for that subject/tier.
        # A question only repeats after every question in the pool has been shown at least once.
        self._decks:    dict[tuple, list] = {}   # (subject, tier) -> shuffled question list
        self._deck_idx: dict[tuple, int]  = {}   # (subject, tier) -> next position in deck
        self._last_q:   dict[tuple, dict | None] = {}  # (subject, tier) -> last question shown

        self.state = QuizState.IDLE
        self.mode: QuizMode | None = None
        self.subject: str = ''
        self.tier: int = 1
        self.required: int = 3      # correct answers needed (threshold) or N/A (chain)
        self.total_qs: int = 5      # total questions to ask (threshold modes)
        self.max_chain: int | None = None
        self.callback = None
        self.timer_seconds: int = 10

        self.time_remaining: float = 0.0
        self.result_timer: float = 0.0
        self.last_correct: bool | None = None

        self.current_question: dict | None = None
        self._pool: list = []
        self._pool_idx: int = 0

        self.score: int = 0
        self.chain: int = 0
        self.correct_count: int = 0
        self.asked_count: int = 0
        self.last_answer: str = ''    # last submitted answer string
        self.confused_order: list | None = None   # shuffled choice indices when confused
        self._timer_modifier: float = 1.0
        self.on_answer = None   # optional callable(is_correct: bool) fired after each answer

        self.celebrating: bool = False
        self.celebration_text: str = ''
        self.celebration_timer: float = 0.0

    # --- Public API ---

    def load_questions(self, subject: str) -> list:
        if subject not in self._cache:
            path = os.path.join(_QUESTIONS_DIR, f"{subject}.json")
            try:
                with open(path, encoding='utf-8') as f:
                    self._cache[subject] = json.load(f)
            except FileNotFoundError:
                import sys
                print(f"WARNING: Question file not found: {path}", file=sys.stderr)
                self._cache[subject] = []
        return self._cache[subject]

    def start_quiz(self, mode: str | QuizMode, subject: str, tier: int,
                   callback, threshold: int = 3, max_chain: int | None = None,
                   wisdom: int = 10, timer_modifier: float = 1.0,
                   extra_seconds: int = 0):
        """
        Start a quiz session.
          threshold     -- for threshold modes: number of correct answers needed.
                          Total questions asked = ceil(threshold * 1.5).
          max_chain     -- for chain modes: auto-succeed after this chain length (None = unlimited).
          timer_modifier -- multiplier on the base timer (e.g. 0.55 when confused).
          callback(QuizResult) is called when the quiz ends.
        """
        if isinstance(mode, str):
            mode = QuizMode(mode)

        all_qs = self.load_questions(subject)
        deck_key = (subject, tier)

        # Build the persistent deck for this subject+tier if it doesn't exist yet.
        if deck_key not in self._decks:
            pool = [q for q in all_qs if q.get('tier', 1) <= tier] or all_qs[:]
            random.shuffle(pool)
            self._decks[deck_key]    = pool
            self._deck_idx[deck_key] = 0
            self._last_q[deck_key]   = None

        self.mode = mode
        self.subject = subject
        self.tier = tier
        self.required = threshold
        self.total_qs = math.ceil(threshold * 1.5)
        self.max_chain = max_chain
        self.callback = callback
        self._timer_modifier = timer_modifier
        self.timer_seconds = round((10 + wisdom) * timer_modifier) + extra_seconds
        self.time_remaining = float(self.timer_seconds)

        self.score = 0
        self.chain = 0
        self.correct_count = 0
        self.asked_count = 0
        self.last_correct = None
        self.last_answer = ''
        self.result_timer = 0.0
        self.confused_order = None
        self.celebrating = False
        self.celebration_text = ''
        self.celebration_timer = 0.0

        # Resume from where the persistent deck left off.
        self._pool     = self._decks[deck_key]
        self._pool_idx = self._deck_idx[deck_key]
        self._next_question()

    def answer(self, choice: str) -> bool:
        """Submit an answer. Returns True if correct. No-op if not in ASKING state."""
        if self.state != QuizState.ASKING:
            return False

        correct = str(self.current_question['answer']).strip().lower()
        is_correct = choice.strip().lower() == correct

        self.last_answer = choice
        self.asked_count += 1
        self.last_correct = is_correct

        if is_correct:
            self.correct_count += 1
            self.chain += 1
            self.score = self.chain if self.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN) \
                else self.correct_count
        else:
            self.chain = 0

        self.state = QuizState.RESULT
        self.result_timer = self.RESULT_DISPLAY_TIME
        if self.on_answer:
            self.on_answer(is_correct)
        return is_correct

    def update(self, dt: float):
        """Call each frame with delta time in seconds."""
        if self.celebrating:
            self.celebration_timer -= dt
            if self.celebration_timer <= 0:
                self.celebrating = False
                self.celebration_text = ''
                self._end(success=True)
            return

        if self.state == QuizState.ASKING:
            if self.time_remaining > 0:
                self.time_remaining = max(0.0, self.time_remaining - dt)
                if self.time_remaining == 0.0:
                    # Time's up -- count as a wrong answer and advance
                    self.last_answer = ''
                    self.asked_count += 1
                    self.last_correct = False
                    self.chain = 0
                    self.state = QuizState.RESULT
                    self.result_timer = self.RESULT_DISPLAY_TIME

        elif self.state == QuizState.RESULT:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self._advance()

    @property
    def active(self) -> bool:
        return self.state not in (QuizState.IDLE, QuizState.COMPLETE)

    # --- Internal ---

    def _next_question(self):
        deck_key = (self.subject, self.tier)
        last = self._last_q.get(deck_key)

        if self._pool_idx >= len(self._pool):
            # Deck exhausted -- reshuffle, but don't let the first card equal the last shown.
            random.shuffle(self._pool)
            if last is not None and len(self._pool) > 1 and self._pool[0] is last:
                swap = random.randint(1, len(self._pool) - 1)
                self._pool[0], self._pool[swap] = self._pool[swap], self._pool[0]
            self._pool_idx = 0

        self.current_question = self._pool[self._pool_idx]
        self._pool_idx += 1

        # Persist deck position immediately so _end() doesn't need to duplicate it.
        if deck_key in self._decks:
            self._deck_idx[deck_key] = self._pool_idx
            self._last_q[deck_key]   = self.current_question

        # Timer is set once in start_quiz() and runs continuously -- no reset per question
        self.state = QuizState.ASKING

        # Always shuffle choice order so correct answer position is randomized
        choices = self.current_question.get('choices', [])
        if choices:
            order = list(range(len(choices)))
            random.shuffle(order)
            self.confused_order = order
        else:
            self.confused_order = None

    def _advance(self):
        mode = self.mode

        if mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            if not self.last_correct:
                self._end(success=True)   # chain mode: always "succeeds"; score = chain length
            elif self.max_chain and self.chain >= self.max_chain:
                # Celebrate before ending
                self.celebrating = True
                self.celebration_text = 'MAX CHAIN!'
                self.celebration_timer = 1.5
                # _end() called from update() after timer expires
            else:
                if mode == QuizMode.ESCALATOR_CHAIN:
                    self._escalate()
                self._next_question()

        else:  # threshold / escalator_threshold
            # End immediately on wrong answer
            if not self.last_correct:
                self._end(success=False)
                return
            # End immediately when threshold reached
            if self.correct_count >= self.required:
                self._end(success=True)
                return
            # Still have questions left
            if self.asked_count >= self.total_qs:
                self._end(success=False)   # ran out before hitting threshold
            else:
                if mode == QuizMode.ESCALATOR_THRESHOLD:
                    self._escalate()
                self._next_question()

    def _escalate(self):
        self.tier += 1
        all_qs = self._cache.get(self.subject, [])
        deck_key = (self.subject, self.tier)

        if deck_key not in self._decks:
            new_pool = [q for q in all_qs if q.get('tier', 1) <= self.tier] or all_qs[:]
            random.shuffle(new_pool)
            self._decks[deck_key]    = new_pool
            self._deck_idx[deck_key] = 0
            self._last_q[deck_key]   = None

        self._pool     = self._decks[deck_key]
        self._pool_idx = self._deck_idx[deck_key]

    def _end(self, success: bool):
        self.state = QuizState.COMPLETE
        result = QuizResult(
            success=success,
            score=self.score,
            correct=self.correct_count,
            asked=self.asked_count,
        )
        if self.callback:
            self.callback(result)
