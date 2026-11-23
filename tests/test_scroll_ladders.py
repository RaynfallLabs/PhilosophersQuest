"""Every scroll is worth reading (2026-11-22).

Brandon, play-testing 3.6.1: "I still think you either didn't update the
light spell or you didn't update the mechanics data... it says it lights up
around you, but I thought I'd said to make it create a light that follows
you for some significant number of turns; other scrolls like this need to
be tweaked too so they are actually useful, like Mapping (only did a tiny
bit around you, not useful), and identify (identifies all items in
inventory, maybe?)".

* The light scrolls lay the light status that goes with the hero, for
  hundreds of turns, brighter by tier (lights.kindle, status_glow,
  glow_tick); they no longer map the floor.
* Mapping maps a real part of the floor at tier 1 (35 tiles round, about
  half a floor), the whole floor from tier 3, and the deeper charts find
  the hidden doors and the traps.
* Identify names a whole sort at tier 1, everything carried from tier 2,
  then what lies in sight and on the floor, then the corpses' lore.
* The numbers are each kind's own (data/items/scroll.json), read by the
  handler and the card alike (wards.field_of), so the two cannot drift.

Headless: how the light looks and how the identify picker feels at the keys
is Brandon's play-test.
"""
import json
import os
import random
import re
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import item_words  # noqa: E402
import lights  # noqa: E402
import wards  # noqa: E402
from game_states import STATE_IDENTIFY_MENU, STATE_PLAYER  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'items', 'scroll.json'), encoding='utf-8') as _f:
    SCROLLS = json.load(_f)
with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    KINDS = json.load(_f)


def _kinds(effect):
    """The spawnable kinds of one effect, by tier."""
    return sorted((v['tier'], k) for k, v in SCROLLS.items()
                  if v.get('effect') == effect and int(v.get('min_level', 0)) < 9999)


def _item(sid, buc='uncursed'):
    it = items.make_item_by_id('scroll', sid)
    it.buc = buc
    return it


def _n(text, after):
    m = re.search(re.escape(after) + r'\s*\+?(\d+)', text, re.I)
    assert m, (after, text)
    return int(m.group(1))


def _line(sid, buc='uncursed', player=None):
    return item_words.what_it_does(_item(sid, buc), player, buc_known=buc != 'uncursed')[0]


# --------------------------------------------------------------- the game

@pytest.fixture
def g(monkeypatch, tmp_path):
    import main
    import paths
    import seeker_profile
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(paths, '_DEV_SAVE_DIR_OVERRIDE', str(tmp_path), raising=False)
    monkeypatch.setattr(seeker_profile, '_DIR_OVERRIDE', str(tmp_path / 'seekers'), raising=False)
    random.seed(11)
    items.bind_unique_registry(set())
    game = main.Game(pygame.display.set_mode((1280, 720)), player_name='__scroll_ladders__')
    from dungeon import FLOOR
    game.monsters[:] = []
    game.pets = []
    game.ground_items[:] = []
    game._maybe_wander_spawn = lambda: None
    game._popup_queue_list().clear()
    game.state = STATE_PLAYER
    d, p = game.dungeon, game.player
    x, y = d.width // 2, d.height // 2
    for i in range(-8, 9):
        for j in range(-8, 9):
            d.tiles[y + j][x + i] = FLOOR
            d.traps.pop((x + i, y + j), None)
            (d.__dict__.get('fixtures') or {}).pop((x + i, y + j), None)
    p.x, p.y = x, y
    p.inventory = []
    p.status_effects.clear()
    if lights.is_light(p.shield):
        p.shield = None
    p.max_hp = p.hp = 500
    game._refresh_fov()
    game.said = []
    game.add_message = lambda text, *a, **k: game.said.append(str(text))
    return game


# ------------------------------------------------- the light: pure rules

def test_kindle_lays_the_light_status_at_its_brightness():
    p = Player()
    p.status_effects.clear()
    assert lights.status_glow(p) == (0, 0)
    got = lights.kindle(p, 500, 5)
    assert got == 500 and p.status_effects['light'] == 500
    assert lights.status_glow(p) == (5, 5)
    assert lights.light_bonus(p) == 5 and lights.shine(p) == 5
    # A light no brighter than the spell's is the status's own.
    q = Player()
    q.status_effects.clear()
    lights.kindle(q, 500, lights.status_sight())
    assert lights.status_glow(q) == (lights.status_sight(), lights.status_notice())


def test_a_brighter_glow_lasts_its_own_turns_and_the_spell_cannot_stretch_it():
    p = Player()
    p.status_effects.clear()
    lights.kindle(p, 10, 5)
    p.add_effect('light', 100, cap=lights.spell_cap())       # the Light spell cast on top
    assert p.status_effects['light'] == 110
    for _ in range(9):
        lights.glow_tick(p)
    assert lights.status_glow(p)[0] == 5
    lights.glow_tick(p)
    # Its own ten turns are spent: the spell's light burns on at the spell's sight.
    assert lights.status_glow(p) == (lights.status_sight(), lights.status_notice())
    assert p.has_effect('light')


def test_only_the_brightest_glow_counts_and_the_dimmer_comes_back():
    p = Player()
    p.status_effects.clear()
    lights.kindle(p, 100, 4)
    lights.kindle(p, 20, 5)
    assert lights.status_glow(p)[0] == 5
    for _ in range(20):
        lights.glow_tick(p)
    assert lights.status_glow(p)[0] == 4
    for _ in range(80):
        lights.glow_tick(p)
    assert lights.status_glow(p)[0] == lights.status_sight()


def test_a_glow_goes_with_its_light():
    p = Player()
    p.status_effects.clear()
    lights.kindle(p, 300, 5)
    p.status_effects.pop('light')                     # a darkness put it out
    assert lights.status_glow(p) == (0, 0) and lights.light_bonus(p) == 0
    lights.glow_tick(p)
    lights.kindle(p, 50, lights.status_sight())        # a new, plain light
    assert lights.status_glow(p)[0] == lights.status_sight()     # no stale glow


# ------------------------------------------------- the light: the handler

LIGHT_KINDS = _kinds('full_light')


def test_the_light_scrolls_climb_with_their_tier_and_outlast_the_spell():
    assert [t for t, _ in LIGHT_KINDS] == [1, 3, 5]
    turns = [SCROLLS[k]['light_turns'] for _, k in LIGHT_KINDS]
    sights = [SCROLLS[k]['light_sight'] for _, k in LIGHT_KINDS]
    assert turns == sorted(turns) and len(set(turns)) == len(turns)
    assert sights == sorted(sights) and sights[0] >= lights.status_sight() and sights[-1] > sights[0]
    for _, k in LIGHT_KINDS:
        # Spent once: it burns far longer than the spell's longest light.
        assert SCROLLS[k]['light_turns'] >= 2 * lights.spell_cap(), k
        assert SCROLLS[k]['light_turns_blessed'] > SCROLLS[k]['light_turns'], k
        assert 'map_radius' not in SCROLLS[k], k


@pytest.mark.parametrize('sid', [k for _, k in LIGHT_KINDS])
def test_a_light_scroll_lays_a_light_that_goes_with_the_hero(g, sid):
    p = g.player
    before = set(g.dungeon.explored)
    base = p.get_sight_radius()
    g._apply_scroll_effect(_item(sid))
    d = SCROLLS[sid]
    assert p.status_effects.get('light') == d['light_turns']
    assert lights.light_bonus(p) == d['light_sight']
    assert p.get_sight_radius() >= base + d['light_sight'] - lights.status_sight()
    # No map lit: only what the hero now sees joins what he had seen.
    assert g.dungeon.explored <= before | set(g.visible)
    assert len(g.dungeon.explored) < g.dungeon.width * g.dungeon.height // 4
    # It goes with him: a step on, the light is about him still.
    p.x += 3
    g._refresh_fov()
    g._light_tick()
    assert p.has_effect('light') and lights.light_bonus(p) == d['light_sight']
    line = item_words.what_it_does(_item(sid), p, buc_known=False)[0]
    assert _n(line, 'for') == d['light_turns'] and _n(line, 'sight') == d['light_sight']
    assert ('invisible' in line) == bool(d.get('light_reveals'))
    assert any(f"sight +{d['light_sight']} for {d['light_turns']} turns" in s for s in g.said), g.said


def test_revelation_lends_lynceuss_eyes(g):
    p = g.player
    d = SCROLLS['scroll_of_revelation']
    g._apply_scroll_effect(_item('scroll_of_revelation'))
    assert p.status_effects.get('see_invisible') == d['light_turns']
    assert p.status_effects.get('clairvoyant') == d['clairvoyant_turns']
    line = _line('scroll_of_revelation')
    assert f"for {d['clairvoyant_turns']} turns you see through stone" in line, line


@pytest.mark.parametrize('sid', [k for _, k in LIGHT_KINDS])
def test_a_blessed_light_scroll_burns_half_again_as_long(g, sid):
    g._apply_scroll_effect(_item(sid, 'blessed'))
    d = SCROLLS[sid]
    assert g.player.status_effects.get('light') == d['light_turns_blessed']
    assert _n(_line(sid, 'blessed'), 'for') == d['light_turns_blessed']


def test_a_cursed_light_scroll_calls_the_dark(g):
    p = g.player
    torch = items.make_item_by_id('light', 'torch')
    torch.lit = True
    p.shield = torch
    p.add_effect('light', 80, cap=lights.spell_cap())
    g._apply_scroll_effect(_item('scroll_of_light', 'cursed'))
    assert not torch.lit and not p.has_effect('light')
    assert lights.light_bonus(p) == 0
    assert 'call the dark' in _line('scroll_of_light', 'cursed')


# ------------------------------------------------------------ mapping

MAP_KINDS = _kinds('mapping')


def test_the_mapping_ladder_climbs():
    assert [t for t, _ in MAP_KINDS] == [1, 2, 3, 4, 5]
    radii = [SCROLLS[k]['map_radius'] for _, k in MAP_KINDS]
    assert radii[0] >= 30 and radii[1] > radii[0]           # a real part of the floor
    assert radii[2:] == [0, 0, 0]                           # the whole floor from tier 3
    finds = [set(SCROLLS[k].get('map_finds', [])) for _, k in MAP_KINDS]
    assert finds[3] == {'secret_doors'} and finds[4] == {'secret_doors', 'traps'}
    assert all(a <= b for a, b in zip(finds, finds[1:]))


def test_local_mapping_maps_a_real_part_of_a_real_floor():
    """On generated floors 1-20, the tier-1 radius reaches about half the
    open tiles from a random spot (it was 6: four in a hundred)."""
    import dungeon as D
    from dungeon import WALL
    rng = random.Random(5)
    r1 = SCROLLS['scroll_of_local_mapping']['map_radius']
    r2 = SCROLLS['scroll_of_area_mapping']['map_radius']
    share1, share2 = [], []
    for lvl in (2, 5, 9, 13, 17):
        random.seed(lvl)
        d = D.generate_dungeon(80, 50, lvl)
        open_t = [(x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] != WALL]
        for px, py in rng.sample([t for t in open_t if d.is_walkable(*t)], 8):
            share1.append(sum(abs(x - px) + abs(y - py) <= r1 for x, y in open_t) / len(open_t))
            share2.append(sum(abs(x - px) + abs(y - py) <= r2 for x, y in open_t) / len(open_t))
    assert statistics.mean(share1) >= 0.35, statistics.mean(share1)
    assert statistics.mean(share2) >= 0.55, statistics.mean(share2)


def test_local_mapping_maps_its_radius_and_no_farther(g):
    d, p = g.dungeon, g.player
    d.explored = set()
    g._apply_scroll_effect(_item('scroll_of_local_mapping'))
    r = SCROLLS['scroll_of_local_mapping']['map_radius']
    for y in range(d.height):
        for x in range(d.width):
            near = abs(x - p.x) + abs(y - p.y) <= r
            assert ((x, y) in d.explored) == near, (x, y)
    line = _line('scroll_of_local_mapping')
    assert _n(line, 'within') == r and 'half the floor' in line


@pytest.mark.parametrize('sid', ['scroll_of_cartography', 'scroll_of_deep_mapping',
                                 'scroll_of_dungeon_mapping'])
def test_the_deeper_charts_map_the_whole_floor_and_find_what_they_say(g, sid):
    from dungeon import DOOR, SECRET_DOOR
    d, p = g.dungeon, g.player
    d.explored = set()
    hidden = [(p.x - 8, p.y - 9), (p.x + 8, p.y + 9)]
    for x, y in hidden:
        d.tiles[y][x] = SECRET_DOOR
    snare = (p.x + 4, p.y + 4)
    d.traps[snare] = {'type': 'pit', 'revealed': False}
    g._apply_scroll_effect(_item(sid))
    assert len(d.explored) == d.width * d.height
    finds = set(SCROLLS[sid].get('map_finds', []))
    assert all((d.tiles[y][x] == DOOR) == ('secret_doors' in finds) for x, y in hidden)
    assert d.traps[snare]['revealed'] == ('traps' in finds)
    line = _line(sid)
    assert 'whole floor' in line
    assert ('hidden door' in line) == ('secret_doors' in finds)
    assert ('trap' in line) == ('traps' in finds)


# ------------------------------------------------------------ identify

ID_KINDS = _kinds('identify')
RUNGS = ('sort', 'pack', 'sight', 'floor')


def test_the_identify_ladder_climbs_and_a_blessing_reaches_a_rung_further():
    assert [t for t, _ in ID_KINDS] == [1, 2, 3, 4, 5]
    reach = [SCROLLS[k]['identify_reach'] for _, k in ID_KINDS]
    assert reach == ['sort', 'pack', 'sight', 'floor', 'floor']
    assert SCROLLS['scroll_of_omnisight']['identify_lore'] is True
    for (_, k), (_, nxt) in zip(ID_KINDS, ID_KINDS[1:]):
        d = SCROLLS[k]
        got = (d.get('identify_reach_blessed', d['identify_reach']),
               bool(d.get('identify_lore_blessed', d.get('identify_lore', False))))
        want = (SCROLLS[nxt]['identify_reach'], bool(SCROLLS[nxt].get('identify_lore', False)))
        assert got == want, k
    # The names no longer promise "two" and "three".
    assert SCROLLS['scroll_of_identify_two']['name'] == 'scroll of discernment'
    assert SCROLLS['scroll_of_identify_three']['name'] == 'scroll of appraisal'


_WORDS = {'sort': 'of its sort', 'pack': 'at your feet', 'sight': 'lying in sight',
          'floor': 'anywhere on this floor'}


@pytest.mark.parametrize('buc', ['uncursed', 'blessed'])
def test_each_identify_card_says_its_reach(buc):
    for _, k in ID_KINDS:
        d = SCROLLS[k]
        reach = wards.field_of(d, 'identify_reach', buc)
        lore = bool(wards.field_of(d, 'identify_lore', buc, False))
        line = _line(k, buc)
        assert _WORDS[reach] in line, (k, buc, line)
        assert ('corpse' in line) == lore, (k, buc, line)


def _unknown_potions(g, n):
    out = []
    for p in items.load_items('potion'):
        if len(out) >= n:
            break
        if any(p.id == o.id for o in out):
            continue
        p.id_level = 0
        p.buc = 'uncursed'
        g.player.known_item_ids.discard(p.id)
        if g._needs_identify(p):
            out.append(p)
    assert len(out) == n
    return out


def _unknown_scroll(g, sid='scroll_of_sleep'):
    s = _item(sid)
    s.id_level = 0
    g.player.known_item_ids.discard(sid)
    assert g._needs_identify(s)
    return s


def _lay(g, it, x, y):
    it.x, it.y = x, y
    g.ground_items.append(it)
    return it


def _far_tile(g):
    p = g.player
    for y in range(g.dungeon.height):
        for x in range(g.dungeon.width):
            if abs(x - p.x) + abs(y - p.y) > 25 and (x, y) not in g.visible:
                return x, y
    raise AssertionError('no tile out of sight')


def test_identify_names_the_thing_chosen_and_every_other_of_its_sort(g):
    p = g.player
    pot_a, pot_b = _unknown_potions(g, 2)
    other = _unknown_scroll(g)
    p.inventory += [pot_a, pot_b, other]
    g._apply_scroll_effect(_item('scroll_of_identify'))
    assert g.state == STATE_IDENTIFY_MENU and g._scroll_identify_pending
    g._identify_sel = [e[0] for e in g.identify_menu_items].index(pot_a)
    g._identify_menu_input(pygame.K_RETURN)
    assert not g._needs_identify(pot_a) and not g._needs_identify(pot_b)
    assert g._needs_identify(other)            # a scroll is another sort
    assert any('rest of that sort' in s for s in g.said), g.said


def test_a_blessed_identify_needs_no_picker_and_names_all_he_carries(g):
    p = g.player
    pots = _unknown_potions(g, 2)
    other = _unknown_scroll(g)
    p.inventory += pots + [other]
    g._apply_scroll_effect(_item('scroll_of_identify', 'blessed'))
    assert g.state == STATE_PLAYER
    assert not any(g._needs_identify(i) for i in pots + [other])


def test_each_rung_reaches_as_far_as_it_says(g):
    p = g.player
    carried, underfoot, in_view, far = _unknown_potions(g, 4)
    p.inventory.append(carried)
    _lay(g, underfoot, p.x, p.y)
    _lay(g, in_view, p.x + 3, p.y)
    g._refresh_fov()
    assert (p.x + 3, p.y) in g.visible
    _lay(g, far, *_far_tile(g))
    chest = _lay(g, items.make_item_by_id('container', 'wooden_chest')
                 or next(iter(items.load_items('container'))), p.x - 2, p.y)
    reached = {}
    for _, k in ID_KINDS[1:]:
        for it in (carried, underfoot, in_view, far):
            it.id_level = 0
            p.known_item_ids.discard(it.id)
        g._apply_scroll_effect(_item(k))
        reached[SCROLLS[k]['identify_reach']] = [not g._needs_identify(i)
                                                 for i in (carried, underfoot, in_view, far)]
    assert reached['pack'] == [True, True, False, False]
    assert reached['sight'] == [True, True, True, False]
    assert reached['floor'] == [True, True, True, True]
    assert chest in g.ground_items               # (a chest is no loose loot: untouched)


def test_omnisight_opens_the_lore_of_every_kind_of_corpse_carried(g):
    from items import Corpse
    p = g.player
    kinds = [k for k, v in KINDS.items() if not v.get('is_boss') and v.get('tags') is not None
             and k not in p.studied_monster_ids][:2]
    for k in kinds:
        p.inventory.append(Corpse(KINDS[k]['name'], k, p.x, p.y, harvest_tier=1,
                                  monster_def={'tags': KINDS[k]['tags']}))
    g._apply_scroll_effect(_item('scroll_of_omnisight'))
    assert all(k in p.lore_known_monster_ids for k in kinds), kinds


# ------------------------------------------------ the other numbers in data

_FIELDS = {
    'mapping': ('map_radius',), 'identify': ('identify_reach',),
    'full_light': ('light_turns', 'light_sight'),
    'confuse_monsters': ('control_turns',), 'sleep_monsters': ('control_turns',),
    'protection': ('shield_turns',),
    'enchant_weapon': ('delta', 'delta_blessed', 'both_weapons'),
    'enchant_armor': ('delta', 'delta_blessed', 'pieces'),
    'enchant_item': ('delta', 'delta_blessed', 'count'),
    'enchant_accessory': ('delta', 'delta_blessed', 'count'),
}


@pytest.mark.parametrize('effect', sorted(_FIELDS))
def test_every_kind_keeps_its_own_numbers(effect):
    kinds = _kinds(effect)
    assert kinds, effect
    for _, k in kinds:
        for f in _FIELDS[effect]:
            assert f in SCROLLS[k], (k, f)
    spec = item_words.entry('scroll', effect)
    assert 'tiers' not in spec, effect                    # one source: the kind's data
    for _, k in kinds:
        line = _line(k)
        assert '?' not in line and '{' not in line, (k, line)


@pytest.mark.parametrize('effect', ['haste_self', 'time_stop_scroll'])
def test_haste_and_stopped_time_keep_their_turns_as_their_power(effect):
    turns = [int(SCROLLS[k]['power']) for _, k in _kinds(effect)]
    assert turns == sorted(turns) and len(set(turns)) == len(turns)
    assert 'mult' not in (item_words.entry('scroll', effect).get('power_turns') or {})


def test_a_tier_one_confusion_is_worth_reading():
    """Bewilderment laid 3 turns on what it saw; the tier-1 wand lays 4 on
    one creature a charge. The scroll, once, on everything in sight: 5."""
    with open(os.path.join(ROOT, 'data', 'items', 'wand.json'), encoding='utf-8') as f:
        wand = json.load(f)['wand_of_bewilderment']
    assert SCROLLS['scroll_of_bewilderment']['control_turns'] > int(wand['power'])


def test_the_old_inline_ladders_are_gone_from_the_handler():
    import inspect
    from game_magic import MagicMixin
    src = inspect.getsource(MagicMixin._apply_scroll_effect)
    for old in ('[6, 12, 22, 40, 999]', '[3, 6, 10, 16, 25]', '[0.4, 0.7, 1.0, 1.6, 2.5]',
                '[0.3, 0.6, 1.0, 1.5, 2.5]', '[10, 20, 30, 50, 80]', '[1, 1, 1, 2, 3]',
                '[1, 2, 3, 4, 99]', '[1, 2, 3, 5, 99]', '[0, 1, 1, 2, 3]', '[0, 0, 10, 30, 60]'):
        assert old not in src, old
