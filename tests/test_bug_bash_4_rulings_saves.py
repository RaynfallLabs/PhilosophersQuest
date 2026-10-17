"""Bug bash 4 rulings (2026-10-17), saves: calls 20, 21, 22 and 23.

20  the high score is recorded when the run ends, not by the drawing code;
    a hero killed by the question left open at Save & Exit gets the death
    screen and a score.
21  two copies of the game playing one hero: the higher version wins; an
    older copy never writes over a later save of the same run. Saves copied
    in by hand still load (an intentional metahack: no tamper checks).
22  names that differ only in case or punctuation get their own save files;
    saves under the old mapping are still found, load, and move over.
23  on load, a hero build's rule flags come from today's SECRET_BUILDS.
Every file the tests write goes to a temp dir.
"""
import os
import pickle
import shutil
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((64, 64))
    return _SCREEN


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    import save_system
    import highscore_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    monkeypatch.setattr(highscore_system, '_SCORE_FILE', str(tmp_path / 'highscores.json'))
    return tmp_path


def _game(name='bb4r5', build=None):
    from main import Game
    from game_states import STATE_PLAYER
    g = Game(_screen(), player_name=name, secret_build=build)
    g.state = STATE_PLAYER
    return g


def _key(g, k):
    return g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0,
                                             unicode='', scancode=0))


def _restore(name):
    from main import _restore_saved_game
    from save_system import load_game
    state = load_game(name)
    assert isinstance(state, dict), f'no save for {name!r}'
    g, notice = _restore_saved_game(_screen(), name, state)
    assert g is not None, notice
    return g


def _scores():
    import highscore_system
    return highscore_system._load()


# ---------------------------------------------------------------- call 20
def test_save_and_exit_whose_open_question_kills_shows_death_and_scores(save_dir):
    """Save & Exit during a fight's question: the question is answered wrong,
    and that answer killed the hero. The game used to quit to the title with
    no death screen and no high score."""
    from save_system import save_exists, save_game
    from game_states import STATE_QUIZ, STATE_DEAD
    g = _game('bb4quitdeath')
    assert save_game(g)

    def _fails_and_kills(result):
        if not result.success:
            g.player.hp = 0
            g._advance_turn()

    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('threshold', 'math', 1, _fails_and_kills, threshold=1)
    pygame.event.clear()
    g.handle_event(pygame.event.Event(pygame.QUIT))          # window X -> dialog
    _key(g, pygame.K_y)                                       # Save & Exit
    assert g.state == STATE_DEAD                              # the death screen
    assert not any(e.type == pygame.QUIT for e in pygame.event.get())
    assert not save_exists('bb4quitdeath')
    rows = [e for e in _scores() if e['name'] == 'bb4quitdeath']
    assert len(rows) == 1 and rows[0]['victory'] is False


def test_save_and_exit_with_a_survivable_question_still_quits(save_dir):
    from game_states import STATE_QUIZ
    g = _game('bb4quitlive')
    results = []
    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('threshold', 'math', 1,
                             lambda r: results.append(r.success), threshold=1)
    pygame.event.clear()
    g.handle_event(pygame.event.Event(pygame.QUIT))
    _key(g, pygame.K_y)
    assert results == [False]
    assert any(e.type == pygame.QUIT for e in pygame.event.get())
    assert g.handle_event(pygame.event.Event(pygame.QUIT)) is False
    assert _scores() == []


def test_score_is_written_once_at_game_over_not_by_the_screen(save_dir):
    from game_states import STATE_DEAD
    g = _game('bb4once')
    g.player.hp = 0
    g.defeat_reason = 'died'
    g._on_game_over()
    g.state = STATE_DEAD
    assert len([e for e in _scores() if e['name'] == 'bb4once']) == 1
    g._on_game_over()                         # a second end call adds nothing
    g._draw_death_screen()
    g._draw_death_screen()
    assert len([e for e in _scores() if e['name'] == 'bb4once']) == 1


def test_victory_records_a_victory_row(save_dir):
    from items import load_items
    g = _game('bb4win')
    stone = next(a for a in load_items('artifact') if a.id == 'philosophers_stone')
    g.player.inventory.append(stone)
    g._do_exit()
    rows = [e for e in _scores() if e['name'] == 'bb4win']
    assert len(rows) == 1 and rows[0]['victory'] is True
    assert rows[0]['score'] >= 50000


def test_the_drawing_code_writes_no_score():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'add_score' not in src


# ---------------------------------------------------------------- call 21
def test_an_older_copy_never_writes_over_a_later_save_of_the_same_run(save_dir):
    from save_system import save_game, read_save_header, _save_path
    g = _game('bb4twin')
    assert save_game(g)
    a = _restore('bb4twin')           # copy A of the game
    b = _restore('bb4twin')           # copy B, same hero, same run
    assert a._run_id == b._run_id
    a.turn_count += 50
    assert save_game(a)
    b.turn_count += 10
    assert save_game(b)                                   # skipped, not an error
    head = read_save_header(_save_path('bb4twin'))
    assert head['turn'] == a.turn_count                   # A's later save kept
    assert any('Another copy of the game' in str(m) for m in _messages(b))
    b.turn_count = a.turn_count + 5                       # B now further on
    assert save_game(b)
    assert read_save_header(_save_path('bb4twin'))['turn'] == b.turn_count


def _messages(g):
    return [str(e[0]) for e in g.msg_log.entries]


def test_a_new_run_under_the_name_is_not_blocked_by_an_old_runs_save(save_dir):
    from save_system import save_game, read_save_header, _save_path
    old = _game('bb4again')
    old.turn_count = 5000
    assert save_game(old)
    new = _game('bb4again')           # a different run (another hero, same name)
    new.turn_count = 3
    assert save_game(new)
    assert read_save_header(_save_path('bb4again'))['turn'] == 3


def test_each_copy_writes_its_own_temp_file(save_dir):
    """Two copies shared one temp name: a temp file held by the other copy
    made about a third of the saves fail."""
    from save_system import save_game, _save_path
    g = _game('bb4tmp')
    os.makedirs(_save_path('bb4tmp') + '.tmp')     # the other copy's temp, in use
    assert save_game(g)


def test_a_save_copied_in_by_hand_still_loads(save_dir, tmp_path_factory):
    """The permadeath metahack stays: back up a save, restore it, it loads.
    Even an older copy restored under a running later game loads, and the
    running game (further on) may still write."""
    from save_system import save_game, _save_path, load_game
    g = _game('bb4copy')
    g.turn_count = 100
    assert save_game(g)
    backup = tmp_path_factory.mktemp('bk') / 'save.pkl'
    shutil.copy(_save_path('bb4copy'), backup)
    g.turn_count = 300
    assert save_game(g)
    shutil.copy(backup, _save_path('bb4copy'))     # the kid puts the old one back
    assert load_game('bb4copy')['turn_count'] == 100
    r = _restore('bb4copy')
    assert r.turn_count == 100


def test_a_save_from_before_headers_still_loads(save_dir):
    from save_system import save_game, load_game, _save_path, MAGIC
    g = _game('bb4bare')
    assert save_game(g)
    path = _save_path('bb4bare')
    raw = open(path, 'rb').read()
    assert raw.startswith(MAGIC)
    state = load_game('bb4bare')
    state.pop('_run_id', None)
    with open(path, 'wb') as f:                      # the old layout: a bare pickle
        pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    r = _restore('bb4bare')
    assert r.player_name == 'bb4bare'
    assert r._run_id == 'legacy:bb4bare'


# ---------------------------------------------------------------- call 22
def test_names_differing_by_case_or_punctuation_get_their_own_saves(save_dir):
    from save_system import save_game, load_game, _save_path
    names = ['Bob', 'bob', 'Bob!', 'bob ', 'BOB_', 'b-o-b', 'Zoë']
    assert len({os.path.normcase(_save_path(n)) for n in names}) == len(names)
    for i, n in enumerate(names):
        g = _game(n)
        g.turn_count = 10 + i
        assert save_game(g)
    for i, n in enumerate(names):
        st = load_game(n)
        assert st['player_name'] == n and st['turn_count'] == 10 + i


def test_a_very_long_name_still_makes_a_valid_file_name(save_dir):
    from save_system import save_game, save_exists, _save_path
    name = '漢' * 48
    assert len(os.path.basename(_save_path(name))) < 200
    assert _save_path(name) != _save_path('漢' * 47)
    assert save_game(_game(name))
    assert save_exists(name)


def _legacy_save(name, turn=77):
    """Write a save the way the old version did: a bare pickle at the old
    (case- and punctuation-folded) path."""
    from save_system import save_game, load_game, _save_path, _legacy_save_path
    g = _game(name)
    g.turn_count = turn
    assert save_game(g)
    state = load_game(name)
    state.pop('_run_id', None)
    os.remove(_save_path(name))
    with open(_legacy_save_path(name), 'wb') as f:
        pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    return _legacy_save_path(name)


def test_a_save_under_the_old_mapping_is_found_loads_and_moves(save_dir):
    from save_system import save_exists, save_game, _save_path
    old = _legacy_save('Bob!')                      # used to be save_bob_.pkl
    assert os.path.basename(old) == 'save_bob_.pkl'
    assert save_exists('Bob!')
    r = _restore('Bob!')
    assert r.player_name == 'Bob!' and r.turn_count == 77
    assert save_game(r)
    assert os.path.exists(_save_path('Bob!'))
    assert not os.path.exists(old)                  # retired: no second copy
    assert save_exists('Bob!')
    assert not save_exists('bob_')                  # no longer found by another name


def test_a_capitalised_old_save_moves_off_the_lowercase_name(save_dir):
    """'Bob' used to live at save_bob.pkl, which is now 'bob''s file."""
    from save_system import save_exists, save_game, _save_path
    old = _legacy_save('Bob')
    assert os.path.normcase(old) == os.path.normcase(_save_path('bob'))
    r = _restore('Bob')
    assert save_game(r)
    assert os.path.exists(_save_path('Bob'))
    assert not save_exists('bob')


def test_death_before_resaving_deletes_the_old_mapping_file(save_dir):
    from save_system import save_exists
    old = _legacy_save('Ann!')
    r = _restore('Ann!')
    r.player.hp = 0
    r.defeat_reason = 'died'
    r._on_game_over()
    assert not os.path.exists(old)
    assert not save_exists('Ann!')


def test_a_new_format_save_is_not_taken_for_another_names_old_save(save_dir):
    from save_system import save_game, save_exists
    assert save_game(_game('bob'))                  # new layout at save_bob.pkl
    assert save_exists('bob')
    assert not save_exists('Bob')                   # not mistaken for 'Bob''s old save


# ---------------------------------------------------------------- call 23
def test_old_build_flags_are_refreshed_on_load(save_dir):
    """An old Dad save kept Dad's old rules: no _joke (boss scrolls, high
    score) and a fist loose in the pack."""
    from welcome_screen import SECRET_BUILDS
    from save_system import save_game
    g = _game('Dad', build=dict(SECRET_BUILDS['dad']))
    fist = g.player.weapon
    assert fist is not None and fist.id == 'punch_in_the_face'
    # Make it look like a save from before the rules: no _joke, no lock, and
    # the fist carried in the pack.
    g.secret_build = {k: v for k, v in g.secret_build.items()
                      if k not in ('_joke', '_lock_weapon')}
    g.player.weapon = None
    fist.bound_to_wielder = False
    g.player.inventory.append(fist)
    assert save_game(g)
    r = _restore('Dad')
    assert r.secret_build.get('_joke') is True
    assert r.secret_build.get('_lock_weapon') is True
    assert r.player.weapon is not None and r.player.weapon.id == 'punch_in_the_face'
    assert r.player.weapon.bound_to_wielder
    assert all(getattr(i, 'id', '') != 'punch_in_the_face' for i in r.player.inventory)


def test_a_plain_hero_named_like_a_build_gets_no_build_on_load(save_dir):
    """Only a run that started as a build is refreshed."""
    from save_system import save_game
    g = _game('Socrates of Athens', build=None)
    assert save_game(g)
    r = _restore('Socrates of Athens')
    assert not r.secret_build
