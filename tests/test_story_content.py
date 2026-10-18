"""The story content (ENCOUNTER_STORIES_DRAFT.md, written into data/npc_encounters.json
and data/flavor_encounters.json) keeps the karma rules Brandon ruled on
(DEEDS_KARMA_DESIGN.md section 11) and hangs together: callbacks land on real
encounters, every oath can be kept, every person has a name, and each 10-floor
block offers two or three genuine chances at a point (decision 5).

Data-layer tests: these are late-game, randomised encounters that a play-test
cannot reach reliably (CLAUDE.md play-test rule).
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import deeds  # noqa: E402
import encounter_schema as ES  # noqa: E402
from tools.encounters import validate as V  # noqa: E402

ALL = V.load_all()                      # [(source, encounter)] after normalise
ENCS = [e for _s, e in ALL]
BY_TAG = {e['tag']: e for e in ENCS}
ANCHORS = [e for s, e in ALL if s == 'npc']
STORY = [e for s, e in ALL if s == 'flavor']

# Oaths an engine hook keeps (laying the thing on an altar), not an option.
ENGINE_KEPT_OATHS = {'aldric_lodestone', 'thoth_return'}
# Encounters the engine places itself rather than through a schedule.
OWN_PLACEMENT = {'flv_setne_tomb', 'flv_the_gate'}
# The only -2s in the draft (J2/J4): freeing Azarael, and giving the family to Death.
MINUS_TWO = {('azarael_demon', 'Shatter the chains and take his bargain'),
             ('flv_deaths_chessboard', 'Offer him the family if he lets you pass')}


def _branches(o):
    return ES.option_branches(o)


def _karma(b):
    """The karma an outcome moves: its own field, plus the engine's +1 for a
    kept oath and -1 for a broken one."""
    k = int(b.get('karma', 0) or 0)
    if b.get('oath_keep'):
        k += 1
    if b.get('oath_break'):
        k -= 1
    return k


def _max_karma(o):
    return max(_karma(b) for b in _branches(o))


def _min_karma(o):
    return min(_karma(b) for b in _branches(o))


def _strings_with_key(obj, keys, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, str):
                out.append(v)
            else:
                _strings_with_key(v, keys, out)
    elif isinstance(obj, list):
        for v in obj:
            _strings_with_key(v, keys, out)
    return out


# ------------------------------------------------------------------ shape

def test_every_encounter_normalises():
    tags = [e['tag'] for e in ENCS]
    assert len(tags) == len(set(tags)), 'tags are unique across both files'
    for e in ENCS:
        assert e['role'] in ES.ROLES and e['stakes'] in ES.STAKES, e['tag']
        assert isinstance(e.get('band'), list) and len(e['band']) == 2, e['tag']
        assert e['band'][0] <= e['band'][1], e['tag']
    # Three anchor candidates in every block, keyed by block so the old
    # placement (_BLOCKS) and the Road's anchor binding both still work.
    import npc_encounters
    for block, lo, hi in npc_encounters._BLOCKS:
        mine = [e for e in ANCHORS if e['block'] == block]
        assert len(mine) == 3, (block, [e['tag'] for e in mine])
        assert all(e['band'] == [lo, hi] for e in mine)
        triggered = [e for e in mine if e.get('trigger_item')]
        for e in triggered:
            fb = BY_TAG[e['fallback_anchor']]
            assert fb['block'] == block and not fb.get('trigger_item'), e['tag']


def test_the_cut_encounters_are_gone():
    for tag in ('flv_disgraced_knight', 'flv_wandering_merchant', 'flv_dwarven_smith',
                'flv_blind_oracle', 'brother_aldous', 'sister_marguerite', 'blinded_soldier',
                'apprentice_healer', 'child_shrine', 'flv_mirror_walker', 'flv_cursed_merchant',
                'flv_prophet_of_the_abyss', 'flv_oracle_of_endings', 'flv_demigod_beggar',
                'flv_discount_demigod_merchant', 'flv_avatar_hermes_laughing'):
        assert tag not in BY_TAG, tag


# ------------------------------------------------------------------ karma rules

def test_the_deadite_gives_nothing_either_way():
    e = BY_TAG['deadite_woman']
    for o in e['options']:
        assert _max_karma(o) == 0 and _min_karma(o) == 0, o['label']


def test_light_encounters_give_no_karma():
    for e in ENCS:
        if e['stakes'] != 'light':
            continue
        for o in e['options']:
            for b in _branches(o):
                assert _karma(b) == 0, (e['tag'], o['label'])
                assert not b.get('oath_keep') and not b.get('oath_break'), e['tag']


def test_naive_options_give_nothing_and_cost_something():
    n = 0
    for e in ENCS:
        for o in e['options']:
            if not o.get('naive'):
                continue
            n += 1
            assert all(_karma(b) == 0 for b in _branches(o)), (e['tag'], o['label'])
            assert V._has_consequence(o), (e['tag'], o['label'])
            assert o.get('warning') and V._norm(o['warning']) in V._norm(e['text']), e['tag']
    assert n >= 20                                    # the draft has two dozen traps


def test_forgo_always_has_a_richer_temptation_beside_it():
    table = V._rules()['reward_value']
    n = 0
    for e in ENCS:
        visible = [s for s in e['options'] if not s.get('requires')]
        for o in e['options']:
            if not any(b.get('karma_kind') == 'forgo' and int(b.get('karma', 0)) > 0
                       for b in _branches(o)):
                continue
            n += 1
            mine = V.option_value(o, table, e)
            assert any(V.option_value(s, table, e) > mine for s in visible if s is not o), \
                (e['tag'], o['label'])
    assert n >= 15


def test_contested_encounters_give_every_side_the_same():
    n = 0
    for e in ENCS:
        if not e.get('contested'):
            continue
        n += 1
        ks = {(_max_karma(o), _min_karma(o)) for o in e['options'] if not o.get('villain')}
        assert len(ks) == 1, (e['tag'], ks)
    assert n >= 8


def test_stance_encounters_lean_the_right_way():
    n = 0
    for e in ENCS:
        if not e.get('stance'):
            continue
        n += 1
        right = [_max_karma(o) for o in e['options'] if o.get('side') == 'right']
        wrong = [_max_karma(o) for o in e['options'] if o.get('side') == 'wrong']
        assert right and wrong and min(right) > max(wrong), e['tag']
        assert e.get('stance_note'), f"{e['tag']}: the opposing case is written down"
    assert n >= 5


def test_minus_two_only_where_the_draft_puts_it():
    found = set()
    for e in ENCS:
        for o in e['options']:
            for b in _branches(o):
                if _karma(b) <= -2:
                    found.add((e['tag'], o['label']))
                assert _karma(b) >= -2 and _karma(b) <= 1, (e['tag'], o['label'])
    assert found == MINUS_TWO


def test_no_virtue_tags_in_data():
    blob = json.dumps(ENCS)
    assert 'virtue:' not in blob
    assert '"virtue"' not in blob


# ------------------------------------------------------------------ references

def _all_outcomes(e):
    for o in e['options']:
        yield from _branches(o)
        if o.get('fail_total'):
            yield o['fail_total']
    for spec in (e.get('escorts') or {}).values():
        for k in ('on_arrive', 'on_fail'):
            if spec.get(k):
                yield spec[k]


def test_every_callback_target_exists_and_is_placed_by_something():
    scheduled = set()
    for e in ENCS:
        for b in _all_outcomes(e):
            for cb in b.get('schedule') or ():
                tgt = BY_TAG.get(cb['encounter'])
                assert tgt is not None, (e['tag'], cb['encounter'])
                assert tgt.get('callback_only'), cb['encounter']
                scheduled.add(cb['encounter'])
    orphans = {e['tag'] for e in ENCS if e.get('callback_only')} - scheduled - OWN_PLACEMENT
    assert not orphans, f'callback-only encounters nothing schedules: {sorted(orphans)}'


def test_every_oath_has_a_keeper():
    sworn, kept = {}, set()
    for e in ENCS:
        for b in _all_outcomes(e):
            if isinstance(b.get('oath'), dict):
                sworn[b['oath']['id']] = e['tag']
            if b.get('oath_keep'):
                kept.add(b['oath_keep'])
    assert sworn, 'the draft swears oaths'
    for oid, tag in sworn.items():
        assert oid in kept or oid in ENGINE_KEPT_OATHS, f'{tag}: oath {oid!r} can never be kept'
    assert kept <= set(sworn)


def test_every_person_has_a_name():
    for e in ENCS:
        p = e.get('person')
        if p is not None:
            assert re.fullmatch(r'[a-z0-9_]+', p.get('id', '')), e['tag']
            assert p.get('name', '').strip(), e['tag']
            assert p['name'][0].isupper(), e['tag']       # proper capitalisation
        for key, spec in (e.get('escorts') or {}).items():
            assert spec.get('name', '').strip() and spec['name'][0].isupper(), (e['tag'], key)
        for row in e.get('gate_lines') or ():
            assert row.get('person') and row.get('name', '').strip(), (e['tag'], row)
        for b in _all_outcomes(e):
            for who in b.get('people') or ():
                assert who.get('id') and who.get('name', '').strip(), e['tag']
    assert sum(1 for e in ENCS if e.get('person')) >= 100


def test_the_gate_reads_only_deeds_the_run_can_record():
    recorded = set()
    for e in ENCS:
        for b in _all_outcomes(e):
            recorded |= {d if isinstance(d, str) else d['id'] for d in b.get('deeds') or ()}
    rows = BY_TAG['flv_the_gate']['gate_lines']
    assert len(rows) >= 28
    for row in rows:
        ids = [i for k in ('deeds_all', 'deeds_any', 'deeds_none') for i in row['when'].get(k, ())]
        assert ids and set(ids) <= recorded, row
        assert set(row['when']) <= deeds.CONDITION_KEYS, row


# ------------------------------------------------------------------ the budget

def _plus_path(e) -> bool:
    """A genuine chance at a point: an option that can pay +1 (a passed test,
    a refused temptation, a costly stance, a kept promise), or a promise made
    here whose keeping comes later."""
    for b in _all_outcomes(e):
        if _karma(b) > 0 or isinstance(b.get('oath'), dict):
            return True
    return False


def _share(pool):
    return sum(_plus_path(e) for e in pool) / len(pool) if pool else 0.0


def block_opportunities() -> dict:
    """Expected +1 chances per block for one run (ENCOUNTER_STORIES_DRAFT
    Part I): the share of the block's anchors with a +1 path, plus each medium
    slot times the share of the medium pool that can land in the band (two
    slots in odd bands), plus the high slot (even bands) times the share of
    the high pool there, plus the chance that Setne's Tomb (its own roll, one
    floor in 45-65) lands in the block. Oath keeps spilling into a later block
    are left out, so the count errs low."""
    import road
    setne = BY_TAG['flv_setne_tomb']['own_roll']['floors']
    tomb = range(setne[0], setne[1] + 1)
    out = {}
    for b in range(1, 11):
        lo, hi = 10 * b - 9, 10 * b

        def pool(stakes):
            return [e for e in STORY if e['stakes'] == stakes and not e.get('callback_only')
                    and e['band'][0] <= hi and e['band'][1] >= lo]
        x = _share([e for e in ANCHORS if e['block'] == b])
        x += (2 if b in road.SECOND_MEDIUM_BANDS else 1) * _share(pool('medium'))
        if b in road.HIGH_BANDS:
            x += _share(pool('high'))
        x += sum(1 for f in tomb if lo <= f <= hi) / len(tomb)
        out[b] = round(x, 2)
    return out


def test_every_block_offers_two_or_three_chances():
    rep = block_opportunities()
    for b, x in rep.items():
        assert 2.0 <= x <= 3.0, f'block {b}: {x} chances (Brandon: two to three) {rep}'


# ------------------------------------------------------------------ lint

def test_chronicle_and_road_lint():
    lines = []
    for e in ENCS:
        lines += _strings_with_key(e, {'chronicle', 'chronicle_meet', 'on_fail_trapdoor',
                                       'keep_chronicle', 'late_chronicle', 'lapse_chronicle'}, [])
        for o in e['options']:
            if o.get('road'):
                bad = V._road_lint(o['road'], o.get('label', ''))
                assert not bad, (e['tag'], o['road'], bad)
                assert re.fullmatch(r'[a-z0-9_.]+', o['road'].get('id', '')), e['tag']
    assert len(lines) > 400
    for ln in lines:
        assert not V._chron_lint(ln), (ln, V._chron_lint(ln))
        assert ' - ' not in ln and '—' not in ln, f'no dashes as punctuation: {ln}'
    # One road per choice; the variants of one choice (a hidden group) share it.
    seen = {}
    for e in ENCS:
        for o in e['options']:
            if o.get('road'):
                key = (e['tag'], o.get('hidden_group') or o['label'])
                assert seen.setdefault(o['road']['id'], key) == key, (o['road']['id'], key)


def test_player_text_has_no_dash_punctuation():
    """Draft rule 0.3: no dashes as sentence punctuation in player-facing text."""
    for e in ENCS:
        texts = [e['text']] + [v['text'] for v in e.get('text_variants') or ()]
        texts += _strings_with_key(e['options'], {'outcome', 'label'}, [])
        for t in texts:
            assert '—' not in t and ' -- ' not in t, (e['tag'], t[:80])


# ------------------------------------------------------------------ ids and pending engine work

# Ids the new content names that the parallel engine work creates (Part J3).
# test_referenced_ids_exist passes once they land; until then the set below
# must cover every missing id, so a typo cannot hide among them.
PENDING_IDS = {
    'item': {'wats_oil_flask', 'olifant', 'rans_net', 'brennans_sword', 'azaraels_brand',
             'locust_charm', 'raphaels_gall', 'brass_wardens_cog', 'black_string_bracelet'},
    'effect': {'porter', 'sickly', 'light'},
    'monster': {'azarael', 'locust_cultist', 'morrow', 'locust_herald', 'neferkaptah_risen',
                'villager_mob', 'palace_guard'},
}


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def referenced_ids() -> dict:
    out = {'item': set(), 'effect': set(), 'monster': set()}
    for e in ENCS:
        if e.get('trigger_item'):
            out['item'].add(e['trigger_item'])
        for d in _walk(e):
            t = d.get('type')
            if t in ('specific_item', 'accept_item', 'triggered_item_id') and d.get('item_id'):
                out['item'].add(d['item_id'])
            if t == 'effect' and d.get('effect'):
                out['effect'].add(d['effect'])
            if 'monster_id' in d:
                out['monster'].add(d['monster_id'])
            if isinstance(d.get('oath'), dict) and d['oath'].get('item_id'):
                out['item'].add(d['oath']['item_id'])
    return out


def known_ids() -> dict:
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        monsters = set(json.load(f))
    import status_effects
    return {'item': V._item_ids(), 'effect': set(status_effects.EFFECT_INFO),
            'monster': monsters}


def test_missing_ids_are_only_the_pending_ones():
    ref, known = referenced_ids(), known_ids()
    for kind in ref:
        stray = ref[kind] - known[kind] - PENDING_IDS[kind]
        assert not stray, f'{kind} ids that exist nowhere: {stray}'


@pytest.mark.xfail(reason='pending engine merge', strict=False)
def test_referenced_ids_exist():
    ref, known = referenced_ids(), known_ids()
    assert all(ref[k] <= known[k] for k in ref), {k: ref[k] - known[k] for k in ref}


# The only validator breaches allowed while the engine work is in flight:
# each one must be explained by one of these new fields or types.
PENDING_MARKERS = ('own_roll', 'people', 'per_miss', 'fail_total', 'seal_room', "'after'",
                   'oath_lapse', 'run_start', 'gate_lines', 'gate_reading', 'fight needs',
                   "'gold_pct'", "'gold_pct_loss'", "'armor_enchant'", "'flag'", "'multi'")


def test_pending_engine_breaches_are_only_the_new_fields():
    pending = V.load_pending()
    for i in V.validate_all():
        if i.code in pending.get(i.tag, ()):
            assert any(m in i.msg for m in PENDING_MARKERS), str(i)
