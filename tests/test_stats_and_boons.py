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
    for floor in (1, 8, 20, 40, 100):
        p.deepest_floor_reached = floor
        caps.append(p.cooking_stat_softcap())
    # 3 + depth/4 (BALANCE_REVIEW_LOOT_AND_FOOD_2026_10_26 F3; was 2 + depth/5)
    assert caps == [3, 5, 8, 13, 28]
    assert p.cooking_stat_softcap('WIS') == 14            # Wisdom keeps half


# -------------------------------------------------- you are what you eat

def test_every_stat_has_parts_that_teach_it():
    """The kitchen rebuild (2026-11-14): a part's nature says what it is rich
    in; the Stat parts name their stat, and every stat can be cooked for."""
    with open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8') as f:
        raw = json.load(f)
    stats = {}
    for k, v in raw.items():
        if v.get('nature') == 'stat':
            assert v.get('stat_grant') in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'), k
            stats[v['stat_grant']] = stats.get(v['stat_grant'], 0) + 1
    assert len(stats) == 6 and min(stats.values()) >= 10, stats


def test_two_floors_of_a_stat_dish_make_one_point():
    import kitchen
    p = Player()
    p.deepest_floor_reached = 12
    recipe = kitchen.recipe('cook_cobra')         # Cobra Tail Steak with Lime: DEX
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
    assert 27 <= p.cooking_stat_gained['STR'] <= p.cooking_stat_softcap() == 28
    q = Player()
    total = 0
    for floor in range(1, 101):
        q.deepest_floor_reached = floor
        q.reset_floor_cook_caps()
        total += q.feed_cut_stat(('STR', 'CON', 'DEX')[floor % 3])[0]
    assert 45 <= total <= 50


def test_dexterity_gives_armor_by_the_body_armours_weight_class():
    """Rewritten 2026-11-13 (winning-build plan 3.3, slice 4): Dexterity was
    worth at most 3 points of armor in anything, plate included. Now the
    body armour decides: 6 in light armour or none, 3 in medium, 0 in heavy.
    A clumsy hero's minus still counts."""
    import items
    p = Player()
    naked = p.get_ac()
    p.DEX = 16
    assert p.get_ac() == naked - 3
    p.DEX = 40
    assert p.dex_ac_cap() == 6
    assert p.get_ac() == naked - 6
    p.DEX = 6
    assert p.get_ac() == naked + 2
    p.DEX = 40
    p._apply_equip(items.instantiate_armor('chain_shirt', 'chain_steel'))
    assert p.dex_ac_cap() == 3
    q = Player()
    q.DEX = 40
    q._apply_equip(items.instantiate_armor('plate', 'chain_steel'))
    assert q.dex_ac_cap() == 0
    assert q.get_ac() == 10 - 7
    q.DEX = 6
    assert q.get_ac() == 10 - 7 + 2


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
    g._chron = lambda kind, text, **kw: g.chron.append(text)
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
    assert any('for good' in m for m in g.msgs) and g.chron
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




def test_the_recipes_menu_path_teaches_the_dishs_stat():
    """The Recipes menu cooks through cook_compound_recipe: a Stat dish
    teaches its stat there (the stamp was once set only in a path nothing
    called, so in play no meal fed a stat), and the menu line names it."""
    import kitchen

    class Quiz:                                   # answers the one cooking question right
        def start_quiz(self, **kw):
            kw['callback'](types.SimpleNamespace(success=True))

    p = Player()
    p.deepest_floor_reached = 10
    dish = kitchen.recipe('cook_wolf_pack_leader')   # Pack Leader Steak: STR
    got = []
    food_system.cook_compound_recipe(p, dish, p.inventory, Quiz(), got.extend)
    assert p.cook_stat_meals.get('STR') == 1
    assert any('Strength: 1 of 2 meals' in m for m in got), got
    assert kitchen.dish_effects(Player(), dish)[0] == 'Teaches STR (half a point)'
