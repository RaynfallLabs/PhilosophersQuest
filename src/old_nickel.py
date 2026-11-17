"""Old Nickel's voice: which of his lines he says, and when (Brandon,
2026-11-17: "Old Nickel is not nearly mean enough... make it clear he will
murder people in their sleep for their things, more lines of dialogue").

He is the kobold miser who wears the Bloomleaf Cloak (data/monsters.json
``old_nickel``; his AI is ``Monster._stalker_turn``, ai_pattern
``stalker_coward``). His lines live in data/old_nickel.json, grouped by the
moment that brings them:

* ``sight``: the first time the hero sees him.
* ``taunt`` (Brandon's rule 2): the hero moves toward him or around him in
  his sight, at most once every ``line_gap`` turns. The 'taunt' pool, with
  'iron' while the hero wears or carries iron and 'cloak' (the leaves he tore
  off a crying Bloomsaur), is said without repeats; once it has run out he
  says the 'recurring' lines, round and round, all of them egging the hero
  on to lie down and rest.
* ``dash``: he darts in on a hero who rests or is helpless, by what holds the
  hero ('dash_groups'); ``dash_unseen`` when the hero cannot see him, which
  never names him.
* ``prey_strike``: his blow on a hero at rest or helpless; ``strike``: now
  and then, his blow in a fight.
* ``cornered``, ``struck`` (the first time he is hurt), ``hurt`` (once at
  each share of ``hurt_at``) and ``death``.

What he has said is kept on him (``m._voice``), so it is saved with him.
Pure module: no pygame, no Game. The game says the lines
(emberpup_encounter.BloomleafMixin).
"""
from __future__ import annotations

import json

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'old_nickel.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def lines(moment: str, group: str = '') -> list:
    """The lines of one moment ('dash' takes a group: rest, held, dazed)."""
    got = (data().get('lines') or {}).get(moment) or []
    if isinstance(got, dict):
        got = got.get(group) or next(iter(got.values()), [])
    return [str(t) for t in got]


def voice(m) -> dict:
    """What he has said so far, kept on him."""
    v = m.__dict__.get('_voice')
    if not isinstance(v, dict):
        v = m.__dict__['_voice'] = {}
    v.setdefault('said', {})
    return v


def _cheb(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


# ---------------------------------------------------------------------------
# Picking
# ---------------------------------------------------------------------------

def pick_once(m, moment: str, rng, group: str = '') -> str:
    """A line of the moment he has not said yet; when every one has been
    said, the moment starts over."""
    pool = lines(moment, group)
    if not pool:
        return ''
    said = voice(m)['said'].setdefault(moment if not group else f'{moment}:{group}', [])
    left = [t for t in pool if t not in said]
    if not left:
        said.clear()
        left = list(pool)
    line = rng.choice(left)
    said.append(line)
    return line


def taunt_pool(iron: bool) -> list:
    """Rule 2's pool: the taunts, the iron lines while the hero has iron,
    and the cloak lines."""
    pool = lines('taunt') + lines('cloak')
    if iron:
        pool += lines('iron')
    return pool


def taunt(m, rng, iron: bool) -> str:
    """Rule 2: a line of the pool he has not said yet; once the pool has run
    out, the recurring lines in turn."""
    v = voice(m)
    said = v['said'].setdefault('taunt', [])
    left = [t for t in taunt_pool(iron) if t not in said]
    if left:
        line = rng.choice(left)
        said.append(line)
        return line
    rec = lines('recurring')
    if not rec:
        return ''
    i = int(v.get('recurring', 0) or 0)
    v['recurring'] = i + 1
    return rec[i % len(rec)]


def taunt_due(m, turn: int) -> bool:
    """Has ``line_gap`` passed since his last line?"""
    last = voice(m).get('last')
    return last is None or int(turn) - int(last) >= int(data().get('line_gap', 4))


def mark(m, turn: int) -> None:
    """He has just said a line."""
    voice(m)['last'] = int(turn)


def came_on(prev_hero, hero, at) -> bool:
    """Rule 2's trigger: the hero has moved, toward him or around him (not
    straight away from him, which is rule 4: he follows)."""
    if prev_hero is None or tuple(prev_hero) == tuple(hero):
        return False
    return _cheb(hero, at) <= _cheb(prev_hero, at)


def dash_line(prey: str, seen: bool, rng, m=None) -> str:
    """His line as he darts in on a hero held by ``prey`` ('resting',
    'sleeping', 'paralyzed', 'confused', 'stunned'). Unseen, the narration
    that never names him."""
    if not seen:
        pool = lines('dash_unseen')
        return rng.choice(pool) if pool else ''
    group = str((data().get('dash_groups') or {}).get(prey, 'rest'))
    if m is not None:
        return pick_once(m, 'dash', rng, group)
    pool = lines('dash', group)
    return rng.choice(pool) if pool else ''


def strike_line(m, turn: int, rng, prey: str = '') -> str:
    """After one of his blows lands: on a hero at rest or helpless, always a
    'prey_strike' line; in a fight, now and then a 'strike' line."""
    if prey:
        return pick_once(m, 'prey_strike', rng)
    d = data()
    last = voice(m).get('last')
    if last is not None and int(turn) - int(last) < int(d.get('strike_gap', 3)):
        return ''
    if rng.random() >= float(d.get('strike_chance', 0.35)):
        return ''
    return pick_once(m, 'strike', rng)


def hurt_line(m, rng) -> str:
    """The first time he is below each share of ``hurt_at``: one line."""
    v = voice(m)
    done = v.setdefault('hurt', [])
    try:
        share = float(m.hp) / max(1.0, float(m.max_hp))
    except (TypeError, ValueError, AttributeError):
        return ''
    crossed = [t for t in data().get('hurt_at', ()) if share < float(t) and float(t) not in done]
    if not crossed:
        return ''
    done.extend(float(t) for t in crossed)
    return pick_once(m, 'hurt', rng)


def carries_iron(player) -> bool:
    """Does the hero wear or carry iron (anything that can rust: the one
    rust check, status_effects._can_rust)?"""
    from status_effects import _can_rust
    worn = []
    try:
        worn = list(player.worn_items())
    except Exception:
        worn = [getattr(player, 'weapon', None), getattr(player, 'shield', None)]
    for item in worn + list(getattr(player, 'inventory', None) or ()):
        try:
            if item is not None and _can_rust(item):
                return True
        except Exception:
            continue
    return False


def seen_chronicle() -> str:
    return str(data().get('seen_chronicle', '') or '')
