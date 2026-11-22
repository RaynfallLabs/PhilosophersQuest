"""Many ways to win: the archetypes the simulator plays, and part 1's rulings
as measurement knobs (Brandon, 2026-11-21; ARCHETYPES_AND_CALLINGS_2026_11_21.md).

The rule under test: each archetype is a stat and a system leaned into; each
one's careful kid wins within about ten points of the others, and each one's
lean, taken away, costs it deaths.

Every knob's default is the game as it is (tests/test_sim_archetypes.py). The
bow's knobs are sim_ranger.py's, the pet's sim_pets.py's; here are the rest:

  cl_wis      R2. 0 = heals read INT (the game). 0.03: heals (dice and the share
              of max HP both), wards' turns and prayer's gifts grow 3% a point
              of the WIS he learned beyond the dungeon's own gift (one point
              every three floors), so that gift alone moves no one's heal.
  cl_wis_cap  R2. 1 = food may teach WIS as far as any stat. The maths clock
              does not count the points today's cap would not have allowed.
  cl_wards    1 = the hero learns and casts Mage Armour, Magic Shield and
              Stoneskin when a fight will last (the game's Shielded: +2 AC,
              physical blows halved). The spells are the game's; only the
              cleric's profile sets this.
  cl_mp_wis   a finding's dial: max MP for a point of learned WIS.
  fu_on       R3. 1 = a hero who leans on fury calls it up at will, in light
              body armour or none.
  fu_dmg      a furious hero's blows (the game's berserk: 1.3). It replaces
              berserk's step and never stacks on it.
  fu_tough    the share of every hurt fury takes off.
  fu_turns    turns a fury lasts.
  fu_cd       turns after it before he can call it again.
  la_wt       R3, light answers: x the weight of every coating.
  kt_even     a finding's dial: the stat this profile leans on is as cookable
              as STR is. In this cell's recipe book the dishes of his first
              stat_focus and of STR change places. A stand-in for writing the
              kitchen's stat dishes evenly; the game's book makes STR the
              easiest lesson in every band from 25 down (one-part dishes on 8
              to 14% of the spawns; DEX 1 to 6%, WIS 0 to 7%).
  st_lean     a finding's dial: a melee blow reads the better of STR and the
              stat this profile leans on (DEX, INT, WIS or PER), so every
              lean pays its blows as STR pays the fighter's. A stand-in for a
              weapon of each calling that reads its stat, never a stack.
  dx_finesse  a finding's dial: 1 = a Finesse weapon reads DEX for STR, as its
              own card says (combat.py declares finesse_dex and never reads it).

Profiles: arch_fighter, arch_tank, arch_mage, arch_rogue, arch_ranger,
arch_cleric, arch_barbarian, arch_beast; for each, the same kid with the lean
taken away, and the cook-only kid of it.
"""
from __future__ import annotations

import copy
import functools

import sim_pets
import sim_ranger

KNOBS = {
    'cl_wis': 0.0,
    'cl_wis_cap': 0,
    'cl_wards': 0,
    'cl_mp_wis': 0.0,
    'fu_on': 0,
    'fu_dmg': 1.3,
    'fu_tough': 0.0,
    'fu_turns': 20,
    'fu_cd': 30,
    'la_wt': 1.0,
    'dx_finesse': 0,
    'st_lean': 0,
    'kt_even': 0,
}
KNOBS.update(sim_ranger.KNOBS)
KNOBS.update(sim_pets.KNOBS)

BLOW_LEANS = ('DEX', 'INT', 'WIS', 'PER')
BERSERK = 1.3                   # combat.strike_damage's berserk step
WARD_TURNS = {'shield_self': 12, 'magic_shield_self': 20, 'stoneskin_self': 25}
WARD_FIGHT = 2.0                # x his blow: a group that will take more is worth a ward
STRIKE_KNOBS = ('ar_per', 'fu_on', 'dx_finesse', 'st_lean')   # those that change combat.strike_damage


def k(run, name):
    return run.knobs.get(name, KNOBS[name])


def _count(run, key, n=1) -> None:
    if run.fs is not None:
        run.fs[key] = run.fs.get(key, 0) + n


def _state(run) -> dict:
    s = run.__dict__.get('_arch_st')
    if s is None:
        s = run._arch_st = dict(wards={}, fury_until=-1, fury_ready=0)
    return s


# ------------------------------------------------------------------ profiles
def register(profiles: dict) -> None:
    fighter = profiles['mastery']
    mage = profiles['mastery_mage']
    rogue = profiles['mastery_dex']

    def add(name, base, knobs=None, **kw):
        prof = dict(base, **kw)
        if knobs:
            prof['knobs'] = dict(base.get('knobs') or {}, **knobs)
        prof['arch'] = name
        profiles[name] = prof
        return prof

    add('arch_fighter', fighter)
    tank = add('arch_tank', fighter, stat_focus=('CON', 'STR'))
    add('arch_mage', mage)
    add('arch_rogue', rogue)
    ranger = add('arch_ranger', rogue, stat_focus=('PER', 'DEX'), knobs=dict(ar_bow=1))
    cleric = add('arch_cleric', fighter, stat_focus=('WIS', 'CON'), armour_class=('light', 'medium'),
                 cleric=True, caster=True, quest_pet='mooble', knobs=dict(cl_wards=1))
    barbarian = add('arch_barbarian', fighter, armour_class='light', fury=True)
    beast = add('arch_beast', fighter, stat_focus=('CON', 'STR'), beast=True)

    # The same kid, his lean taken away.
    add('arch_tank_nolean', tank, armour_class='light', stat_focus=('STR', 'DEX'))
    add('arch_mage_nolean', mage, magic=False, casts=False)
    add('arch_ranger_nolean', ranger, knobs=dict(ar_bow=0))
    add('arch_cleric_nolean', cleric, magic=False, casts=False, knobs=dict(cl_wards=0))
    add('arch_barbarian_nolean', barbarian, fury=False)
    add('arch_beast_nolean', beast, beast=False)

    # The same kid, who only cooks (no study, no tactics).
    for name in ('arch_tank', 'arch_mage', 'arch_rogue', 'arch_ranger', 'arch_cleric',
                 'arch_barbarian', 'arch_beast'):
        add(name + '_cook', profiles[name], knobs=dict(families=0, tactics=0))
    add('arch_fighter_cook', profiles['cookonly'])


# ------------------------------------------------------------------- install
def install(knobs: dict) -> None:
    """combat.strike_damage reads this module's knobs for a simulated hero
    and is the game's for anyone else; with those knobs off it is the game's
    own function again. Once a cell (run_cell), never at import."""
    import combat
    now = combat.strike_damage
    wanted = any(knobs.get(name) for name in STRIKE_KNOBS)
    mine = getattr(now, '_sim_archetypes', False)
    if not wanted:
        if mine:
            combat.strike_damage = now.__wrapped__
        return
    if mine:
        return
    real = now

    @functools.wraps(real)
    def strike_damage(player, monster, chain, *a, **kw):
        run = getattr(player, '__dict__', {}).get('_sim_late')
        if run is None:
            return real(player, monster, chain, *a, **kw)
        return _strike(run, real, player, monster, chain, a, kw)
    strike_damage._sim_archetypes = True
    combat.strike_damage = strike_damage


_KITCHEN = {'swapped': None}


def lean_swap(knobs: dict, prof: dict):
    """The stat whose dishes change places with STR's in this cell, or None."""
    focus = tuple(prof.get('stat_focus') or ())
    if not knobs.get('kt_even') or not focus or focus[0] == 'STR':
        return None
    return focus[0]


def install_kitchen(knobs: dict, prof: dict) -> None:
    """kt_even: this process's recipe book for the cell, or the file's again."""
    import kitchen
    stat = lean_swap(knobs, prof)
    if stat == _KITCHEN['swapped']:
        return
    kitchen._cache.clear()                      # the file's, and all that was read from it
    _KITCHEN['swapped'] = stat
    if stat is None:
        return
    trade = {stat: 'STR', 'STR': stat}
    for rec in kitchen.raw_recipes().values():
        if isinstance(rec, dict) and rec.get('benefit') in trade:
            rec['benefit'] = trade[rec['benefit']]


def _strike(run, real, p, monster, chain, a, kw) -> int:
    import combat
    ranged = bool(kw.get('ranged', False))
    weapon = kw.get('weapon', combat._WIELDED)
    if weapon is combat._WIELDED:
        weapon = p.ranged_weapon if ranged else p.weapon
    if ranged:
        per = float(k(run, 'ar_per') or 0)
        if per <= 0:
            return real(p, monster, chain, *a, **kw)
        was = p.PER, p.STR
        p.PER = p.STR = 10                      # none of the game's own stat bonus
        try:
            out = real(p, monster, chain, *a, **kw)
        finally:
            p.PER, p.STR = was
        mult = sim_ranger.per_step(run, weapon, per)
        return max(1, int(round(out * mult))) if out > 0 else out
    stat = blow_stat(run, weapon)
    if stat != p.STR:
        was = p.STR
        p.STR = stat
        try:
            out = real(p, monster, chain, *a, **kw)
        finally:
            p.STR = was
    else:
        out = real(p, monster, chain, *a, **kw)
    if out > 0 and furious(run):
        step = float(k(run, 'fu_dmg'))
        if p.status_effects.get('berserk', 0) > 0:
            step /= BERSERK
        out = max(1, int(round(out * step)))
    return out


def blow_stat(run, weapon) -> int:
    """What a melee blow reads for Strength."""
    p = run.p
    stat = p.STR
    if k(run, 'dx_finesse') and getattr(weapon, 'class_mechanic', '') == 'finesse_dex':
        stat = p.DEX
    if k(run, 'st_lean'):
        focus = tuple(run.prof.get('stat_focus') or ())
        if focus and focus[0] in BLOW_LEANS:
            stat = max(stat, getattr(p, focus[0]))
    return stat


def str_factor(run, weapon) -> float:
    """Run._est_damage's Strength step."""
    return 1.0 + max(0, blow_stat(run, weapon) - 10) * 0.03


# --------------------------------------------------------------- R2, the cleric
def wis_lean(p) -> int:
    """The WIS he learned: not what he began with, not the depth's gift."""
    start = int((getattr(p, 'stats_at_start', None) or {}).get('WIS', 10))
    gift = max(0, int(getattr(p, 'deepest_floor_reached', 0) or 0)) // p.DEPTH_WIS_EVERY
    return max(0, int(p.WIS) - start - gift)


def wis_step(run) -> float:
    per = float(k(run, 'cl_wis') or 0)
    return 1.0 + per * wis_lean(run.p) if per > 0 else 1.0


def heal_factor(run) -> float:
    if float(k(run, 'cl_wis') or 0) > 0:
        return 2.0 * wis_step(run)              # 2.0 is int_damage_factor at INT 10
    import sim_magic
    return sim_magic.int_factor(run)


def stat_for_cap(p, stat):
    """Whose food cap a stat is held to."""
    return 'STR' if stat == 'WIS' and p._k.get('cl_wis_cap') else stat


def clock_excess(p) -> int:
    """WIS the new cap taught that the clock does not count."""
    if not p._k.get('cl_wis_cap'):
        return 0
    from player import Player
    today = Player.stat_cap_for_tier(p, 'WIS', p.depth_tier())
    return max(0, p.food_taught('WIS') - today)


def clock_wis(p) -> int:
    return p.WIS - clock_excess(p)


def sync_mp(run) -> None:
    per = float(k(run, 'cl_mp_wis') or 0)
    if per <= 0:
        return
    p = run.p
    want = int(round(per * wis_lean(p)))
    have = int(p.__dict__.get('_wis_mp_extra', 0))
    if want != have:
        p.max_mp = max(0, p.max_mp + want - have)
        p.mp = min(p.mp + max(0, want - have), p.max_mp)
        p.__dict__['_wis_mp_extra'] = want


def learn(run, item) -> bool:
    """A spellbook: a ward (cl_wards), or the cleric leaving what is not of
    his school. False = the simulator's own rules decide."""
    import difficulty_sim as ds
    prof = run.prof
    sid = getattr(item, 'spell_id', '') or ''
    sp = ds.SPELLS.get(sid) or {}
    fx = sp.get('effect')
    if k(run, 'cl_wards') and prof.get('casts') and fx in WARD_TURNS:
        book = _state(run)['wards']
        if sid not in book and run.quiz.one_question(item.quiz_tier):
            book[sid] = sp
        return True
    if prof.get('cleric'):
        return not (sid in ds.HEAL_SPELL_IDS or fx == 'smite')
    return False


def ward(run, active: list, queue: list) -> bool:
    """Shielded for a fight that will last. True when the turn went on it."""
    if not k(run, 'cl_wards'):
        return False
    book = _state(run)['wards']
    p = run.p
    if not book or p.has_effect('shielded') or p.has_effect('silenced'):
        return False
    foes = [m for m in list(active) + list(queue) if m.alive]
    if not foes:
        return False
    blow = run._value_vs(p.weapon, foes[0]) if p.weapon is not None else 1.0
    if sum(m.hp for m in foes) <= WARD_FIGHT * blow:
        return False
    reserve = 0
    if run.spells and p.hp < 0.7 * p.max_hp:
        reserve = min(c for c, _, _ in run.spells.values())
    sp = min(book.values(), key=lambda s: int(s['mp_cost']))
    cost = p.spell_mp_cost(int(sp['mp_cost']))
    if p.mp - cost < reserve:
        return False
    p.mp -= cost
    _count(run, 'cl_ward')
    if not run.quiz.one_question(int(sp.get('tier', 1))):
        return True
    if float(k(run, 'cl_wis') or 0) > 0:
        import game_magic
        from status_effects import MAX_EFFECT_DURATION
        reach = min(game_magic.INT_REACH_CAP, wis_step(run))
        p.add_effect('shielded', min(MAX_EFFECT_DURATION,
                                     max(2, int(WARD_TURNS[sp['effect']] * reach))))
    else:
        import difficulty_sim as ds
        ds._MMGame(p, foes, run.floor)._apply_spell_effect(sp, None)
    return True


# ------------------------------------------------------------ R3, the barbarian
def _bare_enough(p) -> bool:
    import gear
    return gear.body_class(p) == 'light'        # no body armour is light


def furious(run) -> bool:
    if not k(run, 'fu_on') or not run.prof.get('fury'):
        return False
    return run.turn < _state(run)['fury_until'] and _bare_enough(run.p)


def call_fury(run) -> None:
    """At will, and at no cost of an action, when it is ready."""
    if not k(run, 'fu_on') or not run.prof.get('fury'):
        return
    s = _state(run)
    if run.turn < s['fury_until'] or run.turn < s['fury_ready'] or not _bare_enough(run.p):
        return
    s['fury_until'] = run.turn + int(k(run, 'fu_turns'))
    s['fury_ready'] = s['fury_until'] + int(k(run, 'fu_cd'))
    _count(run, 'fu_calls')


def incoming(p, amount):
    """SimPlayer.take_damage: what fury takes off a hurt."""
    tough = float(p._k.get('fu_tough', 0) or 0)
    if tough <= 0 or amount <= 0:
        return amount
    run = p.__dict__.get('_sim_late')
    if run is None or not furious(run):
        return amount
    return max(1, round(amount * (1.0 - tough)))


# ------------------------------------------------------------ R3, light answers
def light_answers(run) -> None:
    x = float(k(run, 'la_wt'))
    if x == 1.0:
        return
    import coatings
    for i, it in enumerate(run.flasks):
        if it.__dict__.get('_la_done') or not coatings.coat_spec(it):
            continue
        new = copy.copy(it)                     # a found flask may be the shared one
        new.weight = float(getattr(it, 'weight', 0) or 0) * x
        new.__dict__['_la_done'] = True
        run.flasks[i] = new


# ---------------------------------------------------------- the floor and fight
def floor_start(run, snap) -> None:
    sim_ranger.floor_found(run, snap)
    sim_pets.floor_start(run)


def fight_start(run) -> None:
    call_fury(run)
    sim_ranger.fight_start(run)
    sim_pets.fight_start(run)


def fight_end(run, result: str) -> None:
    sim_ranger.fight_end(run, result)           # the arrows found again
    if result != 'dead':
        sim_pets.fight_end(run)                 # the pet out to mend, and fed


def floor_end(run) -> None:
    """What the review's tables read, for an archetype's profile only."""
    if not run.prof.get('arch'):
        return
    p, fs = run.p, run.fs
    for s in ('WIS', 'PER', 'INT'):
        fs['st_' + s] = fs.get('st_' + s, 0) + int(getattr(p, s))
    _count(run, 'cl_lean', wis_lean(p))
    _count(run, 'mp_max', p.max_mp)
    if sim_pets.on(run) and sim_pets.alive(run):
        _count(run, 'pt_floors')
        _count(run, 'pt_level', sim_pets.level(run))
        _count(run, 'pt_fed_held', sim_pets.state(run)['fed'])
