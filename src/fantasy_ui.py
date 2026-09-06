"""
fantasy_ui.py -- High-fantasy medieval / arcane grimoire UI theme.
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
from paths import data_path

# -----------------------------------------------------------------------------
# FANTASY PALETTE  (FP namespace -- "Fantasy Palette")
# -----------------------------------------------------------------------------
#
# DESIGN-SYSTEM USAGE RULES (enforced by code review; the catalog at
# tools/audit/deliverables/beauty_screen_catalog.md identifies offenders).
#
#   * Never write raw (R, G, B) literals in render code outside this file.
#     Add a named constant here and reference it. The catalog calls this
#     'beauty-palette-bypass' and lists ~50 places it happens.
#
#   * Body text on any midnight panel  -> FP.BODY_TEXT
#     Faded / secondary body text      -> FP.FADED_TEXT
#     Accented labels                  -> FP.ACCENT_TEXT
#     "Press X to close" footer hint   -> FP.HINT_TEXT (mandatory)
#     "Press X" hint that needs to    -> FP.HINT_TEXT_DIM
#       sit quieter (e.g. on dense
#       lore screens where the hint
#       competes with body text)
#
#   * Panel borders:
#       generic modal      -> FP.GOLD
#       arcane / magic     -> FP.ARCANE_BRIGHT  (wand, spell, scroll, identify)
#       success outcome    -> FP.SUCCESS_TEXT   (eat menu)
#       danger / death     -> FP.BLOOD / FP.BURGUNDY_MID
#       lore display       -> FP.LORE_GOLD (corpse) / FP.LORE_BLUE (item)
#
#   * Status / damage tags follow the MessageLog mapping in ui.py:
#       'info'    -> BODY_TEXT
#       'success' -> SUCCESS_TEXT
#       'warning' -> WARNING_TEXT
#       'danger'  -> DANGER_TEXT
#       'loot'    -> LOOT_TEXT
#     Use these tags via add_message(); do not pick the color directly.
#
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

    # -- Semantic aliases (use these in draw code) --------------------------
    PANEL_BG        = MIDNIGHT          # modal/panel background
    PANEL_BG_MID    = MIDNIGHT_MID      # slightly lighter panel
    PANEL_BORDER    = GOLD              # main border colour
    PANEL_INNER     = GOLD_DARK         # inner double-border colour
    HEADER_BG       = MIDNIGHT          # header strip fill
    HEADER_TEXT     = GOLD_BRIGHT       # header text
    BODY_TEXT       = PARCHMENT         # normal body text
    FADED_TEXT      = (165, 155, 185)   # disabled / secondary text -- lavender-grey, ~6:1 on midnight
    ACCENT_TEXT     = GOLD_PALE         # accented label text
    HINT_TEXT       = (170, 165, 215)   # keyboard hint text -- boosted blue-lavender, ~7:1 on midnight
    HINT_TEXT_DIM   = (118, 113, 158)   # dimmer hint variant for dense content screens (~4.5:1)
    DANGER_TEXT     = BLOOD
    # DANGER_TEXT_LIGHT — for danger text rendered ON dark backgrounds (cursed
    # items in menu rows, harmful potions, wrong-answer choice cards). The
    # canonical DANGER_TEXT/BLOOD is too dark on MIDNIGHT_MID and on the
    # incorrect-answer card bg (70,14,14) — contrast 2.67, invisible.
    DANGER_TEXT_LIGHT = (255, 150, 150)
    SUCCESS_TEXT    = (110, 220, 100)
    WARNING_TEXT    = (220, 185,  45)
    LOOT_TEXT       = GOLD_BRIGHT

    # Lore display palettes (used by encyclopedia detail, _draw_lore_screen,
    # _draw_hint_screen). Two families: warm-gold for corpse/biology lore,
    # cool-blue for item/artifact lore. Both were inline RGB before the
    # design-system pass; centralizing them here so refactor in one place
    # propagates everywhere.
    LORE_GOLD_BORDER = (160, 120,  40)
    LORE_GOLD_INNER  = ( 80,  62,  20)
    LORE_GOLD_TITLE  = (220, 180,  80)
    LORE_GOLD_STAT   = (200, 170,  90)
    LORE_GOLD_BODY   = (230, 215, 180)

    LORE_BLUE_BORDER = ( 80, 120, 200)
    LORE_BLUE_INNER  = ( 40,  60, 110)
    LORE_BLUE_TITLE  = (140, 175, 240)
    LORE_BLUE_STAT   = (150, 175, 215)
    LORE_BLUE_BODY   = (200, 215, 240)

    # Accent text colors — used by the character sheet and other detail
    # readouts. CYAN_ACCENT lands lighter / cooler than LORE_BLUE_BODY;
    # ARCANE_ACCENT is a pale arcane purple readable on midnight bg.
    CYAN_ACCENT      = (120, 210, 240)
    ARCANE_ACCENT    = (200, 170, 255)
    AMBER_ACCENT     = (200, 155,  80)   # warm amber for warnings / passives

    # Resource bar colors (HP / SP / MP) — used as BAR FILLS in the sidebar
    # and the quiz combat HUD. Some values run dark on purpose so the bars
    # read as bars, not text. Use the *_TEXT variants below when rendering
    # the corresponding label / readout TEXT on the midnight panel — the
    # contrast on dark blue bg needs ~4.5:1 to be legible.
    HP_RED           = (185,  42,  42)
    SP_GREEN         = (110, 200,  90)
    SP_AMBER         = (200, 170,  50)   # SP hunger warning
    SP_RED           = (210,  80,  60)   # SP starvation
    MP_BLUE          = ( 50,  85, 205)
    MP_BLUE_TEXT     = (130, 175, 255)   # readable on midnight (text use)

    # Cooldown / readiness status colors (sidebar status section).
    COOLDOWN_TEAL    = (120, 195, 230)   # cooldown text — bumped from (80,160,200) for contrast
    READY_TEAL       = (140, 215, 245)   # ready text   — bumped from (120,200,240)
    COOLDOWN_ARCANE  = (185, 140, 235)   # prayer cooldown — bumped from (140,100,200) for contrast

    # Passive status colors (sidebar passive list — Fire Protect, Manifest,
    # Death Ward etc.). Named so they don't compete with each other for
    # attention but stay readable on the midnight bg.
    PASSIVE_FIRE     = (245, 150,  60)
    PASSIVE_MANIFEST = (210, 180, 245)
    PASSIVE_WARD     = (220, 220, 255)

    # Empty equipment slot — the dim "no item" filler in the sidebar.
    # Must still be legible. Original (52,52,70) was ~2:1 contrast (unreadable);
    # (140,140,165) reaches 4.7:1 — clears WCAG AA while staying visibly muted.
    SLOT_EMPTY       = (140, 140, 165)

    # Subject accent mapping — single source of truth used by the quiz
    # panel border, welcome screen domain ring, and standalone study mode.
    # Adding a subject? Add it here and only here.
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
        'trivia':     (255, 200, 100),
        'ai':         (  0, 220, 120),
    }


# -----------------------------------------------------------------------------
# FONT LOADING
# -----------------------------------------------------------------------------
_FONT_DIR = data_path('assets', 'fonts')

# # FANTASY: TTF filenames expected in assets/fonts/
# All shipped from Google Fonts (OFL-licensed). Cinzel is now distributed as a
# single variable-weight TTF — pygame's synthetic-bold flag handles the title
# role's bold rendering off the same file.
_ROLE_FILES = {
    'title':   'Cinzel-Variable.ttf',
    'heading': 'Cinzel-Variable.ttf',
    'body':    'IMFellEnglish-Regular.ttf',
    'small':   'IMFellEnglish-Regular.ttf',
    'gothic':  'UnifrakturMaguntia.ttf',
    'italic':  'IMFellEnglish-Italic.ttf',
}

# Fallback serif chain when the bundled TTF fails: Windows fonts first, then
# Linux (Liberation/DejaVu/Noto), then generic. macOS covered by Palatino/Georgia.
_FALLBACK_FAMILIES = (
    'garamond,palatino linotype,palatino,georgia,book antiqua,times new roman,'
    'liberation serif,dejavu serif,noto serif,urw bookman l,serif,consolas'
)

# Monospace fallback for body/small/mono roles when Consolas isn't available.
_MONO_FAMILIES = (
    'consolas,courier new,'
    'dejavu sans mono,liberation mono,noto mono,ubuntu mono,monospace'
)

# Unicode-capable font families for symbol/icon rendering (* o x Sum Omega * etc.)
_SYMBOL_FAMILIES = 'segoe ui symbol,segoe ui emoji,noto sans symbols,dejavu sans,arial unicode ms,unifont'
_font_cache: dict = {}


def get_font(role: str, size: int, bold: bool = False) -> pygame.font.Font:
    """
    # FANTASY: Return a themed font.
    role: 'title'   -> Cinzel Bold (large display, all-caps)
          'heading' -> Cinzel Regular (section headers)
          'body'    -> Consolas (crisp readable body text)
          'small'   -> Consolas small
          'italic'  -> IM Fell English Italic
          'gothic'  -> UnifrakturMaguntia (dramatic blackletter)
          'mono'    -> Consolas (monospace -- code/numbers)
    Falls back gracefully if TTF not installed.
    """
    key = (role, size, bold)
    if key in _font_cache:
        return _font_cache[key]

    if role == 'symbol':
        # Unicode-capable font for rendering special characters (* o x Sum Omega * etc.)
        font = pygame.font.SysFont(_SYMBOL_FAMILIES, size, bold=bold)
    elif role in ('mono', 'body', 'small'):
        # Use Consolas for all body/small roles -- crisp and highly readable.
        # Fallback chain covers Windows / macOS / Linux monospace families.
        font = pygame.font.SysFont(_MONO_FAMILIES, size, bold=bold)
    else:
        fname = _ROLE_FILES.get(role, 'Cinzel-Variable.ttf')
        path  = os.path.join(_FONT_DIR, fname)
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                # Title role is implicitly bold; heading is regular weight.
                # Synthetic bold via pygame works on variable fonts too.
                if role == 'title' or bold:
                    font.bold = True
            except Exception:
                font = pygame.font.SysFont(_FALLBACK_FAMILIES, size, bold=bold)
        else:
            font = pygame.font.SysFont(_FALLBACK_FAMILIES, size, bold=bold)

    _font_cache[key] = font
    return font


# -----------------------------------------------------------------------------
# PARCHMENT TEXTURE
# -----------------------------------------------------------------------------
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

    # Corner/edge vignette -- slightly darker edges
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
    path = data_path('assets', 'textures', 'parchment.png')
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (w, h))
        img.set_alpha(alpha)
        return img
    except Exception:
        return None


# -----------------------------------------------------------------------------
# OVERLAY HELPERS
# -----------------------------------------------------------------------------

def draw_overlay(surf: pygame.Surface, alpha: int = 185,
                 color: tuple = (0, 0, 0)):
    """# FANTASY: Dark semi-transparent overlay (full screen)."""
    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    ov.fill((*color, alpha))
    surf.blit(ov, (0, 0))


# -----------------------------------------------------------------------------
# ORNATE BORDER & PANEL
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# HEADER STRIP
# -----------------------------------------------------------------------------

def draw_header_bar(surf: pygame.Surface, rect: tuple,
                    text: str = '', font: pygame.font.Font | None = None,
                    text_color: tuple | None = None,
                    accent: tuple | None = None,
                    right_reserve: int = 0) -> None:
    """
    # FANTASY: Decorative header strip inside a panel.
    rect = (x, y, w, h)  -- usually HEADER_H = 44 tall.
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

    # Title text — truncate with ellipsis if wider than the header so the
    # text never overflows the panel sides. Mid-edge diamonds + side padding
    # = 28px each side, so usable interior is w - 56.
    if text and font:
        # Reserve room on the right (e.g. a quiz chain counter) so the centered
        # title never runs under it; clip + center within the remaining region.
        reserve = max(0, right_reserve)
        text = fit_text(text, font, max(20, w - 56 - reserve))
        ts = font.render(text, True, text_color)
        region_w = w - reserve
        sx = x + region_w//2 - ts.get_width()//2
        sy = y + h//2 - ts.get_height()//2
        shadow = font.render(text, True, FP.INK)
        surf.blit(shadow, (sx + 2, sy + 2))
        surf.blit(ts,     (sx,     sy))


# -----------------------------------------------------------------------------
# SECTION DIVIDER
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# TEXT HELPERS
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# ILLUMINATED ORNAMENTS
# -----------------------------------------------------------------------------

def draw_rune_circle(surf: pygame.Surface, cx: int, cy: int,
                     radius: int, color: tuple, t: float = 0.0,
                     segments: int = 12) -> None:
    """
    # FANTASY: Rotating rune circle -- decorative arcane ring.
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
    intensity: 0.0-1.0
    """
    glow = pygame.Surface((200, 200), pygame.SRCALPHA)
    for r in range(90, 0, -8):
        a = int(22 * (r / 90) * intensity)
        pygame.draw.circle(glow, (255, 200, 80, a), (100, 100), r)
    surf.blit(glow, (cx - 100, cy - 100))


# -----------------------------------------------------------------------------
# ITEM CLASS COLOUR MAP  (richer than the old _IC_COLOR in ui.py)
# -----------------------------------------------------------------------------
ITEM_COLOR = {
    'weapon':     (225, 155,  65),   # warm bronze
    'armor':      ( 80, 148, 215),   # steel blue
    'shield':     ( 80, 168, 215),
    'ingredient': (140, 210, 100),   # herb green
    'corpse':     (230, 130, 130),   # blood-red (lifted from 148,68,68 — was unreadable as sidebar text)
    'accessory':  (208, 102, 208),   # arcane violet
    'wand':       ( 90, 185, 230),   # arcane blue
    'scroll':     (225, 215, 150),   # parchment yellow
    'food':       (180, 215, 110),
    'ammo':       (190, 175, 120),
    'artifact':   FP.GOLD_BRIGHT,
    'lockpick':   (175, 175, 175),
    'container':  (160, 135,  90),
}


# -----------------------------------------------------------------------------
# CHOICE BUTTON
# -----------------------------------------------------------------------------

def draw_input_box(surf: pygame.Surface, rect: tuple, value: str,
                   font: pygame.font.Font,
                   border_color: tuple | None = None,
                   text_color: tuple | None = None,
                   placeholder: str = '_') -> None:
    """A small text/number entry box used by the drop-gold, pet-name, and
    QA-warp popups. Shared chrome so the three look like siblings.

    rect = (x, y, w, h). `value` is the current input string; if empty,
    `placeholder` is rendered so the box never looks visually empty.
    """
    if border_color is None:
        border_color = FP.GOLD_BRIGHT
    if text_color is None:
        text_color = FP.PARCHMENT_LIGHT
    x, y, w, h = rect
    pygame.draw.rect(surf, FP.MIDNIGHT_LIGHT, (x, y, w, h), border_radius=4)
    pygame.draw.rect(surf, border_color, (x, y, w, h), 1, border_radius=4)
    display = value if value else placeholder
    val_surf = font.render(display, True, text_color)
    surf.blit(val_surf, (x + 10, y + (h - val_surf.get_height()) // 2))


def draw_choice_button(surf: pygame.Surface, rect: tuple,
                       key_label: str, text: str | list[str],
                       key_font: pygame.font.Font,
                       text_font: pygame.font.Font,
                       selected: bool = False,
                       correct: bool | None = None,
                       incorrect: bool | None = None) -> None:
    """
    # FANTASY: Ornate answer-choice button for the quiz modal.
    rect = (x, y, w, h)
    text: single string or pre-wrapped list[str] of lines (multi-line is
          vertically centered as a block).
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

    # Inner double-stroke for grimoire flavor (matches draw_dark_panel pattern)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x + 3, y + 3, w - 6, h - 6), 1, border_radius=2)

    # Key badge (left side) — bigger rune-stone block
    badge_w = 44
    badge_s = pygame.Surface((badge_w, h), pygame.SRCALPHA)
    badge_s.fill((*FP.MIDNIGHT_MID, 200))
    surf.blit(badge_s, (x, y))
    pygame.draw.line(surf, border_col, (x + badge_w, y), (x + badge_w, y + h), 1)

    k_surf = key_font.render(key_label, True, FP.GOLD_BRIGHT)
    surf.blit(k_surf, (x + badge_w//2 - k_surf.get_width()//2,
                       y + h//2 - k_surf.get_height()//2))

    # Choice text — single string or pre-wrapped list. Always render in
    # PARCHMENT_LIGHT regardless of correct/incorrect state. The BORDER does
    # the color signaling (green/red). Using DANGER_TEXT (200,18,18) as the
    # text color on the incorrect-answer red bg (70,14,14) collapses contrast
    # to 2.67 — invisible. The user reported this as "dark text on blue
    # background" in the identify quiz.
    t_color = FP.PARCHMENT_LIGHT
    if isinstance(text, list):
        lines = text or ['']
    else:
        lines = [text]
    line_h = text_font.get_height() + 3
    block_h = len(lines) * line_h
    ty = y + (h - block_h) // 2
    tx = x + badge_w + 10
    for line in lines:
        t_surf = text_font.render(line, True, t_color)
        surf.blit(t_surf, (tx, ty))
        ty += line_h


# =============================================================================
# UNIVERSAL MENU RENDERER
# =============================================================================

def fit_text(text: str, font, max_w: int) -> str:
    """Truncate text with ellipsis if it exceeds max_w pixels."""
    if font.size(text)[0] <= max_w:
        return text
    while len(text) > 1 and font.size(text + '...')[0] > max_w:
        text = text[:-1]
    return text + '...'


def wrap_text(text: str, font, max_w: int) -> list:
    """Break text into lines that fit within max_w pixels."""
    words = text.split()
    lines, cur = [], ''
    for word in words:
        test = (cur + ' ' + word).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or ['']


def draw_tab_bar(surf, tabs, active_idx: int, bx: int, by: int, bw: int,
                 font, counts=None, y_offset: int = 50):
    """Draw a tab bar. Returns the y position below it."""
    tab_y = by + y_offset
    avail = bw - 20
    PAD = 4
    visible = []
    for i, tab in enumerate(tabs):
        label = tab[0]
        c = counts[i] if counts else None
        if c is not None and c == 0 and i != active_idx:
            continue
        text = f"{label} ({c})" if c is not None else label
        visible.append((i, text))
    # If too wide, drop counts
    total_w = sum(font.size(t)[0] + 14 + PAD for _, t in visible) - PAD
    if total_w > avail and counts:
        visible = []
        for i, tab in enumerate(tabs):
            c = counts[i] if counts else None
            if c is not None and c == 0 and i != active_idx:
                continue
            visible.append((i, tab[0]))
    tab_x = bx + 10
    max_x = bx + bw - 10
    for idx, text in visible:
        tw = font.size(text)[0] + 14
        if tab_x + tw > max_x:
            break
        rect = pygame.Rect(tab_x, tab_y, tw, 24)
        active = idx == active_idx
        if active:
            pygame.draw.rect(surf, FP.MIDNIGHT_MID, rect, border_radius=4)
            pygame.draw.rect(surf, FP.GOLD, rect, 2, border_radius=4)
            col = FP.GOLD_BRIGHT
        else:
            col = FP.FADED_TEXT
        t_surf = font.render(text, True, col)
        surf.blit(t_surf, (tab_x + 7, tab_y + 3))
        tab_x += tw + PAD
    return tab_y + 28


# ── Menu entry helpers ────────────────────────────────────────────────

_ICON_ROW_H = 72
_ICON_SIZE = 32
_TEXT_ROW_BASE = 28
_LETTERS = 'abcdefghijklmnopqrstuvwxyz'


def draw_menu(
    surf,
    *,
    title: str,
    entries: list,         # list of dicts — see below
    scroll: int = 0,
    subtitle: str = '',
    subtitle_color=None,
    tabs=None,
    active_tab: int = 0,
    tab_counts=None,
    hint: str = 'ESC: close',
    border_color=None,
    max_width: int = 820,
    center_in: tuple = (1280, 900),
    font_md=None,
    font_sm=None,
    draw_icon_fn=None,     # callback(surf, icon_source, x, y)
    row_style: str = 'icon',  # default; entries can override per-row
    wrap_detail: bool = False,  # icon rows: wrap long detail across lines
                                # instead of truncating with "..."; row
                                # height grows to fit
):
    """
    Universal scrollable menu overlay.

    Each entry is a dict with keys:
      'name':        str (required)
      'detail':      str (optional, one-line subtitle)
      'detail_lines': list[str] (optional, pre-wrapped multi-line — overrides detail)
      'key':         str (optional, letter label like 'a')
      'icon':        object (optional, passed to draw_icon_fn)
      'name_color':  tuple (default BODY_TEXT)
      'detail_color': tuple (default FADED_TEXT)
      'key_color':   tuple (default GOLD_BRIGHT)
      'selected':    bool (highlight row)
      'section':     str (section header above this row)
      'section_color': tuple
      'badge':       str (right-aligned status badge)
      'badge_color': tuple
      'row_style':   'icon' | 'text' (overrides default)

    Returns (visible_count, total_count, scroll_clamped).
    """
    cw, ch = center_in
    bw = min(max_width, cw - 40)

    # ── Measure content height ──
    header_h = 44
    subtitle_h = 28 if subtitle else 0
    tab_h = 30 if tabs else 0
    divider_h = 10
    hint_h = 38
    chrome_h = header_h + subtitle_h + tab_h + divider_h + hint_h + 16  # padding

    # Measure each entry -- ONE row_heights element PER entry (a section header
    # is folded into its entry's height) so the list stays index-aligned with
    # `entries` for the scroll-to-selection math below.
    row_heights = []
    text_max_w = bw - 50 if row_style == 'text' else bw - 140
    # Width matching the icon-row render path's name_max (assuming no badge):
    #   tx = bx + 110; name_max = bw - 110 - 20 = bw - 130
    icon_detail_wrap_w = bw - 130
    for entry in entries:
        rs = entry.get('row_style', row_style)
        rh = 28 if entry.get('section') else 0   # section header folded in
        if rs == 'icon':
            rh += _ICON_ROW_H
            # Opt-in wrap: cache wrapped lines on the entry so the render
            # path uses the same list (and grows the row by 18px per
            # extra line). First line already fits in the base row.
            if (wrap_detail and entry.get('detail')
                    and not entry.get('detail_lines') and font_sm):
                wrapped = wrap_text(entry['detail'], font_sm, icon_detail_wrap_w)
                if len(wrapped) > 1:
                    entry['_wrapped_detail'] = wrapped
                    rh += (len(wrapped) - 1) * 18
            # Caller-supplied detail_lines (e.g. cook menu pre-wraps for
            # the recipe tier-preview). Bug bash 2026-06-01: without this
            # branch the multi-line content rendered ON TOP of the next
            # row's icon. Now the row grows to fit.
            elif entry.get('detail_lines') and len(entry['detail_lines']) > 1:
                rh += (len(entry['detail_lines']) - 1) * 18
        else:
            # Text row: measure wrapped height
            detail_lines = entry.get('detail_lines')
            if not detail_lines and entry.get('detail'):
                detail_lines = wrap_text(entry['detail'], font_sm, text_max_w) if font_sm else [entry['detail']]
            name_lines = wrap_text(entry['name'], font_md, text_max_w) if font_md else [entry['name']]
            n_lines = len(name_lines) + (len(detail_lines) if detail_lines else 0)
            rh += max(_TEXT_ROW_BASE, n_lines * 22 + 8)
        row_heights.append(rh)

    total_content = sum(row_heights)
    max_content = ch - 40 - chrome_h
    needs_scroll = total_content > max_content
    bh = min(chrome_h + total_content, ch - 40)
    bx = (cw - bw) // 2
    by = (ch - bh) // 2

    # Clamp scroll, then AUTO-FOLLOW the selected row so it is always visible.
    # A cursor-driven menu (one row has 'selected': True) need not track a
    # scroll offset at all -- the viewport chases the cursor. Letter-driven
    # menus (no selected row) keep the caller's offset for manual Up/Down.
    if needs_scroll:
        scroll = max(0, min(scroll, max(0, len(entries) - 1)))
        sel = next((i for i, e in enumerate(entries) if e.get('selected')), None)
        if sel is not None:
            if sel < scroll:
                scroll = sel
            else:
                while scroll < sel and sum(row_heights[scroll:sel + 1]) > max_content:
                    scroll += 1
    else:
        scroll = 0

    # ── Draw chrome ──
    draw_overlay(surf, 190)
    draw_dark_panel(surf, (bx, by, bw, bh), border_color=border_color or FP.GOLD)
    draw_header_bar(surf, (bx, by, bw, header_h), text=title,
                    font=font_md, text_color=FP.GOLD_BRIGHT)

    cy = by + header_h + 4

    if subtitle:
        sc = subtitle_color or FP.BODY_TEXT
        subtitle = fit_text(subtitle, font_sm, bw - 40)
        surf.blit(font_sm.render(subtitle, True, sc), (bx + 20, cy))
        cy += subtitle_h

    if tabs:
        tab_y_off = cy - by  # tabs start wherever cy currently is
        cy = draw_tab_bar(surf, tabs, active_tab, bx, by, bw, font_sm, tab_counts,
                          y_offset=tab_y_off)

    draw_divider(surf, bx + 10, cy, bw - 20)
    cy += 8

    content_top = cy
    content_bottom = by + bh - hint_h - 4  # 4px safety margin above hint

    # ── Clip to content area — HARD boundary, nothing renders outside ──
    old_clip = surf.get_clip()
    clip_rect = pygame.Rect(bx + 5, content_top, bw - 10, max(1, content_bottom - content_top))
    surf.set_clip(clip_rect)

    # ── Render entries ──
    visible_count = 0
    entry_idx = 0
    # Skip entries before scroll offset
    for skip_i in range(scroll):
        if skip_i >= len(entries):
            break
        entry = entries[skip_i]
        entry_idx += 1

    has_more_above = scroll > 0
    has_more_below = False

    for i in range(scroll, len(entries)):
        entry = entries[i]
        rs = entry.get('row_style', row_style)

        # Section header
        sec = entry.get('section', '')
        if sec:
            if cy > content_top + 4:
                draw_divider(surf, bx + 10, cy + 2, bw - 20)
                cy += 8
            sec_col = entry.get('section_color', FP.GOLD_BRIGHT)
            sec = fit_text(sec, font_sm, bw - 36)
            surf.blit(font_sm.render(sec, True, sec_col), (bx + 18, cy))
            cy += 24

        if cy + 20 >= content_bottom:  # stop before last row would overflow
            has_more_below = True
            break

        # Row background
        bg_col = FP.MIDNIGHT_MID if visible_count % 2 == 0 else FP.MIDNIGHT
        if entry.get('selected'):
            bg_col = (40, 55, 110)

        if rs == 'icon':
            rh = _ICON_ROW_H
            # Mirror the measurement-loop row-height growth so wrapped
            # detail lines fit and the next row doesn't overlap.
            wrapped_detail = entry.get('_wrapped_detail')
            if wrapped_detail:
                rh += (len(wrapped_detail) - 1) * 18
            elif entry.get('detail_lines') and len(entry['detail_lines']) > 1:
                # Bug bash 2026-06-01: caller-supplied pre-wrapped lines
                # (e.g. cook menu Recipes tab) also need the row to grow.
                rh += (len(entry['detail_lines']) - 1) * 18
            pygame.draw.rect(surf, bg_col, (bx + 10, cy, bw - 20, rh - 8), border_radius=6)

            # Key label
            key = entry.get('key', '')
            if key:
                kc = entry.get('key_color', FP.GOLD_BRIGHT)
                lbl_h = font_md.get_height()
                lbl_y = cy + 4 + (_ICON_SIZE - lbl_h) // 2
                surf.blit(font_md.render(f"[{key}]", True, kc), (bx + 18, lbl_y))

            # Icon
            icon_src = entry.get('icon')
            if icon_src and draw_icon_fn:
                draw_icon_fn(surf, icon_src, bx + 56, cy + 4)

            # Badge (right-aligned on name line) — measured first so the
            # name's max width accounts for it and they never collide.
            badge = entry.get('badge', '')
            badge_w = 0
            if badge:
                bc = entry.get('badge_color', FP.FADED_TEXT)
                b_surf = font_sm.render(badge, True, bc)
                badge_w = b_surf.get_width() + 12
                surf.blit(b_surf, (bx + bw - 25 - b_surf.get_width(), cy + 10))

            # Name — fitted to leave room for the badge
            tx = bx + (110 if draw_icon_fn else 60)
            name_max = bw - (tx - bx) - 20 - badge_w
            nc = entry.get('name_color', FP.BODY_TEXT)
            name_text = fit_text(entry['name'], font_md, name_max)
            surf.blit(font_md.render(name_text, True, nc), (tx, cy + 8))

            # Detail — three sources, in priority order:
            #   1. caller-supplied detail_lines (pre-wrapped)
            #   2. wrap_detail=True cache (_wrapped_detail)
            #   3. single-line truncated fallback (the original behaviour)
            det_y = cy + 4 + _ICON_SIZE + 6
            dc = entry.get('detail_color', FP.FADED_TEXT)
            detail_lines = entry.get('detail_lines') or wrapped_detail
            if detail_lines:
                for dl in detail_lines:
                    if det_y < content_bottom:
                        surf.blit(font_sm.render(fit_text(dl, font_sm, name_max), True, dc), (tx, det_y))
                        det_y += 18
            elif entry.get('detail'):
                det_text = fit_text(entry['detail'], font_sm, name_max)
                surf.blit(font_sm.render(det_text, True, dc), (tx, det_y))

            cy += rh

        else:  # text row
            name_lines = wrap_text(entry['name'], font_md, bw - 50)
            detail_lines = entry.get('detail_lines')
            if not detail_lines and entry.get('detail'):
                detail_lines = wrap_text(entry['detail'], font_sm, bw - 50)

            n_total = len(name_lines) + (len(detail_lines) if detail_lines else 0)
            rh = max(_TEXT_ROW_BASE, n_total * 22 + 8)
            pygame.draw.rect(surf, bg_col, (bx + 10, cy, bw - 20, rh - 4), border_radius=6)

            # Key label
            key = entry.get('key', '')
            tx = bx + 20
            if key:
                kc = entry.get('key_color', FP.GOLD_BRIGHT)
                surf.blit(font_md.render(f"[{key}]", True, kc), (tx, cy + 4))
                tx += 45

            # Name lines
            nc = entry.get('name_color', FP.BODY_TEXT)
            line_y = cy + 4
            for nl in name_lines:
                if line_y < content_bottom:
                    surf.blit(font_md.render(nl, True, nc), (tx, line_y))
                    line_y += 22

            # Detail lines
            if detail_lines:
                dc = entry.get('detail_color', FP.FADED_TEXT)
                for dl in detail_lines:
                    if line_y < content_bottom:
                        surf.blit(font_sm.render(dl, True, dc), (tx, line_y))
                        line_y += 20

            # Badge
            badge = entry.get('badge', '')
            if badge:
                bc = entry.get('badge_color', FP.FADED_TEXT)
                b_surf = font_sm.render(badge, True, bc)
                surf.blit(b_surf, (bx + bw - 25 - b_surf.get_width(), cy + 6))

            cy += rh

        visible_count += 1

    if scroll + visible_count < len(entries):
        has_more_below = True

    # ── Restore clip ──
    surf.set_clip(old_clip)

    # ── Scroll indicators ──
    if has_more_above:
        ind = font_sm.render("-- more above --", True, FP.FADED_TEXT)
        surf.blit(ind, (bx + (bw - ind.get_width()) // 2, content_top - 2))
    if has_more_below:
        ind = font_sm.render("-- more below --", True, FP.FADED_TEXT)
        surf.blit(ind, (bx + (bw - ind.get_width()) // 2, content_bottom - 4))

    # ── Hint footer — always inside panel, never outside screen ──
    hint_y = min(by + bh - 30, ch - 20)  # clamp to screen
    draw_divider(surf, bx + 10, hint_y - 8, bw - 20)
    h_surf = font_sm.render(hint, True, FP.HINT_TEXT)
    # Center hint, but truncate if wider than panel
    if h_surf.get_width() > bw - 20:
        hint = fit_text(hint, font_sm, bw - 20)
        h_surf = font_sm.render(hint, True, FP.HINT_TEXT)
    surf.blit(h_surf, (bx + (bw - h_surf.get_width()) // 2, hint_y))

    return visible_count, len(entries), scroll
