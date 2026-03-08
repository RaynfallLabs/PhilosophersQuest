import pygame
from dungeon import WALL, FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR

TILE_SIZE = 32

# Visible tile colors
_VISIBLE = {
    WALL:        (130, 130, 140),
    FLOOR:       ( 60,  55,  50),
    STAIRS_UP:   (255, 240,  80),
    STAIRS_DOWN: (200, 185,  50),
    DOOR:        (139,  90,  43),
    SECRET_DOOR: (130, 130, 140),   # indistinguishable from WALL
}

# Explored-but-not-currently-visible (dimmed) colors
_EXPLORED = {
    WALL:        ( 60,  60,  65),
    FLOOR:       ( 25,  22,  20),
    STAIRS_UP:   ( 90,  85,  30),
    STAIRS_DOWN: ( 70,  65,  25),
    DOOR:        ( 55,  35,  18),
    SECRET_DOOR: ( 60,  60,  65),   # same as wall
}

_UNEXPLORED = (0, 0, 0)
_PLAYER     = (255, 255, 255)


class Renderer:
    def __init__(self, screen: pygame.Surface,
                 viewport_tiles_w: int, viewport_tiles_h: int):
        self.screen = screen
        self.vw     = viewport_tiles_w
        self.vh     = viewport_tiles_h
        self._sym_font = pygame.font.SysFont('consolas', TILE_SIZE - 8, bold=True)

    def _to_screen(self, wx: int, wy: int, cam_x: int, cam_y: int):
        return (wx - cam_x) * TILE_SIZE, (wy - cam_y) * TILE_SIZE

    def draw_dungeon(self, dungeon, visible: set, cam_x: int, cam_y: int):
        for ty in range(cam_y, cam_y + self.vh + 1):
            for tx in range(cam_x, cam_x + self.vw + 1):
                if not dungeon.in_bounds(tx, ty):
                    continue

                sx, sy = self._to_screen(tx, ty, cam_x, cam_y)
                rect   = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)
                tile   = dungeon.tiles[ty][tx]

                if (tx, ty) in visible:
                    dungeon.explored.add((tx, ty))
                    color = _VISIBLE.get(tile, _VISIBLE[FLOOR])
                elif (tx, ty) in dungeon.explored:
                    color = _EXPLORED.get(tile, _EXPLORED[FLOOR])
                else:
                    color = _UNEXPLORED

                pygame.draw.rect(self.screen, color, rect)

                # Draw door glyph when visible
                if (tx, ty) in visible and tile == DOOR:
                    glyph = self._sym_font.render('+', True, (210, 130, 60))
                    ox = (TILE_SIZE - glyph.get_width())  // 2
                    oy = (TILE_SIZE - glyph.get_height()) // 2
                    self.screen.blit(glyph, (sx + ox, sy + oy))

    def draw_player(self, player, cam_x: int, cam_y: int):
        sx, sy = self._to_screen(player.x, player.y, cam_x, cam_y)
        pad    = 4
        rect   = pygame.Rect(sx + pad, sy + pad,
                             TILE_SIZE - pad * 2, TILE_SIZE - pad * 2)
        pygame.draw.rect(self.screen, _PLAYER, rect)

    def draw_entity(self, x: int, y: int, color: tuple,
                    cam_x: int, cam_y: int, visible):
        """Draw a monster or dim dot.  Pass visible=None to always draw."""
        if visible is not None and (x, y) not in visible:
            return
        sx, sy = self._to_screen(x, y, cam_x, cam_y)
        pad    = 5
        rect   = pygame.Rect(sx + pad, sy + pad,
                             TILE_SIZE - pad * 2, TILE_SIZE - pad * 2)
        pygame.draw.rect(self.screen, color, rect)

    def draw_item(self, item, cam_x: int, cam_y: int, visible: set):
        """Draw an item glyph (only when visible)."""
        if (item.x, item.y) not in visible:
            return
        sx, sy = self._to_screen(item.x, item.y, cam_x, cam_y)

        # Containers: draw a filled rect in the item color, then the glyph
        from items import Container
        if isinstance(item, Container):
            pad = 3
            pygame.draw.rect(
                self.screen, (30, 20, 10),
                (sx + pad, sy + pad, TILE_SIZE - pad * 2, TILE_SIZE - pad * 2),
                border_radius=3
            )
            pygame.draw.rect(
                self.screen, item.color,
                (sx + pad, sy + pad, TILE_SIZE - pad * 2, TILE_SIZE - pad * 2),
                2, border_radius=3
            )

        surf = self._sym_font.render(item.symbol, True, item.color)
        ox   = (TILE_SIZE - surf.get_width())  // 2
        oy   = (TILE_SIZE - surf.get_height()) // 2
        self.screen.blit(surf, (sx + ox, sy + oy))
