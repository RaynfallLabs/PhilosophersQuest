"""Bug bash 3.5.1, hunter A: the kitchen rebuild of 3.5.0.

Each test pins one finding of A_report.md (the kitchen: harvest, the cook
menu's words, what a dish gives, cook to carry, the boss trophies). Real
keys drive a headless Game where the path has keys; the rest drives
src/kitchen.py and src/food_system.py on a real Player. Whether the menu
reads well to a kid is Brandon's play-test: Claude cannot drive Pygame.
"""
import copy
import os
import pickle
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), os.path.join(ROOT, 'tests')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

import kitchen  # noqa: E402
from test_bug_bash_5_encounters import _game  # noqa: E402

pygame.init()


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _right_answer(g):
    """Every quiz answered right, at once (the harvest and the cook)."""
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))


def _player(deepest=10):
    from player import Player
    p = Player()
    p.deepest_floor_reached = deepest
    return p


def _ing(iid, n=1):
    from food_system import load_ingredient_for
    it = load_ingredient_for(iid)
    it.count = n
    return it


def _harvest(g, monster):
    from food_system import make_corpse
    from game_states import STATE_PLAYER
    px, py = g.player.x, g.player.y
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (px, py)]
    g.ground_items.append(make_corpse(monster, px, py))
    g.state = STATE_PLAYER
    _press(g, pygame.K_h, 'h')


def _held(g, iid):
    return kitchen.held_counts(g.player.inventory).get(iid, 0)


# ---------------------------------------------------------------------------
# A1. Hunter's Harvest gave a second boss trophy, and its power twice.
# ---------------------------------------------------------------------------

def test_a1_hunters_harvest_never_doubles_a_boss_trophy():
    """Great beasts tier 3 (Hunter's Harvest) gave one more portion of
    every great beast's corpse, Fenrir's included: two of Fenrir's Tooth,
    and its +3 STR twice (STR 10 to 17 in two meals), past every cap. A
    trophy is one of a kind; an ordinary great beast still gives two."""
    import family_lore
    g = _game()
    g.monsters = []
    _right_answer(g)
    p = g.player
    p.studied_monster_ids = set(family_lore.members('great_beasts'))
    assert family_lore.tier(p, 'great_beasts') >= 3
    _harvest(g, 'fenrir_wolf')
    assert _held(g, 'fenrir_wolf_trophy') == 1
    last = str(g.msg_log.entries[-1][0])
    assert "Hunter's Harvest" not in last, last
    # An ordinary great beast: the extra portion still comes.
    _harvest(g, 'dire_lion')
    assert _held(g, 'dire_lion_prime') == 2


# ---------------------------------------------------------------------------
# A2. The cook menu promised max HP the lifetime cap would not give.
# ---------------------------------------------------------------------------

def _max_hp_lines(lines):
    return [ln for ln in lines if 'Max HP' in ln]


def test_a2_menu_max_hp_reads_the_lifetime_cap_too():
    """Max HP from cooking stops at 4 a floor reached (cooking_softcap),
    and the floor's cap (5) is more than that: a hero who cooks every floor
    sits at the lifetime cap from about floor 4 on. The menu read only the
    floor's cap and said "+5 Max HP" to a hero who then got nothing, and the
    meal blamed the floor. It says what the meal will really give now."""
    p = _player(deepest=5)
    p.cooking_hp_gained = p.cooking_softcap()            # the depth's cap is full
    dish = kitchen.recipe('cook_troll')                  # an HP dish
    lines = kitchen.dish_effects(p, dish)
    assert _max_hp_lines(lines) == ['Max HP: all cooking can give at this depth'], lines
    before = p.max_hp
    msgs = kitchen.apply_dish(p, dish)
    assert p.max_hp == before
    assert any('at this depth' in m for m in msgs), msgs
    assert not any('this floor' in m for m in msgs), msgs
    # Two points of room left: the menu says +2, the meal gives 2.
    p = _player(deepest=5)
    p.cooking_hp_gained = p.cooking_softcap() - 2
    lines = kitchen.dish_effects(p, dish)
    assert '+2 Max HP' in lines, lines
    before = p.max_hp
    kitchen.apply_dish(p, dish)
    assert p.max_hp - before == 2
    # The floor's cap still reads as the floor's.
    p = _player(deepest=30)
    p._cook_hp_gain_this_floor = p.PER_FLOOR_HP_CAP
    assert 'Max HP full this floor' in kitchen.dish_effects(p, dish)


def test_a2_a_feasts_max_hp_for_good_is_what_the_feast_gives():
    """Sigurd's Hearth Roast said "+8 Max HP for good" with one point of
    the lifetime cap left, and gave 1."""
    feast = kitchen.recipe('feast_05')
    for left in (0, 1, 3, 30):
        p = _player(deepest=60)
        p.cooking_hp_gained = p.cooking_softcap() - left
        p._cook_hp_gain_this_floor = p.PER_FLOOR_HP_CAP     # the floor's share already cooked
        lasting = kitchen.dish_lasting(p, feast)
        assert all(line in kitchen.dish_effects(p, feast) for line in lasting)
        before = p.max_hp
        kitchen.apply_dish(p, feast)
        got = p.max_hp - before
        assert got == min(left, 8)
        want = f"+{got} Max HP for good" if got else "No more Max HP for good at this depth"
        assert want in lasting, (left, lasting)
    # The meal's own max HP lands first, inside the same lifetime cap.
    p = _player(deepest=60)
    p.cooking_hp_gained = p.cooking_softcap() - 6
    first = min(kitchen.dish_outcome(feast)['max_hp'], p.PER_FLOOR_HP_CAP, 6)
    assert f"+{first} Max HP" in kitchen.dish_effects(p, feast)
    assert kitchen.dish_lasting(p, feast)[0] == f"+{6 - first} Max HP for good"
    before = p.max_hp
    kitchen.apply_dish(p, feast)
    assert p.max_hp - before == 6


# ---------------------------------------------------------------------------
# A3. A legendary stat feast promised a point the stat's cap would not give.
# ---------------------------------------------------------------------------

def test_a3_a_stat_feasts_point_for_good_reads_the_stats_cap():
    feast = kitchen.recipe('feast_29')                   # First Seal Wrath Feast (STR)
    assert kitchen.dish_outcome(feast)['permanent'] == ('stat', 1)
    # At the cap: nothing, and the menu says so.
    p = _player(deepest=1)
    p.cooking_stat_gained['STR'] = p.cooking_stat_softcap('STR')
    lasting = kitchen.dish_lasting(p, feast)
    assert lasting == ['No more STR for good at this depth'], lasting
    before = p.STR
    kitchen.apply_dish(p, feast)
    assert p.STR == before
    # One point of room: the lesson (a full point) takes it, the feast's
    # lasting point has none left.
    p = _player(deepest=1)
    p.cooking_stat_gained['STR'] = p.cooking_stat_softcap('STR') - 1
    assert kitchen.dish_lasting(p, feast) == ['No more STR for good at this depth']
    before = p.STR
    kitchen.apply_dish(p, feast)
    assert p.STR == before + 1
    # The lesson used this floor: the lasting point still comes.
    p = _player(deepest=40)
    p._cook_stat_gain_this_floor = p.PER_FLOOR_STAT_CAP
    assert kitchen.dish_lasting(p, feast) == ['+1 STR for good']
    before = p.STR
    kitchen.apply_dish(p, feast)
    assert p.STR == before + 1
    # Room for both: the lesson's point and the lasting one.
    p = _player(deepest=40)
    assert kitchen.dish_lasting(p, feast) == ['+1 STR for good']
    before = p.STR
    kitchen.apply_dish(p, feast)
    assert p.STR == before + 2


# ---------------------------------------------------------------------------
# A4. Four boss trophies said they did more than they do.
# ---------------------------------------------------------------------------

def test_a4_trophy_words_say_what_the_power_does():
    """Surtur's coal said "ZERO fire damage from any source" and Ymir's
    marrow "ZERO cold damage": both give the resistance, which halves (it
    stopped being an immunity in 2026-10). Nidhoggr's scale said "immunity
    to poison" (poison cannot take hold, and does half). Tiamat's tear
    said 25% in the Kit and "each hurt 3 less" when eaten: it is three
    levels of the chain resistance, about a fifth less a hit."""
    from food_system import _apply_permanent_power
    ings = kitchen.ingredients()
    for tid in ('surtur_trophy', 'ymir_last_spawn_trophy', 'nidhoggr_fragment_trophy',
                'tiamat_trophy'):
        text = ings[tid]['description']
        assert 'ZERO' not in text and 'immunity' not in text and '25%' not in text, (tid, text)
    assert 'half damage' in ings['surtur_trophy']['description']
    assert 'half damage' in ings['ymir_last_spawn_trophy']['description']
    assert 'a fifth less' in ings['tiamat_trophy']['description']
    # Tiamat: about a fifth less, as said.
    p = _player(deepest=90)
    p.max_hp = p.hp = 10_000
    before = p.take_damage(100, 'fire')
    p.hp = p.max_hp
    line = _apply_permanent_power(p, 'chromatic_resist_all', {})
    after = p.take_damage(100, 'fire')
    assert 'a fifth less' in line and '3 less' not in line
    assert 0.74 <= after / before <= 0.82, (before, after)
    # Surtur: half, not none.
    p = _player(deepest=90)
    p.max_hp = p.hp = 10_000
    before = p.take_damage(100, 'fire')
    p.hp = p.max_hp
    _apply_permanent_power(p, 'fire_immunity', {})
    after = p.take_damage(100, 'fire')
    assert 0 < after < before


# ---------------------------------------------------------------------------
# A5. A trader bought the Mooble's tart (and the Scroll of Death's Bane).
# ---------------------------------------------------------------------------

def test_a5_a_trader_never_buys_a_withheld_piece():
    """The docs and items.WITHHELD_IDS say the Starnut Tart is never
    stolen, given as payment or sold; a trader who buys food bought it.
    The Scroll of Death's Bane, which the secret ending reads, sold too:
    the Game's list named it "death_bane", not its id. The real sell
    screen's offer says "Not for sale" now."""
    import traders
    from items import make_death_bane_scroll, make_item_by_id
    g = _game()
    tart = make_item_by_id('food', 'starnut_tart')
    scroll = make_death_bane_scroll(0, 0)
    bread = make_item_by_id('food', 'bread_ration')
    for it in (tart, scroll):
        assert traders.is_quest_piece(it, g._QUEST_PIECE_IDS), it.id
        assert traders.refusal({'buys': 'all'}, it, known=True, cursed_known=False,
                               quest_ids=g._QUEST_PIECE_IDS) == 'Not for sale'
    # Food that is only food still sells.
    assert traders.refusal({'buys': ['food']}, bread, known=True, cursed_known=False,
                           quest_ids=g._QUEST_PIECE_IDS) is None
    # Through the trader's own offer, as the Sell screen asks it.
    g._shop_merchant = types.SimpleNamespace(
        buys=['food', 'scroll'], buys_cursed=False, markup=1.0, purse=10_000,
        person='Old Mags', pronouns=lambda: ('she', 'her', 'her'))
    assert g._trader_offer(tart) == (0, 'Not for sale')
    offer, why = g._trader_offer(bread)
    assert why is None and offer > 0
