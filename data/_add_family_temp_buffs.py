"""Give each family recipe's T5 a themed temp buff (2026-06-07).

Before this, family T5 was nearly identical to T4 (just +1 heal / +1 max HP;
the stat grant was the same +1 and capped per floor anyway), so a "perfect"
family cook felt unrewarding. Each family now also lands a SHORT themed status
buff at T5 only -- 60 turns, vs the prime recipes' 150 -- so the hierarchy holds
(basic < family < prime < trophy) while T5 finally feels like a payoff.

Only self-contained status effects are used: resists, regen, haste, shielded,
crit. (heroism/brilliance are deliberately avoided -- their stat bonus is applied
by the potion CALLER, not by add_effect, so they'd be dead buffs here.)

Round-trip guarded; preserves indent=2 / ensure_ascii=True formatting.
"""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'items' / 'recipes.json'
DURATION = 60

# family recipe id -> (canonical temp effect, flavor desc shown in the buff line)
BUFFS = {
    'family_beast_recipe':      ('crit_buff',     'predatory ferocity -- critical strikes land more often'),
    'family_demon_recipe':      ('fire_resist',   'infernal blood -- fire rolls off you'),
    'family_undead_recipe':     ('drain_resist',  'deathless marrow -- you resist stat drain'),
    'family_fey_recipe':        ('hasted',        'fey quickness -- you move with uncanny speed'),
    'family_construct_recipe':  ('shielded',      'construct-plating -- you are harder to hit'),
    'family_elemental_recipe':  ('shock_resist',  'elemental essence -- lightning disperses around you'),
    'family_plant_recipe':      ('regenerating',  'verdant vigor -- your wounds slowly close'),
    'family_aberration_recipe': ('magic_resist',  'alien ward -- hostile magic falters'),
    'family_humanoid_recipe':   ('crit_buff',     'honed battle-tactics -- critical strikes land more often'),
    'family_reptile_recipe':    ('poison_resist', 'venom-tolerant blood -- poison weakens against you'),
    'family_celestial_recipe':  ('magic_resist',  'radiant warding -- hostile magic falters'),
    'family_dragon_recipe':     ('fire_resist',   'draconic blood -- flame cannot harm you'),
}


def main():
    orig = PATH.read_text(encoding='utf-8')
    R = json.loads(orig)
    trailing = orig[len(orig.rstrip('\n')):]
    assert json.dumps(R, indent=2, ensure_ascii=True) == orig.rstrip('\n'), \
        'round-trip mismatch -- aborting'

    for rid, (power, desc) in BUFFS.items():
        r = R[rid]
        t5 = r['tier_outcomes']['5']
        r['temp_power'] = power
        r['temp_desc'] = desc
        r['temp_duration'] = DURATION
        t5['temp_power'] = True
        # keep the T5 desc, but make clear it carries a buff now
        t5['desc'] = t5.get('desc', '') + f" A short {desc.split(' -- ')[0]} lingers."

    PATH.write_text(json.dumps(R, indent=2, ensure_ascii=True) + trailing, encoding='utf-8')
    print(f'added themed {DURATION}-turn T5 buffs to {len(BUFFS)} family recipes:')
    for rid, (power, _) in BUFFS.items():
        print(f'  {rid:28} -> {power}')


if __name__ == '__main__':
    main()
