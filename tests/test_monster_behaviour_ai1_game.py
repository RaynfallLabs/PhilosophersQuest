"""Monster behaviour, first wave (AI-1): the Game's side, on a real Game.

The behaviours are pure modules (tests/test_monster_behaviour_ai1.py);
these are the few things the Game does for them (game_behaviour.py): the
lines said as the hero sees or hears them, the burst of a dying creature
(and the one it kills, after it), the shove that moves the hero, the purse a
yielding bandit throws down, the summoned marked as the summoner's own, and
the help page that tells of them.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_ai1__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(mid, x=0, y=0):
    from monster import Monster
    return Monster({**MONS[mid], 'id': mid}, x, y)


def _scene(*placed, seed=7):
    """A game with the hero in an open spot and ``placed`` = (kind, dx, dy)."""
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.monsters = [_monster(k, x + dx, y + dy) for k, dx, dy in placed]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return g


def _messages(g, n=20):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def test_a_fire_beetle_bursts_on_the_hero_and_a_neighbour_bursts_after_it():
    # (a second fire beetle would shrug off the fire: a gas spore does not)
    g = _scene(('fire_beetle', 1, 0), ('gas_spore', 2, 0))
    first, second = g.monsters
    second.hp = 1
    hp0 = g.player.hp
    first.hp = 0
    first.alive = False
    g._on_monster_killed(first)
    assert g.player.hp < hp0
    assert not second.alive and second.__dict__.get('_throes_done')
    text = ' '.join(_messages(g))
    assert 'spray of fire' in text and 'blast catches you' in text


def test_a_banished_creature_does_not_burst():
    g = _scene(('fire_beetle', 1, 0))
    b = g.monsters[0]
    b._banished = True
    b.hp = 0
    b.alive = False
    hp0 = g.player.hp
    g._on_monster_killed(b)
    assert g.player.hp == hp0


def test_a_shove_throws_the_hero_one_tile_back():
    g = _scene(('hill_giant', -1, 0))
    x0, y0 = g.player.x, g.player.y
    g.player._pending_shove = {'from': (x0 - 1, y0), 'aim': False,
                               'line': 'Thrown!', 'aimed': 'Thrown hard!'}
    g._ai_resolve_shove()
    assert (g.player.x, g.player.y) == (x0 + 1, y0)
    assert 'Thrown!' in _messages(g)


def test_a_shove_never_throws_the_hero_into_water():
    from dungeon import WATER
    g = _scene(('hill_giant', -1, 0))
    x0, y0 = g.player.x, g.player.y
    for dy in (-1, 0, 1):
        g.dungeon.tiles[y0 + dy][x0 + 1] = WATER
    g.player._pending_shove = {'from': (x0 - 1, y0), 'aim': True, 'line': 'x', 'aimed': 'y'}
    g._ai_resolve_shove()
    assert (g.player.x, g.player.y) == (x0, y0)


def test_a_yielding_bandit_throws_down_his_purse_once():
    g = _scene(('bandit_thug', 1, 0))
    b = g.monsters[0]
    b.treasure = {'gold': [20, 20], 'item_chance': 0.0, 'item_tier': 1}
    import morale
    morale.give_up(b)
    g._ai_turn_after(b)
    assert b.treasure['gold'] == [0, 0]
    from items import GoldPile
    gold = sum(it.amount for it in g.ground_items
               if isinstance(it, GoldPile) and (it.x, it.y) == (b.x, b.y))
    assert gold == 20
    assert any('begs for' in t for t in _messages(g))


def test_lines_are_said_as_seen_or_heard():
    import ai_lines
    g = _scene(('kobold', 2, 0))
    k = g.monsters[0]
    ai_lines.say(k, 'The Kobold yaps a warning!', 'Somewhere ahead, a shrill yapping.')
    g._ai_turn_after(k)
    assert 'The Kobold yaps a warning!' in _messages(g)
    g.visible = set()
    ai_lines.say(k, 'The Kobold yaps a warning!', 'Somewhere ahead, a shrill yapping.')
    g._ai_turn_after(k)
    assert _messages(g)[-1] == 'Somewhere ahead, a shrill yapping.'


def test_a_summoners_minion_is_marked_his():
    g = _scene(('skeleton_necromancer', 3, 0))
    s = g.monsters[0]
    g._spawn_summoner_minion(s)
    minions = [m for m in g.monsters if m is not s]
    assert minions and all(m.__dict__.get('_summoned_by') is s for m in minions)


def test_the_monster_ways_help_page_draws():
    g = _game()
    g.screen = _screen()
    assert g.help_page_count() == 4
    assert g._help_page_title(3) == 'Monsters and Their Ways'
    g._help_page = 3
    g._draw_help_screen()


# ===========================================================================
# After the audit (_mm_2026_11_19/AI1/AUDIT.md): the Game's side
# ===========================================================================

def test_d1_a_yielded_thug_in_a_pit_strikes_nobody():
    g = _scene(('bandit_thug', 1, 0))
    b = g.monsters[0]
    import morale
    morale.give_up(b)
    g._ai_turn_after(b)
    b.status_effects['stuck_in_pit'] = 5
    hp0 = g.player.hp
    for _ in range(4):
        g._do_monster_turns()
    assert g.player.hp == hp0
    assert not any('hits you' in t for t in _messages(g))


def test_d5_a_band_routs_when_its_captain_yields():
    g = _scene(('mercenary_veteran', 2, 0), ('bandit_thug', 2, 1))
    lead, f = g.monsters
    lead._band = 'b1'
    lead._band_role = 'leader'
    lead._band_id = 'bandit_crew'
    f._band = 'b1'
    f._band_role = 'guard'
    f._band_leader = lead
    import morale
    morale.give_up(lead)
    g._ai_turn_after(lead)
    assert f.__dict__.get('_band_leader') is None
    # A morale test, not fear for all (war_bands.leader_falls, 2026-11-22):
    # he broke his own way, held, or took up the lead himself; the captain
    # who begs leads no one.
    import war_bands
    assert not f.has_effect('feared')
    assert lead._band_role != 'leader'
    assert (int(f._flee_timer or 0) > 0 or f.__dict__.get('_took_lead')
            or not war_bands.holds_nerve(f))


def test_d7_a_pet_leaves_a_begging_foe_alone():
    from pet_system import Pet, random_species
    g = _scene(('bandit_thug', 1, 0))
    b = g.monsters[0]
    pet = Pet(random_species(), b.x, b.y + 1)
    import morale
    morale.give_up(b)
    act = pet.take_turn(g.player, g.dungeon, g.monsters, [pet])
    assert not (act and act[0] == 'attack' and act[1] is b)


def test_d8_filling_a_soaked_lantern_does_not_light_it():
    import items
    g = _scene()
    lantern = items.make_item_by_id('light', 'horn_lantern')
    lantern.lit = False
    lantern.fuel = 10
    lantern._wet = 3
    g.player.shield = lantern
    flask = next((i for i in items.load_items('flask') if 'oil' in str(getattr(i, 'id', ''))), None)
    if flask is None:
        return
    g.player.inventory.append(flask)
    g._fill_light(lantern)
    assert not lantern.lit
    assert any('soaked' in t for t in _messages(g))


def test_the_mandrakes_death_cry_rouses_the_floor_near_it():
    g = _scene(('mandrake', 2, 0), ('goblin', 2, 3))
    mand, gob = g.monsters
    gob._aware = False
    gob._tracking = False
    mand._aware = True
    mand.hp = 0
    mand.alive = False
    g._on_monster_killed(mand)
    assert gob._aware
    assert any('shrieks as it dies' in t for t in _messages(g))


def test_a_young_dragon_in_reach_rakes_and_bites_while_it_draws_breath():
    """The breath retune (src/breath.py routine()) through the game's own
    monster turns: the claw and bite land together, the breath never with them."""
    import breath
    g = _scene(('young_dragon', 1, 0))
    d = g.monsters[0]
    d._aware = d._tracking = d._opened = True
    g.player.max_hp = g.player.hp = 100000
    fire = next(a for a in d.attacks if a['delivery'] == 'breath')
    breath.spend(d, fire)
    for _ in range(2):
        g._do_monster_turns()
    text = ' '.join(_messages(g, 40))
    assert 'attacks in a frenzy' in text
    assert 'fire breath' not in text.lower()
