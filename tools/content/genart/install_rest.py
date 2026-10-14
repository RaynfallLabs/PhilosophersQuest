"""Install the last reviewed sprites: heroes, NPCs, pet companions and oddments.

    <ComfyUI python> tools/content/genart/install_rest.py [--dry]

Reads every _genart/rNN/review.json. Each id goes to the folder its sprite already lives in
(heroes in assets/tiles/env, the rest in assets/tiles/monsters); Dad's picture also becomes the monster/pet `dad`.
Brandon's painted heroes that are replaced are first copied to
_genart/heroes/originals (never overwritten there), and Robyn is never installed over.
What was written is listed in tools/content/genart/installed_rest.json.
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GEN = os.path.join(ROOT, '_genart')
TILES = os.path.join(ROOT, 'assets', 'tiles')
KEEP = {'player_robyn'}                     # Brandon's painting stays as it is
ALSO = {'player_dad': [('monsters', 'dad')]}


def picks():
    out = {}
    for run in sorted(os.listdir(GEN)):
        f = os.path.join(GEN, run, 'review.json')
        if re.fullmatch(r'r\d\d', run) and os.path.exists(f):
            for sid, v in json.load(open(f, encoding='utf-8')).items():
                if v.get('pick'):
                    out[sid] = os.path.join(GEN, run, sid, f"c{v['pick']}_sprite.png")
    return out


def main():
    dry = '--dry' in sys.argv
    out = {'env': [], 'monsters': []}
    for sid, src in sorted(picks().items()):
        if sid in KEEP:
            continue
        if not os.path.exists(src):
            raise SystemExit('missing ' + src)
        home = 'env' if os.path.exists(os.path.join(TILES, 'env', sid + '.png')) else 'monsters'   # player_ghost lives with the monsters
        for folder, name in [(home, sid)] + ALSO.get(sid, []):
            dst = os.path.join(TILES, folder, name + '.png')
            if not os.path.exists(dst):
                raise SystemExit(f'{folder}/{name} is not a sprite the game has')
            if not dry:
                orig = os.path.join(GEN, 'heroes', 'originals', name + '.png')
                if folder == 'env' and not os.path.exists(orig):
                    os.makedirs(os.path.dirname(orig), exist_ok=True)
                    shutil.copyfile(dst, orig)
                shutil.copyfile(src, dst)
            out[folder].append(name)
    if not dry:
        json.dump(out, open(os.path.join(HERE, 'installed_rest.json'), 'w', encoding='utf-8'), indent=0)
    print(('would install' if dry else 'installed'), len(out['env']), 'heroes,', len(out['monsters']), 'others')


if __name__ == '__main__':
    main()
