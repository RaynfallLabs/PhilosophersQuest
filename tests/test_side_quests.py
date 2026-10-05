"""Data-layer tests for the side quests added in the 2026-10 quest pass, and
for the encounter data in general.

These encounters appear in roughly one run in four or five each, so they
cannot be play-tested on demand. The tests check that every piece of data
uses only machinery with a real handler, and that the linked chains can never
be placed out of order.
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()


def _load(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


FLAVOR = _load('flavor_encounters.json')
NPCS = _load('npc_encounters.json')
MONSTERS = _load('monsters.json')

# Types with a handler in game_encounters._apply_npc_choice / can_pay_cost.
COST_TYPES = {'food', 'healing_potion', 'potion', 'scroll', 'weapon', 'gold',
              'hp_percent', 'max_hp', 'sp', 'hp', 'mp', 'random_item',
              'triggered_item', 'accept_item', 'spawn_deadite_ambush'}
# Types with a handler in game_encounters._apply_npc_reward.
REWARD_TYPES = {'gold', 'random_weapon', 'random_armor', 'random_shield',
                'random_accessory', 'random_potion', 'random_scroll',
                'random_food', 'random_wand', 'stat', 'specific_item',
                'random_item', 'effect', 'hp_restore', 'sp_restore',
                'mp_restore', 'enchant_weapon', 'message', 'multi'}

NEW_FLAVOR_TAGS = ['flv_baucis_table', 'flv_three_purses', 'flv_utgard_contests',
                   'flv_singed_squire', 'flv_old_spearman', 'flv_limping_lion',
                   'flv_lion_remembers', 'flv_coffin_bearer', 'flv_relic_broker',
                   'flv_cuthbert_chapel', 'flv_watch_post']


def _all_item_ids():
    ids = set()
    for name in os.listdir(os.path.join(ROOT, 'data', 'items')):
        if name.endswith('.json'):
            data = _load('items', name)
            if isinstance(data, dict):
                ids |= set(data)
    return ids


def _rewards(reward):
    if not reward:
        return
    yield reward
    for sub in reward.get('rewards', []) or []:
        yield from _rewards(sub)


@pytest.mark.parametrize('source,encounters', [('flavor', FLAVOR), ('npc', NPCS)])
def test_every_option_uses_only_handled_costs_and_rewards(source, encounters):
    from status_effects import EFFECT_INFO
    items = _all_item_ids()
    bad = []
    for enc in encounters:
        assert 1 <= len(enc['options']) <= 3, enc['tag']      # keys 1 to 3
        for opt in enc['options']:
            cost = opt.get('cost')
            if cost and cost['type'] not in COST_TYPES:
                bad.append((enc['tag'], 'cost', cost['type']))
            if cost and cost['type'] == 'accept_item' and cost['item_id'] not in items:
                bad.append((enc['tag'], 'accept_item', cost['item_id']))
            for rew in list(_rewards(opt.get('reward'))) + list(_rewards(opt.get('bonus_reward'))):
                if rew['type'] not in REWARD_TYPES:
                    bad.append((enc['tag'], 'reward', rew['type']))
                if rew['type'] == 'specific_item' and rew['item_id'] not in items:
                    bad.append((enc['tag'], 'item', rew['item_id']))
                if rew['type'] == 'effect' and rew['effect'] not in EFFECT_INFO:
                    bad.append((enc['tag'], 'effect', rew['effect']))
                if rew['type'] == 'stat' and rew['stat'] not in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                    bad.append((enc['tag'], 'stat', rew['stat']))
    assert not bad, bad


def test_new_flavor_quests_are_present_and_well_formed():
    by_tag = {e['tag']: e for e in FLAVOR}
    for tag in NEW_FLAVOR_TAGS:
        assert tag in by_tag, tag
        enc = by_tag[tag]
        assert enc['min_level'] <= enc['max_level']
        assert len(enc['text'].split()) >= 25
        for opt in enc['options']:
            assert opt['label'] and opt['outcome']


def test_trigger_items_exist():
    items = _all_item_ids()
    for enc in FLAVOR + NPCS:
        tid = enc.get('trigger_item')
        if tid:
            assert tid in items, (enc['tag'], tid)


def test_chain_follow_ups_only_appear_after_their_opener():
    """Androcles' lion and Saint Cuthbert's Gospel are multi-floor chains. A
    follow-up must never be placed without its opener, and always deeper."""
    from flavor_encounters import select_flavor_encounters, FLAVOR_ENCOUNTERS
    chained = [e for e in FLAVOR_ENCOUNTERS if e.get('chain_after')]
    assert {e['tag'] for e in chained} >= {'flv_lion_remembers', 'flv_relic_broker',
                                           'flv_cuthbert_chapel'}
    seen_chain = 0
    for _ in range(1500):
        sel = select_flavor_encounters()
        floor_of = {e['tag']: lvl for lvl, e in sel.items()}
        assert len(floor_of) == len(sel), 'a tag was placed twice'
        for e in chained:
            if e['tag'] in floor_of:
                seen_chain += 1
                assert e['chain_after'] in floor_of, e['tag']
                assert floor_of[e['tag']] > floor_of[e['chain_after']], e['tag']
                assert e['min_level'] <= floor_of[e['tag']] <= e['max_level']
                assert floor_of[e['tag']] not in (20, 40, 60, 80, 100)
    assert seen_chain > 100, 'the chains should actually occur'


def test_new_mysteries_use_real_quiz_subjects_and_empty_floor_bands():
    from mystery_system import MYSTERIES
    subjects = {os.path.splitext(n)[0] for n in os.listdir(os.path.join(ROOT, 'data', 'questions'))}
    for mid in ('brendan', 'jerome'):
        m = MYSTERIES[mid]
        ch = m['challenge']
        assert ch['subject'] in subjects, ch['subject']
        assert 1 <= ch['tier'] <= 5
        assert ch['threshold'] <= ch['total']
        assert m['key_item'] is None
    assert MYSTERIES['brendan']['challenge']['subject'] == 'geography'
    assert MYSTERIES['jerome']['challenge']['subject'] == 'grammar'


def test_new_mini_bosses_join_the_band_roll_with_real_drops():
    items = _all_item_ids()
    for mid in ('bonnacon', 'calydonian_boar'):
        m = MONSTERS[mid]
        assert m['is_mini_boss'] and m['peak_weight'] == 0
        assert 0 < m['spawn_chance'] <= 1
        assert m['treasure']['unique_drop_id'] in items
        assert 'legendary' not in m['tags']
    from monster import Monster
    for mid in ('bonnacon', 'calydonian_boar'):
        Monster({**MONSTERS[mid], 'id': mid}, 1, 1)


def test_every_roaming_named_foe_has_an_omen():
    """The player is told something named is on the floor, never what."""
    missing = []
    for mid, m in MONSTERS.items():
        if not m.get('is_mini_boss') or m.get('is_seal_demon'):
            continue
        if not m.get('spawn_chance') or m.get('peak_floor', 0) > 100:
            continue       # gate bosses and the Cow King are not roamers
        omen = m.get('omen', '')
        if len(omen.split()) < 6:
            missing.append(mid)
            continue
        # an omen never names the thing
        for word in re.findall(r"[A-Za-z']+", m['name']):
            if len(word) > 4 and word.lower() not in ('demon', 'giant', 'knight', 'captain', 'queen', 'prince', 'spawn', 'ghost', 'fragment', 'dragon'):
                assert word.lower() not in omen.lower(), (mid, word)
    assert not missing, missing


def test_encounter_and_hint_text_has_no_dashes_or_lowercase_names():
    hints = _load('hints.json')
    blobs = {'npc': json.dumps(NPCS, ensure_ascii=False),
             'flavor': json.dumps(FLAVOR, ensure_ascii=False),
             'hints': json.dumps(hints, ensure_ascii=False)}
    for name, blob in blobs.items():
        n = len(re.findall('[–—]', blob))
        assert n <= 1, (name, n)
    for enc in FLAVOR + NPCS:
        assert enc['name'].lstrip('"')[:1].isupper(), enc['tag']


def test_karma_encounters_cover_every_block_and_load_from_data():
    from npc_encounters import ENCOUNTERS, _BLOCKS, select_encounter_levels
    assert len(ENCOUNTERS) == len(NPCS) >= 31
    for block, _lo, _hi in _BLOCKS:
        assert sum(1 for e in ENCOUNTERS if e['block'] == block) >= 3
    placed = select_encounter_levels(seed=7)
    assert len(placed) == 10


def test_kneeling_to_help_is_not_scored_below_suspicion():
    dw = next(e for e in NPCS if e['tag'] == 'deadite_woman')
    kneel = next(o for o in dw['options'] if 'kneel' in o['label'].lower())
    ax = next(o for o in dw['options'] if 'ax' in o['label'].lower())
    assert kneel.get('karma', 0) > ax.get('karma', 0)
