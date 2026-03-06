import sys
import pygame

from combat import player_attack
from dungeon import generate_dungeon, spawn_monsters, spawn_items
from fov import calculate_fov
from items import Weapon, Armor, Shield, Corpse
from player import Player
from quiz_engine import QuizEngine, QuizMode, QuizState
from renderer import Renderer, TILE_SIZE

WINDOW_W  = 1280
WINDOW_H  = 720
FPS       = 60

VIEWPORT_W = WINDOW_W // TILE_SIZE   # 40 tiles
VIEWPORT_H = WINDOW_H // TILE_SIZE   # 22 tiles

MSG_MAX = 8

# Game states
STATE_PLAYER      = 'player'
STATE_QUIZ        = 'quiz'
STATE_EQUIP_MENU  = 'equip_menu'
STATE_DEAD        = 'dead'


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_sm = pygame.font.SysFont('consolas', 15)
        self.font_md = pygame.font.SysFont('consolas', 20)
        self.font_lg = pygame.font.SysFont('consolas', 28, bold=True)

        self.quiz_engine        = QuizEngine()
        self.messages: list[str] = []
        self.state              = STATE_PLAYER
        self.combat_target      = None
        self.quiz_title         = ''          # set before each quiz start
        self.equip_menu_items: list = []      # items shown in equip menu

        self._new_level(1)

    # ------------------------------------------------------------------
    # Level setup
    # ------------------------------------------------------------------

    def _new_level(self, level: int):
        self.dungeon      = generate_dungeon(80, 50, level)
        self.player       = Player()
        self.player.x, self.player.y = self.dungeon.rooms[0].center
        self.monsters     = spawn_monsters(self.dungeon.rooms, level, self.dungeon)
        self.ground_items = spawn_items(self.dungeon.rooms, level, self.dungeon)
        self.renderer     = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
        self._refresh_fov()
        self.log(f"You descend to dungeon level {level}.")

    def _refresh_fov(self):
        self.visible = calculate_fov(
            self.dungeon, self.player.x, self.player.y,
            self.player.get_sight_radius()
        )

    # ------------------------------------------------------------------
    # Message log
    # ------------------------------------------------------------------

    def log(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > MSG_MAX:
            self.messages.pop(0)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True

        if event.key == pygame.K_ESCAPE:
            if self.state == STATE_EQUIP_MENU:
                self.state = STATE_PLAYER
                return True
            return False  # quit

        if self.state == STATE_PLAYER:
            self._player_input(event.key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(event.key)
        elif self.state == STATE_EQUIP_MENU:
            self._equip_menu_input(event.key)

        return True

    _MOVE_KEYS = {
        pygame.K_UP: (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN: (0, 1), pygame.K_j: (0, 1),
        pygame.K_LEFT: (-1, 0), pygame.K_h: (-1, 0),
        pygame.K_RIGHT: (1, 0), pygame.K_l: (1, 0),
    }

    def _player_input(self, key: int):
        # Pick up item
        if key in (pygame.K_g, pygame.K_COMMA):
            self._pickup()
            return

        # Open equip menu
        if key == pygame.K_e:
            self._open_equip_menu()
            return

        if key not in self._MOVE_KEYS:
            return

        # Paralysis check
        paralyzed = self.player.status_effects.get('paralyzed', 0)
        if paralyzed > 0:
            self.player.status_effects['paralyzed'] = paralyzed - 1
            remaining = paralyzed - 1
            self.log(f"You are paralyzed! ({remaining} turn{'s' if remaining != 1 else ''} left)")
            self._do_monster_turns()
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
            self._do_monster_turns()

    # ------------------------------------------------------------------
    # Pickup
    # ------------------------------------------------------------------

    def _pickup(self):
        px, py = self.player.x, self.player.y
        item = next((i for i in self.ground_items if i.x == px and i.y == py), None)
        if item is None:
            self.log("There is nothing here to pick up.")
            return
        if self.player.add_to_inventory(item):
            self.ground_items.remove(item)
            self.log(f"You pick up the {item.name}.")
            self._do_monster_turns()
        else:
            self.log("You are carrying too much to pick that up.")

    # ------------------------------------------------------------------
    # Equip menu
    # ------------------------------------------------------------------

    def _open_equip_menu(self):
        self.equip_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Weapon, Armor, Shield))
        ]
        if not self.equip_menu_items:
            self.log("You have nothing equippable in your inventory.")
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
            # Weapons equip instantly — no quiz needed
            self.player._apply_equip(item)
            self.player.remove_from_inventory(item)
            self.log(f"You equip the {item.name}.")
            self._do_monster_turns()

        elif isinstance(item, (Armor, Shield)):
            item_name = item.name
            self.quiz_title = f"EQUIPPING {item_name.upper()}  —  GEOGRAPHY"
            self.state = STATE_QUIZ

            def on_complete(result):
                self.state = STATE_PLAYER
                if result.success:
                    self.player._apply_equip(item)
                    self.player.remove_from_inventory(item)
                    self.log(
                        f"You equip the {item_name}. AC is now {self.player.get_ac()}."
                    )
                else:
                    self.log(f"You struggle to put on the {item_name} and give up.")
                self._do_monster_turns()

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
        weapon_name = self.player.weapon.name if self.player.weapon else 'bare hands'
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  —  MATH CHAIN"

        # Floating eye: paralyze on melee contact
        if monster.kind == 'floating_eye':
            cur = self.player.status_effects.get('paralyzed', 0)
            self.player.status_effects['paralyzed'] = max(cur, 3)
            self.log("The floating eye's gaze paralyzes you!")

        def on_complete(damage: int, killed: bool, chain: int):
            self.state = STATE_PLAYER
            if chain == 0:
                self.log(f"You swing wildly at the {monster.name} and miss!")
            else:
                self.log(
                    f"Chain x{chain}! You strike the {monster.name} for {damage} damage!"
                )
                if killed:
                    self.log(f"The {monster.name} is slain!")
                    self.ground_items.append(
                        Corpse(monster.name, monster.kind, monster.x, monster.y)
                    )
            self._do_monster_turns()

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
                self.log(msg)
                if self.player.is_dead():
                    self.state = STATE_DEAD
                    self.log("You have died! Press ESC to quit.")
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
        self.renderer.draw_dungeon(self.dungeon, self.visible, cam_x, cam_y)

        for item in self.ground_items:
            self.renderer.draw_item(item, cam_x, cam_y, self.visible)

        for m in self.monsters:
            if m.alive:
                self.renderer.draw_entity(
                    m.x, m.y, m.color, cam_x, cam_y, self.visible
                )

        self.renderer.draw_player(self.player, cam_x, cam_y)

        self._draw_hud()
        self._draw_messages()

        if self.state == STATE_QUIZ:
            self._draw_quiz()
        elif self.state == STATE_EQUIP_MENU:
            self._draw_equip_menu()
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
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self):
        p = self.player
        weapon_str  = p.weapon.name if p.weapon else 'bare hands'
        paralyzed   = p.status_effects.get('paralyzed', 0)
        status      = f"  [PARALYZED:{paralyzed}]" if paralyzed else ""
        text = (
            f"HP {p.hp}/{p.max_hp}  AC {p.get_ac()}"
            f"  |  {weapon_str}"
            f"  |  SP {p.sp}/{p.max_sp}  MP {p.mp}/{p.max_mp}"
            f"  WIS {p.WIS}{status}"
        )
        surf = self.font_sm.render(text, True, (220, 210, 100))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, WINDOW_W, 22))
        self.screen.blit(surf, (8, 4))

    # ------------------------------------------------------------------
    # Message log
    # ------------------------------------------------------------------

    def _draw_messages(self):
        msgs   = self.messages[-6:]
        line_h = 19
        box_h  = len(msgs) * line_h + 8
        box_y  = WINDOW_H - box_h
        pygame.draw.rect(self.screen, (0, 0, 0), (0, box_y, 760, box_h))
        for i, msg in enumerate(msgs):
            age    = len(msgs) - 1 - i
            bright = max(110, 220 - age * 28)
            surf   = self.font_sm.render(msg, True, (bright, bright, bright))
            self.screen.blit(surf, (8, box_y + 4 + i * line_h))

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
        bx = (WINDOW_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (16, 16, 38), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 140), (bx, by, bw, bh), 2, border_radius=12)

        # Header (context-aware title)
        hdr = self.font_md.render(self.quiz_title, True, (255, 200, 60))
        self.screen.blit(hdr, (bx + 18, by + 14))

        # Counter — chain for chain mode, progress for threshold mode
        if qe.mode in (QuizMode.CHAIN, QuizMode.ESCALATOR_CHAIN):
            counter_text  = f"Chain: {qe.chain}"
            counter_color = (80, 255, 120)
        else:
            counter_text  = f"{qe.correct_count}/{qe.required} correct"
            counter_color = (120, 200, 255)
        c_surf = self.font_md.render(counter_text, True, counter_color)
        self.screen.blit(c_surf, (bx + bw - c_surf.get_width() - 18, by + 14))

        # Timer bar
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

        # Question
        q_text = qe.current_question.get('question', '')
        q_surf = self.font_lg.render(q_text, True, (255, 255, 255))
        self.screen.blit(q_surf, (bx + 18, by + 78))

        # Answer choices — 2×2 grid
        choices    = qe.current_question.get('choices', [])
        labels     = ['1', '2', '3', '4']
        cw, ch     = 340, 72
        positions  = [
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
            if qe.last_correct:
                fb = self.font_lg.render("CORRECT!", True, (80, 255, 80))
            else:
                fb = self.font_lg.render("WRONG!", True, (255, 80, 80))
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

        bw, bh = 560, min(80 + len(self.equip_menu_items) * 48 + 60, 500)
        bx = (WINDOW_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (16, 20, 36), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 140), (bx, by, bw, bh), 2, border_radius=12)

        title = self.font_md.render("EQUIP ITEM", True, (255, 200, 60))
        self.screen.blit(title, (bx + 20, by + 16))

        # Equipped status line
        p = self.player
        eq_weapon = p.weapon.name if p.weapon else 'none'
        eq_str = self.font_sm.render(
            f"Weapon: {eq_weapon}   AC: {p.get_ac()}", True, (160, 200, 160)
        )
        self.screen.blit(eq_str, (bx + 20, by + 44))

        pygame.draw.line(
            self.screen, (60, 60, 100),
            (bx + 10, by + 66), (bx + bw - 10, by + 66)
        )

        for i, item in enumerate(self.equip_menu_items):
            iy = by + 76 + i * 48
            row_bg = (28, 28, 58) if i % 2 == 0 else (22, 22, 48)
            pygame.draw.rect(self.screen, row_bg, (bx + 10, iy, bw - 20, 42), border_radius=6)

            num = self.font_md.render(f"[{i + 1}]", True, (160, 160, 80))
            self.screen.blit(num, (bx + 18, iy + 11))

            name_surf = self.font_md.render(item.name, True, (220, 220, 220))
            self.screen.blit(name_surf, (bx + 70, iy + 11))

            if isinstance(item, Weapon):
                detail = self.font_sm.render(
                    f"weapon  {item.damage}  chain x{item.max_chain_length or '?'}",
                    True, (160, 200, 160)
                )
            elif isinstance(item, (Armor, Shield)):
                quiz_req = f"geography x{item.equip_threshold}"
                ac_str   = f"+{item.ac_bonus} AC"
                slot_str = getattr(item, 'slot', 'shield')
                detail   = self.font_sm.render(
                    f"{slot_str}  {ac_str}  (quiz: {quiz_req})", True, (160, 180, 220)
                )
            else:
                detail = self.font_sm.render(item.item_class, True, (140, 140, 140))

            self.screen.blit(detail, (bx + 70, iy + 30))

        hint_y = by + bh - 34
        pygame.draw.line(
            self.screen, (60, 60, 100),
            (bx + 10, hint_y - 8), (bx + bw - 10, hint_y - 8)
        )
        hint = self.font_sm.render(
            "Press number to equip  |  ESC to cancel", True, (120, 120, 160)
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
        self.screen.blit(dead, ((WINDOW_W - dead.get_width()) // 2, WINDOW_H // 2 - 36))
        self.screen.blit(sub,  ((WINDOW_W - sub.get_width())  // 2, WINDOW_H // 2 + 14))


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
