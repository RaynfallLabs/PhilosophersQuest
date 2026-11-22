"""Carried lights and the Light spell (Brandon, 2026-11-19).

"Ranged monsters were particularly vicious, and did more damage by hit and
run than any melee monsters ... their range is often outside my
perception." A PER-10 hero sees five tiles and an archer shoots from six.

* **A light in the off hand** (data/items/light.json): a torch, a lantern,
  a lamp, or a named light from legend. It sits where a shield would, the way
  Joan of Arc's standard does, but it is not a shield: no AC, no plus, no
  wear (gear.is_light). So it cannot be held with a shield or a two-handed
  weapon: the trade is a shield's AC against seeing the archer.
* **Lit, it widens sight** by its ``sight``. Lights do not add up: the
  BRIGHTEST light the hero has counts, and only one (``light_bonus``): a
  carried light, the ``light`` status (the Light spell, a wand of light, a
  story's lantern), a torch held as a weapon (``equipped_light_aura``, the
  Prometheus Torch) and an escort's lamp. A shield-bearer casts Light; a
  torch-bearer does not need to. Dark vision, true sight and the Wild Road
  are senses, not lights, and still add on top (Player.get_sight_radius).
* **Light has a price**: a monster sees a lit hero from farther, by the
  brightest light's ``notice`` (its sight, unless its data says less: the
  dark lantern's shutter). ``shine`` is read by senses.sight_range.
  Doused (Shift+O, no time), a light gives nothing and costs nothing. A
  turn in which it was lit at no cost in time (``kindled``) burns and shows
  him all the same, once, though he put it straight out again.
* **In and out** (Shift+L, one turn, LightsMixin._swap_light): what the key
  draws is ``pick``, and the kind it draws first is ``readied_kind``, else
  the last put away. A kind and not one object, as the readied weapon is:
  a torch burns away.
* **The off hand, one rule** (``off_hand_takes``, ``two_hands``): whatever
  road a thing takes into the off hand (E, the Kit, a saved kit, S, the
  keys), it is one thing and never a stack (``leave_rest``), and the swap's
  memory follows it. A shield that gave way to a light is the one set
  aside; anything else put on the arm forgets what was set aside.
* **Fuel**: a torch burns itself away (``fuel`` 'self'); a lantern or a
  lamp burns oil ('oil', a Flask of Fire Oil fills it); some never burn out
  ('none'). A light burns only while held and lit (LightsMixin._light_tick).
* **The Light spell** gives the ``light`` status for turns from Intelligence
  (``spell_turns``); a wand of light for its ``power`` in turns.

Every number is in data/lights.json and data/items/light.json. Pure rules:
no pygame, no game state; works on stand-ins (getattr with defaults).
"""
from __future__ import annotations

import copy
import json
from functools import lru_cache


@lru_cache(maxsize=1)
def rules() -> dict:
    from paths import data_path
    with open(data_path('data', 'lights.json'), encoding='utf-8') as f:
        return json.load(f)


def line(key: str, **kw) -> str:
    """One of data/lights.json ``lines``, filled in."""
    return str((rules().get('lines') or {}).get(key, '')).format(**kw)


# ------------------------------------------------------------------ the item

def is_light(item) -> bool:
    """A light carried in the off hand (data/items/light.json)."""
    if item is None:
        return False
    if str(getattr(item, 'item_class', '') or '') == 'light':
        return True
    return type(item).__name__ == 'Light'


def held(player):
    """The light in the hero's off hand, or None."""
    sh = getattr(player, 'shield', None)
    return sh if is_light(sh) else None


def burn_of(item) -> int:
    """Turns a fresh torch or a full lantern lasts (0: it never burns out)."""
    try:
        return max(0, int(getattr(item, 'burn', 0) or 0))
    except (TypeError, ValueError):
        return 0


def everlasting(item) -> bool:
    return burn_of(item) <= 0


def fuel_kind(item) -> str:
    """'self' (a torch, burnt away), 'oil' (filled from a flask) or 'none'."""
    if everlasting(item):
        return 'none'
    k = str(getattr(item, 'fuel_kind', '') or 'self')
    return k if k in ('self', 'oil') else 'self'


def fuel_left(item) -> int:
    """Turns of burning left (an everlasting light: its burn, 0)."""
    if everlasting(item):
        return 0
    f = getattr(item, 'fuel', None)
    if f is None:
        return burn_of(item)
    try:
        return max(0, int(f))
    except (TypeError, ValueError):
        return 0


def has_fuel(item) -> bool:
    return everlasting(item) or fuel_left(item) > 0


def is_lit(item) -> bool:
    """Lit and able to burn."""
    return is_light(item) and bool(getattr(item, 'lit', False)) and has_fuel(item)


def sight_of(item) -> int:
    try:
        return max(0, int(getattr(item, 'sight', 0) or 0))
    except (TypeError, ValueError):
        return 0


def notice_of(item) -> int:
    """How much farther a monster sees the hero while it burns: its own
    ``notice`` when the data gives one (the dark lantern's shutter), else
    its sight."""
    n = getattr(item, 'notice', None)
    if n is None:
        return sight_of(item)
    try:
        return max(0, int(n))
    except (TypeError, ValueError):
        return sight_of(item)


def noun(item) -> str:
    return str(getattr(item, 'noun', '') or 'light')


def power_of(item) -> str:
    return str(getattr(item, 'power', '') or '')


def is_low(item) -> bool:
    """Burning down: at or under data ``low_share`` of its burn."""
    if not is_light(item) or everlasting(item):
        return False
    return fuel_left(item) <= int(burn_of(item) * float(rules().get('low_share', 0.2)))


def is_fresh(item) -> bool:
    """An unburnt torch (or a full lantern), unlit: one that stacks."""
    return (not bool(getattr(item, 'lit', False))) and (everlasting(item)
                                                         or fuel_left(item) >= burn_of(item))


def stacks_with(a, b) -> bool:
    """May these two lights of one kind share a pack row? Only fresh unlit
    ones: a torch half burnt is its own row."""
    if not (is_light(a) and is_light(b)):
        return True
    return is_fresh(a) and is_fresh(b)


# ------------------------------------------------------------ how bright

def status_sight() -> int:
    """Sight the ``light`` status gives (the spell, a wand, a story lamp)."""
    return int(rules().get('status_sight', 3))


def status_notice() -> int:
    return int(rules().get('status_notice', status_sight()))


def _has(player, effect: str) -> bool:
    has = getattr(player, 'has_effect', None)
    if has is None:
        return False
    try:
        return bool(has(effect))
    except Exception:
        return False


def weapon_aura(player) -> int:
    """The brightest torch held as a weapon (``equipped_light_aura``: the
    Prometheus Torch), in either weapon slot."""
    best = 0
    for slot in (getattr(player, 'weapon', None), getattr(player, 'ranged_weapon', None)):
        if slot is not None:
            try:
                best = max(best, int(getattr(slot, 'equipped_light_aura', 0) or 0))
            except (TypeError, ValueError):
                pass
    return best


def sources(player, extra: int = 0, aura: int | None = None) -> list:
    """Every light the hero has now: [(what, sight, notice)]. ``extra``: a
    lamp carried beside him (an escort's 'light' perk), which lights his
    way but is not his to be seen by. ``aura``: the weapon's light, when
    the caller has read it already."""
    out = []
    lt = held(player)
    if is_lit(lt):
        out.append(('carried', sight_of(lt), notice_of(lt)))
    if _has(player, 'light'):
        out.append(('status', status_sight(), status_notice()))
    a = weapon_aura(player) if aura is None else int(aura or 0)
    if a > 0:
        out.append(('weapon', a, a))
    if int(extra or 0) > 0:
        out.append(('escort', int(extra), 0))
    return out


def light_bonus(player, extra: int = 0, aura: int | None = None) -> int:
    """The sight the hero's lights give: the brightest one only."""
    return max([s for _w, s, _n in sources(player, extra, aura)] or [0])


def shine(player) -> int:
    """How much farther a monster sees the hero by the lights he has lit
    (senses.sight_range): the brightest one's notice, and one lit for a
    look this turn counts until the world has had its turn (``kindled``).
    0 in the dark."""
    try:
        looked = int(getattr(player, '_kindled_glow', 0) or 0)
        return max([looked] + [n for _w, _s, n in sources(player)])
    except Exception:
        return 0


# ------------------------------------------------------- the named powers

def _power_on(player, power: str) -> bool:
    lt = held(player)
    return is_lit(lt) and power_of(lt) == power


def shows_invisible(player) -> bool:
    """Psyche's Lamp, lit: invisible creatures are seen (unseen.py)."""
    return _power_on(player, 'shows_invisible')


def unmasks(player) -> bool:
    """Hecate's Torch, lit: ambushers and mimics show themselves (unseen.py)."""
    return _power_on(player, 'unmasks')


def shows_way(player) -> bool:
    """Hero's Lamp, lit: the down stair is on the map."""
    return _power_on(player, 'shows_way')


# ------------------------------------------------------------ the spell

def spell_turns(intelligence) -> int:
    """Turns the Light spell's light lasts: data ``spell``."""
    s = rules()['spell']
    try:
        intel = int(intelligence)
    except (TypeError, ValueError):
        intel = 10
    n = int(s['base_turns']) + int(s['turns_per_int']) * (intel - 10)
    return max(int(s['min_turns']), min(int(s['max_turns']), n))


def spell_cap() -> int:
    """The longest the spell's light can be made to last by casting again."""
    return int(rules()['spell']['max_turns'])


def wand_turns(power) -> int:
    """Turns a wand of light's light lasts: its ``power``."""
    try:
        n = int(str(power).strip())
    except (TypeError, ValueError):
        n = int(rules()['spell']['base_turns'])
    return max(1, min(wand_cap(), n))


def wand_cap() -> int:
    return int(rules().get('wand_max_turns', spell_cap()))


@lru_cache(maxsize=1)
def _wand_defs() -> dict:
    from paths import data_path
    try:
        with open(data_path('data', 'items', 'wand.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def wand_light(wand) -> tuple:
    """(turns, reveals) for a wand of light, from TODAY's data by id: a wand
    pickled before 2026-11-19 carries its old ``power``, a radius (4 or 8),
    which would now read as turns. ``reveals``: the Lantern of Diogenes
    also shows the unseen (``light_reveals``)."""
    d = _wand_defs().get(str(getattr(wand, 'id', '') or '')) or {}
    if d.get('effect') == 'light':
        return wand_turns(d.get('power', '')), bool(d.get('light_reveals', False))
    return wand_turns(getattr(wand, 'power', '')), bool(getattr(wand, 'light_reveals', False))


# ------------------------------------------------------------ burning

def oil_items() -> tuple:
    return tuple(rules().get('oil_items') or ())


def oil_in(inventory):
    """The first flask of oil in the pack that can fill a lantern, or None."""
    ok = set(oil_items())
    for it in inventory or ():
        if getattr(it, 'id', None) in ok:
            return it
    return None


def needs_fill(item) -> bool:
    """A lantern or a lamp that burns oil and is not full."""
    return fuel_kind(item) == 'oil' and fuel_left(item) < burn_of(item)


def fill(item) -> None:
    """Fill a lantern to the brim (the caller spends the flask)."""
    item.fuel = burn_of(item)


def next_torch(inventory, light):
    """A fresh stack of the same kind as the torch that just burnt out, in
    the pack, or None."""
    lid = getattr(light, 'id', None)
    for it in inventory or ():
        if it is not light and getattr(it, 'id', None) == lid and is_light(it) and has_fuel(it):
            return it
    return None


def readied_kind(player) -> str:
    """The kind of light the hero readied from the Kit, which Shift+L takes
    up first. '' for none: then the last put away (``last_kind``)."""
    d = getattr(player, '__dict__', None) or {}
    return str(d.get('_light_kind', '') or '')


def last_kind(player) -> str:
    """The kind of light last put away with Shift+L. '' for none yet."""
    d = getattr(player, '__dict__', None) or {}
    return str(d.get('_light_last', '') or '')


def is_readied(player, item) -> bool:
    """Does Shift+L take up this kind of light first?"""
    kind = readied_kind(player)
    return bool(kind) and is_light(item) and str(getattr(item, 'id', '') or '') == kind


def pick(player):
    """The light Shift+L takes up from the pack, or None. One that can burn
    (a dry lantern only with oil to fill it, and only if nothing else
    burns); the readied kind before any other, then the kind last put away;
    then the brightest, one with a power, one already part burnt (so every
    torch is not started)."""
    inv = getattr(player, 'inventory', None) or []
    oil = oil_in(inv) is not None
    can = [it for it in inv if is_light(it)
           and (has_fuel(it) or (oil and fuel_kind(it) == 'oil'))]
    if not can:
        return None
    last = last_kind(player)
    return max(can, key=lambda it: (has_fuel(it), is_readied(player, it),
                                    str(getattr(it, 'id', '') or '') == last, sight_of(it),
                                    bool(power_of(it)), everlasting(it), -fuel_left(it)))


def take_one(inventory: list, stack):
    """One light off a pack row: the row itself when it is the last, else a
    copy of one (the row keeps the rest). The one taken is NOT in the pack."""
    n = int(getattr(stack, 'count', 1) or 1)
    if n > 1:
        one = copy.copy(stack)
        one.count = 1
        stack.count = n - 1
        return one
    for i, it in enumerate(inventory):
        if it is stack:
            del inventory[i]
            break
    return stack


def leave_rest(inventory: list, piece) -> None:
    """``piece`` as one light, itself (what remembers it still finds it):
    whatever was stacked on it stays behind as a pack row of its own."""
    n = int(getattr(piece, 'count', 1) or 1)
    if n <= 1:
        return
    rest = copy.copy(piece)
    rest.count = n - 1
    piece.count = 1
    at = next((i + 1 for i, it in enumerate(inventory) if it is piece), len(inventory))
    inventory.insert(at, rest)


# ------------------------------------- the off hand, and what is remembered

def _packed(player, item):
    """``item`` while it is in the pack, else None."""
    inv = getattr(player, 'inventory', None) or ()
    return item if item is not None and any(i is item for i in inv) else None


def forget(player) -> None:
    """The light is owed nothing any more."""
    player._light_aside = None
    player._light_sidearm = None


def set_aside(player, shield) -> None:
    """``shield`` left the arm to make room for a light: it is what comes
    back when the light goes."""
    forget(player)
    player._light_aside = shield
    player._shield_slung = None


def off_hand_takes(player, piece, old=None) -> None:
    """``piece`` went into the off hand, by any road (Player._apply_equip),
    in place of ``old``. A light in place of a shield, or in place of the
    shield that waited for a free hand, sets that shield aside; a light in
    place of a light or of nothing changes no memory; a shield on the arm
    ends the light's."""
    slung = _packed(player, player.__dict__.get('_shield_slung'))
    player._shield_slung = None
    if not is_light(piece):
        forget(player)
        return
    gave = old if old is not None else slung
    if gave is not None and not is_light(gave):
        set_aside(player, gave)


def two_hands(player, sent=None) -> None:
    """A two-handed weapon went into the hand and sent ``sent`` from the off
    hand to the pack. A light sent there is only waiting. With no light in
    the hand or waiting, the two hands are given back: the shield set aside
    for a light waits for a free hand instead."""
    d = player.__dict__
    if sent is not None:
        d['_shield_slung'] = sent
        if not is_light(sent):
            forget(player)
        return
    slung = _packed(player, d.get('_shield_slung'))
    if is_light(slung):
        return
    if slung is None:
        d['_shield_slung'] = _packed(player, d.get('_light_aside'))
    forget(player)


# ------------------------------------------------------------ burning

def kindled(player, light) -> None:
    """``light`` was lit at no cost in time (Shift+O, a swap that takes no
    turn): this turn counts as burning and seen, once, even if it is put
    out before the turn passes."""
    player._kindled = light
    player._kindled_glow = max(int(getattr(player, '_kindled_glow', 0) or 0), notice_of(light))


def burn_turn(light, counted: bool = False) -> str:
    """One turn of burning for a held, lit light, or for one that counts as
    burning this turn (``counted``: kindled). Returns what happened:
    '' (it burns on), 'low' (it just crossed into burning low) or 'out' (it
    is spent). An everlasting light never changes."""
    if everlasting(light) or not (is_lit(light) or (counted and has_fuel(light))):
        return ''
    was_low = is_low(light)
    light.fuel = fuel_left(light) - 1
    if light.fuel <= 0:
        light.fuel = 0
        light.lit = False
        return 'out'
    if is_low(light) and not was_low:
        return 'low'
    return ''


# ------------------------------------------------------------ what it says

def card_lines(item) -> list:
    """What a light does, for its card (What It Does), powers first."""
    if not is_light(item):
        return []
    c = rules().get('card') or {}
    out = [c['sight'].format(sight=sight_of(item))]
    p = power_of(item)
    if p:
        txt = (rules().get('powers') or {}).get(p)
        if txt:
            out.append(txt)
    if everlasting(item):
        out.append(c['everlasting'])
    elif fuel_kind(item) == 'oil':
        out.append(c['burn_oil'].format(burn=burn_of(item), left=fuel_left(item)))
    else:
        out.append(c['burn_self'].format(burn=burn_of(item), left=fuel_left(item)))
    if notice_of(item) < sight_of(item):
        out.append(c['notice_less'].format(notice=notice_of(item)))
    else:
        out.append(c['notice'].format(notice=notice_of(item)))
    out.append(c['brightest'])
    out.append(c['hand'])
    out.append(c['swap'])
    out.append(c['douse'])
    return [s for s in out if s]


def hud_line(player, name: str = '') -> str:
    """The sidebar's small marker for the held light: how much is left once
    it burns low, 'dry' or 'out' when it gives no light. '' otherwise."""
    lt = held(player)
    if lt is None:
        return ''
    h = rules().get('hud') or {}
    label = name or str(getattr(lt, 'name', '') or noun(lt).title())
    if everlasting(lt):
        return '' if getattr(lt, 'lit', False) else h.get('dark', '').format(Light=label)
    if not has_fuel(lt):
        return h.get('dry', '').format(Light=label)
    if not getattr(lt, 'lit', False):
        return h.get('dark', '').format(Light=label)
    if is_low(lt):
        return h.get('low', '').format(Light=label, left=fuel_left(lt))
    return ''


def room_chance() -> float:
    return float((rules().get('spawn') or {}).get('room_chance', 0.10))
