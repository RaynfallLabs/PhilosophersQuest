"""The four horns of legend (Brandon, 2026-11-16): Robin Hood's Horn, Arthur's
Bugle, Gjallarhorn and the Olifant.

Each is a carried artifact that only its story path gives, and its use follows
the myth: one blow a run (his 2026-11-16 correction: "once per game... must not
be game-breaking"), a HISTORY escalator chain that sets how many answer,
allies with their own numbers from their lore at their horn's tier, who fight
beside the hero for their stay and go home. The Olifant's host rides from
thirty leagues off and comes late. No horn's allies ever strike a gate's
guardian: Fenrir is Gleipnir's to bind and the Sandal's to end.

The paths are mid- and late-game and the summons are once a run, so they are
proven here by data tests and headless games through the real quiz callback,
not by play-test (CLAUDE.md).
"""
import copy
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

import deeds  # noqa: E402
import encounter_schema as ES  # noqa: E402
import horns  # noqa: E402
from quiz_engine import QuizResult  # noqa: E402
from tools.encounters import validate as V  # noqa: E402

HORNS = ('robin_hoods_horn', 'arthurs_bugle', 'gjallarhorn', 'olifant')
PATHS = {'robin_hoods_horn': 'flv_robin_hood_bridge',
         'arthurs_bugle': 'flv_sleepers_under_the_hill',
         'gjallarhorn': 'flv_heimdalls_watch'}
GATE = ('asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf', 'abaddon_destroyer')


def _load(*rel):
    with open(os.path.join(ROOT, *rel), encoding='utf-8') as f:
        return json.load(f)


ART = _load('data', 'items', 'artifact.json')
MONS = _load('data', 'monsters.json')
FLV = {e['tag']: e for e in _load('data', 'flavor_encounters.json')}
RULES = _load('data', 'karma_rules.json')


def _png(folder, sid):
    p = os.path.join(ROOT, 'assets', 'tiles', folder, sid + '.png')
    assert os.path.isfile(p), p
    return pygame.image.load(p).get_size()


# ================================================================== data

@pytest.mark.parametrize('hid', HORNS)
def test_each_horn_is_a_plot_locked_artifact_never_found_at_random(hid):
    from items import scripted_only_ids
    from main import Game
    e = ART[hid]
    assert e['is_unique'] and e['min_level'] == 0 and e['_meta']['plot_locked']
    assert not e.get('peak_weight') and not e.get('floor_spawn_weight') and not e.get('floorSpawnWeight')
    assert e['special_properties']['plot_role'] and e['lore'] and e['_meta'].get('sources')
    assert hid in scripted_only_ids()                     # no chest, shop or floor roll
    assert hid in Game._QUEST_PIECE_IDS                   # traders refuse, thieves skip
    assert _png('items', hid) == (64, 64)
    assert ART[hid]['weight'] > 0


def test_the_horns_data_is_whole():
    seen = set()
    for hid in HORNS:
        h = horns.horn(hid)
        assert h['power'].startswith('horn_') and h['power'] not in seen
        seen.add(h['power'])
        assert h['quiz']['subject'] == 'history' and h['quiz']['mode'] == 'escalator_chain'
        assert h['quiz']['tier'] == h['tier'] and h['quiz']['max_chain'] == 5
        table = h['allies_by_chain']
        assert len(table) == 6 and table[0] == 0 and table == sorted(table) and table[1] >= 2
        assert len(h['roster']) >= table[-1]
        assert h['turns'] == 10                    # Brandon 2026-11-16: down from 25 and 30
        for key in ('raise', 'fail', 'arrive', 'leave', 'chronicle', 'chronicle_fail'):
            assert h['lines'].get(key), (hid, key)
        assert 'Once a run.' in h['desc'] and len(h['desc']) <= 100     # whole at the smallest window
    assert horns.delay('olifant') > 0 and horns.line('olifant', 'far') and horns.line('olifant', 'on_road')
    assert all(horns.delay(h) == 0 for h in HORNS if h != 'olifant')


def test_every_ally_is_a_written_kind_that_is_never_found():
    for kind in horns.ally_kinds():
        m = MONS[kind]
        assert m['is_allied'] and m['quest_only'] and m['frequency'] == 0
        assert m['peak_weight'] == 0 and m['min_level'] == 0 and not m.get('peak_floor')
        assert m['horn'] in HORNS and kind in horns.horn(m['horn'])['roster']
        assert m['lore'] and m['attacks'] and m['pronoun'] == 'he'
        assert _png('monsters', kind) == (64, 64)
    # the named are proper nouns; the rank and file are not
    assert MONS['little_john']['proper_noun'] and MONS['charlemagne']['proper_noun']
    assert not MONS['yeoman_archer'].get('proper_noun') and not MONS['einherjar'].get('proper_noun')


def _band_damage(hid):
    """Mean damage of the whole band at a full chain, per turn."""
    from sketch_manifest import mean_hp
    kinds = horns.allies_for(hid, 5)
    return sum(mean_hp({'hp': MONS[k]['attacks'][0]['damage']}) for k in kinds)


def test_the_allies_are_sized_from_their_tier_and_help_one_hard_fight():
    """LORE, NOT FLOOR: their numbers are written, and they rise with their
    horn's tier. Every stay is ten turns (Brandon, 2026-11-16: the old 25
    and 30 "may be too strong"), so a full band (about three turns in five at
    blows) deals about four or five ordinary monsters of its tier: a
    war-band's followers or a third of a mini-boss, still worth the call, and
    never a floor. (It was about a dozen at the old stays; the allies' own
    numbers did not change.)"""
    from floor_curve import target_hp
    floors = {'robin_hoods_horn': 15, 'arthurs_bugle': 50, 'gjallarhorn': 75, 'olifant': 90}
    per_turn = [_band_damage(h) for h in HORNS]
    assert per_turn == sorted(per_turn)
    for hid in HORNS:
        assert horns.turns(hid) == 10, hid
        stay = _band_damage(hid) * horns.turns(hid) * 0.6
        worth = stay / target_hp(floors[hid])
        assert 3.5 <= worth <= 6, (hid, round(worth, 1))
    # And mortals of tier one matter less the deeper they are called: the
    # same band against floor 90's monsters is a fraction of one.
    assert _band_damage('robin_hoods_horn') * horns.turns('robin_hoods_horn') * 0.6 < target_hp(90)


def test_the_olifant_tells_rolands_legend_so_the_lesson_is_plain():
    """Brandon, 2026-11-16: the kid must see he blows it early and falls
    back, and the lore must tell the legend (Roland too proud at Roncevaux,
    Charlemagne coming from far off, too late). Told in words, never as a
    count of turns: on the item, the power and the moment of sounding."""
    lore = ART['olifant']['lore']
    for words in ('Roncevaux', 'Oliver', 'too proud', 'thirty leagues', 'comes late',
                  'blow it before the fight', 'give ground'):
        assert words in lore, words
    h = horns.horn('olifant')
    assert 'blow it early, then fall back' in h['desc']
    assert 'Give ground, and hold on until it comes' in h['lines']['far']
    import re
    for text in (lore, h['desc'], h['lines']['far']):
        assert not re.search(r'\d', text), text           # the lesson, not the mechanic
    assert horns.delay('olifant') == 12                    # the delay itself stays


def test_the_three_paths_are_placed_once_a_run_on_their_floors():
    start = {s['encounter']: s['floors'] for s in RULES['run_start_schedule']}
    for hid, tag in PATHS.items():
        e = FLV[tag]
        assert e['callback_only'] and start[tag] == [e['min_level'], e['max_level']]
        rewards = [b.get('reward') for o in e['options'] for b in ES.option_branches(o)]
        assert {'type': 'specific_item', 'item_type': 'artifact', 'item_id': hid} in rewards
        assert sum(1 for r in rewards if r) == 1               # one way to earn it: the myth's
    assert (FLV['flv_robin_hood_bridge']['min_level'], FLV['flv_heimdalls_watch']['max_level']) == (12, 78)
    assert 45 <= FLV['flv_sleepers_under_the_hill']['min_level'] <= 55


def test_rolands_chain_is_kept_as_it_was():
    e = FLV['flv_rolands_horn']
    take = next(o for o in e['options'] if o['label'] == 'Swear to blow it at the Black Gate')
    assert take['cost'] == {'type': 'accept_item', 'item_id': 'olifant'}
    assert take['oath']['id'] == 'roland_horn' and take['schedule'][0]['encounter'] == 'flv_rolands_horn_gate'
    gate = FLV['flv_rolands_horn_gate']
    blow = next(o for o in gate['options'] if o.get('oath_keep') == 'roland_horn')
    assert blow['cost'] == {'type': 'triggered_item_id', 'item_id': 'olifant'}


def test_the_new_paths_pass_the_encounter_validator():
    issues = [i for i in V.validate_all() if any(t in str(i) for t in PATHS.values())]
    assert not issues, issues


def test_the_gjallarhorn_never_names_the_hidden_road_to_the_wolfs_end():
    """The Sandal is a deep hidden path (Brandon, 2026-11-14 and 2026-11-16):
    nothing here may point at the scraps."""
    words = ('scrap', 'cobbler', 'shoe', 'sandal', 'vidar')
    texts = [ART['gjallarhorn']['lore'], json.dumps(FLV['flv_heimdalls_watch']),
             json.dumps(horns.horn('gjallarhorn')), MONS['einherjar']['lore']]
    for t in texts:
        assert not any(w in t.lower() for w in words), t[:80]


# ================================================================== a headless game

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7, name='__test_horns__'):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    g._npc_encounter_levels = {}
    g._flavor_encounter_levels = {}
    g.player.hp = g.player.max_hp = 999
    return g


def _def(tag):
    import economy
    from game_road import _encounter_by_tag
    _src, e = _encounter_by_tag(tag)
    return economy.price_encounter(copy.deepcopy(e))


def _go(g, floor):
    from game_states import STATE_PLAYER
    g._change_level(floor, enter_from_top=floor >= g.dungeon_level, via='stairs')
    g.monsters[:] = [m for m in g.monsters
                     if getattr(m, '_flavor_encounter_tag', None) or getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER


def _npc(g, tag):
    return next((m for m in g.monsters if m.alive and getattr(m, '_flavor_encounter_tag', None) == tag),
                None)


def _meet(g, floor, tag):
    g._deeds['pending'] = [p for p in g._deeds['pending'] if p.get('source') != 'engine:run_start']
    g._flavor_encounter_levels[floor] = _def(tag)
    _go(g, floor)
    npc = _npc(g, tag)
    assert npc is not None, tag
    return npc


def _open(g, npc):
    from game_states import STATE_NPC_ENCOUNTER
    assert g._start_flavor_encounter(npc)
    assert g.state == STATE_NPC_ENCOUNTER
    if g._npc_encounter_phase == 'text':
        g._npc_encounter_input(pygame.K_RETURN)


def _labels(g):
    return [o['label'] for _i, o in g._npc_visible_options()]


def _pick(g, label, *, quiz=None):
    """Pick the option with this label; a quiz option is answered through the
    real callback (``quiz`` is the QuizResult). Lands on the outcome page."""
    labels = _labels(g)
    assert label in labels, labels
    g._npc_encounter_input(pygame.K_1 + labels.index(label))
    if quiz is not None:
        assert g.quiz_engine.callback is not None
        g.quiz_engine.callback(quiz)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    return labels


def _continue(g):
    g._npc_encounter_input(pygame.K_RETURN)


def _has(g, iid):
    return any(getattr(i, 'id', '') == iid for i in g.player.inventory)


PASS = QuizResult(success=True, score=3, correct=3, asked=3)
FAIL = QuizResult(success=False, score=0, correct=0, asked=1)


# ---------------------------------------------------------------- the paths

def test_the_run_puts_each_path_on_a_floor_of_its_band():
    g = _game(name='__test_horns_road__')
    start = {p['spec']['encounter']: p['target'] for p in g._deeds['pending']
             if p.get('source') == 'engine:run_start'}
    for tag in PATHS.values():
        lo, hi = FLV[tag]['min_level'], FLV[tag]['max_level']
        assert lo <= start[tag] <= hi, (tag, start[tag])
    # Walking down to Robin Hood's floor finds him there.
    tag = 'flv_robin_hood_bridge'
    for f in range(2, start[tag] + 1):
        _go(g, f)
    assert _npc(g, tag) is not None


def test_every_seed_finds_a_free_floor_for_every_path():
    """The run-start pick avoids the Road's busy slots and the set pieces'
    floors; a band always has one left."""
    g = _game(name='__test_horns_seeds__')
    for seed in range(40):
        random.seed(seed)
        g._deeds['pending'] = []
        g._init_road()
        start = {p['spec']['encounter']: p['target'] for p in g._deeds['pending']
                 if p.get('source') == 'engine:run_start'}
        busy = set(g._secret_floors())
        for tag in PATHS.values():
            assert FLV[tag]['min_level'] <= start[tag] <= FLV[tag]['max_level'], (seed, tag)
            assert start[tag] not in busy, (seed, tag)
        assert len(set(start.values())) == len(start)          # one floor each


def test_a_fair_bout_on_the_bridge_wins_robin_hoods_horn():
    g = _game(name='__test_horns_robin__')
    robin = _meet(g, 15, 'flv_robin_hood_bridge')
    _open(g, robin)
    assert _labels(g) == ['"A bow against a staff? That\'s a coward\'s fight."',
                          'Cut a staff and meet him on the bridge', 'Step back and let him cross']
    _pick(g, '"A bow against a staff? That\'s a coward\'s fight."')
    assert 'cuts a staff of oak' in g._npc_outcome_text
    _continue(g)
    _pick(g, 'Cut a staff and meet him on the bridge', quiz=PASS)
    assert 'into the stream' in g._npc_outcome_text and _has(g, 'robin_hoods_horn')
    assert g._deeds['threads']['robin_hoods_horn']['status'] == 'open'
    _continue(g)
    assert deeds.has(g._deeds, 'met.robin_hood')
    # Blown, the horn's thread in the Journal closes.
    _sound(g, 'robin_hoods_horn', 1)
    assert g._deeds['threads']['robin_hoods_horn']['status'] == 'closed'


@pytest.mark.parametrize('how', ['lose', 'give way'])
def test_losing_the_bout_or_giving_way_earns_no_horn(how):
    g = _game(name='__test_horns_robin_no__')
    _open(g, _meet(g, 15, 'flv_robin_hood_bridge'))
    if how == 'lose':
        _pick(g, 'Cut a staff and meet him on the bridge', quiz=FAIL)
        assert 'it is you who goes into the stream' in g._npc_outcome_text
    else:
        _pick(g, 'Step back and let him cross')
    _continue(g)
    assert not _has(g, 'robin_hoods_horn')


def test_draw_cut_and_blow_wakes_the_sleepers_and_arthur_gives_the_bugle():
    g = _game(name='__test_horns_arthur__')
    _open(g, _meet(g, 50, 'flv_sleepers_under_the_hill'))
    assert _labels(g) == ['Draw the sword', 'Let the sleepers sleep']
    _pick(g, 'Draw the sword')
    assert 'every eye in the hall opens' in g._npc_outcome_text
    _continue(g)
    assert _labels(g) == ['Cut the garter with it', 'Put the sword back and go']
    _pick(g, 'Cut the garter with it')
    _continue(g)
    assert _labels(g) == ['Blow the bugle', 'Sheathe the sword']
    _pick(g, 'Blow the bugle', quiz=PASS)
    assert 'When your need is greatest' in g._npc_outcome_text and _has(g, 'arthurs_bugle')
    _continue(g)


def test_sheathing_the_sword_closes_the_hall_as_the_rhyme_says():
    g = _game(name='__test_horns_arthur_rhyme__')
    _open(g, _meet(g, 50, 'flv_sleepers_under_the_hill'))
    _pick(g, 'Draw the sword')
    _continue(g)
    _pick(g, 'Cut the garter with it')
    _continue(g)
    _pick(g, 'Sheathe the sword')
    assert 'But never blew the bugle-horn.' in g._npc_outcome_text
    _continue(g)
    assert not _has(g, 'arthurs_bugle')
    assert 'flv_sleepers_under_the_hill' in g._encountered_flavor_npcs


def test_a_weak_blow_lets_them_sleep_on():
    g = _game(name='__test_horns_arthur_weak__')
    _open(g, _meet(g, 50, 'flv_sleepers_under_the_hill'))
    for label in ('Draw the sword', 'Cut the garter with it'):
        _pick(g, label)
        _continue(g)
    _pick(g, 'Blow the bugle', quiz=FAIL)
    _continue(g)
    assert not _has(g, 'arthurs_bugle')


def test_keeping_the_watch_with_heimdall_earns_gjallarhorn():
    g = _game(name='__test_horns_heimdall__')
    _open(g, _meet(g, 74, 'flv_heimdalls_watch'))
    _pick(g, '"What is the horn?"')
    assert 'einherjar' in g._npc_outcome_text
    _continue(g)
    _pick(g, 'Keep the watch with him', quiz=PASS)
    assert 'cannot ride against the wolf himself' in g._npc_outcome_text and _has(g, 'gjallarhorn')
    _continue(g)


def test_hearing_nothing_on_the_watch_earns_nothing():
    g = _game(name='__test_horns_heimdall_deaf__')
    _open(g, _meet(g, 74, 'flv_heimdalls_watch'))
    _pick(g, 'Keep the watch with him', quiz=FAIL)
    _continue(g)
    assert not _has(g, 'gjallarhorn')


# ---------------------------------------------------------------- the power

def _give(g, hid):
    from items import make_item_by_id
    it = make_item_by_id('artifact', hid)
    g.player.inventory.append(it)
    return it


def _sound(g, hid, chain):
    """V, the horn, then its quiz through the real callback."""
    from game_states import STATE_QUIZ
    g._open_power_menu()
    pids = [p[0] for p in g._power_menu_list]
    pid = horns.power_id(hid)
    assert pid in pids, pids
    g._power_menu_input(pygame.K_a + pids.index(pid))
    assert g.state == STATE_QUIZ
    q = g.quiz_engine
    assert (q.subject, getattr(q.mode, 'value', q.mode), q.tier, q.max_chain) == (
        'history', 'escalator_chain', horns.horn(hid)['tier'], 5)
    q.callback(QuizResult(success=chain > 0, score=chain, correct=chain, asked=max(1, chain)))


def _called(g):
    return [p for p in g.pets if getattr(p, 'is_called', False) and p.alive]


def _log(g):
    return ' '.join(str(e[0]) for e in g.msg_log.entries)


@pytest.mark.parametrize('chain', [0, 1, 3, 5])
def test_robin_hoods_horn_the_chain_decides_how_many_come(chain):
    import pet_system
    g = _game(name='__test_horns_robin_call__')
    _go(g, 16)
    _give(g, 'robin_hoods_horn')
    _sound(g, 'robin_hoods_horn', chain)
    came = _called(g)
    assert [a.ally_kind for a in came] == horns.allies_for('robin_hoods_horn', chain)
    assert len(came) == horns.ally_count('robin_hoods_horn', chain)
    if chain:
        assert came[0].name == 'Little John'
        assert not any(pet_system.is_companion(a) for a in came)
        assert all(max(abs(a.x - g.player.x), abs(a.y - g.player.y)) <= 3 for a in came)
    # spent either way: once a run
    g._power_menu_list = []
    g._open_power_menu()
    assert horns.power_id('robin_hoods_horn') not in [p[0] for p in getattr(g, '_power_menu_list', [])]
    assert not horns.ready(g.player, 'robin_hoods_horn')


def test_a_spent_horn_will_not_sound_again_and_costs_no_turn():
    g = _game(name='__test_horns_twice__')
    _go(g, 16)
    _give(g, 'robin_hoods_horn')
    _sound(g, 'robin_hoods_horn', 2)
    turn = g.turn_count
    assert g._activate_horn(horns.power_id('robin_hoods_horn')) is True
    assert g.turn_count == turn and 'sounded once already' in _log(g)
    assert len(_called(g)) == 3


def test_the_called_fight_beside_the_hero_and_go_home_when_their_stay_is_over():
    from monster import Monster
    g = _game(name='__test_horns_fight__')
    _go(g, 16)
    _give(g, 'robin_hoods_horn')
    _sound(g, 'robin_hoods_horn', 1)
    john = next(a for a in _called(g) if a.ally_kind == 'little_john')
    assert (john.max_hp, john.bite_type) == (110, 'blunt')
    d = dict(MONS['giant_rat'], id='giant_rat')
    spot = next((john.x + dx, john.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1))
                if g.dungeon.is_walkable(john.x + dx, john.y + dy)
                and (john.x + dx, john.y + dy) not in g._occupants())
    rat = Monster(d, *spot)
    rat.hp = rat.max_hp = 10000
    g.monsters.append(rat)
    g._do_pet_turns()
    assert rat.hp < 10000                                  # struck by his own dice
    for _ in range(horns.turns('robin_hoods_horn') + 1):
        g._do_pet_turns()
    assert not _called(g)
    assert 'goes back into the greenwood' in _log(g)


def test_the_called_stay_on_the_floor_they_were_called_to():
    g = _game(name='__test_horns_floor__')
    _go(g, 50)
    _give(g, 'arthurs_bugle')
    _sound(g, 'arthurs_bugle', 2)
    assert [a.name for a in _called(g)] == ['King Arthur', 'Sir Bedivere', 'Sir Kay']
    _go(g, 51)
    assert not _called(g) and not any(getattr(p, 'is_called', False) for p in g.pets)
    assert 'back to sleep under the hill' in _log(g)


def test_the_olifants_host_comes_from_thirty_leagues_off_and_late():
    g = _game(name='__test_horns_olifant__')
    _go(g, 88)
    _give(g, 'olifant')
    _sound(g, 'olifant', 3)
    assert not _called(g)                                  # nobody yet: they are far off
    assert 'Thirty leagues off' in _log(g)
    wait = horns.delay('olifant')
    left = horns.due(g.player)['olifant'][0]
    assert left == wait - 1                                # the turn of the call has passed
    while horns.due(g.player):
        assert not _called(g)
        g._horn_tick()
    came = _called(g)
    assert [a.ally_kind for a in came] == horns.allies_for('olifant', 3)
    assert came[0].name == 'Charlemagne'
    assert 'Hooves behind you' in _log(g) and 'too late for Roland' in _log(g)
    # The oath at the Black Gate still stands: the horn is still in the pack.
    assert _has(g, 'olifant')


def test_a_failed_call_spends_the_horn_and_says_so():
    g = _game(name='__test_horns_fail__')
    _go(g, 74)
    _give(g, 'gjallarhorn')
    _sound(g, 'gjallarhorn', 0)
    assert not _called(g) and not horns.ready(g.player, 'gjallarhorn')
    assert 'groans' in _log(g)
    assert any('Nobody in Valhalla heard it' in str(e.get('text', '')) for e in g._chronicle)


def test_the_einherjar_never_kill_fenrir_nor_any_gate_guardian():
    """They fight his kin; the wolf is Gleipnir's and the Sandal's."""
    from monster import Monster
    g = _game(name='__test_horns_fenrir__')
    _go(g, 78)
    _give(g, 'gjallarhorn')
    _sound(g, 'gjallarhorn', 5)
    band = _called(g)
    assert len(band) == 8 and all(a.available_specials() == [] for a in band)   # no binding
    def _free_around(m):
        ts = [(m.x + dx, m.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
        return [t for t in ts if g.dungeon.is_walkable(*t) and t not in g._occupants()]
    # A band of eight can crowd a corridor and box its first man in (seeds 12
    # and 36 left him fewer than two free tiles): the wolf and the rat stand
    # beside whichever of them has room.
    _a, free = max(((m, _free_around(m)) for m in band), key=lambda p: len(p[1]))
    assert len(free) >= 2, free
    wolf = Monster(dict(MONS['fenrir_wolf'], id='fenrir_wolf'), *free[0])
    wolf.hp = 1                                            # one blow would end him
    kin = Monster(dict(MONS['giant_rat'], id='giant_rat'), *free[1])
    kin.hp = kin.max_hp = 10000
    g.monsters += [wolf, kin]
    for _ in range(5):
        g._do_pet_turns()
    assert wolf.alive and wolf.hp == 1
    assert kin.hp < 10000
    for kind in GATE:
        boss = Monster(dict(MONS[kind], id=kind), 0, 0)
        assert not horns.strikes(boss), kind
    assert horns.gate_guardians() == frozenset(GATE)


def test_the_item_card_says_what_the_horn_does_and_whether_it_is_spent():
    g = _game(name='__test_horns_card__')
    _go(g, 88)
    it = _give(g, 'olifant')
    words = [t for t, _c, _f in g._lore_item_mechanic_lines(it, 5)]
    assert 'Horn of legend' in words and 'Power (V): Blow the Olifant' in words
    assert 'Ready, once a run' in words
    assert 'They come late, from far off: blow it before the fight' in words
    assert not any('12' in w for w in words)              # the lesson, not a count
    assert "They never strike a gate's guardian" in words
    _sound(g, 'olifant', 2)
    assert 'On the road to you' in [t for t, _c, _f in g._lore_item_mechanic_lines(it, 5)]


def test_the_hud_shows_a_horn_ready_and_a_host_on_the_road():
    import hud_context
    g = _game(name='__test_horns_hud__')
    _go(g, 88)
    _give(g, 'olifant')
    rows = {r.label: r.status for r in hud_context.active_power_rows(g.player)}
    assert rows.get('The Olifant') == '1 Use'
    _sound(g, 'olifant', 2)
    rows = {r.label: r.status for r in hud_context.active_power_rows(g.player)}
    assert rows.get('The Olifant', '').startswith('Coming')


def test_the_called_survive_a_save_and_an_old_save_has_every_horn_unblown():
    import player as player_mod
    g = _game(name='__test_horns_save__')
    _go(g, 16)
    _give(g, 'robin_hoods_horn')
    _sound(g, 'robin_hoods_horn', 2)
    back = pickle.loads(pickle.dumps((g.player, g.pets)))
    pl, pets = back
    assert horns.sounded(pl) == {'robin_hoods_horn'}
    called = [p for p in pets if getattr(p, 'is_called', False)]
    assert [a.name for a in called] == ['Little John', 'Will Scarlet', 'Yeoman Archer']
    assert called[0].turns_remaining == horns.turns('robin_hoods_horn') - 1
    # A hero saved before the horns: no horn state at all, nothing sounded.
    old = player_mod.Player.__new__(player_mod.Player)
    assert horns.sounded(old) == set() and horns.due(old) == {} and horns.ready(old, 'olifant')
    # An ally pickled without its stay reads as gone at the next tick.
    a = called[0]
    state = dict(a.__dict__)
    state.pop('turns_remaining')
    b = horns.CalledAlly.__new__(horns.CalledAlly)
    b.__setstate__(state)
    assert b.tick_duration() is True


def test_thieves_and_traders_leave_a_horn_alone():
    import theft
    import traders
    from items import withheld
    from main import Game
    g = _game(name='__test_horns_thief__')
    for hid in HORNS:
        it = _give(g, hid)
        assert withheld(it)
        assert traders.is_quest_piece(it, Game._QUEST_PIECE_IDS)
    assert not any(getattr(i, 'id', '') in HORNS for i in theft.stealable(g.player))


def test_the_qa_key_sets_each_path_beside_the_hero_then_every_horn_ready():
    import game_horns
    g = _game(name='__test_horns_qa__')
    g.player.qa_tools = True
    _go(g, 20)
    for tag in game_horns.QA_PATHS:
        g._qa_horns()
        npc = _npc(g, tag)
        assert npc is not None, tag
        assert max(abs(npc.x - g.player.x), abs(npc.y - g.player.y)) <= 3
    g.player.horns_sounded = {'olifant'}
    g._qa_horns()
    assert all(_has(g, h) for h in HORNS) and horns.sounded(g.player) == set()
    g._open_power_menu()
    assert {horns.power_id(h) for h in HORNS} <= {p[0] for p in g._power_menu_list}


# ---------------------------------------------------------------- the Seeker

@pytest.fixture
def seeker(tmp_path):
    import seeker_codes
    import seeker_profile
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved


def _won(g, aid):
    return g._seeker is not None and g._seeker.profile.is_unlocked(aid)


def test_each_path_won_the_myths_way_is_its_achievement(seeker):
    """Brandon, 2026-11-16: the achievements point at the three paths. Each
    fires on its path's own deed, through the real encounter."""
    g = _game(name='__test_horns_badges__')
    assert g._seeker is not None
    _open(g, _meet(g, 15, 'flv_robin_hood_bridge'))
    _pick(g, 'Cut a staff and meet him on the bridge', quiz=PASS)
    _continue(g)
    assert _won(g, 'neither_would_give_way')
    _open(g, _meet(g, 50, 'flv_sleepers_under_the_hill'))
    for label in ('Draw the sword', 'Cut the garter with it'):
        _pick(g, label)
        _continue(g)
    assert not _won(g, 'not_yet_the_hour')               # two of the three is not the waking
    _pick(g, 'Blow the bugle', quiz=PASS)
    _continue(g)
    assert _won(g, 'not_yet_the_hour')
    _open(g, _meet(g, 74, 'flv_heimdalls_watch'))
    _pick(g, 'Keep the watch with him', quiz=PASS)
    _continue(g)
    assert _won(g, 'one_who_listens')


def test_a_path_lost_or_left_is_no_achievement(seeker):
    g = _game(name='__test_horns_no_badges__')
    _open(g, _meet(g, 15, 'flv_robin_hood_bridge'))
    _pick(g, 'Cut a staff and meet him on the bridge', quiz=FAIL)
    _continue(g)
    _open(g, _meet(g, 50, 'flv_sleepers_under_the_hill'))
    for label in ('Draw the sword', 'Cut the garter with it'):
        _pick(g, label)
        _continue(g)
    _pick(g, 'Sheathe the sword')
    _continue(g)
    _open(g, _meet(g, 74, 'flv_heimdalls_watch'))
    _pick(g, 'Leave him to his watch')
    _continue(g)
    for aid in ('neither_would_give_way', 'not_yet_the_hour', 'one_who_listens'):
        assert not _won(g, aid), aid


def test_the_path_achievements_point_at_the_source_not_the_mechanic():
    """Very light hints that name the ballad, the legend or the Eddas, never
    the quiz, the horn or the hero's part; each lists its spoiler words."""
    data = _load('data', 'achievements.json')
    by = {a['id']: a for a in data['achievements']}
    sources = {'neither_would_give_way': 'ballad', 'not_yet_the_hour': 'Roman Wall',
               'one_who_listens': 'Eddas'}
    for aid, source in sources.items():
        a = by[aid]
        assert a['category'] == 'secrets' and source in a['hint'], aid
        assert len(a['hint']) <= 120, aid
        low = a['hint'].lower()
        assert a['spoiler_words'] and not any(w in low for w in a['spoiler_words']), aid
        for word in ('quiz', 'math', 'history', 'chain', 'horn', 'win', 'beat'):
            assert not __import__('re').search(rf'\b{word}\b', low), (aid, word)
