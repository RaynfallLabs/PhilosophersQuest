"""Install the painted sprites for the four Secret Build uniques (2026-11-17):
the Shield of Achilles, the Shield of Ilion, Boudicca's Spear and Joan of
Arc's Standard (tools/content/hero_uniques_2026_11_17.py).

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/hero_uniques_2026_11_17.json --n 4 --out _genart/items/hero_uniques_2026_11_17 --seed 11700
    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/hero_uniques_2026_11_17.json --only joans_standard,boudicca_spear --n 4 --out _genart/items/hero_uniques_2026_11_17 --seed 11900
    py tools/content/genart/install_hero_uniques.py [--dry] [--genart _genart] [--pick id=N ...]

Painted by the pipeline only (no art drawn in code). Round one of the standard
drew the Lord as a standing figure beside the pole and the spear's ash as
white; both were redrawn (the brief now paints the world flat on the banner and
the shaft honey-brown) and round one kept as <id>_r1. Brandon picks the art
himself: candidate 1 of each is installed so the game shows something, and
every candidate stays in _genart/items/hero_uniques_2026_11_17/<id>/c<N>_sprite.png
(the sheet is REVIEW_hero_uniques_2026_11_17.png beside them). Run again with
--pick shield_of_achilles=3 to install another.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GENART = os.path.join(ROOT, 'tools', 'content', 'genart')
RUN = os.path.join('items', 'hero_uniques_2026_11_17')

PICKS = {
    'shield_of_achilles': 1,
    'shield_of_ilion': 1,
    'boudicca_spear': 1,
    'joans_standard': 1,
}


def _write_json(path, obj, indent):
    txt = json.dumps(obj, indent=indent, ensure_ascii=False).replace('\n', '\r\n') + '\r\n'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def install(genart, picks=None, dry=False):
    picks = dict(PICKS, **(picks or {}))
    done = []
    for sid, pick in picks.items():
        src = os.path.join(genart, RUN, sid, f'c{pick}_sprite.png')
        dst = os.path.join(ROOT, 'assets', 'tiles', 'items', sid + '.png')
        if not os.path.exists(src):
            print('missing', src)
            continue
        if not dry:
            shutil.copyfile(src, dst)
        done.append(sid)
    if dry:
        print('would install', done)
        return done
    it_p = os.path.join(GENART, 'installed_items.json')
    with open(it_p, encoding='utf-8') as f:
        it = json.load(f)
    it['items'] = sorted(set(it.get('items', ())) | set(done))
    _write_json(it_p, it, 2)
    print('installed', len(done))
    return done


if __name__ == '__main__':
    args = sys.argv[1:]
    genart = os.path.join(ROOT, '_genart')
    if '--genart' in args:
        genart = args[args.index('--genart') + 1]
    chosen = {}
    if '--pick' in args:
        for tok in args[args.index('--pick') + 1:]:
            if tok.startswith('--'):
                break
            k, _, v = tok.partition('=')
            chosen[k] = int(v)
    install(genart, chosen, dry='--dry' in args)
