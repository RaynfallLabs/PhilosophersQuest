"""One overview sheet of the reviewer's pick for every creature.

    <ComfyUI python> tools/content/genart/picks.py <briefs.json> <run dir> <out.png>

Reads <run dir>/review.json: {"<id>": {"pick": 2, "fails": {"1": "two knives"}, "note": "..."}}.
Each creature is shown as the redrawn picture and as the 64 px sprite at 3x on a floor colour.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

briefs = json.load(open(sys.argv[1], encoding='utf-8'))
run, out = sys.argv[2], sys.argv[3]
review = json.load(open(os.path.join(run, 'review.json'), encoding='utf-8'))
font = ImageFont.truetype('consolab.ttf', 15); small = ImageFont.truetype('consola.ttf', 12)
BIG, SPR, PAD, LAB = 240, 192, 10, 40
CW = BIG + SPR + PAD * 2
cols = 4
fams = []
for b in briefs:
    if b['family'] not in fams:
        fams.append(b['family'])
order = sorted(briefs, key=lambda b: (fams.index(b['family']), b.get('rank', 0)))
rows = (len(order) + cols - 1) // cols
sheet = Image.new('RGB', (cols * CW + PAD, rows * (BIG + LAB + PAD) + PAD), (24, 22, 28))
dr = ImageDraw.Draw(sheet)
for i, b in enumerate(order):
    r = review.get(b['id'], {})
    c = r.get('pick')
    x = PAD + (i % cols) * CW; y = PAD + (i // cols) * (BIG + LAB + PAD)
    dr.text((x, y + BIG + 2), f"{i + 1}. {b['id']}" + (f"  (c{c})" if c else '  NO PICK'), fill=(255, 220, 140), font=font)
    if r.get('note'):
        dr.text((x, y + BIG + 20), r['note'][:56], fill=(190, 190, 200), font=small)
    if not c:
        continue
    sheet.paste(Image.open(os.path.join(run, b['id'], f'c{c}_pixel.png')).convert('RGB').resize((BIG, BIG), Image.LANCZOS), (x, y))
    spr = Image.open(os.path.join(run, b['id'], f'c{c}_sprite.png')).resize((SPR, SPR), Image.NEAREST)
    tile = Image.new('RGB', (SPR, SPR), (58, 52, 46)); tile.paste(spr, (0, 0), spr)
    sheet.paste(tile, (x + BIG + 4, y + BIG - SPR))
sheet.save(out)
print(out, len(order))
