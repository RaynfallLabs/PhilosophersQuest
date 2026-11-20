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


# ===========================================================================
# morale_by_nature: Morale by Nature
# ===========================================================================

import morale  # noqa: E402


class Dice:
    """An rng whose every d10 shows ``face``."""
    def __init__(self, face):
        self.face = face

    def randint(self, a, b):
        return max(a, min(b, self.face))

    def random(self):
        return 0.0


def _hurt(m, share):
    m.hp = max(1, int(m.max_hp * share))
    return m


def test_the_mindless_dead_never_break():
    z = _hurt(make('zombie'), 0.1)
    morale.turn(z, Hero(6, 5), [z], rng=Dice(10))
    assert z._flee_timer == 0
    assert any('falling apart' in t for t, _u, _c in ai_lines.take(z))


def test_a_beast_bolts_then_gives_up_the_fight():
    wolf = _hurt(make('wolf'), 0.2)
    hero = Hero(6, 5)
    morale.turn(wolf, hero, [wolf], rng=Dice(10))
    assert wolf._flee_timer >= 8 and wolf.__dict__.get('_bolting')
    for _ in range(wolf._flee_timer):
        morale.turn(wolf, hero, [wolf], rng=Dice(10))
    assert wolf._flee_timer == 0 and wolf.__dict__.get('_cowed')
    # cowed, it keeps away from a hero it can see; it never closes in
    dun = open_room()
    hero = Hero(10, 10)
    wolf.x, wolf.y = 13, 10
    for _ in range(4):
        wolf.take_turn(hero, dun, [wolf])
    assert max(abs(wolf.x - hero.x), abs(wolf.y - hero.y)) >= 3


def test_the_old_flight_never_re_arms_itself():
    hob = _hurt(make('hobgoblin'), 0.2)
    hero = Hero(6, 5)
    morale.turn(hob, hero, [hob], rng=Dice(10))
    assert hob._flee_timer > 0
    for _ in range(40):
        morale.turn(hob, hero, [hob], rng=Dice(10))
    assert hob._flee_timer == 0                    # one break for one wound


def test_a_goblin_runs_for_its_friends_and_brings_them():
    dun = open_room()
    hero = Hero(4, 10)
    gob = _hurt(make('goblin', 6, 10), 0.2)
    friend = make('goblin', 13, 10)
    friend._tracking = False
    friend._aware = False
    morale.turn(gob, hero, [gob, friend], rng=Dice(10))
    assert gob.__dict__.get('_rally_to') is friend
    assert any('friends' in t for t, _u, _c in ai_lines.take(gob))
    for _ in range(8):
        if gob.__dict__.get('_rally_to') is None:
            break
        morale.run(gob, hero, dun, [gob, friend], set())
    assert gob._flee_timer == 0 and gob.__dict__.get('_rallied')
    assert friend._aware and friend._alerted       # roused to the hero


def test_a_cornered_goblin_turns_at_bay():
    tiles = [[WALL] * 8 for _ in range(5)]
    for x in range(1, 7):
        tiles[2][x] = FLOOR                       # a dead-end passage
    dun = Dungeon(tiles, [Room(0, 0, 8, 5)], 8, 5, 3)
    gob = _hurt(make('goblin', 1, 2), 0.2)
    hero = Hero(2, 2)
    morale.turn(gob, hero, [gob], rng=Dice(10))
    assert gob._flee_timer > 0
    assert morale.run(gob, hero, dun, [gob], set()) is True
    assert gob._at_bay > 0 and morale.at_bay_hit(gob) < 0


def test_a_big_ordinary_kind_can_break_now_and_a_named_foe_cannot():
    big = next(k for k, v in MONS.items() if isinstance(v, dict)
               and v.get('ai_pattern') == 'aggressive' and v.get('family') == 'giants'
               and not (v.get('is_boss') or v.get('is_mini_boss') or v.get('is_seal_demon'))
               and make(k).max_hp > 500)
    g = _hurt(make(big), 0.2)
    assert g.max_hp > 500                          # the old rule kept it standing
    morale.turn(g, Hero(6, 5), [g], rng=Dice(10))
    assert g._flee_timer > 0
    boss = next(k for k, v in MONS.items() if isinstance(v, dict) and v.get('is_mini_boss')
                and v.get('ai_pattern') == 'aggressive')
    b = _hurt(make(boss), 0.1)
    morale.turn(b, Hero(6, 5), [b], rng=Dice(10))
    assert b._flee_timer == 0


def test_steady_nerve_holds_on_a_low_roll():
    dragon_kin = _hurt(make('hobgoblin'), 0.2)
    morale.turn(dragon_kin, Hero(6, 5), [dragon_kin], rng=Dice(1))   # 2 on 2d10
    assert dragon_kin._flee_timer == 0


def test_five_blows_that_do_nothing_break_its_nerve():
    hob = make('hobgoblin')
    for _ in range(5):
        morale.futile_blow(hob, 0)
    assert hob.__dict__.get('_morale_check') == 'futile'
    morale.turn(hob, Hero(6, 5), [hob], rng=Dice(10))
    assert hob._flee_timer > 0


def test_a_kin_falling_in_sight_shakes_the_hurt():
    dun = open_room()
    a = _hurt(make('goblin', 5, 5), 0.4)
    fresh = make('goblin', 6, 6)
    dead = make('goblin', 7, 5)
    dead.alive = False
    assert morale.kin_fell([a, fresh, dead], dead, dun) == 1
    assert a.__dict__.get('_morale_check') == 'kin'
    assert not fresh.__dict__.get('_morale_check')


def test_a_cornered_bandit_with_no_friends_yields():
    tiles = [[WALL] * 8 for _ in range(5)]
    for x in range(1, 7):
        tiles[2][x] = FLOOR
    dun = Dungeon(tiles, [Room(0, 0, 8, 5)], 8, 5, 3)
    b = _hurt(make('bandit_thug', 1, 2), 0.1)
    hero = Hero(2, 2)
    morale.turn(b, hero, [b], rng=Dice(10))
    assert morale.run(b, hero, dun, [b], set()) is False
    assert b.__dict__.get('_yielded') and b.__dict__.get('_wants_purse_dropped')
    for _ in range(5):
        assert b.take_turn(hero, dun, [b]) is False    # it never strikes again


def test_war_band_follower_and_harry_hold_their_nerve():
    lead = make('hobgoblin')
    f = _hurt(make('goblin'), 0.1)
    f._band_leader = lead
    morale.turn(f, Hero(6, 5), [f, lead], rng=Dice(10))
    assert f._flee_timer == 0


def test_every_family_has_a_nature_and_the_mindless_never_run():
    import family_lore
    fams = set(family_lore.families()) if hasattr(family_lore, 'families') else set()
    rows = kind_data.rules('morale')['families']
    for fam in fams:
        assert fam in rows, fam
    for fam in ('restless_dead', 'constructs', 'oozes', 'plants'):
        assert rows[fam]['style'] == 'never'
    for kind in ('gelatinous_cube', 'iron_golem', 'skeleton', 'cult_zealot'):
        assert morale.style(make(kind)) == 'never', kind
    assert morale.style(make('wolf')) == 'bolt'
    assert morale.style(make('goblin')) == 'regroup'
    assert morale.style(make('bandit_thug')) == 'yield'


def test_morale_state_survives_a_save():
    hob = _hurt(make('hobgoblin'), 0.2)
    morale.turn(hob, Hero(6, 5), [hob], rng=Dice(10))
    h2 = pickle.loads(pickle.dumps(hob))
    assert h2._flee_timer == hob._flee_timer and h2.__dict__.get('_wound_checked')


def test_the_simulator_runs_the_real_morale():
    import sim_ai1

    class Run:
        p = Hero(5, 5)
        fs = {}
        knobs = dict(sim_ai1.KNOBS)
        _ai1_queue = []
    wolf = _hurt(make('wolf', 6, 5), 0.2)
    wolf._cached_all_monsters = [wolf]
    random.seed(1)
    results = [sim_ai1.morale_turn(Run, wolf) for _ in range(30)]
    assert results[0] is False or wolf._flee_timer == 0
    if wolf.__dict__.get('_cowed'):
        assert wolf.__dict__.get('_sim_left') == 'bolt'
        keep, _q = sim_ai1.leavers(Run, [wolf], [])
        assert keep == []


# ===========================================================================
# life_drained: Life Drained
# ===========================================================================

import life_drain  # noqa: E402
from player import Player  # noqa: E402


class AlwaysFails:
    def randint(self, a, b):
        return a


def _real_hero():
    p = Player()
    p.max_hp = p.hp = 200
    return p


def test_a_drain_blow_lowers_greatest_health_and_caps_hold(monkeypatch):
    p = _real_hero()
    w = make('wight')
    atk = w.attacks[0]
    assert life_drain.drains_life(atk)              # 'Draining Touch' drains now
    monkeypatch.setattr(life_drain, 'save_holds', lambda m, pl, rng=None: False)
    msg = life_drain.after_blow(w, p, atk, 12, 'hit.')
    assert p.max_hp == 194 and life_drain.drained(p) == 6
    assert 'Max HP -6' in msg
    life_drain.after_blow(w, p, atk, 400, '')       # one blow: at most a tenth
    assert life_drain.drained(p) == 6 + 20
    for _ in range(10):
        life_drain.after_blow(w, p, atk, 400, '')
    assert life_drain.drained(p) == 50              # a quarter in all
    assert p.max_hp == 150


def test_drained_life_comes_back_half_on_the_stairs_and_all_from_a_physician():
    p = _real_hero()
    life_drain.take_life(p, 20)
    assert p.max_hp == 180
    assert life_drain.stairs_rest(p) == 10 and p.max_hp == 190
    assert life_drain.restore(p) == 10 and p.max_hp == 200 and life_drain.drained(p) == 0


def test_drain_resist_and_a_held_save_stop_it(monkeypatch):
    p = _real_hero()
    w = make('wight')
    p.status_effects['drain_resist'] = 5
    life_drain.after_blow(w, p, w.attacks[0], 12, '')
    assert life_drain.drained(p) == 0
    p.status_effects.clear()
    monkeypatch.setattr(life_drain, 'save_holds', lambda m, pl, rng=None: True)
    life_drain.after_blow(w, p, w.attacks[0], 12, '')
    assert life_drain.drained(p) == 0


def test_only_the_greatest_still_take_con(monkeypatch):
    p = _real_hero()
    p.CON = 14
    lich = make('lich')
    monkeypatch.setattr(life_drain, 'save_holds', lambda m, pl, rng=None: False)
    monkeypatch.setattr(Monster, '_drain_takes_hold', lambda self, pl: True)
    life_drain.after_blow(lich, p, lich.attacks[0], 10, '')
    assert p.CON == 13
    shadow = make('shadow')
    p.CON = 14
    life_drain.after_blow(shadow, p, shadow.attacks[0], 10, '')
    assert p.CON == 14 and life_drain.drained(p) > 0


def test_drained_hero_round_trips_and_old_saves_have_none():
    p = _real_hero()
    life_drain.take_life(p, 10)
    p2 = pickle.loads(pickle.dumps(p))
    assert life_drain.drained(p2) == 10
    p2.__dict__.pop('_life_drained')
    assert life_drain.drained(p2) == 0


def test_the_drain_tell_and_the_feeders():
    assert 'life_drain' in tells.abilities(make('wraith'))
    assert make('nosferatu').drain_heals_self == 0.5




# ===========================================================================
# grave_rot: Grave Rot
# ===========================================================================

import grave_rot  # noqa: E402


def test_a_sick_hero_heals_half_and_rest_stops():
    p = _real_hero()
    p.hp = 100
    p.status_effects['diseased'] = 30
    assert p.restore_hp(40) == 20
    assert grave_rot.blocks_regen(p)
    p.status_effects.clear()
    assert p.restore_hp(40) == 40


def test_a_disease_lasts_as_long_as_its_kinds_lore_says():
    assert grave_rot.linger(make('giant_rat'), 4) == 4          # a rat's bite is short
    assert grave_rot.linger(make('plague_zombie'), 6) == 24
    assert grave_rot.linger(make('mummy'), 8) == 60             # mummy rot, to the cap
    grave_rot.ENABLED = False
    try:
        assert grave_rot.linger(make('mummy'), 6) == 6
    finally:
        grave_rot.ENABLED = True


def test_a_sick_troll_does_not_mend():
    t = make('troll')
    t.hp = t.max_hp // 2
    t.status_effects['diseased'] = 5
    before = t.hp
    t.tick_effects()
    assert t.hp == before - max(1, t.max_hp // 40)


# ===========================================================================
# light_shy_and_snuff
# ===========================================================================

import light_shy  # noqa: E402


class Torch:
    item_class = 'light'

    def __init__(self, burn=400, power=''):
        self.id = 'torch'
        self.lit = True
        self.burn = burn
        self.fuel = burn
        self.sight = 2
        self.noun = 'torch'
        self.power = power


def test_a_troll_flinches_from_a_light_and_cannot_mend_in_it():
    troll = make('troll', 5, 5)
    hero = Hero(6, 5)
    assert light_shy.flinch(troll, hero) == 0
    hero.shield = Torch()
    assert light_shy.flinch(troll, hero) == 2
    hero.status_effects['light'] = 10
    assert light_shy.flinch(troll, hero) == 4         # the Light spell, capped
    troll.hp = troll.max_hp // 2
    light_shy.light_turn(troll, hero)
    before = troll.hp
    troll.tick_effects()
    assert troll.hp == before                         # no mending in the light
    assert any('wounds' in t for t, _u, _c in ai_lines.take(troll))


def test_a_troll_stiffens_in_the_light_spell_but_a_named_one_does_not():
    troll = make('troll', 5, 5)
    hero = Hero(6, 5)
    hero.status_effects['light'] = 10
    for _ in range(3):
        light_shy.light_turn(troll, hero)
    assert troll.has_effect('slowed')


def test_a_wave_drowns_a_torch_but_not_hecates():
    hero = Hero(6, 5)
    hero.shield = Torch()
    line = light_shy.snuff(hero, 'water')
    assert not hero.shield.lit and light_shy.wet(hero.shield) == 3 and 'torch' in line
    hero.shield = Torch(burn=0, power='unmasks')
    light_shy.snuff(hero, 'water')
    assert hero.shield.lit
    hero.shield = Torch()
    hero.status_effects['light'] = 5
    light_shy.snuff(hero, 'dark')
    assert 'light' not in hero.status_effects


def test_the_snuffers_carry_it():
    assert any(a.get('snuffs_light') == 'water' for a in make('water_elemental').attacks)
    assert 'light_shy' in tells.abilities(make('troll'))


# ===========================================================================
# hit_and_run_vanishes: Gone Again
# ===========================================================================

import gone_again  # noqa: E402


def _pillar_room():
    d = open_room(20, 20)
    for y in range(4, 16):
        d.tiles[y][10] = WALL                 # a long wall to hide behind
    return d


def test_an_imp_breaks_off_to_cover_and_waits_there():
    dun = _pillar_room()
    imp = make('imp', 8, 10)
    hero = Hero(7, 10)
    imp._hit_run_state = 'retreating'
    for _ in range(12):
        imp.take_turn(hero, dun, [imp])
        if imp._hit_run_state == 'hiding':
            break
    assert imp._hit_run_state == 'hiding'
    assert not senses.clear_view(imp.x, imp.y, hero.x, hero.y, dun)


def test_a_blow_or_a_close_hero_ends_the_hiding():
    dun = _pillar_room()
    imp = make('imp', 12, 10)
    hero = Hero(7, 10)
    imp._hit_run_state = 'hiding'
    imp._hit_run_timer = 5
    imp._struck = False
    assert gone_again.hiding_turn(imp, hero, dun) is False
    imp.take_damage(1)
    assert gone_again.hiding_turn(imp, hero, dun) is True
    assert imp._hit_run_state == 'hunting'


def test_a_shade_hides_in_the_dark_but_not_from_a_torch():
    import unseen
    shade = make('shade', 12, 10)
    hero = Hero(7, 10)
    gone_again.begin_hiding(shade, hero)
    assert unseen.unseen(shade, hero)
    hero.shield = Torch()
    gone_again.dark_hide(shade, hero)
    assert not unseen.unseen(shade, hero)


# ===========================================================================
# raise_the_alarm
# ===========================================================================

import alarm  # noqa: E402


def test_a_kobold_shouts_once_and_rouses_its_own_side_only():
    dun = open_room(30, 10)
    k = make('kobold', 5, 5)
    friend = make('kobold', 15, 5)
    other = make('wolf', 14, 5)
    for o in (friend, other):
        o._tracking = False
        o._aware = False
    hero = Hero(3, 5)
    assert alarm.shout(k, [k, friend, other], hero, dun) == 1
    assert friend._aware and not other._aware
    assert alarm.shout(k, [k, friend, other], hero, dun) == 0     # once a floor
    assert any('yaps' in t for t, _u, _c in ai_lines.take(k))


def test_the_hand_of_glory_keeps_sleepers_asleep(monkeypatch):
    import sleepers
    dun = open_room(30, 10)
    k = make('kobold', 5, 5)
    sleeper = make('kobold', 8, 5)
    sleeper.status_effects['sleeping'] = 50
    monkeypatch.setattr(sleepers, 'factor', lambda p, what: 0.0)
    alarm.shout(k, [k, sleeper], Hero(3, 5), dun)
    assert sleeper.has_effect('sleeping')


def test_a_wall_stops_the_shout():
    w, h = 21, 10
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 9):
        for x in range(1, 9):
            tiles[y][x] = FLOOR
        for x in range(12, 20):
            tiles[y][x] = FLOOR
    dun = Dungeon(tiles, [Room(0, 0, 10, 10), Room(11, 0, 10, 10)], w, h, 3)
    k = make('kobold', 5, 5)
    far = make('kobold', 14, 5)
    far._aware = False
    alarm.shout(k, [k, far], Hero(3, 5), dun)
    assert not far._aware


# ===========================================================================
# death_throes
# ===========================================================================

import death_throes  # noqa: E402


def test_a_fire_beetle_swells_then_is_ready_to_burst():
    b = make('fire_beetle')
    b.hp = 1
    death_throes.warn(b)
    assert any('glow' in t for t, _u, _c in ai_lines.take(b))
    assert death_throes.should_burst(b)
    b._banished = True
    assert not death_throes.should_burst(b)


def test_a_blast_is_a_share_of_each_victims_own_health():
    b = make('fire_beetle', 5, 5)
    assert death_throes.blast(b, 200) == 10
    assert death_throes.in_blast(b, 6, 6, open_room())
    assert not death_throes.in_blast(b, 8, 5, open_room())


# ===========================================================================
# relurk: Back to the Web
# ===========================================================================

import relurk  # noqa: E402


def test_a_hurt_spider_out_of_sight_goes_back_into_hiding_once():
    s = make('giant_spider')
    s.ai_pattern = 'aggressive'
    s._aware = True
    s.hp = int(s.max_hp * 0.5)
    s._lost_turns = 3
    assert relurk.consider(s, Hero(8, 5))
    assert s.ai_pattern == 'ambush' and not s._aware and not s._mimic_surprise
    s.ai_pattern = 'aggressive'
    s._aware = True
    assert not relurk.consider(s)                    # once a life


def test_a_fresh_spider_stays_out():
    s = make('giant_spider')
    s.ai_pattern = 'aggressive'
    s._aware = True
    s._lost_turns = 5
    assert not relurk.consider(s)


# ===========================================================================
# shove_into_danger
# ===========================================================================

import shove  # noqa: E402


def test_a_shove_throws_the_hero_back_never_into_water_or_a_wall():
    from dungeon import WATER, LAVA
    dun = open_room(12, 12)
    assert shove.landing(dun, (5, 5), (4, 5), False, set()) == ((6, 5), False)
    dun.tiles[5][6] = WATER
    assert shove.landing(dun, (5, 5), (4, 5), False, set()) is None
    dun.tiles[5][6] = LAVA
    assert shove.landing(dun, (5, 5), (4, 5), False, set()) is None
    dun.tiles[5][6] = WALL
    assert shove.landing(dun, (5, 5), (4, 5), False, set()) is None
    dun.tiles[5][6] = FLOOR
    assert shove.landing(dun, (5, 5), (4, 5), False, {(6, 5)}) is None


def test_a_shove_leaves_its_move_for_the_game(monkeypatch):
    g = make('hill_giant', 4, 5)
    club = next(a for a in g.attacks if a.get('shove'))
    hero = Hero(5, 5)
    monkeypatch.setattr(shove, '_str_save', lambda p, rng=None: False)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    shove.after_blow(g, hero, club, 10, '')
    assert hero.__dict__.get('_pending_shove', {}).get('from') == (4, 5)


# ===========================================================================
# Every new field reads with a default from an old save
# ===========================================================================

def test_an_old_monster_pickle_takes_its_kinds_new_fields():
    w = make('wight')
    for k in list(w.__dict__):
        if k.startswith('_') and k not in ('_aware',):
            pass
    old = pickle.loads(pickle.dumps(w))
    assert life_drain.drains(old)
    assert kind_data.field(old, 'relurks', False) is False
    assert morale.style(make('kobold')) == 'regroup'


# ===========================================================================
# Help, hints and tells say it
# ===========================================================================

def test_the_help_screen_has_a_page_for_monsters_and_their_ways():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert "('monster_ways', 'Monsters and Their Ways')" in src
    page = json.load(open(os.path.join(ROOT, 'data', 'ui', 'monster_ways.json'), encoding='utf-8'))
    text = json.dumps(page).lower()
    for word in ('breath', 'bolts', 'friends', 'greatest health', 'diseased', 'troll',
                 'snuffed', 'hide', 'alarm', 'chant', 'burst', 'throw you back'):
        assert word in text, word


def test_every_new_tell_is_reachable_from_real_data():
    keys = set()
    for kind, v in MONS.items():
        if isinstance(v, dict):
            keys.update(tells.abilities(make(kind)))
    for k in ('breath_recharge', 'heals_allies', 'life_drain', 'light_shy', 'snuffs_light',
              'raises_alarm', 'death_throes', 'relurks', 'hides_in_dark', 'shove'):
        assert k in keys, k


def test_the_hints_tell_of_the_new_ways():
    hints = json.load(open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8'))
    text = ' '.join(h for lst in hints.values() for h in lst).lower()
    for word in ('draw breath', 'runner', 'lookout', 'chant', 'burst'):
        assert word in text, word


def test_a_withdrawing_giant_strikes_a_hero_who_presses_it(monkeypatch):
    dun = open_room()
    giant = _hurt(make('hill_giant', 10, 10), 0.2)
    hero = Hero(11, 10)
    morale.turn(giant, hero, [giant], rng=Dice(10))
    assert giant._flee_timer > 0 and morale.style(giant) == 'withdraw'
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    assert morale.run(giant, hero, dun, [giant], set()) is True      # it strikes as it goes
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    x0 = giant.x
    assert morale.run(giant, hero, dun, [giant], set()) is False     # or backs off a step
    assert giant.x < x0
