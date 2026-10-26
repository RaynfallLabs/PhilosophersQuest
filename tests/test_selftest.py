"""The release self-test (src/selftest.py; main.py --selftest-saves).

The release workflow runs it on the built Linux AppImage. Here it runs from
source against a temp folder, with a test key in place of the release one,
so a change that breaks saving, restoring or the Seeker seal fails locally
before it fails a release.
"""
import os
import sys

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import paths  # noqa: E402
import seeker_codes  # noqa: E402
import seeker_profile  # noqa: E402
import selftest  # noqa: E402


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    """A save folder of its own, profiles under it (as in the game), and a
    test key standing in for the release key."""
    monkeypatch.setattr(paths, '_DEV_SAVE_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setattr(seeker_profile, '_DIR_OVERRIDE', None)
    monkeypatch.setattr(seeker_codes, '_KEYS_OVERRIDE',
                        {'label': 'pq9', 'keys': {'pq9': bytes(range(32))}})
    return tmp_path


def _run(*flags):
    from main import Game, _restore_saved_game
    return selftest.run(list(flags), game_cls=Game, restore=_restore_saved_game)


def test_the_self_test_passes_from_source(isolated):
    assert _run('--selftest-saves', '--require-real-key') == 0
    report = (isolated / selftest.REPORT_NAME).read_text(encoding='utf-8')
    assert report.startswith("Philosopher's Quest self-test (saves and Seeker profile): PASS")
    assert '[FAIL]' not in report
    for line in ('saved game: the restored run is the one saved',
                 'Seeker profile: reads back with a good seal',
                 'Seeker profile: an edited copy fails the seal',
                 'reward code: made and checked with the build key'):
        assert f'[ok] {line}' in report, line
    assert any(p.name.startswith('save_') and p.suffix == '.pkl' for p in isolated.iterdir())
    assert any((isolated / 'seekers').glob('seeker_*.json'))


def test_it_fails_when_not_the_built_game(isolated):
    assert _run('--selftest-saves', '--require-frozen') == 1
    report = (isolated / selftest.REPORT_NAME).read_text(encoding='utf-8')
    assert '[FAIL] running as the built game' in report


def test_it_fails_with_the_public_development_key(isolated, monkeypatch):
    monkeypatch.setattr(seeker_codes, '_KEYS_OVERRIDE',
                        {'label': seeker_codes.DEV_LABEL,
                         'keys': {seeker_codes.DEV_LABEL: seeker_codes.DEV_KEY}})
    assert _run('--selftest-saves', '--require-real-key') == 1
    report = (isolated / selftest.REPORT_NAME).read_text(encoding='utf-8')
    assert '[FAIL] reward-code key' in report


def test_a_built_game_must_keep_its_files_where_the_platform_says(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('APPDATA', str(tmp_path / 'appdata'))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    expected = selftest._expected_save_dir()
    assert os.path.normpath(expected) == os.path.normpath(paths.save_dir())
    if sys.platform not in ('win32', 'darwin'):
        assert expected == os.path.join(str(tmp_path / 'xdg'), 'PhilosophersQuest')


def test_main_hands_the_self_test_its_game_and_the_bundle_includes_it():
    with open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8') as f:
        main_src = f.read()
    hook = main_src[main_src.index('if __name__ == "__main__":'):]
    assert "'--selftest-saves' in sys.argv" in hook
    assert 'selftest.run(sys.argv[1:], game_cls=Game, restore=_restore_saved_game)' in hook
    assert hook.index('--selftest-saves') < hook.index('main()')
    with open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8') as f:
        assert "'selftest'" in f.read()


def test_on_a_mac_the_error_log_avoids_the_documents_folder(monkeypatch, tmp_path):
    """macOS asks the player's permission before an app touches Documents,
    so a Mac keeps ERROR_LOG.txt in ~/Library/Logs/PhilosophersQuest."""
    import game_log
    monkeypatch.setattr(game_log, '_LOG_DIR', None)
    monkeypatch.setattr(sys, 'platform', 'darwin')
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setattr(os.path, 'expanduser',
                        lambda p: p.replace('~', str(tmp_path), 1) if p.startswith('~') else p)
    got = game_log.log_dir()
    assert os.path.normpath(got) == os.path.normpath(
        os.path.join(str(tmp_path), 'Library', 'Logs', 'PhilosophersQuest'))
    assert not (tmp_path / 'Documents').exists()
    monkeypatch.setattr(game_log, '_LOG_DIR', None)
