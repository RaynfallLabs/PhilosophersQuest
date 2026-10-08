"""LORE, NOT FLOOR (Brandon's ruling, 2026-10-07).

A thing's power is decided by what it is and written as a real number in
its data. Nothing in the running game multiplies damage or health by the
dungeon floor at the moment it lands, and nothing changes a weapon's maths
tier by depth. These tests exist so that mistake cannot quietly come back:
it was made three times (floor_curve.scaled, early mercy, hero weapon
growth).
"""
import json
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)

import floor_curve  # noqa: E402


def _sources():
    for name in sorted(os.listdir(SRC)):
        if name.endswith('.py'):
            with open(os.path.join(SRC, name), encoding='utf-8') as f:
                yield name, f.read()


def test_no_game_code_multiplies_by_the_floor():
    banned = ('floor_curve.scaled(', '_floor_scaled(', 'import scaled', 'early_mercy',
              'grow_signature_weapon', 'grows_with_depth', 'typical_weapon_base',
              'hero_weapon_share', '_mercy')
    hits = []
    for name, text in _sources():
        for word in banned:
            if word in text:
                hits.append((name, word))
        if name != 'floor_curve.py' and re.search(r'\bpower_scale\(', text):
            hits.append((name, 'power_scale('))
    assert not hits, hits
    assert not hasattr(floor_curve, 'scaled')
    assert not hasattr(floor_curve, 'early_mercy')


def test_nothing_writes_a_weapons_tier_after_it_is_made():
    """A weapon's maths tier is fixed: the material's for a common, its own
    for a unique. No code may assign quiz_tier outside the item classes."""
    writers = []
    for name, text in _sources():
        for m in re.finditer(r'^(.*)\.quiz_tier\s*=[^=]', text, flags=re.M):
            line = m.group(0).strip()
            if name == 'items.py' and line.startswith('self.quiz_tier'):
                continue                              # the constructors
            writers.append((name, line[:80]))
    assert not writers, writers


def test_a_share_of_health_is_a_share_of_the_targets_own_health():
    assert floor_curve.wound(0.05, 1000) == 50
    assert floor_curve.wound(0.05, 1000, named=True) == 5        # a tenth, for named foes
    assert floor_curve.wound(0.0, 1000) == 0
    assert floor_curve.wound(0.01, 10) == 1                      # at least 1
    assert floor_curve.power_share(0) == 0.0
    assert abs(floor_curve.power_share(12) - 0.10) < 1e-9
    assert floor_curve.power_share(1000) == floor_curve.POWER_CAP


def test_hero_weapons_are_fixed_artifacts_placed_by_lore():
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        w = json.load(f)
    # found in the dungeon AND a hero's starting reward: a real drop floor
    for wid, tier, low in (('romulus_spear', 2, 20), ('achilles_spear', 3, 35),
                           ('prometheus_torch', 3, 45)):
        v = w[wid]
        assert v['quiz_tier'] == v['tier'] == tier, wid
        assert low <= v['min_level'] < 100 and v['peak_floor'] > v['min_level'], wid
        assert v['base_damage'] >= 25, wid
    # locked to their builds
    for wid, tier in (('witcher_silver_blade', 2), ('zireael', 3), ('boomstick', 3),
                      ('chainsaw_prosthetic', 3)):
        v = w[wid]
        assert v['quiz_tier'] == tier and v['min_level'] >= 9999, wid
        assert v['base_damage'] >= 25, wid
    # lore order, not floor order
    assert (w['romulus_spear']['base_damage'] < w['achilles_spear']['base_damage']
            < w['prometheus_torch']['base_damage'])


def test_dad_punches_for_9999_at_tier_one_with_a_stupid_multiplier():
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        punch = json.load(f)['punch_in_the_face']
    assert punch['base_damage'] == 9999 and punch['quiz_tier'] == 1 and punch['tier'] == 1
    assert punch['chain_exponent'] >= 3.0
    assert punch['min_level'] >= 9999                 # locked to the build


def test_a_hero_starts_with_the_weapon_as_written():
    import items
    import welcome_screen
    by_id = {x.id: x for x in items.load_items('weapon')}
    named = {b['_start_weapon'] for b in welcome_screen.SECRET_BUILDS.values()
             if isinstance(b.get('_start_weapon'), str)}
    assert {'achilles_spear', 'romulus_spear', 'prometheus_torch', 'punch_in_the_face'} <= named
    assert all(n in by_id for n in named)
    main = open(os.path.join(SRC, 'main.py'), encoding='utf-8').read()
    i = main.index("start_weapon  = b.get('_start_weapon', None)")
    assert 'base_damage' not in main[i:i + 1200] and 'quiz_tier' not in main[i:i + 1200]


def test_ammunition_and_bonus_dice_are_real_numbers_in_the_data():
    with open(os.path.join(ROOT, 'data', 'items', 'ammo.json'), encoding='utf-8') as f:
        ammo = json.load(f)
    assert ammo['iron_arrow']['damage_bonus'] == 0
    order = [ammo[k]['damage_bonus'] for k in ('steel_arrow', 'hardened_gold_arrow',
                                               'diamond_arrow', 'dragonbone_arrow')]
    assert order == sorted(order) and order[0] >= 3 and order[-1] >= 20
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        sword = json.load(f)['sword_of_michael']
    assert sword['abaddon_bonus_damage'] == '22d10'
    assert sword['bonus_damage_vs_tag']['demon'] == '9d8'


def test_starting_constitution_is_worth_what_every_other_point_is():
    from player import Player
    p = Player()
    assert p.max_hp == 30 and p.starting_max_hp() == 30
    p.CON = 18
    assert p.starting_max_hp() == 30 + 8 * p.HP_PER_CON
    p.CON = 5
    assert p.starting_max_hp() == 30 - 5 * p.HP_PER_CON
    main = open(os.path.join(SRC, 'main.py'), encoding='utf-8').read()
    assert 'self.player.max_hp = self.player.starting_max_hp()' in main
    assert 'BASE_HP + self.player.CON' not in main


def test_a_save_from_the_one_point_rule_is_brought_to_the_three_point_rule_once():
    import pickle
    from player import Player
    p = Player()
    p.CON = 15                                   # a +5 ring, applied at 1 HP a point
    p.max_hp = p.hp = 35
    state = dict(p.__getstate__()) if hasattr(p, '__getstate__') else dict(p.__dict__)
    state.pop('_con_hp_rule', None)
    old = Player.__new__(Player)
    old.__setstate__(state)
    assert old.max_hp == 45 and old._con_hp_rule == 3
    old.apply_stat_bonus('CON', -5)              # the ring comes off
    assert old.max_hp == 30                      # exactly baseline, not below it
    again = pickle.loads(pickle.dumps(old))
    assert again.max_hp == 30                    # and only once


def test_pets_come_from_a_data_table_by_their_own_level():
    import pet_system
    with open(os.path.join(ROOT, 'data', 'pet_growth.json'), encoding='utf-8') as f:
        table = json.load(f)
    assert len(table['health']) == len(table['bite']) == 100
    assert table['health'] == sorted(table['health']) and table['bite'] == sorted(table['bite'])
    pet = pet_system.Pet(next(iter(pet_system._SPECIES)))
    pet.level = 60
    pet._refresh_stats()
    assert pet.max_hp == table['health'][59] and pet.base_damage == table['bite'][59]
    assert not hasattr(pet, 'damage_on')
    wolf = pet_system.FenrirPet()
    assert wolf.base_damage == wolf.FENRIR_BITE > table['bite'][-1]
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert "'data/pet_growth.json'" in spec


def test_what_a_summoning_calls_up_is_set_by_the_spell():
    import game_magic
    assert game_magic.SUMMON_GUARDIAN_LEVEL < game_magic.GATE_ALLY_LEVEL
    src = open(os.path.join(SRC, 'game_magic.py'), encoding='utf-8').read()
    assert 'pet.level = max(1, self.dungeon_level' not in src
    assert 'pet.level = max(3, self.dungeon_level' not in src
