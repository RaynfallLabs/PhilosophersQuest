"""Light-Shy and Snuff the Light (AI-1, light_shy_and_snuff, 2026-11-19).

Trolls turn to stone in the sun (the Norwegian tales of Asbjornsen and
Moe), the dwarf Alviss talked until sunrise and was stone (Alvissmal), the
dark elves and the shadows dwell where no light comes. Underground no sun
rises, but a strong light is the next best thing:

  * a `light_shy` creature within the reach of a lit hero's light needs
    more to hit him: +2 for each point of the light's glare (a carried
    torch or lantern 1, the Light spell 2, a named light its own), at most
    +4. Its first flinch in a fight is told ("The Troll flinches from your
    light.");
  * a light-shy creature that regenerates (the trolls) cannot close its
    wounds while it stands in the light (the giants' Fire and Dawn block,
    `_regen_blocked`, a turn at a time): "The Troll's wounds stop closing
    in your light.";
  * one that turns to stone in daylight (`turns_to_stone_in_light`: the
    trolls, the dvergar) stiffens in the Light SPELL's glare: three turns
    of it and it is slowed for three (never petrified; named foes never).

And some put the light out (an attack's `snuffs_light`): a water
elemental's wave drowns a torch, a whirlwind's gust blows it out, a
darkmantle or a shadow smothers it. A landed blow douses the light in the
hero's hand, and it will not light again for a few turns (the wick is
soaked: water 3, wind 1, dark 2); 'dark' also ends the Light spell. A light
that never burns out or has a power of its own (the Everburning Lamp,
Jack's Lantern, Hecate's Torch, Psyche's Lamp, the Hero's Lamp) is divine
or fey fire and is never snuffed. The price of a light stays: a lit hero is
seen from farther (senses.sight_range). Pure module.
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_light knob


def rules() -> dict:
    return kind_data.rules('light_shy')


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def glare(player) -> int:
    """The brightest of the hero's lights, as glare (0 in the dark)."""
    try:
        import lights
    except ImportError:
        return 0
    r = rules()
    best = 0
    lt = lights.held(player)
    if lights.is_lit(lt):
        by_id = r.get('glare_by_light') or {}
        best = max(best, int(by_id.get(getattr(lt, 'id', ''), r.get('carried', 1))))
    has = getattr(player, 'has_effect', None)
    if has is not None and has('light'):
        best = max(best, int(r.get('spell', 2)))
    if lights.weapon_aura(player) > 0:
        best = max(best, int(r.get('weapon', 1)))
    return best


def reach(player) -> int:
    """How far the hero's light falls (its sight), at least the tile beside him."""
    try:
        import lights
        return max(1, int(lights.light_bonus(player)))
    except Exception:
        return 1


def shy(m) -> bool:
    return bool(ENABLED and kind_data.field(m, 'light_shy', False) and not kind_data.named(m))


def in_light(m, player, dungeon=None) -> bool:
    """Within the reach of the hero's light and, given the floor, with
    nothing between: light goes through no wall and no shut door."""
    g = glare(player)
    if g <= 0 or _cheb(m.x, m.y, player.x, player.y) > reach(player):
        return False
    if dungeon is None:
        return True                       # (the simulator's fight; a blow, which has its line)
    import senses
    from geom import occupied_tiles
    return any(_cheb(x, y, player.x, player.y) <= 1
               or senses.clear_view(x, y, player.x, player.y, dungeon)
               for x, y in occupied_tiles(m))


def flinch(m, player) -> int:
    """The to-hit a light-shy creature loses in the hero's light (ai_blow)."""
    if not shy(m) or not in_light(m, player):
        return 0
    shift = min(int(rules().get('cap', 4)), int(rules().get('per_glare', 2)) * glare(player))
    if shift > 0 and ai_lines.once(m, 'flinch'):
        ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('flinch', '')), '')
    return shift


def light_turn(m, player, dungeon=None) -> None:
    """A light-shy creature's turn in the hero's light (BehaviourMixin, and
    the simulator's world tick): a troll's wounds stop closing; a troll in
    the Light spell's glare stiffens."""
    if not shy(m) or not getattr(m, 'alive', False) or not in_light(m, player, dungeon):
        m.__dict__.pop('_stiff', None)
        return
    lines = rules().get('lines') or {}
    if int(getattr(m, 'regeneration', 0) or 0) > 0:
        m._regen_blocked = max(int(m.__dict__.get('_regen_blocked', 0) or 0), 1)
        if m.hp < m.max_hp and ai_lines.once(m, 'unmended'):
            ai_lines.say(m, ai_lines.fill(m, lines.get('unmended', '')), '')
    has = getattr(player, 'has_effect', None)
    if kind_data.field(m, 'turns_to_stone_in_light', False) and has is not None and has('light'):
        n = int(m.__dict__.get('_stiff', 0) or 0) + 1
        if n >= int(rules().get('stiffen_turns', 3)):
            n = 0
            if m.add_effect('slowed', int(rules().get('slowed_turns', 3))):
                ai_lines.say(m, ai_lines.fill(m, lines.get('stiffen', '')), '')
        m._stiff = n


# ------------------------------------------------------------ the snuffing

def snuffable(lt) -> bool:
    try:
        import lights
    except ImportError:
        return False
    return (lights.is_lit(lt) and not lights.everlasting(lt) and not lights.power_of(lt))


def wet(lt) -> int:
    return int(getattr(lt, '_wet', 0) or 0)


def dry_tick(lt) -> None:
    """A turn for a soaked wick to dry (LightsMixin._light_tick)."""
    n = wet(lt)
    if n > 0:
        lt._wet = n - 1


def snuff(player, how: str) -> str:
    """Put the hero's light out ('water' | 'wind' | 'dark'). The line, or ''."""
    import lights
    r = rules()
    lines = r.get('lines') or {}
    out = []
    lt = lights.held(player)
    if lt is not None and lights.is_lit(lt):
        if snuffable(lt):
            lt.lit = False
            lt._wet = int((r.get('wet_turns') or {}).get(how, 2))
            out.append(lines.get('snuff_' + how, lines.get('snuff_dark', ''))
                       .replace('{light}', lights.noun(lt)))
        else:
            out.append(lines.get('everlasting', '').replace('{light}', lights.noun(lt)))
    if how == 'dark' and player.status_effects.pop('light', None):
        out.append(lines.get('spell_dark', ''))
    return ' '.join(t for t in out if t)


def after_blow(m, player, atk, actual: int, msg: str) -> str:
    """A landed blow with `snuffs_light` (ai_blow.after_blow)."""
    how = (atk or {}).get('snuffs_light') if isinstance(atk, dict) else None
    if not ENABLED or not how or actual <= 0:
        return msg
    if random.random() >= float(atk.get('snuff_chance', 1.0) or 1.0):
        return msg
    line = snuff(player, str(how))
    if line:
        msg += ' ' + ai_lines.fill(m, line)     # (the view narrows next turn: _light_tick)
    return msg
