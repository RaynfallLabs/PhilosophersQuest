"""Headless smoke test: every menu / overlay screen renders without error.

Added with the pre-v3.0 audit (2026-10-04) after ~2,400 lines of legacy
render code were deleted from game_render.py. pytest cannot judge how a
screen LOOKS, but it can prove that each state's draw path still runs end
to end on a real Game with a stocked inventory, at two window sizes.

2026-10-15 (UI art foundation): six screens used to stay on STATE_PLAYER
and silently count as "drawn" -- spell, cook, power, pet and study had
nothing to show on the old bare stock, and hint (Recall Lore) bounced back
to play inside render() because no hint was set. The game is now the
capture tool's representative mid-game hero (tools/ui/capture.py
``build_game``: known spells, ingredients, a corpse, active powers, a pet,
a missed-question history), the hint card gets a hint, and every screen
must REALLY be on its state both before and after it is drawn.

A failure here means a screen raises when drawn -- it would crash in play --
or a screen silently stopped opening.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import importlib.util  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

# Every test starts with an empty UI art kit and restores the previous one
# (the capture harness loads assets/ui/; GROUNDWORK_REVIEW 9).
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')


def _load_capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


def _menu_states(g):
    """(label, setup callable, expected state) for every screen that can be
    opened from a plain mid-game state."""
    import game_states as S

    def set_state(name, **attrs):
        def _do():
            for k, v in attrs.items():
                setattr(g, k, v)
            g.state = getattr(S, name)
        return _do

    first_item = next((i for i in g.player.inventory
                       if hasattr(i, 'id_level')), g.player.inventory[0])
    return [
        ('equip',        g._open_equip_menu,        S.STATE_EQUIP_MENU),
        ('kit',          g._open_kit_panel,         S.STATE_KIT),
        ('discoveries',  g._open_discoveries,       S.STATE_DISCOVERIES),
        ('wand',         g._open_wand_menu,         S.STATE_WAND_MENU),
        ('spell',        g._open_spell_menu,        S.STATE_SPELL_MENU),
        ('scroll',       g._open_scroll_menu,       S.STATE_SCROLL_MENU),
        ('identify',     g._open_identify_menu,     S.STATE_IDENTIFY_MENU),
        ('cook',         g._open_cook_menu,         S.STATE_COOK_MENU),
        ('eat',          g._open_eat_menu,          S.STATE_EAT_MENU),
        ('quaff',        g._open_quaff_menu,        S.STATE_QUAFF_MENU),
        ('throw',        g._open_throw_menu,        S.STATE_THROW_MENU),
        ('drop',         g._open_drop_menu,         S.STATE_DROP_MENU),
        ('examine',      g._open_examine_menu,      S.STATE_EXAMINE),
        ('power',        g._open_power_menu,        S.STATE_POWER_MENU),
        ('pet',          g._open_pet_menu,          S.STATE_PET_MENU),
        ('charsheet',    g._open_character_sheet,   S.STATE_CHARACTER_SHEET),
        ('quirks',       g._open_quirks_screen,     S.STATE_QUIRKS),
        ('encyclopedia', g._open_encyclopedia,      S.STATE_ENCYCLOPEDIA),
        ('study',        g._open_study_journal,     S.STATE_STUDY),
        ('help',         set_state('STATE_HELP'),   S.STATE_HELP),
        ('hint',         set_state('STATE_HINT', _lore_hint_text=(
            "The giant rat fears fire; its burrows run under every granary."),
            _lore_hint_chain=3),                    S.STATE_HINT),
        ('confirm_exit', set_state('STATE_CONFIRM_EXIT'), S.STATE_CONFIRM_EXIT),
        ('exit_quest',   set_state('STATE_EXIT_QUEST'),   S.STATE_EXIT_QUEST),
        ('abandon',      set_state('STATE_ABANDON_QUEST'), S.STATE_ABANDON_QUEST),
        ('chicken',      set_state('STATE_CHICKEN'),       S.STATE_CHICKEN),
        ('lore_item',    set_state('STATE_LORE', _lore_subject=first_item), S.STATE_LORE),
        ('lore_corpse',  set_state('STATE_LORE', _lore_subject=g._capture_corpse),
         S.STATE_LORE),
        ('player',       set_state('STATE_PLAYER'), S.STATE_PLAYER),
    ]


def _stocked_game(size=(1280, 720)):
    cap = _load_capture()
    screen = pygame.display.set_mode(size)
    return cap.build_game(screen, size)


@pytest.mark.parametrize('size', [(1280, 720), (1920, 1080)])
def test_every_menu_screen_renders(size):
    import game_states as S
    cap = _load_capture()
    with cap.harness():
        g = _stocked_game(size)
        failures = []
        drawn = []
        for label, setup, expected in _menu_states(g):
            g.state = S.STATE_PLAYER
            try:
                setup()
            except Exception as e:   # opening a screen must not raise either
                failures.append(f"{label}: open raised {type(e).__name__}: {e}")
                continue
            if g.state != expected:
                failures.append(f"{label}: did not open (state {g.state!r}, "
                                f"expected {expected!r})")
                continue
            try:
                g.render()
            except Exception as e:
                failures.append(f"{label} ({expected}): render raised "
                                f"{type(e).__name__}: {e}")
                continue
            if g.state != expected:
                failures.append(f"{label}: render left the screen "
                                f"(state {g.state!r})")
                continue
            drawn.append(label)
    assert not failures, "\n".join(failures)
    assert len(drawn) == len(_menu_states(g))


def test_lore_dossier_scroll_and_tab_keys_do_not_raise():
    import game_states as S
    cap = _load_capture()
    with cap.harness():
        g = _stocked_game()
        g._lore_subject = g._capture_corpse
        g.state = S.STATE_LORE
        for key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP, pygame.K_PAGEDOWN,
                    pygame.K_END, pygame.K_HOME):
            g._lore_input(key)
            g.render()
        assert g.state == S.STATE_LORE
