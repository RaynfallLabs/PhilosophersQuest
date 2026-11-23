"""Said Once (src/said_once.py; Brandon, 2026-11-22): "Repetitive messages
like 'You know how to butcher.. X. No question needed' is just noise. The
player gets it."

A line that tells the hero a known kind spares him a question (Butchered
Before, Known by Hand, a chain-equip legend put back on) is said the first
time it does so for that kind, then never again this run. The marks on the
corpse card, the Bestiary and the equip menus stay.
"""
import json
import os
import pickle
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import butchered  # noqa: E402
import known_by_hand as kbh  # noqa: E402
import said_once  # noqa: E402
from items import Corpse  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


def _player():
    from player import Player
    return Player()


def _corpse(kind='giant_rat'):
    return Corpse(MONS[kind]['name'], kind, 0, 0, harvest_tier=1,
                  monster_def={'tags': MONS[kind].get('tags', []),
                               'peak_floor': MONS[kind].get('peak_floor', 1)})


class _Item:
    def __init__(self, id_, unique=False):
        self.id = id_
        self.is_unique = unique


# ---------------------------------------------------------------- the rule

def test_first_is_true_once_per_topic_and_kind():
    p = _player()
    assert said_once.first(p, 'butchered', 'giant_rat')
    assert not said_once.first(p, 'butchered', 'giant_rat')
    assert said_once.said(p, 'butchered', 'giant_rat')
    assert said_once.first(p, 'butchered', 'goblin'), 'another kind is told'
    assert said_once.first(p, 'by_hand', 'giant_rat'), 'another topic is told'


def test_no_hero_or_no_kind_always_says_it():
    assert said_once.first(None, 'butchered', 'giant_rat')
    assert said_once.first(None, 'butchered', 'giant_rat')
    p = _player()
    assert said_once.first(p, 'butchered', '') and said_once.first(p, 'butchered', '')


def test_what_was_said_survives_a_save_and_an_old_save_starts_empty():
    p = _player()
    said_once.first(p, 'butchered', 'giant_rat')
    q = pickle.loads(pickle.dumps(p))
    assert not said_once.first(q, 'butchered', 'giant_rat')
    q.__dict__.pop('said_once')
    assert said_once.first(q, 'butchered', 'giant_rat')


# ---------------------------------------------------------- the two lines

def test_the_butcher_line_is_said_once_per_kind():
    p = _player()
    line = "You know how to butcher a Giant Rat. No question needed."
    assert butchered.fires_line(_corpse(), p) == line
    assert butchered.fires_line(_corpse(), p) == ''
    assert butchered.fires_line(_corpse(), p) == ''
    other = 'orc_scout' if 'orc_scout' in MONS else 'goblin'
    assert butchered.fires_line(_corpse(other), p).startswith('You know how to butcher ')
    assert butchered.fires_line(_corpse(other), p) == ''
    # Without the hero (a card, a test) the words are always there.
    assert butchered.fires_line(_corpse()) == line


def test_the_known_by_hand_line_is_said_once_per_kind():
    p = _player()
    plate = _Item('iron_breastplate')
    assert kbh.fires_line(plate, p) == kbh.FIRES_LINE
    assert kbh.fires_line(_Item('iron_breastplate'), p) == ''
    assert kbh.fires_line(_Item('mithril_breastplate'), p) == kbh.FIRES_LINE
    crown = _Item('crown_of_minos', unique=True)
    assert kbh.fires_line(crown, p) == kbh.FIRES_LINE_UNIQUE
    assert kbh.fires_line(crown, p) == ''
    assert kbh.fires_line(plate) == kbh.FIRES_LINE


def test_dressing_a_known_kind_says_it_the_first_time_only():
    from game_dressing import DressingMixin

    class G:
        _dress_known = DressingMixin._dress_known

        def __init__(self):
            self.player = _player()
            self.msgs, self.on = [], []

        def add_message(self, text, cat='info'):
            self.msgs.append(text)

        def _dress_begin_on(self, item, tier=0):
            self.on.append(item)

    g = G()
    a, b = _Item('iron_breastplate'), _Item('iron_breastplate')
    g._dress_known(a)
    g._dress_known(b)
    g._dress_known(a)
    assert g.on == [a, b, a], 'it still goes on every time'
    assert g.msgs == [kbh.FIRES_LINE]
