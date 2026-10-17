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

# The dev save dir is the project root, so without this every run wrote
# highscores.json, answer_times.json, settings.json, bones/ and test saves
# beside the real ones (bug bash 2026-10-16, CQ-21). Set at conftest import,
# before test modules are collected: main.py opens faulthandler.log in the
# save dir at import time. Frozen-mode paths are untouched.
import paths as _paths  # noqa: E402

_TEST_SAVE_DIR = tempfile.mkdtemp(prefix='pq_test_savedir_')
_paths._DEV_SAVE_DIR_OVERRIDE = _TEST_SAVE_DIR


# ---- slow tests (bug bash 4, ruling 35) ------------------------------------
# The UI gates and frame-time tests take about seven of the suite's ten
# minutes. They are marked `slow` and left out of a plain local run; CI runs
# everything. To run them yourself:
#   python -m pytest tests/ --run-slow          everything
#   python -m pytest tests/ -m slow --run-slow   only the slow ones
# (PQ_RUN_SLOW=1 in the environment does the same as --run-slow.)
def pytest_addoption(parser):
    parser.addoption('--run-slow', action='store_true', default=False,
                     help='also run tests marked slow (the UI gates and frame '
                          'timing); CI always does')


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'slow: slow UI gates and frame-time tests; run with --run-slow (CI does)')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-slow') or os.environ.get('PQ_RUN_SLOW') == '1':
        return
    keep, slow = [], []
    for item in items:
        (slow if item.get_closest_marker('slow') else keep).append(item)
    if slow:
        config.hook.pytest_deselected(items=slow)
        items[:] = keep


@pytest.fixture(autouse=True, scope='session')
def _isolate_dev_save_dir():
    try:
        yield _TEST_SAVE_DIR
    finally:
        shutil.rmtree(_TEST_SAVE_DIR, ignore_errors=True)


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


@pytest.fixture(autouse=True, scope='session')
def _isolate_bones():
    """Keep the suite away from the player's REAL bones files.

    `LevelManager.generate()` calls `bones.load_bones`, which deletes the
    file it reads (a ghost appears once). Any test that generates a floor
    could therefore eat a ghost left by one of the player's own dead
    characters. Point the bones directory at a throwaway temp dir.
    """
    try:
        import bones
    except Exception:
        yield
        return
    tmpdir = tempfile.mkdtemp(prefix='pq_test_bones_')
    saved = bones._bones_dir
    bones._bones_dir = lambda: tmpdir
    try:
        yield
    finally:
        bones._bones_dir = saved
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(autouse=True)
def _fresh_unique_registry():
    """Every test starts as a new run: no named unique has been found yet.
    (items.bind_unique_registry is module state; without this, uniques claimed
    by one test would be missing from the next.)"""
    try:
        import items
        items.bind_unique_registry(set())
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def _restore_layout_and_ui_scale():
    """``layout.update`` sets module state: the window size AND the UI scale
    (_genart/ui/SCALE_PLAN.md), which every font fetched through get_font
    follows. Every test starts from the same baseline -- the default
    1600x900 window at UI scale 1.0, i.e. the unscaled UI the suite's
    geometry and pixel tests were written against -- and the state is put
    back afterwards, so no test inherits another's window size (e.g. a
    3440x1440 render leaving every font 1.5x). Tests about the scale set the
    window themselves with ``layout.update``."""
    try:
        import layout
    except Exception:
        yield
        return
    snap = layout.snapshot()
    layout.restore((1600, 900, 1.0))
    try:
        yield
    finally:
        layout.restore(snap)


@pytest.fixture
def ui_theme_isolated():
    """Each test starts with an EMPTY UI art kit and gets the previous kit
    back afterwards, so a test never depends on whether an earlier test (or
    the capture harness) loaded assets/ui/ (GROUNDWORK_REVIEW 9). Opt in
    with ``pytestmark = pytest.mark.usefixtures('ui_theme_isolated')``."""
    import ui_theme
    saved = ui_theme.save_state()
    ui_theme.unload()
    try:
        yield
    finally:
        ui_theme.restore_state(saved)
