"""What an item does, for every item item_words.py does not cover: gear's
and artifacts' own powers, food, ammunition, ingredients, lockpicks and
chests; and the resistance line in plain words.

Brandon's play-test of 3.6.1, 2026-11-22: "Same problem with spells and
scrolls with rings... Ring of Wizardry gets identified, has nothing useful in
mechanics, and no idea what it actually does; assume this problem persists
across many items." A census of every item, identified, found 37 of 41
artifacts saying "No revealed mechanics recorded.", the dossier's Mechanics
pane never showing a ring's power, and many named pieces whose power lives
only in code keyed by their id (Draupnir's gold, the Jade Cicada's saved
life). Both cards now read one list, RenderMixin._item_power_lines, and
this module writes the parts it could not:

  * a kind's own lines, data/ui/item_powers.json ``by_id[class][id]``:
    ``lines`` (a placeholder ``{field}`` is the item's own field, ``{field:pct}``
    a fraction as a whole percent, so a number never drifts from the data)
    and ``covers`` (the fields those lines already say);
  * food, ammunition, an ingredient, a lockpick, a chest: from their own
    fields and the systems that use them (kitchen, food_system);
  * ``resist_line``: a damage multiplier said as damage taken ("Takes 20%
    less slash"): the cards printed "Resists: slash 80%" for a piece that
    takes 80% of a cut.

Pure: no Game.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

_FIELD = re.compile(r'\{([A-Za-z_][A-Za-z0-9_]*)(?::(pct))?\}')
STAT_NAMES = {'STR': 'Strength', 'CON': 'Constitution', 'DEX': 'Dexterity',
              'INT': 'Intelligence', 'WIS': 'Wisdom', 'PER': 'Perception'}


@lru_cache(maxsize=1)
def data() -> dict:
    """data/ui/item_powers.json, read once ({} when it cannot be read)."""
    try:
        from paths import data_path
        with open(data_path('data', 'ui', 'item_powers.json'), encoding='utf-8') as f:
            got = json.load(f)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError, ImportError):
        return {}


def _get(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def class_of(item, item_class: str | None = None) -> str:
    """The item's data class ('weapon', 'accessory', 'artifact'...)."""
    if item_class:
        return str(item_class)
    ic = str(_get(item, 'item_class', '') or '')
    return ic or type(item).__name__.lower()


def own(item, item_class: str | None = None) -> dict:
    """The kind's own entry in the data, or {}."""
    by_id = data().get('by_id') or {}
    return dict((by_id.get(class_of(item, item_class)) or {}).get(str(_get(item, 'id', '') or '')) or {})


def covers(item, item_class: str | None = None) -> set:
    """The item's own fields its written lines already say."""
    return set(own(item, item_class).get('covers') or ())


class Unfilled(KeyError):
    """A placeholder names a field the item does not have."""


@lru_cache(maxsize=32)
def _kinds(item_class: str) -> dict:
    """data/items/<class>.json, read once ({} when there is none)."""
    try:
        from paths import data_path
        with open(data_path('data', 'items', f'{item_class}.json'), encoding='utf-8') as f:
            got = json.load(f)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError, ImportError):
        return {}


def field(item, key: str, item_class: str | None = None):
    """The item's own value for ``key``: on the copy, else in its kind's
    data entry (a weapon keeps only the fields the game reads through it;
    its Damocles count or its dragon dice are read from the data)."""
    v = _get(item, key, None)
    if v is None:
        entry = _kinds(class_of(item, item_class)).get(str(_get(item, 'id', '') or '')) or {}
        v = entry.get(key) if isinstance(entry, dict) else None
    return v


def fill(template: str, item, item_class: str | None = None) -> str:
    """A line with the item's own numbers put in: ``{field}`` as it is,
    ``{field:pct}`` a fraction as a whole percent (0.25 -> 25%)."""
    def one(m):
        key, fmt = m.group(1), m.group(2)
        v = field(item, key, item_class)
        if v is None:
            raise Unfilled(key)
        if fmt == 'pct':
            f = float(v)
            return f"{round(f * 100 if abs(f) <= 1 else f)}%"
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return str(v)
    return _FIELD.sub(one, str(template))


def own_lines(item, item_class: str | None = None) -> list:
    """The kind's own lines, filled. A line whose field is missing on this
    copy (an old save's) is left out rather than shown with a brace."""
    out = []
    for t in own(item, item_class).get('lines') or ():
        try:
            out.append(fill(t, item, item_class))
        except (Unfilled, TypeError, ValueError):
            continue
    return [s for s in out if s.strip()]


# ------------------------------------------------------------ chain tiers

_VALUE = re.compile(r'\{value(?::(pct|\+))?\}')


def chain_label(key: str, value) -> str:
    """A chain-equip tier bonus in plain words (``chain_bonus`` in the
    data: "Unseen in the dark..."), or '' when none is written. The cards
    printed the code key title-cased ("Stealth In Dark", "Mp Bonus")."""
    spec = (data().get('chain_bonus') or {}).get(str(key)) or {}
    label = spec.get('label') if isinstance(spec, dict) else spec
    if not label:
        return ''

    def one(m):
        fmt = m.group(1)
        try:
            f = float(value)
        except (TypeError, ValueError):
            return str(value)
        if fmt == 'pct':
            return f"{round(f * 100 if abs(f) <= 1 else f)}%"
        n = int(f) if f.is_integer() else f
        return f"{n:+}" if fmt == '+' else str(n)
    return _VALUE.sub(one, str(label))


# ------------------------------------------------------------ resistances

def resist_bits(profile: dict) -> tuple:
    """([(type, percent less)], [(type, percent more)]) from a damage
    multiplier profile, in the order the cards use."""
    less, more = [], []
    for k, v in (profile or {}).items():
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if abs(v - 1.0) < 1e-9:
            continue
        pct = round(abs(1.0 - v) * 100)
        if pct <= 0:
            continue
        (less if v < 1.0 else more).append((str(k).replace('_', ' '), pct))
    return less, more


def _join(words: list) -> str:
    if len(words) <= 1:
        return ''.join(words)
    return ', '.join(words[:-1]) + ' and ' + words[-1]


def _grouped(bits: list) -> str:
    """"slash and pierce 20%, fire 15%": types at one percent together."""
    order, by_pct = [], {}
    for kind, pct in bits:
        if pct not in by_pct:
            order.append(pct)
            by_pct[pct] = []
        by_pct[pct].append(kind)
    return ', '.join(f"{_join(by_pct[p])} {p}%" for p in order)


def resist_line(profile: dict) -> str:
    """'Takes less damage: slash and pierce 20%, fire 15%. Takes no cold
    damage. Takes more damage: lightning 25%.' ('' when the piece changes
    no damage)."""
    less, more = resist_bits(profile)
    none = [k for k, p in less if p >= 100]
    less = [(k, p) for k, p in less if p < 100]
    parts = []
    if less:
        parts.append(f"Takes less damage: {_grouped(less)}.")
    if none:
        parts.append(f"Takes no {_join(none)} damage.")
    if more:
        parts.append(f"Takes more damage: {_grouped(more)}.")
    return ' '.join(parts)


def resist_cell(profile: dict) -> str:
    """The Kit column's short form: 'slash -20%, pierce +15%' ('-' if none)."""
    less, more = resist_bits(profile)
    cells = [f"{k} -{p}%" for k, p in less] + [f"{k} +{p}%" for k, p in more]
    return ', '.join(cells) or '-'


# ------------------------------------------------------------ food

def stat_name(stat: str) -> str:
    return STAT_NAMES.get(str(stat or '').upper(), str(stat or '').title())


def food_bonus_line(item) -> str:
    """A food's own gift, in words (food_system._apply_bonus): '' for none."""
    bt = str(_get(item, 'bonus_type', 'none') or 'none')
    n = int(_get(item, 'bonus_amount', 0) or 0)
    if bt == 'none' or n == 0:
        return ''
    if bt == 'stat':
        return f"Eating it raises your {stat_name(_get(item, 'bonus_stat', ''))} by {n} for good."
    if bt == 'random_stat':
        return f"Eating it raises one stat, chosen by chance, by {n} for good."
    if bt == 'combat_stat':
        return f"Eating it raises your Strength or Constitution, by chance, by {n} for good."
    if bt == 'two_stats':
        return f"Eating it raises two stats, chosen by chance, by {n} each for good."
    if bt == 'all_stats':
        return f"Eating it raises every stat by {n} for good."
    if bt == 'status':
        from status_effects import EFFECT_INFO
        eff = str(_get(item, 'bonus_effect', '') or '')
        info = EFFECT_INFO.get(eff)
        name = info[0] if info else eff.replace('_', ' ').title()
        return f"Eating it gives you {name} for {n} turns."
    return ''


def food_bonus_cell(item) -> str:
    """The Kit column's short form of the gift: 'Wisdom +1', '1 stat +1'."""
    bt = str(_get(item, 'bonus_type', 'none') or 'none')
    n = int(_get(item, 'bonus_amount', 0) or 0)
    if bt == 'none' or n == 0:
        return ''
    return {'stat': f"{stat_name(_get(item, 'bonus_stat', ''))} +{n}",
            'random_stat': f"a stat +{n}", 'combat_stat': f"STR or CON +{n}",
            'two_stats': f"two stats +{n}", 'all_stats': f"every stat +{n}",
            'status': str(_get(item, 'bonus_effect', '') or '').replace('_', ' ')}.get(bt, '')


def food_cap_line(item) -> str:
    """The cap on what food teaches (food_system._apply_bonus), for a food
    that raises a stat."""
    if str(_get(item, 'bonus_type', 'none') or 'none') in ('stat', 'random_stat', 'combat_stat',
                                                          'two_stats', 'all_stats'):
        return "A stat stops rising once food has taught it all it can at your depth."
    return ''


def food_lines(item, player=None) -> list:
    """What a food does: what it restores and ends, its own gift, and what
    the kitchen does with it."""
    from food_system import food_sp, food_stops
    sp = food_sp(player, item)
    hp = int(_get(item, 'hp_restore', 0) or 0)
    parts = ([f"{sp} SP"] if sp else []) + ([f"{hp} HP"] if hp else [])
    out = []
    if parts:
        line = "Eaten, it restores " + ' and '.join(parts)
        ills = [str(e).replace('_', ' ') for e in food_stops(item)]
        line += f" and stops {_join(ills)}." if ills else "."
        out.append(line)
    for t in (food_bonus_line(item), food_cap_line(item)):
        if t:
            out.append(t)
    out += own_lines(item, 'food')
    out += _kitchen_lines(item)
    return out


def _dishes(n: int) -> str:
    return "1 dish calls for it" if n == 1 else f"{n} dishes call for it"


def _side_line(side, kitchen) -> str:
    """The side gift a part brings to a dish it is cooked in (a dish that
    makes food to carry gives none, kitchen.dish_sides)."""
    if side == 'heal':
        return "In a dish you cook, it adds a little healing."
    if side == 'mp':
        return "In a dish you cook, it adds a little mana."
    if side:
        return f"In a dish you cook, it adds {kitchen.power_label(side)} for a while."
    return ''


def _kitchen_lines(item) -> list:
    """What the kitchen does with a ration: how many dishes call for it, and
    the side gift it brings to a dish (unless its own lines say it, with
    the turns)."""
    try:
        import kitchen
    except ImportError:
        return []
    iid = str(_get(item, 'id', '') or '')
    out = []
    n = len(kitchen.dishes_with(iid))
    if n:
        out.append(f"Cooked (C): {_dishes(n)}.")
    if not own(item, 'food'):
        t = _side_line(kitchen.part_side(kitchen.resolve(iid)), kitchen)
        if t:
            out.append(t)
    return out


# ------------------------------------------------------------ ingredients

_NATURE = {'hp': "dishes that heal (the HP tab)",
           'sp': "filling dishes (the SP tab)",
           'mp': "dishes that restore mana (the MP tab)"}
_RAW_SP = {'universal': 12, 'family': 10, 'dungeon': 10, 'prime': 15, 'trophy': 20}


def ingredient_lines(item) -> list:
    """A harvested part or a foraged find: what its dishes do, its side
    gift, a trophy's one dish, and what eating it raw gives
    (food_system.eat_raw)."""
    try:
        import kitchen
    except ImportError:
        return []
    iid = kitchen.resolve(str(_get(item, 'id', '') or ''))
    ing = kitchen.ingredients().get(iid) or {}
    out = []
    nature = ing.get('nature') or _get(item, 'nature', '')
    if nature == 'stat':
        what = f"dishes that raise your {stat_name(ing.get('stat_grant', ''))} (the Stat tab)"
    elif nature == 'special':
        what = f"dishes that give {kitchen.power_label(ing.get('temp_power', ''))} (the Special tab)"
    else:
        what = _NATURE.get(nature, 'dishes')
    n = len(kitchen.dishes_with(iid))
    if ing.get('tier_role') == 'trophy' or _get(item, 'tier_role', '') == 'trophy':
        out += [str(t) for t in kitchen.trophy_warning_lines(item)]
    elif n:
        out.append(f"Cook it (C) into {what}: {_dishes(n)}.")
    else:
        out.append(f"Cook it (C) into {what}.")
    t = _side_line(kitchen.part_side(iid), kitchen)
    if t:
        out.append(t)
    raw = _get(item, 'raw_sp', None)
    if raw is None:
        raw = ing.get('raw_sp')
    sp = int(raw) if raw is not None else _RAW_SP.get(str(_get(item, 'tier_role', '') or ''), 5)
    safe = bool(_get(item, 'edible_safe', False) or ing.get('edible_safe')
                or iid == 'assorted_monster_parts')
    out.append(f"Eaten raw (U): {sp} SP." if safe else
               f"Eaten raw (U): {sp} SP, and a 30% chance of food poisoning.")
    out += own_lines(item, 'ingredient')
    return out


# ------------------------------------------------------------ the rest

def ammo_lines(item) -> list:
    """Arrows, bolts, shells: what each adds to a shot."""
    kind = str(_get(item, 'ammo_type', 'arrow') or 'arrow')
    plural = {'arrow': 'arrows', 'bolt': 'bolts', 'shell': 'shells'}.get(kind, kind + 's')
    bonus = int(_get(item, 'damage_bonus', 0) or 0)
    bow = {'arrow': 'a bow', 'bolt': 'a crossbow'}.get(kind, 'the weapon that fires them')
    if 'damage_bonus' in covers(item, 'ammo'):
        return own_lines(item, 'ammo')
    out = [f"Shot from {bow} (F): each adds {bonus} damage to the hit." if bonus else
           f"Shot from {bow} (F): plain {plural}, no damage added."]
    return out + own_lines(item, 'ammo')


def lockpick_lines(item) -> list:
    return own_lines(item, 'lockpick') or [
        "Press P with a chest beside you or under you: one economics question picks its "
        "lock. Right, it opens; wrong, its trap goes off and you get nothing."]


def container_lines(item) -> list:
    return own_lines(item, 'container') or [
        "A locked chest: press P beside it or standing on it to pick the lock (one economics "
        "question). Right, you take what is inside; wrong, its trap goes off and you get nothing."]


def treasure_lines(item, player=None) -> list:
    """A gem, jewellery, old coins, an art object: its worth, and what it
    is for (treasure.py)."""
    import treasure
    return [treasure.value_text(player, item) + '.',
            "Carried out, it counts toward your score. Any trader buys it near its worth "
            "or takes it as payment."] + own_lines(item, 'treasure')


def flask_lines(item, player=None) -> list:
    """A coating or a thrown flask (coatings.py): what it does on a blade
    and thrown."""
    import coatings
    return [str(t) for t in coatings.card_lines(item, player)] + own_lines(item, 'flask')


def lines(item, player=None, item_class: str | None = None) -> list:
    """What It Does for a class the gear cards do not build: food,
    ammunition, an ingredient, a lockpick, a chest, an artifact, treasure,
    a flask. [] for the rest (their lines come from the card itself plus
    ``own_lines``)."""
    cls = class_of(item, item_class)
    if cls == 'treasure':
        return treasure_lines(item, player)
    if cls == 'flask':
        return flask_lines(item, player)
    if cls == 'food':
        return food_lines(item, player)
    if cls == 'ingredient':
        return ingredient_lines(item)
    if cls == 'ammo':
        return ammo_lines(item)
    if cls == 'lockpick':
        return lockpick_lines(item)
    if cls == 'container':
        return container_lines(item)
    if cls == 'artifact':
        return own_lines(item, 'artifact')
    return []
