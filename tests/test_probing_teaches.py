"""The Wand of Probing teaches the kind (Brandon, 2026-11-14).

"A Wand of Probing is a cool idea, getting points toward a bestiary family
entry or identifying a creature (thus getting the family identification
point)". Probing a creature counts as studying its kind, exactly as a
correct corpse study does, through the one path both share
(FamilyMixin._learn_kind):

  * the kind becomes KNOWN (family_lore.knowledge) and its page opens;
  * its family gains the kind toward its tiers (distinct kinds studied),
    with the same tier line, popup and Journal news;
  * never for a kind already studied, never for a creature with no family,
    and a boss or unique counts as its corpse would (a keystone).

The read-out stays; a probe that teaches adds "You learn the ways of ...".
Logic tests on a real headless Game (Claude cannot play it).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import family_lore  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


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
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_probing_teaches__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    log = []
    real = g.add_message

    def _say(text, kind='info', *a, **k):
        log.append(str(text))
        return real(text, kind, *a, **k)
    monkeypatch.setattr(g, 'add_message', _say)
    g._log = log
    return g


def _probe(g, kind, dx=2, defn=None):
    """A creature of `kind` beside the hero, probed."""
    m = Monster(defn or {**MONS[kind], 'id': kind}, g.player.x + dx, g.player.y)
    g.monsters.append(m)
    wand = items.make_item_by_id('wand', 'wand_of_probing')
    g._wand_override_target = m
    n = len(g._log)
    g._apply_wand_effect(wand)
    g._wand_override_target = None
    return m, g._log[n:]


def _plain(fid, n):
    """`n` kinds of a family that are not keystones (each counts one)."""
    out = [k for k in family_lore.members(fid) if not family_lore.is_keystone(k)]
    assert len(out) >= n, fid
    return out[:n]


def test_probing_an_unstudied_kind_makes_it_known_and_counts_once(game):
    p = game.player
    assert family_lore.knowledge(p, 'ghoul') == family_lore.UNKNOWN
    before = family_lore.score(p, 'restless_dead')
    m, said = _probe(game, 'ghoul')
    assert said[0] == f"The Ghoul: {m.hp}/{m.max_hp} HP."            # the read-out stays first
    assert said[1].startswith('Weak To: ')
    assert 'You learn the ways of the Ghoul.' in said
    assert family_lore.knowledge(p, 'ghoul') == family_lore.KNOWN
    assert 'ghoul' in p.studied_monster_ids and 'ghoul' in p.lore_known_monster_ids
    assert game._family_has_page('ghoul')
    assert family_lore.score(p, 'restless_dead') == before + 1


def test_probing_again_gives_nothing_more(game):
    p = game.player
    _probe(game, 'ghoul')
    score = family_lore.score(p, 'restless_dead')
    told = dict(p.family_tiers_told)
    _m2, said = _probe(game, 'ghoul')
    assert any('HP' in s for s in said)                                # it still reads
    assert not any('learn the ways' in s for s in said)
    assert family_lore.score(p, 'restless_dead') == score
    assert dict(p.family_tiers_told) == told


def test_a_kind_studied_by_its_corpse_teaches_nothing_by_probing(game):
    p = game.player
    family_lore.record_study(p, 'ghoul')
    score = family_lore.score(p, 'restless_dead')
    _m, said = _probe(game, 'ghoul')
    assert not any('learn the ways' in s for s in said)
    assert family_lore.score(p, 'restless_dead') == score


def test_a_creature_with_no_family_teaches_nothing(game):
    # Every kind in monsters.json has a family; the ones without are built in
    # code (Death, the secret cow, the ethereal unicorn: family_lore).
    kind = 'ethereal_unicorn'
    defn = {k: v for k, v in MONS['goblin'].items() if k != 'family'}
    defn['id'] = kind
    assert family_lore.family_of(kind) is None
    assert not family_lore.counts_as_study(game.player, kind)
    lore = set(game.player.lore_known_monster_ids)
    m, said = _probe(game, kind, defn=defn)
    assert family_lore.family_of(m) is None
    assert any('HP' in s for s in said)
    assert not any('learn the ways' in s for s in said)
    assert kind not in game.player.studied_monster_ids
    assert set(game.player.lore_known_monster_ids) == lore


def test_a_boss_counts_as_its_corpse_would_a_keystone(game):
    """The same rule for uniques and bosses as corpse study: Medusa is a
    keystone (keystone_weight kinds). Her quest step opened her page with no
    credit; a probe still counts, as her corpse's study would."""
    p = game.player
    assert family_lore.is_keystone('medusa_gorgon')
    game._quest_teaches('medusa_gorgon')
    assert family_lore.knowledge(p, 'medusa_gorgon') == family_lore.KNOWN
    assert family_lore.counts_as_study(p, 'medusa_gorgon')
    before = family_lore.score(p, 'gorgons')
    _m, said = _probe(game, 'medusa_gorgon')
    assert 'You learn the ways of Medusa the Gorgon.' in said
    assert family_lore.score(p, 'gorgons') == before + family_lore.weight('medusa_gorgon')


def test_crossing_a_tier_pops_the_tier_popup(game):
    p = game.player
    fid = 'gorgons'
    need = family_lore.thresholds(fid)[2]                             # Lore, tier 3: a popup
    kinds = _plain(fid, need)
    p.studied_monster_ids |= set(kinds[:-1])
    family_lore.mark_all_told(p)
    assert family_lore.tier(p, fid) == 2
    game.__dict__['_popup_queue'] = []
    _m, said = _probe(game, kinds[-1])
    assert family_lore.tier(p, fid) == 3
    q = game.__dict__.get('_popup_queue') or []
    fam = [e for e in q if e['kind'] == 'family']
    assert len(fam) == 1, q
    assert fam[0]['data']['title'] == family_lore.popup_title(fid, 3)
    # the learn line comes first, then the tier's own line in the log
    from naming import proper_name
    head = proper_name(family_lore.popup_title(fid, 3).lower()) + ':'
    learn = next(i for i, s in enumerate(said) if 'learn the ways' in s)
    tier_line = next(i for i, s in enumerate(said) if s.startswith(head))
    assert learn < tier_line


def test_a_lower_tier_is_its_gold_line(game):
    p = game.player
    fid = 'restless_dead'
    need = family_lore.thresholds(fid)[0]
    kinds = _plain(fid, need)
    p.studied_monster_ids |= set(kinds[:-1])
    family_lore.mark_all_told(p)
    _m, said = _probe(game, kinds[-1])
    assert family_lore.tier(p, fid) == 1
    assert family_lore.tier_message(fid, 1) in said


def test_probing_knows_every_corpse_of_the_kind_and_tells_the_seeker(game, monkeypatch):
    seen = []
    real = game._seeker_event
    monkeypatch.setattr(game, '_seeker_event', lambda ev, **kw: (seen.append((ev, kw)), real(ev, **kw))[1])
    corpse = items.Corpse('Ghoul', 'ghoul', game.player.x, game.player.y)
    game.ground_items.append(corpse)
    assert not items.corpse_is_known(game.player, corpse) or corpse.id_level < 5
    _probe(game, 'ghoul')
    assert corpse.id_level == 5
    assert ('monster_known', {'monster': 'ghoul'}) in seen


def test_probing_survives_save_and_load(game):
    import main
    import save_system
    p = game.player
    _probe(game, 'ghoul')
    score = family_lore.score(p, 'restless_dead')
    assert save_system.save_game(game)
    g2, note = main._restore_saved_game(game.screen, game.player_name,
                                        save_system.load_game(game.player_name))
    assert g2 is not None, note
    assert 'ghoul' in g2.player.studied_monster_ids
    assert family_lore.knowledge(g2.player, 'ghoul') == family_lore.KNOWN
    assert family_lore.score(g2.player, 'restless_dead') == score
    # and a probe after the load teaches nothing twice
    g2.monsters = []
    m = Monster({**MONS['ghoul'], 'id': 'ghoul'}, g2.player.x + 2, g2.player.y)
    g2.monsters.append(m)
    g2._wand_override_target = m
    n = len(g2.msg_log.entries)
    g2._apply_wand_effect(items.make_item_by_id('wand', 'wand_of_probing'))
    said = [str(e[0]) for e in g2.msg_log.entries[n:]]
    assert not any('learn the ways' in s for s in said)
    assert family_lore.score(g2.player, 'restless_dead') == score


def test_corpse_study_and_probing_share_one_path():
    """Brandon's brief: find how corpse study records a kind and call the same
    path; do not build a second one."""
    def body(path, start, end):
        src = open(os.path.join(ROOT, 'src', path), encoding='utf-8').read()
        return src[src.index(start):src.index(end, src.index(start))]
    corpse = body('main.py', 'def _start_corpse_identify', 'def _examine_corpse_direct')
    probe = body('game_magic.py', "elif effect == 'probing':", "elif effect == 'create_monster':")
    for text in (corpse, probe):
        assert 'self._learn_kind(' in text
        assert 'self._family_study(' not in text
        assert 'lore_known_monster_ids.add' not in text
        assert '_open_kind_page' not in text


def test_counts_as_study_is_the_record_rule():
    from player import Player
    p = Player()
    assert family_lore.counts_as_study(p, 'ghoul')
    assert not family_lore.counts_as_study(p, '')
    assert family_lore.record_study(p, 'ghoul')
    assert not family_lore.counts_as_study(p, 'ghoul')
    assert not family_lore.record_study(p, 'ghoul')
