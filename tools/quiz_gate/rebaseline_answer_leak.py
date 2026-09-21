#!/usr/bin/env python3
"""Regenerate tests/data/answer_leak_violations_baseline.json.

Run this AFTER a batch of questions has had their answer-leak bigrams
fixed. The new baseline reflects the shrunken backlog; the CI gate
(`tests/test_answer_leak.py`) then blocks any NEW leak from being
introduced.

Baseline should only ever shrink.

Usage:
    python tools/quiz_gate/rebaseline_answer_leak.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'tests'))

from test_answer_leak import _current_violations, BANKS  # noqa: E402


def main():
    current = _current_violations()
    total = sum(len(v) for v in current.values())

    out_path = ROOT / 'tests' / 'data' / 'answer_leak_violations_baseline.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding='utf-8')

    print(f'Regenerated baseline at {out_path}')
    print(f'Total flagged questions: {total}')
    for bank in BANKS:
        n = len(current.get(bank, {}))
        if n:
            print(f'  {bank}: {n}')


if __name__ == '__main__':
    main()
