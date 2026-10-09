"""Food slice: recipes (dishes), monster parts, foraged ingredients, rations.

Offline tooling.  draw(rec) -> 32x32 RGBA.  `python food.py` writes out/<folder>/<id>.png
"""
import json, os, sys, zlib, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image, ImageDraw
import core
from core import Sprite, shade, BONE, IVORY, STEEL, IRON, WOOD, LEATHER, DARK, GOLD

WHITE = (244, 242, 232)
STEAM = (232, 234, 240)
CREAM = (232, 222, 196)
GLASS = (176, 208, 216)
CORK = (176, 132, 84)
LEAF = (86, 150, 70)
MEAT = (186, 70, 62)
FAT = (240, 220, 196)
CRUST = (206, 150, 74)
BROWN = (140, 84, 48)


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


# ------------------------------------------------------------------ palette
# keyword -> (main colour, glow colour or None).  Earliest keyword in the id wins.
PAL = [
    ('black_dragon', (58, 60, 78), (150, 220, 90)), ('red_dragon', (196, 48, 40), (255, 170, 60)),
    ('sea_dragon', (40, 140, 150), None), ('undead_dragon', (150, 160, 120), (140, 240, 150)),
    ('sea_serpent', (40, 130, 150), None), ('sea_snake', (60, 150, 170), None),
    ('world_serpent', (50, 120, 110), (120, 230, 200)), ('jormungandr', (50, 120, 110), (120, 230, 200)),
    ('swamp_serpent', (96, 120, 60), None), ('serpent_pepper', (206, 52, 40), None),
    ('dragon_salt', (240, 226, 214), (255, 150, 70)), ('void_salt', (150, 120, 200), (200, 160, 255)),
    ('ember_spice', (214, 84, 36), (255, 190, 80)), ('cave_mushroom', (200, 170, 130), None),
    ('petrified_mushroom', (150, 148, 150), None), ('mandrake', (176, 140, 96), None),
    ('nightshade', (104, 60, 150), None), ('valerian', (226, 170, 200), None),
    ('rosemary', (70, 130, 84), None), ('wild_thyme', (110, 160, 80), None), ('thyme', (110, 160, 80), None),
    ('celery', (190, 214, 150), None), ('carrot', (232, 130, 44), None), ('garlic', (236, 230, 214), None),
    ('frost_giant', (150, 190, 226), (210, 240, 255)), ('stone_giant', (140, 138, 140), (255, 190, 90)),
    ('winter_wolf', (214, 226, 240), (190, 230, 255)), ('wendigo', (170, 200, 220), (190, 240, 255)),
    ('frost', (150, 200, 236), (210, 240, 255)), ('ice', (160, 214, 240), (220, 246, 255)),
    ('rime', (190, 220, 240), (220, 246, 255)), ('glace', (170, 214, 240), (220, 246, 255)),
    ('magma', (200, 70, 30), (255, 180, 60)), ('ember', (220, 96, 36), (255, 200, 90)),
    ('fire', (226, 90, 30), (255, 200, 80)), ('flame', (226, 90, 30), (255, 200, 80)),
    ('cacus', (190, 80, 40), (255, 180, 60)), ('amon', (170, 50, 40), (255, 150, 60)),
    ('torch', (226, 110, 40), (255, 200, 80)), ('blackened', (60, 52, 56), None),
    ('charred', (64, 54, 54), (240, 120, 50)), ('smoked', (120, 84, 64), None), ('ash', (150, 146, 144), None),
    ('abyss', (60, 40, 110), (150, 110, 255)), ('abyzou', (70, 60, 110), (160, 150, 255)),
    ('void', (60, 40, 96), (180, 120, 255)), ('shadow', (64, 50, 90), (170, 120, 255)),
    ('nightwing', (50, 44, 80), (150, 110, 240)), ('night_hag', (90, 60, 110), (220, 110, 240)),
    ('midnight', (50, 50, 100), (150, 150, 255)), ('darkmantle', (70, 56, 84), None),
    ('samael', (50, 44, 60), (160, 240, 120)), ('seal', (150, 40, 50), (255, 210, 110)),
    ('seven_seals', (150, 40, 50), (255, 210, 110)), ('wormwood', (110, 130, 110), (170, 230, 150)),
    ('pit_fiend', (170, 36, 36), (255, 160, 60)), ('infernal', (190, 50, 70), (255, 150, 90)),
    ('demon', (160, 40, 50), (255, 130, 60)), ('devil', (176, 44, 44), (255, 140, 60)),
    ('dretch', (140, 150, 110), None), ('quasit', (96, 140, 80), None), ('imp', (190, 60, 50), None),
    ('erinyes', (120, 36, 50), None), ('vrock', (120, 130, 110), None), ('marilith', (90, 150, 110), None),
    ('bael', (150, 60, 50), (255, 150, 60)), ('beleth', (130, 110, 90), (255, 200, 90)),
    ('buer', (150, 170, 70), (200, 240, 90)), ('mammon', (210, 170, 60), (255, 230, 120)),
    ('ravana', (180, 60, 90), (255, 190, 90)), ('rangda', (190, 60, 50), (255, 220, 120)),
    ('demi_lich', (210, 206, 180), (120, 240, 200)), ('death_mage', (80, 70, 110), (140, 240, 170)),
    ('lich', (190, 200, 170), (130, 240, 170)), ('necro', (80, 90, 80), (140, 240, 150)),
    ('death', (70, 70, 84), (150, 240, 160)), ('grave', (120, 110, 96), None),
    ('crypt', (130, 124, 120), None), ('barrow', (140, 126, 100), None), ('tomb', (140, 136, 130), None),
    ('ossuary', (214, 206, 180), None), ('charnel', (160, 150, 130), None), ('cairn', (130, 132, 136), None),
    ('wight', (130, 170, 180), (170, 240, 240)), ('wraith', (110, 130, 170), (170, 210, 255)),
    ('spectral', (140, 190, 210), (190, 240, 255)), ('revenant', (110, 120, 140), (150, 200, 255)),
    ('ghast', (130, 150, 110), None), ('jiangshi', (120, 170, 150), (180, 250, 200)),
    ('pale_master', (200, 200, 214), (220, 220, 255)), ('hollow', (150, 150, 170), (200, 200, 255)),
    ('mohrg', (150, 100, 110), None), ('zombie', (120, 140, 96), None), ('rotted', (116, 124, 80), None),
    ('plague', (150, 160, 70), (200, 230, 90)), ('corrupt', (120, 70, 140), (200, 110, 240)),
    ('elder_vampire', (120, 20, 36), (255, 80, 90)), ('vampire', (150, 26, 40), None),
    ('strigoi', (140, 40, 60), None), ('vrykolakas', (120, 30, 40), None), ('redcap', (190, 30, 30), None),
    ('thrall', (150, 60, 60), None), ('alpha_lycan', (130, 20, 30), (255, 220, 150)),
    ('lycan', (150, 40, 40), None), ('homunculus', (200, 110, 120), None), ('hobgoblin', (190, 90, 50), None),
    ('goblin', (110, 150, 70), None), ('orc', (110, 120, 70), None), ('bugbear', (150, 100, 60), None),
    ('gnoll', (170, 140, 90), None), ('kobold', (180, 100, 70), None), ('ogre', (160, 140, 90), None),
    ('troglodyte', (120, 130, 90), None), ('troll', (80, 140, 90), None), ('green_knight', (50, 150, 80), (140, 240, 140)),
    ('green_slime', (100, 190, 70), None), ('gray_slime', (150, 154, 160), None), ('black_ooze', (40, 40, 50), None),
    ('ochre', (204, 150, 50), None), ('slime', (110, 190, 90), None), ('kuo_toa', (90, 160, 150), None),
    ('aboleth', (110, 150, 140), None), ('mouther', (190, 130, 140), None), ('gibbering', (200, 130, 170), (250, 180, 220)),
    ('toxic', (140, 200, 60), (190, 250, 90)), ('jelly', (160, 200, 220), None),
    ('basilisk', (110, 140, 90), (200, 240, 110)), ('cockatrice', (200, 170, 70), None),
    ('medusa', (80, 150, 110), (160, 240, 150)), ('echidna', (110, 150, 70), None), ('hydra', (70, 140, 110), None),
    ('lamia', (190, 150, 70), None), ('yuan_ti', (150, 170, 60), None), ('naga', (60, 150, 130), None),
    ('python', (140, 120, 60), None), ('lindworm', (110, 150, 130), None), ('wyvern', (120, 110, 80), None),
    ('komodo', (120, 120, 90), None), ('crocodile', (90, 120, 70), None), ('lizard', (120, 170, 90), None),
    ('behir', (70, 110, 190), (150, 220, 255)), ('nidhoggr', (70, 60, 50), (150, 230, 110)),
    ('yggdrasil', (120, 90, 50), (150, 230, 110)), ('snake', (110, 160, 70), None),
    ('serpent', (80, 150, 90), None), ('drow', (110, 60, 150), None), ('phase', (110, 130, 230), (170, 200, 255)),
    ('spider_queen', (120, 40, 110), None), ('queen', (130, 40, 110), None), ('arachne', (130, 70, 130), None),
    ('ettercap', (150, 140, 110), None), ('anansi', (150, 90, 40), (255, 210, 110)),
    ('spider', (90, 70, 90), None), ('scorpion', (190, 130, 50), None), ('wasp', (226, 180, 40), None),
    ('mantis', (120, 180, 80), None), ('death_beetle', (50, 60, 80), None), ('beetle', (60, 90, 110), None),
    ('scarab', (40, 150, 150), (255, 210, 90)), ('khepri', (40, 110, 180), (255, 210, 90)),
    ('swarmlord', (130, 60, 50), None), ('insect', (120, 100, 60), None), ('chitin', (130, 96, 60), None),
    ('hook_horror', (90, 84, 96), None), ('grick', (130, 110, 120), None), ('grell', (150, 120, 150), None),
    ('otyugh', (150, 120, 90), None), ('roper', (140, 130, 120), None), ('piercer', (130, 126, 130), None),
    ('lurker', (110, 110, 120), None), ('trapper', (130, 120, 104), None), ('cloaker', (70, 70, 100), None),
    ('displacer', (60, 50, 110), (150, 130, 255)), ('nothic', (110, 140, 120), (170, 250, 150)),
    ('cyclops', (70, 130, 200), None), ('hag', (200, 190, 110), None), ('witch', (120, 150, 90), None),
    ('crone', (150, 130, 170), (220, 200, 255)), ('baba_yaga', (150, 120, 90), None),
    ('nemean', (224, 180, 70), (255, 236, 150)), ('sphinx', (220, 180, 90), (255, 236, 150)),
    ('golden', (236, 190, 60), (255, 240, 150)), ('gold', (236, 190, 60), (255, 240, 150)),
    ('mimic', (226, 180, 60), None), ('lion', (206, 160, 80), None), ('manticore', (190, 120, 60), None),
    ('chimera', (190, 110, 60), (255, 180, 80)), ('griffin', (200, 170, 110), None),
    ('owlbear', (140, 100, 70), None), ('peryton', (120, 140, 120), None), ('harpy', (150, 130, 150), None),
    ('raven', (40, 44, 70), None), ('eagle', (130, 90, 56), None), ('roc', (190, 160, 110), None),
    ('anzu', (220, 170, 70), (255, 240, 150)), ('tengu', (60, 50, 60), None), ('camazotz', (90, 50, 70), None),
    ('bat', (96, 72, 70), None), ('rat', (140, 120, 110), None), ('wolf', (130, 130, 140), None),
    ('hero_hound', (200, 160, 100), None), ('death_dog', (90, 70, 70), None), ('pack_lord', (200, 196, 176), None),
    ('fenrir', (90, 96, 120), (190, 220, 255)), ('cerberus', (90, 50, 50), (255, 150, 70)),
    ('bear', (130, 86, 54), None), ('blink', (150, 170, 230), (200, 220, 255)), ('hare', (190, 160, 130), None),
    ('cath_palug', (70, 60, 70), None), ('nue', (190, 150, 90), None), ('ugallu', (200, 150, 80), None),
    ('kusarikku', (140, 96, 60), None), ('minotaur', (140, 90, 60), None), ('catoblepas', (96, 100, 80), None),
    ('satyr', (170, 130, 80), None), ('unicorn', (236, 230, 240), (230, 170, 255)),
    ('each_uisce', (50, 110, 130), None), ('puca', (60, 56, 70), None), ('winged', (236, 232, 220), None),
    ('frog', (120, 180, 90), None), ('bullywug', (100, 160, 100), None),
    ('talos', (190, 130, 70), (255, 170, 70)), ('bronze', (196, 140, 66), None), ('brass', (220, 180, 80), None),
    ('clockwork', (200, 160, 80), None), ('iron', (110, 114, 128), None), ('silver', (200, 206, 220), None),
    ('sentinel', (150, 156, 170), None), ('guardian', (160, 160, 150), (120, 220, 255)),
    ('dread_plate', (60, 60, 76), (255, 80, 70)), ('enchanted_plate', (150, 170, 210), (170, 220, 255)),
    ('horseman', (90, 90, 104), (255, 90, 70)), ('executioner', (90, 92, 104), None),
    ('golem', (150, 140, 130), (120, 220, 255)), ('primordial_clay', (160, 96, 70), (255, 190, 100)),
    ('clay', (180, 110, 76), None), ('stone', (140, 140, 144), None), ('mineral', (120, 160, 190), (190, 230, 255)),
    ('crystal', (150, 200, 230), (210, 240, 255)), ('carbuncle', (220, 40, 60), (255, 130, 130)),
    ('pearl', (236, 232, 240), (255, 250, 255)), ('charybdis', (40, 110, 160), None),
    ('scylla', (60, 120, 130), None), ('elemental_air', (200, 226, 240), (236, 250, 255)),
    ('elemental_water', (50, 130, 220), (150, 210, 255)), ('cloud', (220, 230, 244), (245, 250, 255)),
    ('storm', (80, 110, 190), (255, 240, 130)), ('tempest', (80, 110, 190), (255, 240, 130)),
    ('titan', (190, 150, 90), (255, 230, 140)), ('elemental', (150, 120, 200), (255, 200, 110)),
    ('wisp', (120, 220, 230), (200, 250, 255)), ('pixie', (240, 160, 220), (255, 220, 250)),
    ('soul', (150, 210, 240), (220, 245, 255)), ('astral', (120, 120, 220), (200, 200, 255)),
    ('arcane', (120, 90, 220), (190, 170, 255)), ('chaos', (200, 60, 190), (255, 150, 240)),
    ('changeling', (170, 200, 220), (220, 240, 255)), ('solar', (240, 200, 70), (255, 245, 170)),
    ('archon', (240, 214, 120), (255, 248, 190)), ('herald', (226, 186, 80), (255, 240, 160)),
    ('inquisitor', (170, 40, 40), None), ('patriarch', (220, 180, 70), None), ('assassin', (60, 80, 60), None),
    ('cultist', (130, 50, 130), (220, 130, 240)), ('shaman', (150, 100, 60), None),
    ('set', (190, 150, 90), (255, 90, 60)), ('jackal', (190, 150, 90), None), ('desert', (220, 190, 120), None),
    ('thoth', (30, 40, 90), (120, 200, 255)), ('erlking', (90, 110, 60), (190, 240, 110)),
    ('heartwood', (160, 96, 50), (255, 200, 100)), ('spriggan', (110, 120, 60), None),
    ('assassin_vine', (70, 130, 60), None), ('vine', (80, 150, 70), None), ('enchanted_wood', (150, 104, 60), (150, 230, 255)),
    ('myconid', (170, 130, 190), None), ('violet_fungus', (140, 80, 180), None), ('crimson', (200, 50, 60), None),
    ('sovereign', (190, 150, 60), None), ('yellow', (226, 200, 60), None), ('brown_mold', (130, 96, 60), None),
    ('musk', (220, 190, 110), None), ('spore', (170, 190, 110), (220, 240, 150)), ('glowing', (120, 230, 190), (190, 255, 220)),
    ('fungi', (120, 150, 180), None), ('mushroom', (200, 160, 120), None), ('moss', (100, 150, 90), None),
    ('lucky', (70, 170, 80), None), ('fomorian', (170, 170, 140), None), ('giant', (226, 216, 190), None),
    ('skeletal', (226, 220, 198), None), ('bone', (226, 220, 198), None), ('odin', (90, 110, 170), (190, 220, 255)),
    ('wild_hunt', (90, 110, 150), (190, 220, 255)), ('philosopher', (120, 90, 200), (255, 220, 120)),
    ('royal', (150, 40, 130), None), ('hercules', (200, 150, 80), None), ('predator', (170, 80, 60), None),
    ('hunter', (120, 130, 70), None), ('fallen', (110, 100, 120), None), ('destroyer', (90, 40, 110), (230, 110, 255)),
    ('devourer', (80, 60, 100), (200, 130, 255)), ('horror', (100, 60, 120), None), ('cerebral', (220, 150, 170), None),
    ('brain', (226, 150, 160), None), ('eye', (90, 150, 200), None),
]
PAL_ALIAS = [('medusa', 'snake')]


def palette(i):
    hits = []
    for k, (kw, c, g) in enumerate(PAL):
        p = i.find(kw)
        if p >= 0:
            hits.append((p, -len(kw), k, c, g))
    hits.sort()
    # drop keywords covered by a longer earlier hit at an overlapping place
    out, spans = [], []
    for p, nl, k, c, g in hits:
        if any(a <= p < b for a, b in spans):
            continue
        spans.append((p, p - nl)); out.append((c, g))
    return out


class Ctx:
    def __init__(self, rec):
        self.id = i = rec['id']
        self.cat = rec.get('category', '')
        self.h = zlib.crc32(i.encode())
        self.r = random.Random(self.h)
        self.core = i[7:] if i.startswith('recipe_') else i
        ps = palette(self.core)
        if ps:
            self.m, self.g = ps[0]
        else:
            import colorsys
            hh = (self.h % 360) / 360
            r, g, b = colorsys.hsv_to_rgb(hh, 0.55, 0.8)
            self.m, self.g = (int(r * 255), int(g * 255), int(b * 255)), None
        self.a = ps[1][0] if len(ps) > 1 else shade(self.m, 1)
        self.g2 = ps[1][1] if len(ps) > 1 else None
        self.all = ps

    def has(self, *kws):
        return any(k in self.core for k in kws)

    def glow(self, s, default=None):
        g = self.g or self.g2 or default
        return s.lit(g) if g else None


def stip(s, base, c2, f):
    px = s.img.load()
    for y in range(32):
        for x in range(32):
            p = px[x, y]
            if p[3] and p[:3] == base and f(x, y):
                px[x, y] = c2 + (255,)


def clear(s, pts):
    for x, y in pts:
        if 0 <= x < 32 and 0 <= y < 32:
            s.img.putpixel((x, y), (0, 0, 0, 0))


def mirror(s):
    s.img = s.img.transpose(Image.FLIP_LEFT_RIGHT)
    s.d = ImageDraw.Draw(s.img)


def new():
    s = Sprite(); s.shadow = False
    return s


def sparkle(s, c, col, n=4, box=(3, 3, 28, 12)):
    for _ in range(n):
        x, y = c.r.randint(box[0], box[2]), c.r.randint(box[1], box[3])
        if not s.img.getpixel((x, y))[3]:
            s.px([(x, y)], col)


def steam(s, xs=(11, 16, 21), top=2, bot=9):
    st = s.lit(STEAM)
    for k, x in enumerate(xs):
        for y in range(top + (k % 2), bot):
            s.px([(x + (1 if (y + k) % 4 < 2 else 0), y)], st)


# ------------------------------------------------------------------ garnish
HERBS = ['rosemary', 'thyme', 'nightshade', 'valerian', 'mandrake', 'cave_mushroom', 'petrified_mushroom',
         'ember_spice', 'serpent_pepper', 'void_salt', 'dragon_salt', 'celery', 'carrot', 'garlic', 'herb', 'mushroom',
         'pepper']


def herb_of(c):
    for hname in HERBS:
        if hname in c.core:
            return hname
    return None


def garnish(s, c, x, y, kind=None):
    """small garnish about 6x5 at x,y (top-left)."""
    kind = kind or herb_of(c) or ['parsley', 'lemon', 'berries'][c.h % 3]
    if kind in ('rosemary', 'thyme', 'herb', 'parsley'):
        g = (70, 140, 80) if kind != 'thyme' else (120, 170, 80)
        s.line([(x, y + 4), (x + 5, y)], (60, 100, 60))
        s.px([(x + 1, y + 2), (x + 2, y + 1), (x + 3, y + 3), (x + 4, y), (x + 2, y + 4), (x + 5, y + 2), (x, y + 3)], g)
        if kind == 'thyme':
            s.px([(x + 5, y), (x + 3, y)], (220, 170, 220))
    elif kind == 'nightshade':
        s.poly([(x, y + 2), (x + 3, y), (x + 5, y + 2), (x + 3, y + 4)], (90, 60, 140))
        s.px([(x + 5, y + 4)], (40, 30, 70)); s.px([(x + 4, y + 4)], (60, 40, 110))
    elif kind == 'valerian':
        s.px([(x + 1, y), (x + 3, y), (x + 2, y + 1), (x + 4, y + 1), (x, y + 1)], (240, 190, 214))
        s.line([(x + 2, y + 2), (x + 2, y + 4)], (90, 140, 80))
    elif kind == 'mandrake':
        s.poly([(x + 1, y + 1), (x + 4, y + 1), (x + 4, y + 3), (x + 5, y + 5), (x + 3, y + 3), (x + 1, y + 5)], (190, 150, 100))
        s.px([(x + 2, y), (x + 3, y - 1), (x + 1, y - 1)], LEAF)
    elif kind in ('cave_mushroom', 'mushroom', 'petrified_mushroom'):
        cap = (196, 150, 110) if kind != 'petrified_mushroom' else (150, 150, 156)
        s.rect(x + 2, y + 2, x + 3, y + 4, CREAM); s.ell(x, y, x + 5, y + 3, cap)
    elif kind in ('ember_spice',):
        e = s.lit((255, 170, 60))
        s.px([(x, y + 1), (x + 2, y), (x + 4, y + 2), (x + 1, y + 3), (x + 5, y), (x + 3, y + 4)], (210, 70, 30))
        s.px([(x + 2, y + 2)], e)
    elif kind in ('serpent_pepper', 'pepper'):
        s.poly([(x, y + 1), (x + 3, y + 1), (x + 5, y + 4), (x + 2, y + 3)], (210, 44, 36)); s.px([(x, y), (x - 1, y)], LEAF)
    elif kind == 'void_salt':
        v = s.lit((200, 160, 255))
        s.px([(x, y + 2), (x + 2, y), (x + 4, y + 3), (x + 3, y + 1), (x + 1, y + 4)], (236, 226, 250))
        s.px([(x + 2, y + 2), (x + 5, y + 1)], v)
    elif kind == 'dragon_salt':
        s.px([(x, y + 2), (x + 2, y), (x + 4, y + 3), (x + 3, y + 1), (x + 1, y + 4), (x + 5, y + 1)], WHITE)
        s.px([(x + 2, y + 2)], (240, 130, 60))
    elif kind == 'celery':
        s.rect(x + 1, y, x + 2, y + 4, (190, 220, 150)); s.rect(x + 3, y + 1, x + 4, y + 4, (160, 200, 120))
    elif kind == 'carrot':
        s.poly([(x, y + 1), (x + 2, y), (x + 5, y + 4), (x + 4, y + 4)], (236, 130, 40)); s.px([(x, y), (x + 1, y - 1)], LEAF)
    elif kind == 'garlic':
        s.ell(x + 1, y + 1, x + 5, y + 5, (240, 234, 220)); s.px([(x + 3, y)], (240, 234, 220))
    elif kind == 'lemon':
        s.ell(x, y, x + 5, y + 4, (244, 214, 70)); s.px([(x + 2, y + 2), (x + 3, y + 2)], (250, 240, 170))
    else:
        s.ell(x, y + 1, x + 2, y + 3, (190, 40, 60)); s.ell(x + 3, y, x + 5, y + 2, (190, 40, 60)); s.px([(x + 2, y)], LEAF)


# ------------------------------------------------------------------ crockery
BOWLS = [(150, 100, 60), (182, 100, 66), (150, 156, 170), (70, 112, 176), (226, 214, 190), (74, 74, 88),
         (120, 150, 110), (196, 140, 66)]


def bowl(s, c, liquid, deep=False, mat=None):
    b = mat or BOWLS[c.h % len(BOWLS)]
    rim = shade(b, 1)
    top = 13 if deep else 15
    s.poly([(4, top + 3), (27, top + 3), (25, 25), (21, 28), (10, 28), (6, 25)], b)
    s.rect(12, 28, 19, 29, shade(b, -1))
    s.ell(3, top, 28, top + 7, rim)
    s.ell(5, top + 1, 26, top + 6, liquid)
    if c.h % 3 == 0:
        s.line([(6, 22), (25, 22)], shade(b, -1))
    elif c.h % 3 == 1:
        s.px([(8 + 3 * k, 22 + (k % 2)) for k in range(6)], rim)
    return top


def plate(s, c, mat=None):
    mats = [(232, 226, 210), (150, 156, 170), (160, 110, 66), (200, 214, 226), (226, 200, 150)]
    b = mat or mats[c.h % len(mats)]
    s.ell(2, 17, 29, 29, b)
    s.ell(5, 19, 26, 27, shade(b, -1) if sum(b) > 500 else shade(b, 1))
    return b


def board(s, c):
    w = (164, 116, 70)
    s.poly([(3, 20), (26, 18), (29, 24), (6, 27)], w)
    s.line([(6, 22), (26, 20)], shade(w, -1)); s.line([(8, 25), (27, 23)], shade(w, -1))
    s.rect(1, 20, 3, 23, w)


def bottle(s, c, liquid, glow=None, shape=None):
    shape = c.h % 5 if shape is None else shape
    liq = s.lit(liquid) if glow else liquid
    if shape == 0:      # round flask
        s.rect(13, 5, 18, 13, GLASS); s.ell(6, 11, 25, 29, GLASS); s.ell(8, 15, 23, 27, liq)
        s.rect(8, 15, 23, 17, GLASS); s.rect(9, 18, 22, 19, liq); s.rect(13, 2, 18, 5, CORK)
        s.px([(10, 20), (10, 21), (11, 19)], WHITE)
    elif shape == 1:    # tall vial
        s.rect(11, 6, 20, 28, GLASS); s.rect(13, 13, 18, 26, liq); s.rect(10, 5, 21, 6, shade(GLASS, 1))
        s.rect(12, 2, 19, 5, CORK); s.px([(13, 15), (13, 16), (13, 18)], WHITE); s.rect(11, 9, 20, 10, LEATHER)
    elif shape == 2:    # squat jar
        s.rect(6, 12, 25, 28, GLASS); s.rect(8, 16, 23, 26, liq); s.rect(9, 8, 22, 12, GLASS)
        s.rect(8, 5, 23, 8, CORK); s.px([(9, 18), (9, 19), (10, 17)], WHITE); s.line([(9, 10), (22, 10)], (206, 184, 130))
    elif shape == 3:    # conical
        s.poly([(13, 10), (18, 10), (26, 27), (24, 29), (7, 29), (5, 27)], GLASS)
        s.poly([(12, 17), (19, 17), (23, 26), (8, 26)], liq); s.rect(13, 5, 18, 10, GLASS); s.rect(13, 2, 18, 5, CORK)
        s.px([(11, 20), (10, 22)], WHITE)
    else:               # faceted phial with stopper
        s.poly([(16, 9), (24, 16), (22, 27), (16, 30), (10, 27), (8, 16)], GLASS)
        s.poly([(16, 14), (21, 18), (20, 25), (16, 27), (12, 25), (11, 18)], liq)
        s.rect(14, 5, 18, 9, GLASS); s.ell(13, 1, 19, 6, GOLD); s.px([(12, 19), (12, 20)], WHITE)
    if glow:
        sparkle(s, c, s.lit(glow), 3, (4, 2, 27, 9))


# ================================================================== PARTS
def p_fang(s, c):
    tooth = IVORY if not c.has('charnel', 'death_dog', 'strigoi') else (214, 204, 170)
    if c.has('tusk'):
        s.poly([(6, 27), (12, 28), (20, 22), (25, 13), (26, 3), (21, 10), (15, 17), (8, 20)], tooth)
        s.ell(3, 19, 13, 29, c.m); s.px([(22, 12), (23, 9), (19, 16)], WHITE)
        rime = s.lit((220, 246, 255)); s.px([(26, 2), (24, 6), (27, 6), (20, 13), (16, 19)], rime)
        return
    if c.has('tooth'):
        s.poly([(9, 5), (22, 5), (24, 12), (21, 20), (19, 28), (16, 19), (13, 28), (10, 20), (8, 12)], tooth)
        s.rect(8, 3, 23, 7, c.m)
    else:
        s.poly([(10, 6), (21, 6), (22, 12), (19, 20), (14, 29), (14, 21), (10, 13)], tooth)
        s.rect(9, 3, 22, 7, shade(c.m, 0)); s.line([(15, 10), (16, 20)], shade(tooth, -1))
        if c.has('sets', 'jackal'):
            s.rect(9, 3, 22, 5, GOLD); s.px([(15, 4), (16, 4)], (40, 150, 170))
    g = c.glow(s) if c.g else None
    if c.has('serpent', 'snake', 'fenrir', 'scylla', 'strigoi', 'devourer', 'swamp'):
        d = s.lit(c.g or ((150, 220, 80) if not c.has('strigoi') else (220, 40, 50)))
        s.px([(14, 30), (15, 30)] if not c.has('tooth') else [(13, 29), (19, 29)], d)
    if g:
        s.px([(12, 9), (12, 10)], g)
    if c.h & 1:
        mirror(s)


def p_claw(s, c):
    horn = (70, 60, 70) if not c.has('sphinx', 'ugallu', 'cath') else (226, 214, 180)
    if c.has('talon'):
        horn = (60, 56, 64)
        s.poly([(12, 3), (20, 3), (21, 12), (17, 14), (12, 12)], (226, 180, 70))
        s.line([(12, 6), (20, 6)], (170, 120, 40)); s.line([(12, 9), (21, 9)], (170, 120, 40))
        s.poly([(12, 12), (21, 12), (24, 19), (22, 27), (16, 30), (19, 23), (17, 17)], horn)
        s.poly([(12, 8), (7, 12), (5, 19), (8, 15), (12, 12)], horn)
    elif c.has('mantis'):
        g = c.m
        s.line([(6, 27), (10, 12)], g, 4); s.line([(10, 12), (24, 5)], g, 4); s.line([(24, 5), (27, 16), (22, 26)], shade(g, -1), 3)
        for k in range(5):
            s.px([(13 + k * 2, 13 - k), (13 + k * 2, 14 - k)], IVORY)
        s.ell(7, 9, 13, 15, shade(g, 1)); s.px([(22, 27), (21, 28)], DARK)
    elif c.has('hook'):
        s.poly([(7, 28), (12, 29), (15, 16), (20, 9), (27, 9), (28, 5), (20, 3), (13, 7), (9, 15)], c.m)
        s.line([(11, 26), (13, 16), (18, 8)], shade(c.m, 1)); s.ell(5, 24, 14, 30, shade(c.m, -1))
    else:
        s.poly([(7, 7), (15, 4), (22, 8), (26, 16), (24, 27), (21, 19), (16, 13), (9, 13)], horn)
        s.ell(3, 3, 14, 14, c.m); s.px([(6, 6), (9, 8), (7, 10), (10, 5)], shade(c.m, 1))
        s.px([(19, 10), (22, 14)], shade(horn, 2))
        if c.g:
            s.px([(24, 28), (25, 25)], s.lit(c.g))
    if c.h & 1:
        mirror(s)


def p_horn(s, c):
    if c.has('antler'):
        b = (206, 184, 140)
        s.line([(8, 28), (12, 18), (15, 8), (20, 2)], b, 3)
        s.line([(12, 18), (20, 15), (24, 9)], b, 2); s.line([(14, 11), (8, 7), (7, 2)], b, 2)
        s.line([(20, 15), (26, 16)], b, 2); s.ell(5, 25, 12, 30, c.m)
        return
    if c.has('unicorn', 'corrupted'):
        s.poly([(8, 27), (14, 28), (25, 3), (23, 2)], (236, 230, 240))
        for k in range(5):
            s.line([(10 + 3 * k, 26 - 5 * k), (13 + 3 * k, 22 - 5 * k)], (190, 180, 210))
        t = s.lit((200, 110, 240))
        s.px([(9, 27), (11, 28), (13, 25), (12, 22), (15, 20)], (100, 50, 130)); s.px([(24, 3), (5, 24), (17, 27)], t)
        clear(s, [(8, 27), (10, 28), (13, 28)])
        return
    if c.has('wild_hunt'):
        s.poly([(4, 10), (9, 6), (14, 14), (20, 20), (27, 22), (29, 27), (22, 28), (13, 23), (7, 17)], (220, 206, 170))
        s.rect(3, 6, 9, 11, GOLD); s.line([(20, 20), (22, 28)], GOLD, 2); s.line([(12, 13), (9, 20)], GOLD, 2)
        s.line([(6, 5), (14, 3), (24, 8), (27, 21)], (150, 40, 40)); s.px([(28, 25)], s.lit((190, 220, 255)))
        return
    base = {'demon': (120, 30, 40), 'minotaur': (226, 214, 180), 'satyr': (176, 140, 90),
            'catoblepas': (90, 96, 84), 'kusarikku': (60, 50, 50)}
    b = next((v for k, v in base.items() if k in c.core), c.m)
    if c.has('satyr'):   # ram curl
        s.d.arc([5, 6, 27, 28], 100, 400, fill=b + (255,), width=6)
        s.d.arc([12, 13, 22, 23], 20, 250, fill=b + (255,), width=4)
        for k in range(7):
            import math
            a = math.radians(120 + k * 40)
            x, y = 16 + 9 * math.cos(a), 17 + 9 * math.sin(a)
            s.line([(x - 2 * math.cos(a), y - 2 * math.sin(a)), (x + 2 * math.cos(a), y + 2 * math.sin(a))], shade(b, -1))
        s.rect(9, 24, 15, 29, shade(b, -2))
        return
    s.poly([(5, 25), (12, 28), (19, 21), (24, 12), (27, 3), (20, 9), (13, 15), (7, 19)], b)
    for k in range(4):
        s.line([(8 + 3 * k, 19 - 2 * k), (12 + 3 * k, 25 - 3 * k)], shade(b, -1))
    s.poly([(27, 3), (24, 8), (25, 11)], shade(b, -2) if sum(b) > 400 else shade(b, 2))
    s.ell(3, 21, 13, 30, shade(b, -1))
    if c.g:
        s.px([(26, 2), (22, 7)], s.lit(c.g))
    if c.h & 1:
        mirror(s)


def p_spike(s, c):
    if c.has('quill'):
        s.poly([(5, 27), (7, 28), (27, 5), (26, 3)], IVORY)
        for k in range(5):
            s.line([(8 + 4 * k, 24 - 4 * k), (10 + 4 * k, 22 - 4 * k)], (60, 50, 50), 2)
        s.px([(27, 3), (28, 2)], (40, 36, 40))
    elif c.has('thorn'):
        s.line([(3, 26), (28, 22)], (80, 110, 60), 4)
        s.poly([(10, 23), (16, 22), (14, 6)], c.m if not c.has('spriggan') else (120, 90, 50))
        s.poly([(19, 21), (24, 21), (25, 11)], shade(c.m, -1)); s.px([(14, 5)], s.lit((190, 250, 90)) if c.has('toxic') else WHITE)
    elif c.has('spine'):
        for k, (x, y) in enumerate(((4, 26), (9, 27), (14, 28))):
            s.poly([(x, y - 3), (x + 4, y + 1), (x + 13 + k, y - 22 + k * 2)], (70, 56, 50) if k != 1 else c.m)
        s.ell(2, 22, 19, 30, shade(c.m, -1))
    else:  # stinger / barb
        s.poly([(8, 18), (14, 24), (28, 3), (25, 4)], (60, 50, 56) if not c.has('imp') else (120, 30, 30))
        s.ell(3, 16, 15, 29, c.m); s.px([(6, 19), (8, 22), (11, 25)], shade(c.m, 1))
        if c.has('barb'):
            s.poly([(18, 13), (15, 8), (20, 10)], (60, 50, 56)); s.poly([(21, 15), (26, 16), (23, 11)], (60, 50, 56))
        s.px([(29, 2), (28, 1)], s.lit(c.g or (170, 240, 90)))
    if c.h & 1:
        mirror(s)


def scale1(s, x, y, col, hi):
    s.poly([(x + 2, y), (x + 9, y), (x + 11, y + 3), (x + 11, y + 7)], col); s.ell(x, y, x + 11, y + 13, col)
    s.line([(x + 2, y + 9), (x + 5, y + 11), (x + 9, y + 9)], hi); s.px([(x + 2, y + 2), (x + 3, y + 2)], hi)


def p_scale(s, c):
    hi = shade(c.m, 2)
    scale1(s, 2, 2, shade(c.m, -1), c.m); scale1(s, 18, 4, shade(c.m, -1), c.m); scale1(s, 9, 15, shade(c.m, 1), hi); scale1(s, 10, 8, c.m, hi)
    if c.has('lamia', 'python', 'yuan'):
        s.px([(15, 18), (16, 19), (15, 20), (16, 21), (8, 9), (22, 10)], c.a)
    if c.g:
        s.px([(16, 24), (9, 5), (23, 6)], s.lit(c.g))
    if c.h & 1:
        mirror(s)


def p_pelt(s, c):
    f = c.m
    if c.has('scrap'):
        s.poly([(6, 7), (14, 5), (25, 8), (27, 16), (22, 26), (12, 24), (5, 20), (8, 14)], f)
    else:
        s.poly([(9, 3), (13, 5), (19, 5), (23, 3), (24, 8), (28, 9), (28, 14), (23, 13), (23, 20), (28, 23), (27, 28),
                (21, 25), (16, 29), (11, 25), (5, 28), (4, 23), (9, 20), (9, 13), (4, 14), (4, 9), (8, 8)], f)
    if c.has('skin', 'lindworm', 'lurker'):
        stip(s, f, shade(f, -1), lambda x, y: (x + (y // 3) * 2) % 4 == 0 and y % 3 == 0)
        s.line([(16, 6), (16, 27)], shade(f, 1))
    else:
        stip(s, f, shade(f, -1), lambda x, y: (x * 5 + y * 3) % 11 == 0)
        if not c.has('scrap'):
            s.poly([(13, 9), (19, 9), (20, 22), (16, 25), (12, 22)], shade(f, 1) if sum(f) < 600 else shade(f, -1))
    if c.has('bugbear', 'hero_hound'):
        s.px([(11, 12), (21, 16), (12, 21), (20, 10)], shade(f, -2))
    if c.g:
        sparkle(s, c, s.lit(c.g), 0); s.px([(16, 14), (14, 18), (18, 19)], s.lit(c.g))
    if c.has('shadow'):
        s.px([(2, 6), (29, 20), (3, 18)], s.lit(c.g))


def p_shell(s, c):
    m = c.m
    if c.has('piercer'):
        s.poly([(8, 3), (24, 3), (22, 10), (20, 18), (17, 29), (15, 29), (12, 18), (10, 10)], m)
        for y in (8, 13, 18, 23):
            s.line([(10 + (y - 8) // 4, y), (22 - (y - 8) // 4, y - 2)], shade(m, -1))
        s.rect(7, 2, 25, 4, shade(m, 1)); return
    if c.has('beak'):
        s.poly([(5, 8), (14, 5), (22, 9), (28, 20), (24, 18), (16, 17), (8, 18)], c.m)
        s.poly([(8, 18), (16, 17), (22, 22), (14, 24)], shade(c.m, -1)); s.px([(11, 10), (12, 10)], DARK)
        s.rect(3, 7, 6, 18, (190, 60, 50)); return
    if c.has('plate', 'swarmlord', 'chitin', 'mantis', 'insect'):
        s.poly([(6, 9), (16, 4), (26, 9), (27, 20), (16, 28), (5, 20)], m)
        s.line([(6, 14), (16, 10), (26, 14)], shade(m, -1)); s.line([(6, 19), (16, 15), (26, 19)], shade(m, -1))
        s.line([(16, 5), (16, 27)], shade(m, 1)); s.px([(10, 9), (11, 8)], shade(m, 2))
    else:
        s.ell(4, 6, 27, 27, m); s.line([(16, 7), (16, 27)], shade(m, -2)); s.rect(6, 5, 25, 9, shade(m, -1))
        s.px([(9, 12), (9, 13), (10, 11), (20, 12), (20, 13)], shade(m, 2))
        s.line([(7, 17), (14, 15)], shade(m, -1)); s.line([(18, 15), (25, 17)], shade(m, -1))
        if c.has('scarab', 'khepri'):
            s.rect(6, 5, 25, 7, GOLD); s.ell(13, 1, 19, 6, s.lit((255, 210, 90)))
            s.px([(10, 20), (22, 20), (12, 23), (20, 23)], GOLD)
    if c.g and not c.has('scarab', 'khepri'):
        s.px([(16, 16), (16, 20)], s.lit(c.g))


def p_feather(s, c):
    m = c.m
    tip = {'eagle': WHITE, 'griffin': WHITE, 'owlbear': (90, 60, 40), 'tengu': (190, 40, 40), 'anzu': (255, 240, 170),
           'erinyes': (40, 30, 40), 'vrock': (190, 180, 120), 'storm': (255, 240, 130), 'void': (180, 120, 255),
           'bronze': (240, 200, 120), 'raven': (80, 90, 150), 'corrupted': (150, 70, 190)}
    t = next((v for k, v in tip.items() if k in c.core), shade(m, 2))
    if c.has('corrupted'):
        m = (232, 230, 236)
    s.poly([(24, 3), (27, 7), (25, 14), (19, 21), (12, 25), (9, 23), (10, 16), (15, 9), (20, 4)], m)
    if c.has('anzu', 'storm', 'void'):
        t = s.lit(t)
    s.poly([(24, 3), (27, 7), (25, 11), (20, 6)], t)
    if c.has('owlbear', 'eagle', 'vrock', 'griffin', 'tengu'):
        for k in range(3):
            s.line([(12 + 3 * k, 18 - 3 * k), (17 + 3 * k, 22 - 4 * k)], shade(m, -1) if not c.has('griffin') else (150, 110, 70))
    if c.has('corrupted'):
        s.poly([(12, 25), (9, 23), (10, 18), (15, 20)], (110, 60, 150))
    s.line([(25, 5), (5, 28)], IVORY if sum(m) < 560 else (150, 130, 110))
    clear(s, [(11, 19), (10, 20), (20, 19), (21, 18), (16, 9), (15, 10), (24, 13)])
    if c.has('bronze'):
        s.line([(21, 6), (13, 17)], (250, 226, 160))
    if c.g and not c.has('anzu'):
        s.px([(4, 29), (28, 4), (7, 17)], s.lit(c.g))
    if c.h & 1:
        mirror(s)


def p_eye(s, c):
    sclera = (236, 232, 220) if not c.has('hag') else (232, 220, 160)
    iris = (110, 150, 60) if c.has('hag') else c.m
    slit = c.has('basilisk', 'chimera', 'nothic')
    y0 = 7
    if c.has('eyestalk'):
        s.line([(8, 29), (10, 22), (15, 17)], (150, 100, 150), 4); s.px([(8, 26), (10, 22)], (190, 140, 190))
        y0 = 2
        s.ell(9, 2, 26, 19, sclera); bx, by = 17, 10
    else:
        if c.has('jelly'):
            j = (150, 200, 220)
            s.poly([(4, 20), (9, 10), (22, 9), (28, 20), (26, 28), (6, 28)], j); s.px([(8, 22), (8, 23)], WHITE)
        s.ell(6, 6, 25, 25, sclera); bx, by = 15, 15
        if c.has('hag', 'cyclops'):
            s.px([(8, 12), (9, 13), (22, 19), (23, 18), (9, 19)], (210, 110, 110))
    g = s.lit(c.g) if c.g else None
    s.ell(bx - 5, by - 5, bx + 5, by + 5, iris)
    if slit:
        s.rect(bx, by - 4, bx + 1, by + 4, DARK)
    else:
        s.ell(bx - 2, by - 2, bx + 2, by + 2, DARK)
    if g:
        s.px([(bx - 3, by), (bx + 3, by + 1), (bx, by + 4) if not slit else (bx - 2, by + 3)], g)
    s.px([(bx - 3, by - 3), (bx - 4, by - 3)], WHITE)


def p_heart(s, c):
    m = c.m if c.has('wendigo', 'archon', 'revenant', 'night_hag') else mix(c.m, (180, 40, 50), 0.55)
    s.ell(5, 7, 17, 19, m); s.ell(14, 7, 26, 19, m); s.poly([(5, 14), (26, 14), (16, 28), (15, 28)], m)
    v = shade(m, -2) if not c.has('archon') else GOLD
    s.rect(11, 3, 14, 9, v); s.rect(17, 4, 20, 9, shade(m, 1)); s.line([(18, 4), (23, 2)], shade(m, 1), 2)
    s.px([(8, 11), (9, 10), (8, 12)], shade(m, 2))
    g = s.lit(c.g) if c.g else None
    if c.has('dragon'):
        g = s.lit((255, 180, 70)); stip(s, m, shade(m, -1), lambda x, y: (x + y) % 4 == 0 and y % 2 == 0)
        s.line([(13, 14), (16, 18), (15, 22)], g)
    elif c.has('revenant'):
        s.line([(10, 13), (21, 21)], DARK); s.px([(12, 12), (14, 16), (17, 16), (19, 20)], (200, 200, 190))
    elif c.has('wendigo'):
        s.px([(7, 9), (22, 8), (24, 13), (12, 22), (18, 23), (16, 27)], WHITE); s.poly([(13, 13), (18, 13), (16, 20)], g)
    elif c.has('chimera'):
        s.poly([(15, 9), (26, 12), (22, 20), (16, 27)], mix(c.m, (90, 150, 80), 0.6)); s.px([(16, 15)], g)
    elif c.has('vrykolakas'):
        s.line([(9, 20), (22, 9)], (150, 110, 70), 2); s.px([(8, 21), (7, 22)], (150, 110, 70))
    elif g:
        s.ell(13, 13, 18, 18, g)
    if c.has('demon'):
        s.poly([(8, 8), (5, 2), (11, 6)], DARK); s.poly([(22, 8), (26, 2), (20, 6)], DARK)


def p_bone(s, c):
    b = c.m if c.has('frost', 'witch', 'charred', 'fomorian', 'thrall') else BONE
    if c.has('charred'):
        b = (70, 62, 62)
    if c.has('witch'):
        b = (200, 206, 170)
    if c.has('skull'):
        s.ell(6, 3, 25, 21, b); s.rect(10, 18, 21, 26, b)
        eye = s.lit(c.g) if c.g else DARK
        s.ell(9, 10, 14, 16, DARK); s.ell(17, 10, 22, 16, DARK); s.px([(11, 13), (12, 13), (19, 13), (20, 13)], eye)
        s.poly([(15, 17), (16, 17), (17, 20), (14, 20)], DARK)
        for x in (12, 15, 18):
            s.line([(x, 23), (x, 26)], shade(b, -2))
        if c.has('pack_lord'):
            s.poly([(6, 6), (3, 1), (10, 4)], b); s.poly([(25, 6), (28, 1), (21, 4)], b)
            s.poly([(11, 20), (20, 20), (18, 29), (13, 29)], b); s.px([(13, 28), (18, 28)], WHITE)
        if c.has('demi'):
            s.px([(15, 6), (16, 6), (15, 7), (16, 7)], s.lit((255, 90, 120))); s.rect(9, 2, 22, 3, GOLD)
        return
    if c.has('knuckle', 'finger'):
        skin = c.m if c.has('witch') else b
        s.line([(8, 27), (12, 18)], skin, 5); s.line([(12, 18), (18, 11)], skin, 4); s.line([(18, 11), (22, 6)], skin, 3)
        s.ell(9, 15, 15, 21, shade(skin, 1)); s.ell(15, 8, 21, 14, shade(skin, 1))
        if c.has('witch'):
            s.poly([(21, 7), (24, 5), (28, 1), (23, 3)], (60, 50, 60)); s.px([(11, 23), (14, 14)], (90, 70, 110))
        else:
            s.rect(5, 24, 11, 29, GOLD); s.px([(8, 26)], s.lit((255, 90, 60)))
        return
    if c.has('shard') and not c.has('ossuary'):
        s.poly([(6, 26), (10, 28), (26, 6), (24, 3), (15, 10), (9, 18)], b); s.line([(10, 24), (22, 8)], shade(b, -1))
        clear(s, [(8, 27), (6, 26), (7, 25)]); return
    th = 6 if c.has('giant', 'fomorian', 'draco', 'guardian') else 4
    if c.has('fomorian'):
        s.line([(9, 23), (13, 15), (22, 9)], b, th)
    else:
        s.line([(9, 23), (22, 9)], b, th)
    r = 3 if th == 4 else 4
    for cx, cy in ((6, 22), (10, 26), (21, 5), (25, 9)):
        s.ell(cx - r, cy - r, cx + r, cy + r, b)
    if c.has('hollow'):
        s.ell(21, 4, 26, 9, DARK)
    if c.has('frost', 'giant') and c.g:
        s.px([(12, 19), (15, 17), (19, 12), (7, 21), (24, 7), (22, 4)], s.lit((230, 248, 255)))
        s.px([(13, 24), (18, 19)], WHITE)
    if c.has('charred'):
        s.px([(13, 19), (17, 15), (20, 11)], s.lit((255, 140, 50)))
    if c.has('guardian'):
        s.px([(13, 18), (15, 16), (17, 14), (19, 12)], s.lit((120, 220, 255)))
    if c.has('warrior'):
        clear(s, [(16, 13), (17, 13), (17, 12)]); s.line([(11, 20), (13, 18)], (150, 60, 50))
    if c.has('draco'):
        s.poly([(13, 17), (11, 12), (16, 15)], b); s.poly([(17, 13), (15, 8), (20, 11)], b)
    if c.has('thrall'):
        s.rect(13, 14, 17, 18, IRON)
    if c.has('ossuary'):
        s.px([(12, 20), (16, 16), (19, 13)], shade(b, -2))
    if c.h & 1:
        mirror(s)


def p_gland(s, c):
    m = c.m
    if c.has('brain'):
        m = (226, 150, 164)
        s.ell(4, 8, 27, 26, m); s.line([(16, 9), (16, 25)], shade(m, -2))
        for (a, b) in (((7, 13), (13, 12)), ((6, 18), (12, 20)), ((9, 23), (14, 22)), ((19, 12), (25, 14)), ((19, 19), (26, 18)), ((18, 23), (23, 23))):
            s.line([a, ((a[0] + b[0]) // 2, a[1] + 2), b], shade(m, -1))
        return
    if c.has('organ', 'gut'):
        s.ell(5, 9, 20, 26, m); s.ell(13, 6, 27, 21, m); s.ell(13, 13, 19, 19, shade(m, -1))
        s.line([(22, 7), (25, 3)], shade(m, 1), 3)
        if c.g:
            g = s.lit(c.g); s.ell(15, 14, 18, 17, g); s.px([(8, 15), (23, 11), (10, 21)], g)
        else:
            s.px([(8, 14), (9, 13), (22, 10)], shade(m, 2))
        return
    s.poly([(17, 11), (20, 4), (24, 3), (25, 6), (22, 13)], shade(m, -1))
    s.ell(6, 9, 25, 28, m)
    if c.has('sac'):
        liq = c.g or shade(m, 2)
        if c.has('frost'):
            liq = (220, 246, 255)
        liq = s.lit(liq) if (c.g or c.has('toxic', 'frost')) else liq
        s.ell(9, 15, 22, 26, liq); s.rect(9, 15, 22, 17, m)
    else:
        s.px([(10, 15), (13, 20), (19, 16), (17, 23), (11, 23), (21, 21)], shade(m, 2) if sum(m) < 520 else shade(m, -1))
        if c.g or c.has('fire', 'frost', 'blink', 'troll', 'venom'):
            g = s.lit(c.g or (190, 250, 110)); s.ell(13, 16, 18, 21, g)
    s.px([(9, 13), (10, 12), (9, 14)], WHITE)
    if c.has('venom', 'wasp', 'scorpion', 'komodo', 'yuan', 'echidna'):
        s.px([(24, 2), (26, 1)], s.lit((180, 240, 90)))
    if c.h & 1:
        mirror(s)


def p_dust(s, c):
    m = c.m
    g = s.lit(c.g) if c.g else None
    v = c.h % 3
    if c.has('salt'):
        v = 1
    if c.has('mulch'):
        s.poly([(3, 27), (8, 18), (15, 12), (22, 16), (28, 27)], (96, 70, 46))
        stip(s, (96, 70, 46), (60, 100, 50), lambda x, y: (x * 3 + y * 7) % 9 == 0)
        stip(s, (96, 70, 46), (150, 110, 60), lambda x, y: (x * 5 + y * 3) % 13 == 0)
        s.px([(14, 10), (15, 9), (17, 10)], LEAF); return
    if v == 0:      # open pouch
        s.poly([(8, 14), (23, 14), (27, 24), (23, 29), (8, 29), (4, 24)], LEATHER)
        s.ell(7, 10, 24, 17, shade(LEATHER, -1)); s.ell(9, 8, 22, 15, m)
        s.line([(6, 20), (25, 20)], (206, 184, 130))
        s.px([(24, 12), (26, 15), (5, 13)], m)
    elif v == 1:    # heap on a dish
        s.ell(3, 21, 28, 29, (150, 156, 170) if not c.has('salt') else (120, 90, 60))
        s.poly([(6, 24), (11, 15), (16, 9), (21, 15), (25, 24)], m)
        s.px([(13, 15), (15, 12), (18, 17), (10, 21), (21, 21), (15, 20)], shade(m, 2) if sum(m) < 560 else shade(m, -1))
        if c.has('salt'):
            s.poly([(14, 9), (17, 8), (18, 11), (15, 12)], WHITE); s.rect(8, 19, 10, 21, WHITE); s.rect(20, 18, 22, 20, WHITE)
    else:           # folded paper with a heap
        s.poly([(3, 20), (16, 14), (29, 20), (16, 29)], (226, 214, 180))
        s.poly([(8, 21), (12, 15), (16, 11), (20, 15), (24, 21), (16, 25)], m)
        s.px([(14, 15), (17, 18), (12, 20)], shade(m, 2) if sum(m) < 560 else shade(m, -1))
    if g:
        sparkle(s, c, g, 4, (6, 2, 26, 9)); s.px([(16, 12), (13, 13)], g)
    if c.has('gold'):
        sparkle(s, c, s.lit((255, 244, 170)), 3, (6, 2, 26, 9))
    if c.has('pixie'):
        sparkle(s, c, s.lit((255, 255, 220)), 5, (3, 1, 28, 10))


def p_crystal(s, c):
    m = c.m
    g = s.lit(c.g) if c.g else None
    if c.has('gem', 'heartstone', 'pearl'):
        if c.has('pearl'):
            s.poly([(3, 20), (8, 14), (24, 14), (29, 20), (22, 28), (10, 28)], (110, 130, 150))
            for x in (8, 13, 18, 23):
                s.line([(x, 16), (x - (16 - x) // 3, 27)], (80, 96, 116))
            s.ell(10, 7, 21, 18, s.lit((250, 246, 255))); s.px([(13, 10), (14, 9)], WHITE); return
        if c.has('heartstone'):
            s.ell(5, 6, 17, 18, m); s.ell(14, 6, 26, 18, m); s.poly([(5, 13), (26, 13), (16, 28), (15, 28)], m)
            s.line([(16, 9), (10, 15), (16, 26)], shade(m, 1)); s.line([(16, 9), (21, 15), (16, 26)], shade(m, -1))
            s.px([(15, 15), (16, 15), (15, 16), (16, 16)], g); return
        s.poly([(10, 5), (21, 5), (27, 12), (16, 28), (15, 28), (4, 12)], m)
        s.poly([(10, 5), (21, 5), (19, 12), (12, 12)], shade(m, 1)); s.line([(4, 12), (27, 12)], shade(m, 2))
        s.line([(12, 12), (15, 27)], shade(m, -1)); s.line([(19, 12), (16, 27)], shade(m, -1))
        s.px([(13, 7), (14, 7)], g or WHITE); return
    if c.has('core'):
        ring = IRON if c.has('golem', 'guardian', 'stone') else shade(m, -2)
        s.ell(5, 5, 26, 26, m)
        if c.has('magma'):
            stip(s, m, (70, 50, 50), lambda x, y: (x * 7 + y * 5) % 6 < 2)
        if c.has('ice'):
            s.poly([(9, 3), (12, 9), (7, 9)], m); s.poly([(21, 2), (23, 8), (18, 8)], m); s.poly([(26, 21), (29, 27), (22, 25)], m)
        if c.has('air'):
            s.line([(6, 12), (12, 9), (20, 12), (25, 9)], WHITE); s.line([(7, 20), (13, 18), (20, 21), (24, 19)], WHITE)
        if c.has('water'):
            s.line([(7, 17), (11, 15), (15, 17), (19, 15), (24, 17)], (150, 210, 255))
        if c.has('golem', 'guardian', 'stone', 'slime') or c.id == 'elemental_core':
            s.rect(4, 14, 27, 17, ring); s.rect(14, 4, 17, 27, ring)
        s.ell(11, 11, 20, 20, g or s.lit(shade(m, 2))); s.px([(14, 13), (15, 13)], WHITE)
        return
    if c.has('stone', 'cairn') and not c.has('shard', 'crystal'):
        st = c.m if c.has('basilisk', 'beleth', 'sphinx') else (140, 140, 146)
        if c.has('tomb'):
            s.poly([(8, 28), (8, 9), (12, 4), (20, 4), (24, 9), (24, 20), (19, 24), (21, 28)], st)
            s.line([(12, 11), (20, 11)], shade(st, -2)); s.line([(16, 8), (16, 18)], shade(st, -2))
            s.px([(9, 26), (10, 25), (22, 12)], (96, 130, 80)); return
        s.poly([(6, 12), (13, 5), (22, 6), (27, 14), (25, 24), (17, 28), (8, 26), (4, 19)], st)
        s.line([(13, 6), (15, 13), (11, 19)], shade(st, -2)); s.line([(15, 13), (22, 17)], shade(st, -2))
        if c.has('cairn'):
            s.ell(9, 2, 22, 10, shade(st, 1)); s.px([(8, 22), (9, 22), (8, 23)], (96, 130, 80))
        rune = g or (s.lit((255, 200, 90)) if c.has('riddle', 'quake', 'golem') else None)
        if rune:
            s.px([(18, 9), (19, 10), (18, 11), (8, 16), (9, 17), (19, 21), (20, 22), (19, 23)], rune)
        else:
            s.px([(19, 10), (9, 17), (20, 22)], shade(st, 2))
        return
    # shards / crystals
    metal = c.has('bronze', 'iron', 'brass', 'lance', 'glaive', 'war_shard', 'plate')
    if metal:
        s.poly([(7, 25), (11, 8), (17, 3), (25, 12), (21, 17), (24, 26), (14, 22)], m)
        s.line([(13, 9), (11, 21)], shade(m, 2)); s.line([(18, 6), (20, 15)], shade(m, -1))
        if g:
            s.px([(24, 27), (6, 26), (22, 18)], g)
        return
    lm = s.lit(shade(m, 1)) if g else shade(m, 1)
    if c.has('shard', 'fragment', 'splinter'):
        s.poly([(9, 27), (7, 17), (13, 4), (19, 2), (24, 14), (20, 28), (14, 24)], m)
        s.poly([(13, 4), (19, 2), (17, 14), (12, 16)], lm); s.line([(17, 14), (20, 27)], shade(m, -1))
    else:
        s.poly([(12, 28), (10, 12), (15, 3), (20, 12), (19, 28)], m); s.poly([(15, 3), (20, 12), (17, 14), (13, 12)], lm)
        s.poly([(4, 28), (4, 18), (8, 13), (11, 19), (11, 28)], shade(m, -1)); s.poly([(20, 28), (21, 16), (25, 10), (28, 18), (27, 28)], shade(m, -1))
        s.rect(3, 27, 28, 29, (90, 90, 100))
    if g:
        s.px([(15, 8), (15, 9), (14, 18), (17, 21)], g); sparkle(s, c, g, 2, (20, 2, 29, 9))
    else:
        s.px([(14, 7), (14, 8)], WHITE)
    if c.has('nidhoggr'):
        s.px([(10, 20), (11, 21), (18, 10)], (60, 110, 50))


def p_skein(s, c):
    m = c.m if not c.has('spider_silk', 'ettercap', 'web') else (236, 236, 228)
    if c.id == 'spider_silk':
        m = (236, 236, 228)
    g = s.lit(c.g) if c.g else None
    if c.has('mane', 'hair'):
        s.poly([(11, 5), (20, 5), (21, 10), (25, 22), (22, 29), (18, 25), (15, 30), (11, 25), (7, 28), (6, 21), (10, 10)], m)
        for x in (10, 13, 16, 19, 22):
            s.line([(x, 11), (x - 1 + (x % 2) * 2, 26)], shade(m, -1))
        s.rect(10, 7, 21, 10, (170, 40, 50) if not c.has('each', 'puca') else (60, 130, 90)); s.ell(12, 2, 19, 7, m)
        if c.has('winged'):
            s.poly([(21, 8), (28, 4), (27, 10), (23, 12)], WHITE); s.poly([(10, 8), (3, 4), (4, 10), (8, 12)], WHITE)
        if c.has('each'):
            s.px([(8, 29), (15, 31), (22, 30)], s.lit((150, 220, 240)))
        if g:
            s.px([(13, 15), (18, 20), (15, 23)], g)
        return
    if c.has('strand', 'roper'):
        for k in range(4):
            s.ell(5 + k, 8 + k * 4, 26 - k, 17 + k * 4, m if k % 2 == 0 else shade(m, -1))
        s.line([(24, 10), (28, 4)], m, 3); stip(s, m, shade(m, 1), lambda x, y: (x + y) % 4 == 0); return
    if c.has('filament', 'thread'):
        col = s.lit(c.g or (255, 220, 120))
        s.rect(13, 4, 18, 27, WOOD); s.rect(10, 3, 21, 5, shade(WOOD, 1)); s.rect(10, 26, 21, 28, shade(WOOD, 1))
        s.rect(9, 8, 22, 23, m)
        for y in range(9, 23, 2):
            s.line([(9, y), (22, y + 1)], col)
        s.line([(22, 22), (27, 26), (25, 30)], col); return
    s.ell(4, 9, 27, 24, m)
    for k in range(4):
        s.line([(6, 13 + k * 3), (16, 11 + k * 3), (26, 13 + k * 3)], shade(m, -1) if sum(m) > 420 else shade(m, 1))
    s.rect(14, 8, 18, 25, c.a if c.a != shade(c.m, 1) else (120, 90, 150))
    s.line([(26, 20), (29, 25), (26, 29)], m)
    if g:
        s.px([(8, 11), (23, 22), (29, 26), (10, 20)], g)
    if c.has('gland'):
        pass


def p_liquid(s, c):
    m = c.m
    if c.has('blood') and not c.has('medusa'):
        m = mix(c.m, (180, 20, 30), 0.6)
    if c.has('ink'):
        s.rect(7, 16, 24, 28, GLASS); s.rect(9, 19, 22, 26, (24, 28, 70)); s.rect(11, 12, 20, 16, GLASS)
        s.line([(16, 14), (25, 2)], WHITE, 2); s.poly([(25, 2), (29, 4), (24, 9), (22, 6)], (120, 200, 255))
        s.px([(10, 20)], s.lit((120, 200, 255))); return
    if c.has('perfume'):
        s.poly([(16, 11), (25, 19), (16, 29), (7, 19)], (240, 170, 190)); s.poly([(16, 15), (21, 19), (16, 25), (11, 19)], s.lit((255, 120, 110)))
        s.rect(14, 7, 17, 11, GOLD); s.ell(12, 2, 19, 8, GOLD); s.line([(20, 5), (24, 5)], GOLD); s.ell(24, 3, 28, 7, (190, 50, 70)); return
    if c.has('resin'):
        s.rect(6, 14, 25, 28, (150, 100, 60)); s.ell(6, 11, 25, 18, (190, 130, 60)); s.ell(9, 12, 22, 16, (230, 160, 50))
        s.line([(6, 22), (25, 22)], (110, 70, 40)); s.line([(20, 13), (26, 4)], WOOD, 2); s.px([(12, 13)], WHITE); return
    glow = c.g or (None if not c.has('venom', 'ichor', 'bile', 'solar', 'poison', 'cultist', 'vial', 'saliva', 'reagent') else None)
    bottle(s, c, m, glow)
    if c.has('venom', 'poison'):
        s.px([(15, 21), (16, 21), (15, 22), (16, 22)], shade(m, 2)) if c.h % 5 not in (2,) else None
    if c.has('oil'):
        s.px([(14, 20), (17, 22), (12, 23)], (240, 220, 120))
    if c.has('spore_cloud'):
        s.px([(13, 20), (17, 18), (15, 23), (19, 22), (11, 22)], (236, 240, 190))


def p_blob(s, c):
    m = c.m
    hi = shade(m, 2)
    s.ell(3, 22, 28, 29, shade(m, -1))
    if c.has('mold', 'patch', 'moss'):
        s.poly([(4, 24), (6, 14), (14, 10), (24, 12), (28, 22), (22, 27), (9, 28)], (130, 130, 136))
        for (x, y, r) in ((8, 14, 3), (15, 11, 4), (22, 15, 3), (12, 19, 3), (19, 21, 3)):
            s.ell(x - r, y - r, x + r, y + r, m)
        s.px([(8, 13), (15, 10), (22, 14), (12, 18)], hi)
        if c.has('mold'):
            s.px([(5, 9), (25, 8), (17, 5)], s.lit((226, 200, 120)))
        return
    s.poly([(5, 25), (7, 15), (13, 8), (17, 5), (22, 10), (26, 18), (27, 25), (20, 28), (10, 28)], m)
    s.px([(10, 14), (11, 13), (10, 15), (12, 12)], WHITE); s.ell(17, 17, 21, 21, hi); s.px([(13, 22), (22, 13)], hi)
    if c.has('black_ooze'):
        s.px([(13, 18), (14, 18), (19, 15)], s.lit((200, 230, 120)))
    if c.g:
        s.px([(15, 16), (16, 23)], s.lit(c.g))
    if c.has('cloud'):
        pass


def p_wisp(s, c):
    g1 = s.lit(c.g or shade(c.m, 2)); g0 = s.lit(c.m if sum(c.m) > 300 else shade(c.m, 2))
    v = c.h % 3
    if c.has('cloud'):
        cl = s.lit((236, 242, 250))
        for (x, y, r) in ((10, 17, 6), (17, 13, 7), (23, 18, 5), (15, 20, 6)):
            s.ell(x - r, y - r, x + r, y + r, cl)
        s.px([(12, 14), (18, 10), (8, 20)], WHITE); return
    if c.has('voice', 'glamour', 'shimmer', 'fragment') or v == 0:   # held in a glass orb
        s.ell(5, 8, 26, 29, GLASS); s.rect(12, 4, 19, 9, GLASS); s.rect(12, 2, 19, 4, CORK)
        s.ell(9, 13, 22, 26, g0); s.poly([(13, 15), (18, 14), (20, 19), (15, 23), (12, 20)], g1)
        s.px([(8, 14), (8, 15)], WHITE)
        if c.has('voice'):
            s.line([(11, 19), (14, 17), (17, 21), (20, 18)], WHITE)
        if c.has('fragment'):
            s.poly([(14, 14), (18, 16), (16, 24), (13, 20)], WHITE)
    elif v == 1:    # free flame-wisp
        s.poly([(8, 22), (9, 14), (14, 9), (15, 3), (19, 9), (23, 15), (24, 22), (20, 28), (12, 28)], g0)
        s.poly([(12, 22), (13, 16), (16, 11), (19, 17), (20, 22), (17, 26), (14, 26)], g1)
        s.px([(22, 6), (7, 10), (25, 11)], g1)
    else:           # swirl
        s.ell(6, 8, 25, 27, g0); s.ell(10, 12, 21, 23, g1); s.ell(13, 15, 18, 20, g0)
        s.line([(24, 12), (28, 7), (25, 3)], g0, 2); s.px([(4, 22), (27, 24), (8, 5)], g1)
    if c.has('death', 'wight', 'jiangshi', 'spectral', 'hollow', 'pale'):
        s.px([(13, 18), (14, 18), (18, 18), (19, 18)], DARK)
    if c.has('storm'):
        s.line([(15, 13), (18, 17), (14, 19), (17, 24)], s.lit((255, 244, 140)))
    if c.has('vine', 'nightshade'):
        s.px([(14, 3), (15, 2), (17, 3)], LEAF)
    if c.has('sand'):
        s.px([(11, 24), (13, 25), (17, 25), (20, 24), (15, 24)], (236, 210, 140))


def p_tentacle(s, c):
    m = c.m
    s.line([(6, 28), (9, 20), (16, 15), (22, 17), (24, 22)], m, 5)
    s.line([(24, 22), (21, 26), (18, 24)], m, 3)
    s.line([(9, 20), (8, 10), (13, 4)], m, 4); s.px([(14, 3), (15, 2)], m)
    s.px([(8, 24), (11, 19), (15, 17), (19, 17), (22, 19), (9, 14), (10, 9)], shade(m, 2))
    if c.h & 1:
        mirror(s)


def p_wing(s, c):
    m = c.m
    arm = shade(m, -2)
    if c.has('membrane') and not c.has('camazotz', 'nightwing'):
        s.poly([(4, 8), (14, 5), (26, 8), (28, 20), (22, 27), (10, 26), (3, 18)], m)
        s.line([(6, 10), (24, 24)], shade(m, 1)); s.line([(14, 6), (12, 25)], shade(m, -1)); s.line([(25, 10), (6, 20)], shade(m, -1))
        clear(s, [(18, 14), (19, 14), (18, 15)]); return
    s.poly([(4, 6), (12, 4), (27, 9), (29, 16), (25, 21), (23, 17), (20, 25), (17, 20), (13, 28), (11, 20), (6, 24), (7, 14)], m)
    s.line([(5, 6), (27, 10)], arm, 2); s.line([(6, 7), (12, 26)], arm); s.line([(7, 7), (19, 23)], arm); s.line([(8, 7), (24, 19)], arm)
    s.px([(3, 5), (2, 4)], IVORY)
    if c.g:
        s.px([(12, 12), (18, 14), (22, 13)], s.lit(c.g))
    if c.h & 1:
        mirror(s)


def p_herb(s, c):
    i = c.id
    if 'clover' in i:
        g = (70, 170, 80)
        s.line([(16, 16), (18, 24), (16, 29)], (60, 120, 60), 2)
        for (x, y) in ((11, 6), (17, 6), (11, 12), (17, 12)):
            s.ell(x - 3, y - 2, x + 5, y + 6, g)
        s.px([(15, 11), (16, 11), (15, 12), (16, 12)], shade(g, -1)); s.px([(10, 6), (20, 7), (11, 14), (20, 14)], shade(g, 2))
        sparkle(s, c, s.lit((255, 240, 150)), 3, (3, 2, 28, 20))
    elif 'carrot' in i:
        o = (236, 130, 44) if 'magic' not in i else (240, 150, 60)
        s.poly([(10, 10), (19, 8), (23, 13), (9, 29), (7, 28)], o)
        for k in range(4):
            s.line([(11 + k * 2, 14 + k * 3), (14 + k * 2 - k, 13 + k * 3)], shade(o, -1))
        s.line([(17, 9), (22, 2)], LEAF, 2); s.line([(19, 10), (27, 6)], LEAF, 2); s.line([(15, 9), (15, 3)], (60, 130, 60), 2)
        if 'magic' in i:
            g = s.lit((150, 230, 255)); s.px([(12, 17), (14, 20), (11, 23), (5, 14), (25, 18), (22, 24)], g)
        else:
            s.px([(8, 27), (6, 30)], (150, 100, 60))
    elif 'celery' in i:
        for k, x in enumerate((9, 13, 17)):
            col = (200, 226, 160) if k != 1 else (176, 210, 140)
            s.poly([(x, 28), (x + 5, 28), (x + 5 + k - 1, 10), (x + 1 + k - 1, 10)], col)
            s.line([(x + 2, 12), (x + 2, 27)], shade(col, -1))
        s.ell(5, 3, 14, 11, (120, 180, 90)); s.ell(12, 1, 21, 10, (140, 196, 100)); s.ell(18, 4, 27, 12, (120, 180, 90))
    elif 'mandrake' in i:
        r = (190, 150, 100)
        s.ell(10, 9, 22, 21, r); s.poly([(11, 18), (15, 20), (11, 29), (8, 29)], r); s.poly([(17, 20), (21, 18), (24, 29), (21, 29)], r)
        s.line([(10, 14), (4, 18)], r, 2); s.line([(22, 14), (28, 17)], r, 2)
        s.px([(13, 13), (18, 13)], DARK); s.line([(14, 17), (17, 17)], DARK)
        s.poly([(14, 9), (9, 2), (15, 5)], LEAF); s.poly([(17, 9), (24, 2), (18, 5)], LEAF); s.poly([(15, 9), (16, 1), (18, 8)], (110, 170, 80))
    elif 'valerian' in i:
        r = (200, 170, 130)
        for x, y in ((8, 28), (12, 30), (16, 29), (21, 30), (25, 27)):
            s.line([(16, 16), (x, y)], r, 2)
        s.rect(14, 10, 17, 18, (110, 150, 80)); s.line([(11, 17), (20, 17)], (150, 100, 60))
        for (x, y) in ((10, 6), (16, 3), (21, 7), (13, 8), (19, 4)):
            s.ell(x - 2, y - 2, x + 2, y + 2, (240, 190, 214))
        s.px([(10, 6), (16, 3), (21, 7)], WHITE)
    elif 'pepper' in i:
        r = (210, 44, 36)
        s.poly([(8, 8), (14, 7), (19, 12), (25, 20), (27, 28), (21, 24), (13, 18), (8, 12)], r)
        s.px([(11, 10), (12, 10), (15, 14)], (250, 150, 130)); s.line([(10, 8), (7, 3)], LEAF, 2); s.ell(7, 5, 14, 10, LEAF)
        s.px([(27, 29)], s.lit((255, 170, 60)))
    elif 'nightshade' in i:
        g = (80, 70, 130)
        s.line([(6, 28), (16, 16), (24, 6)], (70, 100, 70), 2)
        s.poly([(16, 16), (9, 12), (5, 4), (13, 6), (18, 13)], g); s.poly([(16, 17), (24, 14), (28, 20), (22, 23), (15, 20)], g)
        s.line([(7, 6), (15, 14)], shade(g, 1)); s.line([(17, 18), (26, 19)], shade(g, 1))
        s.ell(8, 20, 13, 25, (40, 30, 70)); s.px([(9, 21)], WHITE)
    elif 'moss' in i:
        s.poly([(4, 26), (7, 18), (15, 15), (24, 17), (28, 25), (22, 29), (9, 29)], (130, 130, 136))
        for (x, y, r) in ((9, 17, 4), (16, 13, 5), (23, 17, 4), (13, 19, 3)):
            s.ell(x - r, y - r, x + r, y + r, c.m)
        s.px([(8, 15), (15, 11), (22, 15), (17, 15), (11, 19)], shade(c.m, 2)); s.px([(12, 8), (20, 8)], (190, 220, 120))
    elif 'healing' in i:
        s.line([(16, 29), (16, 12)], (60, 120, 60), 2)
        s.poly([(15, 22), (7, 18), (5, 12), (12, 14)], LEAF); s.poly([(17, 20), (25, 16), (27, 10), (20, 12)], LEAF)
        s.poly([(15, 26), (9, 26), (11, 22)], (70, 130, 60))
        s.ell(11, 3, 21, 12, (226, 60, 70)); s.ell(14, 6, 18, 10, s.lit((255, 230, 150)))
        s.px([(9, 4), (23, 4), (25, 22)], s.lit((255, 230, 150)))
    elif 'twig' in i:
        w = (110, 80, 50)
        s.ell(5, 9, 26, 24, w); clear(s, [(x, y) for x in range(8, 24) for y in range(12, 22) if ((x - 15.5) / 8) ** 2 + ((y - 16.5) / 5) ** 2 < 1])
        for (x, y) in ((8, 9), (15, 7), (22, 9)):
            s.line([(x, y + 2), (x - 1, y - 5)], w, 2); s.line([(x, y - 1), (x + 3, y - 4)], w)
        s.px([(7, 3), (14, 1), (21, 3), (25, 5), (18, 2)], s.lit((190, 240, 110)))
        s.px([(6, 15), (26, 18), (12, 23)], LEAF)
    elif 'wood' in i or 'totem' in i:
        w = (150, 104, 60)
        if 'totem' in i:
            s.rect(11, 3, 20, 29, w); s.rect(8, 8, 23, 10, w); s.rect(9, 18, 22, 20, shade(w, -1))
            s.px([(13, 5), (18, 5), (13, 13), (18, 13), (13, 23), (18, 23)], s.lit((255, 220, 110)))
            s.line([(14, 7), (17, 7)], DARK); s.line([(14, 15), (17, 15)], DARK); s.line([(14, 25), (17, 25)], DARK)
            s.poly([(8, 8), (3, 5), (8, 10)], (190, 50, 50)); s.poly([(23, 8), (28, 5), (23, 10)], (190, 50, 50))
        else:
            s.poly([(4, 18), (22, 8), (27, 14), (9, 26)], w); s.ell(20, 7, 29, 16, (214, 176, 120)); s.ell(23, 10, 26, 13, w)
            s.line([(8, 19), (19, 13)], shade(w, -1)); s.line([(10, 23), (21, 17)], shade(w, -1))
            s.px([(11, 17), (15, 19), (17, 14), (13, 22)], s.lit((150, 230, 255)))
    else:   # sprig: rosemary, thyme, generic leaf
        g = c.m if sum(c.m) < 600 else LEAF
        s.line([(8, 29), (14, 18), (22, 4)], (90, 100, 60), 2)
        if 'leaf' in i:
            pass
        if 'thyme' in i:
            s.line([(14, 18), (8, 6)], (90, 100, 60)); s.line([(14, 20), (26, 12)], (90, 100, 60))
            for (x, y) in ((11, 22), (15, 20), (13, 15), (18, 13), (17, 8), (21, 9), (9, 11), (12, 8), (20, 16), (24, 14), (7, 6)):
                s.ell(x - 2, y - 1, x + 1, y + 1, g if (x + y) % 2 else shade(g, -1))
            for (x, y) in ((22, 3), (8, 3), (27, 11)):
                s.ell(x - 1, y - 1, x + 1, y + 1, (226, 170, 226))
            return
        for k in range(6):
            x, y = 10 + k * 2, 24 - k * 4
            s.line([(x, y), (x - 5, y - 3)], g, 2); s.line([(x + 1, y), (x + 6, y + 1)], shade(g, -1), 2)
        if 'rosemary' in i:
            s.px([(23, 3), (5, 20)], (150, 150, 230))


def p_mushroom(s, c):
    i = c.id
    cap = c.m
    stem = CREAM
    if 'petrified' in i:
        cap, stem = (150, 150, 156), (190, 190, 190)
    if c.has('spore') and not c.has('cap'):
        g = s.lit(c.g or shade(cap, 2))
        s.ell(9, 13, 22, 26, cap); s.rect(14, 25, 17, 29, stem); s.ell(13, 16, 18, 21, shade(cap, -1))
        for (x, y) in ((6, 9), (11, 5), (17, 3), (23, 6), (26, 11), (4, 15), (14, 9), (20, 10)):
            s.px([(x, y)], g)
        s.px([(16, 12)], g); return
    if c.has('fungi', 'fungus', 'crimson'):
        s.rect(8, 18, 11, 28, stem); s.rect(19, 15, 22, 28, stem); s.rect(14, 22, 16, 28, stem)
        s.ell(3, 12, 15, 20, cap); s.ell(14, 7, 28, 17, shade(cap, 0)); s.ell(11, 19, 19, 24, shade(cap, 1))
        s.px([(7, 14), (11, 15), (19, 10), (23, 12), (15, 21)], WHITE if not c.has('deep') else s.lit((150, 230, 255)))
        return
    s.poly([(13, 15), (19, 15), (20, 28), (12, 28)], stem)
    s.ell(4, 4, 27, 19, cap); s.rect(6, 15, 25, 17, shade(cap, -1))
    clear(s, [(x, y) for x in range(4, 28) for y in range(18, 20)])
    if 'wild' in i:
        s.ell(8, 7, 12, 10, WHITE); s.ell(17, 6, 21, 9, WHITE); s.px([(14, 12), (23, 11)], WHITE)
    elif 'petrified' in i:
        s.line([(10, 7), (14, 12), (12, 15)], (90, 90, 100)); s.line([(16, 16), (17, 26)], (120, 120, 126))
    else:
        s.px([(9, 9), (10, 8), (11, 8)], shade(cap, 2))
    if c.g:
        s.px([(15, 9), (20, 11)], s.lit(c.g))


def p_egg(s, c):
    e = (232, 222, 196)
    s.poly([(6, 14), (10, 17), (13, 13), (17, 18), (21, 13), (25, 16), (26, 22), (21, 28), (11, 28), (6, 22)], e)
    s.px([(10, 22), (13, 24), (20, 21), (17, 25), (22, 24)], (170, 130, 90))
    s.poly([(18, 3), (25, 5), (27, 11), (22, 9)], e); s.px([(23, 6)], (170, 130, 90))
    s.ell(12, 19, 19, 25, (244, 200, 70))


def p_ember(s, c):
    hot = s.lit((255, 200, 80)); m = s.lit((240, 110, 40))
    if c.has('ash'):
        s.poly([(4, 27), (9, 19), (16, 15), (23, 19), (28, 27)], (150, 146, 144))
        s.px([(12, 21), (16, 18), (20, 22), (15, 24), (9, 25)], m); s.px([(16, 19), (13, 23)], hot)
        s.px([(11, 11), (19, 9), (15, 6)], (190, 186, 184)); return
    s.poly([(5, 20), (9, 12), (18, 9), (26, 14), (27, 23), (20, 28), (9, 27)], (60, 44, 44))
    s.line([(9, 14), (14, 18), (12, 25)], m); s.line([(14, 18), (22, 16), (25, 21)], m); s.line([(18, 10), (17, 16)], m)
    s.px([(14, 18), (13, 19), (22, 16)], hot)
    s.px([(11, 6), (16, 3), (21, 6), (14, 7)], hot if not c.has('amon') else s.lit((255, 90, 60)))
    if c.has('amon'):
        s.poly([(14, 9), (16, 2), (19, 9)], m)


def p_meat(s, c):
    i = c.id
    base = {'bear': (150, 50, 50), 'lion': (190, 80, 60), 'wolf': (170, 60, 60), 'lizard': (214, 190, 170),
            'snake': (226, 196, 180), 'rat': (190, 110, 100), 'goblin': (150, 160, 110), 'rotted': (120, 124, 84),
            'zombie': (124, 140, 104), 'plague': (150, 150, 80), 'prime': (196, 60, 60), 'royal': (200, 50, 70)}
    m = next((v for k, v in base.items() if k in i), MEAT)
    if c.has('frog', 'leg'):
        for ox, oy in ((0, 0), (9, 3)):
            s.ell(4 + ox, 4 + oy, 15 + ox, 16 + oy, (206, 220, 160)); s.line([(11 + ox, 14 + oy), (15 + ox, 23 + oy)], (206, 220, 160), 3)
            s.line([(15 + ox, 23 + oy), (13 + ox, 27 + oy)], IVORY, 2); s.px([(7 + ox, 7 + oy), (8 + ox, 6 + oy)], WHITE)
        return
    if i.endswith('_ear'):
        s.poly([(8, 26), (6, 16), (10, 8), (26, 3), (20, 12), (17, 22), (13, 27)], c.m)
        s.poly([(10, 21), (10, 15), (13, 10), (21, 6), (16, 14), (14, 21)], shade(c.m, -1))
        s.ell(15, 18, 18, 21, GOLD); clear(s, [(16, 19), (17, 20), (16, 20), (17, 19)]); return
    if c.has('snake'):
        s.ell(5, 9, 26, 26, (110, 150, 70)); s.ell(8, 12, 23, 23, m); s.ell(13, 15, 18, 20, (110, 150, 70))
        s.px([(7, 14), (11, 10), (20, 10), (24, 16), (22, 23), (10, 24)], (60, 96, 50)); s.px([(15, 17), (16, 17)], IVORY)
        return
    if c.has('rat', 'lizard'):
        s.ell(4, 6, 20, 22, m); s.line([(17, 19), (24, 26)], IVORY, 3); s.ell(23, 23, 29, 29, IVORY)
        s.px([(8, 10), (9, 9), (10, 9)], shade(m, 2)); s.line([(8, 17), (15, 19)], shade(m, -1))
        if c.has('lizard'):
            s.poly([(4, 10), (10, 6), (8, 12)], (110, 160, 80))
        return
    if c.has('rotted', 'zombie', 'plague', 'goblin', 'flesh'):
        s.poly([(5, 12), (12, 6), (22, 7), (27, 14), (25, 23), (16, 27), (7, 23)], m)
        s.line([(22, 20), (28, 26)], IVORY, 3); s.ell(26, 24, 30, 28, IVORY); s.line([(9, 12), (14, 10), (19, 12)], shade(m, 1))
        sp = shade(m, -2) if not c.has('goblin') else shade(m, 1)
        s.px([(9, 15), (20, 11), (21, 20), (12, 22), (23, 16)], sp)
        if c.has('plague'):
            s.px([(8, 4), (24, 3), (28, 9)], s.lit((200, 230, 90)))
        if c.has('rotted', 'zombie'):
            s.px([(26, 5), (27, 5), (4, 6), (5, 6)], DARK)
        return
    # good butcher's cut: steak with fat rim, marbling and a bone
    s.poly([(4, 14), (9, 7), (19, 5), (27, 10), (28, 19), (22, 26), (11, 27), (5, 22)], FAT)
    s.poly([(7, 15), (11, 10), (19, 8), (24, 12), (25, 18), (20, 23), (12, 24), (8, 20)], m)
    s.line([(11, 14), (15, 16), (14, 20)], FAT); s.line([(18, 11), (21, 15)], FAT); s.px([(19, 20), (12, 12)], FAT)
    if c.has('prime', 'royal', 'bear'):
        s.ell(13, 13, 18, 18, IVORY); s.ell(15, 15, 16, 16, (200, 150, 140))
    if c.has('royal'):
        s.line([(3, 26), (28, 24)], (150, 40, 130), 2); s.rect(14, 23, 18, 27, GOLD); s.px([(6, 4), (24, 3)], s.lit((255, 240, 150)))
    if c.has('lion'):
        s.poly([(26, 10), (30, 6), (29, 12)], IVORY)
    if c.has('wolf'):
        s.line([(24, 22), (29, 28)], IVORY, 3)


def p_clay(s, c):
    m = c.m
    s.poly([(5, 22), (8, 12), (16, 8), (24, 11), (28, 20), (24, 27), (10, 28)], m)
    s.ell(11, 13, 16, 17, shade(m, -1)); s.line([(18, 20), (23, 18)], shade(m, -1)); s.px([(10, 22), (20, 13)], shade(m, 1))
    if c.g:
        g = s.lit(c.g); s.px([(13, 15), (14, 15), (19, 22), (20, 22), (22, 14)], g); sparkle(s, c, g, 2)


def sword(s, c, kind):
    blade, hi = STEEL, (226, 232, 240)
    grip = LEATHER
    # drawn pointing up-right along the diagonal
    def diag(pts, col, w=1):
        s.line(pts, col, w)
    if kind == 'claymore':
        s.poly([(10, 19), (13, 22), (29, 4), (28, 2), (26, 3)], blade); diag([(12, 20), (27, 4)], hi)
        s.line([(6, 15), (17, 26)], IRON, 2); s.px([(5, 14), (6, 13), (18, 27), (19, 26)], GOLD)
        s.line([(10, 22), (4, 28)], grip, 3); s.ell(1, 26, 6, 31, GOLD)
    elif kind == 'flamberge':
        for k in range(6):
            x, y = 11 + k * 3, 21 - k * 3
            s.poly([(x - 2, y), (x + 1, y + 2), (x + 5, y - 2), (x + 2, y - 5)], blade if k % 2 else shade(blade, 1))
        s.poly([(27, 5), (29, 2), (30, 6)], blade)
        s.line([(7, 17), (15, 25)], GOLD, 2); s.line([(10, 22), (4, 28)], (120, 30, 40), 3); s.ell(1, 26, 6, 31, GOLD)
        s.px([(14, 17), (20, 11), (26, 6)], s.lit((255, 170, 70)))
    elif kind == 'estoc':
        s.line([(11, 21), (29, 3)], blade, 2); s.px([(29, 2), (30, 2)], hi)
        s.line([(7, 18), (14, 25)], IRON, 2); s.ell(7, 20, 12, 25, shade(IRON, 1)); s.line([(9, 23), (4, 28)], grip, 2); s.ell(2, 27, 5, 30, STEEL)
    elif kind in ('falchion', 'dao', 'kopis', 'kukri'):
        if kind == 'kukri':
            s.poly([(9, 20), (12, 23), (18, 19), (22, 21), (29, 12), (26, 5), (22, 12), (16, 14)], blade)
            s.line([(12, 21), (17, 16), (22, 14), (27, 7)], hi)
        elif kind == 'kopis':
            s.poly([(9, 20), (12, 23), (19, 18), (26, 16), (29, 8), (27, 3), (23, 9), (16, 13)], blade)
            s.line([(12, 20), (17, 15), (24, 11)], hi)
        elif kind == 'dao':
            s.poly([(9, 20), (13, 24), (27, 13), (29, 4), (24, 6), (16, 13)], blade); s.line([(12, 20), (25, 8)], hi)
            s.line([(4, 28), (1, 24)], (190, 40, 40), 2)
        else:
            s.poly([(9, 20), (12, 23), (26, 12), (29, 5), (27, 3), (22, 7), (16, 13)], blade); s.line([(12, 20), (26, 6)], hi)
        s.line([(7, 18), (14, 25)], GOLD if kind in ('dao', 'kopis') else IRON, 2)
        s.line([(10, 22), (5, 27)], grip if kind != 'kukri' else (70, 50, 40), 3); s.ell(2, 26, 6, 30, IRON)
    elif kind in ('saber', 'sica'):
        if kind == 'sica':
            s.poly([(10, 20), (12, 22), (18, 18), (23, 11), (24, 4), (20, 10), (15, 15)], blade)
            s.line([(8, 18), (14, 24)], GOLD, 2); s.line([(10, 22), (5, 27)], (120, 80, 50), 3)
        else:
            s.poly([(10, 20), (12, 22), (22, 16), (28, 8), (29, 2), (25, 8), (19, 14)], blade); s.line([(12, 20), (26, 8)], hi)
            s.line([(8, 18), (14, 24)], GOLD, 2); s.line([(10, 22), (6, 26), (3, 25)], IVORY, 3); s.line([(8, 18), (3, 23)], GOLD)
    elif kind == 'gladius':
        s.poly([(10, 18), (14, 22), (24, 12), (26, 5), (20, 8)], blade); s.line([(13, 19), (24, 8)], hi)
        s.line([(7, 17), (15, 25)], WOOD, 3); s.line([(10, 22), (6, 26)], IVORY, 3); s.ell(2, 25, 8, 31, WOOD)
    elif kind == 'cinquedea':
        s.poly([(6, 14), (18, 26), (27, 5)], blade); s.line([(13, 19), (25, 7)], hi); s.line([(10, 17), (22, 10)], shade(blade, -1)); s.line([(15, 22), (24, 11)], shade(blade, -1))
        s.line([(5, 15), (17, 27)], GOLD, 2); s.line([(10, 22), (6, 26)], (40, 40, 60), 3); s.ell(2, 25, 7, 30, GOLD)
    else:  # pugio
        s.poly([(11, 19), (13, 21), (20, 17), (24, 8), (15, 12)], blade); s.line([(13, 19), (23, 9)], hi)
        s.line([(8, 17), (15, 24)], GOLD, 2); s.line([(10, 22), (6, 26)], (150, 40, 40), 3); s.ell(2, 25, 7, 30, GOLD)


def p_misc(s, c):
    i = c.id
    if i in ('claymore', 'flamberge', 'estoc', 'falchion', 'dao', 'kopis', 'kukri', 'sica', 'gladius', 'cinquedea', 'pugio'):
        sword(s, c, i)
    elif i == 'mameluke_saber':
        sword(s, c, 'saber')
    elif i == 'francisca':
        s.line([(8, 28), (20, 5)], WOOD, 3)
        s.poly([(15, 6), (21, 3), (28, 5), (29, 13), (24, 11), (19, 12)], STEEL); s.line([(26, 5), (28, 12)], (226, 232, 240))
        s.line([(7, 27), (9, 24)], LEATHER, 3)
    elif i in ('naginata', 'partisan'):
        s.line([(3, 29), (20, 11)], WOOD, 2)
        if i == 'naginata':
            s.poly([(19, 12), (22, 13), (28, 8), (29, 2), (24, 5)], STEEL); s.rect(17, 11, 20, 14, GOLD)
            s.line([(8, 24), (10, 22)], (170, 40, 40), 2)
        else:
            s.poly([(18, 12), (22, 14), (29, 2)], STEEL); s.poly([(16, 10), (13, 6), (19, 10)], STEEL)
            s.poly([(22, 16), (26, 19), (22, 13)], STEEL); s.px([(13, 20), (14, 19)], (170, 40, 40))
    elif i == 'coat_of_plates':
        b = (120, 44, 44)
        s.poly([(8, 4), (13, 5), (18, 5), (23, 4), (27, 9), (24, 12), (24, 28), (7, 28), (7, 12), (4, 9)], b)
        for y in (8, 13, 18, 23):
            for x in (9, 14, 19):
                s.rect(x, y, x + 3, y + 3, STEEL)
        stip(s, b, GOLD, lambda x, y: x in (8, 13, 18, 23) and y in (7, 12, 17, 22, 27))
    elif i == 'cloth_wraps':
        w = (226, 218, 196)
        s.ell(5, 9, 22, 26, w); s.ell(10, 14, 17, 21, shade(w, -1)); s.ell(12, 16, 15, 19, w)
        s.poly([(20, 12), (28, 16), (27, 24), (24, 28), (21, 22)], w); s.line([(22, 14), (25, 26)], shade(w, -1))
    elif i == 'corpse':
        w = (206, 198, 176)
        s.poly([(3, 20), (6, 14), (12, 12), (26, 14), (29, 19), (27, 25), (8, 26)], w); s.ell(3, 13, 11, 22, w)
        for x in (10, 15, 20, 25):
            s.line([(x, 13), (x + 1, 25)], (150, 110, 70))
        s.poly([(24, 13), (28, 10), (29, 15)], w); s.px([(5, 9), (6, 8)], (150, 150, 140))
    elif i == 'rod_of_chaos':
        s.line([(6, 28), (20, 11)], (70, 50, 90), 3); s.px([(9, 24), (13, 19), (17, 15)], GOLD)
        g = s.lit((255, 110, 230)); g2 = s.lit((120, 230, 255))
        s.ell(17, 2, 28, 13, g); s.poly([(20, 5), (25, 4), (24, 9), (21, 10)], g2); s.px([(15, 4), (29, 14), (27, 1), (4, 29)], g2)
    elif i == 'flux_capacitor':
        s.rect(4, 5, 27, 27, (120, 124, 136)); s.rect(6, 7, 25, 25, (50, 52, 64))
        g = s.lit((255, 244, 170))
        s.line([(16, 16), (16, 23)], g, 2); s.line([(16, 16), (9, 9)], g, 2); s.line([(16, 16), (23, 9)], g, 2)
        s.px([(8, 8), (24, 8), (16, 24)], WHITE); s.rect(2, 12, 4, 20, (190, 60, 50)); s.rect(27, 12, 29, 20, (190, 60, 50))
    elif i == 'philosophers_amulet':
        s.line([(8, 3), (5, 10), (10, 17)], GOLD); s.line([(23, 3), (26, 10), (21, 17)], GOLD)
        s.poly([(16, 12), (25, 20), (16, 29), (7, 20)], GOLD); s.poly([(16, 16), (21, 20), (16, 25), (11, 20)], s.lit((170, 120, 255)))
        s.px([(15, 19), (16, 18)], WHITE)
    elif i == 'philosophers_shard':
        g = s.lit((255, 90, 80))
        s.poly([(10, 27), (7, 15), (14, 4), (21, 3), (25, 15), (19, 28)], (170, 30, 50)); s.poly([(14, 4), (21, 3), (18, 14), (12, 15)], g)
        s.line([(18, 14), (19, 27)], (110, 20, 40)); s.px([(4, 8), (27, 6), (26, 24)], s.lit((255, 220, 120)))
    elif i == 'philosophers_wrench':
        s.line([(8, 25), (21, 10)], GOLD, 4); s.ell(17, 2, 29, 14, GOLD); clear(s, [(x, y) for x in range(22, 31) for y in range(0, 9) if x - y >= 20 and x + y >= 26 and x + y <= 34 and x > 22])
        s.ell(3, 21, 11, 29, GOLD); s.ell(6, 24, 8, 26, DARK); s.px([(13, 19), (16, 16)], s.lit((170, 120, 255)))
    elif i == 'shadow_quiver':
        q = (60, 50, 84)
        s.poly([(9, 10), (20, 8), (24, 26), (17, 29), (12, 27)], q); s.line([(9, 13), (21, 11)], (150, 110, 230)); s.line([(11, 23), (23, 21)], (150, 110, 230))
        for x, y in ((11, 9), (14, 8), (17, 8)):
            s.line([(x, y), (x - 1, 2)], (40, 36, 50)); s.poly([(x - 3, 5), (x - 1, 1), (x + 1, 5)], s.lit((170, 120, 255)))
        s.line([(20, 9), (27, 14), (24, 25)], (40, 36, 50))
    elif 'trumpet' in i or 'brass' in i:
        b = (226, 186, 80)
        s.poly([(3, 15), (16, 14), (22, 8), (29, 5), (29, 27), (22, 23), (16, 18), (3, 17)], b)
        s.ell(25, 5, 30, 27, shade(b, -1)); s.rect(8, 11, 10, 15, b); s.rect(12, 11, 14, 15, b)
        s.poly([(8, 18), (14, 18), (12, 27), (9, 24)], (150, 40, 50)); s.px([(18, 13), (22, 10)], s.lit((255, 244, 170)))
    elif 'chain_link' in i:
        s.ell(3, 5, 18, 20, IRON); clear(s, [(x, y) for x in range(7, 15) for y in range(9, 17) if (x - 10.5) ** 2 + (y - 12.5) ** 2 < 13])
        s.ell(13, 12, 28, 27, shade(IRON, 1)); clear(s, [(x, y) for x in range(17, 25) for y in range(16, 24) if (x - 20.5) ** 2 + (y - 19.5) ** 2 < 13])
        s.px([(4, 3), (2, 6), (27, 28), (29, 25), (15, 16)], s.lit((255, 140, 60)))
    elif 'executioners_iron' in i:
        s.line([(6, 28), (15, 12)], WOOD, 3)
        s.poly([(10, 12), (15, 5), (24, 3), (29, 10), (27, 20), (20, 16), (14, 15)], (90, 92, 104)); s.line([(24, 4), (28, 11), (27, 19)], (190, 196, 210))
        s.px([(17, 9), (18, 10)], (60, 60, 70))
    elif 'mimic_gold' in i:
        s.poly([(4, 24), (8, 14), (16, 10), (24, 13), (28, 24), (22, 28), (9, 28)], (236, 190, 60))
        s.ell(8, 12, 14, 16, (250, 220, 110)); s.ell(17, 13, 23, 17, (250, 220, 110)); s.ell(12, 17, 19, 21, (250, 220, 110))
        s.poly([(8, 23), (11, 20), (13, 23), (16, 20), (19, 23), (21, 20), (24, 23), (22, 26), (10, 26)], DARK)
        s.px([(11, 21), (16, 21), (21, 21)], WHITE); s.px([(13, 25), (18, 25)], (220, 80, 110)); s.px([(12, 9), (20, 9)], s.lit((255, 244, 170)))
    elif 'clockwork' in i or 'gear' in i:
        b = (200, 160, 80)
        for k in range(8):
            import math
            a = k * math.pi / 4
            cx, cy = 15.5 + 11 * math.cos(a), 15.5 + 11 * math.sin(a)
            s.rect(int(cx - 1.5), int(cy - 1.5), int(cx + 2), int(cy + 2), b)
        s.ell(6, 6, 25, 25, b); s.ell(10, 10, 21, 21, shade(b, -1)); s.ell(13, 13, 18, 18, DARK); s.px([(9, 9), (10, 8)], (250, 230, 160))
    elif 'signet' in i:
        s.ell(7, 10, 24, 29, GOLD); clear(s, [(x, y) for x in range(10, 22) for y in range(15, 27) if (x - 15.5) ** 2 + (y - 20.5) ** 2 < 28])
        s.ell(9, 3, 22, 15, GOLD); s.ell(11, 5, 20, 13, (170, 40, 50)); s.px([(15, 8), (16, 8), (15, 9), (16, 9), (14, 9), (17, 9), (15, 10), (16, 7)], GOLD)
    elif 'seal' in i:
        w = (176, 36, 40)
        s.poly([(10, 20), (6, 30), (11, 27), (14, 30), (15, 21)], (226, 214, 180)); s.poly([(17, 21), (19, 30), (22, 27), (26, 29), (22, 19)], (226, 214, 180))
        for k in range(10):
            import math
            a = k * math.pi / 5
            cx, cy = 15.5 + 9 * math.cos(a), 13 + 9 * math.sin(a)
            s.ell(int(cx - 2), int(cy - 2), int(cx + 2), int(cy + 2), w)
        s.ell(6, 4, 25, 22, w); s.ell(10, 8, 21, 18, shade(w, -1)); s.line([(15, 9), (15, 17)], GOLD, 2); s.line([(12, 12), (19, 12)], GOLD, 2)
    elif 'mask' in i:
        m = (226, 220, 200)
        s.poly([(8, 4), (20, 3), (26, 10), (22, 18), (24, 28), (15, 22), (9, 15)], m)
        s.ell(12, 7, 19, 12, DARK); s.px([(15, 9), (16, 9)], s.lit((255, 220, 120)))
        s.poly([(17, 17), (21, 16), (21, 24)], IVORY); s.line([(9, 5), (19, 4)], (190, 40, 40), 2); s.px([(11, 13), (12, 14), (14, 16)], (190, 40, 40))
        s.px([(22, 8), (23, 9)], GOLD)
    elif 'phylactery' in i:
        m = c.m if not c.has('lord') else (70, 60, 100)
        g = s.lit(c.g or (140, 240, 170))
        s.rect(7, 12, 24, 27, m); s.rect(5, 9, 26, 12, GOLD); s.rect(5, 26, 26, 28, GOLD); s.rect(12, 5, 19, 9, GOLD); s.ell(13, 1, 18, 6, g)
        s.poly([(15, 14), (20, 19), (16, 24), (11, 19)], g); s.rect(7, 12, 8, 27, GOLD); s.rect(23, 12, 24, 27, GOLD)
        if c.has('plague'):
            s.px([(3, 6), (28, 4), (27, 16), (4, 20)], g)
        if c.has('death_mage'):
            s.px([(14, 18), (17, 18)], DARK)
    elif 'tablet' in i:
        st = (130, 130, 140)
        g = s.lit((140, 240, 170))
        if i.startswith('complete'):
            s.poly([(6, 28), (6, 8), (10, 3), (22, 3), (26, 8), (26, 28)], st); s.rect(6, 26, 26, 28, GOLD); s.rect(6, 8, 26, 9, GOLD)
        else:
            s.poly([(6, 28), (6, 8), (10, 3), (22, 3), (26, 8), (26, 14), (20, 17), (22, 22), (16, 24), (17, 28)], st)
        for y in (12, 16, 20, 24):
            for x in (9, 13, 17, 21):
                if s.img.getpixel((x + 1, y))[:3] == st and (x + y) % 3:
                    s.px([(x, y), (x + 1, y)], g)
        s.ell(13, 4, 18, 8, DARK); s.px([(15, 6), (16, 6)], g)
    elif 'necromantic_focus' in i:
        g = s.lit((140, 240, 150))
        s.line([(16, 16), (16, 28)], (70, 60, 80), 3); s.rect(11, 27, 21, 29, (70, 60, 80))
        s.ell(8, 2, 23, 17, g); s.ell(11, 5, 20, 14, BONE); s.px([(13, 9), (14, 9), (17, 9), (18, 9), (15, 12), (16, 12)], DARK)
        s.poly([(8, 14), (6, 20), (12, 17)], (70, 60, 80)); s.poly([(23, 14), (25, 20), (19, 17)], (70, 60, 80))
    elif 'false_holy_relic' in i:
        s.rect(13, 4, 18, 27, (190, 150, 70)); s.rect(7, 9, 24, 14, (190, 150, 70)); s.rect(10, 26, 21, 29, (120, 90, 50))
        s.ell(13, 9, 18, 14, (110, 180, 120)); s.line([(14, 16), (17, 21), (15, 25)], (90, 80, 60)); s.px([(9, 11), (22, 12), (15, 6)], (120, 150, 110))
        s.px([(16, 11)], s.lit((200, 110, 240)))
    elif 'quiver' in i:
        pass
    else:
        return False
    return True


def p_food(s, c):
    i = c.id
    if i in ('apple', 'golden_apple'):
        a = (206, 44, 44) if i == 'apple' else s.lit((250, 214, 80))
        s.ell(5, 9, 18, 28, a); s.ell(13, 9, 26, 28, a); s.line([(16, 10), (18, 3)], WOOD, 2); s.poly([(18, 6), (24, 3), (25, 7), (21, 9)], LEAF)
        s.px([(8, 14), (9, 13), (8, 15), (10, 12)], WHITE if i == 'apple' else (255, 250, 220))
        if i != 'apple':
            sparkle(s, c, s.lit((255, 250, 200)), 4, (2, 2, 29, 8))
    elif 'peach' in i:
        p = (250, 170, 130)
        s.ell(5, 8, 26, 28, p); s.line([(16, 9), (14, 20), (16, 27)], (226, 110, 110)); s.ell(18, 13, 24, 21, (240, 120, 120))
        s.poly([(16, 9), (22, 3), (27, 5), (22, 10)], LEAF); s.px([(9, 13), (10, 12)], WHITE); sparkle(s, c, s.lit((255, 240, 190)), 4, (2, 1, 28, 7))
    elif 'plum' in i:
        p = (110, 50, 140)
        s.ell(7, 10, 25, 28, p); s.line([(16, 11), (13, 4)], WOOD, 2); s.poly([(13, 5), (6, 3), (8, 8)], LEAF); s.px([(11, 15), (12, 14), (11, 16)], (200, 170, 230))
        s.px([(22, 4), (26, 8)], s.lit((150, 220, 255)))
    elif 'ambrosia' in i:
        g = s.lit((255, 236, 150))
        s.poly([(7, 10), (24, 10), (21, 18), (18, 20), (18, 25), (22, 28), (9, 28), (13, 25), (13, 20), (10, 18)], GOLD)
        s.ell(7, 7, 24, 13, shade(GOLD, 1)); s.ell(9, 8, 22, 12, g); s.px([(12, 4), (16, 2), (20, 4), (15, 5)], g)
        s.px([(10, 15), (16, 23)], (190, 60, 90))
    elif i in ('bread_ration', 'elvish_bread'):
        if i == 'elvish_bread':
            s.poly([(3, 18), (12, 8), (27, 6), (28, 18), (18, 27), (5, 26)], (90, 150, 80))
            s.poly([(9, 17), (15, 11), (24, 10), (24, 17), (17, 23), (9, 23)], (240, 220, 160)); s.line([(11, 21), (23, 11)], (206, 180, 110))
            s.line([(4, 25), (27, 7)], (60, 110, 60)); s.px([(26, 4), (4, 12)], s.lit((220, 250, 190)))
        else:
            loaf(s, c, CRUST)
    elif 'dried_meat' in i:
        m = (130, 50, 44)
        s.poly([(4, 8), (11, 5), (14, 26), (8, 28)], m); s.poly([(13, 6), (19, 4), (22, 22), (17, 26)], shade(m, 1)); s.poly([(21, 8), (27, 6), (28, 24), (24, 27)], m)
        s.line([(7, 10), (10, 24)], (90, 30, 30)); s.line([(16, 8), (19, 22)], (96, 36, 32)); s.line([(24, 10), (26, 23)], (90, 30, 30))
        s.line([(3, 14), (29, 12)], (206, 184, 130))
    elif 'cheese' in i:
        ch = (240, 196, 70)
        s.poly([(3, 20), (22, 8), (28, 12), (28, 24), (9, 28), (3, 26)], ch); s.poly([(3, 20), (22, 8), (28, 12), (9, 22)], (250, 220, 110))
        s.ell(12, 22, 15, 25, (200, 150, 40)); s.ell(20, 18, 24, 22, (200, 150, 40)); s.px([(6, 24), (25, 15)], (200, 150, 40)); s.line([(3, 26), (9, 28), (28, 24)], (220, 150, 50))
    elif 'hearty_stew' in i:
        d_stew(s, c)
    elif i in ('trail_rations', 'battle_ration', 'void_ration'):
        w = {'trail_rations': (206, 184, 130), 'battle_ration': (130, 110, 80), 'void_ration': (60, 44, 96)}[i]
        s.poly([(4, 13), (20, 8), (28, 13), (28, 24), (12, 29), (4, 24)], w); s.poly([(4, 13), (20, 8), (28, 13), (12, 18)], shade(w, 1))
        s.line([(12, 18), (12, 29)], shade(w, -1))
        if i == 'trail_rations':
            s.line([(8, 11), (20, 27)], (150, 60, 50)); s.line([(24, 11), (8, 16)], (150, 60, 50)); s.ell(14, 11, 18, 14, (150, 60, 50))
            s.ell(22, 2, 27, 6, (150, 100, 60)); s.ell(17, 1, 21, 5, (190, 40, 60))
        elif i == 'battle_ration':
            s.rect(15, 10, 19, 28, IRON); s.rect(14, 16, 20, 20, STEEL); s.poly([(6, 6), (14, 3), (17, 6), (9, 9)], (226, 196, 140))
            s.px([(9, 6), (12, 5), (14, 6)], (170, 130, 80))
        else:
            g = s.lit((190, 130, 255)); s.line([(8, 11), (20, 27)], g); s.line([(24, 11), (8, 16)], g); sparkle(s, c, g, 4, (3, 1, 28, 7))
    elif 'tea' in i:
        d_cup(s, c)
    else:
        return False
    return True


# ================================================================== DISHES
def loaf(s, c, crust=CRUST, top=None):
    s.ell(3, 10, 28, 27, crust); s.rect(5, 20, 26, 26, crust); s.rect(4, 25, 27, 27, shade(crust, -1))
    for x in (9, 15, 21):
        s.line([(x, 13), (x + 3, 19)], (244, 220, 160), 2)
    if top:
        garnish(s, c, 12, 6, top)


def bits(s, c, y0, cols, n=5, x0=8, x1=23):
    for k in range(n):
        x = x0 + (k * (x1 - x0)) // max(1, n - 1) + c.r.randint(-1, 1)
        y = y0 + c.r.randint(0, 2)
        col = cols[k % len(cols)]
        s.rect(x, y, x + 1 + (k % 2), y + 1, col)


def liquid_for(c, base, t=0.45):
    return mix(base, c.m, t)


def d_stew(s, c):
    kind = next((k for k in ('goulash', 'ragout', 'fricassee', 'brais', 'royale') if k in c.core), 'stew')
    base = {'goulash': (176, 60, 36), 'ragout': (150, 70, 40), 'fricassee': (232, 214, 170), 'brais': (110, 64, 44),
            'royale': (130, 50, 70), 'stew': (150, 84, 44)}[kind]
    liq = liquid_for(c, base, 0.3)
    top = bowl(s, c, liq, deep=True)
    if kind == 'ragout':
        for k in range(4):
            s.line([(7 + k * 4, top + 2 + k % 2), (11 + k * 4, top + 4 - k % 2), (14 + k * 4, top + 3)], (244, 214, 120))
    if kind in ('brais', 'royale'):
        mt = mix((120, 60, 40), c.m, 0.35)
        s.ell(10, top - 2, 21, top + 5, mt); s.px([(13, top), (14, top - 1)], shade(mt, 2))
        bits(s, c, top + 3, [(232, 140, 50), (90, 150, 70)], 2, 7, 23)
    else:
        bits(s, c, top + 2, [c.a if sum(c.a) > 200 else (200, 150, 90), (232, 140, 50), (226, 206, 150), (90, 150, 70)], 6)
    if kind == 'goulash':
        s.ell(13, top + 1, 18, top + 4, WHITE); s.px([(15, top + 1), (17, top + 3)], (210, 50, 40))
    h = herb_of(c)
    if h and kind != 'goulash':
        garnish(s, c, 6, top, h)
    s.line([(22, top + 3), (29, top - 7)], (176, 130, 80), 2)   # spoon
    steam(s, (9, 14), 3, top - 2)
    if c.g:
        s.px([(12, top + 3), (19, top + 2)], s.lit(c.g))


def d_soup(s, c):
    kind = next((k for k in ('bisque', 'chowder', 'consomme', 'bouillabaisse', 'broth', 'soup') if k in c.core), 'soup')
    base = {'bisque': (232, 150, 96), 'chowder': (240, 230, 196), 'consomme': (226, 170, 70), 'bouillabaisse': (220, 110, 50),
            'broth': (214, 170, 96), 'soup': (200, 150, 80)}[kind]
    liq = liquid_for(c, base, 0.4 if kind != 'chowder' else 0.2)
    if c.g and kind in ('consomme', 'broth'):
        liq = s.lit(mix(liq, c.g, 0.4))
    if kind == 'bisque':       # wide shallow soup plate
        b = BOWLS[c.h % len(BOWLS)]
        s.ell(1, 14, 30, 28, b); s.ell(4, 16, 27, 26, shade(b, 1)); s.ell(6, 17, 25, 25, liq); top = 17
    elif kind == 'consomme':   # two-handled cup
        b = (236, 230, 214) if c.h % 2 else (200, 214, 230)
        top = bowl(s, c, liq, mat=b)
        s.rect(1, top + 4, 3, top + 8, b); s.rect(28, top + 4, 30, top + 8, b); s.line([(6, 22), (25, 22)], GOLD)
    elif kind == 'chowder':    # bread bowl
        top = bowl(s, c, liq, mat=(206, 150, 74))
        s.px([(8, 24), (12, 26), (17, 25), (22, 24), (20, 27)], (244, 220, 160))
    elif kind == 'broth':
        top = bowl(s, c, liq, deep=True)
    else:
        top = bowl(s, c, liq)
    if kind in ('bisque', 'chowder'):
        s.line([(10, top + 3), (14, top + 2), (18, top + 4), (21, top + 3)], WHITE)
        bits(s, c, top + 3, [c.a, (240, 140, 60)], 2, 9, 20)
    elif kind == 'bouillabaisse':
        s.poly([(8, top + 1), (13, top - 1), (15, top + 3)], (236, 100, 70)); s.ell(17, top + 1, 21, top + 4, (60, 60, 80))
    else:
        bits(s, c, top + 2, [(90, 160, 80), c.a, WHITE], 4)
    h = herb_of(c)
    if h:
        garnish(s, c, 13, top, h)
    steam(s, (10, 16, 22), 3, top - 1)
    if c.g:
        s.px([(9, top + 3), (22, top + 3)], s.lit(c.g))


def d_pot(s, c):
    iron = (74, 74, 88) if c.h % 2 else (150, 96, 60)
    liq = liquid_for(c, (160, 90, 44), 0.4)
    s.ell(4, 11, 27, 29, iron); s.ell(3, 9, 28, 17, shade(iron, 1)); s.ell(5, 10, 26, 16, liq)
    s.rect(1, 15, 3, 19, iron); s.rect(28, 15, 30, 19, iron)
    bits(s, c, 11, [c.a, (232, 140, 50), (226, 206, 150), (90, 150, 70)], 6)
    s.px([(9, 21), (9, 22), (10, 20)], shade(iron, 2))
    h = herb_of(c)
    if h:
        garnish(s, c, 13, 10, h)
    steam(s, (10, 16, 22), 2, 8)
    if c.g:
        s.px([(11, 13), (20, 12)], s.lit(c.g))


def d_roast(s, c):
    plate(s, c)
    skin = mix((176, 100, 50), c.m, 0.3)
    if c.has('haunch'):
        s.ell(5, 7, 22, 23, skin); s.poly([(17, 18), (22, 14), (27, 20), (25, 23)], skin)
        s.line([(24, 19), (29, 24)], IVORY, 3); s.px([(8, 11), (9, 10), (10, 10)], (240, 190, 120))
        s.line([(9, 18), (17, 20)], shade(skin, -1))
    else:
        s.ell(5, 8, 26, 23, skin)
        s.ell(3, 13, 10, 19, shade(skin, 1)); s.ell(21, 13, 28, 19, shade(skin, 1))
        s.line([(4, 12), (2, 8)], IVORY, 2); s.line([(27, 12), (29, 8)], IVORY, 2)
        s.px([(10, 11), (11, 10), (12, 10), (13, 10)], (244, 196, 130))
        s.line([(12, 15), (19, 15)], shade(skin, -1))
        if c.has('dragon', 'chimera', 'nidhoggr', 'basilisk'):
            s.px([(14, 12), (17, 13), (20, 12), (16, 17), (11, 17)], shade(c.m, -1))
    garnish(s, c, 4, 22); garnish(s, c, 21, 22, ['berries', 'lemon', 'parsley'][c.h % 3] if herb_of(c) else None)
    steam(s, (12, 19), 1, 6)
    if c.g:
        s.px([(15, 9), (9, 14), (22, 17)], s.lit(c.g))


def d_feast(s, c):
    # platter with a roast bird, a goblet and fruit
    b = (196, 150, 70) if c.h % 2 else (150, 156, 170)
    s.ell(1, 18, 30, 30, b); s.ell(4, 20, 27, 28, shade(b, -1))
    skin = mix((180, 104, 50), c.m, 0.3)
    s.ell(4, 11, 20, 24, skin); s.line([(5, 13), (2, 8)], IVORY, 2); s.line([(17, 12), (20, 7)], IVORY, 2)
    s.px([(8, 14), (9, 13), (10, 13)], (244, 196, 130))
    gob = GOLD if c.h % 3 else STEEL
    s.poly([(21, 5), (29, 5), (27, 12), (26, 13), (26, 19), (28, 21), (22, 21), (24, 19), (24, 13), (23, 12)], gob)
    wine = c.g or c.a
    s.rect(22, 5, 28, 6, s.lit(wine) if c.g else mix(wine, (150, 30, 60), 0.5))
    s.ell(8, 23, 12, 27, (190, 40, 60)); s.ell(12, 24, 16, 28, (110, 50, 140)); s.ell(16, 23, 20, 27, (240, 190, 60))
    garnish(s, c, 20, 23)
    steam(s, (8, 13), 2, 9)


def d_pie(s, c):
    tin = (150, 156, 170)
    fill = mix((150, 60, 50), c.m, 0.5)
    s.poly([(3, 18), (28, 18), (25, 27), (6, 27)], tin)
    s.ell(2, 9, 29, 22, CRUST); s.ell(5, 11, 26, 20, (232, 180, 96))
    if c.has('tourte', 'bake'):
        s.ell(12, 13, 19, 17, shade(CRUST, -1)); s.px([(15, 15), (16, 15)], fill)
        for a, b in (((8, 13), (11, 16)), ((23, 13), (20, 16)), ((15, 12), (15, 11))):
            s.line([a, b], shade(CRUST, -1))
    else:
        for x in (8, 13, 18, 23):
            s.line([(x, 11), (x - 3, 20)], CRUST)
        for y in (13, 16, 18):
            s.line([(5, y), (26, y)], fill)
        s.poly([(16, 15), (27, 12), (27, 19)], fill); s.line([(16, 15), (27, 12)], shade(fill, -2))
    stip(s, CRUST, shade(CRUST, -1), lambda x, y: y in (9, 10, 21, 22) and x % 3 == 0)
    steam(s, (11, 17), 1, 7)
    if c.g:
        s.px([(22, 15), (24, 16)], s.lit(c.g))


def d_skewer(s, c):
    s.line([(2, 29), (29, 2)], (190, 160, 110), 1)
    cols = [mix((170, 90, 50), c.m, 0.45), (226, 80, 50), mix((170, 90, 50), c.a, 0.5), (240, 200, 80), (90, 150, 70)]
    if c.g:
        cols[1] = s.lit(c.g)
    order = [0, 1 + c.h % 4, 2, 1 + (c.h // 4) % 4, 0]
    for k, ci in enumerate(order):
        x, y = 6 + k * 4, 21 - k * 4
        col = cols[ci]
        if ci in (0, 2):
            s.poly([(x - 2, y), (x + 2, y - 4), (x + 5, y - 1), (x + 1, y + 3)], col)
            s.line([(x, y - 1), (x + 2, y + 1)], shade(col, -2))
        else:
            s.ell(x - 1, y - 3, x + 4, y + 2, col)
    s.px([(3, 28), (2, 29), (1, 30)], (150, 110, 70))
    steam(s, (8,), 5, 12)


def d_steak(s, c):
    plate(s, c)
    kind = next((k for k in ('medallion', 'cutlet', 'steak') if k in c.core), 'steak')
    m = mix((150, 76, 50), c.m, 0.35)
    if kind == 'medallion':
        for (x, y) in ((6, 12), (15, 9), (12, 16)):
            s.ell(x, y, x + 10, y + 8, m); s.ell(x + 2, y + 2, x + 8, y + 6, mix(m, (226, 110, 100), 0.5))
        s.line([(20, 21), (25, 18)], (110, 50, 30), 2)
    elif kind == 'cutlet':
        for ox in (0, 9):
            s.poly([(6 + ox, 14), (10 + ox, 9), (16 + ox, 10), (17 + ox, 18), (12 + ox, 23), (7 + ox, 20)], m)
            s.line([(15 + ox, 10), (19 + ox, 4)], IVORY, 2)
            s.line([(9 + ox, 14), (14 + ox, 17)], shade(m, -2)); s.line([(10 + ox, 11), (15 + ox, 14)], shade(m, -2))
    else:
        s.poly([(5, 15), (9, 9), (18, 8), (25, 12), (26, 19), (19, 23), (9, 22)], m)
        for k in range(4):
            s.line([(9 + k * 4, 11), (7 + k * 4, 20)], shade(m, -2))
        s.ell(18, 10, 23, 14, (244, 226, 130))
    garnish(s, c, 22, 20);
    if c.g:
        s.px([(10, 12), (17, 17)], s.lit(c.g))
    steam(s, (12,), 1, 6)


def d_tartare(s, c):
    plate(s, c)
    m = mix((196, 60, 60), c.m, 0.4)
    s.rect(9, 12, 22, 23, m); s.ell(9, 9, 22, 15, shade(m, 1)); s.ell(9, 20, 22, 25, m)
    stip(s, m, shade(m, -1), lambda x, y: (x * 3 + y * 5) % 7 == 0)
    s.ell(13, 9, 18, 13, (250, 200, 60)); s.px([(14, 10)], WHITE)
    garnish(s, c, 3, 21); s.px([(24, 22), (26, 23), (25, 25)], (90, 150, 70))
    if c.g:
        s.px([(11, 17), (20, 19)], s.lit(c.g))


def d_cup(s, c):
    b = BOWLS[(c.h // 3) % len(BOWLS)]
    if b == (74, 74, 88):
        b = (226, 214, 190)
    liq = mix((150, 110, 50), c.m, 0.5)
    s.ell(2, 23, 29, 30, shade(b, -1)); s.poly([(7, 12), (24, 12), (22, 24), (19, 26), (12, 26), (9, 24)], b)
    s.ell(6, 9, 25, 15, shade(b, 1)); s.ell(8, 10, 23, 14, s.lit(mix(liq, c.g, 0.4)) if c.g else liq)
    s.line([(24, 14), (28, 15), (28, 19), (23, 21)], b, 2)
    s.line([(9, 19), (22, 19)], GOLD if c.h % 2 else shade(b, -1))
    garnish(s, c, 12, 9) if herb_of(c) else None
    steam(s, (12, 17), 1, 8)


def d_elixir(s, c):
    liq = c.m if sum(c.m) > 200 else shade(c.m, 2)
    bottle(s, c, liq, c.g or shade(liq, 2))
    if c.has('ferment', 'brew'):
        s.px([(14, 20), (17, 18), (15, 23), (12, 22)], WHITE)


def d_sauce(s, c):
    # saucepan with a thick reduction, or a glazed joint
    if c.has('glaze'):
        board(s, c)
        m = mix((170, 96, 50), c.m, 0.3)
        s.ell(6, 8, 25, 23, m); gl = s.lit(c.g) if c.g else (250, 210, 120)
        s.line([(9, 11), (15, 9), (21, 11)], gl); s.px([(10, 13), (10, 14), (16, 11), (16, 12), (16, 13), (22, 13), (22, 14), (22, 15)], gl)
        s.line([(24, 18), (29, 22)], IVORY, 3)
        for x in (9, 14, 19):
            s.line([(x, 16), (x + 3, 21)], shade(m, -1))
        return
    pan = (176, 110, 60) if c.h % 2 else (90, 92, 104)
    liq = mix((90, 40, 40), c.m, 0.45)
    s.poly([(4, 15), (23, 15), (21, 27), (6, 27)], pan); s.ell(3, 11, 24, 19, shade(pan, 1)); s.ell(5, 12, 22, 18, s.lit(mix(liq, c.g, 0.3)) if c.g else liq)
    s.line([(23, 15), (30, 11)], (70, 50, 40), 3)
    s.px([(9, 14), (10, 14), (16, 16)], shade(liq, 2)); s.line([(14, 14), (19, 4)], (190, 160, 110), 2)
    steam(s, (8, 12), 2, 9)
    h = herb_of(c)
    if h:
        garnish(s, c, 24, 22, h)


def d_loaf(s, c):
    cr = mix(CRUST, c.m, 0.25)
    board(s, c); loaf(s, c, cr, herb_of(c))
    if c.has('lich', 'nightshade', 'wormwood'):
        stip(s, cr, shade(cr, -2), lambda x, y: (x * 7 + y * 3) % 13 == 0)
    if c.g:
        s.px([(7, 16), (24, 17)], s.lit(c.g))


def d_salad(s, c):
    top = bowl(s, c, (90, 150, 70), mat=(160, 110, 66))
    for (x, y, col) in ((7, top - 2, (110, 180, 80)), (13, top - 4, (70, 140, 70)), (19, top - 3, (130, 196, 90)), (10, top + 1, (80, 160, 80)), (17, top + 1, (110, 180, 80))):
        s.ell(x, y, x + 7, y + 5, col)
    s.ell(10, top - 1, 13, top + 2, (220, 50, 50)); s.ell(20, top + 1, 23, top + 4, (220, 50, 50))
    s.px([(15, top - 2), (18, top + 2), (9, top + 3)], c.a if sum(c.a) > 300 else (240, 220, 120))
    if c.g:
        s.px([(16, top), (22, top - 1)], s.lit(c.g))
    if c.has('heartwood'):
        s.line([(14, top - 5), (20, top - 8)], (150, 96, 50), 2)


def d_curry(s, c):
    cur = mix((226, 150, 40), c.m, 0.35)
    top = bowl(s, c, cur)
    s.ell(5, top, 16, top + 6, WHITE); s.px([(8, top + 2), (11, top + 4), (12, top + 1)], (220, 216, 200))
    bits(s, c, top + 2, [shade(cur, -2), (90, 150, 70)], 3, 17, 23)
    s.poly([(18, top - 1), (23, top - 2), (25, top + 1), (20, top + 1)], (210, 44, 36))
    steam(s, (10, 16, 22), 3, top - 2)
    if c.g:
        s.px([(20, top + 4)], s.lit(c.g))


def d_dumplings(s, c):
    b = (190, 150, 90)
    s.rect(3, 17, 28, 27, b); s.ell(3, 12, 28, 21, shade(b, 1)); s.ell(5, 13, 26, 20, (120, 150, 90))
    for y in (22, 25):
        s.line([(3, y), (28, y)], shade(b, -1))
    d = mix((240, 232, 214), c.m, 0.12)
    for (x, y) in ((6, 11), (15, 10), (11, 15)):
        s.ell(x, y, x + 9, y + 6, d); s.px([(x + 3, y), (x + 5, y), (x + 4, y - 1)], d); s.line([(x + 3, y + 1), (x + 5, y + 3)], shade(d, -1))
    steam(s, (9, 16, 23), 1, 8)


def d_risotto(s, c):
    plate(s, c, (70, 112, 176) if c.h % 2 else None)
    r = mix((240, 230, 196), c.m, 0.25)
    s.ell(6, 11, 25, 24, r)
    stip(s, r, shade(r, -1), lambda x, y: (x * 5 + y * 7) % 6 == 0)
    g = s.lit(c.g) if c.g else (90, 150, 70)
    s.px([(11, 14), (15, 12), (19, 15), (13, 19), (20, 20), (16, 17)], g)
    garnish(s, c, 13, 8, herb_of(c) or 'parsley')
    steam(s, (10, 21), 1, 7)


def d_roulade(s, c):
    board(s, c)
    out, inn = mix((190, 120, 70), c.m, 0.35), mix((226, 200, 150), c.a, 0.3)
    for (x, y) in ((4, 9), (12, 8), (20, 10)):
        s.ell(x, y, x + 9, y + 11, out); s.ell(x + 2, y + 2, x + 7, y + 9, inn); s.ell(x + 3, y + 4, x + 6, y + 7, out)
        s.px([(x + 4, y + 5)], s.lit(c.g) if c.g else (90, 150, 70))
    garnish(s, c, 14, 22)


def d_terrine(s, c):
    plate(s, c)
    m = mix((214, 170, 150), c.m, 0.3)
    s.poly([(6, 12), (20, 9), (26, 12), (26, 21), (12, 24), (6, 21)], m); s.poly([(6, 12), (20, 9), (26, 12), (12, 15)], shade(m, 1))
    cols = [(90, 150, 70), (226, 110, 60), c.a, (244, 226, 160)]
    for k, (x, y) in enumerate(((8, 17), (10, 20), (14, 18), (18, 19), (22, 16), (20, 21), (16, 21), (23, 19))):
        s.rect(x, y, x + 1, y + 1, cols[k % 4])
    s.line([(12, 15), (12, 24)], shade(m, -1))
    garnish(s, c, 3, 22)
    if c.g:
        s.px([(15, 12), (20, 12)], s.lit(c.g))


def d_souffle(s, c):
    r = (232, 226, 214)
    top = mix((244, 214, 130), c.m, 0.3)
    s.rect(7, 16, 24, 28, r); s.ell(5, 4, 26, 19, top); s.rect(6, 14, 25, 17, r)
    for x in range(8, 24, 3):
        s.line([(x, 18), (x, 27)], shade(r, -1))
    s.ell(9, 6, 15, 9, shade(top, 1)); s.px([(18, 8), (20, 11), (12, 12)], shade(top, -1))
    steam(s, (11, 19), 0, 3)
    if c.g:
        s.px([(16, 6), (21, 9)], s.lit(c.g))


def d_jelly(s, c):
    plate(s, c)
    j = c.m if sum(c.m) > 260 else shade(c.m, 2)
    s.poly([(7, 23), (9, 11), (13, 7), (19, 7), (23, 11), (25, 23), (16, 26)], j)
    s.line([(12, 9), (10, 22)], shade(j, 1)); s.line([(20, 9), (22, 22)], shade(j, -1)); s.line([(16, 8), (16, 25)], shade(j, 1))
    s.px([(11, 12), (11, 13)], WHITE)
    if c.has('eye'):
        s.ell(13, 13, 19, 19, WHITE); s.ell(15, 15, 17, 17, DARK)
    elif c.has('spider', 'silk'):
        s.line([(10, 16), (22, 14)], WHITE); s.line([(12, 21), (20, 10)], WHITE)
    else:
        s.ell(14, 3, 18, 7, (220, 50, 60))
    if c.g:
        s.px([(14, 17), (18, 14)], s.lit(c.g))


def d_crisps(s, c):
    top = bowl(s, c, (120, 80, 50))
    ch = mix((232, 190, 96), c.m, 0.3)
    for k, (x, y) in enumerate(((6, top - 2), (12, top - 5), (18, top - 3), (9, top + 1), (16, top), (21, top + 1), (13, top - 1))):
        col = ch if k % 2 else shade(ch, 1)
        s.poly([(x, y + 3), (x + 3, y), (x + 7, y + 2), (x + 4, y + 6)], col)
    s.px([(10, top - 1), (20, top - 1), (15, top - 3)], (214, 84, 36) if c.has('pepper') else WHITE)


def d_hash(s, c):
    pan = (70, 70, 84)
    s.ell(2, 12, 25, 28, pan); s.ell(4, 14, 23, 26, shade(pan, -1)); s.line([(23, 16), (30, 8)], pan, 3)
    cols = [mix((200, 150, 80), c.m, 0.4), (226, 190, 110), (90, 150, 70), mix((170, 90, 60), c.a, 0.4)]
    for k in range(12):
        x, y = 6 + (k * 5) % 15, 15 + (k * 3) % 9
        s.rect(x, y, x + 1, y + 1, cols[k % 4])
    s.ell(10, 16, 17, 22, WHITE); s.ell(12, 18, 15, 20, (250, 200, 60))
    steam(s, (8, 14), 3, 11)
    if c.g:
        s.px([(19, 22), (7, 20)], s.lit(c.g))


def d_platter(s, c):
    board(s, c)
    m, a = mix((190, 130, 80), c.m, 0.45), mix((226, 200, 150), c.a, 0.35)
    if c.has('canape'):
        for (x, y) in ((5, 13), (13, 11), (21, 12)):
            s.rect(x, y + 4, x + 6, y + 7, (226, 190, 120)); s.ell(x, y, x + 6, y + 5, m); s.px([(x + 3, y - 1), (x + 3, y - 2)], LEAF)
        return
    s.poly([(5, 20), (8, 12), (13, 10), (15, 20)], m); s.ell(13, 9, 21, 17, a); s.poly([(19, 19), (24, 9), (28, 12), (26, 21)], shade(m, -1))
    s.ell(9, 19, 13, 23, (190, 40, 60)); s.ell(15, 18, 19, 22, (110, 50, 140))
    garnish(s, c, 20, 20)
    if c.g:
        s.px([(16, 12), (17, 13), (9, 14)], s.lit(c.g))


def d_jar(s, c):
    """'X infused Y': a sealed jar of Y steeping with herb X."""
    herb = herb_of(c)
    liq = mix((226, 200, 130), c.a if len(c.all) > 1 else c.m, 0.45)
    s.rect(6, 10, 25, 28, GLASS); s.rect(8, 13, 23, 26, s.lit(mix(liq, c.g2, 0.3)) if c.g2 else liq)
    s.rect(8, 6, 23, 10, (206, 184, 130)); s.line([(8, 9), (23, 9)], (150, 60, 50)); s.rect(10, 3, 21, 6, CORK)
    main = c.a if len(c.all) > 1 else shade(c.m, -1)
    s.poly([(14, 17), (19, 16), (21, 21), (17, 25), (13, 22)], main); s.px([(15, 18)], shade(main, 2))
    garnish(s, c, 9, 15, herb); s.px([(9, 14), (9, 15), (9, 17)], WHITE)
    if c.g2:
        s.px([(17, 20), (20, 14)], s.lit(c.g2))


def d_with(s, c):
    """'<method> X with Y': X plated with garnish Y."""
    plate(s, c)
    method = c.core.split('_')[0]
    base = {'charred': (70, 56, 56), 'blackened': (56, 50, 56), 'baked': (214, 160, 90), 'smoked': (150, 100, 70),
            'braised': (140, 80, 50), 'caramelized': (206, 130, 50), 'cured': (190, 90, 90), 'poached': (236, 220, 200),
            'seared': (160, 90, 60), 'grilled': (170, 110, 60), 'herbed': (150, 150, 90), 'slow': (140, 84, 54),
            'simmered': (170, 110, 70), 'spiced': (200, 100, 50), 'salt': (226, 220, 210), 'fire': (190, 90, 40),
            'ember': (190, 80, 40), 'flame': (180, 90, 50), 'torch': (190, 100, 50), 'cavern': (150, 120, 96),
            'ash': (130, 120, 116), 'wild': (130, 140, 80), 'honey': (230, 170, 60)}.get(method, (176, 120, 70))
    m = mix(base, c.m, 0.4)
    v = c.h % 4
    if v == 0:
        s.poly([(6, 17), (10, 10), (20, 8), (26, 13), (24, 20), (14, 23)], m)
        for k in range(3):
            s.line([(11 + k * 4, 11), (9 + k * 4, 20)], shade(m, -2))
    elif v == 1:
        s.ell(7, 9, 24, 23, m); s.ell(10, 11, 15, 14, shade(m, 1)); s.line([(12, 18), (20, 19)], shade(m, -1))
    elif v == 2:
        s.poly([(8, 22), (10, 10), (15, 7), (22, 11), (24, 22)], m); s.line([(15, 8), (16, 22)], shade(m, -1))
        s.line([(11, 14), (22, 15)], shade(m, 1))
    else:
        for (x, y) in ((6, 13), (14, 9), (15, 17)):
            s.ell(x, y, x + 9, y + 7, m); s.px([(x + 2, y + 2), (x + 3, y + 1)], shade(m, 2))
    if method in ('charred', 'blackened', 'ember', 'fire', 'flame', 'torch'):
        e = s.lit((255, 150, 60)); s.px([(12, 14), (18, 12), (16, 18)], e)
    if method in ('honey', 'caramelized'):
        s.line([(10, 12), (16, 10), (21, 12)], (250, 220, 120)); s.px([(21, 13), (21, 14), (12, 13)], (250, 220, 120))
    if method == 'salt':
        s.px([(11, 11), (15, 9), (19, 12), (13, 15), (20, 16)], WHITE)
    garnish(s, c, 3, 21, herb_of(c)); garnish(s, c, 21, 21, herb_of(c))
    if c.g:
        s.px([(15, 14), (20, 17)], s.lit(c.g))
    steam(s, (14,), 1, 6)


def d_special(s, c):
    """Legendary / abstractly named dishes."""
    v = c.h % 3
    if c.has('paradox', 'balance', 'transcendence', 'fusion', 'triad', 'first_and_last', 'fire_ice'):
        a = s.lit(c.g or shade(c.m, 1)); cols = c.all
        b_c = cols[1][1] or cols[1][0] if len(cols) > 1 else (240, 240, 250)
        b = s.lit(b_c if b_c != (c.g or shade(c.m, 1)) else (240, 240, 250))
        top = bowl(s, c, a, mat=(60, 56, 76))
        s.poly([(16, top + 1), (26, top + 2), (25, top + 5), (16, top + 6), (13, top + 4)], b)
        s.px([(10, top + 3), (11, top + 3)], b); s.px([(21, top + 3), (22, top + 3)], a)
        if c.has('triad'):
            s.ell(13, top - 4, 19, top + 1, s.lit((150, 230, 120)))
        sparkle(s, c, a, 3, (4, 2, 14, 10)); sparkle(s, c, b, 3, (17, 2, 27, 10))
        return
    if c.has('brew', 'vision', 'venom', 'essence', 'fortifier', 'undying', 'base', 'bone_of_ages') or v == 0:
        gob = GOLD if c.h % 2 else (150, 156, 170)
        liq = s.lit(c.g or shade(c.m, 1))
        s.poly([(6, 7), (25, 7), (22, 17), (18, 19), (18, 24), (23, 28), (8, 28), (13, 24), (13, 19), (9, 17)], gob)
        s.ell(6, 4, 25, 10, shade(gob, 1)); s.ell(8, 5, 23, 9, liq)
        s.px([(15, 13), (16, 13), (15, 14), (16, 14)], c.m if sum(c.m) > 200 else (170, 40, 60))
        sparkle(s, c, liq, 4, (6, 0, 25, 3))
        if c.has('bone'):
            s.line([(18, 6), (24, 1)], BONE, 2)
    elif v == 1:    # silver cloche lifted over a glowing dish
        plate(s, c)
        m = mix((176, 110, 60), c.m, 0.45)
        s.ell(8, 15, 23, 25, m); s.px([(11, 18), (12, 17)], shade(m, 2))
        s.poly([(10, 12), (12, 5), (20, 3), (27, 7), (28, 14)], STEEL); s.ell(18, 0, 22, 4, GOLD)
        s.line([(14, 6), (13, 10)], WHITE)
        if c.g:
            s.px([(14, 21), (18, 19), (6, 13), (4, 16)], s.lit(c.g))
        garnish(s, c, 3, 22)
    else:           # tiered serving stand
        st = GOLD if c.h % 2 else STEEL
        s.rect(15, 8, 16, 28, st); s.ell(3, 19, 28, 25, st); s.ell(8, 9, 23, 14, st); s.rect(11, 27, 20, 29, st)
        m, a = mix((190, 120, 70), c.m, 0.5), mix((226, 190, 130), c.a, 0.5)
        for k, x in enumerate((5, 10, 18, 23)):
            s.ell(x, 15, x + 4, 20, m if k % 2 else a)
        s.ell(10, 5, 14, 10, a); s.ell(17, 5, 21, 10, m); s.ell(14, 1, 18, 6, s.lit(c.g) if c.g else (190, 40, 60))


# ------------------------------------------------------------------ dispatch
DISH = [
    (('skewer', 'kebab'), d_skewer), (('pie', 'tourte', 'bake'), d_pie),
    (('dumplings',), d_dumplings), (('risotto',), d_risotto), (('roulade',), d_roulade), (('terrine',), d_terrine),
    (('souffle',), d_souffle), (('pudding', 'jelly'), d_jelly), (('crisps', 'cracklings'), d_crisps),
    (('hash',), d_hash), (('platter', 'canape', 'turf', 'dish'), d_platter),
    (('curry',), d_curry), (('salad',), d_salad), (('loaf', 'bread'), d_loaf),
    (('tea', 'tisane'), d_cup), (('tartare',), d_tartare),
    (('steak', 'medallions', 'medallion', 'cutlets'), d_steak),
    (('elixir', 'tincture', 'brew', 'ferment', 'extract'), d_elixir), (('brined',), d_jar),
    (('reduction', 'glaze'), d_sauce),
    (('hotpot', 'pot', 'feu', 'casserole', 'pottage', 'potage', 'provencal', 'hasenpfeffer', 'perpignan'), d_pot),
    (('stew', 'goulash', 'ragout', 'fricassee', 'braise', 'braisage', 'royale'), d_stew),
    (('soup', 'broth', 'bisque', 'chowder', 'consomme', 'bouillabaisse'), d_soup),
    (('feast', 'banquet', 'conquest', 'supremacy', 'culmination'), d_feast),
    (('roast', 'haunch'), d_roast),
]
DISH_TOK = {k: fn for kws, fn in DISH for k in kws}


def dish_fn(core_id):
    if '_infused_' in core_id:
        return d_jar
    toks = core_id.split('_')
    for tk in reversed(toks):
        if tk in DISH_TOK:
            return DISH_TOK[tk]
    return d_with if '_with_' in core_id else d_special


PART = [
    (('egg',), p_egg), (('skull', 'knuckle', 'finger'), p_bone),
    (('pelt', 'fur', 'skin'), p_pelt),
    (('gland', 'sac', 'organ', '_gut', 'brain_lobe'), p_gland),
    (('heartstone', 'gem', 'pearl'), p_crystal), (('heart', ), p_heart),
    (('eye',), p_eye),
    (('fang', 'tooth', 'tusk'), p_fang), (('claw', 'talon', 'hook', 'mantis_foreleg'), p_claw),
    (('mane', 'hair'), p_skein),
    (('horn_fragment', 'antler', 'wild_hunt_horn', '_horn'), p_horn),
    (('stinger', 'barb', 'spine', 'thorn', 'quill'), p_spike),
    (('feather',), p_feather), (('membrane', 'wing'), p_wing), (('tentacle',), p_tentacle),
    (('scales',), p_scale), (('shell', 'carapace', 'chitin', 'beak', 'mantis_foreleg'), p_shell),
    (('mane', 'hair', 'silk', 'strand', 'filament', 'thread'), p_skein),
    (('ember', '_ash'), p_ember),
    (('dust', 'salt', 'spice', 'pollen', 'mulch', 'residue'), p_dust),
    (('cloudstuff', 'essence', 'voice', 'glamour', 'shimmer', 'soul_fragment'), p_wisp),
    (('mushroom', 'fungus', 'fungi', 'spores', 'spore', ), p_mushroom),
    (('mold', 'moss'), p_blob),
    (('blood', 'venom', 'ichor', 'bile', 'saliva', 'oil', 'extract', 'ink', 'sap', 'perfume', 'musk', 'poison', 'brine',
      'resin', 'vial', 'reagent', 'fluid'), p_liquid),
    (('mucus', 'slime', 'ooze', 'jelly'), p_blob),
    (('bone',), p_bone),
    (('clay',), p_clay),
    (('core', 'crystal', 'shard', 'stone', 'fragment'), p_crystal),
    (('meat', 'flesh', 'beef', 'legs', '_leg', '_ear'), p_meat),
    (('herb', 'sprig', 'thyme', 'root', 'clover', 'celery', 'carrot', 'leaf', 'pepper', 'twig', 'wood', 'totem'), p_herb),
]
WEAPONS = ('claymore', 'flamberge', 'estoc', 'falchion', 'dao', 'kopis', 'kukri', 'sica', 'gladius', 'cinquedea', 'pugio',
           'mameluke_saber', 'francisca', 'naginata', 'partisan', 'coat_of_plates', 'cloth_wraps', 'corpse')
MISC_FIRST = ('spore_cloud_vial', 'samael_death_vial')


def _draw(rec):
    c = Ctx(rec)
    s = new()
    i = c.id
    if i.startswith('recipe_'):
        dish_fn(c.core)(s, c); return s
    if p_food(s, c):
        return s
    if i in WEAPONS:
        p_misc(s, c); return s
    if i in MISC_FIRST:
        p_liquid(s, c); return s
    if i == 'crone_voice' or i == 'changeling_glamour' or i == 'abyssal_shimmer':
        p_wisp(s, c); return s
    if i == 'mimic_gold' or 'chain_link' in i or 'phylactery' in i or 'trumpet' in i or 'mask' in i or 'tablet' in i \
            or i in ('executioners_iron', 'shadow_quiver', 'clockwork_gear', 'necromantic_focus', 'philosophers_shard',
                     'false_holy_relic', 'shaman_totem', 'inquisitor_seal', 'patriarch_signet'):
        if i == 'shaman_totem':
            p_herb(s, c); return s
        if p_misc(s, c):
            return s
    for kws, fn in PART:
        if any(k in i for k in kws):
            fn(s, c); return s
    if p_misc(s, c):
        return s
    # unknown: a wrapped parcel in the thing's colour
    s.poly([(5, 12), (16, 7), (27, 12), (27, 24), (16, 29), (5, 24)], c.m); s.poly([(5, 12), (16, 7), (27, 12), (16, 17)], shade(c.m, 1))
    s.line([(16, 17), (16, 29)], shade(c.m, -1)); s.line([(10, 9), (22, 14)], (206, 184, 130))
    return s


# A recipe's id no longer names its dish (prime_ghoul_recipe), but its NAME
# does ("Smoked Ghoul Shoulder"): choose the dish from the name, and colour
# it from the creature its first ingredient came from.
NAME_DISH = {
    'shoulder': 'roast', 'haunch': 'roast', 'shank': 'roast', 'loin': 'roast', 'flank': 'roast',
    'belly': 'roast', 'roast': 'roast', 'grill': 'roast', 'leg': 'roast',
    'rib': 'steak', 'cheek': 'steak', 'meat': 'steak', 'tongue': 'steak', 'steak': 'steak',
    'liver': 'medallions', 'kidney': 'medallions', 'heart': 'medallions', 'medallions': 'medallions',
    'fat': 'crisps', 'sinew': 'skewer', 'marrow': 'platter', 'scrap': 'hash', 'grease': 'crisps',
    'pot': 'pot', 'pyre': 'pot', 'coldforge': 'pot', 'cauldron': 'pot',
    'broth': 'broth', 'stock': 'broth', 'soup': 'soup', 'chowder': 'chowder', 'bisque': 'bisque',
    'stew': 'stew', 'braise': 'braise', 'ragout': 'ragout',
    'reduction': 'reduction', 'glaze': 'glaze', 'ichor': 'elixir', 'sap': 'elixir',
    'terrine': 'terrine', 'cake': 'pie', 'crust': 'pie', 'pie': 'pie', 'confit': 'terrine',
    'tea': 'tea', 'moss': 'salad', 'mushroom': 'salad', 'kelp': 'salad', 'salad': 'salad',
    'shard': 'platter', 'iron': 'platter', 'ember': 'curry', 'filament': 'skewer',
    'feast': 'feast', 'banquet': 'feast', 'skewer': 'skewer', 'curry': 'curry', 'loaf': 'loaf',
    'dumplings': 'dumplings', 'jelly': 'jelly', 'pudding': 'pudding', 'hash': 'hash',
}


def _recipe_alias(rec):
    import re
    words = [w for w in re.split(r'[^a-z]+', str(rec.get('name', '')).lower()) if w]
    dish = next((NAME_DISH[w] for w in reversed(words) if w in NAME_DISH), None)
    if dish is None:
        dish = 'brined' if 'pickled' in words else 'platter'
    src = str((rec.get('ingredients') or [''])[0]).replace('_prime', '')
    return dict(rec, id=f"recipe_{src or 'house'}_{dish}")


def draw(rec):
    import prime
    img = prime.draw(rec)
    if img is not None:
        return img
    if rec.get('category') == 'recipe' and rec.get('new') and rec.get('name'):
        rec = _recipe_alias(rec)
    s = _draw(rec)
    px = s.img.load()
    for k in range(32):       # keep the frame clear for the outline
        for p in ((k, 0), (k, 31), (0, k), (31, k)):
            px[p] = (0, 0, 0, 0)
    return s.finish()


if __name__ == '__main__':
    recs = json.load(open(os.path.join(HERE, 'slice.json'), encoding='utf-8'))
    n = 0
    for r in recs:
        d = os.path.join(HERE, 'out', r['folder'])
        os.makedirs(d, exist_ok=True)
        draw(r).save(os.path.join(d, r['id'] + '.png'))
        n += 1
    print('wrote', n, 'of', len(recs))
