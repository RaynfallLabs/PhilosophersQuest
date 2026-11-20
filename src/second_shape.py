"""Second Shape: a changer turns mid-fight (monster behaviour, third wave:
AI-3, shapechange, 2026-11-20).

The nahual of Mesoamerican lore is a sorcerer who takes his animal shape,
the jaguar; the werewolf trials of early modern Europe tell of the man who
becomes the wolf. A kind with ``enraged_form`` (data/monsters.json, beside
its ``enrage_at_hp_pct`` and ``enraged_pattern``)

    {"attacks": [...], "speed": N, "multi_attack_count": N,
     "resistances": [...], "shrugs_off": [...], "line": "..."}

takes that shape when its one-way enrage fires (Monster.take_turn): its
attacks, speed and the rest are swapped once, its health kept; the line
says what the hero sees. Its name stays (the line tells the change); its
corpse and its study stay its kind's. The form is ordinary attributes, so it
is pickled with the creature; ``_form_applied`` keeps it from being applied
twice. Pure module; the simulator's enrage calls the same apply().
"""
from __future__ import annotations

import kind_data

ENABLED = True          # the simulator's ai3_shape knob
_FIELDS = ('attacks', 'speed', 'multi_attack_count', 'resistances', 'shrugs_off',
           'weaknesses')


def form(m) -> dict | None:
    f = kind_data.field(m, 'enraged_form', None)
    return f if isinstance(f, dict) else None


def apply(m) -> str:
    """Take the second shape (once). The line, or ''."""
    if not ENABLED or m.__dict__.get('_form_applied'):
        return ''
    f = form(m)
    if f is None or kind_data.outside_rules(m):
        return ''
    for k in _FIELDS:
        if k in f:
            v = f[k]
            setattr(m, k, list(v) if isinstance(v, list) else v)
    m._form_applied = True
    import ai_lines
    return ai_lines.fill(m, str(f.get('line', '') or ''))


def tell_keys(m) -> list:
    return ['second_shape'] if form(m) else []
