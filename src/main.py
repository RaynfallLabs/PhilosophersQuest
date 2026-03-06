import sys
import pygame

from dungeon import generate_dungeon
from fov import calculate_fov
from player import Player
from renderer import Renderer, TILE_SIZE

WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
FPS = 60

VIEWPORT_W = WINDOW_WIDTH  // TILE_SIZE
VIEWPORT_H = WINDOW_HEIGHT // TILE_SIZE


def _camera(player, dungeon):
    cam_x = player.x - VIEWPORT_W // 2
    cam_y = player.y - VIEWPORT_H // 2
    cam_x = max(0, min(cam_x, dungeon.width  - VIEWPORT_W))
    cam_y = max(0, min(cam_y, dungeon.height - VIEWPORT_H))
    return cam_x, cam_y


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    dungeon = generate_dungeon(80, 50, level=1)
    player = Player()
    player.x, player.y = dungeon.rooms[0].center

    renderer = Renderer(screen, VIEWPORT_W, VIEWPORT_H)
    visible = calculate_fov(dungeon, player.x, player.y, player.get_sight_radius())

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                dx, dy = 0, 0
                if event.key == pygame.K_UP    or event.key == pygame.K_k: dy = -1
                if event.key == pygame.K_DOWN  or event.key == pygame.K_j: dy =  1
                if event.key == pygame.K_LEFT  or event.key == pygame.K_h: dx = -1
                if event.key == pygame.K_RIGHT or event.key == pygame.K_l: dx =  1

                if dx or dy:
                    nx, ny = player.x + dx, player.y + dy
                    if dungeon.is_walkable(nx, ny):
                        player.x, player.y = nx, ny
                        visible = calculate_fov(dungeon, player.x, player.y,
                                                player.get_sight_radius())

        cam_x, cam_y = _camera(player, dungeon)

        screen.fill((0, 0, 0))
        renderer.draw_dungeon(dungeon, visible, cam_x, cam_y)
        renderer.draw_player(player, cam_x, cam_y)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
