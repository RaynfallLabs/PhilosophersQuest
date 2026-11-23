"""Review sheets for the dish pictures, old beside new, for Brandon (2026-11-22).

    py tools/content/genart/dish_art_review.py [--before <git rev>] [--out <folder>]

Draws, from the book as it is now and as it was at ``--before`` (default the
commit before the rule changed, fd431df4):

  DISH_ART_REVIEW_2026_11_22_<n>.png      about 60 dishes across forms and
      tiers whose picture changed (the Goblin Cheese Grill first): name,
      ingredients, tier and benefit, the old picture and the new, and what
      each shows (tools/content/kitchen/dish_pictures.json);
  DISH_ART_REVIEW_2026_11_22_NO_MATCH_<n>.png   every dish with no fair
      picture yet (tools/content/kitchen/dish_art_no_match.json): what it
      shows for now and what its own picture should show.

Pygame only, headless; nothing here runs at game time.
"""
import argparse
import json
import os
import subprocess
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))
import dish_art  # noqa: E402
import kitchen  # noqa: E402

ART = os.path.join(ROOT, 'assets', 'tiles', 'items')
STEM = 'DISH_ART_REVIEW_2026_11_22'
BACK, PANEL, INK, DIM, GOLD, RED, GREEN = ((24, 22, 28), (38, 35, 44), (236, 230, 216), (160, 152, 140),
                                           (232, 192, 72), (220, 110, 96), (130, 200, 120))
TAB_WORD = {'hp': 'HP', 'sp': 'SP', 'mp': 'MP', 'stat': 'Stat', 'special': 'Special'}
PER_SHEET = 20
SAMPLE = 60


def _fonts():
    return (pygame.font.SysFont('arial', 30, bold=True), pygame.font.SysFont('arial', 19, bold=True),
            pygame.font.SysFont('arial', 16))


def _wrap(font, text, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if font.size(t)[0] <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _text(surf, font, text, pos, colour, width=None, max_lines=9):
    x, y = pos
    for line in (_wrap(font, text, width) if width else [text])[:max_lines]:
        surf.blit(font.render(line, True, colour), (x, y))
        y += font.get_linesize()
    return y


def _pic(art, size=128):
    path = os.path.join(ART, art + '.png')
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (size, size))


def _names(rec):
    ings, foods = dish_art._ingredients(), dish_art._foods()
    return ', '.join(dish_art._name({**ings, **foods}, i) for i in rec['ingredients'])


def _sees(art):
    row = dish_art.catalogue()['pictures'].get(art)
    return row['sees'] if row else art


def _old_book(rev):
    raw = subprocess.run(['git', '-C', ROOT, 'show', f'{rev}:data/items/recipes.json'],
                         capture_output=True, check=True).stdout
    return json.loads(raw.decode('utf-8'))


def sample(book, old):
    """About SAMPLE changed dishes, the Goblin Cheese Grill first, spread over
    the forms and, within a form, over the tiers."""
    changed = [r for r in book if dish_art.is_ordinary(r) and old.get(r['id'], {}).get('art') != r['art']]
    first = [r for r in changed if r['name'] == 'Goblin Cheese Grill']
    by_form = {}
    for r in sorted(changed, key=lambda r: (kitchen.dish_tier(r), r['name'])):
        if r in first:
            continue
        by_form.setdefault(dish_art.dish_form(r['name']), []).append(r)
    picks = list(first)
    for f, rs in by_form.items():                # each form's dishes, one tier after another
        tiers = {}
        for r in rs:
            tiers.setdefault(kitchen.dish_tier(r), []).append(r)
        by_form[f] = [r for i in range(len(rs)) for t in sorted(tiers) if i < len(tiers[t])
                      for r in [tiers[t][i]]]
    rnd = 0
    while len(picks) < SAMPLE and any(len(v) > rnd for v in by_form.values()):
        for f in sorted(by_form, key=lambda f: (-len(by_form[f]), f)):
            if rnd < len(by_form[f]) and len(picks) < SAMPLE:
                picks.append(by_form[f][rnd])
        rnd += 1
    return picks


def draw_changes(picks, old, out_dir):
    with open(dish_art.NO_MATCH, encoding='utf-8') as f:
        lost = json.load(f)['dishes']
    title, bold, small = _fonts()
    colw, rowh, pad, head = 1000, 182, 20, 92
    paths = []
    for n in range(0, len(picks), PER_SHEET):
        chunk = picks[n:n + PER_SHEET]
        rows = (len(chunk) + 1) // 2
        sheet = pygame.Surface((pad * 3 + colw * 2, head + rows * rowh + pad))
        sheet.fill(BACK)
        _text(sheet, title, f'Dish pictures, old and new ({n // PER_SHEET + 1} of '
              f'{(len(picks) + PER_SHEET - 1) // PER_SHEET})', (pad, 16), GOLD)
        _text(sheet, small, 'Rule: a picture of the dish\'s form, showing no food the dish does not contain; '
              'then its tier\'s vessel and its benefit\'s colour where such a picture is drawn.',
              (pad, 56), DIM)
        for i, r in enumerate(chunk):
            x = pad + (i % 2) * (colw + pad)
            y = head + (i // 2) * rowh
            pygame.draw.rect(sheet, PANEL, (x, y, colw, rowh - 10), border_radius=8)
            tier, tab = kitchen.dish_tier(r), kitchen.dish_tab(r)
            ty = _text(sheet, bold, r['name'], (x + 12, y + 10), INK, 300, 2)
            ty = _text(sheet, small, f'Tier {tier}, {TAB_WORD[tab]}  ({dish_art.dish_form(r["name"])})',
                       (x + 12, ty + 2), GOLD)
            ty = _text(sheet, small, _names(r), (x + 12, ty + 4), DIM, 300, 4)
            if r['id'] in lost:
                _text(sheet, small, 'No fair picture yet: ' + lost[r['id']]['wants'], (x + 12, ty + 4),
                      RED, 300, 3)
            o, nw = old[r['id']]['art'], r['art']
            for k, (art, label, col) in enumerate(((o, 'Old', RED), (nw, 'New', GREEN))):
                px = x + 330 + k * 335
                sheet.blit(_pic(art), (px, y + 12))
                _text(sheet, bold, label, (px + 136, y + 12), col)
                _text(sheet, small, _sees(art), (px + 136, y + 36), INK, 190, 7)
        path = os.path.join(out_dir, f'{STEM}_{n // PER_SHEET + 1}.png')
        pygame.image.save(sheet, path)
        paths.append(path)
    return paths


def draw_no_match(book, out_dir):
    with open(dish_art.NO_MATCH, encoding='utf-8') as f:
        lost = json.load(f)['dishes']
    by_id = {r['id']: r for r in book}
    title, bold, small = _fonts()
    cols, per, colw, rowh, pad, head = 3, 33, 640, 168, 20, 92
    ids = sorted(lost, key=lambda k: (lost[k]['form'], lost[k]['tier'], lost[k]['name']))
    paths = []
    sheets = (len(ids) + per - 1) // per
    for n in range(0, len(ids), per):
        chunk = ids[n:n + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = pygame.Surface((pad * (cols + 1) + colw * cols, head + rows * rowh + pad))
        sheet.fill(BACK)
        _text(sheet, title, f'Dishes with no fair picture yet: {len(ids)} ({n // per + 1} of {sheets})',
              (pad, 16), GOLD)
        _text(sheet, small, 'Each shows the least wrong picture drawn today, until its own is made. '
              '"Wants" is what its own picture should show.', (pad, 56), DIM)
        for i, rid in enumerate(chunk):
            row = lost[rid]
            x = pad + (i % cols) * (colw + pad)
            y = head + (i // cols) * rowh
            pygame.draw.rect(sheet, PANEL, (x, y, colw, rowh - 10), border_radius=8)
            sheet.blit(_pic(row['given']), (x + 10, y + 12))
            tx = x + 150
            ty = _text(sheet, bold, row['name'], (tx, y + 10), INK, colw - 160, 2)
            ty = _text(sheet, small, f"Tier {row['tier']}, {TAB_WORD[row['benefit']]}. "
                       + ', '.join(row['ingredients']), (tx, ty + 2), DIM, colw - 160, 2)
            ty = _text(sheet, small, 'Wants: ' + row['wants'], (tx, ty + 4), GREEN, colw - 160, 3)
            _text(sheet, small, 'Now: ' + row['why'], (tx, ty + 2), RED, colw - 160, 2)
            assert by_id[rid]['art'] == row['given'], rid
        path = os.path.join(out_dir, f'{STEM}_NO_MATCH_{n // per + 1}.png')
        pygame.image.save(sheet, path)
        paths.append(path)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default='fd431df4')
    ap.add_argument('--out', default=ROOT)
    args = ap.parse_args(argv)
    pygame.init()
    pygame.display.set_mode((1, 1))
    book = kitchen.book()
    old = _old_book(args.before)
    picks = sample(book, old)
    for p in draw_changes(picks, old, args.out) + draw_no_match(book, args.out):
        print(p)


if __name__ == '__main__':
    main()
