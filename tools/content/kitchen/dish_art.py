"""Which picture each dish shows (the kitchen's dish art; the rule rewritten
2026-11-22, Brandon: "a Goblin Cheese grill looks like a steak, tomatoes, and
sausage... we need to review our recipe art for consistency").

A dish's picture is of its FORM and shows NO FOOD THE DISH DOES NOT CONTAIN:

  - its FORM is read from its name (a grill is grilled meat, a posset a
    drink, a pie a pie; ``dish_form``);
  - what it CONTAINS comes from its ingredients (``contents``): a creature's
    cut is meat on the bone, a slime's sac is no meat at all, cheese is
    cheese, an elemental's jar is neither; and what the cook makes of them
    for that form (sausages from meat or blood, a sandwich's bread);
  - every ordinary picture is catalogued in ``dish_pictures.json`` (looked at
    one by one): the form it looks like and the foods you can SEE on it.

A picture is FAIR for a dish when its form is the dish's own or one that reads
the same (``FORM_FIT`` rank 0 or 1) and it shows no counted food the dish
lacks. Of the fair pictures the dish takes its own TIER (the vessel: dark
walnut, tawny clay, black iron, bright silver, jewelled gold; else the nearest),
then its own form over one that reads the same, then its own BENEFIT (the
colour cue: red HP, amber SP, blue MP, green Stat, violet Special; else the
nearest colour, ``TAB_NEAR``), then the one showing most of what it holds. A
dish with no fair picture takes the least wrong one and is written to
``dish_art_no_match.json`` (what its picture should show), the list for new
art. The 36 legendary feasts keep their own pictures (``FEASTS``), the 14
boss-trophy dishes their boss's (``recipe_<id>``), a song's dish its song's.

The rule reads only the name, ingredients, tier and benefit, so a new or
renamed dish is placed by it with no table to edit:

    py tools/content/kitchen/dish_art.py           # prints what it would change
    py tools/content/kitchen/dish_art.py --write   # writes recipes.json `art`,
                                                   # dish_art.json, the no-match list

``build_kitchen.py`` calls ``recipe_art`` for every dish it writes.
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART_DIR = os.path.join(ROOT, 'assets', 'tiles', 'items')
ITEMS = os.path.join(ROOT, 'data', 'items')
CATALOGUE = os.path.join(HERE, 'dish_pictures.json')
NO_MATCH = os.path.join(HERE, 'dish_art_no_match.json')
RECORD = os.path.join(HERE, 'dish_art.json')
RECORD_DOC = ('Recipe id -> its picture (assets/tiles/items/<art>.png), placed by dish_art.py: a picture '
              'of its form showing no food it does not contain, at its tier and benefit where one is '
              'drawn (dish_pictures.json says what each picture shows). A record to read; edit the rule '
              'or the catalogue, not this file.')

TABS = ('hp', 'sp', 'mp', 'stat', 'special')
STATS = ('STR', 'DEX', 'CON', 'INT', 'WIS', 'PER')
# A dish that cannot have its own benefit's colour takes the nearest one:
# warm red HP and amber SP stand for each other, the cool glows likewise.
TAB_NEAR = {
    'hp': ('hp', 'sp', 'stat', 'special', 'mp'),
    'sp': ('sp', 'hp', 'stat', 'special', 'mp'),
    'mp': ('mp', 'special', 'stat', 'sp', 'hp'),
    'stat': ('stat', 'sp', 'hp', 'special', 'mp'),
    'special': ('special', 'mp', 'stat', 'sp', 'hp'),
}

# ----------------------------------------------------------------------
# A dish's form, from its name
# ----------------------------------------------------------------------

# Name words -> form. The LAST form word in a name decides ("Kuo-Toa Brine Ham
# Stew" is a stew, "Steak Sandwich" a sandwich), after the phrases below.
FORM_WORDS = {
    'soup': ('soup', 'broth', 'stock', 'consommé', 'consomme', 'noodles', 'ramen', 'pho',
             'reduction', 'sauce', 'gravy', 'jus'),
    'stew': ('stew', 'ragout', 'pottage', 'braise', 'goulash', 'cassoulet', 'stroganoff', 'tagine',
             'hotchpotch', 'scouse', 'hotpot', 'pot', 'stockpot', 'crock', 'beans', 'chili',
             'boil', 'cauldron', 'kettle', 'casserole', 'curry', 'jambalaya', 'moqueca'),
    'chowder': ('chowder', 'gumbo', 'bisque', 'velouté', 'veloute'),
    'porridge': ('porridge', 'gruel', 'grits', 'granola', 'mash', 'purée', 'puree', 'polenta',
                 'risotto', 'couscous', 'pilaf', 'kedgeree', 'dal', 'colcannon'),
    'drink': ('tea', 'tonic', 'cordial', 'infusion', 'syrup', 'punch', 'brew', 'bitters', 'draught',
              'elixir', 'nectar', 'cider', 'grog', 'posset', 'tisane', 'froth', 'mead', 'wine',
              'theriac'),
    'roast': ('roast', 'roasted', 'roulade', 'loin', 'barbecue', 'ham', 'wellington', 'joint'),
    # A baked dish: a roast if it holds meat, else a crust.
    'bake': ('bake',),
    'leg': ('leg', 'legs', 'drumstick', 'drumsticks', 'drumettes', 'shank', 'shanks', 'haunch', 'confit',
            'hock', 'trotters', 'ribs', 'rack', 'marrowbones', 'wings'),
    'steak': ('steak', 'steaks', 'medallions', 'rump', 'sirloin', 'cutlet', 'cutlets', 'chop', 'chops',
              'escalope', 'schnitzel', 'grill', 'tail', 'flank'),
    # A cooked breakfast or a mixed grill: the cook makes sausages of the meat too.
    'fryup': ('breakfast', 'fry-up', 'eggs', 'omelette'),
    'sausage': ('sausage', 'sausages', 'links', 'bangers', 'rashers', 'bacon', 'haggis', 'boudin',
                'salami', 'chorizo'),
    'skewer': ('skewer', 'skewers', 'kebab', 'kebabs', 'spit', 'brochettes'),
    'stirfry': ('stir-fry', 'skillet', 'glaze', 'wok', 'hash', 'fricassee', 'sauté', 'saute',
                'mushrooms', 'teriyaki', 'devilled'),
    'fritter': ('fritters', 'tempura', 'crisps', 'crackling', 'scratchings', 'nuggets', 'brittle',
                'candy', 'toffee', 'toasted'),
    'flambe': ('flambé', 'flambe'),
    # A pot of melted cheese and whatever is dipped in it.
    'fondue': ('fondue',),
    'platter': ('platter', 'board', 'plate', 'fillet', 'fillets', 'slices', 'salad', 'slaw', 'terrine',
                'pâté', 'pate', 'carpaccio', 'sashimi', 'tartare', 'ceviche', 'medley'),
    'pie': ('pie', 'pies', 'pasty', 'pasties', 'pirozhki', 'pirog', 'cobbler', 'crumble', 'quiche',
            'tart', 'tarts', 'galette', 'pithivier'),
    'dumpling': ('dumpling', 'dumplings', 'bun', 'buns', 'bao', 'puffs', 'wontons', 'pelmeni', 'momos',
                 'parcels'),
    'bread': ('sandwich', 'roll', 'rolls', 'butty', 'trencher', 'burger', 'cheeseburger', 'bread', 'loaf',
              'toast', 'crackers', 'flatbread', 'flatbreads', 'pancake', 'pancakes', 'crêpe', 'crepes',
              'blini', 'oatcakes', 'bannock', 'tortilla', 'cakes'),
    'jelly': ('jelly', 'aspic', 'wobble', 'blancmange'),
    'pickle': ('pickle', 'pickles', 'relish', 'preserve', 'preserves', 'jam', 'compote', 'chutney',
               'marmalade', 'honey', 'conserve'),
    'pudding': ('pudding', 'custard', 'flan', 'soufflé', 'souffle', 'sorbet', 'trifle', 'junket',
                'syllabub'),
    # A meal names no form: what it holds decides its picture.
    'meal': ('supper', 'feast', 'banquet', 'dinner', 'spread'),
}
# Phrases that end a name and beat its last word ("Black Pudding Pie" is a pie).
FORM_PHRASES = (
    (r'(black|blood(-[a-z]+)?) pudding$', 'sausage'),
    (r'leg roast$', 'leg'),
    (r'sausage bake$', 'sausage'),
    (r'mixed grill$', 'fryup'),
)
DEFAULT_FORM = 'stew'
_WORD_FORM = {w: k for k, ws in FORM_WORDS.items() for w in ws}

# The picture forms each dish form may show: 0 its own; 1 one that reads the
# same (FAIR); 2 a near stand-in and 3 a far one, shown only when nothing fair
# exists (and the dish goes on the no-match list). A near stand-in is less
# wrong than a food the dish lacks (fried mushrooms as fritters, not as meat
# strips); a far one is more wrong (a sandwich stays a sandwich, not a
# dumpling). A picture form not listed is never shown.
FORM_FIT = {
    # a clear broth is not a creamy chowder: a soup keeps a soup's picture
    'soup': {'soup': 0, 'chowder': 2, 'stew': 2, 'drink': 3},
    'stew': {'stew': 0, 'chowder': 1, 'soup': 2, 'porridge': 3},
    'chowder': {'chowder': 0, 'stew': 1, 'soup': 2},
    'porridge': {'porridge': 0, 'chowder': 2, 'pudding': 3, 'stew': 3},
    'drink': {'drink': 0, 'soup': 3},
    'roast': {'roast': 0, 'leg': 2, 'platter': 2, 'steak': 3, 'flambe': 3},
    'bake': {'roast': 0, 'pie': 0, 'bread': 3},
    'leg': {'leg': 0, 'roast': 2, 'steak': 3},
    'steak': {'steak': 0, 'flambe': 3, 'roast': 3, 'platter': 3, 'leg': 3, 'stirfry': 3},
    'fryup': {'steak': 0, 'sausage': 2, 'platter': 3, 'stirfry': 3},
    'sausage': {'sausage': 0, 'steak': 3, 'roast': 3},
    'skewer': {'skewer': 0, 'stirfry': 2, 'steak': 3},
    'stirfry': {'stirfry': 0, 'fritter': 2, 'steak': 3},
    'fritter': {'fritter': 0, 'stirfry': 3},
    'flambe': {'flambe': 0, 'steak': 3, 'roast': 3},
    'fondue': {'chowder': 0, 'flambe': 3},
    # cold sliced meat reads the same as a carved roast
    'platter': {'platter': 0, 'roast': 1, 'steak': 3},
    'pie': {'pie': 0, 'dumpling': 3, 'bread': 3},
    # a bun or a bao reads as a stuffed roll
    'dumpling': {'dumpling': 0, 'bread': 1, 'pie': 3},
    'bread': {'bread': 0, 'pie': 3, 'dumpling': 3},
    'jelly': {'jelly': 0, 'pudding': 1},
    'pickle': {'pickle': 0, 'jelly': 2, 'porridge': 3},
    'pudding': {'pudding': 0, 'jelly': 1, 'porridge': 2},
    # a meal is a stew or a platter as what it holds says, else any plate
    'meal': {'stew': 0, 'platter': 0, 'roast': 1, 'soup': 1, 'leg': 1, 'steak': 1, 'sausage': 1,
             'bread': 1, 'pie': 1},
}
FAIR_RANK = 1
# How wrong a stand-in form is, counted against the foods a picture wrongly shows.
STAND_IN_COST = {0: 0, 1: 0, 2: 0.5, 3: 1.5}

# What the no-match list says a dish's picture should be.
FORM_NOUN = {
    'soup': 'a bowl of broth', 'stew': 'a stew', 'chowder': 'a creamy chowder',
    'porridge': 'a bowl of porridge or mash', 'drink': 'a drink in a cup', 'roast': 'a roast',
    'leg': 'a roast leg on the bone', 'steak': 'a grilled steak', 'fryup': 'a fry-up or mixed grill',
    'bake': 'a bake', 'fondue': 'a pot of fondue',
    'sausage': 'sausages', 'skewer': 'skewers', 'stirfry': 'a stir-fry', 'fritter': 'fritters',
    'flambe': 'a dish in flames', 'platter': 'a platter', 'pie': 'a pie', 'dumpling': 'dumplings',
    'bread': 'a sandwich, toast or loaf', 'jelly': 'a moulded jelly', 'pickle': 'a pot of pickle or preserve',
    'pudding': 'a pudding', 'meal': 'a meal',
}

# ----------------------------------------------------------------------
# What a dish contains, from its ingredients
# ----------------------------------------------------------------------

# A creature's part, by its `part` in ingredient.json: what it is on a plate.
# 'blood', 'scale' and the rest are contents no picture draws; they matter for
# what the cook makes (a black pudding is blood) and for the no-match list.
PART_FOODS = {
    'cut': ('meat', 'bone'),           # a cut of the creature, on the bone
    'bone': ('bone', 'meat'),          # a shank, a femur, its marrow
    'sac': ('meat',),                  # offal: a gland, a bladder, a stomach
    'ichor': ('blood',),               # blood, bile, venom: no flesh
    'scale': ('scale',),               # hide and scale, rendered crisp: no flesh
    'trophy': ('meat',),
    'core': ('crystal',),              # a construct's heart: no flesh
    'mote': ('ember',),                # a fey acorn, ember or spark
    'jar': ('element',),               # an elemental's bottled stuff
    'wood': ('plant',),                # a vine, a stalk, a log
    'forage': (),                      # by its name below
}
# Words in an ingredient's name that change what it is on a plate.
WORD_FOODS = (
    (('ectoplasm', 'jelly'), ('jelly',), True),                  # a ghost's: no flesh
    (('mushroom', 'fungus', 'myconid', 'spore'), ('mushroom',), False),
    (('flesh',), ('meat',), False),
    (('sausage', 'sausages', 'links', 'bangers', 'bacon'), ('sausage',), False),  # a part that is one
)
# A family whose cut shows as a whole roast bird; a family whose sac is slime.
FAMILY_FOODS = {'birds': ('whole_bird',)}
FAMILY_NOT_FLESH = ('oozes',)
# The staples and special foods (data/items/food.json).
STAPLE_FOODS = {
    'dried_meat': ('meat',),
    'trail_rations': ('meat', 'bread'),     # jerky and hardtack
    'bread_ration': ('bread',),
    'elvish_bread': ('bread',),
    'hard_cheese': ('cheese',),
    'wild_mushroom': ('mushroom',),
    'hearty_stew': ('meat', 'potato'),
    'apple': ('fruit',), 'golden_apple': ('fruit',), 'tantalus_plum': ('fruit',),
    'peach_of_immortality': ('fruit',), 'starnut_tart': ('bread',),
    'healing_herb': ('herbs',), 'tater_tots': ('potato',), 'magic_dungeon_carrot': ('potato',),
    'caviar': ('fish',),
}
# What the cook makes for a form from what the dish holds.
FORM_MAKES = {
    'sausage': (('meat', 'blood', 'jelly'), 'sausage'),   # sausages, a black pudding, a haggis
    'fryup': (('meat',), 'sausage'),
    'bread': ((), 'bread'),                      # a sandwich's or toast's own bread
}

_ings = None


def _ingredients():
    global _ings
    if _ings is None:
        with open(os.path.join(ITEMS, 'ingredient.json'), encoding='utf-8') as f:
            _ings = json.load(f)
    return _ings


def ingredient_foods(iid: str, ings=None) -> set:
    """What one ingredient is on a plate."""
    ings = _ingredients() if ings is None else ings
    if iid in STAPLE_FOODS:
        return set(STAPLE_FOODS[iid])
    ing = ings.get(iid)
    if not ing:
        return set()
    out = set(PART_FOODS.get(ing.get('part'), ()))
    words = set(re.split(r"[\s'’-]+", ing.get('name', '').lower()))
    for keys, foods, replace in WORD_FOODS:
        if words & set(keys):
            out = set(foods) if replace else out | set(foods)
    if ing.get('family') in FAMILY_NOT_FLESH:
        out -= {'meat', 'bone'}
        out.add('jelly')
    if ing.get('part') == 'cut':
        out |= set(FAMILY_FOODS.get(ing.get('family'), ()))
    return out


def contents(ingredients, form: str, ings=None) -> set:
    """Everything a dish holds, and what its form makes of it."""
    has = set()
    for iid in ingredients:
        has |= ingredient_foods(iid, ings)
    need, makes = FORM_MAKES.get(form, ((), None))
    if makes and (not need or has & set(need)):
        has.add(makes)
    return has


# ----------------------------------------------------------------------
# The pictures
# ----------------------------------------------------------------------

_cat = None


def catalogue() -> dict:
    """dish_pictures.json: the vocabulary and every ordinary picture."""
    global _cat
    if _cat is None:
        with open(CATALOGUE, encoding='utf-8') as f:
            _cat = json.load(f)
    return _cat


def counted_foods() -> set:
    return {k for k, v in catalogue()['foods'].items() if v.get('counts')}


def parse(art: str):
    """dish_<form>_t<tier>_<tab> -> (name form, tier, tab)."""
    kind, t, tab = art[5:].rsplit('_', 2)
    return kind, int(t[1:]), tab


_pics = {}


def pictures(have=None) -> dict:
    """picture id -> (form, tier, tab, counted foods), for every catalogued
    picture that is drawn (``have``: the drawn ids, default the folder)."""
    key = None if have is None else frozenset(have)
    if key not in _pics:
        have = drawn() if have is None else have
        count = counted_foods()
        out = {}
        for pid, p in catalogue()['pictures'].items():
            if pid in have:
                _, tier, tab = parse(pid)
                out[pid] = (p['form'], tier, tab, frozenset(set(p['foods']) & count))
        _pics[key] = out
    return _pics[key]


def drawn(art_dir: str = ART_DIR) -> set:
    """Every dish picture that exists."""
    try:
        names = os.listdir(art_dir)
    except OSError:
        return set()
    return {n[:-4] for n in names if n.startswith('dish_') and n.endswith('.png')}


# ----------------------------------------------------------------------
# The rule
# ----------------------------------------------------------------------

def dish_form(name: str) -> str:
    """The form a name says: a phrase first, then its last form word."""
    low = name.lower().replace(',', ' ').strip()
    for pat, form in FORM_PHRASES:
        if re.search(pat, low):
            return form
    for tok in reversed(low.split()):
        tok = tok.strip("'’")
        if tok in _WORD_FORM:
            return _WORD_FORM[tok]
    return DEFAULT_FORM


def tab_of(benefit: str) -> str:
    """The menu tab of a dish's main benefit (kitchen.dish_tab)."""
    if benefit in ('hp', 'sp', 'mp'):
        return benefit
    return 'stat' if benefit in STATS else 'special'


def art_id(form: str, tier: int, tab: str) -> str:
    return f'dish_{form}_t{int(tier)}_{tab}'


def judge(name: str, ingredients, tier: int, benefit: str, have=None, ings=None) -> dict:
    """The rule's whole answer for one ordinary dish: the picture, and why.

    Keys: art, form, has (contents), fair, rank (FORM_FIT of the picture),
    foreign (counted foods it shows that the dish lacks), shows (counted
    foods it shows that the dish has)."""
    form = dish_form(name)
    has = contents(ingredients, form, ings)
    tab = tab_of(benefit)
    fit = FORM_FIT[form]
    order = list(fit)
    best = None
    for pid, (pform, ptier, ptab, foods) in pictures(have).items():
        rank = fit.get(pform)
        if rank is None:
            continue
        foreign = foods - has
        fair = rank <= FAIR_RANK and not foreign
        key = (not fair, len(foreign) + STAND_IN_COST[rank], abs(ptier - tier), ptier > tier, rank,
               TAB_NEAR[tab].index(ptab), -len(foods & has), order.index(pform), pid)
        if best is None or key < best[0]:
            best = (key, pid, rank, foreign, foods & has, fair)
    if best is None:
        raise KeyError(f'no picture of any form {name!r} may show ({form})')
    _, pid, rank, foreign, shows, fair = best
    return {'art': pid, 'form': form, 'has': has, 'fair': fair, 'rank': rank,
            'foreign': set(foreign), 'shows': set(shows)}


def art_for(name: str, tier: int, benefit: str, have=None, ingredients=(), ings=None) -> str:
    """The picture of an ordinary dish (``judge``)."""
    return judge(name, ingredients, tier, benefit, have, ings)['art']


# The 36 legendary feasts: recipe id -> its own picture. Each is drawn for
# that feast from its name, flavour and lore (a grand spread on a gilded
# platter with the creature's motif).
FEASTS = {
    'feast_01': 'feast_bull_kings_wrath',
    'feast_02': 'feast_witch_oven_labyrinth',
    'feast_03': 'feast_gorgon_ironblood',
    'feast_04': 'feast_athena_owl_wise',
    'feast_05': 'feast_sigurd_hearth_roast',
    'feast_06': 'feast_dragonfire_cassoulet',
    'feast_07': 'feast_ragnarok_eve',
    'feast_08': 'feast_wolf_age_black_pudding',
    'feast_09': 'feast_bottomless_pit',
    'feast_10': 'feast_locust_heart',
    'feast_11': 'feast_green_chapel_yule',
    'feast_12': 'feast_evergreen_undying',
    'feast_13': 'feast_root_of_the_world',
    'feast_14': 'feast_serpent_king_antidote',
    'feast_15': 'feast_norns_supper',
    'feast_16': 'feast_crone_midnight_cauldron',
    'feast_17': 'feast_crimson_court',
    'feast_18': 'feast_warlord_blood',
    'feast_19': 'feast_five_fire_dragon',
    'feast_20': 'feast_chaos_sea_starlight',
    'feast_21': 'feast_signed_in_blood',
    'feast_22': 'feast_hellfire_prince',
    'feast_23': 'feast_muspelheim_forge',
    'feast_24': 'feast_flaming_sword',
    'feast_25': 'feast_ginnungagap_frost',
    'feast_26': 'feast_first_giant_marrow',
    'feast_27': 'feast_stone_heart_giant',
    'feast_28': 'feast_whetstone_hearth_pie',
    'feast_29': 'feast_first_seal_wrath',
    'feast_30': 'feast_plague_breaker',
    'feast_31': 'feast_end_of_famine',
    'feast_32': 'feast_king_of_hell_war_roast',
    'feast_33': 'feast_last_breath',
    'feast_34': 'feast_earthshaker',
    'feast_35': 'feast_seventh_seal_silent',
    'feast_36': 'feast_hut_on_chicken_legs',
}


def is_ordinary(rec: dict) -> bool:
    """A dish the rule places (not a feast, a trophy dish or a song's)."""
    return not (rec.get('trophy') or rec.get('song') or rec.get('legendary'))


def recipe_art(rid: str, rec: dict, tier: int, have=None, ings=None) -> str:
    """The picture of any recipe in the book."""
    if rec.get('trophy'):
        return f'recipe_{rid}'
    if rec.get('song'):
        # A dish that plays a song (songs.py) shows the song's own art: the
        # plate from its album cover (genart/caviar_album_art.py).
        return f"song_{rec['song']}"
    if rec.get('legendary'):
        if rid not in FEASTS:
            raise KeyError(f'legendary feast {rid} has no picture of its own in dish_art.FEASTS')
        return FEASTS[rid]
    return art_for(rec['name'], tier, rec['benefit'], have, rec.get('ingredients', ()), ings)


# ----------------------------------------------------------------------
# The no-match list, and writing the book
# ----------------------------------------------------------------------

def _food_words(foods) -> str:
    words = [f.replace('_', ' ') for f in sorted(foods)]
    return ' or '.join(words) if len(words) < 3 else ', '.join(words[:-1]) + ' or ' + words[-1]


def wants(verdict: dict, names=()) -> str:
    """What a dish's own picture should show, for the art to come: its form,
    what it is made of, and the foods its form's pictures show that it lacks."""
    form = verdict['form']
    text = FORM_NOUN[form]
    if names:
        text += ' of ' + ', '.join(names)
    exact = {p for p, r in FORM_FIT[form].items() if r == 0}
    shown = set()
    for pform, _t, _tab, foods in pictures().values():
        if pform in exact:
            shown |= foods
    lacks = (shown | verdict['foreign']) - verdict['has']
    if lacks:
        text += ', with no ' + _food_words(lacks)
    return text


def why(verdict: dict) -> str:
    bits = []
    if verdict['rank'] > FAIR_RANK:
        bits.append(f"no fair picture of its form; shows {FORM_NOUN[catalogue()['pictures'][verdict['art']]['form']]}")
    if verdict['foreign']:
        bits.append('shows ' + _food_words(verdict['foreign']) + ' it does not have')
    return '; '.join(bits)


def place_book(book: dict, tier_of, have=None, ings=None):
    """recipe id -> picture for every recipe (``tier_of``: kitchen.dish_tier),
    and the no-match list: recipe id -> what it shows and should show."""
    arts, lost = {}, {}
    names = {**_ingredients(), **_foods()}
    for rid, rec in book.items():
        if rid.startswith('_'):
            continue
        tier = tier_of(rec)
        if not is_ordinary(rec):
            arts[rid] = recipe_art(rid, rec, tier, have, ings)
            continue
        v = judge(rec['name'], rec.get('ingredients', ()), tier, rec['benefit'], have, ings)
        arts[rid] = v['art']
        if not v['fair']:
            lost[rid] = {
                'name': rec['name'],
                'ingredients': [_name(names, i) for i in rec.get('ingredients', ())],
                'tier': tier, 'benefit': tab_of(rec['benefit']), 'form': v['form'],
                'wants': wants(v, [_name(names, i) for i in rec.get('ingredients', ())]),
                'given': v['art'],
                'given_shows': catalogue()['pictures'][v['art']]['sees'],
                'why': why(v),
            }
    return arts, lost


def _name(names, iid):
    name = names.get(iid, {}).get('name', iid.replace('_', ' '))
    return name[:1].upper() + name[1:] if name.islower() else name


def _foods():
    with open(os.path.join(ITEMS, 'food.json'), encoding='utf-8') as f:
        return json.load(f)


def _dump(path, data, indent=1):
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write('\n')


def write(book_path=os.path.join(ITEMS, 'recipes.json')):
    """Re-place every dish's picture by the rule: recipes.json `art`, the
    record dish_art.json and the no-match list."""
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import kitchen
    with open(book_path, encoding='utf-8') as f:
        book = json.load(f)
    arts, lost = place_book(book, kitchen.dish_tier)
    changed = [rid for rid, a in arts.items() if book[rid].get('art') != a]
    for rid, a in arts.items():
        book[rid]['art'] = a
    _dump(book_path, book)
    _dump(RECORD, {'_doc': RECORD_DOC, **dict(sorted(arts.items()))})
    gaps = Counter()
    for rid, rec in book.items():
        if is_ordinary(rec):
            form = dish_form(rec['name'])
            t, tab = kitchen.dish_tier(rec), kitchen.dish_tab(rec)
            pform, pt, ptab = catalogue()['pictures'][rec['art']]['form'], *parse(rec['art'])[1:]
            if FORM_FIT[form].get(pform) != 0 or pt != t or ptab != tab or rid in lost:
                gaps[f'{form} t{t} {tab}'] += 1
    _dump(NO_MATCH, {
        '_doc': ('Dishes with NO fair picture yet (dish_art.py: a picture of its own form, or one '
                 'that reads the same, showing no food it does not contain). Each shows the least '
                 'wrong picture drawn (given) until art is made for it (wants). Written by '
                 '`py tools/content/kitchen/dish_art.py --write`; tests/test_dish_art.py checks the '
                 'list is exactly the dishes the rule cannot place, and that it only shrinks. '
                 '`wanted` counts, for the art to come, the dishes per form, tier and benefit that '
                 'show another form, tier or benefit today.'),
        'dishes': dict(sorted(lost.items())),
        'wanted': dict(sorted(gaps.items(), key=lambda kv: (-kv[1], kv[0]))),
    })
    return changed, lost


def report(book_path=os.path.join(ITEMS, 'recipes.json')):
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import kitchen
    with open(book_path, encoding='utf-8') as f:
        book = json.load(f)
    arts, lost = place_book(book, kitchen.dish_tier)
    changed = [rid for rid, a in arts.items() if book[rid].get('art') != a]
    ordinary = [rid for rid in arts if is_ordinary(book[rid])]
    print(f'{len(arts)} dishes; {len(ordinary)} ordinary; {len(changed)} would change picture; '
          f'{len(lost)} have no fair picture; {len(set(arts[r] for r in ordinary))} pictures used')
    for art, n in Counter(arts[r] for r in ordinary).most_common(10):
        print(f'  {art}: {n}')
    return changed, lost


if __name__ == '__main__':
    if '--write' in sys.argv:
        ch, lo = write()
        print(f'{len(ch)} dishes changed picture; {len(lo)} on the no-match list')
    else:
        report()
