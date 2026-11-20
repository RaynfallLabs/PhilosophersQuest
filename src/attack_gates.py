"""Attack gates: what a monster cannot use right now (MONSTERS AND MAGIC, 2026-11-19).

Three monster statuses the hero's magic lays on a foe (rules in data/wards.json
'gates'):

* ``silenced`` (Tacita's Seal, the Hush of the Feralia, the Sceptre of
  Agamemnon's blow): no voice attack (a wail, a song, a scream), no magic cast
  from range, no summoning, no healing. A silenced summoner or healer has to
  come and fight with what it has. The mouthless (oozes, plants, constructs)
  cannot be silenced: they have no voice to take.
* ``unstrung`` (the Wand of Unstringing): no missile, no breath and no gaze, its
  opener from range too. An archer or a dragon has to come to the hero.
* ``babbled`` (the Confusion of Tongues): its pack or war band forgets how to
  fight together (packs.py reads it: no surround, no corridor hold, no tricks).

A named foe holds silenced or unstrung ``named_turns`` at most, and after it
shakes off the next for ``named_grace`` turns (``gate_grace``).

Pure: hooks in monster.py ask ``blow_gate`` (Monster._resolve_blow),
``blocks_attack`` (the opener and the gaze), ``may_summon``, and ``must_close``
(Monster.take_turn); ``close_in`` is the closing turn itself.
"""
from __future__ import annotations

GATES = ('silenced', 'unstrung')


def rules() -> dict:
    import wards
    return wards.data()['gates']


def _named(m) -> bool:
    try:
        return bool(m._is_named_foe())
    except Exception:
        return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False))


def _family(m):
    try:
        import family_lore
        return family_lore.family_of(m)
    except Exception:
        return None


def has(m, status: str) -> bool:
    try:
        return int((getattr(m, 'status_effects', None) or {}).get(status, 0) or 0) > 0
    except (TypeError, ValueError):
        return False


def mouthless(m) -> bool:
    """No mouth to silence: an ooze, a plant, a construct (by family), or a
    kind whose own status_immune says so."""
    if 'silenced' in (getattr(m, 'status_immune', None) or ()):
        return True
    return _family(m) in set(rules().get('mouthless_families') or ())


def speaks(m) -> bool:
    """A creature with a language of its own (Babel): by family, or tagged
    humanoid."""
    if _family(m) in set(rules().get('speaking_families') or ()):
        return True
    return bool(set(getattr(m, 'tags', None) or ()) & set(rules().get('speaking_tags') or ()))


def is_person(m) -> bool:
    """Men, goblins and giants: those who can hate (Settled Strife)."""
    return _family(m) in set(rules().get('people_families') or ())


def inflict(m, status: str, turns: int) -> int:
    """Lay ``status`` (silenced, unstrung, babbled) on ``m`` for ``turns``.
    Returns the turns it now has (0: refused). The mouthless cannot be
    silenced; a named foe holds a gate ``named_turns`` at most and shakes
    off the next for ``named_grace`` turns after."""
    if m is None or not getattr(m, 'alive', True):
        return 0
    if status == 'silenced' and mouthless(m):
        m.__dict__['_refused_effect'] = status
        return 0
    turns = max(1, int(turns))
    if status in GATES and _named(m):
        if has(m, 'gate_grace'):
            return 0
        if has(m, status):
            return int(m.status_effects[status])
        nt = int(rules().get('named_turns', 3))
        m.status_effects[status] = min(turns, nt)
        m.status_effects['gate_grace'] = min(turns, nt) + int(rules().get('named_grace', 3))
        return int(m.status_effects[status])
    cur = int(m.status_effects.get(status, 0) or 0)
    try:
        from status_effects import MAX_EFFECT_DURATION as _cap
    except Exception:
        _cap = 60
    m.status_effects[status] = min(max(cur, turns), _cap)
    return int(m.status_effects[status])


# ---------------------------------------------------------------------------
# Which attacks a gate stops
# ---------------------------------------------------------------------------

def _delivery(atk) -> str:
    try:
        import guards
        return guards.delivery(atk or {})
    except Exception:
        return str((atk or {}).get('delivery', 'blow'))


def _is_gaze(atk) -> bool:
    low = str((atk or {}).get('name', '')).lower()
    return _delivery(atk) == 'gaze' or 'gaze' in low or 'evil eye' in low


def blocks_attack(m, atk) -> str:
    """'' when ``m`` may use ``atk`` now, else the gate's line key."""
    if m is None or not atk:
        return ''
    d = _delivery(atk)
    if has(m, 'silenced'):
        if d == 'voice':
            return 'silenced'
        if d == 'ranged' and str(atk.get('type', '')) == 'magic':
            return 'silenced_cast'
    if has(m, 'unstrung'):
        if _is_gaze(atk):
            return 'unstrung_gaze'
        if d in ('ranged', 'breath'):
            return 'unstrung'
    return ''


def _line(key: str, m, atk=None) -> str:
    text = (rules().get('lines') or {}).get(key, '')
    try:
        from monster import fill, attack_noun
        out = fill(m, text, attack=attack_noun(atk or {}))
    except Exception:
        out = text
    return out[:1].upper() + out[1:] if out else out


def gaze_line(m) -> str:
    return _line('unstrung_gaze', m)


def blow_gate(m, atk, player):
    """(atk, None) to go on with ``atk`` (or another attack it may use beside
    the hero), or (None, (0, line)) when it cannot strike this turn."""
    why = blocks_attack(m, atk)
    if not why:
        return atk, None
    # Beside the hero it fights with what it still may use.
    try:
        beside = m._adjacent_to(player)
    except Exception:
        beside = False
    if beside:
        left = [a for a in (getattr(m, 'attacks', None) or ()) if not blocks_attack(m, a)]
        if left:
            import random
            return random.choice(left), None
    return None, (0, _line(why, m, atk))


def may_summon(m) -> bool:
    return not has(m, 'silenced')


def must_close(m) -> bool:
    """A silenced summoner or healer, an unstrung archer or dragon: its own
    way of fighting is shut, so it comes to the hero as the aggressive do."""
    pat = getattr(m, 'ai_pattern', '')
    if has(m, 'silenced') and pat in ('summoner', 'healer'):
        return True
    if has(m, 'unstrung') and pat in ('ranged', 'dragon'):
        return True
    return False


def close_in(m, player, dungeon, all_monsters, extra_occupied) -> bool:
    """The closing turn of a gated caster or archer: find the hero, step
    toward him, strike when beside him. Returns True when it attacks."""
    if not m._spots_player(player, dungeon, all_monsters, extra_occupied):
        return False
    if m._adjacent_to(player):
        return True
    if m._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive'):
        return True
    return bool(m._adjacent_to(player))


def babbled(m) -> bool:
    return has(m, 'babbled')
