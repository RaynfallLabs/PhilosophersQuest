"""The counter items the MONSTERS AND MAGIC kinds' lore names (2026-11-19,
slice M): a Handful of Seed (a vampire must count it), Upas Latex and a Vial
of Eitr (the poison coatings of tiers 3 and 5), a Sprig of Whitethorn (no
strix strikes the one who carries it) and a Caged Cockerel (its crow).
"""
import json
import os
import sys
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import coatings  # noqa: E402
import counters  # noqa: E402
import items  # noqa: E402
import lore_powers  # noqa: E402
import monster as monster_mod  # noqa: E402
from game_lore_powers import LorePowersMixin  # noqa: E402

NEW_FLASKS = ('seed_handful', 'upas_latex', 'eitr_venom')
NEW_ACC = ('whitethorn_branch', 'caged_cockerel')


def _json(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _json('monsters.json')


def _m(kind, x=6, y=5):
    m = monster_mod.Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = True
    return m


def test_the_counter_items_are_real_items_with_art_price_and_shelf():
    worth = _json('item_worth.json')['share_by_id']
    traders = json.dumps(_json('traders.json'))
    installed = set(json.load(open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json'),
                                   encoding='utf-8'))['items'])
    for fid in NEW_FLASKS:
        it = items.make_item_by_id('flask', fid)
        assert it is not None and it.tier in (2, 3, 5), fid
        # On the apothecary's flask shelf by its depth, and found as loot.
        assert getattr(it, 'floor_spawn_weight', None) or _json('items', 'flask.json')[fid]['floorSpawnWeight'], fid
    assert '"class": "flask", "picks"' in traders
    for fid in ('upas_latex', 'eitr_venom'):
        assert fid in traders, fid                        # a stall's venom offers, for what is below
    for aid in NEW_ACC:
        it = items.make_item_by_id('accessory', aid)
        assert it is not None and counters.item_counters(it), aid
        assert aid in worth and aid in traders, aid
    for iid in NEW_FLASKS + NEW_ACC:
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', iid + '.png')), iid
        assert iid in installed, iid


def test_the_poison_ladder_runs_through_every_depth():
    ladder = [(items.make_item_by_id('flask', f).tier, coatings.coat_spec(items.make_item_by_id('flask', f)))
              for f in ('viper_venom', 'upas_latex', 'hydras_blood', 'eitr_venom')]
    assert [t for t, _ in ladder] == [1, 3, 4, 5]
    turns = [s['rider']['turns'] for _, s in ladder]
    assert turns == sorted(turns) and all(s['substance'] == 'poison' for _, s in ladder)


def test_a_vampire_stops_to_count_the_seed_once():
    seed = items.make_item_by_id('flask', 'seed_handful')
    v = _m('vampire')
    lines = coatings.throw_at(seed, v)
    assert v.has_effect('paralyzed') and 'counts the grains' in lines[0][0]
    v.status_effects.clear()
    again = coatings.throw_at(seed, v)
    assert not v.has_effect('paralyzed') and 'no mind' in again[0][0]
    wolf = _m('wolf')
    coatings.throw_at(seed, wolf)
    assert not wolf.has_effect('paralyzed')


def test_no_strix_strikes_the_one_who_carries_whitethorn():
    thorn = items.make_item_by_id('accessory', 'whitethorn_branch')
    hero = SimpleNamespace(inventory=[thorn], armor_slots=[], shield=None, amulet_slot=None,
                           belt_slot=None, accessory_slots=[], ears_stopped=False)
    strix = _m('strix')
    beak = strix.attacks[0]
    assert 'whitethorn' in lore_powers.blow_refused(strix, hero, beak)
    assert lore_powers.blow_refused(_m('harpy'), hero, _m('harpy').attacks[0]) is None
    hero.inventory = []
    assert lore_powers.blow_refused(strix, hero, beak) is None


class _Game(LorePowersMixin):
    def __init__(self, monsters):
        self.monsters = monsters
        self.messages = []
        self.dungeon_level = 10
        self.player = SimpleNamespace(x=5, y=5)
        self.player.__dict__['_crowed_floor'] = None
        self.killed = []

    def add_message(self, text, kind='info'):
        self.messages.append(text)

    def _sees_monster(self, m):
        return True

    def _advance_turn(self):
        pass

    def _on_monster_killed(self, m):
        self.killed.append(m)


def test_the_cockerel_crows_once_a_floor_and_the_cockatrice_falls_back():
    bird = items.make_item_by_id('accessory', 'caged_cockerel')
    assert counters.crows(bird) and not counters.is_applied(bird)
    c, b, w = _m('cockatrice', 6, 5), _m('basilisk', 7, 5), _m('wolf', 8, 5)
    g = _Game([c, b, w])
    assert g._cock_crow(bird)
    assert c.hp <= c.max_hp - c.max_hp // 2 and (c.has_effect('feared') or not c.alive)
    assert b.has_effect('stunned') and not w.status_effects
    assert not g._cock_crow(bird)                             # hoarse until the next floor
    g.dungeon_level = 11
    assert g._cock_crow(bird)


def test_the_kit_apply_labels_say_what_the_counters_do():
    from game_arsenal import ArsenalMixin
    bird = items.make_item_by_id('accessory', 'caged_cockerel')
    wax = items.make_item_by_id('accessory', 'beeswax_earplugs')
    fake = SimpleNamespace(player=SimpleNamespace(ears_stopped=False, inventory=[wax], shield=None))
    assert ArsenalMixin._apply_label(fake, bird) == 'Let It Crow'
    assert ArsenalMixin._apply_label(fake, wax) == 'Put In'
