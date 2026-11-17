"""The Bestiary tells the whole blow (3.5.1 audit).

Brandon: "some monsters take a quarter or half damage from certain attacks,
like a stirge swarm hit with a sword or the beetles. However, this is
conveyed nowhere on the monster identification screen. We need to make sure
all this information is conveyed, and that all bestiary entries are accurate
(weakness AND resistances)."

What the hero is told of a creature (the Bestiary page, a studied corpse,
the Wand of Probing, Observe) is read from affinity.damage_profile, and here
every kind in data/monsters.json is checked against the blow itself:
combat.weapon_type_multiplier for a weapon's form and its material, and
combat._damage_multiplier for a spell, wand, flask or coating. A page can no
longer say less, or more, than the blow does.
"""
import json
import os
import random
import sys
from types import SimpleNamespace

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
import combat  # noqa: E402
from monster import Monster  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

# Types a creature's lists may name that nothing of the hero's lands as:
# what one creature does to another. The page leaves them off.
NO_HERO_SOURCE = {'shadow', 'necrotic'}


def _m(kind):
    return Monster({**MONS[kind], 'id': kind}, 0, 0)


def _weapon(forms, material=''):
    return SimpleNamespace(damage_types=list(forms), material=material, buc='uncursed',
                           is_unique=False, effective_against=[], name='test blade')


def _claimed(kind):
    """{type: multiplier} the page claims, from its profile."""
    step = {affinity.WEAK: affinity.weak_step(), 'banes': affinity.weak_step(),
            affinity.RESISTED: affinity.resisted_step(), affinity.SHRUGS_OFF: affinity.shrugs_step()}
    out = {}
    for k, _label, types in affinity.damage_profile(MONS[kind]):
        for t in types:
            out[t] = step[k]
    return out


def _materials():
    combat._load_material_tags()
    return sorted(combat._MATERIAL_EFFECTIVE_AGAINST)


@pytest.mark.parametrize('kind', sorted(MONS))
def test_the_page_says_what_every_blow_and_spell_does(kind):
    m = _m(kind)
    claimed = _claimed(kind)
    for t in affinity.HERO_TYPES:
        want = claimed.get(t, 1.0)
        if t in affinity.FORMS:
            got = combat.weapon_type_multiplier(_weapon([t]), m)[0]
            assert got == pytest.approx(want), (kind, 'form', t, got, want)
        got = combat._damage_multiplier([t], m)
        assert got == pytest.approx(want), (kind, 'typed', t, got, want)
    for mat in _materials():
        _form, sub = combat.weapon_type_multiplier(_weapon(['physical'], mat), m)
        assert (sub > 1.0) == (mat in claimed), (kind, 'material', mat, sub)


def test_every_listed_type_is_one_the_page_can_tell():
    known = set(affinity.HERO_TYPES) | set(_materials()) | NO_HERO_SOURCE
    stray = sorted({(k, t) for k, v in MONS.items()
                    for key in ('weaknesses', 'resistances', 'shrugs_off')
                    for t in (v.get(key) or ()) if t not in known})
    assert not stray, stray


def test_the_stirge_swarm_and_the_beetle_say_it():
    rows = dict(affinity.bestiary_rows(MONS['stirge_swarm']))
    assert rows['shrugs_off'] == 'Shrugs Off: Slash, Pierce'
    assert rows['resisted'] == 'Resists: Blunt'
    assert rows['weak'] == 'Weak To: Fire, Cold'
    beetle = dict(affinity.bestiary_rows(MONS['giant_beetle']))
    assert beetle['resisted'] == 'Resists: Slash'
    assert beetle['weak'] == 'Weak To: Blunt'


def test_the_hidden_rules_are_told():
    skel = dict(affinity.bestiary_rows(MONS['skeleton']))
    assert 'Silver' in skel['banes'] and 'Sunsteel' in skel['banes']
    assert skel['both'].startswith('Hardest Blow: ') and 'blessed' in skel['both']
    troll = dict(affinity.bestiary_rows(MONS['troll']))
    assert troll['regen'].startswith('Regenerates: ') and 'fire or acid stops it' in troll['regen']
    fafnir = dict(affinity.bestiary_rows(MONS['fafnir_dragon']))
    assert '80%' in fafnir['scales'] and 'pit' in fafnir['scales']
    abaddon = dict(affinity.bestiary_rows(MONS['abaddon_destroyer']))
    assert '50%' in abaddon['ward']


def test_a_type_nothing_of_the_heros_lands_as_is_left_off():
    khepri = affinity.bestiary_rows(MONS['khepri_beetle'])
    assert 'shadow' in MONS['khepri_beetle']['weaknesses']
    assert not any('Shadow' in t for _k, t in khepri)


# ------------------------------------------------------------ the screens

@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(11)
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_bestiary_whole_blow__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    log = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: log.append(text))
    g._log = log
    return g


def _page(g, kind):
    g.player.known_monster_ids.add(kind)
    g._open_encyclopedia()
    g._encyclopedia_load_entries('bestiary')
    entry = next(e for e in g.encyclopedia_entries if e.get('_id') == kind)
    return [str(t[0]) for t in g._encyclopedia_article_lines('bestiary', entry)]


@pytest.mark.parametrize('kind', ['stirge_swarm', 'giant_beetle', 'skeleton', 'troll', 'werewolf'])
def test_the_bestiary_page_of_a_known_kind_shows_every_row(game, kind):
    game._open_kind_page(kind)
    page = _page(game, kind)
    for _k, text in affinity.bestiary_rows(MONS[kind]):
        assert text in page, (kind, text)


def test_the_bestiary_page_of_an_unknown_kind_keeps_it_back(game):
    page = _page(game, 'stirge_swarm')
    assert not any(t.startswith(('Shrugs Off', 'Resists', 'Weak To', 'Bane')) for t in page)


def test_a_studied_corpse_shows_every_row(game):
    from food_system import make_corpse
    corpse = make_corpse('stirge_swarm', 1, 1)
    corpse.monster_def = MONS['stirge_swarm']
    _identity, mechanics, _lore = game._lore_corpse_lines(corpse, 5)
    texts = [str(t[0]) for t in mechanics]
    for _k, text in affinity.bestiary_rows(MONS['stirge_swarm']):
        assert text in texts, text


def test_drain_is_a_drain(game, monkeypatch):
    """The wand of drain life and the Drain Life spells land as 'drain', so
    the undead's "Resists: Drain" is true (they were untyped)."""
    import items
    skel = _m('ghoul')                       # Resists: Cold, Poison, Drain, Pierce
    skel.x, skel.y = game.player.x + 1, game.player.y
    game.monsters = [skel]
    seen = []
    real = Monster.take_damage

    def spy(self, amount, damage_type='physical', *a, **k):
        seen.append(damage_type)
        return real(self, amount, damage_type, *a, **k)
    monkeypatch.setattr(Monster, 'take_damage', spy)
    wand = items.make_item_by_id('wand', 'wand_of_life_drain')
    game._wand_override_target = skel
    game._apply_wand_effect(wand)
    assert 'drain' in seen, seen
    assert combat._damage_multiplier(['drain'], skel) == affinity.resisted_step()
