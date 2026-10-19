"""Monster families, the data layer (MONSTER_FAMILIES_DESIGN.md,
docs/systems/monster_families_v2_design.md and the 2026-10-18 rulings).

* every monster in data/monsters.json carries one valid `family`, the one
  tools/content/assign_monster_families.py settles from its lore;
* data/monster_families.json: 22 families (Spiders merged into Vermin), each
  with exactly five tiers (Recognise, Forewarned, Lore, Hunter, Bane), five
  strictly rising thresholds of DISTINCT kinds, a Field Note slot per tier,
  and abilities that use only known primitives with valid params;
* names are Title Case, nothing uses singular they, ward effects are real
  status effects, and a blurb never names a member.
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import family_edges  # noqa: E402
import family_lore  # noqa: E402
from naming import proper_name  # noqa: E402
from status_effects import EFFECT_INFO  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
FAMS = json.load(open(os.path.join(ROOT, 'data', 'monster_families.json'), encoding='utf-8'))
TIER_NAMES = ['Recognise', 'Forewarned', 'Lore', 'Hunter', 'Bane']


def _singular_they(text):
    from test_no_singular_they import find_singular_they
    return find_singular_they(text)


def _all_abilities():
    for fid, f in FAMS['families'].items():
        for t, entry in enumerate(f['tiers'], start=1):
            for a in entry['abilities']:
                yield fid, t, a


def test_every_monster_has_a_valid_family():
    ids = set(FAMS['families'])
    assert len(ids) == 22
    bad = {k: v.get('family') for k, v in MONS.items() if v.get('family') not in ids}
    assert not bad, bad


def test_the_written_families_match_the_assignment_tool():
    import assign_monster_families as amf
    assert set(amf.FAMILY_IDS) == set(FAMS['families'])
    assert amf.check(MONS) == []


def test_spiders_belong_to_vermin_and_the_builtins_have_no_family():
    for kind in ('cave_spider', 'giant_spider', 'phase_spider', 'spider_queen', 'arachne',
                 'ettercap', 'jorogumo', 'anansi'):
        assert MONS[kind]['family'] == 'vermin', kind
    assert 'spiders' not in FAMS['families']
    assert family_lore.family_of('player_ghost') == 'ghosts'       # the Bones ghost
    for kind in ('death', 'secret_cow', 'ethereal_unicorn'):
        assert family_lore.family_of(kind) is None


def test_five_tiers_and_five_rising_thresholds_everywhere():
    assert FAMS['tier_names'] == TIER_NAMES
    for fid, f in FAMS['families'].items():
        th = f['thresholds']
        assert len(th) == 5, fid
        assert all(isinstance(x, int) and x > 0 for x in th), fid
        assert all(a < b for a, b in zip(th, th[1:])), (fid, th)
        assert [t['name'] for t in f['tiers']] == TIER_NAMES, fid
        for entry in f['tiers']:
            assert 'field_note' in entry and isinstance(entry['field_note'], str), fid
            assert entry['abilities'], fid


def test_thresholds_are_the_ones_given():
    want = {
        'demons': [6, 13, 20, 28, 35], 'restless_dead': [4, 9, 14, 19, 24],
        'dragons': [3, 6, 10, 13, 17], 'giants': [3, 6, 9, 12, 16], 'ghosts': [3, 6, 9, 12, 15],
        'aberrations': [2, 5, 8, 11, 14], 'mortals': [2, 5, 8, 11, 13],
        'goblinkin': [2, 4, 7, 10, 13], 'constructs': [2, 4, 7, 10, 12],
        'legend': [2, 4, 7, 9, 12], 'vampires_liches': [2, 5, 8, 11, 14],
        'elementals': [2, 4, 6, 8, 10], 'serpents': [2, 3, 5, 7, 9],
        'great_beasts': [2, 3, 5, 7, 8], 'fair_folk': [2, 3, 5, 6, 8], 'vermin': [2, 3, 5, 6, 8],
    }
    for fid, th in want.items():
        assert FAMS['families'][fid]['thresholds'] == th, fid
    for fid in ('oozes', 'plants', 'birds', 'gorgons', 'shapeshifters', 'celestials'):
        assert FAMS['families'][fid]['thresholds'] == [2, 3, 4, 5, 6], fid


def test_every_ability_uses_a_known_primitive_with_valid_params():
    for fid, t, a in _all_abilities():
        assert family_edges.validate(a) == [], (fid, t, a.get('name'), family_edges.validate(a))
        assert a['id'].startswith(fid + '_'), a['id']
    for cid, c in FAMS['circles'].items():
        assert family_edges.validate(c['boon']) == [], cid


def test_the_first_two_tiers_are_recognise_and_forewarned():
    for fid, f in FAMS['families'].items():
        assert f['tiers'][0]['abilities'][0]['effect'] == 'recognise', fid
        fw = f['tiers'][1]['abilities'][0]
        assert fw['effect'] == 'forewarned' and fw['params']['line'].endswith('.'), fid


def test_ward_effects_are_real_status_effects():
    for fid, t, a in _all_abilities():
        for part in [a] + list(a.get('also', ())):
            if part['effect'] in ('save_bonus', 'duration_mult'):
                for eff in part['params']['effects']:
                    assert eff in EFFECT_INFO or eff in family_edges.SPECIAL_EFFECTS, (fid, eff)


def test_names_are_title_case_and_text_has_no_singular_they():
    for fid, f in FAMS['families'].items():
        assert proper_name(f['name']) == f['name'], f['name']
        assert proper_name(f['short']) == f['short'], f['short']
        for text in (f['blurb'], f['tiers'][1]['abilities'][0]['params']['line']):
            assert not _singular_they(text), (fid, text)
    for fid, t, a in _all_abilities():
        assert proper_name(a['name']) == a['name'], a['name']
        for text in (a['text'], a.get('trigger_msg', '')):
            assert not _singular_they(text), (fid, text)
    for c in FAMS['circles'].values():
        assert proper_name(c['name']) == c['name']
        assert proper_name(c['boon']['name']) == c['boon']['name']


def test_a_blurb_is_two_sentences_and_names_no_member():
    for fid, f in FAMS['families'].items():
        sentences = [x for x in re.split(r'(?<=[.!?])\s+', f['blurb'].strip()) if x]
        assert len(sentences) == 2, (fid, sentences)
        low = f['blurb'].lower()
        for kind in family_lore.members(fid):
            if kind not in MONS:
                continue                    # the Bones ghost is built in code
            name = MONS[kind]['name'].lower()
            assert not re.search(r'\b' + re.escape(name) + r's?\b', low), (fid, name)


def test_keystones_listed_are_members_and_count_two():
    assert FAMS['keystone_weight'] == 2
    for fid, f in FAMS['families'].items():
        for k in f['keystones']:
            assert MONS[k]['family'] == fid, (fid, k)
            assert family_lore.is_keystone(k)
    assert family_lore.is_keystone('arachne') and family_lore.is_keystone('spider_queen')
    assert family_lore.is_keystone('fafnir_dragon')            # a boss
    assert family_lore.is_keystone('morrow')                   # proper_noun
    assert not family_lore.is_keystone('skeleton')


def test_circles_name_real_families():
    for cid, c in FAMS['circles'].items():
        assert set(c['families']) <= set(FAMS['families']), cid
        assert 1 <= c['need'] <= len(c['families'])
        assert c['chronicle']


def test_the_journal_templates_have_one_per_tier():
    assert len(FAMS['tier_chronicle']) == 5
    assert len(FAMS['tier_messages']) == 5 and len(FAMS['popup_titles']) == 5
    for fid in FAMS['families']:
        for t in range(1, 6):
            assert '{' not in family_lore.tier_chronicle(fid, t)
