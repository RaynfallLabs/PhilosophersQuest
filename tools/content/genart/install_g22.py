"""Install the reviewed sprites of the MONSTERS AND MAGIC kinds (brief g22) and
their counter items (brief items_mm_counters), and draw the review sheet.

    <ComfyUI python> tools/content/genart/install_g22.py <work dir> [--sheet <png>]

<work dir> holds g22/review.json and items_mm/review.json (the reviewer's
picks: {"<id>": {"pick": N, "note": "..."}}). Each pick's cN_sprite.png is
copied to assets/tiles/monsters/<id>.png (items to assets/tiles/items/) and
its id is added to installed.json / installed_items.json, leaving every
earlier entry as it is (install.py rebuilds installed.json from every run in
_genart, which a worktree does not have). The sheet is a lineup of every
pick at 2x with its name, for Brandon.
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def _picks(path):
    with open(path, encoding='utf-8') as f:
        return {k: v for k, v in json.load(f).items() if v.get('pick')}


def main(argv):
    work = argv[0]
    sheet = argv[argv.index('--sheet') + 1] if '--sheet' in argv else None
    runs = (('g22', 'monsters', 'installed.json', None),
            ('items_mm', 'items', 'installed_items.json', 'items'))
    shown = []
    for run, folder, listing, key in runs:
        rv = os.path.join(work, run, 'review.json')
        if not os.path.exists(rv):
            continue
        picks = _picks(rv)
        lpath = os.path.join(HERE, listing)
        with open(lpath, encoding='utf-8') as f:
            listed = json.load(f)
        ids = listed[key] if key else listed
        for iid, v in picks.items():
            src = os.path.join(work, run, iid, f"c{v['pick']}_sprite.png")
            dst = os.path.join(ROOT, 'assets', 'tiles', folder, iid + '.png')
            shutil.copyfile(src, dst)
            if iid not in ids:
                ids.append(iid)
            shown.append((iid, src))
        ids.sort()
        with open(lpath, 'w', encoding='utf-8') as f:
            json.dump(listed, f, indent=2, ensure_ascii=True)
            f.write('\n')
        print(f'{run}: installed {len(picks)}')
    if sheet and shown:
        cell, per_row = 150, 8
        rows = (len(shown) + per_row - 1) // per_row
        im = Image.new('RGBA', (cell * per_row, cell * rows + 30), (40, 38, 36, 255))
        d = ImageDraw.Draw(im)
        d.text((8, 8), 'MONSTERS AND MAGIC (2026-11-19): the new kinds and their counter items', fill=(235, 225, 200))
        for i, (iid, src) in enumerate(shown):
            x, y = (i % per_row) * cell, (i // per_row) * cell + 30
            s = Image.open(src).convert('RGBA').resize((128, 128), Image.NEAREST)
            im.alpha_composite(s, (x + 11, y + 2))
            d.text((x + 6, y + 132), iid[:22], fill=(220, 210, 190))
        im.save(sheet)
        print('sheet', sheet)


if __name__ == '__main__':
    main(sys.argv[1:])
