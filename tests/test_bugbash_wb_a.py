"""Bug bash on the winning build, area A (2026-11-13): gear, armour and the
arsenal (slices 1, 4 and 5) and where they meet.

Each test names the finding it pins (WB-Ann in the bug bash report). Real
headless Game: the turn advance, the dressing runner, the key handler and
the Kit actions are the game's own. Unit tests cannot say whether any of it
feels right: that is Brandon's play-test.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
import known_by_hand as kbh  # noqa: E402
from game_states import (STATE_PLAYER, STATE_ASK, STATE_LOADOUTS,  # noqa: E402
                         STATE_QUAFF_MENU)

pygame.init()


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bugbash_wb_a__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    p = g.player
    from items import ARMOR_SLOTS
    p.shield = None
    p.weapon = None
    p.armor_slots = [None] * len(ARMOR_SLOTS)
    p.accessory_slots = [None] * 4
    p.amulet_slot = None
    p.belt_slot = None
    p.known_by_hand = set()
    p.by_hand_tiers = {}
    p.hp = p.max_hp = 500
    return g


def _said(g, n=40):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _key(g, key, uni='', mod=0):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=mod, scancode=0))


def _body(g):
    from items import ARMOR_SLOTS
    return g.player.armor_slots[ARMOR_SLOTS.index('body')]


def _plate(g):
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(g.player, plate)
    g.player.inventory.append(plate)
    return plate


def _goblin(g, dx=1, **extra):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    m = Monster(dict(defs['goblin'], id='goblin'), g.player.x + dx, g.player.y)
    for k, v in extra.items():
        setattr(m, k, v)
    g.monsters.append(m)
    return m


def _weapon(template='mace', material='iron'):
    w = items.instantiate_weapon(template, material)
    return w


# ------------------------------------------------- WB-A01: Caps Lock

def test_wb_a01_caps_lock_e_is_the_equip_menu_not_the_loadouts(game):
    _key(game, pygame.K_e, 'E', pygame.KMOD_CAPS)
    assert game.state != STATE_LOADOUTS
    game.state = STATE_PLAYER
    # Caps Lock and Shift together: the Loadouts, as Shift+E always is.
    _key(game, pygame.K_e, 'e', pygame.KMOD_CAPS | pygame.KMOD_LSHIFT)
    assert game.state == STATE_LOADOUTS


def test_wb_a01_caps_lock_s_swaps_and_takes_no_stance(game):
    import stance
    p = game.player
    sword, mace = _weapon('longsword'), _weapon('mace')
    p.inventory += [sword, mace]
    game._equip_item(sword)
    game._ready_weapon(mace)
    _key(game, pygame.K_s, 'S', pygame.KMOD_CAPS)
    assert stance.of(p) == 'neutral'
    assert p.weapon is mace


def test_wb_a01_caps_lock_c_is_not_the_coat_picker(game):
    p = game.player
    mace = _weapon('mace', 'steel')
    p.inventory.append(mace)
    game._equip_item(mace)
    p.inventory.append(items.make_item_by_id('flask', 'silver_dust'))
    _key(game, pygame.K_c, 'C', pygame.KMOD_CAPS)
    assert not (game.state == STATE_QUAFF_MENU and getattr(game, '_quaff_mode', '') == 'coat')


# ------------------------------- WB-A02: no dressing while paralysed

def test_wb_a02_a_paralysed_hero_does_not_go_on_dressing(game, monkeypatch):
    p = game.player
    plate = _plate(game)
    m = _goblin(game)
    t0 = game.turn_count
    monkeypatch.setattr(game, '_sees_monster', lambda mon: True)

    def _blow():
        if game.turn_count - t0 == 2:
            game._blows_on_hero = game._hero_blows() + 1
            game._last_striker = m
            p.add_effect('paralyzed', 10)
    monkeypatch.setattr(game, '_do_monster_turns', _blow)
    game._equip_item(plate)
    # A paralysing blow: there is nothing to ask him, he cannot move.
    if game.state == STATE_ASK:
        game._ask_input(pygame.K_y)
    assert _body(game) is None and plate in p.inventory
    assert game._busy is None and game.state == STATE_PLAYER


def test_wb_a02_a_gaze_that_paralyses_mid_dressing_stops_it(game, monkeypatch):
    p = game.player
    plate = _plate(game)
    t0 = game.turn_count

    def _gaze():
        if game.turn_count - t0 == 2:
            p.add_effect('paralyzed', 10)       # no blow: no interrupt by a strike
    monkeypatch.setattr(game, '_do_monster_turns', _gaze)
    game._equip_item(plate)
    assert _body(game) is None and plate in p.inventory
    assert game.turn_count - t0 < 5
    assert game._busy is None


# ------------------------ WB-A03: a friend in view does not stop it

def test_wb_a03_a_friend_coming_into_view_does_not_stop_the_dressing(game, monkeypatch):
    plate = _plate(game)
    _goblin(game, dx=5, is_allied=True)
    t0 = game.turn_count
    monkeypatch.setattr(game, '_sees_monster', lambda mon: game.turn_count - t0 >= 2)
    monkeypatch.setattr(game, '_do_monster_turns', lambda: None)
    game._equip_item(plate)
    assert game.state == STATE_PLAYER
    assert _body(game) is plate


# ---------------- WB-A04: a piece stolen mid-dressing is not "put on"

def test_wb_a04_a_piece_stolen_mid_dressing_spends_no_more_turns(game, monkeypatch):
    p = game.player
    plate = _plate(game)
    m = _goblin(game)
    t0 = game.turn_count
    monkeypatch.setattr(game, '_sees_monster', lambda mon: True)

    def _thief():
        if game.turn_count - t0 == 2:
            p.inventory.remove(plate)            # a thief's blow takes it
            game._blows_on_hero = game._hero_blows() + 1
            game._last_striker = m
    monkeypatch.setattr(game, '_do_monster_turns', _thief)
    game._equip_item(plate)
    # Nothing is left to put on: no "Keep dressing?" for a plate that is
    # not there, and no more turns spent on it.
    if game.state == STATE_ASK:
        game._ask_input(pygame.K_y)
    assert game.state == STATE_PLAYER
    assert game.turn_count - t0 == 2
    assert game._busy is None
    assert any('is gone from your pack' in t for t in _said(game, 4))


# ------------------------------- WB-A05: the earplugs' flag

def test_wb_a05_lost_earplugs_take_the_wax_with_them(game):
    import counters
    p = game.player
    plugs = items.make_item_by_id('accessory', 'beeswax_earplugs')
    p.inventory.append(plugs)
    game._apply_item(plugs)
    assert counters.ears_stopped(p)
    p.inventory.remove(plugs)                     # dropped, sold or stolen
    assert not counters.ears_stopped(p)
    # Another pair picked up later is not in his ears by itself.
    again = items.make_item_by_id('accessory', 'beeswax_earplugs')
    p.inventory.append(again)
    assert not counters.ears_stopped(p)
    assert game._apply_label(again) == 'Put In'


# --------- WB-A06, rewritten to Brandon's rule (2026-11-14, Q10): the back
# remembers a weapon dropped, thrown or stolen; a sale lets go of it.
# (tests/test_remembered_sets.py has the whole rule.)

def test_wb_a06_a_dropped_readied_weapon_is_at_your_back_again_when_picked_up(game):
    import loadouts
    p = game.player
    mace = _weapon()
    p.inventory.append(mace)
    game._ready_weapon(mace)
    game._do_drop_item(mace)
    assert p.readied_weapon is None and loadouts.readied_memory(p) is mace
    game._pickup(target=mace)
    assert p.readied_weapon is mace
    assert _said(game, 3)[-1] == f'The {game._bare_name(mace)} is At Your Back again.'


def test_wb_a06_a_sold_readied_weapon_is_let_go(game):
    import loadouts
    from mystery_system import MerchantNPC, build_trader
    import random as _random
    p = game.player
    mace = _weapon()
    p.inventory.append(mace)
    game._ready_weapon(mace)
    game.ground_items = [i for i in game.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader('generalist', game.dungeon_level, _random.Random(11))
    m.x, m.y = p.x + 1, p.y
    m.purse = 100000
    game.ground_items.append(m)
    game._open_shop()
    game._shop_tab = 1
    game._trader_sell(mace)
    assert mace not in p.inventory and loadouts.readied_memory(p) is None
    p.add_to_inventory(mace)                     # bought back: an ordinary weapon
    assert p.readied_weapon is None


def test_wb_a06_the_back_weapon_drawn_by_e_comes_back_to_the_back(game):
    # Unchanged rule: drawn into the hand by the equip menu, it is still the
    # weapon At Your Back once it is back in the pack.
    p = game.player
    sword, mace = _weapon('longsword'), _weapon('mace')
    p.inventory += [sword, mace]
    game._equip_item(sword)
    game._ready_weapon(mace)
    game._equip_item(mace)
    assert p.weapon is mace and p.readied_weapon is None
    game._equip_item(sword)
    assert p.readied_weapon is mace


# ---------------------------- WB-A07: "1 pieces" on the Loadouts screen

def test_wb_a07_a_one_piece_kit_says_one_piece(game, monkeypatch):
    p = game.player
    mace = _weapon()
    p.inventory.append(mace)
    game._equip_item(mace)
    game._kit_save(0)
    pygame.display.set_mode((1280, 720))
    game.screen = pygame.display.get_surface()
    game.on_resize(1280, 720)
    seen = []
    real = game._fit_line

    def _rec(text, *a, **k):
        seen.append(str(text))
        return real(text, *a, **k)
    monkeypatch.setattr(game, '_fit_line', _rec)
    game._open_loadouts()
    game.render()
    assert any(s.startswith('1 piece:') for s in seen), seen
    assert not any('1 pieces' in s for s in seen)


# --------------- WB-A09: an old save's Aegis turns every gaze, as a new one

def test_wb_a09_an_old_saves_aegis_learns_its_counter_and_template():
    import counters
    import gear
    import gear_saves
    aegis = items.make_item_by_id('shield', 'aegis_of_athena')
    assert 'gaze' in counters.item_counters(aegis)
    want_tpl = aegis.template_basis
    # Pickled before slices 1 and 5: neither field was on the object.
    aegis.__dict__.pop('counters', None)
    aegis.__dict__.pop('template_basis', None)
    assert 'gaze' not in counters.item_counters(aegis)
    assert gear_saves.refresh_named(aegis)
    assert 'gaze' in counters.item_counters(aegis)
    assert gear.template_of(aegis) == want_tpl


# ------------- WB-A10: a flask that does no harm leaves no burn or pitting

def test_wb_a10_a_flask_over_a_friend_sets_nothing_alight(game):
    p = game.player
    friend = _goblin(game, dx=2, is_allied=True)
    friend._npc_encounter_tag = 'a_test_traveller'
    hp0 = friend.hp
    oil = items.make_item_by_id('flask', 'flask_of_fire_oil')
    p.inventory.append(oil)
    game._throw_flask(oil, friend, friend.x, friend.y)
    assert friend.hp == hp0
    assert not friend.has_effect('burning')
    assert not any('set alight' in t for t in _said(game, 3))


# ------------------ WB-A11: the Kit's refused Coat Weapon reads as a sentence

def test_wb_a11_a_refused_coating_from_the_kit_says_why_in_plain_words(game):
    from game_states import STATE_KIT
    p = game.player
    mace = _weapon('mace', 'steel')
    p.inventory.append(mace)
    game._equip_item(mace)
    dust = items.make_item_by_id('flask', 'silver_dust')
    dust.count = 2
    p.inventory.append(dust)
    game._apply_item(dust)                       # silvered now
    game.state = STATE_KIT
    game._item_action_run('apply', dust, {'screen': 'kit'})
    last = _said(game, 1)[0]
    assert 'coat weapon it' not in last.lower()
    assert 'already silvered' in last
    assert last[:1].isupper()


# -------- WB-A12: a refused coating does not name an unidentified metal

def test_wb_a12_a_coating_refusal_does_not_name_an_unknown_metal(game):
    import coatings
    from items import is_fully_known
    p = game.player
    mace = _weapon('mace', 'silver')                # found, not identified
    p.inventory.append(mace)
    game._equip_item(mace)
    assert not is_fully_known(mace, p)
    dust = items.make_item_by_id('flask', 'silver_dust')
    p.inventory.append(dust)
    # "Your Pale Gleaming Mace is already silvered" told him the metal.
    assert coatings.refusal(p, dust) == ''
    assert game._apply_block(dust) == ''
    # Identified, the rule stands: silver dust on silver adds nothing.
    mace.id_level = 5
    assert 'already silvered' in coatings.refusal(p, dust)


def test_wb_a12_the_smiths_inlay_is_known_on_an_unknown_blade(game):
    import coatings
    import smithing
    p = game.player
    mace = _weapon('mace', 'steel')
    assert smithing.inlay(mace, 'silver')
    p.inventory.append(mace)
    game._equip_item(mace)
    dust = items.make_item_by_id('flask', 'silver_dust')
    p.inventory.append(dust)
    # He watched the smith inlay it: that much he knows.
    assert 'already silvered' in coatings.refusal(p, dust)


# --------------------------- WB-A08: a lining is part of the piece's profile

def test_wb_a08_a_lined_cloak_shows_its_lining_where_the_damage_is_read(game):
    import gear
    import smithing
    p = game.player
    cloak = items.instantiate_armor('cloak', 'leather')
    assert smithing.line(cloak, 'fire')
    from items import ARMOR_SLOTS
    p.armor_slots[ARMOR_SLOTS.index('cloak')] = cloak
    assert gear.piece_profile(cloak).get('fire') == pytest.approx(smithing.LINING_MULT)
    # Counted once, not twice.
    assert p.get_armor_resistance('fire') == pytest.approx(
        gear.worn_factor(p, 'fire'))
    assert 'fire' in game._kit_resist_str(cloak)
