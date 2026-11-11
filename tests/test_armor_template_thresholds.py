"""Equip thresholds follow the rule (Brandon, bug bash 3.3.2): "more powerful
gear has a higher tier, complexity and benefit set the threshold".

Complexity is the template's weight class (light 1, medium 2, heavy 3,
data/gear_rules.json); benefit is the enchantment tier (+1 at III-IV, +2 at
V); at most 5. The material no longer sets the tier: a primordial-stone
plate with no enchantment is tier 1 and asks 3, an enchanted one asks more.
Shields follow the same rule (they had no threshold of their own: every
shield asked 2).
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


COMPLEXITY = {'light': 1, 'medium': 2, 'heavy': 3}


def _templates(kind='armor'):
    out = {}
    for path in glob.glob(str(ROOT / "data" / "templates" / kind / "*.json")):
        name = os.path.basename(path)[:-5]
        with open(path, encoding='utf-8') as f:
            out[name] = json.load(f)
    return out


def test_every_template_says_its_weight_class():
    """No template missing the field: it sets the complexity."""
    for kind in ('armor', 'shields'):
        missing = [n for n, t in _templates(kind).items()
                   if t.get('armor_class_tier') not in COMPLEXITY]
        assert not missing, (kind, missing)


def test_no_template_writes_its_own_threshold():
    """The threshold is the rule's, not the file's (gear.equip_threshold)."""
    stray = [n for n, t in _templates().items() if 'equip_threshold' in t]
    assert not stray, stray


def test_total_templates_covered():
    assert len(_templates()) >= 30


def test_class_tier_distribution():
    by_tier = {'light': 0, 'medium': 0, 'heavy': 0}
    for t in _templates().values():
        by_tier[t['armor_class_tier']] += 1
    assert by_tier['light'] >= 8
    assert by_tier['medium'] >= 8
    assert by_tier['heavy'] >= 8


def test_plain_pieces_ask_their_complexity():
    from items import instantiate_armor
    assert instantiate_armor('leather', 'leather').equip_threshold == 1
    assert instantiate_armor('ringmail', 'ring_iron').equip_threshold == 2
    assert instantiate_armor('plate', 'damascus_steel').equip_threshold == 3


def test_benefit_adds_to_complexity_and_five_is_the_most():
    import gear
    from items import instantiate_armor
    for level, extra in ((1, 0), (2, 0), (4, 0), (5, 1), (8, 1), (9, 2), (10, 2)):
        a = instantiate_armor('plate', 'damascus_steel', level=level)
        assert a.equip_threshold == min(5, 3 + extra), level
        assert a.tier == a.quiz_tier == gear.tier_for_level(level), level
        light = instantiate_armor('leather', 'leather', level=level)
        assert light.equip_threshold == 1 + extra, level


def test_the_material_no_longer_sets_the_tier():
    """Materials drive wear, weight and the name; the enchantment drives the
    tier. A plain primordial plate is tier 1, an enchanted one its level's."""
    from items import instantiate_armor
    plain = instantiate_armor('plate', 'primordial_stone_armor')
    assert plain.tier == 1 and plain.equip_threshold == 3
    deep = instantiate_armor('plate', 'primordial_stone_armor', level=10)
    assert deep.tier == 5 and deep.equip_threshold == 5


def test_shields_follow_the_same_rule():
    """The tower shield was +2 AC over the light shield for the same two
    tier-1 questions (Brandon's report)."""
    from items import instantiate_shield
    assert instantiate_shield('buckler', 'oak').equip_threshold == 1
    assert instantiate_shield('light_wooden', 'oak').equip_threshold == 1
    assert instantiate_shield('kite_shield', 'oak').equip_threshold == 2
    tower = instantiate_shield('tower_shield', 'oak')
    assert tower.equip_threshold == 3
    assert instantiate_shield('tower_shield', 'oak', level=10).equip_threshold == 5
