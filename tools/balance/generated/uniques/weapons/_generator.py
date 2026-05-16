"""Generator C — Unique/Named Weapons rebalance against the unified curve.

Reads from data/items/weapon.json (style + lore + special properties only),
re-derives all NUMBERS from tools/balance/curve.py.

Hard rules (per GENERATORS_BRIEFING.md §9):
- All damage numbers derive from curve.weapon_base_damage(min_level) or boss-floor anchor.
- Unique feel = 1.3-2.0× over template+material baseline; quest weapons 2.0-3.0×.
- Chain shape AD&D-compressed: peak chain mult 6-9× (not 16×).
- Story-locked min_level=9999 weapons get a `tier_intended` field pointing at
  the boss floor whose fight they're meant to swing.
- Realistic weights per §4 of the briefing.
- peak_floor + spread replace min_level/max_level (with `min_level` retained
  as the first floor the bell weight crosses ~0.05).

Run:  py tools/balance/generated/uniques/weapons/_generator.py
"""

from __future__ import annotations
import json
import math
import sys
from pathlib import Path

# Path manipulation so we can import curve.py
# This file lives at tools/balance/generated/uniques/weapons/_generator.py
# So parents: [0]=weapons, [1]=uniques, [2]=generated, [3]=balance
BALANCE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BALANCE_DIR))
import curve  # type: ignore  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chain_shape_compressed(max_len: int, peak_mult: float) -> list[float]:
    """Build an AD&D-compressed chain-multiplier table.

    - rung 1 is a 'chained' opener at ~0.4-0.5 of base (so chain-1 < normal hit)
    - rung floor(max_len/2) (~middle) is ~1.0-1.5 (par)
    - rung max_len is `peak_mult` (the 'unique payoff')
    Growth is geometric so the curve feels smooth, not stepped.
    """
    if max_len < 1:
        max_len = 1
    if max_len == 1:
        return [peak_mult]
    start = 0.5
    # Geometric progression from `start` to `peak_mult` across max_len rungs.
    growth = (peak_mult / start) ** (1.0 / (max_len - 1))
    rungs = []
    cur = start
    for i in range(max_len):
        rungs.append(round(cur, 2))
        cur *= growth
    # Replace last to ensure exact match
    rungs[-1] = peak_mult
    return rungs


def chain_shape_dagger(max_len: int, peak_mult: float) -> list[float]:
    """Dagger profile: low opener, big back-half — rewards patient chaining."""
    if max_len < 1:
        max_len = 1
    if max_len == 1:
        return [peak_mult]
    # Daggers ramp slowly then spike — geometric with a lower start.
    start = 0.3
    growth = (peak_mult / start) ** (1.0 / (max_len - 1))
    rungs = [round(start * growth ** i, 2) for i in range(max_len)]
    rungs[-1] = peak_mult
    return rungs


def chain_shape_axe(max_len: int, peak_mult: float) -> list[float]:
    """Axe profile: heavy front-load — most damage early, plateaus late."""
    if max_len < 1:
        max_len = 1
    if max_len == 1:
        return [peak_mult]
    start = 0.9
    growth = (peak_mult / start) ** (1.0 / (max_len - 1))
    rungs = [round(start * growth ** i, 2) for i in range(max_len)]
    rungs[-1] = peak_mult
    return rungs


def spread_from_minlevel(min_level: int) -> tuple[int, int, int]:
    """Default peak_floor/spread/peak_weight for a unique with the given min_level.

    Returns (peak_floor, spread, peak_weight). Uniques peak ~10 floors past
    their min_level (the band where they're 'expected gear'). spread = 10-15
    so they have a long tail.
    """
    peak = min_level + 10
    spread = 12 if min_level >= 40 else 8
    # Most uniques cap at peak_weight 0.5 — they're rare. Story-locked = 0.
    peak_weight = 0.5
    return peak, spread, peak_weight


def base_damage(min_level: int, unique_mult: float = 1.5) -> int:
    """curve.weapon_base_damage(min_level) × unique multiplier."""
    base = curve.weapon_base_damage(min_level)
    return max(1, int(round(base * unique_mult)))


def quest_weapon_base_damage(boss_floor: int, quest_mult: float = 2.5) -> int:
    """For boss-quest weapons: anchor to the boss floor, apply quest multiplier."""
    base = curve.weapon_base_damage(boss_floor)
    return max(1, int(round(base * quest_mult)))


# ---------------------------------------------------------------------------
# Schema builder
# ---------------------------------------------------------------------------

def unique(
    id_: str,
    name: str,
    weapon_class: str,
    template_basis: str,
    hands: int,
    damage_types: list[str],
    weight_lb: float,
    min_level: int,
    unique_mult: float = 1.5,
    chain_profile: str = "normal",  # "normal", "dagger", "axe"
    max_chain: int = 7,
    peak_chain_mult: float = 6.0,
    max_enchant: int = 3,
    special_properties: dict | None = None,
    lore: str = "",
    spawn_method: str = "rare_drop",
    tier_intended: int | None = None,
    base_damage_override: int | None = None,
    peak_floor: int | None = None,
    spread: int | None = None,
    peak_weight: float | None = None,
    curve_note: str | None = None,
) -> dict:
    """Build a unique-weapon JSON record.

    `tier_intended` is the boss floor used for damage anchoring when min_level=9999.
    """
    if min_level == 9999 and tier_intended is None:
        raise ValueError(f"{id_}: story-locked weapon needs tier_intended")

    anchor_floor = tier_intended if min_level == 9999 else min_level

    if base_damage_override is not None:
        bd = base_damage_override
    elif min_level == 9999 and spawn_method == "quest_reward":
        bd = quest_weapon_base_damage(tier_intended, quest_mult=unique_mult)
    else:
        bd = base_damage(anchor_floor, unique_mult)

    # Chain shape
    if chain_profile == "dagger":
        chain = chain_shape_dagger(max_chain, peak_chain_mult)
    elif chain_profile == "axe":
        chain = chain_shape_axe(max_chain, peak_chain_mult)
    else:
        chain = chain_shape_compressed(max_chain, peak_chain_mult)

    # Spawn (peak_floor / spread / peak_weight) — replaces min/max_level pair
    if min_level == 9999:
        pf = sp = pw = 0
    else:
        if peak_floor is None or spread is None or peak_weight is None:
            pf, sp, pw = spread_from_minlevel(min_level)
        else:
            pf, sp, pw = peak_floor, spread, peak_weight

    out = {
        "id": id_,
        "name": name,
        "category": "weapon",
        "weapon_class": weapon_class,
        "template_basis": template_basis,
        "is_unique": True,
        "hands": hands,
        "damage_types": damage_types,
        "base_damage": bd,
        "chain_multipliers": chain,
        "max_chain_length": max_chain,
        "weight_lb": weight_lb,
        "min_level": min_level,
        "peak_floor": pf,
        "spread": sp,
        "peak_weight": pw,
        "max_enchant": max_enchant,
        "spawn_method": spawn_method,
        "special_properties": special_properties or {},
        "lore": lore,
        "curve_note": curve_note or (
            f"base_damage = curve.weapon_base_damage({anchor_floor}) "
            f"× {unique_mult:.2f} unique-mult = {bd}"
        ),
    }
    if min_level == 9999:
        out["tier_intended"] = tier_intended
    return out


# ---------------------------------------------------------------------------
# Sword of Michael — special case calculation
# ---------------------------------------------------------------------------

def sword_of_michael() -> dict:
    """Sword of Michael nerf per the brief.

    Target: best weapon in the game, but should NOT one-shot Abaddon.
    Abaddon naive HP at F100 = curve.boss_hp_naive(100) = 1235.
    Sword max-chain-with-crit should land 250-300 dmg per hit
    (so 4-5 hits to kill naive Abaddon).

    Formula audit (combat.py): final = (base × chain_mult × material × enchant
    × crit_mult × damage_type_mult) + abaddon_bonus_dice.
    Holy weakness = 1.5× (Abaddon weak: holy).
    ignore_resistances = TRUE (bypasses Abaddon's resist suite).

    Worked example for target 250-300 per hit at max chain+crit:
      base 20 × chain 7.0 × 1.5 (holy weakness) × 2.5 (crit) = 525.
      Without crit: 20 × 7.0 × 1.5 = 210.
      With abaddon_bonus 2d10 (avg 11): ~221-236 per hit non-crit; ~536 crit.
    Hmm, that's 250+ non-crit and 500+ crit, which 1-shots are out but a crit
    chain ends the fight fast. Let's target lower:
      base 18, chain max 6.0, crit 2.0, abaddon_bonus 2d10.
      Non-crit chain-max: 18 × 6.0 × 1.5 + 11 = 173.
      Crit chain-max: 18 × 6.0 × 1.5 × 2.0 + 11 = 335.
    Kills Abaddon in 4-6 hits with crit chains, 7-8 without crits. Good.
    """
    # Compute base from curve at F100 with a 2.5× multiplier (quest-weapon scale)
    bd = quest_weapon_base_damage(100, quest_mult=2.5)
    # curve.weapon_base_damage(100) = 23; × 2.5 = ~58. Too high for non-1-shot.
    # Override down so max-chain+crit lands ~250-330.
    bd = 18

    chain = [0.5, 1.0, 1.5, 2.2, 3.0, 4.2, 6.0]  # max chain length 7
    return {
        "id": "sword_of_michael",
        "name": "Sword of Michael",
        "category": "weapon",
        "weapon_class": "sword",
        "template_basis": "longsword",
        "is_unique": True,
        "hands": 1,
        "damage_types": ["holy", "slash"],
        "base_damage": bd,
        "chain_multipliers": chain,
        "max_chain_length": 7,
        "weight_lb": 2.5,
        "min_level": 9999,
        "tier_intended": 100,
        "peak_floor": 0,
        "spread": 0,
        "peak_weight": 0,
        "max_enchant": 5,
        "spawn_method": "quest_reward",
        "special_properties": {
            "ignore_resistances": True,
            "ignore_shield": True,
            "abaddon_bonus_damage": "2d10",
            "crit_multiplier": 2.0,
            "crit_chance_bonus": 0.10,
        },
        "lore": (
            "The flaming sword of the Archangel Michael, Prince of the Heavenly Host. "
            "With this blade he cast Lucifer from Heaven and shall wield it again at the "
            "end of days. No armor, no enchantment, no infernal resistance can turn its "
            "edge. Against the Destroyer, it blazes with the full wrath of Heaven. It is "
            "the reward of the righteous — earned not by strength but by the quality of "
            "one's soul."
        ),
        "curve_note": (
            "ABADDON KILL MATH (curve.py + combat.py): base 18 × max_chain 6.0 × "
            "1.5 holy_weak = 162. With +crit_mult 2.0 = 324. + abaddon_bonus 2d10 "
            "(avg 11) = ~173 non-crit / ~335 crit. "
            "Abaddon naive HP = curve.boss_hp_naive(100) = 1235. "
            "Result: 4-7 hits to kill, conservative crit-chain assumption. "
            "Does NOT one-shot Abaddon. Sword is the best weapon (ignore_resistances "
            "+ holy + ignore_shield + abaddon_bonus) but the fight is real."
        ),
    }


# ---------------------------------------------------------------------------
# The full roster (~94 unique weapons, derived from data/items/weapon.json)
# ---------------------------------------------------------------------------

WEAPONS: list[dict] = [
    # -- T1/F1-20 historical sidearms (small one-handers, named-historical) --
    unique("gladius", "gladius", "sword", "shortsword", 1, ["slash", "pierce"],
           weight_lb=2.0, min_level=3, unique_mult=1.4, max_chain=6, peak_chain_mult=5.0,
           spawn_method="rare_drop", max_enchant=2,
           special_properties={"formation_bonus": True},
           lore="The gladius Hispaniensis — Roman legionary sidearm. Its leaf-shaped 50-60cm blade excelled in close formation fighting. It won an empire."),
    unique("pugio", "pugio", "dagger", "dagger", 1, ["pierce", "slash"],
           weight_lb=1.0, min_level=2, unique_mult=1.4, max_chain=7, peak_chain_mult=5.5,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=2,
           special_properties={"backstab_bonus": 1.3},
           lore="Personal sidearm of the Roman legions. Julius Caesar was allegedly stabbed with a pugio — or many of them."),
    unique("kopis", "kopis", "scimitar", "scimitar", 1, ["slash"],
           weight_lb=3.0, min_level=3, unique_mult=1.4, max_chain=6, peak_chain_mult=5.0,
           spawn_method="rare_drop", max_enchant=2,
           special_properties={"cavalry_bonus": 1.2},
           lore="Forward-curving blade of Greek and Persian cavalry. Alexander's Macedonians carried these alongside their sarissas."),
    unique("francisca", "francisca", "axe", "battleaxe", 1, ["slash"],
           weight_lb=4.0, min_level=3, unique_mult=1.4, max_chain=5, peak_chain_mult=4.5,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=2,
           special_properties={"knockback": True, "throwable": True},
           lore="Frankish throwing axe (5th-8th c.). Caromed unpredictably along the ground to knock down shields before the charge."),
    unique("sica", "sica", "dagger", "dagger", 1, ["slash", "pierce"],
           weight_lb=1.0, min_level=3, unique_mult=1.4, max_chain=7, peak_chain_mult=5.5,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=2,
           special_properties={"bleed_chance": 0.25},
           lore="Dacian and gladiator weapon. Roman writers noted that sica wounds had an unusual tendency to reopen."),

    # -- T2/F20-40 historical mid-tier --
    unique("falchion", "falchion", "sword", "longsword", 1, ["slash"],
           weight_lb=3.0, min_level=22, unique_mult=1.5, max_chain=7, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"crit_multiplier": 1.4},
           lore="Common soldier's blade. Wider than a longsword, brutal against lightly armored opponents."),
    unique("cinquedea", "cinquedea", "dagger", "dagger", 1, ["slash", "pierce"],
           weight_lb=1.5, min_level=22, unique_mult=1.5, max_chain=7, peak_chain_mult=6.0,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=3,
           special_properties={"crit_multiplier": 1.4},
           lore="'Five fingers' wide at the ricasso. Renaissance Italian status weapon — wealthy 15th-century Ferrarans wore these as statements of intent."),
    unique("estoc", "estoc", "sword", "longsword", 1, ["pierce"],
           weight_lb=2.5, min_level=22, unique_mult=1.5, max_chain=7, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"ignore_shield": True, "armor_pierce": True},
           lore="Stiff, unsharpened blade designed to bypass plate armor by driving through mail rings and joint gaps."),
    unique("kukri", "kukri", "dagger", "dagger", 1, ["slash"],
           weight_lb=1.0, min_level=22, unique_mult=1.5, max_chain=7, peak_chain_mult=6.0,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=3,
           special_properties={"bleed_chance": 0.30},
           lore="National weapon of Nepal. The Gurkha saying: 'Never draw it without drawing blood.'"),
    unique("war_scythe", "war scythe", "polearm", "glaive", 2, ["slash", "pierce"],
           weight_lb=7.0, min_level=22, unique_mult=1.5, max_chain=6, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 2, "anti_cavalry": True},
           lore="Weapon of desperate men — peasant armies in the Hussite Wars and Polish uprisings."),
    unique("bastard_sword", "bastard sword", "sword", "bastard_sword", 2, ["slash", "pierce"],
           weight_lb=5.0, min_level=22, unique_mult=1.5, max_chain=7, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"versatile": True},
           lore="Hand-and-a-half sword: one-handed from horseback, two-handed on foot. Bridges longsword and greatsword."),

    # -- T3/F40-60 named mid-game --
    unique("katana", "katana", "sword", "longsword", 1, ["slash"],
           weight_lb=2.5, min_level=42, unique_mult=1.6, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.5, "bleed_chance": 0.15},
           lore="Differential hardening produces a hard edge and tough back. A clean katana cut sometimes isn't felt until seconds later."),
    unique("dao", "dao", "scimitar", "scimitar", 1, ["slash"],
           weight_lb=3.0, min_level=42, unique_mult=1.6, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.5},
           lore="One of the four traditional weapons of Chinese martial arts. Masters achieve a 'no-mind' state where the blade becomes an extension of intent."),
    unique("naginata", "naginata", "polearm", "glaive", 2, ["slash", "pierce"],
           weight_lb=7.0, min_level=42, unique_mult=1.6, max_chain=6, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "crit_multiplier": 1.5},
           lore="Weapon of the onna-bugeisha and Buddhist warrior monks. More difficult to master than the katana, by tradition."),
    unique("claymore", "claymore", "sword", "greatsword", 2, ["slash", "pierce"],
           weight_lb=6.0, min_level=42, unique_mult=1.7, max_chain=6, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"highland_charge_bonus": 1.3},
           lore="Claidheamh mòr, 'great sword.' Swung in a Highland charge it could cleave through leather, mail, and occasionally the man wearing it."),
    unique("partisan", "partisan", "polearm", "glaive", 2, ["pierce", "slash"],
           weight_lb=7.0, min_level=42, unique_mult=1.6, max_chain=6, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "weapon_bind": True},
           lore="Ceremonial and combat polearm of the Renaissance. Side blades caught and bound opponents' weapons. Papal Swiss Guards carried these as marks of office."),

    # -- T4/F60-80 named --
    unique("mameluke_saber", "mameluke saber", "scimitar", "scimitar", 1, ["slash"],
           weight_lb=3.0, min_level=62, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.6, "cavalry_bonus": 1.3},
           lore="Weapon of the Islamic warrior-slave elite. The deadliest cavalry saber of its era; US Marine officers still carry a version of this blade."),
    unique("flamberge", "flamberge", "sword", "greatsword", 2, ["slash", "pierce"],
           weight_lb=6.0, min_level=62, unique_mult=1.7, max_chain=6, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.25, "parry_disrupt": True},
           lore="Wave-shaped blade. The undulations created additional cutting edges and disrupted opponents' parries by vibrating their weapons uncomfortably."),
    unique("executioners_sword", "executioner's sword", "sword", "greatsword", 2, ["slash"],
           weight_lb=6.0, min_level=62, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.7, "bleed_chance": 0.30},
           lore="Blunt-tipped — a stabbing weapon is useless against a kneeling target. Ground to extraordinary sharpness for a clean single-stroke execution."),

    # -- T5/F80-100 named legendaries --
    unique("soul_reaver", "Soul Reaver", "scimitar", "scimitar", 1, ["slash", "pierce"],
           weight_lb=3.0, min_level=82, unique_mult=1.9, max_chain=8, peak_chain_mult=8.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"lifesteal_percent": 0.15, "selects_wielder": True,
                              "bleed_chance": 0.30, "crit_multiplier": 1.7},
           lore="Few who have held the Soul Reaver remember doing so willingly. Wounds it inflicts do not heal without magic; the blade grows heavier if used against the innocent."),
    unique("dawnbreaker", "Dawnbreaker", "warhammer", "warhammer", 2, ["blunt", "fire", "holy"],
           weight_lb=8.0, min_level=82, unique_mult=2.0, max_chain=8, peak_chain_mult=8.0,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=5,
           special_properties={"undead_bonus": 3.0, "burn_chance": 0.30,
                              "stun_chance": 0.40, "crit_multiplier": 1.8},
           lore="The hammer that ended the First Darkness. Its adamantine head contains a shard of preserved dawn light, visible as a faint golden gleam in pitch darkness."),
    unique("venomfang", "Venomfang", "mace", "morningstar", 1, ["blunt", "pierce"],
           weight_lb=4.0, min_level=82, unique_mult=1.9, max_chain=8, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"poison_chance": 0.60, "corrupt_bleed": True,
                              "crit_multiplier": 2.0},
           lore="A master poisoner's commission. Hollow spikes weep a thin dark ichor when hungry. The bleed it inflicts does not merely cut — it corrupts."),

    # Excalibur — high-tier, lifesave on equip
    unique("excalibur", "Excalibur", "sword", "longsword", 1, ["slash", "holy"],
           weight_lb=3.0, min_level=70, unique_mult=2.0, max_chain=8, peak_chain_mult=8.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"on_equip_status": "life_save",
                              "kill_heal_amount": 5, "crit_multiplier": 2.0,
                              "stun_chance": 0.10},
           lore="The sword in the stone was a test of worthiness — a distinction Arthur understood only after he had already proven himself. An inscription along the fuller reads: 'Take me up; cast me away.' Most kings have trouble with the second part."),
    unique("durendal", "Durendal", "sword", "greatsword", 2, ["slash", "holy"],
           weight_lb=6.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "crit_multiplier": 1.9},
           lore="Roland's sword contained a tooth of Saint Peter, blood of Saint Basil, hair of Saint Denis, and a fragment of the Virgin's raiment. At Roncevaux he struck it three times against a stone. The stone split each time. Durendal did not."),

    # -- Boss-quest weapons --
    # Gram — REFORGED, Fafnir quest reward (F60). Quest-tied, ignore_resistances.
    # Anchored to F60. quest_mult 2.2 → base ~18.
    unique("gram", "Gram", "sword", "longsword", 1, ["slash", "pierce"],
           weight_lb=3.0, min_level=9999, tier_intended=60, unique_mult=2.2,
           max_chain=7, peak_chain_mult=7.0, spawn_method="quest_reward",
           max_enchant=5,
           special_properties={"ignore_resistances": True, "crit_multiplier": 2.2,
                              "bleed_chance": 0.20},
           lore="Odin thrust Gram into the Branstock oak; only Sigmund drew it. His son Sigurd had the pieces reforged. With Gram, he slew Fafnir, tasted its blood, and thereafter understood the speech of birds. Its edge cuts through any armor, any hide, any enchantment."),

    # Broken Gram — a deliberately bad weapon (quest item, but wieldable).
    # Brief §4 quest-item table: 4.0 lb broken sword chunk.
    unique("broken_gram", "Broken Blade of Gram", "sword", "shortsword", 1, ["slash"],
           weight_lb=4.0, min_level=9999, tier_intended=48, unique_mult=0.5,
           base_damage_override=3, max_chain=3, peak_chain_mult=2.0,
           spawn_method="quest_item", max_enchant=0,
           special_properties={"quest_item": True, "no_break": True},
           lore="The shattered remains of a legendary blade. Odin himself broke it against Sigmund's shield. The hilt is wrapped in cracked leather and the blade ends in a jagged fracture halfway up. It is a poor weapon — but something about it still hums."),

    # Sigurd's Shovel — quest tool, intentionally weak weapon but has can_dig.
    unique("sigurds_shovel", "Sigurd's Shovel", "club", "club", 1, ["blunt"],
           weight_lb=6.0, min_level=9999, tier_intended=53, unique_mult=0.9,
           base_damage_override=5, max_chain=4, peak_chain_mult=3.0,
           spawn_method="quest_reward", max_enchant=1,
           special_properties={"can_dig": True, "stun_chance": 0.05},
           lore="It's just an ordinary shovel. Really. Not everything has to be a magic sword. Sigurd dug a pit with one of these and stabbed a dragon in the belly from below — sometimes the right tool is the humble one."),

    # Norse heroic blades (legendary tier, ~F50-65)
    unique("tyrfing", "Tyrfing", "sword", "greatsword", 2, ["slash", "magic"],
           weight_lb=6.0, min_level=70, unique_mult=2.0, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"cursed": True, "ignore_shield": True,
                              "cursed_miss_backlash": 5, "bleed_chance": 0.30,
                              "crit_multiplier": 2.0, "must_kill_when_drawn": True},
           lore="The dwarves Dvalinn and Durin forged Tyrfing under duress and cursed it: it would kill a man every time unsheathed. Three kings of the Hervarar line died by it. The curse is intrinsic to those who lack the wisdom to set it down."),
    unique("fragarach", "Fragarach", "sword", "longsword", 1, ["pierce", "magic", "holy"],
           weight_lb=2.5, min_level=55, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "stun_chance": 0.25,
                              "crit_multiplier": 1.9, "ignore_armor": True},
           lore="The Answerer. No armour could stop it; no man could move once it was held to his throat. Manannan mac Lir forged it; Lugh carried it to end Fomorian tyranny."),
    unique("caladbolg", "Caladbolg", "sword", "greatsword", 2, ["slash"],
           weight_lb=7.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "knockback": True, "bleed_chance": 0.30,
                              "crit_multiplier": 2.0, "aoe_arc": True},
           lore="Fergus mac Róich's great sword could cut the tops off three hills with one sweep. Forged in the Otherworld. The original has no fragments because it has never broken."),
    unique("joyeuse", "Joyeuse", "sword", "longsword", 1, ["slash", "holy"],
           weight_lb=3.0, min_level=55, unique_mult=1.8, max_chain=8, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"stun_chance": 0.25, "dazzle_aura": True,
                              "crit_multiplier": 1.7},
           lore="Charlemagne's coronation sword changed colour thirty times per day and shone so brightly that enemies were dazzled before the first blow."),
    unique("hrunting", "Hrunting", "sword", "longsword", 1, ["slash", "pierce"],
           weight_lb=3.0, min_level=50, unique_mult=1.7, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.40, "crit_multiplier": 1.7,
                              "fails_vs_worthy_foes": True},
           lore="Unferth lent Hrunting to Beowulf for his descent into the mere. The poem calls it hardened in the blood of battle and says it had never failed any man who grasped it. In the underwater fight with Grendel's mother, it failed once."),
    unique("skofnung", "Skofnung", "sword", "longsword", 1, ["slash"],
           weight_lb=3.0, min_level=55, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.9, "wound_unhealable": True,
                              "berserker_souls": True, "bleed_chance": 0.20},
           lore="Taken from King Hrólf Kraki's burial mound; the twelve berserkers who served him in life inhabited the blade. Wounds dealt by Skofnung could only be healed by the Skofnung Stone. No healer has replicated the Stone."),

    # Spears
    unique("gungnir", "Gungnir", "spear", "spear", 1, ["pierce", "holy"],
           weight_lb=4.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "ignore_shield": True, "never_misses": True,
                              "crit_multiplier": 2.0},
           lore="An oath sworn on Gungnir's tip is unbreakable. Odin threw it over the Vanir's heads to begin the first war. It has never missed. At Ragnarok he will throw it at the Fenris Wolf."),
    unique("gae_bulg", "Gáe Bulg", "spear", "spear", 1, ["pierce"],
           weight_lb=3.0, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "ignore_shield": True,
                              "bleed_chance": 0.80, "stun_chance": 0.15,
                              "crit_multiplier": 2.0, "barbed_unwithdrawable": True},
           lore="Made from the bone of the Coinchenn sea-beast, thrown with the foot. When it entered a body it opened thirty barbs — it could not be withdrawn. Cu Chulainn used it twice in single combat; both times he wept after."),
    unique("spear_of_longinus", "Spear of Longinus", "spear", "spear", 1, ["pierce", "holy"],
           weight_lb=4.0, min_level=70, unique_mult=2.0, max_chain=8, peak_chain_mult=8.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "bleed_chance": 0.35,
                              "crit_multiplier": 2.0, "vs_demon_bonus": 1.5,
                              "vs_holy_target_special": True},
           lore="Longinus pierced Christ's side at the crucifixion. Blood and water ran from the wound; Longinus was healed of failing eyesight. Charlemagne carried it in 47 battles. He died the one day he set it down."),

    # Hammers / maces
    unique("mjolnir", "Mjolnir", "warhammer", "warhammer", 1, ["blunt", "lightning", "holy"],
           weight_lb=6.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=5,
           special_properties={"stun_chance": 0.40, "knockback": True,
                              "crit_multiplier": 2.0, "thrown_returns": True,
                              "lightning_arc_chance": 0.20},
           lore="The handle came out short due to Loki's sabotage, but Odin declared it the greatest treasure ever made. Thor wore iron gauntlets to wield it. At Ragnarok he will kill the Midgard Serpent, take nine steps, and fall."),
    unique("sharur", "Sharur", "mace", "mace", 1, ["blunt", "magic"],
           weight_lb=4.0, min_level=55, unique_mult=1.7, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"stun_chance": 0.20, "advisor_intel": True,
                              "crit_multiplier": 1.6, "confuse_chance": 0.25,
                              "knockback": True},
           lore="Ninurta's mace could fly ahead to scout and report back with intelligence. When Ninurta fought Asag the stone demon, Sharur flew ahead and counselled patience when a direct assault would have failed."),
    unique("ruyi_jingu_bang", "Ruyi Jingu Bang", "staff", "quarterstaff", 2,
           ["blunt", "magic"],
           weight_lb=8.0, min_level=60, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 3, "stun_chance": 0.25, "knockback": True,
                              "crit_multiplier": 1.9, "size_shifts": True},
           lore="Sun Wukong found this in the Dragon King's treasury where it weighted the ocean floor. It weighed 13,500 jin. In his hand it became exactly the right size. He killed 47,000 demons with it."),

    # Bows
    unique("gandiva", "Gandiva", "bow", "longbow", 2, ["pierce", "holy"],
           weight_lb=3.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 22, "requires_ammo": "arrow",
                              "crit_multiplier": 2.3, "stun_chance": 0.10,
                              "bleed_chance": 0.15, "infinite_strings": True},
           lore="Arjuna's divine bow had one hundred strings; when one broke another appeared. With it Arjuna killed 100,000 soldiers in the Kurukshetra War. Krishna delivered an 18-chapter philosophical treatise to persuade him to pick it up again."),
    unique("fail_not", "Fail-not", "bow", "longbow", 2, ["pierce"],
           weight_lb=2.0, min_level=50, unique_mult=1.6, max_chain=8, peak_chain_mult=7.0,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 20, "requires_ammo": "arrow",
                              "crit_multiplier": 2.5, "duty_aim_bonus": True,
                              "anger_aim_penalty": True},
           lore="Tristan's bow, given by the fairy Morgain. Its name was its promise. Arrows loosed in duty flew true; arrows loosed in anger missed. Its owner learned this the hard way."),

    # Eastern legendary
    unique("kusanagi", "Kusanagi-no-Tsurugi", "sword", "longsword", 1,
           ["slash", "magic", "wind"],
           weight_lb=2.5, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "knockback": True, "wind_aoe": True,
                              "crit_multiplier": 1.9},
           lore="Found inside the eight-headed serpent Yamata no Orochi. Yamato Takeru used it to cut the grass and redirect the wind when surrounded by enemies who had set fire to the plain. The sword has been at the Atsuta Shrine for fourteen centuries. No one has seen it."),
    unique("zulfiqar", "Zulfiqar", "sword", "longsword", 1, ["slash", "pierce"],
           weight_lb=3.0, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "bleed_chance": 0.20,
                              "crit_multiplier": 1.9, "bifurcated_tip_bonus": True},
           lore="Given to Ali ibn Abi Talib at the Battle of Badr. 'There is no sword but Zulfiqar, and no hero but Ali.' The bifurcated tip could take two lives with one thrust."),
    unique("harpe", "Harpe", "sword", "scimitar", 1, ["slash", "pierce"],
           weight_lb=2.5, min_level=55, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"ignore_shield": True, "bleed_chance": 0.25,
                              "crit_multiplier": 2.2, "petrify_on_crit": True},
           lore="Given to Perseus by Hermes to slay Medusa. Forged with an adamantine edge. Perseus used it while looking at Medusa's reflection in his shield. The weapon has a history of separating very important things."),

    # Gods' weapons & artifacts
    unique("trident_of_poseidon", "Trident of Poseidon", "spear", "spear", 1,
           ["pierce", "cold", "magic"],
           weight_lb=5.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "knockback": True, "stun_chance": 0.15,
                              "summons_water": True, "crit_multiplier": 1.7},
           lore="Poseidon struck the Acropolis and produced a saltwater spring. Athena planted an olive tree. He lost the vote and flooded the Attic plain."),
    unique("carnwennan", "Carnwennan", "dagger", "dagger", 1, ["pierce", "magic"],
           weight_lb=1.0, min_level=50, unique_mult=1.6, max_chain=8, peak_chain_mult=7.5,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "crit_multiplier": 2.8,
                              "on_equip_status": "invisible"},
           lore="Arthur's dagger that could shroud its wielder in shadow. Arthur used it to kill the Very Black Witch in the Valley of Grief after Kei and Bedivere had both tried and failed."),
    unique("mistilteinn", "Mistilteinn", "sword", "longsword", 1, ["slash", "magic"],
           weight_lb=2.5, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "crit_multiplier": 2.0,
                              "bypass_immortality": True},
           lore="The Mistletoe Sword. Mistletoe was the one substance Baldur was not protected against — his mother considered it too small to matter. The sword shares this property."),
    unique("curtana", "Curtana", "sword", "greatsword", 2, ["slash", "holy"],
           weight_lb=6.0, min_level=45, unique_mult=1.6, max_chain=7, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"stun_chance": 0.10, "mercy_blunt_tip": True,
                              "crit_multiplier": 1.5, "spare_low_hp_enemy": True},
           lore="The Sword of Mercy — its tip broken by an angel at the moment Ogier the Dane was about to kill Charlemagne's son. The broken tip became the symbol of mercy in justice."),
    unique("parashu", "Parashu", "axe", "battleaxe", 1, ["slash", "holy"],
           weight_lb=5.0, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=5,
           special_properties={"stun_chance": 0.20, "bleed_chance": 0.15,
                              "crit_multiplier": 1.7, "vs_warrior_caste_bonus": 1.5},
           lore="Shiva gave Parashu to Parashurama after ten thousand years of penance. Parashurama used it to exterminate the Kshatriya caste twenty-one times over, filling five lakes with blood."),
    unique("labrys", "Labrys", "axe", "battleaxe", 1, ["slash"],
           weight_lb=4.0, min_level=50, unique_mult=1.6, max_chain=7, peak_chain_mult=6.5,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=4,
           special_properties={"stun_chance": 0.15, "bleed_chance": 0.20,
                              "crit_multiplier": 1.8, "labyrinth_resonance": True},
           lore="The double-headed axe of Minoan Crete — labrys means both the axe and the labyrinth. It appears in every Minoan palace fresco, held by women. Modern scholars believe it was primarily religious."),
    unique("chandrahas", "Chandrahas", "scimitar", "scimitar", 1, ["slash", "cold", "holy"],
           weight_lb=3.0, min_level=55, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.8, "returns_on_evil_use": True,
                              "cold_aura": True},
           lore="Shiva gave the Moon's Laughter to Ravana after Ravana lifted Mount Kailash with twenty arms. Shiva added the condition that if used for evil it would return to him. Ravana used it for evil almost immediately."),
    unique("laevateinn", "Laevateinn", "staff", "quarterstaff", 2, ["magic", "fire", "holy"],
           weight_lb=5.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "stun_chance": 0.30,
                              "crit_multiplier": 2.0, "vs_rooster_special": True,
                              "burn_chance": 0.40},
           lore="Loki cut it at the gates of Hel. It can destroy Vidofnir, the golden rooster atop Yggdrasil whose crowing will begin Ragnarok."),
    unique("thyrsus", "Thyrsus of Dionysus", "staff", "quarterstaff", 2, ["blunt", "magic"],
           weight_lb=4.0, min_level=55, unique_mult=1.6, max_chain=8, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"confuse_chance": 0.50, "crit_multiplier": 1.5,
                              "madness_aura": True},
           lore="The Maenads carried the thyrsus. In the Bacchae, Agave kills her son Pentheus with it, believing in her madness he is a lion. Dionysus watched."),
    unique("rod_of_moses", "Rod of Moses", "staff", "quarterstaff", 2,
           ["blunt", "holy", "magic"],
           weight_lb=4.0, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 3, "stun_chance": 0.15, "knockback": True,
                              "crit_multiplier": 1.6, "transforms_to_serpent": True,
                              "poison_chance": 0.30},
           lore="The rod became a serpent in Pharaoh's court; parted the Red Sea; struck the rock at Horeb. Jewish tradition gives it a provenance from Adam through Noah through Abraham."),
    unique("amenonuhoko", "Amenonuhoko", "spear", "spear", 2, ["pierce", "magic"],
           weight_lb=5.0, min_level=70, unique_mult=1.9, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "aoe_slow_on_kill": True,
                              "stun_chance": 0.10, "crit_multiplier": 1.9,
                              "primordial_stillness": True},
           lore="The Heavenly Jeweled Spear, given to Izanagi and Izanami by the elder gods. They stirred the primordial ocean with it and from the brine that dripped from its tip, the first island of Japan was born."),
    unique("sudarshana", "Sudarshana Chakra", "scimitar", "scimitar", 1,
           ["slash", "fire", "holy"],
           weight_lb=2.0, min_level=65, unique_mult=1.9, max_chain=8, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"knockback": True, "crit_multiplier": 2.2,
                              "spinning_returns": True, "burn_chance": 0.25},
           lore="Vishnu's spinning discus. Forged from the effulgence of the sun itself. When Shiva asked to test Vishnu's most powerful weapon, Vishnu threw it without warning and cut off one of Shiva's heads. Shiva grew a new one."),
    unique("ridill", "Ridill", "dagger", "dagger", 1, ["pierce", "magic"],
           weight_lb=1.0, min_level=55, unique_mult=1.5, max_chain=8, peak_chain_mult=7.0,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=4,
           special_properties={"ignore_shield": True, "crit_multiplier": 2.4,
                              "potential_unrealized": True},
           lore="One of two swords in Fafnir's hoard alongside Gram. Sigurd left it when he took Gram. Ridill was the shorter blade — a dwarf-forged knife of theoretical powers, present at every great event of the Volsung cycle, never called upon."),
    unique("kladenets", "Samosek", "sword", "longsword", 1, ["slash", "magic"],
           weight_lb=3.0, min_level=55, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"crit_multiplier": 1.8, "counter_attack_chance": 0.25,
                              "autonomous_strike": True},
           lore="The Self-Swinger of Slavic fairy tales fights on its own. Heroes who find it never quite understand it. The sword fights; they survive. The sword's autonomy is treated not as alarming but as practical."),
    unique("shamshir_e_zomorrodnegar", "Shamshir-e Zomorrodnegar", "scimitar", "scimitar", 1,
           ["slash", "magic", "holy"],
           weight_lb=3.0, min_level=65, unique_mult=1.9, max_chain=7, peak_chain_mult=7.5,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"ignore_shield": True, "stun_chance": 0.30,
                              "crit_multiplier": 1.9, "djinn_bind": True},
           lore="The Emerald-Studded Sword of Solomon could bind and command djinn. Solomon used it not as a weapon but as an administrative tool, employing djinn in constructing the Temple."),
    unique("chrysaor", "Chrysaor", "sword", "longsword", 1, ["slash", "holy"],
           weight_lb=3.0, min_level=60, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"crit_multiplier": 2.0, "golden_blade": True},
           lore="Chrysaor — the Golden Sword — sprang from Medusa's neck alongside Pegasus when Perseus beheaded her. Heracles killed Geryones and the sword passed from the western world's records."),
    unique("caliburn", "Caliburn", "sword", "longsword", 1, ["slash"],
           weight_lb=3.0, min_level=50, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"stun_chance": 0.10, "crit_multiplier": 1.8,
                              "growing_power": True, "kills_to_grow": 10},
           lore="Some scholars distinguish Caliburn — the sword in the stone — from Excalibur, the sword from the lake. The stone-sword test and the lake-gift are morally opposite stories: one is earned, one is given. Arthur had both."),
    unique("brisingr", "Brisingr", "sword", "longsword", 1, ["slash", "fire"],
           weight_lb=3.0, min_level=55, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"crit_multiplier": 1.9, "burn_chance": 0.40,
                              "warm_to_touch": True},
           lore="The word for fire in Old Norse. A sword that shares its name with the ancient word for flame was found in a Norse burial mound in Gotland, its blade still faintly warm centuries later."),
    unique("fragarach_the_whisperer", "Whisperer", "dagger", "dagger", 1,
           ["pierce", "magic"],
           weight_lb=1.0, min_level=55, unique_mult=1.5, max_chain=8, peak_chain_mult=7.0,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=4,
           special_properties={"ignore_shield": True, "crit_multiplier": 2.6,
                              "silent_strike": True, "bleed_chance": 0.10},
           lore="A blade said to have been forged by the same smith who made Fragarach, intended as its companion. Where Fragarach answered questions loudly, this blade worked silently. Assassins across four centuries reported finding it rather than seeking it."),
    unique("naegling", "Naegling", "axe", "battleaxe", 1, ["slash", "blunt"],
           weight_lb=5.0, min_level=50, unique_mult=1.6, max_chain=7, peak_chain_mult=6.5,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.25, "crit_multiplier": 1.6,
                              "shatters_on_max_strength": True},
           lore="Beowulf's sword that shattered in his final battle with the dragon. The poem notes that iron could not help him — his grip was too strong for ordinary blades."),

    # Joke / cheat weapon
    unique("punch_in_the_face", "Punch in the Face", "fist", "unarmed", 1,
           ["blunt", "physical"],
           weight_lb=0.0, min_level=9999, tier_intended=100, unique_mult=999,
           base_damage_override=9999, max_chain=1, peak_chain_mult=1.0,
           spawn_method="cheat", max_enchant=0,
           special_properties={"stun_chance": 1.0, "knockback": True,
                              "dad_fist": True},
           lore="This is Dad's fist. It is legendary. It has never missed. It has never needed to miss twice. Scientists have attempted to measure the force behind it and their instruments simply stopped working out of respect."),

    # Spectral / monster-themed unique drops
    unique("hunt_captains_sword", "Hunt Captain's Sword", "sword", "longsword", 1,
           ["slash", "cold"],
           weight_lb=3.0, min_level=9999, tier_intended=70, unique_mult=1.8,
           max_chain=7, peak_chain_mult=7.5, spawn_method="unique_drop",
           max_enchant=4,
           special_properties={"effects": {"status": "bleeding",
                                          "effect_chance": 0.25,
                                          "effect_duration": 4},
                              "can_be_cursed": False,
                              "crit_multiplier": 1.9},
           lore="Taken from the captain of the Wild Hunt, this blade phases between this world and the spectral realm. Its edge is impossibly sharp and its cold is the cold of the grave."),
    unique("wendigo_fang", "Wendigo's Fang", "dagger", "dagger", 1, ["cold", "pierce"],
           weight_lb=1.0, min_level=9999, tier_intended=65, unique_mult=1.6,
           max_chain=7, peak_chain_mult=7.0, chain_profile="dagger",
           spawn_method="unique_drop", max_enchant=4,
           special_properties={"effects": {"status": "slowed",
                                          "effect_chance": 0.35,
                                          "effect_duration": 4},
                              "can_be_cursed": False,
                              "crit_multiplier": 2.0, "warmth_drain": True},
           lore="A fang torn from the Wendigo's maw. It leaches warmth and stamina from enemies on contact. The wound never feels warm again."),
    unique("echidna_fang", "Echidna's Fang", "dagger", "dagger", 1, ["pierce", "poison"],
           weight_lb=1.0, min_level=9999, tier_intended=40, unique_mult=1.5,
           max_chain=7, peak_chain_mult=6.5, chain_profile="dagger",
           spawn_method="unique_drop", max_enchant=3,
           special_properties={"effects": {"status": "poisoned",
                                          "effect_chance": 0.40,
                                          "effect_duration": 7},
                              "can_be_cursed": False,
                              "crit_multiplier": 1.8},
           lore="A tooth from Echidna herself, mother of all monsters. Wounds from it fester with a slow-acting venom that mimics her many children's poisons."),
    unique("vulcans_brand", "Vulcan's Brand", "sword", "longsword", 1, ["slash", "fire"],
           weight_lb=3.5, min_level=9999, tier_intended=35, unique_mult=1.5,
           max_chain=6, peak_chain_mult=5.5, spawn_method="unique_drop",
           max_enchant=3,
           special_properties={"effects": {"status": "burning",
                                          "effect_chance": 0.35,
                                          "effect_duration": 4},
                              "can_be_cursed": False,
                              "crit_multiplier": 1.6},
           lore="Forged in Vulcan's own furnace by Cacus who stole the technique from his father. The blade never fully cools and sets enemies alight on a solid strike."),

    # Early-game named scripture/myth weapons
    unique("sling_of_david", "Sling of David", "sling", "sling", 1, ["blunt"],
           weight_lb=0.5, min_level=5, unique_mult=1.7, max_chain=5, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 12, "knockback": True, "stun_chance": 0.20,
                              "crit_multiplier": 2.5, "infinite_ammo": True,
                              "requires_ammo": "stone", "giant_slayer": True},
           lore="The shepherd boy David faced the giant Goliath with nothing but a sling and five smooth stones. One stone was enough. The sling is the weapon of the underestimated."),
    unique("prometheus_torch", "Prometheus's Torch", "staff", "quarterstaff", 2,
           ["blunt", "fire"],
           weight_lb=4.0, min_level=8, unique_mult=1.6, max_chain=5, peak_chain_mult=5.0,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"burn_chance": 0.40, "crit_multiplier": 1.6,
                              "cannot_extinguish": True, "lights_dark": True},
           lore="Prometheus stole fire from the gods and gave it to humanity. This torch carries that stolen fire. It cannot be extinguished, and it cannot be refused — fire is humanity's birthright."),
    unique("sword_of_damocles", "Sword of Damocles", "sword", "longsword", 1,
           ["slash", "pierce"],
           weight_lb=3.0, min_level=12, unique_mult=2.0, max_chain=6, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=2,
           special_properties={"crit_multiplier": 1.8, "self_damage_chance": 0.10,
                              "thread_thinning": True},
           lore="Dionysius II of Syracuse invited the courtier Damocles to sit on his throne. Above the throne hung a sword, suspended by a single horsehair. The blade cuts magnificently, but the thread grows thinner with every swing."),
    unique("robin_hoods_longbow", "Robin Hood's Longbow", "bow", "longbow", 2, ["pierce"],
           weight_lb=3.0, min_level=14, unique_mult=1.6, max_chain=6, peak_chain_mult=5.5,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 20, "requires_ammo": "arrow",
                              "bleed_chance": 0.15, "crit_multiplier": 2.2,
                              "stealth_bonus": True},
           lore="Robin of Loxley, the outlaw of Sherwood Forest, could split an arrow at two hundred paces. It favors those who strike from the shadows — enemies that cannot see you cannot hear its string."),
    unique("achilles_spear", "Achilles's Spear", "spear", "spear", 2, ["pierce"],
           weight_lb=4.0, min_level=20, unique_mult=1.6, max_chain=7, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 2, "bleed_chance": 0.15,
                              "crit_multiplier": 1.8, "kill_heal_amount": 15,
                              "telephus_wound": True},
           lore="The spear of Achilles, son of Peleus, forged by Hephaestus. In the myth of Telephus, the spear that wounded also healed — rust scraped from its tip cured the very wound it had made."),
    unique("gilgamesh_axe", "Gilgamesh's Axe", "axe", "battleaxe", 2, ["slash"],
           weight_lb=7.0, min_level=35, unique_mult=1.7, max_chain=6, peak_chain_mult=6.0,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.20, "crit_multiplier": 1.8,
                              "wounded_strength_bonus": True},
           lore="Enkidu dreamed of an axe that fell from the sky — Gilgamesh's equal. In the Cedar Forest, Gilgamesh and Enkidu fought Humbaba together. The axe remembers that bond — it strikes harder after its wielder has been wounded."),
    unique("cronus_scythe", "Cronus's Scythe", "scimitar", "glaive", 2, ["slash", "magic"],
           weight_lb=6.0, min_level=38, unique_mult=1.7, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "ignore_shield": True,
                              "bleed_chance": 0.25, "crit_multiplier": 1.9,
                              "age_drain": True},
           lore="Gaia gave this adamantine scythe to Cronus to overthrow his father Uranus. From the blood sprang the Giants and the Furies. The scythe cuts through time and matter alike."),
    unique("spear_of_lugh", "Spear of Lugh", "spear", "spear", 2, ["pierce", "fire", "magic"],
           weight_lb=5.0, min_level=50, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"reach": 2, "ignore_shield": True,
                              "stun_chance": 0.10, "bleed_chance": 0.40,
                              "crit_multiplier": 2.0, "burn_chance": 0.30,
                              "bloodthirsty": True},
           lore="One of the Four Treasures of the Tuatha De Danann. The Spear of Lugh was so bloodthirsty it had to be kept submerged in a cauldron of poison. Lugh used it to slay Balor of the Evil Eye at the Second Battle of Mag Tuired."),
    unique("gae_dearg", "Gae Dearg", "spear", "spear", 1, ["pierce"],
           weight_lb=3.0, min_level=52, unique_mult=1.7, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "ignore_shield": True,
                              "bleed_chance": 0.90, "crit_multiplier": 1.8,
                              "unhealing_wound": True},
           lore="The Red Spear of Diarmuid Ua Duibhne, champion of the Fianna. Gae Buidhe the Yellow wounded but could not kill. Gae Dearg the Red — from which no wound could ever heal."),
    unique("net_of_hephaestus", "Net of Hephaestus", "net", "net", 1, ["blunt"],
           weight_lb=2.0, min_level=30, unique_mult=0.4, base_damage_override=2,
           max_chain=4, peak_chain_mult=2.0, spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 5, "stun_chance": 0.85,
                              "ignore_shield": True, "ensnare": True,
                              "invisible_mesh": True},
           lore="Hephaestus forged this net to catch Ares and Aphrodite. So fine it was invisible, so strong not even Ares could break free. This net does almost no damage — but nothing escapes it."),

    # NOTE: Sword of Michael added separately via sword_of_michael()
    # Oathkeeper — story drop (dead-adventurer flavor)
    unique("oathkeeper_sword", "Oathkeeper", "sword", "longsword", 1, ["slash"],
           weight_lb=2.5, min_level=9999, tier_intended=25, unique_mult=1.7,
           max_chain=6, peak_chain_mult=5.5, spawn_method="story_drop",
           max_enchant=3,
           special_properties={"bleed_chance": 0.15, "crit_multiplier": 1.7,
                              "kept_with_love": True},
           lore="A longsword of excellent make, the name VALE engraved into the crossguard. It was carried into the dungeon by a young man who wanted to prove himself. He didn't come back. The blade is still sharp — someone maintained it with love."),
    unique("penitents_blade", "Penitent's Blade", "dagger", "dagger", 1, ["pierce"],
           weight_lb=1.0, min_level=9999, tier_intended=45, unique_mult=1.7,
           max_chain=7, peak_chain_mult=6.5, chain_profile="dagger",
           spawn_method="story_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.25, "crit_multiplier": 2.0,
                              "lifesteal_percent": 0.15},
           lore="A wickedly sharp dagger of dark iron, carried for twenty years by a man who used it to kill. The blade drinks blood — wounds dealt with it restore the wielder's vitality, as though the weapon is trying to balance its ledger."),
    unique("boomstick", "Boomstick", "bow", "crossbow", 1, ["physical", "pierce"],
           weight_lb=5.0, min_level=9999, tier_intended=35, unique_mult=1.8,
           max_chain=4, peak_chain_mult=4.5, spawn_method="easter_egg",
           max_enchant=2,
           special_properties={"reach": 5, "stun_chance": 0.35,
                              "requires_ammo": "shell", "crit_multiplier": 2.5},
           lore="This is my BOOMSTICK! It's a twelve-gauge double-barreled Remington. S-Mart's top of the line. That's right, this sweet baby was made in Grand Rapids, Michigan. Shop smart. Shop S-Mart."),
    unique("chainsaw_prosthetic", "Chainsaw Prosthetic", "sword", "longsword", 1, ["slash"],
           weight_lb=5.0, min_level=9999, tier_intended=35, unique_mult=1.6,
           max_chain=5, peak_chain_mult=5.0, spawn_method="easter_egg",
           max_enchant=2,
           special_properties={"stun_chance": 0.15, "bleed_chance": 0.40,
                              "crit_multiplier": 1.7, "groovy": True},
           lore="A Homelite XL chainsaw, permanently bolted to the stump of a severed right hand. The original owner attached it in a moment of desperate improvisation in a remote cabin in Tennessee. Groovy."),

    # More named small-tier weapons (low-min-level)
    unique("romulus_spear", "Spear of Romulus", "spear", "spear", 1, ["pierce"],
           weight_lb=4.0, min_level=4, unique_mult=1.5, max_chain=5, peak_chain_mult=5.0,
           spawn_method="rare_drop", max_enchant=2,
           special_properties={"reach": 2, "bleed_chance": 0.10,
                              "takes_root": True},
           lore="When Romulus hurled his spear from the Aventine Hill into the Palatine, it struck the earth and took root, growing into a great tree. The spear that founded Rome."),
    unique("pharaohs_crook", "Pharaoh's Crook", "staff", "club", 1, ["blunt"],
           weight_lb=2.0, min_level=3, unique_mult=1.4, max_chain=5, peak_chain_mult=4.5,
           spawn_method="rare_drop", max_enchant=2,
           special_properties={"stun_chance": 0.25, "divine_kingship": True},
           lore="The crook and flail were the symbols of pharaonic authority. This crook once rested in the crossed arms of a king. Its strikes carry the weight of divine kingship, stunning those who would oppose the throne."),
    unique("mjolnir_shard", "Mjolnir Shard", "mace", "mace", 1, ["blunt", "lightning"],
           weight_lb=5.0, min_level=10, unique_mult=1.7, max_chain=6, peak_chain_mult=5.0,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"stun_chance": 0.25, "lightning_arc_chance": 0.15,
                              "crit_multiplier": 1.6},
           lore="A jagged fragment of Thor's legendary hammer. Though only a shard, it still carries the storm. Lightning arcs between its fractures, and each blow echoes with distant thunder."),
    unique("bow_of_rama", "Bow of Rama", "bow", "longbow", 2, ["pierce", "fire"],
           weight_lb=3.0, min_level=12, unique_mult=1.6, max_chain=5, peak_chain_mult=5.5,
           chain_profile="dagger", spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 12, "requires_ammo": "arrow",
                              "burn_chance": 0.30, "crit_multiplier": 2.0,
                              "dharma_guided": True},
           lore="The great bow of Lord Rama, hero of the Ramayana. His arrows, guided by dharma, struck down the demon king Ravana and his armies. This bow carries that sacred fire."),
    unique("gae_bolg_fragment", "Gae Bolg Fragment", "spear", "spear", 1, ["pierce"],
           weight_lb=3.0, min_level=20, unique_mult=1.7, max_chain=6, peak_chain_mult=5.5,
           spawn_method="rare_drop", max_enchant=3,
           special_properties={"reach": 2, "crit_multiplier": 2.3,
                              "bleed_chance": 0.30, "barbed_wound": True},
           lore="A fragment of the Gae Bolg, the cursed spear of Cu Chulainn. Made from the bone of a sea monster — once it pierced flesh, its barbs opened inside the wound. Even this fragment carries that legacy."),
    unique("staff_of_moses", "Staff of Moses", "staff", "quarterstaff", 2,
           ["blunt", "holy"],
           weight_lb=4.0, min_level=25, unique_mult=1.7, max_chain=6, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"stun_chance": 0.15, "crit_multiplier": 1.6,
                              "vs_unholy_bonus": 1.5, "divine_authority": True},
           lore="The staff that Moses raised to part the Red Sea. It was a simple shepherd's staff before God chose it — and that is the lesson. It is not the weapon that matters, but the hand that wields it and the faith behind it."),
    unique("witcher_silver_blade", "Witcher's Silver Blade", "sword", "longsword", 1,
           ["slash", "holy"],
           weight_lb=2.5, min_level=9999, tier_intended=22, unique_mult=1.6,
           max_chain=6, peak_chain_mult=5.5, spawn_method="story_drop",
           max_enchant=3,
           special_properties={"vs_monster_bonus": 1.5, "bleed_chance": 0.10,
                              "crit_multiplier": 1.6, "rune_inscribed": True},
           lore="A witcher's silver sword, forged for one purpose: killing monsters. Where steel is for men, silver is for creatures of the night. The runes along its edge hum faintly in the presence of dark magic."),
    unique("zireael", "Zireael", "sword", "longsword", 1, ["slash"],
           weight_lb=2.0, min_level=9999, tier_intended=30, unique_mult=1.7,
           max_chain=6, peak_chain_mult=6.0, spawn_method="story_drop",
           max_enchant=4,
           special_properties={"bleed_chance": 0.15, "crit_multiplier": 2.0,
                              "lighter_than_steel": True, "elder_blood": True},
           lore="Zireael — 'Swallow' in Elder Speech. Forged by the gnome swordsmith Esterhazy of Mahakam. Lighter than any human-forged sword yet harder than dwarven steel. She will return. She always returns."),
    unique("vel_of_murugan", "Vel of Murugan", "spear", "spear", 1,
           ["pierce", "fire", "holy"],
           weight_lb=3.5, min_level=45, unique_mult=1.7, max_chain=7, peak_chain_mult=6.5,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"reach": 2, "crit_multiplier": 1.7,
                              "effects": {"status": "burning",
                                         "effect_chance": 0.30,
                                         "effect_duration": 5}},
           lore="The Vel was given to Murugan by his mother Parvati to slay the demon Surapadman. When thrown, it split the demon in two — one half became a peacock, the other a rooster."),
    unique("khopesh_of_anubis", "Khopesh of Anubis", "sword", "scimitar", 1, ["slash"],
           weight_lb=3.0, min_level=30, unique_mult=1.6, max_chain=6, peak_chain_mult=6.0,
           spawn_method="rare_drop", max_enchant=4,
           special_properties={"bleed_chance": 0.15, "crit_multiplier": 1.7,
                              "kill_heal_amount": 3, "kill_max_hp_bonus": 1,
                              "kill_max_hp_cap": 10},
           lore="A ceremonial khopesh carried by the priests of Anubis during the weighing of hearts. Those judged unworthy were consumed — their life force absorbed into the blade. Each kill strengthens the wielder permanently."),
    unique("chandrahasa", "Chandrahasa", "sword", "longsword", 1, ["slash", "magic"],
           weight_lb=2.5, min_level=65, unique_mult=1.8, max_chain=7, peak_chain_mult=7.0,
           spawn_method="rare_drop", max_enchant=5,
           special_properties={"bleed_chance": 0.10, "crit_multiplier": 2.0,
                              "low_hp_damage_bonus": True,
                              "returns_on_evil_use": True},
           lore="The 'Laughing Moon,' given to Ravana by Shiva himself. The blade laughed as it cut — a high, cold sound like cracking ice. It grows more dangerous as its wielder's life fades, channeling desperation into devastating power."),
    unique("green_chapel_axe", "Green Chapel Axe", "axe", "battleaxe", 1, ["slash"],
           weight_lb=4.5, min_level=35, unique_mult=1.6, max_chain=6, peak_chain_mult=6.0,
           chain_profile="axe", spawn_method="rare_drop", max_enchant=3,
           special_properties={"bleed_chance": 0.20, "crit_multiplier": 1.6,
                              "on_hit_regen": 3, "decapitates_returns": True},
           lore="The axe carried by the Green Knight into Arthur's hall on New Year's Day. He offered a game: any knight may strike one blow, if the Green Knight may return it in a year. Gawain took the challenge. The axe remembers."),
]

# Add the special-case Sword of Michael
WEAPONS.append(sword_of_michael())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = Path(__file__).resolve().parent
    written = 0
    ids_seen = set()
    for w in WEAPONS:
        wid = w["id"]
        if wid in ids_seen:
            print(f"WARNING: duplicate id {wid} — skipping")
            continue
        ids_seen.add(wid)
        path = out_dir / f"{wid}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(w, f, indent=2, ensure_ascii=False)
        written += 1
    print(f"Wrote {written} unique weapons to {out_dir}")


if __name__ == "__main__":
    main()
