"""Bug bash 4 rulings (2026-10-17), R2: items and containers.

Brandon's calls 7, 8, 9, 10, 11 and 32 (BUG_BASH_REPORT_2026_10_16.md; the
findings are items/I-05, I-13, I-19, I-20, world/TR2, TR4, E2). Behaviour
tests on a real headless Game. What they cannot show (how the chest refusal
and the corpse weights feel in play) is a play-test question: Claude cannot
drive Pygame.
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402
from items import load_items  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__bb4_rulings_items__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.ground_items = [i for i in g.ground_items
                      if (i.x, i.y) != (g.player.x, g.player.y)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _texts(g, n=6):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _fully_known(it):
    return int(it.id_level) == 5 and bool(it.buc_known)


def _chest(g, dx=0, dy=0, mimic=False):
    chest = copy.copy(load_items('container')[0])
    chest.x, chest.y = g.player.x + dx, g.player.y + dy
    chest.is_mimic = mimic
    chest.opened = False
    g.ground_items.append(chest)
    return chest


def _potion(effect):
    return copy.copy(next(p for p in load_items('potion') if p.effect == effect))


# ===================================================================== call 7
def test_call7_the_sword_and_scales_of_michael_arrive_fully_identified(monkeypatch):
    """The Last Judgment's gifts set `identified`, which wrote id level 4:
    the blessing and enchantment stayed hidden on a divine gift."""
    import npc_encounters
    g = _game()
    monkeypatch.setattr(npc_encounters, 'judge_karma',
                        lambda k: ('sword_and_scales', 'Worthy.'))
    g._resolve_judgment()
    got = {i.id: i for i in g.player.inventory + g.ground_items}
    for iid in ('sword_of_michael', 'scales_of_michael'):
        assert iid in got, iid
        assert _fully_known(got[iid]), (iid, got[iid].id_level, got[iid].buc_known)
        assert g.player.knows_item_type(got[iid])


def test_call7_npc_reward_items_are_fully_identified():
    g = _game()
    for kind in ('random_potion', 'random_scroll', 'random_wand', 'random_weapon'):
        it = g._generate_npc_reward_item(kind)
        assert it is not None, kind
        assert _fully_known(it), (kind, it.id_level, it.buc_known)
    heal = g._create_specific_npc_item('potion', 'potion_of_healing')
    assert _fully_known(heal)
    # A reward marked no_auto_identify still arrives unknown.
    plain = g._create_specific_npc_item('potion', 'potion_of_healing',
                                        no_auto_identify=True)
    assert plain.id_level == 0


def test_call7_quest_artifacts_and_boss_drops_are_fully_identified():
    from dungeon import _quest_artifact
    g = _game()
    gleipnir = _quest_artifact('gleipnir')
    assert gleipnir is not None and _fully_known(gleipnir)
    px, py = g.player.x, g.player.y
    g.ground_items = []
    g._spawn_fafnir_blood(px, py)
    name = g._spawn_intercession_artifact(px, py)
    assert name
    for it in g.ground_items:
        assert _fully_known(it), (it.id, it.id_level, it.buc_known)
    assert len(g.ground_items) == 2


def test_call7_divine_gift_does_not_count_as_the_heros_own_identify():
    g = _game()
    before = g.player.total_identifies
    pot = _potion('heal')
    pot.id_level = 0
    items.grant_identified(g, pot)
    assert _fully_known(pot) and g.player.knows_item_type(pot)
    assert g.player.total_identifies == before


# ===================================================================== call 8
def test_call8_unknown_copies_never_merge_so_the_stack_hides_the_blessing():
    """A new unknown potion joined its stack only when the hidden BUC matched,
    so 'would not stack' meant 'different blessing'. (A copy of a KIND the
    hero knows is fully identified, blessing included, so the rule is about
    kinds he does not know: the starting kit's are forgotten here.)"""
    g = _game()
    p = g.player
    p.inventory = []
    for s in ('known_item_ids', 'known_class_ids', 'known_forms', 'known_materials'):
        getattr(p, s).clear()
    a, b = _potion('heal'), _potion('heal')
    for it in (a, b):
        it.id_level, it.buc_known, it.buc = 0, False, 'uncursed'
    assert p.add_to_inventory(a) and p.add_to_inventory(b)
    assert len([i for i in p.inventory if i.id == a.id]) == 2
    assert a.count == 1 and b.count == 1
    # One known, one unknown: still apart.
    c = _potion('heal')
    c.id_level, c.buc_known, c.buc = 0, True, 'uncursed'
    p.add_to_inventory(c)
    assert c in p.inventory and c.count == 1


def test_call8_copies_merge_when_the_blessing_is_known_on_both():
    g = _game()
    p = g.player
    p.inventory = []
    a, b, cursed = _potion('heal'), _potion('heal'), _potion('heal')
    a.buc, a.buc_known, a.id_level = 'uncursed', True, 0
    b.buc, b.id_level = 'uncursed', 5            # identified copy: known
    cursed.buc, cursed.buc_known = 'cursed', True
    p.add_to_inventory(a)
    p.add_to_inventory(b)
    assert a.count == 2 and b not in p.inventory
    p.add_to_inventory(cursed)
    assert cursed in p.inventory and a.count == 2


def test_call8_food_and_ingredients_still_stack():
    g = _game()
    p = g.player
    p.inventory = []
    food = next(f for f in load_items('food') if f.id_level >= 5)
    f1, f2 = copy.copy(food), copy.copy(food)
    p.add_to_inventory(f1)
    p.add_to_inventory(f2)
    assert f1.count == 2 and f2 not in p.inventory


# ===================================================================== call 9
def test_call9_a_chest_cannot_be_picked_up():
    g = _game()
    p = g.player
    weight = p.current_weight() if hasattr(p, 'current_weight') else None
    chest = _chest(g)
    g._pickup()
    assert chest in g.ground_items and chest not in p.inventory
    assert any('cannot carry' in t and 'open it where it stands' in t
               for t in _texts(g)), _texts(g)
    if weight is not None:
        assert p.current_weight() == weight


def test_call9_a_mimic_chest_cannot_be_picked_up_either():
    g = _game()
    chest = _chest(g, mimic=True)
    g._pickup()
    assert chest in g.ground_items and chest not in g.player.inventory
    assert not g.monsters


def test_call9_other_items_on_a_chest_tile_are_still_picked_up():
    g = _game()
    chest = _chest(g)
    pot = _potion('heal')
    pot.x, pot.y = g.player.x, g.player.y
    g.ground_items.append(pot)
    g._pickup()
    assert chest in g.ground_items
    assert any(i.id == pot.id for i in g.player.inventory)


def test_call9_no_path_into_the_pack_takes_a_chest():
    """The pack itself refuses one (rewards, Take & Equip and every other
    path go through add_to_inventory or _pickup)."""
    g = _game()
    chest = _chest(g)
    assert g.player.add_to_inventory(chest) is False
    assert chest not in g.player.inventory
    g._pickup(target=chest)                     # the Kit's Take & Equip route
    assert chest not in g.player.inventory
    acts = {a['id'] for a in g._item_actions(chest, 'floor')}
    assert 'equip' not in acts


def test_call9_an_old_save_carrying_a_chest_sets_it_down_on_load(tmp_path, monkeypatch):
    import save_system
    from main import Game
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    g = _game('bb4chestsave')
    chest = copy.copy(load_items('container')[0])
    chest.is_mimic = True
    g.player.inventory.append(chest)             # how an old save held one
    assert save_system.save_game(g)
    state = save_system.load_game('bb4chestsave')
    g2 = Game(_screen(), player_name='bb4chestsave')
    g2.load_state(state)
    assert not any(isinstance(i, items.Container) for i in g2.player.inventory)
    here = [i for i in g2.ground_items if isinstance(i, items.Container)
            and (i.x, i.y) == (g2.player.x, g2.player.y)]
    assert len(here) == 1 and here[0].is_mimic and not here[0].opened
    assert any('set the' in str(e[0]).lower() and 'feet' in str(e[0])
               for e in g2.msg_log.entries)


# ===================================================================== call 10
def test_call10_corpse_weight_follows_body_size():
    from items import Corpse, corpse_weight
    assert corpse_weight('giant_rat') == 2
    assert corpse_weight('goblin') == 10
    assert corpse_weight('orc_warrior') == 40
    assert corpse_weight('troll') == 150
    assert corpse_weight('ancient_dragon') == 400
    assert corpse_weight('frost_giant') == 400
    assert corpse_weight('wraith') == 2            # incorporeal: little left
    rat = Corpse('giant rat', 'giant_rat', 0, 0)
    dragon = Corpse('ancient dragon', 'ancient_dragon', 0, 0)
    assert rat.weight == 2 and dragon.weight == 400


def test_call10_every_monster_has_a_lore_size():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    with open(os.path.join(ROOT, 'data', 'monster_sizes.json'), encoding='utf-8') as f:
        sizes = json.load(f)
    table = sizes['corpse_weight_lb']
    assert set(table) == {'tiny', 'small', 'medium', 'large', 'huge'}
    missing = [m for m in mons if m not in sizes['sizes']]
    assert not missing, missing
    bad = {m: s for m, s in sizes['sizes'].items() if s not in table}
    assert not bad, bad
    stale = [m for m in sizes['sizes'] if m not in mons]
    assert not stale, stale


def test_call10_a_dragon_cannot_be_carried_and_a_man_is_a_real_choice():
    g = _game()
    p = g.player
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    px, py = p.x, p.y

    def corpse_of(kind):
        m = Monster({**mons[kind], 'id': kind}, px, py)
        return g._make_corpse(m)

    dragon = corpse_of('ancient_dragon')
    g.ground_items.append(dragon)
    g._pickup()
    assert dragon not in p.inventory and dragon in g.ground_items
    g.ground_items.remove(dragon)
    # STR 10: a 40 lb body fits an empty pack but is most of the limit.
    p.inventory = []
    man = corpse_of('orc_warrior')
    assert man.weight == 40
    assert man.weight >= 0.3 * p.get_carry_limit()
    g.ground_items.append(man)
    g._pickup()
    assert man in p.inventory


def test_call10_a_carried_corpse_is_harvested_once_set_down():
    g = _game()
    from items import Corpse
    p = g.player
    p.inventory = []
    c = Corpse('giant rat', 'giant_rat', p.x, p.y)
    g.ground_items.append(c)
    g._pickup()
    assert c in p.inventory
    g._do_drop_item(c)
    assert c in g.ground_items
    started = []
    g.quiz_engine.start_quiz = lambda **kw: started.append(kw)
    g._harvest()
    assert started and started[0]['subject'] == 'animal'


# ===================================================================== call 11
def _no_quiz(g):
    started = []
    g.quiz_engine.start_quiz = lambda **kw: started.append(kw)
    return started


def test_call11_the_knock_spell_opens_a_locked_chest_in_place():
    g = _game()
    started = _no_quiz(g)
    chest = _chest(g, dx=1)
    assert chest.locked is True
    g._apply_spell_effect({'effect': 'knock_spell', 'power': '', 'tier': 1})
    assert chest not in g.ground_items and chest.opened
    assert not started                                 # no economics quiz
    texts = ' '.join(_texts(g, 12))
    assert 'No locked containers' not in texts
    assert 'swings open' in texts


def test_call11_the_wand_of_opening_opens_every_chest_in_sight():
    g = _game()
    started = _no_quiz(g)
    a = _chest(g, dx=1)
    b = _chest(g, dy=1)
    g._refresh_fov()
    wand = copy.copy(next(w for w in load_items('wand') if w.effect == 'opening'))
    g._apply_wand_effect(wand)
    assert a not in g.ground_items and b not in g.ground_items
    assert not started
    assert any('2 chests unlock' in t for t in _texts(g, 20)), _texts(g, 20)


def test_call11_knock_on_a_mimic_wakes_it():
    g = _game()
    chest = _chest(g, dx=1, mimic=True)
    g._apply_spell_effect({'effect': 'knock_spell', 'power': '', 'tier': 1})
    assert chest not in g.ground_items
    assert g.monsters, 'the mimic should be awake'


def test_call11_an_unlocked_chest_opens_on_p_without_a_quiz():
    g = _game()
    started = _no_quiz(g)
    chest = _chest(g, dx=1)
    chest.locked = False
    g._lockpick()
    assert chest not in g.ground_items and not started


def test_call11_old_save_chests_are_locked():
    """A chest pickled before the field existed reads as locked (class
    default), so knock finds it and P still asks the question."""
    chest = copy.copy(load_items('container')[0])
    del chest.__dict__['locked']
    assert chest.locked is True


# ===================================================================== call 32
def test_call32_the_healing_picker_lists_only_identified_healers():
    g = _game()
    p = g.player
    p.inventory = []
    p.known_spells = {}
    heal_unknown = _potion('heal')
    heal_unknown.id_level = 0
    p.known_item_ids.discard(heal_unknown.id)
    other = _potion('confusion')
    other.id_level = 0
    p.inventory += [heal_unknown, other]
    assert g._get_filtered_inventory('healing_potion') == []
    from npc_encounters import can_pay_cost
    ok, why = can_pay_cost(p, {'type': 'healing_potion'}, 0)
    assert not ok and 'know' in why
    # Known by type: listed.
    p.known_item_ids.add(heal_unknown.id)
    assert g._get_filtered_inventory('healing_potion') == [heal_unknown]
    assert can_pay_cost(p, {'type': 'healing_potion'}, 0)[0]
    # Known as a copy (identified), type not recorded: listed too.
    p.known_item_ids.discard(heal_unknown.id)
    heal_unknown.id_level = 5
    assert g._get_filtered_inventory('healing_potion') == [heal_unknown]
