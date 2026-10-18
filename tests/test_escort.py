"""Escorts (DEEDS_KARMA_DESIGN 4.9 and 6.2, tests 8.5, Brandon's decision 11),
on a real headless Game with fixture content (no shipped encounter starts
an escort yet; Wave A brings Lena). Deep or random escort situations are
proven here, not by play-test.
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


LENA = {
    'id': 'lena', 'name': 'Lena', 'sprite_id': 'npc_lost_girl', 'hp': 40, 'ac': 9,
    'goal': 'stairs_down', 'leash': 2, 'floors': 1, 'perk': 'reveal_traps',
    'on_arrive': {'outcome': 'Lena hands you the last of her mother\'s tonic and is gone.',
                  'reward': {'type': 'effect', 'effect': 'blessed', 'duration': 30},
                  'deeds': ['saved.lena'], 'person_status': 'saved',
                  'chronicle': 'Lena walked me a whole floor and never once stepped on a trap.'},
    'on_fail': {'outcome': '', 'deeds': ['lost.lena'], 'person_status': 'lost',
                'chronicle': "I lost Lena on the stairs. I keep thinking about her mother's squint."},
    'on_fail_variants': [{'when': {'deeds_all': ['flag.escort_left_behind.lena']},
                          'chronicle': 'I went down without Lena. I told myself she would find her own way up.'}],
}

ESCORT_ENC = {
    'tag': 'fx_lena', 'name': "Rat-Catcher's Daughter", 'symbol': '@', 'color': [170, 150, 120],
    'sprite_id': 'npc_lost_girl', 'min_level': 1, 'max_level': 99, 'role': 'story',
    'stakes': 'medium', 'band': [1, 99], 'person': {'id': 'lena', 'name': 'Lena'},
    'text': 'A girl with her mother\'s satchel.',
    'escorts': {'escort_lena': LENA},
    'options': [
        {'label': '"Walk me down one floor."', 'escort': {'$ref': 'escort_lena'},
         'outcome': 'She nods.', 'chronicle': 'Lena is walking me down a floor.'},
        {'label': 'Go on alone', 'outcome': 'She watches you go.'},
    ],
}


def _game(level=5, seed=11):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_escort__')
    g.state = STATE_PLAYER
    if level != 1:
        g._change_level(level, enter_from_top=True)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    return g


def _start(g, spec=None, **over):
    """Start an escort through the real outcome path."""
    enc = copy.deepcopy(ESCORT_ENC)
    if spec is not None:
        enc['escorts']['escort_lena'] = spec
    enc['escorts']['escort_lena'].update(over)
    g._npc_encounter_active = enc
    g._apply_outcome_deeds(enc['options'][0], enc['tag'])
    g._npc_encounter_active = None
    assert len(g.escorts) == 1
    return g.escorts[0]


def _descend(g, via='stairs'):
    g._change_level(g.dungeon_level + 1, enter_from_top=True, via=via)
    g.monsters = []
    g.dungeon.traps = {}


def _chron(g):
    return ' | '.join(e['text'] for e in g._chronicle if isinstance(e, dict))


def test_an_escort_is_not_a_pet_and_starts_beside_the_hero():
    g = _game()
    esc = _start(g)
    assert esc not in g.pets and g.pets == []
    assert esc.is_escort and esc.name == 'Lena'
    assert max(abs(esc.x - g.player.x), abs(esc.y - g.player.y)) == 1
    assert g.dungeon.is_walkable(esc.x, esc.y)
    assert (esc.x, esc.y) in g._occupants()
    g.render()                                          # draws without a crash


def test_success_on_a_stair_descent_inside_the_leash():
    import deeds
    g = _game()
    _start(g)
    _descend(g)
    assert g.escorts == []
    assert deeds.has(g._deeds, 'saved.lena')
    assert g._deeds['people']['lena']['status'] == 'saved'
    assert g.player.has_effect('blessed')
    assert 'never once stepped on a trap' in _chron(g)


def test_a_two_floor_escort_counts_only_descents_and_an_up_stair_carries_it():
    g = _game(level=6)
    esc = _start(g, floors=2)
    g._change_level(5, enter_from_top=False)             # up a stair: no count
    assert esc in g.escorts and esc.floors_left == 2 and esc.floor == 5
    assert max(abs(esc.x - g.player.x), abs(esc.y - g.player.y)) <= 3
    _descend(g)                                          # 6, a floor seen before: still counts
    assert esc in g.escorts and esc.floors_left == 1
    _descend(g)
    assert esc not in g.escorts and not esc.alive


def test_left_behind_outside_the_leash_is_lost():
    import deeds
    g = _game()
    esc = _start(g)
    karma = g.karma
    esc.x, esc.y = g.player.x + 10, g.player.y
    _descend(g)
    assert g.escorts == []
    assert deeds.has(g._deeds, 'flag.escort_left_behind.lena')
    assert deeds.has(g._deeds, 'lost.lena')
    assert 'went down without Lena' in _chron(g)
    assert g.karma == karma                              # never karma by itself


def test_a_trapdoor_or_warp_counts_as_lost_and_the_trapdoor_blames_the_floor():
    import deeds
    g = _game()
    _start(g)
    _descend(g, via='trapdoor')
    assert deeds.has(g._deeds, 'lost.lena')
    assert deeds.has(g._deeds, 'flag.escort_trapdoor.lena')
    assert "floor's doing, not mine" in _chron(g)
    g2 = _game()
    _start(g2)
    g2._change_level(9, enter_from_top=True, via='warp')
    assert deeds.has(g2._deeds, 'lost.lena') and g2.escorts == []


def test_a_cow_level_trip_suspends_and_leaves_floors_left_alone():
    from boss_levels import COW_LEVEL
    g = _game(level=6)
    esc = _start(g, floors=2)
    here = (esc.x, esc.y)
    g._cow_return_level = 6
    g._change_level(COW_LEVEL, enter_from_top=True, via='cow')
    assert esc.suspended and esc.floors_left == 2 and esc in g.escorts
    assert g._escorts_here() == [] and (esc.x, esc.y) not in g._occupants()
    g._change_level(6, enter_from_top=False, via='cow')
    assert not esc.suspended and esc.floors_left == 2
    # Back from the farm she is seated beside the hero at the stair, not
    # left where she stood (SAV-06).
    assert max(abs(esc.x - g.player.x), abs(esc.y - g.player.y)) == 1
    assert here is not None
    assert esc in g._escorts_here()


def test_monsters_swipe_at_escorts_for_half_damage_with_no_pet():
    from monster import Monster
    g = _game()
    esc = _start(g)
    assert g.pets == []
    defn = {'id': 'fx_brute', 'name': 'Brute', 'symbol': 'B', 'color': [200, 0, 0], 'hp': 50,
            'thac0': -20, 'speed': 0, 'attacks': [{'damage': '1d2+9'}], 'ai_pattern': 'sessile',
            'resistances': [], 'weaknesses': [], 'min_level': 1}
    spot = next((esc.x + dx, esc.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if (dx or dy) and g.dungeon.is_walkable(esc.x + dx, esc.y + dy)
                and (esc.x + dx, esc.y + dy) not in g._occupants())
    g.monsters = [Monster(defn, *spot)]
    hp = esc.hp
    g._monster_swipes(g._escorts_here(), escorts=True)
    assert esc.hp == hp - 5
    esc.hp = 3
    g.turn_count += 1          # a new turn: one swipe per monster per turn (PET-06)
    g._do_escort_turns()
    assert not esc.alive and g.escorts == []
    import deeds
    assert deeds.has(g._deeds, 'lost.lena')
    assert 'lost Lena on the stairs' in _chron(g)       # no left-behind flag: the plain line


def test_an_escort_never_regenerates():
    g = _game()
    esc = _start(g)
    esc.hp = 10
    for _ in range(30):
        g._do_escort_turns()
    assert esc.hp == 10


def test_the_perk_reveals_traps_within_sight():
    g = _game()
    esc = _start(g)
    g.dungeon.traps = {(esc.x + 1, esc.y): {'type': 'fire', 'revealed': False},
                       (esc.x + 40, esc.y + 40): {'type': 'fire', 'revealed': False}}
    g._do_escort_turns()
    assert g.dungeon.traps[(esc.x + 1, esc.y)]['revealed'] is True
    assert g.dungeon.traps[(esc.x + 40, esc.y + 40)]['revealed'] is False


def test_a_straggler_stops_and_waits():
    g = _game()
    esc = _start(g)
    esc.x, esc.y = g.player.x + 9, g.player.y
    esc.leash = 2

    class _Stuck:
        def is_walkable(self, *_a):
            return False
        pits, traps = set(), {}
    for _ in range(10):
        esc.take_turn(g.player, _Stuck(), [], [], [])
    assert esc.waiting
    esc.x, esc.y = g.player.x + 1, g.player.y
    esc.take_turn(g.player, g.dungeon, [], [], [])
    assert not esc.waiting


def test_settle_and_spawns_never_put_a_creature_on_an_escort():
    from monster import Monster
    g = _game()
    esc = _start(g)
    defn = {'id': 'fx_rat', 'name': 'Rat', 'symbol': 'r', 'color': [1, 1, 1], 'hp': 5,
            'thac0': 20, 'speed': 0, 'attacks': [{'damage': '1d2'}], 'ai_pattern': 'sessile',
            'resistances': [], 'weaknesses': [], 'min_level': 1}
    rat = Monster(defn, esc.x, esc.y)
    g.monsters = [rat]
    g._settle_monsters()
    assert (rat.x, rat.y) != (esc.x, esc.y)
    # an encounter NPC spawn never lands on the escort
    for i in range(20):
        g.monsters = []
        enc = copy.deepcopy(ESCORT_ENC)
        enc['tag'] = f'fx_npc_{i}'
        npc = g._spawn_encounter_npc(enc, '_flavor_encounter_tag', g.dungeon_level)
        assert (npc.x, npc.y) not in g._occupants()


def test_the_black_knight_spawn_counts_the_escort_as_a_body():
    g = _game(level=15)
    esc = _start(g)
    st = g._black_knight_state()
    st.update({'floor': 15, 'spawned': False})
    seen = []
    import black_knight as bk
    real = bk.find_site

    def spy(dungeon, start, rng, taken=(), **kw):
        seen.append(set(taken))
        return real(dungeon, start, rng, taken=taken, **kw)
    bk.find_site = spy
    try:
        g._maybe_spawn_black_knight(15)
    finally:
        bk.find_site = real
    assert seen and (esc.x, esc.y) in seen[0]
    knights = [m for m in g.monsters if getattr(m, 'is_black_knight', False)]
    assert all((k.x, k.y) != (esc.x, esc.y) for k in knights)


def test_a_tile_goal_succeeds_at_an_altar():
    import deeds
    from dungeon import ALTAR
    g = _game()
    _start(g, goal='tile:altar')
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR
    g._do_escort_turns()
    assert g.escorts == [] and deeds.has(g._deeds, 'saved.lena')


def test_walking_into_an_escort_swaps_places():
    g = _game()
    esc = _start(g)
    ox, oy = g.player.x, g.player.y
    ex, ey = esc.x, esc.y
    g._do_move(ex - ox, ey - oy)
    assert (g.player.x, g.player.y) == (ex, ey) and (esc.x, esc.y) == (ox, oy)


# --- CODE-01: escort AC is hero-style (lower is better, 10 is unarmoured) ---

def _shipped_escorts():
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if 'leash' in o and 'hp' in o and 'id' in o:
                out[o['id']] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for f in ('npc_encounters.json', 'flavor_encounters.json'):
        with open(os.path.join(root, 'data', f), encoding='utf-8') as fh:
            walk(json.load(fh))
    return out


def _hit_rate(spec, swipes=2000):
    import types
    from game_combat import CombatMixin
    from escort_system import Escort

    class _Rat:
        alive = True
        thac0 = 12
        is_allied = False
        x = y = 0
        name = 'rat'
        attacks = [{'damage': '1d2'}]

        def has_effect(self, e):
            return False

        def _is_named_foe(self):
            return False

    random.seed(5)
    esc = Escort(dict(spec, hp=10 ** 6), 1, 0)
    g = types.SimpleNamespace(monsters=[_Rat()], visible=set(),
                              player=types.SimpleNamespace(has_effect=lambda e: False),
                              add_message=lambda *a, **k: None)
    hits = 0
    for _ in range(swipes):
        hp0 = esc.hp
        CombatMixin._monster_swipes(g, [esc], escorts=True)
        hits += esc.hp < hp0
    return hits / swipes


def test_an_escort_without_an_ac_is_unarmoured():
    from escort_system import Escort
    spec = dict(LENA)
    spec.pop('ac')
    assert Escort(spec, 1, 0).ac == 10
    assert Escort(dict(LENA, ac=0), 1, 0).ac == 0


def test_shipped_escort_armour_reads_like_the_lore():
    esc = _shipped_escorts()
    for civilian in ('wynn', 'lena', 'quill'):
        assert esc[civilian]['ac'] >= 9, civilian
    assert esc['aristodemus']['ac'] <= 5
    assert esc['azarias']['ac'] < esc['aristodemus']['ac'] < esc['wynn']['ac']
    # Through the real swipe: the angel is the hardest to hit, the pilgrim the easiest.
    assert _hit_rate(esc['azarias']) < _hit_rate(esc['aristodemus']) < _hit_rate(esc['wynn'])


def test_the_validator_rejects_an_escort_ac_off_the_hero_scale():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.encounters import validate as V
    errs = []
    for bad in (15, -11, 'plate', 2.5):
        V._check_escort(lambda code, msg: errs.append((code, msg)), 'x', dict(LENA, ac=bad))
    assert len([e for e in errs if 'ac ' in e[1]]) == 4
    errs.clear()
    V._check_escort(lambda code, msg: errs.append((code, msg)), 'x', LENA)
    assert errs == []
