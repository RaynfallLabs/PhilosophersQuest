"""The Black Knight's limb stages, cut by hand from his picked painting.

    <ComfyUI python> tools/content/genart/black_knight_cuts.py <run dir>

The model will not leave a limb off (README: "a missing limb is not drawn; both
arms come back"; black_knight_stages.py tried it with the painting as a
reference: the arms and legs came back every time). So each stage is the full
knight's own pixel painting with limbs erased to the backdrop and a stump
painted on: a short black armour cap with a pale steel rim, a dark red cut face
and a few drops of blood. Everything else is the same pixels, so the armour,
colours and size match frame for frame.

Coordinates are in the 1024 px painting of candidate 1 (review.json pick).
Output: <run>/black_knight_<stage>/c1_pixel.png, then the stage sprites at the
full knight's scale (black_knight_stages.scaled_sprite) as c1_stage_sprite.png.
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import black_knight_stages as bks   # noqa: E402

KEY = (0, 255, 0)
STEEL = (34, 36, 46)
RIM = (150, 160, 178)
WOUND = (120, 10, 14)
BLOOD = (196, 22, 24)

# His left arm and shield (picture right).
LEFT_ARM = [(572, 255), (672, 255), (672, 298), (780, 298), (780, 860), (690, 860), (672, 800),
            (644, 770), (622, 730), (606, 690), (594, 650), (590, 640), (580, 600), (577, 410), (572, 410)]
# His sword arm and sword (picture left).
RIGHT_ARM = [(170, 0), (430, 0), (430, 252), (408, 262), (402, 352), (170, 352)]
# His right leg (picture left), below the hem.
RIGHT_LEG = [(296, 704), (446, 704), (446, 1010), (296, 1010)]
# Both legs, below the hem.
LEGS = [(290, 704), (720, 704), (720, 1010), (290, 1010)]


def _cap(d, box, face):
    """A stump: an armour cap (box) with its cut face on one side."""
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=STEEL, outline=RIM, width=5)
    if face == 'right':
        d.ellipse((x1 - 16, y0 + 14, x1 + 2, y1 - 14), fill=WOUND, outline=BLOOD, width=4)
    elif face == 'left':
        d.ellipse((x0 - 2, y0 + 14, x0 + 16, y1 - 14), fill=WOUND, outline=BLOOD, width=4)
    else:   # down
        d.ellipse((x0 + 14, y1 - 14, x1 - 14, y1 + 4), fill=WOUND, outline=BLOOD, width=4)


def _drip(d, x, y, length):
    d.rectangle((x, y, x + 15, y + length), fill=BLOOD)
    d.ellipse((x - 3, y + length - 8, x + 18, y + length + 10), fill=BLOOD)


def left_arm_gone(im):
    d = ImageDraw.Draw(im)
    d.polygon(LEFT_ARM, fill=KEY)
    _cap(d, (548, 262, 604, 336), 'right')
    _drip(d, 584, 326, 36)


def right_arm_gone(im):
    d = ImageDraw.Draw(im)
    d.polygon(RIGHT_ARM, fill=KEY)
    _cap(d, (390, 258, 446, 336), 'left')
    _drip(d, 398, 326, 30)


def right_leg_gone(im):
    d = ImageDraw.Draw(im)
    d.polygon(RIGHT_LEG, fill=KEY)
    _cap(d, (360, 672, 432, 726), 'down')
    _drip(d, 384, 726, 30)


def legs_gone(im):
    """Both legs off at the hip, and the long surcoat torn away to a short
    ragged hem, so what is left reads as a torso on the ground."""
    d = ImageDraw.Draw(im)
    hem = [(290, 1010), (290, 610)]
    x, up = 330, True
    while x < 700:
        hem.append((x, 610 if up else 640))
        x += 34
        up = not up
    hem += [(720, 625), (720, 1010)]
    d.polygon(hem, fill=KEY)
    _cap(d, (378, 612, 446, 662), 'down')
    _cap(d, (520, 612, 588, 662), 'down')
    _drip(d, 404, 660, 22)


STAGES = {
    'one_arm': [left_arm_gone],
    'no_arms': [left_arm_gone, right_arm_gone],
    'one_leg': [left_arm_gone, right_arm_gone, right_leg_gone],
    'torso': [left_arm_gone, right_arm_gone, legs_gone],
}


def main(run):
    pick = bks.full_pick(run)
    full = os.path.join(run, 'black_knight', f'c{pick}_pixel.png')
    base = Image.open(full).convert('RGB')
    # erase to the backdrop green as painted (read off the corners), so the
    # cut-away parts do not show as flat patches on the painting
    global KEY
    px = [base.getpixel(c) for c in ((4, 4), (1019, 4), (4, 1019), (1019, 1019))]
    KEY = tuple(sorted(v[i] for v in px)[1] for i in range(3))
    for st, steps in STAGES.items():
        im = base.copy()
        for f in steps:
            f(im)
        if st == 'one_leg':
            # hopping: leaning into the hop on his one leg
            im = im.rotate(-6, resample=Image.NEAREST, center=(590, 990), fillcolor=KEY)
        d = os.path.join(run, f'black_knight_{st}_hand')
        os.makedirs(d, exist_ok=True)
        im.save(os.path.join(d, 'c1_pixel.png'))
    bks.cut_dirs(run, [f'black_knight_{st}_hand' for st in STAGES])


if __name__ == '__main__':
    main(sys.argv[1])
