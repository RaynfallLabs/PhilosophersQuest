"""Bug bash 2026-10-16 (F5), CQ-21: the suite wrote player state
(faulthandler.log, and potentially saves, scores, settings, answer times)
into the dev save dir, which is the project root."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── CQ-21 ────────────────────────────────────────────────────────────────────

def test_the_suite_writes_player_state_outside_the_project_root(tmp_path):
    """Every per-player file the dev build writes goes to save_dir(), and
    during a test run that is a throwaway dir, not the project root."""
    import paths
    import bones
    import highscore_system
    import quiz_engine
    import save_system
    import sound_system
    import main
    root = os.path.normcase(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..')))
    sd = os.path.normcase(os.path.normpath(paths.save_dir()))
    assert sd != root and not sd.startswith(root + os.sep)

    def inside(p):
        return os.path.normcase(os.path.normpath(p)).startswith(sd + os.sep)

    assert inside(highscore_system._SCORE_FILE)
    assert inside(sound_system._settings_path())
    assert inside(save_system._save_path('__cq21__'))
    assert inside(main._fh_path)
    saved = quiz_engine._HISTORY_DIR_OVERRIDE
    try:
        quiz_engine._HISTORY_DIR_OVERRIDE = None
        assert inside(quiz_engine._answer_times_path())
    finally:
        quiz_engine._HISTORY_DIR_OVERRIDE = saved
    # bones: conftest swaps _bones_dir for its own temp dir; it too must be
    # outside the project root
    b = os.path.normcase(os.path.normpath(bones._bones_dir()))
    assert not b.startswith(root + os.sep)


def test_dev_override_never_touches_frozen_paths(monkeypatch, tmp_path):
    import paths
    assert paths._DEV_SAVE_DIR_OVERRIDE
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('APPDATA', str(tmp_path / 'appdata'))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    assert os.path.normpath(paths.save_dir()).startswith(str(tmp_path))
