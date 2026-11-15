"""The rare pets' art (2026-11-14): the Mooble and the Bococho.

Agent P3 drew every picture the two quests need on the high-fantasy pipeline
(briefs/rare_pets.json, installed by tools/content/genart/install_rare_pets.py).
The quest and pet code is built against these exact ids, so each must exist,
at 64 px, in its folder, and be listed in the registry the art-size test reads.
Whether the pictures look right is Brandon's look (RARE_PETS_ART_SHEET.png).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENART = os.path.join(ROOT, 'tools', 'content', 'genart')
sys.path.insert(0, GENART)

import install_rare_pets as inst  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

MONSTERS = ('npc_mooble', 'mooble', 'mooble_dancer', 'mooble_troupe_leader',
            'mooble_dance_left', 'mooble_dance_right', 'mooble_dance_up', 'mooble_dance_down',
            'npc_bococho_young', 'bococho_chick', 'bococho', 'bococho_champion',
            'bococho_saddled', 'bococho_champion_saddled', 'npc_varro_bococho', 'gilt_varro')
ITEMS = ('starnut', 'sunroot')
FIXTURES = ('race_tether_post', 'race_betting_board', 'race_finish_banner')
TILES = ('race_track_floor', 'race_track_rail')


def _json(name):
    with open(os.path.join(GENART, name), encoding='utf-8') as f:
        return json.load(f)


def _where(folder, sid):
    return os.path.join(ROOT, 'assets', 'tiles', *folder.split('/'), sid + '.png')


def test_every_id_exists_at_64_px_in_its_folder():
    for folder, ids in (('monsters', MONSTERS), ('items', ITEMS), ('env/fixtures', FIXTURES), ('env', TILES)):
        for sid in ids:
            path = _where(folder, sid)
            assert os.path.exists(path), path
            assert Image.open(path).size == (64, 64), (folder, sid)


def test_the_installer_covers_exactly_these_ids():
    assert set(inst.MONSTERS) == set(MONSTERS)
    assert set(inst.ITEMS) == set(ITEMS)
    assert set(inst.FIXTURES) == set(FIXTURES)
    assert set(inst.TILES) == set(TILES)
    for sid in MONSTERS + ITEMS + FIXTURES:
        if sid not in inst.DANCE + inst.BUILT:
            assert inst.PICKS.get(sid), sid


def test_every_id_is_registered_as_reviewed_64_px_art():
    """tests/test_art_pass.py sizes a picture by these registries."""
    rest = set(_json('installed_rest.json')['monsters'])
    mons = set(_json('installed.json'))
    for sid in MONSTERS:
        assert sid in rest or sid in mons, sid
    assert 'gilt_varro' in mons
    assert set(ITEMS) <= set(_json('installed_items.json')['items'])
    assert set(TILES) <= set(_json('installed_tiles.json')['env'])


def test_sprites_have_a_clear_background_and_tiles_are_opaque():
    for folder, ids in (('monsters', MONSTERS), ('items', ITEMS), ('env/fixtures', FIXTURES)):
        for sid in ids:
            im = Image.open(_where(folder, sid)).convert('RGBA')
            assert im.getpixel((0, 0))[3] == 0 and im.getpixel((63, 0))[3] == 0, (folder, sid)
            assert im.getbbox() is not None, (folder, sid)
    for sid in TILES:
        alpha = np.asarray(Image.open(_where('env', sid)).convert('RGBA'))[..., 3]
        assert alpha.min() == 255, sid


def test_the_rail_runs_edge_to_edge_so_a_row_of_them_is_one_fence():
    """The two rails meet the tile's left and right edges at the same rows (their
    dark outlines are on the same rows at both edges), so rail tiles laid side by
    side make one unbroken fence."""
    a = np.asarray(Image.open(_where('env', 'race_track_rail')).convert('RGB')).astype(int)
    dark = a.sum(-1) < 90
    left = [y for y in range(64) if dark[y, 0]]
    right = [y for y in range(64) if dark[y, 63]]
    assert len(left) >= 4 and left == right, (left, right)


def test_the_four_dance_poses_are_one_creature_at_one_scale():
    """The rhythm screen shows the four poses in turn: the Mooble's body is the
    same size in each (the cut sizes each window by his cream fur)."""
    fur = []
    for sid in inst.DANCE:
        a = np.asarray(Image.open(_where('monsters', sid)).convert('RGBA')).astype(int)
        mx, mn = a[..., :3].max(-1), a[..., :3].min(-1)
        fur.append(int(((a[..., 3] > 0) & (mx > 150) & ((mx - mn) < 0.38 * mx)).sum()))
    assert max(fur) <= 1.6 * min(fur), fur


def test_the_saddled_birds_name_their_seat():
    for sid in ('bococho_saddled', 'bococho_champion_saddled'):
        x, y = inst.SEAT[sid]
        assert 0 <= x < 64 and 0 <= y < 64
        im = Image.open(_where('monsters', sid)).convert('RGBA')
        assert im.getpixel((x, y))[3] == 255, (sid, x, y)
