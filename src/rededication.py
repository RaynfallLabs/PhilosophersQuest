"""Rededication at an altar (winning build 3.5, Brandon 2026-11-13: "tailor
their stats"): the hero gives one gift back and takes another in its place.

One option on an ordinary altar, for the altar's offering, once per altar.
The hero names the stat he gives back and the stat he takes, then answers
the theology escalator chain (max 5):

  * chain 3 or 4 moves one point, chain 5 moves two; below 3 nothing moves
    and the offering is still the altar's;
  * a stat is never given back below what it was when the run began (the
    hero's own value: what worn rings, a heroism draught or Gawain's morning
    lend is not his to give);
  * **a stat is never raised past what food could teach it** at this depth
    (Player.cooking_stat_softcap): points an altar gives count against the
    same cap as points a meal gives. Wisdom's cap is half the others' (every
    point of it is a second on the combat clock), so Wisdom keeps its half
    rate here too: an altar can never put more Wisdom on a hero than the
    kitchen could. Points moved are kept in ``Player.rededicated`` (net, by
    stat), so a gift given back frees its own room again.

Pure: no pygame, no Game. game_divine.py runs the menu, the quiz and the
lines.
"""
from __future__ import annotations

STATS = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
STAT_NAMES = {'STR': 'Strength', 'CON': 'Constitution', 'DEX': 'Dexterity',
              'INT': 'Intelligence', 'WIS': 'Wisdom', 'PER': 'Perception'}
# What each stat does, in the house words (CLAUDE.md player stats).
STAT_USES = {'STR': 'carries the pack', 'CON': 'fills out the body',
             'DEX': 'slips the blow', 'INT': 'deepens the well of magic',
             'WIS': 'slows the clock', 'PER': 'sees a little farther'}
MIN_CHAIN = 3                    # below this, nothing moves
MAX_CHAIN = 5


def points_for_chain(chain: int) -> int:
    """Points a chain of ``chain`` earns: 3-4 move one, 5 moves two."""
    c = int(chain or 0)
    if c >= MAX_CHAIN:
        return 2
    if c >= MIN_CHAIN:
        return 1
    return 0


def lent(player, stat: str) -> int:
    """What is lent to ``stat`` right now and is not the hero's own: worn
    rings and armour (the worn ledger), a keepsake carried in the pack (the
    Charmander Stuffie's carry bonus), a heroism or brilliance draught, the
    Ring of Gawain's morning surge."""
    n = int((getattr(player, '_worn_stat_ledger', None) or {}).get(stat, 0) or 0)
    for row in (getattr(player, 'active_carry_bonuses', None) or {}).values():
        try:
            s, amt = row
        except (TypeError, ValueError):
            continue
        if s == stat:
            n += int(amt or 0)
    try:
        from status_effects import TIMED_STAT_GRANTS
        for eff in getattr(player, '_timed_grants_held', None) or ():
            for s, amt in TIMED_STAT_GRANTS.get(eff, ()):
                if s == stat:
                    n += int(amt)
    except Exception:
        pass
    if stat == 'STR':
        n += int(getattr(player, '_gawain_surge', 0) or 0)
    return n


def own_value(player, stat: str) -> int:
    return int(getattr(player, stat, 10) or 0) - lent(player, stat)


def start_value(player, stat: str, fallback: dict | None = None) -> int:
    """What ``stat`` was when the run began (Player.stats_at_start; an
    older save without it uses ``fallback``, then 10)."""
    start = getattr(player, 'stats_at_start', None) or fallback or {}
    try:
        return int(start.get(stat, 10))
    except (TypeError, ValueError):
        return 10


def give_room(player, stat: str, fallback: dict | None = None) -> int:
    """Points of ``stat`` the hero can give back."""
    return max(0, own_value(player, stat) - start_value(player, stat, fallback))


def taught(player, stat: str) -> int:
    """How far food and altars together have raised ``stat``."""
    cooked = int((getattr(player, 'cooking_stat_gained', None) or {}).get(stat, 0) or 0)
    moved = int((getattr(player, 'rededicated', None) or {}).get(stat, 0) or 0)
    return cooked + max(0, moved)


def take_room(player, stat: str) -> int:
    """Points ``stat`` can take: up to food's cap at this depth (half for
    Wisdom), less what food and altars have given it already."""
    try:
        cap = int(player.cooking_stat_softcap(stat))
    except Exception:
        return 0
    return max(0, cap - taught(player, stat))


def can_give(player, fallback: dict | None = None) -> list:
    return [s for s in STATS if give_room(player, s, fallback) > 0]


def can_take(player, give: str | None = None) -> list:
    return [s for s in STATS if s != give and take_room(player, s) > 0]


def possible(player, fallback: dict | None = None) -> bool:
    """Is there any gift to give back and any to take in its place?"""
    gives = can_give(player, fallback)
    return any(can_take(player, g) for g in gives)


def points_to_move(player, give: str, take: str, chain: int,
                   fallback: dict | None = None) -> int:
    """What a chain of ``chain`` actually moves from ``give`` to ``take``."""
    if give == take or give not in STATS or take not in STATS:
        return 0
    return max(0, min(points_for_chain(chain), give_room(player, give, fallback),
                      take_room(player, take)))


def move(player, give: str, take: str, n: int) -> int:
    """Move ``n`` points from ``give`` to ``take`` (stats, and what they
    drive: HP from CON, stamina from STR, mana from INT). Returns n."""
    n = max(0, int(n or 0))
    if not n:
        return 0
    flag = getattr(player, '_quirk_grant', False)
    player._quirk_grant = False          # never through a trait's allowance
    try:
        player.apply_stat_bonus(give, -n)
        player.apply_stat_bonus(take, n)
    finally:
        player._quirk_grant = flag
    led = getattr(player, 'rededicated', None)
    if not isinstance(led, dict):
        led = {}
    led[give] = int(led.get(give, 0)) - n
    led[take] = int(led.get(take, 0)) + n
    player.rededicated = {k: v for k, v in led.items() if v}
    return n
