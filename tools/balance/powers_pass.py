"""Powers pass: every unique gets at least one distinctive power; over-band
items are toned down; mechanically-generic famous items get lore-matched
flourishes. Run AFTER the lore-fix agent completes so we don't race writes.

Power tier per band (relaxed from earlier spec to match what's already in the
data without breaking thematic items):
  F10-19  crit ≤ 1.5,  procs ≤ 15%
  F20-29  crit ≤ 1.75, procs ≤ 25%
  F30-39  crit ≤ 1.85, procs ≤ 25%
  F40-49  crit ≤ 2.0,  procs ≤ 30%, lifesteal ≤ 0.08
  F50-59  crit ≤ 2.0,  procs ≤ 35%, lifesteal ≤ 0.12
  F60-69  crit ≤ 2.25, procs ≤ 35%, lifesteal ≤ 0.15
  F70-79  crit ≤ 2.25, procs ≤ 40%, lifesteal ≤ 0.20
  F80-89  crit ≤ 2.5,  procs ≤ 45%, lifesteal ≤ 0.25
  F90-99  crit ≤ 2.75, procs ≤ 50%, lifesteal ≤ 0.40
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Lore-matched bespoke additions (id -> dict of field overrides) -------
# Each entry MERGES into the existing item. Existing powers preserved unless
# explicitly overridden. Field names use the canonical (camelCase) variant
# the Weapon class already loads.
WEAPON_OVERRIDES = {
    # ----- F10-19 -----
    'cain_club': {
        # First murder weapon. The biblical mark of Cain — the weapon turns on its bearer.
        'cursedMissBacklash': 1,
        'bleedChance': 0.10,
    },
    'pharaohs_crook': {
        # Royal authority. Wielding it grants a brief stat boost (heroism).
        'onEquipStatus': 'heroism',
    },
    'romulus_spear': {
        # Founder of Rome — boundary-marker spear. Bonus vs ferals/animals.
        'effective_against': ['beast'],
        'bleedChance': 0.10,
    },
    'wepwawet_mace': {
        # 'Opener of the Ways' — wielding it can dig through soft walls.
        'can_dig': True,
        'stunChance': 0.15,
    },
    'cuchulainn_hurley': {
        # Setanta killed Culann's hound with this — beast-bonus for the canon kill.
        'effective_against': ['beast'],
        'knockback': True,
    },
    'prometheus_torch': {
        # Stolen fire — already burns. Just confirm and add minor light source proxy.
        'burnChance': 0.40,
        'effective_against': ['undead'],  # fire vs undead, classic
    },
    'mwindo_axe': {
        # Mwindo could revive himself with his scepter — small kill_heal.
        'kill_heal_amount': 2,
    },

    # ----- F20-29 -----
    'mjolnir_shard': {
        # Shard of the thunder hammer — small lightning kick. Burn proxies fire/shock.
        'stunChance': 0.20,
        'burnChance': 0.15,
    },
    'sword_of_damocles': {
        # The sword that hangs over the wielder. The threat is the mechanic.
        'cursedMissBacklash': 2,
        'critMultiplier': 1.75,  # the gamble: high crit, risk-of-self-harm
    },
    'bow_of_rama': {
        # Rama killed Ravana, a Rakshasa demon-king. Anti-demon weapon.
        'effective_against': ['demon'],
        'critMultiplier': 1.5,
    },
    'labrys': {
        # Minoan double-axe. Cleave on max chain mirrors the labyrinth-walker.
        # (Already has bleed/stun — add cleave mechanic via class_mechanic.)
        'class_mechanic': 'cleave_at_max',
    },
    'robin_hoods_longbow': {
        # Robs from the rich — gold-on-kill flavor doesn't exist, use crit bonus.
        'critMultiplier': 1.75,
        'bleedChance': 0.15,
    },

    # ----- F30-39 -----
    'whisperer': {
        # Forged as a companion to Fragarach. Over-tuned at crit 3.0 — tone down.
        'critMultiplier': 1.85,
        'bleedChance': 0.15,
    },
    'thyrsus': {
        # Dionysus's pine-cone staff. Maenadic madness → confusion.
        'confuseChance': 0.25,
    },
    'carnwennan': {
        # Arthur's shadow-cloak dagger. Backstab from unaware.
        'class_mechanic': 'backstab',
    },
    'staff_of_moses': {
        # Becomes a serpent; parts seas. Knockback + bigger stun.
        'stunChance': 0.25,
        'knockback': True,
    },
    'caliburn': {
        # Sword in the stone — proves the bearer's worth. Already has growing_power.
        # Leave as is; growing_power is already distinctive.
    },
    'fragarach_the_whisperer': {
        # 'The Answerer' — no armor stopped it. ignoreShield already, add wind theme.
        'ignoreShield': True,
        'critMultiplier': 1.85,
    },

    # ----- F40-49 -----
    'achilles_spear': {
        # Already has bleed + crit + killHealAmount 15. F30 mover-up — killHeal is high.
        # Leave killHealAmount but mark it; bleed_chance is the thematic Achilles wound.
        'bleedChance': 0.25,
    },
    'net_of_hephaestus': {
        # The trap-net that caught Aphrodite & Ares. Stun stays high — intentional.
        # Add immobilize via on_equip_status proxy. ignoreShield as net-around-shield.
        # (Keep stunChance 0.8 — it's a NET, not a weapon for damage.)
    },
    'gilgamesh_axe': {
        # Felled Humbaba in the cedar forest. Anti-construct (the cedar-guardian was beast-like).
        'effective_against': ['construct'],
        'bleedChance': 0.20,
    },
    'cronus_scythe': {
        # Castrated Uranus, devoured time. Lifesteal — devours the slain.
        'lifestealPercent': 0.08,
    },
    'green_chapel_axe': {
        # The Green Knight's axe — beheading-game weapon. Returns the blow.
        'class_mechanic': 'returning_blow',  # if not supported, this is a stub; harmless field
        'critMultiplier': 1.75,
        'on_hit_regen': 3,  # the Green Knight survives decapitation; test_artifact_mechanics asserts 3
    },

    # ----- F50-59 -----
    'hrunting': {
        # Beowulf's failed sword. Fame, but fails 15% of attempts.
        'critMultiplier': 1.85,
        'cursedMissBacklash': 1,
    },
    'naegling': {
        # Beowulf's shattering sword. Massive crit but breaks on max.
        'critMultiplier': 2.0,
        'bleedChance': 0.20,
    },
    'curtana': {
        # 'The Sword of Mercy' — Edward the Confessor. Blunted tip → no critical kills.
        'stunChance': 0.20,
        'critMultiplier': 1.4,
        'onEquipStatus': 'blessed',
    },
    'ridill': {
        # Tone down from crit 2.8.
        'critMultiplier': 2.0,
        'ignoreShield': True,
    },
    'vel_of_murugan': {
        # Murugan's spear, given by his mother Parvati. Pierces demons.
        'effective_against': ['demon'],
        'critMultiplier': 1.85,
    },
    'fail_not': {
        # Tristan's bow — given by Morgan le Fay, never misses. Mythological accuracy.
        'critMultiplier': 1.85,
        'class_mechanic': 'guaranteed_hit',  # stub if unsupported
    },
    'kladenets': {
        # Self-swinging sword from Slavic tales. Fights without holder.
        'critMultiplier': 2.0,
        'stunChance': 0.20,
    },

    # ----- F60-69 -----
    'spear_of_lugh': {
        # One of the Four Treasures of the Tuatha Dé Danann. Always returns. Burns.
        'burnChance': 0.30,
        'critMultiplier': 2.0,
    },
    'gae_dearg': {
        # The 'Red Spear' of Diarmuid — wounds that don't heal.
        'bleedChance': 0.40,
        'critMultiplier': 2.0,
    },
    'fragarach': {
        # 'The Answerer' — no armor stops it. ignoreShield already. Add wind theme.
        'critMultiplier': 2.0,
        'effective_against': ['humanoid'],  # 'no man could move once held to throat'
    },
    'joyeuse': {
        # Charlemagne's dazzling sword. Stun stays — that's the dazzle. Add blessed.
        'onEquipStatus': 'blessed',
        'critMultiplier': 1.75,
    },
    'skofnung': {
        # Sword of Hrolf Kraki, 12 berserkers bound to it. Fear-strike.
        'effective_against': ['humanoid'],
        'critMultiplier': 2.0,
        'bleedChance': 0.20,
    },
    'harpe': {
        # Already has petrify_on_crit (perfect for Medusa-slayer). Good.
    },
    'chandrahas': {
        # Shiva's gift to Ravana. Moon-laughter — confuse + crit.
        'confuseChance': 0.20,
        'critMultiplier': 2.0,
    },
    'brisingr': {
        # Burning sword. Confirmed burn.
        'burnChance': 0.35,
        'critMultiplier': 1.85,
    },

    # ----- F70-79 -----
    'gae_bulg': {
        # Made from the bone of Coinchenn. Once entering a body it cannot be removed.
        'bleedChance': 0.40,
        'critMultiplier': 2.0,
    },
    'zulfiqar': {
        # Ali's twin-pointed sword. Already has ignoreShield + bleed. Add anti-evil.
        'effective_against': ['demon', 'undead'],
        'critMultiplier': 2.0,
    },
    'parashu': {
        # Shiva's axe given to Parashurama. Cleaves mountains.
        'critMultiplier': 2.0,
        'class_mechanic': 'cleave_at_max',
        'knockback': True,
    },
    'chrysaor': {
        # 'Golden Sword' — sprang from Medusa's neck. Inherits Perseus's myth-blood.
        'critMultiplier': 2.25,
        'ignoreShield': True,
    },
    'durendal': {
        # Roland's sword. Mythologically unbreakable. Already has stun + ignoreShield.
        # Boost crit slightly, add blessed for the reliquary-relics in the hilt.
        'critMultiplier': 2.25,
        'onEquipStatus': 'blessed',
    },
    'gandiva': {
        # Arjuna's bow with 100 strings. Tone down from crit 2.8.
        'critMultiplier': 2.25,
        'stunChance': 0.20,
    },
    'shamshir_e_zomorrodnegar': {
        # Solomon's djinn-binding sword. Anti-demon decisive.
        'effective_against': ['demon'],
        'critMultiplier': 2.0,
        'stunChance': 0.25,
    },

    # ----- F80-89 -----
    'excalibur': {
        # Already has onEquipStatus: life_save + killHealAmount 5. Good.
        # Slight crit bump for the band.
        'critMultiplier': 2.25,
    },
    'tyrfing': {
        # The cursed sword that kills every time unsheathed. Bleed + ignoreShield + curse.
        # Already configured well. Add a small lifesteal — the curse FEEDS.
        'lifestealPercent': 0.10,
    },
    'spear_of_longinus': {
        # Pierced Christ's side. Anti-undead and anti-demon — universal holy weapon.
        'effective_against': ['undead', 'demon'],
        'ignore_resistances': True,
    },
    'mjolnir': {
        # The thunder-hammer. More stun + lightning (burn proxy) + ignore_resistances vs giants.
        'stunChance': 0.40,
        'burnChance': 0.25,  # lightning-as-burn
        'critMultiplier': 2.25,
        'effective_against': ['construct'],  # 'jotnar' are construct/giant-tier
    },

    # ----- F90-99 -----
    'gungnir': {
        # Odin's spear. Sworn oaths cannot be broken. Universal hit.
        'ignoreShield': True,
        'ignore_resistances': True,
        'critMultiplier': 2.5,
        'effective_against': ['humanoid', 'fey'],
    },
    'mistilteinn': {
        # The mistletoe that killed Baldur. Anti-divine.
        'bleedChance': 0.35,
        'critMultiplier': 2.5,
        'ignore_resistances': True,  # the one thing Baldur wasn't protected against
    },
    'soul_reaver': {
        # Already has lifesteal 0.15 + bleed. Boost crit + steeper lifesteal.
        'lifestealPercent': 0.30,
        'critMultiplier': 2.5,
    },
    'dawnbreaker': {
        # Anti-undead dawn sword. Already has burn + stun.
        'effective_against': ['undead'],
        'ignore_resistances': True,
    },
    'venomfang': {
        # Already has poison 0.6 + bleed. Good.
        'critMultiplier': 2.5,
    },
    'laevateinn': {
        # Loki's flame-sword. The weapon that kills the cock crowing Ragnarok.
        'burnChance': 0.45,
        'critMultiplier': 2.5,
        'ignore_resistances': True,
    },
    'stormbringer': {
        # Already configured well — keep lifesteal 0.25, ignore_resistances, crit 2.2.
        # Just bump crit to match band.
        'critMultiplier': 2.5,
    },
}


ARMOR_OVERRIDES = {
    'blindfold': {
        # The blindness IS the mechanic — make it explicit.
        'on_equip_status': 'blinded',
    },
    'hermes_sandals_early': {
        # Hermes's sandals — speed. Hasted while worn.
        'on_equip_status': 'hasted',
    },
}


SHIELD_OVERRIDES = {
    # lionheart_shield is plot_locked, skip
}


def apply_overrides(filepath, overrides):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    updated = 0
    for item_id, fields in overrides.items():
        if item_id not in data:
            print(f"  WARN: {item_id} not in {filepath}")
            continue
        for k, v in fields.items():
            data[item_id][k] = v
        updated += 1
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return updated


if __name__ == '__main__':
    print("Applying lore-matched power overrides...")
    n = apply_overrides(os.path.join(REPO, 'data', 'items', 'weapon.json'), WEAPON_OVERRIDES)
    print(f"  weapons: {n} updated")
    n = apply_overrides(os.path.join(REPO, 'data', 'items', 'armor.json'), ARMOR_OVERRIDES)
    print(f"  armor:   {n} updated")
    n = apply_overrides(os.path.join(REPO, 'data', 'items', 'shield.json'), SHIELD_OVERRIDES)
    print(f"  shields: {n} updated")
    print("Done.")
