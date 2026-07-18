"""Game's non-menu input-handling methods, extracted from main.py.

This module defines :class:`InputMixin`, which the real ``Game`` class inherits
alongside :class:`game_menus.MenuMixin` and :class:`game_render.RenderMixin`.
The mixin owns the top-level pygame event router (``handle_event``), the main
player-turn input (``_player_input``), targeting cursor input
(``_target_input``), and all per-state modal/popup input handlers (confirm
dialogs, quiz input, drop-gold numeric input, lore/help/judgment/shop/
encyclopedia/study/quirks/character-sheet/cow/npc/mystery/xyzzy screens).

Menu input handlers (``*_menu_input``) live in :class:`game_menus.MenuMixin`,
NOT here. Action-layer methods that input handlers invoke (``self._do_move``,
``self._pickup``, ``self._confirm_wand_target``, etc.) remain on Game and are
resolved through Python's MRO on the concrete ``Game`` subclass. Class-level
constants accessed by these handlers via ``self.`` (``_COW_MOO_MESSAGES``,
``_STUDY_SUBJECTS``, ``_AZ_KEYS``, etc.) remain on Game as well; the two
constants owned exclusively by handlers in this module (``_MOVE_KEYS`` and
``_TARGET_MOVE_KEYS``) are defined here.
"""
from __future__ import annotations

import pygame

import sound_system as _snd
from dungeon import ALTAR, FOUNTAIN, GRAVE, THRONE
from quiz_engine import QuizState
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_EQUIP_MENU, STATE_KIT, STATE_DISCOVERIES,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_CONFIRM_EXIT, STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
    STATE_VICTORY, STATE_DEAD, STATE_REVIEW_MISSED,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_HELP, STATE_LORE,
    STATE_SPELL_MENU, STATE_HINT, STATE_EXAMINE,
    STATE_ENCYCLOPEDIA, STATE_DROP_MENU, STATE_DROP_GOLD_INPUT, STATE_DROP_QTY_INPUT,
    STATE_STORY_POPUP, STATE_MYSTERY_APPROACH, STATE_SHOP, STATE_POWER_MENU,
    STATE_HACK_REALITY, STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM,
    STATE_THROW_MENU, STATE_QUIRKS, STATE_CHARACTER_SHEET,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_JUDGMENT, STATE_STUDY,
    STATE_PRAY, STATE_PET_NAME_INPUT,
    STATE_PET_MENU, STATE_PET_FEED, STATE_PET_HEAL, STATE_PET_SPECIALS,
    STATE_QA_WARP_INPUT, STATE_ASCENSION,
)


class InputMixin:
    # ------------------------------------------------------------------
    # Top-level event router
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            # A QUIT can come from the window-X, the confirm-exit dialog (which
            # sets _quit_confirmed before posting it), OR a SPURIOUS OS/display
            # event (monitor sleep, focus loss, RDP, screensaver) that must NOT
            # silently end the run. Only a confirmed quit -- or the death/victory
            # screens -- exits outright; anything else routes to the VISIBLE
            # confirm dialog so a stray QUIT can be cancelled, and is logged so a
            # "the window just closed" report names itself.
            if getattr(self, '_quit_confirmed', False):
                return False
            if self.state in (STATE_DEAD, STATE_VICTORY):
                return False
            if self.state != STATE_CONFIRM_EXIT:
                try:
                    from game_log import log_info
                    log_info(f"QUIT event received in state={self.state} -> routed to "
                             f"confirm-exit (NOT exiting). If you didn't click the X, "
                             f"this was a spurious OS/display/focus event.")
                except Exception:
                    pass
                self.state = STATE_CONFIRM_EXIT
            return True
        if event.type == pygame.WINDOWRESIZED:
            self.on_resize(event.x, event.y)
            return True
        if event.type != pygame.KEYDOWN:
            return True

        key = event.key

        if key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return True
        if key == pygame.K_F2:
            self._debug_overlay = not self._debug_overlay
            return True

        if key == pygame.K_ESCAPE:
            if self.state == STATE_QUIZ:
                # Cancel the active quiz — treat as chain-0 failure
                self.quiz_engine._end(success=False)
                return True
            if self.state in (STATE_EQUIP_MENU, STATE_KIT, STATE_DISCOVERIES,
                              STATE_WAND_MENU, STATE_SCROLL_MENU,
                              STATE_IDENTIFY_MENU, STATE_COOK_MENU,
                              STATE_CONFIRM_EXIT, STATE_TARGET,
                              STATE_EXIT_QUEST, STATE_ABANDON_QUEST, STATE_CHICKEN,
                              STATE_EAT_MENU, STATE_QUAFF_MENU, STATE_THROW_MENU,
                              STATE_HELP, STATE_LORE,
                              STATE_SPELL_MENU, STATE_HINT, STATE_HACK_REALITY,
                              STATE_XYZZY_INPUT, STATE_XYZZY_CONFIRM, STATE_QUIRKS,
                              STATE_COW_ENCOUNTER,
                              STATE_CHARACTER_SHEET,
                              STATE_EXAMINE, STATE_ENCYCLOPEDIA,
                              STATE_DROP_MENU, STATE_DROP_GOLD_INPUT, STATE_DROP_QTY_INPUT,
                              STATE_MYSTERY_APPROACH, STATE_SHOP,
                              STATE_POWER_MENU, STATE_STUDY,
                              STATE_PET_MENU, STATE_ASCENSION,
                              STATE_PRAY, STATE_JUDGMENT):
                if self.state == STATE_MYSTERY_APPROACH:
                    self._active_mystery_altar = None
                if self.state == STATE_TARGET:
                    self._throw_targeting = False
                    self._throw_potion = None
                    self._observe_targeting = False
                    self._wand_targeting = False
                    self._pending_wand = None
                    self._power_targeting = False
                    self._pending_power = None
                    self._pet_special_targeting = False
                    self._pending_pet_special = None
                    self._pending_pet_special_pet = None
                    # Refund MP if cancelling mid-targeted-spell (A2-3 fix).
                    # _cast_spell deducts MP before STATE_TARGET; ESC must give it back.
                    _pending_spell = getattr(self, '_pending_spell', None)
                    if _pending_spell is not None:
                        try:
                            _mp_cost = int(_pending_spell.get('mp_cost', 0))
                            if _mp_cost > 0:
                                self.player.mp = min(self.player.max_mp,
                                                      self.player.mp + _mp_cost)
                                self.add_message(
                                    f"You hold the {_pending_spell.get('name', 'spell')} unspoken — your magic returns.",
                                    'info')
                        except (AttributeError, TypeError, ValueError):
                            pass
                        self._pending_spell = None
                        self._pending_spell_id = None
                self.state = STATE_PLAYER
                return True
            if self.state == STATE_STORY_POPUP:
                self.state = self.popup_next_state
                return True
            if self.state == STATE_NPC_ENCOUNTER:
                # Cancel the moral encounter cleanly — the NPC stays on the
                # floor so the player can return later. _close_npc_encounter
                # (with resolved=False) clears all overlay state without
                # consuming the encounter.
                if hasattr(self, '_close_npc_encounter'):
                    self._close_npc_encounter(resolved=False)
                else:
                    self.state = STATE_PLAYER
                return True
            if self.state == STATE_PLAYER:
                self.state = STATE_CONFIRM_EXIT
                return True
            if self.state == STATE_REVIEW_MISSED:
                self.state = STATE_DEAD
                return True
            if self.state in (STATE_DEAD, STATE_VICTORY):
                return False
            if self.state == STATE_PET_NAME_INPUT:
                # ESC on pet-name popup: skip naming, keep default species name.
                self._pet_name_input(key, '')
                return True
            if self.state in (STATE_PET_FEED, STATE_PET_HEAL, STATE_PET_SPECIALS):
                # ESC on a pet sub-menu returns to the main pet menu.
                self.state = STATE_PET_MENU
                return True
            if self.state == STATE_QA_WARP_INPUT:
                self.state = STATE_PLAYER
                self._qa_warp_input = ''
                return True
            return False

        if self.state == STATE_PLAYER:
            # Keys checked by unicode to handle shift-modified chars
            if event.unicode == '>':
                self._descend_stairs()
                return True
            if event.unicode == '<':
                self._ascend_stairs()
                return True
            if event.unicode == '?':
                self.state = STATE_HELP
                return True
            if event.unicode == '@':
                self._open_character_sheet()
                return True
            if event.unicode == 'P':
                # Shift+P opens the pet menu (lowercase p is pickup/disarm).
                self._open_pet_menu()
                return True
            if event.unicode == 'I' and getattr(self.player, 'qa_tools', False):
                # Titivillus QA build: toggle immortality. No quiz, no chronicle.
                self.player.immortal = not getattr(self.player, 'immortal', False)
                state_str = "ON" if self.player.immortal else "OFF"
                self.add_message(f"[QA] Immortal mode {state_str}.", 'info')
                return True
            if event.unicode == 'W' and getattr(self.player, 'qa_tools', False):
                # Titivillus QA build: open floor-warp prompt.
                self._qa_warp_input = ''
                self.state = STATE_QA_WARP_INPUT
                return True
            self._player_input(key)
        elif self.state == STATE_TARGET:
            self._target_input(key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(key)
        elif self.state == STATE_EQUIP_MENU:
            self._equip_menu_input(key)
        elif self.state == STATE_KIT:
            self._kit_input(key)
        elif self.state == STATE_DISCOVERIES:
            self._discoveries_input(key)
        elif self.state == STATE_WAND_MENU:
            self._wand_menu_input(key)
        elif self.state == STATE_SCROLL_MENU:
            self._scroll_menu_input(key)
        elif self.state == STATE_SPELL_MENU:
            self._spell_menu_input(key)
        elif self.state == STATE_IDENTIFY_MENU:
            self._identify_menu_input(key)
        elif self.state == STATE_COOK_MENU:
            self._cook_menu_input(key)
        elif self.state == STATE_ASCENSION:
            self._ascension_menu_input(key)
        elif self.state == STATE_EAT_MENU:
            self._eat_menu_input(key)
        elif self.state == STATE_QUAFF_MENU:
            self._quaff_menu_input(key)
        elif self.state == STATE_THROW_MENU:
            self._throw_menu_input(key)
        elif self.state == STATE_PRAY:
            self._prayer_menu_input(key)
        elif self.state == STATE_HELP:
            self._help_input(key)
        elif self.state == STATE_LORE:
            self._lore_input(key)
        elif self.state == STATE_EXAMINE:
            self._examine_menu_input(key)
        elif self.state == STATE_ENCYCLOPEDIA:
            self._encyclopedia_input(key)
        elif self.state == STATE_HINT:
            self.state = STATE_PLAYER   # any key dismisses hint overlay
        elif self.state == STATE_HACK_REALITY:
            self.state = STATE_PLAYER   # any key dismisses hack reality overlay
        elif self.state == STATE_XYZZY_INPUT:
            self._xyzzy_input(key, event.unicode)
        elif self.state == STATE_PET_NAME_INPUT:
            self._pet_name_input(key, event.unicode)
        elif self.state == STATE_PET_MENU:
            self._pet_menu_input(key)
        elif self.state == STATE_PET_FEED:
            self._pet_feed_input(key)
        elif self.state == STATE_PET_HEAL:
            self._pet_heal_input(key)
        elif self.state == STATE_PET_SPECIALS:
            self._pet_specials_input(key)
        elif self.state == STATE_QA_WARP_INPUT:
            self._qa_warp_input_handler(key, event.unicode)
        elif self.state == STATE_XYZZY_CONFIRM:
            self._xyzzy_confirm_input(key)
        elif self.state == STATE_QUIRKS:
            self._quirks_input(key)
        elif self.state == STATE_COW_ENCOUNTER:
            self._cow_encounter_input(key)
        elif self.state == STATE_CHARACTER_SHEET:
            self._character_sheet_input(key)
        elif self.state == STATE_DROP_MENU:
            self._drop_menu_input(key)
        elif self.state == STATE_DROP_GOLD_INPUT:
            self._drop_gold_input(key, event.unicode)
        elif self.state == STATE_DROP_QTY_INPUT:
            self._drop_qty_input(key, event.unicode)
        elif self.state == STATE_STORY_POPUP:
            self.state = self.popup_next_state   # any key advances
        elif self.state == STATE_CONFIRM_EXIT:
            self._confirm_exit_input(key)
        elif self.state == STATE_EXIT_QUEST:
            self._exit_quest_input(key)
        elif self.state == STATE_ABANDON_QUEST:
            self._abandon_quest_input(key)
        elif self.state == STATE_CHICKEN:
            self._chicken_input(key)
        elif self.state == STATE_MYSTERY_APPROACH:
            self._mystery_approach_input(key, event.unicode)
        elif self.state == STATE_SHOP:
            self._shop_input(key)
        elif self.state == STATE_POWER_MENU:
            self._power_menu_input(key)
        elif self.state == STATE_NPC_ENCOUNTER:
            self._npc_encounter_input(key)
        elif self.state == STATE_JUDGMENT:
            self._judgment_input(key)
        elif self.state == STATE_STUDY:
            self._study_input(key)
        elif self.state == STATE_DEAD:
            if key == pygame.K_r and self.missed_questions:
                self._review_idx = 0
                self.state = STATE_REVIEW_MISSED
        elif self.state == STATE_REVIEW_MISSED:
            if key == pygame.K_PAGEUP:
                self._review_scroll = max(0, getattr(self, '_review_scroll', 0) - 8)
            elif key == pygame.K_PAGEDOWN:
                self._review_scroll = getattr(self, '_review_scroll', 0) + 8
            elif key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_SPACE, pygame.K_RETURN):
                self._review_idx = min(self._review_idx + 1, len(self.missed_questions) - 1)
                self._review_scroll = 0
            elif key in (pygame.K_LEFT, pygame.K_UP):
                self._review_idx = max(0, self._review_idx - 1)
                self._review_scroll = 0

        return True

    # ------------------------------------------------------------------
    # Main player-turn input
    # ------------------------------------------------------------------

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1),
        pygame.K_DOWN:  (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0),
    }

    def _player_input(self, key: int):

        # Sleep / paralysis: no action possible. Turn passes, status ticks down.
        # Damage still wakes from sleep via Player.take_damage.
        if self.player.has_effect('sleeping'):
            self.add_message("You are fast asleep -- you cannot act.", 'warning')
            self._advance_turn()
            return
        if self.player.has_effect('paralyzed'):
            self.add_message("You are paralyzed -- you cannot act.", 'danger')
            self._advance_turn()
            return

        if key == pygame.K_PERIOD:
            qs = getattr(self, 'quirk_system', None)
            near = any(m.alive for m in self.monsters)
            if qs:
                qs.on_wait(near_monsters=near)
            # Meditation: restore 1 MP when waiting if no monsters are adjacent
            _adj_monsters = [
                m for m in self.monsters
                if m.alive and abs(m.x - self.player.x) <= 1 and abs(m.y - self.player.y) <= 1
            ]
            if not _adj_monsters and self.player.mp < self.player.max_mp:
                self.player.restore_mp(1)
                self.add_message("You meditate briefly. (+1 MP)", 'info')
            else:
                self.add_message("You wait.", 'info')
            # Chain-equip passive: unseen_when_still (Helm of Hades T5) increments
            # the no-move counter; reset by any subsequent _do_move.
            self.player._chain_no_move_counter = (
                getattr(self.player, '_chain_no_move_counter', 0) + 1)
            # three_oclock (Ring of Gawain T5) — resting resets the STR-decay counter.
            self.player._three_oclock_decay = 0
            self._advance_turn()
            return

        if key in (pygame.K_g, pygame.K_COMMA):
            self._pickup()
            return
        if key == pygame.K_e:
            self._open_equip_menu()
            return
        if key == pygame.K_r:
            self._open_scroll_menu()
            return
        if key == pygame.K_z:
            self._open_wand_menu()
            return
        if key == pygame.K_u:
            self._open_eat_menu()
            return
        if key == pygame.K_q:
            self._open_quaff_menu()
            return
        if key == pygame.K_m:
            self._open_spell_menu()
            return
        if key == pygame.K_i:
            self._open_identify_menu()
            return
        if key == pygame.K_h:
            self._harvest()
            return
        if key == pygame.K_c:
            self._open_cook_menu()
            return
        if key == pygame.K_p:
            # Try disarm trap first, then lockpick container
            if self._try_disarm_trap():
                return
            self._lockpick()
            return
        if key == pygame.K_a:
            self._open_melee_targeting()
            return
        if key == pygame.K_f:
            self._open_targeting()
            return
        if key == pygame.K_t:
            self._open_throw_menu()
            return
        if key == pygame.K_BACKSLASH:
            self._start_pray()
            return
        if key == pygame.K_n:
            self._start_recall_lore()
            return
        if key == pygame.K_SLASH or key == pygame.K_QUESTION:
            self.state = STATE_HELP
            return
        if key == pygame.K_x:
            self._open_examine_menu()
            return
        if key == pygame.K_b:
            self._open_encyclopedia()
            return
        if key == pygame.K_d:
            tile = self.dungeon.tiles[self.player.y][self.player.x]
            # On a fountain with Bronze Bull: open drop menu so player can offer it
            if tile == FOUNTAIN and any(
                    getattr(i, 'id', '') == 'bronze_bull' for i in self.player.inventory):
                self._open_drop_menu()
            # On an altar with quest items: open drop menu so player can offer
            elif tile == ALTAR and any(
                    getattr(i, 'id', '') in (
                        'eye_of_graeae', 'broken_gram', 'leather_scrap',
                        'cats_footstep', 'womans_beard', 'mountain_root',
                        'fish_breath', 'bird_spittle', 'bear_sinew',
                    )
                    for i in self.player.inventory):
                self._open_drop_menu()
            elif tile in (FOUNTAIN, GRAVE, THRONE):
                self._interact_tile()
            elif tile == ALTAR:
                # D = DROP, even on an altar. It used to auto-launch a theology
                # quiz against the first unidentified item (_altar_buc_identify),
                # which hijacked dropping. Altars are for PRAYER (the pray key,
                # amplified here); dropping/unequipping stay friction-free.
                self._open_drop_menu()
            else:
                # Adjacent to Odin's Altar with items — allow drop for throw-over
                self._open_drop_menu()
            return
        if key == pygame.K_y:
            self._open_shop()
            return
        if key == pygame.K_v:
            self._open_power_menu()
            return
        if key == pygame.K_BACKQUOTE:
            self._open_xyzzy_input()
            return
        if key == pygame.K_w:
            self._open_quirks_screen()
            return
        if key == pygame.K_o:
            self._start_observe()
            return
        if key == pygame.K_k:
            self._open_kit_panel()
            return
        if key == pygame.K_j:
            self._open_discoveries()
            return
        if key == pygame.K_SEMICOLON:
            self._open_study_journal()
            return
        if key == pygame.K_TAB:
            if self.zoom_mode == 'full':
                self.zoom_mode = 'medium'
                self.add_message("Medium view. [Tab] to zoom closer.", 'info')
            elif self.zoom_mode == 'medium':
                self.zoom_mode = 'close'
                self.add_message("Close-up view. [Tab] to zoom out.", 'info')
            else:
                self.zoom_mode = 'full'
                self.add_message("Full map view. [Tab] to zoom in.", 'info')
            return

        if key not in self._MOVE_KEYS:
            return

        self._do_move(*self._MOVE_KEYS[key])

    # ------------------------------------------------------------------
    # Confirm-exit / quest-exit / chicken popups
    # ------------------------------------------------------------------

    def _confirm_exit_input(self, key: int):
        if key in (pygame.K_y, pygame.K_RETURN):
            # Save & exit cleanly -- auto-save runs in main() after the loop
            self._save_on_quit = True
            self._quit_confirmed = True        # this QUIT is deliberate -> actually exit
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key == pygame.K_n:
            # Exit without saving -- delete any existing save to prevent checkpointing
            self._save_on_quit = False
            self._quit_confirmed = True
            from save_system import delete_save
            delete_save(self.player_name)
            import pygame as _pg
            _pg.event.post(_pg.event.Event(_pg.QUIT))
        elif key in (pygame.K_ESCAPE, pygame.K_c):
            self.state = STATE_PLAYER

    def _exit_quest_input(self, key: int):
        """Player has the Stone and is at the L1 exit."""
        if key == pygame.K_y:
            self._do_exit()
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _abandon_quest_input(self, key: int):
        """Player does NOT have the Stone and is at the L1 exit."""
        if key == pygame.K_y:
            self.state = STATE_CHICKEN
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _chicken_input(self, key: int):
        """McFly chicken popup — 1 to flee, 2 to stay and get Flux Capacitor."""
        if key == pygame.K_1:
            # "Yes, I am a coward."
            self.defeat_reason = 'fled'
            self._on_game_over()
            self._show_story_popup('exit_without_stone', STATE_DEAD)
        elif key == pygame.K_2:
            # "Nobody calls me chicken!"
            self.state = STATE_PLAYER
            self._spawn_flux_capacitor()

    # ------------------------------------------------------------------
    # Mystery altar approach overlay
    # ------------------------------------------------------------------

    def _mystery_approach_input(self, key: int, unicode: str):
        """Handle input while showing the mystery approach overlay."""
        if key in (pygame.K_ESCAPE, pygame.K_n):
            self.state = STATE_PLAYER
            self._active_mystery_altar = None
        elif key in (pygame.K_RETURN, pygame.K_y, pygame.K_SPACE):
            self._begin_mystery_challenge()

    # ------------------------------------------------------------------
    # XYZZY — hidden terminal text input and confirm dialog
    # ------------------------------------------------------------------

    def _xyzzy_input(self, key, unicode_char):
        """Handle typing in the XYZZY terminal."""
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        if key == pygame.K_RETURN:
            if self._xyzzy_text.strip().lower() == 'xyzzy':
                self.state = STATE_XYZZY_CONFIRM
                self._xyzzy_confirm_sel = 0  # 0=Yes, 1=No
            else:
                self.add_message("Nothing happens.", 'info')
                self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self._xyzzy_text = self._xyzzy_text[:-1]
            return
        # Accept printable characters (max 20 chars)
        if unicode_char and len(unicode_char) == 1 and unicode_char.isprintable() and len(self._xyzzy_text) < 20:
            self._xyzzy_text += unicode_char

    def _qa_warp_input_handler(self, key, unicode_char):
        """Titivillus QA tool: type a floor number, ENTER to warp.

        No quiz, no chronicle entry — straight debug warp.
        """
        buf = getattr(self, '_qa_warp_input', '')
        if key == pygame.K_RETURN:
            try:
                target = int(buf)
            except ValueError:
                target = 0
            if 1 <= target <= 100:
                self.add_message(f"[QA] Warping to floor {target}...", 'info')
                self._qa_warp_input = ''
                self.state = STATE_PLAYER
                # Floor change preserves saved levels; use _change_level so pets
                # follow, level state saves, etc.
                self._change_level(target, enter_from_top=(target >= self.dungeon_level))
            else:
                self.add_message("[QA] Floor must be 1-100.", 'warning')
                self._qa_warp_input = ''
                self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self._qa_warp_input = buf[:-1]
            return
        if unicode_char and unicode_char.isdigit() and len(buf) < 3:
            self._qa_warp_input = buf + unicode_char

    def _pet_name_input(self, key, unicode_char):
        """Handle typing in the pet-naming popup that opens when a Soul Sphere hatches."""
        pet = getattr(self, '_naming_pet', None)
        if pet is None:
            self.state = STATE_PLAYER
            return
        buf = getattr(self, '_pet_name_input_buffer', '')
        if key == pygame.K_ESCAPE:
            # Skip naming — pet keeps its species name as default.
            pet.nickname = ''
            self._log_chronicle(
                f"A soul sphere hatched. {pet.species_name} emerged. "
                "I'm not alone anymore."
            )
            self._naming_pet = None
            self._pet_name_input_buffer = ''
            self.state = STATE_PLAYER
            return
        if key == pygame.K_RETURN:
            name = buf.strip()
            # Empty or default-species name → no nickname (just show species).
            if name and name.lower() != pet.species_name.lower():
                pet.nickname = name
                self.add_message(
                    f"You name your new companion {name} the {pet.species_name}!",
                    'success')
                self._log_chronicle(
                    f"A soul sphere hatched. I named the {pet.species_name} '{name}'. "
                    "I'm not alone anymore."
                )
            else:
                pet.nickname = ''
                self._log_chronicle(
                    f"A soul sphere hatched. {pet.species_name} emerged. "
                    "I'm not alone anymore."
                )
            self._naming_pet = None
            self._pet_name_input_buffer = ''
            self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self._pet_name_input_buffer = buf[:-1]
            return
        # Printable characters, capped at 16 chars to keep names readable.
        if unicode_char and len(unicode_char) == 1 and unicode_char.isprintable() and len(buf) < 16:
            self._pet_name_input_buffer = buf + unicode_char

    def _xyzzy_confirm_input(self, key):
        """Handle the Yes/No confirmation dialog."""
        if key == pygame.K_ESCAPE or key == pygame.K_n:
            self.add_message("You step back from the edge of reality.", 'info')
            self.state = STATE_PLAYER
            return
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._xyzzy_confirm_sel = 1 - self._xyzzy_confirm_sel
            return
        if key == pygame.K_y or (key == pygame.K_RETURN and self._xyzzy_confirm_sel == 0):
            self._start_hack_reality()
            return
        if key == pygame.K_RETURN and self._xyzzy_confirm_sel == 1:
            self.add_message("You step back from the edge of reality.", 'info')
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # Quirks screen / character sheet
    # ------------------------------------------------------------------

    def _quirks_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_w, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER
            return
        data = getattr(self, '_quirks_data', []) or []
        if not data:
            return
        cur = max(0, min(getattr(self, '_quirks_sel', 0), len(data) - 1))
        if key == pygame.K_UP:
            self._quirks_sel = max(0, cur - 1)
        elif key == pygame.K_DOWN:
            self._quirks_sel = min(len(data) - 1, cur + 1)
        elif key == pygame.K_PAGEUP:
            self._quirks_sel = max(0, cur - 6)
        elif key == pygame.K_PAGEDOWN:
            self._quirks_sel = min(len(data) - 1, cur + 6)
        elif key == pygame.K_HOME:
            self._quirks_sel = 0
        elif key == pygame.K_END:
            self._quirks_sel = len(data) - 1

    def _character_sheet_input(self, key):
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        self._charsheet_clamp()
        focus = getattr(self, '_charsheet_focus', 'loadout')
        order = ['loadout', 'pack', 'actions']

        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if focus == 'actions':
                self._charsheet_activate_action()
            else:
                self._charsheet_focus_actions()
            return

        filter_keys = {
            pygame.K_1: 'all',
            pygame.K_2: 'gear',
            pygame.K_3: 'food',
            pygame.K_4: 'lore',
        }
        if key in filter_keys:
            self._charsheet_set_pack_filter(filter_keys[key])
            return
        if key == pygame.K_TAB:
            try:
                mods = pygame.key.get_mods()
            except pygame.error:
                mods = 0
            delta = -1 if mods & pygame.KMOD_SHIFT else 1
            self._charsheet_cycle_pack_filter(delta)
            return

        shortcut_actions = {
            pygame.K_e: 'equip',
            pygame.K_u: 'unequip',
            pygame.K_i: 'identify',
            pygame.K_x: 'lore',
            pygame.K_d: 'drop',
        }
        if key in shortcut_actions:
            self._charsheet_activate_action(shortcut_actions[key])
            return

        if key == pygame.K_LEFT:
            if focus == 'actions':
                self._charsheet_focus = getattr(self, '_charsheet_action_source', 'pack')
            else:
                idx = max(0, order.index(focus) - 1) if focus in order else 0
                self._charsheet_focus = order[idx]
            self._charsheet_clamp()
            return
        if key == pygame.K_RIGHT:
            if focus in ('loadout', 'pack'):
                idx = min(len(order) - 1, order.index(focus) + 1)
                if order[idx] == 'actions':
                    self._charsheet_focus_actions()
                else:
                    self._charsheet_focus = order[idx]
            else:
                self._charsheet_focus = 'actions'
            self._charsheet_clamp()
            return

        if key == pygame.K_UP:
            if focus == 'pack':
                self._charsheet_pack_idx = max(0, getattr(self, '_charsheet_pack_idx', 0) - 1)
            elif focus == 'actions':
                self._charsheet_action_idx = max(0, getattr(self, '_charsheet_action_idx', 0) - 1)
            else:
                self._charsheet_loadout_idx = max(0, getattr(self, '_charsheet_loadout_idx', 0) - 1)
        elif key == pygame.K_DOWN:
            if focus == 'pack':
                self._charsheet_pack_idx = getattr(self, '_charsheet_pack_idx', 0) + 1
            elif focus == 'actions':
                self._charsheet_action_idx = getattr(self, '_charsheet_action_idx', 0) + 1
            else:
                self._charsheet_loadout_idx = getattr(self, '_charsheet_loadout_idx', 0) + 1
        elif key == pygame.K_PAGEUP:
            if focus == 'pack':
                self._charsheet_pack_idx = max(0, getattr(self, '_charsheet_pack_idx', 0) - 6)
            elif focus == 'actions':
                self._charsheet_action_idx = 0
            else:
                self._charsheet_loadout_idx = max(0, getattr(self, '_charsheet_loadout_idx', 0) - 6)
        elif key == pygame.K_PAGEDOWN:
            if focus == 'pack':
                self._charsheet_pack_idx = getattr(self, '_charsheet_pack_idx', 0) + 6
            elif focus == 'actions':
                self._charsheet_action_idx = 999
            else:
                self._charsheet_loadout_idx = getattr(self, '_charsheet_loadout_idx', 0) + 6
        elif key == pygame.K_HOME:
            if focus == 'pack':
                self._charsheet_pack_idx = 0
            elif focus == 'actions':
                self._charsheet_action_idx = 0
            else:
                self._charsheet_loadout_idx = 0
        elif key == pygame.K_END:
            if focus == 'pack':
                self._charsheet_pack_idx = 9999
            elif focus == 'actions':
                self._charsheet_action_idx = 9999
            else:
                self._charsheet_loadout_idx = 9999
        self._charsheet_clamp()

    # ------------------------------------------------------------------
    # Cow encounter dialog
    # ------------------------------------------------------------------

    def _cow_encounter_input(self, key: int):
        """Handle input for cow dialog."""
        if self._cow_dialog_phase == 'result':
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.state = STATE_PLAYER
            return

        if key == pygame.K_1:
            # Feed the cow (costs an ingredient)
            from items import Ingredient
            ingredient = next(
                (i for i in self.player.inventory if isinstance(i, Ingredient)), None
            )
            if ingredient:
                self.player.remove_from_inventory(ingredient)
                self.add_message(
                    f"You feed the cow your {self._display_name(ingredient)}. "
                    "The cow chews contentedly. Moo.", 'success'
                )
            else:
                self.add_message("You have nothing to feed the cow. Moo.", 'info')
            self._cow_dialog_phase = 'result'
        elif key == pygame.K_2:
            # Walk away
            import random as _rng
            self.add_message(
                _rng.choice(self._COW_MOO_MESSAGES), 'info'
            )
            self.state = STATE_PLAYER
        elif key == pygame.K_3:
            # Poke the cow
            self._cow_poke_count += 1
            if self._cow_poke_count >= 10:
                self._enter_cow_level()
            else:
                import random as _rng
                msg = self._COW_POKE_MESSAGES[
                    min(self._cow_poke_count - 1, len(self._COW_POKE_MESSAGES) - 1)
                ]
                self.add_message(msg, 'info')
                self._cow_dialog_phase = 'result'
        elif key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # NPC encounter (multi-phase)
    # ------------------------------------------------------------------

    def _npc_encounter_input(self, key: int):
        """Handle input during NPC encounter — multi-phase flow."""
        enc = self._npc_encounter_active
        if enc is None:
            self.state = STATE_PLAYER
            return

        phase = self._npc_encounter_phase

        # ── Phase: TEXT (encounter description) ───────────────────
        if phase == 'text':
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._npc_encounter_phase = 'options'
            elif key == pygame.K_ESCAPE:
                self._close_npc_encounter(resolved=False)
            return

        # ── Phase: OPTIONS (choose 1-3) ──────────────────────────
        if phase == 'options':
            if key == pygame.K_ESCAPE:
                self._close_npc_encounter(resolved=False)
                return

            key_to_idx = {
                pygame.K_1: 0, pygame.K_KP1: 0,
                pygame.K_2: 1, pygame.K_KP2: 1,
                pygame.K_3: 2, pygame.K_KP3: 2,
            }
            idx = key_to_idx.get(key)
            if idx is None or idx >= len(enc['options']):
                return

            opt = enc['options'][idx]
            cost = opt.get('cost')

            # Check if player can pay the cost
            from npc_encounters import can_pay_cost, get_inventory_filter
            can_pay, fail_msg = can_pay_cost(self.player, cost, self.player_gold)
            if not can_pay:
                self.add_message(fail_msg, 'warning')
                return

            self._npc_selected_option = opt

            # If cost requires inventory selection, show item picker
            inv_filter = get_inventory_filter(cost)
            if inv_filter:
                self._npc_item_list = self._get_filtered_inventory(inv_filter)
                if not self._npc_item_list:
                    self.add_message(fail_msg or "You don't have what's needed.", 'warning')
                    self._npc_selected_option = None
                    return
                self._npc_item_scroll = 0
                self._npc_encounter_phase = 'select_item'
                return

            # No item selection needed — apply immediately
            self._apply_npc_choice(opt, selected_item=None)
            return

        # ── Phase: SELECT_ITEM (pick from filtered inventory) ────
        if phase == 'select_item':
            if key == pygame.K_ESCAPE:
                # Go back to options
                self._npc_encounter_phase = 'options'
                self._npc_selected_option = None
                return

            items = self._npc_item_list
            idx = self._AZ_KEYS.get(key)
            if idx is not None:
                actual = idx + self._npc_item_scroll
                if 0 <= actual < len(items):
                    self._apply_npc_choice(self._npc_selected_option,
                                           selected_item=items[actual])
                    return

            # Scroll
            if key == pygame.K_DOWN and self._npc_item_scroll + 9 < len(items):
                self._npc_item_scroll += 1
            elif key == pygame.K_UP and self._npc_item_scroll > 0:
                self._npc_item_scroll -= 1
            return

        # ── Phase: OUTCOME (show result) ─────────────────────────
        if phase == 'outcome':
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._close_npc_encounter(resolved=True)
            return

    # ------------------------------------------------------------------
    # Judgment overlay
    # ------------------------------------------------------------------

    def _judgment_input(self, key: int):
        """Dismiss the judgment result overlay."""
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER

    # ------------------------------------------------------------------
    # Targeting cursor input
    # ------------------------------------------------------------------

    _TARGET_MOVE_KEYS = {
        pygame.K_UP:    (0, -1),
        pygame.K_DOWN:  (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0),
        pygame.K_KP7:   (-1,-1), pygame.K_KP8: (0,-1), pygame.K_KP9: (1,-1),
        pygame.K_KP4:   (-1, 0), pygame.K_KP6: (1, 0),
        pygame.K_KP1:   (-1, 1), pygame.K_KP2: (0, 1), pygame.K_KP3: (1, 1),
    }

    def _target_input(self, key: int):
        """Handle key input while in targeting mode (ranged or melee)."""
        # TAB / t -- cycle through valid monster targets
        if key in (pygame.K_TAB, pygame.K_t) and self._target_candidates:
            self._target_idx = (self._target_idx + 1) % len(self._target_candidates)
            m = self._target_candidates[self._target_idx]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
            return

        # Arrow / vi keys -- cursor movement
        if key in self._TARGET_MOVE_KEYS:
            dx, dy = self._TARGET_MOVE_KEYS[key]
            nx = self.target_cursor_x + dx
            ny = self.target_cursor_y + dy
            # Clamp to dungeon bounds
            nx = max(0, min(nx, self.dungeon.width - 1))
            ny = max(0, min(ny, self.dungeon.height - 1))
            # Melee targeting: clamp to weapon reach (Chebyshev distance)
            if self._melee_targeting:
                px, py = self.player.x, self.player.y
                reach = getattr(self, '_melee_reach', 1)
                if max(abs(nx - px), abs(ny - py)) > reach:
                    return  # don't move cursor beyond reach
                if nx == px and ny == py:
                    return  # can't target own tile
            # Throw targeting: clamp to throw range
            if self._throw_targeting:
                px, py = self.player.x, self.player.y
                if max(abs(nx - px), abs(ny - py)) > self._throw_reach:
                    return
                if nx == px and ny == py:
                    return
            # Observe targeting: clamp to sight range (own tile allowed)
            if self._observe_targeting:
                px, py = self.player.x, self.player.y
                if max(abs(nx - px), abs(ny - py)) > getattr(self, '_observe_reach', 99):
                    return
            self.target_cursor_x = nx
            self.target_cursor_y = ny
            return

        # ENTER / SPACE / f / a / y -- confirm target
        confirm_keys = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_f)
        if self._melee_targeting:
            confirm_keys = confirm_keys + (pygame.K_a,)
        if self._throw_targeting:
            confirm_keys = confirm_keys + (pygame.K_y,)
        if self._observe_targeting:
            confirm_keys = confirm_keys + (pygame.K_o,)
        if self._wand_targeting:
            confirm_keys = confirm_keys + (pygame.K_z,)
        if getattr(self, '_power_targeting', False):
            confirm_keys = confirm_keys + (pygame.K_v,)
        if getattr(self, '_pet_special_targeting', False):
            confirm_keys = confirm_keys + (pygame.K_s,)
        if key in confirm_keys:
            if getattr(self, '_power_targeting', False):
                self._confirm_power_target()
                return
            if getattr(self, '_pet_special_targeting', False):
                self._confirm_pet_special_target()
                return
            if self._wand_targeting:
                self._confirm_wand_target()
            elif self._observe_targeting:
                self._confirm_observe()
            elif self._throw_targeting:
                self._confirm_throw_target()
            elif self._melee_targeting:
                self._confirm_melee_target()
            else:
                self._confirm_ranged_target()

    # ------------------------------------------------------------------
    # Quiz input
    # ------------------------------------------------------------------

    def _quiz_input(self, key: int):
        # Necronomicon custom quiz intercept
        if hasattr(self, '_necro_qs') and self._necro_qs is not None:
            self._necro_answer(key)
            return

        if self.quiz_engine.state != QuizState.ASKING:
            return
        q = self.quiz_engine.current_question
        if not q:
            return
        choices = q.get('choices', [])
        key_map = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
        }
        idx = key_map.get(key)
        if idx is not None and idx < len(choices):
            qe = self.quiz_engine
            # Map displayed position back to actual choice via confused_order
            if qe.confused_order and len(qe.confused_order) == len(choices):
                actual_idx = qe.confused_order[idx]
            else:
                actual_idx = idx
            self.quiz_engine.answer(choices[actual_idx])

    # ------------------------------------------------------------------
    # Study journal
    # ------------------------------------------------------------------

    def _study_input(self, key):
        """Handle input in the study journal.
        Left/Right: cycle subject tabs.
        Up/Down: scroll through questions in current category."""
        # Left/Right: cycle subject category
        if key == pygame.K_LEFT:
            self._study_subject_idx = (self._study_subject_idx - 1) % len(self._STUDY_SUBJECTS)
            self._study_filtered = self._study_filter()
            self._study_question_idx = 0
            self._study_scroll = 0
        elif key == pygame.K_RIGHT:
            self._study_subject_idx = (self._study_subject_idx + 1) % len(self._STUDY_SUBJECTS)
            self._study_filtered = self._study_filter()
            self._study_question_idx = 0
            self._study_scroll = 0
        # Up/Down: page through questions within category
        elif key in (pygame.K_DOWN, pygame.K_SPACE, pygame.K_RETURN):
            if self._study_filtered:
                self._study_question_idx = min(
                    getattr(self, '_study_question_idx', 0) + 1, len(self._study_filtered) - 1)
                self._study_scroll = 0
        elif key in (pygame.K_UP, pygame.K_BACKSPACE):
            self._study_question_idx = max(0, getattr(self, '_study_question_idx', 0) - 1)
            self._study_scroll = 0
        elif key == pygame.K_PAGEUP:
            self._study_scroll = max(0, getattr(self, '_study_scroll', 0) - 8)
        elif key == pygame.K_PAGEDOWN:
            self._study_scroll = getattr(self, '_study_scroll', 0) + 8

    # ------------------------------------------------------------------
    # Help / lore overlays
    # ------------------------------------------------------------------

    def _help_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_SLASH, pygame.K_RETURN, pygame.K_SPACE):
            self.state = STATE_PLAYER

    def _lore_input(self, key: int):
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_x):
            self.state = STATE_PLAYER
            self._lore_subject = None
            return

        subject = getattr(self, '_lore_subject', None)
        if subject is None:
            self.state = STATE_PLAYER
            return

        if key == pygame.K_TAB:
            panes = ['identity', 'mechanics', 'lore']
            focus = getattr(self, '_lore_focus', 'mechanics')
            try:
                mods = pygame.key.get_mods()
            except pygame.error:
                mods = 0
            delta = -1 if mods & pygame.KMOD_SHIFT else 1
            idx = panes.index(focus) if focus in panes else 1
            self._lore_focus = panes[(idx + delta) % len(panes)]
            return

        scroll_keys = {
            pygame.K_UP: -1,
            pygame.K_DOWN: 1,
            pygame.K_PAGEUP: -8,
            pygame.K_PAGEDOWN: 8,
            pygame.K_HOME: 'home',
            pygame.K_END: 'end',
        }
        if key in scroll_keys:
            focus = getattr(self, '_lore_focus', 'mechanics')
            attr = {
                'identity': '_lore_identity_scroll',
                'mechanics': '_lore_mech_scroll',
                'lore': '_lore_text_scroll',
            }.get(focus, '_lore_mech_scroll')
            delta = scroll_keys[key]
            if delta == 'home':
                setattr(self, attr, 0)
            elif delta == 'end':
                setattr(self, attr, 9999)
            else:
                setattr(self, attr, max(0, getattr(self, attr, 0) + delta))
            return

        from items import Weapon, Armor, Shield, Accessory, Corpse

        if key == pygame.K_i:
            if isinstance(subject, Corpse) or not hasattr(subject, 'id_level'):
                self.add_message("There is nothing more to identify here.", 'info')
                return
            if int(getattr(subject, 'id_level', 5)) >= 5:
                self.add_message("You already understand that item completely.", 'info')
                return
            self.state = STATE_PLAYER
            self._identify_item(subject)
            return

        if key == pygame.K_e:
            if isinstance(subject, Corpse):
                self.add_message("You cannot equip a corpse.", 'info')
                return
            if not isinstance(subject, (Weapon, Armor, Shield, Accessory)):
                self.add_message("That item cannot be equipped.", 'info')
                return
            slot = None
            if hasattr(self, '_lore_equipped_slot'):
                slot = self._lore_equipped_slot(subject)
            self.state = STATE_PLAYER
            if slot:
                self._unequip_slot(slot, subject)
            elif subject in getattr(self.player, 'inventory', []):
                self._equip_item(subject)
            else:
                self.add_message("That item is not in your pack.", 'info')
            return

    # ------------------------------------------------------------------
    # Drop-gold numeric prompt
    # ------------------------------------------------------------------

    def _drop_gold_input(self, key: int, unicode: str):
        """Handle keystrokes for the gold-amount prompt."""
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            amount = int(self.drop_gold_input) if self.drop_gold_input.isdigit() else 0
            amount = max(0, min(amount, getattr(self, 'player_gold', 0)))
            if amount > 0:
                from items import GoldPile
                pile = GoldPile(amount, self.player.x, self.player.y)
                self.player_gold -= amount
                self.ground_items.append(pile)
                self.add_message(f"You drop {amount} gold coins.", 'info')
                self._advance_turn()
            else:
                self.add_message("No gold dropped.", 'info')
            self.state = STATE_PLAYER
            return
        if key == pygame.K_BACKSPACE:
            self.drop_gold_input = self.drop_gold_input[:-1]
            return
        if unicode.isdigit() and len(self.drop_gold_input) < 7:
            self.drop_gold_input += unicode

    def _drop_qty_input(self, key: int, unicode: str):
        """Handle keystrokes for the 'how many to drop' prompt (stacked items)."""
        item = getattr(self, '_drop_qty_item', None)
        if item is None:
            self.state = STATE_PLAYER
            return
        have = getattr(item, 'count', 1)
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            # Blank entry drops the whole stack (the shown default).
            qty = min(int(self.drop_qty_input), have) if self.drop_qty_input.isdigit() else have
            self.state = STATE_PLAYER
            self._drop_qty_item = None
            if qty > 0:
                self._finish_drop(item, qty)
            else:
                self.add_message("Nothing dropped.", 'info')
            return
        if key == pygame.K_BACKSPACE:
            self.drop_qty_input = self.drop_qty_input[:-1]
            return
        if unicode.isdigit() and len(self.drop_qty_input) < 7:
            self.drop_qty_input += unicode

    # ------------------------------------------------------------------
    # Shop / encyclopedia
    # ------------------------------------------------------------------

    def _shop_input(self, key: int):
        m = getattr(self, '_shop_merchant', None)
        if m is None or key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        stock = m.stock
        if not stock:
            self.add_message("The merchant has nothing left to sell.", 'info')
            self.state = STATE_PLAYER
            return
        sel = getattr(self, '_shop_selection', 0)
        if key in getattr(self, '_MENU_CURSOR_KEYS', (pygame.K_UP, pygame.K_DOWN)):
            if hasattr(self, '_move_menu_cursor'):
                self._shop_selection = self._move_menu_cursor(sel, key, len(stock))
            elif key == pygame.K_UP:
                self._shop_selection = (sel - 1) % len(stock)
            elif key == pygame.K_DOWN:
                self._shop_selection = (sel + 1) % len(stock)
        elif key == pygame.K_h:
            sel = self._shop_selection
            if sel < len(stock):
                haggled = getattr(self, '_shop_haggled', set())
                if sel in haggled:
                    self.add_message("You've already haggled over that item.", 'info')
                else:
                    self._haggle_item(sel)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            sel = self._shop_selection
            if sel < len(stock):
                item  = stock[sel]
                price = m.prices[sel]
                if self.player_gold < price:
                    self.add_message(f"You can't afford that ({price} gold needed).", 'warning')
                else:
                    self.player_gold -= price
                    self.player.add_to_inventory(item)
                    iname = getattr(item, 'name', 'item')
                    _snd.play('buy')
                    self.add_message(f"You buy {iname} for {price} gold.", 'success')
                    m.stock.pop(sel)
                    m.prices.pop(sel)
                    # Shift haggled indices after removal
                    haggled = getattr(self, '_shop_haggled', set())
                    self._shop_haggled = {i - 1 if i > sel else i for i in haggled if i != sel}
                    self._shop_selection = min(sel, len(m.stock) - 1)
                    if not m.stock:
                        m.sold_out = True
                        self.add_message("The merchant has sold everything.", 'info')
                        self.state = STATE_PLAYER

    def _encyclopedia_input(self, key: int):
        cats = getattr(self, '_ENCYCLOPEDIA_CATS', [
            ('a', 'bestiary', 'Bestiary'),
            ('b', 'weapon', 'Armory'),
            ('c', 'armor', 'Armor'),
            ('d', 'accessory', 'Accessories'),
            ('e', 'scroll', 'Scrolls'),
            ('f', 'wand', 'Wands'),
            ('g', 'spellbook', 'Spellbooks'),
            ('h', 'chronicle', 'Chronicle'),
            ('i', 'lore_hints', 'Lore Hints'),
            ('j', 'recipes', 'Recipes'),
        ])
        cat_keys = {getattr(pygame, f'K_{key_label}'): slug
                    for key_label, slug, _ in cats}

        def open_category(slug: str):
            self.encyclopedia_category = slug
            self.encyclopedia_selection = 0
            self._encyclopedia_entry = None
            self._encyclopedia_article_scroll = 0
            for idx, (_key, cat_slug, _label) in enumerate(cats):
                if cat_slug == slug:
                    self._encyclopedia_cat_idx = idx
                    break
            self._encyclopedia_load_entries(slug)

        if self.encyclopedia_category == '':
            # Category selection screen
            if key == pygame.K_ESCAPE:
                self.state = STATE_PLAYER
                return
            if key == pygame.K_UP:
                self._encyclopedia_cat_idx = max(0, getattr(self, '_encyclopedia_cat_idx', 0) - 1)
                return
            if key == pygame.K_DOWN:
                self._encyclopedia_cat_idx = min(len(cats) - 1,
                                                 getattr(self, '_encyclopedia_cat_idx', 0) + 1)
                return
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                idx = max(0, min(getattr(self, '_encyclopedia_cat_idx', 0),
                                 len(cats) - 1))
                open_category(cats[idx][1])
                return
            cat = cat_keys.get(key)
            if cat:
                open_category(cat)
            return

        if self._encyclopedia_entry is not None:
            # Entry detail view
            if key == pygame.K_ESCAPE:
                self._encyclopedia_entry = None
                self._encyclopedia_article_scroll = 0
                return
            if key == pygame.K_PAGEUP:
                self._encyclopedia_article_scroll = max(
                    0, getattr(self, '_encyclopedia_article_scroll', 0) - 8)
                return
            if key == pygame.K_PAGEDOWN:
                self._encyclopedia_article_scroll = getattr(
                    self, '_encyclopedia_article_scroll', 0) + 8
                return
            if key == pygame.K_UP:
                self._encyclopedia_article_scroll = max(
                    0, getattr(self, '_encyclopedia_article_scroll', 0) - 1)
                return
            if key == pygame.K_DOWN:
                self._encyclopedia_article_scroll = getattr(
                    self, '_encyclopedia_article_scroll', 0) + 1
                return
            return

        # List view
        if key == pygame.K_ESCAPE:
            self.encyclopedia_category = ''
            self.encyclopedia_entries = []
            self.encyclopedia_selection = 0
            self._encyclopedia_entry = None
            self._encyclopedia_article_scroll = 0
            return
        if key in cat_keys:
            open_category(cat_keys[key])
            return
        if key == pygame.K_LEFT:
            cur = getattr(self, '_encyclopedia_cat_idx', 0)
            open_category(cats[(cur - 1) % len(cats)][1])
            return
        if key == pygame.K_RIGHT:
            cur = getattr(self, '_encyclopedia_cat_idx', 0)
            open_category(cats[(cur + 1) % len(cats)][1])
            return
        if key == pygame.K_UP:
            self.encyclopedia_selection = max(0, self.encyclopedia_selection - 1)
            self._encyclopedia_article_scroll = 0
            return
        if key == pygame.K_DOWN:
            self.encyclopedia_selection = min(len(self.encyclopedia_entries) - 1,
                                              self.encyclopedia_selection + 1)
            self._encyclopedia_article_scroll = 0
            return
        if key == pygame.K_PAGEUP:
            self._encyclopedia_article_scroll = max(
                0, getattr(self, '_encyclopedia_article_scroll', 0) - 8)
            return
        if key == pygame.K_PAGEDOWN:
            self._encyclopedia_article_scroll = getattr(
                self, '_encyclopedia_article_scroll', 0) + 8
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if 0 <= self.encyclopedia_selection < len(self.encyclopedia_entries):
                self._encyclopedia_entry = self.encyclopedia_entries[self.encyclopedia_selection]
                self._encyclopedia_article_scroll = 0
            return
