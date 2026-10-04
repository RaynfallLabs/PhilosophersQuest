import json
import math
import os
import random
from enum import Enum, auto
from dataclasses import dataclass

from paths import data_path


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


_QUESTIONS_DIR = data_path('data', 'questions')
_CONTEXTS_DIR  = data_path('data', 'question_contexts')

# Subjects that have (or will have) a per-topic context-blurb file. Loader
# walks this list and silently skips any subject whose file is missing or
# malformed — the modal just stays hidden for those questions.
_CONTEXT_SUBJECTS = (
    'philosophy', 'history', 'economics', 'ai', 'theology',
    'geography', 'science', 'trivia', 'animal', 'cooking',
    # math: class-level method cards keyed by skill class, not ladder
    # blurbs (see tools/balance/math_topics.py).
    'math',
)

_CROSS_GAME_RECENT_CAP = 30          # questions remembered per (subject, tier)
_HISTORY_DIR_OVERRIDE = None         # tests point this at a temp dir
_CONTEXTS_DIR_OVERRIDE = None        # tests point this at a temp dir to override _CONTEXTS_DIR


def _quiz_history_path() -> str:
    """Path to the cross-game question-recency file.

    Lives in save_dir() so it is shared across save slots AND new games — the
    per-save deck pickle can't carry recency into a fresh game. Tests override
    the directory via `_HISTORY_DIR_OVERRIDE`.
    """
    from paths import save_dir
    base = _HISTORY_DIR_OVERRIDE if _HISTORY_DIR_OVERRIDE is not None else save_dir()
    return os.path.join(base, 'quiz_history.json')


class QuizEngine:
    RESULT_DISPLAY_TIME = 0.8       # seconds to show correct answer feedback
    WRONG_DISPLAY_TIME  = 3.0       # seconds to show wrong answer (player reads correct)

    def __init__(self):
        self._cache: dict[str, list] = {}

        # Monotonically increasing session id. Incremented at the top of
        # `start_quiz`; downstream effect/UI code reads it as a reliable
        # "this is a new quiz" signal — two consecutive zero-chain quizzes
        # still get distinct ids. Public, read-only; see CHAIN_EFFECTS_PLAN
        # Phase 0 (2026-10-03).
        self.session_id: int = 0
        # Per-quiz scroll offset for the pre-computed quiz layout
        # (`_quiz_layout` in game_render.py). Reset at `start_quiz` so each
        # new quiz starts at the top; bumped by `_quiz_input` on PgUp/PgDn.
        # Phase 2 beautification (2026-10-04).
        self._quiz_scroll_offset: int = 0

        # Persistent shuffle-decks: keyed by (subject, tier).
        # Each deck is walked in order across *all* quiz sessions for that subject/tier.
        # A question only repeats after every question in the pool has been shown at least once.
        self._decks:    dict[tuple, list] = {}   # (subject, tier) -> shuffled question list
        self._deck_idx: dict[tuple, int]  = {}   # (subject, tier) -> next position in deck
        self._last_q:   dict[tuple, dict | None] = {}  # (subject, tier) -> last question shown
        self._seen:     dict[tuple, set]  = {}   # (subject, tier) -> set of seen question texts
        # Cross-GAME anti-repeat memory: the last N question texts shown per
        # (subject, tier), persisted to disk so a NEW game deliberately avoids
        # what recent games already asked. The deck above only prevents repeats
        # WITHIN one game; without this a fresh game re-rolls from scratch and by
        # pure chance re-shows recent openers — which reads as "not random".
        self._recent:   dict[tuple, list] = {}   # (subject, tier) -> recent question texts

        # Per-RUN subject mastery (NOT cross-game). A (subject, tier) is mastered
        # once EVERY distinct question at that tier has been answered correctly
        # this run: wrong answers recycle (re-presented), right answers retire. A
        # mastered (subject, tier) AUTO-SUCCEEDS (escalator chains start at your
        # frontier; a fully-mastered subject auto-succeeds outright). Persisted in
        # the SAVE so it survives save/load WITHIN a run, but a brand-new game
        # starts fresh (__init__ leaves these empty; only restore_deck_state fills
        # them) -- i.e. per-run, reset each run.
        self._retired:   dict[tuple, set] = {}   # (subject, tier) -> question texts answered correctly
        self._mastered:  set = set()             # {(subject, tier), ...} fully cleared this run
        self._tier_size: dict[tuple, int] = {}   # cached count of distinct questions per (subject, tier)
        self.just_mastered: tuple | None = None  # one-shot UI flag: the (subject,tier) just mastered
        self.auto_passed: int = 0                # mastered tier-rounds auto-passed in the current quiz

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
        self.on_complete = None  # optional callable(result, mode, subject, correct, wrong) fired once at quiz end

        self.celebrating: bool = False
        self.celebration_text: str = ''
        self.celebration_timer: float = 0.0
        # When False (default), hitting max_chain ends the quiz silently
        # — no full-screen "MAX CHAIN!" takeover. Only the two sites that
        # explicitly opt in via `start_quiz(celebrate_on_max=True)`
        # (Divine Intercession, Unicorn boon) keep the celebration.
        # See CHAIN_EFFECTS_PLAN Phase 0 (2026-10-03).
        self._celebrate_on_max: bool = False

        # Seed `_seen` from the persisted cross-game history so the first deck
        # built for each (subject, tier) pushes recently-shown questions to the
        # back. Fully guarded — a missing/corrupt file is non-fatal.
        self._load_cross_game_history()

        # Per-topic context blurbs (opt-in orientation shown via a C-key modal
        # during a quiz; math timer pauses while the modal is open). Keyed by
        # (subject, topic). Missing bank file -> that subject contributes no
        # entries; a question without a `topic` field never has a blurb.
        self._contexts: dict[tuple[str, str], str] = {}
        # Timer pause state for the context modal. _timer_paused freezes the
        # countdown in `update()`; the saved value is informational only (the
        # countdown resumes from whatever `time_remaining` already holds).
        self._timer_paused: bool = False
        self._timer_paused_at: float = 0.0

        self._load_context_blurbs()

    # --- Public API ---

    def load_questions(self, subject: str) -> list:
        if subject not in self._cache:
            path = os.path.join(_QUESTIONS_DIR, f"{subject}.json")
            try:
                with open(path, encoding='utf-8') as f:
                    self._cache[subject] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                import sys
                print(f"WARNING: Question file unusable: {path} ({e})", file=sys.stderr)
                self._cache[subject] = []
        return self._cache[subject]

    def start_quiz(self, mode: str | QuizMode, subject: str, tier: int,
                   callback, threshold: int = 3, max_chain: int | None = None,
                   wisdom: int = 10, timer_modifier: float = 1.0,
                   extra_seconds: int = 0, base_seconds: int | None = None,
                   total_qs: int | None = None, timed: bool | None = None,
                   celebrate_on_max: bool = False):
        """
        Start a quiz session.
          threshold     -- for threshold modes: number of correct answers needed.
                          Total questions asked = ceil(threshold * 1.5).
          max_chain     -- for chain modes: auto-succeed after this chain length (None = unlimited).
          timer_modifier -- multiplier on the base timer (e.g. 0.55 when confused).
          base_seconds  -- pre-computed base timer from Player.get_quiz_timer(subject).
                          If provided, replaces the legacy (10 + wisdom) calculation.
          timed         -- True/False forces, None auto-detects from subject.
                          Combat math attack is the ONE timed action (chain pressure
                          + game-design speed). Every other quiz (identify, lockpick,
                          equip, prayer, cooking, magic, etc.) is untimed so the kid
                          can actually READ the substantive content the banks teach.
                          See `proposals/v2_audit/10_quiz_engine.md` §timer policy.
          celebrate_on_max -- opt-in to the full-screen "MAX CHAIN!" takeover
                          when `max_chain` is reached. Default False — the ~12
                          routine chain-mode call sites (combat, prayer, equip,
                          hero specials, mystery, …) no longer flash the
                          celebration. The only two sites that pass True are
                          Divine Intercession (`game_divine.py::_confirm_divine_intercession`)
                          and the Unicorn boon (`game_encounters.py::_start_unicorn_quiz`).
                          See CHAIN_EFFECTS_PLAN Phase 0 (2026-10-03).
          callback(QuizResult) is called when the quiz ends.
        """
        # Monotonic session id — bumped BEFORE any early return so even an
        # aborted quiz (empty bank) still advances the counter and the next
        # quiz is distinguishable from this one for downstream effect/UI code.
        self.session_id += 1
        # Phase 2 beautification (2026-10-04): per-quiz scroll offset for the
        # pre-computed quiz layout (`_quiz_layout` in game_render.py). Reset
        # here so each new quiz always starts at the top; PgUp/PgDn + `[`/`]`
        # bump it in `_quiz_input` when the layout flags `scrollable=True`.
        self._quiz_scroll_offset = 0
        self._celebrate_on_max = celebrate_on_max

        if isinstance(mode, str):
            mode = QuizMode(mode)
        if timed is None:
            # Default policy: only math (combat attack) is timed.
            timed = (subject == 'math')

        all_qs = self.load_questions(subject)
        deck_key = (subject, tier)

        # Build the persistent deck for this subject+tier if it doesn't exist yet.
        # Use ONLY the questions at exactly this tier so lower-tier questions don't
        # flood higher-tier decks and cause frequent repeats.
        # If exact tier is empty, fall back to nearest lower tier, then all.
        if deck_key not in self._decks:
            pool = [q for q in all_qs if q.get('tier', 1) == tier]
            if not pool:
                for fallback_t in range(tier - 1, 0, -1):
                    pool = [q for q in all_qs if q.get('tier', 1) == fallback_t]
                    if pool:
                        break
            if not pool:
                pool = all_qs[:]
            pool = self._shuffle_unseen_first(deck_key, pool)
            self._decks[deck_key]    = pool
            self._deck_idx[deck_key] = 0
            self._last_q[deck_key]   = None

        self.mode = mode
        self.subject = subject
        self.tier = tier
        self.required = threshold
        self.total_qs = total_qs if total_qs is not None else math.ceil(threshold * 1.5)
        self.max_chain = max_chain
        self.callback = callback
        self._timer_modifier = timer_modifier
        self.timed = timed
        if not timed:
            # Untimed quizzes (everything except combat math attack) carry
            # no clock. The tick loop and the renderer both check `self.timed`.
            self.timer_seconds = 0
            self.time_remaining = 0.0
        else:
            if base_seconds is not None:
                self.timer_seconds = round(base_seconds * timer_modifier) + extra_seconds
            else:
                self.timer_seconds = round((10 + wisdom) * timer_modifier) + extra_seconds
            self.time_remaining = float(self.timer_seconds)

        self.score = 0
        self.chain = 0
        self.correct_count = 0
        self.asked_count = 0
        self.just_mastered = None
        self.auto_passed = 0
        self.last_correct = None
        self.last_answer = ''
        self.result_timer = 0.0
        self.confused_order = None
        self.celebrating = False
        self.celebration_text = ''
        self.celebration_timer = 0.0
        # Clear any stale pause state from a prior quiz. A new quiz always
        # starts un-paused; the context modal pauses on open and un-pauses
        # on close within one quiz lifetime.
        self._timer_paused = False
        self._timer_paused_at = 0.0
        # Tablet of Destinies: allow one reroll of a wrong answer
        # Set externally by main.py before starting quiz
        # The flag is one-shot: it applies to THIS quiz only. Left sticky, a
        # combat start granted a free mulligan to every later identify /
        # lockpick / prayer quiz as well (audit B7, 2026-10-04).
        self.reroll_available = bool(getattr(self, '_reroll_flag', False))
        self._reroll_flag = False
        self.reroll_was_used = False

        # Resume from where the persistent deck left off.
        self._pool     = self._decks[deck_key]
        self._pool_idx = self._deck_idx[deck_key]
        # If the question bank for this subject is empty (missing/malformed
        # JSON, or a brand-new subject without data), fail gracefully instead
        # of crashing on _pool[0]. Marks the quiz as failed and invokes
        # callback so the caller can recover (e.g. return to STATE_PLAYER).
        if not self._pool:
            import sys
            print(f"WARNING: No questions available for subject={subject!r} tier={tier} -- aborting quiz",
                  file=sys.stderr)
            self.current_question = None
            self._end(success=False)
            return
        self._next_question()

    def answer(self, choice: str) -> bool:
        """Submit an answer. Returns True if correct. No-op if not in ASKING state."""
        if self.state != QuizState.ASKING:
            return False

        # Case-EXACT match (bug bash 2026-06-01). Grammar capitalization
        # questions intentionally have 4 choices that differ only by case
        # ("We went home. Then we ate dinner." vs "We went home. then we
        # ate dinner."). Case-folding made every choice register correct.
        correct = str(self.current_question['answer']).strip()
        is_correct = choice.strip() == correct

        self.last_answer = choice
        self.asked_count += 1
        self.last_correct = is_correct

        if is_correct:
            self.correct_count += 1
            self.chain += 1
            self._record_correct_for_mastery()   # retire this question; master the tier if cleared
        # Chain combat v2: a wrong answer NO LONGER zeros the chain. The strike
        # lands at whatever chain was achieved before the miss. Chain 0 (miss on
        # the FIRST question) still means "weapon missed" downstream; chain >= 1
        # means the strike lands at that chain.
        if self.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            self.score = self.chain
        elif is_correct:
            self.score = self.correct_count

        self.state = QuizState.RESULT
        self.result_timer = self.RESULT_DISPLAY_TIME if is_correct else self.WRONG_DISPLAY_TIME
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
            if self.timed and self.time_remaining > 0 and not self._timer_paused:
                self.time_remaining = max(0.0, self.time_remaining - dt)
                if self.time_remaining <= 0.0:
                    # Time's up. Chain combat v2: DOES NOT zero the chain. The
                    # strike lands at whatever chain was achieved during the
                    # window; only a wrong answer on the very first question
                    # (chain 0) counts as a miss.
                    self.last_answer = ''
                    self.asked_count += 1
                    self.last_correct = False
                    self.state = QuizState.RESULT
                    self.result_timer = self.WRONG_DISPLAY_TIME
                    if self.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
                        self.score = self.chain
                    if self.on_answer:
                        self.on_answer(False)

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
        # A mastered (subject, tier) auto-succeeds its round -- no question shown.
        if self.is_mastered(self.subject, self.tier):
            self._auto_pass_mastered_round()
            return
        last = self._last_q.get(deck_key)

        # Defensive: empty pool would crash on _pool[0] below. Should already
        # be caught at start_quiz, but escalator paths could also reach here
        # if a fallback tier ends up empty. Fail gracefully.
        if not self._pool:
            self.current_question = None
            self._end(success=False)
            return

        # Draw the next question NOT already answered correctly this run. Right
        # answers retire (stay out of the deck); wrong answers recycle (stay in).
        # If every question is retired, the tier is mastered -> auto-pass.
        retired = self._retired.get(deck_key, set())
        chosen = None
        for _ in range(len(self._pool) * 2 + 1):
            if self._pool_idx >= len(self._pool):
                # Deck exhausted -- reshuffle with unseen questions first.
                reshuffled = self._shuffle_unseen_first(deck_key, self._pool)
                self._pool[:] = reshuffled
                if last is not None and len(self._pool) > 1 and self._pool[0] is last:
                    swap = random.randint(1, len(self._pool) - 1)
                    self._pool[0], self._pool[swap] = self._pool[swap], self._pool[0]
                self._pool_idx = 0
            cand = self._pool[self._pool_idx]
            self._pool_idx += 1
            if cand.get('question') not in retired:
                chosen = cand
                break
        if chosen is None:
            # Every question retired this run -> the tier is mastered.
            if deck_key not in self._mastered:
                self._mastered.add(deck_key)
                self.just_mastered = deck_key
            self._auto_pass_mastered_round()
            return
        self.current_question = chosen

        # Track this question as seen.
        if deck_key not in self._seen:
            self._seen[deck_key] = set()
        self._seen[deck_key].add(self.current_question['question'])
        # ...and in the bounded cross-game recency list (persisted on quiz end).
        _rec = self._recent.setdefault(deck_key, [])
        _rec.append(self.current_question['question'])
        if len(_rec) > _CROSS_GAME_RECENT_CAP * 2:
            del _rec[:-_CROSS_GAME_RECENT_CAP]

        # Persist deck position immediately so _end() doesn't need to duplicate it.
        if deck_key in self._decks:
            self._deck_idx[deck_key] = self._pool_idx
            self._last_q[deck_key]   = self.current_question

        # Timer is set once in start_quiz() and runs continuously -- no reset per question
        self.state = QuizState.ASKING
        # Each question starts at the top; a long previous question must not
        # leave this one pre-scrolled.
        self._quiz_scroll_offset = 0

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

        # Timer expired — no more questions; end immediately.
        # Skip this check for untimed quizzes (time_remaining is permanently 0
        # by design); they end via chain-fail / threshold-met instead.
        if self.timed and self.time_remaining <= 0:
            if mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
                self._end(success=True)  # chain: score = chain length achieved
            else:
                self._end(success=self.correct_count >= self.required)
            return

        if mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            if not self.last_correct:
                # Tablet of Destinies: reroll a wrong answer (once)
                if self.reroll_available:
                    self.reroll_available = False
                    self.reroll_was_used = True
                    self._next_question()
                    return
                self._end(success=True)   # chain mode: always "succeeds"; score = chain length
            elif self.max_chain and self.chain >= self.max_chain:
                # Max chain reached. Two paths (CHAIN_EFFECTS_PLAN Phase 0,
                # 2026-10-03):
                #   celebrate_on_max=True  -> full-screen "MAX CHAIN!" hold,
                #       then _end() fires from update() when the timer runs out.
                #       Only Divine Intercession + Unicorn opt in.
                #   celebrate_on_max=False (default) -> end the quiz
                #       immediately; `celebrating` stays False, no full-screen
                #       takeover, no 1.5s hold. Phase 1's new per-answer
                #       effects handle in-combat feedback instead.
                if self._celebrate_on_max:
                    self.celebrating = True
                    self.celebration_text = 'MAX CHAIN!'
                    self.celebration_timer = 1.5
                    # _end() called from update() after timer expires
                else:
                    self._end(success=True)
            else:
                if mode == QuizMode.ESCALATOR_CHAIN:
                    self._escalate()
                self._next_question()

        else:  # threshold / escalator_threshold
            # Zero-tolerance: any wrong answer ends the quiz, per user
            # direction 2026-05-29 ("no mulligans in ANY quiz mode").
            # The Tablet of Destinies' one-time reroll still applies —
            # if the player has it, consume it and re-pose the question.
            if not self.last_correct:
                if self.reroll_available:
                    self.reroll_available = False
                    self.reroll_was_used = True
                    self._next_question()
                    return
                self._end(success=self.correct_count >= self.required)
                return
            # End immediately when threshold reached
            if self.correct_count >= self.required:
                self._end(success=True)
                return
            # Ran out of questions without reaching threshold
            if self.asked_count >= self.total_qs:
                self._end(success=False)
            else:
                if mode == QuizMode.ESCALATOR_THRESHOLD:
                    self._escalate()
                self._next_question()

    def _escalate(self):
        self.tier = min(self.tier + 1, 5)
        all_qs = self._cache.get(self.subject, [])
        deck_key = (self.subject, self.tier)

        if deck_key not in self._decks:
            new_pool = [q for q in all_qs if q.get('tier', 1) == self.tier]
            if not new_pool:
                for fallback_t in range(self.tier - 1, 0, -1):
                    new_pool = [q for q in all_qs if q.get('tier', 1) == fallback_t]
                    if new_pool:
                        break
            if not new_pool:
                new_pool = all_qs[:]
            new_pool = self._shuffle_unseen_first(deck_key, new_pool)
            self._decks[deck_key]    = new_pool
            self._deck_idx[deck_key] = 0
            self._last_q[deck_key]   = None

        self._pool     = self._decks[deck_key]
        self._pool_idx = self._deck_idx[deck_key]

    def _shuffle_unseen_first(self, deck_key: tuple, pool: list) -> list:
        """Shuffle pool with unseen questions placed before seen ones."""
        seen = self._seen.get(deck_key, set())
        if not seen:
            random.shuffle(pool)
            return pool
        unseen = [q for q in pool if q['question'] not in seen]
        rest   = [q for q in pool if q['question'] in seen]
        random.shuffle(unseen)
        random.shuffle(rest)
        return unseen + rest

    # --- Subject mastery (per-run) ---

    def _full_tier_size(self, subject: str, tier: int) -> int:
        """Count of DISTINCT questions at exactly this (subject, tier) -- the
        number that must each be answered correctly to master the tier."""
        key = (subject, tier)
        if key not in self._tier_size:
            qs = self.load_questions(subject)
            self._tier_size[key] = len({q['question'] for q in qs
                                        if q.get('tier', 1) == tier and q.get('question')})
        return self._tier_size[key]

    def is_mastered(self, subject: str, tier: int) -> bool:
        return (subject, tier) in self._mastered

    def mastered_tiers(self) -> set:
        """Public read for UI: set of (subject, tier) mastered this run."""
        return set(self._mastered)

    def _record_correct_for_mastery(self):
        """Retire the just-answered question; if every distinct question at this
        (subject, tier) is now retired, the tier is mastered for the run."""
        if not self.current_question:
            return
        key = (self.subject, self.tier)
        qtext = self.current_question.get('question')
        if not qtext:
            return
        retired = self._retired.setdefault(key, set())
        if qtext in retired:
            return
        retired.add(qtext)
        size = self._full_tier_size(self.subject, self.tier)
        if size > 0 and len(retired) >= size and key not in self._mastered:
            self._mastered.add(key)
            self.just_mastered = key

    def _auto_pass_mastered_round(self):
        """A mastered (subject, tier) auto-succeeds its round with no question
        shown. In escalator modes this climbs to the next tier (the player always
        fights at their frontier); a fully-mastered subject auto-succeeds outright."""
        self.last_correct = True
        self.correct_count += 1
        self.chain += 1
        self.asked_count += 1
        self.auto_passed += 1
        chain_mode = self.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN)
        self.score = self.chain if chain_mode else self.correct_count
        if chain_mode:
            if self.max_chain and self.chain >= self.max_chain:
                self._end(success=True)
                return
            if self.mode == QuizMode.ESCALATOR_CHAIN:
                prev = self.tier
                self._escalate()
                if self.tier == prev:            # already at the top tier -- can't climb
                    self._end(success=True)
                    return
                self._next_question()            # next tier (may itself be mastered)
                return
            # plain CHAIN, single tier, fully mastered -> strong auto-success
            self.chain = self.max_chain or 5
            self.score = self.chain
            self._end(success=True)
            return
        # threshold / escalator_threshold
        if self.correct_count >= self.required:
            self._end(success=True)
            return
        if self.mode == QuizMode.ESCALATOR_THRESHOLD:
            prev = self.tier
            self._escalate()
            if self.tier == prev:
                # Top tier, no higher to climb. If THIS tier is also mastered we
                # auto-passed the whole reachable ladder -> success even if the
                # threshold count wasn't reached. (Sphinx/Mjolnir are
                # escalator_threshold T3 thr=4: three auto-passes give count=3 <
                # 4, which used to AUTO-FAIL a fully-mastered player.)
                self._end(success=(self.correct_count >= self.required)
                          or self.is_mastered(self.subject, self.tier))
                return
            self._next_question()
            return
        # plain threshold, single tier, mastered -> auto-success
        self._end(success=True)

    def get_deck_state(self) -> dict:
        """Serializable quiz state for the save system.

        We persist ONLY the seen-set (question texts), NOT the shuffled decks.
        Pickling the decks' question OBJECTS made saves go STALE: a bank update
        (new or rewritten questions) never reached a loaded game, because restore
        re-installed the old pickled questions and start_quiz reused that deck
        instead of rebuilding from the current JSON. Seen-only keeps anti-repeat
        for unchanged questions while letting bank updates always take effect.
        """
        # `retired` + `mastered` are this RUN's subject-mastery progress. They go
        # in the per-save pickle (so save/load mid-run keeps your progress) but NOT
        # in the cross-game quiz_history.json -- mastery is per-run, earned fresh.
        return {'seen': self._seen, 'retired': self._retired,
                'mastered': self._mastered}

    def restore_deck_state(self, state: dict):
        """Restore the seen-set + this run's mastery progress; decks rebuild from
        the current question files on the next start_quiz, so bank updates always
        take effect on load (and old saves stop serving stale questions)."""
        if not state:
            return
        self._seen     = state.get('seen', {})
        self._retired  = state.get('retired', {}) or {}
        # tolerant of set-of-tuples (pickle) or list-of-lists (any JSON path)
        self._mastered = {tuple(k) for k in (state.get('mastered') or [])}
        # decks/deck_idx/last_q are intentionally NOT restored — re-installing
        # the pickled question objects is exactly what served stale questions.
        self._decks    = {}
        self._deck_idx = {}
        self._last_q   = {}

    def _load_cross_game_history(self):
        """Load the persisted cross-game recency file and seed `_seen` so the
        first deck built for each (subject, tier) avoids recently-shown
        questions. Non-fatal on any error (missing file / bad JSON)."""
        try:
            path = _quiz_history_path()
            if not os.path.exists(path):
                return
            with open(path, encoding='utf-8') as f:
                raw = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict):
            return
        for skey, texts in raw.items():
            if not isinstance(texts, list):
                continue
            subject, _, tier_s = skey.rpartition('|')
            if not subject or not tier_s.isdigit():
                continue
            recent = [t for t in texts if isinstance(t, str)][-_CROSS_GAME_RECENT_CAP:]
            if not recent:
                continue
            key = (subject, int(tier_s))
            self._recent[key] = recent
            self._seen.setdefault(key, set()).update(recent)

    # --- Context blurbs (opt-in orientation modal) ---

    def _contexts_dir(self) -> str:
        """Return the directory to read context-blurb JSON files from.

        Tests redirect this to a temp dir via ``_CONTEXTS_DIR_OVERRIDE``;
        otherwise it is the shipped ``data/question_contexts`` folder.
        """
        return _CONTEXTS_DIR_OVERRIDE if _CONTEXTS_DIR_OVERRIDE is not None else _CONTEXTS_DIR

    def _load_context_blurbs(self):
        """Read every subject's context-blurb file into ``self._contexts``.

        Non-fatal on any error — a missing file, bad JSON, or an unexpected
        shape leaves that subject's slice empty. The modal + the "[C] context"
        hint are therefore absent for any question whose (subject, topic)
        pair has no blurb.
        """
        self._contexts.clear()
        base = self._contexts_dir()
        if not os.path.isdir(base):
            return
        for subject in _CONTEXT_SUBJECTS:
            path = os.path.join(base, f'{subject}.json')
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
            except (OSError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            for topic, entry in data.items():
                if not isinstance(topic, str) or not topic:
                    continue
                if isinstance(entry, dict):
                    blurb = entry.get('context_blurb')
                elif isinstance(entry, str):
                    blurb = entry
                else:
                    blurb = None
                if isinstance(blurb, str) and blurb.strip():
                    self._contexts[(subject, topic)] = blurb.strip()

    def reload_context_blurbs(self):
        """Force a re-read of all context-blurb files (used by tests)."""
        self._load_context_blurbs()

    def get_context_blurb(self, subject: str, topic: str | None) -> str | None:
        """Return the blurb for a (subject, topic), or None if unknown.

        A None/empty topic always returns None: a question without a topic
        cannot be matched to a blurb.
        """
        if not subject or not topic:
            return None
        return self._contexts.get((subject, topic))

    def current_context_blurb(self) -> str | None:
        """Convenience: blurb for the currently-displayed question."""
        q = self.current_question
        if not q:
            return None
        return self.get_context_blurb(self.subject, q.get('topic'))

    # --- Timer pause / resume (context modal) ---

    def pause_timer(self):
        """Freeze the quiz countdown. Idempotent; safe for untimed quizzes.

        The implementation simply flips a flag; ``update()`` reads the flag
        and skips the ``time_remaining`` decrement. We also snapshot the
        current value for diagnostics / tests, but the countdown resumes
        from whatever ``time_remaining`` already holds.
        """
        if self._timer_paused:
            return
        self._timer_paused = True
        self._timer_paused_at = float(self.time_remaining)

    def resume_timer(self):
        """Unfreeze the quiz countdown. Idempotent."""
        if not self._timer_paused:
            return
        self._timer_paused = False

    def _persist_cross_game_history(self):
        """Atomically write the last N shown questions per (subject, tier) so a
        future NEW game can avoid them. Non-fatal on any error — this is a UX
        nicety, never gameplay-critical."""
        if not self._recent:
            return
        try:
            out = {}
            for (subject, tier), texts in self._recent.items():
                # de-dupe keeping the most-recent occurrence, then cap
                seen_local = set()
                trimmed = []
                for t in reversed(texts):
                    if t in seen_local:
                        continue
                    seen_local.add(t)
                    trimmed.append(t)
                    if len(trimmed) >= _CROSS_GAME_RECENT_CAP:
                        break
                out[f'{subject}|{tier}'] = list(reversed(trimmed))
            path = _quiz_history_path()
            tmp = path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(out, f)
            os.replace(tmp, path)
        except OSError:
            return

    def cancel_and_strike(self) -> bool:
        """Chain combat v2: SPACE key handler. Locks in current chain and lands
        the strike immediately. Only valid in chain modes and only while a
        question is being asked (not during the result flash). Returns True if
        the cancel took effect."""
        if self.mode not in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            return False
        if self.state != QuizState.ASKING:
            return False
        # Freeze the achieved chain into score and end the quiz. Downstream
        # combat callback treats score >= 1 as a landed strike at that chain.
        self.score = self.chain
        self._end(success=True)
        return True

    def _end(self, success: bool):
        # A finished quiz must not finish twice: a second _end used to re-fire
        # the previous quiz's callback (e.g. a stray ESC re-running a combat
        # closure and killing a dead monster again). The callback is cleared
        # once taken, and start_quiz installs a fresh one.
        if self.state == QuizState.COMPLETE and self.callback is None:
            return
        self.state = QuizState.COMPLETE
        self._persist_cross_game_history()
        result = QuizResult(
            success=success,
            score=self.score,
            correct=self.correct_count,
            asked=self.asked_count,
        )
        if self.on_complete:
            mode_name = self.mode.value if isinstance(self.mode, QuizMode) else str(self.mode)
            self.on_complete(result, mode_name, self.subject,
                             self.correct_count, self.asked_count - self.correct_count)
        callback, self.callback = self.callback, None
        if callback:
            callback(result)
