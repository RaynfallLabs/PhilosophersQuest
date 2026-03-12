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


_QUESTIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions')


class QuizEngine:
    RESULT_DISPLAY_TIME = 0.8   # seconds to show correct/wrong feedback

    def __init__(self):
        self._cache: dict[str, list] = {}

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
                   wisdom: int = 10, timer_modifier: float = 1.0):
        """
        Start a quiz session.
          threshold     — for threshold modes: number of correct answers needed.
                          Total questions asked = ceil(threshold * 1.5).
          max_chain     — for chain modes: auto-succeed after this chain length (None = unlimited).
          timer_modifier — multiplier on the base timer (e.g. 0.55 when confused).
          callback(QuizResult) is called when the quiz ends.
        """
        if isinstance(mode, str):
            mode = QuizMode(mode)

        all_qs = self.load_questions(subject)
        pool = [q for q in all_qs if q.get('tier', 1) <= tier] or all_qs[:]
        random.shuffle(pool)

        self.mode = mode
        self.subject = subject
        self.tier = tier
        self.required = threshold
        self.total_qs = math.ceil(threshold * 1.5)
        self.max_chain = max_chain
        self.callback = callback
        self._timer_modifier = timer_modifier
        self.timer_seconds = round((10 + max(0, wisdom - 10)) * timer_modifier)
        self.time_remaining = float(self.timer_seconds)

        self.score = 0
        self.chain = 0
        self.correct_count = 0
        self.asked_count = 0
        self.last_correct = None
        self.last_answer = ''
        self.result_timer = 0.0
        self.confused_order = None

        self._pool = pool
        self._pool_idx = 0
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
        return is_correct

    def update(self, dt: float):
        """Call each frame with delta time in seconds."""
        if self.state == QuizState.ASKING:
            if self.time_remaining > 0:
                self.time_remaining = max(0.0, self.time_remaining - dt)
                if self.time_remaining == 0.0:
                    # Time's up — count as a wrong answer and advance
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
        if self._pool_idx >= len(self._pool):
            random.shuffle(self._pool)
            self._pool_idx = 0
        self.current_question = self._pool[self._pool_idx]
        self._pool_idx += 1
        # Timer is set once in start_quiz() and runs continuously — no reset per question
        self.state = QuizState.ASKING

        # Generate shuffled choice order for confused players
        choices = self.current_question.get('choices', [])
        if choices and self._timer_modifier < 1.0:
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
                self._end(success=True)
            else:
                if mode == QuizMode.ESCALATOR_CHAIN:
                    self._escalate()
                self._next_question()

        else:  # threshold / escalator_threshold
            if self.asked_count >= self.total_qs:
                self._end(success=self.correct_count >= self.required)
            else:
                if mode == QuizMode.ESCALATOR_THRESHOLD:
                    self._escalate()
                self._next_question()

    def _escalate(self):
        self.tier += 1
        all_qs = self._cache.get(self.subject, [])
        new_pool = [q for q in all_qs if q.get('tier', 1) <= self.tier]
        if new_pool:
            self._pool = new_pool
            random.shuffle(self._pool)
            self._pool_idx = 0

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
