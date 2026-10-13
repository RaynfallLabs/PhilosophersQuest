"""Review sheets for the item set as a whole.

    <ComfyUI python> tools/content/genart/item_sheets.py

Writes to the project root:
  ITEM_SHEET_A_materials.png  every weapon and armour template in a spread of materials
  ITEM_SHEET_B_scale.png      one of each kind of item side by side on the floor, with a
                              monster and a hero, to judge the size classes together
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import recolour, install_items

T, S = 64, 2
font = ImageFont.truetype('consolab.ttf', 13)
floor = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'env', 'floor.png')).convert('RGBA')
picks, _ = install_items.reviewed()

MATS = [('iron', (180, 180, 180)), ('bronze', (180, 130, 60)), ('steel', (200, 210, 220)), ('hardened_gold', (220, 180, 60)),
        ('mithril', (180, 200, 220)), ('cobalt_steel', (80, 120, 200)), ('shadowiron', (40, 40, 60)), ('dragonscale', (180, 60, 50)),
        ('obsidian', (30, 25, 40)), ('leather', (160, 110, 60)), ('oak', (140, 100, 60)), ('elven_silk', (180, 230, 240)),
        ('treant_heart', (80, 130, 60)), ('void_touched', (60, 20, 80))]


def cell(spr):
    t = floor.copy(); t.alpha_composite(spr.convert('RGBA'))
    return t.resize((T * S, T * S), Image.NEAREST)


def materials():
    tpl = sorted(k for k in picks if k.startswith('tpl_'))
    W = 150 + len(MATS) * (T * S + 3)
    sheet = Image.new('RGB', (W, 22 + len(tpl) * (T * S + 3)), (24, 22, 28)); d = ImageDraw.Draw(sheet)
    for j, (m, _) in enumerate(MATS):
        d.text((150 + j * (T * S + 3) + 2, 4), m[:15], fill=(255, 220, 140), font=font)
    for i, k in enumerate(tpl):
        y = 22 + i * (T * S + 3)
        d.text((4, y + 56), k[4:], fill=(230, 230, 240), font=font)
        base = Image.open(picks[k])
        for j, (_, c) in enumerate(MATS):
            sheet.paste(cell(recolour.tint(base, c)), (150 + j * (T * S + 3), y))
    p = os.path.join(ROOT, 'ITEM_SHEET_A_materials.png'); sheet.save(p); print(p, len(tpl))


ROWS = [
    ('tiny', ['ring_of_command', 'ring_strength_iron', 'ring_regen_emerald', 'mystery_key_pandora', 'lockpick', 'philosophers_ring']),
    ('small', ['potion_of_healing', 'potion_of_haste', 'amulet_life_saving', 'eye_of_horus', 'scroll_of_identify', 'tpl_w_dagger',
               'carnwennan', 'apple', 'hard_cheese', 'cut_marrow_a_bone_white', 'cut_ichor_a_scarlet', 'gold_pile', 'tpl_w_arrow']),
    ('medium', ['tpl_a_plate_helm', 'helm_of_leonidas', 'tpl_a_leather_boots', 'tpl_a_gauntlets', 'spellbook_fireball', 'wand_of_fire',
                'wand_of_frost', 'tpl_w_shortsword', 'tpl_w_mace', 'tpl_w_axe', 'tpl_a_buckler', 'dish_t2_combo_hearth', 'dish_t5_mythic_phoenix', 'aladdins_lamp']),
    ('large', ['tpl_w_longsword', 'excalibur', 'tpl_w_battleaxe', 'tpl_w_warhammer', 'tpl_a_full_plate', 'tpl_a_chainmail', 'tpl_a_cloak',
               'cloak_of_odin', 'tpl_a_kite_shield', 'shield_of_the_spartans', 'tpl_w_shortbow', 'tpl_w_heavy_crossbow', 'tpl_a_plate_greaves']),
    ('huge', ['tpl_w_greatsword', 'tpl_w_zweihander', 'tpl_w_great_axe', 'tpl_w_maul', 'tpl_w_spear', 'tpl_w_halberd', 'tpl_w_quarterstaff',
              'tpl_w_longbow', 'gungnir', 'tpl_a_tower_shield', 'trident_of_poseidon']),
]


def scale():
    n = max(len(r) for _, r in ROWS) + 2
    sheet = Image.new('RGB', (70 + n * (T * S + 3), len(ROWS) * (T * S + 22) + 8), (24, 22, 28)); d = ImageDraw.Draw(sheet)
    mon = [Image.open(os.path.join(ROOT, 'assets', 'tiles', 'monsters', m + '.png')) for m in ('goblin', 'troll')]
    for i, (name, ids) in enumerate(ROWS):
        y = 6 + i * (T * S + 22)
        d.text((4, y + 56), name, fill=(255, 220, 140), font=font)
        x = 70
        for k in ids:
            if k in picks:
                spr = Image.open(picks[k])
                if k.startswith('tpl_'):
                    spr = recolour.tint(spr, (180, 180, 180))
                sheet.paste(cell(spr), (x, y)); d.text((x + 2, y + T * S + 2), k.replace('tpl_w_', '').replace('tpl_a_', '')[:18], fill=(200, 200, 210), font=font)
                x += T * S + 3
        for m in mon:
            sheet.paste(cell(m), (x, y)); x += T * S + 3
    p = os.path.join(ROOT, 'ITEM_SHEET_B_scale.png'); sheet.save(p); print(p)


if __name__ == '__main__':
    materials(); scale()
