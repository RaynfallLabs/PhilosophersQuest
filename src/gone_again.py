"""Gone Again: a hit-and-run creature really hides (AI-1,
hit_and_run_vanishes, 2026-11-19).

Asterion and the two elder vampires walk off through the walls. The other
hit-and-run kinds (the imp, the quasit, the puca, the boggart, the shade,
the brigand, Hugin...) could not: after their one or two blows they stepped
three tiles off and stood there for four to six turns, in plain sight,
taking the hero's free blows. The boggart and the puca of the house-spirit
tales vanish and come back; the imp of the fable is gone the moment you
turn.

Now, when one of them breaks off, it goes to the nearest tile out of the
hero's sight (a search of at most a dozen tiles: round a corner, behind a
pillar) and hides there. If the hero comes within two tiles of it or sees
it there, the hiding is over and it fights; a blow on it ends it at once.
One that hides in the dark (`hides_in_dark`: the shade, the shadow demon,
the quasit, the imp, the boggart) is unseen while it hides if the hero
carries no light and cannot see the invisible (a lit light leaves it no
dark to hide in). No spot to hide: it backs off as before. Pure module.
"""
from __future__ import annotations

from collections import deque

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_vanish knob


def rules() -> dict:
    return kind_data.rules('gone_again')


def applies(m) -> bool:
    return bool(ENABLED and not getattr(m, 'can_phase_walls', False)
                and not kind_data.named(m))


def _view(dungeon, a, b) -> bool:
    import senses
    return senses.clear_view(a[0], a[1], b[0], b[1], dungeon)


def hiding_spot(m, player, dungeon, monsters, extra_occupied):
    """(spot, first step) of the nearest tile out of the hero's sight, or
    None."""
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles(monsters or [], exclude=m))
    if extra_occupied:
        occ |= set(extra_occupied)
    occ.add((player.x, player.y))
    hero = (player.x, player.y)
    start = (m.x, m.y)
    limit = int(rules().get('search_tiles', 12))
    prev = {start: None}
    q = deque([(start, 0)])
    while q:
        cur, d = q.popleft()
        if cur != start and not _view(dungeon, cur, hero) and max(
                abs(cur[0] - hero[0]), abs(cur[1] - hero[1])) > int(rules().get('spot_reach', 2)):
            step = cur
            while prev[step] != start:
                step = prev[step]
            return cur, step
        if d >= limit:
            continue
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if not ox and not oy:
                    continue
                nxt = (cur[0] + ox, cur[1] + oy)
                if nxt in prev or nxt in occ or not m._can_move_to(dungeon, *nxt):
                    continue
                prev[nxt] = cur
                q.append((nxt, d + 1))
    return None


def retreat(m, player, dungeon, monsters, extra_occupied) -> bool:
    """One turn of breaking off: a step toward cover; at cover it hides.
    True if it handled the turn (False: no cover, back off as before)."""
    spot = m.__dict__.get('_hide_spot')
    hero = (player.x, player.y)
    if spot is None or _view(dungeon, tuple(spot), hero):
        found = hiding_spot(m, player, dungeon, monsters, extra_occupied)
        if found is None:
            return False
        if spot is None:
            break_off_line(m)                 # the turn it breaks off
        spot = found[0]
        m._hide_spot = spot
    if (m.x, m.y) == tuple(spot) or not _view(dungeon, (m.x, m.y), hero):
        begin_hiding(m, player)
        return True
    found = hiding_spot(m, player, dungeon, monsters, extra_occupied)
    if found is None:
        return False
    m._hide_spot = found[0]
    m.x, m.y = found[1]
    if not _view(dungeon, (m.x, m.y), hero):
        begin_hiding(m, player)
    return True


def begin_hiding(m, player) -> None:
    import random
    m._hit_run_state = 'hiding'
    m._hit_run_timer = random.randint(4, 6)
    m._struck = False
    m.__dict__.pop('_hide_spot', None)
    dark_hide(m, player)


def dark_hide(m, player) -> None:
    """In the dark, with no light and no eye for the unseen, it is unseen."""
    import unseen
    try:
        import light_shy
        lit = light_shy.glare(player) > 0
    except ImportError:
        lit = False
    hidden = bool(kind_data.field(m, 'hides_in_dark', False) and not lit
                  and not unseen.sees_invisible(player))
    if hidden:
        if not m.__dict__.get('_dark_hidden'):
            ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('dark', '')), '')
        m._dark_hidden = True
        m._unseen = not unseen.senses(m, player)
    else:
        end_dark(m)


def end_dark(m) -> None:
    if m.__dict__.pop('_dark_hidden', None):
        if not getattr(m, 'invisible', False):
            m._unseen = False


def hiding_turn(m, player, dungeon) -> bool:
    """While it hides: True when the hiding is over (found, or struck)."""
    hero = (player.x, player.y)
    near = max(abs(m.x - hero[0]), abs(m.y - hero[1])) <= int(rules().get('spot_reach', 2))
    if m.__dict__.get('_struck') or near or (
            not m.__dict__.get('_dark_hidden') and _view(dungeon, (m.x, m.y), hero)):
        m._hit_run_state = 'hunting'
        m._hit_run_attacks = 0
        end_dark(m)
        return True
    dark_hide(m, player)
    return False


def break_off_line(m) -> None:
    ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('vanish', '')), '')
