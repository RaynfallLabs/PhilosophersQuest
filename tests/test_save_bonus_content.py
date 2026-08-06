"""Save-bonus CONTENT tests — the conversions feeding Player.save_bonus_for:
equipped gear, converted quirks (Perseus), monster-family masteries, build
affinity, and the flagship amulet data conversions."""
import os
import sys

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def test_equipped_gear_save_bonus_is_read():
    from player import Player
    p = Player()

    class _Stub:
        save_bonus = {'cat': 'CON', 'amount': 2}

    p.amulet_slot = _Stub()
    assert p.save_bonus_for('CON') == 2
    assert p.save_bonus_for('WIS') == 0


def test_perseus_quirk_grants_all_save_bonus():
    from player import Player
    p = Player()
    p.quirk_progress = {'save_bonus_all': 2}     # what the converted Perseus quirk sets
    assert p.save_bonus_for('CON') == 2
    assert p.save_bonus_for('WIS') == 2
    assert p.save_bonus_for('DEX') == 2


# (test_family_mastery_blessings_converted_to_saves removed 2026-08-06 —
# monster-family masteries were retired with the one-question identify
# redesign.)


def test_flagship_amulets_have_save_bonus():
    from items import load_items
    accs = load_items('accessory')
    insight = next((a for a in accs if a.id == 'amulet_of_insight'), None)
    fort = next((a for a in accs if a.id == 'amulet_of_fortitude'), None)
    assert insight is not None and insight.save_bonus == {'cat': 'WIS', 'amount': 3}
    assert fort is not None and fort.save_bonus == {'cat': 'CON', 'amount': 3}


def test_build_affinity_applied_from_name():
    from main import Game
    g = Game(_screen(), player_name='leonidas of sparta')
    assert g.player.save_affinity == {'CON': 2}
    assert g.player.save_bonus_for('CON') == 2
    # A plain (non-build) name gets no affinity.
    g2 = Game(_screen(), player_name='some random kid')
    assert g2.player.save_affinity == {}


def test_old_save_is_backwards_compatible():
    """An OLD save (no save-bonus attrs + the legacy perseus_active flag)
    must load without crashing and migrate cleanly."""
    from main import Game
    from save_system import save_game, load_game, delete_save
    name = '__test_savebonus_compat__'
    try:
        g = Game(_screen(), player_name=name)   # unique save-file key (no collision)
        p = g.player
        # Make the player look pre-upgrade: drop the new attrs, restore old data.
        for attr in ('_save_bonus', 'save_affinity', '_save_guard'):
            if hasattr(p, attr):
                delattr(p, attr)
        p.quirk_progress = {'perseus_active': True}
        assert save_game(g)
        state = load_game(name)
        assert state is not None
        # Pretend this old save belonged to a build, to exercise affinity re-apply.
        state['player_name'] = 'leonidas of sparta'

        g2 = Game(_screen(), player_name='leonidas of sparta')
        g2.load_state(state)             # must not raise
        p2 = g2.player
        # New attrs seeded
        assert isinstance(getattr(p2, '_save_bonus', None), dict)
        assert isinstance(getattr(p2, '_save_guard', None), dict)
        # Perseus legacy flag migrated to the all-saves bonus
        assert p2.quirk_progress.get('save_bonus_all') == 2
        # Build affinity re-applied (load_state replaced the player)
        assert p2.save_affinity == {'CON': 2}
        # And it all composes, capped, without error
        assert p2.save_bonus_for('WIS') == 2      # perseus-all 2
        assert p2.save_bonus_for('CON') == 4      # affinity 2 + perseus-all 2
    finally:
        delete_save(name)
