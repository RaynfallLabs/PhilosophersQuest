"""Back to the Web: an ambusher that hides again (AI-1, relurk, 2026-11-19).

Once sprung, an ambusher was an ordinary brawler for the rest of the floor.
A spider retreats to its web (natural history), the jorogumo to her
waterfall, and drops again. Now a sprung ambusher with `relurks` that is
hurt (under 60% of its health), has had no sight of the hero for three
turns and is not hunting him goes back into hiding: an ambusher again,
unaware, unseen until it springs (Monster.take_turn's ambush branch).
Once a life, and its second spring carries no surprise blow (a mimic's
first-blow crit is never set by an ambusher). A light, Hecate's Torch and
a family's Tremor-Sense find it as they find any lurker (unseen.py).
Pure module.
"""
from __future__ import annotations

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_relurk knob


def consider(m, player=None) -> bool:
    """Called when it has not found the hero this turn. True if it went back
    into hiding (a hero near enough hears it go)."""
    if not ENABLED or not kind_data.field(m, 'relurks', False):
        return False
    d = m.__dict__
    if d.get('_relurked') or kind_data.named(m) or getattr(m, 'ai_pattern', '') != 'aggressive':
        return False
    if not getattr(m, '_aware', False) or d.get('_tracking'):
        return False
    r = kind_data.rules('relurk')
    if m.hp >= m.max_hp * float(r.get('hurt_share', 0.6)):
        return False
    if int(d.get('_lost_turns', 0) or 0) < int(r.get('lost_turns', 3)):
        return False
    m._relurked = True
    m.ai_pattern = 'ambush'
    m._aware = False
    m._alerted = False
    m._goal = None
    m._searching = False
    m._mimic_surprise = False
    if player is not None and max(abs(m.x - player.x), abs(m.y - player.y)) <= int(
            r.get('heard_reach', 8)):
        ai_lines.say(m, '', str(r.get('line_unseen', '') or ''))
    return True
