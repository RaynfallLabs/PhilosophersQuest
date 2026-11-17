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
DMG_ANCHORS = {1: 1.19, 10: 2.19, 20: 2.86, 30: 6.08, 40: 13.63, 50: 22.01, 60: 31.67,
               70: 34.44, 80: 36.89, 90: 39.08, 100: 41.42}


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
# (Re-measured 2026-11-12 after the weapon curve: tools/balance/weapon_curve.py,
# an ordinary fight one or two chains at every depth.)
ONE_ATTACK = {1: 17, 10: 39, 20: 77, 30: 209, 40: 387, 50: 587, 60: 765,
              70: 1157, 80: 1673, 90: 2450, 100: 3009}
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
# player, or while the floor holds wander_alive_cap(level) alive in all, so a
# lingering hero's floor fills back up but does not flood. (Since 3.5.1 most
# floors start above the cap, a median of 13-16 against 10-12 on floors 2-12
# and 28-30 against 23-25 deep, so the trickle refills only a floor the hero
# has thinned out; the maze floors start below it.)
WANDER_HUNTING_CAP = 3


def wander_alive_cap(level: int) -> int:
    return min(10 + int(level) // 5, 30)


# The quickest a lingering hero's newcomers come, in turns (wander_gap; the
# floor's clock, src/wanderers.py): the same 22 turns down to floor 50, then
# longer, to 40 at floor 100. It used
# to shorten with depth (22 - floor // 4, every 10 turns from floor 48), and
# the Monte Carlo of 2026-11-12 (PLAYABILITY_MONTE_CARLO_2026_11_12.md) found
# wanderers were 60% of every deep fight: 30-40 minutes of sums a floor and
# half of all careful runs dead on floors 41-59 from the grind. Fewer things
# roam the deep, and what does is terrible.
WANDER_EVERY = 22
WANDER_EVERY_DEEP = 40
WANDER_TAPER_FROM = 50


def wander_interval(level: int) -> int:
    """The quickest pace of newcomers on a floor, reached only by a hero who
    has lingered there long past its grace (wander_gap)."""
    f = max(1, min(100, int(level)))
    if f <= WANDER_TAPER_FROM:
        return WANDER_EVERY
    share = (f - WANDER_TAPER_FROM) / (100 - WANDER_TAPER_FROM)
    return int(round(WANDER_EVERY + share * (WANDER_EVERY_DEEP - WANDER_EVERY)))


# Time to explore (3.5.1; src/wanderers.py). Brandon: "I just don't think we
# need a constant stream of monsters... I'd rather have a larger population
# at first, with complex encounters set up, then a trickle if you hang around
# TOO LONG, but give the player some time to explore... walking back and
# forth becomes a massive chore."
#
# Until then a newcomer came every 22 turns from the first turn on a floor,
# whenever it held fewer than about what it started with: every kill was
# replaced, and newcomers were half of all floor-1 fights (51%, measured on
# 24 maps). Now nothing new comes for a grace measured from the floor's own
# map: the walk of a full explore (every room, nearest first, then the down
# stair: wanderers.explore_tour; median 224 tiles on floor 1, 330 on floor 5,
# about 500 from floor 12; on a maze its passages too, 1,200-2,000) times
# WANDER_GRACE_PER_TILE, plus
# WANDER_GRACE_FLAT. A thorough explore walks about one and a half times the
# tour (doors, corners, the loot); the rest is time to fight and get your
# breath back. The clock counts only turns spent on that floor.
#
# Sized to a kid's real pace (Brandon, 2026-11-16: "check my previous runs,
# how many turns did I spend on each floor? I bet it's more than you
# expected"; his ruling: size the time to explore and the food to a kid at
# his pace). His saves: about 950 turns on floor 1 and 700 on floor 2
# (3.5.2), about 540 a floor on floors 1-3 and 820 on floor 4 (October).
# The grace had been 100 + 2 a tile, about 500 turns on floor 1's median
# map, so at his pace he met newcomers on most floors. A kid's pace is
# kid_pace below; the grace is now 550 + 2 a tile, about a third more than
# that pace on every map (940 turns on floor 1's median map, 1,550 from
# floor 12, 3,750 on a maze), so a kid at his pace explores in peace and a
# kid who lingers past it meets the trickle.
WANDER_GRACE_FLAT = 550
WANDER_GRACE_PER_TILE = 2.0
# A kid's pace on a floor, from the same saves: KID_PACE_PER_TILE x its
# explore tour (a thorough walk, doors and corners) plus KID_PACE_FLAT
# turns for everything else (fights, getting his breath back, cooking,
# reading, searching): about 700 turns on floor 1's median map, 800-900 on
# floors 2-4, 1,000 by floor 5, 1,150 from floor 12. Nothing in the game
# reads it: the grace above is sized from it, and the difficulty simulator
# (tools/balance/difficulty_sim.py) plays at it.
KID_PACE_FLAT = 400
KID_PACE_PER_TILE = 1.5


def kid_pace(tour: int) -> int:
    """Turns a kid at Brandon's pace spends on a floor whose explore tour is
    ``tour`` tiles (wanderers.explore_tour)."""
    return int(round(KID_PACE_FLAT + KID_PACE_PER_TILE * max(0, int(tour))))


# Hunger: one point of stamina (SP) every HUNGER_EVERY steps or waits
# (Game._tick_sp; Sustained doubles it, a Ring of Sustenance lengthens it by
# its share). The simulator reads the same number.
#
# Food sized to a kid's pace (2026-11-16). The SP economy (every ration and
# dish, docs/systems/conventions.md section 9) was tuned for floors of about
# 400 turns at a point every 2 steps: about 200 SP of hunger a floor. A kid
# takes 700-1,150 turns (kid_pace), so a new hero with nothing to eat
# starved at about turn 420, half-way through his first floor, and in the
# simulator at his pace a careful cook (three meals a floor) starved on the
# maze floors and died by floor 40 in ten runs of ten. A point every 4
# steps puts the hunger back at about 175-290 SP a floor: a new hero's belly
# lasts 840 turns, the floor's rations and a meal or two keep it full, and
# a hero who lingers or will not eat still goes hungry (starvation stays:
# feedback, SP is a soft boundary by supply, never by removing the damage).
HUNGER_EVERY = 4
# The floor stirs (a line, once) at this share of the grace.
WANDER_WARN_SHARE = 0.85
# After the grace, a trickle: the first newcomer comes WANDER_TRICKLE_START
# turns after it, and the gap shortens to wander_interval(level) over the
# next WANDER_TRICKLE_RAMP turns, so a hero who camps on a floor long after
# he has seen it all meets today's pressure again (resting is never safe
# forever: the 2026-10 balance pass).
WANDER_TRICKLE_START = 60
WANDER_TRICKLE_RAMP = 600


def wander_grace(tour: int) -> int:
    """Turns on a floor before anything new comes onto it."""
    return int(round(WANDER_GRACE_FLAT + WANDER_GRACE_PER_TILE * max(0, int(tour))))


def wander_gap(level: int, past: int) -> int:
    """Turns to the next newcomer, ``past`` turns after the grace ran out."""
    floor_gap = wander_interval(level)
    start = max(WANDER_TRICKLE_START, floor_gap)
    share = min(1.0, max(0, int(past)) / WANDER_TRICKLE_RAMP)
    return max(1, int(round(start + share * (floor_gap - start))))


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
# A caster's mind holds more of the quiet (magic as a style, winning-build
# plan 3.6, 2026-11-13): each point of Intelligence over 10 adds a point to
# the share, and it never passes MEDITATE_SHARE_CAP (reached at INT 40).
# Below 10 it is the plain half: a dull wit has a small bar already.
MEDITATE_INT_STEP = 0.01
MEDITATE_SHARE_CAP = 0.80


def meditation_share(intelligence: int = 10) -> float:
    """The share of max MP that meditating can restore on one floor: half,
    plus a point for each point of Intelligence over 10, at most 80%."""
    step = MEDITATE_FLOOR_SHARE + MEDITATE_INT_STEP * (int(intelligence) - 10)
    return round(max(MEDITATE_FLOOR_SHARE, min(MEDITATE_SHARE_CAP, step)), 4)


def meditation_allowance(max_mp: int, intelligence: int = 10) -> int:
    """Mana that meditating can restore on one floor."""
    return max(1, int(round(int(max_mp) * meditation_share(intelligence))))


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
