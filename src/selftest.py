"""A hidden self-test for release builds: can the built game keep a player's
things? It writes a saved game and a Seeker profile where a player's would go,
reads both back, restores the save the way the title screen does, and checks
the profile's seal (and a reward code) with the key the build carries.

    PhilosophersQuest --selftest-saves [--require-frozen] [--require-real-key]

The release workflow runs it on the Linux AppImage with XDG_DATA_HOME pointed
at a temporary folder (.github/workflows/release.yml), so a release that
cannot save never ships, and no real player's files are touched.
From source (``python src/main.py --selftest-saves [--save-dir DIR]``) it
writes to DIR or a fresh temp folder, never the project root.
``--require-frozen`` fails unless this is the built game (not the source);
``--require-real-key`` fails unless the build holds the release reward-code
key (src/_dad_key.py, written from the PQ_DAD_KEY secret), not the public
development key.

Exit code 0 when every check passes, 1 otherwise. The report is printed when
there is a console and always written to <save_dir>/selftest_report.txt.
main.py passes in its Game class and its restore function, because the
built game's main script is not importable as a module.
"""
from __future__ import annotations

import json
import os
import random
import sys
import traceback

SELFTEST_FLAG = '--selftest-saves'
REPORT_NAME = 'selftest_report.txt'
HERO_NAME = 'Selftest Hero'
SEEKER_NAME = 'Selftest Seeker'
MARK_TURN = 4321                # written into the save, looked for on the way back
MARK_GOLD = 1234
STAT_KEY = 'selftest_runs'      # a counter in the profile; no achievement reads it


def _inside(path: str, folder: str) -> bool:
    path = os.path.normcase(os.path.realpath(path))
    folder = os.path.normcase(os.path.realpath(folder))
    return path == folder or path.startswith(folder.rstrip(os.sep) + os.sep)


def _expected_save_dir() -> str | None:
    """Where a built game on this platform must keep a player's files
    (paths.save_dir's frozen branch), or None when not frozen."""
    if not getattr(sys, 'frozen', False):
        return None
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME') or os.path.join(
            os.path.expanduser('~'), '.local', 'share')
    return os.path.join(base, 'PhilosophersQuest')


def run(argv, *, game_cls=None, restore=None) -> int:
    """Run every check. ``game_cls`` and ``restore`` are main.Game and
    main._restore_saved_game. Returns the exit code."""
    require_frozen = '--require-frozen' in argv
    require_real_key = '--require-real-key' in argv
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    os.environ['PQ_NO_BONES'] = '1'          # never roll for (or consume) a ghost

    results: list[tuple[bool, str, str]] = []

    def check(ok, what: str, detail: str = '') -> bool:
        results.append((bool(ok), what, str(detail)))
        return bool(ok)

    import paths
    frozen = bool(getattr(sys, 'frozen', False))
    if not frozen:
        # From source, save_dir() is the project root: never write the test's
        # files there. `--save-dir DIR`, else a fresh temp folder. (A built
        # game ignores this and uses the real player location, the point.)
        given = argv[argv.index('--save-dir') + 1] if '--save-dir' in argv[:-1] else None
        if given:
            paths._DEV_SAVE_DIR_OVERRIDE = given
        elif not paths._DEV_SAVE_DIR_OVERRIDE:
            import tempfile
            paths._DEV_SAVE_DIR_OVERRIDE = tempfile.mkdtemp(prefix='pq_selftest_')
    sd = ''
    try:
        check(frozen or not require_frozen, 'running as the built game',
              f"frozen={frozen}, platform={sys.platform}, executable={sys.executable}")
        sd = paths.save_dir()
        check(os.path.isdir(sd), 'save folder exists', sd)
        expected = _expected_save_dir()
        if expected is not None:
            check(os.path.normcase(os.path.realpath(sd)) == os.path.normcase(os.path.realpath(expected)),
                  'save folder is where this platform keeps player files',
                  f"save_dir={sd}, expected={expected}")
            install = getattr(sys, '_MEIPASS', '') or os.path.dirname(sys.executable)
            check(not _inside(sd, install), 'save folder is outside the installed game',
                  f"install={install}")
        _check_saved_game(check, sd, game_cls, restore)
        _check_seeker_profile(check, sd, require_real_key)
    except Exception:
        check(False, 'the self-test ran to the end', traceback.format_exc())

    return _report(results, sd)


def _check_saved_game(check, sd: str, game_cls, restore) -> None:
    import pygame
    import save_system
    if game_cls is None or restore is None:
        check(False, 'saved game: the game was handed in', 'run() needs game_cls and restore')
        return
    pygame.init()                       # display, fonts and sound, as main() does
    screen = pygame.display.set_mode((1, 1))
    random.seed(7)
    game = game_cls(screen, player_name=HERO_NAME)
    game.turn_count = MARK_TURN
    game.player_gold = MARK_GOLD
    path = save_system._save_path(HERO_NAME)
    if not check(save_system.save_game(game), 'saved game: written', path):
        return
    check(os.path.isfile(path) and os.path.getsize(path) > 0 and _inside(path, sd),
          'saved game: file is in the save folder', f"{path} ({os.path.getsize(path) if os.path.isfile(path) else 0} bytes)")
    state = save_system.load_game(HERO_NAME)
    if not check(isinstance(state, dict), 'saved game: reads back'):
        return
    check(state.get('turn_count') == MARK_TURN and state.get('player_gold') == MARK_GOLD,
          'saved game: what was written came back',
          f"turn={state.get('turn_count')}, gold={state.get('player_gold')}")
    restored, notice = restore(screen, HERO_NAME, state)
    if not check(restored is not None, 'saved game: restores as the title screen does', notice or ''):
        return
    check(restored.turn_count == MARK_TURN and restored.player_gold == MARK_GOLD
          and restored.player is not None and restored.dungeon is not None,
          'saved game: the restored run is the one saved',
          f"turn={restored.turn_count}, gold={restored.player_gold}, floor={restored.dungeon_level}")
    check(os.path.isfile(path), 'saved game: restoring did not set the save aside', path)


def _check_seeker_profile(check, sd: str, require_real_key: bool) -> None:
    import seeker_codes
    import seeker_profile
    label = seeker_codes.current_label()
    check(not (require_real_key and seeker_codes.is_dev()),
          'reward-code key: the release key, not the public development key',
          f"label={label}, dev={seeker_codes.is_dev()}")
    path = seeker_profile.profile_path(SEEKER_NAME)
    check(_inside(path, os.path.join(sd, 'seekers')), 'Seeker profile: path is in the save folder', path)
    prof = seeker_profile.load(SEEKER_NAME)
    before = prof.stat(STAT_KEY)
    prof.add(STAT_KEY, 1)
    if not check(prof.flush(), 'Seeker profile: written', path):
        return
    doc, status = seeker_profile.read(path)
    if not check(status == 'ok', "Seeker profile: reads back with a good seal", f"status={status}"):
        return
    check(doc.get('seal_key') == label, 'Seeker profile: sealed with this build\'s key',
          f"seal_key={doc.get('seal_key')}, build key={label}")
    check(int(doc['stats'].get(STAT_KEY, 0)) == before + 1, 'Seeker profile: what was written came back',
          f"{STAT_KEY}={doc['stats'].get(STAT_KEY)}")
    tampered = json.loads(json.dumps(doc))
    tampered['stats'][STAT_KEY] = int(tampered['stats'].get(STAT_KEY, 0)) + 1000
    check(not seeker_codes.seal_ok(seeker_profile.canonical(tampered), tampered.get('seal_key'),
                                   tampered.get('seal')),
          'Seeker profile: an edited copy fails the seal')
    again = seeker_profile.load(SEEKER_NAME)
    check(again.stat(STAT_KEY) == before + 1 and not again.readonly,
          'Seeker profile: loads again as the game would', f"{STAT_KEY}={again.stat(STAT_KEY)}")
    if not seeker_codes.is_dev():
        code = seeker_codes.make_code('selftest', 'SELFTEST', SEEKER_NAME)
        got = seeker_codes.check_code(code, SEEKER_NAME, [('selftest', 'SELFTEST')])
        check(got is not None and got[0] == 'selftest', 'reward code: made and checked with the build key',
              f"{code} -> {got}")
        check(seeker_codes.check_code(code, 'Someone Else', [('selftest', 'SELFTEST')]) is None,
              "reward code: refused for another Seeker")


def _report(results, sd: str) -> int:
    ok = bool(results) and all(r[0] for r in results)
    lines = [f"Philosopher's Quest self-test (saves and Seeker profile): {'PASS' if ok else 'FAIL'}"]
    try:
        import layout
        lines.append(f"version {getattr(layout, 'VERSION', '?')}")
    except Exception:
        pass
    lines.append(f"save folder: {sd or '?'}")
    for passed, what, detail in results:
        lines.append(f"[{'ok' if passed else 'FAIL'}] {what}" + (f"  ({detail})" if detail else ''))
    text = '\n'.join(lines) + '\n'
    if sys.stdout is not None:
        try:
            sys.stdout.write(text)
            sys.stdout.flush()
        except Exception:
            pass
    if sd:
        try:
            with open(os.path.join(sd, REPORT_NAME), 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError:
            pass
    return 0 if ok else 1
