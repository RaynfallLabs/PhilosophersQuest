"""Bug bash 3.3.1: what the independent review of the combined fixes found.

1. A weapon's on-hit status (Wendigo's Fang: slowed on 35% of hits) counted
   as a worn grant once every accessory removal went through
   Player.drop_worn_status: a lifted Ring of Slowing's slow stayed for good.
2. A Tyet spent at tier 1 (its life is the base effect there) gave a fresh
   life when attuned again at a higher tier.
3. The Helm of Aragorn's command picked a mindless undead (a bone colossus),
   spent its charge and did nothing.
4. A bought stack merged into a found one lost its resale cap.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
from quiz_engine import QuizResult  # noqa: E402

pygame.init()


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_review__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def test_a_weapons_on_hit_status_does_not_keep_a_rings_slow(game):
    p = game.player
    fang = items.make_item_by_id('weapon', 'wendigo_fang')
    p.inventory.append(fang)
    p._apply_equip(fang)
    p.remove_from_inventory(fang)
    ring = items.make_item_by_id('accessory', 'ring_curse_slow')
    ring.buc = 'uncursed'
    p.inventory.append(ring)
    p._apply_equip(ring)
    p.remove_from_inventory(ring)
    assert p.has_effect('slowed') or p.status_effects.get('slowed') == -1
    game._unequip_slot(f'accessory_{p.accessory_slots.index(ring)}', ring)
    assert 'slowed' not in p.status_effects


def _attune(g, item, tier):
    if item not in g.player.inventory:
        g.player.inventory.append(item)
    g._equip_accessory(item)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=tier, correct=tier, asked=tier))
    assert g.player.amulet_slot is item


def _die(g):
    g.player.hp = 0
    g._answer_a_killing_blow()
    return g.player.hp > 0


def test_a_tyet_spent_at_tier_one_gives_no_life_at_tier_two(game):
    p = game.player
    tyet = items.make_item_by_id('accessory', 'tyet_of_isis')
    _attune(game, tyet, 1)
    assert _die(game)
    p.hp = 10
    game._unequip_slot('amulet', tyet)
    _attune(game, tyet, 2)
    assert not p.has_effect('life_save')
    assert not _die(game)


def test_aragorns_command_skips_a_mindless_undead(game):
    import json
    from monster import Monster
    from chain_passives import player_has_passive
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    kind = next(k for k, d in defs.items()
                if {'undead', 'construct'} <= set(d.get('tags') or ())
                and not d.get('is_boss') and 'legendary' not in (d.get('tags') or ()))
    m = Monster(dict(defs[kind], id=kind), game.player.x + 1, game.player.y)
    game.monsters = [m]
    game.visible = {(m.x, m.y), (game.player.x, game.player.y)}
    import chain_passives
    orig = chain_passives.player_has_passive
    chain_passives.player_has_passive = lambda pl, flag: flag == 'command_undead' or orig(pl, flag)
    try:
        assert player_has_passive is not None
        game.player._chain_passive_charges = {}
        game._refresh_fov()
    finally:
        chain_passives.player_has_passive = orig
    assert not getattr(m, '_oathbound', False)
    assert not m.has_effect('charmed')


def test_a_bought_stacks_price_survives_a_merge():
    from player import Player
    p = Player()
    found = items.make_item_by_id('ammo', 'iron_arrow')
    bought = items.make_item_by_id('ammo', 'iron_arrow')
    bought._bought_for = 40.0
    for it in (found, bought):
        it.buc_known = True
    assert p.add_to_inventory(found)
    assert p.add_to_inventory(bought)
    stacks = [i for i in p.inventory if i.id == 'iron_arrow']
    assert len(stacks) == 1
    assert stacks[0]._bought_for == 40.0
