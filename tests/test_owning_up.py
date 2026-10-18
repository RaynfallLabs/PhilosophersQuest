"""Owning up vs surrender (Brandon, 2026-10-18; ENCOUNTER_STORIES_DRAFT.md Part
J10, DEEDS_KARMA_DESIGN.md section 11.15).

"Owning up and taking responsibility is a HUGE lesson for kids. Knowing you'll
face consequences, but choosing to confront that and tell the truth, is a big
part of being successful in life. ... A counterpoint is when the other side is
clearly not honest or just themselves; submitting to unjust 'justice' is also
not courage, it's surrender."

* Owning up is the hero's virtue: a gated +1 of kind 'owning', only where the
  deeds say the hero did the wrong, always at a real, visible cost, and always
  beside a quieter way out (pay back in silence, hide it, keep it).
* Submitting to an unjust authority never pays, and resisting or walking away
  from one never costs.
* The NPC stories of owning up (Oswin, Pell, Lucan) read as courage because the
  authority they face is honest; Boethius and Socrates no longer present
  submission to a lying court as the noble choice.

Data tests plus behaviour tests on a real headless Game. These are callbacks
10 to 90 floors deep, so they are proven here, not by play-test (CLAUDE.md).
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

import deeds  # noqa: E402
import encounter_schema as ES  # noqa: E402
from tools.encounters import validate as V  # noqa: E402

ALL = V.load_all()
BY_TAG = {e['tag']: e for _s, e in ALL}

# (encounter, the confession's label) -> the hero's wrong it answers.
OWNING = {
    ('flv_lena_returns', 'Tell her it was you, and pay back the bread too'):
        'wrong.robbed_marta',
    ('flv_ysolde_gate', 'Tell her you took the pendant from her girl, and give it back'):
        'wrong.kept_pendant',
    ('flv_grumwald_second_bridge', 'Wake him and tell him who emptied his box'):
        'wrong.robbed_grumwald',
    ('flv_aldric_cairn', 'Tell him it was you who drank it, and ask to carry the stone'):
        'wrong.took_cordial',
    ('flv_ruth_gale', 'Tell her you took it from his neck, and give it back'):
        'wrong.robbed_amos',
    # The Green Chapel (Part J11): before the Knight swings, or after his nick.
    ('flv_green_chapel', 'Tell him about the girdle before he swings'):
        'wrong.kept_girdle',
    ('flv_green_chapel', 'Tell him the truth about the girdle, and give it back'):
        'wrong.kept_girdle',
}
# The item a confession hands back needs to be in the hero's hands.
HOLDS = {'flv_ysolde_gate': 'silverlight_pendant', 'flv_ruth_gale': 'prophets_amulet',
         'flv_green_chapel': 'green_girdle'}
# A confession that comes after a step of its scene (the nick at the chapel).
STAGE = {('flv_green_chapel', 'Tell him the truth about the girdle, and give it back'):
         ['told.green_chapel_blow']}
# The showpiece is high stakes (an axe at the neck); the rest are medium.
HIGH = {'flv_green_chapel'}

UNJUST = {'grain_committee', 'live_not_by_lies', 'flv_witch_finder', 'flv_socrates_cell',
          'flv_last_philosopher', 'flv_exposed_child', 'flv_antigone'}
JUST = {'fallen_paladin', 'penitent', 'flv_green_chapel'}


def _opt(tag, label):
    return next(o for o in BY_TAG[tag]['options'] if o['label'] == label)


def _is_owning(o):
    return any(b.get('karma_kind') == 'owning' and int(b.get('karma', 0) or 0) > 0
               for b in ES.option_branches(o))


def _ctx(deed_ids=(), items=()):
    reg = deeds.new_register()
    for d in deed_ids:
        deeds.record(reg, d, floor=5, block=1, turn=0, source='test')
    return {'reg': reg, 'karma': 0, 'stats': {}, 'floor': 50, 'deepest': 50,
            'items': set(items), 'worn': set()}


# ------------------------------------------------------------------ data

def test_every_confession_is_pinned_and_none_is_stray():
    found = {(e['tag'], o['label']) for _s, e in ALL for o in e['options'] if _is_owning(o)}
    assert found == set(OWNING)


def test_a_confession_costs_something_and_answers_the_heros_own_wrong():
    for (tag, label), wrong in OWNING.items():
        e, o = BY_TAG[tag], _opt(tag, label)
        assert (o['karma'], o['karma_kind']) == (1, 'owning'), tag
        assert o.get('cost'), tag                                  # a real, visible price
        req = (o.get('requires') or {}).get('deeds_any') or (e.get('requires') or {}).get('deeds_any')
        assert req == [wrong], tag
        assert e['callback_only'], tag
        assert e['stakes'] == ('high' if tag in HIGH else 'medium'), tag  # a light scene pays nothing
        assert o.get('chronicle') and o.get('road', {}).get('hint'), tag
        assert 'tell' in label.lower(), label                      # the words are the act


def test_a_confession_shows_only_after_the_wrong_and_beside_a_quieter_way():
    for (tag, label), wrong in OWNING.items():
        e = BY_TAG[tag]
        held = [HOLDS[tag]] if tag in HOLDS else []
        step = STAGE.get((tag, label), [])
        vis = [o['label'] for _i, o in ES.visible_options(e, _ctx([wrong] + step, held))]
        assert label in vis, (tag, vis)
        # Never the only thing to do: a silent repayment, hiding it, keeping
        # it, or just walking on are all there too, and each pays nothing.
        others = [o for _i, o in ES.visible_options(e, _ctx([wrong] + step, held))
                  if o['label'] != label]
        assert len(others) >= 2, (tag, vis)
        assert all(ES.max_karma(o) == 0 for o in others), tag
        # A hero who did no wrong never sees it (the scene itself may be
        # what never comes: its requires gates the spawn).
        c = _ctx(['met.x'] + step, held)
        clean = [o['label'] for _i, o in ES.visible_options(e, c)]
        assert label not in clean or not deeds.check(e.get('requires') or {}, c), tag


def test_owning_up_is_a_choice_never_the_quiz_and_never_the_walk_away():
    for (tag, label) in OWNING:
        o = _opt(tag, label)
        assert not ES.is_quiz(o) and not V._is_free(o)


def test_each_confession_has_its_payoff_at_the_gate():
    with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as f:
        rows = json.load(f)['gate']['lines']
    owned = {'told.owned_up_to_lena', 'told.ysolde_owned_pendant', 'told.owned_up_to_aldric',
             'told.owned_up_to_grumwald', 'told.owned_up_to_ruth',
             'told.owned_up_to_green_knight'}
    seen = set()
    for (tag, label), wrong in OWNING.items():
        o = _opt(tag, label)
        c = _ctx([wrong] + list(o['deeds']))
        holding = [r for r in rows if deeds.check(r['when'], c)]
        mine = [r for r in holding if set(r['when'].get('deeds_all') or ()) & owned]
        assert len(mine) == 1, tag
        seen |= set(mine[0]['when']['deeds_all']) & owned
        # Of that person's lines, the confession's is the first that holds,
        # so it is the one the Gate tells (one line a person).
        first = next(r for r in holding if r['person'] == mine[0]['person'])
        assert first is mine[0], (tag, first['line'])
    assert seen == owned


def test_the_quiet_way_out_still_has_its_consequence_at_the_gate():
    with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as f:
        rows = json.load(f)['gate']['lines']
    hid = next(r for r in rows if 'told.ysolde_pendant_hidden' in json.dumps(r['when']))
    assert 'Elara told her mother' in hid['line']


def test_unjust_authorities_are_flagged_and_never_paid_for_submission():
    flagged = {t for t, e in BY_TAG.items() if (e.get('authority') or {}).get('just') is False}
    assert flagged == UNJUST
    honest = {t for t, e in BY_TAG.items() if (e.get('authority') or {}).get('just') is True}
    assert honest == JUST
    for tag in UNJUST:
        e = BY_TAG[tag]
        assert e['authority']['who'] and e['authority']['why']
        for o in e['options']:
            if o.get('submit'):
                assert ES.max_karma(o) <= 0, (tag, o['label'])
            low = min(int(b.get('karma', 0) or 0) for b in ES.option_branches(o))
            if low < 0:
                assert o.get('submit') or o.get('villain') or o.get('side') == 'wrong', \
                    (tag, o['label'])


def test_handing_an_innocent_to_an_unjust_authority_is_still_betrayal():
    o = _opt('grain_committee', 'Tell the commissar where the sack is')
    assert o['submit'] and (o['karma'], o['karma_kind']) == (-1, 'betray')


OSWIN_BACK = '"Go back up. Face the families of Thale, and tell the king\'s court about Ranulf."'


def test_npc_owning_up_faces_an_honest_authority_and_reads_as_courage():
    oswin = _opt('fallen_paladin', OSWIN_BACK)
    # The truth reaches the bishop whichever way the urging goes.
    assert oswin['submit'] and all('Ranulf' in oswin[b]['outcome'] for b in ('pass', 'fail'))
    # Brandon, 2026-10-18 (J11): urging him back is courage and pays, as a
    # stance; it is no longer contested. See test_green_chapel.py too.
    assert not BY_TAG['fallen_paladin'].get('contested')
    assert (oswin['pass']['karma'], oswin['pass']['karma_kind']) == (1, 'stance')
    lucan = _opt('penitent', 'Weigh mercy and justice with them both')
    assert lucan['submit'] and lucan['pass']['karma_kind'] == 'judgment'
    pell = next(v['text'] for v in BY_TAG['flv_ormonds_granary']['text_variants']
                if v['when'] == {'deeds_any': ['told.pell_aristodemus']})
    assert "told us he'd run" in pell


def test_boethius_is_not_shown_choosing_a_lying_court():
    e = BY_TAG['flv_last_philosopher']
    blob = json.dumps(e)
    assert 'door open' not in e['text'] and 'could walk out' not in blob
    assert 'running from a lie' not in blob and 'open cell' not in blob
    assert 'forged letters' in e['text'] and "I won't" in e['text']
    out = _opt('flv_last_philosopher', 'Break the bar and get him out')
    assert out.get('cost') and 'told.boethius_pages' in out['deeds']
    assert e['tragedy'] == 'unsavable' and 'saved.boethius' not in blob


def test_socrates_rescue_is_not_paid_less_and_the_lie_is_named():
    e = BY_TAG['flv_socrates_cell']
    assert e['contested'] and e['authority']['just'] is False
    carry = _opt('flv_socrates_cell', 'Carry him out by force')
    stay = _opt('flv_socrates_cell', 'Stay for the last conversation')
    assert carry.get('reward') and stay.get('reward')
    assert 'liars' in carry['outcome']
    arg = _opt('flv_socrates_cell', 'Argue with him, staking your strength')
    assert 'built on a lie' in arg['pass']['outcome']
    assert {ES.max_karma(o) for o in e['options']} == {0}         # contested: equal


def test_antigone_refuses_to_hide_rather_than_surrenders():
    o = _opt('flv_antigone', 'Help her finish the burial')
    assert 'does not hide' in o['outcome'] and 'agreeing with him' in o['outcome']
    assert 'does not run' not in o['outcome'] and "This part's mine" not in o['outcome']
    # Brandon, 2026-10-18 (J11): Creon's edict is an unjust authority. The
    # defensible answers stay equal (contested), informing is the one submit.
    e = BY_TAG['flv_antigone']
    assert e['contested'] and e['authority']['just'] is False
    assert [o['label'] for o in e['options'] if o.get('submit')] == ["Tell Creon's men where she is"]


def test_the_validator_and_the_report_agree():
    assert V.validate_all() == []
    assert {(t, lbl) for t, lbl, _w, _b, _cb in V.owning_report()} == set(OWNING)


# ------------------------------------------------------------------ behaviour

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=31):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_owning_up__')
    g.state = STATE_PLAYER
    g._npc_encounter_levels = {}
    g._flavor_encounter_levels = {}
    return g


def _def(tag):
    import economy
    import flavor_encounters
    import npc_encounters
    for e in list(flavor_encounters.FLAVOR_ENCOUNTERS) + list(npc_encounters.ENCOUNTERS):
        if e['tag'] == tag:
            return economy.price_encounter(copy.deepcopy(e))
    raise KeyError(tag)


def _go(g, floor):
    g._change_level(floor, enter_from_top=floor >= g.dungeon_level, via='stairs')
    g.monsters[:] = [m for m in g.monsters
                     if getattr(m, '_flavor_encounter_tag', None) or getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}


def _npc(g, tag):
    return next((m for m in g.monsters if m.alive and tag in (
        getattr(m, '_flavor_encounter_tag', None), getattr(m, '_npc_encounter_tag', None))), None)


def _meet(g, floor, tag, flavor=True):
    (g._flavor_encounter_levels if flavor else g._npc_encounter_levels)[floor] = _def(tag)
    _go(g, floor)
    npc = _npc(g, tag)
    assert npc is not None, tag
    return npc


def _choose_label(g, npc, label):
    """Open the encounter and pick the option shown with this label."""
    from game_states import STATE_PLAYER
    if getattr(npc, '_flavor_encounter_tag', None):
        assert g._start_flavor_encounter(npc)
    else:
        assert g._start_npc_encounter(npc)
    g._npc_encounter_input(pygame.K_RETURN)
    labels = [o['label'] for _i, o in g._npc_visible_options()]
    assert label in labels, labels
    g._npc_encounter_input(pygame.K_1 + labels.index(label))
    if g._npc_encounter_phase == 'select_item':
        g._npc_encounter_input(pygame.K_a)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    g._npc_encounter_input(pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    return labels


def _pending(g):
    return [p for p in g._deeds['pending'] if p['kind'] == 'encounter'
            and p.get('source') != 'engine:run_start']


def test_robbing_grumwald_then_owning_up_at_his_next_bridge():
    """The whole chain: empty the honesty box (-1), meet him again 10 to 20
    floors on, wake him and say it (a tenth of the purse, +1 owning)."""
    g = _game()
    k0 = g.karma
    troll = _meet(g, 5, 'grumwald_toll', flavor=False)
    _choose_label(g, troll, 'Empty the box')
    assert g.karma == k0 - 1 and deeds.has(g._deeds, 'wrong.robbed_grumwald')
    (cb,) = _pending(g)
    assert cb['spec']['encounter'] == 'flv_grumwald_second_bridge'
    _go(g, cb['target'])
    bridge = _npc(g, 'flv_grumwald_second_bridge')
    assert bridge is not None
    import economy
    g.player_gold = 1000
    price = economy.pct_cost(1000, 10, g.dungeon_level)        # a tenth, with its floor
    labels = _choose_label(g, bridge, 'Wake him and tell him who emptied his box')
    assert 'Pay the toll' in labels and 'Cross' in labels      # the quiet ways stay open
    assert price >= 100 and g.player_gold == 1000 - price       # the price was paid
    assert g.karma == k0                                        # the point back, not more
    assert deeds.has(g._deeds, 'told.owned_up_to_grumwald')
    assert deeds.count(g._deeds, tag='virtue:owned') == 1
    led = [e for e in g._deeds['karma']['ledger'] if e['kind'] == 'owning']
    assert len(led) == 1 and led[0]['applied'] == 1


def test_aldrics_stone_after_the_truth_and_the_honest_rule(monkeypatch):
    """Owning up twice, in two blocks, pays the 'honest' constancy point; the
    stone Aldric hands over is a real burden, and laying it on an altar pays
    no oath (none was sworn)."""
    from chronicle import text_of
    from dungeon import ALTAR
    g = _game(seed=32)
    g.player.hp = g.player.max_hp = 300
    reg = deeds.ensure_register(g)
    deeds.record(reg, 'wrong.robbed_grumwald', floor=5, block=1, turn=0, source='grumwald_toll')
    deeds.record(reg, 'wrong.took_cordial', floor=14, block=2, turn=0, source='sir_aldric')
    g.player_gold = 1000
    bridge = _meet(g, 18, 'flv_grumwald_second_bridge')
    _choose_label(g, bridge, 'Wake him and tell him who emptied his box')
    k1 = g.karma
    knight = _meet(g, 25, 'flv_aldric_cairn')
    labels = _choose_label(g, knight, 'Tell him it was you who drank it, and ask to carry the stone')
    assert 'Offer to take the stone now' in labels             # the offer without the truth
    assert any(getattr(i, 'id', '') == 'cursed_lodestone' for i in g.player.inventory)
    assert deeds.count(g._deeds, tag='virtue:owned') == 2
    assert 'honest' in g._deeds['karma']['constancy']
    assert g.karma == k1 + 2                                    # owning +1, then honest +1
    assert any('looked someone in the face' in text_of(e) for e in g._chronicle)
    assert g._deeds['people']['aldric']['status'] == 'aided'
    # The stone cannot be put down in a corridor, and breaks on an altar.
    k2 = g.karma
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR
    stone = next(i for i in g.player.inventory if i.id == 'cursed_lodestone')
    g._do_drop_item(stone)
    assert not any(getattr(i, 'id', '') == 'cursed_lodestone' for i in g.player.inventory)
    assert g.karma == k2 and deeds.oath_status(g._deeds, 'aldric_lodestone') is None


def test_a_confession_in_a_block_already_filled_pays_nothing_but_still_counts():
    import karma
    g = _game(seed=33)
    reg = deeds.ensure_register(g)
    deeds.record(reg, 'wrong.robbed_grumwald', floor=5, block=1, turn=0, source='grumwald_toll')
    g.player_gold = 1000
    _go(g, 18)
    karma.adjust(g, 1, kind='forgo', source='flv_three_purses')    # block 2's point, taken
    k = g.karma
    bridge = _meet(g, 19, 'flv_grumwald_second_bridge')
    _choose_label(g, bridge, 'Wake him and tell him who emptied his box')
    assert g.karma == k                                         # absorbed: one point a block
    assert deeds.count(g._deeds, tag='virtue:owned') == 1       # the act still counts
