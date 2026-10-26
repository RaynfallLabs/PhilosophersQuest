"""Achievement badges side by side the way the game shows them, for Brandon's approval.

    <ComfyUI python> tools/content/genart/badge_sheet.py _genart/badges_pilot/picks.json ACHIEVEMENT_PILOT_SHEET.png
    <ComfyUI python> tools/content/genart/badge_sheet.py --catalogue ACHIEVEMENT_SHEET_{:02d}.png

The second form draws every achievement in data/achievements.json from its installed PNG in
assets/achievements, grouped by category, about 32 to a sheet.

picks.json is a list, one entry per badge:
    {"name": "A Hundred Questions", "frame": "bronze", "looks": {"A emblem": "<128 px png>", "B vignette": "<png>"}}
Every look is shown three ways, each inside a plain round ring of the rarity's colour
(the game draws the real frame): 128 px in full colour (won), 128 px grey (locked),
and 64 px (a small gallery cell). The sheet carries the names; the art carries no text.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

FRAMES = {'bronze': (176, 116, 62), 'silver': (196, 198, 208), 'gold': (232, 192, 72), 'violet': (156, 96, 216)}
DISC = (34, 30, 40)                   # the dark inside of the medallion an emblem sits on
BACK = (22, 20, 26)
RING = 7                              # ring width at 128 px


def grey(art):
    """The locked look: luminosity grey, the alpha kept."""
    a = art.convert('RGBA')
    g = a.convert('L').convert('RGB').convert('RGBA')
    g.putalpha(a.getchannel('A'))
    return g


def ringed(art, size=128, frame='bronze', locked=False):
    """The badge at `size`, on the medallion's dark disc, inside a ring of the frame's colour."""
    art = art.convert('RGBA')
    if art.size != (size, size):
        art = art.resize((size, size), Image.LANCZOS)
    if locked:
        art = grey(art)
    ring = max(3, round(RING * size / 128))
    side = size + 2 * ring
    ss = 4                                             # draw the circles large, then shrink, for a smooth ring
    big = Image.new('RGBA', (side * ss, side * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    d.ellipse((0, 0, side * ss - 1, side * ss - 1), fill=FRAMES[frame] + (255,))
    d.ellipse((ring * ss, ring * ss, (side - ring) * ss - 1, (side - ring) * ss - 1), fill=DISC + (255,))
    out = big.resize((side, side), Image.LANCZOS)
    out.alpha_composite(art, (ring, ring))
    # a thin dark line where the ring meets the art, as the game's frame will have
    edge = Image.new('RGBA', (side * ss, side * ss), (0, 0, 0, 0)); e = ImageDraw.Draw(edge)
    e.ellipse((ring * ss, ring * ss, (side - ring) * ss - 1, (side - ring) * ss - 1), outline=(0, 0, 0, 200), width=ss)
    out.alpha_composite(edge.resize((side, side), Image.LANCZOS))
    return out


def sheet(picks, path):
    font = ImageFont.truetype('consola.ttf', 13); bold = ImageFont.truetype('consolab.ttf', 18)
    looks = list(picks[0]['looks'])
    c128, c64, gap, pad = 128 + 2 * RING, 64 + 2 * max(3, round(RING / 2)), 14, 24
    group = 2 * c128 + c64 + 2 * gap
    W = pad * 2 + len(looks) * group + (len(looks) - 1) * 48
    rowh = c128 + 46
    H = 70 + len(picks) * rowh + 10
    sh = Image.new('RGB', (W, H), BACK); dr = ImageDraw.Draw(sh)
    for k, look in enumerate(looks):
        x = pad + k * (group + 48)
        dr.text((x, 12), 'LOOK ' + look, fill=(255, 220, 140), font=bold)
        for j, lab in enumerate(('won, 128 px', 'locked, 128 px', '64 px')):
            dr.text((x + j * (c128 + gap), 40), lab, fill=(170, 165, 180), font=font)
    for r, p in enumerate(picks):
        y = 62 + r * rowh
        for k, look in enumerate(looks):
            x = pad + k * (group + 48)
            art = Image.open(p['looks'][look])
            for j, (size, locked) in enumerate(((128, False), (128, True), (64, False))):
                cell = ringed(art, size, p['frame'], locked)
                cy = y + (c128 - cell.size[1]) // 2
                sh.paste(cell, (x + j * (c128 + gap), cy), cell)
            name = p['name']
            tw = dr.textlength(name, font=bold)
            dr.text((x + (group - tw) / 2, y + c128 + 8), name, fill=(236, 226, 200), font=bold)
    sh.save(path)
    return path


RARITY_FRAME = {'common': 'bronze', 'rare': 'silver', 'epic': 'gold', 'legendary': 'violet'}


def catalogue(root, out_pattern, per_sheet=32, cols=4, art_dir=None):
    """Approval sheets for every achievement, grouped by category in the data's order:
    each badge as won (128 px, its rarity ring), locked (grey) and at 64 px, its name under it.
    A category is never split unless it alone is longer than a sheet. Returns the paths."""
    data = json.load(open(os.path.join(root, 'data', 'achievements.json'), encoding='utf-8'))
    art_dir = art_dir or os.path.join(root, 'assets', 'achievements')
    cats = [(c['id'], c['name']) for c in data['categories']]
    by_cat = {cid: [a for a in data['achievements'] if a['category'] == cid] for cid, _ in cats}
    # pack whole categories onto sheets; a long one is cut into sheet-sized pieces
    sheets, cur = [], []
    for cid, cname in cats:
        items = by_cat[cid]
        chunks = [items[i:i + per_sheet] for i in range(0, len(items), per_sheet)] or [[]]
        for k, chunk in enumerate(chunks):
            label = cname + (f' ({k + 1}/{len(chunks)})' if len(chunks) > 1 else '')
            need = (len(chunk) + cols - 1) // cols * cols
            used = sum((len(ch) + cols - 1) // cols * cols for _, ch in cur)
            if cur and used + need > per_sheet:
                sheets.append(cur); cur = []
            cur.append((label, chunk))
    if cur:
        sheets.append(cur)
    font = ImageFont.truetype('consola.ttf', 13); bold = ImageFont.truetype('consolab.ttf', 15)
    head = ImageFont.truetype('consolab.ttf', 22)
    c128, c64, gap = 128 + 2 * RING, 64 + 2 * max(3, round(RING / 2)), 8
    cellw, cellh = 2 * c128 + c64 + 2 * gap + 28, c128 + 40
    W = 24 + cols * cellw
    paths = []
    for s, groups in enumerate(sheets, 1):
        rows = sum((len(ch) + cols - 1) // cols for _, ch in groups)
        H = 60 + len(groups) * 40 + rows * cellh + 20
        sh = Image.new('RGB', (W, H), BACK); dr = ImageDraw.Draw(sh)
        dr.text((24, 14), f'ACHIEVEMENT BADGES  sheet {s}/{len(sheets)}    each: won 128 px | locked (grey) | 64 px',
                fill=(170, 165, 180), font=bold)
        y = 50
        for label, chunk in groups:
            dr.text((24, y + 8), label.upper(), fill=(255, 220, 140), font=head); y += 40
            for i, a in enumerate(chunk):
                x = 24 + (i % cols) * cellw
                yy = y + (i // cols) * cellh
                p = os.path.join(art_dir, a['art'] + '.png')
                frame = RARITY_FRAME[a['rarity']]
                if os.path.exists(p):
                    art = Image.open(p)
                    for j, (size, locked) in enumerate(((128, False), (128, True), (64, False))):
                        cell = ringed(art, size, frame, locked)
                        sh.paste(cell, (x + j * (c128 + gap), yy + (c128 - cell.size[1]) // 2), cell)
                else:
                    dr.text((x + 20, yy + 60), 'NO PICTURE: ' + a['art'], fill=(240, 120, 120), font=bold)
                name = f"{a['name']}  ({a['rarity']})"
                tw = dr.textlength(name, font=font)
                dr.text((x + (2 * c128 + c64 + 2 * gap - tw) / 2, yy + c128 + 6), name, fill=(236, 226, 200), font=font)
            y += (len(chunk) + cols - 1) // cols * cellh
        path = out_pattern.format(s)
        sh.save(path); paths.append(path)
    return paths


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--catalogue':
    # <ComfyUI python> tools/content/genart/badge_sheet.py --catalogue ACHIEVEMENT_SHEET_{:02d}.png
    here = os.path.dirname(os.path.abspath(__file__))
    for p in catalogue(os.path.dirname(os.path.dirname(os.path.dirname(here))), sys.argv[2]):
        print(p)
elif __name__ == '__main__':
    picks = json.load(open(sys.argv[1], encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    for p in picks:
        p['looks'] = {k: v if os.path.isabs(v) else os.path.join(base, v) for k, v in p['looks'].items()}
    print(sheet(picks, sys.argv[2]))
