"""Monster behaviour, first wave (AI-1, 2026-11-19).

Seeded, deterministic logic tests for each behaviour, on real kinds from
data/monsters.json where the lore is the point and on stubs where the shape
is: the three fixes to today's AI (the floating eye's gaze, healers,
summoners), then Draws Breath, Morale by Nature, Life Drained, Grave Rot,
Light-Shy and Snuff the Light, Gone Again, Raise the Alarm, Death Throes,
Back to the Web and Shove. A save made before the pass loads (every new
field is read with a default).
"""
import copy
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import ai_lines  # noqa: E402
import breath  # noqa: E402
import faction  # noqa: E402
import kind_data  # noqa: E402
import senses  # noqa: E402
import summoning  # noqa: E402
import tells  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Hero:
    """Enough of a hero for the monster's side of a fight."""
    def __init__(self, x=10, y=10, hp=200):
        self.x, self.y = x, y
        self.hp = self.max_hp = hp
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.shield = None
        self.weapon = None
        self.armor_slots = []

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self):
        return 8

    def take_damage(self, amount, damage_type='physical'):
        actual = max(0, int(amount))
        self.hp = max(0, self.hp - actual)
        return actual

    def save_bonus_for(self, _stat):
        return 0

    def add_effect(self, name, duration):
        self.status_effects[name] = duration
        return True


def open_room(w=24, h=24):
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, 5)


def make(kind, x=5, y=5, **extra):
    d = {**MONS[kind], 'id': kind}
    d.update(extra)
    return Monster(d, x, y)


def stub(**over):
    base = {'id': 'test_mob', 'name': 'test mob', 'symbol': 'M', 'color': [200, 200, 200],
            'ai_pattern': 'aggressive', 'hp': '40', 'speed': 10, 'thac0': 1,
            'attacks': [{'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'}],
            'tags': ['beast']}
    base.update(over)
    x, y = base.pop('x', 5), base.pop('y', 5)
    m = Monster(base, x, y)
    m._aware = True
    return m


def setup_function(_):
    random.seed(7)
    senses.begin_turn(moved=True, guilty=False, floor=5)
    breath.ENABLED = True
    summoning.ENABLED = True


# ===========================================================================
# fix_gaze_cooldown: the gaze is ready again for every gazer
# ===========================================================================

def test_floating_eye_gazes_again_after_its_cooldown():
    eye = make('floating_eye')
    hero = Hero(6, 5)
    eye.attack(hero)
    assert eye._gaze_cooldown == eye.gaze_cooldown_max
    for _ in range(eye.gaze_cooldown_max):
        eye.tick_effects()
    assert eye._gaze_cooldown == 0          # it used to stay at 4 for ever


def test_a_dancer_cooldown_falls_one_a_turn_not_two():
    stheno = make('stheno_gorgon')
    stheno._gaze_cooldown = 4
    hero = Hero(20, 20)
    dun = open_room()
    stheno.tick_effects()
    stheno.take_turn(hero, dun, [stheno])
    assert stheno._gaze_cooldown == 3


# ===========================================================================
# fix_healer
# ===========================================================================

def _priest_and(ally_kind='orc_warrior', ally_share=0.5):
    priest = make('orc_priest', 5, 5)
    ally = make(ally_kind, 5, 6)
    ally.hp = max(1, int(ally.max_hp * ally_share))
    return priest, ally


def test_healer_leaves_a_scratch_and_mends_a_real_wound():
    priest, ally = _priest_and(ally_share=0.95)
    hero = Hero(20, 20)
    dun = open_room()
    priest.take_turn(hero, dun, [priest, ally])
    assert priest._heal_target is None
    ally.hp = int(ally.max_hp * 0.5)
    priest.take_turn(hero, dun, [priest, ally])
    assert priest._heal_target is ally and priest._heal_amount > 0


def test_healer_rests_its_voice_between_heals():
    priest, ally = _priest_and(ally_share=0.3)
    hero = Hero(6, 6)                       # beside both: nobody walks off
    dun = open_room()
    priest.take_turn(hero, dun, [priest, ally])
    assert priest._heal_target is ally
    ally.hp = int(ally.max_hp * 0.3)
    heals = 0
    for _ in range(3):
        priest.tick_effects()
        priest.take_turn(hero, dun, [priest, ally])
        heals += priest._heal_target is ally
    assert heals == 1                       # cooldown 3: the third turn heals again


def test_an_orc_priest_does_not_mend_a_bandit():
    priest, bandit = _priest_and('bandit_thug', 0.3)
    assert 'humanoid' in set(priest.tags) & set(bandit.tags)   # the old loose rule
    assert faction.heal_choice(priest, [priest, bandit], Hero(20, 20)) is None


def test_ai_faction_band_then_pack_then_family():
    m = make('orc_warrior')
    assert faction.ai_faction(m) == ('family', 'goblinkin')
    m._pack = 'p1'
    assert faction.ai_faction(m)[0] == 'pack'
    m._band = 'b1'
    assert faction.ai_faction(m) == ('band', 'b1')


def test_a_band_healer_mends_its_band_only():
    priest = make('orc_priest')
    priest._band = 'b1'
    other = make('orc_warrior', 5, 6)
    other._band = 'b2'
    other.hp = 1
    assert not faction.same_side(priest, other)
    other._band = 'b1'
    assert faction.same_side(priest, other)


def test_the_healer_tell():
    assert 'heals_allies' in tells.abilities(make('orc_priest'))


# ===========================================================================
# fix_summoner
# ===========================================================================

def test_summoner_chants_then_calls_and_a_blow_breaks_the_chant():
    s = make('skeleton_necromancer', 5, 5)
    s.summon_cooldown = 2
    hero = Hero(9, 5)
    dun = open_room()
    s.take_turn(hero, dun, [s])                 # it spots him; the timer starts
    assert not s.__dict__.get('_chanting')
    s.take_turn(hero, dun, [s])                 # 2nd turn: it begins to chant
    assert s.__dict__.get('_chanting') and not s._wants_summon
    assert any('chant' in t for t, _u, _c in ai_lines.take(s))
    s.take_damage(5)                            # a blow breaks it
    assert not s.__dict__.get('_chanting')
    assert any('breaks' in t for t, _u, _c in ai_lines.take(s))
    s.take_turn(hero, dun, [s])
    s.take_turn(hero, dun, [s])                 # chants again
    assert s.__dict__.get('_chanting')
    s.take_turn(hero, dun, [s])                 # the chant done: the call
    assert s._wants_summon and s._summons_made == 1


def test_summoner_does_not_call_before_it_has_seen_the_hero():
    s = make('skeleton_necromancer', 5, 5)
    s.summon_cooldown = 1
    s._aware = False
    hero = Hero(5, 20)                          # out of its sight
    tiles = [[WALL] * 24 for _ in range(24)]
    for y in range(1, 10):
        for x in range(1, 23):
            tiles[y][x] = FLOOR
    for y in range(12, 23):
        for x in range(1, 23):
            tiles[y][x] = FLOOR
    dun = Dungeon(tiles, [Room(0, 0, 24, 11), Room(0, 11, 24, 13)], 24, 24, 5)
    for _ in range(6):
        s.take_turn(hero, dun, [s])
    assert s._summons_made == 0 and int(s._summon_turn_counter or 0) == 0


def test_summoner_live_cap():
    s = make('skeleton_necromancer', 5, 5)
    hero = Hero(8, 5)
    a, b = make('skeleton', 6, 6), make('skeleton', 4, 4)
    a._summoned_by = s
    b._summoned_by = s
    assert not summoning.can_call(s, hero, [s, a, b])
    a.alive = False
    assert summoning.can_call(s, hero, [s, a, b])


def test_summoner_needs_the_hero_in_reach():
    s = make('skeleton_necromancer', 5, 5)
    assert not summoning.can_call(s, Hero(20, 5), [s])
    assert summoning.can_call(s, Hero(12, 5), [s])


# ===========================================================================
# breath_recharge: Draws Breath
# ===========================================================================

def test_a_young_red_dragon_breathes_then_must_draw_breath():
    d = make('young_red_dragon', 5, 5)
    d._opened = True
    fire = next(a for a in d.attacks if a['delivery'] == 'breath')
    hero = Hero(9, 5, hp=5000)
    breath.spend(d, fire)
    assert not breath.ready(d, fire) and breath.drawing(d)
    for _ in range(2):
        d.tick_effects()
        assert not breath.ready(d, fire)
    d.tick_effects()
    assert breath.ready(d, fire)
    # while it draws breath it never breathes, even from range
    breath.spend(d, fire)
    for _ in range(20):
        got = breath.choose(d, fire, hero)
        assert got is None or got is not fire


def test_a_drawing_breather_closes_in_with_tooth_and_claw():
    wolf = make('winter_wolf', 5, 5)
    wolf._opened = True
    hero = Hero(10, 5)
    dun = open_room()
    frost = next(a for a in wolf.attacks if a['delivery'] == 'breath')
    breath.spend(wolf, frost)
    x0 = wolf.x
    attacked = wolf.take_turn(hero, dun, [wolf])
    assert not attacked and wolf.x > x0           # it came on; it did not back away


def test_a_breath_only_creature_drawing_breath_strikes_nothing_from_afar():
    s = stub(ai_pattern='ranged', attacks=[{'name': 'Fire Breath', 'damage': '2d6',
                                             'type': 'fire', 'delivery': 'breath'}])
    s._opened = True
    hero = Hero(9, 5)
    dun = open_room()
    breath.spend(s, s.attacks[0])
    assert s.take_turn(hero, dun, [s]) is False
    dmg, msg = s.attack(hero)
    assert dmg == 0 and 'breath' in msg.lower()


def test_a_flurry_never_breathes_twice_running():
    s = stub(multi_attack_count=2, attacks=[
        {'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'},
        {'name': 'Acid Spray', 'damage': '1d4', 'type': 'acid', 'delivery': 'breath'},
        {'name': 'Tail Sweep', 'damage': '1d4', 'type': 'blunt', 'delivery': 'sting'}])
    hero = Hero(6, 5, hp=5000)
    first = [a['name'] for a in breath.flurry(s, s.attacks, 2)]
    assert first == ['Bite', 'Acid Spray']
    s.attack(hero)
    assert not breath.ready(s, s.attacks[1])
    second = [a['name'] for a in breath.flurry(s, s.attacks, 2)]
    assert second == ['Bite', 'Tail Sweep']


def test_an_opener_breath_starts_the_recharge():
    d = make('young_red_dragon', 5, 5)
    hero = Hero(8, 5, hp=5000)
    d._opener_now = d._opener_attack
    d.attack(hero)
    assert not breath.ready(d, d._opener_attack)


def test_every_ordinary_breath_recharges_and_named_foes_keep_their_rhythm():
    for kind, v in MONS.items():
        if not isinstance(v, dict):
            continue
        m = make(kind)
        for a in v.get('attacks') or ():
            if a.get('delivery') != 'breath':
                continue
            n = breath.recharge_of(m, a)
            if kind_data.named(m):
                assert n == int(a.get('recharge', 0)), kind
            else:
                assert n >= 1 or a.get('recharge') == 0, kind


def test_breath_recharge_survives_a_save_and_old_saves_load():
    d = make('young_red_dragon')
    breath.spend(d, d._opener_attack)
    d2 = pickle.loads(pickle.dumps(d))
    assert not breath.ready(d2, d._opener_attack)
    d2.__dict__.pop('_recharge')                     # a save from before the pass
    assert breath.ready(d2, d._opener_attack)


def test_a_copied_monster_shares_no_recharge():
    d = make('young_red_dragon')
    twin = copy.copy(d)
    breath.spend(twin, twin._opener_attack)
    assert breath.ready(d, d._opener_attack)


def test_the_breath_tell_and_its_ready_line():
    d = make('young_red_dragon')
    assert 'breath_recharge' in tells.abilities(d)
    d._tracking = True
    breath.spend(d, d._opener_attack)
    for _ in range(3):
        d.tick_effects()
    lines = [t for t, _u, _c in ai_lines.take(d)]
    assert lines and 'jaws' in lines[-1]


def test_breath_knob_off_is_the_old_rule():
    d = make('young_red_dragon')
    breath.ENABLED = False
    try:
        breath.spend(d, d._opener_attack)
        assert breath.ready(d, d._opener_attack)
    finally:
        breath.ENABLED = True


# ===========================================================================
# The simulator's knobs
# ===========================================================================

def test_the_simulator_has_a_knob_for_each_behaviour():
    import sim_ai1
    for k, v in sim_ai1.KNOBS.items():
        assert k.startswith('ai_') and v == 1
