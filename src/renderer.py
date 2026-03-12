import os
import pygame
from dungeon import WALL, FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR

TILE_SIZE = 40  # kept for UI/font sizing outside the renderer

_SPRITE_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tiles', 'monsters')

# Visible tile colors
_VISIBLE = {
    WALL:        (130, 130, 140),
    FLOOR:       ( 60,  55,  50),
    STAIRS_UP:   (255, 240,  80),
    STAIRS_DOWN: (200, 185,  50),
    DOOR:        (139,  90,  43),
    SECRET_DOOR: (130, 130, 140),
}

# Explored-but-not-currently-visible (dimmed) colors
_EXPLORED = {
    WALL:        ( 60,  60,  65),
    FLOOR:       ( 25,  22,  20),
    STAIRS_UP:   ( 90,  85,  30),
    STAIRS_DOWN: ( 70,  65,  25),
    DOOR:        ( 55,  35,  18),
    SECRET_DOOR: ( 60,  60,  65),
}

_UNEXPLORED = (0, 0, 0)
_PLAYER     = (255, 255, 255)


class Renderer:
    def __init__(self, screen: pygame.Surface,
                 viewport_tiles_w: int, viewport_tiles_h: int):
        self.screen = screen
        self.vw     = viewport_tiles_w
        self.vh     = viewport_tiles_h

        self.map_tile_size = TILE_SIZE
        self.map_offset_x  = 0
        self.map_offset_y  = 0

        self._sym_font = pygame.font.SysFont('consolas', max(8, TILE_SIZE - 8), bold=True)
        self._sprite_cache: dict[str, pygame.Surface | None] = {}

    def set_dungeon(self, dungeon_w: int, dungeon_h: int, game_w: int, game_h: int):
        """Compute tile size and centering offsets to fit the entire dungeon in the game panel."""
        ts = min(game_w // dungeon_w, game_h // dungeon_h)
        self.map_tile_size = max(4, ts)
        self.map_offset_x  = (game_w  - dungeon_w * self.map_tile_size) // 2
        self.map_offset_y  = (game_h  - dungeon_h * self.map_tile_size) // 2
        self.vw = dungeon_w
        self.vh = dungeon_h
        font_size = max(8, self.map_tile_size - 2)
        self._sym_font = pygame.font.SysFont('consolas', font_size, bold=True)
        self._sprite_cache.clear()   # sprites must be rescaled for new tile size

    def world_to_screen(self, wx: int, wy: int) -> tuple[int, int]:
        """Convert world tile coords to screen pixel coords."""
        return (wx * self.map_tile_size + self.map_offset_x,
                wy * self.map_tile_size + self.map_offset_y)

    def _get_sprite(self, mid: str) -> 'pygame.Surface | None':
        if mid in self._sprite_cache:
            return self._sprite_cache[mid]
        path = os.path.join(_SPRITE_DIR, f"{mid}.png")
        if os.path.exists(path):
            raw  = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.scale(raw, (self.map_tile_size, self.map_tile_size))
            self._sprite_cache[mid] = surf
        else:
            self._sprite_cache[mid] = None
        return self._sprite_cache[mid]

    # cam_x / cam_y kept for signature compat but ignored (always 0,0)
    def draw_dungeon(self, dungeon, visible: set, cam_x: int = 0, cam_y: int = 0):
        T = self.map_tile_size
        for ty in range(dungeon.height):
            for tx in range(dungeon.width):
                sx, sy = self.world_to_screen(tx, ty)
                tile   = dungeon.tiles[ty][tx]

                if (tx, ty) in visible:
                    dungeon.explored.add((tx, ty))
                    color = _VISIBLE.get(tile, _VISIBLE[FLOOR])
                elif (tx, ty) in dungeon.explored:
                    color = _EXPLORED.get(tile, _EXPLORED[FLOOR])
                else:
                    color = _UNEXPLORED

                pygame.draw.rect(self.screen, color, (sx, sy, T, T))

                if (tx, ty) in visible and tile == DOOR:
                    glyph = self._sym_font.render('+', True, (210, 130, 60))
                    ox = (T - glyph.get_width())  // 2
                    oy = (T - glyph.get_height()) // 2
                    self.screen.blit(glyph, (sx + ox, sy + oy))

    def draw_player(self, player, cam_x: int = 0, cam_y: int = 0):
        T   = self.map_tile_size
        sx, sy = self.world_to_screen(player.x, player.y)
        pad = max(1, T // 8)
        pygame.draw.rect(self.screen, _PLAYER,
                         (sx + pad, sy + pad, T - pad * 2, T - pad * 2))

    def draw_entity(self, x: int, y: int, color: tuple,
                    cam_x: int = 0, cam_y: int = 0, visible=None, mid: str = ''):
        """Draw a monster or dim dot.  Pass visible=None to always draw."""
        if visible is not None and (x, y) not in visible:
            return
        T = self.map_tile_size
        sx, sy = self.world_to_screen(x, y)
        if mid:
            sprite = self._get_sprite(mid)
            if sprite:
                self.screen.blit(sprite, (sx, sy))
                return
        pad  = max(1, T // 7)
        pygame.draw.rect(self.screen, color,
                         (sx + pad, sy + pad, T - pad * 2, T - pad * 2))

    def draw_item(self, item, cam_x: int = 0, cam_y: int = 0, visible: set = None):
        """Draw an item glyph (only when visible)."""
        if visible is not None and (item.x, item.y) not in visible:
            return
        T = self.map_tile_size
        sx, sy = self.world_to_screen(item.x, item.y)

        from items import Container
        if isinstance(item, Container):
            pad = max(1, T // 10)
            pygame.draw.rect(self.screen, (30, 20, 10),
                             (sx + pad, sy + pad, T - pad * 2, T - pad * 2),
                             border_radius=2)
            pygame.draw.rect(self.screen, item.color,
                             (sx + pad, sy + pad, T - pad * 2, T - pad * 2),
                             1, border_radius=2)

        surf = self._sym_font.render(item.symbol, True, item.color)
        ox   = (T - surf.get_width())  // 2
        oy   = (T - surf.get_height()) // 2
        self.screen.blit(surf, (sx + ox, sy + oy))
