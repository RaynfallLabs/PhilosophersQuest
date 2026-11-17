"""Brandon's decided items of 2026-11-16 (the brief's items 2-7 and 10-12;
the starting kit, Achilles and Fianna are in test_starting_kit_in_hand.py).

Each test names the item and what was wrong. Headless Game and data tests:
how they feel in play is a play-test question.
"""
import copy
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import kitchen  # noqa: E402
from game_states import (STATE_PLAYER, STATE_QUIZ, STATE_ASK, STATE_EAT_MENU,  # noqa: E402
                         STATE_PET_FEED, STATE_PET_MENU, STATE_SHOP, STATE_DEAD)
from quiz_engine import QuizResult  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _game(name='__test_decided_11_16__'):
    from main import Game
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _said(g, n=30):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ------------------------------------------------- 2. harvest's tier band

def test_harvest_band_is_the_games_one_band_rule():
    """BAL-15: food_system used floor // 20 + 1, so floors 20/40/60/80 (every
    gate boss) asked an animal question a tier too hard."""
    import food_system
    from items import _floor_band_tier
    for kind, v in MONS.items():
        if not isinstance(v, dict):
            continue
        floor = int(v.get('peak_floor') or v.get('min_level') or 1)
        if floor > 100:
            continue
        assert food_system._monster_band_tier(kind) == _floor_band_tier(floor), (kind, floor)
    on_20 = [k for k, v in MONS.items() if isinstance(v, dict)
             and int(v.get('peak_floor') or v.get('min_level') or 1) == 20]
    assert on_20 and all(food_system._monster_band_tier(k) == 1 for k in on_20)


def test_a_floor_20_corpse_asks_a_tier_1_question():
    import food_system
    from player import Player
    kind = next(k for k, v in MONS.items() if isinstance(v, dict)
                and int(v.get('peak_floor') or v.get('min_level') or 1) == 20)
    asked = {}

    class Quiz:
        def start_quiz(self, **kw):
            asked.update(kw)
    corpse = types.SimpleNamespace(monster_id=kind, harvest_tier=5, name='X',
                                   monster_def=MONS[kind], family=None)
    food_system.harvest_corpse(Player(), corpse, Quiz(), lambda i, m: None)
    assert asked['tier'] == 1


def test_no_kind_has_harvest_tier_0_and_the_16_sit_in_their_band():
    """BAL-15: 16 kinds had harvest_tier 0 (angels, Abaddon's locusts, the
    deadites, the Black Knight, the Stray Kids zombies...)."""
    from items import _floor_band_tier
    assert not [k for k, v in MONS.items() if isinstance(v, dict) and v.get('harvest_tier', 1) == 0]
    for kind in ('abyssal_locust', 'heavenly_angel', 'deadite', 'fresh_deadite', 'risen_deadite',
                 'black_knight', 'neferkaptah_risen', 'azarael', 'sk_zombie_bang_chan',
                 'sk_zombie_lee_know', 'sk_zombie_changbin', 'sk_zombie_hyunjin', 'sk_zombie_han',
                 'sk_zombie_felix', 'sk_zombie_seungmin', 'sk_zombie_i_n'):
        v = MONS[kind]
        assert v['harvest_tier'] == _floor_band_tier(v.get('peak_floor') or v.get('min_level')), kind


# ---------------------------------------------- 3. a spike is not a missile

def _monster(kind):
    from monster import Monster
    return Monster({**MONS[kind], 'id': kind}, 1, 1)


def test_spike_is_not_a_missile_word_and_one_list_serves_everywhere():
    """BUG-1: 'spike' on the missile list made the orc marauder fire his
    Spiked Shield from across the room."""
    import monster
    assert 'spike' not in monster._RANGED_WORDS
    with open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8') as f:
        src = f.read()
    assert "'spike'" not in src                       # no copy of the list left there
    marauder = _monster('orc_marauder')
    assert not any(a['name'] == 'Spiked Shield' for a in marauder._distance_attacks())
    shield = next(a for a in marauder.attacks if a['name'] == 'Spiked Shield')
    assert 'swings' in marauder._miss_text(shield)     # a blow misses as a blow
    devil = _monster('barbed_devil')
    assert not any(a['name'] == 'Tail Spike' for a in devil._distance_attacks())


def test_a_creature_that_shoots_its_spikes_still_does():
    """The manticore shoots the spikes of its tail (Ctesias): its own data
    says so now, and its elder's is a Tail Spike Volley."""
    for kind, name in (('manticore', 'Tail Spike'), ('manticore_elder', 'Tail Spike Volley')):
        m = _monster(kind)
        assert any(a['name'] == name for a in m._distance_attacks()), kind


# ------------------------------------------ 4. no trap beside the up stair

class _NearStairFirst(random.Random):
    """A rigged rng: any shuffled list of tiles comes out nearest the up
    stair first, so a trap lands beside it whenever the rule lets one."""
    up = (0, 0)

    def shuffle(self, x):
        super().shuffle(x)
        if x and all(isinstance(t, tuple) and len(t) == 2
                     and all(isinstance(c, int) for c in t) for t in x):
            ux, uy = self.up
            x.sort(key=lambda t: max(abs(t[0] - ux), abs(t[1] - uy)))


@pytest.mark.parametrize('level', [1, 2, 10, 21])
def test_no_floor_trap_sits_on_or_beside_the_up_stair(level, monkeypatch):
    """BUG-3: only the start tile was kept clear, so about one floor in 300
    put a trap next to the up stair, floor 1 included."""
    import dungeon as D
    d = D.generate_dungeon(80, 50, level)
    up, _down = D._find_stair_tiles(d.tiles, d.width, d.height)
    assert up is not None
    _NearStairFirst.up = up
    fake = types.SimpleNamespace(**{k: getattr(random, k) for k in dir(random)
                                    if not k.startswith('__')})
    fake.Random = _NearStairFirst
    monkeypatch.setattr(D, 'random', fake)
    d.traps = {}
    D.spawn_items(d.rooms, level, d)
    assert d.traps
    for (tx, ty) in d.traps:
        assert max(abs(tx - up[0]), abs(ty - up[1])) > 1, ((tx, ty), up)


# ----------------------------------------------- 5. a trophy asks first

def _trophy(iid='fenrir_wolf_trophy'):
    from food_system import load_ingredient_for
    t = load_ingredient_for(iid)
    t.count = 1
    return t


def test_a_trophy_is_known_and_its_warning_names_its_feast():
    t = _trophy()
    assert kitchen.is_raw_trophy(t)
    lines = kitchen.trophy_warning_lines(t)
    assert 'one of a kind' in lines[0] and 'STR +3 for good' in lines[1]
    from food_system import load_ingredient_for
    assert not kitchen.is_raw_trophy(load_ingredient_for('goblin_prime'))


def test_eating_a_trophy_raw_asks_first_and_no_keeps_it():
    g = _game()
    t = _trophy()
    g.player.inventory.append(t)
    g._open_eat_menu()
    assert g.state == STATE_EAT_MENU
    tab = next(i for i, (_, filt) in enumerate(g._EAT_TABS) if filt(t))
    g._eat_tab = tab
    g._eat_sel = g._get_eat_tab_items().index(t)
    g._eat_menu_input(pygame.K_RETURN)
    assert g.state == STATE_ASK and t in g.player.inventory
    assert "Fenrir's Tooth" in g._ask_data['title']
    g._ask_input(pygame.K_RETURN)                       # Enter keeps it
    assert g.state == STATE_EAT_MENU and t in g.player.inventory
    g._eat_menu_input(pygame.K_RETURN)
    g._ask_input(pygame.K_ESCAPE)                       # so does Esc
    assert g.state == STATE_EAT_MENU and t in g.player.inventory
    g._eat_menu_input(pygame.K_RETURN)
    g._ask_input(pygame.K_y)                            # Y eats it
    assert t not in g.player.inventory and g.state == STATE_PLAYER


def test_an_ordinary_cut_is_eaten_with_no_question():
    from food_system import load_ingredient_for
    g = _game()
    cut = load_ingredient_for('goblin_prime')
    cut.count = 1
    g.player.inventory.append(cut)
    g._open_eat_menu()
    g._eat_tab = next(i for i, (_, filt) in enumerate(g._EAT_TABS) if filt(cut))
    g._eat_sel = g._get_eat_tab_items().index(cut)
    g._eat_menu_input(pygame.K_RETURN)
    assert g.state == STATE_PLAYER and cut not in g.player.inventory


def test_feeding_a_trophy_to_a_pet_asks_first():
    g = _game()
    t = _trophy()
    g.player.inventory.append(t)
    pet = types.SimpleNamespace(name='Ember', max_hp=20, hp=10, gain_xp=lambda n: [])
    g.pet_feed_items = [t]
    g._pet_feed_target = pet
    g._pet_feed_sel = 0
    g.state = STATE_PET_FEED
    g._pet_feed_input(pygame.K_RETURN)
    assert g.state == STATE_ASK and t in g.player.inventory
    assert 'Ember' in g._ask_data['title']
    g._ask_input(pygame.K_n)
    assert g.state == STATE_PET_FEED and t in g.player.inventory
    g._pet_feed_input(pygame.K_RETURN)
    g._ask_input(pygame.K_y)
    assert g.state == STATE_PET_MENU and t not in g.player.inventory and pet.hp > 10


def test_selling_a_trophy_asks_first_and_comes_back_to_the_shop():
    from mystery_system import MerchantNPC, build_trader
    g = _game()
    t = _trophy()
    g.player.inventory.append(t)
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader('generalist', g.dungeon_level, random.Random(11))
    m.x, m.y = g.player.x + 1, g.player.y
    m.purse = 100000
    g.ground_items.append(m)
    g._open_shop()
    g._shop_tab = 1
    offer, why = g._trader_offer(t)
    assert why is None, why
    gold = g.player_gold
    g._trader_sell(t)
    assert g.state == STATE_ASK and t in g.player.inventory and g.player_gold == gold
    g._ask_input(pygame.K_ESCAPE)
    assert g.state == STATE_SHOP and t in g.player.inventory
    g._trader_sell(t)
    g._ask_input(pygame.K_y)
    assert g.state == STATE_SHOP and t not in g.player.inventory and g.player_gold > gold


# ---------------------------------- 6. a starving hero's cook menu opens on food

def _pack_for(rec):
    from food_system import load_ingredient_for
    foods = {f.id: f for f in items.load_items('food')}
    out = []
    for iid, n in kitchen.needs(rec).items():
        it = load_ingredient_for(iid) or copy.copy(foods[iid])
        it.count = n
        out.append(it)
    return out


def _only_ready(tab):
    """A pack that cooks dishes of ``tab`` only."""
    for rec in kitchen.book():
        if kitchen.dish_tab(rec) != tab or kitchen.makes(rec):
            continue
        try:
            pack = _pack_for(rec)
        except KeyError:
            continue
        counts = kitchen.held_counts(pack)
        if {kitchen.dish_tab(r) for r in kitchen.book() if kitchen.can_cook(r, counts)} == {tab}:
            return pack
    raise AssertionError(f'no pack cooks {tab} alone')


def _hungry():
    from player import Player
    p = Player()
    p.sp = max(0, int(p.max_sp * 0.1))
    return p


def test_a_starving_hero_never_opens_on_a_stat_dish():
    """UI-5: with only a Stat dish ready, the hungry hero's menu opened on
    Stat. It opens where food is, and says what is missing."""
    p = _hungry()
    tab, why = kitchen.opening_choice(p, _only_ready('stat'))
    assert tab in ('sp', 'hp') and why == 'hungry_missing'
    import cook_menu
    line = cook_menu.reason_line(tab, why, p)
    assert 'hungry' in line and 'no SP or HP dish is ready' in line
    assert cook_menu.urgent(why)


def test_a_starving_hero_opens_on_what_will_feed_him():
    p = _hungry()
    assert kitchen.opening_choice(p, _only_ready('sp')) == ('sp', 'hungry')
    assert kitchen.opening_choice(p, _only_ready('hp')) == ('hp', 'hungry')


# ------------------------------------------------ 7. the death line is true

def test_the_death_line_says_esc_goes_to_the_title():
    """UI-2: "You have died! Press ESC to quit." but Esc goes to the title."""
    for path in ('main.py', 'game_combat.py', 'game_render.py'):
        with open(os.path.join(ROOT, 'src', path), encoding='utf-8') as f:
            assert 'ESC to quit' not in f.read(), path
    g = _game()
    g.player.hp = 0
    g._advance_turn()
    assert g.state == STATE_DEAD
    assert any('Press Esc to return to the title' in t for t in _said(g))


# --------------------------------------------- 10. floor-1 war-bands shrink

def _mean(expr):
    import re
    m = re.match(r'(\d+)d(\d+)([+-]\d+)?', str(expr).replace(' ', ''))
    n, s, b = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return n * (s + 1) / 2 + b


def _turn_damage(kind, ac=10):
    """A creature's mean damage a turn on AC 10 (bug bash 3.5.1 Q12's sum)."""
    v = MONS[kind]
    p = max(0.05, min(0.95, (21 - (int(v['thac0']) - ac)) / 20.0))
    atks = v.get('attacks') or []
    return p * sum(_mean(a['damage']) for a in atks) / max(1, len(atks))


def test_the_first_floors_bands_are_a_fair_fight_for_a_new_hero():
    """BAL-8 / bug bash 3.5.1 Q12: a level-1 hero (30 HP, AC 10) died in
    about 5 turns to a whole gang of footpads (about 6.5 HP a turn), and from
    floor 3 a goblin war-band or a bandit crew put about 10 a turn on him.
    Floors 1-6 hold only the two small bands, smaller, keeping the set piece:
    a hobgoblin and at most two followers; a couple of footpads."""
    import dungeon
    import war_bands
    for floor in range(1, 7):
        pool = dungeon._floor_pool(floor, None)
        per_band = {}
        for seed in range(400):
            got = war_bands.pick_band(floor, pool, random.Random(seed))
            if not got:
                continue
            bid, roster = got
            members = [roster['leader']] + [k for r in war_bands.ROLES for k in roster[r]]
            assert 2 <= len(members) <= 3, (floor, bid, members)
            per_band.setdefault(bid, []).append(sum(_turn_damage(k) for k in members))
        assert set(per_band) == {'goblin_scouts', 'footpads'}, (floor, set(per_band))
        for bid, dmg in per_band.items():
            assert max(dmg) <= 5.5, (floor, bid, max(dmg))
            if floor <= 2:
                assert max(dmg) <= 4.5 and sum(dmg) / len(dmg) <= 3.6, (floor, bid)
    b = war_bands.data()['bands']
    assert b['footpads']['most_followers'] == 1 and b['goblin_scouts']['most_followers'] == 2
    for bid in ('goblin_raiders', 'bandit_crew', 'gnoll_pack'):
        assert b[bid]['floors'][0] == 7, bid


# ------------------------------- 11. a failed equip quiz loses its donning time

def _fail_quiz(g):
    assert g.state == STATE_QUIZ
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    g.state = STATE_PLAYER
    cb(QuizResult(success=False, score=0, correct=0, asked=1))


def _bare(g):
    from items import ARMOR_SLOTS
    p = g.player
    p.shield = None
    p.armor_slots = [None] * len(ARMOR_SLOTS)
    p.accessory_slots = [None] * 4
    p.known_by_hand = set()
    p.hp = p.max_hp = 500


def test_a_failed_armour_quiz_costs_its_donning_turns(monkeypatch):
    """Brandon 2026-11-16: "use the equip length as 'lost' turns on a
    failure" (it cost one turn)."""
    import gear
    g = _game()
    _bare(g)
    plate = items.instantiate_armor('full_plate', 'chain_steel')
    n = gear.don_turns(plate)
    assert n > 1
    g.player.inventory.append(plate)
    turns = []
    real = g._advance_turn
    monkeypatch.setattr(g, '_advance_turn', lambda: (turns.append(1), real())[1])
    g._equip_item(plate)
    _fail_quiz(g)
    assert len(turns) == n
    assert plate in g.player.inventory and plate not in g.player.armor_slots
    assert any(f"for {n} turns and give up" in t for t in _said(g))


def test_a_failed_ring_quiz_costs_its_one_turn(monkeypatch):
    g = _game()
    _bare(g)
    ring = items.make_item_by_id('accessory', 'ring_of_regeneration')
    g.player.inventory.append(ring)
    turns = []
    real = g._advance_turn
    monkeypatch.setattr(g, '_advance_turn', lambda: (turns.append(1), real())[1])
    g._equip_accessory(ring)
    _fail_quiz(g)
    assert len(turns) == 1 and any('for 1 turn and give up' in t for t in _said(g))


# ------------------------------- 12. a deeper ring of a known kind asks again

def test_an_old_saves_worn_ring_counts_at_its_own_tier():
    import known_by_hand as kbh
    import rings
    from player import Player
    p = Player()
    worn = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(worn, 7)                              # tier IV
    p.accessory_slots[0] = worn
    p.known_by_hand = {'ring_of_protection', 'ring_of_regeneration', 'iron_breastplate'}
    state = dict(p.__dict__)
    state.pop('by_hand_ring_tiers')                     # a save from before
    q = Player.__new__(Player)
    q.__setstate__(state)
    assert q.by_hand_ring_tiers['ring_of_protection'] == 4
    regen = rings.get('regeneration')
    assert q.by_hand_ring_tiers['ring_of_regeneration'] == \
        (rings.first_level(regen) + 1) // 2
    hi = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(hi, 10)
    lo = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(lo, 3)
    assert not kbh.knows(q, hi) and kbh.knows(q, lo)
    assert 'iron_breastplate' in q.known_by_hand         # everything else as it was


def test_a_starting_ring_is_known_at_its_own_tier():
    import known_by_hand as kbh
    import rings
    from main import Game
    from welcome_screen import SECRET_BUILDS
    g = Game(pygame.display.set_mode((1, 1)), player_name='cain',
             secret_build=SECRET_BUILDS['cain'])
    ring = next(i for i in g.player.inventory if getattr(i, 'id', '') == 'ring_of_protection')
    assert kbh.knows(g.player, ring)
    deeper = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(deeper, 9)
    assert not kbh.knows(g.player, deeper)
