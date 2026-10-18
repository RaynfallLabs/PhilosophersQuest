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
import os
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
    "text": 'karma_rules.json chronicle / the shim',
    "line": 'encounter outcome chronicle (data) or a literal set in the function',
    "_own": 'encounter option chronicle (data)',
    "al['on_time_chronicle']": 'data/setne_tomb.json altar',
    "al['late_chronicle']": 'data/setne_tomb.json altar',
    "_BOSS_CHRONICLE.get(monster.kind, f'Killed {monster.name}. It is done.')": 'inline table',
}


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
                dynamic.append((f'{rel}:{node.lineno}', seg.replace('"', "'")))
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
                    if 'chronicle' in str(k) and isinstance(v, str):
                        out.append((f'{rel}:{where}.{k}', v))
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
    unknown = sorted({f"{w}: {seg}" for w, seg in dynamic if seg not in DYNAMIC_SOURCES})
    assert not unknown, ("journal text from a source the lint does not read "
                         "(add it to the lint):\n" + "\n".join(unknown))


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
