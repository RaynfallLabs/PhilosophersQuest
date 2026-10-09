"""Item sprite resolution + material fallback (2026-06-06).

A weapon is instanced as "<material>_<template>" (e.g. "tin_maul"). Most combos
ship their own art, but some legitimate materials (tin) never got sprites, so
those weapons rendered as a bare "(" glyph instead of an icon.
_resolve_item_sprite_path now falls back to a representative same-base sprite.
Pure filesystem logic -> testable without a display.
"""
import os

import renderer


def test_existing_material_sprite_resolves_directly():
    p = renderer._resolve_item_sprite_path('iron_maul')
    assert p and p.endswith('iron_maul.png') and os.path.exists(p)


def test_tin_maul_has_a_picture_of_its_own_now():
    """Every material x template pair is drawn (2026-10-09); tin gear used to
    borrow another material's picture."""
    p = renderer._resolve_item_sprite_path('tin_maul')
    assert p is not None and os.path.basename(p) == 'tin_maul.png' and os.path.exists(p)


def test_a_material_item_without_art_still_falls_back_to_its_base():
    """The fallback remains for anything added before its art is drawn."""
    import renderer as r
    mats = r._material_ids()
    assert mats
    saved = list(mats)
    try:
        mats.append('zzmadeup')
        p = r._resolve_item_sprite_path('zzmadeup_maul')
    finally:
        mats[:] = saved
    assert p is not None and p.endswith('_maul.png') and os.path.exists(p)


def test_instantiate_tin_maul_has_expected_id():
    from items import instantiate_weapon
    w = instantiate_weapon('maul', 'tin')
    assert w.id == 'tin_maul'                            # the id the renderer resolves


def test_unknown_item_resolves_to_none():
    assert renderer._resolve_item_sprite_path('totally_not_an_item_zzz') is None
