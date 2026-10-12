"""One drawn template, many materials.

A weapon or armour template is drawn once with its MATERIAL part in plain neutral
grey (grips, straps and strings in their own colours). `tint` gives that grey part
a material's colour and leaves everything coloured alone, so an iron longsword, a
bronze one and a mithril one are the same sword, the same size, in the same place.
"""
import numpy as np
from PIL import Image

OUTLINE = (20, 16, 24)
GREY_SAT = 0.20          # a pixel with less colour than this is the material
MID = 0.52               # the grey that becomes exactly the material's colour


def tint(sprite, colour, grey_sat=GREY_SAT):
    a = np.asarray(sprite.convert('RGBA')).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    outline = (np.abs(rgb - np.array(OUTLINE)).sum(2) < 12)
    # painted steel leans a little blue-green: a cool, weakly coloured pixel is still the material
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cool = (b >= r) & (g >= r * 0.98) & (sat < 0.45)
    part = (alpha > 0) & ((sat < grey_sat) | cool) & ~outline
    lum = (rgb * np.array([0.30, 0.59, 0.11])).sum(2) / 255.0
    c = np.array(colour, np.float32)
    dark = c[None, None] * (lum / MID)[..., None]                       # shadows: the colour, darker
    lite = c[None, None] + (255 - c[None, None]) * (((lum - MID) / (1 - MID)) * 0.85)[..., None]   # highlights: towards white
    new = np.where((lum <= MID)[..., None], dark, lite)
    out = a.copy()
    out[..., :3] = np.where(part[..., None], np.clip(new, 0, 255), rgb)
    return Image.fromarray(out.astype(np.uint8), 'RGBA')
