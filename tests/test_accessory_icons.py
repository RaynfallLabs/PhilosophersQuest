"""Every ring/amulet must show a sprite icon, never a bare glyph (2026-06-07).

The one-cosmetic appearance merge renamed the common accessories to a canonical
"<cat>_of_<effect>" id (ring_of_searching, amulet_of_searching, ...), but their
art is still filed under the OLD per-variant names (ring_searching_silver.png).
draw_item() resolves a sprite from item.id, so the 42 renamed commons fell
through to the '=' / '"' glyph -- the "Opal Ring appears as =" regression.

renderer._resolve_item_sprite_path now maps a collapsed ring_*/amulet_* id to a
representative same-effect sprite (and, for an art-less unique, a neutral band).
These tests pin that EVERY accessory id renders an icon, and that items which
already had their own art are NOT hijacked by the fallback.
"""
import json
import os
from pathlib import Path

from renderer import _resolve_item_sprite_path

_ACC = Path(__file__).resolve().parents[1] / 'data' / 'items' / 'accessory.json'


def _ids():
    return list(json.loads(_ACC.read_text(encoding='utf-8')).keys())


def test_every_ring_or_amulet_resolves_to_a_real_sprite():
    misses = []
    for item_id in _ids():
        if not item_id.startswith(('ring_', 'amulet_')):
            continue              # non-jewellery uniques (hand_of_glory) excluded
        p = _resolve_item_sprite_path(item_id)
        if not (p and os.path.exists(p)):
            misses.append(item_id)
    assert not misses, f"ring/amulet ids with no icon (would glyph as =/\"): {misses}"


def test_renamed_commons_map_to_their_effect_art():
    # the exact ids the user sees as random unidentified rings this session
    cases = {
        'ring_of_searching':    'searching',
        'ring_of_strength':     'strength',
        'ring_of_fire_resist':  'fire_res',
        'ring_of_regeneration': 'regen',
        'amulet_of_searching':  'searching',
        'amulet_of_telepathy':  'telepathy',
    }
    for item_id, token in cases.items():
        p = _resolve_item_sprite_path(item_id)
        assert p and token in os.path.basename(p), f"{item_id} -> {p} (want '{token}')"


def test_power_tiers_share_the_base_stat_icon():
    # greater_/master_ tiers have no art of their own; they reuse the stat sprite
    for tier in ('ring_of_strength', 'ring_of_greater_strength', 'ring_of_master_strength'):
        p = _resolve_item_sprite_path(tier)
        assert p and 'strength' in os.path.basename(p), f"{tier} -> {p}"


def test_existing_art_is_not_hijacked_by_the_fallback():
    # ids that ship their OWN <id>.png must resolve to exactly that file
    for item_id in ('ring_invisible', 'ring_hasted', 'amulet_of_fortitude',
                    'amulet_of_merlin'):
        p = _resolve_item_sprite_path(item_id)
        assert p and os.path.basename(p) == f"{item_id}.png", f"{item_id} -> {p}"


def test_artless_unique_ring_falls_back_to_a_band_not_a_glyph():
    # uniques that never got art (ring_of_solomons_authority, amulet_of_hippolyta)
    # still get a neutral same-category icon instead of the '=' glyph
    for item_id in ('ring_of_solomons_authority', 'amulet_of_hippolyta'):
        p = _resolve_item_sprite_path(item_id)
        cat = item_id.split('_', 1)[0]
        assert p and os.path.basename(p).startswith(cat + '_'), f"{item_id} -> {p}"
