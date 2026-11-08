"""Bug bash 3.3.3 play: the Kit / character sheet "Result" box showed
whatever the world said in the turn the action spent (a bite, a hunger pang,
the new hit lines), pushing out the action's own line; and putting on a helm
or leggings said "AC is now 10", which no longer means anything for a piece
that gives no AC.

main._world_turn pauses the Result capture while Game._advance_turn runs;
Game._ac_now_note adds the AC only for body armour and shields.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import quiz_engine
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(2)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_result_box__')
    g.monsters = []
    g.state = STATE_PLAYER
    # The world says something every turn (a monster's bite, say).
    real = g._say_springs
    monkeypatch.setattr(g, '_say_springs', lambda: (g.add_message('A rat bites you.', 'danger'), real()))
    return g


def _equip_from_kit(g, item):
    from game_states import STATE_QUIZ
    from quiz_engine import QuizResult
    g._open_kit_panel()
    g._item_action_run('equip', item, {'screen': 'kit'})
    if g.state == STATE_QUIZ:
        qe = g.quiz_engine
        qe.callback(QuizResult(success=True, score=qe.required, correct=qe.required, asked=qe.required))
    return [t for t, _k in g._item_feedback_lines()]


def test_the_result_box_says_what_the_action_said_not_the_turn(game):
    legs = items.instantiate_armor('leather_leggings', 'leather', level=3, ench_id='mailed_shins')
    game.player.inventory.append(legs)
    lines = _equip_from_kit(game, legs)
    assert any(t.startswith('You equip') for t in lines), lines
    assert not any('rat bites' in t for t in lines), lines
    assert any('rat bites' in str(e[0]) for e in game.msg_log.entries)      # still in the log


def test_a_minor_piece_does_not_say_ac_a_body_armour_does(game):
    legs = items.instantiate_armor('leather_leggings', 'leather', level=1)
    game.player.inventory.append(legs)
    assert not any('AC is now' in t for t in _equip_from_kit(game, legs))
    body = items.instantiate_armor('padded', 'linen', level=1)
    game.player.inventory.append(body)
    assert any('AC is now' in t for t in _equip_from_kit(game, body))


def test_take_and_equip_keeps_capturing_after_the_pickups_turn(game):
    helm = items.instantiate_armor('leather_cap', 'leather', level=1)
    helm.x, helm.y = game.player.x, game.player.y
    game.ground_items.append(helm)
    lines = _equip_from_kit(game, helm)
    assert any(t.startswith('You equip') for t in lines), lines
    assert not any('rat bites' in t for t in lines), lines


def test_the_examine_line_shows_ac_only_where_it_is():
    from main import Game
    g = Game.__new__(Game)
    plate = items.instantiate_armor('plate', 'damascus_steel', level=5)
    helm = items.instantiate_armor('steel_helm', 'damascus_steel', level=5, ench_id='iron_will')
    assert f"-{plate.ac_bonus + plate.enchant_bonus} AC" in Game._get_item_stats_brief(g, plate)
    assert 'AC' not in Game._get_item_stats_brief(g, helm)
    assert 'Iron Will III' in Game._get_item_stats_brief(g, helm)
