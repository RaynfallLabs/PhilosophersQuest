"""The simulated pet as a body that can be fed and can die (2026-11-21, part
1's ruling R4: pets grow by feeding). Measurement only: every default is the
simulator as it was (a pet of the floor's level that never dies).

  pt_hp     1 = it has the game's health (data/pet_growth.json at its level; the
            Mooble's share) and takes the game's swipes
            (game_combat._monster_swipes): a whole attack from the foe it bit in
            the last two turns, half the first attack's dice from one beside the
            hero. It mends 1% every third turn (pet_system.tick_regen). Killed,
            it is gone, its feeding and a quest pet's line with it.
  pt_care   with pt_hp, 1 = a careful owner's care, all of it the game's own
            (game_menus: Recall, Feed): hurt to pt_recall of its health, it is
            recalled to its sphere for the rest of the fight (his action; none
            at a fight's start); between fights it is out to mend, and fed
            what he would leave behind (parts past the pantry's room, food
            past a belly that heals him nothing: a quarter of its health and
            20 to 80 experience each), and only when he is well himself.
  pt_recall the share of its health at or under which he recalls it.
  pt_back   floors until he has another, at level 1, which then levels by the
            game's own experience (a point every third turn, its kills).
  pt_hp_x   x its health (a stand-in for writing the table again).
  pt_feed   how often a beastmaster gives the floor's stat dish to the pet: one
            cooking question, the parts go, and the hero takes no lesson that
            floor. Up to food's own cap.
  pt_lv     levels a dish fed is worth (to the table's 100).
  pt_per    share of health a dish fed adds.
  pt_full   the bite of a pet fed to the cap, as a share of the careful blow at
            its level; part way there for part of the dishes. Unfed, the table's.

mg_pet_anchor (sim_magic) re-sizes the whole bite table against the careful
blow, read at the pet's own level here.

Stand-ins: the first pet's level is the floor it has been raised to (as the
simulator always had it); a foe other than the one it bit is beside it half
the time. Not modelled: specials, line weaknesses, Shep's rescue,
potions poured over it, a better sphere's hatch level.
"""
from __future__ import annotations

import random

KNOBS = {
    'pt_hp': 0,
    'pt_care': 1,
    'pt_recall': 0.5,
    'pt_back': 3,
    'pt_hp_x': 1.0,
    'pt_feed': 0.0,
    'pt_lv': 0.0,
    'pt_per': 0.0,
    'pt_full': 0.0,
}
BESIDE_PET = 0.5
_BLOW = {}
_RATIO = {}


def k(run, name):
    return run.knobs.get(name, KNOBS[name])


def on(run) -> bool:
    return bool(run.prof.get('pet')) and (
        bool(k(run, 'pt_hp'))
        or (bool(run.prof.get('beast')) and float(k(run, 'pt_feed') or 0) > 0))


def state(run) -> dict:
    s = run.__dict__.get('_pet_st')
    if s is None:
        s = run._pet_st = dict(gone=None, first=True, lvl=1, xp=0.0, fed=0, hurt=0.0,
                               turn=run.turn, aggro=None, stowed=False)
    return s


def _count(run, key, n=1) -> None:
    if run.fs is not None:
        run.fs[key] = run.fs.get(key, 0) + n


def alive(run) -> bool:
    return not on(run) or state(run)['gone'] is None


def here(run) -> bool:
    """Beside him: alive and out of its sphere."""
    return alive(run) and (not on(run) or not state(run)['stowed'])


def cared(run) -> bool:
    return bool(k(run, 'pt_hp') and k(run, 'pt_care') and run.prof.get('pet')
                and run.floor >= 3)


def quest_line(run) -> bool:
    """The pet won by a quest is still the one beside him."""
    if not on(run):
        return True
    s = state(run)
    return s['first'] and s['gone'] is None


def food_cap() -> int:
    import kitchen
    return int(((kitchen.rules().get('stat') or {}).get('cap_by_tier') or [28])[-1])


def level(run) -> int:
    s = state(run)
    own = run.floor if s['first'] else s['lvl']
    return max(1, min(100, int(own + s['fed'] * float(k(run, 'pt_lv') or 0))))


def max_health(run) -> int:
    import pet_system
    s = state(run)
    mult = float(k(run, 'pt_hp_x')) * (1.0 + s['fed'] * float(k(run, 'pt_per') or 0))
    if run._quest_pet() == 'mooble':
        mult *= float((pet_system._SPECIES.get('mooble') or {}).get('health_mult', 0.6) or 0.6)
    return max(1, int(round(pet_system.growth('health', level(run)) * mult)))


def bite(run) -> float:
    import pet_system
    import sim_magic
    if not on(run):
        return pet_system.growth('bite', run.floor) * sim_magic.pet_bite_mult(run)
    lv = level(run)
    out = float(pet_system.growth('bite', lv))
    anchor = float(run.knobs.get('mg_pet_anchor', 0) or 0)
    if anchor > 0:
        if lv not in _RATIO:
            _RATIO[lv] = sim_magic.ratio_at(lv)
        out *= anchor * _RATIO[lv]
    full = float(k(run, 'pt_full') or 0)
    fed = state(run)['fed']
    if full > 0 and fed:
        if lv not in _BLOW:
            _BLOW[lv] = sim_magic._careful_blow(lv)
        out += max(0.0, full * _BLOW[lv] - out) * min(1.0, fed / food_cap())
    return out


def _learn(s: dict, xp: float) -> None:
    import pet_system
    if s['first']:
        return
    s['xp'] += xp
    while s['lvl'] < 100 and s['xp'] >= s['lvl'] * pet_system._XP_PER_LEVEL:
        s['xp'] -= s['lvl'] * pet_system._XP_PER_LEVEL
        s['lvl'] += 1


def catch_up(run) -> None:
    """The turns gone by since it was last looked at: it mends and learns."""
    if not on(run):
        return
    import floor_curve
    s = state(run)
    thirds = max(0, run.turn - s['turn']) // 3
    s['turn'] += thirds * 3
    if s['gone'] is not None or s['stowed'] or not thirds:
        return
    _learn(s, thirds)
    if s['hurt'] > 0:
        top = max_health(run)
        s['hurt'] = max(0.0, s['hurt'] - thirds * max(1, int(top * floor_curve.PET_REGEN_SHARE)))


def floor_start(run) -> None:
    if not on(run):
        return
    catch_up(run)
    s = state(run)
    if s['gone'] is not None and run.floor >= s['gone'] + int(k(run, 'pt_back')):
        s.update(gone=None, first=False, lvl=1, xp=0.0, fed=0, hurt=0.0, aggro=None,
                 stowed=False, turn=run.turn)
        _count(run, 'pt_back_n')


def badly_hurt(run) -> bool:
    top = max_health(run)
    return top - state(run)['hurt'] <= float(k(run, 'pt_recall')) * top


def fight_start(run) -> None:
    catch_up(run)
    if cared(run) and alive(run) and badly_hurt(run):
        state(run)['stowed'] = True             # sent in before the fight joins
        _count(run, 'pt_kept_in')


def recall(run) -> bool:
    """Back into its sphere, his action. True when it went."""
    if not cared(run) or not here(run) or not badly_hurt(run):
        return False
    state(run).update(stowed=True, aggro=None)
    _count(run, 'pt_recalls')
    return True


def fight_end(run) -> None:
    """Out again to mend, and fed what he can spare."""
    if not cared(run):
        return
    s = state(run)
    if s['stowed']:                             # no mending in the sphere
        s['stowed'] = False
        s['turn'] = run.turn
    catch_up(run)
    if not alive(run) or s['hurt'] <= 0:
        return
    top = max_health(run)
    if s['hurt'] < 0.25 * top:
        return                                  # the walk mends that much
    if run.p.hp < run.prof['top_up_to'] * run.p.max_hp:
        return                                  # his own meals come first
    import difficulty_sim as ds
    over = max(0, len(run.pantry) - ds.PANTRY_MAX)
    spare = [(run.pantry, it) for it in run._spares()[:over]]
    belly, got = max(1, int(getattr(run.p, 'max_sp', 200) or 200)), 0
    for f in sorted(run.food, key=lambda f: -int(getattr(f, 'sp_restore', 0) or 0)):
        if got >= belly and int(getattr(f, 'hp_restore', 0) or 0) <= 0:
            spare.append((run.food, f))
        got += int(getattr(f, 'sp_restore', 0) or 0)
    for held, meal in spare:
        if meal not in held:
            continue
        held.remove(meal)
        s['hurt'] = max(0.0, s['hurt'] - max(1, int(top * 0.25)))
        _learn(s, max(20, min(80, int(getattr(meal, 'sp_restore', 20) or 20) // 2)))
        _count(run, 'pt_meals')
        top = max_health(run)
        if s['hurt'] < 0.25 * top:
            break


def bit(run, foe) -> None:
    if not on(run):
        return
    s = state(run)
    s['aggro'] = (id(foe), run.turn)
    if not foe.alive:
        _learn(s, 3 + max(1, min(100, int(getattr(foe, 'peak_floor', 1) or 1))) * 6 // 10)


def swipes(run, active: list) -> None:
    """One world turn of blows on the pet."""
    if not run.prof.get('pet') or run.floor < 3 or not k(run, 'pt_hp') or not here(run):
        return
    from dice import roll
    catch_up(run)
    s = state(run)
    aggro = s['aggro']
    for m in active:
        if (not m.alive or not getattr(m, 'attacks', None) or getattr(m, '_sim_away', 0) > 0
                or m.__dict__.get('_yielded') or m.__dict__.get('_holding')
                or getattr(m, 'is_allied', False)
                or any(m.has_effect(e) for e in ('sleeping', 'paralyzed', 'stunned', 'frozen',
                                                 'feared', 'charmed'))):
            continue
        full = bool(aggro and aggro[0] == id(m) and run.turn - aggro[1] <= 2)
        if full:
            dmg = max(1, roll(random.choice(m.attacks)['damage']))
        elif random.random() < BESIDE_PET:
            dmg = max(1, roll(m.attacks[0]['damage']) // 2)
        else:
            continue
        s['hurt'] += max(1, round(dmg * getattr(m, '_sim_dmg_x', 1.0)))
        if s['hurt'] >= max_health(run):
            _die(run)
            return


def _die(run) -> None:
    s = state(run)
    if run._quest_pet() == 'bococho':
        run.p.saddlebag_lb = 0                  # her bags went with her
    s.update(gone=run.floor, fed=0, aggro=None, hurt=0.0, stowed=False)
    _count(run, 'pt_deaths')


def feed(run, stat_ready: list) -> bool:
    """The floor's stat dish, given to the pet. True when it was."""
    share = float(k(run, 'pt_feed') or 0)
    if share <= 0 or not run.prof.get('beast') or not on(run) or run.floor < 3 or not alive(run):
        return False
    s = state(run)
    p = run.p
    if s['fed'] >= p.cooking_stat_softcap('STR'):       # food's own ladder by depth reached
        return False
    if share < 1.0 and random.random() >= share:
        return False
    import kitchen
    rec = stat_ready[-1]                    # what he would least have eaten himself
    run._consume(rec)
    run.dishes_left -= 1
    _count(run, 'cooks')
    p._cook_stat_gain_this_floor = p.PER_FLOOR_STAT_CAP
    if run.quiz.one_question(kitchen.dish_tier(rec)):
        s['fed'] += 1
        _count(run, 'pt_fed')
    return True
