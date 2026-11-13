"""The smith's and the armourer's new work (winning build 3.5, 2026-11-13):
re-shaping a weapon, a silver or cold-iron inlay, a lining against one
element, and the special order. Pure rules on plain items: no pygame, no
Game. game_traders.py sells them as services; domain_counters.py uses the
weapon maker and the lining for a stall's counters.

* **Reforge**: a common weapon re-shaped into another common template of the
  SAME material (a longsword into a mace). The material, the plus, the
  blessing or curse, the smith's work, the wear and any inlay are kept; the
  new template's hands, forms, chain and weight apply. The answer to "a
  spare weapon goes stale": the silver blade stays silver.
* **Inlay**: silver or cold iron worked into a common weapon. The substance
  joins the weapon's ``damage_types``, which is what the bane rule reads
  (combat.weapon_type_multiplier), so a silvered sword meets a werewolf as a
  silver one does. One substance per weapon, for good; the name shows it.
* **Lining**: a worn cloak or shirt lined against fire, cold, lightning or
  poison: that element's damage x0.75 while it is worn
  (Player.get_armor_resistance reads ``lining_mult``). One lining per piece.
  It is its own ``lining`` field, never ``damage_resistances`` (an old-save
  migration clears that field on common pieces).
* **Special order**: a common piece of a material and template from the
  armourer's line, made while the hero goes on down and handed over at the
  armourer's next stall (traders.next_stall).

The names and lines live in data/traders.json (``inlays``, ``linings``);
the prices in economy.SERVICE_SHARE.
"""
from __future__ import annotations

from functools import lru_cache

LINING_MULT = 0.75
LINING_ELEMENTS = ('fire', 'cold', 'lightning', 'poison')
LINING_SLOTS = ('cloak', 'shirt')
INLAY_SUBSTANCES = ('silver', 'cold_iron')
ORDER_CATS = ('weapon', 'armor', 'shield')


def _data(key: str) -> dict:
    import traders
    return traders.data().get(key) or {}


# ------------------------------------------------------------ common weapons

def template_of(item) -> str | None:
    """The common template a weapon (or armour piece) is built on, or None
    for a unique or a legacy piece."""
    from items import get_template
    if getattr(item, 'is_unique', False):
        return None
    ic = getattr(item, 'item_class', '')
    if ic == 'armor':
        tid = getattr(item, 'template_basis', None)
        return tid if tid and get_template('armor', tid) else None
    if ic == 'shield':
        tid = getattr(item, 'template_basis', None)
        if tid and get_template('shields', tid):
            return tid
    mat = str(getattr(item, 'material', '') or '')
    iid = str(getattr(item, 'id', '') or '')
    if not mat or not iid.startswith(mat + '_'):
        return None
    tid = iid[len(mat) + 1:]
    cat = 'shields' if ic == 'shield' else 'weapons'
    return tid if get_template(cat, tid) else None


def is_common_weapon(w) -> bool:
    """A smith's kind of weapon: common (material + template), not a named
    blade, not bound to the hand."""
    from items import load_materials
    if w is None or getattr(w, 'item_class', '') != 'weapon':
        return False
    if getattr(w, 'is_unique', False) or getattr(w, 'bound_to_wielder', False):
        return False
    return str(getattr(w, 'material', '')) in load_materials('weapons') and template_of(w) is not None


def _accepts(tpl: dict, mat: dict) -> bool:
    accepts = set(tpl.get('compatible_material_classes') or ())
    cls = set(str(mat.get('material_class', '')).split(',')) | {mat.get('material_class', '')}
    return not accepts or bool(accepts & cls)


def melee_templates(mat: dict, form: str | None = None, only_form: bool = False) -> list:
    """Melee weapon templates (no ammunition) that take material ``mat``,
    those of ``form`` only when one is asked for. ``only_form``: prefer the
    templates whose only form it is (a mace for blunt, a rapier for pierce)."""
    from items import load_templates
    out = []
    for tid, t in sorted(load_templates('weapons').items()):
        if t.get('requires_ammo') or not _accepts(t, mat):
            continue
        if form and form not in (t.get('damage_types') or ()):
            continue
        out.append(tid)
    if form and only_form:
        pure = [tid for tid in out
                if list(load_templates('weapons')[tid].get('damage_types') or ()) == [form]]
        return pure or out
    return out


def common_weapon(level: int, rng, *, form: str | None = None, material: str | None = None,
                  any_depth: bool = False, only_form: bool = False):
    """A common melee weapon for floor ``level``: of ``material`` (None when
    that material is not found this deep, unless ``any_depth``) or a material
    the floor's loot would roll, in a template of ``form`` when asked."""
    from items import instantiate_weapon, load_materials, material_spawn_weight
    mats = load_materials('weapons')
    if material:
        m = mats.get(material)
        if m is None or (not any_depth and material_spawn_weight(m, int(level)) <= 0):
            return None
        mid = material
    else:
        weighted = [(mid, material_spawn_weight(m, int(level))) for mid, m in sorted(mats.items())]
        weighted = [(mid, w) for mid, w in weighted
                    if w > 0 and melee_templates(mats[mid], form)]
        if not weighted:
            return None
        total = sum(w for _, w in weighted)
        r, acc, mid = rng.random() * total, 0.0, weighted[-1][0]
        for k, w in weighted:
            acc += w
            if r <= acc:
                mid = k
                break
    tids = melee_templates(mats[mid], form, only_form=only_form)
    if not tids:
        return None
    try:
        return instantiate_weapon(rng.choice(tids), mid)
    except ValueError:
        return None


# ------------------------------------------------------------------ reforge

def reforge_targets(w, shield_worn: bool = False) -> list:
    """The templates a smith can re-shape ``w`` into (template ids): every
    other melee template its material takes. Not a two-hander while a
    shield is on the arm, and nothing for a bow or a named blade."""
    from items import get_material, load_templates
    if not is_common_weapon(w) or getattr(w, 'requires_ammo', None):
        return []
    mat = get_material('weapons', w.material)
    here = template_of(w)
    out = []
    for tid in melee_templates(mat):
        if tid == here:
            continue
        if shield_worn and int(load_templates('weapons')[tid].get('hands', 1) or 1) >= 2:
            continue
        out.append(tid)
    return out


def preview(w, tid: str):
    """The weapon ``w`` would become as template ``tid`` (a fresh copy, for
    the picker; ``w`` itself is not touched)."""
    import copy
    out = copy.deepcopy(w)
    reforge(out, tid)
    return out


def reforge(w, tid: str) -> None:
    """Re-shape ``w`` in place into template ``tid`` of its own material.
    What the template decides changes (id, name, forms, hands, chain,
    weight, base damage, the class's mechanic); everything that is the
    piece's own history stays: plus, blessing, smith's work, wear, inlay,
    what was paid, what the hero knows of it."""
    from items import instantiate_weapon
    old_tid = template_of(w)
    if old_tid is None or tid == old_tid:
        return
    was = instantiate_weapon(old_tid, w.material)
    new = instantiate_weapon(tid, w.material)
    a, b = was.__dict__, new.__dict__
    for key in set(a) | set(b):
        if key in ('x', 'y'):
            continue
        if a.get(key, _MISSING) == b.get(key, _MISSING):
            continue                     # not the template's to decide
        if key in b:
            setattr(w, key, b[key] if not isinstance(b[key], list) else list(b[key]))
        elif key in w.__dict__:
            delattr(w, key)
    sub = getattr(w, 'inlay', None)
    if sub and sub not in w.damage_types:
        w.damage_types = list(w.damage_types) + [sub]
    _name_inlay(w)


_MISSING = object()


# ------------------------------------------------------------------ inlay

def inlay_of(w) -> str | None:
    return getattr(w, 'inlay', None) or None


def can_inlay(w, sub: str) -> bool:
    """May a smith work ``sub`` into ``w``? A common weapon with no inlay yet,
    not already of that substance."""
    if sub not in INLAY_SUBSTANCES or not is_common_weapon(w) or inlay_of(w):
        return False
    return sub != str(getattr(w, 'material', '')) and sub not in (w.damage_types or ())


def inlay_name(sub: str) -> str:
    return str((_data('inlays').get(sub) or {}).get('name', sub.replace('_', ' ')))


def _name_inlay(w) -> None:
    """Put the inlay's word on the weapon's names, once."""
    sub = inlay_of(w)
    if not sub:
        return
    prefix = str((_data('inlays').get(sub) or {}).get('prefix', '')).strip()
    if not prefix:
        return
    for attr in ('name', 'unidentified_name'):
        v = str(getattr(w, attr, '') or '')
        if v and not v.startswith(prefix + ' '):
            setattr(w, attr, f"{prefix} {v}")


def inlay(w, sub: str) -> bool:
    """Work ``sub`` into ``w`` for good. True when done."""
    if not can_inlay(w, sub):
        return False
    w.inlay = sub
    w.damage_types = list(w.damage_types or ()) + [sub]
    _name_inlay(w)
    return True


# ------------------------------------------------------------------ lining

def lining_of(piece) -> str | None:
    return getattr(piece, 'lining', None) or None


def can_line(piece) -> bool:
    return (piece is not None and getattr(piece, 'item_class', '') == 'armor'
            and str(getattr(piece, 'slot', '')) in LINING_SLOTS and not lining_of(piece))


def line(piece, element: str) -> bool:
    """Line ``piece`` against ``element``. True when done."""
    if element not in LINING_ELEMENTS or not can_line(piece):
        return False
    piece.lining = element
    return True


def lining_targets(player) -> list:
    """[(piece, element)]: every worn cloak or shirt with no lining yet,
    once for each element it could be lined against."""
    from items import ARMOR_SLOTS
    slots = list(getattr(player, 'armor_slots', None) or ())
    out = []
    for s in LINING_SLOTS:
        i = ARMOR_SLOTS.index(s)
        piece = slots[i] if i < len(slots) else None
        if can_line(piece):
            out += [(piece, e) for e in LINING_ELEMENTS]
    return out


def lining_mult(player, damage_type: str) -> float:
    """What the linings the hero wears do to ``damage_type``: x0.75 for each
    worn piece lined against it."""
    mult = 1.0
    for piece in getattr(player, 'armor_slots', None) or ():
        if piece is not None and lining_of(piece) == damage_type:
            mult *= LINING_MULT
    return mult


def lining_words(element: str) -> dict:
    return _data('linings').get(element) or {'name': element.title(), 'stuff': element}


def work_lines(item) -> list:
    """The smith's work on ``item``, as card lines (the hero paid for it and
    watched it done, so it shows whether the piece is identified or not)."""
    out = []
    sub = inlay_of(item)
    if sub:
        d = _data('inlays').get(sub) or {}
        out.append(str(d.get('card') or f"Inlaid with {inlay_name(sub)}."))
    el = lining_of(item)
    if el:
        w = lining_words(el)
        pct = int(round((1 - LINING_MULT) * 100))
        out.append(f"Lined with {w.get('stuff', el)}: {el} does {pct}% less harm "
                   f"to you while you wear it.")
    return out


# ------------------------------------------------------------ special order

def _materials(cat: str) -> dict:
    from items import load_materials
    return load_materials('weapons' if cat == 'weapon' else 'armor')


def _templates(cat: str) -> dict:
    from items import load_templates
    return load_templates({'weapon': 'weapons', 'armor': 'armor', 'shield': 'shields'}[cat])


def order_templates(cat: str, mid: str) -> list:
    """Template ids of ``cat`` that take material ``mid`` (weapons: melee and
    ranged alike; a smith makes a bow as readily as a blade)."""
    return list(_order_templates(cat, mid))


@lru_cache(maxsize=512)
def _order_templates(cat: str, mid: str) -> tuple:
    mat = _materials(cat).get(mid)
    if mat is None:
        return ()
    if cat == 'shield':
        applies = mat.get('applies_to')
        if applies and 'shield' not in applies:
            return ()
    return tuple(tid for tid, t in sorted(_templates(cat).items()) if _accepts(t, mat))


def order_materials(level: int) -> list:
    """[(cat, material id)] a special order can be made in on floor
    ``level``: what the floor's own loot could be made of, in every line
    the material takes."""
    return list(_order_materials(int(level)))


@lru_cache(maxsize=128)
def _order_materials(level: int) -> tuple:
    from items import material_spawn_weight
    out = []
    for cat in ORDER_CATS:
        for mid, m in sorted(_materials(cat).items(), key=lambda kv: (
                int(kv[1].get('tier', 1) or 1), kv[0])):
            if material_spawn_weight(m, int(level)) > 0 and order_templates(cat, mid):
                out.append((cat, mid))
    return tuple(out)


def material_name(cat: str, mid: str) -> str:
    from naming import proper_name
    m = _materials(cat).get(mid) or {}
    return proper_name(str(m.get('name', mid.replace('_', ' '))))


def make_order(cat: str, tid: str, mid: str):
    """The piece a special order makes: plain (no enchantment level), sound
    (never cursed, and the hero knows it), made to the hero's word."""
    from items import instantiate_armor, instantiate_shield, instantiate_weapon
    try:
        if cat == 'weapon':
            it = instantiate_weapon(tid, mid)
        elif cat == 'armor':
            it = instantiate_armor(tid, mid, level=0)
        else:
            it = instantiate_shield(tid, mid, level=0)
    except ValueError:
        return None
    it.buc = 'uncursed'
    it.buc_known = True
    if hasattr(it, 'id_level'):
        it.id_level = 5
    it.identified = True
    return it
