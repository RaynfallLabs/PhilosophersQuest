"""Skittish, Not Suicidal: the cowardly keep their distance, dart in when
your back is turned, and a cornered leprechaun pays for his freedom
(monster behaviour, third wave: AI-3, fix_cowardly, 2026-11-20).

The cowardly AI (the leprechauns, the ethereal filcher) used to reverse its
step toward the hero and walk straight into the nearest wall, and strike
whenever he stood beside it. It never kept a distance, never came back,
never bargained. Now:

* It keeps keep_near to keep_far tiles off (3 to 5): nearer, it backs off
  along the longest free way (morale.flee_away); farther, it closes.
* In that band it darts in when the hero's last step took him away from
  it, and strikes if it reaches him (the Irish tale: turn your eyes from
  him and he is gone with your gold).
* With a haul (src/theft.py) it keeps as far off as it can.
* Cornered (beside him, or two off with no step away), a kind with a
  ``bargain`` (data/monsters.json) offers its purse for its freedom, once
  ("The Leprechaun, cornered, holds up a fat purse: 'Let me go and it's
  yours!'"). The Game asks the hero (game_monster_ways.py: Y or N, never
  in a quiz). Yes: its gold (its treasure roll times gold_mult) and what it
  stole fall at its feet, and it is gone from the floor (no kill, no
  corpse, no karma: a bargain, not a kindness). No: it fights at bay.
  With no bargain, or after a refusal, a cornered coward fights.

An aggravated hero, or a coward roused by its kin, faces it as a fighter
(the old rule). Pure module: src/ai_turn.py calls turn(); the simulator
models a cornered leprechaun's offer (tools/balance/sim_ai3.py).
"""
from __future__ import annotations

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_coward knob


def rules() -> dict:
    return kind_data.rules('skittish')


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def bargain(m) -> dict | None:
    b = kind_data.field(m, 'bargain', None)
    return b if isinstance(b, dict) else None


def ruled(m, player) -> bool:
    if not ENABLED or getattr(m, 'ai_pattern', '') != 'cowardly':
        return False
    if kind_data.kind_def(m).get('ai_pattern', 'cowardly') != 'cowardly' or getattr(m, 'pack_dependent', False):
        return False                       # a pack hunter left alone is not a coward by nature
    if kind_data.named(m) or kind_data.outside_rules(m):
        return False
    if player.has_effect('aggravated') or getattr(m, '_alerted', False):
        return False                       # it fights, as it always did
    return True


def turned_away(player, m) -> bool:
    """The hero's last step took him away from it."""
    fx = int(getattr(player, '_facing_dx', 0) or 0)
    fy = int(getattr(player, '_facing_dy', 0) or 0)
    if not (fx or fy):
        return False
    return fx * (m.x - player.x) + fy * (m.y - player.y) < 0


def turn(m, player, dungeon, monsters, extra_occupied):
    """True (it strikes), False (it moved, held off, or offered its purse);
    None when this is not its way."""
    if not ruled(m, player):
        return None
    if not m._spots_player(player, dungeon, monsters, extra_occupied):
        return False
    import morale
    r = rules()
    near, far = int(r.get('keep_near', 3)), int(r.get('keep_far', 5))
    d = _cheb(m.x, m.y, player.x, player.y)
    loot = bool(m.__dict__.get('stolen_gold') or m.__dict__.get('stolen_items'))
    if m.__dict__.get('_bargain_refused'):
        if m._adjacent_to(player):
            return True                    # at bay: no more offers
        if morale.flee_away(m, player, dungeon, monsters, extra_occupied):
            return False
        return False
    if int(getattr(m, '_flee_timer', 0) or 0) > 0:
        m.__dict__.pop('_darting', None)  # a broken coward runs: morale first, no darts
        if morale.flee_away(m, player, dungeon, monsters, extra_occupied):
            return False
        return _cornered(m, player)
    darting = bool(m.__dict__.pop('_darting', False))
    if not loot and (darting or near <= d <= far) and turned_away(player, m):
        return _dart(m, player, dungeon, monsters, extra_occupied, r)
    if loot or d < near:
        if morale.flee_away(m, player, dungeon, monsters, extra_occupied):
            return False
        return _cornered(m, player)
    if d > far:
        import senses
        senses.step_toward(m, dungeon, (player.x, player.y), monsters, extra_occupied, player)
        return False
    return False


def _dart(m, player, dungeon, monsters, extra_occupied, r) -> bool:
    """In behind a hero whose back is turned (two steps for a quick one);
    it strikes if it reaches him, else it keeps coming while he looks away."""
    import senses
    steps = 2 if int(getattr(m, 'speed', 10) or 10) >= 14 else 1
    for _ in range(steps):
        if m._adjacent_to(player):
            break
        if not senses.step_toward(m, dungeon, (player.x, player.y), monsters, extra_occupied, player):
            break
    if m._adjacent_to(player):
        if ai_lines.once(m, 'dart'):
            ai_lines.say(m, ai_lines.fill(m, r.get('dart_line', '')), '', 'warning')
        return True
    m._darting = True
    return False


def _cornered(m, player) -> bool:
    """No way further off: a bargain to offer, or a fight."""
    b = bargain(m)
    d = m.__dict__
    if b and not d.get('_bargained') and not d.get('_bargain_refused'):
        if not d.get('_wants_bargain'):
            m._wants_bargain = True
            ai_lines.say(m, ai_lines.fill(m, b.get('line') or rules().get('offer_line', '')),
                         '', 'warning')
        return False
    return bool(m._adjacent_to(player))


def offer_gold(m, rng) -> int:
    """What its purse holds for the bargain: its treasure roll times gold_mult."""
    b = bargain(m) or {}
    lo, hi = (list((getattr(m, 'treasure', None) or {}).get('gold') or [0, 0]) + [0, 0])[:2]
    base = rng.randint(int(lo), max(int(lo), int(hi))) if hi else 0
    return int(round(base * float(b.get('gold_mult', rules().get('gold_mult', 1.5)) or 1.5)))


def accept(m) -> str:
    """The hero took the purse: it is gone (the Game drops the gold)."""
    m._bargained = True
    m.__dict__.pop('_wants_bargain', None)
    m.treasure = dict(getattr(m, 'treasure', None) or {}, gold=[0, 0], item_chance=0.0)
    b = bargain(m) or {}
    return ai_lines.fill(m, b.get('accept_line') or rules().get('accept_line', ''))


def refuse(m) -> str:
    m._bargain_refused = True
    m.__dict__.pop('_wants_bargain', None)
    b = bargain(m) or {}
    return ai_lines.fill(m, b.get('refuse_line') or rules().get('refuse_line', ''))


def tell_keys(m) -> list:
    if getattr(m, 'ai_pattern', '') != 'cowardly':
        return []
    return ['bargains'] if bargain(m) else ['skittish']
