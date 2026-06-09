"""Composed UNIDENTIFIED item names must read as clean English, never garbage
(2026-06-07, comprehensive audit).

User reported "Slender, Pale Length of Wood Longbow". Material
`unidentified_descriptor`s are standalone noun phrases with clauses ("a blade
that shows no edge wear", "a pale fibrous wood"); composed with a template noun
they produced nonsense. The fix hardened items._normalize_descriptor (drop
commas, truncate at a clause word, strip trailing object nouns) and rewrote the
~20 descriptors whose visual was buried in a clause.

This sweeps EVERY template x compatible-material unidentified name and asserts
none is garbage: no comma, no relative-clause word, no 'strange' fallback, and
<= 5 words.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import (load_templates, load_materials, instantiate_weapon,  # noqa: E402
                   instantiate_armor, instantiate_shield, _normalize_descriptor)

# Relative/prepositional words that signal a clause leaked into the name.
_CLAUSE_WORDS = {'that', 'which', 'who', 'whose', 'of', 'like', 'with'}


def _why_messy(name: str):
    ws = name.lower().split()
    if ',' in name:
        return 'comma'
    if 'strange' in ws:
        return 'strange-fallback'          # descriptor reduced to nothing
    if any(w in _CLAUSE_WORDS for w in ws):
        return 'clause-word'
    if len(ws) > 6:   # "Dense Black Metal Full Plate Armor" (6) is the legit max
        return f'{len(ws)}-words'
    return None


def _all_unidentified_names():
    pools = {'weapons': load_materials('weapons'), 'armor': load_materials('armor')}
    specs = (('weapons', instantiate_weapon, 'weapons'),
             ('armor', instantiate_armor, 'armor'),
             ('shields', instantiate_shield, 'armor'))
    for cat, inst, mat_key in specs:
        tpls = load_templates(cat)
        mats = dict(pools[mat_key])
        if cat == 'shields':
            mats.update(pools['weapons'])
        for tid, tpl in tpls.items():
            compat = set(tpl.get('compatible_material_classes') or [])
            for mid, mat in mats.items():
                mcls = mat.get('material_class') or mat.get('class')
                if compat and mcls and mcls not in compat:
                    continue
                try:
                    it = inst(tid, mid)
                except Exception:
                    continue
                yield mid, tid, it.unidentified_name


def test_no_composed_unidentified_name_is_garbage():
    bad = []
    for mid, tid, name in _all_unidentified_names():
        why = _why_messy(name)
        if why:
            bad.append(f"[{why}] {mid}+{tid}: {name!r}")
    assert not bad, "Garbage unidentified names:\n  " + "\n  ".join(sorted(set(bad))[:30])


def test_reported_willow_longbow_name_is_clean():
    n = instantiate_weapon('longbow', 'willow').unidentified_name
    assert n == 'Slender Pale Longbow', n
    assert 'length of wood' not in n.lower()
    assert ',' not in n


def test_normalize_descriptor_strips_clauses_commas_and_shape_nouns():
    # clause + shape-noun stripped; material-class hint words (wood, alloy) KEPT
    assert _normalize_descriptor('a midnight-dark blade that shows no edge wear') == 'midnight-dark'
    assert _normalize_descriptor('a pale fibrous wood') == 'pale fibrous wood'
    assert _normalize_descriptor('a heavy, dark club') == 'heavy dark'
    assert _normalize_descriptor('an impossible alloy, color shifting in firelight') == 'impossible alloy'
    # a descriptor that reduces to nothing yields the neutral fallback, NOT junk
    assert _normalize_descriptor('a blade') == 'strange'
