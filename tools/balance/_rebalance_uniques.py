"""One-shot rebalance for unique weapons.

Redistributes the 92 named uniques in data/items/weapon.json so each
floor band has the right count and damage scales to the unified curve.

NOT a permanent tool — run once and commit the resulting JSON. Then this
file can be deleted (kept under tools/balance/ to record what was done).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import curve  # type: ignore

REPO = Path(__file__).resolve().parents[2]
WEAPON_JSON = REPO / "data" / "items" / "weapon.json"


def quiz_tier(peak_floor: int) -> int:
    return peak_floor // 20 + 1


def material_for_band(peak_floor: int) -> str | None:
    """Return canonical material for a given band; None = don't change."""
    if peak_floor < 20:
        return None  # keep existing — varied early materials
    if peak_floor < 40:
        return None  # keep existing
    if peak_floor < 60:
        return "legendary"
    return "adamantine"


def max_enchant_for_band(peak_floor: int) -> int:
    """Cap enchant by band; legendaries pre-F60 cap at 3-4."""
    if peak_floor < 20:
        return 3
    if peak_floor < 40:
        return 3
    if peak_floor < 60:
        return 4
    if peak_floor < 80:
        return 4
    return 5


def spread_for_band(peak_floor: int) -> int:
    if peak_floor < 30:
        return 8
    if peak_floor < 50:
        return 8
    return 12


def recalc_dmg(peak_floor: int, multiplier: float) -> int:
    """Compute the integer base damage = int(curve(peak) × multiplier)."""
    return max(1, int(curve.weapon_base_damage(peak_floor) * multiplier))


# ---------------------------------------------------------------------------
# Redistribution plan
# ---------------------------------------------------------------------------
# Each entry: key -> (new_peak_floor, damage_multiplier, optional adjustments)
# damage_multiplier: 1.4-1.55 workhorse, 1.6-1.7 strong, 1.7-1.85 signature
REDISTRIBUTIONS: dict[str, dict] = {
    # ----- DOWN-SHIFTS from F60-69 -----
    "labrys": {  # Minoan Bronze Age — F20s
        "peak_floor": 24,
        "mult": 1.65,  # signature Minoan religious axe
        "spread": 8,
        "material": "bronze",
    },
    "carnwennan": {  # Arthur's secondary dagger
        "peak_floor": 34,
        "mult": 1.7,  # signature dagger w/ shadow effect
        "spread": 8,
        "material": "enchanted iron",
        # already has onEquipStatus: invisible — that's fine for F30s tier (single-use utility)
    },
    "caliburn": {  # Pre-Excalibur stone-sword
        "peak_floor": 37,
        "mult": 1.7,
        "spread": 8,
        "material": "enchanted iron",
        # growingPower/killsToGrow stays (band-appropriate moderate effect)
    },
    "thyrsus": {  # Maenadic / Classical
        "peak_floor": 32,
        "mult": 1.5,  # staff, not a signature damage dealer
        "spread": 8,
        "material": "hardwood",
        # weaken confuseChance from 0.5 to 0.25 for F30 tier
        "weaken": {"confuseChance": 0.25},
    },
    "fragarach_the_whisperer": {  # Companion blade, assassin's tool
        "peak_floor": 38,
        "mult": 1.55,
        "spread": 8,
        "material": "legendary",
    },
    "sharur": {  # Sumerian, Bronze Age god war scout
        "peak_floor": 45,
        "mult": 1.55,
        "spread": 8,
        "material": "bronze",
        # confuseChance 0.25 is fine for F40s
    },
    "hrunting": {  # Beowulf's borrowed sword that failed
        "peak_floor": 52,
        "mult": 1.65,
        "spread": 12,
        "material": "legendary",
    },
    "naegling": {  # Beowulf's sword that shattered
        "peak_floor": 54,
        "mult": 1.55,  # not signature — it broke
        "spread": 12,
        "material": "legendary",
    },
    "ridill": {  # Fafnir's secondary, dwarf-forged
        "peak_floor": 55,
        "mult": 1.5,  # dagger, secondary
        "spread": 12,
        "material": "legendary",
    },
    "fail_not": {  # Tristan's fairy bow
        "peak_floor": 57,
        "mult": 1.65,  # signature bow w/ moral compass
        "spread": 12,
        "material": "legendary",
    },
    "kladenets": {  # Slavic self-swinger
        "peak_floor": 58,
        "mult": 1.7,  # signature — it fights on its own
        "spread": 12,
        "material": "legendary",
        # counterAttackChance 0.25 fits F50 tier
    },

    # ----- INTRA-F30/40 reshuffle -----
    "pelops_sword": {  # Move down to F30s — Tantalid lineage curse-sword
        "peak_floor": 36,
        "mult": 1.55,
        "spread": 7,
        "material": "legendary",
        # weaken: lifesteal_percent 0.08 too strong for F30 (band caps at NO lifesteal).
        # Drop lifesteal entirely; keep crit_multiplier but lower to 1.4; keep cursed_lineage flavor.
        "weaken": {"lifesteal_percent": 0, "crit_multiplier": 1.4},
    },

    # ----- UP-SHIFTS from F70-79 -----
    "ruyi_jingu_bang": {  # Sun Wukong cosmic staff
        "peak_floor": 82,
        "mult": 1.7,
        "spread": 12,
        "material": "divine iron",
    },
    "kusanagi": {  # Imperial regalia, god-blade
        "peak_floor": 83,
        "mult": 1.7,
        "spread": 12,
        "material": "adamantine",
    },
    "rod_of_moses": {  # Sea-parting divine staff
        "peak_floor": 84,
        "mult": 1.65,
        "spread": 12,
        "material": "adamantine",
        # poisonChance 0.3 -> bump status to band: serpent-strike works for F80s; keep 0.3
    },
    "trident_of_poseidon": {  # God-king of seas
        "peak_floor": 85,
        "mult": 1.7,
        "spread": 12,
        "material": "adamantine",
    },
    "gungnir": {  # Odin's never-miss spear
        "peak_floor": 86,
        "mult": 1.7,
        "spread": 12,
        "material": "adamantine",
    },
    "mjolnir": {  # Ragnarok-tier (boundary between F80 and F90)
        "peak_floor": 88,
        "mult": 1.8,
        "spread": 12,
        "material": "adamantine",
    },
    "sudarshana": {  # Vishnu's discus
        "peak_floor": 89,
        "mult": 1.7,
        "spread": 12,
        "material": "adamantine",
        # weaken burnChance from 0.2 to 0.25 (band-appropriate)
    },
    # ----- INTO F90-99 -----
    "mistilteinn": {  # Baldur-killer, the one weapon that can slay a god
        "peak_floor": 91,
        "mult": 1.7,
        "spread": 6,  # F90s use small spread
        "material": "legendary",
    },
    "chandrahasa": {  # Shiva's gift that grows more dangerous as wielder falls
        "peak_floor": 92,
        "mult": 1.7,
        "spread": 6,
        "material": "legendary",
        # already has low_hp_damage_bonus — band-appropriate
    },
    "laevateinn": {  # Loki's Ragnarok-trigger weapon
        "peak_floor": 93,
        "mult": 1.7,
        "spread": 6,
        "material": "legendary",
    },
}


def apply_redistribution(item: dict, peak: int, mult: float, spread: int,
                          material: str | None, weaken: dict | None = None) -> None:
    """Mutate a single weapon entry."""
    new_dmg = recalc_dmg(peak, mult)
    new_min = max(1, peak - spread)
    new_qt = quiz_tier(peak)
    new_tier = new_qt  # tier matches quiz_tier in the existing schema
    new_enchant = max_enchant_for_band(peak)

    item["peak_floor"] = peak
    item["min_level"] = new_min
    item["baseDamage"] = new_dmg
    item["base_damage"] = new_dmg
    item["mathTier"] = new_qt
    item["quiz_tier"] = new_qt
    item["tier"] = new_tier
    item["spread"] = spread
    item["max_enchant"] = new_enchant
    if material is not None:
        item["material"] = material

    # Clear stale floorSpawnWeight that was tuned for the old band.
    # An empty dict tells the spawn system to use the peak_floor curve.
    item["floorSpawnWeight"] = {}

    if weaken:
        for k, v in weaken.items():
            if v == 0:
                item.pop(k, None)
            else:
                item[k] = v

    # Stamp a curve note so future diffs are explainable.
    item["_curve_note"] = (
        f"Redistributed: peak={peak}, base={new_dmg} "
        f"(= curve.weapon_base_damage({peak}) x {mult}), "
        f"min_level={new_min}, quiz_tier={new_qt}."
    )


# ---------------------------------------------------------------------------
# New items to fill remaining gaps
# ---------------------------------------------------------------------------
def make_finesse_chains() -> list[float]:
    return [0.20, 0.55, 1.00, 1.80, 3.00]


def make_normal_chains() -> list[float]:
    return [0.50, 0.85, 1.00, 1.45, 2.00]


def make_heavy_chains() -> list[float]:
    return [0.75, 0.90, 1.00, 1.30, 1.75]


def new_unique(
    *,
    name: str,
    klass: str,
    weapon_class: str,
    variant: str,
    chain_class: str,  # 'finesse'/'normal'/'heavy'
    damage_types: list[str],
    color: list[int],
    weight: float,
    two_handed: bool,
    reach: int,
    peak_floor: int,
    spread: int,
    mult: float,
    template_basis: str,
    unidentified_name: str,
    lore: str,
    material: str = "legendary",
    extras: dict | None = None,
) -> dict:
    """Build a fresh unique-weapon entry matching the canonical schema."""
    chains_map = {
        "finesse": make_finesse_chains(),
        "normal": make_normal_chains(),
        "heavy": make_heavy_chains(),
    }
    chains = chains_map[chain_class]
    base_damage = recalc_dmg(peak_floor, mult)
    min_level = max(1, peak_floor - spread)
    qt = quiz_tier(peak_floor)
    tier = qt
    enchant = max_enchant_for_band(peak_floor)
    entry = {
        "name": name,
        "class": klass,
        "weapon_class": weapon_class,
        "variant": variant,
        "tier": tier,
        "material": material,
        "is_unique": True,
        "mathTier": qt,
        "quiz_tier": qt,
        "baseDamage": base_damage,
        "base_damage": base_damage,
        "chainMultipliers": chains,
        "chain_multipliers": chains,
        "maxChainLength": 5,
        "max_chain_length": 5,
        "weapon_class_chain": chain_class,
        "damageTypes": damage_types,
        "damage_types": damage_types,
        "symbol": ")",
        "color": color,
        "weight": weight,
        "twoHanded": two_handed,
        "two_handed": two_handed,
        "reach": reach,
        "stunChance": 0.0,
        "bleedChance": 0.0,
        "knockback": False,
        "ignoreShield": False,
        "critMultiplier": 1.5,
        "requiresAmmo": None,
        "floorSpawnWeight": {},
        "containerLootTier": "rare",
        "container_loot_tier": "rare",
        "value": base_damage * 60,
        "min_level": min_level,
        "peak_floor": peak_floor,
        "spread": spread,
        "peak_weight": 0.5,
        "max_enchant": enchant,
        "unidentified_name": unidentified_name,
        "identified": False,
        "lore": lore,
        "template_basis": template_basis,
        "_curve_note": (
            f"New item: peak={peak_floor}, base={base_damage} "
            f"(= curve.weapon_base_damage({peak_floor}) x {mult})."
        ),
    }
    if extras:
        entry.update(extras)
    return entry


# Four new F10-19 items — early myth and folk-tale weapons.
# Real cultural sources, geek-dad chronicle voice, short, grounded.
NEW_ITEMS: dict[str, dict] = {
    "cain_club": new_unique(
        name="Cain's Club",
        klass="club",
        weapon_class="club",
        variant="1h",
        chain_class="normal",
        damage_types=["blunt"],
        color=[140, 80, 60],
        weight=2.0,
        two_handed=False,
        reach=1,
        peak_floor=12,
        spread=8,
        mult=1.65,
        template_basis="club",
        unidentified_name="a crude root-end cudgel stained at the head",
        lore=(
            "The Bible does not say what Cain used. Talmudic and Quranic commentary "
            "settles on a rough club — the first murder weapon, made of nothing in "
            "particular. The mark on Cain protected him from retaliation but not from "
            "memory. The wood is the wrong colour at one end and no one has been able "
            "to wash it clean."
        ),
        material="hardwood",
        extras={"bleedChance": 0.1},
    ),
    "wepwawet_mace": new_unique(
        name="Mace of Wepwawet",
        klass="mace",
        weapon_class="mace",
        variant="1h",
        chain_class="normal",
        damage_types=["blunt"],
        color=[200, 180, 130],
        weight=2.5,
        two_handed=False,
        reach=1,
        peak_floor=14,
        spread=8,
        mult=1.6,
        template_basis="mace",
        unidentified_name="a slender ceremonial mace topped with a jackal",
        lore=(
            "Wepwawet — 'Opener of the Ways' — went before the army of Egypt as a "
            "standard-bearer. Older than Anubis and originally separate from him, the "
            "jackal-headed god carried the mace that broke the line. Predynastic mace "
            "heads survive in museum cases. They are heavier than they look."
        ),
        material="bronze",
        extras={"stunChance": 0.15},
    ),
    "cuchulainn_hurley": new_unique(
        name="Setanta's Hurley",
        klass="club",
        weapon_class="club",
        variant="1h",
        chain_class="normal",
        damage_types=["blunt"],
        color=[160, 130, 90],
        weight=1.5,
        two_handed=False,
        reach=1,
        peak_floor=16,
        spread=8,
        mult=1.55,
        template_basis="club",
        unidentified_name="a worn ash hurling stick with a stone-hard heel",
        lore=(
            "Before he was Cu Chulainn — Culann's Hound — he was Setanta, the boy who "
            "killed Culann's guard dog by driving a hurling ball down its throat with "
            "this stick. He volunteered to replace the dog. The name stuck. The hurley "
            "is ash and the heel is dense as river stone."
        ),
        material="hardwood",
    ),
    "mwindo_axe": new_unique(
        name="Mwindo's Conga-Scepter",
        klass="axe",
        weapon_class="axe",
        variant="1h",
        chain_class="normal",
        damage_types=["slash"],
        color=[150, 110, 70],
        weight=2.0,
        two_handed=False,
        reach=1,
        peak_floor=18,
        spread=8,
        mult=1.65,
        template_basis="handaxe",
        unidentified_name="a small carved axe-scepter inlaid with cowrie shells",
        lore=(
            "The Mwindo Epic — collected from the Banyanga of the eastern Congo in the "
            "1950s — gives its hero a conga-scepter that did the work of an axe, a "
            "magic wand, and a flyswatter. Born speaking, born walking, born with this "
            "in his hand. He used it to bring his uncles back from the dead, and once "
            "to kill a dragon."
        ),
        material="hardwood",
        extras={"bleedChance": 0.1},
    ),
}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def main() -> None:
    with WEAPON_JSON.open(encoding="utf-8") as f:
        weapons = json.load(f)

    # Apply redistributions
    for key, plan in REDISTRIBUTIONS.items():
        if key not in weapons:
            raise RuntimeError(f"Missing key in weapon.json: {key}")
        apply_redistribution(
            weapons[key],
            peak=plan["peak_floor"],
            mult=plan["mult"],
            spread=plan["spread"],
            material=plan.get("material"),
            weaken=plan.get("weaken"),
        )
        print(f"Redistributed {key}: peak={plan['peak_floor']} mult={plan['mult']}")

    # Add new items — make sure no key collisions
    for key, entry in NEW_ITEMS.items():
        if key in weapons:
            raise RuntimeError(f"New key collides with existing: {key}")
        weapons[key] = entry
        print(f"Added new unique: {key} peak={entry['peak_floor']} base={entry['baseDamage']}")

    # Write back
    with WEAPON_JSON.open("w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Wrote {WEAPON_JSON}")


if __name__ == "__main__":
    main()
