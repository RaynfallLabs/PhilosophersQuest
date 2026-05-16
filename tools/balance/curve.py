"""
The Unified Balance Curve — single source of truth for Philosopher's Quest.

EVERYTHING derives from these functions. Content generators read from here.
The validator reads from here. Run this module directly to print the curve
table at each anchor floor.

NO anchoring to current data. Every number is derived from design constants
that you can tune at the top of this file.

Run:  py tools/balance/curve.py
"""

from __future__ import annotations
import math

# ===========================================================================
# Design constants — the tunable axes of the entire game balance.
# Adjusting any of these reshapes the whole curve.
# ===========================================================================

# --- Floor structure --------------------------------------------------------
TOTAL_FLOORS               = 100   # Stone Level
EARLY_BREAKPOINT           = 20    # boundary between early-game and main-game curves
                                   # (Asterion floor — when "tutorial" ends)

# --- Monster HP growth (AD&D-feel COMPRESSED scaling) -----------------------
# A floor-1 monster is a giant rat (HP ~4). A floor-100 monster is a balor or
# ancient dragon (HP ~175). The whole range stays in AD&D-classic numbers.
MONSTER_HP_F1              = 4     # giant rat at floor 1
MONSTER_HP_EARLY_RATE      = 1.10  # 10% compound growth F1-F20 (rats -> minotaurs)
MONSTER_HP_MID_RATE        = 1.025 # 2.5% compound growth F21-F100 (variety > inflation)

# --- Monster damage ---------------------------------------------------------
# Per-hit damage. AD&D dragons do 1d8 to 4d8 per attack (avg 5-18).
MONSTER_DMG_TO_HP_RATIO    = 0.12  # avg damage per hit = ~12% of monster HP

# --- Monster THAC0 ---------------------------------------------------------
# AD&D: legendary monsters cap around THAC0 -8 to -10. NOT -22.
MONSTER_THAC0_F1           = 19    # AD&D 1-HD monster accuracy
MONSTER_THAC0_F100         = -10   # AD&D ancient-dragon-tier accuracy

# --- Player tension ---------------------------------------------------------
# How many monster hits to kill the player. Tunes the variance corridor.
TENSION_KILLS_TO_DIE_P     = 6     # prepared player dies in ~6 hits
TENSION_KILLS_TO_DIE_SL    = 9     # skilled+lucky player dies in ~9 hits
TENSION_KILLS_TO_DIE_UP    = 3     # unprepared player dies in ~3 hits

# --- Player HP baseline (stat-only) ----------------------------------------
# Stat HP from CON gains, accessories, scrolls. Modest. AD&D-fighter feel.
# Cooking is the main HP track; this is the floor under it.
PLAYER_HP_BASE_F1          = 12    # base HP at start (CON 10 + AD&D-feel base)
PLAYER_HP_BASE_F100        = 50    # stat-only HP at L100 with accessories

# --- Cooking softcap --------------------------------------------------------
# Cooking is the leveling track. Softcap = (target HP for prepared player) - stat HP.
COOKING_DIMINISHING_FLOOR  = 0.20  # below this multiplier, gains stagnate

# --- Player weapon damage ---------------------------------------------------
# Chain design: rung 3 (midpoint) = 1.0× weapon_base. weapon_base IS the
# realistic per-hit damage. The chain produces skill-driven variance:
#   Finesse:  [0.20, 0.55, 1.00, 1.80, 3.00]  — slow ramp, big spike
#   Normal:   [0.50, 0.85, 1.00, 1.45, 2.00]  — flat workhorse
#   Heavy:    [0.75, 0.90, 1.00, 1.30, 1.75]  — front-loaded, max triggers SPECIAL
KILL_TURNS_TARGET_PREPARED   = 3     # ~3-turn kills for prepared player at chain 5
WEAPON_CHAIN_MIDPOINT_MULT   = 1.0   # rung 3 of a 5-rung chain = base damage
WEAPON_CHAIN_PEAK_MULT_NORMAL = 2.0  # rung 5 of a Normal-class weapon

# --- AC progression --------------------------------------------------------
# AD&D: best-ever AC stack around -14 to -18. NOT -34.
PLAYER_AC_F1               = 9     # leather / studded leather feel
PLAYER_AC_F100             = -14   # full magical-plate-and-shield stack

# --- Boss difficulty multipliers -------------------------------------------
BOSS_HP_MULT_BASE          = 6.0   # baseline boss (Asterion)
BOSS_HP_MULT_GROWTH        = 1.04  # later bosses spike slightly harder

# Boss kill-turn target for PREPARED player at math tier matching the boss.
BOSS_KILL_TURNS_TARGET     = 20

# --- Quest layer multipliers (uniform across bosses; per-boss tweaks in data) ---
QUEST_LAYER_LIGHT          = 0.70  # one minor layer (LOS pillars, arena tactic)
QUEST_LAYER_MODERATE       = 0.50  # one major quest layer (Thread, Blindfold, pit)
QUEST_LAYER_HEAVY          = 0.35  # mega-secret single layer (Reforged Gram, Vidar)
QUEST_LAYER_MAX_STACK      = 0.20  # full prep with multiple layers compounded

# --- Math tier bands -------------------------------------------------------
MATH_TIER_BANDS            = [
    (1, 19, 1),      # F1-19: T1 dominant
    (20, 39, 2),     # F20-39: T2 dominant
    (40, 59, 3),     # F40-59: T3 dominant
    (60, 79, 4),     # F60-79: T4 dominant
    (80, 100, 5),    # F80-100: T5 dominant
]


# ===========================================================================
# Derived curves — every function below derives from the constants above.
# Do not edit values here; edit the constants.
# ===========================================================================

def _floor(x: int) -> int:
    """Round toward zero, never below 1."""
    return max(1, int(x))


def monster_hp_med(floor: int) -> int:
    """Median normal monster HP at the given dungeon level."""
    floor = max(1, min(TOTAL_FLOORS, floor))
    if floor <= EARLY_BREAKPOINT:
        return _floor(MONSTER_HP_F1 * (MONSTER_HP_EARLY_RATE ** (floor - 1)))
    early_cap = MONSTER_HP_F1 * (MONSTER_HP_EARLY_RATE ** (EARLY_BREAKPOINT - 1))
    mid = early_cap * (MONSTER_HP_MID_RATE ** (floor - EARLY_BREAKPOINT))
    return _floor(mid)


def monster_hp_tough(floor: int) -> int:
    """75th-percentile (the 'wall' monster) HP at the floor."""
    return _floor(monster_hp_med(floor) * 1.6)


def monster_damage_med(floor: int) -> int:
    """Median damage per monster hit at the floor."""
    return max(1, _floor(monster_hp_med(floor) * MONSTER_DMG_TO_HP_RATIO))


def monster_damage_tough(floor: int) -> int:
    """Max damage per monster hit (the dangerous spike)."""
    return max(1, _floor(monster_hp_tough(floor) * MONSTER_DMG_TO_HP_RATIO * 1.3))


def monster_thac0_med(floor: int) -> int:
    """Median monster THAC0. Smooth interpolation from F1 to F100."""
    floor = max(1, min(TOTAL_FLOORS, floor))
    progress = (floor - 1) / (TOTAL_FLOORS - 1)
    thac0 = MONSTER_THAC0_F1 + (MONSTER_THAC0_F100 - MONSTER_THAC0_F1) * progress
    return int(round(thac0))


def monster_thac0_elite(floor: int) -> int:
    """Elite monsters have THAC0 4 points better than median."""
    return monster_thac0_med(floor) - 4


def player_hp_baseline(floor: int) -> int:
    """Stat-only HP (no cooking) — what a non-cooking player has at this floor."""
    floor = max(1, min(TOTAL_FLOORS, floor))
    progress = (floor - 1) / (TOTAL_FLOORS - 1)
    hp = PLAYER_HP_BASE_F1 + (PLAYER_HP_BASE_F100 - PLAYER_HP_BASE_F1) * progress
    return int(round(hp))


def player_hp_target(floor: int, profile: str = 'P') -> int:
    """Target effective HP for a player at floor.
    profile: 'UP' (unprepared), 'P' (prepared), 'SL' (skilled+lucky).
    Never below the stat-only baseline (you can't have less than your stat HP)."""
    kills_target = {
        'UP': TENSION_KILLS_TO_DIE_UP,
        'P':  TENSION_KILLS_TO_DIE_P,
        'SL': TENSION_KILLS_TO_DIE_SL,
    }[profile]
    derived = monster_damage_med(floor) * kills_target
    return max(player_hp_baseline(floor), _floor(derived))


def cooking_softcap(deepest_floor: int) -> int:
    """Maximum HP gain from cooking, derived from monster threat at deepest floor reached.
    This REPLACES the broken flat 1000 cap. Descent unlocks higher ceilings.
    Can be 0 on early floors where stat HP alone satisfies the tension target."""
    target = player_hp_target(deepest_floor, profile='P')
    stat = player_hp_baseline(deepest_floor)
    return max(0, target - stat)


def cooking_softcap_max(deepest_floor: int) -> int:
    """Maximum HP for the SKILLED+LUCKY profile (the extra slack diligent cooks get)."""
    target = player_hp_target(deepest_floor, profile='SL')
    stat = player_hp_baseline(deepest_floor)
    return max(0, target - stat)


def player_chain_5_damage(floor: int) -> int:
    """Target damage per hit at chain rung 5 with floor-appropriate weapon."""
    return _floor(monster_hp_med(floor) / KILL_TURNS_TARGET_PREPARED)


def weapon_base_damage(min_level: int) -> int:
    """Base damage of a weapon with this min_level. Chain midpoint (rung 3) deals
    exactly this — base IS the realistic per-hit damage. Chain peak (rung 5, normal
    class) deals 2.0×; finesse 3.0×; heavy 1.75× plus a special mechanic trigger.
    Derived: weapon_base × peak_mult × kill_turns = monster_hp_med, so
             weapon_base = monster_hp_med / (peak_mult × kill_turns) = mob_HP / 6."""
    return max(1, _floor(monster_hp_med(min_level) / (WEAPON_CHAIN_PEAK_MULT_NORMAL * KILL_TURNS_TARGET_PREPARED)))


def player_ac_target(floor: int) -> int:
    """Target AC for prepared player at floor (with floor-appropriate armor stack)."""
    floor = max(1, min(TOTAL_FLOORS, floor))
    progress = (floor - 1) / (TOTAL_FLOORS - 1)
    ac = PLAYER_AC_F1 + (PLAYER_AC_F100 - PLAYER_AC_F1) * progress
    return int(round(ac))


def boss_hp_naive(boss_floor: int) -> int:
    """Base boss HP for a boss at the given floor (NAIVE / NO quest prep)."""
    band_idx = boss_floor // 20  # 1=Asterion, 2=Medusa, 3=Fafnir, 4=Fenrir, 5=Abaddon
    mult = BOSS_HP_MULT_BASE * (BOSS_HP_MULT_GROWTH ** (band_idx - 1))
    return _floor(monster_hp_med(boss_floor) * mult)


def boss_hp_effective(boss_floor: int, quest_layer_stack: float) -> int:
    """Effective boss HP after applying compounded quest layer multiplier (0.20-1.0)."""
    return _floor(boss_hp_naive(boss_floor) * quest_layer_stack)


def math_tier_dominant(floor: int) -> int:
    """Math tier dominant at this floor (T1-T5)."""
    for lo, hi, tier in MATH_TIER_BANDS:
        if lo <= floor <= hi:
            return tier
    return 5


def tension_proxy_pct(floor: int) -> float:
    """Estimated % of monsters at this floor that can 2-shot an unprepared player.
    Reflects 'tension floor' — should never be too close to 0."""
    up_hp = player_hp_target(floor, profile='UP')
    tough_dmg = monster_damage_tough(floor)
    if tough_dmg * 2 >= up_hp:
        return 0.30  # at least the 75th-percentile-tough monsters can 2-shot
    elif monster_damage_med(floor) * 2 >= up_hp:
        return 0.15
    return 0.05


# ===========================================================================
# Anchor table printer
# ===========================================================================

ANCHOR_FLOORS = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
BOSS_FLOORS   = {20: 'Asterion', 40: 'Medusa', 60: 'Fafnir', 80: 'Fenrir', 100: 'Abaddon'}


def print_anchor_table() -> None:
    """Print the curve table at each anchor floor for design review."""
    print("=" * 100)
    print(" UNIFIED BALANCE CURVE — anchor floor table")
    print("=" * 100)
    print()
    header = (f"{'Floor':>6}  {'Math':>5}  "
              f"{'mob_HP':>7}  {'tough':>6}  {'dmg':>4}  {'thac0':>5}  "
              f"{'pl_stat':>7}  {'pl_P_HP':>8}  {'pl_SL_HP':>8}  "
              f"{'cook_P':>7}  {'cook_SL':>8}  "
              f"{'chain5':>7}  {'wpn_base':>9}  {'pl_AC':>6}  "
              f"{'tension':>8}")
    print(header)
    print("-" * len(header))
    for f in ANCHOR_FLOORS:
        row = (
            f"{f:>6}  T{math_tier_dominant(f):>3}  "
            f"{monster_hp_med(f):>7}  {monster_hp_tough(f):>6}  "
            f"{monster_damage_med(f):>4}  {monster_thac0_med(f):>5}  "
            f"{player_hp_baseline(f):>7}  {player_hp_target(f, 'P'):>8}  "
            f"{player_hp_target(f, 'SL'):>8}  "
            f"{cooking_softcap(f):>7}  {cooking_softcap_max(f):>8}  "
            f"{player_chain_5_damage(f):>7}  {weapon_base_damage(f):>9}  "
            f"{player_ac_target(f):>6}  "
            f"{tension_proxy_pct(f):>7.0%}"
        )
        boss = BOSS_FLOORS.get(f)
        if boss:
            row += f"  <-- {boss}"
        print(row)
    print()
    print("Bosses (naive HP -- multiply by quest_layer_stack for effective HP):")
    print(f"  {'Boss':<15} {'Floor':>5}  {'naive_HP':>9}  {'with_light':>11}  "
          f"{'with_mod':>9}  {'with_heavy':>11}  {'max_stack':>10}")
    for f, name in BOSS_FLOORS.items():
        naive = boss_hp_naive(f)
        print(f"  {name:<15} {f:>5}  {naive:>9}  "
              f"{boss_hp_effective(f, QUEST_LAYER_LIGHT):>11}  "
              f"{boss_hp_effective(f, QUEST_LAYER_MODERATE):>9}  "
              f"{boss_hp_effective(f, QUEST_LAYER_HEAVY):>11}  "
              f"{boss_hp_effective(f, QUEST_LAYER_MAX_STACK):>10}")
    print()
    print("Legend:")
    print("  mob_HP/tough/dmg/thac0   normal monster stats (median + 75th-pct)")
    print("  pl_stat                  player stat-only HP (no cooking)")
    print("  pl_P_HP / pl_SL_HP       player target HP (Prepared / Skilled+Lucky)")
    print("  cook_P / cook_SL         cooking softcap (HP cap added by cooking)")
    print("  chain5                   target player damage per hit at chain rung 5")
    print("  wpn_base                 weapon base damage for items at this min_level")
    print("  pl_AC                    target AC for prepared player armor stack")
    print("  tension                  % of monsters that can 2-shot an unprepared player")
    print()
    print("Boss kill-turn projections (PREPARED player at math tier matching boss):")
    print(f"  Naive boss = {BOSS_KILL_TURNS_TARGET}-turn fight if quest layers are zero")
    print(f"  Light layer ({QUEST_LAYER_LIGHT})  -> {int(BOSS_KILL_TURNS_TARGET * QUEST_LAYER_LIGHT)}-turn fight")
    print(f"  Mod layer ({QUEST_LAYER_MODERATE})    -> {int(BOSS_KILL_TURNS_TARGET * QUEST_LAYER_MODERATE)}-turn fight")
    print(f"  Heavy layer ({QUEST_LAYER_HEAVY})  -> {int(BOSS_KILL_TURNS_TARGET * QUEST_LAYER_HEAVY)}-turn fight")
    print(f"  Max stack ({QUEST_LAYER_MAX_STACK})    -> {int(BOSS_KILL_TURNS_TARGET * QUEST_LAYER_MAX_STACK)}-turn fight")


if __name__ == '__main__':
    print_anchor_table()
