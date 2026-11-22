"""The simulator's group fight: what a room's monsters do together
(2026-11-20; Brandon: "let's run the simulator first with non-serial
monsters to see what's really happening").

difficulty_sim.fight meets a room's group `engagers` at a time: that many
stand beside the hero (the FRONT, the fight's `active` list) and the rest wait
their turn (the QUEUE). Until now the queue did nothing but wait, so a healer,
a summoner, an archer or a caster at the back of a room never acted until a
slot beside the hero opened for it, and a group's nerve broke one creature at
a time. This module gives the queue its turn (the BACK RANK) and the group its
nerve, through the game's own functions, from a few marked hooks in
difficulty_sim.py. Each mechanic has a knob that defaults on (KNOBS, merged
into difficulty_sim.KNOB_DEFAULTS); 0 is its ablation, and with every knob at
0 the fight is exactly the one before this module.

The ground (Ground). The simulator has no map, but a back rank needs one: its
lines of fire, its lanes and its reach are tiles. Each fight stands on a
small real dungeon.Dungeon around the hero at (5, 5), its shape set by how
many are on him (the larger of `engagers` and the front's size, so a pack
that comes on together fights him in the open):
  1     a corridor: the hero two tiles in, one foe on him (6, 5), the room
        beyond; the front blocks every line of fire down the corridor;
  2-3   a room's corner at his back: three tiles beside him (6, 5), (5, 6),
        (6, 6), the room before him (at 2 one of the three is a gap the
        archers can shoot through);
  4+    the open: all eight tiles beside him.
The front stands on difficulty_sim.fight's own slots (the first `k` of
SLOTS, each its own tile); the back rank on the free tiles 2 to BACK_MAX from
him on the room's side, in the queue's order, nearest first.

  grp_heal      A healer (ai_pattern 'healer') at the back mends a badly hurt
                friend: the real faction.heal_choice / heal through AI-1's own
                turn (sim_ai1.monster_turn, its ai_heal knob), its rest
                between prayers ticking (Monster.tick_effects, faction.tick).
                With nothing to mend it shoots, if it has a distance attack
                (the real Monster._ranged_turn, as Monster._healer_turn).
                Reach is the simulator's melee rule (anywhere in the fight:
                faction.heal_choice reach=None), not the game's one tile.
  grp_summon    A summoner at the back chants and calls (the real
                summoning.step through sim_ai1.monster_turn): the hero cannot
                reach it, so no blow breaks the chant; its summons come up
                behind the front (into the queue, in front of it), at most
                its live cap (2) standing. With no call ready it shoots, as
                Monster._summoner_turn does.
  grp_book      A caster with a Caster's Book (caster_ai.book) at the back
                casts by need: mends its side, wards itself, curses or
                dispels the hero (the real caster_ai.turn, through
                sim_ai3.monster_turn and its ai3_caster knob); its bolts fly
                only with a clear shot (Monster._has_clear_shot on the
                ground), its ranged turn as any archer's. The ward is on the
                caster itself (caster_ai: "a ward rises about it").
  grp_backrank  An archer (ai_pattern 'ranged', no book) at the back takes the
                real Monster._ranged_turn on the ground: a clear shot is
                loosed (the real Monster.attack from its tile, which picks a
                missile within its reach, lanes.within_reach); a shot blocked
                by the front steps to a lane or holds (AI-2's
                lanes.blocked_turn / find_lane, the game's own code); with no
                shot it comes on but never past the front (a step beside the
                hero is taken back: `engagers` stays the front's size). Its
                shots need engagers 2 or more: in the corridor the front
                blocks every line.
  grp_orders    The Captain's Orders (AI-2, tactical_mind.band_order, the
                real function on a band dict like the floor's): when the
                captain orders the screen as the fight opens (the hero seen
                and not badly hurt, the band whole), his guards come at the
                hero first and he behind them (the queue's order of battle:
                guards, the leader, then the shooters, casters and healers,
                who keep their distance); the floor's order put the leader
                first in every band. When half the band is down he calls the
                fall-back: for its turns (orders.fall_back_turns) no band
                member steps up from the back into a free place (those in
                the fight fight on; a shooter with a lane still shoots). A
                charge (the hero under 40%) is the simulator's default: all
                come on as places free. Needs a war-band in the group.
  grp_morale    Morale in groups (AI-1, src/morale.py, src/war_bands.py): one
                of its side falls and its hurt kin that saw it check their
                nerve (the real morale.kin_fell, as Game._ai_on_kill); a
                band's leader falls or yields and the band answers
                (war_bands.on_death: the rout, the crumble, the quarrel; half
                the band down, some of the rest lose heart); a chain of
                war_bands' nerve_chain (6) or more on a living leader shakes
                his followers (war_bands.on_great_blow). The followers'
                `_band_leader` is set to the leader in this fight: it was the
                floor's cached creature (copy.copy of the snapshot), which
                never dies, so no follower ever broke when his captain fell
                (war_bands.holds_nerve). Kin checks need more than one of a
                side in the fight; the band's answer needs a war-band.
  grp_speed     The world's clock, as Game._advance_turn runs it. Each hero
                action moves it 10/speed of a turn (defence.world_turns) and
                every monster takes one turn for each world turn (the game
                has no energy system: a creature's own speed gives it no
                extra actions; see SPEED below). What was wrong, and is now
                the game's rule:
                  * the statuses (the hero's and the monsters': haste, slow,
                    poison, bleeds, a healer's rest, a caster's cooldowns),
                    the prayer's cooldown and regeneration tick once a HERO
                    ACTION, before the world's turns (the game's order), not
                    once a world turn: a hasted hero's haste lasted twice its
                    actions, and a slowed foe stayed slowed twice as long;
                  * a Slowed hero is on the same clock (2026-11-22): every
                    action of his takes two turns, whatever it is
                    (Player.get_speed halves);
                  * a creature of speed 14 or more closes two tiles a turn
                    (Monster._standard_move) and so strikes as it arrives
                    when its last step starts two tiles off: always when it
                    steps up from the queue behind the front, about half the
                    time as a fight opens (FAST_OPENING_BLOW, measured on the
                    real take_turn in tests/test_sim_groups.py). The old rule
                    gave it the blow every time.

SPEED, the game's rule (src/monster.py, src/main.py, src/defence.py), which
the simulator follows exactly (tests/test_sim_groups.py runs the real
Game._advance_turn beside it):
  * speed under 8: it loses (8 - speed) / 10 of its turns (take_turn);
  * speed 8 to 13: no difference from 10, at all;
  * speed 14 and over: two steps of movement a turn (closing, catching a
    fleeing hero, the arrival blow above); never a second blow;
  * the hero's speed (Player.get_speed) sets how many world turns his action
    is worth: haste (20) every other action; speed 9 two turns one action in
    nine.
So a deep kind given more speed by lore does nothing in a melee unless the
game's turn loop changes.

Not modelled: a back-rank healer's walk to the friend it mends (it mends
anyone in the fight), the back rank's shots at a hero who flees, the Tactical
Mind's own moves in the back rank (its measured worth is sim_ai2's), the
captain's charge pulling shooters into the melee, a routed band leaving the
floor (the frightened stay in the fight and do not strike).
"""
from __future__ import annotations

import random

import caster_ai
import kind_data
import morale
import tactical_mind
import war_bands
from dungeon import Dungeon, Room, WALL, FLOOR

KNOBS = {
    'grp_heal': 1,
    'grp_summon': 1,
    'grp_book': 1,
    'grp_backrank': 1,
    'grp_orders': 1,
    'grp_morale': 1,
    'grp_speed': 1,
}
# The knobs of the back rank and the group (grp_speed is the clock's own).
GROUP_KNOBS = ('grp_heal', 'grp_summon', 'grp_book', 'grp_backrank', 'grp_orders', 'grp_morale')
BACK_KNOBS = ('grp_heal', 'grp_summon', 'grp_book', 'grp_backrank')

HERO = (5, 5)
# difficulty_sim.fight's slots, in the order it fills them.
SLOTS = [(6, 5), (5, 6), (6, 6), (4, 5), (5, 4), (4, 4), (6, 4), (4, 6)]
BACK_MAX = 7               # the back rank stands within this many tiles of him
GROUND_SIZE = 18
# A creature of speed 14+ that closes from a fight's opening distance
# strikes as it arrives about this often (its last double step starts two
# tiles off half the time): measured on the real Monster.take_turn,
# tests/test_sim_groups.py. From the queue right behind the front (two tiles
# off) it always does.
FAST_OPENING_BLOW = 0.5
FAST_SPEED = 14            # Monster._standard_move: move_steps = 2 if speed >= 14


def on(run, knob) -> bool:
    return bool(run.knobs.get(knob, 1))


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _fs(run, key, n=1):
    run.fs[key] = run.fs.get(key, 0) + n


# ---------------------------------------------------------------------------
# The ground
# ---------------------------------------------------------------------------

def shape_for(n_front: int) -> str:
    """The ground a fight with this many on the hero stands on."""
    if n_front <= 1:
        return 'corridor'
    if n_front <= 3:
        return 'corner'
    return 'open'


def ground(shape: str, level: int = 1) -> Dungeon:
    """A small real dungeon for the fight (a fresh one each fight: the lanes
    and the orders keep notes on it)."""
    n = GROUND_SIZE
    tiles = [[WALL] * n for _ in range(n)]

    def floor(x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                tiles[y][x] = FLOOR
    if shape == 'corridor':
        floor(5, 5, 7, 5)                    # the hero two tiles in, the front at (6, 5)
        # (the way behind him is no part of the fight: nothing comes from it)
        floor(8, 1, 16, 9)                   # the room beyond the mouth
    elif shape == 'corner':
        floor(5, 5, 16, 16)                  # his back in the room's corner
    else:
        floor(1, 1, 14, 14)
    return Dungeon(tiles, [Room(0, 0, n, n)], n, n, int(level or 1))


def front_tiles(g: Dungeon) -> list:
    return [t for t in SLOTS if g.is_walkable(*t)]


def back_tiles(g: Dungeon) -> list:
    """The tiles the back rank may stand on: walkable, 2 to BACK_MAX from the
    hero, on the room's side of him (reached from the front without passing
    him), nearest first."""
    from collections import deque
    start = front_tiles(g)
    seen = set(start)
    q = deque(start)
    out = []
    while q:
        cx, cy = q.popleft()
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                t = (cx + ox, cy + oy)
                if t in seen or t == HERO or not g.is_walkable(*t):
                    continue
                if _cheb(*t, *HERO) > BACK_MAX:
                    continue
                seen.add(t)
                q.append(t)
                if _cheb(*t, *HERO) >= 2:
                    out.append(t)
    return sorted(out, key=lambda t: (_cheb(*t, *HERO), abs(t[0] - HERO[0]) + abs(t[1] - HERO[1]),
                                      t[1], t[0]))


class Fight:
    """One fight's group state (run._grp)."""

    def __init__(self, run, k: int):
        self.k = max(1, int(k))
        self.level = int(getattr(run, 'floor', 1) or 1)
        self.shape = None
        self.g = None
        self.back = []
        self.back_set = frozenset()
        self.band = None            # the band dict the orders keep (on the ground too)
        self.order = ''
        self.all = []               # every creature of the fight, the fallen too (Game.monsters)
        self.cs0 = int(getattr(getattr(run, 'quiz', None), 'chain_sum', 0) or 0)
        self.lead_hp = {}
        self.set_shape(self.k)

    def set_shape(self, n_front: int) -> None:
        shape = shape_for(max(self.k, n_front))
        if shape == self.shape:
            return
        self.shape = shape
        self.g = ground(shape, self.level)
        if self.band is not None:
            self.g.band = self.band
        self.back = back_tiles(self.g)
        self.back_set = frozenset(self.back)


def _named(m) -> bool:
    return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False)
                or getattr(m, 'is_seal_demon', False) or kind_data.named(m))


def role(m) -> str | None:
    """What a creature does from the back, by the knob that rules it:
    'grp_heal', 'grp_summon', 'grp_book', 'grp_backrank', or None (it waits
    its turn at the doorway). Named foes keep their own fights."""
    if _named(m) or kind_data.outside_rules(m):
        return None
    pat = getattr(m, 'ai_pattern', '')
    if pat == 'healer':
        return 'grp_heal'
    if getattr(m, 'summon_kind', None):
        return 'grp_summon'
    if caster_ai.book(m):
        return 'grp_book'
    if pat == 'ranged':
        return 'grp_backrank'
    return None


def _shoots_from_afar(m) -> bool:
    """Its turn with nothing else to do is the real ranged turn: an archer,
    or a healer or summoner with a distance attack (Monster._healer_turn,
    _summoner_turn: two attacks or more, one from afar)."""
    pat = getattr(m, 'ai_pattern', '')
    if pat == 'ranged':
        return True
    if pat in ('healer', 'summoner'):
        return len(getattr(m, 'attacks', None) or ()) > 1 and bool(m._distance_attacks())
    return False


def _reseat(st: Fight, active: list) -> None:
    """The front on the fight's own slots, each its own tile (enter() seats
    by count, so a newcomer could stand on a survivor's tile)."""
    tiles = front_tiles(st.g) or SLOTS[:1]
    free = [t for t in SLOTS if t in tiles]
    used = set()
    pending = []
    for m in active:
        t = (m.x, m.y)
        if t in free and t not in used:
            used.add(t)
        else:
            pending.append(m)
    spare = [t for t in SLOTS if t not in used]
    for m in pending:
        if spare:
            m.x, m.y = spare.pop(0)


def _place(st: Fight, active: list, queue: list) -> None:
    """Each of the queue on a back-rank tile of its own (kept while it is
    free and its own), nearest the hero first, in the queue's order."""
    taken = {(m.x, m.y) for m in active if m.alive}
    keep = []
    for m in queue:
        t = (m.x, m.y)
        if m.__dict__.get('_grp_back') and t in st.back_set and t not in taken:
            taken.add(t)
            keep.append(m)
    free = [t for t in st.back if t not in taken]
    for m in queue:
        if m in keep:
            continue
        if free:
            m.x, m.y = free.pop(0)
        else:
            m.x, m.y = st.back[-1] if st.back else (HERO[0] + 2, HERO[1])
        m._grp_back = True


# ---------------------------------------------------------------------------
# The hooks (difficulty_sim.Run.fight)
# ---------------------------------------------------------------------------

def fight_start(run, group: list, queue: list) -> list:
    """Before the first blow: the ground, the band's true leader, the order
    of battle. Returns the queue (reordered by the captain's screen)."""
    st = run._grp = Fight(run, getattr(run, 'engagers', 1))
    st.all = list(group)
    if not any(on(run, k) for k in GROUP_KNOBS):
        return queue
    for m in group:
        m.__dict__.pop('_grp_back', None)
        m.__dict__.pop('_grp_answered', None)
    if on(run, 'grp_morale'):
        _true_leaders(group)
    _place(st, [], queue)
    if on(run, 'grp_orders'):
        queue = _order_of_battle(run, st, group, queue)
        _place(st, [], queue)
    return queue


def _true_leaders(group: list) -> None:
    """A follower's leader is the leader in this fight (the copy), not the
    floor's cached creature the copy was made from."""
    by_proto = {id(getattr(m, '_sim_proto', None)): m for m in group}
    for m in group:
        lead = m.__dict__.get('_band_leader')
        if lead is not None and id(lead) in by_proto:
            m._band_leader = by_proto[id(lead)]


def _band_of(group: list):
    """(uid, leader, members) of the war-band in this group, or None."""
    for m in group:
        if m.__dict__.get('_band_role') == 'leader' and m.alive:
            uid = m.__dict__.get('_band')
            members = [o for o in group if o.__dict__.get('_band') == uid]
            if len(members) >= 2:
                return uid, m, members
    return None


def _ask_order(run, st: Fight, everyone: list) -> str:
    """The band's order this turn (tactical_mind.band_order: the captain's
    eyes, the band's count)."""
    if st.band is None:
        return ''
    lead = next((m for m in everyone if m.alive and m.__dict__.get('_band') == st.band['uid']
                 and m.__dict__.get('_band_role') == 'leader'), None)
    if lead is None:
        st.order = ''
        return ''
    lead._tracking = True
    was = tactical_mind.TURN.n
    tactical_mind.TURN.n = max(1, int(getattr(run, 'turn', 1) or 1))
    try:
        st.order = tactical_mind.band_order(lead, run.p, st.g, everyone) or ''
    finally:
        tactical_mind.TURN.n = was
    lead.__dict__.pop('_ai_lines', None)
    return st.order


def _order_of_battle(run, st: Fight, group: list, queue: list) -> list:
    """The captain's screen: his guards come at the hero first, he behind
    them, then those who keep their distance."""
    band = _band_of(group)
    if band is None:
        return queue
    uid, lead, members = band
    counts = {r: sum(1 for o in members if o.__dict__.get('_band_role') == r)
              for r in war_bands.ROLES}
    st.band = {'id': lead.__dict__.get('_band_id', ''), 'uid': uid, 'counts': counts,
               'said': True}
    st.g.band = st.band
    order = _ask_order(run, st, [m for m in group if m.alive])
    if order != 'screen':
        return queue
    mine = [m for m in queue if m.__dict__.get('_band') == uid]
    if lead not in mine:
        return queue
    rank = {'guard': 0, 'leader': 1}
    ordered = sorted(mine, key=lambda o: rank.get(o.__dict__.get('_band_role'), 2))
    if ordered == mine:
        return queue
    _fs(run, 'grp_screens')
    it = iter(ordered)
    return [next(it) if m.__dict__.get('_band') == uid else m for m in queue]


def next_up(run, queue: list, active: list):
    """The next of the queue to step up beside the hero (popped), or None
    when the band falls back round its captain and only band members wait
    (never while no one is on him: then they come)."""
    st = run.__dict__.get('_grp')
    if (st is not None and st.order == 'fall_back' and st.band is not None
            and on(run, 'grp_orders') and any(m.alive for m in active)):
        for i, m in enumerate(queue):
            if m.__dict__.get('_band') != st.band['uid'] or \
                    m.__dict__.get('_band_role') == 'leader':
                return queue.pop(i)
        _fs(run, 'grp_fall_back_turns')
        return None
    return queue.pop(0)


def _everyone(st: Fight, active: list, queue: list) -> list:
    """Every creature of the fight, the fallen too: the game keeps the dead
    in Game.monsters for the floor, so a band's 'half down' counts them."""
    seen = {id(m) for m in st.all}
    for m in active + queue:
        if id(m) not in seen:
            seen.add(id(m))
            st.all.append(m)
    return st.all


def deaths(run, active: list, queue: list) -> None:
    """The top of a turn: who fell since the last (or yielded, a captain),
    and the group's nerve answers (grp_morale)."""
    st = run.__dict__.get('_grp')
    if st is None or not on(run, 'grp_morale'):
        return
    everyone = _everyone(st, active, queue)
    for m in list(everyone):
        d = m.__dict__
        if d.get('_grp_answered'):
            continue
        lead_yield = d.get('_band_role') == 'leader' and d.get('_yielded')
        if m.alive and not lead_yield:
            continue
        d['_grp_answered'] = True
        if not m.alive:
            n = morale.kin_fell(everyone, m, st.g)
            if n:
                _fs(run, 'grp_kin_checks', n)
        if d.get('_band') and not d.get('_band_answered'):
            d['_band_answered'] = True
            out = war_bands.on_death(everyone, m)
            if out.get('effect'):
                _fs(run, 'grp_band_' + str(out['effect']))
            for f in out.get('fall') or ():
                if f.alive:
                    f.hp = 0
                    f.alive = False
                    f._band_answered = True
                    _fs(run, 'grp_crumbled')
    # A great blow on a living leader (war_bands.on_great_blow): this turn's
    # chain landed on him (his health fell with it).
    chain = int(run.quiz.chain_sum) - st.cs0
    st.cs0 = int(run.quiz.chain_sum)
    need = int(war_bands.data().get('nerve_chain', 6))
    for m in active:
        if m.__dict__.get('_band_role') != 'leader' or not m.alive:
            continue
        was = st.lead_hp.get(id(m), m.hp)
        if chain >= need and m.hp < was:
            if war_bands.on_great_blow(everyone, m, chain):
                _fs(run, 'grp_great_blows')
        st.lead_hp[id(m)] = m.hp


def arrival(run, m, free: int, opening: bool) -> int:
    """Its free blows as it comes in (fight.enter). A creature of speed 14+
    that closes from the fight's opening distance strikes on arrival only
    FAST_OPENING_BLOW of the time (its last double step must start two tiles
    off); stepping up from the queue behind the front, always. Ranged,
    lurkers, mimics and openers are enter()'s own rules."""
    if not on(run, 'grp_speed') or not free or not opening:
        return free
    pat = getattr(m, 'ai_pattern', '')
    if pat in ('ambush', 'mimic', 'ranged', 'summoner', 'healer', 'dragon'):
        return free
    if int(getattr(m, 'speed', 10) or 10) < FAST_SPEED:
        return free
    if random.random() < FAST_OPENING_BLOW:
        return free
    _fs(run, 'grp_fast_no_arrival')
    return 0


def ticks_now(run, w: int) -> bool:
    """The statuses tick on this world turn: the first of an action (the
    game ticks them once an action), or every one with grp_speed off."""
    return w == 0 or not on(run, 'grp_speed')


def tick_alone(run, n_world: int) -> bool:
    """An action the world waits out (a quick hero): the statuses still tick."""
    return on(run, 'grp_speed') and n_world == 0


def back_rank(run, active: list, queue: list, ctx, tick: bool = True, act: bool = True) -> list:
    """One world turn of the back rank: each of the queue whose knob is on
    takes its turn from where it stands (after the front's). Returns the
    queue (a summoner's dead join it)."""
    st = run.__dict__.get('_grp')
    if st is None or not queue or not any(on(run, k) for k in BACK_KNOBS + ('grp_orders',)):
        return queue
    p = run.p
    if (p.x, p.y) != HERO:
        return queue
    st.set_shape(len(active))
    _reseat(st, active)
    _place(st, active, queue)
    everyone = [m for m in active + queue if m.alive]
    if on(run, 'grp_orders') and st.band is not None and act:
        before = st.order
        _ask_order(run, st, everyone)
        if st.order == 'fall_back' and before != 'fall_back':
            _fs(run, 'grp_fall_back')
    if not any(on(run, k) for k in BACK_KNOBS):
        return queue
    for m in list(queue):
        if not m.alive or p.hp <= 0:
            continue
        r = role(m)
        if r is None or not on(run, r):
            continue
        if tick:
            run._tick_monster(m)
            if not m.alive:
                continue
        if not act:
            continue
        queue = _back_turn(run, st, m, active, queue, everyone, ctx)
    return queue


def _back_turn(run, st: Fight, m, active: list, queue: list, everyone: list, ctx) -> list:
    """One back-rank creature's turn."""
    p = run.p
    d = m.__dict__
    m._cached_all_monsters = everyone
    m._tracking = True
    n0 = len(everyone)
    d['_heal_target'] = None
    cast0 = sum((d.get('_spells_cast') or {}).values())
    chant0 = bool(d.get('_chanting'))
    got = run.monster_acts(m, ctx)       # the gates and the behaviours (AI-1, AI-3)
    if d.get('_heal_target') is not None:
        _fs(run, 'grp_heals')
    if sum((d.get('_spells_cast') or {}).values()) > cast0:
        _fs(run, 'grp_casts')
    if d.get('_chanting') and not chant0:
        _fs(run, 'grp_chants')
    if len(everyone) > n0:                # its dead came (sim_ai1._summon)
        new = everyone[n0:]
        i = queue.index(m) if m in queue else len(queue)
        queue = queue[:i] + new + queue[i:]
        _place(st, active, queue)
        _fs(run, 'grp_summons', len(new))
    d.pop('_ai_lines', None)
    if not got or p.hp <= 0:
        d.pop('_chosen_blow', None)
        return queue
    hero = (p.x, p.y)
    if d.get('_chosen_blow') is not None:
        # A spell its book drew up (a chanted bolt): it flies if it has a line.
        if m._has_clear_shot(hero[0], hero[1], st.g, everyone):
            _shot(run, m)
        else:
            d.pop('_chosen_blow', None)
        return queue
    if not _shoots_from_afar(m):
        return queue                      # it waits its turn at the doorway
    at = (m.x, m.y)
    shoot = m._ranged_turn(p, st.g, everyone, None)
    if _cheb(m.x, m.y, *hero) <= 1:
        m.x, m.y = at                     # never past the front: `engagers` is its size
        shoot = False
    if (m.x, m.y) != at:
        _fs(run, 'grp_lane_steps')
    if shoot and _cheb(m.x, m.y, *hero) >= 2:
        _shot(run, m)
    return queue


def _shot(run, m) -> None:
    """A shot from the back: the real Monster.attack from its tile."""
    p = run.p
    hp0 = p.hp
    run._monster_attack(m)
    m.__dict__.pop('_force_piercing', None)
    _fs(run, 'grp_shots')
    if p.hp < hp0:
        run.fs['grp_shot_dmg'] = run.fs.get('grp_shot_dmg', 0) + (hp0 - p.hp)

