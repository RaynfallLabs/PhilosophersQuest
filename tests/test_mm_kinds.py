"""The MONSTERS AND MAGIC kinds (2026-11-19, slice M): thirty-two new kinds from
real lore, wired into every system, and their lore powers (src/lore_powers.py,
src/game_lore_powers.py). Seeded and deterministic.
"""
import json
import os
import random
import sys
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import pygame  # noqa: E402

pygame.init()

import lore_powers  # noqa: E402
import monster as monster_mod  # noqa: E402
from dungeon import FLOOR, WALL  # noqa: E402
from game_lore_powers import QA_KINDS, LorePowersMixin  # noqa: E402
from mm_kinds_data import NEW, PEOPLE  # noqa: E402


def _json(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _json('monsters.json')


def _m(kind, x=5, y=5):
    m = monster_mod.Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = True
    return m


class _Map:
    fixture_blocks = frozenset()
    fixture_opaque = frozenset()

    def __init__(self, rows):
        self.tiles = [[WALL if c == '#' else FLOOR for c in r] for r in rows]
        self.height, self.width = len(rows), len(rows[0])
        self.traps = {}
        self.explored = {(x, y) for y in range(self.height) for x in range(self.width)}

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[y][x] == FLOOR

    def is_opaque(self, x, y):
        return not self.is_walkable(x, y)


OPEN = ["#" * 30] + ["#" + "." * 28 + "#" for _ in range(20)] + ["#" * 30]
WALLED = ["##########",
          "#........#",
          "#........#",
          "####.#####",
          "#........#",
          "#........#",
          "##########"]


class _Hero:
    def __init__(self, x=5, y=5, hp=100):
        self.x, self.y = x, y
        self.hp = self.max_hp = hp
        self.status_effects = {}
        self.shield = None
        self.inventory = []
        self.CON = self.STR = self.DEX = 10

    def has_effect(self, e):
        return self.status_effects.get(e, 0) > 0

    def add_effect(self, e, n):
        self.status_effects[e] = max(self.status_effects.get(e, 0), n)

    def take_damage(self, n, typ='physical'):
        self.hp -= n
        return n

    def load_tier(self):
        return ''

    def get_sight_radius(self):
        return 5


# ---------------------------------------------------------------- the data

def test_the_new_kinds_are_in_the_game_at_their_lore_depth():
    assert len(NEW) == 32
    for k, d in NEW.items():
        m = MONS[k]
        tier = (m['peak_floor'] - 1) // 20 + 1
        assert m['harvest_tier'] == tier, k
        assert m['min_level'] <= m['peak_floor'], k
        assert m['peak_weight'] > 0 and m['family'] == d['family'], k
        assert len(m['lore'].split()) >= 50, k
        assert m['tags'], k
        assert m['pronoun'] in ('it', 'he', 'she'), k
        assert 'purse' in m['treasure'], k                         # gold_by_lore.py ran
    # The plan's cuts and moves.
    for gone in ('myling', 'amphisbaena'):
        assert gone not in MONS
    assert 21 <= MONS['centaur']['peak_floor'] <= 22
    assert MONS['reem']['footprint'] == [2, 2]


def test_the_new_kinds_are_wired_into_every_system():
    import dungeon
    import family_lore
    sizes = _json('monster_sizes.json')['sizes']
    hmap = _json('items', 'harvest_map.json')
    ings = _json('items', 'ingredient.json')
    for k in NEW:
        assert sizes[k] in ('tiny', 'small', 'medium', 'large', 'huge'), k
        assert family_lore.family_of(k) == MONS[k]['family'], k
        if k in PEOPLE:
            assert k in hmap['people'] and k not in hmap['monsters'], k
        else:
            assert hmap['monsters'][k] in ings, k
        assert k in dungeon._build_spawn_pool(MONS[k]['peak_floor']), k
        assert k in QA_KINDS, k
    assert set(QA_KINDS) == set(NEW)


def test_every_new_part_has_one_single_dish_and_two_with_partners():
    from mm_kitchen_data import INGREDIENTS, RECIPES
    recs = _json('items', 'recipes.json')
    for item in INGREDIENTS:
        iid = item['id']
        singles = [r for r in recs.values() if r['ingredients'] == [iid]]
        multis = [r for r in recs.values() if iid in r['ingredients'] and len(set(r['ingredients'])) > 1]
        assert len(singles) == 1 and len(multis) >= 2, iid
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', iid + '.png')), iid
    for rid in RECIPES:
        assert rid in recs


def test_the_waiting_fields_carry_the_other_slices_shapes():
    """The kinds carry the other slices' fields in their shapes
    (_mm_2026_11_19/B/PROPOSALS.json and AI1/FIELDS.md) and are sound
    monsters on their plain attacks. AI-1's fields at work:
    tests/test_mm_kinds_ai1.py; AI-3's (hold, aura, enraged_form, moves)
    still wait on its engine."""
    assert MONS['ponaturi']['light_shy'] is True and MONS['star_jelly']['light_shy'] is True
    gape = next(a for a in MONS['bakunawa']['attacks'] if a['name'] == 'Moon-Swallowing Jaws')
    assert gape['snuffs_light'] == 'dark'
    dt = MONS['mandrake']['death_throes']
    assert dt['delivery'] == 'voice' and 0 <= dt['share'] <= 0.15 and dt['radius'] in (1, 2)
    assert 8 <= MONS['waq_waq_tree']['alarm']['radius'] <= 14
    jaws = next(a for a in MONS['taniwha']['attacks'] if a['name'] == 'Gulping Jaws')
    assert jaws['hold']['kind'] == 'swallow' and jaws['hold']['max_turns'] <= 4
    for k in ('mapinguari', 'upas_tree', 'ghast'):
        assert MONS[k]['aura']['kind'] in ('fear', 'heat', 'cold', 'stench'), k
        assert 1 <= MONS[k]['aura']['radius'] <= 3, k
    form = MONS['nahual']['enraged_form']
    assert form['attacks'] and form['line'] and MONS['nahual']['enraged_pattern'] == 'aggressive'
    assert MONS['nuckelavee']['moves'] == []
    for k in ('asanbosam', 'ahuizotl', 'tsuchigumo'):
        assert MONS[k]['relurks'] is True, k
    for k, m in MONS.items():
        if k in NEW:
            assert m['attacks'], k


def test_the_upgrades_are_written_by_lore():
    drag = next(a for a in MONS['each_uisce']['attacks'] if a['name'] == 'Drown Drag')
    assert drag['effect'] == 'immobilized' and MONS['each_uisce']['pull_chance'] == 0.3
    assert MONS['green_hag']['pull_chance'] == 0.25
    touch = next(a for a in MONS['mummy']['attacks'] if a['name'] == 'Rotting Touch')
    assert touch['effect'] == 'heal_blocked'
    bite = next(a for a in MONS['komodo_brute']['attacks'] if a['name'] == 'Venomous Bite')
    assert bite['effect'] == 'bleeding'
    assert MONS['nosferatu']['summon_kind'] == 'giant_rat' and 'hunts alone' not in MONS['nosferatu']['lore']
    assert MONS['catoblepas']['opener']['wind_up']
    assert MONS['lindworm']['sheds_skin']['at'] == [0.66, 0.33]
    assert MONS['jiangshi']['talisman']['turns'] == 2
    crush = next(a for a in MONS['roc_adult']['attacks'] if a['name'] == 'Talon Crush')
    assert crush['carry_off']['chance'] == 0.2


def test_every_new_power_has_a_tell():
    import tells
    d = tells.data()
    for key in lore_powers._TELL_KEYS + ('carry_off', 'ranged_pull', 'steal_offering'):
        assert key in d['effects'] and key in d['order'], key
    for k in ('cu_sith', 'bulgasari', 'vetala', 'kappa', 'preta', 'mapinguari', 'myrmekes',
              'asanbosam', 'blue_men_of_the_minch', 'yacumama'):
        assert tells.abilities(_m(k)), k
    assert 'countdown_voice' in tells.abilities(_m('cu_sith'))
    assert 'carry_off' in tells.abilities(_m('roc_adult'))
    assert 'talisman' in tells.abilities(_m('jiangshi'))


# ------------------------------------------------------ the Cu-Sith's barks

def test_the_cu_sith_barks_three_times_and_the_third_is_its_attack():
    lore_powers.drain()
    d = _Map(OPEN)
    hero = _Hero(10, 10)
    m = _m('cu_sith', 14, 10)
    m._tracking = True                         # it has noticed him (senses.notice)
    got = [lore_powers.countdown_turn(m, hero, d) for _ in range(7)]
    # It holds its ground between the barks (the turns to get away), and
    # the third bark is its attack.
    assert got[:6] == [False] * 6 and got[6] is True
    assert m.__dict__['_opener_now']['name'] == 'Third Bark'
    lines = [t for t, *_ in lore_powers.drain()]
    assert len(lines) == 3 and 'third' in lines[-1].lower()
    # Then it hunts: no more barks or holding while it keeps him in sight.
    assert all(lore_powers.countdown_turn(m, hero, d) is None for _ in range(9))


def test_beside_the_hero_the_hound_bites_between_barks():
    lore_powers.drain()
    m = _m('cu_sith', 11, 10)
    m._tracking = True
    hero = _Hero(10, 10)
    got = [lore_powers.countdown_turn(m, hero, _Map(OPEN)) for _ in range(7)]
    assert got[:6] == [None] * 6 and got[6] is True


def test_out_of_its_sight_the_count_is_lost():
    lore_powers.drain()
    d = _Map(WALLED)
    m = _m('cu_sith', 2, 1)
    m._tracking = True
    hero = _Hero(4, 1)
    for _ in range(4):
        lore_powers.countdown_turn(m, hero, d)
    assert m.__dict__['_lp_barks'] == 2
    hero.x, hero.y = 2, 5                      # round the wall
    assert lore_powers.countdown_turn(m, hero, d) is None
    assert m.__dict__['_lp_barks'] == 0
    assert any('falls silent' in t for t, *_ in lore_powers.drain())


def test_wax_in_the_ears_stops_the_third_bark():
    import counters
    bark = NEW['cu_sith']['countdown_voice']['attack']
    hero = SimpleNamespace(ears_stopped=True, inventory=[SimpleNamespace(counters=['voice'])])
    assert counters.blocks_rider(hero, _m('cu_sith'), bark, 'feared') is not None


# ------------------------------------------------------ the Bulgasari eats iron

class _Blade:
    def __init__(self, material, enchant=2):
        self.material = material
        self.item_class = 'weapon'
        self.enchant_bonus = enchant
        self.name = self.unidentified_name = f"{material} sword"
        self.identified = True
        self.id_level = 5
        self.special_properties = {}
        self.slot = 'weapon'


def test_the_bulgasari_gnaws_an_iron_blade_and_mends():
    w = _Blade('steel')
    from status_effects import _can_rust
    assert _can_rust(w)
    m = _m('bulgasari')
    m.hp = m.max_hp // 2
    before_hp, before_ench = m.hp, int(getattr(w, 'enchant_bonus', 0) or 0)
    random.seed(3)
    old = lore_powers.spec(m, 'metal_eater')['wear_chance']
    try:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = 1.0
        lore_powers.after_struck(None, m, w, 3, 10)
    finally:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = old
    assert m.hp > before_hp
    assert w.enchant_bonus == before_ench - 1


def test_a_blade_it_cannot_eat_is_safe():
    m = _m('bulgasari')
    m.hp = m.max_hp // 2
    old = lore_powers.spec(m, 'metal_eater')['wear_chance']
    try:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = 1.0
        for mat in ('bronze', 'silver', 'oak'):
            blade = _Blade(mat)
            lore_powers.after_struck(None, m, blade, 3, 10)
            assert m.hp == m.max_hp // 2 and blade.enchant_bonus == 2, mat
    finally:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = old


# ---------------------------------------------------- the other lore powers

def test_fire_oil_on_the_blade_keeps_the_bulgasari_off_it():
    m = _m('bulgasari')
    m.hp = m.max_hp // 2
    w = _Blade('steel')
    w.coating = {'id': 'flask_of_fire_oil', 'name': 'Fire Oil', 'substance': 'fire', 'blows': 5}
    old = lore_powers.spec(m, 'metal_eater')['wear_chance']
    try:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = 1.0
        lore_powers.after_struck(None, m, w, 3, 10)
    finally:
        lore_powers._defs()['bulgasari']['metal_eater']['wear_chance'] = old
    assert w.enchant_bonus == 2 and m.hp == m.max_hp // 2


def test_a_long_chain_finds_the_mapinguari_soft_place():
    m = _m('mapinguari')
    assert not lore_powers.weak_spot(m, 9) and lore_powers.weak_spot(m, 10)
    assert not lore_powers.weak_spot(_m('owlbear'), 20)


def test_the_lindworm_sheds_two_skins_and_no_more():
    lore_powers.drain()
    m = _m('lindworm')
    m.status_effects.update(bleeding=5, armor_crack=3, paralyzed=2)
    m.take_damage(int(m.max_hp * 0.40))
    assert m.__dict__['_lp_skins'] == 1
    assert 'bleeding' not in m.status_effects and 'armor_crack' not in m.status_effects
    assert m.status_effects.get('paralyzed') == 2                 # a hold is not a wound
    m.take_damage(int(m.hp - m.max_hp * 0.30))
    assert m.__dict__['_lp_skins'] == 2
    m.take_damage(int(m.hp - m.max_hp * 0.10))
    assert m.__dict__['_lp_skins'] == 2


def test_the_kappa_spills_its_dish_when_stunned():
    m = _m('kappa')
    assert m.add_effect('stunned', 2) > 0
    assert m.status_effects.get('weakened', 0) >= 12


def test_likho_blinded_cannot_use_her_eye():
    m = _m('likho')
    gaze = next(a for a in m.attacks if a['name'] == 'Baleful Gaze')
    hero = _Hero()
    assert lore_powers.blow_refused(m, hero, gaze) is None
    m.status_effects['blinded'] = 3
    assert 'finds nothing' in lore_powers.blow_refused(m, hero, gaze)
    other = next(a for a in m.attacks if a['name'] == 'Gnarled Hands')
    assert lore_powers.blow_refused(m, hero, other) is None


def test_the_roc_carries_off_and_a_heavy_load_is_harder_to_lift():
    m = _m('roc_adult')
    crush = next(a for a in m.attacks if a['name'] == 'Talon Crush')
    random.seed(1)
    lifted = 0
    for _ in range(400):
        hero = _Hero(hp=500)
        lore_powers.after_blow(m, hero, crush, 20)
        lifted += '_lp_carry_off' in hero.__dict__
    heavy = 0
    random.seed(1)
    for _ in range(400):
        hero = _Hero(hp=500)
        hero.load_tier = lambda: 'heavy'
        lore_powers.after_blow(m, hero, crush, 20)
        heavy += '_lp_carry_off' in hero.__dict__
    assert 50 <= lifted <= 110 and heavy < lifted * 0.75


def test_the_yacumama_breath_draws_the_hero_in():
    m = _m('yacumama', 10, 5)
    breath = next(a for a in m.attacks if a.get('pulls'))
    hero = _Hero(5, 5)
    hero._pending_pull_toward = None
    assert 'drags you' in lore_powers.after_blow(m, hero, breath, 5)
    assert hero._pending_pull_toward == (10, 5)
    # The Galdr of Loosing (slice G's free_action): nothing drags him.
    hero._pending_pull_toward = None
    hero.add_effect('free_action', 10)
    assert lore_powers.after_blow(m, hero, breath, 5) == ''
    assert hero._pending_pull_toward is None


def test_a_light_shows_what_hangs_overhead():
    import unseen
    m = _m('asanbosam', 7, 5)
    m._aware = False
    hero = _Hero(5, 5)
    assert unseen.lurking(m, hero)
    import lights
    old = lights.light_bonus
    try:
        lights.light_bonus = lambda p, *a, **k: 2
        assert not unseen.lurking(m, hero)
    finally:
        lights.light_bonus = old


def test_a_calm_creature_holds_its_peace_until_struck():
    lore_powers.drain()
    m = _m('preta')
    m.__dict__['_lp_calm'] = True
    d = _Map(OPEN)
    assert lore_powers.turn(m, _Hero(), d, [m], set()) is False
    m.take_damage(5)
    assert not m.__dict__.get('_lp_calm')


def test_the_jiangshi_loses_a_hero_who_holds_his_breath_and_the_komodo_follows_blood():
    import senses
    d = _Map(OPEN)
    j = _m('jiangshi', 5, 5)
    hero = _Hero(9, 5)
    senses.begin_turn(moved=False, guilty=False, floor=4, rested=False)
    assert senses.lore_sense(j, hero, d) == 'breath'
    senses.begin_turn(moved=False, guilty=False, floor=4, rested=True)
    assert senses.lore_sense(j, hero, d) is None
    k = _m('komodo_brute', 3, 3)
    far = _Hero(20, 15)
    assert senses.lore_sense(k, far, d) is None
    far.status_effects['bleeding'] = 4
    assert senses.lore_sense(k, far, d) == 'blood_scent'
    senses.begin_turn(moved=True, guilty=False, floor=0, rested=False)


def test_the_preta_eats_plain_food_and_never_a_carried_dish():
    import items
    import theft
    bread = items.make_item_by_id('food', 'bread_ration')
    tart = items.make_item_by_id('food', 'starnut_tart')
    assert lore_powers.is_plain_food(bread) and not lore_powers.is_plain_food(tart)

    class _P:
        inventory = [tart, bread]

        def worn_items(self):
            return []

        def drop_stack(self, it, n):
            self.inventory.remove(it)
            return it

    game = SimpleNamespace(player=_P(), player_gold=0, _display_name=lambda it: it.name)
    m = _m('preta')
    msg = theft.steal(game, m, 'offering', rng=random.Random(2))
    assert 'gone' in msg and game.player.inventory == [tart]
    assert not theft.has_loot(m)                                  # eaten: nothing to give back


# ------------------------------------------------- the game's side (a stand-in game)

class _Game(LorePowersMixin):
    def __init__(self, monsters, ground=()):
        self.monsters = list(monsters)
        self.ground_items = list(ground)
        self.messages = []
        self.player = _Hero(5, 5)
        self.player.WIS = 10
        self.dungeon = _Map(OPEN)
        self.visible = {(x, y) for x in range(30) for y in range(22)}

    def add_message(self, text, kind='info'):
        self.messages.append(text)

    def _sees_monster(self, m):
        return True

    def _occupants(self, hero=True):
        return {(self.player.x, self.player.y)} if hero else set()

    def _refresh_fov(self):
        pass


def test_a_gift_of_food_quiets_the_kappa():
    import items
    m = _m('kappa', 6, 5)
    bread = items.make_item_by_id('food', 'bread_ration')
    bread.x, bread.y = 7, 5
    bread._offered = True                      # the hero set it down (main._finish_drop)
    g = _Game([m], [bread])
    g._lore_powers_before(m)
    assert m.__dict__.get('_lp_calm') and bread not in g.ground_items
    assert any('bows' in t for t in g.messages)


def test_gold_dropped_stops_a_gold_digging_ant():
    from items import GoldPile
    m = _m('myrmekes', 6, 5)
    g = _Game([m], [GoldPile(30, 7, 6)])
    g._lore_powers_before(m)
    assert not g.ground_items and m.__dict__['_lp_busy'] == 3
    assert lore_powers.turn(m, g.player, g.dungeon, g.monsters, set()) is False


def test_the_blue_men_wait_for_an_answer_then_attack():
    a, b = _m('blue_men_of_the_minch', 10, 5), _m('blue_men_of_the_minch', 11, 6)
    a._tracking = True                         # it has noticed him
    g = _Game([a, b])
    g._lore_powers_before(a)
    assert a.__dict__['_lp_parley'] == b.__dict__['_lp_parley'] == 'waiting'
    assert any('Press D' in t for t in g.messages)
    assert lore_powers.turn(a, g.player, g.dungeon, g.monsters, set()) is False
    for _ in range(10):
        g._lore_powers_before(a)
    assert a.__dict__['_lp_parley'] == 'angry'


def test_the_blue_men_ask_their_question_on_d():
    a = _m('blue_men_of_the_minch', 8, 5)
    a._tracking = True
    g = _Game([a])
    g._lore_powers_before(a)
    asked = {}

    class _Q:
        def start_quiz(self, **kw):
            asked.update(kw)

    g.quiz_engine = _Q()
    g.player.get_quiz_timer_modifier = lambda: 1.0
    g.player.get_quiz_extra_seconds = lambda s: 0
    g.player.get_quiz_timer = lambda s: 10
    g._advance_turn = lambda: None
    assert g._parley_offer()
    assert asked['subject'] == 'grammar' and asked['total_qs'] == 1
    asked['callback'](SimpleNamespace(success=True))
    assert a.__dict__['_lp_calm'] and a.__dict__['_lp_parley'] == 'calm'


def test_the_vetala_rises_from_the_nearest_corpse_twice_at_most():
    from items import Corpse
    m = _m('vetala', 5, 5)
    body = Corpse('Goblin', 'goblin', 8, 5)
    g = _Game([m], [body])
    m.alive = False
    g._lore_powers_killed(m)
    risen = [o for o in g.monsters if o is not m]
    assert len(risen) == 1 and (risen[0].x, risen[0].y) == (8, 5)
    assert risen[0].max_hp == int(m.max_hp * 0.4) and body not in g.ground_items
    assert risen[0].__dict__['_lp_hops'] == 1
    # The last hop: no more bodies taken after max_hops.
    r = risen[0]
    r.__dict__['_lp_hops'] = 2
    g.ground_items.append(Corpse('Goblin', 'goblin', 9, 6))
    r.alive = False
    g._lore_powers_killed(r)
    assert len(g.monsters) == 2


def test_a_page_read_holds_a_jiangshi():
    j = _m('jiangshi', 7, 5)
    g = _Game([j])
    g._lore_powers_scroll_read()
    assert j.status_effects.get('paralyzed', 0) >= 1
    assert any('talisman' in t for t in g.messages)


# The Roc's lift, set down in the turn of its blow on a tile the hero could
# walk to: on a real Game, tests/test_mm_audit_fixes.py (D1).


def test_an_old_save_monster_has_no_lore_state_and_is_none_the_worse():
    m = _m('cu_sith')
    for k in [k for k in m.__dict__ if k.startswith('_lp_')]:
        del m.__dict__[k]
    assert lore_powers.turn(m, _Hero(), _Map(OPEN), [m], set()) is None


def test_the_ablation_switch_turns_every_power_off():
    lore_powers.ENABLED = False
    try:
        m = _m('cu_sith', 7, 5)
        assert all(lore_powers.countdown_turn(m, _Hero(), _Map(OPEN)) is None for _ in range(9))
        assert not lore_powers.weak_spot(_m('mapinguari'), 20)
    finally:
        lore_powers.ENABLED = True
