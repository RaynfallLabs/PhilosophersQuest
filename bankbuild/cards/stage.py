"""Stage question changes for a card batch without touching the shipped bank.

    py -m bankbuild.cards.stage check  <subject> <changes.json>[,<more.json>]
    py -m bankbuild.cards.stage packet <subject> <batch> <changes.json>[,...] --topics a,b,c
    py -m bankbuild.cards.stage apply  <subject> <changes.json>[,...] [--write]

Added 2026-10-23 for the post-rollout content decisions (re-keyed trivia
spoilers, the split mega-ladders, the AI same-fact dedup, grammar's merged
pairs). Those change a ladder's KEYS, so their cards have to be rewritten and
re-judged against the new questions; `fix_questions` cannot do that, because a
fix made before the merge strands the card's `teaches` hashes (AUTHOR_SPEC,
"Order of operations").

So a writer describes the changes in a file and never edits data/:

    {"replace": [{"hash": "<live stem hash>",
                  "new": {"question", "answer", "choices", "context"[, "tier"]}}],
     "retopic": {"<live stem hash>": "<new topic>"},
     "delete":  ["<live stem hash>", ...],
     "add":     [{"tier", "question", "answer", "choices", "context", "topic"}]}

`packet` cuts bNNN_in.json for the named topics from the bank AS IT WILL BE
(live data plus the changes), so the card is written, gated and judged
against the new hashes. `apply --write` then writes those changes to the bank
just before `merge`, so the bank and the cards move together:
    stage check -> stage packet -> write cards -> gate -> judge -> stage apply -> merge.

`apply` also drops the card of any topic left with no questions (a split or
merged-away ladder), and moves a replaced question's `teaches` entry to its new
hash so the bank never sits with a card pointing at a stem that is gone.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

from bankbuild.cards.common import CDIR, QDIR, ROOT, batch_path, load_cards, stem_hash, write_json
from bankbuild.cards.extract import packet as card_packet

FIELDS = ('question', 'answer', 'choices', 'context')


def _load_changes(spec: str) -> list[dict]:
    out = []
    for p in spec.split(','):
        if p.strip():
            path = Path(p.strip())
            out.append(json.loads((path if path.is_absolute() else ROOT / path)
                                  .read_text(encoding='utf-8')))
    return out


def staged_bank(subject: str, changes: list[dict]) -> tuple[list[dict], list[str], list[dict]]:
    """(the bank with every change applied, problems found while applying,
    the replaced and added questions)."""
    live = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    index = {stem_hash(q['question']): q for q in live}
    problems: list[str] = []
    touched: dict[str, str] = {}
    deleted: set[int] = set()
    changed: list[dict] = []

    def find(h: str, what: str):
        q = index.get(h)
        if q is None:
            problems.append(f'{what}: no live question has hash {h}')
        return q

    for ch in changes:
        for h, topic in (ch.get('retopic') or {}).items():
            q = find(h, 'retopic')
            if q is not None:
                q['topic'] = topic
        for h in ch.get('delete') or []:
            q = find(h, 'delete')
            if q is not None:
                if h in touched:
                    problems.append(f'delete: {h} is also {touched[h]}')
                touched[h] = 'deleted'
                deleted.add(id(q))
        for r in ch.get('replace') or []:
            h = r.get('hash', '')
            q = find(h, 'replace')
            if q is None:
                continue
            if h in touched:
                problems.append(f'replace: {h} is also {touched[h]}')
            touched[h] = 'replaced'
            changed.append(q)
            new = r.get('new') or {}
            for f in FIELDS + ('tier',):
                if f in new:
                    q[f] = new[f]
            if q['answer'] not in q.get('choices', []):
                problems.append(f'replace {h}: the answer is not among the choices')
    bank = [q for q in live if id(q) not in deleted]
    for ch in changes:
        for a in ch.get('add') or []:
            if not a.get('topic'):
                problems.append(f'add: no topic on "{a.get("question", "")[:50]}"')
            bank.append(dict(a))
            changed.append(bank[-1])
    return bank, problems, changed


def _shape_problems(q: dict) -> list[str]:
    errs = []
    for f in FIELDS + ('tier', 'topic'):
        if f not in q or q[f] in ('', None, []):
            errs.append(f'missing {f}')
    ch = q.get('choices') or []
    if len(ch) != 4 or len(set(ch)) != 4:
        errs.append('needs four distinct choices')
    if q.get('answer') not in ch:
        errs.append('answer not among the choices')
    if q.get('tier') not in (1, 2, 3, 4, 5):
        errs.append(f'bad tier {q.get("tier")!r}')
    return errs


def _test_helper(module_file: str, name: str):
    spec = importlib.util.spec_from_file_location('_stage_' + name, ROOT / 'tests' / module_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, name)


def check(subject: str, changes: list[dict]) -> int:
    """Gate every new or replaced question. Returns the number of failures."""
    bank, problems, changed = staged_bank(subject, changes)
    changed_ids = {id(q) for q in changed}

    # A stem may repeat elsewhere in the bank already (grammar has three
    # cross-topic twins); only a repeat that a change creates is this batch's.
    seen: dict[str, int] = {}
    for q in bank:
        h = stem_hash(q['question'])
        seen[h] = seen.get(h, 0) + 1
    changed_hashes = {stem_hash(q['question']) for q in changed}
    problems += [f'two questions share the stem hash {h}' for h, n in seen.items()
                 if n > 1 and h in changed_hashes]

    from tools.quizgen.deterministic import (GateStatus, build_answer_collision_index,
                                             build_duplicate_index, validate_answer_collision,
                                             validate_anti_rote, validate_duplicate,
                                             validate_length_budget, validate_length_parity,
                                             validate_trailing_tokens)
    try:
        gates = importlib.import_module(f'tools.quizgen.gates.{subject}')
    except ModuleNotFoundError:
        gates = None
    soft = getattr(gates, 'SOFT_WARN_GATES', frozenset())
    find_they = _test_helper('test_no_singular_they.py', 'find_singular_they')
    jargon = _test_helper('test_ladder_blurb_coverage.py', '_context_jargon')
    # The bank ratchets the suite runs, so a writer sees them before apply
    # (they are keyed by question index there, so a new failure shows up
    # only after the change lands).
    acronyms = _test_helper('test_acronym_teach_before_test.py', '_find_unexplained_acronyms')
    leaked = _test_helper('test_answer_leak.py', '_leaked_bigrams')
    prints_answer = _test_helper('test_answer_leak.py', '_answer_in_stem')
    parity = _test_helper('test_choice_length_parity.py', 'RATIO_THRESHOLD')
    ratio_answer = _test_helper('test_magpick_wonder_pattern.py', 'is_ratio_answer')
    magnitude_stem = _test_helper('test_magpick_wonder_pattern.py', 'is_magnitude_stem')
    dup_index = build_duplicate_index(bank)
    ans_index = build_answer_collision_index(bank)

    warnings: list[str] = []
    for i, q in enumerate(bank):
        if id(q) not in changed_ids:
            continue
        tag = f'{stem_hash(q["question"])} ({q.get("topic")}, T{q.get("tier")})'
        problems += [f'{tag}: {e}' for e in _shape_problems(q)]
        for name, res in (('length_parity', validate_length_parity(q, subject=subject)),
                          ('length_budget', validate_length_budget(q, subject=subject)),
                          ('anti_rote', validate_anti_rote(q, subject=subject)),
                          ('trailing_tokens', validate_trailing_tokens(q, subject=subject)),
                          ('duplicate', validate_duplicate(q, dup_index, self_idx=i))):
            if res.status == GateStatus.FAIL:
                problems.append(f'{tag}: {name}: {res.detail}')
        res = validate_answer_collision(q, ans_index, self_idx=i, subject=subject)
        if res.status == GateStatus.FAIL:
            warnings.append(f'{tag}: answer_collision: {res.detail}')
        if gates is not None:
            for name, msg in gates.run_gates(q).items():
                if msg:
                    (warnings if name in soft else problems).append(f'{tag}: {name}: {msg}')
        for f in FIELDS:
            text = ' | '.join(q[f]) if f == 'choices' else str(q.get(f, ''))
            if find_they(text):
                problems.append(f'{tag}: singular they in {f}')
        if jargon(q.get('context', '')):
            problems.append(f'{tag}: quiz jargon in context: {jargon(q["context"])}')
        if acronyms(q['question']):
            problems.append(f'{tag}: unexplained acronym in the stem {acronyms(q["question"])} '
                            '(spell it out, or put it in brackets after the words)')
        if leaked(q):
            problems.append(f'{tag}: the stem leaks the answer: {leaked(q)}')
        if prints_answer(q):
            problems.append(f'{tag}: the stem prints its own answer')
        if ratio_answer(str(q.get('answer', ''))) and magnitude_stem(q['question']):
            problems.append(f'{tag}: a bare number answers a "how much / what percentage" stem '
                            '(Wonder Pattern 4: key a named thing, or let the stem build the number)')
        lens = [len(c) for c in q.get('choices') or []]
        if lens and min(lens) and max(lens) / min(lens) > parity:
            problems.append(f'{tag}: choice lengths {lens} are too uneven (longest over '
                            f'{parity}x the shortest)')

    for p in problems:
        print('  FAIL', p)
    for w in warnings:
        print('  warn', w)
    print(f'{subject}: {len(changed)} new or replaced questions; '
          f'{len(problems)} failures, {len(warnings)} warnings')
    return len(problems)


def make_packet(subject: str, batch: int, changes: list[dict], topics: list[str]) -> None:
    bank, problems, _changed = staged_bank(subject, changes)
    if problems:
        sys.exit('fix the change file first:\n  ' + '\n  '.join(problems))
    lad: dict[str, list[dict]] = {}
    for q in bank:
        lad.setdefault(q.get('topic'), []).append(q)
    for t in lad:
        lad[t].sort(key=lambda q: int(q.get('tier', 1)))
    old = load_cards(subject)
    missing = [t for t in topics if t not in lad]
    if missing:
        sys.exit(f'no questions in the staged bank for: {missing}')
    write_json(batch_path(subject, batch, 'in'),
               {'subject': subject, 'batch': batch,
                'topics': [card_packet(subject, t, lad[t], old.get(t)) for t in topics]})
    sizes = ', '.join(f'{t} {len(lad[t])}' for t in topics)
    print(f'{subject} b{batch:03d}: staged packet for {len(topics)} topics ({sizes})')


def apply(subject: str, changes: list[dict], write: bool) -> None:
    qpath = QDIR / f'{subject}.json'
    raw = qpath.read_text(encoding='utf-8')
    live = json.loads(raw)
    before = {stem_hash(q['question']): q.get('topic') for q in live}
    bank, problems, _changed = staged_bank(subject, changes)
    if problems:
        sys.exit('fix the change file first:\n  ' + '\n  '.join(problems))
    cpath = CDIR / f'{subject}.json'
    cards = json.loads(cpath.read_text(encoding='utf-8')) if cpath.exists() else {}

    # A replaced stem keeps its teaching sentence under its new hash until the
    # rewritten card is merged over it.
    moved = 0
    for ch in changes:
        for r in ch.get('replace') or []:
            new_q = (r.get('new') or {}).get('question')
            if not new_q:
                continue
            entry = cards.get(before.get(r['hash']))
            teaches = entry.get('teaches') if isinstance(entry, dict) else None
            if teaches and r['hash'] in teaches:
                teaches[stem_hash(new_q)] = teaches.pop(r['hash'])
                moved += 1
    # Teaches entries for deleted or re-topiced rungs leave their old card.
    after = {stem_hash(q['question']): q.get('topic') for q in bank}
    for h, t in before.items():
        entry = cards.get(t)
        if isinstance(entry, dict) and entry.get('teaches') and h in entry['teaches'] \
                and after.get(h) != t:
            entry['teaches'].pop(h)
    topics_now = {q.get('topic') for q in bank}
    dropped = sorted(t for t in cards if t not in topics_now and t in set(before.values()))
    for t in dropped:
        cards.pop(t)
    new_topics = sorted(topics_now - set(before.values()))

    print(f'{subject}: {len(live)} -> {len(bank)} questions; {moved} teaches entries moved; '
          f'cards dropped {dropped or "none"}; new topics {new_topics or "none"}')
    if write:
        qpath.write_text(json.dumps(bank, ensure_ascii=False, indent=2)
                         + ('\n' if raw.endswith('\n') else ''), encoding='utf-8', newline='\n')
        cpath.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{subject}: written (merge the batch next)')
    else:
        print('(dry run: pass --write to change the bank)')


def main() -> None:
    cmd, subject = sys.argv[1], sys.argv[2]
    if cmd == 'check':
        sys.exit(1 if check(subject, _load_changes(sys.argv[3])) else 0)
    elif cmd == 'packet':
        topics = sys.argv[sys.argv.index('--topics') + 1].split(',')
        make_packet(subject, int(sys.argv[3]), _load_changes(sys.argv[4]), [t for t in topics if t])
    elif cmd == 'apply':
        apply(subject, _load_changes(sys.argv[3]), '--write' in sys.argv)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
