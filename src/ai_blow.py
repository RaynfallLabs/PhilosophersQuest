"""What the AI-1 behaviours add to one monster blow (AI-1, 2026-11-19).

Two hooks in Monster._resolve_blow, so the blow's own code stays as it was:

  to_hit_shift(m, player, atk)   added to the roll the blow needs (higher is
                                 harder): a creature at bay strikes truer
                                 (morale), a light-shy one flinches from a
                                 bright light (light_shy), a cursed one
                                 misses more;
  after_blow(m, player, atk, actual, msg) -> msg
                                 after the blow landed (actual is what got
                                 through): five blows in a row that do
                                 nothing break a creature's nerve (morale);
                                 a drain touch takes life that does not come
                                 back with rest (life_drain); a wave or a gust
                                 puts the hero's light out (light_shy); a
                                 giant's blow throws him back (shove).

Pure module.
"""
from __future__ import annotations

CURSED_TO_HIT = 2            # status_effects 'cursed': "Misses more: -2 to hit"


def to_hit_shift(m, player, atk) -> int:
    shift = 0
    try:
        import morale
        shift += morale.at_bay_hit(m)
    except ImportError:
        pass
    try:
        import light_shy
        shift += light_shy.flinch(m, player)
    except ImportError:
        pass
    try:
        import tactical_mind
        shift += tactical_mind.hit_shift(m)      # a feint's waiting blow (AI-2)
    except ImportError:
        pass
    if m.has_effect('cursed'):
        shift += CURSED_TO_HIT                   # cursed (a wand's), it misses more
    return shift


def after_blow(m, player, atk, actual: int, msg: str) -> str:
    try:
        import morale
        morale.futile_blow(m, actual)
    except ImportError:
        pass
    for mod_name in ('life_drain', 'light_shy', 'shove', 'holds', 'caster_ai'):   # AI-3: holds, a resist seen
        try:
            mod = __import__(mod_name)
        except ImportError:
            continue
        fn = getattr(mod, 'after_blow', None)
        if fn is not None:
            msg = fn(m, player, atk, actual, msg)
    return msg
