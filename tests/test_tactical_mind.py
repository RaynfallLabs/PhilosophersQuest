"""The Tactical Mind (AI-2, MONSTERS AND MAGIC, 2026-11-20).

Seeded, deterministic tests on hand-made maps and real kinds:
  * the pure scorer (src/tactics.py): table-driven Views per mind;
  * each tactic in a scene where it should fire, and where it must not (the
    wrong mind, a creature that cannot act, a hero it cannot see);
  * Wait Your Turn and Archers Find a Lane (every hunter, every archer);
  * The Captain's Orders, Go for the Weak One, Dark Edges and Doorways,
    Over Their Own Snares, Feigned Flight, They Learn Your Tricks;
  * the edges: a leader who dies mid-plan, a hero who leaves the floor
    mid-plan, save and load mid-plan, an old save, a crowded floor's time,
    a creature with no family, every kind that must never think;
  * the data, the tells and the Bestiary lines.
"""
import json
import os
import pickle
import random
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import ai_lines  # noqa: E402
import habits  # noqa: E402
import lanes  # noqa: E402
import senses  # noqa: E402
import tactical_mind as tm  # noqa: E402
import tactics  # noqa: E402
import tells  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
MINDS = json.load(open(os.path.join(ROOT, 'data', 'minds.json'), encoding='utf-8'))


class Hero:
    """Enough of a hero for the monster's side of a fight."""
    def __init__(self, x=10, y=10, hp=200, sight=5):
        self.x, self.y = x, y
        self.hp = self.max_hp = hp
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.shield = None
        self.weapon = None
        self.armor_slots = []
        self.inventory = []
        self.sight = sight
        self.studied_kinds = set()

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self, extra_light=0):
        return self.sight

    def take_damage(self, amount, damage_type='physical'):
        actual = max(0, int(amount))
        self.hp = max(0, self.hp - actual)
        return actual

    def save_bonus_for(self, _stat):
        return 0

    def add_effect(self, name, duration):
        self.status_effects[name] = duration
        return True


class Pet:
    def __init__(self, x, y, hp=30, max_hp=100, name='Rex', **flags):
        self.x, self.y = x, y
        self.hp, self.max_hp = hp, max_hp
        self.name = name
        self.alive = True
        for k, v in flags.items():
            setattr(self, k, v)


def grid(rows):
    """A floor from rows: '#' rock, anything else floor."""
    h, w = len(rows), len(rows[0])
    tiles = [[WALL if c == '#' else FLOOR for c in r] for r in rows]
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, 5)


def open_room(w=20, h=14):
    return grid(['#' * w] + ['#' + '.' * (w - 2) + '#' for _ in range(h - 2)] + ['#' * w])


# A room (x 1-6) with a corridor running east from its middle (y 4).
ROOM_AND_CORRIDOR = [
    "####################",
    "#......#############",
    "#......#############",
    "#......#############",
    "#..................#",
    "#......#############",
    "#......#############",
    "#......#############",
    "####################",
]


def make(kind, x, y, **extra):
    d = {**MONS[kind], 'id': kind}
    d.update(extra)
    m = Monster(d, x, y)
    m._aware = True
    m._tracking = True
    m._alerted = True
    m._opened = True            # its opener spent: these scenes are about the turns after
    return m


def stub(**over):
    base = {'id': 'test_mob', 'name': 'test mob', 'symbol': 'M', 'color': [200, 200, 200],
            'ai_pattern': 'aggressive', 'hp': '60', 'speed': 10, 'thac0': 1,
            'attacks': [{'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'}],
            'tags': ['beast']}
    base.update(over)
    x, y = base.pop('x', 5), base.pop('y', 5)
    m = Monster(base, x, y)
    m._aware = m._tracking = True
    return m


class _Game:
    def __init__(self, pets=(), turn=0):
        self.pets = list(pets)
        self.turn_count = turn


def setup_function(_):
    random.seed(7)
    senses.begin_turn(moved=False, guilty=False, floor=5)
    tm.TURN.__init__()
    tm.ENABLED = True
    tm.OFF.clear()
    lanes.ENABLED = True
    senses.QUEUE = True
    tactics.reload()


_CLOCK = [100]


def turns(mons, hero, d, n, pets=()):
    """n rounds of every monster's turn, as the game runs them."""
    got = []
    for _i in range(n):
        _CLOCK[0] += 1
        tm.begin_turn(_Game(pets, turn=_CLOCK[0]))
        for m in mons:
            if m.alive:
                got.append((m, m.take_turn(hero, d, mons, extra_occupied={(p.x, p.y) for p in pets})))
    return got


def said(m) -> list:
    return [s for s, _u, _c in ai_lines.take(m)]


# ===========================================================================
# The pure scorer
# ===========================================================================

def V(**kw):
    return tactics.View(**kw)


def S(mind):
    return tactics.spec(mind)


def test_no_mind_no_layer_and_attack_wins_every_tie():
    assert tactics.decide(V(dist=3, coming=2), {})[0] == 'attack'
    for kind in ('wolf', 'giant_rat', 'zombie', 'cave_bear', 'gelatinous_cube'):
        assert tm.mind_of(make(kind, 2, 2)) is None, kind
    # The caster weighs holding a choke as much as striking: a tie, it strikes.
    assert tactics.decide(V(mind='caster', dist=3, choke=True), S('caster'))[0] == 'attack'


def test_cunning_waits_for_friends_coming_up_and_holds_a_choke():
    assert tactics.decide(V(mind='cunning', dist=3, coming=1), S('cunning'))[0] == 'wait_allies'
    assert tactics.decide(V(mind='cunning', dist=3, choke=True), S('cunning'))[0] == 'hold_choke'
    assert tactics.decide(V(mind='soldier', dist=3, choke=True), S('soldier'))[0] == 'hold_choke'
    # Nobody coming, nothing to hold: it comes on.
    assert tactics.decide(V(mind='cunning', dist=3), S('cunning'))[0] == 'attack'


def test_patience_a_wound_or_a_clear_shot_ends_the_hold():
    sp = S('cunning')
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, waited=10), sp)[0] == 'attack'
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, hurt_lately=True), sp)[0] == 'attack'
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, has_lane=True), sp)[0] == 'attack'


def test_a_badly_hurt_or_held_hero_is_pressed_and_a_charge_order_presses_all():
    sp = S('cunning')
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, hero_hp_share=0.2), sp)[0] == 'attack'
    assert tactics.decide(V(mind='cunning', dist=3, coming=1, hero_held=True), sp)[0] == 'attack'
    # Unseen, his wounds are not known: no press.
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, hero_hp_share=0.2,
                            sees_hero=False), sp)[0] == 'hold_choke'
    assert tactics.decide(V(mind='soldier', dist=3, choke=True, order='charge'), S('soldier'))[0] == 'attack'


def test_beside_the_hero_it_strikes_unless_it_rotates_feints_or_goes_for_the_pet():
    assert tactics.decide(V(mind='soldier', dist=1, adjacent=True, choke=True), S('soldier'))[0] == 'attack'
    assert tactics.decide(V(mind='soldier', dist=1, adjacent=True, rotate_ok=True), S('soldier'))[0] == 'rotate'
    assert tactics.decide(V(mind='cunning', dist=1, adjacent=True, rotate_ok=True), S('cunning'))[0] == 'attack'
    assert tactics.decide(V(mind='soldier', dist=1, adjacent=True, feint_ok=True), S('soldier'))[0] == 'feint'
    assert tactics.decide(V(mind='cunning', dist=1, adjacent=True, pet_target=True), S('cunning'))[0] == 'focus_pet'
    assert tactics.decide(V(mind='soldier', dist=1, adjacent=True, pet_target=True), S('soldier'))[0] == 'attack'


def test_a_plan_holds_two_turns_and_breaks_when_the_hero_comes_beside_it():
    sp = S('cunning')
    plan = tactics.new_plan('wait_allies')
    assert plan['left'] == 2
    v = V(mind='cunning', dist=3, coming=1)
    assert tactics.decide(v, sp, plan)[0] == 'wait_allies'
    plan = tactics.spend(plan)
    assert plan['left'] == 1 and tactics.keep_plan(plan, v, sp)
    assert tactics.spend(plan) is None
    assert not tactics.keep_plan(plan, V(mind='cunning', dist=1, adjacent=True, coming=1), sp)
    assert not tactics.keep_plan(plan, V(mind='cunning', dist=3), sp)          # no longer open


def test_the_choice_is_the_same_for_the_same_view():
    v = V(mind='trickster', dist=3, engaged=1, flank_spot=True, coming=1)
    a = [tactics.decide(v, S('trickster')) for _ in range(5)]
    assert all(x == a[0] for x in a)


def test_habits_seen_change_the_weights():
    sp = S('cunning')
    base = tactics.scores(V(mind='cunning', dist=3, choke=True), sp)['hold_choke']
    hard = tactics.scores(V(mind='cunning', dist=3, choke=True, habit_choke=2), sp)['hold_choke']
    assert hard > base
    # A kiter seen twice: they no longer stand to be shot.
    assert tactics.decide(V(mind='cunning', dist=3, choke=True, habit_kiter=2), sp)[0] == 'attack'
    assert tactics.decide(V(mind='cunning', dist=3, coming=1, habit_kiter=2), sp)[0] == 'attack'
    # A hero seen resting with foes about is rushed when he rests.
    assert tactics.decide(V(mind='cunning', dist=3, coming=1, hero_resting=True, habit_rest=2),
                          sp)[0] == 'attack'


def test_the_dark_edge_rules():
    sp = S('trickster')
    base = dict(mind='trickster', dark_edge=True, dist=4, hero_sight=5)
    assert tactics.decide(V(in_his_sight=True, dark_tile=True, **base), sp)[0] == 'leave_light'
    assert tactics.decide(V(in_his_sight=True, dark_tile=False, **base), sp)[0] == 'attack'
    assert tactics.decide(V(in_his_sight=True, dark_tile=True, edge_retreats=3, **base), sp)[0] == 'attack'
    lurk = dict(base, dist=7)
    assert tactics.decide(V(**lurk), sp)[0] == 'leave_light'                # lurks at the edge
    assert tactics.decide(V(waited=10, **lurk), sp)[0] == 'attack'          # patience gone
    assert tactics.decide(V(has_lane=True, **lurk), sp)[0] == 'attack'      # an archer shoots
    assert tactics.decide(V(**dict(base, dist=2)), sp)[0] == 'leave_light'  # strikes from the dark
    assert tactics.decide(V(dark_struck=True, **dict(base, dist=2)), sp)[0] == 'attack'
    assert tactics.decide(V(**dict(base, dark_edge=False, in_his_sight=True, dark_tile=True)),
                          sp)[0] == 'attack'


# ===========================================================================
# Who thinks
# ===========================================================================

EXCLUDED_FLAGS = [
    {'is_boss': True}, {'is_mini_boss': True}, {'is_seal_demon': True}, {'is_allied': True},
    {'_npc_encounter_tag': 'x'}, {'_flavor_encounter_tag': 'x'}, {'_is_unicorn': True},
    {'stalker': {'friend_keep': 2}}, {'_is_abandoned_emberpup': True}, {'_called_ally': True},
]


def test_every_kind_that_must_never_think_does_not():
    hero = Hero(9, 4)
    for flags in EXCLUDED_FLAGS:
        m = make('hobgoblin', 6, 4)
        for k, v in flags.items():
            setattr(m, k, v)
        assert not tm.thinks(m, hero), flags
    death = make('hobgoblin', 6, 4)
    death.kind = 'death'
    assert not tm.thinks(death, hero)
    nickel = make('hobgoblin', 6, 4)
    nickel.ai_pattern = 'stalker_coward'
    assert not tm.thinks(nickel, hero)
    legend = make('hobgoblin', 6, 4)
    legend.tags = list(legend.tags) + ['legendary']
    assert not tm.thinks(legend, hero)
    assert tm.thinks(make('hobgoblin', 6, 4), hero)


def test_a_creature_that_cannot_act_or_is_broken_does_not_plan():
    hero = Hero(9, 4)
    for eff in tm.CANNOT + ('feared',):
        m = make('hobgoblin', 6, 4)
        m.status_effects[eff] = 3
        assert not tm.thinks(m, hero), eff
    for k, v in (('_flee_timer', 4), ('_at_bay', 2), ('_yielded', True), ('_cowed', True),
                 ('stolen_gold', 10)):
        m = make('hobgoblin', 6, 4)
        setattr(m, k, v)
        assert not tm.thinks(m, hero), k


def test_a_pack_hunter_keeps_its_packs_brain_and_a_band_goblin_thinks():
    hero = Hero(9, 4)
    g = make('goblin', 6, 4)
    assert not tm.thinks(g, hero)                         # the goblin pack's hunt
    g._band = 'b@1'
    assert tm.thinks(g, hero)                             # a band's goblin has no pack


def test_a_creature_with_no_family_or_no_mind_runs_todays_code():
    d = open_room()
    hero = Hero(12, 6)
    m = stub(x=6, y=6)
    m.__dict__.pop('family', None)
    assert tm.mind_of(m) is None
    m.take_turn(hero, d, [m])
    assert '_tm_plan' not in m.__dict__ and (m.x, m.y) != (6, 6)


# ===========================================================================
# Wait at the Mouth (hold_choke)
# ===========================================================================

def _corridor_scene(kind='hobgoblin', n=3):
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(10, 4)                                    # in the corridor
    mons = [make(kind, 4, 4 + dy) for dy in (0, -1, 1)][:n]
    return d, hero, mons


def test_a_band_holds_the_room_rather_than_file_into_a_corridor():
    d, hero, mons = _corridor_scene()
    patience = int(MINDS['patience'])
    for _ in range(patience - 2):
        turns(mons, hero, d, 1)
        assert all(m.x <= 7 for m in mons), [(m.x, m.y) for m in mons]
        assert not any(m._adjacent_to(hero) for m in mons)
    lines = [s for m in mons for s in said(m)]
    assert any('will not follow you into the narrow way' in s for s in lines), lines
    # Its patience runs out: they come (no stalemate).
    turns(mons, hero, d, patience + 8)
    assert any(m.x >= 8 for m in mons)


def test_a_beast_files_into_the_corridor():
    d, hero, mons = _corridor_scene('cave_bear', n=1)
    turns(mons, hero, d, 4)
    assert mons[0].x >= 7 and '_tm_plan' not in mons[0].__dict__


def test_a_held_hobgoblin_makes_no_plan_and_an_unseen_hero_teaches_no_hold():
    d, hero, mons = _corridor_scene(n=1)
    mons[0].status_effects['paralyzed'] = 5
    turns(mons, hero, d, 2)
    assert (mons[0].x, mons[0].y) == (4, 4) and not mons[0].__dict__.get('_tm_used')
    d, hero, mons = _corridor_scene(n=1)
    hero.status_effects['invisible'] = 50
    mons[0]._tracking = False
    turns(mons, hero, d, 3)
    assert not mons[0].__dict__.get('_tm_used')


# ===========================================================================
# Wait for numbers, come round
# ===========================================================================

def test_a_bandit_waits_for_the_friend_coming_up_behind_him():
    d = open_room()
    hero = Hero(14, 6)
    front = make('bandit_thug', 11, 6)
    back = make('bandit_thug', 4, 6)
    front.take_turn(hero, d, [front, back])
    assert front.__dict__.get('_tm_last') == 'wait_allies'
    assert max(abs(front.x - hero.x), abs(front.y - hero.y)) >= 3
    assert any('waiting for the others' in s for s in said(front))
    # Alone, he comes on.
    alone = make('bandit_thug', 11, 6)
    alone.take_turn(hero, d, [alone])
    assert alone.__dict__.get('_tm_last') in (None, 'attack')
    assert max(abs(alone.x - hero.x), abs(alone.y - hero.y)) == 2


def test_a_trickster_comes_round_to_the_far_side():
    d = open_room()
    hero = Hero(10, 6)
    on_him = make('huldufolk_raider', 9, 6)              # on his west side
    other = make('huldufolk_raider', 7, 6)
    mons = [on_him, other]
    other.take_turn(hero, d, mons)
    assert other.__dict__.get('_tm_last') == 'flank', other.__dict__.get('_tm_last')
    # It went round, not to the tile behind its friend.
    assert (other.x, other.y) != (8, 6)


# ===========================================================================
# Wait Your Turn (every hunter) and the soldiers' rotation
# ===========================================================================

LONG_CORRIDOR = [
    "####################",
    "#..................#",
    "#.################.#",
    "#.################.#",
    "#.################.#",
    "#.################.#",
    "#..................#",
    "####################",
]


def test_find_path_keeps_to_its_budget():
    d = grid(LONG_CORRIDOR)
    m = stub(x=3, y=1)
    full = senses.find_path(m, d, (16, 6))
    assert full and len(full) > 10
    assert senses.find_path(m, d, (16, 6), max_len=8) is None


def test_a_hunter_waits_its_turn_behind_a_friend_and_takes_no_long_detour():
    d = grid(LONG_CORRIDOR)
    hero = Hero(9, 1)
    front = stub(x=8, y=1, family='mortals')
    second = stub(x=7, y=1, family='mortals')
    calls = {'n': 0}
    real = senses.find_path

    def counting(*a, **k):
        calls['n'] += 1
        return real(*a, **k)
    senses.find_path = counting
    try:
        for _ in range(4):
            second.take_turn(hero, d, [front, second])
    finally:
        senses.find_path = real
    assert (second.x, second.y) == (7, 1)                 # it waited, no detour round the loop
    assert calls['n'] <= 3                                # and searched once, not every turn
    # Its friend falls: it steps up at once.
    front.alive = False
    second.take_turn(hero, d, [front, second])
    assert (second.x, second.y) == (8, 1)


def test_without_the_queue_the_same_hunter_walks_the_long_way_round():
    senses.QUEUE = False
    d = grid(LONG_CORRIDOR)
    hero = Hero(9, 1)
    front = stub(x=8, y=1, family='mortals')
    second = stub(x=7, y=1, family='mortals')
    for _ in range(3):
        second.take_turn(hero, d, [front, second])
    assert (second.x, second.y) != (7, 1)


def test_a_hurt_soldier_changes_places_with_a_fresh_one():
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(10, 4)
    front = make('orc_warrior', 9, 4)
    fresh = make('orc_warrior', 8, 4)
    front.hp = int(front.max_hp * 0.3)
    front.take_turn(hero, d, [front, fresh])
    assert (front.x, front.y) == (8, 4) and (fresh.x, fresh.y) == (9, 4)
    assert any('fresh fighter' in s for s in said(front))


def test_no_rotation_for_a_cunning_bandit_or_with_a_held_friend():
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(10, 4)
    front = make('bandit_thug', 9, 4)
    other = make('bandit_thug', 8, 4)
    front.hp = int(front.max_hp * 0.3)
    front.take_turn(hero, d, [front, other])
    assert (front.x, front.y) == (9, 4)
    front = make('orc_warrior', 9, 4)
    fresh = make('orc_warrior', 8, 4)
    front.hp = int(front.max_hp * 0.3)
    fresh.status_effects['stunned'] = 3
    front.take_turn(hero, d, [front, fresh])
    assert (front.x, front.y) == (9, 4)


# ===========================================================================
# Archers Find a Lane
# ===========================================================================

def test_each_missile_reaches_as_its_weapon_does():
    assert lanes.attack_range({'name': 'Yew Longbow'}) == 8
    assert lanes.attack_range({'name': 'Sling Stone'}) == 5
    assert lanes.attack_range({'name': 'Dagger Throw'}) == 4
    assert lanes.attack_range({'name': 'Shortbow'}) == 6
    assert lanes.attack_range({'name': 'Hand Crossbow'}) == 5
    assert lanes.attack_range({'name': 'Fire Bolt'}) == 6
    assert lanes.attack_range({'name': 'Sling Stone', 'range': 3}) == 3


def test_a_slinger_does_not_fire_beyond_its_reach():
    d = open_room()
    hero = Hero(15, 6)
    m = stub(x=9, y=6, ai_pattern='ranged',
             attacks=[{'name': 'Sling Stone', 'damage': '1d3', 'type': 'blunt', 'ranged': True},
                      {'name': 'Knife', 'damage': '1d3', 'type': 'pierce'}])
    assert m.take_turn(hero, d, [m]) is not True           # 6 tiles: out of a sling's reach
    m2 = stub(x=10, y=6, ai_pattern='ranged',
              attacks=[{'name': 'Sling Stone', 'damage': '1d3', 'type': 'blunt', 'ranged': True},
                       {'name': 'Knife', 'damage': '1d3', 'type': 'pierce'}])
    assert m2.take_turn(hero, d, [m2]) is True             # 5: it fires


def test_an_archer_behind_its_swordsman_steps_to_a_lane_not_into_melee():
    d = open_room()
    hero = Hero(14, 6)
    sword = make('orc_warrior', 13, 6)
    archer = make('bandit_archer', 10, 6)
    lanes_before = (archer.x, archer.y)
    archer.take_turn(hero, d, [sword, archer])
    assert (archer.x, archer.y) != lanes_before
    assert max(abs(archer.x - hero.x), abs(archer.y - hero.y)) >= 3
    archer.take_turn(hero, d, [sword, archer])            # a lane may be two steps off
    assert max(abs(archer.x - hero.x), abs(archer.y - hero.y)) >= 3
    assert lanes.clear_shot(archer.x, archer.y, hero.x, hero.y, d, {(sword.x, sword.y)})


def test_beside_the_hero_an_archer_steps_back_twice_then_fights():
    d = open_room()
    hero = Hero(10, 6)
    archer = make('bandit_archer', 9, 6)
    got = []
    for _ in range(3):
        got.append(archer.take_turn(hero, d, [archer]))
        hero.x, hero.y = archer.x + 1, archer.y             # the hero keeps after it
    assert got[:2] == [False, False] and got[2] is True


def test_an_unstrung_archer_has_no_lane():
    d = open_room()
    hero = Hero(14, 6)
    sword = make('orc_warrior', 13, 6)
    archer = make('bandit_archer', 10, 6)
    archer.status_effects['unstrung'] = 5
    assert lanes.usable(archer) == []
    assert lanes.blocked_turn(archer, hero, d, [sword, archer], set()) in (None, False)
    assert not lanes.find_lane(archer, hero, d, [sword, archer], set()) or not lanes.usable(archer)


def test_a_healer_borrowing_the_ranged_turn_keeps_beside_its_friends():
    assert not lanes.applies(make('orc_priest', 5, 5))
    assert lanes.applies(make('bandit_archer', 5, 5))


# ===========================================================================
# The Captain's Orders
# ===========================================================================

def _band(d, hero, guards=2, leader_kind='hobgoblin_captain', guard_kind='hobgoblin'):
    uid = 'goblin_raiders@1,1'
    lead = make(leader_kind, 3, 4)
    lead._band, lead._band_id, lead._band_role = uid, 'goblin_raiders', 'leader'
    mem = [lead]
    for i in range(guards):
        g = make(guard_kind, 2, 2 + 4 * i)
        g._band, g._band_id, g._band_role, g._band_leader = uid, 'goblin_raiders', 'guard', lead
        mem.append(g)
    d.band = {'id': 'goblin_raiders', 'uid': uid, 'room': (0, 0, 8, 9),
              'counts': {'guard': guards, 'shooter': 0, 'caster': 0, 'healer': 0}}
    return mem


def test_the_captain_orders_a_screen_then_the_charge_then_the_pull_back():
    d = open_room()
    hero = Hero(9, 4)
    mem = _band(d, hero, guards=3)
    lead = mem[0]
    assert tm.band_order(mem[1], hero, d, mem) == 'screen'
    assert any('Shields to me' in s for s in said(lead))
    hero.hp = int(hero.max_hp * 0.3)
    assert tm.band_order(mem[1], hero, d, mem) == 'charge'
    hero.hp = hero.max_hp
    mem[2].alive = mem[3].alive = False                   # half the band down
    assert tm.band_order(mem[1], hero, d, mem) == 'fall_back'


def test_a_silenced_held_or_dead_captain_gives_no_order():
    for eff in ('silenced', 'paralyzed', 'feared', 'babbled', 'sleeping'):
        d = open_room()
        hero = Hero(9, 4)
        mem = _band(d, hero)
        mem[0].status_effects[eff] = 4
        assert tm.band_order(mem[1], hero, d, mem) == '', eff
    d = open_room()
    hero = Hero(9, 4)
    mem = _band(d, hero)
    mem[0].alive = False
    assert tm.band_order(mem[1], hero, d, mem) == ''


def test_guards_come_between_the_hero_and_their_captain():
    d = open_room()
    hero = Hero(9, 4)
    mem = _band(d, hero)
    lead = mem[0]
    for i in range(3):
        tm.TURN.n = 50 + i
        for m in mem:
            m.take_turn(hero, d, mem)
    guards = mem[1:]
    # A guard stands next to the captain on the hero's side of him.
    assert any(max(abs(g.x - lead.x), abs(g.y - lead.y)) <= 2 and g.x > lead.x for g in guards), \
        [(g.x, g.y) for g in guards]


def test_a_leader_who_dies_mid_plan_leaves_no_orders_behind():
    d = open_room()
    hero = Hero(9, 4)
    mem = _band(d, hero)
    tm.TURN.n = 10
    for m in mem:
        m.take_turn(hero, d, mem)
    mem[0].alive = False
    for m in mem[1:]:
        m._band_leader = None                             # war_bands.on_death does this
    tm.TURN.n = 11
    assert tm.band_order(mem[1], hero, d, mem) == ''
    for m in mem[1:]:
        m.take_turn(hero, d, mem)                         # no crash, plain minds now
    assert d.band['order'] == ''


# ===========================================================================
# Go for the Weak One
# ===========================================================================

def test_a_gnoll_lord_turns_on_a_badly_hurt_pet():
    d = open_room()
    hero = Hero(10, 6)
    pet = Pet(8, 6, hp=25, max_hp=100)
    m = make('gnoll_pack_lord', 7, 6)
    tm.begin_turn(_Game([pet]))
    got = m.take_turn(hero, d, [m], extra_occupied={(pet.x, pet.y)})
    assert got is False and tm.focus_of(m) == id(pet)
    assert any('hurt' in s for s in said(m))


def test_no_focus_on_the_unicorn_a_ridden_bococho_dad_or_a_healthy_pet():
    for flags in ({'is_unicorn': True}, {'ridden': True}, {'is_dad': True}, {'hp': 90}):
        d = open_room()
        hero = Hero(10, 6)
        kw = {'hp': flags.pop('hp', 25)}
        pet = Pet(8, 6, **kw, **flags)
        m = make('gnoll_pack_lord', 7, 6)
        tm.begin_turn(_Game([pet]))
        m.take_turn(hero, d, [m], extra_occupied={(pet.x, pet.y)})
        assert tm.focus_of(m) is None, flags


def test_a_hero_himself_badly_hurt_is_the_target_not_the_pet():
    d = open_room()
    hero = Hero(10, 6)
    hero.hp = int(hero.max_hp * 0.3)
    pet = Pet(8, 6, hp=20)
    m = make('gnoll_pack_lord', 7, 6)
    tm.begin_turn(_Game([pet]))
    m.take_turn(hero, d, [m], extra_occupied={(pet.x, pet.y)})
    assert tm.focus_of(m) is None


def test_never_more_than_half_of_those_that_see_the_pet_go_for_it():
    d = open_room()
    hero = Hero(14, 6)
    pet = Pet(8, 6, hp=20)
    mons = [make('gnoll_pack_lord', 6, y) for y in (4, 5, 7, 8)]
    tm.begin_turn(_Game([pet]))
    for m in mons:
        m.take_turn(hero, d, mons, extra_occupied={(pet.x, pet.y)})
    went = sum(1 for m in mons if m.__dict__.get('_tm_last') == 'focus_pet')
    assert 1 <= went <= 2


def test_the_swipe_pass_gives_the_chosen_pet_a_whole_blow():
    from game_combat import CombatMixin

    class G:
        turn_count = 5
        visible = set()

        def __init__(self, mons, hero):
            self.monsters = mons
            self.player = hero
            self.msgs = []

        def add_message(self, t, c=''):
            self.msgs.append(t)

        def _say_springs(self):
            pass
    hero = Hero(10, 6)
    pet = Pet(9, 7, hp=20, max_hp=100)
    pet.take_damage = lambda n: setattr(pet, 'hp', pet.hp - n)
    m = make('gnoll_pack_lord', 9, 6, attacks=[{'name': 'Glaive', 'damage': '1d2+9', 'type': 'slash'}])
    m._focus = id(pet)
    g = G([m], hero)
    CombatMixin._monster_swipes(g, [pet])
    assert pet.hp <= 10                                   # its whole blow (10-11), not half


# ===========================================================================
# Dark Edges and Doorways
# ===========================================================================

def test_a_drow_steps_out_of_an_unlit_heros_sight():
    d = open_room(24, 14)
    hero = Hero(6, 6, sight=5)
    drow = make('drow_warrior', 10, 6)
    drow.take_turn(hero, d, [drow])
    assert drow.__dict__.get('_tm_last') == 'leave_light'
    drow.take_turn(hero, d, [drow])                       # the dark is two steps off
    assert max(abs(drow.x - hero.x), abs(drow.y - hero.y)) > 5
    assert any('edge of your light' in s for s in said(drow))


def test_a_bright_light_leaves_the_drow_nowhere_to_hide():
    d = open_room(24, 14)
    hero = Hero(6, 6, sight=11)
    drow = make('drow_warrior', 10, 6)
    drow.take_turn(hero, d, [drow])
    assert drow.__dict__.get('_tm_last') != 'leave_light'


def test_a_hobgoblin_or_a_blind_drow_does_not_seek_the_dark():
    d = open_room(24, 14)
    hero = Hero(6, 6, sight=5)
    hob = make('hobgoblin', 10, 6)
    hob.take_turn(hero, d, [hob])
    assert hob.__dict__.get('_tm_last') != 'leave_light'
    drow = make('drow_warrior', 10, 6)
    drow.status_effects['blinded'] = 4
    assert not tm.thinks(drow, hero)


def test_a_hurt_soldier_backs_into_a_doorway():
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(3, 4)
    m = make('hobgoblin', 6, 4)
    m.hp = int(m.max_hp * 0.4)
    m.take_turn(hero, d, [m])
    assert m.__dict__.get('_tm_last') == 'hold_door' and (m.x, m.y) == (7, 4)
    assert tm.narrow(d, m.x, m.y)


def test_a_door_is_held_ten_turns_at_most():
    v = tactics.View(mind='soldier', dist=3, door_tile=True, hp_share=0.3, door_turns=10)
    assert tactics.decide(v, tactics.spec('soldier'))[0] == 'attack'


# ===========================================================================
# Over Their Own Snares
# ===========================================================================

def test_a_kobold_waits_beyond_a_trap_it_knows():
    d = open_room()
    hero = Hero(4, 6)
    d.traps = {(6, 6): {'name': 'Snare', 'revealed': True}}
    m = make('kobold_pack_leader', 9, 6)
    m.take_turn(hero, d, [m])
    assert m.__dict__.get('_tm_last') == 'bait', m.__dict__.get('_tm_last')
    line = tm.line_tiles(hero.x, hero.y, m.x, m.y)
    assert (6, 6) in line or m.__dict__.get('_tm_plan')


def test_a_kobold_s_path_keeps_off_a_known_snare_when_it_can():
    d = open_room()
    d.traps = {(6, 6): {'name': 'Snare', 'revealed': False}}
    m = make('kobold_pack_leader', 4, 6)
    path = senses.find_path(m, d, (8, 6), avoid=lambda x, y: (x, y) in d.traps)
    assert (6, 6) not in path


def test_a_hero_s_rewired_trap_is_no_bait_and_a_hobgoblin_knows_no_snares():
    d = open_room()
    hero = Hero(4, 6)
    d.traps = {(6, 6): {'name': 'Snare', 'revealed': True, 'safe_for_player': True}}
    m = make('kobold_pack_leader', 9, 6)
    m.take_turn(hero, d, [m])
    assert m.__dict__.get('_tm_last') != 'bait'
    d.traps = {(6, 6): {'name': 'Snare', 'revealed': True}}
    hob = make('hobgoblin', 9, 6)
    hob.take_turn(hero, d, [hob])
    assert hob.__dict__.get('_tm_last') != 'bait'


# ===========================================================================
# Feigned Flight
# ===========================================================================

def _feint_scene(known=False):
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(8, 4)                                     # one tile into the corridor
    mem = _band(d, hero, guards=3)
    lead = mem[0]
    lead.x, lead.y = 2, 4
    front, a, b = mem[1], mem[2], mem[3]
    front.x, front.y = 7, 4                               # at the mouth, on him
    a.x, a.y = 5, 2
    b.x, b.y = 5, 6
    if known:
        hero.status_effects = {}
    return d, hero, mem, front


def test_soldiers_feign_flight_and_the_ones_waiting_strike_the_hero_who_follows():
    d, hero, mem, front = _feint_scene()
    tm.TURN.n = 200
    got = front.take_turn(hero, d, mem)
    assert got is False and front.__dict__.get('_tm_last') == 'feint'
    assert d.band.get('feinted')
    assert any('breaks and runs' in s for s in said(front))
    waiters = [m for m in mem if m.__dict__.get('_tm_feint')]
    assert len(waiters) >= 2
    for i in range(3):
        tm.TURN.n = 201 + i
        for m in mem:
            m.take_turn(hero, d, mem)
    # The hero steps out of the corridor after the runner.
    hero.x, hero.y = 6, 4
    struck = []
    tm.TURN.n = 205
    for m in waiters:
        if m._adjacent_to(hero):
            if m.take_turn(hero, d, mem) is True:
                struck.append(m)
                assert tm.hit_shift(m) == -2
    assert struck, [(m.x, m.y) for m in waiters]


def test_a_feint_comes_once_a_band_a_floor():
    d, hero, mem, front = _feint_scene()
    d.band['feinted'] = True
    front.take_turn(hero, d, mem)
    assert front.__dict__.get('_tm_last') != 'feint'


def test_a_hero_who_knows_the_kind_is_told_it_is_a_feint():
    import family_lore
    d, hero, mem, front = _feint_scene()
    real = family_lore.knowledge
    family_lore.knowledge = lambda p, k: family_lore.KNOWN
    try:
        front.take_turn(hero, d, mem)
    finally:
        family_lore.knowledge = real
    assert any('too neatly' in s for s in said(front))


# ===========================================================================
# They Learn Your Tricks
# ===========================================================================

def test_two_corridor_fights_seen_by_kobolds_teach_the_kobolds_not_the_orcs():
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(9, 4)
    kob = make('kobold_pack_leader', 5, 4)
    orc = make('orc_warrior', 5, 3)
    orc.family = 'giants'                                 # another side
    seen = habits.witnesses([kob], hero, d)
    habits.note(d, 'choke_fighter', seen, 10)
    habits.note(d, 'choke_fighter', seen, 20)             # the same fight: not counted twice
    habits.note(d, 'choke_fighter', seen, 60)
    assert habits.count(d, kob, 'choke_fighter', 60) == 2
    assert habits.count(d, orc, 'choke_fighter', 60) == 0
    assert habits.count(d, kob, 'choke_fighter', 500) == 0  # forgotten after 300 turns


def test_an_invisible_hero_teaches_nothing_and_a_beast_learns_nothing():
    d = open_room()
    hero = Hero(9, 4)
    hero.status_effects['invisible'] = 10
    assert habits.witnesses([make('kobold_pack_leader', 7, 4)], hero, d) == []
    hero.status_effects = {}
    assert habits.witnesses([make('cave_bear', 7, 4)], hero, d) == []


def test_after_the_corridor_trick_a_kobold_holds_harder_and_says_so():
    d, hero, mons = _corridor_scene('kobold_pack_leader', n=1)
    habits.note(d, 'choke_fighter', mons, 10)
    habits.note(d, 'choke_fighter', mons, 60)
    tm.TURN.n = 70
    mons[0].take_turn(hero, d, mons)
    assert any('corridor trick' in s for s in said(mons[0]))


def test_the_games_hooks_note_the_heros_habits():
    class G:
        def __init__(self, d, hero, mons):
            self.dungeon, self.player, self.monsters = d, hero, mons
            self.turn_count = 40
            self._damage_by = 'hero'
    d = grid(ROOM_AND_CORRIDOR)
    hero = Hero(9, 4)
    kob = make('kobold_pack_leader', 6, 4)
    g = G(d, hero, [kob])
    assert habits.hero_melee(g, kob)                      # from the corridor
    far = make('kobold_pack_leader', 3, 4)
    g.turn_count = 100
    assert habits.hero_shot(g, far)
    a, b = make('kobold', 6, 3), make('kobold', 6, 5)
    g.turn_count = 200
    assert habits.hero_struck(g, a) == []
    assert habits.hero_struck(g, b)                       # two in one turn: a blast
    a._dot_tick = True
    g.turn_count = 300
    assert habits.hero_struck(g, a) == [] and habits.hero_struck(g, a) == []


# ===========================================================================
# G's gates and AI-1's morale
# ===========================================================================

def test_a_silenced_or_unstrung_caster_casts_nothing():
    d = open_room()
    hero = Hero(12, 6)
    m = make('kobold_sorcerer', 7, 6)
    assert tm.castable(m, hero, d, [m])
    m.status_effects['silenced'] = 4
    assert tm.castable(m, hero, d, [m]) == []
    m.status_effects = {'unstrung': 4}
    assert tm.castable(m, hero, d, [m]) == []


def test_a_caster_mind_casts_through_choose_cast():
    d = open_room()
    hero = Hero(12, 6)
    m = make('kobold_sorcerer', 7, 6)
    got = m.take_turn(hero, d, [m])
    assert got is True and m.__dict__.get('_tm_last') == 'cast'
    assert m.__dict__.get('_pack_blow') in tm.castable(m, hero, d, [m])


def test_a_yielded_bandit_never_focuses_or_plans():
    hero = Hero(10, 6)
    m = make('bandit_thug', 7, 6)
    m._yielded = True
    assert not tm.thinks(m, hero)


# ===========================================================================
# The edges
# ===========================================================================

def test_the_hero_leaving_mid_plan_drops_the_plan():
    d, hero, mons = _corridor_scene(n=1)
    turns(mons, hero, d, 1)
    m = mons[0]
    assert m.__dict__.get('_tm_plan')
    hero.x, hero.y = 2, 7                                 # back up the stair and down elsewhere
    tm.TURN.n = 900
    m.take_turn(hero, d, mons)
    plan = m.__dict__.get('_tm_plan')
    assert plan is None or tuple(plan['at']) == (hero.x, hero.y)


def test_a_monster_mid_plan_survives_a_save_and_an_old_save_takes_its_turn():
    d, hero, mons = _corridor_scene()
    turns(mons, hero, d, 2)
    blob = pickle.dumps((mons, d))
    mons2, d2 = pickle.loads(blob)
    for m in mons2:
        m.take_turn(hero, d2, mons2)
    # A save from before the pass: none of the new fields.
    for m in mons2:
        for k in [k for k in m.__dict__ if k.startswith(('_tm_', '_lane', '_queue'))]:
            del m.__dict__[k]
    d2.__dict__.pop('habits', None)
    d2.__dict__.pop('_tm_said', None)
    old = pickle.loads(pickle.dumps(mons2))
    for m in old:
        m.take_turn(hero, d2, old)


def test_the_same_seed_gives_the_same_choices():
    def run():
        random.seed(99)
        tm.TURN.__init__()
        d, hero, mons = _corridor_scene()
        turns(mons, hero, d, 14)
        return [((m.x, m.y), dict(m.__dict__.get('_tm_used') or {})) for m in mons]
    assert run() == run()


def test_a_crowded_floor_thinks_in_time():
    """200 monster turns of thinking kinds near the hero stay inside a frame
    budget (a generous bound for a busy test machine)."""
    d = open_room(40, 30)
    hero = Hero(20, 15)
    kinds = ('hobgoblin', 'bandit_thug', 'drow_warrior', 'kobold_pack_leader', 'orc_warrior',
             'bandit_archer', 'gnoll_pack_lord', 'huldufolk_raider')
    rng = random.Random(3)
    mons = []
    taken = {(hero.x, hero.y)}
    while len(mons) < 40:
        x, y = rng.randint(8, 32), rng.randint(5, 25)
        if (x, y) in taken:
            continue
        taken.add((x, y))
        mons.append(make(kinds[len(mons) % len(kinds)], x, y))
    t0 = time.perf_counter()
    n = 0
    for i in range(5):
        tm.begin_turn(_Game(turn=10 + i))
        for m in mons:
            m.take_turn(hero, d, mons)
            n += 1
    dt = time.perf_counter() - t0
    assert n == 200
    assert dt < 4.0, f'{dt:.2f}s for 200 turns'


# ===========================================================================
# The data, the tells, the Bestiary
# ===========================================================================

NO_MIND_FAMILIES = ('oozes', 'plants', 'constructs', 'great_beasts', 'vermin', 'birds',
                    'restless_dead', 'elementals')
# By lore: the drilled dead (Talos's sown men and the warrior skeletons kept
# in rank by their master), and the earth spider that took a monk's shape to
# lay its curse on Raiko.
LORE_EXCEPTIONS = {'skeleton_warrior', 'tsuchigumo'}


def test_every_mind_kind_exists_and_no_beast_or_mindless_kind_thinks():
    for kind, e in MINDS['kinds'].items():
        assert kind in MONS, kind
        assert e['mind'] in tactics.MINDS, kind
        m = MONS[kind]
        if kind not in LORE_EXCEPTIONS:
            assert m.get('family') not in NO_MIND_FAMILIES, kind
        assert not (m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon')), kind
        assert 'mindless' not in (m.get('tags') or ()), kind


def test_every_mind_has_its_weights_lines_and_bestiary_sentence():
    for mind in tactics.MINDS:
        sp = MINDS['minds'][mind]
        assert sp['bestiary'] and sp['weights'].get('attack') == 1.0, mind
        for opt in sp['weights']:
            assert opt in tactics.OPTIONS, (mind, opt)
    lines = MINDS['lines']
    for opt in tactics.OPTIONS:
        if opt != 'attack':
            assert any(k == opt or k.startswith(opt) for k in lines) or opt in (
                'screen', 'fall_back'), opt


def test_no_line_says_they_of_one_creature():
    import re
    texts = list(MINDS['lines'].values()) + [m['bestiary'] for m in MINDS['minds'].values()]
    texts += list(MINDS['flags'].values())
    for band in MINDS['orders'].values():
        if isinstance(band, dict):
            texts += [v for v in band.values() if isinstance(v, str)]
    for t in texts:
        # "they" only after a plural subject ("{The} and the others").
        if re.search(r'\b[Tt]hey\b', t):
            assert 'and the others' in t or 'The rest of them' in t or 'the corridor' in t \
                or 'Fall back' in t, t


def test_the_tells_of_a_thinking_creature_are_reachable_and_last():
    t = json.load(open(os.path.join(ROOT, 'data', 'tells.json'), encoding='utf-8'))
    for key in ('mind_cunning', 'mind_soldier', 'mind_trickster', 'mind_caster', 'dark_edge',
                'knows_traps', 'band_orders'):
        assert key in t['order'] and t['effects'][key]['counter'], key
    assert 'mind_soldier' in tells.abilities(make('hobgoblin', 2, 2))
    assert 'dark_edge' in tells.abilities(make('drow_warrior', 2, 2))
    assert 'knows_traps' in tells.abilities(make('kobold_pack_leader', 2, 2))
    assert 'mind_caster' in tells.abilities(make('kobold_sorcerer', 2, 2))
    assert 'mind_trickster' in tells.abilities(make('vila', 2, 2))
    lead = make('hobgoblin_captain', 2, 2)
    lead._band_role = 'leader'
    assert 'band_orders' in tells.abilities(lead)
    # A creature's worst power is still the tell said first.
    assert tells.abilities(make('drow_priestess', 2, 2))[0] != 'mind_trickster'


def test_the_bestiary_says_the_mind_in_one_sentence():
    assert tm.bestiary_lines('hobgoblin') == [MINDS['minds']['soldier']['bestiary']]
    assert MINDS['flags']['dark_edge'] in tm.bestiary_lines('drow_warrior')
    assert MINDS['flags']['knows_traps'] in tm.bestiary_lines('kobold')
    assert tm.bestiary_lines('wolf') == []
    from game_render import monster_trait_lines
    assert MINDS['minds']['cunning']['bestiary'] in monster_trait_lines(
        {**MONS['bandit_thug'], 'id': 'bandit_thug'}, known=True)
    assert MINDS['minds']['cunning']['bestiary'] not in monster_trait_lines(
        {**MONS['bandit_thug'], 'id': 'bandit_thug'}, known=False)


def test_the_help_page_tells_how_the_clever_ones_fight():
    page = json.load(open(os.path.join(ROOT, 'data', 'ui', 'monster_ways.json'), encoding='utf-8'))
    sec = [s for s in page['sections'] if s['heading'] == 'How the clever ones fight']
    assert sec and len(sec[0]['rows']) >= 6


def test_minds_json_is_packaged():
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert 'data/minds.json' in spec
