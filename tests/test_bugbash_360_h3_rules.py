"""Bug bash 3.6.0, hunt 3: the rules (h3-01 to h3-05) and the true cards.

  h3-01  a seal that is not ASCII is an edited profile: set aside, the backup back
  h3-02  what a swallowed hero wears reaches only what holds him
  h3-03  "7 foes flinch and run"
  h3-04  an opener that never landed is not struck later; the squall still is
  h3-05  a charmed peace holds on a pinned creature
  h3-07, h2-05  the venoms' and the Styx's words, true while the rulings wait
"""
from __future__ import annotations

import json
import os
import random

import pytest

from test_bugbash_360_monsters import _mk, _msgs, _scene, _swallowed

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


# --------------------------------------------------------------------- h3-01

def test_h3_01_a_seal_that_is_not_ascii_is_set_aside_and_the_backup_restored(tmp_path, monkeypatch):
    import seeker_codes
    import seeker_profile as sp
    monkeypatch.setattr(seeker_codes, '_KEYS_OVERRIDE',
                        {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}})
    monkeypatch.setattr(sp, '_DIR_OVERRIDE', str(tmp_path))
    p = sp.load('Test Seeker')
    p.add('kills', 1)
    p.flush()
    p.add('kills', 1)
    p.flush()
    path = sp.profile_path('Test Seeker')
    with open(path, encoding='utf-8') as f:
        doc = json.load(f)
    doc['seal'] = 'Zoë'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f)
    q = sp.load('Test Seeker')
    assert q.edited_found and q.stat('kills') >= 1
    assert any('.edited-' in n for n in os.listdir(os.path.dirname(path)))


# --------------------------------------------------------------------- h3-02

def _wearing(monkeypatch, *flags):
    import chain_passives
    monkeypatch.setattr(chain_passives, 'player_has_passive', lambda p, f: f in flags)
    monkeypatch.setattr(chain_passives, 'consume_passive_charge', lambda *a, **k: True)
    monkeypatch.setattr(chain_passives, 'consume_run_passive', lambda *a, **k: True)
    monkeypatch.setattr(random, 'random', lambda: 0.0)


def _untouched(out):
    return not any(out.has_effect(e) for e in ('feared', 'charmed', 'sleeping', 'paralyzed'))


def test_h3_02_the_ringing_helm_stays_in_the_gut(monkeypatch):
    import armor_procs
    g, cube, out = _swallowed()
    _wearing(monkeypatch)
    monkeypatch.setattr(armor_procs, 'player_has_armor_proc',
                        lambda p, f: f == 'ringing_intimidation')
    g._refresh_fov()
    assert _untouched(out)


@pytest.mark.parametrize('flag,tag', [('aura_of_awe', ''), ('fafnirs_glare', ''),
                                      ('demon_command_one_per_floor', 'demon'),
                                      ('seventy_two_seals', 'demon'),
                                      ('command_undead', 'undead'),
                                      ('paths_of_the_dead', '')])
def test_h3_02_a_worn_passive_stays_in_the_gut(monkeypatch, flag, tag):
    g, cube, out = _swallowed()
    if tag:
        out.tags = list(out.tags or []) + [tag]
    _wearing(monkeypatch, flag)
    g.player._paths_armed = flag == 'paths_of_the_dead'
    out.max_hp = 5000                   # (the strongest: the one the Paths would pick)
    g._refresh_fov()
    assert _untouched(out)


def test_h3_02_solomons_authority_stays_in_the_gut(monkeypatch):
    import chain_passives
    g, cube, out = _swallowed()
    out.tags = list(out.tags or []) + ['demon']
    _wearing(monkeypatch)
    monkeypatch.setattr(chain_passives, 'get_pacify_demon_chance', lambda p: 1.0)
    g._refresh_fov()
    assert _untouched(out)


def test_h3_02_the_seal_stays_in_the_gut(monkeypatch):
    from items import make_item_by_id
    g, cube, out = _swallowed()
    g.player.accessory_slots[0] = make_item_by_id('accessory', 'seal_of_solomon')
    monkeypatch.setattr(g.player.accessory_slots[0], 'pacify_chance', 1.0)
    monkeypatch.setattr(g, '_do_monster_turns', lambda: None)
    g._advance_turn()
    assert _untouched(out)


# --------------------------------------------------------------------- h3-03

def test_h3_03_the_helm_speaks_in_the_plural(monkeypatch):
    import armor_procs
    g = _scene(('orc_warrior', 2, 0), ('orc_warrior', 2, 2))
    _wearing(monkeypatch)
    monkeypatch.setattr(armor_procs, 'player_has_armor_proc',
                        lambda p, f: f == 'ringing_intimidation')
    g._refresh_fov()
    line = next(t for t in _msgs(g) if 'rings out' in t)
    assert line.endswith('2 foes flinch and run!'), line


# --------------------------------------------------------------------- h3-04

def test_h3_04_a_pounce_that_never_landed_is_not_struck_later():
    g = _scene(('pegasus', 1, 0))
    m = g.monsters[0]
    assert m._pounce_now()                          # armed, and the blow never came
    m.x = g.player.x + 6
    m.take_turn(g.player, g.dungeon, g.monsters)
    now = m.__dict__.get('_opener_now')
    assert now is None or now is not m._opener_attack


def test_h3_04_the_squall_a_wrong_answer_called_still_comes():
    g = _scene(('blue_men_of_the_minch', 3, 0))
    m = g.monsters[0]
    m._lp_parley = 'angry'
    squall = dict(m.attacks[-1])
    m._opener_now = squall
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.__dict__.get('_opener_now') is squall


# --------------------------------------------------------------------- h3-05

@pytest.mark.parametrize('pin', ['immobilized', 'stuck_in_pit', 'impaled'])
@pytest.mark.parametrize('peace', ['_strife_peace', '_bribed', ''])
def test_h3_05_a_charmed_peace_holds_on_a_pinned_creature(pin, peace):
    g = _scene(('troll', 1, 0))
    m = g.monsters[0]
    m.status_effects['charmed'] = 12
    if peace:
        setattr(m, peace, True)
    m.status_effects[pin] = 6
    assert not m.take_turn(g.player, g.dungeon, g.monsters)


def test_h3_05_pinned_and_uncharmed_it_still_strikes():
    g = _scene()
    m = _mk('troll', g.player.x + 1, g.player.y)
    g.monsters.append(m)
    m.status_effects['immobilized'] = 6
    assert m.take_turn(g.player, g.dungeon, g.monsters)


# ------------------------------------------------- the cards, until he rules

@pytest.mark.parametrize('fid', ['viper_venom', 'hydras_blood', 'eitr_venom', 'ipoh_venom'])
def test_h3_07_a_venoms_card_says_what_it_spares(fid):
    """Brandon's ruling A2 (2026-11-22): blood is the rule, so the card says blood."""
    flasks = _data('items', 'flask.json')
    lore = next(v['lore'] for k, v in flasks.items()
                if k == fid or (fid == 'ipoh_venom' and 'ipoh' in str(v.get('lore', ''))))
    assert 'no blood' in lore or 'has blood in it' in lore


def test_h2_05_the_styx_promises_only_what_it_turns():
    import food_system
    told = [_data('items', 'potion.json')['water_of_the_styx']['drink_line'],
            food_system._WARD_POTIONS['styx_dipped'][2],
            next(h for h in _walk(_data('hints.json')) if 'Water of the Styx' in h)]
    for line in told:
        assert 'venom' in line and 'magic' in line, line
    status = ' '.join(_walk(_data('wards.json')))
    assert 'No blow, bite or claw can wound you' not in status


def _walk(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)
