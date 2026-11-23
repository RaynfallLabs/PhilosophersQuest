"""Wards: what keeps a monster's blow off the hero (MONSTERS AND MAGIC, 2026-11-19).

The rules are data (data/wards.json); this module is pure: it reads the hero's
statuses and the monster in front of it and answers the one question each hook
asks. Every ward is an ordinary hero status, so it ticks, shows on the HUD, is
dispelled and saved like any other.

* **Family wards** (``ward_*``): a scroll's or a prayer's rite against one family
  (family_lore.family_of). ``holds`` says what it stops:

  - ``melee``: no blow, bite, touch, grapple, sting or trample from that family
    lands. Striking one of them ends the ward against that one (``breaks:
    creature``). A named foe is too strong for it: its first blow lands at half
    and the ward breaks against it.
  - ``riders``: the family's blows carry none of the listed riders (the Psylli).
  - ``sight``: the family cannot notice the hero (senses._hidden); striking any
    one of them ends it for all (Hoichi's ears). A named foe is not fooled.
  - ``damage``: the family's damage times ``mult`` (Saint Martha), named foes too.

* **The hero's own wards**: ``missile_ward`` (every missile fails),
  ``stayed_spear`` (missiles from a foe he can see fail), ``veiled`` (no foe
  farther than ``veil_reach`` sees him or shoots him), ``all_round_ward`` (a pack
  round him gains nothing: packs.py), ``sanctuary`` (ordinary foes hold off until
  he strikes), ``styx_dipped`` (no physical blow, bite or claw wounds him; an unseen one
  finds the heel at half).

Hooks (one line each): Monster._resolve_blow asks ``blow_gate``;
Monster._apply_attack_effect asks ``rider_line``; monster._edge_incoming asks
``damage_mult``; senses._hidden asks ``hidden_from``; senses.sees asks
``veil_hides``; Monster.take_damage tells ``hero_struck`` (through
monster.HERO_STRUCK, which the game sets) whenever the hero's blow lands.

A creature's own memory of a broken ward lives on the creature
(``_wards_broken``, a set of ward ids, always replaced and never mutated in
place: the simulator shallow-copies monsters).
"""
from __future__ import annotations

import json

_DATA = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'wards.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def family_wards() -> dict:
    return data()['family_wards']


def ward_spec(wid: str) -> dict:
    return family_wards().get(wid) or {}


def status_registry() -> dict:
    """{status: (display name, colour, description)} for every ward status,
    for status_effects.EFFECT_INFO."""
    out = {}
    for wid, w in family_wards().items():
        out[wid] = (w['name'], tuple(w.get('colour', (200, 200, 200))), w.get('desc', ''))
    for sid, row in data()['statuses'].items():
        out[sid] = (row[0], tuple(row[1]), row[2])
    return out


def expire_messages() -> dict:
    out = {wid: (w.get('expire', ''), 'info') for wid, w in family_wards().items() if w.get('expire')}
    for sid, row in data()['statuses'].items():
        if len(row) > 3 and row[3]:
            out[sid] = (row[3], 'info')
    return out


def resist_blocks() -> dict:
    """{status: set of statuses it keeps off} (free_action, wakeful, clear_sight)."""
    return {k: set(v) for k, v in data()['resist_blocks'].items()}


def line(key: str, m=None, **kw) -> str:
    text = data()['lines'].get(key, '')
    return _fill(m, text, **kw)


def _fill(m, text: str, **kw) -> str:
    if not text:
        return ''
    try:
        from monster import fill
        out = fill(m, text, **kw)
    except Exception:
        out = text
    return out[:1].upper() + out[1:] if out else out


# ---------------------------------------------------------------------------
# What kind of blow it is
# ---------------------------------------------------------------------------

def delivery(atk) -> str:
    try:
        import guards
        return guards.delivery(atk or {})
    except Exception:
        return str((atk or {}).get('delivery', 'blow'))


def _attack_name(atk) -> str:
    return str((atk or {}).get('name', '') or '').lower()


def is_missile(atk) -> bool:
    """A physical missile: an arrow, a stone, a thrown spear or knife, a
    hurled boulder. Shot from afar (delivery 'ranged') and either of a
    physical damage type or named as a thing shot or thrown
    (data/wards.json missile_words: a poisoned dart, a hurled glacier). A
    bolt of fire, a death ray or a curse is a spell, not a missile; a breath,
    a gaze or a voice is not shot at all."""
    if delivery(atk) != 'ranged':
        return False
    if str((atk or {}).get('type', 'physical') or 'physical') in set(data()['physical_types']):
        return True
    name = _attack_name(atk)
    return any(w in name for w in data().get('missile_words') or ())


def is_cast(atk) -> bool:
    """A spell shot from afar: a 'ranged' attack that is not a missile and
    not a spit, a spray or a swoop (data/wards.json not_cast_words), whatever
    its damage type (fire, cold, necrotic, shadow, magic...)."""
    if delivery(atk) != 'ranged' or is_missile(atk):
        return False
    name = _attack_name(atk)
    return not any(w in name for w in data().get('not_cast_words') or ())


def is_melee(atk) -> bool:
    return delivery(atk) in set(data()['melee_deliveries'])


def _named(m) -> bool:
    try:
        return bool(m._is_named_foe())
    except Exception:
        return bool(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False))


def _family(m):
    try:
        import family_lore
        return family_lore.family_of(m)
    except Exception:
        return None


def _broken(m) -> set:
    return set((getattr(m, '__dict__', {}) or {}).get('_wards_broken') or ())


def _key(player, wid: str) -> str:
    """This rite's own key: a ward read again is a new rite, and what broke
    the last one against a creature does not break this one."""
    gen = ((getattr(player, '__dict__', {}) or {}).get('_ward_gen') or {}).get(wid, 0)
    return f"{wid}#{int(gen)}"


def _break_on(m, key: str) -> None:
    m._wards_broken = _broken(m) | {key}


def _active(player, wid: str) -> bool:
    try:
        return bool(player.has_effect(wid))
    except Exception:
        return False


def wards_on(player, m, hold: str) -> list:
    """The family wards the hero has up against ``m``'s family that hold
    ``hold`` and are not broken against ``m``: [(ward id, spec)]."""
    fam = _family(m)
    if not fam or m is None:
        return []
    broken = _broken(m)
    out = []
    for wid, w in family_wards().items():
        if hold in (w.get('holds') or ()) and fam in (w.get('families') or ()) \
                and _key(player, wid) not in broken and _active(player, wid):
            out.append((wid, w))
    return out


def _seen_by(player, m) -> bool:
    """The hero sees ``m`` now: in his field of view and not hidden from him.
    With no game behind the player (a test, the simulator), seen unless
    concealed (an invisible creature, an ambusher not yet sprung)."""
    try:
        import unseen
    except Exception:
        return True
    game = getattr(player, '_combat_game_ref', None)
    vis = getattr(game, 'visible', None) if game is not None else None
    if vis is None:
        return not unseen.concealed(m, player)
    return bool(unseen.seen(m, vis, player))


def _cheb(m, player) -> int:
    try:
        from geom import chebyshev_distance
        return int(chebyshev_distance(player.x, player.y, m))
    except Exception:
        return max(abs(m.x - player.x), abs(m.y - player.y))


def _attack_word(atk) -> str:
    try:
        from monster import attack_noun
        return attack_noun(atk)
    except Exception:
        return str((atk or {}).get('name', 'attack')).lower()


# ---------------------------------------------------------------------------
# The blow gate (Monster._resolve_blow)
# ---------------------------------------------------------------------------

def blow_gate(player, m, atk):
    """None to let the blow go on; else (0, line): it does not land.

    Sanctuary first (an ordinary foe the hero has not hurt will not strike
    at all), then the missile wards, then the family melee wards, then the
    Styx. A named foe's first blow through a melee ward goes on at half
    (``_ward_half`` read by damage_mult) and the ward breaks against it."""
    if player is None or m is None or getattr(m, 'is_allied', False):
        return None
    word = _attack_word(atk)
    # Sanctuary: the old law of the church door.
    if _active(player, 'sanctuary') and not _named(m) and not _hurt_lately(player, m):
        return 0, _once(m, '_sanct_said', _gen(player, 'sanctuary'), line('sanctuary', m))
    # The Mist of Manannan: a foe farther off than the veil reaches cannot
    # see the hero to aim at him: no shot, no spell, no gaze from there.
    if (_active(player, 'veiled') and _cheb(m, player) > int(data()['veil_reach'])
            and (is_missile(atk) or is_cast(atk) or delivery(atk) == 'gaze')):
        return 0, line('veiled', m, attack=word)
    if is_missile(atk):
        if _active(player, 'missile_ward'):
            return 0, line('missile_ward', m, attack=word)
        if _active(player, 'stayed_spear') and _seen_by(player, m):
            return 0, line('stayed_spear', m, attack=word)
    if is_melee(atk):
        held = wards_on(player, m, 'melee')
        if held and _named(m):
            # Too strong for every rite against it at once: one blow at half,
            # and each such ward breaks against it (two wards are not two
            # half blows).
            for wid, _w in held:
                _break_on(m, _key(player, wid))
            m._ward_half = True
            _say(player, _fill(m, held[0][1].get('named', '')))
            return None
        if held:
            return 0, _fill(m, held[0][1].get('held', ''))
        if (_active(player, 'styx_dipped') and delivery(atk) in set(data()['styx_deliveries'])
                and str(atk.get('type', 'physical')) in set(data()['physical_types'])):
            if _seen_by(player, m):
                return 0, line('styx', m, attack=word)
            m._ward_half = True
            _say(player, line('styx_heel', m))
    return None


def _gen(player, wid: str) -> int:
    return int(((getattr(player, '__dict__', {}) or {}).get('_ward_gen') or {}).get(wid, 0))


def _once(m, key: str, gen: int, text: str) -> str:
    """A line said once per creature for one ward (a creature that stands
    beside the hero all through a sanctuary is told of once; under the next
    sanctuary, once again)."""
    if (getattr(m, '__dict__', {}) or {}).get(key) == gen:
        return ''
    try:
        setattr(m, key, gen)
    except Exception:
        pass
    return text


def _say(player, text: str) -> None:
    if not text:
        return
    game = getattr(player, '_combat_game_ref', None)
    if game is not None and hasattr(game, 'add_message'):
        game.add_message(text, 'info')


def rider_line(player, m, effect: str):
    """The family ward's line when it keeps ``effect`` off (the blow still
    landed), else None."""
    for wid, w in wards_on(player, m, 'riders'):
        riders = w.get('riders')
        if riders and effect not in riders:
            continue
        try:
            from status_effects import _EFFECT_NOUN
            noun = _EFFECT_NOUN.get(effect, effect.replace('_', ' '))
        except Exception:
            noun = effect.replace('_', ' ')
        # A rider with a line of its own (the Psylli's for a hold: 'held',
        # src/holds.py), else the ward's one rider line.
        text = (w.get('rider_lines') or {}).get(effect) or w.get('rider', '')
        return _fill(m, text, noun=noun)
    return None


def damage_mult(player, m) -> float:
    """What the hero's wards leave of ``m``'s damage: a damage ward's mult
    (Saint Martha, named dragons too), and half for a named foe's one blow
    through a melee ward or an unseen blow on a Styx-dipped hero."""
    mult = 1.0
    if m is None or player is None:
        return mult
    d = getattr(m, '__dict__', {}) or {}
    if d.get('_ward_half'):
        m._ward_half = False
        mult *= 0.5
    fam = _family(m)
    if fam:
        for wid, w in family_wards().items():
            if ('damage' in (w.get('holds') or ()) and fam in (w.get('families') or ())
                    and _active(player, wid) and (w.get('named_too') or not _named(m))):
                mult = min(mult, float(w.get('mult', 1.0)))
                if not d.get('_ward_dmg_said'):
                    m._ward_dmg_said = True
                    _say(player, _fill(m, w.get('damage', '')))
    return mult


def hidden_from(player, m) -> bool:
    """A sight ward hides the hero from ``m`` (Hoichi's sutra from a ghost).
    A named foe is not fooled."""
    if m is None or _named(m):
        return False
    return bool(wards_on(player, m, 'sight'))


def veil_hides(player, m, dist: int) -> bool:
    """The Mist of Manannan: a foe farther off than the veil reaches cannot
    see the hero (it may still hear him, smell him, feel his tread)."""
    return _active(player, 'veiled') and int(dist) > int(data()['veil_reach'])


def all_round(player) -> bool:
    """The Breastplate's ward on every side: a pack round the hero gains
    nothing by it (packs.py: no swarm, no hamstring)."""
    return _active(player, 'all_round_ward')


def free_of_pull(player) -> bool:
    return _active(player, 'free_action')


# ---------------------------------------------------------------------------
# The hero strikes
# ---------------------------------------------------------------------------

def hero_struck(player, m, turn: int | None = None) -> list:
    """The hero's blow (a weapon, a spell, a wand, a flask) has landed on
    ``m``: the wards it breaks, and sanctuary, end now. Returns the lines to
    say."""
    out = []
    if m is None or player is None:
        return out
    if turn is not None:
        m._hurt_by_hero_turn = int(turn)
    else:
        m._hurt_by_hero = True
    if _active(player, 'sanctuary'):
        player.status_effects.pop('sanctuary', None)
        out.append(line('sanctuary_ends', m))
    fam = _family(m)
    if not fam:
        return out
    broken = _broken(m)
    for wid, w in family_wards().items():
        if fam not in (w.get('families') or ()) or not _active(player, wid):
            continue
        how = w.get('breaks', 'never')
        if how == 'creature' and _key(player, wid) not in broken:
            _break_on(m, _key(player, wid))
            if w.get('broken'):
                out.append(_fill(m, w['broken']))
        elif how == 'all':
            player.status_effects.pop(wid, None)
            if w.get('broken_all'):
                out.append(_fill(m, w['broken_all']))
    return [t for t in out if t]


def _hurt_lately(player, m) -> bool:
    d = getattr(m, '__dict__', {}) or {}
    if d.get('_hurt_by_hero'):
        return True
    t = d.get('_hurt_by_hero_turn')
    if t is None:
        return False
    game = getattr(player, '_combat_game_ref', None)
    now = getattr(game, 'turn_count', None) if game is not None else None
    if now is None:
        return True
    return int(now) - int(t) <= int(data()['sanctuary_memory'])


def hostile_act(player) -> str:
    """The hero attacks, casts or zaps at a creature (game_combat
    _ring_veil_slips): sanctuary ends. The line, or ''."""
    if _active(player, 'sanctuary'):
        player.status_effects.pop('sanctuary', None)
        return line('sanctuary_ends')
    return ''


def grant(player, wid: str, turns: int, cap: int | None = None) -> int:
    """Put ward ``wid`` up for ``turns`` (each time a fresh rite, whether or
    not the last still stands: every creature's old break is forgotten).
    Returns the turns it now has."""
    turns = max(1, int(turns))
    if wid in family_wards() or wid == 'sanctuary':
        gens = dict((getattr(player, '__dict__', {}) or {}).get('_ward_gen') or {})
        gens[wid] = int(gens.get(wid, 0)) + 1
        player._ward_gen = gens
    if cap:
        player.add_effect(wid, turns, cap=cap)
    else:
        player.add_effect(wid, turns)
    return int(player.status_effects.get(wid, 0) or 0)


def families_of(wid: str) -> list:
    return list(ward_spec(wid).get('families') or ())


_ITEM_DEFS: dict = {}


def item_def_all(item_class: str) -> dict:
    """Every entry of data/items/<class>.json (read once)."""
    item_def(item_class, '')
    return dict(_ITEM_DEFS.get(item_class) or {})


def item_def(item_class: str, item_id: str) -> dict:
    """Today's data entry of an item by class and id (data/items/<class>.json):
    the fields the old item classes do not copy onto the object (a scroll's
    ``ward`` and ``turns``, its ``ward_also``). An old save's item reads
    today's data."""
    if item_class not in _ITEM_DEFS:
        try:
            from paths import data_path
            with open(data_path('data', 'items', f'{item_class}.json'), encoding='utf-8') as f:
                _ITEM_DEFS[item_class] = json.load(f)
        except (OSError, ValueError):
            _ITEM_DEFS[item_class] = {}
    return dict(_ITEM_DEFS[item_class].get(item_id) or {})


def field_of(entry: dict, key: str, buc: str = 'uncursed', default=None):
    """One of a kind's own numbers from its data entry (``item_def``): its
    ``<key>_blessed`` or ``<key>_cursed`` when the copy is so and the data
    names one, else ``<key>``, else ``default``. The one lookup a scroll's
    handler and its card (item_words) share, so the two cannot drift: the
    handler passes the copy's blessing, the card the blessing the hero
    knows."""
    entry = entry or {}
    if buc in ('blessed', 'cursed') and f"{key}_{buc}" in entry:
        return entry[f"{key}_{buc}"]
    return entry.get(key, default)
