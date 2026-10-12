"""Brief -> painted draft -> pixel pass -> 64px sprite -> checks -> review sheets.

    <ComfyUI python> tools/content/genart/pipeline.py tools/content/genart/briefs/pilot.json
        [--n 3] [--only id,id] [--out _genart/pilot] [--sheets-only]

FRONT END: every creature has a written brief (see briefs/README.md): what it is,
its colours, what it wears, exactly what it holds, its pose, and two lists,
must_show and must_not_show, which say what makes it THIS creature and this tier.
BACK END: each candidate gets mechanical checks here (one piece, not cropped, clean
background), and a review sheet per family prints the lists beside the pictures so
a reviewer can mark each one. Verdicts live in <out>/review.json.
"""
import argparse, json, os, re, sys, textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comfy, convert
from PIL import Image, ImageDraw, ImageFont

KEY_WORDS = {'magenta': 'pure magenta (#FF00FF)', 'green': 'pure bright green (#00FF00)', 'blue': 'pure bright blue (#0000FF)'}
# Colour words a backdrop of each key would eat. A brief that names one of them in
# `colours` with that key is refused before anything is drawn.
KEY_CLASH = {'magenta': ('magenta', 'pink', 'purple', 'violet', 'crimson', 'red', 'orange', 'rose'),
             'green': ('green', 'lime', 'olive', 'moss'),
             'blue': ('blue', 'navy', 'indigo', 'azure', 'cyan', 'violet', 'purple')}
FIELDS = ('id', 'family', 'what', 'colours', 'pose', 'must_show', 'must_not_show')


def check_briefs(briefs):
    """Front-end check: every brief is complete and its backdrop will not eat its own colours."""
    bad = []
    for b in briefs:
        for f in FIELDS:
            if not b.get(f):
                bad.append(f"{b.get('id', '?')}: no {f}")
        text = (b.get('colours', '') + ' ' + b.get('what', '')).lower()
        hit = [w for w in KEY_CLASH[b.get('key', 'magenta')] if re.search(r'\b' + w, text)]
        if hit:
            bad.append(f"{b['id']}: a {b.get('key', 'magenta')} backdrop would eat its {', '.join(hit)}")
        if 'holds' in b and 'exactly' not in b['holds'] and 'nothing' not in b['holds'] and 'empty' not in b['holds']:
            bad.append(f"{b['id']}: 'holds' does not say exactly what, or that the hands are empty")
    return bad

# The look Brandon chose on 2026-10-11 (row C of the style board): a classic painted
# high-fantasy illustration, then a light pixel pass that keeps the painting.
DRAFT = ("A classic fantasy oil painting of {what} Colours: {colours} {wears} {holds} {pose} "
         "Painted like the cover illustration of a 1980s fantasy roleplaying rulebook: realistic anatomy, dramatic warm "
         "light from the upper left with a cold rim light on the right, rich earthy colours with jewel-bright accents, "
         "weathered and intricate detail on every surface, heroic and serious. The figure itself is clearly and brightly "
         "lit so every part of it can be read; it is never a dark silhouette. "
         "{action} "
         "Anything it holds is drawn bold, sturdy and a little larger than life, with thick shafts, limbs and blades, "
         "and is held out clear of the body so its whole shape can be seen against the backdrop. "
         "One single figure only, {whole}, seen from far "
         "enough away that the figure is small in the picture: it fills only the middle two thirds, with wide empty "
         "backdrop above it, below it and on both sides. Nothing it holds reaches the edge of the picture. "
         "The background is one completely flat, evenly lit, solid {key} filling the whole picture, with no shading or "
         "gradient in it. There is no ground, no floor, no horizon and no shadow of any kind under or behind the figure, and nothing lies under or around it: no base, no rock, no web, no grass, no puddle, no rubble, no smoke.")
DRAFT_NEG = ("shadow on the ground, cast shadow, drop shadow, floor, ground, scenery, multiple figures, character sheet, "
             "text, labels, border, photo, 3d render, blurry, chibi, cute, big head, cartoon, cartoon proportions, "
             "bright candy colours, flat lighting, dark silhouette, cropped, close-up, portrait, half-length, cut off at the knees, "
             "standing still, stiff symmetrical pose, arms hanging at the sides, thin spindly weapon, "
             "pedestal, base, platform, patch of ground, cobweb, rocks underfoot, debris, gore, blood, nudity")
PIXEL = ("detailed pixel art of a classic fantasy oil painting, realistic proportions, dramatic warm side lighting, "
         "rich earthy colours, intricate detail, dark outline, serious high fantasy, {what} {colours} {holds} "
         "single figure, flat solid {keyname} background, no shadow")
PIXEL_NEG = ("blurry, photograph, 3d render, text, frame, chibi, cute, cartoon, big head, super-deformed, extra limbs, "
             "extra weapons, multiple characters, ground, floor, cast shadow, drop shadow")
# The fixed wording once assumed a head, feet and legs, which pushed fire, slime, clouds
# and eyeballs towards legs or a small man underneath. A brief with "body": "shapeless"
# gets wording that names no body part.
ACTION = {
    'legged': "The figure is caught in the middle of an action like a frozen frame of a fight: weight on one leg, "
              "body twisted, limbs at different heights; it is never standing straight with its arms at its sides.",
    'shapeless': "It is caught in the middle of a movement like a frozen frame: its mass leaning, surging or "
                 "lashing to one side, lopsided and alive, never a still symmetrical lump.",
}
WHOLE = {
    'legged': 'shown full length from the top of its head to the soles of its feet',
    'shapeless': 'shown whole from its highest point to its lowest, with nothing else beneath it',
}
PIXEL_DENOISE = 0.42       # low: the painting survives, the edges sharpen
INSET = 128                # the 64 px sprite shown at 2x on the review sheets


def prompts(b):
    holds = b.get('holds') or 'Its hands are empty and it holds nothing.'
    wears = b.get('wears', '')
    body = 'shapeless' if b.get('body') == 'shapeless' else 'legged'
    f = dict(what=b['what'], colours=b['colours'], wears=wears, holds=holds, pose=b['pose'])
    if body == 'shapeless' and not b.get('holds'):
        f['holds'] = 'It holds nothing.'
    neg = DRAFT_NEG + ''.join(', ' + x for x in b.get('must_not_show', []))
    return (DRAFT.format(key=KEY_WORDS[b.get('key', 'magenta')], action=ACTION[body], whole=WHOLE[body], **f), neg,
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


def generate(items, out, base_seed=5000):
    """items: [(brief, candidate number)]. Draws each one, both passes."""
    if not comfy.running():
        raise SystemExit('ComfyUI is not running on 127.0.0.1:8188')
    drafts, meta = [], {}
    for b, c in items:
        dp, dn, pp, pn = prompts(b)
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
            pix.append((comfy.pixel_workflow(name, pp, pn, seed, PIXEL_DENOISE), os.path.join(out, bid, f'c{c}_pixel.png')))
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
            spr.save(os.path.join(out, b['id'], f'c{c}_sprite.png'))
            facts['mechanical_fail'] = mechanical(facts)
            report[f"{b['id']}/c{c}"] = facts
    json.dump(report, open(os.path.join(out, 'mechanical.json'), 'w'), indent=1)
    return report


def sheets(briefs, out, n, report):
    """One sheet per family, creatures in tier order, the brief's lists printed beside the pictures."""
    font = ImageFont.truetype('consola.ttf', 12); bold = ImageFont.truetype('consolab.ttf', 18)
    BIG, PAD, TEXT_W = 280, 10, 470
    floor = (58, 52, 46)
    fams = {}
    for b in briefs:
        fams.setdefault(b['family'], []).append(b)
    made = []
    for fam, bs in fams.items():
        bs.sort(key=lambda b: b.get('rank', 0))
        W = PAD + TEXT_W + n * (BIG + PAD) + PAD
        rowh = BIG + PAD
        H = PAD + len(bs) * rowh + INSET + 54
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
                p = os.path.join(out, b['id'], f'c{c}_pixel.png'); s = os.path.join(out, b['id'], f'c{c}_sprite.png')
                if not os.path.exists(p):
                    continue
                sh.paste(Image.open(p).convert('RGB').resize((BIG, BIG), Image.LANCZOS), (x, y))
                spr = Image.open(s)
                tile = Image.new('RGB', (INSET + 4, INSET + 4), floor)
                big = spr.resize((INSET, INSET), Image.NEAREST); tile.paste(big, (2, 2), big)
                sh.paste(tile, (x + BIG - INSET - 4, y + BIG - INSET - 4))
                fails = report.get(f"{b['id']}/c{c}", {}).get('mechanical_fail', [])
                dr.rectangle((x, y, x + 26, y + 22), fill=(0, 0, 0))
                dr.text((x + 4, y + 2), str(c), fill=(255, 255, 255), font=bold)
                if fails:
                    dr.rectangle((x, y + BIG - 20, x + BIG - INSET - 6, y + BIG), fill=(120, 20, 20))
                    dr.text((x + 3, y + BIG - 19), '; '.join(fails)[:24], fill=(255, 255, 255), font=font)
        # the lineup: first candidate of each tier at true scale x2, to read the family as a set
        y = PAD + len(bs) * rowh + 10
        dr.text((PAD, y), 'LINEUP (candidate 1 of each, low tier to high):', fill=(236, 226, 200), font=bold)
        x = PAD
        for b in bs:
            s = os.path.join(out, b['id'], 'c1_sprite.png')
            if os.path.exists(s):
                spr = Image.open(s); tile = Image.new('RGB', (INSET + 4, INSET + 4), floor)
                big = spr.resize((INSET, INSET), Image.NEAREST); tile.paste(big, (2, 2), big)
                sh.paste(tile, (x, y + 28)); x += INSET + 12
        path = os.path.join(out, f'REVIEW_{fam}.png'); sh.save(path); made.append(path)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('briefs'); ap.add_argument('--n', type=int, default=3)
    ap.add_argument('--only', default=''); ap.add_argument('--out', default='_genart/pilot')
    ap.add_argument('--sheets-only', action='store_true'); ap.add_argument('--seed', type=int, default=5000)
    ap.add_argument('--retries', type=int, default=3)
    ap.add_argument('--check', action='store_true', help='only check the briefs, draw nothing')
    a = ap.parse_args()
    briefs = json.load(open(a.briefs, encoding='utf-8'))
    todo = [b for b in briefs if not a.only or b['id'] in a.only.split(',')]
    problems = check_briefs(todo)
    if problems:
        raise SystemExit('Briefs need fixing first:\n  ' + '\n  '.join(problems))
    if a.check:
        ids = [b['id'] for b in briefs]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        print(f'{len(briefs)} briefs OK' + (f'; DUPLICATE ids: {dup}' if dup else ''))
        return
    os.makedirs(a.out, exist_ok=True)
    if not a.sheets_only:
        generate([(b, c) for b in todo for c in range(1, a.n + 1)], a.out, a.seed)
    report = cut(briefs, a.out, a.n)
    # A candidate that fails a mechanical check is drawn again from a new seed, so the
    # reviewer is not handed pictures that are cropped or in pieces.
    by_id = {b['id']: b for b in todo}
    for attempt in range(1, a.retries + 1):
        if a.sheets_only:
            break
        again = [(by_id[k.split('/')[0]], int(k.split('/c')[1])) for k, v in report.items()
                 if v['mechanical_fail'] and k.split('/')[0] in by_id]
        if not again:
            break
        print(f'retry {attempt}: {len(again)} candidates failed a mechanical check')
        generate(again, a.out, a.seed + 1000 * attempt)
        report = cut(briefs, a.out, a.n)
    failing = {k: v['mechanical_fail'] for k, v in report.items() if v['mechanical_fail']}
    print(f'{len(report)} candidates, {len(failing)} fail a mechanical check')
    for k, v in sorted(failing.items()):
        print('  ', k, v)
    fams = {b['family'] for b in todo}
    for p in sheets([b for b in briefs if b['family'] in fams], a.out, a.n, report):
        print(p)


if __name__ == '__main__':
    main()
