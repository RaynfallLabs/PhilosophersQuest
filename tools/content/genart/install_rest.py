"""Install the last reviewed sprites: heroes, NPCs, pet companions and oddments.

    <ComfyUI python> tools/content/genart/install_rest.py [--dry] [--only id,id]

Reads every _genart/rNN/review.json. Each id goes to the folder its sprite already lives in
(heroes in assets/tiles/env, the rest in assets/tiles/monsters); Dad's picture also becomes the monster/pet `dad`.
Brandon's painted heroes that are replaced are first copied to
_genart/heroes/originals (never overwritten there), and Robyn is never installed over.
What was written is listed in tools/content/genart/installed_rest.json.

A full run rewrites that list from the rNN runs found, so ids other installers added to it
(the family cats, Shep, traders, story NPCs) would drop out. To redo one or two sprites,
use --only: it installs just those ids and adds them to the list, keeping everything else.
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
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else set()
    found = picks()
    if only - set(found):
        raise SystemExit('no reviewed pick for: ' + ', '.join(sorted(only - set(found))))
    out = {'env': [], 'monsters': []}
    for sid, src in sorted(found.items()):
        if sid in KEEP or (only and sid not in only):
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
    print(('would install' if dry else 'installed'), len(out['env']), 'heroes,', len(out['monsters']), 'others')
    if not dry:
        listed = os.path.join(HERE, 'installed_rest.json')
        if only:
            old = json.load(open(listed, encoding='utf-8'))
            for k, ids in out.items():
                old[k] = sorted(set(old.get(k, [])) | set(ids))
            out = old
        json.dump(out, open(listed, 'w', encoding='utf-8'), indent=0)


if __name__ == '__main__':
    main()
