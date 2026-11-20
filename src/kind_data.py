"""A monster kind's own data, read where the Monster class keeps no copy
(monster behaviour, first wave: AI-1, 2026-11-19).

The behaviour modules (breath.py, morale.py, life_drain.py, light_shy.py,
alarm.py, death_throes.py, relurk.py, shove.py, summoning.py, faction.py)
read their per-kind fields here: the creature's own value if it carries one
(a test, or a creature the game changed), else its kind's entry in
data/monsters.json, else the default. So a save from before the pass reads
the kind's new fields with no migration, and the simulator's copied
monsters (copy.copy) need nothing of their own.

The rules every one of them shares (numbers and lines) are in
data/monster_ai.json, one section a behaviour. Pure module.
"""
from __future__ import annotations

import json

_DEFS: dict | None = None
_RULES: dict | None = None


def defs() -> dict:
    """data/monsters.json, read once."""
    global _DEFS
    if _DEFS is None:
        from paths import data_path
        try:
            with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
                _DEFS = json.load(f)
        except (OSError, ValueError):
            _DEFS = {}
    return _DEFS


def rules(section: str | None = None) -> dict:
    """data/monster_ai.json, or one section of it."""
    global _RULES
    if _RULES is None:
        from paths import data_path
        try:
            with open(data_path('data', 'monster_ai.json'), encoding='utf-8') as f:
                _RULES = json.load(f)
        except (OSError, ValueError):
            _RULES = {}
    if section is None:
        return _RULES
    return _RULES.get(section) or {}


def reload() -> None:
    global _DEFS, _RULES
    _DEFS = None
    _RULES = None


def kind_def(m) -> dict:
    d = defs().get(str(getattr(m, 'kind', '') or ''))
    return d if isinstance(d, dict) else {}


def field(m, name: str, default=None):
    """The creature's ``name``: its own, else its kind's, else ``default``."""
    own = getattr(m, '__dict__', None)
    if isinstance(own, dict) and name in own:
        v = own[name]
        return default if v is None else v
    v = kind_def(m).get(name)
    return default if v is None else v


def named(m) -> bool:
    """A named foe (boss, mini-boss, seal demon): the behaviours leave its
    tuned fight alone unless they say otherwise."""
    return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False)
                or getattr(m, 'is_seal_demon', False))


def outside_rules(m) -> bool:
    """Never touched by the ordinary behaviours: the allied (angels), the
    encounter people, the unicorn, Death, the stalker (Old Nickel)."""
    return bool(getattr(m, 'is_allied', False)
                or getattr(m, '_npc_encounter_tag', None)
                or getattr(m, '_flavor_encounter_tag', None)
                or getattr(m, '_is_unicorn', False)
                or getattr(m, 'kind', '') == 'death'
                or getattr(m, 'ai_pattern', '') == 'stalker_coward'
                or getattr(m, 'stalker', None))


def tell_keys(m) -> list:
    """The tells the AI-1 behaviours give a creature (src/tells.py)."""
    keys = []
    atks = [a for a in (getattr(m, 'attacks', None) or ()) if isinstance(a, dict)]
    try:
        import breath
        if breath.recharging_kind(m):
            keys.append('breath_recharge')
    except ImportError:
        pass
    if any(a.get('type') == 'drain' or a.get('drains_life') for a in atks):
        keys.append('life_drain')
    if field(m, 'light_shy', False):
        keys.append('light_shy')
    if any(a.get('snuffs_light') for a in atks):
        keys.append('snuffs_light')
    if isinstance(field(m, 'alarm', None), dict):
        keys.append('raises_alarm')
    if isinstance(field(m, 'death_throes', None), dict):
        keys.append('death_throes')
    if field(m, 'relurks', False):
        keys.append('relurks')
    if field(m, 'hides_in_dark', False):
        keys.append('hides_in_dark')
    if any(a.get('shove') for a in atks):
        keys.append('shove')
    if getattr(m, 'ai_pattern', '') == 'healer':
        keys.append('heals_allies')
    return keys
