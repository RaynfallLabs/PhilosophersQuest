"""Bug bash 2026-10-16 (F5): player-facing text and badges.

CQ-07  the Cook menu's TROPHY badge keyed on `recipe_class`, a field that
       left recipes.json in v2.6.4, so none of the 30 trophy recipes was
       ever badged. Since the kitchen rebuild (2026-11-14, K2) the 14
       trophy dishes and the legendary feasts sit in the gold Legendary
       Feasts section, each row in a gold frame, and say what they are.
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
    import kitchen
    return (kitchen.recipe('trophy_fafnir_dragon_recipe'), kitchen.recipe('feast_05'),
            kitchen.recipe('cook_goblin'))


# ── CQ-07 ────────────────────────────────────────────────────────────────────

def test_trophy_and_legendary_recipes_are_recognised():
    from food_system import _raw_recipes, recipe_is_trophy
    flagged = [rid for rid, r in _raw_recipes().items() if recipe_is_trophy({'id': rid, **r})]
    assert len([r for r in flagged if r.startswith('trophy_')]) == 14
    assert len(flagged) == 14 + sum(1 for r in _raw_recipes().values() if r.get('legendary'))


def test_cook_menu_marks_trophy_and_legendary_dishes(monkeypatch):
    import kitchen
    import cook_menu
    from main import Game
    from fantasy_ui import KT
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_cq07__')
    trophy, feast, plain = _recipes()
    counts = kitchen.held_counts([])
    rows = [kitchen._row(g.player, r, counts) for r in (trophy, feast, plain)]
    assert [r['group'] for r in rows] == ['legendary', 'legendary', 'building']
    assert cook_menu.status_line(rows[0]).startswith('Trophy Dish')
    assert cook_menu.status_line(rows[1]).startswith('Legendary Feast')
    assert cook_menu.status_line(rows[2]).startswith('Building Toward')
    frames = []
    real = pygame.draw.rect

    def spy(surf, color, rect, width=0, *a, **k):
        if width == 2:
            frames.append(tuple(color)[:3])
        return real(surf, color, rect, width, *a, **k)
    monkeypatch.setattr(pygame.draw, 'rect', spy)
    words = ('2 of 5', 60, ['A Dish'], ['Needs: a part'], pygame.font.Font(None, 20))
    for row in rows:
        frames.clear()
        g._cook_draw_row(pygame.Rect(10, 10, 400, 60), row, words, False, 'hp')
        gold = tuple(KT.GOLD) in frames
        assert gold == (row['group'] == 'legendary'), row['id']


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
