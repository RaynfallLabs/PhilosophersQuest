"""Every item, identified, says what it does, on the Kit card and in the
dossier's Mechanics pane (3.6.1, 2026-11-22).

Brandon, play-testing: "Same problem with spells and scrolls with rings...
Ring of Wizardry gets identified, has nothing useful in mechanics, and no
idea what it actually does; assume this problem persists across many items."
A census found 37 of 41 artifacts saying "No revealed mechanics recorded.",
the dossier never showing a ring's power, named pieces whose power lives
only in code (Draupnir's gold, the Jade Cicada's saved life), "Resists:
slash 80%" for a piece that takes 80% of a cut, and chain tiers named by
their code keys ("Stealth In Dark").

Both cards read one list (RenderMixin._item_power_lines); a kind's own lines
are data (data/ui/item_powers.json, src/item_powers.py).
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_G = None

# A line a player should never read: a code name, an empty value, a doubled
# enchantment name, an unfilled placeholder.
_CODE = re.compile(r"_|\bNone\b|Random Stat|Resists: -|Greater the\b|[{}]|"
                   r"\b([A-Z][\w' ]+ [IVX]+): \1\b")

# Item classes and the fields that are a power when set (Accessory.__init__,
# src/items.py): each needs a written line that covers it.
POWER_FIELDS = {
    'accessory': ('gold_multiplier', 'pacify_chance', 'death_save', 'resurrect_on_death',
                  'passive_regen', 'use_charged', 'passive_dark_vision', 'passive_silent_walk',
                  'tears_of_freya', 'identify_tier_reduction', 'auto_invisible_at_low_hp',
                  'protected_when_surrounded', 'gyges_invisible_attack_karma',
                  'monster_tag_chain_bonus', 'attack_chain_cap_bonus', 'quiz_timer_bonus',
                  'bound_to_wielder', 'calms_locusts', 'save_bonus'),
}


# A power field no code can bring into play, reported to Brandon (3.6.1,
# 2026-11-22) and left unwritten rather than promised on a card.
KNOWN_DEAD = {
    'accessory:ring_of_eluned.auto_invisible_at_low_hp':
        'the ring lends Invisible for as long as it is worn, so the low-health veil never comes',
}


def _game():
    global _G
    from main import Game
    if _G is None:
        random.seed(3)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_every_item_says__')
        _G._autosave = lambda *a, **k: None
    return _G


def _every_item():
    from items import load_items, _CLASS_MAP
    out = []
    for cls in _CLASS_MAP:
        for it in load_items(cls):
            it.id_level = 5
            out.append((cls, it))
    return out


_ITEMS = None


def _items():
    global _ITEMS
    if _ITEMS is None:
        _ITEMS = _every_item()
    return _ITEMS


def _text(lines):
    return [str(t) for t, *_ in lines]


def test_every_identified_item_says_what_it_does():
    g = _game()
    silent = [f"{cls}:{it.id}" for cls, it in _items() if not g._item_power_lines(it)]
    assert not silent, f"{len(silent)} items say nothing: {silent[:20]}"


def test_no_card_line_is_a_code_name():
    g = _game()
    bad = []
    for cls, it in _items():
        lines = list(g._item_power_lines(it)) + _text(g._lore_item_mechanic_lines(it, 5))
        for t in lines:
            if _CODE.search(t):
                bad.append(f"{cls}:{it.id}: {t[:90]}")
                break
    assert not bad, f"{len(bad)} items: {bad[:15]}"


def test_the_dossier_leads_with_what_the_kit_says():
    g = _game()
    for cls, it in _items():
        powers = list(g._item_power_lines(it))
        mech = _text(g._lore_item_mechanic_lines(it, 5))
        assert mech[0] == 'What It Does', f"{cls}:{it.id}"
        assert mech[1:1 + len(powers)] == powers, f"{cls}:{it.id}"
        assert 'No revealed mechanics recorded.' not in mech


def test_ring_of_wizardry_in_the_dossier():
    from items import load_items
    g = _game()
    ring = next(r for r in load_items('accessory') if r.id == 'ring_of_wizardry')
    ring.id_level = 5
    mech = _text(g._lore_item_mechanic_lines(ring, 5))
    assert any('spells cost' in t and 'less mana' in t for t in mech), mech


def test_every_power_field_is_written():
    import item_powers
    from items import load_items
    missing = []
    for cls, fields in POWER_FIELDS.items():
        for it in load_items(cls):
            for f in fields:
                v = getattr(it, f, None)
                if v in (None, '', 0, 0.0, False, {}, []):
                    continue
                key = f"{cls}:{it.id}.{f}"
                if f not in item_powers.covers(it, cls) and key not in KNOWN_DEAD:
                    missing.append(key)
    assert not missing, missing


def test_every_artifact_has_its_own_lines():
    import item_powers
    from items import load_items
    missing = [a.id for a in load_items('artifact') if not item_powers.own_lines(a, 'artifact')]
    assert not missing, missing


def test_every_written_line_fills_from_its_kind():
    """A placeholder names a real field of that kind, and every kind named
    in the data exists."""
    import item_powers
    from items import load_items
    by_id = item_powers.data().get('by_id') or {}
    for cls, kinds in by_id.items():
        if cls.startswith('_'):
            continue
        have = {it.id: it for it in load_items(cls)}
        if cls == 'container':
            # The chests the dungeon places come from data/chest_templates.json
            # (dungeon.py builds each with its template's id).
            from items import Container, load_chest_templates
            for tid, tdef in load_chest_templates().items():
                if isinstance(tdef, dict) and tid not in have:
                    have[tid] = Container({'id': tid, 'name': tdef.get('name', tid),
                                           'symbol': '&', 'color': [180, 140, 60],
                                           'weight': 30.0, 'item_class': 'container',
                                           'tier': int(tdef.get('tier', 1)),
                                           'quiz_tier': int(tdef.get('quiz_tier', tdef.get('tier', 1)))})
        for iid, spec in kinds.items():
            assert iid in have, f"{cls}:{iid} is not an item"
            for t in spec.get('lines') or ():
                item_powers.fill(t, have[iid], cls)      # raises on a missing field
            for f in spec.get('covers') or ():
                assert (item_powers.field(have[iid], f, cls) is not None or hasattr(have[iid], f)
                        or f.startswith('status:')), f"{cls}:{iid} covers {f}"


def test_every_chain_tier_bonus_is_in_words():
    import item_powers
    keys = set()
    for cls in ('weapon', 'armor', 'shield', 'accessory', 'artifact'):
        with open(os.path.join(ROOT, 'data', 'items', f'{cls}.json'), encoding='utf-8') as f:
            raw = json.load(f)
        for d in raw.values():
            if isinstance(d, dict):
                for row in (d.get('tier_bonuses') or {}).values():
                    keys |= set(row or {})
    unwired = set((item_powers.data().get('chain_unwired') or {}).keys())
    missing = sorted(k for k in keys if not item_powers.chain_label(k, 1) and k not in unwired)
    assert not missing, missing


@pytest.mark.parametrize('profile,want', [
    ({'pierce': 0.5}, "Takes less damage: pierce 50%."),
    ({'magic': 0.65, 'fire': 0.8, 'cold': 0.85}, "Takes less damage: magic 35%, fire 20%, cold 15%."),
    ({'fire': 0.0}, "Takes no fire damage."),
    ({'slash': 0.8, 'pierce': 0.8, 'lightning': 1.25},
     "Takes less damage: slash and pierce 20%. Takes more damage: lightning 25%."),
])
def test_resistances_say_the_damage_taken(profile, want):
    import item_powers
    assert item_powers.resist_line(profile) == want


def test_a_doubled_enchantment_name_is_said_once():
    import enchantments
    from items import load_items
    helm = next(a for a in load_items('armor') if a.id == 'helm_of_hades')
    line = enchantments.card_line(helm)
    assert line.startswith('Greater Night Eyes V: ') and 'Night Eyes V: Night' not in line
    assert line.count('Night Eyes') == 1


def test_a_title_enchantment_keeps_its_article_first():
    import enchantments
    ench = enchantments.get('the_hair_shirt')
    assert enchantments.display_name(ench, 6) == 'of the Greater Hair Shirt III'
    assert enchantments.display_name(ench, 5) == 'of the Hair Shirt III'
