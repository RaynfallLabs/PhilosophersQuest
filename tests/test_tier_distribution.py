"""Every content system spread across all five tiers (Brandon, 2026-11-16:
"Every single one should have a good distribution across all tiers... every
time I ask, you come back and say things like 'recipes are clustered at
tier one'").

The census is tools/balance/tier_census.py: one tier per 20 floors, read from
where each thing is FOUND. The target: a category of ten or more holds at
least 10% of its kinds in every tier and no more than 35% in any one; a
smaller one (or a sub-group: a monster family, the stat dishes of one stat)
has at least one in every tier.

KNOWN_GAPS is the ratchet. It is what failed on 2026-11-16, the work still to
do (ENHANCEMENT_AND_BALANCE_PLAN_2026_11_16.md). A category that falls out of
the target and is not on it fails here (a new gap). One that has been fixed
fails here too until it is taken off the list, so the list only shrinks.
KNOWN_MISMATCH does the same for items whose own quiz tier is two or more
tiers from where they are found.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pytest  # noqa: E402

import tier_census  # noqa: E402

KNOWN_GAPS = {
    'Monsters (ordinary kinds)': 'lopsided',
    'Bosses': 'lopsided',
    'Monster family: aberrations': 'gap',
    'Monster family: birds': 'gap',
    'Monster family: celestials': 'gap',
    'Monster family: constructs': 'gap',
    'Monster family: demons': 'lopsided',
    'Monster family: elementals': 'lopsided',
    'Monster family: fair_folk': 'gap',
    'Monster family: ghosts': 'gap',
    'Monster family: giants': 'lopsided',
    'Monster family: goblinkin': 'gap',
    'Monster family: gorgons': 'gap',
    'Monster family: great_beasts': 'gap',
    'Monster family: legend': 'lopsided',
    'Monster family: mortals': 'lopsided',
    'Monster family: oozes': 'gap',
    'Monster family: plants': 'gap',
    'Monster family: restless_dead': 'lopsided',
    'Monster family: serpents': 'gap',
    'Monster family: shapeshifters': 'gap',
    'Monster family: vampires_liches': 'lopsided',
    'Monster family: vermin': 'gap',
    'Weapons (uniques)': 'lopsided',
    'Armour (uniques)': 'lopsided',
    'Rings': 'lopsided',
    'Amulets': 'lopsided',
    'Belts and other accessories': 'gap',
    'Potions': 'gap',
    'Flasks (coatings, thrown)': 'gap',
    'Ammo': 'gap',
    'Plain food': 'gap',
    'Artifacts': 'gap',
    'Containers': 'gap',
    'Ingredients': 'lopsided',
    'Dishes: HP': 'lopsided',
    'Dishes: SP': 'lopsided',
    'Dishes: MP': 'lopsided',
    'Dishes: Stat': 'lopsided',
    'Dishes: Special': 'lopsided',
    'Dishes: Stat CON': 'lopsided',
    'Dishes: Stat DEX': 'gap',
    'Dishes: Stat INT': 'gap',
    'Dishes: Stat PER': 'gap',
    'Dishes: Stat STR': 'lopsided',
    'Dishes: Stat WIS': 'lopsided',
    'Flavor encounters': 'lopsided',
}

KNOWN_MISMATCH = {
    'Armour (uniques)': 2,
    'Shields (uniques)': 1,
    'Rings': 12,
    'Amulets': 7,
    'Belts and other accessories': 1,
    'Ammo': 1,
}


@pytest.fixture(scope='module')
def rows():
    return {r['category']: r for r in tier_census.census()['rows']}


def test_the_census_sees_every_system(rows):
    for cat in ('Monsters (ordinary kinds)', 'Weapons (uniques)', 'Rings', 'Wands', 'Spells',
                'Spellbooks', 'Potions', 'Ingredients', 'Dishes: Stat', 'NPC encounters'):
        assert cat in rows and sum(rows[cat]['counts']) > 0, cat


def test_no_new_lopsided_or_empty_tier(rows):
    bad = {c: (r['verdict'], r['counts']) for c, r in rows.items()
           if r['verdict'] != 'ok' and c not in KNOWN_GAPS}
    assert not bad, (f"Out of the tier target and not a known gap (fix it; never add it to "
                     f"KNOWN_GAPS without Brandon's yes): {bad}")


def test_a_fixed_gap_comes_off_the_list(rows):
    fixed = [c for c in KNOWN_GAPS if c in rows and rows[c]['verdict'] == 'ok']
    gone = [c for c in KNOWN_GAPS if c not in rows]
    assert not fixed, f"Now spread across the tiers: take these off KNOWN_GAPS: {fixed}"
    assert not gone, f"No longer in the census (renamed?): {gone}"


def test_no_more_items_with_a_quiz_tier_far_from_where_they_are_found(rows):
    worse = {c: r['mismatch'] for c, r in rows.items()
             if r['mismatch'] > KNOWN_MISMATCH.get(c, 0)}
    better = {c: rows[c]['mismatch'] for c in KNOWN_MISMATCH
              if c in rows and rows[c]['mismatch'] < KNOWN_MISMATCH[c]}
    assert not worse, f"More items whose quiz tier is 2+ tiers from where they are found: {worse}"
    assert not better, f"Fewer now: lower KNOWN_MISMATCH to {better}"
