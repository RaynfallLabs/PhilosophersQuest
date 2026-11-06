"""Bug bash 3.3.1, magic: Turn Undead (B4), the Heart of Ahriman's charge
(B5), banishment (B8) and enchanting a ranged weapon (B10).

Behaviour tests on a real headless Game. The feel in play is a play-test
question: Claude cannot drive Pygame.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402

_SCREEN = None
_DEFS = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_bugbash_331_magic__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _defs():
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    return _DEFS


def _mdef(kind):
    d = dict(_defs()[kind])
    d.setdefault('id', kind)
    return d


def _open_floor(g, r=5):
    from dungeon import FLOOR
    for yy in range(g.player.y - r, g.player.y + r + 1):
        for xx in range(g.player.x - r, g.player.x + r + 1):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR


def _spawn(g, kind, dx=1, dy=0, hp=None):
    from monster import Monster
    m = Monster(_mdef(kind), g.player.x + dx, g.player.y + dy)
    if hp is not None:
        m.max_hp = m.hp = hp
    m._aware = True
    g.monsters.append(m)
    g.visible = set(g.visible) | {(m.x, m.y)}
    return m


def _zap(g, wand_id, target=None):
    w = items.make_item_by_id('wand', wand_id)
    w.charges = 5
    g._wand_override_target = target
    try:
        g._apply_wand_effect(w)
    finally:
        g._wand_override_target = None


# ---------------------------------------------------------------------------
# B4: Turn Undead reads the undead tag, not words in the monster's id
# ---------------------------------------------------------------------------

# Undead by tag whose ids hold none of the old words, and non-undead whose
# ids did (bone_golem is a construct, death_dog a beast).
_TAGGED_ONLY = ('jiangshi', 'specter', 'shadow', 'nosferatu')
_WORD_ONLY = ('bone_golem', 'death_dog', 'death_beetle')


def _turned(g, kinds, cast):
    mons = []
    for i, k in enumerate(kinds):
        mons.append(_spawn(g, k, dx=1 + (i % 3), dy=-1 + (i // 3), hp=10_000))
    cast()
    return {m.kind for m in mons if m.hp < 10_000 or m.has_effect('feared')}


def test_b4_turn_undead_wand_turns_every_undead_and_nothing_else():
    for k in _TAGGED_ONLY:
        assert 'undead' in _defs()[k]['tags']
    for k in _WORD_ONLY:
        assert 'undead' not in _defs()[k].get('tags', [])
    g = _game(seed=41)
    _open_floor(g)
    hit = _turned(g, _TAGGED_ONLY + _WORD_ONLY, lambda: _zap(g, 'wand_of_turn_undead'))
    assert hit == set(_TAGGED_ONLY), hit


def test_b4_turn_undead_spell_turns_every_undead_and_nothing_else():
    g = _game(seed=42)
    _open_floor(g)
    hit = _turned(g, _TAGGED_ONLY + _WORD_ONLY, lambda: g._apply_spell_effect(
        {'effect': 'turn_undead', 'power': '3d8', 'tier': 2, 'name': 'Turn Undead'}))
    assert hit == set(_TAGGED_ONLY), hit


def test_b4_no_undead_in_the_bestiary_lacks_the_tag():
    """The tag is the whole test now. Every member of the three undead
    families carries it, except the ker, a Greek death spirit (an outsider),
    which the old word list never matched either."""
    fams = {'restless_dead', 'ghosts', 'vampires_liches'}
    missing = sorted(k for k, v in _defs().items()
                     if v.get('family') in fams and 'undead' not in v.get('tags', []))
    assert missing == ['ker'], missing
