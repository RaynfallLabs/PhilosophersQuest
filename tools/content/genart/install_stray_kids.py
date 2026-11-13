"""Install the Stray Kids easter egg's sprites (2026-11-13).

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/stray_kids.json --n 3 --out _genart/stray_kids --seed 97000
    py tools/content/genart/install_stray_kids.py [--dry]

The briefs never name the real people: each member is drawn as a figure
with his prop and his clothes (Bang Chan's mug and headphones, Lee Know's
ginger cat, Felix's black belt and high kick...), not as a likeness. The
picks below were reviewed on the sheets _genart/stray_kids/REVIEW_*.png
(4x zoom of the 64 px cut checked for every pick). Both Seungmins were
redrawn (seed 97500) because every first-round jersey grew a pro team's
monogram; the second round's jerseys are blank.

Monsters go to assets/tiles/monsters, the two fixtures (stand layer, cut
like a monster) to assets/tiles/env/fixtures, the photo to
assets/tiles/items.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RUN = os.path.join(ROOT, '_genart', 'stray_kids')

PICKS = {
    # the zombie band (data/monsters.json)
    'sk_zombie_bang_chan': 2, 'sk_zombie_lee_know': 1, 'sk_zombie_changbin': 1,
    'sk_zombie_hyunjin': 1, 'sk_zombie_han': 1, 'sk_zombie_felix': 2,
    'sk_zombie_seungmin': 3, 'sk_zombie_i_n': 1,
    # the band alive, called up by the photo (stray_kids.StarDancer)
    'sk_star_bang_chan': 1, 'sk_star_lee_know': 2, 'sk_star_changbin': 2,
    'sk_star_hyunjin': 1, 'sk_star_han': 3, 'sk_star_felix': 1,
    'sk_star_seungmin': 2, 'sk_star_i_n': 2,
    # the props
    'sk_idol': 2, 'sk_speaker': 1, 'autographed_stray_kids_photo': 1,
}

DEST = {
    'sk_idol': ('assets', 'tiles', 'env', 'fixtures'),
    'sk_speaker': ('assets', 'tiles', 'env', 'fixtures'),
    'autographed_stray_kids_photo': ('assets', 'tiles', 'items'),
}


GENART = os.path.join(ROOT, 'tools', 'content', 'genart')


def _add_ids(path: str, ids, folder: str | None, indent: int) -> None:
    """Record installed ids in an installer registry (tests/test_art_pass.py
    reads them to know which pictures are the reviewed 64 px art): a sorted
    list stays sorted, a folder's list gains the ids at its end."""
    import json
    with open(path, encoding='utf-8') as f:
        doc = json.load(f)
    lst = doc if folder is None else doc.setdefault(folder, [])
    new = [i for i in ids if i not in lst]
    if not new:
        return
    if lst == sorted(lst):
        lst[:] = sorted(lst + new)
    else:
        lst.extend(new)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(doc, indent=indent, ensure_ascii=False) + '\n')


def main():
    dry = '--dry' in sys.argv
    for sid, pick in PICKS.items():
        src = os.path.join(RUN, sid, f'c{pick}_sprite.png')
        dst_dir = os.path.join(ROOT, *DEST.get(sid, ('assets', 'tiles', 'monsters')))
        dst = os.path.join(dst_dir, sid + '.png')
        if not os.path.exists(src):
            print('MISSING', src)
            continue
        print(('would copy' if dry else 'copy'), os.path.relpath(src, ROOT), '->', os.path.relpath(dst, ROOT))
        if not dry:
            shutil.copyfile(src, dst)
    if dry:
        return
    # The zombies are monsters (installed.json); the stars are drawn by code
    # (installed_rest.json, like the Black Knight's stages); the photo is an
    # item (installed_items.json).
    _add_ids(os.path.join(GENART, 'installed.json'),
             [s for s in PICKS if s.startswith('sk_zombie_')], None, 2)
    _add_ids(os.path.join(GENART, 'installed_rest.json'),
             [s for s in PICKS if s.startswith('sk_star_')], 'monsters', 0)
    _add_ids(os.path.join(GENART, 'installed_items.json'),
             ['autographed_stray_kids_photo'], 'items', 2)


if __name__ == '__main__':
    main()
