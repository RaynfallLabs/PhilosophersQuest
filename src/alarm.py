"""Raise the Alarm: the shout across the room (AI-1, raise_the_alarm,
2026-11-19).

A creature called for help only when it stood beside the hero, and only
its own kind heard (Monster.alert_nearby); only packs and war-bands had an
alarm of their own. Juno's geese woke Rome (Livy); Odin's ravens Hugin and
Munin fly over the world and tell him what they see; the kobolds of the
mines knock; a goblin who spots a stranger yells.

Now a creature with `alarm` ({radius, tags?, line, line_unseen}) that first
sees the hero (senses.notice, its first sight) shouts, once a floor, and
every creature of its side that the sound reaches within `radius` (along
open ground, round corners, a shut door muffling it: senses.sound_map) is
roused to him: its own kind, its war-band, its pack, its family, or a
listed tag. A sleeper wakes as to any loud noise; the Hand of Glory keeps
sleepers asleep. It rouses only creatures already on the floor: nothing
new comes. Kill or silence the lookout first, or never be seen by it.
Pure module.
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_alarm knob


def spec(m):
    a = kind_data.field(m, 'alarm', None)
    return a if isinstance(a, dict) else None


def _side(m, o, tags) -> bool:
    import faction
    if faction.same_side(m, o):
        return True
    return bool(tags and set(tags) & set(getattr(o, 'tags', None) or ()))


def shout(m, monsters, player, dungeon, rng=random) -> int:
    """It has just seen the hero for the first time: the alarm, once a
    floor. Returns how many it roused."""
    a = spec(m)
    if not ENABLED or a is None or m.__dict__.get('_alarm_used'):
        return 0
    if (kind_data.named(m) or kind_data.outside_rules(m) or m.has_effect('sleeping')
            or m.has_effect('feared')):
        return 0
    # A silenced lookout has no voice to shout with; a babbled one's shout is
    # in a tongue its own no longer understand (attack_gates.py, the hero's
    # Tacita's Seal and Confusion of Tongues).
    try:
        import attack_gates
        if attack_gates.has(m, 'silenced') or attack_gates.babbled(m):
            return 0
    except ImportError:
        if m.has_effect('silenced'):
            return 0
    m._alarm_used = True
    import senses
    import sleepers
    radius = int(a.get('radius', kind_data.rules('alarm').get('default_radius', 10)))
    reach = senses.sound_map(dungeon, m.x, m.y, radius) if dungeon is not None else None
    tags = list(a.get('tags') or ())
    n = 0
    for o in monsters or ():
        if o is m or not senses._listens(o) or not _side(m, o, tags):
            continue
        if kind_data.named(o) or o.__dict__.get('_tracking'):
            continue
        if reach is not None:
            if (o.x, o.y) not in reach:
                continue
            d = reach[(o.x, o.y)]
        else:
            d = max(abs(o.x - m.x), abs(o.y - m.y))
            if d > radius:
                continue
        if o.has_effect('sleeping'):
            if sleepers.factor(player, 'take') <= 0:
                continue                         # the Hand of Glory
            if rng.random() >= senses._wake_p(o, 'alarm', d, radius, player):
                continue
        senses.rouse(o, player.x, player.y)
        n += 1
    ai_lines.say(m, ai_lines.fill(m, a.get('line', '')), str(a.get('line_unseen', '') or ''))
    return n
