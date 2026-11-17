"""Armour, shield, ring and amulet rules (bug bash 3.3.2).

docs/design/ARMOR_REDESIGN_PLAN.md (revision 3), numbers proven by
tools/balance/armor_model.py, data in data/gear_rules.json.

  * An item is template x material x enchantment. The template says what it
    is (slot, weight class, base AC for body armour and shields, and on body
    armour the forms it turns: plate an edge, mail lets a point through),
    the material what can wear it (rust, acid, fire), its weight, its name
    and on body armour its elements (iron carries the spark, leather
    catches fire), and the enchantment (level 1-10, 0 = plain) its power:
    the tier (quiz tier) and the plus on body armour and shields. What the
    forms, the elements and the weight class do is the last section of this
    file, "What armour does beyond AC" (winning-build plan 3.3, 2026-11-13:
    until then the material gave "the weight and the wear, never
    protection").
  * AC comes from body armour, the shield and magic only (the defence model,
    2026-11-16: Dexterity is the dodge and the speed, src/defence.py). The
    body armour's weight class sets how much of the dodge is left (all
    light, half medium, none heavy) and what the armour costs in speed
    until Strength pays it back.
  * The floor decides only which level is likely to be found (bells); every
    magnitude is fixed per level (LORE NOT FLOOR).

Pure rules: no pygame, no game state.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache

CORE_SLOTS = ('body',)                    # armour slots that carry AC (with the shield)
MINOR_SLOTS = ('head', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt')
MAX_LEVEL = 10


@lru_cache(maxsize=1)
def rules() -> dict:
    from paths import data_path
    with open(data_path('data', 'gear_rules.json'), encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------ levels

def tier_for_level(level: int) -> int:
    """Tier I-V of an enchantment level (a plain piece is tier 1)."""
    level = int(level or 0)
    return max(1, min(5, (level + 1) // 2)) if level > 0 else 1


def plus_for_level(level: int) -> int:
    """The plus a level gives body armour or a shield: its tier (0 plain)."""
    return tier_for_level(level) if int(level or 0) > 0 else 0


def plain_share(floor: int) -> float:
    lv = rules()['levels']
    return max(lv['plain_end'], lv['plain_start'] - lv['plain_slope'] * (int(floor) - 1))


def level_weights(floor: int) -> list:
    """Relative chance of each level 1-10 on `floor` (sums to 1)."""
    lv = rules()['levels']
    f = int(floor)
    w = []
    for i in range(MAX_LEVEL):
        if f < lv['first'][i]:
            w.append(0.0)
            continue
        d = f - lv['peak'][i]
        w.append(math.exp(-(d * d) / (2 * lv['spread'] ** 2)))
    s = sum(w) or 1.0
    return [x / s for x in w]


def roll_level(floor: int, rng, plain_ok: bool = True) -> int:
    """A found piece's level on `floor`: 0 (plain) or 1-10."""
    if plain_ok and rng.random() < plain_share(floor):
        return 0
    r, acc = rng.random(), 0.0
    for i, x in enumerate(level_weights(floor), 1):
        acc += x
        if r <= acc:
            return i
    return MAX_LEVEL


# ----------------------------------------------------------- weight classes

def weight_class(template: dict) -> str:
    """light / medium / heavy, from the template's armor_class_tier."""
    c = str((template or {}).get('armor_class_tier') or 'light').lower()
    return c if c in ('light', 'medium', 'heavy') else 'light'


def weight_class_weight(cls: str, floor: int) -> float:
    peak, spread, first = rules()['weight_class_bells'][cls]
    f = int(floor)
    if f < first:
        return 0.0
    return math.exp(-((f - peak) ** 2) / (2 * spread ** 2))


def template_weight(template: dict, floor: int) -> float:
    """How likely this template is on `floor`. Body armour and shields carry
    their own bell (`spawn_bell`: [peak, spread, first floor, height?]), so each one
    arrives in its turn down the whole run, padded to full plate, buckler to
    tower; every other template goes by its weight class's bell."""
    bell = (template or {}).get('spawn_bell')
    if not bell:
        return weight_class_weight(weight_class(template), floor)
    # An optional fourth number is the template's height beside the others
    # (the mirror shield, a named counter, is rarer than a kite shield).
    peak, spread, first = bell[:3]
    height = float(bell[3]) if len(bell) > 3 else 1.0
    f = int(floor)
    if f < first:
        return 0.0
    return height * math.exp(-((f - peak) ** 2) / (2 * spread ** 2))


def pick_template(options, floor: int, rng):
    """(template id, template) from `options`, drawn by each template's bell
    (template_weight). Falls back to a uniform pick when none is due on this
    floor."""
    options = list(options)
    if not options:
        return None
    ws = [template_weight(t, floor) for _tid, t in options]
    tot = sum(ws)
    if tot <= 0:
        return rng.choice(options)
    r, acc = rng.random() * tot, 0.0
    for opt, x in zip(options, ws):
        acc += x
        if r <= acc:
            return opt
    return options[-1]


# --------------------------------------------------------------- threshold

def equip_threshold(weight_cls: str, level: int, unique: bool = False) -> int:
    """Armour and shields: complexity (weight class) + benefit (tier)."""
    t = rules()['threshold']
    n = t['complexity'].get(weight_cls, 1) + t['benefit_by_tier'][tier_for_level(level) - 1]
    if unique:
        n += t['unique']
    return max(1, min(t['max'], n))


def accessory_threshold(slot: str, level: int, unique: bool = False) -> int:
    """Rings, amulets, belts: complexity (slot) + benefit (tier)."""
    t = rules()['accessory_threshold']
    n = t['complexity'].get(slot, 1) + t['benefit_by_tier'][tier_for_level(level) - 1]
    if unique:
        n += t['unique']
    return max(1, min(t['max'], n))


def core_enchant_cap() -> int:
    return int(rules()['enchant_cap']['core'])


# ----------------------------------------------------------------- donning

@lru_cache(maxsize=2)
def _template_ids(category: str) -> tuple:
    """Every template id of a category ('armor' or 'shields'), longest first
    (so 'iron_full_plate' reads as full plate, not plate)."""
    import items
    try:
        ids = list(items.load_templates(category))
    except Exception:
        return ()
    return tuple(sorted(ids, key=len, reverse=True))


def template_of(item) -> str:
    """The template a piece is built on: its ``template_basis`` (a named
    piece, or a common one made since 2026-11-13), else read from a common
    piece's id ("{material}_{template}"). '' when there is none."""
    t = str(getattr(item, 'template_basis', '') or '')
    if t:
        return t
    iid = str(getattr(item, 'id', '') or '')
    cat = 'shields' if str(getattr(item, 'item_class', '')) == 'shield' else 'armor'
    for tid in _template_ids(cat):
        if iid == tid or iid.endswith('_' + tid):
            return tid
    return ''


def _piece_kind(item) -> str:
    """'body', 'shield', 'minor', 'accessory' or 'weapon' for donning."""
    cls = str(getattr(item, 'item_class', '') or '')
    if not cls:
        cls = {'Armor': 'armor', 'Shield': 'shield', 'Accessory': 'accessory',
               'Weapon': 'weapon'}.get(type(item).__name__, cls)
    if cls == 'shield':
        return 'shield'
    if cls == 'armor':
        return 'body' if str(getattr(item, 'slot', 'body')) in CORE_SLOTS else 'minor'
    if cls == 'weapon':
        return 'weapon'
    return 'accessory'


def don_turns(item, fast: bool = False) -> int:
    """Turns to put ``item`` on (gear_rules.json ``donning``): body armour by
    its weight class (light 1, medium 3, heavy 5), full plate 6; a shield,
    a minor piece, a ring, an amulet or a belt 1. ``fast`` (the Hephaestus
    quirk) halves it, rounded up."""
    d = rules()['donning']
    kind = _piece_kind(item)
    if kind == 'body':
        n = d['templates'].get(template_of(item))
        if n is None:
            cls = str(getattr(item, 'weight_class', '') or 'light')
            n = d['body'].get(cls, d['body']['light'])
    else:
        n = d.get(kind, 1)
    n = max(1, int(n))
    if fast:
        n = max(1, math.ceil(n * float(d['fast_share'])))
    return n


def doff_turns(item, fast: bool = False) -> int:
    """Turns to take ``item`` off: half its donning, rounded up (at least 1)."""
    d = rules()['donning']
    return max(1, math.ceil(don_turns(item, fast) * float(d['doff_share'])))


def named_ac_floor(kind: str, floor: int) -> int:
    """The least AC (base + plus) a named body armour (`kind` 'body') or
    shield ('shield') found by depth gives on `floor`: the common par there
    plus a margin (gear_rules.json `named_ac`, written by
    tools/balance/rebase_unique_armour.py). A legend is better than the
    plate the hero already wears. 0 when no table is written."""
    t = rules().get('named_ac')
    if not t:
        return 0
    par = t['par_' + kind]
    f = max(1, min(len(par), int(floor)))
    return int(round(float(par[f - 1]) + float(t['margin'][kind])))


def is_core(item) -> bool:
    """Does this piece carry AC: body armour or a shield."""
    cls = str(getattr(item, 'item_class', '') or '')
    if cls not in ('armor', 'shield'):
        # (A piece built without its class: read it from what it is.)
        cls = {'Armor': 'armor', 'Shield': 'shield'}.get(type(item).__name__, cls)
    if cls == 'shield':
        return True
    return cls == 'armor' and str(getattr(item, 'slot', 'body')) in CORE_SLOTS


def ac_value(item) -> int:
    """The AC a piece gives: body armour and shields their base plus their
    plus; a minor piece, ring or amulet none."""
    if not is_core(item):
        return 0
    return int(getattr(item, 'ac_bonus', 0) or 0) + int(getattr(item, 'enchant_bonus', 0) or 0)


def level_for_tier(tier: int, greater: bool = False) -> int:
    """The level of a tier's lesser (or greater) form."""
    t = max(1, min(5, int(tier or 1)))
    return 2 * t if greater else 2 * t - 1


def loot_split() -> dict:
    return {k: float(v) for k, v in rules()['loot_split'].items() if not k.startswith('_')}


def pick_gear_class(rng) -> str:
    """'weapon', 'armor' or 'shield' for a find of common gear, by the loot
    split (45 / 45 / 10)."""
    split = loot_split()
    r, acc = rng.random() * sum(split.values()), 0.0
    for cls, w in split.items():
        acc += w
        if r <= acc:
            return cls
    return 'weapon'


def wears_flag(holder, flag: str) -> bool:
    """Any worn ring, amulet, belt or armour piece of ``holder`` with ``flag``
    set (the Hand of Glory's silent walk on a ring, Elvenkind's on boots).
    Reads attributes only, so a monster's or a test's stand-in works too."""
    worn = list(getattr(holder, 'equipped_accessories', None) or ())
    worn += [a for a in (getattr(holder, 'armor_slots', None) or ()) if a is not None]
    return any(getattr(it, flag, False) for it in worn)


# =================================================================
# What armour does beyond AC (winning-build plan 3.3, slice 4, 2026-11-13)
# =================================================================
# Every number is data:
#
# * the TEMPLATE (how a body armour is built; the tower shield too) sets the
#   physical forms: plate turns an edge, mail parts under a point, quilting
#   soaks a blow (data/templates/armor/*.json and shields/*.json `forms`);
# * the MATERIAL of a body armour sets the elements and the specials: iron
#   carries the spark, leather and cloth catch fire, dragonscale sheds
#   flame, cold iron wards off fey glamour (data/materials/armor/*.json
#   `protection`, `metal`, `quiet`, `casting_free`, `wards`; written with
#   their lore and their price by tools/content/armour_profiles_2026_11.py);
# * the body armour's WEIGHT CLASS sets how well the hero dodges, how far
#   his footsteps carry and what a spell costs in metal (data/gear_rules.json
#   `armour_weight`), and what it costs in speed until Strength pays it back
#   (`defence`, src/defence.py); the load he carries is `load`,
#   Player.load_tier.
#
# A NAMED piece keeps its own resistances (data/items/armor.json and
# shield.json `damage_resistances`): its JSON wins, and its template and
# material add nothing to it. Its weight class still comes from its
# template, and whether it is metal from its own `metal`.
#
# `worn_factor` is THE place a hero's armour meets a typed blow
# (Player.get_armor_resistance calls it from take_damage, beside the hero's
# own resistances). Anything else worn armour should do to a damage type (a
# trader's lining on a cloak or shirt) belongs in `piece_profile`, so every
# reader (the damage, the cards, the simulator) sees it.
#
# Works on a stand-in hero or item (attributes only, getattr with defaults).
FORMS = ('slash', 'pierce', 'blunt')
WEIGHT_CLASSES = ('light', 'medium', 'heavy')
METAL_CLASSES = frozenset({'metal', 'rare_metal', 'magical_metal', 'exotic_metal'})
_ORDER = ('slash', 'pierce', 'blunt', 'fire', 'cold', 'lightning', 'acid', 'poison',
          'drain', 'necrotic', 'shadow', 'magic', 'holy', 'psionic')


def armour_rules() -> dict:
    """data/gear_rules.json `armour_weight`."""
    return rules()['armour_weight']


def ward_rules() -> dict:
    return {k: v for k, v in (rules().get('wards') or {}).items() if not k.startswith('_')}


# ------------------------------------------------------------------ pieces

def _item_cls(item) -> str:
    cls = str(getattr(item, 'item_class', '') or '')
    if cls in ('armor', 'shield'):
        return cls
    return {'Armor': 'armor', 'Shield': 'shield'}.get(type(item).__name__, cls)


def is_shield(item) -> bool:
    return item is not None and _item_cls(item) == 'shield'


def is_body(item) -> bool:
    return item is not None and _item_cls(item) == 'armor' and str(getattr(item, 'slot', '')) == 'body'


def is_named(item) -> bool:
    return bool(getattr(item, 'is_unique', False))


def piece_template(item) -> dict:
    """The template a piece is built on ({} when none is known)."""
    import items
    tid = template_of(item)
    if not tid:
        return {}
    return items.get_template('shields' if is_shield(item) else 'armor', tid) or {}


def piece_material(item) -> dict:
    """A piece's material file ({} for a named piece's own word, "legendary")."""
    import items
    mid = str(getattr(item, 'material', '') or '')
    if not mid:
        return {}
    m = items.get_material('armor', mid)
    if m is None and is_shield(item):
        m = items.get_material('weapons', mid)
    return m or {}


def template_forms(item) -> dict:
    """The physical forms a body armour's or shield's build turns or lets
    through: {'slash': 0.75, 'pierce': 1.15} for mail."""
    if not (is_body(item) or is_shield(item)):
        return {}
    return {str(k): float(v) for k, v in (piece_template(item).get('forms') or {}).items()}


def material_protection(item) -> dict:
    """The elements and forms a BODY armour's material turns or lets
    through: {'lightning': 1.25} for iron. A shield is held, not worn: its
    material gives its weight and its wear only."""
    if not is_body(item):
        return {}
    return {str(k): float(v) for k, v in (piece_material(item).get('protection') or {}).items()}


def piece_profile(item) -> dict:
    """{damage type: multiplier} for one worn piece: a named piece's own
    resistances; a common one's own (none, unless something gave it some)
    times its template's forms and its material's elements; and, on either,
    a lining against one element."""
    if item is None:
        return {}
    own = {str(k): float(v) for k, v in (getattr(item, 'damage_resistances', None) or {}).items()}
    out = dict(own)
    if not is_named(item):
        for part in (template_forms(item), material_protection(item)):
            for k, v in part.items():
                out[k] = out.get(k, 1.0) * v
    # A trader's lining on a cloak or shirt (smithing.py, slice 6), on a
    # named piece as on a common one: here, so the damage and the Kit's
    # resistance column read the same number (bug bash WB-A08).
    try:
        import smithing
        el = smithing.lining_of(item)
        if el:
            out[el] = out.get(el, 1.0) * float(smithing.LINING_MULT)
    except Exception:
        pass
    return out


def worn_pieces(player) -> list:
    """The armour pieces and the shield the hero has on."""
    out = [a for a in (getattr(player, 'armor_slots', None) or ()) if a is not None]
    sh = getattr(player, 'shield', None)
    if sh is not None:
        out.append(sh)
    return out


def worn_factor(player, damage_type: str) -> float:
    """What the hero's worn armour does to a blow of `damage_type`: the
    product of every worn piece's profile (1.0 when nothing answers it)."""
    mult = 1.0
    for piece in worn_pieces(player):
        mult *= piece_profile(piece).get(damage_type, 1.0)
    return mult


# ------------------------------------------------------ the body armour

def body_armour(player):
    """The body armour the hero wears, or None (a piece still being put on
    is not worn yet: game_dressing leaves its slot empty)."""
    for a in getattr(player, 'armor_slots', None) or ():
        if a is not None and str(getattr(a, 'slot', '')) == 'body':
            return a
    return None


def piece_weight_class(item) -> str:
    """light / medium / heavy of a piece (no piece is light)."""
    if item is None:
        return 'light'
    c = str(getattr(item, 'weight_class', '') or '').lower()
    if c not in WEIGHT_CLASSES:
            c = weight_class(piece_template(item))
    return c


def body_class(player) -> str:
    return piece_weight_class(body_armour(player))


def is_metal(item) -> bool:
    """Does the piece clank and tax a spell? Its own word (a named piece's
    `metal`), else its material file's, else its template's materials."""
    if item is None:
        return False
    own = getattr(item, 'metal', None)
    if own is not None:
        return bool(own)
    if not is_named(item):
        m = piece_material(item)
        if 'metal' in m:
            return bool(m['metal'])
        if m:
            return str(m.get('material_class', '')) in METAL_CLASSES
    classes = set(piece_template(item).get('compatible_material_classes') or ())
    return bool(classes & METAL_CLASSES) and classes <= METAL_CLASSES | {'dragon_material'}


def _flag(item, name: str) -> bool:
    own = getattr(item, name, None)
    if own is not None:
        return bool(own)
    if is_named(item):
        return False
    return bool(piece_material(item).get(name, False))


def is_quiet(item) -> bool:
    """A metal that makes no sound (mithril): no clank on the footsteps."""
    return item is not None and _flag(item, 'quiet')


def casts_freely(item) -> bool:
    """A metal a caster can work in (mithril, orichalcum): no spell tax."""
    return item is not None and _flag(item, 'casting_free')


def class_dodge_share(item) -> float:
    return float(armour_rules()['dodge_share'].get(piece_weight_class(item), 1.0))


def dodge_share(player) -> float:
    """The share of the hero's dodge still there: by the body armour's
    weight class (full, half, none), times the load's (Player.load_tier)."""
    share = class_dodge_share(body_armour(player))
    load = getattr(player, 'load_dodge_share', None)
    if callable(load):
        try:
            share *= float(load())
        except Exception:
            pass
    return share


def piece_footsteps(item) -> int:
    """Tiles further footsteps carry in this body armour: medium +1, heavy
    +2, metal +1 more unless it is quiet."""
    r = armour_rules()
    n = int(r['footsteps'].get(piece_weight_class(item), 0))
    if item is not None and is_metal(item) and not is_quiet(item):
        n += int(r.get('metal_footsteps', 0))
    return n


def footstep_tiles(player) -> int:
    return piece_footsteps(body_armour(player))


def sleeper_factor(player) -> float:
    """How much readier a deep sleeper is to stir at the hero's step in his
    armour (sleepers.factor): 1 + share per footstep tile."""
    return 1.0 + footstep_tiles(player) * float(armour_rules().get('sleeper_share_per_tile', 0.0))


def piece_casting_mult(item) -> float:
    if item is None or not is_metal(item) or casts_freely(item):
        return 1.0
    return float(armour_rules()['casting_mult'].get(piece_weight_class(item), 1.0))


def casting_mult(player) -> float:
    """What a spell's mana costs in the body armour worn: x1 out of metal,
    x1.5 medium metal, x2 heavy metal; mithril and the like cast freely."""
    return piece_casting_mult(body_armour(player))


def spell_cost(player, cost: int) -> int:
    """A spell's mana in the armour worn (rounded up; never under 1 for a
    spell that costs anything)."""
    cost = int(cost or 0)
    if cost <= 0:
        return cost
    m = casting_mult(player)
    if m == 1.0:
        return cost
    return max(1, int(math.ceil(cost * m - 1e-9)))


# ------------------------------------------------------------------- wards

def piece_wards(item) -> list:
    if item is None:
        return []
    own = getattr(item, 'wards', None)
    if own is not None:
        return list(own)
    if is_named(item) or not is_body(item):
        return []
    return list(piece_material(item).get('wards') or ())


def ward_against(player, source, effect_id: str):
    """(piece, ward) when the body armour's material stops this rider from
    this attacker outright (cold iron and the fair folk's glamour,
    dragonscale and the flames), else None."""
    body = body_armour(player)
    wards = piece_wards(body)
    if not wards or not effect_id:
        return None
    defs = ward_rules()
    fam = str(getattr(source, 'family', '') or '')
    tags = set(getattr(source, 'tags', None) or ())
    for w in wards:
        d = defs.get(w)
        if not d or effect_id not in (d.get('effects') or ()):
            continue
        fams, wtags = set(d.get('families') or ()), set(d.get('tags') or ())
        if (fams or wtags) and fam not in fams and not (tags & wtags):
            continue
        return body, d
    return None


def ward_line(player, piece, ward: dict) -> str:
    try:
        from hud_context import item_bare_name
        name = item_bare_name(player, piece)
    except Exception:
        name = str(getattr(piece, 'name', 'armour'))
    return str(ward.get('line', 'Your {piece} turns it aside.')).format(piece=name)


# ------------------------------------------------------------- card text

def _x(v: float) -> str:
    return "x" + (f"{float(v):.2f}".rstrip('0').rstrip('.'))


def _phrase(word: str, kind: str, v: float) -> str:
    import re
    if word and re.search(rf"\b{re.escape(kind)}\b", word):
        return f"{word} {_x(v)}"
    if word:
        return f"{word}: {kind} {_x(v)}"
    return f"{kind} {_x(v)}"


def _ordered(d: dict) -> list:
    return sorted(d.items(), key=lambda kv: (_ORDER.index(kv[0]) if kv[0] in _ORDER else 99, kv[0]))


def protection_line(item) -> str:
    """One honest line: what a common body armour's (or a tower shield's)
    build and material do to a blow, and what its material stops:
    "Turns an edge: slash x0.75; parts under a point: pierce x1.15;
    conducts lightning x1.25; cold iron: fey glamour slides off".
    '' for a named piece (its card shows its own resistances) and for a
    piece that does nothing to a blow."""
    if item is None or is_named(item) or not (is_body(item) or is_shield(item)):
        return ''
    parts = []
    # One entry a damage type, at the number that is really applied (the
    # build's and the material's together), in the build's words where it
    # has some, else the material's.
    words = dict(piece_material(item).get('protection_words') or {}) if is_body(item) else {}
    words.update(piece_template(item).get('forms_words') or {})
    for k, v in _ordered(piece_profile(item)):
        if abs(v - 1.0) > 1e-9:
            parts.append(_phrase(str(words.get(k, '')), k, v))
    if is_body(item):
        defs = ward_rules()
        for w in piece_wards(item):
            card = (defs.get(w) or {}).get('card')
            if card:
                parts.append(str(card))
    if not parts:
        return ''
    line = '; '.join(parts)
    return line[:1].upper() + line[1:]


def wear_words(item) -> list:
    """What wear can do to the piece, by the one wear rule
    (status_effects): 'rusts', 'scorches'; a metal that cannot rust says so."""
    try:
        import status_effects as se
    except Exception:
        return []
    out = []
    try:
        if se._can_rust(item):
            out.append('rusts')
        elif is_metal(item):
            out.append('never rusts')
        if se._can_scorch(item):
            out.append('scorches')
    except Exception:
        pass
    return out


def speed_words(item) -> str:
    """What the body armour costs in speed, for its card: 'full speed' in
    light armour, else 'slower below Strength 16' (the Strength that pays
    its drag back: defence.fit_strength). '' for anything but body armour."""
    if not is_body(item):
        return ''
    import defence
    cls = piece_weight_class(item)
    fit = defence.fit_strength(cls)
    return 'full speed' if fit <= 10 else f"slower below Strength {fit}"


def weight_line(item) -> str:
    """The body armour's weight-class line for its card: "Heavy metal:
    slower below Strength 16, no dodge, footsteps +3, spells cost x2 MP;
    rusts." '' for anything but body armour."""
    if not is_body(item):
        return ''
    cls = piece_weight_class(item)
    metal = is_metal(item)
    bits = [speed_words(item)]
    share = class_dodge_share(item)
    bits.append('full dodge' if share >= 1.0 else ('no dodge' if share <= 0.0 else 'half dodge'))
    steps = piece_footsteps(item)
    if steps:
        bits.append(f"footsteps +{steps}")
    elif metal and is_quiet(item):
        bits.append('silent')
    if metal:
        m = piece_casting_mult(item)
        if m > 1.0:
            bits.append(f"spells cost {_x(m)} MP")
        elif casts_freely(item):
            bits.append('spells at full cost')
    head = cls.title() + (' metal' if metal else '')
    line = f"{head}: {', '.join(bits)}"
    wear = wear_words(item)
    if wear:
        line += '; ' + ', '.join(wear)
    return line + '.'


def card_lines(item) -> list:
    """The protection line and the weight-class line, whichever apply."""
    return [s for s in (protection_line(item), weight_line(item)) if s]
