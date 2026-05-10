"""Spells learnable from spellbooks (spell_id -> attributes).

Used by Game (cast / quaff) and RenderMixin (spell menu rendering). Lives
in its own module so game_render.py can import it without re-creating
a main <-> game_render cycle.
"""

LEARNABLE_SPELLS: dict[str, dict] = {
    'magic_missile_spell': {
        'name': 'Magic Missile', 'effect': 'magic_missile', 'power': '2d6',
        'mp_cost': 3,  'quiz_tier': 1, 'needs_target': True,
        'desc': 'Unerring force dart, 2d6 damage.',
    },
    'sleep_spell': {
        'name': 'Sleep', 'effect': 'sleep_monster', 'power': '',
        'mp_cost': 4,  'quiz_tier': 1, 'needs_target': True,
        'desc': 'Puts one monster to sleep for 6 turns.',
    },
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2,  'quiz_tier': 1, 'needs_target': False,
        'desc': 'Reveal nearby tiles in a 15-radius area.',
    },
    'shield_spell': {
        'name': 'Magic Shield', 'effect': 'shield_self', 'power': '',
        'mp_cost': 5,  'quiz_tier': 2, 'needs_target': False,
        'desc': '+2 AC, physical damage halved for 12 turns.',
    },
    'fire_bolt_spell': {
        'name': 'Fire Bolt', 'effect': 'fire_bolt', 'power': '4d6',
        'mp_cost': 6,  'quiz_tier': 2, 'needs_target': True,
        'desc': 'Fire bolt, 4d6 damage.',
    },
    'haste_spell': {
        'name': 'Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 7,  'quiz_tier': 2, 'needs_target': False,
        'desc': 'Move twice per turn for 10 turns.',
    },
    'heal_spell': {
        'name': 'Heal', 'effect': 'extra_heal', 'power': '3d8',
        'mp_cost': 8,  'quiz_tier': 3, 'needs_target': False,
        'desc': 'Restore 3d8 HP (scales with chain score).',
    },
    'invisibility_spell': {
        'name': 'Invisibility', 'effect': 'invisibility_self', 'power': '',
        'mp_cost': 9,  'quiz_tier': 3, 'needs_target': False,
        'desc': 'Become invisible for 15 turns.',
    },
    'lightning_spell': {
        'name': 'Chain Lightning', 'effect': 'lightning_bolt', 'power': '5d6',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Lightning bolt, 5d6 arcing damage.',
    },
    'confusion_spell': {
        'name': 'Confusion', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 7,  'quiz_tier': 3, 'needs_target': True,
        'desc': 'Confuse a monster for 10 turns.',
    },
    'displacement_spell': {
        'name': 'Displacement', 'effect': 'displacement_self', 'power': '',
        'mp_cost': 12, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Attackers miss you 30% of time for 20 turns.',
    },
    'ice_storm_spell': {
        'name': 'Ice Storm', 'effect': 'mass_ice', 'power': '4d8',
        'mp_cost': 14, 'quiz_tier': 4, 'needs_target': False,
        'desc': '4d8 cold damage to all visible monsters.',
    },
    'paralyze_spell': {
        'name': 'Paralysis', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 12, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Paralyze a monster for 8 turns.',
    },
    'army_of_darkness_spell': {
        'name': 'Army of Darkness', 'effect': 'summon_undead_horde', 'power': '',
        'mp_cost': 15, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Summon a horde of undead minions to fight for you. Give me some sugar, baby.',
    },
    'cleanse_spell': {
        'name': 'Cleanse', 'effect': 'cleanse_self', 'power': '',
        'mp_cost': 4,  'quiz_tier': 1, 'needs_target': False,
        'desc': 'Remove one negative status effect.',
    },
    'empower_spell': {
        'name': 'Empower', 'effect': 'empower_next', 'power': '',
        'mp_cost': 8,  'quiz_tier': 2, 'needs_target': False,
        'desc': 'Next melee attack deals 3x damage.',
    },
    'smite_spell': {
        'name': 'Smite', 'effect': 'smite', 'power': '6d8',
        'mp_cost': 12, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Massive holy damage, 6d8 (scales with chain + INT).',
    },
    'summon_guardian_spell': {
        'name': 'Summon Guardian', 'effect': 'summon_guardian', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Summon a guardian pet for 20 turns.',
    },
    'meteor_spell': {
        'name': 'Meteor', 'effect': 'meteor', 'power': '5d8',
        'mp_cost': 16, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Massive fire AoE, 5d8 to all visible monsters.',
    },
    'time_freeze_spell': {
        'name': 'Time Freeze', 'effect': 'time_freeze', 'power': '',
        'mp_cost': 20, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Freeze all monsters for 5 turns. The ultimate emergency.',
    },
    # -- Tier 2 expansions --
    'fireball_spell': {
        'name': 'Fireball', 'effect': 'mass_fire', 'power': '3d6',
        'mp_cost': 7,  'quiz_tier': 2, 'needs_target': False,
        'desc': '3d6 fire damage to all visible monsters.',
    },
    'slow_spell': {
        'name': 'Slow Monster', 'effect': 'slow_monster_spell', 'power': '',
        'mp_cost': 5,  'quiz_tier': 2, 'needs_target': True,
        'desc': 'Target skips every other turn for 4-10 turns.',
    },
    'knock_spell': {
        'name': 'Knock', 'effect': 'knock_spell', 'power': '',
        'mp_cost': 4,  'quiz_tier': 2, 'needs_target': False,
        'desc': 'Magically open the nearest locked container.',
    },
    'teleport_away_spell': {
        'name': 'Teleport Away', 'effect': 'teleport_away_spell', 'power': '',
        'mp_cost': 6,  'quiz_tier': 2, 'needs_target': False,
        'desc': 'Teleport nearest monster away, or yourself if none visible.',
    },
    # -- Tier 3 expansions --
    'acid_arrow_spell': {
        'name': 'Acid Arrow', 'effect': 'acid_arrow', 'power': '3d6',
        'mp_cost': 8,  'quiz_tier': 3, 'needs_target': True,
        'desc': '3d6 acid + poison DoT. Chain extends duration.',
    },
    'drain_life_spell': {
        'name': 'Drain Life', 'effect': 'drain_life_spell', 'power': '4d6',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Steal life — damage target, heal yourself for the same.',
    },
    'fear_spell': {
        'name': 'Fear', 'effect': 'fear_monster_spell', 'power': '',
        'mp_cost': 7,  'quiz_tier': 3, 'needs_target': True,
        'desc': 'Target flees in terror for chain-scaled turns.',
    },
    'detect_spell': {
        'name': 'Detect Monsters', 'effect': 'detect_monsters_spell', 'power': '',
        'mp_cost': 6,  'quiz_tier': 3, 'needs_target': False,
        'desc': 'Reveal all monsters on the level for chain-scaled turns.',
    },
    'polymorph_spell': {
        'name': 'Polymorph', 'effect': 'polymorph_spell', 'power': '',
        'mp_cost': 9,  'quiz_tier': 3, 'needs_target': True,
        'desc': 'Transform a monster into a random creature. Risky!',
    },
    # -- Tier 4 expansion --
    'reflect_spell': {
        'name': 'Reflect', 'effect': 'reflect_self', 'power': '',
        'mp_cost': 11, 'quiz_tier': 4, 'needs_target': False,
        'desc': '50% chance to reflect status attacks for chain-scaled turns.',
    },
    # -- Tier 5 expansion --
    'disintegrate_spell': {
        'name': 'Disintegrate', 'effect': 'disintegrate_spell', 'power': '4d8',
        'mp_cost': 18, 'quiz_tier': 5, 'needs_target': True,
        'desc': 'Chain-scaling instant kill (30-90%). Bosses take 4d8 instead.',
    },
    # -- Witcher Signs (Geralt) --
    'sign_aard': {
        'name': 'Aard', 'effect': 'aard_blast', 'power': '3d6',
        'mp_cost': 3, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Telekinetic blast — damages and stuns a target.',
    },
    'sign_igni': {
        'name': 'Igni', 'effect': 'fire_bolt', 'power': '4d6',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Directed blast of fire. Burns on contact.',
    },
    'sign_quen': {
        'name': 'Quen', 'effect': 'shield_self', 'power': '',
        'mp_cost': 5, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Protective shield absorbs damage for 12 turns.',
    },
    'sign_yrden': {
        'name': 'Yrden', 'effect': 'slow_monster', 'power': '',
        'mp_cost': 3, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Magic trap — slows a target for 8 turns.',
    },
    'sign_axii': {
        'name': 'Axii', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Charms the mind — confuses a target for 10 turns.',
    },
    # -- Elder Blood (Ciri) --
    'elder_blink': {
        'name': 'Blink', 'effect': 'teleport_self', 'power': '',
        'mp_cost': 3, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Teleport to a random safe location. The Elder Blood bends space.',
    },
    'elder_charge': {
        'name': 'Charge', 'effect': 'empower_next', 'power': '',
        'mp_cost': 6, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Channel Elder Blood — next melee attack deals 3x damage.',
    },
    'elder_scream': {
        'name': 'Scream', 'effect': 'mass_ice', 'power': '4d8',
        'mp_cost': 10, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Unleash the Elder Blood — cold damage to all visible enemies.',
    },
}
