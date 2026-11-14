"""Remembered sets (round 3, 2026-11-14; Brandon's Q10): "player can freely
equip items, but we should persist sets under the quickswapping function if
a weapon is dropped or thrown".

The weapon At Your Back and every Loadout keep a piece that leaves the pack
by being dropped, thrown or stolen. Picked up again (a dead thief gives it
back), it is in its place again and one line says so. Sold, destroyed, used
up or made into another object, it is let go for good. While it is away the
Kit, the @ sheet and the Loadouts screen show it "(not carried)", S says it
is not with him, and changing into a kit skips it at no cost.

Real headless Game; the last test is a journey with real keys. Unit tests
cannot say whether any of it feels right: that is Brandon's play-test.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
import known_by_hand as kbh  # noqa: E402
import loadouts as sets  # noqa: E402
from game_states import STATE_PLAYER  # noqa: E402

pygame.init()
SIZE = (1600, 900)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import layout
    import save_system
    from main import Game
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(5)
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode(SIZE)
    layout.update(*SIZE)
    g = Game(screen, player_name='__remembered_sets__', secret_build=None)
    g.on_resize(*SIZE)
    g._resize_grace = 0
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
    p.hp = p.max_hp = 500
    _open_floor(g, p.x, p.y, 4)
    return g


def _open_floor(g, x, y, r=3):
    from dungeon import FLOOR
    d = g.dungeon
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            if 0 < xx < d.width - 1 and 0 < yy < d.height - 1:
                d.tiles[yy][xx] = FLOOR
    g._refresh_fov()


def _said(g, n=30):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _carry(g, it):
    g.player.inventory.append(it)
    return it


def _goblin(g, dx=1):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)
    m = Monster(dict(d['goblin'], id='goblin'), g.player.x + dx, g.player.y)
    g.monsters.append(m)
    return m


def _pick_up_at(g, it):
    """Step onto the piece and pick it up through the game's own pickup."""
    g.player.x, g.player.y = it.x, it.y
    g._pickup(target=it)


# ------------------------------------------------------- the pure rules

def test_let_go_forgets_the_back_and_every_kit():
    from player import Player
    p = Player()
    mace = items.instantiate_weapon('mace', 'iron')
    helm = items.instantiate_armor('iron_helm', 'chain_steel')
    p.inventory = [mace, helm]
    p.readied_weapon = mace
    p.loadouts[0]['pieces'] = {'readied': mace, 'head': helm}
    p.loadouts[2]['pieces'] = {'weapon': mace}
    assert sets.remembered(p) == [mace, helm]
    assert sets.kit_names_holding(p, mace) == ['Kit One', 'Kit Three']
    p.inventory.remove(mace)                       # dropped: away, still held
    assert sets.away(p, mace) and sets.away_pieces(p) == [mace]
    assert p.readied_weapon is None and sets.readied_memory(p) is mace
    assert sets.let_go(p, mace)
    assert sets.readied_memory(p) is None and not sets.holds(p, mace)
    assert p.loadouts[0]['pieces'] == {'head': helm} and p.loadouts[2]['pieces'] == {}
    assert not sets.let_go(p, mace)


def test_the_back_line_reads():
    assert sets.back_line('Plain Dagger', True, []) == 'The Plain Dagger is At Your Back again.'
    assert sets.back_line('Iron Helm', False, ['Kit One', 'Kit Two']) == \
        'The Iron Helm is back in Kit One and Kit Two.'
    assert sets.back_line('Plain Mace', True, ['Kit One', 'Kit Two', 'Iron']) == \
        'The Plain Mace is At Your Back again, and back in Kit One, Kit Two and Iron.'
    assert sets.back_line('Plain Mace', False, []) == ''
    assert sets.not_carried('Silver Mace') == 'Silver Mace (not carried)'


# ------------------------------------------------- dropped, then picked up

def test_a_dropped_readied_weapon_is_remembered_and_back_when_picked_up(game):
    p = game.player
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    sword = _carry(game, items.instantiate_weapon('longsword', 'iron'))
    game._equip_item(sword)
    game._ready_weapon(mace)
    name = game._bare_name(mace)
    game._do_drop_item(mace)
    # Away: not drawn, but remembered, and every screen says so.
    assert p.readied_weapon is None and sets.readied_memory(p) is mace
    p.x += 1                                        # a step off its tile
    assert ('away', mace) in game._kit_collect_items()
    assert game._kit_row_name('away', mace) == f'{game._display_name(mace)} (not carried)'
    assert [a['id'] for a in game._item_actions(mace)] == ['lore']
    back = next(e for e in game._charsheet_loadout_entries() if e['slot'] == 'readied')
    assert back['item'] is None and game._loadout_entry_text(back) == f'{name} (not carried)'
    t0 = game.turn_count
    assert not game._swap_weapons()
    assert _said(game)[-1] == f'Your {name} is not with you. Pick it up again and S draws it.'
    assert game.turn_count == t0 and p.weapon is sword
    # Picked up: in its place again, with one line after the pickup's own.
    _pick_up_at(game, mace)
    assert p.readied_weapon is mace
    said = _said(game, 6)
    i = said.index(f'You pick up the {name}.')
    assert said[i + 1] == f'The {name} is At Your Back again.'
    assert game._swap_weapons() and p.weapon is mace and p.readied_weapon is sword


def test_the_screens_draw_with_a_piece_away(game):
    from game_states import STATE_KIT, STATE_LOADOUTS
    p = game.player
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    helm = _carry(game, items.instantiate_armor('iron_helm', 'chain_steel'))
    kbh.learn(p, helm)
    game._equip_item(helm)
    game._ready_weapon(mace)
    game._kit_save(0)
    game._unequip_slot('head', helm)
    game._do_drop_item(mace)
    game._do_drop_item(helm)
    p.x += 1
    assert game._kit_lines(0) == [('At Your Back', f'{game._bare_name(mace)} (not carried)'),
                                  ('Head', f'{game._bare_name(helm)} (not carried)')]
    for opener, state in ((game._open_kit_panel, STATE_KIT), (game._open_loadouts, STATE_LOADOUTS),
                          (game._open_character_sheet, None)):
        opener()
        if state:
            assert game.state == state
        game.render()
        game.state = STATE_PLAYER
    # The Kit with the away row chosen: its card, and Lore its one action.
    game._open_kit_panel()
    game._kit_tab = [t[1] for t in game._KIT_TABS].index('weapons')
    rows = game._kit_rows_for_slug('weapons')
    game._kit_sel = next(i for i, (src, it) in enumerate(rows) if it is mace)
    assert rows[game._kit_sel][0] == 'away'
    assert [a['id'] for a in game._kit_actions()] == ['lore']
    card = [t for t, _c, _f in game._kit_detail_lines_for_item('weapons', 'away', mace)]
    assert card[0].endswith('(not carried)') and 'Source: At Your Back' in card
    assert 'Not with you: dropped, thrown or stolen. Pick it up again and S draws it.' in card
    game.render()
    game.state = STATE_PLAYER


# ------------------------------------------------------------ stolen

def test_a_stolen_kit_piece_comes_back_from_the_dead_thief(game):
    import theft
    p = game.player
    helm = _carry(game, items.instantiate_armor('iron_helm', 'chain_steel'))
    kbh.learn(p, helm)
    game._equip_item(helm)
    game._kit_save(1)
    game._unequip_slot('head', helm)
    p.inventory = [helm]                            # the one thing to take
    thief = _goblin(game, 3)
    msg = theft.steal(game, thief, 'item', random.Random(1))
    assert 'snatches' in msg and helm in thief.stolen_items and helm not in p.inventory
    assert sets.away(p, helm) and game._kit_plan(1)['missing'] == [helm]
    game._sets_prune(force=True)                    # in a thief's hands: kept
    assert sets.kit_names_holding(p, helm) == ['Kit Two']
    theft.give_back(game, thief)
    game.monsters.remove(thief)
    _pick_up_at(game, helm)
    assert f'The {game._bare_name(helm)} is back in Kit Two.' in _said(game, 4)
    plan = game._kit_plan(1)
    assert not plan['missing'] and [s.item for s in plan['steps']] == [helm]


# ------------------------------------------------------- changing kits

def test_changing_into_a_kit_skips_a_missing_piece_at_no_cost(game):
    p = game.player
    plate = _carry(game, items.instantiate_armor('plate', 'chain_steel'))
    helm = _carry(game, items.instantiate_armor('iron_helm', 'chain_steel'))
    for it in (plate, helm):
        kbh.learn(p, it)
        game._equip_item(it)
    game._kit_save(0)
    game._unequip_slot('body', plate)
    game._unequip_slot('head', helm)
    game._do_drop_item(plate)
    p.x += 1
    plan = game._kit_plan(0)
    assert plan['missing'] == [plate] and plan['turns'] == game._don_turns(helm)
    t0 = game.turn_count
    game._kit_wear(0)
    while game._busy is not None:
        game._advance_turn()
    from items import ARMOR_SLOTS
    assert p.armor_slots[ARMOR_SLOTS.index('head')] is helm
    assert p.armor_slots[ARMOR_SLOTS.index('body')] is None
    assert game.turn_count - t0 == game._don_turns(helm)
    assert any(t == f'Kit One: the {game._bare_name(plate)} is not with you, so it is skipped.'
               for t in _said(game))
    assert sets.kit_names_holding(p, plate) == ['Kit One']      # still remembered


# ------------------------------------------------- let go for good

def test_selling_lets_go_for_good(game):
    from mystery_system import MerchantNPC, build_trader
    p = game.player
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    game._ready_weapon(mace)
    game._kit_save(0)
    game.ground_items = [i for i in game.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader('generalist', game.dungeon_level, random.Random(11))
    m.x, m.y = p.x + 1, p.y
    m.purse = 100000
    game.ground_items.append(m)
    game._open_shop()
    offer, why = game._trader_offer(mace)
    assert why is None, why
    game._shop_tab = 1
    game._trader_sell(mace)
    assert mace not in p.inventory
    assert sets.readied_memory(p) is None and not sets.kit_names_holding(p, mace)
    # Bought back, it is an ordinary weapon: the sale ended it.
    p.add_to_inventory(mace)
    assert p.readied_weapon is None


def test_a_throw_that_shatters_lets_go(game, monkeypatch):
    p = game.player
    dagger = _carry(game, items.instantiate_weapon('dagger', 'iron'))
    game._ready_weapon(dagger)
    monkeypatch.setattr(random, 'random', lambda: 0.0)          # it breaks
    game._throw_weapon(dagger, None, p.x + 2, p.y)
    assert dagger not in game.ground_items
    assert sets.readied_memory(p) is None


def test_a_piece_gone_from_the_world_is_let_go(game):
    """Burned, dissolved, laid on an altar, given away: whatever took it,
    a piece found nowhere any more leaves the back and the kits."""
    p = game.player
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    game._ready_weapon(mace)
    game._kit_save(2)
    game._do_drop_item(mace)
    game._sets_prune(force=True)
    assert sets.readied_memory(p) is mace          # on the floor: kept
    game.ground_items.remove(mace)
    game._sets_prune(force=True)
    assert sets.readied_memory(p) is None and not sets.kit_names_holding(p, mace)
    assert all(src != 'away' for src, _it in game._kit_collect_items())


def test_a_reforged_weapon_is_the_same_object_and_stays_at_your_back(game):
    import smithing
    p = game.player
    sword = _carry(game, items.instantiate_weapon('longsword', 'iron'))
    game._ready_weapon(sword)
    game._kit_save(0)
    smithing.reforge(sword, 'mace')
    assert sword.id == 'iron_mace'
    assert p.readied_weapon is sword and sets.kit_names_holding(p, sword) == ['Kit One']


# ------------------------------------------------------------ saves

def test_a_piece_away_on_another_floor_keeps_its_place_through_a_save(game):
    import main
    import save_system
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    game._ready_weapon(mace)
    game._kit_save(0)
    game._do_drop_item(mace)
    # The floor it lies on is left behind (a stored floor).
    game.ground_items.remove(mace)
    game.level_mgr._saved[game.dungeon_level + 40] = (game.dungeon, [], [mace])
    assert save_system.save_game(game)
    g2, note = main._restore_saved_game(game.screen, game.player_name,
                                        save_system.load_game(game.player_name))
    assert g2 is not None, note
    stored = g2.level_mgr._saved[game.dungeon_level + 40][2]
    there = next(i for i in stored if getattr(i, 'id', '') == mace.id)
    q = g2.player
    assert sets.readied_memory(q) is there and q.loadouts[0]['pieces']['readied'] is there
    assert sets.away(q, there)
    # Back on that floor and picked up: in its place again.
    stored.remove(there)
    there.x, there.y = q.x, q.y
    g2.ground_items.append(there)
    g2._pickup(target=there)
    assert q.readied_weapon is there


def test_a_save_lets_go_of_a_piece_that_is_gone(game):
    import main
    import save_system
    mace = _carry(game, items.instantiate_weapon('mace', 'iron'))
    game._ready_weapon(mace)
    game._kit_save(1)
    game._do_drop_item(mace)
    game.ground_items.remove(mace)                  # gone: nothing holds it but the sets
    assert save_system.save_game(game)
    g2, _note = main._restore_saved_game(game.screen, game.player_name,
                                         save_system.load_game(game.player_name))
    assert sets.readied_memory(g2.player) is None
    assert g2.player.loadouts[1]['pieces'] == {}


def test_an_old_save_with_no_remembered_pieces_loads():
    from player import Player
    p = Player()
    state = p.__getstate__()
    for k in ('_readied_weapon', 'loadouts'):
        state.pop(k, None)
    q = Player.__new__(Player)
    q.__setstate__(state)
    assert sets.readied_memory(q) is None and sets.remembered(q) == []
    assert sets.away_pieces(q) == []


# ------------------------------------------------- the journey, real keys

class _Hero:
    def __init__(self, g):
        self.g = g
        self._mark = len(g.msg_log.entries)

    def frame(self):
        self.g.update(1 / 30)
        self.g.render()

    def key(self, k, uni=''):
        if isinstance(k, str):
            uni = uni or k
            k = getattr(pygame, f'K_{k.lower()}')
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=uni,
                                               mod=0, scancode=0))
        self.frame()

    def said(self):
        out = [str(e[0]) for e in self.g.msg_log.entries[self._mark:]]
        self._mark = len(self.g.msg_log.entries)
        return out


def test_journey_ready_a_dagger_throw_it_pick_it_up_and_s_draws_it(game, monkeypatch):
    from game_states import STATE_KIT, STATE_THROW_MENU, STATE_TARGET
    g = game
    p = g.player
    h = _Hero(g)
    sword = _carry(g, items.instantiate_weapon('longsword', 'iron'))
    g._equip_item(sword)
    dagger = _carry(g, items.instantiate_weapon('dagger', 'iron'))
    monkeypatch.setattr(g, '_get_weapon_break_chance', lambda w: 0.0)
    name = g._bare_name(dagger)
    h.frame()
    h.said()
    # K: the Kit, to the dagger, R readies it.
    h.key('k')
    assert g.state == STATE_KIT
    for _ in range(10):
        rows = g._kit_rows_for_slug(g._KIT_TABS[g._kit_tab][1]) \
            if g._KIT_TABS[g._kit_tab][1] != 'spells' else []
        if any(it is dagger for _s, it in rows):
            break
        h.key(pygame.K_RIGHT)
    want = next(i for i, (_s, it) in enumerate(rows) if it is dagger)
    while g._kit_sel < want:
        h.key(pygame.K_DOWN)
    h.key('r')
    h.key(pygame.K_ESCAPE)
    assert p.readied_weapon is dagger
    # T: throw it two tiles east, at nothing.
    h.key('t')
    assert g.state == STATE_THROW_MENU
    for _ in range(10):
        if any(i is dagger for i in g._get_throw_tab_items()):
            break
        h.key(pygame.K_RIGHT)
    idx = next(i for i, it in enumerate(g._get_throw_tab_items()) if it is dagger)
    h.key(getattr(pygame, f'K_{chr(97 + idx)}'))
    assert g.state == STATE_TARGET
    h.key(pygame.K_RIGHT)
    h.key(pygame.K_RIGHT)
    h.said()
    h.key(pygame.K_RETURN)
    assert dagger in g.ground_items and (dagger.x, dagger.y) == (p.x + 2, p.y)
    assert f'The {name} clatters to the ground.' in h.said()
    # S: not with him.
    h.key('s')
    assert h.said() == [f'Your {name} is not with you. Pick it up again and S draws it.']
    assert p.weapon is sword
    # Walk over, G picks it up: it is at his back again.
    h.key(pygame.K_RIGHT)
    h.key(pygame.K_RIGHT)
    assert (p.x, p.y) == (dagger.x, dagger.y)
    h.said()
    h.key('g')
    said = h.said()
    assert said[:2] == [f'You pick up the {name}.', f'The {name} is At Your Back again.'], said
    # S: it swaps in.
    h.key('s')
    assert p.weapon is dagger and p.readied_weapon is sword
    assert h.said()[0] == (f'You sling the {g._bare_name(sword)} at your back and draw '
                           f'the {name}.')
