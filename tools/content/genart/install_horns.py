"""Install the horns of legend's painted sprites (2026-11-16): the seventeen who
answer a horn, the three people of the paths, and the three horns.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/horns_h01.json --n 3 --out _genart/horns_h01 --seed 9100
    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/horns_h01.json --only robin_hoods_horn,arthurs_bugle,gjallarhorn,npc_heimdall --n 4 --out _genart/horns_h01_r2 --seed 9300
    py tools/content/genart/install_horns.py [--dry] [--genart _genart]

Painted in the pipeline's style only (Brandon, 2026-11-16: no art drawn in code).
The picks below were reviewed on <run>/REVIEW_*.png at 64 px; verdicts are in
<run>/review.json. Each id is <run>/<id>/c<pick>_sprite.png, from the first run
(_genart/horns_h01) or, for the three horns and Heimdall, the second
(_genart/horns_h01_r2: the first drew brass instruments, cattle and a bull's
skull; the shape is now described plainly, "a natural horn with no valves").

Gjallarhorn and Heimdall were redrawn on 2026-11-16 (Brandon: "crescent-shaped
(a curved horn), not straight"): round 2 gave a gently curved cone and, in
Heimdall's hands, a straight trumpet. The horn is now told as plain geometry,
"bent round in a deep half circle", with no simile to draw (no moon, sickle or
animal): Gjallarhorn from _genart/horns_h01_r3, and Heimdall from
_genart/horns_h01_r5, holding it low across his white robe so the dark crescent
reads against it (round 3 held it up by his shoulder, a trumpet again; round 4
out at his side, a crescent on a stick). Before and after:
GJALLARHORN_REDRAW_2026_11_16.png in the project root.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/horns_h01.json --only gjallarhorn,npc_heimdall --n 4 --out _genart/horns_h01_r3 --seed 9500
    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/horns_h01.json --only npc_heimdall --n 4 --out _genart/horns_h01_r5 --seed 10100

Where each goes:
  the allies and the people   assets/tiles/monsters (recorded in installed.json, the
                              people in installed_rest.json)
  the horns                   assets/tiles/items (installed_items.json)
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GENART = os.path.join(ROOT, 'tools', 'content', 'genart')

R1, R2 = 'horns_h01', 'horns_h01_r2'
R3, R5 = 'horns_h01_r3', 'horns_h01_r5'          # the crescent redraw, 2026-11-16
PICKS = {
    # Robin Hood's band, and Robin Hood on his bridge
    'npc_robin_hood': (R1, 3), 'little_john': (R1, 3), 'will_scarlet': (R1, 2),
    'friar_tuck': (R1, 3), 'much_the_millers_son': (R1, 1), 'alan_a_dale': (R1, 2),
    'yeoman_archer': (R1, 2),
    # the sleepers under the hill
    'npc_sleeping_king': (R1, 2), 'king_arthur': (R1, 3), 'sir_lancelot': (R1, 1),
    'sir_gawain': (R1, 2), 'sir_percival': (R1, 2), 'sir_bedivere': (R1, 3), 'sir_kay': (R1, 1),
    # Heimdall and the einherjar
    'npc_heimdall': (R5, 4), 'einherjar': (R1, 1),
    # Charlemagne's host
    'charlemagne': (R1, 2), 'duke_naimes': (R1, 1), 'ogier_the_dane': (R1, 2),
    'frankish_knight': (R1, 2),
    # the horns
    'robin_hoods_horn': (R2, 3), 'arthurs_bugle': (R2, 1), 'gjallarhorn': (R3, 1),
}

ITEMS = ('robin_hoods_horn', 'arthurs_bugle', 'gjallarhorn')


def _write_json(path, obj, indent):
    txt = json.dumps(obj, indent=indent, ensure_ascii=False).replace('\n', '\r\n') + '\r\n'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def install(genart, dry=False):
    done = []
    for sid, (run, pick) in PICKS.items():
        src = os.path.join(genart, run, sid, f'c{pick}_sprite.png')
        folder = 'items' if sid in ITEMS else 'monsters'
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
    mons_p = os.path.join(GENART, 'installed.json')
    mons = set(json.load(open(mons_p, encoding='utf-8')))
    mons |= {s for s in done if s not in ITEMS and not s.startswith('npc_')}
    _write_json(mons_p, sorted(mons), 2)
    rest_p = os.path.join(GENART, 'installed_rest.json')
    rest = json.load(open(rest_p, encoding='utf-8'))
    rest['monsters'] = sorted(set(rest.get('monsters', ())) | {s for s in done if s.startswith('npc_')})
    _write_json(rest_p, rest, 0)
    it_p = os.path.join(GENART, 'installed_items.json')
    it = json.load(open(it_p, encoding='utf-8'))
    it['items'] = sorted(set(it.get('items', ())) | {s for s in done if s in ITEMS})
    _write_json(it_p, it, 2)
    print('installed', len(done))
    return done


if __name__ == '__main__':
    args = sys.argv[1:]
    genart = os.path.join(ROOT, '_genart')
    if '--genart' in args:
        genart = args[args.index('--genart') + 1]
    install(genart, dry='--dry' in args)
