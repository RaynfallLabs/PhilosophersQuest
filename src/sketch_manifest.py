"""Manifest, the Dreamspun Sketchbook's power: what she can draw, how the
drawing fights and how long it lasts, and how the menu sorts it (pure: no
pygame, no Game).

Brandon, 2026-11-15: "she should be able to Manifest ANY monster she has
studied; needs a new menu UI so it's easy to sort by what she'd want...
probably element/attack type? then in the menu sorted by level, descending."
Then: "let's make the image last based on how many quiz questions she gets
right, with the base being her INT" (the rule: INT + 5 turns for each right
answer).

Every rule is in data/manifest.json:

* what can be drawn: every kind she has studied (``family_lore.studied``)
  and any creature in view, never a boss or a named foe (``can_draw``);
* how the drawing bites: as its subject's FIRST attack's type, in the hero's
  words for damage (``affinity.HERO_TYPES``; ``hero_type``), so a weakness
  or a resistance of what it bites applies (Monster.take_damage);
* how long it lasts: her INT plus 5 turns for each right answer; none right
  and the page smudges (``duration``);
* the menu's rows (``make_rows``), sorted by level, highest first, then
  name; its tabs, All then one per bite type she can draw (``tabs``); which
  rows a known foe in view is weak to (``weak_to``: "Weak!") and the tab the
  menu opens on (``opening_tab``).

The Game side (the menu screen, the quiz, the sketch set down beside her) is
src/game_manifest.py.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from affinity import HERO_TYPES
from naming import proper_name, quantity

ALL = 'all'
PHYSICAL = 'physical'

EMPTY_LINE = ("You open the sketchbook, but there is nothing to draw yet. "
              "Study a creature first.")


@lru_cache(maxsize=1)
def rules() -> dict:
    """data/manifest.json (bundled: PhilosophersQuest.spec)."""
    from paths import data_path
    with open(data_path('data', 'manifest.json'), encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def defs() -> dict:
    """data/monsters.json: every kind's definition, by kind."""
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def defn(kind: str) -> dict | None:
    """A kind's definition with its id (as Monster(...) takes it), or None."""
    d = defs().get(str(kind or ''))
    return {**d, 'id': kind} if isinstance(d, dict) else None


def power_id() -> str:
    return str(rules().get('power_id', 'sketch_manifest'))


def cooldown() -> int:
    return int(rules().get('cooldown', 500))


def quiz() -> dict:
    return dict(rules().get('quiz') or {})


def max_chain() -> int:
    return int(quiz().get('max_chain', 5))


# ---------------------------------------------------------------------------
# What she can draw
# ---------------------------------------------------------------------------
def can_draw(kind: str, d: dict | None = None) -> bool:
    """A kind the sketchbook can draw: in monsters.json, not a boss, a
    mini-boss, a named foe, a quest's own creature, a seal demon or an ally
    (``exclude_flags``), not the cow level's nor the Black Knight
    (``exclude_kinds``), and with a family and an attack (no person of an
    encounter, nothing that cannot bite)."""
    d = d if d is not None else defs().get(str(kind or ''))
    if not isinstance(d, dict):
        return False
    r = rules()
    if kind in (r.get('exclude_kinds') or ()):
        return False
    if any(d.get(f) for f in (r.get('exclude_flags') or ())):
        return False
    return bool(d.get('family') and d.get('attacks'))


def drawable(studied, in_view=()) -> list:
    """Every kind she can draw: each studied kind, and each kind in view."""
    return sorted(k for k in set(studied or ()) | set(in_view or ()) if can_draw(k))


# ---------------------------------------------------------------------------
# How the drawing fights
# ---------------------------------------------------------------------------
def hero_type(dtype) -> str:
    """A creature's damage type in the hero's words (HERO_TYPES): its own
    when it is one, else ``type_map``'s (necrotic and shadow drain,
    psionic is magic, a plain blow crushes), else plain physical."""
    t = str(dtype or '').strip().lower()
    t = (rules().get('type_map') or {}).get(t, t)
    return t if t in HERO_TYPES else str(rules().get('unknown_type', PHYSICAL))


def bite_type_of(attacks) -> str:
    """The type a drawing bites as: its subject's first attack's."""
    first = attacks[0] if isinstance(attacks, (list, tuple)) and attacks else None
    return hero_type(first.get('type') if isinstance(first, dict) else None)


def type_word(t: str) -> str:
    return str(t or PHYSICAL).replace('_', ' ').title()


_DICE = re.compile(r'(\d*)d(\d+)([+-]\d+)?')


def mean_hp(d: dict) -> int:
    """The kind's mean health from its ``hp`` dice ("6d8+6" is 33)."""
    s = str((d or {}).get('hp', 1)).strip().lower().replace(' ', '')
    if s.isdigit():
        return int(s)
    m = _DICE.fullmatch(s)
    if not m:
        return 1
    n = int(m.group(1) or 1)
    sides = int(m.group(2))
    mod = int(m.group(3) or 0)
    return max(1, int(n * (sides + 1) / 2 + mod))


def level_of(d: dict) -> int:
    """The drawing's level: its subject's own (``min_level``, 1 to 100), as
    SketchedPet takes it."""
    return max(1, min(100, int((d or {}).get('min_level', 1) or 1)))


def sketch_hp(d: dict) -> int:
    """The drawing's health: SketchedPet's share of the kind's mean health."""
    from pet_system import SketchedPet
    return max(10, int(mean_hp(d) * SketchedPet.SCALE))


def bite_of(d: dict) -> int:
    """The drawing's bite: a pet's bite at the kind's level (give or take a
    fifth in play: SketchedPet.get_attack_damage)."""
    from pet_system import growth
    return growth('bite', level_of(d))


def attack_name(d: dict) -> str:
    atks = (d or {}).get('attacks') or []
    first = atks[0] if atks and isinstance(atks[0], dict) else {}
    return str(first.get('name') or '')


# ---------------------------------------------------------------------------
# How long it lasts
# ---------------------------------------------------------------------------
def stat_name() -> str:
    return str(rules().get('base_stat', 'INT'))


def per_right() -> int:
    return int(rules().get('turns_per_right', 5))


def stat_value(player) -> int:
    """Her INT (``base_stat``) as it stands now."""
    try:
        return max(0, int(getattr(player, stat_name(), 0) or 0))
    except (TypeError, ValueError):
        return 0


def duration(stat: int, chain: int) -> int:
    """INT + 5 turns for each right answer; none right is no sketch (0)."""
    chain = int(chain or 0)
    if chain <= 0:
        return 0
    return int(stat) + per_right() * chain


def max_duration(stat: int) -> int:
    return duration(stat, max_chain())


def duration_line(stat: int) -> str:
    """The menu's rule: "Lasts INT (14) + 5 turns for each right answer: up
    to 39 turns." """
    return (f"Lasts {stat_name()} ({int(stat)}) + {per_right()} turns for each right answer: "
            f"up to {quantity(max_duration(stat), 'turn')}.")


# ---------------------------------------------------------------------------
# What she would want: a known foe in view weak to the bite
# ---------------------------------------------------------------------------
def _mult(bite_type: str, foe) -> float:
    """The step the bite takes against ``foe``, as Monster.take_damage takes
    it (a plain physical bite takes none)."""
    if not bite_type or bite_type == PHYSICAL or foe is None:
        return 1.0
    from combat import _damage_multiplier
    return float(_damage_multiplier([bite_type], foe))


def weak_to(bite_type: str, foe) -> bool:
    return _mult(bite_type, foe) > 1.0 + 1e-9


def resisted_by(bite_type: str, foe) -> bool:
    return _mult(bite_type, foe) < 1.0 - 1e-9


def join_names(names) -> str:
    """"Ghoul", "Ghoul and Wight", "Ghoul, Wight and Lich"."""
    names = list(dict.fromkeys(n for n in names if n))
    if len(names) <= 1:
        return ''.join(names)
    return ', '.join(names[:-1]) + ' and ' + names[-1]


# ---------------------------------------------------------------------------
# The menu's rows and tabs
# ---------------------------------------------------------------------------
def row_for(kind: str, *, studied=(), in_view=(), foes=()) -> dict | None:
    """One kind's row: {'kind', 'name', 'level', 'type', 'type_word',
    'attack', 'hp', 'bite', 'studied', 'in_view', 'strong_against',
    'resisted_by', 'weak'}. ``foes``: [(name, monster)] of the known foes in
    view."""
    d = defs().get(kind)
    if not can_draw(kind, d):
        return None
    bt = bite_type_of(d.get('attacks'))
    strong = [name for name, foe in foes if weak_to(bt, foe)]
    resist = [name for name, foe in foes if resisted_by(bt, foe)]
    return {
        'kind': kind,
        'name': proper_name(str(d.get('name') or kind)),
        'level': level_of(d),
        'type': bt,
        'type_word': type_word(bt),
        'attack': attack_name(d),
        'hp': sketch_hp(d),
        'bite': bite_of(d),
        'studied': kind in set(studied or ()),
        'in_view': kind in set(in_view or ()),
        'strong_against': list(dict.fromkeys(strong)),
        'resisted_by': list(dict.fromkeys(resist)),
        'weak': bool(strong),
    }


def sort_rows(rows: list) -> list:
    """Level, highest first; then name."""
    return sorted(rows, key=lambda r: (-int(r['level']), str(r['name']).lower(), r['kind']))


def make_rows(studied, in_view=(), foes=()) -> list:
    """Every kind she can draw, as rows, sorted (``sort_rows``)."""
    studied = set(studied or ())
    in_view = set(in_view or ())
    rows = [row_for(k, studied=studied, in_view=in_view, foes=foes)
            for k in drawable(studied, in_view)]
    return sort_rows([r for r in rows if r])


def tabs(rows: list) -> list:
    """[(slug, label, count)]: All first, then one per bite type she can
    draw, in HERO_TYPES order (a plain physical bite is under All only)."""
    out = [(ALL, 'All', len(rows))]
    for t in HERO_TYPES:
        n = sum(1 for r in rows if r['type'] == t)
        if n:
            out.append((t, type_word(t), n))
    return out


def tab_rows(rows: list, tab: str) -> list:
    return list(rows) if tab == ALL else [r for r in rows if r['type'] == tab]


def opening_tab(rows: list) -> str:
    """The tab the menu opens on: the bite type with the most kinds a known
    foe in view is weak to (the first in HERO_TYPES order on a tie); All
    when no such kind is there."""
    best, best_n = ALL, 0
    for slug, _label, _n in tabs(rows)[1:]:
        n = sum(1 for r in rows if r['type'] == slug and r['weak'])
        if n > best_n:
            best, best_n = slug, n
    return best


def reason_line(tab: str, rows: list) -> str:
    """Why the menu opened on ``tab`` ('' on All): "Opened on Fire: Strong
    against Ghoul"."""
    if tab == ALL:
        return ''
    names = [n for r in rows if r['type'] == tab for n in r['strong_against']]
    if not names:
        return ''
    return f"Opened on {type_word(tab)}: Strong against {join_names(names)}"


def row_line(row: dict) -> str:
    """A row's second line: "Level 8, Pierce", and "In View" for a kind
    seen now but never studied."""
    text = f"Level {row['level']}, {row['type_word']}"
    if row['in_view'] and not row['studied']:
        text += ", In View"
    return text


def detail_lines(row: dict) -> list:
    """The detail pane's facts beside the picture, as (label, value)."""
    attack = row['type_word'] + (f" ({row['attack']})" if row['attack'] else '')
    out = [('Level', str(row['level'])), ('Attack', attack),
           ('Health', str(row['hp'])), ('Bite', f"About {row['bite']}")]
    if row['in_view'] and not row['studied']:
        out.append(('Drawn From', 'Sight'))
    else:
        out.append(('Drawn From', 'Memory'))
    return out


def qa_max_level(floor: int) -> int:
    """The QA key's reach: kinds up to max(10, floor + 5)."""
    q = rules().get('qa') or {}
    return max(int(q.get('min_level_floor', 10)), int(floor or 1) + int(q.get('levels_past_floor', 5)))


def qa_kinds(floor: int) -> list:
    """Every kind the QA key studies: each one she can draw, up to its reach."""
    top = qa_max_level(floor)
    return sorted(k for k, d in defs().items() if can_draw(k, d) and level_of(d) <= top)
