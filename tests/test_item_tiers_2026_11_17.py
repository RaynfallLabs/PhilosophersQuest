"""Every item system across the five tiers (Brandon, 2026-11-16: "Every single
one should have a good distribution across all tiers"), and light and medium
body armour on the deep floors (his defence-model decision 20).

The census (tools/balance/tier_census.py) is the measure and
tests/test_tier_distribution.py the gate. These are the data and logic tests
for what the 2026-11-17 pass changed: where an item is found is read from the
game's own spawn rule, the potions, flasks, ammo, food, rings, amulets, chests
and artifacts placed by lore, and the deep light and medium body armour.
Whether a deep Dexterity run FEELS right is Brandon's play-test (the
simulator's numbers are in ITEM_TIERS_REPORT_2026_11_17.md).
"""
import collections
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pytest  # noqa: E402

import dungeon  # noqa: E402
import gear  # noqa: E402
import items  # noqa: E402
import tier_census as tc  # noqa: E402


def _data(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


def _tier(fname, iid):
    row = dict(_data('data', 'items', fname)[iid], _key=iid)
    return tc.band(tc.found_floor(row, food=(fname == 'food.json')))


# ------------------------------------------------------------ the measure

def test_the_census_reads_the_floor_pool_s_own_weights():
    """Where a thing is found is the floor pool's own rule (a unique's peak
    bell before its band weights): the census once read the bands and put
    fifteen rings on floors 81-100 that the game never spawned past 80."""
    for it in items.load_items('accessory') + items.load_items('weapon'):
        if not items.is_random_loot(it):
            continue
        tot = s = 0.0
        for f in range(1, 101):
            w = dungeon.floor_spawn_weight(it, f)
            tot += w
            s += w * f
        row = dict(_data('data', 'items', f"{it.item_class}.json")[it.id], _key=it.id)
        if tot:
            assert tc.found_floor(row) == pytest.approx(s / tot), it.id


def test_the_floor_pool_still_drops_a_unique_outside_its_bell():
    ring = next(i for i in items.load_items('accessory') if i.id == 'ring_of_the_nibelung')
    assert dungeon.floor_spawn_weight(ring, 50) == 0          # below its first floor
    assert dungeon.floor_spawn_weight(ring, 88) > 0
    assert dungeon._item_eligible_weighted([ring], 50, random.Random(1)) == []
    assert dungeon._item_eligible_weighted([ring], 88, random.Random(1)) != []


def test_containers_are_the_chest_kinds_a_floor_rolls():
    rows = {r['category']: r for r in tc.census()['rows']}
    assert sum(rows['Containers']['counts']) == len(
        [k for k, v in _data('data', 'chest_templates.json').items() if isinstance(v, dict)])


@pytest.mark.parametrize('iid, floor', [
    ('bronze_bull', 12), ('eye_of_graeae', 29), ('cats_footstep', 62), ('bear_sinew', 77)])
def test_a_story_artifact_is_on_its_story_floor(iid, floor):
    """story_floor is where dungeon.spawn_items really puts the piece."""
    assert _data('data', 'items', 'artifact.json')[iid]['story_floor'] == floor
    rng = random.Random(floor)
    random.seed(floor)
    d = dungeon.generate_dungeon(level=floor, rng=rng)
    got = {getattr(i, 'id', '') for i in dungeon.spawn_items(d.rooms, floor, d)}
    assert iid in got


def test_an_encounter_s_gift_is_found_on_the_encounter_s_floors():
    given = tc._given_by_encounters()
    assert tc.band(given['robin_hoods_horn']) == 1          # the bridge, floors 12-18
    assert tc.band(given['olifant']) == 5                   # Roncevaux, floors 86-92
    assert 'brennans_sword' in given                        # Ser Brennan hands it over
    # an encounter that only asks for a thing does not give it
    assert given.get('lions_thorn') == pytest.approx(13.0)  # the limping lion, not the great one


# ------------------------------------------------------------ the rows

def test_potions_from_plain_remedies_to_rare_draughts():
    for pid in ('potion_of_healing', 'potion_of_stamina', 'potion_of_cure_poison',
                'potion_of_cure_disease'):
        assert _tier('potion.json', pid) == 1, pid
    for pid in ('potion_of_full_healing', 'potion_of_gain_level', 'elixir_of_gilgamesh',
                'soma', 'potion_of_cure_all'):
        assert _tier('potion.json', pid) == 5, pid


def test_every_floor_keeps_a_healing_potion_at_home():
    """The healing ladder: the plain potion near the top, extra healing through
    the middle, full healing deep. No band is left without one."""
    pots = _data('data', 'items', 'potion.json')
    for f in range(1, 101):
        tot = heal = 0.0
        for pid, p in pots.items():
            if f < int(p.get('min_level', 1)):
                continue
            w = tc._band_at(p.get('floorSpawnWeight') or {}, f)
            tot += w
            if p.get('effect') in ('heal', 'extra_heal', 'full_heal'):
                heal += w
        assert heal / tot >= 0.15, f


def test_ammo_is_at_home_with_its_material_s_tier():
    for iid in ('iron_arrow', 'steel_arrow', 'hardened_gold_arrow', 'diamond_arrow', 'dragonbone_arrow',
                'iron_bolt', 'steel_bolt', 'hardened_gold_bolt', 'diamond_bolt', 'adamantine_bolt'):
        own = _data('data', 'items', 'ammo.json')[iid]['tier']
        assert _tier('ammo.json', iid) == own, iid
    assert _tier('ammo.json', 'arrows_of_artemis') == 5
    assert _tier('ammo.json', 'bolts_of_zeus') == 5


def test_each_chest_kind_is_found_within_a_tier_of_its_own():
    for tid, t in _data('data', 'chest_templates.json').items():
        if isinstance(t, dict):
            assert abs(tc.band(tc.chest_floor(t)) - int(t['tier'])) <= 1, tid


def test_a_deep_floor_rolls_a_soul_sphere_as_often_as_before():
    import pet_system
    for f in (70, 90):
        assert sum(c for _s, c in pet_system.sphere_chances(f)) == pytest.approx(0.055)
    assert tc.band(tc.found_floor(dict(_data('data', 'items', 'artifact.json')['greater_soul_sphere']))) == 3


def test_the_rings_and_amulets_placed_by_lore():
    for rid in ('ring_of_thunder', 'ring_of_the_deep', 'amulet_of_insight'):
        assert _tier('accessory.json', rid) == 1, rid
        assert _data('data', 'items', 'accessory.json')[rid]['quiz_tier'] == 2, rid
    for rid in ('ring_of_the_nibelung', 'seal_of_solomon', 'ring_of_solomons_authority',
                'ring_of_lancelot', 'anklet_of_atalanta', 'philosophers_ring_legendary',
                'pectoral_of_amun', 'tyet_of_isis', 'necklace_of_harmonia'):
        assert _tier('accessory.json', rid) == 5, rid


def test_two_labyrinth_weapons_on_the_first_floors():
    for wid in ('theseus_club', 'sword_of_damocles'):
        assert _tier('weapon.json', wid) == 1, wid
        assert _data('data', 'items', 'weapon.json')[wid]['tier'] == 2   # its own maths tier


def test_food_from_a_surface_lunch_to_the_food_of_the_gods():
    for fid in ('apple', 'bread_ration', 'hard_cheese'):
        assert _tier('food.json', fid) == 1, fid
    for fid in ('ambrosia', 'peach_of_immortality', 'void_ration'):
        assert _tier('food.json', fid) == 5, fid


def test_hydras_blood_is_the_deep_venom_and_wired():
    import coatings
    import economy
    import renderer
    it = items.make_item_by_id('flask', 'hydras_blood')
    assert isinstance(it, items.Flask) and coatings.is_tool(it)
    spec = coatings.coat_spec(it)
    viper = coatings.coat_spec(items.make_item_by_id('flask', 'viper_venom'))
    assert spec['substance'] == 'poison' and spec['blows'] > viper['blows']
    assert spec['rider']['turns'] > viper['rider']['turns']
    assert _tier('flask.json', 'hydras_blood') == 4
    assert economy.merchant_price(it, 70) > 0
    p = renderer._resolve_item_sprite_path('hydras_blood')
    assert p and os.path.basename(p) == 'hydras_blood.png'
    poison = _data('data', 'traders.json')['counters']['weak']['poison']
    assert 'hydras_blood' in poison['offers'][0]['ids']
    import domain_counters  # noqa: F401  (the stall reads the same ids)


# ------------------------------------------- deep light and medium armour

def _body_classes(floors, n=150, seed=7):
    rng = random.Random(seed)
    c = collections.Counter()
    names = collections.Counter()
    for f in floors:
        for _ in range(n):
            a = items.pick_random_armor_for_floor(f, rng, slot='body')
            if a is not None:
                c[a.weight_class] += 1
                names[(a.weight_class, a.material)] += 1
    return c, names


def test_light_and_medium_body_armour_reach_the_deep_floors():
    """Decision 20: past floor 40 almost nothing but heavy armour spawned
    (100% from floor 60). Deep light and medium come back in deep materials."""
    for lo, hi, light_min, medium_min in ((61, 80, 0.15, 0.15), (81, 100, 0.20, 0.15)):
        c, names = _body_classes(range(lo, hi + 1, 2))
        n = sum(c.values())
        assert c['light'] / n >= light_min, (lo, c)
        assert c['medium'] / n >= medium_min, (lo, c)
        assert c['heavy'] / n >= 0.35, (lo, c)          # plate is still the commonest find
        # deep light armour is a deep material, never plain floor-1 leather
        for (cls, mat), k in names.items():
            if cls == 'light':
                assert mat in ('drakeskin_armor', 'dragonhide_armor', 'dragonscale', 'spider_silk',
                               'elven_silk', 'petrified_dragon', 'boiled_leather_armor', 'silk'), mat


def test_the_early_floors_are_as_they_were():
    c, _ = _body_classes(range(1, 21), n=100)
    n = sum(c.values())
    assert c['light'] / n > 0.6 and c['heavy'] / n < 0.05


def test_a_deep_light_piece_keeps_light_armour_s_lower_ac():
    """The trade: dodge and speed for AC."""
    deep_light = items.instantiate_armor('studded_leather', 'dragonhide_armor', level=9)
    deep_plate = items.instantiate_armor('full_plate', 'glassteel', level=9)
    assert deep_light.weight_class == 'light' and deep_plate.weight_class == 'heavy'
    assert deep_light.ac_bonus + deep_light.enchant_bonus < deep_plate.ac_bonus + deep_plate.enchant_bonus
    assert deep_light.ac_bonus == items.get_template('armor', 'studded_leather')['base_ac_value']


def test_only_light_and_medium_body_templates_return_deep():
    for tid, t in items.load_templates('armor').items():
        if t.get('deep_bell'):
            assert t.get('slot', 'body') == 'body', tid
            assert gear.weight_class(t) in ('light', 'medium'), tid
            assert gear.template_weight(t, 85) > 0, tid
