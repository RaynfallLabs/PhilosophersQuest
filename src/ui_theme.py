"""ui_theme.py -- the UI art kit: optional painted art for menus and panels.

Every shared UI helper (``fantasy_ui.draw_dark_panel`` / ``draw_header_bar`` /
``draw_divider`` / ``draw_choice_button`` / ``draw_input_box`` /
``draw_overlay`` and the ``RenderMixin._ui_*`` kit in game_render.py) asks this
module first. If the art for that element is loaded, the kit draws it and the
helper returns; if not, the helper falls back to its procedural drawing, which
is exactly what the game drew before the kit existed. With ``assets/ui/`` empty
the game looks exactly as it does without this module.

Design rules (see _genart/ui/FOUNDATION_REVIEW.md and assets/ui/README.md):

* **Loaded once, at startup, never on first draw.** ``load()`` is called by
  ``main()`` right after the window is created. Draw functions never touch the
  disk, and the panel / quiz path never ``smoothscale``s: a stall in a draw
  call is subtracted from the combat quiz timer. (Two off-quiz exceptions:
  ``texture()`` and ``icon()`` scale a size not seen before once, then keep
  it in a small bounded cache.) If ``load()`` was never called the kit is
  simply empty and every helper falls back.
* **A bad manifest never crashes the game.** Every field is validated; a bad
  piece / icon is dropped (its helper draws procedurally) and ``load()``
  logs ONE warning listing everything it dropped. A manifest that is not a
  JSON object, or has a bad ``version`` / ``scale``, loads nothing.
* **Nine-slice from pre-scaled, tiled pieces; no size-keyed cache.** Each
  piece is cut into four corners, four edge strips and a centre at load time,
  scaled once to the UI scale, and the edge / centre strips are pre-repeated to
  at least ``_MIN_STRIP`` px so tiling needs few blits. Drawing a panel of ANY
  size is corners + tiled edge blits + a centre fill, so a quiz panel whose
  height changes every question costs the same as a fixed one, and a window
  resize within one UI-scale step invalidates nothing. A resize ACROSS a
  scale step (_genart/ui/SCALE_PLAN.md) re-cuts the pieces once, from the
  source images kept in memory since ``load()`` (``rescale``, run by the
  ui_scale listener inside ``layout.update``): no disk, never on a draw.
* **Untinted art + a separate accent layer.** Painted gold is never tinted.
  A piece may carry an ``accent`` image (greyscale, same geometry) that is
  multiplied by the caller's colour (the quiz subject colour, a lore blue...)
  and drawn on top. Tinted copies are cached per (piece, colour): a handful of
  colours, never per size.
* **Opaque panel bodies.** Panel-type pieces (``OPAQUE_BODY``) always get the
  body colour filled under their centre, so no text behind a panel bleeds
  through it (lead decision 2026-10-15).

The full-window overlay cache lives here too (``draw_overlay``): one surface
per (window size, colour, alpha), at most ``_OVERLAY_MAX`` of them and at most
``_OVERLAY_BUDGET`` bytes in all, keyed on the target surface's real size (not
the ``layout`` globals).
"""
from __future__ import annotations

import functools
import json
import logging
import os
from collections import OrderedDict

import pygame

from paths import data_path
import ui_scale as _ui_scale_mod

log = logging.getLogger(__name__)

ASSET_DIR = data_path('assets', 'ui')
MANIFEST_NAME = 'manifest.json'
MANIFEST_VERSION = 1

# Edge / centre strips are pre-repeated to at least this many px at load time,
# so a 1 px wide painted edge does not turn into a thousand blits.
_MIN_STRIP = 128

# Pieces whose centre is a panel body: always filled opaque underneath.
OPAQUE_BODY = frozenset({'panel', 'quiz', 'subpanel', 'card', 'input'})

# Every piece name the game asks for, and what it is. assets/ui/README.md
# documents the same list; tests check the two agree.
PIECES = {
    'panel':            'Modal / menu panel frame (draw_dark_panel).',
    'quiz':             'The quiz modal frame (draw_dark_panel kind="quiz").',
    'header':           'Header plaque inside a panel, inset by its band (draw_header_bar).',
    'header_small':     'Sidebar section header plaque, 24 px tall.',
    'divider':          'Horizontal divider, three-slice (draw_divider).',
    'subpanel':         'Inner box with its own label strip (_ui_subpanel).',
    'subpanel_header':  'The label strip at the top of a subpanel.',
    'card':             'Small flat box inside a panel (picker note, reward code, sheet cells).',
    'choice':           'Quiz answer card, idle.',
    'choice_selected':  'Quiz answer card, selected.',
    'choice_correct':   'Quiz answer card, revealed correct.',
    'choice_incorrect': 'Quiz answer card, the wrong pick.',
    'choice_badge':     'Key badge on the left of a quiz answer card.',
    'row':              'Option row (_ui_action_row), idle.',
    'row_selected':     'Option row, selected.',
    'key':              'Key-letter badge on an option row.',
    'chip':             'Tab chip, idle (_ui_chip).',
    'chip_active':      'Tab chip, active.',
    'input':            'Text entry box (draw_input_box).',
    'scroll_track':     'Scrollbar track, vertical (_ui_scrollbar).',
    'scroll_thumb':     'Scrollbar thumb, vertical.',
    'bar_track':        'Progress-bar track (_ui_progress_bar).',
    'bar_frame':        'Progress-bar frame drawn over the fill.',
}


# =============================================================================
# Full-window overlay (cached)
# =============================================================================

# Two surfaces at most, and never more than ~40 MB in all: one 3440x1440
# SRCALPHA wash is 19.8 MB, so four (the old cap) pinned ~79 MB during normal
# play (GROUNDWORK_REVIEW 5). A screen uses one or two washes; a third key
# re-fills the least-recently-used surface (one fill, no allocation). A
# window so big that even one wash is over budget still keeps that one.
_OVERLAY_MAX = 2
_OVERLAY_BUDGET = 40 * 1024 * 1024
_overlays: "OrderedDict[tuple, pygame.Surface]" = OrderedDict()


def overlay_cache_bytes() -> int:
    """Bytes held by the cached overlay surfaces."""
    return sum(o.get_width() * o.get_height() * o.get_bytesize() for o in _overlays.values())


def draw_overlay(surf: pygame.Surface, alpha: int = 185,
                 color: tuple = (0, 0, 0)) -> None:
    """Blend a flat translucent wash over the whole of ``surf``.

    Pixel-identical to building a fresh SRCALPHA surface each call (what the
    game did before), but the surface is kept: at most ``_OVERLAY_MAX`` per
    window size, LRU. An overlay whose alpha animates (the fullscreen
    takeover) re-fills the least-recently-used surface instead of allocating.
    """
    size = surf.get_size()
    if size[0] <= 0 or size[1] <= 0:
        return
    key = (size, tuple(int(c) for c in color[:3]), int(alpha))
    ov = _overlays.get(key)
    if ov is None:
        for k in [k for k in _overlays if k[0] != size]:
            del _overlays[k]                       # window was resized
        per = size[0] * size[1] * 4
        cap = max(1, min(_OVERLAY_MAX, _OVERLAY_BUDGET // per))
        while len(_overlays) > cap:
            _overlays.popitem(last=False)
        if len(_overlays) >= cap:
            _old, ov = _overlays.popitem(last=False)
        else:
            ov = pygame.Surface(size, pygame.SRCALPHA)
        ov.fill((*key[1], key[2]))
        _overlays[key] = ov
    else:
        _overlays.move_to_end(key)
    surf.blit(ov, (0, 0))


def clear_overlay_cache() -> None:
    _overlays.clear()


# =============================================================================
# Pieces
# =============================================================================

class Piece:
    """One nine-slice element, cut and scaled at load time.

    ``l, t, r, b`` are the border sizes in final (screen) px. Corners are
    ``tl tr bl br``; ``top bottom`` are horizontal strips (height t / b);
    ``left right`` vertical strips (width l / r); ``center`` the body tile.
    Any of them may be None when its size is 0 (a three-slice divider has no
    top or bottom row). At a manifest ``scale`` other than 1 use slice values
    that divide evenly (even numbers at scale 2): an odd inset rounds to a
    border one px off its corner image.
    """

    __slots__ = ('name', 'l', 't', 'r', 'b', 'tl', 'tr', 'bl', 'br',
                 'top', 'bottom', 'left', 'right', 'center', 'body',
                 'body_color', 'accent', 'ornament', 'src_size', 'band')

    def __init__(self, name):
        self.name = name
        self.l = self.t = self.r = self.b = 0
        self.tl = self.tr = self.bl = self.br = None
        self.top = self.bottom = self.left = self.right = None
        self.center = None
        self.body = 'tile'          # 'tile' | 'fill' | 'none'
        self.body_color = None      # RGB for 'fill' (or under a translucent tile)
        self.accent = None          # Piece: greyscale layer tinted at draw time
        self.ornament = None        # Surface centred on the piece (divider gem)
        self.src_size = (0, 0)
        self.band = 0               # frame band width (screen px): content sits inside it

    @property
    def min_w(self) -> int:
        return self.l + self.r

    @property
    def min_h(self) -> int:
        return self.t + self.b

    def fits(self, w: int, h: int) -> bool:
        return w >= self.min_w and h >= self.min_h and w > 0 and h > 0


def _repeat(surf: pygame.Surface, min_w: int, min_h: int) -> pygame.Surface:
    """``surf`` tiled into a strip at least ``min_w`` x ``min_h`` px."""
    w, h = surf.get_size()
    if w >= min_w and h >= min_h:
        return surf
    nx = max(1, -(-min_w // w))
    ny = max(1, -(-min_h // h))
    out = pygame.Surface((w * nx, h * ny), pygame.SRCALPHA)
    for iy in range(ny):
        for ix in range(nx):
            out.blit(surf, (ix * w, iy * h))
    return _convert(out, opaque_ok=True)


@functools.lru_cache(maxsize=256)
def _area_weights(n_in: int, n_out: int):
    """(n_out, n_in) matrix: each output pixel averages the input pixels it
    covers, weighted by the covered length (an exact box filter)."""
    import numpy as np
    scale = n_in / n_out
    w = np.zeros((n_out, n_in))
    for i in range(n_out):
        a, b = i * scale, (i + 1) * scale
        j0, j1 = int(a), min(n_in, int(np.ceil(b)))
        for j in range(j0, j1):
            w[i, j] = min(b, j + 1) - max(a, j)
        w[i] /= w[i].sum()
    return w


def _resample(surf: pygame.Surface, size) -> pygame.Surface:
    """``surf`` scaled to ``size`` for the kit (load time only).

    pygame-ce's ``smoothscale`` DOWNSCALES with a rounding bias: a flat
    (16, 19, 38, 255) comes out (14, 17, 36, 253) at 0.75. The kit's frame
    strips then no longer match the panel body filled between them (a seam
    at UI scale 1.25 / 1.5) and opaque art turns faintly translucent. So a
    downscale is an exact, alpha-premultiplied box filter (numpy); an
    upscale (no bias) or a missing numpy uses ``smoothscale``."""
    nw, nh = int(size[0]), int(size[1])
    w, h = surf.get_size()
    if (nw, nh) == (w, h):
        return surf.copy()
    if nw > w or nh > h:
        return pygame.transform.smoothscale(surf, (nw, nh))
    try:
        import numpy as np
    except ImportError:                                  # pragma: no cover
        return pygame.transform.smoothscale(surf, (nw, nh))
    src = surf
    if src.get_bitsize() != 32 or not (src.get_flags() & pygame.SRCALPHA):
        src = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        src.blit(surf, (0, 0))
    rgb = pygame.surfarray.array3d(src).astype(np.float64)        # (w, h, 3)
    a = pygame.surfarray.array_alpha(src).astype(np.float64)       # (w, h)
    pre = rgb * (a[..., None] / 255.0)
    wx, wy = _area_weights(w, nw), _area_weights(h, nh)

    def box(m):
        t = np.tensordot(wx, m, axes=(1, 0))                       # (nw, h, ...)
        return np.moveaxis(np.tensordot(t, wy, axes=(1, 1)), -1, 1)  # (nw, nh, ...)
    a2 = box(a)
    pre2 = box(pre)
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb2 = np.where(a2[..., None] > 0, pre2 * 255.0 / a2[..., None], 0.0)
    out = pygame.Surface((nw, nh), pygame.SRCALPHA, 32)
    px = pygame.surfarray.pixels3d(out)
    px[...] = np.clip(np.rint(rgb2), 0, 255).astype(np.uint8)
    del px
    pa = pygame.surfarray.pixels_alpha(out)
    pa[...] = np.clip(np.rint(a2), 0, 255).astype(np.uint8)
    del pa
    return out


def _fully_opaque(surf: pygame.Surface) -> bool:
    if not (surf.get_flags() & pygame.SRCALPHA):
        return True
    w, h = surf.get_size()
    return pygame.mask.from_surface(surf, 254).count() == w * h


def _convert(surf: pygame.Surface, opaque_ok: bool = False) -> pygame.Surface:
    """``convert_alpha`` when a display exists. Without one (tests, tools
    that load before ``set_mode``) the image is still made 32-bit, so an
    8-bit palette PNG can be ``smoothscale``d (GROUNDWORK_REVIEW 8).

    ``opaque_ok``: a slice with no transparent pixel at all is converted
    WITHOUT per-pixel alpha (pixel-identical, and a several times cheaper
    blit: the kit's frame strips are wide and fully opaque)."""
    if pygame.display.get_surface() is not None:
        try:
            if opaque_ok and _fully_opaque(surf):
                return surf.convert()
            return surf.convert_alpha()
        except pygame.error:
            pass
    if surf.get_bitsize() != 32 or not (surf.get_flags() & pygame.SRCALPHA):
        out = pygame.Surface(surf.get_size(), pygame.SRCALPHA, 32)
        out.blit(surf, (0, 0))
        return out
    return surf


def _cut(img: pygame.Surface, name: str, sl, factor: float,
         pixel_art: bool) -> Piece | None:
    """Cut ``img`` into a Piece with source insets ``sl`` (l, t, r, b),
    scaled by ``factor``. Returns None if the insets do not fit."""
    W, H = img.get_size()
    l, t, r, b = (int(v) for v in sl)  # noqa: E741 (left/top/right/bottom)
    if min(l, t, r, b) < 0 or l + r > W or t + b > H:
        return None
    cw, ch = W - l - r, H - t - b

    def region(x, y, w, h):
        if w <= 0 or h <= 0:
            return None
        sub = img.subsurface(pygame.Rect(x, y, w, h)).copy()
        if factor != 1.0:
            nw = max(1, round(w * factor))
            nh = max(1, round(h * factor))
            if pixel_art and factor >= 1.0 and float(factor).is_integer():
                sub = pygame.transform.scale(sub, (nw, nh))
            else:
                sub = _resample(sub, (nw, nh))
        return _convert(sub, opaque_ok=True)

    p = Piece(name)
    p.src_size = (W, H)
    p.l, p.t, p.r, p.b = (round(v * factor) for v in (l, t, r, b))
    p.tl = region(0, 0, l, t)
    p.tr = region(W - r, 0, r, t)
    p.bl = region(0, H - b, l, b)
    p.br = region(W - r, H - b, r, b)
    top = region(l, 0, cw, t)
    bottom = region(l, H - b, cw, b)
    left = region(0, t, l, ch)
    right = region(W - r, t, r, ch)
    center = region(l, t, cw, ch)
    p.top = _repeat(top, _MIN_STRIP, 1) if top else None
    p.bottom = _repeat(bottom, _MIN_STRIP, 1) if bottom else None
    p.left = _repeat(left, 1, _MIN_STRIP) if left else None
    p.right = _repeat(right, 1, _MIN_STRIP) if right else None
    p.center = _repeat(center, _MIN_STRIP, _MIN_STRIP) if center else None
    return p


# =============================================================================
# The kit
# =============================================================================

class Kit:
    """Everything loaded from one assets/ui folder."""

    def __init__(self):
        self.pieces: dict[str, Piece] = {}
        self.icons: dict[tuple[str, int], pygame.Surface] = {}
        self.icon_src: dict[str, pygame.Surface] = {}
        self.icon_pixel_art: set[str] = set()
        self.textures: dict[str, pygame.Surface] = {}
        self.errors: list[str] = []
        self.source: str | None = None
        self.factor = 1.0
        # For ``rescale``: the decoded source images (file -> Surface), the
        # folders, and whether this kit follows the UI scale (it does unless
        # ``load`` was given an explicit ``ui_scale``).
        self.images: dict[str, pygame.Surface] = {}
        self.texture_dir: str | None = None
        self.ui_scale: float = 1.0
        self.follows_scale = False


_kit: Kit = Kit()
_tinted: "OrderedDict[tuple, Piece]" = OrderedDict()
_TINT_MAX = 64


def kit() -> Kit:
    return _kit


def loaded_names() -> set[str]:
    return set(_kit.pieces)


def has(name: str) -> bool:
    return name in _kit.pieces


def save_state() -> Kit:
    """The current kit, for ``restore_state`` (tools and tests that load a
    kit temporarily, e.g. the capture harness, put the old one back)."""
    return _kit


def restore_state(state: Kit) -> None:
    """Put back a kit returned by ``save_state`` (derived caches dropped)."""
    global _kit
    _kit = state
    _tinted.clear()
    _scaled_textures.clear()
    _icon_extra.clear()


def unload() -> None:
    """Forget every piece (the game then draws procedurally)."""
    global _kit
    _kit = Kit()
    _tinted.clear()
    _scaled_textures.clear()
    _icon_extra.clear()


# Limits a manifest may not exceed (anything outside is dropped, not drawn).
_SCALE_MIN, _SCALE_MAX = 0.125, 8.0     # manifest "scale": art px per screen px
_MAX_IMAGE_PX = 4096                    # per side, after scaling to the UI scale
_ICON_SIZE_MAX = 512


class _Bad(ValueError):
    """One manifest entry is unusable; the message says why."""


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and v == v and v not in (float('inf'), float('-inf')))


def _rel_path(v, what: str) -> str:
    """A file name relative to the kit folder (no absolute paths, no ..)."""
    if not isinstance(v, str) or not v.strip():
        raise _Bad(f"{what} must be a file name (got {v!r})")
    norm = os.path.normpath(v)
    if os.path.isabs(norm) or os.path.splitdrive(norm)[0] or norm.split(os.sep)[0] == '..':
        raise _Bad(f"{what} {v!r} must be a path inside the kit folder")
    return v


def _slice4(v, name: str) -> tuple:
    if (not isinstance(v, (list, tuple)) or len(v) != 4
            or not all(_is_int(x) and x >= 0 for x in v)):
        raise _Bad(f"{name}: slice must be [left, top, right, bottom], four whole "
                   f"numbers >= 0 (got {v!r})")
    return tuple(v)


def _rgb(v, what: str) -> tuple:
    if (not isinstance(v, (list, tuple)) or len(v) < 3
            or not all(_is_int(x) and 0 <= x <= 255 for x in v[:3])):
        raise _Bad(f"{what} must be [r, g, b] with 0-255 values (got {v!r})")
    return tuple(v[:3])


def load(asset_dir: str | None = None, ui_scale: float | None = None,
         texture_dir: str | None = None) -> Kit:
    """Load the art kit from ``asset_dir`` (default ``assets/ui``).

    ``ui_scale`` (screen px per UI px) defaults to the game's current UI
    scale (``ui_scale.get()``), and the kit then FOLLOWS it: when the window
    is resized across a scale step, ``rescale`` re-cuts every piece from the
    source images kept in memory (SCALE_PLAN.md 5). An explicit ``ui_scale``
    pins the kit at that scale.

    Call once at startup, AFTER ``pygame.display.set_mode`` (so pieces can be
    ``convert_alpha``-ed). Never raises: a missing folder or manifest loads
    nothing; a bad field, missing / corrupt / oversized image or bad slice
    drops only that piece or icon (its helper draws procedurally); a manifest
    that is not a JSON object, or has a bad ``version`` / ``scale``, loads
    nothing. Every problem is kept in ``kit().errors`` and reported in ONE
    logged warning.
    """
    global _kit
    k = Kit()
    k.follows_scale = ui_scale is None
    if ui_scale is None:
        ui_scale = _ui_scale_mod.get()
    _tinted.clear()
    _scaled_textures.clear()
    _icon_extra.clear()
    try:
        _load_into(k, asset_dir, ui_scale, texture_dir)
    except Exception as e:                       # backstop: never crash the game
        k.pieces.clear()
        k.icons.clear()
        k.icon_src.clear()
        k.icon_pixel_art.clear()
        k.errors.append(f"art kit not loaded: {type(e).__name__}: {e}")
    if k.errors:
        log.warning("ui_theme: %d problem(s) in %s; the affected UI is drawn "
                    "procedurally:\n  %s", len(k.errors), k.source,
                    "\n  ".join(k.errors))
    _kit = k
    return k


def rescale(ui_scale: float) -> Kit:
    """Re-cut the loaded kit for a new UI scale, from the source images kept
    in memory since ``load`` (no disk access). Runs from the ui_scale
    listener, inside ``layout.update``: once per scale step, never on a draw.
    A kit that does not follow the scale, or is already at it, is left alone."""
    global _kit
    old = _kit
    if not old.follows_scale or not old.source or ui_scale == old.ui_scale:
        return old
    k = Kit()
    k.follows_scale = True
    k.textures = old.textures
    _tinted.clear()
    _scaled_textures.clear()
    _icon_extra.clear()
    try:
        _load_into(k, old.source, ui_scale, old.texture_dir, images=old.images,
                   textures=False)
    except Exception as e:                       # backstop, as in load()
        k.pieces.clear()
        k.icons.clear()
        k.errors.append(f"art kit not rescaled: {type(e).__name__}: {e}")
    if k.errors and k.errors != old.errors:
        log.warning("ui_theme: %d problem(s) rescaling %s:\n  %s",
                    len(k.errors), k.source, "\n  ".join(k.errors))
    _kit = k
    return k


def _on_ui_scale(new_scale: float) -> None:
    rescale(new_scale)


def _load_into(k: Kit, asset_dir, ui_scale, texture_dir, images=None,
               textures=True) -> None:
    k.ui_scale = ui_scale if _is_num(ui_scale) else 1.0
    k.texture_dir = texture_dir
    if images is not None:
        k.images = images
    if textures:
        try:
            _load_textures(k, texture_dir)
        except Exception as e:
            k.textures.clear()
            k.errors.append(f"textures not loaded: {type(e).__name__}: {e}")
    folder = asset_dir or ASSET_DIR
    k.source = folder
    mpath = os.path.join(folder, MANIFEST_NAME)
    if images is not None and MANIFEST_NAME in images:
        manifest = images[MANIFEST_NAME]
    else:
        if not os.path.isfile(mpath):
            return
        try:
            with open(mpath, encoding='utf-8') as f:
                manifest = json.load(f)
        except (OSError, ValueError) as e:
            k.errors.append(f"manifest unreadable: {e}")
            return
        k.images[MANIFEST_NAME] = manifest
    if not isinstance(manifest, dict):
        k.errors.append(f"manifest must be a JSON object, not {type(manifest).__name__}")
        return
    version = manifest.get('version', MANIFEST_VERSION)
    if not _is_int(version) or version != MANIFEST_VERSION:
        k.errors.append(f"manifest version {version!r} != {MANIFEST_VERSION}")
        return
    art_scale = manifest.get('scale', 1)
    if not _is_num(art_scale) or not (_SCALE_MIN <= art_scale <= _SCALE_MAX):
        k.errors.append(f"manifest scale {art_scale!r} must be a number from "
                        f"{_SCALE_MIN} to {_SCALE_MAX}")
        return
    if not _is_num(ui_scale) or ui_scale <= 0:
        k.errors.append(f"ui_scale {ui_scale!r} must be a positive number")
        return
    factor = float(ui_scale) / float(art_scale)
    k.factor = factor
    pixel_art_default = manifest.get('pixel_art', False)
    if not isinstance(pixel_art_default, bool):
        k.errors.append(f"pixel_art must be true or false (got {pixel_art_default!r})")
        pixel_art_default = False

    def load_img(rel, what):
        rel = _rel_path(rel, what)
        img = k.images.get(rel)
        if img is None:
            path = os.path.join(folder, rel)
            if not os.path.isfile(path):
                raise _Bad(f"missing file {rel}")
            try:
                img = pygame.image.load(path)
            except Exception as e:               # corrupt / not an image
                raise _Bad(f"cannot load {rel}: {e}") from None
            img = _convert(img)
            k.images[rel] = img                  # kept for rescale()
        w, h = img.get_size()
        if w <= 0 or h <= 0:
            raise _Bad(f"{rel} is empty")
        if max(w, h) * max(factor, 1.0) > _MAX_IMAGE_PX:
            raise _Bad(f"{rel} is {w}x{h}; at most {_MAX_IMAGE_PX} px a side on screen")
        return img

    pieces = manifest.get('pieces', {})
    if pieces is None:
        pieces = {}
    if not isinstance(pieces, dict):
        k.errors.append(f"pieces must be an object of name: spec (got {type(pieces).__name__})")
        pieces = {}
    for name, spec in pieces.items():
        try:
            k.pieces[name] = _load_piece(k, name, spec, factor, pixel_art_default, load_img)
        except _Bad as e:
            k.errors.append(str(e))
        except Exception as e:                   # anything unforeseen: drop the piece
            k.errors.append(f"{name}: {type(e).__name__}: {e}")

    icons = manifest.get('icons', {})
    if icons is None:
        icons = {}
    if not isinstance(icons, dict):
        k.errors.append("icons must be an object with 'sizes' and 'files'")
        icons = {}
    raw_sizes = icons.get('sizes', [])
    if raw_sizes is None:
        raw_sizes = []
    if not isinstance(raw_sizes, list):
        k.errors.append(f"icons.sizes must be a list (got {raw_sizes!r})")
        raw_sizes = []
    sizes = []
    for sz in raw_sizes:
        if _is_int(sz) and 1 <= sz <= _ICON_SIZE_MAX:
            sizes.append(sz)
        else:
            k.errors.append(f"icon size {sz!r} must be a whole number from 1 to {_ICON_SIZE_MAX}")
    files = icons.get('files', {})
    if files is None:
        files = {}
    if not isinstance(files, dict):
        k.errors.append("icons.files must be an object of name: file")
        files = {}
    for name, rel in files.items():
        try:
            img = load_img(rel, f"icon {name!r}")
            pixel = max(img.get_size()) <= 64
            # Manifest sizes are UI px: pre-fit at their screen size now.
            fitted = {int(sz * k.ui_scale + 0.5): None for sz in sizes}
            fitted = {sz: _fit_icon(img, sz, pixel) for sz in fitted}
        except _Bad as e:
            k.errors.append(str(e))
            continue
        except Exception as e:
            k.errors.append(f"icon {name!r}: {type(e).__name__}: {e}")
            continue
        k.icon_src[name] = img
        if pixel:
            k.icon_pixel_art.add(name)
        for s, surf in fitted.items():
            k.icons[(name, s)] = surf


def _load_piece(k: Kit, name, spec, factor, pixel_art_default, load_img) -> Piece:
    """One validated piece, or raise _Bad. Optional parts (body colour,
    accent, ornament) that are bad are reported and left off; the frame
    itself still loads."""
    if not isinstance(name, str) or name not in PIECES:
        raise _Bad(f"unknown piece {name!r} (see ui_theme.PIECES)")
    if not isinstance(spec, dict):
        raise _Bad(f"{name}: spec must be an object like "
                   f"{{\"file\": \"{name}.png\", \"slice\": [l, t, r, b]}}")
    img = load_img(spec.get('file', f'{name}.png'), f"{name}: file")
    sl = _slice4(spec.get('slice', [0, 0, 0, 0]), name)
    pixel_art = spec.get('pixel_art', pixel_art_default)
    if not isinstance(pixel_art, bool):
        k.errors.append(f"{name}: pixel_art must be true or false (got {pixel_art!r})")
        pixel_art = pixel_art_default
    piece = _cut(img, name, sl, factor, pixel_art)
    if piece is None:
        raise _Bad(f"{name}: slice {list(sl)} does not fit the "
                   f"{img.get_width()}x{img.get_height()} image")
    if 'band' in spec:
        band = spec['band']
        if _is_int(band) and band >= 0 and 2 * band <= min(img.get_size()):
            piece.band = round(band * factor)
        else:
            k.errors.append(f"{name}: band must be a whole number >= 0 that fits the "
                            f"image (got {band!r})")
    body = spec.get('body', 'tile')
    if body not in ('tile', 'fill', 'none'):
        k.errors.append(f"{name}: body must be tile, fill or none (got {body!r})")
        body = 'tile'
    piece.body = body
    if 'body_color' in spec:
        try:
            piece.body_color = _rgb(spec['body_color'], f"{name}: body_color")
        except _Bad as e:
            k.errors.append(str(e))
    acc = spec.get('accent')
    if acc:
        try:
            acc_img = load_img(acc, f"{name}: accent")
            if acc_img.get_size() != img.get_size():
                raise _Bad(f"{name}: accent must be the same size as the frame")
            piece.accent = _cut(acc_img, name + ':accent', sl, factor, pixel_art)
        except _Bad as e:
            k.errors.append(str(e))
    orn = spec.get('ornament')
    if orn:
        try:
            o = load_img(orn, f"{name}: ornament")
            if factor != 1.0:
                ow, oh = o.get_size()
                o = _convert(_resample(
                    o, (max(1, round(ow * factor)), max(1, round(oh * factor)))))
            piece.ornament = o
        except _Bad as e:
            k.errors.append(str(e))
    return piece


def _load_textures(k: Kit, texture_dir: str | None) -> None:
    """Optional full-panel textures. Today only the parchment behind the
    welcome screen's name box (``draw_panel(bg=True)``)."""
    paths = {'parchment': data_path('assets', 'textures', 'parchment.png')}
    if texture_dir is not None:
        paths = {n: os.path.join(texture_dir, os.path.basename(p)) for n, p in paths.items()}
    for name, path in paths.items():
        if not os.path.isfile(path):
            continue
        try:
            k.textures[name] = _convert(pygame.image.load(path))
        except Exception as e:
            k.errors.append(f"cannot load texture {path}: {e}")


_TEXTURE_MAX = 8
_scaled_textures: "OrderedDict[tuple, pygame.Surface]" = OrderedDict()


def texture(name: str, w: int, h: int, alpha: int = 255) -> pygame.Surface | None:
    """Loaded texture ``name`` scaled to (w, h) with ``alpha``; None if absent.

    The file is read once by ``load()``. Each size is scaled once and kept
    (bounded LRU): the texture panels are fixed-size boxes."""
    src = _kit.textures.get(name)
    if src is None or w <= 0 or h <= 0:
        return None
    key = (name, w, h, alpha)
    got = _scaled_textures.get(key)
    if got is None:
        got = pygame.transform.smoothscale(src, (w, h))
        got.set_alpha(alpha)
        _scaled_textures[key] = got
        if len(_scaled_textures) > _TEXTURE_MAX:
            _scaled_textures.popitem(last=False)
    else:
        _scaled_textures.move_to_end(key)
    return got


def _fit_icon(img: pygame.Surface, size: int, pixel_art: bool) -> pygame.Surface:
    """Scale an icon into a size x size box, aspect kept. Pixel-art sources
    are integer-upscaled first (the same rule as renderer.fit_sprite)."""
    w, h = img.get_size()
    scale = size / max(w, h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    if pixel_art and scale >= 2:
        k = int(scale)
        img = pygame.transform.scale(img, (w * k, h * k))
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    scaled = _resample(img, (nw, nh))
    out.blit(scaled, ((size - nw) // 2, (size - nh) // 2))
    return _convert(out)


# =============================================================================
# Drawing
# =============================================================================

def _tile_h(surf, strip, x0, x1, y):
    """Tile a horizontal strip from x0 to x1 at y."""
    sw = strip.get_width()
    sh = strip.get_height()
    x = x0
    while x < x1:
        w = min(sw, x1 - x)
        surf.blit(strip, (x, y), (0, 0, w, sh))
        x += w


def _tile_v(surf, strip, y0, y1, x):
    sw = strip.get_width()
    sh = strip.get_height()
    y = y0
    while y < y1:
        h = min(sh, y1 - y)
        surf.blit(strip, (x, y), (0, 0, sw, h))
        y += h


def _tile_area(surf, tile, rect):
    tw, th = tile.get_size()
    y = rect.y
    while y < rect.bottom:
        h = min(th, rect.bottom - y)
        x = rect.x
        while x < rect.right:
            w = min(tw, rect.right - x)
            surf.blit(tile, (x, y), (0, 0, w, h))
            x += w
        y += h


def _tinted_piece(p: Piece, color) -> Piece:
    """A copy of accent piece ``p`` multiplied by ``color`` (cached)."""
    key = (id(p), tuple(int(c) for c in color[:3]))
    got = _tinted.get(key)
    if got is not None:
        _tinted.move_to_end(key)
        return got
    q = Piece(p.name + ':tint')
    for attr in ('l', 't', 'r', 'b', 'body', 'body_color', 'src_size'):
        setattr(q, attr, getattr(p, attr))
    mul = (*key[1], 255)
    for attr in ('tl', 'tr', 'bl', 'br', 'top', 'bottom', 'left', 'right', 'center'):
        s = getattr(p, attr)
        if s is not None:
            s = s.copy()
            s.fill(mul, special_flags=pygame.BLEND_RGBA_MULT)
        setattr(q, attr, s)
    _tinted[key] = q
    if len(_tinted) > _TINT_MAX:
        _tinted.popitem(last=False)
    return q


def _draw_body(surf, p: Piece, rect: pygame.Rect, body_color, opaque: bool):
    inner = pygame.Rect(rect.x + p.l, rect.y + p.t,
                        rect.w - p.l - p.r, rect.h - p.t - p.b)
    if inner.w <= 0 or inner.h <= 0:
        return
    color = p.body_color or body_color
    if p.body == 'fill' or (opaque and color is not None):
        if color is not None:
            surf.fill(color, inner)
    if p.body == 'tile' and p.center is not None:
        _tile_area(surf, p.center, inner)


def _draw_frame(surf, p: Piece, rect: pygame.Rect):
    x, y, w, h = rect
    if p.top is not None:
        _tile_h(surf, p.top, x + p.l, x + w - p.r, y)
    if p.bottom is not None:
        _tile_h(surf, p.bottom, x + p.l, x + w - p.r, y + h - p.b)
    if p.left is not None:
        _tile_v(surf, p.left, y + p.t, y + h - p.b, x)
    if p.right is not None:
        _tile_v(surf, p.right, y + p.t, y + h - p.b, x + w - p.r)
    if p.tl is not None:
        surf.blit(p.tl, (x, y))
    if p.tr is not None:
        surf.blit(p.tr, (x + w - p.r, y))
    if p.bl is not None:
        surf.blit(p.bl, (x, y + h - p.b))
    if p.br is not None:
        surf.blit(p.br, (x + w - p.r, y + h - p.b))


def draw_piece(surf: pygame.Surface, name: str, rect, *, accent=None,
               body_color=None, frame: bool = True, body: bool = True,
               clip=None) -> bool:
    """Draw art piece ``name`` into ``rect``. Returns False (drawing nothing)
    if the piece is not loaded or ``rect`` is smaller than its corners, so
    the caller can fall back to its procedural drawing.

    ``accent``: colour multiplied into the piece's accent layer (if it has
    one). ``body_color``: the colour filled under the centre of an opaque
    piece (or a ``body: fill`` piece without its own colour). ``frame`` /
    ``body`` select the parts to draw (a header repaints only the frame of the
    panel it sits in). ``clip``: draw only inside this rect.
    """
    p = _kit.pieces.get(name)
    if p is None:
        return False
    rect = pygame.Rect(rect)
    if not p.fits(rect.w, rect.h):
        return False
    old_clip = None
    if clip is not None:
        old_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(clip).clip(old_clip))
    try:
        if body:
            _draw_body(surf, p, rect, body_color, name in OPAQUE_BODY)
        if frame:
            _draw_frame(surf, p, rect)
        if p.accent is not None and accent is not None:
            a = _tinted_piece(p.accent, accent)
            if body and a.center is not None and a.body == 'tile':
                inner = pygame.Rect(rect.x + a.l, rect.y + a.t,
                                    rect.w - a.l - a.r, rect.h - a.t - a.b)
                if inner.w > 0 and inner.h > 0:
                    _tile_area(surf, a.center, inner)
            if frame:
                _draw_frame(surf, a, rect)
        if p.ornament is not None and frame:
            o = p.ornament
            surf.blit(o, (rect.centerx - o.get_width() // 2,
                          rect.centery - o.get_height() // 2))
    finally:
        if old_clip is not None:
            surf.set_clip(old_clip)
    return True


def band(name: str, rect=None) -> int:
    """Width in screen px of the frame band of art piece ``name`` (its
    manifest ``band``): the strip a header plaque and all content sit inside.
    0 when the piece is not loaded, has no band, or would not be drawn as
    art for ``rect`` (a box smaller than its corners falls back to the
    procedural frame, which has no band)."""
    p = _kit.pieces.get(name)
    if p is None or not p.band:
        return 0
    if rect is not None:
        rect = pygame.Rect(rect)
        if not p.fits(rect.w, rect.h):
            return 0
    return p.band


def fits(name: str, w: int, h: int) -> bool:
    """True if piece ``name`` is loaded and would draw as art at w x h."""
    p = _kit.pieces.get(name)
    return p is not None and p.fits(w, h)


def draw_hbar(surf: pygame.Surface, name: str, x: int, cy: int, w: int,
              accent=None) -> bool:
    """Draw a horizontal three-slice piece (a divider) of width ``w`` at the
    art's own height, centred vertically on ``cy``. False if not loaded or
    narrower than its two end caps."""
    p = _kit.pieces.get(name)
    if p is None:
        return False
    h = max(1, round(p.src_size[1] * _kit.factor))
    if w < p.min_w:
        return False
    return draw_piece(surf, name, (x, cy - h // 2, w, h), accent=accent)


_ICON_EXTRA_MAX = 32
_icon_extra: "OrderedDict[tuple, pygame.Surface]" = OrderedDict()


def icon(name: str, size: int) -> pygame.Surface | None:
    """A loaded icon, fitted into size x size. Sizes listed in the manifest
    are pre-scaled at load; any other size is scaled once and kept in a
    small LRU (``_ICON_EXTRA_MAX``). None if not loaded or size < 1."""
    got = _kit.icons.get((name, size))
    if got is not None:
        return got
    src = _kit.icon_src.get(name)
    if src is None or size < 1 or size > _ICON_SIZE_MAX:
        return None
    key = (id(_kit), name, size)
    got = _icon_extra.get(key)
    if got is None:
        got = _fit_icon(src, size, name in _kit.icon_pixel_art)
        _icon_extra[key] = got
        while len(_icon_extra) > _ICON_EXTRA_MAX:
            _icon_extra.popitem(last=False)
    else:
        _icon_extra.move_to_end(key)
    return got


def draw_icon(surf: pygame.Surface, name: str, rect) -> bool:
    """Blit icon ``name`` centred in ``rect``. False if not loaded."""
    rect = pygame.Rect(rect)
    img = icon(name, min(rect.w, rect.h))
    if img is None:
        return False
    surf.blit(img, (rect.centerx - img.get_width() // 2,
                    rect.centery - img.get_height() // 2))
    return True


_ui_scale_mod.add_listener(_on_ui_scale)


def hbar_reach(name: str) -> int:
    """How far (screen px) a three-slice piece drawn by ``draw_hbar`` reaches
    above and below its centre line: half the taller of the bar and its
    centre ornament. 0 when the piece is not loaded."""
    p = _kit.pieces.get(name)
    if p is None:
        return 0
    h = max(1, round(p.src_size[1] * _kit.factor))
    if p.ornament is not None:
        h = max(h, p.ornament.get_height())
    return (h + 1) // 2
