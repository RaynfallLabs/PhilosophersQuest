"""Bug bash 2026-10-16 (F5): player-facing text and badges.

CQ-07  the Cook menu's TROPHY badge keyed on `recipe_class`, a field that
       left recipes.json in v2.6.4, so none of the 30 trophy recipes was
       ever badged.
CQ-10  Nidhoggr's trophy said "permanent poison immunity"; the effect it
       grants (poison_resist) stops poisoning and halves poison damage.
CQ-11  three quirks (and the Blessed status) promised "all quiz timers
       run 25% longer"; only combat (maths) questions are timed.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame

pygame.init()


def _recipes():
    from food_system import _raw_recipes, _load_outcomes
    outcomes = _load_outcomes()
    trophy = plain = None
    for rid, r in _raw_recipes().items():
        o = outcomes.get(r.get('outcome_id')) or {}
        if o.get('permanent_power') and trophy is None:
            trophy = {'id': rid, **r}
        elif not o.get('permanent_power') and plain is None:
            plain = {'id': rid, **r}
    return trophy, plain


# ── CQ-07 ────────────────────────────────────────────────────────────────────

def test_thirty_trophy_recipes_are_recognised():
    from food_system import _raw_recipes, recipe_is_trophy
    n = sum(1 for rid, r in _raw_recipes().items()
            if recipe_is_trophy({'id': rid, **r}))
    assert n == 30


def test_cook_menu_badges_trophy_recipes(monkeypatch):
    from main import Game
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_cq07__')
    trophy, plain = _recipes()
    assert trophy and plain
    g.cook_compound_recipes = [trophy, plain]
    seen = {}
    monkeypatch.setattr(g, '_draw_decision_menu',
                        lambda **kw: seen.update(kw), raising=False)
    g._draw_cook_menu()
    entries = seen['entries']
    assert entries[0]['badge'] == 'TROPHY'
    assert entries[1]['badge'] == ''
    assert entries[0]['name_color'] != entries[1]['name_color']


# ── CQ-10 ────────────────────────────────────────────────────────────────────

def test_nidhoggr_trophy_says_resistance_not_immunity():
    from food_system import _apply_permanent_power
    from player import Player
    from status_effects import EFFECT_INFO
    p = Player()
    msg = _apply_permanent_power(
        p, 'max_mp_per_floor_descent_and_poison_immunity', {})
    assert p.has_effect('poison_resist')
    assert 'immun' not in msg.lower()
    assert 'half damage' in msg
    # the effect's own description agrees with the message
    assert 'halves poison damage' in EFFECT_INFO['poison_resist'][2]


# ── CQ-11 ────────────────────────────────────────────────────────────────────

def test_quirk_text_does_not_promise_untimed_quizzes_get_longer():
    from quirk_text import QUIRK_DESC
    from status_effects import EFFECT_INFO
    for qid, text in QUIRK_DESC.items():
        low = text.lower()
        assert 'all quiz timers' not in low and 'your quiz timers' not in low, qid
    for qid in ('philosophers_stone', 'eye_storm', 'sage_counsel'):
        assert 'combat (maths) quiz timer runs 25% longer' in QUIRK_DESC[qid]
    assert 'all quiz' not in EFFECT_INFO['blessed'][2].lower()


def test_only_combat_maths_is_timed():
    """The premise of the CQ-11 wording: the engine times maths only."""
    from quiz_engine import QuizEngine
    for subject, timed in (('math', True), ('cooking', False),
                           ('history', False), ('theology', False)):
        qe = QuizEngine()
        qe.start_quiz(mode='threshold', subject=subject, tier=1,
                      callback=lambda r: None, threshold=1, total_qs=1,
                      base_seconds=16)
        assert qe.timed is timed, subject
