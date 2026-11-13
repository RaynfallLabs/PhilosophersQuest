"""Stock that knows what's below (winning build 3.5, Brandon 2026-11-13:
"the dungeon needs to SUPPORT this through the merchants and altars").

A trader trades in the floors at and just below his stall. This module reads
what walks there from the spawn data, at run time, and finds:

  * **the weaknesses** those kinds share, commonest first: a form (blunt,
    pierce, slash), a substance (silver, cold iron), holy, or an element a
    wand or a book can carry (fire, cold, lightning). A form, a substance and
    holy are measured through the real bane rule
    (``combat.weapon_type_multiplier``) on a probe weapon, so whatever the
    monster data and the multiplier say today is what counts here;
  * **the elements** they attack with (fire, cold, lightning, poison), so a
    stall can offer a guard as well.

``stall_counters`` then makes the wares: for each need, in order, the first
offer the trader's own line can supply (data/traders.json ``counters``): a
mace where skeletons walk, a silver blade where the shapechangers hunt, a
cloak lined against fire where fire breathes, a resistance draught at the
apothecary. The trader says one line about it when his stall opens.

Nothing here identifies anything: a consumable counter (a wand, a potion, a
book) goes on the shelf unmarked, and the line names only what to look for
("you'll want fire"). A piece of gear whose use shows on it (a mace's head, a
lining's stitching, a blessing the trader vouches for) is marked as set out
for what walks below.

Pure: no pygame, no Game. traders.build_stock calls it.
"""
from __future__ import annotations

from functools import lru_cache
from types import SimpleNamespace

# Weakness kinds measured by probing the bane rule with a weapon.
FORMS = ('blunt', 'pierce', 'slash')
MELEE_FORMS = FORMS


def config() -> dict:
    import traders
    return traders.data().get('counters') or {}


def _span() -> int:
    return max(0, int(config().get('span', 4) or 4))


@lru_cache(maxsize=128)
def _floor_kinds(level: int) -> tuple:
    """((kind, weight, defn), ...) for one floor's ordinary spawn pool, each
    weight a share of the floor (the shares add to one)."""
    try:
        from dungeon import _build_spawn_pool
        pool = _build_spawn_pool(int(level))
    except Exception:
        return ()
    total = sum(float(v.get('_spawn_freq', 0) or 0) for v in pool.values())
    if total <= 0:
        return ()
    return tuple((k, float(v.get('_spawn_freq', 0) or 0) / total, v) for k, v in pool.items())


def _probe_weapon(probe: dict):
    return SimpleNamespace(damage_types=list(probe.get('forms') or ['physical']),
                           material=str(probe.get('material', '') or ''),
                           buc='blessed' if probe.get('blessed') else 'uncursed')


def _mult(weapon, monster) -> float:
    """The whole bane multiplier of ``weapon`` on ``monster``."""
    import combat
    r = combat.weapon_type_multiplier(weapon, monster)
    if isinstance(r, tuple):
        out = 1.0
        for x in r:
            out *= float(x)
        return out
    return float(r)


def _hits(need: dict, defn: dict) -> bool:
    """Is a kind written as ``defn`` weak to this need?"""
    probe = need.get('probe') or {}
    if probe.get('element'):
        return probe['element'] in set(defn.get('weaknesses') or ())
    mon = SimpleNamespace(**{k: v for k, v in defn.items() if isinstance(k, str) and k.isidentifier()})
    for key in ('weaknesses', 'resistances', 'tags'):
        if not hasattr(mon, key):
            setattr(mon, key, [])
    try:
        return _mult(_probe_weapon(probe), mon) > 1.0
    except Exception:
        return False


def _attacks_with(element: str, defn: dict) -> bool:
    for a in defn.get('attacks') or ():
        if isinstance(a, dict) and (a.get('type') == element or a.get('damage_type') == element):
            return True
    return False


def _guard_hits(key: str, need: dict, defn: dict) -> bool:
    """Does a kind written as ``defn`` call for this guard? An element by the
    type of its attacks; a named counter's technique (slice 5, counters.py)
    by how they land: a gaze ('delivery': 'gaze', or a Medusa's
    gaze_paralyze), a voice with a rider ('delivery': 'voice'), or a
    family's glamour ('families' / 'tags' and the 'effects' it carries)."""
    dl = need.get('delivery')
    fams, tags = set(need.get('families') or ()), set(need.get('tags') or ())
    if not dl and not fams and not tags:
        return _attacks_with(key, defn)
    if (fams or tags) and not (str(defn.get('family') or '') in fams
                               or tags & set(defn.get('tags') or ())):
        return False
    if dl == 'gaze' and defn.get('gaze_paralyze'):
        return True
    import guards
    effects = set(need.get('effects') or ())
    for a in defn.get('attacks') or ():
        if not isinstance(a, dict):
            continue
        if dl and guards.delivery(a) != dl:
            continue
        if need.get('riders') and not a.get('effect'):
            continue
        if effects and a.get('effect') not in effects:
            continue
        return True
    return False


@lru_cache(maxsize=128)
def needs(level: int) -> tuple:
    """What the floors at and just below ``level`` call for, commonest first:
    ((side, key, share, family), ...). ``side`` is 'weak' (what hurts them)
    or 'guard' (what they hurt with); ``share`` the part of what spawns there
    it touches (0-1); ``family`` the family most of those kinds belong to."""
    cfg = config()
    lo = max(1, int(level))
    hi = min(100, lo + _span())
    floors = [f for f in range(lo, hi + 1)]
    weight: dict = {}
    defs: dict = {}
    for f in floors:
        for kind, w, defn in _floor_kinds(f):
            weight[kind] = weight.get(kind, 0.0) + w / len(floors)
            defs[kind] = defn
    out = []
    for side in ('weak', 'guard'):
        table = cfg.get(side) or {}
        for key, need in table.items():
            if key.startswith('_') or not isinstance(need, dict):
                continue
            share, fam = 0.0, {}
            for kind, w in weight.items():
                d = defs[kind]
                hit = _hits(need, d) if side == 'weak' else _guard_hits(key, need, d)
                if hit:
                    share += w
                    f = d.get('family') or ''
                    fam[f] = fam.get(f, 0.0) + w
            if share > 0:
                top = max(sorted(fam), key=lambda k: fam[k]) if fam else ''
                out.append((side, key, round(share, 4), top))
    # Commonest first; a tie keeps the data's order (sorted is stable).
    out.sort(key=lambda t: -t[2])
    return tuple(out)


def foes_phrase(side: str, key: str, family: str) -> str:
    """'the dead walk', 'fire breathes': who or what the need is for."""
    cfg = config()
    if side == 'guard':
        g = (cfg.get('guard') or {}).get(key) or {}
        if g.get('foes'):
            return str(g['foes'])
    fam = (cfg.get('foes') or {}).get(family)
    if fam:
        return str(fam)
    try:
        import family_lore
        kin = family_lore.kin(family) if family else None
    except Exception:
        kin = None
    return f"{kin or 'strange things'} walk"


# ------------------------------------------------------------------ the wares

def line_of(defn: dict) -> set:
    """The classes a trader deals in, from his stock list."""
    out = set()
    for e in defn.get('stock') or ():
        for k in ('class', 'gear'):
            if e.get(k):
                out.add(e[k])
        if 'ids' in e and e.get('cat'):
            out.add(e['cat'])
    # Classes he sets out only as a counter for what walks below, never as
    # ordinary stock (Mother Wort's beeswax, Brannoc's cold-iron charm).
    out |= set(defn.get('counter_classes') or ())
    return out


def _offer_class(offer: dict) -> str:
    return offer.get('gear') or offer.get('class') or ''


def _best_kind(cat: str, level: int, rng, pred):
    """The deepest-found kind of ``cat`` the floor can offer that ``pred``
    accepts (the strongest of its line found by this depth), ties at random."""
    from items import is_random_loot, load_items, unique_available
    try:
        pool = [i for i in load_items(cat) if is_random_loot(i) and unique_available(i)
                and not getattr(i, 'is_unique', False)
                and int(getattr(i, 'min_level', 1) or 1) <= max(1, level)
                and pred(i)]
    except Exception:
        return None
    if not pool:
        return None
    deepest = max(int(getattr(i, 'min_level', 1) or 1) for i in pool)
    top = sorted((i for i in pool if int(getattr(i, 'min_level', 1) or 1) == deepest),
                 key=lambda i: str(i.id))
    import copy
    return copy.copy(rng.choice(top))


def _make(offer: dict, level: int, rng, best_form: str | None = None):
    """One ware for ``offer`` on floor ``level``, or None when the floor
    cannot supply it (silver is not found above floor 19). A weapon whose
    offer names no form takes the form that serves the same floors best
    (``best_form``: a blessed mace where skeletons walk), when one fits."""
    import smithing
    gear = offer.get('gear')
    if gear == 'weapon':
        w = None
        if not offer.get('form') and best_form:
            w = smithing.common_weapon(level, rng, form=best_form,
                                       material=offer.get('material'))
        if w is None:
            w = smithing.common_weapon(level, rng, form=offer.get('form'),
                                       material=offer.get('material'))
        if w is not None and offer.get('blessed'):
            w.buc = 'blessed'
            w.buc_known = True              # he says so: "blessed at the shrine"
        return w
    if gear == 'shield' and offer.get('template'):
        # A shield of one build in a metal the floor's loot is made of (the
        # mirror shield, a named counter: counters.py).
        import gear as _gear
        from items import _template_then_material, get_template, instantiate_shield, load_materials
        tpl = get_template('shields', offer['template'])
        if not tpl:
            return None
        chosen = _template_then_material([(offer['template'], tpl)], load_materials('armor'),
                                         int(level), rng, shield=True)
        if chosen is None:
            return None
        try:
            return instantiate_shield(chosen[0], chosen[1], level=_gear.roll_level(int(level), rng))
        except ValueError:
            return None
    if gear == 'armor':
        from items import pick_random_armor_for_floor
        try:
            a = pick_random_armor_for_floor(level, rng, slot=offer.get('slot'))
        except Exception:
            a = None
        if a is not None and offer.get('lining'):
            smithing.line(a, offer['lining'])
        return a
    cls = offer.get('class')
    if cls:
        effects = set(offer.get('effects') or ())
        spells = set(offer.get('spells') or ())
        ids = set(offer.get('ids') or ())

        def ok(i):
            if ids and str(getattr(i, 'id', '') or '') not in ids:
                return False
            if effects and str(getattr(i, 'effect', '') or '') not in effects:
                return False
            if spells and str(getattr(i, 'spell_id', '') or '') not in spells:
                return False
            return True
        return _best_kind(cls, level, rng, ok)
    return None


def _take(side: str, key: str, offer: dict, ware) -> str:
    """What the trader tells the hero to take: the ware's own shape when it
    shows ("a mace"), else the need's plain words ("fire")."""
    from paths import a_or_an
    cfg = config()
    need = (cfg.get(side) or {}).get(key) or {}
    gear = offer.get('gear')
    if gear == 'weapon' and ware is not None:
        import smithing
        tpl = smithing.template_of(ware)
        noun = (tpl or 'blade').replace('_', ' ')
        if offer.get('material'):
            return a_or_an(f"{str(offer['material']).replace('_', ' ')} {noun}").lower()
        if offer.get('blessed'):
            return a_or_an(f"blessed {noun}").lower()
        return a_or_an(noun).lower()
    if gear == 'armor' and ware is not None and offer.get('lining'):
        slot = str(getattr(ware, 'slot', offer.get('slot', 'cloak')) or 'cloak')
        return f"a {slot} lined against {offer['lining']}"
    return str(need.get('take') or key)


def stall_counters(defn: dict, level: int, rng) -> list:
    """The counters a trader of ``defn`` sets out on floor ``level``:
    [(ware, info)], at most ``per_stall`` of them (data). ``info`` is
    {'side', 'key', 'foes', 'take', 'marked'}; the first is the one he speaks
    of when the stall opens. The commonest weakness his line can answer
    comes first; then a guard against the commonest element, if it touches
    enough of what walks below (``guard_min_share``)."""
    cfg = config()
    line = line_of(defn)
    want = max(0, int(cfg.get('per_stall', 2) or 0))
    guard_min = float(cfg.get('guard_min_share', 0.1) or 0)
    ranked = needs(int(level))
    best_form = next((k for s, k, sh, _f in ranked if s == 'weak' and k in FORMS), None)
    out: list = []
    sides_done: set = set()

    def take_one(side, key, family) -> bool:
        need = (cfg.get(side) or {}).get(key) or {}
        for offer in need.get('offers') or ():
            if _offer_class(offer) not in line:
                continue
            ware = _make(offer, int(level), rng, best_form)
            if ware is None:
                continue
            marked = bool(offer.get('gear'))
            info = {'side': side, 'key': key, 'foes': foes_phrase(side, key, family),
                    'take': _take(side, key, offer, ware), 'marked': marked}
            if marked:
                ware._counter = info['foes']
            out.append((ware, info))
            sides_done.add(side)
            return True
        return False

    for side, key, share, family in ranked:
        if len(out) >= want:
            break
        if side in sides_done:
            continue
        # A need may set its own least share (a named counter's technique
        # is rarer than an element, and worth naming sooner).
        need_min = float(((cfg.get(side) or {}).get(key) or {}).get('min_share', guard_min) or 0)
        if side == 'guard' and share < need_min:
            continue
        take_one(side, key, family)
    if not out and want:
        # At least one counter a stall: a guard against a rarer element when
        # his line has nothing for any weakness (an apothecary's draughts).
        for side, key, share, family in ranked:
            if side == 'guard' and take_one(side, key, family):
                break
    return out


def counter_line(template: str, info: dict) -> str:
    """The trader's own words for his counter, from his ``counter`` line."""
    if not template or not info:
        return ''
    try:
        text = template.format(foes=info.get('foes', ''), take=info.get('take', ''))
    except (KeyError, IndexError, ValueError):
        return ''
    return text[:1].upper() + text[1:]


def best_material_forms(stock: list, level: int, rng, want: int = 3) -> list:
    """For an armourer: weapons of the best material on his shelf in the
    forms it lacks (slash, pierce, blunt), so a kid can buy the mace that
    matches his sword. At most ``want - forms already there`` new pieces.
    His best metal: a wood takes only a club's shape, so only a material
    that can be made in every form counts: the best of the shelf's, or (a
    shelf with none) the best such metal this floor's loot is made of."""
    import smithing
    from items import load_materials, material_spawn_weight, material_tier
    mats = load_materials('weapons')

    def every_form(mid) -> bool:
        return all(smithing.melee_templates(mats[mid], f) for f in MELEE_FORMS)

    def rank(mid):
        m = mats[mid]
        return (material_tier(m), float(m.get('weapon_base', 0) or 0), mid)
    commons = [w for w in stock if getattr(w, 'item_class', '') == 'weapon'
               and not getattr(w, 'is_unique', False)
               and str(getattr(w, 'material', '')) in mats and smithing.template_of(w)
               and not getattr(w, 'requires_ammo', None) and every_form(str(w.material))]
    if commons:
        best = max((str(w.material) for w in commons), key=rank)
    else:
        found = [mid for mid, m in mats.items()
                 if material_spawn_weight(m, int(level)) > 0 and every_form(mid)]
        if not found:
            return []
        best = max(found, key=rank)
    have = set()
    for w in commons:
        if w.material == best:
            have |= {t for t in (getattr(w, 'damage_types', None) or ()) if t in MELEE_FORMS}
    out = []
    for form in MELEE_FORMS:
        if len(have) >= want:
            break
        if form in have:
            continue
        w = smithing.common_weapon(level, rng, form=form, material=best, any_depth=True,
                                   only_form=True)
        if w is not None:
            out.append(w)
            have |= {t for t in w.damage_types if t in MELEE_FORMS}
    return out
