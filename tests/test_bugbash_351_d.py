"""Bug bash 3.5.1, hunter D: tonight's fixes reviewed, their seams, the screens.

Each test pins one bug found in review (D1, D2... in the hunter's report).
"""
import json
import os
import random
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import pygame  # noqa: E402

pygame.init()

import affinity  # noqa: E402
from monster import Monster  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _m(kind, x=0, y=0):
    return Monster({**MONS[kind], 'id': kind}, x, y)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(351)
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_bugbash_351_d__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    log = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: log.append(text))
    g._log = log
    return g


def _page_texts(g, corpse):
    identity, mechanics, lore = g._lore_corpse_lines(corpse, 5)
    return [str(t[0]) for t in identity], [str(t[0]) for t in mechanics], lore


# ---------------------------------------------------------------------------
# D1. A studied body's page tells what its kind is made of
# ---------------------------------------------------------------------------

def test_d1_a_slain_stirge_swarms_body_says_it_shrugs_off_a_sword(game):
    """The body of a creature the hero killed carries only its weaknesses
    and resistances (Game._make_corpse), so its studied page never said what
    it shrugs off, refuses or falls to easily, nor its scales, ward or healing:
    a stirge swarm's body did not say a sword hardly touches it, the very
    thing the 3.5.1 Bestiary pass was for. The page reads its kind's own
    definition."""
    corpse = game._make_corpse(_m('stirge_swarm', 3, 3))
    _ident, mech, _lore = _page_texts(game, corpse)
    for _k, text in affinity.bestiary_rows(MONS['stirge_swarm']):
        assert text in mech, (text, mech)
    assert 'Shrugs Off (Quarter Damage): Slash, Pierce' in mech


@pytest.mark.parametrize('kind', ['troll', 'abaddon_destroyer', 'fafnir_dragon', 'skeleton'])
def test_d1_every_row_of_a_slain_kind_is_on_its_bodys_page(game, kind):
    corpse = game._make_corpse(_m(kind, 3, 3))
    _ident, mech, _lore = _page_texts(game, corpse)
    for _k, text in affinity.bestiary_rows(MONS[kind]):
        assert text in mech, (kind, text)


def test_d1_a_graveyard_skeleton_has_its_numbers_and_its_story(game):
    """A graveyard's laid-out skeleton (food_system.make_corpse) carried no
    health, THAC0, blows or lists: studied, its page said "HP: ?   THAC0: ?"
    and "No lore recorded.", and none of its weaknesses."""
    from food_system import make_corpse
    corpse = make_corpse('skeleton', 3, 3)
    _ident, mech, lore = _page_texts(game, corpse)
    stats = next(t for t in mech if t.startswith('HP: '))
    assert '?' not in stats, stats
    assert f"HP: {MONS['skeleton']['hp']}" in stats
    assert 'Weak To (Double Damage): Blunt, Holy' in mech
    assert any(t.startswith('Bane Materials') and 'Silver' in t for t in mech)
    assert lore == MONS['skeleton']['lore']


def test_d1_an_old_saves_body_and_an_encounter_person_still_read(game):
    """A body from an old save (only what was copied then) reads its kind; a
    person built in code (no kind in monsters.json) keeps what the body has."""
    from items import Corpse
    old = Corpse('stirge swarm', 'stirge_swarm', 1, 1,
                 monster_def={'hp': 19, 'thac0': 20, 'resistances': ['blunt'],
                              'weaknesses': ['fire', 'cold']})
    _ident, mech, _lore = _page_texts(game, old)
    assert 'HP: 19   THAC0: 20   Speed: 12' in mech
    assert 'Shrugs Off (Quarter Damage): Slash, Pierce' in mech
    person = Corpse('pilgrim', 'pilgrim_npc_d', 1, 1,
                    monster_def={'hp': 9, 'thac0': 19, 'weaknesses': ['holy']})
    _ident, mech, _lore = _page_texts(game, person)
    assert 'HP: 9   THAC0: 19   Speed: 1' in mech
    assert 'Weak To (Double Damage): Holy' in mech
