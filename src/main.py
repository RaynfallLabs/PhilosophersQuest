import sys
import pygame

from combat import player_attack
from dungeon import generate_dungeon, spawn_monsters, spawn_items
from food_system import harvest_corpse, cook_ingredient
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient
from player import Player
from quiz_engine import QuizEngine, QuizMode, QuizState
from renderer import Renderer, TILE_SIZE
from ui import Sidebar, MessageLog, SIDEBAR_W

WINDOW_W = 1280
WINDOW_H = 720
FPS      = 60

GAME_W = WINDOW_W - SIDEBAR_W      # 980 px — left area for game + messages
MSG_H  = 144                        # message log height (bottom of game area)
GAME_H = WINDOW_H - MSG_H          # 576 px = 18 tiles tall

VIEWPORT_W = GAME_W // TILE_SIZE    # 30 tiles wide
VIEWPORT_H = GAME_H // TILE_SIZE    # 18 tiles tall

# Game states
STATE_PLAYER     = 'player'
STATE_QUIZ       = 'quiz'
STATE_EQUIP_MENU = 'equip_menu'
STATE_COOK_MENU  = 'cook_menu'
STATE_DEAD       = 'dead'


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_md = pygame.font.SysFont('consolas', 20)
        self.font_lg = pygame.font.SysFont('consolas', 28, bold=True)
        self.font_sm = pygame.font.SysFont('consolas', 15)

        self.quiz_engine        = QuizEngine()
        self.msg_log            = MessageLog()
        self.sidebar            = Sidebar(screen, GAME_W)
        self.state              = STATE_PLAYER
        self.combat_target      = None
        self.quiz_title         = ''
        self.equip_menu_items: list = []
        self.cook_menu_items: list  = []
        self.turn_count         = 0
        self.dungeon_level      = 1

        self._new_level(1)

    # ------------------------------------------------------------------
    # Message helper
    # ------------------------------------------------------------------

    def add_message(self, text: str, msg_type: str = 'info'):
        self.msg_log.add(text, msg_type)

    # ------------------------------------------------------------------
    # Level setup
    # ------------------------------------------------------------------

    def _new_level(self, level: int):
        self.dungeon_level    = level
        self.dungeon          = generate_dungeon(80, 50, level)
        self.player           = Player()
        self.player.x, self.player.y = self.dungeon.rooms[0].center
        self.monsters         = spawn_monsters(self.dungeon.rooms, level, self.dungeon)
        self.ground_items     = spawn_items(self.dungeon.rooms, level, self.dungeon)
        self.renderer         = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
        self._refresh_fov()
        self.add_message(f"You descend to dungeon level {level}.", 'info')

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True

        if event.key == pygame.K_ESCAPE:
            if self.state in (STATE_EQUIP_MENU, STATE_COOK_MENU):
                self.state = STATE_PLAYER
                return True
            return False

        if self.state == STATE_PLAYER:
            self._player_input(event.key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(event.key)
        elif self.state == STATE_EQUIP_MENU:
            self._equip_menu_input(event.key)
        elif self.state == STATE_COOK_MENU:
            self._cook_menu_input(event.key)

        return True

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
    }

    def _player_input(self, key: int):
        if key in (pygame.K_g, pygame.K_COMMA):
            self._pickup()
            return
        if key == pygame.K_e:
            self._open_equip_menu()
            return
        if key == pygame.K_h:
            self._harvest()
            return
        if key == pygame.K_c:
            self._open_cook_menu()
            return

        if key not in self._MOVE_KEYS:
            return

        paralyzed = self.player.status_effects.get('paralyzed', 0)
        if paralyzed > 0:
            self.player.status_effects['paralyzed'] = paralyzed - 1
            remaining = paralyzed - 1
            self.add_message(
                f"You are paralyzed! ({remaining} turn{'s' if remaining != 1 else ''} left)",
                'danger'
            )
            self._advance_turn()
            return

        dx, dy = self._MOVE_KEYS[key]
        nx, ny = self.player.x + dx, self.player.y + dy

        target = next(
            (m for m in self.monsters if m.alive and m.x == nx and m.y == ny), None
        )
        if target:
            self._start_combat(target)
        elif self.dungeon.is_walkable(nx, ny):
            self.player.x, self.player.y = nx, ny
            self._refresh_fov()
            self._tick_sp()
            self._advance_turn()

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------

    def _advance_turn(self):
        self.turn_count += 1
        self._do_monster_turns()

    # ------------------------------------------------------------------
    # SP starvation
    # ------------------------------------------------------------------

    def _tick_sp(self):
        if self.player.sp > 0:
            self.player.sp -= 1
            if self.player.sp == 0:
                self.add_message("You are hungry! Find food before you starve.", 'warning')
        else:
            dmg = self.player.take_damage(1, 'starvation')
            self.add_message(f"You are starving! You take {dmg} damage.", 'danger')
            if self.player.is_dead():
                self.state = STATE_DEAD
                self.add_message("You have died of starvation! Press ESC to quit.", 'danger')

    # ------------------------------------------------------------------
    # Pickup
    # ------------------------------------------------------------------

    def _pickup(self):
        px, py = self.player.x, self.player.y
        item = next((i for i in self.ground_items if i.x == px and i.y == py), None)
        if item is None:
            self.add_message("There is nothing here to pick up.", 'info')
            return
        if self.player.add_to_inventory(item):
            self.ground_items.remove(item)
            self.add_message(f"You pick up the {item.name}.", 'loot')
            self._advance_turn()
        else:
            self.add_message("You are carrying too much to pick that up.", 'warning')

    # ------------------------------------------------------------------
    # Harvest
    # ------------------------------------------------------------------

    def _harvest(self):
        px, py = self.player.x, self.player.y
        corpse = next(
            (i for i in self.ground_items
             if isinstance(i, Corpse) and i.x == px and i.y == py),
            None
        )
        if corpse is None:
            self.add_message("There is no corpse here to harvest.", 'info')
            return
        if corpse.ingredient_id is None:
            self.add_message(f"The {corpse.name} yields nothing useful.", 'info')
            self.ground_items.remove(corpse)
            return

        self.ground_items.remove(corpse)
        self.quiz_title = f"HARVESTING {corpse.name.upper()}  —  ANIMAL LORE"
        self.state = STATE_QUIZ

        def on_complete(ingredient, message: str):
            self.state = STATE_PLAYER
            msg_type = 'loot' if ingredient is not None else 'warning'
            self.add_message(message, msg_type)
            if ingredient is not None:
                if not self.player.add_to_inventory(ingredient):
                    self.ground_items.append(ingredient)
                    ingredient.x, ingredient.y = px, py
                    self.add_message(
                        f"Too heavy to carry — {ingredient.name} dropped.", 'warning'
                    )
            self._advance_turn()

        harvest_corpse(self.player, corpse, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Cook menu
    # ------------------------------------------------------------------

    def _open_cook_menu(self):
        self.cook_menu_items = [
            i for i in self.player.inventory if isinstance(i, Ingredient)
        ]
        if not self.cook_menu_items:
            self.add_message("You have no ingredients to cook.", 'info')
            return
        self.state = STATE_COOK_MENU

    def _cook_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP2: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.cook_menu_items):
            return
        self.state = STATE_PLAYER
        self._cook_item(self.cook_menu_items[idx])

    def _cook_item(self, ingredient):
        self.player.remove_from_inventory(ingredient)
        self.quiz_title = f"COOKING {ingredient.name.upper()}  —  COOKING CHAIN"
        self.state = STATE_QUIZ

        def on_complete(messages: list[str]):
            self.state = STATE_PLAYER
            for i, msg in enumerate(messages):
                if i == 0 and 'ruin' in msg.lower():
                    self.add_message(msg, 'warning')
                else:
                    self.add_message(msg, 'success')
            self._advance_turn()

        cook_ingredient(self.player, ingredient, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Equip menu
    # ------------------------------------------------------------------

    def _open_equip_menu(self):
        self.equip_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Weapon, Armor, Shield))
        ]
        if not self.equip_menu_items:
            self.add_message("You have nothing equippable in your inventory.", 'info')
            return
        self.state = STATE_EQUIP_MENU

    def _equip_menu_input(self, key: int):
        key_to_idx = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
            pygame.K_5: 4, pygame.K_KP5: 4,
            pygame.K_6: 5, pygame.K_KP6: 5,
            pygame.K_7: 6, pygame.K_KP7: 6,
            pygame.K_8: 7, pygame.K_KP8: 7,
            pygame.K_9: 8, pygame.K_KP9: 8,
        }
        idx = key_to_idx.get(key)
        if idx is None or idx >= len(self.equip_menu_items):
            return
        self.state = STATE_PLAYER
        self._equip_item(self.equip_menu_items[idx])

    def _equip_item(self, item):
        if isinstance(item, Weapon):
            self.player._apply_equip(item)
            self.player.remove_from_inventory(item)
            self.add_message(f"You equip the {item.name}.", 'success')
            self._advance_turn()

        elif isinstance(item, (Armor, Shield)):
            item_name = item.name
            self.quiz_title = f"EQUIPPING {item_name.upper()}  —  GEOGRAPHY"
            self.state = STATE_QUIZ

            def on_complete(result):
                self.state = STATE_PLAYER
                if result.success:
                    self.player._apply_equip(item)
                    self.player.remove_from_inventory(item)
                    self.add_message(
                        f"You equip the {item_name}. AC is now {self.player.get_ac()}.",
                        'success'
                    )
                else:
                    self.add_message(
                        f"You struggle to put on the {item_name} and give up.", 'warning'
                    )
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='threshold',
                subject='geography',
                tier=1,
                callback=on_complete,
                threshold=item.equip_threshold,
                wisdom=self.player.WIS,
            )

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def _start_combat(self, monster):
        self.state = STATE_QUIZ
        self.combat_target = monster
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  —  MATH CHAIN"

        if monster.kind == 'floating_eye':
            cur = self.player.status_effects.get('paralyzed', 0)
            self.player.status_effects['paralyzed'] = max(cur, 3)
            self.add_message("The floating eye's gaze paralyzes you!", 'danger')

        def on_complete(damage: int, killed: bool, chain: int):
            self.state = STATE_PLAYER
            if chain == 0:
                self.add_message(
                    f"You swing wildly at the {monster.name} and miss!", 'warning'
                )
            else:
                self.add_message(
                    f"Chain x{chain}! You strike the {monster.name} for {damage} damage!",
                    'success'
                )
                if killed:
                    self.add_message(f"The {monster.name} is slain!", 'success')
                    self.ground_items.append(
                        Corpse(
                            monster.name, monster.kind, monster.x, monster.y,
                            harvest_tier=monster.harvest_tier,
                            harvest_threshold=monster.harvest_threshold,
                            ingredient_id=monster.ingredient_id,
                        )
                    )
            self._advance_turn()

        player_attack(self.player, monster, self.quiz_engine, on_complete)

    def _quiz_input(self, key: int):
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
            self.quiz_engine.answer(choices[idx])

    # ------------------------------------------------------------------
    # Monster turns
    # ------------------------------------------------------------------

    def _do_monster_turns(self):
        for m in self.monsters:
            if not m.alive:
                continue
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters)
            if did_attack:
                dmg, msg = m.attack(self.player)
                self.add_message(msg, 'danger')
                if self.player.is_dead():
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        if self.state == STATE_QUIZ:
            self.quiz_engine.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self):
        cam_x, cam_y = self._camera()
        self.screen.fill((0, 0, 0))

        # Clip rendering to the game viewport area
        game_clip = pygame.Rect(0, 0, GAME_W, GAME_H)
        self.screen.set_clip(game_clip)

        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)
        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)
        for m in self.monsters:
            if m.alive:
                self.renderer.draw_entity(m.x, m.y, m.color, cam_x, cam_y, self.visible)
        self.renderer.draw_player(self.player, cam_x, cam_y)

        self.screen.set_clip(None)

        # Message log below game viewport
        self.msg_log.draw(self.screen, 0, GAME_H, GAME_W, MSG_H)

        # Sidebar
        self.sidebar.draw(self.player, self.dungeon_level, self.turn_count)

        # Overlays (drawn on top of everything, no clipping)
        if self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_EQUIP_MENU:
            self._draw_equip_menu()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
        elif self.state == STATE_DEAD:
            self._draw_death_screen()

        pygame.display.flip()

    def _camera(self) -> tuple[int, int]:
        cam_x = self.player.x - VIEWPORT_W // 2
        cam_y = self.player.y - VIEWPORT_H // 2
        cam_x = max(0, min(cam_x, self.dungeon.width  - VIEWPORT_W))
        cam_y = max(0, min(cam_y, self.dungeon.height - VIEWPORT_H))
        return cam_x, cam_y

    # ------------------------------------------------------------------
    # Quiz modal
    # ------------------------------------------------------------------

    def _draw_quiz(self):
        qe = self.quiz_engine
        if not qe.current_question:
            return

        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 740, 410
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (16, 16, 38), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 140), (bx, by, bw, bh), 2, border_radius=12)

        hdr = self.font_md.render(self.quiz_title, True, (255, 200, 60))
        self.screen.blit(hdr, (bx + 18, by + 14))

        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            counter_text  = f"Chain: {qe.chain}"
            counter_color = (80, 255, 120)
        else:
            counter_text  = f"{qe.correct_count}/{qe.required} correct"
            counter_color = (120, 200, 255)
        c_surf = self.font_md.render(counter_text, True, counter_color)
        self.screen.blit(c_surf, (bx + bw - c_surf.get_width() - 18, by + 14))

        bar_x, bar_y, bar_w, bar_h = bx + 18, by + 50, bw - 36, 10
        ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))
        pygame.draw.rect(self.screen, (40, 15, 15), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        bar_color = (
            (50, 200, 50)  if ratio > 0.50 else
            (210, 160, 40) if ratio > 0.25 else
            (210, 50, 50)
        )
        pygame.draw.rect(
            self.screen, bar_color,
            (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=5
        )

        q_text = qe.current_question.get('question', '')
        q_surf = self.font_lg.render(q_text, True, (255, 255, 255))
        self.screen.blit(q_surf, (bx + 18, by + 78))

        choices   = qe.current_question.get('choices', [])
        labels    = ['1', '2', '3', '4']
        cw, ch    = 340, 72
        positions = [
            (bx + 18,        by + 165),
            (bx + 18 + 364,  by + 165),
            (bx + 18,        by + 255),
            (bx + 18 + 364,  by + 255),
        ]
        correct_str = str(qe.current_question.get('answer', '')).strip().lower()
        selected    = qe.last_answer.strip().lower()

        for i, (choice, (cx, cy)) in enumerate(zip(choices, positions)):
            c_lower     = choice.strip().lower()
            is_correct  = c_lower == correct_str
            is_selected = bool(selected) and c_lower == selected

            if qe.state == QuizState.RESULT:
                if is_correct:
                    bg, border = (18, 72, 18),  (50, 210, 50)
                elif is_selected:
                    bg, border = (72, 18, 18),  (210, 50, 50)
                else:
                    bg, border = (22, 22, 52),  (55, 55, 100)
            else:
                bg, border = (24, 24, 56), (65, 65, 120)

            pygame.draw.rect(self.screen, bg,     (cx, cy, cw, ch), border_radius=8)
            pygame.draw.rect(self.screen, border, (cx, cy, cw, ch), 2, border_radius=8)

            lbl = self.font_md.render(f"[{labels[i]}]", True, (160, 160, 80))
            self.screen.blit(lbl, (cx + 12, cy + (ch - lbl.get_height()) // 2))

            c_surf = self.font_md.render(str(choice), True, (220, 220, 220))
            self.screen.blit(c_surf, (cx + 68, cy + (ch - c_surf.get_height()) // 2))

        if qe.state == QuizState.RESULT:
            fb_text  = "CORRECT!" if qe.last_correct else "WRONG!"
            fb_color = (80, 255, 80)  if qe.last_correct else (255, 80, 80)
            fb = self.font_lg.render(fb_text, True, fb_color)
            self.screen.blit(fb, (bx + (bw - fb.get_width()) // 2, by + bh - 52))

        if qe.state == QuizState.ASKING:
            hint = self.font_sm.render("Press 1-4 to answer", True, (120, 120, 160))
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 28))

    # ------------------------------------------------------------------
    # Equip menu overlay
    # ------------------------------------------------------------------

    def _draw_equip_menu(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        bw = 560
        bh = min(80 + len(self.equip_menu_items) * 48 + 60, 500)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (16, 20, 36), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 140), (bx, by, bw, bh), 2, border_radius=12)

        self.screen.blit(
            self.font_md.render("EQUIP ITEM", True, (255, 200, 60)),
            (bx + 20, by + 16)
        )

        p = self.player
        eq_str = self.font_sm.render(
            f"Weapon: {p.weapon.name if p.weapon else 'none'}   AC: {p.get_ac()}",
            True, (160, 200, 160)
        )
        self.screen.blit(eq_str, (bx + 20, by + 44))
        pygame.draw.line(self.screen, (60, 60, 100),
                         (bx + 10, by + 66), (bx + bw - 10, by + 66))

        for i, item in enumerate(self.equip_menu_items):
            iy = by + 76 + i * 48
            row_bg = (28, 28, 58) if i % 2 == 0 else (22, 22, 48)
            pygame.draw.rect(self.screen, row_bg, (bx + 10, iy, bw - 20, 42), border_radius=6)
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, (160, 160, 80)),
                (bx + 18, iy + 11)
            )
            self.screen.blit(
                self.font_md.render(item.name, True, (220, 220, 220)),
                (bx + 70, iy + 11)
            )
            if isinstance(item, Weapon):
                detail = self.font_sm.render(
                    f"weapon  {item.damage}  chain x{item.max_chain_length or '?'}",
                    True, (160, 200, 160)
                )
            elif isinstance(item, (Armor, Shield)):
                detail = self.font_sm.render(
                    f"{getattr(item, 'slot', 'shield')}  +{item.ac_bonus} AC"
                    f"  (quiz: geography x{item.equip_threshold})",
                    True, (160, 180, 220)
                )
            else:
                detail = self.font_sm.render(item.item_class, True, (140, 140, 140))
            self.screen.blit(detail, (bx + 70, iy + 30))

        hint_y = by + bh - 34
        pygame.draw.line(self.screen, (60, 60, 100),
                         (bx + 10, hint_y - 8), (bx + bw - 10, hint_y - 8))
        hint = self.font_sm.render(
            "Press number to equip  |  ESC to cancel", True, (120, 120, 160)
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Cook menu overlay
    # ------------------------------------------------------------------

    def _draw_cook_menu(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        bw = 560
        bh = min(80 + len(self.cook_menu_items) * 48 + 60, 500)
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (20, 16, 10), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (140, 100, 40), (bx, by, bw, bh), 2, border_radius=12)

        self.screen.blit(
            self.font_md.render("COOK INGREDIENT", True, (255, 200, 60)),
            (bx + 20, by + 16)
        )
        self.screen.blit(
            self.font_sm.render(
                f"SP: {self.player.sp}/{self.player.max_sp}  (cooking restores SP + stats)",
                True, (200, 180, 120)
            ),
            (bx + 20, by + 44)
        )
        pygame.draw.line(self.screen, (100, 80, 40),
                         (bx + 10, by + 66), (bx + bw - 10, by + 66))

        for i, item in enumerate(self.cook_menu_items):
            iy = by + 76 + i * 48
            row_bg = (30, 22, 12) if i % 2 == 0 else (24, 18, 10)
            pygame.draw.rect(self.screen, row_bg, (bx + 10, iy, bw - 20, 42), border_radius=6)
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, (200, 160, 60)),
                (bx + 18, iy + 11)
            )
            self.screen.blit(
                self.font_md.render(item.name, True, (220, 220, 200)),
                (bx + 70, iy + 11)
            )
            best = item.recipes.get('5', item.recipes.get('3', {}))
            self.screen.blit(
                self.font_sm.render(f"best: {best.get('name', '?')}", True, (180, 160, 100)),
                (bx + 70, iy + 30)
            )

        hint_y = by + bh - 34
        pygame.draw.line(self.screen, (100, 80, 40),
                         (bx + 10, hint_y - 8), (bx + bw - 10, hint_y - 8))
        hint = self.font_sm.render(
            "Press number to cook  |  ESC to cancel", True, (160, 140, 80)
        )
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, hint_y))

    # ------------------------------------------------------------------
    # Death screen
    # ------------------------------------------------------------------

    def _draw_death_screen(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))
        dead = self.font_lg.render("YOU HAVE DIED", True, (255, 80, 80))
        sub  = self.font_md.render("Press ESC to quit", True, (200, 200, 200))
        self.screen.blit(dead, ((GAME_W - dead.get_width()) // 2, WINDOW_H // 2 - 36))
        self.screen.blit(sub,  ((GAME_W - sub.get_width())  // 2, WINDOW_H // 2 + 14))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    game    = Game(screen)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        game.update(dt)
        game.render()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
