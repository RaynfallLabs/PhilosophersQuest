"""So Then I Was Like... (3.5.2): the badge from Brandon's album cover.

    py tools/content/genart/math_is_cool_album_art.py COVER.webp OUT_DIR

COVER is the 1024 x 1536 cover of "So Then I Was Like..." (A Man Before a
King); it is not kept in the repo. The title is painted out (its letters
filled from the dark background around them, a little grain on top), then
the reaper and the young man writing through the night are cut as a round
128 px badge (the game draws the rarity frame): math_is_cool_badge.png,
installed as assets/achievements/so_then_i_was_like.png.
"""
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
im = Image.open(SRC).convert('RGB')
a = np.asarray(im).astype(float)
lum = a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
mask = np.zeros(lum.shape, bool)
y0, y1, x0, x1 = 150, 440, 60, 700           # the title's box
mask[y0:y1, x0:x1] = lum[y0:y1, x0:x1] > 95
for (bx0, by0, bx1, by1) in [(530, 120, 660, 310), (690, 330, 800, 460)]:
    mask[by0:by1, bx0:bx1] = False            # the skull and the reaper's hand stay
mk = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0


def box(x, r):
    for axis in (0, 1):
        p = np.pad(x, [(r + 1, r) if i == axis else (0, 0) for i in range(x.ndim)], mode='edge')
        c = np.cumsum(p, axis=axis)
        hi = [slice(None)] * x.ndim
        lo = [slice(None)] * x.ndim
        n = x.shape[axis]
        hi[axis] = slice(2 * r + 1, 2 * r + 1 + n)
        lo[axis] = slice(0, n)
        x = (c[tuple(hi)] - c[tuple(lo)]) / (2 * r + 1)
    return x


def blur(x, r):
    for _ in range(3):
        x = box(x, r)
    return x


filled = a.copy()
w = (~mk).astype(float)
left = mk.copy()
for rad in (4, 8, 16, 32, 64):
    num = np.stack([blur(filled[..., c] * w, rad) for c in range(3)], -1)
    den = blur(w, rad)
    est = num / np.maximum(den, 1e-6)[..., None]
    take = left & (den > 0.2)
    filled[take] = est[take]
    w = np.where(take, 1.0, w)
    left &= ~take
grain = np.random.default_rng(1).normal(0, 4, a.shape)
filled[mk] = np.clip(filled[mk] + grain[mk], 0, 255)
clean = Image.fromarray(np.clip(filled, 0, 255).astype(np.uint8))

src = ImageEnhance.Brightness(clean).enhance(1.25)
cx, cy, r = 554, 640, 470          # inside the cover on every side
sq = src.crop((cx - r, cy - r, cx + r, cy + r)).resize((512, 512), Image.LANCZOS)
m = Image.new('L', (512, 512), 0)
ImageDraw.Draw(m).ellipse((4, 4, 508, 508), fill=255)
sq = sq.convert('RGBA')
sq.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
sq.resize((128, 128), Image.LANCZOS).save(f'{OUT}/math_is_cool_badge.png')
view = Image.new('RGBA', (256, 256), (40, 40, 50, 255))
view.alpha_composite(sq.resize((256, 256), Image.LANCZOS))
view.save(f'{OUT}/math_is_cool_badge_review.png')
