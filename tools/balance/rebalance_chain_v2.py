"""
Chain Rebalance v2 — midpoint-anchored 3-class model.

Rewrites all 22 weapon templates and 96 unique weapons to use the new
chain shape system:

  Finesse: [0.20, 0.55, 1.00, 1.80, 3.00]  — slow ramp, big spike
  Normal:  [0.50, 0.85, 1.00, 1.45, 2.00]  — flat workhorse
  Heavy:   [0.75, 0.90, 1.00, 1.30, 1.75]  — front-loaded, max triggers SPECIAL

For non-5-rung chains, the shape preserves the "midpoint at 1.0×" principle.

This script reads existing templates/uniques to preserve all OTHER fields,
overwriting only `chain_multipliers`, `max_chain_length`, `base_damage`
(for uniques), and adding `weapon_class_chain` + `class_mechanic` fields.

Run:  py tools/balance/rebalance_chain_v2.py
"""

from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import curve  # noqa: E402

TEMPLATES_DIR = os.path.join(HERE, "generated", "templates", "weapons")
UNIQUES_DIR = os.path.join(HERE, "generated", "uniques", "weapons")

# ---------------------------------------------------------------------------
# Chain shape table — keyed by (class, rung_count)
# ---------------------------------------------------------------------------

CHAIN_SHAPES: dict[tuple[str, int], list[float]] = {
    # --- Finesse ---
    ("finesse", 3): [0.40, 1.00, 2.40],
    ("finesse", 4): [0.30, 0.80, 1.80, 3.00],
    ("finesse", 5): [0.20, 0.55, 1.00, 1.80, 3.00],
    ("finesse", 6): [0.20, 0.45, 0.75, 1.20, 2.00, 3.00],
    ("finesse", 7): [0.18, 0.40, 0.65, 1.00, 1.50, 2.20, 3.20],
    ("finesse", 8): [0.18, 0.35, 0.55, 0.80, 1.20, 1.75, 2.50, 3.30],
    # --- Normal ---
    ("normal", 3): [0.65, 1.00, 2.00],
    ("normal", 4): [0.55, 0.95, 1.40, 2.00],
    ("normal", 5): [0.50, 0.85, 1.00, 1.45, 2.00],
    ("normal", 6): [0.40, 0.70, 1.00, 1.30, 1.65, 2.00],
    ("normal", 7): [0.40, 0.65, 0.85, 1.10, 1.40, 1.70, 2.10],
    ("normal", 8): [0.35, 0.55, 0.75, 1.00, 1.25, 1.50, 1.80, 2.20],
    # --- Heavy ---
    ("heavy", 3): [0.85, 1.00, 1.50],
    ("heavy", 4): [0.85, 1.00, 1.30, 1.75],
    ("heavy", 5): [0.75, 0.90, 1.00, 1.30, 1.75],
    ("heavy", 6): [0.70, 0.85, 1.00, 1.15, 1.40, 1.75],
    ("heavy", 7): [0.65, 0.80, 0.95, 1.10, 1.25, 1.50, 1.85],
    ("heavy", 8): [0.60, 0.75, 0.85, 1.00, 1.15, 1.35, 1.55, 1.90],
}


def chain_shape(weapon_class: str, n_rungs: int) -> list[float]:
    """Return chain multipliers list for the given class + rung count."""
    key = (weapon_class, n_rungs)
    if key in CHAIN_SHAPES:
        return list(CHAIN_SHAPES[key])
    # Fallback: clamp to nearest known length
    n_rungs = max(3, min(8, n_rungs))
    return list(CHAIN_SHAPES[(weapon_class, n_rungs)])


# ---------------------------------------------------------------------------
# Template class assignments (per user spec)
# ---------------------------------------------------------------------------

TEMPLATE_CLASSES: dict[str, dict] = {
    # FINESSE — duelist's reward, big spike at max
    "dagger": {
        "class": "finesse",
        "rungs": 4,
        "mechanic": "backstab",
        "mechanic_desc": "Backstab: ×2 damage if the target is unaware of you.",
    },
    "rapier": {
        "class": "finesse",
        "rungs": 6,
        "mechanic": "finesse_dex",
        "mechanic_desc": "Finesse: uses DEX instead of STR for damage bonus.",
    },
    "scimitar": {
        "class": "finesse",
        "rungs": 6,
        "mechanic": "disarm_at_max",
        "mechanic_desc": "At max chain, 30% chance to disarm the target.",
    },
    "shortbow": {
        "class": "finesse",
        "rungs": 5,
        "mechanic": "ranged_precision",
        "mechanic_desc": "Ranged precision: critical hits on natural 19-20.",
    },
    "sling": {
        "class": "finesse",
        "rungs": 5,
        "mechanic": "cheap_ammo",
        "mechanic_desc": "Cheap ammo: sling stones are 0.1 lb and abundant.",
    },
    # NORMAL — flat workhorse, modest spike
    "shortsword": {
        "class": "normal",
        "rungs": 5,
        "mechanic": "clean",
        "mechanic_desc": "Clean: no special. The legionary's workhorse.",
    },
    "longsword": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "reach_1",
        "mechanic_desc": "Reach 1: can strike diagonally adjacent foes with full effect.",
    },
    "mace": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "stun_on_chain3",
        "mechanic_desc": "On chain rung 3+, 20% chance to stun for 1 turn.",
    },
    "warhammer": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "stun_plus_anti_heavy",
        "mechanic_desc": "On chain rung 3+, 20% chance to stun. +25% damage vs heavy armor.",
    },
    "battleaxe": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "bleed_on_chain3",
        "mechanic_desc": "On chain rung 3+, applies bleed (1d4/turn for 3 turns).",
    },
    "flail": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "ignores_shield",
        "mechanic_desc": "Ignores shield AC bonus — flail wraps around defenses.",
    },
    "club": {
        "class": "normal",
        "rungs": 5,
        "mechanic": "primitive",
        "mechanic_desc": "Primitive: cheap and abundant — never breaks on harvest tools.",
    },
    "bastard_sword": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "versatile",
        "mechanic_desc": "Versatile: +20% damage when wielded two-handed (no shield).",
    },
    "quarterstaff": {
        "class": "normal",
        "rungs": 6,
        "mechanic": "reach_disarm",
        "mechanic_desc": "Reach 1; on chain rung 4+, 15% chance to disarm.",
    },
    "longbow": {
        "class": "normal",
        "rungs": 5,
        "mechanic": "range_8",
        "mechanic_desc": "Range 8 tiles. STR ≥ 13 recommended for full draw.",
    },
    "composite_bow": {
        "class": "normal",
        "rungs": 5,
        "mechanic": "str_bonus_range_7",
        "mechanic_desc": "Range 7 tiles. +STR modifier added to damage (composite limb power).",
    },
    # HEAVY — front-loaded, max triggers SPECIAL (this IS the reward)
    "greatsword": {
        "class": "heavy",
        "rungs": 5,
        "mechanic": "cleave_on_kill",
        "mechanic_desc": "At max chain, on kill: cleave damage to one adjacent foe.",
    },
    "maul": {
        "class": "heavy",
        "rungs": 5,
        "mechanic": "stun_knockdown_at_max",
        "mechanic_desc": "At chain rung 4+, stun + knockdown (target loses 2 turns).",
    },
    "great_axe": {
        "class": "heavy",
        "rungs": 5,
        "mechanic": "cleave_plus_bleed",
        "mechanic_desc": "At max chain: cleave one adjacent foe + apply bleed (1d6/turn for 3).",
    },
    "glaive": {
        "class": "heavy",
        "rungs": 5,
        "mechanic": "reach_2",
        "mechanic_desc": "Reach 2: can strike foes 2 tiles away. At max chain, hits all in line.",
    },
    "light_crossbow": {
        "class": "heavy",
        "rungs": 4,
        "mechanic": "ignores_half_armor",
        "mechanic_desc": "Ignores half of target armor AC. Single-shot reload between volleys.",
    },
    "heavy_crossbow": {
        "class": "heavy",
        "rungs": 3,
        "mechanic": "ignores_all_armor",
        "mechanic_desc": "Ignores ALL armor AC. Single-shot reload. Speed 6 (slowest).",
    },
}


# ---------------------------------------------------------------------------
# Update templates
# ---------------------------------------------------------------------------

def update_templates() -> int:
    """Rewrite all weapon templates with new chain shapes + class metadata."""
    count = 0
    for tmpl_id, info in TEMPLATE_CLASSES.items():
        path = os.path.join(TEMPLATES_DIR, f"{tmpl_id}.json")
        if not os.path.exists(path):
            print(f"  MISSING: {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cls = info["class"]
        rungs = info["rungs"]
        shape = chain_shape(cls, rungs)
        data["chain_multipliers"] = shape
        data["max_chain_length"] = rungs
        data["weapon_class_chain"] = cls
        data["class_mechanic"] = info["mechanic"]
        data["class_mechanic_desc"] = info["mechanic_desc"]
        # Refresh design_notes with v2 stamp
        peak = shape[-1]
        mid_idx = (rungs - 1) // 2  # midpoint rung (0-indexed)
        mid = shape[mid_idx]
        data["design_notes"] = (
            f"v2 chain rebalance: {cls} class, {rungs} rungs. "
            f"Midpoint rung {mid_idx + 1} = {mid:.2f}× (1.0× anchor band). "
            f"Peak rung {rungs} = {peak:.2f}×. "
            f"Class mechanic: {info['mechanic_desc']} "
            f"(see weapon_class_chain + class_mechanic fields). "
            f"damage_modifier {data.get('damage_modifier', 1.0)} preserved from v1; "
            f"weapon_base_damage now anchored on curve.weapon_base_damage(min_level) "
            f"(2.4× higher than v1 due to midpoint=1.0× re-anchor)."
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        count += 1
        print(f"  template: {tmpl_id} -> {cls} {rungs}-rung peak={peak:.2f}")
    return count


# ---------------------------------------------------------------------------
# Update uniques
# ---------------------------------------------------------------------------

# Map template_basis -> (class, default_rungs).
# Includes aliases for legacy basis names that pre-date the 22-template lineup.
TEMPLATE_CLASS_LOOKUP: dict[str, str] = {tid: info["class"] for tid, info in TEMPLATE_CLASSES.items()}
# Legacy aliases — uniques whose template_basis names a weapon-type
# that isn't one of the 22 canonical templates. Resolved to the closest match.
LEGACY_BASIS_ALIASES: dict[str, str] = {
    "spear":       "glaive",         # spears get polearm Heavy treatment
    "net":         "glaive",         # Net of Hephaestus — polearm-ish
    "crossbow":    "light_crossbow", # generic crossbow -> light
    "unarmed":     "dagger",         # Punch in the Face — finesse fists
    "morningstar": "flail",          # morningstar -> normal flail
}
for alias, target in LEGACY_BASIS_ALIASES.items():
    TEMPLATE_CLASS_LOOKUP[alias] = TEMPLATE_CLASS_LOOKUP[target]

# Default rungs per template — for uniques that didn't specify their own.
TEMPLATE_DEFAULT_RUNGS: dict[str, int] = {tid: info["rungs"] for tid, info in TEMPLATE_CLASSES.items()}
for alias, target in LEGACY_BASIS_ALIASES.items():
    TEMPLATE_DEFAULT_RUNGS[alias] = TEMPLATE_DEFAULT_RUNGS[target]

# Unique mult by name — most are 1.5× (legendary), some 1.7× (boss-tier),
# some 2.0× (capstone / quest reward).
UNIQUE_MULT_DEFAULT = 1.2  # was 1.5 in v1; new curve weapon_base is 2.4× larger,
                           # so a 1.2× unique already feels legendary on the new scale

# Capstone-tier uniques — boss rewards & quest-locked divine artifacts.
# Tuned to 1.5× (NOT 2.0× — the 2.0× tested too high; +crit + special mechanics
# already deliver the "I am a capstone" feel without doubling base damage).
# The Abaddon-killers (Sword of Michael, etc.) have explicit per-unique overrides below.
CAPSTONE_UNIQUES = {
    "gram",                  # reforged Gram, Fenrir-tier quest
    "excalibur",             # mythic capstone
    "mjolnir",               # Thor's hammer
    "gungnir",               # Odin's spear
    "kusanagi",              # Susano's blade
    "trident_of_poseidon",   # divine
    "spear_of_longinus",     # divine
    "ruyi_jingu_bang",       # Sun Wukong
    "sudarshana",            # Vishnu's chakra
    "vel_of_murugan",        # divine
    "amenonuhoko",           # primordial Japanese
    "rod_of_moses",          # divine
    "staff_of_moses",        # divine
    "spear_of_lugh",         # divine Celtic
    "chrysaor",              # golden sword from Medusa's blood
    "bow_of_rama",           # divine Hindu
    "chandrahas",            # Ravana's divine blade
    "chandrahasa",           # variant spelling
    "gandiva",               # Arjuna's bow (divine)
    "khopesh_of_anubis",     # divine Egyptian
    "vulcans_brand",         # forged by Hephaestus
}

# Per-unique explicit damage multipliers (overrides default tier).
# Used for the few quest-locked superweapons that need precise tuning
# vs the boss they're designed to kill.
UNIQUE_MULT_OVERRIDES: dict[str, float] = {
    # Sword of Michael: kills Abaddon (1235 HP) at max-stack (247 HP) in ~3 turns
    # at chain peak (no crit). Base 29 × 1.3 = 38; chain peak Normal 2.0× = 76
    # + abaddon_bonus 11 = 87. 247/87 = 2.8 turns. ✓ design target 3-5 turns.
    "sword_of_michael": 1.3,
}

# Boss-tier uniques (1.7× mult) — strong but not capstones
BOSS_TIER_UNIQUES = {
    "hrunting", "naegling", "skofnung", "tyrfing", "caladbolg",
    "fragarach", "fragarach_the_whisperer", "joyeuse", "durendal",
    "dawnbreaker", "soul_reaver", "zulfiqar", "harpe", "gae_bulg",
    "carnwennan", "curtana", "labrys", "mistilteinn", "parashu",
    "katana", "naginata", "claymore", "flamberge", "executioners_sword",
    "shamshir_e_zomorrodnegar", "fail_not", "achilles_spear",
    "zireael", "oathkeeper_sword", "witcher_silver_blade",
    "kladenets", "ridill", "brisingr", "sharur",
    "cronus_scythe", "gae_dearg", "laevateinn", "thyrsus",
    "robin_hoods_longbow", "sling_of_david", "prometheus_torch",
    "green_chapel_axe", "hunt_captains_sword", "wendigo_fang",
    "echidna_fang", "sword_of_damocles", "caliburn",
    "gae_bolg_fragment", "mjolnir_shard", "broken_gram",
    "pharaohs_crook", "romulus_spear", "sigurds_shovel",
    "penitents_blade", "net_of_hephaestus",
}


def unique_mult_for(uid: str) -> float:
    """Damage multiplier above weapon_base_damage(min_level) for this unique."""
    if uid in UNIQUE_MULT_OVERRIDES:
        return UNIQUE_MULT_OVERRIDES[uid]
    if uid in CAPSTONE_UNIQUES:
        return 1.6   # was 2.0 in v1; lowered to preserve "no one-shot" math
    if uid in BOSS_TIER_UNIQUES:
        return 1.4   # was 1.7; lowered similarly
    return UNIQUE_MULT_DEFAULT  # 1.2


def update_uniques() -> tuple[int, list[str]]:
    """Rewrite all unique weapons with new chain shapes + recomputed base_damage."""
    count = 0
    skipped = []
    for fname in sorted(os.listdir(UNIQUES_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(UNIQUES_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        uid = data.get("id") or fname[:-5]
        basis = data.get("template_basis")
        if basis not in TEMPLATE_CLASS_LOOKUP:
            skipped.append(f"{uid}: template_basis={basis!r} not in lookup")
            continue
        cls = TEMPLATE_CLASS_LOOKUP[basis]
        # Preserve unique's max_chain_length if it differs from template
        # (some uniques have +1 or +2 extra rungs as a "legendary feel" bonus)
        default_rungs = TEMPLATE_DEFAULT_RUNGS.get(basis, 5)
        rungs = data.get("max_chain_length", default_rungs)
        rungs = max(3, min(8, int(rungs)))
        shape = chain_shape(cls, rungs)
        data["chain_multipliers"] = shape
        data["max_chain_length"] = rungs
        data["weapon_class_chain"] = cls

        # Recompute base_damage from new curve
        # Use min_level if real, else tier_intended (for plot-locked uniques)
        min_level = data.get("min_level", 1)
        if min_level >= 9999:
            min_level = data.get("tier_intended", 100)
        # peak_floor==0 + plot_locked -> use tier_intended
        if data.get("peak_floor", -1) == 0 and "tier_intended" in data:
            min_level = data["tier_intended"]
        min_level = max(1, min(100, int(min_level)))

        base_curve = curve.weapon_base_damage(min_level)
        mult = unique_mult_for(uid)
        new_base = max(1, round(base_curve * mult))
        data["base_damage"] = new_base
        data["curve_note"] = (
            f"v2: base_damage = curve.weapon_base_damage({min_level}) × "
            f"{mult:.2f} unique-mult = {new_base}. Class: {cls} {rungs}-rung "
            f"(midpoint=1.0×, peak={shape[-1]:.2f}×)."
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        count += 1
    return count, skipped


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("CHAIN REBALANCE v2 — midpoint-anchored 3-class model")
    print("=" * 70)
    print()
    print("Updating weapon templates...")
    t = update_templates()
    print(f"  -> {t} templates updated")
    print()
    print("Updating unique weapons...")
    u, skipped = update_uniques()
    print(f"  -> {u} uniques updated")
    if skipped:
        print(f"  -> {len(skipped)} skipped:")
        for s in skipped:
            print(f"     {s}")
    print()
    print("Done.")
