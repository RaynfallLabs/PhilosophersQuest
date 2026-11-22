"""The one gate every action of the hero's passes, pure.

Until 2026-11-22 only paralysis and sleep were asked where every key
arrives. Stun, slow, ice, fear and the rest were asked inside Game._do_move,
which A, F, S, Q, Z, R, M and V never enter: a stunned or terrified hero
attacked with A every single time.

Now an action names its DOOR (data/effects.json 'doors') where it is
committed (game_effects.EffectsMixin._gate), and this module answers from
one rule per effect ('gate'). It changes nothing: the Game carries the
answer out.

Slowed is not in the gate: it shuts no door. Every action takes two turns
(Player.get_speed, effect_rules.moves_slow), which no door can slip.
"""
from __future__ import annotations

from typing import NamedTuple

import effect_rules

# What the caller must do about it.
OPEN = 'open'          # nothing: go on
LOSE = 'lose'          # the turn passes, nothing done
REFUSE = 'refuse'      # nothing done, no turn passes
STAND = 'stand'        # the action is standing up instead
THAW = 'thaw'          # the action is thawing with the lit flame instead
FALL = 'fall'          # the step is a fall
DROP = 'drop'          # the thing in hand falls at his feet
FIZZLE = 'fizzle'      # the spell fizzles: the turn, no MP

# The order effects are asked in: what stops everything, then what shuts a
# door, then the once-a-bout prices (paid only for an action that could
# otherwise have been done).
_ORDER = ('sleeping', 'paralyzed', 'knocked_down', 'frozen', 'immobilized', 'silenced',
          'hexed', 'feared', 'charmed', 'stunned', 'fumbling')


class Verdict(NamedTuple):
    what: str = OPEN
    effect: str = ''
    key: str = ''          # its line in data/effects.json
    by: str = ''           # the creature's token, for a line that names it

    @property
    def open(self) -> bool:
        return self.what == OPEN


GO = Verdict()


def doors() -> frozenset:
    return frozenset(effect_rules.data()['doors'])


def _in(rule: dict, key: str, door: str) -> bool:
    names = rule.get(key) or ()
    return '*' in names or door in names


def steady(player) -> bool:
    """In Guard he neither falls nor drops."""
    import stance
    return stance.of(player) == 'guard'


def verdict(player, door: str, *, target=None, worn: bool = False, toward: bool = False,
            cornered: bool = False, source_here: bool = False, flame: bool = False) -> Verdict:
    """May the hero do this now?

    ``target``       the creature the action is aimed at, if any.
    ``worn``         doing it would take off something he is wearing.
    ``toward``       this step brings him nearer what frightens him.
    ``cornered``     he has no step away from it.
    ``source_here``  the charmer is here and in sight.
    ``flame``        a lit flame is in his hand.
    """
    if door not in effect_rules.data()['doors']:
        raise ValueError(f'no such door: {door!r}')
    rules = effect_rules.data()['gate']
    for effect in _ORDER:
        if not effect_rules.running(player, effect):
            continue
        got = _one(player, effect, rules.get(effect) or {}, door, target, worn, toward,
                   cornered, source_here, flame)
        if not got.open:
            return got
    return GO


def _one(player, effect, rule, door, target, worn, toward, cornered, source_here, flame) -> Verdict:
    if _in(rule, 'stand', door):
        return Verdict(STAND, effect, 'stand')
    lose, refuse = _in(rule, 'lose', door), _in(rule, 'refuse', door)
    if lose or refuse:
        if rule.get('thaw') and flame:
            return Verdict(THAW, effect, 'thaw')
        key = effect
        if effect == 'frozen':
            key = 'frozen_feet' if door in ('step', 'stairs', 'climb', 'ride') else 'frozen_hands'
        return Verdict(LOSE if lose else REFUSE, effect, key)
    if worn and _in(rule, 'refuse_worn', door):
        return Verdict(REFUSE, effect, effect)

    by = ''
    if rule.get('aimed') or rule.get('no_approach') or rule.get('refuse_held'):
        by = str(effect_rules.bout(player, effect).get('by') or '')
        if not (cornered and rule.get('cornered_may_fight')):
            if door == 'step' and toward and rule.get('no_approach'):
                return Verdict(REFUSE, effect, 'feared_step', by)
            # A bout laid by no one in particular (a bad meal, an older
            # save) holds against whatever the action is aimed at.
            if (target is not None and _in(rule, 'aimed', door)
                    and (not by or effect_rules.is_source(target, by))):
                return Verdict(REFUSE, effect, f'{effect}_strike', by)
        if source_here and _in(rule, 'refuse_held', door):
            return Verdict(REFUSE, effect, f'{effect}_{door}', by)

    for key, flag, what in (('first_fall', 'fell', FALL), ('first_drop', 'dropped', DROP),
                            ('first_fizzle', 'fizzled', FIZZLE)):
        if not _in(rule, key, door):
            continue
        b = effect_rules.bout(player, effect)
        if b.get('self') or b.get(flag) or steady(player):
            return GO
        if what == FALL and player.has_effect('levitating'):
            return GO                        # off the ground, as against a trample (knockdown.py)
        return Verdict(what, effect, what)
    return GO


def paid(player, v: Verdict) -> None:
    """A once-a-bout price was paid: it is not asked again this bout."""
    flag = {FALL: 'fell', DROP: 'dropped', FIZZLE: 'fizzled'}.get(v.what)
    if flag:
        effect_rules.bout(player, v.effect)[flag] = True
