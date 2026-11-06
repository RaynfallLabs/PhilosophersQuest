"""Bug bash 3.3.1, senet and leaving a quiz.

C4: with philosophy tier 5 mastered, losing senet's first two rounds and
auto-passing the third still won the Book of Thoth: at the top tier a
mastered tier made the whole quiz a success, lost rounds or not.

C5: Esc on a question ended the quiz with no per-round cost (senet's lost
max HP and paralysis were skipped, and so was every round still to come),
and closing the window mid-question froze a timed clock for as long as the
exit dialog stayed up, as often as wanted.

Setne's tomb is on floors 45-65 and rolled per run, so it cannot be
play-tested on demand: these drive the real encounter on a real Game.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


@pytest.fixture(autouse=True)
def _no_saves(monkeypatch, tmp_path):
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _game(seed=5, name='__bb331_senet__'):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    g.state = STATE_PLAYER
    return g


def _senet(g, mastered=()):
    """Open Setne's tomb and sit down at senet, staking yourself."""
    from game_states import STATE_PLAYER, STATE_QUIZ
    g._change_level(g._setne['floor'], enter_from_top=True)
    g.state = STATE_PLAYER
    ghost = next(m for m in g.monsters if m.alive
                 and getattr(m, '_flavor_encounter_tag', None) == 'flv_setne_tomb')
    g.player.max_hp = g.player.hp = 40
    g._start_flavor_encounter(ghost)
    g.quiz_engine._mastered = {('philosophy', t) for t in mastered}
    g._npc_show_options()
    pairs = [p for p in g._npc_visible_options() if p[0] == 1]
    g._npc_selected_index, g._npc_selected_option = pairs[0]
    g._apply_npc_choice(pairs[0][1], None)
    assert g.state == STATE_QUIZ


def _answer(g, right: bool):
    qe = g.quiz_engine
    qe.answer(str(qe.current_question['answer']) if right else '__surely wrong__')
    qe._result_hold_until = 0.0
    qe.release_result_hold()
    qe.update(5.0)


def _has_book(g):
    return any(getattr(i, 'id', '') == 'book_of_thoth' for i in g.player.inventory)


def _esc(g):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=''))


# ----------------------------------------------------------------- C4

def test_two_lost_rounds_then_a_mastered_top_tier_is_still_a_loss():
    g = _game()
    _senet(g, mastered=(5,))
    _answer(g, False)                 # round 1, tier 3: lost
    _answer(g, False)                 # round 2, tier 4: lost; round 3 auto-passes at 5
    assert g.quiz_engine.callback is None
    assert not _has_book(g)
    assert g.quiz_engine.auto_passed == 1


def test_won_two_of_three_by_mastery_still_wins():
    """The rule is two rounds of three: mastered rounds count as won."""
    g = _game()
    _senet(g, mastered=(4, 5))
    _answer(g, False)                 # round 1 lost; rounds 2 and 3 auto-pass
    assert _has_book(g)


def test_a_fully_mastered_escalator_threshold_still_succeeds():
    """The Sphinx and Brokkr's Anvil: a ladder passed by mastery alone,
    short of the threshold only because it ran out of tiers."""
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe._mastered = {('philosophy', 3), ('philosophy', 4), ('philosophy', 5)}
    out = []
    qe.start_quiz('escalator_threshold', 'philosophy', 3, out.append, threshold=4, total_qs=6)
    assert out and out[0].success


# ----------------------------------------------------------------- C5

def test_esc_on_senets_first_question_costs_what_losing_costs():
    g = _game()
    _senet(g)
    floor = g._setne['floor']
    _esc(g)
    assert g.player.max_hp < 40                   # round one's price
    assert g.player.has_effect('paralyzed')       # round two's
    assert g._npc_encounter_phase == 'outcome'    # the lost game's page
    g._npc_outcome_continue()
    assert g.dungeon_level == floor - 1           # no round won: the floor gives you up
    assert not _has_book(g)


def test_esc_after_a_won_round_pays_for_the_rounds_left():
    g = _game()
    _senet(g)
    _answer(g, True)                              # round 1 won
    _esc(g)                                       # rounds 2 and 3 lost
    assert g.player.max_hp < 40
    assert g.player.has_effect('paralyzed')
    assert not _has_book(g)


def test_esc_on_an_ordinary_quiz_is_still_a_plain_failure():
    g = _game()
    got = []
    from game_states import STATE_QUIZ
    g.quiz_engine.start_quiz(mode='threshold', subject='history', tier=1, threshold=1,
                             total_qs=1, callback=got.append)
    g.state = STATE_QUIZ
    _esc(g)
    assert got and not got[0].success


def test_closing_the_window_mid_question_does_not_stop_the_clock():
    from game_states import STATE_QUIZ, STATE_CONFIRM_EXIT
    from quiz_engine import QuizState
    g = _game()
    g.quiz_engine.start_quiz(mode='chain', subject='math', tier=1, max_chain=5,
                             callback=lambda r: None, base_seconds=20)
    g.state = STATE_QUIZ
    before = g.quiz_engine.time_remaining
    g.handle_event(pygame.event.Event(pygame.QUIT))
    assert g.state == STATE_CONFIRM_EXIT
    g._exit_dialog_opened_at -= 7.0               # seven seconds looking at the dialog
    _esc(g)                                       # "Keep playing"
    assert g.state == STATE_QUIZ
    assert g.quiz_engine.time_remaining <= before - 7.0 + 0.5
    # ...and again: the dialog is no pause, however often it is opened.
    g.handle_event(pygame.event.Event(pygame.QUIT))
    g._exit_dialog_opened_at -= 60.0
    _esc(g)
    assert g.quiz_engine.state != QuizState.ASKING     # the clock ran out
