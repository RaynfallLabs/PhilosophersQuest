"""Hunger you can see (2026-11-22; data/hunger.json).

Brandon, on 3.6.1: "SP seems like an afterthought, where it used to be a
major issue and killer". Three states by how full the belly is (SP against max
SP), each a status the HUD shows:

  hungry            under a quarter: a line, no cost;
  weak_from_hunger  under a tenth: Strength -2 (status_effects.TIMED_STAT_GRANTS)
                    and no natural healing until he eats;
  starving          at 0: still Weak, and main._tick_sp wounds him (STARVE_SHARE,
                    as it always has).

``sync`` sets the statuses to match the belly and returns the line to say when
it got worse. Game._tick_sp calls it on every hunger tick, Player.restore_sp
after every meal, Game._advance_turn every turn (SP set straight in: a
prayer's full belly, a famine demon's drain), and the simulator as it walks.
Pure: no pygame, no Game.
"""
import json

from paths import data_path

STATES = ('hungry', 'weak', 'starving')
# The statuses each state holds (a Starving hero keeps the Weak hero's cost).
_HOLDS = {None: (), 'hungry': ('hungry',), 'weak': ('weak_from_hunger',),
          'starving': ('starving', 'weak_from_hunger')}
ALL_STATUSES = ('hungry', 'weak_from_hunger', 'starving')
_rules = None


def rules() -> dict:
    global _rules
    if _rules is None:
        try:
            with open(data_path('data', 'hunger.json'), encoding='utf-8') as f:
                _rules = json.load(f)
        except (OSError, ValueError):
            _rules = {'hungry_below': 0.25, 'weak_below': 0.10, 'lines': {}}
    return _rules


def state(player):
    """None, 'hungry', 'weak' or 'starving', by the belly."""
    sp = float(getattr(player, 'sp', 0) or 0)
    mx = max(1.0, float(getattr(player, 'max_sp', 1) or 1))
    if sp <= 0:
        return 'starving'
    if sp < float(rules().get('weak_below', 0.10)) * mx:
        return 'weak'
    if sp < float(rules().get('hungry_below', 0.25)) * mx:
        return 'hungry'
    return None


def current(player):
    """The state the hero's statuses show now (None when fed)."""
    se = getattr(player, 'status_effects', None) or {}
    if se.get('starving', 0):
        return 'starving'
    if se.get('weak_from_hunger', 0):
        return 'weak'
    if se.get('hungry', 0):
        return 'hungry'
    return None


def sync(player) -> list:
    """Set the hunger statuses to match the belly. Returns the line to say
    when the hero got hungrier ([] otherwise)."""
    se = getattr(player, 'status_effects', None)
    if se is None:
        return []
    before, now = current(player), state(player)
    if before == now:
        return []
    try:
        from status_effects import sync_timed_grants
        sync_timed_grants(player)            # (first sight: what is held now is counted)
    except ImportError:
        pass
    want = set(_HOLDS[now])
    for s in ALL_STATUSES:
        if s in want:
            se[s] = -1
        else:
            se.pop(s, None)
    try:
        from status_effects import sync_timed_grants
        sync_timed_grants(player)            # Weak's Strength comes and goes with it
    except ImportError:
        pass
    order = (None,) + STATES
    if now and order.index(now) > order.index(before):
        line = (rules().get('lines') or {}).get(now)
        return [line] if line else []
    return []


def blocks_regen(player) -> bool:
    """A Weak or Starving hero's wounds do not mend on their own."""
    return state(player) in ('weak', 'starving')
