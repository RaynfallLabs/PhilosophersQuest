"""Knocked Down: a shove or a trample takes the hero off his feet, pure.

Brandon, 2026-11-22. A shove that beat his Strength save floors him, on
the shove's own roll; a landed trample asks a Dexterity save when nothing
else of that blow took hold. Guard keeps him standing, as it does when he
is Stunned; so do the boots (guards.py) and leaving the ground
(levitation). His next action is standing up, with no dodge until then,
and then he has his footing for a few turns.
"""
from __future__ import annotations

import random

import effect_rules


def stands(player, atk) -> bool:
    """Something of his own keeps him on his feet."""
    import action_gate
    if action_gate.steady(player) or player.has_effect('levitating'):
        return True
    if player.has_effect('footing') or player.has_effect('knocked_down'):
        return True
    import guards
    keep = guards.guard_keep(player, dict(atk or {}, effect='knocked_down'))[1]
    return keep < 1.0 and random.random() >= keep


def floors(atk) -> bool:
    """A trample that can take him off his feet. A gore, a tusk or an antler
    is a thrust: written ``"floors": false`` (data/monsters.json, by lore,
    tools/content/effects_pass_2026_11_22.py), it is still a trample for the
    boots' guard (guards.py) but floors no one."""
    return (isinstance(atk, dict)
            and atk.get('delivery') == effect_rules.data()['knockdown']['delivery']
            and atk.get('floors', True) is not False)


def from_shove(player, atk) -> str:
    """The shove has already beaten his Strength save: down he goes."""
    if stands(player, atk) or not player.add_effect('knocked_down', 1):
        return ''
    return ' ' + effect_rules.line('floored')


def from_trample(monster, player, atk, actual: int) -> str:
    if actual <= 0 or not floors(atk):
        return ''
    if stands(player, atk):
        return ''
    from status_effects import apply_debuff_with_save
    dc = min(18, int(atk.get('effect_save_dc', 12 + int(getattr(monster, 'min_level', 1) or 1) // 7)))
    _applied, said = apply_debuff_with_save(player, 'knocked_down', 1, dc, source=monster)
    return ' ' + said if said else ''
