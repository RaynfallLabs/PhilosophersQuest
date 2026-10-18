"""Bug bash 5, content angle: encounter data fixes (CON-01, 05, 07, 10-14,
17-21). Each test names its finding in _bugbash_2026_10_17/content/FINDINGS.md."""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))


def _load(rel):
    with open(os.path.join(ROOT, *rel.split('/')), encoding='utf-8') as f:
        return json.load(f)


FLV = _load('data/flavor_encounters.json')
NPC = _load('data/npc_encounters.json')
ALL = FLV + NPC


def _enc(tag):
    (e,) = [x for x in ALL if x['tag'] == tag]
    return e


def _opt(enc, label_start):
    (o,) = [x for x in enc['options'] if x['label'].startswith(label_start)]
    return o


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def _fights(o):
    if isinstance(o, dict):
        if 'fight' in o:
            f = o['fight']
            for e in (f if isinstance(f, list) else [f]):
                yield e if isinstance(e, str) else e['monster_id']
        for v in o.values():
            yield from _fights(v)
    elif isinstance(o, list):
        for v in o:
            yield from _fights(v)


# ---------------------------------------------------------------- CON-01

def test_con01_moaning_woman_fights_a_deadite_sized_for_her_floors():
    import respawn_by_hp as r
    mons = _load('data/monsters.json')
    enc = _enc('deadite_woman')
    fights = list(_fights(enc))
    assert fights and set(fights) == {'fresh_deadite'}
    d = mons['fresh_deadite']
    # Encounter-only, never in a random pool.
    assert d['frequency'] == 0 and d['peak_weight'] == 0 and d['quest_only']
    hp = r.dice_avg(d['hp'])
    lo, hi = enc['min_level'], enc['max_level']
    # Dangerous on floor 5 (more than a band monster) but well short of the
    # floor-25 Deadite, and inside the HP the encounter's floors are built for.
    assert r.target_hp(lo) < hp < r.target_hp(hi)
    assert hp < r.dice_avg(mons['deadite']['hp']) / 3
    # Seated by respawn_by_hp's own rules on the floor its HP was built for.
    peak = r.fit_floor(hp)
    assert (d['peak_floor'], d['spread'], d['min_level']) == (
        peak, r.spread_for(peak), max(1, peak - r.lead_for(peak)))
    assert lo <= d['peak_floor'] <= hi
    # The same creature as the Deadite, newly possessed.
    for k in ('resistances', 'weaknesses', 'symbol'):
        assert d[k] == mons['deadite'][k]
    assert 'Deadite' in d['lore'] and len(d['lore']) > 120
    from game_magic import _monster_defn
    from monster import Monster
    m = Monster(_monster_defn('fresh_deadite'), 0, 0)
    assert m.max_hp >= 1 and m.kind == 'fresh_deadite'


def test_con01_fresh_deadite_has_the_deadite_picture():
    path = os.path.join(ROOT, 'assets', 'tiles', 'monsters', 'fresh_deadite.png')
    with open(path, 'rb') as f, open(os.path.join(
            ROOT, 'assets', 'tiles', 'monsters', 'deadite.png'), 'rb') as g:
        assert f.read() == g.read()
    assert 'fresh_deadite' in _load('tools/content/genart/installed.json')
    assert _load('data/monster_sizes.json')['sizes']['fresh_deadite'] == 'medium'


def test_con01_fresh_deadite_never_spawns_at_random():
    import dungeon as dungeon_mod
    for floor in (5, 10, 18):
        assert 'fresh_deadite' not in dungeon_mod._build_spawn_pool(floor)


# ---------------------------------------------------------------- CON-05

@pytest.mark.parametrize('tag,label,pct', [
    ('flv_ancient_guardian_chess', "Answer the Warden's sums", 25),
    ('flv_samsons_riddle', 'Answer it yourself', 20),
])
def test_con05_stake_is_taken_only_on_a_loss(tag, label, pct):
    o = _opt(_enc(tag), label)
    assert 'cost' not in o
    assert 'cost' not in o['pass']
    assert o['fail']['cost'] == {'type': 'gold_pct', 'amount': pct}


# ---------------------------------------------------------------- CON-07

def test_con07_chapel_options_go_once_the_book_is_laid():
    import deeds
    from encounter_schema import visible_options
    enc = _enc('flv_cuthbert_chapel')
    reg = deeds.new_register()
    deeds.swear(reg, 'cuthbert_gospel', to='Brother Sacristan', what='carry it',
                floor=40, block=4)
    ctx = {'reg': reg, 'deepest': 50}
    before = [o['label'] for _i, o in visible_options(enc, ctx)]
    assert any(lbl.startswith('Tell him a bearer') for lbl in before)
    deeds.record(reg, 'told.gospel_laid', floor=50, block=5)
    after = [o['label'] for _i, o in visible_options(enc, ctx, used={0})]
    assert after == ['Read the first lines aloud with him']


def test_con07_fiddler_refusal_does_not_claim_you_never_read():
    enc = _enc('flv_crossroads_fiddler')
    read = _opt(enc, 'Read the small print')
    assert read['fail'].get('then') == 'options'
    refuse = enc['options'][2]
    assert 'without reading' not in refuse['label'].lower()
    assert 'never did find out what was in it' not in refuse['chronicle']


# ---------------------------------------------------------------- CON-10, CON-11

def _setne_senet():
    return _opt(_enc('flv_setne_tomb'), 'Play Neferkaptah at senet')


def test_con10_total_loss_shows_one_rescue():
    o = _setne_senet()
    last = o['per_miss'][2]['text']
    assert 'Ahwere' not in last and 'pull' not in last
    assert 'pulls' in o['fail_by_correct']['0']['outcome']


def test_con11_no_lost_round_asks_for_more_control_than_the_cap():
    from status_effects import CONTROL_CAP
    over = []

    def walk(x, where):
        if isinstance(x, dict):
            eff = x.get('effect')
            if isinstance(eff, str) and eff in CONTROL_CAP and 'duration' in x:
                if int(x['duration']) > CONTROL_CAP[eff]:
                    over.append((where, eff, x['duration']))
            for k, v in x.items():
                walk(v, f'{where}.{k}')
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f'{where}[{i}]')
    for e in ALL:
        for i, o in enumerate(e.get('options') or ()):
            walk(o.get('per_miss') or [], f"{e['tag']}.options[{i}].per_miss")
    assert not over, over
    assert _setne_senet()['per_miss'][1]['effect'] == {'effect': 'paralyzed', 'duration': 4}


# ---------------------------------------------------------------- CON-12

def test_con12_priced_labels_name_the_price_once():
    import economy
    bad = []
    for e in ALL:
        priced = economy.price_encounter(e)
        for o in priced['options']:
            cost = o.get('cost')
            if isinstance(cost, dict) and cost.get('type') == 'gold':
                # The engine adds "(N Gold)"; a label that also says "(gold)",
                # "(pay gold)" or "for sixty gold" names the price twice.
                if re.search(r'\((pay )?gold\)|\bfor [a-z-]+ gold\b', o['label'], re.I):
                    bad.append(o['label'])
    assert not bad, bad


# ---------------------------------------------------------------- CON-13

def test_con13_amounts_in_text_match_the_mechanics():
    text = ' '.join(_strings([_enc('grumwald_toll'), _enc('flv_grumwald_second_bridge')]))
    assert 'COPPER' not in text
    broker = ' '.join(_strings(_enc('flv_relic_broker')))
    assert 'four hundred crowns' not in broker
    give = _opt(_enc('flv_moneylender_purse'), 'Give Fisk his purse')
    assert 'reward' not in give
    assert not re.search(r'\b(single|one) coin\b', give['outcome'] + give['chronicle'])


# ---------------------------------------------------------------- CON-14

def test_con14_seraph_text_names_the_monster_that_fights():
    enc = _enc('trapped_seraph')
    assert set(_fights(enc)) == {'war_troll'}
    text = ' '.join(_strings(enc))
    assert 'ogre' not in text.lower()
    assert 'trolls' in text


# ---------------------------------------------------------------- CON-17

def test_con17_prophet_is_never_the_anchor_on_floor_98():
    import npc_encounters
    import road
    prophet = [e for e in npc_encounters.ENCOUNTERS if e['tag'] == 'dying_prophet'][0]
    assert prophet['band'][1] <= 97
    on_98 = 0
    for seed in range(400):
        st = road.new_state(seed, enabled=True)
        placed = road.bind_anchors(st, npc_encounters.ENCOUNTERS)
        for f, e in placed.items():
            if f == 98:
                on_98 += 1
            if e['tag'] == 'dying_prophet':
                assert f <= 97, seed
    assert on_98, 'no seed put an anchor on floor 98; the test proves nothing'


def test_con17_legacy_placement_respects_the_band():
    """The old (Road off) placement, used by saves from before the Road."""
    import npc_encounters
    seen = set()
    for seed in range(300):
        placed = npc_encounters.select_encounter_levels(seed)
        for f, e in placed.items():
            if e['tag'] == 'dying_prophet':
                seen.add(f)
            lo, hi = e.get('band') or (1, 100)
            assert lo <= f <= hi, (seed, e['tag'], f)
    assert seen and max(seen) <= 97


# ---------------------------------------------------------------- CON-18, CON-19

def test_con18_the_brothers_named_astrid_on_every_branch():
    text = ' '.join(_strings(_enc('flv_exposed_child')))
    assert 'Her mother named her Astrid' not in text
    assert 'They named her Astrid."' not in text      # a Brother speaking says "We"


def test_con19_one_person_one_name():
    names = {}
    for e in ALL:
        p = e.get('person')
        if isinstance(p, dict) and p.get('id'):
            names.setdefault(p['id'], set()).add(p.get('name'))
    split = {k: v for k, v in names.items() if len(v) > 1}
    assert not split, split
    assert names['pell'] == {'Jory Pell'}
    assert names['oswin'] == {'Sir Oswin of Harrow'}


# ---------------------------------------------------------------- CON-20

def test_con20_lint_catches_spelled_out_floors():
    import chronicle
    assert 'game term' in chronicle.lint('He is sixty floors off.')
    assert 'game term' in chronicle.lint('He once reached the ninety-second floor.')
    assert 'game term' in chronicle.lint('Went down two floors.')
    assert 'game term' in chronicle.lint('I woke on the third floor.')
    assert chronicle.lint('I woke higher up. The stair was a few floors down.') == []
    assert chronicle.lint('The floor gave way.') == []


def test_con20_text_has_no_floor_counts_or_engine_words():
    text = ' '.join(_strings(ALL))
    for bad in ('sixty floors off', 'ninety-second floor', 'I regenerate now',
                'a floor higher'):
        assert bad not in text, bad


# ---------------------------------------------------------------- CON-21

def test_con21_prose_contradictions():
    text = ' '.join(_strings(ALL))
    assert 'Two brothers, and then one stranger' not in text
    assert 'Captain Creon' not in text
    assert 'a enchanted' not in text
    assert 'two short' not in text
    assert 'gone home.' not in _load('data/setne_tomb.json')['altar']['on_time_chronicle'] \
        or 'had gone home' in _load('data/setne_tomb.json')['altar']['on_time_chronicle']
    tib = ' '.join(_strings(_enc('flv_apprentice_alchemist')))
    assert not re.search(r'\b(she|her)\b', tib)
    finch = ' '.join(_strings(_enc('flv_plague_doctor')))
    # Doctor Finch is a man: "he", never singular they (Brandon, 2026-10-18).
    assert re.search(r'\b(he|him|his)\b', finch, re.I)
    assert not re.search(r'\b(they|their|she|her)\b', finch, re.I)
    quill = _enc('last_merchant')['escorts']['escort_quill']
    assert quill['on_arrive']['outcome'].strip()
    az = _enc('flv_azarias')['escorts']['escort_azarias']
    # Killed: the text owns the fall; left behind: he is simply gone.
    assert 'not there' in az['on_fail']['outcome'] and 'down' in az['on_fail']['outcome']
    (v,) = az['on_fail_variants']
    assert v['when'] == {'deeds_all': ['flag.escort_left_behind.azarias']}


def test_con21_setne_late_message_is_not_a_journal_line():
    al = _load('data/setne_tomb.json')['altar']
    assert not re.search(r'\bI\b', al['late_message'])


# ---------------------------------------------------------------- CON-01 (behaviour)

def test_con01_say_the_words_raises_two_fresh_deadites_on_a_real_game(monkeypatch, tmp_path):
    """The reviewer's floor-5 case: "Say the words" used to raise two 265-HP
    Deadites against a 45-HP hero."""
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import pygame
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    pygame.init()
    from main import Game
    from game_states import STATE_PLAYER
    import items
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb5_con01__')
    g.state = STATE_PLAYER
    g._change_level(5, enter_from_top=True)
    g.monsters = []
    words = _opt(_enc('deadite_woman'), 'Say the words')
    spawned = g._spawn_outcome_fight(words['fight'])
    assert [m.kind for m in spawned] == ['fresh_deadite', 'fresh_deadite']
    for m in spawned:
        assert 20 <= m.max_hp <= 100            # 11d8+10: 21 to 98
        assert all(a['damage'] in ('1d6+1', '1d4+1') for a in m.attacks)
