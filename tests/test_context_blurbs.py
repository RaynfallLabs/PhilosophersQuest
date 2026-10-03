"""Tests for the opt-in context-blurb system (Phase 2 of the orientation plan).

Covers:
- Loader behaves gracefully for a missing directory + missing per-subject file.
- Loader reads a valid per-subject JSON and keys blurbs by (subject, topic).
- get_context_blurb returns None for unknown (subject, topic).
- STATE_QUIZ_CONTEXT constant exists and is wired through the state module.
- quiz_engine.pause_timer / resume_timer freeze and unfreeze the math countdown.

The tests are hermetic: no real quiz-bank or context file is read; the engine
is poked at the public API surface (pause_timer, resume_timer, get_context_blurb,
_contexts, mark_context_seen) plus one escalator-style _check_context_auto_open
smoke check via a synthetic question dict.
"""
import json
import os
import sys

import pytest

# src/ is already on sys.path via tests/conftest.py

import quiz_engine  # noqa: E402
from quiz_engine import QuizEngine, QuizMode, QuizState  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(tier: int, q_text: str, answer: str, choices=None, topic: str | None = None) -> dict:
    """Minimal question dict with an optional topic field."""
    q = {
        'tier': tier,
        'question': q_text,
        'answer': answer,
        'choices': choices or [answer, 'wrong1', 'wrong2', 'wrong3'],
    }
    if topic is not None:
        q['topic'] = topic
    return q


def _write_subject_file(dir_path: str, subject: str, mapping: dict):
    """Write a tiny context-blurb file for a subject under the test dir."""
    with open(os.path.join(dir_path, f'{subject}.json'), 'w', encoding='utf-8') as f:
        json.dump(mapping, f)


# ---------------------------------------------------------------------------
# 1. Loader — missing directory / missing file
# ---------------------------------------------------------------------------

def test_context_loader_handles_missing_file(tmp_path, monkeypatch):
    """A directory that exists but holds no files for the subject leaves
    the (subject, topic) lookup empty — no exception, no entries."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    eng = QuizEngine()
    # No files written to tmp_path -> loader walks the subject list and
    # finds nothing. _contexts stays empty.
    assert eng._contexts == {}
    assert eng.get_context_blurb('philosophy', 'anselm') is None


def test_context_loader_handles_missing_directory(tmp_path, monkeypatch):
    """A completely missing contexts dir is non-fatal: loader just returns."""
    missing_dir = str(tmp_path / 'does_not_exist')
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', missing_dir)
    eng = QuizEngine()
    assert eng._contexts == {}


def test_context_loader_handles_malformed_json(tmp_path, monkeypatch):
    """A bogus/malformed subject file is skipped silently; other subjects
    still load. The loader is defensive about every parse."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    # philosophy.json = broken JSON
    (tmp_path / 'philosophy.json').write_text("{not valid", encoding='utf-8')
    # history.json = valid, one entry
    _write_subject_file(str(tmp_path), 'history',
                        {'ww1': {'context_blurb': 'The Great War, 1914-1918.'}})
    eng = QuizEngine()
    assert eng.get_context_blurb('philosophy', 'anselm') is None
    assert eng.get_context_blurb('history', 'ww1') == 'The Great War, 1914-1918.'


# ---------------------------------------------------------------------------
# 2. Loader — valid file
# ---------------------------------------------------------------------------

def test_context_loader_reads_valid_file(tmp_path, monkeypatch):
    """A well-formed per-subject file is keyed by (subject, topic)."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'philosophy', {
        'anselm': {'context_blurb': 'Anselm of Canterbury was an 11th-century monk.'},
        'godel':  {'context_blurb': 'Kurt Godel proved incompleteness in 1931.'},
    })
    eng = QuizEngine()
    assert eng.get_context_blurb('philosophy', 'anselm') \
        == 'Anselm of Canterbury was an 11th-century monk.'
    assert eng.get_context_blurb('philosophy', 'godel') \
        == 'Kurt Godel proved incompleteness in 1931.'


def test_context_loader_accepts_bare_string_blurb(tmp_path, monkeypatch):
    """Shape tolerance: {topic: 'string'} is also accepted (no inner dict)."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'history', {'ww2': 'World war 2 blurb.'})
    eng = QuizEngine()
    assert eng.get_context_blurb('history', 'ww2') == 'World war 2 blurb.'


def test_get_context_blurb_returns_none_for_unknown_topic(tmp_path, monkeypatch):
    """A topic that isn't present → None, not KeyError."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'philosophy',
                        {'anselm': {'context_blurb': 'blurb'}})
    eng = QuizEngine()
    assert eng.get_context_blurb('philosophy', 'nietzsche') is None
    assert eng.get_context_blurb('history', 'anselm') is None
    # None/empty topic — always None
    assert eng.get_context_blurb('philosophy', None) is None
    assert eng.get_context_blurb('philosophy', '') is None
    assert eng.get_context_blurb('', 'anselm') is None


# ---------------------------------------------------------------------------
# 3. State constant + input wiring
# ---------------------------------------------------------------------------

def test_quiz_context_state_wiring():
    """STATE_QUIZ_CONTEXT must exist on game_states and be re-exported by
    the modules that dispatch on state."""
    from game_states import STATE_QUIZ_CONTEXT  # noqa: F401
    # The input + render modules import it at module top; a missing symbol
    # would raise ImportError before the test ran. Spot-check string value.
    assert STATE_QUIZ_CONTEXT == 'quiz_context'


def test_quiz_context_dispatch_hooks_exist():
    """game_input exposes _quiz_context_input; game_render exposes
    _draw_quiz_context_modal. Both are hit by state-dispatch tables."""
    from game_input import InputMixin
    from game_render import RenderMixin
    assert hasattr(InputMixin, '_quiz_context_input'), \
        "InputMixin must define _quiz_context_input for STATE_QUIZ_CONTEXT"
    assert hasattr(RenderMixin, '_draw_quiz_context_modal'), \
        "RenderMixin must define _draw_quiz_context_modal for STATE_QUIZ_CONTEXT"


# ---------------------------------------------------------------------------
# 4. Timer pause / resume
# ---------------------------------------------------------------------------

def _make_math_engine() -> QuizEngine:
    """QuizEngine with a one-tier math bank, suitable for timer tests."""
    eng = QuizEngine()
    bank = [_q(1, f'math-Q{i}', 'right') for i in range(8)]
    eng._cache['math'] = bank
    return eng


def test_math_timer_pauses_on_context_open():
    """pause_timer() must freeze the countdown; subsequent update(dt) calls
    must NOT decrement time_remaining until resume_timer() is called."""
    eng = _make_math_engine()
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None,
                   base_seconds=20)
    # Timer runs
    assert eng.timed is True
    assert eng.time_remaining == pytest.approx(20.0)
    eng.update(1.0)
    assert eng.time_remaining == pytest.approx(19.0)
    # Pause
    eng.pause_timer()
    frozen = eng.time_remaining
    eng.update(2.0)
    eng.update(3.0)
    assert eng.time_remaining == pytest.approx(frozen), \
        "timer must NOT advance while paused"
    # Resume
    eng.resume_timer()
    eng.update(1.5)
    assert eng.time_remaining == pytest.approx(frozen - 1.5), \
        "timer must resume from where it was paused"


def test_pause_timer_is_idempotent_and_safe_untimed():
    """pause/resume on an untimed subject must be a no-op (no exception).
    Repeat calls must not corrupt state."""
    eng = QuizEngine()
    bank = [_q(1, f'phil-Q{i}', 'right') for i in range(8)]
    eng._cache['philosophy'] = bank
    eng.start_quiz('threshold', 'philosophy', tier=1,
                   callback=lambda r: None, threshold=1)
    assert eng.timed is False
    # Untimed path: time_remaining is 0.0 by design and stays that way.
    eng.pause_timer()
    eng.pause_timer()   # idempotent
    eng.update(5.0)
    assert eng.time_remaining == 0.0
    eng.resume_timer()
    eng.resume_timer()  # idempotent
    assert eng.time_remaining == 0.0


# ---------------------------------------------------------------------------
# 5. Auto-open hook (one-shot per session per topic)
# ---------------------------------------------------------------------------

def test_auto_open_fires_once_per_topic(tmp_path, monkeypatch):
    """A fresh ladder with a blurb flips pending_context_auto_open; after
    mark_context_seen the same (subject, topic) must NOT re-fire."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'philosophy',
                        {'anselm': {'context_blurb': 'Anselm blurb.'}})
    eng = QuizEngine()
    # Simulate the state _next_question leaves behind.
    eng.subject = 'philosophy'
    eng.current_question = _q(1, 'q-anselm-T1', 'right', topic='anselm')
    eng._check_context_auto_open()
    assert eng.pending_context_auto_open == ('philosophy', 'anselm')
    # Record seen -> re-check must NOT flag it.
    eng.pending_context_auto_open = None
    eng.mark_context_seen('philosophy', 'anselm')
    eng.current_question = _q(2, 'q-anselm-T2', 'right', topic='anselm')
    eng._check_context_auto_open()
    assert eng.pending_context_auto_open is None, \
        "auto-open must not re-fire on a seen (subject, topic)"


def test_auto_open_skipped_when_no_blurb(tmp_path, monkeypatch):
    """No blurb → no auto-open flag. Players can still press C, but the
    modal politely says there's nothing to show."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    # empty contexts dir
    eng = QuizEngine()
    eng.subject = 'philosophy'
    eng.current_question = _q(1, 'q-anselm-T1', 'right', topic='anselm')
    eng._check_context_auto_open()
    assert eng.pending_context_auto_open is None


def test_auto_open_skipped_when_no_topic_field(tmp_path, monkeypatch):
    """A question missing the topic field never auto-opens (nothing to
    join on). Loader-level graceful handling for the current bank schema
    which pre-dates the topic field."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'philosophy',
                        {'anselm': {'context_blurb': 'Anselm blurb.'}})
    eng = QuizEngine()
    eng.subject = 'philosophy'
    eng.current_question = _q(1, 'q-anselm-T1', 'right')  # no topic
    eng._check_context_auto_open()
    assert eng.pending_context_auto_open is None
    assert eng.current_context_blurb() is None


# ---------------------------------------------------------------------------
# 6. End-to-end wiring smoke via start_quiz
# ---------------------------------------------------------------------------

def test_start_quiz_sets_auto_open_when_blurb_present(tmp_path, monkeypatch):
    """When start_quiz runs and the first question's topic has a blurb,
    pending_context_auto_open is set; the harness/game loop reads it next
    tick to transition to STATE_QUIZ_CONTEXT."""
    monkeypatch.setattr(quiz_engine, '_CONTEXTS_DIR_OVERRIDE', str(tmp_path))
    _write_subject_file(str(tmp_path), 'philosophy',
                        {'anselm': {'context_blurb': 'Anselm blurb.'}})
    eng = QuizEngine()
    bank = [_q(1, f'anselm-T1-Q{i}', 'right', topic='anselm') for i in range(4)]
    eng._cache['philosophy'] = bank
    eng.start_quiz('threshold', 'philosophy', tier=1,
                   callback=lambda r: None, threshold=1)
    assert eng.pending_context_auto_open == ('philosophy', 'anselm')
    assert eng.current_context_blurb() == 'Anselm blurb.'
