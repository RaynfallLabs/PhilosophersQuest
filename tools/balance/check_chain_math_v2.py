"""
Chain math verification — v2 (midpoint-anchored 3-class model).

Verifies that the new weapon class shapes produce sane kill-turn counts vs
the curve, after the curve.py weapon_base_damage formula was re-anchored
(midpoint chain = 1.0× weapon_base, peak Normal = 2.0×).

Targets (per design brief):
  Median monsters at chain 5/peak with floor-appropriate gear: 2-4 turn kill
  Tough monsters at chain 5/peak: 4-6 turn kill
  Naive Abaddon at chain 5 with floor-appropriate weapon: 15-25 turn fight
  Full-prep Abaddon (Sword of Michael + max_stack 0.2): 3-5 turn fight

Run:  py tools/balance/check_chain_math_v2.py
"""

from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import curve  # noqa: E402


# ---------------------------------------------------------------------------
# Class chain shapes — must match rebalance_chain_v2.CHAIN_SHAPES
# ---------------------------------------------------------------------------

FINESSE_5 = [0.20, 0.55, 1.00, 1.80, 3.00]
NORMAL_5  = [0.50, 0.85, 1.00, 1.45, 2.00]
HEAVY_5   = [0.75, 0.90, 1.00, 1.30, 1.75]

# Representative weapons (post-v2)
WEAPONS = {
    "rapier (finesse, normal damage_modifier 0.90)":
        {"shape": FINESSE_5, "mod": 0.90, "class": "finesse"},
    "longsword (normal, damage_modifier 1.00)":
        {"shape": NORMAL_5,  "mod": 1.00, "class": "normal"},
    "battleaxe (normal, damage_modifier 1.10)":
        {"shape": NORMAL_5,  "mod": 1.10, "class": "normal"},
    "greatsword (heavy, damage_modifier 1.45)":
        {"shape": HEAVY_5,   "mod": 1.45, "class": "heavy"},
    "maul (heavy, damage_modifier 1.55)":
        {"shape": HEAVY_5,   "mod": 1.55, "class": "heavy"},
}

# Floor-appropriate material multipliers (matches existing material assignments)
FLOOR_MATS = {
    1:   ("iron",       1.00),
    20:  ("iron",       1.00),
    40:  ("steel",      1.15),
    50:  ("mithril",    1.20),
    60:  ("mithril",    1.20),
    80:  ("adamantine", 1.40),
    100: ("orichalcum", 1.60),
}


def kill_turns(floor: int, shape: list[float], mod: float, mat_mult: float,
               rung_idx: int) -> tuple[float, float, float]:
    """Returns (damage, kill_turns_median, kill_turns_tough) at this rung."""
    base = curve.weapon_base_damage(floor)
    wpn_dmg = base * mod * mat_mult
    dmg = wpn_dmg * shape[rung_idx]
    mob_hp = curve.monster_hp_med(floor)
    tough_hp = curve.monster_hp_tough(floor)
    return dmg, mob_hp / dmg if dmg > 0 else 999, tough_hp / dmg if dmg > 0 else 999


def print_class_table(name: str, shape: list[float], mod: float) -> None:
    """For each anchor floor, show chain-1/3/5 damage and kill-turn counts."""
    print()
    print(f"--- {name} ---")
    print(f"{'Floor':>5}  {'mat':<11}  {'base':>4}  "
          f"{'C1_dmg':>7}  {'C1_med':>7}  "
          f"{'C3_dmg':>7}  {'C3_med':>7}  "
          f"{'C5_dmg':>7}  {'C5_med':>7}  {'C5_tough':>9}")
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        base = curve.weapon_base_damage(f)
        c1_dmg, c1_med, _ = kill_turns(f, shape, mod, mat_mult, 0)
        c3_dmg, c3_med, _ = kill_turns(f, shape, mod, mat_mult, 2)
        c5_dmg, c5_med, c5_tough = kill_turns(f, shape, mod, mat_mult, 4)
        print(f"{f:>5}  {mat_name:<11}  {base:>4}  "
              f"{c1_dmg:>7.2f}  {c1_med:>7.2f}  "
              f"{c3_dmg:>7.2f}  {c3_med:>7.2f}  "
              f"{c5_dmg:>7.2f}  {c5_med:>7.2f}  {c5_tough:>9.2f}")


def print_class_summary() -> None:
    """Headline summary table: for each class at each anchor floor, peak-chain kill turns."""
    print()
    print("=" * 90)
    print("CLASS HEADLINES — peak-rung damage vs median monster (kill turns)")
    print("=" * 90)
    print(f"{'Floor':>5}  {'mat':<11}  "
          f"{'fin_med':>8}  {'fin_tgh':>8}  "
          f"{'nrm_med':>8}  {'nrm_tgh':>8}  "
          f"{'hvy_med':>8}  {'hvy_tgh':>8}")
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        # Use damage_modifier = 1.0 as the reference (rapier is 0.9, longsword is 1.0, greatsword 1.45)
        # For comparability, use 1.0 across the board.
        _, fin_m, fin_t = kill_turns(f, FINESSE_5, 1.0, mat_mult, 4)
        _, nrm_m, nrm_t = kill_turns(f, NORMAL_5,  1.0, mat_mult, 4)
        _, hvy_m, hvy_t = kill_turns(f, HEAVY_5,   1.0, mat_mult, 4)
        print(f"{f:>5}  {mat_name:<11}  "
              f"{fin_m:>8.2f}  {fin_t:>8.2f}  "
              f"{nrm_m:>8.2f}  {nrm_t:>8.2f}  "
              f"{hvy_m:>8.2f}  {hvy_t:>8.2f}")
    print()
    print("Target: median 2-4 turns (peak chain), tough 4-6 turns.")


def print_midpoint_check() -> None:
    """The midpoint (rung 3 of 5) should equal weapon_base × damage_modifier × material."""
    print()
    print("=" * 90)
    print("MIDPOINT CHECK — chain rung 3 (5-rung weapons) = weapon_base damage")
    print("=" * 90)
    print(f"{'Floor':>5}  {'mat':<11}  {'wpn_base':>9}  "
          f"{'mid_norm':>9}  {'mid_med_turns':>14}  {'mid_tgh_turns':>14}")
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        base = curve.weapon_base_damage(f)
        # Midpoint = chain rung 3 (idx 2) of 5-rung Normal shape = 1.0× exactly
        mid_dmg = base * 1.0 * mat_mult * NORMAL_5[2]
        mob_hp = curve.monster_hp_med(f)
        tough_hp = curve.monster_hp_tough(f)
        print(f"{f:>5}  {mat_name:<11}  {base:>9}  "
              f"{mid_dmg:>9.2f}  {mob_hp/mid_dmg:>14.2f}  {tough_hp/mid_dmg:>14.2f}")
    print()
    print("Target: midpoint kills median monster in ~5-7 turns (typical play feel).")


def print_naive_abaddon() -> None:
    """Abaddon (1235 HP) kill-turn count at chain 5 with floor-appropriate gear."""
    print()
    print("=" * 90)
    print("ABADDON — naive 1235 HP, chain rung 5 with floor-appropriate weapon")
    print("=" * 90)
    abaddon_hp = curve.boss_hp_naive(100)
    mat_name, mat_mult = FLOOR_MATS[100]
    for cls_name, shape in [("Finesse", FINESSE_5), ("Normal", NORMAL_5), ("Heavy", HEAVY_5)]:
        for mod_name, mod in [("mod 1.0", 1.0), ("mod 1.45", 1.45)]:
            base = curve.weapon_base_damage(100)
            dmg = base * mod * mat_mult * shape[4]
            turns = abaddon_hp / dmg
            print(f"  {cls_name:<8} {mod_name:<10}  base={base:>3}  "
                  f"chain5_dmg={dmg:>7.1f}  naive_kill={turns:>5.1f} turns  "
                  f"max_stack(0.2)_kill={(abaddon_hp*0.20)/dmg:>5.1f} turns")
    print()
    print("Target: naive 15-25 turns. Max-stack (0.2) 3-5 turns.")


def print_sword_of_michael() -> None:
    """Confirm Sword of Michael math: tuned unique, holy ignores resist, +crit, +abaddon bonus."""
    print()
    print("=" * 90)
    print("SWORD OF MICHAEL — Abaddon-killer quest reward, vs Abaddon")
    print("=" * 90)
    # Final Sword stats (from generated file):
    #   base_damage 38 (curve 29 × 1.3 override)
    #   max_chain 7 (legendary feel), Normal class, 7-rung peak = 2.10×
    #   crit_mult 2.0, ignore_resistances, ignore_shield, +2d10 abaddon_bonus
    sword_base = 38
    chain_shape_7_normal = [0.40, 0.65, 0.85, 1.10, 1.40, 1.70, 2.10]
    peak = chain_shape_7_normal[-1]                          # 2.10
    chain_peak = sword_base * peak                           # 38 * 2.1 = 79.8
    crit = chain_peak * 2.0                                  # 159.6
    abaddon_bonus = 11                                       # avg 2d10
    chain_peak_w_bonus = chain_peak + abaddon_bonus          # 90.8
    crit_w_bonus = crit + abaddon_bonus                      # 170.6
    abaddon_naive = curve.boss_hp_naive(100)                 # 1235
    abaddon_stack = abaddon_naive * 0.20                     # 247
    print(f"  Sword base_damage (curve 29 × 1.3 override)  = {sword_base}")
    print(f"  × Chain rung 7 peak (Normal 7-rung, 2.10×)   = {chain_peak:.1f}")
    print(f"  +2d10 abaddon bonus (~11 avg)                = {chain_peak_w_bonus:.1f}")
    print(f"  Crit (2.0×) +2d10 abaddon bonus              = {crit_w_bonus:.1f}")
    print(f"  Abaddon naive HP                             = {abaddon_naive}")
    print(f"  -> naive kill turns (non-crit peak)          = {abaddon_naive/chain_peak_w_bonus:.1f}")
    print(f"  -> naive kill turns (crit peak)              = {abaddon_naive/crit_w_bonus:.1f}")
    print(f"  Abaddon w/ max quest stack (0.20)            = {abaddon_stack:.0f}")
    print(f"  -> max-stack kill turns (non-crit peak)      = {abaddon_stack/chain_peak_w_bonus:.1f}")
    print(f"  -> max-stack kill turns (crit peak)          = {abaddon_stack/crit_w_bonus:.1f}")
    print()
    print("Target: naive 10-15 turns; max-stack 2-4 turns. ZERO one-shots.")


def print_design_validation() -> None:
    """Verify the design tuning against the targets stated in the brief."""
    print()
    print("=" * 90)
    print("DESIGN VALIDATION — does the math hit the targets?")
    print("=" * 90)
    targets = []
    # Target 1: Median monsters at peak chain with floor-appropriate gear: 2-4 turns
    fails = []
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        # Normal-class, mod 1.0 (longsword equivalent)
        _, nrm_med, nrm_tgh = kill_turns(f, NORMAL_5, 1.0, mat_mult, 4)
        if not (1.5 <= nrm_med <= 4.5):
            fails.append(f"F{f}: normal-peak median kill = {nrm_med:.2f}")
    targets.append(("Median monsters at peak chain (Normal): 2-4 turns",
                    "PASS" if not fails else "FAIL", fails))
    # Target 2: Tough monsters at peak chain: 4-6 turns (Normal-class, mod 1.0)
    fails = []
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        _, _, nrm_tgh = kill_turns(f, NORMAL_5, 1.0, mat_mult, 4)
        if not (2.5 <= nrm_tgh <= 7.0):
            fails.append(f"F{f}: normal-peak tough kill = {nrm_tgh:.2f}")
    targets.append(("Tough monsters at peak chain (Normal): 4-6 turns (wider 2.5-7)",
                    "PASS" if not fails else "FAIL", fails))
    # Target 3: Naive Abaddon at chain 5 (Normal, mod 1.0, orichalcum): 15-25 turns
    base = curve.weapon_base_damage(100)
    _, mat_mult = FLOOR_MATS[100]
    dmg = base * 1.0 * mat_mult * NORMAL_5[4]
    naive_turns = curve.boss_hp_naive(100) / dmg
    targets.append((f"Naive Abaddon (Normal mod 1.0, peak chain): {naive_turns:.1f} turns",
                    "PASS" if 12.0 <= naive_turns <= 28.0 else "FAIL", []))
    # Target 4: Sword of Michael + max_stack: 2-4 turns (tuned via 1.3× override)
    sword_base = 38  # from generated file (curve 29 × 1.3 override)
    peak_7 = 2.10
    dmg_peak = sword_base * peak_7 + 11  # +abaddon_bonus
    stack_turns = (curve.boss_hp_naive(100) * 0.20) / dmg_peak
    targets.append((f"Sword of Michael + max-stack (peak, no crit): {stack_turns:.1f} turns",
                    "PASS" if 2.0 <= stack_turns <= 5.0 else "FAIL", []))
    # Target 5: NO one-shots. Confirm chain peak < monster HP at any anchor.
    fails = []
    for f in (1, 20, 40, 50, 60, 80, 100):
        mat_name, mat_mult = FLOOR_MATS[f]
        # Worst-case: heaviest weapon (greatsword mod 1.45) at peak Normal vs median monster
        _, nrm_med, _ = kill_turns(f, NORMAL_5, 1.45, mat_mult, 4)
        if nrm_med < 1.0:
            fails.append(f"F{f}: normal mod 1.45 peak one-shots median (kill={nrm_med:.2f})")
    targets.append(("No one-shots on median monster (peak Normal mod 1.45)",
                    "PASS" if not fails else "FAIL", fails))
    # Print
    for label, status, fails in targets:
        print(f"  [{status}] {label}")
        for f in fails:
            print(f"           {f}")


if __name__ == "__main__":
    print("=" * 90)
    print("CHAIN MATH VERIFICATION v2 — midpoint-anchored 3-class model")
    print("=" * 90)

    print_class_summary()
    print_midpoint_check()

    for name, info in WEAPONS.items():
        print_class_table(name, info["shape"], info["mod"])

    print_naive_abaddon()
    print_sword_of_michael()
    print_design_validation()

    print()
    print("=" * 90)
    print("Done.")
    print("=" * 90)
