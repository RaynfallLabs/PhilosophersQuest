"""Display names are always title case (2026-10-04).

Data files author names in lowercase; `naming.proper_name` and the
`ProperNameAttr` descriptor on Item / Monster / Corpse guarantee nothing
reaches the screen or the message log in all-lowercase.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

from naming import proper_name  # noqa: E402


def test_proper_name_title_cases_with_small_words():
    assert proper_name('ring of magic resist') == 'Ring of Magic Resist'
    assert proper_name('giant rat') == 'Giant Rat'
    assert proper_name('a massive shield of ox-hide and bronze') == \
        'A Massive Shield of Ox-Hide and Bronze'
    assert proper_name("st. john's wort") == "St. John's Wort"


def test_proper_name_leaves_authored_capitals_alone():
    assert proper_name('Ring of the Nibelung') == 'Ring of the Nibelung'
    assert proper_name('amulet of STR+1') == 'Amulet of STR+1'
    assert proper_name('ring of protection +1') == 'Ring of Protection +1'
    once = proper_name('wand of cure light wounds')
    assert proper_name(once) == once
    assert proper_name('') == ''
    assert proper_name(None) is None


def test_every_item_and_monster_name_is_capitalised():
    """Data-layer guard: no loaded item or monster exposes a lowercase-
    initial name or unidentified name."""
    import json
    from items import load_items
    from monster import Monster

    bad = []
    for cls in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                'spellbook', 'potion', 'food', 'ammo'):
        for it in load_items(cls):
            for attr in ('name', 'unidentified_name'):
                val = getattr(it, attr, '') or ''
                if val and val[0].isalpha() and not val[0].isupper():
                    bad.append((cls, it.id, attr, val))
    defs = json.loads((_ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
    for mid, d in defs.items():
        if not isinstance(d, dict) or 'name' not in d:
            continue
        name = proper_name(d['name'])
        if name[0].isalpha() and not name[0].isupper():
            bad.append(('monster', mid, 'name', name))
    assert not bad, bad[:10]
    assert Monster.name.__class__.__name__ == 'ProperNameAttr'


def test_old_save_lowercase_names_display_capitalised():
    """An object whose __dict__ still holds a lowercase name (unpickled
    from a save written before this change) reads back capitalised."""
    from items import Corpse
    c = Corpse('giant rat', 'giant_rat', 0, 0)
    assert c.name == 'Giant Rat Corpse'
    assert c.monster_name == 'Giant Rat'
    c.__dict__['name'] = 'giant rat corpse'      # simulate an old pickle
    assert c.name == 'Giant Rat Corpse'
