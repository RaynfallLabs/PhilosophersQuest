"""
Draw a sprite for every monster in data/monsters.json that has none.

Offline tooling (not loaded at runtime).

    python tools/content/gen_missing_monster_sprites.py            # list what is missing
    python tools/content/gen_missing_monster_sprites.py --write    # draw them
    python tools/content/gen_missing_monster_sprites.py --write --all-listed   # redraw every one in BRIEFS

The drawing code is the project's original sprite generator
(tools/content/monster_sprite_gen.py, restored from the archive: it
reproduces the shipped sprites pixel for pixel). This file only supplies the
art brief for each monster that was added after the last art pass: its
silhouette, size and features. The palette comes from the monster's own
`color` in monsters.json, exactly as the original brief builder derived it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

OUT = ROOT / 'assets' / 'tiles' / 'monsters'

# id: (silhouette, size, features)
BRIEFS = {
    # --- the Abyss (floors 74-93) ---
    'locust_swarmlord':        ('insect_spider',    1.30, ['wings', 'crown']),
    'pit_executioner':         ('demon_winged',     1.25, ['horns', 'armor']),
    'void_seraph':             ('demon_winged',     1.25, ['wings', 'glow']),
    'apocalypse_herald':       ('demon_winged',     1.20, ['horns', 'wings', 'flames']),
    'wormwood_blight':         ('serpent_worm',     1.25, ['glow', 'tentacles']),
    'iron_horseman':           ('humanoid_large',   1.20, ['armor', 'skull']),
    'blood_archon':            ('demon_winged',     1.30, ['horns', 'wings', 'crown', 'glow']),
    'asmodeus':                ('demon_winged',     1.35, ['horns', 'wings', 'crown', 'staff', 'flames']),
    'astral_horror':           ('orb_floating',     1.30, ['tentacles', 'glow']),
    # --- orcs ---
    'orc_archer':              ('humanoid_medium',  0.95, []),
    'orc_priest':              ('humanoid_caster',  1.00, ['staff']),
    'orc_marauder':            ('humanoid_medium',  1.07, ['armor']),
    'orc_warbringer':          ('humanoid_large',   1.15, ['armor', 'horns']),
    'dread_orc_champion':      ('humanoid_large',   1.18, ['armor', 'horns', 'glow']),
    # --- goblins ---
    'goblin_sniper':           ('humanoid_small',   0.78, []),
    'goblin_warpriest':        ('humanoid_small',   0.85, ['staff']),
    'hobgoblin_marshal':       ('humanoid_medium',  1.05, ['armor', 'crown']),
    'goblin_kingslayer':       ('humanoid_small',   0.92, ['armor', 'glow']),
    # --- the restless dead ---
    'skeleton_necromancer':    ('lich_caster',      0.95, ['staff', 'skull']),
    'bone_collector':          ('undead_skeleton',  1.20, ['skull', 'armor']),
    'skeleton_lich':           ('lich_caster',      1.10, ['staff', 'skull', 'glow']),
    'banshee_lich':            ('undead_ghost',     1.15, ['crown', 'glow']),
    'ghast_eater':             ('undead_zombie',    1.00, []),
    'draugr_wight':            ('undead_zombie',    1.10, ['armor']),
    'grave_knight':            ('undead_skeleton',  1.20, ['armor', 'skull']),
    'crypt_summoner':          ('lich_caster',      1.05, ['staff', 'glow']),
    'whispering_crone':        ('undead_ghost',     1.25, ['staff', 'glow']),
    # --- kobolds and gnolls ---
    'kobold_trapsetter':       ('humanoid_small',   0.70, ['tail']),
    'kobold_dragonshield':     ('humanoid_small',   0.80, ['tail', 'armor']),
    'kobold_pack_leader':      ('humanoid_small',   0.88, ['tail', 'horns']),
    'gnoll_archer':            ('werewolf',         0.95, []),
    'gnoll_fang_of_yeenoghu':  ('werewolf',         1.07, ['armor']),
    'gnoll_alpha_of_yeenoghu': ('werewolf',         1.20, ['armor', 'crown']),
    # --- people ---
    'bandit_thug':             ('humanoid_medium',  1.02, []),
    'bandit_archer':           ('humanoid_medium',  0.95, []),
    'bandit_thief':            ('humanoid_medium',  0.90, []),
    'bandit_kingpin':          ('humanoid_medium',  1.10, ['armor', 'crown']),
    'cult_initiate':           ('humanoid_caster',  0.92, []),
    'cult_priest':             ('humanoid_caster',  1.00, ['staff']),
    'cult_zealot':             ('humanoid_medium',  1.02, ['flames']),
    'cult_hierophant':         ('humanoid_caster',  1.12, ['staff', 'crown', 'glow']),
    'snake_charmer':           ('humanoid_caster',  0.97, ['staff']),
    'viper_priestess':         ('humanoid_caster',  1.02, ['staff', 'tail']),
    'harrow_witch':            ('humanoid_caster',  0.97, ['staff']),
    'plague_witch':            ('humanoid_caster',  1.00, ['staff', 'glow']),
    'mage_slayer_assassin':    ('humanoid_medium',  0.97, []),
    'shadow_archer':           ('humanoid_medium',  0.99, ['glow']),
    'veiled_inquisitor':       ('humanoid_caster',  1.07, ['staff', 'flames']),
    'iron_patriarch':          ('humanoid_large',   1.20, ['armor', 'crown']),
    'deep_one_priest':         ('humanoid_caster',  1.05, ['staff', 'tentacles']),
    # --- imps and tricksters ---
    'greater_imp':             ('demon_winged',     0.75, ['horns', 'wings', 'tail']),
    'demonic_imp':             ('demon_winged',     0.85, ['horns', 'wings', 'tail', 'flames']),
    'imp_lord':                ('demon_winged',     0.95, ['horns', 'wings', 'tail', 'crown']),
    'demonic_trickster':       ('demon_winged',     1.00, ['horns', 'tail', 'glow']),
    # --- big things ---
    'cave_troll':              ('troll',            1.20, []),
    'ettin_warchief':          ('troll',            1.30, ['multi_head', 'armor']),
    'frostfang_giant':         ('humanoid_large',   1.30, ['ice', 'armor']),
    'stone_golem':             ('construct_golem',  1.20, []),
    'throne_sentinel':         ('construct_golem',  1.25, ['armor', 'crown']),
    'moss_sentinel':           ('construct_golem',  1.15, []),
    'vine_horror':             ('plant_creature',   1.15, ['tentacles']),
    'lurking_horror':          ('blob_ooze',        1.15, ['tentacles']),
    'gilded_mimic':            ('blob_ooze',        1.10, ['crown', 'glow']),
    'sable_serpent':           ('serpent_snake',    1.05, []),
    'lava_elemental':          ('elemental_fire',   1.25, ['flames']),
    # --- legends ---
    'tiamat':                  ('dragon_large',     1.55, ['horns', 'tail', 'wings', 'multi_head']),
    'surtur':                  ('humanoid_large',   1.35, ['flames', 'crown', 'horns']),
    'ymir_last_spawn':         ('humanoid_large',   1.35, ['ice', 'crown']),
    'hrungnirs_ghost':         ('construct_golem',  1.35, ['skull', 'glow']),
    # --- beasts ---
    'bonnacon':                ('quadruped_large',  1.00, ['horns', 'tail']),
    'calydonian_boar':         ('quadruped_large',  1.15, ['horns']),
}


def derive_palette(color) -> dict:
    """The original brief builder's palette rule (gen_monster_art_brief.py)."""
    c = [int(x) for x in color[:3]]
    lighten = lambda f: [min(255, int(x * f)) for x in c]       # noqa: E731
    mx, mn = max(c), min(c)
    sat = c if mx == mn else [min(255, int(x * 1.3)) if x == mx else max(0, int(x * 0.7)) for x in c]
    return {
        'primary':   c,
        'secondary': lighten(1.3),
        'dark':      [max(0, int(x * 0.4)) for x in c],
        'highlight': lighten(1.7),
        'saturated': sat,
    }


def missing() -> list[str]:
    with open(ROOT / 'data' / 'monsters.json', encoding='utf-8') as f:
        mons = json.load(f)
    return [k for k, v in mons.items()
            if isinstance(v, dict) and not (OUT / f'{k}.png').exists()]


def render(mid: str, color) -> 'object':
    import monster_sprite_gen as g
    from PIL import ImageDraw
    sil, size, feats = BRIEFS[mid]
    pal = derive_palette(color)
    img = g.new_canvas()
    d = ImageDraw.Draw(img, 'RGBA')
    P, L, D, H = (g.C(pal[k]) for k in ('primary', 'secondary', 'dark', 'highlight'))
    feats = set(feats)
    fn = g.DRAW_FN.get(sil, g.draw_humanoid)
    if 'glow' in feats and sil != 'undead_ghost':
        g.add_glow_aura(img, g.S // 2, g.S // 2, int(14 * size), P)
    if sil == 'undead_ghost':
        fn(d, P, L, D, H, feats, size=size, img=img)
    else:
        fn(d, P, L, D, H, feats, size=size)
    g.apply_highlight(img)
    return img


def main(argv: list[str]) -> int:
    with open(ROOT / 'data' / 'monsters.json', encoding='utf-8') as f:
        mons = json.load(f)
    todo = sorted(BRIEFS) if '--all-listed' in argv else missing()
    no_brief = [m for m in todo if m not in BRIEFS]
    print(f'{len(todo)} monsters to draw; {len(no_brief)} have no brief: {no_brief}')
    if '--write' not in argv:
        return 1 if no_brief else 0
    n = 0
    for mid in todo:
        if mid not in BRIEFS or mid not in mons:
            continue
        render(mid, mons[mid].get('color') or [160, 160, 160]).save(OUT / f'{mid}.png')
        n += 1
    print(f'wrote {n} sprites to {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
