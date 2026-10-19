"""The journal's voice, as a lint (DEEDS_KARMA_DESIGN 7.2 and 7.7).

Every line the hero writes in the Journal is first person, past tense, terse:
no floor numbers, no digits, no exclamation marks outside quoted speech, no
"+1", no stat names, no game terms (karma, quiz, tier, HP, "per turn"), no
ellipses or ASCII double dashes, and at most 220 characters
(``chronicle.lint``). This test finds every such line and runs the lint:

  * src/: the text argument of every ``_chron`` / ``chronicle.chron`` /
    ``_log_chronicle`` call (string literals and f-strings, with each
    placeholder read as a plain word), every literal a variable passed there
    is set to in the same function, every value of the inline line tables
    (``_BOSS_CHRONICLE``, ``_MILESTONE_FLAVOR``, ``_ROOM_CHRONICLE``,
    ``_CHRONICLE_FLAVOR``, ``_SPEED_CHRONICLE``, ``HERO_JOURNAL``), every dict
    literal value whose key names a chronicle line (``named_chronicle``,
    ``chronicle``...), and every ``default_line=`` handed on;
  * data/: every value of every key whose name contains ``chronicle``
    (encounter options, materials, the Emberpup, the Black Knight, the
    karma rules), questions excepted.

A call whose text is neither a literal nor one of the known data-driven
sources fails ``test_every_dynamic_line_comes_from_a_linted_source``: a new
source of journal lines must be added to the lint, not slip past it.
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import chronicle  # noqa: E402

CALLS = {'_chron': 1, 'chron': 2, '_log_chronicle': 0}     # name -> text arg index
TABLES = {'_BOSS_CHRONICLE', '_MILESTONE_FLAVOR', '_ROOM_CHRONICLE', '_CHRONICLE_FLAVOR',
          '_SPEED_CHRONICLE', 'HERO_JOURNAL'}

# Call-site text that is not a literal, and where its words are linted instead.
DYNAMIC_SOURCES = {
    "d['draw_chronicle']": 'data/black_knight.json',
    "data()['sword_chronicle']": 'data/black_knight.json',
    "d['greet_chronicle']": 'data/black_knight.json',
    "d['attack_chronicle']": 'data/abandoned_emberpup.json',
    "story['unnamed_chronicle']": 'pet_system naming_story / data/abandoned_emberpup.json',
    "story['named_chronicle'].format(name=name)": 'pet_system naming_story / emberpup json',
    "_MILESTONE_FLAVOR[new_level]": 'inline table',
    "_ROOM_CHRONICLE[rtype]": 'inline table',
    "_CHRONICLE_FLAVOR[item.id]": 'inline table',
    "_SPEED_CHRONICLE[dm._speed_pct]": 'inline table',
    "_chronicle_line": "data/materials/*/first_pickup_chronicle",
    "journal": 'HERO_JOURNAL',
    "o['chronicle']": 'encounter outcome chronicle (data)',
    "enc['chronicle_meet']": 'encounter chronicle_meet (data)',
    "spec['chronicle']": 'delayed reward chronicle (data)',
    "_own": 'encounter option chronicle (data)',
    "al['on_time_chronicle']": 'data/setne_tomb.json altar',
    "al['late_chronicle']": 'data/setne_tomb.json altar',
    "_BOSS_CHRONICLE.get(monster.kind, f'Killed {monster.name}. It is done.')": 'inline table',
    "monster.kill_pair_chronicle": 'data/monsters.json kill_pair_chronicle (MON-10)',
}

# Bare variable names are only waved through in the functions known to fill
# them from a linted source (JNL-14: "text" or "line" anywhere used to pass).
SCOPED_DYNAMIC = {
    'text': {'src/karma.py:_soul_line': 'karma_rules.json chronicle',
             'src/main.py:_chron': 'the shim (its callers are linted)',
             'src/main.py:_log_chronicle': 'the old shim (no callers remain)'},
    'line': {'src/game_encounters.py:_npc_log_deed': 'encounter outcome chronicle (data)',
             'src/game_road.py:_callback_lost': 'callback lost_line (data)',
             'src/game_road.py:_lapse_due_oaths': 'oath lapse chronicle (data)',
             'src/game_road.py:_lapse_oath_now': 'oath lapse chronicle (data) or the linted fallback',
             'src/black_knight.py:_black_knight_events': 'black_knight.json draw chronicles (data)',
             'src/game_families.py:_family_news': ('monster_families.json tier_chronicle, '
                                                   'circle and loremaster chronicles (data)')},
}

# Data keys that hold a Journal line without "chronicle" in their name.
JOURNAL_KEYS = {'on_fail_trapdoor', 'closed_line', 'late_thread_line', 'last_line', 'lost_line'}


def _src_files():
    for p in sorted((ROOT / 'src').rglob('*.py')):
        yield p


def _flat(node):
    """The words of a string expression: a literal, an f-string with its
    placeholders read as "Name", a concatenation, a ``.format`` call on one.
    None when the expression is not made of literals."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                out.append(str(v.value))
            else:
                out.append('Name')
        return ''.join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _flat(node.left), _flat(node.right)
        return a + b if a is not None and b is not None else None
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'format'):
        return _flat(node.func.value)
    return None


def _literals(node):
    """Every literal line inside ``node`` (both arms of ``a or b`` / ``x if c
    else y``)."""
    if isinstance(node, ast.BoolOp):
        return [s for v in node.values for s in _literals(v)]
    if isinstance(node, ast.IfExp):
        return _literals(node.body) + _literals(node.orelse)
    s = _flat(node)
    return [s] if s is not None else []


def _text_arg(call, idx):
    for kw in call.keywords:
        if kw.arg == 'text':
            return kw.value
    return call.args[idx] if len(call.args) > idx else None


def _collect_src():
    """(lines, dynamic): ``lines`` = [(where, text)], ``dynamic`` =
    [(where, source segment)] of call-site text that is not literal."""
    lines, dynamic = [], []
    for path in _src_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == 'src/chronicle.py':
            continue
        src = path.read_text(encoding='utf-8')
        tree = ast.parse(src)
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        owner = {}
        for f in funcs:
            for n in ast.walk(f):
                owner.setdefault(id(n), f)
        for node in ast.walk(tree):
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target] if isinstance(node, ast.AnnAssign) else [])
            if any(isinstance(t, ast.Name) and t.id in TABLES for t in targets):
                if isinstance(node.value, ast.Dict):
                    for v in node.value.values:
                        for s in _literals(v):
                            lines.append((f'{rel}:{v.lineno}', s))
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                            and 'chronicle' in k.value):
                        for s in _literals(v):
                            lines.append((f'{rel}:{v.lineno}', s))
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == 'default_line':
                    for s in _literals(kw.value):
                        lines.append((f'{rel}:{kw.value.lineno}', s))
                    if isinstance(kw.value, ast.Name):
                        lines += _assigned(owner.get(id(node)), kw.value.id, rel)
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, 'id', '')
            if name not in CALLS:
                continue
            arg = _text_arg(node, CALLS[name])
            if arg is None:
                continue
            got = _literals(arg)
            for s in got:
                lines.append((f'{rel}:{node.lineno}', s))
            if not got or isinstance(arg, ast.BoolOp):
                seg = ast.get_source_segment(src, arg) or ''
                if isinstance(arg, ast.BoolOp):
                    seg = ast.get_source_segment(src, arg.values[0]) or ''
                    if seg.startswith("getattr(monster, 'kill_chronicle'"):
                        continue        # data/monsters.json kill_chronicle; fallback linted
                func = owner.get(id(node))
                dynamic.append((f'{rel}:{node.lineno}', seg.replace('"', "'"),
                                f"{rel}:{getattr(func, 'name', '')}"))
                if isinstance(arg, ast.Name):
                    lines += _assigned(owner.get(id(node)), arg.id, rel)
    return lines, dynamic


def _assigned(func, var, rel):
    """Every literal ``var`` is set to inside ``func``."""
    out = []
    if func is None:
        return out
    for n in ast.walk(func):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var
                                             for t in n.targets):
            for s in _literals(n.value):
                if s:                       # an empty line is a "write nothing" guard
                    out.append((f'{rel}:{n.lineno}', s))
    return out


def _collect_data():
    out = []
    data = ROOT / 'data'
    for path in sorted(data.rglob('*.json')):
        rel = path.relative_to(ROOT).as_posix()
        if '/questions/' in rel or '/question_contexts/' in rel:
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))

        def walk(o, where):
            if isinstance(o, dict):
                for k, v in o.items():
                    if ('chronicle' in str(k) or k in JOURNAL_KEYS) and isinstance(v, str):
                        out.append((f'{rel}:{where}.{k}', v))
                    elif ('chronicle' in str(k) and isinstance(v, list)
                          and all(isinstance(x, str) for x in v)):
                        # a list of lines (monster_families.json tier_chronicle)
                        out.extend((f'{rel}:{where}.{k}[{i}]', x) for i, x in enumerate(v))
                    else:
                        walk(v, f'{where}.{k}')
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f'{where}[{i}]')
        walk(doc, '')
    return out


def _report(found):
    bad = []
    for where, text in found:
        problems = chronicle.lint(text)
        if problems:
            bad.append(f"{where}: {', '.join(problems)}: {text[:90]!r}")
    return bad


def test_the_lint_catches_each_rule():
    assert chronicle.lint("Took the stone. It was heavier than it looked.") == []
    assert 'floor number' in chronicle.lint("Level 20. The air is heavy.")
    assert 'number' in chronicle.lint("Broke a seal. 3 of 7 now.")
    assert 'exclamation' in chronicle.lint("First Insight!")
    assert chronicle.lint('He said "None shall pass!" and meant it.') == []
    assert '+N' in chronicle.lint("Felt stronger (+1).")
    assert 'stat name' in chronicle.lint("INT permanently increased.")
    assert 'game term' in chronicle.lint("Cleared Tier three of the quiz.")
    assert 'game term' in chronicle.lint("It drains me every turn.")
    assert 'ellipsis' in chronicle.lint("I feel... different.")
    assert 'ASCII dash' in chronicle.lint("Cleared it -- auto-passes.")
    assert 'too long' in chronicle.lint("a" * 221)
    assert chronicle.lint("Sherlock Holmes, of 221B Baker Street.") == []


def test_every_chronicle_line_in_src_passes_the_voice_lint():
    lines, _dyn = _collect_src()
    assert len(lines) >= 110, f"only {len(lines)} lines found: the collector is broken"
    bad = _report(lines)
    assert not bad, f"{len(bad)} journal lines break the voice:\n" + "\n".join(bad)


def test_every_chronicle_line_in_data_passes_the_voice_lint():
    found = _collect_data()
    assert len(found) >= 120, f"only {len(found)} data lines found"
    bad = _report(found)
    assert not bad, f"{len(bad)} data journal lines break the voice:\n" + "\n".join(bad)


def test_every_dynamic_line_comes_from_a_linted_source():
    _lines, dynamic = _collect_src()
    unknown = sorted({f"{w}: {seg} (in {scope})" for w, seg, scope in dynamic
                      if seg not in DYNAMIC_SOURCES
                      and scope not in SCOPED_DYNAMIC.get(seg, {})})
    assert not unknown, ("journal text from a source the lint does not read "
                         "(add it to the lint):\n" + "\n".join(unknown))


def test_a_bare_text_or_line_variable_is_only_trusted_where_it_is_known():
    """JNL-14: a new ``_chron(kind, text)`` in some other function must be
    reported, not waved through because the variable is called ``text``."""
    assert 'text' not in DYNAMIC_SOURCES and 'line' not in DYNAMIC_SOURCES
    # The scope check itself: the same bare name in an unknown function fails.
    fake = [('src/x.py:1', 'text', 'src/x.py:_somewhere_new')]
    assert [s for _w, s, sc in fake if sc not in SCOPED_DYNAMIC.get(s, {})] == ['text']
    _lines, dynamic = _collect_src()
    assert any(seg == 'text' for _w, seg, _s in dynamic), 'the collector lost the shim'


def test_journal_lines_under_other_keys_are_linted():
    """JNL-14: on_fail_trapdoor (an escort's lost-by-trapdoor line), thread
    closing lines and People last lines are Journal text too."""
    found = dict(_collect_data())
    keys = {w.rsplit('.', 1)[-1] for w in found}
    assert {'on_fail_trapdoor', 'closed_line', 'late_thread_line', 'last_line'} <= keys
    assert 'game term' in chronicle.lint('The floor dropped out and I lost karma.')


# ---------------------------------------------------------------- JNL-14
# Placeholders read as "Name" hide what a real value does to the sentence
# ("a bear trap trap", "I took The Bull's Horn", "I named the Sherlock").
# Each placeholder below is filled with every real value it can take, and the
# result is checked for a doubled word, a capitalised article mid-sentence and
# a lowercase article before a proper name.

def _sample_values():
    import dungeon
    import pet_system
    from mystery_system import MYSTERIES
    traps = sorted({t['type'].replace('_', ' ') for t in dungeon.TRAP_TYPES})
    boons = json.loads((ROOT / 'data' / 'boss_boons.json').read_text(encoding='utf-8'))
    gifts = sorted({g['name'] for k, v in boons.items() if k != '_meta'
                    for g in v.get('gifts', ()) if g.get('name')})
    species = []
    for sp in pet_system._SPECIES.values():
        proper = pet_system.has_own_name(sp)
        for st in sp.get('stages', ()):
            if st.get('name'):
                species.append((st['name'], proper))

    def a_or_an(s):
        return ('an ' if s[:1].lower() in 'aeiou' else 'a ') + s
    return {
        "self._a_or_an(trap_type.replace('_', ' '))": [(a_or_an(t), False) for t in traps],
        "self._a_or_an(tname)": [(a_or_an(t), False) for t in traps],
        "gift['name']": [(g, False) for g in gifts],
        "m['name']": [(m['name'], False) for m in MYSTERIES.values() if m.get('name')],
        "pet.species_name": species,
    }


# Sites already filed (JNL-11, JNL-12, JNL-13) and owned by another fix; they
# are skipped while their text still reads this way, and drop out once fixed.
PENDING_SAMPLES = {
    ('src/main.py', "self._a_or_an(trap_type.replace('_', ' '))"),     # JNL-11
    ('src/main.py', "self._a_or_an(tname)"),                           # JNL-11
    ('src/game_input.py', "pet.species_name"),                         # JNL-12
    ('src/game_combat.py', "gift['name']"),                            # JNL-13
    ('src/game_divine.py', "m['name']"),                               # JNL-13
}


def sample_lint(text, proper_spans=()) -> list:
    out = []
    if re.search(r'\b(\w+)\s+\1\b', text, re.I):
        out.append('doubled word')
    if re.search(r'\b[a-z]\w*\s+(The|A|An)\s', text):
        out.append('capital article mid-sentence')
    for start in proper_spans:
        if re.search(r'\b(the|a|an)\s$', text[:start]):
            out.append('article before a proper name')
    return out


def _sampled_src():
    """[(rel, placeholder, filled text, problems)] for every chron call whose
    f-string has a sampled placeholder."""
    samples = _sample_values()
    out = []
    for path in _src_files():
        rel = path.relative_to(ROOT).as_posix()
        src = path.read_text(encoding='utf-8')
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, 'id', '')
            if name not in CALLS:
                continue
            arg = _text_arg(node, CALLS[name])
            parts = []
            for js in ([arg] if isinstance(arg, ast.JoinedStr) else
                       [v for v in ast.walk(arg) if isinstance(v, ast.JoinedStr)] if arg else []):
                parts = js.values
                keys = [ast.get_source_segment(src, v.value) for v in parts
                        if isinstance(v, ast.FormattedValue)]
                for key in keys:
                    if key not in samples:
                        continue
                    for value, proper in samples[key]:
                        text, spans = '', []
                        for v in parts:
                            if isinstance(v, ast.Constant):
                                text += str(v.value)
                            elif ast.get_source_segment(src, v.value) == key:
                                if proper:
                                    spans.append(len(text))
                                text += value
                            else:
                                text += 'Name'
                        out.append((rel, key, text, sample_lint(text, spans)))
    return out


def test_the_sample_lint_catches_each_rule():
    assert sample_lint('Stepped on a bear trap trap.') == ['doubled word']
    assert sample_lint("I took The Bull's Horn and left the rest.") == [
        'capital article mid-sentence']
    assert sample_lint("I named the Sherlock 'Bean'.", [len('I named the ')]) == [
        'article before a proper name']
    assert sample_lint("The Bull's Horn was mine. I named Sherlock 'Bean'.",
                       [len("The Bull's Horn was mine. I named ")]) == []


def test_sampled_placeholders_read_right():
    assert all(_sample_values().values()), 'a sample table came back empty'
    found = _sampled_src()
    bad = sorted({f"{rel} {{{key}}}: {', '.join(p)}: {text[:90]!r}"
                  for rel, key, text, p in found
                  if p and (rel, key) not in PENDING_SAMPLES})
    assert not bad, "journal lines that read wrong with real values:\n" + "\n".join(bad)


def test_every_call_site_writes_through_chron_with_a_kind():
    """All the old ``_log_chronicle`` call sites were migrated (section 7.7);
    only the shim itself remains."""
    hits = []
    for path in _src_files():
        for n in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == '_log_chronicle'):
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{n.lineno}")
    assert not hits, "\n".join(hits)


def test_no_generic_encounter_verbs_remain():
    """The random "Met the Rat-Catcher. Had to make a hard choice." lines are
    gone (DEEDS_KARMA_DESIGN 7.7)."""
    src = (ROOT / 'src' / 'game_encounters.py').read_text(encoding='utf-8')
    for gone in ('_NPC_VERBS', '_FLAVOR_VERBS', 'Had to make a hard choice',
                 'A brief exchange in the dark'):
        assert gone not in src


def test_approved_lines_are_word_for_word():
    """Lines Brandon approved stay exactly as written."""
    import pet_system
    shep = pet_system._SPECIES['shep']['naming_story']
    assert shep['unnamed_chronicle'] == (
        "A soul sphere hatched and out came Shep, the farm dog from the old bedtime "
        "stories. He came to save us in every story. I think he still will.")
    d = json.loads((ROOT / 'data' / 'abandoned_emberpup.json').read_text(encoding='utf-8'))
    assert d['named_chronicle'] == (
        "Found a little fire lizard waiting on a rock in the rain for a trainer who never "
        "came back. I named it {name}. It walks right at my heel, and I am never leaving it "
        "anywhere.")
    src = (ROOT / 'src' / 'game_input.py').read_text(encoding='utf-8')
    assert "I named the {pet.species_name} '{name}'. " in src
    assert "\"I'm not alone anymore.\"" in src
