"""Sample-instantiate armor combos and verify against curve.player_ac_target.

Usage:  py tools/balance/generated/_validate_armor.py

The curve.player_ac_target(floor) function returns the AC target for the
"prepared" (P) player profile. The body-armor contribution should be
roughly HALF of the total AC swing from F1 to F100; the rest comes from
shield + helm + hands + feet + cloak + DEX + enchants.

We validate:
  1. Each combo's body+shield+enchant numbers.
  2. The MINIMUM other-kit + DEX needed to hit curve target with this body+shield.
  3. Whether that's plausible for the P profile vs SL profile.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAL = HERE.parent
sys.path.insert(0, str(BAL))
import curve  # noqa: E402

TEMPLATES_DIR = HERE / "templates" / "armor"
SHIELDS_DIR = HERE / "templates" / "shields"
MATERIALS_DIR = HERE / "materials" / "armor"


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    armor = {p.stem: load(p) for p in TEMPLATES_DIR.glob("*.json")}
    shields = {p.stem: load(p) for p in SHIELDS_DIR.glob("*.json")}
    mats = {p.stem: load(p) for p in MATERIALS_DIR.glob("*.json")}

    print("=" * 100)
    print(" ARMOR/SHIELD/MATERIAL — validation vs curve.player_ac_target")
    print("=" * 100)
    print(f"templates: body={len(armor)}  shield={len(shields)}  materials={len(mats)}")
    print()
    print("AC math: final_AC = 10 - (body_AC + shield_AC + other_kit_AC + DEX_AC + enchants_extra)")
    print("  body_AC   = body_template.base_ac_value + body_material.ac_bonus + body_enchant")
    print("  shield_AC = shield_template.base_ac_value + shield_material.ac_bonus + shield_enchant")
    print()

    # Each row: a body+shield combo at a floor. P profile = no enchants, modest gear.
    # We compute the AC contribution from body+shield and ask: how much remaining stack
    # (other slots + DEX) does the player need to hit the curve target?
    combos = [
        ("F3   light early",   "leather",    "leather",     3,  "buckler",      "leather"),
        ("F30  mid heavy",     "chainmail",  "chain_steel", 30, "heavy_wooden", "chain_steel"),
        ("F75  high light",    "full_plate", "mithril",     75, "kite_shield",  "mithril"),
        ("F95  high heavy",    "full_plate", "adamantine",  95, "tower_shield", "adamantine"),
    ]

    print(f"{'combo':<20} {'body':<28} {'shield':<26} "
          f"{'b_AC':>5} {'s_AC':>5} {'wt(lb)':>7} {'target':>6} {'remain':>6}  {'verdict'}")
    print("-" * 130)
    for label, body_t, body_m, floor, sh_t, sh_m in combos:
        bt = armor[body_t]; bm = mats[body_m]
        st = shields[sh_t]; sm = mats[sh_m]

        # No enchants (P profile, found-as-is)
        body_ac = bt["base_ac_value"] + bm["ac_bonus"]
        sh_ac = st["base_ac_value"] + sm["ac_bonus"]
        b_wt = bt["base_weight_lb"] * bm["weight_mult"]
        s_wt = st["base_weight_lb"] * sm["weight_mult"]
        target = curve.player_ac_target(floor)

        # Remaining stack needed: 10 - target - body_ac - shield_ac
        remain = 10 - target - body_ac - sh_ac

        # Sanity bands: how much remaining stack is "plausible" for prepared player?
        # F1-19 prepared: helm+1 + DEX+1 = 2  (~2)
        # F20-39 prepared: helm+1 + DEX+2 + hands/feet+1 = 4  (~3-4)
        # F40-59 prepared: helm+2 + hands+1 + feet+1 + cloak+1 + DEX+2 = 7  (~5-7)
        # F60-79 prepared: above + enchants = 9  (~7-9)
        # F80-100 prepared: full kit + enchants = 11  (~9-12)
        plausible = {
            3:  (1, 3),
            30: (3, 5),
            75: (7, 10),
            95: (10, 13),
        }[floor]

        if plausible[0] <= remain <= plausible[1]:
            verdict = "OK (prepared player hits target)"
        elif remain < plausible[0]:
            verdict = f"BODY+SHIELD TOO STRONG (only {remain} needed, plausible {plausible[0]}-{plausible[1]})"
        else:
            verdict = f"BODY+SHIELD TOO WEAK ({remain} needed, plausible {plausible[0]}-{plausible[1]})"

        body_desc = f"{body_t}+{body_m}"
        sh_desc = f"{sh_t}+{sh_m}"
        print(f"{label:<20} {body_desc:<28} {sh_desc:<26} "
              f"{body_ac:>5} {sh_ac:>5} {b_wt + s_wt:>7.1f} "
              f"{target:>+6} {remain:>+6}  {verdict}")

    print()
    print("Interpretation: 'remain' = how many AC points must come from helm/hands/feet/cloak/DEX/enchants")
    print("for the player to hit the curve's prepared-profile target. If remain is within the plausible band,")
    print("body+shield numbers are well-tuned.")
    print()

    # Weight sanity
    print("Weight sanity (F95 prepared player STR 14, ~150 lb max carry, ~75 lb light load):")
    print(f"  F95 full_plate+adamantine + tower_shield+adamantine = "
          f"{armor['full_plate']['base_weight_lb'] * mats['adamantine']['weight_mult']:.1f} + "
          f"{shields['tower_shield']['base_weight_lb'] * mats['adamantine']['weight_mult']:.1f} = "
          f"{armor['full_plate']['base_weight_lb'] * mats['adamantine']['weight_mult'] + shields['tower_shield']['base_weight_lb'] * mats['adamantine']['weight_mult']:.1f} lb")
    print(f"  F75 full_plate+mithril + kite_shield+mithril = "
          f"{armor['full_plate']['base_weight_lb'] * mats['mithril']['weight_mult']:.1f} + "
          f"{shields['kite_shield']['base_weight_lb'] * mats['mithril']['weight_mult']:.1f} = "
          f"{armor['full_plate']['base_weight_lb'] * mats['mithril']['weight_mult'] + shields['kite_shield']['base_weight_lb'] * mats['mithril']['weight_mult']:.1f} lb")
    print(f"  F30 chainmail+chain_steel + heavy_wooden+chain_steel = "
          f"{armor['chainmail']['base_weight_lb'] * mats['chain_steel']['weight_mult']:.1f} + "
          f"{shields['heavy_wooden']['base_weight_lb'] * mats['chain_steel']['weight_mult']:.1f} = "
          f"{armor['chainmail']['base_weight_lb'] * mats['chain_steel']['weight_mult'] + shields['heavy_wooden']['base_weight_lb'] * mats['chain_steel']['weight_mult']:.1f} lb")


if __name__ == "__main__":
    main()
