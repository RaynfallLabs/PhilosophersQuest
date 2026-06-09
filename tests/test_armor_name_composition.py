"""Regression test for the 2026-06-01 "missing noun" bug.

User reported pickup messages like:
  - "You find a Stiff Coarse Padded!"
  - "You find Linen Padded!"

The template name 'padded' is a pure adjective. `compose_item_name` used
to concatenate material + template with no noun, producing "Linen Padded".
The fix: add a `noun` field to deficient templates and have
`compose_item_name` append it when the cleaned phrase doesn't already
contain one.

This test asserts:
  1. Every armor template either ends in a recognizable noun
     (boots, helm, mail, ...) OR declares an explicit `noun` field.
  2. Every (template, compatible-material) pair composes to a name with
     >= 2 whitespace-separated words whose final word is a recognizable
     noun.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# Words that count as the final NOUN of an armor name. Anything that ends
# in one of these is a complete name; anything else needs a `noun` field
# in its template JSON.
RECOGNIZED_NOUNS = frozenset({
    'armor', 'mail', 'coat', 'tunic', 'robe', 'vest', 'jerkin',
    'breastplate', 'cloak', 'shirt', 'boots', 'helm', 'cap',
    'gauntlets', 'gloves', 'vambraces', 'bracers', 'leggings',
    'chausses', 'greaves', 'chainmail', 'ringmail', 'hauberk',
})


def _armor_templates() -> dict[str, dict]:
    out = {}
    for path in glob.glob(str(ROOT / "data" / "templates" / "armor" / "*.json")):
        name = os.path.basename(path)[:-5]
        with open(path, encoding='utf-8') as f:
            out[name] = json.load(f)
    return out


def _armor_materials() -> dict[str, dict]:
    out = {}
    for path in glob.glob(str(ROOT / "data" / "materials" / "armor" / "*.json")):
        name = os.path.basename(path)[:-5]
        with open(path, encoding='utf-8') as f:
            out[name] = json.load(f)
    return out


def _final_word(name: str) -> str:
    return name.split()[-1].lower() if name else ''


# ---------------------------------------------------------------------------
# Test 1 — every template has either a name ending in a recognized noun
# or an explicit `noun` field.
# ---------------------------------------------------------------------------

def test_every_armor_template_has_a_noun():
    """Either the template's `name` ends in a recognized noun, or it
    declares an explicit `noun` field. Otherwise composed names will be
    bare adjective phrases like 'Linen Padded'."""
    templates = _armor_templates()
    missing = []
    for tid, tpl in templates.items():
        name = tpl.get('name', '')
        noun = tpl.get('noun', '')
        if _final_word(name) in RECOGNIZED_NOUNS:
            continue
        if noun and _final_word(noun) in RECOGNIZED_NOUNS:
            continue
        missing.append(f"{tid}: name={name!r} noun={noun!r}")
    assert not missing, (
        "Templates without a usable noun (will render as bare adjective "
        "in pickup messages):\n  " + "\n  ".join(missing))


# ---------------------------------------------------------------------------
# Test 2 — instantiate_armor composes a name with >=2 words ending
# in a recognized noun for every template × compatible-material pair.
# ---------------------------------------------------------------------------

def test_instantiate_armor_composes_full_noun_phrase():
    """Cross-product every armor template with every compatible material
    and assert the composed name has at least two words AND ends in a
    recognized noun. Guards against the 'Linen Padded' / 'Stiff Coarse
    Padded' bug coming back via a new template lacking a noun, or a
    code-side regression in `compose_item_name`.
    """
    from items import instantiate_armor

    templates = _armor_templates()
    materials = _armor_materials()
    failures = []

    for tid, tpl in templates.items():
        compat = set(tpl.get('compatible_material_classes', []) or [])
        for mid, mat in materials.items():
            mclass = mat.get('material_class', '')
            # Only test material/template combos the game would actually
            # spawn — otherwise we'd test e.g. cloth-on-plate-armor which
            # the spawn picker would never produce.
            if compat and mclass and mclass not in compat:
                continue
            # Some materials are explicitly armor-applicable and some weapons-only.
            if 'armor' not in (mat.get('applies_to') or ['armor']):
                continue
            try:
                a = instantiate_armor(tid, mid)
            except Exception as e:
                failures.append(f"{tid} + {mid}: instantiation raised {e!r}")
                continue
            name = a.name
            words = name.split()
            if len(words) < 2:
                failures.append(
                    f"{tid} + {mid}: composed name {name!r} has < 2 words")
                continue
            if _final_word(name) not in RECOGNIZED_NOUNS:
                failures.append(
                    f"{tid} + {mid}: composed name {name!r} doesn't end in a "
                    f"recognized noun (last word={_final_word(name)!r})")

    assert not failures, "Composed armor names without a clear noun:\n  " + "\n  ".join(failures[:30])


# ---------------------------------------------------------------------------
# Test 3 — explicit regression on the user-reported strings.
# ---------------------------------------------------------------------------

def test_linen_padded_includes_noun():
    """The user-reported bug: 'Linen Padded' had no noun. After the fix
    the composed name should include a noun ('coat')."""
    from items import instantiate_armor
    a = instantiate_armor('padded', 'linen')
    assert _final_word(a.name) in RECOGNIZED_NOUNS, (
        f"Linen padded composed as {a.name!r} — still missing a noun!")
    assert 'padded' in a.name.lower(), (
        f"'padded' adjective dropped from {a.name!r}")


def test_canvas_padded_includes_noun():
    """Second user-reported example: 'Stiff Coarse Padded' — the canvas
    material has a multi-word name 'stiff coarse canvas' or similar.
    Whatever the material name, the composed armor name must end in a
    recognized noun.
    """
    from items import instantiate_armor, get_material
    if get_material('armor', 'canvas') is None:
        # If canvas material was renamed, skip — the general test still covers it.
        return
    a = instantiate_armor('padded', 'canvas')
    assert _final_word(a.name) in RECOGNIZED_NOUNS, (
        f"canvas padded composed as {a.name!r} — still missing a noun!")


# ---------------------------------------------------------------------------
# Test 4 — no DOUBLED material word (2026-06-07: user reported "Hide Hide
# Armor"). The hide/leather/padded body templates are named after a material
# word, so pairing them with that same material doubled it.
# ---------------------------------------------------------------------------

def _has_doubled_word(name: str) -> bool:
    ws = [w.lower() for w in name.split()]
    if len(ws) != len(set(ws)):
        return True            # exact repeat: 'hide hide'
    # compound-suffix repeat: 'rawhide ... hide', 'plate ... breastplate'
    for a in ws:
        for b in ws:
            if a != b and len(b) >= 4 and len(a) > len(b) and a.endswith(b):
                return True
    return False


def test_no_doubled_material_word_in_any_armor_name():
    from items import instantiate_armor
    templates = _armor_templates()
    materials = _armor_materials()
    bad = []
    for tid, tpl in templates.items():
        compat = set(tpl.get('compatible_material_classes', []) or [])
        for mid, mat in materials.items():
            mclass = mat.get('material_class', '')
            if compat and mclass and mclass not in compat:
                continue
            try:
                a = instantiate_armor(tid, mid)
            except Exception:
                continue
            if _has_doubled_word(a.name):
                bad.append(f"{tid}+{mid} -> {a.name!r}")
    assert not bad, "Doubled-word armor names:\n  " + "\n  ".join(sorted(set(bad))[:30])


def test_reported_doubled_names_are_fixed():
    """Explicit regression on the exact user string + siblings, and proof the
    fix keeps a material word where it still distinguishes the piece."""
    from items import compose_item_name
    assert compose_item_name('hide', 'hide', 'armor') == 'Hide Armor'
    assert compose_item_name('leather', 'leather', 'armor') == 'Leather Armor'
    assert compose_item_name('boiled leather', 'leather', 'armor') == 'Boiled Leather Armor'
    assert compose_item_name('rawhide', 'hide', 'armor') == 'Rawhide Armor'
    assert compose_item_name('dragonhide', 'hide', 'armor') == 'Dragonhide Armor'
    # 'plate' implied by 'breastplate' is dropped...
    assert compose_item_name('dwarven plate', 'breastplate', '') == 'Dwarven Breastplate'
    # ...but KEPT where it distinguishes (plate gauntlets vs leather gauntlets)
    assert compose_item_name('dwarven plate', 'gauntlets', '') == 'Dwarven Plate Gauntlets'
    # no regression on legit composites
    assert compose_item_name('steel', 'iron boots', '') == 'Steel Boots'
    assert compose_item_name('cured leather', 'padded', 'coat') == 'Cured Leather Padded Coat'


def test_cross_leather_family_redundancy_is_dropped():
    """A leather/hide MATERIAL meeting the OTHER family word as the TEMPLATE
    read redundantly ('Boiled Leather Hide Armor'). The class word is dropped."""
    from items import compose_item_name
    assert compose_item_name('boiled leather', 'hide', 'armor') == 'Boiled Leather Armor'
    assert compose_item_name('dragonhide', 'leather', 'armor') == 'Dragonhide Armor'
    assert compose_item_name('leather', 'hide', 'armor') == 'Leather Armor'
    assert compose_item_name('cured leather', 'hide', 'armor') == 'Cured Leather Armor'
    # a NON-leather material keeps a meaningful template class word
    assert compose_item_name('iron', 'plate', 'armor') == 'Iron Plate Armor'
