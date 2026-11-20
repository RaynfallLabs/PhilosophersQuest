"""The Tactical Mind: how a thinking creature weighs its turn (AI-2,
MONSTERS AND MAGIC, 2026-11-20; B/PROPOSALS_ADVANCED.md `tactical_mind`).

Brandon: "extremely advanced AI is acceptable as long as we verify it works
and there are no bugs". Until now every AI pattern was a fixed script: a
hobgoblin walked straight at the hero, single file into his corridor, and
nothing ever weighed what to do.

A creature with a mind (data/minds.json: cunning, soldier, trickster,
caster; beasts, vermin and the mindless have none) now scores a short list of
options every turn from a frozen snapshot of what it can see (``View``, built
by src/tactical_mind.py from the creature's own senses). The weights come
from its mind. The best option wins; a plain attack wins every tie, so when
nothing is worth more than striking, today's code runs unchanged.

  attack       strike, or come on as it always has (today's code)
  rotate       a hurt soldier at the front changes places with a fresh one
  feint        a soldier at a corridor's mouth feigns flight (once a band a floor)
  focus_pet    a cunning one goes for a badly hurt pet
  cast         a caster keeps its distance and casts (choose_cast)
  screen       a band's guard stands between the hero and its leader
  fall_back    half the band down: the rest gather round the leader
  hold_choke   it will not follow the hero into a narrow way: it goes round,
               or waits beyond the mouth out of his sight
  wait_allies  alone in front, with friends coming up behind: it waits
  leave_light  a dark-edge kind steps out of the hero's light, lurks beyond
               it, and strikes first when he comes within two tiles
  hold_door    a hurt soldier backs into a doorway
  bait         one that knows the floor's snares waits beyond one
  flank        it comes round to a side of the hero away from its friends

``decide`` is deterministic: no random draw at all, ties by the order above.
A chosen option other than attack is kept ``commit_turns`` turns (no
dithering) unless it stops being open to the creature, or the hero comes
beside it and the option is not one it keeps then (``KEEP_ADJACENT``).

Pure module: no Game, no monster objects.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

OPTIONS = ('attack', 'rotate', 'feint', 'focus_pet', 'cast', 'screen', 'fall_back',
           'hold_choke', 'wait_allies', 'leave_light', 'hold_door', 'bait', 'flank')
# The options a creature keeps with the hero beside it: every other one
# gives way to a blow.
KEEP_ADJACENT = ('rotate', 'feint', 'focus_pet')
MINDS = ('cunning', 'soldier', 'trickster', 'caster')

_DATA: dict | None = None


def data() -> dict:
    """data/minds.json, read once."""
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'minds.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def reload() -> None:
    global _DATA
    _DATA = None


def spec(mind) -> dict:
    """A mind's profile (weights, flags, its Bestiary line), {} for none."""
    return dict((data().get('minds') or {}).get(mind or '') or {})


def weight(sp: dict, opt: str) -> float:
    return float((sp.get('weights') or {}).get(opt, 0.0) or 0.0)


@dataclass(frozen=True)
class View:
    """What the creature knows this turn (tactical_mind.snapshot). Every
    field has a default, so a test can set only what it needs."""
    mind: str = ''
    dist: int = 99                  # Chebyshev tiles to the hero
    adjacent: bool = False
    sees_hero: bool = True          # by sight (his wounds, his light); else by sound or scent
    hp_share: float = 1.0
    hero_hp_share: float = 1.0
    hero_held: bool = False
    hero_resting: bool = False
    choke: bool = False             # only one tile beside him can be reached from its side
    engaged: int = 0                # its friends beside the hero
    coming: int = 0                 # its friends hunting him from farther back than it
    waited: int = 0                 # turns it has held or waited this fight
    hurt_lately: bool = False       # wounded since its last turn
    flank_spot: bool = False        # a free tile beside him away from its friends
    has_lane: bool = False          # a missile or spell with a clear shot now
    can_cast: bool = False          # a spell it may use, in reach, with a clear shot
    dark_edge: bool = False         # its kind fights from the edge of the light
    in_his_sight: bool = False      # the hero can see it where it stands
    hero_sight: int = 5             # how far the hero sees (his light)
    dark_tile: bool = False         # a tile out of the hero's sight it can reach
    dark_struck: bool = False       # it has struck from the dark this fight
    edge_retreats: int = 0
    door_tile: bool = False
    door_turns: int = 0
    rotate_ok: bool = False
    feint_ok: bool = False
    pet_target: bool = False        # a badly hurt pet it may go for
    knows_traps: bool = False
    bait_tile: bool = False
    bait_turns: int = 0
    role: str = ''                  # its war-band role, '' for none
    order: str = ''                 # its band leader's order, '' for none
    screen_tile: bool = False
    rally_tile: bool = False
    habit_choke: int = 0            # habits its side has seen on this floor
    habit_area: int = 0
    habit_kiter: int = 0
    habit_rest: int = 0


def rules() -> dict:
    return data()


def _r(name: str, default):
    v = rules().get(name, default)
    return type(default)(v) if v is not None else default


def pressing(v: View, sp: dict) -> bool:
    """It presses in, holding back from nothing: its leader called the
    charge; or it is a kind that smells blood and sees the hero badly hurt
    or held; or its side has seen him rest with foes about and he rests."""
    if v.order == 'charge':
        return True
    if sp.get('presses_wounded') and v.sees_hero and (
            v.hero_held or v.hero_hp_share < _r('press_below', 0.35)):
        return True
    return bool(v.hero_resting and v.habit_rest >= int((rules().get('habits') or {}).get(
        'rester_near_foes', 2)))


def activation(opt: str, v: View, sp: dict) -> float:
    """How strongly ``opt`` is open to the creature now: 0 when it is not."""
    if opt == 'attack':
        return 1.0
    patience = _r('patience', 10)
    press = pressing(v, sp)
    kiter = v.habit_kiter >= int((rules().get('habits') or {}).get('kiter', 2))
    if opt == 'rotate':
        return 1.6 if (sp.get('rotates') and v.adjacent and v.rotate_ok) else 0.0
    if opt == 'feint':
        return 1.6 if (v.feint_ok and not press) else 0.0
    if opt == 'focus_pet':
        return 2.0 if (sp.get('focus_weak') and v.pet_target and v.sees_hero) else 0.0
    if opt == 'cast':
        return 1.2 if (v.can_cast and not v.adjacent) else 0.0
    if v.adjacent:
        return 0.0
    if opt == 'screen':
        # Before the fight is joined: once one of them is on the hero, the
        # guards close too (a screen that stood by would be a gift).
        # The leader hangs back behind his guards a while longer.
        if v.order != 'screen' or not v.screen_tile or press:
            return 0.0
        if v.role == 'leader':
            return 1.0 if (v.dist >= 2 and v.waited < 2 * patience) else 0.0
        return 1.0 if (v.role == 'guard' and not v.engaged and v.dist >= 3) else 0.0
    if opt == 'fall_back':
        return 1.2 if (v.order == 'fall_back' and v.rally_tile) else 0.0
    if opt == 'hold_choke':
        if (not v.choke or press or kiter or v.hurt_lately or v.waited >= patience
                or v.has_lane or v.dist > _r('engage_radius', 6)):
            return 0.0
        hard = v.habit_choke >= int((rules().get('habits') or {}).get('choke_fighter', 2))
        return 1.3 if hard else 1.0
    if opt == 'wait_allies':
        # It holds where it is (three or four tiles off) for the friends
        # behind it; a hero who comes to it is fought.
        if (v.engaged or v.choke or press or kiter or v.coming < 1 or not 3 <= v.dist <= 5
                or v.waited >= patience or v.hurt_lately):
            return 0.0
        return 1.0
    if opt == 'leave_light':
        # In his sight it steps out of his light (a few times a fight); out
        # of it, an archer shoots (today's code), the rest lurk at the edge
        # and strike first when he comes within two tiles.
        if not (v.dark_edge and v.sees_hero) or press:
            return 0.0
        if v.in_his_sight:
            return 1.0 if (v.dark_tile and v.edge_retreats < _r('edge_retreats', 3)) else 0.0
        if v.has_lane:
            return 0.0
        if v.dist <= 2:
            return 1.6 if not v.dark_struck else 0.0
        if v.dist <= v.hero_sight + 3 and v.waited < patience:
            return 1.0
        return 0.0
    if opt == 'hold_door':
        if (v.choke or press or not v.door_tile or v.hp_share >= _r('door_below', 0.5)
                or v.door_turns >= _r('door_turns', 10)):
            return 0.0
        return 1.0
    if opt == 'bait':
        if not (v.knows_traps and v.bait_tile) or press or v.bait_turns >= _r('bait_turns', 8):
            return 0.0
        return 1.0
    if opt == 'flank':
        if v.choke or not v.flank_spot or v.dist > 3:
            return 0.0
        if v.engaged:
            return 1.3 if v.habit_area >= 1 else 1.0
        return 0.0
    return 0.0


def scores(v: View, sp: dict) -> dict:
    """{option: score} for every option open to it (attack always is)."""
    out = {}
    for opt in OPTIONS:
        a = activation(opt, v, sp)
        if a <= 0:
            continue
        w = 1.0 if opt == 'attack' and 'attack' not in (sp.get('weights') or {}) else weight(sp, opt)
        s = a * w
        if opt == 'attack' and v.adjacent:
            s += _r('adjacent_bonus', 1.0)
        if s > 0:
            out[opt] = round(s, 6)
    return out


def best(sc: dict) -> str:
    """The highest score; attack wins a tie, then the order of OPTIONS."""
    top = 'attack'
    for opt in OPTIONS:
        if opt in sc and sc[opt] > sc.get(top, 0.0):
            top = opt
    return top


def keep_plan(plan, v: View, sp: dict) -> bool:
    """Its plan from an earlier turn still holds: turns left, still open to
    it, and the hero is not beside it unless it is a plan kept then."""
    if not isinstance(plan, dict):
        return False
    opt = plan.get('opt')
    if opt not in OPTIONS or opt == 'attack' or int(plan.get('left', 0) or 0) <= 0:
        return False
    if v.adjacent and opt not in KEEP_ADJACENT:
        return False
    return activation(opt, v, sp) > 0


def decide(v: View, sp: dict, plan=None) -> tuple:
    """(option, scores). A plan still held wins; otherwise the best score."""
    sc = scores(v, sp)
    if keep_plan(plan, v, sp):
        return plan['opt'], sc
    return best(sc), sc


def new_plan(opt: str) -> dict:
    """A fresh plan for ``opt``: kept commit_turns turns (counting this)."""
    return {'opt': opt, 'left': int(_r('commit_turns', 2))}


def spend(plan) -> dict | None:
    """The plan after one turn of it (a new dict: copies share nothing)."""
    if not isinstance(plan, dict):
        return None
    left = int(plan.get('left', 0) or 0) - 1
    if left <= 0:
        return None
    return dict(plan, left=left)
