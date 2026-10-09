"""The sprite style (2026-10): shared painting and finishing code.

Offline tooling (not loaded at runtime).

Each sprite is painted as flat colour regions, then one finishing pass gives
every region a lit top-left edge, a shaded bottom-right edge, a tinted dark
outline, a glow around anything that emits light, and a ground shadow.
"""
import colorsys
from PIL import Image, ImageDraw

S = 32


def shade(c, k):
    """k steps lighter (+) or darker (-), with the hue drifting warm in the
    light and cool in the shadow, the way hand-made pixel ramps do."""
    r, g, b = [v / 255 for v in c[:3]]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    for _ in range(abs(k)):
        if k > 0:
            v = min(1.0, v * 1.22 + 0.03)
            s *= 0.86
            h += ((0.14 - h + 0.5) % 1 - 0.5) * 0.12
        else:
            v *= 0.70
            s = min(1.0, s * 1.12 + 0.02)
            h += ((0.70 - h + 0.5) % 1 - 0.5) * 0.10
    r, g, b = colorsys.hsv_to_rgb(h % 1, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


class Sprite:
    def __init__(self):
        self.img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.glow = set()          # colours that emit light: never shaded, haloed
        self.shadow = True       # ground shadow: on for creatures, off for icons and tiles
        self.outline = True      # off for floor/wall tiles that must fill the square

    # painting ---------------------------------------------------------
    def rect(self, x0, y0, x1, y1, c): self.d.rectangle([x0, y0, x1, y1], fill=c + (255,))
    def ell(self, x0, y0, x1, y1, c): self.d.ellipse([x0, y0, x1, y1], fill=c + (255,))
    def poly(self, pts, c): self.d.polygon(pts, fill=c + (255,))
    def line(self, pts, c, w=1): self.d.line(pts, fill=c + (255,), width=w)

    def px(self, pts, c):
        for x, y in pts:
            if 0 <= x < S and 0 <= y < S:
                self.img.putpixel((x, y), c + (255,))

    def lit(self, c):
        self.glow.add(c)
        return c

    # finishing --------------------------------------------------------
    def finish(self):
        src = self.img.load()
        base = [[src[x, y] for x in range(S)] for y in range(S)]

        def at(x, y):
            return base[y][x] if 0 <= x < S and 0 <= y < S else (0, 0, 0, 0)

        out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        o = out.load()
        for y in range(S):
            for x in range(S):
                c = at(x, y)
                if c[3] == 0:
                    continue
                rgb = c[:3]
                if rgb in self.glow:
                    o[x, y] = c
                    continue
                up, lf, dn, rt = at(x, y - 1), at(x - 1, y), at(x, y + 1), at(x + 1, y)
                lit = up != c or lf != c
                dark = dn != c or rt != c
                # an edge against a glowing neighbour catches its light
                near_glow = any(n[3] and n[:3] in self.glow for n in (up, lf, dn, rt))
                k = 1 if (lit and not dark) or near_glow else (-1 if dark and not lit else 0)
                o[x, y] = shade(rgb, k) + (255,)
        # outline and glow
        for y in range(S):
            for x in range(S):
                if at(x, y)[3]:
                    continue
                nb = [at(x + dx, y + dy) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))]
                nb = [n for n in nb if n[3]]
                if not nb:
                    continue
                g = [n for n in nb if n[:3] in self.glow]
                if g:
                    o[x, y] = g[0][:3] + (110,)
                elif self.outline:
                    r, gg, b = shade(nb[0][:3], -2)
                    o[x, y] = ((r + 18) // 3, (gg + 10) // 3, (b + 30) // 3, 255)
        if self.shadow:
            sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse([7, 28, 24, 31], fill=(0, 0, 0, 70))
            out = Image.alpha_composite(sh, out)
        return out


# ---------------------------------------------------------------- palette
BONE = (226, 220, 198)
IVORY = (238, 230, 200)
STEEL = (170, 176, 190)
IRON = (104, 108, 122)
WOOD = (132, 92, 52)
LEATHER = (120, 78, 46)
DARK = (44, 36, 44)
GOLD = (226, 178, 62)
STRING = (210, 210, 200)


