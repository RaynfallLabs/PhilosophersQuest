"""Monster behaviour, third wave (AI-3): the Game's side, on a real Game.

The behaviours are pure modules (tests/test_monster_behaviour_ai3.py);
these are the things the Game does for them (game_monster_ways.py): the
held hero's step (a struggle, a blow on the holder), the swallowed hero out
of the others' reach, the holder's death and the floor change that free him,
a save made in the middle of a hold, the auras on the real hero (his fire
resistance halves the heat), the potion a dying captain did not drink, the
hero who sees a potion drunk and knows it, the leprechaun's bargain, and
the help page.
"""
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
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
    random.seed(seed)
    g = Game(_screen(), player_name='__test_ai3__')
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


def _monster(mid, x=0, y=0):
    from monster import Monster
    m = Monster({**MONS[mid], 'id': mid}, x, y)
    m._aware = True
    return m


def _scene(*placed, seed=7):
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.monsters = [_monster(k, x + dx, y + dy) for k, dx, dy in placed]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return g


def _messages(g, n=20):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _hold(g, m, monkeypatch=None):
    import holds
    real = random.randint
    random.randint = lambda a, b: a                       # the DEX save fails
    try:
        atk = next(a for a in m.attacks if holds.spec_of(a))
        holds.after_blow(m, g.player, atk, 5, '')
    finally:
        random.randint = real
    assert holds.is_holder(m, g.player)
    return atk


def test_a_held_heros_step_is_a_struggle_and_a_step_into_the_holder_is_a_blow():
    import holds
    g = _scene(('rock_python', 1, 0))
    m = g.monsters[0]
    _hold(g, m)
    x0, y0 = g.player.x, g.player.y
    t0 = g.turn_count
    real = random.randint
    random.randint = lambda a, b: a                       # the struggle fails
    try:
        assert g._ways_held_move(-1, 0) is True
    finally:
        random.randint = real
    assert (g.player.x, g.player.y) == (x0, y0) and g.turn_count > t0
    assert any('coils' in t for t in _messages(g))
    if holds.is_held(g.player):
        assert g._ways_held_move(1, 0) is False           # into the python: the fight goes on


def test_a_swallowed_hero_cannot_be_struck_by_the_others():
    g = _scene(('gelatinous_cube', 1, 0), ('goblin', -1, 0))
    cube, gob = g.monsters
    _hold(g, cube)
    assert g._ways_shield(gob) and not g._ways_shield(cube)
    g._target_candidates = [cube, gob]
    assert g._target_candidates == [cube]                 # from inside, only its gut to aim at


def test_the_holders_death_frees_the_hero():
    import holds
    g = _scene(('rock_python', 1, 0))
    m = g.monsters[0]
    _hold(g, m)
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    assert not holds.is_held(g.player) and not g.player.has_effect('held')
    assert any('slack' in t for t in _messages(g))


def test_a_floor_change_ends_the_hold():
    import holds
    g = _scene(('rock_python', 1, 0))
    m = g.monsters[0]
    _hold(g, m)
    g._ways_level_change()
    assert not holds.is_held(g.player) and not m.__dict__.get('_holding')


def test_a_save_in_the_middle_of_a_hold_loads_and_the_world_turn_keeps_it():
    import holds
    g = _scene(('rock_python', 1, 0))
    m = g.monsters[0]
    _hold(g, m)
    player, monsters = pickle.loads(pickle.dumps((g.player, g.monsters)))
    assert holds.is_holder(monsters[0], player) and player.has_effect('held')
    g.player, g.monsters = player, monsters
    g._ways_world_turn()
    assert holds.is_held(g.player)


def test_the_heat_of_a_fire_elemental_and_the_heros_fire_resistance():
    g = _scene(('fire_elemental', 1, 0))
    p = g.player
    p.max_hp = p.hp = 400
    g._ways_world_turn()
    burnt = 400 - p.hp
    assert burnt > 0 and any('heat' in t for t in _messages(g))
    p.hp = 400
    p.status_effects['fire_resist'] = 20
    g._ways_world_turn()
    assert 0 < 400 - p.hp < burnt


def test_a_dying_captain_drops_the_potion_he_never_drank():
    g = _scene(('bandit_captain', 1, 0))
    m = g.monsters[0]
    m._kit = ('potion_of_healing',)
    m._kit_had = True
    m.treasure = {'gold': [0, 0], 'item_chance': 1.0, 'item_tier': 1}
    before = len(g.ground_items)
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    new = g.ground_items[before:]
    assert any(getattr(i, 'id', '') == 'potion_of_healing' for i in new)
    # Its kit was its find: no random item besides (and no corpse counted here).
    assert [i for i in new if getattr(i, 'id', '') not in ('potion_of_healing',)
            and type(i).__name__ not in ('Corpse', 'GoldPile')] == []


def test_a_banished_captain_takes_his_potion_home():
    g = _scene(('bandit_captain', 1, 0))
    m = g.monsters[0]
    m._kit = ('potion_of_healing',)
    m._banished = True
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    assert not any(getattr(i, 'id', '') == 'potion_of_healing' for i in g.ground_items)


def test_the_hero_who_sees_a_potion_drunk_knows_it():
    import monster_kit
    g = _scene(('bandit_captain', 2, 0))
    m = g.monsters[0]
    m._kit = ('potion_of_healing',)
    m._tracking = True
    m.hp = max(1, m.max_hp // 4)
    g.player.known_item_ids.discard('potion_of_healing')
    assert monster_kit.turn(m, g.player, g.dungeon, g.monsters, set()) is False
    g._ai_turn_after(m)
    g._ways_turn_after(m)
    assert 'potion_of_healing' in g.player.known_item_ids
    assert any('gulps down' in t for t in _messages(g))


def test_the_leprechauns_bargain_taken():
    from items import GoldPile
    from game_states import STATE_ASK
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m.treasure = {'gold': [40, 40], 'item_chance': 0.6, 'item_tier': 2}
    m._wants_bargain = True
    g._ways_turn_after(m)
    g._ways_after_world()                                 # asked once the world's turn is over
    assert g.state == STATE_ASK

    def gold_here():
        return sum(it.amount for it in g.ground_items
                   if isinstance(it, GoldPile) and (it.x, it.y) == (m.x, m.y))
    before = gold_here()
    g._ask_data['options'][0][3]()                        # Yes: take the purse
    assert m not in g.monsters and not m.alive
    assert gold_here() - before == 60                     # 40, half again for his freedom
    assert not any(getattr(i, 'monster_id', '') == 'leprechaun' for i in g.ground_items)


def test_the_leprechauns_bargain_refused():
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m._wants_bargain = True
    g._ways_turn_after(m)
    g._ways_after_world()                                 # asked once the world's turn is over
    g._ask_data['options'][1][3]()                        # No
    assert m in g.monsters and m._bargain_refused


def test_no_bargain_in_a_quiz():
    from game_states import STATE_QUIZ
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m._wants_bargain = True
    g.state = STATE_QUIZ
    g._ways_turn_after(m)
    g._ways_after_world()
    assert g.state == STATE_QUIZ and m._wants_bargain     # asked once play is calm
    assert g._bargain_pending is m


def test_a_casters_lines_are_said_and_the_ward_shows_on_the_look_screen():
    import status_effects
    g = _scene(('goblin_shaman', 3, 0))
    m = g.monsters[0]
    m._tracking = True
    m.hp = max(1, m.max_hp // 3)
    m.take_turn(g.player, g.dungeon, g.monsters)
    g._ai_turn_after(m)
    assert any('chant' in t for t in _messages(g))
    assert 'spell_ward' in status_effects.EFFECT_INFO and 'held' in status_effects.EFFECT_INFO


def test_the_monster_ways_help_page_tells_of_the_third_wave():
    g = _game()
    g.screen = _screen()
    g._help_page = 3
    g._draw_help_screen()
    with open(os.path.join(ROOT, 'data', 'ui', 'monster_ways.json'), encoding='utf-8') as f:
        text = f.read()
    for word in ('Held fast', 'Casters', 'Auras', 'Home ground', 'What they carry', 'Leprechaun'):
        assert word in text, word
