"""Point one sprite's review entry at a new candidate, and optionally install it.

    <ComfyUI python> tools/content/genart/set_pick.py <run> <id> <cand> [--from <png>] [--note "..."] [--install] [--dry]

    e.g. set_pick.py r01 player_ranger 4 --from _genart/heroes/corwin_2026_10_18/corwin_A_draw_toy_on_back.png
             --note "Brandon picked option A" --install

--from copies a finished 64 px sprite in as _genart/<run>/<id>/c<cand>_sprite.png. It refuses to
overwrite a different picture already there, so none of the run's own candidates is lost.
The pick in _genart/<run>/review.json becomes <cand>, and the note goes in front of the old note,
so the earlier pick stays on record. --install then runs install_rest.py --only <id>: it installs
that one sprite and keeps everything else in installed_rest.json (a full install_rest.py run
would drop the ids other installers added). Paths are relative to the project root.

It warns when the run has a touch_up.py that paints fixed pixels on this id's pick (r01's sets
Corwin's eyes on c2): those pixels would land in the wrong place on the new candidate.
"""
import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GEN = os.path.join(ROOT, '_genart')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('id')
    ap.add_argument('cand', type=int)
    ap.add_argument('--from', dest='src', default='')
    ap.add_argument('--note', default='')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    review = os.path.join(GEN, a.run, 'review.json')
    if not os.path.exists(review):
        raise SystemExit('no ' + review)
    rv = json.load(open(review, encoding='utf-8'))
    if a.id not in rv:
        raise SystemExit(f'{a.id} has no entry in {review}')
    dst = os.path.join(GEN, a.run, a.id, f'c{a.cand}_sprite.png')
    if a.src:
        src = a.src if os.path.isabs(a.src) else os.path.join(ROOT, a.src)
        if not os.path.exists(src):
            raise SystemExit('missing ' + src)
        if os.path.exists(dst) and not filecmp.cmp(src, dst, shallow=False):
            raise SystemExit(f'{dst} is already a different picture; choose another candidate number')
        print(('would copy ' if a.dry else 'copy ') + src + ' -> ' + dst)
        if not a.dry:
            shutil.copyfile(src, dst)
    elif not os.path.exists(dst):
        raise SystemExit('missing ' + dst + ' (give --from)')
    old = rv[a.id].get('pick')
    note = a.note or f'Pick moved from c{old} to c{a.cand}.'
    print(f'{a.run}/{a.id}: pick c{old} -> c{a.cand}')
    if not a.dry:
        rv[a.id]['pick'] = a.cand
        rv[a.id]['note'] = note + (' | Earlier: ' + rv[a.id]['note'] if rv[a.id].get('note') else '')
        with open(review, 'w', encoding='utf-8') as f:
            json.dump(rv, f, indent=1, ensure_ascii=False)
    # A run's hand touch-up script (r01's paints Corwin's and Fianna's eyes) stamps fixed pixels
    # on whatever the pick is; on a new candidate they land in the wrong place.
    touch = os.path.join(GEN, a.run, 'touch_up.py')
    if os.path.exists(touch) and a.id in open(touch, encoding='utf-8').read() and 'SET_FOR' not in open(touch, encoding='utf-8').read():
        print(f'WARNING: {touch} paints fixed pixels on the pick of {a.id}. Before running it again, make it '
              f'skip {a.id} unless the pick is the candidate those pixels were set for (c{old}).')
    if a.install:
        cmd =[sys.executable, os.path.join(HERE, 'install_rest.py'), '--only', a.id] + (['--dry'] if a.dry else [])
        subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
