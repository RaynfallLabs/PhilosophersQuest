"""Uses What It Carries: a creature drinks the potion and throws the fire
pot it carries, and what it used is gone (monster behaviour, third wave:
AI-3, uses_what_it_carries, 2026-11-20).

Real soldiers and brigands carried physic and fire pots (the Byzantines'
Greek fire went into clay pots thrown by hand); a witch carries her own
draughts. A kind with ``kit`` (data/monsters.json: at most two entries,
``[{"item": <potion or flask id>, "chance": 0-1}]``) has it rolled the first
time anything asks (``_kit``, a tuple of item ids: every way a creature comes
onto a floor is covered, and a summoned or split one carries nothing).

* Badly hurt (under drink_below of its health), it drinks a healing
  potion it carries (or one it STOLE from the hero: src/theft.py) with its
  turn: it mends the potion's own share of ITS health (the share a hero's
  draught gives him: food_system.POTION_HEAL_SHARE). A wound that will not
  close (heal_blocked, ruptured, deep_wound) wastes it. The hero who sees it
  drunk knows that potion from then on.
* With a flask of fire oil and a clear throw at the hero two to four tiles
  off, it throws it: an ordinary ranged blow (the roll to hit, the wards,
  the guards), the flask's own fire, and its burning.
* What it used is gone; what it did not use falls where it dies (a real
  item, unidentified as any find is). A creature banished takes it home.

Never drinks: a stolen artifact or quest piece (theft never takes those),
an unknown or harmful potion of the hero's. Named foes and the stalker
keep their own fights. Pure module: src/ai_turn.py calls turn(); the Game
drops what is left (game_monster_ways.py); the simulator rolls and spends
the same kit (tools/balance/sim_ai3.py).
"""
from __future__ import annotations

import json
import random

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_kit knob
_ITEMS: dict | None = None


def rules() -> dict:
    return kind_data.rules('kit')


def item_defs() -> dict:
    """{id: (class, entry)} for the potions and flasks a kit may hold."""
    global _ITEMS
    if _ITEMS is None:
        from paths import data_path
        out = {}
        for cls in ('potion', 'flask'):
            try:
                with open(data_path('data', 'items', f'{cls}.json'), encoding='utf-8') as f:
                    raw = json.load(f)
            except (OSError, ValueError):
                continue
            for k, v in (raw.items() if isinstance(raw, dict) else ()):
                if isinstance(v, dict):
                    out[k] = (cls, v)
        _ITEMS = out
    return _ITEMS


HEAL_SHARES = {'heal': 'POTION_HEAL_SHARE', 'extra_heal': 'POTION_EXTRA_HEAL_SHARE'}


def heal_share(item_id: str) -> float:
    """The share of health the potion gives (0 if it does not heal)."""
    cls, e = item_defs().get(str(item_id or ''), (None, {}))
    eff = e.get('effect') if cls == 'potion' else None
    if eff == 'full_heal':
        return 1.0
    name = HEAL_SHARES.get(eff or '')
    if not name:
        return 0.0
    try:
        import food_system
        return float(getattr(food_system, name))
    except (ImportError, AttributeError):
        return 0.2 if eff == 'heal' else 0.4


def throw_spec(item_id: str) -> dict | None:
    cls, e = item_defs().get(str(item_id or ''), (None, {}))
    t = e.get('throw') if cls == 'flask' else None
    if isinstance(t, dict) and str(t.get('damage_type', '')) == 'fire' and int(t.get('damage', 0) or 0) > 0:
        return t
    return None


def _ruled(m) -> bool:
    d = m.__dict__
    return bool(ENABLED and not kind_data.named(m) and not kind_data.outside_rules(m)
                and not d.get('_is_summoned') and d.get('_summoned_by') is None
                and not d.get('_image_of'))


def kit(m, rng=random) -> tuple:
    """What it carries (item ids), rolled once."""
    have = m.__dict__.get('_kit')
    if isinstance(have, (tuple, list)):
        return tuple(have)
    spec = kind_data.field(m, 'kit', None)
    got = []
    if isinstance(spec, list) and _ruled(m):
        for e in spec[:2]:
            if isinstance(e, dict) and e.get('item') in item_defs():
                if rng.random() < float(e.get('chance', 1.0) or 0.0):
                    got.append(str(e['item']))
    m._kit = tuple(got)
    return m._kit


def _spend(m, item_id: str) -> None:
    left = list(kit(m))
    left.remove(item_id)
    m._kit = tuple(left)                 # a new tuple: copies share none
    used = dict(m.__dict__.get('_kit_used') or {})
    used[item_id] = used.get(item_id, 0) + 1
    m._kit_used = used


def _stolen_heal(m):
    """A healing potion the creature stole from the hero, or None."""
    for it in m.__dict__.get('stolen_items') or ():
        if heal_share(getattr(it, 'id', '')) > 0 and not getattr(it, 'is_artifact', False):
            return it
    return None


def _shown_name(item_id: str, player) -> str:
    """The potion as the hero knows it: its name if he knows the kind, else
    how it looks."""
    _cls, e = item_defs().get(item_id, (None, {}))
    known = item_id in (getattr(player, 'known_item_ids', None) or ())
    return str((e.get('name') if known else e.get('unidentified_name')) or e.get('name') or 'potion')


def _with_article(name: str) -> str:
    from monster import an_article
    return f"{an_article(name)} {name}"


def _drink(m, player, item_id: str, stolen=None) -> bool:
    share = heal_share(item_id)
    if share <= 0:
        return False
    name = _shown_name(item_id, player)
    if stolen is not None:
        m.__dict__['stolen_items'] = [i for i in (m.__dict__.get('stolen_items') or ())
                                      if i is not stolen]
        used = dict(m.__dict__.get('_kit_used') or {})
        used['stolen:' + item_id] = used.get('stolen:' + item_id, 0) + 1
        m._kit_used = used
    else:
        _spend(m, item_id)
    r = rules()
    if not m.can_heal():
        ai_lines.say(m, ai_lines.fill(m, r.get('drink_wasted', ''), potion=_with_article(name)),
                     r.get('drink_unseen', ''), 'info')
    else:
        before = m.hp
        m.hp = min(m.max_hp, m.hp + max(1, int(round(m.max_hp * share))))
        key = 'drink_stolen' if stolen is not None else 'drink'
        ai_lines.say(m, ai_lines.fill(m, r.get(key, ''), potion=_with_article(name),
                                      potion_bare=name, amount=m.hp - before),
                     r.get('drink_unseen', ''), 'warning')
    m._kit_learn = item_id                # the hero who saw it knows the kind now
    return True


def _throw_attack(item_id: str) -> dict:
    t = throw_spec(item_id) or {}
    _cls, e = item_defs().get(item_id, (None, {}))
    dmg = max(1, int(t.get('damage', 1) or 1))
    st = t.get('status') if isinstance(t.get('status'), dict) else {}
    # 'Thrown': a missile (wards.is_missile), never a spell a seal could stop.
    atk = {'name': 'Thrown ' + str(e.get('name') or 'Fire Pot'), 'damage': f"1d2+{max(0, dmg - 2)}",
           'type': 'fire', 'delivery': 'ranged', 'ranged': True, 'thrown_flask': item_id}
    if st.get('effect'):
        atk.update({'effect': st['effect'], 'effect_chance': 1.0,
                    'effect_duration': int(st.get('turns', 3) or 3)})
    return atk


def turn(m, player, dungeon, monsters, extra_occupied):
    """Its turn by what it carries (src/ai_turn.py): False (it drank: its
    turn is spent), True (it throws: Monster.attack takes the flask as a
    ranged blow), None (nothing to use now)."""
    if not _ruled(m):
        return None
    r = rules()
    hurt = m.hp < m.max_hp * float(r.get('drink_below', 0.35))
    if hurt and m.__dict__.get('_tracking'):
        stolen = _stolen_heal(m)
        if stolen is not None:
            return False if _drink(m, player, getattr(stolen, 'id', ''), stolen) else None
        for item_id in kit(m):
            if heal_share(item_id) > 0:
                return False if _drink(m, player, item_id) else None
    if int(getattr(m, '_flee_timer', 0) or 0) > 0:
        return None
    for item_id in kit(m):
        if throw_spec(item_id) is None:
            continue
        d = max(abs(m.x - player.x), abs(m.y - player.y))
        lo, hi = r.get('throw_range', [2, 4])
        if not (int(lo) <= d <= int(hi)) or not m.__dict__.get('_tracking'):
            continue
        if dungeon is not None and not m._has_clear_shot(player.x, player.y, dungeon, monsters or []):
            continue
        atk = _throw_attack(item_id)
        try:
            import attack_gates
            if attack_gates.blocks_attack(m, atk):
                continue                  # unstrung: no throw
        except ImportError:
            pass
        _spend(m, item_id)
        _cls, _e = item_defs().get(item_id, (None, {}))
        ai_lines.say(m, ai_lines.fill(m, r.get('throw', ''),
                                      flask=_with_article(str(_e.get('name') or 'fire pot').lower())),
                     r.get('throw_unseen', ''), 'danger')
        m._chosen_blow = atk
        return True
    return None


def leftovers(m) -> list:
    """What it did not use, as fresh items (the Game sets them down where it
    fell)."""
    out = []
    try:
        from items import make_item_by_id
    except ImportError:
        return out
    for item_id in kit(m):
        cls, _e = item_defs().get(item_id, (None, None))
        if cls is None:
            continue
        it = make_item_by_id(cls, item_id)
        if it is not None:
            out.append(it)
    m._kit = ()
    return out


def tell_keys(m) -> list:
    """What THIS one carries now (the eye sees the flask at his belt, the
    pot in his hand; once drunk or thrown, it is gone)."""
    if not isinstance(kind_data.field(m, 'kit', None), list):
        return []
    have = kit(m)
    keys = []
    if any(heal_share(i) > 0 for i in have):
        keys.append('carries_potion')
    if any(throw_spec(i) for i in have):
        keys.append('carries_fire')
    return keys
