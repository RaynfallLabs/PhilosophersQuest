"""Install the dungeon tiles and map objects.

    <ComfyUI python> tools/content/genart/install_tiles.py [--to <game root>]

- The built tiles (_genart/tiles/out: floor and its variants, wall, rock, water,
  lava, ice) go to assets/tiles/env as they are.
- Each reviewed object (_genart/objects/review.json) is cut from its picked
  picture again at the size it needs, then:
    fixtures and traps  are set on a floor tile and saved to assets/tiles/env
                        (those tiles are opaque: the renderer draws nothing under them);
    chests and shrines  are saved with a clear background to assets/tiles/items.
- What was written is listed in tools/content/genart/installed_tiles.json, which the
  old code-art build and the size test read.
"""
import argparse, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import convert

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GEN = os.path.join(ROOT, '_genart')
T = 64
# object -> (size it is cut at, what it stands on, how far its foot sits above the tile's bottom edge)
ON_FLOOR = {'altar': (58, 'floor', 2), 'fountain': (58, 'floor', 3), 'grave': (56, 'floor', 3), 'throne': (60, 'floor', 1),
            'door': (64, 'dark', 0), 'stairs_down': (62, 'floor', 1), 'stairs_up': (62, 'floor', 1)}
TRAP = (60, 'floor', 2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--to', default=ROOT); a = ap.parse_args()
    env = os.path.join(a.to, 'assets', 'tiles', 'env'); items = os.path.join(a.to, 'assets', 'tiles', 'items')
    out = {'env': [], 'items': []}
    tiles = os.path.join(GEN, 'tiles', 'out')
    for f in sorted(os.listdir(tiles)):
        Image.open(os.path.join(tiles, f)).convert('RGBA').save(os.path.join(env, f)); out['env'].append(f[:-4])
    floor = Image.open(os.path.join(tiles, 'floor.png')).convert('RGBA')
    dark = Image.eval(floor.convert('RGB'), lambda v: int(v * 0.45)).convert('RGBA')
    briefs = {b['id']: b for b in json.load(open(os.path.join(HERE, 'briefs', 'objects.json'), encoding='utf-8'))}
    review = json.load(open(os.path.join(GEN, 'objects', 'review.json'), encoding='utf-8'))
    for oid, v in sorted(review.items()):
        if not v.get('pick'):
            continue
        pic = Image.open(os.path.join(GEN, 'objects', oid, f"c{v['pick']}_pixel.png"))
        key = briefs[oid].get('key', 'magenta')
        rule = ON_FLOOR.get(oid) or (TRAP if oid.startswith('trap_') else None)
        if rule:
            size, under, lift = rule
            spr, _ = convert.to_sprite(pic, key, tile=size)
            tile = (dark if under == 'dark' else floor).copy()
            tile.alpha_composite(spr, ((T - size) // 2, T - size - lift))
            tile.save(os.path.join(env, oid + '.png')); out['env'].append(oid)
        else:
            spr, _ = convert.to_sprite(pic, key, tile=T)
            spr.save(os.path.join(items, oid + '.png')); out['items'].append(oid)
    if os.path.abspath(a.to) == os.path.abspath(ROOT):
        json.dump(out, open(os.path.join(HERE, 'installed_tiles.json'), 'w', encoding='utf-8'), indent=0)
    print('env', len(out['env']), 'items', len(out['items']), '->', a.to)


if __name__ == '__main__':
    main()
