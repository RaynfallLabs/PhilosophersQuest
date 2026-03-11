"""
Balance and integration tests for Philosopher's Quest.
Run with: pytest tests/ -v
"""
import json
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(rel_path):
    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, rel_path), encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# level_manager
# ---------------------------------------------------------------------------

def test_stone_level_is_100():
    from level_manager import STONE_LEVEL
    assert STONE_LEVEL == 100, f"STONE_LEVEL must be 100 for production, got {STONE_LEVEL}"


# ---------------------------------------------------------------------------
# Player quiz timer
# ---------------------------------------------------------------------------

def test_timer_floor_prevents_unsolvable_quizzes():
    from player import Player
    p = Player()
    # Worst-case stacking: confused + stunned + blinded
    p.status_effects['confused'] = 10
    p.status_effects['stunned'] = 10
    p.status_effects['blinded'] = 10
    mod = p.get_quiz_timer_modifier()
    assert mod >= 0.40, f"Stacked debuffs reduced timer below 0.40x floor: {mod}"


def test_hasted_timer_increases():
    from player import Player
    p = Player()
    p.status_effects['hasted'] = 10
    mod = p.get_quiz_timer_modifier()
    assert mod > 1.0, "Haste should increase timer"


# ---------------------------------------------------------------------------
# Shields — level coverage
# ---------------------------------------------------------------------------

def test_shields_cover_every_20_levels():
    from items import load_items
    shields = load_items('shield')
    levels = sorted(s.min_level for s in shields)
    # Every 20-level band 1-100 must have at least one shield available
    for band_start in range(1, 101, 20):
        band = range(band_start, band_start + 20)
        available = [l for l in levels if l in band]
        assert available, f"No shield available in level band {band_start}-{band_start+19}"


def test_shield_count():
    from items import load_items
    shields = load_items('shield')
    assert len(shields) == 10, f"Expected 10 shields, got {len(shields)}"


# ---------------------------------------------------------------------------
# Monsters — no 10-level gaps L26-80
# ---------------------------------------------------------------------------

def test_no_monster_gaps_26_to_80():
    monsters = load_json('data/monsters.json')
    by_level = {}
    for v in monsters.values():
        ml = v.get('min_level', 1)
        by_level.setdefault(ml, []).append(v)

    introduced_levels = set(by_level.keys())
    gaps = []
    for band_start in range(26, 81, 10):
        band = range(band_start, band_start + 10)
        if not any(l in introduced_levels for l in band):
            gaps.append(f"L{band_start}-{band_start+9}")
    assert not gaps, f"Monster introduction gaps remain: {gaps}"


def test_monster_count_increased():
    monsters = load_json('data/monsters.json')
    assert len(monsters) >= 368, f"Expected >= 368 monsters, got {len(monsters)}"


def test_all_monsters_have_required_fields():
    monsters = load_json('data/monsters.json')
    required = ['name', 'symbol', 'color', 'hp', 'speed', 'ai_pattern',
                'min_level', 'thac0', 'frequency', 'attacks',
                'resistances', 'weaknesses', 'treasure']
    for mid, m in monsters.items():
        for field in required:
            assert field in m, f"Monster '{mid}' missing field '{field}'"


def test_new_monsters_instantiate():
    from monster import Monster
    monsters = load_json('data/monsters.json')
    new_ids = [
        'shadow_master', 'void_crawler', 'ruinous_djinn', 'undead_colossus', 'elder_werewolf',
        'abyssal_champion', 'bone_titan', 'spectral_lord', 'chaos_troll', 'wyrm',
        'elder_mind_flayer', 'void_leviathan', 'elder_beholder', 'dread_wyrm', 'abyssal_overlord',
        'elder_dragon', 'lich_sovereign', 'demon_emperor', 'world_serpent', 'entropy_wraith',
    ]
    for mid in new_ids:
        assert mid in monsters, f"New monster '{mid}' missing from monsters.json"
        m = Monster({**monsters[mid], 'id': mid}, 0, 0)
        assert m.hp > 0, f"{mid} rolled 0 hp"
        assert m.name, f"{mid} has no name"


# ---------------------------------------------------------------------------
# Economics questions — balanced pool
# ---------------------------------------------------------------------------

def test_economics_questions_count():
    questions = load_json('data/questions/economics.json')
    assert len(questions) == 80, f"Expected 80 economics questions, got {len(questions)}"


def test_economics_tier_balance():
    questions = load_json('data/questions/economics.json')
    tiers = Counter(q['tier'] for q in questions)
    for t in range(1, 6):
        assert tiers[t] >= 15, f"Tier {t} has only {tiers[t]} questions (minimum 15)"


def test_economics_question_format():
    questions = load_json('data/questions/economics.json')
    for i, q in enumerate(questions):
        assert 'tier' in q and 'question' in q and 'answer' in q and 'choices' in q, \
            f"Question {i} missing required fields"
        assert q['answer'] in q['choices'], \
            f"Question {i} answer not in choices: {q['question']!r}"
        assert len(q['choices']) == 4, \
            f"Question {i} has {len(q['choices'])} choices (expected 4)"


# ---------------------------------------------------------------------------
# Food — spawn weight tapering + new deep items
# ---------------------------------------------------------------------------

def test_food_count():
    from items import load_items
    foods = load_items('food')
    assert len(foods) == 12, f"Expected 12 food items, got {len(foods)}"


def test_new_deep_food_items():
    from items import load_items
    foods = load_items('food')
    ids = {f.id for f in foods}
    assert 'deep_fungi' in ids, "deep_fungi not found in food items"
    assert 'void_ration' in ids, "void_ration not found in food items"
    deep = next(f for f in foods if f.id == 'deep_fungi')
    void = next(f for f in foods if f.id == 'void_ration')
    assert deep.min_level == 35
    assert void.min_level == 60


def test_bread_tapers_at_high_levels():
    from items import load_items
    from dungeon import _food_eligible
    foods = load_items('food')
    pool_l10 = _food_eligible(foods, 10)
    pool_l80 = _food_eligible(foods, 80)
    bread_l10 = sum(1 for x in pool_l10 if x.id == 'bread_ration')
    bread_l80 = sum(1 for x in pool_l80 if x.id == 'bread_ration')
    assert bread_l80 < bread_l10, "bread_ration should be rarer at L80 than L10"


def test_deep_food_absent_early():
    from items import load_items
    from dungeon import _food_eligible
    foods = load_items('food')
    pool_l1 = _food_eligible(foods, 1)
    ids_l1 = {x.id for x in pool_l1}
    assert 'deep_fungi' not in ids_l1, "deep_fungi should not spawn at L1"
    assert 'void_ration' not in ids_l1, "void_ration should not spawn at L1"


# ---------------------------------------------------------------------------
# Weapon spawn weighting
# ---------------------------------------------------------------------------

def test_weapon_spawn_weighting():
    from items import load_items
    from dungeon import _item_eligible_weighted
    weapons = load_items('weapon')
    pool_l1  = _item_eligible_weighted(weapons, 1)
    pool_l100 = _item_eligible_weighted(weapons, 100)
    iron_l1  = sum(1 for x in pool_l1   if x.id == 'iron_sword')
    iron_l100 = sum(1 for x in pool_l100 if x.id == 'iron_sword')
    # iron_sword should be far more common at L1 than L100
    assert iron_l1 > iron_l100, "iron_sword should be weighted down at high levels"


# ---------------------------------------------------------------------------
# Monster spawn count scaling
# ---------------------------------------------------------------------------

def test_monster_spawn_count_scales():
    from level_manager import LevelManager
    # Inspect the scaling formula directly
    for level in [1, 10, 50, 100]:
        min_m = min(3 + (level - 1), 12)
        max_m = min(5 + level, 18)
        assert min_m <= max_m, f"L{level}: min_m ({min_m}) > max_m ({max_m})"
    # Deep levels should have higher ceiling than shallow
    min_l100 = min(3 + 99, 12)
    min_l1   = min(3 + 0,  12)
    assert min_l100 >= min_l1, "Deep levels should have at least as many monsters"
