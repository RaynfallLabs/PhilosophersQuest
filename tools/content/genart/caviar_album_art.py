"""Caviar and Tater Tots (3.5.2): the art cut from Brandon's album cover.

    py tools/content/genart/caviar_album_art.py COVER.webp OUT_DIR

COVER is the 1024 x 1024 cover of "Caviar and Tater Tots" (A Man Before a
King); it is not kept in the repo. Writes, into OUT_DIR:

  caviar.png, tater_tots.png              the two foods (assets/tiles/items)
  song_caviar_and_tater_tots.png          the dish: the whole plate (assets/tiles/items)
  caviar_and_tater_tots_badge.png         the achievement (assets/achievements/caviar_and_tater_tots.png)

and *_review.png / sheet.png to look at. Each object is cut with drawn
shapes, in the cover's own pixels: the jar's dark glass is the background's
colour, so a brightness threshold loses it.
"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

SRC, OUT = sys.argv[1], sys.argv[2]
im = Image.open(SRC).convert('RGB')
W, H = im.size


def caviar(d):
    # Jar: rim ellipse and body (its foot is in the ice).
    d.ellipse((218, 484, 448, 530), fill=255)
    d.rectangle((222, 505, 444, 610), fill=255)
    # Ice heaped over the ramekin's rim.
    d.ellipse((150, 540, 520, 625), fill=255)
    # Ramekin: rim, tapered body, round foot.
    d.polygon([(148, 585), (522, 585), (492, 800), (178, 800)], fill=255)
    d.ellipse((176, 780, 494, 818), fill=255)


def caviar_alone(d):
    # On its own the ramekin stops above the dip bowl (which hides its foot
    # in the cover), with a round foot of its own.
    d.ellipse((218, 484, 448, 530), fill=255)
    d.rectangle((222, 505, 444, 610), fill=255)
    d.ellipse((150, 540, 520, 625), fill=255)
    d.polygon([(148, 585), (522, 585), (501, 735), (169, 735)], fill=255)
    d.ellipse((169, 718, 501, 752), fill=255)


def tots(d):
    d.polygon([(522, 562), (540, 505), (568, 462), (612, 440), (622, 398), (660, 378),
               (708, 383), (738, 425), (790, 433), (838, 452), (868, 492), (908, 515),
               (912, 540), (866, 820), (780, 832), (606, 826), (560, 700)], fill=255)


def plate(d):
    d.ellipse((98, 680, 908, 982), fill=255)


def dip(d):
    # The dip bowl in front: cut out of the caviar and the tots alone.
    d.ellipse((310, 722, 712, 940), fill=0)


def mask(*shapes):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for s in shapes:
        s(d)
    return m.filter(ImageFilter.GaussianBlur(2.0))


def cut(m, name, size=64, pad=2, lift=1.35):
    src = ImageEnhance.Brightness(im).enhance(lift)     # the cover is lit low for a dark tile
    rgba = src.convert('RGBA')
    rgba.putalpha(m)
    bb = m.point(lambda v: 255 if v > 20 else 0).getbbox()
    obj = rgba.crop(bb)
    w, h = obj.size
    s = (size - 2 * pad) / max(w, h)
    small = obj.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    tile = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    tile.paste(small, ((size - small.width) // 2, size - pad - small.height), small)
    tile.save(f'{OUT}/{name}.png')
    big = obj.copy()
    big.thumbnail((360, 360))
    bg = Image.new('RGBA', big.size, (60, 140, 60, 255))
    bg.alpha_composite(big)
    bg.save(f'{OUT}/{name}_review.png')


def sheet(names):
    tiles = [Image.open(f'{OUT}/{n}.png') for n in names]
    sh = Image.new('RGBA', (len(tiles) * 256, 512), (0, 0, 0, 255))
    for i, t in enumerate(tiles):
        for j, c in enumerate([(32, 30, 38, 255), (205, 195, 175, 255)]):
            cell = Image.new('RGBA', (64, 64), c)
            cell.alpha_composite(t)
            sh.paste(cell.resize((256, 256), Image.NEAREST), (i * 256, j * 256))
    sh.save(f'{OUT}/sheet.png')


def badge(name='caviar_and_tater_tots_badge'):
    """The plate in a circle, 128 px (the game draws the rarity frame)."""
    src = ImageEnhance.Brightness(im).enhance(1.3)
    cx, cy, r = 505, 660, 352
    sq = src.crop((cx - r, cy - r, cx + r, cy + r)).resize((512, 512), Image.LANCZOS)
    m = Image.new('L', (512, 512), 0)
    ImageDraw.Draw(m).ellipse((4, 4, 508, 508), fill=255)
    sq = sq.convert('RGBA')
    sq.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
    sq.resize((128, 128), Image.LANCZOS).save(f'{OUT}/{name}.png')


if __name__ == '__main__':
    cut(mask(caviar_alone), 'caviar')
    cut(mask(tots, dip), 'tater_tots')
    cut(mask(plate, caviar, tots), 'song_caviar_and_tater_tots')
    sheet(['caviar', 'tater_tots', 'song_caviar_and_tater_tots'])
    badge()
