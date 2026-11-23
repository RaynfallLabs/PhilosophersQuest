"""How a companion fights beside the hero, pure (data/pet_tactics.json).

Brandon, play-testing 3.6.1 (2026-11-22): "targeting seems off for the
Pet... he just seems to soak damage when I can't see an enemy... make sure
they also take defensive maneuvers and cry for help when their life is low".

A pet fights near its master. On 'return' it goes only for a foe within its
command's reach of the HERO (never of itself, so it does not chain from foe to
foe across the floor) that the hero can see, by a short walk; caught out of
his sight by a foe it cannot finish, it breaks off and comes back to him. Hurt
to its nature's share and losing (it would fall before the foe), it falls back
behind him, on the tile beside him the foes can least reach or see, and comes
back in when it can win (the foe worn down, or itself mended). Its health low
with a foe near, it cries for help: one line a bout of danger.

Each kind keeps its own nature (data: fierce, steady, timid, fearless) and its
own voice. Nothing here knows the Game: pet_system.companion_turn gathers what
the pet sees and carries the plan out; game_combat says the cry.
"""
from __future__ import annotations

import math

_DATA: dict | None = None


def rules() -> dict:
    """data/pet_tactics.json, read once ({} when it cannot be read)."""
    global _DATA
    if _DATA is None:
        import json
        from paths import data_path
        try:
            with open(data_path('data', 'pet_tactics.json'), encoding='utf-8') as f:
                _DATA = json.load(f)
        except (OSError, ValueError):
            _DATA = {}
    return _DATA


_COMMAND_DEFAULT = {'reach': 4, 'needs_sight': True, 'follow': 2, 'max_route': 8,
                    'regroup_unseen': True, 'label': ''}


def command(cmd: str) -> dict:
    """The rules of a pet's command ('return', 'stay', 'wander'); an unknown
    one reads as 'return'."""
    cmds = rules().get('commands') or {}
    got = cmds.get(str(cmd or 'return')) or cmds.get('return') or {}
    return {**_COMMAND_DEFAULT, **got}


def command_label(cmd: str) -> str:
    return str(command(cmd).get('label') or str(cmd or 'return').title())


def _species_entry(pet) -> dict:
    """Its kind's row: the species' own 'nature' / 'voice' (a quest pet's
    data file) over this file's table by species key."""
    sp = getattr(pet, 'species', None) or {}
    row = dict((rules().get('species') or {}).get(str(getattr(pet, 'species_key', '') or '')) or {})
    for k in ('nature', 'voice'):
        if isinstance(sp, dict) and sp.get(k):
            row[k] = sp[k]
    return row


def nature_name(pet) -> str:
    name = _species_entry(pet).get('nature') or rules().get('default_nature') or 'steady'
    return name if name in (rules().get('natures') or {}) else (rules().get('default_nature') or 'steady')


def nature(pet) -> dict:
    """{break_below, rally_above, margin, cry_below, card} for this pet's
    nature."""
    nat = (rules().get('natures') or {}).get(nature_name(pet)) or {}
    return {'break_below': float(nat.get('break_below', 0.4) or 0.0),
            'rally_above': float(nat.get('rally_above', 0.6) or 0.0),
            'margin': int(nat.get('margin', 1) or 0),
            'cry_below': float(nat.get('cry_below', 0.33) or 0.0),
            'card': str(nat.get('card', '') or '')}


def voice(pet) -> str:
    """Its cry ('yelps', 'squawks'...): one word for every stage or one a
    stage; the file's default when its kind has none."""
    v = _species_entry(pet).get('voice')
    if isinstance(v, (list, tuple)) and v:
        try:
            stage = int(getattr(pet, 'stage', 0) or 0)
        except (TypeError, ValueError, AttributeError, KeyError):
            stage = 0
        v = v[max(0, min(len(v) - 1, stage))]
    return str(v or (rules().get('cry') or {}).get('default_voice') or 'cries out')


def dice_mean(notation) -> float:
    """The mean of a dice notation ("2d6+3" is 10)."""
    from sketch_manifest import mean_hp
    return float(mean_hp({'hp': notation}))


def losing(hp: float, bite: float, threat: float, foe_hp: float,
           margin: int = 0, arrive: int = 0) -> bool:
    """True when the pet would fall before the foe: the bites it needs to
    finish it (`foe_hp` over `bite`) and `margin` more are more than the turns
    it can stand `threat` a turn (`arrive` turns of blows taken first, while
    it closes in). No threat, never losing."""
    if threat <= 0:
        return False
    need = math.ceil(max(1.0, float(foe_hp)) / max(1.0, float(bite)))
    stand = math.ceil(max(1.0, float(hp)) / float(threat)) - int(arrive)
    return need + int(margin) > stand


def hurt(hp: float, max_hp: float, nat: dict) -> bool:
    """At or under its nature's share: in a fight, it weighs whether to
    fight on."""
    share = float(nat.get('break_below', 0) or 0)
    return share > 0 and float(hp) <= share * max(1.0, float(max_hp))


def wary(hp: float, max_hp: float, nat: dict) -> bool:
    """Under its rally share (never under its break share): out of a fight,
    it goes back in only when it can win. The gap between the two shares
    keeps a pet that fell back from stepping in again for one point mended."""
    share = max(float(nat.get('rally_above', 0) or 0), float(nat.get('break_below', 0) or 0))
    return share > 0 and float(hp) < share * max(1.0, float(max_hp))


def choose(*, hp, max_hp, bite, nat, cmd, support=False, with_hero=True, foes=()):
    """The pet's plan for its turn: (what, foe).

    ``foes``: one dict a hostile it knows of: ``d_pet`` and ``d_hero``
    (Chebyshev steps from it and from the hero), ``seen`` (its tile in the
    hero's sight, or beside him), ``hp``, ``blow`` (what it lands on the pet
    a turn) and ``route`` (steps for the pet to stand beside it; None: no
    short way). ``with_hero``: the pet is in the hero's sight or beside him.

    'attack' foe: bite it. 'fall_back' foe: take the safest tile beside the
    hero (bite the foe only when cornered). 'regroup' foe: back toward the
    hero, out of his sight as it is (bite only when cornered). 'engage' foe:
    walk to it. 'follow': walk to the hero. 'hold': stay where it is."""
    rules_cmd = command(cmd)
    margin = int(nat.get('margin', 0) or 0)
    is_hurt = hurt(hp, max_hp, nat)
    beside = [f for f in foes if f['d_pet'] <= 1]
    if beside:
        threat = sum(float(f['blow']) for f in beside)
        # The one to bite: one it can finish now, then one at the hero's
        # side, then the weakest.
        best = min(beside, key=lambda f: (f['hp'] > bite, f['d_hero'] > 1, f['hp']))
        if is_hurt and losing(hp, bite, threat, best['hp'], margin):
            return ('fall_back', best)
        if (rules_cmd.get('regroup_unseen') and not with_hero and best['hp'] > bite):
            return ('regroup', best)
        return ('attack', best)
    if str(cmd) == 'stay':
        return ('hold', None)
    danger = int(rules().get('danger_reach', 2) or 2)
    if support and str(cmd) == 'return':
        if is_hurt and any(f['d_pet'] <= danger for f in foes):
            return ('fall_back', None)
        return ('follow', None)
    reach = int(rules_cmd.get('reach', 4) or 0)
    most = int(rules_cmd.get('max_route', 8) or 0)
    sight = bool(rules_cmd.get('needs_sight', True))
    near = [f for f in foes
            if f['d_hero'] <= reach and f.get('route') is not None and f['route'] <= most
            and (f['seen'] or f['d_hero'] <= 1 or not sight)]
    if near:
        target = min(near, key=lambda f: (f['d_hero'], f['route']))
        if (wary(hp, max_hp, nat)
                and losing(hp, bite, float(target['blow']), target['hp'], margin, arrive=1)):
            return ('fall_back', None) if is_hurt else ('follow', None)
        return ('engage', target)
    if is_hurt and any(f['d_pet'] <= danger for f in foes):
        return ('fall_back', None)
    return ('follow', None)


def fall_back_key(c: dict) -> tuple:
    """The order a fall-back tile is chosen in, best first: no foe beside
    it, fewest foes with a clear view of it (a cunning one goes for a hurt
    pet it can see), farthest from the nearest foe, fewest steps away."""
    return (int(c['beside']), int(c['seen_by']), -int(c['far']), int(c['steps']))


def pick_fall_back(candidates):
    """The best of ``candidates`` (dicts with x, y, beside, seen_by, far,
    steps), or None when there are none."""
    got = list(candidates)
    if not got:
        return None
    return min(got, key=lambda c: (fall_back_key(c), c['y'], c['x']))


def cry_step(bout: bool, calm: int, share: float, danger: bool, nat: dict):
    """One turn of a pet's cry for help: (cry now, bout, calm turns).

    It cries when its health share is at or under its nature's cry_below
    with a foe near it (``danger``) and it has not cried this bout. The bout
    ends once no foe has come near for calm_turns, or its health is back
    above cry_below + reset_gap."""
    cr = rules().get('cry') or {}
    below = float(nat.get('cry_below', 0) or 0)
    if below <= 0:
        return False, False, 0
    mended = share > below + float(cr.get('reset_gap', 0.15) or 0)
    if bout:
        if mended:
            return False, False, 0
        calm = 0 if danger else int(calm) + 1
        if calm >= int(cr.get('calm_turns', 5) or 5):
            return False, False, 0
        return False, True, calm
    if danger and share <= below:
        return True, True, 0
    return False, False, 0


def cry_line(name: str, voice_word: str, subj: str, *, seen: bool,
             place: str = '', direction: str = '') -> str:
    """The cry, as the hero hears it: "Ember yelps: he is hurt!", or unseen,
    "Ember yelps from the corridor to the north: he is hurt!"."""
    cr = rules().get('cry') or {}
    tpl = cr.get('seen' if seen or not direction else 'unseen') or '{pet} {voice}: {subj} is hurt!'
    return tpl.format(pet=name, voice=voice_word, subj=subj, place=place, dir=direction)


def place_word(in_room: bool) -> str:
    cr = rules().get('cry') or {}
    return str(cr.get('place_room' if in_room else 'place_corridor')
               or ('the dark' if in_room else 'the corridor'))
