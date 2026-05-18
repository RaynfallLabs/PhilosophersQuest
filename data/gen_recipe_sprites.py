#!/usr/bin/env python3
"""Generate 32x32 procedural pixel-art sprites for the 29 new compound recipes
authored in Phase 5C. Output: assets/tiles/items/recipe_{id}.png (RGBA).

Existing recipe sprites in the bank are 40x40 AI-generated images; this
generator produces consistent-style pixel art at 32x32 so the new entries
display something more specific than the fallback first-ingredient sprite.

Each recipe gets a plate/bowl base in a color derived from its bonus_type +
bonus_stat, with ingredient-flavored accent shapes on top. The result is
visually distinct per dish without claiming AI-quality renders.

Usage: python data/gen_recipe_sprites.py
"""
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install Pillow"); sys.exit(1)

ROOT     = Path(__file__).parent.parent
OUT_DIR  = ROOT / 'assets' / 'tiles' / 'items'
OUT_DIR.mkdir(parents=True, exist_ok=True)
S        = 32


# Color palettes per bonus theme — drives the plate / glaze color
_PALETTES = {
    'STR':  ((200, 60, 60),   (140, 30, 30),   (240, 180, 100)),  # red + gold
    'CON':  ((150, 100, 60),  (100, 60, 30),   (220, 180, 120)),  # earthy brown
    'DEX':  ((100, 180, 100), (60, 130, 60),   (200, 240, 160)),  # forest greens
    'INT':  ((100, 80, 200),  (60, 50, 130),   (180, 160, 240)),  # arcane violet
    'WIS':  ((80, 140, 180),  (50, 100, 140),  (180, 220, 240)),  # contemplative teal
    'PER':  ((220, 200, 100), (180, 160, 60),  (240, 230, 180)),  # eagle-eye gold
    'all':  ((200, 180, 220), (140, 120, 160), (240, 220, 250)),  # iridescent
    'two':  ((180, 120, 180), (120, 80, 130),  (230, 190, 230)),  # plum
    'status_regenerating': ((100, 200, 130), (60, 140, 90), (190, 240, 200)),
    'status_arcane_shield':((150, 130, 220), (90, 70, 160),  (210, 200, 240)),
    'status_fire_shield':  ((230, 130, 60),  (170, 70, 30),  (245, 200, 150)),
    'status_cold_shield':  ((130, 200, 230), (70, 140, 180), (200, 240, 250)),
    'status_haste':        ((230, 200, 70),  (180, 150, 30), (245, 230, 160)),
    'status_invisible':    ((200, 200, 220), (140, 140, 170),(230, 230, 240)),
    'status_truesight':    ((220, 180, 230), (160, 120, 180),(240, 220, 245)),
    'status_poison_resist':((140, 200, 110), (90, 150, 70),  (200, 230, 170)),
    'status_blind_resist': ((180, 180, 100), (130, 130, 60), (220, 220, 160)),
    'status_shock_resist': ((220, 200, 100), (170, 150, 60), (240, 220, 160)),
    'status_death_ward':   ((180, 180, 200), (110, 110, 140),(220, 220, 240)),
    'combat_stat':         ((200, 150, 80),  (150, 100, 50), (230, 200, 150)),
    'random_stat':         ((220, 130, 200), (170, 80, 150), (240, 200, 230)),
    'default':             ((180, 160, 140), (130, 110, 90), (220, 200, 180)),
}


def _palette_for(recipe: dict) -> tuple:
    bt = recipe.get('bonus_type', '')
    bs = recipe.get('bonus_stat', '')
    be = recipe.get('bonus_effect', '')
    if bt == 'stat' and bs in _PALETTES:
        return _PALETTES[bs]
    if bt == 'status':
        key = f"status_{be}"
        if key in _PALETTES:
            return _PALETTES[key]
    if bt == 'all_stats':
        return _PALETTES['all']
    if bt == 'two_stats':
        return _PALETTES['two']
    if bt == 'combat_stat':
        return _PALETTES['combat_stat']
    if bt == 'random_stat':
        return _PALETTES['random_stat']
    return _PALETTES['default']


def _shade(c, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in c)


def _draw_recipe(recipe: dict, recipe_id: str) -> Image.Image:
    """Render a recipe sprite: round dish + glaze + ingredient hint dots.

    Layout (32x32):
      - rim at y=22-26 (a darker oval at the bottom for plate edge)
      - dish bowl at y=14-26 (filled with mid-tone)
      - food glaze at y=12-20 (lighter, on top of bowl)
      - accent dots at y=10-18 (highlights/herbs/garnish)
    """
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    primary, dark, light = _palette_for(recipe)

    # Plate (bottom oval - darker)
    plate_col = _shade(dark, 0.9)
    d.ellipse([2, 22, 30, 30], fill=plate_col + (255,))
    # Plate inner ring (lighter top of rim)
    d.ellipse([4, 21, 28, 28], fill=_shade(dark, 1.1) + (255,))

    # Bowl interior (the food's body, primary color)
    d.ellipse([5, 14, 27, 26], fill=primary + (255,))

    # Glaze/sauce layer (lighter highlights — top half of bowl)
    glaze_col = light
    d.ellipse([7, 13, 25, 22], fill=glaze_col + (220,))

    # Ingredient accents — small dots/shapes scattered on top
    accent_col = _shade(primary, 0.6)
    accent_positions = [
        (10, 14), (15, 12), (20, 14),
        (12, 18), (19, 18),
        (16, 16),
    ]
    for ax, ay in accent_positions:
        d.ellipse([ax-1, ay-1, ax+1, ay+1], fill=accent_col + (255,))

    # Steam / shine: 3 small white pixels at the top
    steam = (255, 255, 255, 200)
    d.point((12, 10), fill=steam)
    d.point((16, 8),  fill=steam)
    d.point((20, 10), fill=steam)

    # Special: status recipes get a glowing rim
    bt = recipe.get('bonus_type', '')
    if bt == 'status':
        # subtle outer glow
        glow = light + (90,)
        d.ellipse([1, 12, 31, 30], outline=glow)

    return img


def main():
    recipes = json.loads((ROOT / 'data' / 'items' / 'recipes.json').read_text(encoding='utf-8'))
    new_recipe_ids = json.loads(
        (ROOT / 'tools' / 'cooking_audit' / 'new_recipes.json').read_text(encoding='utf-8')
    ).keys()

    saved = 0
    for rid in new_recipe_ids:
        if rid not in recipes:
            print(f"  WARN: {rid} not in recipes.json")
            continue
        img = _draw_recipe(recipes[rid], rid)
        out_path = OUT_DIR / f"recipe_{rid}.png"
        img.save(out_path)
        saved += 1
        print(f"  saved recipe_{rid}.png")
    print(f"\n{saved} recipe sprites written to {OUT_DIR}")


if __name__ == '__main__':
    main()
