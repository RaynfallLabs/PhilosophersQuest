"""Shove: a giant's blow throws you back (AI-1, shove_into_danger,
2026-11-19).

Thor wrestled the giants' old nurse at Utgard-Loki's hall and was thrown to
one knee; the Minotaur's horns, Polyphemus' boulders. A landed attack with
`shove` ({chance, aim}) may throw the hero one tile straight back from the
creature (a STR save keeps his feet). Never into a wall, water, lava, a
pit or a creature, never off the map; held fast (immobilized, stuck), he is
not moved. A shove that beats the save also knocks him down, on the same
roll (knockdown.py, 2026-11-22). A clever shover (`aim`) picks, of the
three tiles away from it,
one where a hazard lies, and the hazard's own rule fires as he lands. The
blow leaves the shove for the Game (`_pending_shove`), which moves the
hero after the monsters' turn, as it does a pull. Pure module.
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_shove knob


def rules() -> dict:
    return kind_data.rules('shove')


def _str_save(player, rng=random) -> bool:
    mod = (int(getattr(player, 'STR', 10)) - 10) // 2
    bonus = player.save_bonus_for('STR') if hasattr(player, 'save_bonus_for') else 0
    return rng.randint(1, 20) + mod + bonus >= int(rules().get('save_dc', 13))


def after_blow(m, player, atk, actual: int, msg: str) -> str:
    sp = (atk or {}).get('shove') if isinstance(atk, dict) else None
    if not ENABLED or not isinstance(sp, dict) or actual <= 0:
        return msg
    if random.random() >= float(sp.get('chance', 0.25) or 0):
        return msg
    if any(player.has_effect(e) for e in ('immobilized', 'stuck_in_pit', 'in_pit', 'impaled')):
        return msg
    if _str_save(player):
        return msg + ' ' + ai_lines.fill(m, rules().get('held_line', ''))
    player._pending_shove = {'from': (m.x, m.y), 'aim': bool(sp.get('aim')),
                             'line': ai_lines.fill(m, rules().get('line', '')),
                             'aimed': ai_lines.fill(m, rules().get('aimed_line', ''))}
    import knockdown
    return msg + knockdown.from_shove(player, atk)


def _safe(dungeon, x: int, y: int, occupied) -> bool:
    from dungeon import WATER, LAVA
    if not dungeon.in_bounds(x, y) or not dungeon.is_walkable(x, y):
        return False
    t = dungeon.tiles[y][x]
    if t in (WATER, LAVA):
        return False
    if (x, y) in (getattr(dungeon, 'pits', None) or ()):
        return False
    return (x, y) not in occupied


def landing(dungeon, hero, frm, aim: bool, occupied):
    """The tile the hero is thrown to, or None: straight back from ``frm``,
    or (aim) the one of the three away from it with a hazard on it."""
    hx, hy = hero
    dx = (hx > frm[0]) - (hx < frm[0])
    dy = (hy > frm[1]) - (hy < frm[1])
    if not dx and not dy:
        return None
    straight = (hx + dx, hy + dy)
    options = [straight]
    if dx and dy:
        options += [(hx + dx, hy), (hx, hy + dy)]
    elif dx:
        options += [(hx + dx, hy - 1), (hx + dx, hy + 1)]
    else:
        options += [(hx - 1, hy + dy), (hx + 1, hy + dy)]
    ok = [t for t in options if _safe(dungeon, t[0], t[1], occupied)]
    if not ok:
        return None
    if aim:
        try:
            import hazards
            harmful = [t for t in ok if hazards.hazard_at(dungeon, t[0], t[1])]
            if harmful:
                return harmful[0], True
        except (ImportError, AttributeError):
            pass
    if straight in ok:
        return straight, False
    return None
