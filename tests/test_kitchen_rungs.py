"""The kitchen's two low rungs (Brandon, 2026-11-22: "I have to lug around all
these ingredients with no way to use them (rations, bread, cheese)... there
should be more recipes that use these ONLY... as well as monster recipes that
are just ONE step above a single monster ingredient").

* plain fare: any two of the nine staples make a dish, and a few threes and
  fours; it feeds, heals a little, gives mana or a small power, and never a
  stat or max HP (a creature's part is what builds a hero);
* one step up: every creature's part has a dish of that part and one staple.

Data gates, the numbers (src/kitchen.py over cooking_rules.json ``rungs``), and
real keys on a headless Game. Whether the piles feel gone is a play-test
question: Claude cannot drive Pygame.
"""
import copy
import itertools
import os
import sys
import types
from collections import Counter

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import kitchen  # noqa: E402

pygame.init()

STAPLES = ('bread_ration', 'dried_meat', 'hard_cheese', 'apple', 'trail_rations',
           'wild_mushroom', 'healing_herb', 'elvish_bread', 'hearty_stew')
# What floors 41 and deeper really drop (food.json floor_spawn_weight).
DEEP = ('elvish_bread', 'wild_mushroom', 'hearty_stew', 'healing_herb', 'dried_meat',
        'trail_rations')
EATEN_FOR_A_STAT = ('philosopher_tea', 'deep_fungi', 'void_ration')


def _rung(name):
    return [r for r in kitchen.book() if r.get('rung') == name]


def _dish_of(*ps):
    return next((r for r in kitchen.book() if set(kitchen.parts(r)) == set(ps)), None)


def _primes():
    return [k for k, v in kitchen.ingredients().items() if v['tier_role'] == 'prime']


class _Hero:
    hp, max_hp, sp, max_sp, mp, max_mp = 20, 100, 40, 1000, 3, 40
    PER_FLOOR_HP_CAP = 5


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('a,b', list(itertools.combinations(STAPLES, 2)))
def test_any_two_staples_make_a_dish(a, b):
    rec = _dish_of(a, b)
    assert rec is not None and rec.get('rung') == 'plain', (a, b)
    assert kitchen.can_cook(rec, Counter({a: 1, b: 1}))


def test_his_bread_cheese_and_dried_meat():
    rec = _dish_of('bread_ration', 'hard_cheese', 'dried_meat')
    assert rec is not None and rec.get('rung') == 'plain'


def test_plain_fare_is_staples_and_forage_and_never_teaches():
    rows = _rung('plain')
    assert Counter(kitchen.dish_size(r) for r in rows)[3] >= 4
    assert Counter(kitchen.dish_size(r) for r in rows)[4] >= 3
    for r in rows:
        ps = kitchen.parts(r)
        assert all(p in STAPLES or kitchen.part_kind(p) == 'forage' for p in ps), r['id']
        assert any(p in STAPLES for p in ps), r['id']
        assert kitchen.dish_tab(r) in ('hp', 'sp', 'mp', 'special'), r['id']
        assert not r.get('legendary') and not r.get('makes'), r['id']
    assert {kitchen.dish_tab(r) for r in rows} == {'hp', 'sp', 'mp', 'special'}


def test_every_creature_part_has_a_dish_with_one_staple():
    short = []
    for p in _primes():
        if not any(kitchen.dish_size(r) == 2 and set(kitchen.parts(r)) - {p} <= set(STAPLES)
                   for r in kitchen.dishes_with(p)):
            short.append(p)
    assert not short, (len(short), short[:10])


def test_a_step_is_one_part_and_one_staple_found_where_the_part_is():
    rows = _rung('step')
    assert rows
    for r in rows:
        part, staple = kitchen.parts(r)
        assert kitchen.part_kind(part) == 'monster' and staple in STAPLES, r['id']
        band = kitchen.band_of(kitchen.part_floor(part))
        assert kitchen.band_of(kitchen.part_floor(staple)) <= band, r['id']
        if band >= 4:
            assert staple in DEEP, (r['id'], staple)
        assert kitchen.dish_tier(r) == band, r['id']


def test_a_step_keeps_the_parts_nature_unless_that_is_a_lesson_or_a_full_belly():
    for r in _rung('step'):
        ing = kitchen.ingredients()[kitchen.parts(r)[0]]
        if ing['nature'] in ('stat', 'sp'):
            assert kitchen.dish_tab(r) != 'stat', r['id']       # lesson alone, meal with a staple
        elif ing['nature'] == 'special':
            assert r['benefit'] == ing['temp_power'], r['id']
        else:
            assert r['benefit'] == ing['nature'], r['id']


def test_every_staple_has_work_at_every_depth_it_is_found():
    uses = Counter()
    for r in _rung('step'):
        part, staple = kitchen.parts(r)
        uses[(staple, kitchen.band_of(kitchen.part_floor(part)))] += 1
    for staple in STAPLES:
        bands = range(1, 6) if staple in DEEP else range(1, 3)
        for band in bands:
            assert uses[(staple, band)] >= 2, (staple, band, uses[(staple, band)])


def test_food_eaten_for_a_stat_is_left_out():
    for r in _rung('plain') + _rung('step'):
        assert not set(kitchen.parts(r)) & set(EATEN_FOR_A_STAT), r['id']


def test_the_stew_goes_into_these_two_rungs_only():
    for r in kitchen.dishes_with('hearty_stew'):
        assert r.get('rung') in ('plain', 'step'), r['id']


def test_each_new_dish_shows_its_own_kind_of_dish():
    """Item art is the item: a sandwich never shows a roast."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))
    import dish_art
    for r in _rung('plain') + _rung('step'):
        want = dish_art.art_id(dish_art.dish_kind(r['name']), kitchen.dish_tier(r),
                               kitchen.dish_tab(r))
        assert r['art'] == want, (r['id'], r['name'])


def test_the_builder_rebuilds_the_rungs_as_shipped():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))
    import build_kitchen
    built = build_kitchen.rung_recipes()
    shipped = {r['id']: {k: v for k, v in r.items() if k != 'id'}
               for r in kitchen.book() if r.get('rung')}
    assert built == shipped


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------

def test_plain_fare_gives_no_max_hp_and_says_so():
    for r in _rung('plain'):
        assert kitchen.dish_outcome(r)['max_hp'] == 0, r['id']
        lines = kitchen.dish_effects(_Hero(), r)
        assert kitchen.PLAIN_NO_MAX_HP in lines, (r['id'], lines)
        assert kitchen.MAX_HP_FULL_FLOOR not in lines, r['id']
        assert not any(ln.startswith('+') and ln.endswith('Max HP') for ln in lines), r['id']


def test_cooking_never_gives_less_than_eating_it_raw():
    more = kitchen.rules()['rungs']['cooked_over_raw']
    assert more >= 1.25
    for r in _rung('plain') + _rung('step'):
        ps = kitchen.parts(r)
        raw_sp = sum(int((kitchen.foods().get(p) or {}).get('sp_restore', 0))
                     + int((kitchen.ingredients().get(p) or {}).get('raw_sp', 0)) for p in ps)
        raw_hp = sum(int((kitchen.foods().get(p) or {}).get('hp_restore', 0)) for p in ps)
        out = kitchen.dish_outcome(r)
        assert out['sp'] >= raw_sp * more - 0.51, r['id']
        assert kitchen.heal_amount(_Hero(), out) >= raw_hp * more - 0.51, r['id']


def test_the_rungs_climb():
    """Two staples < the part alone < the part and a staple < two parts."""
    def factor(r):
        return kitchen.dish_outcome(r)['factor']
    two = [r for r in _rung('plain') if kitchen.dish_size(r) == 2
           and all(p in STAPLES for p in kitchen.parts(r))]
    single = kitchen.single_dish_for('cave_bear_prime')
    step = [r for r in _rung('step')]
    pairs = [r for r in kitchen.book() if not r.get('rung') and kitchen.dish_size(r) == 2
             and all(kitchen.part_kind(p) == 'monster' for p in kitchen.parts(r))]
    assert max(map(factor, two)) < factor(single) < min(map(factor, step))
    assert max(map(factor, step)) < min(map(factor, pairs))
    threes = [r for r in _rung('plain') if kitchen.dish_size(r) == 3]
    assert max(map(factor, two)) < max(map(factor, threes)) < min(map(factor, step))
    assert max(map(factor, _rung('plain'))) <= min(map(factor, step))


def test_plain_fare_is_no_free_health():
    """Without a harvest: at most a small heal from two staples, and none
    beyond the foods' own from a dish that is not for health."""
    for r in _rung('plain'):
        out = kitchen.dish_outcome(r)
        if kitchen.dish_tab(r) == 'hp':
            assert out['heal_share'] < 0.5, r['id']
            if kitchen.dish_size(r) == 2:
                assert out['heal_share'] < 0.18, r['id']       # under a tier-1 part's own dish
        else:
            raw_hp = kitchen.raw_gives(r)[1]
            more = kitchen.rules()['rungs']['cooked_over_raw']
            assert kitchen.heal_amount(_Hero(), out) <= raw_hp * more + 1, r['id']


def test_plain_fare_is_listed_after_every_dish_that_builds():
    p = _Hero()
    others = [kitchen.dish_value(p, r) for r in kitchen.book()
              if not r.get('rung') == 'plain' and not r.get('makes') and not r.get('song')]
    assert max(kitchen.dish_value(p, r) for r in _rung('plain')) < min(others)


def test_a_ruined_plain_dish_is_still_only_its_share():
    rec = _dish_of('bread_ration', 'hard_cheese')
    got = {}
    p = types.SimpleNamespace(max_hp=100, max_mp=0,
                              restore_sp=lambda n: got.update(sp=n), restore_hp=lambda n: n,
                              restore_mp=lambda n: None)
    kitchen.salvage_dish(p, rec)
    assert 0 < got['sp'] < kitchen.dish_outcome(rec)['sp']


# ---------------------------------------------------------------------------
# The Widow's Jar stays as hard as it was
# ---------------------------------------------------------------------------

def test_simple_dishes_do_not_fill_the_widows_jar():
    from quirk_system import QuirkSystem
    from player import Player
    pl = Player()
    q = QuirkSystem(types.SimpleNamespace(player=pl, add_message=lambda *a, **k: None))
    for _ in range(12):
        q.on_food_eaten(1, '', 'sp', 'bread_ration', parts=('bread_ration', 'hard_cheese'),
                        rung='plain')
        q.on_food_eaten(1, 'goblin', 'hp', 'goblin_prime', parts=('goblin_prime', 'hard_cheese'),
                        rung='step')
    assert not q.is_unlocked('widows_jar')


# ---------------------------------------------------------------------------
# Real keys
# ---------------------------------------------------------------------------

def _game(size=(1280, 720)):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode(size), player_name='__test_kitchen_rungs__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _pack(g, *ids):
    from items import Food, Ingredient, load_items
    from food_system import load_ingredient_for
    g.player.inventory = [i for i in g.player.inventory if not isinstance(i, (Food, Ingredient))]
    foods = {f.id: f for f in load_items('food')}
    for iid in ids:
        it = load_ingredient_for(iid) or copy.copy(foods[iid])
        it.count = 1
        g.player.inventory.append(it)


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _cook(g, rec):
    _press(g, pygame.K_c, 'c')
    for _ in range(len(kitchen.MENU_TABS)):
        if g._cook_tab_slug() == kitchen.dish_tab(rec):
            break
        _press(g, pygame.K_RIGHT)
    ids = [r['id'] for r in g._cook_tab_rows()]
    for _ in range(ids.index(rec['id'])):
        _press(g, pygame.K_DOWN)
    g.render()
    _press(g, pygame.K_RETURN)


def _right_answers(g):
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](
        types.SimpleNamespace(success=True, score=1))


def test_keys_bread_cheese_and_dried_meat_cook_with_nothing_harvested():
    g = _game()
    _pack(g, 'bread_ration', 'hard_cheese', 'dried_meat')
    _right_answers(g)
    p = g.player
    p.hp, p.sp = max(1, p.max_hp // 3), 10
    hp, max_hp = p.hp, p.max_hp
    rec = _dish_of('bread_ration', 'hard_cheese', 'dried_meat')
    _cook(g, rec)
    held = kitchen.held_counts(p.inventory)
    assert not any(held[k] for k in ('bread_ration', 'hard_cheese', 'dried_meat'))
    assert p.sp > 10 and p.max_hp == max_hp
    if kitchen.dish_tab(rec) == 'hp':
        assert p.hp > hp
        assert any(kitchen.PLAIN_NO_MAX_HP_MSG in str(e[0]) for e in g.msg_log.entries[-8:])


def test_keys_a_part_and_a_staple_one_step_up():
    g = _game()
    _right_answers(g)
    rec = next(r for r in _rung('step') if kitchen.dish_tab(r) == 'hp'
               and kitchen.dish_tier(r) == 1)
    _pack(g, *kitchen.parts(rec))
    p = g.player
    p.hp = max(1, p.max_hp // 4)
    hp, max_hp = p.hp, p.max_hp
    _cook(g, rec)
    assert p.hp > hp and p.max_hp > max_hp
    assert not any(kitchen.held_counts(p.inventory)[k] for k in kitchen.parts(rec))


# ---------------------------------------------------------------------------
# Reflex Ward (the monster-effects proposal Brandon approved 2026-11-22: "All
# as recommended"; Slowed's answers are boots, DEX and a Reflex Ward dish)
# ---------------------------------------------------------------------------

def _reflex():
    return [r for r in kitchen.book() if kitchen.dish_power(r) == 'save_guard_DEX']


@pytest.mark.parametrize('tier', range(1, 6))
def test_a_reflex_ward_dish_in_every_tier_that_a_run_can_cook(tier):
    import json
    with open(os.path.join(ROOT, 'tools', 'content', 'kitchen', 'part_freq.json'),
              encoding='utf-8') as f:
        freq = json.load(f)
    common = freq['rules']['common_share']
    assert any(all(p in STAPLES or freq['parts'][p]['share_of_runs'] >= common
                   for p in kitchen.parts(r))
               for r in _reflex() if kitchen.dish_tier(r) == tier), tier


def test_reflex_ward_can_be_cooked_by_floor_three():
    """Slowing starts on floor 1: staples alone, all found by floor 3."""
    assert any(all(p in STAPLES and kitchen.part_floor(p) <= 3 for p in kitchen.parts(r))
               for r in _reflex())


def test_every_power_in_the_rules_has_a_dish():
    have = {kitchen.dish_power(r) for r in kitchen.book()}
    assert not set(kitchen.rules()['special']['powers']) - have


def test_the_census_holds_reflex_ward_to_every_tier():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    import tier_census
    row = {r['category']: r for r in tier_census.census()['rows']}['Dishes: Reflex Ward']
    assert row['verdict'] == 'ok' and min(row['counts']) >= 1, row


def test_reflex_ward_dish_raises_the_save_against_slowing():
    from player import Player
    import status_effects
    rec = next(r for r in _reflex() if r.get('rung') == 'plain')
    assert status_effects.EFFECT_INFO['save_guard_DEX'][0] == 'Reflex Ward'
    p = Player()
    before = p.save_bonus_for('DEX')
    kitchen.apply_dish(p, rec)
    assert p.status_effects.get('save_guard_DEX', 0) > 0
    assert p.save_bonus_for('DEX') > before


# ---------------------------------------------------------------------------
# A step never takes the floor's stat lesson unsaid (the 2026-11-22 measure:
# the committed build lost it on about one floor in fifteen)
# ---------------------------------------------------------------------------

def _stat_step():
    return next(r for r in _rung('step') if kitchen.dish_tier(r) == 1
                and kitchen.ingredients()[kitchen.parts(r)[0]]['nature'] == 'stat')


def test_a_step_that_would_spend_the_lesson_says_so_and_is_listed_last():
    from player import Player
    rec = _stat_step()
    part, staple = kitchen.parts(rec)
    stat = kitchen.dish_stat(kitchen.single_dish_for(part))
    p = Player()
    one = Counter({part: 1, staple: 1})
    assert kitchen.lesson_spent(p, rec, one) == stat
    assert kitchen.lesson_line(p, rec, one) == \
        f"Cooked alone, {kitchen.part_name(part)} teaches {stat} +1"
    assert kitchen.lesson_spent(p, rec, Counter({part: 2, staple: 1})) is None      # a spare
    assert p.feed_cut_stat(stat, 1) > 0
    assert kitchen.lesson_spent(p, rec, one) is None                  # the lesson is used


def test_keys_the_cook_menu_lists_it_last_and_says_why():
    rec = _stat_step()
    part, staple = kitchen.parts(rec)
    g = _game()
    other = next(s for s in ('bread_ration', 'hard_cheese', 'dried_meat', 'apple', 'trail_rations')
                 if s != staple)
    _pack(g, part, staple, other, 'cave_bear_prime', 'imp_prime', 'fire_beetle_prime', 'goblin_prime')
    _press(g, pygame.K_c, 'c')
    rows = [r for r in g._cook_tab_rows(kitchen.dish_tab(rec)) if r['ready']]
    assert rows[-1]['id'] == rec['id'], [r['id'] for r in rows]
    assert rows[-1]['lesson'] == kitchen.lesson_line(g.player, rec, g._cook_counts)
    while g._cook_tab_slug() != kitchen.dish_tab(rec):
        _press(g, pygame.K_RIGHT)
    g._cook_sel = len(rows) - 1
    g.render()
