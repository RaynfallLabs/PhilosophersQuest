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
    assert abs(p.dodge_chance() - 10 * p.DODGE_PER_DEX) < 1e-9
    p.DEX = 300
    assert p.dodge_chance() == p.DODGE_CAP <= 0.40         # the defence model: near 35-40%
    p.add_effect('paralyzed', 3)
    assert p.dodge_chance() == 0.0


def test_a_stat_dishs_tier_caps_how_far_it_teaches():
    """Brandon, 2026-11-16: "putting caps on how high a given dish can raise
    a stat makes deep and complex cooking way more important... stops early
    spamming". The cap is the dish's tier, not the depth reached: the old
    depth rule's value at the bottom of each band (3 + floor / 4), so the
    deepest dishes keep its ceiling of 28, and Wisdom keeps half."""
    p = Player()
    assert [p.cooking_stat_softcap('STR', t) for t in range(1, 6)] == [8, 13, 18, 23, 28]
    assert [p.cooking_stat_softcap('WIS', t) for t in range(1, 6)] == [4, 6, 9, 11, 14]
    for t in range(1, 6):
        assert p.cooking_stat_softcap('WIS', t) == p.cooking_stat_softcap('STR', t) // 2
    p.deepest_floor_reached = 100                    # depth does not lift a dish's cap
    assert p.cooking_stat_softcap('STR', 1) == 8
    assert p.cooking_stat_softcap('STR') == 28       # no dish: the depth's band (altars)


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


def test_one_stat_dish_teaches_one_point_one_a_floor():
    """Brandon, 2026-11-16: one dish = one point, still one a floor (two
    lessons made a point, which he found hard to follow)."""
    import kitchen
    p = Player()
    p.deepest_floor_reached = 12
    recipe = kitchen.recipe('cook_cobra')         # Cobra Tail Steak with Lime: DEX
    before = p.DEX
    msgs = food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before + 1 and any('Dexterity increases by 1' in m for m in msgs)
    msgs = food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before + 1                                   # one lesson a floor
    assert any('already learned from a meal on this floor' in m for m in msgs)
    p.reset_floor_cook_caps()
    food_system._apply_recipe_outcome(p, recipe, ruined=True)
    assert p.DEX == before + 1                                   # a ruined meal teaches nothing
    food_system._apply_recipe_outcome(p, recipe, ruined=False)
    assert p.DEX == before + 2 and p.cooking_stat_gained['DEX'] == 2


def test_a_whole_run_of_cooking_needs_deep_dishes_for_a_speciality():
    """A point a floor for a hundred floors: a hero who eats only shallow
    dishes stops at their cap, one who eats deeper as he goes reaches the
    top (28), and one point a floor spread over three stats is about a
    hundred points in all."""
    import kitchen
    shallow, deep = Player(), Player()
    for floor in range(1, 101):
        for p in (shallow, deep):
            p.deepest_floor_reached = floor
            p.reset_floor_cook_caps()
        shallow.feed_cut_stat('STR', 1)
        deep.feed_cut_stat('STR', kitchen.band_of(floor))
    assert shallow.cooking_stat_gained['STR'] == 8
    assert deep.cooking_stat_gained['STR'] == 28 == deep.stat_cap_for_tier('STR', 5)
    q = Player()
    total = 0
    for floor in range(1, 101):
        q.deepest_floor_reached = floor
        q.reset_floor_cook_caps()
        total += q.feed_cut_stat(('STR', 'CON', 'DEX')[floor % 3], kitchen.band_of(floor))
    assert 80 <= total <= 84            # each stat at its band's cap, floor by floor


def test_dexterity_gives_no_armor_but_speed_and_the_dodge():
    """Rewritten 2026-11-16 (the defence model, Brandon's approved design):
    AC comes from armour, the shield and magic only. Dexterity was worth up
    to 6 points of armor in light armour (from 2026-11-13; 3 in anything
    before), and a nimble hero in studded leather out-armoured full plate.
    It is the dodge and the speed now, and a clumsy hero's minus is gone
    with it (tests/test_defence_model.py)."""
    import items
    p = Player()
    naked = p.get_ac()
    for dex in (6, 16, 40):
        p.DEX = dex
        assert p.get_ac() == naked
    assert p.get_speed() > 10 and p.dodge_chance() > 0
    q = Player()
    q.DEX = 40
    q._apply_equip(items.instantiate_armor('plate', 'chain_steel'))
    assert q.get_ac() == 10 - 7
    assert q.dodge_chance() == 0.0


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
    s0 = p.STR
    food_system.cook_compound_recipe(p, dish, p.inventory, Quiz(), got.extend)
    assert p.STR == s0 + 1 and p.cooking_stat_gained['STR'] == 1
    assert any('Strength increases by 1' in m for m in got), got
    eff = kitchen.dish_effects(Player(), dish)
    tier = kitchen.dish_tier(dish)
    assert eff[0] == 'Teaches STR +1'
    assert eff[1] == f"Tier {tier} dishes teach STR up to +{Player().cooking_stat_softcap('STR', tier)} (now +0)"
