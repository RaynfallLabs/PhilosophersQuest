"""The debuffs' rules and their bouts, pure (data/effects.json).

Brandon, 2026-11-22, on the monster-effects audit: "All as recommended".
Confusion is the model: an effect shows, knowledge or skill beats it, the
right defence stops it, and no bout locks the hero.

A BOUT is one run of a status on the hero, from the turn it takes hold to
the turn it ends. It remembers what the rules need and the count of turns
does not say:

    by       the token of the creature that laid it (``token``)
    by_name  its name then, and by_the, as a line names it
    self     the hero brought it on himself (a failed identification)
    lethal   a petrifying that ends in stone
    fell, dropped, fizzled
             the once-a-bout prices already paid
    worn     pieces of gear this bout has worn

Bouts live in ``player._bouts`` (plain dicts, saved with the hero). An older
save has none: every reader treats a missing bout as an ordinary one laid by
no one in particular.
"""
from __future__ import annotations

import json
import uuid

_DATA: dict | None = None

# The statuses whose bout has something to remember.
BOUTED = frozenset({'stunned', 'fumbling', 'feared', 'charmed', 'petrifying', 'forgetting',
                    'burning', 'corroding'})


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'effects.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def gate_rules() -> dict:
    return {k: v for k, v in data()['gate'].items() if not k.startswith('_')}


def statuses() -> dict:
    return data()['statuses']


def line(key: str, **words) -> str:
    """One of data/effects.json 'lines', its {words} filled in."""
    text = str(data()['lines'][key])
    for k, v in words.items():
        text = text.replace('{' + k + '}', str(v))
    return text[:1].upper() + text[1:]


# ---------------------------------------------------------------------------
# Who laid it
# ---------------------------------------------------------------------------

def token(monster) -> str:
    """A name for this one creature that survives saving and loading. (uuid
    takes the system's randomness: the game's dice never move.)"""
    d = monster.__dict__
    if not d.get('_effect_token'):
        d['_effect_token'] = uuid.uuid4().hex
    return d['_effect_token']


def is_source(monster, tok) -> bool:
    return bool(tok) and monster is not None and getattr(monster, '__dict__', {}).get('_effect_token') == tok


def source_in(monsters, tok):
    """The living creature with that token among ``monsters``, or None."""
    if not tok:
        return None
    return next((m for m in monsters or ()
                 if getattr(m, 'alive', False) and is_source(m, tok)), None)


# ---------------------------------------------------------------------------
# A monster saved before the pass
# ---------------------------------------------------------------------------

EFFECTS_PASS = 2          # 2: the venom (2026-11-22, venom.py)
_ATTACK_FIELDS = ('effect', 'effect_chance', 'effect_duration', 'lethal', 'venom')


def refresh_monster(monster) -> bool:
    """A monster from a save older than the effects pass (no
    ``_effects_pass``: Monster.__init__ sets one) lays what its kind's
    attacks lay now, by the attack's name. True when it was refreshed."""
    d = getattr(monster, '__dict__', None)
    if d is None or int(d.get('_effects_pass', 0) or 0) >= EFFECTS_PASS:
        return False
    d['_effects_pass'] = EFFECTS_PASS
    atks = d.get('attacks')
    import kind_data
    defn = kind_data.defs().get(str(d.get('kind', '') or ''))
    if not isinstance(defn, dict) or not isinstance(atks, list):
        return False
    now = {a.get('name'): a for a in defn.get('attacks') or () if isinstance(a, dict)}
    out = []
    for atk in atks:
        new = now.get(atk.get('name')) if isinstance(atk, dict) else None
        if new is not None:
            atk = {k: v for k, v in atk.items() if k not in _ATTACK_FIELDS}
            atk.update({k: new[k] for k in _ATTACK_FIELDS if k in new})
        out.append(atk)
    d['attacks'] = out
    return True


# ---------------------------------------------------------------------------
# Bouts
# ---------------------------------------------------------------------------

def _bouts(player) -> dict:
    d = player.__dict__.get('_bouts')
    if not isinstance(d, dict):
        d = player.__dict__['_bouts'] = {}
    return d


def opened(player, effect: str) -> None:
    """``effect`` has just taken hold where there was none: a new bout."""
    if effect in BOUTED:
        _bouts(player)[effect] = {}


def ended(player, effect: str) -> None:
    d = getattr(player, '__dict__', {}).get('_bouts')
    if isinstance(d, dict):
        d.pop(effect, None)


def running(player, effect: str) -> bool:
    return int((getattr(player, 'status_effects', None) or {}).get(effect, 0) or 0) != 0


def bout(player, effect: str) -> dict:
    """The running bout of ``effect``; an empty dict (never kept) when it is
    not on him. A status on him with no bout (an older save) starts one."""
    if not running(player, effect):
        return {}
    return _bouts(player).setdefault(effect, {})


def laid_by(player, effect: str, monster=None, *, lethal: bool = False) -> None:
    """A creature has just begun this bout: whose it is, and whether it can
    end in stone. Only the caller that began the bout calls this."""
    if effect not in BOUTED or not running(player, effect):
        return
    b = bout(player, effect)
    if monster is not None:
        b['by'] = token(monster)
        b['by_name'] = str(getattr(monster, 'name', '') or '')
        from monster import the_name
        b['by_the'] = the_name(monster, lower=True)
    if effect == 'petrifying' and lethal:
        b['lethal'] = True


def self_inflicted(player, effect: str) -> None:
    if effect in BOUTED and running(player, effect):
        bout(player, effect)['self'] = True


def spares(player, monster, melee: bool = False) -> bool:
    """He will not harm it, aimed or not: his charmer, by any means; with
    ``melee`` also what frightens him. Every list of whom an action catches
    asks this (holds.strikable, the two reach checks of game_magic)."""
    for effect in ('charmed', 'feared') if melee else ('charmed',):
        if running(player, effect) and is_source(monster, bout(player, effect).get('by')):
            return True
    return False


# ---------------------------------------------------------------------------
# Petrifying, and what makes every action take two turns
# ---------------------------------------------------------------------------

def is_lethal(player) -> bool:
    return bool(bout(player, 'petrifying').get('lethal'))


def stone_rules(player) -> dict:
    return data()['petrify']['lethal' if is_lethal(player) else 'lesser']


def stone_stage(player, left: int | None = None) -> str:
    """'' (none), 'stiff', 'slow' or 'rigid'."""
    if not running(player, 'petrifying'):
        return ''
    if left is None:
        left = int(player.status_effects.get('petrifying', 0) or 0)
    r = stone_rules(player)
    if 0 < left <= int(r['rigid_at']):
        return 'rigid'
    if 0 < left <= int(r['slow_at']):
        return 'slow'
    return 'stiff'


def moves_slow(player) -> bool:
    """Every action of his takes two of the world's turns: Slowed, or the
    stone far enough along."""
    return running(player, 'slowed') or stone_stage(player) in ('slow', 'rigid')


def may_wear(player, effect: str) -> bool:
    """A bout of burning or corroding may still wear a piece of gear."""
    return int(bout(player, effect).get('worn', 0)) < int(statuses().get('wear_per_bout', 1))


def wore(player, effect: str) -> None:
    b = bout(player, effect)
    b['worn'] = int(b.get('worn', 0)) + 1
