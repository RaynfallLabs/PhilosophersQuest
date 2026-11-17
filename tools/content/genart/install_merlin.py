"""Install the painted sprites for Merlin's staff and its path (2026-11-16): the
Staff of Emrys (the item Merlin starts with and other heroes earn at his
stone) and the great stone itself, the person the hero meets on that path.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/merlin_staff_s01.json --only staff_of_emrys --n 4 --out _genart/items/merlin_staff_s01 --seed 9700
    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/merlin_staff_s01.json --only npc_merlins_stone --n 4 --out _genart/merlin_stone_s01 --seed 10300
    py tools/content/genart/install_merlin.py [--dry] [--genart _genart]

Painted by the pipeline only (no art drawn in code). The picks were reviewed on
<run>/REVIEW_*.png at 64 px; verdicts are in <run>/review.json:
  staff_of_emrys     the knotted hawthorn staff, its loop gripping a grey stone,
                     a flowering vine on its upper half (it matches the
                     vine-wrapped staff Merlin's own sprite holds)
  npc_merlins_stone  the great grey stone with the hawthorn beside it and the
                     staff caught in its branches (the only candidate whose
                     staff and stone both show)

Where each goes: the staff to assets/tiles/items (installed_items.json), the stone
to assets/tiles/monsters (installed_rest.json). The badge, Not by Strength, is
installed with the other badges (install_achievements.py).
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GENART = os.path.join(ROOT, 'tools', 'content', 'genart')

PICKS = {
    'staff_of_emrys': (os.path.join('items', 'merlin_staff_s01'), 1, 'items'),
    'npc_merlins_stone': ('merlin_stone_s01', 1, 'monsters'),
}


def _write_json(path, obj, indent):
    txt = json.dumps(obj, indent=indent, ensure_ascii=False).replace('\n', '\r\n') + '\r\n'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def install(genart, dry=False):
    done = []
    for sid, (run, pick, folder) in PICKS.items():
        src = os.path.join(genart, run, sid, f'c{pick}_sprite.png')
        dst = os.path.join(ROOT, 'assets', 'tiles', folder, sid + '.png')
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
    it = json.load(open(it_p, encoding='utf-8'))
    it['items'] = sorted(set(it.get('items', ())) | {s for s in done if PICKS[s][2] == 'items'})
    _write_json(it_p, it, 2)
    rest_p = os.path.join(GENART, 'installed_rest.json')
    rest = json.load(open(rest_p, encoding='utf-8'))
    rest['monsters'] = sorted(set(rest.get('monsters', ())) | {s for s in done if PICKS[s][2] == 'monsters'})
    _write_json(rest_p, rest, 0)
    print('installed', len(done))
    return done


if __name__ == '__main__':
    args = sys.argv[1:]
    genart = os.path.join(ROOT, '_genart')
    if '--genart' in args:
        genart = args[args.index('--genart') + 1]
    install(genart, dry='--dry' in args)
