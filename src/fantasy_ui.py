"""
fantasy_ui.py -- High-fantasy medieval / arcane grimoire UI theme.
# FANTASY: Central theme module. All visual helpers live here so main.py
#          and ui.py stay logic-focused. Import what you need:
#
#   from fantasy_ui import (FP, KT, get_font, draw_panel, draw_dark_panel,
#                            draw_panel_frame, draw_divider, draw_key_hints,
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

import ui_scale
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
    # The death-screen headline: a hot blood red that still reads on the
    # blood-red wash (FP.BLOOD there measured 1.7:1), set on a near-black
    # glow so it stays dramatic.
    DEATH_TITLE     = (240,  78,  64)
    DEATH_GLOW      = ( 34,   0,   4)
    DEATH_SUB       = (232, 112, 100)
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


class KT:
    """Midnight Codex kit tokens (_genart/ui/style/DESIGN_RULES.md 2.1, style C).

    Used by the CHROME the art kit draws (plaque titles, sub-panel labels,
    key glyphs, footer key hints, tab labels, quiz card text) when the kit
    is loaded. Content text keeps its ``FP`` colours. Every pair is gated
    for contrast in DESIGN_RULES 2.2 and measured by tests/test_ui_gates.py.
    """
    VOID        = (  6,   7,  14)
    INTERIOR    = ( 16,  19,  38)   # flat body of every modal (frame.png centre)
    RAISED      = ( 24,  29,  56)   # cards, rows, sub-panel bodies
    SELECTED    = ( 40,  46,  86)
    PLAQUE      = ( 20,  26,  58)   # header plaque field
    WELL        = ( 12,  14,  28)   # dark well behind item / creature art
    TEXT_QUIZ   = (248, 238, 212)
    TEXT_BODY   = (234, 222, 194)
    TEXT_DIM    = (186, 182, 214)
    TEXT_HINT   = (186, 182, 214)
    TEXT_HEAD   = (234, 196, 100)
    TEXT_SUB    = (222, 184, 100)
    KEY         = (250, 220, 140)
    KEY_BG      = ( 36,  44,  88)
    GOLD        = (198, 156,  62)
    GOLD_DARK   = (116,  86,  34)
    GOLD_HI     = (240, 208, 128)
    LINE        = ( 70,  78, 130)
    OK_TEXT     = (200, 244, 190)
    BAD_TEXT    = (255, 190, 180)
    DIS_TEXT    = (120, 120, 150)
    GOOD_TEXT   = (140, 216, 124)
    # Message-log tags (DESIGN_RULES 2.1 ``log.*``): they replace
    # FP.DANGER_TEXT = BLOOD, which is 2.3:1 on the log.
    LOG = {
        'info':    (226, 216, 192),
        'success': (140, 216, 124),
        'danger':  (255, 146, 130),
        'warning': (234, 200, 100),
        'loot':    (240, 206, 112),
    }


def kit_on(kind: str = 'panel') -> bool:
    """True when the painted art kit is loaded (the Midnight Codex look)."""
    return ui_theme.has(kind)


def _lum(rgb) -> float:
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(v)) for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    """WCAG contrast ratio of two RGB colours."""
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


_readable_cache: dict = {}


def readable(color, bg, ratio: float = 4.5) -> tuple:
    """``color`` lightened toward white (hue kept) until it reaches
    ``ratio``:1 on ``bg``. Signal colours chosen for borders (an altar's
    colour, an NPC's, ARCANE_BRIGHT) stay recognisable as text on the
    kit's dark fields instead of failing the contrast gate."""
    key = (tuple(color[:3]), tuple(bg[:3]), ratio)
    got = _readable_cache.get(key)
    if got is not None:
        return got
    c = tuple(int(v) for v in color[:3])
    for i in range(0, 21):
        t = i / 20
        cand = tuple(int(v + (255 - v) * t) for v in c)
        if contrast(cand, bg) >= ratio:
            c = cand
            break
    else:
        c = (255, 255, 255)
    _readable_cache[key] = c
    return c


_KEEP_UPPER = frozenset({'AI', 'HP', 'MP', 'SP', 'XP', 'AC', 'BUC', 'QA', 'II', 'III',
                         'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'STR', 'CON',
                         'DEX', 'INT', 'WIS', 'PER', 'NPC', 'DR'})


def display_title(text: str) -> str:
    """An ALL-CAPS title in Title Case for the kit's Cinzel plaques
    ("EQUIP / UNEQUIP" -> "Equip / Unequip"): Cinzel sets capitals and small
    capitals by itself (DESIGN_RULES 3). Mixed-case text is left alone;
    acronyms (AI, HP, roman numerals) stay capitals."""
    if not text or text != text.upper() or not any(c.isalpha() for c in text):
        return text
    from naming import proper_name
    out = []
    for word in text.split(' '):
        core = word.strip("[]():,.!?'\"-")
        if core in _KEEP_UPPER:
            out.append(word)
        else:
            out.append(word.lower())
    titled = proper_name(' '.join(out))
    # proper_name leaves words that hold capitals alone; capitalise a word
    # that starts with punctuation ("(unnamed)" stays as typed).
    return titled[:1].upper() + titled[1:]


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
# Fonts are cached by their LOGICAL key (role, size, bold) -- the size as at
# 1280x720 -- for the CURRENT UI scale. A scale change (ui_scale listener,
# inside layout.update) rebuilds the cache for every key the game has asked
# for so far, so no draw ever creates a font for a size it used before
# (~0.1 ms a font; SCALE_PLAN.md 4). ``_font_px`` holds fixed-size fonts
# (``unscaled=True``), keyed by real pixel size.
_font_cache: dict = {}
_font_px: dict = {}


def _make_font(role: str, size: int, bold: bool) -> pygame.font.Font:
    """A new font of ``size`` real pixels for ``role``."""
    if role == 'symbol':
        # Unicode-capable font for rendering special characters (* o x Sum Omega * etc.)
        return pygame.font.SysFont(_SYMBOL_FAMILIES, size, bold=bold)
    if role in ('mono', 'body', 'small'):
        # Use Consolas for all body/small roles -- crisp and highly readable.
        # Fallback chain covers Windows / macOS / Linux monospace families.
        return pygame.font.SysFont(_MONO_FAMILIES, size, bold=bold)
    fname = _ROLE_FILES.get(role, 'Cinzel-Variable.ttf')
    path  = os.path.join(_FONT_DIR, fname)
    if os.path.exists(path):
        try:
            font = pygame.font.Font(path, size)
            # Title role is implicitly bold; heading is regular weight.
            # Synthetic bold via pygame works on variable fonts too.
            if role == 'title' or bold:
                font.bold = True
            return font
        except Exception:
            pass
    return pygame.font.SysFont(_FALLBACK_FAMILIES, size, bold=bold)


def get_font(role: str, size: int, bold: bool = False, *,
             unscaled: bool = False) -> pygame.font.Font:
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

    ``size`` is the size at 1280x720 (UI scale 1): the font returned is
    ``ui_scale.font_px(size)`` pixels, so every caller grows with the window
    (SCALE_PLAN.md). ``unscaled=True`` returns exactly ``size`` pixels.
    """
    if unscaled:
        key = (role, int(size), bold)
        font = _font_px.get(key)
        if font is None:
            font = _font_px[key] = _make_font(role, int(size), bold)
        return font
    key = (role, size, bold)
    font = _font_cache.get(key)
    if font is None:
        font = _font_cache[key] = _make_font(role, ui_scale.font_px(size), bold)
    return font


def _rescale_fonts(_scale: float) -> None:
    """ui_scale listener: rebuild every cached font at the new scale, now
    (during the resize), not on the first draw that needs it. Keys that land
    on the same pixel size share one font."""
    keys = list(_font_cache)
    _font_cache.clear()
    made = {}
    for role, size, bold in keys:
        k = (role, ui_scale.font_px(size), bold)
        if k not in made:
            made[k] = _make_font(*k)
        _font_cache[(role, size, bold)] = made[k]


ui_scale.add_listener(_rescale_fonts)


class ScaledFont:
    """Class attribute that reads as ``get_font(role, size, bold)`` at the
    current UI scale: ``font_sm = ScaledFont('body', 20)``. Objects used to
    keep a Font made once in ``__init__``, which went stale when the window
    was resized across a scale step. A non-data descriptor, so an instance
    may still assign its own font (tests do)."""

    __slots__ = ('role', 'size', 'bold')

    def __init__(self, role: str, size: int, bold: bool = False):
        self.role, self.size, self.bold = role, size, bold

    def __get__(self, obj, objtype=None):
        return get_font(self.role, self.size, self.bold)


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
    Pass ``frame=(rect, border_color, kind)`` to ``draw_header_bar`` for the
    panel's header: with art it is inset inside the frame band
    (``panel_band``); without art the frame is repainted over the strip.
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

def panel_band(kind: str = 'panel', rect=None) -> int:
    """Width of the painted frame band of a ``kind`` panel drawn at ``rect``
    (0 without art, or when the art would not fit and the procedural frame
    is drawn). Headers and content sit inside it."""
    if kind == 'parchment':
        return 0
    return ui_theme.band(kind, rect)


def header_rect(panel, h: int, kind: str = 'panel') -> pygame.Rect:
    """Where ``draw_header_bar(frame=(panel, ...))`` puts an ``h``-tall header:
    inset inside the frame band with the art kit, flush with the panel's top
    edge without it."""
    panel = pygame.Rect(panel)
    b = panel_band(kind, panel)
    if b and ui_theme.has('header'):
        return pygame.Rect(panel.x + b, panel.y + b, panel.w - 2 * b, h)
    return pygame.Rect(panel.x, panel.y, panel.w, h)


# The plaque's painted rim at the bottom (gold rule + accent rule) that a
# title must not sit on: the flat field is the strip above it (DESIGN_RULES
# 5.3). In UI px at scale 1.
_PLAQUE_RIM = 4
# Room the plaque's scroll-roll ends take at each side.
_PLAQUE_END = 34


def draw_header_bar(surf: pygame.Surface, rect: tuple,
                    text: str = '', font: pygame.font.Font | None = None,
                    text_color: tuple | None = None,
                    accent: tuple | None = None,
                    right_reserve: int = 0, *,
                    frame: tuple | None = None,
                    kind: str = 'header',
                    left_reserve: int = 0) -> pygame.Rect:
    """
    # FANTASY: Decorative header strip inside a panel.
    rect = (x, y, w, h)  -- usually HEADER_H = 44 tall.

    ``frame=(panel_rect, border_color[, panel_kind])`` names the panel this
    strip sits in.

    * With the art kit (a painted panel and the ``header`` plaque loaded) the
      plaque is drawn INSET inside the panel's frame band, clear of the
      frame, and the frame is NOT repainted (this kit's frame slices carry
      the panel body: a repaint would cover the plaque). The title is set in
      Title Case on the plaque's flat field, above its painted rim.
    * Without art the strip starts at the panel's own edge and the panel's
      frame is repainted over it, clipped to the strip (FOUNDATION_REVIEW 1).

    ``kind`` is the art piece for the strip (``'header'``; the sidebar uses
    ``'header_small'``). Returns the rect the strip was drawn in.
    """
    if text_color is None:
        text_color = FP.GOLD_BRIGHT
    if accent is None:
        accent = FP.GOLD
    rect = pygame.Rect(rect)

    art_frame = False
    if frame is not None and ui_theme.has(kind):
        panel_rect = pygame.Rect(frame[0])
        panel_kind = frame[2] if len(frame) > 2 else 'panel'
        b = panel_band(panel_kind, panel_rect)
        if b:
            art_frame = True
            left = max(rect.x, panel_rect.x + b)
            right = min(rect.right, panel_rect.right - b)
            top = max(rect.y, panel_rect.y + b)
            rect = pygame.Rect(left, top, right - left, rect.h)
    x, y, w, h = rect

    art = ui_theme.draw_piece(surf, kind, rect, accent=accent)
    if art:
        if frame is not None and not art_frame:
            _repaint_frame(surf, frame, rect)
    else:
        # Two-tone bg
        pygame.draw.rect(surf, FP.MIDNIGHT,     (x, y,      w, h // 2))
        pygame.draw.rect(surf, FP.MIDNIGHT_MID, (x, y+h//2, w, h - h//2))
        if frame is not None:
            _repaint_frame(surf, frame, rect)

        # Bottom separator line
        S = ui_scale.px
        pygame.draw.line(surf, accent, (x + S(8), y + h - 1), (x + w - S(8), y + h - 1), 1)

        # Side diamond accents
        for ax in [x + S(14), x + w - S(15)]:
            _edge_diamond(surf, ax, y + h//2, accent, vertical=True, size=4)

    if not (text and font):
        return rect
    if art:
        # The kit's plaque: Title Case on the flat field, centred between
        # the scroll-roll ends (and any reserved slots), no drop shadow.
        S = ui_scale.px
        if text_color in (FP.GOLD_BRIGHT, FP.GOLD_PALE, FP.GOLD, FP.HEADER_TEXT):
            text_color = KT.TEXT_HEAD
        else:
            text_color = readable(text_color, KT.PLAQUE)
        text = display_title(text)
        end = S(_PLAQUE_END) if kind == 'header' else S(16)
        lo = x + max(end, left_reserve)
        hi = x + w - max(end, right_reserve)
        text = fit_text(text, font, max(20, hi - lo))
        ts = font.render(text, True, text_color)
        field_h = h - S(_PLAQUE_RIM) if kind == 'header' else h - S(1)
        sx = (x + w // 2) - ts.get_width() // 2
        sx = max(lo, min(sx, hi - ts.get_width()))
        sy = y + (field_h - ts.get_height()) // 2
        surf.blit(ts, (sx, sy))
        return rect

    # Title text — truncate with ellipsis if wider than the header so the
    # text never overflows the panel sides. Mid-edge diamonds + side padding
    # = 28px each side, so usable interior is w - 56.
    # Reserve room on the right (e.g. a quiz chain counter) so the centered
    # title never runs under it; clip + center within the remaining region.
    reserve = max(0, right_reserve)
    text = fit_text(text, font, max(20, w - ui_scale.px(56) - reserve))
    ts = font.render(text, True, text_color)
    region_w = w - reserve
    sx = x + region_w//2 - ts.get_width()//2
    sy = y + h//2 - ts.get_height()//2
    shadow = font.render(text, True, FP.INK)
    off = ui_scale.px(2)
    surf.blit(shadow, (sx + off, sy + off))
    surf.blit(ts,     (sx,     sy))
    return rect


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
    S = ui_scale.px
    pygame.draw.line(surf, color, (x + S(18), y), (cx - S(14), y), 1)
    pygame.draw.line(surf, color, (cx + S(14), y), (x + w - S(18), y), 1)
    d = 5
    pts = [(cx-d*2, y), (cx, y-d), (cx+d*2, y), (cx, y+d)]
    pygame.draw.polygon(surf, color, pts)


def divider_reach() -> int:
    """How far a ``draw_divider`` line reaches above (and below) its ``y``:
    the kit's centre ornament rises well above its hairline. Anything drawn
    above a divider must end at least this far above ``y``."""
    r = ui_theme.hbar_reach('divider')
    return r if r else ui_scale.px(5)


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
        # Without the art kit: exactly the box the game drew before it.
        pygame.draw.rect(surf, FP.MIDNIGHT_LIGHT, (x, y, w, h), border_radius=4)
        pygame.draw.rect(surf, border_color, (x, y, w, h), 1, border_radius=4)
        display = value if value else placeholder
        val_surf = font.render(display, True, text_color)
        surf.blit(val_surf, (x + ui_scale.px(10), y + (h - val_surf.get_height()) // 2))
        return
    # A text caret after what is typed, so the box reads as a field the
    # keyboard is writing into (VISUAL_REVIEW minor 11). Steady, not
    # blinking: it is there on every frame a player looks.
    S = ui_scale.px
    tx = x + S(10)
    if value:
        val_surf = font.render(value, True, text_color)
        surf.blit(val_surf, (tx, y + (h - val_surf.get_height()) // 2))
        cx = tx + val_surf.get_width() + S(3)
    else:
        cx = tx
    ch = min(h - S(10), font.get_height())
    pygame.draw.rect(surf, FP.GOLD_BRIGHT, (cx, y + (h - ch) // 2, max(2, S(2)), ch))
    if not value and placeholder:
        ps = font.render(placeholder, True, readable(FP.FADED_TEXT, FP.MIDNIGHT_LIGHT))
        surf.blit(ps, (cx + S(8), y + (h - ps.get_height()) // 2))


def choice_text_insets() -> tuple[int, int]:
    """(left, right) px of a quiz answer card kept clear of the answer text.
    Left: the key badge plus the ``sm`` step (8) between a badge and its
    label (DESIGN_RULES 4). Right, with the kit: the 40 px slot where the
    painted tick / cross of the correct / incorrect card sits (the card
    art's right slice). Nothing more: the answer wraps only when it does
    not fit the card's real text area (VISUAL_REVIEW_2 minor 2)."""
    S = ui_scale.px
    if ui_theme.has('choice'):
        return S(44) + S(8), S(40)
    return S(44) + S(10), S(22)


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
          vertically centered as a block). Wrap it to the card width minus
          ``choice_text_insets()``.
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
    badge_w = ui_scale.px(44)
    art = _choice_button_art(surf, rect, badge_w, correct, incorrect, selected)
    if not art:
        _choice_button_procedural(surf, rect, badge_w, bg_col, border_col)

    k_surf = key_font.render(key_label, True, KT.KEY if art else FP.GOLD_BRIGHT)
    surf.blit(k_surf, (x + badge_w//2 - k_surf.get_width()//2,
                       y + h//2 - k_surf.get_height()//2))

    # Choice text -- single string or pre-wrapped list. Always render in
    # PARCHMENT_LIGHT regardless of correct/incorrect state. The BORDER does
    # the color signaling (green/red). Using DANGER_TEXT (200,18,18) as the
    # text color on the incorrect-answer red bg (70,14,14) collapses contrast
    # to 2.67 -- invisible. With the kit: the token for the card's state.
    t_color = FP.PARCHMENT_LIGHT
    if art:
        t_color = KT.OK_TEXT if correct else KT.BAD_TEXT if incorrect else KT.TEXT_QUIZ
    if isinstance(text, list):
        lines = text or ['']
    else:
        lines = [text]
    line_h = text_font.get_height() + ui_scale.px(3)
    block_h = len(lines) * line_h
    ty = y + (h - block_h) // 2
    tx = x + choice_text_insets()[0]
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
    i = ui_scale.px(3)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x + i, y + i, w - 2 * i, h - 2 * i), 1, border_radius=2)

    # Key badge (left side) — bigger rune-stone block
    badge_s = pygame.Surface((badge_w, h), pygame.SRCALPHA)
    badge_s.fill((*FP.MIDNIGHT_MID, 200))
    surf.blit(badge_s, (x, y))
    pygame.draw.line(surf, border_col, (x + badge_w, y), (x + badge_w, y + h), 1)


# =============================================================================
# KEY BADGES AND FOOTER KEY HINTS
# =============================================================================

_KEY_WORDS = {
    'up/down': '\u2191/\u2193', 'left/right': '\u2190/\u2192', 'arrows': 'Arrows',
    'esc': 'Esc', 'enter': 'Enter', 'space': 'Space', 'tab': 'Tab',
    'backspace': 'Backspace', 'any key': 'Any Key',
}


def key_label(key: str) -> str:
    """Display form of a key name for a key badge: 'Up/Down' -> arrows,
    'ESC' -> 'Esc', 'Enter or a-z' -> 'Enter / a-z'."""
    parts = []
    for part in str(key).replace(' or ', ' / ').split(' / '):
        part = part.strip()
        low = part.lower()
        if low in _KEY_WORDS:
            part = _KEY_WORDS[low]
        else:
            # "ESC/W" -> "Esc/W"; "PgUp/PgDn" is kept as written
            part = '/'.join(_KEY_WORDS.get(p.lower(), p) for p in part.split('/'))
        parts.append(part)
    return ' / '.join(parts)


def parse_key_hints(text: str) -> list[tuple[str, str]]:
    """Split a footer string ("Up/Down: move   Enter or a-z: select   ESC:
    cancel", with '   ', ' | ' or ' // ' between items) into (key, label)
    pairs, keys in badge form (``key_label``), labels capitalised. An item
    without "key: label" comes back as ('', text)."""
    import re
    items = re.split(r'\s+\|\s+|\s+//\s+|\s{3,}', str(text).strip())
    out = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if ': ' in item:
            k, lab = item.split(': ', 1)
            lab = lab.strip()
            out.append((key_label(k.strip()), lab[:1].upper() + lab[1:]))
        else:
            out.append(('', item))
    return out


def draw_key_badge(surf: pygame.Surface, rect, key: str, font,
                   color: tuple | None = None) -> None:
    """A key-letter badge (the kit's ``key`` piece; a rounded box without
    art) with the key glyph centred on it."""
    rect = pygame.Rect(rect)
    art = ui_theme.draw_piece(surf, 'key', rect)
    if not art:
        pygame.draw.rect(surf, FP.MIDNIGHT_MID, rect, border_radius=4)
        pygame.draw.rect(surf, FP.GOLD_DARK, rect, 1, border_radius=4)
    col = color or (KT.KEY if art else FP.GOLD_BRIGHT)
    if art:
        col = readable(col, KT.KEY_BG)
    ks = font.render(str(key), True, col)
    surf.blit(ks, (rect.centerx - ks.get_width() // 2,
                   rect.centery - ks.get_height() // 2))


def key_hint_fonts(size: int = 16):
    return get_font('body', size, bold=True), get_font('body', size)


def _hints_width(pairs, kf, lf, gap, pad, inner):
    w = 0
    for item in pairs:
        k, lab = item[0], item[1]
        if k:
            w += kf.size(k)[0] + 2 * pad + (inner if lab else 0)
        w += lf.size(lab)[0] if lab else 0
    return w + gap * max(0, len(pairs) - 1)


def key_hints_height(size: int = 16) -> int:
    kf, _lf = key_hint_fonts(size)
    return max(kf.get_height() + ui_scale.px(8), ui_scale.px(24))


def draw_key_hints(surf: pygame.Surface, rect, hints, *, align: str = 'center',
                   sizes=(16, 15, 14), label_color: tuple | None = None) -> int:
    """Draw ``hints`` ((key, label[, label colour]) tuples, or a footer string) as
    ``[Key] Label`` units across ``rect`` (DESIGN_RULES 5.4), vertically
    centred. Units shrink (gaps, then font) to fit and are never split; a
    label that still cannot fit is ellipsized. Returns the drawn width."""
    S = ui_scale.px
    rect = pygame.Rect(rect)
    pairs = parse_key_hints(hints) if isinstance(hints, str) else list(hints)
    if not pairs:
        return 0
    pad, inner = S(7), S(8)
    total = 0
    for size in sizes:
        kf, lf = key_hint_fonts(size)
        for gap in (S(30), S(20), S(12)):
            total = _hints_width(pairs, kf, lf, gap, pad, inner)
            if total <= rect.w:
                break
        if total <= rect.w:
            break
    if total > rect.w:
        # Last resort: trim the longest labels with an ellipsis.
        budget = rect.w - _hints_width([(p[0], '') for p in pairs], kf, lf, gap, pad, inner)
        each = max(S(24), budget // max(1, len(pairs)))
        pairs = [(p[0], fit_text(p[1], lf, each)) + tuple(p[2:]) for p in pairs]
        total = _hints_width(pairs, kf, lf, gap, pad, inner)
    if align == 'left':
        x = rect.x
    elif align == 'right':
        x = rect.right - total
    else:
        x = rect.centerx - total // 2
    key_h = max(kf.get_height() + S(8), S(24))
    ky = rect.centery - key_h // 2
    lc = label_color or (KT.TEXT_HINT if kit_on() else FP.HINT_TEXT)
    for item in pairs:
        k, lab = item[0], item[1]
        col = (item[2] if len(item) > 2 and item[2] else None) or lc
        if k:
            kw = kf.size(k)[0] + 2 * pad
            draw_key_badge(surf, (x, ky, kw, key_h), k, kf)
            x += kw + (inner if lab else 0)
        if lab:
            ls = lf.render(lab, True, col)
            surf.blit(ls, (x, rect.centery - ls.get_height() // 2))
            x += ls.get_width()
        x += gap
    return total


def draw_icon(surf: pygame.Surface, name: str, rect) -> bool:
    """Blit kit icon ``name`` centred in ``rect``; False when not loaded."""
    return ui_theme.draw_icon(surf, name, rect)


def subject_icon(subject: str) -> str:
    return f"subject_{subject}"


# =============================================================================
# TEXT FITTING
# =============================================================================

_URL_RE = r'(?:https?://|www\.)[^\s;,)\]]*[^\s;,.)\]]'


# A bare web address ("britannica.com", "nps.gov/brca") with no http/www.
_BARE_DOMAIN = (r"\b[A-Za-z0-9][\w-]*(?:\.[\w-]+)*\."
                r"(?:com|org|edu|gov|net|int|io|info|uk|ch|fr|de|hu|br|au|ca|nz|ie"
                r"|it|es|nl|jp|us|in|za|mx|be)\b"
                r"(?:/[^\s;()]*[^\s;().,:])?")
# Addresses that ARE the content (a phishing look-alike to spot, a site a
# story is about), never a source line: these stay wherever they appear.
_CONTENT_DOMAINS = frozenset((
    'example.com', 'archive.org', 'paypa1.com', 'paypal.com', 'a16z.com',
    'match.com', 'change.org', 'toad.com', 'mises.org', 'bitcointalk.org',
    'freeross.org', 'metzdowd.com', 'saifhouse.com', 'bitcoin.org',
    'opensecrets.org', 'federalreserve.gov', 'coinop.org',
    'wtfhappenedin1971.com',
))
_WIKI = r"(?:Wikipedia|Grokipedia)"


def _is_content_domain(s: str) -> bool:
    import re
    s = s.strip().lower()
    if '/' in s:
        return False          # a page on the site is a source line
    m = re.match(r"[\w.-]+", s)
    host = m.group(0).rstrip('.') if m else ''
    return any(host == d or host.endswith('.' + d) for d in _CONTENT_DOMAINS)


def _strip_bare_citations(t: str) -> str:
    """Remove research citations written without http/www: a parenthesis or
    bracket that holds a bare address or a Wikipedia/Grokipedia reference,
    "; site.org" source tails, "via site.org", a lone "Wikipedia" source,
    and authoring notes such as "(Grokipedia checked first, returned HTTP
    403.)". Prose that mentions a site as part of the story ("Polybius first
    appeared on coinop.org", "from the EU, the UN, Wikipedia, and the web")
    is left alone."""
    import re
    if not re.search(_BARE_DOMAIN + '|' + _WIKI, t):
        return t
    orig = t
    # Authoring notes: "(Grokipedia checked first, returned HTTP 403.)".
    t = re.sub(r"\s*\(?\s*" + _WIKI + r"[^.()]*\bchecked first\b[^()]*?(?:\.\s*\)|\)|\.|$)", '', t)
    # A parenthesis or bracket (one level of nesting allowed) that cites.
    group = r"\((?:[^()]|\([^()]*\))*\)|\[(?:[^\[\]]|\[[^\[\]]*\])*\]"

    def _group(m):
        g = m.group(0)
        doms = re.findall(_BARE_DOMAIN, g)
        if any(_is_content_domain(d) for d in doms):
            return m.group(0)
        if doms or re.search(r"\b" + _WIKI + r"\b", g):
            return ''
        return m.group(0)
    t = re.sub(r"\s*(?:" + group + ")", _group, t)

    def _bare(m):
        return m.group(0) if _is_content_domain(m.group('d')) else m.group('lead')
    # "via site.org"
    t = re.sub(r"(?P<lead>)\s*\bvia\s+(?P<d>" + _BARE_DOMAIN + r")", _bare, t)
    # The rest of a source segment: words and further addresses, up to the
    # next ";" or the end of the sentence.
    tail = r"(?:" + _BARE_DOMAIN + r"|[^;.])*"
    # "; site.org Some Title"
    t = re.sub(r"(?P<lead>)\s*;\s*(?P<d>" + _BARE_DOMAIN + r")" + tail, _bare, t)
    # A source list opening a sentence: "rupress.org/jgp/...; UCSF news 2021."
    # (an address with a page, or one followed by more sources; a sentence
    # that merely starts with a site's name is prose and stays).
    def _opening(m):
        if '/' in m.group('d') or m.group(0).rstrip().endswith(';') \
                or re.fullmatch(r"(?:\s*(?:/|and)\s*" + _BARE_DOMAIN + r")*\s*", m.group('rest')):
            return _bare(m)
        return m.group(0)
    t = re.sub(r"(?P<lead>(?:^\s*|(?<=[.!?])\s+|(?<=[.!?]['\"’”)])\s+))(?P<d>"
               + _BARE_DOMAIN + r")(?P<rest>" + tail + r");?", _opening, t)
    # An address with a path is a source wherever it stands ("... and
    # en.wikipedia.org/wiki/X"); so is a host closing a source list
    # ("Ch. 6; and lawliberty.org.").
    t = re.sub(r"(?P<lead>)\s*(?:(?:and|or|&|/|,)\s+)?(?P<d>" + _BARE_DOMAIN + r")",
               lambda m: m.group(0) if ('/' not in m.group('d') or _is_content_domain(m.group('d')))
               else '', t)
    t = re.sub(r"(?P<lead>)\s*(?:;\s*)?\b(?:and|or|/)\s+(?P<d>" + _BARE_DOMAIN + r")(?=\s*(?:[.;)]|$))",
               _bare, t)
    # A citation sentence: "Wikipedia: Camelot; Wikipedia: Lancelot." or
    # "Wikipedia, Manannan mac Lir." just before a "(Legend.)" tag / the end.
    t = re.sub(r"(?:^|(?<=[.;!?])|(?<=[.!?]['\"’”)]))\s*" + _WIKI
               + r":\s[^.]*\.", '', t)
    t = re.sub(r"(?:(?<=[.;!?])|(?<=[.!?]['\"’”)]))\s*" + _WIKI
               + r",\s[^.,;:'\"]{1,60}\.(?=\s*(?:\(Legend\.\)|$))", '', t)
    # A dash-led source tail: "... years old. -- Wikipedia, 'Ambulocetus'."
    t = re.sub(r"\s*(?:—|–|--)\s*" + _WIKI + r"(?:\s*[:,]\s*'[^']*')?\s*(?:;[^.]*)?\.?\s*$", '', t)
    # A lone "Wikipedia" / "Grokipedia, 'Title'" source between separators.
    t = re.sub(r"(?:(?<=[.;:])|^)\s*" + _WIKI + r"(?:\s*[:,]\s*'[^']*')?\s*(?=[.;]|$)[.;]?", '', t)
    t = re.sub(r";\s*" + _WIKI + r"(?:\s*[:,]\s*'[^']*')?\s*(?=[.;)]|$)", '', t)
    if t == orig:
        return t
    # Tidy what the removals left behind.
    t = re.sub(r"\(\s*\)|\[\s*\]", '', t)
    t = re.sub(r"([.!?])\s*[;,]\s*", r"\1 ", t)
    t = re.sub(r"\s*;\s*(?=[.;)]|$)", '', t)
    t = re.sub(r"(?<!\.)\.\s+\.(?!\.)", '.', t)
    t = re.sub(r"[ \t]{2,}", ' ', t)
    t = re.sub(r"[ \t]+([.,;:)])", r"\1", t)
    return t.strip()


def strip_citations(text: str) -> str:
    """``text`` without its research citations: "Source: <url>" tails, URLs
    in parentheses, and bare URLs with their lead-in dash or semicolon. The
    question banks keep a source link at the end of most context blurbs
    (for the authors); a child reading the game never sees a raw URL or a
    "Source: ..." tail (VISUAL_REVIEW minor 8). Text with neither is
    returned unchanged."""
    import re
    t = str(text)
    if 'http' not in t and 'www.' not in t and 'Source' not in t:
        return _strip_bare_citations(t)
    t = re.sub(r'\s*\(?\b(?:Sources?|See|Ref(?:erence)?s?)\s*:?\s*' + _URL_RE + r'[^\n]*', '', t)
    t = re.sub(r'\s*\(?\bSources?\s*:[^\n]*', '', t)
    t = re.sub(r'\s*\([^()]*' + _URL_RE + r'[^()]*\)', '', t)
    t = re.sub(r'\s*(?:—|–|--|-|;|,)?\s*' + _URL_RE, '', t)
    t = re.sub(r'\(\s*\)', '', t)
    t = re.sub(r'\s*;\s*(?=[.;]|$)', '', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = re.sub(r'[ \t]+([.,;])', r'\1', t)
    return _strip_bare_citations(t.strip())


def display_text(text: str, sources: bool = False) -> str:
    """Typographic form of data text for the screen: an ASCII double hyphen
    becomes an em dash ("Prayer -- Lord" -> "Prayer — Lord"). With
    ``sources=True`` research citations are removed too (``strip_citations``;
    only for context blurbs: a question may quote a web address on purpose)."""
    import re
    t = str(text)
    if sources:
        t = strip_citations(t)
    if '--' in t:
        t = re.sub(r'(?<!-)\s*--\s*(?!-)', ' — ', t)
        t = re.sub(r'^ — ', '— ', t)
        t = re.sub(r' — $', ' —', t)
    return t


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
