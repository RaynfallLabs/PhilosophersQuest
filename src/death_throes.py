"""Death Throes: it bursts when it dies (AI-1, death_throes, 2026-11-19).

A burning skeleton flares, a fire beetle's glands burst (the bombardier
beetle's spray, natural history), a myconid looses its spores (the
puffball), a plague corpse bursts (the Black Death's fear of the dead), a
salamander's fire goes out in a flash. When a creature with `death_throes`
({type, share, radius, effect?, effect_duration?, line, warn_line,
delivery?}) dies, everything beside it, the hero and his pet's foes alike,
takes the blast: floor_curve.wound(share) of its OWN health (so a blast is
as dangerous to a small creature as to a big one) in the throes' type, and
the rider through the usual save. A `share: 0` blast is a rider only (a
cry); `delivery: "voice"` makes it a sound wax in the ears stops.

It swells the turn before: once under a quarter of its health it shows it
("The Fire Beetle's glands glow white-hot!"), so a hero who reads it steps
back or finishes it from range. Not a banished creature, nor one turned to
ash, nor a named foe (their deaths are scripted). A creature killed by
another's throes bursts after it, one at a time (a queue, never inside the
first: BehaviourMixin._ai_throes). The hero gets the kills it makes.
Pure module; the Game applies the blast.
"""
from __future__ import annotations

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_throes knob


def spec(m):
    t = kind_data.field(m, 'death_throes', None)
    return t if isinstance(t, dict) else None


def should_burst(m) -> bool:
    if not ENABLED or spec(m) is None or kind_data.named(m):
        return False
    d = m.__dict__
    if d.get('_throes_done') or d.get('_banished') or d.get('_ashed') or d.get('_danced_down'):
        return False
    return True


def warn(m) -> None:
    """Under a quarter of its health it swells (its line, once)."""
    t = spec(m)
    if t is None or not ENABLED or not getattr(m, 'alive', False) or kind_data.named(m):
        return
    share = float(kind_data.rules('death_throes').get('warn_share', 0.25))
    if m.hp < m.max_hp * share and t.get('warn_line') and ai_lines.once(m, 'throes_warn'):
        ai_lines.say(m, ai_lines.fill(m, t['warn_line']), '')


def reach_of(m) -> int:
    return max(1, int((spec(m) or {}).get('radius', 1) or 1))


def in_blast(m, x: int, y: int, dungeon) -> bool:
    if max(abs(m.x - x), abs(m.y - y)) > reach_of(m):
        return False
    if dungeon is None:
        return True
    import senses
    return senses.clear_view(m.x, m.y, x, y, dungeon)


def blast(m, max_hp: int, named: bool = False) -> int:
    from floor_curve import wound
    return wound(float((spec(m) or {}).get('share', 0) or 0), int(max_hp), named)
