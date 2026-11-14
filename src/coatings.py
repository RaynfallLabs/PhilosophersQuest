"""Coatings and thrown flasks: the arsenal's consumable tools (winning-build
plan 2026-11-13, section 3.5; slice 5).

Brandon: a kid should "identify and learn about monsters, then strategically
find a way to exploit the weakness... throwing potions, targeting
weaknesses... elemental attacks and status attacks both ways".

**A coating** (a flask's ``coat`` block, data/items/flask.json: silver dust,
frost salts, viper venom, holy water, fire oil and their deeper kin) goes on
the weapon in the hero's hand. One turn, no question: as a potion is drunk.
Its substance joins what the weapon is made of (``combat._substances_of``
reads ``weapon.coating``), so it meets a weakness through the one bane rule,
``combat.weapon_type_multiplier``: silver dust on a steel mace hits a
werewolf as silver. A substance is worth the weak step against a creature
that cannot bear it and never makes a blow weaker. Each blow that lands
spends one (``after_blow``); the last says so. A rider (venom's poison,
frost's slowing, fire's burning) takes hold only on a creature that does not
resist or shrug off the substance and whose nature allows it
(``Monster.hold``: status_immune, a named foe's cap). Venom does nothing to
the poison-immune.

The coating lives on the WEAPON (``weapon.coating``), not the hero: swap to
the weapon At Your Back and back again, and the silver is still on the mace.
A coated weapon thrown counts as coated.

**A thrown flask** (its ``throw`` block: fire oil, holy water, acid and their
kin) bursts for real typed damage through ``Monster.take_damage`` (weak x2,
resisted x0.5, shrugged off x0.25; fire frightens what fears fire and stops
a troll's mending), plus a short status where its lore says (oil sets
burning, acid pits a hide). Holy water harms only the unholy. Each flask's
damage is real base data, sized to about one chain of a common weapon at its
own depth on a weak kind (floor_curve.ONE_ATTACK at its peak floor, halved
for the weak step), never computed from the floor the hero stands on (LORE
NOT FLOOR).

**Kit Sense** (slice 3, family at Hunter tier) can ask ``kit_sense_tools``
which coatings and flasks in the pack meet a creature's weakness.

Pure: no pygame, no Game. The Game side is game_arsenal.py.
"""
from __future__ import annotations

import json
import random
from functools import lru_cache

_PENDING: list = []


@lru_cache(maxsize=1)
def data() -> dict:
    """data/arsenal.json."""
    from paths import data_path
    with open(data_path('data', 'arsenal.json'), encoding='utf-8') as f:
        return json.load(f)


def cfg() -> dict:
    return data().get('coating') or {}


def throw_cfg() -> dict:
    return data().get('throw') or {}


@lru_cache(maxsize=1)
def flask_defs() -> dict:
    """data/items/flask.json, by id (today's data: a flask pickled in an old
    save takes today's numbers)."""
    from paths import data_path
    try:
        with open(data_path('data', 'items', 'flask.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _def_of(item) -> dict:
    """The flask definition this item is (an alias: the foraged holy water
    is a Flask of Holy Water), or {}."""
    iid = str(getattr(item, 'id', '') or '')
    iid = str((cfg().get('aliases') or {}).get(iid, iid))
    return flask_defs().get(iid) or {}


def coat_spec(item) -> dict | None:
    """What a coating does: {'substance', 'blows', 'rider'?}, or None for
    anything that is not a coating."""
    if item is None:
        return None
    spec = _def_of(item).get('coat') or getattr(item, 'coat', None)
    return dict(spec) if isinstance(spec, dict) and spec.get('substance') else None


def throw_spec(item) -> dict | None:
    """What a thrown flask does: {'damage_type', 'damage', 'only_weak'?,
    'status'?}, or None for anything that is not one."""
    if item is None:
        return None
    spec = _def_of(item).get('throw') or getattr(item, 'throw', None)
    return dict(spec) if isinstance(spec, dict) and spec.get('damage_type') else None


def is_tool(item) -> bool:
    """A coating or a thrown flask (or both)."""
    return coat_spec(item) is not None or throw_spec(item) is not None


def word(substance: str) -> str:
    """How a coated weapon strikes: 'silver', 'blessed', 'burning'..."""
    return str((cfg().get('words') or {}).get(substance, substance))


def _name(item) -> str:
    """A flask's name: known by sight, so always its true name, no count."""
    from hud_context import strip_article
    return strip_article(str(getattr(item, 'name', '') or 'flask'))


def _weapon_name(player, weapon) -> str:
    try:
        from hud_context import item_bare_name
        return item_bare_name(player, weapon)
    except Exception:
        return str(getattr(weapon, 'name', 'weapon'))


# ---------------------------------------------------------------------------
# The coating on a weapon
# ---------------------------------------------------------------------------

def coating_of(weapon) -> dict | None:
    """The coating still on ``weapon`` ({'id', 'name', 'substance', 'blows',
    'rider'}), or None."""
    c = getattr(weapon, 'coating', None) if weapon is not None else None
    if not isinstance(c, dict) or int(c.get('blows', 0) or 0) <= 0:
        return None
    return c


def coat_substance(weapon) -> str | None:
    """The substance a coating adds to ``weapon``'s blows (silver, holy,
    fire, cold, poison), or None. Read by combat._substances_of."""
    c = coating_of(weapon)
    return str(c.get('substance')) if c else None


def refusal(player, item) -> str:
    """Why ``item`` cannot coat the weapon in the hero's hand now, or ''."""
    spec = coat_spec(item)
    if spec is None:
        return ''
    weapon = getattr(player, 'weapon', None)
    c = cfg()
    if weapon is None:
        return str(c.get('no_weapon', 'You have no weapon to coat.'))
    if getattr(weapon, 'requires_ammo', None):
        return str(c.get('ranged', ''))
    sub = str(spec['substance'])
    held = coating_of(weapon)
    own, forms = _known_make(player, weapon)
    if sub in own or sub in forms:
        return str(c.get('already', '')).format(
            weapon=_weapon_name(player, weapon), word=word(sub), coat=_name(item))
    if held and held.get('id') == getattr(item, 'id', None) and int(held.get('blows', 0)) >= int(spec.get('blows', 0)):
        return str(c.get('already', '')).format(
            weapon=_weapon_name(player, weapon), word=word(sub), coat=_name(item))
    return ''


def _known_make(player, weapon) -> tuple:
    """(substances, forms) the hero can see his weapon has, for a refusal
    to name: all of them once it is identified (or its kind known); before
    that only what he knows of it anyway, a blessing he knows of and the
    smith's inlay he watched go in. A refused coating used to name an
    unidentified blade's metal ("your Pale Gleaming Mace is already
    silvered": bug bash WB-A12); now the coating simply goes on."""
    import combat
    try:
        from items import is_fully_known, buc_known_to
        known = is_fully_known(weapon, player)
    except Exception:
        known, buc_known_to = True, None
    if known:
        return ([s for s in combat._substances_of(_uncoated(weapon)) if s],
                list(combat.blow_forms_of(weapon)))
    own = []
    if (getattr(weapon, 'buc', 'uncursed') == 'blessed' and buc_known_to is not None
            and buc_known_to(weapon, player)):
        own.append('holy')
    try:
        import smithing
        inlay = smithing.inlay_of(weapon)
    except Exception:
        inlay = None
    if inlay:
        own.append(str(inlay))
    return own, []


class _Bare:
    """A weapon seen without its coating (what it is made of, alone)."""
    def __init__(self, weapon):
        self.__dict__.update(getattr(weapon, '__dict__', {}))
        self.__dict__['coating'] = None


def _uncoated(weapon):
    return _Bare(weapon) if weapon is not None else None


def apply(player, item) -> str:
    """Work the coating ``item`` into the weapon in the hero's hand and
    return the line that says so. The caller has checked ``refusal`` and
    takes one ``item`` from the pack."""
    spec = coat_spec(item)
    weapon = getattr(player, 'weapon', None)
    if spec is None or weapon is None:
        return ''
    c = cfg()
    old = coating_of(weapon)
    sub = str(spec['substance'])
    weapon.coating = {
        'id': str(getattr(item, 'id', '') or ''),
        'name': _name(item),
        'substance': sub,
        'blows': int(spec.get('blows', 12) or 12),
        'rider': dict(spec['rider']) if isinstance(spec.get('rider'), dict) else None,
    }
    wname = _weapon_name(player, weapon)
    line = str(c.get('applied', '')).format(coat=_name(item), weapon=wname, word=word(sub),
                                            blows=weapon.coating['blows'])
    if old and old.get('id') != weapon.coating['id']:
        line = str(c.get('replaced', '')).format(old=old.get('name', 'coating'), weapon=wname,
                                                 coat=_name(item)) + ' ' + line
    return line


def _resists(monster, sub: str) -> bool:
    return sub in set(getattr(monster, 'resistances', None) or ()) | \
        set(getattr(monster, 'shrugs_off', None) or ())


def after_blow(player, monster, weapon, actual: int) -> list:
    """A coated weapon's blow that landed on ``monster`` (``actual`` damage):
    its rider, fire's fright and burn-stop, and one blow spent. Returns the
    lines to say at the end of the action ([(text, kind)]), also queued for
    ``drain``."""
    c = coating_of(weapon)
    if c is None or monster is None:
        return []
    out = []
    sub = str(c.get('substance', ''))
    alive = bool(getattr(monster, 'alive', True))
    if alive and actual > 0 and sub in ('fire', 'acid'):
        # A burning blade does to a troll what a torch does: it cannot close
        # the wound, and a beast that fears fire runs (Monster._after_typed_hit).
        hit = getattr(monster, '_after_typed_hit', None)
        if callable(hit):
            hit(sub, actual)
    rider = c.get('rider') if isinstance(c.get('rider'), dict) else None
    if alive and rider and actual > 0:
        eff = str(rider.get('effect', ''))
        if _resists(monster, sub) or (
                callable(getattr(monster, 'resists_control', None)) and monster.resists_control(eff)):
            # Said once a fight per creature, not every blow.
            if monster.__dict__.get('_coat_refused') != c.get('id'):
                monster.__dict__['_coat_refused'] = c.get('id')
                from monster import the_name
                out.append((str(cfg().get('refused', '')).format(
                    coat=c.get('name', 'coating'), the=the_name(monster, lower=True)), 'warning'))
        elif random.random() < float(rider.get('chance', 1.0)):
            hold = getattr(monster, 'hold', None)
            if callable(hold):
                hold(eff, int(rider.get('turns', 3) or 3))
    out += spend_blow(player, weapon)
    _PENDING.extend(out)
    return out


def spend_blow(player, weapon) -> list:
    """One blow of the coating spent; the line when it is gone."""
    c = coating_of(weapon)
    if c is None:
        return []
    left = int(c.get('blows', 0)) - 1
    if left > 0:
        weapon.coating = dict(c, blows=left)
        return []
    weapon.coating = None
    return [(str(cfg().get('worn_off', '')).format(coat=c.get('name', 'coating'),
                                                   weapon=_weapon_name(player, weapon)), 'info')]


def drain() -> list:
    """The coating lines since the last drain ([(text, kind)]), cleared."""
    out = list(_PENDING)
    _PENDING.clear()
    return out


# ---------------------------------------------------------------------------
# Thrown flasks
# ---------------------------------------------------------------------------

def thrown_damage(item, monster) -> tuple:
    """(base damage, damage type) of a thrown flask before the creature's
    weakness or resistance (Monster.take_damage applies those). Holy water
    to a creature not weak to holy is (0, 'holy'): only water."""
    spec = throw_spec(item)
    if spec is None:
        return 0, ''
    dtype = str(spec['damage_type'])
    dmg = max(0, int(spec.get('damage', 0) or 0))
    if spec.get('only_weak') and dtype not in set(getattr(monster, 'weaknesses', None) or ()):
        return 0, dtype
    return dmg, dtype


def throw_at(item, monster) -> list:
    """Burst a thrown flask over ``monster``: the typed damage, then its
    status where the creature does not resist the type. Returns the lines
    ([(text, kind)]). The caller has taken the flask from the pack."""
    from monster import the_name
    t = throw_cfg()
    name = _name(item)
    dmg, dtype = thrown_damage(item, monster)
    if dmg <= 0:
        return [(str(t.get('only_water', '')).format(flask=name, the=the_name(monster, lower=True)),
                 'info')]
    actual = monster.take_damage(dmg, dtype)
    out = [(str(t.get('hit', '')).format(flask=name, the=the_name(monster, lower=True),
                                         damage=actual, dtype=dtype), 'success')]
    st = (throw_spec(item) or {}).get('status')
    # A burst that did no harm at all (a friend the blow passes by:
    # Monster.take_damage leaves him unhurt) sets nothing alight and pits no
    # hide (bug bash WB-A10: "The Goblin is set alight!" over a traveller
    # who never burned).
    if (isinstance(st, dict) and getattr(monster, 'alive', False) and actual > 0
            and not _resists(monster, dtype)):
        eff = str(st.get('effect', ''))
        hold = getattr(monster, 'hold', None)
        if eff and callable(hold):
            hold(eff, int(st.get('turns', 3) or 3))
            if monster.has_effect(eff):
                out.append((str(t.get('status_line', '')).format(
                    The=the_name(monster), effect=_effect_words(eff)), 'success'))
    return out


def _effect_words(eff: str) -> str:
    return {'armor_crack': 'pitted by the acid', 'burning': 'set alight'}.get(
        eff, eff.replace('_', ' '))


# ---------------------------------------------------------------------------
# Cards and the HUD
# ---------------------------------------------------------------------------

def card_lines(item) -> list:
    """What a coating or flask does, for its Kit and lore card."""
    out = []
    c = cfg()
    spec = coat_spec(item)
    if spec:
        out.append(str(c.get('card_coat', '')).format(word=word(spec['substance']),
                                                      blows=spec.get('blows', 12)))
        r = spec.get('rider')
        if isinstance(r, dict):
            key = 'card_rider_sure' if float(r.get('chance', 1.0)) >= 1.0 else 'card_rider'
            out.append(str(c.get(key, '')).format(effect=_effect_words(str(r.get('effect', ''))),
                                                  turns=r.get('turns', 3)))
    t = throw_spec(item)
    if t:
        if t.get('only_weak'):
            out.append(str(c.get('card_throw_weak', '')).format(damage=t.get('damage', 0)))
        else:
            out.append(str(c.get('card_throw', '')).format(damage=t.get('damage', 0),
                                                           dtype=t.get('damage_type', '')))
        st = t.get('status')
        if isinstance(st, dict):
            out.append(str(c.get('card_throw_status', '')).format(
                effect=_effect_words(str(st.get('effect', ''))), turns=st.get('turns', 3)))
    return [s for s in out if s]


def weapon_card_lines(weapon) -> list:
    """'Coated: Silver Dust, 9 blows left (silver).' for a coated weapon."""
    co = coating_of(weapon)
    if not co:
        return []
    return [str(cfg().get('card_weapon', '')).format(coat=co.get('name', 'coating'),
                                                     blows=co.get('blows', 0),
                                                     word=word(str(co.get('substance', ''))))]


def hud_rows(player) -> list:
    """[(label, kind)] for the sidebar's effects: the coating on the weapon
    in the hand, with its blows left."""
    co = coating_of(getattr(player, 'weapon', None))
    if not co:
        return []
    return [(f"{co.get('name', 'Coating')} {int(co.get('blows', 0))}", 'coat')]


# ---------------------------------------------------------------------------
# Kit Sense (slice 3): what in the pack meets this creature's weakness
# ---------------------------------------------------------------------------

def kit_sense_tools(player, monster) -> list:
    """The coatings and thrown flasks in the hero's pack that meet
    ``monster``'s weakness, best first: [(item, why)], ``why`` one of
    'coat' (it would make the weapon in his hand strike where the creature
    is weak, and the weapon does not already) or 'throw' (a thrown flask of
    a damage type it is weak to). Several kinds of one thing count once.

    THE HOOK for Kit Sense (winning-build plan 3.1, slice 3): call it beside
    the weapons in the pack, and name the first: "Your Silver Dust would
    serve here." A pure read: nothing is spent or said."""
    import combat
    import kit_sense
    weapon = getattr(player, 'weapon', None)
    out, seen = [], set()
    weak = set(getattr(monster, 'weaknesses', None) or ())
    tags = set(getattr(monster, 'tags', None) or ())
    import affinity as _aff
    # The blade as the hero knows it (kit_sense.known_mult): an unidentified
    # one's own metal and blessing are no part of the reckoning. Read from
    # the true blade, a coating his hidden silver already gave was left
    # unnamed, and that silence told him the blade was silver (bug bash
    # WB-D01).
    base = 1.0
    if weapon is not None and not getattr(weapon, 'requires_ammo', None):
        base = kit_sense.known_mult(player, weapon, monster)
    for it in getattr(player, 'inventory', None) or ():
        iid = str(getattr(it, 'id', '') or '')
        if iid in seen:
            continue
        spec = coat_spec(it)
        if (spec and weapon is not None and not getattr(weapon, 'requires_ammo', None)
                and not refusal(player, it)):
            sub = str(spec['substance'])
            if _aff.step(sub, monster, also_weak=combat._material_weak(sub, tags)) > 1.0:
                probe = _Bare(weapon)
                probe.__dict__['coating'] = {'substance': sub, 'blows': 1}
                coated = kit_sense.known_mult(player, probe, monster)
                if coated > base + 1e-9:
                    out.append((coated, it, 'coat'))
                    seen.add(iid)
                    continue
        t = throw_spec(it)
        if t and str(t['damage_type']) in weak:
            dmg = int(t.get('damage', 0) or 0) * _aff.weak_step()
            out.append((dmg, it, 'throw'))
            seen.add(iid)
    # Coatings first (they serve a whole fight), the strongest first; then
    # the flasks, the hardest-hitting first.
    out.sort(key=lambda r: (0 if r[2] == 'coat' else 1, -float(r[0])))
    return [(it, why) for _v, it, why in out]
