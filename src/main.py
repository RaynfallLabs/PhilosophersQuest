import sys
import pygame

from combat import player_attack
from dungeon import generate_dungeon, spawn_monsters
from fov import calculate_fov
from player import Player
from quiz_engine import QuizEngine, QuizState
from renderer import Renderer, TILE_SIZE

WINDOW_W  = 1280
WINDOW_H  = 720
FPS       = 60

VIEWPORT_W = WINDOW_W // TILE_SIZE   # 40 tiles
VIEWPORT_H = WINDOW_H // TILE_SIZE   # 22 tiles

MSG_MAX = 8

# Game states
STATE_PLAYER = 'player'
STATE_QUIZ   = 'quiz'
STATE_DEAD   = 'dead'


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_sm = pygame.font.SysFont('consolas', 15)
        self.font_md = pygame.font.SysFont('consolas', 20)
        self.font_lg = pygame.font.SysFont('consolas', 28, bold=True)

        self.quiz_engine   = QuizEngine()
        self.messages: list[str] = []
        self.state         = STATE_PLAYER
        self.combat_target = None

        self._new_level(1)

    # ------------------------------------------------------------------
    # Level setup
    # ------------------------------------------------------------------

    def _new_level(self, level: int):
        self.dungeon  = generate_dungeon(80, 50, level)
        self.player   = Player()
        self.player.x, self.player.y = self.dungeon.rooms[0].center
        self.monsters = spawn_monsters(self.dungeon.rooms, level, self.dungeon)
        self.corpses: list[dict] = []
        self.renderer = Renderer(self.screen, VIEWPORT_W, VIEWPORT_H)
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
        """Process one event. Returns False to signal quit."""
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True
        if event.key == pygame.K_ESCAPE:
            return False

        if self.state == STATE_PLAYER:
            self._player_input(event.key)
        elif self.state == STATE_QUIZ:
            self._quiz_input(event.key)
        return True

    _MOVE_KEYS = {
        pygame.K_UP: (0, -1), pygame.K_k: (0, -1),
        pygame.K_DOWN: (0, 1), pygame.K_j: (0, 1),
        pygame.K_LEFT: (-1, 0), pygame.K_h: (-1, 0),
        pygame.K_RIGHT: (1, 0), pygame.K_l: (1, 0),
    }

    def _player_input(self, key: int):
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

    def _start_combat(self, monster):
        self.state = STATE_QUIZ
        self.combat_target = monster

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
                    self.corpses.append(
                        {'x': monster.x, 'y': monster.y, 'name': monster.name}
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

        for c in self.corpses:
            self.renderer.draw_entity(
                c['x'], c['y'], (100, 30, 30), cam_x, cam_y, self.visible
            )

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
        elif self.state == STATE_DEAD:
            self._draw_death_screen()

        pygame.display.flip()

    def _camera(self) -> tuple[int, int]:
        cam_x = self.player.x - VIEWPORT_W // 2
        cam_y = self.player.y - VIEWPORT_H // 2
        cam_x = max(0, min(cam_x, self.dungeon.width  - VIEWPORT_W))
        cam_y = max(0, min(cam_y, self.dungeon.height - VIEWPORT_H))
        return cam_x, cam_y

    def _draw_hud(self):
        p = self.player
        paralyzed = p.status_effects.get('paralyzed', 0)
        status = f"  [PARALYZED: {paralyzed}]" if paralyzed else ""
        text = (
            f"HP {p.hp}/{p.max_hp}   SP {p.sp}/{p.max_sp}   MP {p.mp}/{p.max_mp}"
            f"   WIS {p.WIS}{status}"
        )
        surf = self.font_sm.render(text, True, (220, 210, 100))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, surf.get_width() + 20, 22))
        self.screen.blit(surf, (8, 4))

    def _draw_messages(self):
        msgs = self.messages[-6:]
        line_h = 19
        box_h  = len(msgs) * line_h + 8
        box_y  = WINDOW_H - box_h
        pygame.draw.rect(self.screen, (0, 0, 0), (0, box_y, 760, box_h))
        for i, msg in enumerate(msgs):
            age = len(msgs) - 1 - i
            bright = max(110, 220 - age * 28)
            surf = self.font_sm.render(msg, True, (bright, bright, bright))
            self.screen.blit(surf, (8, box_y + 4 + i * line_h))

    def _draw_quiz(self):
        qe = self.quiz_engine
        if not qe.current_question:
            return

        # Dim background
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 740, 410
        bx = (WINDOW_W - bw) // 2
        by = (WINDOW_H - bh) // 2

        pygame.draw.rect(self.screen, (16, 16, 38), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 140), (bx, by, bw, bh), 2, border_radius=12)

        # Header
        target_name = self.combat_target.name.upper() if self.combat_target else 'ENEMY'
        hdr = self.font_md.render(
            f"COMBAT vs {target_name}  —  MATH CHAIN", True, (255, 200, 60)
        )
        self.screen.blit(hdr, (bx + 18, by + 14))

        chain_surf = self.font_md.render(f"Chain: {qe.chain}", True, (80, 255, 120))
        self.screen.blit(chain_surf, (bx + bw - chain_surf.get_width() - 18, by + 14))

        # Timer bar
        bar_x, bar_y, bar_w, bar_h = bx + 18, by + 50, bw - 36, 10
        ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))
        pygame.draw.rect(self.screen, (40, 15, 15), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        bar_color = (
            (50, 200, 50)   if ratio > 0.50 else
            (210, 160, 40)  if ratio > 0.25 else
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
            c_lower = choice.strip().lower()
            is_correct  = c_lower == correct_str
            is_selected = bool(selected) and c_lower == selected

            if qe.state == QuizState.RESULT:
                if is_correct:
                    bg, border = (18, 72, 18), (50, 210, 50)
                elif is_selected:
                    bg, border = (72, 18, 18), (210, 50, 50)
                else:
                    bg, border = (22, 22, 52), (55, 55, 100)
            else:
                bg, border = (24, 24, 56), (65, 65, 120)

            pygame.draw.rect(self.screen, bg,     (cx, cy, cw, ch), border_radius=8)
            pygame.draw.rect(self.screen, border, (cx, cy, cw, ch), 2, border_radius=8)

            lbl = self.font_md.render(f"[{labels[i]}]", True, (160, 160, 80))
            self.screen.blit(lbl, (cx + 12, cy + (ch - lbl.get_height()) // 2))

            c_surf = self.font_md.render(str(choice), True, (220, 220, 220))
            self.screen.blit(c_surf, (cx + 68, cy + (ch - c_surf.get_height()) // 2))

        # Correct / wrong feedback
        if qe.state == QuizState.RESULT:
            if qe.last_correct:
                fb = self.font_lg.render("CORRECT!", True, (80, 255, 80))
            else:
                fb = self.font_lg.render("WRONG!", True, (255, 80, 80))
            self.screen.blit(fb, (bx + (bw - fb.get_width()) // 2, by + bh - 52))

        # Key hint (only while asking)
        if qe.state == QuizState.ASKING:
            hint = self.font_sm.render("Press 1-4 to answer", True, (120, 120, 160))
            self.screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 28))

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

    game = Game(screen)
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
