"""Held Fast: constrict, swallow, drag under, one hold with three faces
(monster behaviour, third wave: AI-3, held_fast, 2026-11-20).

A python's coils, a gelatinous cube or a taniwha taking a man inside, a
kelpie or Grendel's mother dragging him down to the water: an attack with
``hold`` (data/monsters.json, on the attack)

    {"kind": "constrict" | "swallow" | "drag", "type": its damage type,
     "break_share": 0.10, "max_turns": 4, "save": "STR" | "DEX"}

that lands and that the hero fails to slip (a DEX save, the status
``held``: HARD control, so its cap, 4 turns, and its grace hold) takes
hold of him:

* He cannot walk away. Trying to is a struggle: a STR or DEX check (the
  hold's ``save``) against the holder's grip; won, he twists free.
* The holder does nothing else: each of its turns it squeezes, digests or
  drags, for its hold attack's own dice, typed, with no roll to hit (it is
  wrapped round him already). A drag pulls him a tile toward the nearest
  water and, at the water's edge, under it.
* Swallowed, he is out of every other creature's reach (they cannot strike
  what is inside another) and they are out of his (shields, strikable: no
  blow, shot, throw, spell, wand, scroll or power of his lands outside; a
  pet's does, it is outside), and every way he turns is its gut.
* The way out is the hero's own: a blow (a maths chain, a spell, a wand, a
  flask, a pet's bite) that takes ``break_share`` of the holder's health
  between two of its turns breaks the coil or cuts him out; the struggle;
  the holder dying, sleeping, held, frightened or broken; Loosed
  (free_action: the Galdr of Loosing), the Coif of Beowulf and a family
  ward against its holds (the Psylli's charm against a serpent: no hold
  takes him, and one read while held lets him go); and at the
  last the ``held`` status running out (max_turns, at most 4). After any of
  them he is Recovering (control_immune, GRACE_TURNS): no hold at once again.
* A floor change, a teleport, a shove or a pull that parts them ends it.

The holder is remembered by its uid (never the object: a floor's monsters
are pickled with the floor), so a save in the middle of a hold loads, and a
holder that is gone on load lets go. Named foes get no hold in this pass;
the allied, the encounter people, the unicorn, Death and the stalker never
hold. Pure module: the Game's side is game_monster_ways.py, the simulator's
tools/balance/sim_ai3.py.
"""
from __future__ import annotations

import random
import uuid

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_hold knob (0 = no holds, as before)
KINDS = ('constrict', 'swallow', 'drag')
STATUS = 'held'


def rules() -> dict:
    return kind_data.rules('holds')


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def uid(m) -> str:
    """This creature's own id (given the first time it is asked for)."""
    u = m.__dict__.get('_uid')
    if not u:
        u = uuid.uuid4().hex[:12]
        m.__dict__['_uid'] = u
    return u


def spec_of(atk) -> dict | None:
    h = (atk or {}).get('hold') if isinstance(atk, dict) else None
    if isinstance(h, dict) and h.get('kind') in KINDS:
        return h
    return None


def hold_attacks(m) -> list:
    return [a for a in getattr(m, 'attacks', None) or () if spec_of(a)]


def state(player) -> dict | None:
    st = getattr(player, '__dict__', {}).get('_held')
    return st if isinstance(st, dict) else None


def is_held(player) -> bool:
    return state(player) is not None


def kind(player) -> str:
    st = state(player)
    return str(st.get('kind', '')) if st else ''


def swallowed(player) -> bool:
    return kind(player) == 'swallow'


def holder(player, monsters):
    """The creature that holds the hero, among ``monsters``, or None."""
    st = state(player)
    if not st:
        return None
    for m in monsters or ():
        if getattr(m, '__dict__', {}).get('_uid') == st.get('uid'):
            return m
    return None


def is_holder(m, player) -> bool:
    st = state(player)
    return bool(st) and getattr(m, '__dict__', {}).get('_uid') == st.get('uid')


def _ruled(m) -> bool:
    return bool(ENABLED and not kind_data.named(m) and not kind_data.outside_rules(m)
                and not getattr(m, '_is_summoned_image', False))


def _the(m) -> str:
    from monster import the_name
    return the_name(m, lower=True)


def _line(key: str, m, hk: str = '', **kw) -> str:
    lines = rules().get('lines') or {}
    text = lines.get(f'{key}_{hk}') or lines.get(key, '')
    return ai_lines.fill(m, text, **kw)


def loosed_line(player) -> str:
    """What keeps the hero from being held, or '' (Loosed: free_action;
    the Coif of Beowulf's Grendel-grip)."""
    try:
        if player.has_effect('free_action'):
            return 'loosed'
    except AttributeError:
        pass
    try:
        from armor_procs import player_has_armor_proc
        if player_has_armor_proc(player, 'grendel_grip'):
            return 'grendel'
    except ImportError:
        pass
    return ''


def ward_line(player, m) -> str:
    """A family ward that keeps ``m``'s holds off the hero (the Psylli's
    against a serpent: wards.rider_line for the rider 'held'), its line;
    else ''."""
    if m is None:
        return ''
    try:
        import wards
        return wards.rider_line(player, m, STATUS) or ''
    except Exception:
        return ''


# ---------------------------------------------------------------------------
# Taking hold (ai_blow.after_blow: after the blow landed)
# ---------------------------------------------------------------------------

def after_blow(m, player, atk, actual: int, msg: str) -> str:
    spec = spec_of(atk)
    if spec is None or actual <= 0 or not _ruled(m) or not getattr(m, 'alive', False):
        return msg
    if not m._adjacent_to(player) or getattr(player, 'hp', 0) <= 0:
        return msg
    got = start(m, player, atk, spec)
    return (msg + ' ' + got) if got else msg


def start(m, player, atk, spec, rng=random) -> str:
    """The hold takes the hero, or does not. The line, or ''."""
    hk = spec['kind']
    if is_held(player):
        return ''                          # one holder at a time
    why = loosed_line(player)
    if why:
        return _line('loosed_' + why, m, hk)
    warded = ward_line(player, m)
    if warded:
        return warded                      # a family ward keeps its holds off (the Psylli)
    if int(getattr(player, 'status_effects', {}).get('control_immune', 0) or 0) > 0:
        return ''                          # steadying after a hold: it finds no grip
    from status_effects import apply_debuff_with_save
    turns = max(1, min(4, int(spec.get('max_turns', 4) or 4)))
    dc = min(18, int(spec.get('save_dc', 12 + int(getattr(m, 'min_level', 1) or 1) // 7)))
    applied, text = apply_debuff_with_save(player, STATUS, turns, dc, source=m)
    if not applied:
        return text or ''
    player.__dict__['_held'] = {
        'uid': uid(m), 'kind': hk, 'attack': str(atk.get('name', '')),
        'type': str(spec.get('type') or atk.get('type') or 'physical'),
        'break_share': float(spec.get('break_share', rules().get('break_share', 0.10)) or 0.10),
        'save': str(spec.get('save', 'STR') or 'STR'),
        'dc': dc, 'name': _the(m), 'turns': 0,
    }
    m.__dict__['_holding'] = True
    m.__dict__['_hold_hurt'] = 0
    counts = dict(m.__dict__.get('_holds_made') or {})
    counts[hk] = counts.get(hk, 0) + 1
    m._holds_made = counts
    return _line('start', m, hk)


# ---------------------------------------------------------------------------
# Letting go
# ---------------------------------------------------------------------------

def release(player, m=None, why: str = '') -> str:
    """The hold ends. Returns its line ('' for a silent end). The hero is
    Recovering for GRACE_TURNS (no hold at once again)."""
    st = state(player)
    if st is None:
        if m is not None:
            m.__dict__.pop('_holding', None)
        return ''
    hk = st.get('kind', '')
    player.__dict__.pop('_held', None)
    se = player.status_effects
    had = int(se.get(STATUS, 0) or 0) > 0
    se.pop(STATUS, None)
    if m is not None:
        m.__dict__.pop('_holding', None)
        m.__dict__.pop('_hold_hurt', None)
    if why != 'floor':
        try:
            from status_effects import GRACE_TURNS
        except ImportError:
            GRACE_TURNS = 3
        cur = se.get('control_immune', 0)
        if cur != -1:
            se['control_immune'] = max(int(cur or 0), GRACE_TURNS)
    if why in ('', 'floor', 'expired') or (why == 'expired' and not had):
        return ''
    name = st.get('name') or 'it'
    text = (rules().get('lines') or {}).get(f'free_{why}_{hk}') or \
        (rules().get('lines') or {}).get(f'free_{why}', '')
    if m is not None:
        return ai_lines.fill(m, text)
    return ai_lines.fill(None, text.replace('{the}', name).replace('{The}', name[:1].upper() + name[1:]))


def broken_reason(m, player) -> str:
    """Why the holder can no longer hold, or ''."""
    if m is None or not getattr(m, 'alive', False):
        return 'dead'
    if not m._adjacent_to(player):
        return 'apart'
    if (m.has_effect('sleeping') or m.has_effect('paralyzed') or m.has_effect('stunned')
            or m.has_effect('frozen') or m.has_effect('petrifying')):
        return 'held'
    if m._under('feared') or m._under('charmed'):
        return 'scared'
    d = m.__dict__
    if int(getattr(m, '_flee_timer', 0) or 0) > 0 or d.get('_yielded') or d.get('_cowed'):
        return 'scared'
    st = state(player) or {}
    share = float(st.get('break_share', 0.10) or 0.10)
    if int(d.get('_hold_hurt', 0) or 0) >= max(1, int(m.max_hp * share)):
        return 'cut'
    return ''


def validate(player, monsters) -> str:
    """Check the hold still stands (the hero's move, the monsters' turn, a
    load): a holder gone, parted, hurt enough, asleep or frightened, the
    hero Loosed, or the status run out, ends it. Returns the line ('')."""
    st = state(player)
    if st is None:
        return ''
    m = holder(player, monsters)
    if int((getattr(player, 'status_effects', None) or {}).get(STATUS, 0) or 0) <= 0:
        return release(player, m, 'expired')
    why = loosed_line(player)
    if why:
        return release(player, m, why)
    if ward_line(player, m):
        return release(player, m, 'warded')    # a ward read while held (the Psylli)
    why = broken_reason(m, player)
    if why:
        return release(player, m, why)
    return ''


def note_hurt(m, actual: int) -> None:
    """A blow on the holder (Monster.take_damage; never a wound's tick): it
    counts toward the hero's way out."""
    if actual > 0 and m.__dict__.get('_holding'):
        m.__dict__['_hold_hurt'] = int(m.__dict__.get('_hold_hurt', 0) or 0) + int(actual)


# ---------------------------------------------------------------------------
# The hero's struggle (Game._do_move while held)
# ---------------------------------------------------------------------------

def struggle(player, m, rng=random) -> tuple:
    """(freed, line): STR or DEX (the hold's ``save``) against its grip."""
    st = state(player) or {}
    stat = 'DEX' if str(st.get('save', 'STR')) == 'DEX' else 'STR'
    mod = (int(getattr(player, stat, 10) or 10) - 10) // 2
    try:
        bonus = int(player.save_bonus_for('DEX')) if stat == 'DEX' else 0
    except (AttributeError, TypeError):
        bonus = 0
    hk = st.get('kind', '')
    dc = int(st.get('dc', 13) or 13) + int(rules().get('struggle_dc_add', 0) or 0)
    if rng.randint(1, 20) + mod + bonus >= dc:
        return True, release(player, m, 'struggle')
    lines = rules().get('lines') or {}
    text = lines.get(f'struggle_fail_{hk}') or lines.get('struggle_fail', '')
    return False, (ai_lines.fill(m, text) if m is not None else text)


# ---------------------------------------------------------------------------
# The holder's turn (src/ai_turn.py) and its squeeze (Monster.attack)
# ---------------------------------------------------------------------------

def holder_turn(m, player, dungeon, monsters, extra_occupied):
    """True (it squeezes: Monster.attack takes blow()), or None (it holds
    nobody, or the hold has ended: its own turn goes on)."""
    if not m.__dict__.get('_holding'):
        return None
    if not is_holder(m, player):
        m.__dict__.pop('_holding', None)
        return None
    why = loosed_line(player) or broken_reason(m, player)
    if why:
        line = release(player, m, why)
        if line:
            ai_lines.say(m, line, line, 'success')
        return None
    st = state(player)
    if st.get('kind') == 'drag' and dungeon is not None:
        _drag_step(m, player, dungeon, monsters, extra_occupied)
    m._squeeze_now = True
    return True


def _water_goal(dungeon, x, y, reach: int):
    """The nearest water tile within ``reach`` (a short search), or None."""
    from collections import deque
    is_water = getattr(dungeon, 'is_water', None)
    if is_water is None:
        return None
    seen = {(x, y)}
    q = deque([(x, y, 0)])
    while q:
        cx, cy, d = q.popleft()
        if d > reach:
            continue
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                nx, ny = cx + ox, cy + oy
                if (nx, ny) in seen or not dungeon.in_bounds(nx, ny):
                    continue
                seen.add((nx, ny))
                if is_water(nx, ny):
                    return (nx, ny)
                if dungeon.is_walkable(nx, ny):
                    q.append((nx, ny, d + 1))
    return None


def at_water(dungeon, x, y) -> bool:
    is_water = getattr(dungeon, 'is_water', None)
    if dungeon is None or is_water is None:
        return False
    return any(is_water(x + ox, y + oy) for ox in (-1, 0, 1) for oy in (-1, 0, 1)
               if (ox or oy) and dungeon.in_bounds(x + ox, y + oy))


def _safe_for_hero(dungeon, x, y) -> bool:
    """Never onto lava, a pit, a trap or a hazard the hero would step on."""
    if not dungeon.is_walkable(x, y):
        return False
    if (x, y) in (getattr(dungeon, 'pits', None) or ()):
        return False
    if (x, y) in (getattr(dungeon, 'traps', None) or {}):
        return False
    try:
        import hazards
        if hazards.hazard_at(dungeon, x, y):
            return False
    except (ImportError, AttributeError):
        pass
    return True


def _drag_step(m, player, dungeon, monsters, extra_occupied) -> bool:
    """One tile toward the water: the holder steps, the hero is hauled into
    the tile it left. Never when he is at the edge already (then it drags
    him under), never onto a hazard. True if they moved."""
    if at_water(dungeon, m.x, m.y) or at_water(dungeon, player.x, player.y):
        m._dragged_under = True            # at the edge: it goes in and takes him under
        return False
    goal = _water_goal(dungeon, m.x, m.y, int(rules().get('drag_reach', 10) or 10))
    if goal is None:
        return False
    ox, oy = m.x, m.y
    if not _safe_for_hero(dungeon, ox, oy):
        return False
    import senses
    if not senses.step_toward(m, dungeon, goal, monsters, extra_occupied, player):
        return False
    if (m.x, m.y) == (ox, oy) or (m.x, m.y) == (player.x, player.y):
        m.x, m.y = ox, oy
        return False
    player.x, player.y = ox, oy
    m._dragged = True
    return True


def blow(m, player):
    """The squeeze, the gut or the drowning, for the hold attack's own
    dice (Monster.attack, when take_turn chose it): (damage, line), or None."""
    if not m.__dict__.pop('_squeeze_now', False):
        return None
    st = state(player)
    if not st or not is_holder(m, player):
        return None
    atk = next((a for a in getattr(m, 'attacks', None) or () if a.get('name') == st.get('attack')),
               None) or (hold_attacks(m) or [None])[0]
    if atk is None:
        return None
    import monster as _mon
    _a, stop = _mon._ward_gate(player, m, atk)   # sanctuary, Styx-dipped (wards.py)
    if stop is not None:
        return stop
    from dice import roll
    hk = st.get('kind', '')
    dtype = st.get('type') or 'physical'
    dmg = max(1, roll(str(atk.get('damage', '1d4'))))
    under = bool(m.__dict__.pop('_dragged_under', False))
    dragged = bool(m.__dict__.pop('_dragged', False))
    if under:
        dmg = max(1, int(round(dmg * float(rules().get('drown_mult', 1.5) or 1.5))))
    if m.has_effect('weakened'):
        dmg = max(1, dmg // 2)
    dmg = _mon._edge_incoming(player, m, dmg, dtype)
    actual = player.take_damage(dmg, dtype)
    st['turns'] = int(st.get('turns', 0) or 0) + 1
    m.__dict__['_hold_hurt'] = 0           # a fresh turn: cut again to get out
    key = 'under' if under else ('drag' if dragged else 'squeeze')
    return actual, _line(key, m, hk, damage=actual)


def shields(player, m) -> bool:
    """A swallowed hero cannot be struck by anything but what holds him,
    nor strike anything else."""
    return swallowed(player) and not is_holder(m, player)


def strikable(player, monsters):
    """Those of ``monsters`` the hero's blows can land on: all of them (the
    list itself), or, swallowed, only what holds him."""
    if not swallowed(player):
        return monsters
    return [m for m in monsters or () if is_holder(m, player)]


def aim_refused(player, m, monsters) -> str:
    """'' when the hero may strike ``m``; else the line that says why not."""
    if m is None or not shields(player, m):
        return ''
    return inside_line(player, monsters)


def inside_line(player, monsters) -> str:
    """What a swallowed hero is told of a blow aimed past the gut."""
    if not swallowed(player):
        return ''
    h = holder(player, monsters)
    if h is not None:
        return _line('swallowed_aim', h)
    text = (rules().get('lines') or {}).get('swallowed_aim', '')
    return text.replace('{the}', str(state(player).get('name') or 'it')).replace('{him}', 'it')


def tell_keys(m) -> list:
    out = []
    for a in hold_attacks(m):
        k = 'hold_' + spec_of(a)['kind']
        if k not in out:
            out.append(k)
    return out
