"""The simulated hero's own bow (2026-11-21, part 1's ruling R1: ruling D4 is
revisited, so a bow can carry a whole run). Measurement only: with `ar_bow` 0
(the default) nothing here runs, and the simulator is the one before it.

  ar_bow      1 = he plays a bow: keeps the best of each ammunition found, fires
              as a room's group closes, and shoots instead of striking when the
              shot is worth at least the blow. Shots go through the game's
              combat.player_attack (the maths chain, the bow's class, the arrow's
              bonus; the weakest arrow first and a crossbow's reload, as
              game_combat._fire_ranged).
  ar_per      0 = the game's bonus (PER and STR, 0.75% a point, onto the base;
              a composite bow's draw, 5% a point of STR, on top).
              R1: 0.03, PER alone, as STR pays a sword. A composite bow reads
              the better of PER and STR at that same rate, never the two
              multiplied (kept apart, its draw made a shot 1.5 to 2.5 sword
              blows deep: the "ranged hits way too hard" double dip again).
  ar_open     x the tiles a foe has still to walk when he is first seen.
  ar_kite     x the share of his actions a quicker archer spends stepping back
              (at most half); each step costs the foes behind him a blow.
  ar_recover  share of the arrows shot that are found again after a fight he
              holds the field of (the game: none).
  ar_fletch   arrows made from a harvest, of the creature's own tier (the game: none).
  ar_stall    arrows he buys up to at a stall (R5, supply follows the lean; 0 = none).
  ar_heads    1 = a coating can go on arrowheads: the bow carries it (the game
              refuses to coat a bow).

Measured for this model, 2026-11-21, on the real generator's floors 5-95: from
a room's doorway a monster stands MEET_TILES away (mean about 5); the hero
sees it no farther than his sight (5 at PER 10) and shoots no farther than the
bow's reach. He gets the shots that fit while it walks in.

Not modelled: cover and walls between, a shot into the dark, noise, habits
(They Learn Your Tricks), arrows of the named uniques' own effects.
"""
from __future__ import annotations

import contextlib
import copy
import random

KNOBS = {
    'ar_bow': 0,
    'ar_per': 0.0,
    'ar_open': 1.0,
    'ar_kite': 1.0,
    'ar_recover': 0.0,
    'ar_fletch': 0.0,
    'ar_stall': 0,
    'ar_heads': 0,
}
MEET_TILES = (2, 3, 3, 4, 4, 5, 5, 6, 7, 9)     # the measured distances' ten deciles
DOORWAY_TILES = (1, 2, 3)                        # those waiting beyond the first
MAX_VOLLEY = 8
AMMO_CARRY = 120                                 # of one type (6 lb of arrows)
_MADE = {}
_LADDER = {}


def k(run, name):
    return run.knobs.get(name, KNOBS[name])


def on(run) -> bool:
    return bool(k(run, 'ar_bow'))


def _state(run) -> dict:
    s = run.__dict__.get('_ranger')
    if s is None:
        s = run._ranger = dict(spares=[], ammo={}, spent={}, opened=False, volley_at=-1,
                               coating=False)
    return s


def _count(run, key, n=1) -> None:
    if run.fs is not None:
        run.fs[key] = run.fs.get(key, 0) + n


def _whole(x: float) -> int:
    n = int(x)
    return n + (1 if random.random() < x - n else 0)


# ------------------------------------------------------------------ ammunition
def _template(aid: str):
    it = _MADE.get(aid)
    if it is None:
        import items
        it = _MADE[aid] = items.make_item_by_id('ammo', aid)
    return it


def ladder(kind: str) -> list:
    """The common ammunition of a type, weakest tier first."""
    if kind not in _LADDER:
        import items
        common = [a for a in items.load_items('ammo')
                  if a.ammo_type == kind and not getattr(a, 'is_unique', False)
                  and a.id.endswith('_' + kind)]
        _LADDER[kind] = sorted(common, key=lambda a: a.tier)
    return _LADDER[kind]


def add_ammo(run, aid: str, n: int) -> int:
    """He takes what he can carry of it. Returns how many."""
    s = _state(run)
    kind = _template(aid).ammo_type
    have = sum(c for a, c in s['ammo'].items() if _template(a).ammo_type == kind)
    n = min(int(n), AMMO_CARRY - have)
    if n <= 0:
        return 0
    s['ammo'][aid] = s['ammo'].get(aid, 0) + n
    return n


def next_ammo(run, bow):
    """(id, template) of what the game would fire: the weakest he carries.
    (None, None) for endless stones; None when he has none."""
    if bow is None:
        return None
    if getattr(bow, 'infinite_ammo', False):
        return (None, None)
    best = None
    for aid, n in _state(run)['ammo'].items():
        if n <= 0:
            continue
        a = _template(aid)
        if a.ammo_type != bow.requires_ammo:
            continue
        if best is None or (a.damage_bonus, a.name) < (best[1].damage_bonus, best[1].name):
            best = (aid, a)
    return best


# --------------------------------------------------------------------- damage
def shot_stat(p, bow) -> int:
    """R1: the stat a shot reads."""
    if getattr(bow, 'class_mechanic', '') == 'str_bonus_range_7':
        return max(p.PER, p.STR)
    return p.PER


def stat_factor(run, bow, base: float) -> float:
    """What PER (and, in the game, STR) does to a shot's base."""
    import combat
    p = run.p
    per = float(k(run, 'ar_per') or 0)
    crossbow = getattr(bow, 'weapon_class', '') == 'crossbow'
    if per > 0:
        return 1.0 + per * max(0, shot_stat(p, bow) - 10)
    else:
        more = 0
        for step in (max(0, (p.PER - 10) // 4),) + (() if crossbow else (max(0, (p.STR - 10) // 4),)):
            if step:
                more += max(step, int(round(base * combat.RANGED_STAT_SHARE * step)))
        out = (base + more) / max(1.0, base)
    if getattr(bow, 'class_mechanic', '') == 'str_bonus_range_7':
        out *= 1.0 + max(0, p.STR - 10) * 0.05
    return out


def shot_value(run, bow, target=None) -> float:
    """A shot as the hero judges it, on the same sum as Run._weapon_score."""
    got = next_ammo(run, bow)
    if got is None:
        return 0.0
    import difficulty_sim as ds
    as_blade = (run._value_vs(bow, target) if target is not None else run._weapon_score(bow))
    as_blade /= 1.0 + max(0, run.p.STR - 10) * 0.03     # _est_damage put Strength on it
    base = float(bow.base_damage or ds.dice_mean(bow.damage))
    own = max(1.0, base + bow.enchant_bonus)
    bonus = got[1].damage_bonus if got[1] is not None else 0
    return as_blade * stat_factor(run, bow, base) * (own + bonus) / own


def per_action(run, bow, melee: float, target=None) -> float:
    """What shooting this bow is worth an action: a crossbow's every other
    action is the cranking, when he strikes."""
    v = shot_value(run, bow, target)
    if v > 0 and getattr(bow, 'weapon_class', '') == 'crossbow':
        return (v + melee) / 2.0
    return v


def kit_blow(run, melee: float) -> float:
    """Run._kit_cost's blows a kill: an archer's are mostly shots."""
    if not on(run) or run.p.ranged_weapon is None:
        return melee
    return max(melee, per_action(run, run.p.ranged_weapon, melee))


def best_blow(run, target, melee: float) -> float:
    """The blow a spell or a flask has to beat."""
    if not on(run) or run.p.ranged_weapon is None:
        return melee
    return max(melee, shot_value(run, run.p.ranged_weapon, target))


def main_weapon(run):
    """The weapon the smith and a scroll of enchant work on."""
    p = run.p
    if not on(run) or p.ranged_weapon is None:
        return p.weapon
    if p.weapon is None:
        return p.ranged_weapon
    bow = p.ranged_weapon
    base = float(bow.base_damage or 1)
    shot = run._weapon_score(bow) / (1.0 + max(0, p.STR - 10) * 0.03) * stat_factor(run, bow, base)
    return bow if shot >= run._weapon_score(p.weapon) else p.weapon


@contextlib.contextmanager
def hand(run, weapon=None):
    """For a while the rules that read the weapon in hand read the bow."""
    weapon = main_weapon(run) if weapon is None else weapon
    p = run.p
    old = p.weapon
    if not on(run) or weapon is None or weapon is old:
        yield
        return
    p.weapon = weapon
    run.__dict__['_hand'] = True
    try:
        yield
    finally:
        p.weapon = old
        run.__dict__.pop('_hand', None)


# ------------------------------------------------------------- bows and packs
def consider_bow(run, item) -> bool:
    """A bow found: the best of each ammunition is kept."""
    if not on(run) or not getattr(item, 'base_damage', None):
        return False
    s = _state(run)
    p = run.p
    held = [b for b in [p.ranged_weapon] + s['spares'] if b is not None]
    same = next((b for b in held if b.requires_ammo == item.requires_ammo), None)

    def worth(b):
        base = float(b.base_damage or 1)
        v = run._weapon_score(b) * stat_factor(run, b, base)
        return v / 2.0 if getattr(b, 'weapon_class', '') == 'crossbow' else v
    if same is not None and worth(item) <= 1.05 * worth(same):
        return False
    new = copy.copy(item)
    if same is not None and same is p.ranged_weapon:
        p._apply_equip(new)
    elif same is not None:
        s['spares'][s['spares'].index(same)] = new
    elif p.ranged_weapon is None:
        p._apply_equip(new)
    else:
        s['spares'].append(new)
    run._sync_pack()
    return True


def consider_ammo(run, item) -> bool:
    if not on(run):
        return False
    if add_ammo(run, item.id, int(getattr(item, 'count', 1) or 1)):
        run._sync_pack()
    return True


def choose(run) -> None:
    """Between fights: the bow worth most that he has the arrows for."""
    s = _state(run)
    p = run.p
    if not s['spares']:
        return
    melee = run._weapon_score(p.weapon) if p.weapon is not None else 1.0
    best, best_v = p.ranged_weapon, 0.0
    for b in ([p.ranged_weapon] if p.ranged_weapon else []) + s['spares']:
        v = per_action(run, b, melee)
        if v > best_v:
            best, best_v = b, v
    if best is None or best is p.ranged_weapon:
        return
    old = p.ranged_weapon
    p._apply_equip(best)
    if p.ranged_weapon is best:
        s['spares'].remove(best)
        if old is not None:
            s['spares'].append(old)
        run._sync_pack()


def spares(run) -> list:
    return _state(run)['spares'] if on(run) else []


def ammo_pack(run) -> list:
    """The arrows as stacks, for the weight."""
    if not on(run):
        return []
    out = []
    for aid, n in _state(run)['ammo'].items():
        if n > 0:
            it = copy.copy(_template(aid))
            it.count = n
            out.append(it)
    return out


# -------------------------------------------------------------------- supply
def floor_found(run, snap) -> None:
    if not on(run):
        return
    for aid, n in getattr(snap, 'ammo', ()) or ():
        if random.random() < run.prof['loot_fraction']:
            _count(run, 'ar_found', add_ammo(run, aid, n))


def on_kill(run, m) -> None:
    """An archer's quiver (game_combat: treasure.ammo_drop)."""
    if not on(run):
        return
    drop = (getattr(m, 'treasure', None) or {}).get('ammo_drop')
    if drop and random.random() < float(drop.get('chance', 0.65)) * run.prof['loot_fraction']:
        lo, hi = drop.get('count_range', [3, 8])
        _count(run, 'ar_found', add_ammo(run, drop['ammo_id'], random.randint(int(lo), int(hi))))


def on_harvest(run, kind) -> None:
    """Fletched from the kill, as good as the creature it came from."""
    per = float(k(run, 'ar_fletch') or 0)
    if not on(run) or per <= 0:
        return
    import items
    import sim_late
    defn = sim_late.real_defs().get(kind) if kind else None
    level = sim_late.peak_of(defn) if defn else run.floor
    tier = items._floor_band_tier(level) or 1
    bow = run.p.ranged_weapon
    made = 'bolt' if bow is not None and bow.requires_ammo == 'bolt' else 'arrow'
    rungs = [a for a in ladder(made) if a.tier <= tier]
    if rungs:
        _count(run, 'ar_made', add_ammo(run, rungs[-1].id, _whole(per)))


def shop(run, floor: int, defn: dict) -> None:
    want = int(k(run, 'ar_stall') or 0)
    bow = run.p.ranged_weapon
    if not on(run) or want <= 0 or bow is None or getattr(bow, 'infinite_ammo', False):
        return
    import economy
    rungs = [a for a in ladder(bow.requires_ammo) if a.min_level <= floor]
    if not rungs:
        return
    have = sum(n for a, n in _state(run)['ammo'].items()
               if _template(a).ammo_type == bow.requires_ammo)
    stack = copy.copy(rungs[-1])
    stack.count = 10
    price = economy.stock_price(stack, floor, float(defn.get('markup', 1.0) or 1.0))
    while have + stack.count <= want:
        if not run._pay(price, 0.5 * economy.floor_income(floor)):
            break
        got = add_ammo(run, stack.id, stack.count)
        _count(run, 'ar_bought', got)
        have += stack.count


# -------------------------------------------------------------------- the fight
def fight_start(run) -> None:
    if not on(run):
        return
    s = _state(run)
    s.update(opened=False, volley_at=-1, spent={})
    choose(run)


def fight_end(run, result: str) -> None:
    if not on(run):
        return
    s = _state(run)
    share = float(k(run, 'ar_recover') or 0)
    if share > 0 and result == 'won':
        for aid, n in s['spent'].items():
            _count(run, 'ar_recovered', add_ammo(run, aid, _whole(n * share)))
    s['spent'] = {}
    run._sync_pack()


def coat_bow(run, target) -> bool:
    """Run._coat_for, for a hero who will shoot this foe: the coating goes on
    the arrowheads (ar_heads), or nowhere. True when this handled it."""
    if not on(run) or target is None or run.__dict__.get('_hand'):
        return False
    bow = run.p.ranged_weapon
    if bow is None or next_ammo(run, bow) is None:
        return False
    if run.p.weapon is not None and shot_value(run, bow, target) < run._value_vs(run.p.weapon, target):
        return False
    if k(run, 'ar_heads'):
        with hand(run, bow):
            run._coat_for(target)
    return True


def will_shoot(run, target) -> bool:
    if not on(run):
        return False
    p = run.p
    bow = p.ranged_weapon
    if bow is None or next_ammo(run, bow) is None or p.status_effects.get('reloading', 0) > 0:
        return False
    melee = run._value_vs(p.weapon, target) if p.weapon is not None else 1.0
    return shot_value(run, bow, target) >= melee


def shoot(run, target, active, crank: bool = True) -> bool:
    """One shot through the game's combat.player_attack. True when loosed."""
    import combat
    import sim_groups
    import sim_late
    p = run.p
    bow = p.ranged_weapon
    got = next_ammo(run, bow)
    if got is None or sim_groups.hero_slowed(run):
        return False
    if p.has_effect('charmed') and random.random() < 0.40:
        return False
    aid, ammo = got
    s = _state(run)
    if aid is not None:
        s['ammo'][aid] -= 1
        s['spent'][aid] = s['spent'].get(aid, 0) + 1
    p._combat_monsters_ref = active
    target._sim_attacks += 1
    run.quiz.stop_at = None
    with hand(run, bow):
        met = sim_late.blow_pre(run, target)
    combat.player_attack(p, target, run.quiz, lambda *a, **kw: None, ammo=ammo, ranged=True)
    with hand(run, bow):
        sim_late.blow_post(run, target, met)
        run._feel(target)
    if crank and getattr(bow, 'weapon_class', '') == 'crossbow':
        skip = int(getattr(p, '_crossbow_skip_reloads', 0) or 0)
        if skip > 0:
            p._crossbow_skip_reloads = skip - 1
        else:
            p.status_effects['reloading'] = 2
    _count(run, 'ar_shots')
    return True


def _shots_before_contact(run, group, tiles: int) -> int:
    import difficulty_sim as ds
    p = run.p
    bow = p.ranged_weapon
    walkers = [m for m in group if m.ai_pattern not in ds.RANGED_PATTERNS and m.ai_pattern != 'dragon']
    if not walkers:                                 # an exchange: as many as they get
        if all(m.ai_pattern == 'dragon' for m in group):
            return 1
        return int(run.knobs['ranged_shots'])
    if any(m.ai_pattern in ('ambush', 'mimic') for m in walkers):
        return 0
    fastest = max(m.speed for m in walkers)
    if fastest >= ds.FAST_SPEED:
        return 0
    seen = min(tiles, max(1, p.get_sight_radius()), bow.reach + max(0, p.PER - 10) // 3)
    steps = max(0.0, (seen - 1) * float(k(run, 'ar_open')))
    if steps <= 0:
        return 0
    n = min(float(MAX_VOLLEY), steps * float(p.get_speed()) / max(1.0, float(fastest)))
    if getattr(bow, 'weapon_class', '') == 'crossbow':
        n /= 2.0
    return _whole(n)


def volley(run, active: list, queue: list, turn: int) -> bool:
    """He has no one at his elbow and foes are coming on: the shots he gets
    before they reach him, one budget for all of them. True when one died
    (Run.fight then books the dead before the rest walk in)."""
    if not on(run) or active or not queue:
        return False
    s = _state(run)
    if s['volley_at'] == turn:
        return False
    s['volley_at'] = turn
    opening, s['opened'] = not s['opened'], True
    p = run.p
    if p.ranged_weapon is None or next_ammo(run, p.ranged_weapon) is None:
        return False
    coming = list(queue) if opening else list(queue[:run.engagers])
    n = _shots_before_contact(run, coming, random.choice(MEET_TILES if opening else DOORWAY_TILES))
    import difficulty_sim as ds
    fell = False
    for _ in range(n):
        left = [m for m in coming if m.alive]
        if not left or p.hp <= 0 or not run.player_can_act():
            break
        target = next((m for m in left if ds.is_named(m)), left[0])
        if not shoot(run, target, coming, crank=False):
            break
        _count(run, 'ar_first')
        run.pass_time_in_fight()
        fell = fell or not target.alive
    return fell


def shoot_or_kite(run, target, active) -> str:
    """A quicker archer sometimes steps back instead: whoever is at his
    elbow follows him in and loses that blow."""
    import difficulty_sim as ds
    p = run.p
    foes = [m for m in active if m.alive and m.ai_pattern not in ds.RANGED_PATTERNS
            and m.ai_pattern not in ('dragon', 'sessile')
            and not any(m.has_effect(e) for e in ('sleeping', 'paralyzed', 'stunned', 'frozen'))]
    if foes:
        speed = max(1.0, float(p.get_speed()))
        share = min(0.5, max(0.0, (speed - max(m.speed for m in foes)) / speed) * float(k(run, 'ar_kite')))
        if share > 0 and random.random() < share:
            for m in foes:
                m.__dict__['_sim_kited'] = True
            _count(run, 'ar_kited')
            return 'kite'
    shoot(run, target, active)
    return 'shoot'


def kited(m) -> bool:
    """Monster turn: spent following a step back."""
    return bool(m.__dict__.pop('_sim_kited', False))
