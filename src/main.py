import sys
import pygame

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

DARK_BLUE = (10, 15, 50)
WHITE = (255, 255, 255)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Philosopher's Quest")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 48)
    text_surface = font.render("Welcome to Philosopher's Quest", True, WHITE)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(DARK_BLUE)
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
