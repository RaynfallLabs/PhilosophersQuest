"""Tells: a dangerous creature shows what it can do (Dungeon Alive slice 5;
known and unknown, 2026-11-12).

Brandon: "players need to pay attention to lore, weaknesses, abilities (stay
away from things that can confuse! use ranged!)". Then, from his first
play: the notes "give away what a monster is AND how to approach it, without
you having seen it or identified it." So each tell has three parts
(data/tells.json):

  sign     what the eye sees: said of a creature the hero does not know;
  does     what it means, what the creature can do to him;
  counter  what to do about it.

How much is said follows what the hero knows of the kind
(family_lore.knowledge): UNKNOWN hears the sign; KIN (its family at
Recognise or Forewarned, the kind itself never studied) hears the sign, its
family and what it does; KNOWN (studied, its page opened, or its family at
Lore) hears all three, and so learns which sign means what.

A counter is honest about reach: an effect the creature can put on the hero
from across a room gets the far counter, never "fight it from a distance".

The first time in a run the hero sees a kind, the Chronicler says its worst
tell (Game._maybe_tell); Observe (O) says them all. Every tell comes from
what the creature really does: an attack effect in data/monsters.json, or
one of its flags. Pure module.

At KNOWN the hero is also told what the creature is made of (`lore_lines`,
winning-build plan 2026-11-13 section 3.1): what hurts it most, what it
resists and shrugs off, and what its nature refuses or falls to easily. He
is told that on first sight and by Observe, tell or no tell.
"""
from __future__ import annotations

import json

from family_lore import KNOWN, UNKNOWN

_DATA: dict | None = None

# The ways a creature attacks from afar (Monster.attack picks a
# ranged attack at range for these, and a rooted one shoots only what is
# flagged `ranged`). Everything else strikes only when it is beside him.
_FAR_AIS = ('ranged', 'dragon', 'healer', 'summoner', 'sessile')
_FLAGS = ('gaze_paralyze', 'splits', 'revive_once_on_death', 'drain_heals_self',
          'regeneration', 'summon_kind', 'pull_chance', 'sp_drain', 'can_charge',
          'can_phase_blink')


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'tells.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def _floor() -> float:
    return float(data().get('min_chance', 0.1))


def abilities(m) -> list:
    """The tell keys of a creature, worst first."""
    d = data()
    have = set()
    for atk in getattr(m, 'attacks', None) or ():
        eff = atk.get('effect') if isinstance(atk, dict) else None
        if eff and float(atk.get('effect_chance', 1.0) or 0) >= _floor():
            have.add(eff)
    for flag in _FLAGS:
        if getattr(m, flag, None):
            have.add(flag)
    return [k for k in d['order'] if k in have and k in d['effects']]


def _reaches_far(m, atk: dict) -> bool:
    """Can the creature use this attack on the hero from across a room?"""
    ai = getattr(m, 'ai_pattern', '') or ''
    if ai not in _FAR_AIS:
        return False
    if atk.get('ranged'):
        return True
    if ai == 'sessile':
        return False
    from monster import _RANGED_WORDS
    name = str(atk.get('name', '')).lower()
    return any(w in name for w in _RANGED_WORDS)


def reach(m, key: str) -> str:
    """'far' when the creature can do this to the hero from across a room
    (a gaze, or an attack it uses at range), else 'close'."""
    if key == 'gaze_paralyze':
        return 'far'
    for atk in getattr(m, 'attacks', None) or ():
        if (isinstance(atk, dict) and atk.get('effect') == key
                and float(atk.get('effect_chance', 1.0) or 0) >= _floor()
                and _reaches_far(m, atk)):
            return 'far'
    return 'close'


def _fill(m, text: str) -> str:
    """The creature's name and pronouns put in (monster.fill), the first
    letter a capital."""
    from monster import fill
    t = fill(m, text or '')
    return t[:1].upper() + t[1:]


def _words(items) -> str:
    items = list(dict.fromkeys(i for i in items if i))
    if not items:
        return ''
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' or ' + items[-1]


def parts(m, key: str) -> tuple:
    """(sign, does, counter) of one tell, filled in for this creature."""
    d = data()
    e = d['effects'][key]
    sign, does, counter = e.get('sign', ''), e.get('does', ''), e.get('counter', '')
    if key == 'splits':
        spec = getattr(m, 'splits', None)
        by = spec.get('by', 'weak_blow') if isinstance(spec, dict) else 'weak_blow'
        if by == 'weak_blow' or not isinstance(by, (list, tuple)):
            does, counter = e.get('does_weak', does), e.get('counter_weak', counter)
        else:
            from affinity import word_for
            does = does.replace('{split_by}', _words(word_for(b) for b in by))
    elif key not in _FLAGS and reach(m, key) == 'far':
        counter = e['counter_far'] if 'counter_far' in e else d.get('far_counter', '')
    return _fill(m, sign), _fill(m, does), _fill(m, counter)


def line(m, key: str, level: int = KNOWN, kin: str = '') -> str:
    """One tell, told as far as the hero knows the kind. `kin` names its
    family in the KIN line ("It is one of the restless dead."); Observe,
    which names the family itself, leaves it out."""
    sign, does, counter = parts(m, key)
    if level <= UNKNOWN:
        return sign
    if level < KNOWN:
        lead = _fill(m, data().get('kin_lead', '').replace('{kin}', kin)) if kin else ''
        return ' '.join(p for p in (sign, lead, does) if p)
    return ' '.join(p for p in (sign, does, counter) if p)


def lines(m, level: int = KNOWN, limit: int | None = None) -> list:
    """Its tells, worst first, at most `limit` (max_lines by default)."""
    keys = abilities(m)[:limit or int(data().get('max_lines', 2))]
    return [line(m, k, level) for k in keys]


def _and(words) -> str:
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' and ' + words[-1]


def _profile(m) -> dict:
    """{kind: (size word, [words])} from affinity.damage_profile, the one
    reading the blow follows: only what the hero can land, each type where
    the blow puts it, with how much it changes a blow."""
    import affinity
    out = {}
    for kind, _label, types in affinity.damage_profile(m):
        step = {affinity.WEAK: affinity.weak_step(), 'banes': affinity.weak_step(),
                affinity.RESISTED: affinity.resisted_step(),
                affinity.SHRUGS_OFF: affinity.shrugs_step()}[kind]
        words = list(dict.fromkeys(affinity.word_for(t) for t in types if t))
        out[kind] = (affinity._size_word(step).lower(), words)
    return out


def _or(words) -> str:
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' or ' + words[-1]


def weak_line(m) -> str:
    """"Fire and holy power hurt it most (double damage). So does a weapon
    of silver.": its weaknesses and the materials it cannot bear, for a kind
    the hero knows. Empty when it has neither."""
    d = data()
    prof = _profile(m)
    out = []
    if 'weak' in prof:
        size, words = prof['weak']
        out.append(d['weak_one' if len(words) == 1 else 'weak_many']
                   .replace('{words}', _and(words)).replace('{size}', size))
    if 'banes' in prof:
        size, words = prof['banes']
        key = 'bane_tail' if out else 'bane_only'
        out.append(d[key].replace('{words}', _or(words)).replace('{size}', size))
    return _fill(m, ' '.join(out)) if out else ''


def hard_line(m) -> str:
    """"A cutting blow and a point do little to it (half damage); fire
    hardly touches it (quarter damage).": what it resists and what it shrugs
    off, for a kind the hero knows. Empty when it has neither."""
    d = data()
    prof = _profile(m)
    parts = []
    for kind, one, many in (('resisted', 'resist_one', 'resist_many'),
                            ('shrugs_off', 'shrugs_one', 'shrugs_many')):
        if kind in prof:
            size, words = prof[kind]
            parts.append(d[one if len(words) == 1 else many]
                         .replace('{words}', _and(words)).replace('{size}', size))
    if not parts:
        return ''
    return _fill(m, '; '.join(parts) + '.')


def status_lore_line(m) -> str:
    """"It cannot be put to sleep, poisoned or charmed. Fire puts it to
    flight.": what its nature refuses and what it falls to easily, for a
    kind the hero knows. Empty when it has neither."""
    d = data()
    words = d.get('status_words') or {}
    out = []
    immune = [words.get(e, str(e).replace('_', ' ')) for e in (getattr(m, 'status_immune', None) or ())]
    if immune:
        out.append(d['immune'].replace('{effects}', _words(immune)))
    weak = list(getattr(m, 'status_weak', None) or ())
    easily = [words.get(e, str(e).replace('_', ' ')) for e in weak if e != 'fear_of_fire']
    if easily:
        out.append(d['easily'].replace('{effects}', _words(easily)))
    if 'fear_of_fire' in weak:
        out.append(d['fire_flight'])
    return _fill(m, ' '.join(out)) if out else ''


def known_lead(m) -> str:
    """"You know what the skeleton is made of.": said before its lore lines
    on first sight of a known kind that has no tell, so the "it" (or "he",
    "she") in them has a creature to stand for."""
    return _fill(m, data().get('known_lead', 'You know what {the} is made of.'))


def lore_lines(m) -> list:
    """What a hero who knows the kind is told it is made of: its weakness
    line, its resistance line and its status line, each only when it has
    something to say (section 3.1: "Studied: its weaknesses, resistances
    and the counter")."""
    return [t for t in (weak_line(m), hard_line(m), status_lore_line(m)) if t]
