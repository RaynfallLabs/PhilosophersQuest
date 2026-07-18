import pygame

from game_input import InputMixin
from game_states import STATE_PLAYER


class _CharacterSheetHarness(InputMixin):
    def __init__(self):
        self.state = "character_sheet"
        self._charsheet_focus = "loadout"
        self._charsheet_loadout_idx = 0
        self._charsheet_pack_idx = 0
        self._charsheet_action_idx = 0
        self._charsheet_action_source = "loadout"
        self._charsheet_pack_filter = "all"
        self._charsheet_pack_scroll = 4
        self.activated = []

    def _charsheet_clamp(self):
        self._charsheet_loadout_idx = max(0, min(self._charsheet_loadout_idx, 3))
        self._charsheet_pack_idx = max(0, min(self._charsheet_pack_idx, 9))
        self._charsheet_action_idx = max(0, min(self._charsheet_action_idx, 2))

    def _charsheet_focus_actions(self):
        if self._charsheet_focus in ("loadout", "pack"):
            self._charsheet_action_source = self._charsheet_focus
        self._charsheet_focus = "actions"
        self._charsheet_clamp()

    def _charsheet_activate_action(self, action_id=None):
        self.activated.append(action_id)
        return True

    def _charsheet_current_pack_filter(self):
        return self._charsheet_pack_filter

    def _charsheet_set_pack_filter(self, active):
        if active != self._charsheet_pack_filter:
            self._charsheet_pack_idx = 0
            self._charsheet_pack_scroll = 0
        self._charsheet_pack_filter = active
        self._charsheet_focus = "pack"
        self._charsheet_action_source = "pack"
        self._charsheet_clamp()

    def _charsheet_cycle_pack_filter(self, delta):
        filters = ("all", "gear", "food", "lore")
        idx = filters.index(self._charsheet_pack_filter)
        self._charsheet_set_pack_filter(filters[(idx + delta) % len(filters)])


def test_character_sheet_left_right_focus_moves_between_panels():
    menu = _CharacterSheetHarness()

    menu._character_sheet_input(pygame.K_RIGHT)
    assert menu._charsheet_focus == "pack"

    menu._character_sheet_input(pygame.K_RIGHT)
    assert menu._charsheet_focus == "actions"
    assert menu._charsheet_action_source == "pack"

    menu._character_sheet_input(pygame.K_LEFT)
    assert menu._charsheet_focus == "pack"


def test_character_sheet_arrows_move_active_panel_highlight():
    menu = _CharacterSheetHarness()

    menu._character_sheet_input(pygame.K_DOWN)
    assert menu._charsheet_loadout_idx == 1

    menu._charsheet_focus = "pack"
    menu._character_sheet_input(pygame.K_PAGEDOWN)
    assert menu._charsheet_pack_idx == 6

    menu._charsheet_focus = "actions"
    menu._character_sheet_input(pygame.K_END)
    assert menu._charsheet_action_idx == 2


def test_character_sheet_enter_and_shortcuts_activate_actions():
    menu = _CharacterSheetHarness()

    menu._character_sheet_input(pygame.K_RETURN)
    assert menu._charsheet_focus == "actions"
    assert menu._charsheet_action_source == "loadout"

    menu._character_sheet_input(pygame.K_RETURN)
    assert menu.activated == [None]

    menu._character_sheet_input(pygame.K_x)
    menu._character_sheet_input(pygame.K_d)
    assert menu.activated[-2:] == ["lore", "drop"]


def test_character_sheet_pack_filter_keys_are_wired():
    menu = _CharacterSheetHarness()
    menu._charsheet_pack_idx = 7

    menu._character_sheet_input(pygame.K_3)

    assert menu._charsheet_pack_filter == "food"
    assert menu._charsheet_focus == "pack"
    assert menu._charsheet_action_source == "pack"
    assert menu._charsheet_pack_idx == 0
    assert menu._charsheet_pack_scroll == 0


def test_character_sheet_tab_cycles_pack_filters():
    menu = _CharacterSheetHarness()

    menu._character_sheet_input(pygame.K_TAB)
    assert menu._charsheet_pack_filter == "gear"


def test_character_sheet_escape_closes_to_player_state():
    menu = _CharacterSheetHarness()

    menu._character_sheet_input(pygame.K_ESCAPE)

    assert menu.state == STATE_PLAYER
