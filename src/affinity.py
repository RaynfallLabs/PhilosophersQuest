"""Weakness, resistance and shrugging off: the steps, what a hit met, and
the lines that say so.

Brandon, bug bash 3.3.2: "when you hit something with its weakness or with
its resistance, we should have a whole set of pokemon style messages, so
you know it when you are blocked or effective."

THE STEPS (winning-build plan 2026-11-13, section 3.2, decision 2) are in
data/affinity_rules.json: a blow of a kind the creature is weak to lands
twice as hard, one it resists half as hard, and one it shrugs off (a swarm
against a sword, a ghost against a club) a quarter as hard. There is no
full immunity. A weapon's form and its substance each take a step and
multiply (combat.weapon_type_multiplier), capped at x3; a spell, wand or
breath is one damage type and takes one step (combat._damage_multiplier).
The kinds' lists are written from their lore (data/family_affinity.json,
tools/content/affinity_pass.py).

A hit that meets a creature's weakness, resistance or shrugging off is
noted here: the hero's blows and shots by combat.strike_damage (the form
and substance of the weapon, after every bypass), spells, wands and
anything else typed by Monster.take_damage. A beast or troll that fire
sends to flight (status_weak `fear_of_fire`) is noted the same way. At the
end of the action Game._advance_turn drains the notes and says one line
for each way creatures were struck, picked from data/affinity_lines.json.
Damage over time (a burn ticking) is not a hit and is not noted.

When they are said (3.3.3 lore audit): a kill says them first, before "X is
slain!" and its loot (Game._say_action_lines, from _on_monster_killed); the
world's turn says its own at its end (Boots of Thor, a pet's typed blow), not
after the hero's next action; and the queue is emptied on a new game, a
load and a change of floor. A blow on which a family technique has just
said the weakness (Bonebreaker) is not noted (combat.strike_damage).

What they say follows what the hero knows of the creature (winning-build
plan 2026-11-13, section 3.1; Brandon: "no omniscient monsters"). He always
FEELS a hit; knowing the creature tells him WHY:
  UNKNOWN  a 'felt' line only ("It reels!", "Barely a mark on the wight."),
           never naming what met it;
  KIN      (its family at Recognise or Forewarned) the felt line and the
           family's habit ("The dead have no heart for a point to find.",
           `habit`), from its group's or its family's lore;
  KNOWN    (studied, its page opened, or its family at Lore) the cause named
           ("Super effective! The wight cannot bear silver.").
Game._say_affinity_lines passes `level_of` (family_lore.knowledge). A beast
put to flight by fire is what the eye sees and is said the same to all.
"""
from __future__ import annotations

import json
import random
from functools import lru_cache

WEAK = 'weak'
RESISTED = 'resisted'
SHRUGS_OFF = 'shrugs_off'
FIRE_FRIGHT = 'fire_fright'           # a beast or troll put to flight by fire

_KINDS = (WEAK, RESISTED, SHRUGS_OFF, FIRE_FRIGHT)
_EPS = 1e-9

# The three ways a weapon wounds. A monster attack of one of these, or a
# plain 'physical' one, is a blow (armour, shields and the Mirror of Souls
# answer it); anything else is an element.
FORMS = ('slash', 'pierce', 'blunt')
PHYSICAL = frozenset(FORMS) | {'physical'}

_PENDING: list = []

# How much the hero knows of a creature (family_lore.UNKNOWN, KIN, KNOWN:
# the same numbers, kept here so this module needs nothing of the hero's).
UNKNOWN, KIN, KNOWN = 0, 1, 2


@lru_cache(maxsize=1)
def lines() -> dict:
    from paths import data_path
    with open(data_path('data', 'affinity_lines.json'), encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def rules() -> dict:
    """data/affinity_rules.json: the steps, the cap, the status rules."""
    from paths import data_path
    with open(data_path('data', 'affinity_rules.json'), encoding='utf-8') as f:
        return json.load(f)


def weak_step() -> float:
    return float(rules()['weak'])


def resisted_step() -> float:
    return float(rules()['resisted'])


def shrugs_step() -> float:
    return float(rules()['shrugs_off'])


def cap() -> float:
    return float(rules()['cap'])


def step(dtype: str, monster, also_weak: bool = False) -> float:
    """The step one damage type (a form, an element, a substance) takes
    against `monster`: weak, resisted, shrugged off or plain. `also_weak`:
    the creature cannot bear it for another reason (a weapon material's
    effective_against matched its tags)."""
    if not dtype:
        return 1.0
    if also_weak or dtype in (getattr(monster, 'weaknesses', None) or ()):
        return weak_step()
    if dtype in (getattr(monster, 'shrugs_off', None) or ()):
        return shrugs_step()
    if dtype in (getattr(monster, 'resistances', None) or ()):
        return resisted_step()
    return 1.0


def capped(mult: float) -> float:
    """A whole blow's multiplier, held to the cap (x3)."""
    return min(float(mult), cap())


def kind_of(mult: float) -> str:
    """'weak' above 1, 'shrugs_off' at or below the shrugging step,
    'resisted' below 1, '' for a plain hit."""
    if mult > 1.0 + _EPS:
        return WEAK
    if mult <= shrugs_step() + _EPS:
        return SHRUGS_OFF
    if mult < 1.0 - _EPS:
        return RESISTED
    return ''


def note(monster, kind: str, word: str) -> None:
    """A hit on `monster` met its weakness, its resistance or what it
    shrugs off (`word`: the damage type, form or substance that did), or
    fire sent it to flight."""
    if kind in _KINDS and monster is not None:
        _PENDING.append((monster, kind, str(word or '')))


def drain() -> list:
    """The notes since the last drain, cleared."""
    out = list(_PENDING)
    _PENDING.clear()
    return out


def word_for(word: str) -> str:
    return str((lines().get('words') or {}).get(word, str(word).replace('_', ' ')))


def say(notes, rng=None, level_of=None) -> list:
    """The lines for one action's notes: one per kind of meeting (weakness,
    resistance, shrugging off, a flight from fire) and per how much the hero
    knows of the creatures struck, naming the creature, or all of them when
    several were struck the same way.

    `level_of(monster)` is how much the hero knows of it (UNKNOWN, KIN,
    KNOWN: family_lore.knowledge); without it every creature counts as
    known, the cause named (the tests' and the tools' plain reading)."""
    rng = rng or random
    from monster import the_name
    by_kind: dict = {}
    for m, kind, word in notes:
        level = KNOWN
        if level_of is not None and kind != FIRE_FRIGHT:
            try:
                level = int(level_of(m))
            except Exception:
                level = UNKNOWN
        by_kind.setdefault((kind, level), []).append((m, word))
    out = []
    for kind in _KINDS:
        for level in (KNOWN, KIN, UNKNOWN):
            hits = by_kind.get((kind, level))
            if not hits:
                continue
            monsters = []
            for m, _w in hits:
                if all(m is not x for x in monsters):
                    monsters.append(m)
            m, word = hits[0]
            many = len(monsters) > 1
            text = _line(kind, level, m, word, many, rng, the_name)
            if text:
                out.append((text, kind))
    return out


def _line(kind: str, level: int, m, word: str, many: bool, rng, the_name) -> str:
    """One meeting's line at what the hero knows (see `say`)."""
    from monster import pronoun_fill
    w = word_for(word)
    fill = dict(name=the_name(m), the=the_name(m, lower=True), word=w, word_cap=w[:1].upper() + w[1:],
                **pronoun_fill(m))
    if level >= KNOWN or kind == FIRE_FRIGHT:
        pool = lines().get(f"{kind}_many" if many else kind) or lines().get(kind) or []
        return rng.choice(pool).format(**fill) if pool else ''
    felt = lines().get('felt') or {}
    pool = felt.get(f"{kind}_many" if many else kind) or felt.get(kind) or []
    if not pool:
        return ''
    text = rng.choice(pool).format(**fill)
    if level >= KIN:
        extra = habit(m, kind, word, rng)
        if extra:
            text = f"{text} {extra}"
    return text


# ---------------------------------------------------------------------------
# The family's habit (KIN): what a hero who knows the family knows of how its
# creatures take a blow (data/affinity_lines.json habits)
# ---------------------------------------------------------------------------
def _keyed(table: dict) -> dict:
    """A habits table with its comma keys spread out: 'resisted:slash,pierce'
    answers both 'resisted:slash' and 'resisted:pierce'."""
    out = {}
    for key, pool in (table or {}).items():
        if key.startswith('_') or ':' not in key:
            continue
        meet, words = key.split(':', 1)
        for w in words.split(','):
            w = w.strip()
            if w:
                out.setdefault(f"{meet}:{w}", pool)
    return out


@lru_cache(maxsize=1)
def _habit_tables() -> tuple:
    """(families, groups) keyed tables, and each family's plain pools."""
    h = lines().get('habits') or {}
    fams = {fid: (_keyed(t), t) for fid, t in (h.get('families') or {}).items()}
    groups = {gid: _keyed(t) for gid, t in (h.get('groups') or {}).items()}
    return fams, groups


@lru_cache(maxsize=1)
def group_of_kind() -> dict:
    """{kind: its group in data/family_affinity.json (skeletons, swarms...)}."""
    from paths import data_path
    try:
        with open(data_path('data', 'family_affinity.json'), encoding='utf-8') as f:
            prof = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for gid, g in (prof.get('groups') or {}).items():
        for k in g.get('kinds') or ():
            out.setdefault(k, gid)
    return out


def habit(m, kind: str, word: str, rng=None) -> str:
    """The family's habit for this meeting: its group's line for what met
    it, else its family's, else the family's plain line for the meeting
    (which names nothing). '' for a creature with no family."""
    rng = rng or random
    import family_lore
    fid = family_lore.family_of(m)
    if not fid:
        return ''
    kid = getattr(m, 'kind', None) or (m if isinstance(m, str) else '')
    fams, groups = _habit_tables()
    key = f"{kind}:{word}"
    gid = group_of_kind().get(kid)
    fam_keyed, fam_plain = fams.get(fid, ({}, {}))
    pool = (groups.get(gid) or {}).get(key) if gid else None
    pool = pool or fam_keyed.get(key) or fam_plain.get(kind) or []
    return rng.choice(pool) if pool else ''


def is_good_news(kind: str) -> bool:
    """A line the hero is glad of (a weakness met, a beast put to flight),
    shown in the success colour; the rest in the warning colour."""
    return kind in (WEAK, FIRE_FRIGHT)


# ---------------------------------------------------------------------------
# Status: what a creature's nature refuses, and what it falls to easily
# (`status_immune`, `status_weak` in data/monsters.json; Monster.add_effect)
# ---------------------------------------------------------------------------
FEAR_OF_FIRE = 'fear_of_fire'


# ---------------------------------------------------------------------------
# Old saves: a monster saved before the lore pass takes its kind's lists
# ---------------------------------------------------------------------------
AFFINITY_KEYS = ('resistances', 'weaknesses', 'shrugs_off', 'status_immune', 'status_weak')


@lru_cache(maxsize=1)
def _monster_defs() -> dict:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def refresh_from_data(m) -> bool:
    """A monster saved before the lore pass (it has no `_affinity_pass`
    mark: Monster.__init__ sets one) takes its kind's weaknesses,
    resistances, shrugs_off and status lists from data/monsters.json, so an
    old save fights the same dungeon a new one does. Abaddon keeps his own
    resistances (holy fire strips them for a while: base_resistances).
    True when it was refreshed."""
    d = getattr(m, '__dict__', None)
    if d is None or '_affinity_pass' in d:
        return False
    from monster import AFFINITY_PASS
    d['_affinity_pass'] = AFFINITY_PASS
    defn = _monster_defs().get(str(d.get('kind', '') or ''))
    if not defn:
        return False
    for key in AFFINITY_KEYS:
        if key == 'resistances' and d.get('base_resistances'):
            continue
        setattr(m, key, list(defn.get(key) or []))
    # Its plain 'physical' blows take the form the pass gave them (a bite
    # pierces, a slam crushes), matched by name.
    typed = {a.get('name'): a.get('type') for a in (defn.get('attacks') or []) if isinstance(a, dict)}
    atks = d.get('attacks')
    if isinstance(atks, list):
        d['attacks'] = [dict(a, type=typed[a.get('name')])
                        if isinstance(a, dict) and a.get('type') == 'physical'
                        and typed.get(a.get('name')) not in (None, 'physical') else a
                        for a in atks]
    return True


def status_noun(effect: str) -> str:
    """'Fear' for feared, 'Sleep' for sleeping... (data/affinity_lines.json
    status_nouns), for the Bestiary page."""
    nouns = lines().get('status_nouns') or {}
    return str(nouns.get(effect) or str(effect).replace('_', ' ').title())


# ---------------------------------------------------------------------------
# What a creature is made of, as the hero is told it (3.5.1 audit)
# ---------------------------------------------------------------------------
# Brandon, 3.5.1: "some monsters take a quarter or half damage from certain
# attacks, like a stirge swarm hit with a sword or the beetles. However,
# this is conveyed nowhere on the monster identification screen. We need to
# make sure all this information is conveyed, and that all bestiary entries
# are accurate (weakness AND resistances)."
#
# damage_profile is the ONE reading of what changes the hero's damage on a
# creature. It follows step() and combat.weapon_type_multiplier exactly, so
# the Bestiary, a studied corpse, the Wand of Probing and Observe can never
# say less (or more) than the blow does:
#   * its weaknesses, resistances and what it shrugs off, each with its
#     size (double, half, a quarter), a type named in more than one list
#     shown where step() puts it (weak, then shrugs off, then resists);
#   * the materials it cannot bear: a weapon metal (or wood) whose
#     effective_against matches its tags (silver and the undead, cold iron
#     and the fey), and any material its weaknesses name (iron, silver).
#     These were never on the page: a skeleton's said "Weak to: Blunt, Holy"
#     and not the eight metals that bite it twice as hard;
#   * dragon scales, a damage ward, regeneration and what stops it.
# Types no blow, shot, spell, wand, flask, coating or pet of the hero's can
# land as ('shadow', 'necrotic': what one creature does to another) are left
# off: nothing of his can meet them.
HERO_TYPES = ('slash', 'pierce', 'blunt', 'fire', 'cold', 'lightning', 'acid',
              'poison', 'holy', 'magic', 'drain')
_SIZE_WORDS = {3.0: 'Triple', 2.0: 'Double', 0.5: 'Half', 0.25: 'Quarter'}


def _size_word(step_value: float) -> str:
    return _SIZE_WORDS.get(round(float(step_value), 4), f"x{float(step_value):g}")


def _getter(defn):
    return defn.get if isinstance(defn, dict) else (lambda k, d=None: getattr(defn, k, d))


def _title(x: str) -> str:
    return str(x).replace('_', ' ').title()


def bane_materials(defn) -> list:
    """The weapon materials ``defn`` cannot bear, a blow of which lands twice
    as hard as its substance (combat.weapon_type_multiplier): those whose
    effective_against matches its tags, then those its weaknesses name."""
    import combat
    combat._load_material_tags()
    table = combat._MATERIAL_EFFECTIVE_AGAINST
    get = _getter(defn)
    tags = set(get('tags', None) or ())
    out = [mat for mat in sorted(table) if table[mat] and (set(table[mat]) & tags)]
    for w in (get('weaknesses', None) or ()):
        if w in table and w not in out:
            out.append(w)
    return out


def damage_profile(defn) -> list:
    """[(kind, label, [types])] for what changes the hero's damage on this
    creature: kind 'weak', 'banes', 'resisted', 'shrugs_off'. Only the types
    a hero can land (HERO_TYPES; the materials under 'banes')."""
    import combat
    combat._load_material_tags()
    materials = set(combat._MATERIAL_EFFECTIVE_AGAINST)
    get = _getter(defn)
    weak_l = [t for t in (get('weaknesses', None) or ()) if t in HERO_TYPES]
    shrug_l = [t for t in (get('shrugs_off', None) or ()) if t in HERO_TYPES and t not in weak_l]
    res_l = [t for t in (get('resistances', None) or ())
             if t in HERO_TYPES and t not in weak_l and t not in shrug_l]
    banes = [m for m in bane_materials(defn) if m in materials]
    # The words only, never "(Double Damage)" (Brandon 2026-11-16: "all the
    # double and half damage is unnecessary; player can figure out what our
    # descriptors mean and can be defined in our hints"): data/hints.json
    # says what Weak To, Resists and Shrugs Off mean.
    out = []
    if weak_l:
        out.append((WEAK, "Weak To", weak_l))
    if banes:
        out.append(('banes', "Hurt Most By", banes))
    if res_l:
        out.append((RESISTED, "Resists", res_l))
    if shrug_l:
        out.append((SHRUGS_OFF, "Shrugs Off", shrug_l))
    return out


def hard_rules(defn) -> list:
    """[(kind, text)] for the rules besides the lists that change the hero's
    damage: dragon scales, a damage ward, regeneration (and what stops it)."""
    get = _getter(defn)
    out = []
    scales = float(get('dragon_scales', 0) or 0)
    if scales > 0:
        out.append(('scales', f"Scales: Turn aside {round(scales * 100)}% of every blow, "
                              "but not one driven upward from a pit."))
    ward = float(get('damage_ward', 0) or 0)
    if ward > 0:
        out.append(('ward', f"Ward: Absorbs {round(ward * 100)}% of every blow while it holds."))
    regen = int(get('regeneration', 0) or 0)
    if regen > 0:
        stops = [t for t in ('fire', 'acid') if t in (get('weaknesses', None) or ())]
        text = f"Regenerates: {regen} HP a turn"
        if stops:
            text += (f"; {' or '.join(stops)} stops it for "
                     f"{int(rules().get('regen_stop_turns', 3))} turns")
        out.append(('regen', text + '.'))
    # A weapon's form and its substance each take a step and multiply, to
    # the cap (combat.weapon_type_multiplier): say so where both can meet.
    weak_l = [t for t in (get('weaknesses', None) or ()) if t in HERO_TYPES]
    forms = [word_for(t) for t in weak_l if t in FORMS]
    subs = (['a blessed weapon'] if 'holy' in weak_l else []) + (
        ['one of a bane material' if 'holy' in weak_l else 'a weapon of a bane material']
        if bane_materials(defn) else [])
    if forms and subs and cap() > weak_step():
        out.append(('both', f"Hardest Blow: {' or '.join(forms)} from {' or '.join(subs)}."))
    return out


def bestiary_rows(defn) -> list:
    """Every row the Bestiary, a studied corpse and the Wand of Probing show
    of what a creature is made of, at the knowledge that shows them:
    [(kind, text)]. Damage first, then its other hard rules, then what its
    nature refuses and falls to easily."""
    rows = [(kind, f"{label}: {', '.join(_title(t) for t in types)}")
            for kind, label, types in damage_profile(defn)]
    rows += hard_rules(defn)
    return rows + [r for r in page_lines(defn) if r[0] != SHRUGS_OFF]


def page_lines(defn) -> list:
    """The status rows of the Bestiary page (what its nature refuses, what it
    falls to easily) and what it shrugs off: [(kind, text)] with kind
    'shrugs_off', 'immune' or 'easily'. bestiary_rows is the whole page."""
    get = defn.get if isinstance(defn, dict) else (lambda k, d=None: getattr(defn, k, d))
    out = []
    shrugs = list(get('shrugs_off', None) or [])
    if shrugs:
        out.append(('shrugs_off', "Shrugs Off: " + ', '.join(x.replace('_', ' ').title() for x in shrugs)))
    immune = list(get('status_immune', None) or [])
    if immune:
        out.append(('immune', "Immune To: " + ', '.join(status_noun(e) for e in immune)))
    weak = list(get('status_weak', None) or [])
    if weak:
        out.append(('easily', "Falls Easily To: " + ', '.join(status_noun(e) for e in weak)))
    return out


def status_weak_duration(duration: int) -> int:
    """Half again as long (data/affinity_rules.json status_weak_duration)."""
    return max(1, int(round(int(duration) * float(rules().get('status_weak_duration', 1.5)))))


def status_line(kind: str, effect: str, monster, rng=None, level: int = KNOWN) -> str:
    """The line for an effect a creature refused by nature (kind 'immune':
    "The golem does not know fear.") or fell to easily ('weak'). A refusal
    says why only to a hero who knows the creature or its family (`level`
    KIN or more); to one who does not it is felt only ("Nothing happens to
    the golem."). Falling to it easily is what the eye sees, said to all."""
    rng = rng or random
    from monster import the_name, pronoun_fill
    if kind == 'immune' and level < KIN:
        pool = lines().get('status_immune_felt') or []
        return (rng.choice(pool).format(name=the_name(monster), the=the_name(monster, lower=True),
                                        **pronoun_fill(monster))
                if pool else '')
    table = lines().get('status_immune' if kind == 'immune' else 'status_weak') or {}
    if kind == 'immune' and effect not in (getattr(monster, 'status_immune', None) or ()):
        # Not its kind's nature but a named foe's will, or the galla's
        # fury: never "it has no mind to frighten" of a thing that has one
        # (bug bash WB-B07).
        named = getattr(monster, '_is_named_foe', None)
        if ((callable(named) and named())
                or (effect == 'feared' and getattr(monster, 'fearless', False))):
            table = lines().get('status_immune_will') or table
    pool = table.get(effect) or table.get('default') or []
    if not pool:
        return ''
    return rng.choice(pool).format(name=the_name(monster), the=the_name(monster, lower=True),
                                   effect=str(effect).replace('_', ' '), **pronoun_fill(monster))
