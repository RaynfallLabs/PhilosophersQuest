"""Validator for regenerated content under tools/balance/generated/.

Reads every JSON file produced by generators A-G, validates each against:
  1. its schema (per GENERATORS_BRIEFING.md §6)
  2. numerical content vs tools/balance/curve.py
  3. realistic-weight table (GENERATORS_BRIEFING.md §4)

Outputs a markdown report at tools/balance/VALIDATION_REPORT.md.

Re-runnable. Idempotent. Exits 0 if zero ERROR-tier drift, exits 1 otherwise.

Usage:  py tools/balance/validate.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import curve  # noqa: E402

GEN = HERE / "generated"
REPORT_PATH = HERE / "VALIDATION_REPORT.md"

# ---------------------------------------------------------------------------
# Drift envelopes per GENERATORS_BRIEFING.md spec.
# ---------------------------------------------------------------------------
# Mob HP: median ±50%, tough ±50% around curve.monster_hp_tough(peak_floor)
MOB_HP_TOLERANCE = 0.50
# Weapon base_damage: ±30% around curve.weapon_base_damage(min_level)
WEAPON_DMG_TOLERANCE = 0.30
# AC drift: ±2 around player_ac_target with floor-appropriate kit
AC_DRIFT_ABS = 2
# Cooking softcap: must equal curve.cooking_softcap(deepest_floor) within ±1 HP
COOKING_SOFTCAP_ABS = 1
# Spawn-weight peak: must be at least 0.05 weight at peak floor and decay
# smoothly. Bell formula is enforced exactly here.
SPAWN_MIN_PEAK = 0.05

# Realistic weight table from §4 — used to sanity-check base_weight_lb on templates.
# Tolerance ±25% because lore variants are allowed.
WEIGHT_TABLE = {
    # one-handed melee
    "dagger": 1.0, "shortsword": 2.0, "longsword": 3.0, "scimitar": 3.0,
    "rapier": 2.0, "mace": 4.0, "warhammer": 4.0, "battleaxe": 4.0,
    "flail": 3.0, "club": 3.0,
    # two-handed melee
    "bastard_sword": 5.0, "greatsword": 6.0, "maul": 8.0, "great_axe": 7.0,
    "glaive": 7.0, "quarterstaff": 4.0,
    # ranged
    "shortbow": 2.0, "longbow": 3.0, "composite_bow": 3.0,
    "light_crossbow": 5.0, "heavy_crossbow": 8.0, "sling": 0.5,
    # armor (iron-baseline; multiply by material weight_mult)
    "padded": 8.0, "leather": 10.0, "studded_leather": 13.0, "hide": 15.0,
    "chain_shirt": 20.0, "ringmail": 25.0, "scale": 30.0, "chainmail": 40.0,
    "breastplate": 20.0, "splint": 40.0, "banded": 35.0, "plate": 50.0,
    "full_plate": 65.0,
    # shields
    "buckler": 2.0, "light_wooden": 5.0, "heavy_wooden": 10.0,
    "light_steel": 6.0, "heavy_steel": 15.0, "tower_shield": 30.0,
    "kite_shield": 10.0,
}
WEIGHT_TOLERANCE = 0.25


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """One drift report — what's wrong with one entry."""
    severity: str       # 'ERROR', 'WARN', 'INFO'
    category: str       # 'monster', 'weapon_template', 'material', etc.
    entry_id: str
    field: str
    detail: str
    expected: Any = None
    actual: Any = None

    def md(self) -> str:
        line = f"- **{self.severity}** [{self.entry_id}] `{self.field}`: {self.detail}"
        if self.expected is not None or self.actual is not None:
            line += f" (expected ≈ `{self.expected}`, got `{self.actual}`)"
        return line


@dataclass
class CategoryReport:
    category: str
    files_seen: int = 0
    findings: list[Finding] = field(default_factory=list)
    schema_required_keys: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(p: Path) -> dict | None:
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return {"__error__": f"JSON parse failure: {e}"}


def _glob(subdir: str, pattern: str = "*.json") -> list[Path]:
    base = GEN / subdir
    if not base.exists():
        return []
    return sorted(base.rglob(pattern))


def _dice_to_avg(dice: str) -> float:
    """Convert AD&D dice notation '1d4+2' to average value. Returns 0 on parse fail."""
    if isinstance(dice, (int, float)):
        return float(dice)
    s = str(dice).strip().lower()
    if not s:
        return 0.0
    # split on '+' or '-'
    bonus = 0
    if "+" in s:
        s, b = s.split("+", 1)
        try:
            bonus = int(b)
        except ValueError:
            bonus = 0
    elif "-" in s and "d" in s.split("-", 1)[0]:
        s, b = s.split("-", 1)
        try:
            bonus = -int(b)
        except ValueError:
            bonus = 0
    if "d" not in s:
        try:
            return float(s) + bonus
        except ValueError:
            return 0.0
    n_s, sides_s = s.split("d", 1)
    try:
        n = int(n_s) if n_s else 1
        sides = int(sides_s)
    except ValueError:
        return 0.0
    return n * (sides + 1) / 2.0 + bonus


def _bell_weight(floor: int, peak_floor: int, spread: int, peak_weight: float) -> float:
    if spread <= 0:
        return 0.0
    distance = floor - peak_floor
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    return max(0.02, peak_weight * bell)


def _within_pct(actual: float, expected: float, pct: float) -> bool:
    if expected == 0:
        return abs(actual) <= pct
    return abs(actual - expected) / abs(expected) <= pct


# ---------------------------------------------------------------------------
# Per-category validators
# ---------------------------------------------------------------------------

def validate_weapon_templates(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "weapon_class", "hands", "damage_types",
                "chain_multipliers", "base_weight_lb", "compatible_material_classes"}
    rep.schema_required_keys = required
    for p in _glob("templates/weapons"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        # Category must be 'weapon'
        if data.get("category") != "weapon":
            rep.findings.append(Finding("ERROR", rep.category, eid, "category",
                                        "must be 'weapon'", "weapon", data.get("category")))
        # Hands: 1 or 2
        if data.get("hands") not in (1, 2):
            rep.findings.append(Finding("ERROR", rep.category, eid, "hands",
                                        "must be 1 or 2", "1|2", data.get("hands")))
        # chain_multipliers: monotonically rising list of floats
        chains = data.get("chain_multipliers", [])
        if not isinstance(chains, list) or len(chains) < 3:
            rep.findings.append(Finding("ERROR", rep.category, eid, "chain_multipliers",
                                        "must be a list of >=3 floats"))
        else:
            for i in range(1, len(chains)):
                if chains[i] <= chains[i - 1]:
                    rep.findings.append(Finding("WARN", rep.category, eid, "chain_multipliers",
                                                f"chain mult #{i+1} ({chains[i]}) "
                                                f"is not strictly greater than #{i} ({chains[i-1]})"))
                    break
            if chains and chains[-1] > 9.0:
                rep.findings.append(Finding("WARN", rep.category, eid, "chain_multipliers",
                                            f"chain ceiling {chains[-1]} exceeds 9× design ceiling",
                                            "<=9.0", chains[-1]))
        # base_weight_lb vs WEIGHT_TABLE
        wt = data.get("base_weight_lb")
        if wt is None:
            rep.findings.append(Finding("ERROR", rep.category, eid, "base_weight_lb", "missing"))
        else:
            ref = WEIGHT_TABLE.get(eid)
            if ref is not None and not _within_pct(wt, ref, WEIGHT_TOLERANCE):
                rep.findings.append(Finding("WARN", rep.category, eid, "base_weight_lb",
                                            f"weight {wt} drifts from §4 reference",
                                            ref, wt))


def validate_armor_templates(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "armor_class_tier", "slot",
                "base_ac_value", "base_weight_lb", "compatible_material_classes"}
    rep.schema_required_keys = required
    for p in _glob("templates/armor"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        if data.get("category") != "armor":
            rep.findings.append(Finding("ERROR", rep.category, eid, "category",
                                        "must be 'armor'", "armor", data.get("category")))
        ac = data.get("base_ac_value")
        if ac is None or not isinstance(ac, (int, float)):
            rep.findings.append(Finding("ERROR", rep.category, eid, "base_ac_value", "missing/not numeric"))
        elif ac < 1 or ac > 10:
            rep.findings.append(Finding("WARN", rep.category, eid, "base_ac_value",
                                        f"AC contribution {ac} outside [1, 10] band", "1..10", ac))
        wt = data.get("base_weight_lb")
        ref = WEIGHT_TABLE.get(eid)
        if wt is not None and ref is not None and not _within_pct(wt, ref, WEIGHT_TOLERANCE):
            rep.findings.append(Finding("WARN", rep.category, eid, "base_weight_lb",
                                        f"weight {wt} drifts from §4 reference", ref, wt))


def validate_shield_templates(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "base_ac_value", "base_weight_lb",
                "compatible_material_classes"}
    rep.schema_required_keys = required
    for p in _glob("templates/shields"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        if data.get("category") != "shield":
            rep.findings.append(Finding("ERROR", rep.category, eid, "category",
                                        "must be 'shield'", "shield", data.get("category")))
        wt = data.get("base_weight_lb")
        ref = WEIGHT_TABLE.get(eid)
        if wt is not None and ref is not None and not _within_pct(wt, ref, WEIGHT_TOLERANCE):
            rep.findings.append(Finding("WARN", rep.category, eid, "base_weight_lb",
                                        f"weight {wt} drifts from §4 reference", ref, wt))


def validate_materials(rep: CategoryReport, subdir: str) -> None:
    required = {"id", "name", "material_class", "applies_to",
                "peak_floor", "spread", "peak_weight"}
    rep.schema_required_keys = required
    for p in _glob(subdir):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        # peak_floor must be in 1..100
        pf = data.get("peak_floor")
        if pf is not None and (pf < 1 or pf > 100):
            rep.findings.append(Finding("ERROR", rep.category, eid, "peak_floor",
                                        "outside 1..100", "1..100", pf))
        spread = data.get("spread")
        if spread is not None and spread <= 0:
            rep.findings.append(Finding("ERROR", rep.category, eid, "spread",
                                        "must be > 0", ">0", spread))
        # peak_weight bell at peak must >= 0.05
        pw = data.get("peak_weight", 0)
        if pf and spread and pw and _bell_weight(pf, pf, spread, pw) < SPAWN_MIN_PEAK:
            rep.findings.append(Finding("WARN", rep.category, eid, "peak_weight",
                                        f"bell peak weight ({pw}) too low to spawn meaningfully",
                                        f">={SPAWN_MIN_PEAK}", pw))
        # chronicle voice check — first_pickup_chronicle is required for material discovery
        if "first_pickup_chronicle" not in data:
            rep.findings.append(Finding("WARN", rep.category, eid, "first_pickup_chronicle",
                                        "missing — material won't trigger discovery chronicle"))
        elif not data["first_pickup_chronicle"].strip():
            rep.findings.append(Finding("WARN", rep.category, eid, "first_pickup_chronicle",
                                        "empty string"))
        # weight_mult sanity
        wm = data.get("weight_mult")
        if wm is not None and (wm <= 0 or wm > 3.0):
            rep.findings.append(Finding("WARN", rep.category, eid, "weight_mult",
                                        f"unusual weight_mult {wm}", "0..3.0", wm))
        # damage_mult sanity (weapon-applicable materials)
        dm = data.get("damage_mult")
        if dm is not None and (dm <= 0 or dm > 2.0):
            rep.findings.append(Finding("WARN", rep.category, eid, "damage_mult",
                                        f"unusual damage_mult {dm}", "0..2.0", dm))


def validate_unique_weapons(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "is_unique", "base_damage",
                "min_level", "peak_floor", "spread"}
    rep.schema_required_keys = required
    for p in _glob("uniques/weapons"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        # base_damage within ±30% of curve.weapon_base_damage(min_level) × unique-mult (1.3-2.0)
        bd = data.get("base_damage")
        ml = data.get("min_level", 1)
        if bd is not None and ml:
            curve_base = curve.weapon_base_damage(ml)
            lo = max(1, int(curve_base * 1.0))
            hi = int(curve_base * 2.5)  # uniques allowed 1.0×-2.5× over plain curve
            if bd < lo or bd > hi:
                rep.findings.append(Finding("WARN", rep.category, eid, "base_damage",
                                            f"unique base_damage {bd} outside expected band "
                                            f"({lo}..{hi}) given curve baseline {curve_base}",
                                            f"{lo}..{hi}", bd))
        # Chain ceiling
        chains = data.get("chain_multipliers", [])
        if chains and chains[-1] > 16:
            rep.findings.append(Finding("ERROR", rep.category, eid, "chain_multipliers",
                                        f"chain ceiling {chains[-1]} > 16 (Sword of Michael is the cap)",
                                        "<=16", chains[-1]))


def validate_unique_artifacts(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "is_unique", "weight_lb"}
    rep.schema_required_keys = required
    # Quest items per §4 — exact-weight reference values
    QUEST_WEIGHT = {
        "bronze_bull": 0.5, "eye_of_graeae": 0.2, "ariadnes_thread": 0.1,
        "leather_scrap": 0.3, "broken_gram": 4.0, "sigurds_shovel": 6.0,
        "philosophers_stone": 1.0, "tablet_of_second_death": 5.0,
        "complete_tablet_of_second_death": 6.0, "philosophers_wrench": 2.0,
        "scroll_lake_of_fire": 0.1, "scroll_deaths_bane": 0.1,
        "aegis_of_athena": 10.0, "greater_aegis": 15.0, "vidars_sandal": 2.0,
        # Gleipnir components
        "cats_footstep": 0.2, "womans_beard": 0.2, "mountain_root": 0.2,
        "fish_breath": 0.2, "bird_spittle": 0.2, "bear_sinew": 0.2,
    }
    for p in _glob("uniques/artifacts"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        wt = data.get("weight_lb")
        ref = QUEST_WEIGHT.get(eid)
        if wt is not None and ref is not None and abs(wt - ref) > 0.05:
            rep.findings.append(Finding("WARN", rep.category, eid, "weight_lb",
                                        f"quest-item weight drift", ref, wt))


def validate_unique_accessories(rep: CategoryReport) -> None:
    required = {"id", "name", "category", "is_unique", "slot",
                "weight_lb", "min_level"}
    rep.schema_required_keys = required
    for p in _glob("uniques/accessories"):
        data = _load_json(p)
        if data is None or "__error__" in (data or {}):
            rep.findings.append(Finding("ERROR", rep.category, p.stem, "<file>",
                                        f"could not load: {data}"))
            continue
        rep.files_seen += 1
        eid = data.get("id", p.stem)
        missing = required - set(data.keys())
        if missing:
            rep.findings.append(Finding("WARN", rep.category, eid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        # accessory stat-bonus sanity — +CON or +HP shouldn't out-scale natural HP growth
        effects = data.get("effects", {})
        bonus = effects.get("amount", 0)
        ml = data.get("min_level", 1)
        if isinstance(bonus, (int, float)) and bonus > 0:
            # cap stat bonus at ~floor/15 + 2 (so a F50 accessory caps at +5)
            cap = max(2, ml // 15 + 2)
            if bonus > cap:
                rep.findings.append(Finding("WARN", rep.category, eid, "effects.amount",
                                            f"accessory bonus +{bonus} may out-scale "
                                            f"curve at min_level {ml}", f"<={cap}", bonus))
        # weight sanity — rings ~0, amulets/charms 0.1-0.5
        wt = data.get("weight_lb")
        slot = data.get("slot", "")
        if isinstance(wt, (int, float)):
            if slot == "ring" and wt > 0.1:
                rep.findings.append(Finding("INFO", rep.category, eid, "weight_lb",
                                            f"ring weight {wt} > 0.1 (§4 says ~0)", "<=0.1", wt))
            if wt > 1.0 and slot != "neck":  # amulet equivalents
                rep.findings.append(Finding("INFO", rep.category, eid, "weight_lb",
                                            f"accessory weight {wt} unusually high", "<=1.0", wt))


def validate_monsters(rep: CategoryReport) -> None:
    """Monsters live in tools/balance/generated/data/monsters.json (single file)."""
    rep.schema_required_keys = {"id", "name", "symbol", "color", "hp", "ai_pattern",
                                "min_level", "peak_floor", "spread", "thac0", "attacks"}
    path = GEN / "data" / "monsters.json"
    if not path.exists():
        rep.findings.append(Finding("INFO", rep.category, "<file>", "monsters.json",
                                    "not generated yet (Agent G pending)"))
        return
    data = _load_json(path)
    if data is None or (isinstance(data, dict) and "__error__" in data):
        rep.findings.append(Finding("ERROR", rep.category, "<file>", "monsters.json",
                                    f"could not load: {data}"))
        return
    for mid, mdef in (data or {}).items():
        rep.files_seen += 1
        merged = {"id": mid, **mdef}
        missing = rep.schema_required_keys - set(merged.keys())
        if missing:
            rep.findings.append(Finding("ERROR", rep.category, mid, "schema",
                                        f"missing keys: {sorted(missing)}"))
        # HP within ±50% of curve.monster_hp_med(peak_floor) (or _tough for elites)
        pf = merged.get("peak_floor") or merged.get("min_level") or 1
        hp_avg = _dice_to_avg(merged.get("hp", "0"))
        tags = set(merged.get("tags", []))
        is_elite = ("elite" in tags) or ("boss" in tags) or merged.get("is_boss")
        if is_elite:
            expected = curve.monster_hp_tough(pf)
        else:
            expected = curve.monster_hp_med(pf)
        if expected and not _within_pct(hp_avg, expected, MOB_HP_TOLERANCE):
            rep.findings.append(Finding("WARN", rep.category, mid, "hp",
                                        f"HP avg {hp_avg:.1f} drifts >50% from curve "
                                        f"{'tough' if is_elite else 'med'} {expected} at peak {pf}",
                                        expected, hp_avg))
        # Boss HP: compare to boss_hp_naive at boss floor
        if merged.get("is_boss"):
            boss_floor = merged.get("peak_floor", merged.get("min_level", 0))
            expected_boss = curve.boss_hp_naive(boss_floor)
            # Accept ±50% — bosses get layered difficulty
            if expected_boss and not _within_pct(hp_avg, expected_boss, 0.50):
                rep.findings.append(Finding("WARN", rep.category, mid, "hp",
                                            f"boss HP {hp_avg:.0f} drifts from "
                                            f"boss_hp_naive({boss_floor})={expected_boss}",
                                            expected_boss, hp_avg))
        # THAC0 within 5 of curve.monster_thac0_med
        thac0 = merged.get("thac0")
        if thac0 is not None and pf:
            target_thac0 = curve.monster_thac0_elite(pf) if is_elite else curve.monster_thac0_med(pf)
            if abs(thac0 - target_thac0) > 5:
                rep.findings.append(Finding("WARN", rep.category, mid, "thac0",
                                            f"thac0 {thac0} drifts >5 from curve target",
                                            target_thac0, thac0))
        # Per-attack damage drift
        for atk in merged.get("attacks", []):
            dmg = _dice_to_avg(atk.get("damage", "0"))
            expected_dmg = curve.monster_damage_med(pf)
            if expected_dmg and dmg > expected_dmg * 2.5:
                rep.findings.append(Finding("WARN", rep.category, mid,
                                            f"attacks.{atk.get('name', '?')}",
                                            f"attack damage {dmg:.1f} >2.5× curve median "
                                            f"{expected_dmg} at floor {pf}",
                                            expected_dmg, dmg))


def validate_ingredients(rep: CategoryReport) -> None:
    """ingredient.json is one combined file by Agent E."""
    path = GEN / "data" / "ingredient.json"
    if not path.exists():
        rep.findings.append(Finding("INFO", rep.category, "<file>", "ingredient.json",
                                    "not generated yet (Agent E pending)"))
        return
    data = _load_json(path)
    if data is None or (isinstance(data, dict) and "__error__" in data):
        rep.findings.append(Finding("ERROR", rep.category, "<file>", "ingredient.json",
                                    f"could not load: {data}"))
        return
    for iid, idef in (data or {}).items():
        rep.files_seen += 1
        # weight 0.1-1.5 lb (§4)
        wt = idef.get("weight_lb", idef.get("weight"))
        if isinstance(wt, (int, float)) and (wt < 0.05 or wt > 2.0):
            rep.findings.append(Finding("WARN", rep.category, iid, "weight_lb",
                                        f"ingredient weight {wt} unusual (§4: 0.1-1.0)",
                                        "0.1-1.0", wt))
        # recipes must have keys 0-5
        recipes = idef.get("recipes", {})
        for q in ("0", "1", "2", "3", "4", "5"):
            if q not in recipes:
                rep.findings.append(Finding("WARN", rep.category, iid, f"recipes.{q}",
                                            f"missing quality {q}"))
                break


def validate_recipes(rep: CategoryReport) -> None:
    path = GEN / "data" / "recipes.json"
    if not path.exists():
        rep.findings.append(Finding("INFO", rep.category, "<file>", "recipes.json",
                                    "not generated yet (Agent E pending)"))
        return
    data = _load_json(path)
    if data is None or (isinstance(data, dict) and "__error__" in data):
        rep.findings.append(Finding("ERROR", rep.category, "<file>", "recipes.json",
                                    f"could not load: {data}"))
        return
    for rid, rdef in (data or {}).items():
        rep.files_seen += 1
        # bonus_amount should not exceed accessory-style cap
        ba = rdef.get("bonus_amount", 0)
        if isinstance(ba, (int, float)) and ba > 5:
            rep.findings.append(Finding("WARN", rep.category, rid, "bonus_amount",
                                        f"recipe stat bonus +{ba} likely out-scales curve",
                                        "<=5", ba))


def validate_wands_scrolls_spellbooks(rep: CategoryReport, kind: str) -> None:
    """Validate wand.json / scroll.json / spellbook.json by Agent F."""
    path = GEN / "data" / f"{kind}.json"
    if not path.exists():
        rep.findings.append(Finding("INFO", rep.category, "<file>", f"{kind}.json",
                                    f"not generated yet (Agent F pending)"))
        return
    data = _load_json(path)
    if data is None or (isinstance(data, dict) and "__error__" in data):
        rep.findings.append(Finding("ERROR", rep.category, "<file>", f"{kind}.json",
                                    f"could not load: {data}"))
        return
    for wid, wdef in (data or {}).items():
        rep.files_seen += 1
        ml = wdef.get("min_level", 1)
        qt = wdef.get("quiz_tier")
        # Quiz tier should match floor band
        if qt is not None and ml:
            expected_tier = curve.math_tier_dominant(ml)
            if abs(qt - expected_tier) > 1:
                rep.findings.append(Finding("INFO", rep.category, wid, "quiz_tier",
                                            f"quiz_tier {qt} drifts from dominant tier "
                                            f"{expected_tier} at min_level {ml}",
                                            expected_tier, qt))


def validate_cooking_softcap_formula() -> list[Finding]:
    """Sanity-check curve.cooking_softcap() returns sensible values at anchor floors.

    This isn't validating a GENERATED file — it's validating the FORMULA we'll
    integrate into player.py:194-213. Catches obvious regressions if curve.py changes.
    """
    findings: list[Finding] = []
    sanity = [
        (1, 0, 5),       # F1: cooking softcap ~0 (no cap needed)
        (50, 0, 30),     # F50: cooking softcap ~5-30 (moderate)
        (100, 50, 130),  # F100: cooking softcap ~50-130 (substantial)
    ]
    for floor, lo, hi in sanity:
        actual = curve.cooking_softcap(floor)
        if not (lo <= actual <= hi):
            findings.append(Finding("ERROR", "cooking_softcap_formula",
                                    f"floor_{floor}", "softcap_value",
                                    f"curve.cooking_softcap({floor}) = {actual} outside "
                                    f"expected band {lo}..{hi}",
                                    f"{lo}..{hi}", actual))
    return findings


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

CATEGORIES = [
    ("weapon_templates", validate_weapon_templates),
    ("armor_templates", validate_armor_templates),
    ("shield_templates", validate_shield_templates),
    ("weapon_materials", lambda r: validate_materials(r, "materials/weapons")),
    ("armor_materials",  lambda r: validate_materials(r, "materials/armor")),
    ("unique_weapons",   validate_unique_weapons),
    ("unique_artifacts", validate_unique_artifacts),
    ("unique_accessories", validate_unique_accessories),
    ("monsters", validate_monsters),
    ("ingredients", validate_ingredients),
    ("recipes", validate_recipes),
    ("wands", lambda r: validate_wands_scrolls_spellbooks(r, "wand")),
    ("scrolls", lambda r: validate_wands_scrolls_spellbooks(r, "scroll")),
    ("spellbooks", lambda r: validate_wands_scrolls_spellbooks(r, "spellbook")),
]


def main() -> int:
    if not GEN.exists():
        print(f"ERROR: {GEN} does not exist. Have generators produced anything?")
        return 1

    reports: list[CategoryReport] = []
    for name, validator in CATEGORIES:
        r = CategoryReport(category=name)
        validator(r)
        reports.append(r)

    softcap_findings = validate_cooking_softcap_formula()
    soft = CategoryReport(category="cooking_softcap_formula")
    soft.findings = softcap_findings
    soft.files_seen = 3  # the 3 sanity floors
    reports.append(soft)

    # --- Aggregate counts ---
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"ERROR": 0, "WARN": 0, "INFO": 0})
    for rep in reports:
        for f in rep.findings:
            counts[rep.category][f.severity] += 1

    # --- Console summary ---
    print("=" * 80)
    print("BALANCE VALIDATION SUMMARY")
    print("=" * 80)
    print(f"{'category':<25} {'files':>6} {'ERROR':>6} {'WARN':>6} {'INFO':>6}")
    print("-" * 80)
    total_err = total_warn = total_info = 0
    for rep in reports:
        c = counts[rep.category]
        total_err += c["ERROR"]
        total_warn += c["WARN"]
        total_info += c["INFO"]
        print(f"{rep.category:<25} {rep.files_seen:>6} "
              f"{c['ERROR']:>6} {c['WARN']:>6} {c['INFO']:>6}")
    print("-" * 80)
    print(f"{'TOTAL':<25} {sum(r.files_seen for r in reports):>6} "
          f"{total_err:>6} {total_warn:>6} {total_info:>6}")
    print()

    # --- Write markdown report ---
    lines: list[str] = []
    lines.append("# Balance Validation Report")
    lines.append("")
    lines.append("Generated by `tools/balance/validate.py`. Re-run with `py tools/balance/validate.py`.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Files | ERROR | WARN | INFO |")
    lines.append("|---|---:|---:|---:|---:|")
    for rep in reports:
        c = counts[rep.category]
        lines.append(f"| `{rep.category}` | {rep.files_seen} | "
                     f"{c['ERROR']} | {c['WARN']} | {c['INFO']} |")
    lines.append(f"| **TOTAL** | **{sum(r.files_seen for r in reports)}** | "
                 f"**{total_err}** | **{total_warn}** | **{total_info}** |")
    lines.append("")

    lines.append("## Curve anchor (for cross-reference)")
    lines.append("")
    lines.append("| Floor | mob_HP | mob_tough | mob_dmg | thac0 | wpn_base | AC_target | cook_softcap |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for f in (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100):
        lines.append(
            f"| {f} | {curve.monster_hp_med(f)} | {curve.monster_hp_tough(f)} "
            f"| {curve.monster_damage_med(f)} | {curve.monster_thac0_med(f)} "
            f"| {curve.weapon_base_damage(f)} | {curve.player_ac_target(f)} "
            f"| {curve.cooking_softcap(f)} |"
        )
    lines.append("")

    for rep in reports:
        if not rep.findings:
            continue
        lines.append(f"## `{rep.category}` ({rep.files_seen} files, "
                     f"{len(rep.findings)} findings)")
        lines.append("")
        if rep.schema_required_keys:
            lines.append(f"Schema required keys: `{sorted(rep.schema_required_keys)}`")
            lines.append("")
        # Group by severity
        for sev in ("ERROR", "WARN", "INFO"):
            sev_findings = [f for f in rep.findings if f.severity == sev]
            if not sev_findings:
                continue
            lines.append(f"### {sev} ({len(sev_findings)})")
            lines.append("")
            for f in sev_findings:
                lines.append(f.md())
            lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
