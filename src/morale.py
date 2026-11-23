"""Morale by Nature: who breaks, how, and when (AI-1, morale_by_nature,
2026-11-19).

The old rule: every aggressive creature that was not a named foe AND had no
more than 500 health fled under a quarter of its health, for 8 turns, and
then fled again for as long as it stayed hurt (the timer re-armed itself).
So a zombie or a golem ran in terror of its wounds, a goblin on floor 2
broke, and about half of every ordinary kind from floor 21 down never did
(the 500 rule was depth by the back door). And a fleeing creature beside
the hero went on swinging.

Now each creature breaks the way its nature says (data/monster_ai.json
`morale`: its kind's own `morale_style` / `morale` in monsters.json, else
its family's, else the default; the mindless tags never):

  never     the restless dead, constructs, oozes, plants, elementals, the
            ghosts, the fanatics: they fight to the end;
  bolt      beasts, vermin, birds, serpents: it runs, and once its run is
            spent it has given up the fight (cowed: it keeps away from the
            hero for good, fighting only when he corners it);
  regroup   goblinkin, mortals: it runs for the nearest of its own side
            within reach, and reaching them rouses them all to the hero: he
            meets three goblins, not one (with none to run to, it withdraws);
  withdraw  giants, demons, dragons, the fair folk...: a fighting withdrawal
            for a few turns (it backs off a step at a time, and half the
            time a hero who presses it is struck as it goes), then back
            into the fight;
  yield     a bandit, a mercenary, a cult initiate: as regroup, but with no
            friend to run to and nowhere to go, it throws down its weapon
            and its purse and begs; it never strikes again (the hero may
            spare it or kill it: no karma either way).

When it breaks: a morale check (2d10 over its `morale` 0-20 breaks it) the
first time it falls under break_share (a quarter) of its health; again when
it is under half and one of its own falls within its sight; and when five
of its blows in a row land and do nothing (it cannot hurt the foe). One
check a trigger: it never re-arms itself. Healed above half it steadies.
A broken creature runs along a real path, away or to its friends; cornered
beside the hero, or caught and struck by him as it runs, it turns at bay for
a few turns (+2 to hit, no flight). A frightened one (``frightened_turn``)
runs the same way and turns at bay when cornered.

Each kind's own nerve (2026-11-22): its kind's ``morale`` in monsters.json
by its lore (an orc warrior or a bugbear holds, a rat breaks), and its kind's
``break_share`` where a wound tests it sooner or later (a jackal at half its
health). The Bestiary says it in one line (``bestiary_line``). When a war-
band's leader falls each follower tests here too (war_bands.leader_falls).

Kept as they were: the galla (fearless), a war-band follower while his
leader lives, a hyena that smells a wounded hero (packs 'harry'), the
thief with a haul, the stalker. Named foes never break (no HP test at all).
Pure module (the movement uses senses' paths); the simulator runs the same
checks (tools/balance/sim_ai1.py).
"""
from __future__ import annotations

import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai_morale knob (0 = the old rule)
STYLES = ('never', 'bolt', 'regroup', 'withdraw', 'yield')


def rules() -> dict:
    return kind_data.rules('morale')


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def nature(m) -> tuple:
    """(style, morale) of this creature."""
    r = rules()
    fam = getattr(m, 'family', None) or ''
    row = dict(r.get('default') or {'style': 'withdraw', 'morale': 10})
    row.update((r.get('families') or {}).get(fam) or {})
    if set(getattr(m, 'tags', None) or ()) & set(r.get('never_tags') or ()):
        row['style'] = 'never'
    if getattr(m, 'fearless', False) or 'feared' in (getattr(m, 'status_immune', None) or ()):
        row['style'] = 'never'
    style = kind_data.field(m, 'morale_style', row.get('style', 'withdraw'))
    try:
        import home_ground                   # on its own ground it never runs (AI-3)
        if home_ground.on_home(m):
            style = 'never'
    except ImportError:
        pass
    score = int(kind_data.field(m, 'morale', row.get('morale', 10)) or 0)
    if style not in STYLES:
        style = 'withdraw'
    return style, max(0, min(20, score))


def style(m) -> str:
    return nature(m)[0]


# The ways of fighting whose creatures keep a nerve to lose: every ordinary
# hunter (the archers, the hit-and-run, the summoners and healers, the
# dragons, a pack creature gone cowardly when alone). Not the rooted
# (sessile), a mimic or an ambusher still lying in wait, the stalker, or
# the bosses' own patterns.
RULED_PATTERNS = frozenset({'aggressive', 'cowardly', 'ranged', 'hit_and_run', 'summoner',
                            'healer', 'dragon', 'dancer'})
# What holds a creature where it is: one that has yielded does not even try
# to move away (and never strikes).
HELD = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'stuck_in_pit', 'impaled', 'immobilized')


def ruled(m) -> bool:
    """Morale is this creature's to keep (an ordinary hunter of no name)."""
    return (getattr(m, 'ai_pattern', '') in RULED_PATTERNS and not kind_data.named(m)
            and not kind_data.outside_rules(m))


def breaks(m, penalty: int = 0, rng=random) -> bool:
    """The morale check: 2d10 over its morale (less ``penalty``) breaks it."""
    _st, score = nature(m)
    return rng.randint(1, 10) + rng.randint(1, 10) > score - int(penalty)


def held_by_others(m, player) -> bool:
    """What keeps its nerve whatever its nature: a war-band follower while
    his leader lives; a hyena or gnoll that smells a wounded hero."""
    lead = m.__dict__.get('_band_leader')
    babbled = bool(getattr(m, 'has_effect', None) and m.has_effect('babbled'))
    if (lead is not None and getattr(lead, 'alive', False) and not babbled
            and not lead.__dict__.get('_yielded')):        # a captain who begs leads no one
        # A babbled follower cannot hear his captain (slice G, attack_gates).
        return True
    try:
        import packs
        if packs.has_trick(m, 'harry') and packs.wounded(player):
            return True
    except (ImportError, AttributeError):
        pass
    return False


def turn(m, player, monsters, rng=random) -> None:
    """One turn of its nerve (Monster.take_turn, where the old flee-when-hurt
    rule was): the flight counts down, the triggers are checked, and a
    creature that breaks starts its flight. State only; run() moves it."""
    if getattr(m, 'fearless', False):
        m._flee_timer = 0
        m.status_effects.pop('feared', None)
        return
    if not ruled(m):
        return
    if held_by_others(m, player):
        m._flee_timer = 0
        return
    d = m.__dict__
    r = rules()
    share = m.hp / max(1, m.max_hp)
    if share > float(r.get('courage_share', 0.5)):
        d.pop('_wound_checked', None)       # healed: it can break again later
    st, _score = nature(m)
    if st == 'never':
        m._flee_timer = 0
        if share < float(r.get('break_share', 0.25)) and ai_lines.once(m, 'never'):
            line = (r.get('never_lines') or {}).get(getattr(m, 'family', '') or '', '')
            if line:
                ai_lines.say(m, ai_lines.fill(m, line), '', 'info')
        d.pop('_morale_check', None)
        return
    if m._flee_timer > 0:
        m._flee_timer -= 1
        if share > float(r.get('courage_share', 0.5)):
            m._flee_timer = 0               # healed above half: it steadies
        if m._flee_timer <= 0:
            _flight_over(m)
        d.pop('_morale_check', None)
        return
    if d.get('_yielded') or d.get('_cowed'):
        return
    why = None
    pen = None
    if share < break_share(m) and not d.get('_wound_checked'):
        m._wound_checked = True
        why = 'wound'
    elif d.get('_morale_check'):
        why = d['_morale_check']
        pen = d.get('_morale_penalty')       # its band's own, when its leader fell
    d.pop('_morale_check', None)
    d.pop('_morale_penalty', None)
    if pen is None:
        pen = (r.get('penalty') or {}).get(why, 0)
    if why and breaks(m, int(pen or 0), rng):
        start_flight(m, player, monsters, rng)


def break_share(m) -> float:
    """The share of its health under which a wound tests its nerve: its
    kind's own ``break_share`` where its lore says otherwise (a jackal
    sooner, a berserker never), else the rule's quarter."""
    own = kind_data.field(m, 'break_share', None)
    try:
        return float(own) if own is not None else float(rules().get('break_share', 0.25))
    except (TypeError, ValueError):
        return float(rules().get('break_share', 0.25))


def start_flight(m, player, monsters, rng=random) -> None:
    r = rules()
    st = style(m)
    m._mo_hp = m.hp                          # a fresh wound from here on is a blow as it runs
    lines = r.get('lines') or {}
    unseen = r.get('unseen') or {}
    if st in ('regroup', 'yield'):
        kin = rally_kin(m, monsters, player)
        if kin is not None:
            m._rally_to = kin
            m._flee_timer = int(r.get('flee_turns', 8))
            ai_lines.say(m, ai_lines.fill(m, lines.get('regroup', '')), unseen.get('regroup', ''))
            return
        if st == 'yield':
            m._flee_timer = int(r.get('flee_turns', 8))
            m._yield_ready = True           # yields if it is caught (run)
            ai_lines.say(m, ai_lines.fill(m, lines.get('withdraw', '')), '')
            return
        st = 'withdraw'
    if st == 'bolt':
        lo, hi = r.get('bolt_turns', [8, 12])
        m._flee_timer = rng.randint(int(lo), int(hi))
        m._bolting = True
        ai_lines.say(m, ai_lines.fill(m, lines.get('bolt', '')), unseen.get('bolt', ''))
        return
    m._flee_timer = int(r.get('flee_turns', 8))
    ai_lines.say(m, ai_lines.fill(m, lines.get('withdraw', '')), '')


def _flight_over(m) -> None:
    d = m.__dict__
    d.pop('_rally_to', None)
    if d.pop('_bolting', None):
        m._cowed = True                      # it has given up the fight


def rally_kin(m, monsters, player):
    """The nearest of its own side to run to: alive, not running itself,
    within rally_reach, and no nearer the hero than it is."""
    import faction
    reach = int(rules().get('rally_reach', 12))
    mine = _cheb(m.x, m.y, player.x, player.y)
    best = None
    for o in monsters or ():
        if o is m or not faction.same_side(m, o):
            continue
        if int(getattr(o, '_flee_timer', 0) or 0) > 0 or o.__dict__.get('_yielded'):
            continue
        d = _cheb(m.x, m.y, o.x, o.y)
        if d > reach or _cheb(o.x, o.y, player.x, player.y) < mine:
            continue
        if best is None or d < best[0]:
            best = (d, o)
    return best[1] if best else None


def rally(m, kin, monsters, player) -> int:
    """It reached its friends: they are roused to the hero, and it comes
    back with them. Returns how many were roused."""
    import faction
    import senses
    near = int(rules().get('rally_rouse', 3))
    n = 0
    for o in monsters or ():
        if o is m or not faction.same_side(m, o):
            continue
        if _cheb(o.x, o.y, kin.x, kin.y) > near:
            continue
        if not o.__dict__.get('_tracking'):
            senses.rouse(o, player.x, player.y)
            n += 1
    m._flee_timer = 0
    m.__dict__.pop('_rally_to', None)
    m._rallied = True
    ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('rally', '')), '')
    return n


def _free(m, dungeon, monsters, extra_occupied, player):
    from geom import all_occupied_tiles
    occ = set(all_occupied_tiles(monsters or [], exclude=m))
    if extra_occupied:
        occ |= set(extra_occupied)
    occ.add((player.x, player.y))
    return occ


def flee_away(m, player, dungeon, monsters, extra_occupied) -> bool:
    """One step along the longest free way from the hero (a short search of
    the ground about it, not the greedy step that walked into dead ends).
    True if it moved."""
    from collections import deque
    occ = _free(m, dungeon, monsters, extra_occupied, player)
    start = (m.x, m.y)
    prev = {start: None}
    q = deque([(start, 0)])
    best = (_cheb(m.x, m.y, player.x, player.y), 0, start)
    depth = int(rules().get('flee_search', 6))
    while q:
        cur, dd = q.popleft()
        if dd >= depth:
            continue
        cx, cy = cur
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if not ox and not oy:
                    continue
                nxt = (cx + ox, cy + oy)
                if nxt in prev or nxt in occ:
                    continue
                if not m._can_move_to(dungeon, *nxt):
                    continue
                prev[nxt] = cur
                q.append((nxt, dd + 1))
                key = (_cheb(nxt[0], nxt[1], player.x, player.y), -(dd + 1), nxt)
                if key > best:
                    best = key
    goal = best[2]
    if goal == start or best[0] <= _cheb(m.x, m.y, player.x, player.y):
        return False
    step = goal
    while prev.get(step) is not None and prev[step] != start:
        step = prev[step]
    m.x, m.y = step
    return True


def run(m, player, dungeon, monsters, extra_occupied):
    """A broken creature's move (Monster.take_turn, before it hunts): True
    (it strikes: at bay, cornered), False (it ran, or holds), None (not
    broken: the hunt goes on)."""
    if not ENABLED:
        return None
    d = m.__dict__
    if d.get('_yielded'):
        return yielded_turn(m, player, dungeon, monsters, extra_occupied)
    if not ruled(m):
        return None
    bay = int(d.get('_at_bay', 0) or 0)
    if bay > 0:
        m._at_bay = bay - 1
        if m._adjacent_to(player):
            return True
        m._at_bay = 0
    if d.get('_cowed') and int(getattr(m, '_flee_timer', 0) or 0) <= 0:
        return cowed_turn(m, player, dungeon, monsters, extra_occupied)
    if int(getattr(m, '_flee_timer', 0) or 0) <= 0:
        return None
    # Caught and struck as it runs (the hero beside it, its wound fresh):
    # it turns at bay rather than take blow after blow in the back; one
    # that would yield begs instead.
    hp_was = d.get('_mo_hp')
    m._mo_hp = m.hp
    if hp_was is not None and m.hp < int(hp_was) and m._adjacent_to(player):
        if d.pop('_yield_ready', None):
            give_up(m)
            return False
        return turn_at_bay(m)
    kin = d.get('_rally_to')
    if kin is not None:
        if not getattr(kin, 'alive', False):
            d.pop('_rally_to', None)
        elif _cheb(m.x, m.y, kin.x, kin.y) <= 1:
            rally(m, kin, monsters, player)
            return None                       # back in the fight, this turn
        else:
            import senses
            if senses.step_toward(m, dungeon, (kin.x, kin.y), monsters, extra_occupied, player):
                return False
    if (m._adjacent_to(player) and style(m) == 'withdraw'
            and random.random() < withdraw_strikes()):
        return True                           # a fighting withdrawal: it strikes
    if flee_away(m, player, dungeon, monsters, extra_occupied):
        return False
    if not m._adjacent_to(player):
        return False                          # nowhere better: it holds
    if d.pop('_yield_ready', None):
        give_up(m)
        return False
    return turn_at_bay(m)


def turn_at_bay(m) -> bool:
    """Cornered or caught: it turns at bay for at_bay_turns turns (better
    to hit, no flight). True: it strikes now."""
    r = rules()
    d = m.__dict__
    m._at_bay = int(r.get('at_bay_turns', 3))
    m._flee_timer = 0
    d.pop('_rally_to', None)
    if ai_lines.once(m, 'at_bay'):
        ai_lines.say(m, ai_lines.fill(m, (r.get('lines') or {}).get('at_bay', '')), '')
    return True


def frightened_turn(m, player, dungeon, monsters, extra_occupied) -> bool:
    """A frightened creature's turn (feared: a spell, a scroll, fire, a
    band's nerve gone): it runs along a real way from the hero, the old
    straight step only where there is none; cornered beside him, it turns
    at bay and strikes (it used to cower there and take every blow). True
    when it strikes."""
    d = m.__dict__
    if int(d.get('_at_bay', 0) or 0) > 0:
        m._at_bay = int(d['_at_bay']) - 1
        if m._adjacent_to(player):
            return True
        m._at_bay = 0
    if flee_away(m, player, dungeon, monsters, extra_occupied):
        return False
    before = (m.x, m.y)
    flee = getattr(m, '_flee_from', None)
    if flee is not None:
        flee(player, dungeon, monsters, extra_occupied)
    if (m.x, m.y) != before or not m._adjacent_to(player):
        return False
    return turn_at_bay(m)


def withdraw_strikes() -> float:
    """How often a withdrawing creature strikes the hero who presses it."""
    return float(rules().get('withdraw_strikes', 0.5))


def give_up(m) -> None:
    """It yields: it throws down its weapon and its purse and begs. It never
    strikes again; the Game drops the purse (BehaviourMixin)."""
    m._yielded = True
    m._flee_timer = 0
    m._wants_purse_dropped = True
    ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('yield', '')), '', 'info')


def _sees(m, player, dungeon) -> bool:
    try:
        import senses
        reach = int(getattr(m, 'perception_range', 8) or 8)
        return (_cheb(m.x, m.y, player.x, player.y) <= reach
                and senses.clear_view(m.x, m.y, player.x, player.y, dungeon))
    except (ImportError, AttributeError):
        return False


def yielded_turn(m, player, dungeon, monsters, extra_occupied) -> bool:
    """A creature that yielded keeps out of the hero's way and never
    strikes (Monster.take_turn, at the top of its turn: always False).
    Held (a pit, a spear, a web, asleep), it stays where it is."""
    has = getattr(m, 'has_effect', None)
    if has is not None and any(has(e) for e in HELD):
        return False
    if _sees(m, player, dungeon):
        flee_away(m, player, dungeon, monsters, extra_occupied)
    return False


def cowed_turn(m, player, dungeon, monsters, extra_occupied) -> bool:
    """A beast that bolted has given up the fight: it keeps away from a
    hero it can see, goes about its business when it cannot, and fights
    only when he corners it."""
    if not _sees(m, player, dungeon):
        try:
            import senses
            m._tracking = False
            senses.idle(m, player, dungeon, monsters, extra_occupied)
        except (ImportError, AttributeError):
            pass
        return False
    if flee_away(m, player, dungeon, monsters, extra_occupied):
        return False
    return bool(m._adjacent_to(player))


def at_bay_hit(m) -> int:
    """To-hit it gains, at bay (ai_blow.to_hit_shift: lower is better)."""
    if int(m.__dict__.get('_at_bay', 0) or 0) > 0:
        return -int(rules().get('at_bay_hit', 2))
    return 0


def kin_fell(monsters, dead, dungeon=None) -> int:
    """One of its own fell within its sight: each hurt creature of its side
    that saw it takes a check on its next turn. Returns how many."""
    if not ENABLED:
        return 0
    import faction
    reach = int(rules().get('kin_sight', 8))
    n = 0
    for o in monsters or ():
        if o is dead or not getattr(o, 'alive', False) or not ruled(o):
            continue
        if not faction.same_side(o, dead) and getattr(o, 'kind', None) != getattr(dead, 'kind', None):
            continue
        if _cheb(o.x, o.y, dead.x, dead.y) > reach:
            continue
        if o.hp >= o.max_hp * float(rules().get('courage_share', 0.5)):
            continue
        if dungeon is not None:
            try:
                import senses
                if not senses.clear_view(o.x, o.y, dead.x, dead.y, dungeon):
                    continue
            except (ImportError, AttributeError):
                pass
        o._morale_check = 'kin'
        n += 1
    return n


def tell_keys(m) -> list:
    """Its tells (data/tells.json): one that runs for its friends."""
    try:
        if ruled(m) and style(m) == 'regroup':
            return ['regroups']
    except (AttributeError, TypeError):
        pass
    return []


def bestiary_line(kind) -> str:
    """The Bestiary's one line of a kind's nerve: its morale in a word and
    how it breaks ('' for one that never does: the Fearless line says it)."""
    import kind_data as _kd

    class _K:
        pass
    k = _K()
    k.kind = str(kind or '')
    kd = _kd.kind_def(k)
    k.family = kd.get('family')
    k.tags = kd.get('tags') or ()
    k.fearless = bool(kd.get('fearless'))
    k.status_immune = kd.get('status_immune') or ()
    k.ai_pattern = kd.get('ai_pattern', '')
    k.is_boss = kd.get('is_boss')
    k.is_mini_boss = kd.get('is_mini_boss')
    if not ruled(k):
        return ''
    st, score = nature(k)
    b = rules().get('bestiary') or {}
    words = (b.get('styles') or {}).get(st, '')
    if not words:
        return ''
    if score >= int(b.get('steady_at', 15)):
        lead = b.get('steady', '')
    elif score <= int(b.get('shaky_at', 8)):
        lead = b.get('shaky', '')
    else:
        lead = b.get('nerve', '')
    return ' '.join(p for p in (lead, words) if p)


def futile_blow(m, landed_for: int) -> None:
    """A blow of its landed (ai_blow.after_blow): five in a row that do
    nothing is a check (it cannot hurt the foe)."""
    if not ENABLED or not ruled(m):
        return
    if landed_for > 0:
        m.__dict__.pop('_zero_hits', None)
        return
    n = int(m.__dict__.get('_zero_hits', 0) or 0) + 1
    if n >= int(rules().get('futile_blows', 5)):
        m._morale_check = 'futile'
        n = 0
    m._zero_hits = n
