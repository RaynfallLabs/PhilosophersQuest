"""Brandon's three cooking rulings of 2026-11-16.

1. Fill the stat dishes in every tier: every stat (STR, CON, DEX, INT, WIS,
   PER) has stat dishes at every tier 1 to 5, each built from parts a hero
   can really get at that depth (its creature spawns there and its harvest
   gives the part, or the part is found there).
2. Humans are not harvested ("that's weird, we're not cannibals"): a person's
   body (humans and the human-like folk: tools/content/kitchen/people.txt,
   written to harvest_map.json "people") is SEARCHED, like picking something
   up: no question, the body used up, one or two ordinary finds of the
   floor's band. No dish calls for a part of a person, and an old save's
   held one becomes the ordinary food it was in his pack.
3. Every special food (food.json "special": the Magic Dungeon Carrot, the
   Starnut Tart, the mythic fruits) is in a decent dish of its own, of a
   tier where it is found; cooking it uses it up.

Data tests read the JSON; logic tests drive src/kitchen.py and
src/food_system.py; the journeys drive a headless Game with real keys. How
the search and the new dishes read to a kid is Brandon's play-test.
"""
import json
import math
import os
import pickle
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), os.path.join(ROOT, 'tests'), os.path.join(ROOT, 'tools', 'balance'),
           os.path.join(ROOT, 'tools', 'content', 'kitchen')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

import kitchen  # noqa: E402
import food_system  # noqa: E402

pygame.init()


def _json(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


MONSTERS = _json('monsters.json')
HMAP = _json('items', 'harvest_map.json')
INGS = _json('items', 'ingredient.json')
FOOD = _json('items', 'food.json')
RULES = _json('cooking_rules.json')
PEOPLE = set(HMAP['people'])
SPECIAL = {k for k, v in FOOD.items() if v.get('special')}

# The spawn pool's bell (dungeon._build_spawn_pool): a kind is in a floor's
# pool while exp(-(floor - peak)^2 / (2 spread^2)) >= 0.005.
_BELL = math.sqrt(2 * math.log(200))


def _band(floor):
    return (int(floor) - 1) // 20 + 1


def _spawn_floors(kind):
    m = MONSTERS.get(kind) or {}
    peak = m.get('peak_floor', m.get('min_level', 1)) or 1
    if (m.get('peak_weight', 0) or 0) > 0:
        lo = int(m.get('min_level', 1) or 1)
        spread = max(1, m.get('spread', 10))
        return {f for f in range(max(1, lo), 101) if abs(f - peak) <= spread * _BELL}
    if (m.get('is_boss') or m.get('is_mini_boss')) and 1 <= int(peak) <= 100:
        return {int(peak)}                       # placed on its own floor
    return set()


def _obtain_floors(part):
    """Every floor a part can be got on: its kin spawn there (and their
    harvest gives it), or it is found there (forage from its first floor;
    food where it spawns)."""
    if part in INGS and INGS[part].get('tier_role') == 'dungeon':
        return set(range(int(INGS[part]['min_level']), 101))
    if part in INGS:
        out = set()
        for kind, iid in HMAP['monsters'].items():
            if iid == part:
                out |= _spawn_floors(kind)
        return out
    rec = FOOD.get(part) or {}
    weights = rec.get('floor_spawn_weight') or rec.get('floorSpawnWeight') or {}
    out = set()
    for key, w in weights.items():
        if (w or 0) <= 0:
            continue
        a, _, b = str(key).partition('-')
        out |= set(range(int(a), int(b or a) + 1))
    return out


def _obtainable_at_tier(rec, tier):
    """Every part can be had by the end of ``tier``'s band, and the deepest
    part within its own band (the dish's tier, or the band below for a big
    dish, which is a tier richer than its deepest part: cooking_rules.json
    big_dish)."""
    top = 20 * tier
    parts = kitchen.parts(rec)
    floors = {p: _obtain_floors(p) for p in parts}
    if any(not fs or min(fs) > top for fs in floors.values()):
        return False
    deepest = max(parts, key=kitchen.part_floor)
    base = kitchen.base_tier(rec)
    return any(20 * (base - 1) + 1 <= f <= 20 * base for f in floors[deepest])


# ---------------------------------------------------------------------------
# Ruling 1: every stat, every tier
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('stat', kitchen.STATS)
@pytest.mark.parametrize('tier', [1, 2, 3, 4, 5])
def test_every_stat_has_stat_dishes_at_every_tier_obtainable_at_that_depth(stat, tier):
    """At least one stat dish of every stat at every tier, its parts ones a
    hero can get at that depth (Brandon: "at least one stat dish per stat per
    tier, ideally two where a tier is thin"). Two are pinned: the gaps of
    2026-11-16 (Dexterity at tiers 4 and 5, Intelligence at 4, Perception at
    5) were filled with two each."""
    ok = [r['id'] for r in kitchen.book()
          if kitchen.dish_stat(r) == stat and kitchen.dish_tier(r) == tier
          and _obtainable_at_tier(r, tier)]
    assert len(ok) >= 2, (stat, tier, ok)


def test_the_census_has_no_stat_left_without_a_tier():
    import tier_census
    rows = {r['category']: r for r in tier_census.census()['rows']}
    for stat in kitchen.STATS:
        row = rows[f'Dishes: Stat {stat}']
        assert min(row['counts']) >= 2, (stat, row['counts'])
        assert row['verdict'] != 'gap', stat


def test_a_deep_stat_dish_teaches_up_to_its_tiers_cap():
    """The new deep Dexterity dish lets food raise Dexterity past tier 3's
    cap: a dish of tier 5 teaches toward +28."""
    from player import Player
    rec = kitchen.recipe('dish_350')
    assert kitchen.dish_stat(rec) == 'DEX' and kitchen.dish_tier(rec) == 5
    p = Player()
    p.deepest_floor_reached = 90
    caps = RULES['stat']['cap_by_tier']
    assert p.cooking_stat_softcap('DEX', 5) == caps[4] > p.cooking_stat_softcap('DEX', 3)


# ---------------------------------------------------------------------------
# Big dishes +1 tier (Brandon, 2026-11-16, on a five-part Wild Game Pie of
# floors 1 to 4 that was only tier 1)
# ---------------------------------------------------------------------------

def test_a_big_dish_is_one_tier_above_its_deepest_part_and_the_rule_is_data():
    big = RULES['big_dish']
    assert big['parts'] == 4 and big['tier_bonus'] == 1
    for r in kitchen.book():
        base = kitchen.base_tier(r)
        if kitchen.dish_size(r) >= big['parts']:
            assert kitchen.dish_tier(r) == min(5, base + big['tier_bonus']), r['id']
        else:
            assert kitchen.dish_tier(r) == base, r['id']
    # A five-part dish of the top floors only: tier 2 now, not 1.
    pie = next(r for r in kitchen.book() if kitchen.dish_size(r) == 5 and kitchen.base_tier(r) == 1)
    assert kitchen.dish_tier(pie) == 2
    assert kitchen.big_dish_line(pie) == 'Five ingredients: one tier richer.'
    four = next(r for r in kitchen.book() if kitchen.dish_size(r) == 4 and kitchen.base_tier(r) == 2)
    assert kitchen.big_dish_line(four) == 'Four ingredients: one tier richer.'
    # Never past tier 5, and nothing to say when the tier is not raised.
    top = next(r for r in kitchen.book() if kitchen.dish_size(r) >= 4 and kitchen.base_tier(r) == 5)
    assert kitchen.dish_tier(top) == 5 and kitchen.big_dish_line(top) == ''
    small = next(r for r in kitchen.book() if kitchen.dish_size(r) == 3)
    assert kitchen.big_dish_line(small) == ''


def test_the_raised_tier_is_the_dishs_tier_everywhere():
    """The cook's question, the numbers, the stat cap it teaches to, the
    menu's tier chip and the line that says why, the picture's vessel."""
    import cook_menu
    from food_system import _recipe_quiz_tier
    from player import Player
    rec = next(r for r in kitchen.book() if kitchen.dish_stat(r) and kitchen.dish_size(r) >= 4
               and kitchen.base_tier(r) == 1)
    assert kitchen.dish_tier(rec) == 2
    assert _recipe_quiz_tier(rec) == 2
    assert kitchen.dish_outcome(rec)['tier'] == 2
    assert rec['art'].split('_t')[1].startswith('2_'), rec['art']
    p = Player()
    p.inventory = []
    row = kitchen._row(p, rec, kitchen.held_counts(p.inventory))
    assert row['tier'] == 2 and cook_menu.tier_line(row).endswith('2')
    assert cook_menu.big_dish_line(row) in ('Four ingredients: one tier richer.',
                                            'Five ingredients: one tier richer.')
    stat = kitchen.dish_stat(rec)
    caps = RULES['stat']['wis_cap_by_tier' if stat == 'WIS' else 'cap_by_tier']
    assert p.cooking_stat_softcap(stat, kitchen.dish_tier(rec)) == caps[1]
    assert any('Tier 2 dishes teach' in line for line in kitchen.dish_effects(p, rec))


# ---------------------------------------------------------------------------
# Ruling 2: people are searched, never harvested
# ---------------------------------------------------------------------------

def test_every_mortal_and_the_elves_and_dwarves_are_people():
    mortals = {k for k, v in MONSTERS.items() if isinstance(v, dict) and v.get('family') == 'mortals'}
    assert mortals <= PEOPLE, sorted(mortals - PEOPLE)
    for kind in ('dark_elf', 'drow_warrior', 'drow_mage', 'drow_priestess', 'light_elf_hostile',
                 'huldufolk_raider', 'nibelung_hoardwarden', 'little_john', 'king_arthur',
                 'einherjar', 'charlemagne', 'brigand', 'cult_priest', 'veiled_inquisitor'):
        assert kind in PEOPLE, kind
    # Goblinoids, orcs, gnolls, kobolds, lizardfolk, giants, ogres and the
    # undead stay as they were, and so do the beast-folk of myth.
    for kind in ('goblin', 'orc_warrior', 'gnoll', 'kobold', 'old_nickel', 'lizardfolk', 'hill_giant',
                 'ogre', 'skeleton', 'lich', 'zombie', 'werewolf', 'yuan_ti_pureblood', 'night_hag',
                 'baba_yaga', 'medusa', 'minotaur', 'death_mage'):
        assert kind not in PEOPLE, kind
        assert kitchen.ingredient_for_monster(kind), kind


def test_no_person_yields_an_ingredient_and_no_dish_holds_a_part_of_one():
    for kind in PEOPLE:
        assert kind in MONSTERS, kind
        assert kind not in HMAP['monsters'], kind
        assert kitchen.is_person(kind)
        assert food_system.corpse_ingredient(kind, 'mortals', 30) is None
    assert not [k for k, v in INGS.items() if v.get('family') == 'mortals']
    assert not [k for k, v in INGS.items() if v.get('source_monster') in PEOPLE]
    gone = set(HMAP['people_parts'])
    assert {'bandit_captain_prime', 'veteran_knight_prime', 'cult_initiate_prime',
            'dark_elf_prime', 'light_elf_hostile_prime'} <= gone
    for r in kitchen.book():
        assert not set(r['ingredients']) & gone, r['id']
    # No alias leads back to a person's part either.
    assert not set(HMAP['aliases']) & PEOPLE
    assert not set(HMAP['aliases'].values()) & gone


def test_a_stranger_of_the_mortals_is_a_person_and_has_no_kin_part():
    """A creature monsters.json does not know (Gilt Varro of the racing camp)
    whose body says mortals is a person: no nearest-kin part for him."""
    assert kitchen.is_person('varro_rider', 'mortals')
    assert food_system.corpse_ingredient('varro_rider', 'mortals', 55) is None
    assert not kitchen.is_person('varro_bird', 'birds')


@pytest.mark.parametrize('floor', [1, 5, 25, 45, 70, 95])
def test_a_search_gives_one_or_two_ordinary_finds_of_the_floors_band(floor):
    rng = random.Random(floor)
    pack = set(RULES['search']['pack'])
    for _ in range(200):
        ids = food_system.search_finds('brigand', floor, rng, tags=['humanoid', 'bandit'])
        assert 1 <= len(ids) <= 2, ids
        for fid in ids:
            assert not kitchen.is_harvested(fid), fid
            assert fid in FOOD or kitchen.part_kind(fid) == 'forage', fid
            assert kitchen.part_floor(fid) <= floor, (fid, floor)
            assert fid in pack or fid in RULES['search']['by_tag']['bandit'], fid
            assert not kitchen.is_special_food(fid), fid


def test_a_cultist_carries_his_incense_and_an_elf_his_waybread():
    rng = random.Random(3)
    cult = [food_system.search_finds('cult_priest', 12, rng, tags=['cultist']) for _ in range(40)]
    assert all(ids[0] == 'altar_incense' for ids in cult)
    elf = [food_system.search_finds('drow_mage', 15, rng, family='fair_folk') for _ in range(40)]
    assert all(ids[0] == 'elvish_bread' for ids in elf)
    # Elvish bread is first found on floor 10: a shallow elf carries none.
    shallow = [food_system.search_finds('dark_elf', 3, rng, family='fair_folk') for _ in range(40)]
    assert not any('elvish_bread' in ids for ids in shallow)


def _game():
    import items
    from main import Game
    from game_states import STATE_PLAYER
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_rulings_1116__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def test_h_on_a_brigands_body_searches_it_with_no_question():
    from food_system import make_corpse
    g = _game()
    asked = []
    g.quiz_engine.start_quiz = lambda **kw: asked.append(kw)
    p = g.player
    px, py = p.x, p.y
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (px, py)]
    g.ground_items.append(make_corpse('brigand', px, py))
    before = kitchen.held_counts(p.inventory)
    turn = g.turn_count if hasattr(g, 'turn_count') else None
    _press(g, pygame.K_h, 'h')
    assert not asked, 'a search asks no question'
    after = kitchen.held_counts(p.inventory)
    gained = {k: after[k] - before.get(k, 0) for k in after if after[k] > before.get(k, 0)}
    assert 1 <= sum(gained.values()) <= 2, gained
    for fid in gained:
        assert not kitchen.is_harvested(fid), fid
        assert fid in FOOD or kitchen.part_kind(fid) == 'forage', fid
    assert not any(getattr(i, 'monster_id', '') == 'brigand' for i in g.ground_items), 'the body is used up'
    msgs = ' '.join(str(e[0]) for e in g.msg_log.entries[-4:])
    assert 'You search the' in msgs and 'harvest' not in msgs.lower()
    if turn is not None:
        assert g.turn_count > turn


def test_a_creatures_body_is_still_harvested_with_its_question():
    from food_system import make_corpse
    g = _game()
    asked = []

    def quiz(**kw):
        asked.append(kw)
        kw['callback'](types.SimpleNamespace(success=True, score=1))
    g.quiz_engine.start_quiz = quiz
    p = g.player
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (p.x, p.y)]
    g.ground_items.append(make_corpse('goblin', p.x, p.y))
    _press(g, pygame.K_h, 'h')
    assert len(asked) == 1 and asked[0]['subject'] == 'animal'
    assert kitchen.held_counts(p.inventory).get('goblin_prime', 0) >= 1


def test_a_persons_corpse_page_says_search_not_harvest():
    from food_system import make_corpse
    g = _game()
    _identity, mechanics, _lore = g._lore_corpse_lines(make_corpse('veteran_knight', 0, 0), 5)
    texts = [m[0] for m in mechanics]
    assert any('searches the body' in t for t in texts), texts
    assert not any(t.startswith(('Harvest:', 'Ingredient:')) for t in texts), texts
    _identity, mechanics, _lore = g._lore_corpse_lines(make_corpse('goblin', 0, 0), 5)
    assert any(m[0].startswith('Harvest:') for m in mechanics)


def test_a_hunt_never_lights_a_person_gold():
    """In Sight's gold is for a creature whose harvest gives a hunted part:
    a person has none, whatever his pack might hold."""
    person = types.SimpleNamespace(kind='brigand')
    assert not kitchen.monster_hunted(person, {'bread_ration', 'dried_meat', 'hard_cheese'})


def test_an_old_saves_part_of_a_person_becomes_the_food_in_his_pack():
    from items import Ingredient, Food
    import main
    old = Ingredient({'id': 'bandit_captain_prime', 'name': 'Bandit Trail Ham', 'symbol': '~',
                      'color': [1, 1, 1], 'tier_role': 'prime'})
    old.count = 3
    old = pickle.loads(pickle.dumps(old))
    elf = pickle.loads(pickle.dumps(Ingredient({'id': 'light_elf_hostile_prime', 'name': 'Elf-Light Acorn',
                                                'symbol': '~', 'color': [1, 1, 1], 'tier_role': 'prime'})))
    ground = pickle.loads(pickle.dumps(Ingredient({'id': 'veteran_knight_prime',
                                                   'name': "Knight's Marching Ham", 'symbol': '~',
                                                   'color': [1, 1, 1], 'tier_role': 'prime'})))
    ground.x, ground.y = 4, 7
    inv = [old, elf]
    gi = [ground]
    fake = types.SimpleNamespace(player=types.SimpleNamespace(inventory=inv))
    main.Game._migrate_legacy_ingredients(fake, {'ground_items': gi, 'level_mgr': None})
    assert [type(i) for i in inv] == [Food, Food]
    assert inv[0].id == 'dried_meat' and inv[0].count == 3
    assert inv[1].id == 'elvish_bread'
    assert isinstance(gi[0], Food) and gi[0].id == 'dried_meat' and (gi[0].x, gi[0].y) == (4, 7)


def test_an_old_hunt_for_a_dish_that_is_gone_is_quietly_dropped():
    from player import Player
    p = Player()
    p.inventory = []
    p.hunted_dishes = {'cook_bandit_captain', 'dish_339'}
    assert 'magic_dungeon_carrot' in kitchen.hunted_parts(p)


# ---------------------------------------------------------------------------
# Ruling 3: every special food has a decent dish of its own
# ---------------------------------------------------------------------------

# Where each special food is found, by tier (Brandon: "a recipe of a tier
# matching where the item is found"): the carrot is placed once a run on
# floors 1 to 19 (game_encounters._maybe_spawn_magic_carrot); the Starnut
# Tart is cooked from starnuts (first found on floor 25) for the Mooble of
# floors 31 to 45; the fruits where they spawn.
FOUND_TIERS = {
    'magic_dungeon_carrot': {1},
    'starnut_tart': {2, 3},
}


def _found_tiers(fid):
    if fid in FOUND_TIERS:
        return FOUND_TIERS[fid]
    return {_band(f) for f in _obtain_floors(fid)}


def _special_dish(fid):
    hits = [r for r in kitchen.book() if fid in r['ingredients']]
    assert len(hits) == 1, (fid, [r['id'] for r in hits])
    return hits[0]


def test_the_special_foods_are_the_quest_and_one_of_a_kind_finds():
    assert SPECIAL == {'magic_dungeon_carrot', 'starnut_tart', 'tantalus_plum', 'golden_apple',
                       'ambrosia', 'peach_of_immortality'}


@pytest.mark.parametrize('fid', sorted(SPECIAL))
def test_each_special_food_has_a_decent_dish_of_its_tier(fid):
    rec = _special_dish(fid)
    # Its deepest part is of a tier where the food is found; a big dish of
    # four parts or more is a tier richer than that (big_dish, 2026-11-16).
    assert kitchen.base_tier(rec) in _found_tiers(fid), (fid, kitchen.base_tier(rec), _found_tiers(fid))
    assert kitchen.dish_tier(rec) == kitchen.base_tier(rec) + kitchen.big_dish_bonus(rec)
    # Decent: four parts or more (the size bonus), never the dish that makes it,
    # and every other part one a run turns up (at most one uncommon part).
    assert kitchen.dish_size(rec) >= 4, rec['id']
    assert kitchen.makes(rec) != fid
    import part_rules
    freq = part_rules.load_freq()
    rare = part_rules.rare_foods(FOOD, freq['rules']['rare_food_weight'])

    def role_of(p):
        if p in INGS:
            return INGS[p]['tier_role']
        return 'food' if p in FOOD else None
    assert not part_rules.PartRules(freq, role_of, rare).problems({rec['id']: rec}), rec['id']
    # It gives more than the food eaten as it is: a stat lesson, or a meal
    # worth well over the plain food's own SP.
    out = kitchen.dish_outcome(rec)
    assert out['stat'] or out['sp'] > int(FOOD[fid].get('sp_restore', 0) or 0), rec['id']


def test_holding_a_special_food_shows_its_dish_and_says_where_it_comes_from():
    import cook_menu
    from player import Player
    from items import make_item_by_id
    p = Player()
    carrot = make_item_by_id('food', 'magic_dungeon_carrot')
    p.inventory = [carrot]
    rec = _special_dish('magic_dungeon_carrot')
    rows = kitchen.menu_rows(p, p.inventory, kitchen.dish_tab(rec))
    row = next(r for r in rows if r['id'] == rec['id'])
    assert row['group'] == 'building' and row['have_count'] == 1
    assert cook_menu.part_source('magic_dungeon_carrot') == 'Find'
    assert cook_menu.part_source('starnut_tart') == 'Cook'
    # A ration alone still puts nothing under Building Toward.
    p.inventory = [make_item_by_id('food', 'bread_ration')]
    assert not [r for t in kitchen.MENU_TABS for r in kitchen.menu_rows(p, p.inventory, t)
                if r['group'] == 'building']


@pytest.mark.parametrize('fid', ['magic_dungeon_carrot', 'starnut_tart'])
def test_cooking_the_special_dish_uses_the_special_food_up(fid):
    """Cooked, it is gone: the unicorn's carrot and the Mooble's tart can no
    longer serve their meeting (the events themselves are unchanged)."""
    from items import make_item_by_id
    from food_system import load_ingredient_for
    g = _game()
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))
    rec = _special_dish(fid)
    p = g.player
    p.inventory = [i for i in p.inventory if kitchen.part_kind(getattr(i, 'id', '')) is None]
    for part in kitchen.parts(rec):
        it = make_item_by_id('food', part) if part in FOOD else load_ingredient_for(part)
        it.count = 1
        it.identified = True
        p.inventory.append(it)
    assert kitchen.can_cook(rec, kitchen.held_counts(p.inventory))
    g._cook_compound(rec)
    assert not any(getattr(i, 'id', '') == fid for i in p.inventory), fid
    assert any(rec['name'] in str(e[0]) for e in g.msg_log.entries[-8:])


def test_a_carried_dish_the_pack_cannot_take_is_set_down_at_the_heros_feet():
    """Ingredients weigh nothing (Brandon, 2026-11-16) and food does, so a
    dish cooked to carry can outweigh what went into it: a full pack sets
    the Starnut Tart down at the hero's feet, and says so."""
    from items import make_item_by_id
    from food_system import load_ingredient_for
    g = _game()
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))
    rec = kitchen.recipe('dish_starnut_tart')
    p = g.player
    for part in kitchen.parts(rec):
        it = make_item_by_id('food', part) if part in FOOD else load_ingredient_for(part)
        it.count = 1
        it.identified = True
        p.inventory.append(it)
    p.add_to_inventory = lambda item: False          # the pack is full
    g._cook_compound(rec)
    tarts = [i for i in g.ground_items if getattr(i, 'id', '') == 'starnut_tart']
    assert len(tarts) == 1 and (tarts[0].x, tarts[0].y) == (p.x, p.y)
    assert not any(getattr(i, 'id', '') == 'starnut_tart' for i in p.inventory)
    assert any('set it down at your feet' in str(e[0]) for e in g.msg_log.entries[-6:])
    assert not kitchen.take_set_down(p), 'the Game took it off the hero'


def test_the_pets_forage_and_the_songs_food_are_cooked_in_good_dishes():
    """Confirmed, not changed: the Mooble's starnuts and the Bococho's
    sunroots each go into two dishes or more besides their own; caviar and
    tater tots make the dish that plays Brandon's song."""
    for fid in ('starnut', 'sunroot'):
        multis = [r for r in kitchen.dishes_with(fid) if kitchen.dish_size(r) > 1]
        assert len(multis) >= 2, fid
    song = [r for r in kitchen.book() if kitchen.song_of(r)]
    assert song and set(kitchen.parts(song[0])) == {'caviar', 'tater_tots'}
