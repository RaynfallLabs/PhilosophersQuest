"""Five item bugs found while writing every scroll's, potion's and wand's card
(3.6.1, 2026-11-22). Brandon: "keep working on getting everything in".

1. The Wand of Wonder's fireball killed with no kill: no loot, no credit.
2. Enchant Item put a plus on rings, amulets and lesser armour pieces, where a
   plus does nothing: they take an enchantment level, as Enchant Armour gives.
3. The Dead Sea Scroll said it survived its reading; it is spent.
4. The disintegrate wand's comment said 85 in 100; it does 70.
5. A cursed wand's misfire said the charge was "doubly wasted"; one is lost.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()
_G = None


def _game():
    global _G
    from main import Game
    from game_states import STATE_PLAYER
    if _G is None:
        random.seed(2)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_item_bugs_361__')
        _G._autosave = lambda *a, **k: None
    _G.state = STATE_PLAYER
    _G.monsters, _G.pets = [], []
    return _G


def test_a_wonder_fireball_kill_is_a_kill(monkeypatch):
    import json
    from items import load_items
    from monster import Monster
    g = _game()
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    foe = Monster({**mons['giant_rat'], 'id': 'giant_rat'}, g.player.x + 1, g.player.y)
    foe.hp = 1
    g.monsters = [foe]
    killed = []
    monkeypatch.setattr(g, '_in_hero_reach', lambda m: True)
    monkeypatch.setattr(g, '_on_monster_killed', lambda m, *a, **k: killed.append(m))
    wand = next(w for w in load_items('wand') if w.effect == 'wonder')
    g._wonder_fireball(wand, random.Random(1))
    assert not foe.alive and killed == [foe]


def _ladder_ring():
    from items import load_items
    for it in load_items('accessory'):
        if getattr(it, 'is_unique', False):
            continue
        lv = int(getattr(it, 'ench_level', 0) or 0)
        if it.relevel(lv + 1) == lv + 1:
            it.relevel(lv)
            return it
    raise AssertionError('no common ring or amulet with a ladder')


def _strip(g):
    p = g.player
    p.weapon = None
    p.ranged_weapon = None
    p.shield = None
    p.armor_slots = [None] * len(p.armor_slots)
    p.accessory_slots = [None] * len(p.accessory_slots)


def _enchant_item():
    """The lowest Enchant Item scroll, uncursed."""
    from items import load_items
    s = min((s for s in load_items('scroll') if s.effect == 'enchant_item'),
            key=lambda s: int(getattr(s, 'tier', 1) or 1))
    s.buc = 'uncursed'
    return s


def test_enchant_item_raises_a_rings_level_not_a_dead_plus():
    g = _game()
    _strip(g)
    ring = _ladder_ring()
    lv = int(getattr(ring, 'ench_level', 0) or 0)
    plus = int(getattr(ring, 'enchant_bonus', 0) or 0)
    g.player.accessory_slots[0] = ring
    g._apply_scroll_effect(_enchant_item())
    assert int(ring.ench_level) > lv
    assert int(getattr(ring, 'enchant_bonus', 0) or 0) == plus


def test_enchant_item_raises_a_lesser_pieces_level():
    import gear
    from items import ARMOR_SLOTS, load_items
    g = _game()
    _strip(g)
    lesser = [i for i, s in enumerate(ARMOR_SLOTS) if s not in gear.CORE_SLOTS]
    slot = ARMOR_SLOTS[lesser[0]]
    piece = next(a for a in load_items('armor') if getattr(a, 'slot', '') == slot)
    assert piece.relevel(1) == 1
    g.player.armor_slots[lesser[0]] = piece
    g._apply_scroll_effect(_enchant_item())
    assert int(piece.ench_level) > 1


def test_the_false_lines_are_gone():
    src = ''.join(open(os.path.join(ROOT, 'src', f), encoding='utf-8').read()
                  for f in ('game_magic.py', 'game_combat.py'))
    assert 'survives your reading' not in src
    assert 'doubly wasted' not in src
    assert '# 85% instant kill. Bosses immune' not in src
