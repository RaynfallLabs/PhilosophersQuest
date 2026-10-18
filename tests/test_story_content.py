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


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import deeds  # noqa: E402
import encounter_schema as ES  # noqa: E402
import setne_tomb  # noqa: E402
from tools.encounters import validate as V  # noqa: E402

ALL = V.load_all()                      # [(source, encounter)] after normalise
with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as _f:
    GATE_ROWS = json.load(_f)['gate']['lines']      # The Gate's lines table (C18)
ENCS = [e for _s, e in ALL]
BY_TAG = {e['tag']: e for e in ENCS}
ANCHORS = [e for s, e in ALL if s == 'npc']
STORY = [e for s, e in ALL if s == 'flavor']

# Oaths an engine hook keeps (laying the thing on an altar), not an option.
ENGINE_KEPT_OATHS = {'aldric_lodestone', 'thoth_return'}
# Encounters the engine places itself rather than through a schedule.
OWN_PLACEMENT = {'flv_setne_tomb', 'flv_the_gate'}
# Brandon, 2026-10-18: "Betrayal is different than handing a murderer over
# for death. Make sure we differentiate. Max karma drop is -1."
# (ENCOUNTER_STORIES_DRAFT.md Part J9.) Every hand-over, inform, sell or
# false-witness option, classified. Betrayal: -1 of the kind named.
BETRAYAL = {
    ('grain_committee', 'Tell the commissar where the sack is'): 'betray',
    ('flv_antigone', "Tell Creon's men where she is"): 'betray',
    ('flv_deaths_chessboard', 'Offer him the family if he lets you pass'): 'cruelty',
    ('trapped_seraph', "Take Vell's finder's fee"): 'cruelty',
    ('fairy_jar', 'Sell her to Vell'): 'cruelty',
    ('flv_sword_in_anvil', "Back Kay's claim"): 'betray',
    ('flv_pardoner', 'Tell the pilgrims you saw a miracle'): 'cruelty',
    # Not a hand-over to the law: urging a blood feud on a killer who has
    # put himself under the law (the cairn later names his sons too).
    ('flv_lawspeaker_rock', 'Tell Steinar to take his revenge'): 'cruelty',
}
# Justice: the guilty handed to lawful judgement, true witness, exposing a
# cheat. Never negative; where the design rewards judgment it still does.
JUSTICE = {
    ('penitent', 'Weigh mercy and justice with them both'): 1,
    ('penitent', '"He was your father. You decide."'): 0,
    ('forgotten_prisoner', 'Leave him to his sentence'): 1,
    ('fallen_paladin', '"Go back up and face the families of Thale."'): 0,
    ('flv_paladin_end', 'Ask the pilgrim about the knight'): 0,
    ('flv_sword_in_anvil', 'Tell Sir Ector what you saw'): 0,
    ('flv_lawspeaker_rock', 'Speak the law: the price, the oath, the outlawry'): 1,
    ('flv_samsons_riddle', 'Tell Samson his bride was threatened, and give up the wager'): 1,
    ('flv_millers_thumb', 'Tell the widow about his thumb'): 1,
    ('flv_pardoner', 'Show the pilgrims his pardons are forged'): 1,
    ('flv_ostrander_pit', 'Leave him'): 0,
}


def _branches(o):
    return ES.option_branches(o)


def _karma(b):
    """The karma an outcome moves: its own field, plus the engine's +1 for a
    kept oath and -1 for a broken one (once: an outcome that pays the break
    itself as betray is not charged again, game_encounters._apply_outcome_deeds)."""
    k = int(b.get('karma', 0) or 0)
    if b.get('oath_keep'):
        k += 1
    if b.get('oath_break') and not (k < 0 and b.get('karma_kind') == 'betray'):
        k -= 1
    return k


def _opt(tag, label):
    return next(o for o in BY_TAG[tag]['options'] if o['label'] == label)


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
        # An anchor's band is its block's floors, or a narrower stretch of
        # them (the dying prophet stops at 97 so Ruth Gale has a floor below
        # him: bug bash 5, CON-17). Only he narrows it.
        assert all(lo <= e['band'][0] <= e['band'][1] <= hi for e in mine)
        narrowed = [e['tag'] for e in mine if e['band'] != [lo, hi]]
        assert narrowed in ([], ['dying_prophet']), narrowed
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


def test_no_choice_costs_more_than_one():
    # "Max karma drop is -1" (Brandon, 2026-10-18): the old -2s (freeing
    # Azarael, giving the family to Death) are -1 now.
    for e in ENCS:
        for o in e['options']:
            for b in _branches(o):
                assert -1 <= _karma(b) <= 1, (e['tag'], o['label'], _karma(b))
    assert _opt('azarael_demon', 'Shatter the chains and take his bargain')['karma'] == -1
    chess = _opt('flv_deaths_chessboard', 'Offer him the family if he lets you pass')
    assert (chess['karma'], chess['karma_kind']) == (-1, 'cruelty')


def test_betrayal_costs_one():
    for (tag, label), kind in BETRAYAL.items():
        o = _opt(tag, label)
        brs = _branches(o)
        assert [(_karma(b), b.get('karma_kind')) for b in brs] == [(-1, kind)] * len(brs), \
            (tag, label)


def test_justice_is_never_negative():
    for (tag, label), best in JUSTICE.items():
        o = _opt(tag, label)
        assert _min_karma(o) >= 0, (tag, label)
        assert _max_karma(o) == best, (tag, label)
    # Silas: the +1 is judgment, and only a hero who read the names sees it.
    silas = _opt('forgotten_prisoner', 'Leave him to his sentence')
    assert silas['karma_kind'] == 'judgment'
    assert silas['requires'] == {'deeds_all': ['noticed.silas_poisoner']}
    # Lucan: handed to his victim's son for the assize on the pass, never a loss.
    lucan = _opt('penitent', 'Weigh mercy and justice with them both')
    assert 'told.lucan_to_assize' in lucan['pass']['deeds']
    assert lucan['pass']['karma_kind'] == 'judgment'


def test_antigone_informing_is_betrayal_and_the_rest_stay_contested():
    # She buried her brother against an edict: a person of conscience, not a
    # criminal by any moral law. Telling Creon's men is the one indefensible
    # option, so it is marked villain (P9 skips it) and costs -1 betray; the
    # defensible options stay equal.
    e = BY_TAG['flv_antigone']
    assert e['contested']
    inform = _opt('flv_antigone', "Tell Creon's men where she is")
    assert inform['villain'] and inform['karma'] == -1 and inform['karma_kind'] == 'betray'
    assert 'wrong.reported_antigone' in inform['deeds']
    rest = [o for o in e['options'] if o is not inform]
    assert len(rest) == 3
    assert {(_max_karma(o), _min_karma(o)) for o in rest} == {(0, 0)}


def test_no_hand_over_option_is_left_unclassified():
    # A new option that hands over, informs on, sells or gives up a person
    # must be classified above (betrayal -1, or justice >= 0) before it ships.
    # ("Sell him a potion" sells TO him; "information" is not informing.)
    pat = re.compile(r"\b(sell (her|him|them)\b(?! (a|an|the|one|some)\b)"
                     r"|hand (him|her|them) over|turn (him|her|them) in"
                     r"|report (him|her|them)|inform(s|ed)?\b|testify|denounce|betray"
                     r"|give (him|her) up"
                     r"|where (she|he|they) (is|are)|where the sack is|offer him the family"
                     r"|finder's fee|back kay|tell sir ector|his sentence|take his revenge)",
                     re.I)
    known = set(BETRAYAL) | set(JUSTICE)
    stray = [(e['tag'], o['label']) for e in ENCS for o in e['options']
             if pat.search(o['label']) and (e['tag'], o['label']) not in known]
    assert not stray, stray


def test_no_virtue_tags_in_data():
    blob = json.dumps(ENCS)
    assert 'virtue:' not in blob
    assert '"virtue"' not in blob


# ------------------------------------------------------------------ references

def _all_outcomes(e):
    for o in e['options']:
        yield from _branches(o)             # pass, fail and fail_by_correct
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
        for b in _all_outcomes(e):
            for who in b.get('people') or ():
                assert who.get('id') and who.get('name', '').strip(), e['tag']
    assert sum(1 for e in ENCS if e.get('person')) >= 100
    for row in GATE_ROWS:
        assert row.get('person') and row.get('name', '').strip(), row
        assert row['name'][0].isupper(), row


def test_the_gate_reads_only_deeds_the_run_can_record():
    recorded = set()
    for e in ENCS:
        for b in _all_outcomes(e):
            recorded |= {d if isinstance(d, str) else d['id'] for d in b.get('deeds') or ()}
    rows = GATE_ROWS
    assert len(rows) >= 28
    gate = BY_TAG['flv_the_gate']
    assert any((o.get('people_lines') or {}).get('table') == 'gate' for o in gate['options'])
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
    tomb = setne_tomb.candidate_floors()      # its own roll, never a boss floor
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


# ------------------------------------------------------------------ ids


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


def test_referenced_ids_exist():
    ref, known = referenced_ids(), known_ids()
    assert all(ref[k] <= known[k] for k in ref), {k: ref[k] - known[k] for k in ref}
    assert ref['item'] and ref['effect'] and ref['monster']     # the walk found them


def test_the_engine_work_is_merged_and_nothing_is_pending():
    """Phase 3 integration: the pending_engine section is empty and the
    validator finds nothing, allowlisted or not."""
    assert V.load_pending() == {}
    assert V.load_allowlist() == {}
    assert V.validate_all() == []


# A fight in a deep band is fought with a monster of that depth (LORE NOT
# FLOOR: the data names a creature that belongs there; nothing is scaled at
# runtime). A shallow pick may sit at most this many floors below its band.
FIGHT_DEPTH_SLACK = 20


def test_fights_use_monsters_of_their_band():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        monsters = json.load(f)
    bad = []
    for e in ENCS:
        lo = e['band'][0]
        for b in _all_outcomes(e):
            for mid, _n in ES.fight_entries(b.get('fight')) if b.get('fight') else ():
                peak = int(monsters[mid].get('peak_floor') or 0)
                if peak + FIGHT_DEPTH_SLACK < lo:
                    bad.append((e['tag'], mid, peak, e['band']))
    assert not bad, bad
