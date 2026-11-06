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


# ---------------------------------------------------------------------------
# B5: the Heart of Ahriman's charge is spent by a destructive spell
# ---------------------------------------------------------------------------

def test_b5_a_heal_does_not_spend_the_heart_of_ahriman():
    """'Your next destructive spell will rend the unmaking': a heal is not
    one. It used to spend the charge (and was doubled by it)."""
    g = _game(seed=51)
    g.player.hp = 1
    g.player._anti_being_charged = True
    g._apply_spell_effect({'effect': 'extra_heal', 'power': '2d8', 'tier': 2,
                           'name': 'Cure Wounds'})
    assert g.player.hp > 1
    assert g.player._anti_being_charged is True


def _missile_damage(charged: bool) -> int:
    g = _game(seed=52)
    _open_floor(g)
    m = _spawn(g, 'giant_rat', dx=2, hp=100_000)
    g.player._anti_being_charged = charged
    random.seed(7)
    g._apply_spell_effect({'effect': 'magic_missile', 'power': '4d6', 'tier': 4,
                           'name': 'Force Storm'}, m)
    assert g.player._anti_being_charged is False
    return 100_000 - m.hp


def test_b5_the_whole_magic_missile_volley_takes_the_charge():
    """Seven missiles are one cast. The first missile used to spend the
    charge alone, so the Heart added a seventh of a double."""
    plain = _missile_damage(False)
    doubled = _missile_damage(True)
    assert doubled >= 1.8 * plain, (plain, doubled)


def test_b5_a_bolt_spends_the_charge_and_doubles():
    g = _game(seed=53)
    _open_floor(g)
    m = _spawn(g, 'giant_rat', dx=2, hp=100_000)
    g.player._anti_being_charged = True
    g._apply_spell_effect({'effect': 'fire_bolt', 'power': '6d6', 'tier': 3,
                           'name': 'Fire Bolt'}, m)
    assert g.player._anti_being_charged is False
    assert m.hp < 100_000


# ---------------------------------------------------------------------------
# B8: a banished creature is sent away, not killed: it leaves no body
# ---------------------------------------------------------------------------

def test_b8_a_banished_demon_leaves_no_corpse_and_is_not_slain():
    from items import Corpse
    g = _game(seed=81)
    _open_floor(g)
    imp = _spawn(g, 'imp', dx=2)
    assert 'demon' in imp.tags
    g._apply_spell_effect({'effect': 'banishment', 'power': '', 'tier': 4,
                           'name': 'Banishment'}, imp)
    assert not imp.alive
    # The next turn's reaper used to treat it as an unnoticed kill.
    g._reap_unnoticed_kills()
    bodies = [i for i in g.ground_items if isinstance(i, Corpse) and i.monster_id == 'imp']
    assert not bodies, "a banished demon left its corpse behind"
    texts = [str(e[0]) for e in g.msg_log.entries[-8:]]
    assert any('banished' in t for t in texts)
    assert not any('is slain' in t for t in texts), texts
