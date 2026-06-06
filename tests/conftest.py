"""Shared pytest fixtures.

Keeps the test suite from writing to the player's REAL error log. Several tests
exercise save/load failure paths and the crash handler, which call into
game_log; without this, running `pytest` would append test noise to
<Documents>/PhilosophersQuest/ERROR_LOG.txt. Redirect the whole test session to
a throwaway temp dir instead. (test_error_logging.py layers its own per-test
redirect on top of this, which still works because it saves/restores state.)
"""
import logging
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(autouse=True, scope='session')
def _redirect_game_log_to_temp():
    try:
        import game_log
    except Exception:
        yield
        return
    tmpdir = tempfile.mkdtemp(prefix='pq_test_log_')
    lg = logging.getLogger('philosophers_quest')
    saved_handlers = lg.handlers[:]
    saved_dir, saved_logger = game_log._LOG_DIR, game_log._LOGGER
    lg.handlers.clear()
    game_log._LOG_DIR = tmpdir
    game_log._LOGGER = None
    try:
        yield
    finally:
        for h in lg.handlers:
            try:
                h.close()
            except Exception:
                pass
        lg.handlers[:] = saved_handlers
        game_log._LOG_DIR = saved_dir
        game_log._LOGGER = saved_logger
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@pytest.fixture(autouse=True, scope='session')
def _isolate_quiz_history():
    """Point the cross-game quiz-recency file at a throwaway temp dir so the
    suite never reads or writes the player's real <save_dir>/quiz_history.json.
    Every quiz that ends persists this file; without the redirect, pytest would
    seed and clobber the real player's question history."""
    try:
        import quiz_engine
    except Exception:
        yield
        return
    tmpdir = tempfile.mkdtemp(prefix='pq_test_quizhist_')
    saved = quiz_engine._HISTORY_DIR_OVERRIDE
    quiz_engine._HISTORY_DIR_OVERRIDE = tmpdir
    try:
        yield
    finally:
        quiz_engine._HISTORY_DIR_OVERRIDE = saved
        shutil.rmtree(tmpdir, ignore_errors=True)
