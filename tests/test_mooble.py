"""The Mooble (src/mooble_encounter.py, src/game_mooble_dance.py, data/mooble.json):
every run, on one floor of 31-45, the last dancer of the old mines waits in a
side cave. Meet him (he hints at the miners' Starnut Tart), give him a tart
(cooked to carry: kitchen.py), win three dance-offs with time between
(practice first, free), then "I choose you!" and he joins as the support
companion: a little mana while near, and the Dance of the Dark.

Behaviour tests on a real headless Game: the encounter is deep and every
run's floor is rolled, so Brandon cannot reach it on demand in a few minutes
(the QA hero's Shift+D sets him down). The rhythm FEEL needs Brandon's hands;
tests/test_rhythm.py pins the scoring.
"""
import copy
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import mooble_encounter as mo  # noqa: E402
import rhythm  # noqa: E402

pygame.init()
_SCREEN = None
D = mo.data()
with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_mooble__', seed=11):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = [m for m in g.monsters if mo.is_mooble(m)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _place(g):
    """The Mooble on this floor, set down by the game's own spawner (his
    cave), and the hero beside him."""
    g._mooble = {'floor': g.dungeon_level, 'spawned': False, 'outcome': None, 'seed': 7}
    g._maybe_spawn_mooble(g.dungeon_level)
    m = g._mooble_here()
    assert m is not None
    cave = getattr(m, '_mooble_cave', None)
    spot = cave['centre'] if cave else next(
        (m.x + dx, m.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
        if (dx or dy) and g.dungeon.is_walkable(m.x + dx, m.y + dy))
    g.player.x, g.player.y = spot
    g.monsters = [x for x in g.monsters if mo.is_mooble(x)]
    return m


def _key(g, key):
    g._mooble_input(key)


def _texts(g, n=10):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _clock(g, start=50_000):
    now = [start]
    g._mooble_clock_fn = lambda: now[0]
    return now


def _tart(g):
    t = mo.make_tart()
    g.player.inventory.append(t)
    return t


def _fed(g):
    """Met, and the tart given: off his ledge."""
    m = _place(g)
    g._start_mooble_encounter(m)
    _key(g, pygame.K_RETURN)
    _tart(g)
    _key(g, pygame.K_3)
    assert mo.has_tart(m)
    _key(g, pygame.K_RETURN)
    return m


_ARROWS = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN}


def _dance_through(g, now, presses='on_time'):
    """Space, then the whole dance on the fake clock: every frame's tick, and
    the keys at the times given (on time, or a list of (t, dir) from the
    dance's start)."""
    from game_states import STATE_MOOBLE_DANCE
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['phase'] == 'ready'
    g._mooble_dance_key(pygame.K_SPACE)
    md = g._mdance
    t0 = md['t0']
    tl = md['tl']
    keys = rhythm.on_time(tl['response']) if presses == 'on_time' else list(presses)
    events = sorted([(t, 'key', d) for t, d in keys]
                    + [(k * tl['beat_ms'], 'tick', None) for k in range(tl['beats'] + 2)])
    for t, kind, d in events:
        now[0] = t0 + int(round(t))
        if kind == 'tick':
            g._mooble_dance_tick()
        elif md['phase'] == 'play':
            g._mooble_dance_key(_ARROWS[d])
    now[0] = t0 + int(g._mooble_end_ms()) + 5
    g._mooble_dance_tick()
    assert md['phase'] == 'result'
    return md


def _win_dance_off(g, now):
    from game_states import STATE_MOOBLE
    _key(g, pygame.K_2)
    md = _dance_through(g, now)
    assert md['won']
    g._mooble_dance_key(pygame.K_RETURN)
    assert g.state == STATE_MOOBLE and g._mooble_phase == 'outcome'


def _wait(g):
    g.turn_count += int(D['gap_turns'])


# ---------------------------------------------------------------------------
# Data: the floors, the words, the numbers
# ---------------------------------------------------------------------------

def test_every_run_on_a_floor_of_31_to_45_never_a_gate_boss_floor():
    floors = [mo.roll_floor(random.Random(i)) for i in range(3000)]
    assert None not in floors
    assert set(floors) == set(range(31, 46)) - {40}


def test_a_planned_mini_boss_floor_is_avoided_while_another_is_left():
    floors = {mo.roll_floor(random.Random(i), exclude=range(31, 45)) for i in range(200)}
    assert floors == {45}


def test_the_roll_leaves_the_shared_random_stream_alone():
    random.seed(5)
    before = random.getstate()
    mo.new_run_state()
    assert random.getstate() == before


def test_a_new_game_rolls_his_floor():
    g = _game()
    st = g._mooble
    assert 31 <= st['floor'] <= 45 and st['floor'] != 40
    assert st['spawned'] is False and st['outcome'] is None


def test_his_lines_are_all_there_one_per_stage():
    assert len(D['story']) >= 3
    assert len(D['waiting']) == D['dances_needed'] + 1
    assert len(D['too_soon']) == D['dances_needed']
    assert len(D['dance_won']) == D['dances_needed']
    assert len(D['refused_dances']) == D['dances_needed']
    for key in ('on_ledge', 'no_tart', 'tart_given', 'already_ate', 'dance_lost', 'all_danced',
                'refused_ledge', 'pass', 'fail', 'ignore', 'named_message', 'named_chronicle'):
        assert D[key].strip(), key
    # The plan's own words for the stages and the too-soon line.
    assert 'bobs, unsure' in D['dance_won'][0]
    assert 'bobble glows' in D['dance_won'][1]
    assert 'spins and laughs' in D['dance_won'][2]
    assert 'still dancing the last one through' in D['too_soon'][1]
    assert 'waves you off with a wing' in D['too_soon'][1]
    assert "Not yet...pom" in D['dance_lost']


def _all_text(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not str(k).startswith('_'):
                yield from _all_text(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _all_text(v)


def test_his_words_are_ours_he_says_pom_and_never_they():
    text = ' '.join(_all_text(D))
    for word in ('Moogle', 'Chocobo', 'Kupo', 'kupo', 'Gysahl', 'Final Fantasy'):
        assert word not in text, word
    assert '...pom' in text
    from test_no_singular_they import find_singular_they
    assert find_singular_they(text) == []
    # 'they' only ever for plurals: the miners, the other Moobles, his feet, steps, foes.
    for m in re.finditer(r'\b(?:they|them|their)\b', text, re.I):
        ctx = text[max(0, m.start() - 120):m.end()]
        assert re.search(r'miners|others|Moobles|feet|steps|foes', ctx), ctx


def test_the_numbers_are_the_plans():
    dd = D['dance']
    assert (dd['good_ms'], dd['perfect_ms'], dd['pass_share'], dd['max_misses']) == (150, 50, 0.75, 2)
    assert [(len(v['steps']), v['bpm']) for v in dd['visits']] == [(4, 80), (6, 95), (8, 110)]
    assert D['dances_needed'] == 3 and D['gap_turns'] > 0
    assert D['quiz'] == {'subject': 'animal', 'tier': 2, 'threshold': 2}


def test_the_data_ships_with_the_game():
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert "('data/mooble.json'," in spec


# ---------------------------------------------------------------------------
# His floor, his cave
# ---------------------------------------------------------------------------

def test_he_waits_only_on_his_floor_in_a_side_cave_with_a_starnut():
    g = _game('__test_mooble_floors__')
    g._mooble = {'floor': 33, 'spawned': False, 'outcome': None, 'seed': 3}
    seen = {}
    for lvl in (31, 32, 33, 34):
        g._change_level(lvl, enter_from_top=True, via='warp')
        here = [m for m in g.monsters if mo.is_mooble(m)]
        seen[lvl] = len(here)
        if lvl == 33:
            m = here[0]
            assert m.is_allied and m.pronoun == 'he' if hasattr(m, 'pronoun') else True
            assert g._needed_to_finish(m)
            cave = getattr(m, '_mooble_cave', None)
            assert cave and (m.x, m.y) == cave['back']
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert cave['centre'] in walk
            nuts = [i for i in g.ground_items if getattr(i, 'id', '') == 'starnut']
            assert any((n.x, n.y) in cave['chamber'] for n in nuts)
    assert seen == {31: 0, 32: 0, 33: 1, 34: 0}
    g._change_level(33, enter_from_top=False, via='warp')
    assert len([m for m in g.monsters if mo.is_mooble(m)]) == 1


def test_a_run_whose_floor_is_none_never_meets_him():
    g = _game('__test_mooble_none__')
    g._mooble = {'floor': None, 'spawned': False, 'outcome': None}
    g._maybe_spawn_mooble(g.dungeon_level)
    assert g._mooble_here() is None


def test_his_floor_is_kept_clear_of_road_scenes():
    g = _game()
    assert g._mooble['floor'] in g._secret_floors()


# ---------------------------------------------------------------------------
# The encounter's state machine
# ---------------------------------------------------------------------------

def test_meeting_him_tells_his_story_and_teaches_the_tart():
    from game_states import STATE_MOOBLE
    import kitchen
    g = _game()
    m = _place(g)
    assert kitchen.recipe(D['tart_recipe']) not in [r['recipe'] for r in kitchen.menu_rows(
        g.player, g.player.inventory, 'special')]
    g._start_mooble_encounter(m)
    assert g.state == STATE_MOOBLE and g._mooble_phase == 'story'
    assert D['tart_recipe'] in g.player.dishes_learned
    assert any('Starnut Tart' in t for t in _texts(g))
    rows = kitchen.menu_rows(g.player, g.player.inventory, 'special')
    tart = next(r for r in rows if r['id'] == D['tart_recipe'])
    assert tart['group'] == 'building'
    assert any('Made to carry' in e for e in tart['effects'])
    _key(g, pygame.K_RETURN)
    assert g._mooble_phase == 'options'
    # Leave and come back: straight to his choices.
    _key(g, pygame.K_5)
    g._start_mooble_encounter(m)
    assert g._mooble_phase == 'options'


def test_before_the_tart_he_will_not_come_down_and_says_why():
    g = _game()
    m = _place(g)
    g._start_mooble_encounter(m)
    _key(g, pygame.K_RETURN)
    for key, line in ((pygame.K_1, 'on_ledge'), (pygame.K_2, 'on_ledge'), (pygame.K_4, 'refused_ledge'),
                      (pygame.K_3, 'no_tart')):
        _key(g, key)
        assert g._mooble_text == D[line], line
        _key(g, pygame.K_RETURN)
    assert not mo.has_tart(m) and g.quiz_engine.callback is None


def test_the_tart_brings_him_down_and_is_eaten():
    g = _game()
    m = _place(g)
    g._start_mooble_encounter(m)
    _key(g, pygame.K_RETURN)
    tart = _tart(g)
    other = copy.copy(tart)
    other.id = 'bread_ration'
    _key(g, pygame.K_3)
    assert g._mooble_text == D['tart_given']
    assert tart not in g.player.inventory and mo.has_tart(m)
    assert m.sprite_id == mo.art(D['sprite_down'])
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_3)
    assert g._mooble_text == D['already_ate']


def test_practice_is_free_repeatable_and_leavable():
    from game_states import STATE_MOOBLE, STATE_MOOBLE_DANCE
    g = _game()
    _fed(g)
    now = _clock(g)
    turn = g.turn_count
    _key(g, pygame.K_1)
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    md = _dance_through(g, now, presses=[])
    assert not md['won'] and md['result']['missed_steps'] == 4
    # Again: Enter dances it again; then Esc in the middle stops it.
    g._mooble_dance_key(pygame.K_RETURN)
    assert g._mdance['phase'] == 'play'
    g._mooble_dance_key(pygame.K_ESCAPE)
    assert g.state == STATE_MOOBLE and g._mooble_phase == 'options'
    assert g._mooble.get('last_turn') is None and g.turn_count == turn
    assert mo.dances(g._mooble_npc) == 0


def test_from_practice_d_goes_to_the_dance_off():
    g = _game()
    _fed(g)
    now = _clock(g)
    _key(g, pygame.K_1)
    _dance_through(g, now)
    g._mooble_dance_key(pygame.K_d)
    assert g._mdance['mode'] == 'dance' and g._mdance['phase'] == 'ready'


def test_a_dance_off_must_be_danced_through_esc_does_not_stop_it():
    g = _game()
    _fed(g)
    now = _clock(g)
    _key(g, pygame.K_2)
    g._mooble_dance_key(pygame.K_SPACE)
    g._mooble_dance_key(pygame.K_ESCAPE)
    assert g._mdance is not None and g._mdance['phase'] == 'play'
    _ = now


def test_a_won_dance_ends_the_visit_with_its_line_and_counts():
    from game_states import STATE_PLAYER
    g = _game()
    m = _fed(g)
    now = _clock(g)
    turn = g.turn_count
    _win_dance_off(g, now)
    assert g._mooble_text == D['dance_won'][0] and mo.dances(m) == 1
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER and g.turn_count == turn + 1


def test_a_lost_dance_ends_the_visit_and_he_needs_time():
    from game_states import STATE_PLAYER
    g = _game()
    m = _fed(g)
    now = _clock(g)
    _key(g, pygame.K_2)
    tl = g._mdance['tl']
    md = _dance_through(g, now, presses=rhythm.on_time(tl['response'])[:2])
    assert not md['won']
    g._mooble_dance_key(pygame.K_RETURN)
    assert g._mooble_text == D['dance_lost'] and mo.dances(m) == 0
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    # Too soon: the line for no dances yet; the dance-off waits...
    g._start_mooble_encounter(m)
    assert g._mooble_phase == 'options' and g._mooble_too_soon(m)
    assert g._mooble_text == D['too_soon'][0]
    turn = g.turn_count
    _key(g, pygame.K_2)
    assert g._mooble_phase == 'outcome' and g._mooble_text == D['too_soon'][0]
    _key(g, pygame.K_RETURN)
    # ...but practice never does (Brandon: "practice as many times as you want").
    from game_states import STATE_MOOBLE_DANCE
    _key(g, pygame.K_1)
    assert g.state == STATE_MOOBLE_DANCE and g._mdance['mode'] == 'practice'
    g._mooble_dance_key(pygame.K_ESCAPE)
    _key(g, pygame.K_5)
    assert g.state == STATE_PLAYER and g.turn_count == turn       # nothing spent
    _wait(g)
    g._start_mooble_encounter(m)
    assert g._mooble_phase == 'options' and not g._mooble_too_soon(m)


def test_too_soon_has_a_line_per_stage_and_leaving_his_floor_is_waiting():
    g = _game()
    m = _fed(g)
    now = _clock(g)
    for n in range(2):
        _win_dance_off(g, now)
        _key(g, pygame.K_RETURN)
        g._start_mooble_encounter(m)
        assert g._mooble_text == D['too_soon'][n + 1] and g._mooble_too_soon(m)
        _key(g, pygame.K_5)
        if n == 0:
            _wait(g)
        else:
            g._mooble_left(g._mooble['floor'], g._mooble['floor'] + 1)   # away and back
        g._start_mooble_encounter(m)
        assert g._mooble_phase == 'options' and not g._mooble_too_soon(m)


def test_i_choose_you_refusals_say_what_is_missing_then_the_quiz():
    from quiz_engine import QuizMode
    from game_states import STATE_QUIZ
    g = _game()
    m = _fed(g)
    now = _clock(g)
    for n in range(3):
        _key(g, pygame.K_4)
        assert g._mooble_text == D['refused_dances'][n]
        _key(g, pygame.K_RETURN)
        _win_dance_off(g, now)
        if n < 2:
            _key(g, pygame.K_RETURN)
            _wait(g)
            g._start_mooble_encounter(m)
    assert g._mooble_text == D['dance_won'][2]
    _key(g, pygame.K_RETURN)
    assert g._mooble_phase == 'options'             # he asks: no wait to answer him
    _key(g, pygame.K_2)
    assert g._mooble_text == D['all_danced']
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_4)
    qe = g.quiz_engine
    assert g.state == STATE_QUIZ and qe.subject == 'animal' and qe.tier == 2
    assert qe.mode == QuizMode.THRESHOLD and qe.required == 2


def _three_dances(g):
    m = _fed(g)
    m._mooble_dances = 3
    return m


def test_a_fumbled_ask_waits_then_he_can_be_asked_again():
    from game_states import STATE_MOOBLE, STATE_QUIZ
    g = _game()
    m = _three_dances(g)
    _key(g, pygame.K_4)
    g.quiz_engine._end(success=False)
    assert g.state == STATE_MOOBLE and g._mooble_text == D['fail']
    _key(g, pygame.K_RETURN)
    g._start_mooble_encounter(m)
    assert g._mooble_text == D['too_soon'][2]
    _key(g, pygame.K_4)
    assert g._mooble_phase == 'outcome' and g._mooble_text == D['too_soon'][2]
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_5)
    _wait(g)
    g._start_mooble_encounter(m)
    _key(g, pygame.K_4)
    assert g.state == STATE_QUIZ


def test_passing_makes_him_your_mooble_with_the_naming_popup():
    from game_states import STATE_MOOBLE, STATE_PET_NAME_INPUT, STATE_PLAYER
    g = _game()
    g.pets = []
    m = _three_dances(g)
    _key(g, pygame.K_4)
    g.quiz_engine._end(success=True)
    assert g.state == STATE_MOOBLE and g._mooble_text == D['pass']
    assert m not in g.monsters and g._mooble['outcome'] == 'adopted'
    pet = g.pets[-1]
    assert pet.species_key == 'mooble' and pet.species_name == 'Mooble' and pet.level == D['pet_level']
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PET_NAME_INPUT and g._naming_pet is pet
    g.render()
    g._pet_name_input_buffer = 'Pip'
    g._pet_name_input(pygame.K_RETURN, '')
    assert g.state == STATE_PLAYER and pet.name == 'Pip the Mooble'
    assert any('never dance alone again' in t for t in _texts(g))
    # Gone from the run: his floor never sets him down again.
    g._mooble['spawned'] = False
    g._maybe_spawn_mooble(g.dungeon_level)
    assert g._mooble_here() is None


def test_adopting_him_follows_the_one_companion_rule():
    from pet_system import Pet, is_companion
    g = _game()
    g.pets = [Pet('water', g.player.x, g.player.y)]
    m = _three_dances(g)
    _key(g, pygame.K_4)
    g.quiz_engine._end(success=True)
    out = [p for p in g.pets if is_companion(p)]
    assert [p.species_key for p in out] == ['mooble']
    held = [i for i in g.player.inventory if getattr(i, 'bound_pet', None) is not None]
    assert held and held[0].bound_pet.species_key == 'water'
    _ = m


# ---------------------------------------------------------------------------
# Cook to carry: the Starnut Tart
# ---------------------------------------------------------------------------

def test_the_tart_recipe_is_a_dish_cooked_to_carry():
    import kitchen
    rec = kitchen.recipe(D['tart_recipe'])
    assert rec['name'] == 'Starnut Tart' and rec['makes'] == D['tart_item']
    assert sorted(rec['ingredients']) == ['apple', 'bread_ration', 'starnut']
    assert kitchen.dish_tab(rec) == 'special' and kitchen.dish_power(rec) is None
    food = kitchen.carried_food(rec)
    assert food['sp_restore'] > 0 and food.get('made_to_carry')
    assert food['floor_spawn_weight'] == {'1-100': 0}
    lines = kitchen.dish_effects(None, rec)
    assert lines[0].startswith('Made to carry') and lines[1].startswith('If eaten: +')
    import cook_menu
    row = {'recipe': rec, 'effects': lines, 'ready': True, 'progress': '3 of 3'}
    assert cook_menu.chip_text(row) == 'To Carry'


def test_cooking_it_puts_the_tart_in_the_pack_uneaten():
    import types
    import kitchen
    from food_system import cook_compound_recipe, load_ingredient_for
    from items import make_item_by_id
    from player import Player
    p = Player()
    p.inventory = []
    for it in (load_ingredient_for('starnut'), make_item_by_id('food', 'bread_ration'),
               make_item_by_id('food', 'apple')):
        p.add_to_inventory(it)
    p.sp = 50
    sp, hp = p.sp, p.hp
    quiz = types.SimpleNamespace(start_quiz=lambda **kw: kw['callback'](types.SimpleNamespace(success=True)))
    got = []
    cook_compound_recipe(p, kitchen.recipe(D['tart_recipe']), p.inventory, quiz, got.append)
    assert [i.id for i in p.inventory] == ['starnut_tart']
    assert p.sp == sp and p.hp == hp                       # not eaten
    assert got[0][0] == 'You prepare Starnut Tart.' and 'in your pack' in got[0][1]
    # Ruined: the parts are gone and there is no tart.
    p2 = Player()
    p2.inventory = []
    for it in (load_ingredient_for('starnut'), make_item_by_id('food', 'bread_ration'),
               make_item_by_id('food', 'apple')):
        p2.add_to_inventory(it)
    bad = types.SimpleNamespace(start_quiz=lambda **kw: kw['callback'](types.SimpleNamespace(success=False)))
    cook_compound_recipe(p2, kitchen.recipe(D['tart_recipe']), p2.inventory, bad, got.append)
    assert p2.inventory == []


def test_the_tart_is_a_pleasant_snack_with_art_and_is_never_taken():
    import items
    import renderer
    tart = mo.make_tart()
    assert isinstance(tart, items.Food) and tart.sp_restore > 0 and tart.weight < 1
    assert renderer._resolve_item_sprite_path('starnut_tart')
    assert 'starnut_tart' in items.WITHHELD_IDS


# ---------------------------------------------------------------------------
# The companion
# ---------------------------------------------------------------------------

def test_he_is_a_small_support_companion_of_three_stages():
    from pet_system import Pet, growth, random_species
    names = [Pet('mooble', level=lv).species_name for lv in (1, 25, 55)]
    assert names == ['Mooble', 'Mooble Dancer', 'Mooble Troupe-Leader']
    pet = Pet('mooble', level=20)
    assert pet.max_hp < growth('health', 20) and pet.base_damage < growth('bite', 20)
    assert pet.pronouns()[0] == 'he'
    assert 'mooble' not in {random_species() for _ in range(400)}
    assert [s['id'] for s in pet.available_specials()] == ['dance_of_the_dark']
    # His pictures: his own once installed, a creature's stand-in until then
    # (never a letter on the map).
    from paths import data_path
    for lv, sid in ((20, 'mooble'), (30, 'mooble_dancer'), (60, 'mooble_troupe_leader')):
        p = Pet('mooble', level=lv)
        have = os.path.exists(data_path('assets', 'tiles', 'monsters', f'{sid}.png'))
        want = sid if have else D['art_standin']
        assert p.sprite_id == want
        assert os.path.exists(data_path('assets', 'tiles', 'monsters', f'{p.sprite_id}.png'))


def test_his_mana_gift_every_few_turns_while_near():
    from pet_system import Pet
    from player import Player
    p = Player()
    p.max_mp, p.mp = 30, 10
    p.x, p.y = 5, 5
    pet = Pet('mooble', 6, 5, level=20)
    gift = pet.species['mana_gift']
    got = [pet.mana_gift(p) for _ in range(gift['every'][0] * 3)]
    assert sum(got) == 3 and p.mp == 13
    assert got[gift['every'][0] - 1] == 1 and not any(got[:gift['every'][0] - 1])
    # Too far: nothing.
    pet.x = 5 + gift['radius'] + 1
    assert sum(pet.mana_gift(p) for _ in range(20)) == 0
    # Back near: it comes (the wait was already served); full mana: nothing.
    pet.x = 6
    assert pet.mana_gift(p) == 1
    p.mp = p.max_mp
    assert sum(pet.mana_gift(p) for _ in range(20)) == 0
    # Quicker as he grows.
    assert [Pet('mooble', level=lv).mana_gift_every() for lv in (1, 25, 55)] == gift['every']


def test_the_game_turn_gives_his_mana_and_says_so_once_a_floor():
    from pet_system import Pet
    g = _game()
    g.monsters = []
    pet = Pet('mooble', g.player.x + 1, g.player.y, level=20)
    g.pets = [pet]
    g.player.max_mp = 40
    g.player.mp = 5
    for _ in range(12):
        g._do_pet_turns()
    assert g.player.mp >= 7
    line = pet.species['mana_gift']['line'].replace('{pet}', pet.name)
    assert sum(1 for e in g.msg_log.entries if str(e[0]) == line) == 1


def _hall(g):
    from dungeon import Dungeon, Room, WALL, FLOOR
    w, h = 40, 20
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = FLOOR
    g.dungeon = Dungeon(tiles, [Room(0, 0, w, h)], w, h, 33)
    g.dungeon_level = 33
    g.monsters[:] = []
    g.ground_items[:] = []
    g.player.x, g.player.y = 10, 10
    g._refresh_fov()


def _mon(kind, x, y):
    from monster import Monster
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = True
    return m


SD = D['pet']['special_dance']
BANDS = {b['name']: b for b in SD['bands']}


def _result(total, perfects=0, goods=0, strays=0):
    return {'total': total, 'perfects': perfects, 'goods': goods, 'hits': perfects + goods,
            'strays': strays, 'missed_steps': total - perfects - goods, 'misses': 0, 'steps': []}


def test_the_dance_of_the_darks_power_scales_with_how_it_was_danced():
    """Pure: the share of steps hit sets the band (how far, how long, how
    many), Perfects count extra, strays cost, and a flop still does a little."""
    flop = mo.dance_band(_result(8))
    assert flop['name'] == 'flop' and flop['radius'] >= 1 and flop['turns'] >= 1 and flop['max_held'] >= 1
    assert not flop['lift']
    order = [mo.dance_band(_result(8, goods=n)) for n in range(9)]
    for a, b in zip(order, order[1:]):
        assert (b['radius'], b['turns'], b['max_held']) >= (a['radius'], a['turns'], a['max_held'])
    assert order[-1]['name'] == 'great'                    # all Good: great, not dazzling
    # Perfects count extra: the same steps hit, all Perfect, dance better.
    assert mo.dance_band(_result(8, perfects=8))['name'] == 'dazzling'
    assert mo.dance_band(_result(8, perfects=4))['score'] > mo.dance_band(_result(8, goods=4))['score']
    # A stray key costs.
    assert mo.dance_band(_result(8, goods=8, strays=4))['score'] < order[-1]['score']
    # The Troupe-Leader's lift needs a good score.
    assert [b['lift'] for b in SD['bands']] == [False, False, True, True, True]
    assert BANDS['good']['min_score'] > BANDS['shaky']['min_score']
    # The phrases grow with his stage.
    assert [len(p['steps']) for p in SD['phrases']] == [4, 6, 8]


def _watchers(g, pet):
    gob = _mon('goblin', 13, 10)
    gob2 = _mon('goblin', 14, 11)
    far = _mon('goblin', 30, 10)
    boss = _mon('lamia', 12, 12)
    golem = _mon('clay_golem', 10, 12)
    blind = _mon('goblin', 9, 9)
    blind.status_effects['blinded'] = 5
    swarm = _mon('scarab_swarm', 12, 8)
    g.monsters.extend([gob, gob2, far, boss, golem, blind, swarm])
    g._refresh_fov()
    return gob, gob2, far, boss, golem, blind, swarm


def test_the_dance_of_the_dark_holds_only_what_the_watch_rule_allows():
    from pet_system import Pet
    g = _game()
    _hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    g.pets = [pet]
    gob, gob2, far, boss, golem, blind, swarm = _watchers(g, pet)
    sp = pet.available_specials()[0]
    held = g._mooble_dance_of_the_dark(pet, sp, BANDS['dazzling'])
    assert held == 2 and gob.has_effect('stunned') and gob2.has_effect('stunned')
    for m in (far, boss, golem, blind, swarm):
        assert not m.has_effect('stunned'), m.kind
    log = ' | '.join(_texts(g, 20))
    assert BANDS['dazzling']['line'].replace('{pet}', pet.name) in log
    assert 'The Goblin stands staring at the glowing bobble.' in log
    assert 'has seen finer dances' in log                 # the named foe
    assert 'has no mind for a dance' in log               # the mindless
    assert 'cannot see the dance at all' in log           # the blind
    assert 'does not even stop' in log                    # cannot be stunned


def test_a_weak_dance_holds_fewer_for_less_time_nearest_first():
    from pet_system import Pet
    g = _game()
    _hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    g.pets = [pet]
    gob, gob2, *_rest = _watchers(g, pet)
    g._mooble_dance_of_the_dark(pet, pet.available_specials()[0], BANDS['flop'])
    # The flop reaches 2 tiles and holds one: the nearest goblin (2 away) for a turn.
    assert gob.has_effect('stunned') and not gob2.has_effect('stunned')
    assert gob.status_effects['stunned'] <= BANDS['flop']['turns']


def test_only_a_troupe_leaders_good_dance_lifts_a_hindrance():
    from pet_system import Pet
    g = _game()
    _hall(g)
    for level, band, lifted in ((30, 'dazzling', False), (60, 'shaky', False), (60, 'good', True)):
        pet = Pet('mooble', 11, 10, level=level)
        g.pets = [pet]
        g.player.status_effects = {'poisoned': 5, 'stunned': 2}
        g._mooble_dance_of_the_dark(pet, pet.available_specials()[0], BANDS[band])
        if lifted:
            assert 'stunned' not in g.player.status_effects                  # the hold first
            assert 'poisoned' in g.player.status_effects                     # one only
        else:
            assert set(g.player.status_effects) == {'poisoned', 'stunned'}, (level, band)


def _special_through_the_menu(g, now, presses):
    """Shift+P, S, Enter: his special opens the dance screen, the count-in
    starts at once; the keys on the fake clock, then Enter."""
    from game_states import STATE_MOOBLE_DANCE
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, unicode='P',
                                      mod=pygame.KMOD_SHIFT, scancode=0))
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, unicode='s', mod=0, scancode=0))
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r', mod=0, scancode=0))
    assert g.state == STATE_MOOBLE_DANCE
    md = g._mdance
    assert md['mode'] == 'special' and md['phase'] == 'play' and not md['tl']['call']
    t0, tl = md['t0'], md['tl']
    keys = presses(tl['response'])
    events = sorted([(t, 'key', d) for t, d in keys]
                    + [(k * tl['beat_ms'], 'tick', None) for k in range(tl['beats'] + 2)])
    for t, kind, d in events:
        now[0] = t0 + int(round(t))
        if kind == 'tick':
            g._mooble_dance_tick()
        elif md['phase'] == 'play':
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=_ARROWS[d], unicode='', mod=0, scancode=0))
    now[0] = t0 + int(g._mooble_end_ms()) + 5
    g._mooble_dance_tick()
    assert md['phase'] == 'result'
    return md


@pytest.mark.parametrize('score', ['high', 'low'])
def test_the_special_is_danced_with_real_keys(score):
    from pet_system import Pet
    from game_states import STATE_PLAYER
    g = _game('__test_mooble_special_' + score)
    _hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    g.pets = [pet]
    gob, gob2, *_rest = _watchers(g, pet)
    g.state = STATE_PLAYER
    now = _clock(g)
    turn = g.turn_count
    moves = []
    real = gob.take_turn

    def watched(*a, **k):
        moves.append(g.state)
        return real(*a, **k)
    gob.take_turn = watched
    if score == 'high':
        md = _special_through_the_menu(g, now, rhythm.on_time)
        assert md['band']['name'] == 'dazzling'
        assert gob.has_effect('stunned') and gob2.has_effect('stunned')
    else:
        md = _special_through_the_menu(g, now, lambda resp: [])
        assert md['band']['name'] == 'flop'
        assert gob.has_effect('stunned') and not gob2.has_effect('stunned')
        assert 'only flickers' in ' '.join(_texts(g, 12))
    assert moves == []                                     # nothing acts during his dance
    assert pet.special_cooldown('dance_of_the_dark') == pet.available_specials()[0]['cooldown']
    g._mooble_dance_key(pygame.K_RETURN)
    assert g.state == STATE_PLAYER and g.turn_count == turn + 1


def test_the_special_spends_its_cooldown_when_it_starts():
    from pet_system import Pet
    g = _game()
    _hall(g)
    pet = Pet('mooble', 11, 10, level=60)
    g.pets = [pet]
    _clock(g)
    sp = pet.available_specials()[0]
    g._begin_pet_special_targeting(pet, sp)
    assert g._mdance['mode'] == 'special' and len(g._mdance['tl']['response']) == 8
    assert pet.special_cooldown('dance_of_the_dark') == sp['cooldown']
    g._mooble_dance_key(pygame.K_ESCAPE)                   # danced through: Esc does nothing
    assert g._mdance is not None and g._mdance['phase'] == 'play'


def test_on_return_he_keeps_beside_you_and_does_not_charge():
    from pet_system import Pet
    g = _game()
    _hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    gob = _mon('goblin', 14, 10)
    g.monsters.append(gob)
    for _ in range(3):
        pet.take_turn(g.player, g.dungeon, g.monsters, [pet])
    assert max(abs(pet.x - 10), abs(pet.y - 10)) <= 2
    assert max(abs(pet.x - gob.x), abs(pet.y - gob.y)) > 1


def test_his_card_tells_his_gifts():
    from pet_system import Pet
    g = _game()
    lines = [t for t, _c, _f in g._pet_gift_lines(Pet('mooble', level=20))]
    assert any('MP every 5 turns' in t for t in lines)
    assert any('Dance of the Dark' in t and 'better you dance' in t for t in lines)
    assert not any('Troupe-Leader' in t for t in lines)
    assert any('Troupe-Leader' in t for t in (x[0] for x in g._pet_gift_lines(Pet('mooble', level=60))))
    assert g._pet_gift_lines(Pet('water', level=20)) == []


# ---------------------------------------------------------------------------
# Saves, old saves, the QA key
# ---------------------------------------------------------------------------

def _roundtrip(g, name, tmp_path, monkeypatch):
    import save_system
    from main import Game
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    state = save_system.load_game(name)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(state)
    return g2


def test_a_save_mid_quest_keeps_his_tart_dances_and_the_wait(tmp_path, monkeypatch):
    name = '__test_mooble_save__'
    g = _game(name)
    m = _fed(g)
    now = _clock(g)
    _win_dance_off(g, now)
    _key(g, pygame.K_RETURN)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    st = g2._mooble
    assert st['spawned'] and st['outcome'] is None and st['last_turn'] is not None
    m2 = g2._mooble_here()
    assert m2 is not None and mo.has_tart(m2) and mo.dances(m2) == 1 and m2._mooble_met
    g2._start_mooble_encounter(m2)
    assert g2._mooble_text == D['too_soon'][1]
    assert D['tart_recipe'] in g2.player.dishes_learned
    _ = m


def test_a_save_mid_dance_opens_the_dance_again_at_its_start(tmp_path, monkeypatch):
    from game_states import STATE_MOOBLE_DANCE, STATE_PLAYER
    name = '__test_mooble_save_dance__'
    g = _game(name)
    _fed(g)
    now = _clock(g)
    _key(g, pygame.K_2)
    g._mooble_dance_key(pygame.K_SPACE)
    now[0] += 9000
    g._mooble_dance_tick()
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._mooble.get('dancing') == {'mode': 'dance'}
    g2.state = STATE_PLAYER
    g2.update(0.016)
    assert g2.state == STATE_MOOBLE_DANCE
    assert g2._mdance['mode'] == 'dance' and g2._mdance['phase'] == 'ready'
    assert g2._mooble.get('last_turn') is None                  # nothing was judged


def test_an_old_save_rolls_him_ahead_or_not_at_all(tmp_path, monkeypatch):
    name = '__test_mooble_old__'
    g = _game(name)
    del g._mooble
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._mooble['floor'] in set(range(31, 46)) - {40}
    g3 = _game(name + '2')
    del g3._mooble
    g3.player.deepest_floor_reached = 41
    g4 = _roundtrip(g3, name + '2', tmp_path, monkeypatch)
    assert g4._mooble['floor'] in set(range(42, 46))
    g5 = _game(name + '3')
    del g5._mooble
    g5.player.deepest_floor_reached = 46
    g6 = _roundtrip(g5, name + '3', tmp_path, monkeypatch)
    assert g6._mooble['floor'] is None


def test_qa_shift_d_sets_him_down_with_a_starnut_and_a_tart():
    g = _game()
    g.player.qa_tools = True
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d, unicode='D',
                                      mod=pygame.KMOD_SHIFT, scancode=0))
    m = g._mooble_here()
    assert m is not None and g._mooble['floor'] == g.dungeon_level
    ids = [getattr(i, 'id', '') for i in g.player.inventory]
    assert 'starnut' in ids and 'starnut_tart' in ids
    g._mooble['last_turn'] = g.turn_count
    g._qa_mooble()
    assert g._mooble['last_turn'] is None
    # Not the QA hero: nothing.
    g2 = _game('__test_mooble_noqa__')
    g2._qa_mooble()
    assert g2._mooble_here() is None


# ---------------------------------------------------------------------------
# A real-keys journey: down to his floor, meet him, cook the tart, give it,
# practise, win three dance-offs with time between, choose him
# ---------------------------------------------------------------------------

def _answer(g, right=True):
    qe = g.quiz_engine
    q = qe.current_question
    qe.answer(str(q['answer']) if right else '__surely wrong__')
    qe._result_hold_until = 0.0
    qe.release_result_hold()
    qe.update(5.0)


def test_journey_meet_bake_dance_three_times_and_choose_him():
    import kitchen
    from items import make_item_by_id
    from game_states import (STATE_PLAYER, STATE_MOOBLE, STATE_MOOBLE_DANCE, STATE_COOK_MENU,
                             STATE_QUIZ, STATE_PET_NAME_INPUT)
    g = _game('__test_mooble_journey__', seed=4)
    g.pets = []
    floor = 34
    g._mooble = {'floor': floor, 'spawned': False, 'outcome': None, 'seed': 9}
    g._change_level(floor, enter_from_top=True, via='warp')
    m = g._mooble_here()
    assert m is not None
    g.monsters = [x for x in g.monsters if mo.is_mooble(x)]
    g.state = STATE_PLAYER

    def press(key, uni='', mod=0):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=mod, scancode=0))

    cave = m._mooble_cave
    # Pick up the starnut growing in his cave.
    nut = next(i for i in g.ground_items if getattr(i, 'id', '') == 'starnut')
    g.player.x, g.player.y = nut.x, nut.y
    press(pygame.K_g, 'g')
    assert any(getattr(i, 'id', '') == 'starnut' for i in g.player.inventory)
    # Walk into him from the middle of the cave.
    g.player.x, g.player.y = cave['centre']
    dx, dy = m.x - g.player.x, m.y - g.player.y
    key = {(0, 1): pygame.K_DOWN, (0, -1): pygame.K_UP, (1, 0): pygame.K_RIGHT, (-1, 0): pygame.K_LEFT}[(dx, dy)]
    press(key)
    assert g.state == STATE_MOOBLE and g._mooble_phase == 'story'
    press(pygame.K_RETURN)
    press(pygame.K_5)
    assert g.state == STATE_PLAYER
    # Bake the tart: bread and an apple from the pack, the starnut from his cave.
    for fid in ('bread_ration', 'apple'):
        g.player.add_to_inventory(make_item_by_id('food', fid))
    press(pygame.K_c, 'c')
    assert g.state == STATE_COOK_MENU
    for _ in range(len(kitchen.MENU_TABS)):
        if g._cook_tab_slug() == 'special':
            break
        press(pygame.K_RIGHT)
    rows = g._cook_tab_rows()
    idx = next(i for i, r in enumerate(rows) if r['id'] == D['tart_recipe'])
    for _ in range(idx):
        press(pygame.K_DOWN)
    press(pygame.K_RETURN)
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'cooking'
    _answer(g, True)
    assert g.state == STATE_PLAYER
    assert any(getattr(i, 'id', '') == 'starnut_tart' for i in g.player.inventory)
    # Give it to him.
    g.player.x, g.player.y = cave['centre']
    press(key)
    press(pygame.K_3)
    assert mo.has_tart(m)
    press(pygame.K_RETURN)
    now = _clock(g)
    # Practise once, then three dance-offs with time between.
    press(pygame.K_1)
    assert g.state == STATE_MOOBLE_DANCE
    _dance_through(g, now)
    press(pygame.K_ESCAPE)
    for n in range(3):
        if n:
            g.turn_count += int(D['gap_turns'])
            g.player.x, g.player.y = cave['centre']
            press(key)
        assert g._mooble_phase == 'options'
        press(pygame.K_2)
        md = _dance_through(g, now)
        assert md['won'] and md['tl']['beat_ms'] == pytest.approx(60000 / D['dance']['visits'][n]['bpm'])
        press(pygame.K_RETURN)
        assert g._mooble_text == D['dance_won'][n]
        press(pygame.K_RETURN)
    # He asks; the answer is "I choose you!" and the animal quiz.
    press(pygame.K_4)
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'animal'
    while g.state == STATE_QUIZ:
        _answer(g, True)
    assert g.state == STATE_MOOBLE and g._mooble_text == D['pass']
    press(pygame.K_RETURN)
    assert g.state == STATE_PET_NAME_INPUT
    press(pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    assert [p.species_key for p in g.pets] == ['mooble'] and g._mooble['outcome'] == 'adopted'


def test_the_soundtrack_steps_aside_while_a_dance_plays(monkeypatch):
    """music.hold when a dance begins, music.release when it ends or is left,
    so the beat is clear (the lead's soundtrack, music.py)."""
    import music
    calls = []
    monkeypatch.setattr(music, 'hold', lambda: calls.append('hold'))
    monkeypatch.setattr(music, 'release', lambda: calls.append('release'))
    g = _game()
    _fed(g)
    now = _clock(g)
    _key(g, pygame.K_1)
    assert calls == []                                  # the ready card: no beat yet
    _dance_through(g, now)
    assert calls == ['hold', 'release']                 # held for the dance, back for the result
    g._mooble_dance_key(pygame.K_RETURN)                # practise again
    g._mooble_dance_key(pygame.K_ESCAPE)                # and stop in the middle
    assert calls == ['hold', 'release', 'hold', 'release']
