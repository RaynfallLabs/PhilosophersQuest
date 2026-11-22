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

import lights as _lights  # noqa: E402

_light = _lights.rules()['spell']
_light_sight = _lights.status_sight()

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
        'desc': 'A rain of five meteors: 6d8 fire damage shared between them, on everything in sight.',
    },

    # ==================================================================
    # COLD FAMILY -- 5 tiers
    # ==================================================================
    'frost_touch_spell': {
        'name': 'Frost Touch', 'effect': 'frost_touch', 'power': '2d4',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'cold',
        'desc': 'Lay a freezing hand on a foe beside you -- 2d4 cold damage, 50% chance to slow.',
    },
    'cold_bolt_spell': {
        'name': 'Cold Bolt', 'effect': 'frost_touch', 'power': '3d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'cold',
        'desc': 'A shard of ice hurled at speed -- 3d6 cold damage, slows on hit.',
    },
    'breath_of_boreas_spell': {
        'name': 'Breath of Boreas', 'effect': 'mass_ice', 'power': '4d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'cold',
        'desc': 'The north wind howls through the room -- 4d6 cold damage to every visible foe.',
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
        'desc': 'Glacial cold all round you, 5 tiles out -- 8d8 damage plus frozen status.',
    },

    # ==================================================================
    # LIGHTNING FAMILY -- 5 tiers
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
    'call_lightning_spell': {
        'name': 'Call Lightning', 'effect': 'lightning_bolt', 'power': '5d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'lightning',
        'desc': 'Lightning called down along a line -- 5d6 damage to everything struck, and a stun.',
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
        'desc': 'Three darts of unerring force -- 2d4 damage in all, always hits.',
    },
    'force_barrage_spell': {
        'name': 'Force Barrage', 'effect': 'magic_missile', 'power': '3d4',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'Five darts of shrieking force -- 3d4 damage in all, never misses.',
    },
    'force_storm_spell': {
        'name': 'Force Storm', 'effect': 'magic_missile', 'power': '4d6',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'force',
        'desc': 'Seven force darts, 4d6 damage in all, no defence available.',
    },
    'annihilation_spell': {
        'name': 'Annihilation', 'effect': 'annihilate', 'power': '10d10',
        'mp_cost': 25, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'force',
        'desc': 'Vaporize weakened enemies in sight, cripple the rest. Bosses only bleed.',
    },

    # ==================================================================
    # ACID FAMILY -- 5 tiers
    # ==================================================================
    'acid_splash_spell': {
        'name': 'Acid Splash', 'effect': 'acid_arrow', 'power': '1d6',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'acid',
        'desc': 'A flick of stinging acid -- 1d6 acid damage plus a short burn.',
    },
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
    'corrosion_spell': {
        'name': 'Corrosion', 'effect': 'acid_arrow', 'power': '6d8',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'acid',
        'desc': 'A gout of acid that eats into hide and steel -- 6d8 acid damage plus a long burn.',
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
        'desc': 'A lullaby that puts every visible foe to sleep for 20 turns. A blow wakes the one it lands on.',
    },

    # ==================================================================
    # SLOW FAMILY -- 3 tiers
    # ==================================================================
    'slow_spell': {
        # v2.15+ audit sync: desc "6 turns" -> matches applied 10 turns.
        'name': 'Slow', 'effect': 'slow_monster_spell', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'slow',
        'desc': 'One target skips every other turn for 10 turns.',
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
        'desc': 'Freeze every creature on the floor for 5 turns (a named foe for 2).',
    },

    # ==================================================================
    # PARALYZE FAMILY -- 3 tiers
    # ==================================================================
    'hold_monster_spell': {
        # v2.15+ audit sync: desc "5 turns" -> matches applied 8 turns.
        'name': 'Hold Monster', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'paralyze',
        'desc': 'One target is paralyzed for 8 turns.',
    },
    'paralyze_spell': {
        # Held longer than Hold Monster (T2, 8 turns): the deeper hold of
        # the ladder (MONSTERS AND MAGIC 2026-11-19; both were 8, a flat
        # ladder). A named foe is still held 2 turns at most.
        'name': 'Paralyze', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'paralyze', 'duration': 12,
        'desc': 'One target is paralyzed for 12 turns.',
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
        # v2.15+ audit sync: desc "8 turns" -> matches applied 10 turns.
        'name': 'Fear', 'effect': 'fear_monster_spell', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'fear',
        'desc': 'One target flees in terror for 10 turns.',
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
        # v2.15+ audit sync: given a distinct effect id so its 20-turn duration
        # is not aliased to mage_armor_spell's 12 turns. Tier progression fix.
        'name': 'Magic Shield', 'effect': 'magic_shield_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'buff_shield',
        'desc': 'A stronger shield -- +2 AC, physical halved for 20 turns.',
    },
    'stoneskin_spell': {
        # v2.15+ audit sync: desc was "30 turns" but code applies 25.
        # Kept the balanced 25-turn code; updated desc to match.
        'name': 'Stoneskin', 'effect': 'stoneskin_self', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'buff_shield',
        'desc': 'Skin hardens to stone -- +2 AC, physical halved for 25 turns.',
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
        # v2.15+ audit sync: distinct effect id + 20-turn duration so T5 haste
        # is meaningfully better than the T2 haste_self (10 turns). Desc updated
        # from "25 turns" to the actual 20 turns applied by the code.
        'name': 'Greater Haste', 'effect': 'greater_haste_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'haste',
        'desc': 'Move twice per turn for 20 turns.',
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
        # v2.15+ audit sync: desc "20 turns" -> matches applied 15 turns.
        'name': 'Spell Reflect', 'effect': 'reflect_self', 'power': '',
        'mp_cost': 20, 'tier': 5, 'quiz_tier': 5, 'needs_target': False,
        'spell_family': 'displacement',
        'desc': '50% chance to reflect status attacks back to source for 15 turns.',
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
        # v2.15+ audit sync: desc "15 turns" -> matches applied 20 turns.
        'name': 'Detect Monsters', 'effect': 'detect_monsters_spell', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'detect_monsters',
        'desc': 'Reveal every living creature on the floor for 20 turns.',
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
        # v2.15+ audit sync: desc "12 turns" -> matches applied 15 turns.
        'name': 'Phase Door', 'effect': 'phase_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'teleport',
        'desc': 'Walk through walls for 15 turns.',
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
    # DRAIN LIFE FAMILY -- 5 tiers
    # ==================================================================
    'life_tap_spell': {
        'name': 'Life Tap', 'effect': 'drain_life_spell', 'power': '1d6+1',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Touch a foe beside you and sip 1d6+1 life -- it is hurt, you heal the same.',
    },
    'drain_life_spell': {
        'name': 'Drain Life', 'effect': 'drain_life_spell', 'power': '4d6+1',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Lay hands on a foe beside you and steal 4d6+1 life -- it is hurt, you heal the same.',
    },
    'vampiric_touch_spell': {
        'name': 'Vampiric Touch', 'effect': 'drain_life_spell', 'power': '6d6+1',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Grip a foe beside you and draw 6d6+1 life out of it into yourself.',
    },
    'soul_drain_spell': {
        'name': 'Soul Drain', 'effect': 'drain_life_spell', 'power': '7d8+1',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Hold a creature beside you and rip 7d8+1 life from it into your own body.',
    },
    'enervation_spell': {
        'name': 'Enervation', 'effect': 'drain_life_spell', 'power': '10d8+1',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'drain_life',
        'desc': 'Seize a foe beside you and drain 10d8+1 life from it into your own body.',
    },

    # ==================================================================
    # UTILITY SINGLES -- one tier each
    # ==================================================================
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'light',
        # (Since 2026-11-19 a light that stays, not a spot of map lit once:
        # data/lights.json, game_magic.)
        'desc': (f"A light stays about you for {_light['base_turns']} turns, "
                 f"{_light['turns_per_int']} more for each point of INT over 10: "
                 f"sight +{_light_sight}. Only your brightest light counts, "
                 f"and you are seen from farther."),
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
    'sacred_flame_spell': {
        'name': 'Sacred Flame', 'effect': 'smite', 'power': '1d8',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'smite',
        'desc': 'A small holy flame -- 1d8 damage that bypasses all resistances.',
    },
    'holy_bolt_spell': {
        'name': 'Holy Bolt', 'effect': 'smite', 'power': '4d6',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'smite',
        'desc': 'A bolt of holy force -- 4d6 damage that bypasses all resistances.',
    },
    'smite_spell': {
        'name': 'Smite', 'effect': 'smite', 'power': '6d6',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'smite',
        'desc': 'Holy fire -- 6d6 damage that bypasses all resistances.',
    },
    'flame_strike_spell': {
        'name': 'Flame Strike', 'effect': 'smite', 'power': '7d8',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': True,
        'spell_family': 'smite',
        'desc': 'Fire falls from above -- 7d8 holy damage that bypasses all resistances.',
    },
    'judgment_spell': {
        'name': 'Judgment', 'effect': 'smite', 'power': '9d8',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'smite',
        'desc': "Heaven's own sentence -- 9d8 holy damage that bypasses all resistances.",
    },
    'dispel_magic_spell': {
        'name': 'Dispel Magic', 'effect': 'dispel_magic', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': True,
        'spell_family': 'dispel_magic',
        'desc': 'Remove every magical buff from a target -- its protections fall.',
    },
    'counterspell_spell': {
        # v2.15+ audit sync: desc "15 turns" -> matches applied 12 turns.
        'name': 'Counterspell', 'effect': 'counterspell_self', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'counterspell',
        'desc': 'Magic resist for 12 turns -- blocks confused/charmed/feared/silenced/hallucinating.',
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
        # v2.15+ audit sync: desc "40 turns" -> matches applied 60 turns
        # (capped by MAX_EFFECT_DURATION in status_effects.py).
        'name': 'Imprisonment', 'effect': 'imprisonment', 'power': '',
        'mp_cost': 22, 'tier': 5, 'quiz_tier': 5, 'needs_target': True,
        'spell_family': 'imprisonment',
        'desc': 'Seal one target in arcane stone -- paralyzed up to 60 turns (capped).',
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
    # MONSTERS AND MAGIC (2026-11-19): spells from myth, each the answer
    # to a threat in the dungeon (C/PROPOSALS.md; the wards are
    # src/wards.py, the gates on a monster src/attack_gates.py, the
    # handlers MagicWardsMixin in src/game_wards.py).
    # ==================================================================
    'galdr_of_loosing_spell': {
        'name': 'Galdr of Loosing', 'effect': 'loosing_self', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'galdr', 'duration': 6,
        'desc': 'Whatever holds you lets go, and for 6 turns nothing can grab, pin or drag you.',
    },
    'cockcrow_spell': {
        'name': 'Cockcrow', 'effect': 'turn_undead', 'power': '1d8',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'turn_undead', 'duration': 4,
        'desc': 'The first crow of the cock: every undead creature you can see takes 1d8 holy damage and flees for 4 turns.',
    },
    'sanctuary_spell': {
        'name': 'Sanctuary', 'effect': 'sanctuary_self', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'sanctuary', 'duration': 8,
        'desc': 'For 8 turns ordinary foes will not strike you. It ends the moment you strike, and a foe you hurt lately is not held back.',
    },
    'elf_shot_spell': {
        'name': 'Elf-Shot', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 3, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'paralyze', 'duration': 3,
        'desc': 'An elf-arrow no one sees fly: one foe you can see is frozen stiff for 3 turns.',
    },
    'stayed_spear_spell': {
        'name': 'Galdr of the Stayed Spear', 'effect': 'stayed_spear_self', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'galdr', 'duration': 12,
        'desc': 'For 12 turns arrows, stones and spears from any foe you can see drop short of you. What you cannot see still finds you.',
    },
    'tacitas_seal_spell': {
        'name': "Tacita's Seal", 'effect': 'silence_monster', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'silence', 'duration': 10,
        'desc': 'One foe is Silenced for 10 turns: it cannot wail, sing, call for help, heal or cast.',
    },
    'dionysus_vine_spell': {
        'name': "Dionysus's Vine", 'effect': 'entangle', 'power': '',
        'mp_cost': 7, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'entangle', 'duration': 4,
        'desc': 'Vines burst up round one foe: everything walking there is held fast for 4 turns, and for 12 turns the vines catch whatever steps in, you too.',
    },
    'shrink_the_earth_spell': {
        'name': 'Shrink the Earth', 'effect': 'aimed_step', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'needs_tile': True, 'spell_family': 'teleport',
        'desc': 'Pick a spot you can see, up to 6 steps away, and stand there.',
    },
    'bough_of_somnus_spell': {
        'name': 'Bough of Somnus', 'effect': 'sleep_area', 'power': '',
        'mp_cost': 6, 'tier': 2, 'quiz_tier': 2, 'needs_target': True,
        'spell_family': 'sleep', 'duration': 8,
        'desc': 'One foe and everything beside it fall asleep for 8 turns. A blow wakes the one it lands on.',
    },
    'dulled_blades_spell': {
        'name': 'Galdr of Dulled Blades', 'effect': 'mass_weaken', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'galdr', 'duration': 8,
        'desc': 'Every foe you can see is Weakened for 8 turns: its blows do half damage.',
    },
    'confusion_of_tongues_spell': {
        'name': 'Confusion of Tongues', 'effect': 'tongues', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'confuse', 'duration': 6,
        'desc': 'Every foe you can see that speaks is Confused for 6 turns, and for 12 its pack or war band forgets how to fight together.',
    },
    'darkness_of_egypt_spell': {
        'name': 'Darkness of Egypt', 'effect': 'mass_blind', 'power': '',
        'mp_cost': 10, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'darkness', 'duration': 6,
        'desc': 'Every foe you can see is Blinded for 6 turns. Your own eyes stay clear.',
    },
    'pans_panic_spell': {
        'name': "Pan's Panic", 'effect': 'pan_panic', 'power': '',
        'mp_cost': 9, 'tier': 3, 'quiz_tier': 3, 'needs_target': False,
        'spell_family': 'fear', 'duration': 8,
        'desc': 'Every foe within 4 steps of you runs in terror for 8 turns.',
    },
    'settled_strife_spell': {
        'name': 'Galdr of Settled Strife', 'effect': 'settled_strife', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'galdr', 'duration': 12,
        'desc': 'Every man, goblin and giant you can see lays down arms for 12 turns. Strike one and it ends for that one.',
    },
    'mist_of_manannan_spell': {
        'name': 'Mist of Manannan', 'effect': 'veil_self', 'power': '',
        'mp_cost': 14, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'veil', 'duration': 20,
        'desc': 'For 20 turns no foe more than 2 steps away can see you or shoot you: archers have to come close.',
    },
    'hush_of_the_feralia_spell': {
        'name': 'Hush of the Feralia', 'effect': 'mass_silence', 'power': '',
        'mp_cost': 15, 'tier': 4, 'quiz_tier': 4, 'needs_target': False,
        'spell_family': 'silence', 'duration': 8,
        'desc': 'Every foe you can see is Silenced for 8 turns: no wail, no song, no summoning, no healing, no spell.',
    },

    # ==================================================================
    # CHARACTER-BUILD SIGNATURE SPELLS (out of general pool)
    # Witcher signs -- Geralt build only. Each is a flavor variant of an
    # existing T1 effect, kept for theming.
    # ==================================================================
    'sign_aard': {
        'name': 'Aard', 'effect': 'aard_blast', 'power': '1d4+2',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Telekinetic blast at close range -- 1d4+2 damage and a stun.',
    },
    'sign_igni': {
        'name': 'Igni', 'effect': 'fire_bolt', 'power': '1d4+2',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'A short gout of fire at close range -- 1d4+2 fire damage.',
    },
    'sign_quen': {
        'name': 'Quen', 'effect': 'shield_self', 'power': '',
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': False,
        'spell_family': 'signature_witcher',
        'desc': 'Protective shield absorbs damage for 12 turns.',
    },
    'sign_yrden': {
        'name': 'Yrden', 'effect': 'slow_monster', 'power': '', 'duration': 14,
        'mp_cost': 2, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Magic trap set close by -- slows a target for 14 turns.',
    },
    'sign_axii': {
        'name': 'Axii', 'effect': 'confuse_monster', 'power': '', 'duration': 16,
        'mp_cost': 4, 'tier': 1, 'quiz_tier': 1, 'needs_target': True,
        'spell_family': 'signature_witcher',
        'desc': 'Charms a mind at close range -- confuses a target for 16 turns.',
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
        # v2.15+ audit sync: mp_cost 10 -> 8 to fit the T2 band (5..8).
        'name': 'Scream', 'effect': 'mass_ice', 'power': '2d4',
        'mp_cost': 8, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
        'spell_family': 'signature_elder',
        'desc': 'Unleash the Elder Blood -- cold damage to all visible enemies.',
    },
}


# ---------------------------------------------------------------------------
# Reach: how far an aimed spell goes (Brandon, 2026-11-07, bug bash 3.3.2).
# "Frost Touch is obviously supposed to be TOUCH, but it has range."
#
#   REACH_TOUCH (1): the hand must reach the foe (any tile of a big one). The
#       risk is standing beside it, so a touch spell hits harder: up to 1.1
#       of a weapon attack (tests/test_magic_role.py), the allowance the
#       undead-only spells have.
#   REACH_SHORT (3): Geralt's signs (close-range in their lore, and stronger
#       for it), a spark from the fingertips, a splash of acid, the lance of
#       Smite.
#   None: as far as the hero can see, in a clear line (bolts, missiles,
#       arrows, beams, and the aimed status spells).
#
# Measured in king moves (geom.chebyshev_distance) and enforced where the
# aim is taken: the target list, the cursor, and the confirm
# (_invoke_spell, _target_input, _confirm_power_target). The effect handlers
# do not check it (a scroll or a test may hand them any target).
# ---------------------------------------------------------------------------
REACH_TOUCH = 1
REACH_SHORT = 3

SPELL_REACH: dict[str, int] = {
    'frost_touch_spell': REACH_TOUCH,
    'drain_life_spell':  REACH_TOUCH,
    'soul_drain_spell':  REACH_TOUCH,
    'life_tap_spell':    REACH_TOUCH,
    'vampiric_touch_spell': REACH_TOUCH,
    'enervation_spell':  REACH_TOUCH,
    'sign_aard':         REACH_SHORT,
    'sign_igni':         REACH_SHORT,
    'sign_yrden':        REACH_SHORT,
    'sign_axii':         REACH_SHORT,
    'spark_spell':       REACH_SHORT,
    'acid_dart_spell':   REACH_SHORT,
    'acid_splash_spell': REACH_SHORT,
    'smite_spell':       REACH_SHORT,
    'sacred_flame_spell': REACH_SHORT,
    # Shrink the Earth folds only a little ground: a tile in sight, 6 off.
    'shrink_the_earth_spell': 6,
}

for _sid, _spell in LEARNABLE_SPELLS.items():
    if _spell.get('needs_target') or _spell.get('needs_tile'):
        _spell['reach'] = SPELL_REACH.get(_sid)


def spell_reach(spell) -> int | None:
    """Tiles an aimed spell reaches (None: as far as the hero can see)."""
    if not spell:
        return None
    r = spell.get('reach') if isinstance(spell, dict) else None
    return int(r) if r else None


def reach_words(reach: int | None) -> str:
    """'touch', '3 tiles' or 'sight', for the spell menu and messages."""
    if not reach:
        return 'sight'
    if reach <= REACH_TOUCH:
        return 'touch'
    return f"{reach} tile{'s' if reach != 1 else ''}"
