"""What a monster's behaviour leaves for the Game to say (AI-1, 2026-11-19).

A behaviour module (breath, morale, summoning, light_shy, alarm,
death_throes, relurk...) cannot print: only the Game knows whether the hero
can see the creature. It leaves (seen, unseen, colour) here; after the
monster's turn the Game says the seen line if he can see it, the unseen one
(a sound, never a name) if he cannot (CombatMixin._say_ai_lines). Lines a
blow on the creature leaves (a chant broken) are said on its next turn.
Pure module.
"""
from __future__ import annotations

MAX_LINES = 6        # the simulator never reads them: keep the list short


def fill(m, text: str, **kw) -> str:
    """``text`` with the creature put in (monster.fill), a capital first."""
    from monster import fill as _fill
    t = _fill(m, text or '', **kw)
    return t[:1].upper() + t[1:]


def say(m, seen: str, unseen: str = '', colour: str = 'warning') -> None:
    if not (seen or unseen) or m is None:
        return
    lines = list(m.__dict__.get('_ai_lines') or ())    # a new list: copies share none
    lines.append((seen or '', unseen or '', colour))
    m._ai_lines = lines[-MAX_LINES:]


def take(m) -> list:
    """The lines waiting, oldest first; the list is emptied."""
    return list(m.__dict__.pop('_ai_lines', None) or ())


def once(m, key: str) -> bool:
    """True the first time ``key`` is asked of this creature (a line said
    once a fight or once a life)."""
    said = set(m.__dict__.get('_ai_said') or ())
    if key in said:
        return False
    said.add(key)
    m._ai_said = said
    return True


def forget(m, key: str) -> None:
    said = set(m.__dict__.get('_ai_said') or ())
    said.discard(key)
    m._ai_said = said
