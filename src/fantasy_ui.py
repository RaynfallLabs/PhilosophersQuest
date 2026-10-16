"""
fantasy_ui.py -- High-fantasy medieval / arcane grimoire UI theme.
# FANTASY: Central theme module. All visual helpers live here so main.py
#          and ui.py stay logic-focused. Import what you need:
#
#   from fantasy_ui import (FP, get_font, draw_panel, draw_dark_panel,
#                            draw_panel_frame, draw_divider,
#                            draw_shadow_text, draw_glow_text,
#                            make_parchment, draw_header_bar,
#                            draw_overlay, draw_choice_button)
#
# ART KIT: the panel / header / divider / choice-button / input-box / overlay
# helpers ask ``ui_theme`` (the optional painted-art kit loaded from
# assets/ui/ at startup) first, and draw procedurally when that art is
# missing. With assets/ui/ empty, everything below draws exactly as before.
"""

import math
import os
import random

import pygame
from paths import data_path

import ui_theme

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
    """The optional assets/textures/parchment.png, scaled to (w, h).

    The image is loaded ONCE, by ``ui_theme.load()`` at startup, and each
    scaled copy is cached per size (``ui_theme.texture``). This used to stat
    the file on every call and, had the file existed, load + smoothscale it on
    every frame (FOUNDATION.md 5, "the parchment trap"). None when absent."""
    return ui_theme.texture('parchment', w, h, alpha)


# -----------------------------------------------------------------------------
# OVERLAY HELPERS
# -----------------------------------------------------------------------------

def draw_overlay(surf: pygame.Surface, alpha: int = 185,
                 color: tuple = (0, 0, 0)):
    """# FANTASY: Dark semi-transparent overlay (full screen).

    Every full-window darkening wash in the game goes through here; the
    surface is cached per (window size, colour, alpha) in ui_theme."""
    ui_theme.draw_overlay(surf, alpha, color)


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

    # Double border, corner flourishes, mid-edge diamonds
    _parchment_panel_frame(surf, x, y, w, h, border_color)


def _parchment_panel_frame(surf, x, y, w, h, border_color) -> None:
    """The procedural frame of ``draw_panel`` (square corners)."""
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
                    alpha: int = 255, kind: str = 'panel') -> None:
    """
    # FANTASY: Dark arcane panel (midnight blue bg + gold border).
    Used for quiz, menus etc. over the game world.

    The body is OPAQUE (lead decision 2026-10-15: no text may bleed through
    a panel). ``alpha`` < 255 keeps the old translucent body for a caller
    that really wants one; nothing in the game asks for it.

    ``kind`` names the art piece (``'panel'``, or ``'quiz'`` for the quiz
    modal). With that art loaded the painted frame is drawn instead and
    ``border_color`` tints only its accent layer, never the painted gold.
    A header strip drawn over the top of the panel must repaint the frame:
    pass ``frame=(rect, border_color, kind)`` to ``draw_header_bar``.
    """
    if border_color is None:
        border_color = FP.GOLD
    x, y, w, h = rect
    if w <= 0 or h <= 0:        # a window too small for the panel: draw nothing, raise nothing
        return
    if ui_theme.draw_piece(surf, kind, rect, accent=border_color,
                           body_color=FP.MIDNIGHT):
        return

    # Dark bg with subtle horizontal texture lines
    if alpha >= 255:
        surf.fill(FP.MIDNIGHT, (x, y, w, h))
        lit = tuple(min(255, v + 4) for v in FP.MIDNIGHT)
        for row in range(0, h - 2, 10):
            pygame.draw.line(surf, lit, (x + 3, y + row + 2), (x + w - 3, y + row + 2))
    else:
        bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_surf.fill((*FP.MIDNIGHT, alpha))
        for row in range(0, h, 5):
            shade = 4 if (row // 5) % 2 == 0 else 0
            c = tuple(min(255, v + shade) for v in FP.MIDNIGHT)
            pygame.draw.line(bg_surf, (*c, alpha - 10), (3, row + 2), (w - 3, row + 2))
        surf.blit(bg_surf, (x, y))

    _dark_panel_frame(surf, x, y, w, h, border_color)


def draw_panel_frame(surf: pygame.Surface, rect: tuple,
                     border_color: tuple | None = None,
                     kind: str = 'panel', clip=None) -> None:
    """Repaint ONLY the frame (border + ornaments) of a panel, optionally
    clipped to ``clip``. ``kind`` is the panel's art piece (``'panel'`` /
    ``'quiz'``), or ``'parchment'`` for a ``draw_panel`` parchment box.

    Used by ``draw_header_bar(frame=...)``: the opaque header strip covers
    the top of the panel, so the frame is painted again over the strip,
    clipped to the strip. The procedural frame is opaque and not
    anti-aliased, so painting it twice changes nothing outside the strip."""
    if border_color is None:
        border_color = FP.GOLD
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    if kind != 'parchment' and ui_theme.draw_piece(
            surf, kind, rect, accent=border_color, body=False, clip=clip):
        return
    old_clip = None
    if clip is not None:
        old_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(clip).clip(old_clip))
    try:
        if kind == 'parchment':
            _parchment_panel_frame(surf, x, y, w, h, border_color)
        else:
            _dark_panel_frame(surf, x, y, w, h, border_color)
    finally:
        if old_clip is not None:
            surf.set_clip(old_clip)


def _dark_panel_frame(surf, x, y, w, h, border_color) -> None:
    """The procedural frame of ``draw_dark_panel``: double border, corner
    flourishes, mid-edge diamonds."""
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
                    right_reserve: int = 0, *,
                    frame: tuple | None = None,
                    kind: str = 'header') -> None:
    """
    # FANTASY: Decorative header strip inside a panel.
    rect = (x, y, w, h)  -- usually HEADER_H = 44 tall.

    ``frame=(panel_rect, border_color[, panel_kind])`` names the panel this
    strip sits in. The strip is opaque and starts at the panel's own edge,
    so on its own it paints over the panel's top and side borders
    (FOUNDATION_REVIEW 1). With ``frame`` the panel's frame is repainted
    over the strip, clipped to the strip, before the title is drawn.

    ``kind`` is the art piece for the strip (``'header'``; the sidebar uses
    ``'header_small'``). The title text is always drawn here, on top.
    """
    if text_color is None:
        text_color = FP.GOLD_BRIGHT
    if accent is None:
        accent = FP.GOLD
    x, y, w, h = rect

    if ui_theme.draw_piece(surf, kind, rect, accent=accent):
        if frame is not None:
            _repaint_frame(surf, frame, rect)
    else:
        # Two-tone bg
        pygame.draw.rect(surf, FP.MIDNIGHT,     (x, y,      w, h // 2))
        pygame.draw.rect(surf, FP.MIDNIGHT_MID, (x, y+h//2, w, h - h//2))
        if frame is not None:
            _repaint_frame(surf, frame, rect)

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


def _repaint_frame(surf, frame, strip_rect) -> None:
    """Repaint a panel's frame over a header strip, clipped to the strip."""
    panel_rect, border_color = frame[0], frame[1]
    panel_kind = frame[2] if len(frame) > 2 else 'panel'
    draw_panel_frame(surf, panel_rect, border_color, panel_kind,
                     clip=pygame.Rect(strip_rect))


# -----------------------------------------------------------------------------
# SECTION DIVIDER
# -----------------------------------------------------------------------------

def draw_divider(surf: pygame.Surface, x: int, y: int, w: int,
                 color: tuple | None = None) -> None:
    """# FANTASY: Ornamental horizontal divider with center diamond."""
    if color is None:
        color = FP.GOLD_DARK
    if ui_theme.draw_hbar(surf, 'divider', x, y, w, accent=color):
        return
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
    # Glow passes (low-alpha renders offset in a halo). Composed on a layer
    # just big enough for the halo, not the whole window (that was a
    # window-sized allocation per call, twice a frame on the end screens);
    # the pixels are the same, since the rest of the layer was transparent.
    gs = font.render(text, True, (*glow_color[:3], 55))
    tw, th = gs.get_size()
    glow_surf = pygame.Surface((tw + 2 * glow_r, th + 2 * glow_r), pygame.SRCALPHA)
    for dx in range(-glow_r, glow_r + 1, 2):
        for dy in range(-glow_r, glow_r + 1, 2):
            if dx == 0 and dy == 0:
                continue
            glow_surf.blit(gs, (glow_r + dx, glow_r + dy))
    surf.blit(glow_surf, (sx - glow_r, sy - glow_r))
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
    if not ui_theme.draw_piece(surf, 'input', rect, accent=border_color,
                               body_color=FP.MIDNIGHT_LIGHT):
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

    if w <= 0 or h <= 0:
        return
    badge_w = 44
    if not _choice_button_art(surf, rect, badge_w, correct, incorrect, selected):
        _choice_button_procedural(surf, rect, badge_w, bg_col, border_col)

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


def _choice_button_art(surf, rect, badge_w, correct, incorrect, selected) -> bool:
    """Painted quiz answer card: the state's card piece, the key badge, then
    the card's frame again over the badge (a badge must never cover the card
    border; FOUNDATION_REVIEW 2.4). False if this state's art is missing."""
    name = ('choice_correct' if correct else 'choice_incorrect' if incorrect
            else 'choice_selected' if selected else 'choice')
    x, y, w, h = rect
    if not ui_theme.draw_piece(surf, name, rect, body_color=FP.MIDNIGHT):
        return False
    ui_theme.draw_piece(surf, 'choice_badge', (x, y, badge_w, h))
    ui_theme.draw_piece(surf, name, rect, body=False)
    return True


def _choice_button_procedural(surf, rect, badge_w, bg_col, border_col) -> None:
    """The procedural answer-card chrome: background, borders, key badge."""
    x, y, w, h = rect
    bg_s = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_s.fill((*bg_col, 220))
    surf.blit(bg_s, (x, y))

    pygame.draw.rect(surf, border_col, (x, y, w, h), 1, border_radius=3)

    # Inner double-stroke for grimoire flavor (matches draw_dark_panel pattern)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x + 3, y + 3, w - 6, h - 6), 1, border_radius=2)

    # Key badge (left side) — bigger rune-stone block
    badge_s = pygame.Surface((badge_w, h), pygame.SRCALPHA)
    badge_s.fill((*FP.MIDNIGHT_MID, 200))
    surf.blit(badge_s, (x, y))
    pygame.draw.line(surf, border_col, (x + badge_w, y), (x + badge_w, y + h), 1)


# =============================================================================
# TEXT FITTING
# =============================================================================

def fit_text(text: str, font, max_w: int) -> str:
    """Truncate text with ellipsis if it exceeds max_w pixels."""
    if font.size(text)[0] <= max_w:
        return text
    while len(text) > 1 and font.size(text + '...')[0] > max_w:
        text = text[:-1]
    return text + '...'


# ── Menu entry helpers ────────────────────────────────────────────────

_ICON_ROW_H = 72
_ICON_SIZE = 32
_TEXT_ROW_BASE = 28
_LETTERS = 'abcdefghijklmnopqrstuvwxyz'
