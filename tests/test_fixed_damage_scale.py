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


def test_monster_regeneration_was_carried_up_with_hit_points():
    import json
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    assert data['abaddon_destroyer']['regeneration'] >= 60     # was 15 on a 6,000 HP boss
    log = open(os.path.join(ROOT, 'tools', 'balance', 'SCALE_LOG.md'), encoding='utf-8').read()
    assert 'regen catch-up: yes' in log
