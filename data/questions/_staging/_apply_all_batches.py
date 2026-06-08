"""Apply the three 2026-06-07 staging batches to their banks, re-gated + round-
trip guarded (I don't trust subagent output blindly):
  - science_wonder_pillar.json  -> APPEND 40 wonder-story questions to science.json
  - history_wonder_fixes.json   -> REPLACE-by-locator in history.json (Magna Carta etc.)
  - animal_rewrite.json         -> REMOVE-by-locator + APPEND adds in animal.json

Gate per question: answer in choices, exactly 4 choices, char-parity ratio <= 1.30.
Failing items are SKIPPED + reported, never applied. Only the 5 canonical fields
are written (tier/question/answer/choices/context).
"""
import json
from pathlib import Path

Q = Path(__file__).resolve().parents[1]          # data/questions
STAGE = Path(__file__).resolve().parent           # _staging
CANON = ('tier', 'question', 'answer', 'choices', 'context')


def gate(q):
    ch = q.get('choices') or []
    if q.get('answer') not in ch:
        return 'answer-not-in-choices'
    if len(ch) != 4:
        return f'need-4-choices (got {len(ch)})'
    L = [len(c) for c in ch]
    if min(L) == 0:
        return 'empty-choice'
    if max(L) / min(L) > 1.30:
        return f'parity {max(L) / min(L):.2f}'
    return None


def canon(q):
    return {k: q[k] for k in CANON}


def load_fmt(path):
    orig = path.read_text(encoding='utf-8')
    data = json.loads(orig)
    trailing = orig[len(orig.rstrip('\n')):]
    for flag in (False, True):
        if json.dumps(data, indent=2, ensure_ascii=flag) == orig.rstrip('\n'):
            return data, flag, trailing
    raise SystemExit(f'cannot round-trip {path.name}')


def write_fmt(path, data, flag, trailing):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=flag) + trailing, encoding='utf-8')


# ---- SCIENCE: append the wonder pillar -------------------------------------
def apply_science():
    bank, flag, trail = load_fmt(Q / 'science.json')
    new = json.loads((STAGE / 'science_wonder_pillar.json').read_text(encoding='utf-8'))
    added = skipped = 0
    for q in new:
        why = gate(q)
        if why:
            print(f'  SKIP science: {why} :: {q.get("question","")[:55]}')
            skipped += 1
            continue
        bank.append(canon(q))
        added += 1
    write_fmt(Q / 'science.json', bank, flag, trail)
    print(f'science.json: +{added} wonder-pillar questions ({skipped} skipped) -> {len(bank)} total')


# ---- HISTORY: replace by locator -------------------------------------------
def apply_history():
    bank, flag, trail = load_fmt(Q / 'history.json')
    fixes = json.loads((STAGE / 'history_wonder_fixes.json').read_text(encoding='utf-8'))
    applied = 0
    for fx in fixes:
        loc = fx['locator']
        hits = [i for i, q in enumerate(bank) if loc in q.get('question', '')]
        if len(hits) != 1:
            print(f'  SKIP history: locator matched {len(hits)} :: {loc[:45]}')
            continue
        why = gate(fx)
        if why:
            print(f'  SKIP history: {why} :: {loc[:45]}')
            continue
        bank[hits[0]] = canon(fx)
        applied += 1
        print(f'  history idx{hits[0]} -> answer: {fx["answer"][:55]}')
    write_fmt(Q / 'history.json', bank, flag, trail)
    print(f'history.json: {applied} rewrites applied -> {len(bank)} total')


# ---- ANIMAL: remove by locator + append adds -------------------------------
def apply_animal():
    bank, flag, trail = load_fmt(Q / 'animal.json')
    spec = json.loads((STAGE / 'animal_rewrite.json').read_text(encoding='utf-8'))
    remove_idx = set()
    for loc in spec.get('remove', []):
        hits = [i for i, q in enumerate(bank) if loc in q.get('question', '')]
        if len(hits) != 1:
            print(f'  SKIP animal remove: locator matched {len(hits)} :: {loc[:45]}')
            continue
        remove_idx.add(hits[0])
    kept = [q for i, q in enumerate(bank) if i not in remove_idx]
    added = skipped = 0
    for q in spec.get('add', []):
        why = gate(q)
        if why:
            print(f'  SKIP animal add: {why} :: {q.get("question","")[:55]}')
            skipped += 1
            continue
        kept.append(canon(q))
        added += 1
    write_fmt(Q / 'animal.json', kept, flag, trail)
    print(f'animal.json: -{len(remove_idx)} removed, +{added} added ({skipped} add-skipped) '
          f'-> {len(bank)} -> {len(kept)} total')


for name, fn in (('SCIENCE', apply_science), ('HISTORY', apply_history), ('ANIMAL', apply_animal)):
    print(f'== {name} ==')
    try:
        fn()
    except Exception as e:
        print(f'  !! {name} failed: {e}')
    print()
