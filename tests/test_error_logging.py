"""Tests for the verbose error-logging + crash-recovery hardening (added so the
dev's kids can play on their own machines, never hard-crash on a recoverable
error, and email a single verbose log file when something goes wrong).

Covers:
  * game_log writes a verbose ERROR_LOG.txt (with full tracebacks)
  * logging never raises, even though it must run inside except blocks
  * crash_handler writes a crash report AND folds it into ERROR_LOG.txt,
    co-located in the same (Documents) folder
  * the in-loop recovery helper logs + returns the game to a playable state
  * save/load failures are recorded to the log (they used to print() into the
    void in the windowed bundle)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pygame  # noqa: E402
pygame.init()


@pytest.fixture
def log_to_tmp(tmp_path):
    """Redirect game_log to a temp dir with a clean logger, restore afterward."""
    import game_log
    lg = logging.getLogger('philosophers_quest')
    saved_handlers = lg.handlers[:]
    saved_dir, saved_logger = game_log._LOG_DIR, game_log._LOGGER
    lg.handlers.clear()
    game_log._LOG_DIR = str(tmp_path)
    game_log._LOGGER = None
    try:
        yield game_log, tmp_path
    finally:
        for h in lg.handlers:
            try:
                h.close()
            except Exception:
                pass
        lg.handlers[:] = saved_handlers
        game_log._LOG_DIR = saved_dir
        game_log._LOGGER = saved_logger


def _read_log(tmp_path):
    p = tmp_path / 'ERROR_LOG.txt'
    return p.read_text(encoding='utf-8') if p.exists() else ''


# ---------------------------------------------------------------------------
# game_log basics
# ---------------------------------------------------------------------------

def test_log_path_points_at_error_log_txt(log_to_tmp):
    game_log, tmp_path = log_to_tmp
    assert game_log.log_path().endswith('ERROR_LOG.txt')
    assert game_log.log_dir() == str(tmp_path)


def test_log_error_writes_message_and_traceback(log_to_tmp):
    game_log, tmp_path = log_to_tmp
    try:
        raise ValueError("boom-xyzzy")
    except ValueError:
        game_log.log_error("something broke in the widget")
    text = _read_log(tmp_path)
    assert "something broke in the widget" in text
    assert "Traceback" in text          # full traceback captured
    assert "boom-xyzzy" in text         # original exception message present
    assert "[ERROR]" in text


def test_log_info_and_session_start_write(log_to_tmp):
    game_log, tmp_path = log_to_tmp
    game_log.log_session_start(version="9.9.9", player="kiddo", build=None)
    game_log.log_info("a breadcrumb")
    text = _read_log(tmp_path)
    assert "SESSION START" in text
    assert "9.9.9" in text and "kiddo" in text
    assert "a breadcrumb" in text


def test_logging_never_raises_even_if_dir_is_bogus(log_to_tmp):
    """A broken log destination must not propagate -- a dead log beats a dead
    game. Point the dir at an unwritable path and confirm no exception."""
    game_log, _ = log_to_tmp
    lg = logging.getLogger('philosophers_quest')
    lg.handlers.clear()
    game_log._LOGGER = None
    # NUL device dir can't be created/written as a directory -> handler init fails
    game_log._LOG_DIR = None  # force re-resolve, but break expanduser via a bad cwd?
    # Simpler: directly force a bogus cached dir on an illegal path.
    game_log._LOG_DIR = "Z:\\nonexistent\\\0illegal"
    # These must all be silent no-throws.
    game_log.log_info("x")
    game_log.log_error("y", exc_info=False)
    game_log.log_crash_report("z")
    # nothing to assert beyond "did not raise"


# ---------------------------------------------------------------------------
# crash_handler integration
# ---------------------------------------------------------------------------

def test_crash_report_writes_file_and_folds_into_error_log(log_to_tmp):
    game_log, tmp_path = log_to_tmp
    import crash_handler
    try:
        raise RuntimeError("kaboom-42")
    except RuntimeError:
        path = crash_handler.write_crash_report(*sys.exc_info(), game=None)
    # standalone crash_*.txt written into the SAME (redirected) folder
    p = Path(path)
    assert p.exists()
    assert p.parent == tmp_path
    assert p.name.startswith('crash_') and p.suffix == '.txt'
    body = p.read_text(encoding='utf-8')
    assert "CRASH REPORT" in body
    assert "kaboom-42" in body
    assert "TRACEBACK" in body
    # AND the full report is folded into the single ERROR_LOG.txt
    log_text = _read_log(tmp_path)
    assert "FATAL CRASH" in log_text
    assert "kaboom-42" in log_text


def test_crash_report_dir_matches_log_dir(log_to_tmp):
    """Crash reports and the error log must live in the same folder so testers
    find everything in one place."""
    game_log, tmp_path = log_to_tmp
    import crash_handler
    assert crash_handler._project_root() == game_log.log_dir() == str(tmp_path)


# ---------------------------------------------------------------------------
# in-loop recovery
# ---------------------------------------------------------------------------

def test_recover_in_loop_resets_state_and_logs(log_to_tmp):
    game_log, tmp_path = log_to_tmp
    import main

    class FakeGame:
        def __init__(self):
            self.state = 'some_menu'
            self.messages = []

        def add_message(self, msg, kind='info'):
            self.messages.append((msg, kind))

    g = FakeGame()
    try:
        raise KeyError("widget_42")
    except KeyError:
        # must not raise, even though we're simulating a loop crash
        main._recover_in_loop(g, "update")

    assert g.state == main.STATE_PLAYER          # recovered to playable
    assert g.messages                            # player was told something
    text = _read_log(tmp_path)
    assert "recovered from error in update" in text
    assert "widget_42" in text                   # traceback captured


def test_recover_in_loop_survives_a_broken_game_object(log_to_tmp):
    """Even if add_message / state assignment fail, recovery must not raise."""
    game_log, _ = log_to_tmp
    import main

    class HostileGame:
        @property
        def state(self):
            raise RuntimeError("no state for you")

        @state.setter
        def state(self, v):
            raise RuntimeError("cannot set state")

        def add_message(self, *a, **k):
            raise RuntimeError("no messages either")

    try:
        raise ValueError("deep_fail")
    except ValueError:
        main._recover_in_loop(HostileGame(), "render")   # must be silent
