"""data/achievements.json: the shipped catalogue.

Brandon's rules (2026-10-25): every name is always shown, so no name may
spoil; hints are VERY light and point at the source material (the myth, the
film, the game an egg comes from), never at the mechanic; the deepest
fourth-wall ones show only "???"; no achievement for being a bad guy.
"""
import json
import re
from pathlib import Path

import achievements as ach

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data' / 'achievements.json').read_text(encoding='utf-8'))
ENTRIES = DATA['achievements']
SHIPPED = (ROOT / 'tests' / 'data' / 'achievement_ids_shipped.txt').read_text(encoding='utf-8').split()

# The deepest secrets: a name and "???" (Brandon: "no hints that give them the idea").
QUESTION_MARKS_ONLY = {'behind_curtain', 'not_dead_yet'}
# Words a secret's hint may never use: they describe how, not what.
MECHANIC_WORDS = ('floor', 'floors', 'turn', 'turns', 'press', 'key', 'type', 'typed',
                  'poke', 'quiz', 'chain', 'pick up', 'pick it', 'wear', 'inventory',
                  'karma', 'level')
SMALL = {'a', 'an', 'the', 'of', 'to', 'in', 'on', 'for', 'and', 'but', 'or', 'at', 'by',
         'from', 'with', 'is', 'it'}


def test_the_catalogue_validates():
    assert ach.validate(DATA) == []


def test_every_shipped_achievement_is_still_here():
    """Codes are made from ids: a removed or renamed id strands a child's code."""
    ids = {a['id'] for a in ENTRIES}
    assert [i for i in SHIPPED if i not in ids] == []


def test_names_are_title_case():
    bad = []
    for a in ENTRIES:
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", a['name'].lstrip("'"))
        for i, w in enumerate(words):
            if w.lower() in SMALL and i > 0:
                continue
            if not w[0].isupper():
                bad.append(a['name'])
                break
    assert bad == []


def test_hints_and_texts_read_as_sentences():
    for a in ENTRIES:
        if a['id'] in QUESTION_MARKS_ONLY:
            assert a['hint'] == '???', a['id']
            continue
        assert a['hint'] != '???', a['id']
        for field in ('hint', 'unlocked_text'):
            text = a[field].strip()
            assert text[0].isupper() or text[0] in "'\"", (a['id'], field)
            assert text.endswith(('.', '!', '?', '...', '."', "'")), (a['id'], field)
            assert '--' not in text, (a['id'], field)


def test_secret_hints_never_describe_the_mechanic():
    bad = []
    for a in ENTRIES:
        if a['category'] != 'secrets':
            continue
        hint = a['hint'].lower()
        bad += [(a['id'], w) for w in MECHANIC_WORDS if re.search(rf'\b{w}\b', hint)]
    assert bad == []


def test_no_achievement_for_villainy():
    for a in ENTRIES:
        blob = json.dumps(a['trigger'])
        assert '"wrong"' not in blob and '"broke"' not in blob and '"lapsed"' not in blob, a['id']
        if a['trigger'].get('event') == 'karma':
            assert a['trigger']['where']['value'] > 0, a['id']


def test_every_counter_is_used():
    used = set()

    def walk(t):
        for k in ('all', 'any'):
            for p in t.get(k, ()):
                walk(p)
        used.update(v for k, v in t.items() if k in ('stat', 'run'))
    for a in ENTRIES:
        walk(a['trigger'])
    assert set(DATA['counters']) - used == set()


def test_art_ids_are_unique():
    arts = [a['art'] for a in ENTRIES]
    assert len(arts) == len(set(arts))


def test_every_badge_is_installed():
    """Brandon's D5: the art ships with the system. Each `art` stem has its
    128 px PNG in assets/achievements (a missing one would quietly fall back
    to the plain medallion)."""
    import pygame
    missing, wrong = [], []
    for a in ENTRIES:
        path = ROOT / 'assets' / 'achievements' / f"{a['art']}.png"
        if not path.exists():
            missing.append(a['art'])
        elif pygame.image.load(str(path)).get_size() != (128, 128):
            wrong.append(a['art'])
    assert missing == [] and wrong == []
