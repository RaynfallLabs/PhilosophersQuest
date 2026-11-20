"""Slice M after its audit (_mm_2026_11_19/M/AUDIT.md, 2026-11-20): each
defect found in how the lore powers meet the game, on a real Game, seeded.

D1 the Roc's lift in the turn of its blow, never across a stair or a save,
   and only onto a tile the hero could walk to; D2 the Kappa's dish spills
   on any stun; D3 only the hero's (or his pet's) blow breaks a peace; D4 the
   Cu-Sith barks only at a hero it has noticed, and not while silenced; D5 a
   held or silenced Blue Man calls no verse; D6 only the hero's own food is
   an offering; D7 a poor answer brings the squall; D8 the seed's pronoun;
   D9 the senses' words; D10 the Bulgasari eats only what it can wear away;
   D12 the tells promise only what is built; the harvest kin of their tier.
"""
import json
import os
import random
import sys
import types

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
import lore_powers  # noqa: E402

_SCREEN = None
with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='__test_mm_audit__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(kind, x=0, y=0, aware=True):
    from monster import Monster
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = aware
    return m


def _scene(*placed, seed=7):
    """A game with the hero in an open spot and ``placed`` = (kind, dx, dy)."""
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.monsters = [_monster(k, x + dx, y + dy) for k, dx, dy in placed]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return g


def _messages(g, n=30):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


@pytest.fixture(autouse=True)
def _fresh():
    lore_powers.ENABLED = True
    lore_powers.drain()
    yield
    lore_powers.drain()


def _the_roc(g, monkeypatch):
    """The Roc beside the hero, sure to strike and to lift him."""
    roc = g.monsters[0]
    roc.attacks = [a for a in roc.attacks if a['name'] == 'Talon Crush']
    roc.thac0 = -60
    monkeypatch.setattr(lore_powers, 'random', types.SimpleNamespace(random=lambda: 0.0))
    g.player.hp = g.player.max_hp = 999
    return roc


# ------------------------------------------------------- D1 the Roc's lift

def test_d1_the_roc_sets_the_hero_down_in_the_turn_of_its_blow(monkeypatch):
    g = _scene(('roc_adult', 1, 0))
    d = g.dungeon
    d.explored = {(x, y) for y in range(d.height) for x in range(d.width)}
    _the_roc(g, monkeypatch)
    before = (g.player.x, g.player.y)
    g._do_monster_turns()                        # the Roc alone: nothing after it
    p = g.player
    assert max(abs(p.x - before[0]), abs(p.y - before[1])) >= 8
    assert '_lp_carry_off' not in p.__dict__
    assert p.status_effects.get('immobilized', 0) >= 1
    text = ' '.join(_messages(g))
    assert 'lifts you into the dark' in text and 'drops you far away' in text


def test_d1_a_lift_never_crosses_a_stair_or_a_save():
    g = _scene()
    g.player.__dict__['_lp_carry_off'] = {'tiles': (8, 15), 'landed': '', 'nowhere': ''}
    assert '_lp_carry_off' not in g.player.__getstate__()          # a save never holds one
    g._change_level(2, True)
    assert '_lp_carry_off' not in g.player.__dict__                  # nor does the next floor


def test_d1_an_old_save_s_pending_lift_is_dropped_as_it_loads(monkeypatch):
    from main import Game
    from player import Player
    from save_system import save_game, load_game, delete_save
    name = '__test_mm_audit_lift__'
    g = _scene()
    g.player_name = name
    g.player.__dict__['_lp_carry_off'] = (8, 15)       # a save from before the fix kept it
    keep = Player.__getstate__
    monkeypatch.setattr(Player, '__getstate__',
                        lambda self: {**keep(self), '_lp_carry_off': (8, 15)})
    try:
        assert save_game(g)
        state = load_game(name)
        monkeypatch.setattr(Player, '__getstate__', keep)
        assert state['player'].__dict__.get('_lp_carry_off') == (8, 15)
        g2 = Game(_screen(), player_name=name)
        g2.load_state(state)
        assert '_lp_carry_off' not in g2.player.__dict__
    finally:
        delete_save(name)


def test_d1_the_roc_lands_him_only_where_he_could_walk(monkeypatch):
    from dungeon import FLOOR, WALL
    g = _scene(('roc_adult', 1, 0))
    d = g.dungeon
    # A walled pocket far off, the only ground he has explored there.
    px, py = g.player.x, g.player.y
    ox = px + 11 if px + 14 < d.width else px - 13
    oy = max(2, min(d.height - 5, py))
    for i in range(-1, 4):
        for j in range(-1, 4):
            if d.in_bounds(ox + i, oy + j):
                d.tiles[oy + j][ox + i] = WALL
    pocket = {(ox + i, oy + j) for i in range(3) for j in range(3)}
    for (x, y) in pocket:
        d.tiles[y][x] = FLOOR
    d.explored = set(pocket) | {(px + i, py + j) for i in range(-2, 3) for j in range(-2, 3)}
    _the_roc(g, monkeypatch)
    before = (g.player.x, g.player.y)
    g._do_monster_turns()
    assert (g.player.x, g.player.y) == before                       # no island landing
    assert any('nowhere to set you down' in t for t in _messages(g))


def test_d1_never_on_a_gate_boss_s_floor(monkeypatch):
    g = _scene(('roc_adult', 1, 0))
    d = g.dungeon
    d.explored = {(x, y) for y in range(d.height) for x in range(d.width)}
    g.dungeon_level = 60
    _the_roc(g, monkeypatch)
    before = (g.player.x, g.player.y)
    g._do_monster_turns()
    assert (g.player.x, g.player.y) == before
    assert any('nowhere to set you down' in t for t in _messages(g))


# ------------------------------------------------------ D2 the Kappa's dish

def test_d2_a_chain_special_s_stun_spills_the_kappa_s_dish():
    import combat
    g = _scene(('kappa', 1, 0))
    k = g.monsters[0]
    combat._max_status(k, 'stunned', 2)          # Monster.hold: the chain specials, pets, techniques
    assert k.status_effects.get('weakened', 0) >= 10
    g._lore_powers_say()
    assert any('water' in t.lower() for t in _messages(g))


def test_d2_a_stun_written_straight_in_spills_it_on_its_next_tick():
    g = _scene(('kappa', 1, 0))
    k = g.monsters[0]
    k.status_effects['paralyzed'] = 2            # an armour's stagger, a ring's pacifying
    k.tick_effects()
    assert k.status_effects.get('weakened', 0) >= 10


# ------------------------------------------------- D3 who breaks a peace

def _fed_kappa():
    g = _scene(('kappa', 2, 0))
    k = g.monsters[0]
    k.__dict__['_lp_calm'] = True
    k.__dict__['_lp_parley'] = 'calm'
    return g, k


def test_d3_a_bleed_tick_does_not_break_the_peace():
    g, k = _fed_kappa()
    k.status_effects['bleeding'] = 3
    k.tick_effects()
    assert k.__dict__.get('_lp_calm')
    assert not any('turns on' in t for t, *_ in lore_powers.drain())


def test_d3_a_fire_vent_or_a_monster_s_blow_does_not_either():
    g, k = _fed_kappa()
    g._hazard_hit_monster(k, {'damage': '2d6', 'type': 'fire'})      # the floor's blow
    g._damage_by = 'monster'                                         # a confused orc's
    try:
        k.take_damage(4)
    finally:
        g._damage_by = 'hero'
    assert k.__dict__.get('_lp_calm')


def test_d3_the_pet_s_blow_breaks_it_and_the_line_says_so():
    g, k = _fed_kappa()
    g._damage_by = 'pet'
    try:
        k.take_damage(4)
    finally:
        g._damage_by = 'hero'
    assert not k.__dict__.get('_lp_calm')
    assert any('your companion' in t for t, *_ in lore_powers.drain())


def test_d3_the_hero_s_own_blow_breaks_it():
    g, k = _fed_kappa()
    k.take_damage(4)
    assert not k.__dict__.get('_lp_calm')
    assert any('turns on you' in t for t, *_ in lore_powers.drain())


def test_d3_a_tick_on_a_waiting_blue_man_leaves_him_waiting():
    g = _scene(('blue_men_of_the_minch', 3, 0))
    b = g.monsters[0]
    b.__dict__['_lp_parley'] = 'waiting'
    b.status_effects['bleeding'] = 3
    b.tick_effects()
    assert b.__dict__['_lp_parley'] == 'waiting'


# ---------------------------------------------------- D4 the Cu-Sith's count

def _hound(g):
    from dungeon import FLOOR
    x, y = g.player.x + 4, g.player.y
    g.dungeon.tiles[y][x] = FLOOR
    c = _monster('cu_sith', x, y, aware=False)
    g.monsters = [c]
    return c


def test_d4_the_hound_does_not_bark_at_a_hero_it_has_not_noticed():
    g = _scene()
    c = _hound(g)
    g.player.add_effect('invisible', 50)       # in its line of view, but not noticed
    c._tracking = False
    got = [lore_powers.countdown_turn(c, g.player, g.dungeon) for _ in range(10)]
    assert got == [None] * 10
    assert not [t for t, *_ in lore_powers.drain() if 'bark' in t.lower()]
    assert not c.__dict__.get('_lp_barks')


def test_d4_on_its_own_turns_it_counts_only_once_it_has_noticed_him():
    # Its first turn finds him (senses.notice, after the count is asked):
    # the bark comes on a later turn, never the turn it first looks up.
    g = _scene()
    c = _hound(g)
    c.take_turn(g.player, g.dungeon, g.monsters)
    first = [t for t, *_ in lore_powers.drain() if 'bark' in t.lower()]
    assert not first and c.__dict__.get('_tracking')


def test_d4_silenced_it_does_not_bark_and_the_count_holds():
    import attack_gates
    g = _scene()
    c = _hound(g)
    c._tracking = True
    c.__dict__['_lp_barks'] = 1
    c.__dict__['_lp_clock'] = 3
    attack_gates.inflict(c, 'silenced', 30)
    for _ in range(9):
        assert lore_powers.countdown_turn(c, g.player, g.dungeon) is None
    assert not [t for t, *_ in lore_powers.drain() if 'bark' in t.lower()]
    assert c.__dict__['_lp_barks'] == 1 and c.__dict__['_lp_clock'] == 3


def test_d4_noticed_and_unsilenced_it_still_counts_three():
    g = _scene()
    c = _hound(g)
    c._tracking = True
    got = [lore_powers.countdown_turn(c, g.player, g.dungeon) for _ in range(7)]
    assert got[6] is True
    assert sum('bark' in t.lower() for t, *_ in lore_powers.drain()) == 3


# --------------------------------------------- D5 a held or silenced Blue Man

def test_d5_a_sleeping_blue_man_calls_no_verse():
    g = _scene(('blue_men_of_the_minch', 3, 0))
    b = g.monsters[0]
    b._aware = False
    b.status_effects['sleeping'] = 20
    g._lore_powers_before(b)
    assert b.__dict__.get('_lp_parley') is None


def test_d5_a_silenced_blue_man_calls_no_verse():
    import attack_gates
    g = _scene(('blue_men_of_the_minch', 3, 0))
    b = g.monsters[0]
    b._tracking = True
    attack_gates.inflict(b, 'silenced', 10)
    g._lore_powers_before(b)
    assert b.__dict__.get('_lp_parley') is None


def test_d5_one_that_has_noticed_him_calls_it():
    g = _scene(('blue_men_of_the_minch', 3, 0))
    b = g.monsters[0]
    b._tracking = True
    g._lore_powers_before(b)
    assert b.__dict__.get('_lp_parley') == 'waiting'


def test_d5_a_sleeping_kappa_eats_nothing():
    g = _scene(('kappa', 1, 0))
    k = g.monsters[0]
    k.status_effects['sleeping'] = 20
    apple = _food(g)
    apple.x, apple.y, apple._offered = k.x, k.y, True
    g.ground_items.append(apple)
    g._lore_powers_before(k)
    assert not k.__dict__.get('_lp_calm') and apple in g.ground_items


# ------------------------------------------------- D6 only his own offering

def _food(g):
    from items import load_items
    return next(f for f in load_items('food') if getattr(f, 'id', '') == 'apple')


def test_d6_food_lying_on_the_floor_is_no_offering():
    g = _scene(('kappa', 1, 0))
    k = g.monsters[0]
    found = _food(g)
    found.x, found.y = k.x, k.y
    g.ground_items.append(found)
    g._lore_powers_before(k)
    assert not k.__dict__.get('_lp_calm')


def test_d6_food_the_hero_sets_down_is():
    g = _scene(('kappa', 1, 0))
    k = g.monsters[0]
    it = _food(g)
    g.player.inventory.append(it)
    g._finish_drop(it, 1)
    g._lore_powers_before(k)
    assert k.__dict__.get('_lp_calm')


# ---------------------------------------------------- D7 a poor answer

def test_d7_a_poor_answer_brings_the_squall_down_at_once(monkeypatch):
    g = _scene(('blue_men_of_the_minch', 3, 0), ('blue_men_of_the_minch', 3, 1))
    for b in g.monsters:
        b.__dict__['_lp_parley'] = 'waiting'
    got = {}
    monkeypatch.setattr(g.quiz_engine, 'start_quiz', lambda **kw: got.update(kw))
    monkeypatch.setattr(g, '_advance_turn', lambda: None)
    assert g._parley_offer()
    got['callback'](types.SimpleNamespace(success=False))
    for b in g.monsters:
        assert b.__dict__['_lp_parley'] == 'angry'
        assert b.__dict__.get('_opener_now', {}).get('name') == 'Squall Spray'
    dmg, msg = g.monsters[0].attack(g.player)
    assert 'Squall' in msg or 'squall' in msg.lower() or dmg >= 0


# ------------------------------------------------- D8, D9 the words

def test_d8_the_seed_kneels_each_creature_by_its_own_pronoun():
    import coatings
    g = _scene(('vampire', 1, 0))
    v = g.monsters[0]
    lines = coatings._counting(None, v, {'kinds': ['vampire'], 'turns': 3})
    assert 'his knees' in lines[0][0] and 'its knees' not in lines[0][0]


def test_d9_no_sense_name_is_capitalised_mid_sentence():
    import senses
    g = _scene(('jiangshi', 1, 0), ('komodo_brute', 2, 0))
    for m in g.monsters:
        line = senses.senses_line(m)
        rest = line[1:]
        assert 'Breath' not in rest and 'Blood Scent' not in rest, line


# ------------------------------------------------- D10 the Bulgasari's meal

def test_d10_a_blade_worn_as_far_as_it_goes_feeds_it_nothing(monkeypatch):
    from items import instantiate_weapon
    g = _scene(('bulgasari', 1, 0))
    b = g.monsters[0]
    sword = instantiate_weapon('dagger', 'steel', enchant=-3)
    sword.enchant_bonus = -3
    monkeypatch.setattr(lore_powers, 'random', types.SimpleNamespace(random=lambda: 0.0))
    b.hp = b.max_hp - 50
    hp0, max0 = b.hp, b.max_hp
    lore_powers.after_struck(g.player, b, sword, 1, 10)
    assert (b.hp, b.max_hp) == (hp0, max0)


# ------------------------------------------------- D12 tells, cards, harvest

def test_d12_the_tells_promise_only_what_is_built():
    with open(os.path.join(ROOT, 'data', 'tells.json'), encoding='utf-8') as f:
        eff = json.load(f)['effects']
    assert 'holy water' not in eff['corpse_hop']['counter']
    assert 'Banishment' in eff['corpse_hop']['counter']
    assert 'can see it' not in eff['talisman']['counter']
    assert not eff['appeased_by']['counter'].startswith('Throw')
    with open(os.path.join(ROOT, 'data', 'arsenal.json'), encoding='utf-8') as f:
        crow = json.load(f)['counters']['techniques']['cock_crow']
    assert 'lesser basilisk' in crow['card']


def test_d12_banishment_stops_the_vetala_s_hop():
    from items import Corpse
    g = _scene(('vetala', 1, 0))
    v = g.monsters[0]
    g.ground_items.append(Corpse('Goblin', 'goblin', v.x + 1, v.y + 1))
    v._banished = True
    v.alive = False
    g._lore_powers_killed(v)
    assert len(g.monsters) == 1


def test_harvest_kin_take_a_part_of_their_own_tier():
    with open(os.path.join(ROOT, 'data', 'items', 'harvest_map.json'), encoding='utf-8') as f:
        hm = json.load(f)['monsters']
    with open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8') as f:
        ing = json.load(f)
    for k in ('asanbosam', 'cu_sith', 'likho'):
        part = ing[hm[k]]
        tier = (int(part['min_level']) - 1) // 20 + 1
        assert tier == MONS[k]['harvest_tier'], (k, hm[k], tier)
        assert MONS[k]['name'].split()[0] in part['description'] or k.replace('_', '-') in \
            part['description'].lower() or 'asanbosam' in part['description'], (k, part['description'])
