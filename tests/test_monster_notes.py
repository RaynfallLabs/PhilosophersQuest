"""Monster notes in versions for what the hero knows (2026-11-12).

Brandon, from his first play of Dungeon Alive: the notes "give away what a
monster is AND how to approach it, without you having seen it or identified
it." Then: "a player only needs to id a couple of corpses to recognize
everything? that seems a little too easy". So (src/tells.py,
family_lore.knowledge):

  UNKNOWN  the sign only, what the eye sees;
  KIN      its family at Recognise or Forewarned: the sign, its family and
           what it does, never how to beat it;
  KNOWN    the kind studied, its page opened, or its family at Lore: all
           that, what to do, and what it fears.

A counter never tells the hero to keep his distance from a creature that
can do the thing from across a room.
"""
import json
import os
import sys
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import family_lore  # noqa: E402
import tells  # noqa: E402
from family_lore import KIN, KNOWN, UNKNOWN  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))

# Words that name a mechanic or a counter: never in a sign.
_TELLING = ('mirror', 'aegis', 'pillar', 'distance', 'from afar', 'corner', 'ranged',
            'kill it', 'finish it', 'do not', 'never fight', 'keep out', 'poison', 'paralys',
            'freeze', 'frozen', 'sleep', 'charge', 'split', 'heal', 'drain', 'blind', 'confus',
            'silence', 'stun', 'bleed', 'burn', 'hallucinat', 'teleport', 'revive', 'regenerat',
            'it can', 'can hold', 'study')
# What only a creature that must come close can be told.
_CLOSE_ONLY = ('from a distance', 'keep your distance', 'do not let it reach you',
               'keep out of its reach', 'do not let it close', 'before it reaches you')


def _m(kind, x=5, y=5):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def _hero(**kw):
    return SimpleNamespace(studied_monster_ids=set(), lore_known_monster_ids=set(),
                           family_lore_grants={}, **kw)


def test_every_tell_has_a_sign_what_it_does_and_a_counter():
    d = tells.data()
    assert set(d['order']) == set(d['effects'])
    for key, e in d['effects'].items():
        assert isinstance(e, dict), key
        assert e.get('sign', '').strip(), key
        assert e.get('does', '').strip(), key
        assert 'counter' in e, key
    assert '{kin}' in d['kin_lead']
    assert '{words}' in d['weak_one'] and '{words}' in d['weak_many']
    assert d['far_counter'].strip()


def test_a_sign_never_names_the_mechanic_or_the_counter():
    for key, e in tells.data()['effects'].items():
        low = e['sign'].lower()
        for w in _TELLING:
            assert w not in low, (key, w, e['sign'])
        assert e['sign'].count('.') == 1, (key, 'one sentence')


def test_no_two_signs_look_alike():
    signs = [e['sign'] for e in tells.data()['effects'].values()]
    assert len(set(signs)) == len(signs)


def test_knowledge_levels():
    hero = _hero()
    assert family_lore.knowledge(hero, 'ghoul') == UNKNOWN
    hero.family_lore_grants = {'restless_dead': 1}
    assert family_lore.knowledge(hero, 'ghoul') == KIN
    hero.family_lore_grants = {'restless_dead': 2}
    assert family_lore.knowledge(hero, 'ghoul') == KIN
    hero.family_lore_grants = {'restless_dead': family_lore.full_lore_tier()}
    assert family_lore.knowledge(hero, 'ghoul') == KNOWN
    hero = _hero()
    hero.studied_monster_ids.add('ghoul')
    assert family_lore.knowledge(hero, 'ghoul') == KNOWN
    hero = _hero()
    hero.lore_known_monster_ids.add('ghoul')          # the Book of Thoth, Omnisight
    assert family_lore.knowledge(hero, 'ghoul') == KNOWN
    assert family_lore.knowledge(None, 'ghoul') == UNKNOWN


def test_two_corpses_no_longer_teach_how_to_beat_a_whole_family():
    """Recognise (tier 1) after studying the cheapest kinds tells the hero
    what the family's creatures do, not how to beat them."""
    hero = _hero()
    need = family_lore.thresholds('restless_dead')[0]
    others = [k for k in family_lore.members('restless_dead')
              if k != 'ghoul' and not family_lore.is_keystone(k)][:need]
    hero.studied_monster_ids.update(others)
    assert family_lore.tier(hero, 'restless_dead') == 1
    assert family_lore.knowledge(hero, 'ghoul') == KIN


def test_the_three_versions_of_one_tell():
    ghoul = _m('ghoul')
    assert tells.abilities(ghoul)[0] == 'paralyzed'
    unknown = tells.line(ghoul, 'paralyzed', UNKNOWN, 'the restless dead')
    kin = tells.line(ghoul, 'paralyzed', KIN, 'the restless dead')
    known = tells.line(ghoul, 'paralyzed', KNOWN, 'the restless dead')
    assert unknown.startswith('The Ghoul') and 'hold you' not in unknown
    assert 'distance' not in unknown and 'restless dead' not in unknown
    assert kin.startswith(unknown) and 'restless dead' in kin and 'hold you still' in kin
    assert 'distance' not in kin
    assert known.startswith(unknown) and 'hold you still' in known and 'distance' in known
    assert 'restless dead' not in known


def test_a_counter_is_honest_about_reach():
    """No creature that can do the thing from across a room is met with
    "fight it from a distance"."""
    far = 0
    for kind, d in MONS.items():
        if not d.get('attacks'):
            continue
        m = _m(kind)
        for key in tells.abilities(m):
            if tells.reach(m, key) != 'far' or key in tells._FLAGS:
                continue
            far += 1
            low = tells.line(m, key, KNOWN).lower()
            for w in _CLOSE_ONLY:
                assert w not in low, (kind, key, low)
    assert far > 10


def test_a_close_confuser_says_keep_your_distance_and_a_far_one_does_not():
    close = [k for k, v in MONS.items()
             if any(a.get('effect') == 'confused' and float(a.get('effect_chance', 0)) >= 0.3
                    for a in v.get('attacks', []))
             and v.get('ai_pattern') not in tells._FAR_AIS]
    far = [k for k, v in MONS.items()
           if v.get('ai_pattern') == 'ranged'
           and any(a.get('effect') == 'confused' and a.get('ranged') for a in v.get('attacks', []))]
    assert close and far
    m = _m(close[0])
    assert tells.reach(m, 'confused') == 'close'
    assert 'distance' in tells.line(m, 'confused', KNOWN)
    f = _m(far[0])
    assert tells.reach(f, 'confused') == 'far'
    low = tells.line(f, 'confused', KNOWN).lower()
    assert 'distance' not in low and 'stone between you' in low


def test_splits_name_the_blows_that_split_it():
    pud = _m('black_pudding')
    known = tells.line(pud, 'splits', KNOWN)
    assert 'cutting blow' in known and 'lightning' in known and '{' not in known
    assert 'weak blow' in tells.line(_m('tiamat_blood'), 'splits', KNOWN)


def test_the_weakness_line():
    assert tells.weak_line(_m('troll')) == 'Fire and acid hurt it most.'
    assert tells.weak_line(_m('ghoul')) == 'Holy power and a cutting blow hurt it most.'
    m = _m('ghoul')
    m.weaknesses = []
    assert tells.weak_line(m) == ''


def test_every_line_fills_in_and_uses_no_singular_they():
    for kind, d in MONS.items():
        if not d.get('attacks'):
            continue
        m = _m(kind)
        for key in tells.abilities(m):
            for level in (UNKNOWN, KIN, KNOWN):
                t = tells.line(m, key, level, 'the restless dead')
                assert '{' not in t and t[:1].isupper(), (kind, key, t)
                low = f" {t.lower()} "
                assert ' they ' not in low and ' their ' not in low and ' them ' not in low, t


# -- First sight: said as far as the hero knows the kind, again when he knows more --

class _G:
    from game_combat import CombatMixin
    _maybe_tell = CombatMixin._maybe_tell

    def __init__(self, hero):
        self.player = hero
        self.msgs = []

    def add_message(self, text, cat='info'):
        self.msgs.append(text)


def test_first_sight_says_more_as_the_hero_learns():
    hero = _hero()
    g = _G(hero)
    ghoul = _m('ghoul')
    g._maybe_tell(ghoul)
    assert len(g.msgs) == 1 and 'distance' not in g.msgs[0] and 'hold you' not in g.msgs[0]
    g._maybe_tell(ghoul)
    assert len(g.msgs) == 1, 'once per run at what he knows'
    hero.family_lore_grants = {'restless_dead': 1}
    g._maybe_tell(ghoul)
    assert len(g.msgs) == 2 and 'restless dead' in g.msgs[1] and 'distance' not in g.msgs[1]
    hero.studied_monster_ids.add('ghoul')
    g._maybe_tell(ghoul)
    # The tell with its counter, then what it is made of (tells.lore_lines,
    # winning-build plan 3.1): weaknesses, resistances, its nature.
    lore = tells.lore_lines(ghoul)
    assert len(lore) == 3
    assert len(g.msgs) == 3 + len(lore)
    assert 'distance' in g.msgs[2] and g.msgs[3] == 'Holy power and a cutting blow hurt it most.'
    assert g.msgs[3:] == lore and 'a thrust' in lore[1] and 'put to sleep' in lore[2]
    n = len(g.msgs)
    g._maybe_tell(ghoul)
    assert len(g.msgs) == n


def test_a_known_kind_seen_first_gets_the_whole_line_at_once():
    hero = _hero()
    hero.studied_monster_ids.add('troll')
    g = _G(hero)
    g._maybe_tell(_m('troll'))
    assert 'do not wear it down' in g.msgs[0] and g.msgs[1] == 'Fire and acid hurt it most.'
    assert g.msgs[2] == 'It is easily confused. Fire puts it to flight.'


def test_a_known_kind_with_no_tell_is_still_told_what_it_is_made_of():
    """At KNOWN the lore lines come tell or no tell; below it, nothing."""
    hero = _hero()
    g = _G(hero)
    plain = next(k for k in ('kobold', 'giant_rat', 'goblin', 'mud_crab', 'skeleton')
                 if k in MONS and not tells.abilities(_m(k)) and tells.lore_lines(_m(k)))
    g._maybe_tell(_m(plain))
    assert g.msgs == []
    hero.studied_monster_ids.add(plain)
    g._maybe_tell(_m(plain))
    # Named first, so the lines' "it" stands for someone (bug bash WB-E02).
    assert g.msgs == [tells.known_lead(_m(plain))] + tells.lore_lines(_m(plain))
    assert _m(plain).name.lower() in g.msgs[0].lower()


def test_a_save_from_before_the_versions_still_says_the_known_line():
    hero = _hero()
    hero.studied_monster_ids.add('ghoul')
    g = _G(hero)
    g._dungeon_alive = {'domains_seen': [], 'told': ['ghoul']}
    g._maybe_tell(_m('ghoul'))
    assert g.msgs and 'distance' in g.msgs[0]


def test_a_creature_with_no_tell_says_nothing_on_sight():
    """...and nothing about what it is made of when there is nothing to say
    (a goblin is flesh like a man)."""
    hero = _hero()
    g = _G(hero)
    plain = next(k for k in ('kobold', 'giant_rat', 'jackal', 'goblin')
                 if k in MONS and not tells.abilities(_m(k)) and not tells.lore_lines(_m(k)))
    g._maybe_tell(_m(plain))
    hero.studied_monster_ids.add(plain)
    g._maybe_tell(_m(plain))
    assert g.msgs == []
