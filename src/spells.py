"""Spells learnable from spellbooks (spell_id -> attributes).

2026 REBALANCE — 5 tiers × ~12 spells = 60 spells with full coverage in every
tier (damage single+AOE, heal, buff, debuff, utility, summon).

Damage power dice and mp_cost scale against tools/balance/curve.py so a
chain-5 spell rivals a chain-5 weapon at the spell's tier band. MP is the
INT-based resource (max_mp = 10 + INT). quiz_tier maps to the math quiz
difficulty (T1 → F0-19, T2 → F20-39, T3 → F40-59, T4 → F60-79, T5 → F80-99).

Witcher signs (sign_*) and Elder Blood spells (elder_*) are character-build
signature spells, only available via specific welcome_screen.py builds, NOT
in the general spellbook drop pool. They duplicate generic spells with
different lore/names — kept for theming, not for variety in the main pool.
"""

LEARNABLE_SPELLS: dict[str, dict] = {

    # ==================================================================
    # TIER 1 — NOVICE (F0-19, 2-5 MP) — 12 spells
    # ==================================================================
    'magic_missile_spell': {
        'name': 'Magic Missile', 'effect': 'magic_missile', 'power': '1d4',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Unerring force darts — fires one per chain link, never misses.',
    },
    'frost_touch_spell': {
        'name': 'Frost Touch', 'effect': 'frost_touch', 'power': '1d6',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Cold damage with a 50% chance to slow the target.',
    },
    'cure_wounds_spell': {
        'name': 'Cure Wounds', 'effect': 'extra_heal', 'power': '2d4',
        'mp_cost': 5, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Restore 2d4 HP (chain-scaled).',
    },
    'mage_armor_spell': {
        'name': 'Mage Armor', 'effect': 'shield_self', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Shimmering force gives +2 AC, halves physical damage for 12 turns.',
    },
    'sleep_spell': {
        'name': 'Sleep', 'effect': 'sleep_monster', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Puts one monster to sleep for 6 turns.',
    },
    'slow_spell': {
        'name': 'Slow', 'effect': 'slow_monster_spell', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': True,
        'desc': 'Target skips every other turn for 4-10 turns.',
    },
    'light_spell': {
        'name': 'Light', 'effect': 'light', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Reveal nearby tiles in a 15-radius area.',
    },
    'detect_magic_spell': {
        'name': 'Detect Magic', 'effect': 'identify_item', 'power': '',
        'mp_cost': 3, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Reveal BUC of all wands/scrolls/spellbooks in sight (and pack at chain 3+).',
    },
    'blink_spell': {
        'name': 'Blink', 'effect': 'teleport_self', 'power': '',
        'mp_cost': 3, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Teleport to a random safe location.',
    },
    'cleanse_spell': {
        'name': 'Cleanse', 'effect': 'cleanse_self', 'power': '',
        'mp_cost': 2, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Remove one negative status effect.',
    },
    'knock_spell': {
        'name': 'Knock', 'effect': 'knock_spell', 'power': '',
        'mp_cost': 5, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Magically open the nearest locked container.',
    },
    'empower_spell': {
        'name': 'Empower', 'effect': 'empower_next', 'power': '',
        'mp_cost': 4, 'quiz_tier': 1, 'needs_target': False,
        'desc': 'Next melee attack deals 3x damage.',
    },

    # ==================================================================
    # TIER 2 — APPRENTICE (F20-39, 5-10 MP) — 12 spells
    # ==================================================================
    'fire_bolt_spell': {
        'name': 'Fire Bolt', 'effect': 'fire_bolt', 'power': '2d4',
        'mp_cost': 6, 'quiz_tier': 2, 'needs_target': True,
        'desc': 'Fire bolt, 2d4 damage. Burns on contact.',
    },
    'acid_arrow_spell': {
        'name': 'Acid Arrow', 'effect': 'acid_arrow', 'power': '2d6',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': True,
        'desc': '2d6 acid + chain-scaled poison DoT.',
    },
    'lightning_bolt_spell': {
        'name': 'Lightning Bolt', 'effect': 'lightning_bolt', 'power': '3d4',
        'mp_cost': 8, 'quiz_tier': 2, 'needs_target': True,
        'desc': 'Line of lightning, 3d4 damage.',
    },
    'fireball_spell': {
        'name': 'Fireball', 'effect': 'mass_fire', 'power': '2d6',
        'mp_cost': 10, 'quiz_tier': 2, 'needs_target': False,
        'desc': '2d6 fire damage to all visible monsters.',
    },
    'heal_spell': {
        'name': 'Heal', 'effect': 'extra_heal', 'power': '3d6',
        'mp_cost': 8, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Restore 3d6 HP (scales with chain).',
    },
    'magic_shield_spell': {
        'name': 'Magic Shield', 'effect': 'shield_self', 'power': '',
        'mp_cost': 5, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Better shield: +2 AC, physical halved for 18 turns.',
    },
    'haste_spell': {
        'name': 'Haste', 'effect': 'haste_self', 'power': '',
        'mp_cost': 7, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Move twice per turn for 10 turns.',
    },
    'confusion_spell': {
        'name': 'Confusion', 'effect': 'confuse_monster', 'power': '',
        'mp_cost': 6, 'quiz_tier': 2, 'needs_target': True,
        'desc': 'Confuse a monster for 10 turns.',
    },
    'sleep_mass_spell': {
        'name': 'Mass Sleep', 'effect': 'mass_sleep', 'power': '',
        'mp_cost': 10, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Lullaby — all visible monsters fall asleep.',
    },
    'detect_monsters_spell_t2': {
        'name': 'Detect Monsters', 'effect': 'detect_monsters_spell', 'power': '',
        'mp_cost': 6, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Reveal all monsters on the level for chain-scaled turns.',
    },
    'levitate_spell': {
        'name': 'Levitate', 'effect': 'levitation_self', 'power': '',
        'mp_cost': 6, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Float for 12+ turns — immune to floor traps and pits.',
    },
    'teleport_away_spell': {
        'name': 'Teleport Away', 'effect': 'teleport_away_spell', 'power': '',
        'mp_cost': 5, 'quiz_tier': 2, 'needs_target': False,
        'desc': 'Teleport nearest monster away, or yourself if none visible.',
    },

    # ==================================================================
    # TIER 3 — ADEPT (F40-59, 10-15 MP) — 12 spells
    # ==================================================================
    'smite_spell': {
        'name': 'Smite', 'effect': 'smite', 'power': '4d6',
        'mp_cost': 13, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Holy fire, 4d6 damage — bypasses resistances.',
    },
    'drain_life_spell': {
        'name': 'Drain Life', 'effect': 'drain_life_spell', 'power': '2d8',
        'mp_cost': 11, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Steal life — damage target, heal yourself for the same.',
    },
    'cone_of_cold_spell': {
        'name': 'Cone of Cold', 'effect': 'cone_of_cold', 'power': '3d6',
        'mp_cost': 14, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Cold AOE within 5 tiles + brief frozen status.',
    },
    'greater_heal_spell': {
        'name': 'Greater Heal', 'effect': 'extra_heal', 'power': '6d6',
        'mp_cost': 14, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Restore 6d6 HP — the major healing word.',
    },
    'stoneskin_spell': {
        'name': 'Stoneskin', 'effect': 'stoneskin_self', 'power': '',
        'mp_cost': 12, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Skin hardens to stone — shielded for 25+ turns.',
    },
    'invisibility_spell': {
        'name': 'Invisibility', 'effect': 'invisibility_self', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Become invisible for 15 turns.',
    },
    'counterspell_spell': {
        'name': 'Counterspell', 'effect': 'counterspell_self', 'power': '',
        'mp_cost': 11, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Magic resist for 12 turns — blocks confused/charmed/feared/silenced/hallucinating.',
    },
    'dispel_magic_spell': {
        'name': 'Dispel Magic', 'effect': 'dispel_magic', 'power': '',
        'mp_cost': 12, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Remove all status effects from target — wipes their buffs.',
    },
    'fear_spell': {
        'name': 'Fear', 'effect': 'fear_monster_spell', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Target flees in terror for chain-scaled turns.',
    },
    'paralyze_spell': {
        'name': 'Hold Monster', 'effect': 'paralyze_monster', 'power': '',
        'mp_cost': 13, 'quiz_tier': 3, 'needs_target': True,
        'desc': 'Paralyze a monster for 8 turns.',
    },
    'summon_guardian_spell': {
        'name': 'Summon Guardian', 'effect': 'summon_guardian', 'power': '',
        'mp_cost': 13, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Summon a guardian pet to fight beside you.',
    },
    'mapping_spell': {
        'name': 'Mapping', 'effect': 'mapping', 'power': '',
        'mp_cost': 10, 'quiz_tier': 3, 'needs_target': False,
        'desc': 'Reveal the entire floor layout.',
    },

    # ==================================================================
    # TIER 4 — MASTER (F60-79, 15-25 MP) — 12 spells
    # ==================================================================
    'ice_storm_spell': {
        'name': 'Ice Storm', 'effect': 'mass_ice', 'power': '5d6',
        'mp_cost': 16, 'quiz_tier': 4, 'needs_target': False,
        'desc': '5d6 cold damage to all visible monsters.',
    },
    'meteor_spell': {
        'name': 'Meteor', 'effect': 'meteor', 'power': '6d6',
        'mp_cost': 18, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Massive single meteor — fire AoE to all visible.',
    },
    'chain_lightning_spell': {
        'name': 'Chain Lightning', 'effect': 'chain_lightning_jump', 'power': '4d6',
        'mp_cost': 17, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Lightning arcs through up to 3 targets at decreasing power.',
    },
    'displacement_spell': {
        'name': 'Displacement', 'effect': 'displacement_self', 'power': '',
        'mp_cost': 15, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Attackers miss you 30% of time for 20 turns.',
    },
    'greater_invisibility_spell': {
        'name': 'Greater Invisibility', 'effect': 'greater_invis_self', 'power': '',
        'mp_cost': 18, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Invisibility for 25+ turns — attacking does not break it.',
    },
    'reflect_spell': {
        'name': 'Spell Reflect', 'effect': 'reflect_self', 'power': '',
        'mp_cost': 15, 'quiz_tier': 4, 'needs_target': False,
        'desc': '50% chance to reflect status attacks for 15+ turns.',
    },
    'mass_paralyze_spell': {
        'name': 'Mass Paralyze', 'effect': 'mass_sleep', 'power': '',
        'mp_cost': 20, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Every visible monster falls under deep paralysis.',
    },
    'polymorph_spell': {
        'name': 'Polymorph', 'effect': 'polymorph_spell', 'power': '',
        'mp_cost': 15, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Transform a monster into a random creature. Risky!',
    },
    'banishment_spell': {
        'name': 'Banishment', 'effect': 'banishment', 'power': '',
        'mp_cost': 18, 'quiz_tier': 4, 'needs_target': True,
        'desc': 'Return a fey/demon/celestial/elemental to its plane of origin.',
    },
    'phase_door_spell': {
        'name': 'Phase Door', 'effect': 'phase_self', 'power': '',
        'mp_cost': 16, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Walk through walls for chain-scaled turns.',
    },
    'army_of_darkness_spell': {
        'name': 'Army of Darkness', 'effect': 'summon_undead_horde', 'power': '',
        'mp_cost': 22, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Raise an undead horde to fight for you. Give me some sugar, baby.',
    },
    'turn_undead_spell': {
        'name': 'Turn Undead', 'effect': 'turn_undead', 'power': '',
        'mp_cost': 14, 'quiz_tier': 4, 'needs_target': False,
        'desc': 'Drive nearby undead to flee in terror.',
    },

    # ==================================================================
    # TIER 5 — ARCHMAGE (F80-99, 20-40 MP) — 12 spells
    # ==================================================================
    'disintegrate_spell': {
        'name': 'Disintegrate', 'effect': 'disintegrate_spell', 'power': '9d8',
        'mp_cost': 25, 'quiz_tier': 5, 'needs_target': True,
        'desc': 'Chain-scaling instant kill (30-90%). Bosses take 9d8 instead.',
    },
    'meteor_swarm_spell': {
        'name': 'Meteor Swarm', 'effect': 'meteor_swarm', 'power': '5d6',
        'mp_cost': 32, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Multiple meteors fall — 2-5 strikes depending on chain.',
    },
    'storm_of_vengeance_spell': {
        'name': 'Storm of Vengeance', 'effect': 'storm_of_vengeance', 'power': '5d8',
        'mp_cost': 30, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Lightning to all visible + 40% stun chance per target.',
    },
    'time_freeze_spell': {
        'name': 'Time Freeze', 'effect': 'time_freeze', 'power': '',
        'mp_cost': 28, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Freeze all monsters for 3-5 turns. The ultimate emergency.',
    },
    'wish_spell': {
        'name': 'Wish', 'effect': 'wish', 'power': '',
        'mp_cost': 40, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Speak desire and reality answers. Random powerful effect.',
    },
    'power_word_kill_spell': {
        'name': 'Power Word: Kill', 'effect': 'power_word_kill', 'power': '',
        'mp_cost': 24, 'quiz_tier': 5, 'needs_target': True,
        'desc': 'Instakill if target HP ≤ INT × chain × 4. Bosses immune.',
    },
    'resurrection_spell': {
        'name': 'Resurrection', 'effect': 'resurrection_self', 'power': '',
        'mp_cost': 30, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Apply life_save — survive one killing blow.',
    },
    'foresight_spell': {
        'name': 'Foresight', 'effect': 'foresight_self', 'power': '',
        'mp_cost': 22, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Long-duration clairvoyance — see all monsters for 30+ turns.',
    },
    'gate_spell': {
        'name': 'Gate', 'effect': 'gate', 'power': '',
        'mp_cost': 28, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Open a planar gate — summon a guardian double the usual level.',
    },
    'imprisonment_spell': {
        'name': 'Imprisonment', 'effect': 'imprisonment', 'power': '',
        'mp_cost': 26, 'quiz_tier': 5, 'needs_target': True,
        'desc': 'Seal target in arcane stone — paralyzed 15-60 turns.',
    },
    'mass_polymorph_spell': {
        'name': 'Mass Polymorph', 'effect': 'mass_polymorph', 'power': '',
        'mp_cost': 26, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Every visible non-boss becomes a small animal — HP/AC/speed slashed.',
    },
    'annihilation_spell': {
        'name': 'Annihilation', 'effect': 'annihilate', 'power': '',
        'mp_cost': 35, 'quiz_tier': 5, 'needs_target': False,
        'desc': 'Vaporize all non-boss enemies. The reckoning.',
    },

    # ==================================================================
    # CHARACTER-BUILD SIGNATURE SPELLS (out of general pool)
    # Witcher signs — Geralt build only. Each is a flavor variant of an
    # existing T1 effect, kept for theming.
    # ==================================================================
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

    # Elder Blood signatures — Ciri build only.
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
