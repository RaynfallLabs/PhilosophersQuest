import sys
import pygame

from combat import player_attack
from dungeon import generate_dungeon, spawn_monsters, spawn_items, STAIRS_UP, STAIRS_DOWN
from food_system import harvest_corpse, cook_ingredient
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse, Ingredient, Artifact
from level_manager import LevelManager
from player import Player
from quiz_engine import QuizEngine, QuizMode, QuizState
from renderer import Renderer, TILE_SIZE
from ui import Sidebar, MessageLog, SIDEBAR_W

WINDOW_W = 1280
WINDOW_H = 720
FPS      = 60

GAME_W = WINDOW_W - SIDEBAR_W      # 980 px
MSG_H  = 144
GAME_H = WINDOW_H - MSG_H          # 576 px = 18 tiles

VIEWPORT_W = GAME_W // TILE_SIZE    # 30
VIEWPORT_H = GAME_H // TILE_SIZE    # 18

# Game states
STATE_PLAYER       = 'player'
STATE_QUIZ         = 'quiz'
STATE_EQUIP_MENU   = 'equip_menu'
STATE_COOK_MENU    = 'cook_menu'
STATE_CONFIRM_EXIT = 'confirm_exit'
STATE_VICTORY      = 'victory'
STATE_DEAD         = 'dead'


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen    = screen
        self.font_sm   = pygame.font.SysFont('consolas', 15)
        self.font_md   = pygame.font.SysFont('consolas', 20)
        self.font_lg   = pygame.font.SysFont('consolas', 28, bold=True)
        self.font_xl   = pygame.font.SysFont('consolas', 36, bold=True)

        self.quiz_engine        = QuizEngine()
        self.msg_log            = MessageLog()
        self.sidebar            = Sidebar(screen, GAME_W)
        self.level_mgr          = LevelManager()
        self.state              = STATE_PLAYER
        self.combat_target      = None
        self.quiz_title         = ''
        self.equip_menu_items: list = []
        self.cook_menu_items: list  = []
        self.turn_count         = 0
        self.dungeon_level      = 1
        self.defeat_reason      = 'died'   # 'died' | 'starved' | 'fled'
        self._slow_skip         = False    # toggled each turn when slowed

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
        """Initial game setup only — creates fresh player."""
        self.dungeon_level           = level
        dungeon, monsters, items     = self.level_mgr.generate(level)
        self.dungeon                 = dungeon
        self.monsters                = monsters
        self.ground_items            = items
        self.player                  = Player()
        self.player.x, self.player.y = dungeon.rooms[0].center
        self.renderer                = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
        self._refresh_fov()
        self.add_message("You enter the dungeon. Find the Philosopher's Stone!", 'info')

    def _change_level(self, new_level: int, enter_from_top: bool):
        """Transition between levels, preserving the player."""
        # Save current level state
        self.level_mgr.save(
            self.dungeon_level, self.dungeon, self.monsters, self.ground_items
        )

        # Load saved or generate fresh
        saved = self.level_mgr.load(new_level)
        if saved:
            dungeon, monsters, ground_items = saved
        else:
            dungeon, monsters, ground_items = self.level_mgr.generate(new_level)

        self.dungeon      = dungeon
        self.monsters     = monsters
        self.ground_items = ground_items
        self.dungeon_level = new_level

        # Place player at the stairs they came through
        if enter_from_top:
            self.player.x, self.player.y = dungeon.rooms[0].center
            self.add_message(f"You descend to level {new_level}.", 'info')
        else:
            self.player.x, self.player.y = dungeon.rooms[-1].center
            self.add_message(f"You ascend to level {new_level}.", 'info')

        self._refresh_fov()

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

        key = event.key

        if key == pygame.K_ESCAPE:
            if self.state in (STATE_EQUIP_MENU, STATE_COOK_MENU, STATE_CONFIRM_EXIT):
                self.state = STATE_PLAYER
                return True
            if self.state in (STATE_DEAD, STATE_VICTORY):
                return False
            return False

        if self.state == STATE_PLAYER:
            # Stair keys checked by unicode to handle shift+. / shift+,
            if event.unicode == '>':
                self._descend_stairs()
                return True
            if event.unicode == '<':
                self._ascend_stairs()
                return True
            self._player_input(key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(key)
        elif self.state == STATE_EQUIP_MENU:
            self._equip_menu_input(key)
        elif self.state == STATE_COOK_MENU:
            self._cook_menu_input(key)
        elif self.state == STATE_CONFIRM_EXIT:
            self._confirm_exit_input(key)

        return True

    _MOVE_KEYS = {
        pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_l: (1,  0),
    }

    def _player_input(self, key: int):
        import random as _rng

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

        # Sleep: skip turn
        if self.player.has_effect('sleeping'):
            self.add_message("You are fast asleep!", 'warning')
            self._advance_turn()
            return

        # Paralyzed: skip turn
        if self.player.has_effect('paralyzed'):
            self.add_message("You are paralyzed and cannot move!", 'danger')
            self._advance_turn()
            return

        # Slowed: skip every other turn
        if self.player.has_effect('slowed'):
            self._slow_skip = not self._slow_skip
            if self._slow_skip:
                self.add_message("You move sluggishly.", 'warning')
                self._advance_turn()
                return

        # Fumbling: 20% chance to waste turn
        if self.player.has_effect('fumbling') and _rng.random() < 0.20:
            self.add_message("You stumble and waste your turn!", 'warning')
            self._advance_turn()
            return

        # Stunned: 25% chance to fail
        if self.player.has_effect('stunned') and _rng.random() < 0.25:
            self.add_message("You are too dazed to act!", 'warning')
            self._advance_turn()
            return

        dx, dy = self._MOVE_KEYS[key]

        # Confused: randomize direction
        if self.player.has_effect('confused'):
            dx, dy = _rng.choice(
                [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(1,-1),(1,1)]
            )
            self.add_message("You stumble in a random direction!", 'warning')

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
            if self.state != STATE_DEAD:
                self._notify_stairs(nx, ny)
                self._advance_turn()
                # Haste: grant a free second move
                if self.player.has_effect('hasted') and self.state == STATE_PLAYER:
                    self.add_message("You move with supernatural speed!", 'info')

    def _notify_stairs(self, x: int, y: int):
        tile = self.dungeon.tiles[y][x]
        if tile == STAIRS_DOWN:
            self.add_message("Stairs lead down here  —  press '>' to descend.", 'info')
        elif tile == STAIRS_UP:
            if self.dungeon_level == 1:
                self.add_message("The dungeon exit  —  press '<' to leave.", 'warning')
            else:
                self.add_message("Stairs lead up here  —  press '<' to ascend.", 'info')

    # ------------------------------------------------------------------
    # Stair navigation
    # ------------------------------------------------------------------

    def _descend_stairs(self):
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_DOWN:
            self.add_message("There are no stairs leading down here.", 'info')
            return
        self._change_level(self.dungeon_level + 1, enter_from_top=True)

    def _ascend_stairs(self):
        px, py = self.player.x, self.player.y
        if self.dungeon.tiles[py][px] != STAIRS_UP:
            self.add_message("There are no stairs leading up here.", 'info')
            return
        if self.dungeon_level == 1:
            self.state = STATE_CONFIRM_EXIT
        else:
            self._change_level(self.dungeon_level - 1, enter_from_top=False)

    def _confirm_exit_input(self, key: int):
        if key in (pygame.K_y, pygame.K_RETURN):
            self._do_exit()
        elif key in (pygame.K_n, pygame.K_ESCAPE):
            self.state = STATE_PLAYER

    def _do_exit(self):
        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )
        if has_stone:
            self.state = STATE_VICTORY
        else:
            self.defeat_reason = 'fled'
            self.state = STATE_DEAD

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _calc_score(self) -> int:
        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )
        return (
            self.turn_count * 10
            + self.level_mgr.max_level_reached * 1000
            + self.level_mgr.monsters_killed * 100
            + (50000 if has_stone else 0)
        )

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------

    def _advance_turn(self):
        self.turn_count += 1

        # Tick all player status effects
        effect_msgs = self.player.tick_effects()
        for text, mtype in effect_msgs:
            if text == '_teleport':
                self._teleport_player()
            elif text == '_petrify_death':
                self.defeat_reason = 'died'
                self.state = STATE_DEAD
                self.add_message("You have turned completely to stone!", 'danger')
            else:
                self.add_message(text, mtype)

        if self.state == STATE_DEAD:
            return

        # Warning: alert for nearby monsters
        self._do_warning()
        # Searching: auto-reveal adjacent tiles
        self._do_searching()

        self._do_monster_turns()

    def _teleport_player(self):
        import random as _rng
        floors = [
            (x, y)
            for y in range(self.dungeon.height)
            for x in range(self.dungeon.width)
            if self.dungeon.is_walkable(x, y)
            and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
        ]
        if floors:
            self.player.x, self.player.y = _rng.choice(floors)
            self._refresh_fov()
            self.add_message("You feel disoriented as space warps around you!", 'warning')

    def _do_warning(self):
        """Warn if monsters are within 5 tiles when player has the warning effect."""
        if not self.player.has_effect('warning'):
            return
        px, py = self.player.x, self.player.y
        nearby = [
            m for m in self.monsters
            if m.alive and abs(m.x - px) <= 5 and abs(m.y - py) <= 5
            and (m.x, m.y) not in self.visible
        ]
        if nearby:
            self.add_message(
                f"Your danger sense tingles! ({len(nearby)} unseen threat{'s' if len(nearby) > 1 else ''} near)",
                'warning'
            )

    def _do_searching(self):
        """Auto-reveal adjacent tiles when player has the searching effect."""
        if not self.player.has_effect('searching'):
            return
        px, py = self.player.x, self.player.y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.dungeon.width and 0 <= ny < self.dungeon.height:
                    if hasattr(self.dungeon, 'explored'):
                        self.dungeon.explored.add((nx, ny))

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
            self.add_message(f"Starving! You take {dmg} damage.", 'danger')
            if self.player.is_dead():
                self.defeat_reason = 'starved'
                self.state = STATE_DEAD
                self.add_message("You have starved to death! Press ESC to quit.", 'danger')

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
            if isinstance(item, Artifact) and item.id == 'philosophers_stone':
                self.add_message(
                    "The Philosopher's Stone! Return to the surface to win!", 'loot'
                )
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
            self.add_message(message, 'loot' if ingredient is not None else 'warning')
            if ingredient is not None:
                if not self.player.add_to_inventory(ingredient):
                    self.ground_items.append(ingredient)
                    ingredient.x, ingredient.y = px, py
                    self.add_message(
                        f"Too heavy — {ingredient.name} dropped.", 'warning'
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
            pygame.K_3: 2, pygame.K_KP3: 2,
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
                self.add_message(msg, 'warning' if (i == 0 and 'ruin' in msg.lower()) else 'success')
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
                        f"You struggle with the {item_name} and give up.", 'warning'
                    )
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='threshold',
                subject='geography',
                tier=1,
                callback=on_complete,
                threshold=item.equip_threshold,
                wisdom=self.player.WIS,
                timer_modifier=self.player.get_quiz_timer_modifier(),
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
                    self.level_mgr.monsters_killed += 1
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
            qe = self.quiz_engine
            # Map displayed position back to actual choice via confused_order
            if qe.confused_order and len(qe.confused_order) == len(choices):
                actual_idx = qe.confused_order[idx]
            else:
                actual_idx = idx
            self.quiz_engine.answer(choices[actual_idx])

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
                    self.defeat_reason = 'died'
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

        game_clip = pygame.Rect(0, 0, GAME_W, GAME_H)
        self.screen.set_clip(game_clip)
        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)
        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)
        for m in self.monsters:
            if m.alive:
                self.renderer.draw_entity(m.x, m.y, m.color, cam_x, cam_y, self.visible)
        # Telepathy: render unseen monsters as dim dots
        if self.player.has_effect('telepathy'):
            for m in self.monsters:
                if m.alive and (m.x, m.y) not in self.visible:
                    self.renderer.draw_entity(m.x, m.y, (70, 70, 120), cam_x, cam_y, None)
        self.renderer.draw_player(self.player, cam_x, cam_y)
        self.screen.set_clip(None)

        self.msg_log.draw(self.screen, 0, GAME_H, GAME_W, MSG_H)
        self.sidebar.draw(self.player, self.dungeon_level, self.turn_count)

        if self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_EQUIP_MENU:
            self._draw_equip_menu()
        elif self.state == STATE_COOK_MENU:
            self._draw_cook_menu()
        elif self.state == STATE_CONFIRM_EXIT:
            self._draw_confirm_exit()
        elif self.state == STATE_VICTORY:
            self._draw_victory_screen()
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

        self.screen.blit(
            self.font_md.render(self.quiz_title, True, (255, 200, 60)),
            (bx + 18, by + 14)
        )

        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            counter_text, counter_color = f"Chain: {qe.chain}", (80, 255, 120)
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
            (210, 50,  50)
        )
        pygame.draw.rect(
            self.screen, bar_color,
            (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=5
        )

        q_surf = self.font_lg.render(
            qe.current_question.get('question', ''), True, (255, 255, 255)
        )
        self.screen.blit(q_surf, (bx + 18, by + 78))

        choices   = qe.current_question.get('choices', [])
        # Confused players see choices in a scrambled order
        if qe.confused_order and len(qe.confused_order) == len(choices):
            display_choices = [choices[i] for i in qe.confused_order]
        else:
            display_choices = choices
        cw, ch    = 340, 72
        positions = [
            (bx + 18,       by + 165), (bx + 18 + 364, by + 165),
            (bx + 18,       by + 255), (bx + 18 + 364, by + 255),
        ]
        correct_str = str(qe.current_question.get('answer', '')).strip().lower()
        selected    = qe.last_answer.strip().lower()

        for i, (choice, (cx, cy)) in enumerate(zip(display_choices, positions)):
            c_lower    = choice.strip().lower()
            is_correct  = c_lower == correct_str
            is_selected = bool(selected) and c_lower == selected

            if qe.state == QuizState.RESULT:
                bg, border = (
                    ((18, 72, 18), (50, 210, 50))   if is_correct  else
                    ((72, 18, 18), (210, 50, 50))   if is_selected else
                    ((22, 22, 52), (55, 55, 100))
                )
            else:
                bg, border = (24, 24, 56), (65, 65, 120)

            pygame.draw.rect(self.screen, bg,     (cx, cy, cw, ch), border_radius=8)
            pygame.draw.rect(self.screen, border, (cx, cy, cw, ch), 2, border_radius=8)

            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, (160, 160, 80)),
                (cx + 12, cy + (ch - self.font_md.get_height()) // 2)
            )
            self.screen.blit(
                self.font_md.render(str(choice), True, (220, 220, 220)),
                (cx + 68, cy + (ch - self.font_md.get_height()) // 2)
            )

        if qe.state == QuizState.RESULT:
            fb = self.font_lg.render(
                "CORRECT!" if qe.last_correct else "WRONG!",
                True,
                (80, 255, 80) if qe.last_correct else (255, 80, 80)
            )
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
            self.font_md.render("EQUIP ITEM", True, (255, 200, 60)), (bx + 20, by + 16)
        )
        p = self.player
        self.screen.blit(
            self.font_sm.render(
                f"Weapon: {p.weapon.name if p.weapon else 'none'}   AC: {p.get_ac()}",
                True, (160, 200, 160)
            ),
            (bx + 20, by + 44)
        )
        pygame.draw.line(self.screen, (60, 60, 100),
                         (bx + 10, by + 66), (bx + bw - 10, by + 66))

        for i, item in enumerate(self.equip_menu_items):
            iy = by + 76 + i * 48
            pygame.draw.rect(
                self.screen,
                (28, 28, 58) if i % 2 == 0 else (22, 22, 48),
                (bx + 10, iy, bw - 20, 42), border_radius=6
            )
            self.screen.blit(
                self.font_md.render(f"[{i+1}]", True, (160, 160, 80)), (bx + 18, iy + 11)
            )
            self.screen.blit(
                self.font_md.render(item.name, True, (220, 220, 220)), (bx + 70, iy + 11)
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
            pygame.draw.rect(
                self.screen,
                (30, 22, 12) if i % 2 == 0 else (24, 18, 10),
                (bx + 10, iy, bw - 20, 42), border_radius=6
            )
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
    # Confirm exit overlay
    # ------------------------------------------------------------------

    def _draw_confirm_exit(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 500, 200
        bx = (GAME_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (20, 20, 38), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (100, 100, 160), (bx, by, bw, bh), 2, border_radius=12)

        has_stone = any(
            isinstance(i, Artifact) and i.id == 'philosophers_stone'
            for i in self.player.inventory
        )

        if has_stone:
            title = self.font_lg.render("LEAVE THE DUNGEON?", True, (255, 215, 0))
            sub   = self.font_md.render(
                "You carry the Philosopher's Stone!", True, (255, 215, 0)
            )
        else:
            title = self.font_lg.render("LEAVE THE DUNGEON?", True, (220, 200, 80))
            sub   = self.font_md.render(
                "You don't have the Philosopher's Stone.", True, (200, 160, 80)
            )

        self.screen.blit(title, (bx + (bw - title.get_width()) // 2, by + 30))
        self.screen.blit(sub,   (bx + (bw - sub.get_width())   // 2, by + 76))

        hint = self.font_md.render("[Y] Leave   [N] Stay", True, (160, 200, 160))
        self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + 136))

    # ------------------------------------------------------------------
    # Victory screen
    # ------------------------------------------------------------------

    def _draw_victory_screen(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((20, 15, 0, 200))
        self.screen.blit(overlay, (0, 0))

        score = self._calc_score()
        cx    = GAME_W // 2

        title = self.font_xl.render("VICTORY!", True, (255, 215, 0))
        self.screen.blit(title, (cx - title.get_width() // 2, 140))

        sub = self.font_lg.render(
            "You retrieved the Philosopher's Stone!", True, (255, 240, 160)
        )
        self.screen.blit(sub, (cx - sub.get_width() // 2, 205))

        score_surf = self.font_lg.render(f"Final Score: {score:,}", True, (255, 215, 0))
        self.screen.blit(score_surf, (cx - score_surf.get_width() // 2, 270))

        details = self.font_md.render(
            f"Turns: {self.turn_count}   |   "
            f"Deepest Level: {self.level_mgr.max_level_reached}   |   "
            f"Kills: {self.level_mgr.monsters_killed}",
            True, (200, 180, 120)
        )
        self.screen.blit(details, (cx - details.get_width() // 2, 326))

        breakdown = self.font_sm.render(
            f"({self.turn_count}×10 turns)  +  "
            f"({self.level_mgr.max_level_reached}×1000 depth)  +  "
            f"({self.level_mgr.monsters_killed}×100 kills)  +  50000 stone bonus",
            True, (160, 145, 90)
        )
        self.screen.blit(breakdown, (cx - breakdown.get_width() // 2, 358))

        hint = self.font_md.render("Press ESC to quit", True, (140, 180, 140))
        self.screen.blit(hint, (cx - hint.get_width() // 2, 420))

    # ------------------------------------------------------------------
    # Death / defeat screen
    # ------------------------------------------------------------------

    def _draw_death_screen(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        score = self._calc_score()
        cx    = GAME_W // 2

        if self.defeat_reason == 'fled':
            title_text = "YOU FLED THE DUNGEON"
            sub_text   = "You left without the Philosopher's Stone."
        elif self.defeat_reason == 'starved':
            title_text = "YOU HAVE STARVED"
            sub_text   = f"You starved on dungeon level {self.dungeon_level}."
        else:
            title_text = "YOU HAVE DIED"
            sub_text   = f"You were slain on dungeon level {self.dungeon_level}."

        title = self.font_xl.render(title_text, True, (255, 80, 80))
        self.screen.blit(title, (cx - title.get_width() // 2, 160))

        sub = self.font_lg.render(sub_text, True, (200, 160, 160))
        self.screen.blit(sub, (cx - sub.get_width() // 2, 218))

        score_surf = self.font_lg.render(f"Final Score: {score:,}", True, (220, 180, 80))
        self.screen.blit(score_surf, (cx - score_surf.get_width() // 2, 280))

        details = self.font_md.render(
            f"Turns: {self.turn_count}   |   "
            f"Deepest Level: {self.level_mgr.max_level_reached}   |   "
            f"Kills: {self.level_mgr.monsters_killed}",
            True, (180, 150, 150)
        )
        self.screen.blit(details, (cx - details.get_width() // 2, 330))

        hint = self.font_md.render("Press ESC to quit", True, (160, 130, 130))
        self.screen.blit(hint, (cx - hint.get_width() // 2, 390))


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
