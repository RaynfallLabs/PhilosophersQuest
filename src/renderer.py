import os
import math
import pygame
from dungeon import WALL, FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR, ALTAR, WATER, LAVA, FOUNTAIN, GRAVE, THRONE, ICE
from paths import data_path

TILE_SIZE = 40  # kept for UI/font sizing outside the renderer

_SPRITE_DIR       = data_path('assets', 'tiles', 'monsters')
_ITEM_SPRITE_DIR  = data_path('assets', 'tiles', 'items')
_ENV_SPRITE_DIR   = data_path('assets', 'tiles', 'env')

# Map tile constants to sprite filenames (SECRET_DOOR looks like WALL)
_TILE_SPRITE = {
    WALL:        'wall',
    FLOOR:       'floor',
    STAIRS_UP:   'stairs_up',
    STAIRS_DOWN: 'stairs_down',
    DOOR:        'door',
    SECRET_DOOR: 'wall',
    ALTAR:       'altar',
    WATER:       'water',
    LAVA:        'lava',
    FOUNTAIN:    'fountain',
    GRAVE:       'grave',
    THRONE:      'throne',
    ICE:         'ice',
}

# Visible tile colors
_VISIBLE = {
    WALL:        (130, 130, 140),
    FLOOR:       ( 60,  55,  50),
    STAIRS_UP:   (255, 240,  80),
    STAIRS_DOWN: (200, 185,  50),
    DOOR:        (139,  90,  43),
    SECRET_DOOR: (130, 130, 140),
    ALTAR:       (200, 170,  80),
    WATER:       ( 30,  60, 180),   # deep blue
    LAVA:        (220,  80,  20),   # hot orange-red
    FOUNTAIN:    ( 80, 140, 220),   # bright blue
    GRAVE:       (120, 110, 100),   # grey stone
    THRONE:      (200, 170,  40),   # gold
    ICE:         (160, 200, 230),   # light blue
}

# Explored-but-not-currently-visible (dimmed) colors
_EXPLORED = {
    WALL:        ( 60,  60,  65),
    FLOOR:       ( 25,  22,  20),
    STAIRS_UP:   ( 90,  85,  30),
    STAIRS_DOWN: ( 70,  65,  25),
    DOOR:        ( 55,  35,  18),
    SECRET_DOOR: ( 60,  60,  65),
    ALTAR:       ( 80,  65,  30),
    WATER:       ( 12,  25,  70),
    LAVA:        ( 85,  30,   8),
    FOUNTAIN:    ( 30,  55,  85),
    GRAVE:       ( 45,  42,  38),
    THRONE:      ( 75,  65,  15),
    ICE:         ( 60,  75,  88),
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
        self._item_sprite_cache: dict[str, pygame.Surface | None] = {}
        self._env_sprite_cache: dict[str, pygame.Surface | None] = {}
        self._player_sprite: pygame.Surface | None = None

    def set_dungeon(self, dungeon_w: int, dungeon_h: int, game_w: int, game_h: int):
        """Compute tile size and centering offsets to fit the entire dungeon in the game panel."""
        ts = min(game_w // dungeon_w, game_h // dungeon_h)
        self._apply_tile_size(max(4, ts), dungeon_w, dungeon_h, game_w, game_h)

    def set_close_up(self, player_x: int, player_y: int,
                     dungeon_w: int, dungeon_h: int,
                     game_w: int, game_h: int, tile_size: int = TILE_SIZE):
        """Set up a close-up view centered on the player with a fixed tile size."""
        self._apply_tile_size(tile_size, dungeon_w, dungeon_h, game_w, game_h,
                              center_x=player_x, center_y=player_y)

    def _apply_tile_size(self, ts: int, dungeon_w: int, dungeon_h: int,
                         game_w: int, game_h: int,
                         center_x: int | None = None, center_y: int | None = None):
        """Internal: set tile size and offsets. If center coords given, scroll to them."""
        old_ts = self.map_tile_size
        self.map_tile_size = ts
        self.vw = dungeon_w
        self.vh = dungeon_h

        if center_x is not None and center_y is not None:
            # Camera centered on player; offset so player is at center of game area
            self.map_offset_x = game_w  // 2 - center_x * ts - ts // 2
            self.map_offset_y = game_h // 2 - center_y * ts - ts // 2
        else:
            # Fit-all: center the whole map
            self.map_offset_x = (game_w  - dungeon_w * ts) // 2
            self.map_offset_y = (game_h  - dungeon_h * ts) // 2

        if ts != old_ts:
            font_size = max(8, ts - 2)
            self._sym_font = pygame.font.SysFont('consolas', font_size, bold=True)
            self._sprite_cache.clear()
            self._item_sprite_cache.clear()
            self._env_sprite_cache.clear()
            self._player_sprite = None

    def world_to_screen(self, wx: int, wy: int) -> tuple[int, int]:
        """Convert world tile coords to screen pixel coords."""
        return (wx * self.map_tile_size + self.map_offset_x,
                wy * self.map_tile_size + self.map_offset_y)

    def _get_env_sprite(self, name: str) -> 'pygame.Surface | None':
        if name in self._env_sprite_cache:
            return self._env_sprite_cache[name]
        path = os.path.join(_ENV_SPRITE_DIR, f"{name}.png")
        if os.path.exists(path):
            raw  = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.scale(raw, (self.map_tile_size, self.map_tile_size))
            self._env_sprite_cache[name] = surf
        else:
            self._env_sprite_cache[name] = None
        return self._env_sprite_cache[name]

    def _get_item_sprite(self, item_id: str) -> 'pygame.Surface | None':
        if item_id in self._item_sprite_cache:
            return self._item_sprite_cache[item_id]
        path = os.path.join(_ITEM_SPRITE_DIR, f"{item_id}.png")
        if not os.path.exists(path) and item_id.startswith('corpse_'):
            path = os.path.join(_ITEM_SPRITE_DIR, "corpse.png")
        if os.path.exists(path):
            raw  = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.scale(raw, (self.map_tile_size, self.map_tile_size))
            self._item_sprite_cache[item_id] = surf
        else:
            self._item_sprite_cache[item_id] = None
        return self._item_sprite_cache[item_id]

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

    # Pre-built overlay surfaces for explored-tile dimming, keyed by tile size
    _dim_overlay_cache: dict[int, pygame.Surface] = {}

    def _get_dim_overlay(self, T: int) -> pygame.Surface:
        if T not in self._dim_overlay_cache:
            ov = pygame.Surface((T, T), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 155))   # ~60% dark overlay
            self._dim_overlay_cache[T] = ov
        return self._dim_overlay_cache[T]

    # cam_x / cam_y kept for signature compat but ignored (always 0,0)
    def draw_dungeon(self, dungeon, visible: set, cam_x: int = 0, cam_y: int = 0):
        T   = self.map_tile_size
        dim = self._get_dim_overlay(T)
        for ty in range(dungeon.height):
            for tx in range(dungeon.width):
                sx, sy = self.world_to_screen(tx, ty)
                tile   = dungeon.tiles[ty][tx]

                if (tx, ty) in visible:
                    dungeon.explored.add((tx, ty))
                    sprite_name = _TILE_SPRITE.get(tile)
                    sprite = self._get_env_sprite(sprite_name) if sprite_name else None
                    if sprite:
                        self.screen.blit(sprite, (sx, sy))
                    else:
                        color = _VISIBLE.get(tile, _VISIBLE[FLOOR])
                        pygame.draw.rect(self.screen, color, (sx, sy, T, T))
                        # Lava glow: pulse red channel with a sine wave
                        if tile == LAVA:
                            ticks = pygame.time.get_ticks()
                            pulse = int(20 * math.sin(ticks / 400.0))
                            glow_r = max(0, min(255, color[0] + pulse))
                            glow_surf = pygame.Surface((T, T), pygame.SRCALPHA)
                            glow_surf.fill((glow_r, color[1], color[2], 80))
                            self.screen.blit(glow_surf, (sx, sy))
                        # Water shimmer: vary blue channel per tile position and time
                        elif tile == WATER:
                            ticks = pygame.time.get_ticks()
                            phase = (tx + ty + ticks // 500) % 3
                            shimmer_b = color[2] + (0, 20, 40)[phase]
                            shimmer_b = max(0, min(255, shimmer_b))
                            shimmer_surf = pygame.Surface((T, T), pygame.SRCALPHA)
                            shimmer_surf.fill((color[0], color[1], shimmer_b, 60))
                            self.screen.blit(shimmer_surf, (sx, sy))

                elif (tx, ty) in dungeon.explored:
                    sprite_name = _TILE_SPRITE.get(tile)
                    sprite = self._get_env_sprite(sprite_name) if sprite_name else None
                    if sprite:
                        self.screen.blit(sprite, (sx, sy))
                        self.screen.blit(dim, (sx, sy))
                    else:
                        color = _EXPLORED.get(tile, _EXPLORED[FLOOR])
                        pygame.draw.rect(self.screen, color, (sx, sy, T, T))

                else:
                    pygame.draw.rect(self.screen, _UNEXPLORED, (sx, sy, T, T))

        # Draw revealed traps (shown as '^' symbol in warning color when visible)
        for (tx, ty), trap in getattr(dungeon, 'traps', {}).items():
            if trap.get('revealed') and (tx, ty) in visible:
                sx, sy = self.world_to_screen(tx, ty)
                trap_color = trap.get('color', (255, 200, 0))
                # Draw a small caret symbol for the trap
                label = self._sym_font.render('^', True, trap_color)
                lw, lh = label.get_size()
                self.screen.blit(label, (sx + (T - lw) // 2, sy + (T - lh) // 2))

        # Draw dug pits (dark brown hollow square)
        _PIT_COLOR = (80, 50, 20)
        for (px, py) in getattr(dungeon, 'pits', set()):
            if (px, py) in visible:
                sx, sy = self.world_to_screen(px, py)
                pad = max(2, T // 6)
                pygame.draw.rect(self.screen, _PIT_COLOR,
                                 (sx + pad, sy + pad, T - pad * 2, T - pad * 2), 2)

    def draw_player(self, player, cam_x: int = 0, cam_y: int = 0,
                    sprite_name: str = 'player'):
        T      = self.map_tile_size
        sx, sy = self.world_to_screen(player.x, player.y)
        sprite = self._get_env_sprite(sprite_name) or self._get_env_sprite('player')
        if sprite:
            self.screen.blit(sprite, (sx, sy))
        else:
            pad = max(1, T // 8)
            pygame.draw.rect(self.screen, _PLAYER,
                             (sx + pad, sy + pad, T - pad * 2, T - pad * 2))

    def draw_entity(self, x: int, y: int, color: tuple,
                    cam_x: int = 0, cam_y: int = 0, visible=None, mid: str = '',
                    tint: tuple = None):
        """Draw a monster or dim dot.  Pass visible=None to always draw.
        tint: optional (R,G,B,A) overlay applied via BLEND_RGBA_MULT."""
        if visible is not None and (x, y) not in visible:
            return
        T = self.map_tile_size
        sx, sy = self.world_to_screen(x, y)
        if mid:
            sprite = self._get_sprite(mid)
            if sprite:
                if tint:
                    sprite = sprite.copy()
                    overlay = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
                    overlay.fill(tint)
                    sprite.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(sprite, (sx, sy))
                return
        pad  = max(1, T // 7)
        pygame.draw.rect(self.screen, color,
                         (sx + pad, sy + pad, T - pad * 2, T - pad * 2))

    def draw_item(self, item, cam_x: int = 0, cam_y: int = 0, visible: set = None):
        """Draw an item sprite (or glyph fallback) only when visible."""
        if visible is not None and (item.x, item.y) not in visible:
            return
        T = self.map_tile_size
        sx, sy = self.world_to_screen(item.x, item.y)

        item_id = getattr(item, 'id', None)
        if item_id:
            sprite = self._get_item_sprite(item_id)
            if sprite:
                self.screen.blit(sprite, (sx, sy))
                return

        # Fallback: glyph rendering (containers get a box outline first)
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
