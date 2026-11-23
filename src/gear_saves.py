"""Old saves meet the 3.3.2 armour ladder (bug bash 3.3.2, Armour 7/7).

Game._migrate_recompose_composite_items already rebuilds a common piece's
AC and level from its template. This finishes the job, once per load:

- a common minor piece keeps its enchantment's name and line (the recompose
  rewrote its name); one from before the enchantments (a level, no
  enchantment) gets one, rolled from its id so the same save always gets
  the same one;
- a named armour piece, shield, ring, amulet or belt takes its mechanical
  fields from today's data (AC, plus, level, enchantment, tier, threshold,
  effects, saving throws), keeping what is the hero's own: its blessing,
  what he knows of it, its wear, an Enchant Armour scroll's plus, an
  attunement's tier;
- a common ring or amulet of a kind (rings.py) takes its effects from
  today's data and its kind's ladder at its own level: the Ring of
  Sustenance lent Sustained for good from its old data, on top of its
  kind's hunger ladder (2026-11-22);
- what the hero wears lends what it lends now: a status it no longer
  grants comes off (unless something else still grants it), a new one goes
  on, and the worn stats re-sync.

Pure item and player plumbing; main.py calls `migrate`.
"""
from __future__ import annotations

import json
import random
from functools import lru_cache


@lru_cache(maxsize=None)
def _named(cat: str) -> dict:
    from paths import data_path
    try:
        with open(data_path('data', 'items', f'{cat}.json'), encoding='utf-8') as f:
            d = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in d.items() if isinstance(v, dict) and v.get('is_unique')}


def _granted(item) -> set:
    """The statuses a worn item lends."""
    out = set()
    st = getattr(item, 'on_equip_status', '') or ''
    if st:
        out.add(st)
    fx = getattr(item, 'effects', None) or {}
    if isinstance(fx, dict) and 'effect_chance' not in fx:
        from items import Weapon, worn_statuses
        # (On a weapon `effects.status` is what its blow does to a foe.)
        if not isinstance(item, Weapon):
            out.update(worn_statuses(fx))
    return out


# ------------------------------------------------------------- common pieces

def enchant_common(item) -> None:
    """A composite minor piece: its enchantment's name back on (the
    recompose rebuilt the name from template and material), or, made before
    the enchantments, one rolled for its level."""
    import enchantments
    import gear
    from items import Armor
    if not isinstance(item, Armor) or getattr(item, 'is_unique', False):
        return
    slot = getattr(item, 'slot', '')
    level = int(getattr(item, 'ench_level', 0) or 0)
    if slot not in gear.MINOR_SLOTS or level <= 0:
        return
    ench_id = getattr(item, 'ench_id', '') or ''
    if not ench_id:
        rng = random.Random(f"{getattr(item, 'id', '')}:{level}")
        ench_id = enchantments.roll(slot, level, rng)
    if ench_id and not str(getattr(item, 'name', '')).endswith(
            enchantments.display_name(enchantments.get(ench_id), level)):
        enchantments.apply_to(item, ench_id)
    ench = enchantments.get(ench_id)
    if ench:
        # Today's words and numbers: a ladder or a line may have moved since
        # the piece was made (the gear balance check of 2026-11-12 halved
        # Striking, laddered Speed and Displacement, and gave every guard its
        # honest wording).
        item.special = enchantments.describe(ench, level)
        item.ench_line = item.special
        _retire_status(item, ench_id, None)


def _retire_status(item, ench_id: str, fresh) -> None:
    """A status an enchantment lent and lends no more (Speed's haste,
    Displacement's status: enchantments.RETIRED_STATUS) comes off the piece,
    unless the piece's own data still lends it (`fresh`, today's copy of a
    named piece: the Greaves of Hermes stay hasted)."""
    import enchantments
    old = enchantments.RETIRED_STATUS.get(ench_id or '')
    if old and getattr(item, 'on_equip_status', '') == old \
            and getattr(fresh, 'on_equip_status', '') != old:
        item.on_equip_status = ''


# -------------------------------------------------------------- named pieces

# (metal, quiet, casting_free, wards: what a named body armour is made of and
# wards off, winning-build plan 3.3; gear reads them. template_basis: what it
# is built on, for its donning time (gear.don_turns); counters: what it
# blocks outright, the Aegis a gaze (counters.py). A piece pickled before
# those fields lacked them: bug bash WB-A09.)
_ARMOR_FIELDS = ('ac_bonus', 'ench_id', 'ench_level', 'tier', 'quiz_tier',
                 'equip_threshold', 'weight_class', 'ench_line', 'effects', 'tier_bonuses',
                 'metal', 'quiet', 'casting_free', 'wards', 'template_basis', 'counters',
                 'special', 'guards_nothing')
_ACC_FIELDS = ('effects', 'save_bonus', 'tier', 'quiz_tier', 'equip_threshold', 'tier_bonuses',
               'special', 'daimonion')


def _refresh_weapon(item) -> bool:
    """A named weapon takes only a status it has since been given to lend in
    the hand (the Shamshir-e Zomorrodnegar's magic resistance): its damage
    is the copy's own."""
    d = _named('weapon').get(getattr(item, 'id', '') or '')
    if not d:
        return False
    lends = d.get('on_equip_status', '') or ''
    if lends and not getattr(item, 'on_equip_status', ''):
        item.on_equip_status = lends
    return True


def refresh_named(item) -> bool:
    """Take a named piece's mechanical fields from today's data. True if it
    is a named armour piece, shield or accessory (whether or not anything
    moved)."""
    from items import Accessory, Armor, Shield, make_item_by_id
    from items import Weapon
    if isinstance(item, Weapon):
        return _refresh_weapon(item)
    if isinstance(item, Armor):
        cat = 'armor'
    elif isinstance(item, Shield):
        cat = 'shield'
    elif isinstance(item, Accessory):
        cat = 'accessory'
    else:
        return False
    iid = getattr(item, 'id', '') or ''
    defn = _named(cat).get(iid) or (_named_accessory(iid) if cat == 'accessory' else None)
    if not defn:
        return False
    fresh = make_item_by_id(cat, iid)
    if fresh is None:
        return False
    attuned = int(getattr(item, 'achieved_tier', 0) or 0) > 0
    if cat == 'accessory':
        # (An attuned item's tier ladder holds what it holds.)
        item.adopt_fields(fresh, [f for f in _ACC_FIELDS if not (f == 'tier_bonuses' and attuned)])
        item.__dict__.pop('surrounded_ac_bonus', None)
        return True
    import gear
    core = cat == 'shield' or getattr(fresh, 'slot', 'body') in gear.CORE_SLOTS
    chain = bool(getattr(fresh, 'equip_chain_mode', ''))
    # (An attuned or chain body piece's AC is its tier's.)
    item.adopt_fields(fresh, [f for f in _ARMOR_FIELDS
                              if not (f in ('ac_bonus', 'tier_bonuses') and (attuned or (core and chain)))])
    if not getattr(fresh, 'ench_id', ''):
        # Its data no longer gives it an enchantment, so the line saying what
        # one did goes too (the Duck of Doom's old Iron Will, 2026-11-16).
        item.__dict__.pop('ench_line', None)
    _retire_status(item, getattr(fresh, 'ench_id', ''), fresh)
    if not getattr(item, 'on_equip_status', '') and getattr(fresh, 'on_equip_status', ''):
        item.on_equip_status = fresh.on_equip_status
    for flag in ('passive_silent_walk',):
        if getattr(fresh, flag, False):
            setattr(item, flag, True)
    if core and not chain:
        # Its tier's plus, or a scroll's higher one (the same on every load).
        item.enchant_bonus = min(gear.core_enchant_cap(),
                                 max(int(fresh.enchant_bonus or 0),
                                     int(getattr(item, 'enchant_bonus', 0) or 0)))
    elif not core:
        item.enchant_bonus = 0
    return True


def refresh_kind(item) -> bool:
    """A common ring or amulet of a kind: its effects as today's data has
    them, with what its kind's ladder adds at its level (a stat kind's
    amount: rings.level_fields). True if it is one."""
    from items import Accessory, make_item_by_id
    import rings
    if not isinstance(item, Accessory) or getattr(item, 'is_unique', False)             or not rings.kind_of(item):
        return False
    fresh = make_item_by_id('accessory', getattr(item, 'id', '') or '')
    if fresh is None:
        return False
    item.effects = dict(getattr(fresh, 'effects', None) or {})
    lv = int(getattr(item, 'ench_level', 0) or 0)
    if lv > 0:
        item.effects = rings.level_fields(item, lv).get('effects', item.effects)
    return True


def _named_accessory(iid: str):
    """A named ring or amulet not flagged unique (the Ouroboros, the Ankh
    of Ra) or a plot one."""
    from paths import data_path
    try:
        with open(data_path('data', 'items', 'accessory.json'), encoding='utf-8') as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    e = d.get(iid)
    if isinstance(e, dict) and (e.get('plot_locked') or iid in ('ouroboros_pendant', 'ankh_of_ra')):
        return e
    return None


# ------------------------------------------------------------------- the load

def migrate(player, all_items) -> None:
    """Run once on load, after the composite recompose."""
    import copy
    worn = [w for w in _worn(player)]
    before = {id(w): _granted(w) for w in worn}
    fx_before = {id(w): copy.deepcopy(getattr(w, 'effects', None)) for w in worn}
    for it in all_items:
        try:
            enchant_common(it)
            refresh_named(it) or refresh_kind(it)
        except Exception:
            from game_log import log_error
            log_error(f"gear_saves: could not refresh {getattr(it, 'id', '?')}")
    after = {id(w): _granted(w) for w in worn}
    for w in worn:
        for st in before[id(w)] - after[id(w)]:
            player.drop_worn_status(st)
        for st in after[id(w)] - before[id(w)]:
            if player.status_effects.get(st) != -1:      # a timed one running too
                player.add_effect(st, -1)
    # The worn stats move only if what a worn piece lends moved (a save's
    # ledger is otherwise left exactly as it was).
    if any(getattr(w, 'effects', None) != fx_before[id(w)] for w in worn):
        try:
            player.sync_worn_stats()
        except Exception:
            from game_log import log_error
            log_error('gear_saves: sync_worn_stats failed on load')


def _worn(player):
    for slot in ('weapon', 'ranged_weapon', 'shield', 'amulet_slot', 'belt_slot'):
        it = getattr(player, slot, None)
        if it is not None:
            yield it
    for attr in ('armor_slots', 'accessory_slots'):
        for it in getattr(player, attr, None) or ():
            if it is not None:
                yield it
