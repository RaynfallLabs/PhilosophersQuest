"""
Generator D — Artifacts + Accessories rebalance.

Reads:
  data/items/artifact.json (~24 entries)
  data/items/accessory.json (~195 entries)

Writes:
  tools/balance/generated/uniques/artifacts/<id>.json   (one per artifact)
  tools/balance/generated/uniques/accessories/<id>.json (one per accessory)

Preserves names, lore, slots, equip_threshold, quiz_tier, special properties.
Rebalances weights (per briefing §4) and adds peak_floor/spread soft-spawn
curves replacing fixed min_level/max_level gates.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

# allow importing curve from sibling module
THIS = Path(__file__).resolve()
ROOT = THIS.parents[3]  # PhilosophersQuest/
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import curve  # noqa: E402

DATA_DIR = ROOT / "data" / "items"
OUT_ART = ROOT / "tools" / "balance" / "generated" / "uniques" / "artifacts"
OUT_ACC = ROOT / "tools" / "balance" / "generated" / "uniques" / "accessories"
OUT_ART.mkdir(parents=True, exist_ok=True)
OUT_ACC.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Artifact weight table (briefing §4 Quest Items + auditing the rest)
# --------------------------------------------------------------------------

ARTIFACT_WEIGHTS = {
    # Briefing-specified explicit weights
    "philosophers_stone":  1.0,
    "bronze_bull":         0.5,
    "ariadnes_thread":     0.1,
    "eye_of_graeae":       0.2,
    "leather_scrap":       0.3,   # 10 of these = 3.0 lb total
    "gleipnir":            0.1,   # the assembled ribbon
    # Gleipnir's six impossible components — each 0.2 lb
    "cats_footstep":       0.2,
    "womans_beard":        0.2,
    "mountain_root":       0.2,
    "fish_breath":         0.2,
    "bird_spittle":        0.2,
    "bear_sinew":          0.2,
    # Seven seals — small sigils, 0.1 each (shatter on demon kill per CSM §H.3)
    "seal_of_wrath":       0.1,
    "seal_of_pestilence":  0.1,
    "seal_of_famine":      0.1,
    "seal_of_war":         0.1,
    "seal_of_death":       0.1,
    "seal_of_earthquake":  0.1,
    "seal_of_silence":     0.1,
    # Other unique artifacts
    "scales_of_michael":   1.0,   # golden scales — meaningful weight
    "cursed_lodestone":   20.0,   # explicitly 20 lb per lore (cannot be put down)
    "sealed_dispatch":     2.0,   # iron-bound scroll case (was 8.0; over-stated)
    "palladium":           3.0,   # small wooden statue of Athena
    "tablet_of_destinies": 4.0,   # clay tablet with cuneiform
}


# --------------------------------------------------------------------------
# Spawn band → peak_floor / spread mapping for soft-spawn curves
# --------------------------------------------------------------------------

def spawn_curve(min_level: int) -> tuple[int, int, float]:
    """Return (peak_floor, spread, peak_weight) from a legacy min_level.
    Items spawn most commonly ~5 floors past their first plausible floor."""
    if min_level >= 9000:
        # Plot-locked items — they don't roll on the generic spawn table.
        # Mark with a sentinel so integration knows.
        return (0, 0, 0.0)
    peak = min_level + 5
    spread = max(8, int(min_level * 0.3) + 6)
    peak_weight = 0.4 if min_level < 30 else 0.3 if min_level < 60 else 0.2
    return (peak, spread, peak_weight)


# --------------------------------------------------------------------------
# Artifact special-properties detection
# --------------------------------------------------------------------------

def artifact_special_properties(aid: str, src: dict) -> dict:
    """Extract / annotate special mechanics for an artifact."""
    sp: dict = {}

    # Pass through any existing mechanic flags.
    for k in (
        "cursed",
        "identified",
        "stair_reveal",
        "quiz_reroll",
    ):
        if k in src:
            sp[k] = src[k]

    # Plot role inferred from id
    if aid == "philosophers_stone":
        sp["plot_role"] = "abaddon_drop_endgame_anchor"
        sp["effects"] = ["auto_identify", "death_kill_ritual_component", "score_bonus_50000"]
        sp["spawn_method"] = "boss_drop_abaddon"
    elif aid == "bronze_bull":
        sp["plot_role"] = "asterion_quest_layer1"
        sp["effects"] = ["pour_on_ariadne_fountain_defangs_asterion_phasing"]
        sp["spawn_method"] = "quest_spawn_pre_asterion"
    elif aid == "ariadnes_thread":
        sp["plot_role"] = "asterion_quest_layer1_companion"
        sp["effects"] = ["reveal_hidden_paths", "consumed_at_fountain"]
        sp["spawn_method"] = "quest_spawn_pre_asterion"
    elif aid == "eye_of_graeae":
        sp["plot_role"] = "medusa_quest_layer1"
        sp["effects"] = ["drop_on_athena_altar_produces_aegis"]
        sp["spawn_method"] = "quest_spawn_pre_medusa"
    elif aid in ("cats_footstep", "womans_beard", "mountain_root",
                 "fish_breath", "bird_spittle", "bear_sinew"):
        sp["plot_role"] = "fenrir_quest_layer1_gleipnir_component"
        sp["effects"] = ["forge_with_5_others_at_dwarven_forge_to_make_gleipnir"]
        sp["spawn_method"] = "quest_spawn_fenrir_components"
    elif aid == "gleipnir":
        sp["plot_role"] = "fenrir_quest_layer1_assembled"
        sp["effects"] = ["bind_fenrir_with_stat_tax_during_fight"]
        sp["spawn_method"] = "forge_assembled"
    elif aid == "leather_scrap":
        sp["plot_role"] = "fenrir_quest_layer2_vidars_sandal_component"
        sp["effects"] = ["10_assembled_at_vidars_altar_become_sandal"]
        sp["spawn_method"] = "quest_spawn_10_scattered_floors"
        sp["count_required"] = 10
    elif aid.startswith("seal_of_"):
        sp["plot_role"] = "seal_demon_drop"
        sp["effects"] = ["shatter_on_pickup_with_chronicle"]  # per CSM §H.3 fix
        sp["spawn_method"] = "seal_demon_drop"
    elif aid == "scales_of_michael":
        sp["plot_role"] = "abaddon_quest_layer4_heavenly_host"
        sp["effects"] = ["v_power_summon_angel_per_locust"]
        sp["spawn_method"] = "michael_gift_karma_1_to_9"
    elif aid == "cursed_lodestone":
        sp["plot_role"] = "knight_encounter_promise"
        sp["effects"] = ["heavy_20lb_cannot_drop_until_remove_curse"]
        sp["spawn_method"] = "npc_encounter_dying_knight"
    elif aid == "sealed_dispatch":
        sp["plot_role"] = "courier_promise"
        sp["effects"] = ["deliver_to_surface_for_karma_or_score"]
        sp["spawn_method"] = "npc_encounter_dying_courier"
    elif aid == "palladium":
        sp["plot_role"] = "wonder_relic"
        sp["effects"] = ["stair_reveal_while_carried"]
        sp["spawn_method"] = "random_lore_quest_mid_dungeon"
    elif aid == "tablet_of_destinies":
        sp["plot_role"] = "wonder_relic"
        sp["effects"] = ["one_quiz_reroll_per_floor_when_wrong"]
        sp["spawn_method"] = "random_lore_quest_deep_dungeon"

    return sp


# --------------------------------------------------------------------------
# Artifact builder
# --------------------------------------------------------------------------

def build_artifact(aid: str, src: dict) -> dict:
    out = {
        "id": aid,
        "name": src["name"],
        "category": "artifact",
        "is_unique": True,
        "symbol": src.get("symbol", "*"),
        "color": src.get("color", [200, 200, 200]),
        "weight_lb": ARTIFACT_WEIGHTS.get(aid, src.get("weight", 1.0)),
        "lore": src.get("lore", ""),
    }
    # Spawn config
    ml = src.get("min_level", 9999)
    peak, spread, pw = spawn_curve(ml)
    if ml >= 9000:
        out["min_level"] = 0  # plot-locked
        out["plot_locked"] = True
    else:
        out["min_level"] = ml
        out["peak_floor"] = peak
        out["spread"] = spread
        out["peak_weight"] = pw

    # Special properties
    sp = artifact_special_properties(aid, src)
    if sp:
        out["special_properties"] = sp

    return out


# --------------------------------------------------------------------------
# Accessory builder
# --------------------------------------------------------------------------

# Cap table per spawn floor band — keeps stat bonuses inside the AD&D-compressed
# scale. Existing data already mostly respects these; we audit and clamp the
# small number of outliers.
def stat_cap(stat: str, min_level: int) -> int:
    """Maximum +stat amount that an accessory can grant when it first plausibly
    spawns at this floor. AC is more constrained because it stacks with armor."""
    band_caps = {
        "AC":   [(1, 1), (15, 1), (25, 2), (40, 2), (50, 3), (75, 3), (101, 3)],
    }
    default = [(1, 2), (15, 2), (25, 3), (40, 4), (60, 4), (75, 5), (101, 5)]
    table = band_caps.get(stat, default)
    for floor_max, cap in table:
        if min_level <= floor_max:
            return cap
    return table[-1][1]


# Weight adjustments — a "Heavy Iron X" should be heavier; pure rings ~0
def calibrate_weight(aid: str, name: str, weight: float, slot: str) -> float:
    name_l = name.lower()
    if slot == "ring":
        if "heavy" in name_l or "iron" in name_l:
            return 0.3
        if weight > 0.2:
            return 0.1  # rings are negligible per briefing §4
        return 0.0 if weight < 0.05 else weight
    if slot == "amulet":
        if "heavy" in name_l or "pectoral" in name_l or "torque" in name_l or "menat" in name_l:
            return 0.3
        return min(0.2, weight) if weight > 0 else 0.1
    # Other accessory slots (cloak, boots, etc.) — accept 0.2-0.5
    if weight <= 0.0:
        return 0.2
    return min(0.5, max(0.1, weight))


def build_accessory(aid: str, src: dict) -> dict:
    name = src.get("name", aid)
    slot = src.get("slot", "ring")
    min_level = src.get("min_level", 1)
    effects = dict(src.get("effects") or {})

    # Clamp stat bonus amounts to curve cap.
    audit_notes = []
    for key in ("amount", "amount2", "second_amount"):
        stat_key = {"amount": "stat", "amount2": "stat2",
                    "second_amount": "second_stat"}[key]
        if key in effects and stat_key in effects:
            stat = effects[stat_key]
            cap = stat_cap(stat, min_level)
            if effects[key] > cap:
                audit_notes.append(
                    f"{stat}+{effects[key]} clamped to +{cap} per curve cap @ L{min_level}"
                )
                effects[key] = cap

    # Weight calibration
    weight = calibrate_weight(aid, name, src.get("weight", 0.1), slot)

    # Spawn curve
    if min_level >= 9000:
        peak, spread, pw = 0, 0, 0.0
        plot_locked = True
    else:
        peak, spread, pw = spawn_curve(min_level)
        plot_locked = False

    out = {
        "id": aid,
        "name": name,
        "category": "accessory",
        "is_unique": False,  # most accessories are templated; some unique
        "symbol": src.get("symbol", "="),
        "color": src.get("color", [200, 200, 200]),
        "slot": slot,
        "weight_lb": weight,
        "equip_threshold": src.get("equip_threshold", 2),
        "quiz_tier": src.get("quiz_tier", 1),
        "effects": effects,
        "lore": src.get("lore", ""),
    }
    if "unidentified_name" in src:
        out["unidentified_name"] = src["unidentified_name"]

    if plot_locked:
        out["min_level"] = 0
        out["plot_locked"] = True
    else:
        out["min_level"] = min_level
        out["peak_floor"] = peak
        out["spread"] = spread
        out["peak_weight"] = pw

    # Unique-feel detection: a proper-noun name (apostrophe-s or interior
    # capital letter) marks the item as a unique (one-of-a-kind drop). Pure
    # "ring of X" / "amulet of X" with lowercase suffix are templated.
    # "Amulet of Merlin" -> unique (Merlin is capitalized).
    has_capital_proper_noun = any(
        w[0].isupper() and len(w) > 2 for w in name.split()[1:]
    )
    has_apostrophe_s = "'s" in name or "'" in name
    if has_capital_proper_noun or has_apostrophe_s:
        out["is_unique"] = True

    if audit_notes:
        out["audit_notes"] = audit_notes

    # Curve cite for design review
    if min_level < 9000:
        out["curve_cite"] = {
            "player_hp_baseline_at_min_level": curve.player_hp_baseline(min_level),
            "player_ac_target_at_min_level":  curve.player_ac_target(min_level),
        }

    return out


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def main() -> None:
    art_src = json.loads((DATA_DIR / "artifact.json").read_text(encoding="utf-8"))
    acc_src = json.loads((DATA_DIR / "accessory.json").read_text(encoding="utf-8"))

    art_count = 0
    art_summary = []
    for aid, src in art_src.items():
        out = build_artifact(aid, src)
        path = OUT_ART / f"{aid}.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        art_count += 1
        art_summary.append((aid, out["weight_lb"], src.get("weight", "?")))

    acc_count = 0
    acc_audit_count = 0
    acc_weight_changes = 0
    for aid, src in acc_src.items():
        out = build_accessory(aid, src)
        if "audit_notes" in out:
            acc_audit_count += 1
        if abs(out["weight_lb"] - src.get("weight", 0)) > 0.01:
            acc_weight_changes += 1
        path = OUT_ACC / f"{aid}.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        acc_count += 1

    print(f"Artifacts written: {art_count}")
    print(f"Accessories written: {acc_count}")
    print(f"  with stat-cap clamps: {acc_audit_count}")
    print(f"  with weight changes: {acc_weight_changes}")
    print("\nArtifact weight audit (id, new, old):")
    for aid, new_w, old_w in art_summary:
        marker = " *" if new_w != old_w else ""
        print(f"  {aid:25s}  {new_w:>6.2f}  (was {old_w}){marker}")


if __name__ == "__main__":
    main()
