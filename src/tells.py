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

At KNOWN the hero is also told what the creature is made of, in ONE line
that names it (`lore_line`, winning-build plan 2026-11-13 section 3.1;
Brandon 2026-11-16: one plain line, no "(double damage)"): what it is weak
to, what it resists and shrugs off, and what its nature refuses or falls to
easily. He is told that on first sight and by Observe, tell or no tell,
and never of a creature still hidden (the game names it "something").
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
          'can_phase_blink', 'stalker')


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'tells.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def _floor() -> float:
    return float(data().get('min_chance', 0.1))


def _floors(atk) -> bool:
    import knockdown
    return knockdown.floors(atk)


def abilities(m) -> list:
    """The tell keys of a creature, worst first."""
    d = data()
    have = set()
    for atk in getattr(m, 'attacks', None) or ():
        eff = atk.get('effect') if isinstance(atk, dict) else None
        if eff and float(atk.get('effect_chance', 1.0) or 0) >= _floor():
            # Stone that kills and stone that only holds are two tells.
            have.add('petrify_lethal' if eff == 'petrifying' and atk.get('lethal') else eff)
        if isinstance(atk, dict) and (atk.get('shove') or _floors(atk)):
            have.add('knocked_down')     # knockdown.py (a gore is a thrust: no fall)
    for flag in _FLAGS:
        if getattr(m, flag, None):
            have.add(flag)
    # Its pack's trick (src/packs.py, data/packs.json): the rat swarm, the
    # wolves' hamstring, the goblins' slings...
    try:
        import packs
        have.update(packs.tell_keys(m))
    except (ImportError, OSError, ValueError):
        pass
    try:
        import lore_powers              # the 2026-11-19 kinds' powers (slice M)
        have.update(lore_powers.tell_keys(m))
    except (ImportError, OSError, ValueError):
        pass
    # Its third-wave ways (AI-3): a hold, an aura, a caster's book, home
    # ground, what it carries, a coward's distance, a second shape.
    try:
        import ways_tells
        have.update(ways_tells.tell_keys(m))
    except (ImportError, OSError, ValueError):
        pass
    # What its behaviour shows (AI-1, src/kind_data.py): a breath drawn up
    # again, a healer's rest, a light it hates, a cry it raises...
    try:
        import kind_data
        have.update(kind_data.tell_keys(m))
    except (ImportError, OSError, ValueError):
        pass
    # How it thinks (AI-2, src/tactical_mind.py): its mind, the dark edge,
    # its snares, a band leader's orders.
    try:
        import tactical_mind
        have.update(tactical_mind.tell_keys(m))
    except (ImportError, OSError, ValueError):
        pass
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
    if key == 'petrify_lethal':
        key = 'petrifying'
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
    if key == 'stalker' and not getattr(m, '_revealed', False):
        # The false friend before the act drops (Old Nickel): a smile, an
        # offer to keep watch. What he is, only for a hero who knows.
        sign = e.get('sign_friend', sign)
        does = e.get('does_friend', does)
        counter = e.get('counter_friend', counter)
    if key in ('parley', 'summon_kind'):
        # A kind's own words: the Blue Men's verse is no Sphinx's riddle, and
        # what the Overseer calls falls with it.
        if key == 'parley':
            import lore_powers
            block = lore_powers.spec(m, 'parley')
        else:
            import kind_data
            block = kind_data.field(m, 'summons_fall')
        own = (block or {}).get('tell') or {}
        sign = own.get('sign', sign)
        does = own.get('does', does)
        counter = own.get('counter', counter)
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


def _or(words) -> str:
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' or ' + words[-1]


# The words of the one lore line (lore_line): the damage types as the
# weapon cards, the fight panel and the Bestiary name them (Slash, Pierce,
# Blunt, Holy...), so a hero can match a weapon to a weakness at a glance.
_LORE_WORDS = {'drain': 'drain'}


def lore_line(m) -> str:
    """ONE plain line of what a known kind is made of, naming it (Brandon
    2026-11-16: "why a whole nother message? this is clutter... all the
    'double' and 'half' damage is unnecessary"): "The skeleton: weak to
    crushing blows, holy power and silver weapons; resists cutting blows;
    can't be poisoned or put to sleep." The words are the Bestiary's (Weak
    To, Resists, Shrugs Off), and data/hints.json says what they mean. ''
    when there is nothing to say."""
    import affinity
    d = data()
    parts = []
    weak, banes, res, shrugs = [], [], [], []

    def plain(types):
        # The blows first, then the elements, in one order everywhere.
        order = {t: i for i, t in enumerate(('slash', 'pierce', 'blunt'))}
        ts = sorted(types, key=lambda t: (order.get(t, 9), types.index(t)))
        return list(dict.fromkeys(_LORE_WORDS.get(t, str(t).replace('_', ' ')) for t in ts))
    for kind, _label, types in affinity.damage_profile(m):
        if kind == affinity.WEAK:
            weak = plain(types)
        elif kind == 'banes':
            banes = list(dict.fromkeys(affinity.word_for(t) for t in types))
        elif kind == affinity.RESISTED:
            res = plain(types)
        elif kind == affinity.SHRUGS_OFF:
            shrugs = plain(types)
    if weak or banes:
        # The metals it cannot bear: one or two by name, never the whole list
        # (the Bestiary's Hurt Most By row has them all).
        if len(banes) > 2:
            lead = 'silver' if 'silver' in banes else banes[0]
            banes_word = f"{lead} weapons (or metals like it)"
        else:
            banes_word = f"{_or(banes)} weapons" if banes else ''
        parts.append('weak to ' + _and(weak + ([banes_word] if banes_word else [])))
    if res:
        parts.append('resists ' + _and(list(dict.fromkeys(res))))
    if shrugs:
        parts.append('shrugs off ' + _and(list(dict.fromkeys(shrugs))))
    sw = d.get('status_words') or {}
    immune = [sw.get(e, str(e).replace('_', ' ')) for e in (getattr(m, 'status_immune', None) or ())]
    if immune:
        parts.append("can't be " + _words(immune))
    status_weak = list(getattr(m, 'status_weak', None) or ())
    easily = [sw.get(e, str(e).replace('_', ' ')) for e in status_weak if e != 'fear_of_fire']
    if easily:
        parts.append('easily ' + _words(easily))
    if 'fear_of_fire' in status_weak:
        parts.append('flees from fire')
    if not parts:
        return ''
    return _fill(m, '{The}: ' + '; '.join(parts) + '.')


def lore_lines(m) -> list:
    """What a hero who knows the kind is told it is made of: one line
    (lore_line), or none (section 3.1: "Studied: its weaknesses,
    resistances and the counter")."""
    t = lore_line(m)
    return [t] if t else []
