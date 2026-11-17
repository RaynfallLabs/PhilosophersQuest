"""The sidebar's Streak line under Lesson (Brandon, 2026-11-16): questions
right in a row in every subject, and maths questions right in a row, read from
the counters quirk_system.on_quiz_answer already keeps."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import hud_context  # noqa: E402


def _hero(**prog):
    return types.SimpleNamespace(quirk_progress=dict(prog))


def test_a_new_hero_reads_zero_and_faded():
    assert hud_context.streak_line(types.SimpleNamespace()) == ("Streak: 0   Math: 0", 'none')


def test_the_line_shows_both_counts():
    text, state = hud_context.streak_line(_hero(consecutive_correct=7, math_streak=3))
    assert text == "Streak: 7   Math: 3" and state == 'open'


def test_ten_in_a_row_glows():
    assert hud_context.streak_line(_hero(consecutive_correct=2, math_streak=10))[1] == 'hot'
    assert hud_context.streak_line(_hero(consecutive_correct=12))[1] == 'hot'


def test_the_sidebar_draws_it_under_the_lesson_line():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'ui.py'), encoding='utf-8').read()
    assert 'cooking_hp_line(player), lesson, streak_line(player)' in src


def test_a_wrong_answer_breaks_both_and_a_time_out_breaks_neither():
    import quirk_system
    from player import Player
    hero = Player()
    hero.quirk_progress = {}
    engine = types.SimpleNamespace(last_answer='B')
    game = types.SimpleNamespace(quiz_engine=engine, player=hero)
    qs = quirk_system.QuirkSystem(game)
    qs.is_unlocked = lambda *_a: True             # no quirk award in the way
    for _ in range(4):
        qs.on_quiz_answer('math', True, 1, False, False, False, False, 0, 0)
    assert hud_context.streak_line(hero)[0] == "Streak: 4   Math: 4"
    engine.last_answer = ''                       # the clock ran out
    qs.on_quiz_answer('math', False, 1, False, False, False, False, 0, 0)
    assert hud_context.streak_line(hero)[0] == "Streak: 4   Math: 4"
    engine.last_answer = 'C'                      # a wrong answer
    qs.on_quiz_answer('math', False, 1, False, False, False, False, 0, 0)
    assert hud_context.streak_line(hero)[0] == "Streak: 0   Math: 0"
