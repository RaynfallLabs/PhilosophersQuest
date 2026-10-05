"""Named unique weapons must be worth finding.

Common weapons are composed from a template and a material and their base
damage climbs with depth. The named uniques' hand-set base damage had not
kept up: past floor 20 a legendary did a half to a fifth of the damage of an
ordinary weapon from the same floor (Excalibur 16 against a floor-80 common
median of 72; the Sword of Michael 18 on floor 100). Quest and mini-boss
weapon rewards were worthless. tools/balance/rebase_unique_weapons.py fixed
the data; this keeps it fixed.
"""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import rebase_unique_weapons as rb  # noqa: E402


@pytest.fixture(scope='module')
def weapons():
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope='module', autouse=True)
def _fewer_samples():
    old = rb.SAMPLES
    rb.SAMPLES = 400
    rb._cache.clear()
    yield
    rb.SAMPLES = old
    rb._cache.clear()


@pytest.mark.parametrize('wid', [
    'excalibur', 'mjolnir', 'gungnir', 'anduril', 'durendal', 'caliburn',
    'gram', 'sword_of_michael',                      # quest payoffs
    'echidna_fang', 'vulcans_brand', 'wendigo_fang', 'hunt_captains_sword',  # mini-boss drops
    'oathkeeper_sword', 'penitents_blade', 'meleager_spear',                 # encounter rewards
])
def test_unique_is_at_least_as_good_as_a_common_weapon_of_its_floor(weapons, wid):
    d = weapons[wid]
    floor = rb.floor_of(wid, d, rb.drop_floors())
    assert floor, f'{wid} has no floor'
    median = rb.class_median(floor, d.get('weapon_class', d['class']))
    assert rb.base_of(d) >= 1.05 * median, (wid, floor, rb.base_of(d), median)


def test_quest_swords_beat_ordinary_uniques(weapons):
    assert rb.base_of(weapons['gram']) > rb.base_of(weapons['spear_of_lugh'])      # both floor 60
    assert rb.base_of(weapons['sword_of_michael']) >= rb.base_of(weapons['mjolnir'])


def test_rebase_never_touches_tools_or_broken_things(weapons):
    assert rb.base_of(weapons['broken_gram']) <= 6
    for wid in rb.SKIP:
        assert wid in weapons
