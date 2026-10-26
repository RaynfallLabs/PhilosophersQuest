"""Achievements: the rules in data/achievements.json, judged against a
Seeker's profile (PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md section 2).

Pure module: no pygame and no Game import. The game only EMITS events
(``Book.apply(profile, run, 'kill', monster='duck_of_doom', ...)``); what each
event counts towards is data:

    "counters": {
      "questions_answered": {"on": "quiz_answer"},                      +1 each
      "right_math": {"on": "quiz_answer", "where": {"subject": "math", "correct": true}},
      "damage_dealt": {"on": "damage", "add": "amount"},                sum of a field
      "biggest_blow": {"on": "damage", "best": "amount"},               largest value
      "right_streak": {"on": "quiz_answer", "streak": {"correct": true}},  longest run
      "secret_builds": {"on": "run_start", "collect": "build"},         distinct values
      "kills_run": {"on": "kill", "scope": "run"}                       this run only
    }

and an achievement's ``trigger`` is one of a closed set:

    {"stat": counter, "at_least": n}     a lifetime counter (a set counts its size)
    {"run": counter, "at_least": n}      a counter of this run
    {"event": name, "where": {...}}      the event being applied right now
    {"all": [...]} / {"any": [...]}

``where`` values: a plain value must be equal; a list means "one of";
{"at_least": n}, {"not": v} and {"present": bool} compare. ``validate`` refuses
any name it does not know, so a typo can never make an achievement impossible
or free.
"""
from __future__ import annotations

import json
import re

# Every event the game emits, with the fields it carries. The closed set the
# data may name (tests/test_seeker_wiring.py checks each is emitted in src/).
KNOWN_EVENTS: dict[str, frozenset] = {name: frozenset(fields) for name, fields in {
    # quizzes
    'quiz_answer':      ('subject', 'correct', 'tier', 'chain', 'mode'),
    'study_answer':     ('subject', 'correct'),
    'card_opened':      ('subject',),
    'subject_cleared':  ('subject', 'tier'),
    'philosophy_tier':  ('tier',),
    # fighting
    'kill':             ('monster', 'ranged', 'unarmed', 'boss', 'legendary', 'family'),
    'damage':           ('amount', 'dealt', 'by'),
    'attack_chain':     ('chain',),
    'seals_broken':     ('count',),
    'story_way':        ('monster',),
    # the dungeon
    'floor_reached':    ('floor',),
    'floor_explored':   ('floor',),
    'trap':             ('kind',),
    'hellmouth':        (),
    # craft and survival
    'harvest':          ('monster',),
    'cooked':           ('recipe',),
    'lockpick':         (),
    'identify':         ('item',),
    'scroll_read':      ('scroll',),
    'wand_zapped':      ('wand',),
    'spell_learned':    ('spell',),
    'spell_cast':       ('spell',),
    'prayer_answered':  (),
    'intercession':     (),
    'gold':             ('amount',),
    'trade':            ('trader',),
    'mystery_solved':   ('altar',),
    # companions
    'pet_hatched':      ('pet', 'line'),
    'pet_evolved':      ('pet', 'line', 'stage'),
    'pet_level':        ('pet', 'line', 'level'),
    'rare_pet':         ('pet',),
    'dad_summoned':     (),
    'escort_delivered': ('person',),
    # lore
    'family_tier':      ('family', 'tier'),
    'circle':           ('circle',),
    'loremaster':       (),
    'monster_known':    ('monster',),
    'topic_read':       ('subject', 'topic'),
    'trait':            ('trait',),
    # character
    'deed':             ('kind', 'id', 'late'),
    'karma':            ('value',),
    'judgment':         ('outcome',),
    # journeys
    'run_start':        ('hero', 'build'),
    'run_end':          ('reason', 'victory', 'floor', 'grade', 'build', 'killer', 'cow_level'),
    'secret_victory':   (),
    # easter eggs
    'duck_worn':        (),
    'duck_hatched':     (),
    'xyzzy':            ('chain',),
    'cow_level':        (),
    'black_knight':     ('outcome',),
    'necronomicon':     ('outcome',),
    'forged':           ('item',),
    'tablet_complete':  (),
    'lore_found':       ('item',),
    'flux':             (),
    'ghost_met':        ('own',),
    'unicorn_joined':   (),
    # the title screen and the fourth wall
    'title_god':        (),
    'seeker_named':     ('name',),
    'konami':           (),
    'plugh':            (),
    'profile_edited':   (),
    'save_restored':    ('ended',),
}.items()}

RARITIES = ('common', 'rare', 'epic', 'legendary')
_ID_RE = re.compile(r'^[a-z0-9_]+$')
_WORD_RE = re.compile(r'^[A-Z]{2,12}$')
_REQUIRED = ('id', 'name', 'category', 'rarity', 'hint', 'unlocked_text', 'code_word',
             'art', 'trigger')
_COUNTER_KINDS = ('add', 'best', 'streak', 'collect')
_WHERE_OPS = ('at_least', 'not', 'present')


def _counter_kind(spec: dict) -> str:
    kinds = [k for k in _COUNTER_KINDS if k in spec]
    return kinds[0] if kinds else 'count'


def _where_ok(where, fields, where_from, problems):
    if where is None:
        return
    if not isinstance(where, dict):
        problems.append(f'{where_from}: where must be an object')
        return
    for k, v in where.items():
        if k not in fields:
            problems.append(f'{where_from}: the event has no field {k!r}')
        if isinstance(v, dict) and (len(v) != 1 or next(iter(v)) not in _WHERE_OPS):
            problems.append(f'{where_from}: unknown test {v!r}')


def _trigger_problems(t, counters, where_from) -> list[str]:
    out: list[str] = []
    if not isinstance(t, dict) or len(t) == 0:
        return [f'{where_from}: trigger must be an object']
    if 'all' in t or 'any' in t:
        key = 'all' if 'all' in t else 'any'
        parts = t[key]
        if len(t) != 1 or not isinstance(parts, list) or not parts:
            return [f'{where_from}: {key} must be the only key and a non-empty list']
        for i, p in enumerate(parts):
            out += _trigger_problems(p, counters, f'{where_from}.{key}[{i}]')
        return out
    if 'stat' in t or 'run' in t:
        key = 'stat' if 'stat' in t else 'run'
        name = t[key]
        spec = counters.get(name)
        if spec is None:
            out.append(f'{where_from}: no counter {name!r}')
        elif (spec.get('scope', 'life') == 'run') != (key == 'run'):
            out.append(f'{where_from}: counter {name!r} is not a {key} counter')
        if set(t) != {key, 'at_least'} or not isinstance(t.get('at_least'), int) \
                or t['at_least'] < 1:
            out.append(f'{where_from}: {key} needs a positive at_least and nothing else')
        return out
    if 'event' in t:
        name = t['event']
        if name not in KNOWN_EVENTS:
            return [f'{where_from}: unknown event {name!r}']
        if set(t) - {'event', 'where'}:
            out.append(f'{where_from}: an event trigger has only event and where')
        _where_ok(t.get('where'), KNOWN_EVENTS[name], where_from, out)
        return out
    return [f'{where_from}: unknown trigger {sorted(t)}']


def _first_threshold(t) -> tuple[str, str, int] | None:
    """('stat' or 'run', counter, n) of a trigger's first counter test."""
    if 'stat' in t or 'run' in t:
        key = 'stat' if 'stat' in t else 'run'
        return key, t[key], t['at_least']
    for key in ('all', 'any'):
        for p in t.get(key, ()):
            got = _first_threshold(p)
            if got:
                return got
    return None


def validate(data) -> list[str]:
    """Every problem in an achievements file (empty when it is good)."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ['the file must be an object']
    cats = data.get('categories')
    if not isinstance(cats, list) or not cats:
        problems.append('categories must be a non-empty list')
        cats = []
    cat_ids = [c.get('id') for c in cats if isinstance(c, dict)]
    if len(set(cat_ids)) != len(cat_ids) or any(not c.get('name') for c in cats):
        problems.append('categories need unique ids and names')
    counters = data.get('counters')
    if not isinstance(counters, dict):
        problems.append('counters must be an object')
        counters = {}
    for name, spec in counters.items():
        w = f'counter {name}'
        if not _ID_RE.match(name) or not isinstance(spec, dict):
            problems.append(f'{w}: bad name or spec')
            continue
        ev = spec.get('on')
        if ev not in KNOWN_EVENTS:
            problems.append(f'{w}: unknown event {ev!r}')
            continue
        kinds = [k for k in _COUNTER_KINDS if k in spec]
        if len(kinds) > 1:
            problems.append(f'{w}: only one of {", ".join(_COUNTER_KINDS)}')
        for k in ('add', 'best', 'collect'):
            if k in spec and spec[k] not in KNOWN_EVENTS[ev]:
                problems.append(f'{w}: event {ev} has no field {spec[k]!r}')
        if 'streak' in spec:
            _where_ok(spec['streak'], KNOWN_EVENTS[ev], w, problems)
        _where_ok(spec.get('where'), KNOWN_EVENTS[ev], w, problems)
        if spec.get('scope', 'life') not in ('life', 'run'):
            problems.append(f'{w}: scope is life or run')
        if set(spec) - {'on', 'where', 'scope', *_COUNTER_KINDS}:
            problems.append(f'{w}: unknown keys {sorted(set(spec) - {"on", "where", "scope", *_COUNTER_KINDS})}')
    achs = data.get('achievements')
    if not isinstance(achs, list) or not achs:
        return problems + ['achievements must be a non-empty list']
    seen_ids, seen_names, seen_words = set(), set(), set()
    ladders: dict[str, list] = {}
    for i, a in enumerate(achs):
        w = f"achievement {a.get('id', i) if isinstance(a, dict) else i}"
        if not isinstance(a, dict):
            problems.append(f'{w}: must be an object')
            continue
        for f in _REQUIRED:
            if not a.get(f):
                problems.append(f'{w}: no {f}')
        aid, name, word = a.get('id', ''), a.get('name', ''), str(a.get('code_word', ''))
        if aid and not _ID_RE.match(aid):
            problems.append(f'{w}: id must be lower_snake_case')
        for val, pool, what in ((aid, seen_ids, 'id'), (name.casefold(), seen_names, 'name'),
                                (word, seen_words, 'code word')):
            if val in pool:
                problems.append(f'{w}: duplicate {what} {val!r}')
            pool.add(val)
        if word and (not _WORD_RE.match(word) or word.startswith('DEV')):
            problems.append(f'{w}: code word must be 2-12 capital letters, never starting DEV')
        if a.get('category') not in cat_ids:
            problems.append(f'{w}: unknown category {a.get("category")!r}')
        if a.get('rarity') not in RARITIES:
            problems.append(f'{w}: rarity is one of {", ".join(RARITIES)}')
        if 'trigger' in a:
            problems += _trigger_problems(a['trigger'], counters, w)
        hint = str(a.get('hint', '')).casefold()
        for sw in a.get('spoiler_words', ()):
            if str(sw).casefold() in hint:
                problems.append(f'{w}: the hint gives away {sw!r}')
        if 'ladder' in a:
            if not isinstance(a.get('tier'), int):
                problems.append(f'{w}: a ladder entry needs an integer tier')
            else:
                ladders.setdefault(a['ladder'], []).append(a)
        # No "note" here: how a secret unlocks is Dad's (tools/dad/
        # achievement_notes.json), and this file ships inside the game.
        extra = set(a) - set(_REQUIRED) - {'ladder', 'tier', 'spoiler_words'}
        if extra:
            problems.append(f'{w}: unknown keys {sorted(extra)}')
    for lad, members in ladders.items():
        members.sort(key=lambda a: a['tier'])
        tiers = [a['tier'] for a in members]
        if tiers != list(range(1, len(tiers) + 1)):
            problems.append(f'ladder {lad}: tiers must run 1..{len(tiers)}')
        marks = [_first_threshold(a.get('trigger') or {}) for a in members]
        if None in marks or len({(m[0], m[1]) for m in marks if m}) != 1:
            problems.append(f'ladder {lad}: every tier must test the same counter')
        elif [m[2] for m in marks] != sorted({m[2] for m in marks}):
            problems.append(f'ladder {lad}: thresholds must rise with the tier')
    return problems


def _matches(where, fields: dict) -> bool:
    for k, want in (where or {}).items():
        have = fields.get(k)
        if isinstance(want, dict):
            op, v = next(iter(want.items()))
            if op == 'at_least':
                try:
                    if have is None or float(have) < float(v):
                        return False
                except (TypeError, ValueError):
                    return False
            elif op == 'not':
                if have == v:
                    return False
            elif op == 'present':
                if (have not in (None, '', False)) != bool(v):
                    return False
        elif isinstance(want, list):
            if have not in want:
                return False
        elif have != want:
            return False
    return True


class RunTally:
    """This run's counters (``scope: run``). A plain dict inside so it
    pickles into the save like the deeds register."""

    def __init__(self, data: dict | None = None):
        self.data = data if isinstance(data, dict) else {}
        for k in ('stats', 'best', 'sets', 'live'):
            self.data.setdefault(k, {})

    def stat(self, k):
        return int(self.data['stats'].get(k, 0))

    def best(self, k):
        return int(self.data['best'].get(k, 0))

    def members(self, k):
        return set(self.data['sets'].get(k, ()))

    def live(self, k):
        return int(self.data['live'].get(k, 0))

    def add(self, k, n=1):
        if n > 0:
            self.data['stats'][k] = self.stat(k) + int(n)

    def raise_best(self, k, v):
        self.data['best'][k] = max(self.best(k), int(v))

    def include(self, k, m):
        s = self.members(k)
        if str(m) in s:
            return False
        self.data['sets'][k] = sorted(s | {str(m)})
        return True

    def set_live(self, k, v):
        self.data['live'][k] = int(v)


class Book:
    """The loaded achievements and counters, indexed for quick judging."""

    def __init__(self, data: dict):
        self.data = data
        self.categories = list(data.get('categories', []))
        self.counters: dict = dict(data.get('counters', {}))
        self.entries: list[dict] = [a for a in data.get('achievements', [])]
        self.by_id = {a['id']: a for a in self.entries}
        self._on_event: dict[str, list[str]] = {}
        for name, spec in self.counters.items():
            self._on_event.setdefault(spec['on'], []).append(name)
        self._watchers: dict[str, list[dict]] = {}     # counter or 'event:x' -> entries
        for a in self.entries:
            for key in self._deps(a['trigger']):
                self._watchers.setdefault(key, []).append(a)

    def _deps(self, t) -> set:
        if 'all' in t or 'any' in t:
            out = set()
            for p in t.get('all', t.get('any', [])):
                out |= self._deps(p)
            return out
        if 'stat' in t:
            return {t['stat']}
        if 'run' in t:
            return {t['run']}
        return {'event:' + t['event']}

    # -- counters --------------------------------------------------------
    def value(self, name: str, profile, run: RunTally | None) -> int:
        spec = self.counters.get(name) or {}
        store = run if spec.get('scope', 'life') == 'run' else profile
        if store is None:
            return 0
        kind = _counter_kind(spec)
        if kind == 'collect':
            return len(store.members(name))
        if kind in ('best', 'streak'):
            return store.best(name)
        return store.stat(name)

    def _count(self, name: str, spec: dict, store, fields: dict) -> bool:
        """Apply one event to one counter. True if its value changed."""
        kind = _counter_kind(spec)
        if kind == 'streak':
            if not _matches(spec.get('where'), fields):
                return False
            if _matches(spec['streak'], fields):
                now = store.live(name) + 1
                store.set_live(name, now)
                if now > store.best(name):
                    store.raise_best(name, now)
                    return True
            else:
                store.set_live(name, 0)
            return False
        if not _matches(spec.get('where'), fields):
            return False
        if kind == 'collect':
            v = fields.get(spec['collect'])
            return v not in (None, '') and store.include(name, v)
        if kind == 'best':
            try:
                v = int(fields.get(spec['best']) or 0)
            except (TypeError, ValueError):
                return False
            if v > store.best(name):
                store.raise_best(name, v)
                return True
            return False
        n = 1
        if kind == 'add':
            try:
                n = int(fields.get(spec['add']) or 0)
            except (TypeError, ValueError):
                n = 0
        if n <= 0:
            return False
        store.add(name, n)
        return True

    # -- judging ---------------------------------------------------------
    def _met(self, t, profile, run, event, fields) -> bool:
        if 'all' in t:
            return all(self._met(p, profile, run, event, fields) for p in t['all'])
        if 'any' in t:
            return any(self._met(p, profile, run, event, fields) for p in t['any'])
        if 'stat' in t or 'run' in t:
            name = t.get('stat', t.get('run'))
            return self.value(name, profile, run) >= t['at_least']
        return event == t['event'] and _matches(t.get('where'), fields)

    def apply(self, profile, run: RunTally | None, event: str, **fields) -> list[str]:
        """Count one event and return the ids of achievements it newly earns
        (not yet unlocked in ``profile``; the caller unlocks them)."""
        touched = {'event:' + event}
        for name in self._on_event.get(event, ()):
            spec = self.counters[name]
            store = run if spec.get('scope', 'life') == 'run' else profile
            if store is not None and self._count(name, spec, store, fields):
                touched.add(name)
        out, seen = [], set()
        for key in touched:
            for a in self._watchers.get(key, ()):
                aid = a['id']
                if aid in seen or profile.is_unlocked(aid):
                    continue
                seen.add(aid)
                if self._met(a['trigger'], profile, run, event, fields):
                    out.append(aid)
        return out

    def settled(self, profile, run: RunTally | None = None) -> list[str]:
        """Achievements the counters already earn with no event needed (a
        tier a newer version added, which an old profile is already past)."""
        out = []
        for a in self.entries:
            if profile.is_unlocked(a['id']):
                continue
            if any(d.startswith('event:') for d in self._deps(a['trigger'])):
                continue
            if self._met(a['trigger'], profile, run, None, {}):
                out.append(a['id'])
        return out

    def progress(self, aid: str, profile, run: RunTally | None = None) -> tuple[int, int] | None:
        """(have, need) for an achievement that tests a counter, else None."""
        a = self.by_id.get(aid)
        if a is None:
            return None
        t = a['trigger']
        parts = t.get('all') if isinstance(t.get('all'), list) else None
        if parts and all(('stat' in p or 'run' in p) for p in parts):
            # Every subject of Polymath, every line of Four Elements: the bar
            # fills with each part's share, not the first part's alone.
            have = need = 0
            for p in parts:
                n = p['at_least']
                have += min(self.value(p.get('stat', p.get('run')), profile, run), n)
                need += n
            return have, need
        mark = _first_threshold(t)
        if not mark:
            return None
        _key, name, need = mark
        return min(self.value(name, profile, run), need), need

    def ladder(self, name: str) -> list[dict]:
        return sorted((a for a in self.entries if a.get('ladder') == name),
                      key=lambda a: a['tier'])


_BOOK: Book | None = None


def load(path: str | None = None) -> Book:
    """The Book from data/achievements.json (cached). A bad file is logged
    and its bad entries dropped, so a typo can never stop the game."""
    global _BOOK
    if _BOOK is not None and path is None:
        return _BOOK
    shared = path is None
    if shared:
        from paths import data_path
        path = data_path('data', 'achievements.json')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {'categories': [], 'counters': {}, 'achievements': []}
    problems = validate(data) if data.get('achievements') else []
    if problems:
        try:
            from game_log import log_error
            log_error('achievements.json: ' + '; '.join(problems[:10]))
        except Exception:
            pass
        bad = {p.split(':')[0].replace('achievement ', '') for p in problems}
        data = dict(data, achievements=[a for a in data.get('achievements', [])
                                        if isinstance(a, dict) and a.get('id') not in bad
                                        and not _trigger_problems(a.get('trigger'), data.get('counters') or {}, 'x')])
    book = Book(data)
    if shared:
        _BOOK = book
    return book
