"""Review sheets for the Dungeon Alive domain art (theme tiles and fixtures).

    <ComfyUI python> tools/content/genart/domain_sheets.py themes      working sheet per theme
    <ComfyUI python> tools/content/genart/domain_sheets.py props <set> working sheet of a prop set's candidates
    <ComfyUI python> tools/content/genart/domain_sheets.py final       DOMAIN_ART_SHEET_NN.png at the project root

A theme is laid out as a small map the way the renderer lays it (a wall that faces
nothing is rock; each floor tile takes one variant by its position, plain slabs most
often), with a few installed monsters and items on it, at 64 px and at 40 px.
A prop is shown on its theme's floor (a wall prop on its wall) at 64 px and at 40 px.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DOM = os.path.join(ROOT, '_genart', 'domains')
INSTALL = os.path.join(DOM, 'install')
ENV = os.path.join(ROOT, 'assets', 'tiles', 'env')
MON = os.path.join(ROOT, 'assets', 'tiles', 'monsters')
ITEMS = os.path.join(ROOT, 'assets', 'tiles', 'items')
T = 64
FONT = ImageFont.truetype('consola.ttf', 13)
BOLD = ImageFont.truetype('consolab.ttf', 17)
BG = (24, 22, 28)

# the renderer's floor mix (renderer._floor_variants): plain slabs five times, floor_2 four, floor_6 three
FLOOR_MIX = ['floor'] * 5 + ['floor_2'] * 4 + ['floor_3', 'floor_4', 'floor_5'] + ['floor_6'] * 3

MAP = ["############",
       "####.......#",
       "###........#",
       "#.....~~...#",
       "#..#..~~...#",
       "#..#.......#",
       "#..D...#####",
       "#......#####",
       "############"]

SPRITES = {   # theme -> [(x, y, kind, id)]
    'base': [(5, 2, 'm', 'goblin'), (9, 4, 'm', 'skeleton_warrior'), (2, 5, 'i', 'potion_of_extra_healing'),
             (5, 6, 'i', 'gold_pile'), (1, 3, 'm', 'kobold')],
    'temple': [(5, 2, 'm', 'medusa_gorgon'), (9, 4, 'm', 'naga_guardian'), (2, 5, 'i', 'potion_of_extra_healing'),
               (5, 6, 'i', 'gold_pile'), (1, 3, 'm', 'cockatrice')],
    'deep': [(5, 2, 'm', 'drake_fire'), (9, 4, 'm', 'kobold_sorcerer'), (2, 5, 'i', 'potion_of_extra_healing'),
             (5, 6, 'i', 'adamantine_longsword'), (1, 3, 'm', 'kobold')],
    'rime': [(5, 2, 'm', 'fenrir_wolf'), (9, 4, 'm', 'draugr'), (2, 5, 'i', 'potion_of_extra_healing'),
             (5, 6, 'i', 'gold_pile'), (1, 3, 'm', 'frost_skeleton')],
    'abyss': [(5, 2, 'm', 'abyssal_hound'), (9, 4, 'm', 'lemure'), (2, 5, 'i', 'potion_of_extra_healing'),
              (5, 6, 'i', 'gold_pile'), (1, 3, 'm', 'demonic_imp')],
}


def tile_dir(theme):
    return ENV if theme == 'base' else os.path.join(INSTALL, 'themes', theme)


def load_tile(theme, name):
    p = os.path.join(tile_dir(theme), name + '.png')
    if not os.path.exists(p):
        p = os.path.join(ENV, name + '.png')           # missing art falls back to the base tile, as the engine does
    return Image.open(p).convert('RGBA')


def variant(tx, ty):
    return FLOOR_MIX[((tx * 73856093) ^ (ty * 19349663)) % len(FLOOR_MIX)]


def tile_name(grid, x, y, theme):
    c = grid[y][x]
    if c == '#':
        for ny in (y - 1, y, y + 1):
            for nx in (x - 1, x, x + 1):
                if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] != '#':
                    return 'wall'
        return 'rock'
    if c == 'D':
        return 'door'
    if c == '~':
        if theme == 'deep':
            return 'hoard'
        if theme == 'abyss':
            return variant(x + 40, y)
        return 'water'
    return variant(x + 40, y)


def map_patch(theme, sprites=True, grid=MAP):
    W, H = len(grid[0]), len(grid)
    im = Image.new('RGBA', (W * T, H * T))
    for y in range(H):
        for x in range(W):
            im.paste(load_tile(theme, tile_name(grid, x, y, theme)), (x * T, y * T))
    if sprites:
        for (x, y, k, sid) in SPRITES.get(theme, SPRITES['base']):
            p = os.path.join(MON if k == 'm' else ITEMS, sid + '.png')
            if os.path.exists(p):
                s = Image.open(p).convert('RGBA').resize((T, T))
                im.alpha_composite(s, (x * T, y * T))
    return im


def floor_grid(theme, n=6):
    im = Image.new('RGBA', (n * T, n * T))
    for y in range(n):
        for x in range(n):
            im.paste(load_tile(theme, variant(x, y)), (x * T, y * T))
    return im


def at40(im):
    """The picture as the map's medium zoom draws it (a 64 px tile at 40 px)."""
    return im.resize((im.width * 40 // T, im.height * 40 // T), Image.BOX)


def label(dr, xy, text, col=(255, 220, 140), font=None):
    dr.text(xy, text, fill=col, font=font or BOLD)


def theme_sheet(theme, out):
    patch = map_patch(theme)
    grid = floor_grid(theme)
    names = [n[:-4] for n in sorted(os.listdir(tile_dir(theme))) if n.endswith('.png')]
    W = patch.width + 20 + grid.width + 20
    H = 40 + patch.height + 30 + at40(patch).height + 40 + 140
    sh = Image.new('RGB', (W, max(H, 40 + grid.height + 30 + 400)), BG); dr = ImageDraw.Draw(sh)
    label(dr, (10, 10), f'{theme}: map at 64 px')
    sh.paste(patch, (10, 36))
    label(dr, (patch.width + 30, 10), 'floor variants mixed, 6x6')
    sh.paste(grid, (patch.width + 30, 36))
    y = 36 + patch.height + 30
    label(dr, (10, y - 24), 'the same at 40 px')
    sh.paste(at40(patch), (10, y))
    base = map_patch('base')
    sh.paste(at40(base), (20 + at40(patch).width, y))
    label(dr, (20 + at40(patch).width, y - 24), 'base set at 40 px')
    y = 36 + grid.height + 30
    x = patch.width + 30 + 0
    yy = y + at40(patch).height + 60 if False else 36 + patch.height + 30 + at40(patch).height + 30
    x = 10
    for n in names:
        t = Image.open(os.path.join(tile_dir(theme), n + '.png')).convert('RGB')
        a = np.asarray(t).astype(np.float32)
        l = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114).mean()
        sh.paste(t.resize((96, 96), Image.NEAREST), (x, yy))
        dr.text((x, yy + 98), f'{n} {l:.0f}', fill=(220, 220, 230), font=FONT)
        x += 108
    sh.save(out)
    return out


# ---------------------------------------------------------------- props
def briefs():
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, 'briefs', 'domains_*.json'))):
        s = os.path.basename(f)[len('domains_'):-5]
        for b in json.load(open(f, encoding='utf-8')):
            b['_set'] = s
            out.append(b)
    return out


def on_tile(spr, b, theme=None):
    """A 64 px fixture sprite on the tile it is drawn over: its theme's floor (a wall
    prop over the wall)."""
    theme = theme or b.get('theme', 'base')
    under = load_tile(theme, 'wall' if b.get('layer') == 'wall' else 'floor').copy()
    under.alpha_composite(spr.convert('RGBA'))
    return under


def props_sheet(set_name, out, n=3, only=None):
    """Working sheet: every candidate of a set, painting + install cut on its tile at 64 and 40 px."""
    import domain_props
    bs = [b for b in briefs() if b['_set'] == set_name and (not only or b['id'] in only)]
    P, S, R = 150, 128, 80
    rowh = max(P, S) + 34
    W = 10 + 230 + n * (P + S + R + 24)
    sh = Image.new('RGB', (W, 10 + len(bs) * rowh), BG); dr = ImageDraw.Draw(sh)
    for r, b in enumerate(bs):
        y = 10 + r * rowh
        label(dr, (10, y), b['id'])
        dr.text((10, y + 22), f"{b.get('layer')} / {b.get('theme')} / p{b.get('p', 1)}", fill=(180, 180, 200), font=FONT)
        import textwrap
        for k, ln in enumerate(textwrap.wrap('; '.join(b.get('must_show', [])), 32)[:7]):
            dr.text((10, y + 40 + k * 14), ln, fill=(150, 230, 150), font=FONT)
        for c in range(1, n + 1):
            x = 240 + (c - 1) * (P + S + R + 24)
            pix = os.path.join(DOM, set_name, b['id'], f'c{c}_pixel.png')
            if not os.path.exists(pix):
                continue
            sh.paste(Image.open(pix).convert('RGB').resize((P, P), Image.LANCZOS), (x, y + 24))
            spr = domain_props.install_cut(b, c)
            t = on_tile(spr, b)
            sh.paste(t.resize((S, S), Image.NEAREST), (x + P + 4, y + 24))
            t40 = at40(t)
            sh.paste(t40.resize((R, R), Image.NEAREST), (x + P + S + 8, y + 24))
            label(dr, (x, y + 2), str(c), (255, 255, 255))
            mf = domain_props.mech_fail(b, c)
            if mf:
                dr.text((x + 20, y + 4), '; '.join(mf)[:40], fill=(255, 120, 120), font=FONT)
    sh.save(out)
    return out


def _vignette(spr, b):
    """The fixture in a 3x3 patch of its theme, the way it would sit on the map."""
    theme = b.get('theme', 'base')
    W = 'wall'
    if b.get('layer') == 'wall':
        grid = [[W, W, W], [W, 'X', W], [variant(1, 7), variant(2, 7), variant(3, 7)]]
    elif b.get('set') == 'barrier' or b.get('_set') == 'barrier':
        grid = [[W, variant(2, 1), W], [W, 'X', W], [W, variant(2, 3), W]]
    else:
        grid = [[variant(x + 1, y + 1) for x in range(3)] for y in range(3)]
    im = Image.new('RGBA', (3 * T, 3 * T))
    for y in range(3):
        for x in range(3):
            n = grid[y][x]
            on = 'water' if b.get('id') == 'lily_pads' else 'floor'           # lily pads float on the pool
            t = load_tile(theme, 'wall' if n == 'X' and b.get('layer') == 'wall' else (on if n == 'X' else n))
            im.paste(t, (x * T, y * T))
    im.alpha_composite(spr.convert('RGBA'), (T, T))
    return im


def final(prefix='DOMAIN_ART_SHEET_{:02d}.png'):
    """The sheets the lead reviews, at the project root."""
    import domain_props
    made = []
    k = 1
    titles = {'temple': 'The Forgotten Temple (floors 21-40)', 'deep': 'The Scorched Deep (floors 41-60)',
              'rime': 'The Rime Halls (floors 61-80)', 'abyss': 'The Abyss (floors 81-100)', 'base': 'Base set (the Labyrinth, 1-20)'}
    for theme in ('temple', 'deep', 'rime', 'abyss'):
        patch = map_patch(theme)
        grid = floor_grid(theme)
        p40 = at40(patch)
        n_tiles = len([f for f in os.listdir(tile_dir(theme)) if f.endswith('.png')])
        W = max(20 + patch.width + 30 + grid.width + 20, 40 + n_tiles * 126)
        H = 50 + patch.height + 40 + p40.height + 40 + 150
        sh = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(sh)
        label(dr, (20, 12), f'{titles[theme]}: map patch at 64 px, installed monsters and items on it')
        sh.paste(patch, (20, 44))
        label(dr, (50 + patch.width, 12 + 16), 'floors mixed as the renderer mixes them')
        sh.paste(grid, (50 + patch.width, 44))
        y = 44 + patch.height + 34
        label(dr, (20, y - 26), 'the same patch at 40 px (the map\'s medium zoom)')
        sh.paste(p40, (20, y))
        b40 = at40(map_patch('base'))
        label(dr, (40 + p40.width, y - 26), 'the base set at 40 px, for brightness')
        sh.paste(b40, (40 + p40.width, y))
        y += p40.height + 30
        x = 20
        for n in sorted(f[:-4] for f in os.listdir(tile_dir(theme)) if f.endswith('.png')):
            t = Image.open(os.path.join(tile_dir(theme), n + '.png')).convert('RGB')
            a = np.asarray(t).astype(np.float32)
            l = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114).mean()
            sh.paste(t.resize((112, 112), Image.NEAREST), (x, y))
            dr.text((x, y + 116), f'{n}  ({l:.0f})', fill=(220, 220, 230), font=FONT)
            x += 126
        out = os.path.join(ROOT, prefix.format(k)); sh.save(out); made.append(out); k += 1
    # all four next to the base set
    pats = [('base', at40(map_patch('base')))] + [(t, at40(map_patch(t))) for t in ('temple', 'deep', 'rime', 'abyss')]
    pw, ph = pats[0][1].size
    sh = Image.new('RGB', (3 * (pw + 30) + 20, 2 * (ph + 50) + 40), BG); dr = ImageDraw.Draw(sh)
    label(dr, (20, 10), 'All four themes beside the base set, at 40 px')
    for i, (t, im) in enumerate(pats):
        x, y = 20 + (i % 3) * (pw + 30), 50 + (i // 3) * (ph + 50)
        label(dr, (x, y - 22), titles[t])
        sh.paste(im, (x, y))
    out = os.path.join(ROOT, prefix.format(k)); sh.save(out); made.append(out); k += 1
    # the fixtures, set by set, each in a 3x3 patch of its theme at 64 px and at 40 px
    rv = domain_props.review()
    art = json.load(open(os.path.join(ROOT, '_alive_research', 'art_list.json'), encoding='utf-8'))
    order = ['barrier', 'labyrinth', 'any', 'temple', 'deep', 'rime', 'abyss', 'room', 'lore', 'hazard', 'camp']
    props = sorted(art['props'], key=lambda p: (p['p'], order.index(p['set'])))
    fx = os.path.join(INSTALL, 'fixtures')
    by_id = {b['id']: b for b in briefs()}
    cells = []
    for p in props:
        f = os.path.join(fx, p['id'] + '.png')
        if not os.path.exists(f):
            continue
        b = dict(by_id.get(p['id'], {}), layer=p['layer'], set=p['set'])
        b.setdefault('theme', {'temple': 'temple', 'deep': 'deep', 'rime': 'rime', 'abyss': 'abyss'}.get(p['set'], 'base'))
        if p['id'] == 'bronze_grate_open':
            b['theme'] = 'base'
        cells.append((p, b, Image.open(f).convert('RGBA')))
    per = 20
    CW, CH = 3 * T + 3 * 40 + 50, 3 * T + 56
    for s in range(0, len(cells), per):
        chunk = cells[s:s + per]
        cols = 5
        rows = (len(chunk) + cols - 1) // cols
        sh = Image.new('RGB', (20 + cols * CW, 50 + rows * CH), BG); dr = ImageDraw.Draw(sh)
        label(dr, (20, 12), 'Fixtures on their theme (left: 64 px, right: 40 px). Status from the review: good / weak.')
        for i, (p, b, spr) in enumerate(chunk):
            x, y = 20 + (i % cols) * CW, 50 + (i // cols) * CH
            st = rv.get(p['id'], {}).get('status', 'good')
            col = (255, 220, 140) if st == 'good' else (255, 140, 120)
            label(dr, (x, y), f"{p['id']}", col)
            dr.text((x, y + 20), f"{p['layer']} / {p['set']} / p{p['p']} / {st}", fill=(180, 180, 200), font=FONT)
            v = _vignette(spr, b)
            sh.paste(v, (x, y + 38))
            sh.paste(at40(v), (x + 3 * T + 16, y + 38))
        out = os.path.join(ROOT, prefix.format(k)); sh.save(out); made.append(out); k += 1
    return made


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'final':
        for p in final():
            print(p)
    if cmd == 'themes':
        for th in (sys.argv[2:] or ['temple', 'deep', 'rime', 'abyss']):
            print(theme_sheet(th, os.path.join(DOM, f'THEME_{th}.png')))
    elif cmd == 'props':
        only = sys.argv[3].split(',') if len(sys.argv) > 3 else None
        tag = sys.argv[4] if len(sys.argv) > 4 else ''
        print(props_sheet(sys.argv[2], os.path.join(DOM, f'PROPS_{sys.argv[2]}{tag}.png'), only=only))
