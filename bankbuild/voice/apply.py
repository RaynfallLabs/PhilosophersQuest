"""Apply a judged voice-pass batch to the bank.

    py -m bankbuild.voice.apply <subject> <batch>            # dry run
    py -m bankbuild.voice.apply <subject> <batch> --write    # change the bank

Only ladders that PASSED the judge are applied (bNNN_score.json); the rest
stay for another round. With --write:
  1. `stage apply` writes the stems, the merges and the deletions, and moves
     each card's `teaches` entries to the new stem hashes;
  2. the index-keyed ratchet baselines in tests/data follow the questions to
     their new positions (a merge deletes questions, which shifts every later
     index), and an entry whose question no longer breaks its rule leaves;
     the stem-keyed whole-answer baseline follows the rewritten stems;
  3. data/question_twins.json drops every group the batch touched (merged, or
     judged not twins);
  4. status.json marks the ladders done.
"""
from __future__ import annotations

import importlib.util
import json
import sys

from bankbuild.cards import stage
from bankbuild.cards.common import QDIR, ROOT
from bankbuild.voice.common import (TWINS, bpath, load_changes, load_notes, read_json, save_status,
                                    stem_hash, status)

BASE = ROOT / 'tests' / 'data'


def _test_mod(name: str):
    spec = importlib.util.spec_from_file_location('_voice_' + name, ROOT / 'tests' / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def filtered_changes(subject: str, batch: int, topics: set[str]) -> dict:
    """The batch's changes for the given topics only."""
    pkt = read_json(bpath(subject, batch, 'in'))
    topic_of = {q['hash']: t['topic'] for t in pkt['topics'] for q in t['questions']}
    ch = load_changes(subject, batch)
    return {'replace': [r for r in ch.get('replace') or [] if topic_of.get(r['hash']) in topics],
            'delete': [h for h in ch.get('delete') or [] if topic_of.get(h) in topics]}


def remap_baselines(subject: str, old_bank: list[dict], new_bank: list[dict],
                    changes: dict) -> list[str]:
    """Carry the tests/data ratchets across the change. Returns a report."""
    deleted = set(changes.get('delete') or [])
    new_stem = {r['hash']: (r.get('new') or {}).get('question') for r in changes.get('replace') or []}
    old_to_new: dict[int, int] = {}
    j = 0
    for i, q in enumerate(old_bank):
        if stem_hash(q['question']) in deleted:
            continue
        old_to_new[i] = j
        j += 1
    assert j == len(new_bank), (j, len(new_bank))
    report = []

    def index_keyed(fname: str, current: dict) -> None:
        p = BASE / fname
        base = json.loads(p.read_text(encoding='utf-8'))
        old = base.get(subject)
        if not old:
            return
        if isinstance(old, list):
            moved = sorted(old_to_new[i] for i in old if i in old_to_new and old_to_new[i] in current)
        else:
            moved = {str(old_to_new[int(k)]): current[old_to_new[int(k)]]
                     for k in old if int(k) in old_to_new and old_to_new[int(k)] in current}
        if moved:
            base[subject] = moved
        else:
            base.pop(subject, None)
        p.write_text(json.dumps(base, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        report.append(f'{fname}: {len(old)} -> {len(moved)}')

    acr = _test_mod('test_acronym_teach_before_test')
    leak = _test_mod('test_answer_leak')
    par = _test_mod('test_choice_length_parity')
    mag = _test_mod('test_magpick_wonder_pattern')
    cur_acr = {i: acr._find_unexplained_acronyms(q['question']) for i, q in enumerate(new_bank)}
    index_keyed('acronym_violations_baseline.json', {i: v for i, v in cur_acr.items() if v})
    cur_leak = {i: [list(b) for b in leak._leaked_bigrams(q)] for i, q in enumerate(new_bank)}
    index_keyed('answer_leak_violations_baseline.json', {i: v for i, v in cur_leak.items() if v})
    cur_par = {}
    for i, q in enumerate(new_bank):
        lens = [len(c) for c in q.get('choices') or []]
        if len(lens) >= 2 and min(lens) and max(lens) / min(lens) > par.RATIO_THRESHOLD:
            cur_par[i] = lens
    index_keyed('choice_length_violations_baseline.json', cur_par)
    cur_mag = {i: True for i, q in enumerate(new_bank)
               if mag.is_ratio_answer(q.get('answer', '')) and mag.is_magnitude_stem(q.get('question', ''))}
    index_keyed('magpick_violations_baseline.json', cur_mag)

    # Keyed by [answer, stem]: follow the rewritten stems.
    p = BASE / 'answer_whole_word_leak_baseline.json'
    base = json.loads(p.read_text(encoding='utf-8'))
    old = base.get(subject) or []
    if old:
        by_stem = {q['question']: stem_hash(q['question']) for q in old_bank}
        allowed = set()
        for a, s in old:
            h = by_stem.get(s)
            if h in deleted:
                continue
            allowed.add((a, new_stem.get(h) or s))
        hits = sorted([str(q.get('answer', '')), q.get('question', '')]
                      for q in new_bank if leak._answer_in_stem(q))
        kept = [h for h in hits if tuple(h) in allowed]
        if kept:
            base[subject] = kept
        else:
            base.pop(subject, None)
        p.write_text(json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        report.append(f'answer_whole_word_leak_baseline.json: {len(old)} -> {len(kept)}')
    return report


def drop_twin_groups(subject: str, touched: set[str]) -> int:
    if not TWINS.exists():
        return 0
    data = json.loads(TWINS.read_text(encoding='utf-8'))
    groups = data.get('groups', {}).get(subject, [])
    keep = [g for g in groups if not any(h in touched for h, _t in g)]
    dropped = len(groups) - len(keep)
    if keep:
        data['groups'][subject] = keep
    else:
        data.get('groups', {}).pop(subject, None)
    TWINS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return dropped


def main() -> None:
    subject, batch = sys.argv[1], int(sys.argv[2])
    write = '--write' in sys.argv
    score = read_json(bpath(subject, batch, 'score'))
    pkt = read_json(bpath(subject, batch, 'in'))
    passed = {t for t, r in score.items() if r.get('pass')}
    waiting = [t['topic'] for t in pkt['topics'] if t['topic'] not in passed]
    st = status(subject)
    passed -= set(st['done'])
    if not passed:
        sys.exit(f'{subject} b{batch:03d}: no passing ladders left to apply '
                 f'(waiting: {waiting or "none"})')
    changes = filtered_changes(subject, batch, passed)
    old_bank = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    stage.apply(subject, [changes], write)
    if not write:
        print(f'(dry run) would apply {len(passed)} ladders; waiting: {waiting or "none"}')
        return
    new_bank = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    for line in remap_baselines(subject, old_bank, new_bank, changes):
        print('  baseline', line)
    touched = {q['hash'] for t in pkt['topics'] if t['topic'] in passed for q in t['questions']}
    print(f'  twin groups dropped: {drop_twin_groups(subject, touched)}')
    # The house-voice ratchet (tests/test_house_voice.py) comes down with it.
    from bankbuild.voice.lint import bank_report
    vp = BASE / 'voice_lint_baseline.json'
    vbase = json.loads(vp.read_text(encoding='utf-8'))
    r = bank_report(subject)
    now = r['n'] - r['clean']
    if now < vbase.get(subject, now + 1):
        print(f'  voice lint baseline: {vbase.get(subject)} -> {now}')
        vbase[subject] = now
        vp.write_text(json.dumps(vbase, indent=2) + '\n', encoding='utf-8')
    notes = load_notes(subject, batch)
    st['done'] = sorted(set(st['done']) | passed)
    b = st['batches'].setdefault(f'b{batch:03d}', {'topics': [t['topic'] for t in pkt['topics']]})
    b['state'] = 'applied' if not [t for t in waiting if t not in st['done']] else 'partly applied'
    b['merges'] = len([m for m in notes['merges']])
    save_status(subject, st)
    print(f'{subject} b{batch:03d}: applied {len(passed)} ladders; waiting: '
          f'{[t for t in waiting if t not in st["done"]] or "none"}')


if __name__ == '__main__':
    main()
