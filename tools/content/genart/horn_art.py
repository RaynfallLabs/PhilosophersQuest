"""Art for the four horns of legend (data/horns.json), made in code from the game's
own painted sprites, because ComfyUI was not running when they were built
(2026-11-16). Each picture starts from an installed 64 px painted sprite of the
same kind of figure (a green-hooded archer, a knight, a robed old man) and is
recoloured to its lore: Lincoln green for Robin Hood's men, the Red Knight's red
for Percival, gold on red for Gawain's pentangle, Valhalla's gold light for the
einherjar, a crown for each king. A painted pass can replace any of them later:
the briefs are in tools/content/genart/briefs/horns_h01.json (ally and NPC
sprites) for pipeline.py, and nothing else changes when it does.

    py tools/content/genart/horn_art.py            # write the pictures into assets/
    py tools/content/genart/horn_art.py --sheet S  # and a review sheet at S

Monsters go to assets/tiles/monsters/<kind>.png, items to assets/tiles/items/.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MON = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
ITM = os.path.join(ROOT, 'assets', 'tiles', 'items')
OUTLINE = (20, 16, 24, 255)

GREEN = 105          # Lincoln green, in degrees of hue
GOLD = (222, 178, 60)


def load(path):
    return Image.open(path).convert('RGBA')


def _hsv(img):
    a = np.asarray(img).astype(np.float32) / 255.0
    rgb = a[..., :3]
    mx, mn = rgb.max(2), rgb.min(2)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    h = np.where(mx - mn < 1e-6, 0, h)
    return a, h, s, v


def _rgb(h, s, v):
    h = (h % 360) / 60.0
    c = v * s
    x = c * (1 - np.abs(h % 2 - 1))
    m = v - c
    z = np.zeros_like(h)
    i = np.floor(h).astype(int) % 6
    rs = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [c, x, z, z, x, c])
    gs = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [x, c, c, x, z, z])
    bs = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [z, z, x, c, c, x])
    return np.stack([rs + m, gs + m, bs + m], -1)


def rehue(img, lo, hi, hue, *, sat=None, sat_min=0.25, sat_max=1.01, gain=1.0, box=None):
    """Pixels whose hue is in [lo, hi] (degrees, wrapping) and saturation at
    least ``sat_min`` take ``hue`` (and ``sat`` if given), keeping their light
    and shade. ``box`` (x0, y0, x1, y1) limits it to a part of the picture."""
    a, h, s, v = _hsv(img)
    if lo <= hi:
        sel = (h >= lo) & (h <= hi)
    else:
        sel = (h >= lo) | (h <= hi)
    sel &= (s >= sat_min) & (s <= sat_max) & (a[..., 3] > 0)
    sel &= ~((np.abs(a[..., :3] * 255 - np.array(OUTLINE[:3])).sum(2)) < 14)
    if box:
        m = np.zeros_like(sel)
        x0, y0, x1, y1 = box
        m[y0:y1, x0:x1] = True
        sel &= m
    nh = np.full_like(h, float(hue))
    ns = s if sat is None else np.clip(s * 0 + sat, 0, 1)
    nv = np.clip(v * gain, 0, 1)
    new = _rgb(nh, ns, nv)
    out = a.copy()
    out[..., :3] = np.where(sel[..., None], new, a[..., :3])
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def tint_grey(img, colour, *, sat_max=0.22, vmin=0.18, vmax=0.86, box=None, mix=1.0):
    """Weakly coloured pixels (steel, grey cloth) between ``vmin`` and
    ``vmax`` in value take ``colour``, keeping their shading; ``mix`` < 1 only
    leans them toward it."""
    a, h, s, v = _hsv(img)
    sel = (s <= sat_max) & (v >= vmin) & (v <= vmax) & (a[..., 3] > 0)
    sel &= ~((np.abs(a[..., :3] * 255 - np.array(OUTLINE[:3])).sum(2)) < 14)
    if box:
        m = np.zeros_like(sel)
        x0, y0, x1, y1 = box
        m[y0:y1, x0:x1] = True
        sel &= m
    c = np.array(colour, np.float32) / 255.0
    lum = (a[..., :3] * np.array([0.30, 0.59, 0.11])).sum(2)
    ramp = np.where(lum[..., None] <= 0.5, c * (lum[..., None] / 0.5),
                    c + (1 - c) * ((lum[..., None] - 0.5) / 0.5) * 0.8)
    new = a[..., :3] * (1 - mix) + ramp * mix
    out = a.copy()
    out[..., :3] = np.where(sel[..., None], new, a[..., :3])
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def darken_grey(img, k):
    """Steel and grey cloth made darker (blackened iron), colours left alone."""
    a, h, s, v = _hsv(img)
    sel = (s <= 0.22) & (a[..., 3] > 0)
    out = a.copy()
    out[..., :3] = np.where(sel[..., None], a[..., :3] * k, a[..., :3])
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def luma_ramp(img, dark, mid, light):
    """Every pixel recoloured along one ramp by its light: a ghost's blue made
    the gold of Valhalla's light. Outline pixels stay outline."""
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = (a[..., :3] * np.array([0.30, 0.59, 0.11])).sum(2)
    lo, hi = lum[a[..., 3] > 0].min(), lum[a[..., 3] > 0].max()
    t = np.clip((lum - lo) / max(1e-6, hi - lo), 0, 1)[..., None]
    d, m, li = (np.array(c, np.float32) / 255.0 for c in (dark, mid, light))
    col = np.where(t < 0.5, d + (m - d) * (t / 0.5), m + (li - m) * ((t - 0.5) / 0.5))
    out = a.copy()
    keep = (np.abs(a[..., :3] * 255 - np.array(OUTLINE[:3])).sum(2)) < 14
    out[..., :3] = np.where(keep[..., None], a[..., :3], col)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def crown(img, cx, top, w=9):
    """A small gold crown, three points, outlined, its base at ``top`` + 4."""
    im = img.copy()
    d = ImageDraw.Draw(im)
    x0, x1 = cx - w // 2, cx + w // 2
    dark, mid, lite = (120, 80, 20, 255), GOLD + (255,), (255, 236, 150, 255)
    d.rectangle([x0 - 1, top + 2, x1 + 1, top + 5], fill=OUTLINE)
    for px in (x0, cx, x1):
        d.rectangle([px - 1, top - 1, px + 1, top + 2], fill=OUTLINE)
    d.rectangle([x0, top + 3, x1, top + 4], fill=mid)
    d.line([(x0, top + 4), (x1, top + 4)], fill=dark)
    for px in (x0, cx, x1):
        d.point([(px, top), (px, top + 1), (px, top + 2)], fill=mid)
        d.point([(px, top)], fill=lite)
    d.point([(cx, top + 3)], fill=(200, 40, 40, 255))
    return im


def feather(img, pts, colour=(200, 40, 40, 255)):
    im = img.copy()
    d = ImageDraw.Draw(im)
    d.line(pts, fill=OUTLINE, width=3)
    d.line(pts, fill=colour, width=1)
    return im


def flip(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def erase(img, box):
    im = img.copy()
    ImageDraw.Draw(im).rectangle(box, fill=(0, 0, 0, 0))
    return im


def outline(img):
    """A dark outline round every opaque shape (after a paste or an erase)."""
    a = np.asarray(img).copy()
    alpha = a[..., 3] > 0
    grown = alpha.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        grown |= np.roll(np.roll(alpha, dy, 0), dx, 1)
    edge = grown & ~alpha
    a[edge] = OUTLINE
    return Image.fromarray(a, 'RGBA')


def paste(base, part, pos, size):
    p = part.resize((size, size), Image.NEAREST)
    im = base.copy()
    im.alpha_composite(p, pos)
    return im


# ---------------------------------------------------------------- the figures

def _m(n):
    return load(os.path.join(MON, n + '.png'))


def _i(n):
    return load(os.path.join(ITM, n + '.png'))


def knight(red_hue=None, white=None, red_sat=None, steel=None, do_flip=False, crown_at=None):
    im = _m('veteran_knight')
    if red_hue is not None:
        # below the head: the face and beard keep their own colours
        im = rehue(im, 330, 20, red_hue, sat=red_sat, sat_min=0.30, box=(14, 12, 64, 64))
    if white is not None:
        # the shield's white band and the tabard's light trim (x 38..56, y 14..46)
        im = tint_grey(im, white, sat_max=0.20, vmin=0.70, vmax=1.0, box=(38, 14, 58, 46))
    if steel is not None:
        im = tint_grey(im, steel, mix=0.35)
    if crown_at:
        im = crown(im, *crown_at)
    return flip(im) if do_flip else im


def build():
    out = {}
    # Robin Hood's band ---------------------------------------------------
    j = _m('bandit_thug')
    j = rehue(j, 300, 358, GREEN, sat=0.45, sat_min=0.08, sat_max=0.50, box=(18, 19, 50, 38))
    j = tint_grey(j, (95, 70, 45), sat_max=0.25, vmin=0.2, vmax=0.85, box=(14, 36, 50, 60))
    out['little_john'] = j
    out['yeoman_archer'] = flip(rehue(_m('bandit_archer'), 120, 200, GREEN, sat=0.55, gain=1.15))
    w = _m('bandit_captain')
    w = rehue(w, 330, 25, 2, sat=0.85, gain=1.1, sat_min=0.62, box=(0, 12, 64, 64))
    w = tint_grey(w, (70, 110, 50), sat_max=0.22, vmin=0.25, vmax=0.78, box=(26, 15, 52, 34))
    out['will_scarlet'] = flip(w)
    t = _m('cult_priest')
    t = rehue(t, 330, 30, 28, sat=0.50, gain=0.85)
    out['friar_tuck'] = t
    m = _m('npc_young_thief')
    m = rehue(m, 30, 75, GREEN, sat=0.50, gain=0.85, box=(0, 17, 64, 40))
    out['much_the_millers_son'] = m
    a = _m('npc_scholar')
    a = rehue(a, 200, 280, 355, sat=0.65)
    a = tint_grey(a, (70, 110, 50), sat_max=0.20, vmin=0.25, vmax=0.80, box=(30, 20, 62, 56))
    out['alan_a_dale'] = flip(a)
    r = rehue(_m('bandit_archer'), 120, 200, GREEN + 5, sat=0.65, gain=1.25)
    out['npc_robin_hood'] = feather(r, [(34, 11), (39, 6)])

    # The sleepers under the hill -------------------------------------------
    out['king_arthur'] = knight(white=GOLD, crown_at=(31, 0))
    out['sir_lancelot'] = knight(red_hue=345, red_sat=0.65, steel=(240, 230, 205), do_flip=True)
    out['sir_gawain'] = knight(red_hue=350, white=GOLD, do_flip=True)
    p = _m('npc_young_knight')
    p = rehue(p, 190, 250, 358, sat=0.75)
    out['sir_percival'] = p
    out['sir_bedivere'] = knight(red_hue=280, red_sat=0.55, do_flip=True)
    out['sir_kay'] = knight(red_hue=28, red_sat=0.80)
    sk = crown(_m('npc_fallen_paladin'), 29, 0, w=11)
    out['npc_sleeping_king'] = sk

    # Valhalla ----------------------------------------------------------------
    out['einherjar'] = luma_ramp(_m('einherjar_ghost'), (90, 50, 20), (205, 150, 60), (255, 240, 190))

    # Charlemagne's host ------------------------------------------------------
    c = _m('wild_hunt_captain')
    c = tint_grey(c, (40, 60, 150), sat_max=0.30, vmin=0.05, vmax=0.45, box=(18, 14, 64, 52))
    c = tint_grey(c, GOLD, sat_max=0.25, vmin=0.55, vmax=1.0, box=(22, 0, 44, 10))
    out['charlemagne'] = c
    out['duke_naimes'] = knight(red_hue=135, red_sat=0.55, do_flip=True)
    out['ogier_the_dane'] = flip(darken_grey(knight(red_hue=355, red_sat=0.9), 0.62))
    out['frankish_knight'] = knight(red_hue=225, red_sat=0.70, white=GOLD)

    # Heimdall: the white god with Gjallarhorn in place of the orb
    h = _m('npc_divine')
    h = erase(h, (41, 5, 55, 20))
    h = tint_grey(h, (235, 235, 245), sat_max=0.35, vmin=0.4, vmax=1.0, box=(0, 0, 64, 64), mix=0.5)
    items = build_items()
    h = paste(h, items['gjallarhorn'], (38, 3), 19)
    out['npc_heimdall'] = outline(h)
    return out, items


def build_items():
    o = _i('olifant')
    robin = rehue(o, 30, 60, 30, sat=0.55, gain=0.55, sat_min=0.0)           # ivory: brown horn
    robin = rehue(robin, 30, 60, 25, sat=0.80, gain=0.45, sat_min=0.6)      # the gold bands: dark brass
    robin = tint_grey(robin, (150, 105, 60), sat_max=0.20, vmin=0.4, vmax=1.0)
    d = ImageDraw.Draw(robin)
    d.line([(10, 24), (24, 12), (40, 12), (50, 20)], fill=OUTLINE, width=3)
    d.line([(10, 24), (24, 12), (40, 12), (50, 20)], fill=(60, 120, 50, 255), width=1)
    arthur = flip(tint_grey(rehue(o, 35, 60, 210, sat=0.12, gain=1.0, sat_min=0.5),
                            (215, 205, 175), sat_max=0.25, vmin=0.4, vmax=1.0, mix=0.6))
    g = rehue(o, 30, 60, 44, sat=0.85, gain=1.0, sat_min=0.55)                # the bands: gold
    g = rehue(g, 0, 360, 25, sat=0.35, gain=0.40, sat_min=0.0, sat_max=0.54)  # the horn: dark aurochs
    g = tint_grey(g, (90, 75, 60), sat_max=0.25, vmin=0.3, vmax=1.0)
    big = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    gs = g.resize((76, 76), Image.NEAREST).rotate(-12, resample=Image.NEAREST)
    big.alpha_composite(gs.crop((6, 6, 70, 70)))
    return {'robin_hoods_horn': outline(robin), 'arthurs_bugle': arthur, 'gjallarhorn': outline(big)}


MONSTER_IDS = ('little_john', 'will_scarlet', 'friar_tuck', 'much_the_millers_son', 'alan_a_dale',
               'yeoman_archer', 'king_arthur', 'sir_lancelot', 'sir_gawain', 'sir_percival',
               'sir_bedivere', 'sir_kay', 'einherjar', 'charlemagne', 'duke_naimes',
               'ogier_the_dane', 'frankish_knight', 'npc_robin_hood', 'npc_sleeping_king',
               'npc_heimdall')


def sheet(pics, path):
    K = 3
    cell = 64 * K + 10
    names = list(pics)
    cols = 7
    rows = (len(names) + cols - 1) // cols
    im = Image.new('RGBA', (cols * cell, rows * (cell + 14)), (34, 30, 38, 255))
    d = ImageDraw.Draw(im)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * (cell + 14)
        tile = Image.new('RGBA', (64, 64), (58, 54, 50, 255))
        tile.alpha_composite(pics[n])
        im.alpha_composite(tile.resize((64 * K, 64 * K), Image.NEAREST), (x + 5, y + 5))
        d.text((x + 5, y + 64 * K + 6), n, fill=(240, 230, 200, 255))
    im.save(path)


def _write_json(path, obj, indent):
    import json
    txt = json.dumps(obj, indent=indent, ensure_ascii=False).replace('\n', '\r\n') + '\r\n'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def record_installed(items):
    """The install manifests the art tests read: the ally kinds with the
    monsters (installed.json), the three people with the NPCs
    (installed_rest.json), the horns with the items (installed_items.json)."""
    import json
    gen = os.path.join(HERE, 'installed.json')
    mons = set(json.load(open(gen, encoding='utf-8')))
    mons |= {n for n in MONSTER_IDS if not n.startswith('npc_')}
    _write_json(gen, sorted(mons), 2)
    rest_p = os.path.join(HERE, 'installed_rest.json')
    rest = json.load(open(rest_p, encoding='utf-8'))
    rest['monsters'] = sorted(set(rest.get('monsters', ())) | {n for n in MONSTER_IDS if n.startswith('npc_')})
    _write_json(rest_p, rest, 0)
    it_p = os.path.join(HERE, 'installed_items.json')
    it = json.load(open(it_p, encoding='utf-8'))
    it['items'] = sorted(set(it.get('items', ())) | set(items))
    _write_json(it_p, it, 2)


def main(argv):
    monsters, items = build()
    for n in MONSTER_IDS:
        monsters[n].save(os.path.join(MON, n + '.png'))
    for n, im in items.items():
        im.save(os.path.join(ITM, n + '.png'))
    record_installed(items)
    if '--sheet' in argv:
        allp = dict(monsters)
        allp.update(items)
        sheet(allp, argv[argv.index('--sheet') + 1])
    print(f'{len(MONSTER_IDS)} sprites, {len(items)} items')


if __name__ == '__main__':
    main(sys.argv[1:])
