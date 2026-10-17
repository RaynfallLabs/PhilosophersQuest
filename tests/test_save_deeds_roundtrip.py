"""Save and load of the deeds register and the structured chronicle
(DEEDS_KARMA_DESIGN 2.7, 7.6, tests 8.6): a round trip keeps both, and an
old save (no _deeds, a chronicle of plain strings) is migrated."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import pygame  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _new(name):
    from main import Game
    return Game(_screen(), player_name=name)


def test_round_trip_keeps_register_and_chronicle():
    import deeds
    import karma
    from chronicle import display_text
    from save_system import delete_save, load_game, save_game
    name = '__test_deeds_roundtrip__'
    try:
        g = _new(name)
        reg = g._deeds
        deeds.record(reg, 'aid.marta', floor=4, block=1, source='marta_ratchatcher')
        deeds.swear(reg, 'aldric_lodestone', to='Sir Aldric', what='Carry it to an altar.',
                    floor=6, block=1)
        karma.adjust(g, 1, kind='legacy', source='marta_ratchatcher')
        g._log_chronicle('Stopped a rat-catcher bleeding out.')
        n_chron = len(g._chronicle)
        assert save_game(g)
        state = load_game(name)
        g2 = _new(name)
        g2.load_state(state)
        assert g2.karma == g.karma
        assert deeds.has(g2._deeds, 'aid.marta')
        assert deeds.oath_status(g2._deeds, 'aldric_lodestone') == 'open'
        assert g2._deeds['karma']['slots'] == {1: 'marta_ratchatcher'}
        assert len(g2._deeds['karma']['ledger']) == 1
        assert len(g2._chronicle) == n_chron
        assert display_text(g2._chronicle[-1]) == \
            f'Stopped a rat-catcher bleeding out. (L{g.dungeon_level})'
    finally:
        delete_save(name)


def test_round_trip_settles_an_open_encounter_quiz():
    import copy
    import deeds
    from save_system import delete_save, load_game, save_game, settle_unfinished_actions
    from test_encounter_flow import QUIZ_ENC, _open
    name = '__test_deeds_quiz_settle__'
    try:
        g = _new(name)
        g.monsters = []
        _open(g, copy.deepcopy(QUIZ_ENC))
        g._npc_encounter_input(pygame.K_RETURN)
        g._npc_encounter_input(pygame.K_1)
        settle_unfinished_actions(g)          # what an exit save does first
        assert save_game(g)
        g2 = _new(name)
        g2.load_state(load_game(name))
        assert deeds.has(g2._deeds, 'lost.anselm')
        assert QUIZ_ENC['tag'] in g2._encountered_flavor_npcs
    finally:
        delete_save(name)


def test_old_save_without_deeds_is_migrated():
    import deeds
    from chronicle import display_text
    from save_system import delete_save, load_game, save_game
    name = '__test_deeds_old_save__'
    try:
        g = _new(name)
        g.player.deepest_floor_reached = 15
        g.dungeon_level = 15
        lvl, enc = next((lv, e) for lv, e in g._npc_encounter_levels.items() if 11 <= lv <= 19)
        g._encountered_npcs = {enc['tag']}
        assert save_game(g)
        state = load_game(name)
        # As a save from before the redesign looked:
        state.pop('_deeds')
        state['_chronicle'] = ['Found: Bronze Bull Idol (L8)', 'A line with no floor']
        g2 = _new(name)
        g2.load_state(state)
        reg = g2._deeds
        assert deeds.has(reg, f"met.{enc['tag']}")
        assert deeds.first(reg, f"met.{enc['tag']}")['floor'] == lvl
        # Block 1 is past; block 2's anchor was already met, so it is closed too.
        assert reg['karma']['slots'] == {1: 'legacy', 2: 'legacy'}
        assert [e['kind'] for e in g2._chronicle] == ['legacy', 'legacy']
        assert g2._chronicle[0]['floor'] == 8 and g2._chronicle[0]['text'] == 'Found: Bronze Bull Idol'
        assert [display_text(e) for e in g2._chronicle] == state['_chronicle']
        # The Journal shows their words; its Timeline puts the floor in a
        # header instead of an "(L8)" tail.
        g2._encyclopedia_load_entries('journal')
        assert [e['name'] for e in g2.encyclopedia_entries] == [
            'Found: Bronze Bull Idol', 'A line with no floor']
    finally:
        delete_save(name)


def test_round_trip_keeps_the_road_escorts_and_pending_queue():
    """Phase 2: _road, escorts and the pending queue survive save and load."""
    import copy
    import deeds
    from save_system import delete_save, load_game, save_game
    from test_escort import ESCORT_ENC
    name = '__test_road_escort_roundtrip__'
    try:
        g = _new(name)
        g.monsters = []
        g._npc_encounter_active = copy.deepcopy(ESCORT_ENC)
        g._apply_outcome_deeds(g._npc_encounter_active['options'][0], 'fx_lena')
        g._apply_outcome_deeds({'delayed': [{'after_floors': [2, 4], 'reward': {
            'type': 'effect', 'effect': 'blessed', 'duration': 20}}]}, 'fx_lena')
        g._npc_encounter_active = None
        esc = g.escorts[0]
        esc.hp -= 7
        road_before = copy.deepcopy(g._road)
        pending_before = copy.deepcopy(g._deeds['pending'])
        assert save_game(g)
        g2 = _new(name)
        g2.load_state(load_game(name))
        assert g2._road == road_before
        assert g2._deeds['pending'] == pending_before
        assert len(g2.escorts) == 1 and g2.pets == []
        e2 = g2.escorts[0]
        assert (e2.escort_id, e2.name, e2.hp, e2.floors_left, e2.floor) == \
            ('lena', 'Lena', esc.hp, esc.floors_left, esc.floor)
        assert (e2.x, e2.y) in g2._occupants()
        assert deeds.has(g2._deeds, 'flag.escorting.lena')
        # and it still finishes after the load
        g2._change_level(g2.dungeon_level + 1, enter_from_top=True)
        assert g2.escorts == [] and deeds.has(g2._deeds, 'saved.lena')
    finally:
        delete_save(name)


def test_a_save_from_before_the_road_keeps_its_legacy_encounter_plan():
    from save_system import delete_save, load_game, save_game
    name = '__test_road_old_save__'
    try:
        g = _new(name)
        plan = dict(g._npc_encounter_levels)
        flavor = dict(g._flavor_encounter_levels)
        assert save_game(g)
        state = load_game(name)
        state.pop('_road')
        state.pop('escorts')
        g2 = _new(name)
        g2.load_state(state)
        assert g2._road['enabled'] is False and g2._road['slots'] == {}
        assert isinstance(g2._road['seed'], int)
        assert g2.escorts == []
        assert set(g2._npc_encounter_levels) == set(plan)
        assert set(g2._flavor_encounter_levels) == set(flavor)
    finally:
        delete_save(name)
