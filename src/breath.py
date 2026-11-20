"""Draws Breath: a breath must be drawn again before the next (AI-1,
breath_recharge, 2026-11-19).

Fafnir alone waited between breaths (Monster._dragon_turn). Every other
breather (57 kinds: dragons, drakes, the winter wolf, the chimera, frost
giants...) breathed on every turn it had a shot, and the ranged AI then
stepped back from a hero who closed: a kiting flamethrower. Now a breath,
once breathed, needs `recharge` turns (an attack's own field, else 3 for a
`delivery: breath` attack) before it can come again, and meanwhile the
creature comes in with tooth and claw. The turn it is ready again the hero
who can see it is told ("Smoke curls from the Young Red Dragon's jaws.").

Named foes (gate bosses, mini-bosses, seal demons) keep their tuned
flurries: their breaths recharge only when their data sets `recharge`.
Fafnir keeps his own clock (_breath_cd), the same three turns.

The state is `_recharge` ({attack name: turns}) in the creature's own
__dict__, written as a new dict every time (the simulator's copies and a
split body share nothing). Pure module.
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_breath knob (0 = the old rule)
RECHARGE_DEFAULT = {'breath': 3}


def _delivery(atk) -> str:
    try:
        import guards
        return str(guards.delivery(atk) or '')
    except (ImportError, AttributeError):
        return str((atk or {}).get('delivery', '') or '')


def recharge_of(m, atk) -> int:
    """Turns this attack needs after use (0: none)."""
    if not isinstance(atk, dict):
        return 0
    if 'recharge' in atk:
        return max(0, int(atk.get('recharge') or 0))
    if kind_data.named(m):
        return 0
    if atk.get('delivery') != 'breath':
        return 0
    return int(RECHARGE_DEFAULT.get('breath', 3))


def recharging_kind(m) -> bool:
    """It has an attack that must be drawn up again (its tell)."""
    return any(recharge_of(m, a) > 0 for a in getattr(m, 'attacks', None) or ())


def ready(m, atk) -> bool:
    if not ENABLED or not isinstance(atk, dict):
        return True
    left = (m.__dict__.get('_recharge') or {}).get(atk.get('name', ''), 0)
    return int(left or 0) <= 0


def spend(m, atk) -> None:
    """It used this attack: start its recharge."""
    if not ENABLED:
        return
    n = recharge_of(m, atk)
    if n <= 0:
        return
    rc = dict(m.__dict__.get('_recharge') or {})
    rc[atk.get('name', '')] = n
    m._recharge = rc


def tick(m) -> None:
    """One turn (Monster.tick_effects): each recharge counts down. A breath
    ready again leaves its line for a hero who can see it (only in a fight)."""
    rc = m.__dict__.get('_recharge')
    if not rc:
        return
    new, ready_now = {}, []
    for name, left in rc.items():
        left = int(left or 0) - 1
        if left > 0:
            new[name] = left
        else:
            ready_now.append(name)
    m._recharge = new
    if ready_now and m.__dict__.get('_tracking') and getattr(m, 'alive', False):
        atk = next((a for a in getattr(m, 'attacks', None) or ()
                    if isinstance(a, dict) and a.get('name') == ready_now[0]), None)
        if atk is not None:
            ai_lines.say(m, ready_line(m, atk), '')


def ready_line(m, atk) -> str:
    r = kind_data.rules('breath')
    lines = r.get('ready_lines') or {}
    text = lines.get(str(atk.get('type', '') or ''), '') or lines.get('default', '')
    return ai_lines.fill(m, text)


def is_distance(atk) -> bool:
    from monster import _RANGED_WORDS
    name = str(atk.get('name', '')).lower()
    return bool(atk.get('ranged')) or any(w in name for w in _RANGED_WORDS)


def has_shot(m) -> bool:
    """It has a distance attack ready now."""
    return any(is_distance(a) and ready(m, a) for a in getattr(m, 'attacks', None) or ())


def has_close(m) -> bool:
    """It has a blow ready for a hero beside it."""
    return any(not is_distance(a) and ready(m, a) for a in getattr(m, 'attacks', None) or ())


def drawing(m) -> bool:
    """Its only distance attacks are drawing breath (the ranged AI closes in
    with tooth and claw, or keeps off if it has none)."""
    if not ENABLED:
        return False
    far = [a for a in getattr(m, 'attacks', None) or () if is_distance(a)]
    return bool(far) and not any(ready(m, a) for a in far)


def choose(m, atk, player):
    """The attack it uses: ``atk`` if ready, else another that is (never a
    blow from afar), else None (it spends the turn drawing breath)."""
    if ready(m, atk):
        return atk
    near = m._adjacent_to(player)
    pool = [a for a in getattr(m, 'attacks', None) or () if ready(m, a)]
    if not near:
        pool = [a for a in pool if is_distance(a)]
    return random.choice(pool) if pool else None


def flurry(m, attacks, limit: int = 0) -> list:
    """The attacks a flurry fires: those ready, in order, up to ``limit``."""
    if not ENABLED:
        return list(attacks[:limit]) if limit > 0 else list(attacks)
    ok = [a for a in attacks if ready(m, a)]
    return ok[:limit] if limit > 0 else ok


def drawing_line(m) -> str:
    return ai_lines.fill(m, kind_data.rules('breath').get('drawing_line', ''))
