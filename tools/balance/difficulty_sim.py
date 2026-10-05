#!/usr/bin/env python
"""Monte Carlo difficulty simulator for Philosopher's Quest.

Question it answers: "how hard is this game for a player who gets most of the
questions right?"  It plays whole runs, floor by floor, with a scripted player
whose only inputs are an ACCURACY (chance each answer is right), a SPEED
(seconds per math answer, by tier) and a PROFILE (how well they cook, loot,
heal and rest).

What is REAL and what is MODELLED
---------------------------------
REAL (the game's own code and data are called):
  * floors            level_manager.LevelManager().generate(floor): the real
                      monster population, room layout, floor loot, mini-boss
                      plan, seal demons and boss floors.
  * monsters          monster.Monster built by the game; every hit on the
                      player goes through Monster.attack(player) (THAC0 vs
                      AC, min hit chance, multi-attack, gaze, rage, on-hit
                      effects and saving throws) and Monster.tick_effects().
  * the player        player.Player: max HP, cooking softcap, get_ac(),
                      take_damage(), status effects, saving throws, the quiz
                      timer. Gear goes on through Player._apply_equip().
  * the player's hit  combat.player_attack(): weapon base x chain^exponent,
                      STR, weakness / resistance, chain specials (bleed, AoE,
                      sunder ...), dragon scales, damage ward.
  * loot              the floor's real item list, real chest loot
                      (container_system), real monster-drop pickers.

MODELLED (simple, explicit, every number a named constant below):
  * the quiz          a math chain is: one shared timer; each answer takes a
                      lognormal time by tier; each is right with probability
                      ACCURACY; the chain ends on a wrong answer or when the
                      clock runs out (quiz_engine.py:313-379). Tier mastery
                      (quiz_engine.py:583-627) is modelled exactly: after all
                      N distinct questions of a tier have been answered right,
                      every later attack at that tier is an instant chain 5.
  * positioning       there is no map. Monsters of one room form a group and
                      come at the player `--engagers` at a time. Who strikes
                      first, ranged opening shots, hit-and-run and fleeing are
                      rules of thumb taken from monster.take_turn.
  * the player's      when to drink, pray, cast, rest, flee, cook and what to
    decisions         wear: the PROFILE tables below.

Usage
-----
    python tools/balance/difficulty_sim.py                 # default report
    python tools/balance/difficulty_sim.py --trials 60 --accuracy 0.85 \
        --profile prepared --knobs mon_dmg=1.5,mastery=0
    python tools/balance/difficulty_sim.py --list-knobs

Standard library + the game's own modules only. Never writes inside the repo,
never touches the save directory (bones are stubbed out), never opens a window.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_REPO, 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# --- the game's own modules (none of these import pygame) -------------------
import combat                                    # noqa: E402
import container_system                          # noqa: E402
import dungeon as dungeon_mod                    # noqa: E402
import items as items_mod                        # noqa: E402
import level_manager as level_manager_mod        # noqa: E402
from dice import roll                            # noqa: E402
from floor_curve import dice_for_average, target_dmg   # noqa: E402
from items import (Accessory, Armor, Container, Food, Potion, Shield,   # noqa: E402
                   Spellbook, Weapon)
from monster import Monster                      # noqa: E402
from player import Player                        # noqa: E402
from quiz_engine import QuizResult               # noqa: E402
import food_system as food_system_mod            # noqa: E402
import status_effects as status_effects_mod      # noqa: E402
from spells import LEARNABLE_SPELLS as SPELLS                        # noqa: E402
from status_effects import DEBUFFS               # noqa: E402

# bones.load_bones() creates a folder in the save dir and can DELETE a bones
# file (level_manager.py:110-115). The simulator must never do that.
level_manager_mod.LevelManager._maybe_spawn_bones = staticmethod(lambda *a, **k: None)

# items.load_items() re-reads and re-parses its JSON file on every call, and
# chest / drop loot calls it several times per roll. Cache the parsed lists
# for this process (the simulator copies anything it goes on to equip).
_ITEM_CACHE = {}
_real_load_items = items_mod.load_items


def _cached_load_items(item_class):
    lst = _ITEM_CACHE.get(item_class)
    if lst is None:
        lst = _ITEM_CACHE[item_class] = _real_load_items(item_class)
    return lst


for _mod in (items_mod, container_system, dungeon_mod, level_manager_mod):
    if getattr(_mod, 'load_items', None) is _real_load_items:
        setattr(_mod, 'load_items', _cached_load_items)

_POOL_CACHE = {}

BOSS_FLOORS = (20, 40, 60, 80, 100)
SEAL_FLOORS = (83, 85, 87, 89, 91, 93, 97)

# =============================================================================
# KNOBS -- global "what if" multipliers. The most important feature of the tool.
# =============================================================================
# Pass on the command line as  --knobs mon_dmg=1.5,mon_hp=1.2  or as a JSON
# object  --knobs '{"mon_dmg": 1.5}'  or as a dict to run_cell(knobs=...).
# Unknown names are an error (a silent typo would report a baseline as a sweep).
#
# DEPTH SCHEDULES: the knobs listed in SCHEDULED_KNOBS also accept  lo:hi ,
# meaning "lo on floor 1, hi on floor 100, linear in between", e.g.
#   --knobs mon_dmg=2.0:1.0      (double damage at the top, normal at the bottom)
# A plain number is the same value on every floor.
KNOB_DEFAULTS = {
    # --- the seven asked for -------------------------------------------------
    'mon_dmg':    1.0,   # x every point of damage a monster or its DOT deals
    'mon_hp':     1.0,   # x every monster's max HP
    'mon_hit':    0,     # +n to every monster's to-hit (thac0 lowered by n)
    'mon_count':  1.0,   # x monsters met per floor (groups duplicated / dropped)
    'heal':       1.0,   # x every HP the player recovers (potion, prayer,
                         #   spell, regen, food, cooking)
    'chain_exp':  0.0,   # chain exponent for polynomial weapons; 0 = leave the
                         #   weapon's own value (1.15 for every common weapon)
    'player_hp':  1.0,   # x player max HP (base and every later gain)
    # --- extras the rules turned out to need ----------------------------------
    'mastery':    1,     # 1 = real rule (2026-10): in combat a cleared math
                         #   tier's deck just comes round again. 0 = same.
                         #   2 = the OLD rule: a cleared tier auto-hits at
                         #   chain 5 with no question.
                         #   3 = "frontier": a cleared tier moves combat up
                         #   to the next tier (tried and rejected: it asked
                         #   tier 3-4 sums on floors 21-39).
    'tier_by_floor': 0,  # 1 = ask math tier 1 + floor//20 (CURVE.md section 2)
                         #   instead of the weapon's quiz_tier (always 1 for
                         #   common weapons, items.py:323 / 1777-1879).
    'timer':      1.0,   # x the math chain timer (WIS seconds)
    'bleed':      1.0,   # x the monster-side bleed tick (max_hp//15 per turn,
                         #   monster.py:353). 0 = bleed does nothing.
    'ac':         1.0,   # x the AC the player gets from gear and DEX
    'heal_spell': 1,     # 0 = healing spells unavailable
    'rest':       1.0,   # x the rest budget (turns of waiting per floor)
    'wander':     1.0,   # x wandering-monster spawn rate
    'min_hit':    -1.0,  # >= 0: floor on every monster's hit chance
                         #   (overrides 0.05 / boss 0.25, monster.py:636-638)
    'spell_heal': 1.0,   # x healing-spell amounts only
    'regen':      1.0,   # x natural regeneration only
    'mp_rest':    0.125, # MP regained per turn of waiting (meditation)
    'potions':    1.0,   # x healing potions found (count, stochastic rounding)
    'ranged_shots': 2,   # free shots a ranged monster gets while you close the
                         #   distance (GUESSED; ranged AI fires at 2-6 tiles)
    'hp_per_floor': 0.0, # + max HP on every new deepest floor (the game's
                         #   Player.HP_PER_LEVEL is 0; CURVE.md section 4 assumes
                         #   a no-cooking base that climbs 30 -> 200 by floor 100)
    'boss_hp':    1.0,   # extra x HP for named foes only (gate bosses, seal
                         #   demons, mini-bosses), on top of mon_hp
    'boss_dmg':   1.0,   # extra x damage for named foes only, on top of mon_dmg
    'dmg_cap':    0.0,   # > 0: any ordinary monster attack whose mean damage is
                         #   above dmg_cap x the floor's damage anchor
                         #   (floor_curve.target_dmg at the monster's peak floor)
                         #   is re-diced down to that. Named foes are exempt.
}


SCHEDULED_KNOBS = ('mon_dmg', 'mon_hp', 'mon_hit', 'mon_count', 'heal',
                   'boss_hp', 'boss_dmg', 'potions', 'wander')


def kval(knobs: dict, name: str, floor: int):
    """Value of a knob on a floor (resolves lo:hi depth schedules)."""
    v = knobs[name]
    if isinstance(v, tuple):
        # lo:hi, or any number of points spaced evenly from floor 1 to 100
        pos = (max(1, min(100, floor)) - 1) / 99.0 * (len(v) - 1)
        i = min(len(v) - 2, int(pos))
        v = v[i] + (v[i + 1] - v[i]) * (pos - i)
        if isinstance(KNOB_DEFAULTS[name], int):
            v = int(round(v))
    return v


def parse_knobs(text) -> dict:
    """'a=1.5,b=2' or a JSON object or a dict -> full knob dict (validated)."""
    knobs = dict(KNOB_DEFAULTS)
    if not text:
        return knobs
    if isinstance(text, dict):
        given = text
    else:
        text = text.strip()
        if text.startswith('{'):
            given = json.loads(text)
        else:
            given = {}
            for part in text.split(','):
                part = part.strip()
                if not part:
                    continue
                if '=' not in part:
                    raise SystemExit(f"--knobs: expected name=value, got {part!r}")
                k, v = part.split('=', 1)
                given[k.strip()] = v.strip()
    for k, v in given.items():
        if k not in KNOB_DEFAULTS:
            raise SystemExit(f"--knobs: unknown knob {k!r}. Valid: "
                             + ', '.join(sorted(KNOB_DEFAULTS)))
        if isinstance(v, (list, tuple)):
            v = ':'.join(str(x) for x in v)
        if isinstance(v, str) and ':' in v:
            if k not in SCHEDULED_KNOBS:
                raise SystemExit(f"--knobs: {k} does not take a lo:hi schedule "
                                 f"(only {', '.join(SCHEDULED_KNOBS)})")
            knobs[k] = tuple(float(x) for x in v.split(':'))
        else:
            knobs[k] = type(KNOB_DEFAULTS[k])(float(v))
    return knobs


def knobs_label(knobs: dict) -> str:
    def fmt(v):
        return ':'.join(f"{x:g}" for x in v) if isinstance(v, tuple) else f"{v:g}"
    diff = [f"{k}={fmt(knobs[k])}" for k in KNOB_DEFAULTS if knobs[k] != KNOB_DEFAULTS[k]]
    return ', '.join(diff) if diff else 'baseline (no knobs)'


# =============================================================================
# ASSUMPTIONS -- every modelled number lives here, named.
# =============================================================================

# ---- The quiz (analytic) ----------------------------------------------------
# Median seconds for a fluent player to read one question, find the right one
# of four shuffled choices and press 1-4 (game_input.py:1131-1194). Tier 1 is
# single-digit sums ("6 + ? = 9"); tier 3 is "48 x 8"; tier 5 is "5(x+2)=35".
# GUESSED from the question text; scale all of them with --speed.
ANSWER_SECONDS = {1: 1.8, 2: 2.6, 3: 4.5, 4: 6.0, 5: 7.0}
ANSWER_SIGMA = 0.30            # lognormal spread of one answer's time
# Accuracy falls a little with tier for timed math and for the untimed
# subjects (equip, prayer, cooking ...). --accuracy is the tier-1 value.
ACC_DROP_PER_TIER = 0.03

# ---- Engagement ---------------------------------------------------------------
# A competent player waits for a melee monster to step adjacent and so strikes
# first (monster.take_turn returns False on the turn it moves in), EXCEPT
# speed >= 14 monsters (two steps, then attack), ambushers and mimics.
FAST_SPEED = 14
RANGED_PATTERNS = ('ranged', 'summoner', 'healer')
RANGED_KITE_PROB = 0.30        # chance a ranged monster backs off and your
                               # turn is spent closing instead of hitting
CHASE_HIT_PROB = 0.5           # chance per turn to land a blow on a fleeing monster
NEIGHBOUR_JOIN_PROB = 0.25     # chance the next room's group arrives before
                               # you can rest (perception 8, no line of sight)
MAX_FIGHT_TURNS = 400          # safety valve; a fight this long is a stalemate
WANDER_FINDS_PLAYER = 0.6      # a wandering spawn reaches the player this often
SP_PER_MOVE = 0.5              # main._tick_sp: 1 SP per 2 moves

# ---- Fleeing ------------------------------------------------------------------
# There are no attacks of opportunity and same-speed monsters never catch a
# walking player (main._do_move); fast and ranged monsters do.
FLEE_OK_SLOW = 0.85
FLEE_OK_FAST = 0.35
MAX_RETREATS_FROM_MANDATORY = 4   # bosses / seal demons: retreat, heal, return

# ---- Cooking (food_system + cook_outcomes.json, summarised) --------------------
# Per outcome tier: (P(outcome raises max HP), mean max-HP amount,
#                    mean HP healed, P(+1 stat)).
COOK_TABLE = {
    1: (1 / 15, 1.0, 2.9, 0.0),
    2: (1 / 43, 1.0, 5.8, 0.0),
    3: (25 / 64, 1.5, 9.8, 8 / 64),
    4: (31 / 65, 3.8, 13.9, 30 / 65),
    5: (33 / 49, 5.0, 21.8, 40 / 49),
}
COOK_STATS = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')

# ---- Fountains and thrones (game_divine.py:380-452, 790-851) ---------------------
FEATURE_BREAK_CHANCE = 0.33    # a fountain dries / a throne crumbles per use
FOUNTAIN_DRINK_BELOW = 0.60    # prepared players drink when under this HP share

# ---- Boss quest layers (QUEST_FLOWS.md) -----------------------------------------
ASTERION_AWAY_TURNS = (9, 12)     # retreat 3 + hide 4-6 + walk back ~2
ASTERION_CHARGE_PROB = 0.6        # he returns down a straight passage this often
FAFNIR_BREATH_BEFORE_PIT = 0.5    # chance he breathes once before you reach the pit
ABADDON_ALTAR_WALK_TURNS = 2      # turns spent reaching each altar under attack
GLEIPNIR_BIND_AT_STACKS = 2       # cast the ribbon before the three-stack flurry

# ---- Profiles -------------------------------------------------------------------
PROFILES = {
    # Cooks, wears what drops, identifies before equipping, uses potions,
    # prayer and spells sensibly, rests a little, has done the boss quests.
    'prepared': dict(
        loot_fraction=0.85,      # share of a floor's loot actually found
        explore_turns=300,       # walking turns per floor (engine notes: 200-400)
        engage_fraction=0.85,    # share of a floor's monster groups fought
        opens_chests=True,
        equips_armor=True, equips_accessories=True, avoids_cursed=True,
        cooks_per_floor=3,       # cook attempts per floor (cap is per floor anyway)
        eats_for_hp=True,
        potion_at=0.25,          # in a fight: drink below this HP fraction
        heal_at=0.40,            # in a fight: pray / cast below this
        top_up_to=0.75,          # between fights: recover to this fraction
        prays=True, casts=True, flees=True, flee_at=0.15,
        rest_turns=400,          # turns per floor spent waiting to heal
        quests=True,             # has each gate boss's quest layer
    ),
    # Dives, cooks rarely, wears little, drinks late, never rests.
    'unprepared': dict(
        loot_fraction=0.45, engage_fraction=0.60, explore_turns=160,
        opens_chests=False,
        equips_armor=True, equips_accessories=False, avoids_cursed=False,
        armor_equip_chance=0.35,  # only this share of armor finds get worn
        cooks_per_floor=0.25,     # i.e. one cook attempt every fourth floor
        eats_for_hp=False,
        potion_at=0.15, heal_at=0.20, top_up_to=0.0,
        prays=False, casts=False, flees=True, flee_at=0.10,
        rest_turns=0, quests=False,
    ),
    # Prepared, and rests as long as it takes (holding '.' is free: waiting
    # costs no SP and regen still ticks, game_input.py:373-395).
    'patient': dict(
        loot_fraction=0.95, engage_fraction=0.95, explore_turns=350,
        opens_chests=True,
        equips_armor=True, equips_accessories=True, avoids_cursed=True,
        cooks_per_floor=4, eats_for_hp=True,
        potion_at=0.25, heal_at=0.45, top_up_to=0.95,
        prays=True, casts=True, flees=True, flee_at=0.20,
        rest_turns=4000, quests=True,
    ),
}

HEAL_SPELL_IDS = ('cure_light_spell', 'cure_wounds_spell', 'heal_spell',
                  'greater_heal_spell')
# game_magic.py:71 and :1296-1306: heal = roll(power) * MULT[tier] * (1 + INT*0.1)
MAGIC_TIER_MULT = {1: 3.0, 2: 2.5, 3: 2.0, 4: 1.75, 5: 1.5}

BANDS = [(1, 9), (10, 19), (21, 29), (30, 39), (41, 49), (50, 59),
         (61, 69), (70, 79), (81, 89), (90, 99)]


# =============================================================================
# Small helpers
# =============================================================================

def dice_mean(expr) -> float:
    """Mean of a dice string like '4d8+10' (or a plain number)."""
    s = str(expr or '').replace(' ', '').lower()
    if not s:
        return 0.0
    total = 0.0
    for term in s.replace('-', '+-').split('+'):
        if not term:
            continue
        if 'd' in term:
            n, sides = term.split('d', 1)
            sign = -1.0 if n.startswith('-') else 1.0
            n = abs(int(n)) if n not in ('', '-') else 1
            total += sign * n * (int(sides) + 1) / 2.0
        else:
            total += float(term)
    return total


def acc_at(accuracy: float, tier: int) -> float:
    return max(0.05, min(0.999, accuracy - ACC_DROP_PER_TIER * (max(1, tier) - 1)))


def band_tier(floor: int) -> int:
    return max(1, min(5, 1 + floor // 20))


_TIER_SIZES = None


def main_wander_alive_cap(floor: int) -> int:
    """Copy of main.wander_alive_cap (main opens a window, so not imported)."""
    return min(10 + int(floor) // 5, 30)


def math_tier_sizes() -> dict:
    """Distinct questions per math tier (what mastery has to clear)."""
    global _TIER_SIZES
    if _TIER_SIZES is None:
        path = os.path.join(_REPO, 'data', 'questions', 'math.json')
        with open(path, encoding='utf-8') as f:
            qs = json.load(f)
        if isinstance(qs, dict):
            qs = qs.get('questions', [])
        sizes = {}
        for t in range(1, 6):
            sizes[t] = len({q['question'] for q in qs if q.get('tier', 1) == t})
        _TIER_SIZES = sizes
    return _TIER_SIZES


# =============================================================================
# The analytic quiz
# =============================================================================

class QuizModel:
    """Stands in for QuizEngine inside combat.player_attack.

    MODELLED, not real: the question text is never drawn. A chain is a race
    between a geometric run of right answers and one shared timer.
    """

    def __init__(self, accuracy: float, speed: float, policy: str, knobs: dict):
        self.accuracy = accuracy
        self.speed = speed
        self.policy = policy          # 'greedy' or 'kill'
        self.knobs = knobs
        self.retired = {t: 0 for t in range(1, 6)}   # right answers per tier
        self.mastered = set()
        self.floor = 1
        self.stop_at = None           # 'kill' policy: chain at which to press SPACE
        # counters (reset per floor by the caller)
        self.n_questions = 0
        self.n_attacks = 0
        self.n_auto = 0
        self.chain_sum = 0
        self.reroll_was_used = False  # read by game code after a quiz

    # -- tier actually asked ---------------------------------------------------
    def tier_for(self, weapon_tier: int) -> int:
        if self.knobs['tier_by_floor']:
            t = band_tier(self.floor)
        else:
            t = max(1, min(5, int(weapon_tier or 1)))
        if self.knobs['mastery'] == 3:
            while t < 5 and t in self.mastered:      # fight at the frontier
                t += 1
        return t

    # -- pure chain sampler (no side effects) -----------------------------------
    def sample_chain(self, tier: int, timer: float, max_chain, stop_at=None):
        """Returns (chain, questions_asked, right_answers)."""
        acc = acc_at(self.accuracy, tier)
        med = ANSWER_SECONDS[tier] * self.speed
        elapsed = 0.0
        chain = 0
        asked = 0
        while True:
            if stop_at and chain >= stop_at:
                break                                 # SPACE: lock the chain in
            t = random.lognormvariate(math.log(med), ANSWER_SIGMA)
            if elapsed + t > timer:
                asked += 1                            # clock ran out mid-question
                break
            elapsed += t
            asked += 1
            if random.random() < acc:
                chain += 1
                if max_chain and chain >= max_chain:
                    break
            else:
                break
        return chain, asked, chain

    # -- QuizEngine.start_quiz stand-in ------------------------------------------
    def start_quiz(self, mode='chain', subject='math', tier=1, callback=None,
                   threshold=3, max_chain=None, wisdom=10, timer_modifier=1.0,
                   extra_seconds=0, base_seconds=None, **_kw):
        tier = self.tier_for(tier)
        # same formula as quiz_engine.py:261-264
        if base_seconds is not None:
            timer = round(base_seconds * timer_modifier) + extra_seconds
        else:
            timer = round((10 + wisdom) * timer_modifier) + extra_seconds
        timer *= self.knobs['timer']
        self.n_attacks += 1
        if self.knobs['mastery'] == 2 and tier in self.mastered:
            # quiz_engine.py:602-627: plain CHAIN on a mastered tier ->
            # chain = max_chain or 5, no question shown.
            chain = max_chain or 5
            self.n_auto += 1
            self.chain_sum += chain
            callback(QuizResult(success=True, score=chain, correct=1, asked=1))
            return
        chain, asked, right = self.sample_chain(tier, timer, max_chain, self.stop_at)
        self.n_questions += asked
        self.retired[tier] += right
        if (self.knobs['mastery'] and tier not in self.mastered
                and self.retired[tier] >= math_tier_sizes()[tier]):
            self.mastered.add(tier)
            if chain >= 1 and self.knobs['mastery'] == 2:
                # the next draw auto-passes and lifts the chain to max_chain or 5
                chain = max_chain or max(chain, 5)
        self.chain_sum += chain
        callback(QuizResult(success=True, score=chain, correct=right, asked=asked))

    def one_question(self, tier: int) -> bool:
        """One untimed question in another subject (equip, harvest, cook ...)."""
        return random.random() < acc_at(self.accuracy, tier)

    def escalator_chain(self, max_len: int = 5) -> int:
        """Untimed escalator chain (prayer): tier 1 up, stop at first wrong."""
        chain = 0
        for t in range(1, max_len + 1):
            if random.random() < acc_at(self.accuracy, t):
                chain += 1
            else:
                break
        return chain


# =============================================================================
# The simulated player (real Player, plus knob hooks)
# =============================================================================

class SimPlayer(Player):
    """player.Player with three knob hooks; every rule is inherited."""

    def __init__(self, knobs: dict):
        super().__init__()
        self._k = knobs
        self._incoming_scale = 1.0     # set to mon_dmg while monsters act
        self._dmg_taken = 0            # running total, read by the stats
        self._heal_x = 1.0             # heal knob on the current floor (set by Run)
        if knobs['player_hp'] != 1.0:
            self.max_hp = max(1, round(self.max_hp * knobs['player_hp']))
            self.hp = self.max_hp

    def take_damage(self, amount, damage_type='physical'):
        if self._incoming_scale != 1.0 and amount > 0:
            amount = max(1, round(amount * self._incoming_scale))
        before = self.hp
        actual = super().take_damage(amount, damage_type)
        self._dmg_taken += max(0, before - self.hp)
        return actual

    def increase_max_hp(self, amount, from_cooking=False):
        before = self.max_hp
        super().increase_max_hp(amount, from_cooking=from_cooking)
        k = self._k['player_hp']
        if k != 1.0:
            extra = round((self.max_hp - before) * (k - 1.0))
            self.max_hp = max(1, self.max_hp + extra)
            self.hp = min(self.max_hp, self.hp + max(0, extra))

    def get_ac(self):
        ac = super().get_ac()
        k = self._k['ac']
        if k != 1.0:
            ac = 10 - round((10 - ac) * k)
        return ac

    def heal(self, amount: float) -> int:
        """All simulator-side healing funnels through here (heal knob)."""
        amount = int(round(amount * self._heal_x))
        if amount <= 0:
            return 0
        return self.restore_hp(amount)


# =============================================================================
# Floor snapshots (real generation, cached and reused across trials)
# =============================================================================

GEN_FAILURES = []      # (floor, error) for every generation the game crashed on


class FloorSnap:
    __slots__ = ('floor', 'groups', 'items', 'n_monsters', 'fountains', 'thrones')


def _room_index(m, rooms) -> int:
    for i, r in enumerate(rooms):
        if r.x <= m.x < r.x + r.width and r.y <= m.y < r.y + r.height:
            return i
    return -1


def build_snapshot(floor: int) -> FloorSnap:
    """One real floor: monsters grouped by the room they stand in, plus loot."""
    # The game's own generator can raise on rare layouts (seen: a one-room
    # maze floor plus the 5% soul-sphere roll -> rng.choice(rooms[1:]) on an
    # empty list, dungeon.py spawn_items). Count it and roll the floor again.
    for _attempt in range(8):
        try:
            lm = level_manager_mod.LevelManager()
            dungeon, monsters, floor_items = lm.generate(floor)
            break
        except (IndexError, ValueError) as exc:
            GEN_FAILURES.append((floor, repr(exc)))
    else:
        raise RuntimeError(f"floor {floor} failed to generate 8 times: {GEN_FAILURES[-1]}")
    by_room = {}
    loners = 0
    for m in monsters:
        if getattr(m, 'is_allied', False):
            continue
        idx = _room_index(m, getattr(dungeon, 'rooms', []) or [])
        if idx < 0:
            loners += 1
            idx = -loners
        by_room.setdefault(idx, []).append(m)
    snap = FloorSnap()
    snap.floor = floor
    snap.groups = list(by_room.values())
    snap.n_monsters = sum(len(g) for g in snap.groups)
    keep = (Weapon, Armor, Shield, Potion, Food, Spellbook, Accessory, Container)
    snap.items = [it for it in floor_items if isinstance(it, keep)]
    tiles = getattr(dungeon, 'tiles', None) or []
    snap.fountains = sum(row.count(dungeon_mod.FOUNTAIN) for row in tiles)
    snap.thrones = sum(row.count(dungeon_mod.THRONE) for row in tiles)
    return snap


class FloorCache:
    def __init__(self, variants: int):
        self.variants = variants
        self._cache = {}

    def get(self, floor: int) -> FloorSnap:
        lst = self._cache.setdefault(floor, [])
        if len(lst) < self.variants:
            lst.append(build_snapshot(floor))
            return lst[-1]
        return random.choice(lst)


def fresh_monster(proto: Monster, knobs: dict, floor: int = 1) -> Monster:
    """A fight-ready copy of a cached monster, with the monster knobs applied."""
    m = copy.copy(proto)
    m.status_effects = {}
    m.alive = True
    named = bool(getattr(proto, 'is_boss', False) or getattr(proto, 'is_mini_boss', False)
                 or getattr(proto, 'is_seal_demon', False))
    hp_x = kval(knobs, 'mon_hp', floor) * (kval(knobs, 'boss_hp', floor) if named else 1.0)
    hp = proto.max_hp
    if hp_x != 1.0:
        hp = max(1, round(hp * hp_x))
    m.max_hp = m.hp = hp
    m._sim_dmg_x = (kval(knobs, 'mon_dmg', floor)
                    * (kval(knobs, 'boss_dmg', floor) if named else 1.0))
    hit = kval(knobs, 'mon_hit', floor)
    if hit:
        m.thac0 = proto.thac0 - int(hit)
    if knobs['dmg_cap'] > 0 and not is_named(proto):
        key = ('cap', proto.kind, knobs['dmg_cap'])
        atks = _POOL_CACHE.get(key)
        if atks is None:
            limit = knobs['dmg_cap'] * target_dmg(getattr(proto, 'peak_floor', 1) or 1)
            atks = []
            for a in proto.attacks:
                if dice_mean(a.get('damage')) > limit:
                    a = dict(a, damage=dice_for_average(limit))
                atks.append(a)
            _POOL_CACHE[key] = atks
        m.attacks = atks
    if knobs['min_hit'] >= 0:
        m.min_hit_chance = max(float(knobs['min_hit']),
                               0.25 if getattr(proto, 'is_boss', False) else 0.05)
    m._aware = True
    m._sim_proto = proto      # the untouched cached monster
    m._sim_attacks = 0        # player attack actions spent on it
    m._sim_dmg = 0            # damage it dealt to the player
    m._sim_away = 0           # hit-and-run: turns until it comes back
    m._sim_hr_left = 0        # hit-and-run: blows left this visit
    return m


def is_named(m) -> bool:
    return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False)
                or getattr(m, 'is_seal_demon', False))


# =============================================================================
# One run
# =============================================================================

def new_floor_stats() -> dict:
    return dict(visits=0, deaths=0, first_deaths=0, monsters=0, kills=0,
                one_shots=0, atk_sum=0, dmg_per_mon=0.0, hp_lost=0.0,
                heal_used=0.0, heal_supply=0.0, heal_free=0.0,
                questions=0, attacks=0, auto=0, chain_sum=0, max_hp=0.0,
                ac=0.0, wbase=0.0, fled=0, potions_end=0.0, has_spell=0,
                consumables=0, atk_hist={}, killers={}, mastered=0)


class Run:
    """One simulated character from floor 1 down."""

    def __init__(self, cache: FloorCache, profile: str, accuracy: float,
                 speed: float, policy: str, engagers: int, knobs: dict):
        self.cache = cache
        self.profile_name = profile
        self.prof = PROFILES[profile]
        self.knobs = knobs
        self.engagers = max(1, engagers)
        self.quiz = QuizModel(accuracy, speed, policy, knobs)
        self.p = SimPlayer(knobs)
        self.p.x, self.p.y = 5, 5
        self.potions = []          # healing Potion items carried
        self.food = []             # Food items carried
        self.spells = {}           # spell_id -> (mp_cost, power, tier)
        self.turn = 0
        self.regen_carry = 0.0
        self.floor = 1
        self.floor_alive = 0       # monsters alive on this floor (wander cap)
        self.dead = False          # a death has happened on this floor
        self.ever_died = False
        self.fs = None             # current floor's stats dict
        self.stats = {}            # floor -> stats dict
        self.boss_rows = []        # (name, floor, variant, attacks, dmg_frac, died, turns)
        self._drop_pool = _POOL_CACHE     # process-wide (spawn pools, drop pools)
        self._score_cache = {}
        self.last_hit_by = '?'
        self.fountain_uses = 0     # drinks left at fountains found on this floor
        self._give_starting_kit()

    def kv(self, name: str):
        """Knob value on the current floor."""
        return kval(self.knobs, name, self.floor)

    # ------------------------------------------------------------------ setup
    def _give_starting_kit(self):
        """A floor-1 common weapon. (Builds differ; this is the plain case.)"""
        for _ in range(20):
            w = items_mod.pick_random_weapon_for_floor(1, random)
            if w is not None and getattr(w, 'requires_ammo', None) is None:
                self._equip(w)
                return

    def fork(self) -> 'Run':
        """Independent copy for a side fight (boss table)."""
        cache, stats, rows = self.cache, self.stats, self.boss_rows
        pool, fs = self._drop_pool, self.fs
        self.cache = self.stats = self.boss_rows = self._drop_pool = self.fs = None
        twin = copy.deepcopy(self)
        self.cache, self.stats, self.boss_rows = cache, stats, rows
        self._drop_pool, self.fs = pool, fs
        twin.cache = cache
        twin._drop_pool = pool
        twin.stats = {}
        twin.boss_rows = []
        twin.fs = new_floor_stats()
        return twin

    # ------------------------------------------------------------- weapon value
    def _est_damage(self, w, chain: int) -> float:
        """Rough per-hit damage of weapon w at a chain (used only to choose
        gear and for the 'kill' chain policy; the real number comes from
        combat.player_attack)."""
        if chain <= 0:
            return 0.0
        p = self.p
        if w is None:
            base = max(1, round(2 * (1 + max(0, p.STR - 10) / 10.0)))
            exp = 1.15
            mult = chain ** exp
        else:
            base = (w.base_damage or dice_mean(w.damage)) + w.enchant_bonus
            exp = getattr(w, 'chain_exponent', None)
            if exp:
                mult = chain ** exp
            else:
                cm = w.chain_multipliers
                mult = cm[min(chain - 1, len(cm) - 1)]
        return max(1.0, base * mult * (1.0 + max(0, p.STR - 10) * 0.03))

    def _weapon_score(self, w) -> float:
        """Expected damage per attack with w under this player's quiz model."""
        tier = self.quiz.tier_for(getattr(w, 'quiz_tier', 1) if w else 1)
        exp = getattr(w, 'chain_exponent', None) if w else 1.15
        max_chain = None if (w is None or exp) else w.max_chain_length
        timer = self.p.get_quiz_timer('math') * self.knobs['timer']
        mastered = bool(self.knobs['mastery'] == 2 and tier in self.quiz.mastered)
        key = (tier, round(timer), max_chain, mastered)
        dist = self._score_cache.get(key)
        if dist is None:
            if mastered:
                dist = [max_chain or 5]
            else:
                dist = [self.quiz.sample_chain(tier, timer, max_chain)[0]
                        for _ in range(150)]
            self._score_cache[key] = dist
        return sum(self._est_damage(w, c) for c in dist) / len(dist)

    # ------------------------------------------------------------------- gear
    def _equip(self, item):
        item = copy.copy(item)          # never mutate a cached / shared item
        try:
            self.p._apply_equip(item)
        except Exception:
            # fall back to a bare slot write; never let odd gear stop a run
            if isinstance(item, Weapon):
                self.p.weapon = item
            elif isinstance(item, Shield):
                self.p.shield = item
        w = self.p.weapon
        if w is not None and self.knobs['chain_exp'] > 0 and getattr(w, 'chain_exponent', None):
            w.chain_exponent = float(self.knobs['chain_exp'])

    def consider(self, item):
        """Decide what to do with one found item."""
        prof, p = self.prof, self.p
        cursed = getattr(item, 'buc', 'uncursed') == 'cursed'
        if isinstance(item, Potion):
            if item.effect in ('heal', 'extra_heal', 'full_heal', 'regeneration'):
                # potions knob: stochastic rounding of the count
                k = self.kv('potions')
                n = int(k) + (1 if random.random() < (k - int(k)) else 0)
                for _ in range(n):
                    self.potions.append(item)
                    self.fs['heal_supply'] += self._potion_value(item)
            return
        if isinstance(item, Food):
            self.food.append(item)
            if prof['eats_for_hp']:
                self.fs['heal_supply'] += item.hp_restore * self.kv('heal')
            return
        if isinstance(item, Spellbook):
            if (prof['casts'] and self.knobs['heal_spell']
                    and item.spell_id in HEAL_SPELL_IDS
                    and item.spell_id not in self.spells
                    and self.quiz.one_question(item.quiz_tier)):   # grammar
                sp = SPELLS[item.spell_id]
                self.spells[item.spell_id] = (int(sp['mp_cost']), sp['power'],
                                              int(sp.get('tier', 1)))
            return
        if cursed and prof['avoids_cursed']:
            return                      # a prepared player identifies first
        if isinstance(item, Weapon):
            if getattr(item, 'requires_ammo', None) is not None:
                return                  # ranged play is not modelled
            cur = p.weapon
            if cur is not None and getattr(cur, 'buc', '') == 'cursed':
                return                  # welded on
            if self._weapon_score(item) > 1.05 * self._weapon_score(cur):
                self._equip(item)
            return
        if isinstance(item, Armor):
            if not prof['equips_armor']:
                return
            if random.random() > prof.get('armor_equip_chance', 1.0):
                return
            try:
                idx = items_mod.ARMOR_SLOTS.index(item.slot)
            except ValueError:
                return
            cur = p.armor_slots[idx]
            if cur is not None and getattr(cur, 'buc', '') == 'cursed':
                return
            new_v = item.ac_bonus + item.enchant_bonus
            old_v = (cur.ac_bonus + cur.enchant_bonus) if cur else -99
            if new_v > old_v:
                # geography threshold quiz; a failure costs a turn and the
                # player may try again, so a prepared player always succeeds.
                if prof['avoids_cursed'] or self._threshold_quiz(item):
                    self._equip(item)
            return
        if isinstance(item, Shield):
            if not prof['equips_armor'] or not p.can_equip_shield():
                return
            cur = p.shield
            if cur is not None and getattr(cur, 'buc', '') == 'cursed':
                return
            new_v = item.ac_bonus + item.enchant_bonus
            old_v = (cur.ac_bonus + cur.enchant_bonus) if cur else -99
            if new_v > old_v and (prof['avoids_cursed'] or self._threshold_quiz(item)):
                self._equip(item)
            return
        if isinstance(item, Accessory):
            if not prof['equips_accessories']:
                return
            fx = getattr(item, 'effects', {}) or {}
            if fx.get('status') in DEBUFFS or fx.get('amount', 0) < 0 \
                    or fx.get('amount2', 0) < 0:
                return
            if getattr(item, 'chain_equip', None) or getattr(item, 'is_unique', False):
                return                  # legendary attunement is not modelled
            slot = getattr(item, 'slot', 'ring')
            if slot == 'amulet' and p.amulet_slot is not None:
                return
            if slot == 'belt' and getattr(p, 'belt_slot', None) is not None:
                return
            if slot == 'none':
                return
            before = p.max_hp
            self._equip(item)
            if p.max_hp > before:       # CON gear raises max HP without healing
                pass
            return

    def _threshold_quiz(self, item) -> bool:
        need = max(1, int(getattr(item, 'equip_threshold', 2)))
        return all(self.quiz.one_question(getattr(item, 'quiz_tier', 1))
                   for _ in range(need))

    # ------------------------------------------------------------------ healing
    def _potion_value(self, pot) -> float:
        p = self.p
        mult = {'blessed': 1.5, 'cursed': 0.5}.get(getattr(pot, 'buc', ''), 1.0)
        if pot.effect == 'full_heal':
            v = p.max_hp * (0.5 if mult < 1 else 1.0)
        elif pot.effect == 'regeneration':
            v = 80
        else:
            share = (food_system_mod.POTION_EXTRA_HEAL_SHARE if pot.effect == 'extra_heal'
                     else food_system_mod.POTION_HEAL_SHARE)
            v = max(dice_mean(pot.power), p.max_hp * share) * mult
        return min(p.max_hp, v) * self.kv('heal')

    def drink(self) -> bool:
        """Drink the most useful healing potion (food_system.drink_potion)."""
        if not self.potions:
            return False
        p = self.p
        missing = p.max_hp - p.hp
        # smallest potion that covers the gap, else the biggest
        ranked = sorted(self.potions, key=self._potion_value)
        pick = next((x for x in ranked if self._potion_value(x) >= missing), ranked[-1])
        self.potions.remove(pick)
        mult = {'blessed': 1.5, 'cursed': 0.5}.get(getattr(pick, 'buc', ''), 1.0)
        if pick.effect == 'full_heal':
            amt = missing * (0.5 if mult < 1 else 1.0)
        elif pick.effect == 'regeneration':
            p.status_effects['regenerating'] = max(
                p.status_effects.get('regenerating', 0), int(pick.duration or 80))
            amt = 0
        else:
            share = (food_system_mod.POTION_EXTRA_HEAL_SHARE if pick.effect == 'extra_heal'
                     else food_system_mod.POTION_HEAL_SHARE)
            amt = max(roll(pick.power), p.max_hp * share) * mult
        got = p.heal(amt)
        self.fs['heal_used'] += got
        self.fs['consumables'] += 1
        return True

    def pray(self) -> bool:
        """game_divine._resolve_simple_prayer, karma 0, no altar."""
        p = self.p
        if p.prayer_cooldown > 0:
            return False
        chain = self.quiz.escalator_chain(5)
        p.prayer_cooldown = max(100, 100 + 25 * chain)
        if chain >= 1:
            p.restore_sp(max(15, p.max_sp // 4))
        if chain >= 2:
            self.fs['heal_used'] += p.heal(max(15, p.max_hp // 4))
        if chain >= 3:
            p.restore_mp(max(5, p.max_mp // 4))
        if chain >= 5:
            p.status_effects['shielded'] = max(p.status_effects.get('shielded', 0), 20)
        return True

    def _best_spell(self, missing: float):
        """(spell_id, cost, power, tier) the player can afford, or None."""
        if not self.spells or not self.knobs['heal_spell']:
            return None
        best = None
        for sid, (cost, power, tier) in self.spells.items():
            if cost > self.p.mp:
                continue
            heal = dice_mean(power) * MAGIC_TIER_MULT[tier] * (1 + self.p.INT * 0.1)
            score = min(heal, missing) / cost
            if best is None or score > best[0]:
                best = (score, sid, cost, power, tier)
        return best[1:] if best else None

    def cast_heal(self) -> bool:
        p = self.p
        if p.has_effect('silenced'):
            return False
        sp = self._best_spell(p.max_hp - p.hp)
        if sp is None:
            return False
        sid, cost, power, tier = sp
        p.mp -= cost                                    # spent even on a fizzle
        if self.quiz.one_question(tier):                # one science question
            amt = int(roll(power) * MAGIC_TIER_MULT[tier] * (1.0 + p.INT * 0.1))
            self.fs['heal_used'] += p.heal(amt * self.knobs['spell_heal'])
        return True

    # ------------------------------------------------------------- passing time
    def _regen_interval(self) -> int:
        return max(10, 20 - max(0, self.p.CON - 12))    # main.py:4293

    def pass_time(self, n: int, moving: bool, resting: bool = False) -> list:
        """Advance n turns outside a fight. Returns wandering monsters that
        found the player (to be fought now)."""
        if n <= 0:
            return []
        p = self.p
        # let short debuffs run out first (poison, bleed tick for real)
        guard = 0
        while guard < 60 and any(v > 0 and e in DEBUFFS
                                 for e, v in p.status_effects.items()):
            p._incoming_scale = self.kv('mon_dmg')
            p.tick_effects()
            p._incoming_scale = 1.0
            guard += 1
            if p.hp <= 0:
                return []
        start, end = self.turn, self.turn + n
        iv = self._regen_interval()
        ticks = end // iv - start // iv
        gain = (ticks * (max(1, p.max_hp // 50) + max(0, getattr(p, 'regen_bonus', 0)))
                * self.knobs['regen'])                   # main.natural_regen
        reg = p.status_effects.get('regenerating', 0)
        if reg:
            dur = n if reg < 0 else min(n, reg)
            gain += dur / status_effects_mod.REGEN_PERIOD
            if reg > 0:
                left = reg - dur
                if left > 0:
                    p.status_effects['regenerating'] = left
                else:
                    p.status_effects.pop('regenerating', None)
        self.regen_carry += gain
        whole = int(self.regen_carry)
        if whole:
            self.regen_carry -= whole
            got = p.heal(whole)
            self.fs['heal_used'] += got
            self.fs['heal_free'] += got
        p.prayer_cooldown = max(0, p.prayer_cooldown - n)
        if resting:
            p.restore_mp(int(n * self.knobs['mp_rest']))  # game_input: meditation
        if moving or resting:                            # game_input: wait ticks SP
            need = n * SP_PER_MOVE
            while p.sp - need < p.max_sp * 0.25 and self.food:
                f = max(self.food, key=lambda x: x.sp_restore)
                self.food.remove(f)
                p.restore_sp(f.sp_restore)
                self.fs['heal_used'] += p.heal(f.hp_restore)
            p.sp -= need
            if p.sp < 0:
                # starvation: 1 HP per drain tick at SP 0 (main.py:4261)
                self.last_hit_by = 'starvation'
                p.take_damage(int(-p.sp), 'starvation')
                p.sp = 0
        # wandering spawns (main._maybe_wander_spawn)
        found = []
        wi = max(10, 22 - self.floor // 4)
        # main._maybe_wander_spawn: capped by monsters HUNTING the player (a
        # wanderer that finds the player here is fought at once, so that
        # count is zero between fights) and by a whole-floor ceiling.
        cap = main_wander_alive_cap(self.floor)
        for _ in range(end // wi - start // wi):
            if self.floor_alive >= cap or random.random() >= self.kv('wander'):
                continue
            if self.floor in BOSS_FLOORS:
                continue
            m = self._wanderer()
            if m is None:
                continue
            self.floor_alive += 1
            if random.random() < WANDER_FINDS_PLAYER:
                found.append(m)
        self.turn = end
        return found

    def _wanderer(self):
        pool = self._drop_pool.get(('wander', self.floor))
        if pool is None:
            pool = dungeon_mod._build_spawn_pool(self.floor)
            self._drop_pool[('wander', self.floor)] = pool
        if not pool:
            return None
        kind = dungeon_mod._weighted_choice(pool, random)
        return fresh_monster(Monster({**pool[kind], 'id': kind}, 0, 0), self.knobs, self.floor)

    def recover(self) -> list:
        """Between fights: get back to the profile's comfort level. Returns any
        wanderers that interrupted the rest."""
        p, prof = self.p, self.prof
        target = prof['top_up_to'] * p.max_hp
        if p.hp >= target or p.hp <= 0:
            return []
        # 1. food that heals
        if prof['eats_for_hp']:
            for f in sorted(self.food, key=lambda x: -x.hp_restore):
                if p.hp >= target or f.hp_restore <= 0:
                    break
                self.food.remove(f)
                p.restore_sp(f.sp_restore)
                self.fs['heal_used'] += p.heal(f.hp_restore)
        # 2. prayer (free, on a cooldown)
        if prof['prays'] and p.hp < target and p.prayer_cooldown <= 0:
            self.pray()
        # 2b. a fountain already found on this floor (AI escalator chain)
        while (self.fountain_uses > 0 and p.hp < FOUNTAIN_DRINK_BELOW * p.max_hp
               and prof['opens_chests']):
            self.fountain_uses -= 1
            chain = self.quiz.escalator_chain(5)
            if chain >= 3:
                self.fs['heal_used'] += p.heal(p.max_hp)
                p.restore_sp(50)
            elif chain == 2:
                self.fs['heal_used'] += p.heal(max(15, p.max_hp // 8))
            elif chain == 1:
                self.fs['heal_used'] += p.heal(max(5, p.max_hp // 20))
            elif random.random() < 1 / 3:
                p.status_effects['poisoned'] = max(p.status_effects.get('poisoned', 0), 10)
            elif random.random() < 0.5:
                w = self._wanderer()
                if w is not None:
                    self.floor_alive += 1
                    return [w]
        # 3. healing spell, waiting for MP as needed (waiting = resting)
        budget = self.rest_left
        while prof['casts'] and self.spells and p.hp < target and self.knobs['heal_spell']:
            sp = self._best_spell(p.max_hp - p.hp)
            if sp is None:
                cheapest = min(c for c, _, _ in self.spells.values())
                need = math.ceil((cheapest - p.mp) / max(0.01, self.knobs['mp_rest']))
                if need > budget or cheapest > p.max_mp:
                    break
                budget -= need
                found = self.pass_time(int(need), moving=False, resting=True)
                if found:
                    self.rest_left = budget
                    return found
                continue
            if not self.cast_heal():     # silenced, or nothing castable
                break
            budget -= 1
            self.turn += 1
            if budget <= 0:
                break
        # 4. plain rest
        iv = self._regen_interval()
        while p.hp < target and budget >= iv:
            budget -= iv
            found = self.pass_time(iv, moving=False, resting=True)
            if found:
                self.rest_left = budget
                return found
            if p.hp <= 0:
                break
        self.rest_left = budget
        # 5. potions, only if still badly hurt
        while p.hp < 0.5 * target and self.potions:
            self.drink()
        return []

    # ------------------------------------------------------------------- cooking
    def cook(self, kills: int):
        """Harvest + cook for the profile's number of attempts this floor."""
        prof, p = self.prof, self.p
        n = prof['cooks_per_floor']
        attempts = int(n) + (1 if random.random() < (n - int(n)) else 0)
        attempts = min(attempts, kills)
        tier = band_tier(self.floor)
        for _ in range(attempts):
            # one animal question (harvest) then one cooking question
            if not (self.quiz.one_question(tier) and self.quiz.one_question(tier)):
                continue
            p_hp, hp_amt, heal_amt, p_stat = COOK_TABLE[tier]
            p.restore_sp(60 + 20 * tier)
            got = p.heal(heal_amt)
            self.fs['heal_used'] += got
            self.fs['heal_supply'] += heal_amt * self.kv('heal')
            if random.random() < p_hp:
                amt = max(1, int(round(random.expovariate(1.0 / hp_amt)))) \
                    if hp_amt > 1 else 1
                p.try_apply_cook_hp_gain(amt)            # real caps + softcap
            else:
                # food_system._apply_outcome_body: every proper meal builds
                # the cook up when the recipe has no max-HP bonus of its own
                p.try_apply_cook_hp_gain(int(getattr(p, 'COOK_BASE_MAX_HP', 0)))
            if random.random() < p_stat:
                p.try_apply_cook_stat_gain(random.choice(COOK_STATS), 1)

    def sit_throne(self) -> list:
        """game_divine._resolve_throne (history escalator chain). Returns any
        monsters the throne summons."""
        p = self.p
        out = []
        while True:
            chain = self.quiz.escalator_chain(5)
            if chain == 0:
                r = random.random()
                if r < 1 / 3:
                    self.last_hit_by = 'throne'
                    p.take_damage(random.randint(5, 15), 'lightning')
                elif r < 2 / 3:
                    p.status_effects['weakened'] = max(p.status_effects.get('weakened', 0), 20)
                else:
                    for _ in range(2):
                        w = self._wanderer()
                        if w is not None:
                            self.floor_alive += 1
                            out.append(w)
            elif chain == 2:
                self.fs['heal_used'] += p.heal(max(20, p.max_hp // 5))
            elif chain == 4:
                bonus = round(random.randint(5, 15) * self.knobs['player_hp'])
                p.max_hp += bonus
                p.hp = min(p.hp + bonus, p.max_hp)
            elif chain >= 5:
                for stat in random.sample(COOK_STATS, 2):
                    p.apply_stat_bonus(stat, 1)
            if out or p.hp <= 0 or random.random() < FEATURE_BREAK_CHANCE:
                return out

    # ----------------------------------------------------------------- monster AI
    def monster_acts(self, m, boss_ctx) -> bool:
        """Does m attack this turn? Mirrors the gates at the top of
        Monster.take_turn (monster.py:900-1010) for an adjacent monster."""
        if not m.alive:
            return False
        if m.has_effect('sleeping') or m.has_effect('paralyzed'):
            return False
        if 0 < m.speed < 8 and random.random() < (8 - m.speed) / 10.0:
            return False
        if m.has_effect('slowed'):
            m._slow_skip = not m._slow_skip
            if m._slow_skip:
                return False
        # one-way enrage (boss second phase)
        if (not m._enraged and m.enraged_pattern and m.enrage_at_hp_pct > 0
                and 0 < m.hp <= m.max_hp * m.enrage_at_hp_pct):
            m._enraged = True
            m.ai_pattern = m.enraged_pattern
            m._sim_away = 0
        named = m._is_named_foe() or m.max_hp > 500
        if not named and m.ai_pattern == 'aggressive':
            if m._flee_timer > 0:
                m._flee_timer -= 1
                if m.hp > m.max_hp * 0.5:
                    m._flee_timer = 0
                return False
            if 0 < m.hp < m.max_hp * 0.25:
                m._flee_timer = 8
                return False
        if m.ai_pattern not in ('sessile', 'mimic'):
            if m._under('feared') or m._under('charmed'):
                return False
            if m._under('confused') and random.random() < 0.40:
                return False
            if m._under('blinded') and random.random() < 0.30:
                return False
        pat = m.ai_pattern
        if pat == 'cowardly':
            return random.random() < 0.3
        if pat == 'hit_and_run':
            # monster.py _hit_and_run_turn: 1-2 blows, then gone for a while
            if m._sim_away > 0:
                m._sim_away -= 1
                if m._sim_away == 0:
                    m._sim_hr_left = random.randint(1, 2)
                    if m.can_charge and random.random() < ASTERION_CHARGE_PROB:
                        m._charge_ready = True
                return False
            if m._sim_hr_left <= 0:
                m._sim_hr_left = random.randint(1, 2)
            m._sim_hr_left -= 1
            if m._sim_hr_left <= 0:
                m._sim_away = random.randint(*ASTERION_AWAY_TURNS)
            return True
        if pat == 'dancer':
            if m._gaze_cooldown > 0:
                m._gaze_cooldown -= 1
        if pat == 'fenrir_rage':
            # monster.py _fenrir_rage_turn
            m._rage_turn_counter += 1
            if (m.rage_interval > 0 and m._rage_turn_counter % m.rage_interval == 0
                    and m.rage_stacks < 8):
                m.rage_stacks += 1
        return True

    def player_can_act(self) -> bool:
        """main._do_move / game_input._player_input turn-loss rules."""
        p = self.p
        if p.has_effect('sleeping') or p.has_effect('paralyzed'):
            return False
        if p.has_effect('frozen'):
            self._frozen_skip = not getattr(self, '_frozen_skip', False)
            if self._frozen_skip:
                return False
        if p.has_effect('fumbling') and random.random() < 0.20:
            return False
        if p.has_effect('stunned') and random.random() < 0.25:
            return False
        return True

    def _tick_monster(self, m):
        """Monster.tick_effects with the bleed knob applied."""
        k = self.knobs['bleed']
        if k != 1.0 and m.status_effects.get('bleeding', 0) > 0:
            dur = m.status_effects.pop('bleeding')
            m.tick_effects()
            if m.alive:
                dmg = int(max(1, m.max_hp // 15) * k)
                if dmg > 0:
                    m.take_damage(dmg)
                if dur - 1 > 0 and m.alive:
                    m.status_effects['bleeding'] = dur - 1
        else:
            m.tick_effects()

    # --------------------------------------------------------------------- fight
    def fight(self, group: list, mandatory: bool = False, boss_ctx=None) -> str:
        """Fight a group. Returns 'won', 'fled', 'dead' or 'stalemate'."""
        p = self.p
        k = self.engagers
        queue = list(group)
        active = []
        ctx = boss_ctx or {}
        turn = 0
        retreats = 0
        hasted_flip = False
        strip_turns = 0                       # Abaddon altar window
        altars_left = 6 if ctx.get('altars') else 0
        p._combat_pets_ref = []
        p._combat_game_ref = None
        p._combat_player_taken_damage = False
        slots = [(6, 5), (5, 6), (6, 6), (4, 5), (5, 4), (4, 4), (6, 4), (4, 6)]

        def enter(m, opening: bool):
            """A monster joins the melee; resolve who strikes first."""
            m.x, m.y = slots[len(active) % len(slots)]
            active.append(m)
            free = 0
            pat = m.ai_pattern
            if pat in RANGED_PATTERNS or (pat == 'dragon' and not ctx.get('pit')):
                free = int(self.knobs['ranged_shots']) if pat != 'dragon' else 1
                if pat == 'dragon' and ctx.get('pit_breath_skip'):
                    free = 0
            elif m.speed >= FAST_SPEED or pat in ('ambush', 'mimic'):
                free = 1
            if pat == 'hit_and_run':
                m._sim_hr_left = random.randint(1, 2)
                if m.can_charge and random.random() < ASTERION_CHARGE_PROB:
                    m._charge_ready = True
            for _ in range(free):
                if p.hp <= 0 or not m.alive:
                    break
                if pat in RANGED_PATTERNS or pat == 'dragon':
                    ax, ay = m.x, m.y
                    m.x, m.y = 9, 5              # at range: attack() picks a ranged blow
                    self._monster_attack(m)
                    m.x, m.y = ax, ay
                else:
                    self._monster_attack(m)

        while True:
            active = [m for m in active if m.alive]
            while len(active) < k and queue:
                enter(queue.pop(0), opening=(turn == 0))
            if p.hp <= 0 and self._player_dead():
                return 'dead'
            if not active:
                return 'won'
            turn += 1
            if turn > MAX_FIGHT_TURNS:
                return 'stalemate'

            # ---------------- player's action ----------------
            action = None
            if self.player_can_act():
                hpf = p.hp / max(1, p.max_hp)
                prof = self.prof
                reachable = [m for m in active if m._sim_away <= 0]
                if hpf < prof['potion_at'] and self.potions:
                    self.drink()
                    action = 'heal'
                elif hpf < prof['heal_at']:
                    if prof['prays'] and p.prayer_cooldown <= 0 and not altars_left:
                        self.pray()
                        action = 'heal'
                    elif prof['casts'] and self.cast_heal():
                        action = 'heal'
                    elif self.potions and hpf < prof['heal_at'] * 0.75:
                        self.drink()
                        action = 'heal'
                if action is None and prof['flees'] and hpf < prof['flee_at'] \
                        and not self.potions:
                    if not mandatory or retreats < MAX_RETREATS_FROM_MANDATORY:
                        slow = all(m.speed < FAST_SPEED
                                   and m.ai_pattern not in RANGED_PATTERNS
                                   and m.rage_stacks < 3 for m in active)
                        if random.random() < (FLEE_OK_SLOW if slow else FLEE_OK_FAST):
                            if not mandatory:
                                self.fs['fled'] += 1
                                return 'fled'
                            # mandatory fight: walk off, recover, come back.
                            retreats += 1
                            self.fs['fled'] += 1
                            self._between_rounds(active)
                            continue
                        action = 'flee_failed'
                if action is None and not reachable:
                    # foe out of reach (hit-and-run): use the lull to heal
                    if hpf < prof['top_up_to']:
                        if prof['casts'] and self.cast_heal():
                            pass
                        elif self.potions and hpf < 0.5:
                            self.drink()
                        else:
                            p.restore_mp(1)
                    action = 'wait'
                if action is None:
                    # Abaddon: pray at an altar to strip the ward
                    if altars_left and strip_turns <= 0:
                        ab = next((m for m in active if m.kind == 'abaddon_destroyer'), None)
                        if ab is not None and ab.damage_ward > 0:
                            for _ in range(ABADDON_ALTAR_WALK_TURNS - 1):
                                self._world_tick(active, ctx)
                                if p.hp <= 0 and self._player_dead():
                                    return 'dead'
                            chain = self.quiz.escalator_chain(5)
                            altars_left -= 1
                            if chain > 0:
                                strip_turns = chain * 2       # game_divine.py:972-982
                                ab.resistances = []
                                ab.damage_ward = 0.0
                            action = 'altar'
                if action is None and ctx.get('gleipnir'):
                    fen = next((m for m in active if m.kind == 'fenrir_wolf'), None)
                    if fen is not None and fen.rage_stacks >= GLEIPNIR_BIND_AT_STACKS:
                        fen.reset_rage()                       # game_menus.py:1502-1506
                        fen.status_effects['paralyzed'] = max(
                            fen.status_effects.get('paralyzed', 0), 3)
                        binds = int(getattr(p, '_gleipnir_binds', 0))
                        stat = ('STR', 'DEX', 'CON')[binds % 3]
                        if getattr(p, stat) > 1:
                            setattr(p, stat, getattr(p, stat) - 1)
                        p._gleipnir_binds = binds + 1
                        action = 'bind'
                if action is None:
                    # focus the named foe if there is one, else the weakest
                    named = [m for m in reachable if is_named(m)]
                    target = named[0] if named else min(reachable, key=lambda m: m.hp)
                    if target._flee_timer > 0 and random.random() > CHASE_HIT_PROB:
                        action = 'chase'
                    elif (target.ai_pattern in RANGED_PATTERNS
                          and random.random() < RANGED_KITE_PROB):
                        action = 'closing'
                    else:
                        self._player_attack(target, active)
                        action = 'attack'

            # ---------------- the world's turn ----------------
            # hasted: the world tick is skipped on every other player action
            # (main.py _advance_turn).
            if p.has_effect('hasted'):
                hasted_flip = not hasted_flip
                if hasted_flip:
                    continue
            self._world_tick(active, ctx)
            if strip_turns > 0:
                strip_turns -= 1
                if strip_turns == 0:
                    for m in active:
                        if m.kind == 'abaddon_destroyer' and m.alive:
                            m.resistances = list(getattr(m, 'base_resistances', []))
                            m.damage_ward = float(getattr(m, 'base_damage_ward', 0.0) or 0.0)
            # Abaddon's locusts (main._spawn_abaddon_locusts), unless the
            # Scales of Michael's angels cancel them one for one.
            if not ctx.get('scales'):
                for m in list(active):
                    if (m.kind == 'abaddon_destroyer' and m.alive
                            and getattr(m, 'locust_interval', 0)
                            and turn % int(m.locust_interval) == 0):
                        live = sum(1 for x in active + queue
                                   if x.alive and x.kind == 'abyssal_locust')
                        lo, hi = m.locust_count
                        for _ in range(random.randint(int(lo), int(hi))):
                            if live >= 12:
                                break
                            loc = self._locust()
                            if loc is None:
                                break
                            live += 1
                            loc.x, loc.y = slots[len(active) % len(slots)]
                            active.append(loc)        # swarms ignore the doorway limit
            if p.hp <= 0 and self._player_dead():
                return 'dead'

    def _between_rounds(self, active):
        """Retreat from a mandatory fight, recover, return. The foe keeps its
        HP (plus its own regeneration for the turns away)."""
        t0 = self.turn
        self.rest_left = max(self.rest_left, 200)
        self.recover()
        while self.potions and self.p.hp < 0.6 * self.p.max_hp:
            self.drink()
        away = max(10, self.turn - t0)
        for m in active:
            if m.alive and getattr(m, 'regeneration', 0):
                m.hp = min(m.max_hp, m.hp + m.regeneration * away)
            m.status_effects.clear()

    def _locust(self):
        defs = self._drop_pool.get('locust')
        if defs is None:
            with open(os.path.join(_REPO, 'data', 'monsters.json'), encoding='utf-8') as f:
                defs = json.load(f).get('abyssal_locust')
            self._drop_pool['locust'] = defs
        if not defs:
            return None
        return fresh_monster(Monster({**defs, 'id': 'abyssal_locust'}, 0, 0), self.knobs, self.floor)

    def _monster_attack(self, m):
        p = self.p
        p._incoming_scale = getattr(m, '_sim_dmg_x', 1.0)
        before = p.hp
        try:
            m.attack(p)
        finally:
            p._incoming_scale = 1.0
        if p.hp < before:
            m._sim_dmg += before - p.hp
            self.last_hit_by = m.kind
        # game_combat's life_save status: a lethal hit leaves 1 HP, once
        if p.hp <= 0 and p.has_effect('life_save'):
            p.status_effects.pop('life_save', None)
            p.hp = 1

    def _world_tick(self, active, ctx):
        """One world turn: statuses tick, then every engaged monster acts
        (main._advance_turn -> game_combat._do_monster_turns)."""
        p = self.p
        for m in active:
            if m.alive:
                self._tick_monster(m)
        p._incoming_scale = self.kv('mon_dmg')
        msgs = p.tick_effects()
        p._incoming_scale = 1.0
        if any(t == '_petrify_death' for t, _ in (msgs or [])):
            p.hp = 0
        self.pass_time_in_fight()
        for m in active:
            if p.hp <= 0:
                break
            if self.monster_acts(m, ctx):
                self._monster_attack(m)

    def pass_time_in_fight(self):
        p = self.p
        self.turn += 1
        if p.prayer_cooldown > 0:
            p.prayer_cooldown -= 1
        if (self.turn % self._regen_interval() == 0 and p.hp < p.max_hp
                and not p.has_effect('bleeding') and not p.has_effect('poisoned')):
            got = p.heal(max(1, p.max_hp // 50) * self.knobs['regen'])
            self.fs['heal_used'] += got

    def _player_dead(self) -> bool:
        return self.p.is_dead()        # real: includes the death-save items

    def _player_attack(self, target, active):
        """One melee attack through the REAL combat.player_attack."""
        p = self.p
        if p.has_effect('charmed') and random.random() < 0.40:
            return                              # game_combat.py:1738
        p._combat_monsters_ref = active
        target._sim_attacks += 1
        if self.quiz.policy == 'kill':
            w = p.weapon
            stop = None
            for c in range(1, 26):
                if self._est_damage(w, c) >= target.hp:
                    stop = c
                    break
            self.quiz.stop_at = stop
        else:
            self.quiz.stop_at = None
        combat.player_attack(p, target, self.quiz, lambda *a, **kw: None)

    # ------------------------------------------------------------- floor by floor
    def _record_monster(self, m):
        fs = self.fs
        fs['monsters'] += 1
        if not m.alive:
            fs['kills'] += 1
            n = max(1, m._sim_attacks)
            fs['atk_sum'] += n
            fs['atk_hist'][min(n, 40)] = fs['atk_hist'].get(min(n, 40), 0) + 1
            if n == 1:
                fs['one_shots'] += 1
        fs['dmg_per_mon'] += m._sim_dmg / max(1, self.p.max_hp)

    def _drop_loot(self, m):
        """game_combat._drop_treasure / _spawn_treasure_item."""
        tr = getattr(m, 'treasure', {}) or {}
        if random.random() >= float(tr.get('item_chance', 0.0)):
            return
        eff = max(1, int(tr.get('item_tier', 1)) * 5, self.floor)
        r = random.random()
        gear = None
        if r < 0.30:
            gear = items_mod.pick_random_weapon_for_floor(eff, random)
        elif r < 0.40:
            gear = items_mod.pick_random_armor_for_floor(eff, random)
        elif r < 0.50:
            gear = items_mod.pick_random_shield_for_floor(eff, random)
        else:
            pool = self._drop_pool.get(eff)
            if pool is None:
                pool = []
                for cls in ('accessory', 'wand', 'scroll', 'potion', 'ammo'):
                    for it in items_mod.load_items(cls):
                        if not getattr(it, 'is_unique', False) and it.min_level <= eff:
                            pool.append(it)
                self._drop_pool[eff] = pool
            if pool:
                gear = copy.copy(container_system._weighted_common_pick(pool, eff, random))
        if gear is not None and random.random() < self.prof['loot_fraction']:
            self.consider(gear)

    def _open_chest(self, chest):
        """container_system.attempt_lockpick: one economics question."""
        if not self.prof['opens_chests']:
            return
        if not self.quiz.one_question(getattr(chest, 'quiz_tier', 1)):
            return                      # wrong: no loot (the trap is not modelled)
        try:
            loot = container_system._generate_loot_from_template(chest, self.floor)
        except Exception:
            loot = []
        for it in loot or []:
            self.consider(it)

    def _fight_and_account(self, group, mandatory=False, boss_ctx=None) -> bool:
        """Run a fight, book the results. Returns False if the run should stop
        this floor (death)."""
        result = self.fight(group, mandatory=mandatory, boss_ctx=boss_ctx)
        kills = 0
        for m in group:
            self._record_monster(m)
            if not m.alive:
                kills += 1
                self.floor_alive = max(0, self.floor_alive - 1)
                self._drop_loot(m)
        self.floor_kills += kills
        if result == 'dead':
            self._on_death()
        return True

    def _on_death(self):
        """Permadeath in the game. Here the death is booked and a 'ghost'
        continues at full HP so deeper floors still get measured; survival
        uses only the FIRST death of a run."""
        fs = self.fs
        fs['deaths'] += 1
        fs['killers'][self.last_hit_by] = fs['killers'].get(self.last_hit_by, 0) + 1
        if not self.ever_died:
            fs['first_deaths'] += 1
            self.ever_died = True
        p = self.p
        for e in list(p.status_effects):
            if e in DEBUFFS:
                p.status_effects.pop(e, None)
        p.hp = p.max_hp
        p.sp = p.max_sp

    def play_floor(self, floor: int, fights: bool = True):
        p = self.p
        self.floor = floor
        self.quiz.floor = floor
        p._heal_x = self.kv('heal')
        if floor > p.deepest_floor_reached:
            # Fafnir's Heart trophy: +2 max HP per new deepest floor (main.py:1229-1237)
            per = int(getattr(p, '_fafnir_per_descent_hp', 0) or 0)
            self._hp_floor_carry = (getattr(self, '_hp_floor_carry', 0.0)
                                    + self.knobs['hp_per_floor'])
            per += int(self._hp_floor_carry)
            self._hp_floor_carry -= int(self._hp_floor_carry)
            if per:
                per = round(per * self.knobs['player_hp'])
                p.max_hp += per
                p.hp = min(p.hp + per, p.max_hp)
        p.deepest_floor_reached = max(p.deepest_floor_reached, floor)
        p.reset_floor_cook_caps()
        p._death_save_used_this_floor = False
        p.on_level_change(ascending=False, first_visit=True)   # +15 SP, +MP, 0 HP
        fs = self.fs = self.stats.setdefault(floor, new_floor_stats())
        fs['visits'] += 1
        fs['max_hp'] += p.max_hp
        fs['ac'] += p.get_ac()
        fs['wbase'] += (p.weapon.base_damage + p.weapon.enchant_bonus) if p.weapon else 2
        q0 = (self.quiz.n_questions, self.quiz.n_attacks, self.quiz.n_auto,
              self.quiz.chain_sum)
        dmg0 = p._dmg_taken
        hp_start_max = p.max_hp
        self.rest_left = int(self.prof['rest_turns'] * self.knobs['rest'])
        self.floor_kills = 0

        snap = self.cache.get(floor)
        groups = [[fresh_monster(m, self.knobs, self.floor) for m in g] for g in snap.groups]
        is_boss_floor = floor in BOSS_FLOORS
        # mon_count knob: duplicate or drop whole groups (named foes stay single)
        kc = self.kv('mon_count')
        if kc != 1.0 and not is_boss_floor:
            out = []
            for g in groups:
                if any(is_named(m) for m in g):
                    out.append(g)
                    continue
                n = int(kc) + (1 if random.random() < (kc - int(kc)) else 0)
                for i in range(n):
                    out.append(g if i == 0 else
                               [fresh_monster(m, self.knobs, self.floor) for m in g])
            groups = out
        random.shuffle(groups)
        self.floor_alive = sum(len(g) for g in groups)

        # loot is found as the floor is explored: spread it over the groups
        loot = [it for it in snap.items if random.random() < self.prof['loot_fraction']]
        self.fountain_uses = 0
        if self.prof['opens_chests']:          # the curious profiles use dungeon features
            for _ in range(snap.fountains):
                if random.random() < self.prof['loot_fraction']:
                    loot.append('fountain')
            for _ in range(snap.thrones):
                if random.random() < self.prof['loot_fraction']:
                    loot.append('throne')
        n_steps = max(1, len(groups))
        loot_at = {}
        for it in loot:
            loot_at.setdefault(random.randrange(n_steps), []).append(it)
        step_turns = self.prof['explore_turns'] // n_steps

        pending = []
        for i, g in enumerate(groups):
            named_group = any(is_named(m) for m in g)
            must = any(getattr(m, 'is_seal_demon', False) or getattr(m, 'is_boss', False)
                       for m in g)
            # walk to the next room
            pending += self.pass_time(step_turns, moving=True) if fights else []
            for it in loot_at.get(i, []):
                if it == 'fountain':
                    uses = 1
                    while random.random() > FEATURE_BREAK_CHANCE:
                        uses += 1
                    self.fountain_uses += uses
                elif it == 'throne':
                    if fights:
                        pending += self.sit_throne()
                elif isinstance(it, Container):
                    self._open_chest(it)
                else:
                    self.consider(it)
            if not fights:
                continue
            # wanderers that found us come first
            while pending:
                w = pending.pop(0)
                self._fight_and_account([w])
                pending += self.recover()
            if not must and random.random() > self.prof['engage_fraction']:
                continue                               # room skipped
            boss_ctx = None
            if named_group:
                boss_ctx = self._boss_ctx(g, self.prof['quests'])
                self._boss_side_fights(g)
            # sometimes the next room's occupants arrive mid-fight
            if (not named_group and i + 1 < len(groups)
                    and random.random() < NEIGHBOUR_JOIN_PROB
                    and not any(is_named(m) for m in groups[i + 1])):
                g = g + groups[i + 1]
                groups[i + 1] = []
            if not g:
                continue
            if boss_ctx:
                self._boss_prefight(boss_ctx)
            self._fight_and_account(g, mandatory=must, boss_ctx=boss_ctx)
            self.p.status_effects.pop('in_pit', None)
            if (floor == 60 and self.prof['cooks_per_floor'] >= 1
                    and any(m.kind == 'fafnir_dragon' and not m.alive for m in g)
                    and self.quiz.one_question(5) and self.quiz.one_question(5)):
                self.p._fafnir_per_descent_hp = 2      # food_system.py:410-412
            pending += self.recover()
        if fights:
            while pending:
                w = pending.pop(0)
                self._fight_and_account([w])
                pending += self.recover()
            self.cook(self.floor_kills)
        else:
            self.cook(3)
            self.quiz.retired[self.quiz.tier_for(1)] += 60    # practice had on the way
            for t in range(1, 6):
                if self.knobs['mastery'] and self.quiz.retired[t] >= math_tier_sizes()[t]:
                    self.quiz.mastered.add(t)

        fs['hp_lost'] += (p._dmg_taken - dmg0) / max(1, hp_start_max)
        fs['questions'] += self.quiz.n_questions - q0[0]
        fs['attacks'] += self.quiz.n_attacks - q0[1]
        fs['auto'] += self.quiz.n_auto - q0[2]
        fs['chain_sum'] += self.quiz.chain_sum - q0[3]
        fs['potions_end'] += len(self.potions)
        fs['has_spell'] += 1 if self.spells else 0
        fs['mastered'] += 1 if self.quiz.mastered else 0
        # normalise the per-floor heal sums by max HP now (they were raw HP)
        for key in ('heal_used', 'heal_supply', 'heal_free'):
            raw = fs.get('_raw_' + key, 0.0)
            fs[key + '_frac'] = fs.get(key + '_frac', 0.0) + (fs[key] - raw) / max(1, hp_start_max)
            fs['_raw_' + key] = fs[key]

    # --------------------------------------------------------------------- bosses
    def _boss_ctx(self, group, quest: bool) -> dict:
        ctx = {'quest': quest}
        kinds = {m.kind for m in group}
        if quest:
            if 'fafnir_dragon' in kinds:
                ctx['pit'] = True
            if 'fenrir_wolf' in kinds:
                ctx['gleipnir'] = True
            if 'abaddon_destroyer' in kinds:
                ctx['altars'] = True
                ctx['scales'] = True
            if 'medusa_gorgon' in kinds:
                ctx['aegis'] = True
            if 'asterion_minotaur' in kinds:
                ctx['thread'] = True
                for m in group:
                    if m.kind == 'asterion_minotaur':
                        # game_combat.py:1995-2009
                        m.can_phase_walls = False
                        m.speed = min(m.speed, 6)
                        if m.ai_pattern == 'hit_and_run':
                            m.ai_pattern = 'aggressive'
        return ctx

    def _boss_prefight(self, ctx):
        """Put the quest item in the player's hands for this fight."""
        p = self.p
        if ctx.get('aegis'):
            aegis = items_mod.make_item_by_id('shield', 'aegis_of_athena')
            if aegis is not None:
                if p.weapon is not None and getattr(p.weapon, 'two_handed', False):
                    # the Aegis needs a free hand: its wearer gives up the 2H weapon bonus
                    pass
                p.shield = aegis
        if ctx.get('pit'):
            # step into the lair's pit: 1d4 on the way down; he may breathe once
            p.take_damage(roll('1d4'))
            p.status_effects['in_pit'] = -1
            if random.random() >= FAFNIR_BREATH_BEFORE_PIT:
                ctx['pit_breath_skip'] = True
            else:
                ctx['pit'] = False          # he breathes once as you come in ...
                ctx['pit_after'] = True     # ... then you are in the pit

    def _boss_side_fights(self, group):
        """Boss table: fight this named foe with a fresh copy of the player at
        full HP, with and without the quest layer. Does not touch this run."""
        named = [m for m in group if is_named(m)]
        if not named or getattr(self, '_is_fork', False):
            return
        boss = named[0]
        gate = bool(getattr(boss, 'is_boss', False)) and self.floor in BOSS_FLOORS
        variants = [('quest', True), ('no quest', False)] if gate else [('-', False)]
        for label, quest in variants:
            twin = self.fork()
            twin._is_fork = True
            twin.floor = self.floor
            twin.quiz.floor = self.floor
            twin.rest_left = 200
            tp = twin.p
            tp.hp = tp.max_hp
            for e in list(tp.status_effects):
                if e in DEBUFFS:
                    tp.status_effects.pop(e, None)
            g2 = [fresh_monster(m._sim_proto, self.knobs, self.floor) for m in named[:1]]
            ctx = twin._boss_ctx(g2, quest)
            twin._boss_prefight(ctx)
            dmg0 = tp._dmg_taken
            t0 = twin.turn
            res = twin.fight(g2, mandatory=True, boss_ctx=ctx)
            b = g2[0]
            self.boss_rows.append((
                boss.kind, self.floor, label, b._sim_attacks,
                (tp._dmg_taken - dmg0) / max(1, tp.max_hp),
                1 if res == 'dead' else 0, twin.turn - t0,
                1 if res == 'stalemate' else 0, twin.fs['consumables']))



# =============================================================================
# One cell = many runs with one (profile, accuracy, knobs)
# =============================================================================

def merge_stats(total: dict, part: dict):
    for floor, fs in part.items():
        t = total.setdefault(floor, new_floor_stats())
        for k, v in fs.items():
            if isinstance(v, dict):
                d = t.setdefault(k, {})
                for n, c in v.items():
                    d[n] = d.get(n, 0) + c
            elif isinstance(v, (int, float)):
                t[k] = t.get(k, 0) + v


def run_cell(profile='prepared', accuracy=0.85, trials=100, floors=(1, 100),
             knobs=None, speed=1.0, policy='greedy', engagers=1, seed=1,
             variants=24, quiet=True) -> dict:
    """Simulate `trials` runs. Returns a result dict (see report_cell)."""
    knobs = parse_knobs(knobs) if not isinstance(knobs, dict) or \
        set(knobs) != set(KNOB_DEFAULTS) else knobs
    random.seed(seed)
    cache = FloorCache(variants)
    lo, hi = floors
    total = {}
    boss_rows = []
    t0 = time.time()
    for t in range(trials):
        run = Run(cache, profile, accuracy, speed, policy, engagers, knobs)
        for f in range(1, lo):                    # gear up without fighting
            run.play_floor(f, fights=False)
        if lo > 1:
            run.stats = {}
            run.p.hp = run.p.max_hp
        for f in range(lo, hi + 1):
            run.play_floor(f)
        merge_stats(total, run.stats)
        boss_rows += run.boss_rows
        if not quiet and (t + 1) % 10 == 0:
            print(f"  .. {profile} acc={accuracy} trial {t + 1}/{trials} "
                  f"({time.time() - t0:.0f}s)", file=sys.stderr)
    return dict(profile=profile, accuracy=accuracy, trials=trials, floors=floors,
                knobs=knobs, speed=speed, policy=policy, engagers=engagers,
                stats=total, boss_rows=boss_rows, seconds=time.time() - t0,
                gen_failures=list(GEN_FAILURES))


def _run_cell_star(kw):
    return run_cell(**kw)


# =============================================================================
# Reporting
# =============================================================================

def _median_from_hist(hist: dict) -> float:
    n = sum(hist.values())
    if not n:
        return float('nan')
    acc = 0
    for k in sorted(hist):
        acc += hist[k]
        if acc * 2 >= n:
            return k
    return max(hist)


def band_rows(res: dict) -> list:
    """Aggregate a cell's per-floor stats into bands. Gate-boss floors get
    their own one-floor rows so the bands show ordinary floors only."""
    stats = res['stats']
    lo, hi = res['floors']
    trials = res['trials']
    spans = list(BANDS) + [(f, f) for f in BOSS_FLOORS]
    spans = sorted(s for s in spans if s[1] >= lo and s[0] <= hi)
    rows = []
    alive = float(trials)
    floors_sorted = sorted(stats)
    surv_after = {}
    for f in floors_sorted:
        alive -= stats[f]['first_deaths']
        surv_after[f] = alive / trials
    for a, b in spans:
        fl = [f for f in floors_sorted if a <= f <= b]
        if not fl:
            continue
        agg = new_floor_stats()
        for f in fl:
            for k, v in stats[f].items():
                if isinstance(v, dict):
                    d = agg.setdefault(k, {})
                    for n, c in v.items():
                        d[n] = d.get(n, 0) + c
                elif isinstance(v, (int, float)):
                    agg[k] = agg.get(k, 0) + v
        v = max(1, agg['visits'])
        mons = max(1, agg['monsters'])
        kills = max(1, agg['kills'])
        rows.append(dict(
            band=f"{a}-{b}" if a != b else f"{a}*",
            mons=agg['monsters'] / v,
            atk_med=_median_from_hist(agg['atk_hist']),
            atk_mean=agg['atk_sum'] / kills,
            one_shot=agg['one_shots'] / kills,
            dmg_mon=agg['dmg_per_mon'] / mons,
            hp_lost=agg['hp_lost'] / v,
            heal_used=agg.get('heal_used_frac', 0.0) / v,
            heal_supply=agg.get('heal_supply_frac', 0.0) / v,
            heal_free=agg.get('heal_free_frac', 0.0) / v,
            p_die=agg['deaths'] / v,
            surv=surv_after[fl[-1]],
            q_floor=agg['questions'] / v,
            auto=agg['auto'] / max(1, agg['attacks']),
            chain=agg['chain_sum'] / max(1, agg['attacks']),
            max_hp=agg['max_hp'] / v, ac=agg['ac'] / v, wbase=agg['wbase'] / v,
            consum=agg['consumables'] / v, fled=agg['fled'] / v,
            spell=agg['has_spell'] / v, pots=agg['potions_end'] / v,
            killers=sorted(agg['killers'].items(), key=lambda kv: -kv[1])[:4],
            deaths=agg['deaths'],
        ))
    return rows


def report_cell(res: dict, out=sys.stdout):
    w = out.write
    w(f"\n=== profile={res['profile']}  accuracy={res['accuracy']:.2f}  "
      f"trials={res['trials']}  floors={res['floors'][0]}-{res['floors'][1]}  "
      f"policy={res['policy']}  engagers={res['engagers']}  speed x{res['speed']:g}\n")
    w(f"    knobs: {knobs_label(res['knobs'])}   ({res['seconds']:.0f}s)\n")
    if res.get('gen_failures'):
        w(f"    NOTE: the game's floor generator raised {len(res['gen_failures'])} time(s) "
          f"and was re-rolled: {sorted(set(res['gen_failures']))[:3]}\n")
    w("band    mons  atk/kill 1-shot dmg/mon  HPlost  heal    finite  P(die)  cum    maxHP   AC  wpn  chain auto  Q per  cons\n")
    w("        /flr  med mean   %    %maxHP  %/floor used%   supply% /floor  surv%               base  mean   %   floor  /flr\n")
    for r in band_rows(res):
        w(f"{r['band']:<7} {r['mons']:4.1f}  {r['atk_med']:3.0f} {r['atk_mean']:4.1f}  "
          f"{100 * r['one_shot']:3.0f}  {100 * r['dmg_mon']:6.1f}  {100 * r['hp_lost']:6.0f}  "
          f"{100 * r['heal_used']:5.0f}   {100 * r['heal_supply']:5.0f}   "
          f"{100 * r['p_die']:5.1f}  {100 * r['surv']:5.1f}  {r['max_hp']:5.0f} {r['ac']:4.0f} "
          f"{r['wbase']:4.0f}  {r['chain']:4.1f} {100 * r['auto']:4.0f}  {r['q_floor']:5.0f}  "
          f"{r['consum']:4.1f}\n")
    w("  top killers by band: ")
    for r in band_rows(res):
        if r['deaths']:
            w("\n    " + f"{r['band']:<7} " + ', '.join(
                f"{k} {100 * c / r['deaths']:.0f}%" for k, c in r['killers']))
    w("\n")
    w("  (* = gate-boss floor. 'heal used' = all HP recovered on the floor, as % of max HP;\n"
      "   'finite supply' = HP value of potions, food and cooked meals found on that floor.\n"
      "   P(die) counts every death on a floor (ghost runs continue); 'cum surv' uses first deaths only.)\n")


def boss_table(res: dict, out=sys.stdout):
    rows = res['boss_rows']
    if not rows:
        return
    agg = {}
    for kind, floor, label, attacks, dmg, died, turns, stale, cons in rows:
        a = agg.setdefault((floor, kind, label), [0, 0, 0.0, 0, 0, 0, 0])
        a[0] += 1
        a[1] += attacks
        a[2] += dmg
        a[3] += died
        a[4] += turns
        a[5] += stale
        a[6] += cons
    w = out.write
    w(f"\n--- named foes, fresh player at full HP  (profile={res['profile']}, "
      f"accuracy={res['accuracy']:.2f}, knobs: {knobs_label(res['knobs'])})\n")
    w("floor foe                      layer      n  attacks  turns  dmg taken  P(die)  stale  potions\n")
    w("                                             to kill          %maxHP      %      %     used\n")
    for (floor, kind, label), a in sorted(agg.items()):
        n = a[0]
        w(f"{floor:4d}  {kind:<24} {label:<9} {n:4d}  {a[1] / n:6.1f}  {a[4] / n:5.1f}  "
          f"{100 * a[2] / n:8.0f}  {100 * a[3] / n:6.1f}  {100 * a[5] / n:4.0f}  {a[6] / n:6.1f}\n")
    w("  ('attacks' and 'dmg taken' are means over all tries, including the fatal ones;\n"
      "   'stale' = fight abandoned after %d turns.)\n" % MAX_FIGHT_TURNS)


def summary_line(res: dict) -> str:
    rows = [r for r in band_rows(res) if not r['band'].endswith('*')]
    last = band_rows(res)[-1]
    hp = ' '.join(f"{100 * r['hp_lost']:4.0f}" for r in rows)
    return (f"{res['profile']:<10} acc={res['accuracy']:.2f} "
            f"[{knobs_label(res['knobs'])}]  HP lost %/floor by band: {hp}   "
            f"survive to end: {100 * last['surv']:.1f}%")


# =============================================================================
# Command line
# =============================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Monte Carlo difficulty simulator for Philosopher's Quest.")
    ap.add_argument('--floors', default='1-100',
                    help="floor range, e.g. 1-100 or 41-60 (default 1-100)")
    ap.add_argument('--trials', type=int, default=60,
                    help="runs per (profile, accuracy) cell (default 60; every run "
                         "plays every floor, so each band gets trials x ~9 floors)")
    ap.add_argument('--accuracy', default='0.75,0.85,0.95',
                    help="comma list of answer accuracies (default 0.75,0.85,0.95)")
    ap.add_argument('--profile', default='prepared,unprepared',
                    help="comma list of: " + ', '.join(PROFILES))
    ap.add_argument('--knobs', default='',
                    help="global multipliers, e.g. mon_dmg=1.5,mon_hp=1.2 "
                         "(see --list-knobs)")
    ap.add_argument('--speed', type=float, default=1.0,
                    help="x seconds per math answer (1.0 fluent, 1.5 slow)")
    ap.add_argument('--policy', choices=('greedy', 'kill'), default='greedy',
                    help="chain policy: answer until wrong / time, or press SPACE "
                         "as soon as the blow should kill")
    ap.add_argument('--engagers', type=int, default=1,
                    help="monsters of a group that can reach you at once (default 1)")
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=0,
                    help="worker processes (default: one per cell, up to CPU count)")
    ap.add_argument('--variants', type=int, default=24,
                    help="distinct generated floors cached per floor number (each has its "
                         "own mini-boss / legendary roll; too few makes deep bands noisy)")
    ap.add_argument('--no-bosses', action='store_true', help="skip the boss table")
    ap.add_argument('--summary', action='store_true',
                    help="one line per cell instead of full tables")
    ap.add_argument('--list-knobs', action='store_true')
    args = ap.parse_args(argv)

    if args.list_knobs:
        for k, v in KNOB_DEFAULTS.items():
            print(f"  {k:<14} default {v}")
        return 0

    try:
        lo, hi = (int(x) for x in args.floors.split('-'))
    except ValueError:
        lo = hi = int(args.floors)
    knobs = parse_knobs(args.knobs)
    accs = [float(a) for a in args.accuracy.split(',') if a.strip()]
    profs = [p.strip() for p in args.profile.split(',') if p.strip()]
    for p in profs:
        if p not in PROFILES:
            raise SystemExit(f"unknown profile {p!r}; choose from {', '.join(PROFILES)}")

    cells = [dict(profile=p, accuracy=a, trials=args.trials, floors=(lo, hi),
                  knobs=knobs, speed=args.speed, policy=args.policy,
                  engagers=args.engagers, seed=args.seed + 1000 * i, variants=args.variants)
             for i, (p, a) in enumerate((p, a) for p in profs for a in accs)]
    jobs = args.jobs or min(len(cells), os.cpu_count() or 1)
    t0 = time.time()
    if jobs > 1 and len(cells) > 1:
        import multiprocessing as mp
        with mp.Pool(jobs) as pool:
            results = pool.map(_run_cell_star, cells)
    else:
        results = [run_cell(**c) for c in cells]

    print(f"Philosopher's Quest difficulty simulator -- {len(cells)} cell(s), "
          f"{args.trials} runs each, {time.time() - t0:.0f}s wall")
    for res in results:
        if args.summary:
            print(summary_line(res))
        else:
            report_cell(res)
            if not args.no_bosses:
                boss_table(res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
