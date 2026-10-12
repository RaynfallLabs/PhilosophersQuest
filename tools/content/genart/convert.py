"""Generated picture -> game sprite, the same way every time.

The generator is asked for a flat key-colour background (magenta, or green for a
purple creature). Everything of that hue is background wherever it sits, so the
gap between two legs goes and so does any shadow on the ground. The figure is
then shrunk to the tile size, lifted a little (a painting shrinks darker than it
looks), cut to a small set of colours and outlined.

Run with ComfyUI's Python (it has numpy, scipy and Pillow).
"""
import colorsys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

TILE = 64
COLOURS = 32
OUTLINE = (20, 16, 24)
LIFT_GAMMA = 0.82
LIFT_COLOUR = 1.15
KEYS = {'magenta': (255, 0, 255), 'green': (0, 255, 0), 'blue': (0, 0, 255)}
WORK = 1024                                  # the mask is made at this size (full size: a bowstring is 3 px wide)
SOLID = 0.43                                 # a sprite pixel is kept when the figure covers this much of it...
THIN = 0.10                                  # ...or this much, where the figure is a thin thing (a bow, a wand, a blade)


def _hsv(a):
    r, g, b = a[..., 0] / 255.0, a[..., 1] / 255.0, a[..., 2] / 255.0
    mx, mn = a.max(2) / 255.0, a.min(2) / 255.0
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    return h / 6.0, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx


def figure_mask(im, key='magenta'):
    """(rgb float array at WORK size, bool mask of the figure, facts about the cut)."""
    a = np.asarray(im.convert('RGB').resize((WORK, WORK), Image.LANCZOS)).astype(np.float32)
    h, s, v = _hsv(a)
    kh = colorsys.rgb_to_hsv(*[c / 255.0 for c in KEYS[key]])[0]
    # A painted style shades its backdrop and drifts it (magenta towards crimson), so
    # read the backdrop's real hue off the rim of the picture when the rim is coloured.
    rim = np.zeros(h.shape, bool); rim[:10] = rim[-10:] = True; rim[:, :10] = rim[:, -10:] = True
    rim &= s > 0.5
    if rim.mean() > 0.02:
        ang = h[rim] * 2 * np.pi
        seen = (np.arctan2(np.sin(ang).mean(), np.cos(ang).mean()) / (2 * np.pi)) % 1.0
        if min(abs(seen - kh), 1 - abs(seen - kh)) < 0.2:
            kh = seen
    dh = np.abs(h - kh); dh = np.minimum(dh, 1 - dh)
    back = (dh < 0.075) & (s > 0.42) & (v > 0.16)          # the key colour, lit or in shadow
    # The fringe: a pixel beside the backdrop that is still mostly the backdrop's colour.
    # (This used to grow the backdrop by a pixel all round, which ate thin things whole:
    # a bow limb, a wand, a crossbow's arms.)
    back |= ndi.binary_dilation(back, iterations=2) & (dh < 0.10) & (s > 0.28) & (v > 0.16)
    fig = ~back
    lab, n = ndi.label(fig)
    parts = 0
    if n:
        sizes = ndi.sum(fig, lab, range(1, n + 1))
        big = max(sizes)
        keep = [i + 1 for i, sz in enumerate(sizes) if sz >= big * 0.012]
        parts = len(keep)
        fig = np.isin(lab, keep)
    edge = np.concatenate([fig[0], fig[-1], fig[:, 0], fig[:, -1]])
    border_key = np.concatenate([back[:3].ravel(), back[-3:].ravel(), back[:, :3].ravel(), back[:, -3:].ravel()])
    facts = {
        'parts': parts,                                    # separate pieces that survived
        'coverage': float(fig.mean()),                     # how much of the frame the figure fills
        'touches_edge': float(edge.mean()),                # cropped by the frame?
        'background_ok': float(border_key.mean()),         # the frame's rim really is the key colour
    }
    return a, fig, facts


def to_sprite(im, key='magenta', tile=TILE, colours=COLOURS):
    """(RGBA sprite Image of tile x tile, facts)."""
    a, fig, facts = figure_mask(im, key)
    if not fig.any():
        return Image.new('RGBA', (tile, tile)), dict(facts, empty=True)
    ys, xs = np.where(fig)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    side = max(y1 - y0, x1 - x0)
    canvas = np.zeros((side, side, 4), np.float32)
    oy, ox = side - (y1 - y0), (side - (x1 - x0)) // 2     # stand on the bottom edge, centred
    canvas[oy:oy + y1 - y0, ox:ox + x1 - x0, :3] = a[y0:y1, x0:x1] * fig[y0:y1, x0:x1, None]
    canvas[oy:oy + y1 - y0, ox:ox + x1 - x0, 3] = fig[y0:y1, x0:x1] * 255
    inner = tile - 2                                       # room for the outline
    small = np.asarray(Image.fromarray(canvas.astype(np.uint8), 'RGBa').resize((inner, inner), Image.BOX)).astype(np.float32)
    al = small[..., 3:4]
    rgb = np.where(al > 0, small[..., :3] * 255.0 / np.maximum(al, 1), 0)
    # Thin things are whatever an opening removes: parts narrower than about one sprite
    # pixel. They never cover half of any pixel, so they get their own, lower bar;
    # otherwise the archer loses his bow and the shaman her rattle.
    px_per = max(1.0, side / float(inner))
    r = max(1, int(round(px_per * 0.6)))
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    disk = (xx * xx + yy * yy) <= r * r
    whole = canvas[..., 3] > 0
    thin = whole & ~ndi.binary_opening(whole, structure=disk)
    thin_cov = np.asarray(Image.fromarray((thin * 255).astype(np.uint8)).resize((inner, inner), Image.BOX)).astype(np.float32) / 255.0
    solid = (al[..., 0] > SOLID * 255) | (thin_cov > THIN)
    facts['thin_pixels'] = int(((thin_cov > THIN) & ~(al[..., 0] > SOLID * 255)).sum())
    # A painted figure's soft shadows average down to mud at this size: lift the
    # midtones and put a little colour back. Black and white stay where they are.
    rgb = 255.0 * (np.clip(rgb, 0, 255) / 255.0) ** LIFT_GAMMA
    grey = rgb.mean(2, keepdims=True)
    rgb = np.clip(grey + (rgb - grey) * LIFT_COLOUR, 0, 255)
    # a small fixed number of colours, chosen from this sprite's own pixels
    px = rgb[solid].astype(np.uint8)
    if len(px):
        q = Image.fromarray(px.reshape(1, -1, 3), 'RGB').quantize(min(colours, max(2, len(px))), method=Image.MEDIANCUT, kmeans=6)
        rgb[solid] = np.asarray(q.convert('RGB')).reshape(-1, 3)
    out = np.zeros((tile, tile, 4), np.uint8)
    out[1:-1, 1:-1, :3] = rgb
    out[1:-1, 1:-1, 3] = solid * 255
    full = out[..., 3] > 0
    ring = ndi.binary_dilation(full) & ~full
    out[ring] = (*OUTLINE, 255)
    facts['sprite_fill'] = float((out[..., 3] > 0).mean())
    return Image.fromarray(out, 'RGBA'), facts
