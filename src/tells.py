"""Tells: a dangerous creature shows what it can do (Dungeon Alive slice 5).

Brandon: "players need to pay attention to lore, weaknesses, abilities (stay
away from things that can confuse! use ranged!)". The first time in a run
that the hero sees a kind, the Chronicler says its worst tell and what to do
about it. Observe (O) says them all, any time. Every tell comes from
what the creature really does: an attack effect in data/monsters.json, or
one of its flags (data/tells.json). Pure module.
"""
from __future__ import annotations

import json

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'tells.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def abilities(m) -> list:
    """The tell keys of a creature, worst first."""
    d = data()
    have = set()
    floor = float(d.get('min_chance', 0.1))
    for atk in getattr(m, 'attacks', None) or ():
        eff = atk.get('effect') if isinstance(atk, dict) else None
        if eff and float(atk.get('effect_chance', 1.0) or 0) >= floor:
            have.add(eff)
    for flag in ('gaze_paralyze', 'splits', 'revive_once_on_death', 'drain_heals_self',
                 'regeneration', 'summon_kind', 'pull_chance', 'sp_drain', 'can_charge',
                 'can_phase_blink'):
        if getattr(m, flag, None):
            have.add(flag)
    order = d['order']
    return [k for k in order if k in have and k in d['effects']]


def lines(m, limit: int | None = None) -> list:
    from monster import the_name
    d = data()
    out = []
    for key in abilities(m)[:limit or int(d.get('max_lines', 2))]:
        t = d['effects'][key].replace('{The}', the_name(m)).replace('{the}', the_name(m, lower=True))
        out.append(t[:1].upper() + t[1:])
    return out
