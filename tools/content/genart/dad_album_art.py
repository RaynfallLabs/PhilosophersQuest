"""Dad Is Here! (3.5.2): the badge from Brandon's album cover for "The
Greatest Trainer of All Time" (A Man Before a King), the song Dad and his
special attacks come from.

    py tools/content/genart/dad_album_art.py COVER.webp OUT_DIR

COVER is the 1024 x 1536 cover (Dad in his red headband and "World's
Greatest Dad" shirt); it is not kept in the repo. Writes a round 128 px
badge (the game draws the rarity frame), dad_badge.png, installed as
assets/achievements/dad_is_here.png, and dad_badge_review.png to look at.
"""
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
im = Image.open(SRC).convert('RGB')
src = ImageEnhance.Brightness(im).enhance(1.15)
cx, cy, r = 505, 425, 360          # headband, face and the shirt's words
sq = src.crop((cx - r, cy - r, cx + r, cy + r)).resize((512, 512), Image.LANCZOS)
m = Image.new('L', (512, 512), 0)
ImageDraw.Draw(m).ellipse((4, 4, 508, 508), fill=255)
sq = sq.convert('RGBA')
sq.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
sq.resize((128, 128), Image.LANCZOS).save(f'{OUT}/dad_badge.png')
view = Image.new('RGBA', (256, 256), (40, 40, 50, 255))
view.alpha_composite(sq.resize((256, 256), Image.LANCZOS))
view.save(f'{OUT}/dad_badge_review.png')
