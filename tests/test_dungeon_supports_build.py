"""The dungeon supports the build (winning build plan 3.5, Brandon 2026-11-13:
"GIVE THE PLAYER THE TOOLS TO DRIVE BUILD FLEXIBILITY ACROSS THE DUNGEON").

Stock that knows what's below (src/domain_counters.py), the smiths' and
armourers' new work (src/smithing.py: reforge, silvering and the cold-iron
inlay, lining, special order), the trade-in (src/game_traders.py), and
rededication at an altar (src/rededication.py, src/game_divine.py).

Logic tests on the real data and a real headless Game. Whether a stall's
counter, a reforge or a rededication FEELS worth its price in a run is
Brandon's play-test: Claude cannot drive Pygame.
"""
import copy
import os
import pickle
import random
import sys
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import combat  # noqa: E402
import domain_counters  # noqa: E402
import economy  # noqa: E402
import items  # noqa: E402
import rededication  # noqa: E402
import smithing  # noqa: E402
import traders  # noqa: E402
from items import ARMOR_SLOTS, instantiate_armor, instantiate_weapon, load_items  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_supports_build__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = [m for m in g.monsters if not getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _trader(g, kind='armourer', stock=None):
    from mystery_system import MerchantNPC, build_trader
    from game_states import STATE_PLAYER
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    g.state = STATE_PLAYER
    m = build_trader(kind, g.dungeon_level, random.Random(11))
    if stock is not None:
        m.stock = list(stock)
        m.prices = [economy.merchant_price(it, g.dungeon_level, m.markup) for it in m.stock]
        m.sold_out = not m.stock
    m.x, m.y = g.player.x + 1, g.player.y
    g.ground_items.append(m)
    g._open_shop()
    return m


def _service_row(g, m, sid):
    g._shop_tab = 2
    g._shop_selection = list(m.services).index(sid)


def _potion(pid):
    return copy.copy(next(p for p in load_items('potion') if p.id == pid))


def _known(it):
    it.id_level = 5
    return it


def _mon(kind):
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)[kind]
    return SimpleNamespace(**{k: v for k, v in d.items() if k.isidentifier()})


def _mult(w, mon):
    form, sub = combat.weapon_type_multiplier(w, mon)
    return form * sub


# ====================================================================== data

NEW = ('reforge', 'silvering', 'cold_iron_inlay', 'lining', 'special_order', 'trade_in')
SMITHS = ('armourer', 'dwarf_armourer', 'regin', 'tyr')
ARMOURERS = ('armourer', 'dwarf_armourer')


def test_every_new_service_is_named_priced_and_sold_by_the_right_people():
    d = traders.data()
    for sid in NEW:
        assert sid in economy.SERVICE_SHARE, sid
        s = d['services'][sid]
        assert s['name'] and s['desc'] and s['name'][0].isupper(), sid
    for kind, t in d['traders'].items():
        sv = set(t['services'])
        assert 'trade_in' in sv, kind                         # everyone
        assert ({'reforge', 'silvering', 'cold_iron_inlay'} <= sv) == (kind in SMITHS), kind
        assert ({'lining', 'special_order'} <= sv) == (kind in ARMOURERS), kind
        # Every smith is someone who sharpens today (the smiths of record).
        assert ('sharpen' in sv) == (kind in SMITHS), kind
    for k in ARMOURERS:
        assert d['traders'][k]['forms_of_best'] >= 3
        for key in ('order_placed', 'order_ready', 'order_refund'):
            assert d['traders'][k]['lines'][key]


def test_every_trader_and_friend_speaks_of_whats_below_in_his_own_words():
    d = traders.data()
    info = {'foes': 'the dead walk', 'take': 'a mace'}
    for kind, t in d['traders'].items():
        lines = [t['lines']['counter']] + ([t['friend']['counter']] if t.get('friend') else [])
        for tmpl in lines:
            assert '{foes}' in tmpl and '{take}' in tmpl, kind
            assert not tmpl.startswith('{'), kind          # never a lowercase opening
            said = domain_counters.counter_line(tmpl, info)
            assert 'the dead walk' in said and 'a mace' in said and '_' not in said, kind
    for fam, words in d['counters']['foes'].items():
        assert words and words == words.strip() and '_' not in words, fam


def test_the_counter_tables_name_real_things():
    c = traders.data()['counters']
    effects = {cat: {getattr(i, 'effect', None) for i in load_items(cat)} for cat in ('wand', 'potion')}
    spells = {getattr(i, 'spell_id', None) for i in load_items('spellbook')}
    mats = items.load_materials('weapons')
    for side in ('weak', 'guard'):
        for key, need in c[side].items():
            assert need['take'] and need['offers'], key
            for o in need['offers']:
                if o.get('class') in effects:
                    assert set(o['effects']) <= effects[o['class']], (key, o)
                if o.get('class') == 'spellbook':
                    assert set(o['spells']) <= spells, (key, o)
                if o.get('material'):
                    assert o['material'] in mats, (key, o)
                if o.get('lining'):
                    assert o['lining'] in smithing.LINING_ELEMENTS and o['slot'] in smithing.LINING_SLOTS
    import counters
    for key, g in c['guard'].items():
        assert g['foes'], key
        if g.get('delivery') or g.get('families') or g.get('tags'):
            # A named counter's technique (slice 5, counters.py): a gaze, a
            # voice, a fairy's glamour, answered by a piece, not a lining.
            assert counters.technique(key), key
        else:
            assert key in smithing.LINING_ELEMENTS, key
    for sub in smithing.INLAY_SUBSTANCES:
        ent = traders.data()['inlays'][sub]
        assert ent['prefix'] and ent['card'] and '{who}' in ent['done'] and '{name}' in ent['done']
    for el in smithing.LINING_ELEMENTS:
        assert traders.data()['linings'][el]['stuff']


# =========================================================== what's below

def _fake_floors(monkeypatch, defn):
    """Every floor's spawn pool is one made-up kind."""
    domain_counters.needs.cache_clear()
    monkeypatch.setattr(domain_counters, '_floor_kinds', lambda lvl: (('test_kind', 1.0, defn),))
    yield_ = None
    return yield_


@pytest.fixture
def bones(monkeypatch):
    """A floor where only a made-up dead thing walks: weak to blunt, resists
    a point, breathes fire. Read from the data handed in, at run time."""
    defn = {'name': 'test bones', 'weaknesses': ['blunt'], 'resistances': ['pierce'],
            'tags': [], 'family': 'restless_dead',
            'attacks': [{'name': 'Breath', 'damage': '1d4', 'type': 'fire'}]}
    _fake_floors(monkeypatch, defn)
    yield defn
    domain_counters.needs.cache_clear()


def test_the_stall_reads_what_walks_below_and_racks_a_counter_for_it(bones):
    from mystery_system import build_trader
    items.bind_unique_registry(set())
    ranked = domain_counters.needs(12)
    assert ranked[0][:2] == ('weak', 'blunt') and ranked[0][2] == 1.0
    assert ('guard', 'fire') in [r[:2] for r in ranked]
    m = build_trader('armourer', 12, random.Random(1))
    assert m.counter['key'] == 'blunt' and m.counter['foes'] == 'the dead walk'
    marked = [w for w in m.stock if getattr(w, '_counter', None)]
    blunt = [w for w in marked if getattr(w, 'item_class', '') == 'weapon']
    assert blunt and 'blunt' in blunt[0].damage_types
    assert m.counter['take'].startswith(('a ', 'an '))         # "Take a mace."
    lined = [w for w in marked if getattr(w, 'lining', None) == 'fire']
    assert lined and lined[0].slot == 'cloak'                  # where fire breathes
    said = domain_counters.counter_line(m.lines['counter'], m.counter)
    assert said.startswith("Where you're going, the dead walk. Take a")


def test_the_counter_line_is_said_once_when_the_stall_opens(bones):
    g = _game()
    m = _trader(g, 'armourer')
    first = [t for t in _texts(g, 12) if 'the dead walk' in t]
    assert first and first[0].startswith('Brannoc: "Where you\'re going, the dead walk.')
    g.state = 'player'
    g._open_shop()
    assert sum('the dead walk' in t for t in _texts(g, 12)) == 1
    # The ware set out for it says so on the Buy tab.
    i = next(i for i, w in enumerate(m.stock) if getattr(w, '_counter', None))
    g._shop_tab, g._shop_selection = 0, i
    details = [d[0] for d in g._trader_menu()['entries'][i]['details'] if isinstance(d, tuple)]
    assert any('set this out for what is below: the dead walk' in t for t in details)


@pytest.mark.parametrize('kind', sorted(traders.data()['traders']))
def test_every_stall_carries_a_counter_for_its_floors(kind):
    """At its first and last floors, every kind of trader sets out at least
    one counter his line can supply, and a marked gear counter really meets
    a weakness among the kinds that walk there (the real multiplier)."""
    from mystery_system import build_trader
    spans = traders.kind_floors(kind)
    assert spans, kind
    for lo, hi in spans:
        for lvl in sorted({lo, hi}):
            items.bind_unique_registry(set())
            m = build_trader(kind, lvl, random.Random(lvl))
            assert m.counter, (kind, lvl)
            line = domain_counters.line_of(traders.kind_def(kind))
            for w in m.stock:
                if getattr(w, '_counter', None):
                    assert getattr(w, 'item_class', '') in line
            weapon = next((w for w in m.stock if getattr(w, '_counter', None)
                           and getattr(w, 'item_class', '') == 'weapon'), None)
            if weapon is not None:
                kinds = [d for f in range(lvl, min(100, lvl + 4) + 1)
                         for _k, _w, d in domain_counters._floor_kinds(f)]
                mons = [SimpleNamespace(**{k: v for k, v in d.items() if k.isidentifier()})
                        for d in kinds]
                assert any(_mult(weapon, mo) > 1.0 for mo in mons), (kind, lvl, weapon.id)


def test_a_wand_potion_or_book_counter_is_never_marked():
    """Marking an unidentified wand as "for the dead" would name it."""
    from mystery_system import build_trader
    for kind, lvl in (('generalist', 25), ('apothecary', 20), ('bookseller', 25),
                      ('ghost_bookseller', 70), ('abyssal', 85)):
        items.bind_unique_registry(set())
        m = build_trader(kind, lvl, random.Random(3))
        for w in m.stock:
            if getattr(w, 'item_class', '') in ('wand', 'potion', 'scroll', 'spellbook'):
                assert not getattr(w, '_counter', None), (kind, w.id)


def test_an_armourer_racks_his_best_metal_in_several_forms():
    from mystery_system import build_trader
    mats = items.load_materials('weapons')
    for kind, lvl in (('armourer', 12), ('armourer', 30), ('dwarf_armourer', 50),
                      ('dwarf_armourer', 70)):
        items.bind_unique_registry(set())
        m = build_trader(kind, lvl, random.Random(lvl))
        melee = [w for w in m.stock if getattr(w, 'item_class', '') == 'weapon'
                 and not getattr(w, 'requires_ammo', None) and w.material in mats
                 and smithing.template_of(w)
                 and all(smithing.melee_templates(mats[w.material], f)
                         for f in ('slash', 'pierce', 'blunt'))]
        best = max(melee, key=lambda w: (items.material_tier(mats[w.material]),
                                         float(mats[w.material].get('weapon_base', 0)),
                                         w.material)).material
        forms = {f for w in melee if w.material == best for f in w.damage_types
                 if f in ('slash', 'pierce', 'blunt')}
        assert len(forms) >= 3, (kind, lvl, best, forms)


# ================================================================ reforge

def _sword(**kw):
    w = instantiate_weapon('longsword', 'iron')
    w.enchant_bonus = kw.get('plus', 2)
    w.buc = kw.get('buc', 'blessed')
    w.buc_known = True
    w._smith_bonus = 1
    w.wear_loss = 1
    w.id_level = 5
    w._bought_for = 300
    return w


def test_reforge_keeps_material_plus_blessing_and_work_and_changes_the_forms():
    w = _sword()
    assert smithing.inlay(w, 'silver')
    smithing.reforge(w, 'mace')
    fresh = instantiate_weapon('mace', 'iron')
    assert w.id == 'iron_mace' and w.material == 'iron'
    assert w.enchant_bonus == 2 and w.buc == 'blessed' and w.buc_known
    assert w._smith_bonus == 1 and w.wear_loss == 1 and w._bought_for == 300 and w.id_level == 5
    assert 'blunt' in w.damage_types and 'slash' not in w.damage_types
    assert 'silver' in w.damage_types and w.inlay == 'silver'
    assert w.name == 'Silvered Iron Mace'
    assert w.base_damage == fresh.base_damage and w.weight == fresh.weight
    assert w.two_handed == fresh.two_handed and w.class_mechanic == fresh.class_mechanic
    # And a one-hander into a two-hander takes the template's hands.
    smithing.reforge(w, 'maul')
    assert w.two_handed and w.id == 'iron_maul' and w.enchant_bonus == 2


def test_reforge_never_touches_a_named_blade_a_bow_or_a_two_hander_under_a_shield():
    named = next(i for i in load_items('weapon') if getattr(i, 'is_unique', False))
    assert smithing.reforge_targets(named) == []
    bow = instantiate_weapon('longbow', 'yew')
    assert smithing.reforge_targets(bow) == []
    w = _sword()
    both = smithing.reforge_targets(w)
    one = smithing.reforge_targets(w, shield_worn=True)
    assert 'maul' in both and 'maul' not in one and 'mace' in one
    assert 'longsword' not in both


def test_the_smith_reforges_the_weapon_in_your_hand_through_the_shop():
    g = _game()
    g.player.weapon = w = _sword()
    g.player.shield = None
    m = _trader(g, 'armourer', stock=[])
    price = g._service_price('reforge')
    g.player_gold = price + 50
    _service_row(g, m, 'reforge')
    _press(g, pygame.K_RETURN)
    picks = g._shop_pick[1]
    i = next(i for i, p in enumerate(picks) if smithing.template_of(p) == 'mace')
    g._shop_selection = i
    _press(g, pygame.K_RETURN)
    assert g.player.weapon is w and w.id == 'iron_mace' and w.enchant_bonus == 2
    assert g.player_gold == 50
    assert any('beats it into' in t for t in _texts(g))


# ================================================================ inlay

def test_a_silvered_weapon_meets_silvers_banes_through_the_real_multiplier():
    wolf = _mon('werewolf')
    w = instantiate_weapon('longsword', 'steel')
    before = _mult(w, wolf)
    assert smithing.inlay(w, 'silver')
    after = _mult(w, wolf)
    # Since the lore pass (slice 2) a werewolf also shrugs at a plain
    # blade's form (x0.5), so the whole blow is x0.5 x2; the SILVER is the
    # substance step, and it is the full weak step.
    _form, _sub = combat.weapon_type_multiplier(w, wolf)
    assert after > before and _sub >= combat.WEAK_TO
    # The affinity line names the silver, not "a cutting blow".
    assert combat.affinity_word(w, wolf, combat._affinity.WEAK) == 'silver'
    # Cold iron meets the Fair Folk the same way.
    fey = next(_mon(k) for k in ('changeling', 'puca', 'leprechaun'))
    c = instantiate_weapon('mace', 'steel')
    plain = _mult(c, fey)
    assert smithing.inlay(c, 'cold_iron') and _mult(c, fey) > plain


def test_one_inlay_to_a_weapon_and_its_name_shows_it():
    w = instantiate_weapon('longsword', 'iron')
    assert smithing.inlay(w, 'silver')
    assert w.name == 'Silvered Iron Longsword' and w.unidentified_name.startswith('Silvered ')
    assert not smithing.inlay(w, 'cold_iron') and not smithing.inlay(w, 'silver')
    assert w.damage_types.count('silver') == 1
    silver = instantiate_weapon('dagger', 'silver')
    assert not smithing.can_inlay(silver, 'silver')           # it is silver already
    assert smithing.work_lines(w) and 'Silvered' in smithing.work_lines(w)[0]


def test_the_shop_silvers_and_the_row_says_why_when_it_cannot():
    g = _game()
    g.player.weapon = w = instantiate_weapon('longsword', 'iron')
    w.id_level = 5                      # a smith works a blade the hero can name
    m = _trader(g, 'armourer', stock=[])
    g.player_gold = 3000
    _service_row(g, m, 'silvering')
    _press(g, pygame.K_RETURN)
    assert w.inlay == 'silver'
    assert g.player_gold == 3000 - g._service_price('silvering')
    entry = next(e for e in g._trader_menu()['entries'] if e['name'] == 'Inlay Cold Iron')
    whys = [d[0] for d in entry['details'] if isinstance(d, tuple)]
    assert any('one inlay to a weapon' in t for t in whys)


# ================================================================ lining

def _wear_cloak(p, element=None):
    c = instantiate_armor('cloak', 'linen')
    p.armor_slots[ARMOR_SLOTS.index('cloak')] = c
    if element:
        assert smithing.line(c, element)
    return c


def test_a_lined_cloak_takes_three_quarters_of_its_element():
    from player import Player
    p = Player()
    base_fire, base_cold = p.get_armor_resistance('fire'), p.get_armor_resistance('cold')
    c = _wear_cloak(p, 'fire')
    assert p.get_armor_resistance('fire') == pytest.approx(base_fire * 0.75)
    assert p.get_armor_resistance('cold') == pytest.approx(base_cold)
    assert c.damage_resistances == {}                          # its own field, never this one
    hp = p.hp = p.max_hp = 1000
    lined = p.take_damage(100, 'fire')
    p.hp = hp
    p.armor_slots[ARMOR_SLOTS.index('cloak')] = None
    plain = p.take_damage(100, 'fire')
    assert lined == pytest.approx(plain * 0.75, abs=1)


def test_one_lining_to_a_piece_and_only_a_cloak_or_shirt():
    c = instantiate_armor('cloak', 'linen')
    assert smithing.line(c, 'cold') and not smithing.line(c, 'fire')
    assert c.lining == 'cold'
    helm = instantiate_armor('leather_cap', 'leather')
    assert not smithing.line(helm, 'fire')
    shirt = instantiate_armor('padded_shirt', 'linen')
    assert smithing.line(shirt, 'poison')
    assert any('poison' in t for t in smithing.work_lines(shirt))


def test_the_armourer_lines_your_cloak_and_a_lined_cloak_on_his_shelf_costs_the_work():
    g = _game()
    c = _wear_cloak(g.player)
    m = _trader(g, 'armourer', stock=[])
    g.player_gold = 3000
    _service_row(g, m, 'lining')
    _press(g, pygame.K_RETURN)
    assert [e for _p, e in g._shop_pick[1]] == list(smithing.LINING_ELEMENTS)
    g._shop_selection = 1                                     # cold
    _press(g, pygame.K_RETURN)
    assert c.lining == 'cold'
    assert g.player_gold == 3000 - g._service_price('lining')
    shelf = instantiate_armor('cloak', 'linen')
    plain = economy.stock_price(shelf, 20)
    smithing.line(shelf, 'fire')
    assert economy.stock_price(shelf, 20) == plain + economy.service_price('lining', 20)


# ================================================================ trade-in

def _spare(g):
    s = _known(instantiate_weapon('longsword', 'steel'))
    g.player.known_item_ids.add(s.id)
    g.player.inventory = [s]
    return s


def test_trade_in_pays_half_his_price_after_a_purchase():
    g = _game()
    full = _known(_potion('potion_of_full_healing'))
    m = _trader(g, 'armourer', stock=[full])
    m.purse = 10 ** 6
    s = _spare(g)
    g.player_gold = 3000
    plain, _ = g._trader_offer(s)
    his = economy.merchant_price(s, g.dungeon_level, m.markup)
    assert plain <= 0.26 * his
    g._shop_tab, g._shop_selection = 0, 0
    _press(g, pygame.K_RETURN)                               # he sells the hero a draught
    spent = m.visit['spent']
    assert spent > 0
    gold = g.player_gold
    g._shop_tab, g._shop_selection = 1, g.player.inventory.index(s)
    _press(g, pygame.K_RETURN)
    got = g.player_gold - gold
    half = economy.sell_offer(s, g.dungeon_level, known=True, identified=True,
                              markup=m.markup, purse=10 ** 6, trade_in=True)
    assert got == min(half, plain + spent)
    assert 0.45 * his <= half <= 0.55 * his
    assert any('as a trade-in' in t for t in _texts(g))


def test_a_sale_before_the_purchase_is_topped_up_when_he_buys():
    g = _game()
    full = _known(_potion('potion_of_full_healing'))
    m = _trader(g, 'armourer', stock=[full])
    m.purse = 10 ** 6
    s = _spare(g)
    g.player_gold = 3000
    plain, _ = g._trader_offer(s)
    half = economy.sell_offer(s, g.dungeon_level, known=True, identified=True,
                              markup=m.markup, purse=10 ** 6, trade_in=True)
    g._shop_tab, g._shop_selection = 1, 0
    start = g.player_gold
    _press(g, pygame.K_RETURN)                               # sold first: a fifth, the rest owed
    assert g.player_gold - start == plain
    price = g._trader_price(0)
    g._shop_tab, g._shop_selection = 0, 0
    _press(g, pygame.K_RETURN)                               # now he buys: the trade-in is paid
    assert g.player_gold - start == plain - price + min(half - plain, price)
    assert any('as a trade-in' in t for t in _texts(g))


def test_trade_in_never_exceeds_what_was_spent_ends_with_the_visit_and_keeps_the_purse():
    g = _game()
    cheap = _known(_potion('potion_of_healing'))
    m = _trader(g, 'armourer', stock=[cheap])
    m.purse = 10 ** 6
    s = _spare(g)
    g.player_gold = 3000
    plain, _ = g._trader_offer(s)
    _press(g, pygame.K_RETURN)
    spent = m.visit['spent']
    assert g._trade_in_extra(s, plain) == min(g._trade_in_gap(s, plain), spent)
    g._traders_leaving(g.dungeon_level)                      # he leaves the floor
    assert m.visit is None and g._trade_in_extra(s, plain) == 0
    # A purse that is short holds a trade-in to what is in it.
    m.purse = plain
    g._trader_visit(m)['spent'] = 10 ** 5
    assert plain + g._trade_in_extra(s, plain) <= m.purse


# ============================================================ special order

def _order(g, floors):
    """At the armourer's stall on the hero's floor, with his stalls on
    ``floors``: order the first metal's first shape. Returns (merchant, gold
    before, price)."""
    plan = g._trader_plan()
    plan['floors'] = {f: 'armourer' for f in floors}
    plan['orders'] = []
    m = _trader(g, 'armourer', stock=[])
    g.player_gold = 3000
    _service_row(g, m, 'special_order')
    _press(g, pygame.K_RETURN)                               # the metals
    assert g._shop_pick[0] == 'special_order'
    _press(g, pygame.K_RETURN)                               # the shapes
    assert g._shop_pick[0] == 'special_order:pick'
    piece = g._shop_pick[1][0]
    price = g._order_price(piece)
    _press(g, pygame.K_RETURN)
    return m, piece, price


def test_a_special_order_is_paid_now_and_collected_at_his_next_stall():
    g = _game()
    here = g.dungeon_level
    m, piece, price = _order(g, [here, here + 12])
    plan = g._trader_plan()
    assert g.player_gold == 3000 - price
    assert len(plan['orders']) == 1 and plan['orders'][0]['collect'] == here + 12
    assert any(f"floor {here + 12}" in t for t in _texts(g))
    # The detail pane said where and when, too.
    g._shop_pick = None
    entry = next(e for e in g._trader_menu()['entries'] if e['name'] == 'Special Order')
    lines = [d[0] for d in entry['details'] if isinstance(d, tuple)]
    assert any(f'waits at his stall on floor {here + 12}' in t for t in lines)
    # His next stall: the order is handed over when the shop opens.
    g.state = 'player'
    g._traders_leaving(here)
    assert plan['orders']                                    # a stall below: nothing paid back
    g.dungeon_level = here + 12
    _trader(g, 'armourer', stock=[])
    got = [i for i in g.player.inventory if getattr(i, 'id', None) == piece.id]
    assert got and got[0].buc == 'uncursed' and got[0].buc_known and got[0].id_level == 5
    assert got[0]._bought_for > 0 and not plan['orders']
    assert any('Made as you asked' in t for t in _texts(g))


def test_a_special_order_is_paid_back_when_there_is_no_stall_below():
    g = _game()
    here = g.dungeon_level
    m, piece, price = _order(g, [here, here + 12])
    plan = g._trader_plan()
    del plan['floors'][here + 12]                            # his stall below is gone
    before = g.player_gold
    g._traders_leaving(here)
    assert g.player_gold == before + price and not plan['orders']
    assert any('Have your coin back' in t for t in _texts(g))


def test_no_order_at_his_last_stall_and_the_row_says_so():
    g = _game()
    plan = g._trader_plan()
    plan['floors'] = {g.dungeon_level: 'armourer'}
    _trader(g, 'armourer', stock=[])
    assert g._service_targets('special_order') == []
    g._shop_tab = 2
    entry = next(e for e in g._trader_menu()['entries'] if e['name'] == 'Special Order')
    lines = [d[0] for d in entry['details'] if isinstance(d, tuple)]
    assert any('last stall' in t for t in lines)


def test_leaving_a_floor_closes_the_visit():
    g = _game()
    seen = []
    g._traders_leaving = lambda lvl: seen.append(lvl)
    here = g.dungeon_level
    g._change_level(here + 1, enter_from_top=True)
    assert seen == [here]


# ============================================================ rededication

def _hero():
    from player import Player
    p = Player()
    p.stats_at_start = {s: 10 for s in rededication.STATS}
    return p


def test_the_chain_earns_one_point_at_three_and_two_at_five():
    assert [rededication.points_for_chain(c) for c in range(7)] == [0, 0, 0, 1, 1, 2, 2]


def test_never_below_the_start_never_past_what_food_could_teach():
    p = _hero()
    p.deepest_floor_reached = 20                             # food's cap: 3 + 5 = 8
    assert rededication.give_room(p, 'STR') == 0             # nothing above the start
    p.apply_stat_bonus('STR', 3)
    p.cooking_stat_gained['STR'] = 3
    assert rededication.give_room(p, 'STR') == 3
    assert rededication.points_to_move(p, 'STR', 'DEX', 5) == 2
    p.cooking_stat_gained['DEX'] = 7                         # one point of room left
    assert rededication.points_to_move(p, 'STR', 'DEX', 5) == 1
    assert rededication.move(p, 'STR', 'DEX', 1) == 1
    assert p.STR == 12 and p.DEX == 11 and p.rededicated == {'STR': -1, 'DEX': 1}
    assert rededication.take_room(p, 'DEX') == 0
    # Two more out of Strength: never below where it began.
    rededication.move(p, 'STR', 'CON', rededication.points_to_move(p, 'STR', 'CON', 5))
    assert p.STR == 10 and rededication.give_room(p, 'STR') == 0
    # A gift given back frees its own room again.
    rededication.move(p, 'DEX', 'STR', 1)
    assert p.rededicated.get('DEX', 0) == 0 and rededication.take_room(p, 'DEX') == 1


def test_wisdom_keeps_its_half_rate():
    p = _hero()
    p.deepest_floor_reached = 40                             # food's cap 13; Wisdom's 6
    p.apply_stat_bonus('CON', 10)
    p.cooking_stat_gained['CON'] = 10
    assert rededication.take_room(p, 'WIS') == p.cooking_stat_softcap('WIS') == 6
    for _ in range(5):
        rededication.move(p, 'CON', 'WIS', rededication.points_to_move(p, 'CON', 'WIS', 5))
    assert p.WIS == 16 and rededication.take_room(p, 'WIS') == 0
    p.cooking_stat_gained['WIS'] = 0
    assert rededication.points_to_move(p, 'CON', 'WIS', 5) == 0   # the altar's six used it


def test_what_is_lent_is_not_the_heros_to_give():
    p = _hero()
    p.STR += 3
    p._worn_stat_ledger = {'STR': 3}                         # a ring of strength
    assert rededication.own_value(p, 'STR') == 10 and rededication.give_room(p, 'STR') == 0
    p._gawain_surge = 2
    p.STR += 2
    assert rededication.give_room(p, 'STR') == 0
    p.CON += 1
    p.active_carry_bonuses = {'charmander_stuffie': ('CON', 1)}   # a keepsake carried
    assert rededication.give_room(p, 'CON') == 0


def test_an_old_hero_without_the_new_fields_reads_his_start_from_the_build():
    from player import Player
    p = Player()
    for k in ('stats_at_start', 'rededicated', 'rededicated_altars'):
        p.__dict__.pop(k, None)
    p.STR = 18
    assert rededication.give_room(p, 'STR', {'STR': 18}) == 0
    assert rededication.give_room(p, 'STR') == 8             # no build: it began at 10
    assert rededication.taught(p, 'STR') == 0


@pytest.fixture
def altar_game(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones as _bones
    import layout
    from main import Game
    from game_states import STATE_PLAYER
    from dungeon import ALTAR
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(_bones, 'save_bones', lambda *a, **k: None)
    size = (1600, 900)
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    random.seed(3)
    g = Game(screen, player_name='__test_rededication__')
    g.on_resize(*size)
    g._resize_grace = 0
    g.monsters = []
    g.state = STATE_PLAYER
    d = g.dungeon
    g.player.x, g.player.y = next((x, y) for y in range(d.height)
                                  for x in range(d.width) if d.tiles[y][x] == ALTAR)
    g.player_gold = 1000
    g.player.prayer_cooldown = 60
    g.player.apply_stat_bonus('STR', 3)
    g.player.cooking_stat_gained['STR'] = 3
    return g


def _answer_chain(g, n):
    from quiz_engine import QuizState
    qe = g.quiz_engine
    for i in range(6):
        if qe.state != QuizState.ASKING:
            break
        q = qe.current_question
        right = str(q['answer'])
        wrong = next(c for c in q['choices'] if str(c).strip() != right.strip())
        qe.answer(right if i < n else wrong)
        for _ in range(40):
            if qe.state != QuizState.RESULT:
                break
            if getattr(qe, '_result_hold', False):
                qe._result_hold_until = 0.0
                qe.release_result_hold()
            g.update(0.25)


def _rededicate(g, give_key, take_key):
    _press(g, pygame.K_BACKSLASH, chr(92))
    _press(g, pygame.K_2)
    assert g.state == 'ask'
    _press(g, give_key)
    assert g.state == 'ask'
    _press(g, take_key)


def test_rededication_moves_exactly_the_earned_points_once_per_altar(altar_game):
    g = altar_game
    p = g.player
    s0, d0 = p.STR, p.DEX
    assert p.stats_at_start['STR'] == rededication.own_value(p, 'STR') - 3
    _press(g, pygame.K_BACKSLASH, chr(92))
    row = g._prayer_choices()[1]
    assert row['id'] == 'rededicate' and row['enabled']
    _press(g, pygame.K_ESCAPE)
    _rededicate(g, pygame.K_s, pygame.K_d)
    assert g.state == 'quiz' and g.player_gold == 1000 - economy.altar_offering(1)
    _answer_chain(g, 5)
    assert (p.STR, p.DEX) == (s0 - 2, d0 + 2) and p.rededicated == {'STR': -2, 'DEX': 2}
    assert p.prayer_cooldown == 60 - 1                       # the altar never sets it
    # Once per altar: the row is shut, and nothing is taken for it.
    _press(g, pygame.K_BACKSLASH, chr(92))
    row = g._prayer_choices()[1]
    assert not row['enabled'] and 'heard your rededication' in row['asks']
    gold = g.player_gold
    _press(g, pygame.K_2)
    assert g.player_gold == gold and g.state == 'prayer_menu'


def test_a_chain_of_three_moves_one_and_a_short_chain_keeps_the_offering(altar_game):
    g = altar_game
    p = g.player
    s0, c0 = p.STR, p.CON
    _rededicate(g, pygame.K_s, pygame.K_c)
    _answer_chain(g, 2)
    assert (p.STR, p.CON) == (s0, c0)                        # nothing moved
    assert g.player_gold == 1000 - economy.altar_offering(1)  # the offering is the altar's
    assert any('Your gifts stay as they were' in t for t in _texts(g))
    # A fresh altar elsewhere hears it again (once per altar, not per run).
    g.player.rededicated_altars = set()
    g.state = 'player'
    hp = g.player.max_hp
    _rededicate(g, pygame.K_s, pygame.K_c)
    _answer_chain(g, 3)
    assert (p.STR, p.CON) == (s0 - 1, c0 + 1) and g.player.max_hp == hp + p.HP_PER_CON


def test_backing_out_costs_nothing_and_god_refuses_at_karma_minus_five(altar_game):
    g = altar_game
    _press(g, pygame.K_BACKSLASH, chr(92))
    _press(g, pygame.K_2)
    _press(g, pygame.K_ESCAPE)
    assert g.state == 'player' and g.player_gold == 1000
    assert not g.player.__dict__.get('rededicated_altars')
    g.karma = -5
    _press(g, pygame.K_BACKSLASH, chr(92))
    row = g._prayer_choices()[1]
    assert row['id'] == 'rededicate' and not row['enabled']
    _press(g, pygame.K_2)
    assert g.player_gold == 1000


# ================================================================== saves

def test_orders_linings_inlays_and_rededications_survive_a_save():
    from player import Player
    w = instantiate_weapon('longsword', 'iron')
    smithing.inlay(w, 'cold_iron')
    c = instantiate_armor('cloak', 'linen')
    smithing.line(c, 'lightning')
    p = Player()
    p.rededicated = {'STR': -1, 'DEX': 1}
    p.rededicated_altars = {(3, 4, 5)}
    p.stats_at_start = {s: 10 for s in rededication.STATS}
    plan = traders.roll_plan(7)
    plan['orders'].append({'kind': 'armourer', 'collect': 30, 'placed': 15, 'paid': 900})
    w2, c2, p2, plan2 = pickle.loads(pickle.dumps((w, c, p, plan)))
    assert w2.inlay == 'cold_iron' and 'cold_iron' in w2.damage_types
    assert w2.name.startswith('Iron-Inlaid ')
    assert c2.lining == 'lightning'
    assert p2.rededicated == {'STR': -1, 'DEX': 1} and (3, 4, 5) in p2.rededicated_altars
    assert plan2['orders'][0]['collect'] == 30
    # An old plan and an old merchant: the new keys and fields default.
    old = traders.ensure_plan({'seed': 1, 'floors': {}})
    assert old['orders'] == []
    from mystery_system import MerchantNPC
    m = MerchantNPC.__new__(MerchantNPC)
    assert m.counter is None and m.visit is None
    assert smithing.inlay_of(instantiate_weapon('mace', 'iron')) is None
    assert smithing.lining_of(instantiate_armor('cloak', 'linen')) is None


# ============================================================== wiring

def test_the_kit_and_shop_cards_show_the_smiths_work_identified_or_not():
    g = _game()
    w = instantiate_weapon('longsword', 'iron')
    smithing.inlay(w, 'silver')
    w.id_level = 0                                          # not identified
    c = _wear_cloak(g.player, 'fire')
    g.player.inventory.append(w)
    for it, word in ((w, 'Silvered'), (c, "salamander's wool")):
        for lines in (g._menu_item_detail_lines(it),
                      g._kit_detail_lines_for_item('weapons', 'pack', it)):
            assert any(word in str(ln[0]) for ln in lines if isinstance(ln, tuple)), word


def test_the_qa_sampler_brings_brannoc_to_try_it_all():
    from mystery_system import MerchantNPC
    g = _game()
    g.player.qa_tools = True
    g._qa_treasure_sampler()
    smith = [i for i in g.ground_items if isinstance(i, MerchantNPC) and i.kind == 'armourer']
    assert len(smith) == 1 and 'reforge' in smith[0].services


def test_a_smith_will_not_work_a_blade_the_hero_cannot_name():
    """Bug bash 2026-11-13 (the smith's tab): his refusals named an
    unidentified weapon's metal ("It is that metal already") and make ("a
    named blade") for free. Now an unknown blade is simply refused, and the
    line names nothing about it."""
    g = _game()
    g.player.weapon = w = instantiate_weapon('longsword', 'silver')
    w.id_level = 0
    m = _trader(g, 'armourer', stock=[])
    g._shop_merchant = m
    for sid in ('reforge', 'silvering', 'cold_iron_inlay'):
        assert g._service_targets(sid) == []
        why = g._service_why(sid)
        assert "can't name" in why
        assert 'silver' not in why.lower() and 'metal' not in why.lower() and 'named blade' not in why
    w.id_level = 5
    assert g._service_targets('cold_iron_inlay')
