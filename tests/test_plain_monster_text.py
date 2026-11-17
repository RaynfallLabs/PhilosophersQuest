"""Plain monster text (Brandon, 2026-11-16: "your writing is confusing and
crappy... What does 'Tremor-Sense: a thread trembles, and you see what waits
on it' mean?... two separate messages... 'You know what something is made
of.' Huh?... 'Magic hurts it most (double damage)' hurts WHAT? why a whole
nother message? this is clutter... all the 'double' and 'half' damage is
unnecessary... can be defined in our hints").

  * A technique's line says what happened and, when it has one, names the
    creature; one sent with no creature still reads (no "{the}" left).
  * What a known kind is made of is ONE line that names it (tells.lore_line).
  * No multiplier in the log, the Bestiary or the fight strip; the help page
    and a hint say what the words mean.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import affinity  # noqa: E402
import family_edges  # noqa: E402
import tells  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
NUMBERS = ('double', 'half damage', 'quarter', 'triple', '(x', ' damage)')


def _m(kind):
    d = dict(MONS[kind])
    d['id'] = kind
    m = Monster(d, 1, 1)
    m._aware = True
    return m


def _trigger_lines():
    d = json.load(open(os.path.join(ROOT, 'data', 'monster_families.json'), encoding='utf-8'))
    out = []

    def walk(o):
        if isinstance(o, dict):
            if o.get('trigger_msg'):
                out.append(o['trigger_msg'])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    return out


def test_every_technique_line_reads_with_or_without_a_creature():
    lines = _trigger_lines()
    assert len(lines) >= 60
    spider = _m('giant_spider')
    for t in lines:
        for m in (None, spider):
            said = family_edges.line_for(t, m)
            assert '{' not in said and '}' not in said, (t, said)


class _Hero:
    def __init__(self, x=10, y=10):
        self.x, self.y = x, y


def _sense(kind, fid, at):
    """The line a sensing technique says of a hidden ``kind`` at ``at``."""
    fams = json.load(open(os.path.join(ROOT, 'data', 'monster_families.json'), encoding='utf-8'))
    root = fams.get('families', fams)
    found = []

    def walk(o):
        if isinstance(o, dict):
            if o.get('effect') == 'sense_hidden' and o.get('trigger_msg'):
                found.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(root[fid])
    m = _m(kind)
    m._aware = False                       # still lurking: the game calls it "something"
    m.x, m.y = at
    hero = _Hero()
    family_edges.tell(hero, m, found[0])
    return hero.__dict__['_edge_msgs'][-1]


def test_tremor_sense_sets_the_scene_and_names_what_is_hiding():
    """Brandon 2026-11-16: "What web? Where is there? Set the stage like
    you're an adventurer in a dungeon." What the hero notices, where, and
    the creature by its real name even while it lurks."""
    said = _sense('giant_spider', 'vermin', (12, 9))
    assert said == ('Tremor-Sense: you notice sticky, pale strands stretched across the passage '
                    'a few steps to the north-east. A web! It trembles ever so slightly, and you '
                    'spot a Giant Spider lying in wait on it!')
    # No web for a creature that spins none: its own scene.
    assert 'ceiling right beside you to the east' in _sense('piercer', 'vermin', (11, 10))
    assert 'a Grick, lying in wait' in _sense('grick', 'vermin', (10, 15))
    assert 'It is a Mimic' in _sense('mimic', 'aberrations', (9, 9))
    for kind, fid in (('giant_spider', 'vermin'), ('mimic', 'aberrations'),
                      ('haunting_presence', 'ghosts')):
        line = _sense(kind, fid, (13, 10))
        assert _m(kind).name in line, line              # its real name, not "something"
        assert 'to the east' in line and '{' not in line


def test_where_says_which_way_and_how_far():
    hero = _Hero()
    spot = _m('giant_spider')
    for (x, y), want in (((11, 10), 'right beside you to the east'),
                         ((8, 8), 'a few steps to the north-west'),
                         ((10, 16), 'to the south')):
        spot.x, spot.y = x, y
        assert family_edges.where(hero, spot) == want


@pytest.mark.parametrize('kind', sorted(k for k, v in MONS.items() if isinstance(v, dict)))
def test_no_multiplier_in_the_lore_line_or_the_bestiary(kind):
    m = _m(kind)
    line = tells.lore_line(m)
    assert not any(n in line.lower() for n in NUMBERS), line
    assert len(tells.lore_lines(m)) <= 1
    if line:
        assert line.startswith(m.name.split()[0]) or line.startswith('The ') or line[:1].isupper()
    for _kind, text in affinity.bestiary_rows(MONS[kind]):
        assert '(Double' not in text and '(Half' not in text and '(Quarter' not in text, text
        assert 'Damage)' not in text, text


def test_the_words_are_defined_once_for_the_player():
    help_page = json.load(open(os.path.join(ROOT, 'data', 'ui', 'how_quizzes_work.json'), encoding='utf-8'))
    rows = {r[0]: r[1] for s in help_page['sections'] for r in s.get('rows', ())}
    for word in ('Weak To', 'Hurt Most By', 'Resists', 'Shrugs Off', 'Hardest Blow', 'Immune To',
                 'Falls Easily To'):
        assert word in rows, word
    # The numbers the page gives are the game's own.
    assert affinity.weak_step() == 2.0 and 'twice' in rows['Weak To']
    assert affinity.resisted_step() == 0.5 and 'half' in rows['Resists']
    assert affinity.shrugs_step() == 0.25 and 'quarter' in rows['Shrugs Off']
    assert affinity.cap() == 3.0 and 'three times' in rows['Hardest Blow']
    hints = json.load(open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8'))
    assert any('Weak To' in h and 'Shrugs Off' in h for h in hints['1'])
