"""Carrying (2026-10-16): worn gear counts, refused past the limit. Plan and
tables: _genart/ui/WEIGHT_PLAN.md; numbers measured with
tools/balance/carry_sim.py.

Weight that bites (Brandon 2026-11-14: "heavy at 50%, burdened at 75%,
overloaded at 100%"; the limit stays a wall): Heavy above half the limit
(half the dodge, footsteps a tile further), Burdened above three quarters
(no dodge, half Dexterity's AC, every second step costs a turn), Overloaded
past the limit itself (no Dexterity AC, every step costs a turn; only lost
Strength, an old save or the Boulder gets there). data/gear_rules.json
`load`. (Burdened 50% / Stressed 75% from 2026-11-13; before that one line.)

Logic tests on Player and on a real headless Game. The FEEL of the tiers
(is the warning seen, is every second step a chore) is a play-test
question: Claude cannot drive Pygame.
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
    assert Player.HEAVY_SHARE == 0.5 and Player.BURDENED_SHARE == 0.75
    assert Player.BURDENED_STEP_EVERY == 2 and Player.OVERLOADED_STEP_EVERY == 1


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
# The three tiers: on and off at each line, with their penalties
# ---------------------------------------------------------------------------

def test_heavy_above_half_burdened_above_three_quarters_overloaded_past_the_limit():
    p = Player()                                      # limit 100
    p.inventory.append(_weight(50))
    assert not p.is_heavy() and p.load_tier() == '' and p.update_burden() is None
    extra = _weight(1)
    p.inventory.append(extra)                         # 51
    assert p.is_heavy() and not p.is_burdened()
    assert p.load_tier() == 'heavy' and p.update_burden() == ('', 'heavy')
    assert p.update_burden() is None                  # said once
    more = _weight(25)
    p.inventory.append(more)                          # 76
    assert p.is_burdened() and p.load_tier() == 'burdened'
    assert p.update_burden() == ('heavy', 'burdened')
    over = _weight(30)
    p.inventory.append(over)                          # 106: only by hand, past the wall
    assert p.is_overloaded() and p.load_tier() == 'overloaded'
    assert p.update_burden() == ('burdened', 'overloaded')
    p.inventory.remove(over)
    p.inventory.remove(more)
    assert p.update_burden() == ('overloaded', 'heavy')
    p.inventory.remove(extra)
    assert p.update_burden() == ('heavy', '')


def test_an_old_saves_stressed_tier_is_told_afresh():
    p = Player()
    p.inventory.append(_weight(80))
    p._load_tier = 'stressed'                         # a 2026-11-13 save's word
    assert p.update_burden() == ('', 'burdened')


def test_strength_moves_the_threshold():
    p = Player()
    p.inventory.append(_weight(52))
    assert p.is_heavy()
    p.apply_stat_bonus('STR', 1)                      # limit 108, line 54
    assert not p.is_heavy()


def test_the_game_says_so_in_title_case():
    g = _game()
    g.player.inventory.append(_weight(60))
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t.startswith("Your load is Heavy.") for t in texts), texts
    g.player.inventory.append(_weight(20))
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t.startswith("You are Burdened. You cannot dodge") for t in texts), texts
    g.player.inventory.append(_weight(30))
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t.startswith("You are Overloaded.") for t in texts), texts
    g.player.inventory.pop()
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t == "You are no longer Overloaded, but you are still Burdened." for t in texts), texts
    g.player.inventory.pop()
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t == "You are no longer Burdened, but your load is still Heavy." for t in texts), texts
    g.player.inventory.pop()
    g._advance_turn()
    texts = _texts(g, 5)
    assert any(t == "Your load is no longer Heavy." for t in texts), texts


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


def test_burdened_costs_every_second_step_overloaded_every_step_heavy_none():
    g = _game()
    assert _walk(g, 8) == 8                           # free: one turn a step
    g.player.inventory.append(_weight(60))
    g._advance_turn()                                 # Heavy: no step costs more
    assert _walk(g, 8) == 8
    g.player.inventory.append(_weight(20))
    g._advance_turn()                                 # Burdened
    assert _walk(g, 8) == 12                          # four of eight cost double
    g.player.inventory.append(_weight(30))
    g._advance_turn()                                 # Overloaded
    assert _walk(g, 8) == 16                          # every step costs double
    for _ in range(3):
        g.player.inventory.pop()
    g._advance_turn()
    assert _walk(g, 8) == 8                           # and it is gone again


def test_the_load_takes_the_dodge_then_dexteritys_ac_but_never_the_clock():
    p = Player()
    p.DEX = 20                                        # +5 to AC in no armour
    before = (p.get_quiz_timer('math'), p.get_quiz_timer_modifier(),
              p.combat_clock(), p.plain_clock())
    ac = p.get_ac()
    dodge = p.dodge_chance()
    assert dodge > 0
    p.inventory.append(_weight(60))
    assert p.load_tier() == 'heavy'
    assert p.dodge_chance() == pytest.approx(dodge / 2)        # half the dodge
    assert p.get_ac() == ac                                    # Dexterity's AC whole
    p.inventory.append(_weight(20))
    assert p.load_tier() == 'burdened'
    assert p.dodge_chance() == 0.0                             # no dodge
    assert p.get_ac() == ac + 5 - 2                            # half of +5, rounded down
    p.inventory.append(_weight(50))                   # past the limit, too
    assert p.is_overloaded() and p.dodge_chance() == 0.0
    assert p.get_ac() == ac + 5                                # none of it
    assert (p.get_quiz_timer('math'), p.get_quiz_timer_modifier(),
            p.combat_clock(), p.plain_clock()) == before


def test_a_clumsy_heros_minus_counts_whatever_the_load():
    p = Player()
    p.DEX = 6                                         # -2 to AC
    ac = p.get_ac()
    p.inventory.append(_weight(80))
    assert p.load_tier() == 'burdened' and p.get_ac() == ac


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
        assert not p.is_heavy(), key
        assert p.get_current_weight() + SUPPLY_ROOM <= p.heavy_threshold(), (
            key, p.get_current_weight(), p.get_carry_limit())


# ---------------------------------------------------------------------------
# The mid-game kits the numbers were chosen for (tools/balance/carry_sim.py)
# ---------------------------------------------------------------------------

def _kits():
    import carry_sim
    return {name: (total, lim) for name, _s, _w, _pk, total, lim
            in carry_sim.kit_rows(Player.CARRY_BASE, Player.CARRY_PER_STR)}


def test_mid_game_kits():
    """Weight that bites: the tiers each kit lands in. Rewritten 2026-11-13
    from the single 75% line, when the typical STR 10 kit and one spare
    suit were both free and plate at STR 18 was comfortable; tiers renamed
    2026-11-14 (Heavy, Burdened, Overloaded), the lines unchanged."""
    k = _kits()

    def tier(name):
        total, lim = k[name]
        if total > lim:
            return 'over'
        if total > lim * Player.BURDENED_SHARE:
            return 'burdened'
        if total > lim * Player.HEAVY_SHARE:
            return 'heavy'
        return ''

    # Free: the early kit, and a low-STR caster in a robe.
    assert tier("Floor 1-5 hero, leather + shield") == ''
    assert tier("STR 6 caster, robe + staff") == ''
    # A typical STR 10 mid kit sits just over half: a spare bow or a lighter
    # helm is the choice; a spare suit is a real decision, not a free one.
    assert tier("STR 10, typical mid kit") == 'heavy'
    assert tier("STR 10, mid kit + 1 spare suit") == 'heavy'
    # Hoarding an armory at STR 10: past the limit (cannot be picked up).
    assert tier("STR 10, mid kit + 2 suits + 4 weapons") == 'over'
    # Plate needs Strength: past the limit at 10, Burdened at 14, and only
    # Heavy (it already has no dodge to halve) for a STR 18-20 warrior.
    assert tier("STR 10, full plate + kite") == 'over'
    assert tier("STR 14, full plate + kite") == 'burdened'
    assert tier("STR 18, full plate + kite") == 'heavy'
    assert tier("STR 20, full plate + tower") == 'heavy'


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
        assert q.is_overloaded() and q.load_tier() == 'overloaded'
        texts = _texts(g2, 6)
        assert any(t.startswith("You are Overloaded.") for t in texts), texts
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
    p.inventory.append(_weight(60))
    assert carry_state(p)[2] == 'Heavy'
    p.inventory.append(_weight(20))
    assert carry_state(p)[2] == 'Burdened'
    p.inventory.append(_weight(30))
    assert carry_state(p)[2] == 'Overloaded'


def test_no_old_wt_readout_left_on_the_screens():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'f"Wt {p.get_current_weight()' not in src
    assert '"Carrying {' in src or 'f"Carrying {' in src
    ui_src = open(os.path.join(ROOT, 'src', 'ui.py'), encoding='utf-8').read()
    assert 'f"Wt {wt' not in ui_src
