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
        # The Chronicle tab shows them exactly as before.
        g2._encyclopedia_load_entries('chronicle')
        assert [e['name'] for e in g2.encyclopedia_entries] == state['_chronicle']
    finally:
        delete_save(name)
