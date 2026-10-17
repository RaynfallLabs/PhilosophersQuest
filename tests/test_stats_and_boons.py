"""Stat design, step one (2026-10): what Constitution and Dexterity do, the
stat a cooked cut raises, and the gift a gate boss leaves.

Logic tests. The gift menu's look and the feel of a dodge need play.
"""
import json
import os
import pickle
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import boons  # noqa: E402
import food_system  # noqa: E402
import game_combat  # noqa: E402
from game_states import STATE_BOON_MENU, STATE_PLAYER  # noqa: E402
from player import Player  # noqa: E402

GATES = ('asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf')


def _boon_data():
    with open(os.path.join(ROOT, 'data', 'boss_boons.json'), encoding='utf-8') as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith('_')}


# ---------------------------------------------------------------- the stats

def test_constitution_is_worth_three_hit_points_and_some_toughness():
    p = Player()
    base = p.max_hp
    p.apply_stat_bonus('CON', 5)
    assert p.max_hp == base + 5 * p.HP_PER_CON and p.HP_PER_CON == 3
    assert abs(p.toughness() - 0.05) < 1e-9
    p.hp = p.max_hp
    took = p.take_damage(100, 'physical')
    assert took == 95
    p.CON = 200
    assert p.toughness() == p.TOUGHNESS_CAP <= 0.40
    q = Player()
    q.CON = 6
    assert q.toughness() == 0.0                       # a weak body is not a penalty


def test_toughness_does_not_slow_starvation():
    p = Player()
    p.CON = 40
    p.max_hp = p.hp = 500
    assert p.take_damage(10, 'starvation') == 10


def test_dexterity_dodges_and_a_held_body_cannot():
    p = Player()
    assert p.dodge_chance() == 0.0
    p.DEX = 20
    assert abs(p.dodge_chance() - 0.075) < 1e-9
    p.DEX = 300
    assert p.dodge_chance() == p.DODGE_CAP <= 0.30
    p.add_effect('paralyzed', 3)
    assert p.dodge_chance() == 0.0


def test_the_cooking_cap_for_one_stat_grows_with_depth():
    p = Player()
    caps = []
    for floor in (1, 20, 40, 100):
        p.deepest_floor_reached = floor
        caps.append(p.cooking_stat_softcap())
    assert caps == [2, 6, 10, 22]


# -------------------------------------------------- you are what you eat

def test_every_prime_cut_names_the_stat_it_raises():
    with open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8') as f:
        raw = json.load(f)
    primes = [k for k, v in raw.items()
              if isinstance(v, dict) and v.get('tier_role') == 'prime']
    assert len(primes) > 100
    stats = {}
    for k in primes:
        s = food_system.cut_stat(k)
        assert s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'), k
        stats[s] = stats.get(s, 0) + 1
    assert len(stats) == 6, stats                     # every stat can be cooked for
    assert food_system.cut_stat('no_such_ingredient') is None


def test_two_floors_of_a_cut_make_one_point():
    cut = next(k for k in food_system._cut_stat_cache if food_system.cut_stat(k) == 'DEX')
    p = Player()
    p.deepest_floor_reached = 12
    oid = next(k for k, v in food_system._load_outcomes().items()
               if isinstance(v, dict) and not v.get('stat_grant')
               and not v.get('permanent_power'))
    recipe = {'name': 'Test Roast', '_cut_stat': food_system.cut_stat(cut),
              'outcome_id': oid}
    before = p.DEX
    msgs = food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before and any('1 of 2 meals' in m for m in msgs)
    food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before and p.cook_stat_meals['DEX'] == 1     # one lesson a floor
    p.reset_floor_cook_caps()
    food_system._apply_recipe_outcome(p, recipe, ruined=True)
    assert p.DEX == before                                      # a ruined meal teaches nothing
    msgs = food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before + 1 and any('increases' in m for m in msgs)
    assert p.cooking_stat_gained['DEX'] == 1 and p.cook_stat_meals['DEX'] == 0


def test_a_whole_run_of_cooking_is_about_fifty_points_and_one_speciality():
    p = Player()
    for floor in range(1, 101):
        p.deepest_floor_reached = floor
        p.reset_floor_cook_caps()
        p.feed_cut_stat('STR')
        p.feed_cut_stat('STR')
    assert 21 <= p.cooking_stat_gained['STR'] <= p.cooking_stat_softcap() == 22
    q = Player()
    total = 0
    for floor in range(1, 101):
        q.deepest_floor_reached = floor
        q.reset_floor_cook_caps()
        total += q.feed_cut_stat(('STR', 'CON', 'DEX')[floor % 3])[0]
    assert 45 <= total <= 50


def test_dexterity_gives_three_points_of_armor_at_most():
    p = Player()
    naked = p.get_ac()
    p.DEX = 16
    assert p.get_ac() == naked - 3
    p.DEX = 40
    assert p.get_ac() == naked - p.DEX_AC_CAP == naked - 3
    p.DEX = 6
    assert p.get_ac() == naked + 2


# ------------------------------------------------------------ gate-boss gifts

def test_each_gate_offers_three_gifts_and_each_stat_twice():
    data = _boon_data()
    assert set(data) == set(GATES)
    seen = {}
    last = 0
    for kind in GATES:
        gifts = data[kind]['gifts']
        assert len(gifts) == 3 and len({g['stat'] for g in gifts}) == 3
        assert len({g['id'] for g in gifts}) == 3
        for g in gifts:
            seen[g['stat']] = seen.get(g['stat'], 0) + 1
            assert g['name'] and g['text']
            assert g['name'] == g['name'].title() or "'" in g['name']
        physical = max(g['amount'] for g in gifts)
        assert physical > last                         # later gates give more
        last = physical
        for g in gifts:                                # Wisdom is the small one
            if g['stat'] == 'WIS':
                assert g['amount'] < physical
    assert seen == {s: 2 for s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')}


def test_taking_a_gift_is_once_and_for_good():
    p = Player()
    base_str, base_hp = p.STR, p.max_hp
    gift, amount = boons.take(p, 'asterion_minotaur', 0)
    assert gift['stat'] == 'STR' and amount == 4 and p.STR == base_str + 4
    assert boons.already_taken(p, 'asterion_minotaur')
    assert boons.take(p, 'asterion_minotaur', 1) is None
    assert boons.take(p, 'medusa_gorgon', 7) is None
    gift, amount = boons.take(p, 'medusa_gorgon', 2)
    assert gift['stat'] == 'CON' and p.max_hp == base_hp + amount * p.HP_PER_CON
    clone = pickle.loads(pickle.dumps(p))
    assert clone.boons_taken == {'asterion_minotaur': 'bulls_horn',
                                 'medusa_gorgon': 'healing_vein'}
    assert boons.offer_for('giant_rat') is None


def test_solving_the_quest_adds_one():
    p = Player()
    assert not boons.solved_quest(p, 'asterion_minotaur')
    p.inventory.append(types.SimpleNamespace(id='ariadnes_thread'))
    assert boons.solved_quest(p, 'asterion_minotaur')
    assert boons.describe(p, 'asterion_minotaur', _boon_data()['asterion_minotaur']['gifts'][0]) \
        == 'Strength +5'
    q = Player()
    q.shield = types.SimpleNamespace(id='greater_aegis_of_athena')
    assert boons.solved_quest(q, 'medusa_gorgon')
    q.struck_from_the_pit = True
    assert boons.solved_quest(q, 'fafnir_dragon')
    q._gleipnir_binds = 2
    assert boons.solved_quest(q, 'fenrir_wolf')
    assert not boons.solved_quest(Player(), 'fenrir_wolf')


def _game(player):
    g = types.SimpleNamespace(player=player, state=STATE_PLAYER, msgs=[], chron=[])
    g.add_message = lambda text, kind='info': g.msgs.append(text)
    g._log_chronicle = lambda text: g.chron.append(text)
    for name in ('_open_boon_menu', '_boon_pick'):
        setattr(g, name, types.MethodType(getattr(game_combat.CombatMixin, name), g))
    return g


def test_the_menu_opens_when_control_returns_and_closes_on_a_pick():
    p = Player()
    g = _game(p)
    assert not g._open_boon_menu()                     # nothing pending
    p.pending_boon = 'fenrir_wolf'
    g.state = 'popup'
    assert not g._open_boon_menu() and p.pending_boon  # waits for the story popup
    g.state = STATE_PLAYER
    assert g._open_boon_menu() and g.state == STATE_BOON_MENU
    g._boon_pick(9)                                    # not a gift: still choosing
    assert g.state == STATE_BOON_MENU
    dex = p.DEX
    g._boon_pick(1)
    assert g.state == STATE_PLAYER and p.DEX == dex + 7 and p.pending_boon is None
    assert any('For Good' in m for m in g.msgs) and g.chron
    p.pending_boon = 'fenrir_wolf'                     # a stale flag clears itself
    assert not g._open_boon_menu() and p.pending_boon is None


def test_the_kill_hook_the_menu_and_the_bundle_are_wired():
    def src(name):
        return open(os.path.join(ROOT, *name.split('/')), encoding='utf-8').read()
    assert 'self.player.pending_boon = monster.kind' in src('src/game_combat.py')
    assert "getattr(self.player, 'pending_boon', None)" in src('src/main.py')
    assert 'self._boon_menu_input(key)' in src('src/game_input.py')
    assert 'self._draw_boon_menu()' in src('src/game_render.py')
    assert "'data/boss_boons.json'" in src('PhilosophersQuest.spec')
    # A real belly strike from the pit is remembered; the Strike Now
    # preview (consume=False) asks the same sum and remembers nothing.
    import combat
    import items
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    wyrm = Monster(dict(defs['giant_rat'], id='giant_rat'), 1, 1)
    wyrm.dragon_scales = 0.8
    hero = Player()
    hero.weapon = items.instantiate_weapon('longsword', 'iron')
    hero.status_effects['in_pit'] = 5
    combat.strike_damage(hero, wyrm, 3)
    assert not getattr(hero, 'struck_from_the_pit', False)
    combat.strike_damage(hero, wyrm, 3, consume=True)
    assert hero.struck_from_the_pit is True


def test_the_gift_menu_draws_headless():
    import pygame
    import game_render
    import layout
    pygame.init()
    pygame.display.set_mode((1, 1))
    p = Player()
    p.inventory.append(types.SimpleNamespace(id='ariadnes_thread'))
    for kind in GATES:
        g = types.SimpleNamespace(
            player=p, _boon_kind=kind,
            screen=pygame.Surface((layout.WINDOW_W, layout.WINDOW_H)))
        game_render.RenderMixin._draw_boon_menu(g)
        assert g.screen.get_at((layout.WINDOW_W // 2, layout.WINDOW_H // 2))[:3] != (0, 0, 0) \
            or g.screen.get_bounding_rect().width > 0




def test_the_recipes_menu_path_feeds_the_cuts_stat():
    """The stamp was set only in cook_ingredient, which nothing calls: in
    play no meal ever fed a stat, and the unit test built its own recipe."""
    import items
    cut = next(k for k in (food_system.cut_stat('x') or 1, ) and food_system._cut_stat_cache
               if food_system.cut_stat(k) == 'STR')
    assert food_system.recipe_cut_stat({'ingredients': ['salt_that_is_not_a_cut', cut]}) == 'STR'
    assert food_system.recipe_cut_stat({'ingredients': []}) is None
    oid = next(k for k, v in food_system._load_outcomes().items()
               if isinstance(v, dict) and not v.get('stat_grant') and not v.get('permanent_power'))

    class Quiz:                                   # answers the one cooking question right
        def start_quiz(self, **kw):
            kw['callback'](types.SimpleNamespace(success=True))

    p = Player()
    p.deepest_floor_reached = 10
    got = []
    food_system.cook_compound_recipe(
        p, {'name': 'Test Roast', 'ingredients': [cut], 'outcome_id': oid, 'tier': 1},
        p.inventory, Quiz(), got.extend)
    assert p.cook_stat_meals.get('STR') == 1
    assert any('Strength: 1 of 2 meals' in m for m in got), got
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'bits.append(f"Feeds {fed}")' in src
