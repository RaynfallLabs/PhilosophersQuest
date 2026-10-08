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


# ------------------------------------------------------------ the first floors

def test_deep_monsters_hit_harder_than_before_and_the_anchors_say_so():
    # Stat design step one made a prepared character about twice as durable
    # deep down; the damage anchors rose with depth to match (SCALE_LOG.md).
    a = floor_curve.DMG_ANCHORS
    assert a[1] < 1.5 and a[20] < 3.5                  # the top is untouched
    assert a[60] > 25 and a[100] > 33
    vals = [a[k] for k in sorted(a)]
    assert vals == sorted(vals)


def test_the_early_outliers_were_softened():
    d = _defs()
    elf = d['dark_elf']['attacks'][0]
    assert elf['effect_chance'] <= 0.25 and elf['effect_duration'] <= 4
    breath = d['anzu_bird']['attacks'][1]
    assert breath['effect'] == 'paralyzed' and breath['effect_duration'] <= 3


def test_meditation_gives_half_a_mana_bar_until_a_new_floor_is_reached():
    assert floor_curve.MEDITATE_FLOOR_SHARE == 0.5
    p = Player()
    p.max_mp, p.mp = 30, 0
    assert p.meditation_left() == 15
    got = sum(p.meditate(1) for _ in range(40))
    assert got == 15 and p.mp == 15 and p.meditation_left() == 0
    p.reset_floor_cook_caps()                 # any staircase: up, down, the cow level
    assert p.meditation_left() == 0           # (it used to refill here)
    p.new_floor_of_quiet()                    # a floor never stood on before
    assert p.meditation_left() == 15
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('self.player.new_floor_of_quiet()')
    assert 'deepest_floor_reached > _was_deepest' in src[i - 120:i]


def test_a_boss_that_is_swinging_or_hit_by_magic_has_not_been_left_alone():
    m = _mon('asterion_minotaur')
    m.take_damage(m.max_hp // 2)
    p = Player()
    p.max_hp = p.hp = 10 ** 6
    p.x, p.y = 3, 4
    hurt = m.hp
    for _ in range(80):                       # he attacks every turn; nobody hits him
        m.tick_effects()
        m.attack(p)
    assert m.hp == hurt and m.fury_mult() > 1.0
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert src.count('target._unhurt_turns = 0') >= 3      # missiles and smite count as hurt
    assert _mon('asterion_minotaur').fury_message.startswith("Asterion's breath")


def test_dodge_lives_in_the_blow_and_spares_no_one_from_breath():
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    i = src.index('_dodge = getattr(player, \'dodge_chance\', None)')
    assert 'not is_breath' in src[i:i + 300]
    combat = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert 'dodge_chance()' not in combat
    p = Player()
    p.DEX = 40
    for effect in ('stunned', 'frozen', 'paralyzed'):
        q = Player()
        q.DEX = 40
        q.add_effect(effect, 3)
        assert q.dodge_chance() == 0.0, effect
    assert p.dodge_chance() > 0


def test_the_dead_are_not_offered_gifts_or_given_pet_turns():
    main = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = main.index('self._do_monster_turns()')
    assert 'if not self.player.is_dead():' in main[i:i + 200]
    combat = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert 'story_key and self.player.is_dead()' in combat
    assert 'self.state != STATE_PLAYER or self.player.is_dead()' in combat


def test_a_gate_boss_mends_for_the_time_spent_on_another_floor():
    m = _mon('medusa_gorgon')
    m.take_damage(m.max_hp // 2)
    hurt = m.hp
    assert m.mend_for_absence(10) == 0 and m.hp == hurt      # a quick trip upstairs
    assert m.mend_for_absence(500) > 0 and m.hp == m.max_hp and m._recovered_note
    rat = _mon('giant_rat')
    rat.take_damage(max(1, rat.max_hp // 2))
    assert rat.mend_for_absence(500) == 0
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert '_m._left_at_turn = self.turn_count' in src
    assert '_m.mend_for_absence(self.turn_count - int(_left))' in src
