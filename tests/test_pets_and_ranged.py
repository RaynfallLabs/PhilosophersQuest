"""Phase 4 of the rebalance (2026-10): companions and distance.

A pet that keeps pace with the dungeon is worth a quarter of the player's
attack at every depth and can take several hits; ranged combat is a
specialist tool. Logic tests: pet strength at floor 80 is not something a
quick play-test reaches.
"""
import os
import pickle
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402
from pet_system import FenrirPet, Pet, _SPECIES  # noqa: E402


def _pet(level):
    p = Pet(next(iter(_SPECIES)))
    p.level = level
    p._refresh_stats()
    p.hp = p.max_hp
    return p


def test_a_pet_can_take_several_hits_at_every_depth():
    import json
    import statistics
    from dice import roll
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    for level in (10, 30, 50, 70, 90):
        hits = [statistics.mean(roll(m['attacks'][0]['damage']) for _ in range(40))
                for m in mons.values()
                if isinstance(m, dict) and m.get('attacks')
                and abs((m.get('peak_floor') or 1) - level) <= 3
                and not m.get('is_boss') and not m.get('is_mini_boss')]
        typical = statistics.median(hits)
        assert _pet(level).max_hp / typical >= 3.5, (level, typical)   # was 2.3 at floor 60


def test_pet_regeneration_is_a_share_of_its_health():
    pet = _pet(80)
    pet.hp = 1
    for _ in range(3):
        pet.tick_regen()
    assert pet.hp == 1 + max(1, int(pet.max_hp * floor_curve.PET_REGEN_SHARE)) > 2


# ---------------------------------------------------------------- ranged (D4)

def test_a_shot_gets_no_stat_multiplier_and_a_blade_does():
    """Decision D4: ranged is a specialist's tool, first strike and safety,
    paid for in ammunition and damage. 'Ranged hits way too hard' was a
    standing bug whenever a bow shared the blade's Strength multiplier."""
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    assert 'str_factor = 1.0 if is_ranged else 1.0 + max(0, player.STR - 10) * 0.03' in src


def test_a_bow_is_no_stronger_than_a_blade_of_the_same_stuff():
    import items
    tpl = items.load_templates('weapons')
    ranged = {k: v for k, v in tpl.items() if v.get('requires_ammo')}
    melee = {k: v for k, v in tpl.items() if not v.get('requires_ammo')}
    assert len(ranged) >= 4
    top_melee = max(float(v.get('damage_modifier', 1.0)) for v in melee.values())
    for k, v in ranged.items():
        assert float(v.get('damage_modifier', 1.0)) <= top_melee, k
        assert int(v.get('reach') or 0) >= 4, k


def test_a_floor_gives_a_handful_of_shots_not_a_quiver_for_every_fight():
    import random
    import container_system as cs
    import level_manager
    from items import Container
    random.seed(2)
    lm = level_manager.LevelManager()
    lm._maybe_spawn_bones = lambda *a, **k: None
    shots = floors = 0
    for floor in range(3, 100, 6):
        if floor % 20 == 0:
            continue
        _d, _m, its = lm.generate(floor)
        floors += 1
        found = list(its)
        for it in its:
            if isinstance(it, Container):
                found += cs._generate_loot_from_template(it, floor)
        shots += sum(int(getattr(i, 'count', 1) or 1) for i in found
                     if getattr(i, 'ammo_type', None))
    per_floor = shots / floors
    assert 6 <= per_floor <= 40, per_floor          # measured 15 to 31 by sample: about half a floor's attacks
