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


def test_tin_maul_falls_back_to_a_maul_sprite():
    p = renderer._resolve_item_sprite_path('tin_maul')   # no tin_*.png exists
    assert p is not None, 'tin_maul should fall back to a base sprite, not a glyph'
    assert p.endswith('_maul.png') and os.path.exists(p)
    assert os.path.basename(p) != 'tin_maul.png'         # because none exists


def test_instantiate_tin_maul_has_expected_id():
    from items import instantiate_weapon
    w = instantiate_weapon('maul', 'tin')
    assert w.id == 'tin_maul'                            # the id the renderer resolves


def test_unknown_item_resolves_to_none():
    assert renderer._resolve_item_sprite_path('totally_not_an_item_zzz') is None
