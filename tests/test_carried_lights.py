"""Carried lights in the off hand and the Light spell that lasts (Brandon,
2026-11-19): "ranged monsters were particularly vicious ... their range is
often outside my perception. ... make a torch, lantern, etc item that can be
used in left hand, and increases the range of vision. Also, rework the light
spell to not use a spot but last X turns (based on INT?)".

The rules are src/lights.py (pure), the Game side src/game_lights.py, the
numbers data/lights.json and data/items/light.json. Data tests, pure-function
tests and behaviour tests on a headless Game. Whether a torch on floor 3
makes the archers fair is Brandon's play-test: Claude cannot drive Pygame.
"""
import json
import os
import pickle
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import gear  # noqa: E402
import items  # noqa: E402
import lights  # noqa: E402
import senses  # noqa: E402
import unseen  # noqa: E402
from items import make_item_by_id  # noqa: E402
from player import Player  # noqa: E402


def _load(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


LIGHTS = {k: v for k, v in _load('data', 'items', 'light.json').items() if isinstance(v, dict)}
RULES = _load('data', 'lights.json')


def _light(lid, n=1):
    it = make_item_by_id('light', lid)
    it.count = n
    return it


def _hero(per=10):
    p = Player()
    p.PER = per
    p.weapon = None
    p.ranged_weapon = None
    p.shield = None
    p.armor_slots = [None] * 8
    p.inventory = []
    p.status_effects = {}
    return p


def _hold(p, lid):
    lt = _light(lid)
    p._apply_equip(lt)
    assert p.shield is lt and lt.lit
    return lt


# ---------------------------------------------------------------- the data

def test_every_light_is_written_by_lore_across_the_five_tiers():
    tiers = set()
    for lid, d in LIGHTS.items():
        it = make_item_by_id('light', lid)
        assert it is not None and gear.is_light(it), lid
        assert 1 <= int(d['tier']) <= 5, lid
        tiers.add(int(d['tier']))
        assert int(d['sight']) >= 2, lid
        assert int(d['burn']) >= 0 and d['fuel'] in ('self', 'oil', 'none'), lid
        assert (int(d['burn']) == 0) == (d['fuel'] == 'none'), lid
        assert d['lore'] and d['name'] == d['name'].title().replace("'S", "'s"), lid
        # Not a shield: no AC, no plus, never cursed.
        assert gear.ac_value(it) == 0 and not gear.is_core(it) and not gear.is_shield(it)
        assert not it.cursed and not it.can_be_cursed
        if d.get('is_unique'):
            assert d.get('unidentified_name') and int(d.get('peak_floor', 0)) > 0, lid
            assert not items.is_fully_known(it, None), lid       # the unique rules
        else:
            assert it.id_level == 5, lid                          # known by sight
    assert tiers == {1, 2, 3, 4, 5}


def test_the_lights_are_named_in_the_brief_and_their_numbers_are_these():
    t = LIGHTS['torch']
    assert (t['tier'], t['sight'], t['burn'], t['fuel'], t['stacks']) == (1, 2, 400, 'self', True)
    lan = LIGHTS['horn_lantern']
    assert (lan['tier'], lan['sight'], lan['fuel']) == (2, 3, 'oil')
    assert LIGHTS['dark_lantern']['notice'] < LIGHTS['dark_lantern']['sight']
    assert LIGHTS['psyches_lamp']['power'] == 'shows_invisible'
    assert LIGHTS['heros_lamp']['power'] == 'shows_way'
    assert LIGHTS['hecates_torch']['power'] == 'unmasks' and LIGHTS['hecates_torch']['tier'] == 5
    # Every power the data names has its card words.
    for d in LIGHTS.values():
        if d.get('power'):
            assert d['power'] in RULES['powers'] and d['power'] in RULES['powers_short']


def test_the_census_finds_lights_in_every_tier():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    import tier_census
    row = next(r for r in tier_census.census()['rows'] if r['category'].startswith('Lights'))
    assert min(row['counts']) >= 1 and row['verdict'] == 'ok' and row['mismatch'] == 0, row


def test_every_light_shows_its_own_64px_picture():
    import renderer
    installed = set(_load('tools', 'content', 'genart', 'installed_items.json')['items'])
    for lid in LIGHTS:
        path = renderer._resolve_item_sprite_path(lid)
        assert path and os.path.basename(path) == f'{lid}.png', lid
        assert lid in installed, lid


def test_the_rules_file_ships_with_the_game():
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert "('data/lights.json'," in spec
    assert "('data/items'," in spec                  # light.json rides with the items folder


# ---------------------------------------------------------- how bright

def test_a_lit_light_widens_sight_and_a_doused_one_does_not():
    p = _hero()
    base = p.get_sight_radius()
    assert base == 5                                   # PER 10 sees five; an archer shoots from six
    lt = _hold(p, 'torch')
    assert p.get_sight_radius() == base + 2
    lt.lit = False
    assert p.get_sight_radius() == base
    lt.lit = True
    lt.fuel = 0                                        # spent: no light
    assert p.get_sight_radius() == base


@pytest.mark.parametrize('lid', sorted(LIGHTS))
def test_each_light_adds_its_own_sight(lid):
    p = _hero()
    base = p.get_sight_radius()
    _hold(p, lid)
    assert p.get_sight_radius() == base + LIGHTS[lid]['sight']


def test_lights_do_not_add_up_only_the_brightest_counts():
    p = _hero()
    base = p.get_sight_radius()
    spell = lights.status_sight()
    assert spell == RULES['status_sight'] == 3
    p.status_effects['light'] = 50                     # the Light spell
    assert p.get_sight_radius() == base + spell
    _hold(p, 'torch')                                  # 2 under the spell's 3: nothing more
    assert p.get_sight_radius() == base + 3
    p.shield = None
    _hold(p, 'dark_lantern')                           # 4 over the spell's 3: the lantern
    assert p.get_sight_radius() == base + 4
    # A torch held as a weapon (the Prometheus Torch) is a light too.
    p.weapon = types.SimpleNamespace(equipped_light_aura=5, two_handed=False)
    assert p.get_sight_radius() == base + 5
    # An escort's lamp is one more light, never added to a brighter one.
    p.weapon = None
    p.status_effects.pop('light')
    assert p.get_sight_radius(extra_light=2) == base + 4
    p.shield = None
    assert p.get_sight_radius(extra_light=2) == base + 2


def test_senses_that_are_not_light_still_add_on_top():
    p = _hero()
    base = p.get_sight_radius()
    _hold(p, 'horn_lantern')
    p.status_effects['dark_vision'] = 20
    assert p.get_sight_radius() == base + 3 + 4


def test_blindness_and_the_blindfold_put_out_every_light():
    p = _hero()
    _hold(p, 'hecates_torch')
    p.status_effects['blinded'] = 5
    assert p.get_sight_radius(extra_light=2) == 1


# ---------------------------------------------------------- the price

def _watcher():
    return types.SimpleNamespace(perception_range=8, kind='skeletal_archer', family='restless_dead',
                                 x=0, y=0)


def test_a_lit_hero_is_seen_from_farther():
    m = _watcher()
    p = _hero()
    assert senses.sight_range(m, p) == 8
    lt = _hold(p, 'torch')
    assert senses.sight_range(m, p) == 8 + 2
    lt.lit = False                                     # doused: seen no farther
    assert senses.sight_range(m, p) == 8
    p.shield = None
    _hold(p, 'dark_lantern')                           # its shutter throws the light ahead
    assert senses.sight_range(m, p) == 8 + LIGHTS['dark_lantern']['notice']
    p.shield = None
    p.status_effects['light'] = 30                     # the spell's light shows him too
    assert senses.sight_range(m, p) == 8 + lights.status_notice()


def test_the_price_works_on_a_stand_in_hero():
    """senses runs on test stand-ins with no shield or weapons at all."""
    stand_in = types.SimpleNamespace(has_effect=lambda e: False)
    assert lights.shine(stand_in) == 0
    assert senses.sight_range(_watcher(), stand_in) == 8


# ---------------------------------------------------------- fuel

def test_a_torch_burns_down_and_says_when_it_is_low_and_spent():
    lt = _light('torch')
    lt.lit = True
    low = int(lt.burn * RULES['low_share'])
    lt.fuel = low + 1
    assert lights.burn_turn(lt) == 'low' and lights.is_low(lt)
    lt.fuel = 1
    assert lights.burn_turn(lt) == 'out' and not lt.lit and lt.fuel == 0
    assert lights.burn_turn(lt) == ''                  # out: nothing burns


def test_a_light_that_never_burns_out_never_changes():
    lt = _light('everburning_lamp')
    lt.lit = True
    for _ in range(5000):
        assert lights.burn_turn(lt) == ''
    assert lights.is_lit(lt)


def test_only_fresh_unlit_torches_share_a_pack_row():
    p = _hero()
    a, b = _light('torch', 2), _light('torch', 1)
    assert p.add_to_inventory(a) and p.add_to_inventory(b)
    assert len(p.inventory) == 1 and p.inventory[0].count == 3
    half = _light('torch')
    half.fuel = 150
    p.add_to_inventory(half)
    assert len(p.inventory) == 2                       # its own row
    assert items.is_stackable(a) and not items.is_stackable(_light('horn_lantern'))


def test_a_bundle_of_torches_sells_by_its_count():
    import economy
    one, three = _light('torch', 1), _light('torch', 3)
    assert economy.ammo_bundles(three) == 3 / ((one.count_min + one.count_max) / 2)
    assert economy.stock_price(three, 5) > economy.stock_price(one, 5)
    assert economy.ammo_bundles(_light('horn_lantern')) is None
    assert economy.merchant_price(_light('horn_lantern'), 20) > economy.merchant_price(_light('torch'), 20)


# ---------------------------------------------------------- the spell

def test_the_light_spell_lasts_turns_from_intelligence():
    s = RULES['spell']
    assert lights.spell_turns(10) == s['base_turns'] == 100
    assert lights.spell_turns(16) == 100 + 6 * s['turns_per_int']
    assert lights.spell_turns(0) == s['min_turns']
    assert lights.spell_turns(99) == s['max_turns']


def test_the_wands_of_light_read_their_turns_from_todays_data():
    for wid, turns, reveals in (('wand_of_candle_light', 60, False),
                                ('wand_of_torch_light', 120, False),
                                ('lantern_of_diogenes', 120, True)):
        w = make_item_by_id('wand', wid)
        assert lights.wand_light(w) == (turns, reveals), wid
        w.power = '8'                                  # a wand pickled with its old radius
        assert lights.wand_light(w) == (turns, reveals), wid


# ---------------------------------------------------------- the headless game

_SCREEN = None


def _game():
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(_SCREEN, player_name='__test_lights__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.player.shield = None
    g.player.status_effects.pop('light', None)
    return g


def _texts(g, n=6):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def test_a_torch_goes_in_the_off_hand_lit_one_off_the_bundle_with_no_question():
    from game_states import STATE_PLAYER
    g = _game()
    p = g.player
    base = p.get_sight_radius()
    bundle = _light('torch', 3)
    p.inventory.append(bundle)
    t0 = g.turn_count
    g._equip_item(bundle)
    assert g.state == STATE_PLAYER                     # no quiz
    held = p.shield
    assert lights.is_light(held) and held.lit and held is not bundle
    assert bundle.count == 2 and bundle in p.inventory and held not in p.inventory
    assert p.get_sight_radius() == base + 2
    assert g.turn_count == t0 + 1
    assert 'You take up the Torch and light it.' in _texts(g)


def test_a_two_handed_weapon_and_a_light_do_not_go_together():
    g = _game()
    p = g.player
    gs = items.instantiate_weapon('greatsword', 'steel')
    p._apply_equip(gs)
    t = _light('torch')
    p.inventory.append(t)
    g._equip_item(t)
    assert p.shield is None and t in p.inventory
    assert any('free hand' in s for s in _texts(g))
    # ...and a two-hander taken up sends a held light to the pack, out.
    sword = items.instantiate_weapon('longsword', 'steel')
    p._apply_equip(sword)
    lt = _light('horn_lantern')
    p.inventory.append(lt)
    g._equip_item(lt)
    assert p.shield is lt and lt.lit
    p.inventory.append(gs)
    g._equip_item(gs)
    assert p.shield is None and lt in p.inventory and not lt.lit


def test_a_shield_and_a_light_share_one_off_hand():
    g = _game()
    p = g.player
    lt = _light('torch')
    p.inventory.append(lt)
    g._equip_item(lt)
    sh = items.instantiate_shield('kite_shield', 'steel')
    p._apply_equip(sh)
    assert p.shield is sh and lt in p.inventory and not lt.lit
    assert gear.ac_value(sh) > 0
    p.inventory.append(_light('torch'))
    g._equip_item(p.inventory[-1])
    assert lights.is_light(p.shield) and sh in p.inventory


def test_a_spent_torch_lights_the_next_and_the_last_says_so():
    g = _game()
    p = g.player
    bundle = _light('torch', 2)
    p.inventory.append(bundle)
    g._equip_item(bundle)
    first = p.shield
    first.fuel = 1
    g._advance_turn()
    second = p.shield
    assert second is not first and second.lit and second.fuel == second.burn
    assert 'Your Torch gutters out. You light another (0 left).' in _texts(g)
    assert first not in p.inventory                    # burnt away
    second.fuel = 1
    g._advance_turn()
    assert p.shield is None
    assert 'Your Torch gutters out. It was your last one.' in _texts(g)


def test_a_lantern_takes_the_next_flask_of_oil_or_goes_dark():
    g = _game()
    p = g.player
    lan = _light('horn_lantern')
    p.inventory.append(lan)
    g._equip_item(lan)
    oil = make_item_by_id('flask', 'flask_of_fire_oil')
    p.inventory.append(oil)
    lan.fuel = 1
    g._advance_turn()
    assert lan.lit and lan.fuel == lan.burn and oil not in p.inventory
    lan.fuel = 1
    g._advance_turn()
    assert p.shield is lan and not lan.lit and lan.fuel == 0
    assert 'Your Horn Lantern runs dry.' in _texts(g)
    # The Kit's Apply fills it from a flask in the pack, one turn.
    oil2 = make_item_by_id('flask', 'flask_of_fire_oil')
    p.inventory.append(oil2)
    acts = {a['id']: a for a in g._item_actions(lan)}
    assert acts['apply']['label'] == 'Fill' and acts['apply']['enabled']
    t0 = g.turn_count
    g._apply_item(lan)
    assert lan.lit and oil2 not in p.inventory
    assert lan.fuel == lan.burn - 1                    # full, then the filling turn burnt one
    assert g.turn_count == t0 + 1


def test_shift_o_puts_the_light_out_and_lights_it_again_at_no_cost():
    g = _game()
    p = g.player
    lt = _light('torch')
    p.inventory.append(lt)
    g._equip_item(lt)
    base_lit = p.get_sight_radius()
    t0 = g.turn_count
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, unicode='O',
                                      mod=pygame.KMOD_SHIFT, scancode=0))
    assert not lt.lit and p.get_sight_radius() == base_lit - 2
    assert g.turn_count == t0
    fuel = lt.fuel
    g._advance_turn()
    assert lt.fuel == fuel                            # doused: it does not burn
    g._toggle_light()
    assert lt.lit and p.get_sight_radius() == base_lit
    assert {a['id']: a for a in g._item_actions(lt)}['apply']['label'] == 'Put Out'


def test_the_light_spell_lasts_its_turns_and_then_ends():
    import spells
    g = _game()
    p = g.player
    p.INT = 14
    base = p.get_sight_radius()
    g._cast_spell_effect(dict(spells.LEARNABLE_SPELLS['light_spell']))
    want = lights.spell_turns(14)
    assert p.status_effects.get('light') == want == 120
    assert p.get_sight_radius() == base + 3
    assert f'A steady light kindles about you: sight +3 for {want} turns.' in _texts(g)
    # A second cast adds to what is left, never past the cap.
    g._cast_spell_effect(dict(spells.LEARNABLE_SPELLS['light_spell']))
    assert p.status_effects['light'] == min(lights.spell_cap(), 2 * want)
    p.status_effects['light'] = 1
    g._advance_turn()
    assert not p.has_effect('light') and p.get_sight_radius() == base
    assert 'The light about you fades.' in _texts(g)


def test_the_light_spells_words_are_the_datas():
    import spells
    desc = spells.LEARNABLE_SPELLS['light_spell']['desc']
    s = RULES['spell']
    assert f"{s['base_turns']} turns" in desc and f"{s['turns_per_int']} more" in desc
    assert 'radius' not in desc and 'Reveal' not in desc


def test_a_wand_of_light_lights_the_hero_for_its_power_in_turns():
    g = _game()
    p = g.player
    w = make_item_by_id('wand', 'wand_of_torch_light')
    g._apply_wand_effect(w)
    assert p.status_effects.get('light') == 120
    d = make_item_by_id('wand', 'lantern_of_diogenes')
    p.status_effects.pop('light')
    g._apply_wand_effect(d)
    assert p.has_effect('light') and p.has_effect('see_invisible')


def test_psyches_lamp_shows_the_invisible_while_it_burns():
    p = _hero()
    lt = _hold(p, 'psyches_lamp')
    assert unseen.sees_invisible(p)
    lt.lit = False
    assert not unseen.sees_invisible(p)


def test_hecates_torch_shows_what_lies_in_wait_in_its_light():
    p = _hero()
    p.x, p.y = 10, 10
    lurker = types.SimpleNamespace(ai_pattern='ambush', _aware=False, x=13, y=10, family='')
    assert unseen.lurking(lurker, p)
    lt = _hold(p, 'hecates_torch')
    assert not unseen.lurking(lurker, p)
    far = types.SimpleNamespace(ai_pattern='mimic', _aware=False, x=40, y=10, family='')
    assert unseen.lurking(far, p)                      # beyond its light
    lt.lit = False
    assert unseen.lurking(lurker, p)


def test_heros_lamp_shows_the_way_down():
    from dungeon import _find_stair_tiles
    g = _game()
    p = g.player
    _up, down = _find_stair_tiles(g.dungeon.tiles, g.dungeon.width, g.dungeon.height)
    assert down is not None
    g.dungeon.explored.discard(down)
    lt = _light('heros_lamp')
    p.inventory.append(lt)
    g._equip_item(lt)
    g._advance_turn()
    assert down in g.dungeon.explored


def test_the_card_says_what_a_light_does_first():
    g = _game()
    lt = _light('dark_lantern')
    lines = g._item_power_lines(lt)
    assert lines[0] == 'Sight +4 while it is lit.'
    assert any('only 2 tiles farther' in s for s in lines)
    assert any('only your brightest light counts' in s for s in lines)
    assert 'No AC: it is a light, not a shield.' in lines
    torch = _light('torch')
    assert any('Burns 400 turns' in s for s in g._item_power_lines(torch))
    assert any('never burns out' in s for s in g._item_power_lines(_light('everburning_lamp')))


def test_the_sidebar_marks_a_light_burning_low_or_out():
    g = _game()
    p = g.player
    lt = _light('torch')
    p.inventory.append(lt)
    g._equip_item(lt)
    assert g._light_hud_line() == ''
    lt.fuel = 30
    assert g._light_hud_line() == 'Torch: 30 turns'
    lt.lit = False
    assert g._light_hud_line() == 'Torch: out'


def test_a_light_rides_in_a_loadout_as_the_off_hand():
    g = _game()
    p = g.player
    lt = _light('horn_lantern')
    p.inventory.append(lt)
    g._equip_item(lt)
    g._kit_save(0)
    assert g._kits()[0]['pieces']['shield'] is lt
    g._unequip_slot('shield', lt)
    assert p.shield is None and lt in p.inventory and not lt.lit
    plan = g._kit_plan(0)
    assert not plan['refused'] and any(s.item is lt for s in plan['steps'])


def test_a_held_light_survives_the_save():
    p = _hero()
    lt = _hold(p, 'horn_lantern')
    lt.fuel = 333
    clone = pickle.loads(pickle.dumps(p))
    assert lights.is_light(clone.shield) and clone.shield.lit and clone.shield.fuel == 333
    # A light pickled before a field existed reads its class default.
    old = _light('torch')
    for f in ('lit', 'fuel', 'power', 'notice'):
        old.__dict__.pop(f, None)
    old2 = pickle.loads(pickle.dumps(old))
    assert old2.lit is False and lights.fuel_left(old2) == old2.burn and lights.notice_of(old2) == 2


def test_wear_and_blessings_never_touch_a_light():
    import status_effects as se
    lt = _light('torch')
    assert not se._can_rust(lt) and not se._can_scorch(lt) and not se._can_corrode(lt)
    assert not items.wear_down(lt)
    import altar
    assert not altar.blessing_helps(lt)                # an altar's blessing gives it nothing


# ---------------------------------------------------------- where they are found

def test_floor_loot_holds_torches_early_and_lanterns_deeper():
    from level_manager import LevelManager
    random.seed(3)
    items.bind_unique_registry(set())
    found = {}
    lm = LevelManager()
    for floor in (2, 4, 6, 8, 12, 16, 30, 34, 38, 55, 60, 70, 75):
        _d, _m, ground = lm.generate(floor)
        for it in ground:
            if lights.is_light(it):
                found.setdefault(it.id, []).append(floor)
    assert 'torch' in found and min(found['torch']) <= 16, found
    assert set(found) - {'torch'}, found


def test_the_general_trader_and_the_sutler_sell_a_torch():
    import traders
    d = traders.data()['traders']
    for kind in ('generalist', 'sutler'):
        stock = traders.build_stock(d[kind], 5, random.Random(7))
        assert any(getattr(w, 'id', '') == 'torch' for w in stock), kind
    deep = traders.build_stock(d['damned_generalist'], 80, random.Random(9))
    assert isinstance(deep, list)


def test_chests_and_drops_draw_lights():
    import container_system as cs
    common = cs._build_common_pool({'loot_table': {'light': 1}}, 40)
    assert {'torch', 'horn_lantern'} <= {i.id for i in common}
    assert not any(getattr(i, 'is_unique', False) for i in common)
    uniq = cs._build_unique_pool({'loot_table': {'light': 1}}, 50)
    assert 'psyches_lamp' in {i.id for i in uniq}
    assert cs.DROP_MAGIC_SHARE['light'] > 0
    tpl = _load('data', 'chest_templates.json')
    assert sum(1 for t in tpl.values() if isinstance(t, dict) and 'light' in t.get('loot_table', {})) >= 3


def test_the_screens_draw_a_light_in_the_hand_and_in_the_pack():
    """The Kit's Off Hand tab, the equip menu, the @ sheet, the lore page
    and the sidebar, drawn by the game's own code with a light held and
    others in the pack (no crash, the right words in the right rows)."""
    from game_states import STATE_KIT, STATE_EQUIP_MENU, STATE_LORE, STATE_PLAYER
    g = _game()
    p = g.player
    p.inventory += [_light('torch', 3), _light('horn_lantern'), _light('psyches_lamp')]
    g._equip_item(p.inventory[-3])
    held = p.shield
    held.fuel = 20                                     # burning low: the sidebar marker
    g.state = STATE_PLAYER
    g.render()
    g._open_kit_panel()
    assert g.state == STATE_KIT
    g._kit_tab = [s for _l, s in g._KIT_TABS].index('shields')
    rows = g._kit_rows_for_slug('shields')
    assert {getattr(it, 'id', '') for _s, it in rows} >= {'torch', 'horn_lantern'}
    cells = g._kit_cells_for_item('shields', 'equip', held)
    assert cells[2] == '-' and 'Sight +2' in cells[-1] and 'lit' in cells[-1]
    g.render()
    g.state = STATE_PLAYER
    g._open_equip_menu()
    assert g.state == STATE_EQUIP_MENU
    g._menu_tab = [lab for lab, _f in g._EQUIP_TABS].index('Off Hand')
    g.render()
    g.state = STATE_PLAYER
    g._open_character_sheet()
    g.render()
    entries = g._charsheet_loadout_entries()
    assert next(e for e in entries if e['slot'] == 'shield')['label'] == 'Light'
    g.state = STATE_PLAYER
    g._lore_subject = held
    g.state = STATE_LORE
    g.render()


def test_the_qa_arsenal_hands_over_every_light_and_oil():
    g = _game()
    g.player.qa_tools = True
    g.player.inventory = []
    g._qa_arsenal_sampler()
    have = {getattr(i, 'id', '') for i in g.player.inventory}
    assert set(LIGHTS) <= have and 'flask_of_fire_oil' in have
    torches = next(i for i in g.player.inventory if i.id == 'torch')
    assert torches.count == 3


def test_the_help_pages_say_what_the_data_says():
    page = _load('data', 'ui', 'gear_and_load.json')
    sec = next(s for s in page['sections'] if s['heading'] == 'A light in your off hand')
    text = ' '.join(sec['paragraphs'])
    t = LIGHTS['torch']
    assert f"sight +{t['sight']} and burns {t['burn']} turns" in text
    s = RULES['spell']
    assert f"lasts {s['base_turns']} turns, {s['turns_per_int']} more" in text
    assert 'only your brightest light counts' in text
    assert any(k == 'Shift+O' for k, _v in sec['rows'])
    hints = _load('data', 'hints.json')['1']
    assert any('torch' in h for h in hints)


def test_a_thief_takes_a_carried_torch_but_never_the_one_in_hand():
    import theft
    p = _hero()
    lt = _hold(p, 'torch')
    spare = _light('torch', 2)
    p.inventory.append(spare)
    took = theft.stealable(p)
    assert spare in took and lt not in took
