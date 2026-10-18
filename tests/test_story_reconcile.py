"""The reward and cost shapes the converted stories use that the engine
did not have before the Phase 3 merge (ENCOUNTER_STORIES_DRAFT Part J6):

* ``armor_enchant`` as a cost (Saint Martin's cloak cut in half) and as a
  reward (the dream that makes it whole);
* the ``multi`` cost (lift the gate AND give the pendant back);
* ``count`` on an item cost (give back two potions), stacks included;
* ``random_artifact`` (Pomfrey Quill's trunk);
* a thread that closes in the scene that opens it (the tomb never found
  again), and The Gate's closing line said even when nobody is told about;
* the shipped Setne, Gate and Death encounters in the engine's shapes.

Pure data and headless-Game tests: these are rare, deep or randomised
encounters (CLAUDE.md play-test rule).
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _game(seed=5):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_story_reconcile__')
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _wear_cloak(p):
    from items import ARMOR_SLOTS, make_item_by_id
    cloak = make_item_by_id('armor', 'cloak_of_the_morrigan')
    cloak.enchant_bonus = 1
    p.armor_slots[ARMOR_SLOTS.index('cloak')] = cloak
    return cloak


# ------------------------------------------------------------------ armor_enchant

def test_armor_enchant_cost_cuts_the_cloak_and_the_dream_mends_it():
    from npc_encounters import armor_enchant_target, can_pay_cost
    g = _game()
    p = g.player
    p.armor_slots = [None] * len(p.armor_slots)
    ok, msg = can_pay_cost(p, {'type': 'armor_enchant', 'amount': 1}, 0)
    assert not ok and msg                                  # nothing worn to cut
    cloak = _wear_cloak(p)
    assert armor_enchant_target(p) is cloak
    assert can_pay_cost(p, {'type': 'armor_enchant', 'amount': 1}, 0) == (True, '')
    g._npc_pay_cost({'type': 'armor_enchant', 'amount': 1})
    assert cloak.enchant_bonus == 0
    g._apply_npc_reward({'type': 'multi', 'rewards': [
        {'type': 'armor_enchant', 'amount': 1}, {'type': 'effect', 'effect': 'blessed', 'duration': 60}]})
    assert cloak.enchant_bonus == 1 and p.has_effect('blessed')
    from items import ENCHANT_CAP
    for _ in range(5):
        g._apply_npc_reward({'type': 'armor_enchant', 'amount': 1})
    assert cloak.enchant_bonus == ENCHANT_CAP['cloak']      # never past the slot's cap
    cloak.enchant_bonus = -3
    g._npc_pay_cost({'type': 'armor_enchant', 'amount': 1})
    assert cloak.enchant_bonus == -3                        # never below the floor


# ------------------------------------------------------------------ multi and count

def test_multi_cost_pays_every_part():
    from items import make_item_by_id
    from npc_encounters import can_pay_cost, get_inventory_filter
    g = _game()
    p = g.player
    cost = {'type': 'multi', 'costs': [{'type': 'sp_pct', 'amount': 10},
                                       {'type': 'triggered_item_id', 'item_id': 'silverlight_pendant'}]}
    ok, _msg = can_pay_cost(p, cost, 0)
    assert not ok                                           # no pendant: the whole cost fails
    pendant = make_item_by_id('accessory', 'silverlight_pendant')
    assert pendant is not None
    p.add_to_inventory(pendant)
    assert can_pay_cost(p, cost, 0) == (True, '')
    assert get_inventory_filter(cost) is None               # nothing to pick
    p.sp = 100
    g._npc_pay_cost(cost)
    assert p.sp == 90 and pendant not in p.inventory
    # A multi cost whose part needs a pick hands the pick to that part.
    assert get_inventory_filter({'type': 'multi', 'costs': [
        {'type': 'gold', 'amount': 1}, {'type': 'potion'}]}) == 'potion'


def _potions(p):
    from items import Potion
    return sum(max(1, int(getattr(i, 'count', 1) or 1)) for i in p.inventory if isinstance(i, Potion))


def test_count_on_an_item_cost_takes_that_many_units():
    from items import make_item_by_id
    from npc_encounters import can_pay_cost
    g = _game()
    p = g.player
    from items import Potion
    p.inventory[:] = [i for i in p.inventory if not isinstance(i, Potion)]
    cost = {'type': 'potion', 'count': 2}
    one = make_item_by_id('potion', 'potion_of_healing')
    p.add_to_inventory(one)
    ok, msg = can_pay_cost(p, cost, 0)
    assert not ok and '2' in msg
    p.add_to_inventory(make_item_by_id('potion', 'potion_of_stamina'))
    p.add_to_inventory(make_item_by_id('potion', 'potion_of_cure_poison'))
    assert can_pay_cost(p, cost, 0) == (True, '')
    before = _potions(p)
    g._npc_pay_cost(cost, one)                              # the picked one, then one more
    assert _potions(p) == before - 2 and one not in p.inventory
    # Without a pick (an outcome's cost) the pack gives them in order.
    p.add_to_inventory(make_item_by_id('potion', 'potion_of_healing'))
    before = _potions(p)
    g._npc_pay_cost({'type': 'potion', 'count': 2})
    assert _potions(p) == before - 2


def test_count_takes_units_from_a_stack():
    from items import Potion, make_item_by_id
    from npc_encounters import can_pay_cost
    g = _game()
    p = g.player
    p.inventory[:] = [i for i in p.inventory if not isinstance(i, Potion)]
    stack = make_item_by_id('potion', 'potion_of_healing')
    stack.count = 3
    p.inventory.append(stack)
    assert can_pay_cost(p, {'type': 'potion', 'count': 2}, 0) == (True, '')
    g._npc_pay_cost({'type': 'potion', 'count': 2}, stack)
    assert stack in p.inventory and stack.count == 1


# ------------------------------------------------------------------ random_artifact

def test_random_artifact_sets_a_relic_at_the_heros_feet():
    g = _game()
    before = len(g.ground_items)
    g._apply_npc_reward({'type': 'random_artifact'})
    new = g.ground_items[before:]
    assert len(new) == 1
    it = new[0]
    assert (it.x, it.y) == (g.player.x, g.player.y)
    from items import is_random_loot
    assert is_random_loot(it)                               # never a quest piece


# ------------------------------------------------------------------ threads and the Gate

def test_a_thread_can_close_in_the_scene_that_opens_it():
    g = _game()
    g._apply_outcome_deeds({'thread': {'id': 'thoth_tomb', 'closed_line': 'I never saw it again.'}},
                           'fx')
    t = g._deeds_reg()['threads']['thoth_tomb']
    assert t['status'] == 'closed' and t['closed_line'] == 'I never saw it again.'


def test_the_gate_says_its_closing_line_even_with_nobody_to_tell():
    g = _game()
    text = g._people_lines_text({'table': 'gate', 'max': 6, 'after': 'The rest is between them and me.'})
    assert text == 'The rest is between them and me.'


# ------------------------------------------------------------------ the shipped shapes

def _enc(tag):
    from game_road import _encounter_by_tag
    _src, e = _encounter_by_tag(tag)
    assert e is not None, tag
    return e


def test_setne_tomb_is_in_the_engines_shape():
    e = _enc('flv_setne_tomb')
    assert e['callback_only'] and e['stakes'] == 'high' and e['name'] == 'Neferkaptah'
    senet = next(o for o in e['options'] if o.get('quiz'))
    assert senet['quiz']['play_all'] and len(senet['per_miss']) == 3
    assert senet['per_miss'][1]['effect']['effect'] == 'paralyzed'
    total = senet['fail_by_correct']['0']
    assert total['expel_up'] is True and 'flag.thoth_lost' in total['deeds']
    rw = senet['pass']['reward']
    assert (rw['type'], rw['item_type'], rw['item_id']) == ('specific_item', 'spellbook', 'book_of_thoth')
    oath = senet['pass']['oath']
    assert oath['id'] == 'thoth_return' and oath['lapse_mode'] == 'callback'
    assert oath['due_floors'] == [8, 15]
    cb = senet['pass']['schedule'][0]
    assert cb['encounter'] == 'flv_dead_come_for_the_book' and cb['after_floors'] == [1, 3]
    assert cb['after_oath_due'] == 'thoth_return'
    assert any(o.get('seal_door') for o in e['options'] if o['label'] == 'Leave the tomb')


def test_the_dead_come_hostile_and_settle_the_oath():
    e = _enc('flv_dead_come_for_the_book')
    assert e['hostile'] and e['callback_only']
    by = {o['label']: o for o in e['options']}
    assert by['Give the book back']['oath_lapse'] == 'thoth_return'
    assert by['"I don\'t have it any more."']['oath_lapse'] == 'thoth_return'
    refuse = next(o for lab, o in by.items() if lab.startswith('Refuse'))
    assert refuse['oath_break'] == 'thoth_return'
    assert not refuse.get('karma')                           # the break itself costs the -1


def test_the_gate_reads_the_table_and_deaths_breath_is_a_deed():
    e = _enc('flv_the_gate')
    tell = next(o for o in e['options'] if o.get('people_lines'))
    assert tell['people_lines']['table'] == 'gate' and tell['people_lines']['max'] == 6
    h07 = _enc('flv_deaths_chessboard')
    mine = next(o for o in h07['options'] if o['label'].startswith('Play for yourself'))
    assert 'flag.deaths_lost_turn' in mine['pass']['deeds'] and 'reward' not in mine['pass']


# ------------------------------------------------------------------ the validator

def test_validator_checks_the_new_cost_shapes():
    from tools.encounters import validate as V
    errs = []
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'multi', 'costs': []}, 'medium')
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'gold', 'amount': 1, 'count': 2}, 'medium')
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'potion', 'count': 9}, 'medium')
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'multi', 'costs': [
        {'type': 'potion'}, {'type': 'food'}]}, 'medium')
    assert len(errs) == 4, errs
    errs.clear()
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'potion', 'count': 2}, 'medium')
    V._check_cost(lambda c, m: errs.append((c, m)), 'o', {'type': 'multi', 'costs': [
        {'type': 'sp_pct', 'amount': 10}, {'type': 'potion'}]}, 'medium')
    assert errs == []


def test_rans_net_is_a_real_unique_net_from_andvaris_pool_only():
    g = _game()
    net = g._create_specific_npc_item('weapon', 'rans_net')
    assert net is not None and net.name == "Ran's Net"
    assert getattr(net, 'is_unique', False) and net.tier == 4      # its own tier, from its lore
    import json
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        spec = json.load(f)['rans_net']
    assert not any(spec['floorSpawnWeight'].values())               # never random loot
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', 'rans_net.png'))
