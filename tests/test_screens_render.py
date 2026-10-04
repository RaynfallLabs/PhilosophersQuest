"""Headless smoke test: every menu / overlay screen renders without error.

Added with the pre-v3.0 audit (2026-10-04) after ~2,400 lines of legacy
render code were deleted from game_render.py. pytest cannot judge how a
screen LOOKS, but it can prove that each state's draw path still runs end
to end on a real Game with a stocked inventory, at two window sizes.

A failure here means a screen raises when drawn -- it would crash in play.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


def _stocked_game(size=(1280, 720)):
    import layout
    from main import Game
    from items import (load_items, Corpse, pick_random_weapon_for_floor,
                       pick_random_armor_for_floor, pick_random_shield_for_floor)
    import random

    screen = pygame.display.set_mode(size)
    layout.update(*size)
    g = Game(screen, player_name='SmokeTest')
    if hasattr(g, 'on_resize'):
        g.on_resize(*size)
    rng = random.Random(7)
    p = g.player
    p.max_carry = 10_000 if hasattr(p, 'max_carry') else None
    stock = []
    for cls, n in (('potion', 3), ('scroll', 3), ('wand', 2), ('spellbook', 2),
                   ('food', 3), ('accessory', 3), ('ammo', 1)):
        try:
            stock += load_items(cls)[:n]
        except Exception:
            pass
    for maker in (pick_random_weapon_for_floor, pick_random_shield_for_floor):
        item = maker(5, rng)
        if item is not None:
            stock.append(item)
    armor = pick_random_armor_for_floor(5, rng, slot='body')
    if armor is not None:
        stock.append(armor)
    import copy
    for it in stock:
        inst = copy.copy(it)
        if len(p.inventory) < 24:
            p.inventory.append(inst)
    corpse = Corpse('giant rat', 'giant_rat', p.x, p.y)
    p.inventory.append(corpse)
    g._smoke_corpse = corpse
    return g


def _menu_states(g):
    """(label, setup callable) for every screen that can be opened from a
    plain mid-game state. Each setup leaves g.state on the screen."""
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
        ('equip',        g._open_equip_menu),
        ('kit',          g._open_kit_panel),
        ('discoveries',  g._open_discoveries),
        ('wand',         g._open_wand_menu),
        ('spell',        g._open_spell_menu),
        ('scroll',       g._open_scroll_menu),
        ('identify',     g._open_identify_menu),
        ('cook',         g._open_cook_menu),
        ('eat',          g._open_eat_menu),
        ('quaff',        g._open_quaff_menu),
        ('throw',        g._open_throw_menu),
        ('drop',         g._open_drop_menu),
        ('examine',      g._open_examine_menu),
        ('power',        g._open_power_menu),
        ('pet',          g._open_pet_menu),
        ('charsheet',    g._open_character_sheet),
        ('quirks',       g._open_quirks_screen),
        ('encyclopedia', g._open_encyclopedia),
        ('study',        g._open_study_journal),
        ('help',         set_state('STATE_HELP')),
        ('hint',         set_state('STATE_HINT')),
        ('confirm_exit', set_state('STATE_CONFIRM_EXIT')),
        ('exit_quest',   set_state('STATE_EXIT_QUEST')),
        ('abandon',      set_state('STATE_ABANDON_QUEST')),
        ('chicken',      set_state('STATE_CHICKEN')),
        ('lore_item',    set_state('STATE_LORE', _lore_subject=first_item)),
        ('lore_corpse',  set_state('STATE_LORE', _lore_subject=g._smoke_corpse)),
        ('player',       set_state('STATE_PLAYER')),
    ]


@pytest.mark.parametrize('size', [(1280, 720), (1920, 1080)])
def test_every_menu_screen_renders(size):
    import game_states as S
    g = _stocked_game(size)
    failures = []
    drawn = 0
    for label, setup in _menu_states(g):
        g.state = S.STATE_PLAYER
        try:
            setup()
        except Exception as e:   # opening a screen must not raise either
            failures.append(f"{label}: open raised {type(e).__name__}: {e}")
            continue
        opened = g.state
        try:
            g.render()
            drawn += 1
        except Exception as e:
            failures.append(f"{label} ({opened}): render raised "
                            f"{type(e).__name__}: {e}")
    assert not failures, "\n".join(failures)
    assert drawn >= 20


def test_lore_dossier_scroll_and_tab_keys_do_not_raise():
    import game_states as S
    g = _stocked_game()
    g._lore_subject = g._smoke_corpse
    g.state = S.STATE_LORE
    for key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP, pygame.K_PAGEDOWN,
                pygame.K_END, pygame.K_HOME):
        g._lore_input(key)
        g.render()
    assert g.state == S.STATE_LORE
