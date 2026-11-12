"""Dungeon Alive, slice 9: encounters with payoffs that teach (Brandon,
2026-11-12: "Most encounters SHOULD have some sort of interaction or payoff,
not just a superficial process"; "it wouldn't make sense to find a happy fat
merchant on level 83").

Data-layer tests on data/flavor_encounters.json: randomised, often deep
content that a play-test cannot reach reliably (CLAUDE.md play-test rule).
They pin what the slice did: no scene is only free talk, every question
decides something, geography finally decides some, people sit where they can
really be, and the rule flags from _alive_research/ENCOUNTER_AUDIT.md stay
fixed.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'flavor_encounters.json'), encoding='utf-8') as _f:
    FLV = json.load(_f)
BY_TAG = {e['tag']: e for e in FLV}

# An option with any of these does something: it costs, asks, fights, walks
# someone, schedules a later scene, writes a deed, moves a person or karma.
_MECHANICS = ('cost', 'quiz', 'fight', 'escort', 'schedule', 'delayed', 'deeds',
              'person_status', 'karma', 'oath', 'oath_keep', 'oath_break', 'people_lines',
              'people', 'thread', 'thread_close', 'expel_up', 'seal_door', 'then')
# What a pass or a fail can change.
_BRANCH_FIELDS = ('reward', 'bonus_reward', 'deeds', 'cost', 'karma', 'person_status',
                  'schedule', 'then', 'fight', 'escort', 'thread_close', 'delayed', 'people')


def _opt(tag, label):
    (o,) = [o for o in BY_TAG[tag]['options'] if o['label'] == label]
    return o


def _free_message(o):
    if any(o.get(k) for k in _MECHANICS):
        return False
    r = o.get('reward')
    return r is None or (isinstance(r, dict) and r.get('type') == 'message')


def _quiz_options():
    return [(e['tag'], o) for e in FLV for o in e['options'] if isinstance(o.get('quiz'), dict)]


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


# ---------------------------------------------------------------- payoff

def test_no_flavor_scene_is_only_free_talk():
    """Every scene offers at least one choice that does something real."""
    flat = [e['tag'] for e in FLV if all(_free_message(o) for o in e['options'])]
    assert not flat, flat


def test_every_question_decides_something():
    """A pass and a fail never read the same or pay the same (the audit's
    Sir Lorvaine paid a random accessory either way)."""
    bad = []
    for tag, o in _quiz_options():
        p, f = o.get('pass') or {}, o.get('fail') or {}
        assert p.get('outcome', '').strip() and f.get('outcome', '').strip(), (tag, o['label'])
        same_text = p.get('outcome') == f.get('outcome')
        same_mech = all(json.dumps(p.get(k), sort_keys=True) == json.dumps(f.get(k), sort_keys=True)
                        for k in _BRANCH_FIELDS)
        if same_text or same_mech:
            bad.append((tag, o['label']))
    assert not bad, bad


def test_light_questions_are_one_untimed_question():
    for tag, o in _quiz_options():
        if BY_TAG[tag].get('stakes', 'light') != 'light':
            continue
        q = o['quiz']
        assert (q.get('mode', 'threshold'), q.get('threshold'), q.get('total_qs'), q.get('timed')) \
            == ('threshold', 1, 1, False), (tag, o['label'])


def test_geography_decides_something_at_last():
    """Finding a way, reading a map, closing a survey: geography had no
    encounter use before this slice."""
    geo = sorted({tag for tag, o in _quiz_options() if o['quiz']['subject'] == 'geography'})
    assert len(geo) >= 4, geo
    for tag in ('flv_lost_merchant', 'flv_mapmaker', 'flv_lost_caravan_guard', 'flv_abyss_cartographer'):
        assert tag in geo, tag


def test_most_scenes_ask_a_question():
    """Knowledge decides something in most scenes now (64 of 611 options
    asked a question before)."""
    asking = {tag for tag, _o in _quiz_options()}
    assert len(asking) >= 105, len(asking)
    assert len(asking) * 10 >= len(FLV) * 7            # seven scenes in ten
    assert len(_quiz_options()) >= 115


# ---------------------------------------------------------------- pronouns

# Labels that say they / them / their mean more than one (rats, mushrooms,
# monks, a crowd). A new one must be read and added here, or fixed.
_PLURAL_LABELS = {
    ('flv_rat_king_tiny', 'Offer them some food'),
    ('flv_rat_king_tiny', 'Try to untangle their tails'),
    ('flv_rat_king_tiny', 'Leave the rats to their politics'),
    ('flv_baucis_table', 'Eat what they offer; refusing would shame them'),
    ('flv_baucis_table', 'Offer to catch the goose for their pot'),
    ('flv_three_mushrooms', 'Sit in their light for a while'),
    ('flv_three_mushrooms', 'Leave them in peace'),
    ('flv_brendans_whale', 'Wish them a happy Easter and go'),
    ('flv_trembler', '"Live. Dying well won\'t change what they call you."'),
    ('flv_trembler', 'Call him what they call him'),
    ('flv_boundary_stone', 'Leave coins in the vinegar for their supplies'),
    ('flv_sword_in_anvil', 'Put it back in the anvil and let them both try'),
    ('flv_the_gate', '"Tell me about them."'),
}


def test_no_individual_is_called_they():
    """Brandon, 2026-10-18: they / them only ever for more than one."""
    labels = {(e['tag'], o['label']) for e in FLV for o in e['options']
              if re.search(r"\b(they|them|their|theirs)\b", o['label'], re.I)}
    assert labels <= _PLURAL_LABELS, sorted(labels - _PLURAL_LABELS)
    text = ' '.join(_strings(FLV))
    assert not re.search(r'\bthemself\b', text, re.I)
    bones = BY_TAG['flv_singing_bones']
    assert [o['label'] for o in bones['options'] if 'died' in o['label']] == ['Ask how he died']
    assert bones['person']['name'] == 'Hamund the Bold'


# ---------------------------------------------------------------- depth

# Where the audit's depth-false people (and the stretches it proposed) now
# stand: ordinary folk near the top, hardy delvers to 40, the exceptional to
# 50, the Greek legends in the Temple (21-40), the Norse ones in the Rime
# Halls (61-80).
_HOMES = {
    'flv_lawspeaker_rock': (1, 20), 'flv_lost_caravan_guard': (1, 20),
    'flv_food_vendor_dungeon': (1, 20), 'flv_rust_collector': (1, 20),
    'flv_exposed_child': (1, 20), 'flv_boundary_stone': (1, 20),
    'flv_sword_in_anvil': (1, 20), 'flv_two_mothers': (1, 29), 'flv_pardoner': (1, 30),
    'flv_squire_tobyn': (21, 40), 'flv_abyssal_wine_merchant': (21, 40),
    'flv_the_mast': (21, 40), 'flv_avatar_athena': (21, 40), 'flv_antigone': (21, 40),
    'flv_abyss_cartographer': (41, 50), 'flv_abyssal_alchemist': (41, 60),
    'flv_dragons_accountant': (41, 60), 'flv_andvaris_pool': (41, 60),
    'flv_mimirs_well': (61, 80), 'flv_utgard_contests': (61, 80),
    'flv_melancholy_old_champion': (61, 80),
}


def test_people_stand_where_they_could_really_be():
    for tag, (lo, hi) in _HOMES.items():
        e = BY_TAG[tag]
        assert lo <= e['min_level'] <= e['max_level'] <= hi, (tag, e['min_level'], e['max_level'])


def test_the_deep_ones_are_deep_folk_the_dead_or_captives():
    # The alchemist is a dwarf of the Scorched Deep; the diviner is a ghost;
    # Oswin's witness is a dead pilgrim; Death's family are the locust cult's
    # captives; the soldier out of time is plainly dead.
    assert BY_TAG['flv_abyssal_alchemist']['sprite_id'] == 'npc_dwarf'
    assert BY_TAG['flv_wandering_oracle_bone']['sprite_id'] == 'npc_ghost'
    assert 'see the step through' in BY_TAG['flv_paladin_end']['text']
    assert 'locust cult' in BY_TAG['flv_deaths_chessboard']['text']
    assert 'does not fog' in BY_TAG['flv_time_lost_soldier']['text']
    # The labels the karma tests read are unchanged.
    _opt('flv_paladin_end', 'Ask the pilgrim about the knight')
    _opt('flv_deaths_chessboard', 'Offer him the family if he lets you pass')


def test_no_happy_merchant_in_the_abyss():
    """The deep generalist Ortolan is a trader (data/traders.json); the old
    flavor scene is Simon Magus now, one of the damned, and still sells."""
    e = BY_TAG['flv_final_merchant_ortolan']
    blob = ' '.join(_strings(e))
    assert 'Ortolan' not in blob and e['person']['name'] == 'Simon Magus'
    assert e['options'][0]['cost'] == {'type': 'gold', 'share': 'potion', 'markup': 1.5}
    # The armourer trader is Brunhild; the shallow smith is someone else.
    assert 'Brunhild' not in ' '.join(_strings(FLV))
    # The bookseller (Crispin Vellum) and the slaver are never confused here.
    assert not re.search(r'\bAmbrose\b', ' '.join(_strings(FLV)))


# ---------------------------------------------------------------- rule flags

def test_the_honest_guest_pays_a_night_for_the_girdle():
    o = _opt('flv_green_girdle', 'Take it, and give it to your host at the door, as agreed')
    assert (o['karma'], o['karma_kind']) == (1, 'forgo')
    assert o['cost'] == {'type': 'sp_pct', 'amount': 20}
    assert 'cock crow' in o['outcome'] and not o.get('schedule')


def test_sir_lorvaines_riddle_decides_his_gift():
    o = _opt('flv_mad_knight_riddle', 'Answer his riddle')
    assert o['pass'].get('reward') and not o['fail'].get('reward')
    assert 'bookworm' in o['pass']['outcome'] and 'Exeter' in BY_TAG['flv_mad_knight_riddle']['text']


# ---------------------------------------------------------------- the deep pools

_NEW_DEEP = ('flv_echo_rime', 'flv_valkyrie_choice', 'flv_ulysses_flame', 'flv_azazel_bound',
             'flv_sisyphus')


def test_new_deep_scenes_are_deep_and_decided_by_knowledge():
    assert len(_NEW_DEEP) <= 8
    for tag in _NEW_DEEP:
        e = BY_TAG[tag]
        assert 61 <= e['min_level'] <= e['max_level'] <= 98, tag
        assert not e.get('callback_only'), tag
        assert e['sprite_id'].startswith('npc_'), tag
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', e['sprite_id'] + '.png')), tag
        assert any(isinstance(o.get('quiz'), dict) for o in e['options']), tag


def test_new_karma_sits_behind_a_passed_question():
    """New points are never on an easy or kind option: each is a judgment
    pass beside a naive sibling (the coordinator's note, and decision 7)."""
    for tag in ('flv_valkyrie_choice', 'flv_ulysses_flame', 'flv_azazel_bound'):
        e = BY_TAG[tag]
        assert any(o.get('naive') for o in e['options']), tag
        for o in e['options']:
            if int(o.get('karma', 0) or 0) > 0:
                raise AssertionError((tag, o['label'], 'karma outside a quiz'))
            q = o.get('pass') if isinstance(o.get('quiz'), dict) else None
            if q and int(q.get('karma', 0) or 0) > 0:
                assert q['karma'] == 1 and q['karma_kind'] == 'judgment', (tag, o['label'])
    brendan = _opt('flv_brendans_whale', 'Look at the island properly')
    assert (brendan['pass']['karma'], brendan['pass']['karma_kind']) == (1, 'judgment')
    assert not brendan['fail'].get('karma')


def test_the_old_repeaters_are_diluted():
    """Death's chessboard was in every run and the echo in the wall in about
    two in three: the deep high pools hold more than Death now, and the voice
    in the wall is four voices, one per domain."""
    deep_high = [e['tag'] for e in FLV if e.get('stakes') == 'high' and not e.get('callback_only')
                 and e['min_level'] <= 98 and e['max_level'] >= 91]
    assert len(deep_high) >= 2 and 'flv_deaths_chessboard' in deep_high
    voices = [BY_TAG[t] for t in ('flv_echo_voice', 'flv_echo_temple', 'flv_echo_deep', 'flv_echo_rime')]
    spans = [(v['min_level'], v['max_level']) for v in voices]
    assert spans == sorted(spans) and all(hi - lo <= 20 for lo, hi in spans)
    assert BY_TAG['flv_ghost_librarian_junior']['max_level'] <= 60


def test_callbacks_this_slice_added_are_wired():
    """Old Nan's cat and Maud Ferrers's boy come back later, and only after the
    scene that sends them."""
    sit = _opt('flv_weeping_ghost', 'Sit with her for a while')
    assert sit['schedule'][0]['encounter'] == 'flv_cobbler_comes_home' and sit['thread']['id'] == 'old_nans_cat'
    pray = _opt('weeping_mother', 'Kneel and pray with her until she can rest')
    assert pray['pass']['schedule'][0]['encounter'] == 'flv_pip_ferrers'
    assert not pray['fail'].get('schedule')
    for tag in ('flv_cobbler_comes_home', 'flv_pip_ferrers'):
        assert BY_TAG[tag]['callback_only'], tag
