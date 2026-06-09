"""Encyclopedia must list KNOWN items, matched by the JSON dict key (2026-06-07).

Item JSON files (accessory/weapon/armor/wand/scroll/...) key each entry by its
id; the VALUES carry no inner 'id' field. The loader matched entry.get('id'),
which returned '' for every item -> EVERY item category came up empty ("none of
my accessories show up there, or anything else across any category"). The loader
now matches on the dict KEY and injects it as _id for the renderer (mirroring
the bestiary path).
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json
from pathlib import Path

from main import Game

_ITEMS = Path(__file__).resolve().parents[1] / 'data' / 'items'


class _Stub:
    pass


def _load(category, known):
    g = _Stub()
    g.player = _Stub()
    g.player.known_item_ids = set(known)
    g.player.inventory = []
    g._chronicle = []
    g._recalled_hints = []
    g._cooked_recipes = set()
    g.encyclopedia_entries = []
    Game._encyclopedia_load_entries(g, category)
    return g.encyclopedia_entries


def test_known_accessory_appears_keyed_by_dict_id():
    acc = json.loads((_ITEMS / 'accessory.json').read_text(encoding='utf-8'))
    key = next(iter(acc))
    out = _load('accessory', {key})
    assert len(out) == 1 and out[0]['_id'] == key


def test_unknown_id_is_excluded():
    assert _load('accessory', {'definitely_not_a_real_id'}) == []


def test_known_unique_weapon_appears():
    out = _load('weapon', {'excalibur'})
    assert any(e.get('_id') == 'excalibur' for e in out)


def test_recipes_tab_lists_cooked_recipes():
    """recipes.json is a DICT; the recipes loader must iterate its VALUES. It
    iterated the dict (yielding string keys), recipe.get(...) raised
    AttributeError, and the bare except left the Recipes tab permanently empty
    even after the player had cooked something."""
    recipes = json.loads((_ITEMS / 'recipes.json').read_text(encoding='utf-8'))
    a_name = next(iter(recipes.values()))['name']
    g = _Stub()
    g.player = _Stub()
    g.player.known_item_ids = set()
    g.player.inventory = []
    g._chronicle = []
    g._recalled_hints = []
    g._cooked_recipes = {a_name}
    g.encyclopedia_entries = []
    Game._encyclopedia_load_entries(g, 'recipes')
    assert any(e.get('name') == a_name for e in g.encyclopedia_entries), \
        "cooked recipe missing from Recipes tab (dict iterated as list)"


def test_every_item_category_can_populate():
    # one real known id per file must yield a non-empty list -- this is the
    # exact regression: get('id') made all of these stay empty forever.
    for cat in ('accessory', 'weapon', 'armor', 'wand', 'scroll'):
        d = json.loads((_ITEMS / f'{cat}.json').read_text(encoding='utf-8'))
        key = next(iter(d))
        out = _load(cat, {key})
        assert len(out) >= 1, f"{cat} stayed empty for a known id ({key})"
