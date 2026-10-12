"""Install the reviewed sprite picks into the game.

    python tools/content/genart/install.py [--dry]

Reads every _genart/<run>/review.json, copies each monster's picked
c<N>_sprite.png to assets/tiles/monsters/<id>.png, and writes the list of what
was installed to tools/content/genart/installed.json. The old code-drawn art
build (tools/content/art/build.py) reads that list and leaves those files alone.
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GEN = os.path.join(ROOT, '_genart')
DST = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed.json')


def picks():
    out = {}
    for run in sorted(os.listdir(GEN)):
        f = os.path.join(GEN, run, 'review.json')
        if run in ('pilot',) or not os.path.exists(f):      # 'pilot' is the superseded 48px run
            continue
        for mid, v in json.load(open(f, encoding='utf-8')).items():
            if v.get('pick'):
                out[mid] = os.path.join(GEN, run, mid, f"c{v['pick']}_sprite.png")
    return out


def main():
    dry = '--dry' in sys.argv
    mons = {k for k, v in json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8')).items()
            if isinstance(v, dict)}
    p = picks()
    missing = sorted(m for m, src in p.items() if not os.path.exists(src))
    unknown = sorted(set(p) - mons)
    if missing or unknown:
        raise SystemExit(f'not installing: missing files {missing}; not in monsters.json {unknown}')
    if not dry:
        for mid, src in p.items():
            shutil.copyfile(src, os.path.join(DST, mid + '.png'))
        json.dump(sorted(p), open(LIST, 'w', encoding='utf-8'), indent=0)
    print(('would install' if dry else 'installed'), len(p), 'sprites;', len(mons - set(p)), 'monsters have no pick')


if __name__ == '__main__':
    main()
