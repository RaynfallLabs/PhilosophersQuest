"""Spells learnable from spellbooks (spell_id -> attributes).

PROPOSED REBALANCE — Generator F, against tools/balance/curve.py.

Power dice derive from curve.weapon_base_damage(floor) * ratio so that
chain-5 spell damage rivals chain-5 weapon damage at the spell's tier band.
MP cost derives from MP_BY_TIER[tier] +/- effect adjustments.
quiz_tier follows math_tier_dominant(spell_floor_anchor).
"""

LEARNABLE_SPELLS: dict[str, dict] = {
    'magic_missile_spell': {
        'name': 'Magic Missile', 'effect': 'magic_missile', 'power': '1d4',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Unerring force dart, 1d4 damage.',
    },
    'sleep_spell': {
        'name': 'Sleep', 'effect': 'sleep_monster', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Puts one monster to sleep for 6 turns.',
    },
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Reveal nearby tiles in a 15-radius area.',
    },
    'shield_spell': {
        'name': 'Magic Shield', 'effect': 'shield_self', 'power': '',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': False,
        'desc': '+2 AC, physical damage halved for 12 turns.',
    },
    'fire_bolt_spell': {
        'name': 'Fire Bolt', 'effect': 'fire_bolt', 'power': '2d4',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': True,
        'desc': 'Fire bolt, 2d4 damage.',
    },
    'haste_spell': {
        'name': 'Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Move twice per turn for 10 turns.',
    },
    'heal_spell': {
        'name': 'Heal', 'effect': 'extra_heal', 'power': '3d4',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Restore 3d4 HP (scales with chain score).',
    },
    'invisibility_spell': {
        'name': 'Invisibility', 'effect': 'invisibility_self', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Become invisible for 15 turns.',
    },
    'lightning_spell': {
        'name': 'Chain Lightning', 'effect': 'lightning_bolt', 'power': '5d4',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Lightning bolt, 5d4 arcing damage.',
    },
    'confusion_spell': {
        'name': 'Confusion', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Confuse a monster for 10 turns.',
    },
    'displacement_spell': {
        'name': 'Displacement', 'effect': 'displacement_self', 'power': '',
        'mp_cost': 13, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Attackers miss you 30% of time for 20 turns.',
    },
    'ice_storm_spell': {
        'name': 'Ice Storm', 'effect': 'mass_ice', 'power': '5d6',
        'mp_cost': 16, 'quiz_tier': 4, 'needs_target': False,
        'desc': '5d6 cold damage to all visible monsters.',
    },
    'paralyze_spell': {
        'name': 'Paralysis', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 13, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Paralyze a monster for 8 turns.',
    },
    'army_of_darkness_spell': {
        'name': 'Army of Darkness', 'effect': 'summon_undead_horde', 'power': '',
        'mp_cost': 7, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Summon a horde of undead minions to fight for you. Give me some sugar, baby.',
    },
    'cleanse_spell': {
        'name': 'Cleanse', 'effect': 'cleanse_self', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Remove one negative status effect.',
    },
    'empower_spell': {
        'name': 'Empower', 'effect': 'empower_next', 'power': '',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Next melee attack deals 3x damage.',
    },
    'smite_spell': {
        'name': 'Smite', 'effect': 'smite', 'power': '4d6',
        'mp_cost': 13, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Massive holy damage, 4d6 (scales with chain + INT).',
    },
    'summon_guardian_spell': {
        'name': 'Summon Guardian', 'effect': 'summon_guardian', 'power': '',
        'mp_cost': 13, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Summon a guardian pet for 20 turns.',
    },
    'meteor_spell': {
        'name': 'Meteor', 'effect': 'meteor', 'power': '6d6',
        'mp_cost': 16, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Massive fire AoE, 6d6 to all visible monsters.',
    },
    'time_freeze_spell': {
        'name': 'Time Freeze', 'effect': 'time_freeze', 'power': '',
        'mp_cost': 20, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Freeze all monsters for 5 turns. The ultimate emergency.',
    },
    'fireball_spell': {
        'name': 'Fireball', 'effect': 'mass_fire', 'power': '2d4',
        'mp_cost': 10, 'quiz_tier': 2, 'needs_target': False,
        'desc': '2d4 fire damage to all visible monsters.',
    },
    'slow_spell': {
        'name': 'Slow Monster', 'effect': 'slow_monster_spell', 'power': '',
        'mp_cost': 5, 'quiz_tier': 2, 'needs_target': True,
        'desc': 'Target skips every other turn for 4-10 turns.',
    },
    'knock_spell': {
        'name': 'Knock', 'effect': 'knock_spell', 'power': '',
        'mp_cost': 5, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Magically open the nearest locked container.',
    },
    'teleport_away_spell': {
        'name': 'Teleport Away', 'effect': 'teleport_away_spell', 'power': '',
        'mp_cost': 5, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Teleport nearest monster away, or yourself if none visible.',
    },
    'acid_arrow_spell': {
        'name': 'Acid Arrow', 'effect': 'acid_arrow', 'power': '2d8',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': '2d8 acid + poison DoT. Chain extends duration.',
    },
    'drain_life_spell': {
        'name': 'Drain Life', 'effect': 'drain_life_spell', 'power': '2d8',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Steal life — damage target, heal yourself for the same.',
    },
    'fear_spell': {
        'name': 'Fear', 'effect': 'fear_monster_spell', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Target flees in terror for chain-scaled turns.',
    },
    'detect_spell': {
        'name': 'Detect Monsters', 'effect': 'detect_monsters_spell', 'power': '',
        'mp_cost': 8, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Reveal all monsters on the level for chain-scaled turns.',
    },
    'polymorph_spell': {
        'name': 'Polymorph', 'effect': 'polymorph_spell', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Transform a monster into a random creature. Risky!',
    },
    'reflect_spell': {
        'name': 'Reflect', 'effect': 'reflect_self', 'power': '',
        'mp_cost': 13, 'quiz_tier': 4, 'needs_target': False,
        'desc': '50% chance to reflect status attacks for chain-scaled turns.',
    },
    'disintegrate_spell': {
        'name': 'Disintegrate', 'effect': 'disintegrate_spell', 'power': '9d8',
        'mp_cost': 20, 'quiz_tier': 5, 'needs_target': True,
        'desc': 'Chain-scaling instant kill (30-90%). Bosses take 9d8 instead.',
    },
    'sign_aard': {
        'name': 'Aard', 'effect': 'aard_blast', 'power': '1d4',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Telekinetic blast — damages and stuns a target.',
    },
    'sign_igni': {
        'name': 'Igni', 'effect': 'fire_bolt', 'power': '1d4',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Directed blast of fire. Burns on contact.',
    },
    'sign_quen': {
        'name': 'Quen', 'effect': 'shield_self', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Protective shield absorbs damage for 12 turns.',
    },
    'sign_yrden': {
        'name': 'Yrden', 'effect': 'slow_monster', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Magic trap — slows a target for 8 turns.',
    },
    'sign_axii': {
        'name': 'Axii', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Charms the mind — confuses a target for 10 turns.',
    },
    'elder_blink': {
        'name': 'Blink', 'effect': 'teleport_self', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Teleport to a random safe location. The Elder Blood bends space.',
    },
    'elder_charge': {
        'name': 'Charge', 'effect': 'empower_next', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Channel Elder Blood — next melee attack deals 3x damage.',
    },
    'elder_scream': {
        'name': 'Scream', 'effect': 'mass_ice', 'power': '2d4',
        'mp_cost': 10, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Unleash the Elder Blood — cold damage to all visible enemies.',
    },
}