"""Generator F — Wands, Scrolls, Spellbooks, Spells.

Reads source data files for names/lore/effects/structure, then rebalances
every numerical value against tools/balance/curve.py. Writes to:

  tools/balance/generated/data/wand.json
  tools/balance/generated/data/scroll.json
  tools/balance/generated/data/spellbook.json
  tools/balance/generated/data/spells.py.proposed
"""

from __future__ import annotations
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import curve  # noqa: E402

OUT_DIR = ROOT / "tools" / "balance" / "generated" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def math_tier_for_floor(floor: int) -> int:
    """Math tier dominant at the given floor (T1-T5). Used as quiz_tier anchor."""
    return curve.math_tier_dominant(max(1, min(100, floor)))


def grammar_tier_for_floor(floor: int) -> int:
    """Grammar tier mirrors math tier per the per-subject quiz_tier convention
    (subject differs, tier bands are shared with the math band table)."""
    return curve.math_tier_dominant(max(1, min(100, floor)))


def dice_from_avg(target_avg: float) -> str:
    """Return a dice string whose expected damage is close to target_avg.
    Damage wands key off this for elemental/force/striking wands.

    Strategy: pick a die size {4,6,8} and count of dice that yields a mean
    in [target * 0.9, target * 1.1]. Mean of NdK = N*(K+1)/2.
    """
    target = max(1.0, target_avg)
    candidates = []
    for k in (4, 6, 8):
        # closest N
        n = max(1, round(target * 2 / (k + 1)))
        mean = n * (k + 1) / 2
        candidates.append((abs(mean - target) / target, n, k, mean))
    candidates.sort()
    _, n, k, _ = candidates[0]
    return f"{n}d{k}"


def heal_dice_for_floor(floor: int) -> str:
    """Heal magnitude scales with player HP target so a heal restores ~30-50% HP."""
    target_hp = curve.player_hp_target(floor, 'P')
    return dice_from_avg(target_hp * 0.40)


def extra_heal_dice_for_floor(floor: int) -> str:
    target_hp = curve.player_hp_target(floor, 'P')
    return dice_from_avg(target_hp * 0.65)


def damage_dice_for_floor(floor: int, ratio: float = 1.0) -> str:
    """Damage wand dice — chain-5 weapon-damage scaled.

    Wand damage at chain-5 should be a serviceable elemental supplement
    to chain weapons, but is single-shot and consumes a charge. We anchor
    on weapon_base_damage at the wand's min_level, scaled by ratio.
    The chain multiplier at rung 5 in the system is 2.5 (curve.WEAPON_CHAIN_5_MULT),
    so base * 2.5 ~ chain-5 average. We aim for ~base-damage average.
    """
    base = curve.weapon_base_damage(floor)
    return dice_from_avg(base * ratio * 1.4)  # ~1.4x base feels right for elemental burst


def spell_damage_dice_for_floor(floor: int, ratio: float = 1.0) -> str:
    """Spell power dice — at chain-5 should rival a chain-5 weapon hit.

    chain-5 mult on most spell damage = ~chain_score-based (multiplied by INT/chain).
    We anchor pure dice average to weapon_base_damage * 1.6 so chain-5 equivalence
    holds after the system's chain scaling.
    """
    base = curve.weapon_base_damage(floor)
    return dice_from_avg(base * ratio * 1.6)


def peak_spread_from_min_level(min_level: int) -> tuple[int, int]:
    """Derive (peak_floor, spread) from a legacy min_level value.

    Convention: the item is most common ~10 floors after first plausible spawn,
    spread scales with floor band so end-game items have wider tails.
    """
    if min_level <= 1:
        return (3, 5)
    if min_level <= 3:
        return (min_level + 4, 6)
    if min_level <= 10:
        return (min_level + 6, 8)
    if min_level <= 20:
        return (min_level + 8, 10)
    if min_level <= 40:
        return (min_level + 10, 12)
    if min_level <= 60:
        return (min_level + 8, 14)
    return (min_level + 5, 16)


# --------------------------------------------------------------------------
# Wand rebalance
# --------------------------------------------------------------------------

# Categorize wands by effect family. Tier shifts the peak floor.
# (effect -> (avg_min_level_band, damage_ratio_if_damage, charges_band, quiz_threshold))
# damage_ratio_if_damage None means status-effect, no power dice.

# Damage families: amount of dice expressed as multiplier on weapon_base_damage.
DAMAGE_EFFECTS = {
    "fire_bolt": 1.3,
    "cold_bolt": 1.3,
    "lightning_bolt": 1.4,    # lightning rewards accuracy
    "acid_spray": 1.1,
    "magic_missile": 1.2,
    "striking": 1.5,           # pure kinetic — no resistance bypass elemental
    "drain_life": 1.0,         # heals user, so dial down
    "explosion": 1.6,          # AOE risk
    "nova": 1.8,               # legendary AOE
    "turn_undead": 1.4,        # damage scroll vs undead
}
# Tier-bands: charges (min,max) and quiz_threshold by tier
CHARGES_BY_TIER = {
    1: (5, 8),
    2: (4, 6),
    3: (3, 5),
    4: (2, 4),
    5: (2, 3),
}
QUIZ_THRESHOLD_BY_TIER = {1: 2, 2: 2, 3: 3, 4: 3, 5: 3}

# Power wands get a manual override (low charges, high floor)
POWER_TIER_WANDS = {
    "wand_of_death", "wand_of_disintegration", "wand_of_time_stop",
    "wand_of_wishing", "wand_of_nova", "wand_of_life_force",
    "wand_of_abjuration", "wand_of_polymorph", "wand_of_transmutation",
    "wand_of_banishment", "wand_of_genocide",
}

# Wand floor anchors — for each id, the floor at which it should be at peak.
# Derived from legacy min_level but clamped to sensible bands. None = derive
# from min_level numerically.
# We won't enumerate everything; derive from min_level via heuristic.

# Effect-aware quiz tier anchor: minimum tier the wand can require
EFFECT_MIN_TIER = {
    "wish": 5,
    "time_stop": 5,
    "death_ray": 4,
    "disintegrate": 5,
    "life_transfer": 5,
    "abjuration": 5,
    "nova": 5,
    "iron_mortar": 4,
}


def rebalance_wand(wid: str, src: dict) -> dict:
    """Produce rebalanced wand entry preserving id/name/lore/effect/symbol/color."""
    effect = src.get("effect", "")
    legacy_min = int(src.get("min_level", 1))

    # The legacy min_level was on a 1-5 tier scale for many wands. If <=5
    # treat as a "tier indicator" and remap to floor band.
    # 1->floor 1, 2->floor 8, 3->floor 18, 4->floor 32, 5->floor 55
    if legacy_min <= 5:
        anchor_floor = {1: 1, 2: 8, 3: 18, 4: 32, 5: 55}[legacy_min]
    elif legacy_min == 9999:
        anchor_floor = 9999  # quest-only
    else:
        anchor_floor = legacy_min

    # Determine quiz_tier — honor source tier as a FLOOR (legacy data was
    # hand-tuned per-wand for difficulty), but let the curve push it up.
    legacy_tier = int(src.get("quiz_tier", 1))
    if anchor_floor == 9999:
        tier = legacy_tier
    else:
        tier = max(legacy_tier, math_tier_for_floor(anchor_floor))
    # Floor on effect-based minimums (power wands)
    if effect in EFFECT_MIN_TIER:
        tier = max(tier, EFFECT_MIN_TIER[effect])
    # Cap at 5
    tier = max(1, min(5, tier))
    # Bump the anchor floor to the band lower-bound of the tier so spawn
    # bell matches the quiz difficulty. (T2 starts at F20, T3 at F40, etc.)
    if anchor_floor != 9999:
        tier_band_floor = {1: max(1, anchor_floor), 2: max(20, anchor_floor),
                           3: max(40, anchor_floor), 4: max(60, anchor_floor),
                           5: max(80, anchor_floor)}[tier]
        anchor_floor = tier_band_floor

    # Charges
    cmin, cmax = CHARGES_BY_TIER[tier]
    if wid in POWER_TIER_WANDS or effect in {"wish", "time_stop", "disintegrate", "death_ray"}:
        cmin, cmax = 1, 3

    # Quiz threshold
    threshold = QUIZ_THRESHOLD_BY_TIER[tier]
    # Bigger commitment to use a power wand
    if wid in POWER_TIER_WANDS:
        threshold = min(threshold + 1, 4)

    # Power dice
    power = ""
    if effect in DAMAGE_EFFECTS:
        ratio = DAMAGE_EFFECTS[effect]
        # Bigger named versions (rod_of_chaos, wand_of_nova) get bumps via wid
        if "wand_of_inferno" == wid or "wand_of_glaciation" == wid or "wand_of_storm" == wid:
            ratio *= 1.2
        if "wand_of_annihilation" == wid:
            ratio *= 1.3
        damage_floor = anchor_floor if anchor_floor != 9999 else 20
        power = damage_dice_for_floor(damage_floor, ratio)
    elif effect == "heal":
        power = heal_dice_for_floor(max(1, anchor_floor if anchor_floor != 9999 else 10))
    elif effect == "extra_heal":
        power = extra_heal_dice_for_floor(max(1, anchor_floor if anchor_floor != 9999 else 15))
    else:
        # Preserve any structured power from legacy if it was a non-empty string
        # we don't otherwise recognize (e.g., quest scroll codes — for wands we
        # really only have damage and heal)
        power = ""

    # Peak/spread
    if anchor_floor == 9999:
        peak_floor, spread, min_level = 9999, 0, 9999
    else:
        peak_floor, spread = peak_spread_from_min_level(anchor_floor)
        min_level = anchor_floor

    out = {
        "name": src["name"],
        "symbol": src.get("symbol", "/"),
        "color": src.get("color", [200, 200, 200]),
        "weight_lb": 1.0,
        "min_level": min_level,
        "peak_floor": peak_floor,
        "spread": spread,
        "charges_min": cmin,
        "charges_max": cmax,
        "max_charges": cmax,
        "quiz_tier": tier,
        "quiz_threshold": threshold,
        "effect": effect,
        "power": power,
        "unidentified_name": src.get("unidentified_name", ""),
        "lore": src.get("lore", ""),
    }
    # Preserve container loot tier / identified / sprite_desc if present
    for key in ("containerLootTier", "identified", "sprite_desc", "value"):
        if key in src:
            out[key] = src[key]
    return out


# --------------------------------------------------------------------------
# Scroll rebalance
# --------------------------------------------------------------------------

# Quest reward scrolls — keep min_level 9999 and structure intact
QUEST_REWARD_EFFECTS = {"boss_reward"}

# Effects that are damage-scaling
SCROLL_DAMAGE_EFFECTS = {
    "earth": 1.4,
    "annihilate": 1.5,
}

# Effects requiring power-tier (T5)
SCROLL_POWER_EFFECTS = {"annihilate", "great_power", "genocide", "time_stop_scroll"}


def rebalance_scroll(sid: str, src: dict) -> dict:
    effect = src.get("effect", "")
    legacy_min = int(src.get("min_level", 1))
    anchor_floor = legacy_min if legacy_min < 9999 else 9999

    # Quiz tier (grammar) — honor source tier as a FLOOR, curve can push up.
    legacy_tier = int(src.get("quiz_tier", 1))
    if anchor_floor == 9999:
        tier = legacy_tier
    else:
        tier = max(legacy_tier, grammar_tier_for_floor(anchor_floor))
    if effect in SCROLL_POWER_EFFECTS:
        tier = max(tier, 5)
    if effect == "enchant_weapon" or effect == "enchant_armor" or effect == "enchant_item" or effect == "enchant_accessory":
        # Permanent enchantments require commitment — bump tier to floor +1
        tier = max(tier, min(5, grammar_tier_for_floor(anchor_floor) + 1))
    tier = max(1, min(5, tier))
    # Adjust anchor floor to match tier band lower-bound (soft, only upward)
    if anchor_floor != 9999:
        tier_band_floor = {1: max(1, anchor_floor), 2: max(20, anchor_floor),
                           3: max(40, anchor_floor), 4: max(60, anchor_floor),
                           5: max(80, anchor_floor)}[tier]
        anchor_floor = tier_band_floor

    # Quiz threshold (scrolls are grammar — fewer questions, since chain is
    # 1-shot effect for reading)
    base_thr = QUIZ_THRESHOLD_BY_TIER[tier]
    threshold = base_thr
    if effect in {"enchant_weapon", "enchant_armor", "enchant_item", "enchant_accessory",
                  "great_power", "genocide", "charging"}:
        threshold += 1
    threshold = max(1, min(5, threshold))

    # Power
    power = src.get("power", "")
    if effect in SCROLL_DAMAGE_EFFECTS:
        ratio = SCROLL_DAMAGE_EFFECTS[effect]
        floor_for_dmg = anchor_floor if anchor_floor != 9999 else 30
        power = damage_dice_for_floor(floor_for_dmg, ratio)
    elif effect == "heal":
        power = heal_dice_for_floor(max(1, anchor_floor if anchor_floor != 9999 else 5))
    elif effect == "haste_self" and power and not power.startswith("QUEST") and not any(c.isalpha() for c in str(power)[:3]):
        # numeric duration — preserve
        pass
    elif effect == "time_stop_scroll":
        power = "8"  # duration in turns; balanced down from legacy 10
    elif effect == "boss_reward":
        # preserve unique boss code
        power = src.get("power", "")

    # Peak/spread
    if anchor_floor == 9999:
        peak_floor, spread, min_level = 9999, 0, 9999
    else:
        peak_floor, spread = peak_spread_from_min_level(anchor_floor)
        min_level = anchor_floor

    out = {
        "name": src["name"],
        "symbol": src.get("symbol", "?"),
        "color": src.get("color", [200, 200, 200]),
        "weight_lb": 0.1,
        "min_level": min_level,
        "peak_floor": peak_floor,
        "spread": spread,
        "quiz_tier": tier,
        "quiz_threshold": threshold,
        "effect": effect,
        "power": power,
        "unidentified_name": src.get("unidentified_name", ""),
        "lore": src.get("lore", ""),
        "read_threshold": threshold,
    }
    # Preserve flags
    for key in ("item_class", "identified", "containerLootTier", "sprite_desc",
                "value", "single_copy"):
        if key in src:
            out[key] = src[key]
    # Lake of fire / death's bane stay single_copy if existing
    if sid in {"scroll_of_lake_of_fire", "scroll_of_deaths_bane"} and "single_copy" not in out:
        out["single_copy"] = True
    return out


# --------------------------------------------------------------------------
# Spell + Spellbook rebalance
# --------------------------------------------------------------------------

# Spell metadata — anchor floor per spell ID. Used to derive quiz_tier (math
# tier matches floor band) and MP cost. Spell damage uses spell_damage_dice.
# Status / utility spells have power="".

SPELL_FLOOR_ANCHORS = {
    # T1 (F1-19)
    "magic_missile_spell": 1,
    "sleep_spell": 3,
    "light_spell": 2,
    "cleanse_spell": 5,
    "sign_aard": 5,
    "sign_igni": 5,
    "sign_quen": 5,
    "sign_yrden": 5,
    "sign_axii": 5,
    "elder_blink": 5,
    "elder_charge": 8,
    "army_of_darkness_spell": 18,   # Necronomicon — flavor T1 but mid-floor
    # T2 (F20-39)
    "shield_spell": 22,
    "fire_bolt_spell": 22,
    "fireball_spell": 22,
    "haste_spell": 25,
    "slow_spell": 22,
    "knock_spell": 22,
    "teleport_away_spell": 26,
    "empower_spell": 30,
    "elder_scream": 28,
    # T3 (F40-59)
    "heal_spell": 42,
    "invisibility_spell": 45,
    "lightning_spell": 45,
    "confusion_spell": 40,
    "smite_spell": 50,
    "summon_guardian_spell": 48,
    "acid_arrow_spell": 42,
    "drain_life_spell": 48,
    "fear_spell": 42,
    "detect_spell": 40,
    "polymorph_spell": 48,
    # T4 (F60-79)
    "displacement_spell": 62,
    "ice_storm_spell": 62,
    "paralyze_spell": 60,
    "meteor_spell": 70,
    "reflect_spell": 65,
    # T5 (F80-100)
    "time_freeze_spell": 85,
    "disintegrate_spell": 88,
}

# Spell base MP cost: tier-banded. Bigger spells pay more.
MP_BY_TIER = {1: 4, 2: 7, 3: 10, 4: 13, 5: 17}

# Effect tags that justify extra MP cost
EXPENSIVE_EFFECTS = {
    "summon_undead_horde", "meteor", "time_freeze", "disintegrate_spell",
    "summon_guardian", "mass_ice", "mass_fire", "smite",
}
CHEAP_EFFECTS = {
    "light", "cleanse_self", "knock_spell", "teleport_self",
    "detect_monsters_spell", "slow_monster", "slow_monster_spell",
    "teleport_away_spell",
}


def rebalance_spell(sid: str, src: dict) -> dict:
    floor = SPELL_FLOOR_ANCHORS.get(sid, 10)
    tier = math_tier_for_floor(floor)

    # Witcher signs are intentionally T1 — Geralt is a starter kit.
    if sid.startswith("sign_") or sid.startswith("elder_"):
        tier = min(tier, 2)
        if sid in {"sign_aard", "sign_igni", "sign_quen", "sign_yrden",
                   "sign_axii", "elder_blink", "elder_charge"}:
            tier = 1
        elif sid == "elder_scream":
            tier = 2

    # Necronomicon: T1 by lore (flesh-bound book even an apprentice can read,
    # but the consequences are real) — preserve.
    if sid == "army_of_darkness_spell":
        tier = 1

    mp = MP_BY_TIER[tier]
    effect = src.get("effect", "")
    if effect in EXPENSIVE_EFFECTS:
        mp += 3
    elif effect in CHEAP_EFFECTS:
        mp = max(2, mp - 2)

    # Power
    power = src.get("power", "")
    if power:
        # damage spell — re-derive
        # Tune ratio by effect
        ratio = 1.0
        if effect in {"smite", "disintegrate_spell"}:
            ratio = 1.5
        elif effect in {"meteor", "mass_ice", "mass_fire", "lightning_bolt"}:
            ratio = 1.2
        elif effect in {"magic_missile"}:
            ratio = 0.8  # reliable, low-tier starter
        elif effect in {"fire_bolt", "acid_arrow"}:
            ratio = 1.1
        elif effect in {"drain_life_spell"}:
            ratio = 0.9  # heals user, dial back
        elif effect == "extra_heal":
            # heal spell uses player_hp_target
            power = heal_dice_for_floor(floor) if floor < 100 else "5d8"
        elif effect == "aard_blast":
            ratio = 0.9
        power = spell_damage_dice_for_floor(floor, ratio)

    # Rewrite desc to replace stale dice references with current power.
    desc = src.get("desc", "")
    if power and "d" in power:
        import re
        # Replace any NdK occurrence in description with new power dice
        desc = re.sub(r"\b\d+d\d+\b", power, desc)

    return {
        "name": src["name"],
        "effect": effect,
        "power": power,
        "mp_cost": mp,
        "quiz_tier": tier,
        "needs_target": src.get("needs_target", False),
        "desc": desc,
    }


def rebalance_spellbook(bid: str, src: dict, rebalanced_spells: dict) -> dict:
    spell_id = src.get("spell_id", "")
    spell = rebalanced_spells.get(spell_id, {})

    # Use spell's tier as basis but books are slightly harder than casting
    # (grammar to LEARN > grammar to USE)
    spell_tier = spell.get("quiz_tier", 1)
    book_tier = min(5, spell_tier + 0 if spell_tier >= 4 else spell_tier)
    # For low-tier spells, learning is approachable. For high-tier, it's a step up.
    # We'll leave tier identical to spell for clarity.
    tier = spell_tier

    # Quiz threshold: harder than casting; books require multiple correct
    # answers to study successfully.
    threshold = QUIZ_THRESHOLD_BY_TIER[tier] + 1
    if tier >= 4:
        threshold += 1
    threshold = max(2, min(6, threshold))

    # MP cost on the book matches the spell's MP cost
    mp = spell.get("mp_cost", src.get("mp_cost", 5))

    legacy_min = int(src.get("min_level", 1))
    # Use SPELL_FLOOR_ANCHORS preferentially
    floor = SPELL_FLOOR_ANCHORS.get(spell_id, legacy_min if legacy_min < 9999 else 10)
    peak_floor, spread = peak_spread_from_min_level(floor)

    out = {
        "name": src["name"],
        "symbol": src.get("symbol", "+"),
        "color": src.get("color", [200, 200, 200]),
        "weight_lb": 3.0,
        "min_level": floor,
        "peak_floor": peak_floor,
        "spread": spread,
        "quiz_tier": tier,
        "quiz_threshold": threshold,
        "spell_id": spell_id,
        "spell_name": src.get("spell_name", spell.get("name", "")),
        "mp_cost": mp,
        "unidentified_name": src.get("unidentified_name", ""),
        "lore": src.get("lore", ""),
        "read_threshold": threshold,
    }
    for key in ("sprite_desc",):
        if key in src:
            out[key] = src[key]
    return out


# --------------------------------------------------------------------------
# Drive
# --------------------------------------------------------------------------

def main():
    src_wand = json.load(open(ROOT / "data" / "items" / "wand.json"))
    src_scroll = json.load(open(ROOT / "data" / "items" / "scroll.json"))
    src_book = json.load(open(ROOT / "data" / "items" / "spellbook.json"))

    # Wands
    out_wand = {wid: rebalance_wand(wid, src) for wid, src in src_wand.items()}
    json.dump(out_wand, open(OUT_DIR / "wand.json", "w"), indent=2)

    # Scrolls
    out_scroll = {sid: rebalance_scroll(sid, src) for sid, src in src_scroll.items()}
    json.dump(out_scroll, open(OUT_DIR / "scroll.json", "w"), indent=2)

    # Import LEARNABLE_SPELLS dict directly
    sys.path.insert(0, str(ROOT / "src"))
    from spells import LEARNABLE_SPELLS  # noqa: E402

    out_spells = {sid: rebalance_spell(sid, src) for sid, src in LEARNABLE_SPELLS.items()}

    # Spellbooks
    out_book = {bid: rebalance_spellbook(bid, src, out_spells)
                for bid, src in src_book.items()}
    json.dump(out_book, open(OUT_DIR / "spellbook.json", "w"), indent=2)

    # Spells (Python source proposal)
    lines = [
        '"""Spells learnable from spellbooks (spell_id -> attributes).',
        '',
        'PROPOSED REBALANCE — Generator F, against tools/balance/curve.py.',
        '',
        'Power dice derive from curve.weapon_base_damage(floor) * ratio so that',
        "chain-5 spell damage rivals chain-5 weapon damage at the spell's tier band.",
        'MP cost derives from MP_BY_TIER[tier] +/- effect adjustments.',
        'quiz_tier follows math_tier_dominant(spell_floor_anchor).',
        '"""',
        '',
        'LEARNABLE_SPELLS: dict[str, dict] = {',
    ]
    for sid, s in out_spells.items():
        needs_target = s.get("needs_target", False)
        lines.append(f"    '{sid}': {{")
        lines.append(f"        'name': {s['name']!r}, 'effect': {s['effect']!r}, 'power': {s['power']!r},")
        lines.append(f"        'mp_cost': {s['mp_cost']}, 'quiz_tier': {s['quiz_tier']}, 'needs_target': {needs_target},")
        lines.append(f"        'desc': {s['desc']!r},")
        lines.append("    },")
    lines.append("}")
    (OUT_DIR / "spells.py.proposed").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wands written: {len(out_wand)}")
    print(f"Scrolls written: {len(out_scroll)}")
    print(f"Spellbooks written: {len(out_book)}")
    print(f"Spells written: {len(out_spells)}")


if __name__ == "__main__":
    main()
