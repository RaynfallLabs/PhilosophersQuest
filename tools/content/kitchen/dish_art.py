"""Which picture each dish shows (the kitchen's dish art, 2026-11-14).

A dish's picture says three things:
  - its KIND, read from its name (a stew, a pie, skewers, a roast...);
  - its TIER, by the vessel (dark walnut wood, tawny clay, black iron,
    bright silver, jewelled gold, for tiers 1 to 5);
  - its MAIN BENEFIT (its menu tab), by one colour cue in the food: warm red
    for HP, amber-gold for SP, glowing deep blue for MP, emerald green for
    Stat, violet for Special.

The pictures are ``assets/tiles/items/dish_<kind>_t<tier>_<tab>.png``. Not
every kind is drawn at every tier and tab: ``stew`` and ``roast`` are drawn
for all 25 (tier, tab) pairs, the other kinds where the book has dishes of
them. A dish whose own kind has no picture at its tier and tab takes the
nearest kind that has one (``FALLBACK``), always ending at the stew, so its
vessel and colour stay true. The 36 legendary feasts each have a picture of
their own (``FEASTS``); the 14 boss-trophy dishes keep their boss's picture
(``recipe_<recipe id>.png``).

The pick reads only the name, tier and benefit, so a rebuilt book with new or
renamed dishes gets the right pictures with no table to edit:

    py tools/content/kitchen/dish_art.py     # prints the map and the counts

``build_kitchen.py`` calls ``art_for`` for every dish and writes the result
to ``dish_art.json`` beside it (recipe id -> picture), a record to read.
The design of each picture is in ``_genart/dishes/KINDS.md`` (work files).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART_DIR = os.path.join(ROOT, 'assets', 'tiles', 'items')

TABS = ('hp', 'sp', 'mp', 'stat', 'special')
STATS = ('STR', 'DEX', 'CON', 'INT', 'WIS', 'PER')

# Name words -> kind. The LAST kind word in a name decides ("Kuo-Toa Brine Ham
# Stew" is a stew, "Steak Sandwich" a sandwich), after the phrases below.
KIND_WORDS = {
    'soup': ('soup', 'broth', 'stock', 'consommé', 'consomme', 'noodles', 'ramen', 'pho',
             'reduction', 'sauce', 'gravy', 'jus'),
    'stew': ('stew', 'ragout', 'pottage', 'braise', 'goulash', 'cassoulet', 'stroganoff', 'tagine',
             'hotchpotch', 'scouse', 'supper', 'hotpot', 'pot', 'stockpot', 'crock', 'beans', 'chili',
             'boil', 'cauldron', 'kettle', 'feast', 'banquet'),
    'chowder': ('chowder', 'gumbo', 'bisque', 'velouté', 'veloute'),
    'porridge': ('porridge', 'gruel', 'grits', 'granola', 'mash', 'purée', 'puree', 'polenta',
                 'risotto', 'couscous', 'jambalaya', 'curry', 'pilaf', 'kedgeree', 'dal', 'colcannon'),
    'drink': ('tea', 'tonic', 'cordial', 'infusion', 'syrup', 'punch', 'brew', 'bitters', 'draught',
              'elixir', 'nectar', 'cider', 'grog', 'posset', 'tisane', 'froth', 'mead', 'wine'),
    'roast': ('roast', 'roulade', 'loin', 'bake', 'barbecue', 'ham', 'wellington', 'joint'),
    'leg': ('leg', 'legs', 'drumstick', 'drumsticks', 'drumettes', 'shank', 'shanks', 'haunch', 'confit',
            'hock', 'trotters', 'ribs', 'rack', 'marrowbones', 'wings'),
    'steak': ('steak', 'steaks', 'medallions', 'rump', 'sirloin', 'cutlet', 'cutlets', 'chop', 'chops',
              'escalope', 'schnitzel', 'grill', 'breakfast', 'fry-up', 'eggs', 'omelette', 'tail'),
    'sausage': ('sausage', 'sausages', 'links', 'bangers', 'rashers', 'bacon', 'haggis', 'boudin',
                'salami', 'chorizo'),
    'skewer': ('skewer', 'skewers', 'kebab', 'kebabs', 'spit', 'brochettes'),
    'stirfry': ('stir-fry', 'skillet', 'glaze', 'wok', 'hash', 'fricassee', 'sauté', 'saute',
                'mushrooms', 'teriyaki', 'devilled'),
    'fritter': ('fritters', 'tempura', 'crisps', 'crackling', 'scratchings', 'nuggets', 'brittle',
                'candy', 'toffee'),
    'flambe': ('flambé', 'flambe', 'fondue'),
    'platter': ('platter', 'board', 'plate', 'fillet', 'fillets', 'slices', 'salad', 'slaw', 'terrine',
                'pâté', 'pate', 'carpaccio', 'sashimi', 'tartare', 'ceviche', 'medley'),
    'pie': ('pie', 'pies', 'pasty', 'pasties', 'pirozhki', 'pirog', 'cobbler', 'crumble', 'quiche',
            'tart', 'tarts', 'galette', 'pithivier'),
    'dumpling': ('dumpling', 'dumplings', 'bun', 'buns', 'bao', 'puffs', 'wontons', 'pelmeni', 'momos',
                 'parcels'),
    'bread': ('sandwich', 'roll', 'rolls', 'butty', 'trencher', 'burger', 'cheeseburger', 'bread', 'loaf',
              'toast', 'crackers', 'flatbread', 'flatbreads', 'pancake', 'pancakes', 'crêpe', 'crepes',
              'blini', 'oatcakes', 'bannock', 'tortilla'),
    'jelly': ('jelly', 'aspic', 'wobble', 'blancmange'),
    'pickle': ('pickle', 'pickles', 'relish', 'preserve', 'preserves', 'jam', 'compote', 'chutney',
               'marmalade', 'honey', 'conserve'),
    'pudding': ('pudding', 'custard', 'flan', 'soufflé', 'souffle', 'sorbet', 'trifle', 'junket',
                'syllabub'),
}
# Phrases that beat the last word.
KIND_PHRASES = (
    (r'black pudding|blood(-[a-z]+)? pudding', 'sausage'),
    (r'leg roast', 'leg'),
    (r'sausage bake', 'sausage'),
)
DEFAULT_KIND = 'stew'
_WORD_KIND = {w: k for k, ws in KIND_WORDS.items() for w in ws}

# A kind with no picture at a dish's tier and tab shows the nearest kind that
# has one. Every chain ends at the stew, drawn for all 25 (tier, tab) pairs.
FALLBACK = {
    'soup': ('soup', 'chowder', 'stew'),
    'stew': ('stew',),
    'chowder': ('chowder', 'soup', 'stew'),
    'porridge': ('porridge', 'stew'),
    'drink': ('drink', 'soup', 'stew'),
    'roast': ('roast', 'leg', 'steak', 'stew'),
    'leg': ('leg', 'roast', 'steak', 'stew'),
    'steak': ('steak', 'roast', 'leg', 'stew'),
    'sausage': ('sausage', 'steak', 'roast', 'stew'),
    'skewer': ('skewer', 'steak', 'roast', 'stew'),
    'stirfry': ('stirfry', 'steak', 'roast', 'stew'),
    'fritter': ('fritter', 'stirfry', 'steak', 'roast', 'stew'),
    'flambe': ('flambe', 'roast', 'steak', 'stew'),
    'platter': ('platter', 'steak', 'roast', 'stew'),
    'pie': ('pie', 'dumpling', 'bread', 'roast', 'stew'),
    'dumpling': ('dumpling', 'pie', 'bread', 'roast', 'stew'),
    'bread': ('bread', 'pie', 'roast', 'stew'),
    'jelly': ('jelly', 'pudding', 'pickle', 'stew'),
    'pickle': ('pickle', 'jelly', 'stew'),
    'pudding': ('pudding', 'jelly', 'stew'),
}
# The kinds drawn for every (tier, tab), so every chain can end.
EVERYWHERE = ('stew', 'roast')

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


def dish_kind(name: str) -> str:
    """The kind of dish a name says: a phrase first, then its last kind word."""
    low = name.lower().replace(',', ' ')
    for pat, kind in KIND_PHRASES:
        if re.search(pat, low):
            return kind
    for tok in reversed(low.split()):
        tok = tok.strip("'’")
        if tok in _WORD_KIND:
            return _WORD_KIND[tok]
    return DEFAULT_KIND


def tab_of(benefit: str) -> str:
    """The menu tab of a dish's main benefit (kitchen.dish_tab)."""
    if benefit in ('hp', 'sp', 'mp'):
        return benefit
    return 'stat' if benefit in STATS else 'special'


def art_id(kind: str, tier: int, tab: str) -> str:
    return f'dish_{kind}_t{int(tier)}_{tab}'


def drawn(art_dir: str = ART_DIR) -> set:
    """Every dish picture that exists."""
    try:
        names = os.listdir(art_dir)
    except OSError:
        return set()
    return {n[:-4] for n in names if n.startswith('dish_') and n.endswith('.png')}


def art_for(name: str, tier: int, benefit: str, have=None) -> str:
    """The picture of an ordinary dish: its kind's at its tier and tab, or the
    nearest kind drawn there. Raises if not even the stew is drawn there."""
    have = drawn() if have is None else have
    tab = tab_of(benefit)
    for kind in FALLBACK[dish_kind(name)]:
        art = art_id(kind, tier, tab)
        if art in have:
            return art
    raise KeyError(f'no dish picture for {name!r} at tier {tier}, {tab} (draw {art_id(DEFAULT_KIND, tier, tab)})')


def recipe_art(rid: str, rec: dict, tier: int, have=None) -> str:
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
    return art_for(rec['name'], tier, rec['benefit'], have)


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import kitchen  # noqa: E402
    have = drawn()
    out = {}
    for r in kitchen.book():
        out[r['id']] = recipe_art(r['id'], r, kitchen.dish_tier(r), have)
    from collections import Counter
    ordinary = {rid: a for rid, a in out.items() if a.startswith('dish_')}
    own = sum(1 for r in kitchen.book() if out[r['id']].startswith(f"dish_{dish_kind(r['name'])}_t"))
    print(f'{len(out)} dishes show {len(set(out.values()))} pictures; {len(ordinary)} ordinary dishes show '
          f'{len(set(ordinary.values()))} of the {len([a for a in have if a.startswith("dish_")])} kind pictures, '
          f'{own} of them their own kind')
    for art, n in Counter(ordinary.values()).most_common(8):
        print(f'  {art}: {n}')
