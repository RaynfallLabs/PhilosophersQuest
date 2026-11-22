"""Brandon's rulings on the 3.6.0 bug bash, group D (2026-11-22: "All as
recommended").

  D4   only packmates that can act count for a swarm's bonus
  D5   hero specials, the Wish and Restore Body heal through disease;
       lifesteal and the paid physicians are as they were
  D10  a sealed smoke vent shows no smoke on the map

Logic tests on a headless Game. How the sealed vent looks in play is a
play-test's to judge.
"""
from __future__ import annotations

import os
import random
import types

import pygame
import pytest

from test_bugbash_360_monsters import _msgs, _scene

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


# ------------------------------------------------------------------------ D4

def _swarm():
    g = _scene(('giant_rat', 1, 0), ('giant_rat', -1, 0), ('giant_rat', 0, 1))
    return g, g.monsters


def _mult(g, m):
    import packs
    return packs.blow_mult(m, g.player, m.attacks[0], g.monsters)[0]


def test_d4_mates_that_can_act_still_count():
    g, (rat, _a, _b) = _swarm()
    assert _mult(g, rat) > 1.5


@pytest.mark.parametrize('state', ['sleeping', 'paralyzed', 'stunned', 'frozen'])
def test_d4_a_mate_that_cannot_act_does_not(state):
    g, (rat, a, b) = _swarm()
    both = _mult(g, rat)
    a.status_effects[state] = 5
    one = _mult(g, rat)
    b.status_effects[state] = 5
    assert both > one > 1.0 and _mult(g, rat) == 1.0


# ------------------------------------------------------------------------ D5

def _sick(hp=100):
    g = _scene()
    p = g.player
    p.max_hp, p.hp = 1000, hp
    p.status_effects['diseased'] = 50
    return g, p


def test_d5_restore_body_heals_half_through_disease():
    g, p = _sick()
    g._apply_wand_effect(types.SimpleNamespace(effect='restore_body', power='', quiz_tier=5,
                                               id='wand_of_test', name='wand', buc='uncursed'))
    assert p.hp == 100 + 450
    assert p.sp == p.max_sp and p.mp == p.max_mp
    said = ' '.join(_msgs(g, 4))
    assert 'Diseased' in said and 'fully restored' not in said


def test_d5_a_well_hero_is_still_restored_whole():
    g, p = _sick()
    p.status_effects.pop('diseased')
    g._apply_wand_effect(types.SimpleNamespace(effect='restore_body', power='', quiz_tier=5,
                                               id='wand_of_test', name='wand', buc='uncursed'))
    assert p.hp == p.max_hp and 'fully restored' in ' '.join(_msgs(g, 4))


def test_d5_the_wish_heals_through_disease(monkeypatch):
    from spells import LEARNABLE_SPELLS
    g, p = _sick()
    wish = next(s for s in LEARNABLE_SPELLS.values() if s.get('effect') == 'wish')
    monkeypatch.setattr(random, 'choice', lambda seq: next(
        (o for o in seq if isinstance(o, tuple) and o[0] == 'full_restore'), seq[0]))
    g._mm_acting(g._cast_spell_effect, wish, None)
    assert p.hp == 100 + 450
    assert 'utterly whole' not in ' '.join(_msgs(g, 4))


SPECIALS = ['heal_and_crit_buff', 'aoe_heal_self']


@pytest.mark.parametrize('effect', SPECIALS)
def test_d5_a_hero_special_heals_through_disease(effect, monkeypatch):
    import hero_specials
    import floor_curve
    monkeypatch.setattr(floor_curve, 'mend', lambda *a, **k: 200)
    fn = getattr(hero_specials, f'_eff_{effect}')
    g, p = _sick()
    tier = {'heal': 20, 'self_heal': 20, 'crit_turns': 2, 'cleanse': 0}
    fn(g, {'id': 'test', 'name': 'test'}, tier, 3)
    assert p.hp == 100 + 100
    assert any('100' in t for t in _msgs(g, 3))


@pytest.mark.parametrize('effect', SPECIALS)
def test_d5_a_closed_wound_says_so(effect, monkeypatch):
    import hero_specials
    import floor_curve
    monkeypatch.setattr(floor_curve, 'mend', lambda *a, **k: 200)
    g, p = _sick()
    p.status_effects['heal_blocked'] = 5
    tier = {'heal': 20, 'self_heal': 20, 'crit_turns': 2, 'cleanse': 0}
    getattr(hero_specials, f'_eff_{effect}')(g, {'id': 'test', 'name': 'test'}, tier, 3)
    assert p.hp == 100 and 'refuse to close' in ' '.join(_msgs(g, 3))


# ----------------------------------------------------------------------- D10

ART = os.path.join(ROOT, 'assets', 'tiles', 'env', 'fixtures')


def test_d10_the_sealed_vent_has_a_picture_of_its_own_with_no_smoke():
    shut = pygame.image.load(os.path.join(ART, 'smoke_vent_sealed.png'))
    smoking = pygame.image.load(os.path.join(ART, 'smoke_vent.png'))
    assert shut.get_size() == smoking.get_size()

    def clear(img, rows):
        return all(img.get_at((x, y))[3] < 40 for y in rows for x in range(img.get_width()))

    assert not clear(smoking, range(0, 28)), 'the smoking vent smokes'
    assert clear(shut, range(0, 28)), 'no smoke rises from the shut one'
    assert not clear(shut, range(28, shut.get_height())), 'the crack is still there'


@pytest.mark.parametrize('sealed', [False, True])
def test_d10_the_map_draws_it(sealed, monkeypatch):
    import decor
    g = _scene()
    pos = (g.player.x + 2, g.player.y)
    decor.place(g.dungeon, pos, 'smoke_vent')
    g.dungeon.__dict__.setdefault('fixture_state', {})[pos] = 'spent'     # spoken over
    if sealed:
        g._lore_reward_seal_vent(pos, 'smoke_vent')
    monkeypatch.setattr(g.renderer, '_onscreen_tile_range', lambda w, h: (0, 0, w, h))
    drawn = []
    monkeypatch.setattr(g.renderer, '_get_env_sprite', lambda name: drawn.append(name))
    g.renderer._draw_fixtures(g.dungeon, {pos}, pygame.Surface((4, 4)))
    assert drawn[0] == ('fixtures/smoke_vent_sealed' if sealed else 'fixtures/smoke_vent')


def test_d10_the_spent_dimming_does_not_hide_the_stopped_crack(monkeypatch):
    import decor
    g = _scene()
    pos = (g.player.x + 2, g.player.y)
    decor.place(g.dungeon, pos, 'smoke_vent')
    g._lore_reward_seal_vent(pos, 'smoke_vent')
    g.dungeon.__dict__.setdefault('fixture_state', {})[pos] = 'spent'
    r = g.renderer
    picture, dim = pygame.Surface((4, 4)), pygame.Surface((4, 4))
    blits = []
    monkeypatch.setattr(r, '_get_env_sprite', lambda name: picture)
    monkeypatch.setattr(r, '_onscreen_tile_range', lambda w, h: (0, 0, w, h))
    monkeypatch.setattr(r, 'screen', types.SimpleNamespace(blit=lambda s, *a, **k: blits.append(s)))
    r._draw_fixtures(g.dungeon, {pos}, dim)
    assert picture in blits and dim not in blits
