"""Floor anchor curve: what an ordinary monster looks like on a given floor.

Median HP and typical damage per hit, by floor. They began as the CURVE.md
section 4 anchors and were re-scaled in the 2026-10 balance pass against
simulated runs (tools/balance/apply_difficulty_schedule.py has the schedule
and the reasons: tougher and harder-hitting at the top of the dungeon, lighter
at the bottom, where tier-5 sums already slow every kill). Monster data is
seated against these by tools/balance/respawn_by_hp.py; runtime code that has
to invent a foe for a floor (the bones ghost) reads them here so it scales
with the dungeon. tests/test_spawn_curve.py checks the two copies agree.
"""
from __future__ import annotations

import math

HP_ANCHORS = {1: 22, 10: 79, 20: 231, 30: 481, 40: 903, 50: 1412, 60: 2246,
              70: 3372, 80: 4928, 90: 6188, 100: 6912}
DMG_ANCHORS = {1: 1.19, 10: 2.19, 20: 2.87, 30: 6.13, 40: 13.97, 50: 22.85, 60: 32.9,
               70: 35.79, 80: 38.01, 90: 39.59, 100: 41.26}


def _interp(anchors: dict, floor: float) -> float:
    ks = sorted(anchors)
    floor = max(ks[0], min(ks[-1], floor))
    for a, b in zip(ks, ks[1:]):
        if a <= floor <= b:
            t = (floor - a) / (b - a)
            return math.exp(math.log(anchors[a]) * (1 - t) + math.log(anchors[b]) * t)
    return float(anchors[ks[-1]])


def target_hp(floor: float) -> float:
    """Median HP of an ordinary monster on `floor`."""
    return _interp(HP_ANCHORS, floor)


# The HP anchors as first written (CURVE.md section 4), before any re-sizing.
# Kept only to measure how far the dungeon's numbers have moved since.
ORIGINAL_HP_ANCHORS = {1: 8, 10: 21, 20: 55, 30: 110, 40: 210, 50: 325, 60: 500,
                       70: 750, 80: 1100, 90: 1400, 100: 1600}


def power_scale(floor: float) -> float:
    """How much bigger an ordinary monster's HP is on `floor` than it was when
    the game's FIXED damage numbers were written (about x3 near the top of
    the dungeon, x5 to x6 deep).

    Weapon damage follows monster HP through the material tables, and spells
    and wands through MAGIC_TIER_MULT. Everything else that hurts a monster
    by a fixed amount (a thrown potion, a pet's bite, a hero power, a trap,
    a weapon's bonus dice, a scroll) was sized for the old numbers and is
    multiplied by this, so it stays worth what it was worth.
    """
    return max(1.0, target_hp(floor) / _interp(ORIGINAL_HP_ANCHORS, floor))


def scaled(amount: float, floor: float) -> int:
    """`amount` of old-scale damage, as it should land on `floor` today."""
    return max(1, int(round(amount * power_scale(floor)))) if amount > 0 else int(amount)


# ---------------------------------------------------------------------------
# The other two yardsticks (REBALANCE_MASTER_PLAN.md section 2).
#
# Anything that helps or hurts by a FIXED amount should be written as a share
# of one of these, never as a bare number: a trap as a share of a health bar,
# a spell or a pet's bite as a share of one attack. Bare numbers are how a
# floor-1 monster came to drop a floor-15 axe and a ten-turn stun came to
# last two.
#
# ONE_ATTACK: damage of a single chain from a weapon typical of the floor, at
# that floor's clock, for the child the game is balanced for. Recomputed by
# tools/balance/yardsticks.py; tests/test_yardsticks.py checks for drift.
# HEALTH_BAR: max HP of a player who cooks steadily, from the simulator.
# ---------------------------------------------------------------------------
ONE_ATTACK = {1: 16, 10: 34, 20: 105, 30: 195, 40: 299, 50: 354, 60: 520,
              70: 715, 80: 1158, 90: 1653, 100: 2143}
HEALTH_BAR = {1: 30, 10: 66, 20: 100, 30: 143, 40: 180, 50: 219, 60: 265,
              70: 311, 80: 365, 90: 424, 100: 450}


def one_attack(floor: float) -> float:
    """Damage one weapon chain does on `floor` (see ONE_ATTACK)."""
    return _interp(ONE_ATTACK, floor)


def health_bar(floor: float) -> float:
    """Max HP of a steady cook on `floor` (see HEALTH_BAR)."""
    return _interp(HEALTH_BAR, floor)


def attacks(amount: float, floor: float) -> int:
    """`amount` weapon chains' worth of damage on `floor`."""
    return max(1, int(round(amount * one_attack(floor))))


def of_health(share: float, floor: float, max_hp: int | None = None) -> int:
    """`share` of a health bar: the player's own when given, else the
    floor's typical one."""
    bar = max_hp if max_hp else health_bar(floor)
    return max(1, int(round(share * bar)))


# Fixed hazard and healing numbers (a trap's 2d6, a wand's 2d8) were written
# when a character had 30 to 60 hit points. A steady cook now has 100 by
# floor 20 and over 400 deep down, so the same numbers had become a tickle:
# a pit trap on floor 80 took under 2% of a health bar.
HAZARD_BAR = 60          # the health bar the written hazard numbers assumed
HAZARD_CAP = 0.30        # no single hazard takes more than this share


def hazard(written: float, max_hp: int) -> int:
    """`written` points of hazard damage (a trap, a shock, a backlash) as the
    same share of the player's own health bar that it was of a 60-point one,
    never more than HAZARD_CAP of it."""
    if written <= 0:
        return 0
    share = min(HAZARD_CAP, float(written) / HAZARD_BAR)
    return max(1, int(round(share * max(1, int(max_hp)))))


def mend(written: float, max_hp: int, least_share: float = 0.0) -> int:
    """Healing: the written amount, or `least_share` of the player's health
    bar if that is more. Keeps a wand or a meal worth using once hit points
    have grown, the way healing potions already work."""
    return max(int(round(written)), int(round(least_share * max(1, int(max_hp)))))


def target_dmg(floor: float) -> float:
    """Typical damage of one ordinary monster hit on `floor`."""
    return _interp(DMG_ANCHORS, floor)


def dice_for_average(avg: float, sides: int = 6) -> str:
    """A dice string whose mean is about `avg` (at least 1d4)."""
    if avg < 3:
        return '1d4'
    n = max(1, int(round(avg / (sides + 1))))
    mod = int(round(avg - n * (sides + 1) / 2))
    return f'{n}d{sides}+{mod}' if mod > 0 else f'{n}d{sides}'


# ---------------------------------------------------------------------------
# Pacing dials (2026-10 balance pass). Kept here, beside the anchors, so the
# game, the tests and tools/balance/difficulty_sim.py read one copy.
# ---------------------------------------------------------------------------

# Wandering monsters stop arriving while this many are already hunting the
# player, or while the floor holds wander_alive_cap(level) alive in all: about
# what a floor starts with, so a floor refills as it is cleared but does not
# flood.
WANDER_HUNTING_CAP = 3


def wander_alive_cap(level: int) -> int:
    return min(10 + int(level) // 5, 30)


def natural_regen(max_hp: int) -> int:
    """HP regained per natural regeneration tick."""
    return max(1, int(max_hp) // 50)


# A hero's signature weapon (the named one a secret build starts with) is
# worth this much of a typical common weapon of the deepest floor reached:
# 1.3 at the top, easing to 1.1 by floor 40. It starts far above that (three
# to five times a floor-1 sword), so the starting edge fades on its own and
# from about floor 12 the weapon grows instead of being thrown away.
HERO_WEAPON_SHARE_START = 1.3
HERO_WEAPON_SHARE_END = 1.1
HERO_WEAPON_SHARE_END_FLOOR = 40


def hero_weapon_share(floor: int) -> float:
    t = min(1.0, max(0.0, (int(floor) - 1) / float(HERO_WEAPON_SHARE_END_FLOOR - 1)))
    return HERO_WEAPON_SHARE_START + (HERO_WEAPON_SHARE_END - HERO_WEAPON_SHARE_START) * t


# A pet that has kept pace with the dungeon (its level about equal to the
# floor) bites for PET_ATTACK_SHARE of one weapon attack and has
# PET_HEALTH_SHARE of the player's health bar for that depth. Pet numbers
# were written as "3 damage at level 1, 30 at level 100" and then multiplied
# by the monster-health scale, which made a pet 72% of the player's attack
# on floor 5 and 7% on floor 100, dying to two or three hits deep down.
PET_ATTACK_SHARE = 0.25
PET_HEALTH_SHARE = 0.70
PET_REGEN_SHARE = 0.01        # of max HP, every third turn


def pet_attack(level: int) -> int:
    """A pet's base bite at `level` (levels track floors, 1 to 100)."""
    return max(3, int(round(PET_ATTACK_SHARE * one_attack(max(1, min(100, int(level)))))))


def pet_health(level: int) -> int:
    return max(20, int(round(PET_HEALTH_SHARE * health_bar(max(1, min(100, int(level)))))))


# Meditation gives back at most this share of max MP on any one floor; a new
# floor brings a new allowance. Unlimited, waiting turned into healing with
# no ceiling: eight waits bought a point of mana, three points a Cure Light
# Wounds, and a patient player cast twenty healing spells a floor and won
# twice as often as one who did not (measured, 71% against 35%).
MEDITATE_FLOOR_SHARE = 0.5


def meditation_allowance(max_mp: int) -> int:
    """Mana that meditating can restore on one floor."""
    return max(1, int(round(int(max_mp) * MEDITATE_FLOOR_SHARE)))


# The first floors go easy: an ordinary monster's blow lands for EARLY_MERCY
# of its damage down to floor EARLY_MERCY_FULL_TO, easing back to full by
# floor EARLY_MERCY_ENDS. Named foes are exempt. This is a rule rather than
# smaller dice because the dice up here are already 1d2 and 1d3: there is
# nothing smaller to write. (Measured: a casual player reached floor 20 in
# 79% of runs without it; the aim is about nine in ten.)
EARLY_MERCY = 0.75
EARLY_MERCY_FULL_TO = 13
EARLY_MERCY_ENDS = 26


def early_mercy(floor: int) -> float:
    """Multiplier on an ordinary monster's damage on this floor (1.0 deep)."""
    floor = int(floor)
    if floor <= EARLY_MERCY_FULL_TO:
        return EARLY_MERCY
    if floor >= EARLY_MERCY_ENDS:
        return 1.0
    t = (floor - EARLY_MERCY_FULL_TO) / float(EARLY_MERCY_ENDS - EARLY_MERCY_FULL_TO)
    return EARLY_MERCY + (1.0 - EARLY_MERCY) * t


# Rest closes wounds only so far: natural regeneration stops at this share
# of max HP. Above it, health comes from food, potions, spells and prayer.
# (Unlimited, a player who simply waited to full before every fight won
# twice as often as one who did not, with no other difference between them.)
REST_MENDS_TO = 0.60


def rest_room(hp: int, max_hp: int) -> int:
    """HP that natural regeneration may still restore."""
    return max(0, int(int(max_hp) * REST_MENDS_TO) - int(hp))


# Waits per point of mana regained by meditating (it was 1: three waits then
# bought one Cure Light Wounds, for ever).
MEDITATE_PERIOD = 8
