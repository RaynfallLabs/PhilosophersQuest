"""Bug bash 3.3.1: Brandon's rulings of 2026-11-06.

- Throne: its +5-15 max HP is given once a throne, not on every sit.
- Banishment: credit, no loot. No corpse, no gold or goods; the kill still
  counts.
- Fail-not: "the promise holds while its archer is calm and unhurt": the
  never-miss save works only at full health.
- Stranded loot: food, gold, chests and gear cut off by water, lava or a
  swamp are moved within reach, as the quest pieces already were.

Logic tests: thrones, banishable foes, Fail-not and island loot are rare.
"""
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)

_SCREEN = None


def _game(seed=7):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    items.bind_unique_registry(set())
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_bugbash_331_rulings__')
    g.state = STATE_PLAYER
    return g


# ------------------------------------------------------------------ throne
def test_a_throne_gives_its_max_hp_once():
    g = _game()
    p = g.player
    p.fortune_stat_gained = 10 ** 6          # fortune spent: no stat noise
    hp0 = p.max_hp
    random.seed(1)
    g._resolve_throne(4)
    once = p.max_hp
    assert once > hp0
    for seed in range(2, 6):
        random.seed(seed)
        g._resolve_throne(5)
    assert p.max_hp == once, "a second sit on the same throne gave more max HP"


def test_another_throne_still_gives_its_own():
    g = _game()
    p = g.player
    p.fortune_stat_gained = 10 ** 6
    g._resolve_throne(4)
    once = p.max_hp
    p.x += 1                                 # the next throne over
    g._resolve_throne(4)
    assert p.max_hp > once


# -------------------------------------------------------------- banishment
def _banishable():
    return next(k for k, d in _DEFS.items()
                if set(d.get('tags') or ()) & {'demon', 'fey', 'elemental', 'celestial'}
                and not d.get('is_boss') and 'legendary' not in (d.get('tags') or ()))


def test_a_banished_creature_leaves_no_loot_but_counts():
    g = _game()
    kind = _banishable()
    m = Monster(dict(_DEFS[kind], id=kind), g.player.x + 1, g.player.y)
    m.treasure = {'gold': [500, 500], 'item_chance': 1.0, 'item_tier': 2,
                  'treasure_chance': 1.0}
    g.monsters = [m]
    g.ground_items = []
    kills0 = int(g.level_mgr.monsters_killed)
    m.alive = False
    m.hp = 0
    m._banished = True
    g._on_monster_killed(m)
    assert g.ground_items == [], [getattr(i, 'name', i) for i in g.ground_items]
    assert int(g.level_mgr.monsters_killed) == kills0 + 1, "a banishment still counts"


def test_a_slain_creature_still_drops_its_loot():
    g = _game()
    kind = _banishable()
    m = Monster(dict(_DEFS[kind], id=kind), g.player.x + 1, g.player.y)
    m.treasure = {'gold': [500, 500]}
    g.monsters = [m]
    g.ground_items = []
    m.alive = False
    m.hp = 0
    g._on_monster_killed(m)
    assert g.ground_items, "an ordinary kill dropped nothing"


# ---------------------------------------------------------------- Fail-not
def _failnot():
    return next(w for w in items.load_items('weapon') if w.id == 'fail_not')


def _kobold():
    m = Monster(dict(_DEFS['kobold'], id='kobold'), 6, 5)
    m.hp = m.max_hp = 10 ** 6
    return m


def test_fail_not_saves_a_wrong_answer_at_full_health():
    p = Player()
    bow = _failnot()
    p.ranged_weapon = bow
    p.hp = p.max_hp
    assert combat.effective_chain(p, _kobold(), bow, 0, consume=False) == 1


def test_a_wounded_hand_makes_fail_not_an_ordinary_bow():
    p = Player()
    bow = _failnot()
    p.ranged_weapon = bow
    p.hp = p.max_hp - 1
    assert combat.effective_chain(p, _kobold(), bow, 0, consume=False) == 0
    assert combat.effective_chain(p, _kobold(), bow, 2, consume=False) >= 2


def test_gungnir_has_no_vow():
    p = Player()
    spear = next(w for w in items.load_items('weapon') if w.id == 'gungnir')
    p.weapon = spear
    p.hp = 1
    assert combat.effective_chain(p, _kobold(), spear, 0, consume=False) == 1


# ------------------------------------------------------------ island loot
@pytest.mark.parametrize('floor', [3, 12, 27, 45, 63, 81, 95])
def test_every_piece_of_loot_can_be_walked_to(floor):
    g = _game(seed=floor)
    g._change_level(floor, enter_from_top=True)
    reach = g._reachable_tiles(g.player.x, g.player.y,
                               through=g._sealed_shrine_doors() or ())
    stranded = [(getattr(it, 'name', '?'), it.x, it.y) for it in g.ground_items
                if not getattr(it, 'not_pickable', False) and (it.x, it.y) not in reach]
    assert stranded == []


# ----------------------------------------------- second batch of rulings
def test_a_raw_ingredient_is_worth_half_a_meal():
    import economy
    import food_system
    raw = next(iter(food_system._raw_ingredients()))
    ing = food_system.load_ingredient_for(raw)
    assert ing.item_class == 'ingredient'
    assert economy.class_share(ing) == economy.MERCHANT_SHARE['food'] / 2
    assert economy.stock_price(ing, 20) > 0
    assert economy.stock_price(ing, 20) <= 100


def test_a_bigger_bundle_of_arrows_costs_more():
    import economy
    lo = items.make_item_by_id('ammo', 'iron_arrow')
    hi = items.make_item_by_id('ammo', 'iron_arrow')
    lo.count, hi.count = lo.count_min, hi.count_max
    assert economy.stock_price(hi, 20) > economy.stock_price(lo, 20)


def test_orpheus_slows_a_new_floor_but_not_a_revisit():
    g = _game()
    g.player.quirk_progress['orpheus_active'] = True
    g._change_level(2, enter_from_top=True)
    assert any(m.status_effects.get('slowed', 0) > 0 for m in g.monsters if m.alive)
    g._change_level(1, enter_from_top=False)
    assert not any(m.status_effects.get('slowed', 0) > 0 for m in g.monsters if m.alive), \
        "a floor already visited was slowed again"
