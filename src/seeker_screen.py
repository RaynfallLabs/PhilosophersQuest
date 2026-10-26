"""seeker_screen.py -- the Seeker Profile screen (title screen, F4), the
achievement badges, and the "Achievement Unlocked" card
(PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md sections 5 and 11).

A Seeker is the real child playing; a hero is who he or she plays this run.
This screen shows one Seeker's achievements across every run: a badge grid
per category, the chosen badge's page with its Reward Code for Dad, and the
"Who Is Playing?" view where the Seeker is chosen. Keyboard only (the game
has no mouse).

Badges (``badge_surface``): ``assets/achievements/<art>.png`` when it exists,
otherwise a medallion drawn in code in the rarity's colour with the
category's emblem, so every screen works before the art is in. A badge not
yet won is greyscale and darkened, and carries a padlock (DESIGN_RULES 2.5:
state is never colour alone). Badges are built once per (art, size, state)
and kept in a bounded cache; the screens prebuild a tab's badges when it
opens, so a frame never loads or scales art.

The module imports the fantasy_ui drawing helpers inside its functions: the
UI capture harness watches ``fantasy_ui.draw_dark_panel`` for panels.
"""
from __future__ import annotations

import math
import os
import sys
from collections import OrderedDict

import pygame

from ui_scale import px as S

# -- badges ---------------------------------------------------------------

GRID_BADGE = 64            # UI px at scale 1: the gallery grid
DETAIL_BADGE = 128         # the badge's own page, the unlock card and popup
LIST_BADGE = 44            # an Encyclopedia list row

RAW_MAX = 8                # source PNGs kept (least recently used goes first)
BADGES_MAX = 96            # finished badges kept: two sizes of the largest tab, and room
_raw: OrderedDict = OrderedDict()       # path -> Surface | None (None: no file)
_badges: OrderedDict = OrderedDict()    # (art id, px, earned) -> Surface

# Tests point this at a folder of their own; None is assets/achievements.
ART_DIR: str | None = None

RARITY_NAMES = {'common': 'Common', 'rare': 'Rare', 'epic': 'Epic', 'legendary': 'Legendary'}

LOCK_TINT = (150, 150, 160)   # multiplied into a greyscale badge: darker, a little cool


def art_dir() -> str:
    if ART_DIR is not None:
        return ART_DIR
    from paths import data_path
    return data_path('assets', 'achievements')


def rarity_color(rarity: str) -> tuple:
    from fantasy_ui import FP
    return {'common': FP.RARITY_COMMON, 'rare': FP.RARITY_RARE, 'epic': FP.RARITY_EPIC,
            'legendary': FP.RARITY_LEGENDARY}.get(rarity, FP.RARITY_COMMON)


def _remember(cache: OrderedDict, key, value, cap: int):
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > cap:
        cache.popitem(last=False)
    return value


def _entry_for_art(art_id: str) -> dict | None:
    """The achievement whose badge is ``art_id`` (for the fallback's colour
    and emblem)."""
    try:
        import achievements
        book = achievements.load()
    except Exception:
        return None
    idx = getattr(book, '_seeker_art_index', None)
    if idx is None:
        idx = {a.get('art'): a for a in book.entries}
        book._seeker_art_index = idx
    return idx.get(art_id)


def _load_raw(art_id: str):
    path = os.path.join(art_dir(), f'{art_id}.png')
    if path in _raw:
        _raw.move_to_end(path)
        return _raw[path]
    surf = None
    if os.path.isfile(path):
        try:
            surf = pygame.image.load(path)
            try:
                surf = surf.convert_alpha()
            except pygame.error:        # no display yet (a test): keep it as read
                pass
        except (pygame.error, OSError):
            surf = None
    return _remember(_raw, path, surf, RAW_MAX)


def has_art(art_id: str) -> bool:
    """True when the badge's own PNG is installed (else the medallion)."""
    return _load_raw(art_id) is not None


def badge_surface(art_id, px, earned, *, rarity=None, category=None) -> pygame.Surface:
    """The badge ``art_id`` at ``px`` square: full colour when ``earned``,
    greyscale, darkened and padlocked when not. Cached (bounded)."""
    px = max(8, int(px))
    key = (str(art_id), px, bool(earned))
    got = _badges.get(key)
    if got is not None:
        _badges.move_to_end(key)
        return got
    a = _entry_for_art(str(art_id)) or {}
    rarity = rarity or a.get('rarity', 'common')
    category = category or a.get('category', '')
    raw = _load_raw(str(art_id))
    if raw is not None:
        from renderer import fit_sprite
        surf = pygame.Surface((px, px), pygame.SRCALPHA)
        surf.blit(fit_sprite(raw, px, px), (0, 0))
        # The rarity ring (bronze, silver, gold, violet) round the painted
        # vignette: the art is only the scene, the game draws the frame.
        ring = max(2, px // 22)
        c = px // 2
        pygame.draw.circle(surf, (12, 10, 20), (c, c), c - 1, ring + 2)
        pygame.draw.circle(surf, rarity_color(rarity), (c, c), c - 2, ring)
    else:
        surf = medallion(px, rarity, category)
    if not earned:
        surf = _locked(surf)
    return _remember(_badges, key, surf, BADGES_MAX)


def prebuild(items, px) -> None:
    """Build every (art id, earned) badge of ``items`` at ``px`` now, so the
    frames that show them only blit (call when a screen or tab opens)."""
    for art_id, earned in items:
        badge_surface(art_id, px, earned)


def clear_cache():
    _raw.clear()
    _badges.clear()


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


_DARK = (10, 10, 22)
_WHITE = (255, 255, 255)


def medallion(px: int, rarity: str, category: str) -> pygame.Surface:
    """The code-made badge: a disc in the rarity's colour (bronze, silver,
    gold, violet) with a studded rim and the category's emblem. Drawn at
    twice the size and smoothed down, so its edges are clean."""
    big = max(64, px * 2)
    s = pygame.Surface((big, big), pygame.SRCALPHA)
    c = rarity_color(rarity)
    cx = cy = big / 2
    r = big / 2 - 2
    rim = max(3, int(big / 13))
    pygame.draw.circle(s, _mix(c, _DARK, 0.45), (cx, cy), r)
    pygame.draw.circle(s, _mix(c, _DARK, 0.80), (cx, cy), r - rim)
    pygame.draw.circle(s, _mix(c, _DARK, 0.70), (cx, cy - r * 0.10), (r - rim) * 0.86)
    pygame.draw.circle(s, c, (cx, cy), r, max(2, rim // 2))
    pygame.draw.circle(s, _mix(c, _WHITE, 0.15), (cx, cy), r - rim, max(1, big // 96))
    stud = max(1.5, rim * 0.28)
    for i in range(16):
        ang = math.tau * i / 16
        rr = r - rim / 2
        pygame.draw.circle(s, _mix(c, _WHITE, 0.35), (cx + rr * math.cos(ang), cy + rr * math.sin(ang)), stud)
    _emblem(s, category, (cx, cy), (r - rim) * 0.58, _mix(c, _WHITE, 0.18), _mix(c, _DARK, 0.55))
    return pygame.transform.smoothscale(s, (px, px))


def _emblem(s, category, centre, g, fill, edge):
    """The category's emblem, in unit coordinates scaled by ``g``."""
    cx, cy = centre
    lw = max(1, int(g * 0.07))

    def P(pts):
        return [(cx + x * g, cy + y * g) for x, y in pts]

    def poly(pts, col=fill):
        pts = P(pts)
        pygame.draw.polygon(s, col, pts)
        pygame.draw.polygon(s, edge, pts, lw)

    def disc(x, y, rr, col=fill):
        pygame.draw.circle(s, col, (cx + x * g, cy + y * g), rr * g)
        pygame.draw.circle(s, edge, (cx + x * g, cy + y * g), rr * g, lw)

    def line(a, b, col=edge, w=lw):
        pygame.draw.line(s, col, P([a])[0], P([b])[0], w)

    if category == 'scholar':                      # an open book
        poly([(-0.95, -0.55), (-0.05, -0.38), (-0.05, 0.68), (-0.95, 0.5)])
        poly([(0.95, -0.55), (0.05, -0.38), (0.05, 0.68), (0.95, 0.5)])
        for k in range(3):
            y = -0.22 + k * 0.25
            line((-0.78, y - 0.05), (-0.22, y + 0.05))
            line((0.78, y - 0.05), (0.22, y + 0.05))
    elif category == 'warrior':                    # crossed swords
        for sx in (-1, 1):
            poly([(sx * -0.62, -0.78), (sx * -0.48, -0.86), (sx * 0.52, 0.32), (sx * 0.38, 0.42)])
            poly([(sx * 0.2, 0.36), (sx * 0.52, 0.04), (sx * 0.62, 0.14), (sx * 0.3, 0.46)])
            disc(sx * 0.66, 0.66, 0.12)
            line((sx * 0.45, 0.39), (sx * 0.62, 0.6), fill, max(2, int(g * 0.12)))
    elif category == 'depths':                     # stairs going down
        poly([(-0.9, -0.75), (-0.4, -0.75), (-0.4, -0.28), (0.1, -0.28), (0.1, 0.18),
              (0.6, 0.18), (0.6, 0.64), (0.9, 0.64), (0.9, 0.82), (-0.9, 0.82)])
    elif category == 'bosses':                     # a crown
        poly([(-0.85, 0.45), (-0.85, -0.4), (-0.42, 0.02), (0.0, -0.7), (0.42, 0.02),
              (0.85, -0.4), (0.85, 0.45)])
        poly([(-0.85, 0.45), (0.85, 0.45), (0.85, 0.7), (-0.85, 0.7)])
        for x in (-0.45, 0.0, 0.45):
            disc(x, 0.575, 0.09, edge)
    elif category == 'endings':                    # the Stone
        poly([(0.8 * math.cos(math.tau * k / 8 + math.pi / 8),
               0.8 * math.sin(math.tau * k / 8 + math.pi / 8)) for k in range(8)])
        poly([(0.38 * math.cos(math.tau * k / 8), 0.38 * math.sin(math.tau * k / 8))
              for k in range(8)], _mix(fill, _WHITE, 0.45))
    elif category == 'lore':                       # a scroll
        poly([(-0.55, -0.6), (0.55, -0.6), (0.55, 0.6), (-0.55, 0.6)])
        for y in (-0.62, 0.62):
            poly([(-0.75, y - 0.14), (0.75, y - 0.14), (0.75, y + 0.14), (-0.75, y + 0.14)])
        for k in range(3):
            line((-0.35, -0.25 + k * 0.25), (0.35, -0.25 + k * 0.25))
    elif category == 'craft':                      # a cauldron
        poly([(-0.8, -0.3), (0.8, -0.3), (0.7, 0.3), (0.4, 0.62), (-0.4, 0.62), (-0.7, 0.3)])
        poly([(-0.92, -0.42), (0.92, -0.42), (0.92, -0.26), (-0.92, -0.26)])
        for x in (-0.25, 0.1, 0.4):
            disc(x, -0.68, 0.1)
    elif category == 'companions':                 # a paw
        disc(0.0, 0.3, 0.4)
        for x, y in ((-0.6, -0.15), (-0.22, -0.55), (0.22, -0.55), (0.6, -0.15)):
            disc(x, y, 0.18)
    elif category == 'heroes':                     # a shield
        poly([(-0.72, -0.78), (0.72, -0.78), (0.72, 0.02), (0.0, 0.86), (-0.72, 0.02)])
        line((0.0, -0.62), (0.0, 0.6), edge, max(2, int(g * 0.1)))
        line((-0.55, -0.22), (0.55, -0.22), edge, max(2, int(g * 0.1)))
    elif category == 'character':                  # a heart
        heart = []
        for k in range(48):
            t = math.tau * k / 48
            heart.append((0.055 * 16 * math.sin(t) ** 3,
                          -0.055 * (13 * math.cos(t) - 5 * math.cos(2 * t)
                                    - 2 * math.cos(3 * t) - math.cos(4 * t)) - 0.05))
        poly(heart)
    elif category == 'journeys':                   # a compass rose
        poly([(0, -0.92), (0.2, -0.2), (0.92, 0), (0.2, 0.2), (0, 0.92), (-0.2, 0.2),
              (-0.92, 0), (-0.2, -0.2)])
        disc(0, 0, 0.16, edge)
    elif category == 'secrets':                    # a keyhole on a plate
        disc(0, 0, 0.82)
        disc(0, -0.2, 0.26, edge)
        poly([(-0.12, -0.05), (0.12, -0.05), (0.26, 0.56), (-0.26, 0.56)], edge)
    else:                                          # a star
        poly([((0.9 if k % 2 == 0 else 0.38) * math.cos(math.tau * k / 10 - math.pi / 2),
               (0.9 if k % 2 == 0 else 0.38) * math.sin(math.tau * k / 10 - math.pi / 2))
              for k in range(10)])


def _locked(surf: pygame.Surface) -> pygame.Surface:
    """Greyscale, darkened, with a padlock in the lower right."""
    try:
        g = pygame.transform.grayscale(surf)
    except (AttributeError, pygame.error):           # pragma: no cover - old pygame
        g = surf.copy()
        arr = pygame.surfarray.pixels3d(g)
        lum = (arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114).astype('uint8')
        for i in range(3):
            arr[..., i] = lum
        del arr
    g.fill(LOCK_TINT, special_flags=pygame.BLEND_RGB_MULT)
    w, h = g.get_size()
    size = max(8, int(w * 0.30))
    bw, bh = size, int(size * 0.72)
    x = w - bw - max(1, w // 24)
    y = h - bh - max(1, h // 24)
    lw = max(1, size // 9)
    shackle = pygame.Rect(x + bw * 0.22, y - bh * 0.62, bw * 0.56, bh * 1.1)
    pygame.draw.ellipse(g, (36, 36, 44), shackle.inflate(lw * 2, lw * 2), lw * 3)
    pygame.draw.ellipse(g, (214, 214, 224), shackle, lw)
    body = pygame.Rect(x, y, bw, bh)
    pygame.draw.rect(g, (36, 36, 44), body.inflate(lw * 2, lw * 2), border_radius=max(1, size // 6))
    pygame.draw.rect(g, (150, 150, 162), body, border_radius=max(1, size // 7))
    pygame.draw.rect(g, (214, 214, 224), body, lw, border_radius=max(1, size // 7))
    pygame.draw.circle(g, (36, 36, 44), (body.centerx, body.centery - bh * 0.08), max(1, size // 9))
    pygame.draw.line(g, (36, 36, 44), (body.centerx, body.centery), (body.centerx, body.bottom - bh * 0.22),
                     max(1, size // 10))
    return g


# -- shared text and chrome ---------------------------------------------------

def _wrap(text, font, width) -> list[str]:
    from text_layout import wrap_lines
    return wrap_lines(str(text), max(1, int(width)), font)


def _blit(screen, text, font, color, x, y):
    ts = font.render(str(text), True, color)
    screen.blit(ts, (x, y))
    return ts


def format_date(stamp) -> str:
    """'2026-10-25T14:03' -> '25 October 2026' ('' if it will not read)."""
    import calendar
    try:
        y, m, d = str(stamp)[:10].split('-')
        return f"{int(d)} {calendar.month_name[int(m)]} {int(y)}"
    except (ValueError, IndexError):
        return ''


def entry_dict(session, aid) -> dict | None:
    """What a card or the popup draws for one achievement (the shape
    game_seeker._show_achievement_popup gives the popup)."""
    a = session.entry(aid) if session is not None else None
    if not a:
        return None
    return {'id': aid, 'name': a['name'], 'text': a['unlocked_text'],
            'code': session.code(aid), 'rarity': a['rarity'], 'art': a['art']}


def _code_box(screen, rect, code, accent):
    """The Reward Code box, in the story popup's style."""
    import ui_theme
    from fantasy_ui import FP, KT, get_font
    rect = pygame.Rect(rect)
    if not ui_theme.draw_piece(screen, 'card', rect, body_color=KT.RAISED):
        pygame.draw.rect(screen, FP.MIDNIGHT_MID, rect, border_radius=6)
        pygame.draw.rect(screen, accent, rect, 1, border_radius=6)
    label = "Reward Code: "
    fl = get_font('small', 16, bold=True)
    fc = get_font('heading', 22)
    lw, cw = fl.size(label)[0], fc.size(code)[0]
    if lw + cw <= rect.w - S(16):
        lx = rect.centerx - (lw + cw) // 2
        ls = fl.render(label, True, FP.PARCHMENT_LIGHT)
        cs = fc.render(code, True, FP.GOLD_BRIGHT)
        screen.blit(ls, (lx, rect.centery - ls.get_height() // 2))
        screen.blit(cs, (lx + lw, rect.centery - cs.get_height() // 2))
    else:
        # A narrow box: the code alone, as large as fits (it is never cut).
        fc = code_font(code, rect.w - S(12))
        cs = fc.render(code, True, FP.GOLD_BRIGHT)
        screen.blit(cs, (rect.centerx - cs.get_width() // 2, rect.centery - cs.get_height() // 2))


def code_font(code, width):
    """The largest code font that fits ``width`` (a DEV- code on a narrow
    pane drops to the narrower body face rather than be cut)."""
    from fantasy_ui import get_font
    for size in (22, 20, 18, 16):
        f = get_font('heading', size)
        if f.size(code)[0] <= width:
            return f
    return get_font('body', 16, bold=True)


def code_box_h() -> int:
    return S(40)


def _block_fonts():
    from fantasy_ui import get_font
    return get_font('heading', 24), get_font('body', 16, bold=True), get_font('body', 18)


def _block_layout(entry, w, badge_px):
    name_f, rar_f, text_f = _block_fonts()
    pad = S(6)
    well = badge_px + 2 * pad
    col_w = max(S(80), w - well - S(18))
    rar = RARITY_NAMES.get(entry.get('rarity'), '')
    rar_w = rar_f.size(rar)[0] + S(12) if rar else 0
    names = _wrap(entry.get('name', ''), name_f, col_w - rar_w)
    texts = _wrap(entry.get('text', ''), text_f, col_w) if entry.get('text') else []
    col_h = (len(names) * (name_f.get_height() + S(2)) + S(4)
             + len(texts) * (text_f.get_height() + S(3)) + S(8)
             + (code_box_h() if entry.get('code') else 0))
    return well, col_w, rar, names, texts, max(well, col_h), col_h


def block_height(entry, w, badge_px) -> int:
    """Height ``draw_block`` takes for ``entry`` in ``w`` px."""
    return _block_layout(entry, w, badge_px)[5]


def draw_block(screen, x, y, w, entry, badge_px, *, bg=None) -> int:
    """One won achievement: its badge in a rarity-coloured frame, the name
    (with the rarity beside it), the unlocked text and its Reward Code box.
    Returns the height drawn. Shared by the unlock card and the in-game
    unlock popup."""
    from fantasy_ui import FP, KT, kit_on, readable
    bg = bg or (KT.INTERIOR if kit_on() else FP.MIDNIGHT)
    well, col_w, rar, names, texts, total, col_h = _block_layout(entry, w, badge_px)
    name_f, rar_f, text_f = _block_fonts()
    color = rarity_color(entry.get('rarity'))
    wr = pygame.Rect(x, y + (total - well) // 2, well, well)
    pygame.draw.rect(screen, KT.WELL, wr)
    pygame.draw.rect(screen, color, wr, max(2, S(2)))
    pad = S(6)
    screen.blit(badge_surface(entry.get('art', entry.get('id', '')), badge_px, True,
                              rarity=entry.get('rarity')), (wr.x + pad, wr.y + pad))
    cx = wr.right + S(18)
    cy = y + (total - col_h) // 2
    head = readable(KT.TEXT_HEAD, bg)
    for i, line in enumerate(names):
        ts = _blit(screen, line, name_f, head, cx, cy)
        if i == 0 and rar:
            rs = rar_f.render(rar, True, readable(color, bg))
            screen.blit(rs, (cx + col_w - rs.get_width(), cy + (ts.get_height() - rs.get_height()) // 2))
        cy += name_f.get_height() + S(2)
    cy += S(4)
    body = readable(KT.TEXT_BODY, bg)
    for line in texts:
        _blit(screen, line, text_f, body, cx, cy)
        cy += text_f.get_height() + S(3)
    cy += S(8)
    if entry.get('code'):
        _code_box(screen, (cx, cy, col_w, code_box_h()), entry['code'], color)
    return total


def _chrome(screen, panel, title, accent, title_font=None, *, left_reserve=0, right_reserve=0):
    """Panel frame + header plaque. Returns (plaque rect, body top, band)."""
    from fantasy_ui import draw_dark_panel, draw_header_bar, draw_divider, panel_band, get_font
    import ui_theme
    draw_dark_panel(screen, panel, border_color=accent)
    hr = draw_header_bar(screen, (panel.x, panel.y, panel.w, S(48)), text=title,
                         font=title_font or get_font('heading', 28), accent=accent,
                         left_reserve=left_reserve, right_reserve=right_reserve,
                         frame=(panel, accent))
    b = panel_band('panel', panel)
    if b and ui_theme.has('header'):
        return hr, hr.bottom + S(12), b
    draw_divider(screen, panel.x + S(18), panel.y + S(48) + S(10), panel.w - 2 * S(18))
    return hr, panel.y + S(48) + S(22), b


def _footer(screen, panel, hint):
    """Divider and key hints at the bottom of ``panel``. Returns the y the
    body must stay above."""
    from fantasy_ui import draw_divider, draw_key_hints, key_hints_height, panel_band
    b = panel_band('panel', panel)
    kh = key_hints_height()
    keys = pygame.Rect(panel.x + b + S(20), panel.bottom - b - S(8) - kh,
                       panel.w - 2 * (b + S(20)), kh)
    div_y = keys.y - S(16)
    draw_divider(screen, panel.x + b + S(28), div_y, panel.w - 2 * (b + S(28)))
    draw_key_hints(screen, keys, hint)
    return div_y - S(16)


def footer_room() -> int:
    """Height the footer takes above a panel's bottom band."""
    from fantasy_ui import key_hints_height
    return S(8) + key_hints_height() + S(32)


def _subpanel(screen, rect, label, *, border=None):
    """A sub-panel with its label strip (the game's ``_ui_subpanel``).
    Returns its body rect."""
    import ui_theme
    from fantasy_ui import FP, KT, get_font, display_title
    border = border or FP.GOLD_DARK
    head = pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, S(29))
    if ui_theme.draw_piece(screen, 'subpanel', rect, accent=border, body_color=KT.RAISED):
        ui_theme.draw_piece(screen, 'subpanel_header', head, accent=border)
        f = get_font('heading', 17, bold=True)
        ts = f.render(display_title(label.upper()), True, KT.TEXT_HEAD)
        screen.blit(ts, (head.centerx - ts.get_width() // 2,
                         head.y + (head.h - S(2) - ts.get_height()) // 2))
    else:
        pygame.draw.rect(screen, FP.MIDNIGHT, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 1, border_radius=6)
        pygame.draw.rect(screen, FP.MIDNIGHT_MID, head, border_radius=6)
        f = get_font('body', 16, bold=True)
        ts = f.render(display_title(label), True, FP.GOLD_BRIGHT)
        screen.blit(ts, (rect.centerx - ts.get_width() // 2, rect.y + S(6)))
    return pygame.Rect(rect.x + S(12), rect.y + S(42), rect.w - 2 * S(12), rect.h - S(54))


def _row_bg(screen, rect, selected):
    import ui_theme
    from fantasy_ui import FP
    if not ui_theme.draw_piece(screen, 'row_selected' if selected else 'row', rect):
        pygame.draw.rect(screen, FP.MIDNIGHT_MID if selected else FP.MIDNIGHT, rect, border_radius=5)
        pygame.draw.rect(screen, FP.GOLD if selected else FP.GOLD_DARK, rect,
                         2 if selected else 1, border_radius=5)


# -- the unlock card ------------------------------------------------------------

def unlock_card_rect(screen, entries):
    """(panel, badge px) of the unlock card for ``entries`` (at most three)."""
    from fantasy_ui import panel_band
    W, H = screen.get_size()
    entries = list(entries)[:3]
    bw = min(S(760), W - S(48))
    probe = pygame.Rect(0, 0, bw, S(400))
    b = panel_band('panel', probe)
    inner_w = bw - 2 * (b + S(32))
    line_h = _card_line_font().get_height()
    chrome = 2 * b + S(48) + S(16) + S(14) + line_h + footer_room()
    bp = S(GRID_BADGE)
    for size in (96, 80, 64, 56):
        bp = S(size)
        h = chrome + sum(block_height(e, inner_w, bp) for e in entries) + S(14) * (len(entries) - 1)
        if h <= H - S(48):
            break
    ph = min(H - S(48), h)
    return pygame.Rect((W - bw) // 2, (H - ph) // 2, bw, ph), bp


def _card_line_font():
    from fantasy_ui import get_font
    return get_font('body', 18, bold=True)


def prebuild_card(entries):
    for e in list(entries)[:3]:
        for size in (96, 80, 64, 56):
            badge_surface(e.get('art', e.get('id', '')), S(size), True, rarity=e.get('rarity'))


def draw_unlock_card(screen, entries, *, hint="Any key: continue"):
    """The small "Achievement Unlocked" card over the title or the Seeker
    screen: each badge, name, text and Reward Code, and the line for Dad."""
    from fantasy_ui import FP, KT, draw_overlay, kit_on, readable
    entries = list(entries)[:3]
    if not entries:
        return
    draw_overlay(screen, 200)
    panel, bp = unlock_card_rect(screen, entries)
    one = len(entries) == 1
    _hr, top, b = _chrome(screen, panel, 'Achievement Unlocked' if one else 'Achievements Unlocked',
                          FP.ACHIEVEMENT)
    x = panel.x + b + S(32)
    w = panel.w - 2 * (b + S(32))
    y = top + S(4)
    for e in entries:
        y += draw_block(screen, x, y, w, e, bp) + S(14)
    y -= S(14)
    y += S(12)
    lf = _card_line_font()
    bg = KT.INTERIOR if kit_on() else FP.MIDNIGHT
    ls = lf.render("Show this code to Dad." if one else "Show these codes to Dad.", True,
                   readable(KT.TEXT_QUIZ, bg))
    screen.blit(ls, (panel.centerx - ls.get_width() // 2, y))
    _footer(screen, panel, hint)


# -- the Konami code ------------------------------------------------------------

class KonamiDetector:
    """Up Up Down Down Left Right Left Right B A, fed one key at a time.
    Modifier keys (Shift for a capital B) are ignored."""

    SEQUENCE = (pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN, pygame.K_LEFT,
                pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_b, pygame.K_a)
    _IGNORE = frozenset({pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_CAPSLOCK, pygame.K_LCTRL,
                         pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT, pygame.K_LGUI, pygame.K_RGUI})

    def __init__(self):
        self._recent: list[int] = []

    def feed(self, key) -> bool:
        """True when ``key`` completes the code."""
        if key in self._IGNORE:
            return False
        n = len(self.SEQUENCE)
        self._recent = (self._recent + [key])[-n:]
        if tuple(self._recent) == self.SEQUENCE:
            self._recent = []
            return True
        return False

    def primed(self) -> bool:
        """True when only the final A is missing (B was the last key)."""
        n = len(self.SEQUENCE) - 1
        return tuple(self._recent[-n:]) == self.SEQUENCE[:n]


# -- names ------------------------------------------------------------------------

def check_name(text) -> tuple[str | None, str]:
    """(the tidy Seeker name, '') or (None, why it cannot be one)."""
    import seeker_profile
    name = seeker_profile.clean_name(text)
    if name is None:
        if not str(text or '').strip():
            return None, "Type a name first."
        return None, "A name needs at least one letter or number."
    return name, ''


# -- the in-game Encyclopedia tab (n) -------------------------------------------

def categories(book=None) -> list[dict]:
    if book is None:
        import achievements
        book = achievements.load()
    return list(book.categories)


def encyclopedia_entries(session, cat_index: int = 0) -> list[dict]:
    """The Encyclopedia's rows for one achievement category, in data order
    (empty without a Seeker). Read-only."""
    if session is None:
        return []
    cats = categories(session.book)
    if not cats:
        return []
    cid = cats[cat_index % len(cats)]['id']
    prof = session.profile
    return [{'_id': a['id'], 'name': a['name'], '_won': prof.is_unlocked(a['id']),
             '_art': a['art'], '_rarity': a['rarity'], '_category': a['category']}
            for a in session.book.entries if a['category'] == cid]


def prebuild_entries(entries, sizes):
    for e in entries:
        for px in sizes:
            badge_surface(e['_art'], px, e['_won'], rarity=e['_rarity'], category=e['_category'])


def won_count(session, cid=None) -> tuple[int, int]:
    """(won, total) for one category, or for the whole book."""
    book, prof = session.book, session.profile
    ids = [a['id'] for a in book.entries if cid is None or a['category'] == cid]
    return sum(1 for i in ids if prof.is_unlocked(i)), len(ids)


def status_line(session, aid) -> str:
    """'Won on 25 October 2026 by Fianna', or 'Not won yet'."""
    info = session.profile.unlocked().get(aid)
    if info is None:
        return "Not won yet"
    date = format_date(info.get('at', ''))
    hero = str(info.get('hero') or '').strip()
    out = f"Won on {date}" if date else "Won"
    if hero:
        out += f" by {hero}"
    return out


def ladder_info(book, a) -> tuple[int, int] | None:
    """(this tier, tiers in its ladder) for a ladder entry, else None."""
    if not a or 'ladder' not in a:
        return None
    lad = book.ladder(a['ladder'])
    return int(a.get('tier', 1)), len(lad)


# -- the Seeker Profile screen ---------------------------------------------------

# The lifetime counters on the stats line: (label, counter).
STATS = (('Questions Answered', 'questions_answered'), ('Journeys', 'journeys'),
         ('Deepest Floor', 'deepest_floor'), ('Falls', 'falls'),
         ('Monsters Slain', 'kills'), ('Biggest Blow', 'biggest_blow'))


class SeekerScreen:
    """The Seeker Profile screen, opened with F4 on the title. With no Seeker
    chosen it opens on "Who Is Playing?"."""

    _PAGE_W = 1240
    _NAME_W = 640
    _NAME_ROWS = 6

    def __init__(self, screen):
        import achievements
        import seeker_session
        self.screen = screen
        self.book = achievements.load()
        self.cats = categories(self.book)
        self.by_cat = {c['id']: [a for a in self.book.entries if a['category'] == c['id']]
                       for c in self.cats}
        try:
            self.session = seeker_session.open_active()
        except Exception:
            self.session = None
        self.phase = 'gallery' if self.session is not None else 'name'
        self.cat = 0
        self.sel = 0
        self.scroll = 0               # first grid row shown
        self._cols = 5
        self._shown: set = set()      # won ids shown on screen (marked seen on close)
        self._new: set = self._unseen()
        self.cards: list = []          # unlock cards waiting for a key
        self._built = None
        self._layout_cache = None
        self._reset_name_view()
        # Anything the profile already owes (a ladder tier a newer version
        # added, an edited file found) is shown at once.
        if self.session is not None:
            self._take(self.session.settle())

    # -- state ------------------------------------------------------------
    def _unseen(self) -> set:
        if self.session is None:
            return set()
        p = self.session.profile
        return {aid for aid in p.unlocked() if not p.is_seen(aid)}

    def _entries(self) -> list:
        if not self.cats:
            return []
        return self.by_cat.get(self.cats[self.cat % len(self.cats)]['id'], [])

    def _won(self, aid) -> bool:
        return self.session is not None and self.session.profile.is_unlocked(aid)

    def _take(self, won):
        """Queue the cards for what was just won."""
        seen = {c['id'] for c in self.cards}
        for aid in won or ():
            if aid in seen:
                continue
            e = entry_dict(self.session, aid)
            if e:
                self.cards.append(e)
                seen.add(aid)
                self._new.add(aid)
        prebuild_card(self.cards[:3])

    def _reset_name_view(self):
        import seeker_profile
        self.name_buf = ''
        self.name_error = ''
        try:
            self.names = seeker_profile.all_names()
        except Exception:
            self.names = []
        active = self.session.name if self.session is not None else None
        import seeker_codes
        self.name_pick = next((i for i, n in enumerate(self.names) if active and
                               seeker_codes.normalise_name(n) == seeker_codes.normalise_name(active)),
                              -1)
        self.name_scroll = 0

    # -- loop -------------------------------------------------------------
    def run(self, clock):
        """Until Esc: back to the title."""
        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._close()
                    pygame.quit()
                    sys.exit()
                if event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                    import layout
                    if (event.x, event.y) != (layout.WINDOW_W, layout.WINDOW_H):
                        layout.update(event.x, event.y)
                    continue
                if event.type == pygame.KEYDOWN and self.handle_key(event):
                    self._close()
                    return
            self.draw()
            pygame.display.flip()

    def _close(self):
        """Everything shown is now seen ("New" goes), and the profile is written."""
        s = self.session
        if s is None:
            return
        try:
            s.profile.mark_seen(self._shown)
            s.flush()
        except Exception:
            pass

    def handle_key(self, event) -> bool:
        """One key press. True when the screen should close."""
        key = event.key
        if key == pygame.K_F11:
            try:
                pygame.display.toggle_fullscreen()
                surf = pygame.display.get_surface()
                if surf is not None:
                    import layout
                    layout.update(*surf.get_size())
            except pygame.error:
                pass
            return False
        if self.cards:
            self._shown.update(c['id'] for c in self.cards[:3])
            self.cards = self.cards[3:]
            return False
        if self.phase == 'name':
            return self._name_key(event)
        return self._gallery_key(event)

    def _gallery_key(self, event) -> bool:
        key = event.key
        n = len(self._entries())
        cols = max(1, self._cols)
        if key == pygame.K_ESCAPE:
            return True
        if key == pygame.K_TAB:
            back = bool(getattr(event, 'mod', 0) & pygame.KMOD_SHIFT)
            self._set_cat(self.cat + (-1 if back else 1), 0)
        elif key == pygame.K_RIGHT:
            if self.sel + 1 < n:
                self.sel += 1
            else:
                self._set_cat(self.cat + 1, 0)
        elif key == pygame.K_LEFT:
            if self.sel > 0:
                self.sel -= 1
            else:
                self._set_cat(self.cat - 1, -1)
        elif key == pygame.K_DOWN:
            if self.sel + cols < n:
                self.sel += cols
            elif self.sel // cols < (n - 1) // cols:
                self.sel = n - 1               # the shorter last row
        elif key == pygame.K_UP:
            if self.sel - cols >= 0:
                self.sel -= cols
        elif key == pygame.K_HOME:
            self.sel = 0
        elif key == pygame.K_END:
            self.sel = max(0, n - 1)
        elif key == pygame.K_F4:
            self._reset_name_view()
            self.phase = 'name'
        return False

    def _set_cat(self, idx, sel):
        if not self.cats:
            return
        self.cat = idx % len(self.cats)
        n = len(self._entries())
        self.sel = max(0, n - 1) if sel == -1 else 0
        self.scroll = 0
        self._prebuild()

    def _name_key(self, event) -> bool:
        key = event.key
        if key == pygame.K_ESCAPE:
            if self.session is None:
                return True                    # opened with nobody chosen: back to the title
            self.phase = 'gallery'
            return False
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if 0 <= self.name_pick < len(self.names):
                self._choose(self.names[self.name_pick])
            else:
                name, why = check_name(self.name_buf)
                if name is None:
                    self.name_error = why
                else:
                    self._choose(name)
            return False
        if key == pygame.K_UP:
            self.name_pick = max(-1, self.name_pick - 1)
            return False
        if key == pygame.K_DOWN:
            self.name_pick = min(len(self.names) - 1, self.name_pick + 1)
            return False
        if key == pygame.K_BACKSPACE:
            self.name_pick = -1
            self.name_buf = self.name_buf[:-1]
            self.name_error = ''
            return False
        ch = getattr(event, 'unicode', '') or ''
        import seeker_profile
        if len(ch) == 1 and ch.isprintable() and len(self.name_buf) < seeker_profile.NAME_MAX:
            self.name_pick = -1
            self.name_buf += ch
            self.name_error = ''
        return False

    def _choose(self, typed):
        """Make ``typed`` the active Seeker, open it, and show what naming
        it won (naming yourself Dad is worth a try)."""
        import seeker_codes
        import seeker_profile
        import seeker_session
        name = seeker_profile.set_active(typed)
        session = seeker_session.open_active() if name else None
        if session is None:
            self.name_error = "That name could not be saved. Try again."
            return
        if self.session is not None and self.session is not session:
            self._close()
        self.session = session
        self._shown = set()
        self._new = self._unseen()
        self.cards = []
        won = list(session.emit('seeker_named', name=seeker_codes.normalise_name(name)))
        won += [w for w in session.settle() if w not in won]
        self._take(won)
        self.phase = 'gallery'
        self.cat = self.sel = self.scroll = 0
        self._built = None

    # -- layout -------------------------------------------------------------
    def _fonts(self):
        from fantasy_ui import get_font
        return {'title': get_font('heading', 32), 'slot': get_font('body', 18, bold=True),
                'stat': get_font('body', 16), 'stat_v': get_font('body', 16, bold=True),
                'tile': get_font('body', 16), 'name': get_font('heading', 24),
                'meta': get_font('body', 16), 'meta_b': get_font('body', 16, bold=True),
                'text': get_font('body', 18), 'chip': get_font('body', 16, bold=True)}

    def _layout(self, W, H):
        """Every rect of the gallery at this window size (cached). The page
        is as tall as the largest category's grid needs (a tall window,
        e.g. a portrait monitor, does not get a page of empty panes), at
        most the window."""
        import ui_scale
        key = (W, H, ui_scale.get(), self.session.name if self.session else '')
        if self._layout_cache and self._layout_cache[0] == key:
            return self._layout_cache[1]
        margin = S(24)
        pw = min(W - 2 * margin, S(self._PAGE_W))
        full = H - 2 * margin
        lay = self._place(pygame.Rect((W - pw) // 2, margin, pw, full))
        need = lay['panes'].y - lay['panel'].y + lay['panes_need'] + lay['foot_h']
        if need < full:
            lay = self._place(pygame.Rect((W - pw) // 2, (H - need) // 2, pw, need))
        self._layout_cache = (key, lay)
        return lay

    def _place(self, panel):
        from fantasy_ui import panel_band, key_hints_height
        b = panel_band('panel', panel)
        f = self._fonts()
        side = b + S(26)
        top = panel.y + (b if b else 0) + S(48) + S(12 if b else 22)
        inner = pygame.Rect(panel.x + side, top, panel.w - 2 * side, 0)
        stats_lines = self._stat_rows(inner.w, f)
        y = top + len(stats_lines) * (f['stat'].get_height() + S(4)) + S(6)
        tabs_y = y
        y += S(30) + S(12)
        kh = key_hints_height()
        bottom = panel.bottom - b - S(8) - kh - S(32)
        panes = pygame.Rect(inner.x, y, inner.w, bottom - y)
        gutter = S(14)
        grid_w = int(panes.w * 0.58)
        grid = pygame.Rect(panes.x, panes.y, grid_w, panes.h)
        detail = pygame.Rect(grid.right + gutter, panes.y, panes.right - grid.right - gutter, panes.h)
        grid_body = pygame.Rect(grid.x + S(12), grid.y + S(42), grid.w - 2 * S(12), grid.h - S(54))
        det_body = pygame.Rect(detail.x + S(12), detail.y + S(42), detail.w - 2 * S(12),
                               detail.h - S(54))
        gb = S(GRID_BADGE)
        tile_w = max(S(124), f['tile'].size('M')[0] * 13)
        gap = S(8)
        lane = S(12)                                  # the scrollbar's lane
        cols = max(1, (grid_body.w - lane + gap) // (tile_w + gap))
        tile_w = (grid_body.w - lane - gap * (cols - 1)) // cols
        dp = min(S(DETAIL_BADGE), int(det_body.w * 0.40), max(S(48), int(det_body.h * 0.42)))
        # The room the largest category's grid needs, at its tallest tiles.
        lines = max([min(3, len(_wrap(a['name'], f['tile'], tile_w - S(8))))
                     for a in self.book.entries] or [1])
        tile_h = S(8) + gb + S(6) + lines * (f['tile'].get_height() + S(1)) + S(8)
        most = max([len(v) for v in self.by_cat.values()] or [1])
        rows = -(-most // cols)
        panes_need = max(rows * (tile_h + gap) - gap + S(54) + S(4), S(DETAIL_BADGE) + S(300))
        return {'panel': panel, 'band': b, 'stats': stats_lines, 'stats_y': top, 'tabs_y': tabs_y,
                'inner': inner, 'grid': grid, 'detail': detail, 'grid_body': grid_body,
                'det_body': det_body, 'tile_w': tile_w, 'gap': gap, 'cols': cols, 'gb': gb,
                'dp': max(S(48), dp), 'panes': panes, 'panes_need': panes_need,
                'foot_h': panel.bottom - bottom}

    def _stat_rows(self, width, f):
        """The stats as rows of (label, value) pairs that fit ``width``."""
        if self.session is None:
            return []
        pairs = []
        for label, counter in STATS:
            v = self.book.value(counter, self.session.profile, None)
            pairs.append((f"{label}: ", f"{v:,}"))
        sep = S(28)
        rows, cur, cur_w = [], [], 0
        for lab, val in pairs:
            w = f['stat'].size(lab)[0] + f['stat_v'].size(val)[0]
            if cur and cur_w + sep + w > width:
                rows.append(cur)
                cur, cur_w = [], 0
            cur_w += (sep if cur else 0) + w
            cur.append((lab, val))
        if cur:
            rows.append(cur)
        return rows

    def _tile_lines(self, lay):
        """The wrapped names of this tab's tiles and the tile height."""
        f = self._fonts()['tile']
        names = [_wrap(a['name'], f, lay['tile_w'] - S(8)) for a in self._entries()]
        n_lines = max([len(x) for x in names] or [1])
        tile_h = S(8) + lay['gb'] + S(6) + n_lines * (f.get_height() + S(1)) + S(8)
        return names, tile_h

    def _prebuild(self):
        """This tab's badges at the grid and detail sizes, before they are drawn."""
        if self.phase != 'gallery' or self.session is None:
            return
        W, H = self.screen.get_size()
        lay = self._layout(W, H)
        key = (self.cat, lay['gb'], lay['dp'], self.session.name)
        if self._built == key:
            return
        items = [(a['art'], self._won(a['id'])) for a in self._entries()]
        prebuild(items, lay['gb'])
        prebuild(items, lay['dp'])
        self._built = key
        self._shown.update(a['id'] for a in self._entries() if self._won(a['id']))

    # -- drawing --------------------------------------------------------------
    def draw(self):
        from fantasy_ui import FP, KT, kit_on
        W, H = self.screen.get_size()
        self.screen.fill(KT.VOID if kit_on() else FP.MIDNIGHT)
        if self.phase == 'name' or self.session is None:
            self._draw_name(W, H)
        else:
            self._draw_gallery(W, H)
        if self.cards:
            draw_unlock_card(self.screen, self.cards[:3])

    def _draw_gallery(self, W, H):
        from fantasy_ui import FP, KT, readable
        self._prebuild()
        lay = self._layout(W, H)
        f = self._fonts()
        panel = lay['panel']
        s = self.session
        won, total = won_count(s)
        count = f"{won} of {total} Won"
        name = s.name
        slot = max(f['slot'].size(count)[0], f['slot'].size(name)[0]) + S(60)
        hr, _top, b = _chrome(self.screen, panel, "Seeker Profile", FP.GOLD, f['title'],
                              left_reserve=slot, right_reserve=slot)
        plaque = KT.PLAQUE
        sy = hr.y + (hr.h - S(4) - f['slot'].get_height()) // 2
        _blit(self.screen, name, f['slot'], readable(KT.TEXT_BODY, plaque), hr.x + S(40), sy)
        cs = f['slot'].render(count, True, readable(KT.TEXT_SUB, plaque))
        self.screen.blit(cs, (hr.right - S(40) - cs.get_width(), sy))
        # The lifetime counters, centred.
        bg = KT.INTERIOR
        y = lay['stats_y']
        sep = S(28)
        for row in lay['stats']:
            widths = [f['stat'].size(lab)[0] + f['stat_v'].size(val)[0] for lab, val in row]
            x = panel.centerx - (sum(widths) + sep * (len(row) - 1)) // 2
            for (lab, val), w in zip(row, widths):
                ls = _blit(self.screen, lab, f['stat'], readable(KT.TEXT_DIM, bg), x, y)
                _blit(self.screen, val, f['stat_v'], readable(KT.TEXT_HEAD, bg), x + ls.get_width(), y)
                x += w + sep
            y += f['stat'].get_height() + S(4)
        self._draw_tabs(lay['inner'].x, lay['tabs_y'], lay['inner'].w)
        cat = self.cats[self.cat % len(self.cats)] if self.cats else {'id': '', 'name': ''}
        cw, ct = won_count(s, cat['id'])
        gbody = _subpanel(self.screen, lay['grid'], f"{cat['name']}: {cw} of {ct} Won")
        self._draw_grid(gbody, lay)
        dbody = _subpanel(self.screen, lay['detail'], "Selected Achievement")
        entries = self._entries()
        if entries:
            self.sel = max(0, min(self.sel, len(entries) - 1))
            self._draw_detail(dbody, entries[self.sel], lay['dp'])
        _footer(self.screen, panel, "Arrows: choose a badge   Tab: next category   "
                                    "F4: change Seeker   ESC: close")

    def _draw_tabs(self, x, y, w):
        import ui_theme
        from fantasy_ui import FP, KT, get_font, kit_on
        from text_layout import tab_strip_window
        f = self._fonts()['chip']
        gap, arrow_w, tab_h = S(8), S(24), S(30)
        labels = [c['name'] for c in self.cats]
        widths = [f.size(t)[0] + S(26) for t in labels]
        win = tab_strip_window(widths, self.cat, w, gap=gap, arrow_w=arrow_w)
        # Centre the strip when it all fits.
        if not win['overflow']:
            x += (w - (sum(widths) + gap * (len(widths) - 1))) // 2
        arrow_f = get_font('symbol', 14)

        def arrow(rect, glyph):
            if not ui_theme.draw_piece(self.screen, 'chip', rect):
                pygame.draw.rect(self.screen, FP.MIDNIGHT, rect, border_radius=4)
                pygame.draw.rect(self.screen, FP.GOLD_DARK, rect, 1, border_radius=4)
            a = arrow_f.render(glyph, True, KT.TEXT_HEAD)
            self.screen.blit(a, (rect.centerx - a.get_width() // 2, rect.centery - a.get_height() // 2))

        tx, max_x = x, x + w
        if win['show_left_arrow']:
            arrow(pygame.Rect(tx, y, arrow_w, tab_h), '◀')
            tx += arrow_w + gap
        reserved = arrow_w + gap if win['show_right_arrow'] else 0
        for i in range(win['start'], win['end']):
            tw = widths[i]
            if tx + tw > max_x - reserved:
                break
            rect = pygame.Rect(tx, y, tw, tab_h)
            active = i == self.cat
            if ui_theme.draw_piece(self.screen, 'chip_active' if active else 'chip', rect,
                                   accent=FP.GOLD if active else None):
                col = KT.TEXT_BODY if active else KT.TEXT_DIM
            else:
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if active else FP.MIDNIGHT, rect,
                                 border_radius=5)
                pygame.draw.rect(self.screen, FP.GOLD if active else FP.GOLD_DARK, rect, 1,
                                 border_radius=5)
                col = FP.GOLD_BRIGHT if active else FP.FADED_TEXT
            font = f if active or not kit_on() else get_font('body', 16)
            ts = font.render(labels[i], True, col)
            self.screen.blit(ts, (rect.centerx - ts.get_width() // 2, rect.centery - ts.get_height() // 2))
            tx += tw + gap
        if win['show_right_arrow']:
            arrow(pygame.Rect(max_x - arrow_w, y, arrow_w, tab_h), '▶')

    def _draw_grid(self, body, lay):
        import ui_theme
        from fantasy_ui import FP, KT, readable
        entries = self._entries()
        f = self._fonts()
        names, tile_h = self._tile_lines(lay)
        cols, gap, tw, gb = lay['cols'], lay['gap'], lay['tile_w'], lay['gb']
        self._cols = cols
        rows = -(-len(entries) // cols) if entries else 0
        vis = max(1, (body.h + gap) // (tile_h + gap))
        row = self.sel // cols
        if row < self.scroll:
            self.scroll = row
        if row >= self.scroll + vis:
            self.scroll = row - vis + 1
        self.scroll = max(0, min(self.scroll, max(0, rows - vis)))
        lh = f['tile'].get_height() + S(1)
        new_f = f['meta_b']
        for i in range(self.scroll * cols, min(len(entries), (self.scroll + vis) * cols)):
            r, c = divmod(i - self.scroll * cols, cols)
            rect = pygame.Rect(body.x + c * (tw + gap), body.y + r * (tile_h + gap), tw, tile_h)
            a = entries[i]
            won = self._won(a['id'])
            sel = i == self.sel
            bg = KT.RAISED
            if sel:
                _row_bg(self.screen, rect, True)
                bg = KT.SELECTED
            self.screen.blit(badge_surface(a['art'], gb, won), (rect.centerx - gb // 2, rect.y + S(8)))
            col = readable(KT.TEXT_BODY if won else KT.TEXT_DIM, bg)
            ty = rect.y + S(8) + gb + S(6)
            for line in names[i]:
                ts = f['tile'].render(line, True, col)
                self.screen.blit(ts, (rect.centerx - ts.get_width() // 2, ty))
                ty += lh
            if won and a['id'] in self._new:
                ns = new_f.render("New", True, KT.TEXT_BODY)
                chip = pygame.Rect(0, 0, ns.get_width() + S(14), ns.get_height() + S(4))
                chip.topright = (rect.right - S(4), rect.y + S(4))
                if not ui_theme.draw_piece(self.screen, 'chip_active', chip, accent=FP.ACHIEVEMENT):
                    pygame.draw.rect(self.screen, FP.MIDNIGHT_MID, chip, border_radius=5)
                    pygame.draw.rect(self.screen, FP.ACHIEVEMENT, chip, 1, border_radius=5)
                self.screen.blit(ns, (chip.centerx - ns.get_width() // 2,
                                      chip.centery - ns.get_height() // 2))
        if rows > vis:
            self._scrollbar(body, self.scroll, rows, vis)

    def _scrollbar(self, rect, scroll, total, visible):
        import ui_theme
        from fantasy_ui import FP
        track = pygame.Rect(rect.right - S(8), rect.y, S(5), rect.h)
        if not ui_theme.draw_piece(self.screen, 'scroll_track', track, body_color=FP.MIDNIGHT):
            pygame.draw.rect(self.screen, FP.MIDNIGHT, track, border_radius=3)
        thumb_h = max(S(20), int(track.h * visible / max(1, total)))
        y = track.y + int((track.h - thumb_h) * (scroll / max(1, total - visible)))
        thumb = pygame.Rect(track.x, y, track.w, thumb_h)
        if not ui_theme.draw_piece(self.screen, 'scroll_thumb', thumb, accent=FP.GOLD_DARK):
            pygame.draw.rect(self.screen, FP.GOLD_DARK, thumb, border_radius=3)

    def _detail_lines(self, a, col_w, full_w, f):
        """The detail pane's text: (beside the badge, under it)."""
        s = self.session
        won = self._won(a['id'])
        beside = [(line, 'name') for line in _wrap(a['name'], f['name'], col_w)]
        cat_name = next((c['name'] for c in self.cats if c['id'] == a['category']), '')
        beside += [(line, 'rarity') for line in
                   _wrap(f"{RARITY_NAMES.get(a['rarity'], '')}  •  {cat_name}", f['meta'], col_w)]
        beside += [(line, 'won' if won else 'locked') for line in
                   _wrap(status_line(s, a['id']), f['meta'], col_w)]
        under = []
        if won:
            under += [(line, 'text') for line in _wrap(a['unlocked_text'], f['text'], full_w)]
        else:
            under.append(("Hint", 'head'))
            under += [(line, 'hint') for line in _wrap(a['hint'], f['text'], full_w)]
        return beside, under

    def _draw_detail(self, body, a, dp):
        import ui_theme
        from fantasy_ui import FP, KT, readable
        s = self.session
        f = self._fonts()
        won = self._won(a['id'])
        color = rarity_color(a['rarity'])
        pad = S(6)
        well = pygame.Rect(body.x, body.y, dp + 2 * pad, dp + 2 * pad)
        pygame.draw.rect(self.screen, KT.WELL, well)
        if won:
            pygame.draw.rect(self.screen, color, well, max(2, S(2)))
        else:
            pygame.draw.rect(self.screen, KT.LINE, well, 1)
        self.screen.blit(badge_surface(a['art'], dp, won), (well.x + pad, well.y + pad))
        cx = well.right + S(16)
        col_w = body.right - cx - S(4)
        beside, under = self._detail_lines(a, col_w, body.w - S(8), f)
        bg = KT.RAISED
        colors = {'name': readable(KT.TEXT_HEAD, bg), 'rarity': readable(color, bg),
                  'won': readable(KT.OK_TEXT, bg), 'locked': readable(KT.TEXT_DIM, bg),
                  'text': readable(KT.TEXT_BODY, bg), 'hint': readable(KT.TEXT_QUIZ, bg),
                  'head': readable(KT.TEXT_SUB, bg)}
        fonts = {'name': f['name'], 'rarity': f['meta'], 'won': f['meta'], 'locked': f['meta'],
                 'text': f['text'], 'hint': f['text'], 'head': f['meta_b']}
        y = body.y + S(2)
        prev = None
        for text, kind in beside:
            if prev is not None and prev != kind:
                y += S(4)
            _blit(self.screen, text, fonts[kind], colors[kind], cx, y)
            y += fonts[kind].get_height() + S(2)
            prev = kind
        y = max(y, well.bottom) + S(12)
        for text, kind in under:
            _blit(self.screen, text, fonts[kind], colors[kind], body.x, y)
            y += fonts[kind].get_height() + S(3)
        y += S(10)
        lad = ladder_info(self.book, a)
        if lad:
            tier, n = lad
            ladder = self.book.ladder(a['ladder'])
            r = S(6)
            x = body.x + r
            mid = y + f['meta'].get_height() // 2
            for t in ladder:
                got = self._won(t['id'])
                c = rarity_color(t['rarity'])
                if got:
                    pygame.draw.circle(self.screen, c, (x, mid), r)
                else:
                    pygame.draw.circle(self.screen, KT.LINE, (x, mid), r, max(1, S(2)))
                if t['id'] == a['id']:
                    pygame.draw.circle(self.screen, KT.TEXT_HEAD, (x, mid), r + S(3), 1)
                x += 3 * r + S(2)
            _blit(self.screen, f"Tier {tier} of {n}", f['meta'], colors['locked'], x + S(6), y)
            y += f['meta'].get_height() + S(10)
        prog = self.book.progress(a['id'], s.profile, None)
        if prog and not won:
            have, need = prog
            label = f"{have:,} of {need:,}"
            ls = f['meta_b'].render(label, True, readable(KT.TEXT_HEAD, bg))
            bar = pygame.Rect(body.x, y + (ls.get_height() - S(12)) // 2,
                              max(S(60), body.w - ls.get_width() - S(20)), S(12))
            if not ui_theme.draw_piece(self.screen, 'bar_track', bar, body_color=FP.MIDNIGHT):
                pygame.draw.rect(self.screen, FP.MIDNIGHT, bar, border_radius=4)
            art = ui_theme.has('bar_track') and ui_theme.fits('bar_track', bar.w, bar.h)
            inner = bar.inflate(-S(4), -S(4)) if art else bar
            fw = int(inner.w * (have / max(1, need)))
            if fw:
                pygame.draw.rect(self.screen, FP.ACHIEVEMENT, (inner.x, inner.y, fw, inner.h),
                                 border_radius=0 if art else 4)
            if not ui_theme.draw_piece(self.screen, 'bar_frame', bar, body=False):
                pygame.draw.rect(self.screen, FP.ARCANE_DIM, bar, 1, border_radius=4)
            self.screen.blit(ls, (bar.right + S(12), y))
            y += ls.get_height() + S(12)
        if won:
            code = s.code(a['id'])
            box = pygame.Rect(body.x, y, body.w - S(8), code_box_h())
            _code_box(self.screen, box, code, color)
            y = box.bottom + S(8)
            _blit(self.screen, "Show this code to Dad.", f['meta_b'], readable(KT.TEXT_QUIZ, bg),
                  body.x, y)

    # -- "Who Is Playing?" ----------------------------------------------------
    def _name_rows_visible(self):
        return min(self._NAME_ROWS, max(1, len(self.names)))

    def _draw_name(self, W, H):
        from fantasy_ui import FP, KT, get_font, draw_input_box, readable, panel_band
        f = self._fonts()
        body_f = f['text']
        margin = S(24)
        pw = min(W - 2 * margin, S(self._NAME_W))
        probe = pygame.Rect(0, 0, pw, S(400))
        b = panel_band('panel', probe)
        side = b + S(32)
        inner_w = pw - 2 * side
        prompt = ("Type your name, or pick it from the list below. Every hero you play "
                  "adds to your achievements." if self.names else
                  "Type your name. Every hero you play adds to your achievements, and "
                  "each one won has a Reward Code to show Dad.")
        p_lines = _wrap(prompt, body_f, inner_w)
        row_h, gap = S(36), S(4)
        rows = self._name_rows_visible() if self.names else 0
        lh = body_f.get_height() + S(4)
        head_f = get_font('heading', 17, bold=True)
        content = (len(p_lines) * lh + S(12) + S(44) + S(8) + f['meta'].get_height() + S(10)
                   + ((head_f.get_height() + S(8) + rows * (row_h + gap) + S(8)) if rows else 0))
        top_chrome = (b + S(48) + S(12)) if b else S(48) + S(22)
        ph = min(H - 2 * margin, top_chrome + content + S(8) + footer_room() + b)
        panel = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)
        _hr, top, b = _chrome(self.screen, panel, "Who Is Playing?", FP.GOLD, f['title'])
        bg = KT.INTERIOR
        x = panel.x + side
        y = top + S(2)
        for line in p_lines:
            _blit(self.screen, line, body_f, readable(KT.TEXT_BODY, bg), x, y)
            y += lh
        y += S(12)
        box = pygame.Rect(x, y, inner_w, S(44))
        draw_input_box(self.screen, box, self.name_buf, get_font('heading', 24),
                       border_color=FP.GOLD_BRIGHT if self.name_pick < 0 else FP.GOLD_DARK,
                       placeholder="Your name")
        y = box.bottom + S(8)
        if self.name_error:
            _blit(self.screen, self.name_error, f['meta'], readable(FP.DANGER_TEXT_LIGHT, bg), x, y)
        y += f['meta'].get_height() + S(10)
        if rows:
            hs = head_f.render("Seekers on This Computer", True, readable(KT.TEXT_HEAD, bg))
            self.screen.blit(hs, (x, y))
            y += head_f.get_height() + S(8)
            if self.name_pick >= 0:
                if self.name_pick < self.name_scroll:
                    self.name_scroll = self.name_pick
                if self.name_pick >= self.name_scroll + rows:
                    self.name_scroll = self.name_pick - rows + 1
            self.name_scroll = max(0, min(self.name_scroll, len(self.names) - rows))
            active = self.session.name if self.session is not None else None
            import seeker_codes
            for i in range(self.name_scroll, min(len(self.names), self.name_scroll + rows)):
                rect = pygame.Rect(x, y, inner_w - (S(12) if len(self.names) > rows else 0), row_h)
                sel = i == self.name_pick
                _row_bg(self.screen, rect, sel)
                rbg = KT.SELECTED if sel else KT.RAISED
                ns = f['slot'].render(self.names[i], True, readable(KT.TEXT_HEAD if sel else KT.TEXT_BODY, rbg))
                self.screen.blit(ns, (rect.x + S(14), rect.centery - ns.get_height() // 2))
                if active and seeker_codes.normalise_name(active) == seeker_codes.normalise_name(self.names[i]):
                    ts = f['meta'].render("Playing Now", True, readable(KT.OK_TEXT, rbg))
                    self.screen.blit(ts, (rect.right - S(14) - ts.get_width(),
                                          rect.centery - ts.get_height() // 2))
                y += row_h + gap
            if len(self.names) > rows:
                self._scrollbar(pygame.Rect(x, y - rows * (row_h + gap), inner_w, rows * (row_h + gap) - gap),
                                self.name_scroll, len(self.names), rows)
        back = "back" if self.session is not None else "close"
        hint = (f"Up/Down: pick a Seeker   Enter: confirm   Esc: {back}" if self.names
                else f"Enter: confirm   Esc: {back}")
        _footer(self.screen, panel, hint)
