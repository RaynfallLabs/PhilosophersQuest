"""The effects pass in the simulator (Brandon, 2026-11-22).

The rules are the game's own (src/action_gate.py, src/effect_rules.py,
src/quiz_sight.py). What is modelled here is only what the simulator's
fight has no geometry or menu for:

* the kid knows the trick: stunned, he stands and fights rather than step
  or fiddle; he fumbles only when he must drink or run;
* what he may not strike (his charmer, what frightens him) he leaves for
  the others, or waits; pinned, he is cornered and fights;
* blinded, each question costs DARK_SECONDS of moving the light;
* stone that kills is stopped as a kid who listens would: the Oil of Rue
  every stall of floors 19-80 sells (one a band for a kid who uses his
  potions and prays), a cure in his kit, or a prayer.

What Forget takes (a known kind, a page) has no price in the simulator's
fights, and is not priced.
"""
from __future__ import annotations

import action_gate
import effect_rules
import quiz_sight

DARK_SECONDS = 0.8             # a timed question: two presses of the arrows
CURES = ('stoneproof', 'cure_all')


def quiz_wait(player) -> float:
    """The seconds each maths question costs him beyond the answer."""
    wait = quiz_sight.wait_for(player, True)
    if quiz_sight.sight_for(player)['dark']:
        wait += DARK_SECONDS
    return wait


def stand(run) -> bool:
    """Knocked down, his action is standing up. True when it was spent."""
    p = run.p
    if not p.has_effect('knocked_down'):
        return False
    from status_effects import FOOTING_TURNS
    p.status_effects.pop('knocked_down', None)
    p.status_effects['footing'] = FOOTING_TURNS
    run.fs['fx_stood'] = run.fs.get('fx_stood', 0) + 1
    return True


def barred(run, door: str, target=None) -> bool:
    """The gate's answer for this action. True: it cannot be done now (a
    fall, a drop or a fizzle has spent it)."""
    p = run.p
    if not p.status_effects:
        return False
    cornered = any(p.has_effect(e) for e in ('held', 'immobilized', 'frozen', 'in_pit'))
    v = action_gate.verdict(p, door, target=target, cornered=cornered)
    if v.open:
        return False
    if v.what in (action_gate.DROP, action_gate.FIZZLE, action_gate.FALL):
        action_gate.paid(p, v)
        if v.what == action_gate.FALL:
            p.status_effects['knocked_down'] = 1
    key = f'fx_{v.effect}_{v.what}'
    run.fs[key] = run.fs.get(key, 0) + 1
    return True


def strikeable(run, foes: list) -> list:
    """The foes he may raise a hand against."""
    p = run.p
    if not (p.has_effect('charmed') or p.has_effect('feared')):
        return foes
    cornered = any(p.has_effect(e) for e in ('held', 'immobilized', 'frozen', 'in_pit'))
    return [m for m in foes
            if action_gate.verdict(p, 'strike', target=m, cornered=cornered).open]


def stop_stone(run) -> bool:
    """A lethal count is stopped with what he has. True when that was his
    action."""
    p = run.p
    if not p.has_effect('petrifying') or not effect_rules.is_lethal(p):
        return False
    kit = run._mm_kit()['potion']
    pot = next((x for x in kit if x.effect in CURES), None)
    if pot is not None:
        kit.remove(pot)
        how = 'potion'
    else:
        prof = run.prof
        band = (int(getattr(run, 'floor', 1) or 1) + 1) // 20
        used = run.__dict__.setdefault('_rue_used', set())
        if (prof.get('prays') and float(prof.get('potion_at', 0) or 0) > 0
                and 1 <= band <= 4 and band not in used):
            used.add(band)                       # bought at that band's camp
            how = 'rue'
        elif prof.get('prays') and getattr(p, 'prayer_cooldown', 0) <= 0:
            run.pray()
            run.fs['fx_stone_prayed'] = run.fs.get('fx_stone_prayed', 0) + 1
            # The mercy lifts stone from a fourth link (game_divine).
            if run.quiz.escalator_chain(5) >= 4:
                p.status_effects.pop('petrifying', None)
            return True
        else:
            return False
    p.status_effects.pop('petrifying', None)
    if how == 'rue' or (pot is not None and pot.effect == 'stoneproof'):
        p.add_effect('petrify_immune', 30)
    run.fs['fx_stone_cured'] = run.fs.get('fx_stone_cured', 0) + 1
    return True


def after_world(run, active: list) -> None:
    """A hold ends with the creature that laid it; a memory eaten is noted."""
    p = run.p
    for tok in p.__dict__.pop('_pending_forget', None) or ():
        if effect_rules.running(p, 'forgetting'):
            run.fs['fx_forgot'] = run.fs.get('fx_forgot', 0) + 1
    for effect in ('feared', 'charmed'):
        if not effect_rules.running(p, effect):
            continue
        by = effect_rules.bout(p, effect).get('by')
        if by and effect_rules.source_in(active, by) is None:
            from status_effects import end_bout
            end_bout(p, effect)


def fight_over(player) -> None:
    """Nothing that waits on the hero's action outlasts the fight."""
    player.status_effects.pop('knocked_down', None)
