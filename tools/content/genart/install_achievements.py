"""Install the reviewed achievement badges.

    <ComfyUI python> tools/content/genart/install_achievements.py [--dry] [--force] [--only art,art]

Reads every _genart/badges/<group>/review.json. A badge's pick (`"pick": N`) is that group's
<art>/cN_sprite.png; it is written to assets/achievements/<art>.png as a 128 x 128 RGBA PNG.
Only ids that are an `art` in data/achievements.json are installed, so a composite's background
brief (`<art>_bg`) never is. When two groups pick the same art, the later group wins and is
reported.

tools/content/genart/installed_achievements.json lists every file this installer has written. A
PNG already in assets/achievements that is not on that list (art made some other way) is left
alone and reported, unless --force. --only installs just those arts and keeps the rest of the list.
At the end every art in data/achievements.json with no PNG is listed.
"""
import argparse, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RUN = os.path.join(ROOT, '_genart', 'badges')
DEST = os.path.join(ROOT, 'assets', 'achievements')
LISTED = os.path.join(HERE, 'installed_achievements.json')
SIZE = 128


def arts():
    data = json.load(open(os.path.join(ROOT, 'data', 'achievements.json'), encoding='utf-8'))
    return [a['art'] for a in data['achievements']]


def reviewed(run=RUN):
    """{art: (group, path of the picked 128 px badge)} over every group's review.json."""
    picks, clashes = {}, []
    for g in sorted(os.listdir(run)):
        rv = os.path.join(run, g, 'review.json')
        if not os.path.isfile(rv):
            continue
        for bid, v in json.load(open(rv, encoding='utf-8')).items():
            if not v.get('pick'):
                continue
            p = os.path.join(run, g, bid, f"c{v['pick']}_sprite.png")
            if not os.path.exists(p):
                print(f'  {g}/{bid}: picked c{v["pick"]} but {p} is missing')
                continue
            if bid in picks:
                clashes.append((bid, picks[bid][0], g))
            picks[bid] = (g, p)
    for bid, old, new in clashes:
        print(f'  {bid}: picked in {old} and {new}; {new} wins')
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true'); ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    want = arts()
    picks = reviewed()
    listed = set(json.load(open(LISTED, encoding='utf-8'))) if os.path.exists(LISTED) else set()
    only = set(a.only.split(',')) if a.only else None
    written, refused, bad = [], [], []
    os.makedirs(DEST, exist_ok=True)
    for art in want:
        if only is not None and art not in only:
            continue
        if art not in picks:
            continue
        dst = os.path.join(DEST, art + '.png')
        if os.path.exists(dst) and art not in listed and not a.force:
            refused.append(art)
            continue
        img = Image.open(picks[art][1]).convert('RGBA')
        if img.size != (SIZE, SIZE):
            bad.append(f'{art} is {img.size[0]}x{img.size[1]}')
            continue
        if not a.dry:
            img.save(dst)
        written.append(art)
    if not a.dry:
        json.dump(sorted(listed | set(written)), open(LISTED, 'w', encoding='utf-8'), indent=0)
    print(('would install' if a.dry else 'installed'), len(written), 'badges to', os.path.relpath(DEST, ROOT))
    if refused:
        print(f'  left alone (not installed by this tool; --force to overwrite): {", ".join(refused)}')
    for b in bad:
        print('  wrong size:', b)
    extra = sorted(set(picks) - set(want))
    if extra and only is None:
        print(f'  picks that are not an art in data/achievements.json (backgrounds, old ids): {len(extra)}')
    missing = [x for x in want if not os.path.exists(os.path.join(DEST, x + '.png'))]
    print(f'{len(want) - len(missing)} of {len(want)} badges have a PNG' + (': missing ' + ', '.join(missing) if missing else ''))


if __name__ == '__main__':
    main()
