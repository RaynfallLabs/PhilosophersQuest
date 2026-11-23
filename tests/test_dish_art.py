"""Dish pictures (the kitchen's art; the rule rewritten 2026-11-22).

Brandon, play-testing 3.6.1: "a Goblin Cheese grill looks like a steak,
tomatoes, and sausage... we need to review our recipe art for consistency".

Every ordinary dish shows a picture of its FORM (a grill is grilled meat, a
posset a drink, a pie a pie) that shows NO FOOD THE DISH DOES NOT CONTAIN,
at its TIER (the vessel) and BENEFIT (the colour cue) where such a picture
is drawn. ``tools/content/kitchen/dish_pictures.json`` says what every
picture shows (looked at one by one); ``dish_art.py`` places every dish by
it from its name, ingredients, tier and benefit; a dish with no fair picture
is on ``dish_art_no_match.json`` (what its picture should show), which may
only shrink. Legendary feasts and trophy dishes keep their own pictures.

What these tests cannot prove is how a picture reads to a player: the
review sheets DISH_ART_REVIEW_2026_11_22_*.png are for that.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))

import pygame  # noqa: E402

import dish_art  # noqa: E402
import kitchen  # noqa: E402

ART = os.path.join(ROOT, 'assets', 'tiles', 'items')
BOOK = kitchen.book()
ORDINARY = [r for r in BOOK if dish_art.is_ordinary(r)]
CAT = dish_art.catalogue()
COUNTED = dish_art.counted_foods()
with open(dish_art.NO_MATCH, encoding='utf-8') as _f:
    NO_MATCH = json.load(_f)['dishes']
# The no-match list on 2026-11-22. It only shrinks: new art (a catalogued
# picture) takes dishes off it, and a new dish must find a fair picture.
MAX_NO_MATCH = 63


def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    assert head[:8] == b'\x89PNG\r\n\x1a\n', path
    return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')


def _verdict(r):
    return dish_art.judge(r['name'], r['ingredients'], kitchen.dish_tier(r), r['benefit'])


def _shows(art):
    """The counted foods a picture shows."""
    return set(CAT['pictures'][art]['foods']) & COUNTED


# ---------------------------------------------------------------------------
# The pictures and the catalogue
# ---------------------------------------------------------------------------

def test_every_dish_picture_exists_and_is_a_64_px_tile():
    for r in BOOK:
        p = os.path.join(ART, r['art'] + '.png')
        assert os.path.exists(p), (r['id'], r['art'])
        assert _png_size(p) == (64, 64), (r['id'], r['art'])
        img = pygame.image.load(p)
        assert img.get_size() == (64, 64)


def test_the_catalogue_describes_every_dish_picture():
    """Every dish_*.png has a row saying its form and the foods on it, in the
    catalogue's own words, and every row is a picture that is drawn."""
    assert set(CAT['pictures']) == dish_art.drawn(ART)
    picture_forms = {f for fit in dish_art.FORM_FIT.values() for f in fit}
    for pid, p in CAT['pictures'].items():
        assert p['form'] in picture_forms, pid
        assert set(p['foods']) <= set(CAT['foods']), pid
        assert set(p['garnish']) <= set(CAT['garnish']), pid
        assert p['sees'].strip(), pid
    # every counted food is one some picture shows, so the rule can see it
    shown = {f for p in CAT['pictures'].values() for f in p['foods']}
    assert COUNTED <= shown
    # the foods Brandon named on the Goblin Cheese Grill count
    assert {'sausage', 'tomato', 'cheese', 'meat'} <= COUNTED


def test_the_rule_reads_every_form_it_names():
    for form, fit in dish_art.FORM_FIT.items():
        assert form in dish_art.FORM_NOUN, form
        assert min(fit.values()) == 0, form
        assert set(fit.values()) <= set(dish_art.STAND_IN_COST), form
    assert set(dish_art.FORM_WORDS) <= set(dish_art.FORM_FIT)
    assert dish_art.DEFAULT_FORM in dish_art.FORM_FIT


# ---------------------------------------------------------------------------
# The book
# ---------------------------------------------------------------------------

def test_every_legendary_feast_has_a_picture_of_its_own():
    feasts = [r for r in BOOK if r.get('legendary')]
    assert len(feasts) == 36
    users = {}
    for r in BOOK:
        users.setdefault(r['art'], []).append(r['id'])
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


def test_every_dish_shows_its_form_and_no_food_it_lacks():
    """The rule holds for the whole book: the picture is of the dish's form
    (or one that reads the same) and shows no counted food its ingredients do
    not hold, except the dishes on the no-match list, which wait for art."""
    for r in ORDINARY:
        if r['id'] in NO_MATCH:
            continue
        form = dish_art.dish_form(r['name'])
        pform = CAT['pictures'][r['art']]['form']
        rank = dish_art.FORM_FIT[form].get(pform)
        assert rank is not None and rank <= dish_art.FAIR_RANK, (r['id'], r['name'], r['art'])
        has = dish_art.contents(r['ingredients'], form)
        assert _shows(r['art']) <= has, (r['id'], r['name'], r['art'], _shows(r['art']) - has)


def test_the_no_match_list_is_exactly_the_dishes_without_a_fair_picture():
    """Each listed dish truly has no fair picture today (so new art takes it
    off), every dish without one is listed, and the list only shrinks."""
    lost = {r['id'] for r in ORDINARY if not _verdict(r)['fair']}
    assert lost == set(NO_MATCH)
    assert len(NO_MATCH) <= MAX_NO_MATCH, len(NO_MATCH)
    by_id = {r['id']: r for r in BOOK}
    for rid, row in NO_MATCH.items():
        r = by_id[rid]
        assert row['given'] == r['art'], rid
        assert row['name'] == r['name'], rid
        assert row['wants'].strip() and row['why'].strip(), rid


def test_the_goblin_cheese_grill_shows_grilled_meat_and_nothing_it_lacks():
    """Brandon's case: goblin meat and hard cheese, grilled. No sausage, no
    tomatoes."""
    r = next(r for r in BOOK if r['name'] == 'Goblin Cheese Grill')
    assert set(r['ingredients']) == {'goblin_prime', 'hard_cheese'}
    assert CAT['pictures'][r['art']]['form'] == 'steak'
    assert 'meat' in _shows(r['art'])
    assert not _shows(r['art']) & {'sausage', 'tomato'}
    assert r['id'] not in NO_MATCH


def test_no_ordinary_dish_shows_tomatoes():
    """No ingredient is a tomato, so the red berries that read as tomatoes
    (the old HP cue) are on no dish's picture."""
    for r in ORDINARY:
        assert 'tomato' not in _shows(r['art']), (r['id'], r['name'], r['art'])


def test_a_sausage_shows_only_where_the_dish_has_one():
    """A sausage on the plate means sausages in the dish: its name makes them
    (sausages, bangers, a black pudding, a fry-up or mixed grill) or a part
    is one (Bugbear Bangers)."""
    for r in ORDINARY:
        if 'sausage' in _shows(r['art']):
            assert 'sausage' in dish_art.contents(r['ingredients'], dish_art.dish_form(r['name'])), r['id']


def test_a_dish_keeps_its_tier_and_benefit_when_a_fair_picture_has_them():
    """Form and contents come first; then the vessel (tier) stays true
    wherever a fair picture has it, and the colour (benefit) wherever a fair
    picture of the dish's closest form at its tier has it."""
    pics = dish_art.pictures()
    for r in ORDINARY:
        v = _verdict(r)
        if not v['fair']:
            continue
        tier, tab = kitchen.dish_tier(r), kitchen.dish_tab(r)
        fit = dish_art.FORM_FIT[v['form']]
        fair = [(fit[pf], t, tb) for pf, t, tb, foods in pics.values()
                if fit.get(pf, 9) <= dish_art.FAIR_RANK and not foods - v['has']]
        _, t, tb = dish_art.parse(r['art'])
        here = [(rank, ptb) for rank, pt, ptb in fair if pt == tier]
        if here:
            assert t == tier, (r['id'], r['name'], r['art'])
            best = min(rank for rank, _ in here)
            if (best, tab) in here:
                assert tb == tab, (r['id'], r['name'], r['art'])


def test_most_dishes_show_their_own_form_and_many_pictures_are_used():
    own = sum(1 for r in ORDINARY
              if dish_art.FORM_FIT[dish_art.dish_form(r['name'])].get(CAT['pictures'][r['art']]['form']) == 0)
    assert own >= 0.85 * len(ORDINARY), (own, len(ORDINARY))
    assert len({r['art'] for r in ORDINARY}) >= 120


def test_the_book_matches_what_dish_art_picks():
    """dish_art.py writes each dish's art, and the record dish_art.json beside
    it says the same."""
    have = dish_art.drawn(ART)
    with open(dish_art.RECORD, encoding='utf-8') as f:
        record = json.load(f)
    for r in BOOK:
        assert r['art'] == dish_art.recipe_art(r['id'], r, kitchen.dish_tier(r), have), r['id']
        assert record[r['id']] == r['art'], r['id']
    assert set(record) - {'_doc'} == {r['id'] for r in BOOK}


# ---------------------------------------------------------------------------
# The rule, pure
# ---------------------------------------------------------------------------

def test_a_name_says_its_form():
    f = dish_art.dish_form
    assert f('Goblin Gristle Stew') == 'stew'
    assert f('Kuo-Toa Brine Ham Stew') == 'stew'
    assert f('Goblin Cheese Grill') == 'steak'
    assert f('Monster Mixed Grill') == 'fryup'
    assert f('Bound-Wolf Breakfast') == 'fryup'
    assert f('War-Wolf Steak Sandwich') == 'bread'
    assert f('Rattling Marrow on Toast') == 'bread'
    assert f('Fried Black Pudding') == 'sausage'
    assert f('Pit Fiend Blood Pudding') == 'sausage'
    assert f('Black Pudding Pie') == 'pie'
    assert f('Ghost Story Bread Pudding') == 'pudding'
    assert f('Dire Lion Leg Roast') == 'leg'
    assert f('Blink Dog Loin Roast') == 'roast'
    assert f('Apple and Cheese Bake') == 'bake'
    assert f('Volcano Fondue') == 'fondue'
    assert f('Rat Rump Kebab') == 'skewer'
    assert f('Crystal Shard Tea') == 'drink'
    assert f('Theriac of Andromachus') == 'drink'
    assert f('Mist-and-Stars Bisque') == 'chowder'
    assert f('Twenty-Armed Demon Curry') == 'stew'
    assert f('Hydra Head Pie') == 'pie'
    assert f('Oven-Spark Pirozhki') == 'pie'
    assert f('Brain Pouch Dumplings') == 'dumpling'
    assert f('Cube Aspic Wobble') == 'jelly'
    assert f('Plague Bladder Pickle') == 'pickle'
    assert f("Sea-Swallower's Feast") == 'meal'
    assert f('Harvest-Home Supper') == 'meal'
    assert f('Something Nobody Has Named Yet') == dish_art.DEFAULT_FORM


def test_what_an_ingredient_is_on_a_plate():
    foods = dish_art.ingredient_foods
    assert foods('goblin_prime') == {'meat', 'bone'}                 # a cut, on the bone
    assert foods('hard_cheese') == {'cheese'}
    assert foods('bread_ration') == {'bread'}
    assert 'meat' not in foods('green_slime_prime')                  # an ooze's sac is slime
    assert 'meat' not in foods('imp_prime')                          # ichor is blood, not flesh
    assert 'meat' not in foods('earth_elemental_prime')              # an elemental's jar
    assert foods('specter_prime') == {'jelly'}                       # ectoplasm: no bone, no flesh
    assert 'whole_bird' in foods('roc_chick_prime')                  # a bird's cut may roast whole
    assert 'sausage' in foods('bugbear_prime')                       # Bugbear Bangers is one
    assert 'mushroom' in foods('cave_mushroom')
    # what the cook makes for a form
    assert 'sausage' in dish_art.contents(['goblin_prime'], 'sausage')
    assert 'sausage' in dish_art.contents(['imp_prime'], 'sausage')    # a blood pudding
    assert 'sausage' not in dish_art.contents(['goblin_prime', 'hard_cheese'], 'steak')
    assert 'bread' in dish_art.contents(['boggart_prime'], 'bread')    # toast is bread


def test_a_new_dish_is_placed_by_the_same_rule():
    """No table to edit: any name and ingredients find a picture by the rule,
    and a picture with a food the dish lacks loses even at its own tier."""
    grill = dish_art.judge('Kobold and Cheese Grill', ['goblin_prime', 'hard_cheese'], 1, 'hp')
    assert grill['fair'] and not dish_art.pictures()[grill['art']][3] & {'sausage', 'tomato'}
    # with only the old picture and the plain fillet drawn, the fillet wins
    fake = {'dish_steak_t1_hp', 'dish_steak_t2_stat'}
    assert dish_art.art_for('Kobold and Cheese Grill', 1, 'hp', fake,
                            ['goblin_prime', 'hard_cheese']) == 'dish_steak_t2_stat'
    # a posset is a drink, a pie a pie, at the dish's own tier where drawn
    assert dish_art.art_for('Night Posset', 2, 'mp', ingredients=['imp_prime']) == 'dish_drink_t2_mp'
    pie = dish_art.art_for('Unheard-Of Wyrm Pie', 3, 'STR', ingredients=['goblin_prime'])
    assert dish_art.parse(pie)[:2] == ('pie', 3)
    # a stew with no flesh in it never shows meat
    v = dish_art.judge('Bottled-Storm Stew', ['storm_elemental_prime'], 3, 'hp')
    assert 'meat' not in dish_art.pictures()[v['art']][3]
    # a sandwich with no meat has no fair picture yet, and stays a sandwich
    v = dish_art.judge('Plain Cheese Sandwich', ['bread_ration', 'hard_cheese'], 1, 'sp')
    assert not v['fair'] and dish_art.parse(v['art'])[0] == 'bread'
    assert 'with no meat' in dish_art.wants(v, ['Bread Ration', 'Hard Cheese'])
