"""Wisdom from depth, wisdom lent by prayer, and the prayer menu.

Logic tests. The menu's look and the feel of the longer clock need play.
"""
import os
import pickle
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import game_divine  # noqa: E402
import prayers  # noqa: E402
from player import Player  # noqa: E402
from status_effects import tick_all  # noqa: E402
from test_prayer import _make_prayer_game  # noqa: E402


# ------------------------------------------------------------ wisdom from depth

def test_the_dungeon_teaches_one_wisdom_every_three_floors():
    p = Player()
    assert p.DEPTH_WIS_EVERY == 3
    total, was = 0, 1
    for floor in range(2, 101):
        total += p.learn_from_depth(was, floor)
        was = floor
    assert total == 33 and p.WIS == 43
    assert p.get_quiz_timer('math') == 43
    # checkpoints the balance was built on
    q = Player()
    for floor, wis in ((20, 16), (40, 23), (60, 30), (80, 36), (100, 43)):
        r = Player()
        r.learn_from_depth(1, floor)
        assert r.WIS == wis, floor
    assert q.learn_from_depth(30, 30) == 0          # no new depth, nothing
    assert q.learn_from_depth(30, 12) == 0          # going up teaches nothing


def test_depth_wisdom_is_granted_once_in_the_level_change():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert src.count('learn_from_depth(') == 1
    i = src.index('learn_from_depth(')
    assert 'deepest_floor_reached > _was_deepest' in src[i - 300:i]


# -------------------------------------------------------------- wisdom lent

def test_lent_wisdom_lengthens_the_clock_and_never_touches_the_stat():
    p = Player()
    p.WIS = 20
    p.grant_insight(12, 5)
    assert p.WIS == 20 and p.effective_wis() == 32
    assert p.get_quiz_timer('math') == 32
    p.grant_insight(6, 3)                     # a lesser gift changes nothing
    assert p.effective_wis() == 32 and p.status_effects['inspired'] == 5
    p.grant_insight(15, 2)                    # larger amount, longer time kept
    assert p.effective_wis() == 35 and p.status_effects['inspired'] == 5
    for _ in range(6):
        tick_all(p)
    assert not p.has_effect('inspired')
    assert p.insight_wis == 0 and p.WIS == 20 and p.get_quiz_timer('math') == 20


def test_lent_wisdom_survives_a_save_and_old_saves_load():
    p = Player()
    p.grant_insight(8, 9)
    q = pickle.loads(pickle.dumps(p))
    assert q.effective_wis() == p.effective_wis() == 18
    old = Player()
    del old.insight_wis                       # a save from before the field
    assert old.effective_wis() == 10 and old.get_quiz_timer('math') == 10


# --------------------------------------------------------- the prayer itself

def test_guide_my_hand_is_a_real_bonus_at_every_depth():
    """A full chain doubles the clock whatever the player's wisdom, and it is
    a burst: eight turns for a full chain, ten at an altar, never longer."""
    for wis in (10, 23, 43):
        bonus5, turns5 = prayers.guide_my_hand(wis, 5)
        assert bonus5 >= wis and turns5 == 8
        prev_bonus = prev_turns = 0
        for chain in range(1, 7):
            bonus, turns = prayers.guide_my_hand(wis, chain)
            assert bonus > prev_bonus and turns > prev_turns
            assert 3 <= turns <= 10
            prev_bonus, prev_turns = bonus, turns
    assert prayers.guide_my_hand(10, 1)[0] >= 3
    assert prayers.guide_my_hand(30, 0) == (0, 0)
    # karma bends the time by a turn at most and never takes the gift away
    assert prayers.guide_my_hand(20, 3, karma=9)[1] == prayers.guide_my_hand(20, 3)[1] + 1
    assert prayers.guide_my_hand(20, 3, karma=-10)[1] == prayers.guide_my_hand(20, 3)[1] - 1
    assert prayers.guide_my_hand(20, 3, karma=-2)[1] == prayers.guide_my_hand(20, 3)[1]
    assert prayers.guide_my_hand(20, 3, desperate=True)[1] == prayers.guide_my_hand(20, 3)[1] + 2


def test_the_menu_offers_mercy_and_michael():
    ids = [p['id'] for p in prayers.available(0)]
    assert ids[:2] == [prayers.MERCY, prayers.GUIDE_MY_HAND]
    for p in prayers.PRAYERS:
        assert p['name'] and p['asks'] and p['title']
    names = [p['name'] for p in prayers.PRAYERS]
    assert "Michael, Guide My Hand" in names


def test_praying_for_the_hand_gives_wisdom_and_not_the_heal():
    g = _make_prayer_game(karma=0, at_altar=False)
    g._answer_guide_my_hand = lambda *a: game_divine.DivineMixin._answer_guide_my_hand(g, *a)
    g.player.WIS = 20
    g.player.max_hp, g.player.hp = 100, 60
    hp0, sp0 = g.player.hp, g.player.sp
    game_divine.DivineMixin._resolve_simple_prayer(g, 5, False, kind='guide_my_hand',
                                                   hp_pct=0.6)
    assert g.player.hp == hp0 and g.player.sp == sp0      # the mercies were not asked for
    assert g.player.get_quiz_timer('math') == 40          # the clock is doubled
    assert g.player.WIS == 20
    assert g.player.prayer_cooldown == 225                # same cooldown as any prayer
    assert not g.player.has_effect('shielded')
    assert any('Wisdom +20' in t for t, _k in g.messages)


def test_a_prayer_from_the_depths_also_shields():
    g = _make_prayer_game(karma=0, at_altar=False)
    g._answer_guide_my_hand = lambda *a: game_divine.DivineMixin._answer_guide_my_hand(g, *a)
    game_divine.DivineMixin._resolve_simple_prayer(g, 2, False, kind='guide_my_hand',
                                                   hp_pct=0.2)
    assert g.player.has_effect('shielded') and g.player.has_effect('inspired')


def test_an_unanswered_prayer_lends_nothing_and_mercy_is_unchanged():
    g = _make_prayer_game(karma=0, at_altar=False)
    g._answer_guide_my_hand = lambda *a: game_divine.DivineMixin._answer_guide_my_hand(g, *a)
    game_divine.DivineMixin._resolve_simple_prayer(g, 0, False, kind='guide_my_hand')
    assert not g.player.has_effect('inspired') and g.player.prayer_cooldown > 0
    h = _make_prayer_game(karma=0, at_altar=False)
    h.player.max_hp, h.player.hp = 100, 40
    game_divine.DivineMixin._resolve_simple_prayer(h, 3, False)          # default = mercy
    assert h.player.hp > 40 and not h.player.has_effect('inspired')


def test_the_prayer_menu_draws_and_routes_keys():
    import pygame
    import game_input
    import game_render
    import layout
    pygame.init()
    screen = pygame.display.set_mode((layout.WINDOW_W, layout.WINDOW_H))
    picked = []
    g = types.SimpleNamespace(screen=screen, karma=0)
    g._prayer_choices = lambda: prayers.available(0)
    game_render.RenderMixin._draw_prayer_menu(g)           # must not raise
    g._prayer_menu_pick = picked.append
    g._prayer_menu_cancel = lambda: picked.append('cancel')
    game_input.InputMixin._prayer_menu_input(g, pygame.K_2)
    game_input.InputMixin._prayer_menu_input(g, pygame.K_ESCAPE)
    assert picked == [1, 'cancel']
