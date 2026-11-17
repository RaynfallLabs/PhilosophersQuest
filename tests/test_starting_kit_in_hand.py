"""The hero starts armed (Brandon's rulings, 2026-11-16).

UI-1: the plain hero's iron shortsword started in the pack, so a new
player's first fight was barehanded unless he knew to wield. Every
starting weapon is now in the hand: a bow in the ranged slot (where the
game fires it from), a melee weapon in the hand, and a second melee weapon
that finds the hand full (Musashi's shortsword) At Your Back in the pack.

Achilles: his spear was two-handed, so his own starting shield could never
go on with it. In the Iliad he fights with the Pelian ash in one hand and
the shield Hephaestus made on his arm, so the spear is one-handed.

Fianna starts with the Magic Dart spellbook, as Fluffs (her nickname build)
does; Fluffs stays a little better by her stats.

Headless Game tests: how this feels in play is a play-test question.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

from welcome_screen import SECRET_BUILDS  # noqa: E402


def _game(name='__test_start_in_hand__', build=None):
    from main import Game
    return Game(pygame.display.set_mode((1, 1)), player_name=name,
                secret_build=build)


def _ammo_weapon(w):
    return w is not None and getattr(w, 'requires_ammo', None) is not None


def test_the_plain_hero_holds_his_iron_shortsword():
    g = _game()
    p = g.player
    assert p.weapon is not None and p.weapon.id == 'iron_shortsword'
    assert not any(i is p.weapon for i in p.inventory)
    assert getattr(p.weapon, 'id_level', 0) == 5       # his own kit: known
    # Exactly one shortsword: it was not also left in the pack.
    assert sum(1 for i in p.inventory if getattr(i, 'id', '') == 'iron_shortsword') == 0


@pytest.mark.parametrize('key', sorted(SECRET_BUILDS))
def test_every_build_holds_what_it_starts_with(key):
    """No build's own weapon is left in the pack unwielded: a bow is in the
    ranged slot, a melee weapon in the hand, and a second melee weapon is At
    Your Back."""
    b = SECRET_BUILDS[key]
    if b.get('_qa_tools'):
        pytest.skip('QA build')
    g = _game(name=key, build=b)
    p = g.player
    from items import Weapon
    packed = [i for i in p.inventory if isinstance(i, Weapon)]
    for w in packed:
        # The only weapon left in the pack is a second melee weapon, readied.
        assert not _ammo_weapon(w), (key, w.id)
        assert p.weapon is not None, (key, w.id)
        assert p.readied_weapon is w, (key, w.id)
    if b.get('_start_weapon') or not b.get('_no_dagger'):
        assert p.weapon is not None or p.ranged_weapon is not None, key


def test_a_ranger_has_his_bow_in_its_slot_and_his_sword_in_hand():
    for key in ('corwin', 'cain'):
        g = _game(name=key, build=SECRET_BUILDS[key])
        p = g.player
        assert _ammo_weapon(p.ranged_weapon) and 'shortbow' in p.ranged_weapon.id, key
        assert p.weapon is not None and p.weapon.id == 'iron_shortsword', key


def test_a_bow_only_hero_has_the_bow_in_its_slot():
    for key in ('robyn', 'odysseus of ithaca'):
        g = _game(name=key, build=SECRET_BUILDS[key])
        assert _ammo_weapon(g.player.ranged_weapon), key


def test_musashi_holds_the_long_sword_with_the_short_at_his_back():
    key = 'miyamoto musashi the sword saint'
    g = _game(name=key, build=SECRET_BUILDS[key])
    p = g.player
    assert p.weapon.id == 'iron_longsword'
    assert p.readied_weapon is not None and p.readied_weapon.id == 'iron_shortsword'


def test_ash_williams_has_the_boomstick_in_its_slot_and_the_chainsaw_on():
    g = _game(name='ash williams', build=SECRET_BUILDS['ash williams'])
    p = g.player
    assert p.ranged_weapon is not None and p.ranged_weapon.id == 'boomstick'
    assert p.weapon is not None and p.weapon.id == 'chainsaw_prosthetic'


def test_achilles_spear_takes_one_hand_by_the_iliad():
    import items
    spear = next(i for i in items.load_items('weapon') if i.id == 'achilles_spear')
    assert spear.two_handed is False
    key = 'achilles son of peleus'
    g = _game(name=key, build=SECRET_BUILDS[key])
    p = g.player
    assert p.weapon is not None and p.weapon.id == 'achilles_spear'
    assert p.can_equip_shield()                 # his kit works together
    sh = next(i for i in p.inventory if type(i).__name__ == 'Shield')
    p._apply_equip(sh)
    assert p.shield is sh and p.weapon.id == 'achilles_spear'


def test_fianna_starts_with_magic_dart_and_fluffs_is_still_a_little_better():
    fianna, fluffs = SECRET_BUILDS['fianna'], SECRET_BUILDS['fluffs']
    assert fianna['_start_book'] == 'spellbook_magic_dart' == fluffs['_start_book']
    g = _game(name='fianna', build=fianna)
    assert any(getattr(i, 'id', '') == 'spellbook_magic_dart' for i in g.player.inventory)
    stats = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
    assert all(fluffs[s] >= fianna[s] for s in stats)
    assert sum(fluffs[s] for s in stats) > sum(fianna[s] for s in stats)
