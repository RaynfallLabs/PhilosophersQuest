"""Spells learnable from spellbooks (spell_id -> attributes).

v2.12.0 REBUILD — matches the scroll (v2.10.0) + wand (v2.11.0) pattern:

  * Each entry is a distinct TIER VARIANT of a spell FAMILY. The player can
    learn multiple tiers of the same family and they all coexist in the
    spellbook menu (Cure Light + Cure Wounds + Heal + Greater Heal +
    Resurrection all live side-by-side).
  * `tier` (1..5) is the authoritative difficulty/depth field. Drives the
    science-quiz difficulty on cast + the spawn-depth ladder for the book.
  * `quiz_tier` kept in sync with `tier` for any legacy caller.
  * `mp_cost` is FIXED per tier (T1 2-5, T2 5-8, T3 8-12, T4 12-18, T5 18-25).
  * `power` is a dice string when the effect is damage/heal (fixed magnitude
    at THIS tier -- no chain multiplier); empty for pure-status spells.
  * `spell_family` is a stable key shared across all tier variants of the
    same lineage ("fire", "cold", "healing", ...). Utility singles use
    their own family key ("wish", "knock", ...).
  * `needs_target` unchanged.
  * `desc` describes the FIXED effect at this tier -- no "chain-scaled" or
    "(chain X)" language.

Cast flow: ONE science threshold=1 quiz at spell.tier. MP consumed on both
success and fail (fizzle). Success fires the effect at the fixed magnitude.

Witcher signs (sign_*) and Elder Blood spells (elder_*) are character-build
signature spells (welcome_screen builds only, NOT in the general drop pool).
They keep their old shape for save-compat.
"""

LEARNABLE_SPELLS: dict[str, dict] = {

    # ==================================================================
    # FIRE FAMILY -- 5 tiers
    # ==================================================================
    'fire_spark_spell': {
        'name': 'Fire Spark', 'effect': 'fire_bolt', 'power': '1d6',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'fire',
        'desc': 'A dart of flame -- 1d6 fire damage to one target.',
    },
    'fire_bolt_spell': {
        'name': 'Fire Bolt', 'effect': 'fire_bolt', 'power': '3d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'fire',
        'desc': 'A bolt of concentrated flame -- 3d6 fire damage.',
    },
    'fireball_spell': {
        'name': 'Fireball', 'effect': 'mass_fire', 'power': '5d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'fire',
        'desc': 'A sphere of fire engulfs every visible enemy -- 5d6 fire damage.',
    },
    'meteor_spell': {
        'name': 'Meteor', 'effect': 'meteor', 'power': '8d6',
        'mp_cost': 16, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'fire',
        'desc': 'A single meteor crashes down -- 8d6 fire damage to all in sight.',
    },
    'cataclysm_spell': {
        'name': 'Cataclysm', 'effect': 'meteor_swarm', 'power': '6d8',
        'mp_cost': 24, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'fire',
        'desc': 'A rain of five meteors -- 6d8 fire damage per meteor, sky-fire everywhere.',
    },

    # ==================================================================
    # COLD FAMILY -- 4 tiers
    # ==================================================================
    'frost_touch_spell': {
        'name': 'Frost Touch', 'effect': 'frost_touch', 'power': '1d6',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'cold',
        'desc': 'A chilling touch -- 1d6 cold damage, 50% chance to slow.',
    },
    'cold_bolt_spell': {
        'name': 'Cold Bolt', 'effect': 'frost_touch', 'power': '3d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'cold',
        'desc': 'A shard of ice hurled at speed -- 3d6 cold damage, slows on hit.',
    },
    'ice_storm_spell': {
        'name': 'Ice Storm', 'effect': 'mass_ice', 'power': '6d6',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'cold',
        'desc': 'Freezing shards blast every visible foe -- 6d6 cold damage.',
    },
    'cone_of_cold_spell': {
        'name': 'Cone of Cold', 'effect': 'cone_of_cold', 'power': '8d8',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'cold',
        'desc': 'A widening cone of glacial cold -- 8d8 damage plus frozen status.',
    },

    # ==================================================================
    # LIGHTNING FAMILY -- 4 tiers
    # ==================================================================
    'spark_spell': {
        'name': 'Spark', 'effect': 'lightning_bolt', 'power': '1d8',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'lightning',
        'desc': 'A crackling spark -- 1d8 lightning damage in a short line.',
    },
    'lightning_bolt_spell': {
        'name': 'Lightning Bolt', 'effect': 'lightning_bolt', 'power': '4d6',
        'mp_cost': 7, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'lightning',
        'desc': 'A line of white lightning -- 4d6 damage to everything struck.',
    },
    'chain_lightning_spell': {
        'name': 'Chain Lightning', 'effect': 'chain_lightning_jump', 'power': '6d6',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'lightning',
        'desc': 'Lightning arcs through up to 4 targets, each at decreasing power.',
    },
    'storm_of_vengeance_spell': {
        'name': 'Storm of Vengeance', 'effect': 'storm_of_vengeance', 'power': '7d8',
        'mp_cost': 24, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'lightning',
        'desc': 'Thunder breaks overhead -- 7d8 lightning to all, 40% stun chance.',
    },

    # ==================================================================
    # FORCE / MISSILE FAMILY -- 5 tiers
    # ==================================================================
    'magic_dart_spell': {
        'name': 'Magic Dart', 'effect': 'magic_missile', 'power': '1d4',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'A single dart of force -- 1d4 damage, never misses.',
    },
    'magic_missile_spell': {
        'name': 'Magic Missile', 'effect': 'magic_missile', 'power': '2d4',
        'mp_cost': 5, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'Three darts of unerring force -- 2d4 damage each, always hits.',
    },
    'force_barrage_spell': {
        'name': 'Force Barrage', 'effect': 'magic_missile', 'power': '3d4',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'Five darts of shrieking force -- 3d4 damage each, never misses.',
    },
    'force_storm_spell': {
        'name': 'Force Storm', 'effect': 'magic_missile', 'power': '4d6',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'Seven force darts, each 4d6 damage, no defence available.',
    },
    'annihilation_spell': {
        'name': 'Annihilation', 'effect': 'annihilate', 'power': '10d10',
        'mp_cost': 25, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'force',
        'desc': 'Vaporize weakened enemies in sight, cripple the rest. Bosses only bleed.',
    },

    # ==================================================================
    # ACID FAMILY -- 3 tiers
    # ==================================================================
    'acid_dart_spell': {
        'name': 'Acid Dart', 'effect': 'acid_arrow', 'power': '2d4',
        'mp_cost': 5, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'acid',
        'desc': 'A splash of acid -- 2d4 acid damage plus a short poison DoT.',
    },
    'acid_arrow_spell': {
        'name': 'Acid Arrow', 'effect': 'acid_arrow', 'power': '4d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'acid',
        'desc': 'An arrow of biting acid -- 4d6 damage plus a lasting poison DoT.',
    },
    'dissolution_spell': {
        'name': 'Dissolution', 'effect': 'acid_arrow', 'power': '9d8',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'acid',
        'desc': 'A green torrent that eats through armor -- 9d8 damage, extreme DoT.',
    },

    # ==================================================================
    # HEALING FAMILY -- 5 tiers
    # ==================================================================
    'cure_light_spell': {
        'name': 'Cure Light Wounds', 'effect': 'extra_heal', 'power': '2d4',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'healing',
        'desc': 'Restore 2d4 HP.',
    },
    'cure_wounds_spell': {
        'name': 'Cure Wounds', 'effect': 'extra_heal', 'power': '4d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'healing',
        'desc': 'Restore 4d6 HP -- the workhorse healing prayer.',
    },
    'heal_spell': {
        'name': 'Heal', 'effect': 'extra_heal', 'power': '7d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'healing',
        'desc': 'Restore 7d6 HP -- the major healing word.',
    },
    'greater_heal_spell': {
        'name': 'Greater Heal', 'effect': 'extra_heal', 'power': '12d6',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'healing',
        'desc': 'Restore 12d6 HP -- full-body restoration.',
    },
    'resurrection_spell': {
        'name': 'Resurrection', 'effect': 'resurrection_self', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'healing',
        'desc': 'Ward yourself with life_save -- the next killing blow is refused.',
    },

    # ==================================================================
    # SLEEP FAMILY -- 3 tiers
    # ==================================================================
    'sleep_spell': {
        'name': 'Sleep', 'effect': 'sleep_monster', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'sleep',
        'desc': 'One target falls into slumber for 6 turns.',
    },
    'mass_sleep_spell': {
        'name': 'Mass Sleep', 'effect': 'mass_sleep', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'sleep',
        'desc': 'Every visible foe falls asleep for 10 turns.',
    },
    'deep_slumber_spell': {
        'name': 'Deep Slumber', 'effect': 'mass_sleep', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'sleep',
        'desc': 'A lullaby that puts every visible foe into deep paralysis.',
    },

    # ==================================================================
    # SLOW FAMILY -- 3 tiers
    # ==================================================================
    'slow_spell': {
        'name': 'Slow', 'effect': 'slow_monster_spell', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'slow',
        'desc': 'One target skips every other turn for 6 turns.',
    },
    'mass_slow_spell': {
        'name': 'Mass Slow', 'effect': 'mass_slow', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'slow',
        'desc': 'Every visible foe is slowed for 8 turns.',
    },
    'time_freeze_spell': {
        'name': 'Time Freeze', 'effect': 'time_freeze', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'slow',
        'desc': 'Freeze every visible foe for 5 turns -- the ultimate emergency.',
    },

    # ==================================================================
    # PARALYZE FAMILY -- 3 tiers
    # ==================================================================
    'hold_monster_spell': {
        'name': 'Hold Monster', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'paralyze',
        'desc': 'One target is paralyzed for 5 turns.',
    },
    'paralyze_spell': {
        'name': 'Paralyze', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'paralyze',
        'desc': 'One target is paralyzed for 10 turns.',
    },
    'mass_paralyze_spell': {
        'name': 'Mass Paralyze', 'effect': 'mass_sleep', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'paralyze',
        'desc': 'Every visible foe is paralyzed for 8 turns.',
    },

    # ==================================================================
    # FEAR FAMILY -- 2 tiers
    # ==================================================================
    'fear_spell': {
        'name': 'Fear', 'effect': 'fear_monster_spell', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'fear',
        'desc': 'One target flees in terror for 8 turns.',
    },
    'terror_spell': {
        'name': 'Terror', 'effect': 'mass_fear', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'fear',
        'desc': 'Every visible foe flees in unreasoning terror for 10 turns.',
    },

    # ==================================================================
    # CONFUSE FAMILY -- 2 tiers
    # ==================================================================
    'confusion_spell': {
        'name': 'Confusion', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'confuse',
        'desc': 'One target is confused for 10 turns.',
    },
    'madness_spell': {
        'name': 'Madness', 'effect': 'mass_confuse', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'confuse',
        'desc': 'Every visible foe is driven mad for 12 turns.',
    },

    # ==================================================================
    # BUFF / SHIELD FAMILY -- 3 tiers
    # ==================================================================
    'mage_armor_spell': {
        'name': 'Mage Armor', 'effect': 'shield_self', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'buff_shield',
        'desc': 'Shimmering force -- +2 AC and physical damage halved for 12 turns.',
    },
    'magic_shield_spell': {
        'name': 'Magic Shield', 'effect': 'shield_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'buff_shield',
        'desc': 'A stronger shield -- +2 AC, physical halved for 20 turns.',
    },
    'stoneskin_spell': {
        'name': 'Stoneskin', 'effect': 'stoneskin_self', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'buff_shield',
        'desc': 'Skin hardens to stone -- +2 AC, physical halved for 30 turns.',
    },

    # ==================================================================
    # HASTE FAMILY -- 2 tiers
    # ==================================================================
    'haste_spell': {
        'name': 'Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 7, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'haste',
        'desc': 'Move twice per turn for 10 turns.',
    },
    'greater_haste_spell': {
        'name': 'Greater Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'haste',
        'desc': 'Move twice per turn for 25 turns.',
    },

    # ==================================================================
    # INVISIBILITY FAMILY -- 2 tiers
    # ==================================================================
    'invisibility_spell': {
        'name': 'Invisibility', 'effect': 'invisibility_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'invisibility',
        'desc': 'Vanish from sight for 15 turns; breaks on attack.',
    },
    'greater_invisibility_spell': {
        'name': 'Greater Invisibility', 'effect': 'greater_invis_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'invisibility',
        'desc': 'Vanish from sight for 25 turns; attacking does NOT break it.',
    },

    # ==================================================================
    # DISPLACEMENT FAMILY -- 2 tiers
    # ==================================================================
    'displacement_spell': {
        'name': 'Displacement', 'effect': 'displacement_self', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'displacement',
        'desc': 'Attackers miss you 30% of the time for 20 turns.',
    },
    'reflect_spell': {
        'name': 'Spell Reflect', 'effect': 'reflect_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'displacement',
        'desc': '50% chance to reflect status attacks back to source for 20 turns.',
    },

    # ==================================================================
    # DETECT MAGIC / IDENTIFY FAMILY -- 3 tiers
    # ==================================================================
    'detect_magic_spell': {
        'name': 'Detect Magic', 'effect': 'identify_item', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'detect_magic',
        'desc': 'Reveal the BUC of every magical item in sight.',
    },
    'identify_spell': {
        'name': 'Identify', 'effect': 'identify_item', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'detect_magic',
        'desc': 'Reveal the BUC of every magical item in sight AND in your pack.',
    },
    'omnisight_spell': {
        'name': 'Omnisight', 'effect': 'identify_item', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'detect_magic',
        'desc': 'Reveal every magical item everywhere -- floor, pack, equipped.',
    },

    # ==================================================================
    # DETECT MONSTERS FAMILY -- 2 tiers
    # ==================================================================
    'detect_monsters_spell': {
        'name': 'Detect Monsters', 'effect': 'detect_monsters_spell', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'detect_monsters',
        'desc': 'Reveal every living creature on the floor for 15 turns.',
    },
    'foresight_spell': {
        'name': 'Foresight', 'effect': 'foresight_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'detect_monsters',
        'desc': 'Long-lasting clairvoyance -- see all creatures for 30 turns.',
    },

    # ==================================================================
    # MAPPING FAMILY -- 2 tiers
    # ==================================================================
    'mapping_spell': {
        'name': 'Mapping', 'effect': 'mapping', 'power': '',
        'mp_cost': 7, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'mapping',
        'desc': 'Reveal the entire floor layout.',
    },
    'greater_mapping_spell': {
        'name': 'Greater Mapping', 'effect': 'mapping', 'power': '',
        'mp_cost': 14, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'mapping',
        'desc': 'Reveal the entire floor -- layout, items, and creatures.',
    },

    # ==================================================================
    # TELEPORT FAMILY -- 3 tiers
    # ==================================================================
    'blink_spell': {
        'name': 'Blink', 'effect': 'teleport_self', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'teleport',
        'desc': 'Teleport to a random safe location on the floor.',
    },
    'phase_door_spell': {
        'name': 'Phase Door', 'effect': 'phase_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'teleport',
        'desc': 'Walk through walls for 12 turns.',
    },
    'gate_spell': {
        'name': 'Gate', 'effect': 'gate', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'teleport',
        'desc': 'Open a planar gate -- summon a powerful guardian ally.',
    },

    # ==================================================================
    # TURN UNDEAD FAMILY -- 2 tiers
    # ==================================================================
    'turn_undead_spell': {
        'name': 'Turn Undead', 'effect': 'turn_undead', 'power': '3d8',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'turn_undead',
        'desc': 'Holy light -- 3d8 holy damage + fear to visible undead.',
    },
    'sunburst_spell': {
        'name': 'Sunburst', 'effect': 'turn_undead', 'power': '10d8',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'turn_undead',
        'desc': 'A blazing sunburst -- 10d8 holy damage + fear to visible undead.',
    },

    # ==================================================================
    # POLYMORPH FAMILY -- 2 tiers
    # ==================================================================
    'polymorph_spell': {
        'name': 'Polymorph', 'effect': 'polymorph_spell', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'polymorph',
        'desc': 'Transform one target into a random creature. Bosses immune.',
    },
    'mass_polymorph_spell': {
        'name': 'Mass Polymorph', 'effect': 'mass_polymorph', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'polymorph',
        'desc': 'Every visible non-boss becomes a small animal -- HP/AC/speed slashed.',
    },

    # ==================================================================
    # DRAIN LIFE FAMILY -- 2 tiers
    # ==================================================================
    'drain_life_spell': {
        'name': 'Drain Life', 'effect': 'drain_life_spell', 'power': '3d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Steal 3d6 life -- damage target, heal yourself for the same.',
    },
    'soul_drain_spell': {
        'name': 'Soul Drain', 'effect': 'drain_life_spell', 'power': '7d8',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Rip 7d8 life from a creature and channel it into your own body.',
    },

    # ==================================================================
    # UTILITY SINGLES -- one tier each
    # ==================================================================
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'light',
        'desc': 'Reveal every tile within 15 squares.',
    },
    'knock_spell': {
        'name': 'Knock', 'effect': 'knock_spell', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'knock',
        'desc': 'Magically open the nearest locked container within 3 tiles.',
    },
    'cleanse_spell': {
        'name': 'Cleanse', 'effect': 'cleanse_self', 'power': '',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'cleanse',
        'desc': 'Remove one negative status effect.',
    },
    'empower_spell': {
        'name': 'Empower', 'effect': 'empower_next', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'empower',
        'desc': 'Next melee attack deals 3x damage.',
    },
    'levitate_spell': {
        'name': 'Levitate', 'effect': 'levitation_self', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'levitate',
        'desc': 'Float for 12 turns -- immune to floor traps and pits.',
    },
    'teleport_away_spell': {
        'name': 'Teleport Away', 'effect': 'teleport_away_spell', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'teleport_away',
        'desc': 'Teleport the nearest visible monster away -- or yourself if none.',
    },
    'smite_spell': {
        'name': 'Smite', 'effect': 'smite', 'power': '6d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'smite',
        'desc': 'Holy fire -- 6d6 damage that bypasses all resistances.',
    },
    'dispel_magic_spell': {
        'name': 'Dispel Magic', 'effect': 'dispel_magic', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'dispel_magic',
        'desc': 'Remove every magical buff from a target -- their protections fall.',
    },
    'counterspell_spell': {
        'name': 'Counterspell', 'effect': 'counterspell_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'counterspell',
        'desc': 'Magic resist for 15 turns -- blocks confused/charmed/feared/silenced/hallucinating.',
    },
    'summon_guardian_spell': {
        'name': 'Summon Guardian', 'effect': 'summon_guardian', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'summon',
        'desc': 'Summon a guardian pet to fight beside you.',
    },
    'disintegrate_spell': {
        'name': 'Disintegrate', 'effect': 'disintegrate_spell', 'power': '10d8',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'disintegrate',
        'desc': 'Reduce one creature to dust (50% chance vs non-bosses); bosses take 10d8.',
    },
    'power_word_kill_spell': {
        'name': 'Power Word: Kill', 'effect': 'power_word_kill', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'power_word_kill',
        'desc': 'Instakill any non-boss with HP at or below INT x 20. Bosses immune.',
    },
    'wish_spell': {
        'name': 'Wish', 'effect': 'wish', 'power': '',
        'mp_cost': 25, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'wish',
        'desc': 'Speak a desire -- reality answers with a random powerful boon.',
    },
    'imprisonment_spell': {
        'name': 'Imprisonment', 'effect': 'imprisonment', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'imprisonment',
        'desc': 'Seal one target in arcane stone -- paralyzed for 40 turns.',
    },
    'banishment_spell': {
        'name': 'Banishment', 'effect': 'banishment', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'banishment',
        'desc': 'Return one fey/demon/celestial/elemental to its plane of origin.',
    },
    'army_of_darkness_spell': {
        'name': 'Army of Darkness', 'effect': 'summon_undead_horde', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'army_of_darkness',
        'desc': 'Raise five undead minions to fight for you. Give me some sugar, baby.',
    },

    # ==================================================================
    # CHARACTER-BUILD SIGNATURE SPELLS (out of general pool)
    # Witcher signs -- Geralt build only. Each is a flavor variant of an
    # existing T1 effect, kept for theming.
    # ==================================================================
    'sign_aard': {
        'name': 'Aard', 'effect': 'aard_blast', 'power': '1d4',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Telekinetic blast -- damages and stuns a target.',
    },
    'sign_igni': {
        'name': 'Igni', 'effect': 'fire_bolt', 'power': '1d4',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Directed blast of fire. Burns on contact.',
    },
    'sign_quen': {
        'name': 'Quen', 'effect': 'shield_self', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'signature_witcher',
        'desc': 'Protective shield absorbs damage for 12 turns.',
    },
    'sign_yrden': {
        'name': 'Yrden', 'effect': 'slow_monster', 'power': '',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Magic trap -- slows a target for 8 turns.',
    },
    'sign_axii': {
        'name': 'Axii', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Charms the mind -- confuses a target for 10 turns.',
    },

    # Elder Blood signatures -- Ciri build only.
    'elder_blink': {
        'name': 'Blink', 'effect': 'teleport_self', 'power': '',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'signature_elder',
        'desc': 'Teleport to a random safe location. The Elder Blood bends space.',
    },
    'elder_charge': {
        'name': 'Charge', 'effect': 'empower_next', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'signature_elder',
        'desc': 'Channel Elder Blood -- next melee attack deals 3x damage.',
    },
    'elder_scream': {
        'name': 'Scream', 'effect': 'mass_ice', 'power': '2d4',
        'mp_cost': 10, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'signature_elder',
        'desc': 'Unleash the Elder Blood -- cold damage to all visible enemies.',
    },
}
