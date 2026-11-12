"""Install the Dungeon Alive domain art: theme tiles and fixtures.

    <ComfyUI python or game python> tools/content/genart/install_domains.py [--dry] [--only good] [--to <game root>]

- _genart/domains/install/themes/<theme>/*.png -> assets/tiles/env/themes/<theme>/
- _genart/domains/install/fixtures/*.png       -> assets/tiles/env/fixtures/

`--dry` lists what would be copied (and what each copy would replace) and writes nothing.
`--only good` skips pieces the manifest marks "weak". Every theme tile falls back to the
base tile in the engine, so a missing piece never breaks a floor.
What was written is listed in tools/content/genart/installed_domains.json.
"""
import argparse, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, '_genart', 'domains', 'install')


def plan(to):
    status = {}
    mf = os.path.join(SRC, 'manifest.json')
    if os.path.exists(mf):
        for m in json.load(open(mf, encoding='utf-8')):
            status[m['id']] = m['status']
    env = os.path.join(to, 'assets', 'tiles', 'env')
    jobs = []
    tdir = os.path.join(SRC, 'themes')
    for theme in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        for f in sorted(os.listdir(os.path.join(tdir, theme))):
            if f.endswith('.png'):
                jobs.append((os.path.join(tdir, theme, f), os.path.join(env, 'themes', theme, f), status.get(f'{theme}/{f}', '?')))
    fdir = os.path.join(SRC, 'fixtures')
    for f in sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []:
        if f.endswith('.png'):
            jobs.append((os.path.join(fdir, f), os.path.join(env, 'fixtures', f), status.get(f[:-4], '?')))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only', choices=['good'], default=None)
    ap.add_argument('--to', default=ROOT)
    a = ap.parse_args()
    jobs = plan(a.to)
    done = []
    for src, dst, st in jobs:
        if a.only == 'good' and st != 'good':
            print(f'skip ({st})  {os.path.relpath(dst, a.to)}')
            continue
        what = 'replace' if os.path.exists(dst) else 'new'
        print(f'{what:7s} [{st}]  {os.path.relpath(dst, a.to)}')
        if not a.dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            done.append(os.path.relpath(dst, a.to).replace(os.sep, '/'))
    if not a.dry:
        if os.path.abspath(a.to) == os.path.abspath(ROOT):
            json.dump(done, open(os.path.join(HERE, 'installed_domains.json'), 'w', encoding='utf-8'), indent=0)
        print(len(done), 'files installed under', a.to)
    else:
        print(len(jobs), 'files would be installed (dry run, nothing written)')


if __name__ == '__main__':
    main()
