"""
fantasy_ui.py — High-fantasy medieval / arcane grimoire UI theme.
# FANTASY: Central theme module. All visual helpers live here so main.py
#          and ui.py stay logic-focused. Import what you need:
#
#   from fantasy_ui import (FP, get_font, draw_panel, draw_divider,
#                            draw_shadow_text, draw_glow_text,
#                            make_parchment, draw_header_bar,
#                            draw_overlay, draw_corner_flourish)
"""

import math
import os
import random

import pygame

# ─────────────────────────────────────────────────────────────────────────────
# FANTASY PALETTE  (FP namespace — "Fantasy Palette")
# ─────────────────────────────────────────────────────────────────────────────
class FP:
    """# FANTASY: Antique gold / aged parchment / midnight blue / burgundy palette."""

    # Parchment family
    PARCHMENT       = (218, 192, 145)   # base aged parchment
    PARCHMENT_DARK  = (175, 148, 100)   # darker / shadow areas
    PARCHMENT_LIGHT = (242, 222, 182)   # lighter vellum highlight
    VELLUM          = (250, 235, 200)   # near-white vellum

    # Gold family
    GOLD            = (205, 162,  45)   # antique gold
    GOLD_BRIGHT     = (255, 215,  60)   # bright highlight gold
    GOLD_DARK       = (130,  95,  18)   # shadow gold
    GOLD_PALE       = (240, 210, 130)   # muted pale gold

    # Ink / text
    INK             = ( 28,  18,  10)   # near-black brown ink
    INK_FADED       = ( 80,  58,  35)   # faded brown ink
    INK_LIGHT       = (115,  88,  55)   # light ink / disabled text

    # Burgundy / crimson
    BURGUNDY        = (128,  20,  30)   # deep burgundy
    BURGUNDY_MID    = (168,  48,  58)   # mid burgundy
    BURGUNDY_DARK   = ( 65,   8,  14)   # very dark burgundy
    BLOOD           = (200,  18,  18)   # bright blood red

    # Midnight blue
    MIDNIGHT        = ( 14,  18,  48)   # deep midnight blue
    MIDNIGHT_MID    = ( 28,  36,  82)   # mid midnight
    MIDNIGHT_LIGHT  = ( 50,  65, 125)   # lighter midnight

    # Arcane purple
    ARCANE          = ( 82,  35, 118)   # arcane purple
    ARCANE_BRIGHT   = (175,  88, 255)   # bright arcane glow
    ARCANE_DIM      = ( 48,  20,  72)   # dim arcane

    # Utility
    SHADOW          = (  0,   0,   0)
    WHITE           = (255, 255, 255)

    # ── Semantic aliases (use these in draw code) ──────────────────────────
    PANEL_BG        = MIDNIGHT          # modal/panel background
    PANEL_BG_MID    = MIDNIGHT_MID      # slightly lighter panel
    PANEL_BORDER    = GOLD              # main border colour
    PANEL_INNER     = GOLD_DARK         # inner double-border colour
    HEADER_BG       = MIDNIGHT          # header strip fill
    HEADER_TEXT     = GOLD_BRIGHT       # header text
    BODY_TEXT       = PARCHMENT         # normal body text
    FADED_TEXT      = INK_LIGHT         # disabled / hint text
    ACCENT_TEXT     = GOLD_PALE         # accented label text
    HINT_TEXT       = (120, 115, 165)   # keyboard hint text
    DANGER_TEXT     = BLOOD
    SUCCESS_TEXT    = (110, 220, 100)
    WARNING_TEXT    = (220, 185,  45)
    LOOT_TEXT       = GOLD_BRIGHT

    # Subject accent mapping (mirrors _SUBJECT_COLOR in main.py but richer)
    SUBJECT = {
        'math':       ( 40, 210, 245),
        'geography':  ( 40, 190,  75),
        'history':    (215, 170,   0),
        'animal':     (210, 105,  20),
        'cooking':    (215,  35, 170),
        'science':    ( 75,  90, 245),
        'philosophy': (195, 190, 215),
        'grammar':    (210,  45,  45),
        'economics':  (150, 210,   0),
        'theology':   (195, 162,  70),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FONT LOADING
# ─────────────────────────────────────────────────────────────────────────────
_FONT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')

# # FANTASY: TTF filenames expected in assets/fonts/
# Download links listed in ASSETS.md
_ROLE_FILES = {
    'title':   'Cinzel-Bold.ttf',
    'heading': 'Cinzel-Regular.ttf',
    'body':    'IMFellEnglish-Regular.ttf',
    'small':   'IMFellEnglish-Regular.ttf',
    'gothic':  'UnifrakturMaguntia.ttf',
    'italic':  'IMFellEnglish-Italic.ttf',
}

_FALLBACK_FAMILIES = 'garamond,palatino linotype,palatino,georgia,book antiqua,times new roman,consolas'
_font_cache: dict = {}


def get_font(role: str, size: int, bold: bool = False) -> pygame.font.Font:
    """
    # FANTASY: Return a themed font.
    role: 'title'   → Cinzel Bold (large display, all-caps)
          'heading' → Cinzel Regular (section headers)
          'body'    → Consolas (crisp readable body text)
          'small'   → Consolas small
          'italic'  → IM Fell English Italic
          'gothic'  → UnifrakturMaguntia (dramatic blackletter)
          'mono'    → Consolas (monospace — code/numbers)
    Falls back gracefully if TTF not installed.
    """
    key = (role, size, bold)
    if key in _font_cache:
        return _font_cache[key]

    if role in ('mono', 'body', 'small'):
        # Use Consolas for all body/small roles — crisp and highly readable
        font = pygame.font.SysFont('consolas,courier new,monospace', size, bold=bold)
    else:
        fname = _ROLE_FILES.get(role, 'Cinzel-Regular.ttf')
        path  = os.path.join(_FONT_DIR, fname)
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
            except Exception:
                font = pygame.font.SysFont(_FALLBACK_FAMILIES, size, bold=bold)
        else:
            font = pygame.font.SysFont(_FALLBACK_FAMILIES, size, bold=bold)

    _font_cache[key] = font
    return font


# ─────────────────────────────────────────────────────────────────────────────
# PARCHMENT TEXTURE
# ─────────────────────────────────────────────────────────────────────────────
_parchment_cache: dict = {}


def make_parchment(w: int, h: int, dark: bool = False, alpha: int = 255) -> pygame.Surface:
    """
    # FANTASY: Return a procedurally generated aged-parchment Surface.
    Uses a fixed seed so the texture is deterministic (no visual jitter).
    Pass dark=True for shadow/backdrop panels.
    """
    key = (w, h, dark, alpha)
    if key in _parchment_cache:
        return _parchment_cache[key]

    base = FP.PARCHMENT_DARK if dark else FP.PARCHMENT
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((*base, alpha))

    rng = random.Random(0xF4F457)   # fixed seed

    # Horizontal paper fibres
    for _ in range(h * 3):
        fy  = rng.randint(0, h - 1)
        fx1 = rng.randint(0, max(1, w - 80))
        fx2 = fx1 + rng.randint(15, min(80, w // 2))
        shade = rng.randint(-15, 15)
        c = tuple(max(0, min(255, v + shade)) for v in base)
        a = rng.randint(25, 65)
        pygame.draw.line(surf, (*c, a), (fx1, fy), (min(w - 1, fx2), fy))

    # Aged foxing spots
    for _ in range(max(1, w * h // 700)):
        sx = rng.randint(0, w - 1)
        sy = rng.randint(0, h - 1)
        sr = rng.randint(1, 5)
        shade = rng.randint(20, 55)
        c = tuple(max(0, v - shade) for v in base)
        pygame.draw.circle(surf, (*c, rng.randint(50, 120)), (sx, sy), sr)

    # Corner/edge vignette — slightly darker edges
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = 18
    for step in range(steps):
        a      = int(80 * (step / steps) ** 1.8)
        m      = int(step * max(w, h) / 38)
        pygame.draw.rect(vig, (*FP.PARCHMENT_DARK, a),
                         (m, m, max(1, w - 2*m), max(1, h - 2*m)), 3)
    surf.blit(vig, (0, 0))

    _parchment_cache[key] = surf
    return surf


def _try_parchment_png(w: int, h: int, alpha: int = 235) -> pygame.Surface | None:
    """Try to load assets/textures/parchment.png and scale it."""
    path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'textures', 'parchment.png')
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (w, h))
        img.set_alpha(alpha)
        return img
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# OVERLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def draw_overlay(surf: pygame.Surface, alpha: int = 185,
                 color: tuple = (0, 0, 0)):
    """# FANTASY: Dark semi-transparent overlay (full screen)."""
    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    ov.fill((*color, alpha))
    surf.blit(ov, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# ORNATE BORDER & PANEL
# ─────────────────────────────────────────────────────────────────────────────

def draw_panel(surf: pygame.Surface, rect: tuple,
               border_color: tuple | None = None,
               bg: bool = True, dark: bool = False,
               alpha: int = 238) -> None:
    """
    # FANTASY: Draw a parchment-backed panel with double border and corner flourishes.
    rect = (x, y, w, h)
    """
    if border_color is None:
        border_color = FP.GOLD
    x, y, w, h = rect

    # Parchment background
    if bg:
        parch = _try_parchment_png(w, h, alpha) or make_parchment(w, h, dark=dark, alpha=alpha)
        surf.blit(parch, (x, y))
    else:
        pygame.draw.rect(surf, (*FP.MIDNIGHT, alpha), (x, y, w, h))

    # Outer border
    pygame.draw.rect(surf, border_color, (x, y, w, h), 2)
    # Inner double border
    pygame.draw.rect(surf, FP.GOLD_DARK, (x+5, y+5, w-10, h-10), 1)

    # Corner flourishes
    _corner_flourish(surf, x,       y,       border_color, False, False)
    _corner_flourish(surf, x+w - 1, y,       border_color, True,  False)
    _corner_flourish(surf, x,       y+h - 1, border_color, False, True)
    _corner_flourish(surf, x+w - 1, y+h - 1, border_color, True,  True)

    # Mid-edge diamond ornaments
    for pos, vert in [
        ((x + w//2,   y),       False),
        ((x + w//2,   y+h - 1), False),
        ((x,          y + h//2), True),
        ((x+w - 1,    y + h//2), True),
    ]:
        _edge_diamond(surf, pos[0], pos[1], border_color, vert)


def draw_dark_panel(surf: pygame.Surface, rect: tuple,
                    border_color: tuple | None = None,
                    alpha: int = 230) -> None:
    """
    # FANTASY: Dark arcane panel (midnight blue bg + gold border).
    Used for quiz, menus etc. over the game world.
    """
    if border_color is None:
        border_color = FP.GOLD
    x, y, w, h = rect

    # Dark bg
    bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_surf.fill((*FP.MIDNIGHT, alpha))
    # Subtle horizontal texture lines
    for row in range(0, h, 5):
        shade = 4 if (row // 5) % 2 == 0 else 0
        c = tuple(min(255, v + shade) for v in FP.MIDNIGHT)
        pygame.draw.line(bg_surf, (*c, alpha - 10), (3, row + 2), (w - 3, row + 2))
    surf.blit(bg_surf, (x, y))

    # Double border
    pygame.draw.rect(surf, border_color, (x, y, w, h), 2, border_radius=4)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x+5, y+5, w-10, h-10), 1, border_radius=2)

    # Corner flourishes
    _corner_flourish(surf, x,       y,       border_color, False, False)
    _corner_flourish(surf, x+w - 1, y,       border_color, True,  False)
    _corner_flourish(surf, x,       y+h - 1, border_color, False, True)
    _corner_flourish(surf, x+w - 1, y+h - 1, border_color, True,  True)

    # Mid ornaments
    for pos, vert in [
        ((x + w//2,   y),        False),
        ((x + w//2,   y+h - 1),  False),
        ((x,          y + h//2),  True),
        ((x+w - 1,    y + h//2),  True),
    ]:
        _edge_diamond(surf, pos[0], pos[1], border_color, vert)


def _corner_flourish(surf: pygame.Surface, x: int, y: int, color: tuple,
                     flip_x: bool, flip_y: bool, arm: int = 20) -> None:
    """# FANTASY: Small L-shaped corner ornament with diamond cap."""
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1

    # Outer arms
    pygame.draw.line(surf, color, (x, y), (x + sx * arm, y), 2)
    pygame.draw.line(surf, color, (x, y), (x, y + sy * arm), 2)
    # Inner angled accent line
    pygame.draw.line(surf, FP.GOLD_DARK,
                     (x + sx * 7, y + sy * 2),
                     (x + sx * 2, y + sy * 7), 1)
    # Diamond cap
    d = 5
    pts = [(x, y - sy*d), (x + sx*d, y), (x, y + sy*d), (x - sx*d, y)]
    pygame.draw.polygon(surf, color, pts)


def _edge_diamond(surf: pygame.Surface, x: int, y: int,
                  color: tuple, vertical: bool, size: int = 6) -> None:
    """# FANTASY: Small diamond ornament at mid-edge."""
    d = size
    if vertical:
        pts = [(x-d, y), (x, y-d), (x+d, y), (x, y+d)]
    else:
        pts = [(x, y-d), (x+d, y), (x, y+d), (x-d, y)]
    pygame.draw.polygon(surf, color, pts)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER STRIP
# ─────────────────────────────────────────────────────────────────────────────

def draw_header_bar(surf: pygame.Surface, rect: tuple,
                    text: str = '', font: pygame.font.Font | None = None,
                    text_color: tuple | None = None,
                    accent: tuple | None = None) -> None:
    """
    # FANTASY: Decorative header strip inside a panel.
    rect = (x, y, w, h)  — usually HEADER_H = 44 tall.
    """
    if text_color is None:
        text_color = FP.GOLD_BRIGHT
    if accent is None:
        accent = FP.GOLD
    x, y, w, h = rect

    # Two-tone bg
    pygame.draw.rect(surf, FP.MIDNIGHT,     (x, y,      w, h // 2))
    pygame.draw.rect(surf, FP.MIDNIGHT_MID, (x, y+h//2, w, h - h//2))

    # Bottom separator line
    pygame.draw.line(surf, accent, (x + 8, y + h - 1), (x + w - 8, y + h - 1), 1)

    # Side diamond accents
    for ax in [x + 14, x + w - 15]:
        _edge_diamond(surf, ax, y + h//2, accent, vertical=True, size=4)

    # Title text
    if text and font:
        ts = font.render(text, True, text_color)
        sx = x + w//2 - ts.get_width()//2
        sy = y + h//2 - ts.get_height()//2
        shadow = font.render(text, True, FP.INK)
        surf.blit(shadow, (sx + 2, sy + 2))
        surf.blit(ts,     (sx,     sy))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION DIVIDER
# ─────────────────────────────────────────────────────────────────────────────

def draw_divider(surf: pygame.Surface, x: int, y: int, w: int,
                 color: tuple | None = None) -> None:
    """# FANTASY: Ornamental horizontal divider with center diamond."""
    if color is None:
        color = FP.GOLD_DARK
    cx = x + w // 2
    pygame.draw.line(surf, color, (x + 18, y), (cx - 14, y), 1)
    pygame.draw.line(surf, color, (cx + 14, y), (x + w - 18, y), 1)
    d = 5
    pts = [(cx-d*2, y), (cx, y-d), (cx+d*2, y), (cx, y+d)]
    pygame.draw.polygon(surf, color, pts)


# ─────────────────────────────────────────────────────────────────────────────
# TEXT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def draw_shadow_text(surf: pygame.Surface, font: pygame.font.Font,
                     text: str, color: tuple, pos: tuple,
                     shadow: tuple = FP.INK, offset: int = 2) -> tuple[int, int]:
    """# FANTASY: Render text with an ink drop-shadow."""
    sx, sy = pos
    sh = font.render(text, True, shadow)
    surf.blit(sh, (sx + offset, sy + offset))
    ts = font.render(text, True, color)
    surf.blit(ts, (sx, sy))
    return ts.get_width(), ts.get_height()


def draw_glow_text(surf: pygame.Surface, font: pygame.font.Font,
                   text: str, color: tuple, pos: tuple,
                   glow_color: tuple | None = None,
                   glow_r: int = 3) -> tuple[int, int]:
    """# FANTASY: Render text with a subtle colour glow."""
    if glow_color is None:
        glow_color = tuple(min(255, c + 70) for c in color[:3])
    sx, sy = pos
    # Glow passes (low-alpha renders offset in a halo)
    glow_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for dx in range(-glow_r, glow_r + 1, 2):
        for dy in range(-glow_r, glow_r + 1, 2):
            if dx == 0 and dy == 0:
                continue
            gs = font.render(text, True, (*glow_color[:3], 55))
            glow_surf.blit(gs, (sx + dx, sy + dy))
    surf.blit(glow_surf, (0, 0))
    ts = font.render(text, True, color)
    surf.blit(ts, (sx, sy))
    return ts.get_width(), ts.get_height()


def centered_text(surf: pygame.Surface, font: pygame.font.Font,
                  text: str, color: tuple, cy: int,
                  cx: int | None = None,
                  shadow: bool = True) -> None:
    """# FANTASY: Horizontally-centred text, optional shadow."""
    if cx is None:
        cx = surf.get_width() // 2
    ts = font.render(text, True, color)
    tx = cx - ts.get_width() // 2
    if shadow:
        sh = font.render(text, True, FP.INK)
        surf.blit(sh, (tx + 2, cy + 2))
    surf.blit(ts, (tx, cy))


# ─────────────────────────────────────────────────────────────────────────────
# ILLUMINATED ORNAMENTS
# ─────────────────────────────────────────────────────────────────────────────

def draw_rune_circle(surf: pygame.Surface, cx: int, cy: int,
                     radius: int, color: tuple, t: float = 0.0,
                     segments: int = 12) -> None:
    """
    # FANTASY: Rotating rune circle — decorative arcane ring.
    Draw on victory/death screens for drama.
    t: animation time in seconds.
    """
    for i in range(segments):
        a = math.radians(i * 360 / segments) + t * 0.3
        a2 = math.radians((i + 0.4) * 360 / segments) + t * 0.3
        x1 = cx + int(radius * math.cos(a))
        y1 = cy + int(radius * math.sin(a))
        x2 = cx + int(radius * math.cos(a2))
        y2 = cy + int(radius * math.sin(a2))
        pygame.draw.line(surf, color, (x1, y1), (x2, y2), 2)
    # Inner ring
    for i in range(segments // 2):
        a = math.radians(i * 360 / (segments // 2)) - t * 0.5
        px = cx + int((radius * 0.65) * math.cos(a))
        py = cy + int((radius * 0.65) * math.sin(a))
        pygame.draw.circle(surf, color, (px, py), 3)


def draw_filigree_bar(surf: pygame.Surface, x: int, y: int, w: int,
                      color: tuple | None = None) -> None:
    """
    # FANTASY: Horizontal decorative filigree bar (title underlines, etc.).
    """
    if color is None:
        color = FP.GOLD_DARK
    cx = x + w // 2
    # Main line
    pygame.draw.line(surf, color, (x, y), (x + w, y), 1)
    # Swirl dots
    for i in range(8):
        px = x + i * (w // 8) + w // 16
        pygame.draw.circle(surf, color, (px, y), 2)
    # Center triple diamond
    for dx, dy in [(-10, 0), (0, -4), (10, 0)]:
        d = 4
        pts = [(cx+dx, y+dy-d), (cx+dx+d, y+dy),
               (cx+dx, y+dy+d), (cx+dx-d, y+dy)]
        pygame.draw.polygon(surf, color, pts)


def draw_candle_glow(surf: pygame.Surface, cx: int, cy: int,
                     intensity: float = 1.0) -> None:
    """
    # FANTASY: Soft warm candle-light glow circle.
    Use on altars, welcome screen, etc.
    intensity: 0.0–1.0
    """
    glow = pygame.Surface((200, 200), pygame.SRCALPHA)
    for r in range(90, 0, -8):
        a = int(22 * (r / 90) * intensity)
        pygame.draw.circle(glow, (255, 200, 80, a), (100, 100), r)
    surf.blit(glow, (cx - 100, cy - 100))


# ─────────────────────────────────────────────────────────────────────────────
# ITEM CLASS COLOUR MAP  (richer than the old _IC_COLOR in ui.py)
# ─────────────────────────────────────────────────────────────────────────────
ITEM_COLOR = {
    'weapon':     (225, 155,  65),   # warm bronze
    'armor':      ( 80, 148, 215),   # steel blue
    'shield':     ( 80, 168, 215),
    'ingredient': (140, 210, 100),   # herb green
    'corpse':     (148,  68,  68),   # dried blood
    'accessory':  (208, 102, 208),   # arcane violet
    'wand':       ( 90, 185, 230),   # arcane blue
    'scroll':     (225, 215, 150),   # parchment yellow
    'food':       (180, 215, 110),
    'ammo':       (190, 175, 120),
    'artifact':   FP.GOLD_BRIGHT,
    'lockpick':   (175, 175, 175),
    'container':  (160, 135,  90),
}


# ─────────────────────────────────────────────────────────────────────────────
# CHOICE BUTTON
# ─────────────────────────────────────────────────────────────────────────────

def draw_choice_button(surf: pygame.Surface, rect: tuple,
                       key_label: str, text: str,
                       key_font: pygame.font.Font,
                       text_font: pygame.font.Font,
                       selected: bool = False,
                       correct: bool | None = None,
                       incorrect: bool | None = None) -> None:
    """
    # FANTASY: Ornate answer-choice button for the quiz modal.
    rect = (x, y, w, h)
    """
    x, y, w, h = rect

    # Background tint
    if correct:
        bg_col = (20, 65, 22)
        border_col = FP.SUCCESS_TEXT
    elif incorrect:
        bg_col = (70, 14, 14)
        border_col = FP.DANGER_TEXT
    elif selected:
        bg_col = FP.MIDNIGHT_MID
        border_col = FP.GOLD
    else:
        bg_col = FP.MIDNIGHT
        border_col = FP.GOLD_DARK

    bg_s = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_s.fill((*bg_col, 220))
    surf.blit(bg_s, (x, y))

    pygame.draw.rect(surf, border_col, (x, y, w, h), 1, border_radius=3)

    # Key badge (left side)
    badge_w = 40
    badge_s = pygame.Surface((badge_w, h), pygame.SRCALPHA)
    badge_s.fill((*FP.MIDNIGHT_MID, 200))
    surf.blit(badge_s, (x, y))
    pygame.draw.line(surf, border_col, (x + badge_w, y), (x + badge_w, y + h), 1)

    k_surf = key_font.render(key_label, True, FP.GOLD_BRIGHT)
    surf.blit(k_surf, (x + badge_w//2 - k_surf.get_width()//2,
                       y + h//2 - k_surf.get_height()//2))

    # Choice text
    t_color = FP.PARCHMENT_LIGHT if not (correct or incorrect) else border_col
    t_surf = text_font.render(text, True, t_color)
    surf.blit(t_surf, (x + badge_w + 10,
                       y + h//2 - t_surf.get_height()//2))
