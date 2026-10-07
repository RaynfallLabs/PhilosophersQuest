"""Phase 2 of the rebalance (2026-10): what makes a gate boss a gate, how
far rest mends, and the easy first floors.

Logic tests: a boss fight at floor 20 and a long rest are not things a
quick play-test shows reliably.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402
import monster as monster_mod  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

GATES = ('asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf',
         'abaddon_destroyer')


def _defs():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def _mon(kind, **over):
    d = dict(_defs()[kind], id=kind)
    d.update(over)
    return Monster(d, 3, 3)


# ---------------------------------------------------------- a boss left alone

def test_every_gate_boss_recovers_when_left_and_nothing_else_does():
    defs = _defs()
    flagged = {k for k, d in defs.items() if isinstance(d, dict) and d.get('recovers_when_left')}
    assert flagged == set(GATES)


def test_a_gate_boss_heals_once_the_challenger_backs_off():
    m = _mon('medusa_gorgon')
    m.take_damage(m.max_hp // 2)
    hurt = m.hp
    for _ in range(monster_mod.RECOVER_AFTER_TURNS - 1):
        m.tick_effects()
    assert m.hp == hurt                               # still in the fight
    m.tick_effects()
    assert m.hp > hurt and m._recovered_note
    for _ in range(60):
        m.tick_effects()
    assert m.hp == m.max_hp                           # a long rest undoes the lot


def test_hitting_the_boss_keeps_it_from_recovering():
    m = _mon('fenrir_wolf')
    m.take_damage(m.max_hp // 2)
    for _ in range(100):
        m.tick_effects()
        before = m.hp
        if _ % 10 == 0:
            m.take_damage(1)
            assert m.hp <= before
    assert m.hp < m.max_hp // 2 + 1


def test_asterions_hiding_is_shorter_than_the_recovery_wait():
    # tools/balance/difficulty_sim.ASTERION_AWAY_TURNS: he is out of reach
    # for 9 to 12 turns at a time; that must not count as being left alone.
    assert monster_mod.RECOVER_AFTER_TURNS >= 20


def test_an_ordinary_monster_never_recovers_this_way():
    m = _mon('giant_rat')
    m.take_damage(max(1, m.max_hp // 2))
    hurt = m.hp
    for _ in range(80):
        m.tick_effects()
    assert m.hp == hurt


# ----------------------------------------------------------------------- fury

def test_asterion_hits_harder_the_longer_the_fight_lasts():
    d = _defs()['asterion_minotaur']
    assert 0 < d['fury_per_attack'] <= 0.05 and d['fury_cap'] <= 1.5 and d['fury_message']
    m = _mon('asterion_minotaur')
    assert m.fury_mult() == 1.0 and m.fury_line() == ''
    p = Player()
    p.max_hp = p.hp = 10 ** 6
    p.x, p.y = 3, 4
    for _ in range(200):
        m.attack(p)
    assert m.fury_mult() == 1.0 + m.fury_cap           # capped
    said = m.fury_line()
    assert said and m.fury_line() == ''               # told once per step
    # left alone, he cools
    for _ in range(monster_mod.RECOVER_AFTER_TURNS):
        m.tick_effects()
    assert m.fury_mult() == 1.0


def test_fury_is_asterions_alone_for_now():
    with_fury = [k for k, d in _defs().items() if isinstance(d, dict) and d.get('fury_per_attack')]
    assert with_fury == ['asterion_minotaur']
    assert _mon('giant_rat').fury_mult() == 1.0


def test_old_saves_load_without_the_new_monster_fields():
    m = _mon('giant_rat')
    for name in ('recovers_when_left', '_unhurt_turns', 'fury_per_attack', 'fury_cap',
                 '_fury_swings', '_fury_told', 'fury_message', '_recovered_note'):
        m.__dict__.pop(name, None)
    m.tick_effects()
    assert m.fury_mult() == 1.0 and m.fury_line() == ''


# ------------------------------------------------------------- rest mends so far

def test_rest_mends_to_sixty_percent_and_no_further():
    assert floor_curve.REST_MENDS_TO == 0.60
    assert floor_curve.rest_room(10, 100) == 50
    assert floor_curve.rest_room(60, 100) == 0
    assert floor_curve.rest_room(95, 100) == 0
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('def _tick_hp_regen')
    body = src[i:src.index('\n    def ', i + 10)]
    assert 'rest_room(self.player.hp, self.player.max_hp)' in body
    assert 'min(base_regen, room)' in body


def test_waiting_still_costs_food():
    src = open(os.path.join(ROOT, 'src', 'game_input.py'), encoding='utf-8').read()
    i = src.index('self.add_message("You wait.", \'info\')')
    assert 'self._tick_sp()' in src[i:i + 900]


def test_meditation_gives_half_a_mana_bar_a_floor():
    assert floor_curve.MEDITATE_FLOOR_SHARE == 0.5
    p = Player()
    p.max_mp, p.mp = 30, 0
    assert p.meditation_left() == 15
    got = sum(p.meditate(1) for _ in range(40))
    assert got == 15 and p.mp == 15 and p.meditation_left() == 0
    assert p.meditate(1) == 0
    p.reset_floor_cook_caps()                          # a new floor
    assert p.meditation_left() == 15
    p.mp = p.max_mp
    assert p.meditate(5) == 0 and p.meditation_left() == 15    # full: nothing spent
    old = Player()
    old.__dict__.pop('_meditated_this_floor', None)             # a save from before
    assert old.meditation_left() > 0
    src = open(os.path.join(ROOT, 'src', 'game_input.py'), encoding='utf-8').read()
    assert 'self.player.meditate(1)' in src and 'self.player.restore_mp(1)' not in src


# ------------------------------------------------------------ the first floors

def test_the_first_floors_go_easy_and_the_deep_ones_do_not():
    assert floor_curve.early_mercy(1) == floor_curve.early_mercy(13) == 0.75
    assert 0.75 < floor_curve.early_mercy(20) < 1.0
    assert floor_curve.early_mercy(26) == floor_curve.early_mercy(90) == 1.0
    p = Player()
    p.max_hp = p.hp = 1000
    p._mercy = 0.75
    assert p.take_damage(100, 'physical') == 75
    p._mercy = 1.0
    assert p.take_damage(100, 'physical') == 100


def test_mercy_is_set_only_around_an_ordinary_monsters_blow():
    src = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    i = src.index('floor_curve.early_mercy(self.dungeon_level)')
    block = src[i - 120:i + 260]
    assert 'm._is_named_foe()' in block and 'finally:' in block
    assert 'self.player._mercy = 1.0' in block


def test_deep_monsters_hit_harder_than_before_and_the_anchors_say_so():
    # Stat design step one made a prepared character about twice as durable
    # deep down; the damage anchors rose with depth to match (SCALE_LOG.md).
    a = floor_curve.DMG_ANCHORS
    assert a[1] < 1.5 and a[20] < 3.5                  # the top is untouched
    assert a[60] > 30 and a[100] > 38
    vals = [a[k] for k in sorted(a)]
    assert vals == sorted(vals)


def test_the_early_outliers_were_softened():
    d = _defs()
    elf = d['dark_elf']['attacks'][0]
    assert elf['effect_chance'] <= 0.25 and elf['effect_duration'] <= 4
    breath = d['anzu_bird']['attacks'][1]
    assert breath['effect'] == 'paralyzed' and breath['effect_duration'] <= 3
