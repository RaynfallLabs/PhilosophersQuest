"""Monster behaviour, third wave (AI-3, 2026-11-20).

Seeded, deterministic logic tests for each behaviour, on real kinds from
data/monsters.json where the lore is the point and on stubs where the shape
is: The Caster's Book, Held Fast, Auras, Home Ground, Uses What It Carries,
Skittish (the leprechaun's bargain), the dancer's footwork, Lurkers Keep
Their Promise, Second Shape. For each, a scenario where it fires and the
ones where it must not; the edges (a holder that dies, flees, is silenced,
a floor change, a save in the middle of a hold, an old save, a stolen
potion, a creature with no family, every excluded kind); and determinism.
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
import ai_turn  # noqa: E402
import auras  # noqa: E402
import caster_ai  # noqa: E402
import dancer  # noqa: E402
import holds  # noqa: E402
import home_ground  # noqa: E402
import kind_data  # noqa: E402
import monster_kit  # noqa: E402
import morale  # noqa: E402
import second_shape  # noqa: E402
import senses  # noqa: E402
import skittish  # noqa: E402
import status_effects  # noqa: E402
import surprise  # noqa: E402
import tells  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR, WATER  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Hero:
    """Enough of a hero for the monster's side of a fight; statuses go
    through the real status_effects.apply_effect (caps, grace, resists)."""
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
        self.inventory = []
        self.known_item_ids = set()
        self.studied_monster_ids = set()
        self.lore_known_monster_ids = set()
        self.family_lore_grants = {}

    def has_effect(self, name):
        return self.status_effects.get(name, 0) != 0

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
        return status_effects.apply_effect(self, name, duration)

    def is_dead(self):
        return self.hp <= 0


def open_room(w=24, h=24):
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = FLOOR
    d = Dungeon(tiles, [Room(0, 0, w, h)], w, h, 5)
    d.traps = {}
    return d


def make(kind, x=5, y=5, **extra):
    d = {**MONS[kind], 'id': kind}
    d.update(extra)
    return Monster(d, x, y)


def stub(**over):
    base = {'id': 'test_mob', 'name': 'test mob', 'symbol': 'M', 'color': [200, 200, 200],
            'ai_pattern': 'aggressive', 'hp': '100', 'speed': 10, 'thac0': 1,
            'attacks': [{'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'}],
            'tags': ['beast']}
    base.update(over)
    x, y = base.pop('x', 5), base.pop('y', 5)
    m = Monster(base, x, y)
    m._aware = True
    return m


def hurt(m, share):
    m.hp = max(1, int(m.max_hp * share))
    return m


def fail_saves(monkeypatch):
    """Every d20 shows 1: every save fails."""
    monkeypatch.setattr(random, 'randint', lambda a, b: a)


def pass_saves(monkeypatch):
    monkeypatch.setattr(random, 'randint', lambda a, b: b)


def setup_function(_):
    random.seed(11)
    senses.begin_turn(moved=True, guilty=False, floor=5)
    for mod in (caster_ai, holds, auras, home_ground, monster_kit, skittish, surprise,
                second_shape, dancer):
        mod.ENABLED = True


# ===========================================================================
# The Caster's Book
# ===========================================================================

def _shaman(x=5, y=5):
    m = make('goblin_shaman', x, y)
    m._tracking = True
    m._aware = True
    return m


def test_a_hurt_shaman_chants_a_ward_then_raises_it():
    d = open_room()
    hero = Hero(9, 5)
    m = hurt(_shaman(), 0.4)
    assert m.take_turn(hero, d, [m]) is False                 # the chant: its turn
    assert m._casting == 'smoke_ward'
    assert any('chant' in t.lower() for t, _u, _c in ai_lines.take(m))
    m.take_turn(hero, d, [m])                                  # the ward rises
    assert m.has_effect('spell_ward') and m.damage_ward == 0.5
    for _ in range(int(m.status_effects['spell_ward']) + 1):
        m.tick_effects()
    assert m.damage_ward == 0.0                                # it faded


def test_a_blow_breaks_the_chant_and_a_wound_ticking_does_not():
    d = open_room()
    hero = Hero(9, 5)
    m = hurt(_shaman(), 0.4)
    m.take_turn(hero, d, [m])
    assert m._casting
    m._dot_tick = True
    m.take_damage(1)
    m._dot_tick = False
    assert m._casting                                          # a bleed is not a blow
    m.take_damage(2)
    assert not m._casting
    assert caster_ai.cooldown(m, 'smoke_ward') > 0             # spent all the same
    m.take_turn(hero, d, [m])
    assert not m.has_effect('spell_ward')


def test_a_silenced_caster_casts_nothing():
    hero = Hero(9, 5)
    m = hurt(_shaman(), 0.4)
    m.add_effect('silenced', 5)
    assert caster_ai.choose(m, caster_ai.Context(hero, open_room(), [m])) is None


def test_a_silenced_lich_picks_no_spell_and_no_cast_bolt():
    """G's gates decide (attack_gates.blocks_attack: a voice is spoken, a
    ranged spell is cast, wards.is_cast): a silenced caster never picks a
    cast, from its book or from its bolts."""
    import attack_gates
    d = open_room()
    hero = Hero(9, 5)
    hero.status_effects = {'hasted': 9}
    m = hurt(make('lich', 5, 5), 0.4)
    m._tracking = True
    m.add_effect('silenced', 6)
    assert caster_ai.choose(m, caster_ai.Context(hero, d, [m])) is None
    assert caster_ai.turn(m, hero, d, [m], set()) is None
    pick = caster_ai.pick_attack(m, hero, m._distance_attacks())
    assert pick is None or not attack_gates.blocks_attack(m, pick)
    # A chant drawn up before the seal came down is let go, not fired.
    m2 = hurt(make('lich', 5, 5), 0.4)
    m2._tracking = True
    m2._casting = 'lich_ward'
    m2.add_effect('silenced', 6)
    assert caster_ai.turn(m2, hero, d, [m2], set()) is None and not m2.has_effect('spell_ward')


def test_an_evil_eye_is_not_spoken_and_a_seal_does_not_stop_it():
    hero = Hero(8, 5)
    m = make('green_hag', 5, 5)
    m._tracking = True
    m.add_effect('silenced', 6)
    ch = caster_ai.choose(m, caster_ai.Context(hero, open_room(), [m]))
    assert ch and ch['id'] == 'evil_eye'


def test_spell_turning_throws_a_curse_back(monkeypatch):
    d = open_room()
    hero = Hero(9, 5)
    hero.status_effects = {'spell_turning': 20}
    m = make('dark_cultist', 5, 5)
    m._tracking = True
    fail_saves(monkeypatch)
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    caster_ai.act(m, ch, hero, d, [m])
    caster_ai.turn(m, hero, d, [m], set())
    assert 'feared' not in hero.status_effects and m.has_effect('feared')


def test_no_spell_fits_an_unhurt_shaman_facing_a_hurt_hero():
    hero = Hero(9, 5, hp=200)
    hero.hp = 60                                               # the hero is losing: no curse
    m = _shaman()
    assert caster_ai.choose(m, caster_ai.Context(hero, open_room(), [m])) is None


def test_a_confused_or_out_of_sight_caster_forgets_its_book():
    d = open_room()
    hero = Hero(9, 5)
    m = hurt(_shaman(), 0.4)
    m.status_effects['confused'] = 4
    assert caster_ai.choose(m, caster_ai.Context(hero, d, [m])) is None
    m2 = hurt(_shaman(), 0.4)
    m2._tracking = False
    assert caster_ai.turn(m2, hero, d, [m2], set()) is None


def test_the_curse_waits_for_a_hero_who_is_winning_and_goes_the_riders_road(monkeypatch):
    d = open_room()
    hero = Hero(9, 5)
    m = make('cult_priest', 5, 5)
    m._tracking = True
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    assert ch and ch['id'] == 'binding_litany'
    fail_saves(monkeypatch)
    caster_ai.act(m, ch, hero, d, [m])                         # the chant
    assert m._casting == 'binding_litany'
    m._cast_ok = caster_ai.turn(m, hero, d, [m], set())        # the curse lands
    assert hero.status_effects.get('immobilized', 0) > 0
    # Steadying after it (control_immune) is a hidden timer the priest cannot
    # see (the lead's ruling, never omniscient): he may chant again, and the
    # grace turns the curse aside.
    hero.status_effects = {'control_immune': 3}
    m._spell_cd = {}
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    assert ch and ch['id'] == 'binding_litany'
    caster_ai.act(m, ch, hero, d, [m])
    caster_ai.turn(m, hero, d, [m], set())
    assert 'immobilized' not in hero.status_effects


def test_wax_in_the_ears_stops_a_spoken_curse(monkeypatch):
    import counters
    d = open_room()
    hero = Hero(9, 5)
    m = make('dark_cultist', 5, 5)
    m._tracking = True
    fail_saves(monkeypatch)
    monkeypatch.setattr(counters, 'blocks_rider',
                        lambda p, mm, atk, eff: ('wax', 'voice') if atk.get('delivery') == 'voice' else None)
    monkeypatch.setattr(counters, 'line', lambda p, a, b, mm: 'The wax in your ears keeps the words out.')
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    caster_ai.act(m, ch, hero, d, [m])
    caster_ai.turn(m, hero, d, [m], set())
    assert 'feared' not in hero.status_effects


def test_a_lich_dispels_a_timed_haste_but_never_a_worn_one():
    d = open_room()
    hero = Hero(9, 5)
    hero.status_effects = {'hasted': 10}
    m = make('lich', 5, 5)
    m._tracking = True
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    assert ch['kind'] == 'dispel'
    caster_ai.act(m, ch, hero, d, [m])
    assert 'hasted' not in hero.status_effects
    hero.status_effects = {'hasted': -1}                       # from his boots: not a spell
    m._spell_cd = {}
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    assert ch is None or ch['kind'] != 'dispel'


def test_a_kobold_sorcerer_puts_out_the_light_spell():
    d = open_room()
    hero = Hero(8, 5)
    hero.status_effects = {'light': 20}
    m = make('kobold_sorcerer', 5, 5)
    m._tracking = True
    assert caster_ai.turn(m, hero, d, [m], set()) is False
    assert 'light' not in hero.status_effects
    assert caster_ai.turn(m, hero, d, [m], set()) is None      # nothing lit: nothing to cast


def test_the_book_heals_only_its_own_side():
    d = open_room()
    hero = Hero(12, 5)
    m = make('drow_priestess', 5, 5)
    m._tracking = True
    friend = hurt(make('drow_warrior', 6, 5), 0.3)
    stranger = hurt(make('goblin', 4, 5), 0.2)
    caster_ai.turn(m, hero, d, [m, friend, stranger], set())
    assert m._heal_target is friend and friend.hp > int(friend.max_hp * 0.3)


def test_a_battle_mage_does_not_cast_fire_at_a_hero_who_wards_off_fire():
    hero = Hero(9, 5)
    hero.status_effects = {'fire_shield': 20}                  # it glows on him: it can see it
    m = make('battle_mage', 5, 5)
    pick = caster_ai.pick_attack(m, hero, m._distance_attacks())
    assert pick['name'] == 'Frost Bolt'
    hero.status_effects = {}
    hero.status_effects['slowed'] = 3                          # already slowed: the fire bolt
    assert caster_ai.pick_attack(m, hero, m._distance_attacks())['name'] == 'Fire Bolt'


def test_a_lich_tries_its_fear_then_blasts_a_hero_who_will_not_fear():
    hero = Hero(9, 5)
    m = make('lich', 5, 5)
    cands = m._distance_attacks()
    assert caster_ai.pick_attack(m, hero, cands)['name'] == 'Fear Gaze'
    hero.status_effects = {'feared': 3}                       # it can see him running
    assert caster_ai.pick_attack(m, hero, cands)['name'] == 'Cold Bolt'
    hero.status_effects = {'control_immune': 3}               # a hidden grace: it cannot know
    assert caster_ai.pick_attack(m, hero, cands)['name'] == 'Fear Gaze'
    hero.status_effects = {}
    hero.hp = 60                                              # badly hurt: finish him
    assert caster_ai.pick_attack(m, hero, cands)['name'] == 'Cold Bolt'


def test_a_thinking_caster_casts_by_the_book_as_a_plain_one_does():
    """A kind with the Tactical Mind's caster mind (data/minds.json) picks
    its spell in tactical_mind.choose_cast by the Caster's Book's rules."""
    import tactical_mind
    assert tactical_mind.mind_of(make('battle_mage')) == 'caster'
    d = open_room()
    hero = Hero(9, 5)
    hero.status_effects = {'fire_shield': 20}                  # a shield it can see
    m = make('battle_mage', 5, 5)
    for _ in range(10):                                        # never by chance
        assert tactical_mind.choose_cast(m, hero, d, [m])['name'] == 'Frost Bolt'
    plain = caster_ai.pick_attack(m, hero, m._distance_attacks())
    assert plain['name'] == 'Frost Bolt'
    hero.status_effects = {'slowed': 3}
    assert tactical_mind.choose_cast(m, hero, d, [m])['name'] == 'Fire Bolt'
    m.add_effect('silenced', 5)                                # a seal: no cast at all
    assert tactical_mind.choose_cast(m, hero, d, [m]) is None


def test_a_blinded_caster_wards_but_aims_nothing():
    d = open_room()
    hero = Hero(9, 5)
    hero.status_effects = {'hasted': 9}
    m = hurt(make('lich', 5, 5), 0.5)
    m.status_effects['blinded'] = 5
    ch = caster_ai.choose(m, caster_ai.Context(hero, d, [m]))
    assert ch and ch['kind'] == 'ward'


def test_the_same_fight_gives_the_same_spells():
    def run():
        random.seed(3)
        d = open_room()
        hero = Hero(9, 5)
        hero.status_effects = {'hasted': 9}
        m = make('lich', 5, 5)
        m._tracking = True
        out = []
        for i in range(12):
            if i == 4:
                hurt(m, 0.5)
            m.take_turn(hero, d, [m])
            m.tick_effects()
            out.append((m.__dict__.get('_casting'), tuple(sorted((m.__dict__.get('_spells_cast') or {}).items()))))
        return out
    assert run() == run()


def test_a_named_foe_or_an_ally_never_casts_from_a_book():
    hero = Hero(9, 5)
    m = hurt(_shaman(), 0.4)
    m.is_mini_boss = True
    assert caster_ai.choose(m, caster_ai.Context(hero, open_room(), [m])) is None
    a = hurt(_shaman(), 0.4)
    a.is_allied = True
    assert caster_ai.choose(a, caster_ai.Context(hero, open_room(), [a])) is None


# ===========================================================================
# Held Fast
# ===========================================================================

def _python(x=5, y=5):
    m = make('rock_python', x, y)
    m._aware = True
    m._tracking = True
    return m


def _constrict(m):
    return next(a for a in m.attacks if holds.spec_of(a))


def test_a_pythons_coils_take_hold_and_squeeze_every_turn(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    msg = holds.after_blow(m, hero, _constrict(m), 5, 'It hits.')
    assert 'coils close' in msg
    assert holds.is_held(hero) and holds.is_holder(m, hero) and hero.has_effect('held')
    monkeypatch.undo()
    before = hero.hp
    assert m.take_turn(hero, open_room(), [m]) is True         # its turn is the squeeze
    dmg, line = m.attack(hero)
    assert dmg > 0 and hero.hp == before - dmg and 'squeeze' in line


def test_a_hero_loosed_is_never_held(monkeypatch):
    hero = Hero(6, 5)
    hero.status_effects = {'free_action': 10}
    m = _python()
    fail_saves(monkeypatch)
    msg = holds.after_blow(m, hero, _constrict(m), 5, 'It hits.')
    assert not holds.is_held(hero) and 'nothing can hold you' in msg


def test_a_hero_steadying_after_a_hold_is_not_held_again(monkeypatch):
    hero = Hero(6, 5)
    hero.status_effects = {'control_immune': 3}
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    assert not holds.is_held(hero)


def test_one_holder_at_a_time_and_none_for_a_named_foe_or_an_ally(monkeypatch):
    fail_saves(monkeypatch)
    hero = Hero(6, 5)
    a, b = _python(), _python(7, 5)
    holds.after_blow(a, hero, _constrict(a), 5, '')
    holds.after_blow(b, hero, _constrict(b), 5, '')
    assert holds.is_holder(a, hero) and not b.__dict__.get('_holding')
    hero2 = Hero(6, 5)
    n = _python()
    n.is_boss = True
    holds.after_blow(n, hero2, _constrict(n), 5, '')
    assert not holds.is_held(hero2)
    al = _python()
    al.is_allied = True
    holds.after_blow(al, hero2, _constrict(al), 5, '')
    assert not holds.is_held(hero2)


def test_a_hard_blow_cuts_the_hero_free_and_a_bleed_does_not(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    monkeypatch.undo()
    m._dot_tick = True
    m.take_damage(m.max_hp // 5)
    m._dot_tick = False
    assert holds.validate(hero, [m]) == '' and holds.is_held(hero)
    m.take_damage(int(m.max_hp * 0.12))
    line = holds.validate(hero, [m])
    assert 'coils' in line and not holds.is_held(hero)
    assert hero.status_effects.get('control_immune', 0) >= status_effects.GRACE_TURNS
    assert not hero.has_effect('held') and not m.__dict__.get('_holding')


def test_the_hold_ends_when_the_holder_dies_flees_sleeps_or_is_parted(monkeypatch):
    for why in ('dead', 'flee', 'sleep', 'apart', 'feared'):
        fail_saves(monkeypatch)
        hero = Hero(6, 5)
        m = _python()
        holds.after_blow(m, hero, _constrict(m), 5, '')
        monkeypatch.undo()
        if why == 'dead':
            m.alive = False
        elif why == 'flee':
            m._flee_timer = 5
        elif why == 'sleep':
            m.status_effects['sleeping'] = 3
        elif why == 'apart':
            hero.x = 9                                         # teleported, shoved, pulled
        else:
            m.status_effects['feared'] = 3
        holds.validate(hero, [m])
        assert not holds.is_held(hero), why


def test_a_holder_takes_no_lane_step_and_squeezes_instead(monkeypatch):
    """The naga guardian is a ranged kind (src/lanes.py would step it back
    from a hero beside it); while it holds him it squeezes, and no lane
    rule moves it."""
    import lanes
    d = open_room()
    hero = Hero(6, 5)
    m = make('naga_guardian', 5, 5)
    m._aware = True
    m._tracking = True
    assert lanes.applies(m)
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, next(a for a in m.attacks if holds.spec_of(a)), 5, '')
    monkeypatch.undo()
    assert not lanes.applies(m)
    assert not lanes.back_off(m, hero, d, [m], set())
    for _ in range(3):
        assert m.take_turn(hero, d, [m]) is True and (m.x, m.y) == (5, 5)
        m.attack(hero)
    holds.release(hero, m, 'dead')
    assert lanes.applies(m)


def test_a_drinking_or_throwing_creature_spends_its_turn_before_any_lane():
    d = open_room()
    hero = Hero(8, 5)
    m = make('bandit_kingpin', 5, 5)
    m._aware = True
    m._tracking = True
    m._kit = ('potion_of_extra_healing',)
    hurt(m, 0.2)
    pos = (m.x, m.y)
    assert m.take_turn(hero, d, [m]) is False and (m.x, m.y) == pos    # it drank, it did not move


def test_a_silenced_holder_keeps_its_grip(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    m.add_effect('silenced', 5)
    holds.validate(hero, [m])
    assert holds.is_held(hero)


def test_the_hold_runs_out_with_its_status_and_the_grace_follows(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    assert hero.status_effects['held'] <= 4
    hero.status_effects.pop('held')
    assert holds.validate(hero, [m]) == ''
    assert not holds.is_held(hero) and not m.__dict__.get('_holding')


def test_the_struggle(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    freed, line = holds.struggle(hero, m, rng=random.Random(1))
    lo = type('R', (), {'randint': staticmethod(lambda a, b: a)})()
    hi = type('R', (), {'randint': staticmethod(lambda a, b: b)})()
    freed, line = holds.struggle(hero, m, rng=lo)
    assert not freed and 'coils' in line and holds.is_held(hero)
    freed, line = holds.struggle(hero, m, rng=hi)
    assert freed and not holds.is_held(hero)


def test_a_swallowed_hero_is_out_of_every_other_reach(monkeypatch):
    hero = Hero(6, 5)
    cube = make('gelatinous_cube', 5, 5)
    cube._aware = True
    other = make('goblin', 7, 5)
    fail_saves(monkeypatch)
    atk = next(a for a in cube.attacks if holds.spec_of(a))
    assert 'swallows you' in holds.after_blow(cube, hero, atk, 3, '')
    assert holds.swallowed(hero)
    assert holds.shields(hero, other) and not holds.shields(hero, cube)
    cube.alive = False
    assert 'climb out' in holds.validate(hero, [cube])


def test_a_drag_hauls_the_hero_toward_the_water_and_under_it(monkeypatch):
    d = open_room(20, 10)
    for x in range(1, 19):
        d.tiles[1][x] = WATER
    hero = Hero(6, 5)
    m = make('each_uisce', 6, 4)
    m._aware = True
    m._tracking = True
    fail_saves(monkeypatch)
    atk = next(a for a in m.attacks if holds.spec_of(a))
    holds.after_blow(m, hero, atk, 5, '')
    monkeypatch.undo()
    assert m.take_turn(hero, d, [m]) is True
    assert m.y == 3 and (hero.x, hero.y) == (6, 4)             # a tile toward the water, him after
    _dmg, line = m.attack(hero)
    assert 'drags you' in line
    lines = []
    for _ in range(3):
        hero.hp = hero.max_hp
        assert holds.validate(hero, [m]) == ''
        assert m.take_turn(hero, d, [m]) is True
        assert d.is_walkable(hero.x, hero.y)                   # never into the water itself
        lines.append(m.attack(hero)[1])
    assert holds.at_water(d, m.x, m.y) and any('under' in t for t in lines)


def test_a_drag_never_hauls_the_hero_onto_a_pit_or_a_trap(monkeypatch):
    d = open_room(20, 10)
    for x in range(1, 19):
        d.tiles[1][x] = WATER
    d.pits = {(6, 4)}
    hero = Hero(6, 5)
    m = make('each_uisce', 6, 4)
    m._aware = True
    m._tracking = True
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, next(a for a in m.attacks if holds.spec_of(a)), 5, '')
    monkeypatch.undo()
    m.take_turn(hero, d, [m])
    assert (hero.x, hero.y) == (6, 5)                          # not into the pit it left


def test_a_hold_survives_a_save_and_lets_go_when_the_holder_is_gone(monkeypatch):
    hero = Hero(6, 5)
    m = _python()
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, _constrict(m), 5, '')
    monkeypatch.undo()
    h2, ms = pickle.loads(pickle.dumps((hero, [m])))
    assert holds.validate(h2, ms) == '' and holds.is_holder(ms[0], h2)
    assert ms[0].take_turn(h2, open_room(), ms) is True
    h3, _ms = pickle.loads(pickle.dumps((hero, [m])))
    holds.validate(h3, [])                                    # a new floor's monsters
    assert not holds.is_held(h3)


def test_the_same_seed_gives_the_same_holds_and_squeezes():
    def run():
        random.seed(21)
        d = open_room()
        hero = Hero(6, 5, hp=5000)
        m = _python()
        out = []
        for _ in range(30):
            holds.validate(hero, [m])
            if m.take_turn(hero, d, [m]):
                dmg, line = m.attack(hero)
                out.append((dmg, line[:30], holds.is_held(hero)))
            hero.status_effects = {k: v - 1 for k, v in hero.status_effects.items() if v - 1 > 0}
            m.tick_effects()
        return out
    a = run()
    assert a == run() and any(held for _d, _l, held in a)


def test_an_old_save_has_no_hold_and_needs_none():
    hero = Hero(6, 5)
    m = _python()
    m.__dict__.pop('_uid', None)
    m.__dict__.pop('_holding', None)
    assert holds.validate(hero, [m]) == ''
    assert holds.holder_turn(m, hero, open_room(), [m], set()) is None
    assert holds.blow(m, hero) is None


# ===========================================================================
# Auras
# ===========================================================================

def test_a_fire_elemental_scorches_the_hero_beside_it_and_not_beyond():
    hero = Hero(6, 5, hp=300)
    m = make('fire_elemental', 5, 5)
    out = auras.pulse([m], hero, None)
    assert hero.hp == 300 - 9 and out and 'heat' in out[0][0].lower()
    hero.hp = 300
    hero.x = 8
    assert auras.pulse([m], hero, None) == [] and hero.hp == 300
    m.alive = False
    hero.x = 6
    assert auras.pulse([m], hero, None) == []


def test_two_heat_auras_burn_at_most_twice_the_strongest():
    hero = Hero(6, 5, hp=1000)
    ms = [make('fire_elemental', 5, 5), make('fire_elemental', 7, 5), make('fire_elemental', 6, 6)]
    auras.pulse(ms, hero, None)
    assert hero.hp == 1000 - 60


def test_dread_rolls_once_a_fight_and_only_when_seen(monkeypatch):
    hero = Hero(6, 5)
    m = make('dullahan_spawn', 5, 5)
    m._aware = True
    assert auras.pulse([m], hero, lambda _m: False) == []      # not seen: no dread
    fail_saves(monkeypatch)
    out = auras.pulse([m], hero, lambda _m: True)
    assert hero.has_effect('feared') and out
    hero.status_effects = {}
    assert auras.pulse([m], hero, lambda _m: True) == []       # once a fight
    m._lost_turns = 9                                          # it lost him: a new fight
    auras.pulse([m], hero, lambda _m: True)
    assert hero.has_effect('feared')


def test_a_stench_until_the_hero_masters_his_stomach(monkeypatch):
    hero = Hero(6, 5)
    m = make('ghast', 5, 5)
    m._aware = True
    fail_saves(monkeypatch)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    auras.pulse([m], hero, None)
    assert hero.has_effect('weakened')
    left = hero.status_effects['weakened']
    auras.pulse([m], hero, None)
    assert hero.status_effects['weakened'] == left             # never stacked while it lasts
    hero.status_effects = {}
    pass_saves(monkeypatch)
    out = auras.pulse([m], hero, None)
    assert 'master' in out[0][0] and not hero.has_effect('weakened')
    fail_saves(monkeypatch)
    assert auras.pulse([m], hero, None) == []                  # used to it for the fight


def test_no_aura_on_a_named_foe_or_an_encounter():
    hero = Hero(6, 5)
    m = make('fire_elemental', 5, 5)
    m.is_mini_boss = True
    assert auras.pulse([m], hero, None) == []
    m2 = make('fire_elemental', 5, 5)
    m2._npc_encounter_tag = 'x'
    assert auras.pulse([m2], hero, None) == []


# ===========================================================================
# Home Ground
# ===========================================================================

def _draugr(x=5, y=5):
    m = make('draugr', x, y)
    m._home = (5, 5)
    m._aware = True
    return m


def test_a_draugr_lets_the_hero_go_at_the_edge_of_its_mound():
    d = open_room(40, 12)
    m = _draugr(10, 5)
    hero = Hero(5 + 8 + 3, 5)                                  # past lair_radius + slack
    assert home_ground.leash(m, hero, d, [m], set(), True) is False
    assert m.x == 9                                            # a step home
    assert any('mound' in t for t, _u, _c in ai_lines.take(m))
    hero.x = 5 + 9                                             # in the slack: still let go
    assert home_ground.leash(m, hero, d, [m], set(), True) is False
    hero.x = 5 + 8                                             # back on its ground
    assert home_ground.leash(m, hero, d, [m], set(), True) is True


def test_no_leash_inside_the_ground_or_with_no_home_or_in_a_band():
    d = open_room(40, 12)
    m = _draugr()
    hero = Hero(5 + 9, 5)                                      # within radius + slack
    assert home_ground.leash(m, hero, d, [m], set(), True) is True
    m2 = make('draugr', 5, 5)
    m2.__dict__.pop('_home', None)                             # summoned, split, an old save
    hero.x = 30
    assert home_ground.leash(m2, hero, d, [m2], set(), True) is True
    m3 = _draugr()
    m3._band = 'b1'
    assert home_ground.leash(m3, hero, d, [m3], set(), True) is True
    m4 = make('goblin', 5, 5)
    m4._home = (5, 5)
    assert home_ground.leash(m4, hero, d, [m4], set(), True) is True


def test_on_its_own_ground_it_never_breaks():
    m = hurt(_draugr(), 0.1)
    m.ai_pattern = 'aggressive'
    m.fearless = False
    m.status_immune = []
    assert home_ground.on_home(m) and morale.style(m) == 'never'
    m.x = 30
    assert not home_ground.on_home(m)


# ===========================================================================
# Uses What It Carries
# ===========================================================================

def _captain(**kit):
    m = make('bandit_captain', 5, 5)
    m._aware = True
    m._tracking = True
    m._kit = tuple(kit.get('items', ('potion_of_healing',)))
    return m


def test_a_hurt_captain_drinks_his_potion_and_it_is_gone():
    hero = Hero(6, 5)
    m = hurt(_captain(), 0.3)
    hp0 = m.hp
    assert monster_kit.turn(m, hero, open_room(), [m], set()) is False
    assert m.hp == min(m.max_hp, hp0 + round(m.max_hp * 0.2))
    assert monster_kit.kit(m) == () and monster_kit.leftovers(m) == []
    assert m._kit_learn == 'potion_of_healing'
    assert monster_kit.turn(m, hero, open_room(), [m], set()) is None   # nothing left to drink


def test_no_drink_unhurt_or_for_a_named_foe_and_a_wound_that_will_not_close_wastes_it():
    hero = Hero(6, 5)
    m = _captain()
    assert monster_kit.turn(m, hero, open_room(), [m], set()) is None
    n = hurt(_captain(), 0.2)
    n.is_mini_boss = True
    assert monster_kit.turn(n, hero, open_room(), [n], set()) is None
    w = hurt(_captain(), 0.2)
    w.status_effects['heal_blocked'] = 5
    hp0 = w.hp
    monster_kit.turn(w, hero, open_room(), [w], set())
    assert w.hp == hp0 and monster_kit.kit(w) == ()


def test_a_thief_drinks_the_potion_he_stole_and_never_gives_it_back():
    from types import SimpleNamespace
    import theft
    hero = Hero(6, 5)
    m = hurt(make('bandit_thief', 5, 5), 0.2)
    m._tracking = True
    m._kit = ()
    pot = SimpleNamespace(id='potion_of_healing', name='potion of healing', x=0, y=0)
    other = SimpleNamespace(id='scroll_of_light', name='scroll', x=0, y=0)
    theft.carried(m).extend([pot, other])
    assert monster_kit.turn(m, hero, open_room(), [m], set()) is False
    assert pot not in m.stolen_items and other in m.stolen_items
    game = SimpleNamespace(ground_items=[], _display_name=lambda it: it.name)
    theft.give_back(game, m)
    assert game.ground_items == [other]                        # one item back, none twice


def test_a_marauder_throws_his_fire_pot_from_a_few_paces_and_not_beside_you():
    d = open_room()
    hero = Hero(8, 5)
    m = make('orc_marauder', 5, 5)
    m._tracking = True
    m._kit = ('flask_of_fire_oil',)
    assert monster_kit.turn(m, hero, d, [m], set()) is True
    atk = m._chosen_blow
    assert atk['type'] == 'fire' and atk['delivery'] == 'ranged' and monster_kit.kit(m) == ()
    m2 = make('orc_marauder', 5, 5)
    m2._tracking = True
    m2._kit = ('flask_of_fire_oil',)
    hero.x = 6
    assert monster_kit.turn(m2, hero, d, [m2], set()) is None
    hero.x = 8
    m2.add_effect('unstrung', 5)
    assert monster_kit.turn(m2, hero, d, [m2], set()) is None  # a thrown pot is a missile
    m3 = make('orc_marauder', 5, 5)
    m3._tracking = True
    m3._kit = ('flask_of_fire_oil',)
    m3.add_effect('silenced', 5)
    assert monster_kit.turn(m3, hero, d, [m3], set()) is True  # a seal stops no throw


def test_a_thrown_pot_takes_no_charge(monkeypatch):
    hero = Hero(8, 5, hp=500)
    m = make('orc_marauder', 5, 5)
    m._tracking = True
    m._kit = ('flask_of_fire_oil',)
    m._charge_ready = True
    monkeypatch.setattr(random, 'randint', lambda a, b: b)
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    assert monster_kit.turn(m, hero, open_room(), [m], set()) is True
    dmg, msg = m.attack(hero)
    assert dmg == 16 and 'CHARGES' not in msg and m._charge_ready


def test_the_kit_is_rolled_once_and_the_same_for_a_seed():
    def roll():
        random.seed(5)
        return [monster_kit.kit(make('bandit_kingpin', 5, 5)) for _ in range(20)]
    assert roll() == roll()
    m = make('bandit_kingpin', 5, 5)
    k = monster_kit.kit(m)
    assert monster_kit.kit(m) == k
    s = make('bandit_kingpin', 5, 5)
    s._is_summoned = True
    assert monster_kit.kit(s) == ()


def test_the_tell_says_what_this_one_carries():
    m = _captain()
    assert 'carries_potion' in tells.abilities(m)
    m._kit = ()
    assert 'carries_potion' not in tells.abilities(m)         # drunk, or never had one


def test_what_it_did_not_use_falls_as_real_items():
    m = _captain(items=('potion_of_healing', 'flask_of_fire_oil'))
    left = monster_kit.leftovers(m)
    assert sorted(i.id for i in left) == ['flask_of_fire_oil', 'potion_of_healing']
    assert monster_kit.leftovers(m) == []                      # never twice


# ===========================================================================
# Skittish, Not Suicidal (the leprechaun)
# ===========================================================================

def _lep(x=5, y=5):
    m = make('leprechaun', x, y)
    m._aware = True
    return m


def test_a_leprechaun_backs_off_from_a_hero_too_close():
    d = open_room()
    hero = Hero(10, 10)
    m = _lep(11, 10)
    assert m.take_turn(hero, d, [m]) is False
    assert max(abs(m.x - hero.x), abs(m.y - hero.y)) == 2


def test_a_cornered_leprechaun_offers_his_purse_once():
    tiles = [[WALL] * 6 for _ in range(3)]
    for x in range(1, 5):
        tiles[1][x] = FLOOR
    d = Dungeon(tiles, [Room(0, 0, 6, 3)], 6, 3, 2)
    hero = Hero(2, 1)
    m = _lep(1, 1)
    assert m.take_turn(hero, d, [m]) is False
    assert m._wants_bargain
    assert any('purse' in t for t, _u, _c in ai_lines.take(m))
    m.take_turn(hero, d, [m])
    assert not ai_lines.take(m)                                # no second offer line
    skittish.refuse(m)
    assert m.take_turn(hero, d, [m]) is True                   # at bay, it fights
    m2 = _lep(1, 1)
    m2.take_turn(hero, d, [m2])
    skittish.accept(m2)
    assert m2.treasure['gold'] == [0, 0] and m2._bargained


def test_a_pack_hunter_left_alone_is_no_coward_and_an_aggravated_hero_faces_a_fighter():
    hero = Hero(6, 5)
    m = make('bandit_thug', 5, 5)
    m.ai_pattern = 'cowardly'                                  # pack_dependent, alone
    assert skittish.turn(m, hero, open_room(), [m], set()) is None
    lep = _lep()
    hero.status_effects = {'aggravated': 5}
    assert skittish.turn(lep, hero, open_room(), [lep], set()) is None


def test_a_skittish_kind_darts_in_when_the_hero_turns_away():
    d = open_room()
    hero = Hero(10, 10)
    hero._facing_dx, hero._facing_dy = 1, 0                    # he stepped east
    m = make('ethereal_filcher', 7, 10)                        # three off, quick (speed 14)
    m._aware = True
    assert m.take_turn(hero, d, [m]) is True                   # in behind him
    assert m._adjacent_to(hero)
    assert m.take_turn(hero, d, [m]) is False                  # then off again
    assert not m._adjacent_to(hero)
    hero._facing_dx = -1                                       # he turns to face it
    m2 = make('ethereal_filcher', 6, 10)
    m2._aware = True
    m2.take_turn(hero, d, [m2])
    assert not m2._adjacent_to(hero)


# ===========================================================================
# The dancer's footwork
# ===========================================================================

def test_the_dancer_never_steps_into_a_pit_a_trap_or_out_of_her_gaze():
    d = open_room(12, 12)
    hero = Hero(6, 6)
    m = make('totentanz_dancer', 5, 6)
    occ = {(6, 6)}
    d.pits = {(5, 5), (7, 5), (7, 7)}
    d.traps = {(5, 7): {'type': 'spike'}, (6, 5): {'type': 'spike'}, (6, 7): {'type': 'spike'}}
    for _ in range(20):
        step = dancer.sidestep(m, hero, d, occ)
        assert step == (7, 6)
    d.pits |= {(7, 6)}
    assert dancer.sidestep(m, hero, d, occ) is None            # nowhere good: she stays


def test_a_gazer_keeps_her_eyes_on_the_hero():
    d = open_room(12, 12)
    hero = Hero(6, 6)
    m = make('totentanz_dancer', 5, 6)
    m.gaze_paralyze = 3
    import senses as _s
    real = _s.clear_view
    _s.clear_view = lambda x0, y0, x1, y1, dd: (x0, y0) == (7, 7)
    try:
        assert dancer.sidestep(m, hero, d, {(6, 6)}) == (7, 7)
    finally:
        _s.clear_view = real


# ===========================================================================
# Lurkers Keep Their Promise
# ===========================================================================

def test_an_unseen_ambusher_drops_within_two_with_a_surprise_blow():
    d = open_room()
    hero = Hero(10, 10)
    m = make('giant_spider', 13, 10)
    assert surprise.ambush_step(m, hero, d) == 'lurk'          # three off: it waits
    m.x = 12
    assert surprise.ambush_step(m, hero, d) == 'spring'
    m.take_turn(hero, d, [m])
    assert m._mimic_surprise and m._aware


def test_an_ambusher_spotted_first_has_no_surprise():
    d = open_room()
    hero = Hero(10, 10)
    m = make('giant_spider', 12, 10)
    m._aware = True                                            # his keen senses found it
    m.take_turn(hero, d, [m])
    assert not m._mimic_surprise


def test_a_mimic_of_a_known_kind_has_no_surprise():
    hero = Hero(6, 5)
    kinds = [k for k, v in MONS.items() if isinstance(v, dict) and v.get('ai_pattern') == 'mimic'
             and not v.get('is_boss') and not v.get('is_mini_boss')]
    m = make(kinds[0], 5, 5)
    hero.studied_monster_ids.add(kinds[0])
    m._mimic_turn(hero, open_room(), [m], set())
    assert m._aware and not m._mimic_surprise
    m2 = make(kinds[0], 5, 5)
    m2._mimic_turn(Hero(6, 5), open_room(), [m2], set())
    assert m2._mimic_surprise


def test_the_surprise_blow_lands_harder(monkeypatch):
    hero = Hero(6, 5, hp=10000)
    m = stub(attacks=[{'name': 'Bite', 'damage': '2d2+8', 'type': 'pierce', 'delivery': 'bite'}])
    monkeypatch.setattr(random, 'randint', lambda a, b: b)     # a natural 20
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    m._mimic_surprise = True
    dmg, msg = m.attack(hero)
    assert dmg == int(12 * 1.75) and 'drops on you from hiding' in msg


# ===========================================================================
# Second Shape
# ===========================================================================

def test_the_nahual_becomes_the_jaguar_at_half_health_once():
    d = open_room()
    hero = Hero(9, 5)
    m = make('nahual', 5, 5)
    m._aware = True
    hurt(m, 0.45)
    m.take_turn(hero, d, [m])
    assert m._enraged and m._form_applied and m.speed == 16
    assert [a['name'] for a in m.attacks] == ['Jaguar Claws', 'Skull-Piercing Bite']
    assert 'jaguar' in m._enrage_message.lower()
    assert second_shape.apply(m) == ''                         # never twice
    m2 = pickle.loads(pickle.dumps(m))
    assert m2.speed == 16 and m2.attacks[0]['name'] == 'Jaguar Claws'


# ===========================================================================
# Exclusions and the hooks
# ===========================================================================

def test_the_excluded_never_run_the_third_wave(monkeypatch):
    from monster import DeathMonster
    hero = Hero(6, 5)
    fail_saves(monkeypatch)
    for flag in ('is_allied', '_npc_encounter_tag', '_flavor_encounter_tag', '_is_unicorn'):
        m = hurt(_python(), 0.2)
        setattr(m, flag, True)
        assert ai_turn.turn(m, hero, open_room(), [m], set()) is None
        holds.after_blow(m, hero, _constrict(m), 5, '')
        assert not holds.is_held(hero), flag
    death = DeathMonster(5, 5)
    assert ai_turn.turn(death, hero, open_room(), [death], set()) is None
    nick = make('old_nickel', 5, 5) if 'old_nickel' in MONS else None
    if nick is not None:
        assert ai_turn.turn(nick, hero, open_room(), [nick], set()) is None


def test_a_creature_with_no_family_casts_and_holds_by_its_kind(monkeypatch):
    hero = Hero(6, 5)
    m = stub(tags=['caster'], spells=[{'id': 'w', 'kind': 'ward', 'share': 0.5, 'turns': 3,
                                       'weight': 5, 'when': {'self_hp_below': 0.5}}],
             attacks=[{'name': 'Coil', 'damage': '1d4', 'type': 'blunt', 'delivery': 'grapple',
                       'hold': {'kind': 'constrict', 'type': 'blunt'}}])
    m.family = None
    m.spells = [{'id': 'w', 'kind': 'ward', 'share': 0.5, 'turns': 3, 'weight': 5,
                 'when': {'self_hp_below': 0.5}}]
    hurt(m, 0.3)
    m._tracking = True
    assert caster_ai.turn(m, hero, open_room(), [m], set()) is False
    assert m.has_effect('spell_ward')
    fail_saves(monkeypatch)
    holds.after_blow(m, hero, m.attacks[0], 3, '')
    assert holds.is_holder(m, hero)


def test_a_stale_chosen_blow_is_dropped_at_the_next_turn():
    hero = Hero(6, 5)
    m = stub()
    m._chosen_blow = {'name': 'Old', 'damage': '1d4', 'type': 'fire', 'delivery': 'ranged'}
    ai_turn.turn(m, hero, open_room(), [m], set())
    assert '_chosen_blow' not in m.__dict__


def test_the_simulators_copies_share_no_state():
    m = _python()
    c = copy.copy(m)
    c._spell_cd = {'x': 3}
    caster_ai._spend(c, {'id': 'y', 'cooldown': 2})
    assert 'y' not in (m.__dict__.get('_spell_cd') or {})
    k = _captain()
    kc = copy.copy(k)
    monster_kit._spend(kc, 'potion_of_healing')
    assert monster_kit.kit(k) == ('potion_of_healing',)


# ===========================================================================
# The data
# ===========================================================================

def test_every_book_hold_aura_kit_and_bargain_is_well_formed():
    from monster_kit import item_defs
    named = {k for k, v in MONS.items() if isinstance(v, dict)
             and (v.get('is_boss') or v.get('is_mini_boss') or v.get('is_seal_demon'))}
    for k, v in MONS.items():
        if not isinstance(v, dict):
            continue
        names = {a.get('name') for a in v.get('attacks') or ()}
        for s in v.get('spells') or ():
            assert s['kind'] in caster_ai.KINDS and s.get('id'), (k, s)
            if s['kind'] == 'control':
                assert s.get('effect') and 1 <= int(s.get('duration', 0)) <= 4, (k, s)
                assert s.get('delivery', 'voice') in ('voice', 'gaze', 'ranged'), (k, s)
            if s['kind'] == 'hurt':
                assert s.get('attack') in names, (k, s)
        for a in v.get('attacks') or ():
            h = a.get('hold')
            if h is not None:
                assert h['kind'] in holds.KINDS and 1 <= int(h.get('max_turns', 4)) <= 4, k
                assert 0 < float(h.get('break_share', 0.1)) <= 0.25, k
                assert 'share' not in h, k                    # the squeeze is the attack's dice
                assert a.get('delivery') in ('grapple', 'bite', 'touch', 'blow'), k
                assert not a.get('effect'), (k, 'the old stand-in rider is gone')
        au = v.get('aura')
        if au is not None:
            assert au['kind'] in auras.AURA_KINDS and 1 <= int(au.get('radius', 1)) <= 3, k
            if au['kind'] in ('heat', 'cold'):
                assert 0 < float(au['share']) <= 0.05, k
        for e in v.get('kit') or ():
            assert e['item'] in item_defs() and 0 < e['chance'] <= 1, k
            assert monster_kit.heal_share(e['item']) > 0 or monster_kit.throw_spec(e['item']), k
        assert len(v.get('kit') or ()) <= 2, k
        if v.get('territorial') or v.get('spells') or v.get('aura') or v.get('kit') \
                or any(a.get('hold') for a in v.get('attacks') or ()):
            assert k not in named, (k, 'named foes keep their own fights')


def test_every_new_tell_is_in_the_order_and_reachable():
    d = tells.data()
    keys = ('hold_constrict', 'hold_swallow', 'hold_drag', 'aura_fear', 'aura_heat', 'aura_cold',
            'aura_stench', 'casts_ward', 'casts_curse', 'casts_dispel', 'casts_darkness',
            'casts_escape', 'carries_potion', 'carries_fire', 'territorial', 'bargains',
            'skittish', 'second_shape')
    seen = set()
    for k, v in MONS.items():
        if isinstance(v, dict) and v.get('symbol'):
            try:
                m = make(k)
            except Exception:
                continue
            if v.get('kit'):
                m._kit = tuple(e['item'] for e in v['kit'])    # this one carries all of it
            seen.update(tells.abilities(m))
    for key in keys:
        assert key in d['order'] and key in d['effects'] and key in seen, key


def test_the_rules_are_in_monster_ai_json():
    for sec in ('casters', 'holds', 'auras', 'home_ground', 'kit', 'skittish', 'surprise'):
        assert kind_data.rules(sec), sec


def test_the_simulator_knobs_default_on_and_switch_the_modules():
    import difficulty_sim as ds
    import sim_ai3
    for k in sim_ai3.KNOBS:
        assert ds.KNOB_DEFAULTS[k] == 1
    sim_ai3.apply_flags({k: 0 for k in sim_ai3.KNOBS})
    assert not (caster_ai.ENABLED or holds.ENABLED or auras.ENABLED or monster_kit.ENABLED)
    sim_ai3.apply_flags({})
    assert caster_ai.ENABLED and holds.ENABLED and auras.ENABLED and surprise.ENABLED
