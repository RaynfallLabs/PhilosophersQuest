"""Math is Cool (3.5.2): Brandon's song "So Then I Was Like..." as A Man
Before a King.

A hundred math answers right in a row in one run earns the power Math is
Cool (V), ready every 5,000 turns. Using it plays the song once in place of
the soundtrack, and while it plays every right answer in a fight counts as
two links. The first time also earns the achievement So Then I Was Like...
(songs.py, quirk_system.py, combat.effective_chain, game_menus.)
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import songs  # noqa: E402

SONG = 'math_is_cool'
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


@pytest.fixture
def quiet_music(monkeypatch):
    import music
    calls = []
    monkeypatch.setattr(music, 'play_song', lambda path, at=0.0: calls.append(('play', path)))
    monkeypatch.setattr(music, 'end_song', lambda: calls.append(('end',)))
    monkeypatch.setattr(music, 'mute_song', lambda: calls.append(('mute',)))
    monkeypatch.setattr(music, 'is_held', lambda: False)
    monkeypatch.setattr(music, 'song_playing', lambda: False)
    return calls


def _game():
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='__test_math_is_cool__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _answer(g, correct, subject='math', timed_out=False):
    g.quiz_engine.last_answer = '' if timed_out else ('7' if correct else '9')
    g.quirk_system.on_quiz_answer(
        subject=subject, correct=correct, chain=1, while_blinded=False,
        while_confused=False, while_hallucinating=False, while_feared=False,
        wrong_this_session=0, score_this_session=0)


def _goblin():
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        gob = dict(json.load(f)['goblin'], id='goblin')
    return Monster(gob, 1, 1)


# ---------------------------------------------------------------- the data

def test_the_song_its_power_and_its_art_ship():
    s = songs.song(SONG)
    assert s['title'] == 'So Then I Was Like...' and s['artist'] == 'A Man Before a King'
    assert s['chain_mult'] == 2
    assert songs.power_of(SONG) == {'id': 'math_is_cool', 'streak': 100, 'cooldown': 5000}
    assert songs.song_for_power('math_is_cool') == SONG
    assert os.path.exists(songs.track_path(SONG))
    assert os.path.exists(os.path.join(ROOT, 'assets', 'achievements', 'so_then_i_was_like.png'))
    import quirk_system
    assert quirk_system._ACTIVE_POWER_DEFS['math_is_cool']['cooldown'] == 5000
    assert quirk_system._QUIRK_PROGRESS['math_is_cool'] == ('math_streak', 100, False)
    import quirk_text
    assert 'Doubles your math chain' in quirk_text.quirk_description('math_is_cool')
    assert quirk_text.quirk_hint('math_is_cool')


# ---------------------------------------------------------------- earning it

def test_a_hundred_math_answers_right_in_a_row_earns_the_power():
    g = _game()
    for _ in range(99):
        _answer(g, True)
    assert not g.quirk_system.is_unlocked('math_is_cool')
    _answer(g, True)
    assert g.quirk_system.is_unlocked('math_is_cool')
    assert g.player.power_cooldowns['math_is_cool'] == 0          # ready at once
    assert any('POWER UNLOCKED: Math is Cool' in str(e[0]) for e in g.msg_log.entries)


def test_a_wrong_answer_breaks_the_run_the_clock_does_not():
    g = _game()
    for _ in range(60):
        _answer(g, True)
    _answer(g, False, timed_out=True)        # the clock ends every fight's chain
    _answer(g, True, subject='history')      # other subjects neither count nor break it
    _answer(g, False, subject='history')
    assert g.quirk_system._p('math_streak') == 60
    _answer(g, False)
    assert g.quirk_system._p('math_streak') == 0
    for _ in range(99):
        _answer(g, True)
    assert not g.quirk_system.is_unlocked('math_is_cool')


# ---------------------------------------------------------------- using it

def _attack_chain(g, right):
    """A real attack quiz on a goblin: ``right`` answers right, then the
    chain on the quiz's own counter."""
    import combat
    qe = g.quiz_engine
    combat.player_attack(g.player, _goblin(), qe, lambda *a, **k: None)
    seen = []
    for _ in range(right):
        qe.answer(str(qe.current_question['answer']))
        seen.append(qe.chain)
        qe.result_timer = 0
        qe.update(0.01)                       # on to the next question
    return seen


def test_the_power_plays_the_song_and_doubles_the_chain_on_the_quiz(quiet_music):
    g = _game()
    for _ in range(100):
        _answer(g, True)
    p = g.player
    assert _attack_chain(g, 3) == [1, 2, 3]
    assert g._activate_power('math_is_cool') is False                # a turn passes
    assert p.power_cooldowns['math_is_cool'] == 5000
    st = songs.active(p)
    assert st and st['id'] == SONG and st['left'] == pytest.approx(175)
    said = ' '.join(str(e[0]) for e in g.msg_log.entries[-3:])
    assert 'Math is NOT cool' in said and 'counts double' in said
    assert songs.effect_label(p) == 'Math is Cool 2:55'
    # The counter on the quiz goes up by two, where it is seen.
    assert _attack_chain(g, 3) == [2, 4, 6]
    g._song_frame(0.0)
    assert quiet_music[0][0] == 'play' and quiet_music[0][1].endswith('math_is_cool.ogg')
    for _ in range(400):
        g._song_frame(0.5)
    assert songs.active(p) is None
    assert any('help me with my homework' in str(e[0]) for e in g.msg_log.entries[-4:])
    assert _attack_chain(g, 3) == [1, 2, 3]


def test_the_text_is_short_and_keeps_the_song_a_surprise():
    import quirk_system
    import quirk_text
    texts = [quirk_text.quirk_description('math_is_cool'), quirk_text.quirk_hint('math_is_cool'),
             quirk_system._QUIRK_EFFECTS['math_is_cool'], quirk_system._QUIRK_TRIGGER['math_is_cool'],
             quirk_system._ACTIVE_POWER_DEFS['math_is_cool']['desc']]
    for t in texts:
        assert 'song' not in t.lower() and 'So Then' not in t, t
    assert len(quirk_text.quirk_description('math_is_cool')) <= 100


def test_a_cap_is_never_passed_by_a_step_of_two():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.start_quiz(mode='chain', subject='math', tier=1, callback=lambda *a: None,
                  max_chain=5, chain_step=lambda: 2)
    for _ in range(3):
        if qe.current_question is None:
            break
        qe.answer(str(qe.current_question['answer']))
        qe.result_timer = 0
        qe.update(0.01)
    assert qe.chain == 5


def test_the_cooldown_counts_down_turn_by_turn(quiet_music):
    g = _game()
    for _ in range(100):
        _answer(g, True)
    g._activate_power('math_is_cool')
    for _ in range(10):
        g.quirk_system.tick_powers()
    assert g.player.power_cooldowns['math_is_cool'] == 4990
    import hud_context
    rows = hud_context.active_power_rows(g.player)
    row = next(r for r in rows if r.label == 'Math is Cool')
    assert row.state == 'cooldown' and row.status == '4990 Turns'


def test_one_song_at_a_time(quiet_music):
    import kitchen
    g = _game()
    for _ in range(100):
        _answer(g, True)
    songs.begin(g.player, 'caviar_and_tater_tots')
    # The power waits, its cooldown not spent and no turn passed.
    assert g._activate_power('math_is_cool') is True
    assert g.player.power_cooldowns['math_is_cool'] == 0
    assert songs.active(g.player)['id'] == 'caviar_and_tater_tots'
    assert 'One song at a time' in str(g.msg_log.entries[-1][0])
    # And the dish waits while Math is Cool plays.
    songs.end(g.player)
    g._activate_power('math_is_cool')
    for fid in ('caviar', 'tater_tots'):
        f = items.make_item_by_id('food', fid)
        f.count = 1
        g.player.add_to_inventory(f)
    g._open_cook_menu()
    g._cook_tab = kitchen.MENU_TABS.index('special')
    rows = g._cook_tab_rows()
    g._cook_sel = next(i for i, r in enumerate(rows) if r['id'] == 'dish_caviar_and_tater_tots')
    g._cook_menu_input(pygame.K_RETURN)
    assert songs.active(g.player)['id'] == SONG
    assert sum(1 for i in g.player.inventory if getattr(i, 'id', '') in ('caviar', 'tater_tots')) == 2


# ---------------------------------------------------------------- the badge

def test_the_achievement_comes_with_the_power():
    import achievements
    with open(os.path.join(ROOT, 'data', 'achievements.json'), encoding='utf-8') as f:
        a = next(x for x in json.load(f)['achievements'] if x['id'] == 'so_then_i_was_like')
    assert a['name'] == 'So Then I Was Like...' and a['category'] == 'secrets'
    assert 'A Man Before a King' in a['hint']
    for w in a['spoiler_words']:
        assert w.lower() not in a['hint'].lower()
    assert a['trigger'] == {'event': 'trait', 'where': {'trait': 'math_is_cool'}}
    assert achievements._matches(a['trigger']['where'], {'trait': 'math_is_cool'})


def test_the_power_tells_the_seeker(monkeypatch):
    g = _game()
    seen = []
    monkeypatch.setattr(g, '_seeker_event', lambda ev, **kw: seen.append((ev, kw)) or [])
    for _ in range(100):
        _answer(g, True)
    assert ('trait', {'trait': 'math_is_cool'}) in seen


def test_the_qa_build_previews_the_achievement():
    """The QA build records nothing, so its test runs saw no achievement:
    one an event earns opens as a preview, once, with no code."""
    from welcome_screen import SECRET_BUILDS
    from main import Game
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='Titivillus', secret_build=SECRET_BUILDS['titivillus'])
    g.player.qa_tools = True
    assert g._seeker is None
    g._qa_math_is_cool()
    _answer(g, True)
    pops = [e for e in g._popup_queue if e.get('kind') == 'achievement']
    assert pops, 'no achievement popup on the QA build'
    card = pops[-1]['data']['achievements'][0]
    assert card['id'] == 'so_then_i_was_like' and card['code'] == 'QA PREVIEW'
    n = len(pops)
    g._seeker_event('trait', trait='math_is_cool')
    assert len([e for e in g._popup_queue if e.get('kind') == 'achievement']) == n   # once


def test_the_qa_mooble_key_sets_the_hero_beside_him():
    from welcome_screen import SECRET_BUILDS
    from main import Game
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='Titivillus', secret_build=SECRET_BUILDS['titivillus'])
    g.player.qa_tools = True
    g._qa_mooble()
    m = g._mooble_here()
    if m is None:
        pytest.skip('no room for the Mooble on this floor')
    assert max(abs(g.player.x - m.x), abs(g.player.y - m.y)) <= 2
    assert (m.x, m.y) in g.visible


def test_the_qa_build_can_reach_it_in_one_answer():
    g = _game()
    g._qa_math_is_cool()
    assert not g.quirk_system.is_unlocked('math_is_cool')
    _answer(g, True)
    assert g.quirk_system.is_unlocked('math_is_cool')
    g.player.power_cooldowns['math_is_cool'] = 4000
    g._qa_math_is_cool()
    assert g.player.power_cooldowns['math_is_cool'] == 0
