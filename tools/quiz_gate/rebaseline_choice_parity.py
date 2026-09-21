#!/usr/bin/env python3
"""Regenerate tests/data/choice_length_violations_baseline.json.

Baseline should only ever shrink.

Usage:
    python tools/quiz_gate/rebaseline_choice_parity.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'tests'))

from test_choice_length_parity import _current_violations, BANKS  # noqa: E402


def main():
    current = _current_violations()
    total = sum(len(v) for v in current.values())

    out_path = ROOT / 'tests' / 'data' / 'choice_length_violations_baseline.json'
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
