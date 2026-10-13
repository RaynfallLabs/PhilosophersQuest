"""The art pass (2026-10-08): every sprite redrawn in one style, crisp
scaling, solid rock drawn apart from wall faces, and a picture for every
map object that used to show as a letter.

What the art LOOKS like needs eyes; these pin the plumbing.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

import renderer  # noqa: E402
from dungeon import FLOOR, SECRET_DOOR, WALL  # noqa: E402

TILES = os.path.join(ROOT, 'assets', 'tiles')
PAINTINGS = {'player_ranger.png', 'player_wizard_f.png', 'player_robyn.png'}     # Brandon's painted portraits: kept as they are
with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed.json'), encoding='utf-8') as _f:
    GENERATED = set(json.load(_f))     # monsters carrying a reviewed 64px picture
with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_tiles.json'), encoding='utf-8') as _f:
    GENERATED_TILES = json.load(_f)    # map tiles and objects carrying one, by folder
_items = os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json')
if os.path.exists(_items):             # items (and the trader) carrying one, by folder
    with open(_items, encoding='utf-8') as _f:
        for _folder, _ids in json.load(_f).items():
            GENERATED_TILES[_folder] = sorted(set(GENERATED_TILES.get(_folder, ())) | set(_ids))


def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')


def test_every_sprite_is_one_size():
    for folder in ('monsters', 'items', 'env'):
        for name in os.listdir(os.path.join(TILES, folder)):
            if name.endswith('.png') and name not in PAINTINGS:
                big = (folder == 'monsters' and name[:-4] in GENERATED) or name[:-4] in GENERATED_TILES.get(folder, ())
                want = (64, 64) if big else (32, 32)
                assert _png_size(os.path.join(TILES, folder, name)) == want, (folder, name)


def test_every_monster_has_its_generated_sprite():
    """The 529 monsters carry the reviewed 64px pictures (2026-10-12); pets, NPCs
    and the rest of that folder are still 32px code art."""
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = {k for k, v in json.load(f).items() if isinstance(v, dict)}
    assert mons <= GENERATED, sorted(mons - GENERATED)[:10]


def test_every_map_object_defined_in_code_has_a_picture():
    """Death, a fallen hero's ghost, gold, the trader and the mystery shrines
    showed as a letter or a coloured square."""
    import mystery_system
    for mid in ('death', 'player_ghost', 'abyssal_shimmer'):
        assert os.path.exists(os.path.join(TILES, 'monsters', f'{mid}.png')), mid
    want = ['gold_pile', 'merchant_npc']
    for key, m in mystery_system.MYSTERIES.items():
        want.append(f'mystery_altar_{key}')
        if m.get('key_item'):
            want.append(f'mystery_key_{key}')
    for iid in want:
        assert renderer._resolve_item_sprite_path(iid), iid
        assert os.path.exists(os.path.join(TILES, 'items', f'{iid}.png')), iid


def test_every_ingredient_has_a_picture_of_its_own():
    """All 537 prime cuts and trophies shared one meat icon."""
    with open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8') as f:
        ing = json.load(f)
    for iid, v in ing.items():
        if isinstance(v, dict):
            assert os.path.exists(os.path.join(TILES, 'items', f'{iid}.png')), iid


def test_every_trap_and_tile_has_a_picture():
    for name in renderer._TILE_SPRITE.values():
        assert os.path.exists(os.path.join(TILES, 'env', f'{name}.png')), name
    assert os.path.exists(os.path.join(TILES, 'env', 'rock.png'))


def test_pixel_art_is_enlarged_with_hard_edges_before_it_is_fitted():
    """Smooth-scaling 32px art straight to a 40px tile blurred every edge."""
    src = pygame.Surface((32, 32), pygame.SRCALPHA)
    src.fill((0, 0, 0, 0))
    pygame.draw.rect(src, (255, 0, 0, 255), (8, 8, 16, 16))
    out = renderer.fit_sprite(src, 40, 40)
    assert out.get_size() == (40, 40)
    assert out.get_at((20, 20)).r >= 250 and out.get_at((20, 20)).a >= 250     # solid inside
    assert out.get_at((2, 2)).a == 0                          # clear outside
    # the edge is one pixel wide at most: two pixels in from it, full colour
    assert out.get_at((12, 20)).a >= 250 and out.get_at((8, 20)).a == 0
    same = renderer.fit_sprite(src, 32, 32)
    assert same is src
    painting = pygame.Surface((1024, 1024), pygame.SRCALPHA)
    assert renderer.fit_sprite(painting, 40, 40).get_size() == (40, 40)


class _Dungeon:
    def __init__(self, rows):
        code = {'#': WALL, '.': FLOOR, 'S': SECRET_DOOR}
        self.tiles = [[code[c] for c in row] for row in rows]


def test_solid_rock_is_drawn_apart_from_a_wall_that_faces_something():
    d = _Dungeon(['#######',
                  '#######',
                  '#######',
                  '###...#',
                  '###...#',
                  '#######'])
    name = renderer._tile_sprite_name
    assert name(d, 0, 0, WALL) == 'rock'
    assert name(d, 1, 1, WALL) == 'rock'
    assert name(d, 2, 2, WALL) == 'wall'            # touches the room at a corner
    assert name(d, 3, 2, WALL) == 'wall'
    assert name(d, 3, 3, FLOOR).startswith('floor')    # one of the flagstone pictures


def test_the_floor_varies_by_place_and_stays_put():
    """One flagstone on every tile read as wallpaper. Each tile takes one of a
    few floor pictures, fixed by its position so it never changes underfoot."""
    d = _Dungeon(['.' * 30] * 30)
    name = renderer._tile_sprite_name
    seen = {name(d, x, y, FLOOR) for y in range(30) for x in range(30)}
    assert len(seen) >= 3 and all(n.startswith('floor') for n in seen)
    assert all(os.path.exists(os.path.join(TILES, 'env', n + '.png')) for n in seen)
    assert name(d, 7, 9, FLOOR) == name(d, 7, 9, FLOOR)


def test_the_rock_does_not_give_a_secret_door_away():
    """A secret door is drawn exactly as the wall it pretends to be, and the
    walls around it are drawn as they would be if it were plain wall."""
    plain = _Dungeon(['#####', '#####', '#####', '.....'])
    secret = _Dungeon(['#####', '##S##', '#####', '.....'])
    for y in range(4):
        for x in range(5):
            a = renderer._tile_sprite_name(plain, x, y, plain.tiles[y][x])
            b = renderer._tile_sprite_name(secret, x, y, secret.tiles[y][x])
            assert a == b, (x, y, a, b)


def test_the_art_tools_cover_every_sprite_file():
    """tools/content/art can redraw everything it ships: each file has an
    owner module."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'art'))
    import manifest
    recs = manifest.build()
    kinds = {r['kind'] for r in recs}
    for kind in kinds:
        assert os.path.exists(os.path.join(ROOT, 'tools', 'content', 'art', kind, f'{kind}.py')), kind
    listed = {(r['folder'], r['id']) for r in recs}
    for folder in ('monsters', 'items', 'env'):
        for name in os.listdir(os.path.join(TILES, folder)):
            if name.endswith('.png'):
                assert (folder, name[:-4]) in listed, (folder, name)
