"""Fixed damage numbers follow the size of the dungeon's monsters.

Monster HP was re-sized (about x3 near the top, x5 deep) when weapons gained
a damage step per tier. Weapon and spell damage followed through their own
tables. Everything else that hurts a monster by a fixed amount is passed
through floor_curve.scaled so it stays worth what it was worth.
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402


def test_power_scale_is_never_below_one_and_is_larger_deep():
    vals = [floor_curve.power_scale(f) for f in range(1, 101)]
    assert min(vals) >= 1.0
    assert floor_curve.power_scale(60) > floor_curve.power_scale(1)
    assert floor_curve.scaled(0, 50) == 0
    assert floor_curve.scaled(10, 60) == round(10 * floor_curve.power_scale(60))


def test_poison_on_a_monster_is_a_share_of_its_health():
    import json
    from monster import POISON_DIVISOR, Monster
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    deep = next(k for k, v in data.items() if v.get('peak_weight', 0) > 0
                and 60 <= v.get('peak_floor', 0) <= 70 and not v.get('is_mini_boss'))
    m = Monster({**data[deep], 'id': deep}, 1, 1)
    m.status_effects['poisoned'] = 3
    before = m.hp
    m.tick_effects()
    assert before - m.hp == max(1, m.max_hp // POISON_DIVISOR) > 1


def test_pets_hit_for_the_floor_and_level_at_the_old_pace():
    from pet_system import Pet
    src = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert 'floor_curve.scaled(pet.get_attack_damage(quiz_acc)' in src
    assert 'floor_curve.scaled(pet.base_damage, self.dungeon_level)' in src
    calls = []
    stub = types.SimpleNamespace(kills_count=0, gain_xp=lambda xp: calls.append(xp) or [])
    Pet.gain_xp_from_kill(stub, 5600, 60)        # a floor-60 monster today
    Pet.gain_xp_from_kill(stub, 5600)            # the same number at the old scale
    assert calls[0] < calls[1]
    assert abs(calls[0] - (3 + int(5600 / floor_curve.power_scale(60)) // 10)) <= 1


def test_hero_specials_scale_and_huge_follows_the_floor():
    import hero_specials
    ordinary = types.SimpleNamespace(is_boss=False, peak_floor=80, min_level=75,
                                     max_hp=int(floor_curve.target_hp(80)))
    giant = types.SimpleNamespace(is_boss=False, peak_floor=80, min_level=75,
                                  max_hp=int(3 * floor_curve.target_hp(80)))
    assert not hero_specials.is_boss_or_huge(ordinary)    # was "huge" at > 500 HP
    assert hero_specials.is_boss_or_huge(giant)
    assert hero_specials.is_boss_or_huge(types.SimpleNamespace(is_boss=True, max_hp=10))
    src = open(os.path.join(ROOT, 'src', 'hero_specials.py'), encoding='utf-8').read()
    assert src.count('_floor_scaled(') >= 3


def test_every_fixed_source_goes_through_the_scale():
    """Source-level: each site that was a bare number or dice roll."""
    def has(name, *needles):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        for n in needles:
            assert n in src, (name, n)
    has('combat.py',
        "_floor_scaled(_ab_roll(weapon.abaddon_bonus_damage), _floor)",    # weapon bonus dice
        "_floor_scaled(_tb_roll(_bt_dice), _floor)",                       # bonus vs tag
        "_floor_scaled(ammo.damage_bonus, _floor)",                        # ammo
        "_floor_scaled(unarmed_bonus, _floor)",                            # Beowulf
        "_floor_scaled(3, _floor)")                                        # Helm of Leonidas
    has('game_combat.py',
        "floor_curve.scaled(_fb_roll(dice), self.dungeon_level)",          # stuffie breath
        "floor_curve.scaled(_pit_roll('1d4'), self.dungeon_level)",        # pit fall
        "floor_curve.scaled(random.randint(2, 9), self.dungeon_level)")    # fire/cold shield
    has('game_magic.py',
        "_floor_scaled(_rng.randint(5, 15), self.dungeon_level)",          # wand blast
        "_floor_scaled(int(base_dmg * _chain_mult), self.dungeon_level)")  # earth scroll
    has('game_menus.py', "_floor_scaled(_es_roll('4d8'), self.dungeon_level)")
    has('main.py',
        "_floor_scaled(random.randint(1, 6), self.dungeon_level)",         # lightning aura
        "_floor_scaled(_dice_roll(dmg_str), self.dungeon_level)")          # trap on a monster


def test_bare_hands_are_sized_to_the_floor():
    """Unarmed base was a flat 2: fists have no material to carry them deeper."""
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    i = src.index("max(1, round(2 * (1 + max(0, player.STR - 10) / 10.0))), _floor)")
    assert '_floor_scaled(' in src[i - 60:i]
    assert floor_curve.scaled(2, 60) >= 8


def test_monster_regeneration_was_carried_up_with_hit_points():
    import json
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    assert data['abaddon_destroyer']['regeneration'] >= 60     # was 15 on a 6,000 HP boss
    log = open(os.path.join(ROOT, 'tools', 'balance', 'SCALE_LOG.md'), encoding='utf-8').read()
    assert 'regen catch-up: yes' in log
