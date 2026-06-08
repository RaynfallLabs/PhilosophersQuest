"""Fill the missing top-tier outcomes on the 13 common recipes (2026-06-07).

Bug: the 12 family recipes + basic_monster_stew were authored only up to tier 4
(basic only to tier 3). _apply_tier_outcome resolved a missing tier via
`outcomes.get(str(tier), outcomes.get('0', {}))`, so a PERFECT T5 cook silently
fell back to the '0' RUINED outcome (sp 0 / hp 0) -- the success message printed
but the player gained nothing. The prime/trophy recipes (607 of them) already
define tiers 0-5, so only these 13 were affected.

Fix (data half; the code half adds graceful nearest-lower degrade as a net):
  * family T5 = that recipe's own T4 + one more permanent max-HP (the capstone
    escalation), keeping the family's stat grant. No temp_power -- families are
    the numeric tier; temp_power is the prime tier's premium.
  * basic_monster_stew gets a T4 (max-HP fortify) and a T5 (a perfect-cook stat
    point), staying the humblest recipe.

Round-trip guarded: the unmodified parse must re-serialize byte-for-byte before
any write, so formatting (indent=2, ensure_ascii=True) is preserved.
"""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'items' / 'recipes.json'

FAMILIES = [
    'family_beast_recipe', 'family_demon_recipe', 'family_undead_recipe',
    'family_fey_recipe', 'family_construct_recipe', 'family_elemental_recipe',
    'family_plant_recipe', 'family_aberration_recipe', 'family_humanoid_recipe',
    'family_reptile_recipe', 'family_celestial_recipe', 'family_dragon_recipe',
]

# Capstone flavor per family (desc is metadata only; not shown in-game).
FAMILY_T5_DESC = {
    'family_beast_recipe':     'A flawless beast-roast; primal vigor floods your limbs.',
    'family_demon_recipe':     'A perfected infernal course; the demon-fire tempers you.',
    'family_undead_recipe':    'A perfect bone-broth; deep marrow steels you against death.',
    'family_fey_recipe':       'A flawless fey delicacy; enchantment quickens your senses.',
    'family_construct_recipe': 'A masterwork construct-dish; stone and gear brace your frame.',
    'family_elemental_recipe': 'A perfected elemental dish; raw force settles into your bones.',
    'family_plant_recipe':     'A flawless verdant course; deep roots feed your vitality.',
    'family_aberration_recipe':'A perfected aberrant dish; alien sinew fortifies you.',
    'family_humanoid_recipe':  'A masterful humanoid feast; hard-won cunning sharpens you.',
    'family_reptile_recipe':   'A flawless reptile course; cold-blooded endurance hardens you.',
    'family_celestial_recipe': 'A perfected celestial dish; radiant grace lifts your frame.',
    'family_dragon_recipe':    'A perfect draconic feast; the wyrm\'s might becomes your own.',
}


def main():
    orig = PATH.read_text(encoding='utf-8')
    R = json.loads(orig)
    # round-trip guard -- confirm we can rewrite byte-for-byte before touching it.
    # Preserve whatever trailing-newline the file has (json.dumps adds none).
    trailing = orig[len(orig.rstrip('\n')):]
    assert json.dumps(R, indent=2, ensure_ascii=True) == orig.rstrip('\n'), \
        'round-trip mismatch -- aborting (formatting would change)'

    changed = []

    for fid in FAMILIES:
        to = R[fid]['tier_outcomes']
        assert '4' in to, (fid, 'no T4 to derive from')
        assert '5' not in to, (fid, 'already has T5 -- aborting to avoid clobber')
        t4 = to['4']
        to['5'] = {
            'sp': int(t4.get('sp', 65)),
            'hp': max(int(t4.get('hp', 4)), 5),
            'max_hp_bonus': int(t4.get('max_hp_bonus', 2)) + 1,   # capstone: +1 over T4
            'stat_grant': int(t4.get('stat_grant', 1)) or 1,
            'desc': FAMILY_T5_DESC[fid],
        }
        changed.append(fid)

    # basic_monster_stew: humblest recipe, missing BOTH T4 and T5
    bto = R['basic_monster_stew']['tier_outcomes']
    assert '3' in bto and '4' not in bto and '5' not in bto, 'basic stew unexpected shape'
    bto['4'] = {
        'sp': 65, 'hp': 4, 'max_hp_bonus': 2,
        'desc': 'A hearty stew; the long simmer fortifies you.',
    }
    bto['5'] = {
        'sp': 65, 'hp': 5, 'max_hp_bonus': 2, 'stat_grant': 1,
        'desc': 'A flawless stew; even plain fare, cooked perfectly, hardens you.',
    }
    changed.append('basic_monster_stew')

    PATH.write_text(json.dumps(R, indent=2, ensure_ascii=True) + trailing, encoding='utf-8')
    print(f'patched {len(changed)} recipes with top-tier outcomes:')
    for c in changed:
        print('  +', c, '->', sorted(R[c]['tier_outcomes'].keys()))


if __name__ == '__main__':
    main()
