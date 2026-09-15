#!/usr/bin/env python3
"""Regenerate tests/data/acronym_violations_baseline.json.

Run this AFTER a batch of questions has been fixed (acronyms expanded
inline). The new baseline reflects the shrunken backlog; the CI gate
(`tests/test_acronym_teach_before_test.py`) then blocks any NEW violation.

Baseline should only ever shrink. `test_baseline_did_not_grow` asserts
current total <= baseline total, so an accidental "regenerate after
adding new violations" is caught.

Usage:
    python tools/quiz_gate/rebaseline_acronyms.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'tests'))

# Reuse the rule from the CI test — single source of truth.
from test_acronym_teach_before_test import _current_violations, BANKS  # noqa: E402


def main():
    current = _current_violations()
    total = sum(len(v) for v in current.values())

    out_path = ROOT / 'tests' / 'data' / 'acronym_violations_baseline.json'
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
