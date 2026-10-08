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
DMG_ANCHORS = {1: 1.19, 10: 2.19, 20: 2.79, 30: 5.66, 40: 12.12, 50: 19.16, 60: 27.54,
               70: 29.95, 80: 32.08, 90: 33.98, 100: 36.02}


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
    """OFFLINE TOOLS ONLY. How much bigger an ordinary monster's HP is on
    `floor` than when the game's first numbers were written. The balance
    tools use it to convert an old figure ONCE and write the result into the
    data. Nothing in the running game may call it (a test checks): damage is
    never multiplied by the floor at the moment it lands.
    """
    return max(1.0, target_hp(floor) / _interp(ORIGINAL_HP_ANCHORS, floor))


# LORE, NOT FLOOR. Nothing in the game multiplies damage or health by the
# dungeon floor at the moment it lands. (`scaled(amount, floor)` did, in
# twenty-seven places; it is gone.) A thing's power is written as a real
# number in its data, or it is a stated SHARE of what it acts on:

WOUND_NAMED = 0.10        # a named foe takes this much of any share-of-health effect


def wound(share: float, max_hp: int, named: bool = False) -> int:
    """`share` of a creature's own full health, as hit points (at least 1).
    Named foes (bosses, mini-bosses, seal demons) take a tenth of it: their
    health is many times an ordinary monster's."""
    if share <= 0:
        return 0
    if named:
        share *= WOUND_NAMED
    return max(1, int(round(share * max(1, int(max_hp)))))


# One weapon chain takes most of an ordinary monster's health, and a hero
# power is on a long cooldown: 2d6 is about a sixth of a creature, 6d6 half.
POWER_BAR = 40.0
POWER_CAP = 0.60


def power_share(written: float) -> float:
    """Dice written for a hero power, as a share of the target's health."""
    return max(0.0, min(POWER_CAP, float(written) / POWER_BAR))


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


# Death's scythe on the climb out: this share of the player's max health a
# blow (or the written dice, if more). The climb is the last stretch of a
# won game, and decision D9 counts a win as getting out, so it is meant to
# be tense rather than a second coin-flip: Death hits a dozen or two times
# over the last twenty-five floors, and each must matter without ending the
# run by itself. Not simulated (the chase is geometry); confirm by play.
DEATH_REAP_SHARE = 0.08

# Turns after the player reaches a floor on the climb before Death steps off
# the stair behind them, by his speed (50 / 75 / 100 / 125 percent).
DEATH_ARRIVAL_DELAY = {50: 6, 75: 5, 100: 4, 125: 3}


def death_arrival_delay(speed_pct: int) -> int:
    return DEATH_ARRIVAL_DELAY.get(int(speed_pct), 4)


# A pet's health and bite are real numbers by its own level: data/pet_growth.json.
PET_REGEN_SHARE = 0.01        # of a pet's max HP, every third turn


# Meditation gives back at most this share of max MP on any one floor, once
# (Player.meditate keeps the tally per floor). Unlimited, waiting turned into healing with
# no ceiling: eight waits bought a point of mana, three points a Cure Light
# Wounds, and a patient player cast twenty healing spells a floor and won
# twice as often as one who did not (measured, 71% against 35%).
MEDITATE_FLOOR_SHARE = 0.5


def meditation_allowance(max_mp: int) -> int:
    """Mana that meditating can restore on one floor."""
    return max(1, int(round(int(max_mp) * MEDITATE_FLOOR_SHARE)))


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
