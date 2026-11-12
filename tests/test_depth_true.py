"""Depth-true (Dungeon Alive slice 7, Brandon 2026-11-12): "as we descend, it
feels like we are delving deeper and deeper, to places where normal men cannot
go. It wouldn't make sense to find a happy fat merchant on level 83. He could
never reach it."

Every trader, every friend who stands in for one, and every Road anchor names
the kind of being it is (its ``reach``), and data/traders.json ``reach`` says
how deep that kind can go. These tests hold every floor any of them can stand
on inside that reach. An anchor's reach is its person's ``reach``: the most
limited being the scene puts there (the nine captives with Saint Lawrence are
captives; the bride at Thrym's feast is a god).

Data-layer tests: which trader or anchor a run meets is randomised and mostly
deep, so a play-test cannot reach them reliably (CLAUDE.md play-test rule).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import npc_encounters  # noqa: E402
import road  # noqa: E402
import traders  # noqa: E402

DOMAINS = {'the Labyrinth': (1, 20), 'the Forgotten Temple': (21, 40),
           'the Scorched Deep': (41, 60), 'the Rime Halls': (61, 80), 'the Abyss': (81, 100)}


def _reach(name):
    r = traders.reach(name)
    assert r is not None, f'no reach {name!r} in data/traders.json'
    return r


def _inside(span, reach):
    return reach[0] <= int(span[0]) <= int(span[1]) <= reach[1]


# ------------------------------------------------------------------ the table

def test_the_reach_table_is_well_formed():
    table = traders.data()['reach']
    names = [k for k in table if not k.startswith('_')]
    assert len(names) >= 10
    for name in names:
        lo, hi = traders.reach(name)
        assert 1 <= lo <= hi <= 100, name
        assert table[name]['who'].strip()[0].isupper(), name
    # The rulings the table rests on (the encounter audit's reach table).
    assert _reach('ordinary') == (1, 20)                 # the town's folk, the Labyrinth only
    assert _reach('hardy')[1] == 40                      # mortal guards stop by about 45
    assert _reach('damned_demon') == (61, 100)
    assert _reach('saint_angel') == (1, 100) and _reach('dead') == (1, 100)


# ------------------------------------------------------------------ anchors

def test_every_anchor_names_a_reach_and_its_floors_fit_it():
    for e in npc_encounters.ENCOUNTERS:
        r = (e.get('person') or {}).get('reach')
        assert r, f"{e['tag']}: person.reach missing"
        assert _inside(e['band'], _reach(r)), (e['tag'], e['band'], r, _reach(r))


def test_the_road_never_binds_an_anchor_out_of_its_reach():
    for i in range(400):
        st = road.new_state((i * 0x9E3779B1 + 7) & 0xFFFFFFFFFFFFFFFF, enabled=True)
        anchors = road.bind_anchors(st, npc_encounters.ENCOUNTERS)
        by_tag = {e['tag']: e for e in npc_encounters.ENCOUNTERS}
        for f, e in anchors.items():
            lo, hi = _reach(e['person']['reach'])
            assert lo <= f <= hi, (e['tag'], f)
            fb = st['slots'][f]['fallback']
            if fb:
                lo, hi = _reach(by_tag[fb]['person']['reach'])
                assert lo <= f <= hi, (fb, f)


def test_the_audits_depth_false_anchors_now_stand_where_they_can():
    """The eight the 2026-11-12 audit marked depth-false: ordinary folk in the
    Labyrinth, hardy delvers and the basilisk's work in Athena's temple."""
    by_tag = {e['tag']: e for e in npc_encounters.ENCOUNTERS}
    want = {'last_merchant': (1, 20), 'old_konstantin': (1, 20), 'grain_committee': (1, 20),
            'ser_brennan': (21, 40), 'penitent': (21, 40), 'roderic_shield': (21, 40),
            'petrified_adventurer': (21, 40), 'slavers_wagon': (21, 40)}
    for tag, (lo, hi) in want.items():
        band = by_tag[tag]['band']
        assert lo <= band[0] <= band[1] <= hi, (tag, band)
    # No wagon came down thirty stairs: Rusk drives a coffle.
    assert 'wagon' not in by_tag['slavers_wagon']['text'].lower()
    # The near-free point for the bell is gone: it costs knowing whose it is.
    bell = next(o for o in by_tag['last_merchant']['options']
                if 'forgo' in str((o.get('pass') or o).get('karma_kind')))
    assert bell.get('quiz') and bell['pass']['karma_kind'] == 'forgo'


def test_every_deep_block_keeps_three_anchors_who_belong_there():
    by_block = {}
    for e in npc_encounters.ENCOUNTERS:
        by_block.setdefault(e['block'], []).append(e)
    for block in range(5, 11):
        mine = by_block[block]
        assert len(mine) >= 3, block
        for e in mine:
            assert e['person']['reach'] not in ('ordinary', 'hardy'), (block, e['tag'])


def test_the_new_deep_anchors_teach_with_one_question_and_keep_the_karma_rules():
    """Each new deep anchor asks one question (threshold 1 of 1) where
    knowing decides the outcome, records deeds, and uses an existing sprite;
    a judgment point sits only in a quiz pass beside a naive choice."""
    from encounter_schema import has_naive_sibling, is_quiz, option_branches
    new = ('dwarf_siblings', 'lawrence_gridiron', 'sigyn_bowl', 'swan_shirt', 'thrym_wedding',
           'rich_man_gulf', 'euphrates_four')
    by_tag = {e['tag']: e for e in npc_encounters.ENCOUNTERS}
    for tag in new:
        e = by_tag[tag]
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters',
                                           e['sprite_id'] + '.png')), tag
        quizzes = [o for o in e['options'] if is_quiz(o)]
        assert quizzes, tag
        for o in quizzes:
            q = o['quiz']
            assert q['threshold'] == 1 and q['total_qs'] == 1, tag
            assert o['pass']['outcome'] != o['fail']['outcome'], tag
        for o in e['options']:
            for b in option_branches(o):
                assert b.get('deeds'), (tag, o['label'])
                if b.get('karma_kind') == 'judgment' and int(b.get('karma', 0)) > 0:
                    assert b is o.get('pass') and has_naive_sibling(e, o), (tag, o['label'])
    # Geography is asked somewhere in the anchors now (it was asked nowhere).
    assert any(o.get('quiz', {}).get('subject') == 'geography'
               for e in npc_encounters.ENCOUNTERS for o in e['options'])


# ------------------------------------------------------------------ traders

def _kinds():
    return {k: v for k, v in traders.data()['traders'].items() if not k.startswith('_')}


def test_every_trader_names_a_reach_and_every_floor_the_plan_gives_him_fits_it():
    planned = set()
    for kind, t in _kinds().items():
        r = _reach(t.get('reach'))
        spans = traders.kind_floors(kind)
        assert spans, f'{kind}: the plan never places this trader'
        for span in spans:
            assert _inside(span, r), (kind, span, t['reach'], r)
        planned.add(kind)
    assert planned == set(_kinds())


def test_every_friend_keeps_to_his_own_reach_and_to_his_traders_floors():
    for kind, t in _kinds().items():
        fr = t.get('friend')
        if not fr:
            continue
        span = fr.get('floors')
        assert span, f'{kind}: friend {fr["name"]} has no floors'
        assert _inside(span, _reach(fr.get('reach'))), (kind, fr['name'], span)
        assert any(lo <= span[0] and span[1] <= hi for lo, hi in traders.kind_floors(kind)), \
            (kind, fr['name'], span)


def test_a_rolled_plan_never_puts_a_trader_out_of_his_reach():
    for seed in range(150):
        plan = traders.roll_plan(seed * 7919 + 1)
        for fl, kind in plan['floors'].items():
            lo, hi = _reach(traders.kind_def(kind)['reach'])
            assert lo <= fl <= hi, (seed, kind, fl)


def test_the_gate_camps_change_hands_as_the_domains_deepen():
    camps = {int(f): k for f, k in traders.data()['plan']['gate_camps'].items()}
    assert camps == {19: 'sutler', 39: 'sutler', 59: 'regin', 79: 'tyr'}
    assert '59' not in traders.kind_def('sutler')['gate_lines']
    assert '79' not in traders.kind_def('sutler')['gate_lines']
    assert traders.kind_def('regin')['gate_lines'].keys() == {'59'}
    assert traders.kind_def('tyr')['gate_lines'].keys() == {'79'}


def test_individuals_are_he_or_she_and_only_vesper_is_it():
    for kind, t in _kinds().items():
        want = 'it' if kind == 'abyssal' else ('he', 'she')
        assert t['pronoun'] in want, (kind, t['pronoun'])
        fr = t.get('friend')
        if fr:
            assert fr['pronoun'] in ('he', 'she'), (kind, fr['name'])
