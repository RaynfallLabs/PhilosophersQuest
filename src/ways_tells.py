"""The tells of the third wave of monster behaviour (AI-3, 2026-11-20): one
list of keys for src/tells.py from each behaviour's own module (holds,
auras, caster_ai, home_ground, monster_kit, skittish, second_shape), so the
tells and the code never disagree. Pure module."""
from __future__ import annotations


def tell_keys(m) -> list:
    keys = []
    for mod_name in ('holds', 'auras', 'caster_ai', 'home_ground', 'monster_kit',
                     'skittish', 'second_shape'):
        try:
            mod = __import__(mod_name)
        except ImportError:
            continue
        for k in mod.tell_keys(m):
            if k not in keys:
                keys.append(k)
    return keys
