"""Install the rare pets' sprites: the Mooble and the Bococho (2026-11-14).

    <ComfyUI python> tools/content/genart/domain_props.py draw tools/content/genart/briefs/rare_pets.json --n 3 --out _genart/rare_pets --seed 98100
    <ComfyUI python> tools/content/genart/rare_pets_art.py tiles paint ; ... tiles build ; ... dance ; ... sheet
    py tools/content/genart/install_rare_pets.py [--dry] [--run <folder>]

The briefs (briefs/rare_pets.json) are homages, never copies: the Mooble is our own
cream-furred cave creature with little dark bat wings and a glowing red bobble on a
short CURLED antenna (no pom-pom on a straight stalk), and the Bococho our own golden
riding bird with slate-grey scaled legs and a dark-tipped horn beak, painted as a real
beast. No Square Enix names, emblems or text appear anywhere. The picks below were
reviewed on <run>/REVIEW_*.png at 64 px and 4x; verdicts are in <run>/review.json.

Where each goes:
  monsters            assets/tiles/monsters (the pets' stages, the dance poses, the NPCs, Varro)
  items               assets/tiles/items (starnut, sunroot: replace the kitchen's placeholders)
  fixtures            assets/tiles/env/fixtures (stand layer, cut like a monster)
  race track tiles    assets/tiles/env (opaque 64 px tiles, made by rare_pets_art.py tiles)

The dance poses come from <run>/dance (cut again at one body scale by rare_pets_art.py
dance; the two leans are one painting tipped each way), the champion's riding sprite and the
young bird from <run>/final (rare_pets_art.py finals: the saddled grown bird in the champion's
marks; the young bird's pick with its tan turned dull yellow), the
track tiles from <run>/tiles/out; every other id is <run>/<id>/c<pick>_sprite.png.

The rider's seat (the middle of the saddle's dip, where a rider's hips sit) is SEAT below,
in the 64 px frame, for the code that draws the hero on top of a saddled bird.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GENART = os.path.join(ROOT, 'tools', 'content', 'genart')

# <run>/<id>/c<pick>_sprite.png. A pick of 4 or more is a candidate kept from a backup
# round (gilt_varro, npc_varro_bococho) or a klein edit of a picked painting (bococho_saddled).
PICKS = {
    # the Mooble (floors 31-45)
    'npc_mooble': 1, 'mooble': 2, 'mooble_dancer': 1, 'mooble_troupe_leader': 1,
    # the Bococho (floors 51-65)
    'npc_bococho_young': 3,             # installed retinted from <run>/final (BUILT)
    'bococho_chick': 2, 'bococho': 2, 'bococho_champion': 3,
    'bococho_saddled': 4,
    'npc_varro_bococho': 4, 'gilt_varro': 4,
    # forage finds and the camp
    'starnut': 1, 'sunroot': 3,
    'race_tether_post': 1, 'race_betting_board': 1, 'race_finish_banner': 3,
}

MONSTERS = ('npc_mooble', 'mooble', 'mooble_dancer', 'mooble_troupe_leader',
            'mooble_dance_left', 'mooble_dance_right', 'mooble_dance_up', 'mooble_dance_down',
            'npc_bococho_young', 'bococho_chick', 'bococho', 'bococho_champion',
            'bococho_saddled', 'bococho_champion_saddled', 'npc_varro_bococho', 'gilt_varro')
ITEMS = ('starnut', 'sunroot')
FIXTURES = ('race_tether_post', 'race_betting_board', 'race_finish_banner')
TILES = ('race_track_floor', 'race_track_rail')
DANCE = ('mooble_dance_left', 'mooble_dance_right', 'mooble_dance_up', 'mooble_dance_down')
# finished in code by rare_pets_art.py finals into <run>/final: the champion's riding sprite
# (the saddled grown bird in the champion's marks) and the young bird's tan turned dull yellow
BUILT = ('bococho_champion_saddled', 'npc_bococho_young')

# The rider's seat in each saddled bird's 64 px frame (x, y): the middle of the saddle's dip,
# where the hero's hips go. The bird faces left; the pommel is at x 26-30, the cantle at x 36-42.
# Drawn on top at about 0.6 scale (a 38 px hero) with his hips here, the hero's head clears the
# top of the tile and his legs hang over the flap (RARE_PETS_ART_SHEET.png shows it).
SEAT = {'bococho_saddled': (33, 23), 'bococho_champion_saddled': (33, 23)}


def dest(sid: str) -> str:
    if sid in ITEMS:
        return os.path.join(ROOT, 'assets', 'tiles', 'items')
    if sid in FIXTURES:
        return os.path.join(ROOT, 'assets', 'tiles', 'env', 'fixtures')
    if sid in TILES:
        return os.path.join(ROOT, 'assets', 'tiles', 'env')
    return os.path.join(ROOT, 'assets', 'tiles', 'monsters')


def source(run: str, sid: str) -> str:
    if sid in DANCE:
        return os.path.join(run, 'dance', sid + '.png')
    if sid in BUILT:
        return os.path.join(run, 'final', sid + '.png')
    if sid in TILES:
        return os.path.join(run, 'tiles', 'out', sid + '.png')
    return os.path.join(run, sid, f'c{PICKS[sid]}_sprite.png')


def _add_ids(path: str, ids, folder: str | None, indent) -> None:
    """Record installed ids in an installer registry (tests/test_art_pass.py reads them to
    know which pictures are the reviewed 64 px art): a sorted list stays sorted, a
    folder's list gains the ids at its end."""
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


def _run_dir() -> str:
    if '--run' in sys.argv:
        return sys.argv[sys.argv.index('--run') + 1]
    here = os.path.join(ROOT, '_genart', 'rare_pets')
    if os.path.isdir(here):
        return here
    # a worktree has no _genart of its own: the work files live in the main checkout
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ROOT))), '_genart', 'rare_pets')


def main():
    dry = '--dry' in sys.argv
    run = _run_dir()
    missing = []
    for sid in MONSTERS + ITEMS + FIXTURES + TILES:
        if sid not in DANCE + TILES + BUILT and not PICKS.get(sid):
            missing.append(sid)
            continue
        src = source(run, sid)
        dst = os.path.join(dest(sid), sid + '.png')
        if not os.path.exists(src):
            missing.append(sid)
            print('MISSING', src)
            continue
        print(('would copy' if dry else 'copy'), src, '->', os.path.relpath(dst, ROOT))
        if not dry:
            shutil.copyfile(src, dst)
    if missing:
        print('no picture for:', ', '.join(missing))
    if dry:
        return
    # Varro is a man of the world (a monster when struck, like Old Nickel): installed.json.
    # The pets' stages, the dance poses and the NPCs are drawn by code: installed_rest.json.
    # The forage finds are items; the track tiles are map tiles.
    _add_ids(os.path.join(GENART, 'installed.json'), ['gilt_varro'], None, 2)
    _add_ids(os.path.join(GENART, 'installed_rest.json'),
             [s for s in MONSTERS if s != 'gilt_varro'], 'monsters', 0)
    _add_ids(os.path.join(GENART, 'installed_items.json'), list(ITEMS), 'items', 2)
    _add_ids(os.path.join(GENART, 'installed_tiles.json'), list(TILES), 'env', 0)


if __name__ == '__main__':
    main()
