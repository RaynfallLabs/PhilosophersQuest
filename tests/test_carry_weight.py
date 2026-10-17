"""Carrying (2026-10-16): worn gear counts, Burdened above 75%, refused past
the limit. Plan and tables: _genart/ui/WEIGHT_PLAN.md; numbers measured with
tools/balance/carry_sim.py.

Logic tests on Player and on a real headless Game. The FEEL of Burdened (is
one extra turn every fourth step mild enough, is the warning seen) is a
play-test question: Claude cannot drive Pygame.
"""
import copy
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pygame
import pytest

pygame.init()

import items
from player import Player

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_carry_weight__', build=None):
    from main import Game
    random.seed(3)
    g = Game(_screen(), player_name=name, secret_build=build)
    g.monsters = []
    g.ground_items = [i for i in g.ground_items
                      if (i.x, i.y) != (g.player.x, g.player.y)]
    g.dungeon.traps = {}
    from game_states import STATE_PLAYER
    g.state = STATE_PLAYER          # past any opening story popup
    return g


def _texts(g, n):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _plain(it):
    it = copy.copy(it)
    it.cursed = False
    it.buc = 'uncursed'
    it.buc_known = True
    it.id_level = 5
    return it


def _weight(lb, cls='weapon'):
    it = _plain(items.instantiate_weapon('longsword', 'iron'))
    it.weight = float(lb)
    return it


# ---------------------------------------------------------------------------
# The numbers
# ---------------------------------------------------------------------------

def test_the_limit_is_twenty_plus_eight_per_strength():
    p = Player()
    assert (p.CARRY_BASE, p.CARRY_PER_STR) == (20, 8)
    assert p.get_carry_limit() == 100                  # STR 10
    p.STR = 18
    assert p.get_carry_limit() == 164
    assert Player.BURDENED_SHARE == 0.75 and Player.BURDEN_STEP_EVERY == 4


def test_item_weights_were_not_compressed():
    """The limit moved, the items did not: plate is still 65 lb."""
    tpl = items.load_templates('armor')
    assert tpl['full_plate']['base_weight_lb'] == 65.0
    assert items.load_templates('shields')['tower_shield']['base_weight_lb'] == 30.0


# ---------------------------------------------------------------------------
# Worn gear counts; equipping moves weight, never changes the total
# ---------------------------------------------------------------------------

def test_worn_gear_counts_toward_the_load():
    p = Player()
    plate = _plain(items.instantiate_armor('full_plate', 'chain_steel'))
    p._apply_equip(plate)
    assert plate not in p.inventory
    assert p.get_worn_weight() == pytest.approx(65.0)
    assert p.get_current_weight() == pytest.approx(65.0)


def test_equip_and_unequip_leave_the_total_unchanged_on_the_player():
    p = Player()
    a = _plain(items.instantiate_armor('chain_shirt', 'chain_steel'))
    b = _plain(items.instantiate_armor('scale', 'chain_steel'))
    p.inventory.extend([a, b])
    total = p.get_current_weight()
    p._apply_equip(a)
    p.inventory.remove(a)
    assert p.get_current_weight() == pytest.approx(total)
    p._apply_equip(b)                 # swap: a goes back to the pack
    p.inventory.remove(b)
    assert a in p.inventory
    assert p.get_current_weight() == pytest.approx(total)


def test_an_item_both_worn_and_listed_in_the_pack_counts_once():
    """_equip_item puts a weapon on, then takes it out of the pack: for that
    moment it is in both places."""
    p = Player()
    w = _weight(6)
    p.inventory.append(w)
    p._apply_equip(w)
    assert p.get_current_weight() == pytest.approx(6.0)


def test_equip_and_unequip_through_the_game_keep_the_total():
    g = _game()
    p = g.player
    w = _plain(items.instantiate_weapon('battleaxe', 'iron'))
    p.inventory.append(w)
    total = p.get_current_weight()
    g._equip_item(w)
    assert p.weapon is w
    assert p.get_current_weight() == pytest.approx(total)
    g._unequip_slot('weapon', w)
    assert w in p.inventory and p.weapon is None
    assert p.get_current_weight() == pytest.approx(total)


# ---------------------------------------------------------------------------
# Burdened: on and off at the threshold, with its penalty
# ---------------------------------------------------------------------------

def test_burdened_turns_on_above_three_quarters_and_off_again():
    p = Player()                                      # limit 100
    p.inventory.append(_weight(75))
    assert not p.is_burdened() and p.update_burden() is None
    extra = _weight(1)
    p.inventory.append(extra)
    assert p.is_burdened() and p.update_burden() == 'on'
    assert p.update_burden() is None                  # said once
    p.inventory.remove(extra)
    assert p.update_burden() == 'off'


def test_strength_moves_the_threshold():
    p = Player()
    p.inventory.append(_weight(80))
    assert p.is_burdened()
    p.apply_stat_bonus('STR', 1)                      # limit 108, threshold 81
    assert not p.is_burdened()


def test_the_game_says_so_in_title_case():
    g = _game()
    g.player.inventory.append(_weight(80))
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t.startswith("You are Burdened.") for t in texts), texts
    g.player.inventory.pop()
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t == "You are no longer Burdened." for t in texts), texts


def _open_step(g):
    """A direction the player can walk to and back from."""
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if g.dungeon.is_walkable(px + dx, py + dy):
            return dx, dy
    raise AssertionError("no open tile beside the start")


def _walk(g, n):
    dx, dy = _open_step(g)
    start = g.turn_count
    for i in range(n):
        if i % 2 == 0:
            g._do_move(dx, dy)
        else:
            g._do_move(-dx, -dy)
    return g.turn_count - start


def test_burdened_steps_cost_an_extra_turn_every_fourth_step():
    g = _game()
    assert _walk(g, 8) == 8                           # free: one turn a step
    g.player.inventory.append(_weight(80))
    g._advance_turn()                                 # notices the load
    assert _walk(g, 8) == 10                          # two of eight cost double
    g.player.inventory.pop()
    g._advance_turn()
    assert _walk(g, 8) == 8                           # and it is gone again


def test_burdened_does_not_touch_the_quiz_clock_or_the_fight():
    p = Player()
    before = (p.get_quiz_timer('math'), p.get_quiz_timer_modifier(),
              p.combat_clock(), p.plain_clock(), p.get_ac(), p.dodge_chance())
    p.inventory.append(_weight(99))
    assert p.is_burdened()
    after = (p.get_quiz_timer('math'), p.get_quiz_timer_modifier(),
             p.combat_clock(), p.plain_clock(), p.get_ac(), p.dodge_chance())
    assert before == after
    p.inventory.append(_weight(50))                   # past the limit, too
    assert p.is_overloaded()
    assert (p.get_quiz_timer('math'), p.get_quiz_timer_modifier(),
            p.combat_clock(), p.plain_clock(), p.get_ac(), p.dodge_chance()) == before


# ---------------------------------------------------------------------------
# Pickups past the limit are refused, and say why
# ---------------------------------------------------------------------------

def test_pickup_is_refused_past_the_limit():
    p = Player()
    p._apply_equip(_plain(items.instantiate_armor('full_plate', 'chain_steel')))   # 65
    assert p.add_to_inventory(_weight(35))            # exactly 100: allowed
    assert not p.add_to_inventory(_weight(1))         # 101: refused


def test_floor_pickup_says_plainly_why():
    g = _game()
    heavy = _weight(150)
    heavy.x, heavy.y = g.player.x, g.player.y
    g.ground_items.append(heavy)
    g._pickup()
    assert heavy in g.ground_items and heavy not in g.player.inventory
    texts = _texts(g, 3)
    assert "Too heavy: that would put you over your limit of 100." in texts


def test_take_and_equip_counts_what_is_already_worn():
    g = _game()
    p = g.player
    p._apply_equip(_plain(items.instantiate_armor('full_plate', 'chain_steel')))   # 65 worn
    shield = _plain(items.instantiate_shield('tower_shield', 'chain_steel'))       # 30
    shield.x, shield.y = p.x, p.y
    g.ground_items.append(shield)
    acts = {a['id']: a for a in g._item_actions(shield, 'floor')}
    assert acts['equip']['enabled']                   # 95 of 100
    p.inventory.append(_weight(10))
    acts = {a['id']: a for a in g._item_actions(shield, 'floor')}
    assert not acts['equip']['enabled']
    assert acts['equip']['why'] == "Too heavy for your limit of 100"


def test_the_boulder_is_taken_up_whatever_the_load():
    """Sisyphus' Boulder can always be taken up, even past the limit (its
    trial is to carry it, whatever else the hero carries)."""
    from mystery_system import MysteryKeyItem
    p = Player()
    p.inventory.append(_weight(95))
    boulder = MysteryKeyItem('sisyphus', "The Boulder", '*', (140, 140, 140), 20.0)
    assert p.add_to_inventory(boulder)
    assert p.is_overloaded()
    other = MysteryKeyItem('brendan', "Oar", '/', (1, 1, 1), 20.0)
    assert not p.add_to_inventory(other)


def test_a_reward_too_heavy_to_carry_is_set_at_the_heros_feet():
    g = _game()
    g.player.inventory.append(_weight(100))
    prize = _weight(5)
    assert g._give_item(prize) is False
    assert prize in g.ground_items
    assert (prize.x, prize.y) == (g.player.x, g.player.y)


# ---------------------------------------------------------------------------
# Every starting build begins unburdened, with room for supplies
# ---------------------------------------------------------------------------

SUPPLY_ROOM = 10.0      # carry_sim.SUPPLIES: potions, scrolls, food, wands...


def test_every_starting_build_starts_unburdened_with_room_for_supplies():
    import welcome_screen
    builds = [('adventurer', None)] + sorted(welcome_screen.SECRET_BUILDS.items())
    for key, b in builds:
        g = _game(name=key, build=b)
        p = g.player
        assert not p.is_burdened(), key
        assert p.get_current_weight() + SUPPLY_ROOM <= p.burden_threshold(), (
            key, p.get_current_weight(), p.get_carry_limit())


# ---------------------------------------------------------------------------
# The mid-game kits the numbers were chosen for (tools/balance/carry_sim.py)
# ---------------------------------------------------------------------------

def _kits():
    import carry_sim
    return {name: (total, lim) for name, _s, _w, _pk, total, lim
            in carry_sim.kit_rows(Player.CARRY_BASE, Player.CARRY_PER_STR)}


def test_mid_game_kits():
    k = _kits()
    share = Player.BURDENED_SHARE

    def free(name):
        total, lim = k[name]
        return total <= lim * share

    # Comfortable: early kit, typical STR 10 kit, even with one spare suit.
    assert free("Floor 1-5 hero, leather + shield")
    assert free("STR 10, typical mid kit")
    assert free("STR 10, mid kit + 1 spare suit")
    # Hoarding an armory at STR 10: past the limit (cannot be picked up).
    total, lim = k["STR 10, mid kit + 2 suits + 4 weapons"]
    assert total > lim
    # Plate needs Strength: past the limit at 10, Burdened at 14 ...
    total, lim = k["STR 10, full plate + kite"]
    assert total > lim
    assert not free("STR 14, full plate + kite")
    # ... and comfortable for a STR 18-20 warrior, tower shield and all.
    assert free("STR 18, full plate + kite")
    assert free("STR 20, full plate + tower")
    # A low-STR caster in a robe is fine.
    assert free("STR 6 caster, robe + staff")


# ---------------------------------------------------------------------------
# Old saves: worn gear did not count before; such a save may now be heavy
# ---------------------------------------------------------------------------

def test_an_old_save_over_the_limit_loads_burdened_and_can_drop():
    from save_system import save_game, load_game, delete_save
    name = '__test_carry_old_save__'
    g = _game(name=name)
    p = g.player
    p._apply_equip(_plain(items.instantiate_armor('full_plate', 'chain_steel')))
    p._apply_equip(_plain(items.instantiate_shield('tower_shield', 'chain_steel')))
    spare = _weight(20)
    p.inventory.append(spare)
    for attr in ('_burdened', '_burden_steps'):           # what an old save lacks
        p.__dict__.pop(attr, None)
    assert p.is_overloaded()                              # 115+ of 100
    try:
        assert save_game(g)
        state = load_game(name)
        assert state is not None
        g2 = _game(name=name)
        g2.load_state(state)
        q = g2.player
        assert q.is_overloaded() and q.is_burdened()
        texts = _texts(g2, 6)
        assert any(t.startswith("You are Burdened.") for t in texts), texts
        # It can still drop things and walk.
        held = next(i for i in q.inventory if getattr(i, 'weight', 0) == 20)
        g2.monsters = []
        g2._do_drop_item(held)
        assert held not in q.inventory
        g2._advance_turn()
    finally:
        delete_save(name)


# ---------------------------------------------------------------------------
# What the player reads
# ---------------------------------------------------------------------------

def test_readout_says_carrying_and_burdened():
    from ui import carry_state
    p = Player()
    assert p.carry_line() == "Carrying 0 / 100"
    assert carry_state(p) == (0.0, 100, '')
    p.inventory.append(_weight(80))
    assert carry_state(p)[2] == 'Burdened'
    p.inventory.append(_weight(30))
    assert carry_state(p)[2] == 'Over Limit'


def test_no_old_wt_readout_left_on_the_screens():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'f"Wt {p.get_current_weight()' not in src
    assert '"Carrying {' in src or 'f"Carrying {' in src
    ui_src = open(os.path.join(ROOT, 'src', 'ui.py'), encoding='utf-8').read()
    assert 'f"Wt {wt' not in ui_src
