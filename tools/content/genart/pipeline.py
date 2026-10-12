"""Brief -> draft -> pixel art -> 48px sprite -> checks -> review sheets.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/pilot.json
        [--n 3] [--only id,id] [--out _genart/pilot] [--sheets-only]

FRONT END: every creature has a written brief (see briefs/README.md): what it is,
its colours, what it wears, exactly what it holds, its pose, and two lists,
must_show and must_not_show, which say what makes it THIS creature and this tier.
BACK END: each candidate gets mechanical checks here (one piece, not cropped, clean
background), and a review sheet per family prints the lists beside the pictures so
a reviewer can mark each one. Verdicts live in <out>/review.json.
"""
import argparse, json, os, sys, textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comfy, convert
from PIL import Image, ImageDraw, ImageFont

KEY_WORDS = {'magenta': 'pure magenta (#FF00FF)', 'green': 'pure bright green (#00FF00)'}

DRAFT = ("Pixel art game sprite of {what} Colours: {colours} {wears} {holds} {pose} "
         "Detailed 16-bit JRPG sprite style: chunky visible pixels, heavy black outline, bright rich saturated colours "
         "with strong highlights and deep shadows on the figure itself, dramatic, high-fantasy tone. "
         "One single figure only, the whole body inside the frame with a clear margin on every side. "
         "The background is one completely flat, solid {key} filling the whole picture. There is no ground, no floor, "
         "no horizon and no shadow of any kind under or behind the figure.")
DRAFT_NEG = ("shadow on the ground, cast shadow, drop shadow, floor, ground, scenery, multiple figures, character sheet, "
             "text, labels, border, photo, 3d render, smooth painting, blurry, muddy brown colours, chibi, cute, big head, cartoon proportions, cropped")
PIXEL = ("high-detail 16-bit JRPG pixel art sprite, chunky pixels, bold black outline, rich saturated colours, crisp pixel "
         "shading with bright highlights, serious high fantasy, realistic proportions, {what} {colours} {holds} single figure, isolated game asset, "
         "flat solid {keyname} background, no shadow")
PIXEL_NEG = ("blurry, painterly, realistic, photograph, 3d render, smooth gradients, muddy colours, low contrast, text, frame, "
             "chibi, cute, cartoon, big head, super-deformed, extra limbs, extra weapons, multiple characters, ground, floor, cast shadow, drop shadow")


def prompts(b):
    holds = b.get('holds') or 'Its hands are empty and it holds nothing.'
    wears = b.get('wears', '')
    f = dict(what=b['what'], colours=b['colours'], wears=wears, holds=holds, pose=b['pose'])
    neg = DRAFT_NEG + ''.join(', ' + x for x in b.get('must_not_show', []))
    return (DRAFT.format(key=KEY_WORDS[b.get('key', 'magenta')], **f), neg,
            PIXEL.format(keyname=b.get('key', 'magenta'), **f), PIXEL_NEG + ''.join(', ' + x for x in b.get('must_not_show', [])))


def mechanical(facts):
    """The reasons a candidate fails before anyone looks at it."""
    bad = []
    if facts.get('empty'):
        return ['nothing left after the cut-out']
    if facts['parts'] != 1:
        bad.append(f"{facts['parts']} separate pieces")
    if facts['touches_edge'] > 0.02:
        bad.append('cropped by the frame')
    if facts['background_ok'] < 0.85:
        bad.append('background is not the flat key colour')
    if not 0.06 <= facts['coverage'] <= 0.72:
        bad.append(f"figure fills {facts['coverage']:.0%} of the frame")
    return bad


def generate(briefs, out, n, base_seed=5000):
    if not comfy.running():
        raise SystemExit('ComfyUI is not running on 127.0.0.1:8188')
    drafts, meta = [], {}
    for b in briefs:
        dp, dn, pp, pn = prompts(b)
        for c in range(1, n + 1):
            seed = base_seed + c * 97 + sum(map(ord, b['id'])) % 1000
            d = os.path.join(out, b['id'], f'c{c}_draft.png')
            meta[(b['id'], c)] = (pp, pn, seed)
            drafts.append((comfy.draft_workflow(dp, dn, seed), d))
    print(f'pass 1: {len(drafts)} drafts'); sys.stdout.flush()
    for f in comfy.run(drafts):
        print('  FAILED', f)
    pix = []
    for (bid, c), (pp, pn, seed) in meta.items():
        d = os.path.join(out, bid, f'c{c}_draft.png')
        if os.path.exists(d):
            name = comfy.stage_input(d, f'genart_{bid}_c{c}.png')
            pix.append((comfy.pixel_workflow(name, pp, pn, seed), os.path.join(out, bid, f'c{c}_pixel.png')))
    print(f'pass 2: {len(pix)} redraws'); sys.stdout.flush()
    for f in comfy.run(pix):
        print('  FAILED', f)


def cut(briefs, out, n):
    report = {}
    for b in briefs:
        for c in range(1, n + 1):
            p = os.path.join(out, b['id'], f'c{c}_pixel.png')
            if not os.path.exists(p):
                continue
            spr, facts = convert.to_sprite(Image.open(p), b.get('key', 'magenta'))
            spr.save(os.path.join(out, b['id'], f'c{c}_48.png'))
            facts['mechanical_fail'] = mechanical(facts)
            report[f"{b['id']}/c{c}"] = facts
    json.dump(report, open(os.path.join(out, 'mechanical.json'), 'w'), indent=1)
    return report


def sheets(briefs, out, n, report):
    """One sheet per family, creatures in tier order, the brief's lists printed beside the pictures."""
    font = ImageFont.truetype('consola.ttf', 12); bold = ImageFont.truetype('consolab.ttf', 18)
    BIG, PAD, TEXT_W = 240, 10, 470
    floor = (58, 52, 46)
    fams = {}
    for b in briefs:
        fams.setdefault(b['family'], []).append(b)
    made = []
    for fam, bs in fams.items():
        bs.sort(key=lambda b: b.get('rank', 0))
        W = PAD + TEXT_W + n * (BIG + PAD) + PAD
        rowh = BIG + PAD
        H = PAD + len(bs) * rowh + 150
        sh = Image.new('RGB', (W, H), (24, 22, 28)); dr = ImageDraw.Draw(sh)
        for r, b in enumerate(bs):
            y = PAD + r * rowh
            dr.text((PAD, y), f"{b['id']}   (tier {b.get('rank', 0)})", fill=(255, 220, 140), font=bold)
            lines = []
            for label, key, col in (('MUST SHOW', 'must_show', (150, 230, 150)), ('MUST NOT', 'must_not_show', (240, 150, 150))):
                for item in b.get(key, []):
                    lines.append((f'{label}: {item}', col))
            lines.append((f"HOLDS: {b.get('holds') or 'nothing'}", (200, 200, 230)))
            yy = y + 24
            wrapped = [(ln, col) for t, col in lines for ln in textwrap.wrap(t, 66)]
            step = min(14, (rowh - 30) // max(1, len(wrapped)))
            for ln, col in wrapped:
                dr.text((PAD, yy), ln, fill=col, font=font); yy += step
            for c in range(1, n + 1):
                x = PAD + TEXT_W + (c - 1) * (BIG + PAD)
                p = os.path.join(out, b['id'], f'c{c}_pixel.png'); s = os.path.join(out, b['id'], f'c{c}_48.png')
                if not os.path.exists(p):
                    continue
                sh.paste(Image.open(p).convert('RGB').resize((BIG, BIG), Image.LANCZOS), (x, y))
                spr = Image.open(s)
                tile = Image.new('RGB', (100, 100), floor)
                big = spr.resize((96, 96), Image.NEAREST); tile.paste(big, (2, 2), big)
                sh.paste(tile, (x + BIG - 100, y + BIG - 100))
                fails = report.get(f"{b['id']}/c{c}", {}).get('mechanical_fail', [])
                dr.rectangle((x, y, x + 26, y + 22), fill=(0, 0, 0))
                dr.text((x + 4, y + 2), str(c), fill=(255, 255, 255), font=bold)
                if fails:
                    dr.rectangle((x, y + BIG - 20, x + BIG - 102, y + BIG), fill=(120, 20, 20))
                    dr.text((x + 3, y + BIG - 19), '; '.join(fails)[:24], fill=(255, 255, 255), font=font)
        # the lineup: first candidate of each tier at true scale x2, to read the family as a set
        y = PAD + len(bs) * rowh + 10
        dr.text((PAD, y), 'LINEUP (candidate 1 of each, low tier to high):', fill=(236, 226, 200), font=bold)
        x = PAD
        for b in bs:
            s = os.path.join(out, b['id'], 'c1_48.png')
            if os.path.exists(s):
                spr = Image.open(s); tile = Image.new('RGB', (100, 100), floor)
                big = spr.resize((96, 96), Image.NEAREST); tile.paste(big, (2, 2), big)
                sh.paste(tile, (x, y + 28)); x += 108
        path = os.path.join(out, f'REVIEW_{fam}.png'); sh.save(path); made.append(path)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('briefs'); ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--only', default=''); ap.add_argument('--out', default='_genart/pilot')
    ap.add_argument('--sheets-only', action='store_true'); ap.add_argument('--seed', type=int, default=5000)
    a = ap.parse_args()
    briefs = json.load(open(a.briefs, encoding='utf-8'))
    todo = [b for b in briefs if not a.only or b['id'] in a.only.split(',')]
    os.makedirs(a.out, exist_ok=True)
    if not a.sheets_only:
        generate(todo, a.out, a.n, a.seed)
    report = cut(briefs, a.out, a.n)
    failing = {k: v['mechanical_fail'] for k, v in report.items() if v['mechanical_fail']}
    print(f'{len(report)} candidates, {len(failing)} fail a mechanical check')
    for k, v in sorted(failing.items()):
        print('  ', k, v)
    for p in sheets(briefs, a.out, a.n, report):
        print(p)


if __name__ == '__main__':
    main()
