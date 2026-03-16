"""
Generate 32x32 pixel-art player sprites for each secret character build.
Run from the project root: python data/gen_player_sprites.py
"""
import os
import pygame

pygame.init()
SIZE    = 32
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tiles', 'env')


# ---------------------------------------------------------------------------
# Primitive drawing helpers
# ---------------------------------------------------------------------------

def _rect(surf, col, x, y, w, h):
    if col and len(col) == 4:
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        tmp.fill(col)
        surf.blit(tmp, (x, y))
    elif col:
        pygame.draw.rect(surf, col, (x, y, w, h))

def _px(surf, col, x, y):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        surf.set_at((x, y), col)


# ---------------------------------------------------------------------------
# Character template
# ---------------------------------------------------------------------------

def draw_character(
    skin      = (220, 180, 140),
    hair      = (80, 60, 40),
    robe      = (120, 100, 200),
    robe2     = None,            # second colour (belt/cloak/stripes)
    legs      = (70, 70, 90),
    boots     = (60, 45, 30),
    helmet    = None,            # colour → draw helmet
    plume     = None,            # colour → feather on helmet
    has_beard = False,
    bald      = False,
    has_hood  = False,
    has_staff = False,
    has_bow   = False,
    has_wings = False,           # hermes winged hat
    crown     = None,            # colour → crown
    sash      = None,            # diagonal accent strip
    star_robe = False,           # sparkles on robe
    eye_col   = (40, 30, 20),
    cape      = None,            # colour → cape behind torso
):
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    # ── Cape (behind body) ──────────────────────────────────────────────────
    if cape:
        _rect(surf, cape, 9, 11, 14, 14)

    # ── Head ────────────────────────────────────────────────────────────────
    hx, hy = 12, 3
    if bald:
        _rect(surf, skin, hx, hy, 8, 8)
        _rect(surf, hair, hx, hy,  8, 2)  # subtle fringe/shadow on top
    elif has_hood:
        _rect(surf, hair, hx - 1, hy - 1, 10, 3)   # hood top
        _rect(surf, hair, hx - 1, hy,     2, 7)    # hood left
        _rect(surf, hair, hx + 7, hy,     2, 7)    # hood right
        _rect(surf, skin, hx, hy + 1, 8, 7)        # face inside hood
    else:
        _rect(surf, skin, hx, hy, 8, 8)
        _rect(surf, hair, hx, hy, 8, 3)            # hair on top
        if not helmet:
            _rect(surf, hair, hx, hy + 3, 2, 4)    # side burn left

    # Beard
    if has_beard:
        _rect(surf, hair, hx, hy + 5, 8, 4)

    # Eyes
    _px(surf, eye_col, hx + 2, hy + 4)
    _px(surf, eye_col, hx + 5, hy + 4)

    # Helmet (over hair)
    if helmet:
        _rect(surf, helmet, hx - 1, hy - 2, 10, 5)
        if plume:
            _rect(surf, plume, hx + 2, hy - 6, 4, 5)  # plume feathers
            _px(surf, plume, hx + 3, hy - 7)

    # Crown
    if crown:
        _px(surf, crown, hx + 1, hy - 1)
        _px(surf, crown, hx + 3, hy - 2)
        _px(surf, crown, hx + 5, hy - 1)
        _rect(surf, crown, hx, hy - 1, 8, 1)

    # Winged hat elements
    if has_wings:
        _rect(surf, (200, 200, 220), hx - 4, hy + 1, 4, 3)
        _rect(surf, (200, 200, 220), hx + 8, hy + 1, 4, 3)

    # ── Body ────────────────────────────────────────────────────────────────
    bx, by = 11, 11
    _rect(surf, robe, bx, by, 10, 8)

    # Second robe colour belt/trim
    if robe2:
        _rect(surf, robe2, bx, by + 6, 10, 2)

    # Sash
    if sash:
        for i in range(8):
            _px(surf, sash, bx + i, by + i // 2)

    # Star robe sparkles
    if star_robe:
        sparkle = (255, 240, 120)
        for sx, sy in [(bx+1, by+1), (bx+7, by+2), (bx+3, by+5), (bx+8, by+6)]:
            _px(surf, sparkle, sx, sy)

    # Arms
    _rect(surf, robe, bx - 3, by + 1, 3, 6)   # left arm
    _rect(surf, robe, bx + 10, by + 1, 3, 6)  # right arm
    _rect(surf, skin, bx - 3, by + 5, 3, 2)   # left hand
    _rect(surf, skin, bx + 10, by + 5, 3, 2)  # right hand

    # ── Legs ────────────────────────────────────────────────────────────────
    lx, ly = 12, 19
    _rect(surf, legs, lx, ly, 4, 7)
    _rect(surf, legs, lx + 4, ly, 4, 7)

    # Boots
    _rect(surf, boots, lx - 1, ly + 5, 5, 3)
    _rect(surf, boots, lx + 4, ly + 5, 5, 3)

    # ── Staff ───────────────────────────────────────────────────────────────
    if has_staff:
        _rect(surf, (120, 85, 40), bx + 13, 1, 2, 30)
        _rect(surf, (180, 150, 60), bx + 12, 0, 4, 3)   # gem top

    # ── Bow ─────────────────────────────────────────────────────────────────
    if has_bow:
        bow_x = bx + 13
        bow_col = (110, 75, 30)
        for dy in range(22):
            off = int(3 * abs(dy / 11.0 - 1.0))
            _px(surf, bow_col, bow_x + off, dy + 1)
            _px(surf, bow_col, bow_x - off, dy + 1)
        # bowstring
        string_col = (200, 190, 160)
        for dy in range(22):
            _px(surf, string_col, bow_x, dy + 1)

    return surf


# ---------------------------------------------------------------------------
# Character definitions
# ---------------------------------------------------------------------------

CHARS = {
    # ── Philosophers ────────────────────────────────────────────────────────
    "player_aristotle": dict(
        skin=(210,175,130), hair=(200,195,185), robe=(70,100,160),
        robe2=(50,75,120), legs=(55,70,110), has_beard=True,
    ),
    "player_socrates": dict(
        skin=(205,170,125), hair=(190,185,175), robe=(230,225,210),
        robe2=(180,170,140), legs=(160,155,145), bald=True, has_beard=True,
    ),
    "player_plato": dict(
        skin=(215,178,135), hair=(160,150,140), robe=(130,80,160),
        robe2=(100,60,130), legs=(90,60,110), has_beard=True,
    ),
    "player_nietzsche": dict(
        skin=(210,175,135), hair=(60,45,35), robe=(40,40,45),
        robe2=(80,70,60), legs=(35,35,40), eye_col=(50,40,30),
        has_beard=False,   # Nietzsche had a massive mustache not a beard
    ),
    "player_pythagoras": dict(
        skin=(215,180,135), hair=(90,70,50), robe=(60,130,90),
        robe2=(40,100,65), legs=(50,100,70), has_beard=True,
    ),
    "player_theseus": dict(
        skin=(200,165,120), hair=(80,60,40), robe=(180,150,60),
        robe2=(140,110,40), legs=(100,80,50),
        helmet=(160,140,60), plume=(200,50,50),
    ),
    "player_prometheus": dict(
        skin=(205,170,125), hair=(200,130,30), robe=(200,100,30),
        robe2=(180,60,20), legs=(150,70,30), sash=(255,180,50),
        star_robe=True,
    ),
    "player_diogenes": dict(
        skin=(195,160,115), hair=(130,110,90), robe=(120,95,65),
        robe2=(90,70,45), legs=(100,80,55), boots=(90,70,45),
        bald=True,
    ),
    # ── Warriors ────────────────────────────────────────────────────────────
    "player_achilles": dict(
        skin=(200,165,120), hair=(200,170,60), robe=(200,170,60),
        robe2=(160,130,40), legs=(180,145,50), boots=(80,60,35),
        helmet=(200,170,60), plume=(220,50,50),
    ),
    "player_leonidas": dict(
        skin=(195,160,115), hair=(60,45,30), robe=(160,120,50),
        robe2=(140,100,40), legs=(140,100,40), boots=(70,50,30),
        helmet=(160,125,50), plume=(190,40,40), cape=(160,30,30),
    ),
    "player_alexander": dict(
        skin=(210,178,135), hair=(200,180,100), robe=(130,50,160),
        robe2=(100,30,120), legs=(110,45,130), boots=(80,60,35),
        helmet=(200,170,60), crown=(220,200,60), cape=(130,50,160),
    ),
    # ── Rogues ──────────────────────────────────────────────────────────────
    "player_hermes": dict(
        skin=(205,175,130), hair=(200,200,220), robe=(160,175,210),
        robe2=(130,145,180), legs=(120,135,165), has_wings=True,
        boots=(160,175,210),
    ),
    "player_odysseus": dict(
        skin=(195,160,115), hair=(60,50,40), robe=(100,80,55),
        robe2=(80,60,40), legs=(75,60,40), has_hood=True,
        boots=(60,45,30),
    ),
    # ── Mages ───────────────────────────────────────────────────────────────
    "player_merlin": dict(
        skin=(210,180,140), hair=(210,205,200), robe=(25,30,90),
        robe2=(20,25,70), legs=(20,25,70), has_beard=True,
        bald=False, star_robe=True, has_staff=True,
    ),
    # ── Balanced ────────────────────────────────────────────────────────────
    "player_diogenes_already_done": None,   # skip duplicate key guard
    # ── New characters ───────────────────────────────────────────────────────
    "player_ranger": dict(   # Corwin
        skin=(195,160,115), hair=(110,70,40), robe=(65,115,60),
        robe2=(50,90,45), legs=(70,55,35), has_bow=True,
        boots=(70,50,30),
    ),
    "player_wizard_f": dict(   # Fianna / Fluffs
        skin=(220,185,150), hair=(220,200,130), robe=(130,60,180),
        robe2=(100,40,140), legs=(100,45,135), has_staff=True,
        boots=(90,60,120),
    ),
    "player_dad": dict(
        skin=(210,175,130), hair=(100,80,55), robe=(70,130,200),   # blue polo
        robe2=(200,185,130), legs=(160,145,100), boots=(80,65,45), # khaki
        eye_col=(50,40,30),
    ),
    "player_robyn": dict(   # Robyn — literature rogue / druid archer
        skin=(220,185,155), hair=(220,190,80),
        robe=(60,130,70), robe2=(80,160,90),
        legs=(50,90,55), boots=(65,45,30),
        has_bow=True, eye_col=(60,100,60),
    ),
}

# Remove placeholder
CHARS.pop("player_diogenes_already_done", None)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    saved = []
    for name, kwargs in CHARS.items():
        if kwargs is None:
            continue
        surf = draw_character(**kwargs)
        path = os.path.join(OUT_DIR, f"{name}.png")
        pygame.image.save(surf, path)
        saved.append(name)
        print(f"  saved {name}.png")
    print(f"\n{len(saved)} sprites written to {OUT_DIR}")


if __name__ == "__main__":
    main()
    pygame.quit()
