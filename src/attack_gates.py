"""Attack gates: what a monster cannot use right now (MONSTERS AND MAGIC, 2026-11-19).

Three monster statuses the hero's magic lays on a foe (rules in data/wards.json
'gates'):

* ``silenced`` (Tacita's Seal, the Hush of the Feralia, the Sceptre of
  Agamemnon's blow): no voice attack (a wail, a song, a scream), no spell cast
  from range whatever its damage type (wards.is_cast), no summoning, no
  healing. A silenced summoner or healer has to
  come and fight with what it has. The mouthless (oozes, plants, constructs)
  cannot be silenced: they have no voice to take.
* ``unstrung`` (the Wand of Unstringing): no missile (a bow, a sling, a thrown
  thing), its opener from range too. A gaze or a breath is not strung. An
  archer with nothing else to use from afar has to come to the hero.
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


def heeds_assembly(m) -> bool:
    """Men and goblins: those the Sceptre of Agamemnon calls to order."""
    return _family(m) in set(rules().get('assembly_families') or ())


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
        if has(m, status):
            return int(m.status_effects[status])      # held already: not refreshed
        if has(m, 'gate_grace'):
            return 0
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


DISTANCE = ('ranged', 'breath', 'gaze', 'voice')


def _melee(atk) -> bool:
    import wards
    return wards.is_melee(atk)


def gated(m) -> bool:
    return has(m, 'silenced') or has(m, 'unstrung')


def blocks_attack(m, atk) -> str:
    """'' when ``m`` may use ``atk`` now, else the gate's line key.

    Silenced: nothing spoken (a voice) and nothing cast (a bolt, a ray, a
    curse or a prayer shot from afar, whatever its damage type: wards.is_cast).
    Unstrung: no missile (a bow, a sling, a thrown thing: wards.is_missile).
    A gaze or a breath is neither spoken nor strung."""
    if m is None or not atk:
        return ''
    import wards
    if has(m, 'silenced'):
        if _delivery(atk) == 'voice':
            return 'silenced'
        if wards.is_cast(atk):
            return 'silenced_cast'
    if has(m, 'unstrung') and wards.is_missile(atk):
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


def blow_gate(m, atk, player):
    """(atk, None) to go on with ``atk`` (or another attack it may still use),
    or (None, (0, line)) when it cannot strike this turn.

    A gated monster never ends up striking with a melee attack from range:
    beside the hero it takes any attack it may still use; at range only one
    that reaches (an unblocked breath, gaze, voice or shot), else nothing."""
    try:
        beside = bool(m._adjacent_to(player))
    except Exception:
        beside = True
    why = blocks_attack(m, atk)
    if not why:
        if gated(m) and not beside and _melee(atk):
            return None, (0, '')            # it cannot reach him from there: it must come on
        return atk, None
    import random
    left = [a for a in (getattr(m, 'attacks', None) or ()) if not blocks_attack(m, a)]
    if not beside:
        left = [a for a in left if _delivery(a) in DISTANCE and not _melee(a)]
    if left:
        return random.choice(left), None
    return None, (0, _line(why, m, atk))


def may_summon(m) -> bool:
    return not has(m, 'silenced')


def reaches_from_afar(m) -> bool:
    """It still has something it may use from a distance."""
    return any(_delivery(a) in DISTANCE and not _melee(a) and not blocks_attack(m, a)
               for a in (getattr(m, 'attacks', None) or ()))


def must_close(m) -> bool:
    """A gated monster whose own way of fighting is shut comes to the hero as
    the aggressive do: a silenced summoner or healer (it can neither call nor
    mend), and an archer, a caster or a dragon with nothing left to use from
    afar (a seal on a mage whose bolts are all spells: he walks up, he does
    not stand stunned)."""
    if not gated(m):
        return False
    pat = getattr(m, 'ai_pattern', '')
    if has(m, 'silenced') and pat in ('summoner', 'healer'):
        return True
    if pat in ('ranged', 'dragon', 'summoner', 'healer'):
        return not reaches_from_afar(m)
    return False


def close_in(m, player, dungeon, all_monsters, extra_occupied) -> bool:
    """The closing turn of a gated caster or archer: find the hero, step
    toward him, strike when beside him (as the aggressive do: a step is its
    turn, unless it covered the ground in a double move). Returns True when
    it attacks."""
    if not m._spots_player(player, dungeon, all_monsters, extra_occupied):
        return False
    if m._adjacent_to(player):
        return True
    return bool(m._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive'))


def babbled(m) -> bool:
    return has(m, 'babbled')
