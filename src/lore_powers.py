"""Lore powers of the MONSTERS AND MAGIC kinds (2026-11-19, slice M).

Each power is the creature's own, from its lore, written as data on the kind
in data/monsters.json (tools/content/mm_kinds_data.py has the why), and each
says one plain line when it fires:

* ``countdown_voice`` -- the Cu-Sith barks three times while the hero is in
  its sight, one bark every few of its turns; the third is its attack
  (a voice: wax stops its rider). Out of its sight (a wall, a corner) the
  count is lost: the Highlanders' shelter.
* ``metal_eater`` -- the Bulgasari eats iron: a blade that can rust (iron or
  steel; never a unique) and lands on it may lose a point to its hide, and
  every mouthful mends it, its body growing up to ``grow_cap`` beyond its
  health.
* ``weak_spot_chain`` -- the Mapinguari's hide turns weak blows; a maths
  chain of that length finds the soft place, and the blow ignores its
  resistances.
* ``sheds_skin`` -- the Lindworm sheds a skin at each share of its health in
  ``at``: its wounds' effects come away and it mends ``heal_share``.
* ``on_stunned`` -- knock the Kappa senseless and the water spills from its
  dish: it is weakened for ``turns``.
* ``blinded_loses`` -- Likho blinded cannot use the attacks named (her eye).
* ``appeased_by`` -- a gift of plain food quiets the Kappa and the Preta for
  the floor (the game sets ``_lp_calm``: game_lore_powers.py); struck, the
  deal is off.
* ``parley`` -- the Blue Men wait for an answer (game_lore_powers.py asks
  it); calling it is their first turn of noticing him (calls), and while
  they wait they hold their fire (at_peace: no blow on the hero, a pet or
  an escort, pinned or free, and no pet goes for them unbidden).
* ``gold_gatherer`` -- a gold-digging ant stops to gather gold the hero
  drops near it, no other (``_lp_busy`` turns: game_lore_powers.py).
* attack ``carry_off`` -- the Roc lifts the hero and drops him far away
  (the game moves him: game_lore_powers.py); a Heavy or Burdened load halves
  the chance, as a heavy man is hard to lift.
* attack ``pulls`` -- the Yacumama's breath draws the hero a step toward it
  (the pull the game already resolves: player._pending_pull_toward).
* ``hidden_overhead`` -- the Asanbosam and the star jelly hang above; a lit
  light shows them within its glow (unseen.senses asks ``shown_overhead``).

Lines go to OUTBOX; the game says them (game_lore_powers.py) and the
simulator never reads them. ``ENABLED`` is the simulator's ablation knob
(tools/balance/difficulty_sim.py ``mm_powers``). Pure: no pygame, no Game.
Every per-creature count is a plain number in the monster's own __dict__
(the simulator shallow-copies monsters); an old save's monster has none and
starts at zero.
"""
from __future__ import annotations

import json
import random

ENABLED = True
OUTBOX: list = []
_OUTBOX_CAP = 40
_DEFS: dict | None = None

# What a shed skin takes with it: the wounds, not a hold.
SHED_EFFECTS = ('bleeding', 'poisoned', 'burning', 'corroding', 'diseased', 'armor_crack',
                'sundered', 'deep_wound', 'ruptured', 'impaled', 'weakened', 'heal_blocked',
                'doom_dot', 'slowed')


def _defs() -> dict:
    global _DEFS
    if _DEFS is None:
        try:
            from paths import data_path
            with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
                _DEFS = json.load(f)
        except (OSError, ValueError, ImportError):
            _DEFS = {}
    return _DEFS


def spec(m, key: str, default=None):
    """The kind's own `key` (data/monsters.json), or `default`."""
    d = _defs().get(str(getattr(m, 'kind', '') or ''))
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def say(text: str, kind: str = 'warning', m=None, unseen: str | None = None) -> None:
    """A line for the game to say; with `m`, `unseen` is said instead when
    the hero cannot see the creature (None: nothing)."""
    if text and len(OUTBOX) < _OUTBOX_CAP:
        OUTBOX.append((text, kind, m, unseen))


def drain() -> list:
    """The lines waiting to be said, and none left."""
    out = list(OUTBOX)
    OUTBOX.clear()
    return out


def _fill(m, text: str) -> str:
    try:
        from monster import fill
        return fill(m, text)
    except Exception:
        return text


def _in_sight(m, player, dungeon) -> bool:
    """The creature can see the hero now (no dungeon: the simulator's fight,
    where it always can)."""
    if dungeon is None:
        return True
    d = max(abs(m.x - player.x), abs(m.y - player.y))
    if d > int(getattr(m, 'perception_range', 8) or 8):
        return False
    if d <= 1:
        return True
    import senses
    return senses.clear_view(m.x, m.y, player.x, player.y, dungeon)


# ---------------------------------------------------------------------------
# Peace: what every blow a creature strikes, and every blow that goes at it
# unbidden, asks first.
# ---------------------------------------------------------------------------
def holds_fire(m) -> bool:
    """Fed or answered, or waiting for an answer: it strikes no one."""
    d = getattr(m, '__dict__', {})
    return bool(ENABLED and (d.get('_lp_calm') or d.get('_lp_parley') == 'waiting'))


def gathering(m) -> bool:
    """Stopped for gold: it has no blow to spare (not a peace)."""
    return bool(ENABLED and int(getattr(m, '__dict__', {}).get('_lp_busy', 0) or 0) > 0)


def at_peace(m) -> bool:
    """No one left to himself (a pet, a horn's ally, boots that throw
    lightning) breaks this peace: one that holds its fire, has yielded
    (src/morale.py), or was bought or sung to a peace a blow breaks (the
    Bribe, a family's calm, the Song of Settled Strife). The hero's own
    blow, or a special he orders, still may."""
    d = getattr(m, '__dict__', {})
    if d.get('_yielded') or holds_fire(m):
        return True
    return bool((d.get('_bribed') or d.get('_strife_peace'))
                and int((getattr(m, 'status_effects', None) or {}).get('charmed', 0) or 0) > 0)


# ---------------------------------------------------------------------------
# The parley's call
# ---------------------------------------------------------------------------
PARLEY_GROUP = 10        # those this near call, wait and answer as one


def parley_group(m, monsters) -> list:
    return [o for o in monsters or ()
            if getattr(o, 'alive', False) and o.kind == m.kind
            and max(abs(o.x - m.x), abs(o.y - m.y)) <= PARLEY_GROUP]


def calls(m, player, dungeon, monsters) -> bool:
    """It has just noticed the hero (Monster._spots_player): one of a parley
    kind that has him in sight and has never called spends this turn calling
    (the game says the verse). Not one with no voice, nor one whose fellows
    are angry already."""
    d = m.__dict__
    if (not ENABLED or dungeon is None or d.get('_lp_parley') is not None or d.get('_lp_call')
            or not spec(m, 'parley')):
        return False                      # (a call the game has yet to say is one turn, not more)
    if m.has_effect('silenced') or not _in_sight(m, player, dungeon):
        return False
    if any(o.__dict__.get('_lp_parley') == 'angry' for o in parley_group(m, monsters)):
        d['_lp_parley'] = 'angry'
        return False
    return True


# ---------------------------------------------------------------------------
# The creature's turn (Monster.take_turn): None to go on as usual, True when
# it attacks now (attack() takes ``_opener_now``), False when it spends the
# turn.
# ---------------------------------------------------------------------------
def turn(m, player, dungeon, all_monsters=None, extra_occupied=None):
    if not ENABLED:
        return None
    d = m.__dict__
    if d.get('_lp_calm'):
        # Fed or answered: it keeps to itself for the floor.
        try:
            m._wander(dungeon, all_monsters or [], extra_occupied, player)
        except Exception:
            pass
        return False
    busy = int(d.get('_lp_busy', 0) or 0)
    if busy > 0:
        d['_lp_busy'] = busy - 1             # gathering gold (game_lore_powers.py)
        return False
    if d.get('_lp_parley') == 'waiting':
        return False                          # holding its fire for an answer
    return countdown_turn(m, player, dungeon)


def countdown_turn(m, player, dungeon):
    """The Cu-Sith's three barks. None, or True when the third is its attack."""
    cv = spec(m, 'countdown_voice')
    if not cv or not ENABLED:
        return None
    d = m.__dict__
    n = int(d.get('_lp_barks', 0) or 0)
    # It barks only at a hero it has noticed (src/senses.py: its sight, its
    # nose; the simulator's fight is always engaged). Silenced, it has no
    # voice to bark with: the count holds where it was, and it hunts.
    if dungeon is not None and not d.get('_tracking'):
        return None
    if m.has_effect('silenced'):
        return None
    if not _in_sight(m, player, dungeon):
        d.pop('_lp_barked', None)            # out of sight: the next sight barks again
        if n:
            d['_lp_barks'] = 0
            d['_lp_clock'] = 0
            if cv.get('safe_line'):
                say(cv['safe_line'], 'info')
        return None
    if d.get('_lp_barked'):
        return None                          # the third bark is given: now it hunts
    every = max(1, int(cv.get('every', 3) or 3))
    clock = int(d.get('_lp_clock', 0) or 0) + 1
    d['_lp_clock'] = clock
    if n and (clock - 1) % every:
        return _hold(m, player, dungeon, cv)
    n += 1
    d['_lp_barks'] = n
    count = max(1, int(cv.get('count', 3) or 3))
    lines = cv.get('lines') or []
    heard = cv.get('unseen') or []
    if lines:
        say(lines[min(n, len(lines)) - 1], 'danger' if n >= count else 'warning', m=m,
            unseen=heard[min(n, len(heard)) - 1] if heard else None)
    if n < count:
        return _hold(m, player, dungeon, cv)
    d['_lp_barks'] = 0
    d['_lp_clock'] = 0
    d['_lp_barked'] = True
    d['_opener_now'] = dict(cv['attack'])
    return True


def _hold(m, player, dungeon, cv):
    """Between its barks the hound stands and watches the hero (False: the
    turn spent) unless he is beside it (None: it bites as usual), so a hero
    who reads the barks has the turns to get out of its sight. In the
    simulator's fight it is always beside him."""
    if dungeon is None or not cv.get('holds', True):
        return None
    if max(abs(m.x - player.x), abs(m.y - player.y)) <= 1:
        return None
    return False


def sim_turn(m, player):
    """The simulator's world turn for one engaged creature (it is always in
    sight there): the Cu-Sith's barks."""
    return countdown_turn(m, player, None)


# ---------------------------------------------------------------------------
# A blow by the creature (Monster._resolve_blow)
# ---------------------------------------------------------------------------
def blow_refused(m, player, atk: dict):
    """The line when the creature cannot use this attack now, else None:
    Likho blinded cannot cast her baleful eye."""
    if not ENABLED:
        return None
    try:
        import counters
        shun = counters.shuns(player, m)          # the whitethorn and the strix
    except Exception:
        shun = None
    if shun is not None:
        return counters.line(player, shun[0], shun[1], m)
    lost = spec(m, 'blinded_loses') or ()
    if atk.get('name') in lost and m.has_effect('blinded'):
        return _fill(m, "{The} turns {his} blinded eye on you, and it finds nothing.")
    return None


def _loosed(player) -> bool:
    """The Galdr of Loosing (slice G's free_action): nothing drags the hero."""
    try:
        return bool(player.has_effect('free_action'))
    except Exception:
        return False


def _loosed_line(m) -> str:
    import wards
    return wards.line('pull_loosed', m)


def after_blow(m, player, atk: dict, actual: int) -> str:
    """What follows a landed blow: the Roc's carry-off, the Yacumama's pull.
    Returns text for the blow's line ('' for none)."""
    if not ENABLED or actual <= 0:
        return ''
    out = ''
    co = atk.get('carry_off')
    if co and getattr(player, 'hp', 0) > 0:
        chance = float(co.get('chance', 0.0) or 0.0)
        try:
            if player.load_tier() in ('heavy', 'burdened', 'overloaded'):
                chance *= 0.5             # a heavy man is hard to lift
        except Exception:
            pass
        seized = random.random() < chance
        if seized and _loosed(player):
            out += ' ' + _loosed_line(m)        # nothing can grab him or lift him
        elif seized:
            lo, hi = (co.get('tiles') or (8, 15))[:2]
            # The game sets him down at once, right after this blow's line
            # (LorePowersMixin._lore_powers_lift): never left for a later turn.
            player.__dict__['_lp_carry_off'] = {'tiles': (int(lo), int(hi)),
                                                'landed': co.get('landed', ''),
                                                'nowhere': co.get('nowhere', '')}
            hurt = max(1, int(round(player.max_hp * float(co.get('share', 0.05) or 0.05))))
            player.take_damage(hurt, 'blunt')
            out += ' ' + _fill(m, co.get('line') or "{The} seizes you and lifts you into the air!")
    if (atk.get('pulls') and max(abs(m.x - player.x), abs(m.y - player.y)) > 1
            and not _loosed(player)):
        player._pending_pull_toward = (m.x, m.y)
        out += ' ' + _fill(m, atk.get('pull_line') or "{The} drags you toward {him}!")
    return out


# ---------------------------------------------------------------------------
# What happens to the creature (Monster.add_effect, Monster.take_damage)
# ---------------------------------------------------------------------------
def on_effect(m, name: str) -> None:
    """An effect just took hold on the creature: the Kappa's dish spills."""
    if not ENABLED or name not in ('stunned', 'paralyzed'):
        return
    os_ = spec(m, 'on_stunned')
    if not os_:
        return
    eff = str(os_.get('effect', 'weakened'))
    turns = int(os_.get('turns', 12) or 12)
    if m.status_effects.get(eff, 0) < turns:
        m.status_effects[eff] = turns
        if not m.__dict__.get('_lp_spilled'):
            m.__dict__['_lp_spilled'] = True
            say(_fill(m, os_.get('line') or "{The} is weakened!"), 'success', m=m)


# Whose blow it is, told by the game (LorePowersMixin: the Game's
# `_damage_by`): 'hero', 'pet', 'escort', 'monster', 'hazard', 'throes' (a
# death-throes blast) or 'status' (what a wound's last tick sets off). None
# (the simulator, a test) is the hero's.
BLAME = None


def _striker() -> str:
    try:
        return str(BLAME()) if BLAME is not None else 'hero'
    except Exception:
        return 'hero'


def on_tick(m) -> None:
    """Each of its turns (Monster.tick_effects): a stun or a hold on it now,
    however it was laid, spills the Kappa's dish (add_effect and hold say so
    at once; this catches one written straight into its statuses)."""
    if not ENABLED or not spec(m, 'on_stunned'):
        return
    st = getattr(m, 'status_effects', None) or {}
    for name in ('stunned', 'paralyzed'):
        if int(st.get(name, 0) or 0) > 0:
            on_effect(m, name)
            return


def after_damage(m, actual: int) -> None:
    """The creature took a blow: a calm one is calm no more, and a Lindworm
    sheds a skin at its marks.

    Only the hero's own blow breaks a peace or a parley, or his pet's (and
    then the line says so). A bleed, a burn or a poison ticking is no blow
    (``_dot_tick``, set by Monster.tick_effects), nor is a fire vent, a
    monster's blow or an escort's."""
    if actual <= 0 or not ENABLED:
        return
    d = m.__dict__
    by = None if d.get('_dot_tick') else _striker()
    if by in ('hero', 'pet'):
        if d.pop('_lp_calm', None):
            say(_fill(m, "{The} turns on you: the peace is broken." if by == 'hero'
                      else "{The} turns on your companion: the peace is broken."), 'warning', m=m)
        if d.get('_lp_parley') in ('waiting', 'calm'):
            d['_lp_parley'] = 'angry'
    ss = spec(m, 'sheds_skin')
    if not ss or m.hp <= 0 or not getattr(m, 'alive', True):
        return
    marks = sorted((float(x) for x in (ss.get('at') or ())), reverse=True)
    shed = int(d.get('_lp_skins', 0) or 0)
    if shed >= len(marks) or m.hp > m.max_hp * marks[shed]:
        return
    d['_lp_skins'] = shed + 1
    for e in SHED_EFFECTS:
        m.status_effects.pop(e, None)
    heal = int(m.max_hp * float(ss.get('heal_share', 0.08) or 0.0))
    m.hp = min(m.max_hp, m.hp + max(0, heal))
    say(_fill(m, ss.get('line') or "{The} sheds a skin!"), 'warning', m=m)


# ---------------------------------------------------------------------------
# The hero's blow (combat.strike_damage, combat.player_attack)
# ---------------------------------------------------------------------------
def weak_spot(m, chain: int) -> bool:
    """A chain long enough finds the Mapinguari's soft place: the blow
    ignores its resistances."""
    need = spec(m, 'weak_spot_chain')
    return bool(ENABLED and need and chain >= int(need))


def after_struck(player, m, weapon, chain: int, actual: int) -> None:
    """A hero's blow landed: the weak spot found (its line), and the
    Bulgasari's meal of iron."""
    if not ENABLED or actual <= 0:
        return
    if weak_spot(m, chain) and spec(m, 'weak_spot_line'):
        say(_fill(m, spec(m, 'weak_spot_line')), 'success')
    me = spec(m, 'metal_eater')
    if not me or weapon is None or not getattr(m, 'alive', False):
        return
    try:
        from status_effects import _can_rust
        if not _can_rust(weapon):
            return
        import coatings
        co = coatings.coating_of(weapon)
        if co and co.get('substance') == 'fire':
            return                  # a burning blade: its hide will not close on fire
    except Exception:
        return
    if random.random() >= float(me.get('wear_chance', 0.2) or 0.0):
        return
    try:
        from items import wear_down
        lost = wear_down(weapon)
    except Exception:
        lost = False
    if not lost:
        return                      # worn as far as it goes: nothing left to eat
    d = m.__dict__
    base = int(d.get('_lp_base_hp', 0) or m.max_hp)
    d['_lp_base_hp'] = base
    heal = max(1, int(base * float(me.get('heal_share', 0.04) or 0.0)))
    cap = int(base * (1.0 + float(me.get('grow_cap', 0.12) or 0.0)))
    if m.hp + heal > m.max_hp and m.max_hp < cap:
        m.max_hp = min(cap, m.hp + heal)            # it grows with every meal
    m.hp = min(m.max_hp, m.hp + heal)
    try:
        from hud_context import item_bare_name
        wname = item_bare_name(player, weapon)
    except Exception:
        wname = str(getattr(weapon, 'name', 'blade'))
    line = str(me.get('line') or "{The} gnaws your {weapon}.").replace('{weapon}', wname)
    say(_fill(m, line), 'warning', m=m, unseen=line.split(':')[0])


# ---------------------------------------------------------------------------
# What the hero sees (unseen.senses)
# ---------------------------------------------------------------------------
def shown_overhead(m, player) -> bool:
    """A creature that hangs overhead, inside the glow of a lit light."""
    if player is None or not spec(m, 'hidden_overhead'):
        return False
    try:
        import lights
        if lights.light_bonus(player) <= 0:      # no lit light, no Light spell
            return False
        reach = int(player.get_sight_radius())
    except Exception:
        return False
    return max(abs(m.x - player.x), abs(m.y - player.y)) <= reach


# ---------------------------------------------------------------------------
# Tells (src/tells.py): the keys of the powers this creature has.
# ---------------------------------------------------------------------------
_TELL_KEYS = ('countdown_voice', 'metal_eater', 'corpse_hop', 'parley', 'appeased_by',
              'on_stunned', 'hidden_overhead', 'weak_spot_chain', 'sheds_skin',
              'gold_gatherer', 'talisman')


def tell_keys(m) -> list:
    out = [k for k in _TELL_KEYS if spec(m, k)]
    for atk in getattr(m, 'attacks', None) or ():
        if not isinstance(atk, dict):
            continue
        if atk.get('carry_off'):
            out.append('carry_off')
        if atk.get('pulls'):
            out.append('ranged_pull')
        if atk.get('steal') == 'offering':
            out.append('steal_offering')
    return out


# ---------------------------------------------------------------------------
# Food that is an offering: plain food, never a dish cooked to carry.
# ---------------------------------------------------------------------------
_DISH_FOODS: set | None = None


def is_plain_food(item) -> bool:
    """A ration, bread, cheese, an apple...: Food that no recipe makes (a
    dish cooked to carry is levelling, never an offering) and that is not a
    one-of-a-kind find."""
    global _DISH_FOODS
    try:
        from items import Food
    except ImportError:
        return False
    if not isinstance(item, Food):
        return False
    if _DISH_FOODS is None:
        try:
            from paths import data_path
            with open(data_path('data', 'items', 'recipes.json'), encoding='utf-8') as f:
                recs = json.load(f)
            with open(data_path('data', 'items', 'food.json'), encoding='utf-8') as f:
                food = json.load(f)
            _DISH_FOODS = ({r['makes'] for r in recs.values() if isinstance(r, dict) and r.get('makes')}
                           | {k for k, v in food.items() if isinstance(v, dict) and v.get('special')})
        except (OSError, ValueError, ImportError, KeyError):
            _DISH_FOODS = set()
    return str(getattr(item, 'id', '') or '') not in _DISH_FOODS
