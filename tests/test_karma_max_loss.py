"""No karma loss bigger than one, anywhere (Brandon, 2026-10-18).

"Betrayal is different than handing a murderer over for death. Make sure we
differentiate. Max karma drop is -1."

* karma.adjust clamps any single negative change to -1 and logs the ask,
  with the karma gate on or off, whatever the kind;
* no data file asks for more (encounters, the Emberpup, the patterns);
* no karma.adjust call in src/ passes a literal below -1;
* the Ring of Gyges and the Emberpup attack, driven for real, take one.

The betrayal / justice classification of every hand-over option is pinned in
tests/test_story_content.py (ENCOUNTER_STORIES_DRAFT.md Part J9).
"""
import glob
import json
import os
import re
import sys
import types

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)

import karma  # noqa: E402


def _game(k=0, deepest=35):
    return types.SimpleNamespace(karma=k, dungeon_level=deepest, turn_count=0,
                                 player=types.SimpleNamespace(deepest_floor_reached=deepest))


@pytest.fixture
def logged(monkeypatch):
    import game_log
    out = []
    monkeypatch.setattr(game_log, 'log_error', lambda msg, exc_info=True: out.append(msg))
    return out


def test_the_ceiling_is_one():
    assert karma.MAX_LOSS == 1


@pytest.mark.parametrize('kind', sorted(karma.NEGATIVE) + [karma.LEGACY])
@pytest.mark.parametrize('gate', [True, False])
def test_adjust_clamps_a_bigger_loss_to_one_and_logs_it(kind, gate, monkeypatch, logged):
    monkeypatch.setattr(karma, '_RULES', dict(karma.rules(), gate_enabled=gate))
    g = _game(5)
    assert karma.adjust(g, -2, kind=kind, source='test_source') == -1
    assert g.karma == 4
    assert karma.adjust(g, -7, kind=kind, source='test_source') == -1
    assert g.karma == 3
    assert len(logged) == 2 and all('test_source' in m and '-1' in m for m in logged)
    led = [e for e in g._deeds['karma']['ledger'] if e['source'] == 'test_source']
    assert [(e['requested'], e['applied']) for e in led] == [(-2, -1), (-7, -1)]


def test_a_loss_of_one_is_untouched_and_not_logged(logged):
    g = _game(0)
    assert karma.adjust(g, -1, kind='betray', source='x') == -1
    assert g.karma == -1
    assert not logged


def test_the_floor_still_holds_at_minus_ten(logged):
    g = _game(-10)
    assert karma.adjust(g, -2, kind='cruelty', source='x') == 0
    assert g.karma == -10


def test_gains_are_not_touched_by_the_loss_ceiling(gate_off, logged):
    g = _game(0)
    assert karma.adjust(g, 2, kind='legacy', source='x') == 2
    assert not logged


# ------------------------------------------------------------------ data

def _negative_karma_values(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f'{path}/{k}'
            # Conditions (karma_min / karma_max) are ranges, not changes.
            if ('karma' in k.lower() and not k.endswith(('_min', '_max'))
                    and isinstance(v, (int, float)) and not isinstance(v, bool)):
                out.append((here, v))
            _negative_karma_values(v, here, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _negative_karma_values(v, f'{path}[{i}]', out)
    return out


def test_no_data_file_asks_for_a_loss_beyond_one():
    bad = []
    n = 0
    for path in glob.glob(os.path.join(ROOT, 'data', '**', '*.json'), recursive=True):
        with open(path, encoding='utf-8') as f:
            try:
                d = json.load(f)
            except ValueError:
                continue
        for where, v in _negative_karma_values(d, os.path.relpath(path, ROOT), []):
            n += 1
            if v < -karma.MAX_LOSS:
                bad.append((where, v))
    assert n > 50                                   # the scan really saw the karma fields
    assert not bad, bad


def test_the_emberpup_attack_and_the_patterns_take_one():
    with open(os.path.join(ROOT, 'data', 'abandoned_emberpup.json'), encoding='utf-8') as f:
        assert json.load(f)['attack_karma'] == -1
    for rule in karma.rules()['patterns_neg']:
        assert rule['karma'] == -1, rule['id']


def test_the_validator_rejects_a_loss_beyond_one_outside_the_encounters(monkeypatch):
    from tools.encounters import validate as V
    rules = dict(V._rules())
    rules['patterns_neg'] = [{'id': 'harsh', 'tag': 'vice:cruelty', 'min': 1, 'karma': -2}]
    issues = V._other_karma_sources(rules)
    assert any(i.code == 'karma_size' and 'harsh' in i.msg for i in issues)
    assert not V._other_karma_sources(V._rules())


def test_no_adjust_call_in_src_passes_a_literal_below_minus_one():
    call = re.compile(r'\badjust\(\s*[\w.]+\s*,\s*(-\s*\d+)')
    bad = []
    for path in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        with open(path, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                for m in call.finditer(line):
                    if int(m.group(1).replace(' ', '')) < -karma.MAX_LOSS:
                        bad.append(f'{os.path.basename(path)}:{n}: {line.strip()}')
    assert not bad, bad


# ------------------------------------------------------------------ behaviour

class _Quiz:
    """Stands in for QuizEngine: the attack's callback gets ``score``."""
    def __init__(self, score):
        self.score = score

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True))


def test_the_ring_of_gyges_takes_one_for_striking_an_innocent_unseen():
    import combat
    import items
    from monster import Monster
    from player import Player
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    p = Player()
    p.x, p.y = 5, 5
    p.hp = p.max_hp = 10 ** 6
    p.weapon = items.instantiate_weapon('longsword', 'iron')
    ring = items.make_item_by_id('accessory', 'ring_of_gyges')
    assert ring.gyges_invisible_attack_karma
    p.accessory_slots[0] = ring
    p.status_effects['invisible'] = 20
    g = _game(3, deepest=30)
    p._combat_game_ref = g
    m = Monster(dict(defs['giant_rat'], id='giant_rat'), 6, 5)
    m.hp = m.max_hp = 10 ** 8
    m.hostile = False                        # an innocent, as the ring counts it
    combat.player_attack(p, m, _Quiz(5), lambda *a, **k: None)
    assert g.karma == 2
    led = g._deeds['karma']['ledger']
    assert [(e['source'], e['requested'], e['applied']) for e in led] == \
        [('ring_of_gyges', -1, -1)]


def test_the_ring_of_gyges_costs_once_per_victim_not_per_blow():
    import re
    src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'combat.py'), encoding='utf-8').read()
    block = src[src.index('Ring of Gyges (gyges_invisible_attack_karma)'):]
    block = block[:block.index('Echidna')]
    assert "_gyges_struck" in block and re.search(r"karma\.adjust\(_g, -1", block)
