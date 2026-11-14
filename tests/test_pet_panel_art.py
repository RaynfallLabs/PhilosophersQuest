"""Round 3, Q16 (2026-11-14): the pet panel shows the pet.

Brandon: "pet panel should show the pet, just like bestiary and item lore".
The Shift+P card is headed by the companion's CURRENT picture, drawn the
way the lore pages draw theirs (lore_art.plate in the framed well,
``_draw_plate_well``): the stage it has grown to, and for the Emberpup in
the Bloomleaf Cloak the cloaked picture of every stage. The map and the
card agree on that picture (lore_art.pet_ref). A pet with no art has no
picture at all, never a letter glyph. Shep's long card fits at 1280x720.

The panel is opened with the real key (Shift+P) on a headless Game at the
smallest window with the UI kit the game ships. Whether it looks right is
Brandon's look (the captures: tools/ui/capture.py --only menu_pet).
"""
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import lore_art  # noqa: E402
import pet_system  # noqa: E402
from pet_system import Pet  # noqa: E402

SMALL = (1280, 720)
STAGE_LEVELS = (1, pet_system._EVOLVE_1, pet_system._EVOLVE_2)


# ---------------------------------------------------------------- the picture's id

def test_pet_ref_is_the_stage_it_has_grown_to():
    assert lore_art.pet_ref(Pet('plant', 0, 0)) == ('monster', 'seedling')
    assert lore_art.pet_ref(Pet('plant', 0, 0, level=pet_system._EVOLVE_1)) == \
        ('monster', 'thornback')
    assert lore_art.pet_ref(Pet('water', 0, 0, level=pet_system._EVOLVE_2)) == \
        ('monster', 'torrentoise')
    assert lore_art.pet_ref(None) is None


def test_the_cloaked_emberpup_wears_the_cloak_at_every_stage():
    for level, stage in zip(STAGE_LEVELS, ('emberpup', 'flamescale', 'infernodrake')):
        pup = Pet('fire', 0, 0, level=level)
        assert lore_art.pet_ref(pup) == ('monster', stage)
        pup.bloomleaf = True
        assert lore_art.pet_ref(pup) == ('monster', f'{stage}_cloaked')
        assert lore_art.art_path('monster', f'{stage}_cloaked') is not None


def test_a_drawing_shows_the_creature_it_was_drawn_from():
    sketch = types.SimpleNamespace(is_sketch=True, monster_kind='goblin', sprite_id='')
    assert lore_art.pet_ref(sketch) == ('monster', 'goblin')


def test_every_stage_of_every_pet_line_has_its_picture():
    missing = []
    for species in pet_system._SPECIES:
        for level in STAGE_LEVELS:
            try:
                pet = Pet(species, 0, 0, level=level)
            except Exception as e:                 # pragma: no cover - a broken line
                missing.append((species, level, repr(e)))
                continue
            ref = lore_art.pet_ref(pet)
            if ref is None or lore_art.art_path(*ref) is None:
                missing.append((species, level, ref))
    assert not missing, missing


# ---------------------------------------------------------------- the panel

@pytest.fixture
def kit_game():
    import layout
    import ui_theme
    from main import Game
    from game_states import STATE_PLAYER
    saved = ui_theme.save_state()
    try:
        ui_theme.load()
        lore_art.clear_cache()
        screen = pygame.display.set_mode(SMALL)
        layout.update(*SMALL)
        g = Game(screen, player_name='__test_pet_panel__')
        g.on_resize(*SMALL)
        g._resize_grace = 0
        g.monsters = []
        g.state = STATE_PLAYER
        yield g
    finally:
        ui_theme.restore_state(saved)
        lore_art.clear_cache()


def _beside(g):
    """A walkable tile beside the hero."""
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        x, y = px + dx, py + dy
        if g.dungeon.is_walkable(x, y):
            return x, y
    raise AssertionError('no free tile beside the hero')


def _open_panel(g, pet, monkeypatch):
    """Shift+P with ``pet`` the only companion; returns what was drawn:
    the plates put in a well, and every text line of the panel."""
    x, y = _beside(g)
    pet.x, pet.y = x, y
    g.pets[:] = [pet]
    wells, texts = [], []
    real_well = g._draw_plate_well
    monkeypatch.setattr(g, '_draw_plate_well',
                        lambda surf, well, top_rule=True: (wells.append(surf),
                                                           real_well(surf, well, top_rule))[1])
    real_fit = g._menu_fit_block

    def fit(lines, *a, **k):
        # What a pane really draws: its lines as fitted (a cut card ends
        # with the "more" cue).
        out = real_fit(lines, *a, **k)
        for ln in out:
            if isinstance(ln, tuple) and ln:
                texts.append(ln[2] if ln[0] == '__key__' else ln[0])
        return out
    monkeypatch.setattr(g, '_menu_fit_block', fit)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, unicode='P',
                                      mod=pygame.KMOD_SHIFT, scancode=0))
    from game_states import STATE_PET_MENU
    assert g.state == STATE_PET_MENU
    g.render()
    return wells, texts


@pytest.mark.parametrize('species,level,nick,cloak', [
    ('plant', 1, '', False),                                  # just hatched
    ('electric', pet_system._EVOLVE_1, 'Sparky', False),      # evolved once
    ('water', pet_system._EVOLVE_2, 'Bubbles', False),        # the last stage
    ('fire', 1, 'Ember', True),                               # the cloaked Emberpup
    ('fire', pet_system._EVOLVE_1, 'Ember', True),            # ... grown, still cloaked
    ('fire', pet_system._EVOLVE_2, 'Ember', True),
])
def test_the_panel_shows_the_pets_current_picture(kit_game, monkeypatch, species, level,
                                                  nick, cloak):
    pet = Pet(species, 0, 0, level=level)
    pet.nickname = nick
    pet.bloomleaf = cloak
    wells, texts = _open_panel(kit_game, pet, monkeypatch)
    kind, sid = lore_art.pet_ref(pet)
    if cloak:
        assert sid.endswith('_cloaked')
    plates = lore_art.cached(kind, sid)
    assert plates, f'no picture of {sid} was made'
    assert len(wells) == 1 and wells[0] in plates
    # Whole-number enlargement of the 64 px art, like the lore pages.
    assert wells[0].get_width() % 64 == 0 and wells[0].get_width() >= 64
    assert pet.name in texts and f'Level {pet.level}' in texts
    if cloak:
        import emberpup_encounter as ep
        assert ep.data()['pet_wears_cloak'] in texts


def test_the_map_and_the_panel_show_the_same_picture(kit_game, monkeypatch):
    g = kit_game
    pet = Pet('fire', 0, 0, level=pet_system._EVOLVE_1)
    pet.bloomleaf = True
    pet.x, pet.y = _beside(g)
    g.pets[:] = [pet]
    g._refresh_fov()
    mids = []
    real = g.renderer.draw_entity

    def spy(x, y, *a, **k):
        if (x, y) == (pet.x, pet.y):
            mids.append(k.get('mid'))
        return real(x, y, *a, **k)
    monkeypatch.setattr(g.renderer, 'draw_entity', spy)
    g.render()
    assert mids == [lore_art.pet_ref(pet)[1]] == ['flamescale_cloaked']


def test_a_pet_with_no_art_has_no_picture_and_no_glyph(kit_game, monkeypatch):
    pet = Pet('plant', 0, 0)
    pet.sprite_id = 'no_such_picture'
    wells, texts = _open_panel(kit_game, pet, monkeypatch)
    assert wells == []
    assert lore_art.cached('monster', 'no_such_picture') == []
    assert pet.name in texts and 'Command: Return' in texts
    assert pet.symbol not in texts


def test_sheps_whole_card_fits_at_the_smallest_window(kit_game, monkeypatch):
    shep = Pet('shep', 0, 0, level=pet_system._EVOLVE_2)
    shep.hatch_sphere = 'master_hearth_sphere'
    wells, texts = _open_panel(kit_game, shep, monkeypatch)
    assert len(wells) == 1
    assert "More in the item's dossier." not in texts
    assert any(t.startswith('He Always Comes') for t in texts)
    assert any(t.startswith('He growls') for t in texts)
    for action in ('Feed', 'Pet', 'Heal', 'Recall', 'Cycle command', 'Specials'):
        assert any(t.startswith(action) for t in texts), action
