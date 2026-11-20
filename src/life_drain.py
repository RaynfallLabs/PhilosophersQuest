"""Life Drained: energy drain that lasts (AI-1, life_drained, 2026-11-19).

The drain TYPE (67 kinds: shadows, wights, vampires, liches...) cost a
point of CON on a failed save, at most once a floor, never below CON 8:
most of them hit like anyone else. Worse, the classic drainers (the wight,
the wraith, the barrow-wight, the cairn-wight, the fetch) struck with plain
necrotic and drained nothing at all.

Now a drain blow that lands (type 'drain', or an attack flagged
`drains_life`) and whose save fails takes life that rest does not give
back: the hero's greatest health falls by `drain_share` (0.5) of the blow,
at most a tenth of his whole health from one blow and a quarter in all, and
never below a new hero's health. It is kept in `_life_drained` on the hero.
It comes back: half at the next stair down (a night's sleep, on a floor he
has not seen), all of it from the physician's Restore, from the Mercy
prayer at a chain of 4 (an altar counts one), and the drain_resist status
and a family's ward against draining (Grave-Salt, Iron and Salt) stop it.
The old CON -1 stays for the greatest (`drain_con`: the liches and the
death lord), once a floor as before. Named foes keep their tuned fights:
their drain is the old CON rule.

The save is the old one (a CON save, DC 12 + depth/7). Pure module.
"""
from __future__ import annotations

import random

import kind_data

ENABLED = True          # the simulator's ai_drain knob (0 = the old CON rule)


def rules() -> dict:
    return kind_data.rules('life_drain')


def drains_life(atk) -> bool:
    return isinstance(atk, dict) and (atk.get('type') == 'drain' or bool(atk.get('drains_life')))


def drains(m) -> bool:
    return any(drains_life(a) for a in getattr(m, 'attacks', None) or ())


def drained(player) -> int:
    return int(getattr(player, '__dict__', {}).get('_life_drained', 0) or 0)


def _floor_hp(player) -> int:
    fn = getattr(player, 'starting_max_hp', None)
    try:
        return int(fn()) if callable(fn) else 1
    except Exception:
        return 1


def take_life(player, n: int) -> int:
    """Lower the hero's greatest health by up to ``n`` (the caps); returns
    what was taken."""
    r = rules()
    taken = drained(player)
    whole = int(player.max_hp) + taken
    room = min(int(n),
               max(1, int(whole * float(r.get('blow_cap', 0.10)))),
               int(whole * float(r.get('total_cap', 0.25))) - taken,
               int(player.max_hp) - _floor_hp(player))
    if room <= 0:
        return 0
    player.max_hp = int(player.max_hp) - room
    player.hp = min(int(player.hp), player.max_hp)
    player._life_drained = taken + room
    return room


def restore(player, n: int | None = None) -> int:
    """Give back ``n`` of the drained life (all of it when None); returns
    what came back. Exactly what was taken: health cooked on since is not
    touched."""
    taken = drained(player)
    back = taken if n is None else max(0, min(int(n), taken))
    if back <= 0:
        return 0
    player.max_hp = int(player.max_hp) + back
    player.hp = min(player.max_hp, int(player.hp) + back)
    player._life_drained = taken - back
    return back


def stairs_rest(player) -> int:
    """A night's sleep on a new floor down: half the drained life back
    (rounded up)."""
    taken = drained(player)
    if taken <= 0:
        return 0
    return restore(player, (taken + 1) // 2)


def save_holds(m, player, rng=random) -> bool:
    """The old drain save: a CON save, with the hero's save bonus and a
    family's ward against draining (said when it holds)."""
    import monster as _mon
    mod = (int(getattr(player, 'CON', 10)) - 10) // 2
    bonus = player.save_bonus_for('CON') if hasattr(player, 'save_bonus_for') else 0
    ward = _mon._edge_save(player, m, 'drain')
    dc = min(18, 12 + int(getattr(m, 'min_level', 1) or 1) // 7)
    if rng.randint(1, 20) + mod + bonus + ward < dc:
        return False
    if ward > 0:
        _mon._edge_ward_held(player, m, 'drain')
    return True


def _con_drain(m, player, actual: int, msg: str) -> str:
    """The old rule: a point of CON, once a floor, never below CON 8 (it
    asks its own save, Monster._drain_takes_hold)."""
    if not m._drain_takes_hold(player):
        return msg
    old_con = player.CON
    player.apply_stat_bonus('CON', -1)
    player._con_drained_this_floor = int(getattr(player, '_con_drained_this_floor', 0)) + 1
    if player.CON < old_con:
        from status_effects import note_stat_drain
        note_stat_drain(player, 'CON', old_con - player.CON)   # a physician can restore it
        from monster import the_name
        msg = f"{the_name(m)} drains your life force! ({actual} dmg, CON -1)"
    return msg


def after_blow(m, player, atk, actual: int, msg: str) -> str:
    """A landed drain blow (ai_blow.after_blow). Replaces the old CON block
    of Monster._resolve_blow."""
    if not drains_life(atk) or player.has_effect('drain_resist'):
        return msg
    old_rule = (not ENABLED) or kind_data.named(m)
    if old_rule:
        if atk.get('type') == 'drain':
            return _con_drain(m, player, actual, msg)
        return msg
    if kind_data.field(m, 'drain_con', False):
        msg = _con_drain(m, player, actual, msg)
    if actual <= 0 or save_holds(m, player):
        return msg
    share = float(kind_data.field(m, 'drain_share', rules().get('drain_share', 0.5)) or 0.5)
    n = take_life(player, max(1, int(round(actual * share))))
    if n > 0:
        import ai_lines
        msg += ' ' + ai_lines.fill(m, rules().get('line', ''), n=n)
    return msg
