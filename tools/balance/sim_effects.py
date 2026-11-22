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
  every stall of floors 19-99 sells (one a band for a kid who uses his
  potions and prays; its price is not charged, which flatters him a
  little), a cure in his kit, or a prayer.

What Forget takes (a known kind, a page) has no price in the simulator's
fights, and is not priced.
"""
from __future__ import annotations

import action_gate
import effect_rules
import quiz_sight

DARK_SECONDS = 0.8             # a timed question: two presses of the arrows
CURES = ('stoneproof', 'cure_all')
# Poison (src/venom.py, 2026-11-22): a careful kid drinks his cure when the
# venom would still take this share of the HP he has, or would kill him.
VENOM_CURES = ('cure_poison', 'cure_all')
VENOM_AT = 0.25
# He keeps this many cures in his pack, bought where every stall sells one.
VENOM_CARRY = 2


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
    p.status_effects['footing'] = FOOTING_TURNS + 1
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
            if getattr(run, '_prayed_chain', 0) >= 4:
                p.status_effects.pop('petrifying', None)
            return True
        else:
            return False
    p.status_effects.pop('petrifying', None)
    if how == 'rue' or (pot is not None and pot.effect == 'stoneproof'):
        p.add_effect('petrify_immune', 30)
    run.fs['fx_stone_cured'] = run.fs.get('fx_stone_cured', 0) + 1
    return True


def stop_venom(run) -> bool:
    """A venom worth curing is cured with what he carries (the kit's cure
    poison or cure all). True when that was his action."""
    p = run.p
    if not p.has_effect('poisoned'):
        return False
    import venom
    n = venom.to_come(p)
    if n <= 0 or (n < VENOM_AT * max(1, p.hp) and not venom.deadly(p)):
        return False
    kit = run._mm_kit()['potion']
    pot = next((x for x in kit if getattr(x, 'effect', '') in VENOM_CURES), None)
    if pot is None:
        return False
    if barred(run, 'drink'):
        return True
    kit.remove(pot)
    import food_system
    food_system.drink_potion(p, pot)
    run.fs['fx_venom_cured'] = run.fs.get('fx_venom_cured', 0) + 1
    return True


def buy_venom_cure(run, floor: int, defn: dict, reserve: float) -> None:
    """At a stall that keeps the cure (data/traders.json always_stocked, or
    the apothecary's sure line), a kid who keeps potions buys up to
    VENOM_CARRY."""
    if not run._mm('mm_potions'):
        return
    import traders
    import economy
    from items import make_item_by_id
    sure = any(x.get('id') == 'potion_of_cure_poison'
               and int(x.get('floors', (1, 100))[0]) <= floor <= int(x.get('floors', (1, 100))[1])
               for x in traders.data().get('always_stocked') or ())
    sure = sure or any(x.get('id') == 'potion_of_cure_poison' for x in defn.get('stock') or ())
    if not sure:
        return
    kit = run._mm_kit()['potion']
    pot = make_item_by_id('potion', 'potion_of_cure_poison')
    if pot is None:
        return
    price = economy.stock_price(pot, floor, float(defn.get('markup', 1.0) or 1.0))
    while (sum(1 for x in kit if getattr(x, 'effect', '') == 'cure_poison') < VENOM_CARRY
           and len(kit) < 8 and run._pay(price, reserve)):
        kit.append(pot)
        run.fs['venom_cures_bought'] = run.fs.get('venom_cures_bought', 0) + 1


def wants_guard(run, group) -> bool:
    """The careful kid (tactics=1) fights in Guard a creature whose tell he
    knows says it floors or stuns him (the help and the tell: "Meet him in
    Guard"). Guard costs a third of his blows' weight (stance.py)."""
    if not run.knobs.get('tactics'):
        return False
    import tells
    for m in group:
        if not run._knows(getattr(m, 'kind', '')):
            continue
        have = set(tells.abilities(m))
        if have & {'knocked_down', 'stunned'}:
            run.fs['fx_guard_up'] = run.fs.get('fx_guard_up', 0) + 1
            return True
    return False


def note_stone(run, group) -> None:
    """He has met a creature whose stone kills (its tell, once seen)."""
    import tells
    if any('petrify_lethal' in tells.abilities(m) for m in group):
        run.__dict__['_stone_seen'] = True


RUE_CARRY = 2


def buy_rue(run, floor: int, defn: dict, reserve: float) -> None:
    """Once he has met a stone that kills, a kid who keeps potions buys Oil
    of Rue where a stall keeps it (data/traders.json always_stocked), up to
    RUE_CARRY in his pack."""
    if not run.__dict__.get('_stone_seen') or not run._mm('mm_potions'):
        return
    import traders
    import economy
    from items import make_item_by_id
    if not any(x.get('id') == 'oil_of_rue'
               and int(x.get('floors', (1, 100))[0]) <= floor <= int(x.get('floors', (1, 100))[1])
               for x in traders.data().get('always_stocked') or ()):
        return
    kit = run._mm_kit()['potion']
    oil = make_item_by_id('potion', 'oil_of_rue')
    if oil is None:
        return
    price = economy.stock_price(oil, floor, float(defn.get('markup', 1.0) or 1.0))
    while (sum(1 for x in kit if getattr(x, 'effect', '') == 'stoneproof') < RUE_CARRY
           and len(kit) < 8 and run._pay(price, reserve)):
        kit.append(oil)
        run.fs['rue_bought'] = run.fs.get('rue_bought', 0) + 1


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
