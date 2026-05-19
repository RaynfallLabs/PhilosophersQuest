"""Rebuild unique weapon baseDamage to the new chain-5-anchored formula, and
apply signature chain shapes to a curated set of named legendaries.

Run once. Output is written back to data/items/weapon.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEAPON_FILE = ROOT / "data" / "items" / "weapon.json"

# Template damage_modifier table (from prompt; copied here so this script is
# self-contained and doesn't depend on the live template files for the 22
# standard templates). Six template_basis values used by uniques have no
# template file on disk (crossbow, handaxe, morningstar, net, spear, unarmed);
# we map those to sensible nearest-equivalent values.
TEMPLATE_DMG_MOD: dict[str, float] = {
    "bastard_sword":  1.15,
    "battleaxe":      1.10,
    "club":           0.70,
    "composite_bow":  1.15,
    "dagger":         0.70,
    "flail":          1.10,
    "glaive":         1.35,
    "great_axe":      1.50,
    "greatsword":     1.45,
    "heavy_crossbow": 1.40,
    "light_crossbow": 1.10,
    "longbow":        1.00,
    "longsword":      1.00,
    "mace":           1.05,
    "maul":           1.55,
    "quarterstaff":   0.85,
    "rapier":         0.90,
    "scimitar":       1.00,
    "shortbow":       0.80,
    "shortsword":     0.85,
    "sling":          0.60,
    "warhammer":      1.40,
    # No template file on disk -- pick nearest equivalent so the formula has a
    # value to multiply by. These choices documented for traceability.
    "crossbow":       1.10,  # treat as light_crossbow analogue
    "handaxe":        1.00,  # battleaxe minus a notch
    "morningstar":    1.10,  # like flail
    "net":            0.50,  # ensnaring tool, low raw damage
    "spear":          1.15,  # between rapier (0.9) and glaive (1.35)
    "unarmed":        0.50,  # fist
}


# Signature chains for curated uniques. Each entry maps unique_id -> (chain, note)
# where chain is exactly 5 floats and note is appended to design_notes.
# Keep within the prompt's 25-30 cap; restraint matters.
SIGNATURE_CHAINS: dict[str, tuple[list[float], str]] = {
    "excalibur": (
        [1.0, 1.5, 2.0, 3.0, 5.0],
        "Signature chain: the king's killing blow -- chain-1 already a meaningful "
        "cut (1.0x), then a steep climb to a legendary peak of 5.0x at chain-5.",
    ),
    "soul_reaver": (
        [0.2, 0.55, 1.0, 1.8, 3.0],
        "Signature chain: finesse opener; the blade hesitates on the first cut "
        "(0.2x) and only commits once it tastes blood. Lifesteal makes the long "
        "ramp viable.",
    ),
    "gae_bulg": (
        [1.0, 1.3, 1.6, 2.0, 2.5],
        "Signature chain: the never-miss spear of Cu Chulainn -- chain-1 is "
        "already a confirmed kill (1.0x), and every rung climbs cleanly. No "
        "weak openers, no dramatic peak; the spear simply lands.",
    ),
    "mjolnir_shard": (
        [0.8, 1.0, 1.2, 1.6, 2.5],
        "Signature chain: heavy with thunder peak -- a chip of the hammer keeps "
        "the weight even when broken. NOTE: chain-5 should trigger a lightning "
        "status proc; requires combat.py wiring.",
    ),
    "anduril": (
        [0.7, 1.0, 1.3, 1.8, 2.5],
        "Signature chain: the Flame of the West -- a bright, steady ramp. Each "
        "rung is meaningful; no dead opener.",
    ),
    "glamdring": (
        [0.7, 1.0, 1.3, 1.8, 2.5],
        "Signature chain: the Foe-hammer -- a bright, steady ramp like Anduril. "
        "Goblin-bane reliability over flashy peaks.",
    ),
    "stormbringer": (
        # Reduce 5-rung shape; keep current camel-case array shape with peak-3
        # finesse vibe so the signature is the chain-5 effect, not the curve.
        [0.5, 0.85, 1.2, 1.7, 2.4],
        "Signature: chain-5 drains the victim's soul (lifesteal-style heal). "
        "Requires combat.py wiring for the soul-steal proc; chain curve here is "
        "the runesword's tempered finesse profile.",
    ),
    "boomstick": (
        [0.5, 0.9, 1.2, 1.8, 3.5],
        "Signature chain: explosive peak -- chain-5 triggers an AOE/shotgun "
        "spread. Requires combat.py wiring for the AOE. peak_floor=0 so "
        "baseDamage is special-cased (not formula-derived).",
    ),
    "aiglos": (
        [0.8, 1.1, 1.4, 1.8, 2.4],
        "Signature chain: Elendil's spear -- steady, reliable, no surprises. "
        "Every rung climbs by ~0.3x; the spear keeps its word.",
    ),
    "zireael": (
        [0.4, 0.7, 1.0, 1.6, 2.8],
        "Signature chain: Swallow, the witcher's blade -- fast finesse opener "
        "(0.4x) with a sharp closing peak. Rewards the chain.",
    ),
    "ruyi_jingu_bang": (
        [0.6, 1.0, 1.5, 2.5, 4.0],
        "Signature chain: the As-You-Will Cudgel -- starts modest, then expands "
        "to a climactic spike at chain-5 (4.0x). Sun Wukong's staff grows with "
        "intent.",
    ),
    "heracles_club": (
        [1.0, 1.0, 1.5, 2.5, 4.0],
        "Signature chain: the Olive-Club -- first hits crush evenly (1.0x, "
        "1.0x), then break into a huge peak. Heracles never warms up; he "
        "finishes.",
    ),
}


def mob_hp(peak_floor: int) -> float:
    if peak_floor <= 20:
        return 4 * (1.10 ** (peak_floor - 1))
    early_cap = 4 * (1.10 ** 19)
    return early_cap * (1.025 ** (peak_floor - 20))


def compute_base_damage(entry: dict, chain_for_calc: list | None = None) -> int | None:
    """Return the new baseDamage per the chain-5-anchored formula, or None
    if the entry should be skipped (peak_floor <= 0)."""
    pf = int(entry.get("peak_floor", 0))
    if pf <= 0:
        return None
    cm = chain_for_calc
    if cm is None:
        cm = entry.get("chainMultipliers") or entry.get("chain_multipliers")
    if not cm:
        return None
    chain_5 = float(cm[-1])
    if chain_5 <= 0:
        return None
    dmg_mod = entry.get("damage_modifier")
    if dmg_mod is None:
        dmg_mod = TEMPLATE_DMG_MOD.get(entry.get("template_basis"), 1.0)
    dmg_mult = float(entry.get("damage_mult", 1.0))
    weapon_base = max(1, round(mob_hp(pf) / chain_5))
    base_damage = max(2, round(weapon_base * dmg_mult * float(dmg_mod)))
    return base_damage


def append_design_note(entry: dict, note: str) -> None:
    existing = entry.get("design_notes")
    if existing:
        # Avoid double-appending if rerun
        if note.split(" -- ")[0] in existing:
            return
        entry["design_notes"] = f"{existing}\n\n{note}"
    else:
        entry["design_notes"] = note


def main() -> None:
    data = json.loads(WEAPON_FILE.read_text(encoding="utf-8"))

    edited = 0
    skipped = []
    signature_applied = []

    for key, entry in data.items():
        # Step 1: apply signature chain edit first (so baseDamage computes from
        # the new chain_5 value).
        if key in SIGNATURE_CHAINS:
            new_chain, note = SIGNATURE_CHAINS[key]
            entry["chainMultipliers"] = list(new_chain)
            append_design_note(entry, note)
            signature_applied.append(key)

        # Step 2: rebuild baseDamage from formula.
        new_bd = compute_base_damage(entry)
        if new_bd is None:
            skipped.append((key, int(entry.get("peak_floor", 0))))
            continue
        entry["baseDamage"] = new_bd
        edited += 1

    WEAPON_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Edited baseDamage on {edited} uniques.")
    print(f"Skipped {len(skipped)} (peak_floor<=0):")
    for k, pf in skipped:
        print(f"  - {k} (peak_floor={pf})")
    print(f"\nApplied signature chains to {len(signature_applied)} uniques:")
    for k in signature_applied:
        cm = data[k]["chainMultipliers"]
        print(f"  - {k}: chainMultipliers={cm} baseDamage={data[k].get('baseDamage')}")


if __name__ == "__main__":
    main()
