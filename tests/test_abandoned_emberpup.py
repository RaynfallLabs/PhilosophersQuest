"""The abandoned Emberpup (src/emberpup_encounter.py): about one run in five, on
one floor from 3 to 8, a small fire lizard waits alone on a rock under a rain
cloud. Feed it, leave it, attack it, or (once fed) say "I choose you!" and pass
an animal quiz (tier 2, two right answers) to make it your pet.

Behaviour tests on a real headless Game. The encounter is a rare, randomized
event, so Brandon cannot reach it on demand in play: these are the proof that
each outcome does what it says.
"""
import copy
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


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_emberpup__', seed=11):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _pups(g):
    import emberpup_encounter as ep
    return [m for m in g.monsters if ep.is_emberpup(m) and m.alive]


def _place_pup(g, floor=None):
    """The Emberpup on this floor, placed by the game's own spawner, and moved
    beside the hero so a step can bump it."""
    g._emberpup = {'floor': floor or g.dungeon_level, 'spawned': False, 'outcome': None}
    g.dungeon_level = floor or g.dungeon_level
    g._maybe_spawn_emberpup(g.dungeon_level)
    pup = _pups(g)[0]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = g.player.x + dx, g.player.y + dy
        if g.dungeon.is_walkable(x, y) and not any(
                (m.x, m.y) == (x, y) for m in g.monsters if m is not pup):
            pup.x, pup.y = x, y
            return pup, (dx, dy)
    raise AssertionError('no free tile beside the hero')


def _food(g, n=1, identified=True):
    from items import load_items, Food
    foods = [f for f in load_items('food') if isinstance(f, Food)
             and f.id != 'magic_dungeon_carrot']
    out = []
    for i in range(n):
        f = copy.copy(foods[i % len(foods)])
        f.identified = identified
        f.count = 1
        g.player.inventory.append(f)
        out.append(f)
    return out


def _clear_food(g):
    import emberpup_encounter as ep
    for it in ep.food_choices(g.player.inventory):
        g.player.inventory.remove(it)


def _key(g, key):
    g._emberpup_input(key)


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ---------------------------------------------------------------------------
# Rarity and placement
# ---------------------------------------------------------------------------

def test_about_one_run_in_five_gets_it_on_a_floor_from_3_to_8():
    import emberpup_encounter as ep
    floors = [ep.roll_floor(random.Random(i)) for i in range(20000)]
    hits = [f for f in floors if f is not None]
    assert 0.18 < len(hits) / len(floors) < 0.22, len(hits)
    assert set(hits) == {3, 4, 5, 6, 7, 8}


def test_the_roll_leaves_the_shared_random_stream_alone():
    """Seeded floors and tests must come out as they did before it existed."""
    import emberpup_encounter as ep
    random.seed(77)
    before = random.getstate()
    ep.roll_for_new_run()
    assert random.getstate() == before


def test_a_new_game_rolls_its_emberpup():
    g = _game()
    st = g._emberpup
    assert st['spawned'] is False and st['outcome'] is None
    assert st['floor'] is None or 3 <= st['floor'] <= 8


def test_it_waits_only_on_its_floor_and_is_reachable():
    g = _game('__test_emberpup_floors__')
    g._emberpup = {'floor': 4, 'spawned': False, 'outcome': None}
    seen = {}
    for lvl in (2, 3, 4, 5):
        g._change_level(lvl, enter_from_top=True)
        seen[lvl] = len(_pups(g))
        if lvl == 4:
            pup = _pups(g)[0]
            assert pup.is_allied and pup.kind == 'npc_abandoned_emberpup'
            assert g._needed_to_finish(pup)
            walk = g._reachable_tiles(g.player.x, g.player.y)
            assert any((pup.x + dx, pup.y + dy) in walk
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    assert seen == {2: 0, 3: 0, 4: 1, 5: 0}
    # Back up to its floor: still there, still only one.
    g._change_level(4, enter_from_top=False)
    assert len(_pups(g)) == 1
    assert g._emberpup['spawned'] is True


def test_a_run_without_it_never_meets_it():
    g = _game('__test_emberpup_none__')
    g._emberpup = {'floor': None, 'spawned': False, 'outcome': None}
    for lvl in range(2, 10):
        g._change_level(lvl, enter_from_top=True)
        assert not _pups(g), lvl


def test_on_a_crowded_floor_it_takes_the_shared_fallback_tile():
    """Every room it samples is full: it still gets a reachable tile."""
    g = _game('__test_emberpup_crowded__')
    calls = []
    real = g._free_spawn_tile

    def spy(occupied):
        calls.append(1)
        return real(occupied)
    g._free_spawn_tile = spy
    rooms = g.dungeon.rooms
    g.dungeon.rooms = rooms[:1] + [type('R', (), {'inner_tiles': lambda self: iter(())})()
                                   for _ in rooms[1:]]
    try:
        g._emberpup = {'floor': 1, 'spawned': False, 'outcome': None}
        g._maybe_spawn_emberpup(1)
    finally:
        g.dungeon.rooms = rooms
    assert calls and len(_pups(g)) == 1


# ---------------------------------------------------------------------------
# The screen and its four choices
# ---------------------------------------------------------------------------

def test_bumping_it_tells_its_story_then_offers_four_choices():
    from game_states import STATE_EMBERPUP
    g = _game()
    pup, (dx, dy) = _place_pup(g, 5)
    g._do_move(dx, dy)
    assert g.state == STATE_EMBERPUP and g._emberpup_phase == 'story'
    assert (g.player.x, g.player.y) != (pup.x, pup.y)
    _key(g, pygame.K_RETURN)
    assert g._emberpup_phase == 'options'
    # Leave and come back: straight to the choices this time.
    _key(g, pygame.K_2)
    g._do_move(dx, dy)
    assert g.state == STATE_EMBERPUP and g._emberpup_phase == 'options'


def test_give_food_eats_one_food_and_unlocks_i_choose_you():
    g = _game()
    pup, _ = _place_pup(g, 5)
    _clear_food(g)
    food = _food(g, 2)
    karma = g.karma
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    assert g._emberpup_phase == 'select_food'
    assert g._emberpup_food == food
    _key(g, pygame.K_a)
    assert food[0] not in g.player.inventory and food[1] in g.player.inventory
    assert pup._emberpup_fed is True
    # Kindness, not a weighed deed: with the karma gate on (as shipped) the
    # first feed moves nothing (DEEDS_KARMA_DESIGN 3.1); off, it was +1.
    assert g.karma == karma
    assert g._emberpup_phase == 'outcome'
    _key(g, pygame.K_RETURN)
    assert g._emberpup_phase == 'options'
    # Feeding it again while it is fed costs nothing.
    _key(g, pygame.K_1)
    assert food[1] in g.player.inventory and g._emberpup_phase == 'outcome'


def test_only_identified_food_is_offered():
    g = _game()
    pup, _ = _place_pup(g, 5)
    _clear_food(g)
    known = _food(g, 1)[0]
    _food(g, 1, identified=False)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    assert g._emberpup_food == [known]


def test_no_food_no_crash_and_it_stays_wary():
    g = _game()
    pup, _ = _place_pup(g, 5)
    _clear_food(g)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    assert g._emberpup_phase == 'outcome'
    assert 'nothing it could eat' in g._emberpup_text
    assert pup._emberpup_fed is False
    _key(g, pygame.K_RETURN)
    g.render()                                  # its screen draws with nothing to give
    _key(g, pygame.K_4)                         # still wary
    assert 'does not trust you yet' in g._emberpup_text


def test_i_choose_you_before_food_is_refused():
    from game_states import STATE_EMBERPUP
    g = _game()
    pup, _ = _place_pup(g, 5)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_4)
    assert g.state == STATE_EMBERPUP and g._emberpup_phase == 'outcome'
    assert g.quiz_engine.callback is None
    assert pup in g.monsters and not g.pets


def test_attack_drives_it_off_for_the_run_and_costs_karma():
    from game_states import STATE_PLAYER
    g = _game()
    pup, _ = _place_pup(g, 5)
    g.karma = 3
    corpses = len(g.ground_items)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_3)
    assert pup not in g.monsters and not pup.alive
    assert g._emberpup['outcome'] == 'fled'
    assert g.karma == 2              # -1: no single loss is bigger than one (2026-10-18)
    assert 'never see it again' in g._emberpup_text
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    assert len(g.ground_items) == corpses        # no corpse, no loot
    assert not g.pets
    # Gone for the run: its floor never places it again.
    g._emberpup['spawned'] = False
    g._maybe_spawn_emberpup(5)
    assert not _pups(g)


def test_ignore_leaves_it_on_its_rock_to_help_later():
    from game_states import STATE_PLAYER
    g = _game()
    pup, (dx, dy) = _place_pup(g, 5)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_2)
    assert g.state == STATE_PLAYER
    assert pup in g.monsters and pup.alive and g._emberpup['outcome'] is None
    # Come back and help it after all.
    _food(g, 1)
    g._do_move(dx, dy)
    _key(g, pygame.K_1)
    _key(g, pygame.K_a)
    assert pup._emberpup_fed


def _fed_and_asked(g):
    from game_states import STATE_QUIZ
    pup, _ = _place_pup(g, 6)
    _food(g, 1)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    _key(g, pygame.K_a)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_4)
    assert g.state == STATE_QUIZ
    return pup


def test_i_choose_you_asks_animal_tier_2_needing_2_right():
    from quiz_engine import QuizMode
    g = _game()
    _fed_and_asked(g)
    qe = g.quiz_engine
    assert qe.subject == 'animal' and qe.tier == 2
    assert qe.mode == QuizMode.THRESHOLD and qe.required == 2
    assert qe.callback is not None


def test_passing_makes_it_your_emberpup_with_the_naming_popup():
    from game_states import STATE_EMBERPUP, STATE_PET_NAME_INPUT, STATE_PLAYER
    g = _game()
    pup = _fed_and_asked(g)
    g.quiz_engine._end(success=True)
    assert g.state == STATE_EMBERPUP and g._emberpup_phase == 'outcome'
    assert 'stopped waiting' in g._emberpup_text
    assert pup not in g.monsters
    assert g._emberpup['outcome'] == 'adopted'
    assert len(g.pets) == 1
    pet = g.pets[0]
    assert pet.species_key == 'fire' and pet.species_name == 'Emberpup'
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PET_NAME_INPUT and g._naming_pet is pet
    g.render()                                  # the naming card with its own title
    g._pet_name_input_buffer = 'Ember'
    g._pet_name_input(pygame.K_RETURN, '')
    assert g.state == STATE_PLAYER
    assert pet.name == 'Ember the Emberpup'
    assert any('will not be left behind again' in t for t in _texts(g))
    from chronicle import text_of
    assert any('rock in the rain' in text_of(c) for c in g._chronicle)
    assert not any('soul sphere' in text_of(c).lower() for c in g._chronicle)


def test_failing_it_shies_away_stays_and_can_be_fed_and_asked_again():
    from game_states import STATE_EMBERPUP, STATE_PLAYER, STATE_QUIZ
    g = _game()
    pup = _fed_and_asked(g)
    g.quiz_engine._end(success=False)
    assert g.state == STATE_EMBERPUP and 'shies away' in g._emberpup_text
    _key(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    assert pup in g.monsters and pup.alive and not g.pets
    assert pup._emberpup_fed is False
    # Not fed now: refused.
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_4)
    assert g._emberpup_phase == 'outcome' and g.state == STATE_EMBERPUP
    _key(g, pygame.K_RETURN)
    # Feed it again and try again.
    _food(g, 1)
    karma = g.karma
    _key(g, pygame.K_1)
    _key(g, pygame.K_a)
    assert g.karma == karma                     # the kindness counts once
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_4)
    assert g.state == STATE_QUIZ
    g.quiz_engine._end(success=True)
    assert len(g.pets) == 1


# ---------------------------------------------------------------------------
# Save and load
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


def test_save_and_load_mid_encounter_keeps_it_fed_on_its_rock(tmp_path, monkeypatch):
    from game_states import STATE_EMBERPUP
    name = '__test_emberpup_save__'
    g = _game(name)
    pup, (dx, dy) = _place_pup(g, 5)
    _food(g, 1)
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    _key(g, pygame.K_a)                         # fed; its screen still open
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._emberpup == {'floor': 5, 'spawned': True, 'outcome': None}
    pups = _pups(g2)
    assert len(pups) == 1 and pups[0]._emberpup_fed and pups[0]._emberpup_met
    assert g2._needed_to_finish(pups[0])
    # Walk into it again: its choices, and "I choose you" goes straight to the quiz.
    from game_states import STATE_PLAYER, STATE_QUIZ
    g2.state = STATE_PLAYER
    g2._start_emberpup_encounter(pups[0])
    assert g2.state == STATE_EMBERPUP and g2._emberpup_phase == 'options'
    _key(g2, pygame.K_4)
    assert g2.state == STATE_QUIZ


def test_quitting_mid_quiz_counts_as_a_failed_try(tmp_path, monkeypatch):
    name = '__test_emberpup_save_quiz__'
    g = _game(name)
    _fed_and_asked(g)
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    pups = _pups(g2)
    assert len(pups) == 1 and pups[0]._emberpup_fed is False and not g2.pets


def test_a_save_from_before_it_existed_has_no_emberpup(tmp_path, monkeypatch):
    name = '__test_emberpup_old_save__'
    g = _game(name)
    del g._emberpup
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2._emberpup == {'floor': None, 'spawned': False, 'outcome': None}


def test_the_data_ships_with_the_game():
    with open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8') as f:
        assert "'data/abandoned_emberpup.json'" in f.read()
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters',
                                       'npc_abandoned_emberpup.png'))


def test_first_feed_paid_its_old_point_only_with_the_gate_off(gate_off):
    g = _game()
    pup, _ = _place_pup(g, 5)
    _clear_food(g)
    _food(g, 1)
    karma = g.karma
    g._start_emberpup_encounter(pup)
    _key(g, pygame.K_RETURN)
    _key(g, pygame.K_1)
    _key(g, pygame.K_a)
    assert pup._emberpup_fed is True and g.karma == karma + 1
