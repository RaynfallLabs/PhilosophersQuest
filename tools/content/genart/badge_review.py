"""Working sheets for reviewing achievement badge candidates, a few badges per sheet.

    <ComfyUI python> tools/content/genart/badge_review.py <run dir> <briefs json> [--ids a,b] [--per 4] [--n 3]

For every brief, a row: each candidate as the painting (what the model drew), then the
badge in its rarity ring in full colour (won), grey (locked) and at 64 px (a small gallery
cell), with its grey range. The rarity comes from data/achievements.json by the brief's
id (a composite's background brief, `<art>_bg`, takes its badge's rarity). Sheets are
written to <run dir>/CANDS_<k>.png and their paths printed.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
from badge_sheet import ringed
import convert

FRAME = {'common': 'bronze', 'rare': 'silver', 'epic': 'gold', 'legendary': 'violet'}


def rarities():
    data = json.load(open(os.path.join(ROOT, 'data', 'achievements.json'), encoding='utf-8'))
    return {a['art']: a['rarity'] for a in data['achievements']}


def art_of(bid):
    return bid[:-3] if bid.endswith('_bg') else bid


def sheet(run, briefs, n, path, rar, names):
    font = ImageFont.truetype('consola.ttf', 13); bold = ImageFont.truetype('consolab.ttf', 16)
    P, C, S = 176, 142, 78
    cw = P + 6 + 2 * (C + 4) + S + 18
    rowh = P + 26
    sh = Image.new('RGB', (10 + n * cw, 10 + len(briefs) * rowh), (22, 20, 26)); dr = ImageDraw.Draw(sh)
    mech = {}
    mp = os.path.join(run, 'mechanical.json')
    if os.path.exists(mp):
        mech = json.load(open(mp, encoding='utf-8'))
    for r, b in enumerate(briefs):
        y = 10 + r * rowh
        bid = b['id']
        rarity = rar.get(art_of(bid), 'rare')
        dr.text((10, y), f"{bid}  ({rarity})  {names.get(art_of(bid), '')}", fill=(255, 220, 140), font=bold)
        for c in range(1, n + 1):
            x = 10 + (c - 1) * cw
            p = os.path.join(run, bid, f'c{c}_pixel.png'); s = os.path.join(run, bid, f'c{c}_sprite.png')
            if not os.path.exists(s):
                continue
            if os.path.exists(p):
                sh.paste(Image.open(p).convert('RGB').resize((P, P), Image.LANCZOS), (x, y + 22))
            spr = Image.open(s)
            for j, (size, locked) in enumerate(((128, False), (128, True), (64, False))):
                cell = ringed(spr, size, FRAME[rarity], locked)
                xx = x + P + 6 + j * (C + 4)
                sh.paste(cell, (xx, y + 22 + (C - cell.size[1]) // 2), cell)
            f = mech.get(f'{bid}/c{c}', {})
            gr = f.get('grey_range')
            if gr is None:                                  # a composite: not in the pipeline's facts
                gr = convert.grey_range(spr.convert('RGBA'))
            dr.text((x + P + 6, y + 22 + C + 2), f"c{c}  grey {gr:.2f}", fill=(200, 200, 210), font=font)
    sh.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('briefs')
    ap.add_argument('--ids', default=''); ap.add_argument('--per', type=int, default=4); ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--tag', default='')
    ap.add_argument('--add', default='', help='more ids with no brief of their own (composites: badge_composite.py)')
    a = ap.parse_args()
    briefs = json.load(open(a.briefs, encoding='utf-8'))
    briefs += [{'id': i} for i in a.add.split(',') if i]
    if a.ids:
        want = a.ids.split(',')
        briefs = [b for b in briefs if b['id'] in want]
    data = json.load(open(os.path.join(ROOT, 'data', 'achievements.json'), encoding='utf-8'))
    names = {x['art']: x['name'] for x in data['achievements']}
    rar = rarities()
    for k in range(0, len(briefs), a.per):
        print(sheet(a.run, briefs[k:k + a.per], a.n, os.path.join(a.run, f'CANDS{a.tag}_{k // a.per + 1}.png'), rar, names))


if __name__ == '__main__':
    main()
