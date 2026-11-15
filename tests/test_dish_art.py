"""Dish pictures (the kitchen rebuild's art, 2026-11-14, agent KA).

Every dish shows what its name says: its KIND (a stew, a pie, skewers...), its
TIER by the vessel (dark walnut, tawny clay, black iron, silver, jewelled
gold) and its MAIN BENEFIT by one colour cue (warm red HP, amber-gold SP,
glowing blue MP, green Stat, violet Special). ``tools/content/kitchen/
dish_art.py`` picks the picture from the name, tier and benefit alone, so a
rebuilt book with renamed dishes picks the right pictures; each legendary
feast has a picture of its own. What these tests cannot prove is how a
picture reads to a player: the sheets DISH_ART_SHEET.png and
FEAST_ART_SHEET.png are for that.
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))

import pygame  # noqa: E402

import dish_art  # noqa: E402
import kitchen  # noqa: E402

ART = os.path.join(ROOT, 'assets', 'tiles', 'items')
BOOK = kitchen.book()
# A dish that plays a song shows the song's own art (dish_art.recipe_art).
ORDINARY = [r for r in BOOK if not r.get('legendary') and not r.get('trophy') and not r.get('song')]


def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    assert head[:8] == b'\x89PNG\r\n\x1a\n', path
    return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')


def _parse(art):
    """dish_<kind>_t<tier>_<tab> -> (kind, tier, tab)."""
    assert art.startswith('dish_'), art
    kind, t, tab = art[5:].rsplit('_', 2)
    assert t[0] == 't', art
    return kind, int(t[1:]), tab


def test_every_dish_picture_exists_and_is_a_64_px_tile():
    for r in BOOK:
        p = os.path.join(ART, r['art'] + '.png')
        assert os.path.exists(p), (r['id'], r['art'])
        assert _png_size(p) == (64, 64), (r['id'], r['art'])
        img = pygame.image.load(p)
        assert img.get_size() == (64, 64)


def test_every_legendary_feast_has_a_picture_of_its_own():
    feasts = [r for r in BOOK if r.get('legendary')]
    assert len(feasts) == 36
    users = defaultdict(list)
    for r in BOOK:
        users[r['art']].append(r['id'])
    for r in feasts:
        assert r['art'] == dish_art.FEASTS[r['id']], r['id']
        assert r['art'].startswith('feast_'), r['id']
        assert users[r['art']] == [r['id']], (r['id'], users[r['art']])
    assert len({r['art'] for r in feasts}) == 36


def test_trophy_dishes_keep_their_boss_picture():
    trophies = [r for r in BOOK if r.get('trophy')]
    assert len(trophies) == 14
    for r in trophies:
        assert r['art'] == f"recipe_{r['id']}", r['id']
    assert len({r['art'] for r in trophies}) == 14


def test_a_shared_picture_is_always_one_tier_and_one_benefit():
    """The vessel says the tier and the colour says the benefit, so a picture
    is never shared across tiers or tabs; and two dishes that differ in kind,
    tier band and benefit never share a picture."""
    by_art = defaultdict(list)
    for r in ORDINARY:
        kind, tier, tab = _parse(r['art'])
        assert tier == kitchen.dish_tier(r), (r['id'], r['art'])
        assert tab == kitchen.dish_tab(r), (r['id'], r['art'])
        # the picture is the dish's own kind, or the nearest one drawn there
        assert kind in dish_art.FALLBACK[dish_art.dish_kind(r['name'])], (r['id'], r['name'], r['art'])
        by_art[r['art']].append(r)
    for art, rs in by_art.items():
        sigs = {(dish_art.dish_kind(r['name']), kitchen.dish_tier(r), kitchen.dish_tab(r)) for r in rs}
        assert len({(t, tab) for _, t, tab in sigs}) == 1, art
        for a in sigs:
            for b in sigs:
                assert not (a[0] != b[0] and a[1] != b[1] and a[2] != b[2]), (art, a, b)


def test_ordinary_dishes_show_many_different_pictures():
    arts = {r['art'] for r in ORDINARY}
    assert len(arts) >= 60, len(arts)
    # most dishes show their own kind, not a stand-in
    own = sum(1 for r in ORDINARY if _parse(r['art'])[0] == dish_art.dish_kind(r['name']))
    assert own >= 0.8 * len(ORDINARY), (own, len(ORDINARY))


def test_the_book_matches_what_dish_art_picks():
    """build_kitchen.py writes each dish's art from dish_art.py, and the record
    dish_art.json beside it says the same."""
    have = dish_art.drawn(ART)
    record = json.load(open(os.path.join(ROOT, 'tools', 'content', 'kitchen', 'dish_art.json'), encoding='utf-8'))
    for r in BOOK:
        assert r['art'] == dish_art.recipe_art(r['id'], r, kitchen.dish_tier(r), have), r['id']
        assert record[r['id']] == r['art'], r['id']
    assert set(record) - {'_doc'} == {r['id'] for r in BOOK}


def test_a_name_says_its_kind():
    k = dish_art.dish_kind
    assert k('Goblin Gristle Stew') == 'stew'
    assert k('Kuo-Toa Brine Ham Stew') == 'stew'
    assert k('War-Wolf Steak Sandwich') == 'bread'
    assert k('Rattling Marrow on Toast') == 'bread'
    assert k('Fried Black Pudding') == 'sausage'
    assert k('Pit Fiend Blood Pudding') == 'sausage'
    assert k('Ghost Story Bread Pudding') == 'pudding'
    assert k('Dire Lion Leg Roast') == 'leg'
    assert k('Blink Dog Loin Roast') == 'roast'
    assert k('Rat Rump Kebab') == 'skewer'
    assert k('Crystal Shard Tea') == 'drink'
    assert k('Mist-and-Stars Bisque') == 'chowder'
    assert k('Hydra Head Pie') == 'pie'
    assert k('Oven-Spark Pirozhki') == 'pie'
    assert k('Brain Pouch Dumplings') == 'dumpling'
    assert k('Cube Aspic Wobble') == 'jelly'
    assert k('Plague Bladder Pickle') == 'pickle'
    assert k("Sea-Swallower's Feast") == 'stew'
    assert k('Something Nobody Has Named Yet') == dish_art.DEFAULT_KIND


def test_a_renamed_dish_always_finds_a_true_vessel_and_colour():
    """Stew and roast are drawn at every tier and benefit, so any new or
    renamed dish gets a picture with its own vessel and colour."""
    have = dish_art.drawn(ART)
    for kind in dish_art.EVERYWHERE:
        for tier in range(1, 6):
            for tab in dish_art.TABS:
                assert dish_art.art_id(kind, tier, tab) in have, (kind, tier, tab)
    for kind, chain in dish_art.FALLBACK.items():
        assert chain[0] == kind and chain[-1] == dish_art.DEFAULT_KIND, kind
        assert set(chain) <= set(dish_art.KIND_WORDS), kind
    for benefit in ('hp', 'sp', 'mp', 'STR', 'fire_resist'):
        for tier in range(1, 6):
            art = dish_art.art_for('Unheard-Of Wyrm Pie', tier, benefit, have)
            kind, t, tab = _parse(art)
            assert (t, tab) == (tier, dish_art.tab_of(benefit))
            assert kind in dish_art.FALLBACK['pie']
    # a fallback is the nearest kind drawn there, and never another tier or tab
    fake = {'dish_stew_t2_hp', 'dish_roast_t2_hp', 'dish_bread_t2_hp'}
    assert dish_art.art_for('Odd Pie', 2, 'hp', fake) == 'dish_bread_t2_hp'
    assert dish_art.art_for('Odd Tea', 2, 'hp', fake) == 'dish_stew_t2_hp'
